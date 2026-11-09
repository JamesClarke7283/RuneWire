extends Enemy
## Ember Wisp: a darting flame spirit that strafes the player and spits homing fireballs.

var _flames: Array = []
var _embers: Array = []
var _light: OmniLight3D


func _setup() -> void:
	body_height = 0.8
	body_radius = 0.4
	hover_height = 2.6


func _on_model_ready() -> void:
	for i in 4:
		var f := node("Flame_%d" % i)
		if f:
			_flames.append(f)
	for i in 3:
		var e := node("Ember_%d" % i)
		if e:
			_embers.append(e)
	_light = OmniLight3D.new()
	_light.light_color = Color(1.0, 0.6, 0.25)
	_light.light_energy = 1.4
	_light.omni_range = 5.0
	add_child(_light)
	AudioManager.attach_loop(self, "wisp_loop", -12.0, 4.0)


func think(delta: float, dist: float) -> void:
	if aggro and target:
		strafe_around(target.global_position, 9.0, move_speed)
		face_towards(target.global_position, delta, 8.0)
		if attack_cd <= 0.0 and can_attack() and dist < 24.0:
			attack_cd = randf_range(1.8, 2.6)
			var from := aim_point() + facing_dir() * 0.4
			shoot(from, target_pos(), 16.0, 8.0, "fire", Color(1.0, 0.55, 0.15), {"size": 0.2, "homing_target": target, "homing_strength": 0.9})
			AudioManager.play("wisp_attack", from, -2.0)
	else:
		wander(move_speed)


func animate(delta: float) -> void:
	if model:
		model.position.y = sin(_anim_t * 3.0) * 0.12
	for i in _flames.size():
		var f: Node3D = _flames[i]
		var s := 1.0 + sin(_anim_t * 9.0 + i * 1.7) * 0.15
		f.scale = Vector3(s, 1.0 + sin(_anim_t * 11.0 + i) * 0.22, s)
	for i in _embers.size():
		var e: Node3D = _embers[i]
		var a := _anim_t * 2.2 + i * TAU / 3.0
		e.position = Vector3(cos(a) * 0.6, sin(_anim_t * 3.0 + i) * 0.15, sin(a) * 0.6)
	if _light:
		_light.light_energy = 1.2 + sin(_anim_t * 13.0) * 0.3
	var _u := delta
