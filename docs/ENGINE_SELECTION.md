# Engine selection: decision record

Date: 23 September 2026. Status: recommendation, awaiting the owner's answers to section 11 and the milestone 1
Mac benchmark. Branch of record: `claude/aokigahara-engine-selection-tqyqx6`. The owner has excluded Unreal Engine 5,
so it was not scored. The evidence behind every section is in `docs/engine_selection/` (research reports,
fact-checks, judge verdicts and prototypes).

## 1. Decision

Build the free-roam world as a **Godot 4 native macOS app**, using the Forward+ renderer on Metal with MetalFX
Temporal upscaling. Feed it from an **engine-agnostic Python pipeline** that turns the Yamanashi 0.5 m LiDAR into three
things: terrain, real tree positions, and precomputed canopy light maps. Godot is deliberately a thin runtime that can
be replaced; the pipeline and its baked data are the lasting asset.

The **runner-up is three.js r186 WebGPU** in Chrome, fed by the same pipeline. It takes over if a shareable web link
becomes a requirement or if Godot fails the Mac benchmark.

All three judging lenses (fidelity, waste, risk) chose the same winner and runner-up.

UE5.8 is not needed. The look the owner values comes mostly from three things: sunlight through the canopy, deep sky
occlusion, and a low exposure key. Shadow maps, LiDAR-baked canopy maps, fog and auto-exposure can reproduce all
three. A Godot render of this repository's real data already meets 3 of the 4 primary lighting targets, and it was
rendered headless in the cloud without the Mac. It is not yet at parity by eye; section 4 says what is missing.

## 2. What the UE5.8 attempt achieved, and why

**What it achieved.** Frames g–j in `renders/ue58_baseline/` show the valued result: dappled sun, a dark
sky-occluded understorey, bright sky gaps, haze, warm bounce and a wide range. The engine-specific parts were Lumen
global illumination (GI), Virtual Shadow Maps (VSM), Nanite and default-on fog and auto-exposure (section 4). The
slope-driven moss (a shader rule), the rocks, the terrain and the tree data are portable.

**Where it fell short.** Most of the flaws were content, not engine, and any engine must fix them:

- a clipped white sky;
- far canopy as dark, flat masses;
- textures stretched across 1 m heightmap steps;
- hard-edged material blotches, because layers were not height-blended;
- dithered masked materials;
- noisy, stretched bark;
- a sparse understorey and no litter.

**Why it wasted so much.**

- The world existed only as binary `.uasset` files on the Mac. Branch `ue5.8/aokigahara-production` holds only 12
  script and JSON files, with no `.uproject`, so the corruption could not be recovered.
- Agents could not see the viewport, so the owner had to supply phone photos.
- UE plus its derived-data cache (DDC) filled what is very probably a 256 GB disk.

## 3. The honest ceiling

**Hardware.** Model MC7X4 is very probably the 16 GB / 256 GB M2 Air with an 8-core GPU; the only source found is a
retailer listing [21], so confirm with the milestone 0 audit:

- about 2.9 TFLOPS FP32;
- 100 GB/s of memory bandwidth, shared with the CPU [19];
- GPU family Apple8: MetalFX temporal upscaling works, but there is no hardware ray tracing and no MetalFX denoiser
  (both start with M3) [18];
- a GPU working set of about 10.7 GiB, two-thirds of RAM [20];
- fanless, so it throttles under sustained load. How much has not been verified.

**Realistic result.** A warm, locked 30 fps at about 1280×800 internal resolution, upscaled with MetalFX from about
0.67 scale, with a fixed or slow-moving sun. Within that:

- **Lighting:** about 75–90% of the frames g–j look, within 150–200 m of the camera. This is the judges' estimate,
  not a measurement.
- **Overall:** "high-end indie / AA", roughly level with UE5.8.
- **Better than UE5.8 where UE5.8's flaws were content:**
  - a physical sky;
  - far canopy shaded from the canopy height model (CHM) and tinted from the orthophoto;
  - measured 0.5 m terrain;
  - height-blended materials;
  - no dithering;
  - a dense understorey.
- **Short of UE5.8 on:**
  - off-screen and multi-bounce light;
  - sharp canopy shadows hundreds of metres away;
  - Nanite-level density;
  - time of day without re-baking.
