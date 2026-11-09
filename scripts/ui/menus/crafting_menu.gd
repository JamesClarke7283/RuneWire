class_name CraftingMenu
extends MenuPanel
## Crafting at a station - or anywhere with the Crafting Book [B], which lists every recipe but only
## makes the simple "anywhere" ones. Browse recipes by category, see what you have and where to find
## what you lack, craft one or many, and Track a recipe so the objective tracker guides you to its
## materials. Stations add tabs: Upgrade (Workbench, Forge, Altar), Salvage (Workbench) and Enchant
## (Altar: reroll perks or infuse a weapon to a higher rarity).

const TAB_NAMES := {"craft": "Craft", "upgrade": "Upgrade weapons", "salvage": "Salvage", "enchant": "Enchant"}
const BLOCK_TEXT := {
	"schematic": "Needs its schematic: find one in chests, vaults or on Champions, or buy it",
	"rank": "Needs Artisan rank %d (you are rank %d)",
	"materials": "Missing materials",
	"gold": "Not enough gold",
	"room": "No room in your pack",
	"station": "Craft it at the %s in Emberwick",
}

var ui: GameUI
var station: String = "workbench"     # "field" = the Crafting Book
var tab: String = "craft"
var _tab_row: HBoxContainer
var _body: VBoxContainer
var _gold: Label
var _rank_label: Label
var _rank_bar: ProgressBar
var _selected_uid: int = 0
var _recipe: String = ""
var _cat: String = "All"
var _only_ready: bool = false
var _list_scroll: float = 0.0
var _dirty: bool = false


func _init() -> void:
	panel_size = Vector2(1340, 840)


func is_book() -> bool:
	return station == "field"


func build() -> void:
	var d: Dictionary = Catalog.STATIONS.get(station, Catalog.STATIONS["field"])
	set_title(str(d["name"]))
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 8)
	content.add_child(top)
	_tab_row = HBoxContainer.new()
	_tab_row.add_theme_constant_override("separation", 8)
	top.add_child(_tab_row)
	for t in d.get("tabs", ["craft"]):
		var b := MenuPanel.button(TAB_NAMES.get(t, t), func(): _set_tab(t), 170)
		b.toggle_mode = true
		b.name = "Tab_" + t
		_tab_row.add_child(b)
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(sp)
	var rk := VBoxContainer.new()
	rk.add_theme_constant_override("separation", 2)
	top.add_child(rk)
	_rank_label = UIStyle.label("", 17, Color("5a3f8a"), "ui")
	rk.add_child(_rank_label)
	_rank_bar = ProgressBar.new()
	_rank_bar.custom_minimum_size = Vector2(250, 10)
	_rank_bar.show_percentage = false
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.2, 0.15, 0.1, 0.35)
	bg.set_corner_radius_all(5)
	var fg := StyleBoxFlat.new()
	fg.bg_color = Color("8a6cff")
	fg.set_corner_radius_all(5)
	_rank_bar.add_theme_stylebox_override("background", bg)
	_rank_bar.add_theme_stylebox_override("fill", fg)
	rk.add_child(_rank_bar)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(18, 0)
	top.add_child(gap)
	_gold = UIStyle.label("", 22, Color("8a5a10"), "display")
	top.add_child(_gold)
	_body = VBoxContainer.new()
	_body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(_body)
	Game.inventory_changed.connect(_mark_dirty)
	Game.gold_changed.connect(_on_gold)
	Game.artisan_changed.connect(func(_x, _r): _mark_dirty())
	Game.schematic_learned.connect(func(_r): _mark_dirty())
	if not Game.loadout_weapon(0).is_empty():
		_selected_uid = int(Game.loadout_weapon(0)["uid"])
	if Game.tracked_recipe != "" and _station_has(Game.tracked_recipe):
		_recipe = Game.tracked_recipe
	Events.station_opened.emit(station)
	_refresh()


func _set_tab(t: String) -> void:
	tab = t
	_refresh()


func _mark_dirty() -> void:
	if not _dirty:
		_dirty = true
		_refresh.call_deferred()


func _on_gold(_g: int, _d: int) -> void:
	_mark_dirty()


