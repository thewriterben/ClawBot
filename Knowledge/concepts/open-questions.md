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

**Closed 2026-08-23.** OPC had no entry for the XM430, so the first record here carried no
`part_id`. One was contributed upstream and merged (OpenPartsCore#4), and this record now cites
`electronic/dynamixel-xm430-w350`. The two records sit side by side sharing **zero** fields,
which is the boundary tested rather than argued.

The residual question — whether a ClawBot record should *require* a `part_id`, or whether an
uncatalogued actuator is a legitimate state — answers itself in the negative: the XM430 was
uncatalogued for a day and the record was correct throughout. `manifest.py` already reports
uncatalogued parts separately rather than dropping them, which is the right shape.

### 4. Radians in the file (ADR-0005) protects against one bug and invites another

The `_rad` suffix plus a bounded range is the stated defence against a hand-typed `90`. Nothing has tested whether that defence holds for a value like `3` — plausibly 3 radians, plausibly a typo for 30 degrees, in range either way.

### 5. PD-5 legality gating has no ClawBot position — **unblocked, still undecided**

A mechanism repo needs one more obviously than a parts registry does.

**The reading is done.** [[project-bingo]] owns the taxonomy in `v3/specs/REFUSAL-CATEGORIES.md`
(v0.1, marked DRAFT). Legality gating is two-tier — design-time refusal at the assistants,
fabrication-time refusal at the nodes — and the spec names design-time assistants explicitly:
[[opendesigncore]], OpenCircuitCore and deployment tools. ClawBot is not named only because it
did not exist when the spec was written.

**Two of the nine categories land here.** `weapons.other` (items designed as weapons that are not
firearms; default stance refuse network-wide) and `regulated.medical` (which explicitly includes
**load-bearing prosthetics**; refuse unless a node opts in with declared certification context).
A prosthetic limb is a mechanism, and it is the most likely thing anyone would describe with this
schema that carries a category at all.

**One mechanic cuts against this repo's grain and needs deciding on purpose.** In BINGO, an asset
manifest with no `policy_categories` means `none` **as a declaration**, carrying the same fraud
consequences as misdeclaring a licence. Everywhere in ClawBot, absent means *unknown*. Both are
right in their own frame — a declaration is a claim somebody makes, an absent measurement is one
nobody took — and a ClawBot position has to say which it is adopting and why.

**Decided 2026-08-22 in ADR-0019**, and the middle question turned out to be the interesting one.

- **Does the field exist?** Yes — `policy`, optional. The argument is mechanical rather than
  moral: there is already a path from a robot record through `manifest.py` to OpenBuildCore to a
  BINGO job, and BINGO reads an absent declaration as `none` *declared*. So an undeclared
  manifest is not neutral; it makes that claim at the far end.
- **Absent means unknown, or `none`?** Neither rule loses, because they govern **different kinds
  of field**. This repo's absent-means-unknown covers *measurements* — nobody can declare a joint
  limit, you measure it or you do not. A policy category is a *statement of intent*, and the
  author always knows. So the field's nature is BINGO's; what ClawBot refuses is to **supply**
  the declaration. Absent stays undeclared and is never converted at the boundary.
- **Refuse to compute?** No. Forward kinematics is not fabrication and the mathematics is in every
  textbook; a repo declining to multiply matrices would be theatre. The refusal is at the
  **output boundary**, the same place ADR-0007 put the URDF refusal.

**One consequence found while implementing it, worth reporting upstream:** OpenBuildCore's
project schema is `additionalProperties: false` and has **no field for a policy declaration**, so
the declaration cannot travel as data through `--as-project`. It goes as prose in `description`
and is not machine-readable downstream. That is a gap in the seam, and the emitter says so rather
than smuggling it.

---

## The reading list

`raw/robotics/` was empty and so was every domain page. Six sources were ingested on 2026-08-22 and **all eight sourcing topics are now closed**. The rule that emptied the directory has not stopped applying: nothing here is built on recall, and a new page still waits for a source.

### Read but not written up — **PAID 2026-08-22**

OpenCircuitCore, ClawCam and Project BINGO were read during the opening platform survey and had
no entity pages, while the index claimed they were unread. Both halves are fixed:
[[opencircuitcore]], [[clawcam]] and [[project-bingo]] now exist.

The debt is recorded rather than deleted because the failure is worth remembering: the wiki's own
ingest rule says a source that touches pages updates them **in the same pass**, and this one did
not, across two separate sessions. An ingest that stops at "I have read it" leaves the knowledge
in commit messages, which is exactly where a wiki exists to stop it living.

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

### The type enum was swept, and three of six types cannot be recorded — **open**

Added 2026-08-23, after ADR-0023 was found the expensive way: a stepper arrived, and the schema
turned out to have accepted `stepper` since it was written while no field could hold one. That is
the fourth gap discovered by a part rather than by review, so the surface was measured instead of
waited on. `type` has six values; `data/` exercised two.

Sweeping the other four against real listings found **three more gaps in one sitting**:

| Type | Status | What has no home |
|---|---|---|
| `stepper` | **closed** by ADR-0023 | — |
| `dc-gearmotor` | **partial** | Pololu publishes a **gearbox torque limit** — *"the recommended upper limit for continuously applied loads is 4 kg·cm"* — which at 34:1 is *below* the motor's 4.7 kg·cm stall, so it binds. `gearbox` has ratio, type, backlash, efficiency, starting and backdriving torque, and no limit. It must not go in `continuous_torque_nm`: that means torque the actuator can sustain, and a geartrain limit says nothing about the motor's heating. |
| `bldc` | **open** | The iPower GM4108H-120T publishes *"load torque 1200–1800 g·cm"* at 1.5 A — a **range**, indexed by current. `torqueAtVolts` and `torqueAtAmps` both take a single value. ADR-0021 already met ranges on starting and backdriving torque; this is that shape on a different field. |
| `linear-actuator` | **closed** by ADR-0025 | Was: the word *force* did not occur in the schema. Now `stall_force_n`, `continuous_force_n` and `duty_cycle_pct` exist and wrong-family fields are refused. Four other L12 figures still have no home — back-drive force, max static force, the peak-power point, and a linear no-load speed — and the sweep found the deeper thing: **the schema is rotary-shaped throughout**, so those are one assumption rather than four gaps. |

**None of these is fixed, deliberately.** Each wants its own ADR and at least one properly-read
datasheet, and three schema changes in one day would be three decisions made in a hurry. What
changed is that they are now **visible**: `tests/test_coverage.py` fails if an enum value is
neither exercised nor declared here with a reason, and fails again if a declaration outlives its
gap. Fixtures live in `tests/fixtures/`, never `data/`, because they are questions put to the
schema rather than records of owned hardware — and every figure in one is still cited, since a
fabricated fixture would be invented data with extra steps.

**Joint types are swept the same way** and are a different problem: five of six are unexercised,
but the schema can express all six. That is a coverage gap, not an expressiveness gap, and the
pairing is worth noting — `prismatic` has no robot to use it *and* no recordable actuator to drive
it.

**The honest limit of this method.** It finds gaps where the schema promises something it cannot
deliver. It cannot find ADR-0024, where the failure was that the servo in the drawer was not the
servo on the datasheet. No enum sweep reaches that; only looking at the object does.

---

**One of the eight left a claim it could not source, and that claim was closed on 2026-08-23.** The
gearbox page recorded "backlash has no measurement standard" as trade-press hearsay and said so in
capitals in the schema. A vendor's own pages supplied the core of it primarily -- see
[[backlash-measurement]] -- and a standard with backlash in its title turned out to measure a
different quantity. The reading list did not reopen: nothing new was asked, an existing answer got
a better source. **That is the ordinary shape of wiki maintenance and is worth naming, because a
reading list that only ever empties is a reading list nobody is checking.**

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

Per [`../CLAUDE.md`](../CLAUDE.md), a lint pass should check whether `TODO(source)` markers have
been waiting long enough to chase.

**Lint run 2026-08-22.** There is **one**, in [[clawbot]]. This paragraph said three, in
[[clawbot]] and [[ecosystem-position]] — the ecosystem-position markers were removed during a
rewrite and the count was not updated, which is the ordinary way a self-describing document
goes wrong.

The surviving one is worth reading rather than chasing: its literal condition has been met and
it still stands. See [[clawbot]] for why.
