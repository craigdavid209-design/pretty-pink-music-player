"""Pretty Pink Voice Presence School v3 research trainer.

Trains a tiny, interpretable song-split student on Jamendo VAD public
voice/no-voice truth using only phone-feasible mixture features. The student has
ZERO playback authority; this script produces coefficients and held-out metrics
for a future shadow witness.
"""
from __future__ import annotations
import argparse, json, math, re
from pathlib import Path
import numpy as np
import librosa
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score, precision_score, recall_score, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler

AUDIO_EXT={'.ogg','.mp3','.wav','.flac','.m4a'}
FEATURES=[
 'active','body','vowel','articulation_band','air','tonal_concentration',
 'modulation','spectral_flux','center','broadband_density','side_activity','persistence',
 'harmonic_comb','pitch_motion','envelope_motion','upper_flatness'
]

def u(x): return float(np.clip(x,0,1))
def normstem(s):
    s=Path(str(s)).stem.lower()
    return re.sub(r'[^a-z0-9]+','',s)

def parse_label_file(path:Path):
    seg=[]
    for line in path.read_text(errors='ignore').splitlines():
        line=line.strip()
        if not line or line.startswith('#'): continue
        p=re.split(r'\s+',line)
        nums=[]; idx=[]
        for i,t in enumerate(p):
            try: nums.append(float(t)); idx.append(i)
            except: pass
        if len(nums)<2: continue
        a,b=nums[0],nums[1]
        lab=' '.join(p[idx[1]+1:]).strip().lower() if idx[1]+1<len(p) else ''
        if not lab and len(nums)>=3: lab=str(int(nums[2]))
        neg=any(k in lab for k in ('no voice','no_voice','novoice','nonvoice','no-voc','nosong','no_sing','nosing','instrument','non-vocal','nonvocal'))
        pos=(lab in {'1','true','voice','sing','singing','vocal','vocals'}) or any(k in lab for k in ('voice','sing','vocal'))
        y=0 if neg else 1 if pos else None
        if y is not None and b>a: seg.append((float(a),float(b),y))
    return seg

def discover(root:Path):
    audio=[p for p in root.rglob('*') if p.suffix.lower() in AUDIO_EXT]
    labs=[p for p in root.rglob('*') if p.suffix.lower() in {'.lab','.txt','.trs'} and 'list' not in p.name.lower()]
    by={}
    for p in labs: by.setdefault(normstem(p.name),[]).append(p)
    pairs=[]
    for a in audio:
        cand=by.get(normstem(a.name),[]); chosen=None
        for c in cand:
            seg=parse_label_file(c)
            if seg: chosen=(c,seg); break
        if chosen: pairs.append((a,chosen[0],chosen[1]))
    split={}
    for name,aliases in [('train',('train','jam_train_list.txt')),('valid',('valid','validation','jam_valid_list.txt')),('test',('test','jam_test_list.txt'))]:
        f=None
        for p in root.rglob('*'):
            if p.is_file() and p.name.lower() in aliases: f=p; break
        if f:
            for line in f.read_text(errors='ignore').splitlines():
                if line.strip(): split[normstem(line.strip())]=name
    if not split:
        keys=sorted({normstem(a.name) for a,_,_ in pairs})
        for i,k in enumerate(keys): split[k]='train' if i<61 else 'valid' if i<77 else 'test'
        split_source='deterministic-61-16-16-fallback'
    else: split_source='archive-manifest'
    return pairs,split,split_source

def label_at(seg,t):
    for a,b,y in seg:
        if a<=t<b: return y
    return None

def harmonic_candidates(sr,nfft):
    out=[]
    for f0 in np.arange(90.0,401.0,20.0):
        bins=[];weights=[]
        for h in range(1,9):
            target=f0*h
            if target>5000: break
            j=int(round(target*nfft/sr))
            if 1<=j<nfft//2:
                bins.append(j);weights.append(1/(h**0.35))
        out.append((float(f0),np.asarray(bins,int),np.asarray(weights,float)))
    return out

