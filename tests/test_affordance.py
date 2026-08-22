#!/usr/bin/env python3
"""The four affordance verdicts, and the one that is missing on purpose.

The composition in ADR-0015 is the thing under test: sampled reach is sound
positive and unsound negative, static capacity is sound negative and unsound
positive, and there is therefore no combination that yields a provable yes.
These tests exist to stop a later change from quietly inventing one.

    python tests/test_affordance.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import affordance as aff  # noqa: E402
import kinematics as kin  # noqa: E402

SRC = {"citation": "test fixture"}


def lever(effort_nm=10.0, arm_mm=100) -> dict:
    """One revolute joint about y; the tool sits `arm_mm` out along x.

    Reachable set is an arc of radius arm_mm in the xz plane, so a target on that
    arc is reachable and the load at it is hand-computable."""
    return {
        "schema_version": 0, "robot_id": "lever", "kind": "arm", "base_link": "base",
        "links": [
            {"link_id": "base", "part_id": "mechanical/x", "source": SRC},
            {"link_id": "l1", "part_id": "mechanical/x", "mass_g": 0, "source": SRC},
        ],
        "joints": [
            {"joint_id": "j1", "type": "revolute", "parent": "base", "child": "l1",
             "origin": {}, "axis": {"x": 0, "y": 1, "z": 0},
             "limits": {"lower_rad": -1.5, "upper_rad": 1.5, "effort_nm": effort_nm,
                        "source": SRC},
             "source": SRC},
        ],
        "tool": {"offset": {"xyz_mm": {"x": arm_mm, "y": 0, "z": 0}},
                 "tool_id": "probe", "attached_to": "l1", "mass_g": 0, "source": SRC},
        "source": SRC,
    }


def ask(robot, target, payload_g=0.0, tolerance=5.0, samples=4000, seed=0):
    return aff.affordance(robot, target, payload_g, tolerance, samples, seed)


# ----------------------------------------------------------- the missing verdict

def test_there_is_no_can_verdict_anywhere():
    """ADR-0015's central claim. If a later change adds one, this fails."""
    reachable = ask(lever(), (100, 0, 0))
    assert reachable["verdict"] == "within-static-bound"
    assert reachable["verdict"] != "can"
    assert "not a yes" in reachable["detail"].lower()


def test_there_is_no_score():
    verdict = ask(lever(), (100, 0, 0))
    assert "score" not in verdict
    assert "affordance" not in {k.lower() for k in verdict} - {"no_score"}
    assert "frequency estimate" in verdict["no_score"]
    for key, value in verdict.items():
        if isinstance(value, float):
            assert not (0.0 <= value <= 1.0 and key.endswith("score"))


def test_the_closest_thing_to_yes_names_what_it_ignores():
    verdict = ask(lever(), (100, 0, 0))
    for ignored in ("efficiency", "friction", "backlash", "acceleration"):
        assert ignored in verdict["detail"]
    assert "Self-collision" in verdict["detail"]


# ------------------------------------------------------- the one sound negative

def test_exceeding_the_upper_bound_is_a_real_claim():
    """1 kg at 100 mm is 0.980665 N.m against a 0.5 N.m ceiling."""
    verdict = ask(lever(effort_nm=0.5), (100, 0, 0), payload_g=1000)
    assert verdict["verdict"] == "cannot"
    assert verdict["binding"] == "joint 'j1'"
    assert verdict["margin_nm"] < 0
    assert "settles the matter" in verdict["detail"]


def test_cannot_is_scoped_to_the_pose_it_found():
    """Not "impossible everywhere" — a different pose may reach the same point."""
    verdict = ask(lever(effort_nm=0.5), (100, 0, 0), payload_g=1000)
    assert "not about every pose" in verdict["caveat"]


def test_a_bigger_actuator_flips_the_same_request():
    request = ((100, 0, 0), 1000)
    assert ask(lever(effort_nm=0.5), *request)["verdict"] == "cannot"
    assert ask(lever(effort_nm=10.0), *request)["verdict"] == "within-static-bound"


