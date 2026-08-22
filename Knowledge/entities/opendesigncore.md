---
title: OpenDesignCore
type: entity
updated: 2026-08-22
sources:
  - OpenDesignCore/wiki/CLAUDE.md
  - OpenDesignCore/wiki/index.md
  - OpenDesignCore/wiki/concepts/ecosystem-map.md
  - OpenDesignCore/wiki/concepts/platform-decisions.md
  - OpenDesignCore/wiki/log.md
  - OpenBuildCore/README.md (for the provenance-record interface)
---

# OpenDesignCore

The deterministic engineering core: requirements → validated geometry + provenance. C#/.NET on the PicoGK kernel. Its own wiki describes it as "the only repo with a rigorous determinism/provenance contract".

Two things make it the platform's centre of gravity for [[clawbot]]'s purposes: it defines the **provenance record**, and it hosts the **platform decisions** and the **wiki pattern** everything else follows.

## The provenance record

An artifact carries a hash, a bounding box (`artifact.bbox_mm`) and a volume (`volume_cubic_mm`) — its ADR-0010. This is what makes a peer interface possible without a dependency: [[openbuildcore]] reads the sidecar file and imports nothing.

[[clawbot]]'s third link kind is a `provenance_ref` to one of these (ClawBot ADR-0006). It is the strongest of the three because the geometry exists — bbox and volume are facts rather than declared intent.

A detail worth carrying: OBC **refuses** a provenance record too old to carry those fields, naming the schema, rather than falling back to the part envelope. The envelope is the thing that goes *inside* an enclosure, not the thing that gets printed, and substituting it would be wrong by twice the clearance plus twice the wall while looking entirely plausible. That is the general shape of the failure this platform guards against.

## Platform decisions (PD-1..PD-6)

Recorded in its `wiki/concepts/platform-decisions.md`; new repos' DECISIONS.md are seeded from them. The three that bind ClawBot:

- **PD-2** — schema-first registry; **user inventory is a separate store** referencing canonical part ids, never mixed into cited reference data. ClawBot ADR-0001 leans on this: a robot is on both sides of that split, which is part of why it needed its own repo.
- **PD-4** — the Open\*Core repos are Apache-2.0. ClawBot ADR-0002.
- **PD-5** — two-tier legality gating; the refusal-category taxonomy lives in Project BINGO's schema and other repos reference it. **Not yet addressed by ClawBot** — see [[open-questions]].

**A lesson recorded in PD-1 that applies directly to us:** the electronics kernel decision was made from documentation and a web search, and survived four hours before installation proved it wrong. "Kernel choices get installed and run before they are recorded." ClawBot has now recorded a representation decision (ADR-0005, URDF-over-DH) without having run a single conversion. That is the same exposure, and [[open-questions]] carries it.

## The wiki pattern

`wiki/` is a working instantiation of [[llm-wiki-pattern]], with `CLAUDE.md`, `index.md`, `log.md`, `entities/`, `concepts/`, `sources/`. ClawBot's `Knowledge/` matches it on purpose rather than inventing a second dialect.

Its grounding rule, adopted verbatim here: "No number in a wiki page may enter a model run... A wiki page never cites another wiki page as evidence."

Its `log.md` is worth reading as an example of what a good log entry does — the 2026-08-21 entry records not just what was adopted but what was **rejected and why**, "written down so it is not relitigated". See [[inherited-invariants]].
