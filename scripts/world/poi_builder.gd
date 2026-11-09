class_name PoiBuilder
extends Node3D
## Places every point of interest: the town of Emberwick and its NPCs, the target range, the
## Arena of Echoes, the Gearworks foundry, the Sunken Shrine, the Builder's Flats, the gorge,
## the watchtower, ley stones, race rings, enemy spawners and challenge terminals.

var world: World
var challenges: Dictionary = {}
var npcs: Dictionary = {}
var cargo_zone: CargoZone
var watchtower_lamp: OmniLight3D
var _boss_spawned: Dictionary = {}


func build(w: World) -> void:
	world = w
	_town()
	_range()
	_arena()
	_foundry()
	_shrine()
	_flats()
	_gorge()
	_watchtower()
	_ley_stones()
	_race()
	_lake()
	_sky_islands()
	_treasure()
	_crystal_nodes()
	_gather_nodes()
	_spawners()
	Quests.quest_accepted.connect(_on_quest_accepted)


# ------------------------------------------------------------------ helpers
func gp(x: float, z: float, lift: float = 0.0) -> Vector3:
	return world.ground_point(x, z, lift)


func place(model: String, x: float, z: float, yaw: float = 0.0, scl: float = 1.0, lift: float = 0.0) -> Node3D:
	return Props.place(world.props_root, model, gp(x, z, lift), yaw, scl)


## The flattest dry spot within `radius` of p (keeps chests and crystals off cliffs and out of water).
func settle(p: Vector2, radius: float = 6.0) -> Vector2:
	var t := world.terrain
	var best := p
	var best_score := INF
	for i in 25:
		var q := p if i == 0 else p + Vector2.from_angle(i * 2.39996) * radius * sqrt(i / 24.0)
		if t.height_at(q.x, q.y) < 0.8:
			continue
		var score := t.slope_at(q.x, q.y) * 10.0 + q.distance_to(p) * 0.05
		if score < best_score:
			best_score = score
			best = q
	return best


## Yaw (degrees) that makes a model's front (+Z) face a target point.
static func face(from: Vector2, to: Vector2) -> float:
	var d := to - from
	return rad_to_deg(atan2(d.x, d.y))


## Point at an angle around a centre. Angles are compass-like on the map: 0 = east, 90 = north (-Z).
func polar(center: Vector2, angle_deg: float, r: float) -> Vector2:
	var a := deg_to_rad(angle_deg)
	return center + Vector2(cos(a), -sin(a)) * r


func add_npc(id: String, model: String, x: float, z: float, yaw: float) -> Npc:
	var n := Npc.new()
	n.npc_id = id
	n.model_name = model
	n.name = "NPC_" + id
	world.npcs_root.add_child(n)
	n.global_position = gp(x, z)
	n.rotation.y = deg_to_rad(yaw)
	npcs[id] = n
	return n


func add_trigger(id: String, pos: Vector3, radius: float, once: bool = false) -> LocationTrigger:
	var t := LocationTrigger.new()
	t.location_id = id
	t.radius = radius
	t.once = once
	add_child(t)
	t.global_position = pos
	return t


