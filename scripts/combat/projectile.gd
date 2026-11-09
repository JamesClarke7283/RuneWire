class_name Projectile
extends Node3D
## Swept-raycast projectile: bolts, fireballs, rivets, bombs, rockets and enemy shots.
## Explodes on impact when `splash_radius` > 0, can bounce, home in, and is blocked by Ward domes.

var velocity: Vector3 = Vector3.ZERO
var gravity: float = 0.0
var damage: float = 10.0
var damage_type: String = "arcane"
var splash_damage: float = 0.0
var splash_radius: float = 0.0
var from_player: bool = true
var source: Node = null
var lifetime: float = 4.0
var color: Color = Color(0.7, 0.5, 1.0)
var size: float = 0.18
var bounces: int = 0
var fuse: float = -1.0
var homing_target: Node3D = null
var homing_strength: float = 0.0
var knockback: float = 2.0
var trail: bool = true
var kind: String = "orb"   # orb, rivet, bomb, rocket

var _age: float = 0.0
var _mask: int = 0
var _visual: MeshInstance3D
var _light: OmniLight3D
var _trail: GPUParticles3D


static func spawn(ctx: Node, pos: Vector3, vel: Vector3, opts: Dictionary) -> Projectile:
	var p := Projectile.new()
	for k in opts:
		p.set(k, opts[k])
	p.velocity = vel
	VFX.root(ctx).add_child(p)
	p.global_position = pos
	return p


func _ready() -> void:
	_mask = Combat.MASK_WORLD | Combat.MASK_PARTS | Combat.MASK_DEBRIS
	_mask |= Combat.MASK_ENEMIES if from_player else Combat.MASK_PLAYER
	if not from_player:
		add_to_group("enemy_projectiles")
	_build_visual()


func _build_visual() -> void:
	_visual = MeshInstance3D.new()
	_visual.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	match kind:
		"rivet":
			var cm := CylinderMesh.new()
			cm.top_radius = size * 0.35
			cm.bottom_radius = size * 0.35
			cm.height = size * 4.0
			cm.radial_segments = 6
			_visual.mesh = cm
			_visual.material_override = VFX.glow_mat(color, 3.0)
			_visual.rotation.x = PI / 2
		"bomb", "rocket":
			var sm := SphereMesh.new()
			sm.radius = size
			sm.height = size * 2.0 * (1.6 if kind == "rocket" else 1.0)
			sm.radial_segments = 10
			sm.rings = 6
			_visual.mesh = sm
			_visual.material_override = MaterialLib.get_named("M_DarkMetal")
			var fuse_glow := MeshInstance3D.new()
			var fm := SphereMesh.new()
			fm.radius = size * 0.35
			fm.height = size * 0.7
			fuse_glow.mesh = fm
			fuse_glow.material_override = VFX.glow_mat(color, 5.0)
			fuse_glow.position = Vector3(0, size * 0.9, 0) if kind == "bomb" else Vector3(0, 0, size * 1.4)
			_visual.add_child(fuse_glow)
			if kind == "rocket":
				_visual.rotation.x = PI / 2
		_:
			var sm2 := SphereMesh.new()
			sm2.radius = size
			sm2.height = size * 2.0
			sm2.radial_segments = 10
			sm2.rings = 6
			_visual.mesh = sm2
			_visual.material_override = VFX.glow_mat(color, 4.0)
			var halo := MeshInstance3D.new()
			var hm := QuadMesh.new()
			hm.size = Vector2.ONE * size * 6.0
			halo.mesh = hm
			var hmat := VFX.additive_mat("vfx_glow", false).duplicate() as StandardMaterial3D
			hmat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
			hmat.albedo_color = Color(color, 0.8)
			hmat.vertex_color_use_as_albedo = false
			halo.material_override = hmat
			halo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_visual.add_child(halo)
	add_child(_visual)
	if kind == "orb" and size >= 0.25:
		_light = OmniLight3D.new()
		_light.light_color = color
		_light.light_energy = 1.8
		_light.omni_range = 5.0
		add_child(_light)
	if trail:
		_trail = GPUParticles3D.new()
		_trail.amount = 24 if kind != "rivet" else 8
		_trail.lifetime = 0.35 if kind != "bomb" else 0.6
		_trail.local_coords = false
		var pm := ParticleProcessMaterial.new()
		pm.gravity = Vector3(0, 1.0 if kind in ["bomb", "rocket"] else 0.0, 0)
		pm.initial_velocity_min = 0.0
		pm.initial_velocity_max = 0.4
		pm.spread = 180.0
		pm.scale_min = size * 1.2
		pm.scale_max = size * 2.0
		VFX._curves()
		pm.scale_curve = VFX._scale_curve
		pm.color = color if kind not in ["bomb", "rocket"] else Color(0.55, 0.55, 0.6)
		_trail.process_material = pm
		if kind in ["bomb", "rocket"]:
			_trail.draw_pass_1 = VFX._puff_mesh
			_trail.material_override = VFX.puff_mat()
		else:
			_trail.draw_pass_1 = VFX._quad
			_trail.material_override = VFX.additive_mat("vfx_glow")
		_trail.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(_trail)


