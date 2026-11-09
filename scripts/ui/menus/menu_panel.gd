class_name MenuPanel
extends Control
## Base for modal menus: dimmed backdrop, centred parchment panel, title and close button.

signal closed

var panel: PanelContainer
var content: VBoxContainer
var title_label: Label
var panel_size: Vector2 = Vector2(1100, 700)
var title_text: String = ""
var dark: bool = false


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var dim := ColorRect.new()
	dim.color = Color(0.04, 0.03, 0.08, 0.55)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	panel = PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UIStyle.panel_box(dark, 22))
	panel.custom_minimum_size = panel_size
	UIStyle.anchor(panel, Control.PRESET_CENTER, -panel_size / 2.0)
	add_child(panel)
	var outer := VBoxContainer.new()
	outer.add_theme_constant_override("separation", 12)
	panel.add_child(outer)
	var head := HBoxContainer.new()
	outer.add_child(head)
	title_label = UIStyle.label(title_text, 38, UIStyle.INK if not dark else UIStyle.GOLD, "display", 0)
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(title_label)
	var close := Button.new()
	close.text = "✕"
	close.custom_minimum_size = Vector2(48, 44)
	close.pressed.connect(func(): closed.emit())
	head.add_child(close)
	var sep := HSeparator.new()
	var line := StyleBoxLine.new()
	line.color = Color(UIStyle.BRASS_DARK, 0.6)
	line.thickness = 2
	sep.add_theme_stylebox_override("separator", line)
	outer.add_child(sep)
	content = VBoxContainer.new()
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 10)
	outer.add_child(content)
	panel.scale = Vector2(0.92, 0.92)
	panel.pivot_offset = panel_size / 2.0
	panel.modulate.a = 0.0
	var tw := create_tween().set_parallel(true)
	tw.tween_property(panel, "scale", Vector2.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(panel, "modulate:a", 1.0, 0.12)
	build()


## Subclasses fill `content` here.
func build() -> void:
	pass


func set_title(t: String) -> void:
	title_text = t
	if title_label:
		title_label.text = t


func clear_content() -> void:
	for c in content.get_children():
		c.queue_free()


static func button(text: String, cb: Callable, min_w: float = 0.0, disabled: bool = false) -> Button:
	var b := Button.new()
	b.text = text
	b.disabled = disabled
	if min_w > 0.0:
		b.custom_minimum_size.x = min_w
	b.pressed.connect(func():
		AudioManager.play_ui("ui_click")
		cb.call())
	b.mouse_entered.connect(func(): AudioManager.play_ui("ui_hover", -14.0))
	return b


static func rich(text: String, size: int = 19) -> RichTextLabel:
	var r := RichTextLabel.new()
	r.bbcode_enabled = true
	r.fit_content = true
	r.scroll_active = false
	r.text = text
	r.add_theme_font_size_override("normal_font_size", size)
	r.add_theme_font_size_override("bold_font_size", size + 2)
	var f := UIStyle.ui_font()
	if f:
		r.add_theme_font_override("bold_font", f)
	r.add_theme_color_override("default_color", UIStyle.INK)
	return r


static func coin_price(price: int, affordable: bool = true) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 4)
	var tex := UIStyle.tex("ui_coin")
	if tex:
		var tr := TextureRect.new()
		tr.texture = tex
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.custom_minimum_size = Vector2(22, 22)
		h.add_child(tr)
	var l := UIStyle.label(str(price) if price > 0 else "Free", 19, Color("8a5a10") if affordable else Color("b03a2e"), "ui")
	h.add_child(l)
	return h


static func icon_rect(tex: Texture2D, sz: float) -> Control:
	if tex == null:
		var c := ColorRect.new()
		c.color = Color(0, 0, 0, 0.08)
		c.custom_minimum_size = Vector2(sz, sz)
		return c
	var tr := TextureRect.new()
	tr.texture = tex
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.custom_minimum_size = Vector2(sz, sz)
	return tr


## Card for a purchasable thing (part / spell / weapon / consumable / upgrade).
static func card(icon: Texture2D, name: String, desc: String, price: int, extra: String, buttons: Array, locked_text: String = "") -> PanelContainer:
	var pc := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(1, 1, 1, 0.35)
	sb.border_color = Color(UIStyle.BRASS_DARK, 0.5)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(10)
	sb.set_content_margin_all(10)
	pc.add_theme_stylebox_override("panel", sb)
	pc.custom_minimum_size = Vector2(240, 0)
	pc.tooltip_text = desc
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	pc.add_child(v)
	var ic := icon_rect(icon, 104)
	ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	if locked_text != "":
		ic.modulate = Color(0.3, 0.3, 0.35, 0.8)
	v.add_child(ic)
	var nl := UIStyle.label(name, 20, UIStyle.INK, "ui")
	nl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	nl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(nl)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 12)
	if price >= 0:
		row.add_child(coin_price(price, Game.can_afford(price)))
	if extra != "":
		row.add_child(UIStyle.label(extra, 16, Color("4a3a2a"), "body"))
	v.add_child(row)
	if locked_text != "":
		var ll := UIStyle.label("🔒 " + locked_text, 15, Color("7a2a2a"), "body")
		ll.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		ll.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(ll)
	else:
		var br := HBoxContainer.new()
		br.alignment = BoxContainer.ALIGNMENT_CENTER
		br.add_theme_constant_override("separation", 6)
		for b in buttons:
			br.add_child(b)
		v.add_child(br)
	return pc
