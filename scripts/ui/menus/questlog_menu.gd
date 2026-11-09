class_name QuestLogMenu
extends MenuPanel
## Quest log [J]: active and completed quests with objectives and rewards.

var _list: VBoxContainer
var _detail: RichTextLabel
var _buttons: HBoxContainer
var _selected: String = ""


func _init() -> void:
	panel_size = Vector2(1150, 720)
	title_text = "Quest Log"


func build() -> void:
	var hb := HBoxContainer.new()
	hb.size_flags_vertical = Control.SIZE_EXPAND_FILL
	hb.add_theme_constant_override("separation", 18)
	content.add_child(hb)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(390, 0)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	hb.add_child(sc)
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 6)
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(_list)
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hb.add_child(right)
	var sc2 := ScrollContainer.new()
	sc2.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc2.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	right.add_child(sc2)
	_detail = MenuPanel.rich("", 19)
	_detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc2.add_child(_detail)
	_buttons = HBoxContainer.new()
	_buttons.add_theme_constant_override("separation", 10)
	right.add_child(_buttons)
	_selected = Quests.tracked
	_fill()


func _fill() -> void:
	for c in _list.get_children():
		c.queue_free()
	var active := Quests.active_quests()
	active.sort_custom(func(a, b): return int(Quests.def(a).get("main", false)) > int(Quests.def(b).get("main", false)))
	_list.add_child(UIStyle.label("Active", 24, Color("8a5a22"), "display"))
	if active.is_empty():
		_list.add_child(UIStyle.label("No active quests. Look for ! markers in town.", 17, Color("5a4632"), "body"))
	for q in active:
		_list.add_child(_entry(q))
	_list.add_child(UIStyle.label("Completed", 24, Color("8a5a22"), "display"))
	for q in Quests.completed_quests():
		if Quests.is_active(q):
			continue
		_list.add_child(_entry(q))
	if _selected == "" and not active.is_empty():
		_selected = active[0]
	_show(_selected)


func _entry(q: String) -> Button:
	var d := Quests.def(q)
	var mark := "★ " if Quests.status(q) == "ready" else ("◆ " if d.get("main", false) else "• ")
	if not Quests.is_active(q):
		mark = "✔ "
	var b := MenuPanel.button(mark + d["title"] + ("  (tracked)" if q == Quests.tracked else ""), func(): _show(q))
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	return b


func _show(q: String) -> void:
	_selected = q
	for c in _buttons.get_children():
		c.queue_free()
	if q == "" or Quests.def(q).is_empty():
		_detail.text = "Select a quest."
		return
	var d := Quests.def(q)
	var who: String = QuestDB.NPC_NAMES.get(d["giver"], "")
	var s := "[font_size=28][b]%s[/b][/font_size]\n[i]From %s%s[/i]\n\n" % [d["title"], who, "  ·  Main story" if d.get("main", false) else ""]
	s += d.get("offer", "") + "\n\n[b]Objectives[/b]\n"
	for i in d["objectives"].size():
		var done := Quests.objective_done(q, i) if Quests.is_active(q) else not Quests.is_active(q)
		s += ("  ✔ " if done else "  • ") + Quests.objective_text(q, i) + "\n"
	if Quests.status(q) == "ready":
		s += "\n[color=#8a5a10][b]Complete! Return to %s.[/b][/color]\n" % QuestDB.NPC_NAMES.get(d["turn_in"], "")
	var r: Dictionary = d.get("rewards", {})
	s += "\n[b]Rewards:[/b] %d gold, %d XP" % [int(r.get("gold", 0)), int(r.get("xp", 0))]
	for p in r.get("unlock_parts", []):
		s += ", blueprint: " + Catalog.display_name(p)
	_detail.text = s
	if Quests.is_active(q):
		_buttons.add_child(MenuPanel.button("Track", func():
			Quests.set_tracked(q)
			_fill(), 160))
		if not d.get("main", false):
			_buttons.add_child(MenuPanel.button("Abandon", func():
				Quests.abandon(q)
				_selected = ""
				_fill(), 160))
