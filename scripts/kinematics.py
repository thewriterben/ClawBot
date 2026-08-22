#!/usr/bin/env python3
"""Forward kinematics, sampled reachability, and static capacity.

    python scripts/kinematics.py fk    <robot_id> [--pose j1=0.5,j2=-0.2]
    python scripts/kinematics.py reach <robot_id> [--target X,Y,Z] [--samples N] [--seed S]
    python scripts/kinematics.py hold  <robot_id> --pose j1=0.5 [--payload-g N]

Three answers, and the same discipline behind all of them: **the assumptions that
make an answer true travel inside the answer**, never in documentation
(inherited invariant #4).

* **fk** composes each joint's transform down the tree. Lynch and Park teach this
  via the product of exponentials; for a branching tree, composing homogeneous
  transforms is the same result regrouped, and it is what URDF's own semantics
  define. See `Knowledge/sources/forward-kinematics.md`.
* **reach** samples the joint space (ADR-0013). "Reachable" is a claim — a sample
  got there. **"Not reachable" is not a claim** — it means no sample landed
  within tolerance in N draws, and N travels in the verdict.
* **hold** derives static gravity load per joint from `continuous_torque_nm`, and
  is an upper bound because efficiency, friction and acceleration are not
  modelled (ADR-0004). The word "upper bound" travels with the number.

Any missing input makes the answer `incomplete` and **names what is missing** —
never a default that lets the computation proceed. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
G = 9.80665                     # m/s^2, standard gravity
MM_PER_M = 1000.0
UNDETERMINED = {"floating", "planar"}


# ------------------------------------------------------------------ 4x4 transforms

IDENTITY = ((1.0, 0, 0, 0), (0, 1.0, 0, 0), (0, 0, 1.0, 0), (0, 0, 0, 1.0))


def mul(a, b):
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4))
        for i in range(4)
    )


def translation(x, y, z):
    return ((1.0, 0, 0, x), (0, 1.0, 0, y), (0, 0, 1.0, z), (0, 0, 0, 1.0))


def rpy_matrix(r, p, y):
    """Fixed-axis roll-pitch-yaw applied in X, Y, Z order — REP-103 and URDF."""
    cr, sr, cp, sp, cy, sy = (math.cos(r), math.sin(r), math.cos(p),
                              math.sin(p), math.cos(y), math.sin(y))
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr, 0.0),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr, 0.0),
        (-sp,     cp * sr,                cp * cr,                0.0),
        (0.0, 0.0, 0.0, 1.0),
    )


def axis_rotation(axis, angle):
    """Rodrigues. The axis is normalised here; a zero axis is refused by the validator."""
    x, y, z = axis
    n = math.sqrt(x * x + y * y + z * z)
    x, y, z = x / n, y / n, z / n
    c, s, t = math.cos(angle), math.sin(angle), 1 - math.cos(angle)
    return (
        (t * x * x + c,     t * x * y - s * z, t * x * z + s * y, 0.0),
        (t * x * y + s * z, t * y * y + c,     t * y * z - s * x, 0.0),
        (t * x * z - s * y, t * y * z + s * x, t * z * z + c,     0.0),
        (0.0, 0.0, 0.0, 1.0),
    )


def origin_matrix(origin: dict):
    origin = origin or {}
    xyz = origin.get("xyz_mm") or {}
    rpy = origin.get("rpy_rad") or {}
    return mul(
        translation(xyz.get("x", 0.0), xyz.get("y", 0.0), xyz.get("z", 0.0)),
        rpy_matrix(rpy.get("r", 0.0), rpy.get("p", 0.0), rpy.get("y", 0.0)),
    )


def position(matrix):
    return (matrix[0][3], matrix[1][3], matrix[2][3])


def distance(a, b):
    return math.sqrt(sum((p - q) ** 2 for p, q in zip(a, b)))


# ------------------------------------------------------------------------- model

class Incomplete(Exception):
    """The one honest failure. Carries what is missing, never a default."""

    def __init__(self, missing: str, detail: str):
        super().__init__(f"{missing}: {detail}")
        self.missing = missing
        self.detail = detail


def load_robot(robot_id: str) -> dict:
    for path in sorted((ROOT / "data" / "robots").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("robot_id") == robot_id:
            return doc
    raise SystemExit(f"no robot '{robot_id}' in data/robots/")


def load_actuator(actuator_id: str) -> dict | None:
    for path in sorted((ROOT / "data" / "actuators").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("actuator_id") == actuator_id:
            return doc
    return None


def joint_index(robot: dict) -> dict:
    return {j["joint_id"]: j for j in robot.get("joints", [])}


def free_joints(robot: dict) -> list[dict]:
    """Joints a caller may set. A mimic follows another and is not free (ADR-0008)."""
    return [j for j in robot.get("joints", [])
            if j.get("type") not in ("fixed",) and not j.get("mimic")]


def resolve_pose(robot: dict, pose: dict) -> dict:
    """Fill in mimic joints from the joints they follow."""
    joints = joint_index(robot)
    resolved = dict(pose)
    for _ in range(len(joints) + 1):          # iterate to settle chained mimics
        changed = False
        for jid, joint in joints.items():
            mimic = joint.get("mimic")
            if not mimic or jid in resolved:
                continue
            target = mimic.get("joint")
            if target in resolved:
                resolved[jid] = (resolved[target] * mimic.get("multiplier", 1)
                                 + mimic.get("offset", 0))
                changed = True
        if not changed:
            break
    return resolved


def joint_transform(joint: dict, value: float):
    jtype = joint.get("type")
    origin = origin_matrix(joint.get("origin"))
    if jtype == "fixed":
        return origin
    if jtype in UNDETERMINED:
        raise Incomplete(
            f"joint '{joint['joint_id']}'",
            f"type '{jtype}' has no value determined by the mechanism — its pose "
            f"comes from a localization stack, which this repo does not model (ADR-0009)",
        )
    axis = joint.get("axis") or {}
    vec = (axis.get("x", 0.0), axis.get("y", 0.0), axis.get("z", 0.0))
    if jtype in ("revolute", "continuous"):
        return mul(origin, axis_rotation(vec, value))
    if jtype == "prismatic":
        n = math.sqrt(sum(c * c for c in vec))
        return mul(origin, translation(*(c / n * value for c in vec)))
    raise Incomplete(f"joint '{joint['joint_id']}'", f"unknown type '{jtype}'")


def forward_kinematics(robot: dict, pose: dict) -> dict:
    """link_id -> 4x4 pose in the base frame. Every frame here is base-relative."""
    pose = resolve_pose(robot, pose)
    frames = {robot["base_link"]: IDENTITY}
    joints = list(robot.get("joints", []))
    for _ in range(len(joints) + 1):
        progressed = False
        for joint in joints:
            parent, child = joint.get("parent"), joint.get("child")
            if parent in frames and child not in frames:
                value = pose.get(joint["joint_id"], 0.0)
                frames[child] = mul(frames[parent], joint_transform(joint, value))
                progressed = True
        if not progressed:
            break
    return frames


def tool_matrix(robot: dict, frames: dict):
    """The flange pose with the tool offset applied — the frame ADR-0003 insists on."""
    tool = robot.get("tool")
    parented = {j["child"] for j in robot.get("joints", [])}
    leaves = [lid for lid in frames if lid not in
              {j["parent"] for j in robot.get("joints", [])}]
    attach = (tool or {}).get("attached_to") or (leaves[0] if leaves else robot["base_link"])
    if attach not in frames:
        raise Incomplete("tool", f"attached_to '{attach}' has no computed frame")
    if not tool:
        return frames[attach], None
    return mul(frames[attach], origin_matrix(tool.get("offset"))), tool


def tool_offset_description(robot: dict) -> str:
    tool = robot.get("tool")
    if tool is None:
        return "none declared (null is a declaration, not an omission)"
    xyz = (tool.get("offset") or {}).get("xyz_mm") or {}
    return (f"tool '{tool.get('tool_id', 'unnamed')}' at "
            f"({xyz.get('x', 0)}, {xyz.get('y', 0)}, {xyz.get('z', 0)}) mm")


# -------------------------------------------------------------------- reachability

def sample_ranges(robot: dict) -> list[tuple]:
    """(joint, lower, upper) for every free joint. Unknown limits stop the computation."""
    ranges = []
    for joint in free_joints(robot):
        jtype, jid = joint.get("type"), joint["joint_id"]
        if jtype == "continuous":
            ranges.append((joint, -math.pi, math.pi))
            continue
        if jtype in UNDETERMINED:
            raise Incomplete(
                f"joint '{jid}'",
                f"type '{jtype}' is not bounded by the mechanism (ADR-0009)")
        limits = joint.get("limits")
        if not limits:
            raise Incomplete(
                f"joint '{jid}'",
                "no limits. UNKNOWN is never unlimited — assuming full travel would "
                "claim points the mechanism cannot reach (ADR-0003)")
        lo = limits.get("lower_rad", limits.get("lower_mm"))
        hi = limits.get("upper_rad", limits.get("upper_mm"))
        if lo is None or hi is None:
            raise Incomplete(f"joint '{jid}'", "limits are present but incomplete")
        ranges.append((joint, lo, hi))
    return ranges


def sample_workspace(robot: dict, samples: int, seed: int) -> list[tuple]:
    """Deterministic given (robot, samples, seed) — ADR-0013."""
    ranges = sample_ranges(robot)
    rng = random.Random(seed)
    points = []

    # Limit extremes first: a uniform draw reaches a corner of an n-joint space
    # with probability approaching zero, and the interesting reach is at the limits.
    corners = [{}]
    for joint, lo, hi in ranges:
        corners = [dict(c, **{joint["joint_id"]: v}) for c in corners for v in (lo, hi)]
        if len(corners) > 4096:               # 12 joints of corners is already plenty
            corners = corners[:4096]
            break

    for pose in corners:
        frames = forward_kinematics(robot, pose)
        points.append((position(tool_matrix(robot, frames)[0]), pose))

    for _ in range(samples):
        pose = {j["joint_id"]: rng.uniform(lo, hi) for j, lo, hi in ranges}
        frames = forward_kinematics(robot, pose)
        points.append((position(tool_matrix(robot, frames)[0]), pose))

    return points


def harness_status(robot_id: str) -> str:
    """ADR-0012: an unchecked cable run makes reach over-claim, and must say so."""
    directory = ROOT / "data" / "harnesses"
    found = None
    for path in sorted(directory.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("robot_id") == robot_id:
            found = doc
            break
    if found is None:
        return "no harness record: cable routing unknown, so travel may be narrower"
    runs = [r for r in found.get("routing") or [] if r.get("crosses")]
    unchecked = [r["run_id"] for r in runs
                 if r.get("permits_full_travel") is None and not r.get("travel_limit")]
    if not runs:
        return "harness declares no runs crossing joints"
    if unchecked:
        return (f"{len(unchecked)} cable run(s) cross joints with permits_full_travel "
                f"null ({', '.join(unchecked)}): nobody checked, so this over-claims")
    return "harness checked: every run crossing a joint declares its travel"


def reach_verdict(robot: dict, target, tolerance_mm: float,
                  samples: int, seed: int) -> dict:
    """Every assumption that makes this true is in the returned value."""
    base = {
        "robot_id": robot.get("robot_id"),
        "relative_to": robot["base_link"],
        "frame_note": ("all coordinates are relative to base_link; this is never a "
                       "world claim, because this repo has no source for where the "
                       "base is (ADR-0009)"),
        "tool_offset": tool_offset_description(robot),
    }
    try:
        points = sample_workspace(robot, samples, seed)
    except Incomplete as exc:
        return dict(base, verdict="incomplete", missing=exc.missing, detail=exc.detail)

    base.update({
        "samples": len(points),
        "random_samples": samples,
        "seed": seed,
        "caveats": [
            "joint-limit result, NOT a collision result: self-collision is not "
            "modelled, so this over-claims (ADR-0003)",
            harness_status(robot.get("robot_id")),
        ],
    })

    if target is None:
        xs = [p[0][0] for p in points]
        ys = [p[0][1] for p in points]
        zs = [p[0][2] for p in points]
        return dict(base, verdict="sampled", sampled_extent_mm={
            "x": [min(xs), max(xs)], "y": [min(ys), max(ys)], "z": [min(zs), max(zs)]},
            extent_note=("the extent of points SAMPLED, not the boundary of the "
                         "workspace. A sampled set is inner-bounded: it under-claims "
                         "by an unknown amount and is not a reach figure (ADR-0013)"))

    best, best_pose = min(((distance(p, target), pose) for p, pose in points),
                          key=lambda t: t[0])
    if best <= tolerance_mm:
        return dict(base, verdict="reachable", target_mm=list(target),
                    tolerance_mm=tolerance_mm, nearest_sample_mm=round(best, 4),
                    pose={k: round(v, 6) for k, v in sorted(best_pose.items())})
    return dict(
        base, verdict="no-sample-reached-it", target_mm=list(target),
        tolerance_mm=tolerance_mm, nearest_sample_mm=round(best, 4),
        detail=(f"no sample came within {tolerance_mm} mm in {len(points)} samples. "
                f"This is NOT a claim that the point is unreachable — a sampled "
                f"workspace only ever proves the positive (ADR-0013). Raise --samples "
                f"or --tolerance to test harder."))


# ---------------------------------------------------------------- static capacity

def supply_volts(robot_id: str) -> float | None:
    """From the harness, because the supply voltage is a fact about the built machine
    and the actuator's datasheet cannot know it (ADR-0014)."""
    for path in sorted((ROOT / "data" / "harnesses").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("robot_id") == robot_id:
            return (doc.get("power") or {}).get("supply_volts")
    return None


def joint_capacity_nm(joint: dict, volts: float | None) -> float:
    """The lesser of what the motor sustains and what the joint is allowed to produce."""
    jid = joint["joint_id"]
    available = []

    limits = joint.get("limits") or {}
    if limits.get("effort_nm"):
        available.append(limits["effort_nm"])

    aid = joint.get("actuator_id")
    if aid:
        actuator = load_actuator(aid)
        if actuator is None:
            raise Incomplete(f"joint '{jid}'",
                             f"actuator '{aid}' is not in data/actuators/")
        rows = actuator.get("continuous_torque_nm")
        if not rows:
            raise Incomplete(
                f"actuator '{aid}'",
                "no continuous_torque_nm. Most datasheets publish stall torque and "
                "nothing else — including good ones. Stall may not feed a capacity "
                "derivation (ADR-0004), and a fraction of it is a guess.")
        if volts is None:
            raise Incomplete(
                "harness supply voltage",
                f"actuator '{aid}' publishes continuous torque at "
                f"{', '.join(str(r['at_volts']) for r in rows)} V and no harness "
                f"declares power.supply_volts for this robot. Picking a row would be "
                f"an invisible choice, and picking the lowest 'to be safe' "
                f"under-reports capacity (ADR-0014).")
        match = [r for r in rows if abs(r["at_volts"] - volts) < 1e-9]
        if not match:
            raise Incomplete(
                f"actuator '{aid}' at {volts} V",
                f"published rows are at {', '.join(str(r['at_volts']) for r in rows)} V. "
                f"Interpolation is refused: torque against voltage is approximately "
                f"linear and 'approximately' is an unsourced model whose output would "
                f"be indistinguishable from a datasheet value (ADR-0014).")
        available.append(match[0]["value"] * (joint.get("gear_ratio") or 1))

    if not available:
        raise Incomplete(f"joint '{jid}'",
                         "no actuator_id and no limits.effort_nm — nothing to derive from")
    return min(available)


def descendants(robot: dict, link_id: str) -> set:
    out, frontier = set(), [link_id]
    children = {}
    for j in robot.get("joints", []):
        children.setdefault(j["parent"], []).append(j["child"])
    while frontier:
        node = frontier.pop()
        for child in children.get(node, []):
            if child not in out:
                out.add(child)
                frontier.append(child)
    return out


def hold_verdict(robot: dict, pose: dict, payload_g: float) -> dict:
    """Static gravity load per joint. An upper bound, and it says so (ADR-0004)."""
    volts = supply_volts(robot.get("robot_id"))
    base = {
        "robot_id": robot.get("robot_id"),
        "relative_to": robot["base_link"],
        "pose": {k: round(v, 6) for k, v in sorted(pose.items())},
        "payload_g": payload_g,
        "supply_volts": volts,
    }

    if any(j.get("type") in UNDETERMINED for j in robot.get("joints", [])):
        return dict(base, verdict="incomplete", missing="base orientation",
                    detail=("this robot has a floating or planar joint, so gravity "
                            "direction is a function of a base pose with no source "
                            "here. A z-up assumption would be a flat-ground figure "
                            "presented as a general one (ADR-0009)."))

    gravity = (0.0, 0.0, -1.0)                # base frame, z up per REP-103
    try:
        frames = forward_kinematics(robot, pose)
    except Incomplete as exc:
        return dict(base, verdict="incomplete", missing=exc.missing, detail=exc.detail)

    links = {l["link_id"]: l for l in robot.get("links", [])}
    tool = robot.get("tool") or {}
    tool_mat, _ = tool_matrix(robot, frames)

    # (link_id the mass rides on, position_mm, mass_g). The link matters: a mass
    # only loads the joints BELOW which it hangs.
    masses = []
    missing_mass = []
    for lid, link in links.items():
        if lid == robot["base_link"] or lid not in frames:
            continue
        if link.get("mass_g") is None:
            missing_mass.append(lid)
        else:
            masses.append((lid, position(frames[lid]), link["mass_g"]))

    tool_link = tool.get("attached_to") or next(
        (lid for lid in frames if lid not in
         {j["parent"] for j in robot.get("joints", [])}), robot["base_link"])
    if tool.get("mass_g"):
        masses.append((tool_link, position(tool_mat), tool["mass_g"]))
    if payload_g:
        masses.append((tool_link, position(tool_mat), payload_g))

    if missing_mass:
        return dict(
            base, verdict="incomplete", missing="link mass",
            detail=(f"link(s) {', '.join(sorted(missing_mass))} have no mass_g and it "
                    f"is not obtainable from a part_id or provenance record without "
                    f"resolving them, which this repo does not do (ADR-0006). "
                    f"Absent means the derivation reports incomplete, never zero."))

    results, binding = [], None
    for joint in robot.get("joints", []):
        if joint.get("type") not in ("revolute", "continuous"):
            continue
        jid = joint["joint_id"]
        try:
            capacity = joint_capacity_nm(joint, volts)
        except Incomplete as exc:
            return dict(base, verdict="incomplete", missing=exc.missing, detail=exc.detail)

        child_frame = frames[joint["child"]]
        pivot = position(child_frame)
        below = descendants(robot, joint["child"]) | {joint["child"]}

        # The joint axis is declared in the CHILD frame; rotate it into the base
        # frame, where gravity is expressed.
        local = joint.get("axis") or {}
        axis_base = tuple(
            sum(child_frame[i][k] * (local.get("xyz"[k], 0.0)) for k in range(3))
            for i in range(3))
        norm = math.sqrt(sum(c * c for c in axis_base)) or 1.0
        axis_base = tuple(c / norm for c in axis_base)

        # Torque about the joint axis is n . (r x F). Anything NOT below this joint
        # is carried by the structure above it and does not load it.
        load_nm = 0.0
        for lid, point, mass_g in masses:
            if lid not in below:
                continue
            r = tuple((point[i] - pivot[i]) / MM_PER_M for i in range(3))   # metres
            force = tuple(c * (mass_g / 1000.0) * G for c in gravity)       # newtons
            cross = (r[1] * force[2] - r[2] * force[1],
                     r[2] * force[0] - r[0] * force[2],
                     r[0] * force[1] - r[1] * force[0])
            load_nm += abs(sum(axis_base[i] * cross[i] for i in range(3)))
        margin = capacity - load_nm
        row = {"joint_id": jid, "capacity_nm": round(capacity, 4),
               "static_load_nm": round(load_nm, 4), "margin_nm": round(margin, 4),
               "holds": margin >= 0}
        results.append(row)
        if binding is None or margin < binding["margin_nm"]:
            binding = row

    if not results:
        return dict(base, verdict="incomplete", missing="revolute joints",
                    detail="no revolute joint carries a gravity load here")

    return dict(
        base,
        verdict="holds" if all(r["holds"] for r in results) else "exceeds-capacity",
        bound="STATIC UPPER BOUND",
        bound_note=("gravity load at a held pose. Acceleration, dynamic loading, "
                    "gearbox efficiency, friction and backlash are NOT modelled, so "
                    "the real capacity is LOWER than this (ADR-0004). This figure may "
                    "never be printed without the word that makes it a bound."),
        gravity_in_base=list(gravity),
        binding_joint=binding["joint_id"],
        joints=results,
    )


# ----------------------------------------------------------------------------- cli

def parse_pose(text: str | None) -> dict:
    if not text:
        return {}
    out = {}
    for pair in text.split(","):
        key, _, value = pair.partition("=")
        out[key.strip()] = float(value)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_fk = sub.add_parser("fk")
    p_fk.add_argument("robot_id")
    p_fk.add_argument("--pose", default="")

    p_reach = sub.add_parser("reach")
    p_reach.add_argument("robot_id")
    p_reach.add_argument("--target", help="X,Y,Z in mm, relative to base_link")
    p_reach.add_argument("--tolerance", type=float, default=5.0)
    p_reach.add_argument("--samples", type=int, default=20000)
    p_reach.add_argument("--seed", type=int, default=0)

    p_hold = sub.add_parser("hold")
    p_hold.add_argument("robot_id")
    p_hold.add_argument("--pose", default="")
    p_hold.add_argument("--payload-g", type=float, default=0.0)

    args = parser.parse_args()
    robot = load_robot(args.robot_id)

    if args.command == "fk":
        try:
            frames = forward_kinematics(robot, parse_pose(args.pose))
        except Incomplete as exc:
            print(json.dumps({"verdict": "incomplete", "missing": exc.missing,
                              "detail": exc.detail}, indent=2))
            return 1
        tool_mat, _ = tool_matrix(robot, frames)
        print(json.dumps({
            "relative_to": robot["base_link"],
            "tool_offset": tool_offset_description(robot),
            "links_mm": {lid: [round(c, 4) for c in position(m)]
                         for lid, m in sorted(frames.items())},
            "tool_mm": [round(c, 4) for c in position(tool_mat)],
        }, indent=2))
        return 0

    if args.command == "reach":
        target = tuple(float(c) for c in args.target.split(",")) if args.target else None
        verdict = reach_verdict(robot, target, args.tolerance, args.samples, args.seed)
        print(json.dumps(verdict, indent=2))
        return 0 if verdict["verdict"] in ("reachable", "sampled") else 1

    verdict = hold_verdict(robot, parse_pose(args.pose), args.payload_g)
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["verdict"] == "holds" else 1


if __name__ == "__main__":
    sys.exit(main())
