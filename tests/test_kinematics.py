#!/usr/bin/env python3
"""Known-answer tests for FK, reachability and static capacity.

Known answers, not pinned outputs — OpenDesignCore's distinction, and the reason
its `tests/reference/` exists. A pinned output test tells you the code still does
what it did; a known-answer test tells you it does the right thing. A 1 kg mass on
a 100 mm arm loads the joint with 0.980665 N.m because g is 9.80665 m/s^2, and
that is true whether or not this code has ever run.

    python tests/test_kinematics.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import kinematics as kin  # noqa: E402

SRC = {"citation": "test fixture"}
TOL = 1e-9


def planar_arm(tool=True) -> dict:
    """Two 100 mm links rotating about z. Every pose below is hand-computable."""
    robot = {
        "schema_version": 0, "robot_id": "planar", "kind": "arm", "base_link": "base",
        "links": [
            {"link_id": "base", "part_id": "mechanical/x", "source": SRC},
            {"link_id": "l1", "part_id": "mechanical/x", "mass_g": 0, "source": SRC},
            {"link_id": "l2", "part_id": "mechanical/x", "mass_g": 0, "source": SRC},
        ],
        "joints": [
            {"joint_id": "j1", "type": "revolute", "parent": "base", "child": "l1",
             "origin": {}, "axis": {"x": 0, "y": 0, "z": 1},
             "limits": {"lower_rad": -math.pi, "upper_rad": math.pi, "source": SRC},
             "source": SRC},
            {"joint_id": "j2", "type": "revolute", "parent": "l1", "child": "l2",
             "origin": {"xyz_mm": {"x": 100, "y": 0, "z": 0}},
             "axis": {"x": 0, "y": 0, "z": 1},
             "limits": {"lower_rad": -math.pi, "upper_rad": math.pi, "source": SRC},
             "source": SRC},
        ],
        "source": SRC,
    }
    if tool:
        robot["tool"] = {"offset": {"xyz_mm": {"x": 100, "y": 0, "z": 0}},
                         "tool_id": "probe", "attached_to": "l2", "source": SRC}
    return robot


def tool_at(robot, pose):
    frames = kin.forward_kinematics(robot, pose)
    return kin.position(kin.tool_matrix(robot, frames)[0])


def close(got, want, tol=1e-6):
    assert all(abs(g - w) < tol for g, w in zip(got, want)), f"{got} != {want}"


# ------------------------------------------------------------------------ the maths

def test_zero_pose_is_fully_extended():
    close(tool_at(planar_arm(), {"j1": 0, "j2": 0}), (200, 0, 0))


def test_base_joint_rotates_the_whole_chain():
    close(tool_at(planar_arm(), {"j1": math.pi / 2, "j2": 0}), (0, 200, 0))


def test_second_joint_rotates_only_what_is_below_it():
    """The elbow bends: the first link stays on x, the second turns onto y."""
    close(tool_at(planar_arm(), {"j1": 0, "j2": math.pi / 2}), (100, 100, 0))


def test_folded_back_returns_to_the_first_joint():
    close(tool_at(planar_arm(), {"j1": 0, "j2": math.pi}), (0, 0, 0))


def test_tool_offset_changes_the_answer():
    """ADR-0003's whole point: a reach answer without its tool offset is meaningless."""
    close(tool_at(planar_arm(tool=False), {"j1": 0, "j2": 0}), (100, 0, 0))
    close(tool_at(planar_arm(tool=True), {"j1": 0, "j2": 0}), (200, 0, 0))


def test_prismatic_joint_translates_along_its_axis():
    robot = planar_arm(tool=False)
    robot["joints"][1] = {"joint_id": "j2", "type": "prismatic", "parent": "l1",
                          "child": "l2", "origin": {"xyz_mm": {"x": 100, "y": 0, "z": 0}},
                          "axis": {"x": 0, "y": 0, "z": 1},
                          "limits": {"lower_mm": 0, "upper_mm": 50, "source": SRC},
                          "source": SRC}
    close(tool_at(robot, {"j1": 0, "j2": 25}), (100, 0, 25))


