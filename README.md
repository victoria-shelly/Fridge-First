# Fridge-First

**HackUTA 2026 · Odyssey** — watch over food provisions on the journey home.

A small Flask web app that tracks what’s in your fridge (the galley locker), colors each item by how soon it spoils, and ranks recipes so you cook the most urgent food first. Same fridge + same voyage day → same answer every time.

> Fridge-First is the ship’s steward for your fridge: it colors what expires soonest and tells you what to cook first so nothing goes to waste.

---

## Features

- **Stow provisions** — add foods with use-by dates, or load a sample galley
- **Galley locker** — urgency colors: red (today) · yellow (1–3 days) · green (4+) · gray (spoiled)
- **Cook first** — recipes from `recipes.json` plus crew-submitted meals, ranked by urgency score
- **This week’s plan** — greedy multi-meal plan that burns through soon-to-spoil food
- **Served it / Pitch spoiled** — cook to save rations, or log waste
- **Shore shopping list** — missing ingredients, no duplicates
- **Voyage log** — saved vs. lost counts and estimated money saved
- **Voyage day control** — set “today” so demos stay deterministic

**Demo lock:** with today = `2026-11-14` and the sample galley, **Chicken stir-fry** ranks first with score **16**.

---

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app app run --port 5000
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) → set voyage day to **2026-11-14** → **Load sample galley**.

### Tests

```bash
pip install pytest
PYTHONPATH=. pytest -q
PYTHONPATH=. python -m unittest test_ranking.py -v
```

---

## Built with

| Layer | Tech |
| --- | --- |
| Backend | Python 3, Flask |
| Data | SQLite, `recipes.json`, `ingredients.json` |
| Frontend | HTML, CSS, JavaScript |
| Design | Figma → Odyssey voyage UI |
| Ranking | Set matching + `heapq` (deterministic, no LLM) |

---

## Project layout

```text
Fridge-First/
├── app.py                 # Flask routes & wiring
├── models.py              # FoodItem, Recipe
├── db.py                  # SQLite + sample galley
├── ranking.py             # Urgency scoring & this-week plan
├── security.py            # Input checks & CSP headers
├── shopping.py / stats.py # Shopping list & voyage impact
├── recipes.json           # Voyage cookbook
├── ingredients.json       # Ingredient dropdown
├── templates/             # Flask HTML (served)
├── static/                # CSS / JS (served)
├── docs/                  # Guides, contracts, Devpost story
└── test_*.py              # Model, DB, and ranking tests
```

Root `index.html`, `css/`, and `js/` mirror the Flask `templates/` + `static/` assets for convenience.

---

## Team (HackUTA)

| Role | Owns |
| --- | --- |
| Python / API | Routes, shopping list, stats, integration |
| Frontend + security | Screens, voyage theme, input hardening |
| DSA | Urgency points, set matching, heap ranking |
| Data-model | Classes, SQLite, `recipes.json` |

---

## Docs

| Doc | What it is |
| --- | --- |
| [docs/HACKUTA_BUILD_GUIDE.md](./docs/HACKUTA_BUILD_GUIDE.md) | Build plan, demo script, judging alignment |
| [docs/CONTRACTS.md](./docs/CONTRACTS.md) | Shared API / ranking contracts |
| [docs/PROJECT_STORY.md](./docs/PROJECT_STORY.md) | Full Devpost project story |
| [docs/PROJECT_STORY_SHORT.md](./docs/PROJECT_STORY_SHORT.md) | Short Devpost story |

---

## Scoring (quick reference)

| Days left | Color | Points |
| ---: | --- | ---: |
| 0 | red | 10 |
| 1–3 | yellow | 5 |
| 4+ | green | 1 |
| &lt; 0 | gray | 0 (excluded) |

Recipe score = sum of points for locker ingredients it uses. Rank by score ↓, missing ↑, name A–Z.

---

## License

Hackathon project for HackUTA 2026. See repository collaborators for team ownership.
