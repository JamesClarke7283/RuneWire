class_name ShopMenu
extends MenuPanel
## Vendor shop: parts, spells, weapons, today's featured (rolled) weapons, pouches, crafting materials,
## schematics, upgrades, consumables and a Sell tab, depending on the vendor.

var vendor: String = "odda"
var tab: int = 0
var _tabs: Array = []
var _grid: GridContainer
var _gold: Label
var _tab_row: HBoxContainer


func _init() -> void:
	panel_size = Vector2(1300, 800)


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
		if t.begins_with("featured"):
			nm = "★ Today's wares"
		var b := MenuPanel.button(nm, func(): tab = i; _fill(), 128)
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
	Game.gold_changed.connect(_on_gold)
	_fill()


func _on_gold(_g: int, _d: int) -> void:
	_fill.call_deferred()


func _fill() -> void:
	if not is_instance_valid(_grid):
		return
	for c in _grid.get_children():
		c.queue_free()
	_gold.text = "Gold: %d  ·  Pack %d/%d" % [Game.gold, Game.pack_used(), Game.pack_capacity()]
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
			for id in Catalog.WEAPONS:
				var e: Dictionary = Catalog.WEAPONS[id]
				if (Catalog.weapon_school(id) == "magic") != (kind == "spells") or not bool(e.get("sold", false)):
					continue
				var price2 := int(e["price"])
				var n_owned := Game.weapon_count(id)
				var bt2 := [MenuPanel.button("Buy", func(): _buy_equipment(id), 140, not Game.can_afford(price2) or not Game.has_weapon_room())]
				var extra := _stat_line(e) + ("  ·  owned ×%d" % n_owned if n_owned > 0 else "")
				_grid.add_child(MenuPanel.card(Catalog.equipment_icon(id), e["name"], e["desc"], price2, extra, bt2))
		"featured":
			var stock := Game.featured_stock(vendor, only[0] if not only.is_empty() else "gun")
			if stock.is_empty():
				_grid.add_child(UIStyle.label("Sold out! New wares arrive tomorrow.", 20, UIStyle.INK, "ui"))
			for i in stock.size():
				var w: Dictionary = stock[i]
				var price5 := Game.featured_price(w)
				var bt5 := [MenuPanel.button("Buy", func(): _buy_featured(i), 140, not Game.can_afford(price5) or not Game.has_weapon_room())]
				var perks := []
				for pk in w.get("perks", []):
					perks.append(Catalog.PERKS[pk]["name"])
				var desc5: String = "%s %s. %s" % [Catalog.RARITY_NAMES[int(w["rarity"])], Catalog.display_name(str(w["base"])), ", ".join(perks)]
				var card5 := MenuPanel.card(Catalog.weapon_icon(w), Catalog.weapon_name(w), desc5, price5,
					"%s · %d DPS" % [Catalog.RARITY_NAMES[int(w["rarity"])], int(Catalog.weapon_dps(Catalog.weapon_stats(w)))], bt5)
				_tint_card(card5, int(w["rarity"]))
				_grid.add_child(card5)
		"sell":
			_fill_sell()
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
		"pouches", "materials":
			for id in only:
				var price6 := Catalog.buy_price(id)
				var owned := Game.item_count(id)
				var bt6 := [MenuPanel.button("Buy", func(): _buy_item(id, 1), 0, not Game.can_afford(price6) or Game.room_for(id, 1) < 1)]
				if kind == "materials":
					bt6.append(MenuPanel.button("×5", func(): _buy_item(id, 5), 0, not Game.can_afford(price6 * 5) or Game.room_for(id, 5) < 5))
				var desc6 := str(Catalog.stack_def(id).get("desc", ""))
				var extra6 := "Owned: %d" % owned
				if kind == "pouches":
					var pd := Catalog.pouch_def(id)
					desc6 = "+%d pack slots when worn. %s" % [int(pd["slots"]), desc6]
					extra6 = "+%d slots · owned %d" % [int(pd["slots"]), owned]
				var card6 := MenuPanel.card(Catalog.stack_icon(id), Catalog.display_name(id), desc6, price6, extra6, bt6)
				if kind == "pouches":
					_tint_card(card6, int(Catalog.pouch_def(id).get("rarity", 0)))
				_grid.add_child(card6)
		"schematics":
			for rid in only:
				var sid := Catalog.schematic_id(rid)
				var price7 := Catalog.buy_price(sid)
				var known := Game.knows_recipe(rid)
				var r: Dictionary = Catalog.recipe(rid)
				var bt7 := [] if known else [MenuPanel.button("Learn", func(): _buy_item(sid, 1), 140, not Game.can_afford(price7))]
				var desc7 := "Teaches you to craft %s at the %s (Artisan rank %d)." % [Catalog.recipe_name(rid), Catalog.STATIONS[r["station"]]["name"], int(r.get("rank", 1))]
				_grid.add_child(MenuPanel.card(Catalog.recipe_icon(rid), "Schematic: " + Catalog.recipe_name(rid), desc7,
					-1 if known else price7, "Already known" if known else "Recipe", bt7))
		"consumables":
			for id in Catalog.CONSUMABLES:
				if not only.is_empty() and not (id in only):
					continue
				var c: Dictionary = Catalog.CONSUMABLES[id]
				var price4 := int(c["price"])
				var bt4 := [MenuPanel.button("Buy", func(): _buy_cons(id, 1), 0, not Game.can_afford(price4)),
					MenuPanel.button("×5", func(): _buy_cons(id, 5), 0, not Game.can_afford(price4 * 5))]
				_grid.add_child(MenuPanel.card(Catalog.item_icon(c["model"]), c["name"], c["desc"], price4, "Owned: %d" % Game.item_count(id), bt4))
		_:
			pass


