extends Node
## Static game data: build parts, tools, spells, weapons, consumables, upgrades, items and enemies.
## Sizes are Godot metres (X width, Y height, Z depth); a part's front faces +Z.

const MODEL_DIR := "res://assets/models/%s/%s.glb"
const PART_ICON := "res://assets/icons/parts/part_%s.png"
const ITEM_ICON := "res://assets/icons/items/%s.png"
const UI_ICON := "res://assets/textures/ui/%s.png"

const PART_CATEGORIES := ["structure", "mechanics", "arcana", "defense"]
const CATEGORY_NAMES := {
	"structure": "Structure",
	"mechanics": "Mechanics",
	"arcana": "Arcana",
	"defense": "Defense",
}

# shape: {type: box|cylinder, size: Vector3 (box) | radius/height/axis (cylinder), offset: Vector3}
const PARTS := {
	"plank": {
		"name": "Wooden Plank", "category": "structure", "price": 6, "mass": 18.0, "hp": 60.0,
		"desc": "A sturdy double-board plank. The backbone of every questionable invention.",
		"shape": {"type": "box", "size": Vector3(2.0, 0.12, 0.5)}, "material": "wood"},
	"crate": {
		"name": "Wooden Crate", "category": "structure", "price": 10, "mass": 35.0, "hp": 90.0,
		"desc": "A brass-cornered crate. Stack it, weld it, sit on it.",
		"shape": {"type": "box", "size": Vector3(1.0, 1.0, 1.0)}, "material": "wood"},
	"beam": {
		"name": "Steel Girder", "category": "structure", "price": 16, "mass": 60.0, "hp": 200.0,
		"desc": "A three-metre riveted I-beam. Great for frames, bridges and long arms.",
		"shape": {"type": "box", "size": Vector3(3.0, 0.3, 0.3)}, "material": "metal"},
	"plate": {
		"name": "Riveted Plate", "category": "structure", "price": 18, "mass": 45.0, "hp": 160.0,
		"desc": "A 2 x 2 m steel plate. Floors, walls, armour.",
		"shape": {"type": "box", "size": Vector3(2.0, 0.08, 2.0)}, "material": "metal"},
	"platform": {
		"name": "Deck Platform", "category": "structure", "price": 40, "mass": 120.0, "hp": 300.0,
		"desc": "A big 4 x 4 m plank deck with a brass trim. The perfect chassis.",
		"shape": {"type": "box", "size": Vector3(4.0, 0.2, 4.0)}, "material": "wood"},
	"glass": {
		"name": "Glass Pane", "category": "structure", "price": 12, "mass": 20.0, "hp": 30.0,
		"desc": "A brass-framed window. Fragile, but very stylish.",
		"shape": {"type": "box", "size": Vector3(2.0, 2.0, 0.08)}, "material": "glass"},
	"stone_block": {
		"name": "Rune Block", "category": "structure", "price": 8, "mass": 160.0, "hp": 260.0,
		"desc": "A heavy carved stone block. Ballast, walls and counterweights.",
		"shape": {"type": "box", "size": Vector3(1.0, 1.0, 1.0)}, "material": "stone"},
	"barrel": {
		"name": "Volatile Mana Barrel", "category": "structure", "price": 14, "mass": 30.0, "hp": 30.0,
		"desc": "Leaky ley-juice in a barrel. Explodes when damaged. Handle with mittens.",
		"shape": {"type": "cylinder", "radius": 0.35, "height": 1.0, "axis": "y"},
		"device": "explosive", "material": "wood"},
	"wheel": {
		"name": "Cog Wheel", "category": "mechanics", "price": 25, "mass": 20.0, "hp": 120.0,
		"desc": "A chunky treaded wheel. Weld at least three to a seat-driven frame to make a vehicle.",
		"shape": {"type": "cylinder", "radius": 0.45, "height": 0.3, "axis": "x"},
		"device": "wheel", "radius": 0.45, "material": "rubber"},
	"big_wheel": {
		"name": "Brute Wheel", "category": "mechanics", "price": 60, "mass": 45.0, "hp": 220.0,
		"desc": "A huge off-road wheel for climbing hills and crushing doubts.",
		"shape": {"type": "cylinder", "radius": 0.8, "height": 0.45, "axis": "x"},
		"device": "wheel", "radius": 0.8, "unlock": "q_wheels", "material": "rubber"},
	"thruster": {
		"name": "Steam Thruster", "category": "mechanics", "price": 45, "mass": 25.0, "hp": 100.0,
		"desc": "Pushes its contraption toward the way it faces. Bound to Forward by default.",
		"shape": {"type": "cylinder", "radius": 0.22, "height": 0.9, "axis": "z"},
		"device": "thruster", "force": 2600.0, "unlock": "q_scrap", "material": "metal"},
	"rotor": {
		"name": "Lift Rotor", "category": "mechanics", "price": 90, "mass": 30.0, "hp": 120.0,
		"desc": "A spinning rotor that holds a pilot's craft aloft. Space climbs, Ctrl descends.",
		"shape": {"type": "cylinder", "radius": 0.25, "height": 0.35, "axis": "y"},
		"device": "rotor", "force": 3400.0, "unlock": "q_cargo", "material": "metal"},
	"seat": {
		"name": "Pilot Seat", "category": "mechanics", "price": 35, "mass": 30.0, "hp": 100.0,
		"desc": "Press E to sit. Drives every wheel, thruster and rotor welded to it.",
		"shape": {"type": "box", "size": Vector3(0.8, 1.2, 0.8)},
		"device": "seat", "material": "leather"},
	"lamp": {
		"name": "Brass Lantern", "category": "mechanics", "price": 10, "mass": 6.0, "hp": 40.0,
		"desc": "A cosy light. Toggle with F while piloting, or with the Rune Toolkit.",
		"shape": {"type": "box", "size": Vector3(0.35, 0.6, 0.35)},
		"device": "lamp", "material": "metal"},
	"spring_pad": {
		"name": "Spring Pad", "category": "mechanics", "price": 20, "mass": 25.0, "hp": 100.0,
		"desc": "Boing. Launches anything that lands on it.",
		"shape": {"type": "cylinder", "radius": 0.6, "height": 0.4, "axis": "y"},
		"device": "spring", "material": "metal"},
	"hover_stone": {
		"name": "Levitation Stone", "category": "arcana", "price": 85, "mass": 40.0, "hp": 150.0,
		"desc": "Floats its contraption a few metres above the ground. Steer with the pilot seat.",
		"shape": {"type": "box", "size": Vector3(0.8, 0.6, 0.8)},
		"device": "hover", "lift_mass": 450.0, "unlock": "q_survey", "material": "stone"},
	"arcane_turret": {
		"name": "Arcane Turret", "category": "defense", "price": 140, "mass": 40.0, "hp": 150.0,
		"desc": "Auto-targets nearby enemies with arcane bolts. Extra damage to tech foes.",
		"shape": {"type": "box", "size": Vector3(0.7, 0.9, 0.7)},
		"device": "turret_arcane", "range": 32.0, "unlock": "q_golems", "material": "metal"},
	"rivet_turret": {
		"name": "Rivet Gatling", "category": "defense", "price": 120, "mass": 45.0, "hp": 170.0,
		"desc": "Auto-targets nearby enemies with a hail of rivets. Extra damage to magic foes.",
		"shape": {"type": "box", "size": Vector3(0.7, 0.9, 0.8)},
		"device": "turret_rivet", "range": 28.0, "unlock": "q_arena", "material": "metal"},
	"ward_pylon": {
		"name": "Ward Pylon", "category": "defense", "price": 180, "mass": 50.0, "hp": 200.0,
		"desc": "Projects a shimmering dome that stops enemy projectiles.",
		"shape": {"type": "box", "size": Vector3(0.6, 1.7, 0.6)},
		"device": "ward", "radius": 7.0, "unlock": "q_foundry", "material": "stone"},
}

