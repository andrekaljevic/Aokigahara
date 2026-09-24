# Aokigahara fresh start: granular roadmap

Written 24 September 2026. It turns `docs/ENGINE_SELECTION.md` into steps, using the best resources that need no
Unreal Engine anywhere: not on the Mac, and not in the cloud as a converter. `docs/engine_selection/PROJECT_HISTORY.md`
explains why each rule below exists.

## The rules (copy into the new repository's CLAUDE.md, so every session loads them)

1. **One builder, one repository.** Every step is committed and pushed the same day. No relaying between AI tools.
2. **Fixed targets.** The target look is chosen once (open decision 2). Lighting targets come from the valued UE5.8
   frames g–j; ground targets from the owner's photos and IMG-013. Only the owner judges realism.
3. **Measure every change before the owner sees it.** Render headless in the cloud from a warmed, known state; run
   `tools/lighting_stats.py` and the ground reports; fixed regression cameras must not get worse; random eye-level
   spots, never one hero camera. A change that does not show up in the render fails loudly.
4. **Prove small, then scale.** One sheet, then one tile, then the plot. Area is never a quality lever.
5. **Budgets and stop rules.** Every step has a session budget. On a miss: stop, report, and let the owner decide.
   Normal effort by default; helper-agent teams only after stating the cost.
6. **The Mac runs only the finished app.** Building, baking and testing happen in the cloud.

## Resources

Everything here works without Unreal. Items marked *verify* are checked in step 0.6 before anything depends on them.