def test_mimic_joint_follows_and_is_not_free():
    """ADR-0008: a mimicking joint is not independently commandable."""
    robot = planar_arm(tool=False)
    robot["joints"][1]["mimic"] = {"joint": "j1", "multiplier": -1}
    assert [j["joint_id"] for j in kin.free_joints(robot)] == ["j1"]
    # j1 = pi/2 turns the base; j2 = -pi/2 turns the second link back onto x
    close(tool_at(robot, {"j1": math.pi / 2}), (0, 100, 0))


# ------------------------------------------------------ ADR-0003: incomplete answers

def test_unknown_limits_make_reach_incomplete_and_name_the_joint():
    robot = planar_arm()
    robot["joints"][1]["limits"] = None
    verdict = kin.reach_verdict(robot, (150, 0, 0), 5.0, 100, 0)
    assert verdict["verdict"] == "incomplete"
    assert "j2" in verdict["missing"]
    assert "never unlimited" in verdict["detail"]


def test_floating_joint_makes_fk_incomplete():
    robot = planar_arm()
    robot["joints"][0] = {"joint_id": "j1", "type": "floating", "parent": "base",
                          "child": "l1", "origin": {}, "source": SRC}
    try:
        kin.forward_kinematics(robot, {})
    except kin.Incomplete as exc:
        assert "localization" in exc.detail
        return
    raise AssertionError("a floating joint should not silently evaluate")


# ------------------------------------------------------- ADR-0013: sampled workspace

def test_a_reachable_point_is_a_claim_with_the_pose_that_got_there():
    """Target taken from a real FK evaluation, so it is reachable by construction —
    the test is whether sampling finds it, not whether the point exists."""
    robot = planar_arm()
    target = tool_at(robot, {"j1": 0.4, "j2": 0.7})
    verdict = kin.reach_verdict(robot, target, 5.0, 20000, 0)
    assert verdict["verdict"] == "reachable", verdict
    assert "pose" in verdict
    assert verdict["nearest_sample_mm"] <= 5.0


def test_an_unreached_point_is_not_called_unreachable():
    """The refusal ADR-0013 is built on. A sampled set only proves the positive."""
    verdict = kin.reach_verdict(planar_arm(), (5000, 0, 0), 1.0, 200, 0)
    assert verdict["verdict"] == "no-sample-reached-it"
    assert "NOT a claim" in verdict["detail"]
    assert verdict["samples"] > 0


def test_every_verdict_carries_its_five_assumptions():
    verdict = kin.reach_verdict(planar_arm(), (200, 0, 0), 1.0, 200, 0)
    assert verdict["relative_to"] == "base"
    assert "probe" in verdict["tool_offset"]
    assert verdict["seed"] == 0 and verdict["samples"] > 0
    assert any("NOT a collision result" in c for c in verdict["caveats"])
    assert any("harness" in c or "cable" in c for c in verdict["caveats"])


def test_sampling_is_deterministic_for_a_given_seed():
    a = kin.reach_verdict(planar_arm(), (150, 50, 0), 3.0, 500, 7)
    b = kin.reach_verdict(planar_arm(), (150, 50, 0), 3.0, 500, 7)
    assert a == b
    c = kin.reach_verdict(planar_arm(), (150, 50, 0), 3.0, 500, 8)
    assert c["nearest_sample_mm"] != a["nearest_sample_mm"]


def test_limit_extremes_are_always_sampled():
    """A uniform draw reaches a corner of an n-joint space with probability ~0."""
    points = kin.sample_workspace(planar_arm(), 0, 0)
    assert len(points) == 4                      # 2 joints, 2 limits each
    assert any(abs(p[0] - 0.0) < 1e-6 and abs(p[1]) < 1e-6 for p, _ in points)


# --------------------------------------------------------- ADR-0004: static capacity

def with_actuator(monkey_value, volts=None):
    kin.load_actuator = lambda aid: monkey_value
    kin.supply_volts = lambda robot_id: volts


