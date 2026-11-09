class_name HarvestNode
extends Node3D
## A gatherable resource (see Catalog.HARVEST). Press E to gather; it refills after a few minutes.
##   crystal      teal Ley Crystal cluster (its "Crystals" shrink away and regrow)
##   scrap        a Gearworks scrap heap to rummage through (attach as a child of the scrap pile prop)
##   ore_copper   copper vein · ore_iron iron vein (mine; the ore chunks "Harvest" shrink away)
##   glowcap      glowing mushrooms · sunpetal golden flowers · reeds lake-shore reeds
## Yields go into the pack (anything that does not fit drops at your feet). The Prospector's Satchel
## adds +1, and the Forager talent has a chance of +1 more.

const BONUS := {
	"crystal": {"item": "rune_shard", "chance": 0.12},
	"ore_copper": {"item": "ley_crystal", "chance": 0.1},
	"ore_iron": {"item": "scrap_gear", "chance": 0.2},
}

var kind: String = "crystal"
var regrow_time: float = 240.0
var cooldown: float = 0.0
var model: Node3D
var _crystals: Node3D        # the part that shrinks away ("Crystals" or "Harvest")
var _light: OmniLight3D
var _t: float = 0.0


func def() -> Dictionary:
	return Catalog.HARVEST.get(kind, Catalog.HARVEST["crystal"])


func _ready() -> void:
	add_to_group("harvest_nodes")
	_t = randf() * 10.0
	var d := def()
	regrow_time = float(d.get("regrow", 240.0))
	if kind == "scrap":
		return
	var mname := str(d.get("model", ""))
	model = MaterialLib.instance_model("res://assets/models/env/%s.glb" % mname) if mname != "" else null
	if model == null:
		model = _fallback_crystals() if kind == "crystal" else _fallback_node()
	model.name = "Model"
	model.rotation.y = randf() * TAU
	add_child(model)
	_crystals = model.find_child("Crystals", true, false) as Node3D
	if _crystals == null:
		_crystals = model.find_child("Harvest", true, false) as Node3D
	Props.set_visibility_range(model, 110.0 if kind in ["crystal", "glowcap"] else 90.0)
	if model.find_children("*", "StaticBody3D", true, false).is_empty():
		var body := StaticBody3D.new()
		body.collision_layer = 1 | 32
		var cs := CollisionShape3D.new()
		var cyl := CylinderShape3D.new()
		cyl.radius = float(d.get("radius", 0.65))
		cyl.height = float(d.get("height", 1.5))
		cs.shape = cyl
		cs.position.y = cyl.height * 0.5
		body.add_child(cs)
		add_child(body)
	if d.has("light"):
		_light = OmniLight3D.new()
		_light.light_color = d["light"]
		_light.light_energy = 1.0
		_light.omni_range = 4.0
		_light.position.y = 1.0 if kind == "crystal" else 0.6
		_light.distance_fade_enabled = true
		_light.distance_fade_begin = 50.0
		_light.distance_fade_length = 15.0
		add_child(_light)


func _fallback_crystals() -> Node3D:
	var root := Node3D.new()
	var rock := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.7
	sm.height = 0.7
	rock.mesh = sm
	rock.position.y = 0.2
	rock.scale = Vector3(1.0, 0.7, 1.0)
	rock.material_override = MaterialLib.get_named("M_StoneRough")
	root.add_child(rock)
	# all six crystals in one MultiMesh: a single draw call
	var crystals := MultiMeshInstance3D.new()
	crystals.name = "Crystals"
	crystals.position.y = 0.4
	var pm := PrismMesh.new()
	pm.size = Vector3(0.22, 1.0, 0.22)
	pm.material = MaterialLib.get_named("M_Crystal")
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = pm
	mm.instance_count = 6
	for i in 6:
		var h := randf_range(0.6, 1.2)
		var a := i * TAU / 6.0 + randf() * 0.4
		var b := Basis.from_euler(Vector3(randf_range(-0.4, 0.4), randf() * TAU, randf_range(-0.4, 0.4))) * Basis.from_scale(Vector3(1, h, 1))
		mm.set_instance_transform(i, Transform3D(b, Vector3(cos(a) * 0.25, h * 0.5, sin(a) * 0.25)))
	crystals.multimesh = mm
	root.add_child(crystals)
	return root


