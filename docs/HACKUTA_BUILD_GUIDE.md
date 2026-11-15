# Fridge-First — HackUTA 2026 Build Guide

Team of 4 · Odyssey theme · Flask + SQLite + HTML/CSS/JS · Figma for UI

This guide turns your pitch into a buildable plan that matches HackUTA expectations: ship a working demo, tell a clear Odyssey story, and hit Devpost + judging.

> **Note:** The HackUTA slide PDF (`HackUTA 2026_compressed.pdf`) was not readable from the upload. Expectations below are taken from [hackuta.com](https://www.hackuta.com/) plus past HackUTA Devpost judging (Technology, Design, Learning, Completion, Originality). Re-upload the PDF if it adds tracks, sponsor challenges, or scoring details we should weave in.

---

## 1. One-sentence story (say this first in every pitch)

**Fridge-First is the ship’s steward for your fridge:** it watches food provisions on the journey home, warns before they spoil, and tells you what to cook first so nothing is wasted.

| Odyssey idea | Product feature |
| --- | --- |
| Provisions on the voyage home | Fridge inventory with expiry dates |
| Watching over stores | Color urgency (red / yellow / green / gray) |
| What to use first so the crew survives | Deterministic recipe ranking |
| Log of the voyage | Saved vs wasted + money saved |
| Charting the route | “Today is” date control for demos |

You do **not** need AI, accounts, or a mobile app. Judges care that it works, looks intentional, and has a crisp problem → solution → tech story in 3–4 minutes.

---

## 2. HackUTA rules that actually change how you work

From HackUTA 2026 FAQ / schedule:

| Rule | What you should do |
| --- | --- |
| Hacking window: **Sat noon → Sun noon** | All code, Figma assets, and build work happen in that window. Brainstorming beforehand is fine. |
| **Devpost deadline: Sat 11:59 PM** | Submit **Title + Description + GitHub URL** Saturday night even if polish continues until Sunday noon. |
| Judging: expo-style, **3–4 min pitch + Q&A** | Rehearse a fixed demo script (section 8). Problem, solution, tech. |
| Team size ≤ 4 | Perfect fit. Stick to four equal ownership slices. |
| Open source / templates OK | Flask, SQLite, vanilla JS are fine; credit them in Devpost. |
| Start fresh | Do not paste a finished pre-hack repo. Planning docs (this file) and public recipes ideas are OK; write the app during the event. |

Past HackUTA judging criteria (use these as your quality bar):

1. **Completion** — Does the demo path work end-to-end?
2. **Design** — Can a judge use it without you explaining every click?
3. **Technology** — Real ranking logic + DB + security checks beat a slideshow.
4. **Originality** — Odyssey framing + deterministic “same fridge → same answer” is your hook.
5. **Learning** — Call out that most of the team is C/Java and shipped a web stack this weekend.

**Priority order if time is short:** Completion → Design → Technology → Originality → Learning.

---

## 3. Stack (chosen for your skills)

| Layer | Choice | Why |
| --- | --- | --- |
| Backend | **Flask (Python)** | One teammate is comfortable with Python; routes stay small and readable for C/Java folks. |
| Data | **SQLite + `recipes.json`** | No cloud setup. Java-like classes map cleanly to rows. |
| Frontend | **Plain HTML / CSS / JS** | Closest mental model to Java GUIs; no React learning tax. |
| Design | **Figma → CSS** | Design in Figma, implement screens that match; don’t chase pixel-perfect. |
| Stats | **pandas** (optional if time) | Nice for impact page; hand-written counters are fine as MVP. |

### Skill bridge for C / Java teammates

| You already know | In this project |
| --- | --- |
| Classes, getters | `FoodItem`, `Recipe` in `models.py` |
| `HashSet` / `TreeSet` | Python `set` for ingredient match / missing |
| Priority queues / heaps | `heapq` for ranking |
| JDBC `?` placeholders | SQLite `?` params (never string-concat SQL) |
| JUnit assertions | Small `test_*.py` with assert |
| Swing / Android layouts | HTML forms + CSS grid; Figma frames ≈ screens |

Python person owns Flask wiring and the 3:30 integration. Everyone else stays in **their own files** until then.

---

## 4. Roles → files (no merge fights)

Agree on names once, then work only in your column.

| Role | Owns | Files (suggested) | Done when |
| --- | --- | --- | --- |
| **Python** — API + stats + glue | Routes, shopping list, stats, app entry | `app.py`, `stats.py`, `shopping.py` | Every route returns agreed JSON; sample fridge demos |
| **Frontend + security** | UI screens + input hardening | `static/`, `templates/`, `security.py` | Five screens + date control; XSS/SQL-ish names stay plain text |
| **DSA** — ranking | Urgency, score, heap rank, “This week” | `ranking.py`, `test_ranking.py` | Worked example (chicken stir-fry = 16) passes |
| **Data-model** | Classes, DB, recipe seed | `models.py`, `db.py`, `recipes.json`, `ingredients.json` | Colors/days_left correct; cook/throw mutate DB safely |

**Shared contracts (write these on a whiteboard or in [`docs/CONTRACTS.md`](./CONTRACTS.md) first hour):**

```text
FoodItem: { id, name, expires_on }
status(today): red | yellow | green | gray
urgency_points: red=10, yellow=5, green=1, gray=0 (not used in scores)

Recipe: { name, ingredients: set[str] }
score = sum(urgency of fridge items it uses)
rank: score desc, missing count asc, name asc

POST /items  { name, expires_on }
GET  /items?today=YYYY-MM-DD
POST /recipes  { name, ingredients: [...] }
GET  /rank?today=YYYY-MM-DD
POST /cook  { recipe_name, today }
POST /items/<id>/throw
GET  /shopping-list
GET  /stats
```

---

## 5. MVP scope (must ship) vs nice-to-have

### Must ship (demo path)

1. Add food (dropdown + expiry) + **Load sample fridge**
2. Fridge list sorted by urgency with colors
3. Ranked recipe cards (uses / missing / score)
4. **Cooked it** removes ingredients + bumps saved count
5. **Throw out** bumps wasted count
6. Shopping list (deduped missing ingredients)
7. Stats: saved vs wasted (+ rough $ if easy)
8. **Today is** date control
9. Security basics: escape output, length/date checks, parameterized SQL

### Ship if time (after integration)

- Add custom recipe form
- “This week” greedy multi-recipe plan
- Figma polish (type, color tokens, empty states)
- Rate limit (~20 adds/min)

### Cut without guilt

- Accounts / Auth0
- Camera / barcode scan
- Real nutrition APIs
- Mobile apps
- ML recipe generation (your pitch is **deterministic on purpose**)

---

## 6. Hour-by-hour plan (6–7 hour build)

Assume start ~1:00 PM after lunch / workshops. Adjust clocks; keep the **integration checkpoint**.

| Time | Everyone | Focus |
| --- | --- | --- |
| **0:00–0:30** | Kickoff | Clone repo, create venv, paste contracts, assign roles, open Figma file with 5 frames |
| **0:30–2:00** | Parallel build | Fake-data unit tests; no waiting on each other |
| **2:00–2:15** | Sync | Show JSON shapes; fix naming mismatches |
| **2:15–3:30** | Parallel finish | Frontend wires to real routes as they appear; DSA locks ranking tests |
| **3:30–4:15** | **Integration** (Python lead) | Sample fridge → rank → cook → stats on one laptop |
| **4:15–5:00** | Bug bash | Broken dates, empty fridge, duplicate shopping items |
| **5:00–5:30** | Demo script | Rehearse 3–4 min pitch twice |
| **Evening** | Buffer | Polish CSS, custom recipes, Devpost draft |
| **Sat 11:59 PM** | Submit | Devpost: title, description, GitHub URL |
| **Sun morning** | Optional | One more polish pass; stop by 11:00 so judging prep is calm |
| **Sun noon** | Hard stop | Hacking ends |
| **1:00–3:00 PM** | Judging | Expo table; run the same demo every time |

### Figma workflow (Frontend lead + 10 min from everyone)

1. Five frames only: Add · Fridge · Recipes · Impact · (optional) Add recipe  
2. Tokens: background, text, red/yellow/green/gray urgency, one accent  
3. Odyssey mood without clutter: one journey metaphor in the header (“provisions for the voyage home”), not a pirate theme park  
4. Export spacing/colors into CSS variables; implement HTML to match structure, not every shadow  

---

## 7. Deterministic rules (memorize for Q&A)

Judges love “we can check the answer by hand.”

1. **Color** from days left only: `0 → red`, `1–3 → yellow`, `4+ → green`, past → gray  
2. **Score** = sum of urgency points of matching fridge items (gray never scores)  
3. **Rank** = score ↓, missing ↑, name A–Z  
4. **No wall clock** — every calculation takes `today` from the date control  
5. **Recipes** live in `recipes.json` (~30–40) written during the hack; custom recipes go in SQLite and use the same scorer  

**Worked example (today = Nov 14):** chicken stir-fry scores `10+5+1 = 16` and ranks first. After cook: chicken, bell pepper, rice leave; soy sauce hits shopping list; saved += 3.

---

## 8. Demo script (3–4 minutes)

Practice until it fits without rushing.

1. **Problem (20s)** — Food expires; people guess what to cook; waste happens on the “journey home” from the store.  
2. **Solution (20s)** — Fridge-First watches provisions, colors urgency, ranks recipes deterministically.  
3. **Live demo (2 min)**  
   - Set **Today is Nov 14**  
   - Load sample fridge → point at chicken (red)  
   - Open rankings → stir-fry first, score 16  
   - Cooked it → fridge updates, saved +3, soy sauce on list  
   - Move date to Nov 17 → yogurt yellow, parfait rises  
4. **Tech (40s)** — Flask + SQLite; set matching + heap ranking; security escaping; four equal owners.  
5. **Learning / ask (20s)** — C/Java team shipping web + DSA in one weekend; happy to walk through the scorer.

Print the worked-example table and keep it on the table for judges.

---

## 9. Devpost checklist (submit Saturday night)

**Title ideas:** `Fridge-First` or `Fridge-First: Provisions for the Journey Home`

**Description outline:**

- Inspiration (Odyssey / watching provisions / food waste)  
- What it does (5 screens, bullet list)  
- How we built it (Flask, SQLite, ranking rules, roles)  
- Challenges (integration, learning web from C/Java)  
- What’s next (custom recipes polish, barcode optional)  

**Required:** Title · Description · **GitHub URL**  
**Helpful:** 2–4 screenshots, short demo clip, link to Figma  

---

## 10. Integration checklist (3:30)

- [ ] `Load sample fridge` shows ~8 items with correct colors for today’s date  
- [ ] `/rank` puts chicken stir-fry first on Nov 14 sample  
- [ ] Cook removes exactly that recipe’s fridge ingredients  
- [ ] Throw out increments wasted, not saved  
- [ ] Shopping list has no duplicate onion when two recipes need it  
- [ ] `<script>` in a name renders as text  
- [ ] Stats match a hand count after the demo path  
- [ ] App runs with: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && flask --app app run`

---

## 11. Suggested repo layout

```text
Fridge-First/
  HACKUTA_BUILD_GUIDE.md   ← this file
  README.md
  requirements.txt
  app.py                   ← Python role
  models.py                ← Data-model
  db.py                    ← Data-model
  ranking.py               ← DSA
  security.py              ← Frontend/security
  stats.py                 ← Python
  shopping.py              ← Python
  recipes.json             ← Data-model
  ingredients.json         ← Data-model
  templates/               ← Frontend
  static/css/              ← Frontend (from Figma tokens)
  static/js/               ← Frontend
  tests/                   ← each role’s small tests
```

---

## 12. Judging alignment scoreboard

| Criterion | How Fridge-First earns it |
| --- | --- |
| Completion | One fixed demo path always works |
| Design | Figma → clear urgency colors + recipe cards |
| Technology | Real ranking + SQLite + input hardening |
| Originality | Odyssey provisions metaphor + deterministic scoring |
| Learning | Explicit C/Java → Python/web stretch |

If you only remember three things: **ship the demo path**, **tell the voyage-home story**, **submit Devpost Saturday night**.
