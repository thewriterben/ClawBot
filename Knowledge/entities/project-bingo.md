---
title: Project BINGO
type: entity
updated: 2026-08-22
sources:
  - ProjectBINGO/README.md
  - ProjectBINGO/VISION.md
  - ProjectBINGO/v3/specs/REFUSAL-CATEGORIES.md
  - ProjectBINGO/v3/specs/NODE-AGENT.md
  - ProjectBINGO/v3/ARCHITECTURE.md
---

# Project BINGO

The settlement peer, and the one that owns two vocabularies this platform already borrows. An
open protocol for distributed manufacturing where a design's creator is paid a royalty **in the
same atomic transaction** that pays the fabricator — enforced at the point of fabrication rather
than by policy.

On 2026-08-03 it settled its first real job: a part printed on a Creality K2 Plus, with the
designer's royalty paid alongside the printer's fee. One node, real hardware.

Read on 2026-08-22, written up late — see [[open-questions]].

## The two vocabularies that reach ClawBot

**The machine record.** A machine under a node is
`{machine_id, driver, make/model, process, envelope_mm, materials[], tier}`.
[[openbuildcore]]'s `machine.schema.json` copies those field names deliberately, so a machine on
a bench and a machine offered to the network describe themselves the same way. ClawBot's
`manifest.py` emits into OBC's requirement vocabulary, so a robot's bill of made parts reaches
BINGO's tier routing without anyone translating twice.

Capability tiers run 0 (hobbyist FDM) to 3 (specialised — PCBA, tooling, sheet metal), and
**orders route to the minimum tier that satisfies the spec**. Declaring a tier is a claim about
evidence you can produce, not about equipment.

**Human labour registers exactly like a machine** — an inspector, finisher or courier is a node
with `process: "inspection" | "finishing" | "courier"` and a capability profile instead of an
envelope. Same jobs, same evidence, same settlement.

## The refusal taxonomy — what PD-5 has been waiting for

`v3/specs/REFUSAL-CATEGORIES.md` (v0.1, marked DRAFT and unreviewed) is the shared category list
platform decision PD-5 assigns to this repo. Legality gating is two-tier: **design-time refusal
at the assistants, fabrication-time refusal at the nodes**, speaking one vocabulary.

Its stated principle is narrow on purpose — the network "does not adjudicate law and does not
generate legal claims". It does three things: names a small set of commonly-restricted
categories, requires assets and orders to **declare** theirs, and lets every node refuse
categories outright.

Two of the nine categories land directly on a mechanism repo:

- **`weapons.other`** — items designed as weapons that are not firearms. Default stance: refuse
  network-wide.
- **`regulated.medical`** — implants, **load-bearing prosthetics**, anything marketed with
  medical claims. Refuse unless a node opts in with declared certification context.

A prosthetic limb is a mechanism. It is the single most likely thing somebody would describe with
ClawBot's schema that carries a policy category.

Three mechanics matter for how ClawBot would implement a position:

- **Absence is a declaration.** An asset manifest with no `policy_categories` means `none` **as a
  declaration**, with the same fraud consequences as misdeclaring a licence. That is the opposite
  of this repo's usual "absent means unknown" — and the difference is deliberate on their side,
  because a declaration is a claim someone makes rather than a measurement someone failed to take.
- **The category list is versioned by hash**, frozen into the job at order time, so a dispute
  resolves against the list as it stood. Same pattern as their frozen acceptance checklist.
- **Design-time assistants apply the same ids when declining to design** — the spec names
  [[opendesigncore]], OpenCircuitCore and deployment tools explicitly. ClawBot is not named,
  because it did not exist when the spec was written.

**ClawBot still has no PD-5 position.** That is open-question 5, and it is now unblocked: the
taxonomy has been read, the two relevant categories are identified, and the declaration mechanics
are understood. What remains is a decision, not more reading.

## What it is honest about

The README marks its own seams: **real** are the registry and royalty maths, the Ed25519
signed evidence chain cross-checked against RFC 8032, atomic to-the-cent settlement, real STL
analysis, and a driver that has printed and settled on real hardware. **Stand-ins, clearly
marked**, are the local ledger, simulated carrier confirmation, and — worth noting here — "the
perception/reach work still spec-only".

That last phrase is the closest thing in the ecosystem to a request for what ClawBot does, and it
is not one. It is BINGO describing its own unbuilt half, in its own domain. ADR-0001's admission
that nobody has asked for this repo still stands.

## Proof-of-fabrication, and why the shape is familiar

Evidence is layered and tier-scaled: signed telemetry from the machine, in-process imaging hashed
at capture time, second-party QA attestation at higher tiers, reputation staking, and staked
human arbitrators as the backstop. No single layer is trusted; the stack is designed so cheating
costs more than honest work.

The design principle underneath — *"the oracle problem is a first-class engineering target"*,
attacked with layered evidence "rather than pretending any single proof suffices" — is the same
move ClawBot makes when a reachability verdict carries five separate caveats instead of one
confident number.

Licensed MIT, unlike the Apache-2.0 Open\*Core peers.
