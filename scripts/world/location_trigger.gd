class_name LocationTrigger
extends Area3D
## Fires Events.location_reached when the player (on foot or piloting) enters the sphere.

var location_id: String = ""
var radius: float = 5.0
var once: bool = false
var toast_text: String = ""
var _inside: bool = false
var _fired: bool = false


func _ready() -> void:
	collision_layer = 0
	collision_mask = 2
	monitoring = true
	var cs := CollisionShape3D.new()
	var s := SphereShape3D.new()
	s.radius = radius
	cs.shape = s
	add_child(cs)
	body_entered.connect(_on_enter)
	body_exited.connect(func(b): if b is Player: _inside = false)


func _process(_delta: float) -> void:
	# Piloted contraptions carry the player with collisions disabled: check by distance too.
	var p := get_tree().get_first_node_in_group("player") as Player
	if p and p.piloting and not _inside:
		if p.global_position.distance_to(global_position) < radius + 2.0:
			_on_enter(p)
	elif p and p.piloting and _inside and p.global_position.distance_to(global_position) > radius + 4.0:
		_inside = false


func _on_enter(b: Node) -> void:
	if not (b is Player) or _inside:
		return
	_inside = true
	if once and _fired:
		return
	_fired = true
	Events.location_reached.emit(location_id)
	var need := false
	for q in Quests.active_quests():
		for o in Quests.def(q)["objectives"]:
			if o["type"] == "reach" and o.get("target", "") == location_id:
				need = true
	if need:
		if toast_text != "":
			Events.toast(toast_text, "quest")
		AudioManager.play_2d("notify", -2.0)
		VFX.sparkle(self, global_position, Color(0.4, 0.95, 0.9), 20, 0.4)
