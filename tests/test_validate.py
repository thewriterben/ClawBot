#!/usr/bin/env python3
"""Negative tests: proof that the validator refuses.

A validator nobody has watched reject something is a validator that might be
returning zero because it never looks. Every rule with teeth in DECISIONS.md gets
a test here that makes it bite, and the two that are deliberately *warnings*
rather than failures get a test proving they do not block — because "unknown"
being allowed through is the whole point of ADR-0003.

Runs under pytest, or standalone:

    python tests/test_validate.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validate  # noqa: E402

SRC = {"citation": "test fixture"}


def robot(**overrides) -> dict:
    """A minimal valid two-link robot. Tests corrupt one thing at a time."""
    base = {
        "schema_version": 0,
        "robot_id": "fixture",
        "kind": "arm",
        "base_link": "base",
        "links": [
            {"link_id": "base", "make": {"size_mm": {"x": 1, "y": 1, "z": 1},
                                         "material": "petg"}, "source": SRC},
            {"link_id": "arm", "part_id": "mechanical/fixture", "source": SRC},
        ],
        "joints": [
            {"joint_id": "j1", "type": "revolute", "parent": "base", "child": "arm",
             "origin": {}, "axis": {"x": 0, "y": 0, "z": 1},
             "limits": {"lower_rad": -1.5, "upper_rad": 1.5, "source": SRC},
             "source": SRC},
        ],
        "source": SRC,
    }
    base.update(overrides)
    return base


def run(kind: str, doc: dict, robots: dict | None = None):
    """Check one document, returning the report."""
    report = validate.Report()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fixture.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        if kind == "robot":
            validate.check_robot(path, report)
        elif kind == "actuator":
            validate.check_actuator(path, report)
        elif kind == "assembly":
            validate.check_assembly(path, report, robots or {})
        else:
            validate.check_harness(path, report, robots or {})
    return report


def refuses(report, needle: str) -> bool:
    return any(needle in f for f in report.failures)


def warns(report, needle: str) -> bool:
    return any(needle in w for w in report.warnings)


# ------------------------------------------------------------------ the positive

def test_minimal_robot_is_valid():
    assert run("robot", robot()).failures == []


# ------------------------------------------------- ADR-0005: radians in the file

def test_degrees_in_a_rad_field_are_refused():
    """The main defence ADR-0005 leaves standing."""
    doc = robot()
    doc["joints"][0]["limits"] = {"lower_rad": -90, "upper_rad": 90, "source": SRC}
    report = run("robot", doc)
    assert refuses(report, "outside +/-4*pi")
    assert refuses(report, "If this is degrees")


def test_inverted_limits_are_refused():
    doc = robot()
    doc["joints"][0]["limits"] = {"lower_rad": 1.5, "upper_rad": -1.5, "source": SRC}
    assert refuses(run("robot", doc), "exceeds upper_rad")


def test_bare_integer_radians_warn_but_pass():
    """open-questions #4: a `3` is plausibly 3 rad and plausibly 30 degrees.
    In range either way, so it cannot be refused — but it can be surfaced."""
    doc = robot()
    doc["joints"][0]["limits"] = {"lower_rad": -3, "upper_rad": 3, "source": SRC}
    report = run("robot", doc)
    assert report.failures == []
    assert warns(report, "bare integer in radians")


# --------------------------------------------------------- ADR-0008: it's a tree

def test_two_parents_for_one_link_is_refused():
    """A loop, not a tree."""
    doc = robot()
    doc["links"].append({"link_id": "extra", "part_id": "mechanical/x", "source": SRC})
    doc["joints"].append(
        {"joint_id": "j2", "type": "revolute", "parent": "extra", "child": "arm",
         "origin": {}, "axis": {"x": 1, "y": 0, "z": 0},
         "limits": {"lower_rad": -1, "upper_rad": 1, "source": SRC}, "source": SRC})
    assert refuses(run("robot", doc), "two parents is a loop")


def test_unreachable_link_is_refused():
    doc = robot()
    doc["links"].append({"link_id": "floating", "part_id": "mechanical/x", "source": SRC})
    assert refuses(run("robot", doc), "not reachable from base_link")


def test_branching_tree_is_allowed():
    """The contradiction ADR-0008 resolved: a tree branches, a serial chain does not."""
    doc = robot()
    doc["links"].append({"link_id": "head", "part_id": "mechanical/x", "source": SRC})
    doc["joints"].append(
        {"joint_id": "j2", "type": "revolute", "parent": "base", "child": "head",
         "origin": {}, "axis": {"x": 0, "y": 1, "z": 0},
         "limits": {"lower_rad": -1, "upper_rad": 1, "source": SRC}, "source": SRC})
    assert run("robot", doc).failures == []


# ---------------------------------------------------------- ADR-0008: mimic rules

def test_mimic_cycle_is_refused():
    doc = robot()
    doc["links"].append({"link_id": "jaw", "part_id": "mechanical/x", "source": SRC})
    doc["joints"].append(
        {"joint_id": "j2", "type": "revolute", "parent": "arm", "child": "jaw",
         "origin": {}, "axis": {"x": 0, "y": 0, "z": 1},
         "limits": {"lower_rad": -1, "upper_rad": 1, "source": SRC},
         "mimic": {"joint": "j1"}, "source": SRC})
    doc["joints"][0]["mimic"] = {"joint": "j2"}
    assert refuses(run("robot", doc), "mimic cycle")


def test_mimic_naming_a_missing_joint_is_refused():
    doc = robot()
    doc["joints"][0]["mimic"] = {"joint": "nonexistent"}
    assert refuses(run("robot", doc), "does not exist")


def test_coupled_gripper_is_valid():
    """The mechanism ADR-0008 made expressible: one actuator, two jaws, no loop."""
    doc = robot()
    for jaw in ("left", "right"):
        doc["links"].append({"link_id": jaw, "part_id": "mechanical/jaw", "source": SRC})
    doc["joints"].append(
        {"joint_id": "left-jaw", "type": "prismatic", "parent": "arm", "child": "left",
         "origin": {}, "axis": {"x": 1, "y": 0, "z": 0},
         "limits": {"lower_mm": 0, "upper_mm": 20, "source": SRC}, "source": SRC})
    doc["joints"].append(
        {"joint_id": "right-jaw", "type": "prismatic", "parent": "arm", "child": "right",
         "origin": {}, "axis": {"x": 1, "y": 0, "z": 0},
         "limits": {"lower_mm": 0, "upper_mm": 20, "source": SRC},
         "mimic": {"joint": "left-jaw", "multiplier": -1}, "source": SRC})
    assert run("robot", doc).failures == []


# ------------------------------------------------------- ADR-0006: link is one kind

def test_link_with_two_kinds_is_refused():
    doc = robot()
    doc["links"][1]["make"] = {"size_mm": {"x": 1, "y": 1, "z": 1}, "material": "petg"}
    assert refuses(run("robot", doc), "declares 2 of part_id/make/provenance_ref")


def test_link_with_no_kind_is_refused():
    doc = robot()
    del doc["links"][1]["part_id"]
    assert refuses(run("robot", doc), "declares 0 of part_id/make/provenance_ref")


# --------------------------------------------------------------- the citation gate

def test_uncited_joint_is_refused():
    doc = robot()
    del doc["joints"][0]["source"]
    assert refuses(run("robot", doc), "has no source")


def test_todo_source_passes_but_is_counted():
    """A placeholder must block downstream, not here. It is what it is for."""
    doc = robot()
    doc["joints"][0]["source"] = {"citation": "TODO(source)"}
    report = run("robot", doc)
    assert report.failures == []
    assert report.todo_sources == 1


# --------------------------------------------------------- ADR-0003: unknown limits

def test_missing_limits_warn_but_do_not_block():
    """The honest state the whole repo is built around. Refusing it would be wrong."""
    doc = robot()
    doc["joints"][0]["limits"] = None
    report = run("robot", doc)
    assert report.failures == []
    assert warns(report, "UNKNOWN, never unlimited")


def test_zero_axis_is_refused():
    doc = robot()
    doc["joints"][0]["axis"] = {"x": 0, "y": 0, "z": 0}
    assert refuses(run("robot", doc), "axis is the zero vector")


# ------------------------------------------------- ADR-0009: floating and planar

def test_floating_joint_is_a_valid_type():
    doc = robot()
    doc["joints"][0] = {"joint_id": "j1", "type": "floating", "parent": "base",
                        "child": "arm", "origin": {}, "source": SRC}
    assert run("robot", doc).failures == []


def test_floating_joint_with_limits_is_refused():
    doc = robot()
    doc["joints"][0] = {"joint_id": "j1", "type": "floating", "parent": "base",
                        "child": "arm", "origin": {},
                        "limits": {"lower_rad": -1, "upper_rad": 1, "source": SRC},
                        "source": SRC}
    assert refuses(run("robot", doc), "bounded by an")


# ------------------------------------------------------------- ADR-0004: actuators

def test_rule_of_thumb_continuous_torque_is_refused():
    """The exact failure ADR-0004 exists to prevent."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "hobby-servo", "source": SRC,
           "stall_torque_nm": [{"value": 2.0, "at_volts": 6.0, "source": SRC}],
           "continuous_torque_nm": [{"value": 0.6, "at_volts": 6.0,
                                     "how_determined": "30% of stall torque, typical",
                                     "source": SRC}]}
    assert refuses(run("actuator", doc), "reads like a rule of thumb")


