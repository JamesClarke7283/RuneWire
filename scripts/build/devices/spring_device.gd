class_name SpringDevice
extends Device
## Spring pad: launches players and loose contraptions that land on top. Boing.

var area: Area3D
var _top: Node3D
var _top_rest: Vector3
var _cooldown: Dictionary = {}


func _ready() -> void:
	area = Area3D.new()
	area.collision_layer = 0
	area.collision_mask = 2 | 4 | 8
	var cs := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = 0.55
	cyl.height = 0.5
	cs.shape = cyl
	cs.position = Vector3(0, 0.35, 0)
	area.add_child(cs)
	add_child(area)
	area.body_entered.connect(_on_body)
	_top = part.model.find_child("Top", true, false) as Node3D
	if _top:
		_top_rest = _top.position


func _on_body(body: Node) -> void:
	if not enabled or body == contraption:
		return
	var now := Time.get_ticks_msec()
	var key := body.get_instance_id()
	if _cooldown.has(key) and now - int(_cooldown[key]) < 600:
		return
	_cooldown[key] = now
	var up := part.global_transform.basis.y.normalized()
	if body is Player:
		(body as Player).velocity = (body as Player).velocity * 0.5 + up * 17.0
	elif body is RigidBody3D:
		var rb := body as RigidBody3D
		rb.apply_central_impulse(up * rb.mass * 13.0)
	elif body is CharacterBody3D:
		(body as CharacterBody3D).velocity += up * 14.0
	AudioManager.play("spring_boing", part.global_position, 0.0)
	VFX.ring(self, part.global_position + up * 0.3, Color(1.0, 0.85, 0.4), 1.6, 0.35)
	if _top:
		var tw := create_tween()
		tw.tween_property(_top, "position", _top_rest + Vector3(0, 0.35, 0), 0.08)
		tw.tween_property(_top, "position", _top_rest, 0.4).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
