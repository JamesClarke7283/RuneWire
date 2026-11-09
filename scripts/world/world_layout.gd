class_name WorldLayout
## The valley of Emberwick: points of interest, roads and zones (x, z in metres; terrain spans
## -320..320 on both axes, water level y = 0). Compass: north = -Z, east = +X.

const SIZE := 640.0
const HALF := 320.0
const WATER_LEVEL := 0.0
const PLAY_RADIUS := 292.0

# Flattened areas: centre, radius (flat core), blend width, height
const POIS := {
	"town": {"pos": Vector2(0, 0), "radius": 64.0, "blend": 30.0, "height": 6.0},
	"range": {"pos": Vector2(84, 26), "radius": 16.0, "blend": 14.0, "height": 6.0},
	"arena": {"pos": Vector2(170, -40), "radius": 44.0, "blend": 26.0, "height": 5.0},
	"foundry": {"pos": Vector2(150, -175), "radius": 58.0, "blend": 30.0, "height": 10.0},
	"shrine": {"pos": Vector2(-150, -165), "radius": 46.0, "blend": 28.0, "height": 14.0},
	"flats": {"pos": Vector2(-10, 165), "radius": 66.0, "blend": 30.0, "height": 4.0},
	"gorge_start": {"pos": Vector2(140, 100), "radius": 16.0, "blend": 14.0, "height": 6.0},
	"gorge_goal": {"pos": Vector2(150, 190), "radius": 14.0, "blend": 14.0, "height": 6.0},
	"watchtower": {"pos": Vector2(-150, 150), "radius": 13.0, "blend": 26.0, "height": 15.0},
	"island": {"pos": Vector2(-190, 10), "radius": 8.0, "blend": 9.0, "height": 1.6},
	"ley_north": {"pos": Vector2(10, -212), "radius": 7.0, "blend": 12.0, "height": 22.0},
	"ley_east": {"pos": Vector2(214, 62), "radius": 7.0, "blend": 12.0, "height": 16.0},
	"race_start": {"pos": Vector2(0, 82), "radius": 10.0, "blend": 12.0, "height": 5.5},
}

const LAKE := {"pos": Vector2(-190, 10), "radius": 64.0, "depth": 7.0}
const GORGE := {"a": Vector2(60, 142), "b": Vector2(250, 150), "width": 13.0, "depth": 15.0}
const WOODS := {"pos": Vector2(-105, -55), "radius": 82.0}

# Roads (polylines). Width in metres.
const ROADS := [
	{"pts": [Vector2(0, 0), Vector2(60, -12), Vector2(120, -30), Vector2(150, -38)], "width": 5.0},
	{"pts": [Vector2(0, 0), Vector2(40, -60), Vector2(90, -120), Vector2(130, -160)], "width": 5.0},
	{"pts": [Vector2(0, 0), Vector2(-50, -50), Vector2(-100, -110), Vector2(-135, -150)], "width": 4.5},
	{"pts": [Vector2(0, 0), Vector2(-4, 60), Vector2(-8, 110), Vector2(-10, 140)], "width": 5.0},
	{"pts": [Vector2(0, 0), Vector2(-60, 60), Vector2(-120, 120), Vector2(-145, 142)], "width": 4.5},
	{"pts": [Vector2(0, 0), Vector2(-70, 8), Vector2(-120, 10)], "width": 4.5},
	{"pts": [Vector2(0, 0), Vector2(60, 40), Vector2(110, 80), Vector2(136, 96)], "width": 4.5},
]

# Ley stones for the survey quest.
const LEY_STONES := {
	"ley_north": Vector2(10, -212),
	"ley_lake": Vector2(-190, 10),
	"ley_east": Vector2(214, 62),
}

# Fast-travel points on the map: the plaza, plus each ley stone once the player has touched it.
# "arrive" is where travellers land: beside the stone on the town side, turned to face it.
const WAYPOINTS := {
	"town": {"name": "Emberwick Plaza", "pos": Vector2(0, 0), "arrive": Vector2(0, 14)},
	"ley_north": {"name": "Northern Ley Stone", "pos": Vector2(10, -212), "arrive": Vector2(10, -207.5)},
	"ley_lake": {"name": "Lake Ley Stone", "pos": Vector2(-187.5, 11.5), "arrive": Vector2(-183.5, 12.0)},
	"ley_east": {"name": "Eastern Ley Stone", "pos": Vector2(214, 62), "arrive": Vector2(209.5, 62.0)},
}

