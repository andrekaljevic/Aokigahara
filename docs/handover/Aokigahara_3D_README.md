# Aokigahara: exportable 3D reconstruction

This package contains actual three-dimensional geometry and PBR materials, a continuous walk/fly viewer, editable glTF exports, and the spatial data used to place the scene. It is a geographically anchored reconstruction with substantial procedural content. It is not a surveyed digital twin or a finished AAA-quality environment.

## Open the models

**Start with Aokigahara_World.glb** for the assembled landscape. It combines the detailed corridor, surrounding terrain and wider instanced forest, with duplicate local ground and vegetation groups removed. It requires EXT_mesh_gpu_instancing. Use the separate standard Corridor/Terrain files if your application does not support that extension.

- **Aokigahara_Cave_Corridor.glb**: a 2.048 km × 2.048 km ground scene (4.194 km²) around the Fugaku–Narusawa corridor. Standard glTF 2.0, embedded materials, 53,999 independently placed mature trees using shared meshes, mapped path surfaces, and representative ferns, timber and rocks near the starting station. Four nearby mature fir representatives use a licensed textured model. These are not exact species or surveyed individuals. Detailed tree geometry is concentrated within 120 m of the initial station; trees elsewhere use simplified crowns.
- **Aokigahara_Surface_Terrain.glb**: one continuous 32 km × 30 km terrain surface (960 km²), combining the detailed corridor, study terrain and regional context. 895,734 triangles. Includes actual Mount Fuji relief. Use this OR the Regional Terrain, not both overlaid. Core terrain in this file overlaps the Corridor ground.
- **Aokigahara_Regional_Terrain.glb**: standalone regional terrain at coarser sampling, 524,288 triangles, for a lighter context import.
- **Aokigahara_Instanced_Forest.glb**: 467,601 procedural placements in 744 spatial groups. Simplified canopy geometry; requires **EXT_mesh_gpu_instancing** support. It contains vegetation only. The footprint is mapped forested communities intersected with Jōgan deposits, plus the modelling square. It is a project interpretation, not the boundary of the place name or a tree census. The first 53,999 placement records duplicate the local corridor population; remove the overlap before combining layers.

Import at scale **1 unit = 1 metre**. Preserve shared meshes/instances: realising every tree into unique geometry can consume substantial memory. Ordinary glTF import is sufficient for the Corridor and terrain files. The wider forest requires an importer supporting its stated extension; the raw transform buffer is also provided for another engine's instancing system. No claim is made that a particular DCC import was tested.

## Coordinate frame

Origin: longitude 138.658°, latitude 35.4775°, WGS84. Horizontal projection:
`+proj=aeqd +lat_0=35.4775 +lon_0=138.658 +datum=WGS84 +units=m +no_defs`

Scene x points east; z points south; y points up. Scene y = published GSI elevation in metres minus **900 m**. The subtraction is an origin shift, not a vertical-datum conversion. No vertical exaggeration is used. Inverse-project `(x, -z)` to recover longitude/latitude. Do not treat Web Mercator coordinates as scene metres.

The starting station is approximately x=32.14 m, z=-9.84 m, at 1001.4 m published elevation. Landmark positions are map-derived approximations. The detailed terrain uses 8 m output sampling from the acquired DEM5A web grid (~7.78 m source ground pixel); it is not a native 1 m survey. The 5 m designation describes the underlying GSI product, not every exported vertex interval.

## Viewer

Open the supplied hosted viewer, or run the bundled `launch_viewer.py` with Python and open the printed local address. Directly opening an HTML file will not reliably load module and binary assets.

Desktop: enter the forest; WASD/arrows move; mouse looks; Shift moves faster. Escape releases the pointer. Fly mode adds E/Space up and Q/Ctrl down. On touch devices use the two pads. The controls include forest/cave-approach/lake/Fuji locations, sun elevation, haze, detail level and downloads. Sun and haze are adjustable visual states, not a reconstructed date-specific weather record.

The viewer streams nearby procedural vegetation over the measured landscape. It includes a 256 m patch export with the currently loaded trees, ground detail and path segments. The mature-tree and sapling assets are generic representatives; they do not establish local botanical identity. Hardware/browser performance varies; Balanced avoids the optional high-resolution sapling load.

## Evidence and limits

**Source-constrained:** GSI macro terrain and aerial coverage, MOE community mapping, GSJ eruptive-deposit geometry and OSM mapped line/point relationships. Height grids and quality masks retain source distinctions. All three acquired height grids contain finite numerical data, with no nearest-neighbour nodata fills. Regional fallback data is coarser than the detailed corridor. Surface triangulation changes interpolation between samples; it adds no surveyed detail.

**Procedural:** every individual tree placement, mature-tree form, root network, fine stone/deadwood distribution, path width and many ground materials. Representative Poly Haven materials/models are CC0; they were not captured at Aokigahara. Japanese cedar bark is not confirmed hinoki, the rough-rock material is not a verified basalt scan, and the fir/fern species are not verified local species. Crown variation and ground roughness are not a calibrated ecological simulation.

**Not reconstructed:** complete cave interiors, accurate cave-mouth/visitor-building meshes, current signs/barriers and their measured dimensions, individual-tree survey, lava fissures/overhangs below DEM sampling, accurate bathymetry or calibrated seasonal lighting. Cave destinations are surface approach references, not completed cave models. Do not infer underground connections from the terrain.

The attached master dossier was audited rather than accepted uncritically. Its un-ingested DEM/geology/vegetation statements were superseded by acquired data. Its 250 m confidence grid remains heuristic, not a measured coverage assessment. Conflicting cave lengths and incorrect cave-source cross-links are retained in the evidence audit. The 2026 upload of an English ecotour guide contains older guidance; it is not a new route survey.

## What was checked

GLB headers, declared byte lengths, buffers, indices, embedded-image decoding and finite coordinates were validated. Terrain source/export checks found no degenerate or downward-facing terrain triangles. The viewer's Three.js loader parsed the tree library and terrain, and accelerated ground intersections were checked at the starting point, both visitor-cave locations and Fuji context. Standard model geometry was rendered for inspection. Browser interaction and target DCC applications were not exercised in this session.

## Sources and reuse

Retain `provenance.json`, source manifests and their attributions with derivatives. GSI terrain/aerial content is attributed to the Geospatial Information Authority of Japan under its stated public-data terms; GSJ geology to GSJ/AIST; vegetation mapping to Japan's Ministry of the Environment. OSM paths and mapped features: © OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright). Poly Haven source models/materials: CC0 (https://polyhaven.com/license), with creators preserved in the manifests. Three.js and three-mesh-bvh retain their MIT licence files.

Source entry points: https://maps.gsi.go.jp/development/ichiran.html ; https://www.gsj.jp/Map/EN/volcano.html ; https://www.biodic.go.jp/ ; https://polyhaven.com/a/fir_tree_01 . Full asset URLs, transformations, checksums and qualifications are in the manifests. No AI-generated images or models were used as factual evidence.

## Production pass 2 (2026-09-10)
See HANDOVER.md and Aokigahara_3D_Provenance.json → productionPass2. Runtime now renders a near-field procedural lava/moss ground system, tree library v2 with surface roots and spray-card foliage, densified stand structure, deadwood/rocks/ferns and three daylight presets. Before/after evidence: renders/BEFORE_AFTER_*.jpg (identical cameras).
