---
title: ROBOTIS Dynamixel XM430-W350 — a datasheet that says the quiet part
type: source-summary
updated: 2026-08-22
sources:
  - https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/ (retrieved 2026-08-22)
  - https://www.motioncontroltips.com/how-to-calculate-continuous-and-peak-torque-values-for-servo-applications/ (retrieved 2026-08-22, secondary — trade press)
---

# ROBOTIS Dynamixel XM430-W350 — a datasheet that says the quiet part

Read looking for an actuator with a published **continuous** torque rating, to test whether
ADR-0004's central premise survives contact with a good datasheet. The XM430 is a
well-documented smart servo from a vendor that publishes more than most.

## What is published

Stall torque at three supply voltages — 3.8 N.m at 11.1 V (2.1 A), 4.1 N.m at 12.0 V (2.3 A),
4.8 N.m at 14.8 V (2.7 A) — with matching no-load speeds of 43, 46 and 57 rev/min. Gear ratio
353.5:1. Mass 82 g. Contactless absolute magnetic encoder, 12-bit over 360 degrees. Operating
temperature -5 to +80 C.

## What is not published

**No continuous torque figure.** And the manual says so itself:

> "The given Stall torque rating for a servo is different from its continuous output rating"

and notes that the maximum torque shown in its own performance-graph testing is less than the
stall figure. The vendor names the distinction, tells you the headline number is not the usable
one — and then publishes only the headline number and a graph.

## Why this is the best possible confirmation of ADR-0004

The ADR predicted: *"most robots described here will not have a payload answer, because most
actuator datasheets publish stall torque and nothing else."* That was written from reasoning,
not from a datasheet. It is now confirmed on a high-quality source from a vendor who
demonstrably understands the distinction.

The schema's shape is vindicated exactly as designed. An XM430 record carries three
`stall_torque_nm` figures, each with its `at_volts` — which is why that field is required, since
the same servo differs by 26% across its own voltage range — and a **null**
`continuous_torque_nm`. It validates. Capacity is underivable. The answer is "incomplete,
naming this actuator", and that answer is *true*.

## The rule of thumb, and why it is still refused

Secondary vendor and trade sources describe continuous torque as roughly 30-50% of stall, with
derating of roughly 10-15% per 10 C above rated ambient. Those figures are recorded here as
**prose about what the literature says**, and they must not reach `data/`:

- The range spans a factor of 1.67. A capacity derived from its low end and one derived from its
  high end are different engineering answers, and picking one is a guess.
- The sources are vendor blogs and trade press, not the actuator's own datasheet.
- `continuous_torque_nm.how_determined` exists specifically to reject this. A rule of thumb
  applied to a stall figure is not a determination; it is a guess wearing a citation.

**The honest path stays the one ADR-0004 named:** measure the thing, record the pose, record the
method. What this source adds is that the path is not a fallback for cheap hardware — it is the
path even for good hardware from a good vendor.

## Also relevant: `travel` and `feedback`

Extended Position Control Mode makes this actuator multi-turn, so its `travel` is not bounded by
a single revolution — which is why the actuator schema bounds `_rad` fields at +/- 4*pi rather
than +/- pi, and why `continuous_rotation` is a separate flag. The absolute encoder makes
`feedback: magnetic-encoder` the correct token, and the schema's note that `none` is "a real
answer and a consequential one" is the contrast case.