func _station_has(rid: String) -> bool:
	return is_book() or Catalog.recipe(rid).get("station", "") == station


func _refresh() -> void:
	_dirty = false
	if not is_instance_valid(_body):
		return
	for b in _tab_row.get_children():
		if b is Button:
			(b as Button).set_pressed_no_signal(String(b.name) == "Tab_" + tab)
	_gold.text = "Gold: %d" % Game.gold
	var rank := Game.artisan_rank()
	var prog := Game.artisan_progress()
	_rank_label.text = "Artisan rank %d · %s" % [rank, Catalog.artisan_title(rank)]
	_rank_bar.max_value = float(prog.y)
	_rank_bar.value = float(prog.x)
	_rank_bar.tooltip_text = "%d / %d crafting experience to the next rank" % [prog.x, prog.y] if rank < Catalog.ARTISAN_XP.size() else "Maximum rank!"
	# keep the recipe list's scroll position across refreshes
	var old := _body.find_child("RecipeScroll", true, false) as ScrollContainer
	if old:
		_list_scroll = old.scroll_vertical
	for c in _body.get_children():
		c.queue_free()
	match tab:
		"craft":
			_craft_tab()
		"upgrade":
			_upgrade_tab()
		"salvage":
			_salvage_tab()
		"enchant":
			_enchant_tab()


# ------------------------------------------------------------------ helpers
func _cost_row(cost: Dictionary, gold: int) -> HFlowContainer:
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 10)
	for id in cost:
		var have := Game.item_count(id)
		var need := int(cost[id])
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 2)
		h.add_child(MenuPanel.icon_rect(Catalog.stack_icon(id), 26))
		h.add_child(UIStyle.label("%d/%d" % [have, need], 16, Color("2e7d32") if have >= need else Color("b03a2e"), "ui"))
		h.tooltip_text = Catalog.display_name(id)
		row.add_child(h)
	if gold > 0:
		row.add_child(MenuPanel.coin_price(gold, Game.can_afford(gold)))
	return row


func _scroll(name_hint: String = "") -> VBoxContainer:
	var sc := ScrollContainer.new()
	if name_hint != "":
		sc.name = name_hint
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_body.add_child(sc)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_theme_constant_override("separation", 8)
	sc.add_child(v)
	return v


func _card() -> PanelContainer:
	var pc := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(1, 1, 1, 0.35)
	sb.border_color = Color(UIStyle.BRASS_DARK, 0.5)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(10)
	sb.set_content_margin_all(12)
	pc.add_theme_stylebox_override("panel", sb)
	return pc


func _block_text(rid: String, block: String) -> String:
	var r := Catalog.recipe(rid)
	match block:
		"rank":
			return BLOCK_TEXT["rank"] % [int(r.get("rank", 1)), Game.artisan_rank()]
		"station":
			return BLOCK_TEXT["station"] % Catalog.STATIONS[r["station"]]["name"]
	return BLOCK_TEXT.get(block, "")


func _station_for_check() -> String:
	return "field" if is_book() else station


## A flat parchment list row (instead of the round theme button) with a coloured left edge; the
## selected row gets a teal frame. Keeps the text readable in every state.
static func list_row_style(b: Button, text_col: Color, edge: Color) -> void:
	for st in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color("fbf3df") if st in ["normal", "disabled", "focus"] else (Color("fff9ea") if st == "hover" else Color("e3f4ee"))
		if st == "focus":
			sb.draw_center = false
		sb.border_color = edge if not st in ["pressed", "hover_pressed"] else UIStyle.TEAL
		sb.border_width_left = 6
		sb.border_width_top = 1 if not st in ["pressed", "hover_pressed"] else 3
		sb.border_width_bottom = sb.border_width_top
		sb.border_width_right = sb.border_width_top
		sb.set_corner_radius_all(8)
		sb.content_margin_left = 8
		sb.content_margin_right = 8
		b.add_theme_stylebox_override(st, sb)
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color", "font_focus_color"]:
		b.add_theme_color_override(c, text_col)
	b.add_theme_constant_override("outline_size", 0)


