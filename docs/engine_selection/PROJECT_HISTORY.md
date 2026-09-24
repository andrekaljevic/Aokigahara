# What went wrong across the restarts, 9–22 September 2026

Written 24 September 2026 from everything that survives: every branch in this repository, a git bundle of 20
Mac-only Unreal commits from 11 September (with that day's visual QA notes and contact sheets), 56 Unreal frames from
15 September, the owner's screenshots of the sessions, and the research files uploaded on 23–24 September. The detailed
git reconstruction is in `history/git_timeline.md`. The Unreal project itself was never committed, so nothing here can
be re-run.

## The short answer

The world was restarted about eight times (more, counting the scope cuts inside the 15–16 September passes), and each restart changed the area, the tool or the data. None of them
defined what "right" looks like at a spot you are standing on, or checked it in a way that could catch a step
backwards. Three things kept happening:

1. **Detail only ever existed in one small place.** Every version had a small detailed zone inside a large coarse one,
   and each restart made the zone smaller rather than making the detail spread.
2. **Changes often never reached the screen, and the checks could not tell.** Settings silently fell back, captures
   were taken while the engine was still compiling, auto-exposure cancelled lighting changes, and new assets were never
   loaded by the build.
3. **The measuring stick kept moving.** The comparison was the old web build one day, an overcast photo the next, and
   "looks better" throughout. When the world flipped from a dark closed forest to a bright open park on 15 September,
   nothing flagged it.

Shrinking the map could not fix any of these, which is why each cut felt like no progress.

## The restarts

| When | What | Area with real detail | Outcome |
|---|---|---|---|
| to 9 Sep | Research dossier (chat assistant, `/mnt/data` scripts) | none: a 171 km² study area, forest about 30 km² | 35-page dossier and a plan to "check GSI 1 m DEM coverage first"; no data fetched |
| 9 Sep | Pass 1 web world (hosted on a chatgpt.site address, inferred) | 2.048 km square at 8 m, inside a 32 × 30 km terrain | 467,601 procedural trees; the 1 m DEM advice was not followed |
| 10 Sep | Pass 2 web world (Claude.ai, Fable 5.1 Max) | a 120 m patch that follows the camera | Session ended mid-diagnosis; its handover zip was truncated (12 files still missing) |
| 10 Sep | Recovery and web fixes (Claude Code, Opus 5) | same | Fixes stayed on `dev` and never reached `main` |
| 10 Sep evening | Unreal 5.8 migration prepared in a cloud container with no Mac, GPU or Unreal | three overlapping landscapes: 2 km (8 m data resampled), 19.5 × 14 km and 32 × 30 km | Importers written but never run there; the brief asked for "AAA near-field density" over 32 × 30 km |
| 11 Sep | Unreal on the Mac, passes v1–v3b (Opus 5) | the 2 km core | The best lighting of the whole project (the frames the owner values) at 6–18 fps; never pushed |
| 12 Sep | Research track: photo dossier, supplement, gap audit | none | Leads only; "stop broad discovery here" |
| 15–16 Sep | Visual quality iteration v7–v20 on the Mac (Fable 5.1, ultracode) | a hero field about 30 m deep, masked to one reference photo (IMG-013) | Flipped to a bright open park; later passes mostly changed crown colour; never pushed |
| 17–19 Sep | Measured rebuild (likely Codex): 916 MB of Yamanashi LiDAR downloaded; the `Aokigahara_Real` world deleted | one survey sheet, about 400 × 300 m, with a validation crop never chosen | Rules and tests only; CI passed on test fixtures, never on real data; no landscape built |
| 22 Sep | Texture packs (Fable 5.1, two parallel sessions) | none | About 63% of all bytes ever pushed; not loaded by any runtime; "none of the photographs was taken at Aokigahara" |

The Unreal work on the Mac (11 and 15–16 September) left no trace in git beyond the 11 September bundle. Nothing was
pushed for 7.1 days, from 10 September 21:11 to 17 September 23:00.

## What went wrong

### 1. The target was a size, not a picture

The brief asked for a full-scale, photorealistic replica: first 171 km², then 960 km², then 32 × 30 km with "AAA
near-field density", on a fanless 16 GB MacBook Air. Every cut changed the area; none said what a correct view at a
given spot should look like or how that would be checked. The Unreal migration brief itself said to make "the first
20–30 m genuinely excellent" and prove one area before scaling (`MIGRATION_BRIEF.md` on
`ue5.8/aokigahara-production`); that was not followed.

### 2. Detail never existed where you walk

- Pass 1: a 2 km core at 8 m resolution; everything else 38–62 m.
- Pass 2: a 120 m patch around the camera.
- Unreal: the 2 km core resampled from the same 8 m data, so no new detail. Three landscapes were imported at full
  extent and no script ever cut or deleted one. The owner's aerial frames show the detailed block sitting in coarse
  terrain that runs to the horizon.
- 15 September: ground detail confined "to IMG-013 by a world-rect mask in the floor shader", about 30 m around one
  photo's location.
