extends Node
## Static game data: build parts, tools, weapons (tech guns and melee, magic wands, staves, tomes, orbs,
## scepters and blades), rarities and perks, consumables, materials, pouches, crafting stations and
## recipes, schematics, talents, gathering nodes, upgrades, vendors, loot tables and enemies.
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


# ------------------------------------------------------------------------------------------ tools
# Tools always sit in hotbar slots 3 and 4.
const TOOLS := {
	"gauntlet": {
		"name": "Grav Gauntlet", "kind": "tool", "price": 0, "model": "vm_gauntlet",
		"desc": "LMB grab and move parts. Wheel: push/pull. Hold R: rotate (Shift snaps). RMB: freeze/unfreeze."},
	"toolkit": {
		"name": "Rune Toolkit", "kind": "tool", "price": 0, "model": "vm_toolkit",
		"desc": "R cycles mode: Weld, Detach, Dismantle, Configure, Paint. LMB applies, RMB alternate."},
}
const TOOL_SLOTS := ["gauntlet", "toolkit"]

# ------------------------------------------------------------------------------------------ weapons
# Every combat item is a weapon instance in the inventory (see make_weapon). Two of them sit in the
# hotbar weapon slots, and any weapon - gun, wand, staff, tome, blade - can go in either slot.
#   kind: gun | spell | melee      school: tech | magic (which damage bonuses apply)
#   fire (guns): hitscan | projectile | lob | pellets | flame | bolt | gatling | charge
#   cast (spells): bolt | fireball | chain | ward | spray | seeker | orb | beam
#   burn: fire damage per second for 3 s on hit · chill: slow fraction for 2.5 s on hit
#   sold: list-price stock at the base vendors (others are found, crafted or rolled into featured stock)
#   drop: weight in random loot
const WEAPONS := {
	# ---------------------------------------------------------------- tech
	"arc_pistol": {
		"name": "Arc Pistol", "kind": "gun", "school": "tech", "fire": "hitscan", "price": 90, "model": "vm_arc_pistol", "drop": 1.0,
		"damage": 13.0, "damage_type": "shock", "fire_rate": 4.5, "mag": 12, "reload": 1.1, "range": 70.0,
		"spread": 0.6, "color": Color(0.4, 0.9, 1.0), "sfx": "gun_arc_pistol", "tracer": "lightning", "sold": true,
		"desc": "A zappy sidearm. Hitscan shock bolts and a quick reload. Machines hate it."},
	"rivet_repeater": {
		"name": "Rivet Repeater", "kind": "gun", "school": "tech", "fire": "projectile", "price": 320, "model": "vm_rivet_repeater", "drop": 1.0,
		"damage": 8.0, "damage_type": "kinetic", "fire_rate": 11.0, "mag": 45, "reload": 1.9, "speed": 90.0, "range": 120.0,
		"spread": 2.2, "color": Color(1.0, 0.8, 0.4), "auto": true, "sfx": "gun_rivet", "sold": true,
		"desc": "Full-auto rivets from a spinning drum. Excellent against spirits and golems."},
	"boom_mortar": {
		"name": "Boom Mortar", "kind": "gun", "school": "tech", "fire": "lob", "price": 480, "model": "vm_boom_mortar", "drop": 0.8,
		"damage": 25.0, "splash": 60.0, "radius": 5.0, "damage_type": "fire", "fire_rate": 1.1, "mag": 4, "reload": 2.4,
		"speed": 26.0, "gravity": 14.0, "spread": 0.0, "range": 60.0, "color": Color(1.0, 0.6, 0.2), "sfx": "gun_mortar", "sold": true,
		"desc": "Lobs bouncing bombs. Big boom, bigger smile."},
	"scattergun": {
		"name": "Cogburst Scattergun", "kind": "gun", "school": "tech", "fire": "pellets", "price": 380, "model": "vm_scattergun", "drop": 0.9,
		"damage": 7.5, "pellets": 9, "damage_type": "kinetic", "fire_rate": 1.35, "mag": 6, "reload": 2.1, "range": 30.0,
		"spread": 6.5, "color": Color(1.0, 0.82, 0.45), "auto": true, "sfx": "gun_scatter", "sold": true,
		"desc": "Nine hot rivets in one brassy blast. Devastating up close, polite at range."},
	"tesla_lance": {
		"name": "Tesla Lance", "kind": "gun", "school": "tech", "fire": "charge", "price": 560, "model": "vm_tesla_lance", "drop": 0.6,
		"damage": 64.0, "damage_type": "shock", "charge": 1.0, "mag": 5, "reload": 2.3, "range": 150.0, "pierce": 3,
		"fire_rate": 1.6, "spread": 0.0, "color": Color(0.45, 0.95, 1.0), "sold": true,
		"desc": "Hold LMB to charge, release to loose a piercing bolt of lightning. Full charge hits hardest."},
	"longshot": {
		"name": "Brass Longshot", "kind": "gun", "school": "tech", "fire": "hitscan", "price": 620, "model": "vm_longshot", "drop": 0.7,
		"damage": 48.0, "damage_type": "kinetic", "fire_rate": 1.15, "mag": 5, "reload": 2.3, "range": 240.0, "spread": 1.4,
		"scope": true, "crit": 0.1, "color": Color(1.0, 0.86, 0.55), "sfx": "gun_longshot", "tracer": "beam",
		"desc": "A long brass marksman rifle with a ley-lens scope. Hold RMB to zoom: scoped shots fly true and hit 25% harder."},
	"gatling": {
		"name": "Steamroller Gatling", "kind": "gun", "school": "tech", "fire": "gatling", "price": 780, "model": "vm_gatling", "drop": 0.45,
		"damage": 6.0, "damage_type": "kinetic", "fire_rate": 18.0, "spinup": 1.1, "mag": 140, "reload": 3.4, "speed": 110.0,
		"range": 120.0, "spread": 3.0, "auto": true, "move_slow": 0.3, "color": Color(1.0, 0.75, 0.35), "sfx": "gun_gatling",
		"desc": "Six steam-spun barrels. Hold LMB to spin up into a torrent of rivets; you walk slower while it roars."},
	"flamer": {
		"name": "Bellows Flamethrower", "kind": "gun", "school": "tech", "fire": "flame", "price": 560, "model": "vm_flamer", "drop": 0.6,
		"damage": 5.0, "damage_type": "fire", "fire_rate": 10.0, "mag": 100, "reload": 2.6, "range": 9.0, "cone": 14.0,
		"burn": 6.0, "auto": true, "color": Color(1.0, 0.55, 0.15), "sfx": "flamer_burst",
		"desc": "A roaring cone of bellows-fed flame that sets foes ablaze. Short range, long smiles. Fire spirits just laugh."},
	"crossbow": {
		"name": "Clockwork Crossbow", "kind": "gun", "school": "tech", "fire": "bolt", "price": 340, "model": "vm_crossbow", "drop": 0.85,
		"damage": 36.0, "damage_type": "kinetic", "fire_rate": 1.5, "mag": 6, "reload": 1.9, "speed": 75.0, "gravity": 5.0,
		"range": 140.0, "spread": 0.3, "pierce": 1, "crit": 0.2, "color": Color(0.95, 0.88, 0.7), "sfx": "crossbow_fire", "sold": true,
		"desc": "A repeating crossbow wound by clockwork. Heavy, silent bolts that punch through a foe and crit often."},
	"thunder_wrench": {
		"name": "Thunder Wrench", "kind": "melee", "school": "tech", "price": 240, "model": "vm_thunder_wrench", "drop": 0.8,
		"damage": 32.0, "damage_type": "kinetic", "swing_time": 0.55, "reach": 3.0, "zap": 10.0, "repair": 35.0,
		"color": Color(0.5, 0.9, 1.0), "sold": true,
		"desc": "A capacitor-charged spanner. Clangs foes with a shocking whack, and repairs your contraption parts on hit."},
	"steam_hammer": {
		"name": "Piston Maul", "kind": "melee", "school": "tech", "price": 480, "model": "vm_steam_hammer", "drop": 0.6,
		"damage": 52.0, "damage_type": "kinetic", "swing_time": 0.9, "reach": 3.2, "quake": 4.5, "knock": 14.0,
		"color": Color(1.0, 0.8, 0.45), "sfx_hit": "hammer_slam",
		"desc": "A steam-driven sledgehammer. Slow, crushing swings; RMB slams the ground in a shockwave that flings foes away."},
	# ---------------------------------------------------------------- magic
	"arcane_bolt": {
		"name": "Arcane Bolt", "kind": "spell", "school": "magic", "cast": "bolt", "price": 60, "model": "vm_staff", "icon": "icon_spell_arcane_bolt", "drop": 0.7,
		"mana": 7.0, "cooldown": 0.32, "damage": 16.0, "damage_type": "arcane", "speed": 46.0, "range": 110.0,
		"color": Color(0.66, 0.42, 1.0), "crystal": Color("a066ff"), "sfx": "spell_arcane_cast", "sold": true,
		"desc": "A gnarled wand that flings quick bolts of violet force. Shreds tech foes."},
	"ember_wand": {
		"name": "Emberwick Wand", "kind": "spell", "school": "magic", "cast": "bolt", "price": 200, "model": "vm_wand", "drop": 0.8,
		"mana": 5.0, "cooldown": 0.24, "damage": 10.0, "damage_type": "fire", "speed": 54.0, "range": 100.0, "burn": 4.0,
		"color": Color(1.0, 0.55, 0.2), "crystal": Color("ff8a2e"), "sfx": "wand_ember", "sold": true,
		"desc": "A slender wand that spits rapid embers. Every bolt leaves its target smouldering."},
	"frost_wand": {
		"name": "Rimefang Wand", "kind": "spell", "school": "magic", "cast": "spray", "price": 280, "model": "vm_wand", "drop": 0.75,
		"mana": 9.0, "cooldown": 0.5, "damage": 9.0, "shards": 3, "spread": 5.0, "damage_type": "frost", "speed": 62.0,
		"range": 70.0, "chill": 0.4, "color": Color(0.62, 0.9, 1.0), "crystal": Color("8fe3ff"), "sfx": "wand_frost", "sold": true,
		"desc": "Flings a fan of three frost shards. Chilled foes move 40% slower. Ember Wisps hate it."},
	"fireball": {
		"name": "Fireball", "kind": "spell", "school": "magic", "cast": "fireball", "price": 220, "model": "vm_staff", "icon": "icon_spell_fireball", "drop": 0.7,
		"mana": 24.0, "cooldown": 0.9, "damage": 34.0, "splash": 34.0, "radius": 4.0, "damage_type": "fire", "speed": 30.0,
		"range": 90.0, "color": Color(1.0, 0.55, 0.15), "crystal": Color("ff8a2e"), "sfx": "spell_fireball_cast", "sold": true,
		"desc": "A spell focus that hurls roaring balls of fire. They explode on impact."},
	"chain_lightning": {
		"name": "Chain Lightning", "kind": "spell", "school": "magic", "cast": "chain", "price": 360, "model": "vm_staff", "icon": "icon_spell_chain_lightning", "drop": 0.6,
		"mana": 28.0, "cooldown": 1.0, "damage": 30.0, "chains": 3, "damage_type": "shock", "range": 34.0,
		"color": Color(0.45, 0.9, 1.0), "crystal": Color("5fe9ff"), "sold": true,
		"desc": "A spell focus crackling with lightning that leaps between up to four foes. Devastating against machines."},
	"mending_ward": {
		"name": "Mending Ward", "kind": "spell", "school": "magic", "cast": "ward", "price": 280, "model": "vm_staff", "icon": "icon_spell_mending_ward", "drop": 0.4,
		"mana": 40.0, "cooldown": 9.0, "heal": 70.0, "duration": 5.0, "damage": 0.0, "damage_type": "none",
		"color": Color(0.5, 1.0, 0.55), "crystal": Color("6fdc6a"), "sold": true,
		"desc": "A spell focus of green light. Heals 70 over five seconds and halves damage taken while it glows."},
	"seeker_tome": {
		"name": "Wispcaller Grimoire", "kind": "spell", "school": "magic", "cast": "seeker", "price": 440, "model": "vm_tome", "drop": 0.55,
		"mana": 22.0, "cooldown": 0.85, "damage": 15.0, "seekers": 3, "damage_type": "arcane", "speed": 24.0, "range": 60.0,
		"color": Color(0.35, 0.95, 0.85), "crystal": Color("39d5c4"), "sfx": "tome_cast",
		"desc": "Every page you turn frees three homing wisps that hunt the foes nearest your aim."},
	"void_orb": {
		"name": "Gloom Orb", "kind": "spell", "school": "magic", "cast": "orb", "price": 660, "model": "vm_orb", "drop": 0.4,
		"mana": 38.0, "cooldown": 3.2, "damage": 16.0, "splash": 46.0, "radius": 6.0, "duration": 3.0, "damage_type": "arcane",
		"speed": 9.0, "range": 40.0, "color": Color(0.58, 0.32, 1.0), "crystal": Color("7a3cff"), "sfx": "orb_cast",
		"desc": "Launches a slow orb of gloom that drags nearby foes into it, grinds them for three seconds, then implodes."},
	"sun_scepter": {
		"name": "Sunlance Scepter", "kind": "spell", "school": "magic", "cast": "beam", "price": 720, "model": "vm_scepter", "drop": 0.4,
		"mana": 16.0, "cooldown": 0.1, "damage": 30.0, "ramp": 1.6, "damage_type": "arcane", "range": 42.0,
		"color": Color(1.0, 0.86, 0.38), "crystal": Color("ffd34a"), "sfx": "beam_hum",
		"desc": "Hold LMB to pour out a searing beam of sunlight that burns hotter the longer you hold it. Costs mana every second."},
	"runeblade": {
		"name": "Runeblade", "kind": "melee", "school": "magic", "price": 540, "model": "vm_runeblade", "drop": 0.55,
		"damage": 30.0, "damage_type": "arcane", "swing_time": 0.42, "reach": 2.9, "wave": 40.0, "wave_mana": 15.0,
		"color": Color(0.55, 0.85, 1.0), "crystal": Color("6fd6ff"), "sfx_swing": "blade_swing",
		"desc": "A sword etched with ley runes. Quick arcane slashes; RMB looses a piercing crescent wave for 15 mana."},
}

