class_name VoidOrb
extends Node3D
## The Gloom Orb spell: a slow orb of gloom that drifts forward until it meets a foe or a wall, drags
## nearby foes toward itself, grinds those close to it with arcane damage, and implodes after
## `duration` seconds.

var velocity: Vector3 = Vector3.ZERO
var data: Dictionary = {}
var mult: float = 1.0
var source: Node3D = null
var _age: float = 0.0
var _tick: float = 0.0
var _travel: float = 0.0
var _stopped: bool = false
var _core: MeshInstance3D
var _halo: MeshInstance3D
var _light: OmniLight3D
var _swirl: GPUParticles3D


static func spawn(src: Node3D, pos: Vector3, dir: Vector3, d: Dictionary, m: float) -> VoidOrb:
	var o := VoidOrb.new()
	o.source = src
	o.data = d
	o.mult = m
	o.velocity = dir.normalized() * float(d.get("speed", 9.0))
	VFX.root(src).add_child(o)
	o.global_position = pos
	return o


func _ready() -> void:
	var col: Color = data.get("color", Color(0.58, 0.32, 1.0))
	_core = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.38
	sm.height = 0.76
	sm.radial_segments = 16
	sm.rings = 8
	_core.mesh = sm
	_core.material_override = VFX.glow_mat(col.darkened(0.55), 1.6)
	_core.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_core)
	_halo = MeshInstance3D.new()
	var hm := QuadMesh.new()
	hm.size = Vector2.ONE * 2.6
	_halo.mesh = hm
	var hmat := VFX.additive_mat("vfx_glow", false).duplicate() as StandardMaterial3D
	hmat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	hmat.albedo_color = Color(col, 0.9)
	hmat.vertex_color_use_as_albedo = false
	_halo.material_override = hmat
	_halo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_halo)
	_light = OmniLight3D.new()
	_light.light_color = col
	_light.light_energy = 2.2
	_light.omni_range = 7.0
	add_child(_light)
	# motes spiralling inward
	VFX._curves()
	_swirl = GPUParticles3D.new()
	_swirl.amount = 28
	_swirl.lifetime = 0.8
	_swirl.local_coords = true
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = 2.2
	pm.radial_accel_min = -9.0
	pm.radial_accel_max = -6.0
	pm.tangential_accel_min = 4.0
	pm.tangential_accel_max = 7.0
	pm.gravity = Vector3.ZERO
	pm.scale_min = 0.12
	pm.scale_max = 0.24
	pm.scale_curve = VFX._scale_curve
	pm.color = col.lightened(0.3)
	_swirl.process_material = pm
	_swirl.draw_pass_1 = VFX._quad
	_swirl.material_override = VFX.additive_mat("vfx_spark")
	_swirl.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_swirl)


func _physics_process(delta: float) -> void:
	_age += delta
	var dur := float(data.get("duration", 3.0))
	if not _stopped and _foe_near(1.6):
		_stopped = true
	if not _stopped:
		var step := velocity * delta
		var q := PhysicsRayQueryParameters3D.create(global_position, global_position + step * 1.5, 1 | 4)
		var h := get_world_3d().direct_space_state.intersect_ray(q)
		if h:
			global_position = h["position"] - velocity.normalized() * 0.6
			_stopped = true
		else:
			global_position += step
			_travel += step.length()
			if _travel >= float(data.get("range", 40.0)):
				_stopped = true
	_pull(delta)
	_tick -= delta
	if _tick <= 0.0:
		_tick = 0.25
		_grind()
	var pulse := 1.0 + sin(_age * 9.0) * 0.08
	_core.scale = Vector3.ONE * pulse * (1.0 + 0.25 * clampf(_age / dur, 0.0, 1.0))
	_halo.scale = Vector3.ONE * (1.0 + sin(_age * 5.0) * 0.12)
	_light.light_energy = 2.0 + sin(_age * 9.0) * 0.4
	if _age >= dur:
		_implode()


func _foe_near(r: float) -> bool:
	for e in get_tree().get_nodes_in_group("enemies"):
		if not e.get("dead") and (e.aim_point() as Vector3).distance_to(global_position) < r:
			return true
	return false


## Foes inside the pull radius slide toward the orb (bosses barely budge).
func _pull(delta: float) -> void:
	var r := float(data.get("radius", 6.0))
	for e in get_tree().get_nodes_in_group("enemies"):
		if e.get("dead") or e.get("is_static"):
			continue
		var n := e as Node3D
		var to := global_position - n.global_position
		to.y *= 0.3
		var d := to.length()
		if d > r or d < 0.6:
			continue
		var strength := 22.0 * (1.0 - d / r) * (0.15 if e.get("boss") else 1.0)
		e.velocity += to.normalized() * strength * delta


func _grind() -> void:
	var dps := float(data.get("damage", 16.0)) * mult
	for e in get_tree().get_nodes_in_group("enemies"):
		if e.get("dead"):
			continue
		var ap: Vector3 = e.aim_point()
		if ap.distance_to(global_position) > 3.4:
			continue
		var info := DamageInfo.make(dps * 0.25, str(data.get("damage_type", "arcane")), source, ap,
			(global_position - ap).normalized(), 0.0, true)
		info.weapon = data
		info.proc = true
		e.apply_damage(info)


func _implode() -> void:
	set_physics_process(false)
	var col: Color = data.get("color", Color(0.58, 0.32, 1.0))
	Combat.explode(self, global_position, 4.5, float(data.get("splash", 40.0)) * mult, str(data.get("damage_type", "arcane")),
		source, true, false, 0.9, data)
	VFX.sphere_pop(self, global_position, col, 3.0, 0.35)
	VFX.burst(self, global_position, col.lightened(0.3), 24, 8.0, 0.22, 0.6, 0.0, "star")
	AudioManager.play("orb_implode", global_position, 0.0, 1.0, 0.05, 18.0)
	queue_free()