func _physics_process(delta: float) -> void:
	_age += delta
	if _age > lifetime:
		_detonate(global_position, null)
		return
	if fuse > 0.0 and _age >= fuse:
		_detonate(global_position, null)
		return
	if homing_target and is_instance_valid(homing_target) and homing_strength > 0.0:
		var tp: Vector3 = homing_target.aim_point() if homing_target.has_method("aim_point") else homing_target.global_position
		var want := (tp - global_position).normalized() * velocity.length()
		velocity = velocity.lerp(want, clampf(homing_strength * delta, 0.0, 1.0))
	velocity.y -= gravity * delta
	var from := global_position
	var to := from + velocity * delta
	var q := PhysicsRayQueryParameters3D.create(from, to, _mask)
	if source is CollisionObject3D:
		q.exclude = [(source as CollisionObject3D).get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if hit:
		if bounces > 0 and not (hit["collider"] is CharacterBody3D) and not Combat.is_enemy(hit["collider"]):
			bounces -= 1
			var n: Vector3 = hit["normal"]
			velocity = velocity.bounce(n) * 0.55
			global_position = hit["position"] + n * 0.05
			AudioManager.play("impact_metal", global_position, -8.0, 1.4)
			return
		global_position = hit["position"]
		_impact(hit)
		return
	global_position = to
	if velocity.length_squared() > 0.01:
		var look_up := Vector3.UP if absf(velocity.normalized().dot(Vector3.UP)) < 0.98 else Vector3.RIGHT
		look_at(global_position + velocity, look_up)
	if not from_player:
		_check_wards()


func _check_wards() -> void:
	for w in get_tree().get_nodes_in_group("wards"):
		if w.has_method("blocks") and w.blocks(global_position):
			w.on_block(global_position)
			VFX.sparkle(self, global_position, Color(0.5, 0.95, 1.0), 8, 0.3)
			queue_free()
			return


func _impact(hit: Dictionary) -> void:
	var col: Object = hit["collider"]
	var info := DamageInfo.make(damage, damage_type, source, hit["position"], velocity.normalized(), knockback, from_player)
	if damage > 0.0:
		Combat.damage_hit(hit, info)
	_detonate(hit["position"], hit.get("normal", Vector3.UP), col)


func _detonate(pos: Vector3, normal: Variant, _col: Object = null) -> void:
	if splash_radius > 0.0:
		Combat.explode(self, pos, splash_radius, splash_damage, damage_type, source, from_player, true)
	else:
		var n: Vector3 = normal if normal is Vector3 else Vector3.UP
		VFX.burst(self, pos + n * 0.05, color, 10, 4.0, 0.14, 0.35, -6.0, "spark", 70.0, n)
		if kind == "orb":
			VFX.sphere_pop(self, pos, color, size * 1.4, 0.2)
		var snd := "spell_arcane_hit" if damage_type in ["arcane", "shock"] else "impact_metal"
		AudioManager.play(snd, pos, -6.0, 1.1)
	queue_free()
