# Broadleaf library — before / after evidence

The deciduous component of the forest was the one part of the stand that tree library v2 never
reached. Until this pass it kept the Pass-1 representation: untextured flat geometry
(`map=false`, `alphaTest=0`, `color=#c4cead`), coloured in the runtime because no foliage source
existed for it, and with no `far` mesh, so the runtime substituted the `low` mesh at every distance
beyond about 50 m. Counted from `tree-library.glb`: `tree_2_high` is **27,656 triangles**, more
than twice the most expensive conifer in library v2, and `tree_2_low` is 842 — what every distant
broadleaf rendered at, however far, against **32** for a conifer impostor at the same range.

`before/` is the state immediately prior — the recovered `viewer/app.js` with the Pass-1
`tree-library.glb`. `after/` is the same six cameras with `tree-library-broadleaf.glb` wired in.
Nothing else differs: same server, same terrain, same placements, same presets, same viewport.
`regression/` is the eight standard audit cameras (`harness/cams2.json`) re-rendered afterwards to
show the near field is untouched.

Side-by-side plates are at `renders/BEFORE_AFTER_B*.jpg`.

| Camera | What it shows | triangles before | after | pixels changed |
|---|---|---|---|---|
| B1_deciduous_stand | Stand interior at eye level | 9,296,860 | 8,219,201 | 61.0 % |
| B2_deciduous_lookup | Looking up into the crowns | 9,590,821 | 8,513,162 | 56.3 % |
| B3_deciduous_above | Above the canopy, 34 m | 8,998,032 | 7,920,373 | 50.3 % |
| B4_deciduous_midfield | Mid-distance across the stand | 8,301,705 | 8,006,357 | 55.1 % |
| B5_deciduous_distance | Elevated to 95 m, overcast | 3,947,641 | 3,402,948 | 9.4 % |
| B6_deciduous_edge | Stand edge, clear midday | 9,446,789 | 8,684,864 | 74.0 % |

Both runs recorded zero console errors, zero page errors and zero failed requests.

The pixel-change column was measured on the renderer's lossless output. The frames archived here
are JPEG at quality 92, matching how `renders/distant_ground_fix/` and the rest of this directory
store evidence, so re-running `tools/compose_before_after.py` over them reports 2–3 points higher
(63.7, 60.7, 53.5, 57.6, 10.1, 76.3 %). That excess is compression noise crossing the tool's
8/255 threshold, not a difference in the renders.

Read the numbers with the pictures. B5 changes only 9.4 % of pixels because at 95 m most of the
frame is conifer, ground and haze, and the broadleaves occupy one corner — but it drops the most
triangles of any camera (−13.8 %), because that is the camera where the missing `far` impostor was
costing the most. B6 changes 74 % because a broadleaf crown fills it.

## What these renders do *not* show

The bare middle-distance band across `after/B3_deciduous_above.png`, and the thin poles across
`after/B5_deciduous_distance.png`, are **conifers**, not broadleaves, and they are unchanged by this
pass: the same band is present in `before/` and at the `main` checkpoint. The conifer `low` meshes
have the same defect this pass fixed for the broadleaves — spray cards sized off the shoot rather
than off the crown — and fixing it means regenerating `tree-library-v2.glb`, which is a separate
pass because it would change the canonical asset the recovery regression is pinned to. See
`docs/PROJECT_STATE.md` §6.4a.

Rendered under software OpenGL (SwiftShader) at 1280 × 800. No frame rate is claimed.

Regenerate with:

```bash
python3 launch_viewer.py --port 8765 --quiet &
node tools/audit_render.mjs http://127.0.0.1:8765/viewer/ renders/broadleaf_library/after tools/cams_broadleaf.json 1280 800
python3 tools/compose_before_after.py renders/broadleaf_library BEFORE_AFTER_ "Pass-1 broadleaf (before)" "Broadleaf library (after)"
```
