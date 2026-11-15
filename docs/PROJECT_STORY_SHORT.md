# Fridge-First (short Devpost story)

## Inspiration

We waste food because we guess what to cook instead of cooking what expires first. HackUTA’s Odyssey theme made that concrete: a fridge is a galley on the voyage home, and someone has to watch the provisions. We wanted a tool that felt thematic, demoable, and checkable by hand — no AI black box.

## What it does

Fridge-First tracks your fridge, colors items by urgency (red / yellow / green / gray), and ranks recipes from `recipes.json` so you cook the most urgent food first. You can load a sample galley, serve a meal, pitch spoiled food, build a shore shopping list, and track saved vs. lost in the voyage log. A “voyage day” control makes demos deterministic — on Nov 14, chicken stir-fry ranks first with score \(16\).

## How we built it

Flask + SQLite + HTML/CSS/JS, with an Odyssey ship-home UI. Four equal roles: API/stats, frontend/security, DSA ranking, and data-model/`recipes.json`.

Urgency points: red \(= 10\), yellow \(= 5\), green \(= 1\), gray \(= 0\). Recipe score is the sum of points for ingredients still in the locker; ties break by fewer missing ingredients, then name.

## Challenges we ran into

Merging four branches with mismatched APIs, learning web stack from a mostly C/Java background, keeping the Odyssey theme tied to real UX (not just decoration), and cutting barcodes/accounts/LLM features so we could ship.

## Accomplishments that we're proud of

A working demo path (sample galley → rank → serve → shopping/log), a ranking rule judges can verify by hand, a cohesive voyage UI, and four people integrating separate modules into one story.

## What we learned

Contracts beat last-hour glue. Deterministic rules calm demos. Theme should shape language and flow, not just visuals. Shipping the spine matters more than a long feature list.

## What's next for Fridge-First

**A new theme every month** — same ranking engine, fresh skin, cookbook, and story (seasonal kitchens, campus life, holiday feasts, more literary voyages). Also: bigger rotating cookbooks, optional barcode/receipt import, light household accounts, richer waste stats, and swappable theme packs.
