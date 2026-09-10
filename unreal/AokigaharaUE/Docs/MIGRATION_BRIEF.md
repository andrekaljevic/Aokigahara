# Aokigahara → Unreal Engine 5.8: cold-start brief

**Written from a Linux container that could not run Unreal.** Everything below was verified by
running code against the repository; nothing here is inferred or remembered. The Unreal work
itself — project creation, landscape import, rendering, profiling — has **not** been started,
because that requires the Mac.

Read this first, then `docs/PROJECT_STATE.md` at the repository root for the web build's history.

---

## 1. Repository state at the point of handover

| | |
|---|---|
| Branch for this work | `ue5.8/aokigahara-production` (branched from `dev/generational-visual-upgrade`) |
| `main` | `c32be30` — the canonical Fable Pass-2 checkpoint plus the Pages workflow |
| `dev/generational-visual-upgrade` | `de637bb` — broadleaf library + rebuilt conifer mid-LOD |
| Live web build | https://andrekaljevic.github.io/Aokigahara/ (deploy runs on `main`, publishes `dev`) |
| Integrity | `python3 tools/verify_manifest.py` → 0 unexpected mismatches, 0 LFS pointers |

The web build is the **baseline, not the target**. Do not delete or rewrite it. `main` must keep
verifying byte-for-byte against the Pass-2 manifest.

---

## 2. Coordinate frame — the single most important thing to get right

Source projection, used by every asset in this repository:

```
+proj=aeqd +lat_0=35.4775 +lon_0=138.658 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs
```

Source scene convention: **x = east, z = south, y = up, 1 unit = 1 metre**, and

```
source_y = published GSI elevation (m MSL) − 900
```

That 900 m is an origin shift, **not** a vertical datum conversion. Local terrain elevations run
933.39–1064.52 m MSL; the regional grid spans 243.68–3765.62 m MSL (the top of that range is Fuji).

### Proposed Unreal mapping (verify before global use)

Unreal is X = forward/north, Y = right/east, Z = up, in **centimetres**. The brief proposed
X = east, Y = north. Taking that:

```
UE_X_cm = source_x_m × 100
UE_Y_cm = −source_z_m × 100        # source z is SOUTH, so negate to get north
UE_Z_cm = source_y_m × 100         # already elevation − 900
```

**This is a left/right-handed flip and it is the classic place to introduce a mirrored world.**
Do not accept it on inspection. Verify numerically against control points whose real-world
position is independently known — the georegistration control points and the IMG-013 camera
geotag are in `docs/research/`, and the viewer's destination table in `viewer/app.js` carries
known scene positions (e.g. Fugaku Wind Cave approach at source x −38, z −18; Narusawa Ice Cave
at 785, 284). Round-trip at least three of them through the AEQD projection back to WGS 84 and
compare against the published coordinates before building anything on top.

If you keep the elevation shift, **document it in the level** — a UE Z of 0 is 900 m MSL, not sea
level. Alternatively drop the shift for Unreal and use true MSL; either is fine, but pick one,
write it down, and make every importer agree.

---

## 3. Terrain source data — use this, not the GLB

`viewer/assets/terrain/` holds three GSI-derived elevation grids, and they are **fully
self-describing**: each `<id>-height.json` carries width, height, bounds, step, encoding, layout,
sample positions, the height offset, the projection and a per-cell quality class. Build the UE
Landscape from these, not by laying `models/Aokigahara_Surface_Terrain.glb` under the scene.

| grid | samples | extent (source m) | step | notes |
|---|---|---|---|---|
| `local` | 257 × 257 | x −1024…1024, z −1024…1024 | 8.0 × 8.0 m | 100 % GSI DEM5A (quality class 1) |
| `study` | 513 × 385 | x −9000…10500, z −6000…8000 | 38.09 × 36.46 m | 88 % class 1, 12 % class 2 |
| `regional` | 513 × 513 | x −14000…18000, z −11000…19000 | 62.5 × 58.59 m | 25 % class 1, 75 % class 2 fallback |

- Encoding: `float32` little-endian, **row-major, `index = row*width + column`**
- Sample position: `x = minX + column*dx`, `z = minZ + row*dz`, **both edges inclusive**
- Values are elevation in metres MSL, **unshifted** — subtract 900 to get scene Y
- `<id>-quality.u8` is a parallel `uint8` grid: 0 = no source, 1 = DEM5A ~7.78 m, 2 = numeric DEM
  z12 ~31 m fallback, 3 = nearest-neighbour fill. Nothing is class 0 or 3 anywhere.

The regional grid is the 32 × 30 km context and is where Fuji comes from — it is real relief, not
a backdrop mesh. Note the resolution asymmetry: 8 m in the playable core, ~60 m regionally. Do not
let a single uniform Landscape resolution either waste memory on the far field or destroy the core.

**Heightmap export gotchas.** UE Landscape wants 16-bit unsigned, with resolution
`(componentCount × quadsPerComponent) + 1`. Choose the Z scale so the full elevation range maps
into 0–65535 without clipping, and record the exact `Landscape Scale` you used — getting this
wrong is the usual cause of "the terrain looks right but everything is 1.7× too tall".

---

## 4. Forest placement data — 467,601 real placements, empirically validated

Two files, both **flat arrays of 6 × `float32` little-endian per record**:

| file | records |
|---|---|
| `data/forest-wide.f32` | 467,601 |
| `viewer/assets/forest-instances.f32` | 53,999 |

