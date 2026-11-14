# Fridge-First

HackUTA 2026 · Odyssey theme · team of 4

A web app that tracks what’s in your fridge, warns before it expires, and ranks recipes so you cook the most urgent food first — **watching over food provisions on the journey home.**

## Start here

Read the full team plan: **[HACKUTA_BUILD_GUIDE.md](./HACKUTA_BUILD_GUIDE.md)**

Shared API / ranking contracts: **[CONTRACTS.md](./CONTRACTS.md)**

## Stack

- Flask (Python) + SQLite  
- Plain HTML / CSS / JS  
- Figma for UI before coding screens  
- Deterministic ranking (no LLM recipe generation)

## Roles

| Role | Owns |
| --- | --- |
| Python | Flask routes, stats, shopping list, integration |
| Frontend + security | Screens, Figma → CSS/JS, input hardening |
| DSA | Urgency points, set matching, heap ranking, “This week” |
| Data-model | `FoodItem` / `Recipe`, SQLite, `recipes.json` |

## HackUTA checkpoints

- **Sat 11:59 PM** — Devpost: title, description, GitHub URL  
- **Sun 12:00 PM** — Hacking ends  
- **Sun 1:00–3:00 PM** — Expo judging (3–4 min pitch + Q&A)

## Pitch line

> Fridge-First is the ship’s steward for your fridge: it watches provisions on the journey home, colors what expires soonest, and tells you what to cook first so nothing goes to waste.
