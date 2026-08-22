---
title: REP-103 — standard units and coordinate conventions
type: source-summary
updated: 2026-08-22
sources:
  - https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-0103.rst (retrieved 2026-08-22)
---

# REP-103 — standard units and coordinate conventions

The normative document behind URDF's units. URDF's own XSD declares no units at all
([[urdf-spec]]); REP-103 is where they are actually stated, which is worth knowing before
writing a converter that assumes.

## Units

Base: length **metre**, mass **kilogram**, time **second**, current **ampere**.
Derived: angle **radian**, frequency hertz, force newton, power watt, voltage volt,
temperature **celsius**, magnetism tesla.

## Frames

> "All systems are right handed."

Body-fixed: **x forward, y left, z up**. Geographic (ENU): x east, y north, z up.
Two suffixed exceptions exist — `_optical` (z forward, x right, y down) and `_ned`
(x north, y east, z down).

## Rotation

Preference order, most to least preferred: **quaternion**, rotation matrix,
**fixed-axis roll-pitch-yaw in X, Y, Z order**, then Euler angles — the last discouraged
outright, because there are 24 conventions and the notation does not record which.

## Why this matters here

**Three agreements and one divergence with ClawBot.**

Agreements: radians (ADR-0005), right-handed, and rpy as fixed-axis X-Y-Z — which is what
`transform.rpy_rad` already means, though the schema does not currently say so and should.

Divergence: **metres versus millimetres.** ClawBot uses millimetres by inheritance from
OpenPartsCore and OpenDesignCore ADR-0004, which take it from PicoGK. Neither is wrong; they
are different boundaries. The consequence is a factor of 1000 at exactly one place per
boundary — which is [[opendesigncore]]'s own rule for unit conversion, and the rule that
makes this survivable rather than a recurring bug.

**Worth noting for its own sake:** REP-103's argument against Euler angles is
*structurally identical* to ADR-0005's argument against DH. Twenty-four conventions, and
the numbers do not record which one they are. The platform reached the same conclusion
independently, about a different notation, for the same reason. See [[dh-conventions]].
