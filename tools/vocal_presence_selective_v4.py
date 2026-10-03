#!/usr/bin/env python3
"""Selective/abstaining calibration for Pretty Pink Vocal Presence School v4.

The binary school showed distribution shift on the held-out Jamendo test set. This
script does *not* add model capacity. It changes the question to the Pretty Pink
question: when is the evidence strong enough to make a cautious voice/no-voice
hypothesis, and when should the answer be AMBIGUOUS?

All thresholds and model selection are chosen on validation only. Test is sealed
until final reporting. Zero playback authority; lyric intelligibility remains UNKNOWN.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from vocal_presence_school_v4 import collect, FEATURE_NAMES

TARGET=.80
MIN_SIDE_COVERAGE=.08

def side_stats(y,p,lo,hi):
    voice=p>=hi; no=p<=lo; claimed=voice|no
    vp=float(np.mean(y[voice]==1)) if np.any(voice) else None
    npv=float(np.mean(y[no]==0)) if np.any(no) else None
    acc=float(np.mean(((p[claimed]>=hi).astype(int)==y[claimed]))) if np.any(claimed) else None
    return {'voiceThreshold':float(hi),'noVoiceThreshold':float(lo),'voicePrecision':vp,'noVoicePrecision':npv,
            'voiceCoverage':float(np.mean(voice)),'noVoiceCoverage':float(np.mean(no)),'claimCoverage':float(np.mean(claimed)),
            'claimAccuracy':acc,'ambiguousCoverage':float(np.mean(~claimed)),'n':int(len(y))}

def calibrate(y,p):
    upp=[]
    for t in np.linspace(.50,.95,91):
        m=p>=t; cov=float(np.mean(m)); prec=float(np.mean(y[m]==1)) if np.any(m) else 0
        if cov>=MIN_SIDE_COVERAGE and prec>=TARGET: upp.append((cov,float(t),prec))
    lows=[]
    for t in np.linspace(.05,.50,91):
        m=p<=t; cov=float(np.mean(m)); prec=float(np.mean(y[m]==0)) if np.any(m) else 0
        if cov>=MIN_SIDE_COVERAGE and prec>=TARGET: lows.append((cov,float(t),prec))
    if not upp or not lows:return None
    hi=max(upp,key=lambda x:x[0])[1];lo=max(lows,key=lambda x:x[0])[1]
    if lo>=hi:return None
    return lo,hi,side_stats(y,p,lo,hi)

def train(root:Path,out:Path,sr=16000):
    out.mkdir(parents=True,exist_ok=True);X,y,s,tracks=collect(root,sr);tr=s=='train';va=s=='valid';te=s=='test';sc=StandardScaler().fit(X[tr]);A=sc.transform(X[tr]);V=sc.transform(X[va]);T=sc.transform(X[te])
    cand={
      'linear':LogisticRegression(C=.25,class_weight='balanced',max_iter=2500,random_state=209),
      'mlp10':MLPClassifier(hidden_layer_sizes=(10,),activation='tanh',alpha=.035,batch_size=256,learning_rate_init=.002,max_iter=400,early_stopping=True,validation_fraction=.15,n_iter_no_change=30,random_state=209),
    }
    valid={};trained={}
    for n,m in cand.items():
        m.fit(A,y[tr]);pv=m.predict_proba(V)[:,1];cal=calibrate(y[va],pv);trained[n]=(m,cal)
        valid[n]=None if cal is None else cal[2]
    eligible=[n for n,v in valid.items() if v is not None]
    if not eligible:raise SystemExit('No candidate can earn both selective claims on validation')
    best=max(eligible,key=lambda n:(valid[n]['claimCoverage'],valid[n]['claimAccuracy']))
    model,cal=trained[best];lo,hi,_=cal;pt=model.predict_proba(T)[:,1];test=side_stats(y[te],pt,lo,hi)
    gate=(test['voicePrecision'] is not None and test['noVoicePrecision'] is not None and test['voicePrecision']>=.75 and test['noVoicePrecision']>=.75 and test['claimAccuracy']>=.75 and test['claimCoverage']>=.20)
    report={'schema':'pretty-pink-vocal-presence-selective-v4','truthBoundary':'VOICE_PRESENCE_HYPOTHESIS_WITH_ABSTENTION_ONLY','validationTargetPrecisionPerSide':TARGET,'minValidationSideCoverage':MIN_SIDE_COVERAGE,'validationCandidates':valid,'chosenOnValidation':best,'heldOutTest':test,'researchGate':bool(gate),'gateDefinition':'held-out voice precision>=.75, no-voice precision>=.75, claimed accuracy>=.75, total claim coverage>=.20; all else AMBIGUOUS'}
    (out/'selective-v4-report.json').write_text(json.dumps(report,indent=2));
    mj={'schema':'pretty-pink-vocal-presence-selective-v4-'+best,'authority':0,'observeOnly':True,'lyricIntelligibility':'UNKNOWN','states':['LIKELY_VOICE','AMBIGUOUS','LIKELY_NO_VOICE'],'featureNames':FEATURE_NAMES,'mean':sc.mean_.tolist(),'scale':sc.scale_.tolist(),'voiceThreshold':float(hi),'noVoiceThreshold':float(lo),'temporalSmoothing':'0.25 prev + 0.50 current + 0.25 next after full scan'}
    if best=='linear':mj.update(type='linear-logistic',coef=model.coef_[0].tolist(),intercept=float(model.intercept_[0]),learnedParameterCount=int(model.coef_.size+1))
    else:mj.update(type='mlp-tanh',layer0Weights=model.coefs_[0].tolist(),layer0Bias=model.intercepts_[0].tolist(),layer1Weights=model.coefs_[1].reshape(-1).tolist(),layer1Bias=float(model.intercepts_[1][0]),learnedParameterCount=int(sum(x.size for x in model.coefs_)+sum(x.size for x in model.intercepts_)))
    (out/'selective-v4-student.json').write_text(json.dumps(mj,indent=2));print(json.dumps(report,indent=2),flush=True)
    if not gate:raise SystemExit('Selective held-out gate failed')

def main():
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('outdir');p.add_argument('--sr',type=int,default=16000);a=p.parse_args();train(Path(a.root),Path(a.outdir),a.sr)
if __name__=='__main__':main()
