import sys
sys.path.insert(0, 'tools')
from production_context_witness import ProductionEvidence, understand
from vocal_intelligibility_witness import evaluate


def evidence(**kw):
    data = dict(
        vocal_compatible=.8,
        articulation_support=.7,
        masking_burden=.25,
        spatial_layering=.2,
        temporal_smear=.25,
        production_density=.4,
        confidence=.85,
    )
    data.update(kw)
    return ProductionEvidence(**data)


clean = evidence()
assert understand(clean).label in ('MIXTURE_CONTEXT', 'DENSE_CONTEXT')
clean_v = evaluate(clean)
assert clean_v.label == 'LOW_OBSERVED_RISK'
assert not clean_v.scene_restraint_veto

masked = evidence(
    masking_burden=.85,
    temporal_smear=.75,
    spatial_layering=.65,
    articulation_support=.3,
    production_density=.8,
)
masked_v = evaluate(masked)
assert masked_v.risk >= .42
assert masked_v.scene_restraint_veto
assert masked_v.label.startswith('HIGH_')

uncertain = evidence(confidence=.3)
assert evaluate(uncertain).label == 'UNAVAILABLE'

# Strong vocal-compatible evidence is intentionally NOT equivalent to intelligibility.
assert masked.vocal_compatible == clean.vocal_compatible
assert masked_v.risk > clean_v.risk

print('vocal/production witness tests: PASS')
