class_name GameUI
extends CanvasLayer
## Root of all UI: loading screen, title menu, HUD and the in-game menus (stacked, pausing).

var hud: Hud
var loading: Control
var main_menu: Control
var menu_layer: Control
var toast_box: VBoxContainer
var current_menu: Control = null
var player: Player
var _loading_bar: ProgressBar
var _loading_label: Label
var _tip_label: Label

const TIPS := [
	"Magic foes resist magic. Tech foes resist tech. Mix your arsenal!",
	"Weld a Pilot Seat to anything with wheels and press E to drive it.",
	"Levitation Stones make anything float. Yes, anything.",
	"Press Z to undo your last spawned part.",
	"Hold R with the Grav Gauntlet to rotate what you're holding. Shift snaps.",
	"Spring Pads launch players AND contraptions.",
	"Volatile Mana Barrels explode when damaged. Plan accordingly.",
	"Gold medals pay the most, but every new medal pays out.",
	"Turrets welded to your vehicle fire where you aim while you hold LMB.",
	"The Bounty Board by the fountain always has work for you.",
	"Press I for your Inventory. Drag weapons onto hotbar slots 1 and 2.",
	"Carry one tech weapon and one magic focus: X swaps between them instantly.",
	"Champions glow and wear a crown. They drop the best weapons, and sometimes Ley Keys.",
	"Treasure chests hide all over the valley. Two Ley Vaults float in the sky: build something that flies!",
	"Harvest teal Ley Crystal clusters and scavenge Gearworks scrap heaps for crafting materials.",
	"Five crafting stations ring the plaza: Workbench, Forge, Alchemist's Table, Enchanter's Altar and Loom.",
	"Sell weapons you've outgrown to any vendor. Favourite (★) the ones you want to keep safe.",
	"Your pack has limited room. Equip up to five pouches [I] to carry more; sew better ones at the Loom.",
	"Mine copper and iron veins in the hills, then smelt the ore into ingots at the Forge.",
	"Glowcaps glow in the woods, sunpetals bloom on the southern flats and reeds line the lake shore.",
	"Press B for the Crafting Book. Track a recipe and the objective tracker leads you to its materials.",
	"Every level gives a talent point: press K to spend it.",
	"Look at a weapon on the ground and press E to wield it right away; walk over it to stash it instead.",
	"Burning foes take fire damage over time; chilled foes move and attack more slowly.",
	"Schematics teach new recipes. Vaults always hold one you don't know yet.",
	"Higher Artisan ranks unlock recipes and make crafted weapons roll rarer.",
	"The Enchanter's Altar rerolls a weapon's perks, or infuses it all the way up to Epic.",
	"Foes show their level. Orange and red ones hit much harder than you'd like.",
	"Every five levels you earn a milestone cache: gold, a Rare weapon and a schematic.",
	"Press M for the map. Every new region you discover pays XP and gets its name on the map.",
	"Touch a ley stone to attune it, then fast-travel there from the map [M].",
]


func _ready() -> void:
	layer = 10
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group("game_ui")
	# Controls under a CanvasLayer don't inherit the window theme, so set it on each UI root.
	var th := UIStyle.build_theme()
	hud = Hud.new()
	hud.theme = th
	hud.name = "HUD"
	hud.visible = false
	add_child(hud)
	menu_layer = Control.new()
	menu_layer.name = "Menus"
	menu_layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	menu_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu_layer.theme = th
	add_child(menu_layer)
	toast_box = VBoxContainer.new()
	toast_box.name = "Toasts"
	toast_box.custom_minimum_size = Vector2(430, 0)
	toast_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_layout_toasts()
	toast_box.add_theme_constant_override("separation", 6)
	add_child(toast_box)
	Events.notify.connect(_on_toast)
	Events.player_died.connect(_on_player_died)
	_build_loading()


