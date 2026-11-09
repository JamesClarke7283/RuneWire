class_name InventoryMenu
extends MenuPanel
## Inventory [I]: your pack (weapons, consumables, materials and pouches, each stack filling a slot),
## its capacity, the five pouch slots that grow it, your key ring (keys and schematics) and the hotbar
## loadout. Drag a weapon onto hotbar slot 1 or 2 to wield it, a consumable onto quick slots 5-8, a
## pouch onto a pouch slot - or hover an item and press that number key. Right-click a weapon to equip /
## unequip it, a consumable to use it, a pouch to wear / remove it. Click anything for its details.

const TABS := ["all", "weapons", "consumables", "materials", "pouches"]
const TAB_NAMES := {"all": "All", "weapons": "Weapons", "consumables": "Consumables", "materials": "Materials",
	"pouches": "Pouches & Keys"}
const COLS := 7
const SLOT := 80.0
const TYPE_HINTS := {
	"shock": "Strong vs Cogwork machines",
	"arcane": "Strong vs Cogwork machines",
	"kinetic": "Strong vs wisps, golems and other Choir spirits",
	"fire": "Strong vs cultists; wisps shrug it off",
	"frost": "Chills foes; Ember Wisps and crawlers hate it",
	"none": "Support",
}

var ui: GameUI
var tab: String = "all"
var _tab_row: HBoxContainer
var _grid: GridContainer
var _info: VBoxContainer
var _actions: VBoxContainer   # the selected thing's buttons, pinned under the scrolling details
var _loadout_row: HBoxContainer
var _pouch_row: HBoxContainer
var _header: Label
var _cap_bar: ProgressBar
var _selected: Dictionary = {}
var _hover: Dictionary = {}
var _dirty: bool = false


func _init() -> void:
	panel_size = Vector2(1360, 880)
	title_text = "Inventory"


func build() -> void:
	_tab_row = HBoxContainer.new()
	_tab_row.add_theme_constant_override("separation", 8)
	content.add_child(_tab_row)
	for t in TABS:
		var b := MenuPanel.button(TAB_NAMES[t], func(): _set_tab(t), 0)
		b.toggle_mode = true
		b.name = "Tab_" + t
		_tab_row.add_child(b)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_tab_row.add_child(spacer)
	var hv := VBoxContainer.new()
	hv.add_theme_constant_override("separation", 2)
	_tab_row.add_child(hv)
	_header = UIStyle.label("", 20, Color("8a5a10"), "ui")
	_header.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	hv.add_child(_header)
	_cap_bar = ProgressBar.new()
	_cap_bar.custom_minimum_size = Vector2(330, 10)
	_cap_bar.show_percentage = false
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.2, 0.15, 0.1, 0.35)
	bg.set_corner_radius_all(5)
	_cap_bar.add_theme_stylebox_override("background", bg)
	hv.add_child(_cap_bar)

	var mid := HBoxContainer.new()
	mid.size_flags_vertical = Control.SIZE_EXPAND_FILL
	mid.add_theme_constant_override("separation", 16)
	content.add_child(mid)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(COLS * (SLOT + 8) + 22, 0)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	mid.add_child(sc)
	_grid = GridContainer.new()
	_grid.columns = COLS
	_grid.add_theme_constant_override("h_separation", 8)
	_grid.add_theme_constant_override("v_separation", 8)
	sc.add_child(_grid)
	var card := PanelContainer.new()
	var csb := StyleBoxFlat.new()
	csb.bg_color = Color(1, 1, 1, 0.32)
	csb.border_color = Color(UIStyle.BRASS_DARK, 0.5)
	csb.set_border_width_all(2)
	csb.set_corner_radius_all(12)
	csb.set_content_margin_all(14)
	card.add_theme_stylebox_override("panel", csb)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mid.add_child(card)
	var cardv := VBoxContainer.new()
	cardv.add_theme_constant_override("separation", 8)
	card.add_child(cardv)
	var isc := ScrollContainer.new()
	isc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	isc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	cardv.add_child(isc)
	_info = VBoxContainer.new()
	_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_info.add_theme_constant_override("separation", 6)
	isc.add_child(_info)
	_actions = VBoxContainer.new()
	cardv.add_child(_actions)

	# pouches (grow the pack) and the hotbar
	var pr := HBoxContainer.new()
	pr.add_theme_constant_override("separation", 14)
	content.add_child(pr)
	var pl := UIStyle.label("Pouches", 26, Color("8a5a22"), "display")
	pl.custom_minimum_size = Vector2(110, 0)
	pl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	pr.add_child(pl)
	_pouch_row = HBoxContainer.new()
	_pouch_row.add_theme_constant_override("separation", 8)
	pr.add_child(_pouch_row)
	var ph := UIStyle.label("Each pouch adds pack slots. Drag one from your pack onto a slot, or right-click it.\nFind pouches in chests, buy them from Odda, or sew them at the Loom.", 15, Color("5a4632"), "body")
	ph.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ph.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	pr.add_child(ph)

	var bottom := HBoxContainer.new()
	bottom.add_theme_constant_override("separation", 14)
	content.add_child(bottom)
	var bl := UIStyle.label("Hotbar", 26, Color("8a5a22"), "display")
	bl.custom_minimum_size = Vector2(110, 0)
	bl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	bottom.add_child(bl)
	_loadout_row = HBoxContainer.new()
	_loadout_row.add_theme_constant_override("separation", 8)
	bottom.add_child(_loadout_row)
	var hint := UIStyle.label("Drag any weapon - gun, wand, staff, blade - onto slots 1-2 and items onto 5-8, or hover one and press the number.\nRight-click: equip / unequip / use · X swaps weapons in play · I closes", 15, Color("5a4632"), "body")
	hint.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hint.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	bottom.add_child(hint)

	Game.inventory_changed.connect(_mark_dirty)
	Game.loadout_changed.connect(_mark_dirty)
	Game.pouches_changed.connect(_mark_dirty)
	Game.gold_changed.connect(_on_gold)
	# start on the weapon in hand
	var p := _player()
	if p and p.current_uid > 0:
		_selected = {"type": "weapon", "uid": p.current_uid}
	_refresh()