- **Not photoreal:** the trees cap it, because no scan-quality *Tsuga sieboldii* or *Chamaecyparis* assets exist.

**Going beyond UE5.8 would need**, in order of value:

1. Species-accurate assets, either the owner's own photogrammetry or paid scans.
2. A fan-cooled Mac from M3 onwards, or an RTX PC, together with next-generation GI once it has shipped and proved
   itself (Godot HDDAGI [5], Unity Surface Cache GI, Flax DDGI).
3. For stills and fly-throughs only, Blender Cycles on the same data, which can exceed UE5.8 today.

## 4. Lighting parity

### What produced the look in UE5.8

- **Lumen:** sky occlusion (dark interior, bright gaps) and warm bounce light off rocks and ferns.
- **Virtual Shadow Maps:** sharp sunflecks near the camera, and soft canopy shade far away.
- **Volumetric fog:** haze and light shafts.
- **Auto-exposure with filmic tonemapping:** a low exposure key and a wide range without clipping.

### The target, measured

Running `tools/lighting_stats.py` on frames g–j gives these ranges [1]. The four primary targets are the ones that
separate the valued frames from the flatter UE5.8 frames and from the old Three.js viewer; the secondary checks do not
separate them on their own and are reported, not gated.

| Metric | Target range | Role |
|---|---|---|
| Sunfleck fraction | 0.07–0.16 | primary |
| Log-average luminance (exposure key) | 0.003–0.008 | primary |
| Black fraction | 0.17–0.43 | primary |
| Highlight B/R (warm sunlit patches) | 0.29–0.42 | primary |
| Dynamic range | 8.5–10.2 stops | secondary |
| Shade B/R | 0.60–1.28 | secondary |
| Clipped fraction | under 0.005 | must hold |

The older "cool shadows" metric (`shadow_blue_ratio`) was withdrawn on 23 September as JPEG noise. Ignore it wherever
it appears, including in the research reports under `docs/engine_selection/wip/`, some of which quote it.

### Prototype evidence

Both prototypes used the repository's real GSI terrain, tree library and moss materials, rendered at 1280×800,
headless, in a cloud container with no GPU [2]. **Bold** means in range. "Primary met" counts the four primary
targets. The cameras were not composed to match frames g–j, so these numbers compare lighting character, not views.

| Render (under `docs/engine_selection/prototypes/`) | log-avg | sunfleck | black | highlight B/R | stops | Primary met |
|---|---|---|---|---|---|---|
| Godot, SDFGI (`godot/renders/godot_sdfgi.jpg`) | **0.0056** | **0.157** | **0.27** | 0.70 | 8.18 | 3/4 |
| Godot, no SDFGI, baked canopy map (`godot/renders/godot_canopy.jpg`) | **0.0064** | **0.124** | **0.18** | 0.70 | 6.75 | 3/4 |
| Godot, SDFGI + canopy map, stronger sun (`godot/renders/godot_sdfgi_canopy_sun6.jpg`) | **0.0078** | 0.163 | **0.20** | 0.66 | **8.60** | 2/4 |
| Godot, neither (`godot/renders/godot_nosdfgi.jpg`) | 0.0106 | **0.083** | 0.05 | 0.70 | 6.50 | 1/4 |
| three.js, plain + canopy map (`webgpu/renders/t4_off_tuned.jpg`) | **0.0036** | 0.34 | 0.51 | 0.48 | 12.8 | 1/4 |
| three.js, sparse canopy (`webgpu/renders/t0_off.jpg`) | 0.0315 | **0.106** | 0.13 | 0.55 | 12.1 | 1/4 |
| three.js, SSGI (`webgpu/renders/t5_ssgi_tuned_BROKEN.jpg`) | 0.099 | 0.001 | 0.00 | 0.52 | 5.9 | 0/4 |

What the table shows:

- **The baked canopy map carries the load.** On its own it matches SDFGI on three targets. SDFGI adds about 1.4 stops
  of range and also darkens trunks and rocks. Dropping SDFGI therefore costs range, not the whole look.
- **No render hits the warm-highlight target.** Sun colour, albedo and bounce are the first things to tune.
- **By eye, parity has not been reached yet.** Next to UE frames g and i, the Godot frames are grey-green and flat:
  the sky gaps are dull, and there are no shafts and no warm patches. three.js `t4` dapples more crisply, but it has
  too many sunflecks and crushed blacks.

