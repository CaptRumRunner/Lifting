"""Core data models used across Over40Lift.

Kept as plain dataclasses/enums so they're trivial to serialize to/from
SQLite rows in database.py without pulling in an ORM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class MuscleGroup(str, Enum):
    NECK = "neck"
    SHOULDERS = "shoulders"
    CHEST = "chest"
    UPPER_BACK = "upper_back"
    LOWER_BACK = "lower_back"
    LATS = "lats"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    FOREARMS = "forearms"
    CORE = "core"
    GLUTES = "glutes"
    QUADS = "quads"
    HAMSTRINGS = "hamstrings"
    CALVES = "calves"
    HIPS = "hips"
    KNEES = "knees"
    ELBOWS = "elbows"
    WRISTS = "wrists"
    ANKLES = "ankles"


class Equipment(str, Enum):
    BARBELL = "barbell"
    DUMBBELLS = "dumbbells"
    KETTLEBELL = "kettlebell"
    BENCH = "bench"
    SQUAT_RACK = "squat_rack"
    PULL_UP_BAR = "pull_up_bar"
    CABLE_MACHINE = "cable_machine"
    LEG_PRESS = "leg_press"
    RESISTANCE_BANDS = "resistance_bands"
    BATTLE_ROPES = "battle_ropes"
    ROWING_MACHINE = "rowing_machine"
    ASSAULT_BIKE = "assault_bike"
    MEDICINE_BALL = "medicine_ball"
    TRX = "trx_suspension_trainer"
    BODYWEIGHT_ONLY = "bodyweight_only"


class MovementPattern(str, Enum):
    SQUAT = "squat"
    HINGE = "hinge"
    LUNGE = "lunge"
    HORIZONTAL_PUSH = "horizontal_push"
    HORIZONTAL_PULL = "horizontal_pull"
    VERTICAL_PUSH = "vertical_push"
    VERTICAL_PULL = "vertical_pull"
    CARRY = "carry"
    ROTATION = "rotation"
    CONDITIONING = "conditioning"
    ISOLATION = "isolation"


class SorenessLevel(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    INJURY = "injury"

    @property
    def hard_exclude(self) -> bool:
        """Injuries hard-exclude a muscle group; soreness only deprioritizes it."""
        return self == SorenessLevel.INJURY


class GoalStatus(str, Enum):
    ACTIVE = "active"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"


@dataclass
class Exercise:
    key: str  # stable slug, e.g. "barbell_back_squat"
    name: str
    primary_muscles: tuple[MuscleGroup, ...]
    secondary_muscles: tuple[MuscleGroup, ...]
    equipment_required: tuple[Equipment, ...]
    movement_pattern: MovementPattern
    cns_demand: int  # 1 (low, e.g. curls) - 5 (high, e.g. heavy deadlifts)
    # Muscles/joints that flare up if aggravated, beyond the prime movers
    # (e.g. bench press also loads the shoulders and elbows).
    aggravates: tuple[MuscleGroup, ...] = field(default_factory=tuple)
    low_irritation_substitute: Optional[str] = None  # key of a gentler alternative

    def all_loaded_muscles(self) -> set[MuscleGroup]:
        return set(self.primary_muscles) | set(self.secondary_muscles) | set(self.aggravates)


@dataclass
class SorenessReport:
    muscle_group: MuscleGroup
    level: SorenessLevel
    reported_at: datetime
    notes: str = ""
    report_id: Optional[int] = None


@dataclass
class Goal:
    description: str
    target_muscle: Optional[MuscleGroup]
    target_movement: Optional[MovementPattern]
    target_date: Optional[date]
    created_at: datetime
    status: GoalStatus = GoalStatus.ACTIVE
    goal_id: Optional[int] = None


@dataclass
class WorkoutLogEntry:
    exercise_key: str
    performed_at: datetime
    sets: int
    reps: int
    weight: float = 0.0
    rpe: Optional[float] = None
    notes: str = ""
    log_id: Optional[int] = None


@dataclass
class ReadinessFeedback:
    """Daily check-in used to compute a composite readiness / CNS score."""

    logged_at: datetime
    sleep_quality: int  # 1-5
    stress_level: int  # 1-5 (5 = very stressed)
    overall_soreness: int  # 1-5 (5 = very sore everywhere)
    motivation: int  # 1-5
    notes: str = ""
    feedback_id: Optional[int] = None

    @property
    def cns_score(self) -> float:
        """Composite readiness score, 1 (fried) - 5 (fresh).

        sleep and motivation pull the score up; stress and overall soreness
        pull it down. Simple average of the "positive" and inverted
        "negative" inputs — deliberately simple/transparent so it's easy to
        tune later against real training response.
        """
        stress_inv = 6 - self.stress_level
        soreness_inv = 6 - self.overall_soreness
        return round((self.sleep_quality + self.motivation + stress_inv + soreness_inv) / 4, 2)

    @property
    def is_light_day(self) -> bool:
        return self.cns_score < 2.75