func _player() -> Player:
	return get_tree().get_first_node_in_group("player") as Player


func _set_tab(t: String) -> void:
	tab = t
	_refresh()


func _mark_dirty() -> void:
	if not _dirty:
		_dirty = true
		_refresh.call_deferred()


func _on_gold(_g: int, _d: int) -> void:
	_mark_dirty()


func _refresh() -> void:
	_dirty = false
	if not is_instance_valid(_grid):
		return
	for b in _tab_row.get_children():
		if b is Button:
			(b as Button).set_pressed_no_signal(String(b.name) == "Tab_" + tab)
	var used := Game.pack_used()
	var cap := Game.pack_capacity()
	_header.text = "Pack %d / %d   ·   %d gold" % [used, cap, Game.gold]
	_cap_bar.max_value = float(maxi(cap, 1))
	_cap_bar.value = float(mini(used, cap))
	var fg := StyleBoxFlat.new()
	fg.bg_color = Color("c0392b") if used >= cap else (Color("e0a030") if used >= cap - 2 else Color("3aa76d"))
	fg.set_corner_radius_all(5)
	_cap_bar.add_theme_stylebox_override("fill", fg)
	_fill_grid()
	_fill_pouches()
	_fill_loadout()
	_show_info(_hover if not _hover.is_empty() and _valid(_hover) else _selected)


func _valid(p: Dictionary) -> bool:
	match p.get("type", ""):
		"weapon":
			return not Game.get_weapon(int(p["uid"])).is_empty()
		"item":
			return Game.item_count(str(p["id"])) > 0 or Catalog.is_schematic(str(p["id"]))
		"pouch_slot":
			return str(Game.pouches[int(p["slot"])]) != ""
	return false


# ------------------------------------------------------------------ grid
## Pack contents for the tab: weapons in the pack, then one entry per stack of each item.
func _entries() -> Array:
	var out := []
	if tab in ["all", "weapons"]:
		var ws: Array = []
		for w in Game.weapons:
			if Game.equipped_slot(int(w["uid"])) < 0:
				ws.append(w)
		ws.sort_custom(func(a, b):
			if int(a["rarity"]) != int(b["rarity"]):
				return int(a["rarity"]) > int(b["rarity"])
			if int(a["level"]) != int(b["level"]):
				return int(a["level"]) > int(b["level"])
			return Catalog.weapon_name(a) < Catalog.weapon_name(b))
		for w in ws:
			out.append({"type": "weapon", "uid": int(w["uid"])})
	var ids := []
	if tab in ["all", "consumables"]:
		for id in Catalog.CONSUMABLES:
			ids.append(id)
	if tab in ["all", "materials"]:
		for id in Catalog.MATERIALS:
			ids.append(id)
	if tab in ["all", "pouches"]:
		for id in Catalog.POUCHES:
			ids.append(id)
	for id in ids:
		var n := Game.item_count(id)
		if n <= 0:
			continue
		var stack := Game.item_stack_size(id)
		var stacks := int(ceil(float(n) / float(stack)))
		for si in stacks:
			var c := mini(stack, n - si * stack)
			out.append({"type": "item", "id": id, "stack": si, "count": c})
	if tab == "pouches":
		# the key ring: keys and schematics take no pack space
		for id in Catalog.ITEMS:
			if Catalog.is_key_item(id) and Game.item_count(id) > 0:
				out.append({"type": "item", "id": id, "stack": 0, "count": Game.item_count(id), "keyring": true})
	return out


