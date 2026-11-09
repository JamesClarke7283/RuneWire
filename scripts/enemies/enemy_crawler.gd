extends Enemy
## Clank Crawler: a fast spider-bot that skitters in and pounces. Procedural six-leg gait.

var _pounce_t: float = -1.0
var _gait: float = 0.0
var _legs: Array = []


func _setup() -> void:
	body_height = 0.9
	body_radius = 0.6


func _on_model_ready() -> void:
	for i in 6:
		var hip := node("Leg%d_Hip" % i)
		var up := node("Leg%d_Upper" % i)
		var lo := node("Leg%d_Lower" % i)
		if hip or up:
			_legs.append({"hip": hip, "upper": up, "lower": lo, "phase": (0.0 if i % 2 == 0 else PI) + (i / 2) * 0.4})
	AudioManager.attach_loop(self, "crawler_skitter", -16.0, 4.0)


func think(delta: float, dist: float) -> void:
	if _pounce_t >= 0.0:
		_pounce_t += delta
		if _pounce_t > 0.25 and is_on_floor():
			_pounce_t = -1.0
		if melee(1.8, 12.0, "kinetic", 5.0):
			AudioManager.play("crawler_bite", global_position, 0.0)
			_pounce_t = -1.0
			attack_cd = 1.2
		return
	if aggro and target:
		face_towards(target.global_position, delta, 9.0)
		if dist < 7.0 and attack_cd <= 0.0 and is_on_floor():
			attack_cd = 1.8
			_pounce_t = 0.0
			var to := (target.global_position - global_position)
			to.y = 0
			velocity = to.normalized() * 11.0 + Vector3.UP * 6.5
			AudioManager.play("crawler_bite", global_position, -6.0, 1.3)
			return
		steer_to(target.global_position, move_speed)
	else:
		wander(move_speed)


func _move(delta: float) -> void:
	if _pounce_t >= 0.0:
		velocity.y -= 22.0 * delta
		move_and_slide()
		return
	super._move(delta)


func animate(delta: float) -> void:
	var spd := Vector2(velocity.x, velocity.z).length()
	_gait += delta * clampf(spd, 0.0, 9.0) * 2.4
	var body := node("Body")
	if body:
		body.position.y = body.position.y
		body.rotation.x = lerpf(body.rotation.x, -0.35 if _pounce_t >= 0.0 else 0.0, 1.0 - exp(-10.0 * delta))
	for leg in _legs:
		var ph: float = leg["phase"] + _gait
		var lift := maxf(0.0, sin(ph)) * clampf(spd / 4.0, 0.0, 1.0)
		var swing := cos(ph) * 0.35 * clampf(spd / 4.0, 0.0, 1.0)
		if leg["hip"]:
			(leg["hip"] as Node3D).rotation.y = swing
		if leg["upper"]:
			(leg["upper"] as Node3D).rotation.z = 0.0
			(leg["upper"] as Node3D).rotation.x = -lift * 0.5
		if leg["lower"]:
			(leg["lower"] as Node3D).rotation.x = lift * 0.6