- 19 September: one 400 × 300 m sheet.

Close-up data (roots, rock faces, moss) does not exist publicly (`aokigahara_gap_audit`, 12 September), so it has to
be generated by rules. It was tuned by hand at a hero spot instead, and "propagate by variant tiles" was left for later.

### 3. Changes did not reach the screen, and nobody could tell

From the agents' own commit messages and QA notes:

- **"Nanite foliage" was never on.** A default setting left Nanite disabled on every generated tree, so v1 and v2 drew
  about 54,000 heavy trees with no LODs "four times per frame". Every speed conclusion until then described "a forest
  that never rendered through Nanite".
- **Scanned rocks and wood rendered with Unreal's grey default material** in the game, because a usage flag was set
  in memory but never saved (26 warnings). The fix took three attempts.
- **Two capture runs in a row were invalid.** One was taken mid-compile ("pale grey shards"); the next rendered
  everything with default materials because the shader cache started 100 s late.
- **Auto-exposure absorbed lighting changes.** "Sky ×0.6 leaves the overcast floor unchanged (108 → 108)."
- **Bounce light lagged about 300 frames** after a material change, so early screenshots showed stale lighting.
- **Speed tests drifted more than the effects.** "Lumen off and half resolution both came out slower than base."
- **The landscape material did not reach every streaming piece** (fixed in the local-only commit `5912fc8`).
- In the web builds: a distant-ground fallback that "never fired", a lighting menu "that did nothing", broadleaf trees
  that "fell back to the low mesh at every distance", and texture packs that the runtime never loaded.

So a carefully written prompt could change a parameter and the picture would not move, or would move for an unrelated
reason.

### 4. The measuring stick kept moving

- The Unreal tone was scored against the old web build: "the comparison reference, not truth".
- The key camera (09) was tuned to IMG-013, an overcast photo, while the owner valued sunlit frames.
- Captures were run with `-AokiLightingOverride=Overcast` (session screenshot, 16 September).
- Before/after sheets showed that something changed, not whether it moved towards the target.
- An outside assessment on 15 September said it plainly: "I was too loose earlier in treating visible improvement as
  evidence of fidelity."

### 5. The Mac could not run what was being built

Forest views ran at 6–18 fps at 1280 × 720 with 67% of the pixels rendered; the texture pool hit "Critical" in v1.
Each speed fix traded looks away: lower shadow resolution, baked trees that then rendered black, thinner crowns. On a
fanless machine, run-to-run drift was larger than most of the effects being tested.

### 6. Work was scattered and lost

Nine branches and no merges. Web fixes stranded on `dev`. A week of Unreal work kept only on the Mac. A world deleted.
A handover zip truncated. The owner's brief never committed. Research, asset hunts and texture packs ran as
separate tracks that rarely reached the world. Each restart, and each switch between ChatGPT, Claude Fable 5.1, Claude
Opus 5 and (likely) Codex, began by reconstructing context from what survived.

### 7. The fix was managed by relayed prose, and the same diagnosis came back at every scale

The owner's ChatGPT handoff notes from 15–16 September (pasted into the session on 24 September; one chat of several)
show a second layer of management. ChatGPT reviewed screenshots and wrote the prompts; Claude Fable 5.1 built in
Unreal on the Mac; the owner carried text and screenshots between them.

- **Scope kept shrinking.** By 15 September a propagated world existed: `v52_propagated_real_map_20260915`, with 166
  tiles of 200 m (about 6.6 km²), 39,016 canopy trees, about 4.46 million understory instances and six ecological
  recipes. Work then narrowed to a 100 × 100 m proof section, then a 25 × 25 m hero patch (625 m²), then a single
  acceptance camera (Camera 92, framed on IMG-013).
- **The diagnosis never changed.** At every one of those scales the notes say the same thing: the ground reads as
  "terrain + separately placed rocks + separately placed ferns", roots as cylinders, moss as a green coating, ferns
  too big and bright.
- **Finer terrain did not help.** The relief was rebaked at 0.125 m (64 chunks). The notes' own verdict: it "largely
  produced higher-resolution smoothness". A heightfield cannot hold ledges, undercuts, fissures or slabs, so the
  missing layer, the fractured lava and the roots and moss fused into it, never came from terrain work.
- **Experiments were tried and abandoned.** Generated lava blobs ("faceted, artificial rubble"), a bespoke hero trunk,
  dark cylindrical roots, hundreds of moss-clump props, and Landscape/Nanite displacement (switched off) were all
  rejected.
- **The look that finally read as forest was unplayable.** The approved dense state (commit `a4d7f2a`, not pushed to
  this repository) measured 104 ms a frame, about 10 fps.
- **The advice pulled in opposite directions.** One note asks for more enclosure and less sky; another says the scene
  is too contrasty, collapses into black, and needs its midtones lifted. One says to keep the forest and not rebuild
  it; another says the hero foreground may be substantially replaced.
- **The prompts grew until they contradicted themselves.** One ran to 30 sections of rules and "anti-faff" limits,
  and still carried stale lines ("establish the actual reference camera", "preserve a BEFORE") that contradicted its
  main body.
