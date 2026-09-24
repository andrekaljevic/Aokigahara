# Can the plan reach photorealistic fidelity?

## 1. The answer

**No for walking around in real time on the M2 Air, and no for stills taken from that app. Partly, by other means: offline-rendered stills and fly-throughs, and fixed walks along captured trails.** Here "photorealistic" means that an attentive viewer who knows the real forest cannot tell a 1280-px still from a photograph, or a clip from footage. That is about 85 or more on the scale in section 3.

The Godot plan tops out at roughly UE5.8 level, about 40, because what separates the renders from the photos is mostly content: thin stems, litter, root tangles, moss in relief and species-accurate trees. Three things cap that content: the M2's budget, Godot's lack of virtualised geometry, and the lack of scans. Walking is harder than stills: thin twigs upscaled by MetalFX from about 985×640 shimmer, detail levels pop in and out, and the fanless chip slows down as it heats.

## 2. Where the gap is

This ranking comes from comparing the owner's photos with UE5.8 frames g–j and the Godot renders. The first item does the most to make a frame read as a render.

1. **Geometric clutter and thin structure.** The photos have twigs, thin crooked stems, leaf litter, root tangles, clumped moss and lava rubble at 0.1–2 m scale; the renders have smooth carpets and heightfield humps. *Assets, hardware, engine.* On the M2 this gap can only be closed within about 10–20 m of the camera.
2. **Trees and stand structure.** The renders use one or two evenly spaced copies of the same conifer over an empty floor. The real stands are crowded with thin, lichen-mottled, leaning and fallen stems, which the canopy height model (CHM) cannot see. *Assets, data.* This is the cap the engine selection already named.
3. **Surface variety.** Godot's ground is one 1k moss texture set repeated every 2.2 m, with no litter, lichen or large-scale variation. *Assets, craft.* Godot 4.8-dev5 does have texture streaming, but it clashes with SDFGI in dev6 (issue #123626).
4. **Irregularity and repetition:** uniform spacing, uniform moss colour, few objects that show scale. *Craft, assets.*
5. **Lighting.** For Godot this comes second today:
   - dull grey sky gaps;
   - a haze veil;
   - broad soft patches instead of hard sunflecks;
   - no small-scale shadowing inside the moss;
   - no light coming through leaves.

   *Engine, hardware* (no hardware ray tracing or MetalFX denoiser on the M2's Apple8 GPU family), *craft*.
6. **Camera and grade.**
   - Saturation over lit pixels is 0.14–0.22 in the photos, 0.37–0.42 in UE g–j and 0.24–0.27 in Godot.
   - Godot's 70° field of view is vertical, about 96° horizontal, against about 54° for the photos' lens.
   - There is no lens character.

   *Craft*: cheap, fully closable in Godot, worth perhaps 5–8 points.

The edge-density measurements agree with item 1 (photos 0.41–0.50, UE g–j 0.18–0.32, Godot 0.21–0.28). They mostly measure the sharpening applied to the photos in Lightroom, though: one sharpening pass (unsharp mask) puts Godot inside the photo range on two of the three detail measures.

**Lighting gate against real photos** (`tools/lighting_stats.py` on 12 photos, U01–U13; two fact-checks reproduced these figures):

| Metric | Target (from UE g–j) | Real photos | Photos in target | Godot |
|---|---|---|---|---|
| Exposure key | 0.003–0.008 | 0.0060–0.0117 | 5/12 | 0.0056–0.0106 |
| Sunfleck fraction | 0.07–0.16 | 0.091–0.224 | 6/12 | 0.08–0.16 |
| Black fraction | 0.17–0.43 | 0.056–0.221 | 2/12 | 0.05–0.27 |
| Highlight B/R (warm) | 0.29–0.42 | 0.69–0.80 | 0/12 | 0.66–0.70; 0.35–0.38 on sunlit ground |
| Dynamic range, stops | 8.5–10.2 | 9.6–11.8 | 5/12 | 6.5–8.6 |
| Sky peak | ≥170 | 166–244 | 11/12 | 109–132 |

No photo meets more than 2 of the 4 primary targets; the Godot SDFGI render meets 3. The gate was designed to measure likeness to UE g–j, and that is all it measures. It does not measure photorealism.

Three caveats change the reading:
- **The photos are one edited shoot.** They were taken on one winter day (29 February 2016, midday, sun about 42–45° high) and edited in Lightroom. Exposure was raised by +0.35 to +0.70 EV on 9 of the 12; undoing that puts 10 of the 12 keys inside the existing target. "The real forest is brighter" is mostly the edit.
- **The dynamic-range gap is mostly an artefact.** The photos' crushed blacks hit the tool's floor; measured between the 5th and 99th percentiles, the gap is only about 1–2 stops. The differences that hold up are brighter sky gaps and brighter highlights.
- **Colour temperature is the one consistent difference.** On the ground in the photos, sunlit patches and shade are nearly the same colour: the ratio of sunlit to shaded blue/red is 0.90–1.17. UE g–j has orange sun against cool shade (0.33–0.57), and Godot's sunlit moss is a yellow-green with little blue (0.52–0.62). Part of this comes from the photographer's white balance.

**Should the targets change? Yes, narrowly.**
- Replace the fixed warm-highlight target with a sunlit-to-shade colour ratio, measured on the ground only and aimed near neutral.
- Drop the plan's "warmer sun, lighter moss" step; Godot's sunlit moss needs neutralising.
- Keep the key and black targets until there are unedited reference photos from a known camera.
- Do not adopt the proposed edge-density, spectral-slope or brighter-key thresholds. Real photos at the plan's 0.67 render scale would fail them, and a sharpening filter would game them.
- Add a blind test: the owner sorts renders from photos with matched framing. The photos are about 1% sky; the Godot view is about 8%.

## 3. Ratings

The scale runs from 0 to 100: how likely an attentive viewer who knows the photos is to take a 1280-px still for a photograph of Aokigahara.
- 100: indistinguishable under scrutiny.
- 85: passes a glance, fails scrutiny.
- 70: the best real-time forest on an RTX 4090 with scanned foliage.
- 50: a good AAA console forest.
- 35: good indie/AA.
- 20: clearly a CG prototype.
- 5: greybox.

**These are judgement, not measurement. The scale is uncalibrated and no blind test has been run.**

| Subject | Rating |
|---|---|
| UE5.8 frames g–j | 35 (30–42) |
| UE5.8 frames a–e | 22 |
| Godot prototype, best | 18 |
| three.js prototype, best | 14 |
| Older three.js viewer | 10 |
| Recommended plan, fully executed on the M2 Air | 40 (32–48) for stills, about 35 in motion. Probably optimistic, since no frame time has been measured |
| Any engine on the M2 Air in real time | about 50 at most |
| Blender Cycles offline, with scanned trees and debris | 80–85 |
| Gaussian splats, on the line where they were captured | 85–90 as stills; lower when walked, and away from that line |

## 4. Routes

The photorealism figures are judgement on the scale above.

| Route | How photoreal | Where | Hardware | Rough cost | Agent usage | Main risk | Real place? |
|---|---|---|---|---|---|---|---|
| Recommended Godot plan as is | 35–40 | Whole world | M2 Air | £0 | As planned | Frame time and heat slowdown unmeasured | Yes |
| Plan plus scanned assets: debris kit, 3D moss, extra thin stems, species trees | 45–50 near the camera | Whole world, best within 10–20 m | M2 Air | Bought scans or a trip; unpriced | High; trees are most of it | No scans of the species found; leaving the trails is illegal | Yes, more closely |
| Stronger Mac, staying on Godot | 45–55 | Whole world | Fan-cooled M4/M5 Max | About £4,099 | Little extra | Godot still lacks virtualised geometry and mature GI | Yes |
| Stronger PC plus UE5: hardware Lumen, Nanite Foliage, scans | 60–70; hand-picked clips have been mistaken for real footage | Whole world, best in hand-picked views | RTX 4070/5070 PC | About £529 for the card, £1,474 for a complete PC | High; agents again unable to see the viewport | Brings back the excluded UE; needs studio-scale content | Yes |
| Gaussian splats of trails and chosen spots | Photographic within about 1–2 m of the walked line | About 1% of the plot | M2 Air, 1–1.5 M splats (unmeasured) | 360 camera, 7–10-day trip, about 1 TB of storage, rented GPU | Medium to high; would run in PlayCanvas, not Godot | Lighting frozen at capture, no wind, visible joins with the rest of the world | Yes, most literally |
| 360 video trail walk, fixed path | Photographic | Fixed paths only | M2 Air | Camera and trip | Low | No free movement | Yes |
| Neural enhancement | Real time: no; the network alone manages about 1–5 fps on an M2. Offline, Cosmos Transfer clips can look photographic | Offline clips | Rented H100, median about $3.38/h; DLSS 5 needs RTX 50 and has no public SDK | A few GPU-hours per set of clips | Medium | Flicker, warping, invented bark and moss | Partly: the layout holds, the detail is invented |
| World models: Genie 3, Marble | Photographic-looking for about a minute; "video game quality" when based on real streets | Invented worlds | Cloud | Genie: $249.99/month, 60 s limit per world | Low | Drift; invented geometry | No |
| Blender Cycles stills and fly-throughs | Above UE5.8 today; 80–85 with scans | Stills and fixed-path clips anywhere | M2 Air (slow) or rented | £0 plus scans | Medium | Render time on a fanless Air, 256 GB disk, same asset cap | Yes |

## 5. Recommendation

**If photorealism is non-negotiable,** the smallest change that turns "no" into "yes" is to change what you produce, not the engine or the Mac. Photographic results are within reach in two forms:
- Blender Cycles stills and fly-throughs built from the same LiDAR pipeline;
- fixed trail walks made from 360 video or splats.

Neither breaks the no-UE rule, the M2 Air or a modest agent budget. Both still need real content: bought scans of the species (none found yet) or a trip. On a trip, stay on the trails, and contact the Yamanashi Film Commission before posting anything commercially. Try it first in a mossy UK wood with a 360 camera (£0–600).

Photoreal free roam over the whole plot is not available to this owner in 2026. The smallest step that moves it materially is an RTX 4070/5070-class PC running UE5 with hardware Lumen, Nanite Foliage and scanned species trees. That reaches about 60–70, in hand-picked views. It is still not "yes", and it breaks all three constraints: UE, new hardware, and heavy agent work with no view of the viewport. I would not do it.

**If "as good as possible on this Mac" is acceptable,** keep the Godot plan and call its target "high-end indie, not photoreal". Reorder it as follows:
1. **Test motion on the Air first (milestone 0).** Measure frame time, heat slowdown, and shimmer of thin geometry under MetalFX.
2. **Fix the gate as in section 2** (about 1 session). Decide which look is wanted: the edited winter photos or a neutral summer look.
3. **Camera and grade** (about 1 session):
   - a narrower field of view for stills;
   - a colour grade (LUT) that brings saturation down to about 0.2;
   - light sharpening after MetalFX;
   - subtle grain;
   - brighter sky gaps.
4. **Put the effort into content, not lighting:**
   - first, a near-field kit of 20–40 debris meshes and 3D moss clumps;
   - then thin stems added statistically, after checking whether the raw point cloud resolves them;
   - then species trees, which set the ceiling.
5. **Optionally**, add a Cycles "photo mode" built from the same data.

Expect about 40–50 for stills near the trail and 35–45 in motion.

## 6. Sources

**Survived fact-check:**
- **Repository:**
  - `tools/lighting_stats.py` run on the photos, the Godot renders and `renders/ue58_baseline/` (reproduced);
  - XMP metadata in `refphotos/*.webp`;
  - `prototypes/godot/proj/main.gd` (field of view);
  - `docs/ENGINE_SELECTION.md` §3;
  - OSM paths in `viewer/assets/terrain/study-context.json`.
- **Apple and Godot:**
  - Apple Metal Feature Set Tables (the denoiser needs Apple9; the M2 is Apple8);
  - Godot 4.8-dev5 texture streaming, and issue #123626.
- **Real-time benchmarks:**
  - Witcher 4 path-traced forest on an RTX 4070 (TechSpot, VideoCardz);
  - Witcher 4 UE5 demo on a base PS5 (TechPowerUp);
  - fanless penalty, M5 Air against M5 Pro (Notebookcheck);
  - stock-UE5 forest clip on an RTX 4090 (80.lv).
- **Neural rendering:**
  - REGEN README;
  - DLSS 5 inputs, SDK status and cost (NVIDIA developer blog, Tom's Hardware);
  - diffusion on an M3 Ultra (arXiv 2605.16259);
  - Cosmos benchmarks;
  - H100 median price (getdeploying.com).
- **Splats:**
  - lighting limits (RealityKit, PlayCanvas, KHR_gaussian_splatting and GDGS documentation);
  - PlayCanvas performance chart.
- **World models:**
  - Genie 3 (DeepMind);
  - Street View grounding (TechCrunch);
  - WorldRoamBench (arXiv 2606.31672).

**Unverified or judgement:**
- all 0–100 ratings and route ratings;
- M2 frame times for splats or dense content, and heat slowdown;
- UK hardware prices;
- splat quality in forest away from the capture path;
- Cosmos Transfer on dense forest;
- whether scans of *Tsuga sieboldii* or *Chamaecyparis* can be obtained;
- capture rules (from search snippets only);
- the licence and editing history of the owner's photos.
