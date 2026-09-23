export const meta = {
  name: 'aokigahara-engine-selection',
  description: 'Research, fact-check, prototype and judge non-UE engine paths for a 5x5 km photoreal Aokigahara on an M2 MacBook Air',
  phases: [
    { title: 'Research', detail: 'seven web-research agents: forest lighting parity plus one per option family' },
    { title: 'Verify', detail: 'adversarial fact-check of each research report' },
    { title: 'Prototype', detail: 'headless Godot and three.js WebGPU renders of the real data in this container' },
    { title: 'Judge', detail: 'three independent lenses score every path' },
    { title: 'Synthesize', detail: 'draft the decision record' },
    { title: 'Critique', detail: 'completeness and accuracy review of the draft' },
  ],
}

const SCRATCH = '/tmp/claude-0/-home-user-Aokigahara/f3a7dee1-ddd5-5966-b7a1-ff45901003d9/scratchpad'
const REPO = '/home/user/Aokigahara'

const CONTEXT = `PROJECT CONTEXT (read carefully; it is shared by every agent)
Date: 23 September 2026.
Owner goal: a free-roam (first-person, walkable), photorealistic recreation of a REAL 5 km x 5 km plot of Aokigahara (Jukai forest on the 864 CE Jogan lava flow, NW foot of Mt Fuji, Yamanashi, Japan). Ambition: fidelity at or beyond their UE5.8 attempt.
Owner machine: MacBook Air M2 (Mac14,2), 8-core CPU (4P+4E), 16 GB unified memory, FANLESS; GPU is 8- or 10-core (unknown); internal storage limited (UE5.8 + DDC + agent-built content exhausted it). Owner is in the UK.
History: The owner built the world in Unreal Engine 5.8 (Metal SM6, Lumen/Nanite) on that Mac, driven by Claude Code and OpenAI Codex agents. It burnt a lot of agent usage and disk, the project became corrupted, and UE was deleted. The owner has RULED OUT re-downloading / restarting with UE5.8: "there must be less wasteful paths forward". Do not recommend UE5 (not locally, not on a cloud workstation) except to note it is excluded.
UE5.8 result, as seen in the owner's screenshots (all 1280x800 captures and phone photos): moss-covered lava rocks, soft sun shadows and AO, plausible conifers at mid-distance; flaws: blown-out flat sky, distant canopy as dark flat masses, stretched landscape textures on steep heightmap steps, hard-edged material-layer blotches, stippled/dithered masked materials, noisy stretched bark on roots, sparse understorey. Overall: good indie game, not photoreal.
OWNER'S TOP PRIORITY — NATURAL LIGHTING: the owner says "the most astonishing gain was the natural lighting". The later UE5.8 frames (/tmp/claude-0/-home-user-Aokigahara/f3a7dee1-ddd5-5966-b7a1-ff45901003d9/images/6.jpg to 10.jpg — view them) show: dappled sunlight breaking through a dense conifer canopy onto the floor, a deep sky-occluded understorey (dark interior, bright sky gaps), light shafts and aerial haze in the distance, warm bounced light on rocks and ferns, strong dynamic range with eye adaptation, fern leaves catching sun against dark background. In UE5.8 that came from Lumen (software ray-traced GI and sky occlusion), Virtual Shadow Maps (sharp-to-soft canopy shadows far from the camera), volumetric fog and auto-exposure. ANY recommended alternative must show a credible, evidenced way to reproduce this forest lighting look on the M2 Air — real-time GI, baked/precomputed sky-visibility and canopy-shadow tricks driven by the LiDAR canopy height model, probe volumes, screen-space GI/AO, ray-traced or voxel GI, volumetric fog, etc. Lighting parity is the primary acceptance test for the decision.
Earlier baseline in this repository (${REPO}): a Three.js r180 WebGL viewer (no build step) built by earlier AI sessions — lower fidelity (flat lighting, faceted rocks), 7-8 M triangles and ~90 draw calls at 1280x800; a headless-Chromium audit renderer (tools/audit_render.mjs) already works in cloud containers.
Engine-agnostic assets already in hand: GSI DEM5A 8 m terrain grids (viewer/assets/terrain/*.f32 + json), 467,601 procedural tree placements (data/forest-wide.f32), OSM trails, MoE vegetation classes, GSJ Jogan lava mask, a verified coordinate transform (AEQD origin 138.658E 35.4775N; measured data in EPSG:6676), research dossier (docs/). On the owner's Mac (~916 MB, not in git): Yamanashi Prefecture 2024 point cloud — airborne classified LAS (class 1 surface, 2 ground), 0.5 m DEM/DSM products and 0.5 m relief, MMS vehicle LiDAR (~3 cm spacing, per-point RGB, roads only), MMS trajectory, 20 m forest register with species/stand age (see branch rebuild/measured-2026-09-19, file unreal/AokigaharaUE/Docs/REBUILD_2026-09-19.md). Photo-derived tileable PBR material packs (moss, mossy lava, root moss, trail, understorey) at 1k/2k/4k from owner-supplied Aokigahara photos (branch claude/aokigahara-uhd-assets-5l10c2, viewer/assets/materials_uhd/).
How work gets done: mostly by AI coding agents — Claude Code, including Claude Code on the web in Linux cloud containers (no GPU, 4 CPUs, ~30 GB disk, egress proxy: GitHub + GitHub release assets, npm, PyPI, apt reachable; download.blender.org and some other hosts blocked) — with the owner as human-in-the-loop on the Mac. The owner is usage-sensitive.
Repository branches (read-only via: git -C ${REPO} show origin/<branch>:<path>): main, dev/generational-visual-upgrade, ue5.8/aokigahara-production, rebuild/measured-2026-09-19, claude/aokigahara-uhd-assets-5l10c2, claude/4k-asset-packs-photos-sy83u7.
Rules for every agent: never modify, commit or push anything in ${REPO}; write scratch files only under ${SCRATCH}. Use British English.`

