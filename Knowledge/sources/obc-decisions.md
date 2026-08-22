---
title: OpenBuildCore DECISIONS.md
type: source-summary
updated: 2026-08-22
sources:
  - OpenBuildCore/DECISIONS.md
  - OpenBuildCore/README.md
  - OpenBuildCore/ROADMAP.md
  - OpenBuildCore/schema/machine.schema.json
---

# OpenBuildCore DECISIONS.md

Six ADRs, 2026-08-15 to 2026-08-16. The single most load-bearing source for [[clawbot]]'s own decisions — four of ClawBot's six ADRs argue from one of these.

## ADR-0001 — a separate repo for inventory

Inventory is mutable user state referencing canonical part ids (PD-2), so it gets its own peer rather than living in the cited registry or inside [[oh-ben-claw]]'s deployment generator. Justified by "a different lifecycle, different privacy posture, and different consumers".

ClawBot ADR-0001 is the same argument shape and reaches the same answer for different reasons.

## ADR-0002 — quantity-aware exclusive allocation

Read [[oh-ben-claw]]'s `planDeployment` closely and named three properties that do not survive generalisation: presence-only matching (`.length > 0`, so a project needing two hosts is satisfiable by one board), no exclusivity, and hardcoded suggestion strings that go stale as the registry grows.

The fix: quantities, exclusive allocation, specific parts allocated **before** capabilities (a capability requirement would otherwise consume a specific part's only unit and report a false gap), and suggestions computed by querying the registry.

Greedy is admitted as non-optimal, and the ADR says a fix "belongs in a superseding ADR rather than a quiet rewrite".

## ADR-0004 — a shopping list must state its basis

Sequential (parts reused, take the max shortfall) or simultaneous (shortfalls sum). With the seed catalogue the answers differ: 2 versus 3 LoRa radios. "Picking one silently is how a shopping list under-orders — and under-ordering is discovered at the bench, after the parts arrive."

The basis is printed in human output and carried as a `basis` field in JSON. Source of [[inherited-invariants]] #4.

## ADR-0005 — machines are owned state, print time is never modelled

**The direct ancestor of ClawBot ADR-0003 and ADR-0004.** A time estimate exists only from a `measured_throughput` with a `how_measured`; everything else answers "requires slicing". The reasoning against a volumetric guess: no provenance, wrong by factors rather than percentages, "and once printed it will be read as a measurement".

Also: every machine needs a `source.citation` because "a capability is a physical claim about hardware" — the sentence ClawBot's joint-limit citation requirement is modelled on. And fit is checked in six axis-aligned orientations only, with false negatives accepted as "the safe direction to be wrong in" — which ClawBot ADR-0003 explicitly does *not* get to say about optimistic reach.

The `machine.schema.json` is worth reading directly. Its field descriptions carry the reasoning inline rather than deferring to the ADR — `axis_calibration` explains that absence means UNKNOWN and never "fine", and that a residual of exactly zero "is suspicious rather than excellent". ClawBot's schemas copy that habit.

## ADR-0006 — made parts are a third requirement kind

"A missing part and an unmakeable part fail differently and are fixed differently." Collapsing both into "missing" would put an unmakeable part on a shopping list "where it would sit unbought forever looking like an ordering oversight rather than a design problem".

Consequences worth carrying: two booleans rather than one, because "one label cannot say which half failed"; `makeable: null` when no machines are declared; the validator checks a made part's **shape only** and never against owned machines, because "projects are shareable; machines are personal" and validating against machines "would make a project's validity depend on who is reading it".

Source of ClawBot ADR-0006's three link kinds, and of the `make` field shape ClawBot copies verbatim so a manifest needs no translation.

**Three kinds is stated as the ceiling** — a fourth needs its own ADR and a real case. ClawBot inherited the ceiling along with the kinds.