const STARTER_WEAPONS := ["arc_pistol", "arcane_bolt"]
const STARTER_EQUIPMENT := ["gauntlet", "toolkit", "arcane_bolt", "arc_pistol"]

const KIND_NAMES := {"gun": "Gun", "spell": "Spell focus", "melee": "Melee", "tool": "Tool"}
const SCHOOL_NAMES := {"tech": "Tech", "magic": "Magic"}
const DAMAGE_TYPES := ["kinetic", "fire", "shock", "arcane", "frost"]

# Unique names for legendary drops.
const LEGENDARY_NAMES := {
	"arc_pistol": "Old Sparky", "rivet_repeater": "The Rivetstorm", "boom_mortar": "Grandma's Kettle",
	"scattergun": "Brassbeard's Bellower", "tesla_lance": "Skyspear", "thunder_wrench": "Thunderclap Torque",
	"longshot": "The Long Goodbye", "gatling": "Aunt Clatterby", "flamer": "Dragon's Hiccup", "crossbow": "Tick-Tock Twang",
	"steam_hammer": "The Kettledrum", "arcane_bolt": "Whisper of the Archmage", "ember_wand": "Hearthfire's Last Word",
	"frost_wand": "Winter's Tooth", "fireball": "Sunpiper's Ember", "chain_lightning": "Stormweaver's Fork",
	"mending_ward": "The Heartbloom", "seeker_tome": "The Murmuring Folio", "void_orb": "Heart of the Hollow",
	"sun_scepter": "Dawnbringer", "runeblade": "Leyline's Edge",
}

# ------------------------------------------------------------------------------------------ rarity & levels
const RARITY_NAMES := ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
const RARITY_COLORS := [Color("d9d2c0"), Color("6fdc6a"), Color("4d9dff"), Color("b56cff"), Color("ffa63c")]
const RARITY_POWER := [1.0, 1.12, 1.26, 1.42, 1.62]
const RARITY_PERKS := [0, 1, 1, 2, 2]
const RARITY_VALUE := [1.0, 1.7, 2.8, 4.5, 7.5]
const RARITY_WEIGHTS := [60.0, 26.0, 10.0, 3.5, 0.5]
const MAX_WEAPON_LEVEL := 10
const MAX_LEVEL := 30
const MAX_INFUSE_RARITY := 3      # enchanting can raise a weapon to Epic; Legendaries only drop

# Perks roll on Uncommon+ weapons. kinds: which weapon kinds can roll it.
const PERKS := {
	"brutal": {"name": "Brutal", "suffix": "of Ruin", "desc": "+18% damage", "kinds": ["gun", "spell", "melee"]},
	"hasty": {"name": "Hasty", "suffix": "of Haste", "desc": "+20% attack speed", "kinds": ["gun", "spell", "melee"]},
	"deep": {"name": "Deep-Drum", "suffix": "of Plenty", "desc": "+50% magazine size", "kinds": ["gun"]},
	"quick": {"name": "Quickload", "suffix": "of Readiness", "desc": "35% faster reloads", "kinds": ["gun"]},
	"steady": {"name": "Steady", "suffix": "of Steadiness", "desc": "Half the spread, +20% range", "kinds": ["gun"]},
	"frugal": {"name": "Frugal", "suffix": "of Thrift", "desc": "-30% mana cost", "kinds": ["spell"]},
	"keen": {"name": "Keen", "suffix": "of Precision", "desc": "+15% chance to crit for double damage", "kinds": ["gun", "spell", "melee"]},
	"leech": {"name": "Leeching", "suffix": "of the Leech", "desc": "Heals you for 5% of damage dealt", "kinds": ["gun", "spell", "melee"]},
	"volatile": {"name": "Volatile", "suffix": "of Kaboom", "desc": "12% chance for hits to explode", "kinds": ["gun", "spell", "melee"]},
	"arcing": {"name": "Arcing", "suffix": "of Storms", "desc": "15% chance for hits to arc lightning to a nearby foe", "kinds": ["gun", "spell", "melee"]},
	"hexbane": {"name": "Hexbreaker", "suffix": "of Hexbreaking", "desc": "+30% damage against Hollow Choir (magic) foes", "kinds": ["gun", "spell", "melee"]},
	"gearbane": {"name": "Scrapper's", "suffix": "of Scrap", "desc": "+30% damage against Cogwork Legion (tech) foes", "kinds": ["gun", "spell", "melee"]},
	"searing": {"name": "Searing", "suffix": "of Cinders", "desc": "20% chance for hits to set foes ablaze", "kinds": ["gun", "spell", "melee"]},
	"chilling": {"name": "Rimebound", "suffix": "of Frost", "desc": "20% chance for hits to chill foes (40% slower)", "kinds": ["gun", "spell", "melee"]},
}

# ------------------------------------------------------------------------------------------ consumables
# Quick-slot items (hotbar slots 5-8). use: heal | mana | throw | buff | repair | regen
const CONSUMABLES := {
	"health_tonic": {"name": "Health Tonic", "price": 25, "heal": 60.0, "model": "item_health_tonic", "use": "heal",
		"desc": "Restores 60 health. Tastes of cherries and copper. (H)"},
	"greater_health_tonic": {"name": "Greater Health Tonic", "price": 70, "heal": 150.0, "model": "item_greater_health_tonic", "use": "heal",
		"desc": "Restores 150 health. Brewed with glowcaps and a sunpetal for courage."},
	"mana_draught": {"name": "Mana Draught", "price": 20, "mana": 70.0, "model": "item_mana_draught", "use": "mana",
		"desc": "Restores 70 mana. Fizzes. (G)"},
	"greater_mana_draught": {"name": "Greater Mana Draught", "price": 60, "mana": 180.0, "model": "item_greater_mana_draught", "use": "mana",
		"desc": "Restores 180 mana. Fizzes in two directions at once."},
	"regen_salve": {"name": "Mender's Salve", "price": 50, "heal": 140.0, "duration": 20.0, "model": "item_regen_salve", "use": "regen",
		"desc": "Heals 140 health over 20 seconds. Smells of moss and good intentions."},
	"spark_bomb": {"name": "Spark Bomb", "price": 30, "model": "item_spark_bomb", "use": "throw",
		"damage": 22.0, "splash": 55.0, "radius": 4.5, "damage_type": "fire",
		"desc": "A throwable bomb with a ley-crystal heart. Explodes on a short fuse for heavy fire damage."},
	"frost_bomb": {"name": "Rime Bomb", "price": 40, "model": "item_frost_bomb", "use": "throw",
		"damage": 14.0, "splash": 34.0, "radius": 5.5, "damage_type": "frost", "chill": 0.55,
		"desc": "Bursts into a cloud of rime that chills every foe caught in it (55% slower for a few seconds)."},
	"shock_jar": {"name": "Lightning Jar", "price": 45, "model": "item_shock_jar", "use": "throw",
		"damage": 20.0, "splash": 50.0, "radius": 4.5, "damage_type": "shock",
		"desc": "A jar of bottled storm. Shatters into a crackling shock blast that Cogwork machines adore. Not."},
	"swift_elixir": {"name": "Swiftfoot Elixir", "price": 45, "model": "item_swift_elixir", "use": "buff", "buff": "swift", "duration": 45.0,
		"desc": "For 45 s: move 30% faster, and sprinting costs no stamina."},
	"iron_tonic": {"name": "Ironhide Tonic", "price": 45, "model": "item_iron_tonic", "use": "buff", "buff": "iron", "duration": 40.0,
		"desc": "For 40 s: take 35% less damage. Tastes like a horseshoe."},
	"berserker_brew": {"name": "Berserker Brew", "price": 80, "model": "item_berserker_brew", "use": "buff", "buff": "fury", "duration": 30.0,
		"desc": "For 30 s: every weapon deals 25% more damage. Foam included."},
	"fortune_tonic": {"name": "Gambler's Fortune", "price": 90, "model": "item_fortune_tonic", "use": "buff", "buff": "luck", "duration": 180.0,
		"desc": "For 3 minutes: foes drop 40% more gold, and loot rolls rarer."},
	"skyleap_draught": {"name": "Skyleap Draught", "price": 55, "model": "item_skyleap_draught", "use": "buff", "buff": "leap", "duration": 60.0,
		"desc": "For 60 s: jump 60% higher and drift gently down like a dandelion."},
	"weapon_oil": {"name": "Gunsmith's Oil", "price": 60, "model": "item_weapon_oil", "use": "buff", "buff": "oiled", "duration": 90.0,
		"desc": "For 90 s: tech weapons deal 20% more damage and reload 20% faster."},
	"focus_incense": {"name": "Arcane Incense", "price": 60, "model": "item_focus_incense", "use": "buff", "buff": "attuned", "duration": 90.0,
		"desc": "For 90 s: magic weapons deal 20% more damage and cost 20% less mana."},
	"repair_kit": {"name": "Tinker's Patch Kit", "price": 35, "model": "item_repair_kit", "use": "repair", "amount": 0.6,
		"desc": "Repairs 60% of every part on the contraption you are piloting or looking at."},
	"treasure_map": {"name": "Treasure Map", "price": 40, "model": "item_treasure_map", "use": "buff", "buff": "map", "duration": 180.0,
		"desc": "For 3 minutes your compass marks the nearest unopened treasure chest (and Ley Vaults while you carry a Ley Key)."},
}