# Race rings in order: Vector3(x, z, _) - .y is the map z; the third value is unused (PoiBuilder.RING_LIFT).
const RACE_RINGS := [
	Vector3(0, 110, 4), Vector3(40, 130, 5), Vector3(90, 115, 6), Vector3(125, 60, 5),
	Vector3(130, -0, 5), Vector3(105, -70, 6), Vector3(55, -110, 7), Vector3(-10, -120, 6),
	Vector3(-70, -90, 6), Vector3(-95, -20, 5), Vector3(-75, 50, 5), Vector3(-30, 85, 4),
]

const ALTITUDE_BEACON := Vector3(-10, 44, 195)

# The little pier on the lake's east shore: the arched footbridge runs west from the bank (where its end
# sinks into the ground) out over the water. "y" is its origin height (water level 0); kept clear of trees.
const LAKE_PIER := {"pos": Vector2(-135.5, 8.0), "y": 0.7, "yaw": 0.0, "clear": 9.0}

const TOWN_SPAWN := Vector3(0, 6.5, 14)

# Treasure chests (x, z). Vaults need a Ley Key. "sky" ones sit on floating islands (see SKY_ISLANDS).
const CHESTS := {
	"woods_hollow": {"pos": Vector2(-118, -42)},
	"woods_deep": {"pos": Vector2(-140, -88)},
	"woods_glade": {"pos": Vector2(-100, -70)},
	"lake_island": {"pos": Vector2(-194, 6)},
	"watchtower": {"pos": Vector2(-159, 159)},
	"ley_north": {"pos": Vector2(15, -209)},
	"ley_east": {"pos": Vector2(219, 66)},
	"foundry_yard": {"pos": Vector2(180, -205)},
	"shrine_ruins": {"pos": Vector2(-176, -140)},
	"flats_far": {"pos": Vector2(-62, 196)},
	"arena_back": {"pos": Vector2(206, -28)},
	"south_hills": {"pos": Vector2(60, 235)},
	"lake_north": {"pos": Vector2(-170, -60)},
	"north_meadow": {"pos": Vector2(-40, -150)},
	"gorge_rim": {"pos": Vector2(110, 130)},
	"vault_shrine": {"pos": Vector2(-150, -184), "vault": true},
	"vault_foundry": {"pos": Vector2(120, -203), "vault": true},
	"vault_sky_flats": {"pos": Vector2(-30, 140), "vault": true, "sky": "flats"},
	"vault_sky_lake": {"pos": Vector2(-205, 30), "vault": true, "sky": "lake"},
}

# Floating islands: centre (x, z) and the absolute height of the walkable top.
const SKY_ISLANDS := {
	"flats": {"pos": Vector2(-30, 140), "top": 30.0},
	"lake": {"pos": Vector2(-205, 30), "top": 20.0},
}

# Harvestable ley-crystal clusters (x, z).
const CRYSTAL_NODES := [
	Vector2(2, -218), Vector2(4, -206), Vector2(205, 70), Vector2(226, 70), Vector2(-186, 2), Vector2(-95, -30),
	Vector2(-130, -60), Vector2(-75, -95), Vector2(-115, -15), Vector2(-125, -150), Vector2(-172, -186),
	Vector2(20, 192), Vector2(-48, 150), Vector2(100, -62), Vector2(60, -150), Vector2(-120, 210), Vector2(240, 0),
]

const WORKBENCH := Vector2(5.7, -21.25)

# Crafting stations around the plaza (x, z). The workbench sits next to Odda's workshop.
const STATIONS := {
	"workbench": Vector2(5.7, -21.25),
	"forge": Vector2(-7.0, -22.0),
	"alchemy": Vector2(-16.5, -9.5),
	"altar": Vector2(-22.8, -3.2),
	"loom": Vector2(5.2, 19.3),
}

