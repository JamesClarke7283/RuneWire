class_name InfoPopup
extends MenuPanel
## Simple popup: title, rich text body, one button. Optional medal badge.

var body_text: String = ""
var button_text: String = "OK"
var medal: int = -1


func _init() -> void:
	panel_size = Vector2(900, 640)


func build() -> void:
	set_title(title_text)
	if medal >= 0:
		var circle := PanelContainer.new()
		var sb := StyleBoxFlat.new()
		sb.bg_color = Challenges.MEDAL_COLORS[medal]
		sb.border_color = UIStyle.BRASS_DARK
		sb.set_border_width_all(4)
		sb.set_corner_radius_all(48)
		circle.add_theme_stylebox_override("panel", sb)
		circle.custom_minimum_size = Vector2(96, 96)
		circle.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		var l := UIStyle.label(["—", "B", "S", "G"][medal], 44, UIStyle.INK, "display")
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		circle.add_child(l)
		content.add_child(circle)
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	content.add_child(sc)
	var r := MenuPanel.rich(body_text, 20)
	r.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(r)
	var b := MenuPanel.button(button_text, func(): closed.emit(), 260)
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	b.custom_minimum_size.y = 54
	content.add_child(b)