def test_continuous_above_stall_is_refused():
    doc = {"schema_version": 0, "actuator_id": "a", "type": "hobby-servo", "source": SRC,
           "stall_torque_nm": [{"value": 2.0, "at_volts": 6.0, "source": SRC}],
           "continuous_torque_nm": [{"value": 3.0, "at_volts": 6.0,
                                     "how_determined": "measured, held 10 min to steady",
                                     "source": SRC}]}
    assert refuses(run("actuator", doc), "not less than stall")


def test_torque_without_voltage_is_refused():
    doc = {"schema_version": 0, "actuator_id": "a", "type": "hobby-servo", "source": SRC,
           "stall_torque_nm": [{"value": 2.0, "source": SRC}]}
    assert refuses(run("actuator", doc), "without its supply voltage")


def test_scalar_torque_is_refused():
    """ADR-0014: one point on a curve is not the figure."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "hobby-servo", "source": SRC,
           "stall_torque_nm": {"value": 2.0, "at_volts": 6.0, "source": SRC}}
    assert refuses(run("actuator", doc), "is not an array")


def test_two_rows_at_the_same_voltage_are_refused():
    """The voltage is the index a derivation looks the row up by."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "hobby-servo", "source": SRC,
           "stall_torque_nm": [{"value": 2.0, "at_volts": 6.0, "source": SRC},
                               {"value": 2.4, "at_volts": 6.0, "source": SRC}]}
    assert refuses(run("actuator", doc), "two rows at 6.0 V")


