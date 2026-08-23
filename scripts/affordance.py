#!/usr/bin/env python3
"""Can this body do this thing? Four answers, and none of them is an unqualified yes.

    python scripts/affordance.py <robot_id> --target X,Y,Z [--payload-g N]
                                 [--tolerance MM] [--samples N] [--seed S]

The affordance verdict ADR-0010 promised — the *can-it-actually-happen* half of
the SayCan pattern, where a language model's "does this skill serve the
instruction" is multiplied by an affordance model's "can this robot do it now".

**There is no score.** The literature's affordance is a float in [0,1], and that
float is a frequency estimate: it comes from trials. ClawBot has run no trials.
A float emitted here would have the shape of a probability with nothing behind
it, and SayCan-style consumers *multiply* affordances — so a fabricated number
would not sit in a report where somebody might question it, it would propagate
into a product and vanish. Rank on the **margin** instead: real headroom, in the
units of whatever is binding (ADR-0015).

**And a yes is not available**, because the two derivations underneath are
unsound in opposite directions:

* sampled reach is sound *positive*, unsound negative (ADR-0013) — a point is
  only reachable once FK put the tool there;
* static capacity is sound *negative*, unsound positive (ADR-0004) — it is an
  upper bound, so exceeding it settles the matter, and coming in under it
  proves nothing.

So `cannot` is a real claim and `can` is not one this repo can make. The closest
it gets is `within-static-bound`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kinematics as kin  # noqa: E402

# How many reaching poses to evaluate capacity at when looking for the best
# margin. Capped because each one is a full FK pass; the cap is reported in the
# verdict rather than applied silently.
BEST_POSE_CAP = 25


def affordance(robot: dict, target, payload_g: float, tolerance_mm: float,
               samples: int, seed: int) -> dict:
    request = {
        "target_mm": list(target),
        "payload_g": payload_g,
        "tolerance_mm": tolerance_mm,
        "relative_to": robot["base_link"],
    }
    base = {"robot_id": robot.get("robot_id"), "request": request,
            "no_score": ("deliberately absent. An affordance float is a frequency "
                         "estimate and no trials were run; rank on margin_nm, which "
                         "is a derived quantity with units (ADR-0015).")}

    # --- reach half -------------------------------------------------------
    reach = kin.reach_verdict(robot, tuple(target), tolerance_mm, samples, seed)
    base["reach"] = reach

    if reach["verdict"] == "incomplete":
        return dict(base, verdict="incomplete", binding="reach",
                    missing=reach["missing"], detail=reach["detail"])

    if reach["verdict"] != "reachable":
        return dict(
            base, verdict="unproven", binding="reach",
            detail=(f"no sample placed the tool within {tolerance_mm} mm of the target "
                    f"in {reach['samples']} samples (nearest "
                    f"{reach['nearest_sample_mm']} mm). This is NOT a claim that the "
                    f"body cannot do it — a sampled workspace only ever proves the "
                    f"positive (ADR-0013). Raise --samples or --tolerance."))

    pose = reach["pose"]

    # --- capacity half ----------------------------------------------------
    hold = kin.hold_verdict(robot, pose, payload_g)
    base["hold"] = hold

    if hold["verdict"] == "incomplete":
        return dict(base, verdict="incomplete", binding="capacity",
                    missing=hold["missing"], detail=hold["detail"],
                    note=("the target IS reachable — the pose is in reach.pose. What "
                          "is missing is the input that would let capacity be judged "
                          "there."))

    binding = min(hold["joints"], key=lambda j: j["margin_nm"])

    if hold["verdict"] == "exceeds-capacity":
        return dict(
            base, verdict="cannot", binding=f"joint '{binding['joint_id']}'",
            margin_nm=binding["margin_nm"],
            detail=(f"at the pose that reached the target, joint "
                    f"'{binding['joint_id']}' sees {binding['static_load_nm']} N.m "
                    f"against a capacity of {binding['capacity_nm']} N.m — over by "
                    f"{abs(binding['margin_nm'])} N.m. This IS a claim: the figure it "
                    f"exceeds is a STATIC UPPER BOUND, and real capacity is lower, so "
                    f"exceeding it settles the matter (ADR-0004, ADR-0015)."),
            caveat=("this is about the pose that was found, not about every pose that "
                    "reaches this point. See best_margin_pose for whether another one "
                    "does better."),
            **best_margin(robot, target, payload_g, tolerance_mm, samples, seed))

    return dict(
        base, verdict="within-static-bound", binding=f"joint '{binding['joint_id']}'",
        margin_nm=binding["margin_nm"],
        detail=(f"the target is reachable, and at the pose that reached it the "
                f"tightest joint '{binding['joint_id']}' has {binding['margin_nm']} "
                f"N.m of headroom against a static upper bound. **This is not a yes.** "
                f"The bound ignores gearbox efficiency, friction, backlash and "
                f"acceleration, so real capacity is lower by an unmodelled amount "
                f"(ADR-0004). Self-collision is not modelled either, so the reach half "
                f"over-claims (ADR-0003)."),
        **best_margin(robot, target, payload_g, tolerance_mm, samples, seed))


def best_margin(robot: dict, target, payload_g: float, tolerance_mm: float,
                samples: int, seed: int) -> dict:
    """The most comfortable pose that still reaches the target.

    Reported ALONGSIDE the verdict's own pose, never instead of it: the best-margin
    pose is the one holding the load closest to the joint axes, which is frequently
    useless for the actual task (ADR-0015)."""
    try:
        points = kin.sample_workspace(robot, samples, seed)
    except kin.Incomplete:
        return {}

    reaching = [pose for point, pose in points
                if kin.distance(point, tuple(target)) <= tolerance_mm]
    if not reaching:
        return {}

    considered, best = reaching[:BEST_POSE_CAP], None
    for pose in considered:
        verdict = kin.hold_verdict(robot, pose, payload_g)
        if verdict["verdict"] not in ("holds", "exceeds-capacity"):
            continue
        joint = min(verdict["joints"], key=lambda j: j["margin_nm"])
        if best is None or joint["margin_nm"] > best["margin_nm"]:
            best = {"margin_nm": joint["margin_nm"], "joint_id": joint["joint_id"],
                    "pose": {k: round(v, 6) for k, v in sorted(pose.items())}}
    if best is None:
        return {}

    out = {"best_margin_pose": best,
           "best_margin_note": (f"the most comfortable of {len(considered)} reaching "
                                f"pose(s) evaluated. Offered beside the verdict's pose, "
                                f"not instead of it — the easiest pose is often the "
                                f"wrong one for the task.")}
    if len(reaching) > BEST_POSE_CAP:
        out["best_margin_truncated"] = (
            f"{len(reaching)} poses reached the target; only the first "
            f"{BEST_POSE_CAP} were evaluated for capacity. A better margin may exist "
            f"among the {len(reaching) - BEST_POSE_CAP} not checked.")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("robot_id")
    parser.add_argument("--target", required=True, help="X,Y,Z in mm, from base_link")
    parser.add_argument("--payload-g", type=float, default=0.0)
    parser.add_argument("--tolerance", type=float, default=5.0)
    parser.add_argument("--samples", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    robot = kin.load_robot(args.robot_id)
    target = tuple(float(c) for c in args.target.split(","))
    verdict = affordance(robot, target, args.payload_g, args.tolerance,
                         args.samples, args.seed)
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["verdict"] == "within-static-bound" else 1


if __name__ == "__main__":
    sys.exit(main())
