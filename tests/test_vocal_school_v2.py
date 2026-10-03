import os,sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools')))
from vocal_school_v2 import evaluate, production_context, VocalLabel


def base(**kw):
    e=dict(active=.90,body=.70,vowel=.72,articulation_band=.68,air=.40,tonal=.72,
           modulation=.66,flux=.64,center=.78,broadband_density=.28,side_activity=.16,
           persistence=.82)
    e.update(kw); return e

r=evaluate(base())
assert r.available and r.label is VocalLabel.LIKELY_VOCAL_LOW_PRODUCTION_BURDEN
assert r.authority == 0 and r.lyric_intelligibility == 'UNKNOWN'

r=evaluate(base(air=.02,articulation_band=.50,vowel=.80,body=.78,modulation=.72))
assert r.available

r=evaluate(base(center=.30,side_activity=.60,vowel=.82,articulation_band=.64,modulation=.74,flux=.67))
assert r.available

r=evaluate(base(articulation_band=.28,modulation=.36,flux=.20,center=.38,
                broadband_density=.92,side_activity=.72,persistence=.86,vowel=.80,body=.72))
assert r.available and r.production_burden >= .27 and r.authority == 0
assert r.lyric_intelligibility == 'UNKNOWN'

r=evaluate(base(body=.05,vowel=.05,articulation_band=.95,tonal=.05,modulation=.05,
                flux=.05,persistence=.20,center=.90,broadband_density=.20,side_activity=.05))
assert not r.available

r=evaluate(base(body=.08,vowel=.12,articulation_band=.84,air=.92,tonal=.08,
                modulation=.18,flux=.92,persistence=.14,center=.52,broadband_density=.90,
                side_activity=.60))
assert not r.available

r=evaluate(base(body=.82,vowel=.70,articulation_band=.08,air=.05,tonal=.95,
                modulation=.05,flux=.06,persistence=.92,center=.76,broadband_density=.24,
                side_activity=.18))
assert not r.available

tags=production_context(base(broadband_density=.90,side_activity=.68,center=.35,flux=.18,modulation=.20))
assert 'DENSE_MIXTURE_CONTEXT' in tags and 'LAYERED_OR_WIDE_CONTEXT' in tags
assert all('REVERB' not in t and 'DEFECT' not in t for t in tags)
print('VocalSchoolV2: synthetic truth boundaries passed')
