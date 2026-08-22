# Roadmap

## Now
- [x] Decide where a mechanism lives in the platform — fifth peer rather than an OpenBuildCore machine kind, argued from the shape of the data (ADR-0001) (2026-08-22)
- [x] Settle the representation before writing any of it down: link/joint tree over DH parameters, radians in the file (ADR-0005) (2026-08-22)
- [x] Establish the two rules with teeth — reach derived not declared (ADR-0003), payload a function of pose (ADR-0004) — before a single record exists to violate them (2026-08-22)
- [x] JSON Schema for robot and actuator records, citation-gated like every other registry on the platform (2026-08-22)
- [x] Knowledge base standing up, matching OpenDesignCore's `wiki/` conventions rather than inventing a second dialect (2026-08-22)

## Next
- [x] **Read the robotics half of the wiki's queue** — four of eight sourcing topics ingested: the URDF XSD and `urdfdom`'s parser, REP-103, Corke on DH assignment, and a real actuator datasheet. Four pages written, `raw/robotics/` no longer empty in effect (2026-08-22)
- [x] **Falsify ADR-0005 by running the conversion** — the standing breach of inherited invariant #8, closed. Structure maps; **absence does not**, in either direction. ADR-0007 retracts ADR-0005's consequences sentence and makes the converter a boundary with an explicit absence rule each way (2026-08-22)
- [x] Fix the schema's own contradiction — `kind` said "serial chains only" while `joints` said "must be a tree". Trees branch. ADR-0008 keeps the tree, adds `mimic` for coupled joints, still refuses true loops (2026-08-22)
- [x] Adopt URDF's full six joint types; a moving base is expressible and every answer is explicitly relative to `base_link` (ADR-0009) (2026-08-22)
- [x] Draw the control line: ClawBot owns the body model, the derivations, and an affordance verdict; the loop stays behind Track 0 (ADR-0010) (2026-08-22)
- [x] `validate.py`, following OpenPartsCore's and OpenBuildCore's — refuses an uncited joint limit, an out-of-range `_rad`, a link with two kinds, a mimic cycle, a non-tree graph, and a continuous torque that reads like a fraction of stall. **29 tests, every rule with teeth proven to bite** (2026-08-22)
- [x] Assembly records: a DAG of steps, citation-gated fastener torques, and no modelled build time (ADR-0011) (2026-08-22)
- [x] Harness records: the channel map, and **a cable that crosses a joint is a joint limit** (ADR-0012) (2026-08-22)
- [x] Emit a link manifest OpenBuildCore can answer `what-can-i-build` about, in its `part_id` / `capability` / `make` vocabulary (ADR-0006) — `manifest.py`, with `--as-project`. **Verified against OpenBuildCore's own `project.schema.json`**, not against a copy of it (2026-08-22)
- [x] Read the remaining sourcing topics that gate computation — Lynch and Park for forward kinematics, and the workspace/self-collision literature. **Seven of eight now answered** (2026-08-22)
- [x] Decide how reachability is computed: sampled, deterministic under a declared seed, and **"not reachable" is never a claim** (ADR-0013) (2026-08-22)
- [x] Forward kinematics and a reachability answer that names its tool offset, its base frame, its sample count and seed, and says it is a joint-limit result rather than a collision result (ADR-0003) — `kinematics.py fk` / `reach`, 23 known-answer tests (2026-08-22)
- [x] Static payload derivation from `continuous_torque_nm`, per-pose, labelled a static upper bound, torque taken about the real joint axis and loaded only by what hangs below it (ADR-0004). A floating base answers incomplete rather than assuming z-up (2026-08-22)
- [x] URDF import/export against the boundary ADR-0007 defines — `urdf.py`, **19 tests that actually run the round trip**. Structure survives; provenance and absence do not, and both are proven rather than asserted (2026-08-22)
- [ ] A first robot record. Still needs a real mechanism with real datasheets — a described-from-memory arm would be exactly the invented data the schema exists to refuse. The [[dynamixel-xm430]] reading means a first *actuator* record is now writable from a cited datasheet.
- [ ] A Rust binding, following OpenPartsCore's codegen discipline, so Oh-Ben-Claw can read the body model without taking Python.
- [ ] The affordance verdict ADR-0010 promised — a named request in, "this body can/cannot/incomplete" out. `reach` and `hold` are its two halves; nothing composes them yet.
- [ ] Resolve the degrees/radians seam with Oh-Ben-Claw. `ServoAngle` is degrees; this repo and REP-103 are radians. ADR-0010 puts the conversion at one boundary and nothing enforces it yet.
- [ ] An MCP surface. ClawBot is the only peer without one; reads and derivations execute, nothing reaches an actuator (ODC ADR-0009's line).
- [ ] A position on PD-5 legality gating. Project BINGO's `REFUSAL-CATEGORIES.md` names design-time assistants as bound by the taxonomy, and `weapons.other` and `regulated.medical` land directly on a mechanism repo.

## Not yet
- **Self-collision.** Named in ADR-0003 as the reason computed reach is optimistic. Until it exists, every reachability answer has to say so. It now has a sibling: ADR-0012's unchecked cable runs are a second over-claim in the same direction, and both are named in the value.
- Inverse kinematics. Reachability needs an IK solve or a workspace sample; which one is a real decision and gets its own ADR.
- **True closed loops** — delta arms, four-bar linkages, Stewart platforms. ADR-0008 split this: *coupled* joints (parallel jaws, differentials) are now expressible as `mimic` on a tree, which was the common 80%. A real loop is a simultaneous constraint rather than a function of one other joint, and conflating the two later would be worse than refusing it now.
- Wheels, propellers, odometry and gait. ADR-0009 makes a moving base *expressible* — a `planar` joint says the base moves in a plane. It does not say how, and this repo does not model how.
- A learned policy surface: action-space definitions, simulation export, dataset schemas. Rejected in ADR-0010 as a second product rather than a schema change, not as a bad idea. A real request pulls it forward.
- Cable mechanics. `service_loop_mm` is recorded and feeds nothing, because relating slack to permitted travel needs bend-radius behaviour under load that has no source here (ADR-0012).
- Dynamics, and the full inertia tensor URDF carries. ADR-0004 draws the line at static gravity load; the gap is recorded in `Knowledge/concepts/urdf-round-trip.md`.
- Dynamics. ADR-0004 draws the line at static gravity load and says so in every answer.
- Compliance, backlash, gearbox efficiency. Each turns an upper bound into an estimate, and each needs measured data.

## Not ever
- A `reach_mm` field (ADR-0003).
- A scalar `payload_kg` (ADR-0004).
- Stall torque feeding a capacity derivation (ADR-0004).
- DH parameters as the stored form (ADR-0005).
- Part facts. Those belong in OpenPartsCore with citations.
- Actuating anything. Commanding a physical robot belongs behind Oh-Ben-Claw's safety gate.
- Simulation, motion planning, or trajectory optimisation. Mature implementations exist; this repo describes the robot they operate on.
