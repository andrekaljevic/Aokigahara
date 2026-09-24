extends Node3D
## Aokigahara lighting probe: builds terrain, trees, lighting and environment at runtime from the
## repository's real data, waits for GI to settle, saves a 1280x800 PNG and quits.
## Usage (user args after "--"):  --mode=sdfgi|nosdfgi|canopy|sdfgi_canopy  --frames=N  --tag=name

const REPO := "/home/user/Aokigahara"
const OUT := "/tmp/claude-0/-home-user-Aokigahara/f3a7dee1-ddd5-5966-b7a1-ff45901003d9/scratchpad/proto/godot/out"

var mode := "sdfgi"
var frames_to_wait := 60
var tag := ""
var sun_elev_deg := 24.0
var sun_azim_deg := 240.0     # clockwise from north; 240 = WSW (afternoon)
var cam_yaw_azim_deg := 318.0 # camera looks NW; sun off to the left (side light)
var cam_pitch_deg := 4.0
var sun_energy := 3.2

# terrain grid
var H := PackedFloat32Array()
var W := 0
var HT := 0
var min_x := 0.0
var min_z := 0.0
var dx := 8.0
var dz := 8.0
const Y_OFFSET := 900.0

var env: Environment
var frame := 0
var t_start := 0
var t_ready_done := 0
var frame_times: Array = []
var last_ms := 0
var stats := {}
var cam_pos := Vector3.ZERO
var canopy_items: Array = []   # [x, z, crown_radius] for the sky-visibility bake

func _ready() -> void:
	t_start = Time.get_ticks_msec()
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--mode="): mode = a.substr(7)
		elif a.begins_with("--frames="): frames_to_wait = int(a.substr(9))
		elif a.begins_with("--tag="): tag = a.substr(6)
		elif a.begins_with("--sun_elev="): sun_elev_deg = float(a.substr(11))
		elif a.begins_with("--sun_azim="): sun_azim_deg = float(a.substr(11))
		elif a.begins_with("--cam_azim="): cam_yaw_azim_deg = float(a.substr(11))
		elif a.begins_with("--cam_pitch="): cam_pitch_deg = float(a.substr(12))
		elif a.begins_with("--sun_energy="): sun_energy = float(a.substr(13))
	print("PROBE mode=", mode, " frames=", frames_to_wait)
	print("RENDERER=", RenderingServer.get_current_rendering_method(), " DRIVER=",
		RenderingServer.get_current_rendering_driver_name(), " ADAPTER=", RenderingServer.get_video_adapter_name(),
		" VENDOR=", RenderingServer.get_video_adapter_vendor(), " API=", RenderingServer.get_video_adapter_api_version())
	get_window().size = Vector2i(1280, 800)
	load_terrain()
	cam_pos = choose_camera()
	var ground_mat := build_ground_material()
	build_terrain_mesh(ground_mat)
	var t1 := Time.get_ticks_msec()
	build_forest()
	print("forest built in ", Time.get_ticks_msec() - t1, " ms")
	if mode.contains("canopy"):
		var t2 := Time.get_ticks_msec()
		apply_canopy_sky_visibility(ground_mat)
		print("canopy sky-visibility bake in ", Time.get_ticks_msec() - t2, " ms")
	build_lighting()
	build_camera()
	t_ready_done = Time.get_ticks_msec()
	last_ms = t_ready_done
	print("scene built in ", t_ready_done - t_start, " ms")

# ------------------------------------------------------------------ terrain
func load_terrain() -> void:
	var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(REPO + "/viewer/assets/terrain/local-height.json"))
	W = int(meta["width"]); HT = int(meta["height"])
	min_x = float(meta["minX"]); min_z = float(meta["minZ"])
	dx = float(meta["dx"]); dz = float(meta["dz"])
	H = FileAccess.get_file_as_bytes(REPO + "/viewer/assets/terrain/" + String(meta["file"])).to_float32_array()
	assert(H.size() == W * HT)
	print("terrain ", W, "x", HT, " samples, elevation at origin ", height_at(0, 0) + Y_OFFSET, " m")

func hraw(c: int, r: int) -> float:
	c = clampi(c, 0, W - 1); r = clampi(r, 0, HT - 1)
	return H[r * W + c]

