class_name Hud
extends Control
## In-game HUD: vitals, gold and pack, the hotbar, buffs, crosshair and prompts, the quest tracker, the
## compass, the objective tracker (what to do next, how far, which way), boss and challenge bars, and
## the level-up banner.

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
var _slots: Array = []          # [{panel, meter, count, index}] for the 8 hotbar slots
var _slot_box: HBoxContainer
var _buff_box: HBoxContainer
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
var _map_t: float = 0.0
var _nav_t: int = 0
var _hurt_t: float = 0.0
var _pack_label: Label
var _obj_panel: PanelContainer
var _obj_text: Label
var _obj_sub: Label
var _obj_hint: Label
var _obj_dist: Label
var _obj_target: Variant = null
var _obj_last: String = ""
var _obj_t: float = 0.0
var _obj_ping_t: float = 0.0
var _obj_flash: float = 0.0
var _lvl_panel: VBoxContainer
var _lvl_title: Label
var _lvl_sub: Label
var _lvl_t: float = 0.0
var _area_panel: VBoxContainer
var _area_name: Label
var _area_sub: Label
var _area_new: Label
var _area_t: float = 0.0
var _area_id: String = ""
var _area_pos: Vector3 = Vector3.INF   # where the area was last checked


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
	_pack_label = UIStyle.label("Pack 0/0", 16, UIStyle.PARCHMENT, "ui", 4, Color(0, 0, 0, 0.8))
	_pack_label.position = Vector2(26, 98)
	add_child(_pack_label)
	# ---- hotbar (bottom-center)
	var hot := VBoxContainer.new()
	hot.custom_minimum_size = Vector2(760, 0)
	UIStyle.anchor(hot, Control.PRESET_CENTER_BOTTOM, Vector2(-380, -138))
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
	# ---- active buffs (above the vitals)
	_buff_box = HBoxContainer.new()
	_buff_box.add_theme_constant_override("separation", 8)
	_buff_box.custom_minimum_size = Vector2(400, 30)
	UIStyle.anchor(_buff_box, Control.PRESET_BOTTOM_LEFT, Vector2(24, -306))
	_buff_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_buff_box)
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
	# ---- objective tracker (under the compass): the next step, its distance and direction
	_obj_panel = _dark_panel(10)
	_obj_panel.custom_minimum_size = Vector2(600, 0)
	UIStyle.anchor(_obj_panel, Control.PRESET_CENTER_TOP, Vector2(-300, 62))
	var osb := _obj_panel.get_theme_stylebox("panel").duplicate() as StyleBoxFlat
	osb.border_color = Color(UIStyle.TEAL, 0.9)
	osb.border_width_left = 6
	_obj_panel.add_theme_stylebox_override("panel", osb)
	var oh := HBoxContainer.new()
	oh.add_theme_constant_override("separation", 12)
	oh.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_obj_panel.add_child(oh)
	var ov := VBoxContainer.new()
	ov.add_theme_constant_override("separation", 1)
	ov.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ov.mouse_filter = Control.MOUSE_FILTER_IGNORE
	oh.add_child(ov)
	var otag := UIStyle.label("OBJECTIVE", 13, UIStyle.TEAL, "ui", 3, Color(0, 0, 0, 0.8))
	ov.add_child(otag)
	_obj_text = UIStyle.label("", 21, UIStyle.PARCHMENT, "ui", 4, Color(0, 0, 0, 0.85))
	_obj_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_obj_text.custom_minimum_size = Vector2(470, 0)
	ov.add_child(_obj_text)
	_obj_sub = UIStyle.label("", 15, Color(0.85, 0.82, 0.74), "body", 3, Color(0, 0, 0, 0.8))
	_obj_sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_obj_sub.custom_minimum_size = Vector2(470, 0)
	ov.add_child(_obj_sub)
	_obj_hint = UIStyle.label("", 14, UIStyle.GOLD, "body", 3, Color(0, 0, 0, 0.8))
	ov.add_child(_obj_hint)
	_obj_dist = UIStyle.label("", 22, UIStyle.GOLD, "display", 5, Color(0, 0, 0, 0.85))
	_obj_dist.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_obj_dist.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_obj_dist.custom_minimum_size = Vector2(90, 0)
	oh.add_child(_obj_dist)
	_obj_panel.visible = false
	add_child(_obj_panel)
	# ---- level-up banner
	_lvl_panel = VBoxContainer.new()
	_lvl_panel.custom_minimum_size = Vector2(700, 0)
	UIStyle.anchor(_lvl_panel, Control.PRESET_CENTER_TOP, Vector2(-350, 190))
	_lvl_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_lvl_title = UIStyle.label("", 58, UIStyle.GOLD, "display", 10, Color("2a1030"))
	_lvl_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_lvl_panel.add_child(_lvl_title)
	_lvl_sub = UIStyle.label("", 21, UIStyle.PARCHMENT, "ui", 6, Color(0, 0, 0, 0.9))
	_lvl_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_lvl_sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_lvl_panel.add_child(_lvl_sub)
	_lvl_panel.visible = false
	add_child(_lvl_panel)
	# ---- "now entering" area banner
	_area_panel = VBoxContainer.new()
	_area_panel.custom_minimum_size = Vector2(700, 0)
	UIStyle.anchor(_area_panel, Control.PRESET_CENTER_TOP, Vector2(-350, 300))
	_area_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_area_name = UIStyle.label("", 40, UIStyle.PARCHMENT, "display", 9, Color(0.1, 0.06, 0.12, 0.95))
	_area_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_area_panel.add_child(_area_name)
	_area_sub = UIStyle.label("", 18, UIStyle.GOLD, "ui", 6, Color(0, 0, 0, 0.9))
	_area_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_area_panel.add_child(_area_sub)
	_area_new = UIStyle.label("", 20, Color("8ff5e6"), "ui", 6, Color(0, 0, 0, 0.9))
	_area_new.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_area_new.visible = false
	_area_panel.add_child(_area_new)
	_area_panel.visible = false
	add_child(_area_panel)
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
	p.buffs_changed.connect(_rebuild_buffs)
	p.interact_hint_changed.connect(_on_interact)
	p.aim_info_changed.connect(func(t): _aim_label.text = t)
	Game.gold_changed.connect(func(g, _d): _gold_target = g)
	Game.xp_changed.connect(func(_x, _l): _update_xp())
	Game.leveled_up.connect(func(_l): _update_xp())
	Game.equipment_changed.connect(_rebuild_slots)
	Game.loadout_changed.connect(_rebuild_slots)
	Game.inventory_changed.connect(_update_consumables)
	Game.inventory_changed.connect(_update_quick_counts)
	Game.inventory_changed.connect(_update_pack)
	Game.pouches_changed.connect(_update_pack)
	Game.talents_changed.connect(_update_pack)
	Game.leveled_up.connect(_show_level_up)
	Game.milestone_reached.connect(_on_milestone)
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
	_update_pack()
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
	for i in Player.SELECT_SLOTS + Game.QUICK_SLOTS:
		if i == Game.WEAPON_SLOTS or i == Player.SELECT_SLOTS:
			var gap := Control.new()
			gap.custom_minimum_size = Vector2(10, 0)
			gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
			_slot_box.add_child(gap)
		_slot_box.add_child(_make_slot(i))
	_update_quick_counts()


