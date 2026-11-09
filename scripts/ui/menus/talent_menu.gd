class_name TalentMenu
extends MenuPanel
## Talents [K]: one point per level, spent across three trees (Tinker, Arcanist, Wayfarer). Each talent
## has a few ranks and unlocks at a player level. Points can be refunded for gold.

var ui: GameUI
var _cols: HBoxContainer
var _points: Label
var _dirty: bool = false


func _init() -> void:
	panel_size = Vector2(1320, 820)
	title_text = "Talents"


func build() -> void:
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 14)
	content.add_child(top)
	_points = UIStyle.label("", 24, Color("5a3f8a"), "display")
	top.add_child(_points)
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(sp)
	var reset := MenuPanel.button("Refund all points (%d gold)" % Game.respec_cost(), func():
		if Game.reset_talents():
			AudioManager.play_ui("ui_buy", -4.0)
			Events.toast("Talent points refunded", "info")
		else:
			AudioManager.play_ui("ui_error"), 0)
	reset.name = "Reset"
	top.add_child(reset)
	var hint := UIStyle.label("You earn a talent point every level (up to level %d). Higher rows open at higher levels." % Catalog.MAX_LEVEL,
		16, Color("5a4632"), "body")
	content.add_child(hint)
	_cols = HBoxContainer.new()
	_cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_cols.add_theme_constant_override("separation", 14)
	content.add_child(_cols)
	Game.talents_changed.connect(_mark_dirty)
	Game.xp_changed.connect(func(_x, _l): _mark_dirty())
	_refresh()


func _mark_dirty() -> void:
	if not _dirty:
		_dirty = true
		_refresh.call_deferred()


func _refresh() -> void:
	_dirty = false
	if not is_instance_valid(_cols):
		return
	var pts := Game.talent_points()
	_points.text = "Level %d  ·  %d talent point%s to spend" % [Game.level, pts, "" if pts == 1 else "s"]
	var reset := content.find_child("Reset", true, false) as Button
	if reset:
		reset.text = "Refund all points (%d gold)" % Game.respec_cost()
		reset.disabled = Game.talents.is_empty()
	for c in _cols.get_children():
		c.queue_free()
	for tree_id in Catalog.TALENT_TREES:
		_cols.add_child(_tree_column(tree_id))


func _tree_column(tree_id: String) -> Control:
	var td: Dictionary = Catalog.TALENT_TREES[tree_id]
	var col: Color = td["color"]
	var pc := PanelContainer.new()
	pc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(col, 0.12)
	sb.border_color = Color(col, 0.7)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(12)
	sb.set_content_margin_all(12)
	pc.add_theme_stylebox_override("panel", sb)
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	pc.add_child(sc)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 8)
	sc.add_child(v)
	var spent := 0
	for t in Catalog.TALENTS:
		if Catalog.TALENTS[t]["tree"] == tree_id:
			spent += Game.talent_rank(t)
	v.add_child(UIStyle.label("%s  (%d)" % [td["name"], spent], 28, col.darkened(0.35), "display"))
	v.add_child(UIStyle.label(str(td["desc"]), 15, Color("5a4632"), "body"))
	for t in Catalog.TALENTS:
		var d: Dictionary = Catalog.TALENTS[t]
		if d["tree"] != tree_id:
			continue
		v.add_child(_talent_card(t, d, col))
	return pc


func _talent_card(id: String, d: Dictionary, col: Color) -> Control:
	var rank := Game.talent_rank(id)
	var maxr := int(d["ranks"])
	var locked := Game.level < int(d["level"])
	var pc := PanelContainer.new()
	pc.name = "Talent_" + id
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(1, 1, 1, 0.45 if not locked else 0.2)
	sb.border_color = Color(col, 0.9 if rank > 0 else 0.35)
	sb.set_border_width_all(2 if rank > 0 else 1)
	sb.set_corner_radius_all(10)
	sb.set_content_margin_all(10)
	pc.add_theme_stylebox_override("panel", sb)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 10)
	pc.add_child(h)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var pips := ""
	for i in maxr:
		pips += "●" if i < rank else "○"
	v.add_child(UIStyle.label("%s   %s" % [d["name"], pips], 20, UIStyle.INK if not locked else Color("8a7a68"), "ui"))
	var dl := UIStyle.label(str(d["desc"]), 15, Color("4a3a2a") if not locked else Color("8a7a68"), "body")
	dl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	dl.custom_minimum_size = Vector2(260, 0)
	v.add_child(dl)
	if locked:
		v.add_child(UIStyle.label("Unlocks at level %d" % int(d["level"]), 14, Color("9a3a2a"), "body"))
	var b := MenuPanel.button("+", func():
		if Game.learn_talent(id):
			AudioManager.play_ui("talent_unlock", -3.0)
		else:
			AudioManager.play_ui("ui_error"), 54, not Game.can_learn_talent(id))
	b.name = "Learn_" + id
	b.tooltip_text = "Spend a talent point" if rank < maxr else "Maxed"
	h.add_child(b)
	return pc
