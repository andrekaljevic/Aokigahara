# Engine selection — research record and how to pick it up

**Status, 23 September 2026: complete.** The decision record is `docs/ENGINE_SELECTION.md`. It
recommends a Godot 4 native macOS app fed by an engine-agnostic LiDAR pipeline, with three.js WebGPU
as the runner-up. This folder holds the evidence behind it. The next piece of work is milestone 0 in
section 8 of the decision record, which needs the owner's answers to its section 11 first.

The research was paused once at the owner's request, about 25 minutes in, and resumed the same day.
Nothing was lost; the one report finished before the pause was reused.

## The question that was answered

The owner abandoned the UE5.8 build. It exhausted the fanless M2 MacBook Air (16 GB) and its
storage, used a great deal of agent usage, and the project became corrupted. Re-installing UE5.8
was ruled out. The question was which less wasteful path could reach, and ideally beat, the
fidelity of the UE5.8 frames for a walkable, photorealistic 5 km × 5 km plot of Aokigahara.

**The primary acceptance test is lighting.** In the owner's words: "the most astonishing gain was
the natural lighting". That look is shown in `renders/ue58_baseline/ue58_g`–`ue58_j` and is
measured by `tools/lighting_stats.py`. `renders/ue58_baseline/README.md` explains the numbers,
including a correction made during the research.

## What is here

| Path | What it is |
|---|---|
| `wip/research_*.json` | Seven research reports: lighting parity without UE, Godot, Web/WebGPU, Unity and other engines, Gaussian-splat capture, the data pipeline and assets, and the M2 Air ceiling with agent-usage efficiency |
| `wip/verify_*.json` | An adversarial fact-check of each report. Where a report and its fact-check disagree, the fact-check wins |
| `wip/proto_godot.json`, `wip/proto_webgpu.json` | The two prototype reports: what ran in the GPU-less container, timings, disk use and lighting scores |
| `wip/judge_*.json` | Three independent verdicts (fidelity-first, waste-first, risk and longevity). All three chose Godot, with WebGPU second |
| `wip/ENGINE_SELECTION_draft.md` | The synthesis agent's draft, before the orchestrator's corrections |
| `prototypes/godot/` | The Godot project: three text files, the run script, renders and their scores |
| `prototypes/webgpu/` | The three.js r186 WebGPU page, run scripts, renders and logs |
| `prototypes/lighting_stats_prototypes.json` | Every prototype render scored with the corrected metrics |
| `workflow/aokigahara-engine-selection.js` | The multi-agent workflow that produced all of this, as last run |
| `wip/sources_consulted.md`, `wip/webgpu_probe/` | Leads and an early probe from the two agents interrupted by the pause |

Some research reports quote the withdrawn per-pixel `shadow_blue_ratio` (targets 1.16–1.73). That
metric was JPEG noise; ignore it. The corrected targets are in `renders/ue58_baseline/README.md`
and section 4 of the decision record.

## Recipes for the cloud container

These are recorded so that the next agent does not rediscover them.

**Godot, headless, with the full Forward+ renderer**
- Download the Linux x86_64 editor from the GitHub release assets (`downloads.tuxfamily.org` is
  blocked).
- Run `apt-get install -y mesa-vulkan-drivers` to get lavapipe, a software Vulkan.
- Run under `xvfb-run -a -s "-screen 0 1280x800x24"` with `--rendering-driver vulkan
  --rendering-method forward_plus`. Do not pass `--headless`: it disables rendering.
- SDFGI, SSAO, SSIL, volumetric fog, 4-split PSSM, AgX and auto-exposure all work.
- Expect about 7 s per frame at 5 M triangles and about 25 s of compile per launch, so 3–4 minutes
  per settled still.
- See `prototypes/godot/run_all.sh`.

**three.js WebGPU, headless**
- Use the global Playwright at `/opt/node22/lib/node_modules/playwright` with the pre-installed
  Chromium 141. `cdn.playwright.dev` is blocked, so a newer Chromium cannot be downloaded.
- Serve the page over HTTP. `navigator.gpu` is missing on `about:blank` and on `file://` pages.
- Launch with `--enable-unsafe-webgpu --no-sandbox --enable-features=Vulkan --use-vulkan=swiftshader
  --use-angle=swiftshader --ignore-gpu-blocklist --disable-vulkan-surface`.
- three r186 passes a texture-view `swizzle` property that Chromium 141 rejects. Strip it with the
  shim in `prototypes/webgpu/forest.html`.
- Expect about 20 s per frame with real content. The SSGI pipeline broke the shadows and the cause is
  not yet found.

**General**
- GitHub release downloads, npm, PyPI and apt are reachable. `download.blender.org`, Unity's sites,
  review sites and Wikipedia are not.
- Blender is available as the `bpy` wheel from PyPI: 5.2.2 needs Python 3.13 exactly, and the
  container's default `python3` is 3.11.

## Re-running the research

The workflow is only worth re-running if something in section 10 of the decision record changes,
such as a new Godot GI landing or the owner requiring a web link. To re-run it:

1. Pass `scriptPath: docs/engine_selection/workflow/aokigahara-engine-selection.js` to the Workflow tool.
2. First update the date, the `SCRATCH` constant and the `/tmp/claude-0/...` image paths. Point the
   image paths at `renders/ue58_baseline/`.
3. The container has 4 CPUs, so it runs two agents at a time. A full run is about 25 agents and
   roughly an hour and a half.

Day-to-day building should use single-agent sessions (decision record, section 6).
