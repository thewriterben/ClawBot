# Decisions

Append-only. Newest at the bottom.

---

## ADR-0001 — A fifth peer, for the things that move

**Date:** 2026-08-22
**Status:** accepted (extends OpenDesignCore ADR-0007's engine-among-peers shape)

**Context.** The platform can now say what a part *is* (OpenPartsCore), what you *own* and could build from it (OpenBuildCore), what its electronics look like (OpenCircuitCore), and what its geometry is (OpenDesignCore). Nothing models a mechanism — a thing with joints, whose capability is a function of its configuration rather than a fixed property of the object.

Three homes were considered. **A new `process` token in OpenBuildCore's machine record** is the cheapest: a robot arm is a machine you own, `machines.json` already exists, and `can-print` could gain a `can-reach` sibling. **A crate inside Oh-Ben-Claw**, which already commands physical robots and has the world memory and safety gate to do it. **Its own peer.**

**Decision.** Its own repo, the fifth Open\*Core-shaped peer.

Folding it into OBC's machine record fails on the shape of the data, not on taste. OBC answers "can this part be made" with `envelope_mm: {x, y, z}` and an axis-aligned containment test in six orientations (its ADR-0005). That model is correct for a printer and structurally wrong for an arm:

1. **The reachable set is not a box.** For any serial mechanism past two joints it is non-convex, frequently has a hole at the base where the arm cannot fold into itself, and can be disconnected across configuration branches. Every box you could pick either claims points it cannot reach or disclaims points it can. There is no conservative choice — under-claiming makes a robot look incapable, over-claiming sends someone to the bench with a part that never gets picked up.
2. **Capability varies within the workspace.** A printer's material list does not change when the gantry moves. An arm's usable payload falls as it extends, because shoulder torque is force times moment arm. OBC's model has no place to put a capability that is a function of position, and adding one would distort the machine record for every non-robot that uses it.
3. **A robot is on both sides of the platform's own split.** PD-2 separates cited reference data from mutable user state, and OBC's ADR-0001 made that separation structural. A robot design is shareable, reviewable and citable — reference data. A robot on your bench is owned state. A robot you are partway through building is an OBC *project*. It is all three, and a machine record can only be the second.

Putting it in Oh-Ben-Claw fails differently: that repo's competence is commanding a robot in real time behind a safety gate, and it needs a robot *model* to do it well. A model that lives inside the runtime is a model no other consumer can read without taking the runtime as a dependency — the registry-drift problem PD-2 exists to prevent, recreated one layer up.

**Consequences.** A fifth repo is a real maintenance cost, and the honest accounting is that this one is justified by a data shape rather than by demand: nothing is asking for it yet. Set against that, the alternative is a `robot` shoehorned into a `machine` that will be wrong in the specific way described above, discovered later, and expensive to unpick once three repos read the field.

Oh-Ben-Claw becomes a consumer rather than an owner. That is the right direction — it already treats its hardware registry as something it reads.

---

## ADR-0002 — Apache-2.0

**Date:** 2026-08-22
**Status:** accepted (PD-4)

Uniform with OpenDesignCore, OpenPartsCore, OpenCircuitCore and OpenBuildCore. The older ecosystem repos (Oh-Ben-Claw, ClawCam) stay MIT; nothing here links them.

---

## ADR-0003 — Reach is derived, never declared

**Date:** 2026-08-22
**Status:** accepted

**Context.** Every robot vendor publishes a reach figure. It is the single most useful-looking number in the datasheet and it is not usable as a specification, for reasons that compound:

- It is a **radius to an unstated frame** — sometimes the tool flange, sometimes the wrist centre, sometimes a nominal TCP. The three differ by the length of a wrist.
- It is measured **without a tool**. The gripper you bolt on changes it, and changes it anisotropically.
- It describes a **sphere the arm cannot fill**. Joint limits carve pieces out of it; the arm cannot fold tightly enough to reach near its own base; self-collision removes more.
- It says nothing about **orientation**. A point reachable with the tool pointing down may be unreachable pointing sideways, and "reach" collapses that distinction entirely.

The tempting design is to carry the vendor figure in a `reach_mm` field, cited to the datasheet, and let consumers interpret it. The citation makes it *look* like the platform's discipline is satisfied. It is not: the citation proves the vendor said it, which was never in doubt. What matters is what the number means, and it means four different things depending on who reads it.

**Decision.** There is no `reach_mm` field, and there will not be one.

- Reachability is answered by **computing it from the joint model** — link transforms, joint types, joint limits, and the declared tool offset.
- A model too incomplete to compute against answers **"incomplete"** and **names the joint that is missing its limits**, in the same way OpenBuildCore's unsourced throughput answers "requires slicing" rather than guessing (its ADR-0005).
- A vendor reach figure may be recorded in `note` as prose. It never enters a computation, and it is never a field a consumer could mistake for a derived answer.
- A reachability verdict carries the **tool offset it assumed**, because the answer is meaningless without it — the same reason OBC's shopping list carries its sequential/simultaneous basis (its ADR-0004).

**Consequences.** ClawBot will refuse to answer questions about a robot somebody described in three fields, which is more friction than a `reach_mm` field would have been. That friction is the point: the fields it demands instead are the ones that make the answer true.

Self-collision is **not** modelled at this stage, so computed reach will be optimistic — it will claim points the arm cannot occupy without hitting itself. This is the wrong direction to be wrong in, and it is stated here rather than buried, because it is the opposite of the conservative error OBC accepted in axis-aligned-only fit. Until self-collision exists, a reachability answer must say that it is a joint-limit result and not a collision result. Whoever implements this should treat the caveat as travelling in the returned value, not in documentation.

---

## ADR-0004 — Payload is a function of pose, and an unposed payload figure is refused

**Date:** 2026-08-22
**Status:** accepted (completes ADR-0003)

**Context.** The same failure as reach, one step worse, because the error is silent and lands on hardware. Rated payload falls with extension: the load torque at the shoulder is the payload's weight times its horizontal distance from the joint. A figure quoted at a tucked pose can overstate capacity at full extension by a large factor, and the failure mode is not a wrong answer on a screen — it is a stalled joint, a dropped workpiece, or a servo cooking itself trying to hold a position it cannot hold.

There is a second trap inside the actuator data. A hobby servo's headline number is **stall torque**: what it produces at the instant it stops moving, at a stated voltage, drawing a current it cannot sustain. Continuous safe torque is a fraction of it. A model that reads stall torque as capacity will confidently specify a mechanism that overheats.

**Decision.**

- No scalar `payload_kg` on a robot record.
- Capacity is **derived** from actuator effort limits and the geometry, and reported **per-pose**. The pose is part of the answer, not context the caller is expected to remember.
- A measured figure is accepted only as `measured_payload`, which **requires** the pose it was measured at and a `how_measured`. The same shape as OBC's `measured_throughput`, and for the same reason: an unsourced figure is indistinguishable from a recalled one.
- Actuator records distinguish `stall_torque_nm` from `continuous_torque_nm`. **Only the continuous figure feeds a capacity derivation.** Stall torque is recorded because datasheets publish it and omitting it invites someone to write it into the wrong field, not because it is usable.
- A derived capacity is labelled a **static** result — gravity load at a held pose. Acceleration, dynamic loading and gearbox efficiency are not modelled, so the figure is an upper bound, and the label travels with it.

**Consequences.** Most robots described here will not have a payload answer, because most actuator datasheets publish stall torque and nothing else. That is a true statement about the available evidence rather than a gap in the model, and the fix is a path a user can walk: measure the thing, record the pose, record the method.

Deriving an upper bound and calling it one is a deliberate line. The alternative — refusing any figure until dynamics are modelled — was rejected because a static gravity bound is genuinely load-bearing for the "can this arm hold that thing still" question, which is most of them. The line is that the bound must never be printed without the word that makes it a bound.

---

## ADR-0005 — A link/joint tree, not DH parameters; radians in the file

**Date:** 2026-08-22
**Status:** accepted

**Context.** A serial mechanism's kinematics can be written as a Denavit–Hartenberg table — four numbers per joint — or as an explicit tree of links joined by transforms, which is what URDF does. DH is far more compact and is the notation the textbooks use.

DH is also **ambiguous in exactly the way this platform refuses**. Two conventions are in common circulation — the original Denavit–Hartenberg assignment and Craig's modified form — and they differ in which link frame the parameters are attached to. The same four columns describe two different mechanisms depending on a convention that the table itself does not record. A DH table with a citation to a paper is a set of numbers whose meaning depends on a fact stored somewhere else, which is the general shape of every provenance failure in this platform.

**Decision.** Links and joints as an explicit tree: each joint names its parent and child link and carries an `origin` transform (translation and rotation) and an `axis`. Structurally URDF, so a converter is a mapping rather than a reinterpretation.

- **Angles are radians**, fields suffixed `_rad`. Lengths stay millimetres suffixed `_mm`, per OpenPartsCore's rule and OpenDesignCore ADR-0004.
- Degrees may appear in **rendered output for humans**. They never appear in a file.

**Consequences.** Files are more verbose than a DH table and hand-authoring is less pleasant. Radians in particular are hostile to hand-authoring — `1.5708` is not a number anyone recognises as a right angle, and a hand-typed `90` in a `_rad` field is a plausible mistake. Two things mitigate it: the `_rad` suffix makes the unit local to the field rather than a document-level convention, and joint limits are bounded, so a schema range check catches the classic error where a value that should be under 2π arrives in the hundreds. Whoever implements validation should make sure that check exists — it is the main defence this decision leaves standing.

DH is not forbidden as an *input*. Importing a published DH table is legitimate if the convention is recorded alongside it and it is converted on the way in. What is forbidden is DH as the stored form.

---

## ADR-0006 — A link is a bought part, a made part, or a provenance record — the peers meet at data

**Date:** 2026-08-22
**Status:** accepted

**Context.** A robot is mostly parts, and the platform already has strong opinions about parts. OpenPartsCore holds cited facts about things you can buy. OpenBuildCore's third requirement kind (its ADR-0006) covers things you fabricate, carrying a size and a material, judged against machines you own. OpenDesignCore emits a provenance record with a real bounding box and volume for geometry that has actually been designed.

The question is what a `link` points at. The wrong answer is an API: ClawBot importing OBC to ask whether a bracket is makeable, or importing OPC to resolve a part id. OpenBuildCore already settled the general form of this — it reads OpenDesignCore's provenance file and imports nothing (its README, "the peers meet at the provenance record, not at an API").

**Decision.** A link is exactly one of three kinds, mirroring OBC's requirement kinds so the two vocabularies do not diverge:

- **`part_id`** — a part from OpenPartsCore. ClawBot stores the id and does not resolve it; a consumer that needs the mass reads the registry.
- **`make`** — something fabricated, carrying `size_mm` and `material`, the same fields OBC's `make` requirement carries, so a robot's bill of made parts can be handed to OBC's machine check without translation.
- **`provenance_ref`** — an OpenDesignCore artifact hash. The strongest form: the geometry exists, and its bounding box and volume are facts rather than intent.

`make` and `provenance_ref` are the same distinction OBC drew between a project's declared `size_mm` and `can-print --from-sidecar`: the first is what you check before you have a design, the second is what you check after.

**Consequences.** ClawBot's dependency list stays empty and its records stay readable by anything. The cost is that ClawBot alone cannot tell you whether a robot is buildable — it can only emit the list that OBC answers that question about. That division is correct: ClawBot knows what the robot is made of, OBC knows what you have.

Three kinds is the ceiling, for the reason OBC gave. A fourth — salvaged from an existing mechanism, say — needs a real case and its own ADR.

---

## ADR-0007 — The URDF boundary: structure survives the round trip, absence does not

**Date:** 2026-08-22
**Status:** accepted (amends the consequences of ADR-0005; does not disturb its decision)

**Context.** ADR-0005 justified a URDF-shaped tree with a claim about a converter nobody had
written: *"structurally URDF, so a converter is a mapping rather than a reinterpretation."*
[`Knowledge/concepts/inherited-invariants.md`](Knowledge/concepts/inherited-invariants.md) #8
recorded that as a breach the day it was made — kernel choices get installed and run before
they are recorded, and this one had not been run. It was question 1 in the open-questions
list.

The sources have now been read: the `urdfdom` XSD, the reference parser's `joint.cpp`, and
REP-103. The findings are written up in
[`Knowledge/concepts/urdf-round-trip.md`](Knowledge/concepts/urdf-round-trip.md). Two of them
bite.

**Export.** `urdfdom` **refuses to parse a revolute or prismatic joint with no `limit`
element**, and within a `limit`, a missing `effort` or `velocity` is fatal. So a ClawBot record
in precisely the state ADR-0003 exists to handle — a real mechanism whose joint travel nobody
has sourced — has **no valid URDF representation at all**. The format cannot say "unknown".

**Import.** The mirror, and worse because it is silent. Inside a `limit`, missing `lower` and
`upper` default to `0` with a debug log; a joint with no `axis` defaults to `(1, 0, 0)`. So
`<limit effort="10" velocity="1"/>` parses cleanly into a joint **locked at zero**, and nothing
in the parsed tree distinguishes that from a joint somebody deliberately locked. URDF's
defaults turn absence into a specific plausible value, which is
[inherited invariant #3](Knowledge/concepts/inherited-invariants.md) inverted, sitting inside
the interchange format this repo chose.

**Decision.** The converter is a boundary with an explicit absence rule in each direction, not
a mapping.

- **Export refuses rather than defaults.** A robot with any joint whose `limits` are null does
  not export; the failure names the joint. Emitting `lower="0" upper="0"` was considered and
  rejected — it manufactures a physical claim, which is the one thing this repo may never do.
  Emitting a wide default was rejected for over-claiming in the direction ADR-0003 already
  regrets. **URDF export is therefore partial by construction:** a fully-sourced robot exports,
  an honest incomplete one does not, and that is the correct asymmetry.
- **Import reads the XML, not the parsed tree.** The parse is where absence is destroyed, so an
  importer built on `urdf_parser` cannot be correct no matter how carefully it is written. An
  attribute not present in the document imports as absent.
- **A value the format defaulted is recorded as such.** Where an import must fill something in
  to proceed, `source.citation` says the format supplied it — not the author. A defaulted axis
  is a guess, and it is labelled one.
- **Lengths convert at exactly one boundary.** REP-103 fixes URDF at metres; ClawBot is
  millimetres by inheritance. One factor of 1000, one place, per OpenDesignCore ADR-0004's
  own rule.

**Consequences.** ADR-0005's decision stands and its argument is now *stronger* than when it
was written — see [`Knowledge/sources/dh-conventions.md`](Knowledge/sources/dh-conventions.md),
which supplies three arguments against DH that ADR-0005 did not make, including the one that
matters most here: a DH table cannot carry the tool transform, which ADR-0003 makes
load-bearing.

What is retracted is the *consequences* sentence. "A mapping rather than a reinterpretation"
was too strong. The honest form: structure maps both ways, absence maps neither, and each
direction needs a rule it does not get for free.

The breach against invariant #8 is closed. It cost a day, which is the going rate — PD-1 cost
four hours. The lesson repeats because the temptation repeats: a claim about a converter is
cheap to write and expensive to leave unchecked.

---

## ADR-0008 — Trees branch, and a coupled joint is a `mimic`

**Date:** 2026-08-22
**Status:** accepted (amends ADR-0005's `kind` enum)

**Context.** `robot.schema.json` contradicts itself. The `kind` enum says "Open serial chains
only. Delta arms, four-bar linkages and differentials are closed chains that the tree in
ADR-0005 cannot express." The `joints` field says "the graph must be a tree rooted at
base_link, which a validator checks." **A tree branches; a serial chain does not.** Both
sentences were written the same day and only one can be enforced.

The contradiction hid a real question. Three mechanism shapes were being lumped together:

1. **A branching tree** — a torso carrying two arms and a head, a pan-tilt with two payloads,
   a gripper with two independently driven fingers. Still a tree. FK is still a walk.
2. **A coupled tree** — a parallel-jaw gripper where one actuator drives both jaws, a
   differential wrist, a linkage where one joint's value is a fixed function of another's.
   Kinematically constrained, but the *graph* is still a tree.
3. **A true closed loop** — a delta arm, a four-bar, a Stewart platform. The graph has a cycle,
   and FK stops being a walk and becomes a constraint solve.

ADR-0005 refused all three by refusing the third. URDF distinguishes 2 from 3 with a single
element: `mimic`, carrying `joint`, `multiplier` and `offset`
([`Knowledge/sources/urdf-spec.md`](Knowledge/sources/urdf-spec.md)).

**Decision.** Trees, including branching ones, and coupled joints via `mimic`. Loops stay
refused.

- The `joints` tree rule is the correct one and it stands. The `kind` enum's "open serial
  chains only" is **withdrawn** — it described a restriction the schema never enforced.
- `kind` remains as a *label* for what sort of mechanism this is, not as a topology constraint.
  The two were conflated and are now separate.
- A joint may carry `mimic: { joint, multiplier, offset }`, meaning its value is
  `multiplier * other + offset`. A mimicking joint is **not independently commandable**, and a
  reachability computation must not sample it as a free axis — which is the whole reason it has
  to be in the model rather than left as prose.
- A `mimic` cycle is a validation error. So is a `mimic` pointing at a joint that does not
  exist, or at a `fixed` joint.

**Consequences.** The cheap 80% of "closed chains" is now expressible and the expensive 20% is
still refused, which is a better line than refusing both. A parallel gripper — the single most
common mechanism anyone would try to describe with this schema — was previously inexpressible
for a reason that turned out to be about loops it does not have.

True loops remain out, and the ROADMAP entry stays. When one arrives it needs its own ADR, and
it is a representation change rather than a field: `mimic` is a fixed function of one other
joint, and a delta arm is a simultaneous constraint over several. Conflating them later would
be worse than refusing them now.

Rejected: adding a `closed_chain` boolean to signal "this record is an approximation of a loop".
A flag that says the data is wrong is not better than refusing the data.

---

## ADR-0009 — Six joint types, and reach is relative to `base_link`

**Date:** 2026-08-22
**Status:** accepted (amends ADR-0005's joint enum; extends ADR-0003)

**Context.** ClawBot's joint enum carries four types. URDF's carries six: the four, plus
`floating` (six degrees of freedom) and `planar` (motion in a plane). The ROADMAP files mobile
bases under "Not yet", and `base_link` is documented as "assumed fixed to the world".

So "structurally URDF" was already false by omission before anyone asked for a rover. That is
worth separating from the question of whether rovers are wanted, because it means the enum was
short for a reason nobody had written down.

The reason mobile bases *looked* hard is a conflation. A moving base seems to break reachability
— if the robot can drive, what does "can it reach that point" even mean? But that is only true
if reach is expressed in world coordinates, and **ADR-0003 already refuses to express it that
way**. Reach is computed from the joint model and the declared tool offset. Every transform in a
robot record is relative to `base_link`. None of that needs the base to be anywhere in
particular.

**Decision.** Adopt URDF's full six-type enum, and state explicitly what was previously assumed.

- `floating` and `planar` join the joint type enum.
- **Every reachability and capacity answer is relative to `base_link`, and says so in the
  value.** This was already true and undocumented; it is now a declared property, carried the
  same way ADR-0003 makes the verdict carry its tool offset.
- ClawBot **does not model where the base is.** A world pose comes from a localization stack,
  which is Oh-Ben-Claw's competence
  ([`Knowledge/concepts/ecosystem-position.md`](Knowledge/concepts/ecosystem-position.md)). A
  ClawBot answer that claimed world coordinates would be asserting a pose it has no source for
  — invariant #1, in a new costume.
- A `floating` or `planar` joint has **no meaningful `limits`**, and a validator must not demand
  them. Its travel is bounded by an environment, not by the mechanism, and ClawBot does not model
  environments.
- Gravity direction is **not** derivable for a non-fixed base. A static capacity derivation
  (ADR-0004) needs to know which way is down; with a floating base that is a function of the
  base's orientation, which is unknown here. Such a derivation must either take a declared base
  orientation as an input and report it, or answer "incomplete". It may not assume z-up.

**Consequences.** A mobile manipulator is describable, and the description is honest about what
it does not know. This is a smaller change than "support robotic vehicles" sounds like, because
it adds expressiveness without adding a localization story — and the localization story is the
part ClawBot has no business owning.

The gravity consequence is the sharp one and it will be unpopular: an arm on a rover gets a
capacity answer only if somebody says which way the rover is tilted. That is correct. The
alternative is a capacity figure that is silently a flat-ground figure, which is exactly the
"true at one configuration, wrong everywhere else" failure ADR-0004 removed `payload_kg` to
prevent, reintroduced through the base instead of the pose.

Wheels, propellers, odometry and gait are **not** in scope. A `planar` base joint says the base
moves in a plane. It does not say how, and this repo does not model how.

---

## ADR-0010 — ClawBot owns the body contract; the loop stays in Oh-Ben-Claw

**Date:** 2026-08-22
**Status:** accepted (extends ADR-0001; does not reverse it)

**Context.** ADR-0001 rejected putting a mechanism model inside Oh-Ben-Claw, on the grounds
that a model living in a runtime is a model no other consumer can read without taking the
runtime as a dependency. The obvious follow-on question — whether the reverse should happen,
and ClawBot should grow the control layer — was never asked.

Reading Oh-Ben-Claw settles the factual half. **It has no robot model.** `obc-movement` is two
files exposing `MovementCommand::ServoAngle { name, channel, angle }` — a flat map from a name
and a channel number to an angle, with no representation of the fact that channel 3 is
mechanically downstream of channel 1. `obc-navigation` is a 2D mobile-base localization,
mapping and planning column. There is no link tree, no joint limit table, no kinematics.

So ADR-0001's second rejection was argued against a repo that had not solved this, and the
gap is real rather than assumed. That removes the argument for folding ClawBot into
Oh-Ben-Claw. It does not, by itself, answer how far the other way to go.

The line has to be drawn somewhere, because "control" is not one thing. Four layers were
considered:

1. **The body model** — links, joints, limits, actuators. Already ClawBot's.
2. **Derivations over it** — forward kinematics, the reachable set, static capacity. Already
   promised by ADR-0003 and ADR-0004.
3. **A control contract** — the bounds and rates a controller must respect, and a verdict on
   whether this body can do a named thing at all.
4. **The loop** — inverse kinematics, trajectory generation, servo updates, actuation.

**Decision.** ClawBot owns 1 through 3. Layer 4 stays in Oh-Ben-Claw, behind Track 0.

The dividing line is not "how much control" but **what the answer is derived from**. Layers 1-3
are functions of cited hardware data and geometry: the same inputs always give the same answer,
and every answer can name the citation it rests on. Layer 4 is a function of the world right
now — where the target is, what the sensors say, what the operator approved. Those are
different kinds of claim, and the platform already separates them everywhere else. It is the
same split as OpenBuildCore's `can-print`: OBC decides whether the geometry fits the machine;
AdvancedStudio runs the print.

Concretely, ClawBot adds:

- **Control-relevant bounds as first-class, cited data.** Joint travel, effort and velocity
  limits already exist in the schema. What is new is that they are declared as *the* source for
  a controller's limits, so a bound enforced on hardware traces to a datasheet rather than to a
  config file somebody typed.
- **An affordance verdict.** Given a robot and a named request, ClawBot answers whether this
  body can do it, or answers "incomplete" and names the missing input. This is the
  can-it-actually-happen half of the SayCan pattern, and it is genuinely ClawBot's: the question
  is a function of the body, not of the world. The difference from a learned affordance model is
  that this one is *derived and cited*, so it can say why it said no.

And ClawBot still never:

- commands an actuator, or emits anything a device could execute directly;
- solves inverse kinematics, plans a trajectory, or optimises one;
- knows where anything in the world is, including itself (ADR-0009).

**Consequences.** Oh-Ben-Claw becomes a consumer of a model it currently lacks, which is what
ADR-0001 predicted, and the direction of the dependency stays correct — data flows out of
ClawBot, nothing flows in. The peers meet at data (ADR-0006) and this is one more instance of
it, not an exception.

**One seam is now visible and must be resolved at the boundary, not in the middle.**
`MovementCommand::ServoAngle` is in **degrees**; ClawBot mandates radians in the file
(ADR-0005), and REP-103 puts URDF in radians too. The conversion belongs at exactly one place
in whatever consumes ClawBot data, the same rule ADR-0007 applies to millimetres. Recorded here
because a degrees/radians seam between two repos that both believe they are right is the classic
way a mechanism ends up commanded to 57 times the intended angle.

Rejected: emitting a Track 0 limit table directly, in Oh-Ben-Claw's own config format. It was
tempting — the limits are right here and cited, and Track 0's are typed by hand. But a
ClawBot that writes another repo's config file has taken that repo's format as a dependency,
which is the coupling ADR-0006 exists to prevent. ClawBot publishes the limits as its own data
and Oh-Ben-Claw reads them. If that proves too much friction, it is Oh-Ben-Claw's importer to
write, and its ADR to record.

Rejected: a learned policy surface — action-space definitions, simulation export, dataset
schemas. Not because it is wrong, but because it is a second product rather than a schema
change, and nothing in the repo is built yet. It goes on the ROADMAP under "Not yet", where a
real request can pull it forward.

---

## ADR-0011 — An assembly is a graph of steps, and build time is never modelled

**Date:** 2026-08-22
**Status:** accepted

**Context.** A robot record says what a mechanism *is*. Nothing said what somebody has to *do*
to end up holding one, and the gap is not cosmetic: the difference between a described robot
and a built robot is a pile of fasteners, an order to install them in, and a handful of steps
that cannot be undone.

Three things had to be decided.

**Shape.** A numbered list is the obvious form and it destroys information. "These two
sub-assemblies can be built in either order" and "this one must come first" are different facts,
and a list can only express the second. Anyone reading a list has to guess which constraints are
real, and the guesses that matter are the ones about steps that cannot be reversed.

**Time.** The temptation is a `build_time_minutes` field, or worse, a per-step estimate summed
into a total. OpenBuildCore settled the general case for print time in its ADR-0005: a modelled
estimate "is wrong by factors rather than percentages ... and once printed it will be read as a
measurement." Assembly is worse than printing, because the dominant variable is the builder. An
author assembling their own design for the fifth time and a stranger doing it for the first are
not the same measurement with noise; they are different quantities.

**Torque.** A fastener torque is a physical claim about hardware, exactly like a joint limit, and
its failure mode is sharper than most: a stripped heat-set insert in a printed part is
unrecoverable, and it is the single most common way a first build is damaged. The convention in
hobby documentation is to say nothing, and "nothing" is read as "hand tight", which is a number
somebody invented at the bench.

**Decision.**

- Steps form a **DAG**, each naming its `depends_on`. A cycle is a validation error. Two steps
  with the same dependencies are genuinely order-free and the file says so.
- **No `build_time` field.** Only `measured_build_time`, requiring `how_measured` and carrying
  `builder_experience`, because the author of an assembly is simultaneously the fastest possible
  builder and the least representative one. Absent means the answer is that it requires building
  one — the same shape as OBC answering "requires slicing".
- **`torque_nm` is citation-gated and absent means UNKNOWN.** Not hand tight, not snug. Most
  hobby assemblies will carry null, and that is a true statement about the evidence.
- **`irreversible` is a declared boolean.** A press fit, a cut, a heat-set insert, a permanent
  adhesive. No downstream tool can infer it, and declaring it is what allows a warning *before*
  the step rather than a discovery after it.
- **`verify` is prose per step**, because a step whose failure only becomes visible three steps
  later is the expensive kind, and naming the check is cheap.

**Consequences.** Assembly records will be laborious to write and mostly full of nulls where
torque should be. That is the same friction ADR-0003 accepted for reach: the fields it demands
are the ones that make the answer true, and a null torque at least announces itself.

A DAG is harder to render than a list. Rendering a linearisation for a human is fine and
expected — what is refused is *storing* the linearisation, because that is where the
distinction between "must" and "may" is lost.

Rejected: per-step time estimates, even marked as estimates. Summing guesses produces a total
that looks more precise than any of its inputs, which is how a guess acquires authority.

Rejected: modelling fastener torque from thread size and material. The relationship exists in
engineering literature, but for a heat-set insert in a 3D-printed part it depends on the insert,
the boss geometry, the material, the infill and the installation temperature — a derivation with
five unsourced inputs is five guesses wearing one citation.

---

## ADR-0012 — A cable that crosses a joint is a joint limit

**Date:** 2026-08-22
**Status:** accepted (narrows ADR-0003)

**Context.** ADR-0003 computes reachability from link transforms, joint types and joint limits,
and admits one known optimism: self-collision is not modelled, so computed reach claims points
the arm cannot occupy without hitting itself.

There is a second source of the same optimism and it was not written down. **The wiring is part
of the mechanism.** A servo cable running from a wrist back to a controller in the base crosses
every joint between them, and unless somebody left enough slack, it binds before the joint
does. The mechanism's real travel is the tighter of what the hardware permits and what the
harness permits — and the second number lives nowhere in the robot record.

This is not a rare edge case. It is the normal state of a first build, it is discovered by
either a snagged cable or a torn-out connector, and it is invisible to every model that treats
wiring as an implementation detail. It is also the reason a mechanism that worked on the bench
stops working once it is tidied.

The neighbouring temptation is to *compute* it: take a declared service loop, a cable bend
radius, and the joint geometry, and derive permitted travel. That derivation needs cable
mechanics — bend radius under load, torsion, how a bundle behaves differently from a strand —
none of which this repo has sources for, and all of which would produce a plausible number.

**Decision.** The harness may narrow a joint's travel, and it may only do so with a figure
somebody established.

- A `run` declares which joints it `crosses`.
- `permits_full_travel` is a tri-state and **null means nobody checked** — the common case, and
  it must never be read as true.
- `travel_limit` carries the narrower bound **and requires `how_determined`**, the same gate as
  `measured_payload` and for the same reason.
- A reachability computation takes **the tightest of** the joint's own limits, the actuator's
  travel, and any harness limit — and **names which one bound**, because "this arm cannot reach
  that" and "this arm's wiring cannot reach that" have different fixes and only one of them
  requires a new servo.
- `service_loop_mm` is recorded and **feeds no derivation**, exactly as `gearbox.efficiency` is
  recorded and unused. The number is there for when the mechanics are sourced.

**Consequences.** A reachability verdict now has a third caveat to carry alongside the tool
offset and the self-collision warning: whether the harness was checked. A robot with no harness
record, or one with `permits_full_travel: null`, gets an answer that says so.

This makes ClawBot's optimism *legible* rather than fixing it. Both known over-claims —
self-collision and wiring — are now named in the returned value instead of in documentation,
which is inherited invariant #4 and the only honest position available while neither is
modelled.

There is a real cost: three sources of truth for one joint's travel — the joint's `limits`, the
actuator's `travel`, and the harness's `travel_limit`. Three places to disagree. The mitigation
is that they are *different claims* rather than duplicates — what the mechanism permits, what
the motor can do, what the wiring allows — and collapsing them into one field would lose which
is which, which is precisely the fix a caller needs.

**Also settled here, quietly:** the channel map. ADR-0010 said ClawBot publishes a control
contract and never commands. `harness.channels` is that contract — joint to physical output,
plus `inverted` and `zero_offset_rad`. Both of those are facts about how the thing was
physically built that no amount of modelling recovers, and `inverted` is the most common reason
a correct model drives a mechanism into its own end stop.

---

## ADR-0013 — Reachability is sampled, and "not reachable" is not a claim

**Date:** 2026-08-22
**Status:** accepted (implements ADR-0003; the ROADMAP flagged this as needing its own ADR)

**Context.** ADR-0003 says reach is computed from the joint model rather than declared, and
left open *how*. The literature splits the question three ways — analytic, graphic, numerical —
with the numerical family covering grid, Monte Carlo and interval analysis
([`Knowledge/sources/workspace-and-collision.md`](Knowledge/sources/workspace-and-collision.md)).

Analytic workspace boundaries exist for specific mechanism families and are reported as having
"great complexity and poor visibility". They also do not generalise: a new mechanism means new
mathematics, which is a poor fit for a repo whose whole point is describing mechanisms nobody
anticipated. Interval analysis is rigorous and is a research programme, not a script.

That leaves sampling, and sampling has a property the surveys do not lead with but which
decides this for ClawBot.

**A sampled workspace is inner-bounded.** Every point it reports is genuinely reachable,
because a point only enters the set after forward kinematics put the tool there. Its errors are
all false *negatives* — points the mechanism can reach that no sample happened to hit.

This is the direction this repo is allowed to be wrong in. ADR-0003 already records that
computed reach **over**-claims by ignoring self-collision, and names that as the opposite of the
conservative error OpenBuildCore accepted for axis-aligned fit. Sampling errs the other way. It
does not cancel the self-collision problem — they are different points — but it does mean the
method is not adding to it.

**Decision.** Reachability is answered by sampling the joint space, and the two directions of
the answer are not symmetric.

- **"Reachable" is a claim.** A sample reached it. It carries the pose that got there.
- **"Not reachable" is never a claim.** The honest phrasing is *"no sample reached it in N
  samples"*, and N travels in the value. A caller that wants a stronger negative needs a
  different method, and this repo does not have one.
- **Sampling is deterministic.** A declared integer seed, recorded in the verdict, so the same
  robot and the same seed give the same answer. This is OpenDesignCore's determinism discipline
  (its ADR-0003) applied to a stochastic method: randomness is fine, *unrecorded* randomness is
  not.
- **Joint limit extremes are always sampled**, in addition to the random draw. The interesting
  parts of a workspace are at the limits, and a uniform sample reaches a corner of an n-joint
  space with probability approaching zero.
- **A joint with unknown limits stops the computation.** The verdict is "incomplete", naming the
  joint, per ADR-0003. It is not sampled over an assumed range.
- **A `mimic` joint is not a free axis.** It is evaluated from the joint it follows (ADR-0008).
  Sampling it independently would report poses the mechanism cannot hold.

**Every verdict carries its assumptions in the value**, not in documentation — inherited
invariant #4. That is five things, and all five are load-bearing:

| Carried | Because |
|---|---|
| the tool offset assumed | ADR-0003: the answer is meaningless without it |
| the base frame | ADR-0009: it is never a world claim |
| sample count and seed | the negative answer means nothing without N; the seed makes it reproducible |
| "joint-limit result, not a collision result" | self-collision is not modelled and the reach over-claims |
| whether the harness was checked | ADR-0012: an unchecked cable run is a second over-claim |

**Consequences.** Reachability answers get verbose, and the verbosity is the product. A bare
"yes" from this system would be indistinguishable from a vendor's reach figure, which is the
thing ADR-0003 exists to refuse.

Cost accepted: sampling scales badly in the number of joints. Coverage of an n-dimensional
joint space by N samples thins as n grows, so the same N that is generous for a pan-tilt is
sparse for a six-axis arm. The mitigation is that N is in the answer, so a thin result announces
itself rather than looking like a thorough one.

Rejected: reporting a workspace **volume**. It is the number everyone wants and it is a
boundary claim in disguise — a volume computed from an inner-bounded sample understates by an
unknown amount, and printed as a single figure it will be read as measured. If it is ever added
it must carry N and be labelled a lower bound.

Rejected: bounding-box broad-phase self-collision using `make` link sizes. It would flag
adjacent links constantly — they share a joint — and its silence would be indistinguishable
from real clearance. A collision check that cannot tell "clear" from "not checked" is worse than
none, because the first is a claim.

---

## ADR-0014 — A torque figure is a curve sampled at voltages, and the derivation must say which sample it used

**Date:** 2026-08-22
**Status:** accepted (refines ADR-0004; found by first contact with a real datasheet)

**Context.** ADR-0004 made `at_volts` required, with the reasoning that "the same servo quoted
at 6.0 V and 7.4 V differs substantially". That was right, and the shape it produced was wrong.
It modelled voltage as an **annotation on a scalar** — one torque figure, wearing the voltage it
was measured at.

Writing the first real actuator record broke it immediately. The ROBOTIS Dynamixel XM430-W350
publishes stall torque at **three** voltages — 3.8 N·m at 11.1 V, 4.1 at 12.0, 4.8 at 14.8 —
with three matching no-load speeds. That is not an unusual datasheet. It is what a competent
vendor publishes, because torque against voltage is a curve and one point on it is not the
figure.

The schema forced a choice of one row. Three things are wrong with that, in increasing order of
severity:

1. **It discards published evidence.** Two of the three rows have nowhere to go, and they came
   from the same table as the one that was kept.
2. **The choice is invisible.** A record showing 4.1 N·m at 12.0 V looks complete. Nothing on
   the page says the vendor also published 4.8 at 14.8, or that somebody picked.
3. **It silently mismatches the supply.** The spread across this actuator's own rated range is
   **26%**. A capacity derived from the 11.1 V row on a mechanism running 14.8 V understates by
   a fifth; the reverse overstates by a fifth, which is the direction that cooks a servo. Both
   failures look exactly like a correct answer.

The third is the one that matters, because it is ADR-0004's own failure mode — a number true at
one operating point and silently wrong at others — reappearing one level down. ADR-0004 deleted
`payload_kg` because capacity varies with pose. Torque varies with voltage for the same kind of
reason, and the fix has to be the same kind of fix.

**Decision.** `stall_torque_nm`, `continuous_torque_nm` and `no_load_speed_rad_s` become
**arrays** of voltage-indexed measurements. A single-voltage datasheet records a one-element
array; nothing is lost and the shape stops lying about what is known.

- A capacity derivation **selects the row matching the supply voltage**, which comes from
  `harness.power.supply_volts`.
- **No supply voltage declared, no derivation.** The answer is "incomplete", naming the harness.
  Picking a row on the author's behalf — the nominal one, the lowest one, the first one — is the
  invisible choice this ADR exists to remove, and defaulting to the lowest "to be safe" is
  conservative in the wrong place: it under-reports capacity, which sends someone to buy a bigger
  servo they did not need.
- **No matching row, no derivation.** The answer names the voltage that was asked for and the
  voltages that exist.
- **Interpolation is refused.** A supply at 13.0 V between published rows at 12.0 and 14.8 does
  not get a computed figure. Torque against voltage is approximately linear for a DC motor and
  "approximately" is a model — an unsourced one, whose output would be indistinguishable on the
  page from a datasheet value. If a sourced motor model ever arrives, this is the line to revisit,
  and it needs its own ADR.

**Consequences.** The array is more verbose for the common single-row case and that is accepted.
The alternative — allowing either a bare object or an array — means two shapes to validate, two
shapes to read, and a branch in every consumer, to save a pair of brackets.

**A derivation now depends on the harness**, which it did not before. That is a real coupling
between two records and it is the correct one: the supply voltage is a fact about the built
machine, not about the actuator, and the actuator's datasheet cannot know it. It also means a
robot with no harness record gets no capacity answer, which is one more thing that will report
incomplete. Consistent with the rest of the repo, and the reason the harness schema exists.

**This is the schema being corrected by data rather than by argument**, which is the outcome
inherited invariant #8 is fishing for. ADR-0004 reasoned its way to requiring `at_volts` and got
the requirement right and the cardinality wrong. One datasheet found it. The general lesson is
the one PD-1 paid four hours for and ADR-0007 paid a day for: a shape that has never met real
data is a hypothesis.

Rejected: keeping a scalar and adding a separate `torque_curve` array beside it. It would leave
two places for the same fact and a question about which one wins — the registry-drift shape the
platform exists to end, in miniature, inside one record.

---

## ADR-0015 — The affordance answer is a verdict and a margin, never a score — and it can never be an unqualified yes

**Date:** 2026-08-22
**Status:** accepted (delivers the affordance verdict ADR-0010 promised)

**Context.** ADR-0010 said ClawBot would answer whether a given body can do a named thing — the
*can-it-actually-happen* half of the SayCan pattern, where a language model's "does this skill
serve the instruction" is multiplied by an affordance model's "can this robot do it now". The
literature's affordance is a **float in [0.0, 1.0]**.

Building it out of `reach` and `hold` surfaced two problems, and the second one is the
interesting one.

### A score would be a fabricated number

A learned affordance model's float is a frequency estimate: it comes from trials, and 0.7 means
something close to "succeeded in 70% of attempts". ClawBot has run no trials. It has cited
hardware facts and two derivations over them. Any float it emitted would be a number with the
*shape* of a probability and no frequency behind it — the exact failure this repo deletes fields
to prevent, and worse than most because SayCan-style consumers **multiply** it. A fabricated
0.7 does not sit in a report where someone might question it; it propagates into a product and
disappears.

There is a real need underneath the request, though: a planner comparing options needs to rank
them. The honest thing to rank on is the **margin** — the actual physical headroom, in newton
metres or millimetres, derived and cited. A margin is a real quantity with units. A score is a
fabricated one without.

### The two derivations are unsound in opposite directions, so a yes is not available

This is the part that was not obvious until the two were composed.

**Sampled reach is sound positive, unsound negative** (ADR-0013). A point only enters the
reachable set after forward kinematics put the tool there, so "reachable" is proven and "no
sample reached it" is merely unproven.

**Static capacity is sound negative, unsound positive** (ADR-0004). The derived figure is an
*upper bound* — efficiency, friction, backlash and acceleration are not modelled, so real
capacity is lower. If the load exceeds the upper bound, it exceeds the real capacity too: that
negative is **conclusive**. But a load *under* the upper bound proves nothing, because the bound
overstates.

Compose them and the four combinations do not include a provable success:

| reach | capacity | what is actually known |
|---|---|---|
| sample found a pose | load exceeds the bound | **cannot** — conclusive, because exceeding an upper bound settles it |
| sample found a pose | load under the bound | reachable, and **not refuted** on capacity. Not a yes. |
| no sample reached it | — | **unproven**. Not a no (ADR-0013) |
| either | a missing input | **incomplete**, naming it |

**Decision.** Four verdicts, no score, and a margin that carries its own units.

- **`cannot`** — the only negative this repo will assert, and it is available only through
  capacity. It requires a pose that actually reached the target, so the claim is "at the pose we
  found, the static upper bound is exceeded", not "this is impossible everywhere". A different
  pose reaching the same point may do better, and the verdict says so.
- **`within-static-bound`** — the closest thing to yes. Reach found a pose; capacity is not
  exceeded there. Named this way on purpose: `can` would be read as a guarantee, and a bound that
  overstates cannot guarantee anything.
- **`unproven`** — no sample reached the target in N samples. Never `cannot`.
- **`incomplete`** — a named missing input, propagated from whichever derivation raised it.

Every verdict carries the **binding constraint** — which joint, or reach itself — and the
**margin** in the units of that constraint. Rank on the margin.

**Consequences.** ClawBot will never tell a caller that a robot *can* do something, and that is
going to read as unhelpful the first few times. It is the correct amount of confidence: the two
things it knows are a sampled lower bound on reach and an optimistic upper bound on capacity,
and neither supports a guarantee. A system that said "yes" here would be claiming that
efficiency, friction and self-collision do not matter — three things this repo explicitly does
not model and says so in every answer.

The **`cannot`** is worth more than it looks. A conclusive negative that names the joint and the
overage is directly actionable: it says which actuator to change and by how much. Most systems
in this space give a confident yes and a vague no; this one does the opposite, which is the more
useful half if only one is going to be honest.

Rejected: emitting a score derived from the margin — normalising headroom into [0,1] with some
squashing function. It would be a fabricated number wearing arithmetic, and the choice of
squashing function would silently set a risk posture nobody declared.

Rejected: taking the *best* pose across all reaching samples and reporting its margin as the
answer. Tempting, and wrong in a specific way: the best-margin pose is the one where the load
sits closest to the joint axes, which is frequently a pose that is useless for the task. The
verdict reports the pose it reached with and offers the best-margin pose alongside as a
*separate* field, so a caller can see both without one masquerading as the other.

---

## ADR-0016 — The MCP surface is entirely execute, and deliberately cannot read a file you name

**Date:** 2026-08-22
**Status:** accepted (adopts OpenDesignCore ADR-0009's line; the propose side comes out empty)

**Context.** ClawBot was the last of the five peers without an MCP surface. OpenDesignCore
ADR-0009 set the platform's rule: reads and deterministic runs **execute**, anything reaching a
fabricator **proposes**, and no approval tool exists on the server side. OpenBuildCore adopted
it and observed that all of its tools land on the execute side because nothing in it writes.

ClawBot is the stronger case of the same thing. **It has no side effects at all**, by
construction rather than by accident: ADR-0010 put every actuating loop behind Oh-Ben-Claw's
Track 0, ADR-0006 keeps it from importing a peer, and it writes to no store — `data/` is edited
by people, and every script returns a value rather than changing one. So the propose side of
ADR-0009 is not merely unused here, it is **empty**, and there is nothing a future tool could be
added to it without first breaking a different ADR.

That is worth writing down, because "no propose tools" reads like an oversight and is actually
the load-bearing consequence of two earlier decisions.

**The one real risk is the opposite of the usual one.** `urdf.py import` takes a path and reads
it. Exposed as an MCP tool, that is not a robotics feature — it is an **arbitrary file read**
handed to whatever is driving the client, wearing a domain-specific name. The interesting part
is that it looks harmless in a repo whose entire threat surface is otherwise "returns a number
that might be wrong".

**Decision.**

- Every tool is a **read or a deterministic derivation**, and all of them execute. No propose
  path, no approval tool, and none may be added without an ADR that first reverses ADR-0010.
- **No tool accepts a filesystem path.** `import_urdf` is deliberately absent from the surface;
  it stays a CLI command, where the person running it already chose the file. A tool that takes
  URDF **text** may be added later — that is a different thing, because the caller supplies the
  bytes rather than naming a file the server can reach.
- **Sample counts are capped** at a stated ceiling, and a request above it is clamped **with the
  clamp reported in the result**. A sampled reach with a large enough N is a denial of service
  against the process, and silently honouring it is as bad as silently refusing it.
- Every tool returns the **full verdict object**, caveats included. A tool that returned a bare
  boolean or a bare distance would strip the assumptions that ADR-0003, ADR-0004, ADR-0013 and
  ADR-0015 each require to travel *inside* the value. This is the failure mode an MCP surface
  invites most, because tool results get summarised by a model before a human sees them.

**Consequences.** An agent can ask what a mechanism can do and gets back an answer it cannot
strip the caveats from without doing so deliberately. That is the point: the whole repo is an
argument that the caveats are the answer.

The absent import tool will be asked for. The reply is that it exists on the CLI, and that a
text-taking variant is the right shape if the need is real.

Rejected: a `validate` tool that fixes what it finds. Validation is a read; repair is a write,
and a write to `data/` is a person's judgement about physical hardware. An agent quietly filling
in a joint limit is the precise failure this repo was built to prevent.

---

## ADR-0017 — The Rust binding encodes the refusals in the type system

**Date:** 2026-08-22
**Status:** accepted (adopts OpenPartsCore ADR-0003's codegen discipline)

**Context.** ADR-0010 made Oh-Ben-Claw a consumer of a body model it does not have, and left
open how it reads one. OpenPartsCore settled the general mechanism: hand-rolled emitters, stdlib
only, generated output **committed**, and a `--check` gate that regenerates and diffs so a data
change without a regenerated binding fails rather than drifting. Its Rust crate takes **zero
dependencies**, on the grounds that a consumer should not need serde to read static reference
data.

Copying that gets a working binding. It also misses the opportunity, which is this: **every
refusal in this repo is currently a convention.** `stall_torque_nm` must not reach a capacity
derivation — enforced by a validator, a docstring and an ADR, all of which are advice. Absent
limits mean unknown — enforced the same way. Radians in the file while Oh-Ben-Claw's
`ServoAngle` is degrees — named in ADR-0010 as a seam and enforced by nothing at all.

A type system enforces at compile time what a docstring enforces by hope. The JSON cannot carry
that; the binding can.

**Decision.** The binding is const data with zero dependencies, per OpenPartsCore, **and its
types make the repo's central refusals unrepresentable rather than merely discouraged.**

- **`Radians` and `Degrees` are distinct newtypes**, and conversion between them is explicit and
  the only path. Oh-Ben-Claw's `ServoAngle` is degrees; a value crossing that boundary must be
  converted at the boundary or it does not compile. ADR-0010 said "the conversion belongs at
  exactly one place"; this is the mechanism that makes that true instead of aspirational. The
  failure it prevents is a mechanism commanded to 57 times the intended angle.
- **`StallTorque` and `ContinuousTorque` are distinct types with no conversion between them.**
  Not a shared struct with a flag, not a newtype pair with a `From` impl — there is deliberately
  **no way to turn one into the other**, because ADR-0004's central rule is that stall torque may
  never feed a capacity derivation. A consumer that wants to try must write the fraction itself,
  in its own code, where it is visible in review.
- **Unknown stays `Option`.** Absent joint limits are `Option<JointLimits>`, not a struct with
  sentinel zeros. Rust forces the caller to confront the `None`, which is inherited invariant #3
  — absence of evidence is recorded as absence — moved from a convention to a thing the compiler
  will not let you skip.
- **Torque lookup by voltage returns `Option` and there is no interpolating variant** (ADR-0014).
  A caller asking for 13.0 V on an actuator published at 12.0 and 14.8 gets `None`.
- **No `Default`, and no convenience accessor that unwraps.** A `limits_or_default()` would undo
  the whole point in one function.

**Consequences.** The binding is more annoying to use than a plain struct dump, and that is the
feature. Every place a consumer is forced to write `match` or an explicit conversion is a place
the platform's discipline used to depend on someone having read an ADR.

Zero dependencies is kept: the newtypes are `#[repr(transparent)]` wrappers over `f64` and cost
nothing at runtime.

The generated file is committed and `--check` gates it, byte-identical or red, exactly as
OpenPartsCore does — with one difference worth noting. OpenPartsCore's binding is *only* data,
so regenerating it is mechanical. This one is data **plus hand-written types**, so the emitter
carries the type definitions as a literal header and the data as generated tail. If the types
need to change, they change in the emitter, not in the output. Editing `lib.rs` directly is the
one thing that silently works and then gets reverted by the next regeneration.

**A note on what is NOT emitted.** No Track 0 limit table in Oh-Ben-Claw's config format. ADR-0010
rejected that and it stays rejected: writing another repo's format takes that format as a
dependency. This crate publishes ClawBot's own types, and the importer is Oh-Ben-Claw's to write
and Oh-Ben-Claw's ADR to record.

Rejected: `serde` derives behind a feature flag. It would be genuinely convenient and it starts
the dependency conversation that OpenPartsCore's zero-dep decision exists to end. If a consumer
needs serialisation, the JSON is right there and is the canonical form anyway.

Rejected: emitting a `pub fn is_safe(...)` or any predicate that answers a safety question.
Nothing in this crate may look like a safety authority. Track 0 is the safety authority, this is
a data model, and a function named like a permission is how those two get confused.

---

## ADR-0018 — A cited value may describe a population rather than your unit, and efficiency does not apply to a static hold

**Date:** 2026-08-22
**Status:** accepted (closes the last sourcing topic; refines ADR-0004 without loosening it)

**Context.** Eight sourcing topics were opened when this repo was created. Seven closed quickly.
Gearbox efficiency and backlash was held to last on purpose: every other topic licensed a
**decision**, and a decision can rest on a survey, but this one would license a **number** — an
efficiency multiplies a derived capacity and turns ADR-0004's static upper bound into an
estimate. Only a vendor document with a stated method was admissible.

One was found and read: Harmonic Drive's FR Gearing engineering data
([`Knowledge/sources/gearbox-efficiency.md`](Knowledge/sources/gearbox-efficiency.md)). It
closes the topic in two directions, neither of them the expected one.

### Efficiency is a five-variable curve, and the schema field is a scalar

> "Efficiency varies depending on input speed, ratio, load level, temperature, and type of
> lubrication."

Eight charts, no scalar. And the curves are themselves conditional — published for units at the
torque rated for 2,000 rpm, then corrected by a load-compensation factor. The document's worked
example lands at **58% at rated load, and 50% at 60% of rated**, against the "80 to 90 percent"
the secondary literature quotes. The rule of thumb is not imprecise here; on the vendor's own
figures it is wrong by nearly a factor of two, in the unsafe direction.

`gearbox.efficiency` is a `number` in [0,1]. That is the third time this repo has found the same
defect: a quantity that varies over an operating envelope, stored as one number. ADR-0004 deleted
scalar `payload_kg` because capacity varies with pose. ADR-0014 made torque an array because it
varies with voltage. This is the same shape again.

### Efficiency does not apply to the computation it was wanted for

The sharper half. Efficiency curves describe a gearbox that is **turning** — they are indexed by
input speed and published at 1,000–2,000 rpm. ClawBot's `hold` is a *static* derivation, and a
mechanism holding a pose has an input speed of **zero**. There is no efficiency curve at zero
speed. What governs a stationary geartrain is starting torque and backdriving torque, which the
same document publishes as separate tables of **ranges spanning better than an order of
magnitude** (FR 40: starting 3–50 N·cm, backdriving 7–190 N·m).

Applying a running efficiency to a static hold would be wrong **in kind**, not in value.

### And a distinction this platform has never made

On torsional stiffness, the same vendor:

> "The values quoted are the average of many tests of actual units. The spring rate of an
> individual unit may vary within approximately ±30% of the average."

A cited value has meant, everywhere in this platform so far, "somebody published it, and here is
where". This is a vendor stating in a datasheet that their published number describes a
**population**, and that an individual specimen may sit 30% away from it.

Those are different kinds of claim and nothing here distinguishes them. A `mass_g` from a
datasheet is a model-typical figure. A `mass_g` from a scale is a fact about the object on the
bench. Both currently validate identically and read identically downstream, and a derivation
that chains several model-typical figures compounds a spread nobody declared.

**Decision.**

1. **`gearbox.efficiency` as a scalar is removed.** In its place, `measured_efficiency` — an
   array of points, each requiring the operating conditions that make it meaningful:
   `input_speed_rad_s`, `output_torque_nm`, `temperature_c`, `lubricant`, and `how_determined`.
   Same shape as `measured_payload` and for the same reason. A vendor curve may be sampled into
   it; a single catalogue number may not, because there is no such thing.
2. **Efficiency still feeds no derivation, and now for a sourced reason.** ADR-0004 said "not
   modelled" and left it as a gap to be closed later. It is not a gap: a running efficiency is
   the wrong quantity for a static hold. `hold` remains a static upper bound, and the ROADMAP
   entry moves from "not yet" to a scoped statement of what would actually be needed —
   starting and backdriving torque, which are different fields nobody has yet had a reason to add.
3. **Every field that can carry a physical value gains an optional `basis`**, one of
   `model-typical` or `this-unit`, plus an optional `spread_pct` for the former where the vendor
   states one. Absent means **unknown**, per invariant #3 — not "assumed exact".
4. **A derivation reports the weakest basis it consumed.** If any input is `model-typical`, the
   answer says so. A verdict built from population averages is not the same claim as one built
   from measurements of the specific hardware, and ADR-0015's margin is meaningless without
   knowing which it is.
5. **Backlash keeps its `_rad` field and gains nothing**, because the "no measurement standard"
   finding is secondary-sourced and not strong enough to build a rule on. It is recorded as
   believed and under-sourced in the source page, and it is the one thing in this topic still
   worth a primary source.

**Consequences.** Point 4 is the expensive one and the reason this ADR is worth writing. It
means most derived answers will grow a line saying they rest partly on population averages,
which is unglamorous and true. It also means the platform now has a vocabulary for something it
could not previously express: the difference between a number that describes a product line and
a number that describes your hardware.

That distinction is almost certainly not confined to gearboxes. It probably applies to
`mass_g` on links, to actuator mass, and to any figure read from a catalogue rather than a
scale. This ADR introduces the field and applies it where a source has forced the issue; a sweep
across the other schemas is deliberately **not** done here, because doing it without a source per
field would be guessing at which values are population figures — the exact error the field
exists to prevent.

**Rejected:** modelling efficiency from the published curves by fitting them. The curves are
per-model, per-lubricant, per-ratio, and reading a value off a chart image is not a citation.

**Rejected:** a default `basis: model-typical` for any value carrying a vendor URL. It would be
right most of the time, which is what makes it dangerous — the cases where it is wrong are
precisely the measured ones a user took trouble over, and silently relabelling those as
population figures would discard the better evidence.

---

## ADR-0019 — ClawBot carries a policy declaration and refuses to make one on your behalf

**Date:** 2026-08-22
**Status:** accepted (ClawBot's position on platform decision PD-5)

**Context.** PD-5 makes legality gating two-tier — design-time refusal at the assistants,
fabrication-time refusal at the nodes — with [[project-bingo]] owning the shared taxonomy in
`v3/specs/REFUSAL-CATEGORIES.md`. That spec names design-time assistants explicitly:
OpenDesignCore, OpenCircuitCore, deployment tools. ClawBot is absent only because it did not
exist when the spec was written.

Two of the nine categories land squarely on a mechanism repo. **`weapons.other`** — items
designed as weapons that are not firearms, default stance refuse network-wide. And
**`regulated.medical`**, which explicitly covers **load-bearing prosthetics**. A prosthetic limb
is a mechanism, and it is the most likely thing anybody would describe with this schema that
carries a category at all.

Three things needed deciding.

### 1. Does a policy declaration belong on a robot record?

Yes, and the argument is mechanical rather than moral. `manifest.py` already emits into
OpenBuildCore's requirement vocabulary, and OpenBuildCore's machine records already mirror
BINGO's field-for-field. **There is a path from a ClawBot robot record to a BINGO fabrication
job.** BINGO reads an absent `policy_categories` as `none` **declared**. So a ClawBot manifest
that carries no declaration is not neutral — it makes the `none` declaration on the author's
behalf, invisibly, at the far end. That is the invisible-choice failure ADR-0014 removed from
torque lookup, in a place where the consequence is legal rather than thermal.

### 2. Absent means unknown here, or `none` as BINGO reads it?

The collision. Everywhere in ClawBot, absent means UNKNOWN. In BINGO, absent means `none`
**as a declaration**, carrying the same fraud consequences as misdeclaring a licence.

**Both are right, because they are different kinds of field, and noticing that is the whole
decision.** ClawBot's absent-means-unknown governs **measurements** — a joint limit nobody
sourced, a torque nobody published. Nobody can *declare* a joint limit; you measure it or you do
not. A policy category is not a measurement. It is a **statement by the author about their own
intent**, and the author always knows. There is no honest "I do not know whether this is a
weapon".

So the field's nature is BINGO's, not this repo's. But ClawBot still refuses to *supply* the
declaration. The resolution: **absent in the file means undeclared, and ClawBot will not convert
undeclared into `none` at the boundary.** It declines to emit the fabrication-bound document
instead.

### 3. Refuse to compute, or record and let consumers route?

**Compute always.** Forward kinematics on a mechanism is not fabrication, the mathematics is in
every textbook, and a repo refusing to multiply matrices would be theatre. BINGO's own spec is
careful about this: it is "not a compliance oracle, not legal advice".

The actionable refusal is at the **output boundary**, which is the same place ADR-0007 put the
URDF refusal: decline to emit the artifact that a downstream system would act on.

**Decision.**

- A robot record may carry `policy`: a list of `categories`, the `taxonomy_version` they were
  declared against, and who declared them. **Categories are stored verbatim and never validated
  against a hardcoded list** — that would fork BINGO's taxonomy and drift, which is the failure
  [[openpartscore]] exists to end. `taxonomy_version` is **required** whenever categories are
  present, because a category id without the list version it came from is a string whose meaning
  lives somewhere else.
- **ClawBot never infers a category.** Not from link lengths, not from geometry, not from a
  name. A repo that guessed "this looks like a weapon" from a bounding box would be manufacturing
  exactly the confident, unfounded judgement the whole invariant refuses. The declaration is the
  author's and only the author's.
- **Every derivation runs regardless.** `fk`, `reach`, `hold` and `can_it` do not consult the
  policy field.
- **`manifest.py --as-project` refuses when the record is undeclared**, and says why: emitting it
  would make the `none` declaration on the author's behalf. The plain bill of parts is
  ungated — it is a shopping list for a person, not a document bound for a network.
- **`--as-project` also refuses for categories BINGO marks refuse-network-wide.** Not because
  ClawBot is adjudicating: because *no node can accept that job under any configuration*, so the
  document has no valid destination. The refusal names the taxonomy version it judged against and
  states that BINGO is authoritative.
- That check reads a **dated copy** of BINGO's default stances, marked as a copy, cited to the
  spec version, and carrying the date it was taken. It is a cache with provenance, the same shape
  as OpenPartsCore ingesting a registry — not a fork, because it never overrides and always names
  its upstream.

**Consequences.** The stance copy will go stale, and that is the cost. It is bounded: it affects
only whether ClawBot emits a document, never whether a job is accepted, and BINGO re-checks at
matching time against the frozen list. A stale copy makes ClawBot slightly over- or
under-cautious about emitting, and never makes a routing decision.

**A prosthetic is the case to think with, not a firearm.** `regulated.medical` is node-opt-in
rather than refused, so a declared prosthetic **emits normally** and carries its category to a
node that has opted in with certification context. The design is correct if it lets that person
work while making the declaration explicit — and wrong if it treats every category as a
prohibition. Refusal is scoped to the four categories the network refuses outright.

Rejected: requiring `policy` on every robot record. It would force a declaration to compute
forward kinematics, which is the theatre above with extra steps, and it would make the field
noise on the majority of records where the honest answer is `none`.

Rejected: a `policy_categories` enum in the schema. Convenient, and it forks a taxonomy whose
own spec says growth requires a spec revision rather than an enum edit. ClawBot stores the
string and the version; BINGO adjudicates.

Rejected: refusing to *describe* a mechanism in a refused category. ClawBot is a notation. A
notation that cannot express a thing does not prevent the thing; it prevents the thing being
described accurately, which is worse, and it would put this repo in the business of deciding
what may be written down.

---

## ADR-0020 — The binding carries the control contract, and the contract's own arithmetic

**Date:** 2026-08-22
**Status:** accepted (completes ADR-0017; scopes what the binding emits)

**Context.** ADR-0017 justified the Rust binding almost entirely on one seam: `Radians` and
`Degrees` are distinct types, so passing degrees where radians are required does not compile, and
Oh-Ben-Claw's `MovementCommand::ServoAngle` is in degrees.

The binding shipped without the field that seam actually lives on. It emitted `Robot` and
`Actuator` and **no `Harness`** — so `harness.channels.zero_offset_rad`, the one angular value a
runtime would read on its way to commanding a servo, was not in the crate at all. The binding
could not be used for the thing that justified it. That is a gap in execution rather than a
change of mind, and it is worth recording because the ADR read as complete while the artifact
was not.

Two decisions came out of closing it.

**Decision 1 — the contract's arithmetic lives in the crate.**

`Channel::actuator_angle(Radians) -> Radians` applies `inverted` and `zero_offset` and returns
radians.

That looks, at a glance, like ClawBot computing a command, which ADR-0010 forbids. It is not, and
the distinction is worth stating: **inversion and zero offset are part of the contract, not part
of the decision to move.** They are facts about how the hardware was physically installed, they
are fixed for the life of the build, and applying them is arithmetic that every consumer would
otherwise write identically — which means every consumer would eventually write one of them
differently. Nothing here reaches hardware, chooses a target, or decides when to act.

It **returns `Radians` deliberately.** Returning `Degrees` would move the boundary inside the
crate and the consumer would stop seeing it, which is the opposite of ADR-0017's whole argument.
The consumer converts at its own edge, and the seam stays one legible line:
`Degrees::from(channel.actuator_angle(target))`.

**Decision 2 — assemblies are not emitted, and that is deliberate.**

An assembly is a DAG of steps for a person at a bench: fasteners, torques, what cannot be undone.
No runtime consumes it. Emitting it would be data nothing reads, which is precisely what
ADR-0017's zero-dependency, nothing-you-do-not-need argument is against. It stays in
`data/assemblies/` as JSON, where a build-guide renderer can read it.

If something ever consumes assemblies programmatically, this is the decision to revisit — and the
question to ask first is whether that consumer wants Rust or wants the JSON it is already
sitting next to.

**Consequences.** `Option<bool>` on `CableRun::permits_full_travel` is now doing real work: the
compiler will not let a caller collapse *nobody checked* into *does not permit* without writing
the match arm. That is ADR-0012's tri-state, enforced rather than documented, and it is the
second-best thing in the crate after the `compile_fail` doctests.

The crate's surface grows by five types and two lookups, all of them const data with no
dependencies. `HARNESSES` is empty today because `data/harnesses/` is, so the harness tests
exercise the type API rather than real records — which is honest and stated in the tests rather
than papered over with a fixture pretending to be data.

Rejected: a `Channel::command(...)` or anything else named like an instruction. ADR-0017 already
refused predicates that look like safety authorities; the same reasoning applies to names that
look like actions. `actuator_angle` describes what it returns, not what to do with it.

---

## ADR-0021 — Starting and backdriving torque are ranges, and the two ends answer opposite questions

**Date:** 2026-08-22
**Status:** accepted (picks up what ADR-0018 named)

**Context.** ADR-0018 closed the gearbox-efficiency topic by establishing that efficiency is the
wrong quantity for a static hold — efficiency curves are indexed by input speed, and a held pose
has none. It named what would actually be needed: **starting torque and backdriving torque**,
which the same Harmonic Drive document publishes as separate tables.

Those tables have a shape worth stopping on. For an FR 40, starting torque is **3–50 N·cm** and
backdriving torque is **7–190 N·m**
([`Knowledge/sources/gearbox-efficiency.md`](Knowledge/sources/gearbox-efficiency.md)). Not a
value with a tolerance — a range spanning better than an order of magnitude, and the vendor
states its method:

> "Values quoted are based on actual tests with the component sets assembled in their housings,
> and inclusive of friction resistance of oil seals, and churning of oil."

**Decision.** Both are recorded as **ranges**, `{ min, max, how_determined }`, and there is no
scalar form of either.

This is the fourth time this repo has met the same defect and the first time it has met it
before writing the field rather than after. ADR-0004 deleted scalar `payload_kg` because capacity
varies with pose. ADR-0014 made torque an array because it varies with voltage. ADR-0018 removed
scalar `efficiency` because it varies over five variables. Here the variation is not over an
operating envelope at all — it is **unit to unit**, which is why a range rather than an index is
the right shape, and why `basis: model-typical` from ADR-0018 belongs on it.

**The part that makes this more than a data-entry decision: the two ends answer opposite
questions.**

- *"Can this mechanism hold a load without powering the motor?"* is answered by the **minimum**.
  The unit on your bench might be the loose one, and assuming otherwise means a load that slips.
- *"Will this mechanism back-drive when I need it to — for hand-guiding, or for a fault that
  must not lock the joint?"* is answered by the **maximum**. The unit might be the stiff one.

A single figure cannot serve both, and picking an end silently is wrong in one direction or the
other **depending on a question the record does not know the caller is asking**. So the range is
stored whole and a consumer picks the end its question needs.

**Neither feeds a derivation.** Recorded and unused, exactly as `gearbox.efficiency` was before
it was removed and as `harness.service_loop_mm` still is.

The reason is specific rather than lazy. The tempting inference — *a load below the backdriving
minimum is held by the geartrain with no actuator torque* — is a **physical claim this repo has
no source for.** The Harmonic Drive document publishes the numbers and their test method; it
does not state a relationship between a backdriving figure and a statically held load, and
nothing else read here does either. Writing that relationship into `hold` would be exactly the
plausible, uncited reasoning the invariant refuses, and it would be more dangerous than most
because its failure mode is a joint that lets go.

So `hold` continues to report a static upper bound from continuous actuator torque and continues
to say what it does not model. What changes is that the data is now here when a source for the
relationship arrives.

**Consequences.** A third recorded-but-unused field is a real smell, and worth naming as one:
this repo now carries efficiency-shaped data, cable-slack data and geartrain-resistance data that
nothing computes with. The defence is that each was added because a *source* arrived, not because
a feature was wanted, and each has a written condition for becoming useful. If a fourth appears
without one, that is the point to ask whether the schema is collecting rather than modelling.

Units: `_nm` per the repo's rule, so a figure published in N·cm is converted on the way in and
`how_determined` records the original. A conversion is not a citation and the original units
belong in the record, because a reader checking against the datasheet will be looking for N·cm.

Rejected: a single `typical` value alongside the range. It would be read as the answer, the range
would become decoration, and the vendor does not publish one — inventing a midpoint would be a
number with no source sitting between two that have one.

---

## ADR-0022 — The upstream gap closed, so the declaration travels as data

**Date:** 2026-08-23
**Status:** accepted (records a consequence of ADR-0019 changing; its decision is untouched)

**Context.** ADR-0019 gave this repo its PD-5 position and recorded one consequence found while
implementing it: OpenBuildCore's project schema is `additionalProperties: false` and had **no
field for a policy declaration**, so a declared category could only travel as **prose** in
`description`. `manifest.py` printed a note saying so rather than smuggling the field in.

That was reported as OpenBuildCore#9 and fixed by its ADR-0007, which added
`policy_categories` with Project BINGO's own field name and shape. It is on that repo's `main`
as of 2026-08-23.

**Decision.** `manifest.py --as-project` emits `policy_categories` as data. The prose in
`description` goes, because carrying the same claim in two places is how the two disagree later.

**The `taxonomy_version` deliberately does not travel**, and this is the part worth recording.
ClawBot requires it on a record (ADR-0019) because a category id without the version of the list
it came from is a string whose meaning lives somewhere else. BINGO solves the same problem
differently — it **freezes the category list's hash into the job at order time**, so an id is
pinned by the order rather than by the asset. Adding an asset-level version field to
OpenBuildCore would fork a mechanism that already works. So the version stays in the ClawBot
record, where a reader can see what the author declared against, and the id travels alone into a
system that will pin it.

**Consequences.** This is the first time a limitation this repo *reported* upstream has been
fixed upstream and read back. Worth noting what made it work: ADR-0019 refused to smuggle the
field into `description` **as a field**, and refused to invent a name — so when the real field
arrived it had the name BINGO had already specified, and the change here was three lines rather
than a migration.

Two tests were rewritten rather than deleted. `test_the_declaration_cannot_travel_as_data...`
became `test_the_declaration_travels_as_data`, and the docstring keeps the history, because the
failure it used to guard is the interesting one: **a declaration that does not travel as data
reads, downstream, as no declaration at all** — and BINGO treats an absent declaration as `none`
*declared*, with fraud consequences. That hazard did not go away; it moved upstream, where the
field now exists to prevent it.

ADR-0019's decision is unchanged: absent still means undeclared, ClawBot still refuses to emit a
fabrication-bound document for an undeclared record, and it still never infers a category.

---

## ADR-0023 — Torque carries the index its datasheet indexes it by, and for a stepper that is current

**Date:** 2026-08-23
**Status:** accepted

**Context.** The `type` enum has accepted `stepper` and `bldc` since the schema was written. No field could express one.

Every torque row required `at_volts`: `$defs/torqueAtVolts` requires it, and `continuous_torque_nm` requires it with `additionalProperties: false` and no `at_amps` anywhere. A stepper publishes **holding torque against rated current per phase**. So recording one honestly was impossible, and the only way through was to invent a voltage the datasheet does not state — which is the precise failure this repo exists to refuse, reached by following the schema rather than by carelessness.

An enum that promises support the fields cannot deliver is worse than an enum that refuses the type outright, because it looks like a supported path right up until the moment somebody fills it in.

**Why not just write the vendor's voltage in.** StepperOnline publishes, for the 17HS19-2004S1: holding torque 59 N·cm, rated current/phase 2.0 A, phase resistance 1.4 Ω, **voltage 2.8 V**.

> 2.0 A × 1.4 Ω = 2.8 V, exactly.

The published "voltage" is the I·R product of the two figures beside it. It carries no information they do not, it is not the supply the motor is driven from, and — since phase resistance moves with temperature — it is not even stable. A second retailer lists the same motor with **no voltage at all**, which is consistent with it not being an independent specification.

Writing that number into `at_volts` would make one field name mean *"the supply voltage this figure applies at"* on a servo and *"rated current times winding resistance"* on a stepper. A consumer reading `at_volts` across a mixed registry would be silently comparing two different quantities. That is ADR-0014's problem — a figure whose index is not stated is not a figure — arriving from the other direction.

**Options considered.**

1. *Make `at_volts` optional on the existing rows.* Rejected. It would let a servo record omit the voltage that ADR-0014 exists to require, trading a stepper gap for a servo hole.
2. *Accept either index on one row type (`anyOf`).* Rejected. A row that may be indexed either way must be inspected to know which it is, and the whole point of an index is that a lookup does not have to guess.
3. *Store the vendor's I·R voltage and note the meaning in prose.* Rejected. A note does not travel into a derivation, and the number would be numerically indistinguishable from a real supply voltage.
4. *A separate current-indexed field, with no voltage on it at all.* Accepted.

**Decision.** `holding_torque_nm`, an array of `$defs/torqueAtAmps` = `{value, at_amps, source}`, `additionalProperties: false`.

- `at_amps` is **required**, per phase, and is the index — the exact role `at_volts` plays for a servo.
- **There is deliberately no `at_volts` on this type.** Re-admitting it reopens the ambiguity the field exists to close. A genuine supply voltage belongs in `electrical.nominal_volts`, where it describes the actuator rather than annotating a torque.
- The validator refuses a holding row carrying `at_volts` and *says why*, because `scripts/` is stdlib-only and does not evaluate the schema's own `additionalProperties`.
- Using the wrong field for the type is **reported, not refused**: both are legal shapes, and a vendor may yet publish something this ADR did not anticipate.

**What this does not decide.** *Whether a holding torque may size a mechanism.* It may not, today — `continuous_torque_nm` remains the only torque that does (ADR-0004), and a stepper with only a holding figure answers `incomplete` exactly as the XM430 and the MG90S do.

That is not a claim that holding torque is unsustainable. It is a record that **the datasheet read for this ADR does not say**, and the question is left open rather than settled by inference. The Rust binding enforces it the way it enforces the stall rule: `HoldingTorque` has no conversion to `ContinuousTorque`, and a `compile_fail` doctest executes that guarantee.

**Consequences.** A stepper or BLDC can now be recorded without inventing anything. Six tests cover the index, the duplicate, the refused voltage, both wrong-field warnings, and the underivable-capacity outcome. The binding gains `HoldingTorque` and `Actuator::holding_torque`, empty for every servo — and empty is not zero.

This is the third field to arrive this way, after ADR-0014 (voltage) and ADR-0018 (efficiency). All three came from one datasheet meeting one schema field, which is the mechanism `Knowledge/concepts/open-questions.md` predicted would keep producing them: *"not from thinking harder, but from one datasheet meeting one schema field."*