const BUFFS := {
	"swift": {"name": "Swiftfoot", "color": Color("39d5c4")},
	"iron": {"name": "Ironhide", "color": Color("f2b84e")},
	"map": {"name": "Treasure Map", "color": Color("ffc93c")},
	"fury": {"name": "Berserk", "color": Color("ff6a4d")},
	"luck": {"name": "Fortune", "color": Color("7ddc5a")},
	"leap": {"name": "Skyleap", "color": Color("9fd8ff")},
	"oiled": {"name": "Oiled", "color": Color("e0a85a")},
	"attuned": {"name": "Attuned", "color": Color("b48cff")},
}

const DEFAULT_QUICK := ["health_tonic", "mana_draught", "spark_bomb", "swift_elixir"]

# ------------------------------------------------------------------------------------------ materials & key items
# tier: 1 raw (dropped / gathered), 2 refined, 3 component. src: where to get it (shown in the UI).
const ITEMS := {
	"scrap_gear": {"name": "Scrap Gear", "model": "item_scrap_gear", "value": 6, "tier": 1,
		"src": "Cogwork machines (Gearworks, north road) and scrap heaps",
		"desc": "A gear salvaged from a Cogwork machine. Crafting material."},
	"ember_essence": {"name": "Ember Essence", "model": "item_ember_essence", "value": 8, "tier": 1,
		"src": "Ember Wisps in the Whispering Woods",
		"desc": "The still-warm heart of an Ember Wisp. Crafting material."},
	"rune_shard": {"name": "Rune Shard", "model": "item_rune_shard", "value": 12, "tier": 1,
		"src": "Rune Golems and Choir Cultists at the Sunken Shrine",
		"desc": "A humming crystal splinter from a golem or cultist. Crafting material."},
	"shade_silk": {"name": "Shade Silk", "model": "item_shade_silk", "value": 10, "tier": 1,
		"src": "Shade Wraiths (woods at night, the Shrine)",
		"desc": "Shimmering thread unravelled from a Shade Wraith's cloak. Crafting material."},
	"ley_crystal": {"name": "Ley Crystal", "model": "item_ley_crystal", "value": 9, "tier": 1,
		"src": "Teal ley-crystal clusters all over the valley",
		"desc": "A teal crystal grown on the valley's ley lines. Harvest them from crystal clusters."},
	"copper_ore": {"name": "Copper Ore", "model": "item_copper_ore", "value": 5, "tier": 1,
		"src": "Copper veins in the rocky hills (north, east, the gorge rim)",
		"desc": "A lump of rock shot through with bright copper. Smelt it at the Forge."},
	"iron_ore": {"name": "Iron Ore", "model": "item_iron_ore", "value": 6, "tier": 1,
		"src": "Iron veins around the Gearworks and the shrine hills",
		"desc": "Heavy, rusty and full of promise. Smelt it at the Forge."},
	"reed_fiber": {"name": "Reed Fiber", "model": "item_reed_fiber", "value": 3, "tier": 1,
		"src": "Reed clumps along the lake shore",
		"desc": "Tough golden reeds. Weave them into cloth at the Loom."},
	"glowcap": {"name": "Glowcap", "model": "item_glowcap", "value": 5, "tier": 1,
		"src": "Glowing mushroom patches in the Whispering Woods",
		"desc": "A softly glowing mushroom. Alchemists love it; your stomach will not."},
	"sunpetal": {"name": "Sunpetal", "model": "item_sunpetal", "value": 7, "tier": 1,
		"src": "Golden flowers on the southern flats and the meadows",
		"desc": "A warm golden blossom that hums with daylight. An alchemy staple."},
	"copper_ingot": {"name": "Copper Ingot", "model": "item_copper_ingot", "value": 14, "tier": 2,
		"src": "Smelt at the Forge (2 Copper Ore)",
		"desc": "A shiny bar of copper. Wires, coils and cheerful sparks."},
	"iron_ingot": {"name": "Iron Ingot", "model": "item_iron_ingot", "value": 15, "tier": 2,
		"src": "Smelt at the Forge (2 Iron Ore)",
		"desc": "A sturdy iron bar, the bones of every machine."},
	"brass_ingot": {"name": "Brass Ingot", "model": "item_brass_ingot", "value": 16, "tier": 2,
		"src": "Alloy at the Forge (copper ingot + scrap gears)",
		"desc": "Golden brass. Emberwick's favourite metal, for looks AND function."},
	"steel_plate": {"name": "Steel Plate", "model": "item_steel_plate", "value": 30, "tier": 2,
		"src": "Forge from iron ingots and ember essence",
		"desc": "A thick riveted plate of tempered steel."},
	"runesteel_ingot": {"name": "Runesteel Ingot", "model": "item_runesteel_ingot", "value": 70, "tier": 2,
		"src": "Forge from steel, rune shards and ley crystal (Artisan rank 5)",
		"desc": "Steel folded with rune shards until it hums. The finest weapons need it."},
	"spun_cloth": {"name": "Spun Cloth", "model": "item_spun_cloth", "value": 12, "tier": 2,
		"src": "Weave at the Loom (3 Reed Fiber)",
		"desc": "A bolt of sturdy cloth. Pouches, slings and very fashionable scarves."},
	"arcane_thread": {"name": "Arcane Thread", "model": "item_arcane_thread", "value": 18, "tier": 2,
		"src": "Spin at the Loom (shade silk + ley crystal)",
		"desc": "Thread that glows faintly teal. Stitch it into pouches and grimoires."},
	"rune_ink": {"name": "Rune Ink", "model": "item_rune_ink", "value": 14, "tier": 2,
		"src": "Mix at the Enchanter's Altar (rune shard + glowcap)",
		"desc": "Violet ink that writes itself if you leave it alone too long."},
	"focus_gem": {"name": "Focus Gem", "model": "item_focus_gem", "value": 40, "tier": 3,
		"src": "Cut at the Enchanter's Altar (ley crystals + a rune shard)",
		"desc": "A faceted gem that gathers ley power. The heart of every wand and enchantment."},
	"spring_coil": {"name": "Spring Coil", "model": "item_spring_coil", "value": 10, "tier": 3,
		"src": "Wind at the Workbench (1 Iron Ingot makes 2)",
		"desc": "A fat, bouncy steel spring. Boing."},
	"power_cell": {"name": "Power Cell", "model": "item_power_cell", "value": 34, "tier": 3,
		"src": "Assemble at the Workbench (copper, ley crystal, gear)",
		"desc": "A glass battery of sloshing teal ley-juice. Do not lick."},
	"ley_lens": {"name": "Ley Lens", "model": "item_ley_lens", "value": 38, "tier": 3,
		"src": "Grind at the Workbench (ley crystals + brass)",
		"desc": "A perfectly ground crystal lens in a brass ring. Scopes and scepters need one."},
	"clockwork_core": {"name": "Clockwork Core", "model": "item_clockwork_core", "value": 30, "tier": 3,
		"src": "Sentries, rarely drones and crawlers; craft at the Workbench (Artisan rank 6)",
		"desc": "The ticking heart of a Cogwork machine. Rare. Needed for the finest crafting."},
	"ley_key": {"name": "Ley Key", "model": "item_ley_key", "value": 40, "key": true,
		"src": "Champions, bosses; craft at the Workbench",
		"desc": "Opens one sealed Ley Vault. Champions sometimes carry them; artificers can craft them."},
}
const MATERIALS := ["scrap_gear", "ember_essence", "rune_shard", "shade_silk", "ley_crystal", "clockwork_core",
	"copper_ore", "iron_ore", "reed_fiber", "glowcap", "sunpetal",
	"copper_ingot", "iron_ingot", "brass_ingot", "steel_plate", "runesteel_ingot", "spun_cloth", "arcane_thread",
	"rune_ink", "focus_gem", "spring_coil", "power_cell", "ley_lens"]
const STACK_SIZE := {1: 40, 2: 30, 3: 20}
const CONSUMABLE_STACK := 10

