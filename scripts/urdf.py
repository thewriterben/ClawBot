#!/usr/bin/env python3
"""The URDF boundary: import that does not believe defaults, export that refuses.

    python scripts/urdf.py import <file.urdf> [--robot-id ID]
    python scripts/urdf.py export <robot_id>

ADR-0007 decided this is a **boundary with an explicit absence rule in each
direction**, not a mapping. The reason is in
`Knowledge/concepts/urdf-round-trip.md`: structure survives the round trip and
absence does not.

**Import reads the XML, never the parsed tree.** `urdfdom` fills in a missing
`lower`/`upper` with `0` and a missing `axis` with `(1, 0, 0)`, both with only a
debug log. An importer built on that parser cannot be correct however carefully it
is written, because the parse is where absence is destroyed. So this walks the
document with `xml.etree` and an attribute that is not present imports as absent.
Where the format would have supplied a value, the citation says so.

**Export refuses rather than defaults.** `urdfdom` will not parse a revolute or
prismatic joint with no `limit`, and inside one, a missing `effort` or `velocity`
is fatal. A ClawBot record in exactly the state ADR-0003 exists to handle —
travel nobody has sourced — therefore has no valid URDF at all. Emitting a zero
would manufacture a physical claim. So export is **partial by construction**: a
fully-sourced robot exports, an honest incomplete one does not, and the failure
names every joint responsible rather than the first.

Lengths convert at exactly one place: URDF is metres (REP-103), this repo is
millimetres (ADR-0005). Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

ROOT = Path(__file__).resolve().parent.parent
MM_PER_M = 1000.0
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
NEEDS_LIMIT = {"revolute", "prismatic"}
ANGULAR = {"revolute", "continuous"}


def slugify(name: str) -> str:
    """URDF names routinely contain underscores; ClawBot ids may not. Renaming is a
    transformation, so every rename is reported rather than done quietly."""
    slug = re.sub(r"[^a-z0-9-]+", "-", name.strip().lower()).strip("-")
    return slug or "unnamed"


def floats(text: str | None, count: int = 3) -> list | None:
    if text is None:
        return None
    parts = [float(p) for p in text.replace(",", " ").split()]
    return parts if len(parts) == count else None


# ------------------------------------------------------------------------ import

def import_urdf(path: Path, robot_id: str | None) -> tuple[dict, list]:
    tree = ET.parse(path)
    root = tree.getroot()
    notes: list[str] = []
    renames: dict[str, str] = {}

    def link_id(name: str) -> str:
        slug = slugify(name)
        if slug != name:
            renames[name] = slug
        return slug

    links = []
    for element in root.findall("link"):
        name = element.get("name", "")
        link = {"link_id": link_id(name),
                "source": {"citation": f"URDF import from {path.name}"}}

        inertial = element.find("inertial")
        mass = inertial.find("mass") if inertial is not None else None
        if mass is not None and mass.get("value") is not None:
            # URDF mass is kilograms (REP-103); this repo is grams.
            link["mass_g"] = float(mass.get("value")) * 1000.0
        # No part_id, make or provenance_ref: URDF does not carry one, and
        # inventing a `make` box from a <visual> mesh would be a fabricated size.
        note = []
        if len(element.findall("visual")) + len(element.findall("collision")):
            note.append("URDF carried visual/collision geometry, which is not "
                        "imported: geometry is OpenDesignCore's (ADR-0006)")
        if inertial is not None and inertial.find("inertia") is not None:
            note.append("URDF carried a full inertia tensor; only mass is modelled "
                        "here, because ADR-0004 stops at static gravity load")
        if note:
            link["note"] = ". ".join(note)
        links.append(link)

    joints = []
    for element in root.findall("joint"):
        name = element.get("name", "")
        jtype = element.get("type", "")
        jid = slugify(name)
        if jid != name:
            renames[name] = jid
        # `or` is wrong on an Element: one with no children is falsy, so a present
        # <parent> would fall through to the fallback every time.
        parent_el, child_el = element.find("parent"), element.find("child")
        joint = {
            "joint_id": jid,
            "type": jtype,
            "parent": link_id(parent_el.get("link", "") if parent_el is not None else ""),
            "child": link_id(child_el.get("link", "") if child_el is not None else ""),
            "origin": {},
            "source": {"citation": f"URDF import from {path.name}"},
        }

        origin = element.find("origin")
        if origin is not None:
            xyz = floats(origin.get("xyz"))
            rpy = floats(origin.get("rpy"))
            if xyz:
                joint["origin"]["xyz_mm"] = {k: v * MM_PER_M for k, v in zip("xyz", xyz)}
            if rpy:
                joint["origin"]["rpy_rad"] = dict(zip("rpy", rpy))

        # THE AXIS RULE. urdfdom defaults a missing axis to (1,0,0) with a debug
        # log. Absent here means absent; if it was absent and the type needs one,
        # the fact that the FORMAT would have supplied it is recorded as the source.
        axis = element.find("axis")
        if axis is not None and (vec := floats(axis.get("xyz"))):
            joint["axis"] = dict(zip("xyz", vec))
        elif jtype in ("revolute", "continuous", "prismatic"):
            joint["axis"] = {"x": 1.0, "y": 0.0, "z": 0.0}
            joint["source"] = {"citation": f"URDF import from {path.name}; axis "
                                           f"DEFAULTED by the format, not stated by "
                                           f"the author"}
            notes.append(f"joint '{jid}': no <axis> element. urdfdom would silently "
                         f"use (1,0,0); recorded as a format default, not a claim")

        # THE LIMIT RULE. A missing lower/upper is 0 to urdfdom. Here it is absent.
        limit = element.find("limit")
        if limit is not None:
            bounds = {}
            lower, upper = limit.get("lower"), limit.get("upper")
            if lower is not None and upper is not None:
                if jtype in ANGULAR:
                    bounds["lower_rad"], bounds["upper_rad"] = float(lower), float(upper)
                else:
                    bounds["lower_mm"] = float(lower) * MM_PER_M
                    bounds["upper_mm"] = float(upper) * MM_PER_M
            elif jtype in NEEDS_LIMIT:
                notes.append(
                    f"joint '{jid}': <limit> present with no lower/upper. urdfdom "
                    f"reads this as a joint LOCKED AT ZERO; imported as UNKNOWN, "
                    f"because the document does not distinguish them (ADR-0007)")
            if limit.get("effort") is not None:
                bounds["effort_nm"] = float(limit.get("effort"))
            if limit.get("velocity") is not None:
                bounds["velocity_rad_s"] = float(limit.get("velocity"))
            joint["limits"] = dict(
                bounds, source={"citation": f"URDF import from {path.name}"}
            ) if bounds else None
        else:
            joint["limits"] = None
            if jtype in NEEDS_LIMIT:
                notes.append(f"joint '{jid}': type '{jtype}' with no <limit>. "
                             f"urdfdom refuses to parse this document")

        mimic = element.find("mimic")
        if mimic is not None:
            joint["mimic"] = {"joint": slugify(mimic.get("joint", ""))}
            if mimic.get("multiplier") is not None:
                joint["mimic"]["multiplier"] = float(mimic.get("multiplier"))
            if mimic.get("offset") is not None:
                joint["mimic"]["offset"] = float(mimic.get("offset"))

        if element.find("safety_controller") is not None:
            notes.append(f"joint '{jid}': <safety_controller> soft limits present and "
                         f"not imported — a second limit set, and which one binds a "
                         f"derivation is undecided (urdf-round-trip.md)")
        joints.append(joint)

    parented = {j["child"] for j in joints}
    roots = [l["link_id"] for l in links if l["link_id"] not in parented]

    robot = {
        "schema_version": 0,
        "robot_id": robot_id or slugify(root.get("name", "imported")),
        "kind": "arm",
        "base_link": roots[0] if roots else (links[0]["link_id"] if links else ""),
        "links": links,
        "joints": joints,
        "tool": None,
        "measured_payload": None,
        "source": {"citation": f"URDF import from {path.name}"},
        "note": ("Imported from URDF. `kind` is a label and defaults to 'arm' — the "
                 "format does not carry one. `tool` is null, which is a DECLARATION "
                 "of no tool; if this mechanism has one, its offset must be stated, "
                 "because a reach answer without it is meaningless (ADR-0003)."),
    }
    if len(roots) > 1:
        notes.append(f"{len(roots)} unparented links ({', '.join(roots)}); "
                     f"'{robot['base_link']}' chosen as base_link. A URDF with "
                     f"several roots is not one tree")
    for original, slug in sorted(renames.items()):
        notes.append(f"renamed '{original}' -> '{slug}': ClawBot ids are lowercase "
                     f"slugs and may not contain underscores")
    return robot, notes


# ------------------------------------------------------------------------ export

def export_urdf(robot: dict) -> tuple[str | None, list]:
    """Returns (xml, refusals). A non-empty refusal list means no document."""
    refusals = []
    for joint in robot.get("joints", []):
        jid, jtype = joint["joint_id"], joint.get("type")
        if jtype not in NEEDS_LIMIT:
            continue
        limits = joint.get("limits")
        if not limits:
            refusals.append(
                f"joint '{jid}': type '{jtype}' has no limits. URDF cannot say "
                f"'unknown' — urdfdom refuses to parse a {jtype} joint without a "
                f"<limit>, and emitting lower=0 upper=0 would claim the joint is "
                f"locked at zero, which nobody established (ADR-0007)")
            continue
        has_bounds = ("lower_rad" in limits and "upper_rad" in limits) or \
                     ("lower_mm" in limits and "upper_mm" in limits)
        if not has_bounds:
            refusals.append(f"joint '{jid}': limits present but carry no travel bounds")
        if limits.get("effort_nm") is None:
            refusals.append(f"joint '{jid}': no limits.effort_nm. urdfdom treats a "
                            f"missing effort as fatal, and a default would be invented")
        if limits.get("velocity_rad_s") is None:
            refusals.append(f"joint '{jid}': no limits.velocity_rad_s. Same as effort — "
                            f"urdfdom treats a missing velocity as fatal")
    if refusals:
        return None, refusals

    root = ET.Element("robot", {"name": robot["robot_id"]})
    for link in robot.get("links", []):
        element = ET.SubElement(root, "link", {"name": link["link_id"]})
        if link.get("mass_g") is not None:
            inertial = ET.SubElement(element, "inertial")
            ET.SubElement(inertial, "mass",
                          {"value": f"{link['mass_g'] / 1000.0:.9g}"})
            # No <inertia>: this repo does not carry a tensor, and zeros would be
            # a claim about mass distribution nobody made.

    for joint in robot.get("joints", []):
        element = ET.SubElement(root, "joint", {"name": joint["joint_id"],
                                                "type": joint["type"]})
        ET.SubElement(element, "parent", {"link": joint["parent"]})
        ET.SubElement(element, "child", {"link": joint["child"]})

        origin = joint.get("origin") or {}
        xyz = origin.get("xyz_mm") or {}
        rpy = origin.get("rpy_rad") or {}
        if xyz or rpy:
            ET.SubElement(element, "origin", {
                "xyz": " ".join(f"{xyz.get(k, 0.0) / MM_PER_M:.9g}" for k in "xyz"),
                "rpy": " ".join(f"{rpy.get(k, 0.0):.9g}" for k in "rpy"),
            })
        if joint.get("axis"):
            ET.SubElement(element, "axis", {
                "xyz": " ".join(f"{joint['axis'].get(k, 0.0):.9g}" for k in "xyz")})

        limits = joint.get("limits")
        if limits and joint["type"] in NEEDS_LIMIT:
            if "lower_rad" in limits:
                lower, upper = limits["lower_rad"], limits["upper_rad"]
            else:
                lower = limits["lower_mm"] / MM_PER_M
                upper = limits["upper_mm"] / MM_PER_M
            ET.SubElement(element, "limit", {
                "lower": f"{lower:.9g}", "upper": f"{upper:.9g}",
                "effort": f"{limits['effort_nm']:.9g}",
                "velocity": f"{limits['velocity_rad_s']:.9g}"})

        if joint.get("mimic"):
            mimic = joint["mimic"]
            attrs = {"joint": mimic["joint"]}
            if mimic.get("multiplier") is not None:
                attrs["multiplier"] = f"{mimic['multiplier']:.9g}"
            if mimic.get("offset") is not None:
                attrs["offset"] = f"{mimic['offset']:.9g}"
            ET.SubElement(element, "mimic", attrs)

    xml = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    header = ("<!-- Exported by ClawBot. Lengths are metres (REP-103); the source\n"
              "     record is millimetres (ADR-0005). Provenance does not survive:\n"
              "     URDF has nowhere to record where a joint limit came from. -->\n")
    lines = xml.splitlines()
    return lines[0] + "\n" + header + "\n".join(lines[1:]) + "\n", []


# --------------------------------------------------------------------------- cli

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_in = sub.add_parser("import")
    p_in.add_argument("file", type=Path)
    p_in.add_argument("--robot-id")

    p_out = sub.add_parser("export")
    p_out.add_argument("robot_id")

    args = parser.parse_args()

    if args.command == "import":
        if not args.file.exists():
            print(f"no such file: {args.file}", file=sys.stderr)
            return 1
        robot, notes = import_urdf(args.file, args.robot_id)
        print(json.dumps(robot, indent=2))
        for note in notes:
            print(f"note: {note}", file=sys.stderr)
        if notes:
            print(f"\n{len(notes)} note(s) above. Each is a place the format and this "
                  f"repo disagree about what a missing value means.", file=sys.stderr)
        return 0

    for path in sorted((ROOT / "data" / "robots").glob("*.json")):
        robot = json.loads(path.read_text(encoding="utf-8"))
        if robot.get("robot_id") == args.robot_id:
            break
    else:
        print(f"no robot '{args.robot_id}' in data/robots/", file=sys.stderr)
        return 1

    xml, refusals = export_urdf(robot)
    if refusals:
        print(f"REFUSED: cannot export '{args.robot_id}' as URDF.\n", file=sys.stderr)
        for refusal in refusals:
            print(f"  {refusal}", file=sys.stderr)
        print(f"\nThis is ADR-0007 working, not a bug. URDF has no way to say "
              f"'unknown',\nso a record honest about what nobody sourced has no valid "
              f"representation\nin it. Fill in the sources, or keep the record and "
              f"lose the export.", file=sys.stderr)
        return 1
    print(xml)
    return 0


if __name__ == "__main__":
    sys.exit(main())