### Recipe on the recommended path (most important first)

1. **Sun shadows.**
   - Settings: 4-split PSSM out to 150–200 m, with blended splits, a 4096 atlas and about 0.5° angular size [8].
   - Casters: alpha-scissor foliage, with impostor casters in the far splits.
   - Add Godot 4.8's contact shadows, which cost about 0.04 ms on the pull request's test GPU.
   - Use PCSS only if the budget allows.
2. **Canopy maps from the LiDAR CHM** (DSM2 minus DEM), baked in the cloud with rvt-py or a numpy heightfield march
   [24].
   - Maps:
     - sky-view factor, as a ground map plus a coarse 3D volume for trunks and foliage;
     - sun transmittance, which gives canopy shade beyond the shadow distance;
     - a gap mask for placing shafts.
   - Apply them to **every** material through global shader uniforms (AO, IRRADIANCE, light()).
   - Apply them to fog through custom FogVolume shaders. Godot's fog GI-inject only reads VoxelGI and SDFGI [9].
3. **Sky ambient:** PhysicalSkyMaterial ambient, scaled by the sky-view factor.
4. **SDFGI** at half resolution, with occlusion and sky light on. It needs 4.8 on Metal [4]. It is the first thing
   to drop if it costs more than about 5 ms [7].
5. **SSAO plus half-resolution SSIL** for short-range warm bounce.
6. **Volumetric fog** with a shadowed sun and temporal reprojection, plus aerial fog.
7. **AgX tonemapping and auto-exposure.**
8. **Foliage:** fern and needle backlight, bent normals.
9. **MetalFX Temporal** at about 0.67 scale, with a 30 fps cap.

**Expected shortfall against UE5.8:**

- blurrier far canopy shade;
- low-frequency bounce light, with some SDFGI leaks and cascade shifts;
- GI that ignores wind: SDFGI supports dynamic lights but not dynamic occluders, so swaying crowns and ferns do not
  update bounce or sky occlusion [7];
- no off-screen bounce;
- a fixed sun (each extra sun angle costs about 25 MB of maps at 1 m);
- possible drift of fog shafts during camera motion, from open issue #120163 [10].

### How it will be measured

1. **Cameras.** Add `harness/cams_ue58.json` with four cameras composed like frames g, h, i and j, plus two
   regression cameras (a trail and a road edge). Render them as 1280×800 PNG.
2. **Gate.** On the four matched cameras, all four primary targets must be in range, and the sky must not clip
   (`clipped_fraction` below 0.5%). Dynamic range and shade B/R are reported alongside.
3. **Review.** Agents read the JSON first. The owner sees one contact sheet per milestone, with each render beside the
   matching UE frame.
4. **Bake check.** Blender Cycles renders the same tile and cameras. In shaded areas the sky-view factor should agree
   within about 0.05.
5. **Metal check.** The same cameras are captured on the Mac under Metal. Lavapipe, the software Vulkan renderer in
   the cloud, only checks appearance.

## 5. Options compared

The scores below are the mean of the three judges' scores out of 10; higher is better. For disk, a higher score means
a smaller footprint. The weighted column averages each judge's own weighting. Two lenses weighted lighting heaviest,
and the waste lens weighted agent efficiency heaviest.

| Path | Lighting | Fidelity | Mac feasibility | Disk | Agent efficiency | Cost | First result | Weighted |
|---|---|---|---|---|---|---|---|---|
| **P1 Godot 4 (Metal)** | **7.0** | 6.2 | **6.3** | 8.0 | **8.0** | 10 | **8.0** | **7.4** |
| P2 three.js r186 WebGPU | 5.2 | 5.2 | 5.7 | **9.0** | 7.0 | 10 | 7.0 | 6.5 |
| P3 Unity 6 URP | 4.7 | 6.2 | 4.7 | 3.0 | 3.0 | 7.3 | 3.7 | 4.6 |
| P4 Bevy 0.19 | 4.0 | 4.3 | 6.0 | 7.0 | 6.3 | 10 | 3.3 | 5.5 |
| P4 Flax 1.12 (two judges) | 5.5 | 5.8 | 4.0 | 5.5 | 3.0 | 8.5 | 3.0 | 4.9 |
| P5 Capture hybrid | 5.0 | 6.3 | 4.7 | 2.7 | 3.0 | 2.7 | 1.3 | 4.1 |
| P6 Cycles (ineligible) | 8.7 | 7.2 | 2.3 | 7.7 | 6.3 | 10 | 6.7 | 6.8 |

