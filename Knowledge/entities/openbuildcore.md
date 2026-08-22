---
title: OpenBuildCore
type: entity
updated: 2026-08-22
sources:
  - OpenBuildCore/README.md
  - OpenBuildCore/DECISIONS.md (ADR-0001..0006)
  - OpenBuildCore/ROADMAP.md
---

# OpenBuildCore

"Tell it what you own. It tells you what you can build, and exactly what you're missing." Fourth peer; inventory, machines, and project matching. Pre-alpha, eight projects in the catalogue.

The **closest prior art for ClawBot**, and the source of most of the discipline ClawBot inherits. Read its DECISIONS.md before arguing with any of ours.

## The three requirement kinds

A project declares requirements as exactly one of: a specific `part_id`, a `capability` any part may provide, or a `make` — a part you fabricate, carrying `size_mm` and `material`. [[clawbot]]'s three link kinds deliberately mirror this so the vocabularies do not diverge (ClawBot ADR-0006).

Its ADR-0006 is the one worth internalising: **a missing part and an unmakeable part fail differently and are fixed differently.** Short a radio, buy one; need a 260 mm part on a 220 mm bed, nothing you can buy fixes it. So made parts never reach the shopping list, and a result carries two booleans — `buildable` and `makeable` — because one label cannot say which half failed.

## Machines, and the decision ClawBot copied

Its ADR-0005 is the direct ancestor of ClawBot ADR-0003 and ADR-0004. **Print time is never modelled.** A machine gets a time estimate only from a `measured_throughput` its owner measured, with a `how_measured` saying how; everything else answers "requires slicing". A volumetric guess is a number with no provenance that would be read as a measurement.

The shipped K2 Plus record demonstrated the placeholder discipline uncomfortably: its `envelope_mm` was a `1×1×1` `TODO(source)` for a day, and every fit check on it failed loudly during that time. That is the intended behaviour of a placeholder, and ClawBot's `example/` templates copy it deliberately.

**Absence is not a negative finding.** No machines declared means `makeable: null` — unknown, not "cannot".

## Why ClawBot is not a machine kind here

The full argument is ClawBot ADR-0001. In short: `envelope_mm: {x, y, z}` with axis-aligned containment is correct for a printer and structurally wrong for an arm, whose reachable set is non-convex and often holed; capability varies within the workspace where a printer's does not; and a robot is simultaneously reference data, owned state, and an in-progress project, where a machine record can only be the second.

## Where the peers meet

Its README states the rule plainly: "**The peers meet at the provenance record, not at an API.** OpenBuildCore imports nothing from OpenDesignCore; it reads a file that already had to exist." `can-print --from-sidecar` reads [[opendesigncore]]'s `artifact.bbox_mm` and `volume_cubic_mm` directly. [[clawbot]] follows the same rule.

## Open item relevant to us

Its ROADMAP still carries "**Measure a K2 Plus throughput**" — the envelope is sourced, the throughput is not, so the machine Benji owns answers "requires slicing" for every time question. Worth noting as the live demonstration that this discipline has an ongoing cost somebody is actually paying.
