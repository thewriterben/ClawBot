---
title: ClawCam
type: entity
updated: 2026-08-22
sources:
  - ClawCam/README.md
  - ClawCam/schemas/ (device, event, health, observation)
  - ClawCam/brain/oh-ben-claw-adapter/
  - ClawCam/NEXT_PHASE_PLAN.md
---

# ClawCam

The perception peer. ESP32 camera-trap nodes, an offline-first field gateway, and an edge AI
operations layer. Wildlife monitoring is its first device profile; nine others cover home
security, bird feeders, livestock, apiaries, gardens and driveways.

Read on 2026-08-22 during the platform survey, written up late — see [[open-questions]].

## Shape

Three layers, and the middle one is the interesting choice:

- **Node** — ESP32 firmware: motion-triggered capture, local storage, deep sleep, OTA.
- **Gateway** — a field station on a Raspberry Pi or similar. FastAPI and SQLite, **offline
  first**: it holds detections, alert rules, schedules and zones without a network, and uploads
  opportunistically. Cloud is optional and disabled by default.
- **Brain** — [[oh-ben-claw]], consuming the gateway through an MCP stdio bridge.

Four JSON schemas define the wire: device, event, health, observation.

## The approval model, which ClawBot reinvented

The adapter exposes **35 auto-approved read tools and 11 approval-gated write tools**. Reads
execute; anything that changes the world asks first. It also carries call / session / forever
approval scopes and a plan mode, and its production-hardening pass added a webhook SSRF guard and
upload hardening.

That is the same split ClawBot ADR-0016 arrived at independently, and the same one
[[opendesigncore]] ADR-0009 states as platform policy. Three repos, three subject matters, one
shape: **reads execute, effects ask.**

ClawBot's version is degenerate in a way worth noting — its propose side is *empty*, because it
has no effects at all. ClawCam's is the fully populated case, and it is the one to look at if
ClawBot ever grows a tool that changes something.

The SSRF guard is a reminder of a category ClawBot has only one instance of: the risk that is not
about the domain. ClawBot's is `urdf.py import` taking a path, refused from the MCP surface for
the same reason a webhook target needs validating.

## Why a mechanism repo cares

**A mechanism that must act on something needs to know where the something is.** ClawBot answers
what a body can reach *relative to `base_link`* and explicitly refuses to claim world coordinates
(ADR-0009), because it has no source for where the base is. Perception is one of the things that
could supply that, and localization is [[oh-ben-claw]]'s competence.

The seam, if it is ever built, is the one this platform always uses: an observation record that
already had to exist, not an API. Nothing is asking for it yet, and that is recorded rather than
pitched.

## A ground rule worth stealing

> "No feature will be described as 'Production-ready' until verified with tests and reproducible
> steps."

ClawCam states its status per component — working, working in simulation, pending field
validation — and its whole software stack is **simulator-verified with hardware integration still
outstanding**. It says so at the top of its README rather than in a footnote.

That is the same discipline as ClawBot's rule against writing a README claim the code does not
support, and the same honesty problem: a system that works in simulation and has never met
hardware is a specific, nameable state, and naming it is cheaper than being found out.

ClawBot is in an adjacent state and should say so as plainly: it has one real actuator record and
**no robot record**, because that needs a real mechanism with real datasheets.
