#!/usr/bin/env python3
"""Emit a robot's bill of parts in OpenBuildCore's vocabulary.

    python scripts/manifest.py <robot_id> [--assembly <id>] [--harness <id>]
                               [--as-project] [--json]

ClawBot knows what a robot is made of. OpenBuildCore knows what is in the drawer.
Neither imports the other (ADR-0006), so the seam is a document: this script emits
requirements in OBC's *exact* three-kind vocabulary — `part_id`, `capability`,
`make` with `size_mm` and `material` — so the output drops into `data/projects/`
and `advisor.py what-can-i-build` answers about a robot without translating
anything.

**Three link kinds do not map onto three requirement kinds.** Two of them do:

    ClawBot link      OpenBuildCore requirement
    ---------------   -------------------------------------
    part_id           {part_id, qty}          — buy it
    make              {make, size_mm, material, qty}  — fabricate it
    provenance_ref    (nothing)               — see below

A `provenance_ref` is an OpenDesignCore artifact hash and *nothing else*. ClawBot
stores the hash; it does not resolve it, so it does not know the part's bounding
box or volume and cannot honestly emit a `make` requirement for it. Inventing a
`size_mm` here would be exactly the fabrication this platform refuses, and it
would be invisible — a plausible box in a valid document.

So those links are reported separately, with the hash, and the answer is: run
OBC's `can-print --from-sidecar` against that artifact's provenance record. That
is the stronger check anyway, because it judges the geometry rather than the
intent (OBC ADR-0006, ODC ADR-0010).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import validate   # the citation gate lives there; ADR-0028 reuses it

ROOT = Path(__file__).resolve().parent.parent


def load(directory: str, entry_id: str, key: str) -> dict | None:
    for path in sorted((ROOT / "data" / directory).glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get(key) == entry_id:
            return doc
    return None


def placeholder_refusals(robot: dict) -> list[str]:
    """ADR-0028: a manifest lists parts to fabricate, so a placeholder size is a
    thing somebody would print. Reported rather than raised, because this module
    already collects its problems into the document it returns."""
    found = validate.consumed_placeholders(robot, ("links", "joints"))
    return [validate.placeholder_detail(found)] if found else []


def build_manifest(robot: dict, assembly: dict | None, harness: dict | None) -> dict:
    parts: dict[str, int] = defaultdict(int)
    makes: dict[tuple, dict] = {}
    provenance: list[dict] = []
    uncatalogued: dict[str, int] = defaultdict(int)

    def add_make(name: str, spec: dict) -> None:
        size = spec["size_mm"]
        key = (name, size["x"], size["y"], size["z"], spec["material"],
               spec.get("min_feature_mm"))
        if key in makes:
            makes[key]["qty"] += 1
            return
        entry = {"make": name, "size_mm": dict(size),
                 "material": spec["material"], "qty": 1}
        if spec.get("min_feature_mm") is not None:
            entry["min_feature_mm"] = spec["min_feature_mm"]
        makes[key] = entry

    for link in robot.get("links", []):
        lid = link.get("link_id", "unnamed")
        if link.get("part_id"):
            parts[link["part_id"]] += 1
        elif link.get("make"):
            add_make(lid, link["make"])
        elif link.get("provenance_ref"):
            provenance.append({
                "link_id": lid,
                "artifact_sha256": link["provenance_ref"]["artifact_sha256"],
                "schema": link["provenance_ref"].get("schema"),
            })

    # Actuators are parts too — a joint names one, and the actuator record may
    # carry the part_id that OpenPartsCore catalogues it under.
    for joint in robot.get("joints", []):
        aid = joint.get("actuator_id")
        if not aid:
            continue
        actuator = load("actuators", aid, "actuator_id")
        if actuator and actuator.get("part_id"):
            parts[actuator["part_id"]] += 1
        else:
            uncatalogued[aid] += 1

    if robot.get("tool") and robot["tool"].get("tool_id"):
        pass  # a tool's own parts are its own record's business, not this one's

    # Fasteners come from the assembly, and are usually where the count lives.
    if assembly:
        for step in assembly.get("steps", []):
            for f in step.get("fasteners", []):
                if f.get("part_id"):
                    parts[f["part_id"]] += f.get("qty", 1)
                elif f.get("spec"):
                    uncatalogued[f["spec"]] += f.get("qty", 1)

    if harness and (harness.get("controller") or {}).get("part_id"):
        parts[harness["controller"]["part_id"]] += 1

    return {
        "robot_id": robot.get("robot_id"),
        "buy": [{"part_id": pid, "qty": q} for pid, q in sorted(parts.items())],
        "make": sorted(makes.values(), key=lambda m: m["make"]),
        "designed": provenance,
        "uncatalogued": [{"what": k, "qty": q} for k, q in sorted(uncatalogued.items())],
    }


# A DATED COPY of Project BINGO's default stances, taken from
# ProjectBINGO/v3/specs/REFUSAL-CATEGORIES.md v0.1 on 2026-08-22. This is a cache
# with provenance, not a fork: it never overrides BINGO, it always names its
# upstream, and it decides one thing only — whether ClawBot emits a document.
# BINGO re-checks at matching time against the version frozen into the job.
# It WILL go stale. That is bounded: a stale copy makes this repo slightly over-
# or under-cautious about emitting, and never makes a routing decision (ADR-0019).
BINGO_TAXONOMY_VERSION_SEEN = "REFUSAL-CATEGORIES v0.1 (draft), read 2026-08-22"
REFUSED_NETWORK_WIDE = {
    "weapons.firearms",
    "weapons.other",
    "covert.surveillance",
    "ip.counterfeit",
}


class PolicyRefusal(Exception):
    """Raised at the output boundary, never during a derivation."""


def check_policy(robot: dict) -> list[str]:
    """Gate on the fabrication-bound path only. Returns advisory notes, or raises.

    ADR-0019: ClawBot will not make a declaration on the author's behalf, and will
    not emit a document that has no valid destination.
    """
    policy = robot.get("policy")
    if not policy:
        raise PolicyRefusal(
            "this record carries no `policy` declaration, and an OpenBuildCore project "
            "is bound for a network that requires one. Project BINGO reads an absent "
            "declaration AS a 'none' declaration, carrying the same fraud consequences "
            "as misdeclaring a licence — so emitting this would make that declaration "
            "on your behalf, invisibly, at the far end (ADR-0019).\n\n"
            "  Declare it: policy.categories (e.g. [\"none\"]) and "
            "policy.taxonomy_version.\n"
            "  The plain bill of parts is ungated and needs no declaration; it is a "
            "shopping list for a person, not a document bound for a network."
        )

    declared = [c for c in policy.get("categories", [])]
    refused = sorted(set(declared) & REFUSED_NETWORK_WIDE)
    if refused:
        raise PolicyRefusal(
            f"this record declares {', '.join(refused)}, which Project BINGO's taxonomy "
            f"marks refuse-network-wide.\n\n"
            f"  ClawBot is not adjudicating that. It is declining to emit a "
            f"fabrication-bound document with no valid destination: no node can accept "
            f"such a job under any configuration.\n"
            f"  Judged against a dated copy of {BINGO_TAXONOMY_VERSION_SEEN}. "
            f"BINGO is authoritative and re-checks at matching time.\n"
            f"  Every derivation still runs — fk, reach, hold and can_it do not consult "
            f"this field (ADR-0019)."
        )

    notes = []
    opt_in = sorted(set(declared) - {"none"})
    if opt_in:
        notes.append(
            f"declares {', '.join(opt_in)} against {policy['taxonomy_version']}. Not "
            f"refused: these route only to nodes that have opted in, with whatever "
            f"context the category requires. The declaration travels with the manifest.")
    if policy.get("taxonomy_version") != BINGO_TAXONOMY_VERSION_SEEN and declared != ["none"]:
        notes.append(
            f"declared against '{policy['taxonomy_version']}'; the stance copy used here "
            f"is {BINGO_TAXONOMY_VERSION_SEEN}. If those differ, BINGO's list at order "
            f"time is what counts.")
    return notes


def as_project(robot: dict, manifest: dict) -> dict:
    """An OpenBuildCore project document. Its own validator is the judge."""
    requires = [dict(r) for r in manifest["buy"]]
    for m in manifest["make"]:
        requires.append(dict(m))
    name = " ".join(filter(None, [robot.get("make"), robot.get("model")])) \
        or robot.get("robot_id", "robot")

    # The declaration travels as DATA as of 2026-08-23. It used to go as prose in
    # `description`, because OpenBuildCore's project schema was
    # additionalProperties:false with no slot for it — reported as OpenBuildCore#9,
    # fixed by its ADR-0007, and the field is now `policy_categories` with BINGO's
    # own name and shape (ClawBot ADR-0022).
    policy = robot.get("policy") or {}
    project = {
        "schema_version": 0,
        "id": robot["robot_id"],
        "name": f"Build {name}",
        "description": (
            f"A {robot.get('kind', 'mechanism')} with "
            f"{len(robot.get('links', []))} link(s) and "
            f"{len(robot.get('joints', []))} joint(s). "
            f"Emitted from a ClawBot robot record by scripts/manifest.py; the "
            f"mechanism's own definition stays in ClawBot."
        ),
        "requires": requires,
    }
    if policy.get("categories"):
        project["policy_categories"] = list(policy["categories"])
    # The taxonomy_version deliberately does NOT travel. BINGO does not version at
    # the asset — it freezes the category list's hash into the job at order time —
    # so OpenBuildCore has no field for it and inventing one would fork a
    # mechanism that is already solved elsewhere. It stays in the ClawBot record,
    # where a reader can see what the author declared against.
    return project


def render(manifest: dict, robot: dict) -> str:
    out = [f"Bill of parts for {manifest['robot_id']}", ""]

    if manifest["buy"]:
        out.append("  BUY  (OpenBuildCore resolves these against your inventory)")
        for r in manifest["buy"]:
            out.append(f"    {r['qty']}x  {r['part_id']}")
        out.append("")

    if manifest["make"]:
        out.append("  MAKE  (checked against machines you own, never shopped for)")
        for r in manifest["make"]:
            s = r["size_mm"]
            out.append(f"    {r['qty']}x  {r['make']:<20} "
                       f"{s['x']} x {s['y']} x {s['z']} mm, {r['material']}")
        out.append("")

    if manifest["designed"]:
        out.append("  DESIGNED  (geometry exists; its bounding box is a fact, not a "
                   "declared intent)")
        for r in manifest["designed"]:
            out.append(f"    {r['link_id']:<20} sha256:{r['artifact_sha256'][:12]}")
        out.append("      Not emitted as a make requirement: ClawBot stores the hash and "
                   "does not")
        out.append("      resolve it, so it has no size to declare. Judge these with")
        out.append("      OpenBuildCore's `machines.py can-print --from-sidecar` against "
                   "the")
        out.append("      artifact's provenance record — which checks the real geometry.")
        out.append("")

    if manifest["uncatalogued"]:
        out.append("  UNCATALOGUED  (no OpenPartsCore id — cannot be matched or shopped)")
        for r in manifest["uncatalogued"]:
            out.append(f"    {r['qty']}x  {r['what']}")
        out.append("      These are real parts with no home in the registry. Until one "
                   "exists,")
        out.append("      OpenBuildCore cannot tell you whether you have them.")
        out.append("")

    unlimited = [j["joint_id"] for j in robot.get("joints", [])
                 if j.get("type") in ("revolute", "prismatic") and not j.get("limits")]
    placeheld = placeholder_refusals(robot)
    if placeheld:
        out.append("")
        out.append("  PLACEHOLDER SIZES — this bill of parts is not printable.")
        out.append(f"  {placeheld[0]}")
        out.append("  `--as-project` refuses outright, because that document routes to "
                   "a machine.")

    if unlimited:
        out.append(f"  Note: {len(unlimited)} joint(s) have no limits "
                   f"({', '.join(unlimited)}).")
        out.append("  The bill of parts is unaffected — but reachability over this robot "
                   "answers")
        out.append("  'incomplete', and URDF export refuses (ADR-0003, ADR-0007).")

    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("robot_id")
    parser.add_argument("--assembly", help="assembly_id whose fasteners to include")
    parser.add_argument("--harness", help="harness_id whose controller to include")
    parser.add_argument("--as-project", action="store_true",
                        help="emit an OpenBuildCore project document")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    robot = load("robots", args.robot_id, "robot_id")
    if robot is None:
        print(f"no robot '{args.robot_id}' in data/robots/", file=sys.stderr)
        return 1

    assembly = load("assemblies", args.assembly, "assembly_id") if args.assembly else None
    if args.assembly and assembly is None:
        print(f"no assembly '{args.assembly}' in data/assemblies/", file=sys.stderr)
        return 1
    harness = load("harnesses", args.harness, "harness_id") if args.harness else None
    if args.harness and harness is None:
        print(f"no harness '{args.harness}' in data/harnesses/", file=sys.stderr)
        return 1

    manifest = build_manifest(robot, assembly, harness)

    if args.as_project:
        # ADR-0028. This document routes to a machine. A `make` requirement whose
        # size_mm is a placeholder is a part somebody prints, so this path refuses
        # where `render` only warns - the same distinction ADR-0019 draws about
        # emitting a fabrication-bound document the record does not support.
        placeheld = placeholder_refusals(robot)
        if placeheld:
            print(f"REFUSED: cannot emit an OpenBuildCore project for "
                  f"'{args.robot_id}'.\n\n  {placeheld[0]}", file=sys.stderr)
            return 1
        try:
            notes = check_policy(robot)
        except PolicyRefusal as exc:
            print(f"REFUSED: cannot emit an OpenBuildCore project for "
                  f"'{args.robot_id}'.\n\n  {exc}", file=sys.stderr)
            return 1
        for note in notes:
            print(f"note: {note}", file=sys.stderr)
        print("note: the declaration travels as `policy_categories`, machine-readable. "
              "Its taxonomy_version does not — BINGO pins an id's meaning by freezing "
              "the list hash into the job at order time, so there is no asset-level "
              "field for it and inventing one would fork a solved mechanism (ADR-0022).",
              file=sys.stderr)
        print(json.dumps(as_project(robot, manifest), indent=2))
    elif args.json:
        print(json.dumps(manifest, indent=2))
    else:
        print(render(manifest, robot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
