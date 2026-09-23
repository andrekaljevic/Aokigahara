# How far a Marble world holds up: walk-out test on World Labs' sample exports

Run on 23 September 2026 with `tools/marble_test/view_splats.mjs` and `score_walk.py`. The inputs
were two of World Labs' public example exports (500k-splat SPZ from `wlt-ai-cdn.art/example_exports/`):
`modern_house_with_lush_landscaping` and `narrow_european_cobblestone_lane`.

Each world was rendered headless from its origin, the viewpoint it was generated from, and then
from 2, 5, 10 and 20 units out, in four headings, looking outwards. The images are not kept in
this public repository because they are renders of World Labs' content. Reproduce them with the
commands in `tools/marble_test/README.md`.

A second part, below, records the owner's own test in the Marble web app the same evening.

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
- **detail:** the mean absolute Laplacian. The four of the owner's photos used as references
  here score 21–27.

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

## The owner's own test in the Marble web app (23 September 2026)

### What went in

- **App and model:** the free Marble web app (marble.worldlabs.ai), 3D input mode, Chisel editor,
  Marble 1.1 Plus.
- **Prompt:** a text description of the Aokigahara Sea of Trees at the foot of Mount Fuji:
  old-growth hemlock and hinoki on moss-covered lava.
- **Layout:** the prompt started Chisel's automatic layout before the real-terrain block-out
  (`tools/marble_test/chisel_glb.py`: sheet 08LE9335, 105 trees) had been uploaded. So the world
  came from Chisel's own layout plus the prompt, **not from the real terrain**.

### What came out

- **At the start point:** a bright tropical jungle. Broad palm-like and banana-like leaves, red
  spiky flowers, bamboo-like stems and moss-covered leaning trunks. Not Aokigahara's conifers on
  black lava. The look is smooth and illustration-like rather than photographic.
- **Moving away** (the owner used the scroll wheel and keys): stretched green streaks within a
  short distance.
- **From outside:** the whole world is one small bubble surrounded by black.
- **The owner's verdict:** "fairly limited world it made tbh".

### Measured

The start-point view was cropped from the owner's browser screenshot to leave out the app's
interface (a 1540 × 640 px region of the viewport), rescaled to 1280 px wide, and scored with
`tools/lighting_stats.py`, the `texture()` function in `tools/marble_test/score_walk.py`, and a
whole-frame mean HSV saturation. The owner's 14 reference photos and UE5.8 frames h–k were scored
the same way. The lighting targets are the g–j ranges from `renders/ue58_baseline/README.md`.

| Measure | Marble start view | Owner's photos, all 14 | Photos U01–U13 only (12) | UE5.8 |
|---|---|---|---|---|
| Fine detail (mean absolute Laplacian) | **8.1** | 14.2–34.1 | 19.8–26.6 (median 22.7) | 17.9–26.5 (h–k) |
| Saturation (whole-frame mean, HSV) | **0.605** | 0.24–0.43 | 0.24–0.33 (median 0.26) | 0.19–0.44 (h–k) |
| Exposure key (log-average luminance) | **0.101** | 0.006–0.027 | 0.006–0.012 (median 0.010) | g–j target 0.003–0.008 |
| Black fraction (deep shade) | **0.014** | 0.056–0.221 | 0.056–0.221 | g–j target 0.17–0.43 |
| Sunfleck fraction | **0.038** | 0.091–0.249 | 0.091–0.224 | g–j target 0.07–0.16 |
| Highlight B/R (below 1 is warm) | 0.774 | 0.585–0.797 | 0.689–0.797 | g–j target 0.29–0.42 |
| Edge density | 0.447 | 0.336–0.575 | 0.336–0.403 | 0.17–0.28 (h–k) |

In words, against the owner's photos:

- about twice as saturated as a typical photo;
- about ten times a typical photo's exposure key, and 4–17 times across all 14 photos;
- almost no deep shade, and few sunflecks;
- about a third of a typical photo's fine detail, and below every photo.

That is the opposite of the dark, dappled forest light the owner valued in UE5.8. Two measures do
not count against it: its highlight colour sits inside the photos' range, and its edge density
sits inside the 14-photo range. Edge density tracks sharpening and compression as much as content,
so it says little here.

The widest photo ranges come from two outliers: U15, a heavily dehazed phone edit, and an upscaled
4K portrait. U01–U13 are one edited winter shoot. The saturation here is the whole-frame mean,
not the lit-pixel figure used in the photorealism research, so the two are not comparable.

### Caveats

- **One screenshot,** from one viewpoint.
- **A browser capture, not a render.** It was WebP-compressed and taken at Retina scale, then
  cropped and rescaled. Compression and rescaling change the detail and edge figures. The lighting
  figures describe the displayed image after the app's own tonemapping.
- **The wrong layout:** Chisel's automatic layout, not the real terrain.
- **Text-only input.** A photo-driven try (2D input from Aokigahara photos the owner holds the
  rights to) has not been done. It is the fair best case.

The screenshot and its metrics are kept outside this public repository, like the sample renders.

## What it means for the project

A single Marble world is a photographic bubble a few metres across, not a place you can roam.
Covering a walked trail with unbroken photographic quality would need a new world every few
metres: thousands of worlds for the plot's trails, all hand-joined. So Marble suits fixed
look-around stops and short vignettes at most, not the free-roam backbone.

The owner's test adds two things:

- **A prompt alone does not give Aokigahara.** Marble drew a generic tropical jungle: brighter,
  more saturated and much less detailed than the owner's photos, with little of the deep shade and
  few of the sunflecks the owner valued in UE5.8.
- **Marble 1.1 Plus showed no sign of a larger world in this try:** streaks began a short,
  unmeasured distance from the start, and the whole world was one small bubble.

Two tests are still open, and together they are the fair best case:

- **Photo-driven (2D input):** a world generated from a few Aokigahara photos, walked out from
  the start point in the same way. Only this can show whether Marble reproduces this forest at
  all. Use only photos the owner took or holds the rights to; World Labs' terms for uploaded
  inputs have not been checked.
- **API real-terrain test:** the kit in `tools/marble_test/` dresses a depth panorama of real sheet
  08LE9335 and measures the walk-out in metres. It needs `WLT_API_KEY` set in the cloud
  environment's settings, never pasted into a chat, and $5 of API credit (6,250 credits): enough
  for one draft world at 150 credits and three standard worlds at 1,500 credits each, with some
  margin for the depth-to-RGB step, whose price is not published.

Until one of these shows a world that looks like Aokigahara and stays photographic well beyond a
few metres, Marble stays outside the plan. At most it could add a few look-around stops at trail
spots, labelled as synthetic. The sample worlds' model version is unknown.
