class_name SettingsMenu
extends MenuPanel
## Graphics, controls and audio settings (applied live, saved on change).


func _init() -> void:
	panel_size = Vector2(860, 760)
	title_text = "Settings"


func build() -> void:
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	content.add_child(sc)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 24)
	grid.add_theme_constant_override("v_separation", 10)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(grid)
	_section(grid, "Graphics")
	var q := OptionButton.new()
	for n in ["Low (fastest)", "Medium", "High"]:
		q.add_item(n)
	q.selected = Settings.quality
	q.item_selected.connect(func(i): Settings.quality = i; _apply())
	_row(grid, "Quality preset", q)
	_row(grid, "Render scale", _slider(0.5, 1.0, 0.05, Settings.render_scale, func(v): Settings.render_scale = v; _apply(), "%d%%", 100.0))
	_row(grid, "Fullscreen", _check(Settings.fullscreen, func(v): Settings.fullscreen = v; _apply()))
	_row(grid, "V-Sync", _check(Settings.vsync, func(v): Settings.vsync = v; _apply()))
	_row(grid, "Cartoon outlines", _check(Settings.outlines, func(v): Settings.outlines = v; _apply()))
	_row(grid, "Grass density", _slider(0.0, 1.5, 0.1, Settings.grass_density, func(v): Settings.grass_density = v; _apply(), "%d%%", 100.0))
	_row(grid, "Show FPS", _check(Settings.show_fps, func(v): Settings.show_fps = v; _apply()))
	_row(grid, "Objective tracker", _check(Settings.show_objective, func(v): Settings.show_objective = v; _apply()))
	_section(grid, "Controls")
	_row(grid, "Field of view", _slider(65.0, 105.0, 1.0, Settings.fov, func(v): Settings.fov = v; _apply(), "%d°", 1.0))
	_row(grid, "Mouse sensitivity", _slider(0.03, 0.4, 0.01, Settings.mouse_sensitivity, func(v): Settings.mouse_sensitivity = v; _apply(), "%.2f", 1.0))
	_row(grid, "Invert Y", _check(Settings.invert_y, func(v): Settings.invert_y = v; _apply()))
	_section(grid, "Audio")
	_row(grid, "Master", _slider(0.0, 1.0, 0.05, Settings.volume_master, func(v): Settings.volume_master = v; _apply(), "%d%%", 100.0))
	_row(grid, "Music", _slider(0.0, 1.0, 0.05, Settings.volume_music, func(v): Settings.volume_music = v; _apply(), "%d%%", 100.0))
	_row(grid, "Effects", _slider(0.0, 1.0, 0.05, Settings.volume_sfx, func(v): Settings.volume_sfx = v; _apply(), "%d%%", 100.0))
	_row(grid, "Ambience", _slider(0.0, 1.0, 0.05, Settings.volume_ambience, func(v): Settings.volume_ambience = v; _apply(), "%d%%", 100.0))
	content.add_child(MenuPanel.button("Done", func(): closed.emit(), 200))


func _apply() -> void:
	Settings.apply()
	Settings.save_settings()


func _section(grid: GridContainer, t: String) -> void:
	grid.add_child(UIStyle.label(t, 26, Color("8a5a22"), "display"))
	grid.add_child(Control.new())


func _row(grid: GridContainer, label: String, ctl: Control) -> void:
	var l := UIStyle.label(label, 19, UIStyle.INK, "ui")
	l.custom_minimum_size.x = 260
	grid.add_child(l)
	ctl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.add_child(ctl)


func _check(v: bool, cb: Callable) -> CheckButton:
	var c := CheckButton.new()
	c.button_pressed = v
	c.toggled.connect(func(on): cb.call(on))
	return c


func _slider(mn: float, mx: float, step: float, v: float, cb: Callable, fmt: String, mult: float) -> HBoxContainer:
	var h := HBoxContainer.new()
	var s := HSlider.new()
	s.min_value = mn
	s.max_value = mx
	s.step = step
	s.value = v
	s.custom_minimum_size = Vector2(320, 30)
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var l := UIStyle.label(fmt % (v * mult), 18, UIStyle.INK, "ui")
	l.custom_minimum_size.x = 70
	s.value_changed.connect(func(nv):
		l.text = fmt % (nv * mult)
		cb.call(nv))
	h.add_child(s)
	h.add_child(l)
	return h
