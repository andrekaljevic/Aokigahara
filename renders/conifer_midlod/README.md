# Conifer mid-detail LOD — before / after evidence

The broadleaf pass exposed this defect and could not fix it: across the whole middle distance the
stand thinned to bare poles. It is the conifers, and it was there from the start — visible in the
`before/` frames of `renders/broadleaf_library/` and at the `main` checkpoint.

`tree-library-v2.glb` switches a conifer to its mid-detail mesh at 46 m (balanced) or 62 m (high)
and holds it there to 230 m, which is most of the visible forest. Measured in the running page from above the canopy at the corridor start, that tier carries **8,092 of the instanced stems** against 400 at high detail and 5,732 impostors: more than either of the tiers either side of it. That mesh carried four
crown-mass cards, sized `cw*1.1` and then passed through `sz*h*1.15` where `h` is the atlas box's
height as a fraction of the atlas, about 0.39. The result was roughly **2 m of card inside a crown
12 m across** — a sixth of the width, four times over. The same mistake the Pass-1 broadleaves
made, in the library that otherwise got everything right.

They are now sized in metres, and each is seeded on a vertex of the foliage the branch pass has
already built, jittered slightly. Sampling the real distribution rather than a guessed cone means
the added mass lands where that tree's branches actually are, so the hemlock keeps its spreading,
drooping laterals and the cypress its ascending ones with no per-species tuning.

## What changed, exactly

Regenerating and grafting the shipped texture payload back (`tools/rebuild_tree_library.sh`) leaves
**28 of 37 meshes byte-identical** to the library the original session shipped. The nine that
changed are all and only mid-detail meshes:

```
tsuga_a_low tsuga_b_low tsuga_c_low hinoki_a_low hinoki_b_low hinoki_c_low
sap_tsuga_low sap_hinoki_low sap_small_low
```

Every `_high` and `_far` mesh, and every snag, log and rock, is untouched. Verify with
`python3 tools/compare_glb.py`.

| Mesh | before | after |
|---|---|---|
| tsuga_a / b / c `_low` | 906 / 914 / 890 | 1,066 / 1,114 / 1,026 |
| hinoki_a / b / c `_low` | 813 / 805 / 744 | 929 / 961 / 836 |
| sap_* `_low` | 426 | 474 |

The file grows from 12,521,860 to 12,610,808 bytes.

## Cost

| Camera | triangles before | after | change | draw calls | pixels changed |
|---|---|---|---|---|---|
| M1_canopy_start | 7,090,998 | 7,568,142 | +6.7 % | 94 → 94 | 21.9 % |
| M2_high_overlook | 3,393,799 | 3,657,275 | +7.8 % | 58 → 58 | 17.6 % |
| M3_eye_level_through_stand | 7,405,713 | 7,882,857 | +6.4 % | 99 → 99 | 9.0 % |
| M4_fugaku_overcast | 3,595,448 | 3,861,588 | +7.4 % | 55 → 55 | 24.1 % |
| M5_east_clear | 5,122,279 | 5,402,615 | +5.5 % | 70 → 70 | 20.2 % |
| M6_narusawa_canopy | 4,930,923 | 5,203,911 | +5.5 % | 67 → 67 | 20.7 % |

This pass **costs** triangles where the broadleaf pass saved them: 5.5–7.8 % more per frame, no
additional draw calls. That is the honest trade. `M4_fugaku_overcast` shows what it buys — a
see-through lattice of bare stems with the forest floor visible between them becomes a closed
canopy. `M3` changes least in pixels (9.0 %) because it is at eye level, where the near field is
already high-detail and the mid distance is largely occluded by trunks.

Zero console errors, zero page errors and zero failed requests in both runs.

The pixel-change column was measured on the renderer's lossless output; the frames archived here
are JPEG at quality 92, so re-running `tools/compose_before_after.py` over them reports slightly
higher. That excess is compression noise crossing the tool's 8/255 threshold.

`regression/` is the eight standard audit cameras with both this pass and the broadleaf library in
place, against `renders/audit_recovery/audit.json`:

| Camera | checkpoint | now | change | draw calls |
|---|---|---|---|---|
| C1_start_corridor | 7,507,695 | 7,882,857 | +5.0 % | 95 → 99 |
| C2_start_lookdown | 7,200,799 | 7,574,455 | +5.2 % | 86 → 90 |
| C3_offpath_trunks | 7,153,585 | 7,454,639 | +4.2 % | 92 → 92 |
| C4_path_ahead | 7,702,147 | 8,103,687 | +5.2 % | 89 → 89 |
| C5_fugaku_approach | 7,111,871 | 7,592,975 | +6.8 % | 87 → 87 |
| C6_arbitrary_east | 7,353,326 | 7,673,065 | +4.3 % | 91 → 94 |
| R1_img013_geotag_overcast | 7,861,107 | 8,347,006 | +6.2 % | 94 → 94 |
| C1_start_corridor_overcast | 7,507,695 | 7,882,857 | +5.0 % | 95 → 99 |

`C5_fugaku_approach` was the exact control for the broadleaf pass — no deciduous stem falls in that
frame, so it did not move at all. It moves now, by the most of any camera, which is the expected
sign: it is a pure conifer stand, so it is exactly where a conifer change should show.

Rendered under software OpenGL (SwiftShader) at 1280 × 800. No frame rate is claimed.

## Not fixed here

The `far` impostor — three crossed cards from 230 m out — was not touched. It is cheap and it is
what the horizon is made of; whether it holds up is a separate question from this one, and
changing it would have put `_far` meshes in the changed list and muddied this comparison.
