# data/actuators/

One actuator per file, validated against [`schema/actuator.schema.json`](../../schema/actuator.schema.json).

**One entry**, as of 2026-08-22: the ROBOTIS Dynamixel XM430-W350, written from the vendor's own
e-Manual. It is here mainly to demonstrate what the schema refuses.

The prediction in this file's previous version was that most entries would carry a
`stall_torque_nm` and a null `continuous_torque_nm`, because that is what hobby datasheets
publish. The first entry confirms it on a **non-hobby** datasheet from a vendor who states the
distinction outright — "the given Stall torque rating for a servo is different from its
continuous output rating" — names it, publishes a performance graph, and then publishes no
continuous figure.

So capacity over the XM430 is underivable, and every `hold` answer naming it says so. That is
[ADR-0004](../../DECISIONS.md) working rather than failing. Resist the 30–50%-of-stall rule of
thumb: the range spans a factor of 1.67, so choosing a point in it is a guess, and
`how_determined` exists to reject exactly that. A mechanism specified from a guessed continuous
torque overheats at the bench rather than in the file.

**Torque and speed are arrays, indexed by voltage** ([ADR-0014](../../DECISIONS.md)). The XM430
publishes three rows spanning 3.8 to 4.8 N⋅m — a 26% spread across its own rated range — so a
derivation that picks the wrong row is wrong by that much, silently. A capacity derivation
selects the row matching `harness.power.supply_volts`, refuses to interpolate between rows, and
answers incomplete when no supply voltage is declared.

An actuator that is also a catalogued part should carry its OpenPartsCore `part_id`. The facts
about the part belong upstream; what belongs here is what it does in a mechanism. Note that OPC
files servos under **`electronic`**, not `mechanical` (its ADR-0005) — and that it has no entry
for this actuator, so the first record here carries no `part_id` at all.
