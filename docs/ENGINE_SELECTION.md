# Engine selection: decision record

Date: 23 September 2026, revised the same evening. Status: recommendation. The plan's first step (milestone 0) is a
cheap test on the owner's Mac that can still overturn it. Branch of record:
`claude/aokigahara-engine-selection-tqyqx6`. The owner has ruled out restarting with Unreal Engine 5 (certainly on
the Mac; whether that covers a separate machine is open, section 11), so the first round of judging did not score it;
a later round scored UE5.8 on a separate RTX-class GPU, only as an option that needs the owner's OK. The evidence
behind every section is in `docs/engine_selection/`: research reports, fact-checks, prototype reports, judge verdicts
and an independent critique of the draft. A key to that folder is in `docs/engine_selection/RESUME.md`; the later
evidence is listed in section 12.

**What the revision adds.** Three later rounds of research and one hands-on test by the owner are folded in:
photorealism (section 3), yield when nothing heavy may be installed on the Mac (sections 1, 5, 6, 8 and 10), and
World Labs' Marble (section 5). None of them changes the engine. They change how the app reaches the Mac: the cloud
agents now export it, so the Mac never holds the Godot editor.

## 1. Decision

Build the free-roam world as a **Godot 4 native macOS app**: Forward+ renderer on Metal, with MetalFX Temporal
upscaling. Feed it from an **engine-agnostic Python pipeline** that turns the Yamanashi 0.5 m LiDAR into terrain, tree
positions detected from the canopy height model (CHM), and precomputed canopy light maps.

**Delivered as an exported app, with no editor on the Mac (revised).** Cloud agents build the project and export the
finished macOS app from Linux. The Mac holds only that app and the world data: no Godot editor, no project folder and
no `.godot` caches. In the later yield ranking (section 5) this variant, "P1b", scored 3.27, the top score of the
ten paths the yield judge rated, against 3.08 for the original editor-on-the-Mac plan [36]. Yield is a different scale
from section 5's first table: it multiplies value, cost efficiency and chance of delivery, so every score is low.
Yield scores are judgement anchored to checked facts, not measurements. The official export templates are universal
(Intel and Apple silicon in one file), so each app is 170 MB for Godot 4.7.2 or 232 MB for 4.8-dev6: about 0.4 GB for
the milestone 0 pair [37].

**The tie, and how it is broken.** Two other variants also scored 3.27 [36]:

- **P1b+G:** the same, plus a small rented cloud GPU for the agents' test renders, about £3–15 a month;
- **P9g:** the same Godot project on a bought RTX PC (a Windows PC with an NVIDIA RTX graphics card), about
  £1,600–2,400 up front (unverified prices).

The ranking breaks the tie by order, not by score. Start with P1b, because it costs £0 and needs no new accounts. Add
the cloud GPU only when milestone 1a needs motion checks. Consider the RTX PC only after P1b has proven the content,
and only if the M2 misses 30 fps or the owner wants more (section 10).

**Runner-up: three.js r186 WebGPU in Chrome**, fed by the same pipeline. It takes over if a shareable web link becomes
a requirement, or if Godot proves unstable on this Mac (section 10).

All three judging lenses chose this winner and this runner-up: fidelity-first, waste-first, and risk and longevity.
The later yield ranking kept a Godot variant on top under every alternative weighting it tried [36].

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

- warm highlights, on the tool's band. On sunlit ground alone Godot is already inside the target, and whether warmth
  is wanted at all waits on the owner's choice of look (section 11, question 10);
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

**Not photoreal.** On a 0–100 judgement scale of how likely an attentive viewer is to take a still for a photograph,
the fully executed plan reaches about 40, against about 35 for UE5.8 frames g–j. No engine on this Mac is expected
to pass about 50 in real time. Section 3 says what does reach photoreal, and at what cost [33].

**UE5 on a separate machine is a flip condition, not the plan.** The owner has excluded UE5 on the Mac but has not
said whether that also covers a separate RTX PC or a rented GPU. UE5.8 there is the only real-time route with a
clearly higher ceiling: about 60–70 on the section 3 scale, still short of photoreal at about 85. The yield ranking
puts it first only if the owner wants the highest real-time fidelity available and accepts that it stays short of
photoreal; its "hard requirement" meant a ceiling of at least 7 on its own 0–10 scale, not a photograph [36]. The
photorealism round advises against UE even then, and for truly photographic output recommends offline Cycles stills or
captured trail walks instead [33]. Sections 3, 10 and 11 set out the three cases.

**Marble is at most an add-on.** World Labs' generated worlds look photographic only within a few metres of where
they were made, and the owner's own text-prompted test produced a tropical jungle, not Aokigahara. At most they could
add look-around stops; they cannot carry free roam (section 5) [39].

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
- a sparse understorey and no litter;
- detail in one small area only. The source package was a 32 × 30 km terrain with detailed trees only within 120 m
  of the start (`docs/handover/Aokigahara_3D_README.md`), and the owner's aerial frames show the detailed block
  sitting inside a much larger, coarse landscape. The world could be roamed, but only a small part looked as intended,
  and trimming the scope to 10 km did not spread the detail.

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