def harmonic_score(power,freqs,candidates):
    total=float(power[(freqs>=80)&(freqs<=5000)].sum())+1e-12
    best=0.0;best_f=0.0
    for f0,bins,weights in candidates:
        if bins.size==0: continue
        lo=np.maximum(0,bins-1);hi=np.minimum(len(power)-1,bins+1)
        vals=power[lo]+power[bins]+power[hi]
        s=float(np.sum(vals*weights))
        if s>best: best=s;best_f=f0
    return u((best/total)*2.2),best_f

def song_features(path:Path, seg, sr=11025, win_s=.5):
    y,_=librosa.load(path,sr=sr,mono=False)
    if y.ndim==1: y=np.stack([y,y])
    elif y.shape[0]>2: y=y[:2]
    n=int(round(sr*win_s));sub=int(round(sr*.1));nfft=2048
    freqs=np.fft.rfftfreq(nfft,1/sr);candidates=harmonic_candidates(sr,nfft)
    X=[];Y=[];prev_spec=None;prev_f0=None;persist=0.0
    for st in range(0,y.shape[1]-n+1,n):
        center_t=(st+n/2)/sr;lab=label_at(seg,center_t)
        if lab is None: continue
        chunk=y[:,st:st+n];mono=chunk.mean(0);mid=(chunk[0]+chunk[1])*.5;side=(chunk[0]-chunk[1])*.5
        rms=float(np.sqrt(np.mean(mono**2)+1e-12));db=20*np.log10(rms+1e-12);active=u((db+75)/40)
        band_rows=[];tonal_rows=[];flux_rows=[];harm_rows=[];f0_rows=[];flat_rows=[];env=[]
        for ss in range(0,n-sub+1,sub):
            z=mono[ss:ss+sub];spec=np.abs(np.fft.rfft(z*np.hanning(len(z)),nfft))**2+1e-16;total=float(spec.sum())+1e-16
            def frac(lo,hi):
                m=(freqs>=lo)&(freqs<hi);return float(spec[m].sum()/total) if m.any() else 0.0
            b,v,a,h=frac(120,500),frac(500,2000),frac(2000,5000),frac(5000,min(9000,sr/2+1));band_rows.append((u(b/.35),u(v/.50),u(a/.28),u(h/.15)))
            m=(freqs>=120)&(freqs<=min(9000,sr/2));p=spec[m]
            triple=float(np.max(p[:-2]+p[1:-1]+p[2:])) if len(p)>=3 else float(p.sum())
            tonal_rows.append(u(triple/(float(p.sum())+1e-16)))
            ns=spec/(np.sqrt(np.sum(spec**2))+1e-16);flux_rows.append(0.0 if prev_spec is None else u(np.sqrt(np.sum((ns-prev_spec)**2))/.8));prev_spec=ns
            hs,f0=harmonic_score(spec,freqs,candidates);harm_rows.append(hs);f0_rows.append(f0)
            hi=(freqs>=2000)&(freqs<=min(8500,sr/2));q=np.sqrt(spec[hi]);flat=float(np.exp(np.mean(np.log(q+1e-12)))/(np.mean(q)+1e-12)) if q.size else 0;flat_rows.append(u(flat/.7));env.append(float(np.sqrt(np.mean(z*z)+1e-12)))
        br=np.mean(np.asarray(band_rows),axis=0);body,vowel,art,air=map(float,br);tonal=float(np.mean(tonal_rows));flux=float(np.mean(flux_rows));harmonic=float(np.mean(harm_rows));upper_flat=float(np.mean(flat_rows))
        env=np.asarray(env);mod=u((float(np.std(env))/(float(np.mean(env))+1e-9)-.05)/.65)
        me=float(np.mean(mid**2));se=float(np.mean(side**2));center=u(me/(me+se+1e-12));side_a=u(se/(me+se+1e-12));density=active*u(.50*(1-tonal)+.22*art+.16*air+.12*upper_flat)
        vocalish=active>=.28 and max(body,vowel)>=.30 and tonal>=.20;persist=min(1.0,persist+.5) if vocalish else max(0.0,persist-.5)
        f0=np.median([x for x in f0_rows if x>0]) if any(x>0 for x in f0_rows) else 0;pitch_motion=0.0 if not prev_f0 or not f0 else u(abs(math.log2(f0/prev_f0))/0.7);prev_f0=f0 or prev_f0
        bands=np.asarray(band_rows);env_motion=u(float(np.mean(np.std(bands,axis=0)))/.22)
        X.append([active,body,vowel,art,air,tonal,mod,flux,center,density,side_a,persist,harmonic,pitch_motion,env_motion,upper_flat]);Y.append(int(lab))
    return np.asarray(X,float),np.asarray(Y,int)

