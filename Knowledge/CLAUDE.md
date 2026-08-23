# Wiki schema

This directory is ClawBot's LLM Wiki. The agent writes and maintains every page here; the human curates sources and asks the questions.

It follows the pattern described in [`raw/platform/llm-wiki.md`](raw/platform/llm-wiki.md), and deliberately **matches the instantiation already running in OpenDesignCore's `wiki/`** rather than inventing a second dialect — same three layers, same page types, same index/log split. Someone who can read one can read the other. Where ClawBot diverges, it is noted below and the reason is given.

## Layers

- **Raw sources** — immutable. Two trees under `raw/`, plus sources that already live in sibling repos and are cited by repo-relative path (`OpenBuildCore/DECISIONS.md`). Never edit a source. If a source needs correcting, the correction is a wiki page that says so.
- **Wiki** — `entities/`, `concepts/`, `sources/` and the two special files. Fully agent-owned; rewrite pages freely as understanding improves.
- **Schema** — this file. Co-evolve it with the human.

## The grounding rule

**No number in a wiki page may enter a schema, a data file, or a computation.** Values that hardware depends on come from `data/` with a citation, and `data/` cites raw sources, never here.

**A wiki page never cites another wiki page as evidence.** Evidence citations point at raw sources only. `[[links]]` between pages are navigation, not grounding. This is the rule that keeps a synthesis from laundering itself into a fact: page A summarises a source, page B cites page A, page C cites page B, and by page C nobody can see that the original was a blog post.

Inherited from OpenDesignCore ADR-0006 and its ADR-0011 grounding discipline. See [[inherited-invariants]].

## Structure

```
Knowledge/
  CLAUDE.md      this schema
  index.md       catalogue of every page, by category; updated on every ingest
  log.md         append-only; entries start "## [YYYY-MM-DD] <op> | <title>"
  raw/
    robotics/    domain sources: papers, datasheets, standards, textbook extracts
    platform/    sources about this platform and how it works
  entities/      one page per repo, tool, standard, vendor, mechanism, component family
  concepts/      cross-cutting syntheses: position in the ecosystem, invariants, open questions
  sources/       one short summary page per ingested raw source, pointing at the original
```

**Two raw trees rather than one.** ClawBot's wiki carries two subjects that touch: the robotics domain, and the platform ClawBot is a peer in. Keeping the sources separated makes the asymmetry between them visible — see the note on the empty half below — while the wiki pages themselves stay in one interlinked set, because the interesting pages are the ones that cross over.

## Page conventions

- YAML frontmatter: `title`, `type` (`entity` | `concept` | `source-summary`), `updated`, `sources` (list of raw-source paths).
- Wiki-links as `[[page-name]]`, matching the file's basename.
- Flag contradictions inline with `**Conflict:**` and say which source each side came from. A contradiction between two sources is a finding worth keeping, not a problem to resolve by picking one.
- Mark an unsourced claim `TODO(source)` inline. It is better to record that something is believed and unsourced than to leave it out and have it reappear as an assumption later.
- Keep pages short and dense. A page that restates a source at length is a failed page; link and summarise.

## The empty half — filled 2026-08-22, and the rule that emptied it still applies

**This section used to say `raw/robotics/` was empty and that every domain page depending on it was unwritten.** That was true for one day. Six sources were ingested on 2026-08-22 and all eight sourcing topics are answered; gearbox efficiency and backlash was the last, and a seventh source on 2026-08-23 closed the one claim it had to leave secondary ([[backlash-measurement]]). The history is kept here rather than deleted, because the *reason* the directory was empty is the part that has to survive:

An assistant asked about forward kinematics or servo thermal limits will produce fluent, mostly-correct, entirely uncited prose. Filing that into a wiki whose whole purpose is provenance would poison it at the root — and worse, it would look exactly like a page that had been researched. **The pages get written when sources arrive, and not before.** That rule did not stop applying when the first sources turned up; it is what every future page is still held to.

Two things learned in the filling, both worth keeping:

- **Evidence quality is not uniform, and a page must say where it sits.** [[urdf-spec]] rests on a schema and a parser read directly. [[forward-kinematics]] rests on a table of contents and secondary reports of an appendix. [[workspace-and-collision]] rests on abstracts. All three are enough to justify a *decision*; only the first would be enough to justify a *value*. Each page states its own standing rather than leaving a reader to assume they are equivalent.
- **A closed topic is sometimes a refusal.** Self-collision was answered by establishing that this repo cannot do it and naming what it would need. That counts as read, not as pending.

What remains is a reading list, in [[open-questions]]. Treat filling it as the highest-value ingest work available.

## Operations

**Ingest.** Read the source → discuss the takeaways with the human → write or update a `sources/` summary → update the `entities/` and `concepts/` pages it touches → update `index.md` → append to `log.md`. A single source may touch a dozen pages; that is normal and is the point.

**Query.** Read `index.md` first, drill into the pages it names, synthesise with citations to raw sources. A durable answer gets filed back as a concept page rather than left in chat history.

**Lint.** Check for: contradictions between pages, claims a newer source has superseded, orphan pages nothing links to, concepts mentioned repeatedly but with no page of their own, and `TODO(source)` markers that have been waiting long enough to be worth chasing. Append findings to `log.md`.

## Where this wiki must not drift

ClawBot's repo has decisions with teeth (ADR-0003, ADR-0004) that exist precisely because plausible numbers are easy to produce. The wiki is the most likely place for one to enter the repo, because prose does not look like data. If a wiki page ever states a joint limit, a torque or a reach as though it were established, and no raw source is named — that is the failure this whole structure was built to prevent, and it should be fixed on sight.
