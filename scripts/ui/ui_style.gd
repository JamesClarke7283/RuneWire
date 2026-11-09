class_name UIStyle
## RuneWire UI look: warm parchment + brass for menus, dark slate + brass for the HUD,
## teal/violet magic accents. Uses the GIMP-painted 9-slice textures when they exist.

const PARCHMENT := Color("f3e3bf")
const PARCHMENT_DARK := Color("d9c08f")
const INK := Color("3a2a1e")
const BRASS := Color("d9a441")
const BRASS_DARK := Color("8a5a22")
const SLATE := Color("1d2333")
const SLATE_LIGHT := Color("2c3550")
const TEAL := Color("39d5c4")
const VIOLET := Color("9a66ff")
const GOLD := Color("ffc93c")
const HEALTH := Color("e8484e")
const MANA := Color("4d8dff")
const XP := Color("ffc93c")
const GOOD := Color("6fdc6a")
const BAD := Color("ff5a4e")

const UI_TEX := "res://assets/textures/ui/%s.png"

static var _theme: Theme = null
static var _fonts: Dictionary = {}


static func font(font_name: String) -> Font:
	if _fonts.has(font_name):
		return _fonts[font_name]
	var path := "res://assets/fonts/%s.ttf" % font_name
	var f: Font = null
	if ResourceLoader.exists(path):
		f = load(path)
	if f is FontFile and font_name in ["Fredoka", "Nunito"]:
		# variable fonts: pick a bolder instance for readability
		var fv := FontVariation.new()
		fv.base_font = f
		fv.variation_opentype = {"wght": 600 if font_name == "Fredoka" else 650}
		f = fv
	_fonts[font_name] = f
	return f


static func display_font() -> Font:
	return font("LilitaOne")


static func ui_font() -> Font:
	return font("Fredoka")


static func body_font() -> Font:
	return font("Nunito")


static func tex(tex_name: String) -> Texture2D:
	var path := UI_TEX % tex_name
	if ResourceLoader.exists(path):
		return load(path)
	return null


static func panel_box(dark: bool = false, margin: int = 18) -> StyleBox:
	var t := tex("ui_panel_dark" if dark else "ui_panel")
	if t:
		var sb := StyleBoxTexture.new()
		sb.texture = t
		sb.texture_margin_left = 48
		sb.texture_margin_right = 48
		sb.texture_margin_top = 48
		sb.texture_margin_bottom = 48
		sb.content_margin_left = margin + 6
		sb.content_margin_right = margin + 6
		sb.content_margin_top = margin + 4
		sb.content_margin_bottom = margin + 4
		return sb
	var f := StyleBoxFlat.new()
	f.bg_color = SLATE.lerp(Color.BLACK, 0.1) if dark else PARCHMENT
	f.bg_color.a = 0.94
	f.border_color = BRASS
	f.set_border_width_all(3)
	f.set_corner_radius_all(14)
	f.shadow_color = Color(0, 0, 0, 0.35)
	f.shadow_size = 8
	f.set_content_margin_all(margin)
	return f


static func button_box(state: String) -> StyleBox:
	var name := {"normal": "ui_button", "hover": "ui_button_hover", "pressed": "ui_button_pressed"}.get(state, "ui_button")
	var t := tex(name)
	if t:
		var sb := StyleBoxTexture.new()
		sb.texture = t
		# 14 + 16 px caps fit the 36-44 px tabs and small buttons (20 + 20 squashed the rim into the label)
		sb.texture_margin_left = 24
		sb.texture_margin_right = 24
		sb.texture_margin_top = 14
		sb.texture_margin_bottom = 16
		if state == "disabled":
			sb.modulate_color = Color(0.72, 0.74, 0.74)
		sb.content_margin_left = 18
		sb.content_margin_right = 18
		sb.content_margin_top = 8
		sb.content_margin_bottom = 10
		return sb
	var f := StyleBoxFlat.new()
	match state:
		"hover":
			f.bg_color = Color("f2b84e")
		"pressed":
			f.bg_color = Color("b9822f")
		"disabled":
			f.bg_color = Color("9c8f7a")
		_:
			f.bg_color = BRASS
	f.border_color = BRASS_DARK
	f.set_border_width_all(2)
	f.border_width_bottom = 4
	f.set_corner_radius_all(10)
	f.content_margin_left = 16
	f.content_margin_right = 16
	f.content_margin_top = 6
	f.content_margin_bottom = 8
	return f


