class_name GrassField
extends Node3D
## Dense low-poly grass streamed in cells around the player (MultiMesh per cell, no shadows,
## gentle wind sway). Density follows Settings.grass_density.

const CELL := 14.0
const RADIUS := 52.0
const BASE_PER_CELL := 110

var world: World
var _cells: Dictionary = {}
var _mesh: ArrayMesh
var _flower_mesh: ArrayMesh
var _last_center := Vector2i(999999, 999999)


func setup(w: World) -> void:
	world = w
	_mesh = _make_clump(8, 0.5, Color("3c8424"), Color("94d455"))
	_flower_mesh = _make_flowers()
	Settings.changed.connect(_rebuild_all)


func _process(_delta: float) -> void:
	var cam := get_viewport().get_camera_3d()
	if cam == null or world == null:
		return
	var p := cam.global_position
	var center := Vector2i(int(floor(p.x / CELL)), int(floor(p.z / CELL)))
	if center == _last_center:
		return
	_last_center = center
	var r := int(ceil(RADIUS / CELL))
	var wanted := {}
	for dz in range(-r, r + 1):
		for dx in range(-r, r + 1):
			var key := Vector2i(center.x + dx, center.y + dz)
			var cc := Vector2((key.x + 0.5) * CELL, (key.y + 0.5) * CELL)
			if cc.distance_to(Vector2(p.x, p.z)) > RADIUS + CELL:
				continue
			wanted[key] = true
			if not _cells.has(key):
				_cells[key] = _build_cell(key)
	for key in _cells.keys():
		if not wanted.has(key):
			var n: Node = _cells[key]
			if n:
				n.queue_free()
			_cells.erase(key)


func _rebuild_all() -> void:
	for key in _cells.keys():
		var n: Node = _cells[key]
		if n:
			n.queue_free()
	_cells.clear()
	_last_center = Vector2i(999999, 999999)


func _build_cell(key: Vector2i) -> Node3D:
	var count := int(BASE_PER_CELL * Settings.grass_density)
	if count <= 0:
		return null
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(key)
	var t := world.terrain
	var xfs: Array[Transform3D] = []
	var flowers: Array[Transform3D] = []
	for i in count:
		var x := (key.x + rng.randf()) * CELL
		var z := (key.y + rng.randf()) * CELL
		var s: Color = t.splat_at(x, z)
		if s.r > 0.35 or s.g > 0.4 or s.a > 0.3:
			continue
		var h := t.height_at(x, z)
		if h < 0.7 or t.slope_at(x, z) > 0.45:
			continue
		var sc := rng.randf_range(0.7, 1.35) * (0.8 if s.b > 0.5 else 1.0)
		var b := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(sc, sc * rng.randf_range(0.8, 1.3), sc))
		var xf := Transform3D(b, Vector3(x, h - 0.03, z))
		if rng.randf() < 0.06:
			flowers.append(xf)
		else:
			xfs.append(xf)
	if xfs.is_empty() and flowers.is_empty():
		return null
	var holder := Node3D.new()
	add_child(holder)
	_add_mm(holder, _mesh, xfs)
	_add_mm(holder, _flower_mesh, flowers)
	return holder


func _add_mm(holder: Node3D, mesh: Mesh, xfs: Array[Transform3D]) -> void:
	if xfs.is_empty():
		return
	var mmi := MultiMeshInstance3D.new()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = xfs.size()
	for i in xfs.size():
		mm.set_instance_transform(i, xfs[i])
	mmi.multimesh = mm
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mmi.visibility_range_end = RADIUS + 6.0
	holder.add_child(mmi)


## A clump of tapered blades with vertex colours (dark root → light tip).
func _make_clump(blades: int, height: float, root_col: Color, tip_col: Color) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for b in blades:
		var a := rng.randf() * TAU
		var off := Vector3(cos(a), 0, sin(a)) * rng.randf_range(0.0, 0.18)
		var lean := Vector3(cos(a + 0.6), 0, sin(a + 0.6)) * rng.randf_range(0.05, 0.22)
		var h := height * rng.randf_range(0.7, 1.15)
		var w := rng.randf_range(0.05, 0.08)
		var side := Vector3(-sin(a), 0, cos(a)) * w
		var segs := 3
		var prev_l := off - side
		var prev_r := off + side
		for s in segs:
			var t1 := float(s + 1) / segs
			var center := off + Vector3.UP * h * t1 + lean * t1 * t1
			var wid := 1.0 - t1
			var l := center - side * wid
			var r := center + side * wid
			var c0 := root_col.lerp(tip_col, float(s) / segs)
			var c1 := root_col.lerp(tip_col, t1)
			var n := side.cross(Vector3.UP).normalized()
			for v in [[prev_l, c0], [prev_r, c0], [r, c1], [prev_l, c0], [r, c1], [l, c1]]:
				st.set_color((v[1] as Color).srgb_to_linear())
				st.set_normal((n + Vector3.UP * 1.5).normalized())
				st.add_vertex(v[0])
			prev_l = l
			prev_r = r
	var mesh := st.commit()
	var mat: ShaderMaterial = MaterialLib.get_flat(Color.WHITE, "", "foliage").duplicate()
	mat.set_shader_parameter("use_vertex_color", true)
	mat.set_shader_parameter("wind_strength", 0.09)
	mat.set_shader_parameter("wind_height", 0.6)
	mat.set_shader_parameter("rim_strength", 0.2)
	mat.set_shader_parameter("roughness", 1.0)
	mesh.surface_set_material(0, mat)
	return mesh


func _make_flowers() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var cols := [Color("ff7ad9"), Color("ffd84a"), Color("ffffff"), Color("8fb8ff")]
	for i in 3:
		var a := i * TAU / 3.0
		var base := Vector3(cos(a), 0, sin(a)) * 0.12
		var top := base + Vector3(0, 0.32 + i * 0.05, 0)
		var c: Color = cols[i % cols.size()]
		# stem
		for v in [base + Vector3(-0.01, 0, 0), base + Vector3(0.01, 0, 0), top]:
			st.set_color(Color("3c8424").srgb_to_linear())
			st.set_normal(Vector3.UP)
			st.add_vertex(v)
		# petals: a little star of triangles
		for p in 5:
			var pa := p * TAU / 5.0
			var p1 := top + Vector3(cos(pa), 0.02, sin(pa)) * 0.07
			var p2 := top + Vector3(cos(pa + 0.6), 0.02, sin(pa + 0.6)) * 0.07
			for v2 in [top, p1, p2]:
				st.set_color(c.srgb_to_linear())
				st.set_normal(Vector3.UP)
				st.add_vertex(v2)
	var mesh := st.commit()
	var mat: ShaderMaterial = MaterialLib.get_flat(Color.WHITE, "", "foliage").duplicate()
	mat.set_shader_parameter("use_vertex_color", true)
	mat.set_shader_parameter("wind_strength", 0.06)
	mat.set_shader_parameter("wind_height", 0.4)
	mat.set_shader_parameter("roughness", 1.0)
	mesh.surface_set_material(0, mat)
	return mesh
