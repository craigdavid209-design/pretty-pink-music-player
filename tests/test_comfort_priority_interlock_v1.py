#!/usr/bin/env python3
from tools.comfort_priority_interlock_v1 import (
    balance_scene_factor, qdi_scene_factor, apply_balance_cut
)


def close(a, b, eps=1e-12):
    assert abs(a-b) <= eps, (a,b)


def main():
    # No earned spectral comfort evidence: behavior is exactly current Scene v3.
    close(balance_scene_factor(.86, True, 0.0), .86)
    close(balance_scene_factor(.91, False, 1.0), .91)

    # Earned existing comfort evidence: Scene loses Balance-reduction authority.
    close(balance_scene_factor(.82, True, .15), 1.0)
    close(balance_scene_factor(.93, True, 1.0), 1.0)

    # QDI must remain exactly on the current Scene factor.
    close(qdi_scene_factor(.82), .82)
    close(qdi_scene_factor(.94), .94)

    # Monotonic authority proof: candidate can restore the original cut but can
    # never exceed it (never become more negative than the planner asked for).
    for cut in [0.0, -.05, -.20, -.55]:
        for scene in [.82, .86, .91, 1.0]:
            current = apply_balance_cut(cut, scene)
            candidate = apply_balance_cut(cut, balance_scene_factor(scene, True, .3))
            assert cut - 1e-12 <= candidate <= current + 1e-12 <= 1e-12, (cut, scene, candidate, current)
            close(candidate, cut)

    # Invalid confidence must fail closed to current behavior, not invent authority.
    for bad in [float('nan'), -1.0, 1.1]:
        close(balance_scene_factor(.87, True, bad), .87)

    print('comfort priority interlock v1 tests: PASS')


if __name__ == '__main__':
    main()
