"""Pretty Pink SUL Phase-A round-2 wrapper.

Extends the frozen Phase-A semantic/truth-boundary engine with temporal scene
motion. The v1 result remains the baseline for A/B research comparison.
"""
from __future__ import annotations
import copy
from typing import Any, Iterable, Mapping
from scene_understanding import understand_scene as understand_scene_v1, _safe_get, _score01

SUL_SCHEMA_VERSION=2


def understand_scene_v2(probe: Mapping[str,Any], teachers: Iterable[Any]=()):
    result=copy.deepcopy(understand_scene_v1(probe,teachers))
    result['schemaVersion']=SUL_SCHEMA_VERSION
    result['phase']='A_RESEARCH_SHADOW_ROUND2'
    measured=result['measured']

    # Round-2 real-music evidence showed near-ceiling NMF effective-component
    # counts across very different songs. Keep it visible, but stop treating it
    # as source count or a dominant complexity vote.
    measured['flags']=[f for f in measured['flags'] if f!='MULTIPLE_TEXTURE_FACTORS']
    measured['texture']['authority']='DIAGNOSTIC_ONLY'
    measured['texture']['claim']='NMF texture factors are not source count and do not independently establish mix complexity.'

    temporal=probe.get('temporalSceneMotion') if isinstance(probe,Mapping) else None
    temporal_available=isinstance(temporal,Mapping)
    median=_safe_get(probe,('temporalSceneMotion','medianMotion'),0.0)
    p90=_safe_get(probe,('temporalSceneMotion','p90Motion'),0.0)
    peak=_safe_get(probe,('temporalSceneMotion','peakMotion'),0.0)
    contrast=_safe_get(probe,('temporalSceneMotion','sectionContrast'),max(0.0,p90-median))
    abrupt=int(round(_safe_get(probe,('temporalSceneMotion','abruptTransitionCount'),0.0)))
    profile=temporal.get('profile','UNAVAILABLE') if temporal_available else 'UNAVAILABLE'

    if temporal_available:
        if median>=0.14: measured['flags'].append('SUSTAINED_SCENE_MOTION')
        if abrupt>=1 or peak>=0.35: measured['flags'].append('ABRUPT_SCENE_CHANGE_EVIDENCE')
        if contrast>=0.18: measured['flags'].append('HIGH_SECTION_CONTRAST')
        if median<0.08 and p90<0.16 and abrupt==0: measured['flags'].append('LOW_SCENE_MOTION')

    measured['temporalScene']={
        'available':temporal_available,'profile':profile,'medianMotion':median,'p90Motion':p90,
        'peakMotion':peak,'sectionContrast':contrast,'abruptTransitionCount':abrupt,
        'claim':'time-varying mixture structure only; not source identity, defect detection, or playback advice'
    }

    side_mid=_safe_get(probe,('stereo','sideToMidEnergy'))
    regimes=max(1,int(round(_safe_get(probe,('acousticRegimes','bestClusterCount'),1.0))))
    onset=_safe_get(probe,('onsetRatePerMinute',),0.0)
    residual=_safe_get(probe,('layerEvidence','unassignedEnergyRatio'))
    flatness=_safe_get(probe,('spectralFlatness','p50'),0.0)
    terms=[_score01(side_mid,0.01,0.20),_score01(regimes,1.0,5.0),_score01(onset,20.0,180.0),_score01(residual+flatness,0.02,0.35)]
    if temporal_available:
        terms.extend([_score01(median,0.04,0.24),_score01(p90,0.10,0.50),_score01(contrast,0.04,0.30)])
    measured['mixtureComplexity']=float(sum(terms)/len(terms))

    result['round2ResearchNotes']=[
        'Temporal scene motion is descriptive evidence, not playback advice.',
        'Raw NMF effective-component count is diagnostic-only after real-music saturation evidence.',
        'Unusual or sample-heavy production is not a defect.',
        'Playback authority remains zero.'
    ]
    return result