# ------------------------------------------------------------------------------------------ pouches
# Equip up to five pouches (Game.POUCH_SLOTS) to grow your pack. Pouch perks do not stack.
const POUCHES := {
	"pouch_cloth": {"name": "Patched Cloth Pouch", "slots": 3, "rarity": 0, "price": 70, "model": "item_pouch_cloth",
		"desc": "A drawstring sack held together by optimism and big stitches."},
	"pouch_leather": {"name": "Leather Belt Pouch", "slots": 4, "rarity": 0, "price": 160, "model": "item_pouch_leather",
		"desc": "A proper leather pouch with a flap, a stud and a belt loop."},
	"pouch_brass": {"name": "Brass-Buckled Pouch", "slots": 6, "rarity": 1, "price": 360, "model": "item_pouch_brass",
		"desc": "Sturdy dark leather with brass buckles. Built to carry an artificer's clutter."},
	"pouch_rune": {"name": "Rune-Stitched Pouch", "slots": 8, "rarity": 2, "price": 0, "model": "item_pouch_rune",
		"desc": "Glowing rune stitches fold a little extra space inside it."},
	"pouch_ley": {"name": "Ley-Woven Satchel", "slots": 10, "rarity": 3, "price": 0, "model": "item_pouch_ley",
		"desc": "Woven from ley-touched thread. It is noticeably bigger on the inside."},
	"pouch_void": {"name": "Bottomless Pouch", "slots": 13, "rarity": 4, "price": 0, "model": "item_pouch_void",
		"desc": "Do not look directly into it. Something in there is looking for its socks."},
	"pouch_alchemist": {"name": "Alchemist's Bandolier", "slots": 4, "rarity": 2, "price": 0, "model": "item_pouch_alchemist",
		"perk": "alchemist", "perk_desc": "Potions, bombs and other consumables stack twice as high",
		"desc": "A leather bandolier lined with little vial loops."},
	"pouch_prospector": {"name": "Prospector's Satchel", "slots": 5, "rarity": 2, "price": 0, "model": "item_pouch_prospector",
		"perk": "prospector", "perk_desc": "+1 extra ore, herb, reed or crystal every time you gather",
		"desc": "Rugged canvas with a pickaxe strapped to the side."},
	"pouch_scavenger": {"name": "Scavenger's Sack", "slots": 5, "rarity": 1, "price": 0, "model": "item_pouch_scavenger",
		"perk": "scavenger", "perk_desc": "Coins and loot fly to you from twice as far away",
		"desc": "A lumpy burlap sack with a horseshoe magnet charm. Things just... follow you home."},
}

# ------------------------------------------------------------------------------------------ crafting stations
# "field" recipes can be made anywhere from the Crafting Book [B]; the rest need their station.
const STATIONS := {
	"workbench": {"name": "Artificer's Workbench", "short": "Workbench", "model": "prop_workbench", "sfx": "craft",
		"tabs": ["craft", "upgrade", "salvage"], "light": Color(1.0, 0.8, 0.45), "size": Vector3(2.5, 1.2, 1.3),
		"desc": "Gadgets, components and guns. Upgrade and salvage any weapon here."},
	"forge": {"name": "Emberwick Forge", "short": "Forge", "model": "prop_forge", "sfx": "forge_smelt",
		"tabs": ["craft", "upgrade"], "light": Color(1.0, 0.55, 0.2), "size": Vector3(2.6, 2.0, 2.0),
		"desc": "Smelt ore into ingots, alloy brass, temper steel and smith heavy weapons."},
	"alchemy": {"name": "Alchemist's Table", "short": "Alchemy Table", "model": "prop_alchemy_table", "sfx": "alchemy_brew",
		"tabs": ["craft"], "light": Color(0.55, 1.0, 0.6), "size": Vector3(2.0, 1.1, 1.0),
		"desc": "Brew tonics, salves, buffs and bombs from herbs and essences."},
	"altar": {"name": "Enchanter's Altar", "short": "Altar", "model": "prop_arcane_altar", "sfx": "enchant",
		"tabs": ["craft", "enchant", "upgrade"], "light": Color(0.7, 0.45, 1.0), "size": Vector3(1.6, 1.4, 1.6),
		"desc": "Mix rune ink, cut focus gems, craft wands and grimoires, and enchant weapons."},
	"loom": {"name": "Tailor's Loom", "short": "Loom", "model": "prop_loom", "sfx": "loom_weave",
		"tabs": ["craft"], "light": Color(1.0, 0.85, 0.6), "size": Vector3(2.0, 1.8, 1.2),
		"desc": "Weave cloth and thread, and sew the pouches that grow your pack."},
	"field": {"name": "Crafting Book", "short": "Anywhere", "model": "", "sfx": "craft", "tabs": ["craft"],
		"desc": "Simple recipes you can make anywhere. Everything else needs a station in Emberwick."},
}
const STATION_ORDER := ["workbench", "forge", "alchemy", "altar", "loom"]

# Artisan rank r needs ARTISAN_XP[r - 1] total crafting experience (rank 1-10).
const ARTISAN_XP := [0, 30, 80, 160, 280, 450, 680, 980, 1360, 1850]
const ARTISAN_TITLES := ["Tinkerer", "Apprentice", "Handy Hands", "Journeyman", "Craftsperson", "Artisan",
	"Expert Artisan", "Master Artisan", "Grandmaster", "Living Legend"]

