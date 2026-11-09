class_name Npc
extends Node3D
## Townsfolk and quest givers: idle "breathing", head tracking, gestures while talking,
## quest markers (! / ?) and simple wandering for villagers.

var npc_id: String = ""
var model_name: String = ""
var wanders: bool = false
var model: Node3D
var talking: float = 0.0

var _nodes: Dictionary = {}
var _t: float = 0.0
var _marker: Node3D
var _marker_kind: String = ""
var _marker_timer: float = 0.0
var _home: Vector3
var _walk_target: Vector3
var _walk_wait: float = 0.0
var _world: World
var _rest: Dictionary = {}

const VILLAGER_LINES := [
	"Lovely day for tinkering, isn't it?",
	"I heard the Gearworks drones stole a whole bakery oven.",
	"Gold makes the gears go round, my nan always said.",
	"Mind the wisps after dark, dear.",
	"Odda once built a flying bathtub. It flew, too. Briefly.",
	"They say the Arena crowd cheers louder for builders.",
	"If you see a crate on wheels speeding by, that's my son.",
	"The ley stones hum when nobody's listening.",
]


func _ready() -> void:
	add_to_group("npcs")
	_world = get_tree().get_first_node_in_group("world")
	_home = global_position
	_walk_target = _home
	model = MaterialLib.instance_model("res://assets/models/npcs/%s.glb" % model_name)
	if model == null:
		model = _placeholder()
	add_child(model)
	for n in model.find_children("*", "Node3D", true, false):
		_nodes[String(n.name)] = n
		_rest[String(n.name)] = (n as Node3D).transform
	var body := StaticBody3D.new()
	body.collision_layer = 32 if wanders else (1 | 32)
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.45
	cap.height = 1.8
	cs.shape = cap
	cs.position.y = 0.9
	body.add_child(cs)
	add_child(body)
	_marker = Node3D.new()
	_marker.position.y = 2.6 if npc_id != "gus" else 2.0
	add_child(_marker)
	_t = randf() * 10.0
	Quests.quest_updated.connect(func(_q): _marker_timer = 0.0)
	Quests.quest_completed.connect(func(_q): _marker_timer = 0.0)
	Quests.quest_accepted.connect(func(_q): _marker_timer = 0.0)


func display_name() -> String:
	if npc_id.begins_with("villager"):
		return "Villager"
	return QuestDB.NPC_NAMES.get(npc_id, npc_id.capitalize())


func get_interact_text() -> String:
	return "[E] Talk to %s" % display_name()


func interact(player: Player) -> void:
	talking = 3.0
	_face(player.global_position, 1.0)
	if npc_id.begins_with("villager"):
		Events.toast("Villager: \"%s\"" % VILLAGER_LINES[randi() % VILLAGER_LINES.size()], "info")
		return
	Events.npc_talked.emit(npc_id)
	var ui := get_tree().get_first_node_in_group("game_ui")
	if ui:
		ui.open_dialogue(self)


func node(n: String) -> Node3D:
	return _nodes.get(n, null)


func _face(p: Vector3, w: float) -> void:
	var d := p - global_position
	d.y = 0
	if d.length() > 0.1:
		rotation.y = lerp_angle(rotation.y, atan2(d.x, d.z), w)


func _process(delta: float) -> void:
	_t += delta
	talking = maxf(0.0, talking - delta)
	var player := get_tree().get_first_node_in_group("player") as Player
	var near := player != null and player.global_position.distance_to(global_position) < 7.0
	# breathing
	var body := node("Body")
	if body and _rest.has("Body"):
		var r: Transform3D = _rest["Body"]
		body.transform = r
		body.scale = Vector3(1.0, 1.0 + sin(_t * 2.2) * 0.012, 1.0)
	# head tracking
	var head := node("Head")
	if head and _rest.has("Head"):
		var hr: Transform3D = _rest["Head"]
		var yaw := 0.0
		var pitch := 0.0
		if near and player:
			var local := global_transform.basis.inverse() * (player.camera.global_position - head.global_position)
			yaw = clampf(atan2(local.x, local.z), -1.1, 1.1)
			pitch = clampf(-atan2(local.y, Vector2(local.x, local.z).length()), -0.4, 0.4)
		else:
			yaw = sin(_t * 0.4) * 0.3
		head.transform = Transform3D(hr.basis * Basis.from_euler(Vector3(pitch, yaw, sin(_t * 0.7) * 0.04)), hr.origin)
	# arms: idle sway, gestures while talking
	for side in ["ArmL", "ArmR"]:
		var arm := node(side)
		if arm and _rest.has(side):
			var ar: Transform3D = _rest[side]
			var s := 1.0 if side == "ArmL" else -1.0
			var g := 0.0
			if talking > 0.0:
				g = (sin(_t * 5.0 + (0.0 if side == "ArmL" else 1.5)) * 0.5 + 0.5) * 0.9
			var walk := 0.0
			if wanders and _walk_wait <= 0.0:
				walk = sin(_t * 7.0) * 0.4 * s
			arm.transform = Transform3D(ar.basis * Basis.from_euler(Vector3(-g + walk + sin(_t * 1.6) * 0.03, 0, s * (0.06 + g * 0.15))), ar.origin)
	if wanders:
		_wander(delta, near and talking > 0.0)
	elif near and talking > 0.0 and player:
		_face(player.global_position, 1.0 - exp(-4.0 * delta))
	_marker_timer -= delta
	if _marker_timer <= 0.0:
		_marker_timer = 0.6
		_update_marker()
	if _marker:
		_marker.position.y = (2.6 if npc_id != "gus" else 2.0) + sin(_t * 3.0) * 0.08
		_marker.rotation.y += delta * 1.5


