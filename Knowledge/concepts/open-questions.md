---
title: Open questions
type: concept
updated: 2026-08-22
sources:
  - ClawBot/DECISIONS.md
  - OpenDesignCore/wiki/concepts/platform-decisions.md (PD-1, PD-5)
  - Knowledge/raw/platform/llm-wiki.md
---

# Open questions

Two lists. The first is what needs **falsifying** — decisions already recorded that were made without evidence. The second is what needed **reading**, and is now empty of sourcing topics.

Ordered by how expensive the mistake gets if left alone.

---

## Decisions made without evidence

### 1. ADR-0005 chose URDF-over-DH without running a conversion — **CLOSED 2026-08-22**

Was the direct breach of [[inherited-invariants]] #8, the rule PD-1 paid for.

**Falsified as predicted, and the prediction was too optimistic about what would break.** The
guesses here were `mimic`, multiple visual/collision geometries, xacro and inertial frames — all
real, all minor. The actual failure is **absence**: `urdfdom` refuses to parse a revolute joint
with no `limit`, so ClawBot's honest "unknown travel" state has no URDF representation at all;
and on import, missing bounds silently become `0` and a missing axis silently becomes `(1,0,0)`.
The format destroys exactly the distinction this repo is built on.

Written up in [[urdf-round-trip]]; decided in ADR-0007, which retracts ADR-0005's consequences
sentence and leaves its decision standing — now supported by three arguments from
[[dh-conventions]] that ADR-0005 did not make.

### 2. Nobody has asked for ClawBot — **half closed 2026-08-22**

ADR-0001 admits the fifth repo is "justified by a data shape rather than by demand".

**The factual half is settled: [[oh-ben-claw]] has no robot model.** `obc-movement` is two files
exposing `ServoAngle { name, channel, angle }` — a flat name-and-channel-to-angle map with no
representation that channel 3 is mechanically downstream of channel 1. `obc-navigation` is 2D
mobile-base only. No link tree, no joint limit table, no kinematics. ADR-0001's second rejection
was therefore argued against a repo that had *not* solved it, which is the answer that supports
the decision. Recorded in ADR-0010, which also draws the line at which layer of control ClawBot
stops.

**Still open:** nobody has *asked*. A gap confirmed is not a request received, and the
`TODO(source)` markers saying so stay until a peer reads ClawBot data on purpose.

**New, found in the same reading:** `MovementCommand::ServoAngle` is in **degrees** while ClawBot
mandates radians. Two repos each correct in their own frame is how a mechanism gets commanded to
57 times the intended angle. ADR-0010 puts the conversion at one boundary; nothing enforces it yet.

### 3. The actuator/parts boundary is untested — **CLOSED 2026-08-22, and the split holds**

The stated split — the registry holds *what the part is*, ClawBot holds *what it does in a
mechanism* — was defensible and had never met a real entry.

It has now. [[openpartscore]] already carries `electronic/sg90`, a hobby servo. What that record
contains: id, name, description, source, and attributes `bus`, `capabilities`, `connector`,
`compatible_boards`. What it does **not** contain: **no torque, no speed, no mass, no travel, no
gearing, no feedback type.**

So the overlap in practice is *zero*. OPC answers "what is this thing and how do you talk to
it"; ClawBot answers "what does it do when you bolt it into a mechanism". The XM430 record
written the same day carries torque at three voltages, gear ratio, travel and encoder type, and
none of those fields has a home upstream.

**Two smaller findings from the same comparison:**

- A servo lives in OPC's **`electronic`** namespace, not `mechanical` — that is OPC ADR-0005
  ("accessories are electronic parts"), and it means a ClawBot `part_id` for an actuator reads
  `electronic/...`. Worth knowing before writing one.
- `bus` appears on both sides — OPC's `attributes.bus` and ClawBot's `harness.channels.bus`.
  Not yet a conflict, because they answer different questions (what the part speaks; what it is
  wired to on this machine), but it is the one field to watch.

**Still open, and now sharper:** OPC has no entry for the XM430 at all, so ClawBot's first
record carries no `part_id`. Whether ClawBot records should *require* one, or whether an
uncatalogued actuator is a legitimate state, is a real question the manifest emitter already
half-answers by reporting uncatalogued parts separately rather than dropping them.

### 4. Radians in the file (ADR-0005) protects against one bug and invites another

The `_rad` suffix plus a bounded range is the stated defence against a hand-typed `90`. Nothing has tested whether that defence holds for a value like `3` — plausibly 3 radians, plausibly a typo for 30 degrees, in range either way.

### 5. PD-5 legality gating has no ClawBot position

A mechanism repo needs one more obviously than a parts registry does. Requires reading Project BINGO's acceptance schema, which owns the taxonomy.

---

## The reading list

`raw/robotics/` was empty and so was every domain page. Six sources were ingested on 2026-08-22 and **all eight sourcing topics are now closed**. The rule that emptied the directory has not stopped applying: nothing here is built on recall, and a new page still waits for a source.

### Read but not written up — an outstanding debt

**OpenCircuitCore, ClawCam and Project BINGO were read on 2026-08-22** during the platform survey
that opened this work. None of them has an entity page, and the index still says they are
unread. That is a real gap in this wiki's own bookkeeping and is recorded here rather than
quietly corrected, because the wiki's ingest rule says a source that touches pages should update
them in the same pass.

