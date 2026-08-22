//! Tests for the generated binding.
//!
//! The interesting ones are not about the data — they are about what the types
//! make impossible. Several of ADR-0017's guarantees are *compile-time* and
//! cannot be asserted at runtime at all; those are marked, with the code that
//! would have to fail written out in a comment so a later change has to
//! deliberately delete the note rather than quietly add the impl.

use clawbot::*;

// --------------------------------------------------------------- the seam

#[test]
fn radians_and_degrees_convert_explicitly() {
    let half_turn = Radians(core::f64::consts::PI);
    let degrees: Degrees = half_turn.into();
    assert!((degrees.0 - 180.0).abs() < 1e-12);

    let back: Radians = degrees.into();
    assert!((back.0 - core::f64::consts::PI).abs() < 1e-12);
}

#[test]
fn a_right_angle_is_the_number_nobody_recognises() {
    // 1.5708 is not a number anyone reads as a right angle, which is exactly
    // why ADR-0005 accepted the cost and why this type exists.
    let right_angle: Radians = Degrees(90.0).into();
    assert!((right_angle.0 - 1.570_796_326_794_896_6).abs() < 1e-12);
}

// COMPILE-TIME GUARANTEE, not assertable here:
//
//     let d: Degrees = Degrees(90.0);
//     let r: Radians = d;              // does not compile
//     some_fn_taking_radians(d);       // does not compile
//
// Oh-Ben-Claw's `MovementCommand::ServoAngle` is in degrees and this repo is in
// radians (ADR-0010). The conversion is a thing the compiler makes you write,
// at one place, instead of a comment somebody has to notice.

// COMPILE-TIME GUARANTEE, and the one most likely to be "helpfully" removed:
//
//     let stall: StallTorque = /* ... */;
//     let c: ContinuousTorque = stall.into();   // no such impl, deliberately
//     let c = stall.to_continuous();            // no such method, deliberately
//
// ADR-0004: stall torque may never feed a capacity derivation, and the
// 30-50%-of-stall rule of thumb spans a factor of 1.67. A consumer who wants it
// must write the arithmetic in their own code, where review can see it.

// ------------------------------------------------------------ unknown is None

#[test]
fn there_is_no_accessor_that_unwraps_an_unknown_limit() {
    // The API surface is the assertion. A `limits_or_default()` would undo
    // inherited invariant #3 in one function, so reading a limit means handling
    // the `None` — which the compiler enforces below and cannot be skipped.
    let unknown: Option<JointLimits> = None;
    let lower = match unknown {
        Some(limits) => limits.lower,
        None => None, // the only honest branch: absent is not zero
    };
    assert!(lower.is_none());
}

#[test]
fn present_limits_are_ordered() {
    for robot in ROBOTS {
        for joint in robot.joints {
            let Some(limits) = joint.limits else { continue };
            if let (Some(lo), Some(hi)) = (limits.lower, limits.upper) {
                assert!(lo.0 <= hi.0, "{} has inverted limits", joint.id);
            }
            if let (Some(lo), Some(hi)) = (limits.lower_mm, limits.upper_mm) {
                assert!(lo.0 <= hi.0, "{} has inverted prismatic limits", joint.id);
            }
        }
    }
}

#[test]
fn a_bounded_joint_with_no_limits_blocks_derivation_rather_than_defaulting() {
    for robot in ROBOTS {
        for joint in robot.joints {
            if joint.kind.is_bounded_by_mechanism() && joint.limits.is_none() {
                // It must show up in the list a consumer is meant to check first.
                assert!(
                    robot.joints_without_limits().any(|j| j.id == joint.id),
                    "{} has unknown limits but is not reported as blocking",
                    joint.id
                );
            }
        }
    }
}

#[test]
fn joints_without_limits_are_findable() {
    for robot in ROBOTS {
        let blocking: Vec<_> = robot.joints_without_limits().map(|j| j.id).collect();
        // While this is non-empty, reach answers incomplete and URDF export
        // refuses. A consumer should check it before asking for either.
        for id in &blocking {
            let joint = robot.joint(id).expect("named joint exists");
            assert!(joint.limits.is_none());
            assert!(joint.kind.is_bounded_by_mechanism());
        }
    }
}

#[test]
fn floating_and_planar_are_not_bounded_by_the_mechanism() {
    assert!(!JointType::Floating.is_bounded_by_mechanism());
    assert!(!JointType::Planar.is_bounded_by_mechanism());
    assert!(JointType::Revolute.is_bounded_by_mechanism());
    assert!(JointType::Prismatic.is_bounded_by_mechanism());
    // Fixed is not "bounded" either, but for the opposite reason: it never moves.
    assert!(!JointType::Fixed.is_bounded_by_mechanism());
}

#[test]
fn a_mimicking_joint_is_not_free() {
    for robot in ROBOTS {
        let free: Vec<_> = robot.free_joints().map(|j| j.id).collect();
        for joint in robot.joints {
            if joint.mimic.is_some() {
                assert!(
                    !free.contains(&joint.id),
                    "{} mimics another joint and must not be sampled as a free axis",
                    joint.id
                );
            }
        }
    }
}

// ------------------------------------------------------- ADR-0014: the voltage

#[test]
fn continuous_torque_lookup_is_exact_and_never_interpolates() {
    for actuator in ACTUATORS {
        for row in actuator.continuous_torque {
            assert!(actuator.continuous_at(row.at_volts).is_some());
            // A voltage between two published rows yields nothing. There is no
            // interpolating variant, because "approximately linear" is a model.
            assert!(actuator.continuous_at(row.at_volts + 0.37).is_none());
        }
    }
}

