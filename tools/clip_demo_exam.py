"""Run Vocal School v2 on the public Cadenza CLIP demo.

Downloaded data is ephemeral CI input and is never committed. The report contains
only derived metrics/metadata. This is a research calibration, not a production gate.
"""
from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
import numpy as np
import librosa
from scipy.stats import spearmanr
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vocal_school_v2 import evaluate

AUDIO_EXT={'.wav','.flac','.mp3','.ogg','.m4a'}

def unit(x): return float(np.clip(x,0,1))
def sig(x): return float(1/(1+np.exp(-x)))

def analyze(path: Path, sr=11025, win_s=.5):
    y,_=librosa.load(path,sr=sr,mono=False)
    if y.ndim==1: y=np.stack([y,y])
    elif y.shape[0]>2: y=y[:2]
    n=max(2048,int(sr*win_s)); base=[]
    for st in range(0,y.shape[1]-n+1,n):
        seg=y[:,st:st+n]; mono=seg.mean(0); mid=(seg[0]+seg[1])*.5; side=(seg[0]-seg[1])*.5
        db=20*np.log10(np.sqrt(np.mean(mono**2)+1e-12)+1e-12)
        D=np.abs(librosa.stft(mono,n_fft=1024,hop_length=256,window='hann'))**2+1e-12
        f=librosa.fft_frequencies(sr=sr,n_fft=1024); total=D.sum()
        def frac(lo,hi):
            m=(f>=lo)&(f<hi); return float(D[m].sum()/total) if m.any() else 0.0
        body,form,art,air=frac(120,500),frac(500,2000),frac(2000,5000),frac(5000,sr/2+1)
        flat=float(np.mean(librosa.feature.spectral_flatness(S=np.sqrt(D)))); tonal=unit((.42-flat)/.38)
        mag=np.sqrt(D); norm=mag/(np.sqrt((mag**2).sum(0,keepdims=True))+1e-12)
        flux=float(np.mean(np.sqrt(np.sum(np.diff(norm,axis=1)**2,axis=0)))) if norm.shape[1]>1 else 0
        flux_s=unit((flux-.04)/.28)
        hop=max(1,int(sr*.02)); env=np.array([np.sqrt(np.mean(mono[j:j+hop]**2)+1e-12) for j in range(0,len(mono)-hop+1,hop)])
        mod=float(np.std(env)/(np.mean(env)+1e-9)) if len(env)>2 else 0; mod_s=unit((mod-.12)/.65)
        me=float(np.mean(mid**2)); se=float(np.mean(side**2)); center=unit((me/(me+se+1e-12)-.30)/.65)
        base.append([db,body,form,art,air,tonal,mod_s,flux_s,center,1-center,flat])
    if not base: return {'windows':0,'availableFraction':0,'riskP90':None,'riskMedian':None}
    a=np.asarray(base); med_db=np.median(a[:,0]); prelim=[]
    for r in a:
        db,body,form,art,air,tonal,mod_s,flux_s,center,side_s,flat=r
        active=sig((db-(med_db-18))/5); body_s=unit((body-.03)/.25); vowel_s=unit((form-.08)/.30); art_s=unit((art-.02)/.24)
        prelim.append(unit(active*(.28*vowel_s+.22*body_s+.18*art_s+.16*tonal+.16*mod_s)))
    prelim=np.asarray(prelim); results=[]
    for i,r in enumerate(a):
        db,body,form,art,air,tonal,mod_s,flux_s,center,side_s,flat=r
        active=sig((db-(med_db-18))/5); body_s=unit((body-.03)/.25); vowel_s=unit((form-.08)/.30); art_s=unit((art-.02)/.24); air_s=unit(air/.10)
        persistence=float(np.mean(prelim[max(0,i-2):min(len(prelim),i+3)]))
        density=unit(.38*flat+.22*art_s+.18*vowel_s+.12*active+.10*side_s)
        e=dict(active=active,body=body_s,vowel=vowel_s,articulation_band=art_s,air=air_s,
               tonal=tonal,modulation=mod_s,flux=flux_s,center=center,broadband_density=density,
               side_activity=side_s,persistence=persistence)
        results.append(evaluate(e))
    avail=[r for r in results if r.available]
    risks=np.array([r.risk for r in avail],float)
    return {'windows':len(results),'availableFraction':len(avail)/len(results),
            'riskMedian':float(np.median(risks)) if len(risks) else None,
            'riskP90':float(np.percentile(risks,90)) if len(risks) else None,
            'elevatedFraction':sum('ELEVATED' in r.label.value or 'HIGH' in r.label.value for r in results)/len(results),
            'meanPresence':float(np.mean([r.presence for r in results])),
            'meanConfidence':float(np.mean([r.confidence for r in results]))}

