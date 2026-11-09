class_name Pickup
extends Node3D
## Bouncy, spinning loot: gold coins, items (materials, consumables, pouches, keys, schematics) and
## weapons. They pop out of defeated foes and treasure chests. Coins and items get pulled into the player
## when close (if the pack has room); weapons stand in a rarity-coloured beam of light: walk over one to
## stash it, or look at it and press E to wield it right away (swapping out the weapon in your hand).

var kind: String = "coin"      # coin | item | weapon
var value: int = 1
var item_id: String = ""
var weapon: Dictionary = {}
var velocity: Vector3 = Vector3.ZERO
var _age: float = 0.0
var _model: Node3D
var _grounded: bool = false
var _base_y: float = 0.0
var _magnet: bool = false
var _world: World
var _full_warned: float = 0.0
var _body: StaticBody3D

static var _coin_scene: PackedScene = null
static var _coin_checked: bool = false

const ITEM_COLORS := {
	"scrap_gear": Color(0.7, 0.45, 0.25), "ember_essence": Color(1.0, 0.6, 0.2), "rune_shard": Color(0.65, 0.45, 1.0),
	"shade_silk": Color(0.45, 0.3, 0.7), "ley_crystal": Color(0.35, 0.95, 0.88), "clockwork_core": Color(1.0, 0.6, 0.25),
	"ley_key": Color(1.0, 0.85, 0.35), "health_tonic": Color(0.95, 0.3, 0.3), "mana_draught": Color(0.3, 0.55, 1.0),
	"spark_bomb": Color(1.0, 0.55, 0.2), "swift_elixir": Color(0.3, 0.9, 0.75), "iron_tonic": Color(0.95, 0.7, 0.3),
	"repair_kit": Color(0.6, 0.45, 0.3), "treasure_map": Color(0.95, 0.85, 0.6),
	"copper_ore": Color(0.95, 0.55, 0.3), "iron_ore": Color(0.6, 0.42, 0.36), "reed_fiber": Color(0.8, 0.82, 0.4),
	"glowcap": Color(0.3, 0.85, 1.0), "sunpetal": Color(1.0, 0.82, 0.25), "focus_gem": Color(0.45, 0.95, 0.9),
	"rune_ink": Color(0.65, 0.4, 1.0), "power_cell": Color(0.35, 0.95, 0.85), "frost_bomb": Color(0.6, 0.9, 1.0),
	"shock_jar": Color(0.45, 0.9, 1.0),
}


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


static func drop_item(ctx: Node, pos: Vector3, id: String, count: int = 1) -> void:
	for i in maxi(count, 1):
		var p := Pickup.new()
		p.kind = "item"
		p.item_id = id
		p.velocity = Vector3(randf_range(-2, 2), 6.0, randf_range(-2, 2))
		VFX.root(ctx).add_child(p)
		p.global_position = pos


static func drop_weapon(ctx: Node, pos: Vector3, w: Dictionary) -> Pickup:
	var p := Pickup.new()
	p.kind = "weapon"
	p.weapon = w
	p.velocity = Vector3(randf_range(-1.5, 1.5), 7.0, randf_range(-1.5, 1.5))
	VFX.root(ctx).add_child(p)
	p.global_position = pos
	if int(w.get("rarity", 0)) >= 2:
		AudioManager.play("pickup_rare", pos, -2.0, 1.0, 0.0, 14.0)
	return p


func _ready() -> void:
	add_to_group("pickups")
	_world = get_tree().get_first_node_in_group("world")
	match kind:
		"coin":
			_model = _coin_model()
		"weapon":
			_model = _weapon_model()
			_body = StaticBody3D.new()
			_body.collision_layer = 32
			_body.collision_mask = 0
			var cs := CollisionShape3D.new()
			var sph := SphereShape3D.new()
			sph.radius = 0.75
			cs.shape = sph
			_body.add_child(cs)
			add_child(_body)
		_:
			var model_name: String = Catalog.stack_def(item_id).get("model", "")
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