# Tools, spells and weapons share the hotbar. kind: tool | spell | weapon
const EQUIPMENT := {
	"gauntlet": {
		"name": "Grav Gauntlet", "kind": "tool", "price": 0, "model": "vm_gauntlet",
		"desc": "LMB grab and move parts. Wheel: push/pull. Hold R: rotate (Shift snaps). RMB: freeze/unfreeze."},
	"toolkit": {
		"name": "Rune Toolkit", "kind": "tool", "price": 0, "model": "vm_toolkit",
		"desc": "R cycles mode: Weld, Detach, Dismantle, Configure, Paint. LMB applies, RMB alternate."},
	"arcane_bolt": {
		"name": "Arcane Bolt", "kind": "spell", "price": 0, "model": "vm_staff", "icon": "icon_spell_arcane_bolt",
		"mana": 7.0, "cooldown": 0.32, "damage": 16.0, "damage_type": "arcane", "speed": 46.0,
		"color": Color(0.66, 0.42, 1.0),
		"desc": "A quick bolt of violet force. Shreds tech foes."},
	"fireball": {
		"name": "Fireball", "kind": "spell", "price": 220, "model": "vm_staff", "icon": "icon_spell_fireball",
		"mana": 24.0, "cooldown": 0.9, "damage": 34.0, "splash": 34.0, "radius": 4.0, "damage_type": "fire", "speed": 30.0,
		"color": Color(1.0, 0.55, 0.15),
		"desc": "A roaring ball of fire that explodes on impact."},
	"chain_lightning": {
		"name": "Chain Lightning", "kind": "spell", "price": 360, "model": "vm_staff", "icon": "icon_spell_chain_lightning",
		"mana": 28.0, "cooldown": 1.0, "damage": 30.0, "chains": 3, "damage_type": "shock", "range": 34.0,
		"color": Color(0.45, 0.9, 1.0),
		"desc": "Lightning that leaps between up to four foes. Devastating against machines."},
	"mending_ward": {
		"name": "Mending Ward", "kind": "spell", "price": 280, "model": "vm_staff", "icon": "icon_spell_mending_ward",
		"mana": 40.0, "cooldown": 9.0, "heal": 70.0, "duration": 5.0, "damage_type": "none",
		"color": Color(0.5, 1.0, 0.55),
		"desc": "Heals 70 over five seconds and halves damage taken while it glows."},
	"arc_pistol": {
		"name": "Arc Pistol", "kind": "weapon", "price": 0, "model": "vm_arc_pistol",
		"damage": 13.0, "damage_type": "shock", "fire_rate": 4.5, "mag": 12, "reload": 1.1, "hitscan": true, "range": 70.0,
		"spread": 0.6, "color": Color(0.4, 0.9, 1.0),
		"desc": "A zappy sidearm. Hitscan shock damage, quick reload."},
	"rivet_repeater": {
		"name": "Rivet Repeater", "kind": "weapon", "price": 320, "model": "vm_rivet_repeater",
		"damage": 8.0, "damage_type": "kinetic", "fire_rate": 11.0, "mag": 45, "reload": 1.9, "speed": 90.0,
		"spread": 2.2, "color": Color(1.0, 0.8, 0.4),
		"desc": "Full-auto rivets. Excellent against spirits and golems."},
	"boom_mortar": {
		"name": "Boom Mortar", "kind": "weapon", "price": 480, "model": "vm_boom_mortar",
		"damage": 25.0, "splash": 60.0, "radius": 5.0, "damage_type": "fire", "fire_rate": 1.1, "mag": 4, "reload": 2.4,
		"speed": 26.0, "gravity": 14.0, "spread": 0.0, "color": Color(1.0, 0.6, 0.2),
		"desc": "Lobs bouncing bombs. Big boom, bigger smile."},
}

