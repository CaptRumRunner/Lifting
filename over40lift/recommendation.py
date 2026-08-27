"""The Over40Lift recommendation engine.

Pipeline, per session request:
  1. Filter out exercises requiring equipment the user doesn't have.
  2. Hard-exclude exercises that load an *injured* muscle group; try to
     swap in a listed low-irritation substitute instead.
  3. Score the remaining pool:
       - penalize muscles the user reported as *sore*
       - penalize exercises done recently (variety / anti-repetition)
       - boost exercises aligned with an active goal
       - if readiness is low, penalize high-CNS-demand exercises so the
         session naturally shifts toward lighter accessory work
  4. Pick the top-scoring exercise per requested movement slot, apply a
     light-day adjustment to prescribed sets/reps/RPE, and return a
     SessionPlan with the reasoning attached for transparency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from over40lift.exercise_library import EXERCISE_BY_KEY, get_exercise
from over40lift.models import (
    Exercise,
    Goal,
    MovementPattern,
    MuscleGroup,
    ReadinessFeedback,
    SorenessLevel,
    WorkoutLogEntry,
)

# Default template of movement slots for a balanced full-body session.
DEFAULT_SESSION_TEMPLATE: tuple[MovementPattern, ...] = (
    MovementPattern.SQUAT,
    MovementPattern.HINGE,
    MovementPattern.HORIZONTAL_PUSH,
    MovementPattern.HORIZONTAL_PULL,
    MovementPattern.VERTICAL_PUSH,
    MovementPattern.ISOLATION,
)

RECENCY_WINDOW_SESSIONS = 6  # how many past sessions count against variety
LIGHT_DAY_CNS_CEILING = 3  # on a light day, avoid exercises with cns_demand above this


@dataclass
class RecommendedExercise:
    exercise: Exercise
    sets: int
    reps: str  # "reps" not "int" since light-day/heavy-day reps ranges differ (e.g. "8-10")
    target_rpe: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class SessionPlan:
    is_light_day: bool
    cns_score: float | None
    exercises: list[RecommendedExercise]
    excluded_summary: list[str]  # human-readable notes on what got filtered and why


def _equipment_ok(exercise: Exercise, available_equipment: set[str]) -> bool:
    return all(eq.value in available_equipment for eq in exercise.equipment_required)


def _has_injury_conflict(exercise: Exercise, soreness: dict[MuscleGroup, SorenessLevel]) -> bool:
    for muscle in exercise.all_loaded_muscles():
        level = soreness.get(muscle)
        if level is not None and level.hard_exclude:
            return True
    return False


def _substitute_if_needed(
    exercise: Exercise,
    soreness: dict[MuscleGroup, SorenessLevel],
    available_equipment: set[str],
    depth: int = 0,
) -> tuple[Exercise | None, list[str]]:
    """Return a usable exercise (possibly a substitute), or None if nothing works.

    Follows the low_irritation_substitute chain up to 3 hops to avoid
    infinite loops if the seed data ever has a cycle.
    """
    notes: list[str] = []
    if not _has_injury_conflict(exercise, soreness) and _equipment_ok(exercise, available_equipment):
        return exercise, notes

    if _has_injury_conflict(exercise, soreness):
        notes.append(f"{exercise.name} excluded: conflicts with an injured area")
    elif not _equipment_ok(exercise, available_equipment):
        notes.append(f"{exercise.name} excluded: required equipment not available")

    if depth >= 3 or not exercise.low_irritation_substitute:
        return None, notes

    substitute = EXERCISE_BY_KEY.get(exercise.low_irritation_substitute)
    if substitute is None:
        return None, notes

    result, sub_notes = _substitute_if_needed(substitute, soreness, available_equipment, depth + 1)
    notes.extend(sub_notes)
    if result is not None:
        notes.append(f"Substituted {exercise.name} -> {result.name}")
    return result, notes


def _score_exercise(
    exercise: Exercise,
    soreness: dict[MuscleGroup, SorenessLevel],
    recent_keys_with_recency: dict[str, int],
    goals: list[Goal],
    light_day: bool,
) -> tuple[float, list[str]]:
    score = 10.0
    reasons: list[str] = []

    # Soreness (non-injury) deprioritization.
    for muscle in exercise.all_loaded_muscles():
        level = soreness.get(muscle)
        if level == SorenessLevel.MODERATE:
            score -= 4
            reasons.append(f"deprioritized: {muscle.value} reported moderately sore")
        elif level == SorenessLevel.MILD:
            score -= 1.5
            reasons.append(f"slightly deprioritized: {muscle.value} reported mildly sore")

    # Recency / variety penalty — more recent = bigger penalty.
    if exercise.key in recent_keys_with_recency:
        sessions_ago = recent_keys_with_recency[exercise.key]
        penalty = max(0, RECENCY_WINDOW_SESSIONS - sessions_ago) * 1.2
        score -= penalty
        reasons.append(f"done {sessions_ago} session(s) ago, penalized for variety")

    # Goal alignment boost.
    for goal in goals:
        if goal.target_muscle and goal.target_muscle in exercise.primary_muscles:
            score += 3
            reasons.append(f"boosted: supports goal '{goal.description}'")
        if goal.target_movement and goal.target_movement == exercise.movement_pattern:
            score += 3
            reasons.append(f"boosted: matches movement goal '{goal.description}'")

    # Light-day CNS demand penalty.
    if light_day and exercise.cns_demand > LIGHT_DAY_CNS_CEILING:
        score -= 6
        reasons.append("deprioritized: too CNS-taxing for a light/recovery day")

    return score, reasons


def _recent_keys_by_recency(recent_logs: list[WorkoutLogEntry]) -> dict[str, int]:
    """Map exercise_key -> how many distinct sessions ago it was last done (0 = today)."""
    session_dates_seen: list = []
    result: dict[str, int] = {}
    for entry in sorted(recent_logs, key=lambda e: e.performed_at, reverse=True):
        d = entry.performed_at.date()
        if d not in session_dates_seen:
            session_dates_seen.append(d)
        sessions_ago = session_dates_seen.index(d)
        if entry.exercise_key not in result:
            result[entry.exercise_key] = sessions_ago
    return result


def build_session_plan(
    available_equipment: set[str],
    soreness: dict[MuscleGroup, SorenessLevel],
    goals: list[Goal],
    recent_logs: list[WorkoutLogEntry],
    latest_feedback: ReadinessFeedback | None,
    template: tuple[MovementPattern, ...] = DEFAULT_SESSION_TEMPLATE,
    exercise_pool: list[Exercise] | None = None,
) -> SessionPlan:
    pool = exercise_pool if exercise_pool is not None else list(EXERCISE_BY_KEY.values())
    recent_keys = _recent_keys_by_recency(recent_logs)

    light_day = bool(latest_feedback and latest_feedback.is_light_day)
    cns_score = latest_feedback.cns_score if latest_feedback else None

    excluded_summary: list[str] = []
    used_keys: set[str] = set()
    recommendations: list[RecommendedExercise] = []

    for pattern in template:
        candidates = [ex for ex in pool if ex.movement_pattern == pattern]
        scored: list[tuple[float, Exercise, list[str]]] = []

        for candidate in candidates:
            resolved, sub_notes = _substitute_if_needed(candidate, soreness, available_equipment)
            excluded_summary.extend(sub_notes)
            if resolved is None or resolved.key in used_keys:
                continue
            score, reasons = _score_exercise(resolved, soreness, recent_keys, goals, light_day)
            scored.append((score, resolved, reasons))

        if not scored:
            excluded_summary.append(f"No available exercise found for movement pattern: {pattern.value}")
            continue

        scored.sort(key=lambda t: t[0], reverse=True)
        best_score, best_exercise, best_reasons = scored[0]
        used_keys.add(best_exercise.key)

        sets, reps, rpe = _prescribe(best_exercise, light_day)
        recommendations.append(
            RecommendedExercise(
                exercise=best_exercise,
                sets=sets,
                reps=reps,
                target_rpe=rpe,
                reasons=best_reasons or ["baseline pick for this movement pattern"],
            )
        )

    return SessionPlan(
        is_light_day=light_day,
        cns_score=cns_score,
        exercises=recommendations,
        excluded_summary=excluded_summary,
    )


def _prescribe(exercise: Exercise, light_day: bool) -> tuple[int, str, float]:
    """Basic sets/reps/RPE prescription, trimmed on a light day."""
    if light_day:
        if exercise.cns_demand >= 3:
            return 2, "10-12", 6.0
        return 3, "12-15", 6.5
    # Normal day: heavier compound work gets lower reps / higher intended RPE.
    if exercise.cns_demand >= 4:
        return 4, "4-6", 8.0
    if exercise.cns_demand == 3:
        return 3, "6-10", 7.5
    return 3, "10-15", 7.0