const WEB_METHOD = `Method:
- Load web tools first: ToolSearch with query "select:WebSearch,WebFetch". Research on the live web; your training data may be stale. It is September 2026: look for 2026 releases and announcements and state version numbers with dates.
- Prefer primary sources (official docs, release notes, GitHub repos/issues, vendor posts). Every finding needs a source URL. If something comes from memory with no source, mark confidence 'low' and say so in the claim.
- You may read the repository (read-only). Do not install large software; other agents run the prototypes.
- Judge everything against THIS project: a 5 km x 5 km walkable photoreal forest, fanless M2 MacBook Air 16 GB, built mostly by AI agents, owner wants less waste (disk + agent usage + money) than the UE5.8 attempt.
- Be concise and concrete: summary <= 250 words, 8-20 findings, no padding.`

const TOPICS = [
  {
    key: 'lighting',
    title: 'Reproducing UE5 Lumen-style forest lighting without Unreal (the owner\'s primary criterion)',
    brief: `View the owner's UE5.8 frames first (paths in the context, images 6-10 especially). Then establish, with evidence, how close each non-UE path can get to that lighting on an M2 MacBook Air and by which techniques. Cover: (a) Godot 4.x — SDFGI (and any successor/new GI in 4.5-4.7), VoxelGI, LightmapGI with directional lightmaps, SSIL, SSAO, volumetric fog + fog volumes, directional shadow quality (PSSM splits, soft shadows / PCSS, shadow distance), light probes, sky occlusion under canopy, foliage transmission; the best Godot screenshots/videos of sunlit forests with GI (links). (b) three.js WebGPU / Babylon.js / PlayCanvas — SSGI, GTAO, probe-based GI (DDGI-style irradiance probes on WebGPU, e.g. any three.js/Babylon DDGI or 'light probe volume' implementations), baked lightmaps, volumetric light shafts; links to the best examples. (c) Unity 6 URP APV + SSAO and HDRP SSGI/volumetrics, for comparison. (d) Engine-agnostic 'forest lighting' techniques that do not need real-time GI and scale to 5 km: precomputing sky-visibility / ambient occlusion and a sun-visibility (canopy shadow) texture from the LiDAR canopy height model or the tree instance field (as used in large open-world games, e.g. baked 'forest canopy shadow maps', height-field / terrain shadow maps, 'sky visibility' volumes, Ghost of Tsushima / Horizon / Far Cry / RDR2 GDC talks — link the talks), irradiance volumes baked offline (e.g. with Blender/Cycles), bent-normal AO for foliage, cheap light-shaft techniques, auto-exposure and filmic/AgX tonemapping. (e) What the M2 GPU can afford: cost of SDFGI/SSGI/probe GI at ~1280x800 internal with upscaling (MetalFX/FSR), any measured numbers. Conclude with a ranked recipe per engine for matching images 6-10, the expected shortfall vs Lumen, and which parts could be verified by an agent rendering headlessly in a Linux container.`,
  },
  {
    key: 'godot',
    title: 'Godot Engine 4.x as the engine',
    brief: `Latest stable Godot 4.x as of Sept 2026 and what is in the current dev cycle. Cover: native Metal rendering driver on macOS Apple Silicon (status, maturity vs MoltenVK, MetalFX upscaling support); Forward+ features that matter for a photoreal forest — GI options (SDFGI and any replacement/new GI landed in 4.5-4.7, VoxelGI, LightmapGI, SSIL), SSAO, specular occlusion / bent normals, volumetric fog, TAA / FSR / MetalFX, shadow quality and distance, foliage shading (alpha-to-coverage, subsurface/transmission, wind), physical sky/atmosphere, tonemapping (AgX). Large worlds: double-precision builds, origin shifting. Terrain: Terrain3D (max size, LOD/clipmap, texture layers + height blending, heightmap import formats incl. 16-bit/EXR, instancer for foliage, Mac support, maintenance status) and alternatives. Vegetation at scale: MultiMesh, Terrain3D instancer, Spatial Gardener, ProtonScatter, visibility ranges / HLOD, automatic mesh LOD, impostor plugins, occlusion culling. Streaming/background loading for a 5x5 km world. The best photoreal Godot forest/nature showcases (links). Realistic fidelity ceiling vs UE5. Editor download size and typical project size. macOS editor stability on M2 16 GB. Agent operability: text .tscn/.tres, GDScript/C#, CLI export, rendering screenshots from the CLI (note: --headless disables rendering), Godot MCP servers in 2026. Licence.`,
  },
  {
    key: 'web',
    title: 'Browser / WebGPU stack (continuing the repo Three.js path, or Babylon.js / PlayCanvas)',
    brief: `Three.js latest release (r18x) WebGPURenderer + TSL: production readiness and features (SSGI, GTAO/AO node, TRAA/TAA, SSR, cascaded shadow maps, BatchedMesh, indirect/multi-draw, compute-driven culling, instancing at scale). WebGPU in Safari (macOS 26 Tahoe / Safari 26) and Chrome on Apple Silicon in 2026. Babylon.js latest (IBL shadows, Frame Graph, GPU-driven rendering, Gaussian splats) and PlayCanvas engine (WebGPU, streamed LOD Gaussian splats / SOG format) as alternatives. Browser memory limits on a 16 GB Mac (per-tab GPU memory, Safari limits), streaming a 5x5 km world (tiling, KTX2/Basis, meshopt, 3D Tiles/Cesium), best photoreal WebGPU forest/terrain demos (links). Native wrappers (Tauri/Electron) to escape browser limits. Realistic fidelity ceiling vs UE5 and vs Godot. Hosting a multi-GB world (GitHub Pages limits, Cloudflare R2 etc.). Agent operability: headless Chromium rendering in cloud containers (WebGL already proven in this repo; WebGPU via SwiftShader/lavapipe?). What in the existing repo viewer (viewer/app.js, assets) carries over.`,
  },
  {
    key: 'unity_others',
    title: 'Unity 6 and every other engine or framework (shortlist and eliminate)',
    brief: `Unity 6.x latest as of Sept 2026 on Apple Silicon: HDRP status (any maintenance-mode / deprecation / render-pipeline unification announcements), URP photoreal capability (Adaptive Probe Volumes, SSAO, shadows, GPU Resident Drawer, occlusion), terrain limits, SpeedTree support, streaming; HDRP forest precedent (Book of the Dead); editor + Mac build support disk footprint and Library folder growth; licence/pricing in 2026; Unity AI / MCP / agent operability (YAML scenes, batchmode), expected performance on an M2 Air. THEN, briefly, each of: Bevy (latest 0.1x — virtual geometry/meshlets, atmosphere, SSAO, TAA, Solari and whether it needs hardware RT, Metal via wgpu), Flax Engine (macOS editor, GI, terrain, foliage), O3DE (macOS editor?), Stride, Unigine (macOS?), CryEngine, Wicked Engine, Apple RealityKit / custom Metal. For each: runs its editor/tooling on an M2 Mac? photoreal forest capability? large terrain? maturity? agent operability? Produce a shortlist with explicit elimination reasons. UE5 is excluded by the owner; mention only as excluded.`,
  },
  {
    key: 'capture',
    title: 'Capture-based photorealism: Gaussian splatting / photogrammetry for a real place',
    brief: `State of 3D Gaussian splatting in 2026 for large real places: hierarchical/LOD splats, city/forest scale, streaming formats (PlayCanvas SOG + streamed LOD, Spark / sparkjs, 3D Tiles with KHR_gaussian_splatting, Niantic/Scaniverse SPZ), training tools that run on an Apple Silicon Mac (Brush, OpenSplat, Postshot platform?, RealityScan 2.x licence/platform, Polycam, Luma, XGRIDS LCC), splat support inside Godot / Unity / three.js / Babylon / PlayCanvas. Limitations for a walkable game: no relighting, collisions, wind, thin branches and canopy occlusion in forests, memory. What capture a 25 km2 forest at walking height would need (hours of footage, storage, compute) — and what a solo UK-based owner could realistically do (a trip to Japan capturing trails and hero spots). Legal/etiquette: Japanese drone law (national parks, Fuji-Hakone-Izu), Aokigahara filming sensitivities. Alternative sources: public Yamanashi MMS LiDAR RGB point clouds as point/splat sources; street-level imagery licensing (Google Street View terms forbid reuse — confirm). Conclude with a realistic hybrid recommendation (splat hero areas vs mesh world).`,
  },
  {
    key: 'data_assets',
    title: 'Real-data pipeline and photoreal asset sourcing (engine-agnostic)',
    brief: `PART A, data: Yamanashi 2024 point cloud (geospatial.jp dataset 'yamanashi-pointcloud-2024'): does it cover all of Aokigahara? products (0.5 m DEM, DSM, relief, classified LAS density), licence (CC BY 4.0?), tiling; GSI DEM1A/5A coverage. Individual tree detection from a canopy height model to get REAL stem positions and heights over 25 km2 (lidR, PyCrown, PDAL filters, watershed) and species assignment from the 20 m forest register + MoE vegetation. Turning these into engine inputs: 16-bit heightmap tiles, splat/weight maps, instance lists. Storage for 5x5 km at 0.5 m (10k x 10k samples) and the whole pipeline. Which parts an AI agent in a Linux cloud container can run (PDAL, GDAL, laspy, lidR via pip/conda/apt) vs must run on the Mac (licensed data kept locally). Read the repo branch docs listed in the context. PART B, assets: Fab / Quixel Megascans licensing in 2026 (free period ended? cost now? can they be used outside Unreal, e.g. Godot/web/Unity?), Poly Haven, ambientCG, Sketchfab CC0/CC-BY scans; tree creation — SpeedTree (licence, price, macOS, export to non-UE engines), Blender tree tools (Sapling, The Grove, geometry-nodes generators), EZ-Tree, and whether any scanned or high-quality assets exist for the actual species (Tsuga sieboldii, Chamaecyparis obtusa, Chamaecyparis pisifera, Pinus densiflora, deciduous broadleaves — check the repo dossier for the community list). Impostor baking and LOD tools (Blender add-ons, gltfpack/meshoptimizer, Godot impostor plugins). How the repo's photo-derived material packs can be reused. Blender as a headless, agent-scriptable asset pipeline (bpy on PyPI).`,
  },
  {
    key: 'hw_agentflow',
    title: 'M2 MacBook Air rendering ceiling, and AI-agent workflow efficiency',
    brief: `PART A, hardware: M2 MacBook Air (Mac14,2) 8/10-core GPU, 16 GB, fanless — FP32 throughput, 100 GB/s bandwidth, Metal 3 feature set, no hardware ray tracing (M3+), MetalFX availability, thermal throttling under sustained GPU load (measured benchmarks), real game data points on M2 Air, any Godot / WebGPU / Unity benchmark numbers on M2. Realistic budget for a dense forest at ~1280x800 internal with upscaling: triangles, draw calls, shadow cascades, foliage overdraw, texture memory. What fidelity is realistic for 5 km free-roam; what a newer Mac (M4/M5 MacBook Pro or Mac mini) would change, with UK prices — as an optional note only. External SSD for projects/data (Thunderbolt/USB speeds on M2 Air). PART B, agent workflow: why UE5 burnt agent usage (binary .uasset, GUI-only operations, long shader/C++ compiles, huge logs, agent blind to the viewport, human taking phone photos); which engines let a Claude Code agent in a Linux cloud container WITHOUT a GPU render frames headlessly to self-verify (Mesa lavapipe/llvmpipe, SwiftShader, xvfb) — Godot, three.js/Babylon WebGPU/WebGL, Blender, Bevy, Unity batchmode; MCP servers (Godot MCP, Blender MCP, Unity MCP) maturity in 2026; text-diffable formats; a token-efficient loop (fixed audit cameras, scripted scenes, image metrics); how to split work between the cloud agent (data pipeline, code, headless renders) and the Mac (final performance checks); storage hygiene on the Mac (external SSD, keep source data off the internal disk, git LFS). Claude Code usage-saving practices (plan mode, scoped sessions, when to use or avoid multi-agent runs).`,
  },
]