# ------------------------------------------------------------------ town
func _town() -> void:
	var c := Vector2.ZERO
	place("prop_fountain", 0, 0)
	# shops
	var wpos := polar(c, 90, 33)
	place("bld_workshop", wpos.x, wpos.y, face(wpos, c))
	var mpos := polar(c, 158, 33)
	place("bld_magic_shop", mpos.x, mpos.y, face(mpos, c))
	var tpos := polar(c, 28, 33)
	place("bld_tinker_shop", tpos.x, tpos.y, face(tpos, c))
	# NPCs in front of their shops
	var o := polar(c, 90, 23)
	add_npc("odda", "npc_odda", o.x, o.y, face(o, c))
	var l := polar(c, 158, 24)
	add_npc("lirael", "npc_lirael", l.x, l.y, face(l, c))
	var g := polar(c, 28, 24.5)
	add_npc("gus", "npc_gus", g.x, g.y, face(g, c))
	add_npc("brannoc", "npc_brannoc", 15, 7, face(Vector2(15, 7), Vector2(0, 12)))
	# quest board near the fountain
	var board := place("prop_quest_board", 9, 13, face(Vector2(9, 13), Vector2(0, 6)))
	var qb := QuestBoard.new()
	board.add_child(qb)
	# houses around the plaza, avoiding the road directions
	var house_angles := [32.0, 78.0, 112.0, 160.0, 203.0, 247.0, 290.0, 305.0, 345.0, 135.0 + 18.0]
	var radii := [50.0, 52.0, 50.0, 54.0, 48.0, 50.0, 52.0, 58.0, 49.0, 60.0]
	for i in house_angles.size():
		var hp := polar(c, house_angles[i], radii[i])
		if hp.distance_to(wpos) < 16.0 or hp.distance_to(mpos) < 14.0 or hp.distance_to(tpos) < 14.0:
			continue
		var model := "bld_house_a" if i % 3 != 1 else "bld_house_b"
		place(model, hp.x, hp.y, face(hp, c) + randf_range(-8, 8))
	# market stalls, benches, lamps, banners
	for a in [205.0, 238.0, 300.0, 330.0]:
		var sp := polar(c, a, 19)
		place("prop_market_stall", sp.x, sp.y, face(sp, c))
	for a in [0.0, 120.0, 240.0]:
		var bp := polar(c, a + 60.0, 8.5)
		place("prop_bench", bp.x, bp.y, face(bp, c) + 180.0)
	for i in 10:
		var lp := polar(c, i * 36.0 + 18.0, 27.0)
		place("prop_street_lamp", lp.x, lp.y, face(lp, c))
	for a in [11.0, 56.0, 135.0, 186.0, 225.0, 266.0, 326.0]:
		var bn := polar(c, a + 7.0, 31.0)
		place("prop_banner", bn.x, bn.y, face(bn, c))
		var bn2 := polar(c, a - 7.0, 31.0)
		place("prop_banner", bn2.x, bn2.y, face(bn2, c))
		var sg := polar(c, a + 4.0, 40.0)
		place("prop_signpost", sg.x, sg.y, face(sg, c))
	place("prop_well", -22, 20)
	place("prop_crate_stack", 26, -20, 30)
	place("prop_barrels", -30, -22, 10)
	place("prop_cart", 22, 24, 70)
	place("prop_crate_stack", -6, -44, 0)
	place("prop_barrels", 8, -44, 0)
	# lamps along the roads out of town
	for road in WorldLayout.ROADS:
		var pts: Array = road["pts"]
		for i in pts.size() - 1:
			var a2: Vector2 = pts[i]
			var b2: Vector2 = pts[i + 1]
			var seg := b2 - a2
			var n := Vector2(-seg.y, seg.x).normalized()
			var steps := int(seg.length() / 28.0)
			for s in steps:
				var p := a2 + seg * ((s + 0.5) / maxf(steps, 1))
				if p.length() < 40.0:
					continue
				var lp2 := p + n * 4.5 * (1 if s % 2 == 0 else -1)
				place("prop_street_lamp", lp2.x, lp2.y, face(lp2, p))
	# crafting stations: Workbench and Forge by Odda, Alchemy Table and Altar by Lirael, Loom by the stalls
	for sid in WorldLayout.STATIONS:
		var sp2: Vector2 = WorldLayout.STATIONS[sid]
		var sm := place(str(Catalog.STATIONS[sid]["model"]), sp2.x, sp2.y, face(sp2, c))
		var st := Workbench.new() if sid == "workbench" else CraftingStation.new()
		st.station = sid
		st.name = "Station_" + sid
		sm.add_child(st)
	# villagers
	var vill := [Vector2(-10, -10), Vector2(12, -14), Vector2(-16, 6), Vector2(4, 22)]
	for i in vill.size():
		var v: Vector2 = vill[i]
		var npc := add_npc("villager_%d" % i, "npc_villager_a" if i % 2 == 0 else "npc_villager_b", v.x, v.y, randf() * 360.0)
		npc.wanders = true


