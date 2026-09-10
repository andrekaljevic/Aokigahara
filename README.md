# Aokigahara — free-roam reconstruction

A geographically anchored, continuously explorable reconstruction of Aokigahara and the
north-western foot of Mount Fuji, built on measured elevation data and mapped vegetation, geology
and route sources, with procedurally generated forest structure on top.

It is **not** a surveyed digital twin and **not** finished photorealism. Every individual tree,
root, rock and log is procedural. Read `docs/PROJECT_STATE.md` for the current state and
`docs/handover/Aokigahara_3D_README.md` for the original evidence-and-limits statement.

---

## Present status

The repository preserves **production pass 2**, recovered from the Fable 5.1 Max session that
built it. The world loads and renders. Verified in this environment under software OpenGL:

| Check | Result |
|---|---|
| Manifest verification | 211 of 223 files present, **0 hash mismatches** |
| World ready | 12.3 s |
| Console errors, page errors, failed requests | **0** |
| Fixed-camera audit | 8 of 8 cameras reproduce the source session's triangle and draw-call counts **exactly** |
| Per frame | 7.1–7.9 M triangles, 86–95 draw calls at 1280 × 800 |

No frame rate has been measured on any target device.

Running today: the near-field procedural lava and moss ground system, tree library v2 with modelled
surface roots, stand densification across three stem-size layers, deadwood, lava blocks, ferns and
three daylight presets.

On `dev/generational-visual-upgrade`, the interrupted pass has been continued: the preset selector
is finished and the distant-ground defect the source session was diagnosing is fixed, with
identical-camera evidence in `renders/distant_ground_fix/`.

---

## Running it

Requires Python 3 and a browser with WebGL 2. No build step and no dependencies.

```bash
python3 launch_viewer.py            # serves the repository root
# then open http://127.0.0.1:8000/viewer/
```

The server must be the repository root, not `viewer/`, because the viewer resolves
`../models/Aokigahara_Surface_Terrain.glb`. Opening `viewer/index.html` from the filesystem will
not work: ES modules and the binary terrain grids need HTTP.

Walk with WASD or the arrow keys, look with the mouse, hold Shift to move faster, press F to
toggle fly mode, Escape to release the pointer. On touch devices use the two pads.

**Verify the recovered state:**

```bash
python3 tools/verify_manifest.py
```

**Re-render the fixed audit cameras** (needs Node and Playwright):

```bash
python3 launch_viewer.py --port 8765 --quiet &
node tools/audit_render.mjs http://127.0.0.1:8765/viewer/ renders/audit harness/cams2.json 1280 800
```

This writes one PNG per camera plus an `audit.json` recording triangle counts, draw calls, console
errors and failed requests.

---

## Technology

Three.js r180 and three-mesh-bvh, both vendored under `viewer/vendor/` with their MIT licences.
No bundler, no framework, no package manager: `viewer/app.js` is a single ES module loaded through
an import map. Terrain grids are raw little-endian `Float32Array` and `Uint8Array` blobs fetched
directly. Asset generation is Python (NumPy, Pillow, SciPy, trimesh) under `construction_code/` and
`construction_code_v2/`.

Ground shading is a custom multi-layer material: four PBR sets — moss, basalt, litter and trail —
blended in world space per vertex or procedurally, with anti-tiling rotation and triplanar
projection for rocks and logs.

---

## Coordinate frame

Origin 138.658° E, 35.4775° N, WGS 84.

```
+proj=aeqd +lat_0=35.4775 +lon_0=138.658 +datum=WGS84 +units=m +no_defs
```

Scene x points east, z points south, y points up. **1 unit = 1 metre**, no vertical exaggeration.
Scene y is the published GSI elevation minus 900 m; that subtraction is an origin shift, not a
vertical-datum conversion. Inverse-project `(x, −z)` to recover longitude and latitude.

The research dossier recommends EPSG:6676 as the project CRS. The built world does not use it. That
divergence is deliberate and is recorded in `docs/PROJECT_STATE.md`; reconcile the two before
ingesting any further GSI or GSJ vector data.

---

## Layout

```
viewer/            The runtime. app.js, index.html, vendored Three.js, and every asset it fetches
models/            Standalone GLB exports: 32 × 30 km surface terrain, regional terrain
data/              Wide-forest placements, and the recovered GIS / elevation / route research data
docs/              PROJECT_STATE.md, the research dossier and its 18 extracted artifacts, methodology
renders/           Before/after evidence from each production pass, and this session's audit renders
harness/           The original session's render harness, preserved unmodified
construction_code/    Pass-1 asset build scripts
construction_code_v2/ Pass-2 tree-library and texture generators
construction_inputs/  Pass-1 procedural tree arrays
source_manifests/  Per-asset provenance, checksums and licence records
tools/             Manifest verification, portable audit renderer, research generation scripts
```

Directory names follow the original package so that no path inside `viewer/` was rewritten during
recovery.

---

## Significant assets

