# ClawBot

Describe a robot once — links, joints, actuators, and where every number came from. Then ask what it can actually reach, and what it can actually hold there.

**Status:** pre-alpha. Four schemas, twenty-one ADRs, six scripts, an MCP surface, a zero-dependency Rust binding, **152 Python tests and 35 Rust tests**, all run by CI, and a knowledge base whose robotics half is no longer empty. `data/` holds one real record — a Dynamixel XM430-W350, written from the vendor's own manual, whose continuous torque is `null` because ROBOTIS names the stall/continuous distinction and then publishes only stall. No robot record yet: that needs a real mechanism in hand, and a described-from-memory arm is exactly the invented data the schema exists to refuse.

```
python scripts/validate.py                     # uncited claims, degrees in _rad, non-trees
python scripts/kinematics.py reach <id>        # sampled workspace, with every assumption
python scripts/kinematics.py hold <id> --pose  # static capacity, labelled an upper bound
python scripts/manifest.py <id> --as-project   # the bill of parts, in OBC's vocabulary
python scripts/affordance.py <id> --target X,Y,Z --payload-g N   # can this body do it?
python scripts/urdf.py import <file.urdf>      # reads the XML, not the parsed tree
python -m clawbot_mcp.server                   # the same answers over MCP
python scripts/emit_rust.py --check            # is the committed binding stale?
python -m pytest tests/ -q                     # 152 tests
cd bindings/rust && cargo test                 # 35 more, 3 of them compile_fail
```

CI runs all of it on every push, and refuses to start if the two peers those tests depend on are
missing — a skipped seam test proves nothing while reading as green. A second workflow checks
citation links weekly, because every robotics source here is cited by URL rather than copied
into the repo, which makes link rot the whole exposure.

The tests are the interesting part. 31 are negative — every rule with teeth, proven to bite. 26 are known answers rather than pinned outputs: a 1 kg mass on a 100 mm arm loads the joint with 0.980665 N⋅m whether or not this code has ever run. 19 run the URDF round trip that [ADR-0007](DECISIONS.md) makes claims about, including one asserting that provenance *does not* survive it. 16 guard the affordance composition, one of them named `test_there_is_no_can_verdict_anywhere`. 10 guard the MCP surface against the two ways it would quietly go wrong — a tool that takes a file path, and a tool that strips its caveats. And two validate emitted output against **OpenBuildCore's own schema file**, not a copy of it — skipping honestly if that repo is not checked out beside this one.

Three of the Rust tests are `compile_fail` doctests, which is the only way to assert a guarantee that exists in the type system: passing `Degrees` where `Radians` is required does not compile, and neither does converting a `StallTorque` into a `ContinuousTorque`.

## Where it sits

