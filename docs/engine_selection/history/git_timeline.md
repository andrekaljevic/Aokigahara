# Aokigahara: how the project evolved, reconstructed from git

Repository `andrekaljevic/Aokigahara`, full clone with all 9 remote branches. 61 commits in total. This analysis covers 49 of them. The 12 on `claude/aokigahara-engine-selection-tqyqx6` are excluded because they are the current session's own work.

Times are BST (UTC+1), which matches the owner's `+0100` commits. Anything marked *(inferred)* is my reading and is not stated in the repository.

**Known gaps (not in any pushed branch):**
- The Mac-local Unreal commits after `58e42e6`, up to `5912fc8` and then 20 more on 11 Sep 05:31–14:53. These are in the owner's bundle; see `../PROJECT_HISTORY.md`.
- The 15–16 Sep "visual quality iteration" sessions (v7–v20 passes, the IMG-013 mask, tile propagation), known only from screenshots.
- The owner's own brief. It is cited in the repo as "the brief", with sections up to §48, but was never committed.

## 1. Branch map

There are no merge commits. Every branch is a straight line off one of three bases:

```
e12a0f0 Initial commit (owner, GitHub web UI, 10 Sep 06:32)
└─ 859ab5d Preserve latest Fable 5.1 Max Aokigahara reconstruction  = claude/aokigahara-fable-handoff-0fdzom
   ├─ c32be30 Pages workflow                                          = main
   │   ├─ 4b85951…2245a99 (7)   22 Sep  claude/aokigahara-uhd-assets-5l10c2   (Claude Fable 5.1)
   │   ├─ 8dbc389…312d2ec (10)  22 Sep  claude/4k-asset-packs-photos-sy83u7   (Claude Fable 5.1)
   │   └─ 31d32fc…d709d58 (12)  23 Sep  engine selection (EXCLUDED)
   └─ dc33485…de637bb (11)  10 Sep  web-viewer fixes (Claude Opus 5)
       ├─ 225f7c1, 8e6b4a4      17 Sep  dev/generational-visual-upgrade (Netlify helper, owner identity)
       └─ 6a6c612, 58e42e6      10 Sep  ue5.8/aokigahara-production (last pushed UE commit)
           ├─ [Mac-local: … 5912fc8 + 20 commits on 11 Sep — never pushed]
           └─ 228523f…c519d0c (14) 19 Sep  rebuild/measured-2026-09-19 (owner identity, no AI trailer)
```

**Merge bases:**
- main / ue5.8: `859ab5d`
- ue5.8 / dev: `de637bb`
- ue5.8 / rebuild: `58e42e6`
- main / uhd, main / 4k, and uhd / 4k: `c32be30`

**Consequences of this shape:**
- The dev fixes never reached `main`.
- Both 22 Sep asset branches start from the 10 Sep web checkpoint. They contain no `unreal/` directory and none of the dev fixes.
- The 19 Sep rebuild starts from `58e42e6`, so it discards all Mac-local Unreal work.

**Tool attribution:**
- **Claude Opus 5** (session `01BrEakqy…`): 15 commits on 10 Sep. `de637bb` carries no trailer, and its message is truncated.
- **Claude Fable 5.1**: 17 commits on 22 Sep, from two sessions (`01SzmoGb…` and `01Y3BVdF…`).
- **Owner identity with no AI trailer**: `e12a0f0` (made in the web UI) and 16 commits on 17 and 19 Sep.
- **Codex**: no pushed commit carries a Codex marker. The 17 and 19 Sep owner-identity commits are the candidates *(inferred)*. The rebuild commits add one file per commit, 2–30 s apart, unsigned, which suggests an agent writing files one at a time.

## 2. Dated phase table

