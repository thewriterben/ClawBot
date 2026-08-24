"""Every enum value is exercised by a record, or listed here with its reason.

The point, stated once. On 2026-08-23 the schema's `type` enum had accepted
`stepper` since it was written, while every torque row required `at_volts` — so
a stepper could not be recorded without inventing a voltage. Nobody found that
by reading the schema. It was found when a real part arrived, which is how
ADR-0014, ADR-0018 and ADR-0023 all arrived.

That pattern is not random and its surface is enumerable: `type` has six values
and `data/` exercised two. The other four were each a candidate for the same
failure, sitting in a set nothing measured.

So this measures it. Unexercised is allowed — owning six kinds of actuator to
satisfy a test would be absurd — but it must be *declared*, with the reason, and
the declaration must not go stale in either direction.

Fixtures live in `tests/fixtures/` and not `data/`, because `data/` is real
records of real hardware. A fixture is a question put to the schema: can it hold
this? Every figure in one is still cited from a real listing, because a
fabricated fixture would be invented data with extra steps and would prove
nothing about a schema meeting reality.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import validate  # noqa: E402
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "actuators"


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _enum(schema: str, *path: str) -> set[str]:
    node = json.loads((ROOT / "schema" / schema).read_text(encoding="utf-8"))
    for key in path:
        node = node[key]
    return set(node["enum"])


# Why each unexercised value is unexercised. A reason, not an excuse: three of
# these are gaps in the schema rather than gaps in the shelf, and saying so is
# the whole reason this file exists.
ACTUATOR_GAPS = {
    "bldc":
        "SCHEMA GAP. The iPower GM4108H-120T publishes 'load torque 1200-1800 "
        "g-cm' at 1.5 A — a RANGE, indexed by current. `torqueAtVolts` takes a "
        "single value with a voltage and `torqueAtAmps` a single value with a "
        "current; neither takes a range. ADR-0021 already established that some "
        "torques are published as ranges, for starting and backdriving torque. "
        "This is the same shape arriving on a different field.",
}

JOINT_GAPS = {
    "continuous": "No robot here has an unlimited-rotation joint.",
    "prismatic": "No robot here has a linear joint. Note the pairing: the "
                 "actuator that would drive one cannot be recorded either.",
    "fixed": "The pan-tilt has no rigid sub-assembly worth a joint.",
    "floating": "Would need a base that is not fixed, which ADR-0009 treats as "
                "a separate problem — gravity direction becomes unknown.",
    "planar": "Nothing here moves in a plane.",
}


def _actuator_types_in_use() -> set[str]:
    found = set()
    for d in ((ROOT / "data" / "actuators"), FIXTURES):
        if d.is_dir():
            found |= {_load(p)["type"] for p in d.glob("*.json")}
    return found


def test_every_actuator_type_is_exercised_or_declared():
    declared = _actuator_types_in_use()
    for kind in sorted(_enum("actuator.schema.json", "properties", "type")):
        assert kind in declared or kind in ACTUATOR_GAPS, (
            f"actuator type {kind!r} is exercised by no record and no fixture, and "
            f"is not listed in ACTUATOR_GAPS. Either write a fixture from a real "
            f"datasheet, or say here why you cannot — an enum value nothing has "
            f"ever tried is where the last three schema gaps were found.")


def test_the_actuator_gap_list_has_not_gone_stale():
    """A known-gap list that outlives its gaps is the disease it treats."""
    declared = _actuator_types_in_use()
    for kind in ACTUATOR_GAPS:
        assert kind not in declared, (
            f"actuator type {kind!r} is listed as unexercised but a record or "
            f"fixture now uses it. Delete the entry.")


def test_every_joint_type_is_exercised_or_declared():
    used = set()
    for p in (ROOT / "data" / "robots").glob("*.json"):
        used |= {j["type"] for j in _load(p)["joints"]}
    for kind in sorted(_enum("robot.schema.json", "$defs", "joint",
                             "properties", "type")):
        assert kind in used or kind in JOINT_GAPS, (
            f"joint type {kind!r} is used by no robot and is not listed in "
            f"JOINT_GAPS")


def test_the_joint_gap_list_has_not_gone_stale():
    used = set()
    for p in (ROOT / "data" / "robots").glob("*.json"):
        used |= {j["type"] for j in _load(p)["joints"]}
    for kind in JOINT_GAPS:
        assert kind not in used, (
            f"joint type {kind!r} is listed as unexercised but a robot uses it")


@pytest.mark.parametrize("path", sorted(FIXTURES.glob("*.json")),
                         ids=lambda p: p.stem)
def test_each_fixture_is_a_valid_record(path):
    """A fixture that does not validate proves nothing about the schema."""
    report = validate.Report()
    validate.check_actuator(path, report)
    assert report.failures == [], f"{path.name}: {report.failures}"


def test_there_is_at_least_one_fixture():
    """Guards the parametrize above: an empty glob makes it vacuously green."""
    assert list(FIXTURES.glob("*.json")), "no fixtures found"
