# data/actuators/

One actuator per file, validated against [`schema/actuator.schema.json`](../../schema/actuator.schema.json).

**Empty on purpose**, for the same reason as [`data/robots/`](../robots/README.md).

When entries do arrive, expect most of them to have a `stall_torque_nm` and a null `continuous_torque_nm`, because that is what hobby datasheets publish. Resist the fraction-of-stall rule of thumb — `how_determined` exists to reject exactly that, and a mechanism specified from a guessed continuous torque is one that overheats at the bench rather than in the file.

An actuator that is also a catalogued part should carry its OpenPartsCore `part_id`. The facts about the part belong upstream; what belongs here is what it does in a mechanism.