| Asset | Size | Notes |
|---|---|---|
| `models/Aokigahara_Surface_Terrain.glb` | 22.6 MB | 32 × 30 km, 895,734 triangles, real Fuji relief |
| `models/Aokigahara_Regional_Terrain.glb` | 11.8 MB | Coarser context terrain |
| `viewer/assets/models/fir_tree_c.glb` | 22.5 MB | Mature fir representative, Poly Haven CC0 |
| `viewer/assets/tree-library-v2.glb` | 12.5 MB | 11 procedural variants, 37 meshes across 3 LODs |
| `viewer/assets/tree-library.glb` | 12.2 MB | Pass-1 library, still required for broadleaf variants |
| `data/forest-wide.f32` | 11.2 MB | 467,601 tree placements |
| `viewer/assets/forest-instances.f32` | 1.3 MB | 53,999 corridor placements |
| `renders/exports/Aokigahara_patch_E32_S10_compressed.glb` | 29.8 MB | Patch export from the deployed site |

Three derived exports — the cave corridor, the instanced forest and the assembled world — were
**not** in the recovered archive. They are rebuildable from `construction_code/`. The viewer greys
out downloads for whichever of them a checkout lacks, naming the script that rebuilds each, rather
than offering links that fail. `launch_viewer.py` keeps that index current.

---

## Binary assets and Git LFS

Every binary asset is stored **directly in Git**, not in Git LFS. A normal `git clone` gets a
working world with no extra steps.

That is a deliberate fallback, not the preferred design. The intended LFS ruleset is preserved
verbatim in `.gitattributes.lfs`; it is inactive because the environment that first published this
repository cannot reach `lfs.github.com` — its egress gateway refuses the connection. Rather than
push a repository whose large assets were silently missing, the assets were committed as ordinary
Git objects. Every file is well inside GitHub's limits: the largest is 29.8 MB against a 100 MB
per-file ceiling, and the whole tree is about 240 MB.

To move to LFS from a machine that can reach `lfs.github.com`:

```bash
bash tools/enable_lfs.sh          # rewrites history for the binary paths
git lfs push --all origin
git push --force-with-lease origin --all
```

The ruleset it applies covers `*.glb *.gltf *.fbx *.blend *.obj *.exr *.hdr *.tif *.tiff *.f32
*.npz *.zip *.7z *.bin *.pdf`, the runtime texture sets under `viewer/assets/materials*/`, and the
render evidence under `renders/`. Small categorical grids (`*.u8`, all under 300 KB) and every
JSON, CSV and GeoJSON deliberately stay in plain Git so they remain diffable — including the 4 MB
evidence grid, which is worth reading in diffs.

Line-ending normalisation is disabled for all data formats so the SHA-256-verified files and the
recovered research data stay byte-exact. `tools/verify_manifest.py` reports any file that is an
unresolved LFS pointer.

## Research and provenance

`docs/research/Aokigahara_Master_Consolidated_Dossier.pdf` is the consolidated research record,
dated 9 September 2026. Its 18 embedded machine-readable artifacts were extracted and filed:
the 2,790-cell 250 m evidence grid, 3,528 candidate GSI DEM tile URLs, the 152-entry visual and map
catalogue, a 22-source authoritative register, the route topology graph, the boundary-layer
register, georegistration control points and the master reconstruction blueprint.

The project distinguishes what is source-constrained from what is inferred and what is invented:

- **Source-constrained** — macro terrain (GSI DEM), vegetation communities (Ministry of the
  Environment), eruptive-deposit footprint (Geological Survey of Japan), path centre lines
  (OpenStreetMap).
- **Inferred** — stand composition and structure, path appearance, ground-cover distribution.
- **Procedural** — every individual tree, root, rock, log, and all near-field micro-relief.
- **Not reconstructed** — cave interiors and mouths, current signs and barriers, individual-tree
  survey, bathymetry, calibrated seasonal lighting.

The dossier's governing rule is preserved: the named forest, the Jōgan lava field, the legal
protection boundaries and the practical build extent are related but are **not one polygon**.

---

## Current limitations

- No individual tree, root, rock or log is surveyed; placement is procedural, constrained by mapped
  community classes rather than by a census.
- Bark, foliage, fern and log sources are Poly Haven CC0 representatives, not captured at
  Aokigahara. The "hinoki" and "tsuga" variants are species-suggestive only, and establish no
  botanical identity.
- Ground materials are procedurally synthesised, not photogrammetry of the site.
- Terrain is 8 m output sampling of the GSI DEM5A web grid, not a native 1 m survey; lava fissures
  and overhangs below that sampling are absent.
- Cave destinations are surface approach references only. No cave interior is modelled.
- Of the seven forest community types the underlying survey distinguishes, the runtime represents
  three. Pinus and Tsuga-Pinus communities are not modelled at all.
- The 120 m near-field patch edge is no longer a change in material or shading, but it is still a
  change in ground geometry detail: inside it the lava relief is sampled at 0.6 m, outside it the
  surface is the plain 8 m DEM.

---

## Attribution

Elevation and aerial data: Geospatial Information Authority of Japan (GSI), under its stated
public-data terms. Geology: Geological Survey of Japan / AIST, Fuji Volcano Geological Map 2nd
edition. Vegetation: Ministry of the Environment, Japan. Paths and mapped features:
© OpenStreetMap contributors, ODbL 1.0. Representative models, textures and the twig atlas:
Poly Haven, CC0, with creators preserved in `source_manifests/`. Three.js and three-mesh-bvh retain
their MIT licences.

Retain `viewer/assets/provenance.json` and the source manifests with any derivative work.
No AI-generated image or model was used as factual evidence.