func _fill_grid() -> void:
	for c in _grid.get_children():
		c.queue_free()
	var entries := _entries()
	var cap := Game.pack_capacity()
	# "All" shows the whole pack: its open slots, then at least a row of locked ones (what pouches add)
	var open_slots := maxi(entries.size(), cap) if tab == "all" else entries.size()
	var total := open_slots + (InventoryMenu.COLS if tab == "all" else 0)
	total = maxi(total, COLS * 5)
	total = int(ceil(total / float(COLS))) * COLS
	var first_locked := open_slots if tab == "all" else total + 1
	for i in total:
		var s := InvSlot.new()
		s.menu = self
		s.size_px = SLOT
		if i < entries.size():
			var e: Dictionary = entries[i]
			s.payload = e
			s.selected = _same(e, _selected)
			_dress(s, e)
		elif i >= first_locked:
			s.payload = {"type": "locked"}
			s.setup(null, "+", -1, "", "", "", true, "Equip pouches to unlock more pack slots")
			s.modulate = Color(1, 1, 1, 0.45)
		else:
			s.payload = {"type": "empty"}
			s.setup(null)
		s.clicked.connect(_on_slot_clicked)
		s.hovered.connect(_on_slot_hovered)
		s.mouse_exited.connect(_on_slot_unhovered.bind(s))
		_grid.add_child(s)


func _same(a: Dictionary, b: Dictionary) -> bool:
	if a.is_empty() or b.is_empty() or a.get("type") != b.get("type"):
		return false
	match a["type"]:
		"weapon":
			return int(a["uid"]) == int(b["uid"])
		"pouch_slot":
			return int(a["slot"]) == int(b["slot"])
	return str(a.get("id", "")) == str(b.get("id", "")) and int(a.get("stack", 0)) == int(b.get("stack", 0))


func _dress(s: InvSlot, e: Dictionary) -> void:
	if e["type"] == "weapon":
		var w := Game.get_weapon(int(e["uid"]))
		var badge := ""
		if bool(w.get("new", false)):
			badge = "NEW"
		if bool(w.get("fav", false)):
			badge = "★ " + badge
		var lvl := int(w.get("level", 1))
		var sch := "✦" if Catalog.weapon_school(str(w["base"])) == "magic" else "⚙"
		s.setup(Catalog.weapon_icon(w), Catalog.display_name(str(w["base"])), int(w["rarity"]), "+%d" % (lvl - 1) if lvl > 1 else "",
			sch, badge, false, Catalog.weapon_name(w))
	else:
		var id: String = e["id"]
		var n := int(e.get("count", Game.item_count(id)))
		var q := Game.quick.find(id)
		var badge := ("[%d]" % (q + 5)) if q >= 0 and int(e.get("stack", 0)) == 0 else ""
		var rarity := -1
		if Catalog.is_pouch(id):
			rarity = int(Catalog.pouch_def(id).get("rarity", 0))
			badge = "+%d" % int(Catalog.pouch_def(id)["slots"])
		elif bool(e.get("keyring", false)):
			badge = "key"
		s.setup(Catalog.stack_icon(id), Catalog.display_name(id), rarity, "×%d" % n if n > 1 or not Catalog.is_pouch(id) else "", "", badge,
			false, Catalog.display_name(id))


# ------------------------------------------------------------------ pouch slots
func _fill_pouches() -> void:
	for c in _pouch_row.get_children():
		c.queue_free()
	for i in Game.POUCH_SLOTS:
		var s := InvSlot.new()
		s.menu = self
		s.size_px = 70.0
		var pid: String = Game.pouches[i]
		s.payload = {"type": "pouch_slot", "slot": i, "id": pid}
		if pid == "":
			s.setup(null, "Pouch\nslot", -1, "", "P%d" % (i + 1), "", true, "Drag a pouch here to carry more")
		else:
			var pd := Catalog.pouch_def(pid)
			s.selected = _same({"type": "pouch_slot", "slot": i}, _selected)
			s.setup(Catalog.stack_icon(pid), "", int(pd.get("rarity", 0)), "+%d" % int(pd["slots"]), "P%d" % (i + 1), "", false,
				"%s: +%d pack slots" % [pd["name"], int(pd["slots"])])
		s.clicked.connect(_on_slot_clicked)
		s.hovered.connect(_on_slot_hovered)
		s.mouse_exited.connect(_on_slot_unhovered.bind(s))
		_pouch_row.add_child(s)


# ------------------------------------------------------------------ loadout (hotbar) row
func _fill_loadout() -> void:
	for c in _loadout_row.get_children():
		c.queue_free()
	for i in Player.SELECT_SLOTS + Game.QUICK_SLOTS:
		if i == Game.WEAPON_SLOTS or i == Player.SELECT_SLOTS:
			var gap := VSeparator.new()
			_loadout_row.add_child(gap)
		var s := InvSlot.new()
		s.menu = self
		s.size_px = 78.0 if i < Game.WEAPON_SLOTS else 66.0
		if i < Game.WEAPON_SLOTS:
			var w := Game.loadout_weapon(i)
			s.payload = {"type": "loadout", "slot": i, "uid": int(w.get("uid", 0))}
			if w.is_empty():
				s.setup(null, "Weapon\nslot", -1, "", str(i + 1), "", true, "Drag any weapon here")
			else:
				s.selected = _same({"type": "weapon", "uid": int(w["uid"])}, _selected)
				s.setup(Catalog.weapon_icon(w), "", int(w["rarity"]), "", str(i + 1), "", false, Catalog.weapon_name(w))
		elif i < Player.SELECT_SLOTS:
			var tid: String = Catalog.TOOL_SLOTS[i - Game.WEAPON_SLOTS]
			s.payload = {"type": "tool", "id": tid}
			s.setup(Catalog.equipment_icon(tid), Catalog.display_name(tid), -1, "", str(i + 1), "", true,
				"%s: tools always stay on your hotbar" % Catalog.display_name(tid))
		else:
			var q := i - Player.SELECT_SLOTS
			var qid: String = Game.quick[q]
			s.payload = {"type": "quick", "slot": q, "id": qid}
			if qid == "":
				s.setup(null, "Item", -1, "", str(i + 1), "", true, "Drag a consumable here")
			else:
				s.setup(Catalog.stack_icon(qid), Catalog.display_name(qid), -1, "×%d" % Game.item_count(qid), str(i + 1), "",
					Game.item_count(qid) <= 0, Catalog.display_name(qid))
		s.clicked.connect(_on_slot_clicked)
		s.hovered.connect(_on_slot_hovered)
		s.mouse_exited.connect(_on_slot_unhovered.bind(s))
		_loadout_row.add_child(s)


