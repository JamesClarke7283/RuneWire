class_name Pickup
extends Node3D
## Bouncy, spinning gold coins and loot items. They pop out of defeated foes, then get pulled
## into the player when close.

var kind: String = "coin"      # coin | item
var value: int = 1
var item_id: String = ""
var velocity: Vector3 = Vector3.ZERO
var _age: float = 0.0
var _model: Node3D
var _grounded: bool = false
var _base_y: float = 0.0
var _magnet: bool = false
var _world: World

static var _coin_scene: PackedScene = null
static var _coin_checked: bool = false


static func drop_coins(ctx: Node, pos: Vector3, gold: int) -> void:
	if gold <= 0:
		return
	var n := clampi(int(ceil(gold / 3.0)), 1, 10)
	var per := gold / n
	var rem := gold - per * n
	for i in n:
		var p := Pickup.new()
		p.kind = "coin"
		p.value = per + (1 if i < rem else 0)
		p.velocity = Vector3(randf_range(-3, 3), randf_range(5, 8), randf_range(-3, 3))
		VFX.root(ctx).add_child(p)
		p.global_position = pos
	AudioManager.play("coin_shower", pos, -4.0)


static func drop_item(ctx: Node, pos: Vector3, id: String) -> void:
	var p := Pickup.new()
	p.kind = "item"
	p.item_id = id
	p.velocity = Vector3(randf_range(-2, 2), 6.0, randf_range(-2, 2))
	VFX.root(ctx).add_child(p)
	p.global_position = pos


func _ready() -> void:
	_world = get_tree().get_first_node_in_group("world")
	if kind == "coin":
		_model = _coin_model()
	else:
		var model_name: String = Catalog.ITEMS.get(item_id, {}).get("model", "")
		_model = MaterialLib.instance_model("res://assets/models/items/%s.glb" % model_name)
		if _model == null:
			_model = _fallback_item()
		_model.scale = Vector3.ONE * 0.9
		var l := OmniLight3D.new()
		l.light_color = Color(1.0, 0.85, 0.4)
		l.light_energy = 1.0
		l.omni_range = 3.0
		add_child(l)
	add_child(_model)


func _coin_model() -> Node3D:
	if not _coin_checked:
		_coin_checked = true
		var path := "res://assets/models/items/item_coin.glb"
		if ResourceLoader.exists(path):
			_coin_scene = load(path)
	if _coin_scene:
		var n := _coin_scene.instantiate() as Node3D
		MaterialLib.apply(n)
		n.scale = Vector3.ONE * 0.8
		return n
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.11
	cm.bottom_radius = 0.11
	cm.height = 0.035
	cm.radial_segments = 16
	mi.mesh = cm
	mi.rotation.x = PI / 2
	var m := MaterialLib.get_named("M_Brass").duplicate() as ShaderMaterial
	m.set_shader_parameter("albedo_color", Color(1.0, 0.82, 0.3))
	m.set_shader_parameter("emission_color", Color(1.0, 0.75, 0.2))
	m.set_shader_parameter("emission_energy", 0.4)
	mi.material_override = m
	var root := Node3D.new()
	root.add_child(mi)
	return root


func _fallback_item() -> Node3D:
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.16
	sm.height = 0.32
	mi.mesh = sm
	var col := {"scrap_gear": Color(0.7, 0.45, 0.25), "ember_essence": Color(1.0, 0.6, 0.2), "rune_shard": Color(0.65, 0.45, 1.0)}.get(item_id, Color.WHITE)
	mi.material_override = MaterialLib.get_glow(col, 2.0)
	var root := Node3D.new()
	root.add_child(mi)
	return root


func _physics_process(delta: float) -> void:
	_age += delta
	var player := get_tree().get_first_node_in_group("player") as Player
	if player and not player.dead:
		var to := player.global_position + Vector3.UP * 1.0 - global_position
		var d := to.length()
		# coins jump to you when close, and home in from further away after a few seconds
		var reach := 9.0 if kind == "coin" else 6.0
		if _age > 4.0 and kind == "coin":
			reach = 35.0
		if _age > 0.5 and (d < reach or _magnet):
			_magnet = true
			velocity = velocity.lerp(to.normalized() * clampf(22.0 - d, 8.0, 22.0), 1.0 - exp(-8.0 * delta))
			global_position += velocity * delta
			if d < 0.9:
				_collect(player)
				return
			_spin(delta)
			return
	if not _grounded:
		velocity.y -= 18.0 * delta
		global_position += velocity * delta
		var gy := _world.ground_y(global_position.x, global_position.z) if _world else 0.0
		if global_position.y < gy + 0.35:
			global_position.y = gy + 0.35
			if absf(velocity.y) > 2.0:
				velocity.y = -velocity.y * 0.4
				velocity.x *= 0.6
				velocity.z *= 0.6
			else:
				_grounded = true
				_base_y = global_position.y
	else:
		global_position.y = _base_y + sin(_age * 3.0) * 0.08
	_spin(delta)
	if _age > 90.0:
		queue_free()


func _spin(delta: float) -> void:
	if _model:
		_model.rotation.y += delta * 4.0


func _collect(player: Player) -> void:
	if kind == "coin":
		Game.add_gold(value)
		AudioManager.play_2d("coin_pickup", -6.0, randf_range(0.95, 1.15))
		VFX.sparkle(player, global_position, Color(1.0, 0.85, 0.3), 4, 0.2)
	else:
		Game.add_item(item_id, 1)
		AudioManager.play_2d("notify", -4.0, 1.2)
		Events.toast("+1 %s" % Catalog.display_name(item_id), "item")
	queue_free()
