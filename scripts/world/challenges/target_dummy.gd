class_name TargetDummy
extends StaticBody3D
## The hittable face of a range target. Tilts up when active, flips down when hit.

var challenge: TargetChallenge
var up: bool = false
var _model: Node3D


func _ready() -> void:
	collision_layer = 8
	collision_mask = 0
	var cs := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = 0.75
	cyl.height = 0.3
	cs.shape = cyl
	cs.rotation.x = PI / 2
	cs.position = Vector3(0, 1.45, 0)
	add_child(cs)
	_model = get_parent() as Node3D


func set_up(v: bool) -> void:
	up = v
	if _model == null:
		return
	var tw := create_tween()
	tw.tween_property(_model, "rotation:x", 0.0 if v else -1.4, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	if v:
		VFX.sparkle(self, global_position + Vector3.UP * 1.5, Color(1.0, 0.85, 0.3), 6, 0.25)


func apply_damage(_info: DamageInfo) -> void:
	if up and challenge:
		VFX.burst(self, global_position + Vector3.UP * 1.5, Color(1.0, 0.85, 0.3), 12, 4.0, 0.15, 0.4, -8.0, "spark")
		challenge.on_hit(self)