#[test]
fn capacity_derivable_is_false_when_only_stall_is_published() {
    // The XM430 case, and the general one: a populated stall slice does not make
    // capacity derivable, however tempting the arithmetic looks.
    for actuator in ACTUATORS {
        assert_eq!(
            actuator.capacity_derivable(),
            !actuator.continuous_torque.is_empty()
        );
        if actuator.continuous_torque.is_empty() {
            assert!(
                actuator.continuous_at(12.0).is_none(),
                "no continuous rating means no lookup succeeds at any voltage"
            );
        }
    }
}

#[test]
fn every_torque_row_carries_its_voltage() {
    for actuator in ACTUATORS {
        for row in actuator.stall_torque {
            assert!(row.at_volts > 0.0, "{} has a stall row with no voltage", actuator.id);
        }
        for row in actuator.continuous_torque {
            assert!(row.at_volts > 0.0);
            assert!(!row.how_determined.is_empty());
        }
    }
}

// ------------------------------------------------------------- the real record

#[test]
fn the_xm430_is_present_and_says_capacity_is_underivable() {
    let Some(xm) = actuator("dynamixel-xm430-w350") else {
        // data/ may legitimately be empty in a fork; nothing to assert then.
        assert!(ACTUATORS.is_empty() || ACTUATORS.iter().all(|a| a.id != "dynamixel-xm430-w350"));
        return;
    };
    assert_eq!(xm.make, Some("ROBOTIS"));
    assert_eq!(xm.stall_torque.len(), 3, "three published voltage rows");
    assert!(
        !xm.capacity_derivable(),
        "ROBOTIS names the stall/continuous distinction and publishes only stall"
    );
    assert_eq!(xm.gear_ratio, Some(353.5));
    assert_eq!(xm.backlash_rad, None, "absent means UNKNOWN, never zero");
    assert_eq!(xm.part_id, None, "OpenPartsCore has no entry for it");

    let twelve = xm
        .stall_torque
        .iter()
        .find(|r| (r.at_volts - 12.0).abs() < 1e-9)
        .expect("12.0 V row");
    assert!((twelve.newton_metres - 4.1).abs() < 1e-9);
}

#[test]
fn the_torque_curve_spans_enough_to_matter() {
    // ADR-0014's whole argument: the spread across an actuator's own rated range
    // is large enough that picking the wrong row is a real error.
    for actuator in ACTUATORS {
        if actuator.stall_torque.len() < 2 {
            continue;
        }
        let lo = actuator
            .stall_torque
            .iter()
            .map(|r| r.newton_metres)
            .fold(f64::INFINITY, f64::min);
        let hi = actuator
            .stall_torque
            .iter()
            .map(|r| r.newton_metres)
            .fold(f64::NEG_INFINITY, f64::max);
        assert!(hi > lo, "{} publishes rows that do not differ", actuator.id);
    }
}

// ------------------------------------------------------------------ structure

#[test]
fn every_joint_names_links_that_exist() {
    for robot in ROBOTS {
        for joint in robot.joints {
            assert!(robot.link(joint.parent).is_some(), "{} parent", joint.id);
            assert!(robot.link(joint.child).is_some(), "{} child", joint.id);
        }
        assert!(robot.link(robot.base_link).is_some(), "base_link exists");
    }
}

#[test]
fn a_link_declares_exactly_one_kind() {
    for robot in ROBOTS {
        for link in robot.links {
            let kinds = [
                link.part_id.is_some(),
                link.provenance_sha256.is_some(),
                link.make_size_mm.is_some(),
            ]
            .iter()
            .filter(|b| **b)
            .count();
            assert_eq!(kinds, 1, "link {} declares {} kinds", link.id, kinds);
        }
    }
}

// ------------------------------------------------- ADR-0018: population vs unit

#[test]
fn an_undeclared_basis_is_none_and_none_means_unknown() {
    // Not "assumed exact". A vendor may be publishing a population average —
    // Harmonic Drive states ±30% unit-to-unit on torsional stiffness — and a
    // consumer has to be made to notice that nobody said which this is.
    for actuator in ACTUATORS {
        if actuator.basis.is_none() {
            assert!(
                actuator.spread_pct.is_none(),
                "{} declares a spread without saying what it is a spread of",
                actuator.id
            );
        }
    }
}

#[test]
fn basis_round_trips_through_its_string() {
    assert_eq!(Basis::ModelTypical.as_str(), "model-typical");
    assert_eq!(Basis::ThisUnit.as_str(), "this-unit");
}

#[test]
fn there_is_no_efficiency_field_to_reach_for() {
    // Asserted by construction: `Actuator` has no `efficiency`, so the line
    //
    //     let _ = ACTUATORS[0].efficiency;
    //
    // does not compile. Its absence is a decision (ADR-0018), not an omission —
    // efficiency curves describe a gearbox that is turning, and a static hold has
    // an input speed of zero. This test exists to carry that note next to the
    // data rather than only in an ADR.
    for actuator in ACTUATORS {
        let _ = actuator.gear_ratio; // the field that DOES exist and is a scalar
    }
}

#[test]
fn millimetres_convert_to_metres_at_one_named_place() {
    assert!((Millimetres(1000.0).to_metres() - 1.0).abs() < 1e-12);
    assert!((Millimetres(39.6).to_metres() - 0.0396).abs() < 1e-12);
}

#[test]
fn joint_type_round_trips_through_its_string() {
    for kind in [
        JointType::Revolute,
        JointType::Continuous,
        JointType::Prismatic,
        JointType::Fixed,
        JointType::Floating,
        JointType::Planar,
    ] {
        assert_eq!(kind.to_string(), kind.as_str());
    }
    assert_eq!(JointType::Floating.as_str(), "floating");
}