# ------------------------------------------------------------------ target range
func _range() -> void:
	var c: Vector2 = WorldLayout.POIS["range"]["pos"]
	var term_pos := c + Vector2(-12, 0)
	var term := _terminal("targets", term_pos, face(term_pos, c))
	var targets := []
	for i in 7:
		var tp := c + Vector2(10 + (i % 2) * 3.0, -9.0 + i * 3.0)
		var t := place("prop_target", tp.x, tp.y, face(tp, term_pos))
		targets.append(t)
	var ch := TargetChallenge.new()
	ch.targets = targets
	ch.area_center = gp(c.x, c.y)
	term.add_child(ch)
	challenges["targets"] = ch
	place("prop_fence", c.x - 15, c.y - 8, 90)
	place("prop_fence", c.x - 15, c.y + 8, 90)
	place("prop_banner", c.x - 14, c.y - 3, face(c + Vector2(-14, -3), c))


func _terminal(challenge_id: String, p: Vector2, yaw: float) -> ChallengeTerminal:
	var model := place("prop_challenge_terminal", p.x, p.y, yaw)
	var t := ChallengeTerminal.new()
	t.challenge_id = challenge_id
	model.add_child(t)
	return t


# ------------------------------------------------------------------ arena
func _arena() -> void:
	var c: Vector2 = WorldLayout.POIS["arena"]["pos"]
	var seg_count := 24
	var gate_index := 12   # facing west, towards town
	for i in seg_count:
		var ang := float(i) * 360.0 / seg_count
		var p := polar(c, ang, 30.0)
		var model := "bld_arena_gate" if i == gate_index else "bld_arena_wall"
		place(model, p.x, p.y, face(p, c))
	var gate := polar(c, 180.0, 36.0)
	var term := _terminal("arena", gate + Vector2(0, 4.5), face(gate + Vector2(0, 4.5), c))
	var ch := ArenaChallenge.new()
	ch.center = gp(c.x, c.y)
	ch.radius = 28.0
	term.add_child(ch)
	challenges["arena"] = ch
	for a in [150.0, 210.0]:
		var lp := polar(c, a, 38.0)
		place("prop_street_lamp", lp.x, lp.y, face(lp, c))
		var bn := polar(c, a, 34.5)
		place("prop_banner", bn.x, bn.y, face(c, bn))


# ------------------------------------------------------------------ foundry
func _foundry() -> void:
	var c: Vector2 = WorldLayout.POIS["foundry"]["pos"]
	var town := Vector2.ZERO
	place("bld_factory_shed", c.x, c.y + 8, face(c, town))
	place("prop_smokestack", c.x - 22, c.y + 20, 0)
	place("prop_smokestack", c.x + 20, c.y + 24, 0)
	place("prop_smokestack", c.x + 26, c.y + 2, 0, 0.8)
	place("prop_tank", c.x - 26, c.y - 4, 20)
	place("prop_tank", c.x - 30, c.y + 6, 50, 0.8)
	place("prop_pipes", c.x - 18, c.y - 14, 90)
	place("prop_pipes", c.x + 24, c.y - 10, 0)
	place("prop_conveyor", c.x + 4, c.y - 16, 0)
	for p in [Vector2(-12, -24), Vector2(14, -26), Vector2(30, 16), Vector2(-34, 22), Vector2(4, 32)]:
		var pile := place("prop_scrap_pile", c.x + p.x, c.y + p.y, randf() * 360.0)
		var hn := HarvestNode.new()
		hn.kind = "scrap"
		pile.add_child(hn)
	place("prop_crate_stack", c.x + 10, c.y - 20, 15)
	place("prop_barrels", c.x - 8, c.y - 22, 0)
	add_trigger("foundry", gp(c.x, c.y), 46.0)