static func build_theme() -> Theme:
	if _theme:
		return _theme
	var th := Theme.new()
	var uf := ui_font()
	if uf:
		th.default_font = uf
	th.default_font_size = 19
	th.set_stylebox("panel", "PanelContainer", panel_box(false))
	th.set_stylebox("panel", "Panel", panel_box(false))
	for st in ["normal", "hover", "pressed", "disabled", "focus"]:
		var sb: StyleBox = button_box(st if st != "focus" else "hover")
		if st == "focus":
			sb = StyleBoxEmpty.new()
		th.set_stylebox(st, "Button", sb)
	# Button labels sit across the teal button's light and dark halves: warm white with a dark-teal
	# outline reads on both (dark ink on the lower half was hard to read). List rows override this.
	th.set_color("font_color", "Button", Color("fff6e0"))
	th.set_color("font_hover_color", "Button", Color("ffffff"))
	th.set_color("font_focus_color", "Button", Color("fff6e0"))
	th.set_color("font_pressed_color", "Button", Color("ffe7a3"))
	th.set_color("font_hover_pressed_color", "Button", Color("ffe7a3"))
	th.set_color("font_disabled_color", "Button", Color(0.9, 0.9, 0.86, 0.72))
	th.set_color("font_outline_color", "Button", Color("173634"))
	th.set_constant("outline_size", "Button", 5)
	th.set_font_size("font_size", "Button", 19)
	th.set_color("font_color", "Label", INK)
	th.set_color("default_color", "RichTextLabel", INK)
	var bf := body_font()
	if bf:
		th.set_font("normal_font", "RichTextLabel", bf)
	th.set_font_size("normal_font_size", "RichTextLabel", 18)
	var df := display_font()
	if df:
		th.set_font("bold_font", "RichTextLabel", df)
	# Tabs
	var tab_sel := StyleBoxFlat.new()
	tab_sel.bg_color = BRASS
	tab_sel.set_corner_radius_all(8)
	tab_sel.set_content_margin_all(8)
	var tab_un := tab_sel.duplicate() as StyleBoxFlat
	tab_un.bg_color = PARCHMENT_DARK
	th.set_stylebox("tab_selected", "TabBar", tab_sel)
	th.set_stylebox("tab_unselected", "TabBar", tab_un)
	th.set_stylebox("tab_hovered", "TabBar", tab_sel)
	th.set_color("font_selected_color", "TabBar", INK)
	th.set_color("font_unselected_color", "TabBar", INK)
	th.set_color("font_hovered_color", "TabBar", INK)
	# Scroll & sliders
	# (the content margins give the bars their width: without them every scrollbar was 0 px wide and
	# long lists gave no hint that they scroll)
	var grab := StyleBoxFlat.new()
	grab.bg_color = BRASS
	grab.set_corner_radius_all(6)
	grab.content_margin_left = 5
	grab.content_margin_right = 5
	grab.content_margin_top = 12
	grab.content_margin_bottom = 12
	var grab_hi := grab.duplicate() as StyleBoxFlat
	grab_hi.bg_color = Color("f2b84e")
	th.set_stylebox("grabber", "VScrollBar", grab)
	th.set_stylebox("grabber_highlight", "VScrollBar", grab_hi)
	th.set_stylebox("grabber_pressed", "VScrollBar", grab_hi)
	var track := StyleBoxFlat.new()
	track.bg_color = Color(0, 0, 0, 0.12)
	track.set_corner_radius_all(6)
	track.content_margin_left = 5
	track.content_margin_right = 5
	th.set_stylebox("scroll", "VScrollBar", track)
	th.set_stylebox("scroll_focus", "VScrollBar", track)
	th.set_stylebox("slider", "HSlider", track)
	th.set_icon("grabber", "HSlider", _circle_icon(BRASS))
	th.set_icon("grabber_highlight", "HSlider", _circle_icon(Color("f2b84e")))
	th.set_color("font_color", "CheckBox", INK)
	# toggles are plain rows (label, switch on the right) rather than full-width teal buttons
	var row_hover := StyleBoxFlat.new()
	row_hover.bg_color = Color(BRASS, 0.14)
	row_hover.set_corner_radius_all(8)
	row_hover.set_content_margin_all(6)
	var row_plain := StyleBoxEmpty.new()
	row_plain.set_content_margin_all(6)
	for kind in ["CheckButton", "CheckBox"]:
		for st in ["normal", "pressed", "disabled", "focus"]:
			th.set_stylebox(st, kind, row_plain)
		th.set_stylebox("hover", kind, row_hover)
		th.set_stylebox("hover_pressed", kind, row_hover)
		for c in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color", "font_focus_color"]:
			th.set_color(c, kind, INK)
		th.set_constant("outline_size", kind, 0)
	for c in ["font_color", "font_focus_color"]:
		th.set_color(c, "OptionButton", Color("fff6e0"))
	th.set_color("font_hover_color", "OptionButton", Color("ffffff"))
	th.set_color("font_pressed_color", "OptionButton", Color("ffe7a3"))
	th.set_color("font_outline_color", "OptionButton", Color("173634"))
	th.set_constant("outline_size", "OptionButton", 5)
	var tip := StyleBoxFlat.new()
	tip.bg_color = Color(SLATE, 0.96)
	tip.border_color = BRASS
	tip.set_border_width_all(2)
	tip.set_corner_radius_all(8)
	tip.set_content_margin_all(10)
	th.set_stylebox("panel", "TooltipPanel", tip)
	th.set_color("font_color", "TooltipLabel", PARCHMENT)
	_theme = th
	return th