# ------------------------------------------------------------------------------------------ recipes
# station: where it is made (field: true = also anywhere). gives: item counts; weapon: base id (rolls
# Uncommon or better, luckier at higher Artisan ranks). rank: Artisan rank needed. schematic: must be
# learned first (find, buy or earn "sch_<recipe id>"). cat: grouping in the crafting screen.
const RECIPES := {
	# ---------------------------------------------------------------- Artificer's Workbench
	"spring_coil": {"station": "workbench", "cat": "Components", "gives": {"spring_coil": 2}, "cost": {"iron_ingot": 1}, "gold": 4, "rank": 1},
	"power_cell": {"station": "workbench", "cat": "Components", "gives": {"power_cell": 1}, "cost": {"copper_ingot": 1, "ley_crystal": 1, "scrap_gear": 1}, "gold": 8, "rank": 2},
	"ley_lens": {"station": "workbench", "cat": "Components", "gives": {"ley_lens": 1}, "cost": {"ley_crystal": 2, "brass_ingot": 1}, "gold": 10, "rank": 3},
	"clockwork_core": {"station": "workbench", "cat": "Components", "gives": {"clockwork_core": 1}, "cost": {"brass_ingot": 2, "spring_coil": 2, "power_cell": 1}, "gold": 30, "rank": 6},
	"focus_gem_fine": {"station": "altar", "cat": "Reagents", "gives": {"focus_gem": 2}, "cost": {"ley_crystal": 4, "rune_shard": 1, "rune_ink": 1}, "gold": 20, "rank": 9},
	"spark_bomb": {"station": "workbench", "field": true, "cat": "Gadgets", "gives": {"spark_bomb": 2}, "cost": {"scrap_gear": 2, "ember_essence": 1}, "gold": 10, "rank": 1},
	"shock_jar": {"station": "workbench", "cat": "Gadgets", "gives": {"shock_jar": 2}, "cost": {"power_cell": 1, "copper_ingot": 1}, "gold": 14, "rank": 3},
	"repair_kit": {"station": "workbench", "field": true, "cat": "Gadgets", "gives": {"repair_kit": 1}, "cost": {"scrap_gear": 3}, "gold": 12, "rank": 1},
	"weapon_oil": {"station": "workbench", "cat": "Gadgets", "gives": {"weapon_oil": 2}, "cost": {"brass_ingot": 1, "ember_essence": 1}, "gold": 12, "rank": 2},
	"treasure_map": {"station": "workbench", "cat": "Gadgets", "gives": {"treasure_map": 1}, "cost": {"shade_silk": 1, "ley_crystal": 1}, "gold": 20, "rank": 1},
	"ley_key": {"station": "workbench", "cat": "Gadgets", "gives": {"ley_key": 1}, "cost": {"ley_crystal": 3, "rune_shard": 2, "clockwork_core": 1}, "gold": 60, "rank": 1},
	"w_arc_pistol": {"station": "workbench", "cat": "Guns", "weapon": "arc_pistol", "cost": {"copper_ingot": 2, "scrap_gear": 2}, "gold": 30, "rank": 1},
	"w_crossbow": {"station": "workbench", "cat": "Guns", "weapon": "crossbow", "cost": {"iron_ingot": 2, "spring_coil": 2, "spun_cloth": 1}, "gold": 90, "rank": 2},
	"w_rivet_repeater": {"station": "workbench", "cat": "Guns", "weapon": "rivet_repeater", "cost": {"brass_ingot": 2, "spring_coil": 2, "scrap_gear": 3}, "gold": 90, "rank": 2},
	"w_scattergun": {"station": "workbench", "cat": "Guns", "weapon": "scattergun", "cost": {"scrap_gear": 6, "clockwork_core": 1}, "gold": 160, "rank": 1},
	"w_longshot": {"station": "workbench", "cat": "Guns", "weapon": "longshot", "cost": {"brass_ingot": 3, "ley_lens": 1, "spring_coil": 2}, "gold": 200, "rank": 4, "schematic": true},
	"w_flamer": {"station": "workbench", "cat": "Guns", "weapon": "flamer", "cost": {"copper_ingot": 3, "power_cell": 1, "ember_essence": 4}, "gold": 180, "rank": 4, "schematic": true},
	"w_tesla_lance": {"station": "workbench", "cat": "Guns", "weapon": "tesla_lance", "cost": {"clockwork_core": 2, "ley_crystal": 4, "scrap_gear": 4}, "gold": 240, "rank": 1},
	# ---------------------------------------------------------------- Emberwick Forge
	"copper_ingot": {"station": "forge", "cat": "Smelting", "gives": {"copper_ingot": 1}, "cost": {"copper_ore": 2}, "gold": 0, "rank": 1},
	"iron_ingot": {"station": "forge", "cat": "Smelting", "gives": {"iron_ingot": 1}, "cost": {"iron_ore": 2}, "gold": 0, "rank": 1},
	"brass_ingot": {"station": "forge", "cat": "Smelting", "gives": {"brass_ingot": 2}, "cost": {"copper_ingot": 1, "scrap_gear": 2}, "gold": 4, "rank": 2},
	"steel_plate": {"station": "forge", "cat": "Smelting", "gives": {"steel_plate": 1}, "cost": {"iron_ingot": 2, "ember_essence": 1}, "gold": 6, "rank": 3},
	"runesteel_ingot": {"station": "forge", "cat": "Smelting", "gives": {"runesteel_ingot": 1}, "cost": {"steel_plate": 1, "rune_shard": 2, "ley_crystal": 1}, "gold": 15, "rank": 5},
	"runesteel_bulk": {"station": "forge", "cat": "Smelting", "gives": {"runesteel_ingot": 3}, "cost": {"steel_plate": 2, "rune_shard": 4, "ley_crystal": 2, "ember_essence": 1}, "gold": 30, "rank": 10},
	"w_thunder_wrench": {"station": "forge", "cat": "Smithing", "weapon": "thunder_wrench", "cost": {"scrap_gear": 5, "rune_shard": 2}, "gold": 120, "rank": 1},
	"w_boom_mortar": {"station": "forge", "cat": "Smithing", "weapon": "boom_mortar", "cost": {"steel_plate": 2, "spark_bomb": 3, "brass_ingot": 1}, "gold": 150, "rank": 3},
	"w_steam_hammer": {"station": "forge", "cat": "Smithing", "weapon": "steam_hammer", "cost": {"steel_plate": 3, "spring_coil": 2, "ember_essence": 2}, "gold": 220, "rank": 5, "schematic": true},
	"w_gatling": {"station": "forge", "cat": "Smithing", "weapon": "gatling", "cost": {"steel_plate": 4, "brass_ingot": 4, "spring_coil": 3, "clockwork_core": 1}, "gold": 360, "rank": 6, "schematic": true},
	"w_runeblade": {"station": "forge", "cat": "Smithing", "weapon": "runeblade", "cost": {"runesteel_ingot": 2, "focus_gem": 1, "arcane_thread": 1}, "gold": 300, "rank": 6, "schematic": true},
	# ---------------------------------------------------------------- Alchemist's Table
	"health_tonic": {"station": "alchemy", "field": true, "cat": "Tonics", "gives": {"health_tonic": 1}, "cost": {"ember_essence": 1}, "gold": 8, "rank": 1},
	"health_tonic_glowcap": {"station": "alchemy", "field": true, "cat": "Tonics", "gives": {"health_tonic": 2}, "cost": {"glowcap": 3}, "gold": 4, "rank": 1},
	"mana_draught": {"station": "alchemy", "cat": "Tonics", "gives": {"mana_draught": 1}, "cost": {"ley_crystal": 1}, "gold": 6, "rank": 1},
	"greater_health_tonic": {"station": "alchemy", "cat": "Tonics", "gives": {"greater_health_tonic": 1}, "cost": {"glowcap": 2, "sunpetal": 1, "ember_essence": 1}, "gold": 12, "rank": 2},
	"greater_mana_draught": {"station": "alchemy", "cat": "Tonics", "gives": {"greater_mana_draught": 1}, "cost": {"ley_crystal": 2, "glowcap": 1, "sunpetal": 1}, "gold": 12, "rank": 3},
	"regen_salve": {"station": "alchemy", "cat": "Tonics", "gives": {"regen_salve": 1}, "cost": {"glowcap": 2, "reed_fiber": 2}, "gold": 8, "rank": 2},
	"swift_elixir": {"station": "alchemy", "cat": "Elixirs", "gives": {"swift_elixir": 1}, "cost": {"shade_silk": 1, "ley_crystal": 1}, "gold": 15, "rank": 1},
	"iron_tonic": {"station": "alchemy", "cat": "Elixirs", "gives": {"iron_tonic": 1}, "cost": {"rune_shard": 1, "scrap_gear": 2}, "gold": 15, "rank": 1},
	"skyleap_draught": {"station": "alchemy", "cat": "Elixirs", "gives": {"skyleap_draught": 1}, "cost": {"sunpetal": 2, "shade_silk": 1}, "gold": 14, "rank": 3},
	"focus_incense": {"station": "alchemy", "cat": "Elixirs", "gives": {"focus_incense": 2}, "cost": {"rune_ink": 1, "sunpetal": 1}, "gold": 14, "rank": 3},
	"berserker_brew": {"station": "alchemy", "cat": "Elixirs", "gives": {"berserker_brew": 1}, "cost": {"ember_essence": 2, "sunpetal": 1, "glowcap": 1}, "gold": 20, "rank": 4, "schematic": true},
	"fortune_tonic": {"station": "alchemy", "cat": "Elixirs", "gives": {"fortune_tonic": 1}, "cost": {"sunpetal": 3, "ley_crystal": 2}, "gold": 45, "rank": 4, "schematic": true},
	"frost_bomb": {"station": "alchemy", "cat": "Bombs", "gives": {"frost_bomb": 2}, "cost": {"glowcap": 1, "ley_crystal": 2, "iron_ore": 1}, "gold": 12, "rank": 3},
	# ---------------------------------------------------------------- Enchanter's Altar
	"rune_ink": {"station": "altar", "cat": "Reagents", "gives": {"rune_ink": 2}, "cost": {"rune_shard": 1, "glowcap": 1}, "gold": 4, "rank": 1},
	"focus_gem": {"station": "altar", "cat": "Reagents", "gives": {"focus_gem": 1}, "cost": {"ley_crystal": 3, "rune_shard": 1}, "gold": 10, "rank": 2},
	"w_arcane_bolt": {"station": "altar", "cat": "Spell foci", "weapon": "arcane_bolt", "cost": {"rune_ink": 1, "ley_crystal": 2}, "gold": 30, "rank": 1},
	"w_ember_wand": {"station": "altar", "cat": "Spell foci", "weapon": "ember_wand", "cost": {"focus_gem": 1, "ember_essence": 3, "copper_ingot": 1}, "gold": 60, "rank": 2},
	"w_frost_wand": {"station": "altar", "cat": "Spell foci", "weapon": "frost_wand", "cost": {"focus_gem": 1, "glowcap": 2, "ley_crystal": 3}, "gold": 90, "rank": 2},
	"w_fireball": {"station": "altar", "cat": "Spell foci", "weapon": "fireball", "cost": {"ember_essence": 4, "rune_shard": 2}, "gold": 140, "rank": 1},
	"w_chain_lightning": {"station": "altar", "cat": "Spell foci", "weapon": "chain_lightning", "cost": {"ley_crystal": 4, "shade_silk": 2, "rune_shard": 2}, "gold": 200, "rank": 1},
	"w_mending_ward": {"station": "altar", "cat": "Spell foci", "weapon": "mending_ward", "cost": {"focus_gem": 1, "glowcap": 3, "sunpetal": 2}, "gold": 160, "rank": 3},
	"w_seeker_tome": {"station": "altar", "cat": "Spell foci", "weapon": "seeker_tome", "cost": {"arcane_thread": 2, "rune_ink": 3, "shade_silk": 2}, "gold": 220, "rank": 5, "schematic": true},
	"w_void_orb": {"station": "altar", "cat": "Spell foci", "weapon": "void_orb", "cost": {"focus_gem": 2, "shade_silk": 4, "runesteel_ingot": 1}, "gold": 320, "rank": 7, "schematic": true},
	"w_sun_scepter": {"station": "altar", "cat": "Spell foci", "weapon": "sun_scepter", "cost": {"focus_gem": 2, "ley_lens": 1, "brass_ingot": 3, "sunpetal": 4}, "gold": 340, "rank": 7, "schematic": true},
	# ---------------------------------------------------------------- Tailor's Loom
	"spun_cloth": {"station": "loom", "cat": "Weaving", "gives": {"spun_cloth": 1}, "cost": {"reed_fiber": 3}, "gold": 0, "rank": 1},
	"arcane_thread": {"station": "loom", "cat": "Weaving", "gives": {"arcane_thread": 2}, "cost": {"shade_silk": 1, "ley_crystal": 1}, "gold": 4, "rank": 2},
	"pouch_cloth": {"station": "loom", "field": true, "cat": "Pouches", "gives": {"pouch_cloth": 1}, "cost": {"spun_cloth": 2}, "gold": 10, "rank": 1},
	"pouch_leather": {"station": "loom", "cat": "Pouches", "gives": {"pouch_leather": 1}, "cost": {"spun_cloth": 3, "iron_ingot": 1}, "gold": 30, "rank": 2},
	"pouch_brass": {"station": "loom", "cat": "Pouches", "gives": {"pouch_brass": 1}, "cost": {"spun_cloth": 3, "brass_ingot": 2}, "gold": 60, "rank": 3},
	"pouch_rune": {"station": "loom", "cat": "Pouches", "gives": {"pouch_rune": 1}, "cost": {"spun_cloth": 3, "arcane_thread": 2, "rune_ink": 1}, "gold": 120, "rank": 4},
	"pouch_scavenger": {"station": "loom", "cat": "Pouches", "gives": {"pouch_scavenger": 1}, "cost": {"spun_cloth": 4, "spring_coil": 2, "scrap_gear": 4}, "gold": 80, "rank": 3, "schematic": true},
	"pouch_alchemist": {"station": "loom", "cat": "Pouches", "gives": {"pouch_alchemist": 1}, "cost": {"spun_cloth": 3, "glowcap": 2, "ley_crystal": 1}, "gold": 90, "rank": 3, "schematic": true},
	"pouch_prospector": {"station": "loom", "cat": "Pouches", "gives": {"pouch_prospector": 1}, "cost": {"spun_cloth": 4, "iron_ingot": 2, "copper_ore": 3}, "gold": 90, "rank": 3, "schematic": true},
	"pouch_ley": {"station": "loom", "cat": "Pouches", "gives": {"pouch_ley": 1}, "cost": {"arcane_thread": 4, "ley_crystal": 4, "brass_ingot": 2}, "gold": 220, "rank": 6, "schematic": true},
	"pouch_void": {"station": "loom", "cat": "Pouches", "gives": {"pouch_void": 1}, "cost": {"arcane_thread": 6, "focus_gem": 2, "clockwork_core": 1, "shade_silk": 4}, "gold": 400, "rank": 9, "schematic": true},
	"pouch_brass_fine": {"station": "loom", "cat": "Pouches", "gives": {"pouch_brass": 2}, "cost": {"spun_cloth": 5, "brass_ingot": 3}, "gold": 90, "rank": 8},
}

# Schematic prices at vendors (recipe id -> gold). Others come from chests, vaults, Champions and quests.
const SCHEMATIC_PRICES := {
	"w_longshot": 420, "w_flamer": 380, "w_steam_hammer": 400, "w_seeker_tome": 420, "fortune_tonic": 300,
	"berserker_brew": 260, "pouch_alchemist": 320, "pouch_scavenger": 300, "pouch_prospector": 320,
}

const UPGRADES := {
	"vitality": {"name": "Heartstone Amulet", "prices": [120, 300, 600], "icon": "icon_upgrade_vitality",
		"desc": "+30 max health per tier."},
	"arcana": {"name": "Rune Focus", "prices": [200, 450, 800], "icon": "icon_upgrade_arcana",
		"desc": "+15% magic weapon damage per tier."},
	"engineering": {"name": "Gunsmith's Kit", "prices": [200, 450, 800], "icon": "icon_upgrade_engineering",
		"desc": "+15% tech weapon and turret damage per tier."},
	"capacity": {"name": "Workshop Permit", "prices": [150, 350, 700], "icon": "icon_upgrade_capacity",
		"desc": "+15 contraption parts allowed in the world per tier."},
	"mana_regen": {"name": "Mana Battery", "prices": [100, 250, 500], "icon": "icon_upgrade_mana_regen",
		"desc": "+50% mana regeneration per tier."},
}

# Vendors: which shop tabs each NPC offers. "featured" = rotating rolled stock, "sell" = sell to them.
# "weapons"/"spells" list the base weapons marked "sold"; pouches/materials/schematics list ids.
const VENDORS := {
	"odda": {"title": "Odda's Workshop", "tabs": ["parts", "pouches:pouch_cloth,pouch_leather,pouch_brass",
		"materials:copper_ore,iron_ore,reed_fiber,spun_cloth,copper_ingot,iron_ingot",
		"schematics:pouch_scavenger,pouch_alchemist,pouch_prospector", "upgrades:capacity,vitality", "sell"]},
	"lirael": {"title": "Lirael's Arcanum", "tabs": ["spells", "featured:spell", "schematics:w_seeker_tome,fortune_tonic,berserker_brew",
		"materials:glowcap,sunpetal,rune_ink,ley_crystal", "upgrades:arcana,mana_regen",
		"consumables:mana_draught,greater_mana_draught,swift_elixir,focus_incense,regen_salve", "sell"]},
	"gus": {"title": "Gus's Gizmos", "tabs": ["weapons", "featured:gun", "schematics:w_longshot,w_flamer,w_steam_hammer",
		"materials:scrap_gear,spring_coil,power_cell,brass_ingot", "upgrades:engineering",
		"consumables:health_tonic,mana_draught,spark_bomb,shock_jar,iron_tonic,weapon_oil,repair_kit,treasure_map", "sell"]},
}