- **Progress was read from the tools' interface.** Diff counts (+219, then +946 lines) and "thinking" time stood in
  for pictures while a pass ran. The deciding picture was always a single hero camera, judged by eye.

The advice itself was often sound: "visual truth beats implementation explanation", "geometry must survive lighting
changes", "screenshots are the arbiter". What failed was the loop around it: each chat started fresh, and neither the
planner nor the builder could render and measure quickly. Each iteration meant a compile and a warm launch on a fanless
laptop, and the hardest problem, a ground structure that no terrain or setting provides, was attempted as a sequence
of prompted experiments at one spot.

## What the frames show (15 September, 56 renders)

Measured with `tools/lighting_stats.py`; the full tables are in the analysis kept outside the repository.

- **v7 → v13 changed 87–99% of pixels on all seven cameras,** and made every view 3.7–4.3 stops brighter than the
  valued frames g–j. Black fraction fell to 0.000 and stayed there; sky share rose from 0.03–0.06 to 0.20–0.49. A dark,
  closed forest became an open pine park on lawn-like ground.
- **After v13, versions mostly changed crown colour and tints,** sometimes undoing each other (grey needles in v15 and
  v16, green again in v19). On camera 81 only 1.6% of the ground changed between v13 and v20.
- **Only two frames of 28 met two of the three lighting bands:** the earliest camera 09 frame and the 25 m prototype.
- **Against the IMG-013 photo** (same width): detail 5–22 against 52, edge density 0.07–0.39 against 0.83, and no
  red-brown at all from v7 on. No version shows moss-covered lava.
- The real improvements removed defects the process had created itself: white untextured cards, a black lattice crown,
  grey crowns.

The 11 September contact sheets tell the opposite story for that day: v1 (bare poles in full sun) to v3b (dark crowns,
deep shade) was a genuine gain, and is where the owner's valued frames come from. Everything after moved away from it.

## What survives and is worth keeping

- The lighting of 11 September, as measured targets (`renders/ue58_baseline/`, frames g–j).
- The Yamanashi 2024 LiDAR route: 0.5 m products fetchable from the cloud (`tools/marble_test/yamanashi_sheets.py`).
- The rebuild's evidence rules (`REBUILD_2026-09-19.md` on `rebuild/measured-2026-09-19`): no invented lava relief,
  no orthophoto colour on the ground, no silent hole filling.
- The Ministry of the Environment vegetation map (uploaded 24 September): the forest core is natural hinoki forest with
  the fern *Arachniodes mutica* (シノブカグマ–ヒノキ群集), 24.7 km², plus 4.3 km² of *Tsuga* forest. Licence to confirm.
- Content leads from the 15 September asset audit: CC0 scans of *Chamaecyparis obtusa* (ffish.asia on Sketchfab),
  PBRPX *C. pisifera* trunk scans (CC0), free fern scans on Fab, and one real Aokigahara forest-floor scan whose author
  would need to be asked.

## What the plan changes because of this

| What went wrong | What `ENGINE_SELECTION.md` now does |
|---|---|
| A size, not a picture | Fixed targets: the valued frames' lighting numbers, the owner's photos, a blind sort, and one sheet, then one tile, then the plot |
| Detail in one small place | Near-field detail generated by the same rules in every tile, checked at random spots across the plot |
| Changes not reaching the screen | Agents render and measure every change headless in the cloud, from a warmed, known state, before the owner sees it |
| A moving measuring stick | Regression cameras must not get worse; the target look is chosen once (open question 10) |
| A Mac that could not run it | Godot app exported from the cloud; one 10-minute benchmark on the Mac (milestone 0) before any content work |
| A ground structure no heightfield can carry | The near-field kit includes fractured-lava geometry fused into the terrain, root flares and moss as a surface condition (section 3) |
| A dense look that ran at 10 fps | The milestone 0 probe includes a dense near-field segment, so the density budget is known before content is built |
| Relayed prose, fresh chats, one hero camera | One builder in one repository; decisions written down once; numbers and random spots, not a single view, decide |
| Scattered, lost work | One repository, every step pushed, the brief and decisions committed, session budgets and stop rules |

## Evidence

- Branches: `main`, `dev/generational-visual-upgrade`, `ue5.8/aokigahara-production`, `rebuild/measured-2026-09-19`,
  `claude/aokigahara-fable-handoff-0fdzom`, `claude/aokigahara-uhd-assets-5l10c2`,
  `claude/4k-asset-packs-photos-sy83u7`. Detail in `history/git_timeline.md`.
- The 11 September bundle (`ue5.8-aokigahara-production-5912fc8..bc8e9e1`) was supplied by the owner. It depends on
  commit `5912fc8`, which exists only on the owner's Mac, so it cannot be fetched into this repository; its commit
  messages and QA notes were read by parsing the pack. It is not committed here.
- The 15 September frames, the session screenshots and the other uploads are the owner's and are not committed.
  Two pairs are reproduced in `renders/ue58_history/`.
