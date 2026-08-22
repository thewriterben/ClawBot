#!/usr/bin/env python3
"""The staleness gate, and the emitter's own output shape.

OpenPartsCore ADR-0003's discipline, adopted here: the generated binding is
**committed**, and `--check` regenerates it and diffs. A data change without a
regenerated binding fails rather than drifting — which is the whole reason the
platform has generated bindings at all, since three hand-maintained copies of
Oh-Ben-Claw's registry drifting apart is the documented failure OpenPartsCore
was created to end.

Cargo is not required to run these; they check the emitter, not the crate. The
Rust crate's own tests live in `bindings/rust/tests/binding.rs` and include three
`compile_fail` doctests that prove the type-level refusals.

    python tests/test_emit_rust.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import emit_rust  # noqa: E402


def test_the_committed_binding_is_not_stale():
    """The gate. If this fails, run `python scripts/emit_rust.py` and commit."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "emit_rust.py"), "--check"],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


def test_rendering_is_deterministic():
    assert emit_rust.render() == emit_rust.render()


def test_records_are_sorted_by_id_so_a_reorder_is_not_a_diff():
    text = emit_rust.render()
    ids = [a["actuator_id"] for a in emit_rust.load("actuators", "actuator_id")]
    assert ids == sorted(ids)
    positions = [text.index(json.dumps(i)) for i in ids]
    assert positions == sorted(positions)


def test_the_header_carries_the_types_not_the_output_file():
    """ADR-0017: types live in the emitter. Editing lib.rs works until the next
    regeneration silently reverts it, so the header is where they must be."""
    assert "pub struct Radians" in emit_rust.HEADER
    assert "pub struct StallTorque" in emit_rust.HEADER
    assert "pub struct ContinuousTorque" in emit_rust.HEADER


def test_there_is_no_conversion_from_stall_to_continuous():
    """The refusal ADR-0004 exists for, checked at the source level so it cannot
    be reintroduced by an emitter edit that the Rust doctests would catch only
    after someone runs cargo."""
    header = emit_rust.HEADER
    assert "impl From<StallTorque> for ContinuousTorque" not in header
    assert "fn to_continuous" not in header
    assert "impl From<ContinuousTorque> for StallTorque" not in header


def test_radians_and_degrees_are_separate_types_with_explicit_conversion():
    header = emit_rust.HEADER
    assert "pub struct Radians(pub f64)" in header
    assert "pub struct Degrees(pub f64)" in header
    assert "impl From<Degrees> for Radians" in header
    assert "impl From<Radians> for Degrees" in header


def test_the_compile_fail_guarantees_are_actually_asserted():
    """Three of ADR-0017's promises are compile-time. Doctests make them run."""
    header = emit_rust.HEADER
    assert header.count("```compile_fail") >= 3


def test_no_default_impl_and_no_unwrapping_accessor():
    """A limits_or_default() would undo invariant #3 in one function."""
    header = emit_rust.HEADER
    assert "impl Default" not in header
    assert "_or_default" not in header
    assert "unwrap_or" not in header


def test_nothing_in_the_crate_looks_like_a_safety_authority():
    """ADR-0017's last refusal. Track 0 is the safety authority; this is a data
    model, and a function named like a permission is how those get confused."""
    header = emit_rust.HEADER
    for forbidden in ("fn is_safe", "fn permit", "fn allow", "fn authorize", "fn approve"):
        assert forbidden not in header


def test_absent_values_emit_none_never_a_sentinel():
    joint = {"joint_id": "j", "type": "revolute", "parent": "a", "child": "b",
             "origin": {}, "limits": None}
    rendered = emit_rust.render_joint(joint)
    assert "limits: None" in rendered
    assert "axis: None" in rendered
    assert "gear_ratio: None" in rendered
    assert "0.0" not in rendered.split("limits:")[1].split(",")[0]


def test_a_data_change_makes_the_check_fail():
    """Proof the gate is load-bearing rather than always green."""
    original = emit_rust.load
    emit_rust.load = lambda d, k: ([{
        "actuator_id": "phantom", "type": "hobby-servo",
        "stall_torque_nm": [{"value": 1.0, "at_volts": 6.0}],
    }] if d == "actuators" else original(d, k))
    try:
        drifted = emit_rust.render()
    finally:
        emit_rust.load = original
    committed = (ROOT / "bindings" / "rust" / "src" / "lib.rs").read_text(encoding="utf-8")
    assert drifted != committed, "the check would not notice a data change"
    assert "phantom" in drifted


def test_the_crate_manifest_takes_no_dependencies():
    cargo = (ROOT / "bindings" / "rust" / "Cargo.toml").read_text(encoding="utf-8")
    body = cargo.split("[dependencies]")[1]
    assert not [line for line in body.splitlines()
                if line.strip() and not line.strip().startswith("#")], \
        "zero dependencies is the point (OpenPartsCore ADR-0003)"


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
