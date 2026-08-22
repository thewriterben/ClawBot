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