# ------------------------------------------------------------------ loading
func _build_loading() -> void:
	loading = ColorRect.new()
	(loading as ColorRect).color = Color("120f1d")
	loading.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(loading)
	var vb := VBoxContainer.new()
	vb.custom_minimum_size = Vector2(760, 0)
	UIStyle.anchor(vb, Control.PRESET_CENTER, Vector2(-380, -170))
	vb.alignment = BoxContainer.ALIGNMENT_CENTER
	vb.add_theme_constant_override("separation", 18)
	loading.add_child(vb)
	vb.add_child(_logo(560))
	_loading_label = UIStyle.label("Loading", 24, UIStyle.PARCHMENT, "ui")
	_loading_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(_loading_label)
	_loading_bar = ProgressBar.new()
	_loading_bar.custom_minimum_size = Vector2(760, 22)
	_loading_bar.show_percentage = false
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(1, 1, 1, 0.08)
	bg.set_corner_radius_all(11)
	var fg := StyleBoxFlat.new()
	fg.bg_color = UIStyle.TEAL
	fg.set_corner_radius_all(11)
	_loading_bar.add_theme_stylebox_override("background", bg)
	_loading_bar.add_theme_stylebox_override("fill", fg)
	vb.add_child(_loading_bar)
	_tip_label = UIStyle.label("Tip: " + TIPS[randi() % TIPS.size()], 19, Color(0.8, 0.78, 0.9), "body")
	_tip_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_tip_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vb.add_child(_tip_label)


func _logo(width: float) -> Control:
	var tex := UIStyle.tex("ui_title_logo")
	if tex:
		var tr := TextureRect.new()
		tr.texture = tex
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.custom_minimum_size = Vector2(width, width * 0.3)
		return tr
	var l := UIStyle.label("RUNEWIRE", int(width / 5.5), UIStyle.GOLD, "display", 18, Color("2a1a35"))
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l


func show_loading(step: String, f: float) -> void:
	loading.visible = true
	_loading_label.text = step + "..."
	_loading_bar.value = f * 100.0


func hide_loading() -> void:
	var tw := create_tween()
	tw.tween_property(loading, "modulate:a", 0.0, 0.6)
	tw.tween_callback(func(): loading.visible = false)


# ------------------------------------------------------------------ main menu
func show_main_menu() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	main_menu = MainMenu.new()
	main_menu.ui = self
	main_menu.theme = UIStyle.build_theme()
	add_child(main_menu)


func on_game_started(p: Player) -> void:
	player = p
	if main_menu:
		main_menu.queue_free()
		main_menu = null
	hud.visible = true
	hud.bind(p)


func show_intro() -> void:
	var d := InfoPopup.new()
	d.title_text = "Welcome to Emberwick"
	d.body_text = "[b]Emberwick[/b] is a valley town of artificers who fuse [color=#9a66ff]rune-magic[/color] with [color=#d9a441]clockwork[/color]. Lately the ley lines have gone sour: the [color=#9a66ff]Hollow Choir[/color] haunts the woods and the shrine, and the rogue [color=#ff9a3c]Cogwork Legion[/color] stomps around the old Gearworks.\n\nYou're the new Runewright apprentice. Take [b]quests[/b] and [b]challenges[/b] to earn [color=#ffc93c]gold[/color], spend it on parts, spells and weapons, and [b]build[/b] whatever wonderful contraption the job needs.\n\n[b]Start by talking to Master Artificer Odda[/b] (north side of the plaza, look for the [color=#ffc93c]![/color]). The [b]Objective[/b] tracker under the compass always shows your next step.\n\nGather ore, herbs, reeds and crystals, and [b]craft[/b] at the five stations around the plaza. Wear up to five [b]pouches[/b] to carry more. Every level brings a [b]talent point[/b].\n\n[color=#3a2a1e][b]Controls[/b][/color]\nWASD move · Space jump · Shift sprint · Ctrl crouch · E interact\n1-2 weapons · 3-4 tools · 5-8 quick items · X swap weapons · wheel cycle · LMB use · RMB alternate · R reload / tool mode\n[b]I inventory[/b] · [b]B crafting book[/b] · [b]K talents[/b] · Q build catalog · J quest log · Tab character · Z undo spawn · H/G tonics · Esc menu"
	d.button_text = "Let's tinker!"
	open_menu(d)