func _wander(delta: float, hold: bool) -> void:
	if hold:
		return
	if _walk_wait > 0.0:
		_walk_wait -= delta
		return
	var to := _walk_target - global_position
	to.y = 0
	if to.length() < 0.5:
		_walk_wait = randf_range(2.0, 6.0)
		var a := randf() * TAU
		_walk_target = _home + Vector3(cos(a), 0, sin(a)) * randf_range(2.0, 9.0)
		return
	var step := to.normalized() * 1.3 * delta
	global_position += step
	if _world:
		global_position.y = _world.ground_y(global_position.x, global_position.z)
	rotation.y = lerp_angle(rotation.y, atan2(to.x, to.z), 1.0 - exp(-6.0 * delta))
	if model:
		model.position.y = absf(sin(_t * 7.0)) * 0.04


func _update_marker() -> void:
	if npc_id.begins_with("villager"):
		return
	var kind := ""
	if not Quests.ready_for(npc_id).is_empty():
		kind = "turnin"
	else:
		for q in Quests.offered_by(npc_id):
			if not Quests.def(q).get("repeatable", false):
				kind = "offer"
				break
	if kind == _marker_kind:
		return
	_marker_kind = kind
	for c in _marker.get_children():
		c.queue_free()
	if kind == "":
		return
	var tex := UIStyle.tex("ui_quest_marker" if kind == "offer" else "ui_quest_turnin")
	if tex:
		var s := Sprite3D.new()
		s.texture = tex
		s.pixel_size = 0.006
		s.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		s.shaded = false
		s.no_depth_test = false
		_marker.add_child(s)
	else:
		var l := Label3D.new()
		l.text = "!" if kind == "offer" else "?"
		l.font_size = 140
		l.outline_size = 28
		l.modulate = Color(1.0, 0.84, 0.25)
		l.outline_modulate = Color(0.25, 0.12, 0.05)
		l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		var f := UIStyle.display_font()
		if f:
			l.font = f
		_marker.add_child(l)


func _placeholder() -> Node3D:
	var root := Node3D.new()
	var colors := {"odda": Color("3aa6a0"), "lirael": Color("7a4fd8"), "gus": Color("d9a441"), "brannoc": Color("a9b0b8")}
	var c: Color = colors.get(npc_id, Color("c9784a"))
	var body := MeshInstance3D.new()
	body.name = "Body"
	var cm := CapsuleMesh.new()
	cm.radius = 0.38
	cm.height = 1.3
	body.mesh = cm
	body.position.y = 0.65
	body.material_override = MaterialLib.get_named("M_Fabric__" + c.to_html(false))
	root.add_child(body)
	var head := MeshInstance3D.new()
	head.name = "Head"
	var sm := SphereMesh.new()
	sm.radius = 0.3
	sm.height = 0.6
	head.mesh = sm
	head.position.y = 1.55
	head.material_override = MaterialLib.get_named("M_Skin") if npc_id != "gus" else MaterialLib.get_named("M_Brass")
	root.add_child(head)
	for side in [-1, 1]:
		var eye := MeshInstance3D.new()
		var em := SphereMesh.new()
		em.radius = 0.06
		em.height = 0.12
		eye.mesh = em
		eye.material_override = MaterialLib.get_flat(Color(0.1, 0.08, 0.12))
		eye.position = Vector3(side * 0.1, 0.05, 0.26)
		head.add_child(eye)
	return root
