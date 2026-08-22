---
title: OpenPartsCore
type: entity
updated: 2026-08-22
sources:
  - OpenPartsCore/README.md
---

# OpenPartsCore

The canonical parts registry: one JSON Schema, data files one part per file, generated bindings for every consumer language. Pre-alpha, schema v0.

Exists to fix the registry drift documented in [[oh-ben-claw]]'s ECOSYSTEM-INTEGRATION.md, where the same component data existed in Rust, TypeScript and Python copies that diverged.

## Namespaces

`boards` (dev boards, ingested from Oh-Ben-Claw's `registry.json`, not forked), `electronic` (ICs, passives, connectors), `mechanical` (motors, fasteners, bearings, stock), `material` (filament, resin, sheet stock).

**`mechanical` is where ClawBot's actuators and hardware belong.** [[clawbot]] stores a `part_id` and does not resolve it (ClawBot ADR-0006); the facts about the servo — mass, dimensions, datasheet torque — live here with citations.

## The rules ClawBot inherits

- **Every entry carries a citation. An uncited value fails validation. No plausible-looking numbers.**
- **Length fields are millimetres and end in `_mm`** (matching OpenDesignCore ADR-0004). Other units are named in the field: `mass_g`, `voltage_v`.

ClawBot extends the second with `_rad` for angles (ClawBot ADR-0005) rather than inventing a document-level angle convention. Making the unit local to the field name is the point of the rule.

- **User inventory does not live here** (PD-2). Same reason ClawBot's `owned-robots.json` is git-ignored while `data/robots/` is not.

## Open question for us

Does an actuator's torque data belong in an OpenPartsCore `mechanical` entry, in ClawBot's `data/actuators/`, or split? ClawBot's actuator schema currently duplicates fields a parts entry would plausibly carry — make, model, mass, electrical. The defensible split is that OpenPartsCore holds *what the part is* and ClawBot holds *what it does in a mechanism*, but the boundary has not been tested against a real entry. See [[open-questions]].
