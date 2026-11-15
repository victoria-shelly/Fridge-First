# Shared contracts

Fill this in during the first 30 minutes. Do not change field names after the 2:00 sync without telling everyone.

## Urgency

| Days left | Color | Points |
| --- | --- | --- |
| 0 | red | 10 |
| 1–3 | yellow | 5 |
| 4+ | green | 1 |
| < 0 (expired) | gray | 0 (excluded from scores) |

`days_left = (expires_on - today).days`

## Ranking

1. Higher score first (`sum` of points for fridge ingredients the recipe uses)  
2. Fewer missing ingredients  
3. Alphabetical recipe name  

Same fridge + same `today` → same order, always.

## JSON shapes

### Item

```json
{
  "id": 1,
  "name": "chicken",
  "expires_on": "2026-11-14",
  "days_left": 0,
  "color": "red",
  "urgency_points": 10
}
```

### Recipe (ranked)

```json
{
  "name": "Chicken stir-fry",
  "uses": [
    { "name": "chicken", "color": "red", "urgency_points": 10 },
    { "name": "bell pepper", "color": "yellow", "urgency_points": 5 },
    { "name": "rice", "color": "green", "urgency_points": 1 }
  ],
  "missing": ["soy sauce"],
  "score": 16
}
```

### Stats

```json
{
  "saved_count": 3,
  "wasted_count": 1,
  "estimated_money_saved": 12.5
}
```

## Routes

| Method | Path | Body / query | Owner notes |
| --- | --- | --- | --- |
| POST | `/items` | `{ "name", "expires_on" }` | reject bad dates / long names |
| GET | `/items` | `?today=YYYY-MM-DD` | sorted urgent first |
| DELETE or POST | `/items/<id>/throw` | `{ "today" }` optional | increments wasted |
| GET | `/recipes` | | built-in + custom |
| POST | `/recipes` | `{ "name", "ingredients": [] }` | custom → DB |
| GET | `/rank` | `?today=YYYY-MM-DD` | DSA scorer |
| POST | `/cook` | `{ "recipe_name", "today" }` | remove uses; saved += n; shopping += missing |
| GET | `/shopping-list` | | unique ingredient names |
| GET | `/stats` | | saved / wasted / $ |
| POST | `/sample-fridge` | `{ "today" }` | load ~8 demo items |

## Ingredient name rules

- Store lowercase trimmed names (`"Bell Pepper"` → `"bell pepper"`)  
- Dropdown list = `ingredients.json`  
- Unknown foods allowed in fridge; they just won’t match recipes  

## Worked example lock

`today = 2026-11-14` with the pitch sample fridge → **Chicken stir-fry** ranks #1 with score **16**.