# ------------------------------------------------------------------ interaction
func _payload_item(s: InvSlot) -> Dictionary:
	var p := s.payload
	match p.get("type", ""):
		"weapon", "item":
			return p
		"loadout":
			return {"type": "weapon", "uid": int(p["uid"])} if int(p.get("uid", 0)) > 0 else {}
		"quick":
			return {"type": "item", "id": p["id"], "stack": 0} if str(p.get("id", "")) != "" and Game.item_count(p["id"]) > 0 else {}
		"pouch_slot":
			return p if str(p.get("id", "")) != "" else {}
	return {}


func _on_slot_hovered(s: InvSlot) -> void:
	var it := _payload_item(s)
	_hover = it
	if it.get("type", "") == "weapon":
		var w := Game.get_weapon(int(it["uid"]))
		if bool(w.get("new", false)):
			w["new"] = false   # seen; the badge clears on the next refresh
	_show_info(it if not it.is_empty() else _selected)


func _on_slot_unhovered(_s: InvSlot) -> void:
	_hover = {}
	_show_info(_selected)


func _on_slot_clicked(s: InvSlot, button: int, double: bool) -> void:
	var p := s.payload
	var it := _payload_item(s)
	if button == MOUSE_BUTTON_RIGHT or double:
		_quick_action(p, it)
		return
	if not it.is_empty():
		_selected = it
		AudioManager.play_ui("ui_click", -8.0)
		_refresh()


## Right-click / double-click: equip or unequip a weapon or pouch, use a consumable, clear a quick slot.
func _quick_action(p: Dictionary, it: Dictionary) -> void:
	match p.get("type", ""):
		"loadout":
			if Game.unequip_slot(int(p["slot"])):
				AudioManager.play_ui("ui_equip")
		"quick":
			Game.set_quick(int(p["slot"]), "")
			AudioManager.play_ui("ui_click")
		"pouch_slot":
			if Game.unequip_pouch(int(p["slot"])):
				AudioManager.play_ui("pouch_equip", -4.0)
			else:
				AudioManager.play_ui("ui_error")
		"weapon":
			var uid := int(p["uid"])
			if Game.equipped_slot(uid) >= 0:
				Game.unequip_slot(Game.equipped_slot(uid))
			else:
				Game.equip_weapon(uid, _target_weapon_slot())
			AudioManager.play_ui("ui_equip")
		"item":
			var id := str(p["id"])
			if Catalog.is_pouch(id):
				if Game.equip_pouch(id):
					AudioManager.play_ui("pouch_equip", -4.0)
					it = {}
			else:
				_use_item(id)
	if not it.is_empty():
		_selected = it


## Which weapon slot an equip without an explicit slot goes to: an empty one, else the one in hand.
func _target_weapon_slot() -> int:
	for i in Game.WEAPON_SLOTS:
		if int(Game.loadout[i]) == 0:
			return i
	var p := _player()
	if p and p.slot < Game.WEAPON_SLOTS:
		return p.slot
	return 0


func _use_item(id: String) -> void:
	var c: Dictionary = Catalog.CONSUMABLES.get(id, {})
	if c.is_empty():
		return
	if str(c.get("use", "")) == "throw":
		Events.toast("Put the %s in a quick slot (5-8) and throw it in play" % c["name"], "info")
		return
	var p := _player()
	if p and p.use_consumable(id):
		AudioManager.play_ui("ui_click", -6.0)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouse or not event.is_pressed() or event.is_echo():
		return
	var it := _hover if not _hover.is_empty() else _selected
	if it.is_empty():
		return
	for i in 8:
		if not event.is_action_pressed("slot_%d" % (i + 1)):
			continue
		if it.get("type", "") == "weapon" and i < Game.WEAPON_SLOTS:
			Game.equip_weapon(int(it["uid"]), i)
			AudioManager.play_ui("ui_equip")
			get_viewport().set_input_as_handled()
		elif it.get("type", "") == "item" and i >= Player.SELECT_SLOTS and Catalog.is_consumable(str(it["id"])):
			Game.set_quick(i - Player.SELECT_SLOTS, str(it["id"]))
			AudioManager.play_ui("ui_equip")
			get_viewport().set_input_as_handled()
		elif it.get("type", "") == "item" and Catalog.is_pouch(str(it["id"])) and i < Game.POUCH_SLOTS:
			if Game.equip_pouch(str(it["id"]), i):
				AudioManager.play_ui("pouch_equip", -4.0)
			get_viewport().set_input_as_handled()
		return