const STARTER_EQUIPMENT := ["gauntlet", "toolkit", "arcane_bolt", "arc_pistol"]

const CONSUMABLES := {
	"health_tonic": {"name": "Health Tonic", "price": 25, "heal": 60.0, "model": "item_health_tonic",
		"desc": "Restores 60 health. Tastes of cherries and copper. (H)"},
	"mana_draught": {"name": "Mana Draught", "price": 20, "mana": 70.0, "model": "item_mana_draught",
		"desc": "Restores 70 mana. Fizzes. (G)"},
}

const UPGRADES := {
	"vitality": {"name": "Heartstone Amulet", "prices": [120, 300, 600], "icon": "icon_upgrade_vitality",
		"desc": "+30 max health per tier."},
	"arcana": {"name": "Rune Focus", "prices": [200, 450, 800], "icon": "icon_upgrade_arcana",
		"desc": "+15% spell damage per tier."},
	"engineering": {"name": "Gunsmith's Kit", "prices": [200, 450, 800], "icon": "icon_upgrade_engineering",
		"desc": "+15% weapon and turret damage per tier."},
	"capacity": {"name": "Workshop Permit", "prices": [150, 350, 700], "icon": "icon_upgrade_capacity",
		"desc": "+15 contraption parts allowed in the world per tier."},
	"mana_regen": {"name": "Mana Battery", "prices": [100, 250, 500], "icon": "icon_upgrade_mana_regen",
		"desc": "+50% mana regeneration per tier."},
}