What was learned and is currently held only in commit messages and ADRs:

- **Project BINGO** owns the PD-5 refusal taxonomy in `v3/specs/REFUSAL-CATEGORIES.md`, and two of
  its categories land directly on a mechanism repo — `weapons.other` (refuse network-wide) and
  `regulated.medical` (load-bearing prosthetics). It names design-time assistants as bound by the
  same vocabulary. This is what question 5 below needs.
- **OpenCircuitCore** is KiCad-direct with netlist-as-source, and emits provenance per build. Its
  `pcb export step|stl` is the board→enclosure path. An arm's wiring is a real constraint on its
  joint travel (ADR-0012), so the two repos touch more than expected.
- **ClawCam** is the perception peer, with a read-free / write-gated MCP approval model that
  ADR-0016 arrived at independently.

### Still on disk, not yet read

- [[oh-ben-claw]] `docs/SOTA-COMPARISON.md` — a component-by-component benchmark against ROS 2 Nav2, slam_toolbox, Cartographer, AMCL, BehaviorTree.CPP and Open-RMF. The closest thing on disk to a robotics state-of-the-art survey.
- [[oh-ben-claw]] `docs/EMBODIED-ARCHITECTURE.md`, `Knowledge Base/`.
- Oh-Ben-Claw's README past the four-control-modes table (~770 lines unread), plus `registry/`.

### Needs sourcing

No page gets written from these headings until a citable source exists behind it.
**Four of the original eight were ingested 2026-08-22** — see [`../raw/robotics/README.md`](../raw/robotics/README.md).

| Topic | Why it matters | Status |
|---|---|---|
| ~~URDF specification~~ | ADR-0005's entire basis | **done** — XSD + `urdfdom` parser → [[urdf-spec]], ADR-0007 |
| ~~DH conventions, standard vs Craig~~ | The ambiguity ADR-0005 rejects DH for | **done** — Corke 2007 → [[dh-conventions]] |
| ~~Units and frames~~ | Not on the original list, and it should have been | **done** — REP-103 → [[rep-103-units]] |
| ~~Servo thermal limits~~ | ADR-0004's whole premise | **done** — [[dynamixel-xm430]]: a good vendor names the stall/continuous distinction and publishes only stall. ADR-0004 confirmed on real evidence. |
| ~~Forward kinematics~~ | The computation ADR-0003 promises | **done** — Lynch and Park → [[forward-kinematics]]. Turned up a third representation ADR-0005 never considered; see below. |
| ~~Workspace determination~~ | Whether reach is sampled or solved — needed its own ADR | **done** — [[workspace-and-collision]] → ADR-0013. Sampled, because a sampled set is inner-bounded and under-claims. |
| ~~Self-collision~~ | Named in ADR-0003 as why computed reach over-claims | **done** — [[workspace-and-collision]]. Outcome is a *refusal*: it needs link geometry this repo does not carry, plus an allowed-collision matrix nobody has authored. The caveat can now name why. |
| ~~Gearbox efficiency and backlash~~ | Would turn an upper bound into an estimate | **done** — Harmonic Drive engineering data → [[gearbox-efficiency]], ADR-0018. It does **not** turn the bound into an estimate: efficiency curves are indexed by input speed and a static hold has none, so a running efficiency is the wrong quantity in kind. |

**All eight answered, as of 2026-08-22.** The last one was held to the end because it was the
only topic where a source would license a *number* rather than a *decision*, and it closed in the
most useful way available: by establishing that the number does not apply to the computation it
was wanted for.

Two of the eight closed as **refusals** — self-collision needs geometry this repo does not carry,
and a running efficiency does not describe a stationary geartrain. A topic answered by
establishing that the thing cannot or should not be done is a topic answered.

**The reading list is empty. That is not the same as the wiki being finished** — it means every
question written down at the start has a source behind its answer. New questions will arrive from
data, the way ADR-0014 and ADR-0018 both did: not from thinking harder, but from one datasheet
meeting one schema field.

### 6. Product of exponentials was never considered — **resolved, no change needed**

Lynch and Park teach forward kinematics via the **product of exponentials** and relegate DH to an
appendix. ADR-0005 framed its choice as DH versus a URDF tree; there was a third option on the
table and nobody looked at it.

It does not reopen the decision, for a reason worth keeping: **PoE is a computation, not a
storage format.** A screw axis is derivable from what the tree already stores. And the two frames
PoE requires are exactly the two this repo already insists on naming — a fixed base frame
(ADR-0009) and an end-effector frame (ADR-0003's tool offset). DH loses both as factorisation
residue. The representation ClawBot picked is on the right side of the distinction that matters.

Recorded because "we did not consider X" is worth writing down even when the answer is that X
would not have changed anything. See [[forward-kinematics]].

**Note the shape of that table.** Eight rows, and the schema already has fields for most of them. Fields were written from an understanding that has no sources behind it yet — which is defensible for a *shape* and would not be defensible for a *value*. The distinction is doing real work here and is worth checking again once the reading is done.

---

## Ingestion queue hygiene

Per [`../CLAUDE.md`](../CLAUDE.md), a lint pass should check whether `TODO(source)` markers have been waiting long enough to chase. As of 2026-08-22 there are three, all in [[clawbot]] and [[ecosystem-position]], all recording the same thing: nobody has asked for this repo yet.
