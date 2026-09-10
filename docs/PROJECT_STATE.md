# PROJECT_STATE

Canonical record of the transition from the Claude conversational session (Fable 5.1 Max) into
Claude Code. Written at the point of the first repository checkpoint.

**Status of this document:** factual. Where a system is incomplete it is described as incomplete.
Nothing here claims photorealism or a surveyed digital twin.

---

## 1. What was recovered

### 1.1 Supplied material

| Input | Form | Size | Outcome |
|---|---|---|---|
| `Aokigahara_Pass2_Handover.zip` | 5 upload parts, concatenated | 146,800,640 bytes | Truncated tail; 211 of 223 manifest files recovered |
| `Aokigahara_Master_Consolidated_Dossier.pdf` | 25-page research PDF, 9 September 2026 | 2,476,272 bytes | Read in full; 18 embedded artifacts extracted |
| `Aokigahara_patch_E32_S10_compressed.glb` | Runtime patch export from the deployed site | 29,766,796 bytes | Parsed and used as evidence of the deployed runtime |
| Deployed site URL | `aokigahara-field-world.akal95.chatgpt.site` | — | **Not reachable**: blocked by this environment's network egress policy |

### 1.2 Archive recovery method

The five uploaded parts were byte-concatenated. The resulting archive is a valid ZIP prefix but has
no central directory: the upload ends inside local entry 249. Rather than discard it, every local
file header was walked directly, each entry inflated and checked against its stored CRC-32 and
uncompressed length, then written out with its original modification time.

- **211 entries** recovered and CRC-verified.
- **1 entry** truncated mid-stream (`construction_inputs/procedural_trees/evergreen_spreading/high_leaves.npz`).
- Every recovered file was then re-checked against `MANIFEST_PASS2_SHA256.json`.
  **223 manifest entries, 211 present, 0 hash mismatches.**

Re-run this check at any time with `python3 tools/verify_manifest.py`.

### 1.3 Files that did not survive the truncation

These are named in the manifest but fall beyond the upload cut. They are recorded here so their
absence is never mistaken for a design decision.

| File | Consequence |
|---|---|
| `HANDOVER.md` | Pass-2 narrative handover note lost. Its content is partly recoverable from `Aokigahara_3D_Provenance.json` → `productionPass2`, which survived intact. |
| `launch_viewer.py` | **Replaced.** A functional equivalent was written (see §4). |
| `Aokigahara_3D_Validation.json` | GLB structural-validation report lost. The checks it recorded are described in the Pass-1 README. |
| `MANIFEST_SHA256.json` | Pass-1 manifest lost. The Pass-2 manifest survived and supersedes it. |
| `viewer_original_backup/app_pass1_original.js`, `index_pass1_original.html` | Pass-1 viewer backup lost. Not required: Pass 2 is the canonical runtime. |
| `evidence/attachment_audit.md`, `attachment_cave_constraints.json`, `attachment_asset_manifest.json`, `Research_Source_Catalogue.csv` | Evidence-audit set lost from the archive. **Substantially recovered from a different source** — see §1.4. |
| `construction_inputs/procedural_trees/evergreen_spreading/{high_leaves,high_bark,low_bark}.npz` | Three of sixteen Pass-1 procedural-tree input arrays. Pass-1 trees are superseded by tree library v2; the compiled Pass-1 `tree-library.glb` is present and still loaded by the runtime. |

### 1.4 Research data recovered from the dossier

The master dossier carries 18 machine-readable artifacts as PDF file attachments. All 18 were
extracted and filed. This recovers most of the lost `evidence/` set and adds considerably more:

| Artifact | Filed at | Content |
|---|---|---|
| 250 m evidence grid | `data/gis/Aokigahara_250m_coverage_grid.{geojson,csv}` | 2,790 cells. Verified split: 81 High, 1,283 Medium, 1,426 Low |
| GSI DEM tile plan | `data/elevation/Aokigahara_GSI_DEM_tile_plan.csv` | 3,528 candidate tile URLs with bounds |
| Route topology graph | `data/routes/Aokigahara_route_topology_graph.csv` | 9 edges, each with separate geometry-status and access-status |
| Visual/map/GIS catalogue | `data/reference-metadata/Aokigahara_visual_asset_manifest.csv` | 152 entries |
| Authoritative-source register | `data/reference-metadata/Aokigahara_authoritative_source_register.csv` | 22 audited sources |
| Boundary-layer register | `data/reference-metadata/Aokigahara_boundary_layer_register.csv` | 8 distinct boundary concepts, deliberately not merged |
| Georegistration control points | `data/reference-metadata/Aokigahara_georegistration_control_points.csv` | 9 controls with confidence |
| Temporal imagery register | `data/reference-metadata/Aokigahara_temporal_imagery_register.csv` | Historical GSI aerial series 1961–69 onward |
| Sector gap matrix | `data/reference-metadata/Aokigahara_sector_gap_matrix.csv` | Ten-sector plan with per-sector confidence and gap |
| Reconstruction blueprint | `docs/methodology/Aokigahara_Reconstruction_Blueprint.json` | 26-key master specification |
| Layer stack, coverage methodology | `docs/methodology/` | Production layer hierarchy and scoring assumptions |
| Interactive atlas, coverage map, original dossier | `docs/research/atlas/*.html` | Leaflet atlases preserved as authored |
| Generation scripts | `tools/research/*.py` | Provenance scripts for the dossier and coverage expansion |

The dossier's own core rule is retained: **the named forest, the Jōgan lava field, the legal
protection boundaries and the practical build area are related but are not one polygon.**

---

## 2. Latest Fable 5.1 Max state

The recovered package is **production pass 2**, dated 2026-09-10 in
`Aokigahara_3D_Provenance.json` → `productionPass2`. It is the most advanced coherent state
available and it is what this repository preserves. Pass 1 is present only where pass 2 still
depends on it (the Pass-1 `tree-library.glb` supplies the `tree_2` / `tree_3` broadleaf variants
that pass 2 continues to instance).

The `Aokigahara_patch_E32_S10_compressed.glb` export supplied from the deployed site independently
confirms the deployed runtime is pass 2: its 8,857 nodes carry tree-library-v2 mesh names
(`tsuga_*`, `hinoki_*`, `snag_*`, `sap_*` at high and low LOD), five `fir_tree_C_representative`
hero trees, and procedural lava-block, fern and fallen-log nodes.

### 2.1 Near-field ground system — **running**

Fully wired into the runtime, not merely written. `viewer/app.js` builds a 120 m × 120 m ground
patch at 200 × 200 sampling (0.6 m spacing) centred on the camera, rebuilt whenever the camera
moves more than 12 m. Elevation is the GSI DEM sample plus a procedural lift comprising:

- metre-scale lava lobes, 1–3 m block relief, sub-metre clinker and occasional linear clefts
  (`reliefRaw`, amplitude about ±0.6 m);
- Gaussian root mounds under every nearby stem (`mound`, 0.24 m × instance scale);
- path suppression, so trails cut through the relief rather than riding over it.

Per-vertex `aWeights` carry moss / basalt / litter / trail proportions derived from slope,
curvature, value noise, mound proximity and path weight. A custom `MeshStandardMaterial` program
blends four PBR sets in world space with anti-tiling rotation and a moss-height sharpening term.

### 2.2 Tree library v2 — **running**

`viewer/assets/tree-library-v2.glb`, 12,521,860 bytes, generated by
`construction_code_v2/generate_trees_v2.py` with deterministic seeds. 11 variants × up to 3 LODs =
37 meshes.

| Variant group | Form | High-LOD triangles |
|---|---|---|
| `tsuga_a/b/c` | Tsuga-like hemlock, spreading and drooping laterals | 9,119–12,187 |
| `hinoki_a/b/c` | Chamaecyparis-like cypress, ascending laterals | 9,754–11,330 |
| `snag_a/b` | Standing dead stems, broken tops | 1,602–1,623 |
| `sap_tsuga`, `sap_hinoki`, `sap_small` | Regeneration stems 1.5–6 m | 3,551–4,260 |
| `log_a/b`, `rock_a–d` | Fallen timber and lava blocks | 294–1,280 |