# ------------------------------------------------------------------ drag & drop
func drag_data_for(s: InvSlot) -> Variant:
	var p := s.payload
	match p.get("type", ""):
		"weapon":
			return {"kind": "weapon", "uid": int(p["uid"])}
		"item":
			var id := str(p["id"])
			if Catalog.is_consumable(id):
				return {"kind": "item", "id": id}
			if Catalog.is_pouch(id):
				return {"kind": "pouch", "id": id}
		"loadout":
			if int(p.get("uid", 0)) > 0:
				return {"kind": "weapon", "uid": int(p["uid"]), "from_slot": int(p["slot"])}
		"quick":
			if str(p.get("id", "")) != "":
				return {"kind": "item", "id": str(p["id"]), "from_quick": int(p["slot"])}
		"pouch_slot":
			if str(p.get("id", "")) != "":
				return {"kind": "pouch", "id": str(p["id"]), "from_pouch": int(p["slot"])}
	return null


func can_drop_on(s: InvSlot, data: Variant) -> bool:
	if typeof(data) != TYPE_DICTIONARY:
		return false
	var d: Dictionary = data
	match s.payload.get("type", ""):
		"loadout":
			return d.get("kind", "") == "weapon"
		"quick":
			return d.get("kind", "") == "item" and Catalog.is_consumable(str(d.get("id", "")))
		"pouch_slot":
			return d.get("kind", "") == "pouch"
		"weapon", "item", "empty":
			return d.has("from_slot") or d.has("from_quick") or d.has("from_pouch")
	return false


func drop_on(s: InvSlot, data: Variant) -> void:
	if not can_drop_on(s, data):
		return
	var d: Dictionary = data
	var ok := true
	match s.payload.get("type", ""):
		"loadout":
			Game.equip_weapon(int(d["uid"]), int(s.payload["slot"]))
			_selected = {"type": "weapon", "uid": int(d["uid"])}
		"quick":
			Game.set_quick(int(s.payload["slot"]), str(d["id"]))
		"pouch_slot":
			if d.has("from_pouch"):
				Game.swap_pouch_slots(int(d["from_pouch"]), int(s.payload["slot"]))
			else:
				ok = Game.equip_pouch(str(d["id"]), int(s.payload["slot"]))
		_:
			if d.has("from_slot"):
				ok = Game.unequip_slot(int(d["from_slot"]))
			elif d.has("from_quick"):
				Game.set_quick(int(d["from_quick"]), "")
			elif d.has("from_pouch"):
				ok = Game.unequip_pouch(int(d["from_pouch"]))
	if not ok:
		AudioManager.play_ui("ui_error")
	else:
		AudioManager.play_ui("pouch_equip" if d.get("kind", "") == "pouch" else "ui_equip", -4.0 if d.get("kind", "") == "pouch" else 0.0)


# ------------------------------------------------------------------ details card
func _show_info(it: Dictionary) -> void:
	if not is_instance_valid(_info):
		return
	for c in _info.get_children() + _actions.get_children():
		c.queue_free()
	if it.is_empty() or not _valid(it):
		_info.add_child(UIStyle.label("Your pack", 30, Color("8a5a22"), "display"))
		var r := MenuPanel.rich("Click an item to inspect it.\n\n[b]Pack space:[/b] every weapon and every stack of items fills one slot (materials stack to 20-40, consumables to 10). Equipped weapons and pouches, keys and schematics take no space. Wear up to [b]five pouches[/b] to grow your pack.\n\n[b]Weapons[/b] go in hotbar slots [b]1[/b] and [b]2[/b]: any gun, wand, staff, tome or blade fits either slot. Tools sit in [b]3[/b] and [b]4[/b]; consumables in quick slots [b]5-8[/b] are used instantly.\n\nFind weapons on foes (Champions drop the best), in chests and Ley Vaults, or buy and craft them. Craft at the five stations in Emberwick; upgrade, salvage and enchant there too.", 17)
		r.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_info.add_child(r)
		_add_schematic_list()
		return
	match it["type"]:
		"weapon":
			_weapon_info(Game.get_weapon(int(it["uid"])))
		"pouch_slot":
			_pouch_info(str(Game.pouches[int(it["slot"])]), int(it["slot"]))
		_:
			if Catalog.is_pouch(str(it["id"])):
				_pouch_info(str(it["id"]), -1)
			else:
				_item_info(str(it["id"]))


func _add_schematic_list() -> void:
	if Game.schematics.is_empty():
		return
	var names := []
	for rid in Game.schematics:
		names.append(Catalog.recipe_name(rid))
	names.sort()
	_info.add_child(UIStyle.label("Schematics learned (%d)" % names.size(), 20, Color("5a3f8a"), "display"))
	var l := MenuPanel.rich(", ".join(names), 15)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_info.add_child(l)


