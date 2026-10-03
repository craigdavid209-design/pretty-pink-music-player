from pathlib import Path
import json, warnings, sys
import numpy as np
import librosa
from sklearn.decomposition import NMF
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
warnings.filterwarnings('ignore')

AUDIO_EXT={'.flac','.wav','.mp3','.m4a','.ogg','.aac'}

def safe_entropy(w):
    w=np.maximum(np.asarray(w,float),0)
    s=w.sum()
    if s<=0:return 0.0,1.0
    p=w/s;p=p[p>0]
    h=float(-(p*np.log(p)).sum())
    return h,float(np.exp(h))

def robust_stats(x):
    x=np.asarray(x,float);x=x[np.isfinite(x)]
    if x.size==0:return dict(mean=None,p10=None,p50=None,p90=None)
    return dict(mean=float(np.mean(x)),p10=float(np.percentile(x,10)),p50=float(np.percentile(x,50)),p90=float(np.percentile(x,90)))

def analyze(path):
    # Research-only bounded-rate analysis; original playback PCM is never replaced.
    y,sr=librosa.load(path,sr=11025,mono=False,dtype=np.float32)
    if y.ndim==1:
        y=np.stack([y,y])
    elif y.shape[0]>2:
        y=y[:2]
    mono=np.mean(y,axis=0)
    duration=len(mono)/sr
    rms_l=float(np.sqrt(np.mean(y[0]**2)+1e-20)); rms_r=float(np.sqrt(np.mean(y[1]**2)+1e-20))
    mid=(y[0]+y[1])*0.5; side=(y[0]-y[1])*0.5
    mid_e=float(np.mean(mid**2)); side_e=float(np.mean(side**2))
    corr=float(np.corrcoef(y[0],y[1])[0,1]) if np.std(y[0])>1e-9 and np.std(y[1])>1e-9 else 1.0

    n_fft=1024;hop=512
    D=librosa.stft(mono,n_fft=n_fft,hop_length=hop,window='hann')
    mag=np.abs(D)+1e-10
    harm,perc=librosa.decompose.hpss(mag,margin=(2.0,2.0))
    residual=np.maximum(mag-harm-perc,0)
    eall=float(np.sum(mag**2)); eh=float(np.sum(harm**2)); ep=float(np.sum(perc**2)); er=float(np.sum(residual**2))
    norm=max(eall,1e-20)

    mel=librosa.feature.melspectrogram(S=mag**2,sr=sr,n_mels=64,fmin=30,fmax=sr/2)
    mel_log=np.log1p(mel/np.maximum(np.median(mel),1e-12))
    # NMF is a source-texture factorizer here, explicitly NOT stem truth.
    X=np.maximum(mel_log,0).T
    if len(X)>1200:
        idx=np.linspace(0,len(X)-1,1200).astype(int); Xfit=X[idx]
    else:Xfit=X
    rank=min(8,max(2,min(Xfit.shape)-1))
    nmf=NMF(n_components=rank,init='nndsvda',random_state=209,max_iter=100,tol=1e-4)
    W=nmf.fit_transform(Xfit); H=nmf.components_
    comp_energy=W.sum(axis=0)*np.maximum(H.sum(axis=1),1e-12)
    _,effective=safe_entropy(comp_energy)
    dominance=float(np.max(comp_energy)/np.sum(comp_energy)) if comp_energy.sum()>0 else 1.0
    recon=float(nmf.reconstruction_err_/max(np.linalg.norm(Xfit),1e-12))

    # Acoustic-regime diversity only: these clusters are not singer/instrument labels.
    mfcc=librosa.feature.mfcc(y=mono,sr=sr,n_mfcc=13,n_fft=1024,hop_length=1024)
    d1=librosa.feature.delta(mfcc); feat=np.vstack([mfcc,d1]).T
    block=max(1,int(2*sr/1024))
    emb=[]
    for i in range(0,len(feat)-block+1,block):
        emb.append(np.mean(feat[i:i+block],axis=0))
    emb=np.asarray(emb)
    best_k=1;best_sil=-1.0
    if len(emb)>=8:
        z=(emb-emb.mean(axis=0))/(emb.std(axis=0)+1e-6)
        for k in range(2,min(6,len(z)-1)+1):
            lab=KMeans(n_clusters=k,random_state=209,n_init=10).fit_predict(z)
            if len(set(lab))<2:continue
            s=float(silhouette_score(z,lab))
            if s>best_sil: best_sil=s;best_k=k

    centroid=librosa.feature.spectral_centroid(S=mag,sr=sr)[0]
    flatness=librosa.feature.spectral_flatness(S=mag)[0]
    rolloff=librosa.feature.spectral_rolloff(S=mag,sr=sr,roll_percent=.85)[0]
    onset=librosa.onset.onset_strength(y=mono,sr=sr,hop_length=hop)
    onsets=librosa.onset.onset_detect(onset_envelope=onset,sr=sr,hop_length=hop,units='time')
    onset_rate=float(len(onsets)/(duration/60)) if duration>0 else 0
    chroma=librosa.feature.chroma_stft(S=mag,sr=sr)
    cp=np.mean(chroma,axis=1)+1e-12; cp/=cp.sum(); chroma_entropy=float(-(cp*np.log(cp)).sum()/np.log(12))

    return {
      'file':Path(path).name,'durationSeconds':duration,'analysisSampleRate':sr,
      'stereo':{'correlation':corr,'sideToMidEnergy':side_e/max(mid_e,1e-20),'leftRightRmsRatio':rms_l/max(rms_r,1e-20)},
      'layerEvidence':{'harmonicEnergyRatio':eh/norm,'percussiveEnergyRatio':ep/norm,'unassignedEnergyRatio':er/norm},
      'textureFactorization':{'rank':rank,'effectiveComponents':effective,'dominantComponentFraction':dominance,'normalizedReconstructionError':recon},
      'acousticRegimes':{'bestClusterCount':best_k,'silhouette':None if best_sil<0 else best_sil,'windowSeconds':2.0,'claim':'acoustic-regime diversity only; not speaker or instrument identity'},
      'spectralCentroidHz':robust_stats(centroid),'spectralRolloff85Hz':robust_stats(rolloff),'spectralFlatness':robust_stats(flatness),
      'onsetRatePerMinute':onset_rate,'chromaEntropy':chroma_entropy,
      'interpretationLimit':'Read-only mixture descriptors. NMF/HPSS/clusters are hypotheses, not isolated-source ground truth.'
    }

if __name__=='__main__':
    out=[]
    for arg in sys.argv[1:]:
      p=Path(arg)
      if p.suffix.lower() in AUDIO_EXT:
        print('analyzing',p.name,flush=True)
        try:out.append(analyze(p))
        except Exception as e:out.append({'file':p.name,'error':repr(e)})
    print(json.dumps(out,indent=2))
