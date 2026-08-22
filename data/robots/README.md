# data/robots/

One robot per file, validated against [`schema/robot.schema.json`](../../schema/robot.schema.json), every entry citing its sources.

**Empty on purpose.** A first record needs a real mechanism with real datasheets in hand. A plausible arm written from recall — 300 mm links, ±90° joints, a 2 Nm servo — would validate cleanly and be entirely fictional, which is the precise failure the schema exists to prevent. It would also be the worst kind of seed data, because everything built afterwards would be tested against it.

Robot *designs* are shareable reference data and live here. Robots *you own* are mutable user state and do not — `owned-robots.json` is git-ignored, the same split OpenBuildCore applies to `inventory.json` and `machines.json` (its ADR-0001, platform decision PD-2).

See [`ROADMAP.md`](../../ROADMAP.md) — "A first robot record" is the next real milestone.