func _weapon_info(w: Dictionary) -> void:
	var s := Catalog.weapon_stats(w)
	var rarity := int(w["rarity"])
	var rc := Catalog.rarity_color(rarity)
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 12)
	_info.add_child(top)
	var icon_box := PanelContainer.new()
	var ib := StyleBoxFlat.new()
	ib.bg_color = Color(0.12, 0.1, 0.16, 0.9)
	ib.border_color = rc
	ib.set_border_width_all(3)
	ib.set_corner_radius_all(12)
	ib.set_content_margin_all(6)
	icon_box.add_theme_stylebox_override("panel", ib)
	icon_box.add_child(MenuPanel.icon_rect(Catalog.weapon_icon(w), 118))
	top.add_child(icon_box)
	var tv := VBoxContainer.new()
	tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(tv)
	var nl := UIStyle.label(Catalog.weapon_name(w), 26, rc.darkened(0.35) if rarity == 0 else rc.darkened(0.25), "display", 5, Color(0.15, 0.1, 0.08, 0.9))
	nl.add_theme_color_override("font_color", rc if rarity > 0 else Color("f3e3bf"))
	nl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tv.add_child(nl)
	var school := str(s.get("school", "tech"))
	tv.add_child(UIStyle.label("%s %s %s  ·  Level %d / %d" % [Catalog.RARITY_NAMES[rarity], Catalog.SCHOOL_NAMES.get(school, ""),
		Catalog.KIND_NAMES.get(s.get("kind", ""), ""), int(w["level"]), Catalog.MAX_WEAPON_LEVEL], 17, Color("5a4632"), "ui"))
	var es := Game.equipped_slot(int(w["uid"]))
	tv.add_child(UIStyle.label("Equipped in slot %d" % (es + 1) if es >= 0 else "In your pack", 16,
		Color("2e7d32") if es >= 0 else Color("6a5a48"), "body"))
	var desc := MenuPanel.rich("[i]%s[/i]" % Catalog.weapon_base(str(w["base"])).get("desc", ""), 16)
	desc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_info.add_child(desc)
	# comparison target: the weapon in hand (or slot 1) when looking at something else
	var cmp := {}
	var cmp_w := {}
	var p := _player()
	var hand := p.current_uid if p else 0
	if hand > 0 and hand != int(w["uid"]):
		cmp_w = Game.get_weapon(hand)
	elif Game.equipped_slot(int(w["uid"])) < 0 and not Game.loadout_weapon(0).is_empty():
		cmp_w = Game.loadout_weapon(0)
	if not cmp_w.is_empty():
		cmp = Catalog.weapon_stats(cmp_w)
		_info.add_child(UIStyle.label("Compared with %s" % Catalog.weapon_name(cmp_w), 14, Color("6a5a48"), "body"))
	var grid := GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 18)
	grid.add_theme_constant_override("v_separation", 2)
	_info.add_child(grid)
	var dmult := Game.school_mult(school)
	var cmult := Game.school_mult(str(cmp.get("school", "tech")))
	var rows := []
	if float(s.get("damage", 0.0)) > 0.0:
		var dmg := float(s["damage"]) * dmult
		var txt := "%d" % int(round(dmg))
		var mult_n := int(s.get("pellets", s.get("shards", s.get("seekers", 1))))
		if mult_n > 1:
			txt = "%d × %d" % [int(round(dmg)), mult_n]
		if str(s.get("cast", "")) == "beam":
			txt += " / s"
		rows.append(["Damage", txt, dmg * mult_n, float(cmp.get("damage", 0.0)) * cmult * float(cmp.get("pellets", cmp.get("shards", cmp.get("seekers", 1)))), true])
		rows.append(["Damage per second", "%d" % int(round(Catalog.weapon_dps(s) * dmult)), Catalog.weapon_dps(s) * dmult,
			Catalog.weapon_dps(cmp) * cmult if not cmp.is_empty() else 0.0, true])
	rows.append(["Damage type", "%s" % str(s.get("damage_type", "")).capitalize(), null, null, true])
	if s.has("fire_rate") and not s.has("charge") and str(s.get("fire", "")) != "flame":
		rows.append(["Fire rate", "%.1f / s" % float(s["fire_rate"]), float(s["fire_rate"]), cmp.get("fire_rate"), true])
	if s.has("spinup"):
		rows.append(["Spin-up", "%.1f s" % float(s["spinup"]), null, null, false])
	if s.has("charge"):
		rows.append(["Charge time", "%.2f s" % float(s["charge"]), float(s["charge"]), cmp.get("charge"), false])
	if s.has("cooldown") and str(s.get("cast", "")) != "beam":
		rows.append(["Cooldown", "%.2f s" % float(s["cooldown"]), float(s["cooldown"]), cmp.get("cooldown"), false])
	if s.has("swing_time"):
		rows.append(["Swing time", "%.2f s" % float(s["swing_time"]), float(s["swing_time"]), cmp.get("swing_time"), false])
	if s.has("mag"):
		rows.append(["Fuel" if str(s.get("fire", "")) == "flame" else "Magazine", "%d" % int(s["mag"]), float(s["mag"]), cmp.get("mag"), true])
	if s.has("reload"):
		rows.append(["Reload", "%.1f s" % float(s["reload"]), float(s["reload"]), cmp.get("reload"), false])
	if s.has("mana"):
		rows.append(["Mana cost", "%d%s" % [int(round(float(s["mana"]))), " / s" if str(s.get("cast", "")) == "beam" else ""], float(s["mana"]), cmp.get("mana"), false])
	if s.has("splash"):
		rows.append(["Blast", "%d  (%.1f m)" % [int(round(float(s["splash"]) * dmult)), float(s.get("radius", 0.0))], null, null, true])
	if s.has("chains"):
		rows.append(["Chains", "%d extra foes" % int(s["chains"]), null, null, true])
	if s.has("pierce"):
		rows.append(["Pierces", "%d foes" % (int(s["pierce"]) + 1), null, null, true])
	if float(s.get("burn", 0.0)) > 0.0:
		var bc := float(s.get("burn_chance", 0.0))
		rows.append(["Burn", "%d fire / s%s" % [int(round(float(s["burn"]) * dmult)), "" if bc >= 1.0 else " (%d%% chance)" % int(bc * 100.0)], null, null, true])
	if float(s.get("chill", 0.0)) > 0.0:
		var cc := float(s.get("chill_chance", 0.0))
		rows.append(["Chill", "%d%% slower%s" % [int(float(s["chill"]) * 100.0), "" if cc >= 1.0 else " (%d%% chance)" % int(cc * 100.0)], null, null, true])
	if float(s.get("crit_chance", 0.0)) > 0.0:
		rows.append(["Critical hits", "%d%% chance" % int(round(float(s["crit_chance"]) * 100.0)), null, null, true])
	if s.has("zap"):
		rows.append(["Capacitor zap", "+%d shock" % int(round(float(s["zap"]) * dmult)), null, null, true])
	if s.has("quake"):
		rows.append(["Ground slam", "%.1f m shockwave" % float(s["quake"]), null, null, true])
	if s.has("wave"):
		rows.append(["Rune wave", "%d (pierces 4)" % int(round(float(s["wave"]) * dmult)), null, null, true])
	if s.has("repair"):
		rows.append(["Repairs parts", "%d HP per hit" % int(round(float(s["repair"]))), null, null, true])
	if s.has("heal"):
		rows.append(["Heals", "%d over %d s" % [int(round(float(s["heal"]))), int(s.get("duration", 5))], null, null, true])
	if bool(s.get("scope", false)):
		rows.append(["Scope", "RMB zoom, +25% damage", null, null, true])
	if s.has("move_slow"):
		rows.append(["While firing", "you move %d%% slower" % int(float(s["move_slow"]) * 100.0), null, null, true])
	if s.has("range"):
		rows.append(["Range", "%d m" % int(s["range"]), float(s["range"]), cmp.get("range"), true])
	for r in rows:
		grid.add_child(UIStyle.label(r[0], 17, UIStyle.INK, "body"))
		grid.add_child(UIStyle.label(r[1], 17, Color("6b3f0e"), "ui"))
		grid.add_child(_delta_label(r[2], r[3], r[4]))
	_info.add_child(UIStyle.label(TYPE_HINTS.get(str(s.get("damage_type", "")), ""), 15, Color("3a6a8a"), "body"))
	var perks: Array = w.get("perks", [])
	if not perks.is_empty():
		_info.add_child(UIStyle.label("Perks", 21, Color("8a5a22"), "display"))
		for pk in perks:
			var pd: Dictionary = Catalog.PERKS.get(pk, {})
			var pl := MenuPanel.rich("[color=#%s][b]%s[/b][/color]  %s" % [rc.darkened(0.3).to_html(false), pd.get("name", pk), pd.get("desc", "")], 16)
			pl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			_info.add_child(pl)
	_info.add_child(UIStyle.label("Sells for %d gold  ·  upgrade, salvage and enchant at the stations" % Catalog.weapon_value(w), 14, Color("6a5a48"), "body"))
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 8)
	row.add_theme_constant_override("v_separation", 8)
	_actions.add_child(row)
	var uid := int(w["uid"])
	for i in Game.WEAPON_SLOTS:
		var b := MenuPanel.button("Equip → slot %d" % (i + 1), func():
			Game.equip_weapon(uid, i)
			AudioManager.play_ui("ui_equip"), 0, Game.equipped_slot(uid) == i)
		row.add_child(b)
	if es >= 0:
		row.add_child(MenuPanel.button("Unequip", func():
			if Game.unequip_slot(Game.equipped_slot(uid)):
				AudioManager.play_ui("ui_equip")
			else:
				AudioManager.play_ui("ui_error"), 0, Game.pack_free() <= 0))
	row.add_child(MenuPanel.button("★ Unfavourite" if bool(w.get("fav", false)) else "☆ Favourite", func():
		Game.toggle_favorite(uid)))