Every mature tree carries a modelled surface-root system: 7–11 roots per stem riding over the lava
with wobble, forking and moss vertex-tint on upper surfaces. Bark uses buttress flare in the lowest
0.9 m. Foliage is folded spray cards cut from a Poly Haven twig atlas, with a shader fix that lights
both faces toward world-up so thin sprays do not read as black undersides. LOD selection is
distance-based: high below 46 m (balanced) or 62 m (high), low to 230 m, then 32-triangle crossed-card
impostors.

### 2.3 Stand densification — **running**

Three superimposed procedural layers, all reaching the renderer:

1. **Per-instance augmentation** of the unchanged 53,999 corridor placements: size class
   (22 % small, 66 % mid, 12 % dominant), 6 % standing dead, ±2.6° tilt, variant chosen from the
   mapped community class.
2. **Small stems**, 1.5–6 m, on a 3.6 m jittered lattice out to 110–130 m, with clustered density
   noise and suppression close to existing stems.
3. **Sub-canopy stems**, 7–13 m, on a 6.0 m lattice out to 170–230 m.

### 2.4 Deadwood and rocks — **running**

Fallen logs use the Poly Haven `dead_tree_trunk` mesh with a procedural moss overlay material and
are tilted to follow the local ground gradient. Lava blocks are five noise-displaced icosahedra
with flattened, partly buried bases, instanced with moss on upper faces. Both are placed on a
2.5 m lattice keyed to the same rock-density noise that drives the ground layer weights, so blocks
appear where the ground is already reading as rock.

### 2.5 Lighting — **running, with a stale control**

Three daylight presets are implemented in `PRESETS` — `overcast`, `soft`, `clear` — each setting
sun intensity, hemisphere colours and intensity, Rayleigh/Mie/turbidity on the sky shader, fog
colour and tone-mapping exposure together. Shadows are PCF-soft, 2048², with the shadow camera
retargeted to follow the viewer. Fog density responds to the haze slider and thins with altitude.

### 2.6 Preset selector — **incomplete, and now repaired**

This is the "building the preset selector" work. It was left half-finished in the markup:

- `viewer/index.html` contained **two** daylight `<select>` elements. `#light` (soft / overcast /
  clear) is wired in `app.js`. `#lighting` (overcast / sunlit) is **not referenced anywhere** —
  an orphan from an earlier iteration, presented to the user as a live control that did nothing.
- The `#destination` list contained the **IMG-013 reference viewpoint twice**, under two different
  labels for the same value.

Both were repaired on `dev/generational-visual-upgrade`. See §4.

### 2.7 Distant ground — **this was the unfinished investigation; cause found and fixed**

The Fable session stopped while "diagnosing why distant ground…". The defect is real and is in
`viewer/app.js`.

`layerMaterial('ground')` compiles with `#define GROUND_WEIGHTS`, which makes the shader read a
per-vertex `attribute vec4 aWeights`. The near-field patch supplies that attribute. The **base
terrain** — the corridor ground inside `Aokigahara_Surface_Terrain.glb`, which covers everything
outside the 120 m patch — is assigned `groundMats.base`, built by the *same* `layerMaterial('ground')`
call, but its geometry has no `aWeights` attribute at all.

WebGL supplies a default of `(0, 0, 0, 1)` for an unbound vertex attribute. The author anticipated
the missing-attribute case and wrote a fallback:

```glsl
vec4 w = vW;
if (w.x + w.y + w.z + w.w < 0.01) { /* moss + litter mix from noise */ }
```

but `(0,0,0,1)` sums to exactly `1.0`, so the guard never fires. The weights stay `(0,0,0,1)`, and
the fourth channel is the **trail** layer. Every square metre of ground beyond the near-field patch
is therefore shaded as compacted trail cinder — a flat mid-brown — instead of the intended
moss-and-litter forest floor. This is visible in the recovered evidence renders: in
`renders/after_p4/C6_arbitrary_east.png` the near-field reads as moss, rock and litter while the
ground behind it flattens to uniform brown.

The fix is described in §4.2. It was applied on `dev/generational-visual-upgrade`, not on the
checkpoint, so `main` still holds the exact state the Fable session reached.

---

## 3. Current canonical components