func height_at(x: float, z: float) -> float:
	var fc := (x - min_x) / dx
	var fr := (z - min_z) / dz
	var c := int(floor(fc)); var r := int(floor(fr))
	var tx := fc - c; var tz := fr - r
	var h0 := lerpf(hraw(c, r), hraw(c + 1, r), tx)
	var h1 := lerpf(hraw(c, r + 1), hraw(c + 1, r + 1), tx)
	return lerpf(h0, h1, tz) - Y_OFFSET

func build_terrain_mesh(mat: Material) -> void:
	var verts := PackedVector3Array(); verts.resize(W * HT)
	var norms := PackedVector3Array(); norms.resize(W * HT)
	var uv2 := PackedVector2Array(); uv2.resize(W * HT)
	var span_x := (W - 1) * dx
	var span_z := (HT - 1) * dz
	for r in HT:
		for c in W:
			var i := r * W + c
			verts[i] = Vector3(min_x + c * dx, H[i] - Y_OFFSET, min_z + r * dz)
			var sx := (hraw(c + 1, r) - hraw(c - 1, r)) / (2.0 * dx)
			var sz := (hraw(c, r + 1) - hraw(c, r - 1)) / (2.0 * dz)
			norms[i] = Vector3(-sx, 1.0, -sz).normalized()
			uv2[i] = Vector2(c * dx / span_x, r * dz / span_z)
	var idx := PackedInt32Array(); idx.resize((W - 1) * (HT - 1) * 6)
	var k := 0
	for r in HT - 1:
		for c in W - 1:
			var i00 := r * W + c
			var i10 := i00 + 1
			var i01 := i00 + W
			var i11 := i01 + 1
			# Godot front faces are clockwise; seen from above (+y) with z south these are clockwise.
			idx[k] = i00; idx[k + 1] = i10; idx[k + 2] = i01
			idx[k + 3] = i10; idx[k + 4] = i11; idx[k + 5] = i01
			k += 6
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = norms
	arrays[Mesh.ARRAY_TEX_UV2] = uv2
	arrays[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	am.surface_set_material(0, mat)
	var mi := MeshInstance3D.new()
	mi.name = "Terrain"
	mi.mesh = am
	mi.gi_mode = GeometryInstance3D.GI_MODE_STATIC
	add_child(mi)

func load_tex(path: String, srgb := true) -> ImageTexture:
	var img := Image.load_from_file(path)
	if img == null:
		push_error("could not load " + path)
		return null
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)

func build_ground_material() -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	var base := REPO + "/viewer/assets/materials_v2/"
	m.albedo_texture = load_tex(base + "moss_diff_1k.jpg")
	m.albedo_color = Color(0.85, 0.9, 0.8)
	m.normal_enabled = true
	m.normal_texture = load_tex(base + "moss_nor_gl_1k.jpg", false)
	m.normal_scale = 1.2
	m.roughness_texture = load_tex(base + "moss_rough_1k.jpg", false)
	m.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	m.roughness = 1.0
	m.uv1_triplanar = true
	m.uv1_world_triplanar = true
	m.uv1_triplanar_sharpness = 4.0
	m.uv1_scale = Vector3(0.45, 0.45, 0.45)   # ~2.2 m per tile
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	return m

# ------------------------------------------------------------------ camera placement
var mature: PackedFloat32Array
func choose_camera() -> Vector3:
	mature = FileAccess.get_file_as_bytes(REPO + "/viewer/assets/forest-instances.f32").to_float32_array()
	var best := Vector3.ZERO
	var best_score := -1.0
	var near_pts: Array = []
	for q in range(0, mature.size(), 6):
		if absf(mature[q]) < 40 and absf(mature[q + 2]) < 40:
			near_pts.append(Vector2(mature[q], mature[q + 2]))
	for oz in range(-12, 13, 2):
		for ox in range(-12, 13, 2):
			var nearest := 1e9
			for p in near_pts:
				nearest = minf(nearest, (p - Vector2(ox, oz)).length())
			var score := minf(nearest, 4.0) - 0.05 * sqrt(ox * ox + oz * oz)
			if score > best_score:
				best_score = score; best = Vector3(ox, 0, oz)
	best.y = height_at(best.x, best.z) + 1.7
	print("camera at ", best, " (nearest-trunk score ", best_score, ")")
	return best

# ------------------------------------------------------------------ forest
func hash01(i: int, j: int, s: int) -> float:
	var h := (i * 374761393 + j * 668265263 + s * 2147483647) & 0x7fffffff
	h = ((h ^ (h >> 13)) * 1274126177) & 0x7fffffff
	h = h ^ (h >> 16)
	return float(h & 0xffffff) / float(0xffffff)

