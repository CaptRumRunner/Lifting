"""SQLite persistence layer for Over40Lift.

No ORM — a thin wrapper around sqlite3 that returns/accepts the dataclasses
from models.py. Keeps the schema visible and the dependency footprint small.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from over40lift.models import (
    Goal,
    GoalStatus,
    MovementPattern,
    MuscleGroup,
    ReadinessFeedback,
    SorenessLevel,
    SorenessReport,
    WorkoutLogEntry,
)

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "over40lift.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_equipment (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    equipment_key TEXT NOT NULL,
    PRIMARY KEY (user_id, equipment_key)
);

CREATE TABLE IF NOT EXISTS soreness_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    muscle_group TEXT NOT NULL,
    level TEXT NOT NULL,
    reported_at TEXT NOT NULL,
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    target_muscle TEXT,
    target_movement TEXT,
    target_date TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workout_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    exercise_key TEXT NOT NULL,
    performed_at TEXT NOT NULL,
    sets INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight REAL DEFAULT 0,
    rpe REAL,
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS readiness_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    logged_at TEXT NOT NULL,
    sleep_quality INTEGER NOT NULL,
    stress_level INTEGER NOT NULL,
    overall_soreness INTEGER NOT NULL,
    motivation INTEGER NOT NULL,
    notes TEXT DEFAULT ''
);
"""


