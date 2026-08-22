# ClawBot — working rules

Read [`DECISIONS.md`](DECISIONS.md) before changing anything structural. The ADRs are the reasoning, not a changelog; a decision reversed without a superseding ADR is a decision lost.

## The invariant

**Never invent physical data.** Every number that describes hardware — a joint limit, a link length, a torque — comes from a cited source, or it is absent, or it is a `TODO(source)` placeholder that fails loudly until a real source arrives. A plausible number is worse than a missing one, because a missing number announces itself and a plausible one does not.

This is inherited from the platform, not local policy. See `Knowledge/concepts/inherited-invariants.md`.

## Specific refusals

These are decided. If a change would introduce one, it needs a superseding ADR, not a commit message.

| Refused | Why | ADR |
|---|---|---|
| A `reach_mm` field | A vendor reach figure is a radius to an unstated frame, before a tool, over a sphere the arm cannot fill | ADR-0003 |
| A scalar `payload_kg` | Capacity is a function of pose; one number is true at one configuration | ADR-0004 |
| Stall torque in a capacity derivation | It is an instantaneous figure the actuator cannot sustain | ADR-0004 |
| DH parameters as the stored form | Two incompatible conventions; the table does not record which | ADR-0005 |
| Degrees in a data file | `_rad` in the file, degrees only in rendered output | ADR-0005 |
| Importing a peer repo | The peers meet at data that already had to exist | ADR-0006 |

## Units

- Lengths: millimetres, field suffix `_mm` (OpenPartsCore rule, OpenDesignCore ADR-0004).
- Angles: radians, field suffix `_rad` (ADR-0005).
- Anything else names its unit in the field: `mass_g`, `torque_nm`, `velocity_rad_s`.

## When an answer cannot be given

Say so, and say which input is missing. "Incomplete: joint `shoulder_pitch` has no limits" is a useful answer. A default that lets the computation proceed is not. Absence of evidence is recorded as absence and never as a negative finding — no machines declared means `makeable: null` in OpenBuildCore, and the same rule holds here.

## The knowledge base

[`Knowledge/`](Knowledge/) is an LLM-maintained wiki. Its schema is [`Knowledge/CLAUDE.md`](Knowledge/CLAUDE.md) and it governs everything under that directory. Two rules matter most from outside it:

- **Wiki pages are never evidence.** A number entering a schema, a data file or a computation cites a raw source, never a wiki page.
- **The robotics pages are empty on purpose.** Filling them from recall would manufacture the exact uncited content the invariant refuses. `Knowledge/concepts/open-questions.md` is the reading list.

## Status

Scaffold. Schemas and decisions, no code. Do not write a README claim the code does not support.
