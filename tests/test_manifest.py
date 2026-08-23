#!/usr/bin/env python3
"""The seam test: does ClawBot's output actually satisfy OpenBuildCore's schema?

ADR-0006 says the peers meet at data rather than at an API, and `manifest.py`
claims its output "drops into `data/projects/` without translating anything".
That is a claim about another repo's schema, and the only honest way to hold it
is to fetch that schema and check against it — which is what this does.

If OpenBuildCore is not checked out beside this repo, or `jsonschema` is not
installed, the cross-repo tests skip rather than pass. A skipped test is an
honest "not checked"; a passing one that never ran is the failure mode this
whole platform is built to refuse.

    python tests/test_manifest.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import manifest  # noqa: E402

OBC_SCHEMA = (Path(__file__).resolve().parents[2] / "OpenBuildCore"
              / "schema" / "project.schema.json")
SRC = {"citation": "test fixture"}


class Skip(Exception):
    pass


def _skip(reason: str):
    """Skip in a way BOTH runners understand.

    `raise Skip(...)` is caught by the __main__ runner below and reads as a
    FAILURE under pytest, which turns "this peer is not checked out" into a red
    build. pytest's own skip raises a BaseException subclass, so the runner
    below has to catch it by name rather than by type.
    """
    import sys
    if "pytest" in sys.modules:
        import pytest
        pytest.skip(reason)
    raise Skip(reason)


def fixture_robot() -> dict:
    """A robot exercising all three link kinds at once."""
    return {
        "schema_version": 0,
        "robot_id": "seam-fixture",
        "make": "Fixture",
        "model": "Mk I",
        "kind": "arm",
        "base_link": "base",
        "links": [
            {"link_id": "base", "make": {"size_mm": {"x": 80, "y": 80, "z": 20},
                                         "material": "petg"}, "source": SRC},
            {"link_id": "upper-arm", "part_id": "mechanical/alu-extrusion-2020",
             "source": SRC},
            {"link_id": "fore-arm", "part_id": "mechanical/alu-extrusion-2020",
             "source": SRC},
            {"link_id": "wrist", "provenance_ref": {
                "artifact_sha256": "e8401edf6cd1" + "0" * 52,
                "schema": "odc/provenance/0.2"}, "source": SRC},
        ],
        "joints": [
            {"joint_id": "shoulder", "type": "revolute", "parent": "base",
             "child": "upper-arm", "origin": {}, "axis": {"x": 0, "y": 0, "z": 1},
             "limits": {"lower_rad": -1.5, "upper_rad": 1.5, "source": SRC},
             "actuator_id": "not-in-data", "source": SRC},
            {"joint_id": "elbow", "type": "revolute", "parent": "upper-arm",
             "child": "fore-arm", "origin": {}, "axis": {"x": 0, "y": 1, "z": 0},
             "limits": None, "source": SRC},
            {"joint_id": "wrist-pitch", "type": "revolute", "parent": "fore-arm",
             "child": "wrist", "origin": {}, "axis": {"x": 0, "y": 1, "z": 0},
             "limits": {"lower_rad": -1.0, "upper_rad": 1.0, "source": SRC},
             "source": SRC},
        ],
        "source": SRC,
    }


def fixture_assembly() -> dict:
    return {"schema_version": 0, "assembly_id": "a", "robot_id": "seam-fixture",
            "source": SRC,
            "steps": [{"step_id": "mount", "action": "Bolt the base down",
                       "fasteners": [
                           {"part_id": "mechanical/m3x8-shcs", "qty": 4},
                           {"spec": "M3 heat-set insert OD 4.6", "qty": 4}]}]}


def built() -> dict:
    return manifest.build_manifest(fixture_robot(), fixture_assembly(), None)


# ------------------------------------------------------------------ the mapping

def test_identical_part_ids_aggregate():
    """Two links, one part id, quantity two. OBC allocates exclusively, so this
    is the difference between a buildable arm and one short an extrusion."""
    buy = {r["part_id"]: r["qty"] for r in built()["buy"]}
    assert buy["mechanical/alu-extrusion-2020"] == 2


def test_fastener_quantities_come_from_the_assembly():
    buy = {r["part_id"]: r["qty"] for r in built()["buy"]}
    assert buy["mechanical/m3x8-shcs"] == 4


def test_make_links_carry_obc_fields_verbatim():
    make = built()["make"][0]
    assert make["size_mm"] == {"x": 80, "y": 80, "z": 20}
    assert make["material"] == "petg"


def test_provenance_links_are_not_invented_into_make_requirements():
    """The refusal that matters. ClawBot holds a hash and no bounding box, so
    emitting a size_mm here would be a fabricated number in a valid document."""
    m = built()
    assert len(m["designed"]) == 1
    assert m["designed"][0]["link_id"] == "wrist"
    assert all(r["make"] != "wrist" for r in m["make"])
    project = manifest.as_project(fixture_robot(), m)
    assert all(r.get("make") != "wrist" for r in project["requires"])


def test_uncatalogued_parts_are_reported_not_dropped():
    """A part with no registry id cannot be matched — saying so beats silence."""
    what = {r["what"]: r["qty"] for r in built()["uncatalogued"]}
    assert what["M3 heat-set insert OD 4.6"] == 4
    assert what["not-in-data"] == 1


def test_unlimited_joints_are_surfaced_in_the_rendering():
    text = manifest.render(built(), fixture_robot())
    assert "elbow" in text and "incomplete" in text


# --------------------------------------------------------------- the cross-repo

def load_obc_schema():
    if not OBC_SCHEMA.exists():
        _skip(f"OpenBuildCore not found at {OBC_SCHEMA}")
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        _skip("jsonschema not installed")
    return json.loads(OBC_SCHEMA.read_text(encoding="utf-8"))


def test_emitted_project_validates_against_openbuildcores_own_schema():
    import jsonschema
    schema = load_obc_schema()
    project = manifest.as_project(fixture_robot(), built())
    jsonschema.validate(project, schema)


def test_a_fabricated_size_would_have_been_caught_here():
    """Proof the check above is load-bearing: OBC's schema rejects a make
    requirement with no size_mm, so if manifest.py ever emitted a provenance
    link as a make without inventing dimensions, this test would fail — and if
    it invented them, only the refusal test above would catch it."""
    import jsonschema
    schema = load_obc_schema()
    project = manifest.as_project(fixture_robot(), built())
    project["requires"].append({"make": "wrist", "material": "petg", "qty": 1})
    try:
        jsonschema.validate(project, schema)
    except jsonschema.ValidationError:
        return
    raise AssertionError("OBC's schema accepted a make requirement with no size_mm")


# --------------------------------------------------------- ADR-0019: the PD-5 gate

def declared(*categories, version="REFUSAL-CATEGORIES v0.1 (draft), read 2026-08-22"):
    robot = fixture_robot()
    robot["policy"] = {"categories": list(categories), "taxonomy_version": version,
                       "declared_by": "test"}
    return robot


def test_an_undeclared_record_will_not_emit_a_project():
    """Emitting it would make the `none` declaration on the author's behalf."""
    try:
        manifest.check_policy(fixture_robot())
    except manifest.PolicyRefusal as exc:
        assert "on your behalf" in str(exc)
        assert "policy.taxonomy_version" in str(exc)
        return
    raise AssertionError("undeclared records must not emit a fabrication-bound document")


