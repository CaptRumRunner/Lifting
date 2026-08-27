"""Seed exercise library.

A plain list of Exercise records. Add to this list to extend what the
recommender can choose from — no schema/migration needed.
"""

from __future__ import annotations

from over40lift.models import Equipment as Eq
from over40lift.models import Exercise
from over40lift.models import MovementPattern as Mv
from over40lift.models import MuscleGroup as M

EXERCISES: list[Exercise] = [
    # ---- Squat pattern ----
    Exercise(
        "barbell_back_squat", "Barbell Back Squat",
        (M.QUADS, M.GLUTES), (M.HAMSTRINGS, M.CORE),
        (Eq.BARBELL, Eq.SQUAT_RACK), Mv.SQUAT, cns_demand=5,
        aggravates=(M.LOWER_BACK, M.KNEES),
        low_irritation_substitute="goblet_squat",
    ),
    Exercise(
        "front_squat", "Barbell Front Squat",
        (M.QUADS, M.GLUTES), (M.CORE,),
        (Eq.BARBELL, Eq.SQUAT_RACK), Mv.SQUAT, cns_demand=5,
        aggravates=(M.KNEES, M.WRISTS),
        low_irritation_substitute="goblet_squat",
    ),
    Exercise(
        "goblet_squat", "Goblet Squat",
        (M.QUADS, M.GLUTES), (M.CORE,),
        (Eq.DUMBBELLS,), Mv.SQUAT, cns_demand=2,
        aggravates=(M.KNEES,),
    ),
    Exercise(
        "leg_press", "Leg Press",
        (M.QUADS, M.GLUTES), (M.HAMSTRINGS,),
        (Eq.LEG_PRESS,), Mv.SQUAT, cns_demand=3,
        aggravates=(M.KNEES,),
        low_irritation_substitute="goblet_squat",
    ),
    Exercise(
        "bodyweight_squat", "Bodyweight Squat",
        (M.QUADS, M.GLUTES), (M.CORE,),
        (Eq.BODYWEIGHT_ONLY,), Mv.SQUAT, cns_demand=1,
        aggravates=(M.KNEES,),
    ),

    # ---- Hinge pattern ----
    Exercise(
        "conventional_deadlift", "Conventional Deadlift",
        (M.HAMSTRINGS, M.GLUTES, M.LOWER_BACK), (M.UPPER_BACK, M.FOREARMS),
        (Eq.BARBELL,), Mv.HINGE, cns_demand=5,
        aggravates=(M.LOWER_BACK,),
        low_irritation_substitute="kettlebell_deadlift",
    ),
    Exercise(
        "romanian_deadlift", "Romanian Deadlift",
        (M.HAMSTRINGS, M.GLUTES), (M.LOWER_BACK,),
        (Eq.BARBELL,), Mv.HINGE, cns_demand=4,
        aggravates=(M.LOWER_BACK,),
        low_irritation_substitute="kettlebell_deadlift",
    ),
    Exercise(
        "kettlebell_deadlift", "Kettlebell Deadlift",
        (M.HAMSTRINGS, M.GLUTES), (M.LOWER_BACK,),
        (Eq.KETTLEBELL,), Mv.HINGE, cns_demand=2,
    ),
    Exercise(
        "glute_bridge", "Glute Bridge",
        (M.GLUTES,), (M.HAMSTRINGS, M.CORE),
        (Eq.BODYWEIGHT_ONLY,), Mv.HINGE, cns_demand=1,
    ),
    Exercise(
        "kettlebell_swing", "Kettlebell Swing",
        (M.GLUTES, M.HAMSTRINGS), (M.CORE, M.LOWER_BACK),
        (Eq.KETTLEBELL,), Mv.HINGE, cns_demand=3,
        aggravates=(M.LOWER_BACK,),
    ),

    # ---- Lunge pattern ----
    Exercise(
        "walking_lunge", "Walking Lunge",
        (M.QUADS, M.GLUTES), (M.HAMSTRINGS, M.CORE),
        (Eq.DUMBBELLS,), Mv.LUNGE, cns_demand=3,
        aggravates=(M.KNEES,),
    ),
    Exercise(
        "bulgarian_split_squat", "Bulgarian Split Squat",
        (M.QUADS, M.GLUTES), (M.HAMSTRINGS,),
        (Eq.DUMBBELLS, Eq.BENCH), Mv.LUNGE, cns_demand=3,
        aggravates=(M.KNEES,),
        low_irritation_substitute="glute_bridge",
    ),
    Exercise(
        "step_up", "Dumbbell Step-Up",
        (M.QUADS, M.GLUTES), (M.HAMSTRINGS,),
        (Eq.DUMBBELLS, Eq.BENCH), Mv.LUNGE, cns_demand=2,
        aggravates=(M.KNEES,),
    ),

    # ---- Horizontal push ----
    Exercise(
        "barbell_bench_press", "Barbell Bench Press",
        (M.CHEST,), (M.TRICEPS, M.SHOULDERS),
        (Eq.BARBELL, Eq.BENCH), Mv.HORIZONTAL_PUSH, cns_demand=4,
        aggravates=(M.SHOULDERS, M.ELBOWS),
        low_irritation_substitute="pushup",
    ),
    Exercise(
        "dumbbell_bench_press", "Dumbbell Bench Press",
        (M.CHEST,), (M.TRICEPS, M.SHOULDERS),
        (Eq.DUMBBELLS, Eq.BENCH), Mv.HORIZONTAL_PUSH, cns_demand=3,
        aggravates=(M.SHOULDERS,),
        low_irritation_substitute="pushup",
    ),
    Exercise(
        "pushup", "Push-Up",
        (M.CHEST,), (M.TRICEPS, M.SHOULDERS, M.CORE),
        (Eq.BODYWEIGHT_ONLY,), Mv.HORIZONTAL_PUSH, cns_demand=1,
        aggravates=(M.WRISTS,),
    ),
    Exercise(
        "cable_chest_fly", "Cable Chest Fly",
        (M.CHEST,), (M.SHOULDERS,),
        (Eq.CABLE_MACHINE,), Mv.ISOLATION, cns_demand=1,
        aggravates=(M.SHOULDERS,),
    ),

    # ---- Horizontal pull ----
    Exercise(
        "barbell_row", "Barbell Bent-Over Row",
        (M.UPPER_BACK, M.LATS), (M.BICEPS, M.LOWER_BACK),
        (Eq.BARBELL,), Mv.HORIZONTAL_PULL, cns_demand=4,
        aggravates=(M.LOWER_BACK,),
        low_irritation_substitute="cable_seated_row",
    ),
    Exercise(
        "dumbbell_row", "Single-Arm Dumbbell Row",
        (M.UPPER_BACK, M.LATS), (M.BICEPS,),
        (Eq.DUMBBELLS, Eq.BENCH), Mv.HORIZONTAL_PULL, cns_demand=2,
    ),
    Exercise(
        "cable_seated_row", "Seated Cable Row",
        (M.UPPER_BACK, M.LATS), (M.BICEPS,),
        (Eq.CABLE_MACHINE,), Mv.HORIZONTAL_PULL, cns_demand=2,
    ),
    Exercise(
        "trx_row", "TRX Inverted Row",
        (M.UPPER_BACK, M.LATS), (M.BICEPS, M.CORE),
        (Eq.TRX,), Mv.HORIZONTAL_PULL, cns_demand=2,
    ),

    # ---- Vertical push ----
    Exercise(
        "overhead_press", "Barbell Overhead Press",
        (M.SHOULDERS,), (M.TRICEPS, M.CORE),
        (Eq.BARBELL,), Mv.VERTICAL_PUSH, cns_demand=4,
        aggravates=(M.SHOULDERS, M.LOWER_BACK),
        low_irritation_substitute="dumbbell_shoulder_press",
    ),
    Exercise(
        "dumbbell_shoulder_press", "Dumbbell Shoulder Press",
        (M.SHOULDERS,), (M.TRICEPS,),
        (Eq.DUMBBELLS,), Mv.VERTICAL_PUSH, cns_demand=3,
        aggravates=(M.SHOULDERS,),
    ),
    Exercise(
        "pike_pushup", "Pike Push-Up",
        (M.SHOULDERS,), (M.TRICEPS, M.CORE),
        (Eq.BODYWEIGHT_ONLY,), Mv.VERTICAL_PUSH, cns_demand=2,
        aggravates=(M.WRISTS,),
    ),

    # ---- Vertical pull ----
    Exercise(
        "pull_up", "Pull-Up",
        (M.LATS,), (M.BICEPS, M.UPPER_BACK),
        (Eq.PULL_UP_BAR,), Mv.VERTICAL_PULL, cns_demand=4,
        aggravates=(M.ELBOWS,),
        low_irritation_substitute="lat_pulldown",
    ),
    Exercise(
        "lat_pulldown", "Cable Lat Pulldown",
        (M.LATS,), (M.BICEPS, M.UPPER_BACK),
        (Eq.CABLE_MACHINE,), Mv.VERTICAL_PULL, cns_demand=2,
    ),
    Exercise(
        "band_pulldown", "Band Lat Pulldown",
        (M.LATS,), (M.BICEPS,),
        (Eq.RESISTANCE_BANDS,), Mv.VERTICAL_PULL, cns_demand=1,
    ),

    # ---- Isolation / accessory ----
    Exercise(
        "dumbbell_biceps_curl", "Dumbbell Biceps Curl",
        (M.BICEPS,), (M.FOREARMS,),
        (Eq.DUMBBELLS,), Mv.ISOLATION, cns_demand=1,
        aggravates=(M.ELBOWS,),
    ),
    Exercise(
        "triceps_pushdown", "Cable Triceps Pushdown",
        (M.TRICEPS,), (),
        (Eq.CABLE_MACHINE,), Mv.ISOLATION, cns_demand=1,
        aggravates=(M.ELBOWS,),
    ),
    Exercise(
        "lateral_raise", "Dumbbell Lateral Raise",
        (M.SHOULDERS,), (),
        (Eq.DUMBBELLS,), Mv.ISOLATION, cns_demand=1,
        aggravates=(M.SHOULDERS,),
    ),
    Exercise(
        "hanging_leg_raise", "Hanging Leg Raise",
        (M.CORE,), (M.HIPS,),
        (Eq.PULL_UP_BAR,), Mv.ISOLATION, cns_demand=2,
        aggravates=(M.LOWER_BACK,),
        low_irritation_substitute="plank",
    ),
    Exercise(
        "plank", "Plank",
        (M.CORE,), (),
        (Eq.BODYWEIGHT_ONLY,), Mv.ISOLATION, cns_demand=1,
    ),
    Exercise(
        "calf_raise", "Standing Calf Raise",
        (M.CALVES,), (),
        (Eq.DUMBBELLS,), Mv.ISOLATION, cns_demand=1,
        aggravates=(M.ANKLES,),
    ),
    Exercise(
        "band_face_pull", "Band Face Pull",
        (M.UPPER_BACK, M.SHOULDERS), (),
        (Eq.RESISTANCE_BANDS,), Mv.ISOLATION, cns_demand=1,
    ),

    # ---- Carry / core ----
    Exercise(
        "farmers_carry", "Farmer's Carry",
        (M.FOREARMS, M.CORE), (M.UPPER_BACK, M.HIPS),
        (Eq.DUMBBELLS,), Mv.CARRY, cns_demand=2,
        aggravates=(M.LOWER_BACK,),
    ),
    Exercise(
        "medicine_ball_rotational_throw", "Medicine Ball Rotational Throw",
        (M.CORE,), (M.SHOULDERS, M.HIPS),
        (Eq.MEDICINE_BALL,), Mv.ROTATION, cns_demand=3,
        aggravates=(M.LOWER_BACK,),
    ),

    # ---- Conditioning ----
    Exercise(
        "battle_ropes", "Battle Ropes",
        (M.SHOULDERS, M.CORE), (M.FOREARMS,),
        (Eq.BATTLE_ROPES,), Mv.CONDITIONING, cns_demand=3,
        aggravates=(M.SHOULDERS, M.ELBOWS),
    ),
    Exercise(
        "assault_bike_intervals", "Assault Bike Intervals",
        (M.QUADS, M.HAMSTRINGS), (M.SHOULDERS, M.CORE),
        (Eq.ASSAULT_BIKE,), Mv.CONDITIONING, cns_demand=3,
        aggravates=(M.KNEES,),
    ),
    Exercise(
        "rowing_machine_intervals", "Rowing Machine Intervals",
        (M.UPPER_BACK, M.QUADS), (M.HAMSTRINGS, M.LATS),
        (Eq.ROWING_MACHINE,), Mv.CONDITIONING, cns_demand=3,
        aggravates=(M.LOWER_BACK,),
    ),
]

EXERCISE_BY_KEY: dict[str, Exercise] = {ex.key: ex for ex in EXERCISES}


def get_exercise(key: str) -> Exercise:
    return EXERCISE_BY_KEY[key]