static func _circle_icon(c: Color) -> Texture2D:
	var img := Image.create(22, 22, false, Image.FORMAT_RGBA8)
	for y in 22:
		for x in 22:
			var d := Vector2(x - 10.5, y - 10.5).length()
			var a := clampf(10.5 - d, 0.0, 1.0)
			var col := c if d < 8.0 else BRASS_DARK
			img.set_pixel(x, y, Color(col, a))
	return ImageTexture.create_from_image(img)


## Anchor a control to a preset point of its parent and offset it from that point.
## Bottom/right anchored controls grow up/left so they stay on screen.
static func anchor(c: Control, preset: int, offset: Vector2) -> void:
	c.set_anchors_and_offsets_preset(preset)
	var w := c.custom_minimum_size.x
	var h := c.custom_minimum_size.y
	c.offset_left = offset.x
	c.offset_top = offset.y
	c.offset_right = offset.x + w
	c.offset_bottom = offset.y + h
	if preset in [Control.PRESET_BOTTOM_LEFT, Control.PRESET_BOTTOM_RIGHT, Control.PRESET_CENTER_BOTTOM, Control.PRESET_BOTTOM_WIDE]:
		c.grow_vertical = Control.GROW_DIRECTION_BEGIN
	if preset in [Control.PRESET_TOP_RIGHT, Control.PRESET_BOTTOM_RIGHT, Control.PRESET_CENTER_RIGHT]:
		c.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	if preset in [Control.PRESET_CENTER_TOP, Control.PRESET_CENTER_BOTTOM, Control.PRESET_CENTER]:
		c.grow_horizontal = Control.GROW_DIRECTION_BOTH


## Label helper with font / size / colour / outline.
static func label(text: String, size: int = 20, color: Color = INK, font_kind: String = "ui", outline: int = 0, outline_color: Color = Color(0, 0, 0, 0.7)) -> Label:
	var l := Label.new()
	l.text = text
	var f: Font = ui_font()
	if font_kind == "display":
		f = display_font()
	elif font_kind == "body":
		f = body_font()
	if f:
		l.add_theme_font_override("font", f)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if outline > 0:
		l.add_theme_constant_override("outline_size", outline)
		l.add_theme_color_override("font_outline_color", outline_color)
	return l