func _delta_label(v: Variant, c: Variant, higher_better: bool) -> Label:
	if v == null or c == null or float(c) <= 0.0 or is_equal_approx(float(v), float(c)):
		return UIStyle.label("", 15, UIStyle.INK, "ui")
	var pct := (float(v) - float(c)) / float(c) * 100.0
	var good := (pct > 0.0) == higher_better
	return UIStyle.label("%s%d%%" % ["+" if pct > 0.0 else "", int(round(pct))], 15, Color("2e7d32") if good else Color("b03a2e"), "ui")


func _pouch_info(id: String, slot: int) -> void:
	var pd := Catalog.pouch_def(id)
	var r := int(pd.get("rarity", 0))
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 12)
	_info.add_child(top)
	top.add_child(MenuPanel.icon_rect(Catalog.stack_icon(id), 118))
	var tv := VBoxContainer.new()
	tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(tv)
	var nl := UIStyle.label(str(pd.get("name", id)), 26, Catalog.rarity_color(r).darkened(0.35) if r > 0 else UIStyle.INK, "display")
	nl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tv.add_child(nl)
	tv.add_child(UIStyle.label("%s pouch  ·  +%d pack slots" % [Catalog.RARITY_NAMES[r], int(pd["slots"])], 17, Color("5a4632"), "ui"))
	tv.add_child(UIStyle.label("Worn in pouch slot %d" % (slot + 1) if slot >= 0 else "In your pack (%d)" % Game.item_count(id), 16,
		Color("2e7d32") if slot >= 0 else Color("6a5a48"), "body"))
	var txt := str(pd.get("desc", ""))
	if pd.has("perk_desc"):
		txt += "\n\n[b]Perk:[/b] [color=#2e5d8a]%s[/color]" % pd["perk_desc"]
	var dl := MenuPanel.rich(txt, 17)
	dl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_info.add_child(dl)
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 8)
	_actions.add_child(row)
	if slot >= 0:
		row.add_child(MenuPanel.button("Take off", func():
			if Game.unequip_pouch(slot):
				AudioManager.play_ui("pouch_equip", -4.0)
			else:
				AudioManager.play_ui("ui_error")))
	else:
		row.add_child(MenuPanel.button("Wear it", func():
			if Game.equip_pouch(id):
				AudioManager.play_ui("pouch_equip", -4.0)
				_selected = {}
			else:
				AudioManager.play_ui("ui_error"), 0, not Game.pouches.has("")))
		for i in Game.POUCH_SLOTS:
			row.add_child(MenuPanel.button("→ P%d" % (i + 1), func():
				if Game.equip_pouch(id, i):
					AudioManager.play_ui("pouch_equip", -4.0)
					_selected = {}
				else:
					AudioManager.play_ui("ui_error")))


