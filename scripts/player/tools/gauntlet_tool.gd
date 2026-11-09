class_name GauntletTool
extends EquipBase
## Grav Gauntlet: grab and carry parts at a distance, push/pull with the wheel, hold R and move
## the mouse to rotate (Shift snaps to 45°), RMB freezes in place (or unfreezes what you aim at).

const MAX_RANGE := 32.0
const MAX_MASS := 300.0

var held: RigidBody3D = null
var grab_local: Vector3 = Vector3.ZERO
var hold_dist: float = 4.0
var rel_basis: Basis = Basis()
var _beam: MeshInstance3D
var _imesh: ImmediateMesh
var _hum: AudioStreamPlayer
var _rotating: bool = false


func on_equip() -> void:
	super.on_equip()
	if _beam == null:
		_imesh = ImmediateMesh.new()
		_beam = MeshInstance3D.new()
		_beam.mesh = _imesh
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		m.albedo_color = Color(0.35, 0.95, 0.9, 0.85)
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.vertex_color_use_as_albedo = true
		_beam.material_override = m
		_beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_beam.top_level = true
		player.add_child(_beam)
		_hum = AudioStreamPlayer.new()
		_hum.bus = &"SFX"
		_hum.stream = AudioManager.stream("tool_grab_loop", true)
		_hum.volume_db = -10.0
		player.add_child(_hum)


func on_unequip() -> void:
	release()
	super.on_unequip()


func hint() -> String:
	if held:
		return "LMB release · Wheel push/pull · Hold R + mouse rotate (Shift snap) · RMB freeze"
	return "LMB grab · RMB unfreeze aimed part"


func status() -> String:
	return "Holding %d kg" % int(held.mass) if held else "Ready"


func aim_info() -> String:
	if held:
		return ""
	var hit := player.aim_ray(MAX_RANGE, 4)
	if hit and hit["collider"] is Contraption:
		var c := hit["collider"] as Contraption
		var p := c.part_from_shape(hit["shape"])
		var n := p.display_name() if p else "Contraption"
		var heavy := "  ·  TOO HEAVY" if c.mass > MAX_MASS else ""
		return "%s  ·  %s%s" % [n, c.describe(), heavy]
	return ""


func primary(pressed: bool) -> void:
	if pressed:
		_try_grab()
	else:
		release()


func secondary(pressed: bool) -> void:
	if not pressed:
		return
	if held:
		var c := held
		release()
		c.linear_velocity = Vector3.ZERO
		c.angular_velocity = Vector3.ZERO
		c.freeze = true
		AudioManager.play("tool_freeze", c.global_position, -2.0)
		VFX.ring(player, c.global_position, Color(0.5, 0.85, 1.0), 2.0, 0.35)
		Events.toast("Frozen in place", "info")
		return
	var hit := player.aim_ray(MAX_RANGE, 4)
	if hit and hit["collider"] is Contraption:
		var c2 := hit["collider"] as Contraption
		if c2.freeze:
			c2.freeze = false
			c2.sleeping = false
			AudioManager.play("tool_freeze", c2.global_position, -2.0, 1.4)
			VFX.ring(player, c2.global_position, Color(1.0, 0.8, 0.4), 2.0, 0.35)
			Events.toast("Unfrozen", "info")


func scroll(dir: int) -> bool:
	if held:
		hold_dist = clampf(hold_dist - dir * 0.9, 1.6, MAX_RANGE)
		return true
	return false


func mouse_motion(rel: Vector2) -> bool:
	if held and Input.is_action_pressed("reload"):
		_rotating = true
		var cam_basis := Basis(Vector3.UP, player.yaw)
		var right := Vector3.RIGHT
		rel_basis = Basis(Vector3.UP, rel.x * 0.006) * Basis(right, rel.y * 0.006) * rel_basis
		rel_basis = rel_basis.orthonormalized()
		var _unused := cam_basis
		return true
	_rotating = false
	return false


