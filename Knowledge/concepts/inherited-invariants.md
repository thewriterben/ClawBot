---
title: Inherited invariants
type: concept
updated: 2026-08-22
sources:
  - OpenPartsCore/README.md
  - OpenBuildCore/DECISIONS.md (ADR-0004, ADR-0005, ADR-0006)
  - OpenBuildCore/README.md
  - OpenDesignCore/wiki/CLAUDE.md
  - OpenDesignCore/wiki/concepts/platform-decisions.md
  - OpenDesignCore/wiki/log.md (2026-08-21)
---

# Inherited invariants

The rules [[clawbot]] did not invent and may not quietly drop. Each is stated where it came from, because "we've always done it this way" is how a discipline decays into a habit and then into an exception.

## 1. Never invent physical data

> "Every entry carries a citation. An uncited value fails validation. No plausible-looking numbers." — [[openpartscore]]

The failure mode is specific: a plausible number is *worse* than a missing one, because a missing number announces itself and a plausible one does not. Applied in ClawBot to joint limits, link lengths and torque figures.

## 2. A placeholder must block, not default

[[openbuildcore]] shipped its K2 Plus record with a `1×1×1` `TODO(source)` envelope, and **every fit check on that machine failed loudly for a day** until a real source turned up. That is what a placeholder is for.

ClawBot's `example/` templates are built this way on purpose: every dimension is a `1`, every citation is `TODO(source)`.

## 3. Absence of evidence is recorded as absence, never as a negative finding

> "No machines declared means `makeable: null` — unknown, not false." — OBC ADR-0006, which notes it is "the same rule as OpenDesignCore's undeclared scanner accuracy".

In ClawBot: a joint with no `limits` is UNKNOWN, never unlimited. A missing `continuous_torque_nm` makes capacity underivable, not zero. A missing `backlash_rad` is not `0`.

## 4. A derived number carries the assumption that makes it true, in the value

Not in the documentation. [[openbuildcore]]'s shopping list prints its sequential/simultaneous basis and carries a `basis` field in JSON (its ADR-0004), because "the difference between a wrong number and an unexplained one" is whether the reader was told which assumption produced it.

In ClawBot: a reachability verdict carries its tool offset and says it is a joint-limit result, not a collision result (ADR-0003). A derived capacity says it is a static upper bound (ADR-0004).

## 5. If it was not measured and cannot be derived from something that was, say so

OBC ADR-0005 on print time: a volumetric estimate "is wrong by factors rather than percentages on anything but a solid block, and once printed it will be read as a measurement."

ClawBot's ADR-0003 and ADR-0004 are this invariant applied twice — to reach and to payload. The consequence is accepted in both: the system will frequently answer "I cannot tell you", which is less useful than a number and more useful than a wrong one.

## 6. The grounding rule for this wiki

> "No number in a wiki page may enter a model run... A wiki page never cites another wiki page as evidence." — [[opendesigncore]] `wiki/CLAUDE.md`

`[[links]]` are navigation, not grounding. The failure this prevents: page A summarises a blog post, page B cites page A, page C cites page B, and by C nobody can see the original was a blog post.

## 7. Record what was rejected, so it is not relitigated

[[opendesigncore]]'s log entry of 2026-08-21 ends with a **Rejected** section naming three things and why. This is cheap to write and expensive to reconstruct.

ClawBot's ADRs do this inline: ADR-0001 records why not a machine kind and why not a crate inside [[oh-ben-claw]]; ADR-0005 records why not DH.

## 8. Kernel choices get installed and run before they are recorded

Platform decision PD-1 was made from documentation and a web search, and **survived four hours** before installation proved atopile was maintenance-only with a hosted-SaaS successor.

**ClawBot is currently in breach of this one.** ADR-0005 chose a URDF-shaped tree over DH parameters without a single conversion having been run. Carried in [[open-questions]] as the highest-priority thing to falsify.

## 9. Legality gating (PD-5) — not yet addressed

Design-time refusal categories are meant to be enforced by every design assistant on the platform, with the taxonomy owned by Project BINGO. ClawBot has no position on this and a mechanism repo plainly needs one. See [[open-questions]].
