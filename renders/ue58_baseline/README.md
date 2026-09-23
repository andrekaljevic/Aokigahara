# UE5.8 baseline frames

Frames captured by the owner from the Unreal Engine 5.8 build of this world (Metal SM6, Lumen,
Nanite), made on the MacBook Air before the UE project was abandoned and the engine deleted. They
are kept as the visual baseline that any replacement engine is judged against. All frames are
1280 × 800 except the before/after strip.

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

## Lighting metrics

`lighting_stats.json` holds the output of `tools/lighting_stats.py` for every JPEG frame here.
Re-run it on a candidate engine's renders from comparable viewpoints and compare the figures:

```bash
python3 tools/lighting_stats.py renders/ue58_baseline/*.jpg
python3 tools/lighting_stats.py path/to/candidate/*.png
```

What separates the frames the owner valued (`g`–`j`) from the flatter UE5.8 frames (`a`–`e`) and
from the earlier Three.js viewer (`renders/after_p4/`):

| Metric | `g`–`j` | `a`–`e` | Three.js pass 2 |
|---|---|---|---|
| `sunfleck_fraction` — ground pixels brighter than 4 × the ground median | 0.07–0.16 | 0.01–0.03 | 0.03–0.04 |
| `shadow_blue_ratio` — mean B/R in the darkest 20 % | 1.16–1.73 | 1.05–1.14 | 0.53–0.55 |
| `log_avg_luminance` — exposure key | 0.003–0.008 | 0.02–0.04 | 0.02–0.03 |
| `stops_p01_p99` — dynamic range | 8.5–10.2 | 3.3–5.7 | 10.0–10.9 |

In words: the valued look has many sharp sunflecks on the floor, sky-lit shadows that read cool
rather than brown, a low overall exposure, and a wide range that the tonemapper holds without
clipping. The Three.js viewer's wide range comes from near-black trunks rather than from sunlit
patches, so range alone is not a match.

These are JPEG screen captures, not HDR buffers, so the numbers describe the displayed image
after tonemapping. They are a comparison aid, not a physical measurement.