**Not photoreal.** Content caps the fidelity, and the trees most of all. No species-accurate scans of *Tsuga
sieboldii* or *Chamaecyparis* were found; a CC0 lead and commercial hinoki models are unverified.

**Going beyond UE5.8 would need, in order of value:**

1. Species-accurate trees, from the owner's own photogrammetry or verified scans.
2. A fan-cooled M3-or-later Mac or an RTX PC, together with a newer GI once it is proven on that class of hardware.
   Candidates: Godot HDDAGI or its screen-probe GI [5], Flax DDGI, Unity Surface Cache GI. On Godot, a stronger
   machine buys higher settings, not photoreal: Godot has no Nanite-class virtualised geometry, and mainline Godot
   has no hardware-ray-traced GI. A fan-cooled M4/M5 Max Mac (about £4,099) rates about 45–55 on the scale below
   [33][38].
3. For stills and fly-throughs only: Blender Cycles on the same data, which can exceed UE5.8 today.

### How close to photoreal (added after the photorealism round)

The owner asked whether the plan can reach photorealistic fidelity. **Not for walking around in real time on this
Mac, with any engine.** Partly yes, by other means: offline stills and fly-throughs, and fixed walks along captured
trails [33].

**The scale.** It runs from 0 to 100: how likely an attentive viewer who knows the owner's photos is to take a
1280-px still for a photograph of Aokigahara.

- 100: indistinguishable under scrutiny;
- 85: passes a glance, fails scrutiny;
- 70: the best real-time forest on an RTX 4090 with scanned foliage;
- 50: a good AAA console forest;
- 35: good indie/AA;
- 20: clearly a CG prototype;
- 5: greybox.

**These ratings are judgement, not measurement.** The scale is uncalibrated, and no blind test has been run [33].

| Subject | Rating |
|---|---|
| UE5.8 frames g–j | 35 (30–42) |
| UE5.8 frames a–e | 22 |
| Godot prototype, best | 18 |
| three.js prototype, best | 14 |
| This plan, fully executed on the M2 Air | 40 (32–48) for stills, about 35 in motion; probably optimistic, since no frame time has been measured |
| Any engine on the M2 Air in real time | about 50 at most |

**Why the plan stops there.** What separates the renders from the photos is mostly content: thin stems, twigs,
litter, root tangles, moss in relief and species-accurate trees. The M2's budget, Godot's lack of virtualised
geometry and the lack of scans cap that content. Walking is harder than stills: thin twigs upscaled by MetalFX
shimmer, detail levels pop in and out, and the fanless chip slows down as it heats [33][34].

**What does reach photoreal, and at what cost** (ratings on the same judgement scale) [33][35]:

- **Offline path tracing** (light simulated ray by ray, taking minutes per frame): Blender Cycles stills and
  fly-throughs with scanned trees and debris, about 80–85. Not free-roam. £0 plus the scans; slow on the fanless Air,
  or rented.
- **Gaussian splats at captured spots** (a 3D capture from many photos, drawn as soft coloured blobs): about 85–90 as
  stills on the line where they were captured, lower when walked and away from that line; the fact-check calls 85–90
  optimistic for free roam. They are photographic within about 1–2 m of the captured line, and they are the only route
  to locally photographic real-time frames on the Air itself (its splat budget is unmeasured). They would run in
  PlayCanvas or Spark, not Godot, whose splat plugin has no LOD and failed on Metal in its one Mac report; that would
  roughly double the agent build. They cover about 1% of the plot and need a 360 camera, a 7–10-day trip, about 1 TB
  of storage and a rented GPU. The light is frozen at capture and nothing moves in the wind.
- **360 video of a trail walk:** photographic, on fixed paths only. It needs a camera and a trip.
- **UE5 on an RTX 4070/5070-class PC,** with hardware-ray-traced Lumen lighting, Nanite Foliage (UE's very dense
  foliage geometry) and scanned species trees: about 60–70, in hand-picked views. Still not photoreal. About £529 for
  an RTX 5070 card, or from about £1,474 for a complete RTX 5070 PC (unverified); the yield ranking priced a faster
  RTX 5070 Ti or 5080 PC at £1,600–2,400 [36]. It brings back the excluded UE, and agents that cannot see the
  viewport.
- **Neural enhancement of the rendered frames:** not in real time on this Mac, where the network alone manages about
  1–5 fps. Offline, geometry-guided video models can make photographic-looking clips (unverified on dense forest) on a
  rented datacentre GPU (median about $3.38 an hour), with flicker and morphing, and they invent the bark and moss.

**If photorealism is non-negotiable,** the photorealism round's advice is to change what is produced, not the engine
or the Mac [33]:

- Blender Cycles stills and fly-throughs built from the same LiDAR pipeline;
- fixed trail walks made from 360 video or captured splats.

Neither is free roam. Neither needs UE, a new computer or a heavy agent budget, but both still need real content:
bought scans of the species (none found yet) or a trip. Try it first in a mossy UK wood with a 360 camera (£0–600).
The same round rates UE5 on an RTX PC at about 60–70, still not photoreal, and advises against it. The yield ranking
sends a "hard requirement" to UE instead (section 5), because it counts a real-time ceiling of about 70 as meeting it.
The two rounds differ mainly on what "photoreal" means and on whether free roam may be given up.