def test_stall_only_actuator_is_valid_and_warns():
    """The XM430 case: a good datasheet, three voltages, and capacity still
    underivable because not one of the three rows is a continuous rating."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "smart-servo", "source": SRC,
           "stall_torque_nm": [{"value": 3.8, "at_volts": 11.1, "source": SRC},
                               {"value": 4.1, "at_volts": 12.0, "source": SRC},
                               {"value": 4.8, "at_volts": 14.8, "source": SRC}],
           "continuous_torque_nm": None}
    report = run("actuator", doc)
    assert report.failures == []
    assert warns(report, "capacity is underivable")



# ------------------------------------------------------- ADR-0023: current-indexed torque

def test_holding_torque_without_current_is_refused():
    """The stepper mirror of test_torque_without_voltage_is_refused. Current is
    the index for a current-controlled actuator, so a row without one cannot be
    looked up."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "stepper", "source": SRC,
           "holding_torque_nm": [{"value": 0.59, "source": SRC}]}
    assert refuses(run("actuator", doc), "without its current")


def test_two_holding_rows_at_one_current_are_refused():
    doc = {"schema_version": 0, "actuator_id": "a", "type": "stepper", "source": SRC,
           "holding_torque_nm": [{"value": 0.59, "at_amps": 2.0, "source": SRC},
                                 {"value": 0.61, "at_amps": 2.0, "source": SRC}]}
    assert refuses(run("actuator", doc), "two rows at 2.0 A")


