---
title: A stepper's rated voltage is its rated current times its phase resistance
type: source-summary
updated: 2026-08-23
sources:
  - STEPPERONLINE, 17HS19-2004S1 product listing, General Specification (retrieved 2026-08-23, https://www.omc-stepperonline.com/nema-17-bipolar-59ncm-84oz-in-2a-42x48mm-4-wires-w-1m-cable-connector-17hs19-2004s1)
  - DHM Online, 17HS19-2004S1 listing, Motor Parameters (retrieved 2026-08-23, https://www.dhm-online.com/en/nema-17/10127-17hs19-2004s1-20a-18-stepper-motor-stepperonline-nema-17-cnc-3d-print.html)
---

# A stepper's rated voltage is its rated current times its phase resistance

Read to settle one question: **what does a stepper datasheet index torque by?** The answer decided
ADR-0023, and it turned on a single line of arithmetic.

## The manufacturer's own figures

STEPPERONLINE, for the 17HS19-2004S1 (NEMA 17, 42 × 48 mm):

| | |
|---|---|
| Holding Torque | 59 Ncm (83.55 oz.in) |
| Rated Current/phase | 2.0 A |
| Phase Resistance | 1.4 ohms |
| **Voltage** | **2.8 V** |
| Inductance | 3.0 mH ±20% (1 kHz) |

> 2.0 A × 1.4 Ω = 2.8 V, exactly.

**The published "voltage" is the I·R product of the two figures beside it.** It is not an
independent specification, it carries no information the other two do not, and it is not the
supply the motor is driven from. Since phase resistance moves with temperature, it is not even a
stable number.

## A second listing omits it entirely

DHM Online lists the same motor with step angle, holding torque, rated current per phase, phase
resistance, inductance, leads and weight — **and no voltage row at all.**

Two vendors, two treatments: one computes it, one does not bother. Neither presents it as the
condition the torque figure was measured under. What *both* state is the current.

## The consequence for the schema

ClawBot's `type` enum accepted `stepper` and `bldc` from the start, while every torque row
required `at_volts`. So the only way to record this motor was to write `at_volts: 2.8` — a number
that means "rated current times winding resistance" here and "the supply voltage this figure
applies at" on the servo record two files away. One field name, two quantities, no way for a
consumer to tell which they were reading.

That is [[gearbox-efficiency]]'s lesson arriving from the other side. There, a figure without its
index was not a figure. Here, a figure with the *wrong* index is worse: it looks correct.

ADR-0023's answer is a separate current-indexed field with **no voltage on it at all**. Not
optional — absent. An optional `at_volts` would be filled in by exactly the person the rule is
meant to stop.

## What this source does not say

**Whether a holding torque is sustainable.** Neither listing states a continuous or thermal
rating, or the mounting and duty conditions the holding figure assumes. So a stepper recorded from
this datasheet has `continuous_torque_nm: null` and its capacity is underivable — the same answer
the XM430 and the MG90S get, for the same reason.

That is recorded as **not stated**, not as *unsustainable*. Steppers are commonly run at rated
current continuously, and this page does not contradict that; it simply has no source for it.
Anyone with a datasheet that gives a thermal rating and its conditions closes this, and until then
the refusal is about the evidence rather than about the physics.

**Also unread:** the manufacturer's full PDF datasheet. It is published as a vectorised drawing —
zero text operators, all line art — so no text could be extracted from it, and the specification
figures above come from the product listings rather than the PDF. If the PDF states measurement
conditions the listings omit, this page does not know it.
