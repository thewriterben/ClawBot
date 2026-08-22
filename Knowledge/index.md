# Index

Catalogue of every page in this wiki. Read this first when answering a question, then drill into the pages it names. Updated on every ingest.

## Concepts
- [[ecosystem-position]] — the five peers, the seam they meet at, and the six boundaries ClawBot must not cross (2026-08-22)
- [[inherited-invariants]] — the nine rules ClawBot did not invent and may not quietly drop, each traced to where it came from (2026-08-22)
- [[open-questions]] — decisions made without evidence, and the reading list. Three questions closed and seven of eight sourcing topics answered (2026-08-22)
- [[urdf-round-trip]] — what reading the URDF spec cost ADR-0005: structure maps both ways, absence maps neither (2026-08-22)

## Entities
- [[clawbot]] — this repo; the mechanism peer, defined mostly by what it refuses to answer
- [[openbuildcore]] — inventory, machines, three requirement kinds; the closest prior art and the source of most inherited discipline
- [[opendesigncore]] — the provenance record, the platform decisions, and the wiki pattern this one matches
- [[openpartscore]] — the canonical parts registry. Its `electronic/sg90` proved the actuator boundary: identity, bus and capabilities upstream; torque, speed and travel here
- [[oh-ben-claw]] — the embodied runtime; likely consumer, confirmed to have no robot model of its own

**Read on 2026-08-22 but not written up**: OpenCircuitCore, ClawCam, Project BINGO. An outstanding debt against this wiki's own ingest rule — what was learned is held in ADRs and commit messages instead of entity pages. Recorded in [[open-questions]].

## Sources

### Platform
- [[llm-wiki-pattern]] — the founding idea document; three layers, three operations, index/log split (2026-08-22)
- [[obc-decisions]] — OpenBuildCore's six ADRs; ancestor of four of ClawBot's six (2026-08-22)
- [[odc-wiki]] — the prior-art wiki instantiation, its grounding rule, and PD-1's four-hour lesson (2026-08-22)

### Robotics
- [[urdf-spec]] — the URDF XSD and the parser that enforces it, which disagree; and the two defaults that turn absence into a value (2026-08-22)
- [[rep-103-units]] — metres, radians, right-handed, fixed-axis XYZ; and the same anti-ambiguity argument ADR-0005 made, aimed at Euler angles (2026-08-22)
- [[dh-conventions]] — standard versus Craig, and the three things neither table records: the convention, the joint offsets, and the tool transform (2026-08-22)
- [[dynamixel-xm430]] — a good vendor states that stall is not continuous, then publishes only stall. ADR-0004 confirmed on real evidence (2026-08-22)
- [[forward-kinematics]] — Lynch and Park; the product of exponentials, and why a third representation ADR-0005 never considered does not reopen it (2026-08-22)
- [[workspace-and-collision]] — sampling is inner-bounded and under-claims, which is the direction this repo may be wrong in; self-collision stays refused and can now say why (2026-08-22)
- [[gearbox-efficiency]] — efficiency is a five-variable curve, not a scalar; it does not apply to a static hold at all; and a vendor states its published stiffness varies ±30% unit to unit (2026-08-22)

## The empty half, revisited

It is no longer empty. Six robotics sources were ingested on 2026-08-22 and six domain pages
exist. None of the sources is copied into `raw/robotics/` — each has a stable home and is cited
there with a retrieval date, per the rule in
[`raw/platform/README.md`](raw/platform/README.md).

**All eight sourcing topics are answered**, as of 2026-08-22. The reading list is empty.

Three of the answers were *refusals* rather than features, and each counts as closed:
self-collision needs link geometry this repo deliberately does not carry; a workspace volume is a
boundary claim in disguise; and a running gearbox efficiency does not describe a stationary
geartrain, so it is the wrong quantity for `hold` rather than a missing one.

An empty reading list is not a finished wiki. It means every question written down at the start
has a source behind its answer. The next ones will arrive from data — ADR-0014 and ADR-0018 both
came from a single datasheet meeting a single schema field, not from thinking harder.

## Counts

4 concepts, 5 entities, 10 source summaries, 6 log entries. One real record in `data/`, cited to a vendor manual. 1 raw source copied locally; the rest cited by
repo-relative path or by URL with a retrieval date.

Evidence quality is not uniform and the pages say so individually. The URDF pages rest on a
schema and a parser read directly. [[forward-kinematics]] rests on a table of contents and
secondary reports of an appendix. [[workspace-and-collision]] rests on abstracts and surveys.
All three are enough to justify a decision; only the first would be enough to justify a value,
and no value in this repo cites any of them.