def test_a_holding_row_may_not_carry_a_voltage():
    """ADR-0023's whole point. A stepper datasheet's 'rated voltage' is rated
    current times phase resistance, so admitting at_volts here would let one
    field name mean two different quantities across two actuator types."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "stepper", "source": SRC,
           "holding_torque_nm": [{"value": 0.59, "at_amps": 2.0, "at_volts": 2.8,
                                  "source": SRC}]}
    assert refuses(run("actuator", doc), "at_volts")


def test_a_stepper_using_the_servo_field_is_reported():
    doc = {"schema_version": 0, "actuator_id": "a", "type": "stepper", "source": SRC,
           "stall_torque_nm": [{"value": 0.59, "at_volts": 2.8, "source": SRC}]}
    report = run("actuator", doc)
    assert report.failures == []          # a legal shape, just the wrong one
    assert warns(report, "publishes HOLDING torque against current")


def test_a_servo_using_the_stepper_field_is_reported():
    doc = {"schema_version": 0, "actuator_id": "a", "type": "hobby-servo", "source": SRC,
           "holding_torque_nm": [{"value": 0.18, "at_amps": 0.7, "source": SRC}]}
    report = run("actuator", doc)
    assert report.failures == []
    assert warns(report, "publishes stall torque against voltage")


def test_holding_torque_alone_leaves_capacity_underivable():
    """The 17HS19-2004S1 case, and the same answer ADR-0004 gives for stall.
    Whether a holding torque is sustainable is not something the datasheet says,
    so it may not stand in for a continuous rating."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "stepper", "source": SRC,
           "holding_torque_nm": [{"value": 0.59, "at_amps": 2.0, "source": SRC}],
           "continuous_torque_nm": None}
    report = run("actuator", doc)
    assert report.failures == []
    assert warns(report, "capacity is underivable")


# ------------------------------------------------- ADR-0024: a part with no datasheet

def test_an_actuator_with_no_torque_at_all_is_valid_and_says_so():
    """The unbranded-clone case. Legal, because a part no datasheet describes is a
    real thing to own; reported on every run, because silence would let it pass as
    an ordinary record."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "hobby-servo", "source": SRC,
           "stall_torque_nm": None, "continuous_torque_nm": None}
    report = run("actuator", doc)
    assert report.failures == []
    assert warns(report, "no torque or force figure of any kind")


def test_having_any_torque_figure_silences_that_warning():
    """Guards the condition itself: the warning must key on all three fields being
    absent, not on continuous alone, or every stall-only record would trip it."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "hobby-servo", "source": SRC,
           "stall_torque_nm": [{"value": 2.0, "at_volts": 6.0, "source": SRC}]}
    report = run("actuator", doc)
    assert not warns(report, "no torque or force figure of any kind")
    assert warns(report, "capacity is underivable")


# ------------------------------------------- ADR-0025: force is not torque

def test_a_linear_actuator_carrying_a_torque_is_refused():
    """A unit error, not a convention difference. Newtons are not newton-metres,
    and this platform is strictest about units."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "linear-actuator",
           "source": SRC,
           "stall_torque_nm": [{"value": 2.0, "at_volts": 12.0, "source": SRC}]}
    assert refuses(run("actuator", doc), "output is a FORCE in newtons")


def test_a_rotary_actuator_carrying_a_force_is_refused():
    """The same rule in the other direction, so neither family can borrow the
    other's fields."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "hobby-servo", "source": SRC,
           "stall_force_n": [{"value": 80.0, "at_volts": 12.0, "source": SRC}]}
    assert refuses(run("actuator", doc), "Only a linear-actuator produces a force")


