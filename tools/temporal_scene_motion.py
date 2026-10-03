"""Pretty Pink SUL Phase-A round-2 temporal scene-motion witness.

Mixture-only, deterministic, read-only research code. It describes how the
stereo scene changes through time and is deliberately incapable of naming
sources or changing playback.
"""
from __future__ import annotations
import math
import numpy as np
import librosa


def _js_distance(p, q):
    p=np.maximum(np.asarray(p,float),1e-12); q=np.maximum(np.asarray(q,float),1e-12)
    p=p/p.sum(); q=q/q.sum(); m=.5*(p+q)
    klp=np.sum(p*np.log2(p/m)); klq=np.sum(q*np.log2(q/m))
    return float(np.sqrt(max(0.0,.5*(klp+klq))))


def _clamp01(x):
    return float(min(1.0,max(0.0,x)))


def temporal_scene_motion(y, sr, window_seconds=2.0):
    if y.ndim==1:
        y=np.stack([y,y])
    elif y.shape[0]>2:
        y=y[:2]
    win=max(2048,int(round(sr*window_seconds)))
    rows=[]
    band_edges=np.array([30,120,300,1000,2500,4000,sr/2+1.0],float)

    for start in range(0,y.shape[1]-win+1,win):
        seg=y[:,start:start+win]; mono=np.mean(seg,axis=0)
        rms=float(np.sqrt(np.mean(mono**2)+1e-20)); rms_db=float(20*np.log10(rms+1e-12))
        mid=(seg[0]+seg[1])*.5; side=(seg[0]-seg[1])*.5
        side_mid=float(np.mean(side**2)/max(np.mean(mid**2),1e-20))
        corr=float(np.corrcoef(seg[0],seg[1])[0,1]) if np.std(seg[0])>1e-9 and np.std(seg[1])>1e-9 else 1.0
        D=librosa.stft(mono,n_fft=1024,hop_length=512,window='hann')
        power=np.abs(D)**2+1e-20; mag=np.sqrt(power)
        freqs=librosa.fft_frequencies(sr=sr,n_fft=1024)
        bands=[]
        for lo,hi in zip(band_edges[:-1],band_edges[1:]):
            mask=(freqs>=lo)&(freqs<hi); bands.append(float(np.sum(power[mask]))+1e-20)
        bands=np.asarray(bands,float); bands/=bands.sum()
        flat=float(np.mean(librosa.feature.spectral_flatness(S=mag+1e-12)))
        centroid=float(np.mean(librosa.feature.spectral_centroid(S=mag,sr=sr))/(sr/2))
        onset=float(np.mean(librosa.onset.onset_strength(y=mono,sr=sr,hop_length=512)))
        rows.append((bands,rms_db,side_mid,corr,flat,centroid,onset))

    if len(rows)<2:
        return {
            'windowSeconds':window_seconds,'windowCount':len(rows),'edgeCount':0,
            'medianMotion':0.0,'p90Motion':0.0,'peakMotion':0.0,'sectionContrast':0.0,
            'abruptTransitionCount':0,'abruptTransitionRatePerMinute':0.0,
            'profile':'INSUFFICIENT_DURATION','eventTimesSeconds':[],
            'claim':'mixture scene motion only; not source identity, source count, defect detection, or playback advice'
        }

    scores=[]
    for a,b in zip(rows[:-1],rows[1:]):
        spectral=_js_distance(a[0],b[0])
        level=_clamp01(abs(a[1]-b[1])/12.0)
        spatial=_clamp01(abs(math.log1p(a[2])-math.log1p(b[2]))/0.35)
        decor=_clamp01(abs(a[3]-b[3])/0.50)
        texture=_clamp01(abs(a[4]-b[4])/0.12)
        centroid=_clamp01(abs(a[5]-b[5])/0.25)
        transient=_clamp01(abs(math.log1p(a[6])-math.log1p(b[6]))/0.80)
        scores.append(float(.30*spectral+.15*level+.15*spatial+.10*decor+.10*texture+.10*centroid+.10*transient))

    scores=np.asarray(scores,float)
    median=float(np.median(scores)); p90=float(np.percentile(scores,90)); peak=float(np.max(scores))
    contrast=float(max(0.0,p90-median))
    candidates=np.where(scores>=0.35)[0]
    kept=[]
    for i in candidates:
        i=int(i)
        if not kept or i-kept[-1]>=2: kept.append(i)
        elif scores[i]>scores[kept[-1]]: kept[-1]=i
    duration=y.shape[1]/sr
    rate=float(len(kept)/(duration/60.0)) if duration>0 else 0.0

    if len(kept)>=1 and median<0.10:
        profile='SPARSE_ABRUPT_CHANGES'
    elif median<0.08 and p90<0.16 and len(kept)==0:
        profile='LOW_MOTION'
    elif median>=0.14 and contrast>=0.18:
        profile='SUSTAINED_AND_PUNCTUATED_MOTION'
    elif median>=0.14:
        profile='SUSTAINED_MOTION'
    elif contrast>=0.18 or len(kept)>=4:
        profile='PUNCTUATED_MOTION'
    else:
        profile='MODERATE_MOTION'

    return {
        'windowSeconds':window_seconds,'windowCount':len(rows),'edgeCount':len(scores),
        'medianMotion':median,'p90Motion':p90,'peakMotion':peak,'sectionContrast':contrast,
        'abruptTransitionCount':len(kept),'abruptTransitionRatePerMinute':rate,
        'profile':profile,'eventTimesSeconds':[float((i+1)*window_seconds) for i in kept],
        'claim':'mixture scene motion only; not source identity, source count, defect detection, or playback advice'
    }