func _item_info(id: String) -> void:
	var d := Catalog.stack_def(id)
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 12)
	_info.add_child(top)
	top.add_child(MenuPanel.icon_rect(Catalog.stack_icon(id), 118))
	var tv := VBoxContainer.new()
	tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(tv)
	var nl := UIStyle.label(str(d.get("name", id)), 26, UIStyle.INK, "display")
	nl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tv.add_child(nl)
	var cat := Catalog.item_category(id)
	var kind := {"consumable": "Consumable", "key": "Key item (no pack space)", "material": "Crafting material"}.get(cat, "Item")
	tv.add_child(UIStyle.label("%s  ·  ×%d" % [kind, Game.item_count(id)], 17, Color("5a4632"), "ui"))
	if Catalog.takes_space(id):
		tv.add_child(UIStyle.label("Stacks to %d per pack slot  ·  sells for %d gold each" % [Game.item_stack_size(id), Catalog.stack_value(id)], 15, Color("6a5a48"), "body"))
	var desc := MenuPanel.rich(str(d.get("desc", "")), 17)
	desc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_info.add_child(desc)
	if d.has("src"):
		var sl := MenuPanel.rich("[b]Where to get it:[/b] [i]%s[/i]" % d["src"], 15)
		sl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_info.add_child(sl)
	var uses := []
	for rid in Catalog.RECIPES:
		var r: Dictionary = Catalog.RECIPES[rid]
		if (r.get("cost", {}) as Dictionary).has(id) and not Catalog.recipe_name(rid) in uses:
			uses.append(Catalog.recipe_name(rid))
	if not uses.is_empty():
		var ul := MenuPanel.rich("[b]Crafts into:[/b] " + ", ".join(uses), 16)
		ul.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_info.add_child(ul)
	if not Catalog.is_consumable(id):
		return
	var q := Game.quick.find(id)
	_info.add_child(UIStyle.label("In quick slot %d" % (q + 5) if q >= 0 else "Not on your hotbar", 16,
		Color("2e7d32") if q >= 0 else Color("6a5a48"), "body"))
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 8)
	row.add_theme_constant_override("v_separation", 8)
	_actions.add_child(row)
	var use: String = Catalog.CONSUMABLES[id].get("use", "")
	if use != "throw":
		row.add_child(MenuPanel.button("Use now", func(): _use_item(id)))
	for i in Game.QUICK_SLOTS:
		row.add_child(MenuPanel.button("→ %d" % (i + 5), func():
			Game.set_quick(i, id)
			AudioManager.play_ui("ui_equip"), 0, q == i))