# ------------------------------------------------------------------ shrine
func _shrine() -> void:
	var c: Vector2 = WorldLayout.POIS["shrine"]["pos"]
	place("ruin_altar", c.x, c.y, 0)
	for i in 8:
		var p := polar(c, i * 45.0 + 22.5, 16.0)
		if i % 3 == 2:
			continue
		place("ruin_pillar", p.x, p.y, randf() * 360.0, randf_range(0.85, 1.15))
	for a in [0.0, 90.0, 180.0, 270.0]:
		var ap := polar(c, a, 26.0)
		place("ruin_arch", ap.x, ap.y, face(ap, c))
	for a in [45.0, 135.0, 225.0, 315.0]:
		var wp := polar(c, a, 30.0)
		place("ruin_wall", wp.x, wp.y, face(wp, c) + 90.0)
	add_trigger("shrine_altar", gp(c.x, c.y, 1.0), 6.5)
	var glow := OmniLight3D.new()
	glow.light_color = Color(0.6, 0.4, 1.0)
	glow.light_energy = 2.5
	glow.omni_range = 16.0
	add_child(glow)
	glow.global_position = gp(c.x, c.y, 3.0)


# ------------------------------------------------------------------ flats, gorge, tower
func _flats() -> void:
	var c: Vector2 = WorldLayout.POIS["flats"]["pos"]
	var tp := c + Vector2(0, 16)
	var term := _terminal("altitude", tp, face(tp, c))
	var ch := AltitudeChallenge.new()
	ch.beacon_pos = WorldLayout.ALTITUDE_BEACON
	term.add_child(ch)
	challenges["altitude"] = ch
	var beacon := Props.place(world.props_root, "prop_beacon", WorldLayout.ALTITUDE_BEACON, 0.0, 1.0)
	ch.beacon_node = beacon
	for a in [30.0, 150.0, 270.0]:
		var bp := polar(c, a, 60.0)
		place("prop_banner", bp.x, bp.y, face(bp, c))
	place("prop_crate_stack", c.x + 20, c.y + 30, 0)
	place("prop_signpost", tp.x + 4, tp.y + 2, 0)


func _gorge() -> void:
	var s: Vector2 = WorldLayout.POIS["gorge_start"]["pos"]
	var g: Vector2 = WorldLayout.POIS["gorge_goal"]["pos"]
	var term := _terminal("cargo", s + Vector2(-8, 4), face(s + Vector2(-8, 4), g))
	var pad := place("prop_goal_pad", g.x, g.y, 0)
	var ch := CargoChallenge.new()
	ch.start_pos = gp(s.x, s.y, 1.2)
	ch.goal_pos = gp(g.x, g.y)
	ch.goal_node = pad
	term.add_child(ch)
	challenges["cargo"] = ch
	place("prop_goal_pad", s.x, s.y, 0, 0.6)
	place("prop_signpost", s.x + 6, s.y - 6, face(s, g))


func _watchtower() -> void:
	var c: Vector2 = WorldLayout.POIS["watchtower"]["pos"]
	var tower := place("bld_watchtower", c.x, c.y, face(c, Vector2.ZERO))
	watchtower_lamp = OmniLight3D.new()
	watchtower_lamp.light_color = Color(0.35, 0.95, 0.9)
	watchtower_lamp.light_energy = 0.0
	watchtower_lamp.omni_range = 30.0
	tower.add_child(watchtower_lamp)
	watchtower_lamp.position = Vector3(0, 15.0, 0)
	if Quests.is_done("q_cargo"):
		watchtower_lamp.light_energy = 4.0
	var zp := c + (Vector2.ZERO - c).normalized() * 9.0
	place("prop_goal_pad", zp.x, zp.y, 0, 0.75)
	cargo_zone = CargoZone.new()
	cargo_zone.zone_id = "watchtower"
	cargo_zone.radius = 5.0
	add_child(cargo_zone)
	cargo_zone.global_position = gp(zp.x, zp.y, 1.0)
	cargo_zone.delivered.connect(func(_c):
		var tw := create_tween()
		tw.tween_property(watchtower_lamp, "light_energy", 4.0, 2.0))
	add_trigger("watchtower", gp(c.x, c.y), 14.0)


