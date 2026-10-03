#!/usr/bin/env python3
"""Pretty Pink Vocal Presence School v3b: tiny nonlinear student.

This is a research-only follow-up to the linear v3 student. It intentionally keeps
exactly the same 18 cheap evidence features and asks one question only: can a tiny
nonlinear student reduce instrument false positives *without* losing difficult voice
recall? It has zero playback authority and makes no lyric/singer claims.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from vocal_presence_school_v3 import collect_dataset, metrics, FEATURE_NAMES, synthetic_impostor_exam


def choose_threshold(y, p):
    """Tune on validation only. Refuse a low-FPR win bought by collapsing recall."""
    rows=[]
    for th in np.linspace(.30,.80,101):
        m=metrics(y,p,float(th))
        # Primary targets are deliberately soft; held-out test remains the real exam.
        penalty=max(0.0,m['fpr']-.20)*3.0 + max(0.0,.68-m['recall'])*3.0
        score=m['balancedAccuracy'] + .20*m['f1'] - penalty
        rows.append((score,float(th),m))
    rows.sort(key=lambda x:x[0], reverse=True)
    return rows[0][1], rows[0][2]


def fit(root:Path,outdir:Path,sr:int=16000):
    outdir.mkdir(parents=True,exist_ok=True)
    X,y,splits,tracks=collect_dataset(root,sr=sr)
    tr=splits=='train'; va=splits=='valid'; te=splits=='test'
    scaler=StandardScaler().fit(X[tr])
    Xtr=scaler.transform(X[tr]); Xv=scaler.transform(X[va]); Xt=scaler.transform(X[te])
    # Tiny student: 18 -> 8 -> 1. About 161 learned parameters including biases.
    # Training-only complexity; inference is a few dozen multiply-adds per 500 ms window.
    model=MLPClassifier(hidden_layer_sizes=(8,), activation='tanh', solver='adam',
                        alpha=.025, batch_size=256, learning_rate_init=.002,
                        max_iter=350, early_stopping=True, validation_fraction=.15,
                        n_iter_no_change=25, random_state=209)
    model.fit(Xtr,y[tr])
    pv=model.predict_proba(Xv)[:,1]; pt=model.predict_proba(Xt)[:,1]
    th,vm=choose_threshold(y[va],pv); tm=metrics(y[te],pt,th)
    model_json={
      'schema':'pretty-pink-vocal-presence-student-v3b-mlp8-1',
      'authority':0,'observeOnly':True,'lyricIntelligibility':'UNKNOWN',
      'claimBoundary':'VOICE_PRESENCE_HYPOTHESIS_ONLY',
      'featureNames':FEATURE_NAMES,
      'mean':[float(x) for x in scaler.mean_], 'scale':[float(x) for x in scaler.scale_],
      'hiddenActivation':'tanh',
      'layer0Weights':[[float(v) for v in row] for row in model.coefs_[0]],
      'layer0Bias':[float(v) for v in model.intercepts_[0]],
      'layer1Weights':[float(v) for v in model.coefs_[1].reshape(-1)],
      'layer1Bias':float(model.intercepts_[1][0]),
      'voiceThreshold':float(th),
      'noVoiceThreshold':float(min(.35,max(.15,1.0-th))),
      'temporalSmoothing':'0.25*prev + 0.50*current + 0.25*next; full-scan evidence only',
      'learnedParameterCount':int(sum(w.size for w in model.coefs_)+sum(b.size for b in model.intercepts_)),
    }
    report={
      'schema':'pretty-pink-vocal-presence-school-v3b-jamendo-v1',
      'truthBoundary':'VOICE_PRESENCE_ONLY_NOT_LYRIC_INTELLIGIBILITY_NOT_SINGER_ID_NOT_PLAYBACK_AUTHORITY',
      'tracksMatched':len(set(tracks)), 'windows':int(len(y)),
      'validation':vm,'test':tm,
      'validationAuc':float(roc_auc_score(y[va],pv)),
      'testAuc':float(roc_auc_score(y[te],pt)),
      'thresholdChosenOn':'validation_only',
      'parameterCount':model_json['learnedParameterCount'],
    }
    (outdir/'jamendo-v3b-report.json').write_text(json.dumps(report,indent=2))
    (outdir/'vocal-presence-student-v3b.json').write_text(json.dumps(model_json,indent=2))
    print(json.dumps(report,indent=2),flush=True)
    # Do not reuse the linear student's synthetic scorer; these cases are re-evaluated
    # below through this student's own exported MLP math.
    mean=np.asarray(model_json['mean']); scale=np.asarray(model_json['scale'])
    W0=np.asarray(model_json['layer0Weights']); b0=np.asarray(model_json['layer0Bias'])
    W1=np.asarray(model_json['layer1Weights']); b1=model_json['layer1Bias']
    def prob(row):
        x=(np.asarray(row,dtype=float)-mean)/scale
        h=np.tanh(x@W0+b0); z=float(h@W1+b1)
        return float(1/(1+np.exp(-np.clip(z,-40,40))))
    cases={
      'sustained_harmonic_pad':[.9,.08,.12,.18,.18,.16,.12,.08,.05,.94,.35,.05,.12,.9,.04,.50,.75,.45],
      'vibrato_guitar_like':[.9,.08,.10,.12,.15,.16,.14,.14,.08,.88,.48,.32,.78,.78,.45,.42,.60,.60],
      'woodwind_like':[.85,.05,.10,.20,.22,.18,.12,.07,.03,.92,.30,.20,.72,.85,.24,.72,.90,.35],
      'bright_percussive':[.9,.02,.03,.05,.07,.10,.20,.28,.25,.20,.78,.95,.25,.45,.90,.05,.20,.95],
      'wide_synth_lead':[.9,.05,.08,.15,.17,.17,.15,.12,.08,.86,.50,.28,.70,.35,.44,.55,.72,.60],
    }
    ps={k:prob(v) for k,v in cases.items()}; confident=sum(p>=th for p in ps.values())
    stress={'cases':ps,'voiceThreshold':float(th),'confidentVoiceCases':int(confident),'totalCases':len(ps),'pass':bool(confident<=1)}
    (outdir/'synthetic-impostor-v3b-report.json').write_text(json.dumps(stress,indent=2)); print(json.dumps(stress,indent=2),flush=True)
    if not stress['pass']: raise SystemExit('v3b synthetic impostor gate failed')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('outdir');ap.add_argument('--sr',type=int,default=16000);a=ap.parse_args();fit(Path(a.root),Path(a.outdir),a.sr)
if __name__=='__main__':main()
