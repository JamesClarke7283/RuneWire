class_name AltitudeChallenge
extends ChallengeRunner
## Skyward Beacon: touch the beacon floating 40 m above the Builder's Flats.

var beacon_pos: Vector3 = Vector3.ZERO
var beacon_node: Node3D
var _light: OmniLight3D
var _t: float = 0.0


func _ready() -> void:
	super._ready()
	challenge_id = "altitude"
	time_limit = 300.0
	_light = OmniLight3D.new()
	_light.light_color = Color(0.4, 0.95, 0.9)
	_light.light_energy = 3.0
	_light.omni_range = 18.0
	add_child(_light)
	_light.top_level = true
	_light.global_position = beacon_pos


func _begin() -> void:
	Events.toast("Reach the floating beacon! Hover stones, rotors, spring pads... anything goes.", "quest")


func status_text() -> String:
	var p := player()
	var d := p.global_position.distance_to(beacon_pos) if p else 0.0
	return "Beacon: %d m away  ·  %s" % [int(d), Challenges.format_value("altitude", elapsed)]


func _process(delta: float) -> void:
	super._process(delta)
	_t += delta
	if beacon_node:
		beacon_node.rotation.y += delta * 0.8
		beacon_node.position.y = beacon_pos.y + sin(_t * 1.5) * 0.4
	if _light:
		_light.global_position = beacon_pos
		_light.light_energy = 3.0 + (2.0 if running else 0.0) + sin(_t * 3.0) * 0.6


func _tick(_delta: float) -> void:
	var p := player()
	if p == null:
		return
	if p.global_position.distance_to(beacon_pos) < 5.0 or p.camera.global_position.distance_to(beacon_pos) < 5.0:
		VFX.sparkle(self, beacon_pos, Color(0.4, 0.95, 0.9), 40, 0.6)
		VFX.ring(self, beacon_pos, Color(1.0, 0.85, 0.4), 8.0, 0.6)
		complete(elapsed)