**The corridor file is byte-identical to the first 53,999 records of the wide file** — verified with
`np.array_equal`. So the total number of unique placements is **467,601, not 521,600**. Ingest the
wide file only.

Record layout, confirmed by reading `viewer/app.js` *and* by checking value ranges:

| index | meaning | wide-set range |
|---|---|---|
| 0 | x, east, metres | −5705.29 … 3776.47 |
| 1 | y, scene metres (elevation − 900) | −0.23 … 628.25 |
| 2 | z, south, metres | −2697.03 … 5974.79 |
| 3 | uniform scale | 0.720 … 1.220 |
| 4 | yaw, **radians** | 0 … 2π |
| 5 | vegetation community class | 0 … 3 |

Class histogram across the wide set: `{0: 204243, 1: 203551, 2: 30015, 3: 29792}`. Classes 0 and 1
dominate at ~44 % each; classes 2 and 3 are ~6 % each. In the web runtime, class ≥ 2 is what biases
a stem toward broadleaf.

The placements cover roughly 9.5 × 8.7 km — much smaller than the 32 × 30 km terrain. Beyond that
footprint the web build generates stems procedurally on a grid; see `collectTrees()` in
`viewer/app.js`. Decide deliberately whether Unreal reproduces that or uses PCG for the far field.

`viewer/app.js` also applies a **deterministic per-instance augmentation** on load
(`augmentForest()`): size-class multipliers, a ~6 % snag conversion, small tilt on two axes, and
the variant choice. That logic is worth reading before deciding whether to reproduce it, replace
it with PCG, or bake it into the exported data.

---

## 5. What exists to carry forward, and what to leave behind

**Worth ingesting**
- The three elevation grids and their quality masks (§3)
- The 467,601 placements with class and scale (§4)
- Land-cover / Jōgan / quality `.u8` masks in `viewer/assets/terrain/`
- Trail centre-lines in `viewer/assets/terrain/{local,study}-context.json` — OSM-derived, with an
  `access` field; the web build skips `private`/`no`
- The research corpus in `docs/research/` — 250 m evidence grid, control points, the community
  survey, the blueprint

**Reference only, not final assets**
- `viewer/assets/tree-library-v2.glb`, `tree-library-broadleaf.glb` — procedural card-based trees.
  Useful for silhouette, proportion, scale distribution and species mix. Their foliage is alpha-cut
  cards and will not survive close first-person inspection in UE.
- `models/Aokigahara_Surface_Terrain.glb` — an 8 m resample. Use as a **validation reference** to
  check the Landscape against, not as the terrain itself.

**Two lessons from the web build that transfer directly**

1. *A crown is a volume, not a plate.* Emitting every primary limb from one fork gives a flat
   umbrella. Stagger limb origins up a continuing leader.
2. *Atlas boxes are scaled by the card, not the leaf.* A card ~1 m across showing a box that holds
   16 large leaves puts each lamina at ~0.35 m — five times life size. This bug shipped twice in
   this project, in the Pass-1 broadleaves and in the conifer mid-LOD. In Unreal the equivalent
   trap is billboard/impostor texel density. Check leaf size against a metre reference explicitly.

---

## 6. Hardware reality — read before designing the renderer

Target machine is a **MacBook Air (Mac14,2), Apple M2, 8 cores (4P + 4E), 16 GB unified memory,
fanless**. See `MACHINE_AUDIT.md`, and re-run the detection there for real — the values in it came
from a screenshot, not from `system_profiler` on the machine.

Honest constraints, not pessimism:
- **Fanless.** Sustained GPU load throttles. Benchmark after 10 minutes of load, not from a cold
  start, or the numbers will not reproduce.
- **16 GB unified**, shared between macOS, the editor and the GPU. Nanite + Virtual Shadow Maps +
  Lumen over dense foliage is memory-hungry; budget deliberately.
- **Lumen: software ray tracing only** in practice — verify, do not assume hardware RT.
- **Nanite foliage / assemblies are experimental in 5.8.** Benchmark in isolation before the whole
  forest depends on them, and keep an instanced-static-mesh fallback, exactly as §11 of the brief says.
- A 32 × 30 km World Partition world with AAA near-field density is a workstation-class target.
  Expect to spend most of the budget on Tier A (0–50 m) and to lean hard on HLOD and impostors
  beyond it.

---

## 7. Suggested order of work

The brief's §48 priority order is sound. Concretely:

1. `system_profiler` / `sw_vers` / `xcodebuild` audit → rewrite `MACHINE_AUDIT.md` with real values
2. Locate and launch UE 5.8; confirm `UnrealEditor-Cmd` and Python editor scripting work
3. Create `unreal/AokigaharaUE/AokigaharaUE.uproject` with the content namespaces from §5 of the brief
4. **Prove the coordinate transform** with automated control-point tests before anything else
5. Export the `local` grid to 16-bit and import one Landscape; validate against the GLB at ≥ 5 points
6. Ingest the 467,601 placements; validate counts, bounds and class distribution; colour-code by
   class as a debug pass **before** any artistic foliage
7. Only then: one benchmark camera, and make the first 20–30 m genuinely excellent

Do not scale to the whole world until step 7 clears.

---

## 8. What has NOT been done

Everything requiring Unreal. No `.uproject` exists. No landscape, no import scripts have been run,
no renders, no performance numbers. The brief's audit → launch → render → inspect loop has not
started, and no claim in this document rests on it.