# ------------------------------------------------------------------ craft
func _recipes() -> Array:
	var out := []
	for rid in Catalog.RECIPES:
		var r: Dictionary = Catalog.RECIPES[rid]
		if not is_book() and r["station"] != station:
			continue
		if is_book() and _cat != "All" and _cat != r["station"] and not (_cat == "field" and bool(r.get("field", false))):
			continue
		if not is_book() and _cat != "All" and r.get("cat", "") != _cat:
			continue
		if _only_ready and not Game.can_craft(rid, _station_for_check()):
			continue
		out.append(rid)
	# ready first, then unlocked, then locked; stable by rank
	out.sort_custom(func(a, b):
		var ka := _sort_key(a)
		var kb := _sort_key(b)
		return ka < kb)
	return out


func _sort_key(rid: String) -> String:
	var block := Game.craft_block(rid, _station_for_check())
	var group := 0 if block == "" else (1 if block in ["materials", "gold", "room", "station"] else 2)
	var r := Catalog.recipe(rid)
	return "%d_%02d_%s" % [group, int(r.get("rank", 1)), Catalog.recipe_name(rid)]


func _categories() -> Array:
	if is_book():
		return ["All", "field"] + Catalog.STATION_ORDER
	var cats := ["All"]
	for rid in Catalog.recipes_for(station):
		var c: String = Catalog.recipe(rid).get("cat", "")
		if c != "" and not c in cats:
			cats.append(c)
	return cats


func _craft_tab() -> void:
	var hb := HBoxContainer.new()
	hb.size_flags_vertical = Control.SIZE_EXPAND_FILL
	hb.add_theme_constant_override("separation", 16)
	_body.add_child(hb)
	var left := VBoxContainer.new()
	left.custom_minimum_size = Vector2(540, 0)
	left.add_theme_constant_override("separation", 8)
	hb.add_child(left)
	var filters := HFlowContainer.new()
	filters.add_theme_constant_override("h_separation", 6)
	filters.add_theme_constant_override("v_separation", 6)
	left.add_child(filters)
	for c in _categories():
		var label: String = c
		if is_book() and c != "All":
			label = "Anywhere" if c == "field" else str(Catalog.STATIONS[c]["short"])
		var b := MenuPanel.button(label, func(): _cat = c; _refresh(), 0)
		b.toggle_mode = true
		b.set_pressed_no_signal(_cat == c)
		b.name = "Cat_" + c
		filters.add_child(b)
	var ready_btn := MenuPanel.button("Ready to craft", func(): _only_ready = not _only_ready; _refresh(), 0)
	ready_btn.toggle_mode = true
	ready_btn.set_pressed_no_signal(_only_ready)
	ready_btn.name = "ReadyOnly"
	filters.add_child(ready_btn)
	var sc := ScrollContainer.new()
	sc.name = "RecipeScroll"
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	left.add_child(sc)
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 5)
	sc.add_child(list)
	var recipes := _recipes()
	if _recipe == "" or not _recipe in recipes:
		_recipe = recipes[0] if not recipes.is_empty() else ""
	for rid in recipes:
		list.add_child(_recipe_row(rid))
	if recipes.is_empty():
		list.add_child(UIStyle.label("Nothing here yet: gather materials, raise your Artisan rank or find schematics.", 16, Color("6a5a48"), "body"))
	sc.set_deferred("scroll_vertical", int(_list_scroll))
	var right := _card()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hb.add_child(right)
	var rsc := ScrollContainer.new()
	rsc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	right.add_child(rsc)
	var rv := VBoxContainer.new()
	rv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rv.add_theme_constant_override("separation", 8)
	rsc.add_child(rv)
	if _recipe != "":
		_recipe_details(rv, _recipe)