| Role | Path | Notes |
|---|---|---|
| Runtime / viewer | `viewer/app.js` (47,433 B), `viewer/index.html` | Pass 2. SHA-256 `289e3f48…84ed` matches the provenance record |
| Renderer | `viewer/vendor/three.module.js` | Three.js r180, vendored, MIT licence retained |
| Ray acceleration | `viewer/vendor/mesh-bvh.module.js` | three-mesh-bvh, used for ground intersection |
| Terrain grids | `viewer/assets/terrain/{local,study,regional}-height.{json,f32}` | Local 8 m, study and regional coarser |
| Terrain masks | `…-{landcover,jogan,quality}.u8` | Vegetation class, Jōgan deposit, source-quality |
| World terrain mesh | `models/Aokigahara_Surface_Terrain.glb` (22.6 MB) | 32 × 30 km, 895,734 triangles, includes Fuji relief |
| Regional terrain | `models/Aokigahara_Regional_Terrain.glb` (11.8 MB) | Lighter context import |
| Canonical vegetation | `viewer/assets/tree-library-v2.glb` | See §2.2 |
| Legacy vegetation | `viewer/assets/tree-library.glb` | Pass-1 library, **still required** for `tree_2`/`tree_3` broadleaf variants |
| Corridor placements | `viewer/assets/forest-instances.f32` | 53,999 records, 6 floats each |
| Wide forest placements | `data/forest-wide.f32` | 467,601 records; first 53,999 duplicate the corridor set |
| Hero and detail models | `viewer/assets/models/{fir_tree_c,fern_02,dead_tree_trunk}.glb` | Poly Haven CC0 |
| Ground materials | `viewer/assets/materials_v2/` | Procedural moss, basalt, litter, trail, blend noise |
| Provenance | `docs/handover/Aokigahara_3D_Provenance.json` | Includes the full `productionPass2` record |
| Research corpus | `docs/research/`, `docs/methodology/`, `data/` | See §1.4 |

### 3.1 Assets referenced but not present

- **`models/Aokigahara_Cave_Corridor.glb`** — `viewer/assets/corridor-download.json` points at
  `../../models/Aokigahara_Cave_Corridor.glb` (declared 65,601,664 bytes). The file is not in the
  handover archive, so the viewer's "Download corridor · GLB" button will fail. It is a *derived*
  export, rebuildable from `construction_code/export_scene.py`.
- **`models/Aokigahara_Instanced_Forest.glb`** and **`models/Aokigahara_World.glb`** — likewise
  linked from `viewer/index.html` and the README, likewise absent, likewise derived
  (`export_forest.py`, `assemble_world.py`).

None of these three is required to run the world. All three are documented here rather than
silently dropped, and since the repair in §4.2 the viewer no longer advertises them as downloads
when they are absent.

---

## 4. Handoff repairs

### 4.1 Made for the canonical checkpoint (`main`)

1. **`launch_viewer.py` rewritten.** The original was lost in the truncated tail. The replacement
   serves the repository root over HTTP so `viewer/` can still resolve `../models/…`, and registers
   correct MIME types for `.glb`, `.f32` and `.u8`, which the stock Python handler does not know.
2. **`tools/verify_manifest.py` added** so the recovered state can be re-verified against the
   Pass-2 SHA-256 manifest at any time, including after a fresh Git LFS checkout.
3. **`tools/audit_render.mjs` added.** The original `harness/shoot.mjs` is preserved unmodified but
   hard-codes a server on port 8000 rooted at `/home/claude/aoki`. The new tool takes a base URL,
   and additionally records console errors, page errors, failed requests and HTTP ≥ 400 responses
   to `audit.json`, so a render can be judged on more than whether an image appeared.
4. **Research artifacts extracted and filed** from the dossier PDF (§1.4).

No recovered source file, asset or manifest was edited for the checkpoint.

### 4.2 Made on `dev/generational-visual-upgrade`

Applied after the checkpoint, continuing the interrupted pass rather than redesigning it.

**1. Preset selector completed.** Removed the orphan `#lighting` select and the duplicated IMG-013
destination option. Introduced a single `applyPreset(preset, angle)` entry point used by the panel
control, the destination jumps and the headless `setPreset` hook alike, so the UI can no longer
disagree with the live preset. Verified in the running page: the orphan select is gone, exactly one
IMG-013 option remains, the select initialises to the live preset, and calling
`setPreset('clear', 60)` moves both the select and the sun slider.

