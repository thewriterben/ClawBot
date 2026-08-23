#!/usr/bin/env python3
"""Guards on the MCP surface, which is where the caveats are most likely to be lost.

Two invariants from ADR-0016 are easy to break by accident and hard to notice:

* **no tool may take a filesystem path** — `import_urdf` over MCP is an arbitrary
  file read wearing a domain-specific name;
* **every tool returns its whole verdict** — a bare boolean or a bare distance
  strips the assumptions ADR-0003/0004/0013/0015 require to travel inside the
  value, and a tool result gets summarised by a model before a human sees it.

Skips rather than passes when the MCP SDK is absent.

    python tests/test_mcp.py
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


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


def load():
    try:
        from clawbot_mcp import server
    except SystemExit as exc:                       # the SDK's absence message
        _skip(str(exc))
    except ImportError as exc:
        _skip(f"MCP SDK not importable: {exc}")
    return server


TOOLS = ["list_robots", "list_actuators", "describe_robot", "forward_kinematics",
         "reach", "hold", "can_it", "bill_of_parts", "export_urdf", "validate"]

PATHLIKE = ("path", "file", "filename", "dir", "directory", "url", "src")


def test_every_advertised_tool_exists():
    server = load()
    missing = [t for t in TOOLS if not hasattr(server, t)]
    assert not missing, f"missing tools: {missing}"


def test_no_tool_accepts_a_filesystem_path():
    """ADR-0016's security guard. A path parameter here is a file-read gadget."""
    server = load()
    offenders = []
    for name in TOOLS:
        for param in inspect.signature(getattr(server, name)).parameters:
            if any(token in param.lower() for token in PATHLIKE):
                offenders.append(f"{name}({param})")
    assert not offenders, f"path-like parameters on the MCP surface: {offenders}"


def test_there_is_no_urdf_import_tool():
    server = load()
    assert not hasattr(server, "import_urdf")
    assert not hasattr(server, "urdf_import")


def test_there_is_no_repair_or_write_tool():
    """The propose side is empty and must stay empty (ADR-0016)."""
    server = load()
    for forbidden in ("repair", "fix", "write_robot", "add_robot", "set_limit",
                      "approve", "propose", "actuate", "move", "command"):
        assert not hasattr(server, forbidden), f"{forbidden} must not exist"


def test_sample_counts_are_clamped_and_the_clamp_is_reported():
    server = load()
    unchanged, note = server._clamp_samples(100)
    assert unchanged == 100 and note is None
    clamped, note = server._clamp_samples(10_000_000)
    assert clamped == server.MAX_SAMPLES
    assert "clamped" in note and "10000000" in note


def test_list_actuators_surfaces_whether_capacity_is_derivable_at_all():
    """The single most consequential fact about an actuator record, and the one a
    summariser would drop first."""
    server = load()
    for row in server.list_actuators():
        assert "capacity_derivable" in row
        assert row["capacity_derivable"] == bool(row["continuous_torque_volts"])


def test_list_robots_surfaces_joints_that_block_every_derivation():
    server = load()
    for row in server.list_robots():
        assert "joints_without_limits" in row
        assert row["derivable"] == (not row["joints_without_limits"])


def test_reach_passes_the_caveats_through_untouched():
    server = load()
    import kinematics as kin
    robot = {
        "schema_version": 0, "robot_id": "t", "kind": "arm", "base_link": "base",
        "links": [{"link_id": "base", "part_id": "m/x", "source": {"citation": "t"}},
                  {"link_id": "l", "part_id": "m/x", "source": {"citation": "t"}}],
        "joints": [{"joint_id": "j", "type": "revolute", "parent": "base", "child": "l",
                    "origin": {}, "axis": {"x": 0, "y": 0, "z": 1},
                    "limits": {"lower_rad": -1, "upper_rad": 1,
                               "source": {"citation": "t"}},
                    "source": {"citation": "t"}}],
        "source": {"citation": "t"},
    }
    original = server._robot
    server._robot = lambda rid: robot
    try:
        verdict = server.reach("t", "0,0,0", 5.0, 100, 0)
    finally:
        server._robot = original
    assert "caveats" in verdict
    assert any("NOT a collision result" in c for c in verdict["caveats"])
    assert verdict["seed"] == 0
    assert verdict["relative_to"] == "base"


def test_validate_reports_but_does_not_repair():
    server = load()
    result = server.validate()
    for key in ("valid", "failures", "warnings", "todo_source_placeholders"):
        assert key in result
    assert "do not block" in result["note"]


def test_every_tool_has_a_docstring_that_states_its_refusal():
    """The docstring IS the contract for an MCP client. A tool whose docstring
    does not say what it will not claim invites a caller to over-read it."""
    server = load()
    for name in ("reach", "hold", "can_it", "export_urdf", "validate"):
        doc = inspect.getdoc(getattr(server, name)) or ""
        assert "ADR-" in doc, f"{name} docstring cites no decision"
        assert len(doc) > 200, f"{name} docstring is too thin to carry its caveats"


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
