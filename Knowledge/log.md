# Log

Append-only. Newest at the bottom. Entries start `## [YYYY-MM-DD] <op> | <title>` so that `grep "^## \[" log.md | tail -5` works.

---

## [2026-08-22] build | ClawBot created — scaffold, six ADRs, and a wiki with an empty half

Started from an empty directory containing an empty `Knowledge/`. Two instructions: apply the LLM Wiki pattern, and create the repo for the robotics module for OBC.

**Read before writing anything.** OpenBuildCore's README, ROADMAP, DECISIONS and `machine.schema.json`; OpenPartsCore's README; OpenDesignCore's whole `wiki/`; the accessible part of Oh-Ben-Claw's README. The single most useful discovery was that **the platform already runs an LLM Wiki** — `OpenDesignCore/wiki/` has been live since 2026-08-15 with 25 pages. Matching it was clearly better than instantiating the pattern fresh, so `Knowledge/CLAUDE.md` is ODC's schema with two changes, both recorded in [[odc-wiki]].

**The scoping question that shaped everything.** "Robotics module for OBC" admits at least four readings — a machine kind inside OpenBuildCore, a peer repo, a bridge to Oh-Ben-Claw's runtime, or a catalogue of buildable robot kits. Asked rather than guessed. Answer: fifth peer, robot models and kinematics. ADR-0001 then had to argue *why* not the machine kind, and the argument turned out to be about data shape rather than preference — an `envelope_mm` box with axis-aligned containment is correct for a printer and structurally wrong for an arm, whose reachable set is non-convex and frequently holed.

**Two decisions with teeth, both refusals.** ADR-0003 removes `reach_mm`; ADR-0004 removes scalar `payload_kg`. Both are OpenBuildCore ADR-0005 applied to a new quantity: if nobody measured it and it cannot be derived from something that was, the answer is that it cannot be given. Writing them as *absent fields* rather than as validation rules matters — a rule can be waived by whoever is in a hurry, a missing field has to be added on purpose.

**One asymmetry recorded rather than smoothed over.** OBC could say its axis-aligned-only fit was "the safe direction to be wrong in", because it under-claims. ClawBot's computed reach without self-collision **over**-claims: it will name points the arm cannot occupy without hitting itself. That is the wrong direction, and ADR-0003 says so in its consequences rather than in a footnote, along with the requirement that every reachability answer state it is a joint-limit result and not a collision result.

**The wiki's robotics half is empty on purpose, and that was the hardest thing to hold to.** There was nothing stopping a dozen fluent pages on forward kinematics, DH conventions and servo thermal derating. All of them would have been uncited, most of them roughly right, and none of them distinguishable on the page from something researched. `raw/robotics/` has a README explaining the vacancy and [[open-questions]] carries the reading list that fills it — eight sourcing topics, plus six documents already sitting on disk unread, of which Oh-Ben-Claw's `docs/SOTA-COMPARISON.md` is the cheapest and most valuable.

**A distinction that came up while writing the schemas and is worth keeping.** Fields were written for gearbox type, backlash and harmonic drives from an understanding with no sources behind it. That is defensible for a *shape* and would not be defensible for a *value* — the schema says what a record may contain, not what is true. Recorded at the end of [[open-questions]] because it is the sort of line that erodes if it is not written down.

**Self-audit against the platform's own rules, since [[inherited-invariants]] was written the same day.** ClawBot is in breach of #8: ADR-0005 chose a URDF-shaped tree over DH parameters without running a single conversion, which is exactly what PD-1 cost four hours to learn. It is question 1 in [[open-questions]] with a concrete falsification — round-trip a real URDF and see what does not survive.

