# Engine selection: decision record

Date: 23 September 2026. Status: recommendation. The plan's first step (milestone 0) is a cheap test on the owner's
Mac that can still overturn it. Branch of record: `claude/aokigahara-engine-selection-tqyqx6`. The owner has
excluded Unreal Engine 5, so it was not scored. The evidence behind every section is in `docs/engine_selection/`:
research reports, fact-checks, prototype reports, judge verdicts and an independent critique of the draft. A key to
that folder is in `docs/engine_selection/RESUME.md`.

## 1. Decision

Build the free-roam world as a **Godot 4 native macOS app**: Forward+ renderer on Metal, with MetalFX Temporal
upscaling. Feed it from an **engine-agnostic Python pipeline** that turns the Yamanashi 0.5 m LiDAR into terrain, tree
positions detected from the canopy height model (CHM), and precomputed canopy light maps.

**Runner-up: three.js r186 WebGPU in Chrome**, fed by the same pipeline. It takes over if a shareable web link becomes
a requirement, or if Godot proves unstable on this Mac (section 10).

All three judging lenses chose this winner and this runner-up: fidelity-first, waste-first, and risk and longevity.

**UE5.8 is not needed**, but it is not dispensable for free, so the claim should be precise. The valued look in frames
g–j comes mostly from four things:

- sunflecks through the canopy;
- deep sky-occluded shade;
- a low exposure key;
- warm sunlit patches.

Godot has all the real-time parts, and LiDAR-baked canopy maps can stand in for Lumen's far-field sky occlusion.

**What has been shown so far.** A Godot render met 3 of the 4 primary lighting targets from one viewpoint, rendered
headless in the cloud with no Mac. It used the repository's 8 m terrain, its procedural tree placements, and a canopy
map splatted from those crowns (not yet from LiDAR).

**What has not been shown:**

- warm highlights;
- bright sky gaps;
- light shafts;
- a LiDAR-derived canopy map;
- any frame time on an M2.

By eye the render is not yet at parity.

**What is portable and what is not.** The recommendation makes the data portable, not the runtime.

- **Engine-agnostic:** the pipeline, the rasters and bakes, the stem list, glTF/KTX2 assets, the cameras and the
  lighting gate.
- **Godot-specific, rewritten on a switch:** the shaders (shared ShaderMaterial templates), the fog volumes, the
  streaming, the character controller and the settings. The risk judge estimates that rewrite at several agent
  sessions.

## 2. What the UE5.8 attempt achieved, and why it was so costly

**What it achieved.** Frames g–j in `renders/ue58_baseline/` show the valued result: dappled sun, a dark sky-occluded
understorey, bright sky gaps, haze and warm bounce light. The engine-specific parts were:

- Lumen global illumination (GI);
- Virtual Shadow Maps;
- Nanite;
- fog and auto-exposure that are on by default.

The slope-driven moss is a shader rule and is portable, as are the rocks, the terrain and the tree data.

**Where it fell short.** Most flaws were content problems, not engine problems, and any engine has to fix them:

- a flat, pale, textureless sky;
- far canopy as dark, flat masses;
- textures stretched across 1 m heightmap steps;
- hard-edged material blotches, because layers were not height-blended;
- stippled masked materials with no temporal resolve;
- noisy, stretched bark;
- a sparse understorey and no litter.

**Why it cost so much:**

- **Nothing recoverable.** The world existed only as binary `.uasset` files on the Mac. Branch
  `ue5.8/aokigahara-production` holds 12 script and JSON files and no `.uproject`, so the corrupted project could not
  be recovered.
- **Agents worked blind.** They could not see the viewport, so the owner had to supply phone photos.
- **Disk.** UE plus its derived-data cache filled a disk that is very probably 256 GB.

## 3. The honest ceiling

**Hardware.** Model MC7X4 is very probably the 16 GB / 256 GB M2 Air with an 8-core GPU. The only source is a retailer
listing [21], so confirm it with the milestone 0 audit.

- **Compute:** about 2.9 TFLOPS FP32 and 100 GB/s of shared memory bandwidth [19].
- **GPU family Apple8:** MetalFX temporal upscaling works. There is no hardware ray tracing and no MetalFX denoiser;
  both start with M3 [18].
- **GPU working set:** about 10.7 GiB [20].
- **Cooling:** fanless. How much it throttles under load is unmeasured.

**Target, not yet measured on any M2:**

- a warm, locked 30 fps;
- output at 1470×956, the Air's default scaled resolution, from about 985×640 internal via MetalFX Temporal at 0.67
  scale;
- a fixed or slow-moving sun.

Headless gate renders stay at 1280×800 so they can be compared with the UE frames.

**What the judges estimate within that target:**

- **Lighting:** about 75–90% of the frames g–j look within 150–200 m of the camera. This is judgement, not a
  measurement.
- **Overall:** "high-end indie / AA", roughly level with UE5.8.

**Likely better than UE5.8, because its flaws there were content:**

- a physical sky with proper exposure;
- far canopy shaded from the CHM and tinted from the orthophoto;
- measured terrain (0.5 m source, 1 m in the engine, 0.5 m for bakes);
- height-blended materials;
- no visible stipple;
- a dense understorey.