func _recipe_row(rid: String) -> Control:
	var b := Button.new()
	b.name = "Recipe_" + rid
	b.toggle_mode = true
	b.button_pressed = rid == _recipe
	b.custom_minimum_size = Vector2(510, 58)
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.icon = Catalog.recipe_icon(rid)
	b.expand_icon = true
	b.add_theme_constant_override("icon_max_width", 46)
	var o := Catalog.recipe_output(rid)
	var block := Game.craft_block(rid, _station_for_check())
	var status := "  ✔" if block == "" else ""
	match block:
		"schematic":
			status = "   · needs schematic"
		"rank":
			status = "   · Artisan rank %d" % int(Catalog.recipe(rid).get("rank", 1))
		"station":
			status = "   · %s" % Catalog.STATIONS[Catalog.recipe(rid)["station"]]["short"]
	var count := " ×%d" % int(o["count"]) if int(o.get("count", 1)) > 1 else ""
	var star := "★ " if Game.tracked_recipe == rid else ""
	b.text = "  %s%s%s%s" % [star, Catalog.recipe_name(rid), count, status]
	var col := UIStyle.INK
	if block == "":
		col = Color("1d5e27")
	elif block in ["schematic", "rank"]:
		col = Color("7a6a58")
	list_row_style(b, col, Color("3aa76d") if block == "" else (Color("b8a888") if block in ["schematic", "rank"] else Color("c99a4e")))
	b.pressed.connect(func():
		AudioManager.play_ui("ui_click", -8.0)
		_recipe = rid
		_refresh())
	return b


func _recipe_details(rv: VBoxContainer, rid: String) -> void:
	var r := Catalog.recipe(rid)
	var o := Catalog.recipe_output(rid)
	var out_id := str(o["id"])
	var block := Game.craft_block(rid, _station_for_check())
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 12)
	rv.add_child(top)
	top.add_child(MenuPanel.icon_rect(Catalog.recipe_icon(rid), 112))
	var tv := VBoxContainer.new()
	tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(tv)
	var title := Catalog.recipe_name(rid) + (" ×%d" % int(o["count"]) if int(o["count"]) > 1 else "")
	var nl := UIStyle.label(title, 26, UIStyle.INK, "display")
	nl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tv.add_child(nl)
	var st: Dictionary = Catalog.STATIONS[r["station"]]
	var where := str(st["name"]) + (" (or anywhere)" if bool(r.get("field", false)) else "")
	tv.add_child(UIStyle.label("%s  ·  %s  ·  Artisan rank %d" % [r.get("cat", ""), where, int(r.get("rank", 1))], 16, Color("5a4632"), "ui"))
	var desc := ""
	if o["type"] == "weapon":
		var bd := Catalog.weapon_base(out_id)
		var sch := Catalog.weapon_school(out_id)
		tv.add_child(UIStyle.label("%s weapon (%s)  ·  rolls Uncommon or better" % [Catalog.SCHOOL_NAMES[sch], Catalog.KIND_NAMES.get(bd.get("kind", ""), "")],
			16, Color("3a6a8a"), "body"))
		desc = str(bd.get("desc", ""))
		var s := Catalog.weapon_stats(Catalog.make_weapon(out_id, 1, [], 1 + (Game.artisan_rank() - 1) / 3))
		desc += "\n[color=#6b3f0e]About %d damage per second · %s damage[/color]" % [int(round(Catalog.weapon_dps(s) * Game.school_mult(sch))), str(bd.get("damage_type", "")).capitalize()]
	elif Catalog.is_pouch(out_id):
		var pd := Catalog.pouch_def(out_id)
		desc = "[b]+%d pack slots[/b] when equipped in a pouch slot.%s\n%s" % [int(pd["slots"]),
			("\n[color=#2e5d8a]%s[/color]" % pd["perk_desc"]) if pd.has("perk_desc") else "", pd.get("desc", "")]
	else:
		desc = str(Catalog.stack_def(out_id).get("desc", ""))
	var dl := MenuPanel.rich(desc, 17)
	dl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rv.add_child(dl)
	# ingredients with what you have and where to find the rest
	rv.add_child(UIStyle.label("Ingredients", 21, Color("8a5a22"), "display"))
	var cost: Dictionary = r.get("cost", {})
	for id in cost:
		var have := Game.item_count(id)
		var need := int(cost[id])
		var line := HBoxContainer.new()
		line.add_theme_constant_override("separation", 8)
		line.add_child(MenuPanel.icon_rect(Catalog.stack_icon(id), 34))
		var ok := have >= need
		var txt := "[b]%s[/b]  [color=#%s]%d / %d[/color]" % [Catalog.display_name(id), "2e7d32" if ok else "b03a2e", have, need]
		if not ok:
			var src := str(Catalog.ITEMS.get(id, {}).get("src", ""))
			if src == "" and Catalog.RECIPES.has(id):
				src = "Craft it at the " + str(Catalog.STATIONS[Catalog.recipe(id)["station"]]["name"])
			if src != "":
				txt += "\n[color=#6a5a48][i]%s[/i][/color]" % src
		var rl := MenuPanel.rich(txt, 16)
		rl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		line.add_child(rl)
		rv.add_child(line)
	if int(r.get("gold", 0)) > 0:
		var gl := HBoxContainer.new()
		gl.add_child(UIStyle.label("Fee  ", 16, UIStyle.INK, "ui"))
		gl.add_child(MenuPanel.coin_price(int(r["gold"]), Game.can_afford(int(r["gold"]))))
		rv.add_child(gl)
	if block != "":
		var bl := UIStyle.label(("Locked: " if block in ["schematic", "rank"] else "") + _block_text(rid, block), 16, Color("9a3a2a"), "body")
		bl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		rv.add_child(bl)
	rv.add_child(UIStyle.label("+%d crafting experience" % Catalog.recipe_xp(rid), 14, Color("5a3f8a"), "body"))
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 8)
	row.add_theme_constant_override("v_separation", 8)
	rv.add_child(row)
	var can := block == ""
	row.add_child(MenuPanel.button("Craft", func(): _craft(rid, 1), 150, not can))
	if o["type"] == "item" and not Catalog.is_pouch(out_id):
		var mx := Game.craft_max(rid, _station_for_check()) if can else 0
		if mx >= 2:
			var n := mini(mx, 5)
			row.add_child(MenuPanel.button("Craft ×%d" % n, func(): _craft(rid, n), 130))
			if mx > 5:
				row.add_child(MenuPanel.button("Craft all (%d)" % mx, func(): _craft(rid, mx), 150))
	var tracked := Game.tracked_recipe == rid
	row.add_child(MenuPanel.button("★ Tracking" if tracked else "☆ Track on objective", func():
		Game.set_tracked_recipe("" if tracked else rid)
		AudioManager.play_ui("ui_click")
		if not tracked:
			Events.toast("Tracking %s: the objective tracker will guide you to its materials" % Catalog.recipe_name(rid), "info"), 0))