Created: 6 ADRs, 2 JSON Schemas, 2 deliberately-placeholder templates (every dimension a `1`, every citation `TODO(source)`, copying OBC's K2 Plus discipline), 11 wiki pages, and 3 `TODO(source)` markers that all say the same thing — nobody has asked for this repo yet, and ADR-0001 admits it.

---

## [2026-08-22] ingest | The empty half, filled by a quarter — and ADR-0005's consequences retracted

Four robotics sources read, four ADRs written, the schema corrected in three places. The
repo's highest-priority self-recorded breach is closed.

**What was read.** The `urdfdom` XSD; the reference parser's `joint.cpp`; REP-103; Corke's 2007
paper on DH assignment; the ROBOTIS Dynamixel XM430-W350 manual. None copied into
`raw/robotics/` — each has a stable home, and a second copy is a copy that drifts. Cited with
retrieval dates instead, because unlike a sibling repo a URL is not under version control.

**The finding that mattered, and it was not the one predicted.** [[open-questions]] guessed the
URDF round trip would break on `mimic`, multiple geometries, xacro, inertial frames. All real,
all minor. The actual break is **absence**. `urdfdom` will not parse a revolute joint with no
`limit` element — so a ClawBot record in exactly the state ADR-0003 exists to handle has *no
valid URDF at all*. And in the other direction, missing bounds default to `0` and a missing axis
defaults to `(1,0,0)`, silently, so the parse is where absence gets destroyed.

That is invariant #3 inverted, living inside the interchange format this repo chose to speak.
ADR-0007 makes the converter a boundary with an explicit absence rule each way: export refuses
and names the joint rather than emitting a zero, and the importer reads the XML rather than the
parsed tree, because no importer built on `urdf_parser` can be correct.

**ADR-0005 survives, better armed.** Its *decision* stands. Its consequences sentence — "a
mapping rather than a reinterpretation" — is retracted. Meanwhile [[dh-conventions]] handed the
ADR three arguments it never made: the zero-angle offsets are a second undeclared variable; the
base and tool transforms fall out of a DH factorisation as *residue*, which is fatal for a repo
whose ADR-0003 makes the tool offset load-bearing; and DH cannot branch at all.

**A contradiction found in the schema, not in the sources.** `kind` said "open serial chains
only" while `joints` said "must be a tree rooted at base_link". A tree branches. Both were
written the same day. ADR-0008 keeps the tree rule, withdraws the enum's claim, and separates
*label* from *topology constraint* — then adds `mimic`, which splits "closed chains" into the
cheap 80% (coupled joints on a tree: parallel jaws, differentials) and the expensive 20% (true
loops, still refused). A parallel gripper — the most likely first thing anyone would describe —
was previously inexpressible because of loops it does not have.

**Scope, revisited on evidence rather than taste.** ADR-0009 adopts URDF's full six joint types.
The realisation that unlocked it: a moving base only breaks reachability if reach is a *world*
claim, and ADR-0003 already refuses to make it one. Every answer is relative to `base_link`, and
now says so. The sharp consequence is gravity — a static capacity derivation on a floating base
must take a declared base orientation or answer incomplete, because assuming z-up would
reintroduce the exact "true at one configuration" failure ADR-0004 deleted `payload_kg` to
prevent, through the base instead of the pose.

**Where control stops.** ADR-0010, written after confirming [[oh-ben-claw]] has **no robot
model** — `obc-movement` is a flat `ServoAngle { name, channel, angle }` map with no notion that
one channel is downstream of another. So ADR-0001's second rejection was argued against a repo
that had not solved this. ClawBot takes the body model, the derivations over it, and an
affordance verdict; the loop stays behind Track 0. The dividing line is not *how much control*
but *what the answer is derived from*: cited hardware data and geometry on one side, the world
right now on the other.

**Rejected.** Emitting a Track 0 limit table in Oh-Ben-Claw's own config format — tempting,
since ClawBot's limits are cited and Track 0's are hand-typed, but writing another repo's config
takes its format as a dependency, which is the coupling ADR-0006 exists to prevent. Also
rejected: a `closed_chain` boolean meaning "this record approximates a loop" — a flag that says
the data is wrong is not better than refusing the data. Also deferred: the learned-policy
surface (action spaces, sim export, dataset schemas), which is a second product rather than a
schema change.

**Found and not yet fixed.** `MovementCommand::ServoAngle` is in **degrees**; ClawBot and
REP-103 are both radians. ADR-0010 puts the conversion at one boundary. Nothing enforces it,
because there is still no code.

**The one that keeps being true.** ADR-0004 predicted most actuators would have no usable torque
figure. The XM430 is a well-documented smart servo whose manual explicitly says "the given Stall
torque rating for a servo is different from its continuous output rating" — and then publishes
three stall figures and no continuous one. The prediction was made from reasoning; it is now
confirmed from a datasheet. The 30-50%-of-stall rule of thumb exists in the trade press and
stays refused: the range spans a factor of 1.67, so choosing a point in it is a guess, and
`how_determined` exists to reject exactly that.

---

## [2026-08-22] build | Two schemas for the half a robot record never described, and the first code

A robot record says what a mechanism *is*. Nothing said what somebody has to *do* to end up
holding one, or how the wires get from the controller to the joints. Both gaps turned out to
carry a decision with teeth.

**Assembly (ADR-0011).** Three things had to be settled and two of them were refusals. Steps
form a **DAG**, not a list, because "these two can be done in either order" and "this one must
come first" are different facts and a numbered list can only express the second — and the
constraints that matter most are the ones about steps that cannot be undone. **Build time is
never modelled**, following OBC ADR-0005 on print time, and assembly is worse than printing
because the dominant variable is the builder: an author on their fifth build and a stranger on
their first are not one measurement with noise, they are different quantities, which is why
`measured_build_time` carries `builder_experience`. And **fastener torque is citation-gated with
absence meaning UNKNOWN** — not "hand tight", which is a number somebody invented at the bench.
The failure mode is a stripped heat-set insert in a printed part, which is unrecoverable.

**Harness (ADR-0012), and the finding worth keeping.** The wiring is part of the mechanism. A
servo cable running from a wrist to a controller in the base crosses every joint between them,
and unless somebody left slack, **it binds before the joint does**. So a mechanism's real travel
is the tighter of what the hardware permits and what the harness permits, and the second number
lived nowhere. `permits_full_travel` is tri-state and **null means nobody checked** — never that
it is fine.

The neighbouring temptation was to *compute* it from a declared service loop and a bend radius.
Refused: that needs cable mechanics under load that this repo has no source for, and it would
produce a plausible number. `service_loop_mm` is recorded and feeds nothing, exactly as
`gearbox.efficiency` is.

This gives ADR-0003 a second known over-claim alongside self-collision, and the right response
was the same one: name it in the returned value rather than fix it silently.

**Three sources of truth for one joint's travel** — the joint's `limits`, the actuator's
`travel`, the harness's `travel_limit` — and that is deliberate. They are different claims, not
duplicates: what the mechanism permits, what the motor can do, what the wiring allows.
Collapsing them would lose which one bound, and "this arm cannot reach that" and "this arm's
*wiring* cannot reach that" have different fixes.

**The first code, and the first proof that a rule bites.** `validate.py` in
[[openbuildcore]]'s and OpenPartsCore's idiom — stdlib only, structure as the easy half,
referential integrity as the half that matters. 29 negative tests, one per rule with teeth:
degrees in a `_rad` field, a link with two parents, a mimic cycle, a link declaring two kinds, a
continuous torque whose `how_determined` reads like a fraction of stall. Two tests exist to prove
the *warnings* do not block, because "unknown" passing through is the entire point of ADR-0003.

**And the seam, tested against the peer's own file.** `manifest.py` emits a bill of parts in
OpenBuildCore's three-kind vocabulary, and the test validates the output against
`OpenBuildCore/schema/project.schema.json` itself rather than a copy — skipping honestly if that
repo is not checked out, because a skipped test is an honest "not checked" and a passing test
that never ran is the failure this platform exists to refuse.

The interesting part of that emitter is what it will not do. Three link kinds do not map onto
three requirement kinds: a `provenance_ref` is a hash and nothing else, so ClawBot has no
bounding box to declare, and emitting a `make` requirement for it would put a fabricated
`size_mm` inside a document that validates. Those links are reported separately and handed to
OBC's `can-print --from-sidecar`, which judges the real geometry (ODC ADR-0010) and is the
stronger check anyway.
