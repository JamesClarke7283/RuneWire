class_name CargoChallenge
extends ChallengeRunner
## Gorge Haul: move a heavy crate across the gorge onto the goal pad.

var start_pos: Vector3 = Vector3.ZERO
var goal_pos: Vector3 = Vector3.ZERO
var goal_node: Node3D
var _crate: Part = null
var _settle: float = 0.0


func _ready() -> void:
	super._ready()
	challenge_id = "cargo"
	time_limit = 300.0


func _begin() -> void:
	var bm := _world.build_manager
	_crate = bm.spawn_part("haul_crate", Transform3D(Basis(), start_pos), false)
	_settle = 0.0
	Events.toast("Get the crate across the gorge onto the glowing pad! Too heavy to carry: build something.", "quest")


func status_text() -> String:
	var d := -1.0
	if _crate and is_instance_valid(_crate):
		d = Vector2(_crate.global_position.x - goal_pos.x, _crate.global_position.z - goal_pos.z).length()
	return "Crate to pad: %s  ·  %s" % ["%d m" % int(d) if d >= 0 else "?", Challenges.format_value("cargo", elapsed)]


func _tick(delta: float) -> void:
	if _crate == null or not is_instance_valid(_crate):
		abort("the crate was lost")
		return
	var flat := Vector2(_crate.global_position.x - goal_pos.x, _crate.global_position.z - goal_pos.z).length()
	if flat < 4.2 and absf(_crate.global_position.y - goal_pos.y) < 3.0:
		_settle += delta
		if _settle > 1.0:
			VFX.sparkle(self, goal_pos + Vector3.UP, Color(1.0, 0.85, 0.3), 30, 0.5)
			complete(elapsed)
	else:
		_settle = 0.0
	if _crate.global_position.y < -20.0:
		abort("the crate fell into the abyss")


func _cleanup() -> void:
	if _crate and is_instance_valid(_crate):
		var c := _crate.contraption
		VFX.sparkle(self, _crate.global_position, Color(0.4, 0.95, 0.9), 16, 0.4)
		if c:
			c.remove_part(_crate, false)
		_crate.queue_free()
	_crate = null