**2. Distant ground repaired.** The shader was never wrong; the attribute it reads was simply never
built for that geometry. Rather than add a second shader path, the fix supplies what the existing
one expects: `buildBaseWeights()` evaluates the same moss/rock/litter/trail model the near-field
patch uses — same procedural lava relief, same noise fields, same land-cover term — over the
corridor terrain's vertices, and writes it into an `aWeights` attribute. 66,306 vertices across two
meshes, computed once at load.

Because both surfaces now evaluate the same model, they agree by construction rather than by
tuning. Measured mean layer weights:

| Surface | moss | rock | litter | trail |
|---|---|---|---|---|
| Near-field patch (was always correct) | 0.544 | 0.153 | 0.267 | 0.035 |
| Base terrain, before | 0.000 | 0.000 | 0.000 | **1.000** |
| Base terrain, after | 0.468 | 0.206 | 0.311 | 0.015 |

**3. The brightness step behind it removed.** With the materials matched, a second seam became the
visible one. The canopy term is spatial and continuous — `(0.8 + 0.2 * world noise)` — but the base
material scaled it by a further 0.62 while the patch used 1.0. That is a 38 % albedo step along an
edge that is rebuilt around the camera every 12 m, so it could not produce anything except a seam
that follows the player. One value now serves both surfaces and the floor is continuous by
construction rather than by tuning. The near field is unaffected: it already used 1.0.

Identical-camera evidence for all three is in `renders/distant_ground_fix/`, which keeps the
intermediate stage as well, with side-by-side composites at `renders/BEFORE_AFTER_D*.jpg`. The
elevated cameras show the defects at full extent — 45.0 % of pixels change at
`D5_above_canopy_look_down` and 37.6 % at `D4_above_canopy_look_out` — while eye-level cameras
change 7.5 % or less because canopy and trunks occlude most distant ground.

**4. Download controls made honest.** Two of the three derived exports the panel advertised are
absent from the recovered archive, so those controls returned HTTP 404. The corridor button
reported "The model download was interrupted. Try again." — advice that could never succeed.
`launch_viewer.py` now records which derived exports a checkout actually contains in
`viewer/assets/derived-exports.json`, rewriting it only when it changes, and the viewer greys out
the ones that are missing, naming the script that rebuilds each. Where that index is absent — some
other static server — it falls back to probing, which is noisier but always truthful. The audit
renderer classifies an availability probe separately from a genuine failure so a clean audit stays
readable. Verified: the panel now offers the regional terrain and the in-browser patch export,
marks the corridor and wider-forest exports unavailable, and produces no console errors.

**Checked and deliberately not chased.** Magnifying the distant ground reveals a fine dotted moiré.
It is texture aliasing at oblique angles and it pre-dates this work: measured as the fraction of
image energy in the 3–12 pixel band over the same crop, the Fable session's own renders score
0.441 and 0.450, the checkpoint scores 0.432, and current `dev` scores 0.448. Brightening the
surface raised it by about 4 % relative, which is the surface becoming visible rather than a new
artifact. It has not been tested on hardware GL.

**Regression check.** The eight standard audit cameras were re-rendered after every change. All
eight still reproduce the source session's triangle and draw-call counts exactly, with zero console
errors, and the two cameras that see only near-field ground (`C2_start_lookdown`,
`C5_fugaku_approach`) remain bit-identical to the checkpoint. The near-field path was not touched.

---

## 5. Known remaining problems

**Verified defects**

- Corridor, instanced-forest and assembled-world GLBs are absent (§3.1); the viewer's corridor
  download button will fail until they are rebuilt.
- Three Pass-1 procedural-tree input arrays are lost (§1.3).

**Honest limits of the reconstruction itself**

- No individual tree, root, rock or log is surveyed. Placement is procedural and constrained by
  mapped community classes, not by a census.
- Bark, foliage, fern and log sources are Poly Haven CC0 representatives. They were not captured at
  Aokigahara and establish no botanical identity. The "hinoki" and "tsuga" variants are
  species-suggestive only.