# ------------------------------------------------------------------------------------------ talents
# One talent point per level (from level 2). Each talent has ranks; "level" is the player level needed.
const TALENT_TREES := {
	"tinker": {"name": "Tinker", "color": Color("e0a24a"), "desc": "Guns, gadgets and good engineering."},
	"arcanist": {"name": "Arcanist", "color": Color("a77bff"), "desc": "Spells, mana and the elements."},
	"wayfarer": {"name": "Wayfarer", "color": Color("5fc98a"), "desc": "Toughness, travel and treasure."},
}
const TALENTS := {
	"gunsmith": {"tree": "tinker", "name": "Gunsmith", "ranks": 5, "level": 2, "desc": "+6% tech weapon damage per rank."},
	"quick_hands": {"tree": "tinker", "name": "Quick Hands", "ranks": 3, "level": 2, "desc": "Reload 10% faster per rank."},
	"deep_pockets": {"tree": "tinker", "name": "Deep Pockets", "ranks": 3, "level": 4, "desc": "+2 pack slots per rank."},
	"scrapper": {"tree": "tinker", "name": "Scrapper", "ranks": 2, "level": 6, "desc": "+25% chance per rank of a bonus material when salvaging or scavenging."},
	"master_artisan": {"tree": "tinker", "name": "Master Artisan", "ranks": 3, "level": 8, "desc": "+15% crafting experience per rank, and crafted weapons roll rarer."},
	"spellweaver": {"tree": "arcanist", "name": "Spellweaver", "ranks": 5, "level": 2, "desc": "+6% magic weapon damage per rank."},
	"mana_well": {"tree": "arcanist", "name": "Mana Well", "ranks": 3, "level": 2, "desc": "+20 max mana per rank."},
	"flow": {"tree": "arcanist", "name": "Ley Flow", "ranks": 3, "level": 4, "desc": "+15% mana regeneration per rank."},
	"elementalist": {"tree": "arcanist", "name": "Elementalist", "ranks": 3, "level": 6, "desc": "Burn and chill are 15% stronger and last longer per rank."},
	"siphon": {"tree": "arcanist", "name": "Siphon", "ranks": 2, "level": 8, "desc": "Magic weapons heal you for 2% of their damage per rank."},
	"toughness": {"tree": "wayfarer", "name": "Toughness", "ranks": 5, "level": 2, "desc": "+15 max health per rank."},
	"fleet_foot": {"tree": "wayfarer", "name": "Fleet Foot", "ranks": 3, "level": 2, "desc": "+4% movement speed per rank."},
	"forager": {"tree": "wayfarer", "name": "Forager", "ranks": 3, "level": 4, "desc": "+30% chance per rank of an extra yield when gathering."},
	"treasure_hunter": {"tree": "wayfarer", "name": "Treasure Hunter", "ranks": 3, "level": 6, "desc": "+10% gold per rank, and loot rolls rarer."},
	"second_wind": {"tree": "wayfarer", "name": "Second Wind", "ranks": 2, "level": 8, "desc": "Health regenerates 50% faster per rank when out of combat."},
}
# Every 5 levels: a milestone cache (gold, a Rare+ weapon and an unknown schematic).
const LEVEL_MILESTONES := [5, 10, 15, 20, 25, 30]

# ------------------------------------------------------------------------------------------ gathering
# HarvestNode kinds. count: yield range; regrow: seconds until it refills.
const HARVEST := {
	"crystal": {"name": "Ley Crystal Cluster", "verb": "Harvest", "model": "node_ley_crystal", "item": "ley_crystal",
		"count": [2, 3], "regrow": 240.0, "sfx": "crystal_harvest", "light": Color(0.35, 0.95, 0.88), "radius": 0.65, "height": 1.5},
	"scrap": {"name": "Scrap Heap", "verb": "Scavenge", "model": "", "item": "scrap_gear", "count": [2, 4], "regrow": 180.0,
		"sfx": "scavenge"},
	"ore_copper": {"name": "Copper Vein", "verb": "Mine", "model": "node_ore_copper", "item": "copper_ore", "count": [2, 3],
		"regrow": 260.0, "sfx": "mine_ore", "radius": 0.75, "height": 1.2, "color": Color(0.95, 0.55, 0.3)},
	"ore_iron": {"name": "Iron Vein", "verb": "Mine", "model": "node_ore_iron", "item": "iron_ore", "count": [2, 3],
		"regrow": 260.0, "sfx": "mine_ore", "radius": 0.75, "height": 1.2, "color": Color(0.6, 0.42, 0.36)},
	"glowcap": {"name": "Glowcap Patch", "verb": "Gather", "model": "node_glowcap", "item": "glowcap", "count": [2, 3],
		"regrow": 200.0, "sfx": "herb_pick", "light": Color(0.3, 0.85, 1.0), "radius": 0.55, "height": 0.9, "color": Color(0.3, 0.85, 1.0)},
	"sunpetal": {"name": "Sunpetal Blooms", "verb": "Pick", "model": "node_sunpetal", "item": "sunpetal", "count": [1, 2],
		"regrow": 200.0, "sfx": "herb_pick", "radius": 0.45, "height": 0.9, "color": Color(1.0, 0.82, 0.25)},
	"reeds": {"name": "Reed Clump", "verb": "Cut", "model": "node_reeds", "item": "reed_fiber", "count": [2, 4],
		"regrow": 180.0, "sfx": "herb_pick", "radius": 0.5, "height": 1.6, "color": Color(0.75, 0.8, 0.35)},
}

# ------------------------------------------------------------------------------------------ enemies
# resist: multipliers per damage type (arcane, fire, shock, kinetic, frost). loot: item -> drop chance.
const ENEMIES := {
	"wisp": {"name": "Ember Wisp", "faction": "magic", "hp": 35.0, "speed": 7.0, "xp": 14, "gold": [3, 6],
		"resist": {"arcane": 0.6, "fire": 0.0, "shock": 1.0, "kinetic": 1.3, "frost": 1.7}, "flying": true,
		"loot": {"ember_essence": 0.45}, "model": "enemy_wisp"},
	"golem": {"name": "Rune Golem", "faction": "magic", "hp": 260.0, "speed": 2.6, "xp": 70, "gold": [18, 28],
		"resist": {"arcane": 0.5, "fire": 0.6, "shock": 0.8, "kinetic": 1.3, "frost": 0.9}, "flying": false,
		"loot": {"rune_shard": 0.8, "ley_crystal": 0.35, "iron_ore": 0.3}, "model": "enemy_golem"},
	"wraith": {"name": "Shade Wraith", "faction": "magic", "hp": 90.0, "speed": 5.5, "xp": 32, "gold": [8, 14],
		"resist": {"arcane": 0.75, "fire": 1.0, "shock": 1.2, "kinetic": 0.55, "frost": 1.0}, "flying": true,
		"loot": {"shade_silk": 0.6}, "model": "enemy_wraith"},
	"cultist": {"name": "Choir Cultist", "faction": "magic", "hp": 75.0, "speed": 3.8, "xp": 26, "gold": [7, 12],
		"resist": {"arcane": 0.75, "fire": 1.25, "shock": 1.0, "kinetic": 1.0, "frost": 1.1}, "flying": false,
		"loot": {"rune_shard": 0.2, "shade_silk": 0.25, "glowcap": 0.15, "rune_ink": 0.06}, "model": "enemy_cultist"},
	"archon": {"name": "The Hollow Archon", "faction": "magic", "hp": 1400.0, "speed": 3.0, "xp": 600, "gold": [250, 300],
		"resist": {"arcane": 0.5, "fire": 1.0, "shock": 1.0, "kinetic": 1.2, "frost": 0.9}, "flying": false, "boss": true,
		"loot": {}, "boss_loot": {"rune_shard": 4, "shade_silk": 3, "focus_gem": 2, "ley_key": 1}, "model": "enemy_cultist"},
	"drone": {"name": "Scout Drone", "faction": "tech", "hp": 45.0, "speed": 8.0, "xp": 16, "gold": [4, 7],
		"resist": {"arcane": 1.25, "fire": 1.0, "shock": 2.0, "kinetic": 0.75, "frost": 1.0}, "flying": true,
		"loot": {"scrap_gear": 0.55, "copper_ore": 0.12, "clockwork_core": 0.04}, "model": "enemy_drone"},
	"sentry": {"name": "Sentry Turret", "faction": "tech", "hp": 150.0, "speed": 0.0, "xp": 40, "gold": [10, 16],
		"resist": {"arcane": 1.25, "fire": 0.75, "shock": 2.0, "kinetic": 0.5, "frost": 0.8}, "flying": false, "static": true,
		"loot": {"scrap_gear": 0.9, "clockwork_core": 0.3, "spring_coil": 0.25, "power_cell": 0.08}, "model": "enemy_sentry"},
	"crawler": {"name": "Clank Crawler", "faction": "tech", "hp": 55.0, "speed": 7.5, "xp": 20, "gold": [5, 9],
		"resist": {"arcane": 1.25, "fire": 1.0, "shock": 1.75, "kinetic": 1.0, "frost": 1.3}, "flying": false,
		"loot": {"scrap_gear": 0.4, "iron_ore": 0.15, "clockwork_core": 0.06}, "model": "enemy_crawler"},
	"ironclad": {"name": "Ironclad Warwalker", "faction": "tech", "hp": 1600.0, "speed": 2.4, "xp": 650, "gold": [250, 320],
		"resist": {"arcane": 1.0, "fire": 0.75, "shock": 1.5, "kinetic": 0.5, "frost": 0.75}, "flying": false, "boss": true,
		"loot": {}, "boss_loot": {"clockwork_core": 3, "scrap_gear": 6, "steel_plate": 2, "ley_key": 1}, "model": "enemy_ironclad"},
}

# Weapon drops: chance per kill and luck (pushes rarity up) by enemy tier.
const DROP_CHANCE := {"normal": 0.05, "elite": 0.5, "boss": 1.0}
const DROP_LUCK := {"normal": 0.0, "elite": 1.0, "boss": 2.5}
const ELITE_CHANCE := 0.09
const SCHEMATIC_DROP := {"normal": 0.004, "elite": 0.12, "boss": 1.0}

# Enemy levels: HP, damage, XP and gold scale with level; loot rolls higher-level weapons.
const ENEMY_HP_PER_LEVEL := 0.12
const ENEMY_DMG_PER_LEVEL := 0.085
const ENEMY_XP_PER_LEVEL := 0.12
const ENEMY_GOLD_PER_LEVEL := 0.08


func part(id: String) -> Dictionary:
	return PARTS.get(id, {})


