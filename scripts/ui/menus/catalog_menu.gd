class_name CatalogMenu
extends MenuPanel
## Build Catalog [Q]: buy parts with gold and spawn them in front of you.

var ui: GameUI
var category: String = "structure"
var shop_mode: bool = false
var _grid: GridContainer
var _info: Label


func _init() -> void:
	panel_size = Vector2(1240, 760)
	title_text = "Build Catalog"


func build() -> void:
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 10)
	content.add_child(top)
	for cat in Catalog.PART_CATEGORIES:
		var b := MenuPanel.button(Catalog.CATEGORY_NAMES[cat], func(): category = cat; _fill(), 150)
		b.toggle_mode = true
		b.button_pressed = cat == category
		b.set_meta("cat", cat)
		top.add_child(b)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(spacer)
	_info = UIStyle.label("", 19, UIStyle.INK, "ui")
	top.add_child(_info)
	var sub := UIStyle.label("Courier runes deliver anywhere. Click Spawn to place a part where you're looking; Z undoes.", 17, Color("5a4632"), "body")
	content.add_child(sub)
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	content.add_child(sc)
	_grid = GridContainer.new()
	_grid.columns = 4
	_grid.add_theme_constant_override("h_separation", 14)
	_grid.add_theme_constant_override("v_separation", 14)
	_grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(_grid)
	Game.gold_changed.connect(func(_g, _d): _fill())
	Game.inventory_changed.connect(_fill)
	_fill()


func _fill() -> void:
	if not is_instance_valid(_grid):
		return
	for c in _grid.get_children():
		c.queue_free()
	for b in (content.get_child(0) as HBoxContainer).get_children():
		if b is Button and b.has_meta("cat"):
			(b as Button).set_pressed_no_signal(b.get_meta("cat") == category)
	var bm := get_tree().get_first_node_in_group("build_manager") as BuildManager
	_info.text = "Gold: %d   ·   Parts placed: %d / %d" % [Game.gold, bm.placed_count if bm else 0, Game.part_limit()]
	for id in Catalog.PARTS:
		var p: Dictionary = Catalog.PARTS[id]
		if p["category"] != category:
			continue
		var owned := Game.part_count(id)
		var price := int(p["price"])
		var locked := ""
		if not Game.is_part_unlocked(id):
			locked = "Blueprint from quest: " + Quests.def(p["unlock"]).get("title", "?")
		var buttons := []
		if not shop_mode:
			buttons.append(MenuPanel.button("Spawn", func(): _spawn(id), 0, owned <= 0))
		buttons.append(MenuPanel.button("Buy", func(): _buy(id, 1), 0, not Game.can_afford(price)))
		buttons.append(MenuPanel.button("×5", func(): _buy(id, 5), 0, not Game.can_afford(price * 5)))
		var card := MenuPanel.card(Catalog.part_icon(id), p["name"], p["desc"], price, "Owned: %d" % owned, buttons, locked)
		_grid.add_child(card)


func _buy(id: String, n: int) -> void:
	if Game.buy_part(id, n):
		AudioManager.play_ui("ui_buy")
	else:
		AudioManager.play_ui("ui_error")


func _spawn(id: String) -> void:
	var player := get_tree().get_first_node_in_group("player") as Player
	var bm := get_tree().get_first_node_in_group("build_manager") as BuildManager
	if player == null or bm == null:
		return
	closed.emit()
	bm.spawn_for_player(id, player)
