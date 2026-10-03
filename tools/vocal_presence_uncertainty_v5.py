#!/usr/bin/env python3
"""Pretty Pink Vocal Presence Uncertainty School v5.

Research-only. This lesson does not add playback authority and does not claim lyric
intelligibility, singer identity, or source separation.

v5 fixes an important research mismatch in selective v4: the v4 student contract
specified 0.25/0.50/0.25 temporal smoothing, but calibration/testing thresholded raw
per-window probabilities. v5 applies smoothing *within each song only*, never across
track boundaries, then turns local disagreement into explicit uncertainty.

States:
  STRONG_VOICE / LIKELY_VOICE / AMBIGUOUS / LIKELY_NO_VOICE / STRONG_NO_VOICE

All model fitting uses train songs. All thresholds and disagreement limits are chosen
from validation songs only. Held-out test songs are reported only after calibration.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from vocal_presence_school_v4 import collect, FEATURE_NAMES

LIKELY_TARGET = 0.85
STRONG_TARGET = 0.90
LIKELY_MIN_COVERAGE = 0.05
STRONG_MIN_COVERAGE = 0.015


def smooth_by_track(p, tracks):
    """0.25 prev + 0.50 current + 0.25 next, strictly within track identity."""
    p=np.asarray(p,float); tracks=np.asarray(tracks); out=p.copy()
    for name in np.unique(tracks):
        idx=np.flatnonzero(tracks==name)
        if not len(idx): continue
        q=p[idx]
        if len(q)==1: out[idx]=q; continue
        prev=np.r_[q[0],q[:-1]]; nxt=np.r_[q[1:],q[-1]]
        out[idx]=.25*prev+.50*q+.25*nxt
    return out


def local_disagreement(p, tracks):
    """Largest neighbor disagreement, within-track only. High values mean boundary/conflict."""
    p=np.asarray(p,float); tracks=np.asarray(tracks); out=np.zeros_like(p)
    for name in np.unique(tracks):
        idx=np.flatnonzero(tracks==name); q=p[idx]
        if len(q)<=1: continue
        dprev=np.r_[0,np.abs(np.diff(q))]; dnxt=np.r_[np.abs(np.diff(q)),0]
        out[idx]=np.maximum(dprev,dnxt)
    return out


def side_precision(y,p,d,threshold,side,dmax):
    if side=='voice': m=(p>=threshold)&(d<=dmax); correct=(y[m]==1)
    else: m=(p<=threshold)&(d<=dmax); correct=(y[m]==0)
    cov=float(np.mean(m)); prec=float(np.mean(correct)) if np.any(m) else None
    return cov,prec,m


def choose_side(y,p,d,side,target,min_cov):
    ths=np.linspace(.50,.97,95) if side=='voice' else np.linspace(.03,.50,95)
    # A disagreement cap is part of uncertainty, not model capacity. Prefer maximum
    # coverage among validation candidates meeting the requested precision.
    candidates=[]
    for dmax in (.08,.12,.16,.20,.25,.35,1.0):
        for th in ths:
            cov,prec,_=side_precision(y,p,d,float(th),side,float(dmax))
            if prec is not None and cov>=min_cov and prec>=target:
                candidates.append((cov,prec,-dmax,float(th),float(dmax)))
    if not candidates: return None
    cov,prec,_,th,dmax=max(candidates,key=lambda x:(x[0],x[1],x[2]))
    return {'threshold':th,'disagreementMax':dmax,'coverage':cov,'precision':prec}


def classify(p,d,cfg):
    state=np.full(len(p),'AMBIGUOUS',dtype=object)
    # likely tiers
    lv=(p>=cfg['likelyVoice']['threshold'])&(d<=cfg['likelyVoice']['disagreementMax'])
    ln=(p<=cfg['likelyNoVoice']['threshold'])&(d<=cfg['likelyNoVoice']['disagreementMax'])
    state[lv]='LIKELY_VOICE'; state[ln]='LIKELY_NO_VOICE'
    # strong tiers overwrite only same-side likely regions
    if cfg.get('strongVoice'):
        sv=(p>=cfg['strongVoice']['threshold'])&(d<=cfg['strongVoice']['disagreementMax'])
        state[sv]='STRONG_VOICE'
    if cfg.get('strongNoVoice'):
        sn=(p<=cfg['strongNoVoice']['threshold'])&(d<=cfg['strongNoVoice']['disagreementMax'])
        state[sn]='STRONG_NO_VOICE'
    return state


def report(y,state):
    voice=np.isin(state,['LIKELY_VOICE','STRONG_VOICE']); no=np.isin(state,['LIKELY_NO_VOICE','STRONG_NO_VOICE']); claimed=voice|no
    strongv=state=='STRONG_VOICE'; strongn=state=='STRONG_NO_VOICE'; strong=strongv|strongn
    def prec(mask,label): return float(np.mean(y[mask]==label)) if np.any(mask) else None
    return {
      'n':int(len(y)),
      'voicePrecision':prec(voice,1),'noVoicePrecision':prec(no,0),
      'voiceCoverage':float(np.mean(voice)),'noVoiceCoverage':float(np.mean(no)),
      'claimCoverage':float(np.mean(claimed)),'ambiguousCoverage':float(np.mean(~claimed)),
      'claimAccuracy':float(np.mean(((voice[claimed]).astype(int))==y[claimed])) if np.any(claimed) else None,
      'strongVoicePrecision':prec(strongv,1),'strongNoVoicePrecision':prec(strongn,0),
      'strongCoverage':float(np.mean(strong)),
    }


def train(root:Path,out:Path,sr=16000):
    out.mkdir(parents=True,exist_ok=True)
    X,y,s,tracks=collect(root,sr); tracks=np.asarray(tracks)
    tr=s=='train'; va=s=='valid'; te=s=='test'
    sc=StandardScaler().fit(X[tr]); model=LogisticRegression(C=.25,class_weight='balanced',max_iter=2500,random_state=209).fit(sc.transform(X[tr]),y[tr])

    raw=model.predict_proba(sc.transform(X))[:,1]
    smooth=smooth_by_track(raw,tracks); disagree=local_disagreement(smooth,tracks)

    cfg={
      'likelyVoice':choose_side(y[va],smooth[va],disagree[va],'voice',LIKELY_TARGET,LIKELY_MIN_COVERAGE),
      'likelyNoVoice':choose_side(y[va],smooth[va],disagree[va],'no',LIKELY_TARGET,LIKELY_MIN_COVERAGE),
      'strongVoice':choose_side(y[va],smooth[va],disagree[va],'voice',STRONG_TARGET,STRONG_MIN_COVERAGE),
      'strongNoVoice':choose_side(y[va],smooth[va],disagree[va],'no',STRONG_TARGET,STRONG_MIN_COVERAGE),
    }
    if cfg['likelyVoice'] is None or cfg['likelyNoVoice'] is None:
        raise SystemExit('Validation could not earn both likely states; keep research-only')

    vstate=classify(smooth[va],disagree[va],cfg); tstate=classify(smooth[te],disagree[te],cfg)
    vr=report(y[va],vstate); tt=report(y[te],tstate)

    # This is deliberately stricter than v4's gate. We want uncertainty to improve
    # trustworthiness, not merely rescue a binary classifier by hiding most windows.
    gate=(tt['voicePrecision'] is not None and tt['noVoicePrecision'] is not None and
          tt['voicePrecision']>=.78 and tt['noVoicePrecision']>=.78 and
          tt['claimAccuracy'] is not None and tt['claimAccuracy']>=.78 and
          tt['claimCoverage']>=.15)

    result={
      'schema':'pretty-pink-vocal-presence-uncertainty-v5',
      'truthBoundary':'VOICE_PRESENCE_HYPOTHESIS_WITH_EXPLICIT_UNCERTAINTY_ONLY',
      'authority':0,'observeOnly':True,'lyricIntelligibility':'UNKNOWN',
      'featureGeometry':'same-FFT research geometry from Vocal Presence v4; Android implementation forbidden until exact production-geometry parity is revalidated',
      'states':['STRONG_VOICE','LIKELY_VOICE','AMBIGUOUS','LIKELY_NO_VOICE','STRONG_NO_VOICE'],
      'calibration':cfg,'validation':vr,'heldOutTest':tt,
      'researchGate':bool(gate),
      'gateDefinition':'held-out likely voice precision>=.78, likely no-voice precision>=.78, claimed accuracy>=.78, claim coverage>=.15; otherwise remain research-only',
      'windows':{'train':int(np.sum(tr)),'valid':int(np.sum(va)),'test':int(np.sum(te))},
    }
    (out/'uncertainty-v5-report.json').write_text(json.dumps(result,indent=2))
    student={'schema':'pretty-pink-vocal-presence-uncertainty-v5-linear','authority':0,'observeOnly':True,'lyricIntelligibility':'UNKNOWN','states':result['states'],'featureNames':FEATURE_NAMES,'mean':sc.mean_.tolist(),'scale':sc.scale_.tolist(),'coef':model.coef_[0].tolist(),'intercept':float(model.intercept_[0]),'calibration':cfg,'temporalSmoothing':'0.25 prev + 0.50 current + 0.25 next strictly within track; local disagreement can force AMBIGUOUS','androidStatus':'RESEARCH_ONLY_NOT_IMPLEMENTABLE_UNTIL_EXACT_PRODUCTION_GEOMETRY_PARITY'}
    (out/'uncertainty-v5-student.json').write_text(json.dumps(student,indent=2))
    print(json.dumps(result,indent=2),flush=True)
    if not gate: raise SystemExit('v5 uncertainty research gate failed')


def main():
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('outdir');p.add_argument('--sr',type=int,default=16000);a=p.parse_args();train(Path(a.root),Path(a.outdir),a.sr)
if __name__=='__main__': main()
