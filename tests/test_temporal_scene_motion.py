import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from temporal_scene_motion import temporal_scene_motion

SR=11025
SECONDS=24
T=np.arange(SR*SECONDS)/SR
BASE=(.2*np.sin(2*np.pi*220*T)).astype(np.float32)

stable=np.stack([BASE,BASE])

b=(.16*np.sin(2*np.pi*660*T)).astype(np.float32)
click=np.zeros_like(BASE)
for p in np.arange(12.1,SECONDS,.4):
    i=int(p*SR); n=min(80,len(BASE)-i)
    if n>0: click[i:i+n]+=.6*np.hanning(n).astype(np.float32)
left=BASE.copy(); right=BASE.copy(); mask=T>=12
left[mask]=BASE[mask]+b[mask]+click[mask]
right[mask]=BASE[mask]-.7*b[mask]+.8*click[mask]
abrupt=np.stack([left,right])

amp=(.7+.3*np.sin(2*np.pi*T/SECONDS)).astype(np.float32)
mod=(.12*np.sin(2*np.pi*(220+440*(T/SECONDS))*T)).astype(np.float32)
pan=(.5+.45*np.sin(2*np.pi*T/SECONDS)).astype(np.float32)
flow=np.stack([BASE*amp+mod*pan,BASE*amp+mod*(1-pan)])

s=temporal_scene_motion(stable,SR)
a=temporal_scene_motion(abrupt,SR)
f=temporal_scene_motion(flow,SR)

assert s['profile']=='LOW_MOTION', s
assert s['peakMotion'] < 0.02, s
assert s['abruptTransitionCount']==0, s
assert a['profile']=='SPARSE_ABRUPT_CHANGES', a
assert a['abruptTransitionCount']>=1, a
assert 10.0 <= a['eventTimesSeconds'][0] <= 14.0, a
assert a['peakMotion'] > f['peakMotion'] > s['peakMotion'], (s,a,f)
assert f['profile'] in {'MODERATE_MOTION','SUSTAINED_MOTION'}, f
assert 'not source identity' in a['claim']
print('PASS: temporal scene motion distinguishes stable, abrupt, and smoothly changing synthetic scenes')
