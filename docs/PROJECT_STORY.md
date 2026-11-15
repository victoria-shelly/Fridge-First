# Fridge-First

HackUTA 2026 · Odyssey · watching over food provisions on the journey home

---

## Inspiration

Food waste is quietly dramatic: you buy groceries with the best intentions, blink, and the chicken that was “for later” is already gone. We kept noticing how often people guess what to cook instead of letting urgency decide.

HackUTA’s Odyssey theme gave us the metaphor we’d been missing. Odysseus doesn’t just sail home — he has to **watch the provisions**. A fridge is a galley locker on the voyage from store to dinner. That framing made the product feel alive for a hackathon demo and honest about the problem: finite rations, a ticking use-by date, and a choice to cook in time or lose it before you make port.

We also wanted something a mostly C/Java team could ship in one weekend without leaning on a black-box AI. Deterministic rules you can check by hand felt like the right kind of clever.

## What it does

**Fridge-First** is a web app that tracks what’s in your fridge (the galley), colors each item by how soon it spoils, and ranks recipes so you cook the most urgent food first.

- **Stow provisions** — add foods with use-by dates, or load a sample galley for demos  
- **Galley locker** — items sorted by urgency: red (today), yellow (1–3 days), green (4+), gray (already spoiled)  
- **Cook first** — recipe cards from our voyage cookbook (`recipes.json`), scored by how much expiring food they use, plus what’s missing  
- **This week’s plan** — a greedy set of meals that burns through soon-to-spoil rations without reusing the same item twice  
- **Served it / Pitch spoiled** — cook to save provisions, or pitch spoiled food and log the loss  
- **Shore shopping list** — missing ingredients, deduped for the next port stop  
- **Voyage log** — saved vs. lost counts and a rough estimate of money saved  
- **Voyage day control** — set “today” so demos and tests always replay the same day  

On voyage day **Nov 14**, with chicken expiring today, **Chicken stir-fry** ranks first with score \(16\) — cook it now or lose it before port.

## How we built it

Stack: **Flask (Python) + SQLite + plain HTML/CSS/JS**, with Figma for UI direction and an Odyssey “ship sailing home” interface.

We split the work into four equal ownership slices so we could build in parallel:

| Role | Owned |
|------|--------|
| Python / API | Flask routes, shopping list, stats, integration |
| Frontend + security | Screens, voyage theme, input hardening / CSP |
| DSA | Urgency points, set matching, heap ranking, weekly plan |
| Data-model | `FoodItem` / `Recipe`, SQLite, `recipes.json` |

Core scoring is intentionally simple and auditable. Urgency points by days left:

\[
p(d) =
\begin{cases}
10 & d = 0 \quad (\text{red}) \\
5 & 1 \le d \le 3 \quad (\text{yellow}) \\
1 & d \ge 4 \quad (\text{green}) \\
0 & d < 0 \quad (\text{gray; excluded})
\end{cases}
\]

A recipe’s score is the sum of points for ingredients still in the locker:

\[
\text{score}(R) = \sum_{i \in R \cap \text{locker}} p(d_i)
\]

We rank by highest score, then fewest missing ingredients, then name — so the same fridge on the same day always produces the same order. Recipes shown in ranking come from **`recipes.json`** (our fixed voyage cookbook), not from generative AI.

## Challenges we ran into

- **Merging four branches under time pressure.** Frontend expected `/api/...` shapes while backend drafts used different paths and field names. We had to stop and rewrite contracts so the demo path worked end-to-end.  
- **Skill stretch.** Most of the team is strongest in C/Java; shipping Flask + browser UI meant learning just enough web stack without boiling the ocean.  
- **Keeping the theme honest.** It was easy for “Odyssey” to become decoration. We kept rewriting copy and layout until the ship/galley language matched the real product: urgency, cook-first, saved vs. lost.  
- **Resisting feature creep.** Barcodes, accounts, and LLM recipe generation all sounded cool. We cut them so completion and a clean 3–4 minute pitch stayed realistic.

## Accomplishments that we're proud of

- A **working demo path**: sample galley → ranked cookbook → Served it → shopping list + voyage log  
- A ranking algorithm judges can verify by hand (chicken stir-fry = \(10 + 5 + 1 = 16\))  
- An Odyssey UI that feels like a voyage home, not a generic dark dashboard  
- Four people owning separate modules and still integrating into one story  

## What we learned

- Clear **API contracts** beat heroic last-hour glue  
- Deterministic rules make demos calmer than “hope the model agrees”  
- Theme works best when it shapes vocabulary and UX, not just the wallpaper  
- For a hackathon, **shipping the spine** (add → see urgency → cook → impact) matters more than a long feature list  
- C/Java instincts transfer: classes, sets, heaps, and parameterized queries map cleanly onto Python/SQLite once you stop fighting the web layer  

## What's next for Fridge-First

Fridge-First was built as a fridge steward for this Odyssey weekend — but the product idea is bigger than one theme.

**We’re planning a new theme every month.** Same core engine (urgency colors, deterministic ranking, voyage-day control, impact log); a fresh skin, cookbook, and story each month so the experience stays playful and shareable. Think seasonal kitchens, campus life, holiday feasts, or another literary voyage — always still answering: *what should we cook first so nothing goes to waste?*

Near-term roadmap under that cadence:

- Grow and rotate monthly `recipes.json` cookbooks  
- Optional barcode / receipt import for faster stowing  
- Light accounts so a household can share one galley  
- Stronger impact stats (waste trends over a real month)  
- Theme packs: art, copy, and sample galley that swap without rewriting the ranking brain  

Fridge-First stays the steward. The journey just keeps changing.
