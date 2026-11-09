class_name TargetChallenge
extends ChallengeRunner
## Target Range: 60 seconds, three targets up at a time; every hit pops up another.

var targets: Array = []
var area_center: Vector3 = Vector3.ZERO
var score: int = 0
var _dummies: Array = []


func _ready() -> void:
	super._ready()
	challenge_id = "targets"
	time_limit = 60.0
	_setup_dummies.call_deferred()


func _setup_dummies() -> void:
	for t in targets:
		var d := TargetDummy.new()
		d.challenge = self
		(t as Node3D).add_child(d)
		_dummies.append(d)
		d.set_up(false)


func status_text() -> String:
	return "Hits: %d  ·  Time left %ds" % [score, int(ceil(time_limit - elapsed))]


func _begin() -> void:
	score = 0
	for d in _dummies:
		d.set_up(false)
	for i in 3:
		_raise_random()
	Events.toast("Hit the raised targets! 60 seconds!", "quest")


func _raise_random() -> void:
	var down := _dummies.filter(func(d): return not d.up)
	if down.is_empty():
		return
	(down[randi() % down.size()] as TargetDummy).set_up(true)


func on_hit(d: TargetDummy) -> void:
	if not running or not d.up:
		return
	score += 1
	d.set_up(false)
	AudioManager.play_2d("coin_pickup", -3.0, 1.0 + score * 0.01)
	_raise_random()


func _on_timeout() -> void:
	complete(float(score))


func _cleanup() -> void:
	for d in _dummies:
		d.set_up(false)