func _ley_stones() -> void:
	for id in WorldLayout.LEY_STONES:
		var p: Vector2 = WorldLayout.LEY_STONES[id]
		var offset := Vector2(0, 0)
		if id == "ley_lake":
			offset = Vector2(2.5, 1.5)
		var pos := p + offset
		var stone := place("ley_stone", pos.x, pos.y, randf() * 360.0)
		var light := OmniLight3D.new()
		light.light_color = Color(0.3, 0.95, 0.85)
		light.light_energy = 1.6
		light.omni_range = 8.0
		stone.add_child(light)
		light.position = Vector3(0, 2.5, 0)
		var t := add_trigger(id, gp(pos.x, pos.y, 1.0), 4.5)
		t.toast_text = "The ley stone hums as you touch it..."


const RING_LIFT := 4.8   # race ring centre above the ground (outer radius 4.48: the rim clears uneven ground)


func _race() -> void:
	var start: Vector2 = WorldLayout.POIS["race_start"]["pos"]
	var term := _terminal("race", start, face(start, Vector2(WorldLayout.RACE_RINGS[0].x, WorldLayout.RACE_RINGS[0].y)))
	var ch := RaceChallenge.new()
	term.add_child(ch)
	var rings := []
	for i in WorldLayout.RACE_RINGS.size():
		# RACE_RINGS hold Vector3(x, z, _). This used to read them as (x, height, z), which stacked the rings
		# from underground to 140 m up instead of looping the valley. Every ring stands with its rim just
		# above the ground (centre 4.8 m up), so the "fly or drive" rally is drivable: the pass check is
		# 5.5 m from the centre, which a driver's camera reaches from the ground.
		var r: Vector3 = WorldLayout.RACE_RINGS[i]
		var nxt: Vector3 = WorldLayout.RACE_RINGS[(i + 1) % WorldLayout.RACE_RINGS.size()]
		var pos := gp(r.x, r.y, RING_LIFT)
		var yaw := face(Vector2(r.x, r.y), Vector2(nxt.x, nxt.y))
		var ring := Props.place(world.props_root, "prop_race_ring", pos, yaw, 1.0)
		rings.append(ring)
	ch.rings = rings
	challenges["race"] = ch


func _lake() -> void:
	var island: Vector2 = WorldLayout.POIS["island"]["pos"]
	place("tree_oak_small", island.x - 3.0, island.y - 2.0, 0)
	place("rock_b", island.x + 4.0, island.y - 3.0, 40)
	# a little pier on the east shore, out over the water (it used to run along the bank, under trees)
	var pier: Vector2 = WorldLayout.LAKE_PIER["pos"]
	Props.place(world.props_root, "prop_bridge", Vector3(pier.x, float(WorldLayout.LAKE_PIER["y"]), pier.y), float(WorldLayout.LAKE_PIER["yaw"]))


# ------------------------------------------------------------------ treasure & gathering
var sky_tops: Dictionary = {}   # sky island id -> Vector3 centre of its walkable top


