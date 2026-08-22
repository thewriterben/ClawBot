---
title: Forward kinematics — Lynch and Park, and the third representation ADR-0005 never considered
type: source-summary
updated: 2026-08-22
sources:
  - Lynch, K. M. and Park, F. C., "Modern Robotics: Mechanics, Planning, and Control", Cambridge University Press, 2017, ISBN 9781107156302. Free preprint at http://hades.mech.northwestern.edu/index.php/Modern_Robotics (retrieved 2026-08-22)
  - Wikipedia, "Product of exponentials formula" (retrieved 2026-08-22, secondary)
---

# Forward kinematics — Lynch and Park, and the third representation ADR-0005 never considered

The reference behind the computation ADR-0003 promises. Chapter 4 is forward kinematics,
chapter 5 velocity kinematics and the Jacobian, chapter 6 inverse kinematics, chapter 7
**kinematics of closed chains** — relevant when ADR-0008's refusal of true loops is revisited.

**The finding that matters is structural, not mathematical.** This textbook teaches forward
kinematics via the **product of exponentials** and puts Denavit-Hartenberg in **Appendix C**.
ADR-0005 framed its decision as DH versus a URDF-shaped tree. There was a third option and it
was not considered.

## Product of exponentials, in one paragraph

A configuration is `T(q) = e^{[S_1]q_1} e^{[S_2]q_2} ... e^{[S_n]q_n} M`, where `M` is the
end-effector pose at the zero configuration and each `S_i` is a **screw axis** expressed in a
fixed frame.

The stated advantages over DH:

- **No link frames.** Only a base frame and an end-effector frame are needed, and both may be
  chosen arbitrarily. DH requires a frame per link assigned by special rules.
- **Prismatic and revolute joints are treated uniformly** — one formula, not two cases.
- **Each joint twist is constructed independently of its neighbours**, which the sources note
  makes them "easier to construct and easier to process by computer". A DH parameter depends on
  the adjacent joint axis.
- **Cost:** PoE is not minimal. It needs 6n numbers for n screw axes where DH needs 4n.

## Why this does not reopen ADR-0005

It looked at first like a missed option that might unseat the decision. It is better than that:
**PoE is a computation, not a storage format, and the tree gives it for free.**

A screw axis is derivable from what a ClawBot record already stores — each joint's `origin`
transform and its `axis`, composed down the tree to the base frame. So the repo can store the
tree, which is what a human edits and what URDF interchanges, and compute in PoE, which is what
the math wants. Nothing is stored twice and nothing is stored ambiguously.

And the two frames PoE requires are **exactly the two frames this repo already insists on
naming**:

- its fixed base frame is `base_link`, which ADR-0009 makes every derived answer relative to;
- its end-effector frame `M` is the tool offset, which ADR-0003 makes travel inside the verdict
  because the verdict is meaningless without it.

DH's failure on this same point is what [[dh-conventions]] records: base and tool transforms
fall out of a DH factorisation as leftover residue. PoE puts them at the centre. The two
representations disagree about precisely the thing ClawBot cares most about, and the one this
repo already chose is on the right side of it.

**A note on the arithmetic, since it will be asked.** For a tree, composing homogeneous
transforms down each branch and the PoE formula give the same answer — PoE is a regrouping of
the same product, not different physics. Composing down the tree is what URDF's own semantics
define and what branching requires, so that is the implementation, with this chapter as the
authority for the underlying result rather than as a recipe transcribed.

## Still not read

Chapter 4 in full, from the free preprint rather than from summaries of it. This page rests on
the book's table of contents, its Appendix C argument as reported by secondary sources, and the
publisher's preview. **That is thinner evidence than the URDF pages rest on**, and it is
recorded here rather than smoothed over. It is sufficient to justify an implementation
decision and it is *not* sufficient to justify a number. No value in this repo cites this page.