# Quest / loot items.
const ITEMS := {
	"scrap_gear": {"name": "Scrap Gear", "model": "item_scrap_gear", "desc": "A gear salvaged from a Cogwork machine."},
	"ember_essence": {"name": "Ember Essence", "model": "item_ember_essence", "desc": "The still-warm heart of a wisp."},
	"rune_shard": {"name": "Rune Shard", "model": "item_rune_shard", "desc": "A humming crystal splinter from a golem."},
}

# Vendors: which shop tabs each NPC offers.
const VENDORS := {
	"odda": {"title": "Odda's Workshop", "tabs": ["parts", "upgrades:capacity,vitality"]},
	"lirael": {"title": "Lirael's Arcanum", "tabs": ["spells", "upgrades:arcana,mana_regen", "consumables:mana_draught"]},
	"gus": {"title": "Gus's Gizmos", "tabs": ["weapons", "upgrades:engineering", "consumables:health_tonic,mana_draught"]},
}

# Enemy stats. resist: multipliers per damage type (arcane, fire, shock, kinetic).
const ENEMIES := {
	"wisp": {"name": "Ember Wisp", "faction": "magic", "hp": 35.0, "speed": 7.0, "xp": 14, "gold": [3, 6],
		"resist": {"arcane": 0.6, "fire": 0.0, "shock": 1.0, "kinetic": 1.3}, "flying": true,
		"loot": {"ember_essence": 0.45}, "model": "enemy_wisp"},
	"golem": {"name": "Rune Golem", "faction": "magic", "hp": 260.0, "speed": 2.6, "xp": 70, "gold": [18, 28],
		"resist": {"arcane": 0.5, "fire": 0.6, "shock": 0.8, "kinetic": 1.3}, "flying": false,
		"loot": {"rune_shard": 0.8}, "model": "enemy_golem"},
	"wraith": {"name": "Shade Wraith", "faction": "magic", "hp": 90.0, "speed": 5.5, "xp": 32, "gold": [8, 14],
		"resist": {"arcane": 0.75, "fire": 1.0, "shock": 1.2, "kinetic": 0.55}, "flying": true,
		"loot": {}, "model": "enemy_wraith"},
	"cultist": {"name": "Choir Cultist", "faction": "magic", "hp": 75.0, "speed": 3.8, "xp": 26, "gold": [7, 12],
		"resist": {"arcane": 0.75, "fire": 1.25, "shock": 1.0, "kinetic": 1.0}, "flying": false,
		"loot": {"rune_shard": 0.15}, "model": "enemy_cultist"},
	"archon": {"name": "The Hollow Archon", "faction": "magic", "hp": 1400.0, "speed": 3.0, "xp": 600, "gold": [250, 300],
		"resist": {"arcane": 0.5, "fire": 1.0, "shock": 1.0, "kinetic": 1.2}, "flying": false, "boss": true,
		"loot": {}, "model": "enemy_cultist"},
	"drone": {"name": "Scout Drone", "faction": "tech", "hp": 45.0, "speed": 8.0, "xp": 16, "gold": [4, 7],
		"resist": {"arcane": 1.25, "fire": 1.0, "shock": 2.0, "kinetic": 0.75}, "flying": true,
		"loot": {"scrap_gear": 0.55}, "model": "enemy_drone"},
	"sentry": {"name": "Sentry Turret", "faction": "tech", "hp": 150.0, "speed": 0.0, "xp": 40, "gold": [10, 16],
		"resist": {"arcane": 1.25, "fire": 0.75, "shock": 2.0, "kinetic": 0.5}, "flying": false, "static": true,
		"loot": {"scrap_gear": 0.9}, "model": "enemy_sentry"},
	"crawler": {"name": "Clank Crawler", "faction": "tech", "hp": 55.0, "speed": 7.5, "xp": 20, "gold": [5, 9],
		"resist": {"arcane": 1.25, "fire": 1.0, "shock": 1.75, "kinetic": 1.0}, "flying": false,
		"loot": {"scrap_gear": 0.4}, "model": "enemy_crawler"},
	"ironclad": {"name": "Ironclad Warwalker", "faction": "tech", "hp": 1600.0, "speed": 2.4, "xp": 650, "gold": [250, 320],
		"resist": {"arcane": 1.0, "fire": 0.75, "shock": 1.5, "kinetic": 0.5}, "flying": false, "boss": true,
		"loot": {}, "model": "enemy_ironclad"},
}


