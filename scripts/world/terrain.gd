class_name Terrain
extends Node3D
## Procedural valley terrain: deterministic height field (cached to user://), chunked mesh with
## the cartoon terrain shader, HeightMapShape3D collision and a splat map for paths, sand,
## forest floor and cobbles.

const RES := 257                    # samples per side
const CELL := WorldLayout.SIZE / float(RES - 1)   # 2.5 m
const CHUNKS := 8
const CACHE_VERSION := 4
const CACHE_PATH := "user://terrain_cache_v%d.bin"

var heights := PackedFloat32Array()
var splat_image: Image
var material: ShaderMaterial
var _noise_hills := FastNoiseLite.new()
var _noise_detail := FastNoiseLite.new()
var _noise_ridge := FastNoiseLite.new()


func _init() -> void:
	_noise_hills.seed = 1337
	_noise_hills.frequency = 1.0 / 170.0
	_noise_hills.fractal_octaves = 4
	_noise_detail.seed = 4242
	_noise_detail.frequency = 1.0 / 38.0
	_noise_detail.fractal_octaves = 2
	_noise_ridge.seed = 777
	_noise_ridge.frequency = 1.0 / 90.0
	_noise_ridge.fractal_type = FastNoiseLite.FRACTAL_RIDGED
	_noise_ridge.fractal_octaves = 4


func build() -> void:
	if not _load_cache():
		_generate_heights()
		_save_cache()
	_build_splat()
	_build_material()
	_build_mesh()
	_build_collision()


# ------------------------------------------------------------------ height function
func _raw_height(x: float, z: float) -> float:
	var p := Vector2(x, z)
	var r := p.length()
	var h := 5.0 + _noise_hills.get_noise_2d(x, z) * 9.0 + _noise_detail.get_noise_2d(x, z) * 1.4
	# mountain rim around the valley (and the square corners)
	var edge := maxf(r, maxf(absf(x), absf(z)) * 1.02)
	var rim := smoothstep(228.0, 300.0, edge)
	h += rim * (42.0 + (_noise_ridge.get_noise_2d(x, z) * 0.5 + 0.5) * 38.0)
	# gentle northern foothills
	h += smoothstep(150.0, 240.0, -z) * 8.0 * (0.5 + 0.5 * _noise_hills.get_noise_2d(x * 1.7, z * 1.7))
	# lake bowl
	var lp: Vector2 = WorldLayout.LAKE["pos"]
	var lr: float = WorldLayout.LAKE["radius"]
	var ld := p.distance_to(lp)
	if ld < lr + 30.0:
		var t := 1.0 - smoothstep(lr * 0.35, lr + 26.0, ld)
		h = lerpf(h, -float(WorldLayout.LAKE["depth"]), t)
	# flatten points of interest
	for k in WorldLayout.POIS:
		var poi: Dictionary = WorldLayout.POIS[k]
		var d := p.distance_to(poi["pos"])
		var rad: float = poi["radius"]
		var bl: float = poi["blend"]
		if d < rad + bl:
			var w := 1.0 - smoothstep(rad, rad + bl, d)
			h = lerpf(h, float(poi["height"]), w)
	# roads: soften towards a smoothed profile
	var road_w := _road_weight(p)
	if road_w > 0.0:
		var smooth_h := 5.0 + _noise_hills.get_noise_2d(x, z) * 6.0
		h = lerpf(h, maxf(smooth_h, h - 1.5), road_w * 0.5)
	# the gorge (cut after flattening so it stays a gorge)
	var ga: Vector2 = WorldLayout.GORGE["a"]
	var gb: Vector2 = WorldLayout.GORGE["b"]
	var gd := _dist_to_segment(p, ga, gb)
	var gw: float = WorldLayout.GORGE["width"]
	if gd < gw + 10.0:
		var t2 := 1.0 - smoothstep(gw * 0.45, gw, gd)
		var floor_h := 6.0 - float(WorldLayout.GORGE["depth"]) + _noise_detail.get_noise_2d(x * 2.0, z * 2.0) * 1.5
		h = lerpf(h, floor_h, t2)
	return h


func _road_weight(p: Vector2) -> float:
	var best := 0.0
	for road in WorldLayout.ROADS:
		var pts: Array = road["pts"]
		var w: float = road["width"]
		for i in pts.size() - 1:
			var d := _dist_to_segment(p, pts[i], pts[i + 1])
			if d < w * 1.6:
				best = maxf(best, 1.0 - smoothstep(w * 0.5, w * 1.6, d))
	return best


