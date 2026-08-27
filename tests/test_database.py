from datetime import date, datetime

import pytest

from over40lift.database import Database
from over40lift.models import (
    Goal,
    MovementPattern,
    MuscleGroup,
    ReadinessFeedback,
    SorenessLevel,
    SorenessReport,
    WorkoutLogEntry,
)


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "test.db")
    yield database
    database.close()


def test_get_or_create_user_is_idempotent(db):
    id1 = db.get_or_create_user("alex")
    id2 = db.get_or_create_user("alex")
    assert id1 == id2
    assert db.list_users() == ["alex"]


def test_equipment_roundtrip(db):
    uid = db.get_or_create_user("sam")
    db.set_user_equipment(uid, {"barbell", "dumbbells"})
    assert db.get_user_equipment(uid) == {"barbell", "dumbbells"}
    # Overwrites rather than appends.
    db.set_user_equipment(uid, {"kettlebell"})
    assert db.get_user_equipment(uid) == {"kettlebell"}


def test_soreness_latest_report_wins(db):
    uid = db.get_or_create_user("jo")
    db.add_soreness_report(
        uid,
        SorenessReport(MuscleGroup.SHOULDERS, SorenessLevel.MILD, datetime(2026, 1, 1)),
    )
    db.add_soreness_report(
        uid,
        SorenessReport(MuscleGroup.SHOULDERS, SorenessLevel.INJURY, datetime(2026, 1, 2)),
    )
    current = db.get_current_soreness(uid)
    assert current[MuscleGroup.SHOULDERS] == SorenessLevel.INJURY


def test_clear_soreness(db):
    uid = db.get_or_create_user("jo")
    db.add_soreness_report(
        uid,
        SorenessReport(MuscleGroup.KNEES, SorenessLevel.MODERATE, datetime.now()),
    )
    assert MuscleGroup.KNEES in db.get_current_soreness(uid)
    db.clear_soreness(uid, MuscleGroup.KNEES)
    assert MuscleGroup.KNEES not in db.get_current_soreness(uid)


def test_goal_roundtrip(db):
    uid = db.get_or_create_user("pat")
    db.add_goal(
        uid,
        Goal(
            description="Squat 315x3",
            target_muscle=MuscleGroup.QUADS,
            target_movement=MovementPattern.SQUAT,
            target_date=date(2026, 12, 1),
            created_at=datetime.now(),
        ),
    )
    goals = db.get_active_goals(uid)
    assert len(goals) == 1
    assert goals[0].description == "Squat 315x3"
    assert goals[0].target_muscle == MuscleGroup.QUADS


def test_workout_log_and_recent_sessions(db):
    uid = db.get_or_create_user("ren")
    db.log_workout(
        uid,
        WorkoutLogEntry(
            exercise_key="barbell_back_squat",
            performed_at=datetime(2026, 1, 1, 10, 0),
            sets=5, reps=5, weight=225,
        ),
    )
    db.log_workout(
        uid,
        WorkoutLogEntry(
            exercise_key="barbell_bench_press",
            performed_at=datetime(2026, 1, 3, 10, 0),
            sets=5, reps=5, weight=185,
        ),
    )
    recent = db.get_recent_workouts(uid, limit_sessions=6)
    assert len(recent) == 2
    keys = {e.exercise_key for e in recent}
    assert keys == {"barbell_back_squat", "barbell_bench_press"}


def test_feedback_latest_only(db):
    uid = db.get_or_create_user("ren")
    db.add_feedback(
        uid,
        ReadinessFeedback(
            logged_at=datetime(2026, 1, 1),
            sleep_quality=2, stress_level=4, overall_soreness=4, motivation=2,
        ),
    )
    db.add_feedback(
        uid,
        ReadinessFeedback(
            logged_at=datetime(2026, 1, 2),
            sleep_quality=5, stress_level=1, overall_soreness=1, motivation=5,
        ),
    )
    latest = db.get_latest_feedback(uid)
    assert latest.sleep_quality == 5
    assert latest.cns_score == 5.0
    assert latest.is_light_day is False
