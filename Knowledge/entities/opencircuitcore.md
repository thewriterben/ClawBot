---
title: OpenCircuitCore
type: entity
updated: 2026-08-22
sources:
  - OpenCircuitCore/README.md
  - OpenCircuitCore/ARCHITECTURE.md
  - OpenCircuitCore/DECISIONS.md (ADR-0001 through ADR-0006)
  - OpenCircuitCore/DEPENDENCIES.md
  - OpenCircuitCore/ROADMAP.md
  - OpenCircuitCore/boards/ (reference-esp32s3, sensor-breakout)
---

# OpenCircuitCore

The electronics peer. Circuits designed, verified and manufactured through **KiCad, scripted** —
driven by `kicad-cli` and design scripts rather than by hand in the GUI.

Read on 2026-08-22 during the platform survey, and written up late — see the note at the end of
[[open-questions]] about that.

## What it does

The pipeline is `design scripts → KiCad project → ERC → DRC → gerbers + BOM + STEP/STL +
provenance record`. A design that does not pass its checks **does not export**, which is the same
gate shape [[opendesigncore]] applies to geometry.

Two boards exist: a reference ESP32-S3 module with an I2C sensor, and a sensor breakout whose
gerbers were checked against a **cited** JLCPCB fab profile with zero violations. Both emit a
provenance record — sources, upstream netlist, outputs, ERC/DRC results, KiCad version, commit —
in canonical JSON, hash-comparable with [[opendesigncore]]'s and BINGO's.

## Why it matters to a mechanism repo

Not obvious at first, and it turned out to be direct.

**An arm's wiring is a real constraint on its joint travel.** ClawBot ADR-0012 says a cable that
crosses a joint *is* a joint limit, and the `harness` schema's `controller.part_id` points at a
board. The two repos touch at the controller: OpenCircuitCore designs the thing that drives the
actuators, and ClawBot records which joint lands on which of its channels.

They do not import each other. A `part_id` is stored, not resolved, per ADR-0006 — the same rule
that governs every other peer boundary here.

**And the co-design path already exists.** `kicad-cli pcb export step|stl` produces board
geometry that [[opendesigncore]] imports at its mesh boundary, so an enclosure is fitted to the
real board rather than to a guess. A mechanism adds a dimension that neither currently handles: a
moving part's clearance requirement is a swept volume, not a bounding box. That connection is
noted in [[ecosystem-position]] and remains speculative.

## Two decisions worth borrowing

**"A custom DRC rule ships only once it has been proven to fire" (its ADR-0006).** This is the
same discipline ClawBot's 31 negative tests exist for — a rule nobody has watched reject
something is a rule that might be passing because it never looks. Two repos reached it
independently, about different subject matter.

**"The MCP surface inspects and verifies; it does not regenerate" (its ADR-0005).** ClawBot
ADR-0016 landed on the neighbouring position — every tool reads or derives, and the propose side
is empty. Worth noting that OCC's surface *could* regenerate and chose not to, whereas ClawBot's
has nothing to regenerate; the constraint is the same shape from different starting points.

## The lesson it paid for

OpenCircuitCore's ADR-0001 chose **atopile** as the authoring layer. ADR-0003 dropped it **the
same day**, on evidence: the CLI is maintenance-only, 0.16+ moved to a hosted browser workspace,
and the last CLI release will not install without a C++ toolchain. A SaaS dependency in the
design path contradicts a platform that is local-first everywhere else.

That is platform decision PD-1, and it is the origin of [[inherited-invariants]] #8 — *kernel
choices get installed and run before they are recorded*. The decision was made from documentation
and a web search and survived four hours. ClawBot was in breach of the same rule for a day, over
ADR-0005's unverified converter claim, until [[urdf-round-trip]] closed it.

**tscircuit stays on the watch list**, not as a dependency: actively developed, MIT, but its
ERC/DRC was incomplete as of 2026-08, so KiCad would remain the verification substrate anyway.

## Boundaries it holds

- **KiCad is GPLv3 and is invoked as an external process only, never linked** (its ADR-0002).
  Outputs are not derivative works, and invocation stays at arm's length.
- **No invented component values.** Every part fact traces to [[openpartscore]] or a datasheet,
  or it is `TODO(source)`. The same gate ClawBot applies to joint limits.
- **It is not a router.** Its ROADMAP says routing is interactive in KiCad or an external tool —
  "Not writing one" — which is the same posture ClawBot takes toward motion planning.
- **Pricing and stock are never stored.** Live from distributor APIs, keyed by part id.