**If "as good as possible on this Mac" is acceptable,** the photorealism round suggests this order [33]:

1. test motion on the Air first, in milestone 0: frame time, heat slowdown, and shimmer of thin geometry;
2. fix the gate as proposed in section 4 (about 1 session);
3. a camera-and-grade pass: a narrower field of view for stills, a colour grade that brings saturation over lit pixels
   down to about 0.2 (the photos measure 0.14–0.22 on that measure), light sharpening after MetalFX, subtle grain and
   brighter sky gaps (about 1 session, worth perhaps 5–8 points);
4. put the effort into content, not lighting: first a near-field kit of 20–40 debris meshes and 3D moss clumps, then
   thin stems, then species trees, which set the ceiling;
5. optionally, a Cycles "photo mode" built from the same data.

Expect about 40–50 for stills near the trail and 35–45 in motion. Steps 1 and 2 are in milestone 0 (section 8).
Steps 3 and 4 are an optional re-ordering on top of section 8 and are not yet budgeted there; the photo mode is in
milestone 3. The upper end of that range needs scanned assets or a trip [33].

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

Three notes on the metrics:

- **A withdrawn metric.** The earlier "cool shadows" metric (`shadow_blue_ratio`) was JPEG noise and has been
  withdrawn. Some research reports under `docs/engine_selection/wip/` still quote it; ignore it there.
- **The sky flaw is judged by eye.** No metric here detects UE5.8's flat, pale sky, so it is checked on the contact
  sheet.
- **The gate measures likeness to frames g–j, not photorealism** [34]. Measured the same way, none of the owner's
  12 main photos meets more than 2 of the 4 primary targets; the Godot SDFGI render meets 3. Three findings qualify
  this:
  - the photos are one edited winter shoot (29 February 2016, midday). Exposure was raised by +0.35 to +0.70 EV
    (exposure value; +1 EV doubles the brightness) on 9 of the 12, and undoing that puts 10 of the 12 keys inside
    the existing target, so "the real forest is brighter" is mostly the edit;
  - the one consistent difference is colour. In the photos, sunlit ground and shade are nearly the same colour; UE
    g–j has orange sun against cool shade, and Godot's sunlit moss is a yellow-green with little blue;
  - the detail measures (edge density and fine detail) mostly track the photos' sharpening, so they cannot gate
    content.

  The proposed change is narrow: replace the fixed warm-highlight target with a sunlit-to-shade colour ratio,
  measured on the ground only and aimed near neutral; keep the key and black targets until there are unedited
  reference photos from a known camera; adopt no detail thresholds; and add a blind test in which the owner sorts
  renders from photos with matched framing. It waits on the owner's choice of look (section 11, question 10) and is
  applied at the milestone 0 decision point (section 8) [33]. **Until then, Highlight B/R is reported, not gating.**

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
  0.66–0.70 whatever the GI mode, so sun colour and moss albedo set it. The crushed three.js `t1` does meet it. A
  later check found that on the ground alone Godot's sunlit patches measure 0.35–0.38, inside the target: the tool's
  band also takes in haze and sky-lit trunks [34].
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
8. **AgX tonemapping and auto-exposure.** Hold off on warming the sun or lightening the moss for the warm-highlight
   target until the owner picks the look (section 11, question 10). The owner's photos have sunlit patches and shade
   in nearly the same colour, and the photorealism round advises neutralising Godot's sunlit moss instead [33][34].
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
   Shade B/R and dynamic range are reported. The two regression cameras must not get worse. Until the gate change
   above is applied, Highlight B/R is reported, not gating, so the gate uses the other three primary targets.
4. **Review.** Agents read the JSON first. The owner sees one contact sheet per milestone, each render beside its
   matching UE frame, and judges the sky and any stipple by eye.
5. **Bake check.** Blender Cycles renders the same tile and cameras. In shade, the sky-view factor should agree within
   about 0.05.
6. **Metal check.** The same cameras are captured on the Mac under Metal. Lavapipe, the software renderer in the
   cloud, checks appearance only.
7. **Spot check across the plot.** From milestone 1b, the gate also runs at eight or more random eye-height spots
   drawn across the loaded area, not only at the start. Their median must meet the same targets, and no spot may lose
   the near-field detail (debris, moss clumps, thin stems) that the start shows. This is the UE5.8 lesson in section 2:
   detail has to follow the walker everywhere, generated by the same rules around wherever the camera is.

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

### Yield ranking (added after the decision)

The owner then asked whether Godot is still the highest-yield option if no GB-heavy engine may be installed on the
Mac. A yield judge scored ten paths [36]. **Yield** is expected fidelity per unit of total cost, adjusted for risk, on
a 0–10 scale. It multiplies three things:

- **value:** the mean of the photoreal-ceiling and lighting scores, cut to 0.35 of that for output that is not
  free-roam;
- **cost efficiency:** agent usage weighted 0.35, money 0.25, owner effort 0.20, and Mac disk and install 0.20;
- **chance of delivery,** from a risk score.

