extends Node
## End-to-end gameplay test: quests, economy, building, driving, combat, challenges, saving.
## Run: godot --path . -- --autostart --no-intro --test=core

var main: Node
var fails := 0
var passes := 0


func check(cond: bool, what: String) -> void:
	if cond:
		passes += 1
		printerr("TEST PASS ", what)
	else:
		fails += 1
		printerr("TEST FAIL ", what)


func wait(sec: float) -> void:
	await get_tree().create_timer(sec, true, true).timeout


func run(m: Node) -> void:
	main = m
	get_tree().create_timer(150.0, true, false, true).timeout.connect(func():
		printerr("TEST TIMEOUT passes=%d fails=%d" % [passes, fails])
		get_tree().quit(2))
	printerr("TEST start")
	await wait(1.0)
	printerr("TEST waited")
	var p: Player = m.player
	var bm: BuildManager = m.world.build_manager
	# ---------------------------------------------------------------- quest 1 + economy
	Quests.accept("q_arrival")
	check(Quests.is_active("q_arrival"), "quest accepted")
	var g0 := Game.gold
	check(Game.buy_part("plank", 2), "bought planks")
	check(Game.gold == g0 - 12, "gold deducted (%d -> %d)" % [g0, Game.gold])
	p.teleport(m.world.ground_point(0, 30, 0.2) + Vector3(0, 0, 0), 0.0, -25.0)
	await wait(0.6)
	var a := bm.spawn_part("crate", Transform3D(Basis(), m.world.ground_point(2, 28, 0.6)))
	var b := bm.spawn_part("plank", Transform3D(Basis(), m.world.ground_point(2, 28, 1.3)))
	check(a != null and b != null, "spawned crate and plank")
	await wait(1.0)
	check(bm.weld(a, b), "welded crate + plank")
	check(a.contraption == b.contraption and a.contraption.parts.size() == 2, "single contraption with 2 parts")
	await wait(0.3)
	check(Quests.status("q_arrival") == "ready", "q_arrival objectives complete (status %s)" % Quests.status("q_arrival"))
	var g1 := Game.gold
	check(Quests.turn_in("q_arrival"), "turned in q_arrival")
	check(Game.gold == g1 + 60, "quest paid 60 gold")
	check(Game.part_count("wheel") >= 4 and Game.part_count("seat") >= 1, "received wheels + seat")
	# ---------------------------------------------------------------- vehicle build + drive
	Quests.accept("q_wheels")
	Game.add_parts("platform", 1)
	var base: Vector3 = m.world.ground_point(10, 34, 1.2)
	var deck := bm.spawn_part("platform", Transform3D(Basis(), base))
	var seat := bm.spawn_part("seat", Transform3D(Basis(), base + Vector3(0, 0.75, -0.6)))
	var wheels: Array = []
	for off in [Vector3(-2.25, -0.2, 1.3), Vector3(2.25, -0.2, 1.3), Vector3(-2.25, -0.2, -1.3), Vector3(2.25, -0.2, -1.3)]:
		wheels.append(bm.spawn_part("wheel", Transform3D(Basis(), base + off)))
	check(deck != null and seat != null and wheels.size() == 4 and not wheels.has(null), "spawned vehicle parts")
	bm.weld(deck, seat)
	for w in wheels:
		bm.weld(deck, w)
	var car := deck.contraption
	check(car.parts.size() == 6, "vehicle has 6 parts (%d)" % car.parts.size())
	check(car.tags.has("vehicle"), "vehicle tag detected")
	await wait(1.5)
	var start: Vector3 = car.global_position
	p.sit(seat)
	check(p.piloting == car, "player is piloting")
	var t := 0.0
	while t < 4.0:
		car.pilot_input = {"throttle": 1.0, "steer": 0.0, "lift": 0.0, "boost": false, "fire": false, "aim": Vector3.ZERO}
		p.input_enabled = false
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
	var moved := Vector2(car.global_position.x - start.x, car.global_position.z - start.z).length()
	check(moved > 6.0, "vehicle drove %.1f m" % moved)
	p.input_enabled = true
	p.exit_seat()
	check(p.piloting == null, "exited seat")
	# ---------------------------------------------------------------- combat
	var drone := Enemy.spawn("drone", m.world, p.global_position + Vector3(0, 3.0, -8.0))
	check(drone != null, "spawned drone")
	await wait(0.5)
	var gold_before := Game.gold
	var kills_before := int(Game.stats.get("kills", 0))
	var shots := 0
	while is_instance_valid(drone) and not drone.dead and shots < 40:
		drone.apply_damage(DamageInfo.make(13.0, "shock", p, drone.aim_point(), Vector3.FORWARD, 0.0, true))
		shots += 1
		await wait(0.05)
	check(shots < 40, "drone destroyed in %d shock hits" % shots)
	check(int(Game.stats.get("kills", 0)) == kills_before + 1, "kill counted")
	# coins should drop and be collected (magnet) - stand near the drop
	p.teleport(p.global_position, NAN)
	await wait(6.0)
	check(Game.gold > gold_before, "gold coins collected (%d -> %d)" % [gold_before, Game.gold])
	# ---------------------------------------------------------------- spells / weapons smoke
	var caster: EquipBase = p._handler_for("arcane_bolt")
	var mana0 := p.mana
	caster.on_equip()
	caster.primary(true)
	caster.primary(false)
	check(p.mana < mana0, "arcane bolt spent mana")
	p.select_slot(Game.hotbar.find("arc_pistol"))
	var gun: EquipBase = p.current
	gun.primary(true)
	await wait(0.4)
	gun.primary(false)
	check((gun as WeaponGun).mag < 12, "arc pistol fired (mag %d)" % (gun as WeaponGun).mag)
	# ---------------------------------------------------------------- challenge payout
	var g2 := Game.gold
	var res := Challenges.finish("targets", 19.0)
	check(int(res["medal"]) == 2 and Game.gold == g2 + 60 + 120, "silver target medal pays bronze+silver (got %s)" % str(res))
	# ---------------------------------------------------------------- save / load
	main.save_now()
	check(SaveSystem.has_save(), "save written")
	var saved_gold := Game.gold
	var saved_parts := bm.placed_count
	Game.gold = 0
	check(SaveSystem.load_game(), "save loaded")
	check(Game.gold == saved_gold, "gold restored (%d)" % Game.gold)
	var build_data: Variant = SaveSystem.pending.get("build", null)
	check(build_data is Dictionary and (build_data["contraptions"] as Array).size() >= 2, "contraptions in save (placed %d)" % saved_parts)
	printerr("TEST SUMMARY passes=%d fails=%d" % [passes, fails])
	get_tree().quit(0 if fails == 0 else 1)
