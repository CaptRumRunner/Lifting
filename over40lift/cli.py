"""Interactive command-line front end for Over40Lift."""

from __future__ import annotations

from datetime import date, datetime

from over40lift.database import Database
from over40lift.exercise_library import EXERCISE_BY_KEY, get_exercise
from over40lift.models import (
    Equipment,
    Goal,
    MovementPattern,
    MuscleGroup,
    ReadinessFeedback,
    SorenessLevel,
    SorenessReport,
    WorkoutLogEntry,
)
from over40lift.recommendation import build_session_plan


def _choose_enum(prompt: str, enum_cls) -> object:
    options = list(enum_cls)
    print(prompt)
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option.value}")
    while True:
        raw = input("> ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("Invalid choice, try again.")


def _choose_int(prompt: str, low: int, high: int) -> int:
    while True:
        raw = input(f"{prompt} [{low}-{high}]: ").strip()
        if raw.isdigit() and low <= int(raw) <= high:
            return int(raw)
        print("Invalid choice, try again.")


def cmd_setup_equipment(db: Database, user_id: int) -> None:
    current = db.get_user_equipment(user_id)
    print("\nToggle your available equipment. Currently available:")
    print(", ".join(sorted(current)) or "(none set)")
    print("\nEnter equipment keys you HAVE, comma-separated, from this list:")
    print(", ".join(e.value for e in Equipment))
    raw = input("> ").strip()
    keys = {k.strip() for k in raw.split(",") if k.strip()}
    valid_keys = {e.value for e in Equipment}
    invalid = keys - valid_keys
    if invalid:
        print(f"Ignoring unknown equipment: {invalid}")
    db.set_user_equipment(user_id, keys & valid_keys)
    print("Equipment saved.")


def cmd_log_soreness(db: Database, user_id: int) -> None:
    muscle = _choose_enum("\nWhich muscle/joint area?", MuscleGroup)
    level = _choose_enum("How bad?", SorenessLevel)
    notes = input("Notes (optional): ").strip()
    report = SorenessReport(
        muscle_group=muscle, level=level, reported_at=datetime.now(), notes=notes
    )
    db.add_soreness_report(user_id, report)
    print(f"Logged: {muscle.value} -> {level.value}")


def cmd_clear_soreness(db: Database, user_id: int) -> None:
    current = db.get_current_soreness(user_id)
    if not current:
        print("Nothing currently flagged as sore/injured.")
        return
    print("\nCurrently flagged areas:")
    items = list(current.items())
    for i, (muscle, level) in enumerate(items, 1):
        print(f"  {i}. {muscle.value} ({level.value})")
    raw = input("Enter number to clear (or blank to cancel): ").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(items):
        muscle, _ = items[int(raw) - 1]
        db.clear_soreness(user_id, muscle)
        print(f"Cleared {muscle.value}.")


def cmd_add_goal(db: Database, user_id: int) -> None:
    description = input("\nDescribe the goal (e.g. 'Bench 225x5 by meet day'): ").strip()
    tie_to_muscle = input("Tie to a specific muscle group? (y/n): ").strip().lower() == "y"
    target_muscle = _choose_enum("Muscle group:", MuscleGroup) if tie_to_muscle else None
    tie_to_movement = input("Tie to a specific movement pattern? (y/n): ").strip().lower() == "y"
    target_movement = _choose_enum("Movement pattern:", MovementPattern) if tie_to_movement else None
    date_str = input("Target date YYYY-MM-DD (optional): ").strip()
    target_date = date.fromisoformat(date_str) if date_str else None
    goal = Goal(
        description=description,
        target_muscle=target_muscle,
        target_movement=target_movement,
        target_date=target_date,
        created_at=datetime.now(),
    )
    db.add_goal(user_id, goal)
    print("Goal saved.")


def cmd_log_feedback(db: Database, user_id: int) -> None:
    print("\nHow are you feeling today? (1 = worst, 5 = best, except stress/soreness where 5 = worst)")
    sleep_quality = _choose_int("Sleep quality", 1, 5)
    stress_level = _choose_int("Stress level (5 = very stressed)", 1, 5)
    overall_soreness = _choose_int("Overall body soreness (5 = very sore)", 1, 5)
    motivation = _choose_int("Motivation to train", 1, 5)
    notes = input("Notes (optional): ").strip()
    feedback = ReadinessFeedback(
        logged_at=datetime.now(),
        sleep_quality=sleep_quality,
        stress_level=stress_level,
        overall_soreness=overall_soreness,
        motivation=motivation,
        notes=notes,
    )
    db.add_feedback(user_id, feedback)
    print(f"Readiness (CNS) score: {feedback.cns_score}/5")
    if feedback.is_light_day:
        print("-> Recommending a lighter day today.")


def cmd_recommend(db: Database, user_id: int) -> None:
    equipment = db.get_user_equipment(user_id)
    if not equipment:
        print("No equipment set yet — recommending bodyweight-only work. "
              "Run 'equipment' to set this up properly.")
    soreness = db.get_current_soreness(user_id)
    goals = db.get_active_goals(user_id)
    recent_logs = db.get_recent_workouts(user_id)
    feedback = db.get_latest_feedback(user_id)

    plan = build_session_plan(
        available_equipment=equipment,
        soreness=soreness,
        goals=goals,
        recent_logs=recent_logs,
        latest_feedback=feedback,
    )

    print("\n=== Recommended Session ===")
    if plan.cns_score is not None:
        print(f"Readiness score: {plan.cns_score}/5" + (" (LIGHT DAY)" if plan.is_light_day else ""))
    else:
        print("No readiness feedback logged yet — assuming a normal day.")

    if not plan.exercises:
        print("No exercises could be recommended — check equipment and soreness settings.")
    for rec in plan.exercises:
        print(f"\n- {rec.exercise.name}: {rec.sets} sets x {rec.reps} reps @ RPE {rec.target_rpe}")
        for reason in rec.reasons:
            print(f"    * {reason}")

    if plan.excluded_summary:
        print("\n(notes)")
        for note in plan.excluded_summary:
            print(f"  - {note}")


def cmd_log_workout(db: Database, user_id: int) -> None:
    print("\nExercise keys:", ", ".join(sorted(EXERCISE_BY_KEY)))
    key = input("Exercise key: ").strip()
    if key not in EXERCISE_BY_KEY:
        print("Unknown exercise key.")
        return
    sets = _choose_int("Sets", 1, 10)
    reps = _choose_int("Reps", 1, 30)
    weight = float(input("Weight (0 for bodyweight): ").strip() or 0)
    rpe_raw = input("RPE (optional, 1-10): ").strip()
    rpe = float(rpe_raw) if rpe_raw else None
    notes = input("Notes (optional): ").strip()
    entry = WorkoutLogEntry(
        exercise_key=key, performed_at=datetime.now(), sets=sets, reps=reps,
        weight=weight, rpe=rpe, notes=notes,
    )
    db.log_workout(user_id, entry)
    print(f"Logged {get_exercise(key).name}.")


MENU = """
Over40Lift
  1. equipment      - set what gym equipment you have
  2. soreness        - log a sore or injured area
  3. clear-soreness  - clear a previously flagged area
  4. goal            - add a strength/competition goal
  5. feedback        - log today's readiness (sleep/stress/soreness/motivation)
  6. recommend        - get today's recommended session
  7. log              - log a completed exercise
  8. quit
"""


def main() -> None:
    print("Welcome to Over40Lift.")
    existing = None
    with Database() as db:
        users = db.list_users()
        if users:
            print("Existing users:", ", ".join(users))
        name = input("Enter your name: ").strip() or "default_user"
        user_id = db.get_or_create_user(name)

        actions = {
            "1": cmd_setup_equipment,
            "equipment": cmd_setup_equipment,
            "2": cmd_log_soreness,
            "soreness": cmd_log_soreness,
            "3": cmd_clear_soreness,
            "clear-soreness": cmd_clear_soreness,
            "4": cmd_add_goal,
            "goal": cmd_add_goal,
            "5": cmd_log_feedback,
            "feedback": cmd_log_feedback,
            "6": cmd_recommend,
            "recommend": cmd_recommend,
            "7": cmd_log_workout,
            "log": cmd_log_workout,
        }

        while True:
            print(MENU)
            choice = input("> ").strip().lower()
            if choice in ("8", "quit", "q", "exit"):
                print("See you at the gym.")
                break
            action = actions.get(choice)
            if action is None:
                print("Unrecognized option.")
                continue
            action(db, user_id)


if __name__ == "__main__":
    main()
