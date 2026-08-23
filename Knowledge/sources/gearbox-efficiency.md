---
title: Gearbox efficiency and backlash — a five-variable curve, and a figure that is not about your unit
type: source-summary
updated: 2026-08-23
sources:
  - Harmonic Drive LLC, "FR Gearing — Precision Gearing and Motion Control", engineering data, 16 pp. (retrieved 2026-08-22, https://www.harmonicdrive.net/_hd/content/documents/fr.pdf)
  - Trade-press and vendor articles on planetary backlash measurement, via survey results (retrieved 2026-08-22, secondary — used only for the no-standard claim, and marked as such)
---

# Gearbox efficiency and backlash — a five-variable curve, and a figure that is not about your unit

The last of the eight sourcing topics, and it was left until last deliberately: every other topic
licensed a **decision**, which can rest on a survey. This one would license a **number** —
an efficiency multiplies a derived capacity and turns ADR-0004's upper bound into an estimate —
so only a vendor document with a stated method was admissible.

One was found. It closes the topic, and not in the direction expected.

## Efficiency is a function of five variables, in the vendor's own words

> "Efficiency varies depending on input speed, ratio, load level, temperature, and type of
> lubrication. The effect of these factors are illustrated in the curves shown."

Eight charts follow. There is no scalar anywhere.

## And the published curves are themselves conditional

> "Efficiency of the gears vary depending on output torque. The efficiency curves given on the
> preceding pages are for units operating at an output torque rated for 2,000 rpm. Efficiency of
> a unit operating at a load below the rated torque may be estimated using a compensation curve
> and formula shown below."

So the curves are read at an operating point, then **corrected again** for load. The document's
own worked example, for an FR 40-160-2GR at 1,000 rpm input, 1,560 lb-in output, 40 °C:

```
Torque ratio = 1,560 / 2,600 = 0.6
Ke           = 0.87
Efficiency   = 58 × 0.87 = 50 %
```

**Two things in that example are worth staring at.** The base efficiency is **58%**, and at 60%
of rated load it falls to **50%** — while the secondary sources this reading started from quote
"80 to 90 percent when properly lubricated". The rule of thumb is not merely imprecise here; on
this vendor's own numbers it is wrong by a factor approaching two, in the unsafe direction.

## The finding that reaches past gearboxes

On torsional stiffness, the same document:

> "The values quoted are the average of many tests of actual units. The spring rate of an
> individual unit may vary within approximately ±30% of the average."

A catalogue figure here is explicitly a **property of the model, not of the unit on your bench**.
Nothing in this platform distinguishes those two kinds of number. A cited value has so far meant
"somebody published it"; this source is a vendor saying, in a datasheet, that their published
value describes a population and an individual may sit 30% off it.

That distinction is not specific to gearboxes and probably applies to several fields already in
these schemas. It is the substance of ADR-0018.

## What a proper method statement looks like

The same page, on no-load starting and backdriving torque:

> "Values quoted are based on actual tests with the component sets assembled in their housings,
> and inclusive of friction resistance of oil seals, and churning of oil."

That is a `how_determined` written by a vendor — what was assembled, what was included. Worth
keeping as the reference example of the standard this repo asks for. Note also that the figures
it qualifies are **ranges**, not points: FR 40 starting torque is 3–50 N·cm and backdriving
torque 7–190 N·m, each spanning better than an order of magnitude.

## Backlash has no measurement standard

**Secondary sourcing, and flagged as such** — this claim comes from trade-press and vendor
articles rather than a standards body, and no primary source was found for it.

The reported situation: manufacturers commonly average four or more points on the output shaft;
some apply 2% of rated torque to generate the rating and others apply less; and a usable spec
needs units, applied load, direction, ambient temperature and reference point. If that is
right, two vendors' backlash figures are not comparable without their methods, which is the
`how_determined` pattern again.

**Recorded as believed and under-sourced.** It is consistent with everything primary in this
page, and it is not strong enough to build a schema rule on by itself.

**Followed up 2026-08-23, and half of it held.** The core — that two vendors' figures are not
comparable without their methods — is now primary: a vendor states in its own words that its
definition of backlash differs from the one many others use. The framing was too strong, though.
A standard with backlash in its title does exist; it appears to measure a gear mesh rather than an
assembled reducer, and its scope was paywalled and unread. The four-point averaging and the 2%
figure remain unsourced. See [[backlash-measurement]].

## The consequence for this repo, and it is not the expected one

The topic was open because efficiency would turn ADR-0004's static upper bound into an estimate.
It will not, and the reason is sharper than "the data is inconvenient":

**Efficiency curves describe a gearbox that is turning.** They are indexed by input speed and
published at 1,000–2,000 rpm. ClawBot's `hold` derivation is *static* — a mechanism holding a
pose has an input speed of **zero**, and there is no efficiency curve at zero speed. The
quantities that govern a stationary geartrain are starting torque and backdriving torque, which
this document publishes as separate tables of ranges.

Applying a running efficiency to a static hold would be wrong **in kind**, not merely in value.
The last open sourcing topic therefore closes by establishing that the number it would have
licensed does not apply to the computation it was wanted for.