| Phase | Date (BST) | Commits / tool | World scope (source file) | Data resolution | Brief / instructions | Delivered | Abandoned or never applied |
|---|---|---|---|---|---|---|---|
| P0a Research dossier (pre-git) | up to 9 Sep | none. Chat research; scripts write to `/mnt/data` *(ChatGPT-style sandbox, inferred)* | Research AOI 138.55–138.72°E × 35.43–35.53°N ≈ **15.4 × 11.1 km ≈ 171 km²**, covered by 2,790 × 250 m cells. Forest ≈ **3,000 ha / 30 km²**. 10 sectors, including a "playable core" and an "outer context shell". (`Aokigahara_Reconstruction_Blueprint.json` → `working_extent`; dossier §4, §9) | No data ingested. Plan: "Check GSI 1 m DEM coverage first"; 3,528 tile URLs "were not fetched" | "geographically faithful free-roam digital recreation"; use EPSG:6676; "not one polygon" rule | 35-page dossier, 152-entry catalogue, evidence grid | Neither the 1 m DEM-first rule nor EPSG:6676 was followed by the build (divergence recorded as "deliberate") |
| P0b Pass 1: the "32 × 30 km terrain package" (pre-git) | 9 Sep | none. Built in `/workspace/sites/aokigahara-field-world`, served at `aokigahara-field-world.akal95.chatgpt.site` *(ChatGPT-hosted, inferred)* | Terrain **32 × 30 km = 960 km²**, 895,734 triangles, including Fuji. Study grid 19.5 × 14 km. Detailed core **2.048 × 2.048 km = 4.19 km²** with 53,999 trees. 467,601 placements on a 35.96 km² mask (bounding box 9.48 × 8.67 km). Detailed trees within 120 m of the start station. (`Aokigahara_3D_README.md`, `*-height.json`, `forest-wide.json`) | Local grid **8 m** (DEM5A z14, ~7.78 m pixel). Study grid 38 × 36 m. Regional grid 62.5 × 58.6 m, of which 75 % is the ~31 m fallback | Not preserved (pass-1 handover lost) | Three-tier terrain, paths, vegetation classes, procedural trees, hosted viewer | Corridor, Forest and World GLBs never reached the repo |
| P0c Pass 2 (pre-git) | 10 Sep | none. Claude.ai "Fable 5.1 Max" (`/home/claude/aoki`) | Terrain unchanged. Detail moved to a **camera-following 120 × 120 m patch at 0.6 m**. Tree LOD rings at 46/62 m, 230 m and 360/460 m. (`Provenance.json` → `productionPass2`) | ±0.6 m lava relief, procedural and not measured | IMG-013 geotag adopted as audit view ("precision uncalibrated") | Ground system, tree library v2, densification, 3 lighting presets | Stopped "diagnosing why distant ground…"; handover zip truncated (211 of 223 files survived) |
| P1 Git checkpoint | 10 Sep 06:32–13:02 | `e12a0f0` (owner), `859ab5d` (Opus 5) | Unchanged (`README.md`, `docs/PROJECT_STATE.md`) | Unchanged | The brief asked for a new repo `aokigahara-free-roam` (refused by policy, `35f1a5b`); "push only to the dev branch" (`c32be30`) | Byte-exact recovery, verifiers | Git LFS; the new repo |
| P2 Web viewer on dev | 10 Sep 13:20–18:11 | 12 commits, Opus 5 | Unchanged | Unchanged | Continue the interrupted pass "rather than redesigning it" | Distant-ground fix, seam fix, broadleaf library, conifer mid-LOD rebuild, Drive corpus, Pages (run #7 succeeded) | Never merged to `main`; the far-impostor fault was left open |
| P3 UE5.8 migration prep | 10 Sep 18:46–21:11 | `6a6c612`, `58e42e6`, Opus 5, running in a Linux container "no macOS, no GPU and no Unreal install" | Brief: **32 × 30 km World Partition** "with AAA near-field density". Advice: "Tier A (0–50 m)", "make the first 20–30 m genuinely excellent". Landscapes planned: local **2.048 km at 2.032 m/quad**, study 19.5 × 14 km, regional 32 × 30 km. Placements imported as a subset by default. (`MIGRATION_BRIEF.md`, `*_heightmap.json`) | 2.032 m/quad is the 8 m grid resampled, so there is no new data | Brief §3 (machine audit), §5 (namespaces), §11 (keep an ISM fallback), step 9 (prove placement before foliage), §48 (priority order); the brief's axis mapping | Proven transform and 12 tests; exporters and importers, never run | "No .uproject exists. No landscape, no import, no render, no performance number." `MACHINE_AUDIT.md` is based on a screenshot |
| P4 UE on the Mac | 10 Sep evening to 11 Sep 14:53 | Local only, up to `5912fc8` + 20 commits | see `../PROJECT_HISTORY.md` (bundle of 20 commits, 11 Sep) | — | — | Never pushed | Superseded on 19 Sep |
| P5 Visual iteration | 12–16 Sep | Not in git | Caller-reported: v7–v20 passes; ground detail masked to the **IMG-013 photo area**. In git, IMG-013 is only a viewpoint at scene (−100.4, −197.6), heading 271.6°, with "precision uncalibrated" | ? | ? | Never pushed | Superseded |
| P6 Survey data, re-deploy attempt | 17 Sep | `225f7c1`, `8e6b4a4` (owner identity) | "The 17 September verification recorded 916 MB of real local blocks" (Yamanashi 2024 LiDAR) | 0.5 m products; MMS ~3 cm | The Netlify build targets the **10 Sep web viewer** (dev) | Helper added at 23:00, removed at 23:05; Pages runs #8–#9 failed | "the deleted `Aokigahara_Real` world" (date unknown, before 19 Sep); `lava_skin_field.py` banned |
| P7 Measured (LiDAR) rebuild | 19 Sep 02:34–02:38 | 14 commits in 4 min 15 s, owner identity, no trailer | Restart from `58e42e6`. **One airborne LAS sheet `08LE9307`** (38 MB), plus MMS (698 MB) and a trajectory file. The sheet is ≈ **400 × 300 m** if the code follows the national 1:500 sheet scheme *(inferred)*. A 0.5 m **"small validation crop"** whose bounds are deliberately unset; "No full-world propagation until that gate passes." (`REBUILD_2026-09-19.md`, `build_real_terrain.py`) | 0.5 m | 7 "Non-negotiable evidence rules" | Coordinate wrapper, LAS rasteriser, axis audit, tests; CI green on fixtures only | No crop, no raster, no UE landscape |
| P8 Asset packs | 22 Sep 07:33–10:48 | Two parallel Fable 5.1 sessions (7 and 10 commits), both based on `main` from 10 Sep | **No spatial extent.** Texture tiles only, 4096² masters (`PROJECT_STATE` §7 on each branch) | UHD 4k tier "interpolated 3–16×"; normal and height maps come from luminance heuristics | Owner photos supplied as chat attachments | UHD: 13 materials × 3 tiers (188.7 MB), opt-in via `?mats=uhd`. 4K: 19 PBR sets, skies, presets, LUTs (343.9 MB) | 4K packs "not loaded by the runtime yet"; "none of the photographs was taken at Aokigahara" |

## 3. Narrative

1. **9–10 Sep, before git.** The research dossier set out to recreate the whole forest faithfully (~30 km² of forest inside a ~171 km² research AOI). Pass 1 built something both larger and smaller than that:
   - a 32 × 30 km terrain, so that Fuji is real relief;
   - real detail only in a 2 km square at 8 m DEM sampling;
   - procedural trees placed by mapped class.

   Pass 2, in a Claude.ai session, narrowed detail further, to a 120 m patch that follows the camera. That session ended mid-diagnosis, and its handover zip was truncated.

2. **10 Sep, Claude Code, one 8-hour session.** The session recovered the archive and fixed web-viewer defects on `dev`. It then wrote the UE5.8 brief and import pipeline in a container that could not run Unreal. It warned that a 32 × 30 km AAA world on a fanless M2 Air is "a workstation-class target" and told the next session to perfect the first 20–30 m first.

3. **11–16 Sep, local only.** The Unreal world existed only on the Mac. Per the caller, by 15–16 Sep the visual passes had narrowed ground detail to the footprint of the single photo IMG-013. None of this was pushed.

4. **17–19 Sep.** The owner obtained measured Yamanashi LiDAR. A world called `Aokigahara_Real` was deleted. A new branch restarted from the 10 Sep pipeline with strict evidence rules. It admits the previous world had been "inventing pahoehoe lobes/ridges" that the 0.5 m LiDAR already measured. It stopped at scripts and tests: no crop was chosen and nothing was rendered.

5. **22 Sep.** Two parallel sessions made texture packs from photographs. They built on the 10 Sep web checkpoint, which still has the distant-ground bug and has no Unreal content. One set is opt-in in the web viewer. The other is not loaded at all and is made from photos not taken at Aokigahara.

## 4. Scope changes

1. **9 Sep, research to build.** Research AOI ~171 km² and forest ~30 km² became a terrain of **960 km²**, with detail in **4.19 km²** and trees on 35.96 km². Why: to have Fuji as real relief, and to put detail where evidence was densest *(inferred link to dossier sector S5)*.
2. **10 Sep, pass 2.** Detail narrowed to a camera-following **120 m** patch and LOD rings out to 230 m.
3. **10 Sep evening, UE brief (`6a6c612`, `58e42e6`).** The brief's 32 × 30 km World Partition became "Tier A (0–50 m)" and "first 20–30 m". The 2.048 km local landscape was to be built first, and the 467,601 trees were imported as a subset by default. Why: the target is a fanless M2 Air with 16 GB.
4. **11 Sep:** see the bundle analysis.
5. **15–16 Sep (caller-reported):** ground detail confined to the IMG-013 photo area.
6. **17–19 Sep (`228523f`–`c519d0c`).** The GSI 8 m world was replaced by one LiDAR sheet (≈0.12 km², *inferred*) and an unspecified 0.5 m crop, with full-world propagation suspended. Why: the old world contained invented lava geometry, and `Aokigahara_Real` had been deleted.
7. **22 Sep.** Work moved from world geometry to texture tiles, with no spatial scope, on the 10 Sep web codebase.

## 5. Changes that did not reach the rendered world, or were measured wrongly

**Did not take effect, or silently fell back:**
- **`859ab5d` / `dc33485`:** the distant-ground guard "never fired". Every square metre beyond 120 m shaded as trail cinder. The fix exists only on dev.
- **`2245a99` / `312d2ec` lineage:** both 22 Sep branches still carry that bug; I verified their `app.js` has no `buildBaseWeights`. So the `?mats=uhd` ground would reach only the 120 m patch *(inferred from code, not rendered)*.
- **`dc33485`:** the `#lighting` control was "presented to the user as a live control that did nothing".
- **`7e73974`:** "a 38 % albedo step … a seam that follows the player".
- **`341a173`:** the download offered "advice that could never succeed, because the file was never there".
- **`0e156a5`:** broadleaf trees were untextured, and the runtime "fell back to the low mesh at every distance".
- **`a55cab6`:** crown cards were 1/6 of crown width, leaving "bare poles". `MIGRATION_BRIEF`: "This bug shipped twice in this project".
- **`c32be30`:** "a deployment-branch rule for dev/generational-visual-upgrade did not take". Pages runs #2–#5 and #8–#9 failed.
- **`225f7c1` / `8e6b4a4`:** the Netlify helper was removed after 5 minutes.
- **`58e42e6`:** caught before any import, so nothing wrong was built:
  - the brief's axis mapping "would have built a mirrored world";
  - the 16-bit PNGs had the wrong byte order;
  - the size search picked "37x37 components of 7 quads".
- **`58e42e6`:** by design, the landscape importer "falls back to printing", and the placement importer uses "deliberately a subset". The 2.032 m/quad resolution is resampled 8 m data.
- **`6a6c612` / `58e42e6`:** no `.uproject`, map, UE render or frame rate was ever pushed. `.gitignore` says they "ARE tracked".
- **`228523f`:** `lava_skin_field.py` was "inventing pahoehoe lobes/ridges". The doc refers to "the deleted Aokigahara_Real world" and warns "Do not `>> 8` it", which implies an earlier colour bug *(inferred)*.
- **`a01c375` → `f66dee4`:** wrong LAS class semantics, replaced 2 minutes later.
- **`aa8088f` / `c519d0c`:** CI is green on fixtures only and never touched real LAS data.
- **`f247fb6`:** the procedural tiles are "not periodic" and are "not fixed here".
- **`62fc234` / `2245a99`:** "The default remains `materials_v2`". Four pack types are "asset-only". The "true4K" photo is "visibly an upscale".
- **`8dbc389`–`312d2ec`:** the packs are "not loaded by the runtime yet".

**Measured wrongly, or never measured:**
- **`0e156a5` (PROJECT_STATE §4.2.5):** "1,684 triangles and 'fifty-three times'" came from "a runtime probe that double-counted". A load-time gain "was warm-up noise".
- **`6a6c612`:** the machine audit "came from a screenshot". The GPU core count is unknown.
- **`58e42e6`:** the control points prove the transform only. Independent controls "disagree by up to 536 m at Omuro Cave".
- **README from `859ab5d` on:** "No frame rate has been measured on any target device".
- **`PROJECT_STATE` §1.1:** calls the dossier "25-page"; the PDF has 35 pages.
- **`de637bb`:** the commit message is cut off mid-sentence.

## 6. Effort

| Day (BST) | Pushed commits | Phases |
|---|---|---|
| 10 Sep | 16 (06:32–21:11; 15 of them by Claude in 8 h 09 min) | P1–P3 |
| 11–16 Sep | 0 pushed (≥21 local commits on 11 Sep; v7–v20 passes on 15–16 Sep per the caller) | P4–P5 |
| 17 Sep | 2 | P6 |
| 19 Sep | 14 (in 4 min 15 s) | P7 |
| 22 Sep | 17 (two sessions overlapping 08:45–09:55) | P8 |

**Gaps between pushes:**
- 169.8 h (7.1 days, 10 Sep 21:11 → 17 Sep 23:00)
- 27.5 h (17 Sep → 19 Sep)
- 76.9 h (19 Sep → 22 Sep)

**Hand-written lines by phase:**
- P2: code +1,344, docs +696
- P3: code +1,262, docs +323
- P7: code +686, docs +126
- P8a: code +754, plus 262 binary files (188.7 MB)
- P8b: code +1,438, plus 481,800 lines of generated data and 168 binary files (343.9 MB)

P1 was mostly recovered and vendored files: 250.9 MB and 95,926 vendored three.js lines. About 63 % of all bytes pushed (532.6 of 846.5 MB) went into texture packs that the Unreal world never received.

## 7. Root causes the history supports

1. **Ambition, machine and data did not match, which forced repeated curtailment.**
   - The brief wanted a 32 × 30 km AAA World Partition world.
   - The target machine is a fanless M2 Air with 16 GB (`6a6c612` calls this "a workstation-class target").
   - The data is an 8 m DEM core and a 62.5 m regional grid.

   Real detail only ever existed in a 2 km core. Each later phase shrank it again: 0–50 m, then one photo's area, then one LiDAR-sheet crop.

2. **The rendered Unreal world was never in the recorded feedback loop.**
   - The brief and importers were written without Unreal.
   - The machine audit came from a screenshot.
   - Every pushed render or metric is of the web viewer under software GL.
   - No UE project, frame or FPS figure exists in any branch.
   - The importers fall back to printing settings or to a subset.

3. **The lineage is fragmented and context was lost.**
   - Seven branches and zero merges.
   - The dev fixes are stranded on dev.
   - The 22 Sep sessions built on the 10 Sep web checkpoint.
   - The 11–16 Sep Mac work was never pushed, and a world was deleted.
   - The 19 Sep restart went back to `58e42e6`.
   - The owner's brief is not stored anywhere in git.

4. **Detail was invented or interpolated rather than measured, and it reached the screen through opt-in or fallback paths.**
   - Procedural lava relief, and `lava_skin_field.py` inventing lobes.
   - 2.03 m/quad produced from 8 m data.
   - Textures upsampled 3–16×, and packs made from non-Aokigahara photos.
   - A guard that never fired, a dead control, and 1/6-size crown cards that shipped twice.

   So prompt changes moved the parameters of invented content, and defaults and fallbacks hid their effect. That matches "stayed the same or got worse".

Machine-readable version: `history_timeline.json`, which lists every commit, branch membership, statistics, phases, scope changes, the non-effect list and the root causes. The generators are `commit_stats.py` and `build_timeline_json.py`.
