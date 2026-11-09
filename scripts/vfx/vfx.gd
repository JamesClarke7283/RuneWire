class_name VFX
## Cartoon effects built from GPU particles and short tweens: sparks, magic sparkles, toon smoke
## puffs, explosions, beams, lightning, rings, muzzle flashes and floating damage numbers.

const FX_TEX := "res://assets/textures/fx/%s.png"

static var _mat_cache: Dictionary = {}
static var _tex_cache: Dictionary = {}
static var _puff_mesh: SphereMesh = null
static var _quad: QuadMesh = null
static var _scale_curve: CurveTexture = null
static var _grow_curve: CurveTexture = null


static func root(ctx: Node) -> Node:
	var r := ctx.get_tree().get_first_node_in_group("vfx_root")
	return r if r else ctx.get_tree().current_scene


static func fx_texture(tex_name: String) -> Texture2D:
	if _tex_cache.has(tex_name):
		return _tex_cache[tex_name]
	var t: Texture2D = null
	var path := FX_TEX % tex_name
	if ResourceLoader.exists(path):
		t = load(path)
	if t == null:
		var g := GradientTexture2D.new()
		g.fill = GradientTexture2D.FILL_RADIAL
		g.fill_from = Vector2(0.5, 0.5)
		g.fill_to = Vector2(1.0, 0.5)
		var gr := Gradient.new()
		gr.set_color(0, Color(1, 1, 1, 1))
		gr.set_color(1, Color(1, 1, 1, 0))
		gr.add_point(0.35, Color(1, 1, 1, 0.8))
		g.gradient = gr
		g.width = 64
		g.height = 64
		t = g
	_tex_cache[tex_name] = t
	return t


static func additive_mat(tex_name: String = "vfx_glow", billboard: bool = true) -> StandardMaterial3D:
	var key := "add_%s_%s" % [tex_name, billboard]
	if _mat_cache.has(key):
		return _mat_cache[key]
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = fx_texture(tex_name)
	m.no_depth_test = false
	m.disable_receive_shadows = true
	if billboard:
		m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	_mat_cache[key] = m
	return m


static func glow_mat(color: Color, energy: float = 3.0) -> StandardMaterial3D:
	var key := "glow_%s_%.1f" % [color.to_html(), energy]
	if _mat_cache.has(key):
		return _mat_cache[key]
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = color
	m.emission_enabled = true
	m.emission = color
	m.emission_energy_multiplier = energy
	m.disable_receive_shadows = true
	_mat_cache[key] = m
	return m