**Likely short of UE5.8:**

- off-screen and multi-bounce light;
- sharp canopy shadows hundreds of metres away;
- Nanite-level geometric density;
- GI that ignores wind: moving crowns do not update occlusion;
- no time of day without re-baking.

**Not photoreal.** The trees cap the fidelity. No species-accurate scans of *Tsuga sieboldii* or *Chamaecyparis* were
found; a CC0 lead and commercial hinoki models are unverified.

**Going beyond UE5.8 would need, in order of value:**

1. Species-accurate trees, from the owner's own photogrammetry or verified scans.
2. A fan-cooled M3-or-later Mac or an RTX PC, together with a newer GI once it is proven on that class of hardware.
   Candidates: Godot HDDAGI or its screen-probe GI [5], Flax DDGI, Unity Surface Cache GI.
3. For stills and fly-throughs only: Blender Cycles on the same data, which can exceed UE5.8 today.

## 4. Lighting parity

### What produced the look in UE5.8

- **Lumen:** sky occlusion, which gives the dark interior and bright gaps, and warm bounce light off rocks and ferns.
- **Virtual Shadow Maps:** sharp sunflecks near the camera and soft canopy shade far away.
- **Volumetric fog:** haze and light shafts.
- **Auto-exposure and filmic tonemapping:** a low key and a wide range without clipping.

### The target, measured

`tools/lighting_stats.py` on frames g–j [1]. The primary targets are the metrics that separate the valued frames from
the flatter UE5.8 frames and from the old Three.js viewer. The rest are checks.

| Metric | Target range | Role |
|---|---|---|
| Sunfleck fraction | 0.07–0.16 | primary |
| Exposure key (log-average luminance) | 0.003–0.008 | primary |
| Black fraction | 0.17–0.43 | primary |
| Highlight B/R (warm sunlit patches) | 0.29–0.42 | primary |
| Sky peak (sky gaps not greyed) | 170 or more | must hold |
| Clipped fraction | under 0.005 | must hold |
| Shade B/R | 0.60–1.28 | sanity check |
| Dynamic range | 8.5–10.2 stops | reported |

Two notes on the metrics:

- **A withdrawn metric.** The earlier "cool shadows" metric (`shadow_blue_ratio`) was JPEG noise and has been
  withdrawn. Some research reports under `docs/engine_selection/wip/` still quote it; ignore it there.
- **The sky flaw is judged by eye.** No metric here detects UE5.8's flat, pale sky, so it is checked on the contact
  sheet.

### Prototype evidence

Both prototypes used the repository's GSI 8 m terrain, the procedural tree library, the repository's placements
(infilled to close the canopy) and the moss materials. Each rendered at 1280×800, headless, in a cloud container with
no GPU [2]. Each engine used one or two cameras, not composed like g–j, so these numbers compare lighting character,
not views. **Bold** means within the primary target range.

| Render (under `docs/engine_selection/prototypes/`) | Exposure key | Sunfleck | Black | Highlight B/R | Shade B/R | Sky peak | Primary met |
|---|---|---|---|---|---|---|---|
| Godot, SDFGI (`godot/renders/godot_sdfgi.jpg`) | **0.0056** | **0.157** | **0.27** | 0.70 | 0.74 | 118 | 3/4 |
| Godot, no SDFGI, canopy map (`godot/renders/godot_canopy.jpg`) | **0.0064** | **0.124** | **0.18** | 0.70 | 0.82 | 109 | 3/4 |
| Godot, SDFGI + canopy map, stronger sun (`godot/renders/godot_sdfgi_canopy_sun6.jpg`) | **0.0078** | 0.163 | **0.20** | 0.66 | 0.68 | 132 | 2/4 |
| Godot, neither (`godot/renders/godot_nosdfgi.jpg`) | 0.0106 | **0.083** | 0.05 | 0.70 | 0.92 | 124 | 1/4 |
| three.js, plain + canopy map (`webgpu/renders/t4_off_tuned.jpg`) | **0.0036** | 0.344 | 0.51 | 0.48 | 2.90 | 248 | 1/4 |
| three.js, plain + canopy map, darker (`webgpu/renders/t1_off.jpg`) | 0.0011 | 0.349 | 0.69 | **0.37** | 1.00 | 235 | 1/4 |
| three.js, sparse canopy (`webgpu/renders/t0_off.jpg`) | 0.0315 | **0.106** | 0.13 | 0.55 | 0.77 | 235 | 1/4 |
| three.js, SSGI (broken) (`webgpu/renders/t5_ssgi_tuned_BROKEN.jpg`) | 0.0986 | 0.001 | 0.00 | 0.52 | 0.35 | 255 | 0/4 |

What the table shows:

- **A canopy term does most of the work.** Either SDFGI or the canopy map alone reaches 3 of 4. Without either, the
  render reaches 1 of 4. The judges regarded SDFGI as load-bearing; the prototype suggests the canopy term matters at
  least as much. One camera cannot settle which, so milestone 1a runs a three-way comparison.