static func _dist_to_segment(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var t := clampf((p - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
	return p.distance_to(a + ab * t)


func _generate_heights() -> void:
	heights.resize(RES * RES)
	for zi in RES:
		var z := -WorldLayout.HALF + zi * CELL
		for xi in RES:
			var x := -WorldLayout.HALF + xi * CELL
			heights[zi * RES + xi] = _raw_height(x, z)


func _load_cache() -> bool:
	var path := CACHE_PATH % CACHE_VERSION
	if not FileAccess.file_exists(path):
		return false
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return false
	var data := f.get_buffer(f.get_length())
	f.close()
	var arr := data.to_float32_array()
	if arr.size() != RES * RES:
		return false
	heights = arr
	return true


func _save_cache() -> void:
	var f := FileAccess.open(CACHE_PATH % CACHE_VERSION, FileAccess.WRITE)
	if f:
		f.store_buffer(heights.to_byte_array())
		f.close()


# ------------------------------------------------------------------ queries
func sample(xi: int, zi: int) -> float:
	xi = clampi(xi, 0, RES - 1)
	zi = clampi(zi, 0, RES - 1)
	return heights[zi * RES + xi]


## Interpolated terrain height at world (x, z).
func height_at(x: float, z: float) -> float:
	var fx := (x + WorldLayout.HALF) / CELL
	var fz := (z + WorldLayout.HALF) / CELL
	var x0 := int(floor(fx))
	var z0 := int(floor(fz))
	var tx := fx - x0
	var tz := fz - z0
	var h00 := sample(x0, z0)
	var h10 := sample(x0 + 1, z0)
	var h01 := sample(x0, z0 + 1)
	var h11 := sample(x0 + 1, z0 + 1)
	# match the mesh triangulation (diagonal from (0,0) to (1,1))
	if tx > tz:
		return h00 + (h10 - h00) * tx + (h11 - h10) * tz
	return h00 + (h11 - h01) * tx + (h01 - h00) * tz


func normal_at(x: float, z: float) -> Vector3:
	var e := CELL
	var hl := height_at(x - e, z)
	var hr := height_at(x + e, z)
	var hd := height_at(x, z - e)
	var hu := height_at(x, z + e)
	return Vector3(hl - hr, 2.0 * e, hd - hu).normalized()


func slope_at(x: float, z: float) -> float:
	return 1.0 - normal_at(x, z).y


# ------------------------------------------------------------------ splat map
func _build_splat() -> void:
	var n := RES
	splat_image = Image.create(n, n, false, Image.FORMAT_RGBA8)
	var lake_pos: Vector2 = WorldLayout.LAKE["pos"]
	var woods_pos: Vector2 = WorldLayout.WOODS["pos"]
	var woods_r: float = WorldLayout.WOODS["radius"]
	for zi in n:
		var z := -WorldLayout.HALF + zi * CELL
		for xi in n:
			var x := -WorldLayout.HALF + xi * CELL
			var p := Vector2(x, z)
			var h := heights[zi * RES + xi]
			var dirt := _road_weight(p)
			var sand := 1.0 - smoothstep(0.6, 2.2, h)
			var gd := _dist_to_segment(p, WorldLayout.GORGE["a"], WorldLayout.GORGE["b"])
			sand = maxf(sand, (1.0 - smoothstep(4.0, 9.0, gd)) * 0.8)
			var forest := (1.0 - smoothstep(woods_r * 0.55, woods_r, p.distance_to(woods_pos)))
			forest = maxf(forest, smoothstep(150.0, 200.0, -z) * 0.6 * (1.0 - smoothstep(220.0, 240.0, p.length())))
			var cobble := 0.0
			cobble = maxf(cobble, 1.0 - smoothstep(24.0, 30.0, p.length()))
			var shrine: Vector2 = WorldLayout.POIS["shrine"]["pos"]
			cobble = maxf(cobble, (1.0 - smoothstep(20.0, 30.0, p.distance_to(shrine))) * 0.85)
			var foundry: Vector2 = WorldLayout.POIS["foundry"]["pos"]
			dirt = maxf(dirt, 1.0 - smoothstep(36.0, 52.0, p.distance_to(foundry)))
			var arena: Vector2 = WorldLayout.POIS["arena"]["pos"]
			sand = maxf(sand, 1.0 - smoothstep(26.0, 29.0, p.distance_to(arena)))
			var flats: Vector2 = WorldLayout.POIS["flats"]["pos"]
			dirt = maxf(dirt, (1.0 - smoothstep(40.0, 62.0, p.distance_to(flats))) * 0.55)
			splat_image.set_pixel(xi, zi, Color(clampf(dirt, 0, 1), clampf(sand, 0, 1), clampf(forest, 0, 1), clampf(cobble, 0, 1)))


func splat_at(x: float, z: float) -> Color:
	var xi := clampi(int(round((x + WorldLayout.HALF) / CELL)), 0, RES - 1)
	var zi := clampi(int(round((z + WorldLayout.HALF) / CELL)), 0, RES - 1)
	return splat_image.get_pixel(xi, zi)


func _build_material() -> void:
	material = ShaderMaterial.new()
	material.shader = load("res://shaders/terrain.gdshader")
	material.set_shader_parameter("splat_map", ImageTexture.create_from_image(splat_image))
	material.set_shader_parameter("terrain_origin", Vector2(-WorldLayout.HALF, -WorldLayout.HALF))
	material.set_shader_parameter("terrain_size", Vector2(WorldLayout.SIZE, WorldLayout.SIZE))
	var macro: Texture2D = MaterialLib.texture("res://assets/textures/fx/noise_perlin.png")
	if macro == null:
		var nt := NoiseTexture2D.new()
		nt.seamless = true
		nt.width = 256
		nt.height = 256
		var fn := FastNoiseLite.new()
		fn.frequency = 0.02
		nt.noise = fn
		macro = nt
	material.set_shader_parameter("macro_noise", macro)
	var sets := {"grass_tex": "grass", "dirt_tex": "dirt", "rock_tex": "rock", "sand_tex": "sand",
		"forest_tex": "forest_floor", "cobble_tex": "cobble", "snow_tex": "snow"}
	var all := true
	for param in sets:
		var t: Texture2D = MaterialLib.texture("res://assets/textures/%s/%s_albedo.png" % [sets[param], sets[param]])
		if t == null:
			all = false
			break
		material.set_shader_parameter(param, t)
	material.set_shader_parameter("has_textures", all)


# ------------------------------------------------------------------ mesh
func _build_mesh() -> void:
	var per := (RES - 1) / CHUNKS
	for cz in CHUNKS:
		for cx in CHUNKS:
			var mi := MeshInstance3D.new()
			mi.name = "Chunk_%d_%d" % [cx, cz]
			mi.mesh = _chunk_mesh(cx * per, cz * per, per)
			mi.material_override = material
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
			add_child(mi)


func _chunk_mesh(x0: int, z0: int, per: int) -> ArrayMesh:
	var n := per + 1
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var idx := PackedInt32Array()
	verts.resize(n * n)
	norms.resize(n * n)
	for j in n:
		for i in n:
			var xi := x0 + i
			var zi := z0 + j
			var x := -WorldLayout.HALF + xi * CELL
			var z := -WorldLayout.HALF + zi * CELL
			verts[j * n + i] = Vector3(x, sample(xi, zi), z)
			var hl := sample(xi - 1, zi)
			var hr := sample(xi + 1, zi)
			var hd := sample(xi, zi - 1)
			var hu := sample(xi, zi + 1)
			norms[j * n + i] = Vector3(hl - hr, 2.0 * CELL, hd - hu).normalized()
	idx.resize(per * per * 6)
	var k := 0
	for j in per:
		for i in per:
			var a := j * n + i
			var b := a + 1
			var c := a + n
			var d := c + 1
			# diagonal a-d (matches height_at)
			idx[k] = a
			idx[k + 1] = b
			idx[k + 2] = d
			idx[k + 3] = a
			idx[k + 4] = d
			idx[k + 5] = c
			k += 6
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = norms
	arrays[Mesh.ARRAY_INDEX] = idx
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return m


func _build_collision() -> void:
	var body := StaticBody3D.new()
	body.name = "TerrainBody"
	body.collision_layer = 1
	body.collision_mask = 0
	var shape := HeightMapShape3D.new()
	shape.map_width = RES
	shape.map_depth = RES
	var scaled := PackedFloat32Array()
	scaled.resize(heights.size())
	for i in heights.size():
		scaled[i] = heights[i] / CELL
	shape.map_data = scaled
	var cs := CollisionShape3D.new()
	cs.shape = shape
	cs.scale = Vector3(CELL, CELL, CELL)
	body.add_child(cs)
	body.set_meta("surface", "terrain")
	add_child(body)
