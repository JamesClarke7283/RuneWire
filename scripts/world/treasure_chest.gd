class_name TreasureChest
extends Node3D
## A one-time treasure chest hidden somewhere in the valley, or a sealed Ley Vault that needs a Ley
## Key. Opening it swings the lid, sprays sparkles and pops out gold, materials, consumables and
## (usually) a weapon. Opened chests are remembered in the save (Game.opened_chests).

var chest_id: String = ""
var vault: bool = false
var opened: bool = false
var model: Node3D
var _lid: Node3D
var _light: OmniLight3D
var _sparkle: GPUParticles3D
var _t: float = 0.0
var _shake_t: float = 0.0


func _ready() -> void:
	add_to_group("chests")
	opened = Game.is_chest_opened(chest_id)
	var mname := "item_vault" if vault else "item_chest"
	model = MaterialLib.instance_model("res://assets/models/items/%s.glb" % mname)
	if model == null:
		model = _fallback()
	model.name = "Model"
	add_child(model)
	_lid = model.find_child("Lid", true, false) as Node3D
	var body := StaticBody3D.new()
	body.collision_layer = 1 | 32
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = Vector3(1.25, 0.95, 0.85) if vault else Vector3(1.05, 0.8, 0.75)
	cs.shape = bs
	cs.position.y = bs.size.y * 0.5
	body.add_child(cs)
	add_child(body)
	_light = OmniLight3D.new()
	_light.light_color = Color(0.35, 0.95, 0.88) if vault else Color(1.0, 0.82, 0.4)
	_light.light_energy = 1.3
	_light.omni_range = 4.5
	_light.position.y = 1.3
	_light.distance_fade_enabled = true
	_light.distance_fade_begin = 55.0
	_light.distance_fade_length = 15.0
	add_child(_light)
	_sparkle = GPUParticles3D.new()
	_sparkle.amount = 8
	_sparkle.lifetime = 1.6
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(0.6, 0.3, 0.45)
	pm.gravity = Vector3(0, 0.9, 0)
	pm.initial_velocity_max = 0.2
	pm.scale_min = 0.1
	pm.scale_max = 0.2
	VFX._curves()
	pm.scale_curve = VFX._scale_curve
	pm.color = _light.light_color
	_sparkle.process_material = pm
	_sparkle.draw_pass_1 = VFX._quad
	_sparkle.material_override = VFX.additive_mat("vfx_star")
	_sparkle.position.y = 0.9
	_sparkle.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_sparkle)
	if opened:
		_set_open_pose()
	Props.set_visibility_range(model, 110.0)
	Props.set_visibility_range(_sparkle, 75.0)


func _fallback() -> Node3D:
	var root := Node3D.new()
	var w := 1.2 if vault else 1.0
	var d := 0.8 if vault else 0.7
	var h := 0.95 if vault else 0.8
	var body := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(w, h * 0.62, d)
	body.mesh = bm
	body.position.y = h * 0.31
	body.material_override = MaterialLib.get_named("M_Stone" if vault else "M_WoodPlanks")
	root.add_child(body)
	for sx in [-1.0, 1.0]:
		var band := MeshInstance3D.new()
		var bb := BoxMesh.new()
		bb.size = Vector3(0.08, h * 0.64, d + 0.04)
		band.mesh = bb
		band.position = Vector3(sx * w * 0.32, h * 0.31, 0)
		band.material_override = MaterialLib.get_named("M_Brass")
		root.add_child(band)
	var lid := Node3D.new()
	lid.name = "Lid"
	lid.position = Vector3(0, h * 0.62, -d * 0.5)
	root.add_child(lid)
	var lm := MeshInstance3D.new()
	var lb := BoxMesh.new()
	lb.size = Vector3(w + 0.04, h * 0.38, d + 0.04)
	lm.mesh = lb
	lm.position = Vector3(0, h * 0.19, d * 0.5)
	lm.material_override = MaterialLib.get_named("M_Stone" if vault else "M_WoodDark")
	lid.add_child(lm)
	var lock := MeshInstance3D.new()
	var lk := BoxMesh.new()
	lk.size = Vector3(0.18, 0.22, 0.06)
	lock.mesh = lk
	lock.position = Vector3(0, h * 0.55, d * 0.5 + 0.03)
	lock.material_override = MaterialLib.get_glow(Color(0.35, 0.95, 0.88), 2.5) if vault else MaterialLib.get_named("M_Brass")
	root.add_child(lock)
	return root


func get_interact_text() -> String:
	if opened:
		return ""
	if vault:
		return "[E] Unlock the Ley Vault  (Ley Keys: %d)" % Game.item_count("ley_key")
	return "[E] Open treasure chest"


func interact(_player: Player) -> void:
	if opened:
		return
	if vault:
		if not Game.remove_item("ley_key", 1):
			Events.toast("This Ley Vault is sealed. You need a Ley Key: Champions carry them, and the Workbench can craft one.", "warn")
			AudioManager.play("chest_locked", global_position + Vector3.UP * 0.5, 0.0)
			_shake_t = 0.4
			return
	open()


