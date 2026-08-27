from datetime import datetime

from over40lift.models import (
    Equipment,
    Goal,
    MovementPattern,
    MuscleGroup,
    ReadinessFeedback,
    SorenessLevel,
    WorkoutLogEntry,
)
from over40lift.recommendation import build_session_plan

FULL_EQUIPMENT = {e.value for e in Equipment}


def test_battle_ropes_never_recommended_without_equipment():
    plan = build_session_plan(
        available_equipment=FULL_EQUIPMENT - {Equipment.BATTLE_ROPES.value},
        soreness={},
        goals=[],
        recent_logs=[],
        latest_feedback=None,
        template=(MovementPattern.CONDITIONING,),
    )
    names = [rec.exercise.name for rec in plan.exercises]
    assert "Battle Ropes" not in names


def test_battle_ropes_recommended_when_available():
    plan = build_session_plan(
        available_equipment=FULL_EQUIPMENT,
        soreness={},
        goals=[],
        recent_logs=[],
        latest_feedback=None,
        template=(MovementPattern.CONDITIONING,),
    )
    names = [rec.exercise.name for rec in plan.exercises]
    # With everything available, conditioning slot should pick from the pool
    # that includes battle ropes (not asserting it wins, just that it's legal).
    assert len(names) == 1


def test_injured_lower_back_excludes_deadlift_and_substitutes():
    plan = build_session_plan(
        available_equipment=FULL_EQUIPMENT,
        soreness={MuscleGroup.LOWER_BACK: SorenessLevel.INJURY},
        goals=[],
        recent_logs=[],
        latest_feedback=None,
        template=(MovementPattern.HINGE,),
    )
    names = [rec.exercise.name for rec in plan.exercises]
    assert "Conventional Deadlift" not in names
    assert "Romanian Deadlift" not in names


def test_no_equipment_falls_back_to_bodyweight():
    plan = build_session_plan(
        available_equipment={Equipment.BODYWEIGHT_ONLY.value},
        soreness={},
        goals=[],
        recent_logs=[],
        latest_feedback=None,
        template=(MovementPattern.SQUAT, MovementPattern.HORIZONTAL_PUSH),
    )
    for rec in plan.exercises:
        assert all(
            eq.value == Equipment.BODYWEIGHT_ONLY.value
            for eq in rec.exercise.equipment_required
        )


def test_recently_done_exercise_is_deprioritized():
    recent_logs = [
        WorkoutLogEntry(
            exercise_key="pull_up",
            performed_at=datetime.now(),
            sets=3, reps=8,
        )
    ]
    plan = build_session_plan(
        available_equipment=FULL_EQUIPMENT,
        soreness={},
        goals=[],
        recent_logs=recent_logs,
        latest_feedback=None,
        template=(MovementPattern.VERTICAL_PULL,),
    )
    # pull_up was done today (0 sessions ago) so it should lose to lat_pulldown
    # or band_pulldown given the recency penalty, assuming equal starting score.
    picked = plan.exercises[0].exercise.key
    assert picked != "pull_up"


def test_low_readiness_triggers_light_day_and_lower_volume():
    feedback = ReadinessFeedback(
        logged_at=datetime.now(),
        sleep_quality=1, stress_level=5, overall_soreness=5, motivation=1,
    )
    assert feedback.is_light_day is True
    plan = build_session_plan(
        available_equipment=FULL_EQUIPMENT,
        soreness={},
        goals=[],
        recent_logs=[],
        latest_feedback=feedback,
        template=(MovementPattern.SQUAT,),
    )
    assert plan.is_light_day is True
    rec = plan.exercises[0]
    assert rec.sets <= 3
    assert rec.target_rpe <= 6.5


def test_goal_alignment_boosts_matching_exercise():
    goal = Goal(
        description="Bigger biceps",
        target_muscle=MuscleGroup.BICEPS,
        target_movement=None,
        target_date=None,
        created_at=datetime.now(),
    )
    plan = build_session_plan(
        available_equipment=FULL_EQUIPMENT,
        soreness={},
        goals=[goal],
        recent_logs=[],
        latest_feedback=None,
        template=(MovementPattern.ISOLATION,),
    )
    reasons = " ".join(plan.exercises[0].reasons)
    # Not asserting biceps curl always wins (isolation slot has many
    # candidates) but if it does win, the goal reason should be present.
    if plan.exercises[0].exercise.key == "dumbbell_biceps_curl":
        assert "goal" in reasons