## Tools and weapon bases share this lookup (legacy name).
func equipment(id: String) -> Dictionary:
	if TOOLS.has(id):
		return TOOLS[id]
	return WEAPONS.get(id, {})


func weapon_base(id: String) -> Dictionary:
	return WEAPONS.get(id, {})


func weapon_school(base: String) -> String:
	var d := weapon_base(base)
	if d.has("school"):
		return str(d["school"])
	return "magic" if d.get("kind", "") == "spell" else "tech"


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


## Icon for any stackable item id (consumable, material, key, pouch, schematic).
func stack_icon(id: String) -> Texture2D:
	var d := stack_def(id)
	return item_icon(str(d.get("model", ""))) if not d.is_empty() else null


func upgrade_icon(id: String) -> Texture2D:
	return MaterialLib.texture(UI_ICON % UPGRADES[id]["icon"])


func display_name(id: String) -> String:
	if PARTS.has(id):
		return PARTS[id]["name"]
	if TOOLS.has(id):
		return TOOLS[id]["name"]
	if WEAPONS.has(id):
		return WEAPONS[id]["name"]
	if CONSUMABLES.has(id):
		return CONSUMABLES[id]["name"]
	if ITEMS.has(id):
		return ITEMS[id]["name"]
	if POUCHES.has(id):
		return POUCHES[id]["name"]
	if is_schematic(id):
		return "Schematic: " + recipe_name(schematic_recipe(id))
	if UPGRADES.has(id):
		return UPGRADES[id]["name"]
	if ENEMIES.has(id):
		return ENEMIES[id]["name"]
	if TALENTS.has(id):
		return TALENTS[id]["name"]
	if STATIONS.has(id):
		return STATIONS[id]["name"]
	return id.capitalize()


## Consumable, material/key, pouch or schematic definition.
func stack_def(id: String) -> Dictionary:
	if CONSUMABLES.has(id):
		return CONSUMABLES[id]
	if POUCHES.has(id):
		return POUCHES[id]
	if is_schematic(id):
		var rid := schematic_recipe(id)
		return {"name": display_name(id), "model": "item_schematic", "value": 25, "key": true, "schematic": rid,
			"desc": "Teaches you to craft %s (%s, Artisan rank %d)." % [recipe_name(rid), STATIONS[RECIPES[rid]["station"]]["name"], int(RECIPES[rid].get("rank", 1))]}
	return ITEMS.get(id, {})


func is_consumable(id: String) -> bool:
	return CONSUMABLES.has(id)


func is_pouch(id: String) -> bool:
	return POUCHES.has(id)


func is_material(id: String) -> bool:
	return ITEMS.has(id) and not bool(ITEMS[id].get("key", false))


func is_key_item(id: String) -> bool:
	return bool(ITEMS.get(id, {}).get("key", false))


func is_schematic(id: String) -> bool:
	return id.begins_with("sch_") and RECIPES.has(id.substr(4))


func schematic_recipe(id: String) -> String:
	return id.substr(4) if id.begins_with("sch_") else ""


func schematic_id(recipe_id: String) -> String:
	return "sch_" + recipe_id


## "consumable" | "material" | "pouch" | "key" | "schematic" | ""
func item_category(id: String) -> String:
	if CONSUMABLES.has(id):
		return "consumable"
	if POUCHES.has(id):
		return "pouch"
	if is_schematic(id):
		return "schematic"
	if is_key_item(id):
		return "key"
	if ITEMS.has(id):
		return "material"
	return ""


## Key items and schematics ride on your key ring and take no pack space.
func takes_space(id: String) -> bool:
	var c := item_category(id)
	return c != "key" and c != "schematic" and c != ""


## How many of an item one pack slot holds (before pouch perks).
func stack_size(id: String) -> int:
	if CONSUMABLES.has(id):
		return CONSUMABLE_STACK
	if POUCHES.has(id):
		return 1
	var d: Dictionary = ITEMS.get(id, {})
	if d.is_empty():
		return 1
	return int(STACK_SIZE.get(int(d.get("tier", 1)), 30))


## Gold a vendor pays for one of a stackable item.
func stack_value(id: String) -> int:
	if CONSUMABLES.has(id):
		return maxi(1, int(CONSUMABLES[id]["price"]) / 2)
	if POUCHES.has(id):
		var p: Dictionary = POUCHES[id]
		return maxi(20, int(p.get("price", 0)) / 2) if int(p.get("price", 0)) > 0 else 40 * (int(p["slots"]) - 1)
	if is_schematic(id):
		return 25
	return int(ITEMS.get(id, {}).get("value", 1))


## Gold a vendor charges for one material / pouch / schematic.
func buy_price(id: String) -> int:
	if CONSUMABLES.has(id):
		return int(CONSUMABLES[id]["price"])
	if POUCHES.has(id):
		return int(POUCHES[id].get("price", 0))
	if is_schematic(id):
		return int(SCHEMATIC_PRICES.get(schematic_recipe(id), 300))
	return int(ceil(stack_value(id) * 2.5))


func pouch_def(id: String) -> Dictionary:
	return POUCHES.get(id, {})


# ------------------------------------------------------------------------------------------ recipes
func recipe(id: String) -> Dictionary:
	return RECIPES.get(id, {})


## What a recipe makes: {"id", "count", "type": "weapon" | "item"}.
func recipe_output(rid: String) -> Dictionary:
	var r := recipe(rid)
	if r.has("weapon"):
		return {"id": str(r["weapon"]), "count": 1, "type": "weapon"}
	var gives: Dictionary = r.get("gives", {})
	if gives.is_empty():
		return {}
	var gid: String = gives.keys()[0]
	return {"id": gid, "count": int(gives[gid]), "type": "item"}


func recipe_name(rid: String) -> String:
	var o := recipe_output(rid)
	if o.is_empty():
		return rid.capitalize()
	return display_name(str(o["id"]))


func recipe_icon(rid: String) -> Texture2D:
	var o := recipe_output(rid)
	if o.is_empty():
		return null
	return equipment_icon(str(o["id"])) if o["type"] == "weapon" else stack_icon(str(o["id"]))


## Crafting experience a recipe gives.
func recipe_xp(rid: String) -> int:
	var r := recipe(rid)
	return int(r.get("xp", 5 + 5 * int(r.get("rank", 1))))


func recipes_for(station: String) -> Array:
	var out := []
	for rid in RECIPES:
		var r: Dictionary = RECIPES[rid]
		if r["station"] == station or (station == "field" and bool(r.get("field", false))):
			out.append(rid)
	return out


func schematic_recipes() -> Array:
	var out := []
	for rid in RECIPES:
		if bool(RECIPES[rid].get("schematic", false)):
			out.append(rid)
	return out


func artisan_rank_for(xp: int) -> int:
	var r := 1
	for i in ARTISAN_XP.size():
		if xp >= int(ARTISAN_XP[i]):
			r = i + 1
	return r


func artisan_title(rank: int) -> String:
	return ARTISAN_TITLES[clampi(rank, 1, ARTISAN_TITLES.size()) - 1]


# ------------------------------------------------------------------------------------------ weapon instances
## A new weapon instance: {uid (set by Game.add_weapon), base, rarity, level, perks, fav, new}.
func make_weapon(base: String, rarity: int = 0, perks: Array = [], level: int = 1) -> Dictionary:
	if not WEAPONS.has(base):
		base = random_weapon_base()
	rarity = clampi(rarity, 0, RARITY_NAMES.size() - 1)
	var w := {"uid": 0, "base": base, "rarity": rarity, "level": clampi(level, 1, MAX_WEAPON_LEVEL), "perks": [], "fav": false, "new": true}
	if perks.is_empty():
		w["perks"] = roll_perks(base, RARITY_PERKS[rarity])
	else:
		w["perks"] = perks.duplicate()
	return w


func roll_perks(base: String, count: int, exclude: Array = []) -> Array:
	var d: Dictionary = WEAPONS[base]
	var kind: String = d["kind"]
	var pool: Array = []
	for p in PERKS:
		if not kind in PERKS[p]["kinds"] or p in exclude:
			continue
		# a heal-only spell has no use for damage perks
		if base == "mending_ward" and p not in ["hasty", "frugal"]:
			continue
		if p == "deep" and str(d.get("fire", "")) == "charge":
			continue
		if p == "hasty" and str(d.get("cast", "")) == "beam":
			continue
		if p == "searing" and d.has("burn"):
			continue
		if p == "chilling" and d.has("chill"):
			continue
		pool.append(p)
	pool.shuffle()
	return pool.slice(0, mini(count, pool.size()))


## Random rarity. luck >= 0 pushes the odds toward rarer tiers; floor is the minimum tier.
func roll_rarity(luck: float = 0.0, floor_tier: int = 0) -> int:
	var weights: Array = []
	var total := 0.0
	for i in RARITY_WEIGHTS.size():
		var w: float = RARITY_WEIGHTS[i] * pow(1.0 + luck, float(i)) if i >= floor_tier else 0.0
		weights.append(w)
		total += w
	var r := randf() * total
	for i in weights.size():
		r -= weights[i]
		if r <= 0.0:
			return i
	return weights.size() - 1


## Random weapon base for loot. faction "magic"/"tech" favours that school; kind ("gun" includes
## melee) or school ("school:tech" / "school:magic") filter.
func random_weapon_base(faction: String = "", kind: String = "") -> String:
	var total := 0.0
	var opts := {}
	var school_filter := kind.substr(7) if kind.begins_with("school:") else ""
	for id in WEAPONS:
		var d: Dictionary = WEAPONS[id]
		var sch := weapon_school(id)
		if school_filter != "":
			if sch != school_filter:
				continue
		elif kind != "" and d["kind"] != kind and not (kind == "gun" and d["kind"] == "melee" and sch == "tech"):
			continue
		var w := float(d.get("drop", 1.0))
		if faction == "magic" and sch == "magic":
			w *= 2.0
		elif faction == "tech" and sch == "tech":
			w *= 1.7
		opts[id] = w
		total += w
	var r := randf() * total
	for id in opts:
		r -= opts[id]
		if r <= 0.0:
			return id
	return opts.keys()[0] if not opts.is_empty() else "arc_pistol"


func roll_weapon(luck: float = 0.0, floor_tier: int = 0, faction: String = "", kind: String = "", level: int = 1) -> Dictionary:
	return make_weapon(random_weapon_base(faction, kind), roll_rarity(luck, floor_tier), [], level)


## Weapon level a drop from a foe of `enemy_level` rolls at (+0 .. +7).
func drop_level(enemy_level: int) -> int:
	var base := 1 + (maxi(enemy_level, 1) - 1) / 4
	if randf() < 0.3:
		base += 1
	return clampi(base, 1, MAX_WEAPON_LEVEL - 2)