## One hotbar slot: 0-1 weapons (bigger, rarity border, ammo meter), 2-3 tools, 4-7 quick items.
func _make_slot(i: int) -> Control:
	var is_weapon := i < Game.WEAPON_SLOTS
	var is_quick := i >= Player.SELECT_SLOTS
	var sz := 84.0 if is_weapon else (72.0 if not is_quick else 62.0)
	var sel := i == player.slot and not is_quick
	var slot := PanelContainer.new()
	slot.custom_minimum_size = Vector2(sz, sz)
	slot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var tex := UIStyle.tex("ui_slot_selected" if sel else "ui_slot")
	var rarity := -1
	var icon: Texture2D = null
	var short := ""
	var entry := {}
	if is_quick:
		var qid: String = Game.quick[i - Player.SELECT_SLOTS]
		if qid != "":
			icon = Catalog.stack_icon(qid)
			short = Catalog.display_name(qid)
		entry["item"] = qid
	else:
		var e := player.slot_entry(i)
		if not e.is_empty():
			if is_weapon:
				rarity = int(e["weapon"].get("rarity", 0))
				icon = Catalog.weapon_icon(e["weapon"])
				short = Catalog.display_name(e["id"])
			else:
				icon = Catalog.equipment_icon(e["id"])
				short = Catalog.display_name(e["id"])
		entry["uid"] = int(e.get("uid", 0))
	if tex:
		var sbt := StyleBoxTexture.new()
		sbt.texture = tex
		sbt.set_content_margin_all(8 if not is_quick else 7)
		slot.add_theme_stylebox_override("panel", sbt)
	else:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.07, 0.07, 0.12, 0.8)
		sb.border_color = UIStyle.TEAL if sel else Color(0.85, 0.65, 0.3, 0.8)
		sb.set_border_width_all(4 if sel else 2)
		sb.set_corner_radius_all(12)
		sb.set_content_margin_all(6)
		slot.add_theme_stylebox_override("panel", sb)
	var holder := Control.new()
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	slot.add_child(holder)
	if rarity >= 0:
		# rarity frame drawn over the slot texture
		var frame := Panel.new()
		var fs := StyleBoxFlat.new()
		fs.bg_color = Color(Catalog.rarity_color(rarity), 0.12)
		fs.border_color = Catalog.rarity_color(rarity)
		fs.set_border_width_all(3)
		fs.set_corner_radius_all(10)
		frame.add_theme_stylebox_override("panel", fs)
		frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		frame.offset_left = -4
		frame.offset_top = -4
		frame.offset_right = 4
		frame.offset_bottom = 4
		frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(frame)
	if icon:
		var tr := TextureRect.new()
		tr.texture = icon
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(tr)
	elif short != "":
		var l := UIStyle.label(short.substr(0, 2).to_upper(), 24, UIStyle.PARCHMENT, "display")
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		l.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		holder.add_child(l)
	elif is_weapon or is_quick:
		var el := UIStyle.label("empty" if is_weapon else "·", 13 if is_weapon else 22, Color(1, 1, 1, 0.45), "body")
		el.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		el.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		el.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		holder.add_child(el)
	var key := UIStyle.label(str(i + 1), 14, UIStyle.GOLD if not is_quick else UIStyle.TEAL, "ui", 4, Color(0, 0, 0, 0.9))
	key.position = Vector2(-2, -6)
	holder.add_child(key)
	var meter: ProgressBar = null
	if is_weapon and short != "":
		meter = ProgressBar.new()
		meter.show_percentage = false
		meter.max_value = 1.0
		meter.step = 0.0
		meter.custom_minimum_size = Vector2(sz - 22, 6)
		meter.position = Vector2(2, sz - 22)
		meter.size = Vector2(sz - 22, 6)
		var bg := StyleBoxFlat.new()
		bg.bg_color = Color(0, 0, 0, 0.6)
		bg.set_corner_radius_all(3)
		var fg := StyleBoxFlat.new()
		fg.bg_color = Catalog.rarity_color(rarity).lerp(Color.WHITE, 0.2)
		fg.set_corner_radius_all(3)
		meter.add_theme_stylebox_override("background", bg)
		meter.add_theme_stylebox_override("fill", fg)
		meter.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(meter)
	var count: Label = null
	if is_quick:
		count = UIStyle.label("", 15, Color.WHITE, "ui", 4, Color(0, 0, 0, 0.95))
		count.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		count.position = Vector2(sz - 50, sz - 34)
		count.custom_minimum_size = Vector2(34, 0)
		holder.add_child(count)
	if sel:
		slot.scale = Vector2(1.08, 1.08)
		slot.pivot_offset = Vector2(sz, sz) * 0.5
	entry.merge({"panel": slot, "meter": meter, "count": count, "index": i, "icon": icon})
	_slots.append(entry)
	return slot


