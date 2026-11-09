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

# Race rings in order (x, z, height above ground).
const RACE_RINGS := [
	Vector3(0, 110, 4), Vector3(40, 130, 5), Vector3(90, 115, 6), Vector3(125, 60, 5),
	Vector3(130, -0, 5), Vector3(105, -70, 6), Vector3(55, -110, 7), Vector3(-10, -120, 6),
	Vector3(-70, -90, 6), Vector3(-95, -20, 5), Vector3(-75, 50, 5), Vector3(-30, 85, 4),
]

const ALTITUDE_BEACON := Vector3(-10, 44, 195)

const TOWN_SPAWN := Vector3(0, 6.5, 14)
