---
title: Workspace computation and self-collision — the two methods, and their honesty costs
type: source-summary
updated: 2026-08-22
sources:
  - Cao, Y. et al. and related literature on Monte Carlo workspace determination, via ScienceDirect / ResearchGate survey results (retrieved 2026-08-22, secondary — abstracts and survey summaries, full papers not read)
  - Pan, J. et al., FCL (Flexible Collision Library) two-phase architecture, via survey and documentation results (retrieved 2026-08-22, secondary)
  - MoveIt allowed collision matrix (ACM) documentation, via survey results (retrieved 2026-08-22, secondary)
---

# Workspace computation and self-collision — the two methods, and their honesty costs

Two of the four remaining sourcing topics, read together because they are the same question
asked twice: *what does it cost to be sure?*

**Both are secondary sources** — abstracts, surveys and documentation rather than the primary
papers. That is weaker than the URDF pages and is stated here so nobody mistakes the two.
Enough to choose a method; not enough to justify a number.

## Workspace: three families

The literature splits reachable-workspace computation into **analytic**, **graphic**, and
**numerical** methods, the last including grid, Monte Carlo and interval-analysis approaches.

**Monte Carlo** samples joint values at random across the joint ranges, runs forward kinematics
on each, and accumulates the reachable points; volume follows from the fraction of a bounding
region that gets hit. The trade-off reported across the surveys: analytic methods have "great
complexity and poor visibility", graphic methods produce cross-sections rather than volumes,
and Monte Carlo balances visualisation against cost.

**The property that decides it for this repo is not on that list.** A sampled workspace is
**inner-bounded**: every point it reports is genuinely reachable, because a sample only enters
the set after FK put the tool there. Points it misses are false negatives — under-claims.

That is the direction this repo is allowed to be wrong in. ADR-0003 already regrets that
computed reach over-claims by ignoring self-collision, and named that as the opposite of the
conservative error OpenBuildCore accepted on axis-aligned fit. A sampling method's error runs
the *other* way, which partially offsets a known problem rather than compounding it.

The cost is that a sampled answer must never be stated as a boundary. "This point is reachable"
is sound. "This point is not reachable" is **not** sound from a sampling method — it means
*no sample landed there*, and the honest form of that answer names the sample count.

## Self-collision: two phases, and a matrix that says what to ignore

The standard architecture is **broad phase then narrow phase**. Broad phase uses bounding
volumes to cheaply eliminate pairs that cannot be touching; narrow phase runs exact geometry
tests (GJK, triangle intersection) only on the survivors.

The piece that matters more here is the **allowed collision matrix**. Adjacent links are
*always* in contact — they share a joint — so a naive all-pairs check reports collisions for
every mechanism ever built. The ACM is the per-pair table of which contacts are permitted,
covering adjacent links and pairs that geometry makes it impossible to bring together.

**The consequence for ClawBot is a refusal, not a feature.** Self-collision needs three things
this repo does not have:

1. **Link geometry.** ClawBot stores a `part_id`, a `make` box, or a `provenance_ref` hash —
   never a mesh. It cannot test what it cannot see, and ADR-0006 keeps geometry in
   [[opendesigncore]] on purpose.
2. **An allowed collision matrix**, which is per-mechanism, partly hand-authored, and would be a
   set of claims requiring citations like any other.
3. A collision library, which would be the first runtime dependency in a repo that has none.

So self-collision stays refused, and ADR-0003's caveat stays in every reachability verdict. What
this reading changes is that the caveat can now name *why*: not "unimplemented" but "requires
link geometry this record does not carry, and an allowed-collision matrix nobody has authored".

**A cheaper approximation was considered and rejected**: treat each `make` link's `size_mm` as a
bounding box and run broad phase only. It would catch some self-collisions. It would also report
collisions between adjacent links constantly — the exact thing the ACM exists to suppress — and
its silence would be indistinguishable from a real clearance. A collision check that cannot tell
"clear" from "not checked" is worse than none, because the first is a claim.