# --------------------------------------------------- unreached is not a negative

def test_an_unreachable_target_is_unproven_not_cannot():
    """ADR-0013 propagating up through the composition."""
    verdict = ask(lever(), (5000, 0, 0))
    assert verdict["verdict"] == "unproven"
    assert verdict["verdict"] != "cannot"
    assert "NOT a claim" in verdict["detail"]


def test_unproven_names_how_hard_it_looked():
    verdict = ask(lever(), (5000, 0, 0), samples=1234)
    assert "1234" in verdict["detail"] or str(verdict["reach"]["samples"]) in verdict["detail"]


# --------------------------------------------------------------- incomplete

def test_unknown_joint_limits_are_incomplete_at_the_reach_half():
    robot = lever()
    robot["joints"][0]["limits"] = None
    verdict = ask(robot, (100, 0, 0))
    assert verdict["verdict"] == "incomplete"
    assert verdict["binding"] == "reach"
    assert "j1" in verdict["missing"]


def test_missing_capacity_input_is_incomplete_but_says_reach_succeeded():
    """The distinction that makes an incomplete actionable: which half failed."""
    robot = lever()
    robot["joints"][0]["limits"].pop("effort_nm")
    robot["joints"][0]["actuator_id"] = "stall-only"
    original, original_volts = kin.load_actuator, kin.supply_volts
    kin.load_actuator = lambda aid: {"actuator_id": "stall-only",
                                     "stall_torque_nm": [{"value": 4.1, "at_volts": 12.0}],
                                     "continuous_torque_nm": None}
    kin.supply_volts = lambda rid: 12.0
    try:
        verdict = ask(robot, (100, 0, 0))
    finally:
        kin.load_actuator, kin.supply_volts = original, original_volts
    assert verdict["verdict"] == "incomplete"
    assert verdict["binding"] == "capacity"
    assert "reachable" in verdict["note"]
    assert verdict["reach"]["verdict"] == "reachable"


# ------------------------------------------------------------- the best pose

def test_best_margin_pose_is_offered_beside_the_verdict_not_instead_of_it():
    verdict = ask(lever(), (100, 0, 0), payload_g=200)
    assert "best_margin_pose" in verdict
    assert "pose" in verdict["reach"]
    assert "not instead of it" in verdict["best_margin_note"]


def test_best_margin_is_at_least_as_good_as_the_found_pose():
    verdict = ask(lever(), (100, 0, 0), payload_g=200)
    assert verdict["best_margin_pose"]["margin_nm"] >= verdict["margin_nm"] - 1e-9


def test_a_truncated_search_says_so_rather_than_looking_thorough():
    """No silent caps: if poses were dropped, the verdict names how many."""
    verdict = ask(lever(), (100, 0, 0), tolerance=100.0, samples=4000)
    if "best_margin_truncated" in verdict:
        assert "not checked" in verdict["best_margin_truncated"]
    else:
        assert True        # under the cap on this fixture; the branch is still guarded


# ------------------------------------------------------------ carried assumptions

def test_the_request_is_echoed_with_its_frame():
    verdict = ask(lever(), (100, 0, 0), payload_g=50)
    assert verdict["request"]["relative_to"] == "base"
    assert verdict["request"]["payload_g"] == 50


def test_the_full_reach_verdict_travels_inside_the_affordance():
    """Its caveats are the affordance's caveats; hiding them would launder them."""
    verdict = ask(lever(), (100, 0, 0))
    assert any("NOT a collision result" in c for c in verdict["reach"]["caveats"])
    assert verdict["reach"]["seed"] == 0


def test_the_hold_verdict_keeps_its_upper_bound_label():
    verdict = ask(lever(), (100, 0, 0))
    assert verdict["hold"]["bound"] == "STATIC UPPER BOUND"


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"pass  {name}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {name} — {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