## Procedural stand-in until the Blender node models exist: a rock / stump / clump base with the
## gatherable bits in one MultiMesh named "Harvest".
func _fallback_node() -> Node3D:
	var root := Node3D.new()
	var col: Color = def().get("color", Color(0.8, 0.8, 0.4))
	var base := MeshInstance3D.new()
	var harvest := MultiMeshInstance3D.new()
	harvest.name = "Harvest"
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var count := 7
	match kind:
		"ore_copper", "ore_iron":
			var sm := SphereMesh.new()
			sm.radius = 0.75
			sm.height = 1.2
			base.mesh = sm
			base.position.y = 0.35
			base.scale = Vector3(1.0, 0.75, 0.9)
			base.material_override = MaterialLib.get_named("M_StoneRough")
			var bm := BoxMesh.new()
			bm.size = Vector3(0.22, 0.18, 0.2)
			bm.material = MaterialLib.get_named("M_Copper" if kind == "ore_copper" else "M_Rust")
			mm.mesh = bm
			harvest.position.y = 0.75
		"glowcap":
			var cm := CylinderMesh.new()
			cm.top_radius = 0.45
			cm.bottom_radius = 0.55
			cm.height = 0.45
			base.mesh = cm
			base.position.y = 0.22
			base.material_override = MaterialLib.get_named("M_Bark")
			var cap := SphereMesh.new()
			cap.radius = 0.16
			cap.height = 0.18
			cap.material = MaterialLib.get_glow(col, 2.0)
			mm.mesh = cap
			harvest.position.y = 0.5
		"sunpetal":
			var sm2 := SphereMesh.new()
			sm2.radius = 0.4
			sm2.height = 0.3
			base.mesh = sm2
			base.position.y = 0.1
			base.material_override = MaterialLib.get_flat(Color(0.35, 0.6, 0.25))
			var fm := SphereMesh.new()
			fm.radius = 0.12
			fm.height = 0.08
			fm.material = MaterialLib.get_glow(col, 1.2)
			mm.mesh = fm
			harvest.position.y = 0.45
		_:
			var sm3 := CylinderMesh.new()
			sm3.top_radius = 0.45
			sm3.bottom_radius = 0.55
			sm3.height = 0.12
			base.mesh = sm3
			base.position.y = 0.06
			base.material_override = MaterialLib.get_flat(Color(0.35, 0.28, 0.2))
			var rm := CylinderMesh.new()
			rm.top_radius = 0.02
			rm.bottom_radius = 0.035
			rm.height = 1.5
			rm.material = MaterialLib.get_flat(col)
			mm.mesh = rm
			count = 12
			harvest.position.y = 0.75
	mm.instance_count = count
	for i in count:
		var a := i * TAU / count + randf() * 0.5
		var r := randf_range(0.15, 0.4)
		var b := Basis.from_euler(Vector3(randf_range(-0.3, 0.3), randf() * TAU, randf_range(-0.3, 0.3)))
		mm.set_instance_transform(i, Transform3D(b, Vector3(cos(a) * r, randf_range(-0.1, 0.15), sin(a) * r)))
	harvest.multimesh = mm
	root.add_child(base)
	root.add_child(harvest)
	return root


func available() -> bool:
	return cooldown <= 0.0


func get_interact_text() -> String:
	var d := def()
	var item := str(d.get("item", ""))
	var c: Array = d.get("count", [1, 2])
	if not available():
		match kind:
			"crystal":
				return "The crystals are regrowing (%ds)" % int(ceil(cooldown))
			"scrap":
				return "Picked clean for now (%ds)" % int(ceil(cooldown))
		return "%s: gathered, regrows in %ds" % [d.get("name", kind), int(ceil(cooldown))]
	if kind == "crystal":
		return "[E] Harvest Ley Crystals"
	if kind == "scrap":
		return "[E] Scavenge the scrap heap"
	var room := "" if Game.room_for(item, 1) > 0 else "  ·  pack full!"
	return "[E] %s the %s  (+%d-%d %s)%s" % [d.get("verb", "Gather"), d.get("name", kind), int(c[0]), int(c[1]), Catalog.display_name(item), room]