def single_joint(effort_nm=10.0, link_mass_g=0, tool_mass_g=0, arm_mm=100) -> dict:
    """One revolute joint about y at the origin, with the mass `arm_mm` out along x."""
    return {
        "schema_version": 0, "robot_id": "lever", "kind": "arm", "base_link": "base",
        "links": [
            {"link_id": "base", "part_id": "mechanical/x", "source": SRC},
            {"link_id": "l1", "part_id": "mechanical/x", "mass_g": link_mass_g,
             "source": SRC},
        ],
        "joints": [
            {"joint_id": "j1", "type": "revolute", "parent": "base", "child": "l1",
             "origin": {}, "axis": {"x": 0, "y": 1, "z": 0},
             "limits": {"lower_rad": -1.5, "upper_rad": 1.5, "effort_nm": effort_nm,
                        "source": SRC},
             "source": SRC},
        ],
        "tool": {"offset": {"xyz_mm": {"x": arm_mm, "y": 0, "z": 0}},
                 "attached_to": "l1", "mass_g": tool_mass_g, "source": SRC},
        "source": SRC,
    }


def test_one_kilogram_at_one_hundred_millimetres():
    """1 kg * 9.80665 m/s^2 * 0.1 m = 0.980665 N.m. True before this code existed."""
    verdict = kin.hold_verdict(single_joint(tool_mass_g=1000), {"j1": 0}, 0)
    assert verdict["verdict"] == "holds"
    assert abs(verdict["joints"][0]["static_load_nm"] - 0.980665) < 1e-4


def test_load_falls_to_zero_when_the_arm_hangs_straight_down():
    """The reason ADR-0004 deleted scalar payload_kg: capacity is a function of pose.
    Same mass, same arm, quarter turn — the lever arm goes to zero."""
    robot = single_joint(tool_mass_g=1000)
    extended = kin.hold_verdict(robot, {"j1": 0}, 0)["joints"][0]["static_load_nm"]
    hanging = kin.hold_verdict(robot, {"j1": math.pi / 2}, 0)["joints"][0]["static_load_nm"]
    assert abs(extended - 0.980665) < 1e-4
    assert abs(hanging) < 1e-4


def test_load_scales_linearly_with_the_lever_arm():
    at_100 = kin.hold_verdict(single_joint(tool_mass_g=1000, arm_mm=100),
                              {"j1": 0}, 0)["joints"][0]["static_load_nm"]
    at_200 = kin.hold_verdict(single_joint(tool_mass_g=1000, arm_mm=200),
                              {"j1": 0}, 0)["joints"][0]["static_load_nm"]
    assert abs(at_200 - 2 * at_100) < 1e-4


def test_a_payload_beyond_capacity_is_reported_not_rounded_away():
    verdict = kin.hold_verdict(single_joint(effort_nm=0.5), {"j1": 0}, payload_g=1000)
    assert verdict["verdict"] == "exceeds-capacity"
    assert verdict["binding_joint"] == "j1"


def test_the_bound_is_labelled_a_bound():
    """ADR-0004: the figure may never be printed without the word that bounds it."""
    verdict = kin.hold_verdict(single_joint(), {"j1": 0}, 0)
    assert verdict["bound"] == "STATIC UPPER BOUND"
    assert "NOT modelled" in verdict["bound_note"]


def test_missing_link_mass_is_incomplete_never_zero():
    robot = single_joint()
    robot["links"][1].pop("mass_g")
    verdict = kin.hold_verdict(robot, {"j1": 0}, 0)
    assert verdict["verdict"] == "incomplete"
    assert verdict["missing"] == "link mass"
    assert "never zero" in verdict["detail"]


