# Distant-ground repair — identical-camera evidence

`before/` is the recovered pass-2 viewer as it stood at the canonical checkpoint (main, 859ab5d).
`after/` is the same viewer with the base-terrain layer weights supplied. Same cameras, same
presets, same 1280 x 800 viewport, same software-GL renderer.

The defect: the corridor terrain shares the near-field patch's layered ground material but shipped
no `aWeights` vertex attribute, so the shader read the WebGL default for an unbound attribute,
(0, 0, 0, 1) - pure trail. The guard intended to catch that tests the sum against 0.01, and
(0, 0, 0, 1) sums to 1, so it never fired. Everything beyond the 120 m patch shaded as compacted
trail cinder.

Measured layer weights, mean over all vertices:

| Surface | moss | rock | litter | trail |
|---|---|---|---|---|
| Near-field patch (already correct) | 0.544 | 0.153 | 0.267 | 0.035 |
| Base terrain, before | 0.000 | 0.000 | 0.000 | 1.000 |
| Base terrain, after | 0.468 | 0.206 | 0.311 | 0.015 |

Pixel difference, before vs after:

| Camera | mean abs difference per pixel | pixels changed |
|---|---|---|
| D4_above_canopy_look_out | 3.694 | 19.86% |
| D5_above_canopy_look_down | 4.009 | 26.82% |
| D6_patch_boundary | 1.421 | 9.03% |
| D1_midfield_from_start | 0.401 | 2.18% |

The eye-level cameras change least because canopy and trunks occlude most distant ground; the
elevated cameras show the full extent of the defect.

`near_field_regression_audit.json` records the eight standard cameras re-rendered after the fix.
All eight still reproduce the source session's triangle and draw-call counts exactly, and the two
cameras that see only near-field ground (C2_start_lookdown, C5_fugaku_approach) are bit-identical,
confirming the near-field path was not touched.