const RESEARCH_SCHEMA = {
  type: 'object',
  properties: {
    topic: { type: 'string' },
    latest_versions: { type: 'string', description: 'Current versions as of Sept 2026, with release dates' },
    summary: { type: 'string', description: '<= 250 words' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          claim: { type: 'string' },
          source_url: { type: 'string' },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
          relevance: { type: 'string', description: 'why it matters for this project' },
        },
        required: ['claim', 'source_url', 'confidence'],
      },
    },
    fidelity_ceiling: { type: 'string' },
    m2_air_feasibility: { type: 'string' },
    storage_footprint: { type: 'string' },
    agent_operability: { type: 'string' },
    cost_licence: { type: 'string' },
    risks: { type: 'array', items: { type: 'string' } },
    unknowns: { type: 'array', items: { type: 'string' } },
  },
  required: ['topic', 'summary', 'findings', 'fidelity_ceiling', 'm2_air_feasibility', 'storage_footprint', 'agent_operability', 'risks'],
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    topic: { type: 'string' },
    checks: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          claim: { type: 'string' },
          verdict: { type: 'string', enum: ['confirmed', 'partially', 'refuted', 'unverifiable'] },
          correction: { type: 'string' },
          source_url: { type: 'string' },
        },
        required: ['claim', 'verdict'],
      },
    },
    overall_reliability: { type: 'string' },
    important_omissions: { type: 'array', items: { type: 'string' } },
  },
  required: ['topic', 'checks', 'overall_reliability'],
}

