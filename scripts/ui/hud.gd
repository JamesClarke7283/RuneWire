class_name Hud
extends Control
## In-game HUD.

var player: Player
var _hp_bar: ProgressBar
var _mp_bar: ProgressBar
var _st_bar: ProgressBar
var _xp_bar: ProgressBar
var _hp_label: Label
var _mp_label: Label
var _level_label: Label
var _gold_label: Label
var _parts_label: Label
var _tonic_label: Label
var _draught_label: Label
var _slots: Array = []
var _slot_box: HBoxContainer
var _equip_label: Label
var _hint_label: Label
var _crosshair: Control
var _hitmark: Label
var _interact_panel: PanelContainer
var _interact_label: Label
var _aim_label: Label
var _quest_panel: PanelContainer
var _quest_title: Label
var _quest_lines: VBoxContainer
var _compass: Compass
var _challenge_panel: PanelContainer
var _challenge_label: Label
var _boss_panel: VBoxContainer
var _boss_bar: ProgressBar
var _boss_name: Label
var _boss: Node = null
var _vignette: ColorRect
var _pilot_label: Label
var _fps_label: Label
var _gold_shown: float = 0.0
var _gold_target: int = 0
var _hit_t: float = 0.0
var _hurt_t: float = 0.0


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()


func _bar(color: Color, h: float, w: float) -> ProgressBar:
	var b := ProgressBar.new()
	b.custom_minimum_size = Vector2(w, h)
	b.show_percentage = false
	b.max_value = 100.0
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.05, 0.04, 0.08, 0.85)
	bg.set_corner_radius_all(int(h / 2))
	bg.border_color = Color(0.85, 0.65, 0.3, 0.9)
	bg.set_border_width_all(2)
	var fg := StyleBoxFlat.new()
	fg.bg_color = color
	fg.set_corner_radius_all(int(h / 2))
	fg.border_color = color.lightened(0.35)
	fg.border_width_top = 2
	b.add_theme_stylebox_override("background", bg)
	b.add_theme_stylebox_override("fill", fg)
	b.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return b


func _dark_panel(margin: int = 10) -> PanelContainer:
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.07, 0.07, 0.12, 0.72)
	sb.border_color = Color(0.85, 0.65, 0.3, 0.8)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(12)
	sb.set_content_margin_all(margin)
	p.add_theme_stylebox_override("panel", sb)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return p


