---
title: Open questions
type: concept
updated: 2026-08-22
sources:
  - ClawBot/DECISIONS.md
  - OpenDesignCore/wiki/concepts/platform-decisions.md (PD-1, PD-5)
  - Knowledge/raw/platform/llm-wiki.md
---

# Open questions

Two lists. The first is what needs **falsifying** — decisions already recorded that were made without evidence. The second is what needs **reading** — the empty half of this wiki.

Ordered by how expensive the mistake gets if left alone.

---

## Decisions made without evidence

### 1. ADR-0005 chose URDF-over-DH without running a conversion

The direct breach of [[inherited-invariants]] #8, the rule PD-1 paid for. The argument against DH is real — two incompatible conventions, four columns that do not record which — but "structurally URDF, so a converter is a mapping rather than a reinterpretation" is a **claim about a converter nobody has written**.

**To falsify:** take a published URDF, map it to the schema in `schema/robot.schema.json`, map it back, and see what does not survive. Candidates for what breaks: `<mimic>` joints, multiple `<visual>`/`<collision>` geometries per link, xacro macros, inertial frames that are not the link frame. If a real URDF cannot round-trip, ADR-0005's consequences section is wrong and needs amending — the way [[opendesigncore]] amended ADR-0008 in place when the PicoGK Linux native turned out to be missing.

### 2. Nobody has asked for ClawBot

ADR-0001 admits the fifth repo is "justified by a data shape rather than by demand". [[ecosystem-position]] carries the same admission about the co-design gap.

**To falsify:** read [[oh-ben-claw]]'s `docs/ECOSYSTEM-INTEGRATION.md` and `docs/EMBODIED-ARCHITECTURE.md` and find out whether it already has a robot model, in what form, and whether it is shareable. If it does and it is, ADR-0001's second rejection ("a crate inside Oh-Ben-Claw") was argued against a repo that had already solved it.

### 3. The actuator/parts boundary is untested

ClawBot's actuator schema carries make, model, mass and electrical fields that an [[openpartscore]] `mechanical` entry would plausibly also carry. The stated split — the registry holds *what the part is*, ClawBot holds *what it does in a mechanism* — is defensible and has never met a real entry.

**To falsify:** write one actuator both ways and see which fields genuinely have two homes.

### 4. Radians in the file (ADR-0005) protects against one bug and invites another

The `_rad` suffix plus a bounded range is the stated defence against a hand-typed `90`. Nothing has tested whether that defence holds for a value like `3` — plausibly 3 radians, plausibly a typo for 30 degrees, in range either way.

### 5. PD-5 legality gating has no ClawBot position

A mechanism repo needs one more obviously than a parts registry does. Requires reading Project BINGO's acceptance schema, which owns the taxonomy.

---

## The reading list

`raw/robotics/` is empty and so is every domain page. This is deliberate — see the "empty half" section of [`../CLAUDE.md`](../CLAUDE.md) — and this list is what fills it. **Nothing in the repo should be built on recall while this list is untouched.**

### Already on disk, not yet read

Cheapest first; these need no sourcing, only time.

- [[oh-ben-claw]] `docs/SOTA-COMPARISON.md` — a component-by-component benchmark against ROS 2 Nav2, slam_toolbox, Cartographer, AMCL, BehaviorTree.CPP and Open-RMF. The closest thing on disk to a robotics state-of-the-art survey.
- [[oh-ben-claw]] `docs/EMBODIED-ARCHITECTURE.md`, `docs/ECOSYSTEM-INTEGRATION.md`, `Knowledge Base/` — see question 2 above.
- Oh-Ben-Claw's README past the four-control-modes table (~770 lines unread), plus `registry/`.
- **OpenCircuitCore** — the only peer with no entity page, because none of it has been read. An arm's wiring is a real constraint on its joint travel.
- ClawCam — the perception peer; relevant if a mechanism ever needs to know where its target is.
- Project BINGO — machine records, capability tiers, and the PD-5 taxonomy.

### Needs sourcing

No page gets written from these headings until a citable source exists behind it.

| Topic | Why it matters | What would settle it |
|---|---|---|
| URDF specification | ADR-0005's entire basis | The official spec, not a tutorial |
| DH conventions, standard vs Craig | The ambiguity ADR-0005 rejects DH for | A primary text stating both |
| Forward kinematics | The computation ADR-0003 promises | A standard reference |
| Workspace determination | Whether reach is sampled or solved — needs its own ADR | Literature on reachable-workspace computation |
| Self-collision | Named in ADR-0003 as why computed reach is optimistic | Broad-phase/narrow-phase collision literature |
| Servo thermal limits | ADR-0004's whole premise | A datasheet with a real continuous rating, plus anything on duty-cycle derating |
| Gearbox efficiency and backlash | Turns an upper bound into an estimate | Vendor data with method |
| Harmonic and cycloidal drives | Fields exist in the schema on the strength of the names alone | Anything primary |

**Note the shape of that table.** Eight rows, and the schema already has fields for most of them. Fields were written from an understanding that has no sources behind it yet — which is defensible for a *shape* and would not be defensible for a *value*. The distinction is doing real work here and is worth checking again once the reading is done.

---

## Ingestion queue hygiene

Per [`../CLAUDE.md`](../CLAUDE.md), a lint pass should check whether `TODO(source)` markers have been waiting long enough to chase. As of 2026-08-22 there are three, all in [[clawbot]] and [[ecosystem-position]], all recording the same thing: nobody has asked for this repo yet.