const PROTO_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    succeeded: { type: 'boolean' },
    versions: { type: 'string' },
    environment_steps: { type: 'string', description: 'exact commands that worked' },
    render_files: { type: 'array', items: { type: 'string' }, description: 'absolute paths of saved renders' },
    timings: { type: 'string' },
    disk_used: { type: 'string' },
    what_worked: { type: 'array', items: { type: 'string' } },
    blockers: { type: 'array', items: { type: 'string' } },
    implications: { type: 'string', description: 'what this means for an agent-driven workflow with this engine' },
  },
  required: ['name', 'succeeded', 'environment_steps', 'render_files', 'what_worked', 'blockers', 'implications'],
}

const PROTOS = [
  {
    key: 'godot',
    prompt: `${CONTEXT}

TASK: prove or disprove, empirically, that an AI agent in THIS Linux cloud container (no GPU, 4 CPUs) can build and render a Godot 4 scene from text files only, using this repository's real data, so that it could self-verify visual work without the owner's Mac. Work only in ${SCRATCH}/proto/godot/. Time-box yourself to roughly 40 minutes of effort and report partial results honestly.

Steps:
1. Find the latest stable Godot 4 release (https://api.github.com/repos/godotengine/godot/releases/latest or the releases page). Download the Linux x86_64 editor zip from the GitHub release assets (these are reachable; downloads.tuxfamily.org is not). Record the version.
2. Software Vulkan: apt-get install -y mesa-vulkan-drivers (lavapipe). Run Godot under: xvfb-run -a -s "-screen 0 1280x800x24". Try --rendering-driver vulkan --rendering-method forward_plus first; if that fails try mobile, then gl_compatibility (OpenGL via llvmpipe). Do NOT pass --headless (it disables rendering). Consider running the project with --path and a main scene, or with --script.
3. Build a minimal project entirely from text (project.godot + .tscn and/or GDScript) that at runtime:
   - loads ${REPO}/viewer/assets/terrain/local-height.f32 (257 x 257 float32 little-endian, row-major index=row*width+col, 8 m step; read local-height.json for bounds; values are metres above sea level, subtract 900 to match the placements' y) into an ArrayMesh terrain;
   - applies a StandardMaterial3D with triplanar UVs using ${REPO}/viewer/assets/materials_v2/moss_diff_1k.jpg, moss_nor_gl_1k.jpg, moss_rough_1k.jpg (load images at runtime with Image.load_from_file / ImageTexture);
   - loads ${REPO}/viewer/assets/tree-library-v2.glb at runtime via GLTFDocument + GLTFState and scatters a few hundred instances (MultiMeshInstance3D per mesh) using records from ${REPO}/viewer/assets/forest-instances.f32 (6 float32 per record: x east m, y = elevation-900, z south m, uniform scale, yaw radians, class) within ~150 m of a camera near the origin; pick the tsuga/hinoki high-LOD meshes by name;
   - LIGHTING IS THE PRIORITY (the owner's key criterion is UE5.8's natural forest lighting — view /tmp/claude-0/-home-user-Aokigahara/f3a7dee1-ddd5-5966-b7a1-ff45901003d9/images/6.jpg to 10.jpg first): a low-ish sun DirectionalLight3D with shadows tuned for dappled canopy light (PSSM, soft shadows, max distance ~150 m), trees dense enough around the camera that the canopy actually shades the floor; WorldEnvironment with a sky (PhysicalSkyMaterial or ProceduralSkyMaterial), AgX tonemap and auto-exposure, SSAO, SSIL, SDFGI (note if unavailable on the working renderer), volumetric fog for aerial haze/light shafts;
   - Camera3D ~1.7 m above the terrain looking into the forest; waits enough frames for GI to settle (e.g. 60), saves get_viewport().get_texture().get_image() as PNG at 1280x800 to ${SCRATCH}/proto/godot/out/, then quits.
   Save a second frame with SDFGI off for comparison. If time permits, add a cheap engine-agnostic trick and a third frame: darken ambient/sky light under the canopy using a top-down canopy-density (sky-visibility) texture computed from the tree placements, to test whether it approximates the Lumen interior darkening.
4. Record which renderer worked, seconds per frame, total wall time, errors, disk used by Godot + mesa.
5. Delete downloaded zips at the end; keep the extracted Godot binary and your project files (small).
Never modify, commit or push the repository.`,
  },
  {
    key: 'webgpu',
    prompt: `${CONTEXT}

TASK: determine, empirically, whether THIS cloud container can render three.js WebGPU (WebGPURenderer + TSL) headlessly for agent self-verification, and compare it with WebGL2. Work only in ${SCRATCH}/proto/web/. Time-box yourself to roughly 40 minutes of effort and report partial results honestly.

Chromium for Playwright is pre-installed at /opt/pw-browsers (PLAYWRIGHT_BROWSERS_PATH is set; do not run "playwright install"; if the npm playwright version expects a different Chromium revision, launch with executablePath pointing at the installed chromium binary under /opt/pw-browsers). npm registry is reachable: npm init -y && npm i playwright three@latest.

Steps:
1. Launch Chromium headless with candidate flag sets and record, for each, whether navigator.gpu exists, whether requestAdapter() returns an adapter, and the adapter info. Try at least: --enable-unsafe-webgpu with --use-webgpu-adapter=swiftshader; --enable-unsafe-webgpu --enable-features=Vulkan --use-vulkan=swiftshader; and (after apt-get install -y mesa-vulkan-drivers) --enable-unsafe-webgpu --enable-features=Vulkan --use-vulkan=native --use-angle=vulkan under xvfb-run. Try both the full chromium and chromium_headless_shell if present.
2. If any combination yields an adapter: serve files with python3 -m http.server and render a small scene with three/webgpu + TSL: terrain from ${REPO}/viewer/assets/terrain/local-height.f32 (257 x 257 float32 LE, row-major, 8 m step, see local-height.json; metres ASL), moss PBR from ${REPO}/viewer/assets/materials_v2/, instanced trees from ${REPO}/viewer/assets/tree-library-v2.glb near the camera (placements in ${REPO}/viewer/assets/forest-instances.f32: 6 float32 per record x, y=elev-900, z, scale, yaw, class), shadows, sky, and the AO / post-processing nodes available in the installed three.js version (e.g. ao / GTAO, TRAA; note whether an SSGI node exists and use it if it does). LIGHTING IS THE PRIORITY: the owner's key criterion is UE5.8's natural forest lighting (view /tmp/claude-0/-home-user-Aokigahara/f3a7dee1-ddd5-5966-b7a1-ff45901003d9/images/6.jpg to 10.jpg first) — aim for dappled sun through a dense canopy (enough trees around the camera, soft shadow maps), a darker sky-occluded understorey and AgX/ACES tonemapping; report honestly how close it gets. Screenshot at 1280x800 to ${SCRATCH}/proto/web/out/ and time it.
3. Whatever happens with WebGPU, confirm the repository's existing WebGL2 viewer renders here: python3 ${REPO}/launch_viewer.py --port 8765 --quiet (in background), then run a copy of ${REPO}/tools/audit_render.mjs from your proto dir (so that "playwright" resolves) against http://127.0.0.1:8765/viewer/ with ${REPO}/harness/cams2.json at 1280x800, writing to ${SCRATCH}/proto/web/audit/. Keep at most 2 cameras if it is slow. Kill the server afterwards.
4. Record the three.js version and which post-processing / GI features exist in it.
Never modify, commit or push the repository.`,
  },
]