func find_meshes(root: Node, out: Dictionary) -> void:
	if root is MeshInstance3D:
		out[String(root.name)] = root.mesh
	elif root is ImporterMeshInstance3D:
		out[String(root.name)] = root.mesh.get_mesh()
	for ch in root.get_children():
		find_meshes(ch, out)

func build_forest() -> void:
	var t0 := Time.get_ticks_msec()
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_file(REPO + "/viewer/assets/tree-library-v2.glb", state)
	if err != OK:
		push_error("GLTF load failed: " + str(err)); return
	var scene := doc.generate_scene(state)
	var meshes := {}
	find_meshes(scene, meshes)
	print("GLB loaded in ", Time.get_ticks_msec() - t0, " ms; meshes: ", meshes.keys().size())
	# foliage: add back-light transmission so needles glow when the sun is behind them
	for mname in meshes.keys():
		var mesh: Mesh = meshes[mname]
		for s in mesh.get_surface_count():
			var mat := mesh.surface_get_material(s) as StandardMaterial3D
			if mat and mat.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR:
				mat.backlight_enabled = true
				mat.backlight = Color(0.32, 0.38, 0.12)
				mat.alpha_antialiasing_mode = BaseMaterial3D.ALPHA_ANTIALIASING_OFF
	scene.queue_free()

	var groups := {}   # mesh name -> Array[Transform3D]
	var n_mature := 0
	var R_HIGH := 32.0
	var R_LOW := 220.0
	var R_FAR := 480.0
	var tall := ["tsuga_a", "tsuga_b", "tsuga_c", "hinoki_a", "hinoki_b", "hinoki_c"]
	for q in range(0, mature.size(), 6):
		var x := mature[q]; var y := mature[q + 1]; var z := mature[q + 2]
		var d := Vector2(x - cam_pos.x, z - cam_pos.z).length()
		if d > R_FAR: continue
		var s := mature[q + 3]; var yaw := mature[q + 4]; var cls := int(mature[q + 5])
		var ii := int(round(x * 10)); var jj := int(round(z * 10))
		var r := hash01(ii, jj, 5)
		var v: String
		if hash01(ii, jj, 6) < 0.05: v = "snag_a" if r < 0.5 else "snag_b"
		elif cls >= 2: v = tall[3 + int(r * 3) % 3] if r < 0.6 else tall[int(r * 7) % 3]
		else: v = tall[int(r * 6) % 6]
		s *= 0.85 + 0.35 * hash01(ii, jj, 7)
		var lod := "_high" if d < R_HIGH else ("_low" if d < R_LOW else "_far")
		if v.begins_with("snag") and lod == "_far": continue
		if v.begins_with("snag") and lod == "_low": lod = "_low"
		add_inst(groups, v + lod, x, y - 0.15, z, s, yaw)
		if not v.begins_with("snag"): canopy_items.append(Vector3(x, z, 4.6 * s))
		n_mature += 1
	# sub-canopy stems (procedural densification, as the three.js viewer does): 6 m jittered grid
	var n_sub := 0
	var cs := 5.0
	var R_SUB := 160.0
	var c0 := int(ceil(R_SUB / cs))
	var ci := int(floor(cam_pos.x / cs)); var cj := int(floor(cam_pos.z / cs))
	for j in range(cj - c0, cj + c0 + 1):
		for i in range(ci - c0, ci + c0 + 1):
			var tx := i * cs + (hash01(i, j, 21) - 0.5) * 5.0
			var tz := j * cs + (hash01(i, j, 22) - 0.5) * 5.0
			var d := Vector2(tx - cam_pos.x, tz - cam_pos.z).length()
			if d > R_SUB or d < 3.0: continue
			if hash01(i, j, 23) > 0.6: continue
			var s := 0.5 + 0.4 * hash01(i, j, 24)
			var v: String = tall[int(hash01(i, j, 25) * 6) % 6]
			var lod := "_high" if d < 22.0 else "_low"
			add_inst(groups, v + lod, tx, height_at(tx, tz) - 0.1, tz, s, hash01(i, j, 26) * TAU)
			canopy_items.append(Vector3(tx, tz, 4.6 * s))
			n_sub += 1
	# saplings and lava blocks near the camera
	var n_small := 0
	cs = 3.2
	var R_SM := 55.0
	c0 = int(ceil(R_SM / cs))
	ci = int(floor(cam_pos.x / cs)); cj = int(floor(cam_pos.z / cs))
	var saps := ["sap_tsuga", "sap_hinoki", "sap_small", "sap_small"]
	var rocks := ["rock_a", "rock_b", "rock_c", "rock_d"]
	for j in range(cj - c0, cj + c0 + 1):
		for i in range(ci - c0, ci + c0 + 1):
			var tx := i * cs + (hash01(i, j, 31) - 0.5) * 3.0
			var tz := j * cs + (hash01(i, j, 32) - 0.5) * 3.0
			var d := Vector2(tx - cam_pos.x, tz - cam_pos.z).length()
			if d > R_SM or d < 1.5: continue
			var p := hash01(i, j, 33)
			if p < 0.30:
				var v: String = saps[int(hash01(i, j, 34) * 4) % 4]
				add_inst(groups, v + ("_high" if d < 30 else "_low"), tx, height_at(tx, tz) - 0.05, tz, 0.7 + 0.6 * hash01(i, j, 35), hash01(i, j, 36) * TAU)
				n_small += 1
			elif p < 0.62:
				var v: String = rocks[int(hash01(i, j, 37) * 4) % 4]
				var sc := 0.6 + 1.0 * hash01(i, j, 38)
				add_inst(groups, v + "_high", tx, height_at(tx, tz) - 0.25 * sc, tz, sc, hash01(i, j, 39) * TAU)
				n_small += 1
			elif p < 0.66:
				var v: String = "log_a" if hash01(i, j, 40) < 0.5 else "log_b"
				add_inst(groups, v + "_high", tx, height_at(tx, tz) - 0.1, tz, 0.9, hash01(i, j, 41) * TAU)
				n_small += 1
	var total_tris := 0
	for key in groups.keys():
		if not meshes.has(key):
			push_warning("missing mesh " + key); continue
		var arr: Array = groups[key]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = meshes[key]
		mm.instance_count = arr.size()
		for k in arr.size():
			mm.set_instance_transform(k, arr[k])
		var mmi := MultiMeshInstance3D.new()
		mmi.name = "MM_" + key
		mmi.multimesh = mm
		mmi.gi_mode = GeometryInstance3D.GI_MODE_STATIC
		add_child(mmi)
		var tris := 0
		var mesh: Mesh = meshes[key]
		for s in mesh.get_surface_count():
			var a := mesh.surface_get_arrays(s)
			var ind = a[Mesh.ARRAY_INDEX]
			tris += (ind.size() if ind != null else a[Mesh.ARRAY_VERTEX].size()) / 3
		total_tris += tris * arr.size()
	stats["mature_trees"] = n_mature
	stats["subcanopy_stems"] = n_sub
	stats["small_props"] = n_small
	stats["multimesh_count"] = groups.size()
	stats["instance_triangles"] = total_tris
	print("forest: mature ", n_mature, ", sub-canopy ", n_sub, ", saplings/rocks/logs ", n_small,
		", multimeshes ", groups.size(), ", instance triangles ", total_tris)