func _craft(rid: String, times: int) -> void:
	var made := 0
	var weapons := []
	var items := {}
	for i in times:
		var out := Game.craft(rid, _station_for_check())
		if out.is_empty():
			break
		made += 1
		if out.has("weapon"):
			weapons.append(out["weapon"])
		for id in out.get("items", {}):
			items[id] = int(items.get(id, 0)) + int(out["items"][id])
	if made == 0:
		AudioManager.play_ui("ui_error")
		return
	AudioManager.play_ui(str(Catalog.STATIONS.get(station, {}).get("sfx", "craft")), -2.0)
	var p := get_tree().get_first_node_in_group("player") as Node3D
	if p:
		VFX.sparkle(p, p.global_position + Vector3.UP * 1.2, Color(1, 0.85, 0.4), 12, 0.3)
	for id in items:
		Events.toast("Crafted %d × %s" % [int(items[id]), Catalog.display_name(id)], "item")
		if Catalog.is_pouch(id):
			Events.toast("Equip it in a pouch slot in your Inventory [I] for +%d pack slots" % int(Catalog.pouch_def(id)["slots"]), "info")


# ------------------------------------------------------------------ upgrade
func _weapon_list(filter: Callable = Callable()) -> Array:
	var out := []
	for w in Game.weapons:
		if filter.is_valid() and not bool(filter.call(w)):
			continue
		out.append(w)
	return out