func _update_quick_counts() -> void:
	for s in _slots:
		if s.get("count") == null or not is_instance_valid(s["count"]):
			continue
		var id: String = s.get("item", "")
		var n := Game.item_count(id) if id != "" else 0
		(s["count"] as Label).text = ("×%d" % n) if id != "" else ""
		(s["panel"] as Control).modulate = Color(1, 1, 1, 1.0 if n > 0 or id == "" else 0.45)


func _update_slot_meters() -> void:
	for s in _slots:
		var m: ProgressBar = s.get("meter")
		if m == null or not is_instance_valid(m):
			continue
		var h: EquipBase = player.handlers.get(Player.weapon_key(int(s.get("uid", 0))))
		m.value = h.meter() if h and h.meter() >= 0.0 else 1.0


func _rebuild_buffs() -> void:
	for c in _buff_box.get_children():
		c.queue_free()
	if player == null:
		return
	for b in player.buffs:
		var pc := _dark_panel(5)
		var l := UIStyle.label("", 16, Catalog.BUFFS[b]["color"], "ui", 4, Color(0, 0, 0, 0.8))
		l.name = "L_" + b
		pc.add_child(l)
		_buff_box.add_child(pc)


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
		_obj_t = 0.0
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
	_obj_t = 0.0


func _update_pack() -> void:
	var used := Game.pack_used()
	var cap := Game.pack_capacity()
	_pack_label.text = "Pack %d / %d  ·  %d pouch%s" % [used, cap, Game.pouch_count(), "" if Game.pouch_count() == 1 else "es"]
	var full := used >= cap
	_pack_label.add_theme_color_override("font_color", Color("ff7a5c") if full else (Color("ffd27a") if used >= cap - 2 else UIStyle.PARCHMENT))


