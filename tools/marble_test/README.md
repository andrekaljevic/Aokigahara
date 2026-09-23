# Marble test: can a generated world dress the real Aokigahara terrain?

This kit answers one question before any engine is committed to: if Marble (World Labs'
generative world model) is given the **real** ground and tree positions of an Aokigahara sheet,
does the world it produces look photographic, and how far can you walk from its origin before it
breaks down?

It runs entirely in the Claude Code cloud container. The owner's Mac is not involved.

## Pipeline

1. **`yamanashi_sheets.py`** finds and downloads the Yamanashi 2024 LiDAR products for one
   1:500 sheet (400 m × 300 m) from the prefecture's vector-tile index. It fetches the 0.5 m DEM,
   the 0.5 m DSM2 and the 0.25 m orthophoto. Licence: CC BY 4.0 / ODbL. Credit "山梨県 (Yamanashi
   Prefecture), 山梨県点群データ 2024".
2. **`depth_pano.py`** builds a scene from that sheet and renders equirectangular depth
   panoramas at eye height from viewpoints under closed canopy.
   - The ground is the real 0.5 m DEM.
   - There is one tree per canopy-height peak, at its real height. Trunk and crown shapes are
     placeholders.
   - Outputs are an EXR (radial metres), a log-encoded PNG, a preview and the viewpoint in
     EPSG:6676.
3. **`marble_api.py run`** makes two World API calls:
   - `pano:depth_to_rgb` turns the depth panorama and an Aokigahara prompt into a photographic
     panorama that follows the geometry;
   - `worlds:generate` turns that panorama into a Gaussian-splat world.

   It then downloads the SPZ splats, the collider mesh, the panoramas and the metric-scale
   metadata, and records every request, response and credit balance.
4. **`view_splats.mjs`** renders a world headless: from its origin and at increasing distances,
   in four headings. It uses the pre-installed Playwright Chromium and Spark 2.2, World Labs'
   three.js splat renderer.
5. **`score_walk.py`** measures each distance and writes `scores.json` and `contact_sheet.jpg`:
   - holes: the share of screen with no splats;
   - fine detail and edge density, comparable with the owner's photos;
   - the lighting metrics.

## Running it

It needs `WLT_API_KEY` set as an environment variable in the cloud environment's settings,
followed by a new session. Never paste the key into a chat. API credit is bought at
platform.worldlabs.ai, separately from the Marble app. The minimum is $5, which is 6,250
credits.

```bash
pip install mapbox-vector-tile tifffile pyproj scipy trimesh embreex OpenEXR pillow numpy
W=/tmp/marble && mkdir -p $W
python3 tools/marble_test/yamanashi_sheets.py --lat 35.4775 --lon 138.658 --out $W/data
python3 tools/marble_test/depth_pano.py --dem $W/data/dem/08LE9335.tif --dsm2 $W/data/dsm2/08LE9335.tif --out $W/panos --views 3
python3 tools/marble_test/marble_api.py credits
python3 tools/marble_test/marble_api.py run --pano $W/panos/08LE9335_v2 --out $W/worlds --model marble-1.0-draft   # 150 credits: pipeline check
python3 tools/marble_test/marble_api.py run --pano $W/panos/08LE9335_v2 --out $W/worlds --model marble-1.1         # 1,500 credits: the real test
(cd $W && npm init -y >/dev/null && npm i @sparkjsdev/spark@2.2.0 three@0.180.0)
node tools/marble_test/view_splats.mjs --splat $W/worlds/08LE9335_v2_500k.spz --out $W/walk/v2 --nm $W/node_modules --eye 1.6 --scale <1/metric_scale_factor>
python3 tools/marble_test/score_walk.py $W/walk/v2 --ref <owner photos>
```

`--scale` is `1 / metric_scale_factor` from `assets.splats.semantics_metadata` in the
downloaded record. It converts metres to the file's units, so the walk distances are real
metres.

## Budget

| Step | Credits | USD |
|---|---|---|
| Depth to RGB | not priced in the docs; recorded by the script | — |
| Draft world (`marble-1.0-draft`) | 150 | 0.12 |
| Standard world (`marble-1.1`) | 1,500 | 1.20 |

$5 covers one draft plus three standard worlds, with some margin for the depth step.

## Known limits

- **Placeholder trees.** Tree shapes are cones on cylinders. Only positions and heights are
  measured. Marble paints over them, but crown silhouettes come from the placeholder.
- **Loose geometry.** World Labs' docs say the depth-to-RGB model follows the geometry
  "loosely", and HY-World 2.0 (Tencent, April 2026) found Marble 1.0 deviates from its
  inputs.
- **Short reach.** WorldGen (Meta, November 2025) found quality falling 3–5 m from the origin in
  an earlier Marble. Measuring that on the real terrain is the point of step 4.
- **Coordinate conventions.** The depth panorama's centre column faces grid north. Marble's
  exported frame is y-down (OpenCV-style); `view_splats.html` flips it by default. Check the
  heading alignment against the depth panorama before placing worlds on the terrain.
