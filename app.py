"""Over40Lift — Streamlit front end.

Deploy this the same way as any Streamlit Community Cloud app: push this
repo to GitHub, then on share.streamlit.io point the app at
`app.py`. No local Python install needed to test it — Streamlit
Cloud builds and runs it for you from requirements.txt.

Locally (optional): `streamlit run app.py`
"""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from over40lift.database import Database
from over40lift.exercise_library import EXERCISE_BY_KEY
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

st.set_page_config(page_title="Over40Lift", page_icon="🏋️", layout="centered")


@st.cache_resource
def get_db() -> Database:
    # Streamlit Cloud's filesystem is ephemeral across redeploys/reboots,
    # same as the trading dashboard — data persists while the app instance
    # is running but isn't a substitute for a real hosted DB long-term.
    return Database()


db = get_db()

st.title("🏋️ Over40Lift")
st.caption("Lifting recommendations that work around soreness, old injuries, your actual equipment, and how beat-up your nervous system feels today.")

# ---- user selection ----
with st.sidebar:
    st.header("Who's lifting?")
    existing_users = db.list_users()
    choice = st.selectbox(
        "Select existing user", options=["(new user)"] + existing_users
    )
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
    st.subheader("What do you have access to?")
    current_equipment = db.get_user_equipment(user_id)
    selected = st.multiselect(
        "Available equipment",
        options=[e.value for e in Equipment],
        default=sorted(current_equipment),
    )
    if st.button("Save equipment"):
        db.set_user_equipment(user_id, set(selected))
        st.success("Equipment saved.")
        st.rerun()

# ---- Soreness ----
with tab_soreness:
    st.subheader("Log a sore or injured area")
    col1, col2 = st.columns(2)
    with col1:
        muscle = st.selectbox("Muscle / joint", options=[m.value for m in MuscleGroup])
    with col2:
        level = st.selectbox("Severity", options=[s.value for s in SorenessLevel])
    notes = st.text_input("Notes (optional)", key="soreness_notes")
    if st.button("Log soreness"):
        db.add_soreness_report(
            user_id,
            SorenessReport(
                muscle_group=MuscleGroup(muscle),
                level=SorenessLevel(level),
                reported_at=datetime.now(),
                notes=notes,
            ),
        )
        st.success(f"Logged {muscle} as {level}.")
        st.rerun()

    st.divider()
    st.subheader("Currently flagged areas")
    current = db.get_current_soreness(user_id)
    if not current:
        st.caption("Nothing flagged right now.")
    for m, lvl in current.items():
        c1, c2 = st.columns([4, 1])
        c1.write(f"**{m.value}** — {lvl.value}")
        if c2.button("Clear", key=f"clear_{m.value}"):
            db.clear_soreness(user_id, m)
            st.rerun()

# ---- Goals ----
with tab_goals:
    st.subheader("Add a strength or competition goal")
    description = st.text_input("Goal description", placeholder="e.g. Bench 225x5 by meet day")
    tie_muscle = st.checkbox("Tie to a muscle group")
    target_muscle = st.selectbox("Muscle group", options=[m.value for m in MuscleGroup]) if tie_muscle else None
    tie_movement = st.checkbox("Tie to a movement pattern")
    target_movement = st.selectbox("Movement pattern", options=[m.value for m in MovementPattern]) if tie_movement else None
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
    exercise_key = st.selectbox(
        "Exercise",
        options=sorted(EXERCISE_BY_KEY.keys()),
        format_func=lambda k: EXERCISE_BY_KEY[k].name,
    )
    c1, c2, c3 = st.columns(3)
    sets = c1.number_input("Sets", min_value=1, max_value=10, value=3)
    reps = c2.number_input("Reps", min_value=1, max_value=30, value=8)
    weight = c3.number_input("Weight", min_value=0.0, value=0.0, step=5.0)
    rpe = st.slider("RPE (optional)", 0.0, 10.0, 0.0, step=0.5)
    log_notes = st.text_input("Notes (optional)", key="log_notes")