func _tint_card(card: PanelContainer, rarity: int) -> void:
	var sb := card.get_theme_stylebox("panel").duplicate() as StyleBoxFlat
	if sb:
		sb.border_color = Catalog.rarity_color(rarity)
		sb.set_border_width_all(3)
		card.add_theme_stylebox_override("panel", sb)


func _fill_sell() -> void:
	var any := false
	for w in Game.weapons:
		var uid := int(w["uid"])
		if Game.equipped_slot(uid) >= 0 or bool(w.get("fav", false)):
			continue
		any = true
		var v := Catalog.weapon_value(w)
		var card := MenuPanel.card(Catalog.weapon_icon(w), Catalog.weapon_name(w), Catalog.weapon_base(str(w["base"])).get("desc", ""), -1,
			"Sells for %d" % v, [MenuPanel.button("Sell", func(): _sell_weapon(uid), 140)])
		_tint_card(card, int(w["rarity"]))
		_grid.add_child(card)
	for id in Catalog.CONSUMABLES.keys() + Catalog.ITEMS.keys() + Catalog.POUCHES.keys():
		var n := Game.item_count(id)
		if n <= 0 or Catalog.is_key_item(id) and id != "ley_key":
			continue
		any = true
		var v2 := Catalog.stack_value(id)
		var bts := [MenuPanel.button("Sell 1", func(): _sell_item(id, 1))]
		if n > 1:
			bts.append(MenuPanel.button("All ×%d" % n, func(): _sell_item(id, Game.item_count(id))))
		_grid.add_child(MenuPanel.card(Catalog.stack_icon(id), "%s ×%d" % [Catalog.display_name(id), n], Catalog.stack_def(id).get("desc", ""),
			-1, "%d gold each" % v2, bts))
	if not any:
		_grid.add_child(UIStyle.label("Nothing to sell. Equipped and ★ favourite weapons are kept safe.", 20, UIStyle.INK, "ui"))


func _sell_weapon(uid: int) -> void:
	AudioManager.play_ui("ui_sell" if Game.sell_weapon(uid) else "ui_error")
	_fill()


func _sell_item(id: String, n: int) -> void:
	AudioManager.play_ui("ui_sell" if Game.sell_item(id, n) else "ui_error")
	_fill()


func _buy_featured(i: int) -> void:
	AudioManager.play_ui("ui_buy" if Game.buy_featured(vendor, i) else "ui_error")
	_fill()


func _stat_line(e: Dictionary) -> String:
	if e.has("mana") and float(e.get("damage", 0.0)) <= 0.0:
		return "%d mana" % int(e["mana"])
	if e.has("damage"):
		var dmg := "%d" % int(e["damage"]) if not e.has("pellets") else "%d×%d" % [int(e["damage"]), int(e["pellets"])]
		return "%s %s dmg" % [dmg, e.get("damage_type", "")]
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


func _buy_item(id: String, n: int) -> void:
	AudioManager.play_ui("ui_buy" if Game.buy_item(id, n) else "ui_error")
	_fill()


func _buy_cons(id: String, n: int) -> void:
	AudioManager.play_ui("ui_buy" if Game.buy_consumable(id, n) else "ui_error")
	_fill()