**P1 Godot** won under all three lenses. It is the only path with the measured lighting signature of frames g–j on
real data, it has every lighting part built in, and it runs natively on Metal with MetalFX (the only measured M2 Air
figure: 19% less GPU time than FSR2 [6]). Its weaknesses are that SDFGI on Metal needs 4.8 [4], SDFGI's cost on an
integrated GPU is unmeasured (its own docs say integrated GPUs need tuning) [7], and a Metal freeze reproduced on an
M2 Air, and also on M1 Max and M4 machines, is still open [11].

**P2 three.js** has the smallest footprint, a shareable URL and reuses the existing viewer. It lost because its SSGI
pipeline brightened frames 25–30× and removed all shadows (cause not found), and it has no auto-exposure (Babylon
does [16], but offers no other lighting advantage). LightProbeGrid cannot save, load or stream [15], the browser has
no MetalFX, and Safari WebGPU needs macOS 26 [17].

**P3 Unity** has baked Adaptive Probe Volume sky occlusion, the closest ready-made match to Lumen's. It lost because
that bake treats leaves as opaque, and URP lacks volumetric fog, auto-exposure and a physical sky [25]. The editor
(about 8.5 GB) and its Library cache (tens of GB) would repeat the UE5.8 pattern.

**P4 Bevy** is text-only and compiles in the cloud, but it lost because it has no GI on the M2 (meshlets need M3 or
later [26]), no terrain system, no editor, and a breaking release every 4–5 months. **Flax** has software DDGI, the
nearest thing to Lumen outside UE [27]. It lost because it runs only through MoltenVK, has documented foliage
artefacts and has never been measured on an M2.

**P5 Capture** looks photographic inside captured spots, but covers under 1% of the plot (trails only). Splats keep
the light of the day they were captured and ignore scene exposure and shadows [28], and wind and moving sunflecks
degrade forest captures. It stays an optional later add-on.

**P6 Cycles** is not free-roam, so it is ineligible. Use it as the calibration reference and bake tool, through the
bpy wheel [24].

## 6. Why the recommended path is less wasteful

| Where | Item | Size |
|---|---|---|
| Mac internal | Godot editor | 170.6 MB zip [3] |
| Mac internal | Project code, scenes and scripts (git) | under 1 GB |
| External SSD | Import and Metal shader caches (deletable) | 1–4 GB (estimate) |
| External SSD | Engine-ready world: 1 m terrain, maps, instances, textures, impostors | 2–5 GB (estimate) |
| External SSD | Raw LiDAR: 916 MB now, plus about 8–10 GB of airborne LAS for 25 km² | about 10 GB |
| Cloud | Godot 140 MB, lavapipe 96 MB, caches 17 MB (measured); bpy 402 MB; GIS and lidR environment 1–2 GB | about 2–3 GB |

The Mac total is about 5–15 GB, mostly on an external SSD. UE5.8 filled the internal disk.

**Who does what.** Cloud agents own the pipeline, the code, the scenes, the bakes, the trees, and the headless
rendering and scoring. The owner runs one scripted warm benchmark per milestone, approves one contact sheet, and does
any downloads the cloud cannot reach.

**Headless self-verification has been demonstrated [2].**