# Gathering nodes (x, z) by HarvestNode kind: ore veins in the rocky hills, glowcaps in the woods,
# sunpetals on the southern flats and meadows, reeds on the lake shore.
const GATHER_NODES := {
	"ore_copper": [Vector2(30, -190), Vector2(-25, -195), Vector2(55, -215), Vector2(200, 40), Vector2(232, 92),
		Vector2(188, 105), Vector2(92, 122), Vector2(178, 124), Vector2(45, 248), Vector2(100, 238)],
	"ore_iron": [Vector2(95, -140), Vector2(205, -140), Vector2(150, -245), Vector2(90, -200), Vector2(215, -200),
		Vector2(-100, -205), Vector2(-195, -210), Vector2(-170, 172), Vector2(-125, 178)],
	"glowcap": [Vector2(-90, -40), Vector2(-122, -72), Vector2(-142, -32), Vector2(-72, -82), Vector2(-108, -102),
		Vector2(-62, -42), Vector2(-152, -62), Vector2(-98, -16), Vector2(-132, -112), Vector2(-82, -122)],
	"sunpetal": [Vector2(-32, 182), Vector2(22, 172), Vector2(-52, 132), Vector2(42, 202), Vector2(-72, 176),
		Vector2(12, 132), Vector2(-62, 62), Vector2(-22, 102), Vector2(82, 188), Vector2(62, 62)],
	"reeds": [Vector2(-122, 10), Vector2(-134, 49), Vector2(-167, 74), Vector2(-213, 74), Vector2(-249, 44),
		Vector2(-257, -2), Vector2(-234, -42), Vector2(-190, -58), Vector2(-138, -34)],
}

# Area levels of the enemy spawners (foes are at least the player's level - 2).
const ZONE_LEVELS := {
	"woods": 1, "west_meadow": 1, "lake_shore": 2, "north_road": 3, "east_hills": 3, "foundry": 4,
	"woods_night": 4, "foundry_sentries": 5, "north_hills": 5, "shrine": 6, "shrine_golems": 7,
	"ironclad": 9, "archon": 11,
}

# Named regions for the "now entering" banner: centre, radius, the level of the foes there (see
# ZONE_LEVELS; foes are at least the player's level - 2) and what is worth gathering.
const AREAS := {
	"town": {"name": "Emberwick", "pos": Vector2(0, 0), "radius": 66.0, "levels": [0, 0], "note": "Crafting stations, vendors and quest givers"},
	"arena": {"name": "The Arena", "pos": Vector2(170, -40), "radius": 46.0, "levels": [0, 0], "note": "Trials and challenges"},
	"foundry": {"name": "The Gearworks Foundry", "pos": Vector2(150, -175), "radius": 72.0, "levels": [4, 6], "note": "Cogwork machines · scrap heaps · iron veins"},
	"shrine": {"name": "The Sunken Shrine", "pos": Vector2(-150, -165), "radius": 60.0, "levels": [6, 8], "note": "The Hollow Choir · rune shards · iron veins"},
	"north_hills": {"name": "The Northern Hills", "pos": Vector2(20, -200), "radius": 48.0, "levels": [3, 6], "note": "Copper veins · the northern ley stone"},
	"woods": {"name": "The Whispering Woods", "pos": Vector2(-105, -55), "radius": 82.0, "levels": [1, 4], "note": "Ember Wisps · glowcaps · treasure"},
	"lake": {"name": "The Lake Shore", "pos": Vector2(-190, 10), "radius": 74.0, "levels": [2, 4], "note": "Reeds · a floating vault overhead"},
	"east_hills": {"name": "The Eastern Hills", "pos": Vector2(205, 70), "radius": 55.0, "levels": [3, 4], "note": "Clank Crawlers · copper veins"},
	"flats": {"name": "The Builder's Flats", "pos": Vector2(-10, 165), "radius": 72.0, "levels": [1, 2], "note": "Sunpetals · a floating vault overhead"},
	"watchtower": {"name": "The Old Watchtower", "pos": Vector2(-150, 150), "radius": 30.0, "levels": [1, 3], "note": "Iron veins nearby"},
}
