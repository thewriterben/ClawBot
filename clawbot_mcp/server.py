"""ClawBot stdio MCP server.

Exposes the mechanism model to any MCP client, so an agent can ask what a robot
can reach and what it can hold there without shelling out to the CLI.

Every tool here **reads or derives**. ClawBot has no side effects at all — by
construction, not by accident: ADR-0010 put every actuating loop behind
Oh-Ben-Claw's Track 0, ADR-0006 keeps this repo from importing a peer, and
`data/` is edited by people. So OpenDesignCore ADR-0009's propose side comes out
**empty** here, and nothing can be added to it without first reversing an ADR
(ADR-0016).

**No tool takes a filesystem path.** `urdf.py import` reads a file you name, and
exposed over MCP that is an arbitrary file read wearing a domain-specific name.
It stays on the CLI, where the person running it chose the file.

**Every tool returns the whole verdict, caveats included.** A tool returning a
bare boolean would strip the assumptions ADR-0003, ADR-0004, ADR-0013 and
ADR-0015 each require to travel inside the value — and tool results get
summarised by a model before a human sees them, which is exactly where a
stripped caveat disappears.

The package is named `clawbot_mcp`, not `mcp`, because the latter shadows the SDK.

Run:
    python -m clawbot_mcp.server

Requires:  pip install -r clawbot_mcp/requirements.txt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import affordance as aff_lib  # noqa: E402
import kinematics as kin  # noqa: E402
import manifest as manifest_lib  # noqa: E402
import urdf as urdf_lib  # noqa: E402
import validate as validate_lib  # noqa: E402

try:
    from mcp.server import MCPServer
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing or too-old dependency. Run: pip install -r clawbot_mcp/requirements.txt"
    ) from exc

server = MCPServer("clawbot")

# A sampled reach with a large enough N is a denial of service against this
# process. Clamp, and REPORT the clamp — silently honouring it and silently
# refusing it are equally dishonest (ADR-0016).
MAX_SAMPLES = 200_000


def _clamp_samples(samples: int) -> tuple[int, str | None]:
    if samples <= MAX_SAMPLES:
        return samples, None
    return MAX_SAMPLES, (f"requested {samples} samples, clamped to {MAX_SAMPLES}. "
                         f"The verdict below was computed at the clamped count.")


def _read(directory: str) -> list:
    out = []
    for path in sorted((ROOT / "data" / directory).glob("*.json")):
        out.append(json.loads(path.read_text(encoding="utf-8")))
    return out


def _robot(robot_id: str) -> dict:
    for doc in _read("robots"):
        if doc.get("robot_id") == robot_id:
            return doc
    raise ValueError(f"no robot '{robot_id}' in data/robots/")


def _pose(pose_json: str) -> dict:
    return json.loads(pose_json) if pose_json else {}


@server.tool()
def list_robots() -> list:
    """Every robot record, summarised: id, kind, link and joint counts, and —
    importantly — which joints have no limits, because those make every
    derivation over this robot answer incomplete (ADR-0003)."""
    out = []
    for robot in _read("robots"):
        unlimited = [j["joint_id"] for j in robot.get("joints", [])
                     if j.get("type") in ("revolute", "prismatic") and not j.get("limits")]
        out.append({
            "robot_id": robot.get("robot_id"),
            "kind": robot.get("kind"),
            "make": robot.get("make"),
            "model": robot.get("model"),
            "base_link": robot.get("base_link"),
            "links": len(robot.get("links", [])),
            "joints": len(robot.get("joints", [])),
            "joints_without_limits": unlimited,
            "derivable": not unlimited,
        })
    return out


@server.tool()
def list_actuators() -> list:
    """Every actuator record. `capacity_derivable` is the field that matters:
    most datasheets publish stall torque and no continuous rating, and only the
    continuous figure may feed a capacity derivation (ADR-0004)."""
    out = []
    for act in _read("actuators"):
        cont = act.get("continuous_torque_nm") or []
        stall = act.get("stall_torque_nm") or []
        out.append({
            "actuator_id": act.get("actuator_id"),
            "make": act.get("make"),
            "model": act.get("model"),
            "type": act.get("type"),
            "stall_torque_volts": [r.get("at_volts") for r in stall],
            "continuous_torque_volts": [r.get("at_volts") for r in cont],
            "capacity_derivable": bool(cont),
            "note": act.get("note"),
        })
    return out


@server.tool()
def describe_robot(robot_id: str) -> dict:
    """The full robot record, verbatim. Nothing is resolved: a `part_id` and a
    `provenance_ref` are stored, not looked up (ADR-0006)."""
    return _robot(robot_id)


@server.tool()
def forward_kinematics(robot_id: str, pose_json: str = "") -> dict:
    """Where every link and the tool sit at a given pose.

    `pose_json` maps joint_id to a value — radians for revolute joints,
    millimetres for prismatic. Omitted joints are zero. All positions are
    relative to `base_link` and are never a world claim (ADR-0009)."""
    robot = _robot(robot_id)
    try:
        frames = kin.forward_kinematics(robot, _pose(pose_json))
    except kin.Incomplete as exc:
        return {"verdict": "incomplete", "missing": exc.missing, "detail": exc.detail}
    tool_mat, _ = kin.tool_matrix(robot, frames)
    return {
        "relative_to": robot["base_link"],
        "tool_offset": kin.tool_offset_description(robot),
        "links_mm": {lid: [round(c, 4) for c in kin.position(m)]
                     for lid, m in sorted(frames.items())},
        "tool_mm": [round(c, 4) for c in kin.position(tool_mat)],
    }


@server.tool()
def reach(robot_id: str, target_mm: str = "", tolerance_mm: float = 5.0,
          samples: int = 20000, seed: int = 0) -> dict:
    """Sampled reachability. `target_mm` is "X,Y,Z" relative to base_link;
    omit it for the sampled extent of the whole workspace.

    Read the verdict, not just its name. **"Reachable" is a claim and its
    negative is not** — a sampled workspace only ever proves the positive, so an
    unreached target returns `no-sample-reached-it` with the sample count, never
    "unreachable" (ADR-0013)."""
    samples, clamped = _clamp_samples(samples)
    target = tuple(float(c) for c in target_mm.split(",")) if target_mm else None
    verdict = kin.reach_verdict(_robot(robot_id), target, tolerance_mm, samples, seed)
    return dict(verdict, clamped=clamped) if clamped else verdict


@server.tool()
def hold(robot_id: str, pose_json: str = "", payload_g: float = 0.0) -> dict:
    """Static gravity load per joint at a held pose, against continuous actuator
    torque.

    The result is a **static upper bound**: efficiency, friction, backlash and
    acceleration are not modelled, so real capacity is lower (ADR-0004). The
    `bound` field says so and must not be dropped when summarising."""
    return kin.hold_verdict(_robot(robot_id), _pose(pose_json), payload_g)


@server.tool()
def can_it(robot_id: str, target_mm: str, payload_g: float = 0.0,
           tolerance_mm: float = 5.0, samples: int = 20000, seed: int = 0) -> dict:
    """Can this body put its tool there and hold that load?

    Four verdicts, and **none of them is an unqualified yes** (ADR-0015):
    `cannot` (a real claim — a static upper bound was exceeded, and real capacity
    is lower still), `within-static-bound` (the closest thing to yes, and not a
    guarantee), `unproven` (no sample reached it — not a negative), and
    `incomplete` (a named missing input).

    There is deliberately **no score**. An affordance float is a frequency
    estimate and no trials were run; rank on `margin_nm`, which has units."""
    samples, clamped = _clamp_samples(samples)
    target = tuple(float(c) for c in target_mm.split(","))
    verdict = aff_lib.affordance(_robot(robot_id), target, payload_g,
                                 tolerance_mm, samples, seed)
    return dict(verdict, clamped=clamped) if clamped else verdict


@server.tool()
def bill_of_parts(robot_id: str, assembly_id: str = "", harness_id: str = "",
                  as_project: bool = False) -> dict:
    """What the robot is made of, in OpenBuildCore's own vocabulary, so
    `what-can-i-build` answers about it without translation (ADR-0006).

    Note `designed`: links that are OpenDesignCore artifact hashes are reported
    separately and NOT as `make` requirements, because ClawBot holds the hash and
    not the bounding box. Judge those with OBC's `can-print --from-sidecar`.

    `as_project=True` is the fabrication-bound path and is **gated on a PD-5 policy
    declaration** (ADR-0019). An undeclared record refuses, because emitting it
    would make the `none` declaration on the author's behalf at the far end. The
    plain bill of parts is ungated."""
    robot = _robot(robot_id)
    assembly = manifest_lib.load("assemblies", assembly_id, "assembly_id") \
        if assembly_id else None
    harness = manifest_lib.load("harnesses", harness_id, "harness_id") \
        if harness_id else None
    built = manifest_lib.build_manifest(robot, assembly, harness)
    if not as_project:
        return built
    try:
        notes = manifest_lib.check_policy(robot)
    except manifest_lib.PolicyRefusal as exc:
        return {"verdict": "refused", "manifest": built, "detail": str(exc),
                "note": ("the plain bill of parts is in `manifest` and is unaffected; "
                         "what is refused is the fabrication-bound document")}
    return {
        "verdict": "emitted",
        "manifest": built,
        "openbuildcore_project": manifest_lib.as_project(robot, built),
        "policy_notes": notes,
        "declaration_travels_as": (
            "`policy_categories`, machine-readable, as of 2026-08-23. Its "
            "taxonomy_version does not travel: BINGO pins an id's meaning by freezing "
            "the category list hash into the job at order time, so there is no "
            "asset-level field for it (ADR-0022)"),
    }


@server.tool()
def export_urdf(robot_id: str) -> dict:
    """URDF for a robot, or the reasons it cannot be expressed as one.

    Export is **partial by construction**: URDF has no way to say "unknown", and
    `urdfdom` refuses a revolute joint without a `<limit>`. So a record honest
    about what nobody sourced has no valid URDF, and this returns the offending
    joints rather than emitting a zero (ADR-0007). Provenance never survives the
    conversion — the format has nowhere to record where a limit came from."""
    xml, refusals = urdf_lib.export_urdf(_robot(robot_id))
    if refusals:
        return {"verdict": "refused", "refusals": refusals,
                "detail": ("this is ADR-0007 working, not a bug. Fill in the sources, "
                           "or keep the record and lose the export.")}
    return {"verdict": "exported", "urdf": xml,
            "lost": "provenance: URDF cannot record where a joint limit came from"}


@server.tool()
def validate() -> dict:
    """Check every record: citations, radian ranges, tree structure, mimic
    cycles, voltage indexing, and cross-file references.

    **Reads only.** There is no tool that repairs what this finds: a write to
    `data/` is a person's judgement about physical hardware, and an agent quietly
    filling in a joint limit is the precise failure this repo exists to prevent
    (ADR-0016)."""
    report = validate_lib.Report()
    robots = {}
    for path in sorted((ROOT / "data" / "robots").glob("*.json")):
        model = validate_lib.check_robot(path, report)
        if model:
            robots[model["robot"].get("robot_id")] = model
    for path in sorted((ROOT / "data" / "actuators").glob("*.json")):
        validate_lib.check_actuator(path, report)
    for directory, checker in (("assemblies", validate_lib.check_assembly),
                               ("harnesses", validate_lib.check_harness)):
        for path in sorted((ROOT / "data" / directory).glob("*.json")):
            checker(path, report, robots)
    return {
        "valid": not report.failures,
        "failures": report.failures,
        "warnings": report.warnings,
        "todo_source_placeholders": report.todo_sources,
        "note": ("warnings do not block. An unknown joint limit is the honest state "
                 "this repo is built around, not an error (ADR-0003)."),
    }


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