The scores are the judge's judgement, anchored to the earlier lighting scores and to checked facts. They are not
measurements. Unity, Bevy and Flax were not re-scored.

| Path | What goes on the Mac | Money | Yield |
|---|---|---|---|
| **P1b Godot app exported by cloud agents, no editor on the Mac** | about 0.4 GB of apps for milestone 0, plus the world pack (2–5 GB, estimate) | £0 a month | **3.27** |
| P1b+G: P1b plus a small on-demand cloud GPU for the agents' test renders | the same as P1b | about £3–15 a month | 3.27 |
| P9g: the same Godot project on a bought RTX PC | nothing if played at the PC; a 59.8 MB streaming app if streamed to the Air | £1,600–2,400 up front (unverified), plus £5–18 a month of electricity | 3.27 |
| P1 as first planned (editor on the Mac) | about 0.7 GB of editors, plus 2–6 GB of project caches (estimate) | £0 a month | 3.08 |
| P9u: UE5.8 on a bought RTX PC (needs the owner's OK) | as P9g | as P9g | 2.55 |
| P7: Godot on a rented cloud GPU, streamed to the Mac | 0–60 MB | about £58–71 a month at 10 hours a week | 2.52 |
| P2 three.js WebGPU in the browser | 0 MB with Safari on macOS 26 or later; a 0–5 GB browser cache | about £0–1 a month | 2.35 |
| P8: UE5.8 on a rented cloud GPU, streamed (needs the owner's OK) | 0–60 MB | about £132–159 a month to play at 10 hours a week; about £200–350 a month while agents build | 1.91 |
| P6 Cycles fly-throughs (not free-roam) | video files only | £0 for stills | 1.72 |
| P5 Captured splats of the trails | 0.2–1.6 TB of raw 360 video on external drives | a trip of about £1.5–3k (unverified) | 0.47 |

What the ranking shows:

- **The premise does not hold.** Godot is not GB-heavy: its editor zips are 170.6 MB and 184.6 MB, about 351 MB each
  unpacked, and an exported app is 170–232 MB [37]. The GB problem was UE, at about 43–63 GB plus its cache
  [36][38]. Every option that renders on the Mac still needs a world pack of an estimated 2–5 GB, which can sit on an
  external SSD, except the browser path (P2), whose 0–5 GB cache stays on the internal disk and can be evicted.
- **A Godot variant stays top** under all four alternative weightings the judge tried. Only when fidelity is squared
  do the RTX-PC paths, with either engine, draw level [36].
- **If the owner wants the highest real-time fidelity available,** the order flips. The judge tested this as
  "photorealism a hard requirement": any path whose ceiling is below 7 on its 0–10 scale (roughly 70 on the section 3
  scale) loses three-quarters of its value. Then P9u scores 2.55, P8 1.91, P6 1.72, and every Godot path 0.82 or
  less. Both UE paths need the owner's explicit OK [36]. That ceiling is still short of photoreal, and the
  photorealism round advises against UE for this case (section 3) [33].
- **Streaming Godot from a rented GPU (P7) is poor value:** about £60 a month for little gain, because Godot's ceiling
  is set by its features, not the GPU. The stream also smears exactly the foliage detail that matters [36][38].
- **What P1b costs** [37]:
  - Metal shaders cannot be pre-compiled from Linux, so the first run of each app stutters while they compile;
  - the app must be fetched with `curl`. A browser download is quarantined, and macOS's download check (Gatekeeper)
    then blocks the app, which is signed but not notarised by Apple (Apple's online check for apps shared outside the
    App Store);
  - any GDExtension (native plug-in code, such as Terrain3D) needs a macOS build, which GitHub's free Mac build
    machines can make because this repository is public, plus the "Disable Library Validation" entitlement;
  - no Xcode and no paid Apple Developer account are needed.

### Marble (World Labs), tested after the decision

**What it is.** A generative world model. From a text prompt, a few photos, a short video or a coarse 3D layout (its
Chisel editor), it makes a Gaussian-splat world: a cloud of soft coloured blobs that looks photographic from near
where it was generated. It invents what it cannot see, and its lighting is baked in [35]. It has no LiDAR input; the
kit in `tools/marble_test/` feeds it the real terrain indirectly, as a depth panorama or a block-out model [40].

**Walk-out on World Labs' sample worlds** [39]. Photographic at the origin, convincing about 2 units out, broken by 5,
and broken or gone by 10. With one unit at about 1.7–2.1 m, that is photographic within about 2–4 m and broken by
about 8–10 m. Meta's WorldGen paper found the same fall-off 3–5 m out.

**The owner's own test, 23 September 2026** [39]. Free web app, Chisel editor, Marble's larger-world model, text
prompt only. The prompt started Chisel's automatic layout before the real-terrain block-out was uploaded, so the world
did not use the real terrain. The result was a bright tropical jungle (palm-like and banana-like leaves, red spiky
flowers, bamboo-like stems), smooth and illustration-like rather than photographic. It turned into stretched green
streaks a short way from the start, and from outside it was one small bubble surrounded by black. The owner's
verdict: "fairly limited world it made tbh". Measured on the start view, cropped from a browser screenshot, against
the owner's 12 main photos (U01–U13):

- whole-frame saturation 0.605, against 0.24–0.33 in the photos: more than twice a typical photo. This is a different
  measure from the lit-pixel saturation in section 3, and the two are not comparable;
- exposure key 0.101, against 0.006–0.012 in the photos and the g–j target of 0.003–0.008: about ten times a typical
  photo;
- black fraction 0.014 and sunfleck fraction 0.038, against 0.056–0.221 and 0.091–0.224 in the photos: almost no
  deep shade and few sunflecks;
- fine detail 8.1, against 19.8–26.6 in the photos and 17.9–26.5 in UE5.8 frames h–k (k is j at a brighter
  exposure): about a third of a typical photo. This is weak evidence: the measure tracks sharpening and compression
  (section 4).

That is the opposite of the natural forest lighting the owner valued in UE5.8. Two further photos, a dehazed phone
edit and an upscaled portrait, widen the ranges; the README gives both sets. The caveats are real: one screenshot,
compressed and rescaled by the browser capture; the wrong layout; text-only input.

**Role: optional look-around stops at most, labelled as synthetic, not the backbone.** One world is a bubble a few
metres across. Covering the trails would take thousands of hand-joined worlds, and none is expected to follow the
LiDAR more than loosely (the API test will measure this) [40]. World Labs' newer Atlas (early access, unpriced) takes
camera poses and depth maps, so depth from the LiDAR could in principle constrain it; it is worth revisiting once it
is priced [35].

**Still untested** (section 11); either could earn Marble a place:

- a photo-driven world from a few Aokigahara photos, which is the fair best case. It needs photos the owner took or
  holds the rights to, and World Labs' terms for uploaded inputs have not been checked;
- the API real-terrain test in `tools/marble_test/`, which needs `WLT_API_KEY` set in the cloud environment's
  settings.

**Cost.** The web app has a free plan, which cannot export [40]; paid plans are about $20–95 a month (secondary
sources, unverified) [35]. Through the API, a standard world costs 1,500 credits (about $1.20) and a draft 150 (about
$0.12); the minimum purchase is $5 for 6,250 credits [40].

## 6. Why the recommended path is less wasteful

### Disk

| Where | Item | Size |
|---|---|---|
| Mac internal | Two exported Godot apps, 4.8-dev6 and 4.7.2 (universal, no editor) | 232 + 170 MB [37] |
| Mac internal | macOS's own Metal pipeline cache (not movable) | a few hundred MB (estimate) |
| External SSD, or internal if none | Engine-ready world pack: 1 m terrain, bakes, instances, textures, impostors | 2–5 GB (estimate) |
| External SSD, or internal if none | Raw LiDAR: 916 MB now, plus an estimated 8–10 GB of airborne LAS for 25 km² (unverified) | about 10 GB |
| Cloud (reinstalled each session) | Linux Godot editors 4.8-dev6 and 4.7.2 (about 78 MB zipped each); their macOS export templates (about 0.27 GB if only each bundle's macos.zip is fetched, 2.7 GB for the full bundles); lavapipe 96 MB, bpy 402 MB, GIS and R environments 1–2 GB | about 2–3 GB |
| Cloud (each session) | The Godot project and git working tree, including `.godot/` import and shader caches | 2–6 GB (estimate) |

**Total on the Mac: about 13–16 GB, of which about 10 GB is raw LiDAR.** It was 13–20 GB while the plan put the
editor and the project on the Mac. The project and its caches now stay in the cloud, where a session has 30 GB of
disk [38]; the Mac holds only the exported apps, the world pack and the raw LiDAR. With an SSD, the internal disk
carries under 1 GB. Without one, keep about 20 GB free. Once a month, run:

```bash
du -sh ~/Library/Caches "$HOME/Library/Application Support/Godot"
```

The second folder is where an exported Godot app keeps its user data and shader caches (Godot's default location, not
yet checked on this Mac). The Godot editor is optional, for the owner to inspect scenes by hand: about 351 MB per
version unpacked [37], plus the project and its 2–6 GB of caches (estimate) if the owner opens scenes. The agents do
not need it. UE5.8 filled the internal disk.

### Who does what

- **Cloud agents:** the pipeline, the code, the scenes, the bakes, the trees, headless rendering and scoring, and
  exporting the macOS app. It is signed ad hoc, for running on the owner's own Mac, so no Apple account is needed [37].
- **The owner:** one scripted Mac benchmark per milestone, approval of one contact sheet, licence checks, and any
  downloads the cloud cannot reach. The owner starts each Mac bench and passes its JSON summary back by pasting or
  uploading it. Optionally, an agent session that the owner runs on the Mac can send it back instead; cloud agents
  cannot currently start that exchange [37].

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
- **Delivering apps and world packs.** The milestone 0 and 1a apps may be public release assets of this repository,
  because they contain only data already public in it. Once a pack contains survey products whose licence is not yet
  confirmed, or purchased assets, it reaches the Mac through a private channel instead, such as a private bucket
  behind a signed, expiring link, never a public release [37]. Purchased assets reach the cloud build the same way,
  from a private store whose credentials are kept as an environment secret, or the owner adds them on the Mac.
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
- `tools/marble_test/`: the Marble test kit. Its `yamanashi_sheets.py` downloads one sheet's 0.5 m DEM, 0.5 m DSM2
  and 0.25 m orthophoto from the prefecture's own index, so it can serve the pipeline's fetch step [40].

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

Budget: 1 agent session, plus about 1 more for the gate change once the owner has chosen the look (see the decision
point), and about 2 hours of the owner's time.

**The agent, in the cloud:**

1. **Turn the Godot prototype into a Mac probe, exported as a macOS app from Linux** [37].
   - Package its assets as a small pack beside the app, so the Mac needs no repository checkout.
   - Set the macOS driver to Metal and the scaling mode to MetalFX Temporal.
   - Add a `--bench` mode: a scripted 10-minute camera path. It logs process time, GPU frame time, video memory
     (`RENDER_VIDEO_MEM_USED`) and physics time to JSON, and compares `Engine.max_fps = 30` against a vsync-based cap.
     The owner passes it after `--`, and picks Metal or MoltenVK with `--rendering-driver metal` or `vulkan` [30][37].
     Add a short warm-up pass that shows every material once, so shaders compile before the timed run.
   - Export with the official universal templates, the only kind they ship, and the default ad-hoc signature. That
     needs no Xcode and no Apple Developer account. Keep GDExtensions out of the probe.
   - Publish the two apps as release assets of this repository. That is fine here, because they contain only data
     already public in it; later packs may need a private channel (section 6).
2. **Pin one Godot build for both cloud and Mac:** 4.8-dev6 (Linux editor 78.1 MB [32]; exported macOS app 232 MB
   [37]). Record it in `godot/VERSION`, and re-render the gate cameras whenever it changes. Keep 4.7.2 as the stable
   and MoltenVK fallback (exported app 170 MB).
3. **Add `tools/cloud_setup.sh`,** run by the environment's setup script or a SessionStart hook, because every cloud
   session starts from a fresh machine. It installs lavapipe, the Linux editors of both pinned versions (4.8-dev6 and
   4.7.2) and their macOS export templates, plus two separate environments. For the templates, fetch only the
   macos.zip inside each bundle (124 MB and 146 MB), not the 1.3–1.4 GB bundles [37]. The environments are:
   - bpy in its own Python 3.13 virtualenv;
   - a pipeline environment from conda-forge (gdal, rasterio, pdal, pyproj, laspy, lidR and lasR). If rvt-py is used,
     install it with `--no-deps`, because its declared dependency on source-only `gdal` fails to build.

   Commit the lockfiles.
4. **Add the gate:** `harness/cams_ue58.json` following section 4's composition rules, a gate script and a
   contact-sheet script. Until the gate change below, the script reports Highlight B/R without gating on it.
5. **Add `ATTRIBUTION.md`:** CC BY 4.0 for the Yamanashi and Forestry Agency data once confirmed, and ODbL for the OSM
   layers.
6. **Propose the 5 × 5 km plot.** State its bounds in EPSG:6676 (xmin, ymin, xmax, ymax) and list the 1:500 sheet IDs
   that cover it.

**The owner, on the Mac:**

1. Run `system_profiler SPDisplaysDataType SPHardwareDataType; sw_vers; df -h /` and paste the output.
2. Download the two probe apps with `curl`, using the one Terminal command the agent provides. A browser download
   would be quarantined and blocked [37]. No Godot editor is installed. Then run the probe four ways:
   - 4.8-dev6 on Metal;
   - 4.7.2 on Metal, to see whether the SDFGI bounce bug reproduces on an M2;
   - 4.7.2 on MoltenVK;
   - the best of the three again with SDFGI off.

   Each run is about 12 minutes. Before the timed runs, warm up each app once on each driver it will use (three
   warm-ups), because Metal shaders cannot be pre-compiled from Linux and MoltenVK compiles its own. The bench offers
   a short warm-up pass that shows every material, so this adds about 10 minutes. While the path runs, note any
   shimmer of thin branches and needles: motion matters more than stills [33][37].
3. Confirm the licence text on the geospatial.jp dataset page, and the Forestry Agency terms for the 20 m register,
   before anything is uploaded publicly.
4. Approve or adjust the plot bounds.
5. Read the dataset's resource list through its CKAN API [31] and pass it to the agent. The agent then tests one sheet
   URL from the cloud: only a 200 there means the cloud can fetch the sheets itself. The Marble test kit has since
   fetched one sheet's DEM, DSM2 and orthophoto into the cloud from the prefecture's own index [40], so this check now
   matters mainly for the raw LAS point clouds, which were not tried.
6. Optionally, attach an external APFS SSD and move the survey folder onto it.

**Decision point.** Apply the section 10 flip conditions to the probe results, and to the owner's answers to section
11, before any pipeline work starts. Once the owner has answered question 10 (the look), apply the section 4 gate
change: about 1 session, before milestone 1a's tuning starts.

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
- Target: the owner walks the tile on the Mac within about a week of starting, subject to their availability. Each
  time there is something to walk, the agents export a new app and the owner fetches it with the same `curl` command
  (from a private link once the pack carries survey products under an unconfirmed licence, or purchased assets;
  section 6).
- If motion or temporal checks (stipple, fog drift, walk tests) become the bottleneck, add a small on-demand cloud GPU
  for the agents' test renders (P1b+G) [36][38]. AWS London's g6f.large costs about $0.26 an hour, or about £3–15 a
  month with its disk. It needs an AWS account, a GPU quota request that new accounts must make first and that can
  be refused, and scoped credentials stored as environment secrets. Its first job is to prove that Godot renders on
  it. It gives no M2 timings.

Acceptance:

- the lighting gate passes on the four matched cameras, in its changed form once the owner has chosen the look
  (until then, Highlight B/R is reported, not gating);
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
- **Near-field detail everywhere:** the debris, moss and thin-stem kit is generated deterministically from the tile's
  own rasters around the camera, in every tile, so no part of the plot is a coarse fill. The spot check (section 4,
  "How it will be measured", item 7) runs over the whole plot.

The owner benchmarks a scripted flight and walk.

### Milestone 3 (optional)

- extra sun angles;
- notarised packaging for others, if wanted. If shaders are ever baked on a Mac, set a minimum macOS of 14 because of
  issue #123266 [13];
- a capture trip;
- a Blender Cycles "photo mode" for stills and fly-throughs from the same data (section 3);
- Marble look-around stops at a few trail spots, labelled as synthetic, only if the photo-driven test or the API
  real-terrain test (section 5) shows a world that looks like Aokigahara and stays photographic well beyond a few
  metres.

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
- **Exporting from Linux:** the first run of each app stutters while Metal shaders compile; the official templates are
  universal-only; any GDExtension needs a macOS build and an extra entitlement [37]. Delivery can break the licence
  rules: once a world pack carries survey products under an unconfirmed licence, or purchased scans, it must not be a
  public release asset (section 6).
- **Terrain3D** on 4.7/4.8 exists only on its main branch [14], so it stays optional.
- **Throttling** on the fanless M2 has not been quantified.
- **Content, trees most of all,** caps the photorealism (section 3).
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
foliage density, then consider the non-SDFGI blend rule (b). After that, the same project can move to an RTX PC
(P9g, below).

**Move the same Godot project to an RTX PC (P9g)** once P1b has proven the content, and only if the M2 misses 30 fps
or the owner wants more. It raises the ceiling a notch, not to photoreal: full-resolution SDFGI, longer shadows,
denser foliage, native 1440p and no throttling. Godot's features, not the GPU, set the limit. It needs the owner's
OK to spend about £1,600–2,400 (unverified) [36].

**Add a cloud GPU for the agents (P1b+G)** when milestone 1a needs motion or temporal checks (section 8) [36].

**Move to UE5.8 on an RTX-class GPU only if all of these hold** [36][38]. This needs the owner's explicit OK: they
excluded UE5 on the Mac and have not said whether that covers a separate machine.

- The owner wants the highest real-time fidelity available (a ceiling of about 60–70 on the section 3 scale) and
  accepts that it stays short of photoreal. For truly photographic output, section 3's non-negotiable case applies
  instead, and it does not need UE.
- The owner allows UE5.8 on a separate RTX PC or a rented GPU.
- A one-day rented spike confirms the jump over frames g–j. Use AWS g6e.2xlarge (an L40S GPU) on Windows, in
  Stockholm at $2.746 an hour or Frankfurt at $3.17; about £25–35 for the day, by estimate. London has no L40S, and
  the cheaper L4 is not a fair test, because it games below an RTX 3060. Request the GPU quota first: it is 0 on new
  accounts, and approval can take days.
- The level is rebuilt by scripts from pipeline data held as text in git. Never again hand-edited `.uasset` files as
  the only copy.
- The owner accepts about £1,600–2,400 for an RTX PC (P9u, best for sustained use; unverified prices), or about
  £130–350 a month to rent (P8, for light or trial use).
- If it is streamed to the Air, the broadband holds a steady 30 Mbps or more with low jitter.

Even then, UE raises the ceiling to about 60–70 on the section 3 scale, in hand-picked views, not to photoreal: the
gap is mostly content, and Nanite Foliage is still Experimental in 5.8 [33][36].

**Other changes:**

- **Godot strengthens** if HDDAGI or the screen-probe GI merges and runs on Metal in under about 6 ms.
- **Unity or Flax** are worth a one-day spike only on a fan-cooled Mac or an RTX PC.
- **P6** becomes the product if non-interactive output turns out to be acceptable.
- **Marble** stays an optional add-on at most. It would earn a place only if the photo-driven test or the API
  real-terrain test shows a world that looks like Aokigahara and stays photographic well beyond the 2–4 m found so
  far; even then it cannot carry free roam [39].

## 11. Open questions for the owner

1. What does the milestone 0 audit report for GPU cores, macOS version and free disk?
2. Do you have an external SSD, and is there any budget for scans or a newer Mac?
3. Who is the world for: you on this Mac, or others through a link? A link switches the choice to P2.
4. Is a fixed afternoon sun acceptable, or do you need time of day?
5. Is a capture trip to Aokigahara conceivable?
6. How close to photoreal must it be? The yield ranking and the photorealism round read "photoreal required"
   differently (section 3), so pick one of three answers:
   - **(a)** "High-end indie / AA, roughly level with your UE5.8 frames g–j" (about 40 on the section 3 scale) is
     fine: Godot, as planned.
   - **(b)** The best real-time fidelity available, at real cost, knowing it is still not photoreal (about 60–70): the
     UE flip conditions in section 10.
   - **(c)** Truly photographic: only offline Cycles stills and fly-throughs, or captured trail walks, which are not
     free roam (section 3). Photographic free roam is not available on any engine in 2026. Godot stays for any
     free-roam part.
7. When you ruled out UE5.8, did you mean "not on my MacBook Air" or "never again"? Would you allow it on a separate
   RTX PC or a rented GPU, with the level rebuilt by scripts from data in git?
8. Which is the real limit: "nothing heavy installed on the Mac", or "the Mac must be the machine that renders"?
   Would you install a streaming app of about 60 MB (Moonlight) to play from a PC or a rented GPU, or must it be
   browser-only?
9. What could you spend: £0; about £3–15 a month for a cloud GPU for the agents; £1,600–2,400 up front for an RTX PC;
   or £130–350 a month to rent one? How many hours a week would you play, and for how many months? Buying beats
   renting after about 4–5 months at 40 hours a week, or 12–18 months at 10 hours a week. Is there room, power and
   wired Ethernet for a PC? What does your broadband deliver (steady speed, ping, any data cap, Wi-Fi or wired)?
   Streaming needs a steady 30 Mbps or more. Would you open an AWS account? Which subscription plan do the agents run
   on? Pro and Max plans can run agents on your own PC through Remote Control (driving an agent session on that
   machine from claude.ai).
10. Which look is the target: your edited winter photos from 29 February 2016, the warm UE5.8 look, or a neutral
    summer look? The answer sets the gate's colour target (section 4).
11. Would you try Marble once more with 2D input, from a few Aokigahara photos, and walk out from the start point?
    This is the fair best case for Marble. Use only photos you took yourself or hold the rights to; World Labs' terms
    for uploaded inputs have not been checked. For the real-terrain API test, add `WLT_API_KEY` in the cloud
    environment's settings, never in a chat, and buy $5 of API credit.

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

Added in the revision (all under `docs/engine_selection/` unless stated):

33. `wip/photoreal_synthesize.md`: the photorealism synthesis, including the 0–100 scale and the routes.
34. `wip/photoreal_research_gap.json` and `wip/photoreal_verify_gap.json`: the owner's photos against the gate, the
    renders and UE5.8, with a fact-check that re-ran every figure.
35. `wip/photoreal_research_realtime.json`, `photoreal_research_capture.json` and `photoreal_research_neural.json`,
    with their fact-checks `photoreal_verify_realtime.json`, `photoreal_verify_capture.json` and
    `photoreal_verify_neural.json`.
36. `wip/yield_judge_yield.json`: the yield ranking and its sensitivity checks.
37. `wip/yield_research_lightmac.json` and `wip/yield_verify_lightmac.json`: exported-app sizes, signing, shader
    baking and the Mac-side steps. Where they disagree the fact-check wins: official templates are universal-only.
38. `wip/yield_research_cloud.json` and `wip/yield_verify_cloud.json`: cloud GPUs, prices and streaming.
39. `marble_walkout/README.md`, with `garden_scores.json` and `lane_scores.json`: the walk-out test on sample worlds
    and the owner's hands-on test of 23 September 2026. The screenshot and its metrics are not committed.
40. Repository: `tools/marble_test/README.md` and its scripts: the real-terrain kit and its credit costs.

**Unverified — do not rely on these:**

- 30 fps on the M2 Air; any M2 millisecond cost for SDFGI, SSGI or contact shadows; how much the fanless Air throttles;
- the 75–90% lighting ceiling, which is the judges' estimate;
- the 8–10 GB of airborne LAS for 25 km², which is an extrapolation;
- the Yamanashi and Forestry Agency licence terms and sheet details, which come from the repository's own survey notes;
  the catalogue is blocked from the cloud;
- Unity, Megascans and SpeedTree pricing; UK prices for Macs and SSDs; a legal ban on leaving the trails;
- the AAA precedents for baked canopy probes (Ghost of Tsushima, Far Cry 3), which were not re-checked;
- every 0–100 photorealism rating and every yield score, which are judgement;
- RTX PC, GPU and Marble plan prices, and the cost of a one-day UE spike;
- Godot rendering on a rented cloud GPU, and the start-render-stop workflow for agents, which are untested;
- an arm64-only app of about 0.2 GB, which would need an untested strip-and-re-sign step;
- Marble's reach on the real terrain and with photo input, which are untested;
- geometry-guided video models on dense forest, and splat quality in forest away from the capture path;
- the rules for capturing in Aokigahara, which come from search snippets only;
- the licence and editing history of the owner's photos.