- **Stacking both hurts.** The SDFGI + canopy render scores 2 of 4, worse than either alone. The likely cause is
  that Godot's AO output also scales SDFGI's indirect light, so sky occlusion is counted twice. Hence the blend rule
  below.
- **Warm highlights are a tuning problem, not a GI problem.** No Godot render meets the target, and its value is
  0.66–0.70 whatever the GI mode, so sun colour and moss albedo set it. The crushed three.js `t1` does meet it.
- **Godot's sky gaps are dull.** Its sky peak is 109–132 against 176–243 in g–j. This matches what the eye sees: the
  gaps read as grey-blue. Sky energy and exposure need tuning.
- **three.js fails the shade check badly** (2.90), with a blue cast in the shade. Its SSGI path broke the shadows
  entirely, cause not found.
- **By eye, parity has not been reached by either engine.** Next to frames g and i, the Godot frames look grey-green
  and flat. The three.js `t4` dapples crisply but has too many sunflecks and crushed, blue-cast shade.

### Recipe on the recommended path (most important first)

1. **Sun shadows.**
   - Start with 4-split PSSM to 150–200 m, blended splits, a 4096 atlas and angular distance 0 (PCF).
   - Try 0.5° angular distance only if the benchmark allows it: in Godot that turns on PCSS, which is expensive [8].
   - Foliage should be alpha-scissor casters, with impostor casters in the far splits.
   - Godot 4.8's directional contact shadows cost about 0.04 ms on the pull request's RTX 5090. Their cost on the M2
     is unmeasured.
2. **Canopy maps from the LiDAR CHM** (DSM2 minus DEM), baked in the cloud with a numpy heightfield march or rvt-py's
   `vis` functions [24]:
   - a sky-view factor for the ground, plus a coarse 3D volume for trunks and foliage;
   - sun transmittance;
   - a gap mask for placing shafts.

   Deliver them as global shader uniforms read by shared ShaderMaterial templates, one per material family.
   StandardMaterial3D cannot read global uniforms. Fog reads them through custom FogVolume shaders, because Godot's fog
   GI-inject only reads VoxelGI and SDFGI [9].
3. **Blend rule.** Choose one after the milestone 1a three-way comparison:
   - **(a)** SDFGI handles near-field sky occlusion and bounce within its last cascade, about 200 m. The CHM
     sky-view factor fades in beyond that, and CHM sun transmittance applies beyond the shadow distance.
   - **(b)** SDFGI off. The CHM sky-view factor scales ambient light on every material, and SSIL supplies short-range
     bounce.

   Never apply both occlusion terms at full strength in the same place.
4. **Sky ambient** from PhysicalSkyMaterial, scaled by the sky-view factor where rule (b) or the far field applies.
   Tune the sky energy until sky peak reaches 170 or more.
5. **SDFGI** at half resolution, with occlusion and sky light on. It needs 4.8 on Metal [4]. Its own documentation says
   integrated GPUs need tuning [7]. Planning budget, by judgement: drop it if it costs more than about 5 ms on the M2.