func _upgrade_tab() -> void:
	var hb := HBoxContainer.new()
	hb.size_flags_vertical = Control.SIZE_EXPAND_FILL
	hb.add_theme_constant_override("separation", 16)
	_body.add_child(hb)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(470, 0)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	hb.add_child(sc)
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 6)
	sc.add_child(list)
	if Game.get_weapon(_selected_uid).is_empty() and not Game.weapons.is_empty():
		_selected_uid = int(Game.weapons[0]["uid"])
	for w in Game.weapons:
		list.add_child(_weapon_row(w, int(w["uid"]) == _selected_uid, func(): _selected_uid = int(w["uid"]); _refresh()))
	var right := _card()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hb.add_child(right)
	var rv := VBoxContainer.new()
	rv.add_theme_constant_override("separation", 8)
	right.add_child(rv)
	var w := Game.get_weapon(_selected_uid)
	if w.is_empty():
		rv.add_child(UIStyle.label("No weapons to upgrade.", 20, UIStyle.INK, "ui"))
		return
	_weapon_header(rv, w)
	var cost := Catalog.upgrade_cost(w)
	if cost.is_empty():
		rv.add_child(UIStyle.label("Fully upgraded! This one is as good as it gets.", 19, Color("2e7d32"), "ui"))
		return
	var now := Catalog.weapon_stats(w)
	var nxt_w := w.duplicate(true)
	nxt_w["level"] = int(w["level"]) + 1
	var nxt := Catalog.weapon_stats(nxt_w)
	var mult := Game.school_mult(str(now.get("school", "tech")))
	var lines := "[b]Next level: +%d[/b]\n" % (int(w["level"]))
	if float(now.get("damage", 0.0)) > 0.0:
		lines += "Damage  %d  →  [color=#2e7d32][b]%d[/b][/color]\n" % [int(round(float(now["damage"]) * mult)), int(round(float(nxt["damage"]) * mult))]
		lines += "Damage per second  %d  →  [color=#2e7d32][b]%d[/b][/color]\n" % [int(round(Catalog.weapon_dps(now) * mult)), int(round(Catalog.weapon_dps(nxt) * mult))]
	if now.has("heal"):
		lines += "Healing  %d  →  [color=#2e7d32][b]%d[/b][/color]\n" % [int(round(float(now["heal"]))), int(round(float(nxt["heal"])))]
	if now.has("repair"):
		lines += "Repair  %d  →  [color=#2e7d32][b]%d[/b][/color]\n" % [int(round(float(now["repair"]))), int(round(float(nxt["repair"])))]
	var rt := MenuPanel.rich(lines, 18)
	rt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rv.add_child(rt)
	rv.add_child(UIStyle.label("Cost", 20, Color("8a5a22"), "display"))
	rv.add_child(_cost_row(cost["items"], int(cost["gold"])))
	var block := Game.upgrade_block(int(w["uid"]))
	if block == "rank":
		rv.add_child(UIStyle.label("Locked: needs Artisan rank %d (you are rank %d)" % [int(cost["rank"]), Game.artisan_rank()], 16, Color("9a3a2a"), "body"))
	var uid := int(w["uid"])
	rv.add_child(MenuPanel.button("Upgrade to +%d" % int(w["level"]), func():
		if Game.upgrade_weapon(uid):
			AudioManager.play_ui("craft", -2.0)
			Events.toast("%s upgraded!" % Catalog.weapon_name(Game.get_weapon(uid)), "unlock")
		else:
			AudioManager.play_ui("ui_error"), 240, block != ""))


func _weapon_header(rv: VBoxContainer, w: Dictionary) -> void:
	var rc := Catalog.rarity_color(int(w["rarity"]))
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 12)
	top.add_child(MenuPanel.icon_rect(Catalog.weapon_icon(w), 110))
	var tv := VBoxContainer.new()
	var nl := UIStyle.label(Catalog.weapon_name(w), 24, rc if int(w["rarity"]) > 0 else UIStyle.INK, "display", 5, Color(0.15, 0.1, 0.08, 0.85))
	nl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	nl.custom_minimum_size.x = 440
	tv.add_child(nl)
	var sch := Catalog.weapon_school(str(w["base"]))
	tv.add_child(UIStyle.label("%s %s · Level %d / %d" % [Catalog.RARITY_NAMES[int(w["rarity"])], Catalog.SCHOOL_NAMES[sch], int(w["level"]), Catalog.MAX_WEAPON_LEVEL], 17, Color("5a4632"), "ui"))
	top.add_child(tv)
	rv.add_child(top)