- The ground materials are procedurally synthesised, not photogrammetric captures of the site.
- Cave destinations are surface approach references. No cave mouth or interior is modelled, despite
  the dossier holding A-confidence dimensions for nine caves.
- Terrain is 8 m output sampling of the GSI DEM5A web grid, not a native 1 m survey. Lava fissures
  and overhangs below that sampling are not represented.
- The dossier recommends EPSG:6676 (JGD2011 / Japan Plane Rectangular CS VIII) as the project CRS.
  The built world uses a local azimuthal-equidistant frame at 138.658 E, 35.4775 N. This divergence
  is deliberate and documented, not an error, but any future ingest of GSI or GSJ vector data must
  reconcile the two rather than assume they agree.
- The dossier identifies **seven** forest community types from the University of Tokyo survey
  (open Pinus, Pinus, Tsuga-Pinus, Tsuga, Chamaecyparis-Tsuga, Chamaecyparis, deciduous broadleaved).
  The runtime models Tsuga-like, Chamaecyparis-like and a broadleaf proxy. **Pinus communities are
  not represented at all**, and open-Pinus is specifically associated with exposed lava sites.
- The 250 m evidence grid is a research instrument. 1,426 of 2,790 cells are Low evidence. It is
  not a forest boundary and not a measured coverage assessment.

**Not measured**

- No frame-rate figure has been measured on any target device. The only performance evidence is
  triangle and draw-call counts from the headless audit renderer.

---

## 5a. Repository location

The brief asked for a new private repository named `aokigahara-free-roam`. **It could not be
created from this session.** GitHub access here is bound to the repositories the session was
configured with; `POST /user/repos` returns

> `This GitHub API path is not available: sessions are bound to their configured repositories.`

That is an access-policy refusal, not a transient error, so it was not retried. Rather than leave
the recovered state unpushed, everything was published to the private repository this session can
write to:

**`https://github.com/andrekaljevic/Aokigahara`** — private, default branch `main`.

| Branch | Commit | Contents |
|---|---|---|
| `main` | `859ab5d` | The canonical checkpoint: the recovered Fable state, untouched |
| `dev/generational-visual-upgrade` | `dc33485` | The continued production pass |
| `claude/aokigahara-fable-handoff-0fdzom` | `859ab5d` | Session branch, same commit as `main` |

To move to the preferred name, create an **empty** private repository called
`aokigahara-free-roam` (no README, no .gitignore, no licence), then:

```bash
git remote add canonical https://github.com/<you>/aokigahara-free-roam.git
git push canonical main dev/generational-visual-upgrade
git remote rename origin session && git remote rename canonical origin
```

Nothing in the project depends on the repository name.

---

## 6. Next development step

The checkpoint on `main` is the recovery. Work continues on `dev/generational-visual-upgrade`.

1. Re-render the fixed cameras and compare distant-ground appearance against
   `renders/after_p4/` before/after evidence.
2. Rebuild the three missing derived GLB exports. The viewer no longer misreports them, but they
   are still absent. The blocker is that `export_scene.py` and `export_forest.py` source tree
   geometry from the Pass-1 `.npz` arrays, three of which were lost with the archive tail; they
   would need to read the compiled `tree-library.glb` instead. Note also that the assembled world
   would likely exceed GitHub's 100 MB per-file limit, so it may belong outside the repository.
3. Ingest the GSJ 2016 Fuji Volcano vector geology in place of the current raster-derived Jōgan
   mask, which the dossier names as the highest-value geometry still to ingest.
4. Add Pinus and Tsuga-Pinus community types so all seven surveyed communities are representable,
   and drive the mix from the MoE vegetation classes already in the terrain masks.
5. Give the ground beyond the 120 m patch real micro-relief. Material and shading are now
   continuous across that boundary, but the geometry is not: the patch carries lava relief at 0.6 m
   sampling while the corridor terrain outside it is the plain 8 m DEM surface. A coarser
   intermediate tier, or displacing the corridor vertices by the same `reliefRaw` field already
   used for their weights, would close the remaining discontinuity. Displacing the base requires
   reworking the patch's edge fade, which currently blends to flat rather than to the surrounding
   relief, so the two surfaces would otherwise part company by up to 0.6 m at the seam.