func part(id: String) -> Dictionary:
	return PARTS.get(id, {})


func equipment(id: String) -> Dictionary:
	return EQUIPMENT.get(id, {})


func enemy(id: String) -> Dictionary:
	return ENEMIES.get(id, {})


func part_model_path(id: String) -> String:
	return MODEL_DIR % ["parts", "part_" + id]


func model_path(category: String, model_name: String) -> String:
	return MODEL_DIR % [category, model_name]


func part_icon(id: String) -> Texture2D:
	return MaterialLib.texture(PART_ICON % id)


func equipment_icon(id: String) -> Texture2D:
	var e := equipment(id)
	if e.has("icon"):
		var t := MaterialLib.texture(UI_ICON % e["icon"])
		if t:
			return t
	if e.has("model"):
		return MaterialLib.texture(ITEM_ICON % e["model"])
	return null


func item_icon(model_name: String) -> Texture2D:
	return MaterialLib.texture(ITEM_ICON % model_name)


func upgrade_icon(id: String) -> Texture2D:
	return MaterialLib.texture(UI_ICON % UPGRADES[id]["icon"])


func display_name(id: String) -> String:
	if PARTS.has(id):
		return PARTS[id]["name"]
	if EQUIPMENT.has(id):
		return EQUIPMENT[id]["name"]
	if CONSUMABLES.has(id):
		return CONSUMABLES[id]["name"]
	if ITEMS.has(id):
		return ITEMS[id]["name"]
	if UPGRADES.has(id):
		return UPGRADES[id]["name"]
	if ENEMIES.has(id):
		return ENEMIES[id]["name"]
	return id.capitalize()
