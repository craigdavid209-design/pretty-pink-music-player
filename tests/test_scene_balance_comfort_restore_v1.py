from tools.scene_balance_comfort_restore_v1 import (
    old_scene_balance_cut,
    comfort_restored_balance_cut,
    scene_qdi_lift,
)


def test_balance_restore_is_never_more_aggressive_than_approved_balance():
    for cut in [0.0, -0.01, -0.10, -0.30, -0.55]:
        for factor in [0.82, 0.86, 0.92, 0.99, 1.0]:
            restored = comfort_restored_balance_cut(cut, factor)
            assert restored == cut
            if cut <= 0:
                old = old_scene_balance_cut(cut, factor)
                # Negative-number ordering: approved Balance <= restored <= current relaxed Scene result.
                assert cut <= restored <= old + 1e-15


def test_scene_still_reduces_qdi_only():
    for lift in [0.0, 0.05, 0.25, 0.75, 1.0]:
        for factor in [0.82, 0.90, 1.0]:
            out = scene_qdi_lift(lift, factor)
            assert 0.0 <= out <= lift + 1e-15


def test_identity_when_scene_abstains():
    for cut in [-0.55, -0.2, 0.0]:
        assert comfort_restored_balance_cut(cut, 1.0) == cut
        assert old_scene_balance_cut(cut, 1.0) == cut


def test_no_new_boost_or_cut_is_created():
    # This bridge only restores the existing Balance request. It cannot invent authority.
    for cut in [-0.55, -0.25, -0.01, 0.0]:
        for factor in [0.82, 0.9, 1.0]:
            out = comfort_restored_balance_cut(cut, factor)
            assert out == cut
            assert -0.55 <= out <= 0.0