## The weapon's first-person model without the glove, enlarged, plus a rarity beam and light.
func _weapon_model() -> Node3D:
	var root := Node3D.new()
	var bd := Catalog.weapon_base(str(weapon.get("base", "")))
	var col := Catalog.rarity_color(int(weapon.get("rarity", 0)))
	var model := MaterialLib.instance_model("res://assets/models/weapons/%s.glb" % bd.get("model", ""))
	if model:
		var g := model.find_child("Glove", true, false)
		if g:
			g.queue_free()
		var crystal: Color = bd.get("crystal", Color.TRANSPARENT)
		for mi in model.find_children("*", "MeshInstance3D", true, false):
			var m := mi as MeshInstance3D
			for i in m.mesh.get_surface_count():
				var mat := m.get_surface_override_material(i)
				if mat and mat.resource_name.begins_with("RarityGlow"):
					m.set_surface_override_material(i, MaterialLib.get_glow(col, 3.0))
				elif mat and mat.resource_name.begins_with("M_Crystal") and crystal.a > 0.0:
					m.set_surface_override_material(i, MaterialLib.get_named("M_Crystal__" + crystal.to_html(false)))
		model.scale = Vector3.ONE * 1.7
		model.rotation_degrees = Vector3(0, 90, 18)
		root.add_child(model)
	else:
		var mi2 := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(0.18, 0.22, 0.7)
		mi2.mesh = bm
		mi2.material_override = MaterialLib.get_named("M_Brass")
		root.add_child(mi2)
	var beam := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.02
	cm.bottom_radius = 0.18
	cm.height = 3.2
	cm.radial_segments = 10
	cm.rings = 1
	beam.mesh = cm
	var bmat := VFX.glow_alpha_mat(Color(col, 0.35))
	beam.material_override = bmat
	beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	beam.position.y = 1.2
	beam.name = "Beam"
	add_child(beam)
	var l := OmniLight3D.new()
	l.light_color = col
	l.light_energy = 1.4 + 0.4 * float(weapon.get("rarity", 0))
	l.omni_range = 4.0
	add_child(l)
	var lab := Label3D.new()
	lab.text = "%s\n%s %s" % [Catalog.weapon_name(weapon), Catalog.RARITY_NAMES[clampi(int(weapon.get("rarity", 0)), 0, 4)],
		Catalog.SCHOOL_NAMES.get(Catalog.weapon_school(str(weapon.get("base", ""))), "")]
	lab.font_size = 34
	lab.outline_size = 10
	lab.modulate = col
	lab.outline_modulate = Color(0.08, 0.05, 0.1)
	lab.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lab.pixel_size = 0.005
	lab.position.y = 0.75
	var f := UIStyle.display_font()
	if f:
		lab.font = f
	add_child(lab)
	return root


func _fallback_item() -> Node3D:
	var mi := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.16
	sm.height = 0.32
	mi.mesh = sm
	var col: Color = ITEM_COLORS.get(item_id, Color.WHITE)
	mi.material_override = MaterialLib.get_glow(col, 2.0)
	var root := Node3D.new()
	root.add_child(mi)
	return root


func _physics_process(delta: float) -> void:
	_age += delta
	_full_warned -= delta
	var player := get_tree().get_first_node_in_group("player") as Player
	if player and not player.dead:
		var to := player.global_position + Vector3.UP * 1.0 - global_position
		var d := to.length()
		# coins jump to you when close, and home in from further away after a few seconds
		var reach := 9.0 if kind == "coin" else 6.0
		if _age > 4.0 and kind == "coin":
			reach = 35.0
		if player.has_method("magnet_mult"):
			reach *= player.magnet_mult()
		if kind == "weapon":
			reach = 2.0
			if d < reach and not Game.has_weapon_room():
				if _full_warned <= 0.0:
					_full_warned = 6.0
					Events.toast("Pack full! Look at %s and press E to swap it for the weapon in your hand" % Catalog.weapon_name(weapon), "warn")
				reach = 0.0
		elif kind == "item" and d < reach and Game.room_for(item_id, 1) <= 0:
			if _full_warned <= 0.0 and d < 3.0:
				_full_warned = 8.0
				Events.toast("Pack full (%d/%d)! Equip a bigger pouch, sell or craft to make room." % [Game.pack_used(), Game.pack_capacity()], "warn")
			reach = 0.0
			_magnet = false
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
		var gy := _floor_y()
		var lift := 0.35 if kind != "weapon" else 0.7
		if global_position.y < gy + lift:
			global_position.y = gy + lift
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
	if _age > (300.0 if kind == "weapon" else 90.0):
		queue_free()


## Height of whatever world surface is below: terrain, a chest lid, or a floating island's top
## (loot from the sky vaults must not fall through the island).
func _floor_y() -> float:
	var terrain_y := _world.ground_y(global_position.x, global_position.z) if _world else 0.0
	var from := global_position + Vector3.UP * 0.3
	var q := PhysicsRayQueryParameters3D.create(from, Vector3(from.x, terrain_y - 1.0, from.z), 1)
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	return maxf(float(hit["position"].y), terrain_y) if hit else terrain_y


