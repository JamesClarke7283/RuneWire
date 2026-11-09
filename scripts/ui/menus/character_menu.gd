class_name CharacterMenu
extends MenuPanel
## Character sheet [Tab]: level, stats, upgrades, inventory and lifetime stats.


func _init() -> void:
	panel_size = Vector2(1100, 720)
	title_text = "Runewright"


func build() -> void:
	var hb := HBoxContainer.new()
	hb.size_flags_vertical = Control.SIZE_EXPAND_FILL
	hb.add_theme_constant_override("separation", 26)
	content.add_child(hb)
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation", 6)
	hb.add_child(left)
	left.add_child(UIStyle.label("Level %d" % Game.level, 34, Color("8a5a22"), "display"))
	left.add_child(UIStyle.label("XP %d / %d" % [Game.xp, Game.xp_to_next()], 19, UIStyle.INK, "ui"))
	var stats := [
		["Max health", "%d" % int(Game.max_health())],
		["Max mana", "%d" % int(Game.max_mana())],
		["Mana regeneration", "%.1f / s" % Game.mana_regen()],
		["Spell damage", "×%.2f" % Game.spell_damage_mult()],
		["Weapon & turret damage", "×%.2f" % Game.weapon_damage_mult()],
		["Part limit", "%d" % Game.part_limit()],
		["Gold", "%d" % Game.gold],
	]
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 30)
	for s in stats:
		grid.add_child(UIStyle.label(s[0], 19, UIStyle.INK, "body"))
		grid.add_child(UIStyle.label(s[1], 19, Color("8a5a10"), "ui"))
	left.add_child(grid)
	left.add_child(UIStyle.label("Upgrades", 26, Color("8a5a22"), "display"))
	for id in Catalog.UPGRADES:
		var u: Dictionary = Catalog.UPGRADES[id]
		left.add_child(UIStyle.label("%s  ·  tier %d/%d" % [u["name"], Game.upgrade_tier(id), u["prices"].size()], 18, UIStyle.INK, "body"))
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_theme_constant_override("separation", 6)
	hb.add_child(right)
	right.add_child(UIStyle.label("Inventory", 26, Color("8a5a22"), "display"))
	var any := false
	for id in Game.items:
		if int(Game.items[id]) <= 0:
			continue
		any = true
		var row := HBoxContainer.new()
		var model: String = Catalog.CONSUMABLES.get(id, Catalog.ITEMS.get(id, {})).get("model", "")
		row.add_child(MenuPanel.icon_rect(Catalog.item_icon(model), 44))
		row.add_child(UIStyle.label("%s  ×%d" % [Catalog.display_name(id), int(Game.items[id])], 19, UIStyle.INK, "ui"))
		right.add_child(row)
	if not any:
		right.add_child(UIStyle.label("Empty pockets.", 18, Color("5a4632"), "body"))
	right.add_child(UIStyle.label("Spare parts", 26, Color("8a5a22"), "display"))
	var parts_txt := ""
	for id in Game.parts:
		if int(Game.parts[id]) > 0:
			parts_txt += "%s ×%d   " % [Catalog.display_name(id), int(Game.parts[id])]
	var pl := UIStyle.label(parts_txt if parts_txt != "" else "None. Buy some in the Build Catalog [Q].", 17, UIStyle.INK, "body")
	pl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	pl.custom_minimum_size.x = 480
	right.add_child(pl)
	right.add_child(UIStyle.label("Deeds", 26, Color("8a5a22"), "display"))
	var st := Game.stats
	right.add_child(UIStyle.label("Foes defeated: %d (magic %d · tech %d) · Bosses: %d" % [int(st.get("kills", 0)), int(st.get("kills_magic", 0)), int(st.get("kills_tech", 0)), int(st.get("bosses", 0))], 17, UIStyle.INK, "body"))
	right.add_child(UIStyle.label("Gold earned: %d · spent: %d" % [int(st.get("gold_earned", 0)), int(st.get("gold_spent", 0))], 17, UIStyle.INK, "body"))
	right.add_child(UIStyle.label("Parts spawned: %d · Welds: %d · Quests: %d" % [int(st.get("parts_spawned", 0)), int(st.get("welds", 0)), int(st.get("quests_done", 0))], 17, UIStyle.INK, "body"))
	var medals := ""
	for cid in Challenges.CHALLENGES:
		medals += "%s: %s   " % [Challenges.def(cid)["name"], Challenges.MEDAL_NAMES[Challenges.best_medal(cid)]]
	var ml := UIStyle.label(medals, 16, UIStyle.INK, "body")
	ml.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ml.custom_minimum_size.x = 480
	right.add_child(ml)
