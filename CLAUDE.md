# ClawBot — working rules

Read [`DECISIONS.md`](DECISIONS.md) before changing anything structural. The ADRs are the reasoning, not a changelog; a decision reversed without a superseding ADR is a decision lost.

## The invariant

**Never invent physical data.** Every number that describes hardware — a joint limit, a link length, a torque — comes from a cited source, or it is absent, or it is a `TODO(source)` placeholder that fails loudly until a real source arrives. A plausible number is worse than a missing one, because a missing number announces itself and a plausible one does not.

This is inherited from the platform, not local policy. See `Knowledge/concepts/inherited-invariants.md`.

## Specific refusals

These are decided. If a change would introduce one, it needs a superseding ADR, not a commit message.

| Refused | Why | ADR |
|---|---|---|
| A `reach_mm` field | A vendor reach figure is a radius to an unstated frame, before a tool, over a sphere the arm cannot fill | ADR-0003 |
| A scalar `payload_kg` | Capacity is a function of pose; one number is true at one configuration | ADR-0004 |
| Stall torque in a capacity derivation | It is an instantaneous figure the actuator cannot sustain | ADR-0004 |
| DH parameters as the stored form | Two incompatible conventions; the table does not record which — and it cannot carry the tool transform or branch | ADR-0005, ADR-0007 |
| Degrees in a data file | `_rad` in the file, degrees only in rendered output | ADR-0005 |
| Importing a peer repo | The peers meet at data that already had to exist | ADR-0006 |
| Exporting URDF with a zero for an unknown limit | The format cannot say "unknown"; export refuses and names the joint instead | ADR-0007 |
| Importing URDF through the parsed tree | The parse is where absence is destroyed — missing bounds become `0`, a missing axis becomes `(1,0,0)` | ADR-0007 |
| A world-coordinate reach or capacity answer | Every answer is relative to `base_link`; a world pose has no source here | ADR-0009 |
| Assuming z-up for a non-fixed base | Gravity direction is unknown, so a static capacity answers incomplete rather than assuming level ground | ADR-0009 |
| Commanding an actuator, or solving IK | ClawBot publishes the contract; the loop stays behind Oh-Ben-Claw's Track 0 | ADR-0010 |
| Writing another repo's config format | That takes its format as a dependency, which is the coupling ADR-0006 prevents | ADR-0010 |
| A modelled build time, or summed per-step estimates | Summing guesses produces a total more precise than any of its inputs | ADR-0011 |
| A fastener torque defaulting to "hand tight" | Absent means UNKNOWN; a stripped insert in a printed part is unrecoverable | ADR-0011 |
| Reading `permits_full_travel: null` as true | Null means nobody checked, and an unchecked cable run makes reach over-claim | ADR-0012 |
| Inventing a `size_mm` for a `provenance_ref` link | ClawBot holds the hash and not the bounding box; OBC's `can-print --from-sidecar` judges the real geometry | ADR-0006 |
| A torque figure as a scalar wearing a voltage | Torque against voltage is a curve; the XM430 spans 26% across its own rated range | ADR-0014 |
| Interpolating between published torque rows | "Approximately linear" is an unsourced model whose output is indistinguishable from a datasheet value | ADR-0014 |
| An affordance score in [0,1] | A float is a frequency estimate and no trials were run — and SayCan consumers *multiply* it, so it would vanish into a product | ADR-0015 |
| A `can` verdict | Sampled reach is sound positive, static capacity sound negative; no combination yields a provable yes | ADR-0015 |
| An MCP tool taking a filesystem path | That is an arbitrary file read wearing a domain-specific name | ADR-0016 |
| An MCP tool that repairs what `validate` finds | A write to `data/` is a person's judgement about physical hardware | ADR-0016 |
| A scalar `gearbox.efficiency` | Efficiency varies with input speed, ratio, load, temperature and lubricant — eight curves, no scalar | ADR-0018 |
| A running efficiency applied to a static hold | Efficiency curves are indexed by input speed; a held pose has none. Wrong in kind, not in value | ADR-0018 |
| Treating a catalogue figure as a fact about your unit | A vendor may be publishing a population average — ±30% unit-to-unit is stated in one datasheet | ADR-0018 |
| A scalar starting or backdriving torque | Published as ranges spanning an order of magnitude, varying unit to unit | ADR-0021 |
| A `typical` beside a range | It gets read as the answer and the range becomes decoration | ADR-0021 |
| Deriving a passive hold from backdriving torque | That a load below the minimum is held unpowered is a physical claim with no source here, and it fails by letting go | ADR-0021 |
| Inferring a policy category from geometry | A declaration is the author's claim about intent, not something a bounding box implies | ADR-0019 |
| Emitting a fabrication-bound manifest for an undeclared record | BINGO reads an absent declaration AS `none` declared, so emitting makes that claim on the author's behalf | ADR-0019 |
| A `policy_categories` enum in the schema | That forks a taxonomy whose own spec says growth needs a spec revision | ADR-0019 |
| Refusing to *describe* a mechanism in a refused category | A notation that cannot express a thing does not prevent it — it prevents it being described accurately | ADR-0019 |

