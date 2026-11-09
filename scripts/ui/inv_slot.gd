class_name InvSlot
extends PanelContainer
## One inventory / loadout slot: icon, rarity frame, count and key badges. Supports drag & drop; the
## owning menu decides what a slot holds and what may be dropped on it (see InventoryMenu).

signal clicked(slot: InvSlot, button: int, double: bool)
signal hovered(slot: InvSlot)

var menu: Object = null          # receives drag_data_for / can_drop_on / drop_on
var payload: Dictionary = {}     # {"type": "weapon"|"item"|"loadout"|"quick"|"tool"|"empty", ...}
var size_px: float = 76.0
var selected: bool = false

var _icon: TextureRect
var _frame: Panel
var _count: Label
var _key: Label
var _badge: Label
var _fallback: Label


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_NONE


func _ready() -> void:
	custom_minimum_size = Vector2(size_px, size_px)
	var tex := UIStyle.tex("ui_slot_selected" if selected else "ui_slot")
	if tex:
		var sbt := StyleBoxTexture.new()
		sbt.texture = tex
		sbt.set_content_margin_all(maxf(6.0, size_px * 0.1))
		add_theme_stylebox_override("panel", sbt)
	else:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.1, 0.09, 0.14, 0.85)
		sb.border_color = UIStyle.TEAL if selected else UIStyle.BRASS_DARK
		sb.set_border_width_all(3 if selected else 2)
		sb.set_corner_radius_all(10)
		sb.set_content_margin_all(6)
		add_theme_stylebox_override("panel", sb)
	mouse_entered.connect(func(): hovered.emit(self))


## Fill the slot. rarity < 0 hides the frame. dim greys the icon (e.g. empty stacks, locked tools).
func setup(icon: Texture2D, label_text: String = "", rarity: int = -1, count_text: String = "", key_text: String = "",
		badge: String = "", dim: bool = false, tip: String = "") -> InvSlot:
	var holder := Control.new()
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(holder)
	if rarity >= 0:
		_frame = Panel.new()
		var fs := StyleBoxFlat.new()
		var rc := Catalog.rarity_color(rarity)
		fs.bg_color = Color(rc, 0.16)
		fs.border_color = rc
		fs.set_border_width_all(3)
		fs.set_corner_radius_all(9)
		_frame.add_theme_stylebox_override("panel", fs)
		_frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		_frame.offset_left = -3
		_frame.offset_top = -3
		_frame.offset_right = 3
		_frame.offset_bottom = 3
		_frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(_frame)
	if icon:
		_icon = TextureRect.new()
		_icon.texture = icon
		_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		_icon.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		if dim:
			_icon.modulate = Color(0.55, 0.55, 0.6, 0.75)
		holder.add_child(_icon)
	elif label_text != "":
		_fallback = UIStyle.label(label_text, int(size_px * 0.2), Color(1, 1, 1, 0.55 if dim else 0.9), "ui", 4, Color(0, 0, 0, 0.7))
		_fallback.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_fallback.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		_fallback.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_fallback.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		_fallback.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(_fallback)
	if count_text != "":
		_count = UIStyle.label(count_text, 15, Color.WHITE, "ui", 4, Color(0, 0, 0, 0.95))
		_count.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		_count.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
		_count.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		_count.offset_right = 2
		_count.offset_bottom = 4
		_count.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(_count)
	if key_text != "":
		_key = UIStyle.label(key_text, 14, UIStyle.GOLD, "ui", 4, Color(0, 0, 0, 0.9))
		_key.position = Vector2(-3, -7)
		_key.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(_key)
	if badge != "":
		_badge = UIStyle.label(badge, 12, Color("ffe8a0"), "ui", 4, Color(0.15, 0.05, 0.05, 0.95))
		_badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		_badge.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
		_badge.offset_top = -6
		_badge.offset_right = 2
		_badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(_badge)
	tooltip_text = tip
	return self


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		var mb := event as InputEventMouseButton
		if mb.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
			clicked.emit(self, mb.button_index, mb.double_click)
			accept_event()


func _get_drag_data(_at_position: Vector2) -> Variant:
	if menu == null or not menu.has_method("drag_data_for"):
		return null
	var data: Variant = menu.drag_data_for(self)
	if data == null:
		return null
	var prev := TextureRect.new()
	prev.texture = _icon.texture if _icon else null
	prev.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	prev.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	prev.custom_minimum_size = Vector2(size_px, size_px) * 0.9
	prev.size = prev.custom_minimum_size
	prev.modulate = Color(1, 1, 1, 0.85)
	var c := Control.new()
	c.add_child(prev)
	prev.position = -prev.size * 0.5
	set_drag_preview(c)
	return data


func _can_drop_data(_at_position: Vector2, data: Variant) -> bool:
	return menu != null and menu.has_method("can_drop_on") and bool(menu.can_drop_on(self, data))


func _drop_data(_at_position: Vector2, data: Variant) -> void:
	if menu and menu.has_method("drop_on"):
		menu.drop_on(self, data)
