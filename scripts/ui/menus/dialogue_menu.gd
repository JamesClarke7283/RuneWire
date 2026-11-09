class_name DialogueMenu
extends MenuPanel
## NPC conversation (quests, turn-ins, shop) and the bounty board.

var npc: Npc = null
var board: bool = false
var ui: GameUI
var _text: RichTextLabel
var _options: VBoxContainer
var _type_t: float = 0.0
var _side: VBoxContainer


func _init() -> void:
	panel_size = Vector2(1080, 640)


func build() -> void:
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 20)
	hb.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(hb)
	_side = VBoxContainer.new()
	_side.custom_minimum_size = Vector2(220, 0)
	hb.add_child(_side)
	var portrait: Texture2D = null
	if npc:
		portrait = MaterialLib.texture("res://assets/icons/items/%s.png" % npc.model_name)
	else:
		portrait = UIStyle.tex("ui_quest_marker")
	_side.add_child(MenuPanel.icon_rect(portrait, 210))
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_theme_constant_override("separation", 12)
	hb.add_child(right)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(0, 250)
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	right.add_child(sc)
	_text = MenuPanel.rich("", 20)
	_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(_text)
	_options = VBoxContainer.new()
	_options.add_theme_constant_override("separation", 8)
	right.add_child(_options)
	_show_main()


func _process(delta: float) -> void:
	if _text and _text.visible_ratio < 1.0:
		_type_t += delta
		_text.visible_ratio = minf(1.0, _type_t * 90.0 / maxf(1.0, float(_text.get_total_character_count())))


func _say(t: String) -> void:
	_text.text = t
	_text.visible_ratio = 0.0
	_type_t = 0.0


func _npc_id() -> String:
	return "board" if board else npc.npc_id


func _clear_options() -> void:
	for c in _options.get_children():
		c.queue_free()


func _opt(text: String, cb: Callable) -> void:
	var b := MenuPanel.button(text, cb)
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	_options.add_child(b)


func _show_main() -> void:
	var id := _npc_id()
	set_title(QuestDB.NPC_NAMES.get(id, "Bounty Board"))
	_clear_options()
	if board:
		_say("[b]EMBERWICK BOUNTY BOARD[/b]\nPaid in gold by the Town Guard. Bounties can be taken again once claimed.")
	else:
		var lines: Array = QuestDB.NPC_GREETINGS.get(id, ["Hello."])
		_say("[i]\"%s\"[/i]" % lines[randi() % lines.size()])
	for q in Quests.ready_for(id):
		_opt("★  Turn in: %s" % Quests.def(q)["title"], func(): _show_turn_in(q))
	for q in Quests.offered_by(id):
		var d := Quests.def(q)
		var prefix := "!  " if not d.get("repeatable", false) else "◆  "
		_opt(prefix + d["title"] + ("  (%d gold)" % int(d["rewards"].get("gold", 0))), func(): _show_offer(q))
	for q in Quests.active_for(id):
		_opt("…  %s (in progress)" % Quests.def(q)["title"], func(): _show_progress(q))
	if not board and Catalog.VENDORS.has(id):
		_opt("🛒  Browse %s" % Catalog.VENDORS[id]["title"], func():
			var u := ui
			closed.emit()
			u.open_shop.call_deferred(id))
	_opt("Goodbye", func(): closed.emit())


func _rewards_text(d: Dictionary) -> String:
	var r: Dictionary = d.get("rewards", {})
	var parts := []
	if r.has("gold"):
		parts.append("[color=#8a5a10][b]%d gold[/b][/color]" % int(r["gold"]))
	if r.has("xp"):
		parts.append("%d XP" % int(r["xp"]))
	for p in r.get("parts", {}):
		parts.append("%d× %s" % [int(r["parts"][p]), Catalog.display_name(p)])
	for i in r.get("items", {}):
		parts.append("%d× %s" % [int(r["items"][i]), Catalog.display_name(i)])
	for p in r.get("unlock_parts", []):
		parts.append("[color=#6a3fc0]Blueprint: %s[/color]" % Catalog.display_name(p))
	return ", ".join(parts)


func _objectives_text(q: String) -> String:
	var d := Quests.def(q)
	var s := ""
	for i in d["objectives"].size():
		var o: Dictionary = d["objectives"][i]
		var done := Quests.is_active(q) and Quests.objective_done(q, i)
		var txt: String = Quests.objective_text(q, i) if Quests.is_active(q) else o["text"]
		s += ("  ✔ " if done else "  • ") + txt + "\n"
	return s


func _show_offer(q: String) -> void:
	var d := Quests.def(q)
	set_title(d["title"])
	_say("%s\n\n[b]Objectives[/b]\n%s\n[b]Rewards:[/b] %s" % [d.get("offer", ""), _objectives_text(q), _rewards_text(d)])
	_clear_options()
	_opt("✔  Accept", func():
		Quests.accept(q)
		AudioManager.play_ui("quest_accept")
		_show_main())
	_opt("Not right now", _show_main)


func _show_progress(q: String) -> void:
	var d := Quests.def(q)
	set_title(d["title"])
	_say("%s\n\n[b]Progress[/b]\n%s" % [d.get("progress", "Keep at it!"), _objectives_text(q)])
	_clear_options()
	_opt("Got it", _show_main)


func _show_turn_in(q: String) -> void:
	var d := Quests.def(q)
	set_title(d["title"])
	_say("%s\n\n[b]Rewards:[/b] %s" % [d.get("complete", "Well done!"), _rewards_text(d)])
	_clear_options()
	_opt("★  Claim reward", func():
		Quests.turn_in(q)
		VFX.sparkle(get_tree().get_first_node_in_group("player"), (get_tree().get_first_node_in_group("player") as Node3D).global_position + Vector3.UP, Color(1, 0.85, 0.3), 24, 0.4)
		_show_main())