def test_stall_only_actuator_makes_capacity_incomplete():
    """The XM430 case, end to end: a good datasheet and still no capacity answer."""
    robot = single_joint()
    robot["joints"][0].pop("limits")
    robot["joints"][0]["actuator_id"] = "xm430"
    original = kin.load_actuator
    original_volts = kin.supply_volts
    with_actuator({"actuator_id": "xm430",
                   "stall_torque_nm": [{"value": 3.8, "at_volts": 11.1},
                                       {"value": 4.1, "at_volts": 12.0},
                                       {"value": 4.8, "at_volts": 14.8}],
                   "continuous_torque_nm": None}, volts=12.0)
    try:
        verdict = kin.hold_verdict(robot, {"j1": 0}, 0)
    finally:
        kin.load_actuator, kin.supply_volts = original, original_volts
    assert verdict["verdict"] == "incomplete"
    assert "continuous_torque_nm" in verdict["detail"]
    assert "ADR-0004" in verdict["detail"]


def test_a_cited_continuous_torque_does_produce_an_answer():
    """The other half: when the evidence exists, the derivation runs."""
    robot = single_joint(tool_mass_g=500)
    robot["joints"][0].pop("limits")
    robot["joints"][0]["actuator_id"] = "measured"
    robot["joints"][0]["gear_ratio"] = 2
    original, original_volts = kin.load_actuator, kin.supply_volts
    with_actuator({"actuator_id": "measured",
                   "continuous_torque_nm": [{"value": 1.0, "at_volts": 12.0,
                                             "how_determined": "measured, 30 min to "
                                                               "thermal steady state"}]},
                  volts=12.0)
    try:
        verdict = kin.hold_verdict(robot, {"j1": 0}, 0)
    finally:
        kin.load_actuator, kin.supply_volts = original, original_volts
    assert verdict["verdict"] == "holds"
    assert verdict["joints"][0]["capacity_nm"] == 2.0        # 1.0 N.m through 2:1
    assert abs(verdict["joints"][0]["static_load_nm"] - 0.4903) < 1e-3


def test_floating_base_refuses_to_assume_which_way_is_down():
    """ADR-0009's sharp consequence."""
    robot = planar_arm(tool=False)
    robot["joints"][0] = {"joint_id": "j1", "type": "floating", "parent": "base",
                          "child": "l1", "origin": {}, "source": SRC}
    verdict = kin.hold_verdict(robot, {}, 0)
    assert verdict["verdict"] == "incomplete"
    assert verdict["missing"] == "base orientation"
    assert "flat-ground figure" in verdict["detail"]


# --------------------------------------------------- ADR-0014: the voltage is an index

TWO_ROW = {"actuator_id": "two-row", "continuous_torque_nm": [
    {"value": 1.0, "at_volts": 12.0, "how_determined": "datasheet continuous rating"},
    {"value": 1.3, "at_volts": 14.8, "how_determined": "datasheet continuous rating"}]}


def capacity_at(volts):
    robot = single_joint()
    robot["joints"][0].pop("limits")
    robot["joints"][0]["actuator_id"] = "two-row"
    original, original_volts = kin.load_actuator, kin.supply_volts
    with_actuator(TWO_ROW, volts=volts)
    try:
        return kin.hold_verdict(robot, {"j1": 0}, 0)
    finally:
        kin.load_actuator, kin.supply_volts = original, original_volts


def test_capacity_selects_the_row_matching_the_supply():
    """30% apart. Picking the wrong row is wrong by the width of the curve."""
    assert capacity_at(12.0)["joints"][0]["capacity_nm"] == 1.0
    assert capacity_at(14.8)["joints"][0]["capacity_nm"] == 1.3


def test_no_declared_supply_voltage_means_no_capacity_answer():
    """Picking a row on the author's behalf is the invisible choice ADR-0014 removes."""
    verdict = capacity_at(None)
    assert verdict["verdict"] == "incomplete"
    assert verdict["missing"] == "harness supply voltage"
    assert "invisible choice" in verdict["detail"]


def test_interpolation_between_published_rows_is_refused():
    """13 V sits between 12.0 and 14.8. Approximately linear is still a model."""
    verdict = capacity_at(13.0)
    assert verdict["verdict"] == "incomplete"
    assert "Interpolation is refused" in verdict["detail"]
    assert "12.0" in verdict["detail"] and "14.8" in verdict["detail"]


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
