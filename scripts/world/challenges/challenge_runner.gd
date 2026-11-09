class_name ChallengeRunner
extends Node3D
## Base for in-world challenge logic. Subclasses implement _begin(), _tick(delta), _cleanup().

var challenge_id: String = ""
var running: bool = false
var time_limit: float = 300.0
var elapsed: float = 0.0
var objective: String = ""
var _world: World


func _ready() -> void:
	_world = get_tree().get_first_node_in_group("world")
	Events.player_died.connect(func():
		if running:
			_on_player_died())


func start() -> bool:
	if running:
		return false
	if not Challenges.start(challenge_id):
		Events.toast("Finish your current challenge first!", "warn")
		return false
	running = true
	elapsed = 0.0
	AudioManager.play_2d("quest_accept", -2.0)
	if challenge_id == "arena":
		AudioManager.play_music("music_combat")
	_begin()
	return true


func abort(reason: String = "") -> void:
	if not running:
		return
	running = false
	_cleanup()
	Challenges.fail(challenge_id, reason)
	AudioManager.play_music("music_town")


func complete(value: float) -> void:
	if not running:
		return
	running = false
	_cleanup()
	var res := Challenges.finish(challenge_id, value)
	var medal: int = res["medal"]
	AudioManager.play_2d("quest_complete" if medal > 0 else "notify", -2.0)
	var ui := get_tree().get_first_node_in_group("game_ui")
	if ui:
		ui.show_challenge_result(challenge_id, res)
	AudioManager.play_music("music_town")


func _process(delta: float) -> void:
	if not running:
		return
	elapsed += delta
	if time_limit > 0.0 and elapsed > time_limit:
		_on_timeout()
		return
	_tick(delta)


func _on_timeout() -> void:
	abort("out of time")


func _on_player_died() -> void:
	abort("you were knocked out")


## HUD line shown while running.
func status_text() -> String:
	return "%s · %s" % [objective, Challenges.format_value("race", elapsed)]


func _begin() -> void:
	pass


func _tick(_delta: float) -> void:
	pass


func _cleanup() -> void:
	pass


func player() -> Player:
	return get_tree().get_first_node_in_group("player") as Player
