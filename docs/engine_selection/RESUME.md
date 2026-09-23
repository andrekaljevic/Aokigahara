# Engine selection — paused work, and how to resume it

**Status, 23 September 2026, 19:30 UTC: resumed.** The research phase and both prototypes have
finished; fact-checking, judging and the decision record are still running. The raw results are
checkpointed in `wip/` and `prototypes/` as they arrive. No engine decision has been made yet.
Nothing below is a recommendation.

Headline prototype results. An agent in the cloud container, with no GPU and no Mac, built and
rendered the repository's real terrain, trees and materials in both engines, and scored the renders
against the UE5.8 lighting baseline with `tools/lighting_stats.py`. The full reports are in
`wip/proto_godot.json` and `wip/proto_webgpu.json`; the renders and their scores are in
`prototypes/`.

- **Godot 4.7.2 (Forward+ on software Vulkan).** The SDFGI render meets four of the five baseline
  targets. It misses only the warm-highlight target.
- **three.js r186 WebGPU.** It rendered, and a baked canopy sky-visibility map gave the plain
  render a dappled look. But its screen-space GI pass broke the shadows. The plain renders meet
  one or two of the five targets. The best-looking one has too many sunflecks and over-blue shade.

(Earlier status: paused at the owner's request about 25 minutes into the research phase.)

## The question being answered

The owner abandoned the UE5.8 build. It exhausted the fanless M2 MacBook Air (16 GB) and its
storage, used a great deal of agent usage, and the project became corrupted. Re-installing
UE5.8 is ruled out. The question is which less wasteful path can reach, and ideally beat, the
fidelity of the UE5.8 frames for a walkable, photorealistic 5 km × 5 km plot of Aokigahara.

**The primary acceptance test is lighting.** The owner's own words: "the most astonishing gain
was the natural lighting". That look is shown in `renders/ue58_baseline/ue58_g`–`ue58_j` and is
quantified in `renders/ue58_baseline/lighting_stats.json` by `tools/lighting_stats.py`. See
`renders/ue58_baseline/README.md` for what the numbers mean.

## What is saved

| Path | What it is |
|---|---|
| `renders/ue58_baseline/` | The owner's UE5.8 frames, and the lighting metrics that define the target |
| `tools/lighting_stats.py` | Measures lighting the same way for any engine's renders |
| `docs/engine_selection/workflow/aokigahara-engine-selection.js` | The full multi-agent research workflow script. It holds the complete project context, the seven research briefs, two prototype briefs, the fact-check, judge, synthesis and critique stages, and the scoring weights with lighting as the heaviest criterion |
| `docs/engine_selection/wip/research_godot.json` | **Completed** research report on Godot 4.x: 19 sourced findings (not yet fact-checked) |
| `docs/engine_selection/wip/sources_consulted.md` | 126 searches and pages the two interrupted agents (lighting parity, Web/WebGPU) had reached. Leads only |
| `docs/engine_selection/wip/webgpu_probe/` | Scripts and one render from an interrupted agent's headless WebGPU test (below) |

## Research status

| Stage | Status |
|---|---|
| Research: Godot 4.x | **Done**, saved, not yet fact-checked |
| Research: lighting parity without UE (the primary criterion) | Interrupted; sources saved |
| Research: Web / WebGPU (three.js, Babylon.js, PlayCanvas) | Interrupted; sources and probe saved |
| Research: Unity 6 and other engines; Gaussian-splat capture; real-data pipeline and assets; M2 Air ceiling and agent-usage efficiency | Not started |
| Prototypes: headless Godot render of the real terrain and trees; three.js WebGPU render | Not started as their own agents; one WebGPU probe was done incidentally (below) |
| Fact-check, judges, synthesis, critique | Not started |

## Interim findings

These are single-source and not yet fact-checked. Treat them as leads.

**Godot 4.x** (`wip/research_godot.json`)
- **Versions.** 4.7.2 is the latest stable (18 Aug 2026). 4.8 is at dev6 (15 Sep 2026). Runs on Metal on Apple Silicon, with MetalFX upscaling. MIT licence, about a 171 MB download, text-based scenes, fully drivable from the command line.
- **Lighting.** Godot has nothing equivalent to Lumen or Virtual Shadow Maps. Its large-world real-time GI is still SDFGI. The proposed successor, HDDAGI, is an unmerged pull request (#119869).
- **Metal bug.** Reported: in 4.7, SDFGI on Metal drops bounced light from the sun and other lights. The report says it is fixed only in 4.8 (PR #122675), so a 4.7 prototype would need the Vulkan/MoltenVK fallback or a 4.8 build.
- **Recipe for the UE5.8 look (judgement, not measured).** Plausible within about 150 m of the camera:
  - soft 4-band shadows (PSSM + PCSS) for dappled sun;
  - SDFGI with sky light, or SSIL/SSAO, for bounce and occlusion;
  - volumetric fog for shafts and haze;
  - AgX tonemapping with auto-exposure;
  - a shader term driven by the LiDAR canopy-height model to fake distant canopy shadow and interior darkness, which Godot cannot compute itself.
- **Terrain.** The Terrain3D plugin fits: clipmap LOD, 32 height-blended textures, 16/32-bit heightmap import, a tree instancer. Its own docs call Metal support "not clear".

**Web / WebGPU** (interrupted agent's probe, `wip/webgpu_probe/`)
- **Library versions seen on npm today:** three 0.186.0 (it ships a screen-space GI node, `SSGINode`), @babylonjs/core 9.27.1, playcanvas 2.22.4, @playcanvas/splat-transform 3.6.4.
- **Headless WebGPU works in this container.** The pre-installed headless Chromium 141 exposes a WebGPU adapter (SwiftShader, CPU) once the page is served over HTTP.
- **One workaround needed.** three r186 needs a small shim, because it passes a texture-view `swizzle` property that Chromium 141 rejects.
- **Timing.** With it, three r186 WebGPU rendered a placeholder forest at 960 × 600:
  - without GI: about 0.65 s per frame;
  - with its screen-space GI: about 1.8 s per frame.
- **What this proves.** An agent can render and inspect WebGPU frames, including GI, without the Mac. It says nothing about the achievable look: the render is placeholder geometry (`three186_webgpu_ssgi_swiftshader.jpg`).
- **Blocked host.** `cdn.playwright.dev` is blocked here, so Playwright cannot download a newer Chromium. Use the pre-installed build.

**Container facts for the next session**
- GitHub release downloads, npm, PyPI and apt are reachable. `download.blender.org` and `downloads.tuxfamily.org` are not.
- Mesa lavapipe (software Vulkan) is installable with `apt-get install -y mesa-vulkan-drivers`, for a headless Godot test under `xvfb-run`.

## How to resume

The workflow cache from this session cannot be carried into a new session. To resume:

1. Open a Claude Code session on branch `claude/aokigahara-engine-selection-tqyqx6` and read this
   file.
2. Re-run the workflow with the Workflow tool, passing
   `scriptPath: docs/engine_selection/workflow/aokigahara-engine-selection.js`.
   - Update the date and the scratchpad path in its `SCRATCH` constant and in the image paths
     under `/tmp/claude-0/...`; they point at this session's scratch space.
   - Point the image paths at `renders/ue58_baseline/` instead.
   - To avoid repeating the finished Godot research, remove the `godot` entry from `TOPICS` and
     feed `docs/engine_selection/wip/research_godot.json` into the verify stage.
   - The container has 4 CPUs, so the workflow runs two agents at a time. The full run is about
     21 agents and roughly an hour.
3. The workflow ends with a draft decision record. Finalise it as
   `docs/ENGINE_SELECTION.md`, commit it to this branch, and update draft PR #1.

Owner's open questions that would sharpen the decision (answer any time):
- GPU core count: check System Settings → General → About, or run `system_profiler SPDisplaysDataType`.
- Free disk space, and whether an external SSD is available.
- Budget, if any: software or a newer Mac.
- Who the world is for: yourself on the Mac, or shared with others (for example as a web link).
- Whether a trip to Aokigahara to capture photos or video is conceivable.