def _rows_from_json(obj):
    if isinstance(obj,list):
        for x in obj:
            yield from _rows_from_json(x)
    elif isinstance(obj,dict):
        if 'signal' in obj and ('correctness' in obj or ('words_correct' in obj and 'n_words' in obj)):
            yield obj
        for v in obj.values():
            if isinstance(v,(list,dict)):
                yield from _rows_from_json(v)

def metadata_scores(root: Path):
    candidates=[]
    # Current CLIP metadata is JSON: signal is the audio identifier and correctness
    # is the listener word-correct ratio. Keep CSV fallback for forward compatibility.
    for p in root.rglob('*.json'):
        try:
            obj=json.loads(p.read_text(encoding='utf-8-sig'))
            for row in _rows_from_json(obj):
                ident=str(row.get('signal','')).strip()
                score=row.get('correctness')
                if score is None and row.get('n_words'):
                    score=float(row.get('words_correct',0))/float(row['n_words'])
                if ident and score is not None:
                    candidates.append((ident,float(score)))
        except Exception:
            pass
    for p in root.rglob('*.csv'):
        try:
            with p.open(newline='',encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    keys={k.lower():k for k in row}
                    score_key=next((orig for low,orig in keys.items() if any(t in low for t in ('correctness','intellig','word_correct','wcr'))),None)
                    id_key=next((orig for low,orig in keys.items() if any(t in low for t in ('signal','file','audio','sample','scene','id'))),None)
                    if score_key and id_key:
                        try: candidates.append((str(row[id_key]),float(row[score_key])))
                        except Exception: pass
        except Exception:
            pass
    # One signal can appear in listener-level rows; aggregate listener correctness.
    by={}
    for ident,score in candidates:
        by.setdefault(ident,[]).append(score)
    return [(ident,float(np.mean(vals))) for ident,vals in by.items()]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('output');args=ap.parse_args()
    root=Path(args.root); audio=[p for p in root.rglob('*') if p.suffix.lower() in AUDIO_EXT]
    scores=metadata_scores(root); score_map={str(k).lower():v for k,v in scores};items=[]
    for p in sorted(audio):
        m=analyze(p); stem=p.stem.lower(); ident=stem[:-7] if stem.endswith('_unproc') else stem
        score=score_map.get(ident)
        m.update(file=str(p.relative_to(root)),listenerScore=score);items.append(m)
    # Evaluate processed signals only against listener scores; unprocessed files are useful
    # acoustic controls but do not represent the exact listener stimulus when processing differs.
    matched=[x for x in items if '/signals/' in ('/'+x['file'].replace('\\','/')) and x['listenerScore'] is not None and x['riskP90'] is not None]
    rho=None
    if len(matched)>=3:
        rho=float(spearmanr([x['riskP90'] for x in matched],[1-x['listenerScore'] for x in matched]).statistic)
    report={'audioFiles':len(audio),'metadataScoreCandidates':len(scores),'matchedProcessedScores':len(matched),
            'riskVsListenerDifficultySpearman':rho,
            'note':'Tiny public demo correlation is descriptive only; it is not a promotion gate.',
            'items':items}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True);Path(args.output).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in report if k!='items'},indent=2))
    if not audio: raise SystemExit('No CLIP demo audio found')
    if len(matched)==0: raise SystemExit('No listener correctness scores matched processed CLIP demo signals')
if __name__=='__main__': main()