const VISUAL_DIAGNOSIS = `ORCHESTRATOR'S DIAGNOSIS OF THE UE5.8 FRAMES (images: /root/.claude/uploads/f3a7dee1-ddd5-5966-b7a1-ff45901003d9/*.jpg and *.png, /tmp/claude-0/-home-user-Aokigahara/f3a7dee1-ddd5-5966-b7a1-ff45901003d9/images/1.jpg..4.jpg, 5.webp and 6.jpg..10.jpg; you may view them):
Doing real work: Lumen-style soft GI and AO, virtual-shadow-map soft sun shadows, slope-driven moss on rocks, scanned-looking rocks.
Deficits, mostly NOT engine-specific: (1) exposure/sky: sky clipped to white, flat; (2) far canopy reads as dark flat masses (no foliage transmission, impostor/HLOD darkening); (3) landscape texture stretching where the heightmap has 1 m steps — terrain data/tessellation, not the engine; (4) hard-edged material-layer blotches (weight blend without height blend); (5) stippled/dithered masked materials (dithered opacity without a temporal resolve); (6) noisy, over-contrasted stretched bark on roots and logs (UV/triplanar); (7) sparse, uniform understorey; (8) no ground clutter (needles, twigs, litter) at scale. Images 6-10 are the strongest: dappled canopy sunlight, a deep sky-occluded understorey, haze and warm bounce — the owner's most valued result, driven by Lumen + VSM + volumetric fog + auto-exposure. Verdict: 'good indie game' overall with genuinely striking lighting, not photoreal; the gap to photoreal is mostly assets, art direction, terrain data and density — which any engine needs — plus GI quality, which is UE's genuine advantage.`

