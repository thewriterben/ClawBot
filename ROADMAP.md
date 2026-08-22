# Roadmap

## Now
- [x] Decide where a mechanism lives in the platform — fifth peer rather than an OpenBuildCore machine kind, argued from the shape of the data (ADR-0001) (2026-08-22)
- [x] Settle the representation before writing any of it down: link/joint tree over DH parameters, radians in the file (ADR-0005) (2026-08-22)
- [x] Establish the two rules with teeth — reach derived not declared (ADR-0003), payload a function of pose (ADR-0004) — before a single record exists to violate them (2026-08-22)
- [x] JSON Schema for robot and actuator records, citation-gated like every other registry on the platform (2026-08-22)
- [x] Knowledge base standing up, matching OpenDesignCore's `wiki/` conventions rather than inventing a second dialect (2026-08-22)

## Next
- [ ] **Read the robotics half of the wiki's queue.** The domain pages are empty on purpose (see `Knowledge/concepts/open-questions.md`). Nothing else here should be built on recall.
- [ ] A first robot record. It needs a real mechanism with real datasheets — a described-from-memory arm would be exactly the invented data the schema exists to refuse.
- [ ] `validate.py`, following OpenPartsCore's and OpenBuildCore's: refuses an uncited joint limit, refuses a `measured_payload` with no pose, refuses an out-of-range `_rad` value (the defence ADR-0005 leaves standing).
- [ ] Forward kinematics and a reachability answer that names its tool offset and says it is a joint-limit result, not a collision result (ADR-0003).
- [ ] Static payload derivation from `continuous_torque_nm`, reported per-pose and labelled an upper bound (ADR-0004).
- [ ] URDF import/export. Structural mapping, not reinterpretation — that is what ADR-0005 bought.
- [ ] Emit a link manifest OpenBuildCore can answer `what-can-i-build` about, in its `part_id` / `capability` / `make` vocabulary (ADR-0006).

## Not yet
- **Self-collision.** Named in ADR-0003 as the reason computed reach is optimistic. Until it exists, every reachability answer has to say so.
- Inverse kinematics. Reachability needs an IK solve or a workspace sample; which one is a real decision and gets its own ADR.
- Closed-chain mechanisms — delta arms, four-bar linkages, differentials. The tree in ADR-0005 cannot express a loop. Add it when a real mechanism needs it.
- Mobile bases and wheeled odometry. A rover is a mechanism whose base frame moves, which the current model has no place for.
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
