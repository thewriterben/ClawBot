# raw/robotics/

Domain sources: papers, specifications, datasheets, standards, textbook extracts.

**No longer empty in effect, still empty as a directory.** On 2026-08-22 the first four
robotics sources were ingested. None of them is copied here, for the reason
[`../platform/README.md`](../platform/README.md) gives: a source with a stable home is cited
at that home, because a second copy is a copy that drifts.

| Source | Cited at | Summarised in |
|---|---|---|
| URDF XSD and `urdfdom` joint parser | `github.com/ros/urdfdom` | [`../../sources/urdf-spec.md`](../../sources/urdf-spec.md) |
| REP-103, units and coordinate conventions | `github.com/ros-infrastructure/rep` | [`../../sources/rep-103-units.md`](../../sources/rep-103-units.md) |
| Corke 2007 on DH assignment; Denavit and Hartenberg 1955; Craig 1986 | published papers and books | [`../../sources/dh-conventions.md`](../../sources/dh-conventions.md) |
| ROBOTIS Dynamixel XM430-W350 manual | `emanual.robotis.com` | [`../../sources/dynamixel-xm430.md`](../../sources/dynamixel-xm430.md) |
| Lynch and Park, *Modern Robotics* (2017) | Cambridge UP; free preprint at Northwestern | [`../../sources/forward-kinematics.md`](../../sources/forward-kinematics.md) |
| Monte Carlo workspace and FCL/ACM collision literature | survey and documentation results | [`../../sources/workspace-and-collision.md`](../../sources/workspace-and-collision.md) |

A web source is cited with the URL **and the date it was retrieved**, because unlike a sibling
repo it is not under version control and can change under the citation. If one of these
contradicts its summary later, the correction is a wiki page saying so — not an edit.

## What is still missing

The reading list in [`../../concepts/open-questions.md`](../../concepts/open-questions.md) had
eight sourcing topics. **Seven are answered.** One remains:

- **Gearbox efficiency and backlash; harmonic and cycloidal drives** — fields exist in the
  actuator schema on the strength of the names alone.

It is last for a reason worth noting. Every other topic licensed a *decision* — how to store a
mechanism, how to compute reach, whether self-collision is in scope — and a decision can rest on
a survey or a table of contents. This one would license a **number**: an efficiency figure
multiplies a derived capacity and turns ADR-0004's upper bound into an estimate. A secondary
source is not admissible for that, so this topic needs vendor data with a stated method or it
stays open.

## A note on evidence quality

These six are not equally strong and the pages say so individually. The URDF and REP-103 pages
rest on primary artifacts read directly — a schema, a parser, a normative document. The
forward-kinematics page rests on a table of contents and secondary reports of an appendix. The
workspace-and-collision page rests on abstracts and surveys.

All were sufficient to justify the decisions built on them, and **no value in `data/` cites any
of them**, because `data/` cites the hardware's own source. That separation is what makes it
acceptable to act on a survey at all.

Sources here are **immutable**. If one is wrong, the correction is a wiki page saying so, not
an edit.
