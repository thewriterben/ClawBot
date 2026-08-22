---
title: Ecosystem position
type: concept
updated: 2026-08-22
sources:
  - OpenDesignCore/wiki/concepts/ecosystem-map.md
  - OpenBuildCore/README.md
  - OpenPartsCore/README.md
  - ClawBot/DECISIONS.md (ADR-0001, ADR-0006)
---

# Ecosystem position

Where [[clawbot]] sits, and — more usefully — what it is **not** allowed to do because something else already does it.

## The five peers

| Repo | Answers |
|---|---|
| [[openpartscore]] | what a part *is* — cited reference data |
| [[openbuildcore]] | what you *have*, and what you could make of it |
| OpenCircuitCore | the electronics of the thing you decided to build — **not yet read** |
| [[opendesigncore]] | the geometry, validated and provenance-carrying |
| [[clawbot]] | the mechanism — links, joints, actuators, and what they can reach |

[[oh-ben-claw]] sits outside this set: it is the runtime that *commands* a robot, and a likely consumer.

## The seam

**The peers meet at data that already had to exist, never at an API.** [[openbuildcore]] states it directly: it imports nothing from [[opendesigncore]] and reads a provenance file instead. ClawBot ADR-0006 adopts the same rule, which is why a link is a `part_id`, a `make`, or a `provenance_ref` — three pointers, zero dependencies.

This is not stylistic. The failure it prevents is documented: three copies of [[oh-ben-claw]]'s registry drifting apart across Rust, TypeScript and Python, which is what [[openpartscore]] was created to end.

## The boundaries ClawBot must not cross

Each of these is somebody else's competence, and the discipline is to notice when a feature request is really a request to duplicate one:

- **Actuating anything** → [[oh-ben-claw]], behind Track 0. ClawBot describes; it never commands.
- **Facts about a servo** → [[openpartscore]]'s `mechanical` namespace, with citations. ClawBot stores what a part *does in a mechanism*, not what it *is*.
- **Whether you can build the robot** → [[openbuildcore]]. ClawBot emits the link manifest; OBC knows what is in the drawer.
- **Whether a bracket prints** → [[openbuildcore]]'s machine check. ClawBot's `make` links carry OBC's exact fields so the manifest needs no translation.
- **What the bracket looks like** → [[opendesigncore]]. ClawBot holds the hash.
- **Simulation, planning, trajectory optimisation** → mature implementations exist. ClawBot describes the robot they operate on.

## The gap it fills

Nothing in the ecosystem models a mechanism. [[opendesigncore]]'s own gap list names "multi-domain co-design: board outline ↔ enclosure ↔ thermal ↔ mounting as one constrained problem" — a mechanism adds a dimension to that, because a moving part's clearance requirement is a swept volume rather than a bounding box.

**That connection is speculative and unsourced.** No document read so far asks for a mechanism model. ClawBot ADR-0001 admits this plainly: the fifth repo is "justified by a data shape rather than by demand: nothing is asking for it yet". Recorded here so the honest version does not get lost the first time somebody writes a pitch.
