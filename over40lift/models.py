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


# Which body-diagram view (front/back) each muscle group is shown under in
# the Soreness tab. Each muscle appears in exactly one view — the
# underlying soreness state is the same regardless of which view it's
# tapped from, this just controls layout.
BODY_VIEW_FRONT: tuple[MuscleGroup, ...] = (
    MuscleGroup.NECK, MuscleGroup.SHOULDERS, MuscleGroup.CHEST,
    MuscleGroup.BICEPS, MuscleGroup.FOREARMS, MuscleGroup.WRISTS,
    MuscleGroup.CORE, MuscleGroup.HIPS, MuscleGroup.QUADS,
    MuscleGroup.KNEES, MuscleGroup.ANKLES,
)
BODY_VIEW_BACK: tuple[MuscleGroup, ...] = (
    MuscleGroup.UPPER_BACK, MuscleGroup.LATS, MuscleGroup.TRICEPS,
    MuscleGroup.ELBOWS, MuscleGroup.LOWER_BACK, MuscleGroup.GLUTES,
    MuscleGroup.HAMSTRINGS, MuscleGroup.CALVES,
)


class Equipment(str, Enum):
    # Free weights
    BARBELL = "barbell"
    DUMBBELLS = "dumbbells"
    KETTLEBELL = "kettlebell"
    EZ_CURL_BAR = "ez_curl_bar"
    TRAP_BAR = "trap_bar"
    SAFETY_SQUAT_BAR = "safety_squat_bar"
    BENCH = "bench"
    SQUAT_RACK = "squat_rack"
    POWER_RACK = "power_rack"
    SMITH_MACHINE = "smith_machine"
    LANDMINE = "landmine_attachment"
    # Machines
    CABLE_MACHINE = "cable_machine"
    LAT_PULLDOWN = "lat_pulldown_machine"
    LEG_PRESS = "leg_press"
    LEG_EXTENSION = "leg_extension_machine"
    LEG_CURL_MACHINE = "leg_curl_machine"
    HACK_SQUAT = "hack_squat_machine"
    CHEST_PRESS_MACHINE = "chest_press_machine"
    SHOULDER_PRESS_MACHINE = "shoulder_press_machine"
    PEC_DECK = "pec_deck"
    # Cardio
    TREADMILL = "treadmill"
    ASSAULT_BIKE = "assault_bike"
    SPIN_BIKE = "spin_bike"
    ROWING_MACHINE = "rowing_machine"
    SKI_ERG = "ski_erg"
    STAIR_CLIMBER = "stair_climber"
    ELLIPTICAL = "elliptical"
    # CrossFit / functional
    PULL_UP_BAR = "pull_up_bar"
    GYMNASTIC_RINGS = "gymnastic_rings"
    CLIMBING_ROPE = "climbing_rope"
    BATTLE_ROPES = "battle_ropes"
    MEDICINE_BALL = "medicine_ball"
    SLAM_BALL = "slam_ball"
    WALL_BALL = "wall_ball"
    PLYO_BOX = "plyo_box"
    JUMP_ROPE = "jump_rope"
    SLED = "sled_prowler"
    FARMERS_CARRY_HANDLES = "farmers_carry_handles"
    GHD = "ghd_glute_ham_developer"
    DIP_STATION = "dip_station"
    TRX = "trx_suspension_trainer"
    RESISTANCE_BANDS = "resistance_bands"
    # Other
    FOAM_ROLLER = "foam_roller"
    BODYWEIGHT_ONLY = "bodyweight_only"


EQUIPMENT_CATEGORIES: dict[str, tuple[Equipment, ...]] = {
    "Free weights": (
        Equipment.BARBELL, Equipment.DUMBBELLS, Equipment.KETTLEBELL,
        Equipment.EZ_CURL_BAR, Equipment.TRAP_BAR, Equipment.SAFETY_SQUAT_BAR,
        Equipment.BENCH, Equipment.SQUAT_RACK, Equipment.POWER_RACK,
        Equipment.SMITH_MACHINE, Equipment.LANDMINE,
    ),
    "Machines": (
        Equipment.CABLE_MACHINE, Equipment.LAT_PULLDOWN, Equipment.LEG_PRESS,
        Equipment.LEG_EXTENSION, Equipment.LEG_CURL_MACHINE, Equipment.HACK_SQUAT,
        Equipment.CHEST_PRESS_MACHINE, Equipment.SHOULDER_PRESS_MACHINE, Equipment.PEC_DECK,
    ),
    "Cardio": (
        Equipment.TREADMILL, Equipment.ASSAULT_BIKE, Equipment.SPIN_BIKE,
        Equipment.ROWING_MACHINE, Equipment.SKI_ERG, Equipment.STAIR_CLIMBER,
        Equipment.ELLIPTICAL,
    ),
    "CrossFit / functional": (
        Equipment.PULL_UP_BAR, Equipment.GYMNASTIC_RINGS, Equipment.CLIMBING_ROPE,
        Equipment.BATTLE_ROPES, Equipment.MEDICINE_BALL, Equipment.SLAM_BALL,
        Equipment.WALL_BALL, Equipment.PLYO_BOX, Equipment.JUMP_ROPE,
        Equipment.SLED, Equipment.FARMERS_CARRY_HANDLES, Equipment.GHD,
        Equipment.DIP_STATION, Equipment.TRX, Equipment.RESISTANCE_BANDS,
    ),
    "Other": (
        Equipment.FOAM_ROLLER, Equipment.BODYWEIGHT_ONLY,
    ),
}


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
