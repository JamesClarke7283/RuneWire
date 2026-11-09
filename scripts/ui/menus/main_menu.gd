class_name MainMenu
extends Control
## Title screen, centred over the slowly orbiting town.

var ui: GameUI
var _buttons: VBoxContainer
var _main: Node


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_main = get_tree().current_scene
	# soft vignette plus a darker column behind the menu for readability
	var shade := ColorRect.new()
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = """shader_type canvas_item;
void fragment() {
	float vig = smoothstep(0.35, 0.9, distance(UV, vec2(0.5)));
	float column = 1.0 - smoothstep(0.12, 0.3, abs(UV.x - 0.5));
	COLOR = vec4(0.05, 0.04, 0.1, clamp(vig * 0.7 + column * 0.45, 0.0, 0.85));
}"""
	var sm := ShaderMaterial.new()
	sm.shader = sh
	shade.material = sm
	add_child(shade)
	# everything centred on screen
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	var col := VBoxContainer.new()
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	col.add_theme_constant_override("separation", 16)
	center.add_child(col)
	var logo := ui._logo(640)
	logo.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	col.add_child(logo)
	var sub := UIStyle.label("A cartoon RPG of magic and machines", 26, UIStyle.PARCHMENT, "ui", 6, Color(0, 0, 0, 0.7))
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(sub)
	var gap := Control.new()
	gap.custom_minimum_size.y = 24
	col.add_child(gap)
	_buttons = VBoxContainer.new()
	_buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	_buttons.add_theme_constant_override("separation", 12)
	_buttons.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	col.add_child(_buttons)
	_main_buttons()
	var foot := UIStyle.label("Made with Godot, Blender and GIMP  ·  Fonts: Lilita One, Fredoka, Nunito (OFL)", 15, Color(1, 1, 1, 0.6), "body", 4, Color(0, 0, 0, 0.6))
	foot.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	foot.custom_minimum_size = Vector2(900, 0)
	UIStyle.anchor(foot, Control.PRESET_CENTER_BOTTOM, Vector2(-450, -44))
	add_child(foot)


func _clear() -> void:
	for c in _buttons.get_children():
		c.queue_free()


func _main_buttons() -> void:
	_clear()
	if SaveSystem.has_save():
		_btn("Continue", func(): _main.start_game(false))
	_btn("New Game", func():
		if SaveSystem.has_save():
			_confirm_new()
		else:
			_main.start_game(true))
	_btn("Settings", func():
		var s := SettingsMenu.new()
		s.closed.connect(func(): s.queue_free())
		add_child(s))
	_btn("Quit", func(): get_tree().quit())


func _btn(t: String, cb: Callable) -> void:
	var b := MenuPanel.button(t, cb, 360)
	b.custom_minimum_size.y = 60
	b.add_theme_font_size_override("font_size", 24)
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_buttons.add_child(b)


func _confirm_new() -> void:
	_clear()
	var l := UIStyle.label("Start over? Your current save will be replaced.", 22, UIStyle.PARCHMENT, "ui", 6, Color(0, 0, 0, 0.7))
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_buttons.add_child(l)
	_btn("Yes, new game", func():
		SaveSystem.delete_save()
		_main.start_game(true))
	_btn("Back", _main_buttons)