def test_force_without_voltage_is_refused():
    doc = {"schema_version": 0, "actuator_id": "a", "type": "linear-actuator",
           "source": SRC,
           "stall_force_n": [{"value": 80.0, "source": SRC}]}
    assert refuses(run("actuator", doc), "without its supply voltage")


def test_continuous_force_above_stall_force_is_refused():
    doc = {"schema_version": 0, "actuator_id": "a", "type": "linear-actuator",
           "source": SRC,
           "stall_force_n": [{"value": 80.0, "at_volts": 12.0, "source": SRC}],
           "continuous_force_n": [{"value": 90.0, "at_volts": 12.0,
                                   "how_determined": "measured, held 30 min",
                                   "source": SRC}]}
    assert refuses(run("actuator", doc), "not less than")


def test_continuous_force_from_a_rule_of_thumb_is_refused():
    """The 30-50%-of-stall guess ADR-0004 refuses for torque, refused for force."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "linear-actuator",
           "source": SRC,
           "continuous_force_n": [{"value": 30.0, "at_volts": 12.0,
                                   "how_determined": "rule of thumb, 40% of stall",
                                   "source": SRC}]}
    assert refuses(run("actuator", doc), "guess wearing a citation")


def test_a_force_figure_silences_the_nothing_at_all_warning():
    """Guards the widened condition: an L12 has no torque and should not be
    reported as having no figure at all."""
    doc = {"schema_version": 0, "actuator_id": "a", "type": "linear-actuator",
           "source": SRC,
           "stall_force_n": [{"value": 80.0, "at_volts": 12.0, "source": SRC}]}
    report = run("actuator", doc)
    assert report.failures == []
    assert not warns(report, "no torque or force figure of any kind")
    assert warns(report, "capacity is underivable")


# --------------------------------------- ADR-0026: a how_determined that says nothing

def _with_range(how):
    return {"schema_version": 0, "actuator_id": "a", "type": "smart-servo", "source": SRC,
            "gearbox": {"ratio": 100,
                        "starting_torque_nm": {"min": 0.03, "max": 0.5,
                                               "how_determined": how, "source": SRC},
                        "source": SRC}}


def test_a_how_determined_that_states_nothing_is_refused():
    """The tempting way to launder an unexplained range: a required field can
    always be satisfied with a word, and the record then LOOKS explained."""
    for empty in ("unknown", "not stated", "N/A", "none", "TBD", "?",
                  "vendor does not say"):
        report = run("actuator", _with_range(empty))
        assert refuses(report, "states nothing"), f"{empty!r} was accepted"


def test_a_real_method_containing_the_word_unknown_is_accepted():
    """The pattern anchors to the whole string. A method is a method even when it
    admits uncertainty, and refusing that would push authors toward vaguer prose."""
    report = run("actuator", _with_range(
        "unknown provenance, but measured on a bench rig at 20 C"))
    assert not refuses(report, "states nothing")


def test_a_range_still_needs_some_how_determined():
    """ADR-0021's original rule, unchanged by ADR-0026."""
    doc = _with_range("x")
    del doc["gearbox"]["starting_torque_nm"]["how_determined"]
    assert refuses(run("actuator", doc), "has no how_determined")


# ------------------------------------- ADR-0027: a ceiling refuses, it never sizes

def _with_limit(**over):
    limit = {"continuous_nm": 0.392266, "intermittent_nm": 0.784532,
             "how_determined": "vendor family page, kg-cm converted", "source": SRC}
    limit.update(over)
    return {"schema_version": 0, "actuator_id": "a", "type": "dc-gearmotor",
            "source": SRC,
            "gearbox": {"ratio": 34, "torque_limit": limit, "source": SRC}}


def test_a_ceiling_alone_leaves_capacity_underivable():
    """The Pololu case. Knowing what NOT to exceed is not knowing what is
    deliverable, so the ceiling buys a refusal and never a capacity."""
    report = run("actuator", _with_limit())
    assert report.failures == []
    assert warns(report, "sound refusal")


