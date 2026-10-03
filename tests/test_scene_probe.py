import json, tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
import sys
from pathlib import Path as _Path
sys.path.insert(0,str(_Path(__file__).resolve().parents[1]/"tools"))
from scene_probe import analyze

SR=22050

def write(path, x): sf.write(path, x.T, SR, subtype='FLOAT')

def tone(freq, seconds, amp=.25):
    t=np.arange(int(SR*seconds))/SR
    x=amp*(np.sin(2*np.pi*freq*t)+.35*np.sin(2*np.pi*2*freq*t))
    return x.astype(np.float32)

def clicks(seconds, step=.25, amp=.7):
    x=np.zeros(int(SR*seconds),np.float32)
    for p in np.arange(.1,seconds,step):
        i=int(p*SR); n=min(100,len(x)-i)
        if n>0:x[i:i+n]+=amp*np.hanning(n).astype(np.float32)
    return x

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    a=tone(220,12)
    mono=np.stack([a,a])
    write(td/'single.wav',mono)
    r1=analyze(td/'single.wav')

    b=tone(660,12,.18)
    p=clicks(12)
    left=a+b+p; right=a-.7*b+p*.8
    write(td/'layered.wav',np.stack([left,right]))
    r2=analyze(td/'layered.wav')

    assert r1['stereo']['sideToMidEnergy'] < 1e-5, r1['stereo']
    assert r2['stereo']['sideToMidEnergy'] > 0.02, r2['stereo']
    assert r2['layerEvidence']['percussiveEnergyRatio'] > r1['layerEvidence']['percussiveEnergyRatio'] + 0.01, (r1['layerEvidence'],r2['layerEvidence'])
    assert r2['textureFactorization']['normalizedReconstructionError'] > 0
    assert 'not speaker or instrument identity' in r2['acousticRegimes']['claim']
    assert 'not isolated-source ground truth' in r2['interpretationLimit']
    print(json.dumps({'status':'PASS','single':r1,'layered':r2},indent=2))