def metrics(y,p,score):
    tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel()
    return dict(n=int(len(y)),balancedAccuracy=float(balanced_accuracy_score(y,p)),f1=float(f1_score(y,p,zero_division=0)),precision=float(precision_score(y,p,zero_division=0)),recall=float(recall_score(y,p,zero_division=0)),falsePositiveRate=float(fp/max(1,fp+tn)),falseNegativeRate=float(fn/max(1,fn+tp)),auc=float(roc_auc_score(y,score)) if len(np.unique(y))>1 else None,confusion=dict(tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp)))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('output');args=ap.parse_args();root=Path(args.root)
    pairs,split,split_source=discover(root);sets={k:[[],[]] for k in ('train','valid','test')};songs={k:[] for k in sets}
    for a,l,seg in pairs:
        s=split.get(normstem(a.name))
        if s not in sets: continue
        X,y=song_features(a,seg)
        if len(y):sets[s][0].append(X);sets[s][1].append(y);songs[s].append(a.name)
    data={}
    for s,(xs,ys) in sets.items():
        if not xs: raise SystemExit(f'No usable {s} data; pairs={len(pairs)} splitSource={split_source}')
        data[s]=(np.vstack(xs),np.concatenate(ys))
    Xtr,ytr=data['train'];Xv,yv=data['valid'];Xt,yt=data['test'];best=None
    for C in (.03,.1,.3,1,3,10):
        sc=StandardScaler().fit(Xtr);m=LogisticRegression(C=C,max_iter=2000,class_weight='balanced').fit(sc.transform(Xtr),ytr);sv=m.predict_proba(sc.transform(Xv))[:,1]
        for th in np.arange(.30,.711,.02):
            pv=(sv>=th).astype(int);mm=metrics(yv,pv,sv);key=(mm['balancedAccuracy'],mm['f1'],-mm['falsePositiveRate'])
            if best is None or key>best[0]:best=(key,C,float(th),mm)
    _,C,th,valm=best;Xtv=np.vstack([Xtr,Xv]);ytv=np.concatenate([ytr,yv]);sc=StandardScaler().fit(Xtv);m=LogisticRegression(C=C,max_iter=2000,class_weight='balanced').fit(sc.transform(Xtv),ytv);st=m.predict_proba(sc.transform(Xt))[:,1];pt=(st>=th).astype(int);testm=metrics(yt,pt,st)
    report={'dataset':'Jamendo Corpus for Singing Voice Detection','splitSource':split_source,'songs':{k:len(v) for k,v in songs.items()},'windows':{k:int(len(data[k][1])) for k in data},'voiceFraction':{k:float(np.mean(data[k][1])) for k in data},'featureNames':FEATURES,'selectedC':C,'threshold':th,'validation':valm,'test':testm,'student':{'mean':sc.mean_.tolist(),'scale':sc.scale_.tolist(),'coefficient':m.coef_[0].tolist(),'intercept':float(m.intercept_[0])},'phoneContract':'Research-only shadow student. All features are mixture evidence; no singer identity, lyric, defect, or playback authority.','graduationCriteria':{'balancedAccuracyAtLeast':.75,'f1AtLeast':.75,'falsePositiveRateAtMost':.25}}
    report['graduatesPublicTruth']=bool(testm['balancedAccuracy']>=.75 and testm['f1']>=.75 and testm['falsePositiveRate']<=.25)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True);Path(args.output).write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='student'},indent=2))
    if not report['graduatesPublicTruth']:raise SystemExit('Student did not graduate public voice/no-voice truth; keep research-only and inspect artifact.')
if __name__=='__main__':main()
