---
title: LLM Wiki pattern
type: source-summary
updated: 2026-08-22
sources:
  - Knowledge/raw/platform/llm-wiki.md
---

# LLM Wiki pattern

The founding source for this directory. An intentionally abstract idea document, meant to be handed to an agent and instantiated rather than followed literally.

## The core claim

RAG rediscovers knowledge from scratch on every query — nothing accumulates. The alternative is a **persistent, compounding artifact**: the LLM reads each new source and integrates it into an existing wiki, updating entity pages, revising summaries, and noting where new data contradicts old claims. "The cross-references are already there. The contradictions have already been flagged."

The human curates sources and asks questions; the LLM does all the writing, filing and bookkeeping.

## Three layers

Raw sources (immutable), the wiki (agent-owned markdown), and **the schema** — "the key configuration file — it's what makes the LLM a disciplined wiki maintainer rather than a generic chatbot", co-evolved with the human. `Knowledge/CLAUDE.md` is ours.

## Three operations

- **Ingest** — read → discuss → write a summary → update entity and concept pages → update the index → append to the log. "A single source might touch 10-15 wiki pages."
- **Query** — search, read, synthesise with citations. The key insight: **good answers get filed back as new pages**, so explorations compound the same way ingested sources do.
- **Lint** — periodically health-check for contradictions, stale claims superseded by newer sources, orphan pages, concepts lacking their own page, missing cross-references.

## index.md and log.md

Deliberately different. `index.md` is **content-oriented** — a catalogue read first when answering a query, then drilled into. The document claims this "works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embedding-based RAG infrastructure".

`log.md` is **chronological** and append-only. The parseability tip is adopted here verbatim: entries starting `## [YYYY-MM-DD] op | Title` make `grep "^## \[" log.md | tail -5` a working query.

## What this instantiation took, and what it left

**Took:** the three layers, the three operations, the index/log split and its prefix convention, the schema-as-configuration idea, and the git-repo-of-markdown framing.

**Left:** Obsidian tooling (web clipper, graph view, attachment hotkeys, Dataview), Marp decks, matplotlib output, and the `qmd` search engine. The document explicitly frames all of it as optional and modular — "pick what's useful, ignore what isn't" — and this wiki is far below the scale at which the index stops being enough.

**Diverged:** two raw trees (`robotics/`, `platform/`) rather than one, because this wiki has two subjects that touch. And the grounding rule — no wiki page cites another wiki page as evidence — is **not from this document**; it comes from [[opendesigncore]]'s instantiation, which added it. Worth noting as the clearest example of the pattern being extended rather than copied.

## The bit worth re-reading

"Humans abandon wikis because the maintenance burden grows faster than the value. LLMs don't get bored, don't forget to update a cross-reference, and can touch 15 files in one pass."

The corollary this wiki has to hold onto: an LLM also does not get bored of writing plausible prose about things it has not read. Which is why [[open-questions]] exists in the shape it does.