func _weapon_row(w: Dictionary, sel: bool, cb: Callable) -> Control:
	var b := Button.new()
	b.toggle_mode = true
	b.button_pressed = sel
	b.custom_minimum_size = Vector2(440, 64)
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.icon = Catalog.weapon_icon(w)
	b.expand_icon = true
	b.add_theme_constant_override("icon_max_width", 54)
	var es := Game.equipped_slot(int(w["uid"]))
	b.text = "  %s%s" % [Catalog.weapon_name(w), ("   [slot %d]" % (es + 1)) if es >= 0 else ""]
	var rc := Catalog.rarity_color(int(w["rarity"]))
	list_row_style(b, rc.darkened(0.55) if int(w["rarity"]) > 0 else UIStyle.INK, rc)
	b.pressed.connect(func():
		AudioManager.play_ui("ui_click", -8.0)
		cb.call())
	return b


# ------------------------------------------------------------------ salvage
func _salvage_tab() -> void:
	var v := _scroll()
	v.add_child(UIStyle.label("Break weapons down into crafting materials. Equipped and ★ favourite weapons are protected.", 17, Color("5a4632"), "body"))
	var any_common := false
	for w in Game.weapons:
		var uid := int(w["uid"])
		var locked := Game.equipped_slot(uid) >= 0 or bool(w.get("fav", false))
		if int(w["rarity"]) == 0 and not locked:
			any_common = true
		var pc := _card()
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 12)
		pc.add_child(h)
		h.add_child(MenuPanel.icon_rect(Catalog.weapon_icon(w), 58))
		var col := VBoxContainer.new()
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(col)
		var rc := Catalog.rarity_color(int(w["rarity"]))
		col.add_child(UIStyle.label(Catalog.weapon_name(w), 19, rc.darkened(0.4) if int(w["rarity"]) > 0 else UIStyle.INK, "ui"))
		var yields := []
		var y := Catalog.salvage_yield(w)
		for id in y:
			yields.append("%d %s" % [int(y[id]), Catalog.display_name(id)])
		col.add_child(UIStyle.label("→ " + ", ".join(yields), 15, Color("5a4632"), "body"))
		var why := ""
		if Game.equipped_slot(uid) >= 0:
			why = "Equipped"
		elif bool(w.get("fav", false)):
			why = "★ Favourite"
		if why != "":
			h.add_child(UIStyle.label(why, 16, Color("6a5a48"), "ui"))
		else:
			h.add_child(MenuPanel.button("Salvage", func(): _salvage(uid), 130))
		v.add_child(pc)
	if any_common:
		v.add_child(MenuPanel.button("Salvage every unprotected Common weapon", func():
			for w2 in Game.weapons.duplicate():
				if int(w2["rarity"]) == 0 and Game.equipped_slot(int(w2["uid"])) < 0 and not bool(w2.get("fav", false)):
					Game.salvage_weapon(int(w2["uid"]))
			AudioManager.play_ui("scavenge"), 0))


func _salvage(uid: int) -> void:
	var got := Game.salvage_weapon(uid)
	if got.is_empty():
		AudioManager.play_ui("ui_error")
		return
	AudioManager.play_ui("scavenge", -2.0)
	var parts := []
	for id in got:
		parts.append("%d %s" % [int(got[id]), Catalog.display_name(id)])
	Events.toast("Salvaged: " + ", ".join(parts), "item")


