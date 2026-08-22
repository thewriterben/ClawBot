#!/usr/bin/env python3
"""Validate robots, actuators, assemblies and harnesses — and the claims they make.

    python scripts/validate.py [--data <dir>]

Structure is the easy half and the JSON Schema files already describe it. What a
schema cannot express is the half that matters here:

* **The graph is a tree.** A robot's joints must form a tree rooted at
  `base_link` — every link reachable, no cycles, no second root. JSON Schema
  cannot see across array elements, so this is the first thing checked.
* **Radians are hostile to hand-authoring.** `1.5708` is not a number anyone
  recognises as a right angle, and a typed `90` in a `_rad` field is a plausible
  mistake. ADR-0005 accepted that cost and named the range check as "the main
  defence this decision leaves standing". It is implemented here, plus a
  *warning* for the middle cases a range check cannot catch.
* **A citation gate.** A joint limit is a physical claim about hardware.
  `TODO(source)` is a legal citation and is expected to fail loudly downstream —
  so it is counted and reported, never silently accepted.
* **Absence must stay absence.** A `mimic` that is really a cycle, a harness that
  narrows a joint without saying how it was determined, a continuous torque
  figure derived from a rule of thumb — each is a way for a guess to enter
  wearing the shape of a fact.

Stdlib only, matching OpenPartsCore's and OpenBuildCore's validators. Nothing here
imports a peer repo: a `part_id` and a `provenance_ref` are stored, not resolved
(ADR-0006), so this validator deliberately cannot tell you whether a part exists.
That is OpenBuildCore's question and it needs the drawer, not the schema.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RAD_LIMIT = 4 * math.pi                      # +/- 4*pi, the schema's own bound
NEEDS_AXIS = {"revolute", "continuous", "prismatic"}
NEEDS_LIMITS_IN_URDF = {"revolute", "prismatic"}
UNBOUNDED_BASE = {"floating", "planar"}      # ADR-0009: no meaningful limits
JOINT_TYPES = {"revolute", "continuous", "prismatic", "fixed", "floating", "planar"}

# ADR-0004: "a rule of thumb applied to stall torque is not a determination -
# it is a guess wearing a citation." A validator cannot read intent, but these
# are the words that show up when someone does it anyway.
RULE_OF_THUMB = re.compile(
    r"\b(stall|rule[ -]of[ -]thumb|percent|%|fraction|typical|assum|estimat|approx)",
    re.IGNORECASE,
)


class Report:
    """Failures block; warnings are findings a human should look at."""

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []
        self.todo_sources = 0

    def fail(self, where: str, message: str) -> None:
        self.failures.append(f"{where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")


def check_source(report: Report, where: str, what: str, source) -> None:
    """Every physical claim carries a citation. TODO(source) counts and is reported."""
    if source is None:
        report.fail(where, f"{what} has no source; a physical claim needs a citation")
        return
    citation = (source or {}).get("citation")
    if not citation:
        report.fail(where, f"{what} has a source with no citation")
    elif citation.strip().startswith("TODO(source)"):
        report.todo_sources += 1
        report.warn(where, f"{what} cites TODO(source) — blocks downstream until replaced")


def check_rad(report: Report, where: str, field: str, value) -> None:
    """The main defence ADR-0005 leaves standing, plus the case it cannot catch."""
    if value is None:
        return
    if not isinstance(value, (int, float)):
        report.fail(where, f"{field} is not a number")
        return
    if abs(value) > RAD_LIMIT:
        report.fail(
            where,
            f"{field} = {value} is outside +/-4*pi ({RAD_LIMIT:.3f}). "
            f"If this is degrees, it is {math.radians(value):.4f} rad",
        )
        return
    # 6.29 < |v| <= 4*pi is legal (multi-turn) but 90, 180, 45 are not in range at
    # all, so the dangerous survivors are small integers: 3 is plausibly 3 rad and
    # plausibly a typo for 30 degrees. open-questions.md #4 names this exactly.
    if isinstance(value, int) and 2 <= abs(value) <= 12:
        report.warn(
            where,
            f"{field} = {value} is a bare integer in radians ({math.degrees(value):.1f} deg). "
            f"In range, so not refused — but if degrees were meant this is the error "
            f"ADR-0005's range check cannot catch",
        )


# --------------------------------------------------------------------------- robot

def check_robot(path: Path, report: Report) -> dict | None:
    where = path.name
    try:
        robot = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.fail(where, f"invalid JSON: {exc}")
        return None

    for field in ("schema_version", "robot_id", "kind", "base_link", "links", "joints"):
        if field not in robot:
            report.fail(where, f"missing required field '{field}'")
    if report.failures:
        return None

    check_source(report, where, "robot", robot.get("source"))

    # ADR-0019: the author's declaration, never ClawBot's inference.
    policy = robot.get("policy")
    if policy:
        if not (policy.get("taxonomy_version") or "").strip():
            report.fail(where, "policy declares categories with no taxonomy_version. A "
                               "category id without the version of the list it came "
                               "from is a string whose meaning lives somewhere else")
        if not policy.get("categories"):
            report.fail(where, "policy is present with no categories; omit the field "
                               "entirely rather than declaring nothing")
        if not policy.get("declared_by"):
            report.warn(where, "policy has no declared_by — a declaration is a claim a "
                               "person makes, so it has an author rather than a method")
    else:
        report.warn(where, "no policy declaration (PD-5). Every derivation still runs; "
                           "what this blocks is manifest.py --as-project, because "
                           "emitting a fabrication-bound document would make the 'none' "
                           "declaration on your behalf (ADR-0019)")

    # ---- links: exactly one kind (ADR-0006)
    links: dict[str, dict] = {}
    for link in robot.get("links", []):
        lid = link.get("link_id", "<unnamed>")
        if not ID_RE.match(lid or ""):
            report.fail(where, f"link id '{lid}' is not a lowercase slug")
        if lid in links:
            report.fail(where, f"duplicate link_id '{lid}'")
        links[lid] = link
        kinds = [k for k in ("part_id", "make", "provenance_ref") if link.get(k)]
        if len(kinds) != 1:
            report.fail(
                where,
                f"link '{lid}' declares {len(kinds)} of part_id/make/provenance_ref; "
                f"exactly one is required (ADR-0006)",
            )

    base = robot.get("base_link")
    if base not in links:
        report.fail(where, f"base_link '{base}' is not a declared link")

    # ---- joints
    joints: dict[str, dict] = {}
    children: dict[str, str] = {}     # child link -> joint that parents it
    for joint in robot.get("joints", []):
        jid = joint.get("joint_id", "<unnamed>")
        jwhere = f"{where} joint '{jid}'"
        if jid in joints:
            report.fail(where, f"duplicate joint_id '{jid}'")
        joints[jid] = joint

        jtype = joint.get("type")
        if jtype not in JOINT_TYPES:
            report.fail(jwhere, f"type '{jtype}' is not one of URDF's six")

        for end in ("parent", "child"):
            lid = joint.get(end)
            if lid not in links:
                report.fail(jwhere, f"{end} '{lid}' is not a declared link")
        if joint.get("parent") == joint.get("child"):
            report.fail(jwhere, "parent and child are the same link")

        child = joint.get("child")
        if child in children:
            report.fail(
                jwhere,
                f"link '{child}' is already the child of joint '{children[child]}'; "
                f"two parents is a loop, not a tree (ADR-0008)",
            )
        elif child:
            children[child] = jid

        check_source(report, jwhere, "joint", joint.get("source"))

        # axis: required except fixed, and never the zero vector
        axis = joint.get("axis")
        if jtype in NEEDS_AXIS:
            if not axis:
                report.fail(jwhere, f"type '{jtype}' requires an axis")
            elif all(abs(axis.get(k, 0)) < 1e-12 for k in "xyz"):
                report.fail(jwhere, "axis is the zero vector")

        # limits
        limits = joint.get("limits")
        if limits:
            if jtype in UNBOUNDED_BASE:
                report.fail(
                    jwhere,
                    f"type '{jtype}' carries limits; its travel is bounded by an "
                    f"environment, which this repo does not model (ADR-0009)",
                )
            for f in ("lower_rad", "upper_rad"):
                check_rad(report, jwhere, f"limits.{f}", limits.get(f))
            lo, hi = limits.get("lower_rad"), limits.get("upper_rad")
            if lo is not None and hi is not None and lo > hi:
                report.fail(jwhere, f"limits.lower_rad ({lo}) exceeds upper_rad ({hi})")
            lo, hi = limits.get("lower_mm"), limits.get("upper_mm")
            if lo is not None and hi is not None and lo > hi:
                report.fail(jwhere, f"limits.lower_mm ({lo}) exceeds upper_mm ({hi})")
            check_source(report, jwhere, "joint limits", limits.get("source"))
        elif jtype in NEEDS_LIMITS_IN_URDF:
            # Not a failure. This is the honest state ADR-0003 exists to handle.
            report.warn(
                jwhere,
                f"type '{jtype}' has no limits: UNKNOWN, never unlimited. Reachability "
                f"answers 'incomplete' naming this joint, and URDF export refuses "
                f"(ADR-0003, ADR-0007)",
            )

        if joint.get("origin", {}).get("rpy_rad"):
            for k in ("r", "p", "y"):
                check_rad(report, jwhere, f"origin.rpy_rad.{k}",
                          joint["origin"]["rpy_rad"].get(k))

    # ---- mimic (ADR-0008)
    for jid, joint in joints.items():
        mimic = joint.get("mimic")
        if not mimic:
            continue
        jwhere = f"{where} joint '{jid}'"
        target = mimic.get("joint")
        if target not in joints:
            report.fail(jwhere, f"mimic names joint '{target}', which does not exist")
            continue
        if target == jid:
            report.fail(jwhere, "mimic names itself")
        if joints[target].get("type") == "fixed":
            report.fail(jwhere, f"mimic names fixed joint '{target}', which never moves")
        if joint.get("type") == "fixed":
            report.fail(jwhere, "a fixed joint cannot mimic; it has no value to follow")

    # mimic cycles
    for jid in joints:
        seen, cur = set(), jid
        while cur and (m := joints.get(cur, {}).get("mimic")):
            cur = m.get("joint")
            if cur in seen or cur == jid:
                report.fail(where, f"mimic cycle involving joint '{jid}' (ADR-0008)")
                break
            seen.add(cur)

    # ---- the tree: every link reachable from base_link
    if base in links:
        reached, frontier = {base}, [base]
        adjacency: dict[str, list[str]] = {}
        for joint in joints.values():
            adjacency.setdefault(joint.get("parent"), []).append(joint.get("child"))
        while frontier:
            node = frontier.pop()
            for child in adjacency.get(node, []):
                if child and child not in reached:
                    reached.add(child)
                    frontier.append(child)
        for orphan in sorted(set(links) - reached):
            report.fail(
                where,
                f"link '{orphan}' is not reachable from base_link '{base}' — "
                f"the graph must be a tree rooted there",
            )

    # ---- measured_payload (ADR-0004)
    for i, mp in enumerate(robot.get("measured_payload") or []):
        mwhere = f"{where} measured_payload[{i}]"
        for jid, value in (mp.get("pose_rad") or {}).items():
            if jid not in joints:
                report.fail(mwhere, f"pose names joint '{jid}', which does not exist")
                continue
            if joints[jid].get("type") == "prismatic":
                continue                      # millimetres for a prismatic joint
            check_rad(report, mwhere, f"pose_rad.{jid}", value)
        if not (mp.get("how_measured") or "").strip():
            report.fail(mwhere, "measured payload has no how_measured (ADR-0004)")
        if mp.get("sustained") is None:
            report.warn(mwhere, "sustained not declared — a mass lifted once is not a "
                                "mass the mechanism can hold")

    return {"robot": robot, "links": links, "joints": joints}


# ----------------------------------------------------------------------- actuator

def check_actuator(path: Path, report: Report) -> str | None:
    where = path.name
    try:
        act = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.fail(where, f"invalid JSON: {exc}")
        return None

    for field in ("schema_version", "actuator_id", "type"):
        if field not in act:
            report.fail(where, f"missing required field '{field}'")
    check_source(report, where, "actuator", act.get("source"))

    # Voltage-indexed arrays (ADR-0014). The voltage is the index, not an
    # annotation, so a duplicate or missing one makes the row unlookupable.
    for field in ("stall_torque_nm", "continuous_torque_nm", "no_load_speed_rad_s"):
        rows = act.get(field)
        if rows is None:
            continue
        if not isinstance(rows, list):
            report.fail(where, f"{field} is not an array. Torque against voltage is a "
                               f"curve and one point on it is not the figure (ADR-0014)")
            continue
        seen_volts = set()
        for row in rows:
            volts = row.get("at_volts")
            if volts is None:
                report.fail(where, f"{field} row has no at_volts; a torque or speed "
                                   f"figure without its supply voltage is not a figure")
            elif volts in seen_volts:
                report.fail(where, f"{field} has two rows at {volts} V — the voltage "
                                   f"is the index a derivation looks the row up by")
            else:
                seen_volts.add(volts)

    # Guarded: a non-list here was already reported above, and iterating a dict
    # would yield its keys and crash on the next .get().
    cont = act.get("continuous_torque_nm")
    cont = cont if isinstance(cont, list) else []
    stall_rows = act.get("stall_torque_nm")
    stall = {r.get("at_volts"): r.get("value")
             for r in (stall_rows if isinstance(stall_rows, list) else [])}
    for row in cont:
        volts = row.get("at_volts")
        how = (row.get("how_determined") or "").strip()
        if not how:
            report.fail(where, f"continuous_torque_nm at {volts} V has no "
                               f"how_determined (ADR-0004)")
        elif RULE_OF_THUMB.search(how):
            report.fail(
                where,
                f"continuous_torque_nm at {volts} V has a how_determined that reads "
                f"like a rule of thumb ({how!r}). ADR-0004: only a datasheet continuous "
                f"rating or a measurement with its method. A fraction of stall torque "
                f"is a guess wearing a citation",
            )
        if not row.get("thermal_basis"):
            report.warn(where, f"continuous_torque_nm at {volts} V has no thermal_basis "
                               f"— a torque held for ten seconds is not a continuous one")
        if volts in stall and row.get("value", 0) >= stall[volts]:
            report.fail(where, f"continuous_torque_nm at {volts} V is not less than "
                               f"stall_torque_nm at the same voltage")
    if not cont and act.get("stall_torque_nm"):
        report.warn(where, "stall torque only, continuous is null: capacity is "
                           "underivable and that is the honest answer (ADR-0004)")

    travel = act.get("travel") or {}
    for f in ("lower_rad", "upper_rad"):
        check_rad(report, where, f"travel.{f}", travel.get(f))

    gearbox = act.get("gearbox") or {}
    if gearbox.get("backlash_rad") == 0:
        report.warn(where, "gearbox.backlash_rad is 0 — absent means UNKNOWN; a "
                           "measured zero is extraordinary and needs its method")
    if "efficiency" in gearbox:
        report.fail(where, "gearbox.efficiency is a scalar and was removed (ADR-0018). "
                           "Efficiency varies with input speed, ratio, load, temperature "
                           "and lubricant — use measured_efficiency, which requires the "
                           "operating point that makes a figure mean something")

    # ADR-0018: a value may describe a product line or the unit on your bench.
    for row in gearbox.get("measured_efficiency") or []:
        speed = row.get("input_speed_rad_s")
        if not (row.get("how_determined") or "").strip():
            report.fail(where, "measured_efficiency row has no how_determined")
        if speed == 0:
            report.warn(
                where,
                "measured_efficiency at zero input speed: published efficiency curves "
                "describe a gearbox that is TURNING. What governs a stationary geartrain "
                "is starting and backdriving torque, which are different quantities "
                "(ADR-0018)")
    if gearbox.get("spread_pct") is not None and gearbox.get("basis") is None:
        report.warn(where, "gearbox.spread_pct is declared with no basis — a spread is a "
                           "statement about a population, so the basis should say "
                           "'model-typical'")
    if gearbox.get("basis") == "model-typical" and gearbox.get("spread_pct") is None:
        report.warn(where, "gearbox.basis is model-typical with no spread_pct: the "
                           "figure describes a population of unknown width. Absent means "
                           "UNKNOWN, not zero (ADR-0018)")

    return act.get("actuator_id")


# ----------------------------------------------------------- assembly and harness

def check_assembly(path: Path, report: Report, robots: dict) -> None:
    where = path.name
    try:
        asm = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.fail(where, f"invalid JSON: {exc}")
        return

    check_source(report, where, "assembly", asm.get("source"))
    model = robots.get(asm.get("robot_id"))
    if asm.get("robot_id") and model is None:
        report.warn(where, f"robot_id '{asm.get('robot_id')}' is not in data/robots/")

    steps = {s.get("step_id"): s for s in asm.get("steps", [])}
    for sid, step in steps.items():
        swhere = f"{where} step '{sid}'"
        for dep in step.get("depends_on") or []:
            if dep not in steps:
                report.fail(swhere, f"depends_on '{dep}', which is not a step")
        if model:
            for lid in step.get("joins") or []:
                if lid not in model["links"]:
                    report.fail(swhere, f"joins link '{lid}', not in the robot record")
        for f in step.get("fasteners") or []:
            kinds = [k for k in ("part_id", "spec") if f.get(k)]
            if len(kinds) != 1:
                report.fail(swhere, "fastener needs exactly one of part_id or spec")
            torque = f.get("torque_nm")
            if torque:
                check_source(report, swhere, "fastener torque", torque.get("source"))
            elif step.get("irreversible"):
                report.warn(swhere, "irreversible step with an untorqued fastener — "
                                    "absent means UNKNOWN, not hand tight (ADR-0011)")

    # DAG (ADR-0011)
    state: dict[str, int] = {}

    def visit(sid: str) -> bool:
        if state.get(sid) == 1:
            return False
        if state.get(sid) == 2:
            return True
        state[sid] = 1
        for dep in steps.get(sid, {}).get("depends_on") or []:
            if dep in steps and not visit(dep):
                return False
        state[sid] = 2
        return True

    for sid in steps:
        if not visit(sid):
            report.fail(where, f"step dependency cycle involving '{sid}' (ADR-0011)")
            break

    mbt = asm.get("measured_build_time")
    if mbt and not (mbt.get("how_measured") or "").strip():
        report.fail(where, "measured_build_time has no how_measured (ADR-0011)")


def check_harness(path: Path, report: Report, robots: dict) -> None:
    where = path.name
    try:
        h = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.fail(where, f"invalid JSON: {exc}")
        return

    check_source(report, where, "harness", h.get("source"))
    model = robots.get(h.get("robot_id"))
    if h.get("robot_id") and model is None:
        report.warn(where, f"robot_id '{h.get('robot_id')}' is not in data/robots/")

    seen_addr: dict[tuple, str] = {}
    driven: set[str] = set()
    for ch in h.get("channels") or []:
        jid = ch.get("joint_id")
        cwhere = f"{where} channel for '{jid}'"
        if model and jid not in model["joints"]:
            report.fail(cwhere, f"joint '{jid}' is not in the robot record")
        if jid in driven:
            report.fail(cwhere, f"joint '{jid}' is driven by two channels")
        driven.add(jid)
        check_rad(report, cwhere, "zero_offset_rad", ch.get("zero_offset_rad"))
        if ch.get("bus_address") is not None:
            key = (ch.get("bus"), ch.get("bus_address"))
            if key in seen_addr:
                report.fail(cwhere, f"bus address {key[1]} on {key[0]} is already used "
                                    f"by joint '{seen_addr[key]}'")
            seen_addr[key] = jid
        if ch.get("inverted") is None:
            report.warn(cwhere, "inverted not declared — the most common reason a "
                                "correct model drives a mechanism into its end stop")

    for run in h.get("routing") or []:
        rwhere = f"{where} run '{run.get('run_id')}'"
        crossed = run.get("crosses") or []
        if model:
            for jid in crossed:
                if jid not in model["joints"]:
                    report.fail(rwhere, f"crosses joint '{jid}', not in the robot record")
        if crossed and run.get("permits_full_travel") is None and not run.get("travel_limit"):
            report.warn(
                rwhere,
                f"crosses {len(crossed)} joint(s) with permits_full_travel null and no "
                f"travel_limit: NOBODY CHECKED. Reachability over this robot over-claims "
                f"and must say so (ADR-0012)",
            )
        for tl in run.get("travel_limit") or []:
            if not (tl.get("how_determined") or "").strip():
                report.fail(rwhere, "travel_limit has no how_determined (ADR-0012)")
            for f in ("lower_rad", "upper_rad"):
                check_rad(report, rwhere, f"travel_limit.{f}", tl.get(f))


# ----------------------------------------------------------------------------- main

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    args = parser.parse_args()

    report = Report()
    robots: dict[str, dict] = {}
    counts = {}

    robot_files = sorted((args.data / "robots").glob("*.json"))
    for path in robot_files:
        model = check_robot(path, report)
        if model:
            robots[model["robot"].get("robot_id")] = model
    counts["robot"] = len(robot_files)

    actuator_files = sorted((args.data / "actuators").glob("*.json"))
    actuator_ids = {a for p in actuator_files if (a := check_actuator(p, report))}
    counts["actuator"] = len(actuator_files)

    # every actuator_id a joint names must exist in data/actuators/
    for rid, model in robots.items():
        for jid, joint in model["joints"].items():
            aid = joint.get("actuator_id")
            if aid and aid not in actuator_ids:
                report.fail(f"{rid} joint '{jid}'",
                            f"actuator_id '{aid}' is not in data/actuators/")

    for directory, label, checker in (
        ("assemblies", "assembly", check_assembly),
        ("harnesses", "harness", check_harness),
    ):
        files = sorted((args.data / directory).glob("*.json"))
        for path in files:
            checker(path, report, robots)
        counts[label] = len(files)

    for failure in report.failures:
        print(f"FAIL {failure}")
    for warning in report.warnings:
        print(f"warn {warning}")

    plural = {"robot": "robots", "actuator": "actuators",
              "assembly": "assemblies", "harness": "harnesses"}
    described = ", ".join(
        f"{n} {k if n == 1 else plural[k]}" for k, n in counts.items())
    print(f"\nchecked {described}")
    if report.todo_sources:
        print(f"{report.todo_sources} TODO(source) placeholder(s) — these block "
              f"downstream answers until replaced, which is what they are for")
    if not any(counts.values()):
        print("nothing to check: data/ is empty on purpose until a real mechanism "
              "with real datasheets arrives (see data/robots/README.md)")
    print("all valid" if not report.failures
          else f"{len(report.failures)} problem(s)")
    return 1 if report.failures else 0


if __name__ == "__main__":
    sys.exit(main())