func _build() -> void:
	# vignette (damage / ward tint)
	_vignette = ColorRect.new()
	_vignette.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var vs := Shader.new()
	vs.code = "shader_type canvas_item;\nuniform vec4 tint : source_color = vec4(0.8,0.05,0.1,0.0);\nvoid fragment(){ float d = distance(UV, vec2(0.5)); COLOR = vec4(tint.rgb, tint.a * smoothstep(0.35, 0.75, d)); }"
	var vm := ShaderMaterial.new()
	vm.shader = vs
	_vignette.material = vm
	add_child(_vignette)
	# ---- vitals (bottom-left)
	var vit := _dark_panel(12)
	UIStyle.anchor(vit, Control.PRESET_BOTTOM_LEFT, Vector2(22, -150))
	add_child(vit)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 12)
	vit.add_child(hb)
	var badge := PanelContainer.new()
	var bsb := StyleBoxFlat.new()
	bsb.bg_color = Color("2c3550")
	bsb.border_color = UIStyle.GOLD
	bsb.set_border_width_all(3)
	bsb.set_corner_radius_all(32)
	bsb.set_content_margin_all(4)
	badge.add_theme_stylebox_override("panel", bsb)
	badge.custom_minimum_size = Vector2(64, 64)
	_level_label = UIStyle.label("1", 30, UIStyle.GOLD, "display", 6, Color("1a1020"))
	_level_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_level_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	badge.add_child(_level_label)
	hb.add_child(badge)
	var bars := VBoxContainer.new()
	bars.add_theme_constant_override("separation", 5)
	hb.add_child(bars)
	var hp_row := _bar_row(UIStyle.HEALTH, 22, 300)
	_hp_bar = hp_row[0]
	_hp_label = hp_row[1]
	bars.add_child(hp_row[2])
	var mp_row := _bar_row(UIStyle.MANA, 18, 300)
	_mp_bar = mp_row[0]
	_mp_label = mp_row[1]
	bars.add_child(mp_row[2])
	_st_bar = _bar(Color("f2c94c"), 7, 300)
	bars.add_child(_st_bar)
	_xp_bar = _bar(Color("b48cff"), 7, 300)
	bars.add_child(_xp_bar)
	var cons := HBoxContainer.new()
	cons.add_theme_constant_override("separation", 14)
	_tonic_label = UIStyle.label("", 16, Color("ff9a9a"), "ui", 4, Color(0, 0, 0, 0.8))
	_draught_label = UIStyle.label("", 16, Color("9ac0ff"), "ui", 4, Color(0, 0, 0, 0.8))
	cons.add_child(_tonic_label)
	cons.add_child(_draught_label)
	bars.add_child(cons)
	# ---- gold (top-left)
	var gold_p := _dark_panel(8)
	gold_p.position = Vector2(22, 20)
	add_child(gold_p)
	var gh := HBoxContainer.new()
	gh.add_theme_constant_override("separation", 8)
	gold_p.add_child(gh)
	var coin_tex := UIStyle.tex("ui_coin")
	if coin_tex:
		var ci := TextureRect.new()
		ci.texture = coin_tex
		ci.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ci.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		ci.custom_minimum_size = Vector2(38, 38)
		gh.add_child(ci)
	else:
		gh.add_child(UIStyle.label("●", 30, UIStyle.GOLD, "ui"))
	_gold_label = UIStyle.label("0", 32, UIStyle.GOLD, "display", 6, Color("2a1a10"))
	gh.add_child(_gold_label)
	_parts_label = UIStyle.label("Parts 0/40", 16, UIStyle.PARCHMENT, "ui", 4, Color(0, 0, 0, 0.8))
	_parts_label.position = Vector2(26, 76)
	add_child(_parts_label)
	# ---- hotbar (bottom-center)
	var hot := VBoxContainer.new()
	hot.custom_minimum_size = Vector2(660, 0)
	UIStyle.anchor(hot, Control.PRESET_CENTER_BOTTOM, Vector2(-330, -138))
	hot.alignment = BoxContainer.ALIGNMENT_END
	hot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(hot)
	_hint_label = UIStyle.label("", 16, Color(0.95, 0.92, 0.85, 0.9), "body", 5, Color(0, 0, 0, 0.85))
	_hint_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hot.add_child(_hint_label)
	_equip_label = UIStyle.label("", 21, UIStyle.PARCHMENT, "ui", 6, Color(0, 0, 0, 0.85))
	_equip_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hot.add_child(_equip_label)
	_slot_box = HBoxContainer.new()
	_slot_box.alignment = BoxContainer.ALIGNMENT_CENTER
	_slot_box.add_theme_constant_override("separation", 6)
	hot.add_child(_slot_box)
	# ---- crosshair & prompts
	_crosshair = Control.new()
	_crosshair.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_crosshair)
	var ch_tex := UIStyle.tex("ui_crosshair")
	if ch_tex:
		var tr := TextureRect.new()
		tr.texture = ch_tex
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.custom_minimum_size = Vector2(36, 36)
		tr.size = Vector2(36, 36)
		tr.position = Vector2(-18, -18)
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_crosshair.add_child(tr)
	else:
		var dot := UIStyle.label("+", 30, Color(1, 1, 1, 0.9), "ui", 6, Color(0, 0, 0, 0.8))
		dot.position = Vector2(-9, -22)
		_crosshair.add_child(dot)
	_hitmark = UIStyle.label("✕", 30, Color(1.0, 0.85, 0.3, 0.0), "ui", 6, Color(0, 0, 0, 0.6))
	_hitmark.position = Vector2(-11, -22)
	_crosshair.add_child(_hitmark)
	_interact_panel = _dark_panel(8)
	_interact_panel.custom_minimum_size = Vector2(400, 0)
	UIStyle.anchor(_interact_panel, Control.PRESET_CENTER, Vector2(-200, 44))
	_interact_label = UIStyle.label("", 19, UIStyle.PARCHMENT, "ui")
	_interact_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_interact_panel.add_child(_interact_label)
	_interact_panel.visible = false
	add_child(_interact_panel)
	_aim_label = UIStyle.label("", 16, Color(0.9, 0.95, 1.0), "body", 5, Color(0, 0, 0, 0.85))
	_aim_label.custom_minimum_size = Vector2(600, 0)
	UIStyle.anchor(_aim_label, Control.PRESET_CENTER, Vector2(-300, 96))
	_aim_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_aim_label)
	# ---- quest tracker (top-right)
	_quest_panel = _dark_panel(12)
	_quest_panel.custom_minimum_size = Vector2(370, 0)
	UIStyle.anchor(_quest_panel, Control.PRESET_TOP_RIGHT, Vector2(-392, 20))
	add_child(_quest_panel)
	var qv := VBoxContainer.new()
	qv.add_theme_constant_override("separation", 4)
	_quest_panel.add_child(qv)
	_quest_title = UIStyle.label("", 21, UIStyle.GOLD, "ui")
	_quest_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	qv.add_child(_quest_title)
	_quest_lines = VBoxContainer.new()
	qv.add_child(_quest_lines)
	# ---- compass, challenge, boss (top-center)
	_compass = Compass.new()
	UIStyle.anchor(_compass, Control.PRESET_CENTER_TOP, Vector2(-280, 16))
	_compass.size = Vector2(560, 40)
	add_child(_compass)
	_challenge_panel = _dark_panel(8)
	_challenge_panel.custom_minimum_size = Vector2(520, 0)
	UIStyle.anchor(_challenge_panel, Control.PRESET_CENTER_TOP, Vector2(-260, 64))
	_challenge_label = UIStyle.label("", 20, UIStyle.TEAL, "ui")
	_challenge_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_challenge_panel.add_child(_challenge_label)
	_challenge_panel.visible = false
	add_child(_challenge_panel)
	_boss_panel = VBoxContainer.new()
	_boss_panel.custom_minimum_size = Vector2(660, 0)
	UIStyle.anchor(_boss_panel, Control.PRESET_CENTER_TOP, Vector2(-330, 64))
	_boss_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_boss_name = UIStyle.label("", 26, Color("ffd2a8"), "display", 8, Color("2a0a10"))
	_boss_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_boss_panel.add_child(_boss_name)
	_boss_bar = _bar(Color("d8433f"), 20, 660)
	_boss_panel.add_child(_boss_bar)
	_boss_panel.visible = false
	add_child(_boss_panel)
	# ---- pilot telemetry, fps
	_pilot_label = UIStyle.label("", 18, UIStyle.PARCHMENT, "ui", 5, Color(0, 0, 0, 0.85))
	_pilot_label.custom_minimum_size = Vector2(600, 0)
	UIStyle.anchor(_pilot_label, Control.PRESET_CENTER_BOTTOM, Vector2(-300, -190))
	_pilot_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_pilot_label)
	_fps_label = UIStyle.label("", 14, Color(1, 1, 1, 0.7), "body", 4, Color(0, 0, 0, 0.8))
	UIStyle.anchor(_fps_label, Control.PRESET_BOTTOM_RIGHT, Vector2(-90, -28))
	add_child(_fps_label)


