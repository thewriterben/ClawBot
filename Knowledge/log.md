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

---

## [2026-08-22] build | The computations exist, and the converter ADR-0007 described was actually run

Two more sources, one ADR, three scripts, 79 tests. The repo went from "schemas and decisions"
to "answers a question and refuses to answer several others on the record".

**Sourcing finished, except the one that would license a number.** Lynch and Park for forward
kinematics; the Monte Carlo workspace and FCL/ACM collision literature for the two remaining
computation topics. Seven of eight topics answered. The last — gearbox efficiency and backlash —
is last on purpose: every other topic licensed a *decision*, which can rest on a survey, and this
one would multiply a derived capacity and turn ADR-0004's upper bound into an estimate. That
needs vendor data with a method.

**A third representation nobody had considered, and it changes nothing.** [[forward-kinematics]]
teaches FK by **product of exponentials** and puts DH in an appendix. ADR-0005 framed its choice
as DH versus a URDF tree; PoE was never on the table. It does not reopen the decision, and the
reason is the good part: PoE is a *computation*, not a storage format, and a screw axis is
derivable from what the tree already stores. Better still, the two frames PoE requires are
exactly the two this repo already insists on naming — a fixed base frame (ADR-0009) and an
end-effector frame (ADR-0003's tool offset). DH loses both as factorisation residue. Recorded as
open-question 6 and closed in the same breath, because "we did not consider X" is worth writing
down even when X would not have changed anything.

**Two topics closed by refusing them, which counts as read.** Self-collision needs link geometry
this repo deliberately does not carry (ADR-0006 keeps geometry in [[opendesigncore]]) plus an
allowed-collision matrix nobody has authored. The bounding-box shortcut was considered and
rejected: it would flag adjacent links constantly, and its silence would be indistinguishable
from real clearance. **A collision check that cannot tell "clear" from "not checked" is worse
than none, because the first is a claim.** Same shape of answer for workspace volume — a single
figure computed from an inner-bounded sample understates by an unknown amount and would be read
as measured.

**ADR-0013: sampled reachability, and the asymmetry that makes it honest.** A sampled workspace
is inner-bounded — every point it reports was actually reached by FK, so its errors are all
false negatives. That is the direction this repo is allowed to be wrong in, and the opposite of
ADR-0003's known over-claim on self-collision. So "reachable" is a claim carrying the pose that
got there, and **"not reachable" is never returned** — the verdict is `no-sample-reached-it` with
the sample count in it. Sampling is seeded and the seed is recorded, because unrecorded
randomness would break [[opendesigncore]]'s determinism discipline.

**Two real bugs found while writing the capacity derivation**, both caught by writing the test
before trusting the code. Every joint was being loaded by every mass regardless of whether it
hung below that joint; and the lever arm was an xy-distance approximation instead of torque about
the actual joint axis. Fixed to `n . (r x F)` with the axis rotated from the child frame into the
base frame, and the masses filtered by descendant set. The known-answer test that caught it —
1 kg at 100 mm is 0.980665 N.m — was true before the code existed, which is the whole argument
for known answers over pinned outputs.

**A third bug, and a nice one.** `element.find("parent") or ET.Element("p")` looks harmless and
is always wrong: an ElementTree element with no children is *falsy*, so a present `<parent>` fell
through to the empty fallback every time. There is now a test named after it.

**ADR-0007's claims are no longer claims.** The converter it described exists and 19 tests run
the round trip. Everything it asserted holds: structure survives both ways; a `<limit>` with no
bounds imports as UNKNOWN rather than the zero `urdfdom` would produce; a missing `<axis>` is
recorded as a *format default* in the citation rather than as the author's statement; and a robot
with unsourced limits **cannot be exported at all**, with every offending joint named rather than
the first. Two things turned up that ADR-0007 did not anticipate: `effort` and `velocity` are
*also* fatal to `urdfdom`, so export refuses on those too; and URDF names routinely contain
underscores while ClawBot ids may not, so every rename is reported rather than done quietly.

**And the loss that is the whole reason URDF is not the storage format**, now with a test named
after it: `test_provenance_does_not_survive_the_round_trip`. A joint limit cited to a vendor
datasheet exports, re-imports, and comes back cited to "URDF import". The format has nowhere to
record where a number came from. That was ADR-0005's opening premise and it is now demonstrated
rather than asserted.

**Documentation caught up twice, and that is a rule now.** The README said "no code yet" for
exactly as long as that was true, and `Knowledge/CLAUDE.md` said the robotics half was empty for
exactly one day. Both were corrected in the same change as the work that falsified them. The
"empty half" section was rewritten rather than deleted, because the rule that emptied the
directory still governs every page written into it.

---

## [2026-08-22] ingest | The first real record, and the schema it broke on contact

`data/` stopped being empty. One actuator — the ROBOTIS Dynamixel XM430-W350, written from the
vendor's own e-Manual — and it did what a first record is supposed to do, which is find
something wrong.

**The record exists mainly to demonstrate a refusal.** `continuous_torque_nm` is **null**, on a
good datasheet, from a vendor who states the distinction outright: *"the given Stall torque
rating for a servo is different from its continuous output rating."* ROBOTIS names it, publishes
a performance graph, publishes three stall figures — and no continuous one. So capacity over
this actuator is underivable and every `hold` answer naming it will say so. That is ADR-0004
working, and it is worth restating that this was *predicted from reasoning* in ADR-0004 and is
now *confirmed from a datasheet*.

**What broke: ADR-0004 got the requirement right and the cardinality wrong.** It required
`at_volts`, correctly, and then modelled voltage as an **annotation on a scalar** — one figure
wearing the voltage it was measured at. The XM430 publishes **three rows**: 3.8 N·m at 11.1 V,
4.1 at 12.0, 4.8 at 14.8, with three matching no-load speeds, from one table.

The schema forced picking one. Three problems, worst last: it discards published evidence; the
choice is invisible on the page; and the spread across this actuator's own rated range is
**26%**, so a capacity derived from the wrong row is wrong by a fifth — and the direction that
overstates is the one that cooks a servo. That is ADR-0004's own failure mode — a number true at
one operating point and silently wrong at others — reappearing one level down, which is why the
fix had to be the same kind of fix.

**ADR-0014** makes torque and speed voltage-indexed arrays, and puts three refusals around the
lookup. A derivation selects the row matching `harness.power.supply_volts`. **No declared supply
voltage, no derivation** — picking a row on the author's behalf is the invisible choice this
removes, and defaulting to the lowest "to be safe" is conservative in the wrong place, because
it under-reports capacity and sends someone to buy a servo they did not need. **No matching row,
no derivation**, naming what was asked for and what exists. And **interpolation is refused**:
torque against voltage is approximately linear for a DC motor, "approximately" is a model, and
an unsourced model's output would be indistinguishable on the page from a datasheet value.

That creates a real coupling — a capacity answer now depends on the **harness** record, which it
did not before. It is the correct coupling: supply voltage is a fact about the built machine,
and the actuator's datasheet cannot know it. It also means one more thing reports incomplete,
which is consistent with everything else here.

**Open question 3 closed, against real records rather than argument.** The actuator/parts
boundary had never met an entry on both sides. It has now: [[openpartscore]] already carries
`electronic/sg90`, and that record holds id, description, source, `bus`, `capabilities`,
`connector`, `compatible_boards` — and **no torque, no speed, no mass, no travel, no gearing, no
feedback type**. The overlap in practice is zero. Upstream answers *what is this and how do you
talk to it*; ClawBot answers *what does it do when you bolt it into a mechanism*.

Two smaller findings from the same comparison. A servo lives in OPC's **`electronic`** namespace,
not `mechanical` (its ADR-0005), so a ClawBot `part_id` for an actuator reads `electronic/...`.
And `bus` now appears on both sides — not a conflict, because they answer different questions,
but it is the field to watch.

**Also: OPC has no entry for the XM430 at all**, so this record carries no `part_id`. Whether an
uncatalogued actuator is a legitimate state or something the schema should require is a real
question, and `manifest.py` already half-answers it by reporting uncatalogued parts separately
rather than dropping them.

**Lint pass on the top-level docs, since they were being edited anyway.** Three ADR citations in
the README were wrong and had been since the scaffold: reach cited to ADR-0002 (which is the
licence), payload to ADR-0003, and the DH argument to ADR-0004 — each off by one. Fixed, along
with a duplicated line in ROADMAP's "Not yet". Worth noting the shape: a citation pointing at
the wrong thing is exactly the failure this repo is built to prevent, and it was sitting in the
file that explains the discipline.

---

## [2026-08-22] build | Composing the two derivations proves there is no yes to give

The affordance verdict ADR-0010 promised, and an MCP surface. The interesting result came out
of the composition rather than out of either half.

**The two derivations are unsound in opposite directions.** Neither ADR-0004 nor ADR-0013 said
this, because it is only visible when they meet.

Sampled reach is **sound positive, unsound negative**: a point only enters the reachable set
after forward kinematics put the tool there, so "reachable" is proven and "no sample found it"
is merely unproven. Static capacity is the mirror — **sound negative, unsound positive**: the
derived figure is an upper bound, so exceeding it is conclusive, and coming in under it proves
nothing, because efficiency, friction, backlash and acceleration are all unmodelled and all
subtract.

Compose them and the four combinations contain no provable success. So ADR-0015's verdict set is
`cannot` (the only assertable negative, and it is a real claim), `within-static-bound` (the
closest thing to yes, deliberately not named `can` because a bound that overstates cannot
guarantee anything), `unproven`, and `incomplete`. There is a test called
`test_there_is_no_can_verdict_anywhere` whose entire job is to fail if somebody later adds one.

**The score was the other refusal.** The literature's affordance is a float in [0,1], and that
float is a frequency estimate — it comes from trials. This repo has run none. What made it worth
an explicit refusal rather than an omission is that SayCan-style consumers **multiply**
affordances: a fabricated 0.7 does not sit in a report where somebody might question it, it goes
into a product and disappears. The honest thing to rank on is the **margin** — real headroom in
newton metres, derived and cited. A margin has units; a score does not.

**Rejected, and worth recording:** reporting the *best* margin across all reaching poses as the
answer. Tempting, and wrong in a specific way — the best-margin pose is the one holding the load
closest to the joint axes, which is frequently useless for the actual task. It is offered as a
separate field beside the verdict's own pose, so a caller sees both without one masquerading as
the other. Also rejected: squashing the margin into [0,1], which would be a fabricated number
wearing arithmetic, with the squashing function silently setting a risk posture nobody declared.

**The MCP surface, and the thing it made visible.** ClawBot was the last peer without one.
Adopting [[opendesigncore]] ADR-0009's execute-versus-propose line produced an empty propose
side — **not unused, empty**. This repo has no side effects by construction: ADR-0010 put every
actuating loop behind Track 0, ADR-0006 keeps it from importing a peer, and `data/` is edited by
people. Nothing can be added to that side without first reversing an ADR. Worth writing down,
because "no propose tools" reads like an oversight and is actually the load-bearing consequence
of two earlier decisions.

**The one real risk ran the other way, and it is not a robotics risk at all.** `urdf.py import`
takes a path and reads it. Exposed as an MCP tool that is an **arbitrary file read** wearing a
domain-specific name — in a repo whose threat surface is otherwise "might return a number that
is wrong". It stays on the CLI, where the person running it chose the file, and there is a test
that fails if any tool ever grows a path-like parameter. A text-taking variant would be a
different thing and is the right shape if the need is real.

**And the failure mode an MCP surface invites most.** Every tool returns its whole verdict
object rather than a bare boolean or a bare distance, because a tool result is usually
summarised by a model before a human reads it, and a stripped caveat is exactly what a summary
drops. `list_actuators` surfaces `capacity_derivable` for the same reason: on the one real
record in `data/`, it is `false`, and that is the single most consequential fact about that
actuator.

Sample counts are clamped at 200,000 **and the clamp is reported**. Silently honouring a
pathological N is a denial of service; silently refusing it is a lie about what was computed.

---

## [2026-08-22] build | The refusals stop being conventions

A Rust binding, following [[openpartscore]]'s codegen discipline. Copying that pattern gets a
working crate; the reason this one was worth building is what it does *beyond* the pattern.

**Every refusal in this repo was a convention.** Stall torque must not reach a capacity
derivation — enforced by a validator, a docstring and an ADR, all of which are advice you have
to have read. Absent limits mean unknown — same. Radians here while Oh-Ben-Claw's `ServoAngle`
is degrees — named in ADR-0010 as a seam and enforced by **nothing at all**.

A type system enforces at compile time what a docstring enforces by hope. The JSON cannot carry
that. The binding can, and ADR-0017 makes it:

- **`Radians` and `Degrees` are distinct newtypes.** Passing degrees where radians are required
  does not compile. This is the mechanism that makes ADR-0010's "conversion at exactly one
  place" true rather than aspirational, and the failure it prevents is a mechanism commanded to
  57 times the intended angle.
- **`StallTorque` and `ContinuousTorque` are distinct with no conversion between them.** Not a
  shared struct with a flag, not a `From` impl, not a feature flag — there is deliberately no
  way to turn one into the other. A consumer who wants the 30-50% rule of thumb must write that
  arithmetic in their own code, where a reviewer sees it.
- **Unknown stays `Option`, with no `limits_or_default()`.** One convenience accessor would undo
  inherited invariant #3 in a single function.

**The best part is that three of those guarantees are testable.** They are compile-time
properties, which normally means they can only be asserted in a comment — and a comment is
exactly what gets deleted by the next person who wants the conversion. Rust's `compile_fail`
doctests execute them: `cargo test` now runs code that *must not compile* and fails if it does.
So "you cannot convert stall torque to continuous torque" is a test result rather than a claim.

That felt like the whole point of the exercise in miniature. This repo's argument has always
been that a refusal only counts if something enforces it, and every previous enforcement here
has been a validator that a person could choose not to run.

**On the emitter's shape, which differs from OpenPartsCore's.** Theirs is only data, so
regeneration is mechanical. This one is data **plus hand-written types**, carried in the emitter
as a literal header. That creates a trap worth naming: editing `bindings/rust/src/lib.rs`
directly *works*, right up until the next regeneration silently reverts it. The header says so
and there is a test asserting the types live in the emitter.

**Rejected.** `serde` derives behind a feature flag — genuinely convenient, and it starts the
dependency conversation OpenPartsCore's zero-dep decision exists to end; the JSON is right there
and is canonical anyway. And emitting a Track 0 limit table in Oh-Ben-Claw's config format,
which ADR-0010 already rejected and which stays rejected: writing another repo's format takes
that format as a dependency.

**Rejected, and this one is the sharpest.** Any `pub fn is_safe(...)` or similar predicate.
Nothing in this crate may look like a safety authority — Track 0 is the safety authority, this
is a data model, and a function named like a permission is precisely how those two get confused
by a caller in a hurry. There is a test that fails if one appears.

**What is still upstream's call.** Oh-Ben-Claw actually consuming the binding. That is the same
unfinished half [[openpartscore]] has been waiting on since it shipped its own Rust crate — the
registry contract exists, and the consumer switching to it is a different repo's decision.

---

## [2026-08-22] ingest | The last sourcing topic closes by proving the number does not apply

Gearbox efficiency was held to the end of the reading list on purpose. Every other topic
licensed a **decision**, and a decision can rest on a survey. This one would license a **number**
— an efficiency multiplies a derived capacity and turns ADR-0004's static upper bound into an
estimate — so only a vendor document with a stated method was admissible.

One was found: Harmonic Drive's FR Gearing engineering data. It closed the topic in two
directions, neither expected.

**Efficiency is a five-variable curve, in the vendor's own words:** *"Efficiency varies depending
on input speed, ratio, load level, temperature, and type of lubrication."* Eight charts, no
scalar. And the curves are themselves conditional — published at the torque rated for 2,000 rpm,
then corrected again by a load factor. The worked example lands at **58% at rated load and 50% at
60% of rated**, against the "80 to 90 percent" the trade literature quotes. The rule of thumb is
not imprecise; on the vendor's own figures it is wrong by nearly a factor of two, in the unsafe
direction.

So `gearbox.efficiency` as a scalar was the **third instance of the same defect**: a quantity
varying over an operating envelope, stored as one number. ADR-0004 deleted scalar `payload_kg`
because capacity varies with pose. ADR-0014 made torque an array because it varies with voltage.
Three times now, and the pattern is worth naming: *whenever a field holds one number for a
quantity that has an operating envelope, the field is wrong and the envelope is the fix.*

**But the sharper half is that efficiency does not apply here at all.** Efficiency curves
describe a gearbox that is **turning** — they are indexed by input speed and published at
1,000–2,000 rpm. `hold` is a *static* derivation, and a mechanism holding a pose has an input
speed of **zero**. There is no efficiency curve at zero speed. What governs a stationary
geartrain is starting and backdriving torque, which the same document publishes as separate
tables of ranges spanning better than an order of magnitude.

Applying a running efficiency to a held pose would be wrong **in kind**, not in value. So the
last open sourcing topic closes by establishing that the number it would have licensed does not
apply to the computation it was wanted for — and ADR-0004's bound stays a bound for a *sourced*
reason rather than an unmodelled one. The ROADMAP entry moves from "gearbox efficiency" to
"starting and backdriving torque", which is a different field nobody has yet needed.

**And a distinction the platform has never made.** On torsional stiffness, the same vendor:
*"The values quoted are the average of many tests of actual units. The spring rate of an
individual unit may vary within approximately ±30% of the average."*

A cited value has meant "somebody published it, and here is where" everywhere in this platform.
This is a vendor stating **in a datasheet** that their published number describes a *population*
and an individual specimen may sit 30% away from it. A `mass_g` from a datasheet and a `mass_g`
from a scale are different kinds of claim, they currently validate identically, and a derivation
chaining several model-typical figures compounds a spread nobody declared.

ADR-0018 adds `basis` — `model-typical` or `this-unit`, absent meaning unknown — plus an optional
`spread_pct`, and makes **a derivation report the weakest basis it consumed**. That last part is
the expensive one and the reason the ADR is worth writing: most answers now grow a line saying
they rest partly on population averages, which is unglamorous and true.

**Deliberately not done:** sweeping `basis` across the other schemas. Applying it to `mass_g` and
the rest without a source per field would be guessing at which values are population figures —
the exact error the field exists to prevent.

**Also found, and recorded rather than fixed.** The vendor's method statement for starting and
backdriving torque — *"based on actual tests with the component sets assembled in their housings,
and inclusive of friction resistance of oil seals, and churning of oil"* — is the reference
example of the `how_determined` standard this repo asks for, written by a vendor. Worth keeping.
And the "no standard governs backlash measurement" claim is **secondary-sourced only**; it is
consistent with everything primary here and is not strong enough to build a rule on, so backlash
gained nothing this pass.

**A debt this pass exposed.** OpenCircuitCore, ClawCam and Project BINGO were read on 2026-08-22
during the platform survey and **none of them has an entity page**. The index said they were
unread, which was false. Corrected, and the gap recorded in [[open-questions]] with what was
actually learned — notably that BINGO's `REFUSAL-CATEGORIES.md` is what question 5 has been
waiting for. The wiki's own ingest rule says a source that touches pages updates them in the same
pass; this one did not, twice over.

**The reading list is now empty.** That is not the same as the wiki being finished. It means
every question written down at the start has a source behind its answer. Three of the eight
closed as *refusals* — self-collision, workspace volume, efficiency-for-static-hold — and a topic
answered by establishing that the thing should not be done is answered. The next questions will
arrive the way ADR-0014 and ADR-0018 both did: from one datasheet meeting one schema field, not
from thinking harder.

---

## [2026-08-22] ingest | Paying the entity-page debt, and finding PD-5 was already unblocked

Three entity pages — [[opencircuitcore]], [[clawcam]], [[project-bingo]] — for three peers read
during the opening platform survey and never written up. The index had been claiming they were
unread, which was false in one direction and the debt was real in the other.

**The failure is worth keeping rather than deleting.** This wiki's ingest rule says a source that
touches pages updates them **in the same pass**. That did not happen, across two sessions. The
knowledge did not vanish — it went into ADRs and commit messages — but a wiki exists precisely to
stop knowledge living there, where nobody looking for "what does OpenCircuitCore do" will find
it.

**Writing them up surfaced things that were not obvious while reading.**

[[opencircuitcore]] is the origin of an invariant this repo inherited. Its ADR-0001 chose atopile
and its ADR-0003 dropped it **the same day**, on evidence — that is PD-1, and it is where
[[inherited-invariants]] #8 comes from. Two of its decisions also parallel ClawBot's without
either repo knowing: *"a custom DRC rule ships only once it has been proven to fire"* is exactly
what 31 negative tests are for, and *"the MCP surface inspects and verifies, it does not
regenerate"* is the neighbour of ADR-0016. Three repos converged on reads-execute /
effects-ask — [[clawcam]] runs the fully populated version with 35 auto-approved read tools and
11 gated write tools, while ClawBot's is degenerate because its propose side is empty.

**And PD-5 turned out to be unblocked already.** [[project-bingo]]'s
`v3/specs/REFUSAL-CATEGORIES.md` is the taxonomy that platform decision assigns to it, and it
names design-time assistants explicitly — [[opendesigncore]], OpenCircuitCore, deployment tools.
ClawBot is absent only because it did not exist when the spec was written.

Two of the nine categories land squarely here: `weapons.other`, and `regulated.medical`, which
explicitly covers **load-bearing prosthetics**. A prosthetic limb is a mechanism, and it is the
most likely thing anybody would describe with this schema that carries a policy category at all.

**One mechanic cuts directly against this repo's grain**, and that is the interesting part. In
BINGO, an asset manifest with no `policy_categories` means `none` **as a declaration**, carrying
the same fraud consequences as misdeclaring a licence. Everywhere in ClawBot, absent means
*unknown*. Both are right in their own frame — a declaration is a claim somebody makes, an absent
measurement is one nobody took — and a ClawBot position has to choose deliberately and say why.
Question 5 is rewritten to name the three things that actually need deciding rather than "read
the spec".

**Also corrected:** [[ecosystem-position]]'s peer table still said OpenCircuitCore was "not yet
read", and listed only [[oh-ben-claw]] as sitting outside the five. [[clawcam]] and
[[project-bingo]] sit outside it too, and BINGO owns two vocabularies the Open\*Core repos borrow
— the machine record that [[openbuildcore]]'s schema copies field-for-field, and the refusal
taxonomy.

**One line worth recording for what it is not.** BINGO's README marks its own seams honestly, and
among the stand-ins is "the perception/reach work still spec-only". That is the closest thing in
the whole ecosystem to a request for what ClawBot does, and it is **not one** — it is BINGO
describing its own unbuilt half, in its own domain. ADR-0001's admission that nobody has asked
for this repo still stands, and finding a phrase that could be read as demand is exactly when to
check whether it is.

---

## [2026-08-22] build | PD-5, and two absence rules that are both right

ClawBot's position on platform decision PD-5, which it has owed since the day it was created.
The decision is ADR-0019 and it turned on a collision that looked like a contradiction and was
not.

**The collision.** Everywhere in this repo, absent means UNKNOWN. In [[project-bingo]], an asset
manifest with no `policy_categories` means `none` **as a declaration**, carrying the same fraud
consequences as misdeclaring a licence. Two peers, opposite rules, same word.

**Both are right, because they govern different kinds of field, and noticing that was the whole
decision.** This repo's absent-means-unknown covers **measurements** — a joint limit nobody
sourced, a torque nobody published. Nobody can *declare* a joint limit; you measure it or you do
not. A policy category is not a measurement. It is a **statement by the author about their own
intent**, and the author always knows. There is no honest "I do not know whether this is a
weapon".

So the field's nature is BINGO's. What ClawBot refuses is to **supply** the declaration: absent
stays undeclared, and is never converted to `none` at the boundary.

**Why the field exists at all is mechanical, not moral.** `manifest.py` already emits into
[[openbuildcore]]'s vocabulary, and OBC's machine records already mirror BINGO's field-for-field.
There is a real path from a robot record to a fabrication job. So a manifest carrying no
declaration is not neutral — it makes the `none` claim at the far end, invisibly. That is the
invisible-choice failure ADR-0014 removed from torque lookup, in a place where the consequence is
legal rather than thermal.

**Where the refusal lives.** Not in the derivations. `fk`, `reach`, `hold` and `can_it` do not
consult the policy field, because computing kinematics is not fabricating and the mathematics is
in every textbook — a repo declining to multiply matrices would be theatre. The refusal is at the
**output boundary**, the same place ADR-0007 put the URDF refusal: decline to emit the artifact a
downstream system would act on.

`manifest.py --as-project` therefore refuses twice — for an undeclared record, and for the four
categories BINGO marks refuse-network-wide. The second is *not* ClawBot adjudicating: it is
declining to produce a document with no valid destination, since no node can accept such a job
under any configuration. The message says so, names the taxonomy version it judged against, and
states that BINGO is authoritative.

**The case to design against is a prosthetic, not a firearm.** `regulated.medical` explicitly
covers load-bearing prosthetics and is **node-opt-in, not refused** — so a declared prosthetic
emits normally and carries its category to a node that has opted in with certification context.
The design is correct if it lets that person work while making the declaration explicit, and
wrong if it treats every category as a prohibition. Checked with a test named for it.

**Three refusals recorded, and the last is the one that matters most.** No `policy_categories`
enum in the schema — that forks a taxonomy whose own spec says growth needs a spec revision, and
a forked registry that drifts is the failure [[openpartscore]] exists to end. No inference of a
category from geometry, link lengths or a name — a repo guessing "this looks like a weapon" from
a bounding box would be manufacturing exactly the confident unfounded judgement the invariant
refuses. And **no refusal to describe**: a notation that cannot express a thing does not prevent
the thing, it prevents the thing being described accurately, and it would put this repo in the
business of deciding what may be written down.

**A gap found while implementing, worth reporting upstream.** [[openbuildcore]]'s project schema
is `additionalProperties: false` and has **no field for a policy declaration**. So the
declaration cannot travel as *data* through `--as-project` — it goes as prose in `description`
and is not machine-readable downstream. The emitter prints that as a note rather than smuggling
the field in, and the test that proves it also proves the emitted document still validates
against OBC's real schema.

**On the stance copy.** The four refuse-network-wide ids are held here as a **dated copy** of
BINGO's defaults, cited to the spec version and marked as a copy. It will go stale. That is
bounded on purpose: it decides only whether ClawBot emits a document, never whether a job is
accepted, and BINGO re-checks at matching time against the list frozen into the job. A stale copy
makes this repo slightly over- or under-cautious about emitting, and never makes a routing
decision.

The open question that has been sitting at number 5 since the repo was created is closed.

---

## [2026-08-22] build | The binding was missing the field its own argument rested on

ADR-0017 justified the Rust binding almost entirely on one seam: `Radians` and `Degrees` are
distinct types, so passing degrees where radians are required does not compile, and
[[oh-ben-claw]]'s `ServoAngle` is in degrees.

**It shipped without the field that seam lives on.** The crate emitted `Robot` and `Actuator` and
no `Harness` — so `harness.channels.zero_offset_rad`, the one angular value a runtime reads on
its way to commanding a servo, was not in it at all. The binding could not be used for the thing
that justified it.

That is a gap in execution rather than a change of mind, and it is worth recording because **the
ADR read as complete while the artifact was not**. An ADR describes a decision; it does not
witness that the decision was carried out. Nothing in the test suite noticed, because every test
checked what the crate *did* contain.

ADR-0020 closes it and settles two things a future reader would question.

**Why arithmetic lives in a data crate.** `Channel::actuator_angle(Radians) -> Radians` applies
`inverted` and `zero_offset`. At a glance that looks like ClawBot computing a command, which
ADR-0010 forbids. It is not: **inversion and zero offset are part of the contract, not part of
the decision to move.** They are facts about how the hardware was physically installed, fixed for
the life of the build, and arithmetic every consumer would otherwise write identically — which
means every consumer would eventually write one of them differently. Nothing reaches hardware,
chooses a target, or decides when to act.

It returns **radians** deliberately. Returning degrees would move the boundary inside the crate
and the consumer would stop seeing it, which is the opposite of ADR-0017's argument. The seam
stays one legible line: `Degrees::from(channel.actuator_angle(target))`.

**Why assemblies are not emitted.** A DAG of bench steps — fasteners, torques, what cannot be
undone — is for a person, and no runtime consumes it. Emitting it would be data nothing reads,
which is what the zero-dependency argument is against. It stays as JSON where a build-guide
renderer can find it. Recorded so the absence reads as a decision rather than an oversight,
which is exactly the mistake this entry is about.

**The best thing in the change is a type, not a function.** `CableRun::permits_full_travel` is
`Option<bool>`, so the compiler will not let a caller collapse *nobody checked* into *does not
permit* without writing the match arm. ADR-0012's tri-state, enforced rather than documented —
second only to the `compile_fail` doctests.

**Honest about the data.** `HARNESSES` is empty, because `data/harnesses/` is. The harness tests
exercise the type API rather than real records, and say so, instead of a fixture pretending to be
data. 147 Python tests, 33 Rust tests.

---

## [2026-08-22] lint | First lint pass, and two of the first three findings were bugs in the lint

`CLAUDE.md` has described a Lint operation since the day this wiki was created — contradictions
between pages, claims a newer source has superseded, orphan pages, concepts with no page, and
`TODO(source)` markers waiting long enough to chase. It had never been run. Eleven log entries
in one day is when a wiki starts contradicting itself, so: run.

**Two of the first three findings were false positives, and they are findings about the
instrument rather than the wiki.**

A naive `[[target]]` scan flagged `[[links]]`, `[[page-name]]` and `[[wiki-link]]` as broken.
All three are prose *about* the wiki-link syntax, already correctly inside code spans — in
`CLAUDE.md`'s own grounding rule, among others. **A lint must strip fenced blocks and inline
code before matching, or it reports the schema that defines the syntax as violating it.** With
code spans excluded there are **zero** broken links.

The orphan check flagged `raw/platform/llm-wiki.md`. That is a category error: raw sources are
not wiki pages, they are cited **by path** and deliberately never by `[[link]]`, so every source
in `raw/` is an orphan by construction and always will be. The orphan check applies to
`entities/`, `concepts/` and `sources/` only. With `raw/` excluded there are **zero** orphans.

Worth keeping both, because a future automated lint will make the same two mistakes.

**Three real defects, all of the same species: a document describing its own state, outrun by
the state.**

1. `index.md` claimed **7** log entries. There were 11.
2. `open-questions.md` claimed **three** `TODO(source)` markers, "all in [[clawbot]] and
   [[ecosystem-position]]". There is one, in [[clawbot]]; the ecosystem-position markers were
   removed during a rewrite and the count was not updated.
3. The surviving marker's condition has been **met**, and the page did not say so.

**That third one is the finding worth the whole pass.** The marker reads "Nobody has asked for
ClawBot yet." Since it was written, `crates/obc-body` appeared in [[oh-ben-claw]] and consumes
ClawBot's Rust binding to derive Track 0 limits from a cited body model. Literally, a peer now
reads ClawBot data.

The marker stays, and [[clawbot]] now explains why: that crate was written in the same session,
by the same author, at the same person's direction, and is deliberately unwired — its own
ROADMAP entry says the first condition to wire it is *not Oh-Ben-Claw's to meet*, because
`data/robots/` here is empty. **Building your own consumer and then citing it as demand is
circular**, and it is precisely the self-satisfying move a provenance wiki exists to catch.
ADR-0001's admission is unchanged.

Recorded as an amendment rather than a deletion, because the next reader will see a consumer
exists and reasonably conclude the marker is stale. A marker that survives its own trigger
condition needs to say why, or it will not survive the reader after next.

**Checked and clean:** every page carries `title`, `type`, `updated` and `sources` frontmatter;
no broken `[[links]]`; no orphans among the linkable pages; entity, concept and source counts in
`index.md` match the filesystem. The hub check is unremarkable and slightly telling —
[[opendesigncore]] is the most-linked page at 16 inbound, ahead of [[clawbot]] at 10, which is
what a repo that inherited most of its discipline from a peer should look like.

**Not checked, and honestly out of reach of a script:** contradictions between pages that are
both internally consistent, and "concepts mentioned repeatedly but with no page of their own".
The second needs a judgement about what deserves a page, and the frequency counts a script can
produce are dominated by the vocabulary every page shares. Left for a human, and named here so
the omission is visible rather than implied by a clean report.

---

## [2026-08-22] build | The fourth time the same defect showed up, and the first time it was caught before the field was written

ADR-0018 closed gearbox efficiency by establishing it is the *wrong quantity* for a static hold —
efficiency curves are indexed by input speed, and a held pose has none — and named what would
actually be needed. This is that: **starting and backdriving torque**, from the same Harmonic
Drive document.

**The shape decided it.** For an FR 40, starting torque is 3–50 N·cm and backdriving torque is
7–190 N·m. Not a value with a tolerance — a range spanning better than an order of magnitude,
with the vendor's own method attached.

That is the **fourth** appearance of one defect, and the first time this repo met it *before*
writing the field rather than after. ADR-0004 deleted scalar `payload_kg` (varies with pose).
ADR-0014 made torque an array (varies with voltage). ADR-0018 removed scalar `efficiency`
(varies over five variables). Here the variation is not over an operating envelope at all — it is
**unit to unit**, which is why a range is the right shape rather than an index, and why
ADR-0018's `basis: model-typical` belongs on it.

**The finding worth keeping: the two ends answer opposite questions.**

*"Can this hold a load unpowered?"* is answered by the **minimum** — your unit might be the loose
one, and assuming otherwise means a load that slips. *"Will this back-drive when I need it to,"*
for hand-guiding or a fault that must not lock a joint, is answered by the **maximum** — your
unit might be the stiff one.

A single figure cannot serve both. Picking an end silently is wrong in a direction that depends
on **a question the record does not know the caller is asking**, which is why the range is stored
whole and neither the schema nor the Rust type offers an accessor that picks one.

**And then the discipline bit, which was the harder call.** Neither field feeds a derivation.

The tempting inference is right there: *a load below the backdriving minimum is held by the
geartrain with no actuator torque*. It is probably true. It is also **a physical claim this repo
has no source for** — the Harmonic Drive document publishes the numbers and their test method and
says nothing about a relationship to a statically held load, and nothing else read here does
either. Writing it into `hold` would be exactly the plausible uncited reasoning the invariant
refuses, and more dangerous than most, because its failure mode is a joint that lets go rather
than a wrong number on a screen.

So `hold` is unchanged. What changed is that the data is here for when a source arrives.

**A smell, named rather than ignored.** This repo now carries *three* recorded-but-unused fields:
`measured_efficiency`, `harness.service_loop_mm`, and these two ranges. That is a real pattern and
it could become hoarding. The defence is that each arrived because a **source** did, not because
a feature was wanted, and each has a written condition for becoming useful. A fourth without one
is the point to ask whether the schema has started collecting rather than modelling — recorded in
the ROADMAP so the question gets asked rather than drifted past.

Rejected: a `typical` value beside the range. It would be read as the answer, the range would
become decoration, and no vendor publishes one — a midpoint invented here would be a number with
no source sitting between two that have one.

---

## [2026-08-23] build | Three promises came due at once

Seven pull requests merged across five repositories, and three things this repo had written down
as *waiting on a merge* stopped waiting. All three were commitments made in prose — the kind that
quietly become false rather than loudly failing.

**The `part_id` resolves.** [[openpartscore]] merged `electronic/dynamixel-xm430-w350`,
contributed from here because the registry had no entry for it. The actuator record's note said
"No part_id: OpenPartsCore has no entry for this actuator", which stopped being true the moment
that merged. Now cited, and the two records sit side by side sharing **zero fields** — upstream
carries identity, mass, gear ratio, sensor and operating temperature; this carries what the
actuator does in a mechanism. Open-question 3 closes on evidence rather than argument.

Its residual half answers itself in the negative. *Should a record require a `part_id`?* No: the
XM430 was uncatalogued for a day and the record was correct throughout.

**The declaration travels as data** (ADR-0022). ADR-0019 recorded that OpenBuildCore's project
schema was `additionalProperties: false` with no slot for a policy declaration, so a declared
category could only go as prose in `description`. Reported as OpenBuildCore#9, fixed by its
ADR-0007, merged.

What made the change three lines rather than a migration is worth keeping: **ADR-0019 refused to
smuggle the field into `description` as a field, and refused to invent a name.** So when the real
field arrived it already had the name BINGO had specified, and nothing had to be unpicked.

The `taxonomy_version` deliberately does *not* travel. This repo requires it because an id
without its list version is a string whose meaning lives elsewhere; BINGO solves the same problem
by freezing the list hash into the **job** at order time. Adding an asset-level version upstream
would fork a working mechanism, so the version stays here and the id travels alone into a system
that pins it.

**Two tests rewritten rather than deleted**, and the docstrings keep the history, because the
failure they used to guard is the interesting one: *a declaration that does not travel as data
reads, downstream, as no declaration at all* — and BINGO treats an absent declaration as `none`
**declared**, with fraud consequences. The hazard did not go away. It moved upstream, to where
the field now exists to prevent it.

**A property of the CI design got exercised for the first time.** ClawBot's workflow checks out
[[openbuildcore]]'s `main` **at run time**, so that repo's schema change could have turned this
repo red with no commit here. It did not — `policy_categories` is optional, so every previously
valid document stayed valid — but the coupling is real and now demonstrated. It is the price of
the two seam tests validating against a peer's *own* schema file rather than a copy, and the copy
would have been worse: it would have gone stale silently instead of failing loudly.

## [2026-08-23] ingest | Backlash: the under-sourced half of the last sourcing topic

Sources: Nabtesco Motion Control, "Does Zero Backlash in Gearboxes exist?"; Nabtesco FAQ glossary,
"Backlash"; ANSI/AGMA 2002-D19 listing (title only — paywalled, not read). → [[backlash-measurement]]

**Why this ingest happened at all.** The reading list was empty and nothing was asking for work.
But [[gearbox-efficiency]] had closed with one claim explicitly marked *"secondary sourcing, and
flagged as such"*, and `backlash_rad`'s schema description carried the same flag in capitals. A
claim that is recorded as under-sourced is not finished; it is *honest*, which is different. The
flag was doing its job by still being there to notice.

**What came back.** A vendor describing its own definition against the field's: *"many gearbox
manufacturers choose to use the standard definition of backlash ... Nabtesco's definition includes
not only the mechanical gap between parts, but also ... angular displacement that occurs due to
loading."* That is the disagreement in writing, from a party to it, which is a better class of
evidence than a trade article reporting that it exists. The same vendor publishes 0.1–0.3 arc·min
and 0.3–0.6 arc·min for one shaft, differing only by which definition applies.

**And a correction to the shape of the original claim.** "Backlash has no measurement standard"
was too strong: ANSI/AGMA 2002-D19 is titled *"Tooth Thickness and Backlash Measurement of
Cylindrical Involute Gearing"*. It appears to address backlash as gear-mesh geometry rather than an
assembled reducer's output figure — but the scope is paywalled and **was not read**, so the page
says "appears to answer a different question" and refuses to say "no standard covers assembled
reducers". Half the original claim survives as primary; the other half is now known to have been
imprecise.

**Still open, and recorded as unknown rather than absent:** whether Harmonic Drive defines lost
motion at a different percentage than Nabtesco's 3%. Its FR engineering data is already in this
repo's citation chain and would be the natural second vendor, but the PDF resisted text extraction
with the tooling to hand. One look by a human with the file open would settle it.

**No ADR.** Nothing was decided that ADR-0018 and ADR-0021 had not already decided. A note's
evidence standing improved, and the schema description now says primary where it said SECONDARY.
Changing a description is not changing a rule, and the rule — absent means UNKNOWN — is untouched.

## [2026-08-23] ingest | The second vendor was in the citation chain all along

Source: Harmonic Drive LLC, FR engineering data (already cited by [[gearbox-efficiency]]).
→ [[backlash-measurement]]

The entry above closed the backlash claim as half-sourced and left one thing open: whether Harmonic
Drive defines lost motion at a percentage other than Nabtesco's 3%. It was recorded as **unknown
rather than absent**, because the PDF would not yield to any tool to hand.

**It does not define lost motion at all.** Neither "lost motion" nor "hysteresis" occurs in the
document. It defines backlash as *"pure play existing between the input and output"*, *"measured at
output with input locked"* — which is exactly the definition Nabtesco named as the one "many gearbox
manufacturers choose to use" and distinguished its own from. Both parties to the disagreement are
now on the record, and one of them was already in this repo's bibliography.

**The finding is better than the one being looked for.** The question assumed the two vendors
measure the same quantity at different loads. They do not: Nabtesco reads one arc-minute figure at
3% of rated torque, while Harmonic Drive publishes pure play with no torque named, plus a
three-region spring rate for the low-torque behaviour. The quantities do not correspond and cannot
be converted. "Not comparable without their methods" turns out to understate it.

**Method, recorded because it constrains what may be quoted.** The PDF was read by decompressing its
content streams with `zlib` and undoing a subset-font shift by hand — no PDF library was available.
That recovers prose and **destroys numerals**: the ±30% spring-rate variation comes back as
"approximately ___ of the average". So the page quotes prose only and takes **no number** from this
reading. The decoder was validated first against a sentence already verified independently — the oil
seals and churning-of-oil quote — and reproduced it exactly.

## [2026-08-23] ingest | The enum promised a type the fields could not express

Source: STEPPERONLINE and DHM Online listings for the 17HS19-2004S1.
→ [[stepper-torque-index]], ADR-0023

**Where the question came from.** Not from the reading list, which is empty, and not from thinking
about the schema. It came from a build: a pan-tilt was being specified, the parts on the bench
included steppers as well as servos, and checking whether the schema could hold one turned up that
it could not. `type` has accepted `stepper` and `bldc` since the schema was written, while every
torque row required `at_volts`.

**The arithmetic that settled it.** STEPPERONLINE publishes holding torque 59 Ncm, rated current
2.0 A, phase resistance 1.4 Ω, and voltage 2.8 V. The last is the product of the middle two,
exactly. A second listing omits voltage altogether. So the "rated voltage" is not a measurement
condition, it is a derived number — and writing it into `at_volts` would make one field name mean
two different quantities depending on which actuator you were reading.

**Why this shape keeps recurring.** Third time: ADR-0014 came from a voltage, ADR-0018 from an
efficiency, ADR-0023 from a current. Each was one datasheet meeting one schema field, which is
exactly what [[open-questions]] said would keep happening once the reading list emptied — *"not
from thinking harder, but from one datasheet meeting one schema field."* The prediction is holding
up well enough to be worth trusting: **the next schema gap will most likely arrive the same way,
from the next real part, rather than from review.**

**Recorded as not-stated rather than decided:** whether a holding torque is sustainable. Neither
listing gives a continuous or thermal rating, so a stepper gets `continuous_torque_nm: null` and
underivable capacity, the same as the XM430 and the MG90S. Steppers are commonly run at rated
current continuously and nothing here contradicts that — there is simply no source for it, and the
refusal is about the evidence, not the physics.

**A tooling note worth keeping.** The manufacturer's PDF datasheet could not be read at all: it is
published as a vectorised drawing with zero text operators, so the `zlib` stream extraction that
worked on the Harmonic Drive document returned nothing. The figures came from product listings
instead. That is the second PDF this month to resist reading for a different reason, and the page
says which of its numbers came from where.

## [2026-08-23] finding | The warning in the MG90S record was right about its own hardware

Source: the owner, on inspecting the parts. → ADR-0024

`towerpro-mg90s` closed its note with a hedge: the MG90S is heavily cloned, these figures describe
TowerPro's population, and if the unit on the bench is not a verified TowerPro then the record is
cited for the wrong thing. **It was not.** The servos are unbranded — marked `MG90S` and
`Micro servo`, no manufacturer mark.

**The measurement had already said so and nobody read it that way.** Total height came to 26.3 mm
against TowerPro's own 28.5 mm and 35.5 mm. That was recorded as *"the two TowerPro documents
disagree with each other"*, which was true, and the more useful reading — *the part in hand agrees
with neither, so it may be neither* — was available at the time and not taken. A discrepancy was
treated as evidence about the documents when it was also evidence about the object.

**Why `basis` was the wrong tool, which is the substance of ADR-0024.** [[gearbox-efficiency]]
established `basis` from Harmonic Drive's ±30% statement: a published figure may describe a
population rather than your unit. That presumes your unit is drawn from the population. A clone is
not, so there is no population it is typical of, and marking the figure `model-typical` and using
it anyway would assert exactly what is unknown — while looking like careful practice.

**The outcome is a record whose evidence is a caliper rather than a document**, and it is *better*
evidence than the branded record it replaced, because a measurement of the object in hand outranks
a datasheet about a different object. Worth naming, since this wiki's discipline is easy to read as
"prefer the published figure" — the actual rule is prefer the source that describes the thing you
have.

## [2026-08-23] lint | Sweeping the type enum, because waiting for parts is not a plan

Sources: STEPPERONLINE / DHM listings for the 17HS19-2004S1; Pololu 34:1 25D MP 12V product page;
iPower GM4108H-120T listings. → [[open-questions]], `tests/test_coverage.py`

Four schema gaps had been found by hardware arriving — ADR-0014 from a voltage, ADR-0018 from an
efficiency, ADR-0023 from a current, ADR-0024 from an unbranded case. The first three share a
shape: **an enum value nothing had ever tried.** That set is finite, so it was measured rather
than waited on.

`type` has six values and `data/` exercised two. Sweeping the other four against real listings
found **three more gaps in one sitting** — a gearbox torque limit with no field, a BLDC torque
published as a range at a current, and no force field at all for a linear actuator. Details on
[[open-questions]].

**None fixed.** Three schema changes in an afternoon would be three decisions made in a hurry, and
each wants a properly-read datasheet rather than a product listing. The change is that they are
visible: a test fails if an enum value is neither exercised nor declared with a reason, and fails
again if a declaration outlives its gap — a known-gap list that goes stale being the disease it
treats.

**What the method cannot do, recorded so nobody over-trusts it.** It finds places where the schema
promises what it cannot deliver. It could never have found ADR-0024, where the defect was that the
part in the drawer was not the part on the datasheet. That needed looking at the object, and the
measurement that hinted at it had already been taken and read the wrong way. Enumerable surfaces
can be swept; contact with the world cannot be simulated.

## [2026-08-23] decision | The sweep's first close, and it found something bigger than the gap

Source: Actuonix L12 vendor and retailer specification listings. → ADR-0025, [[open-questions]]

The enum sweep flagged `linear-actuator` hours earlier: the word **force** did not occur anywhere
in the actuator schema, while `type` had accepted the value since the schema was written. This
closes it — and unlike the four gaps before it, **it was found by the method rather than by a part
arriving.** That is the sweep doing the job it was added for.

**What the L12 turned out to publish** is five distinct quantities, not one: max force lifted 80 N,
a 20% max duty cycle, back-drive force 45 N, max static force 200 N, and a peak power point of 62 N
at 3.2 mm/s. ADR-0025 takes the headline and the duty cycle, and names the rest.

**The duty cycle is the part worth remembering.** `thermal_basis` already carried duty-cycle prose,
but only on a continuous row — so it had nowhere to live precisely when the continuous row is the
thing that does not exist. Actuonix stating "20%" is a vendor explaining why its own headline is not
a continuous rating, which is more than either servo vendor offered, and it is now recorded as data
rather than left in a note.

**The larger finding.** Four other L12 figures have no home, and the reason is not four separate
oversights: `no_load_speed_rad_s` is angular, `gearbox.backlash_rad` is radians, back-drive torque is
rotary, the efficiency curve is rotary. **The schema is rotary-shaped throughout.** Force was the
largest mismatch, not the only one — one assumption made once, before anything linear existed.

**Where the line was drawn, and why.** Before ADR-0025, nothing about a linear actuator could be
written down. After it, the headline can, and what cannot is named in a fixture where the next
person will find it. Difference in kind, not degree — the same place ADR-0023 stopped. Modelling all
five figures would have meant deciding the rotary counterparts of two of them in the same afternoon,
asymmetrically, which is how a schema acquires a lopsided half.

## [2026-08-23] decision | The sweep's own entry was wrong, and nothing could have caught it

Source: iPower GM4108H-120T specification table, read verbatim from the vendor listing.
-> ADR-0026, [[open-questions]]

The coverage sweep declared `bldc` a schema gap. **It was not one.** ADR-0023's
`holding_torque_nm` had accepted a current-indexed torque all along and names `bldc` explicitly.
The unrecordable thing was one vendor's figure, not the type.

**What the vendor actually publishes:** *"Load torque(g-cm): 1200-1800"* at *"Load current: 1.5A"*,
and no statement anywhere of what the two ends mean. Storing that in ADR-0021's `torqueRange` --
whose description reads *"varies UNIT TO UNIT rather than over an operating envelope"* -- would make
the schema assert something the source never claimed.

**The notation is the only evidence, and it is not pushed further than it goes.** One page uses
`124+/-0.5g` and `11.1 ohm +/-5%` for tolerances, `513~567` for a speed span, and a plain hyphen for
the torque. None is explained. A vendor who has a tolerance notation and did not use it here is not
obviously stating a tolerance -- enough to refuse a collapse, not enough to say what the range is.

So the figure is **absent**, with the span in `note`. Absent means UNKNOWN, which is exactly the
state. And `how_determined` is now refused when it states nothing -- `unknown`, `not stated`, `n/a`,
`tbd` -- because that was the tempting way through: a required field can always be satisfied with a
word, and the record would then *look* explained.

**The finding worth carrying forward is about the sweep itself.** Its gap list's reasons are prose,
and both staleness guards ask only whether a type is exercised -- never whether the stated reason is
true. `bldc` sat there for an afternoon carrying a wrong reason while every check in the file passed.

That is not fixable: a test that verified prose would verify nothing. It is a **limit to state where
the list lives**, so the next reader treats those entries as claims to re-read rather than
conclusions to trust. The comment above `ACTUATOR_GAPS` now says so. A tool built this morning to
catch bad reasoning produced some of its own by lunchtime, which is worth knowing about every tool
of this kind.

## [2026-08-23] decision | The last gap, and this time the stated reason held

Source: Pololu 25D Metal Gearmotors family page. -> ADR-0027, [[open-questions]]

After [[open-questions]]'s `bldc` entry turned out to carry a wrong reason, the `dc-gearmotor`
entry beside it was re-read rather than trusted. **It held.** Pololu does publish a figure with
nowhere to go: *"the recommended upper limit for continuously applied loads is 4 kg-cm"*, plus an
intermittent limit of 8 kg-cm.

**What settled that it belongs to the geartrain:** the figure is identical across the LP, MP and
HP variants and at every ratio in the family. A motor thermal rating would move with both.

**And what settled that it is not a capacity** is the other end of the same family. At 9.7:1 the
motor stalls at 3.9 kg-cm while the ceiling is 4 kg-cm - so treating the ceiling as a capacity
would promise a torque that motor cannot produce at all. *Do not exceed X* and *can sustain X* are
different claims, and a ceiling can sit above what is achievable, below it, or anywhere between,
with nothing in the number to say which.

So `gearbox.torque_limit` refuses and never sizes. That makes it the purest instance of the
asymmetry ADR-0015 already rests on: sampled reach is sound positive, static capacity sound
negative, and this field can **only ever say no**.

The record for that gearmotor still has `continuous_torque_nm: null`. The real continuous torque is
`min(ceiling, unpublished thermal limit)` and only one of those is known - now said in fields
rather than in a note.

**The sweep's list is empty.** Six actuator types, all exercised. Of the three gaps it declared this
afternoon, one was real and fixed ([[stepper-torque-index]] had already closed a fourth), one was a
mislabelled datasheet problem, and one was a reason that turned out to be wrong. **Two of three
entries needed correcting** - which is the rate to expect from a list whose reasons nothing checks,
and worth remembering the next time one reads convincingly.
