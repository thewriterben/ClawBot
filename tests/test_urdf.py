#!/usr/bin/env python3
"""The round trip ADR-0007 made claims about, actually run.

ADR-0005 was written on a claim about a converter nobody had written, and that
cost the repo its highest-priority open question. These tests are the standing
guard against the same thing happening to ADR-0007: every assertion it makes
about what URDF can and cannot express is exercised here against a real document.

    python tests/test_urdf.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import urdf  # noqa: E402

SRC = {"citation": "test fixture"}


def write(xml: str) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".urdf", delete=False,
                                         encoding="utf-8")
    handle.write(xml)
    handle.close()
    return Path(handle.name)


def imported(xml: str):
    return urdf.import_urdf(write(xml), None)


def exportable_robot() -> dict:
    """Fully sourced: bounds, effort and velocity all present. This one exports."""
    return {
        "schema_version": 0, "robot_id": "exportable", "kind": "arm",
        "base_link": "base",
        "links": [{"link_id": "base", "part_id": "mechanical/x", "source": SRC},
                  {"link_id": "arm", "part_id": "mechanical/x", "mass_g": 250,
                   "source": SRC}],
        "joints": [{"joint_id": "j1", "type": "revolute", "parent": "base",
                    "child": "arm",
                    "origin": {"xyz_mm": {"x": 100, "y": 0, "z": 50}},
                    "axis": {"x": 0, "y": 0, "z": 1},
                    "limits": {"lower_rad": -1.5, "upper_rad": 1.5, "effort_nm": 2.0,
                               "velocity_rad_s": 3.0, "source": SRC},
                    "source": SRC}],
        "source": SRC,
    }


# --------------------------------------------------- import: do not believe defaults

def test_limit_without_bounds_imports_as_unknown_not_zero():
    """The finding at the centre of ADR-0007. urdfdom reads this as locked at zero."""
    robot, notes = imported("""
      <robot name="r">
        <link name="base"/><link name="arm"/>
        <joint name="j1" type="revolute">
          <parent link="base"/><child link="arm"/>
          <axis xyz="0 0 1"/>
          <limit effort="10" velocity="1"/>
        </joint>
      </robot>""")
    limits = robot["joints"][0]["limits"]
    assert "lower_rad" not in limits and "upper_rad" not in limits
    assert limits["effort_nm"] == 10.0 and limits["velocity_rad_s"] == 1.0
    assert any("LOCKED AT ZERO" in n for n in notes)


def test_missing_axis_is_recorded_as_a_format_default():
    robot, notes = imported("""
      <robot name="r">
        <link name="base"/><link name="arm"/>
        <joint name="j1" type="revolute">
          <parent link="base"/><child link="arm"/>
          <limit lower="-1" upper="1" effort="10" velocity="1"/>
        </joint>
      </robot>""")
    joint = robot["joints"][0]
    assert joint["axis"] == {"x": 1.0, "y": 0.0, "z": 0.0}
    assert "DEFAULTED by the format" in joint["source"]["citation"]
    assert any("silently use (1,0,0)" in n for n in notes)


def test_parent_and_child_are_actually_read():
    """An ElementTree element with no children is falsy; `find(...) or fallback`
    would silently blank every parent link. Guarding the fix."""
    robot, _ = imported("""
      <robot name="r">
        <link name="base"/><link name="arm"/>
        <joint name="j1" type="fixed">
          <parent link="base"/><child link="arm"/>
        </joint>
      </robot>""")
    assert robot["joints"][0]["parent"] == "base"
    assert robot["joints"][0]["child"] == "arm"


def test_metres_become_millimetres():
    robot, _ = imported("""
      <robot name="r">
        <link name="base"/><link name="arm"><inertial><mass value="0.25"/></inertial></link>
        <joint name="j1" type="fixed">
          <parent link="base"/><child link="arm"/>
          <origin xyz="0.1 0 0.05" rpy="0 1.5708 0"/>
        </joint>
      </robot>""")
    assert robot["joints"][0]["origin"]["xyz_mm"] == {"x": 100.0, "y": 0.0, "z": 50.0}
    assert abs(robot["joints"][0]["origin"]["rpy_rad"]["p"] - 1.5708) < 1e-9
    assert robot["links"][1]["mass_g"] == 250.0        # kg -> g


def test_underscored_names_are_renamed_and_the_rename_is_reported():
    robot, notes = imported("""
      <robot name="r">
        <link name="base_link"/><link name="upper_arm"/>
        <joint name="shoulder_pan" type="fixed">
          <parent link="base_link"/><child link="upper_arm"/>
        </joint>
      </robot>""")
    assert robot["base_link"] == "base-link"
    assert robot["joints"][0]["joint_id"] == "shoulder-pan"
    assert any("renamed 'base_link' -> 'base-link'" in n for n in notes)


def test_geometry_and_inertia_are_not_imported_but_are_flagged():
    robot, _ = imported("""
      <robot name="r">
        <link name="base">
          <visual><geometry><box size="0.1 0.1 0.1"/></geometry></visual>
          <inertial><mass value="1"/>
            <inertia ixx="1" ixy="0" ixz="0" iyy="1" iyz="0" izz="1"/></inertial>
        </link>
      </robot>""")
    note = robot["links"][0]["note"]
    assert "not imported" in note and "OpenDesignCore" in note
    assert "inertia tensor" in note
    assert "make" not in robot["links"][0]        # no fabricated size_mm


def test_mimic_survives_import():
    robot, _ = imported("""
      <robot name="r">
        <link name="base"/><link name="l"/><link name="r2"/>
        <joint name="left" type="prismatic">
          <parent link="base"/><child link="l"/><axis xyz="1 0 0"/>
          <limit lower="0" upper="0.02" effort="5" velocity="0.1"/>
        </joint>
        <joint name="right" type="prismatic">
          <parent link="base"/><child link="r2"/><axis xyz="1 0 0"/>
          <limit lower="0" upper="0.02" effort="5" velocity="0.1"/>
          <mimic joint="left" multiplier="-1"/>
        </joint>
      </robot>""")
    mimic = robot["joints"][1]["mimic"]
    assert mimic["joint"] == "left" and mimic["multiplier"] == -1.0


def test_safety_controller_is_flagged_as_a_second_limit_set():
    _, notes = imported("""
      <robot name="r">
        <link name="base"/><link name="arm"/>
        <joint name="j1" type="revolute">
          <parent link="base"/><child link="arm"/><axis xyz="0 0 1"/>
          <limit lower="-1" upper="1" effort="10" velocity="1"/>
          <safety_controller k_velocity="10" soft_lower_limit="-0.9"/>
        </joint>
      </robot>""")
    assert any("second limit set" in n for n in notes)


def test_imported_tool_is_null_and_says_why():
    robot, _ = imported('<robot name="r"><link name="base"/></robot>')
    assert robot["tool"] is None
    assert "meaningless" in robot["note"]


# ----------------------------------------------------- export: refuse, do not default

def test_export_refuses_a_joint_with_unknown_limits_and_names_it():
    robot = exportable_robot()
    robot["joints"][0]["limits"] = None
    xml, refusals = urdf.export_urdf(robot)
    assert xml is None
    assert any("j1" in r and "cannot say 'unknown'" in r for r in refusals)


def test_export_refuses_missing_effort_and_velocity_separately():
    """urdfdom treats both as fatal, so both are refusals, not one."""
    robot = exportable_robot()
    del robot["joints"][0]["limits"]["effort_nm"]
    del robot["joints"][0]["limits"]["velocity_rad_s"]
    xml, refusals = urdf.export_urdf(robot)
    assert xml is None
    assert any("effort_nm" in r for r in refusals)
    assert any("velocity_rad_s" in r for r in refusals)


def test_export_reports_every_offending_joint_not_just_the_first():
    robot = exportable_robot()
    robot["links"].append({"link_id": "hand", "part_id": "mechanical/x", "source": SRC})
    robot["joints"].append({"joint_id": "j2", "type": "revolute", "parent": "arm",
                            "child": "hand", "origin": {},
                            "axis": {"x": 0, "y": 1, "z": 0}, "limits": None,
                            "source": SRC})
    robot["joints"][0]["limits"] = None
    _, refusals = urdf.export_urdf(robot)
    assert any("j1" in r for r in refusals) and any("j2" in r for r in refusals)


def test_a_fully_sourced_robot_does_export():
    xml, refusals = urdf.export_urdf(exportable_robot())
    assert refusals == []
    assert '<robot name="exportable">' in xml
    assert 'lower="-1.5"' in xml and 'effort="2"' in xml


def test_export_writes_metres():
    xml, _ = urdf.export_urdf(exportable_robot())
    assert 'xyz="0.1 0 0.05"' in xml       # 100 mm, 50 mm -> metres


def test_export_omits_the_inertia_tensor_rather_than_zeroing_it():
    """Zeros would be a claim about mass distribution nobody made."""
    xml, _ = urdf.export_urdf(exportable_robot())
    assert "<mass" in xml and "<inertia " not in xml


def test_export_carries_a_header_saying_provenance_is_lost():
    xml, _ = urdf.export_urdf(exportable_robot())
    assert "Provenance does not survive" in xml


# ------------------------------------------------------------------- the round trip

def test_structure_survives_the_round_trip():
    """ADR-0007's surviving half: structure maps both ways."""
    original = exportable_robot()
    xml, refusals = urdf.export_urdf(original)
    assert refusals == []
    back, _ = urdf.import_urdf(write(xml), "exportable")

    assert back["base_link"] == original["base_link"]
    assert [l["link_id"] for l in back["links"]] == \
           [l["link_id"] for l in original["links"]]
    joint_out, joint_in = original["joints"][0], back["joints"][0]
    for field in ("joint_id", "type", "parent", "child"):
        assert joint_in[field] == joint_out[field]
    assert joint_in["axis"] == joint_out["axis"]
    for field in ("lower_rad", "upper_rad", "effort_nm", "velocity_rad_s"):
        assert abs(joint_in["limits"][field] - joint_out["limits"][field]) < 1e-9
    for k in "xyz":
        assert abs(joint_in["origin"]["xyz_mm"][k]
                   - joint_out["origin"]["xyz_mm"][k]) < 1e-6


def test_provenance_does_not_survive_the_round_trip():
    """ADR-0007's other half, and the reason URDF is not the storage format:
    the citation that made a joint limit admissible has nowhere to live."""
    original = exportable_robot()
    original["joints"][0]["limits"]["source"] = {"citation": "vendor datasheet p.4"}
    xml, _ = urdf.export_urdf(original)
    assert "vendor datasheet" not in xml
    back, _ = urdf.import_urdf(write(xml), "exportable")
    assert "vendor datasheet" not in back["joints"][0]["limits"]["source"]["citation"]
    assert "URDF import" in back["joints"][0]["limits"]["source"]["citation"]


def test_an_honest_incomplete_robot_cannot_round_trip_at_all():
    """The asymmetry ADR-0007 accepted: the records this repo exists to hold are
    exactly the ones URDF cannot represent."""
    robot = exportable_robot()
    robot["joints"][0]["limits"] = None
    xml, refusals = urdf.export_urdf(robot)
    assert xml is None and refusals


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
