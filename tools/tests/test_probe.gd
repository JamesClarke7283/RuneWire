extends Node
## Dev helper: prints terrain height / slope / splat at candidate positions for world content.
## Run: godot --headless --path . -- --autostart --no-intro --test=probe -- (edit POINTS as needed)

const POINTS := {
	"woods_hollow": Vector2(-118, -42), "woods_deep": Vector2(-140, -88), "woods_edge": Vector2(-60, -70),
	"island": Vector2(-194, 6), "watchtower": Vector2(-159, 159), "ley_north": Vector2(18, -205),
	"ley_east": Vector2(222, 56), "foundry_yard": Vector2(180, -205), "shrine": Vector2(-176, -140),
	"flats_far": Vector2(-62, 196), "arena_back": Vector2(206, -28), "south_hills": Vector2(60, 235),
	"lake_north": Vector2(-170, -60), "north_meadow": Vector2(-40, -150), "east_ridge": Vector2(250, -100),
	"gorge_rim": Vector2(110, 130), "vault_shrine": Vector2(-150, -184), "vault_foundry": Vector2(120, -203),
	"sky_flats": Vector2(-30, 140), "sky_lake": Vector2(-205, 30),
	"c_ley_n1": Vector2(2, -218), "c_ley_n2": Vector2(22, -214), "c_ley_e1": Vector2(205, 70), "c_ley_e2": Vector2(226, 70),
	"c_island": Vector2(-186, 2), "c_woods1": Vector2(-95, -30), "c_woods2": Vector2(-130, -60), "c_woods3": Vector2(-75, -95),
	"c_woods4": Vector2(-115, -15), "c_shrine1": Vector2(-125, -150), "c_shrine2": Vector2(-172, -186),
	"c_flats1": Vector2(20, 192), "c_flats2": Vector2(-48, 150), "c_hill1": Vector2(100, -62), "c_hill2": Vector2(60, -150),
	"c_south": Vector2(-120, 210), "c_east": Vector2(240, 0),
	"workbench": Vector2(5.7, -21.25),
}


func run(m: Node) -> void:
	var t: Terrain = m.world.terrain
	for k in POINTS:
		var p: Vector2 = POINTS[k]
		var h := t.height_at(p.x, p.y)
		var s := t.slope_at(p.x, p.y)
		var sp := t.splat_at(p.x, p.y)
		var near := ""
		var best := 1e9
		for poi in WorldLayout.POIS:
			var d := p.distance_to(WorldLayout.POIS[poi]["pos"])
			if d < best:
				best = d
				near = poi
		var lake := p.distance_to(WorldLayout.LAKE["pos"])
		var gorge := Terrain._dist_to_segment(p, WorldLayout.GORGE["a"], WorldLayout.GORGE["b"])
		printerr("PROBE %-14s h=%6.2f slope=%.2f road=%.2f sand=%.2f forest=%.2f cobble=%.2f near=%s(%.0f) lake=%.0f gorge=%.0f r=%.0f" % [
			k, h, s, sp.r, sp.g, sp.b, sp.a, near, best, lake, gorge, p.length()])
	get_tree().quit(0)