6. **SSAO, plus SSIL at half resolution.**
7. **Volumetric fog** with a shadowed sun and temporal reprojection, plus aerial fog. Shafts drift during camera motion
   (issue #120163 [10]); check this in the walk test.
8. **AgX tonemapping and auto-exposure.** A warmer sun and lighter moss albedo are needed for the warm-highlight target.
9. **Foliage:** fern and needle backlight, bent normals, and alpha-scissor or alpha-hash with a temporal resolve.
   Alpha-to-coverage needs MSAA, which MetalFX Temporal excludes.
10. **MetalFX Temporal** at 0.67 scale, with a 30 fps cap. On Metal, a fixed `max_fps` cap raised process time sharply
    (#114258 [12]), so milestone 0 compares it with a vsync-based cap.

### How it will be measured

1. **Cameras.** `harness/cams_ue58.json` holds four cameras composed to the g–j rules plus two regression cameras (a
   trail and a road edge). The composition rules:
   - eye height 1.6–1.7 m;
   - pitch −5° to +5°;
   - 90° horizontal field of view;
   - sun elevation 25–35°, side- or back-lit;
   - a sky fraction within 0.014–0.075.
2. **Renders.** Every render is a 1280×800 PNG.
3. **Gate.** On the four matched cameras, all four primary targets must be met, and so must both must-hold checks.
   Shade B/R and dynamic range are reported. The two regression cameras must not get worse.
4. **Review.** Agents read the JSON first. The owner sees one contact sheet per milestone, each render beside its
   matching UE frame, and judges the sky and any stipple by eye.
5. **Bake check.** Blender Cycles renders the same tile and cameras. In shade, the sky-view factor should agree within
   about 0.05.
6. **Metal check.** The same cameras are captured on the Mac under Metal. Lavapipe, the software renderer in the
   cloud, checks appearance only.

## 5. Options compared

Each cell is the mean of the three judges' scores out of 10; higher is better. For disk and cost, a higher score means
less. Weighted is the mean of each judge's own weighted total. The weights were:

- **Fidelity-first:** lighting 0.30, fidelity 0.25, Mac feasibility 0.20, agent efficiency 0.10, 0.05 each for the
  rest.
- **Waste-first:** agent efficiency 0.25, lighting 0.20, storage 0.15, first result 0.15, fidelity 0.10, cost 0.10,
  Mac feasibility 0.05.
- **Risk and longevity:** lighting, Mac feasibility and agent efficiency 0.20 each, fidelity 0.15, first result 0.10,
  cost 0.10, storage 0.05.

| Path | Lighting | Fidelity | Mac feasibility | Disk | Agent efficiency | Cost | First result | Weighted |
|---|---|---|---|---|---|---|---|---|
| **P1 Godot 4 (Metal)** | **7.0** | 6.2 | **6.3** | 8.0 | **8.0** | 10 | **8.0** | **7.4** |
| P2 three.js r186 WebGPU | 5.2 | 5.2 | 5.7 | **9.0** | 7.0 | 10 | 7.0 | 6.5 |
| P3 Unity 6 URP | 4.7 | 6.2 | 4.7 | 3.0 | 3.0 | 7.3 | 3.7 | 4.6 |
| P4 Bevy 0.19 | 4.0 | 4.3 | 6.0 | 7.0 | 6.3 | 10 | 3.3 | 5.5 |
| P4 Flax 1.12 (two judges) | 5.5 | 5.8 | 4.0 | 5.5 | 3.0 | 8.5 | 3.0 | 4.9 |
| P5 Capture hybrid | 5.0 | 6.3 | 4.7 | 2.7 | 3.0 | 2.7 | 1.3 | 4.1 |
| P6 Cycles (not free-roam, ineligible) | 8.7 | 7.2 | 2.3 | 7.7 | 6.3 | 10 | 6.7 | 6.8 |

On lighting alone, the owner's primary criterion, the order among eligible paths is P1 7.0, then Flax 5.5 (two
judges, never measured on an M2), then P2 5.2, P5 5.0, P3 4.7 and P4 Bevy 4.0. P1 wins either way.

**P1 Godot** has every lighting part built in. It is the only path with measured evidence of the g–j lighting
character on real project data. It runs natively on Metal with MetalFX: the only measured M2 Air figure is 19% less GPU
time than FSR2 [6]. Its weaknesses:

- SDFGI's bounce light on Metal needs 4.8 [4];
- SDFGI's cost on this GPU is unmeasured [7];
- an open Metal freeze reproduces on the M2 Air and on M1 Max and M4 machines [11].

Milestone 0 tests all three before any further investment.

**P2 three.js** has the smallest footprint, a shareable URL and reuses the existing viewer. It lost for four reasons:

- its SSGI pipeline brightened frames 25–30× and removed all shadows, cause not found;
- it has no auto-exposure; Babylon.js has it [16] but no other lighting advantage;
- its LightProbeGrid cannot save, load or stream [15];
- the browser has no MetalFX, and Safari's WebGPU needs macOS 26 or later [17].

**P3 Unity** has baked Adaptive Probe Volume sky occlusion, the nearest ready-made match to Lumen's. It lost because:

- that bake treats leaves as opaque;
- URP lacks volumetric fog, auto-exposure and a physical sky [25];
- the editor (about 8.5 GB) and its Library cache (tens of GB) would repeat the UE5.8 disk pattern.

**P4 Bevy** is text-only and compiles in the cloud. It lost because:

- it has no real-time GI on the M2: Solari needs ray queries, which are impractical without RT hardware, so only baked
  irradiance volumes are available;
- it has no virtual geometry, because meshlets need Apple9 (M3 or later) [26];
- it has no terrain system and no editor, and a breaking release lands every 4–5 months.

**Flax** has software DDGI, the nearest thing to Lumen outside UE [27]. It lost because it runs only through MoltenVK,
has documented foliage artefacts, and has never been measured on an M2.

**P5 Capture** looks photographic inside the captured spots but covers under 1% of the plot. Splats keep the light
of the day they were captured and ignore scene exposure and shadows [28]. It stays an optional add-on for later.

**P6 Cycles** is not free-roam. Use it as the calibration reference and bake tool, through the bpy wheel [24].

## 6. Why the recommended path is less wasteful

### Disk

| Where | Item | Size |
|---|---|---|
| Mac internal | Godot 4.8-dev6 and 4.7.2 editors | 184.6 + 170.6 MB [3][32] |
| Mac internal | macOS's own Metal pipeline cache (not movable) | a few hundred MB (estimate) |
| External SSD, or internal if none | The Godot project and git working tree, including `.godot/` import and shader caches | 2–6 GB (estimate) |
| External SSD, or internal if none | Engine-ready world: 1 m terrain, bakes, instances, textures, impostors | 2–5 GB (estimate) |
| External SSD, or internal if none | Raw LiDAR: 916 MB now, plus an estimated 8–10 GB of airborne LAS for 25 km² (unverified) | about 10 GB |
| Cloud (reinstalled each session) | Godot 78 MB, lavapipe 96 MB, bpy 402 MB, GIS and R environments 1–2 GB | about 2–3 GB |

**Total on the Mac: about 13–20 GB, of which about 10 GB is raw LiDAR.** Godot keeps its caches inside the project
folder, so wherever the project lives, its caches live too. With an SSD, the internal disk carries under 1 GB. Without
one, keep about 20 GB free. Run `du -sh .godot ~/Library/Caches` once a month. UE5.8 filled the internal disk.

### Who does what

- **Cloud agents:** the pipeline, the code, the scenes, the bakes, the trees, and headless rendering and scoring.
- **The owner:** one scripted Mac benchmark per milestone, approval of one contact sheet, licence checks, and any
  downloads the cloud cannot reach.

### Headless self-verification has been demonstrated [2]

- **Godot 4.7.2**, Forward+ on lavapipe under `xvfb-run`: SDFGI, SSAO, SSIL, volumetric fog, PSSM, AgX and
  auto-exposure all ran without errors, at about 7 s per frame and 3–4 minutes per settled still. The project is
  three text files in `docs/engine_selection/prototypes/godot/proj/`.
- **three.js** on SwiftShader WebGPU: about 20 s per frame. The page and renders are in
  `docs/engine_selection/prototypes/webgpu/`.

### Usage budget and stop rules

The owner's defining constraint is agent usage, so every milestone in section 8 has a session budget and a stop
rule. A session is one scoped, single-agent Claude Code session with plan mode first. When a budget runs out with the
gate unmet, the agent stops and reports to the owner rather than continuing to tune.

Three further rules:

- **Rendering:** at most 4 gate cameras per iteration and 3 iterations per session. Never run parameter sweeps.
- **Images:** read the metrics JSON before opening any image. Each 1280×800 image costs about 1.3k tokens on every
  later turn [22].
- **Session shape:** keep multi-agent runs for one-off research; they cost about 15× the tokens of a chat [22]. This
  decision came from such a run of about 25 agents across research, fact-checks, prototypes and judges. It is not
  the pattern for building.

### Storage and publication

Text lives in git. Before any binary is published, bear in mind that **this repository is public**, with GitHub Pages
on, so a release asset is public redistribution.

- **Survey data:** publish derived rasters only after milestone 0 confirms the Yamanashi and Forestry Agency licences.
  Keep raw LAS local until then.
- **Purchased assets** (for example Fab or Megascans scans) never go into this repository or its releases.
- **Git LFS:** not used, because the cloud container cannot reach it [23].

## 7. What carries over

**On `main`:**

- `tools/audit_render.mjs`, `harness/cams*.json` and `harness/sheet.py`: camera and contact-sheet tooling.
- `viewer/assets/terrain/`: the GSI DEM5A 8 m height grids with their JSON, the GSJ Jōgan lava mask
  (`*-jogan.u8`), the Ministry of the Environment vegetation (`*-landcover.u8`), and OSM paths and landmarks
  (`*-context.json`, ODbL).
- `data/forest-wide.f32` (467,601 placements) and `viewer/assets/forest-instances.f32`. Both are placeholders until
  replaced by stems detected from the CHM.
- `viewer/assets/tree-library-v2.glb` and `viewer/assets/materials_v2/`: placeholders. Both prototypes and milestone
  1a use them.
- `docs/research/`: the research dossier.

**On branch `claude/aokigahara-engine-selection-tqyqx6`** (this PR; merge before milestone 1):

- `renders/ue58_baseline/` and `tools/lighting_stats.py`: the target and the gate.
- `docs/engine_selection/`: the research, the prototypes (including the Godot project) and the index.

**On other branches:**

- **`rebuild/measured-2026-09-19`**, under `unreal/AokigaharaUE/`, holds engine-agnostic Python that becomes the
  start of the pipeline:
  - `Scripts/jprcs8.py`, `real_terrain_lib.py`, `build_real_terrain.py`, `audit_measured_axes.py` and
    `test_measured_rebuild.py`, with their CI workflow;
  - `Docs/REBUILD_2026-09-19.md`, whose evidence rules and validation gate still apply.
- **`ue5.8/aokigahara-production`:** `unreal/AokigaharaUE/Scripts/aokigahara_geo.py` and `test_geo.py`, the verified
  coordinate transform.
- **`claude/aokigahara-uhd-assets-5l10c2`:** the photo-derived `materials_uhd` packs. Use them as colour targets
  only; they were upscaled from small crops.
- **`claude/4k-asset-packs-photos-sy83u7`:** the source photographs.

**On the owner's Mac**, in `/Users/Shared/Aokigahara-survey-2026-09-17` (916 MB):

- `08LE9307.zip`: the airborne LAS for one sheet;
- `mms_08LE9307.zip`: MMS LiDAR with RGB for the same sheet, including a road;
- `mmstrj.zip`: the MMS trajectory;
- `fr_mesh20m_08le3_2025.7z`: the 20 m forest register;
- `dem_9325.zip`, `ortho_9325.zip`, `inyou_9325.zip` and `survey_report.md`.

The UE project itself is lost. Any Megascans claimed under a UE plan may be licensed for UE only.

## 8. Phased plan

Session budgets are planning estimates, not measurements. Each milestone ends in a decision, not a slide into the next.

### Milestone 0: set-up and the Mac probe

Budget: 1 agent session, plus about 2 hours of the owner's time.

**The agent, in the cloud:**

1. **Turn the Godot prototype into a Mac probe.**
   - Make the repository path a `--repo=` argument.
   - Set the macOS driver to Metal and the scaling mode to MetalFX Temporal.
   - Add a `--bench` mode: a scripted 10-minute camera path. It logs process time, GPU frame time, video memory
     (`RENDER_VIDEO_MEM_USED`) and physics time to JSON, and compares `Engine.max_fps = 30` against a vsync-based cap.
2. **Pin one Godot build for both cloud and Mac:** 4.8-dev6 (Linux 78.1 MB, macOS 184.6 MB [32]). Record it in
   `godot/VERSION`, and re-render the gate cameras whenever it changes. Keep 4.7.2 as the stable and MoltenVK
   fallback.
3. **Add `tools/cloud_setup.sh`,** run by the environment's setup script or a SessionStart hook, because every cloud
   session starts from a fresh machine. It installs lavapipe and the pinned Godot, plus two separate environments:
   - bpy in its own Python 3.13 virtualenv;
   - a pipeline environment from conda-forge (gdal, rasterio, pdal, pyproj, laspy, lidR and lasR). If rvt-py is used,
     install it with `--no-deps`, because its declared dependency on source-only `gdal` fails to build.

   Commit the lockfiles.
4. **Add the gate:** `harness/cams_ue58.json` following section 4's composition rules, a gate script and a
   contact-sheet script.
5. **Add `ATTRIBUTION.md`:** CC BY 4.0 for the Yamanashi and Forestry Agency data once confirmed, and ODbL for the OSM
   layers.
6. **Propose the 5 × 5 km plot.** State its bounds in EPSG:6676 (xmin, ymin, xmax, ymax) and list the 1:500 sheet IDs
   that cover it.

**The owner, on the Mac:**

1. Run `system_profiler SPDisplaysDataType SPHardwareDataType; sw_vers; df -h /` and paste the output.
2. Run the probe four ways:
   - 4.8-dev6 on Metal;
   - 4.7.2 on Metal, to see whether the SDFGI bounce bug reproduces on an M2;
   - 4.7.2 on MoltenVK;
   - the best of the three again with SDFGI off.

   Each run is about 12 minutes.
3. Confirm the licence text on the geospatial.jp dataset page, and the Forestry Agency terms for the 20 m register,
   before anything is uploaded publicly.
4. Approve or adjust the plot bounds.
5. Read the dataset's resource list through its CKAN API [31] and pass it to the agent. The agent then tests one sheet
   URL from the cloud: only a 200 there means the cloud can fetch the sheets itself.
6. Optionally, attach an external APFS SSD and move the survey folder onto it.

**Decision point.** Apply the section 10 flip conditions to the probe results before any pipeline work starts.

### Milestone 1a: lighting and walking on existing assets

Budget: 3 sessions. Stop rule: if the gate is not met after 3 sessions, stop and report.

- Use the repository's 8 m terrain and tree library on the plot's first tile, so no asset or data work is mixed into
  the lighting result.
- Apply the section 4 recipe.
- Run the three-way comparison on the gate cameras (SDFGI only, CHM term only, blended per rule (a)) and fix the blend
  rule.
- Add walking:
  - a CharacterBody3D controller;
  - a HeightMapShape3D terrain collider;
  - capsule colliders for trunks within about 50 m, generated from the placement list;
  - convex shapes for large rocks.
- Target: the owner walks the tile on the Mac within about a week of starting, subject to their availability.

Acceptance:

- the lighting gate passes on the four matched cameras;
- a scripted walk over rough ground completes without falling through or snagging;
- the bench holds at least 95% of frames under 33.3 ms, warm, at the section 3 resolution pair;
- there is no visible stipple after the temporal resolve.

### Milestone 1b: measured data on the sheet already held

Budget: 4 sessions, with the same stop rule.

1. **Run the REBUILD gate first:** `test_geo.py`, `test_measured_rebuild.py` and `audit_measured_axes.py` against the
   MMS trajectory, plus one independent GSI control. Then compare the raw-cell reconstruction against the provider's
   0.5 m DEM and DSMs.
2. **Build the measured products** for sheet 08LE9307: DEM, DSM2 and CHM, with buildings masked using OSM. Process one
   sheet at a time: unzip, rasterise, delete.
3. **Detect stems** with lasR local maxima and Dalponte crowns, calibrated against the 20 m register.
4. **Bake the canopy maps from the real CHM** and swap them in for the splatted ones.

Acceptance:

- terrain RMSE of at most 0.15 m against the provider's 0.5 m DEM, with gaps counted and any interpolation named;
- at least 80% of placed dominant stems within 1 m of a CHM local maximum, with height within 10%;
- the lighting gate still passes;
- GPU memory is taken from the bench JSON.

### Milestone 1c: species trees

Budget: 2 sessions per species, *Tsuga* then *Chamaecyparis*.

- Build each tree with a custom bpy space-colonisation or L-system script, with needle cards and bark from photographs.
  An alternative, with compatibility unverified, is the archived Sapling add-on from the `blender/blender-addons`
  GitHub mirror; Blender's extension sites are blocked from the cloud.
- Produce LOD0, LOD1 and an opaque-core octahedral impostor.
- Accept each species against reference photographs before placing it at scale.

### Milestone 2: the full 5 × 5 km plot

Budget: 6–8 sessions.

- **Data:** fetch or upload the covering sheets and run the milestone 1b pipeline sheet by sheet. After the licence
  check, publish the derived rasters (DEM, DSM2, CHM and bakes, about 1 GB) as versioned release assets, so later
  sessions do not reprocess raw LAS.
- **Streaming:** 250–500 m tiles loaded with `ResourceLoader.load_threaded_request` in a ring of about 1–1.5 km, with
  per-tile terrain colliders and trunk colliders streamed alongside.
- **Terrain:** a 1 m geomorphing clipmap. Terrain3D is optional, because its Godot 4.7/4.8 support exists only on its
  main branch [14].
- **Trees, by distance:**
  - full detail to 30–40 m;
  - mid LOD to about 150 m;
  - impostors to 1–2 km;
  - beyond that, a CHM canopy heightfield tinted from the orthophoto.
- **Shadows:** far cascades cached, with baked transmittance beyond the shadow distance.

The owner benchmarks a scripted flight and walk.

### Milestone 3 (optional)

- extra sun angles;
- packaging, with a minimum macOS of 14 because of issue #123266 [13];
- a capture trip.

## 9. Must-do regardless of engine

- **Coordinates.** Build in EPSG:6676 with a local origin. Reproject the legacy AEQD assets rather than shifting them:
  0.092° of grid convergence gives up to 5.7 m of error at the corners [29].
- **Resolution.** Use 1 m terrain in the engine and 0.5 m for bakes. Terrain3D-style 32-bit maps at 0.5 m would take
  about 1.2 GB [14].
- **Trees.** Place trees from CHM maxima so the baked light matches the visible trees. Label any synthetic infill.
- **Canopy term.** Apply it through shared ShaderMaterials to every material family and to the fog, using the blend
  rule. Both prototypes applied it only to the ground.
- **Content flaws.** Fix UE5.8's content flaws:
  - a physical sky with auto-exposure and sky gaps that are not greyed;
  - height-blended layers;
  - triplanar mapping on steep slopes;
  - opaque-core foliage, because alpha testing defeats Apple's hidden-surface removal [18];
  - coverage-preserving mipmaps;
  - dense ferns and litter;
  - far canopy tinted from the orthophoto.
- **Walking.** Make the world walkable: colliders stream with the tiles.
- **Licences.** Credit data under its licences, keep raw data and caches off the internal disk, and keep purchased
  assets out of this public repository.

## 10. Risks and flip conditions

**Risks**

- **Godot on Metal.**
  - SDFGI's bounce light on Metal needs 4.8, and the MoltenVK workaround loses MetalFX [4][6].
  - The Metal freeze #119436 is open [11].
  - Frame pacing breaks with a capped frame rate [12].
  - Fog shafts drift and yellow [10].
- **4.8 is a development build** until its stable release.
- **Terrain3D** on 4.7/4.8 exists only on its main branch [14], so it stays optional.
- **Throttling** on the fanless M2 has not been quantified.
- **Tree assets** cap the photorealism.
- **Appearance** in the cloud may differ from Metal.
- **Tuning loops** could still burn usage; the stop rules exist for this.

**Switch to P2 (three.js WebGPU) if:**

- the owner requires a shareable link. Godot's web export supports only its Compatibility renderer, so the lighting
  stack would be lost;
- Godot on Metal is unstable on this Mac in the milestone 0 probe, and MoltenVK is too;
- a Chrome WebGPU build of the same content, benchmarked on the same Mac, beats Godot's frame time with equal or
  better gate scores.

**If the Mac cannot hold 30 fps:** do not switch engines for that reason alone. The browser path would carry the same
content without MetalFX and with more overhead. First reduce render scale, shadow distance, impostor distance and
foliage density, then consider the non-SDFGI blend rule (b).

**Other changes:**

- **P1 strengthens** if HDDAGI or the screen-probe GI merges and runs on Metal in under about 6 ms.
- **Unity or Flax** are worth a one-day spike only on a fan-cooled Mac or an RTX PC.
- **P6** becomes the product if non-interactive output turns out to be acceptable.

## 11. Open questions for the owner

1. What does the milestone 0 audit report for GPU cores, macOS version and free disk?
2. Do you have an external SSD, and is there any budget for scans or a newer Mac?
3. Who is the world for: you on this Mac, or others through a link? A link switches the choice to P2.
4. Is a fixed afternoon sun acceptable, or do you need time of day?
5. Is a capture trip to Aokigahara conceivable?

## 12. Sources

These survived fact-checking unless listed under the heading below. The research reports, fact-checks, judge verdicts
and critique are all in `docs/engine_selection/wip/`.

1. Repository: `renders/ue58_baseline/README.md`, `tools/lighting_stats.py`.
2. Repository: `docs/engine_selection/prototypes/lighting_stats_prototypes.json`, `wip/proto_godot.json`,
   `wip/proto_webgpu.json`.
3. https://github.com/godotengine/godot/releases/tag/4.7.2-stable
4. https://github.com/godotengine/godot/issues/120496 ; https://github.com/godotengine/godot/pull/122675 (not in the
   4.7 branch as of 20 September)