## Refresh the objective tracker from the Guide (twice a second).
func _update_objective() -> void:
	var o := Guide.next_objective(get_tree())
	if o.is_empty() or Challenges.running != "":
		_obj_panel.visible = false
		_obj_target = null
		_compass.target = null
		return
	# the compass keeps pointing at the objective even with the banner switched off in Settings
	_obj_panel.visible = Settings.show_objective
	var text := str(o["text"])
	_obj_text.text = text
	_obj_sub.text = str(o.get("sub", ""))
	_obj_sub.visible = _obj_sub.text != ""
	_obj_hint.text = ("✦ " + str(o["hint"])) if str(o.get("hint", "")) != "" else ""
	_obj_hint.visible = _obj_hint.text != ""
	_obj_target = o.get("target")
	_compass.target = _obj_target
	if text != _obj_last:
		if _obj_last != "" and _obj_ping_t <= 0.0:
			AudioManager.play_ui("objective_ping", -6.0)
			_obj_ping_t = 2.0
		_obj_last = text
		_obj_flash = 1.0
		Events.objective_changed.emit(text)


## Distance and a direction arrow to the objective, relative to where the player faces.
func _objective_distance() -> void:
	if _obj_target == null or not (_obj_target is Vector3):
		_obj_dist.text = ""
		return
	var to: Vector3 = (_obj_target as Vector3) - player.global_position
	var flat := Vector2(to.x, to.z)
	var d := flat.length()
	if d < 4.0:
		_obj_dist.text = "here"
		return
	var fwd := -player.global_transform.basis.z
	var rel := wrapf(atan2(flat.x, flat.y) - atan2(fwd.x, fwd.z), -PI, PI)
	var arrows := ["↑", "↖", "←", "↙", "↓", "↘", "→", "↗"]
	var idx := int(round(rel / (TAU / 8.0))) % 8
	if idx < 0:
		idx += 8
	_obj_dist.text = "%s %d m" % [arrows[idx], int(d)] if d < 1000.0 else "%s %.1f km" % [arrows[idx], d / 1000.0]


## The named region (WorldLayout.AREAS) a point lies in: the smallest one that contains it, or "".
static func area_at(pos: Vector3) -> String:
	var here := Vector2(pos.x, pos.z)
	var best := ""
	var best_r := INF
	for id in WorldLayout.AREAS:
		var a: Dictionary = WorldLayout.AREAS[id]
		if here.distance_to(a["pos"]) < float(a["radius"]) and float(a["radius"]) < best_r:
			best = id
			best_r = float(a["radius"])
	return best


## "Now entering" banner with the region's foe levels (coloured against the player's level).
func _check_area() -> void:
	if player.piloting and player.piloting.linear_velocity.length() > 25.0:
		return
	_area_pos = player.global_position
	var best := area_at(player.global_position)
	if best == _area_id:
		return
	var first := _area_id == ""
	_area_id = best
	if best == "":
		return
	# the first visit names the region on the map [M] (the one the player loads into counts quietly)
	var fresh := Game.discover_area(best, first)
	if first:
		return
	var a2: Dictionary = WorldLayout.AREAS[best]
	var lv: Array = a2["levels"]
	_area_name.text = str(a2["name"])
	var sub := str(a2.get("note", ""))
	if int(lv[1]) > 0:
		var lo := maxi(int(lv[0]), Game.level - 2)
		var hi := maxi(int(lv[1]), Game.level - 1)
		var danger := lo - Game.level
		var col := "c8c8c8" if danger <= -3 else ("ffe7b0" if danger <= 1 else ("ffae42" if danger <= 4 else "ff5a4d"))
		_area_sub.add_theme_color_override("font_color", Color(col))
		sub = "Foes Lv %d-%d  ·  %s" % [lo, hi, sub]
	else:
		_area_sub.add_theme_color_override("font_color", UIStyle.GOLD)
	_area_sub.text = sub
	_area_new.visible = fresh
	_area_new.text = "✦ New region discovered  ·  +%d XP  ·  marked on your map [M] ✦" % Game.discovery_xp(best) if fresh else ""
	if fresh:
		AudioManager.play_ui("objective_ping", -3.0)
	_area_t = 4.6 if fresh else 3.6
	_area_panel.visible = true
	_area_panel.modulate.a = 0.0


