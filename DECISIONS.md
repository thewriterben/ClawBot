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