func _try_grab() -> void:
	var hit := player.aim_ray(MAX_RANGE, 4 | 128)
	if hit.is_empty():
		AudioManager.play_2d("tool_configure", -12.0, 0.7)
		return
	var col: Object = hit["collider"]
	if not (col is RigidBody3D):
		return
	var rb := col as RigidBody3D
	if rb is Contraption and (rb as Contraption).pilot:
		Events.toast("Someone is piloting that!", "warn")
		return
	if rb.mass > MAX_MASS:
		Events.toast("Too heavy for the gauntlet (%d kg, max %d). Build a vehicle!" % [int(rb.mass), int(MAX_MASS)], "warn")
		AudioManager.play_ui("ui_error")
		return
	held = rb
	held.freeze = false
	held.sleeping = false
	if held is Contraption:
		(held as Contraption).held = true
	grab_local = held.to_local(hit["position"])
	hold_dist = player.camera.global_position.distance_to(hit["position"])
	rel_basis = Basis(Vector3.UP, -player.yaw) * held.global_transform.basis.orthonormalized()
	AudioManager.play_2d("tool_grab_start", -4.0)
	if _hum and _hum.stream:
		_hum.play()
	player.viewmodel.set_tilt(0.25)


func release() -> void:
	if held and is_instance_valid(held):
		if held is Contraption:
			(held as Contraption).held = false
		held.angular_velocity *= 0.3
	held = null
	_rotating = false
	if _hum:
		_hum.stop()
	if _imesh:
		_imesh.clear_surfaces()
	if player:
		player.viewmodel.set_tilt(0.0)


func tick(delta: float) -> void:
	if held == null:
		return
	if not is_instance_valid(held) or held.is_queued_for_deletion() or held.freeze:
		release()
		return
	var cam := player.camera
	var target := cam.global_position - cam.global_transform.basis.z * hold_dist
	var desired := (Basis(Vector3.UP, player.yaw) * rel_basis).orthonormalized()
	if _rotating and Input.is_key_pressed(KEY_SHIFT):
		var e := desired.get_euler()
		var snap := deg_to_rad(45.0)
		desired = Basis.from_euler(Vector3(roundf(e.x / snap) * snap, roundf(e.y / snap) * snap, roundf(e.z / snap) * snap))
	var cur := held.to_global(grab_local)
	var err := target - cur
	held.linear_velocity = (err / maxf(delta, 0.001) * 0.32).limit_length(38.0)
	var q_cur := held.global_transform.basis.orthonormalized().get_rotation_quaternion()
	var q_tgt := desired.get_rotation_quaternion()
	var q_err := q_tgt * q_cur.inverse()
	if q_err.w < 0.0:
		q_err = -q_err
	var angle := 2.0 * acos(clampf(q_err.w, -1.0, 1.0))
	if angle > 0.001:
		var axis := Vector3(q_err.x, q_err.y, q_err.z).normalized()
		held.angular_velocity = (axis * angle / maxf(delta, 0.001) * 0.25).limit_length(18.0)
	else:
		held.angular_velocity = Vector3.ZERO
	_draw_beam(player.viewmodel.muzzle_position(), cur)


func _draw_beam(from: Vector3, to: Vector3) -> void:
	_imesh.clear_surfaces()
	var cam_pos := player.camera.global_position
	var mid := (from + to) * 0.5 + Vector3.UP * from.distance_to(to) * 0.08
	var segs := 14
	_imesh.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
	var t_now := Time.get_ticks_msec() / 1000.0
	for i in segs + 1:
		var t := float(i) / segs
		var p := from.lerp(mid, t).lerp(mid.lerp(to, t), t)
		p += Vector3(sin(t * 18.0 + t_now * 14.0), cos(t * 15.0 + t_now * 11.0), 0) * 0.03 * sin(t * PI)
		var tangent := (mid.lerp(to, t) - from.lerp(mid, t)).normalized()
		var side := tangent.cross((cam_pos - p).normalized()).normalized()
		var w := lerpf(0.035, 0.07, t)
		var col := Color(0.35, 0.95, 0.9, 0.9).lerp(Color(0.6, 0.5, 1.0, 0.9), t)
		_imesh.surface_set_color(col)
		_imesh.surface_add_vertex(p - side * w)
		_imesh.surface_set_color(col)
		_imesh.surface_add_vertex(p + side * w)
	_imesh.surface_end()