func _spin(delta: float) -> void:
	if _model:
		_model.rotation.y += delta * (1.6 if kind == "weapon" else 4.0)


func _collect(player: Player) -> void:
	match kind:
		"coin":
			Game.add_gold(value)
			AudioManager.play_2d("coin_pickup", -6.0, randf_range(0.95, 1.15))
			VFX.sparkle(player, global_position, Color(1.0, 0.85, 0.3), 4, 0.2)
		"weapon":
			if Game.add_weapon(weapon, true) == 0:
				_magnet = false
				return
			var r := int(weapon.get("rarity", 0))
			AudioManager.play_2d("pickup_weapon" if r < 2 else "pickup_rare", -3.0)
			VFX.sparkle(player, global_position, Catalog.rarity_color(r), 14, 0.3)
		_:
			if Game.add_item(item_id, 1) <= 0:
				_magnet = false
				return
			if Catalog.is_pouch(item_id):
				AudioManager.play_2d("pouch_equip", -4.0)
				Events.toast("+1 %s  ·  equip it in a pouch slot [I]" % Catalog.display_name(item_id), "rarity_%d" % int(Catalog.pouch_def(item_id).get("rarity", 0)))
			elif not Catalog.is_schematic(item_id):
				AudioManager.play_2d("notify", -4.0, 1.2)
				Events.toast("+1 %s" % Catalog.display_name(item_id), "item")
	queue_free()


# ------------------------------------------------------------------ aim + E on a weapon
func get_interact_text() -> String:
	if kind != "weapon":
		return ""
	var p := get_tree().get_first_node_in_group("player") as Player
	var s := Catalog.weapon_stats(weapon)
	var nm := Catalog.weapon_name(weapon)
	var line := "[E] Wield %s  (%s %s)" % [nm, Catalog.RARITY_NAMES[int(weapon.get("rarity", 0))], Catalog.SCHOOL_NAMES.get(str(s.get("school", "")), "")]
	var held := Game.get_weapon(p.current_uid) if p else {}
	var dps := Catalog.weapon_dps(s) * Game.school_mult(str(s.get("school", "tech")))
	if not held.is_empty():
		var hs := Catalog.weapon_stats(held)
		var hdps := Catalog.weapon_dps(hs) * Game.school_mult(str(hs.get("school", "tech")))
		var pct := int(round((dps - hdps) / maxf(hdps, 0.01) * 100.0))
		line += "\n%d DPS (%s%d%% vs %s)" % [int(round(dps)), "+" if pct >= 0 else "", pct, Catalog.display_name(str(held["base"]))]
		line += "  ·  %s" % ("yours goes to your pack" if Game.pack_free() > 0 else "swaps: yours is dropped here")
	else:
		line += "\n%d DPS" % int(round(dps))
	return line


## Wield it in the active weapon slot. The weapon in hand goes to the pack, or (pack full) is dropped
## right here - a straight swap.
func interact(player: Player) -> void:
	if kind != "weapon":
		return
	var slot := player.slot if player.slot < Game.WEAPON_SLOTS else player.last_weapon_slot()
	var old := Game.loadout_weapon(slot)
	var dropped := false
	if not old.is_empty() and Game.pack_free() <= 0:
		if bool(old.get("fav", false)):
			Events.toast("Your %s is a favourite: make room in your pack instead" % Catalog.weapon_name(old), "warn")
			return
		Game.remove_weapon(int(old["uid"]))
		var keep := old.duplicate(true)
		keep["new"] = false
		Pickup.drop_weapon(player, global_position + Vector3.UP * 0.4, keep)
		dropped = true
	var uid := Game.add_weapon(weapon, false)
	if uid == 0:
		return
	Game.equip_weapon(uid, slot)
	player.select_slot(slot, true)
	var r := int(weapon.get("rarity", 0))
	AudioManager.play_2d("pickup_weapon" if r < 2 else "pickup_rare", -3.0)
	VFX.sparkle(player, global_position, Catalog.rarity_color(r), 14, 0.3)
	Events.toast("Wielding %s%s" % [Catalog.weapon_name(Game.get_weapon(uid)), "  ·  dropped your old weapon" if dropped else ""], "rarity_%d" % r)
	queue_free()
