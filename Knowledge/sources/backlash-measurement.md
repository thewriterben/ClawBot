---
title: Backlash — two vendors mean different things by the word, and the standard named after it measures something else
type: source-summary
updated: 2026-08-23
sources:
  - Nabtesco Motion Control, "Does Zero Backlash in Gearboxes exist?" (retrieved 2026-08-23, https://www.nabtescoprecision.com/gearbox-backlash/)
  - Nabtesco, FAQ glossary — "Backlash" (retrieved 2026-08-23, https://www.nabtesco.de/en/service/faq/glossar/backlash)
  - ANSI/AGMA 2002-D19, "Tooth Thickness and Backlash Measurement of Cylindrical Involute Gearing" — title and public listing only; the standard itself is paywalled and was **not** read (https://webstore.ansi.org/standards/agma/ansiagma2002d19)
---

# Backlash — two vendors mean different things by the word, and the standard named after it measures something else

[[gearbox-efficiency]] closed the last of the eight sourcing topics, and left one claim explicitly
under-sourced: that there is no standard governing how backlash is measured, so two vendors'
figures are not comparable without their methods. That page marked it *"secondary sourcing, and
flagged as such"* and said it was *"not strong enough to build a schema rule on by itself."*
`backlash_rad`'s schema description repeats the flag in capitals.

This page is the attempt to source it properly. **It half succeeded**, and the half that succeeded
is the half that mattered.

## The core claim is now primary, and the source is a vendor describing itself

Nabtesco, on its own definition versus everyone else's:

> "Many gearbox manufacturers choose to use the standard definition of backlash, which is just
> the amount of free travel between parts"

> "Nabtesco's definition of backlash includes not only the mechanical gap between parts, but also
> takes into account the amount of angular displacement that occurs due to loading the gearbox."

And its method, stated plainly:

> "We test this on every gearbox by fixing the input side of the gearbox, then loading and
> unloading the gearbox in both directions."

From the FAQ glossary, the two figures that result:

> "The purely mechanical backlash is between 0.1 and 0.3 arc.min, which means there is no
> perceptible backlash at the gear output shaft."

> [Lost motion] "Measured at 3 % of the rated torque, it specifies how the gear behaves when
> subjected to low torques. This characteristic is also negligible in Nabtesco gears, on average
> between 0.3 and 0.6 arc.min."

**This is better evidence than the trade-press claim it replaces.** A trade article saying vendors
disagree is one step removed. A vendor saying *"many manufacturers use the standard definition;
ours is different, and here is what ours includes"* is the disagreement itself, in writing, from
one of the parties to it. The core of the original claim — that two backlash figures are not
comparable without their methods — is now primary-sourced.

Note also that the vendor publishes **two different numbers for the same shaft** (0.1–0.3 arc·min
mechanical backlash, 0.3–0.6 arc·min lost motion) which differ by which definition is applied.
The name of the field does not determine the quantity.

## The standard exists, and answers a different question

**ANSI/AGMA 2002-D19 — "Tooth Thickness and Backlash Measurement of Cylindrical Involute
Gearing."** The title alone disposes of a loose reading of "there is no standard": there is one,
and the word is in its name.

**What it appears to cover**, from its public listing: calculation procedures relating specified
tooth thickness, centre distance and tolerances to backlash in a *gear mesh*. That is backlash as
a consequence of gear geometry — not the assembled-reducer arc-minute figure a robot builder
reads off a datasheet, measured at the output shaft of a housed unit with seals, bearings, and
preload.

**Recorded honestly: the scope text was not read.** The standard is paywalled, the ANSI preview
PDF returns 403, and no verbatim scope statement was obtainable. The distinction above rests on
the title and a public abstract. It is enough to say *"a similarly-named standard exists and
appears to answer a different question"* and not enough to say *"no standard covers assembled
reducers"* — so this page says the first and refuses the second.

## What is still not sourced

The original trade-press claim had specifics beyond the core: that manufacturers commonly average
four or more points on the output shaft, and that some apply 2% of rated torque to generate the
rating while others apply less. **Neither is sourced.** Nabtesco's 3% is now primary, but a
*second* vendor's differing percentage — which is what would make "they differ" a demonstrated
fact rather than a reasonable inference from one data point — was looked for and not found in a
readable primary document.

**Conflict, unresolved:** [[gearbox-efficiency]]'s source, Harmonic Drive's FR engineering data,
would be the natural second vendor and is already in this repo's citation chain. Its PDF could
not be text-extracted with the tooling available, so whether Harmonic Drive defines lost motion
at a different percentage is **unknown, not absent**. Worth one look by a human with the PDF open.

## Consequence for the schema

**Still no rule, and the reason has changed for the better.** The `backlash_rad` note can stop
saying its basis is secondary — the incomparability is a vendor's own words now. What it must
keep saying is that this licenses no *value*: a figure whose meaning depends on the definition
applied is exactly the shape ADR-0018 and ADR-0021 already handle, and neither needs superseding.
Absent still means UNKNOWN.

No new ADR. Nothing was decided here that was not already decided; a note's evidence standing
improved, which is a wiki-and-description change, not a decision.