## Units

- Lengths: millimetres, field suffix `_mm` (OpenPartsCore rule, OpenDesignCore ADR-0004).
- Angles: radians, field suffix `_rad` (ADR-0005).
- Anything else names its unit in the field: `mass_g`, `torque_nm`, `velocity_rad_s`.

## When an answer cannot be given

Say so, and say which input is missing. "Incomplete: joint `shoulder_pitch` has no limits" is a useful answer. A default that lets the computation proceed is not. Absence of evidence is recorded as absence and never as a negative finding — no machines declared means `makeable: null` in OpenBuildCore, and the same rule holds here.

## The knowledge base

[`Knowledge/`](Knowledge/) is an LLM-maintained wiki. Its schema is [`Knowledge/CLAUDE.md`](Knowledge/CLAUDE.md) and it governs everything under that directory. Two rules matter most from outside it:

- **Wiki pages are never evidence.** A number entering a schema, a data file or a computation cites a raw source, never a wiki page.
- **The robotics pages were empty on purpose, and the rule that emptied them still stands.** Six sources were ingested on 2026-08-22 and seven of eight topics are answered; the last is gearbox efficiency, and it stays open because it would license a *number* rather than a *decision*. Filling a page from recall would manufacture the exact uncited content the invariant refuses. `Knowledge/concepts/open-questions.md` is the reading list.

## Status

Pre-alpha. Four schemas (`robot`, `actuator`, `assembly`, `harness`), twenty-two ADRs, six stdlib
scripts (`validate`, `kinematics`, `affordance`, `manifest`, `urdf`, `emit_rust`), an MCP
surface and a zero-dependency Rust binding. 154 Python tests, 35 Rust tests, all run by CI. `data/` holds one
real actuator record; no robot record yet, and that one needs hardware in hand.

Do not write a README claim the code does not support. Equally: do not leave a status claim
standing after the code has moved past it — this section said "no code" for exactly as long as
that was true.

## Verify with

```
python scripts/validate.py
python scripts/emit_rust.py --check
python -m pytest tests/ -q
cd bindings/rust && cargo test
```

`bindings/rust/src/lib.rs` is **generated and committed**. Never edit it — the types live in
`scripts/emit_rust.py`, and a hand edit works right up until the next regeneration reverts it.

Tests are **known answers, not pinned outputs** — OpenDesignCore's distinction. A pinned-output
test says the code still does what it did; a known-answer test says it does the right thing.
When a test fails, check the arithmetic before changing the expectation.

Stdlib only for `scripts/`, matching OpenPartsCore and OpenBuildCore. `tests/` may use
`jsonschema` to check output against a **peer's own schema file**, and must *skip* rather than
pass when that peer is not checked out — a skipped test is an honest "not checked".
