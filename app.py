"""Over40Lift — Streamlit front end.

Deploy this the same way as any Streamlit Community Cloud app: push this
repo to GitHub, then on share.streamlit.io point the app at
`app.py`. No local Python install needed to test it — Streamlit
Cloud builds and runs it for you from requirements.txt.

Locally (optional): `streamlit run app.py`

UI notes: every selector in this app is a tappable tile or a horizontal
radio row — there are no dropdown/select boxes anywhere. Equipment tiles
cycle neutral -> have it (green) -> don't have it (red) -> neutral.
Soreness/injury tiles on the body diagram cycle
neutral -> mild (yellow) -> moderate (orange) -> injury (red) -> neutral.
"""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from over40lift.database import Database
from over40lift.exercise_library import EXERCISE_BY_KEY
from over40lift.models import (
    BODY_VIEW_BACK,
    BODY_VIEW_FRONT,
    EQUIPMENT_CATEGORIES,
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

st.set_page_config(page_title="Over40Lift", page_icon="🏋️", layout="centered")

# ---------------------------------------------------------------------
# Tap-to-cycle tile helpers
# ---------------------------------------------------------------------

EQUIP_CYCLE = ["neutral", "green", "red"]
EQUIP_COLORS = {
    "neutral": ("#F0F2F6", "#31333F", "#D3D3D3"),
    "green": ("#2f9e44", "#FFFFFF", "#1f7a34"),
    "red": ("#e03131", "#FFFFFF", "#b02525"),
}
EQUIP_ICON = {"neutral": "⚪", "green": "🟢", "red": "🔴"}

SORENESS_CYCLE = ["neutral", "mild", "moderate", "injury"]
SORENESS_COLORS = {
    "neutral": ("#F0F2F6", "#31333F", "#D3D3D3"),
    "mild": ("#f5c518", "#3d3300", "#c9a30f"),
    "moderate": ("#ff8c00", "#FFFFFF", "#cc7000"),
    "injury": ("#e03131", "#FFFFFF", "#b02525"),
}
SORENESS_ICON = {"neutral": "⚪", "mild": "🟡", "moderate": "🟠", "injury": "🔴"}
SORENESS_LABEL = {"neutral": "OK", "mild": "Mild", "moderate": "Moderate", "injury": "Injury"}


def next_state(current: str, cycle: list[str]) -> str:
    idx = cycle.index(current)
    return cycle[(idx + 1) % len(cycle)]


def inject_tile_css(states: dict[str, str], colors: dict) -> None:
    """states: {css_key: state_name}. Colors keyed by state_name."""
    rules = []
    for css_key, state in states.items():
        bg, fg, border = colors[state]
        rules.append(
            f".st-key-{css_key} button {{"
            f"background-color: {bg} !important;"
            f"color: {fg} !important;"
            f"border-color: {border} !important;"
            f"}}"
        )
    st.markdown(f"<style>{''.join(rules)}</style>", unsafe_allow_html=True)


@st.cache_resource
def get_db() -> Database:
    # Streamlit Cloud's filesystem is ephemeral across redeploys/reboots,
    # same as the trading dashboard — data persists while the app instance
    # is running but isn't a substitute for a real hosted DB long-term.
    return Database()


db = get_db()

st.title("🏋️ Over40Lift")
st.caption("Lifting recommendations that work around soreness, old injuries, your actual equipment, and how beat-up your nervous system feels today.")

# ---- user selection (radio, not a dropdown) ----
with st.sidebar:
    st.header("Who's lifting?")
    existing_users = db.list_users()
    options = ["(new user)"] + existing_users
    choice = st.radio("Select user", options=options, key="user_choice")
    if choice == "(new user)":
        name = st.text_input("Enter a name", value="")
    else:
        name = choice

    if not name:
        st.info("Enter or select a name to continue.")
        st.stop()

    user_id = db.get_or_create_user(name)
    st.success(f"Signed in as **{name}**")

tab_recommend, tab_equipment, tab_soreness, tab_goals, tab_feedback, tab_log = st.tabs(
    ["Recommend", "Equipment", "Soreness", "Goals", "Readiness", "Log Workout"]
)

# ---- Recommend ----
with tab_recommend:
    st.subheader("Today's recommended session")
    equipment = db.get_user_equipment(user_id)
    soreness = db.get_current_soreness(user_id)
    goals = db.get_active_goals(user_id)
    recent_logs = db.get_recent_workouts(user_id)
    feedback = db.get_latest_feedback(user_id)

    if not equipment:
        st.warning("No equipment set yet — set it in the Equipment tab for a real recommendation. Defaulting to bodyweight-only for now.")
        equipment = {Equipment.BODYWEIGHT_ONLY.value}

    plan = build_session_plan(
        available_equipment=equipment,
        soreness=soreness,
        goals=goals,
        recent_logs=recent_logs,
        latest_feedback=feedback,
    )

    if feedback is None:
        st.caption("No readiness check-in yet today — log one in the Readiness tab for light-day logic to kick in.")
    else:
        if plan.is_light_day:
            st.error(f"Readiness score: {plan.cns_score}/5 — **Light day.** Volume and RPE are trimmed below.")
        else:
            st.info(f"Readiness score: {plan.cns_score}/5 — normal training day.")

    if not plan.exercises:
        st.warning("No exercises could be recommended. Check your equipment and soreness settings.")

    for rec in plan.exercises:
        with st.container(border=True):
            st.markdown(f"**{rec.exercise.name}** — {rec.sets} sets × {rec.reps} reps @ RPE {rec.target_rpe}")
            for reason in rec.reasons:
                st.caption(f"• {reason}")

    if plan.excluded_summary:
        with st.expander("Why some exercises were swapped or skipped"):
            for note in plan.excluded_summary:
                st.write(f"- {note}")

# ---- Equipment ----
with tab_equipment:
    st.subheader("What does your gym have?")
    st.caption("Tap once for **have it** (green), tap again for **don't have it** (red), tap again to reset.")

    state_key = f"equip_state_owner_{user_id}"
    if st.session_state.get(state_key) is None:
        current_have = db.get_user_equipment(user_id)
        st.session_state[state_key] = {
            item.value: ("green" if item.value in current_have else "neutral")
            for item in Equipment
        }

    equip_states: dict[str, str] = st.session_state[state_key]
    css_states: dict[str, str] = {}

    for category, items in EQUIPMENT_CATEGORIES.items():
        st.markdown(f"**{category}**")
        cols = st.columns(3)
        for i, item in enumerate(items):
            css_key = f"eq_{user_id}_{item.value}"
            state = equip_states.get(item.value, "neutral")
            css_states[css_key] = state
            label = f"{EQUIP_ICON[state]} {item.value.replace('_', ' ').title()}"
            with cols[i % 3]:
                if st.button(label, key=css_key, use_container_width=True):
                    equip_states[item.value] = next_state(state, EQUIP_CYCLE)
                    have_set = {k for k, v in equip_states.items() if v == "green"}
                    db.set_user_equipment(user_id, have_set)
                    st.rerun()

    inject_tile_css(css_states, EQUIP_COLORS)

# ---- Soreness ----
with tab_soreness:
    st.subheader("Sore or injured areas")
    st.caption("Tap a spot to cycle: OK → Mild → Moderate → Injury → OK. Injuries are excluded from recommendations; mild/moderate areas are just deprioritized.")

    view = st.radio("View", options=["Front", "Back"], horizontal=True, key="soreness_view")
    view_muscles = BODY_VIEW_FRONT if view == "Front" else BODY_VIEW_BACK

    sore_key = f"soreness_state_owner_{user_id}"
    if st.session_state.get(sore_key) is None:
        current = db.get_current_soreness(user_id)
        st.session_state[sore_key] = {
            m.value: current[m].value if m in current else "neutral"
            for m in MuscleGroup
        }

    sore_states: dict[str, str] = st.session_state[sore_key]
    sore_css_states: dict[str, str] = {}

    cols = st.columns(3)
    for i, muscle in enumerate(view_muscles):
        css_key = f"sore_{user_id}_{muscle.value}"
        state = sore_states.get(muscle.value, "neutral")
        sore_css_states[css_key] = state
        label = f"{SORENESS_ICON[state]} {muscle.value.replace('_', ' ').title()} ({SORENESS_LABEL[state]})"
        with cols[i % 3]:
            if st.button(label, key=css_key, use_container_width=True):
                new_state = next_state(state, SORENESS_CYCLE)
                sore_states[muscle.value] = new_state
                if new_state == "neutral":
                    db.clear_soreness(user_id, muscle)
                else:
                    db.add_soreness_report(
                        user_id,
                        SorenessReport(
                            muscle_group=muscle,
                            level=SorenessLevel(new_state),
                            reported_at=datetime.now(),
                        ),
                    )
                st.rerun()

    # Also render CSS classes for muscles in the *other* view so their
    # colors stay correct/consistent once the user switches views.
    other_muscles = BODY_VIEW_BACK if view == "Front" else BODY_VIEW_FRONT
    for muscle in other_muscles:
        css_key = f"sore_{user_id}_{muscle.value}"
        sore_css_states[css_key] = sore_states.get(muscle.value, "neutral")

    inject_tile_css(sore_css_states, SORENESS_COLORS)

    st.divider()
    st.caption("⚪ OK &nbsp;&nbsp; 🟡 Mild &nbsp;&nbsp; 🟠 Moderate &nbsp;&nbsp; 🔴 Injury", unsafe_allow_html=True)

# ---- Goals ----
with tab_goals:
    st.subheader("Add a strength or competition goal")
    description = st.text_input("Goal description", placeholder="e.g. Bench 225x5 by meet day")

    tie_muscle = st.checkbox("Tie to a muscle group")
    target_muscle = None
    if tie_muscle:
        target_muscle = st.radio(
            "Muscle group", options=[m.value for m in MuscleGroup], horizontal=True, key="goal_muscle"
        )

    tie_movement = st.checkbox("Tie to a movement pattern")
    target_movement = None
    if tie_movement:
        target_movement = st.radio(
            "Movement pattern", options=[m.value for m in MovementPattern], horizontal=True, key="goal_movement"
        )

    target_date = st.date_input("Target date (optional)", value=None)

    if st.button("Save goal"):
        if not description:
            st.error("Enter a description first.")
        else:
            db.add_goal(
                user_id,
                Goal(
                    description=description,
                    target_muscle=MuscleGroup(target_muscle) if target_muscle else None,
                    target_movement=MovementPattern(target_movement) if target_movement else None,
                    target_date=target_date if isinstance(target_date, date) else None,
                    created_at=datetime.now(),
                ),
            )
            st.success("Goal saved.")
            st.rerun()

    st.divider()
    st.subheader("Active goals")
    active_goals = db.get_active_goals(user_id)
    if not active_goals:
        st.caption("No active goals yet.")
    for g in active_goals:
        st.write(f"- {g.description}" + (f" (target: {g.target_date})" if g.target_date else ""))

# ---- Readiness ----
with tab_feedback:
    st.subheader("How are you feeling today?")
    st.caption("1 = worst, 5 = best — except stress and soreness, where 5 = worst.")
    sleep_quality = st.slider("Sleep quality", 1, 5, 3)
    stress_level = st.slider("Stress level (5 = very stressed)", 1, 5, 3)
    overall_soreness = st.slider("Overall body soreness (5 = very sore)", 1, 5, 3)
    motivation = st.slider("Motivation to train", 1, 5, 3)
    fb_notes = st.text_input("Notes (optional)", key="feedback_notes")

    if st.button("Log readiness"):
        fb = ReadinessFeedback(
            logged_at=datetime.now(),
            sleep_quality=sleep_quality,
            stress_level=stress_level,
            overall_soreness=overall_soreness,
            motivation=motivation,
            notes=fb_notes,
        )
        db.add_feedback(user_id, fb)
        st.success(f"Readiness score: {fb.cns_score}/5" + (" — light day recommended." if fb.is_light_day else ""))
        st.rerun()

# ---- Log workout ----
with tab_log:
    st.subheader("Log a completed exercise")
    exercise_names = sorted(EXERCISE_BY_KEY.values(), key=lambda e: e.name)
    name_to_key = {e.name: e.key for e in exercise_names}
    chosen_name = st.radio("Exercise", options=list(name_to_key.keys()), key="log_exercise_choice")
    exercise_key = name_to_key[chosen_name]

    c1, c2, c3 = st.columns(3)
    sets = c1.number_input("Sets", min_value=1, max_value=10, value=3)
    reps = c2.number_input("Reps", min_value=1, max_value=30, value=8)
    weight = c3.number_input("Weight", min_value=0.0, value=0.0, step=5.0)
    rpe = st.slider("RPE (optional)", 0.0, 10.0, 0.0, step=0.5)
    log_notes = st.text_input("Notes (optional)", key="log_notes")

    if st.button("Log workout"):
        db.log_workout(
            user_id,
            WorkoutLogEntry(
                exercise_key=exercise_key,
                performed_at=datetime.now(),
                sets=int(sets),
                reps=int(reps),
                weight=float(weight),
                rpe=rpe if rpe > 0 else None,
                notes=log_notes,
            ),
        )
        st.success(f"Logged {EXERCISE_BY_KEY[exercise_key].name}.")
        st.rerun()

    st.divider()
    st.subheader("Recent sessions")
    recent = db.get_recent_workouts(user_id)
    if not recent:
        st.caption("No workouts logged yet.")
    for entry in recent:
        ex = EXERCISE_BY_KEY.get(entry.exercise_key)
        label = ex.name if ex else entry.exercise_key
        st.write(
            f"- {entry.performed_at.strftime('%Y-%m-%d')} — {label}: "
            f"{entry.sets}×{entry.reps}" + (f" @ {entry.weight}lb" if entry.weight else "")
        )