const PATHS = `CANDIDATE PATHS (score all; you may add one if evidence shows a better option):
P1 Godot 4 native macOS app (Forward+ on Metal; Terrain3D or custom clipmap terrain; instanced vegetation with LOD + impostors; real LiDAR terrain and tree positions).
P2 Web / WebGPU: evolve the repository's Three.js viewer to WebGPURenderer + TSL (or move to Babylon.js / PlayCanvas); runs in Safari/Chrome; shareable URL.
P3 Unity 6 (URP, or HDRP if still viable).
P4 Best of the rest from the shortlist (e.g. Bevy code-first, or Flax) — name it.
P5 Capture-led hybrid: Gaussian-splat / photogrammetry hero areas from an on-site capture trip, embedded in a mesh world built with P1 or P2.
P6 Non-interactive reference: Blender/Cycles stills and fly-throughs (not free-roam) — score it honestly as a fidelity reference and as an asset-pipeline tool, not as the product.`

const LENSES = [
  { key: 'fidelity', name: 'Fidelity-first', desc: 'What gets closest to, and beyond, the UE5.8 frames on the REAL hardware at a 5 km scale?', weights: 'lighting 0.30, fidelity 0.25, mac_feasibility 0.20, agent_efficiency 0.10, storage 0.05, cost 0.05, time_to_first_result 0.05' },
  { key: 'waste', name: 'Waste-first (the owner\'s stated priority)', desc: 'Least disk, agent usage and money per unit of visible progress; how fast the owner sees a convincing result.', weights: 'agent_efficiency 0.25, lighting 0.20, storage 0.15, fidelity 0.10, time_to_first_result 0.15, mac_feasibility 0.05, cost 0.10' },
  { key: 'longevity', name: 'Risk and longevity', desc: 'Which path is least likely to dead-end: engine maturity and trajectory on Apple Silicon, data/asset portability, ability to switch later, bus factor of key plugins.', weights: 'lighting 0.20, fidelity 0.15, mac_feasibility 0.20, agent_efficiency 0.20, time_to_first_result 0.10, storage 0.05, cost 0.10' },
]