func add_inst(groups: Dictionary, key: String, x: float, y: float, z: float, s: float, yaw: float) -> void:
	var b := Basis(Vector3.UP, yaw).scaled(Vector3(s, s, s))
	if not groups.has(key): groups[key] = []
	groups[key].append(Transform3D(b, Vector3(x, y, z)))

# ------------------------------------------------------------------ canopy sky-visibility (engine-agnostic trick)
## Splat every crown into a top-down cover map over the terrain extent (2 m/px), blur to ~8 m
## (roughly the hemisphere footprint of a 20 m canopy), convert to sky visibility exp(-k*cover)
## and feed it to the ground material as an ambient-only occlusion map on UV2.
func apply_canopy_sky_visibility(mat: StandardMaterial3D) -> void:
	var span := (W - 1) * dx
	var N := 1024
	var px := span / N
	var cover := PackedFloat32Array(); cover.resize(N * N)
	for it in canopy_items:
		var cx: float = (it.x - min_x) / px
		var cz: float = (it.y - min_z) / px
		var rr: float = it.z / px
		var r0 := int(floor(cz - rr)); var r1 := int(ceil(cz + rr))
		var c0 := int(floor(cx - rr)); var c1 := int(ceil(cx + rr))
		for r in range(maxi(r0, 0), mini(r1, N - 1) + 1):
			for c in range(maxi(c0, 0), mini(c1, N - 1) + 1):
				var dd := Vector2(c - cx, r - cz).length() / rr
				if dd < 1.0:
					cover[r * N + c] += 0.85 * (1.0 - dd * dd * 0.5)
	# far field (beyond the instanced radius) treated as closed canopy of average density
	var img := Image.create_from_data(N, N, false, Image.FORMAT_RF, cover.to_byte_array())
	img.convert(Image.FORMAT_RGBAF)
	img.shrink_x2(); img.shrink_x2()   # 1024 -> 256, 8 m box average
	var M := img.get_width()
	var out := Image.create(M, M, false, Image.FORMAT_RGB8)
	var k := 1.6
	var vmin := 1.0; var vmax := 0.0; var vsum := 0.0
	for r in M:
		for c in M:
			var cv := img.get_pixel(c, r).r
			var wx := min_x + (c + 0.5) * span / M
			var wz := min_z + (r + 0.5) * span / M
			if Vector2(wx - cam_pos.x, wz - cam_pos.z).length() > 640.0: cv = 1.2
			var vis := clampf(exp(-k * cv), 0.04, 1.0)
			vmin = minf(vmin, vis); vmax = maxf(vmax, vis); vsum += vis
			out.set_pixel(c, r, Color(vis, vis, vis))
	out.save_png(OUT + "/canopy_sky_visibility.png")
	var t := ImageTexture.create_from_image(out)
	mat.ao_enabled = true
	mat.ao_texture = t
	mat.ao_on_uv2 = true
	mat.ao_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	mat.ao_light_affect = 0.0   # ambient / sky / GI only; direct sun untouched
	var camvis := out.get_pixel(int((cam_pos.x - min_x) / span * M), int((cam_pos.z - min_z) / span * M)).r
	stats["sky_vis_at_camera"] = camvis
	print("sky visibility: min ", vmin, " max ", vmax, " mean ", vsum / (M * M), " at camera ", camvis)