func _sky_islands() -> void:
	for id in WorldLayout.SKY_ISLANDS:
		var d: Dictionary = WorldLayout.SKY_ISLANDS[id]
		var p: Vector2 = d["pos"]
		var top := Vector3(p.x, float(d["top"]), p.y)
		var n: Node3D
		if Props.exists("prop_sky_island"):
			n = Props.instance("prop_sky_island")
		else:
			n = _sky_island_fallback()
		n.name = "SkyIsland_" + id
		world.props_root.add_child(n)
		n.global_position = top
		n.rotation.y = randf() * TAU
		var glow := OmniLight3D.new()
		glow.light_color = Color(0.35, 0.95, 0.88)
		glow.light_energy = 2.0
		glow.omni_range = 12.0
		n.add_child(glow)
		glow.position = Vector3(0, -3.0, 0)
		sky_tops[id] = top
		for k in 2:
			var hn := HarvestNode.new()
			hn.kind = "crystal"
			world.props_root.add_child(hn)
			hn.global_position = top + Vector3(cos(k * 2.6 + 0.8), 0, sin(k * 2.6 + 0.8)) * 2.4


## Floating island stand-in until the Blender model exists: grassy disc on a rocky cone.
func _sky_island_fallback() -> Node3D:
	var root := Node3D.new()
	var top := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 4.2
	cm.bottom_radius = 3.9
	cm.height = 0.8
	top.mesh = cm
	top.position.y = -0.4
	top.material_override = MaterialLib.get_flat(Color("6cc24a"))
	root.add_child(top)
	var under := MeshInstance3D.new()
	var um := CylinderMesh.new()
	um.top_radius = 3.9
	um.bottom_radius = 0.4
	um.height = 4.2
	under.mesh = um
	under.position.y = -2.9
	under.material_override = MaterialLib.get_named("M_StoneRough")
	root.add_child(under)
	var body := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var cyl := CylinderShape3D.new()
	cyl.radius = 4.1
	cyl.height = 0.8
	cs.shape = cyl
	cs.position.y = -0.4
	body.add_child(cs)
	root.add_child(body)
	return root


func _treasure() -> void:
	for id in WorldLayout.CHESTS:
		var d: Dictionary = WorldLayout.CHESTS[id]
		var p: Vector2 = d["pos"]
		var pos: Vector3
		var yaw := 0.0
		if d.has("sky"):
			pos = sky_tops.get(d["sky"], Vector3(p.x, 30.0, p.y)) + Vector3(0.0, 0.0, -1.2)
			yaw = face(Vector2(pos.x, pos.z), Vector2.ZERO)
		else:
			var q := settle(p, 6.0)
			pos = gp(q.x, q.y, -0.04)
			yaw = face(q, Vector2.ZERO) + randf_range(-25.0, 25.0)
		var ch := TreasureChest.new()
		ch.chest_id = id
		ch.vault = bool(d.get("vault", false))
		ch.name = "Chest_" + id
		world.props_root.add_child(ch)
		ch.global_position = pos
		ch.rotation.y = deg_to_rad(yaw)


## Ore veins, glowcaps, sunpetals and reeds (see WorldLayout.GATHER_NODES).
func _gather_nodes() -> void:
	for kind in WorldLayout.GATHER_NODES:
		for p in WorldLayout.GATHER_NODES[kind]:
			var q := settle(p, 7.0)
			var hn := HarvestNode.new()
			hn.kind = kind
			hn.name = "Node_%s_%d_%d" % [kind, int(q.x), int(q.y)]
			world.props_root.add_child(hn)
			hn.global_position = gp(q.x, q.y, -0.08)


func _crystal_nodes() -> void:
	for c in WorldLayout.CRYSTAL_NODES:
		var q := settle(c, 5.0)
		var hn := HarvestNode.new()
		hn.kind = "crystal"
		world.props_root.add_child(hn)
		hn.global_position = gp(q.x, q.y, -0.1)