5. https://github.com/godotengine/godot/pull/119869 ; https://github.com/godotengine/godot/pull/122999
6. https://github.com/godotengine/godot/pull/99603 ;
   https://raw.githubusercontent.com/godotengine/godot/4.7-stable/doc/classes/ProjectSettings.xml
7. https://github.com/godotengine/godot-docs/blob/master/tutorials/3d/global_illumination/using_sdfgi.rst
8. https://github.com/godotengine/godot-docs/blob/master/tutorials/3d/lights_and_shadows.rst ;
   https://github.com/godotengine/godot/pull/118045
9. https://github.com/godotengine/godot-docs/blob/master/tutorials/3d/volumetric_fog.rst ;
   https://raw.githubusercontent.com/godotengine/godot/4.7-stable/doc/classes/Environment.xml
10. https://github.com/godotengine/godot/issues/120163 ; https://github.com/godotengine/godot/issues/118348
11. https://github.com/godotengine/godot/issues/119436
12. https://github.com/godotengine/godot/issues/110600 ; https://github.com/godotengine/godot/issues/114258
13. https://github.com/godotengine/godot/issues/123266
14. https://github.com/TokisanGames/Terrain3D/blob/main/doc/docs/platforms.md ; `import_export.md` and
    `controlmap_format.md` in the same folder
