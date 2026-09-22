# construction_code_v3 — photo-derived material packs

`extract_uhd_materials.py` turns regions of the owner-supplied Aokigahara photographs in
`construction_inputs/uhd_photos/` into tileable PBR material packs. It replaces nothing: the
procedural `materials_v2` set stays the runtime default, and the packs it writes are an optional
alternative (`?mats=uhd` in the viewer) and a stand-alone asset deliverable.

## What it produces

For every material in `uhd_extraction_spec.json`, three resolution tiers:

| Tier | Directory | Square tile | Strip tile | Consumer |
|---|---|---|---|---|
| 4k master | `asset_packs/materials_uhd_4k/` | 4096 × 4096 | 2048 × 4096 | DCC / engine import |
| 2k | `asset_packs/materials_uhd_2k/` | 2048 × 2048 | 1024 × 2048 | DCC / engine import |
| 1k | `viewer/assets/materials_uhd/` | 1024 × 1024 | 512 × 1024 | the web viewer |

Six maps per material and tier: `diff` (sRGB base colour), `nor_gl` (OpenGL tangent-space
normal, the same convention as `materials_v2`), `rough`, `height`, `ao`, and `orm` (packed
R = ao, G = roughness, B = metallic 0). A manifest with per-file bytes and SHA-256, the source
rectangle, the estimated physical scale, the native source pixel count, the upsample factor and
quality metrics is written to both `viewer/assets/materials_uhd/MATERIALS_UHD_MANIFEST.json` and
`asset_packs/MATERIALS_UHD_MANIFEST.json`. Preview sheets go to `renders/assets/`.

## Pipeline (per material)

1. Decode the photograph to linear light; rotate about the region centre if the trunk or log
   axis is not vertical; crop; light denoise (σ 0.6 px) at source resolution.
2. Mask clipped highlights (sun dapples, dilated 6 px) and pixels that are black relative to
   the crop (deep clefts); these never enter the albedo.
3. Delight: divide by a mask-aware Gaussian estimate of the illumination (σ = 12 % of the short
   side), bounded to ±2.5× the crop's median gain; desaturate noise-dominated shadow in
   proportion to its lift; inpaint masked pixels by normalised convolution; match the mean
   linear luminance of the corresponding `materials_v2` (or Poly Haven bark) texture.
4. Lanczos-resize to the 4096 master and apply a gentle unsharp mask scaled to the upsample.
5. Make the tile toroidal: Moisan periodic-plus-smooth decomposition, then Efros–Freeman
   minimum-error-boundary quilting of the interior over the half-rolled tile, then a second
   pass that covers the four residual stubs at the tile centre; cuts are feathered by 2 px.
6. Height = signed multi-scale luminance high-pass (σ 8/24/72 px at the master, plus a green
   chroma term for moss). Normal = `gen_textures.height_to_normal()` from `construction_code_v2`,
   so the convention is identical to the procedural set. Roughness = per-slot base minus a
   small highlight term. AO = darkening where the height is below its 56-px neighbourhood.
7. Write the master, then Lanczos-downsample to 2k and 1k (normals re-normalised).

## Honesty statement

The albedo is the delit photograph. Height, normal, roughness and ambient occlusion are
single-image heuristic estimates; nothing is photogrammetry or a survey. Physical scale is
estimated from objects in frame (trunk diameters, leaf sizes), not measured. The photographs
arrived at 2000 × 983 px, so the 4k and 2k tiers are interpolated above the native resolution
recorded per material as `native_source_px` and `upsample_factor` in the manifest.

## Running

```bash
python3 construction_code_v3/extract_uhd_materials.py                 # all materials, all tiers (~15 min)
python3 construction_code_v3/extract_uhd_materials.py --only moss_uhd  # one material
python3 construction_code_v3/extract_uhd_materials.py --master-factor 1  # quick 1k-only preview run
python3 tools/verify_material_pack.py viewer/assets/materials_uhd      # independent quality checks
```

Deterministic (no randomness, no timestamps). Requires numpy, pillow (with WebP) and scipy.