func weapon_name(w: Dictionary) -> String:
	var base: String = w.get("base", "")
	var bd := weapon_base(base)
	var nm: String = bd.get("name", base.capitalize())
	var rarity := int(w.get("rarity", 0))
	var perks: Array = w.get("perks", [])
	if rarity >= 4 and LEGENDARY_NAMES.has(base):
		nm = LEGENDARY_NAMES[base]
	elif perks.size() >= 1 and PERKS.has(perks[0]):
		nm = "%s %s" % [PERKS[perks[0]]["name"], nm]
		if perks.size() >= 2 and PERKS.has(perks[1]):
			nm += " " + str(PERKS[perks[1]]["suffix"])
	var lvl := int(w.get("level", 1))
	if lvl > 1:
		nm += " +%d" % (lvl - 1)
	return nm


func weapon_icon(w: Dictionary) -> Texture2D:
	var bd := weapon_base(str(w.get("base", "")))
	# spell foci show their painted spell icon, guns their rendered model icon
	return equipment_icon(str(w.get("base", ""))) if not bd.is_empty() else null


func rarity_color(rarity: int) -> Color:
	return RARITY_COLORS[clampi(rarity, 0, RARITY_COLORS.size() - 1)]


## Final stats of a weapon instance: base stats x rarity x level, then perks applied.
## School bonuses (Game.school_mult) and the player's buffs are applied when firing.
func weapon_stats(w: Dictionary) -> Dictionary:
	var base: String = w.get("base", "")
	var s: Dictionary = weapon_base(base).duplicate(true)
	if s.is_empty():
		return s
	s["school"] = weapon_school(base)
	var rarity := clampi(int(w.get("rarity", 0)), 0, RARITY_POWER.size() - 1)
	var lvl := clampi(int(w.get("level", 1)), 1, MAX_WEAPON_LEVEL)
	var mult: float = RARITY_POWER[rarity] * (1.0 + 0.1 * float(lvl - 1))
	for k in ["damage", "splash", "zap", "burn", "wave", "heal", "repair"]:
		if s.has(k):
			s[k] = float(s[k]) * mult
	s["crit_chance"] = float(s.get("crit", 0.0))
	s["leech"] = 0.0
	s["volatile"] = 0.0
	s["arc_chance"] = 0.0
	s["burn_chance"] = 1.0 if s.has("burn") else 0.0
	s["chill_chance"] = 1.0 if s.has("chill") else 0.0
	s["vs_magic"] = 1.0
	s["vs_tech"] = 1.0
	for p in w.get("perks", []):
		match p:
			"brutal":
				for k in ["damage", "splash", "zap", "burn", "wave"]:
					if s.has(k):
						s[k] = float(s[k]) * 1.18
			"hasty":
				if s.has("fire_rate"):
					s["fire_rate"] = float(s["fire_rate"]) * 1.2
				if s.has("cooldown") and str(s.get("cast", "")) != "beam":
					s["cooldown"] = float(s["cooldown"]) / 1.2
				if s.has("charge"):
					s["charge"] = float(s["charge"]) / 1.2
				if s.has("swing_time"):
					s["swing_time"] = float(s["swing_time"]) / 1.2
				if s.has("spinup"):
					s["spinup"] = float(s["spinup"]) / 1.2
			"deep":
				if s.has("mag"):
					s["mag"] = int(ceil(float(s["mag"]) * 1.5))
			"quick":
				if s.has("reload"):
					s["reload"] = float(s["reload"]) * 0.65
			"steady":
				if s.has("spread"):
					s["spread"] = float(s["spread"]) * 0.5
				if s.has("cone"):
					s["cone"] = float(s["cone"]) * 0.8
				if s.has("range"):
					s["range"] = float(s["range"]) * 1.2
			"frugal":
				if s.has("mana"):
					s["mana"] = float(s["mana"]) * 0.7
				if s.has("wave_mana"):
					s["wave_mana"] = float(s["wave_mana"]) * 0.7
			"keen":
				s["crit_chance"] = float(s["crit_chance"]) + 0.15
			"leech":
				s["leech"] = 0.05
			"volatile":
				s["volatile"] = 0.12
			"arcing":
				s["arc_chance"] = 0.15
			"hexbane":
				s["vs_magic"] = 1.3
			"gearbane":
				s["vs_tech"] = 1.3
			"searing":
				s["burn_chance"] = maxf(float(s["burn_chance"]), 0.2)
				if not s.has("burn"):
					s["burn"] = maxf(float(s.get("damage", 10.0)) * 0.35, 3.0)
			"chilling":
				s["chill_chance"] = maxf(float(s["chill_chance"]), 0.2)
				if not s.has("chill"):
					s["chill"] = 0.4
	s["rarity"] = rarity
	s["level"] = lvl
	s["base"] = base
	return s


## Damage per second (rough, for comparing weapons in the inventory).
func weapon_dps(s: Dictionary) -> float:
	var dmg := float(s.get("damage", 0.0)) * float(s.get("pellets", 1)) * float(s.get("shards", 1)) * float(s.get("seekers", 1))
	dmg += float(s.get("splash", 0.0)) * 0.5 + float(s.get("zap", 0.0))
	dmg *= 1.0 + float(s.get("crit_chance", 0.0))
	# burn refreshes instead of stacking: it adds its own damage per second once (chance-weighted)
	var burn := float(s.get("burn", 0.0)) * minf(float(s.get("burn_chance", 0.0)) * 3.0, 1.0)
	match s.get("kind", ""):
		"gun":
			var rate := float(s.get("fire_rate", 1.0))
			if s.has("charge"):
				rate = 1.0 / (float(s["charge"]) + 1.0 / maxf(rate, 0.1))
			if str(s.get("fire", "")) == "gatling":
				rate *= 0.85
			var mag := float(s.get("mag", 1))
			var cycle := mag / maxf(rate, 0.01) + float(s.get("reload", 0.0))
			return dmg * mag / maxf(cycle, 0.01) + burn
		"spell":
			match str(s.get("cast", "")):
				"beam":
					return float(s.get("damage", 0.0)) * (1.0 + float(s.get("ramp", 1.0))) * 0.5
				"orb":
					return (float(s.get("damage", 0.0)) * float(s.get("duration", 3.0)) * 1.5 + float(s.get("splash", 0.0))) / maxf(float(s.get("cooldown", 1.0)), 0.05)
			return dmg * (1.0 + float(s.get("chains", 0)) * 0.6) / maxf(float(s.get("cooldown", 1.0)), 0.05) + burn
		"melee":
			return dmg / maxf(float(s.get("swing_time", 0.6)), 0.05) + burn
	return dmg


## Gold a vendor pays for a weapon instance.
func weapon_value(w: Dictionary) -> int:
	var bd := weapon_base(str(w.get("base", "")))
	var price := maxf(float(bd.get("price", 60)), 60.0)
	var rarity := clampi(int(w.get("rarity", 0)), 0, RARITY_VALUE.size() - 1)
	return int(round(price * 0.3 * RARITY_VALUE[rarity] * (1.0 + 0.25 * float(int(w.get("level", 1)) - 1))))


## Artisan rank needed to upgrade a weapon from `lvl` to the next level.
func upgrade_rank(lvl: int) -> int:
	return maxi(1, lvl - 2)


## Upgrade cost to go from the weapon's level to the next: {gold, items, rank}. Empty at max level.
func upgrade_cost(w: Dictionary) -> Dictionary:
	var lvl := int(w.get("level", 1))
	if lvl >= MAX_WEAPON_LEVEL:
		return {}
	var rarity := int(w.get("rarity", 0))
	var base := str(w.get("base", ""))
	var kind: String = weapon_base(base).get("kind", "gun")
	var items := {}
	if weapon_school(base) == "magic":
		items["rune_shard"] = mini(lvl, 4)
		items["ley_crystal"] = lvl
		if lvl >= 3:
			items["rune_ink"] = lvl - 2
		if lvl >= 5:
			items["focus_gem"] = lvl - 4
		if lvl >= 7:
			items["runesteel_ingot"] = lvl - 6
	elif kind == "melee":
		items["scrap_gear"] = mini(lvl + 1, 6)
		items["rune_shard"] = maxi(1, mini(lvl - 1, 3))
		if lvl >= 3:
			items["iron_ingot"] = lvl - 2
		if lvl >= 5:
			items["steel_plate"] = lvl - 4
	else:
		items["scrap_gear"] = mini(lvl * 2, 8)
		if lvl >= 3:
			items["clockwork_core"] = 1 if lvl < 7 else 2
		if lvl >= 4:
			items["brass_ingot"] = lvl - 3
		if lvl >= 6:
			items["steel_plate"] = lvl - 5
	return {"gold": int(40 * lvl * (1.0 + rarity * 0.5)), "items": items, "rank": upgrade_rank(lvl)}


## Materials returned when salvaging a weapon at the workbench.
func salvage_yield(w: Dictionary) -> Dictionary:
	var rarity := int(w.get("rarity", 0))
	var lvl := int(w.get("level", 1))
	var base := str(w.get("base", ""))
	var kind: String = weapon_base(base).get("kind", "gun")
	var out := {}
	if weapon_school(base) == "magic":
		out["rune_shard"] = 1 + rarity / 2
		out["ley_crystal"] = 1 + rarity / 2 + (lvl - 1) / 2
		if rarity >= 1:
			out["rune_ink"] = rarity
		if rarity >= 3:
			out["focus_gem"] = rarity - 2
	elif kind == "melee":
		out["scrap_gear"] = 2 + rarity
		out["rune_shard"] = rarity / 2
		if rarity >= 1:
			out["iron_ingot"] = 1 + rarity / 2
	else:
		out["scrap_gear"] = 2 + rarity + (lvl - 1)
		if rarity >= 1:
			out["iron_ingot"] = 1 + rarity / 2
		if rarity >= 2:
			out["brass_ingot"] = rarity - 1
	if rarity >= 3:
		out["clockwork_core"] = rarity - 2
	if lvl >= 5:
		out["steel_plate" if weapon_school(base) == "tech" else "rune_ink"] = (lvl - 3) / 2
	for k in out.keys():
		if int(out[k]) <= 0:
			out.erase(k)
	return out


## Enchanter's Altar: reroll the perks of an Uncommon+ weapon. {gold, items, rank} or {} if impossible.
func reroll_cost(w: Dictionary) -> Dictionary:
	var rarity := int(w.get("rarity", 0))
	if rarity < 1:
		return {}
	return {"gold": 60 * (1 + rarity), "items": {"rune_ink": 2, "focus_gem": 1}, "rank": 3}


## Enchanter's Altar: infuse a weapon one rarity tier higher (up to Epic). {gold, items, rank} or {}.
func infuse_cost(w: Dictionary) -> Dictionary:
	var rarity := int(w.get("rarity", 0))
	if rarity >= MAX_INFUSE_RARITY:
		return {}
	var items := {"focus_gem": rarity + 1}
	if rarity >= 1:
		items["runesteel_ingot"] = rarity
	if rarity >= 2:
		items["clockwork_core"] = rarity - 1
	return {"gold": 150 * (rarity + 1), "items": items, "rank": 4 + rarity}