func _bar_row(color: Color, h: float, w: float) -> Array:
	var holder := Control.new()
	holder.custom_minimum_size = Vector2(w, h)
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var b := _bar(color, h, w)
	holder.add_child(b)
	var l := UIStyle.label("", int(h * 0.72), Color.WHITE, "ui", 4, Color(0, 0, 0, 0.9))
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.custom_minimum_size = Vector2(w, h)
	l.position.y = -1
	holder.add_child(l)
	return [b, l, holder]


func bind(p: Player) -> void:
	player = p
	p.health_changed.connect(_on_health)
	p.mana_changed.connect(func(m, mx): _mp_bar.value = m / mx * 100.0; _mp_label.text = "%d / %d" % [int(m), int(mx)])
	p.stamina_changed.connect(func(s, mx): _st_bar.value = s / mx * 100.0)
	p.equipment_switched.connect(func(_id): _rebuild_slots())
	p.interact_hint_changed.connect(_on_interact)
	p.aim_info_changed.connect(func(t): _aim_label.text = t)
	Game.gold_changed.connect(func(g, _d): _gold_target = g)
	Game.xp_changed.connect(func(_x, _l): _update_xp())
	Game.leveled_up.connect(func(_l): _update_xp())
	Game.equipment_changed.connect(_rebuild_slots)
	Game.inventory_changed.connect(_update_consumables)
	Quests.tracked_changed.connect(func(_q): _update_quest())
	Quests.quest_updated.connect(func(_q): _update_quest())
	Quests.quest_ready.connect(func(_q): _update_quest())
	Quests.quest_completed.connect(func(_q): _update_quest())
	Events.enemy_damaged.connect(_on_enemy_damaged)
	Events.player_damaged.connect(func(a, _t): _hurt_t = clampf(a / 25.0, 0.3, 1.0))
	Events.boss_started.connect(_on_boss)
	Events.boss_ended.connect(func(_b): _boss = null; _boss_panel.visible = false)
	var bm := get_tree().get_first_node_in_group("build_manager") as BuildManager
	if bm:
		bm.placed_changed.connect(func(c, l): _parts_label.text = "Parts placed %d / %d" % [c, l])
		_parts_label.text = "Parts placed %d / %d" % [bm.placed_count, bm.limit()]
	_gold_target = Game.gold
	_gold_shown = Game.gold
	_gold_label.text = str(Game.gold)
	_on_health(p.health, Game.max_health())
	_mp_bar.value = p.mana / Game.max_mana() * 100.0
	_update_xp()
	_rebuild_slots()
	_update_consumables()
	_update_quest()
	_compass.player = p


