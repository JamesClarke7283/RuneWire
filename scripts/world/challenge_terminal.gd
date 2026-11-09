class_name ChallengeTerminal
extends Node3D
## Console that shows a challenge's medals and best result and starts it.

var challenge_id: String = ""
var _light: OmniLight3D
var _t: float = 0.0


func _ready() -> void:
	var body := StaticBody3D.new()
	body.collision_layer = 32
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = Vector3(1.4, 1.8, 1.4)
	cs.shape = bs
	cs.position = Vector3(0, 0.9, 0)
	body.add_child(cs)
	add_child(body)
	_light = OmniLight3D.new()
	_light.light_color = Color(0.4, 0.95, 0.85)
	_light.light_energy = 1.2
	_light.omni_range = 4.0
	_light.position = Vector3(0, 1.8, 0)
	add_child(_light)


func runner() -> ChallengeRunner:
	for c in get_children():
		if c is ChallengeRunner:
			return c
	return null


func get_interact_text() -> String:
	var d := Challenges.def(challenge_id)
	if Challenges.running == challenge_id:
		return "[E] %s: abandon run" % d["name"]
	return "[E] %s" % d["name"]


func interact(_player: Player) -> void:
	var r := runner()
	if Challenges.running == challenge_id and r:
		r.abort("abandoned")
		return
	var ui := get_tree().get_first_node_in_group("game_ui")
	if ui:
		ui.open_challenge(challenge_id, r)


func _process(delta: float) -> void:
	_t += delta
	if _light:
		_light.light_energy = 1.0 + sin(_t * 3.0) * 0.3 + (1.5 if Challenges.running == challenge_id else 0.0)
