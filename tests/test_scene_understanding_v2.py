import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from scene_understanding_v2 import understand_scene_v2

PROBE={
 'stereo':{'sideToMidEnergy':0.11,'correlation':0.71},
 'textureFactorization':{'effectiveComponents':7.8,'dominantComponentFraction':0.18,'normalizedReconstructionError':0.31},
 'acousticRegimes':{'bestClusterCount':3,'silhouette':0.24},
 'layerEvidence':{'harmonicEnergyRatio':0.38,'percussiveEnergyRatio':0.14,'unassignedEnergyRatio':0.12},
 'onsetRatePerMinute':112.0,'spectralFlatness':{'p50':0.06},
 'temporalSceneMotion':{'medianMotion':0.16,'p90Motion':0.42,'peakMotion':0.72,'sectionContrast':0.26,'abruptTransitionCount':4,'profile':'SUSTAINED_AND_PUNCTUATED_MOTION'}
}
r=understand_scene_v2(PROBE)
assert r['schemaVersion']==2
assert r['authority']['audioMutationAllowed'] is False
assert r['authority']['playbackPlanInfluenceAllowed'] is False
assert r['measured']['texture']['authority']=='DIAGNOSTIC_ONLY'
assert 'MULTIPLE_TEXTURE_FACTORS' not in r['measured']['flags']
assert 'SUSTAINED_SCENE_MOTION' in r['measured']['flags']
assert 'ABRUPT_SCENE_CHANGE_EVIDENCE' in r['measured']['flags']
assert 'HIGH_SECTION_CONTRAST' in r['measured']['flags']
assert r['measured']['temporalScene']['profile']=='SUSTAINED_AND_PUNCTUATED_MOTION'
assert r['semantic']['status']=='UNAVAILABLE'
assert r['vocalTimbres']['status']=='UNAVAILABLE'
print('PASS: SUL round-2 wrapper adds temporal structure, demotes NMF saturation, and keeps zero playback authority')
