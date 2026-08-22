# ClawBot

Describe a robot once — links, joints, actuators, and where every number came from. Then ask what it can actually reach, and what it can actually hold there.

**Status:** scaffold. Schemas, decisions and a knowledge base; **no code yet**. What is written down here is the contract an implementation will have to satisfy, and the reasoning it is not allowed to quietly discard.

## Where it sits

Fifth peer in the platform (OpenDesignCore ADR-0007):

| | |
|---|---|
| [OpenPartsCore](https://github.com/thewriterben/OpenPartsCore) | what parts *are* — cited reference data |
| [OpenBuildCore](https://github.com/thewriterben/OpenBuildCore) | what you *have*, and what you could make of it |
| [OpenCircuitCore](https://github.com/thewriterben/OpenCircuitCore) | electronics design for the thing you decided to build |
| [OpenDesignCore](https://github.com/thewriterben/OpenDesignCore) | the geometry, validated and provenance-carrying |
| **ClawBot** | the thing that moves — links, joints, actuators, and what they can reach |

Like its peers, ClawBot **imports nothing from them**. A link references an OpenPartsCore `part_id`; a fabricated link references an OpenDesignCore provenance record. The peers meet at data that already had to exist, not at an API (ADR-0005).

## Why a fifth repo, and not a machine kind in OpenBuildCore

OBC already models machines you own — envelope, materials, throughput (its ADR-0005). A robot arm looks like it belongs there. It does not, for three reasons that ADR-0001 works through:

**A machine's capability is a box; a robot's is not.** `envelope_mm: {x, y, z}` answers "does the part fit" with an axis-aligned containment test. The set of points a 5-DOF arm can reach is a non-convex, possibly disconnected volume with holes in it, determined by joint limits and link lengths. There is no box that describes it without lying in one direction or the other.

**Payload is a function of pose.** A printer's material list does not change when the nozzle moves. An arm that lifts 3 kg tucked in lifts a fraction of that at full extension, because the load torque at the shoulder is force times moment arm. A single `payload_kg` field is a number that is true at exactly one configuration and silently wrong everywhere else.

**A robot is on both sides of OBC's split.** OBC deliberately separates cited reference data from mutable user state (platform decision PD-2). A robot is a *design* — shareable, reviewable, citable — and also *a thing you own*, and also *a thing you are trying to build*. Forcing it into one side of that split loses the other two.

## What a robot record says

A robot is a tree of **links** connected by **joints**, driven by **actuators**. The shape follows URDF rather than Denavit–Hartenberg parameters, because DH has two incompatible conventions in common use and a table of four numbers does not say which one it is (ADR-0004).

```
robot
├── links[]       a rigid body. Either a part_id from OpenPartsCore,
│                 or a `make` — something you fabricate, carrying size and material
│                 exactly as OpenBuildCore's third requirement kind does.
├── joints[]      parent link, child link, type, origin transform, axis,
│                 and limits: travel, effort, velocity — each with a source
└── actuators[]   what drives a joint. Torque and speed come from a datasheet
                  with a citation, or they are absent.
```

Every record needs a `source.citation`, the same gate the reference registry uses. A joint limit is a physical claim about hardware.

## The two rules with teeth

**Reach is derived, never declared** (ADR-0002). A vendor's "850 mm reach" is a radius to some unstated frame, before a tool, ignoring self-collision and the joint limits that make parts of that sphere unreachable. ClawBot will not carry a `reach_mm` field, because a number that looks like a measurement and is actually a marketing figure is worse than no number. Reach is computed from the joint model, or the answer is that the model is incomplete and which joint is missing.

**Payload is a function of pose** (ADR-0003). A payload figure is accepted only as a `measured_payload` that names the pose it was measured at and how. Otherwise capacity is derived from actuator effort limits and geometry, and reported per-pose. Absence of a payload answer is the honest default.

Both are the same discipline OpenBuildCore applied to print time: *if nobody measured it, and it cannot be derived from something that was, the answer is "I cannot tell you"* — which is less useful than a number and more useful than a wrong one.

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