def test_a_continuous_torque_above_the_ceiling_is_refused():
    """The cross-check that makes the field earn its place today."""
    doc = _with_limit()
    doc["continuous_torque_nm"] = [{"value": 0.5, "at_volts": 12.0,
                                    "how_determined": "measured, held 30 min",
                                    "source": SRC}]
    assert refuses(run("actuator", doc), "above the gearbox's continuous ceiling")


def test_a_continuous_torque_below_the_ceiling_is_accepted():
    doc = _with_limit()
    doc["continuous_torque_nm"] = [{"value": 0.3, "at_volts": 12.0,
                                    "how_determined": "measured, held 30 min",
                                    "source": SRC}]
    assert not refuses(run("actuator", doc), "continuous ceiling")


def test_an_intermittent_limit_below_the_continuous_one_is_refused():
    assert refuses(run("actuator", _with_limit(intermittent_nm=0.2)),
                   "is not an intermittent limit")


def test_a_ceiling_needs_a_how_determined_that_says_something():
    """ADR-0026 applied to the new field, so the same fig leaf cannot be used."""
    assert refuses(run("actuator", _with_limit(how_determined="not stated")),
                   "states nothing")

# ------------------------------------------------------------ ADR-0011: assemblies

def test_assembly_dependency_cycle_is_refused():
    doc = {"schema_version": 0, "assembly_id": "a", "robot_id": "fixture", "source": SRC,
           "steps": [{"step_id": "one", "action": "x", "depends_on": ["two"]},
                     {"step_id": "two", "action": "y", "depends_on": ["one"]}]}
    assert refuses(run("assembly", doc), "dependency cycle")


def test_assembly_step_joining_a_missing_link_is_refused():
    model = {"robot": robot(), "links": {"base": {}, "arm": {}}, "joints": {"j1": {}}}
    doc = {"schema_version": 0, "assembly_id": "a", "robot_id": "fixture", "source": SRC,
           "steps": [{"step_id": "one", "action": "x", "joins": ["nonexistent"]}]}
    assert refuses(run("assembly", doc, {"fixture": model}), "not in the robot record")


def test_measured_build_time_without_method_is_refused():
    doc = {"schema_version": 0, "assembly_id": "a", "robot_id": "fixture", "source": SRC,
           "steps": [{"step_id": "one", "action": "x"}],
           "measured_build_time": {"minutes": 90, "how_measured": "  "}}
    assert refuses(run("assembly", doc), "no how_measured")


# -------------------------------------------------------------- ADR-0012: harness

def test_two_channels_driving_one_joint_is_refused():
    doc = {"schema_version": 0, "harness_id": "h", "robot_id": "fixture", "source": SRC,
           "channels": [{"joint_id": "j1", "channel": 0, "inverted": False},
                        {"joint_id": "j1", "channel": 1, "inverted": False}]}
    assert refuses(run("harness", doc), "driven by two channels")


def test_duplicate_bus_address_is_refused():
    doc = {"schema_version": 0, "harness_id": "h", "robot_id": "fixture", "source": SRC,
           "channels": [
               {"joint_id": "j1", "bus": "i2c", "bus_address": 64, "inverted": False},
               {"joint_id": "j2", "bus": "i2c", "bus_address": 64, "inverted": False}]}
    assert refuses(run("harness", doc), "is already used by joint")


def test_harness_travel_limit_without_method_is_refused():
    doc = {"schema_version": 0, "harness_id": "h", "robot_id": "fixture", "source": SRC,
           "routing": [{"run_id": "r1", "crosses": ["j1"],
                        "travel_limit": [{"joint_id": "j1", "lower_rad": -1,
                                          "upper_rad": 1, "how_determined": ""}]}]}
    assert refuses(run("harness", doc), "no how_determined")


