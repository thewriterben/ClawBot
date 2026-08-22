---
title: URDF — the XSD and the parser that enforces it
type: source-summary
updated: 2026-08-22
sources:
  - https://raw.githubusercontent.com/ros/urdfdom/master/xsd/urdf.xsd (retrieved 2026-08-22)
  - https://raw.githubusercontent.com/ros/urdfdom/master/urdf_parser/src/joint.cpp (retrieved 2026-08-22)
---

# URDF — the XSD and the parser that enforces it

The first robotics source this wiki has. Read because ADR-0005 rests entirely on the claim
that ClawBot's record is "structurally URDF, so a converter is a mapping rather than a
reinterpretation" — a claim about a converter nobody had written. See [[urdf-round-trip]]
for what the reading did to that claim.

**Two sources, deliberately.** The XSD says what a URDF document may contain. `joint.cpp`
says what `urdfdom` — the reference parser every ROS consumer uses — actually accepts and
what it silently fills in. **They disagree**, and the disagreement is the interesting part.

## What the XSD defines

Six joint types: `revolute`, `continuous`, `prismatic`, `fixed`, `floating`, `planar`.

Joint children, all optional and at most one each: `origin`, `parent`, `child`, `axis`,
`calibration`, `dynamics`, `limit`, `safety_controller`, `mimic`.

| Element | Attributes | XSD default |
|---|---|---|
| `axis` | `xyz` | `"1 0 0"` |
| `limit` | `lower`, `upper`, `effort`, `velocity` | all `"0"` |
| `mimic` | `joint` (required), `multiplier`, `offset` | `1`, `0` |
| `safety_controller` | `soft_lower_limit`, `soft_upper_limit`, `k_position`, `k_velocity` (required) | `k_position` `0` |
| `dynamics` | `damping`, `friction` | both `"0"` |

`link` takes an **unbounded** choice of `inertial`, `visual` and `collision` children — many
of each, not one. `inertial` carries `mass` plus a full six-component inertia tensor
(`ixx ixy ixz iyy iyz izz`), each defaulting to `0`. `geometry` is a choice of `box`,
`cylinder`, `sphere`, `mesh`.

Also defined and outside ClawBot's model entirely: `transmission` (with `actuator`,
`mechanicalReduction`), `sensor`, and `gazebo`, the last accepting arbitrary content
under lax processing.

## What the parser does that the XSD does not say

- A `revolute` or `prismatic` joint with **no `limit` element at all is a parse error**.
  The parser logs "Joint [%s] is of type REVOLUTE but it does not specify limits" and
  returns false. The XSD marks `limit` optional; the parser does not.
- Inside a `limit`, **missing `effort` or `velocity` is also fatal**. Missing `lower` or
  `upper` is **not** — they default to `0` with only a debug log.
- A `revolute`, `continuous` or `prismatic` joint with no `axis` **defaults to (1, 0, 0)**
  with a debug log. Not an error.

**Conflict:** the XSD says `limit` is optional; `joint.cpp` refuses to parse a revolute
joint without one. Both are the same project. Anything reasoning about URDF from the schema
alone will be wrong about the most load-bearing element in the file.

## The two defaults that matter to this repo

`lower`/`upper` defaulting to `0`, and `axis` defaulting to `(1,0,0)`, are both cases of a
missing value becoming a **specific plausible value** rather than an absence. That is
[[inherited-invariants]] #3 inverted — the exact failure mode this platform is built to
refuse — sitting in the interchange format ClawBot has chosen to speak.

A joint with `<limit effort="10" velocity="1"/>` and no bounds parses cleanly and describes
a joint **locked at zero**. Nothing in the file distinguishes that from a joint whose
travel nobody recorded.
