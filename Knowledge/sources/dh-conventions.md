---
title: Denavit-Hartenberg — standard, modified, and what neither records
type: source-summary
updated: 2026-08-22
sources:
  - Corke, P. I., "A simple and systematic approach to assigning Denavit-Hartenberg parameters", IEEE Transactions on Robotics 23(3), 2007 (retrieved 2026-08-22, https://petercorke.com/doc/simple_systematic.pdf)
  - Hartenberg, R. S. and Denavit, J., "A kinematic notation for lower pair mechanisms based on matrices", Journal of Applied Mechanics 77, pp. 215-221, June 1955 (cited via Corke, not read)
  - Craig, J. J., "Introduction to Robotics", Addison Wesley, 1986 (cited via Corke, not read)
---

# Denavit-Hartenberg — standard, modified, and what neither records

ADR-0005 refuses DH as the stored form. This is the source behind that refusal, read after
the fact. **It supports the decision and supplies three arguments the ADR did not make.**

## The four parameters

Two describe the link: length `a_i` and twist `alpha_i`, fixing the relative location of the
two joint axes attached to it. Two describe the joint: offset `d_i` along the joint axis, and
angle `theta_i` about it. For a revolute joint `theta` varies and `d` is constant; for a
prismatic joint the reverse.

## The two conventions

The difference is **where the link frame is attached**, and it propagates into the
transformation order:

| | Frame attached to | Transform sequence |
|---|---|---|
| Standard (Denavit and Hartenberg 1955; Paul 1981) | **distal** end — origin of frame {i} on the axis of joint i+1 | Rz(theta_i), Tz(d_i), Tx(a_i), Rx(alpha_i) |
| Modified (Craig 1986) | **proximal** end | Rx(alpha_i-1), Tx(a_i-1), Rz(theta_i), Tz(d_i) |

Both are in current use. Corke's 2007 method exists precisely to emit **either**, which is
itself the evidence that neither has won.

## What ADR-0005 got right

The ADR's argument was: four columns do not record which convention they are, so the same
table describes two different mechanisms. The sources confirm the ambiguity is real, live,
and unresolved after fifty years.

## Three arguments ADR-0005 did not make

**1. The zero-angle pose is a third free variable.** Corke:

> "The kinematic zero-angle configuration of the robot is often different to the joint
> controller's zero-angle configuration, and requires that joint angle offsets be introduced."

So a DH table is under-determined by *two* facts it does not carry — the convention, and the
joint offsets. A table with a citation to a paper is a set of numbers whose meaning depends
on two facts stored somewhere else.

**2. Base and tool transforms do not fit in the table at all.** In Corke's worked examples the
base and tool transforms fall out as *residue* — terms left over after factorisation that are
not link transforms. He also notes the first and last links' parameters "are meaningless, and
are arbitrarily chosen to be 0".

This is the sharper argument for this repo, because **ADR-0003 makes the tool offset
load-bearing**: a reachability verdict is meaningless without it, so it travels in the returned
value. A notation in which the tool transform is leftover residue is a notation that
structurally cannot carry the thing ClawBot refuses to answer without.

**3. DH cannot branch.** DH describes a serial chain. A tree — a torso with two arms and a head
— has no DH table. This is now directly load-bearing, since the topology decision settles
ClawBot on trees plus coupled joints.

## Not a ban on import

ADR-0005 already permits DH as an *input* if the convention is recorded and it is converted on
the way in. That stands, and Corke's paper is the method for doing it in reverse. Note what a
faithful importer must therefore demand: the convention, **and** the joint offsets, **and** the
base and tool transforms — none of which are in the table.
