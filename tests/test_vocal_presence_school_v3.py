import tempfile, sys
from pathlib import Path
import numpy as np
import soundfile as sf
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'tools'))
from vocal_presence_school_v3 import _parse_label_file, extract_track_features, FEATURE_NAMES, _overlap_voice_fraction

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    lab=td/'x.lab';lab.write_text('0.0 1.0 nosing\n1.0 2.0 sing\n2.0 3.0 no_voice\n')
    seg=_parse_label_file(lab)
    assert len(seg)==3 and seg[0][2] is False and seg[1][2] is True and seg[2][2] is False
    assert abs(_overlap_voice_fraction(.75,1.25,seg)-.5)<1e-9
    sr=16000;t=np.arange(sr*2)/sr
    y=(.12*np.sin(2*np.pi*220*t*(1+.005*np.sin(2*np.pi*6*t)))+.04*np.sin(2*np.pi*440*t)).astype(np.float32)
    wav=td/'tone.wav';sf.write(wav,np.stack([y,y],axis=1),sr)
    X,centers=extract_track_features(wav,sr=sr)
    assert X.shape[1]==len(FEATURE_NAMES)==18
    assert len(X)==len(centers)>=3
    assert np.all(np.isfinite(X)) and np.all((X>=0)&(X<=1))
    wav2=td/'pan.wav';sf.write(wav2,np.stack([y,np.zeros_like(y)],axis=1),sr)
    X2,_=extract_track_features(wav2,sr=sr)
    assert np.mean(X2[:,13]) < np.mean(X[:,13])
print('VocalPresenceSchoolV3: local truth boundaries passed')
