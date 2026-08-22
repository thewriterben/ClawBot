---
title: OpenDesignCore wiki
type: source-summary
updated: 2026-08-22
sources:
  - OpenDesignCore/wiki/CLAUDE.md
  - OpenDesignCore/wiki/index.md
  - OpenDesignCore/wiki/log.md
  - OpenDesignCore/wiki/concepts/ecosystem-map.md
  - OpenDesignCore/wiki/concepts/platform-decisions.md
---

# OpenDesignCore wiki

A working instantiation of [[llm-wiki-pattern]], running since 2026-08-15. **Prior art for this directory**, and the reason `Knowledge/` matches its conventions instead of inventing new ones.

At the time of reading: 12 entity pages, 5 concept pages, 8 source summaries, a 323-line log.

## What was copied

The whole structure — `CLAUDE.md` / `index.md` / `log.md` / `entities/` / `concepts/` / `sources/`, the frontmatter fields, the `[[wiki-link]]` convention, the `**Conflict:**` inline marker, and the three operations.

And the rule the original pattern document does not contain:

> "No number in a wiki page may enter a model run. Values used by code come from `data/` with a citation. The wiki may read the ledger; it never writes to it. **A wiki page never cites another wiki page as evidence** — evidence citations point at raw sources or the ledger only. `[[links]]` between pages are navigation, not grounding."

## What was changed

- **Two raw trees** (`robotics/`, `platform/`) instead of ODC's "raw sources live outside this directory". ClawBot has domain sources with no home in a sibling repo, so it needs somewhere to put them.
- **An explicitly empty half**, with a reading list standing in for the pages. ODC's wiki has no equivalent because its sources already existed when it started.

## Platform decisions (PD-1..PD-6)

Recorded in `concepts/platform-decisions.md`. "Decisions that span repos... the new repos' DECISIONS.md are seeded from here at creation." Summarised in [[opendesigncore]]; PD-2, PD-4 and PD-5 bind [[clawbot]].

**PD-1 is the one to keep re-reading.** The electronics kernel decision was made from documentation and a web search and survived four hours before installation proved atopile was maintenance-only with a hosted-SaaS successor. Its own lesson: *"Kernel choices get installed and run before they are recorded."* [[open-questions]] carries ClawBot's breach of it.

## The log as a model of what to write

The 2026-08-21 entry is the best example read so far, and worth imitating on three counts:

1. **It records a conflict rather than resolving it.** The awesome-3d-printing list describes Open Filament Database as carrying "print settings"; it does not. The entry notes the misreading is "the more likely outcome than the adoption", and the ADR records it *before* the mechanism.
2. **It records a finding that came from the wrong place.** "PicoGK 2.2.0 ships natives for `win-x64` and `osx-arm64` only" — found by reading a lockfile, not documentation. ADR-0008's "CI needs only the .NET SDK" was "true and incomplete", and was **amended in the ADR rather than written as a new one**, because "it is a consequence nobody had checked, not a decision anybody made". A useful precedent for what ClawBot should do when question 1 in [[open-questions]] resolves.
3. **It ends with a Rejected section**, "written down so it is not relitigated" — three rejections, each with its reason.

The 2026-08-16 entry adds a maxim worth keeping: *"A restore that reads its baseline from the thing it is about to fix is not a restore."*

## The ecosystem map

`concepts/ecosystem-map.md` covers eight repos — "brains, bodies, fabrication, and settlement, converging on MCP as the universal seam" — and names four gaps nothing in the ecosystem fills. **Mechanisms are not among them**, which is a real data point against [[clawbot]]'s premise and is recorded in [[ecosystem-position]] rather than glossed.