def test_the_plain_bill_of_parts_is_ungated():
    """A shopping list for a person is not a document bound for a network."""
    built = manifest.build_manifest(fixture_robot(), None, None)
    assert built["buy"], "the ungated path still works without a declaration"


def test_declaring_none_emits_normally():
    assert manifest.check_policy(declared("none")) == []


def test_a_network_wide_refused_category_will_not_emit():
    for category in ("weapons.firearms", "weapons.other", "covert.surveillance",
                     "ip.counterfeit"):
        try:
            manifest.check_policy(declared(category))
        except manifest.PolicyRefusal as exc:
            assert "no valid destination" in str(exc)
            assert "BINGO is authoritative" in str(exc)
            continue
        raise AssertionError(f"{category} must not emit")


def test_a_prosthetic_emits_and_carries_its_category():
    """regulated.medical is node-opt-in, not refused. The design is wrong if it
    treats every category as a prohibition."""
    notes = manifest.check_policy(declared("regulated.medical"))
    assert notes, "an opt-in category should be surfaced, not silently passed"
    assert "regulated.medical" in notes[0]
    assert "opted in" in notes[0]


def test_a_stale_taxonomy_version_is_flagged_not_refused():
    notes = manifest.check_policy(declared("regulated.rf", version="v0.9 (2030)"))
    assert any("what counts" in n for n in notes)


