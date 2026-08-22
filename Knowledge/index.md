# Index

Catalogue of every page in this wiki. Read this first when answering a question, then drill into the pages it names. Updated on every ingest.

## Concepts
- [[ecosystem-position]] — the five peers, the seam they meet at, and the six boundaries ClawBot must not cross (2026-08-22)
- [[inherited-invariants]] — the nine rules ClawBot did not invent and may not quietly drop, each traced to where it came from (2026-08-22)
- [[open-questions]] — decisions made without evidence, and the reading list that fills the empty half. Two questions closed and four sourcing topics answered (2026-08-22)
- [[urdf-round-trip]] — what reading the URDF spec cost ADR-0005: structure maps both ways, absence maps neither (2026-08-22)

## Entities
- [[clawbot]] — this repo; the mechanism peer, defined mostly by two refusals
- [[openbuildcore]] — inventory, machines, three requirement kinds; the closest prior art and the source of most inherited discipline
- [[opendesigncore]] — the provenance record, the platform decisions, and the wiki pattern this one matches
- [[openpartscore]] — the canonical parts registry; where an actuator's facts belong
- [[oh-ben-claw]] — the embodied runtime; likely consumer, confirmed to have no robot model of its own

**Not yet written**, because nothing has been read: OpenCircuitCore, ClawCam, Project BINGO. See [[open-questions]].

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

## The empty half, revisited

It is no longer empty. Six robotics sources were ingested on 2026-08-22 and six domain pages
exist. None of the sources is copied into `raw/robotics/` — each has a stable home and is cited
there with a retrieval date, per the rule in
[`raw/platform/README.md`](raw/platform/README.md).

Seven of the eight sourcing topics are now answered. The one still open is **gearbox efficiency
and backlash** — and it is the only one where a source would license a *number* rather than a
*decision*, which is why a secondary source will not do for it. Named in [[open-questions]].

Two of the answers were *refusals* rather than features, and that counts as the topic being
closed: self-collision needs link geometry this repo deliberately does not carry, and a workspace
volume is a boundary claim in disguise.

## Counts

4 concepts, 5 entities, 9 source summaries. 1 raw source copied locally; the rest cited by
repo-relative path or by URL with a retrieval date.

Evidence quality is not uniform and the pages say so individually. The URDF pages rest on a
schema and a parser read directly. [[forward-kinematics]] rests on a table of contents and
secondary reports of an appendix. [[workspace-and-collision]] rests on abstracts and surveys.
All three are enough to justify a decision; only the first would be enough to justify a value,
and no value in this repo cites any of them.
