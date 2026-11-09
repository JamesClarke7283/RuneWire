class_name WheelDevice
extends Device
## Raycast suspension wheel. Welded wheels drive the contraption from the pilot seat:
## W/S throttle, A/D steer (front wheels turn, plus skid-steer for tank builds), idle = brake.

var radius: float = 0.45
var travel: float = 0.32
var spin: float = 0.0
var steer: float = 0.0
var grounded: bool = false
var _up_local: Vector3 = Vector3.UP       # contraption-space up captured when attached
var _wheel_node: Node3D
var _rest_xf: Transform3D
var _offset: float = 0.0
var _front: bool = false
var _side: float = 0.0
var _roll_snd: AudioStreamPlayer3D


func on_attached(c: Contraption) -> void:
	super.on_attached(c)
	radius = float(part.def.get("radius", 0.45))
	travel = clampf(radius * 0.7, 0.25, 0.55)
	_up_local = (c.global_transform.basis.inverse() * Vector3.UP).normalized()
	_wheel_node = part.model.find_child("Wheel", true, false) as Node3D
	if _wheel_node == null:
		_wheel_node = part.model
	_rest_xf = _wheel_node.transform


func on_detached() -> void:
	super.on_detached()
	if _wheel_node:
		_wheel_node.transform = _rest_xf


func on_recomputed() -> void:
	if contraption == null:
		return
	var seat := contraption.seat_part()
	var rel := part.global_position - contraption.global_transform * contraption.center_of_mass
	if seat:
		var b := seat.global_transform.basis.orthonormalized()
		_front = rel.dot(b.z) > 0.25
		_side = signf(rel.dot(-b.x))   # +1 on the right side
	else:
		_front = false
		_side = 0.0


func physics_step(delta: float, ctl: Dictionary, piloted: bool) -> void:
	if contraption == null or contraption.parts.size() < 2:
		return
	var body := contraption
	var up := (body.global_transform.basis * _up_local).normalized()
	var center := part.global_position
	var origin := center + up * travel * 0.5
	var ray_len := travel + radius
	var q := PhysicsRayQueryParameters3D.create(origin, origin - up * ray_len, 1 | 4 | 128)
	q.exclude = [body.get_rid()]
	var hit := body.get_world_3d().direct_space_state.intersect_ray(q)
	var n_wheels := maxi(1, body.wheel_count())
	var m_share := body.mass / n_wheels
	# steering
	var steer_in: float = ctl.get("steer", 0.0) if piloted else 0.0
	var speed := body.linear_velocity.length()
	var max_steer := deg_to_rad(32.0) * lerpf(1.0, 0.35, clampf(speed / 24.0, 0.0, 1.0))
	steer = lerpf(steer, (-steer_in * max_steer) if _front else 0.0, 1.0 - exp(-8.0 * delta))
	var axle := (part.global_transform.basis.x).normalized()
	axle = axle.rotated(up, steer).normalized()
	var fwd := axle.cross(up).normalized()
	var seat := body.seat_part()
	if seat and fwd.dot(seat.global_transform.basis.z) < 0.0:
		fwd = -fwd
	var dist := ray_len
	grounded = not hit.is_empty()
	if grounded:
		var contact: Vector3 = hit["position"]
		dist = origin.distance_to(contact)
		var compression := ray_len - dist
		var rel_pos := contact - body.global_position
		var point_vel := body.linear_velocity + body.angular_velocity.cross(rel_pos)
		var k := m_share * Contraption.G / (travel * 0.45)
		var c := 2.0 * sqrt(k * m_share) * 0.55
		var f_spring := maxf(0.0, k * compression - c * point_vel.dot(up))
		var grip := f_spring * 1.15
		var v_long := point_vel.dot(fwd)
		var v_lat := point_vel.dot(axle)
		var f_lat := clampf(-v_lat * m_share / delta * 0.35, -grip, grip)
		var throttle: float = ctl.get("throttle", 0.0) if piloted else 0.0
		var boost := 1.5 if ctl.get("boost", false) else 1.0
		var engine := body.mass * 8.0 / n_wheels * boost
		var drive := 0.0
		var max_speed := 22.0 * boost
		if absf(throttle) > 0.05:
			if v_long * signf(throttle) < max_speed:
				drive = throttle * engine
			# skid-steer helps builds without steerable front wheels
			drive += steer_in * _side * engine * 0.6 * (1.0 if absf(throttle) > 0.05 else 0.0)
			if signf(throttle) != signf(v_long) and absf(v_long) > 1.0:
				drive += -signf(v_long) * engine * 0.6
		elif piloted and absf(steer_in) > 0.05 and _side != 0.0:
			drive = steer_in * _side * engine * 0.7
		else:
			drive = -v_long * m_share * (1.6 if piloted else 3.0)
		var f_long := clampf(drive, -grip, grip)
		body.apply_force(up * f_spring + fwd * f_long + axle * f_lat, rel_pos)
		spin += v_long / radius * delta
	else:
		spin += 0.0
	# visuals: travel along the suspension, spin about the axle, steer about up
	if _wheel_node:
		var part_basis_inv := part.global_transform.basis.orthonormalized().inverse()
		var up_part := (part_basis_inv * up).normalized()
		var drop := clampf(dist - radius - travel * 0.5, -travel * 0.5, travel)
		var xf := _rest_xf
		xf.basis = Basis(up_part, steer) * Basis(Vector3.RIGHT, -spin) * _rest_xf.basis
		xf.origin = _rest_xf.origin - up_part * drop
		_wheel_node.transform = xf