func interact(player: Player) -> void:
	if not available():
		AudioManager.play_ui("ui_error", -10.0)
		return
	cooldown = regrow_time
	var pos := global_position + Vector3.UP * 1.0
	var d := def()
	if kind == "scrap":
		var gears := randi_range(1, 3) + (1 if randf() < Game.scrap_chance() else 0)
		Game.give_item("scrap_gear", gears)
		var msg := "+%d Scrap Gear" % gears
		if randf() < 0.15:
			Game.give_item("clockwork_core", 1)
			msg += ", +1 Clockwork Core!"
		elif randf() < 0.2:
			Game.give_item("spark_bomb", 1)
			msg += ", +1 Spark Bomb"
		elif randf() < 0.15:
			Game.give_item("spring_coil", 1)
			msg += ", +1 Spring Coil"
		Game.add_stat("scavenged")
		Events.scavenged.emit(1)
		Events.toast(msg, "item")
		AudioManager.play("scavenge", pos, 0.0)
		VFX.puffs(self, pos, Color(0.55, 0.5, 0.45), 6, 0.6, 0.8, 1.5)
		VFX.burst(self, pos, Color(1.0, 0.8, 0.45), 10, 4.0, 0.1, 0.5, -12.0, "spark")
		player.viewmodel.kick(0.0, -8.0)
		return
	var item := str(d.get("item", "ley_crystal"))
	var c: Array = d.get("count", [2, 3])
	var n := randi_range(int(c[0]), int(c[1]))
	if Game.has_pouch_perk("prospector"):
		n += 1
	if randf() < Game.forage_chance():
		n += 1
	Game.give_item(item, n)
	var msg2 := "+%d %s" % [n, Catalog.display_name(item)]
	var bonus: Dictionary = BONUS.get(kind, {})
	if not bonus.is_empty() and randf() < float(bonus["chance"]):
		Game.give_item(str(bonus["item"]), 1)
		msg2 += ", +1 %s" % Catalog.display_name(str(bonus["item"]))
	match kind:
		"crystal":
			Game.add_stat("harvested", n)
		"ore_copper", "ore_iron":
			Game.add_stat("mined", n)
		_:
			Game.add_stat("gathered", n)
	Events.resource_harvested.emit(item, n)
	Game.add_xp(3 + 2 * n)
	Events.toast(msg2, "item")
	AudioManager.play(str(d.get("sfx", "crystal_harvest")), pos, 0.0)
	var fx_col: Color = d.get("light", d.get("color", Color(0.35, 0.95, 0.88)))
	VFX.sparkle(self, pos, fx_col, 16, 0.3)
	if kind in ["ore_copper", "ore_iron"]:
		VFX.burst(self, pos, fx_col.lightened(0.2), 14, 5.0, 0.12, 0.5, -12.0, "spark")
		VFX.puffs(self, pos - Vector3.UP * 0.4, Color(0.6, 0.55, 0.5), 5, 0.5, 0.7, 1.2)
	else:
		VFX.burst(self, pos, fx_col.lightened(0.3), 12, 4.0, 0.12, 0.6, -10.0, "spark")
	if _crystals:
		var tw := create_tween()
		tw.tween_property(_crystals, "scale", Vector3.ONE * 0.05, 0.4).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
	if _light:
		create_tween().tween_property(_light, "light_energy", 0.0, 0.5)
	player.viewmodel.kick(0.0, -8.0)


func _process(delta: float) -> void:
	_t += delta
	if cooldown > 0.0:
		cooldown -= delta
		if cooldown <= 0.0:
			if _crystals:
				var tw := create_tween()
				tw.tween_property(_crystals, "scale", Vector3.ONE, 1.2).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)
			if _light:
				create_tween().tween_property(_light, "light_energy", 1.0, 1.0)
	elif _light:
		_light.light_energy = 0.9 + sin(_t * 1.7) * 0.25
