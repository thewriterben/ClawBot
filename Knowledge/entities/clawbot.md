---
title: ClawBot
type: entity
updated: 2026-08-22
sources:
  - ClawBot/DECISIONS.md
  - ClawBot/README.md
---

# ClawBot

This repo. The fifth Open\*Core peer: **mechanisms** — links, joints, actuators, and what they can reach.

**Status:** scaffold. Schemas, six ADRs, and this wiki. No code.

## What it models

A tree of rigid **links** joined by **joints**, driven by **actuators**. Structurally URDF (ADR-0005). A link is exactly one of three kinds, mirroring [[openbuildcore]]'s requirement kinds: a `part_id` from [[openpartscore]], a `make` carrying size and material, or a `provenance_ref` to an [[opendesigncore]] artifact (ADR-0006).

## What it refuses to model

The two decisions that define the repo are both refusals:

- **No `reach_mm`** (ADR-0003). A vendor reach figure is a radius to an unstated frame, measured without a tool, over a sphere that joint limits and self-collision carve holes in. Reach is computed from the joint model or the answer is "incomplete", naming the joint that is missing limits.
- **No scalar `payload_kg`** (ADR-0004). Capacity falls with extension because load torque is force times moment arm. Capacity is derived per-pose from **continuous** actuator torque — never stall torque — and a measured figure is accepted only with the pose it was measured at.

Both are the same move [[openbuildcore]] made with print time: if nobody measured it and it cannot be derived from something that was, the answer is that it cannot be given.

## Known limitations, stated rather than buried

- **Computed reach will be optimistic** until self-collision is modelled — the opposite of the conservative error OBC accepted in axis-aligned fit. ADR-0003 records this as a wrong-direction error deliberately taken, and requires every reachability answer to say it is a joint-limit result.
- **Derived capacity is a static upper bound.** No acceleration, no gearbox efficiency, no dynamics. ADR-0004 permits the bound only if the word "bound" travels with it.
- **Open chains only.** The tree cannot express a loop, so delta arms and four-bar linkages are absent rather than approximated (ADR-0005, ROADMAP).

## Position

Fifth peer; see [[ecosystem-position]]. Imports nothing — the peers meet at data, not an API (ADR-0006).

A likely consumer is [[oh-ben-claw]], which commands physical robots and currently has no shareable robot *model* to command them against. ADR-0001 records that as the reason ClawBot is not a crate inside it: a model inside the runtime is a model no other consumer can read without taking the runtime as a dependency. **TODO(source):** this is reasoning about Oh-Ben-Claw from its README, not a request from it. Nobody has asked for ClawBot yet, and ADR-0001 says so.