15. https://github.com/mrdoob/three.js/releases/tag/r186 ;
    https://github.com/mrdoob/three.js/blob/r186/examples/jsm/lighting/LightProbeGrid.js
16. https://github.com/BabylonJS/Babylon.js/blob/master/packages/dev/core/src/PostProcesses/RenderPipeline/Pipelines/standardRenderingPipeline.ts
17. https://developer.apple.com/tutorials/data/documentation/safari-release-notes/safari-27-release-notes.json ;
    https://github.com/Fyrd/caniuse/blob/main/features-json/webgpu.json
18. https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf ; https://developer.apple.com/videos/play/wwdc2020/10632/ ;
    https://developer.apple.com/videos/play/tech-talks/111375/
19. https://github.com/philipturner/metal-benchmarks
20. https://github.com/01-ai/Yi (a ggml log showing `recommendedMaxWorkingSetSize` on a 16 GB Apple8 device)
21. https://github.com/scrapfly/scrapfly-scrapers/blob/main/bestbuy-scraper/results/products.json (the MC7X4 record)
22. https://code.claude.com/docs/en/costs ; https://www.anthropic.com/engineering/multi-agent-research-system ;
    https://platform.claude.com/docs/en/build-with-claude/vision
23. https://github.com/github/docs/blob/main/data/variables/large_files.yml
24. https://pypi.org/project/bpy/ ; https://github.com/EarthObservation/RVT_py
25. https://github.com/Unity-Technologies/Graphics/blob/master/Packages/com.unity.render-pipelines.high-definition/Documentation~/probevolumes-skyocclusion.md ;
    https://github.com/Unity-Technologies/Graphics/tree/master/Packages/com.unity.render-pipelines.universal/Runtime/Overrides