def test_clawbot_never_infers_a_category():
    """The declaration is the author's and only the author's. Nothing in the
    emitter reads geometry to guess one."""
    source = (Path(__file__).resolve().parent.parent / "scripts" / "manifest.py").read_text(
        encoding="utf-8")
    gate = source.split("def check_policy")[1].split("def as_project")[0]
    for inferring in ("size_mm", "bbox", "link", "geometry", "length"):
        assert inferring not in gate, f"the policy gate reads {inferring}"


def test_the_declaration_travels_as_data():
    """Was the opposite assertion until 2026-08-23. OpenBuildCore's project schema
    is additionalProperties:false and had no field for a policy declaration, so it
    could only go as prose in `description` — reported as OpenBuildCore#9 and fixed
    by its ADR-0007. This test is kept rather than deleted because the failure it
    used to guard is the interesting one: a declaration that does not travel as
    data reads, downstream, as no declaration at all."""
    robot = declared("regulated.medical")
    project = manifest.as_project(robot, manifest.build_manifest(robot, None, None))
    assert project["policy_categories"] == ["regulated.medical"]
    assert "regulated.medical" not in project["description"],         "no longer smuggled through prose"
    import jsonschema
    jsonschema.validate(project, load_obc_schema())


def test_the_taxonomy_version_deliberately_does_not_travel():
    """BINGO pins an id's meaning by freezing the list hash into the JOB at order
    time, not at the asset. Inventing an asset-level version field would fork a
    mechanism that is already solved, so it stays in the ClawBot record."""
    robot = declared("regulated.rf")
    project = manifest.as_project(robot, manifest.build_manifest(robot, None, None))
    assert "taxonomy_version" not in project
    assert robot["policy"]["taxonomy_version"], "but it is kept where it was declared"


def test_an_undeclared_record_emits_no_policy_field_at_all():
    """Belt and braces on the refusal: check_policy stops an undeclared record
    before it reaches here, and if that ever regressed, emitting an ABSENT field
    is still safer than emitting an empty one — BINGO reads absent as `none`
    declared and an empty list as neither."""
    robot = fixture_robot()
    project = manifest.as_project(robot, manifest.build_manifest(robot, None, None))
    assert "policy_categories" not in project
    import jsonschema
    jsonschema.validate(project, load_obc_schema())


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = skipped = 0
    for name, fn in tests:
        try:
            fn()
            print(f"pass  {name}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {name} — {exc}")
        except BaseException as exc:              # noqa: BLE001 - see _skip
            # AFTER AssertionError, which is itself a BaseException: the other
            # order swallows the failure branch entirely and re-raises real
            # failures instead of counting them.
            if type(exc).__name__ not in ("Skip", "Skipped"):
                raise
            skipped += 1
            print(f"SKIP  {name} — {exc}")
    print(f"\n{len(tests) - failed - skipped}/{len(tests)} passed"
          + (f", {skipped} skipped" if skipped else ""))
    sys.exit(1 if failed else 0)
