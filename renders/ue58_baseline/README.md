# UE5.8 baseline frames

Frames captured by the owner from the Unreal Engine 5.8 build of this world (Metal SM6, Lumen,
Nanite), made on the MacBook Air before the UE project was abandoned and the engine deleted. They
are kept as the visual baseline that any replacement engine is judged against. All frames are
1280 × 800 except the before/after strip and frames `l` and `m` (1280 × 720).

The owner's most valued result from that attempt was the natural lighting, best seen in frames
`g` to `j`: dappled sun through the canopy, a dark sky-occluded understorey, bright sky gaps, cool
shadows and warm sunlit highlights.

| File | View |
|---|---|
| `ue58_a_moss_boulders.jpg` | Moss boulder field under open canopy (converted from the owner's PNG) |
| `ue58_b_moss_mound.jpg` | Moss mound and lava rise, saplings |
| `ue58_c_rock_mound_wide.jpg` | Wider view of the same rise |
| `ue58_d_gully_log.jpg` | Rocky gully with a leaning log |
| `ue58_e_boulder_close.jpg` | Close boulder, moss floor |
| `ue58_f_before_after_wide.webp` | Before/after strip from one iteration, showing dithered masked materials |
| `ue58_g_dappled_haze.jpg` | Dappled sun with blue aerial haze |
| `ue58_h_dark_interior.jpg` | Dark forest interior with a single sunfleck |
| `ue58_i_fern_sunfleck.jpg` | Ferns catching sun against dense trunks |
| `ue58_j_rock_fern_sun.jpg` | Rocks and ferns under canopy light |
| `ue58_k_rock_fern_sun_alt.jpg` | Same view as `j`, brighter exposure |
| `ue58_l_trail_sunflecks.jpg` | Trail through open pines, sunflecks (1280 × 720, added 23 September) |
| `ue58_m_rock_slab_tiling.jpg` | Rock slab and boulder in sun, showing hard-edged, repeating ground textures (1280 × 720, added 23 September) |

## Lighting metrics

`lighting_stats.json` holds the output of `tools/lighting_stats.py` for every JPEG frame here.
Re-run it on a candidate engine's renders from comparable viewpoints and compare the figures:

```bash
python3 tools/lighting_stats.py renders/ue58_baseline/*.jpg
python3 tools/lighting_stats.py path/to/candidate/*.png
```

What separates the frames the owner valued (`g`–`j`) from the flatter UE5.8 frames (`a`–`e`) and
from the earlier Three.js viewer (`renders/after_p4/C1`, `C3`):

| Metric | `g`–`j` (target) | `a`–`e` | Three.js pass 2 |
|---|---|---|---|
| `sunfleck_fraction` — ground pixels brighter than 4 × the ground median | **0.07–0.16** | 0.01–0.03 | 0.03–0.04 |
| `log_avg_luminance` — exposure key | **0.003–0.008** | 0.02–0.04 | 0.02–0.03 |
| `black_fraction` — pixels darker than about 7/255 | **0.17–0.43** | 0.00 | 0.05–0.10 |
| `highlight_blue_ratio` — B/R of the brightest ground pixels (below 1 is warm) | **0.29–0.42** | 0.54–0.76 | 0.39–0.76 |
| `shade_blue_ratio` — B/R of the shade band above the black floor | 0.60–1.28 | 1.05–1.19 | 0.48–0.49 |
| `stops_p01_p99` — dynamic range | 8.5–10.2 | 3.3–5.7 | 10.0–10.9 |
| `sky_peak` — brightness of sky gaps, 95th-percentile 8-bit | 176–243 | 221–228 | 235–246 |

In words: the valued look has many sharp sunflecks on the floor, a low overall exposure, genuinely
deep shade under the canopy, and warm sunlit patches. The first three rows separate it cleanly from
the flatter frames and from the Three.js viewer. Warm highlights separate it from the flatter UE5.8
frames but overlap one Three.js camera (`C3`, 0.39). Shade colour does not separate it: it runs from slightly warm
to slightly cool across `g`–`j`, so it is a sanity check (the Three.js viewer's brown 0.48 is
outside it) rather than a target. Dynamic range alone is not a match either, because the Three.js
viewer's wide range comes from near-black trunks rather than from sunlit patches.

`sky_peak` does not separate the frames either, but it catches a different failure: sky gaps that
render dull and grey. The first Godot prototype scored 109–132 there. Nothing in this set of
metrics detects the flat, pale, textureless sky of frames `a`–`e`; that flaw is judged by eye on a
contact sheet.

**Correction, 23 September 2026.** The first version of this table reported a per-pixel
`shadow_blue_ratio` of 1.16–1.73 for `g`–`j` and read it as "cool, sky-lit shadows". That metric
averaged B/R over the darkest pixels, where JPEG noise dominates. It moved from 1.23 to 1.63 when
the same render was re-encoded from PNG to JPEG. It has been replaced by the band-based
`shade_blue_ratio` above, and the claim of cool shadows is withdrawn.

These are JPEG screen captures, not HDR buffers, so the numbers describe the displayed image
after tonemapping. They are a comparison aid, not a physical measurement. Compare renders at the
same resolution, and prefer PNG for candidate renders.

## Frames `l` and `m`

These two were added later from the same build. They are brighter than the target look: exposure key 0.040 and
0.076, and almost no near-black pixels (black fraction 0.001 and 0.000). So they are not lighting targets. They are
kept because they show the build's typical content away from the best views:
- evenly spaced pines with visibly flat crown cards over an open, grassy floor, unlike the dense moss-and-lava forest;
- in `m`, square, hard-edged patches where two ground materials meet, and a visibly repeating rock texture.