# ------------------------------------------------------------------ lighting + environment
func dir_from_azel(az_deg: float, el_deg: float) -> Vector3:
	var a := deg_to_rad(az_deg); var e := deg_to_rad(el_deg)
	return Vector3(sin(a) * cos(e), sin(e), -cos(a) * cos(e))   # x east, z south, azimuth clockwise from north

func build_lighting() -> void:
	var to_sun := dir_from_azel(sun_azim_deg, sun_elev_deg)
	var sun := DirectionalLight3D.new()
	sun.name = "Sun"
	sun.transform.basis = Basis.looking_at(-to_sun, Vector3.UP)
	sun.light_color = Color(1.0, 0.9, 0.76)
	sun.light_energy = sun_energy
	stats["sun_energy"] = sun_energy
	sun.light_angular_distance = 0.6        # soft (PCSS) penumbrae widening with blocker distance
	sun.shadow_enabled = true
	sun.shadow_bias = 0.03
	sun.shadow_normal_bias = 1.2
	sun.shadow_blur = 1.0
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 150.0
	sun.directional_shadow_split_1 = 0.06
	sun.directional_shadow_split_2 = 0.18
	sun.directional_shadow_split_3 = 0.45
	sun.directional_shadow_blend_splits = true
	sun.directional_shadow_fade_start = 0.85
	sun.light_volumetric_fog_energy = 1.6
	sun.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_AND_SKY
	add_child(sun)

	env = Environment.new()
	var sky := Sky.new()
	var psky := PhysicalSkyMaterial.new()
	psky.rayleigh_coefficient = 2.2
	psky.mie_coefficient = 0.008
	psky.turbidity = 8.0
	psky.ground_color = Color(0.12, 0.13, 0.1)
	psky.energy_multiplier = 1.0
	sky.sky_material = psky
	sky.radiance_size = Sky.RADIANCE_SIZE_256
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_sky_contribution = 1.0
	env.ambient_light_energy = 1.0
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = 1.0
	env.tonemap_white = 12.0
	# screen-space AO + indirect light
	env.ssao_enabled = true
	env.ssao_radius = 1.6
	env.ssao_intensity = 2.5
	env.ssao_power = 1.6
	env.ssao_detail = 0.6
	env.ssao_light_affect = 0.15
	env.ssil_enabled = true
	env.ssil_radius = 6.0
	env.ssil_intensity = 1.2
	env.ssil_sharpness = 0.9
	# SDFGI
	var use_sdfgi := mode.begins_with("sdfgi")
	env.sdfgi_enabled = use_sdfgi
	env.sdfgi_use_occlusion = true
	env.sdfgi_read_sky_light = true
	env.sdfgi_bounce_feedback = 0.5
	env.sdfgi_cascades = 4
	env.sdfgi_min_cell_size = 0.25
	env.sdfgi_energy = 1.0
	env.sdfgi_normal_bias = 1.1
	env.sdfgi_probe_bias = 1.1
	env.sdfgi_y_scale = Environment.SDFGI_Y_SCALE_75_PERCENT
	# volumetric fog: aerial haze and light shafts through canopy gaps
	env.volumetric_fog_enabled = true
	env.volumetric_fog_density = 0.0045
	env.volumetric_fog_albedo = Color(0.82, 0.88, 0.95)
	env.volumetric_fog_anisotropy = 0.55
	env.volumetric_fog_length = 120.0
	env.volumetric_fog_detail_spread = 1.6
	env.volumetric_fog_gi_inject = 0.6
	env.volumetric_fog_ambient_inject = 0.25
	env.volumetric_fog_sky_affect = 0.15
	env.volumetric_fog_temporal_reprojection_enabled = true
	env.volumetric_fog_temporal_reprojection_amount = 0.9
	# distance haze beyond the froxel range
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.fog_light_color = Color(0.55, 0.65, 0.8)
	env.fog_light_energy = 0.6
	env.fog_density = 0.0012
	env.fog_aerial_perspective = 0.6
	env.fog_sky_affect = 0.0
	env.glow_enabled = true
	env.glow_intensity = 0.4
	env.glow_bloom = 0.03
	env.glow_hdr_threshold = 1.2
	var we := WorldEnvironment.new()
	we.environment = env
	var cam_attr := CameraAttributesPractical.new()
	cam_attr.auto_exposure_enabled = true
	cam_attr.auto_exposure_scale = 0.5
	cam_attr.auto_exposure_speed = 4.0
	cam_attr.auto_exposure_min_sensitivity = 10.0
	cam_attr.auto_exposure_max_sensitivity = 1600.0
	we.camera_attributes = cam_attr
	add_child(we)
	stats["sdfgi"] = use_sdfgi

