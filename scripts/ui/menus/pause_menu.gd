class_name PauseMenu
extends MenuPanel
## Escape menu.

var ui: GameUI


func _init() -> void:
	panel_size = Vector2(520, 600)
	title_text = "Paused"


func build() -> void:
	var main := get_tree().current_scene
	var items := [
		["Resume", func(): closed.emit()],
		["Save game", func():
			if main.has_method("save_now"):
				main.save_now()],
		["Settings", func(): _open_settings()],
		["Controls", func(): _controls()],
		["Quit to title", func():
			closed.emit()
			main.quit_to_menu()],
		["Quit game", func():
			if main.has_method("save_now"):
				main.save_now()
			get_tree().quit()],
	]
	for it in items:
		var b := MenuPanel.button(it[0], it[1], 420)
		b.custom_minimum_size.y = 58
		b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		content.add_child(b)
	var st := UIStyle.label("Playtime %s  ·  Level %d  ·  %d gold" % [_fmt_time(float(Game.stats.get("playtime", 0.0))), Game.level, Game.gold], 17, Color("5a4632"), "body")
	st.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	content.add_child(st)


func _fmt_time(t: float) -> String:
	return "%d:%02d" % [int(t) / 3600, (int(t) / 60) % 60]


func _open_settings() -> void:
	var s := SettingsMenu.new()
	ui.open_menu(s)


func _controls() -> void:
	clear_content()
	set_title("Controls")
	content.add_child(MenuPanel.rich("[b]Move[/b] WASD · [b]Jump[/b] Space · [b]Sprint[/b] Shift · [b]Crouch[/b] Ctrl\n[b]Interact / sit / exit seat[/b] E\n[b]Use[/b] LMB · [b]Alternate[/b] RMB · [b]Reload / tool mode / rotate[/b] R\n[b]Hotbar[/b] 1-8 or mouse wheel\n[b]Build Catalog[/b] Q · [b]Undo spawn[/b] Z\n[b]Quest log[/b] J · [b]Character[/b] Tab\n[b]Health Tonic[/b] H · [b]Mana Draught[/b] G\n[b]Piloting[/b] WASD drive · Space/Ctrl lift · Shift boost · LMB turrets · F lights · V camera", 19))
	content.add_child(MenuPanel.button("Back", func():
		clear_content()
		set_title("Paused")
		build(), 200))