func open() -> void:
	if opened:
		return
	opened = true
	Game.mark_chest_opened(chest_id, vault)
	AudioManager.play("vault_open" if vault else "chest_open", global_position + Vector3.UP * 0.6, 2.0, 1.0, 0.03, 12.0)
	if _lid:
		var tw := create_tween()
		tw.tween_property(_lid, "rotation:x", deg_to_rad(-105.0), 0.55).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	var top := global_position + Vector3.UP * 0.9
	VFX.flash_light(self, top, _light.light_color, 5.0, 8.0, 0.8)
	VFX.sparkle(self, top, _light.light_color, 26, 0.4)
	VFX.burst(self, top, Color(1.0, 0.85, 0.35), 18, 5.0, 0.14, 0.7, -9.0, "spark", 50.0)
	_sparkle.emitting = false
	var tw2 := create_tween()
	tw2.tween_property(_light, "light_energy", 0.0, 1.5)
	get_tree().create_timer(0.35).timeout.connect(_spill_loot)
	var total := get_tree().get_nodes_in_group("chests").size()
	Events.toast("%s  (%d / %d treasures found)" % ["Ley Vault unsealed!" if vault else "Treasure chest opened!", int(Game.stats.get("chests", 0)), total], "unlock")
	Events.chest_opened.emit(chest_id, vault)
	SaveSystem.request_autosave()


## The world is built before a save is loaded: match the chest to Game.opened_chests on game start.
func sync_state() -> void:
	var want := Game.is_chest_opened(chest_id)
	if want and not opened:
		opened = true
		_set_open_pose()
	elif not want and opened:
		opened = false
		if _lid:
			_lid.rotation.x = 0.0
		_light.light_energy = 1.3
		_sparkle.emitting = true


func _set_open_pose() -> void:
	if _lid:
		_lid.rotation.x = deg_to_rad(-105.0)
	_light.light_energy = 0.0
	_sparkle.emitting = false


## Loot: gold, materials, a consumable or two, often a weapon (always a Rare+ one from a vault), and a
## chance of a pouch or an unknown schematic (vaults always hold a schematic while any are unknown).
func _spill_loot() -> void:
	var pos := global_position + Vector3.UP * 1.0
	var lvl := float(Game.level)
	var p := get_tree().get_first_node_in_group("player") as Player
	var luck := Game.loot_luck() + (0.6 if p and p.has_buff("luck") else 0.0)
	var gold := randi_range(140, 220) if vault else int(randi_range(25, 55) * (1.0 + lvl * 0.08))
	Pickup.drop_coins(self, pos, int(gold * Game.gold_mult()))
	var raw := ["scrap_gear", "ember_essence", "rune_shard", "shade_silk", "ley_crystal", "copper_ore", "iron_ore",
		"glowcap", "sunpetal", "reed_fiber"]
	var fine := ["copper_ingot", "iron_ingot", "brass_ingot", "spun_cloth", "rune_ink", "spring_coil", "power_cell",
		"focus_gem", "steel_plate", "arcane_thread"]
	raw.shuffle()
	fine.shuffle()
	var n_mats := randi_range(4, 6) if vault else randi_range(2, 3)
	for i in n_mats:
		var id: String = raw[i % raw.size()] if (i % 2 == 0 or not vault) else fine[i % fine.size()]
		Pickup.drop_item(self, pos, id, 2 if vault and i % 3 == 0 else 1)
	if vault:
		Pickup.drop_item(self, pos, "clockwork_core" if randf() < 0.5 else "focus_gem")
	elif randf() < 0.35:
		Pickup.drop_item(self, pos, fine[0])
	if randf() < (1.0 if vault else 0.6):
		Pickup.drop_item(self, pos, ["health_tonic", "mana_draught", "spark_bomb", "swift_elixir", "iron_tonic", "treasure_map",
			"frost_bomb", "regen_salve", "skyleap_draught", "greater_health_tonic"][randi() % 10])
	var wl := Catalog.drop_level(Game.level + (3 if vault else 0))
	if vault:
		Pickup.drop_weapon(self, pos, Catalog.roll_weapon(1.8 + luck, 2, "", "", wl))
		if randf() < 0.3:
			Pickup.drop_weapon(self, pos, Catalog.roll_weapon(1.0 + luck, 1, "", "", wl))
	elif randf() < 0.7:
		Pickup.drop_weapon(self, pos, Catalog.roll_weapon(0.7 + luck, 0, "", "", wl))
	# schematics and pouches
	if vault or randf() < 0.25:
		var sch := Game.random_unknown_schematic()
		if sch != "":
			Pickup.drop_item(self, pos, Catalog.schematic_id(sch))
	if vault and randf() < 0.5:
		Pickup.drop_item(self, pos, ["pouch_brass", "pouch_rune", "pouch_alchemist", "pouch_prospector", "pouch_scavenger"][randi() % 5])
	elif not vault and randf() < 0.15:
		Pickup.drop_item(self, pos, ["pouch_cloth", "pouch_leather", "pouch_leather", "pouch_brass"][randi() % 4])


func _process(delta: float) -> void:
	_t += delta
	if not opened and _light:
		_light.light_energy = 1.1 + sin(_t * 2.2) * 0.35
		# only sparkle when someone is near enough to see it
		if fmod(_t, 0.5) < delta:
			var cam := get_viewport().get_camera_3d()
			_sparkle.emitting = cam != null and cam.global_position.distance_to(global_position) < 70.0
	if _shake_t > 0.0 and model:
		_shake_t -= delta
		model.rotation.z = sin(_t * 60.0) * 0.04 * (_shake_t / 0.4)
		if _shake_t <= 0.0:
			model.rotation.z = 0.0
