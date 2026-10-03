import sys
sys.path.insert(0, 'tools')
from selective_scene_restraint_v3 import *


event = SceneEvent(10, .40, 3, .14)
assert factor_at([event], 0) == 1
near = factor_at([event], 10)
assert .82 <= near < 1
assert factor_at([event], 10, vocal_veto=True) == 1
assert factor_at([event], 10, production_ambiguity=.9) == 1

weak = SceneEvent(10, .30, 1, .12)
assert factor_at([weak], 10) == 1

for factor in [1, .95, .82]:
    cut = balance_cut(-.5, factor)
    lift = qdi_lift(.3, factor)
    assert -.5 - 1e-12 <= cut <= 1e-12
    assert -1e-12 <= lift <= .3 + 1e-12
    assert abs(cut) <= .5 + 1e-12

# No event == exact old behavior. There is intentionally no profile/global factor API.
assert factor_at([], 10) == 1

print('selective scene restraint v3 tests: PASS')