func show_challenge_result(id: String, res: Dictionary) -> void:
	var d := InfoPopup.new()
	var medal: int = res["medal"]
	d.title_text = "%s: %s" % [Challenges.def(id)["name"], ("%s medal!" % Challenges.MEDAL_NAMES[medal]) if medal > 0 else "No medal"]
	var body := "Result: [b]%s[/b]%s\n" % [Challenges.format_value(id, res["value"]), "  (new best!)" if res.get("best", false) else ""]
	if res["gold"] > 0:
		body += "Reward: [color=#b8860b][b]%d gold[/b][/color]\n" % res["gold"]
	body += "\nMedals: "
	var d2 := Challenges.def(id)
	for i in 3:
		body += "%s %s   " % [Challenges.MEDAL_NAMES[i + 1], Challenges.format_value(id, float(d2["medals"][i]))]
	d.body_text = body
	d.button_text = "Nice!"
	d.medal = medal
	open_menu(d)


func _on_player_died() -> void:
	var c := ColorRect.new()
	c.color = Color(0.25, 0.02, 0.05, 0.0)
	c.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(c)
	var l := UIStyle.label("Knocked out!", 72, UIStyle.PARCHMENT, "display", 16, Color("2a0a10"))
	l.custom_minimum_size = Vector2(520, 100)
	UIStyle.anchor(l, Control.PRESET_CENTER, Vector2(-260, -80))
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	c.add_child(l)
	var s := UIStyle.label("You wake up back in town, a little lighter in the purse.", 22, UIStyle.PARCHMENT, "body", 6)
	s.custom_minimum_size = Vector2(800, 40)
	UIStyle.anchor(s, Control.PRESET_CENTER, Vector2(-400, 20))
	s.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	c.add_child(s)
	var tw := create_tween()
	tw.tween_property(c, "color:a", 0.75, 0.6)
	tw.tween_interval(2.6)
	tw.tween_property(c, "modulate:a", 0.0, 0.6)
	tw.tween_callback(c.queue_free)


# ------------------------------------------------------------------ menus
func open_menu(m: Control) -> void:
	close_menu(false)
	current_menu = m
	menu_layer.add_child(m)
	if m.has_signal("closed"):
		m.connect("closed", func(): close_menu())
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if player:
		player.input_enabled = false
	get_tree().paused = true
	hud.visible = player != null
	_layout_toasts()
	AudioManager.play_ui("ui_open")
	Events.menu_opened.emit(m.name)


func close_menu(resume: bool = true) -> void:
	if current_menu and is_instance_valid(current_menu):
		current_menu.queue_free()
		Events.menu_closed.emit(current_menu.name)
		AudioManager.play_ui("ui_close")
	current_menu = null
	_layout_toasts()
	if resume:
		get_tree().paused = false
		if player and main_menu == null:
			player.input_enabled = true
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func is_menu_open() -> bool:
	return current_menu != null and is_instance_valid(current_menu)


func open_dialogue(npc: Npc) -> void:
	var d := DialogueMenu.new()
	d.npc = npc
	d.ui = self
	open_menu(d)


func open_board() -> void:
	var d := DialogueMenu.new()
	d.board = true
	d.ui = self
	open_menu(d)


func open_shop(vendor: String) -> void:
	var s := ShopMenu.new()
	s.vendor = vendor
	open_menu(s)


func open_catalog() -> void:
	var c := CatalogMenu.new()
	c.ui = self
	open_menu(c)