# ------------------------------------------------------------------ enchant (altar)
func _enchant_tab() -> void:
	var hb := HBoxContainer.new()
	hb.size_flags_vertical = Control.SIZE_EXPAND_FILL
	hb.add_theme_constant_override("separation", 16)
	_body.add_child(hb)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(470, 0)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	hb.add_child(sc)
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 6)
	sc.add_child(list)
	if Game.get_weapon(_selected_uid).is_empty() and not Game.weapons.is_empty():
		_selected_uid = int(Game.weapons[0]["uid"])
	for w in Game.weapons:
		list.add_child(_weapon_row(w, int(w["uid"]) == _selected_uid, func(): _selected_uid = int(w["uid"]); _refresh()))
	var right := _card()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hb.add_child(right)
	var rsc := ScrollContainer.new()
	rsc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	right.add_child(rsc)
	var rv := VBoxContainer.new()
	rv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rv.add_theme_constant_override("separation", 8)
	rsc.add_child(rv)
	var w := Game.get_weapon(_selected_uid)
	if w.is_empty():
		rv.add_child(UIStyle.label("No weapons to enchant.", 20, UIStyle.INK, "ui"))
		return
	_weapon_header(rv, w)
	var rc := Catalog.rarity_color(int(w["rarity"]))
	var perks: Array = w.get("perks", [])
	if perks.is_empty():
		rv.add_child(UIStyle.label("No perks yet. Common weapons have none; infuse it to Uncommon to gain one.", 16, Color("6a5a48"), "body"))
	for pk in perks:
		var pd: Dictionary = Catalog.PERKS.get(pk, {})
		var pl := MenuPanel.rich("[color=#%s][b]%s[/b][/color]  %s" % [rc.darkened(0.3).to_html(false), pd.get("name", pk), pd.get("desc", "")], 16)
		pl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		rv.add_child(pl)
	var uid := int(w["uid"])
	# reroll
	rv.add_child(UIStyle.label("Reroll perks", 21, Color("5a3f8a"), "display"))
	var rcost := Catalog.reroll_cost(w)
	if rcost.is_empty():
		rv.add_child(UIStyle.label("Only Uncommon or better weapons have perks to reroll.", 16, Color("6a5a48"), "body"))
	else:
		rv.add_child(UIStyle.label("Replace this weapon's perks with fresh ones (different where possible).", 15, Color("5a4632"), "body"))
		rv.add_child(_cost_row(rcost["items"], int(rcost["gold"])))
		var rb := Game.reroll_block(uid)
		if rb == "rank":
			rv.add_child(UIStyle.label("Locked: needs Artisan rank %d" % int(rcost["rank"]), 15, Color("9a3a2a"), "body"))
		rv.add_child(MenuPanel.button("Reroll perks", func():
			if Game.reroll_perks(uid):
				AudioManager.play_ui("enchant", -2.0)
				Events.toast("Enchanted: %s" % Catalog.weapon_name(Game.get_weapon(uid)), "unlock")
			else:
				AudioManager.play_ui("ui_error"), 220, rb != ""))
	# infuse
	rv.add_child(UIStyle.label("Infuse rarity", 21, Color("5a3f8a"), "display"))
	var icost := Catalog.infuse_cost(w)
	if icost.is_empty():
		rv.add_child(UIStyle.label("Already as rare as infusion can make it (Epic). Legendaries are only ever found.", 16, Color("6a5a48"), "body"))
	else:
		var nr := int(w["rarity"]) + 1
		rv.add_child(MenuPanel.rich("Raise it to [color=#%s][b]%s[/b][/color]: +%d%% power%s." % [Catalog.rarity_color(nr).darkened(0.25).to_html(false),
			Catalog.RARITY_NAMES[nr], int(round((float(Catalog.RARITY_POWER[nr]) / float(Catalog.RARITY_POWER[nr - 1]) - 1.0) * 100.0)),
			", and a new perk" if int(Catalog.RARITY_PERKS[nr]) > perks.size() else ""], 16))
		rv.add_child(_cost_row(icost["items"], int(icost["gold"])))
		var ib := Game.infuse_block(uid)
		if ib == "rank":
			rv.add_child(UIStyle.label("Locked: needs Artisan rank %d" % int(icost["rank"]), 15, Color("9a3a2a"), "body"))
		rv.add_child(MenuPanel.button("Infuse to %s" % Catalog.RARITY_NAMES[nr], func():
			if Game.infuse_weapon(uid):
				AudioManager.play_ui("enchant", -1.0)
				Events.toast("Infused: %s" % Catalog.weapon_name(Game.get_weapon(uid)), "rarity_%d" % int(Game.get_weapon(uid)["rarity"]))
			else:
				AudioManager.play_ui("ui_error"), 240, ib != ""))
