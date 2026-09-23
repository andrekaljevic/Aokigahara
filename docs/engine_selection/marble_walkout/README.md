# How far a Marble world holds up: walk-out test on World Labs' sample exports

Run on 23 September 2026 with `tools/marble_test/view_splats.mjs` and `score_walk.py`. The inputs
were two of World Labs' public example exports (500k-splat SPZ from `wlt-ai-cdn.art/example_exports/`):
`modern_house_with_lush_landscaping` and `narrow_european_cobblestone_lane`.

Each world was rendered headless from its origin, the viewpoint it was generated from, and then
from 2, 5, 10 and 20 units out, in four headings, looking outwards. The images are not kept in
this public repository because they are renders of World Labs' content. Reproduce them with the
commands in `tools/marble_test/README.md`.

## What the frames showed

| Distance from origin | Garden | Cobblestone lane |
|---|---|---|
| 0 | Photographic | Photographic |
| 2 units | Convincing, with smearing and small holes at the edges | Convincing along the lane; sideways you walk into the walls |
| 5 units | Broken: blurred smears, large holes | Heavily smeared, holes |
| 10 units | Nothing: off the edge of the world | Broken |
| 20 units | Nothing | Nothing |

Marble exports are in model units. These samples carry no metric-scale metadata, and the ground
sits about 0.75–0.96 units below the origin. If the origin is at eye height, one unit is roughly
1.7–2.1 m. So photographic quality holds within about 2–4 m of the origin and has broken down by
about 8–10 m.

That agrees with Meta's WorldGen paper (November 2025), which found Marble's quality falling "as
the camera moves just a few meters away (e.g., 3–5 m)".

## Measured (scores.json)

These are means over the four headings.

- **holes:** the share of screen with no splats.
- **detail:** the mean absolute Laplacian. The owner's photos score 21–27.

The first two origin views of the garden, and the first of the lane, came back empty. That was a
renderer warm-up fault, fixed since, so the 0-unit hole figures overstate the holes.

| Units | Garden holes | Garden detail | Lane holes | Lane detail |
|---|---|---|---|---|
| 0 | 0.50 (warm-up fault) | 2.7 | 0.25 (warm-up fault) | 5.9 |
| 2 | 0.25 | 2.0 | 0.50 | 2.6 |
| 5 | 0.45 | 0.7 | 0.52 | 1.3 |
| 10 | 1.00 | 0.0 | 0.57 | 0.7 |
| 20 | 1.00 | 0.0 | 0.76 | 0.4 |

The detail figures are far below the photos even at the origin. The software renderer at
960×600 and splat softness both contribute, so compare distances with each other, not with the
photos.

## What it means for the project

A single Marble world is a photographic bubble a few metres across, not a place you can roam.
Covering a walked trail with unbroken photographic quality would need a new world every few
metres: thousands of worlds for the plot's trails, all hand-joined. So Marble suits fixed
look-around stops and short vignettes, not the free-roam backbone.

The pending real-terrain test (`tools/marble_test/`) measures the same thing for a `marble-1.1`
world dressed on actual Aokigahara terrain. `marble-1.1-plus` can generate larger worlds and may
push the bubble out further. These samples' model version is unknown.