- **Godot 4.7.2, Forward+ on lavapipe under `xvfb-run` with `--write-movie` [30]:**
  - SDFGI, SSAO, SSIL, volumetric fog, PSSM, AgX and auto-exposure all ran without errors;
  - about 7 s per frame with 5 M triangles, and 3–4 minutes per settled still;
  - the project is three text files in `docs/engine_selection/prototypes/godot/proj/`;
  - renders are in `docs/engine_selection/prototypes/godot/renders/` (JPEG copies; the PNG originals lived in the
    session's scratch space and are not kept).
- **three.js on SwiftShader WebGPU:** about 20 s per frame. Renders and page source are in
  `docs/engine_selection/prototypes/webgpu/`. The recipe that makes WebGPU work headless in the container is in
  `docs/engine_selection/RESUME.md`.

**Usage practices.**

- **Storage:** text in git; binaries as release assets with SHA-256 manifests (each under 2 GiB); no LFS, which the
  container cannot reach [23].
- **Sessions:** one scoped single-agent session per step. Use plan mode first, `/clear` between steps, and a smaller
  model for routine work. Multi-agent runs cost about 15× the tokens of a chat, so keep them for one-off research
  [22]. This decision itself came from such a run, about 25 agents across research, fact-checks, prototypes and
  judges; it is not the pattern for day-to-day building.
- **Images:** read the metrics before images. A 1280×800 image costs about 1.3k tokens on every turn [22].
- **Renders:** render a few fixed cameras per change, never parameter sweeps.

## 7. What carries over

**Repository** (on `main` unless a branch is named):

- `renders/ue58_baseline/` and `tools/lighting_stats.py`: the target and the gate.
- `tools/audit_render.mjs`, `harness/cams*.json` and `harness/sheet.py`: camera and contact-sheet tooling.
- `viewer/assets/terrain/`:
  - `{local,study,regional}-height.f32` with their JSON: GSI DEM5A, 8 m;
  - `*-jogan.u8`: the GSJ Jogan lava mask;
  - `*-landcover.u8`: Ministry of the Environment vegetation;
  - `*-context.json`: OSM paths, lakes and landmarks.
- `data/forest-wide.f32` (467,601 placements) and `viewer/assets/forest-instances.f32`. Both are to be replaced by
  stems detected from the CHM.
- `viewer/assets/tree-library-v2.glb` and `viewer/assets/materials_v2/`: placeholders. Both prototypes used them.
- Branch `claude/aokigahara-uhd-assets-5l10c2`: `asset_packs/materials_uhd_*` and `MATERIALS_UHD_MANIFEST.json`.
  Use these as colour targets only, because they were upscaled from 125–340 px crops.
- Branch `claude/4k-asset-packs-photos-sy83u7`: `asset_packs/_sources/`, the source photos.
- Branch `rebuild/measured-2026-09-19`, folder `unreal/AokigaharaUE/`:
  - `Scripts/jprcs8.py`, `real_terrain_lib.py`, `build_real_terrain.py`, `audit_measured_axes.py` and
    `test_measured_rebuild.py`, with their CI workflow;
  - `Docs/REBUILD_2026-09-19.md`, which sets the evidence rules.

  This is engine-agnostic Python, so it becomes the start of the new pipeline.
- Branch `ue5.8/aokigahara-production`: `unreal/AokigaharaUE/Scripts/aokigahara_geo.py` and `test_geo.py`, the
  verified transform. Also `export_heightmaps.py`, `export_placements.py` and `Docs/MACHINE_AUDIT.md`.
- Branch `claude/aokigahara-engine-selection-tqyqx6`: `docs/engine_selection/`, holding the research (`wip/`), the
  prototypes and `RESUME.md`.
- `docs/research/`: the research dossier.

**Owner's Mac:** `/Users/Shared/Aokigahara-survey-2026-09-17` (916 MB):

- `08LE9307.zip`: airborne LAS;
- `mms_08LE9307.zip`: MMS LiDAR with RGB;
- `mmstrj.zip`;
- `fr_mesh20m_08le3_2025.7z`: the 20 m forest register;
- `dem_9325.zip`, `ortho_9325.zip`, `inyou_9325.zip`;
- `survey_report.md`.

The UE project itself is lost. Megascans claimed under a UE plan may be licensed for UE only.

## 8. Phased plan

**Milestone 0: set-up (about one day)**

The owner, on the Mac (about 1 hour):

1. Run `system_profiler SPDisplaysDataType SPHardwareDataType; sw_vers; df -h /`.
2. If you have an external SSD (1 TB, APFS), attach it and move the survey folder onto it. If not, the plan still
   works within about 15 GB of internal space, but that space must be free before starting.
3. Download Godot 4.8-dev6 and 4.7.2 for macOS, about 170 MB each.
4. Test whether the `gic-yamanashi` S3 URL downloads. If it does, export the per-sheet URL list so the cloud can
   fetch the sheets itself. If not, upload the sheets as release assets.

The agent, in the cloud:

1. Pin Godot 4.7.2 for Linux and install lavapipe.
2. Create a Python 3.13 environment with `uv`, holding bpy 5.2.2, rasterio, laspy, pyproj and rvt-py.
3. Create a conda environment for lidR and lasR, on R 4.5.
4. Add `godot/` and `pipeline/` folders, a short CLAUDE.md, the cameras file and the gate script.

**Milestone 1: vertical slice**

The slice is 500 m × 500 m of real 0.5 m LiDAR, about 4–6 sheets, covering forest interior, a trail and a road edge.

The agent builds the DEM, DSM2 and CHM (buildings masked with OSM); detects stems with lasR local maxima and
Dalponte crowns, calibrated to the 20 m register; bakes the canopy maps; builds a 1 m terrain clipmap (Terrain3D
optional) with height-blended triplanar materials; builds Tsuga and Chamaecyparis in bpy (LOD0, LOD1, impostor); adds
ferns, moss and litter; applies the section 4 recipe; renders a Cycles reference; and iterates against the gate.

The owner runs one script on the Mac. It runs a 10-minute warm benchmark capped at 30 fps and writes frame times to
JSON. It also captures the six cameras, once on 4.8-dev with Metal and MetalFX and once on 4.7.2 with MoltenVK. The
owner then approves one contact sheet.

Acceptance:

- the section 4 lighting gate passes on the four matched cameras in `harness/cams_ue58.json`, and the two regression
  cameras do not get worse;
- at least 95% of frames come in under 33.3 ms once the Mac is warm, at 0.67 MetalFX scale;
- GPU memory stays under 4 GB;
- the project uses under 2 GB of internal disk;
- the terrain RMSE against the provider's DEM is reported;
- trees register to CHM maxima;
- there is no dithering, texture stretching or clipped sky.

**Milestone 2: 5 × 5 km**

- **Streaming:** 250–500 m tiles, loaded with `ResourceLoader.load_threaded_request` in a ring of about 1–1.5 km.
- **Terrain:** a 1 m geomorphing clipmap.
- **Trees, by distance:**
  - full detail to 30–40 m;
  - mid LOD to about 150 m;
  - opaque-core octahedral impostors, baked in bpy, to 1–2 km;
  - beyond that, a canopy heightfield from the CHM, tinted from the orthophoto.
- **Shadows:** far cascades are cached, and baked transmittance takes over beyond the shadow distance.

The owner benchmarks a scripted flight path through the world.

**Milestone 3 (optional)**

- extra sun angles;
- packaging, with the minimum macOS version set to 14 because of issue #123266 [13];
- a capture trip.

## 9. Must-do regardless of engine

- **Coordinates.** Build in EPSG:6676 with a local origin. Reproject the legacy AEQD assets rather than shifting
  them, because 0.092° of grid convergence gives up to 5.7 m of error at the corners [29].
- **Resolution.** Use 1 m terrain in the engine and keep 0.5 m for bakes. Terrain3D-style 32-bit maps at 0.5 m take
  about 1.2 GB [14].
- **Trees.** Place trees from CHM maxima so that the baked light matches the visible trees. Label any synthetic infill.
- **Canopy maps.** Apply them to every material and to the fog. Both prototypes applied them only to the ground.
- **Content flaws.** Fix the UE5.8 content flaws:
  - a physical sky with auto-exposure;
  - height-blended layers;
  - triplanar mapping on steep slopes;
  - opaque-core foliage, because alpha testing defeats Apple's hidden-surface removal [18];
  - coverage-preserving mipmaps;
  - dense ferns and litter;
  - far canopy tinted from the orthophoto.
- **Conifers.** Build them from species parameters in bpy, with scanned bark and needle cards.
- **Data handling.** Credit the data under CC BY, and keep raw data and caches off the internal disk.

## 10. Risks and flip conditions

**Risks**

- **Godot on Metal:**
  - SDFGI bounce light on Metal needs 4.8; the MoltenVK workaround loses MetalFX [4][6];
  - the Metal freeze #119436 [11];
  - frame pacing when the frame rate is capped [12];
  - fog drift and yellowing [10].
- **Terrain3D:** Godot 4.7/4.8 support exists only in its unreleased main branch [14], so it stays optional.
- **Throttling:** the fanless M2's throttling has not been quantified.
- **Assets:** the tree assets cap how photoreal it can look.
- **Cloud vs Metal:** cloud renders may not look the same as Metal renders.
- **Tuning loops:** undisciplined loops could burn usage the way UE5.8 did.

**Switch to P2 if any of these happen:**

- the warm benchmark cannot hold 30 fps even without SDFGI;
- Godot on Metal is unstable on this Mac, and MoltenVK is too;
- the owner requires a shareable link (Godot's web export only supports its Compatibility renderer);
- the three.js shadow loss is fixed and a Chrome build meets at least 4 of the 5 metrics at 30 fps on the M2.

**Other changes:**

- **P1 strengthens** if HDDAGI or screen-probe GI merges and runs on Metal in under 6 ms.
- **Revisit Unity or Flax** only on a fan-cooled Mac or an RTX PC, and only after a successful one-day spike.
- **P6 wins** if non-interactive output is acceptable.

## 11. Open questions for the owner

1. What does the milestone 0 audit command report for GPU cores, macOS version and free disk?
2. Do you have an external SSD, and is there any budget for scans or a newer Mac?
3. Who is the world for: you on this Mac, or others through a link? A link flips the choice to P2.
4. Is a fixed afternoon sun acceptable, or do you need time of day?
5. Is a capture trip to Aokigahara conceivable?

## 12. Sources

These survived fact-checking unless flagged.

1. Repository: `renders/ue58_baseline/README.md`, `tools/lighting_stats.py`.
2. Repository: `docs/engine_selection/prototypes/lighting_stats_prototypes.json`, `wip/proto_godot.json`,
   `wip/proto_webgpu.json`.
3. https://github.com/godotengine/godot/releases/tag/4.7.2-stable ; https://github.com/godotengine/godot-builds/releases
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
19. https://github.com/philipturner/metal-benchmarks ; https://github.com/ggml-org/llama.cpp/discussions/4167
20. https://github.com/01-ai/Yi (the ggml log shows `recommendedMaxWorkingSetSize` on a 16 GB Apple8 device)
21. https://github.com/scrapfly/scrapfly-scrapers/blob/main/bestbuy-scraper/results/products.json (MC7X4 record)
22. https://code.claude.com/docs/en/costs ; https://www.anthropic.com/engineering/multi-agent-research-system ;
    https://platform.claude.com/docs/en/build-with-claude/vision
23. https://github.com/github/docs/blob/main/data/variables/large_files.yml
24. https://pypi.org/project/bpy/ ; https://github.com/EarthObservation/RVT_py ; https://github.com/c-webster/CanRad.jl
    (its Julia hosts are blocked from the container)
25. https://github.com/Unity-Technologies/Graphics/blob/master/Packages/com.unity.render-pipelines.high-definition/Documentation~/probevolumes-skyocclusion.md ;
    https://github.com/Unity-Technologies/Graphics/tree/master/Packages/com.unity.render-pipelines.universal/Runtime/Overrides ;
    https://github.com/frarees/unity-changelog/blob/main/Changelogs/6000.7/6000.7.0a6.md
26. https://github.com/gfx-rs/wgpu/blob/trunk/wgpu-hal/src/metal/adapter.rs
27. https://github.com/FlaxEngine/FlaxDocs/blob/master/manual/graphics/lighting/gi/realtime.md
28. https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_gaussian_splatting/README.md ;
    https://github.com/playcanvas/developer-site/blob/main/docs/user-manual/gaussian-splatting/building/shadows.md ;
    https://cloud.google.com/maps-platform/terms (§3.2.3: no reuse of Street View)
29. Grid convergence recomputed with pyproj during fact-checking: https://pypi.org/project/pyproj/
30. https://github.com/godotengine/godot-docs/blob/master/tutorials/editor/command_line_tutorial.rst

**Unverified; do not rely on these:**

- how much the M2 Air throttles (the 25% figure);
- any M2 millisecond cost for SDFGI or SSGI (the 25–35 ms SSGI figure came from a misread trace);
- HDRP maintenance mode and "about 20 fps on M1";
- Unity, Megascans and SpeedTree pricing;
- a legal ban on leaving the trails;
- UK prices for Macs and SSDs;
- the Yamanashi licence and sheet details, which come from the repository's own survey notes because the catalogue is
  blocked from the container;
- the AAA probe precedents (Ghost of Tsushima, Far Cry 3), which were not re-checked.