static func glow_alpha_mat(color: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.albedo_color = color
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.disable_receive_shadows = true
	return m


static func puff_mat() -> Material:
	if _mat_cache.has("puff"):
		return _mat_cache["puff"]
	var m: ShaderMaterial = MaterialLib.get_flat(Color.WHITE).duplicate()
	m.set_shader_parameter("use_vertex_color", true)
	m.set_shader_parameter("rim_strength", 0.45)
	m.set_shader_parameter("shadow_light", 0.55)
	_mat_cache["puff"] = m
	return m


static func _curves() -> void:
	if _scale_curve:
		return
	var c := Curve.new()
	c.add_point(Vector2(0, 0.6))
	c.add_point(Vector2(0.15, 1.0))
	c.add_point(Vector2(1, 0.0))
	_scale_curve = CurveTexture.new()
	_scale_curve.curve = c
	var g := Curve.new()
	g.add_point(Vector2(0, 0.3))
	g.add_point(Vector2(0.3, 1.0))
	g.add_point(Vector2(0.7, 0.85))
	g.add_point(Vector2(1, 0.0))
	_grow_curve = CurveTexture.new()
	_grow_curve.curve = g
	_puff_mesh = SphereMesh.new()
	_puff_mesh.radius = 0.5
	_puff_mesh.height = 1.0
	_puff_mesh.radial_segments = 10
	_puff_mesh.rings = 6
	_quad = QuadMesh.new()
	_quad.size = Vector2(1, 1)


static func _free_later(n: Node, t: float) -> void:
	var timer := n.get_tree().create_timer(t, false)
	timer.timeout.connect(func():
		if is_instance_valid(n):
			n.queue_free())


## Generic one-shot particle burst. kind: "spark" (additive glow quads), "star", "puff" (toon smoke balls).
static func burst(ctx: Node, pos: Vector3, color: Color, amount: int = 16, speed: float = 6.0, size: float = 0.15,
		lifetime: float = 0.6, gravity: float = -9.0, kind: String = "spark", spread: float = 180.0, dir: Vector3 = Vector3.UP) -> GPUParticles3D:
	if ctx == null or not ctx.is_inside_tree():
		return null
	_curves()
	var p := GPUParticles3D.new()
	p.one_shot = true
	p.explosiveness = 0.92
	p.amount = maxi(1, amount)
	p.lifetime = lifetime
	p.local_coords = false
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if kind != "puff" else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	var pm := ParticleProcessMaterial.new()
	pm.direction = dir
	pm.spread = spread
	pm.initial_velocity_min = speed * 0.35
	pm.initial_velocity_max = speed
	pm.gravity = Vector3(0, gravity, 0)
	pm.damping_min = 1.0
	pm.damping_max = 3.0 if kind == "puff" else 1.5
	pm.scale_min = size * 0.6
	pm.scale_max = size * 1.2
	pm.scale_curve = _grow_curve if kind == "puff" else _scale_curve
	pm.color = color
	pm.angle_min = -180.0
	pm.angle_max = 180.0
	if kind == "puff":
		pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
		pm.emission_sphere_radius = size * 0.5
	p.process_material = pm
	if kind == "puff":
		p.draw_pass_1 = _puff_mesh
		p.material_override = puff_mat()
	else:
		p.draw_pass_1 = _quad
		p.material_override = additive_mat("vfx_star" if kind == "star" else "vfx_spark")
		if kind == "spark":
			pm.particle_flag_align_y = false
	var r := root(ctx)
	r.add_child(p)
	p.global_position = pos
	p.emitting = true
	_free_later(p, lifetime + 0.5)
	return p


static func sparkle(ctx: Node, pos: Vector3, color: Color, amount: int = 14, size: float = 0.35) -> void:
	burst(ctx, pos, color, amount, 3.0, size, 0.8, 1.5, "star")


static func puffs(ctx: Node, pos: Vector3, color: Color, amount: int = 8, size: float = 0.8, lifetime: float = 1.2, rise: float = 2.5) -> void:
	burst(ctx, pos, color, amount, 2.5, size, lifetime, rise, "puff", 70.0)


static func flash_light(ctx: Node, pos: Vector3, color: Color, energy: float = 4.0, light_range: float = 8.0, duration: float = 0.3) -> void:
	var l := OmniLight3D.new()
	l.light_color = color
	l.light_energy = energy
	l.omni_range = light_range
	l.shadow_enabled = false
	root(ctx).add_child(l)
	l.global_position = pos
	var tw := l.create_tween()
	tw.tween_property(l, "light_energy", 0.0, duration)
	tw.tween_callback(l.queue_free)


static func sphere_pop(ctx: Node, pos: Vector3, color: Color, radius: float, duration: float = 0.35) -> void:
	_curves()
	var mi := MeshInstance3D.new()
	mi.mesh = _puff_mesh
	mi.material_override = glow_mat(color, 2.5)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root(ctx).add_child(mi)
	mi.global_position = pos
	mi.scale = Vector3.ONE * radius * 0.3
	var tw := mi.create_tween()
	tw.tween_property(mi, "scale", Vector3.ONE * radius * 2.0, duration * 0.4).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	tw.tween_property(mi, "scale", Vector3.ZERO, duration * 0.6).set_ease(Tween.EASE_IN)
	tw.tween_callback(mi.queue_free)


static func ring(ctx: Node, pos: Vector3, color: Color, radius: float, duration: float = 0.45, normal: Vector3 = Vector3.UP) -> void:
	var mi := MeshInstance3D.new()
	var tm := TorusMesh.new()
	tm.inner_radius = 0.86
	tm.outer_radius = 1.0
	tm.rings = 32
	tm.ring_segments = 6
	mi.mesh = tm
	mi.material_override = glow_mat(color, 3.0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root(ctx).add_child(mi)
	mi.global_position = pos
	if not normal.is_equal_approx(Vector3.UP):
		mi.look_at(pos + normal, Vector3.RIGHT if absf(normal.dot(Vector3.UP)) > 0.9 else Vector3.UP)
		mi.rotate_object_local(Vector3.RIGHT, PI / 2)
	mi.scale = Vector3.ONE * 0.2
	var tw := mi.create_tween()
	tw.tween_property(mi, "scale", Vector3(radius, radius * 0.5, radius), duration).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.parallel().tween_property(mi, "transparency", 1.0, duration)
	tw.tween_callback(mi.queue_free)


static func explosion(ctx: Node, pos: Vector3, radius: float, color: Color) -> void:
	flash_light(ctx, pos + Vector3.UP * 0.5, color, 6.0, radius * 3.0, 0.4)
	sphere_pop(ctx, pos, color.lerp(Color(1, 0.95, 0.7), 0.4), radius * 0.55, 0.42)
	burst(ctx, pos, color.lerp(Color.WHITE, 0.3), int(18 + radius * 4), radius * 4.0, 0.22, 0.7, -12.0, "spark")
	puffs(ctx, pos + Vector3.UP * 0.3, Color(0.42, 0.4, 0.45), int(6 + radius * 2), radius * 0.5, 1.4, 3.0)
	puffs(ctx, pos, color.lerp(Color(1, 0.8, 0.5), 0.5), 6, radius * 0.4, 0.5, 1.0)
	ring(ctx, pos + Vector3.UP * 0.2, color.lerp(Color.WHITE, 0.5), radius * 1.2, 0.4)
	scorch(ctx, pos, radius * 0.8)


static func scorch(ctx: Node, pos: Vector3, size: float) -> void:
	var d := Decal.new()
	d.texture_albedo = fx_texture("vfx_scorch")
	d.size = Vector3(size * 2.0, 2.0, size * 2.0)
	d.modulate = Color(0.1, 0.08, 0.1, 0.75)
	d.cull_mask = 1
	d.upper_fade = 0.3
	d.lower_fade = 0.3
	root(ctx).add_child(d)
	d.global_position = pos
	d.rotation.y = randf() * TAU
	var tw := d.create_tween()
	tw.tween_interval(10.0)
	tw.tween_property(d, "modulate:a", 0.0, 3.0)
	tw.tween_callback(d.queue_free)


## A glowing straight beam between two points that fades out.
static func beam(ctx: Node, from: Vector3, to: Vector3, color: Color, width: float = 0.06, duration: float = 0.12) -> void:
	var len := from.distance_to(to)
	if len < 0.01:
		return
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = width
	cm.bottom_radius = width
	cm.height = len
	cm.radial_segments = 6
	cm.rings = 1
	mi.mesh = cm
	mi.material_override = glow_mat(color, 4.0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root(ctx).add_child(mi)
	_orient_between(mi, from, to)
	var tw := mi.create_tween()
	tw.tween_property(mi, "scale", Vector3(0.05, 1.0, 0.05), duration).set_ease(Tween.EASE_IN)
	tw.tween_callback(mi.queue_free)


static func _orient_between(n: Node3D, from: Vector3, to: Vector3) -> void:
	var mid := (from + to) * 0.5
	var dir := (to - from).normalized()
	var up := Vector3.UP if absf(dir.dot(Vector3.UP)) < 0.95 else Vector3.RIGHT
	var b := Basis.looking_at(dir, up)
	b = b * Basis(Vector3.RIGHT, PI / 2)
	n.global_transform = Transform3D(b, mid)


## Jagged lightning bolt made of short glowing segments.
static func lightning(ctx: Node, from: Vector3, to: Vector3, color: Color, segments: int = 9, jitter: float = 0.7, duration: float = 0.2) -> void:
	var pts: Array[Vector3] = [from]
	var dir := to - from
	var side := dir.cross(Vector3.UP).normalized()
	if side.length_squared() < 0.01:
		side = Vector3.RIGHT
	var up2 := dir.cross(side).normalized()
	for i in range(1, segments):
		var t := float(i) / segments
		var p := from + dir * t
		var amp := jitter * sin(t * PI)
		p += side * randf_range(-amp, amp) + up2 * randf_range(-amp, amp)
		pts.append(p)
	pts.append(to)
	for i in pts.size() - 1:
		beam(ctx, pts[i], pts[i + 1], color, 0.055, duration)
		if i % 3 == 1:
			beam(ctx, pts[i], pts[i] + (side * randf_range(-1, 1) + up2 * randf_range(-1, 1)) * 0.8, color, 0.03, duration * 0.8)
	flash_light(ctx, to, color, 3.0, 6.0, duration + 0.1)


static func muzzle(ctx: Node, pos: Vector3, color: Color, size: float = 0.25) -> void:
	sphere_pop(ctx, pos, color, size, 0.12)
	burst(ctx, pos, color, 5, 3.0, 0.08, 0.2, 0.0, "spark", 25.0)


static func damage_number(ctx: Node, pos: Vector3, amount: float, color: Color, crit: bool = false) -> void:
	var l := Label3D.new()
	l.text = str(int(round(amount))) + ("!" if crit else "")
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.fixed_size = true
	l.pixel_size = 0.0011 if not crit else 0.0015
	l.font_size = 48
	l.outline_size = 14
	l.modulate = color
	l.outline_modulate = Color(0.08, 0.05, 0.1)
	var f := UIStyle.display_font()
	if f:
		l.font = f
	root(ctx).add_child(l)
	l.global_position = pos + Vector3(randf_range(-0.3, 0.3), 0.3, randf_range(-0.3, 0.3))
	var tw := l.create_tween()
	tw.set_parallel(true)
	tw.tween_property(l, "global_position", l.global_position + Vector3(0, 1.3, 0), 0.8).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(l, "modulate:a", 0.0, 0.35).set_delay(0.5)
	tw.tween_property(l, "outline_modulate:a", 0.0, 0.35).set_delay(0.5)
	tw.chain().tween_callback(l.queue_free)


static func weld_sparks(ctx: Node, pos: Vector3) -> void:
	burst(ctx, pos, Color(1.0, 0.82, 0.4), 22, 5.0, 0.12, 0.5, -14.0, "spark")
	flash_light(ctx, pos, Color(1.0, 0.8, 0.5), 3.0, 4.0, 0.25)
	sparkle(ctx, pos, Color(0.4, 0.95, 0.9), 8, 0.3)