# ------------------------------------------------------------------ enemies
func _spawners() -> void:
	var woods: Vector2 = WorldLayout.WOODS["pos"]
	_spawner("woods", woods, 55.0, {"wisp": 1.0}, 6, 25.0)
	_spawner("lake_shore", Vector2(-150, 50), 30.0, {"wisp": 0.7, "wraith": 0.3}, 3, 70.0, func(): return Quests.is_done("q_wisps"))
	_spawner("north_hills", Vector2(20, -192), 32.0, {"crawler": 0.5, "drone": 0.5}, 4, 60.0, func(): return Quests.is_done("q_scrap"))
	_spawner("woods_night", woods + Vector2(-20, -30), 50.0, {"wraith": 1.0}, 2, 60.0, func(): return Quests.is_done("q_wisps"))
	var shrine: Vector2 = WorldLayout.POIS["shrine"]["pos"]
	_spawner("shrine", shrine, 30.0, {"cultist": 0.6, "wraith": 0.4}, 5, 40.0, func(): return Quests.is_done("q_wisps") or Quests.is_active("q_survey"))
	_spawner("shrine_golems", shrine, 20.0, {"golem": 1.0}, 2, 70.0, func(): return Quests.is_active("q_golems") or Quests.is_done("q_golems"))
	var foundry: Vector2 = WorldLayout.POIS["foundry"]["pos"]
	_spawner("foundry", foundry, 40.0, {"drone": 0.55, "crawler": 0.45}, 7, 30.0)
	var sentries := _spawner("foundry_sentries", foundry, 0.0, {"sentry": 1.0}, 4, 150.0)
	sentries.fixed_points = [foundry + Vector2(-20, -30), foundry + Vector2(22, -30), foundry + Vector2(-34, 6), foundry + Vector2(34, 10)]
	_spawner("north_road", Vector2(70, -110), 30.0, {"drone": 1.0}, 2, 60.0)
	_spawner("west_meadow", Vector2(-70, 60), 30.0, {"wisp": 1.0}, 2, 60.0, func(): return Quests.is_done("q_arrival"))
	_spawner("east_hills", Vector2(190, 40), 35.0, {"crawler": 1.0}, 3, 60.0, func(): return Quests.is_done("q_wheels"))


func _spawner(id: String, center: Vector2, radius: float, types: Dictionary, max_alive: int, respawn: float, cond: Callable = Callable()) -> EnemySpawner:
	var s := EnemySpawner.new()
	s.spawner_id = id
	s.center = center
	s.radius = radius
	s.types = types
	s.max_alive = max_alive
	s.respawn_time = respawn
	s.condition = cond
	s.level = int(WorldLayout.ZONE_LEVELS.get(id, 1))
	s.world = world
	add_child(s)
	return s


# ------------------------------------------------------------------ quest-driven events
func on_game_started() -> void:
	for c in get_tree().get_nodes_in_group("chests"):
		c.sync_state()
	for id in Quests.active_quests():
		_on_quest_accepted(id)
	if Quests.is_done("q_cargo") and watchtower_lamp:
		watchtower_lamp.light_energy = 4.0


func _on_quest_accepted(id: String) -> void:
	match id:
		"q_cargo":
			_spawn_cargo()
		"q_foundry":
			_spawn_boss("ironclad", WorldLayout.POIS["foundry"]["pos"] + Vector2(0, -6))
		"q_choir":
			_spawn_boss("archon", WorldLayout.POIS["shrine"]["pos"])


func _spawn_cargo() -> void:
	for c in get_tree().get_nodes_in_group("contraptions"):
		for p in (c as Contraption).parts:
			if p.part_id == "cargo":
				return
	var pos := gp(0, -47, 1.0)
	var xf := Transform3D(Basis(), pos)
	world.build_manager.spawn_part("cargo", xf, false)
	Events.toast("The Ley Crystal cargo is waiting behind the Workshop", "quest")


func _spawn_boss(kind: String, at: Vector2) -> void:
	if _boss_spawned.get(kind, false):
		return
	_boss_spawned[kind] = true
	var e := Enemy.spawn(kind, world, gp(at.x, at.y, 0.5), false, int(WorldLayout.ZONE_LEVELS.get(kind, 8)))
	if e:
		e.home = e.global_position
		e.leash = 40.0