Fifth peer in the platform — by the shape of the argument in [ADR-0001](DECISIONS.md), not by
anyone's blessing. This line used to cite OpenDesignCore ADR-0007, which enumerates the platform's
peers and **does not name this repo**; a citation pointing at a document that does not say the
thing being cited is the precise failure this platform's discipline exists to prevent, and it sat
in the README of the repo that keeps saying so. Reported as
[OpenDesignCore#15](https://github.com/thewriterben/OpenDesignCore/issues/15) and corrected here
rather than left pending their answer.

The peers, whatever the count turns out to be:

| | |
|---|---|
| [OpenPartsCore](https://github.com/thewriterben/OpenPartsCore) | what parts *are* — cited reference data |
| [OpenBuildCore](https://github.com/thewriterben/OpenBuildCore) | what you *have*, and what you could make of it |
| [OpenCircuitCore](https://github.com/thewriterben/OpenCircuitCore) | electronics design for the thing you decided to build |
| [OpenDesignCore](https://github.com/thewriterben/OpenDesignCore) | the geometry, validated and provenance-carrying |
| **ClawBot** | the thing that moves — links, joints, actuators, and what they can reach |

Like its peers, ClawBot **imports nothing from them**. A link references an OpenPartsCore `part_id`; a fabricated link references an OpenDesignCore provenance record. The peers meet at data that already had to exist, not at an API (ADR-0006).

## Why a fifth repo, and not a machine kind in OpenBuildCore

OBC already models machines you own — envelope, materials, throughput (its ADR-0005). A robot arm looks like it belongs there. It does not, for three reasons that ADR-0001 works through:

**A machine's capability is a box; a robot's is not.** `envelope_mm: {x, y, z}` answers "does the part fit" with an axis-aligned containment test. The set of points a 5-DOF arm can reach is a non-convex, possibly disconnected volume with holes in it, determined by joint limits and link lengths. There is no box that describes it without lying in one direction or the other.

**Payload is a function of pose.** A printer's material list does not change when the nozzle moves. An arm that lifts 3 kg tucked in lifts a fraction of that at full extension, because the load torque at the shoulder is force times moment arm. A single `payload_kg` field is a number that is true at exactly one configuration and silently wrong everywhere else.

**A robot is on both sides of OBC's split.** OBC deliberately separates cited reference data from mutable user state (platform decision PD-2). A robot is a *design* — shareable, reviewable, citable — and also *a thing you own*, and also *a thing you are trying to build*. Forcing it into one side of that split loses the other two.

## What a robot record says

A robot is a tree of **links** connected by **joints**, driven by **actuators**. The shape follows URDF rather than Denavit–Hartenberg parameters, because DH has two incompatible conventions in common use and a table of four numbers does not say which one it is (ADR-0005) — and, it turned out on reading the sources, because a DH table cannot carry the tool transform or branch at all (ADR-0007).

```
robot
├── links[]       a rigid body. Either a part_id from OpenPartsCore,
│                 or a `make` — something you fabricate, carrying size and material
│                 exactly as OpenBuildCore's third requirement kind does,
│                 or a provenance_ref — an OpenDesignCore artifact hash.
├── joints[]      parent link, child link, type, origin transform, axis,
│                 and limits: travel, effort, velocity — each with a source.
│                 A `mimic` makes one joint follow another, so a parallel gripper
│                 is expressible without a loop in the graph (ADR-0008).
└── actuators[]   what drives a joint. Torque and speed come from a datasheet
                  with a citation, or they are absent.

assembly         a DAG of steps — what joins what, which fasteners at what torque,
                 which steps cannot be undone. No modelled build time (ADR-0011).

harness          which actuator is on which channel, and which cables cross which
                 joints — because a cable that crosses a joint is a joint limit,
                 and an unchecked one makes reach over-claim (ADR-0012).
```

The graph is a **tree**, and trees branch: a torso with two arms and a head is one robot
record. All six URDF joint types are available, including `floating` and `planar`, so a
mechanism on a moving base is describable — and every derived answer is explicitly relative to
`base_link`, because ClawBot has no source for where that is in the world (ADR-0009).

Every record needs a `source.citation`, the same gate the reference registry uses. A joint limit is a physical claim about hardware.

## The rules with teeth

**Reach is derived, never declared** (ADR-0003). A vendor's "850 mm reach" is a radius to some unstated frame, before a tool, ignoring self-collision and the joint limits that make parts of that sphere unreachable. ClawBot will not carry a `reach_mm` field, because a number that looks like a measurement and is actually a marketing figure is worse than no number. Reach is computed from the joint model, or the answer is that the model is incomplete and which joint is missing.

**Payload is a function of pose** (ADR-0004). A payload figure is accepted only as a `measured_payload` that names the pose it was measured at and how. Otherwise capacity is derived from actuator effort limits and geometry, and reported per-pose. Absence of a payload answer is the honest default.

Both are the same discipline OpenBuildCore applied to print time: *if nobody measured it, and it cannot be derived from something that was, the answer is "I cannot tell you"* — which is less useful than a number and more useful than a wrong one.

A third rule joined them once the computation existed. **A sampled workspace only ever proves the positive** (ADR-0013). "Reachable" is a claim, and carries the pose that got there. "Not reachable" is never returned — the verdict says `no-sample-reached-it` and names how many samples were drawn, because a sampled set is inner-bounded and its silence is not evidence.

And a fourth, from the wiring: **a cable that crosses a joint is a joint limit** (ADR-0012). `permits_full_travel: null` means nobody checked, never that it is fine, and a reachability answer over an unchecked harness says so in the value.

The fifth only appeared when the first two were composed. **ClawBot cannot tell you a robot *can* do something** (ADR-0015). Sampled reach is sound positive and unsound negative; static capacity is sound *negative* and unsound positive. Put them together and there is no combination that yields a provable yes — so `affordance.py` answers `cannot` (a real claim: an upper bound was exceeded, and real capacity is lower still), `within-static-bound` (the closest thing to yes, and not a guarantee), `unproven`, or `incomplete`. There is deliberately no affordance score: a float in [0,1] is a frequency estimate, no trials were run, and SayCan-style consumers *multiply* affordances — so a fabricated one would propagate into a product and vanish. Rank on the margin, which has units.

## The Rust binding

`bindings/rust/` is generated from `data/` by `scripts/emit_rust.py`, committed, and gated by
`--check` — OpenPartsCore's discipline (its ADR-0003), for the reason that repo exists: three
hand-maintained copies of a registry drifting apart is a documented failure, not a hypothetical.
Zero dependencies, because a consumer should not take serde to read a static body model.

The reason it is worth having is not the data — `data/` is one actuator. It is that **every
refusal in this repo is otherwise a convention**, enforced by a validator, a docstring and an
ADR, all of which are advice. In the binding they are compile errors (ADR-0017):

- `Radians` and `Degrees` are distinct types with explicit conversion. Oh-Ben-Claw's
  `ServoAngle` is degrees and this repo is radians; ADR-0010 called that a seam and enforced it
  with nothing. Now the seam fails to compile instead of failing on the bench.
- `StallTorque` and `ContinuousTorque` are distinct **with no conversion between them** — no
  `From`, no `to_continuous()`, no feature flag. A consumer who wants the 30–50% rule of thumb
  must write that arithmetic themselves, where review can see it.
- Unknown stays `Option`, and there is deliberately no `limits_or_default()`. Rust makes you
  confront the `None`, which is inherited invariant #3 moved out of a document.
- `CableRun::permits_full_travel` is `Option<bool>`, so the compiler will not let a caller
  collapse *nobody checked* into *does not permit* without writing the match arm (ADR-0012).

The crate carries the **control contract** ADR-0010 promised — `Harness`, `Channel`, and the two
facts no amount of modelling recovers: which way the actuator was installed (`inverted`) and
where its zero is (`zero_offset`). `Channel::actuator_angle` applies both and **returns
radians**, so the degrees conversion stays at the consumer's own edge and the whole seam is one
legible line: `Degrees::from(channel.actuator_angle(target))` (ADR-0020).

Assemblies are deliberately *not* emitted — a DAG of bench steps is for a person, and no runtime
reads it.

## Knowledge base

[`Knowledge/`](Knowledge/) is an LLM-maintained wiki following the LLM Wiki pattern, matching the instantiation already running in OpenDesignCore's `wiki/`. It carries what has been read about this domain and this platform, and — just as importantly — an explicit queue of what has **not** been read yet. See [`Knowledge/CLAUDE.md`](Knowledge/CLAUDE.md) for the schema and [`Knowledge/index.md`](Knowledge/index.md) for the catalogue.

The robotics half of the wiki is deliberately empty. Writing kinematics pages from an assistant's own recall would produce exactly the uncited, plausible-looking numbers this platform exists to refuse. Those pages get written when sources arrive; until then they are listed in [`Knowledge/concepts/open-questions.md`](Knowledge/concepts/open-questions.md) as a reading list.

## Not this

- **Not a simulator.** No dynamics integration, no contact physics, no rendering. Those are Gazebo's, MuJoCo's and Isaac's job.
- **Not a motion planner.** Collision-free trajectories are a solved problem with mature implementations; ClawBot describes the robot they plan for.
- **Not a runtime.** Nothing here actuates anything. Commanding a physical robot is Oh-Ben-Claw's embodied stack, behind its Track 0 safety gate.
- **Not a parts database.** Facts about servos and bearings belong in OpenPartsCore with citations.
- **Not a URDF replacement.** URDF is the interchange format and ClawBot should read and write it. The difference is provenance: URDF has nowhere to record where a joint limit came from.

## License

Apache-2.0 (platform decision PD-4) — see [LICENSE](LICENSE).
