class_name ShopMenu
extends MenuPanel
## Vendor shop: parts, spells, weapons, upgrades and consumables depending on the vendor.

var vendor: String = "odda"
var tab: int = 0
var _tabs: Array = []
var _grid: GridContainer
var _gold: Label
var _tab_row: HBoxContainer


func _init() -> void:
	panel_size = Vector2(1240, 760)


func build() -> void:
	var v: Dictionary = Catalog.VENDORS.get(vendor, {"title": "Shop", "tabs": []})
	set_title(v["title"])
	_tabs = v["tabs"]
	_tab_row = HBoxContainer.new()
	_tab_row.add_theme_constant_override("separation", 10)
	content.add_child(_tab_row)
	for i in _tabs.size():
		var t: String = _tabs[i]
		var nm := t.split(":")[0].capitalize()
		var b := MenuPanel.button(nm, func(): tab = i; _fill(), 150)
		b.toggle_mode = true
		_tab_row.add_child(b)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_tab_row.add_child(spacer)
	_gold = UIStyle.label("", 22, Color("8a5a10"), "display")
	_tab_row.add_child(_gold)
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	content.add_child(sc)
	_grid = GridContainer.new()
	_grid.columns = 4
	_grid.add_theme_constant_override("h_separation", 14)
	_grid.add_theme_constant_override("v_separation", 14)
	sc.add_child(_grid)
	Game.gold_changed.connect(func(_g, _d): _fill())
	_fill()


func _fill() -> void:
	if not is_instance_valid(_grid):
		return
	for c in _grid.get_children():
		c.queue_free()
	_gold.text = "Gold: %d" % Game.gold
	for i in _tab_row.get_child_count():
		var b := _tab_row.get_child(i)
		if b is Button:
			(b as Button).set_pressed_no_signal(i == tab)
	if _tabs.is_empty():
		return
	var spec: String = _tabs[tab]
	var kind := spec.split(":")[0]
	var only: Array = []
	if spec.contains(":"):
		only = Array(spec.split(":")[1].split(","))
	match kind:
		"parts":
			for id in Catalog.PARTS:
				var p: Dictionary = Catalog.PARTS[id]
				var locked: String = "" if Game.is_part_unlocked(id) else "Blueprint from quest: " + str(Quests.def(p["unlock"]).get("title", "?"))
				var price := int(p["price"])
				var bt := [MenuPanel.button("Buy", func(): _buy_part(id, 1), 0, not Game.can_afford(price)),
					MenuPanel.button("×5", func(): _buy_part(id, 5), 0, not Game.can_afford(price * 5))]
				_grid.add_child(MenuPanel.card(Catalog.part_icon(id), p["name"], p["desc"], price, "Owned: %d" % Game.part_count(id), bt, locked))
		"spells", "weapons":
			var want := "spell" if kind == "spells" else "weapon"
			for id in Catalog.EQUIPMENT:
				var e: Dictionary = Catalog.EQUIPMENT[id]
				if e["kind"] != want:
					continue
				var owned := Game.has_equipment(id)
				var price2 := int(e["price"])
				var bt2 := [] if owned else [MenuPanel.button("Buy", func(): _buy_equipment(id), 140, not Game.can_afford(price2))]
				_grid.add_child(MenuPanel.card(Catalog.equipment_icon(id), e["name"], e["desc"], -1 if owned else price2, "Owned ✔" if owned else _stat_line(e), bt2))
		"upgrades":
			for id in Catalog.UPGRADES:
				if not only.is_empty() and not (id in only):
					continue
				var u: Dictionary = Catalog.UPGRADES[id]
				var tier := Game.upgrade_tier(id)
				var price3 := Game.upgrade_price(id)
				var maxed := price3 < 0
				var bt3 := [] if maxed else [MenuPanel.button("Upgrade", func(): _buy_upgrade(id), 140, not Game.can_afford(price3))]
				_grid.add_child(MenuPanel.card(Catalog.upgrade_icon(id), "%s (%d/%d)" % [u["name"], tier, u["prices"].size()], u["desc"], -1 if maxed else price3, "MAX" if maxed else u["desc"], bt3))
		"consumables":
			for id in Catalog.CONSUMABLES:
				if not only.is_empty() and not (id in only):
					continue
				var c: Dictionary = Catalog.CONSUMABLES[id]
				var price4 := int(c["price"])
				var bt4 := [MenuPanel.button("Buy", func(): _buy_cons(id, 1), 0, not Game.can_afford(price4)),
					MenuPanel.button("×5", func(): _buy_cons(id, 5), 0, not Game.can_afford(price4 * 5))]
				_grid.add_child(MenuPanel.card(Catalog.item_icon(c["model"]), c["name"], c["desc"], price4, "Owned: %d" % Game.item_count(id), bt4))


func _stat_line(e: Dictionary) -> String:
	if e.has("mana"):
		return "%d mana" % int(e["mana"])
	if e.has("damage"):
		return "%d %s dmg" % [int(e["damage"]), e.get("damage_type", "")]
	return ""


func _buy_part(id: String, n: int) -> void:
	AudioManager.play_ui("ui_buy" if Game.buy_part(id, n) else "ui_error")
	_fill()


func _buy_equipment(id: String) -> void:
	AudioManager.play_ui("ui_buy" if Game.buy_equipment(id) else "ui_error")
	_fill()


func _buy_upgrade(id: String) -> void:
	AudioManager.play_ui("ui_buy" if Game.buy_upgrade(id) else "ui_error")
	_fill()


func _buy_cons(id: String, n: int) -> void:
	AudioManager.play_ui("ui_buy" if Game.buy_consumable(id, n) else "ui_error")
	_fill()