func _show_level_up(lvl: int) -> void:
	_lvl_title.text = "LEVEL %d!" % lvl
	var bits := ["+10 health", "+8 mana", "+3% damage", "+1 talent point [K]"]
	if Game.is_max_level():
		bits.append("Maximum level!")
	_lvl_sub.text = "  ·  ".join(bits)
	_lvl_t = 4.5
	_lvl_panel.visible = true
	_lvl_panel.modulate.a = 0.0
	_lvl_panel.pivot_offset = Vector2(350, 40)
	_lvl_panel.scale = Vector2.ONE * 1.3
	var tw := _lvl_panel.create_tween().set_parallel(true)
	tw.tween_property(_lvl_panel, "modulate:a", 1.0, 0.25)
	tw.tween_property(_lvl_panel, "scale", Vector2.ONE, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_obj_t = 0.0


func _on_milestone(lvl: int, rewards: Array) -> void:
	_lvl_sub.text += "\nLevel %d milestone cache: %s" % [lvl, ", ".join(rewards)]
	_lvl_t = maxf(_lvl_t, 6.0)


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
		_equip_label.text = "%s  ·  %s" % [player.current_name(), cur.status()]
		_hint_label.text = cur.hint()
	_update_slot_meters()
	_map_t -= delta
	if _map_t <= 0.0:
		_map_t = 0.5
		_compass.treasure = player.nearest_treasure() if player.has_buff("map") else null
	# objective tracker: re-plan twice a second ("nearest vein / crystal / Champion" moves with you)
	_obj_t -= delta
	_obj_ping_t -= delta
	if _obj_t <= 0.0:
		_obj_t = 0.5
		_update_objective()
		_check_area()
	elif _area_pos.distance_to(player.global_position) > 20.0:
		# a long jump (respawn, teleport, a fast vehicle): name the new area right away
		_check_area()
	if _obj_panel.visible:
		_objective_distance()
		if _obj_flash > 0.0:
			_obj_flash = maxf(0.0, _obj_flash - delta * 1.6)
			_obj_panel.modulate = Color(1, 1, 1).lerp(Color(1.6, 1.5, 1.1), _obj_flash)
	if _area_t > 0.0:
		_area_t -= delta
		_area_panel.modulate.a = clampf(minf(_area_t, (4.6 if _area_new.visible else 3.6) - _area_t) / 0.5, 0.0, 1.0)
		if _area_t <= 0.0:
			_area_panel.visible = false
	if _lvl_t > 0.0:
		_lvl_t -= delta
		if _lvl_t < 0.6:
			_lvl_panel.modulate.a = clampf(_lvl_t / 0.6, 0.0, 1.0)
		if _lvl_t <= 0.0:
			_lvl_panel.visible = false
	for pc in _buff_box.get_children():
		if pc.get_child_count() > 0:
			var bl := pc.get_child(0) as Label
			var bid := String(bl.name).substr(2)
			bl.text = "%s  %ds" % [Catalog.BUFFS.get(bid, {}).get("name", bid), int(ceil(float(player.buffs.get(bid, 0.0))))]
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
	var below := 64.0 if not _obj_panel.visible else 70.0 + _obj_panel.size.y
	_challenge_panel.offset_top = below
	_boss_panel.offset_top = below
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
			_challenge_panel.offset_top = below + 66.0
	else:
		_boss_panel.visible = false
	_fps_label.visible = Settings.show_fps
	if Settings.show_fps:
		_fps_label.text = "%d FPS" % Engine.get_frames_per_second()


func _runner_for(id: String) -> ChallengeRunner:
	var pb := get_tree().get_first_node_in_group("world")
	if pb and pb.pois:
		return pb.pois.challenges.get(id, null)
	return null