class Database:
    """Thin data-access layer, one instance per SQLite file."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ---- users ----

    def get_or_create_user(self, name: str) -> int:
        cur = self._conn.execute("SELECT id FROM users WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur = self._conn.execute(
            "INSERT INTO users (name, created_at) VALUES (?, ?)",
            (name, datetime.now().isoformat()),
        )
        self._conn.commit()
        return cur.lastrowid

    def list_users(self) -> list[str]:
        cur = self._conn.execute("SELECT name FROM users ORDER BY name")
        return [row["name"] for row in cur.fetchall()]

    # ---- equipment ----

    def set_user_equipment(self, user_id: int, equipment_keys: set[str]) -> None:
        self._conn.execute("DELETE FROM user_equipment WHERE user_id = ?", (user_id,))
        self._conn.executemany(
            "INSERT INTO user_equipment (user_id, equipment_key) VALUES (?, ?)",
            [(user_id, key) for key in equipment_keys],
        )
        self._conn.commit()

    def get_user_equipment(self, user_id: int) -> set[str]:
        cur = self._conn.execute(
            "SELECT equipment_key FROM user_equipment WHERE user_id = ?", (user_id,)
        )
        return {row["equipment_key"] for row in cur.fetchall()}

    # ---- soreness / injuries ----

    def add_soreness_report(self, user_id: int, report: SorenessReport) -> int:
        cur = self._conn.execute(
            """INSERT INTO soreness_reports
               (user_id, muscle_group, level, reported_at, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (
                user_id,
                report.muscle_group.value,
                report.level.value,
                report.reported_at.isoformat(),
                report.notes,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_current_soreness(self, user_id: int) -> dict[MuscleGroup, SorenessLevel]:
        """Latest report per muscle group (most recent report wins)."""
        cur = self._conn.execute(
            """SELECT muscle_group, level, reported_at FROM soreness_reports
               WHERE user_id = ? ORDER BY reported_at ASC""",
            (user_id,),
        )
        latest: dict[MuscleGroup, SorenessLevel] = {}
        for row in cur.fetchall():
            latest[MuscleGroup(row["muscle_group"])] = SorenessLevel(row["level"])
        return latest

    def clear_soreness(self, user_id: int, muscle_group: MuscleGroup) -> None:
        """Mark a muscle group as no longer sore by recording a fresh 'clear'.

        Implemented by deleting existing rows for that muscle so
        get_current_soreness no longer reports it.
        """
        self._conn.execute(
            "DELETE FROM soreness_reports WHERE user_id = ? AND muscle_group = ?",
            (user_id, muscle_group.value),
        )
        self._conn.commit()

    # ---- goals ----

    def add_goal(self, user_id: int, goal: Goal) -> int:
        cur = self._conn.execute(
            """INSERT INTO goals
               (user_id, description, target_muscle, target_movement,
                target_date, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                goal.description,
                goal.target_muscle.value if goal.target_muscle else None,
                goal.target_movement.value if goal.target_movement else None,
                goal.target_date.isoformat() if goal.target_date else None,
                goal.status.value,
                goal.created_at.isoformat(),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_active_goals(self, user_id: int) -> list[Goal]:
        cur = self._conn.execute(
            "SELECT * FROM goals WHERE user_id = ? AND status = 'active'", (user_id,)
        )
        goals = []
        for row in cur.fetchall():
            goals.append(
                Goal(
                    description=row["description"],
                    target_muscle=MuscleGroup(row["target_muscle"]) if row["target_muscle"] else None,
                    target_movement=MovementPattern(row["target_movement"]) if row["target_movement"] else None,
                    target_date=date.fromisoformat(row["target_date"]) if row["target_date"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    status=GoalStatus(row["status"]),
                    goal_id=row["id"],
                )
            )
        return goals

    def update_goal_status(self, goal_id: int, status: GoalStatus) -> None:
        self._conn.execute("UPDATE goals SET status = ? WHERE id = ?", (status.value, goal_id))
        self._conn.commit()

    # ---- workout logs ----

    def log_workout(self, user_id: int, entry: WorkoutLogEntry) -> int:
        cur = self._conn.execute(
            """INSERT INTO workout_logs
               (user_id, exercise_key, performed_at, sets, reps, weight, rpe, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                entry.exercise_key,
                entry.performed_at.isoformat(),
                entry.sets,
                entry.reps,
                entry.weight,
                entry.rpe,
                entry.notes,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_recent_workouts(self, user_id: int, limit_sessions: int = 6) -> list[WorkoutLogEntry]:
        """Return log entries from the most recent N distinct session dates."""
        cur = self._conn.execute(
            """SELECT DISTINCT date(performed_at) as d FROM workout_logs
               WHERE user_id = ? ORDER BY d DESC LIMIT ?""",
            (user_id, limit_sessions),
        )
        session_dates = [row["d"] for row in cur.fetchall()]
        if not session_dates:
            return []
        placeholders = ",".join("?" for _ in session_dates)
        cur = self._conn.execute(
            f"""SELECT * FROM workout_logs WHERE user_id = ?
                AND date(performed_at) IN ({placeholders})
                ORDER BY performed_at DESC""",
            (user_id, *session_dates),
        )
        return [
            WorkoutLogEntry(
                exercise_key=row["exercise_key"],
                performed_at=datetime.fromisoformat(row["performed_at"]),
                sets=row["sets"],
                reps=row["reps"],
                weight=row["weight"],
                rpe=row["rpe"],
                notes=row["notes"],
                log_id=row["id"],
            )
            for row in cur.fetchall()
        ]

    # ---- readiness feedback ----

    def add_feedback(self, user_id: int, feedback: ReadinessFeedback) -> int:
        cur = self._conn.execute(
            """INSERT INTO readiness_feedback
               (user_id, logged_at, sleep_quality, stress_level,
                overall_soreness, motivation, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                feedback.logged_at.isoformat(),
                feedback.sleep_quality,
                feedback.stress_level,
                feedback.overall_soreness,
                feedback.motivation,
                feedback.notes,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_latest_feedback(self, user_id: int) -> Optional[ReadinessFeedback]:
        cur = self._conn.execute(
            """SELECT * FROM readiness_feedback WHERE user_id = ?
               ORDER BY logged_at DESC LIMIT 1""",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return ReadinessFeedback(
            logged_at=datetime.fromisoformat(row["logged_at"]),
            sleep_quality=row["sleep_quality"],
            stress_level=row["stress_level"],
            overall_soreness=row["overall_soreness"],
            motivation=row["motivation"],
            notes=row["notes"],
            feedback_id=row["id"],
        )