const JUDGE_SCHEMA = {
  type: 'object',
  properties: {
    lens: { type: 'string' },
    scores: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          path: { type: 'string' },
          lighting: { type: 'number', description: 'how close to the UE5.8 natural forest lighting (images 6-10) on the M2 Air' },
          fidelity: { type: 'number' },
          mac_feasibility: { type: 'number' },
          storage: { type: 'number' },
          agent_efficiency: { type: 'number' },
          cost: { type: 'number' },
          time_to_first_result: { type: 'number' },
          weighted_total: { type: 'number' },
          rationale: { type: 'string' },
        },
        required: ['path', 'lighting', 'fidelity', 'mac_feasibility', 'storage', 'agent_efficiency', 'cost', 'time_to_first_result', 'weighted_total', 'rationale'],
      },
    },
    winner: { type: 'string' },
    runner_up: { type: 'string' },
    honest_ceiling: { type: 'string', description: 'what fidelity is realistically reachable on this Mac for 5 km free-roam, and what would be needed to go beyond' },
    flip_conditions: { type: 'array', items: { type: 'string' } },
    must_do_regardless: { type: 'array', items: { type: 'string' } },
    key_risks: { type: 'array', items: { type: 'string' } },
  },
  required: ['lens', 'scores', 'winner', 'runner_up', 'honest_ceiling', 'flip_conditions', 'must_do_regardless', 'key_risks'],
}

const CRITIC_SCHEMA = {
  type: 'object',
  properties: {
    issues: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          location: { type: 'string' },
          problem: { type: 'string' },
          fix: { type: 'string' },
        },
        required: ['severity', 'problem', 'fix'],
      },
    },
    verdict: { type: 'string' },
  },
  required: ['issues', 'verdict'],
}

// ---------- Research -> Verify (pipelined per topic), Prototypes alongside ----------
phase('Research')
const researchRun = pipeline(
  TOPICS,
  t => agent(`${CONTEXT}\n\nYOUR TOPIC: ${t.title}\n${t.brief}\n\n${WEB_METHOD}`, { label: `research:${t.key}`, phase: 'Research', schema: RESEARCH_SCHEMA }),
  (r, t) => r
    ? agent(`${CONTEXT}\n\nYou are an adversarial fact-checker. Another agent researched "${t.title}" and produced the report below. Pick the 6-10 claims the engine decision most depends on (versions and dates, feature availability on macOS / Apple Silicon, licence and cost, storage, performance, headless/agent operability) and try to REFUTE each with fresh primary sources on the live web (load tools first with ToolSearch "select:WebSearch,WebFetch"). 'refuted' and 'partially' need a source and a correction; use 'unverifiable' when you cannot find one. Then list important omissions: facts that would change the decision and that the report missed (with sources). Be concise.\n\nREPORT:\n${JSON.stringify(r)}`, { label: `verify:${t.key}`, phase: 'Verify', schema: VERIFY_SCHEMA })
        .then(v => ({ topic: t.key, title: t.title, report: r, factcheck: v }))
    : null,
)
const protoRun = parallel(PROTOS.map(p => () => agent(p.prompt, { label: `proto:${p.key}`, phase: 'Prototype', schema: PROTO_SCHEMA })))

const [researchedRaw, protosRaw] = await Promise.all([researchRun, protoRun])
const researched = researchedRaw.filter(Boolean)
const protos = protosRaw.filter(Boolean)
const missingTopics = TOPICS.filter(t => !researched.find(r => r.topic === t.key)).map(t => t.key)
if (missingTopics.length) log(`Research missing for: ${missingTopics.join(', ')}`)
if (protos.length < PROTOS.length) log(`Only ${protos.length}/${PROTOS.length} prototypes returned`)
log(`Researched ${researched.length} topics, ${protos.length} prototypes returned`)

const bundle = JSON.stringify(researched)
const protoBundle = JSON.stringify(protos)