26. https://github.com/gfx-rs/wgpu/blob/trunk/wgpu-hal/src/metal/adapter.rs
27. https://github.com/FlaxEngine/FlaxDocs/blob/master/manual/graphics/lighting/gi/realtime.md
28. https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_gaussian_splatting/README.md ;
    https://github.com/playcanvas/developer-site/blob/main/docs/user-manual/gaussian-splatting/building/shadows.md ;
    https://cloud.google.com/maps-platform/terms (§3.2.3: Street View may not be reused)
29. Grid convergence recomputed with pyproj during fact-checking.
30. https://github.com/godotengine/godot-docs/blob/master/tutorials/editor/command_line_tutorial.rst
31. https://www.geospatial.jp/ckan/api/3/action/package_show?id=yamanashi-pointcloud-2024 (blocked from the cloud
    container; to be read on the Mac)
32. https://github.com/godotengine/godot-builds/releases (4.8-dev6; the Linux build was downloaded through the
    container's proxy during the critique)

**Unverified — do not rely on these:**

- 30 fps on the M2 Air; any M2 millisecond cost for SDFGI, SSGI or contact shadows; how much the fanless Air throttles;
- the 75–90% lighting ceiling, which is the judges' estimate;
- the 8–10 GB of airborne LAS for 25 km², which is an extrapolation;
- the Yamanashi and Forestry Agency licence terms and sheet details, which come from the repository's own survey notes;
  the catalogue is blocked from the cloud;
- Unity, Megascans and SpeedTree pricing; UK prices for Macs and SSDs; a legal ban on leaving the trails;
- HDRP maintenance mode (secondary sources only);
- the AAA precedents for baked canopy probes (Ghost of Tsushima, Far Cry 3), which were not re-checked.
