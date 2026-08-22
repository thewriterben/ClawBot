---
title: Oh-Ben-Claw
type: entity
updated: 2026-08-22
sources:
  - Oh-Ben-Claw/README.md (read to the "four control modes" table; remainder not yet ingested)
  - OpenDesignCore/wiki/concepts/ecosystem-map.md
---

# Oh-Ben-Claw

An embodied AI agent in Rust, built on the ZeroClaw architecture. "One brain, many bodies." Began as a multi-device orchestrator over an MQTT spine and grew a full embodied control stack. ~33 crates per [[opendesigncore]]'s ecosystem map.

**The most likely consumer of [[clawbot]], and the repo ClawBot was deliberately not built inside.**

## The stack, as its README describes it

One loop — perceive → remember → react → act — over a shared substrate:

- **World memory** (`src/memory/world`): bitemporal, append-only. Every observation carries a *valid time* and a *transaction time*, so the agent can answer "what did we believe the battery was at 12:04, and when did we find out?".
- **Track 0 safety gate** (`src/security/limits`): every physical action — servo, motor, GPIO — passes a `SafetyLimit` constraining pins, value range and command rate before reaching hardware. A `RiskClass` marks each tool safe or physical, and high-blast-radius physical actions require per-call human approval. **The same gate logic is mirrored in the ESP32-S3 firmware**, so a node protects itself if the host link drops.
- Four control modes on that substrate: reflexes, foresight, deliberative missions, fleet coordination.

It is benchmarked component-by-component against ROS 2 Nav2, slam_toolbox/Cartographer, AMCL, BehaviorTree.CPP and Open-RMF in its `docs/SOTA-COMPARISON.md` — **not yet read**, and a high-value ingest for [[open-questions]], since it is the closest thing on disk to a survey of the robotics state of the art.

## The relationship to ClawBot

ClawBot ADR-0001 rejected putting the robot model in here. The reasoning: a model that lives inside the runtime is a model no other consumer can read without taking the runtime as a dependency — the registry-drift problem [[openpartscore]] exists to fix, recreated one layer up.

The division that falls out:

| | |
|---|---|
| Oh-Ben-Claw | commands a robot in real time, behind Track 0 |
| ClawBot | describes what the robot *is*, so something else can reason about it |

**ClawBot never actuates anything.** That is stated in its README's "Not this" and its ROADMAP's "Not ever", and Track 0 is the reason the line is easy to hold: there is already a correct place for physical actuation, with a safety model ClawBot has no business duplicating.

## Also upstream of the platform

Its `registry.json` (44+ boards, connector taxonomy, capability tokens) is the seed for [[openpartscore]]'s `boards` namespace — ingested, not forked. Its deployment planner is the prior art [[openbuildcore]]'s ADR-0002 read closely and then diverged from on three specific points (presence-only matching, no exclusivity, hardcoded suggestions).

**Conflict:** [[opendesigncore]]'s ecosystem map calls Oh-Ben-Claw's registry the component database "three repos consume" and notes drift across the Rust/TS/Python copies as a *known problem*; OpenPartsCore's README treats that drift as the thing it was built to end. Not a disagreement about facts — a snapshot taken before and after a fix was decided. Worth re-checking whether the drift has actually stopped, since nothing read so far confirms the generated bindings exist (OpenPartsCore's README says `bindings/`, **none yet**).

## Not yet read

Most of an 849-line README, plus `docs/EMBODIED-ARCHITECTURE.md`, `docs/SOTA-COMPARISON.md`, `docs/ECOSYSTEM-INTEGRATION.md`, and the `Knowledge Base/` directory. This page should be revised once they are.
