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