func _on_health(h: float, mx: float) -> void:
	_hp_bar.value = h / mx * 100.0
	_hp_label.text = "%d / %d" % [int(ceil(h)), int(mx)]


func _update_xp() -> void:
	_level_label.text = str(Game.level)
	_xp_bar.value = float(Game.xp) / Game.xp_to_next() * 100.0


func _update_consumables() -> void:
	_tonic_label.text = "[H] Tonic ×%d" % Game.item_count("health_tonic")
	_draught_label.text = "[G] Draught ×%d" % Game.item_count("mana_draught")


func _rebuild_slots() -> void:
	for c in _slot_box.get_children():
		c.queue_free()
	_slots.clear()
	if player == null:
		return
	for i in Game.hotbar.size():
		var id: String = Game.hotbar[i]
		var slot := PanelContainer.new()
		slot.custom_minimum_size = Vector2(72, 72)
		var sel := i == player.slot
		var tex := UIStyle.tex("ui_slot_selected" if sel else "ui_slot")
		if tex:
			var sbt := StyleBoxTexture.new()
			sbt.texture = tex
			sbt.set_content_margin_all(8)
			slot.add_theme_stylebox_override("panel", sbt)
		else:
			var sb := StyleBoxFlat.new()
			sb.bg_color = Color(0.07, 0.07, 0.12, 0.8)
			sb.border_color = UIStyle.TEAL if sel else Color(0.85, 0.65, 0.3, 0.8)
			sb.set_border_width_all(4 if sel else 2)
			sb.set_corner_radius_all(12)
			sb.set_content_margin_all(6)
			slot.add_theme_stylebox_override("panel", sb)
		slot.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var icon := Catalog.equipment_icon(id)
		if icon:
			var tr := TextureRect.new()
			tr.texture = icon
			tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
			slot.add_child(tr)
		else:
			var nm := Catalog.display_name(id)
			var l := UIStyle.label(nm.substr(0, 2).to_upper(), 24, UIStyle.PARCHMENT, "display")
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			slot.add_child(l)
		var key := UIStyle.label(str(i + 1), 14, UIStyle.GOLD, "ui", 4, Color(0, 0, 0, 0.9))
		key.position = Vector2(4, 0)
		slot.add_child(key)
		if sel:
			slot.scale = Vector2(1.08, 1.08)
		_slot_box.add_child(slot)
		_slots.append(slot)


func _on_interact(t: String) -> void:
	_interact_panel.visible = t != ""
	_interact_label.text = t


func _on_enemy_damaged(_e: Node, _amount: float, _pos: Vector3, _type: String) -> void:
	_hit_t = 0.18


func _on_boss(b: Node, display_name: String) -> void:
	_boss = b
	_boss_name.text = display_name
	_boss_panel.visible = false