def test_unchecked_cable_run_warns_loudly():
    """ADR-0012's whole point: null means nobody checked, never true."""
    doc = {"schema_version": 0, "harness_id": "h", "robot_id": "fixture", "source": SRC,
           "routing": [{"run_id": "r1", "crosses": ["j1"], "permits_full_travel": None}]}
    report = run("harness", doc)
    assert report.failures == []
    assert warns(report, "NOBODY CHECKED")


# ------------------------------------------------- ADR-0018: efficiency and basis

def actuator(**over):
    doc = {"schema_version": 0, "actuator_id": "a", "type": "hobby-servo", "source": SRC}
    doc.update(over)
    return doc


def test_scalar_gearbox_efficiency_is_refused():
    """The third instance of the same defect: a quantity varying over an operating
    envelope, stored as one number."""
    doc = actuator(gearbox={"ratio": 100, "efficiency": 0.85})
    assert refuses(run("actuator", doc), "scalar and was removed")


def test_measured_efficiency_without_a_method_is_refused():
    doc = actuator(gearbox={"ratio": 100, "measured_efficiency": [
        {"value": 0.58, "input_speed_rad_s": 104.7, "output_torque_nm": 294,
         "how_determined": "  "}]})
    assert refuses(run("actuator", doc), "no how_determined")


def test_efficiency_at_zero_input_speed_warns_that_it_is_the_wrong_quantity():
    """A held pose has zero input speed, and there is no efficiency curve there."""
    doc = actuator(gearbox={"ratio": 100, "measured_efficiency": [
        {"value": 0.58, "input_speed_rad_s": 0, "output_torque_nm": 294,
         "how_determined": "chart 3, FR gearing engineering data"}]})
    report = run("actuator", doc)
    assert report.failures == []
    assert warns(report, "gearbox that is TURNING")


def test_model_typical_without_a_spread_warns_the_width_is_unknown():
    doc = actuator(gearbox={"ratio": 100, "basis": "model-typical"})
    assert warns(run("actuator", doc), "population of unknown width")


def test_a_spread_without_a_basis_warns():
    doc = actuator(gearbox={"ratio": 100, "spread_pct": 30})
    assert warns(run("actuator", doc), "no basis")


# ------------------------------ ADR-0021: ranges, and ends that answer opposites

def gearbox_range(field, **over):
    row = {"min": 0.03, "max": 0.5, "how_determined": "vendor table, converted from N.cm"}
    row.update(over)
    return actuator(gearbox={"ratio": 100, field: row})


def test_a_torque_range_is_accepted():
    assert run("actuator", gearbox_range("starting_torque_nm")).failures == []
    assert run("actuator", gearbox_range("backdriving_torque_nm")).failures == []


def test_an_inverted_range_is_refused():
    doc = gearbox_range("backdriving_torque_nm", min=190.0, max=7.0)
    assert refuses(run("actuator", doc), "above max")


def test_a_range_with_no_method_is_refused():
    doc = gearbox_range("starting_torque_nm", how_determined="   ")
    assert refuses(run("actuator", doc), "no how_determined")


def test_a_collapsed_range_warns_that_it_is_a_value_wearing_a_range():
    """min == max validates, and it is worth surfacing: the field is a range
    because the variation is unit-to-unit, so a single figure usually means
    somebody collapsed one rather than that the vendor published one."""
    doc = gearbox_range("backdriving_torque_nm", min=50.0, max=50.0)
    report = run("actuator", doc)
    assert report.failures == []
    assert warns(report, "value wearing a range")


def test_there_is_no_typical_field_to_collapse_a_range_into():
    """ADR-0021's refusal: a typical would be read as the answer and the range
    would become decoration."""
    import json as _json
    schema = _json.loads((Path(__file__).resolve().parents[1]
                          / "schema" / "actuator.schema.json").read_text(encoding="utf-8"))
    props = schema["$defs"]["torqueRange"]["properties"]
    assert "typical" not in props
    assert schema["$defs"]["torqueRange"]["additionalProperties"] is False


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"pass  {name}")
        except AssertionError:
            failed += 1
            print(f"FAIL  {name}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
