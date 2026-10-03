#!/usr/bin/env python3
"""Pretty Pink Vocal Presence School v3 research trainer/evaluator.

Purpose: learn a tiny, interpretable, phone-friendly *voice-presence* student from
public frame/segment truth while preserving Pretty Pink's epistemic boundary:
voice presence != lyric intelligibility, singer identity, or playback authority.

The student uses only features that can be collected from the same FFT / envelope
work already performed during Pretty Pink's verified scan. It is a research tool,
not production playback code.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import librosa
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

AUDIO_EXT = {'.wav', '.flac', '.ogg', '.mp3', '.m4a'}
FEATURE_NAMES = [
    'active',
    'band_120_300', 'band_300_500', 'band_500_900', 'band_900_1400',
    'band_1400_2200', 'band_2200_3500', 'band_3500_5000', 'band_5000_8000',
    'tonal_concentration', 'spectral_centroid', 'spectral_flux', 'envelope_modulation',
    'center_fraction', 'band_motion', 'vowel_peakiness', 'mid_fraction', 'articulation_fraction',
]


def u(x):
    return np.clip(x, 0.0, 1.0)


def _find_audio(root: Path) -> List[Path]:
    return sorted([p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in AUDIO_EXT])


def _find_labels(root: Path) -> Dict[str, Path]:
    out = {}
    for p in root.rglob('*.lab'):
        out[p.stem.lower()] = p
    return out


def _parse_label_file(path: Path) -> List[Tuple[float, float, bool]]:
    segs = []
    for raw in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        raw = raw.strip()
        if not raw or raw.startswith('#'):
            continue
        parts = raw.split()
        if len(parts) < 3:
            continue
        try:
            a, b = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        label = ' '.join(parts[2:]).strip().lower()
        voice = label in {'sing', 'singer', 'voice', 'vocal', 'vocals', '1', 'true'} or label.startswith('sing')
        segs.append((a, b, voice))
    return segs


def _discover_splits(root: Path, audio: Sequence[Path]) -> Dict[str, str]:
    """Return stem->split. Prefer explicit filelists, then path names, then deterministic song split."""
    stem_to_audio = {p.stem.lower(): p for p in audio}
    mapping: Dict[str, str] = {}
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in {'', '.txt', '.lst', '.list'}:
            continue
        low = p.name.lower()
        split = 'train' if 'train' in low else 'valid' if ('valid' in low or 'dev' in low) else 'test' if 'test' in low else None
        if not split:
            continue
        try:
            lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
        except OSError:
            continue
        for line in lines:
            token = line.strip().split()[0] if line.strip() else ''
            token = Path(token).stem.lower()
            if token.endswith('.trs'):
                token = token[:-4]
            if token in stem_to_audio:
                mapping[token] = split
    for stem, p in stem_to_audio.items():
        if stem in mapping:
            continue
        parts = [x.lower() for x in p.parts]
        if 'train' in parts:
            mapping[stem] = 'train'
        elif 'valid' in parts or 'validation' in parts or 'dev' in parts:
            mapping[stem] = 'valid'
        elif 'test' in parts:
            mapping[stem] = 'test'
    if len(mapping) >= max(3, int(.8 * len(audio))):
        return mapping
    stems = sorted(stem_to_audio)
    for i, stem in enumerate(stems):
        frac = (i + .5) / len(stems)
        mapping[stem] = 'train' if frac < 61/93 else ('valid' if frac < 77/93 else 'test')
    return mapping


def _overlap_voice_fraction(start: float, end: float, segs: Sequence[Tuple[float,float,bool]]) -> float:
    dur = max(1e-9, end - start)
    voice = 0.0
    for a, b, is_voice in segs:
        if b <= start or a >= end:
            continue
        if is_voice:
            voice += max(0.0, min(end, b) - max(start, a))
    return min(1.0, voice / dur)


def _triple_peak(power: np.ndarray, mask: np.ndarray) -> np.ndarray:
    idx = np.flatnonzero(mask)
    if len(idx) < 3:
        return np.zeros(power.shape[1], dtype=np.float64)
    sub = power[idx]
    total = sub.sum(axis=0) + 1e-12
    tri = sub[:-2] + sub[1:-1] + sub[2:]
    return np.max(tri, axis=0) / total


def extract_track_features(path: Path, sr: int = 16000, win_s: float = .5) -> Tuple[np.ndarray, np.ndarray]:
    """Return features [windows,F] and center times.

    Spectral evidence is sampled every 100 ms from 20 ms Hann windows, then
    aggregated into 500 ms windows. This mirrors the phone design's cheap cadence
    without claiming bit/numeric parity with Android.
    """
    y, _ = librosa.load(path, sr=sr, mono=False)
    if y.ndim == 1:
        y = np.stack([y, y])
    elif y.shape[0] > 2:
        y = y[:2]
    n_samples = y.shape[1]
    n500 = int(sr * win_s)
    if n_samples < n500:
        return np.empty((0, len(FEATURE_NAMES))), np.empty(0)

    mono = y.mean(axis=0)
    fft_win = max(128, int(round(sr * .020)))
    hop = max(1, int(round(sr * .100)))
    n_fft = 1
    while n_fft < fft_win:
        n_fft <<= 1
    D = np.abs(librosa.stft(mono, n_fft=n_fft, win_length=fft_win, hop_length=hop, window='hann', center=False)) ** 2 + 1e-15
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    t_spec = (np.arange(D.shape[1]) * hop + fft_win/2) / sr
    total_spec = D.sum(axis=0) + 1e-15

    edges = [(120,300),(300,500),(500,900),(900,1400),(1400,2200),(2200,3500),(3500,5000),(5000,min(8000,sr/2-1))]
    band_fracs=[]
    for lo,hi in edges:
        if hi <= lo:
            band_fracs.append(np.zeros(D.shape[1]))
            continue
        m=(freqs>=lo)&(freqs<hi)
        band_fracs.append(D[m].sum(axis=0)/total_spec if np.any(m) else np.zeros(D.shape[1]))
    B=np.vstack(band_fracs)
    vocal_mask=(freqs>=120)&(freqs<min(8000,sr/2-1))
    tonal=u(_triple_peak(D,vocal_mask)*2.5)
    centroid=u(((freqs[:,None]*D).sum(axis=0)/(total_spec+1e-15)-250)/(5000-250))
    normB=B/(B.sum(axis=0,keepdims=True)+1e-12)
    flux=np.zeros(D.shape[1])
    if D.shape[1]>1:
        flux[1:]=u(np.sum(np.abs(np.diff(normB,axis=1)),axis=0)/1.2)

    rms_hop=max(1,int(round(sr*.020))); rms_win=rms_hop
    rms=librosa.feature.rms(y=mono,frame_length=rms_win,hop_length=rms_hop,center=False)[0]+1e-12
    t_rms=(np.arange(len(rms))*rms_hop+rms_win/2)/sr

    frame100=hop
    n100=max(0,1+(n_samples-frame100)//hop)
    center=np.zeros(n100); active100=np.zeros(n100)
    for i in range(n100):
        st=i*hop; seg=y[:,st:st+frame100]
        l=seg[0]; r=seg[1]
        mid=(l+r)*.5; side=(l-r)*.5
        me=float(np.mean(mid*mid)); se=float(np.mean(side*side))
        center[i]=me/(me+se+1e-12)
        full=float(np.mean(seg*seg))
        db=10*math.log10(full+1e-12)
        active100[i]=float(u((db+75)/40))
    t100=(np.arange(n100)*hop+frame100/2)/sr

    nwin=n_samples//n500
    feats=[]; centers=[]
    for w in range(nwin):
        a=w*win_s; b=(w+1)*win_s; c=(a+b)/2
        ms=(t_spec>=a)&(t_spec<b); mr=(t_rms>=a)&(t_rms<b); mc=(t100>=a)&(t100<b)
        if not np.any(ms) or not np.any(mr) or not np.any(mc):
            continue
        bm=B[:,ms].mean(axis=1)
        act=float(active100[mc].mean()); ton=float(tonal[ms].mean()); cen=float(centroid[ms].mean()); flx=float(flux[ms].mean())
        rr=rms[mr]; mod=float(u((np.std(rr)/(np.mean(rr)+1e-12)-.05)/.75)); ctr=float(center[mc].mean())
        nb=normB[:,ms]; motion=float(u(np.mean(np.sum(np.abs(np.diff(nb,axis=1)),axis=0))/1.0)) if nb.shape[1]>1 else 0.0
        vowel_peak=max(0.0, float(max(bm[2],bm[3],bm[4]) - .5*(bm[1]+bm[5]))); vowel_peak=float(u(vowel_peak/.20))
        mid=float(u((bm[2]+bm[3]+bm[4])/.65)); art=float(u((bm[5]+bm[6])/.45))
        row=[act,*bm.tolist(),ton,cen,flx,mod,ctr,motion,vowel_peak,mid,art]
        feats.append([float(u(x)) for x in row]); centers.append(c)
    return np.asarray(feats,dtype=np.float64),np.asarray(centers,dtype=np.float64)


def v2_proxy_probability(X: np.ndarray) -> np.ndarray:
    if len(X)==0:return np.empty(0)
    active=X[:,0]; b=X[:,1]+X[:,2]; vowel=X[:,3]+X[:,4]+X[:,5]; art=X[:,6]+X[:,7]; tonal=X[:,9]; flux=X[:,11]; mod=X[:,12]; center=X[:,13]; persist=1-X[:,14]*.4
    body_s=u(b/.45); vowel_s=u(vowel/.65); art_s=u(art/.45)
    spectral=u(.36*vowel_s+.22*body_s+.22*art_s+.20*tonal); temporal=u(.43*mod+.32*flux+.25*persist); articulation=u(.48*art_s+.27*flux+.25*mod); voiced=u(.42*body_s+.34*tonal+.24*vowel_s); breathy=u(.40*vowel_s+.28*art_s+.20*mod+.12*(1-tonal))
    R=np.sort(np.vstack([spectral,temporal,articulation,voiced,breathy]),axis=0); support=(np.vstack([spectral,temporal,articulation,voiced,breathy])>=.43).sum(axis=0)
    presence=active*u(.72*(.58*R[-2]+.42*R[-3])+.18*persist+.10*np.maximum(center,.35))
    available=(active>=.28)&(support>=2)&(np.maximum.reduce([spectral,voiced,breathy])>=.45)&(np.maximum(temporal,articulation)>=.40)&(presence>=.38)
    return np.where(available,presence,0.0)


def collect_dataset(root: Path, sr: int=16000):
    audio=_find_audio(root); labels=_find_labels(root)
    if not audio: raise RuntimeError('No audio files found in Jamendo root')
    splits=_discover_splits(root,audio)
    Xs=[];ys=[];ss=[];tracks=[];matched=0
    for i,p in enumerate(audio):
        lp=labels.get(p.stem.lower())
        if lp is None: continue
        segs=_parse_label_file(lp)
        if not segs: continue
        X,t=extract_track_features(p,sr=sr)
        if len(X)==0: continue
        y=[];keep=[]
        for j,c in enumerate(t):
            frac=_overlap_voice_fraction(c-.25,c+.25,segs)
            if frac>=.80: y.append(1);keep.append(j)
            elif frac<=.20: y.append(0);keep.append(j)
        if not keep: continue
        Xs.append(X[np.asarray(keep)]);ys.append(np.asarray(y,dtype=np.int8));ss.extend([splits.get(p.stem.lower(),'train')]*len(keep));tracks.extend([p.stem]*len(keep));matched+=1
        if (i+1)%10==0: print(f'processed {i+1}/{len(audio)} audio; matched={matched}',flush=True)
    if not Xs: raise RuntimeError('No audio/label pairs matched')
    return np.vstack(Xs),np.concatenate(ys),np.asarray(ss),tracks


def metrics(y,p,thr):
    pred=(p>=thr).astype(int);tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return dict(accuracy=float(accuracy_score(y,pred)),balancedAccuracy=float(balanced_accuracy_score(y,pred)),precision=float(precision_score(y,pred,zero_division=0)),recall=float(recall_score(y,pred,zero_division=0)),f1=float(f1_score(y,pred,zero_division=0)),fpr=float(fp/max(1,fp+tn)),fnr=float(fn/max(1,fn+tp)),auc=float(roc_auc_score(y,p)) if len(np.unique(y))>1 else float('nan'),n=int(len(y)),positiveFraction=float(np.mean(y)),threshold=float(thr))


def choose_threshold(y,p):
    scored=[]
    for th in np.linspace(.35,.85,101):
        m=metrics(y,p,float(th));penalty=max(0,m['fpr']-.12)*3+max(0,.72-m['recall'])*2;score=m['f1']-.35*m['fpr']-penalty;scored.append((score,th,m))
    scored.sort(key=lambda x:x[0],reverse=True);return float(scored[0][1])


def fit_and_report(root:Path,outdir:Path,sr:int=16000):
    outdir.mkdir(parents=True,exist_ok=True);X,y,splits,tracks=collect_dataset(root,sr=sr);counts={k:int(np.sum(splits==k)) for k in ['train','valid','test']};print('window counts',counts,flush=True)
    tr=splits=='train';va=splits=='valid';te=splits=='test'
    if min(tr.sum(),va.sum(),te.sum())<100: raise RuntimeError(f'Insufficient split windows: {counts}')
    scaler=StandardScaler().fit(X[tr]);Xtr=scaler.transform(X[tr]);Xv=scaler.transform(X[va]);Xt=scaler.transform(X[te])
    model=LogisticRegression(C=.35,class_weight='balanced',max_iter=2000,solver='lbfgs',random_state=209).fit(Xtr,y[tr])
    pv=model.predict_proba(Xv)[:,1];pt=model.predict_proba(Xt)[:,1];th=choose_threshold(y[va],pv)
    report={'schema':'pretty-pink-vocal-presence-school-v3-jamendo-v1','truthBoundary':'VOICE_PRESENCE_ONLY_NOT_LYRIC_INTELLIGIBILITY_NOT_SINGER_ID_NOT_PLAYBACK_AUTHORITY','dataset':{'tracksMatched':len(set(tracks)),'windows':int(len(y)),'splits':counts,'sampleRate':sr},'featureNames':FEATURE_NAMES,'validation':metrics(y[va],pv,th),'test':metrics(y[te],pt,th),'threshold':th}
    bval=v2_proxy_probability(X[va]);btest=v2_proxy_probability(X[te]);bth=choose_threshold(y[va],bval);report['v2ProxyValidation']=metrics(y[va],bval,bth);report['v2ProxyTest']=metrics(y[te],btest,bth);report['v2ProxyThreshold']=bth
    model_json={'schema':'pretty-pink-vocal-presence-student-v3-linear-1','authority':0,'observeOnly':True,'lyricIntelligibility':'UNKNOWN','featureNames':FEATURE_NAMES,'mean':[float(x) for x in scaler.mean_],'scale':[float(x) for x in scaler.scale_],'coef':[float(x) for x in model.coef_[0]],'intercept':float(model.intercept_[0]),'voiceThreshold':th,'noVoiceThreshold':min(.35,max(.15,1-th)),'temporalSmoothing':'0.25*prev + 0.50*current + 0.25*next; full-scan evidence only'}
    (outdir/'jamendo-v3-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');(outdir/'vocal-presence-student-v3.json').write_text(json.dumps(model_json,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True);return report,model_json


def synthetic_impostor_exam(model_json):
    mean=np.asarray(model_json['mean']);scale=np.asarray(model_json['scale']);coef=np.asarray(model_json['coef']);inter=float(model_json['intercept']);th=float(model_json['voiceThreshold'])
    def prob(row):
        z=np.dot((np.asarray(row)-mean)/scale,coef)+inter;return float(1/(1+math.exp(-float(np.clip(z,-40,40)))))
    cases={'sustained_harmonic_pad':[.9,.08,.12,.18,.18,.16,.12,.08,.05,.94,.35,.05,.12,.9,.04,.50,.75,.45],'vibrato_guitar_like':[.9,.08,.10,.12,.15,.16,.14,.14,.08,.88,.48,.32,.78,.78,.45,.42,.60,.60],'woodwind_like':[.85,.05,.10,.20,.22,.18,.12,.07,.03,.92,.30,.20,.72,.85,.24,.72,.90,.35],'bright_percussive':[.9,.02,.03,.05,.07,.10,.20,.28,.25,.20,.78,.95,.25,.45,.90,.05,.20,.95],'wide_synth_lead':[.9,.05,.08,.15,.17,.17,.15,.12,.08,.86,.50,.28,.70,.35,.44,.55,.72,.60]}
    ps={k:prob(v) for k,v in cases.items()};confident=sum(p>=th for p in ps.values());return {'cases':ps,'voiceThreshold':th,'confidentVoiceCases':confident,'totalCases':len(ps),'pass':confident<=1}


def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);p=sub.add_parser('train-eval');p.add_argument('root');p.add_argument('outdir');p.add_argument('--sr',type=int,default=16000);p=sub.add_parser('stress');p.add_argument('model');p.add_argument('output');args=ap.parse_args()
    if args.cmd=='train-eval':
        report,model=fit_and_report(Path(args.root),Path(args.outdir),args.sr);stress=synthetic_impostor_exam(model);(Path(args.outdir)/'synthetic-impostor-report.json').write_text(json.dumps(stress,indent=2));print(json.dumps(stress,indent=2));
        if not stress['pass']: raise SystemExit('Synthetic impostor gate failed')
    else:
        model=json.loads(Path(args.model).read_text());stress=synthetic_impostor_exam(model);Path(args.output).write_text(json.dumps(stress,indent=2));print(json.dumps(stress,indent=2));
        if not stress['pass']: raise SystemExit('Synthetic impostor gate failed')

if __name__=='__main__':main()