func open_inventory() -> void:
	var inv := InventoryMenu.new()
	inv.ui = self
	open_menu(inv)
	AudioManager.play_ui("ui_bag", -2.0)


func open_workbench() -> void:
	open_station("workbench")


## A crafting station's screen (workbench, forge, alchemy, altar, loom) or "field": the Crafting Book.
func open_station(station: String) -> void:
	var m: CraftingMenu = WorkbenchMenu.new() if station == "workbench" else CraftingMenu.new()
	m.station = station
	m.ui = self
	open_menu(m)


func open_crafting_book() -> void:
	open_station("field")


func open_talents() -> void:
	var t := TalentMenu.new()
	t.ui = self
	open_menu(t)


func open_map() -> void:
	var m := MapMenu.new()
	m.ui = self
	open_menu(m)
	AudioManager.play_ui("ui_bag", -6.0)


## Why the player can't fast-travel to `id` right now ("" = they can).
func travel_block(id: String) -> String:
	if not WorldLayout.WAYPOINTS.has(id):
		return "Pick a place to travel to"
	if not Game.waypoints.has(id):
		return "Touch that ley stone first to attune it"
	if player == null or player.dead:
		return "You can't travel right now"
	if player.piloting:
		return "Step out of your vehicle first"
	if Challenges.running != "":
		return "Finish (or leave) the challenge first"
	if foes_near(player.global_position, 30.0):
		return "Foes are hunting you: deal with them first"
	var a: Vector2 = WorldLayout.WAYPOINTS[id]["arrive"]
	if Vector2(player.global_position.x, player.global_position.z).distance_to(a) < 12.0:
		return "You're already here"
	return ""


func foes_near(pos: Vector3, radius: float) -> bool:
	for e in get_tree().get_nodes_in_group("enemies"):
		var en := e as Enemy
		if en and not en.dead and en.aggro and en.global_position.distance_to(pos) < radius:
			return true
	return false


## Ley travel: close the map and step out beside the chosen stone (or the plaza fountain).
func fast_travel(id: String) -> bool:
	var why := travel_block(id)
	if why != "":
		AudioManager.play_ui("ui_error")
		Events.toast(why, "warn")
		return false
	var w := get_tree().get_first_node_in_group("world") as World
	var wp: Dictionary = WorldLayout.WAYPOINTS[id]
	var a: Vector2 = wp["arrive"]
	var d: Vector2 = (wp["pos"] as Vector2) - a
	close_menu()
	VFX.sparkle(player, player.global_position + Vector3.UP, Color(0.3, 0.95, 0.85), 24, 0.5)
	player.teleport(w.ground_point(a.x, a.y, 0.3), rad_to_deg(atan2(-d.x, -d.y)), 0.0)
	VFX.ring(player, player.global_position + Vector3.UP * 0.2, Color(0.3, 0.95, 0.85), 3.5, 0.7)
	VFX.sparkle(player, player.global_position + Vector3.UP, Color(0.3, 0.95, 0.85), 30, 0.5)
	AudioManager.play_2d("spell_arcane_cast", -4.0, 0.75, 0.0)
	Game.add_stat("travels")
	Events.toast("You step out of the ley line at %s" % wp["name"], "info")
	return true


func open_challenge(id: String, runner: ChallengeRunner) -> void:
	var c := ChallengeMenu.new()
	c.challenge_id = id
	c.runner = runner
	open_menu(c)


