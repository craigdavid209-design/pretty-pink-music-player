#!/usr/bin/env python3
"""Pretty Pink Vocal Presence School v4 -- richer same-FFT evidence.

Research-only. The lesson is *voice presence hypothesis*, never lyric intelligibility,
singer identity, source separation, or playback authority.

v4 changes the evidence rather than merely the classifier: energy-combined stereo
spectra, 12 log-frequency envelope bands, six compact cepstral-envelope terms,
spectral entropy/flatness/peakiness, and the existing cheap temporal/stereo cues.
All spectral features can be derived from the same 20 ms FFT Pretty Pink already
performs; no second decode/FFT is part of the intended Android design.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from typing import Dict,List,Sequence,Tuple
import librosa
import numpy as np
from scipy.fft import dct
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

AUDIO_EXT={'.wav','.flac','.ogg','.mp3','.m4a'}
LOG_EDGES=np.geomspace(120.0,8000.0,13)
FEATURE_NAMES=(['active']+[f'logband_{i}' for i in range(12)]+[f'cepstral_{i}' for i in range(1,7)]+
               ['spectral_flatness','spectral_entropy','peakiness','centroid','spectral_flux','envelope_modulation','center_fraction','band_motion'])

def u(x): return np.clip(x,0.0,1.0)

def find_audio(root): return sorted(p for p in Path(root).rglob('*') if p.is_file() and p.suffix.lower() in AUDIO_EXT)
def find_labels(root): return {p.stem.lower():p for p in Path(root).rglob('*.lab')}

def parse_lab(p):
    out=[]
    for line in p.read_text(errors='ignore').splitlines():
        q=line.strip().split()
        if len(q)<3: continue
        try:a,b=float(q[0]),float(q[1])
        except:continue
        label=' '.join(q[2:]).lower(); voice=(label=='sing' or label.startswith('sing') or label in {'voice','vocal','vocals','1','true'})
        out.append((a,b,voice))
    return out

def discover_splits(root,audio):
    by={p.stem.lower():p for p in audio};m={}
    for p in Path(root).rglob('*'):
        if not p.is_file() or p.suffix.lower() not in {'','.txt','.lst','.list'}:continue
        low=p.name.lower();s='train' if 'train' in low else 'valid' if ('valid' in low or 'dev' in low) else 'test' if 'test' in low else None
        if not s:continue
        try:lines=p.read_text(errors='ignore').splitlines()
        except:continue
        for line in lines:
            if not line.strip():continue
            token=Path(line.strip().split()[0]).stem.lower();m[token]=s if token in by else m.get(token,s)
    if len(m)>=.8*len(audio): return m
    stems=sorted(by)
    for i,stem in enumerate(stems):
        f=(i+.5)/len(stems);m[stem]='train' if f<61/93 else ('valid' if f<77/93 else 'test')
    return m

def overlap(start,end,segs):
    v=0.0
    for a,b,voice in segs:
        if voice and b>start and a<end:v+=max(0,min(end,b)-max(start,a))
    return min(1,v/max(1e-9,end-start))

def extract(path:Path,sr=16000,win_s=.5):
    y,_=librosa.load(path,sr=sr,mono=False)
    if y.ndim==1:y=np.stack([y,y])
    elif y.shape[0]>2:y=y[:2]
    n=y.shape[1]; n500=int(sr*win_s)
    if n<n500:return np.empty((0,len(FEATURE_NAMES))),np.empty(0)
    fftwin=max(128,int(round(sr*.020)));hop=max(1,int(round(sr*.100)));nfft=1
    while nfft<fftwin:nfft<<=1
    powers=[]
    for ch in range(y.shape[0]):
        powers.append(np.abs(librosa.stft(y[ch],n_fft=nfft,win_length=fftwin,hop_length=hop,window='hann',center=False))**2+1e-15)
    P=np.stack(powers); M=P.sum(axis=0); freqs=librosa.fft_frequencies(sr=sr,n_fft=nfft); total=M.sum(axis=0)+1e-15
    t_spec=(np.arange(M.shape[1])*hop+fftwin/2)/sr
    edges=np.minimum(LOG_EDGES,sr/2-1); bands=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        mask=(freqs>=lo)&(freqs<hi);bands.append(M[mask].sum(axis=0)/total if np.any(mask) else np.zeros(M.shape[1]))
    B=np.vstack(bands); Bn=B/(B.sum(axis=0,keepdims=True)+1e-12)
    logB=np.log(Bn+1e-5); C=dct(logB,axis=0,type=2,norm='ortho')[1:7]
    flat=np.exp(np.mean(np.log(M+1e-15),axis=0))/(np.mean(M,axis=0)+1e-15);flat=u(flat/.45)
    prob=M/(total[None,:]);entropy=-np.sum(prob*np.log(prob+1e-15),axis=0)/math.log(M.shape[0]);entropy=u(entropy)
    sortedM=np.sort(M,axis=0);peak=u(sortedM[-6:].sum(axis=0)/(total+1e-15)*2.0)
    cent=u(((freqs[:,None]*M).sum(axis=0)/(total+1e-15)-250)/4750)
    flux=np.zeros(M.shape[1]);
    if M.shape[1]>1:flux[1:]=u(np.sum(np.abs(np.diff(Bn,axis=1)),axis=0)/1.1)
    mono=y.mean(axis=0);rh=max(1,int(sr*.020));rms=librosa.feature.rms(y=mono,frame_length=rh,hop_length=rh,center=False)[0]+1e-12;t_rms=(np.arange(len(rms))*rh+rh/2)/sr
    n100=max(0,1+(n-hop)//hop);center=np.zeros(n100);active=np.zeros(n100)
    for i in range(n100):
        seg=y[:,i*hop:i*hop+hop];l,r=seg[0],seg[1];mid=(l+r)*.5;side=(l-r)*.5;me=float(np.mean(mid*mid));se=float(np.mean(side*side));center[i]=me/(me+se+1e-12);db=10*math.log10(float(np.mean(seg*seg))+1e-12);active[i]=u((db+75)/40)
    t100=(np.arange(n100)*hop+hop/2)/sr
    rows=[];times=[]
    for w in range(n//n500):
        a=w*win_s;b=(w+1)*win_s;c=(a+b)/2;ms=(t_spec>=a)&(t_spec<b);mr=(t_rms>=a)&(t_rms<b);mc=(t100>=a)&(t100<b)
        if not np.any(ms) or not np.any(mr) or not np.any(mc):continue
        bb=B[:,ms].mean(axis=1);cc=C[:,ms].mean(axis=1);rr=rms[mr];mod=u((np.std(rr)/(np.mean(rr)+1e-12)-.05)/.75);nb=Bn[:,ms];motion=u(np.mean(np.sum(np.abs(np.diff(nb,axis=1)),axis=0))/1.0) if nb.shape[1]>1 else 0
        row=[float(active[mc].mean()),*bb.tolist(),*cc.tolist(),float(flat[ms].mean()),float(entropy[ms].mean()),float(peak[ms].mean()),float(cent[ms].mean()),float(flux[ms].mean()),float(mod),float(center[mc].mean()),float(motion)]
        rows.append(row);times.append(c)
    return np.asarray(rows,float),np.asarray(times,float)

def collect(root,sr=16000):
    audio=find_audio(root);labs=find_labels(root);splits=discover_splits(root,audio);Xs=[];ys=[];ss=[];tracks=[]
    for i,p in enumerate(audio):
        lp=labs.get(p.stem.lower());
        if not lp:continue
        segs=parse_lab(lp);X,t=extract(p,sr)
        keep=[];y=[]
        for j,c in enumerate(t):
            f=overlap(c-.25,c+.25,segs)
            if f>=.8:y.append(1);keep.append(j)
            elif f<=.2:y.append(0);keep.append(j)
        if keep:Xs.append(X[keep]);ys.append(np.asarray(y));ss.extend([splits.get(p.stem.lower(),'train')]*len(keep));tracks.extend([p.stem]*len(keep))
        if (i+1)%10==0:print('processed',i+1,'of',len(audio),flush=True)
    return np.vstack(Xs),np.concatenate(ys),np.asarray(ss),tracks

def metr(y,p,th):
    pred=(p>=th).astype(int);tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return {'balancedAccuracy':float(balanced_accuracy_score(y,pred)),'precision':float(precision_score(y,pred,zero_division=0)),'recall':float(recall_score(y,pred,zero_division=0)),'f1':float(f1_score(y,pred,zero_division=0)),'fpr':float(fp/max(1,fp+tn)),'fnr':float(fn/max(1,fn+tp)),'auc':float(roc_auc_score(y,p)),'n':int(len(y)),'threshold':float(th)}
def threshold(y,p):
    rows=[]
    for th in np.linspace(.30,.85,111):
        m=metr(y,p,th);pen=max(0,m['fpr']-.22)*4+max(0,.68-m['recall'])*4;score=m['balancedAccuracy']+.20*m['f1']-pen;rows.append((score,th,m))
    return max(rows,key=lambda x:x[0])[1]

def train(root,out,sr=16000):
    out.mkdir(parents=True,exist_ok=True);X,y,s,tracks=collect(root,sr);tr=s=='train';va=s=='valid';te=s=='test';sc=StandardScaler().fit(X[tr]);A=sc.transform(X[tr]);V=sc.transform(X[va]);T=sc.transform(X[te])
    candidates={
      'linear':LogisticRegression(C=.25,class_weight='balanced',max_iter=2500,random_state=209),
      'mlp10':MLPClassifier(hidden_layer_sizes=(10,),activation='tanh',alpha=.035,batch_size=256,learning_rate_init=.002,max_iter=400,early_stopping=True,validation_fraction=.15,n_iter_no_change=30,random_state=209),
    }
    reports={};models={}
    for name,model in candidates.items():
        model.fit(A,y[tr]);pv=model.predict_proba(V)[:,1];pt=model.predict_proba(T)[:,1];th=threshold(y[va],pv);reports[name]={'validation':metr(y[va],pv,th),'test':metr(y[te],pt,th)};models[name]=(model,th)
    # Selection is validation-only: highest balanced accuracy among candidates satisfying a basic anti-collapse constraint; otherwise best penalized validation result.
    eligible=[n for n,r in reports.items() if r['validation']['fpr']<=.30 and r['validation']['recall']>=.62]
    pool=eligible or list(reports);best=max(pool,key=lambda n: reports[n]['validation']['balancedAccuracy']+.1*reports[n]['validation']['f1'])
    model,th=models[best];chosen=reports[best]
    gate=chosen['test']['auc']>=.74 and chosen['test']['fpr']<=.32 and chosen['test']['recall']>=.62 and chosen['test']['balancedAccuracy']>=.66
    base={'schema':'pretty-pink-vocal-presence-v4-same-fft','truthBoundary':'VOICE_PRESENCE_ONLY_NOT_LYRIC_INTELLIGIBILITY_NOT_SINGER_ID_NOT_PLAYBACK_AUTHORITY','tracksMatched':len(set(tracks)),'windows':int(len(y)),'featureCount':len(FEATURE_NAMES),'featureNames':FEATURE_NAMES,'candidates':reports,'chosen':best,'promotionResearchGate':bool(gate),'gateDefinition':'test AUC>=.74, FPR<=.32, recall>=.62, balancedAccuracy>=.66; test never used for threshold/model selection'}
    (out/'jamendo-v4-report.json').write_text(json.dumps(base,indent=2))
    mj={'schema':'pretty-pink-vocal-presence-v4-'+best,'authority':0,'observeOnly':True,'lyricIntelligibility':'UNKNOWN','featureNames':FEATURE_NAMES,'mean':sc.mean_.tolist(),'scale':sc.scale_.tolist(),'voiceThreshold':float(th),'noVoiceThreshold':.30,'temporalSmoothing':'0.25 prev + 0.50 current + 0.25 next after full scan'}
    if best=='linear':mj.update(type='linear-logistic',coef=model.coef_[0].tolist(),intercept=float(model.intercept_[0]),learnedParameterCount=int(model.coef_.size+1))
    else:mj.update(type='mlp-tanh',layer0Weights=model.coefs_[0].tolist(),layer0Bias=model.intercepts_[0].tolist(),layer1Weights=model.coefs_[1].reshape(-1).tolist(),layer1Bias=float(model.intercepts_[1][0]),learnedParameterCount=int(sum(x.size for x in model.coefs_)+sum(x.size for x in model.intercepts_)))
    (out/'vocal-presence-student-v4.json').write_text(json.dumps(mj,indent=2));print(json.dumps(base,indent=2),flush=True)
    if not gate:raise SystemExit('v4 public held-out promotion research gate failed')

def main():
    a=argparse.ArgumentParser();a.add_argument('root');a.add_argument('outdir');a.add_argument('--sr',type=int,default=16000);q=a.parse_args();train(Path(q.root),Path(q.outdir),q.sr)
if __name__=='__main__':main()
