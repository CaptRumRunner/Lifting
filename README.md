# Over40Lift

A workout/lifting recommendation engine built for lifters 40 and up — it
keeps you training around soreness and old injuries, works with whatever
equipment you actually have, tracks progress toward strength and competition
goals, and pulls back the intensity on days your nervous system is fried
instead of pushing you into a setback.

Recovery capacity changes with age, but most mainstream lifting apps still
program as if everyone's 22. Over40Lift leans the other way: soreness and
injury flags aren't an afterthought, readiness-driven light days are core to
the recommendation logic (not just a manual toggle), and variety tracking
keeps joints from getting hammered by the same movement pattern week after
week.

Built after looking at what current strength apps (Jefit, RP Hypertrophy,
JuggernautAI, Alpha Progression, Cora) do well in 2026 — autoregulation off of
RPE/soreness/readiness, deload logic driven by accumulated fatigue instead of
a fixed week count, equipment-aware plan generation, and history-aware
variety so you don't get the same session on repeat.

## Core features

- **Soreness / injury map** — flag any muscle group as sore (mild/moderate)
  or injured. Injured areas are hard-excluded from recommendations; sore
  areas are deprioritized and swapped for lower-irritation variants.
- **Equipment inventory** — toggle what you have access to (barbell,
  dumbbells, bands, battle ropes, etc.). Anything you don't have never gets
  recommended — e.g. no battle ropes checked in means battle rope work never
  shows up.
- **Goals** — log strength goals per muscle group or movement pattern
  (e.g. "bench 225x5", "improve back squat for meet on Nov 14"), with an
  optional target date. Recommendations lean toward exercises that serve
  active goals.
- **Workout history database** (SQLite) — every logged session is stored.
  The recommender penalizes exercises you've done recently so you get
  variety instead of the same five movements on repeat.
- **Readiness / CNS feedback** — log how you feel pre-workout (sleep,
  stress, overall soreness, motivation, optional RPE from yesterday). A low
  composite readiness score automatically triggers a lighter day: fewer
  sets, lower target RPE, and a bias toward lower-CNS-demand exercises
  (isolation work over max-effort compound lifts).

## Project layout

```
over40lift/
  over40lift/
    __init__.py
    models.py           # dataclasses & enums (MuscleGroup, Equipment, etc.)
    database.py          # SQLite schema + CRUD access layer
    exercise_library.py  # seed exercise data (movement, muscles, equipment, CNS demand)
    recommendation.py    # the recommendation engine
    cli.py                # interactive command-line app
  tests/
    test_database.py
    test_recommendation.py
  data/                  # over40lift.db lives here (gitignored)
  requirements.txt
  pyproject.toml
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m over40lift.cli
```

The CLI walks you through: create/select a user, set your equipment, log
soreness/injuries, set goals, log daily readiness feedback, and get a
recommended session. Everything persists to `data/over40lift.db`.

## Running tests

```bash
pip install -r requirements.txt
pytest
```

## How recommendations are built

1. **Filter** the exercise library down to movements whose required
   equipment you have, and whose target muscles don't include an area
   you've marked as *injured*.
2. **Penalize** exercises that hit muscles you've marked *sore* (they're not
   excluded outright, but rank lower and lower-irritation substitutes are
   preferred).
3. **Score for variety** using your workout history — anything logged in
   the last few sessions gets a recency penalty so the plan rotates.
4. **Boost** exercises that align with an active goal's target muscle group
   or movement pattern.
5. **Apply readiness** — your latest feedback produces a composite
   readiness/CNS score. Below the light-day threshold, the engine trims
   volume, drops target RPE, and shifts selection toward lower-CNS-demand
   accessory work instead of maximal compound lifts.

## Extending the exercise library

`over40lift/exercise_library.py` is a plain list of `Exercise` records — add
entries there and they're immediately available to the recommender, no
schema changes needed.