// ---------- Judge (barrier: needs all evidence) ----------
phase('Judge')
const judgements = (await parallel(LENSES.map(l => () => agent(
  `${CONTEXT}\n\n${VISUAL_DIAGNOSIS}\n\nYou are one of three independent judges. Your lens: ${l.name}. ${l.desc}\nWeights for weighted_total: ${l.weights}.\n\n${PATHS}\n\nEVIDENCE: research reports, each followed by an adversarial fact-check. Where they disagree, trust the fact-check; ignore claims it refuted.\n${bundle}\n\nPROTOTYPE RESULTS from this cloud container (agent self-verification evidence; you may view the render files):\n${protoBundle}\n\nThe owner's most valued gain from UE5.8 was the natural lighting (images 6-10): score 'lighting' as how close each path can credibly get to that look on the M2 Air, based on evidence (research, fact-checks, prototype renders), not hope. Score every path 1-10 on each criterion (10 = best for the project; for storage and cost, 10 = least), compute weighted_total with your weights, choose a winner and runner-up, and state what would flip the decision. Be concrete and honest: if no path on this Mac can reach 'beyond UE5.8' for a 5 km world, say so and say what can. List what must be done regardless of engine.`,
  { label: `judge:${l.key}`, phase: 'Judge', schema: JUDGE_SCHEMA },
)))).filter(Boolean)

// ---------- Synthesize ----------
phase('Synthesize')
const draftPath = `${SCRATCH}/ENGINE_SELECTION_draft.md`
const synth = await agent(
  `${CONTEXT}\n\n${VISUAL_DIAGNOSIS}\n\n${PATHS}\n\nEVIDENCE (research + fact-checks):\n${bundle}\n\nPROTOTYPES:\n${protoBundle}\n\nJUDGEMENTS (three lenses):\n${JSON.stringify(judgements)}\n\nTASK: write the project's engine-selection decision record as Markdown to ${draftPath} (create ${SCRATCH} if needed; do NOT write into the repository). Audience: the owner (capable but not an engine specialist) and future AI-agent sessions that will start cold from this file. British English, plain and direct, no hype, no emoji. Required sections:\n1. Decision in one paragraph (the recommended path, the runner-up, and the one-line reason UE5.8 is not needed).\n2. What the UE5.8 attempt actually achieved and why (what is engine-specific vs portable) — short.\n3. The honest ceiling: what fidelity is realistic on a fanless M2 Air 16 GB for 5 km free-roam, and what 'beyond' would require.\n4. Lighting parity — the owner's most valued gain from UE5.8 was the natural lighting (images 6-10). Explain what produced it in UE (Lumen, VSM, volumetric fog, auto-exposure), and give the recommended path's concrete recipe to reproduce it (real-time features + precomputed canopy sky-visibility/sun-visibility from LiDAR, etc.), the expected shortfall, and how it will be measured against the UE5.8 frames. Cite prototype renders.
5. Options compared: one table (path x lighting, fidelity, Mac feasibility, disk, agent efficiency, cost, first-result time) with the judges' consolidated scores, then 2-4 sentences per path including why it lost.\n6. Why the recommended path is less wasteful: disk budget in GB, agent-usage practices, what runs in the cloud container vs on the Mac, headless self-verification evidence from the prototypes (cite render file paths).\n7. What carries over from this repository and from the owner's local data (exact paths/branches).\n8. Phased plan: milestone 0 (set-up, with sizes), milestone 1 = a small vertical slice (e.g. 250-500 m square from real 0.5 m LiDAR) with acceptance criteria and fixed audit cameras, then scale-out to 5 x 5 km with streaming/LOD strategy; for each milestone what the agent does and what the owner does on the Mac.\n9. Must-do regardless of engine (assets, terrain data, lighting/exposure, density).\n10. Risks and flip conditions (what would make us switch).\n11. Open questions for the owner (at most 5, e.g. GPU core count, free disk, budget, target audience/platform, willingness to travel for capture).\n12. Sources: every external claim linked inline or in a numbered list — only claims that survived fact-checking; flag anything unverified.\nKeep it under ~3,000 words. Return the file path and a 150-word summary of the decision.`,
  { label: 'synthesize', phase: 'Synthesize' },
)

// ---------- Critique ----------
phase('Critique')
const critique = await agent(
  `${CONTEXT}\n\nYou are a completeness and accuracy critic. Read the draft decision record at ${draftPath}. Compare it against the evidence below. Find: claims not supported by the evidence or contradicted by the fact-checks; stale or wrong version numbers; missing considerations that would change the owner's decision (disk, usage, cost, Mac limits, legal/licensing, data availability); internal contradictions; places where the plan is vague where it should be concrete; anything that recommends UE5 despite the owner ruling it out; over-claiming of fidelity. You may use ToolSearch "select:WebSearch,WebFetch" to check a claim. Do not edit the file; return issues with concrete fixes.\n\nEVIDENCE:\n${bundle}\n\nPROTOTYPES:\n${protoBundle}\n\nJUDGEMENTS:\n${JSON.stringify(judgements)}`,
  { label: 'critique', phase: 'Critique', schema: CRITIC_SCHEMA },
)

return { draftPath, synth, critique, judgements, protos, researched, missingTopics }
