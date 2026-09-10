# Distant-ground repair — identical-camera evidence

Three passes, same cameras, same presets, same 1280 x 800 viewport, same software-GL renderer.

| Folder | State |
|---|---|
| `before/` | The canonical checkpoint (`main`, 859ab5d) as recovered |
| `after_weights_only/` | Base-terrain layer weights supplied; canopy constant still 0.62 |
| `after/` | Weights supplied and the canopy constant unified — current `dev` |

## Defect 1 — the base terrain shaded as pure trail

The corridor terrain shares the near-field patch's layered ground material, which reads a per-vertex
`aWeights` attribute, but that geometry ships no such attribute. WebGL supplies (0, 0, 0, 1) for an
unbound attribute. The guard written to catch exactly this tests the sum against 0.01, and
(0, 0, 0, 1) sums to 1, so it never fired. Everything beyond the 120 m patch shaded as compacted
trail cinder.

The shader was never wrong, so it is unchanged. `buildBaseWeights()` supplies what it expects,
evaluating the same moss/rock/litter/trail model the patch uses over the same procedural lava
relief and noise fields, across 66,306 corridor vertices at load.

| Surface | moss | rock | litter | trail |
|---|---|---|---|---|
| Near-field patch (always correct) | 0.544 | 0.153 | 0.267 | 0.035 |
| Base terrain, before | 0.000 | 0.000 | 0.000 | 1.000 |
| Base terrain, after | 0.468 | 0.206 | 0.311 | 0.015 |

## Defect 2 — a brightness step that followed the camera

With the materials matched, a second seam became the visible one. The canopy term is spatial and
continuous, `(0.8 + 0.2 * world noise)`, but the base material scaled it by a further 0.62 while the
patch used 1.0 — a 38 % albedo step along an edge that is rebuilt around the camera every 12 m. A
constant like that cannot produce anything except a seam that follows the player, so one value now
serves both surfaces and the floor is continuous by construction.

## Combined effect, before vs after

| Camera | mean abs difference per pixel | pixels changed |
|---|---|---|
| D4_above_canopy_look_out | 12.322 | 37.55% |
| D5_above_canopy_look_down | 14.378 | 44.99% |
| D6_patch_boundary | 6.585 | 26.5% |
| D1_midfield_from_start | 1.84 | 7.52% |

Eye-level cameras change least because canopy and trunks occlude most distant ground; the elevated
cameras show the defects at full extent.

## Not caused by this work

Magnifying the distant ground reveals a fine dotted moire. It is texture aliasing at oblique angles
under the software renderer and it pre-dates these changes. Measured as the fraction of image energy
in the 3-12 pixel band over the same crop:

| Pass | high-frequency energy fraction |
|---|---|
| Fable session render, `after_p4/C1_start_corridor` | 0.450 |
| Fable session render, `after_p4/C2_start_lookdown` | 0.441 |
| Checkpoint, base terrain as pure trail | 0.432 |
| Current `dev` | 0.448 |

Brightening the surface raised it by about 4 % relative, which is the surface becoming visible
rather than a new artifact. Whether it appears on hardware GL has not been tested.

## Regression

`near_field_regression_audit.json` records the eight standard cameras re-rendered after both fixes.
All eight still reproduce the source session's triangle and draw-call counts exactly with zero
console errors, and the two cameras that see only near-field ground (`C2_start_lookdown`,
`C5_fugaku_approach`) remain bit-identical to the checkpoint.