func _update_quest() -> void:
	for c in _quest_lines.get_children():
		c.queue_free()
	var q := Quests.tracked
	if q == "" or not Quests.is_active(q):
		_quest_panel.visible = false
		_compass.target = null
		return
	_quest_panel.visible = true
	var d := Quests.def(q)
	_quest_title.text = d["title"]
	if Quests.status(q) == "ready":
		var l := UIStyle.label("★ Return to %s" % QuestDB.NPC_NAMES.get(d["turn_in"], "the quest giver"), 17, UIStyle.GOLD, "body", 0)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_quest_lines.add_child(l)
	else:
		for i in d["objectives"].size():
			var done := Quests.objective_done(q, i)
			var l2 := UIStyle.label(("✔ " if done else "• ") + Quests.objective_text(q, i), 17,
				Color(0.6, 0.85, 0.6) if done else UIStyle.PARCHMENT, "body", 0)
			l2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			l2.custom_minimum_size = Vector2(340, 0)
			_quest_lines.add_child(l2)
	_compass.target = QuestNav.target_for(q, get_tree())


func _process(delta: float) -> void:
	if player == null:
		return
	if absf(_gold_shown - _gold_target) > 0.5:
		_gold_shown = lerpf(_gold_shown, float(_gold_target), 1.0 - exp(-8.0 * delta))
		if absf(_gold_shown - _gold_target) < 1.0:
			_gold_shown = _gold_target
		_gold_label.text = str(int(round(_gold_shown)))
		_gold_label.scale = Vector2.ONE * 1.12
	else:
		_gold_label.scale = _gold_label.scale.lerp(Vector2.ONE, 1.0 - exp(-10.0 * delta))
	if _hit_t > 0.0:
		_hit_t -= delta
	_hitmark.modulate.a = clampf(_hit_t / 0.18, 0.0, 1.0)
	_hitmark.add_theme_color_override("font_color", Color(1.0, 0.85, 0.3, clampf(_hit_t / 0.18, 0.0, 1.0)))
	_hurt_t = maxf(0.0, _hurt_t - delta * 1.4)
	var vm := _vignette.material as ShaderMaterial
	var low_hp := clampf(1.0 - player.health / Game.max_health() * 2.5, 0.0, 1.0)
	if player.ward_timer > 0.0:
		vm.set_shader_parameter("tint", Color(0.4, 1.0, 0.55, 0.35))
	else:
		vm.set_shader_parameter("tint", Color(0.85, 0.05, 0.12, maxf(_hurt_t * 0.8, low_hp * (0.35 + 0.15 * sin(Time.get_ticks_msec() / 200.0)))))
	var cur := player.current
	if cur:
		_equip_label.text = "%s  ·  %s" % [Catalog.display_name(player.current_id), cur.status()]
		_hint_label.text = cur.hint()
	if player.piloting:
		var c := player.piloting
		var spd := c.linear_velocity.length() * 3.6
		var alt := c._height_above_ground()
		_pilot_label.text = "%d km/h  ·  altitude %.1f m  ·  %s\nWASD drive · Space/Ctrl lift · LMB turrets · F lights · V camera · E exit" % [int(spd), alt, c.describe()]
		_hint_label.text = ""
		_equip_label.text = ""
		_slot_box.visible = false
		_crosshair.visible = not player.third_person
	else:
		_pilot_label.text = ""
		_slot_box.visible = true
		_crosshair.visible = true
	if Challenges.running != "":
		var ui := get_parent() as GameUI
		var r := _runner_for(Challenges.running)
		_challenge_panel.visible = true
		_challenge_label.text = "%s  ·  %s" % [Challenges.def(Challenges.running)["name"], r.status_text() if r else ""]
	else:
		_challenge_panel.visible = false
	if _boss and is_instance_valid(_boss) and not _boss.dead:
		var dist: float = (_boss as Node3D).global_position.distance_to(player.global_position)
		_boss_panel.visible = dist < 90.0
		_boss_bar.value = _boss.hp / _boss.max_hp * 100.0
		if _boss_panel.visible:
			_challenge_panel.offset_top = 130.0
	else:
		_boss_panel.visible = false
		_challenge_panel.offset_top = 64.0
	_fps_label.visible = Settings.show_fps
	if Settings.show_fps:
		_fps_label.text = "%d FPS" % Engine.get_frames_per_second()


func _runner_for(id: String) -> ChallengeRunner:
	var pb := get_tree().get_first_node_in_group("world")
	if pb and pb.pois:
		return pb.pois.challenges.get(id, null)
	return null