func _unhandled_input(event: InputEvent) -> void:
	if main_menu != null or player == null:
		return
	if event.is_action_pressed("pause"):
		if is_menu_open():
			close_menu()
		else:
			var pm := PauseMenu.new()
			pm.ui = self
			open_menu(pm)
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("spawn_menu"):
		if is_menu_open() and current_menu is CatalogMenu:
			close_menu()
		elif not is_menu_open() and not player.piloting:
			open_catalog()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("inventory"):
		if is_menu_open() and current_menu is InventoryMenu:
			close_menu()
		elif not is_menu_open():
			open_inventory()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("quest_log"):
		if is_menu_open() and current_menu is QuestLogMenu:
			close_menu()
		elif not is_menu_open():
			open_menu(QuestLogMenu.new())
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("character"):
		if is_menu_open() and current_menu is CharacterMenu:
			close_menu()
		elif not is_menu_open():
			open_menu(CharacterMenu.new())
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("crafting"):
		if is_menu_open() and current_menu is CraftingMenu:
			close_menu()
		elif not is_menu_open():
			open_crafting_book()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("talents"):
		if is_menu_open() and current_menu is TalentMenu:
			close_menu()
		elif not is_menu_open():
			open_talents()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("map"):
		if is_menu_open() and current_menu is MapMenu:
			close_menu()
		elif not is_menu_open():
			open_map()
		get_viewport().set_input_as_handled()


# ------------------------------------------------------------------ toasts
const TOAST_COLORS := {
	"gold": Color("ffc93c"), "quest": Color("39d5c4"), "quest_done": Color("ffd84a"), "levelup": Color("ffd84a"),
	"warn": Color("ff7a5c"), "unlock": Color("b48cff"), "item": Color("8fe07a"), "save": Color("9fb0d8"),
	"tool": Color("f2b84e"), "info": Color("f3e3bf"),
	"rarity_0": Color("d9d2c0"), "rarity_1": Color("6fdc6a"), "rarity_2": Color("4d9dff"),
	"rarity_3": Color("b56cff"), "rarity_4": Color("ffa63c"),
}


## Toasts stack on the left under the gold and pack counters in play (clear of the compass, the
## objective tracker and the banners), and in the top-right corner while a menu covers the screen.
func _layout_toasts() -> void:
	if toast_box == null:
		return
	if is_menu_open():
		UIStyle.anchor(toast_box, Control.PRESET_TOP_RIGHT, Vector2(-446, 8))
	else:
		UIStyle.anchor(toast_box, Control.PRESET_TOP_LEFT, Vector2(22, 130))
	for pc in toast_box.get_children():
		var l := pc.get_child(0) as Label if pc.get_child_count() > 0 else null
		if l:
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT


func _on_toast(text: String, kind: String) -> void:
	var max_toasts := 3 if is_menu_open() else 5
	while toast_box.get_child_count() >= max_toasts:
		var old := toast_box.get_child(0)
		toast_box.remove_child(old)
		old.queue_free()
	var pc := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.08, 0.07, 0.13, 0.82)
	sb.border_color = TOAST_COLORS.get(kind, UIStyle.BRASS)
	sb.border_width_left = 5
	sb.set_corner_radius_all(8)
	sb.content_margin_left = 16
	sb.content_margin_right = 16
	sb.content_margin_top = 6
	sb.content_margin_bottom = 7
	pc.add_theme_stylebox_override("panel", sb)
	pc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var l := UIStyle.label(text, 19, TOAST_COLORS.get(kind, UIStyle.PARCHMENT), "ui", 0)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	pc.add_child(l)
	toast_box.add_child(pc)
	pc.modulate.a = 0.0
	var tw := pc.create_tween()
	tw.tween_property(pc, "modulate:a", 1.0, 0.2)
	tw.tween_interval(3.2 if kind not in ["quest", "quest_done", "levelup", "unlock", "rarity_2", "rarity_3", "rarity_4"] else 4.5)
	tw.tween_property(pc, "modulate:a", 0.0, 0.5)
	tw.tween_callback(pc.queue_free)
	match kind:
		"levelup":
			AudioManager.play_ui("level_up", 0.0)
		"quest_done":
			AudioManager.play_ui("quest_complete", 0.0)
		"quest":
			AudioManager.play_ui("notify", -6.0)
		"unlock":
			AudioManager.play_ui("ui_buy", -4.0)
		"warn":
			AudioManager.play_ui("ui_error", -8.0)
