---
title: The URDF round trip, and what it costs ADR-0005
type: concept
updated: 2026-08-22
sources:
  - https://raw.githubusercontent.com/ros/urdfdom/master/xsd/urdf.xsd (retrieved 2026-08-22)
  - https://raw.githubusercontent.com/ros/urdfdom/master/urdf_parser/src/joint.cpp (retrieved 2026-08-22)
  - https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-0103.rst (retrieved 2026-08-22)
  - ClawBot/schema/robot.schema.json
  - ClawBot/DECISIONS.md (ADR-0003, ADR-0005)
---

# The URDF round trip, and what it costs ADR-0005

[[open-questions]] question 1, and [[inherited-invariants]] #8 — the breach ClawBot recorded
against itself on the day it was created. ADR-0005 chose a URDF-shaped tree over DH
parameters and justified it with a claim about a converter nobody had written:

> "Structurally URDF, so a converter is a mapping rather than a reinterpretation."

The sources are now read ([[urdf-spec]], [[rep-103-units]]). **The claim is half right, and
the half that is wrong is the half ClawBot cares about.**

The *structure* does map: links, joints, parent/child, origin, axis, limits. That was never
really in doubt. What does not map is **absence** — and absence is the thing ADR-0003 and
ADR-0004 are built out of.

## Export: ClawBot's honesty is not expressible

ClawBot's whole position on unknown data is that `limits: null` means UNKNOWN, never
unlimited, and that a derivation over it answers "incomplete" and names the joint.

`urdfdom` **will not parse a revolute or prismatic joint without a `limit` element**, and
within one, a missing `effort` or `velocity` is fatal. So a ClawBot record in exactly the
state ADR-0003 was designed to handle — a real mechanism whose joint travel nobody has
sourced yet — **has no valid URDF representation at all.**

There are three ways out and only one is acceptable:

| Option | Verdict |
|---|---|
| Emit `lower="0" upper="0"` | **Refused.** Silently converts UNKNOWN into "locked at zero", inventing a physical claim. Invariant #1 and #3 together. |
| Emit some wide default | **Refused.** Invents travel the mechanism may not have; over-claims in the same direction ADR-0003 already regrets on self-collision. |
| **Refuse to export, name the joint** | The only one consistent with the repo. Export fails loudly the way OpenBuildCore's placeholder envelope failed every fit check. |

So URDF export is **partial by construction** — a fully-sourced robot exports, an honest
incomplete one does not. That is a real limitation and it belongs in the ADR, not here.

## Import: URDF's defaults must not be believed

The mirror problem, and the more dangerous one because it is silent.

- A joint with `<limit effort="10" velocity="1"/>` and no bounds parses cleanly as
  `lower = upper = 0`. Indistinguishable in the parsed tree from a genuinely locked joint.
- A joint with no `axis` becomes `(1, 0, 0)` with a debug log nobody reads.

An importer that trusts the parser's output writes plausible values into a repo whose
entire purpose is refusing them. **The importer must read the XML, not the parsed tree** —
because the parse is where the absence is destroyed. An attribute that was not present
imports as absent; `source.citation` for such a joint records that the value was defaulted
by the format, not stated by the author.

## What else does not survive

| URDF | ClawBot today | Disposition |
|---|---|---|
| `floating`, `planar` joint types | absent from the enum | **being added** — see the base-frame decision |
| `mimic` (coupled joints) | no equivalent | **being added** — coupled tree, not a loop |
| many `visual` / `collision` per link | none | out of scope; geometry is [[opendesigncore]]'s (ADR-0006) |
| full inertia tensor | `mass_g` only | needed for dynamics, which ADR-0004 refuses. Record the gap. |
| `safety_controller` soft limits | none | a *second* limit set. Which one binds a derivation is undecided. |
| `transmission` / `mechanicalReduction` | `actuator_id` + `gear_ratio` | maps, roughly |
| `dynamics` damping/friction | none | out of scope, and both default to `0` in URDF — the same absence-as-zero trap |
| lengths in **metres** (REP-103) | millimetres (ADR-0005) | converts; one boundary, one factor of 1000 |

## The verdict on ADR-0005

**The decision stands; its consequences section is wrong and needs amending.** DH is still
refused for the reason given, and the reason is now better than it was — see
[[dh-conventions]], which adds two arguments ADR-0005 did not make.

But "a converter is a mapping rather than a reinterpretation" was too strong, and it was
made without evidence in the way invariant #8 warns about. The honest form: *structure maps
both ways; absence maps neither way, and the importer and exporter each need an explicit
rule for it.*

This is the second time the platform has learned this. PD-1 chose atopile from documentation
and a web search and it survived four hours. This claim survived a day, and only because
nobody tried it.
