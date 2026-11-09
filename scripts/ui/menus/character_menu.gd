class_name CharacterMenu
extends MenuPanel
## Character sheet [Tab]: level, talents, Artisan rank, stats, upgrades, loadout, pack, materials and
## lifetime deeds.


func _init() -> void:
	panel_size = Vector2(1180, 780)
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
	left.add_child(UIStyle.label("Level %d / %d" % [Game.level, Catalog.MAX_LEVEL], 34, Color("8a5a22"), "display"))
	left.add_child(UIStyle.label("XP %d / %d" % [Game.xp, Game.xp_to_next()] if not Game.is_max_level() else "Maximum level!", 19, UIStyle.INK, "ui"))
	var pts := Game.talent_points()
	left.add_child(UIStyle.label("Talents: %d spent%s  ·  [K]" % [Game.talent_points_spent(), (", %d to spend!" % pts) if pts > 0 else ""], 18,
		Color("5a3f8a") if pts > 0 else UIStyle.INK, "ui"))
	var rank := Game.artisan_rank()
	left.add_child(UIStyle.label("Artisan rank %d · %s  ·  %d schematics" % [rank, Catalog.artisan_title(rank), Game.schematics.size()], 18, UIStyle.INK, "ui"))
	var stats := [
		["Max health", "%d" % int(Game.max_health())],
		["Max mana", "%d" % int(Game.max_mana())],
		["Mana regeneration", "%.1f / s" % Game.mana_regen()],
		["Magic weapon damage", "×%.2f" % Game.school_mult("magic")],
		["Tech weapon & turret damage", "×%.2f" % Game.school_mult("tech")],
		["Move speed", "×%.2f" % Game.move_mult()],
		["Pack", "%d / %d slots (%d pouches)" % [Game.pack_used(), Game.pack_capacity(), Game.pouch_count()]],
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
	var rsc := ScrollContainer.new()
	rsc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rsc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	hb.add_child(rsc)
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_theme_constant_override("separation", 6)
	rsc.add_child(right)
	right.add_child(UIStyle.label("Loadout", 26, Color("8a5a22"), "display"))
	for i in Game.WEAPON_SLOTS:
		var w := Game.loadout_weapon(i)
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		row.add_child(MenuPanel.icon_rect(Catalog.weapon_icon(w) if not w.is_empty() else null, 44))
		var nm := UIStyle.label("[%d] %s" % [i + 1, Catalog.weapon_name(w) if not w.is_empty() else "empty"], 19,
			Catalog.rarity_color(int(w.get("rarity", 0))).darkened(0.45) if not w.is_empty() else Color("8a7a68"), "ui")
		row.add_child(nm)
		right.add_child(row)
	var inv := UIStyle.label("Weapons carried: %d  ·  pack %d / %d  ·  open your Inventory with [I]" % [Game.weapons.size(), Game.pack_used(), Game.pack_capacity()], 17, UIStyle.INK, "body")
	right.add_child(inv)
	var mats := ""
	for id in Catalog.MATERIALS + ["ley_key"]:
		if Game.item_count(id) > 0:
			mats += "%s ×%d   " % [Catalog.display_name(id), Game.item_count(id)]
	var ml0 := UIStyle.label(mats if mats != "" else "No crafting materials yet.", 16, UIStyle.INK, "body")
	ml0.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ml0.custom_minimum_size.x = 480
	right.add_child(ml0)
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
	var total_chests := get_tree().get_nodes_in_group("chests").size()
	right.add_child(UIStyle.label("Treasure found: %d / %d (vaults %d) · Champions felled: %d" % [int(st.get("chests", 0)), total_chests, int(st.get("vaults", 0)), int(st.get("elites", 0))], 17, UIStyle.INK, "body"))
	right.add_child(UIStyle.label("Crystals harvested: %d · Ore mined: %d · Herbs & reeds: %d · Heaps scavenged: %d" % [int(st.get("harvested", 0)), int(st.get("mined", 0)), int(st.get("gathered", 0)), int(st.get("scavenged", 0))], 17, UIStyle.INK, "body"))
	right.add_child(UIStyle.label("Crafted: %d · Upgrades: %d · Enchantments: %d · Salvaged: %d" % [int(st.get("crafted", 0)), int(st.get("upgraded", 0)), int(st.get("enchanted", 0)), int(st.get("salvaged", 0))], 17, UIStyle.INK, "body"))
	var best := int(st.get("best_drop", 0))
	right.add_child(UIStyle.label("Best weapon found: %s" % Catalog.RARITY_NAMES[clampi(best, 0, 4)], 17, Catalog.rarity_color(best).darkened(0.4), "body"))
	var medals := ""
	for cid in Challenges.CHALLENGES:
		medals += "%s: %s   " % [Challenges.def(cid)["name"], Challenges.MEDAL_NAMES[Challenges.best_medal(cid)]]
	var ml := UIStyle.label(medals, 16, UIStyle.INK, "body")
	ml.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ml.custom_minimum_size.x = 480
	right.add_child(ml)