func build_camera() -> void:
	var cam := Camera3D.new()
	cam.name = "Camera"
	cam.fov = 70.0
	cam.near = 0.1
	cam.far = 2500.0
	add_child(cam)
	cam.global_position = cam_pos
	var f := dir_from_azel(cam_yaw_azim_deg, cam_pitch_deg)
	cam.look_at(cam_pos + f, Vector3.UP)
	cam.make_current()

# ------------------------------------------------------------------ frame loop + capture
func _process(_delta: float) -> void:
	frame += 1
	var now := Time.get_ticks_msec()
	frame_times.append(now - last_ms)
	last_ms = now
	if frame % 10 == 0 or frame <= 8:
		print("frame ", frame, " t=", (now - t_start) / 1000.0, " s, last frame ", frame_times[-1], " ms")
	if frame == frames_to_wait:
		set_process(false)
		await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		var fname := "godot_" + (tag if tag != "" else mode) + ".png"
		img.save_png(OUT + "/" + fname)
		var tail: Array = frame_times.slice(maxi(0, frame_times.size() - 20))
		var s := 0.0
		for v in tail: s += v
		stats["mode"] = mode
		stats["file"] = fname
		stats["image_size"] = [img.get_width(), img.get_height()]
		stats["frames"] = frame
		stats["scene_build_s"] = (t_ready_done - t_start) / 1000.0
		stats["first_frame_s"] = frame_times[0] / 1000.0
		stats["steady_s_per_frame"] = s / tail.size() / 1000.0
		stats["total_s"] = (Time.get_ticks_msec() - t_start) / 1000.0
		stats["renderer"] = RenderingServer.get_current_rendering_method()
		stats["driver"] = RenderingServer.get_current_rendering_driver_name()
		stats["adapter"] = RenderingServer.get_video_adapter_name()
		print("STATS ", JSON.stringify(stats))
		var f := FileAccess.open(OUT + "/" + fname.get_basename() + ".json", FileAccess.WRITE)
		f.store_string(JSON.stringify(stats, "  "))
		f.close()
		get_tree().quit()
