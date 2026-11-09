class_name RaceChallenge
extends ChallengeRunner
## Valley Rally: pass through the rune rings in order, as fast as possible.

var rings: Array = []
var index: int = 0
var _beam: MeshInstance3D
var _light: OmniLight3D


func _ready() -> void:
	super._ready()
	challenge_id = "race"
	time_limit = 300.0


func _begin() -> void:
	index = 0
	_make_marker()
	_move_marker()
	Events.toast("Go! Fly or drive through ring 1 of %d" % rings.size(), "quest")


func status_text() -> String:
	return "Ring %d/%d  ·  %s" % [index + 1, rings.size(), Challenges.format_value("race", elapsed)]


func _make_marker() -> void:
	if _beam:
		return
	_beam = MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.6
	cm.bottom_radius = 0.6
	cm.height = 60.0
	cm.radial_segments = 12
	_beam.mesh = cm
	var m := VFX.glow_alpha_mat(Color(0.3, 0.95, 0.85, 0.35))
	_beam.material_override = m
	_beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_beam)
	_beam.top_level = true
	_light = OmniLight3D.new()
	_light.light_color = Color(0.3, 0.95, 0.85)
	_light.light_energy = 4.0
	_light.omni_range = 14.0
	add_child(_light)
	_light.top_level = true


func _move_marker() -> void:
	if index >= rings.size():
		return
	var r: Node3D = rings[index]
	_beam.global_position = r.global_position + Vector3.UP * 30.0
	_light.global_position = r.global_position
	_beam.visible = true
	_light.visible = true


func _tick(_delta: float) -> void:
	var p := player()
	if p == null or index >= rings.size():
		return
	var r: Node3D = rings[index]
	if p.camera.global_position.distance_to(r.global_position) < 5.5 or p.global_position.distance_to(r.global_position) < 5.5:
		VFX.ring(self, r.global_position, Color(0.3, 0.95, 0.85), 6.0, 0.5)
		VFX.sparkle(self, r.global_position, Color(1.0, 0.85, 0.4), 20, 0.45)
		AudioManager.play_2d("coin_pickup", -2.0, 0.8 + index * 0.05)
		index += 1
		if index >= rings.size():
			complete(elapsed)
			return
		_move_marker()


func _cleanup() -> void:
	if _beam:
		_beam.visible = false
		_light.visible = false