| Need | Resource | Notes |
|---|---|---|
| Engine | Godot 4 (pinned 4.8-dev6, fallback 4.7.2), Forward+ on Metal, MetalFX | Exported in the cloud as an Apple-silicon app of about 83 MB |
| Terrain | Terrain3D (Godot add-on) | 4.7/4.8 support is on its main branch only; *verify* against the pinned build |
| Asset building | Blender, or the `bpy` Python module, headless in the cloud | Fracturing, roots, LODs, impostors, normal/AO bakes, Cycles reference stills |
| Elevation and trees | Yamanashi 2024 LiDAR: 0.5 m DEM and DSM2, 0.25 m orthophoto, classified LAS | CC BY 4.0; fetched in the cloud by `tools/marble_test/yamanashi_sheets.py` |
| Point-cloud tools | PDAL, GDAL, WhiteboxTools (curvature, roughness, geomorphons), `lidR` or the existing stem detector | All open source |
| Species zones | Ministry of the Environment vegetation map (owner's GeoPackage) | Core is natural hinoki forest with *Arachniodes mutica*, 24.7 km²; *verify* licence |
| Stand detail | Yamanashi 20 m forest register (`fr_mesh20m_08le3_2025`) | On the owner's Mac from 17 September; *verify* licence and content |
| Geology | GSJ Geological Map of Fuji Volcano (vector) | Separates the AD 864 Aokigahara lava from older units |
| Trails and caves | OpenStreetMap; Yamanashi 2026 Aokigahara guidelines map | OSM is ODbL |
| Textures | Poly Haven and ambientCG | CC0: bark, rock, moss, litter, forest floor |
| Models | Poly Haven root clusters 01/02, single root, tree stump 02, dead tree trunk, fern 02 | CC0, glTF |
| Hinoki and cypress | ffish.asia CC0 *Chamaecyparis obtusa* scans (Sketchfab); PBRPX CC0 *C. pisifera* trunk scans | *Verify*: downloads need an account, and the content is uninspected |
| Tree generation | A scripted Blender generator, or EZ-Tree (open source, exports glTF); The Grove or SpeedTree if paid is acceptable | A one-session bake-off decides |
| Real floor scan | Trey Brown's Aokigahara forest-floor photogrammetry | Contact only; a permission request can be drafted for the owner to send |
| Photo references | Owner's 14 photos; IMG-013 (Floodmfx, CC0) | IMG-013 lies in LiDAR sheet 08LE9325 |
| Faster cloud renders (optional) | A rented GPU, about $0.26 an hour (AWS g6f) | Only when motion checks need it |
| Real M2 tests without the owner (optional) | A rented M2 Mac mini, about €0.17 an hour with a 24-hour minimum | From the 23 September research; set-up untested |

**Excluded:** anything distributed only in Unreal format (most free Fab assets, MM Props Trees and Rocks) and
Megascans under Unreal-only terms. Using them would mean installing Unreal to convert them.

## Phase 0: clean start and the Mac test

Budget: 2–3 sessions. Owner: about 30 minutes.

| Step | What | Output | Check |
|---|---|---|---|
| 0.1 | Owner creates an empty **private** repository and adds it to the Claude environment. Private removes the publication limits on photos and bought assets | New repository | Session can push to it |
| 0.2 | Seed it: `CLAUDE.md` (the rules), `docs/DECISIONS.md` (one page), this roadmap, the project history, `tools/lighting_stats.py`, frames g–j and the owner's photos as targets | First commit | Nothing else carried over |
| 0.3 | Cloud set-up script run by a SessionStart hook: pinned Godot editors and export templates, lavapipe, Blender/`bpy`, GDAL, PDAL, WhiteboxTools, Python packages | `tools/cloud_setup.sh` | A fresh session renders a test frame unaided |
| 0.4 | Owner picks the look: sunny and dappled (frames g–j, recommended) or soft overcast (IMG-013) | One line in `DECISIONS.md` | Gate numbers fixed to match |
| 0.5 | Build the Mac test app: LiDAR sheet 08LE9335 with its 1,953 real stems; the lighting prototype; a 30 m dense segment at the density that read as forest in UE5.8; `--bench` logs frame time, memory and heat slowdown over 10 minutes | Apple-silicon app, about 83 MB, as a release | Runs headless in the cloud first |
| 0.6 | Verify every *verify* item in the resources table (licences, downloads, Terrain3D on the pinned build) | `docs/RESOURCES.md` with status | Nothing unverified is relied on |
| 0.7 | Owner runs the app with one Terminal command and sends back the JSON | Benchmark file | |

**Decision 0:** Is the dense segment at least 30 fps with MetalFX? Then continue. At 20–30 fps, set a density budget
from the numbers. Below 20 fps, try the three.js/WebGPU fallback on the same scene before building anything else.

## Phase 1: the whole 5 × 5 km plot at base quality

Revised 24 September at the owner's request: build the whole plot first, then raise quality everywhere by rules and
build out from there. This fits the lessons: detail comes from rules that run in every tile, and quality is judged at
random spots across the plot, never in one showcase area. Budget: 6–9 sessions. Owner: plot boundary, one test run,
one walk.

**1A. Fix the plot** (half a session)
- Propose a 5 × 5 km square over the forest core: inside the vegetation map's natural hinoki area (about 24.7 km²),
  containing IMG-013 (sheet 08LE9325) and the main trails. The owner approves it on a map.
- About 208 Yamanashi sheets of 400 × 300 m cover it.

**1B. Measured ground and trees everywhere** (2–3 sessions)
- Batch-fetch the 0.5 m DEM, DSM2 and 0.25 m orthophoto for every sheet in the cloud (roughly 1–2 GB). The raw LAS is
  not needed yet.
- For each sheet: 1 m terrain for Terrain3D; 0.5 m normal, curvature and occlusion bakes; the fields the ground layer
  will use later (slope, curvature, roughness, geomorphons, canopy height, gap fraction, sky-view factor, vegetation
  class, forest-register stand data).
- Detect stems from canopy-height peaks across the plot.
- Checks: at least 80% of stems within 1 m of a peak with height within 10%; no seams between sheets.

**1C. A walkable world** (2–3 sessions)
- Streaming: 250–500 m tiles loaded in a background ring; collision on terrain and trunks; an eye-height walking
  character.
- Trees: placeholder species models at every real stem position, with LODs and impostors, and a canopy heightfield
  beyond 1–2 km.
- Lighting to the sunny target: physical sky and sun, canopy light maps from the sky-view factor, SDFGI or HDDAGI.
- Ground: base materials only (Poly Haven and ambientCG), blended by slope and curvature.
- Checks: the lighting gate at the fixed cameras; 20 random eye-level spots across the plot for the record.

**1D. Mac test 2** (owner, 15 minutes): a scripted walk and flight across the plot at 30 fps or better, with no heat
collapse over 10 minutes.

**Decision 1:** a walkable, real-terrain 5 × 5 km world exists at base quality (about the level of the Godot
prototype). Everything after this raises quality everywhere; nothing shrinks the area.

## Phase 2: raise quality everywhere, by rules

Budget: 8–12 sessions. Owner: two or three rating rounds of about 15 minutes.

**2A. The ground layer, the crux** (4–6 sessions; stop rule below)
1. **Ground grammar** (half a session): from the photos, IMG-013 and the gap audit, write down slab sizes (mostly
   0.3–1.2 m), fissure widths, where moss grows and where rock stays bare, and where litter collects.
2. **Fractured lava as geometry** (Blender in the cloud): fracture displaced surfaces into slabs, ledges,
   near-vertical faces, fissures and modest undercuts; weather the edges; build a kit with three LODs. At run time,
   place and sink the pieces around the walker in every tile from that tile's curvature and roughness fields, so
   terrain and rock read as one surface.
3. **Moss as a surface condition**: masks from orientation, curvature, occlusion and moisture proxies blend moss over
   rock and root in the material. Dimensional moss only where the silhouette needs it.
4. **Roots from real trees**: flared bases on the real stems near the walker; flattened roots that ride over and into
   the rock, split, and disappear under slabs and litter. Poly Haven root clusters and CC0 bark supply the surfaces.
5. **Litter and small plants**: needles, twigs and leaves collected in hollows; ferns small, dark and in sheltered
   pockets.
6. **Evaluation** after each pass:
   - numbers: lighting gate; ground reports (small-gap density, stretch, edge density, ground colour against the
     photos);
   - pictures: 8 random eye-level spots drawn from the whole plot (new ones each round), 2 low views and IMG-013's
     viewpoint;
   - owner: rates each spot 1–5 for "reads as moss-covered lava forest", on a simple private page, mixed with real
     photos.
- **Pass:** median rating 4 or more, none at 2 or below, and the lighting gate still passing.
- **Stop rule:** not passing after 6 sessions. Stop and decide with the owner: accept the best version, lower the
  target, or make rendered stills for chosen views.

**2B. Trees and understorey** (2–3 sessions)
- Species: *Tsuga* then *Chamaecyparis*, following the vegetation map and stand data.
- One-session bake-off between a scripted Blender tree, an EZ-Tree export and the CC0 hinoki scan (if step 0.6
  cleared it). Pick by owner rating.
- LOD0 and LOD1 plus an octahedral impostor for each. Thin sub-canopy stems added statistically, varied in age,
  diameter, lean and damage.
- Check: ratings at new random spots do not drop; trunks read as bases grown into the ground.

**2C. Mac test 3** (owner): the upgraded plot at 30 fps or better.

## Phase 3: polish, then build out

- Polish: 50 random spots across the plot, outliers fixed; release 1.0 of the 5 × 5 km world.
- Build out, only if Phase 2 passed: extend beyond 5 km with the same pipeline, unchanged (the full forest is about
  30 km², and the survey covers the surroundings). Each extension is a batch run plus random-spot checks, not new
  systems.

## Phase 4: optional extras

A Cycles photo mode for stills and fly-throughs from the same data; look-around stops made with Marble from real
photos; ambient sound; seasons and weather; caves, if the municipal cave report's CD yields geometry.

## Owner's decisions (24 September 2026)

1. **A new private repository:** `aokigahara-free-roam`, created by the owner (GitHub refuses repository creation from
   the Claude integration).
2. **The look: sunny and dappled,** matching the valued frames g–j. The lighting gate uses their numbers.
3. **No spending beyond the cloud credit,** unless minimal. So no paid tree tools, bought scans, rented GPUs or rented
   Macs; free resources only.
4. **Forest register: yes.** The owner uploads `fr_mesh20m_08le3_2025.7z` (8.5 MB) from
   `/Users/Shared/Aokigahara-survey-2026-09-17` on the Mac. The MMS colour point cloud and the remaining Pass 2
   handover parts are skipped: neither is needed for the fresh start.
5. **No contact** with the author of the Aokigahara floor scan.

## Start here (for the first session in the new repository)

Attach `andrekaljevic/Aokigahara` read-only as the source, then run Phase 0 steps 0.2–0.6 in the new repository.
The owner chose to build the whole 5 × 5 km plot first (Phase 1) and raise quality everywhere afterwards (Phase 2).

- **Copy in:** this roadmap, `docs/engine_selection/PROJECT_HISTORY.md`, `docs/ENGINE_SELECTION.md` (as reference),
  `tools/lighting_stats.py`, `tools/marble_test/yamanashi_sheets.py`, the Godot prototype in
  `docs/engine_selection/prototypes/godot/`, and the target frames `renders/ue58_baseline/ue58_g`–`j` with
  `lighting_stats.json`. Add the owner's photos and the vegetation GeoPackage when the owner uploads them.
- **Write:** `CLAUDE.md` (the rules above plus these decisions) and `docs/DECISIONS.md` (one page).
- **Work** at normal effort, with no helper-agent teams. Commit after each step.
