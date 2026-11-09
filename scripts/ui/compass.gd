class_name Compass
extends Control
## Heading strip with cardinal points and a marker for the tracked quest objective.

var player: Player
var target: Variant = null   # Vector3 or null

const FOV_DEG := 160.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _process(_delta: float) -> void:
	queue_redraw()


func _heading() -> float:
	if player == null:
		return 0.0
	if player.piloting and player.third_person:
		return -player.chase_yaw
	return -player.yaw


func _draw() -> void:
	var w := size.x
	var h := size.y
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.07, 0.07, 0.12, 0.6)
	bg.border_color = Color(0.85, 0.65, 0.3, 0.7)
	bg.set_border_width_all(2)
	bg.set_corner_radius_all(10)
	draw_style_box(bg, Rect2(Vector2.ZERO, size))
	var font := UIStyle.ui_font()
	var heading := rad_to_deg(_heading())   # 0 = facing -Z (north)
	var labels := {0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW"}
	for deg in range(0, 360, 15):
		var rel := wrapf(float(deg) - heading, -180.0, 180.0)
		if absf(rel) > FOV_DEG / 2.0:
			continue
		var x := w * 0.5 + rel / (FOV_DEG / 2.0) * (w * 0.5 - 14.0)
		if labels.has(deg):
			var txt: String = labels[deg]
			var fs := 20 if txt.length() == 1 else 14
			var col := UIStyle.GOLD if txt == "N" else UIStyle.PARCHMENT
			var tw := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x if font else 10.0
			if font:
				draw_string(font, Vector2(x - tw / 2.0, h * 0.68), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)
		else:
			draw_line(Vector2(x, h * 0.3), Vector2(x, h * 0.62), Color(1, 1, 1, 0.35), 2.0)
	if target is Vector3 and player:
		var d: Vector3 = (target as Vector3) - player.global_position
		var bearing := rad_to_deg(atan2(d.x, -d.z))
		var rel2 := wrapf(bearing - heading, -180.0, 180.0)
		var clamped := clampf(rel2, -FOV_DEG / 2.0, FOV_DEG / 2.0)
		var x2 := w * 0.5 + clamped / (FOV_DEG / 2.0) * (w * 0.5 - 14.0)
		var pts := PackedVector2Array([Vector2(x2, h - 4), Vector2(x2 - 9, h - 18), Vector2(x2 + 9, h - 18)])
		draw_colored_polygon(pts, UIStyle.TEAL)
		draw_circle(Vector2(x2, h - 24), 6.0, UIStyle.GOLD)
		var dist := Vector2(d.x, d.z).length()
		if font:
			var t := "%dm" % int(dist)
			draw_string(font, Vector2(x2 + 12, h - 18), t, HORIZONTAL_ALIGNMENT_LEFT, -1, 13, UIStyle.TEAL)
	draw_line(Vector2(w * 0.5, 2), Vector2(w * 0.5, 9), UIStyle.GOLD, 3.0)
