class_name ChallengeMenu
extends MenuPanel
## Challenge terminal: description, medal thresholds and rewards, best result, start.

var challenge_id: String = ""
var runner: ChallengeRunner


func _init() -> void:
	panel_size = Vector2(900, 600)


func build() -> void:
	var d := Challenges.def(challenge_id)
	set_title(d["name"])
	content.add_child(MenuPanel.rich(d["desc"], 20))
	var medals := HBoxContainer.new()
	medals.alignment = BoxContainer.ALIGNMENT_CENTER
	medals.add_theme_constant_override("separation", 26)
	content.add_child(medals)
	var claimed := int(Challenges.claimed.get(challenge_id, 0))
	for i in 3:
		var v := VBoxContainer.new()
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		var circle := PanelContainer.new()
		var sb := StyleBoxFlat.new()
		sb.bg_color = Challenges.MEDAL_COLORS[i + 1] if claimed > i else Color(0, 0, 0, 0.15)
		sb.border_color = Challenges.MEDAL_COLORS[i + 1]
		sb.set_border_width_all(4)
		sb.set_corner_radius_all(40)
		circle.add_theme_stylebox_override("panel", sb)
		circle.custom_minimum_size = Vector2(80, 80)
		var ml := UIStyle.label(["B", "S", "G"][i], 34, UIStyle.INK, "display")
		ml.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		ml.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		circle.add_child(ml)
		circle.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		v.add_child(circle)
		var l := UIStyle.label("%s\n%s\n%d gold" % [Challenges.MEDAL_NAMES[i + 1], Challenges.format_value(challenge_id, float(d["medals"][i])), int(d["rewards"][i])], 17, UIStyle.INK, "ui")
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(l)
		medals.add_child(v)
	var best_txt := "No attempts yet."
	if Challenges.best.has(challenge_id):
		best_txt = "Personal best: %s (%s)" % [Challenges.format_value(challenge_id, Challenges.best[challenge_id]), Challenges.MEDAL_NAMES[Challenges.best_medal(challenge_id)]]
	var bl := UIStyle.label(best_txt + "   ·   Repeat medals pay 25%.", 18, Color("5a4632"), "body")
	bl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	content.add_child(bl)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_child(spacer)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 16)
	content.add_child(row)
	var busy := Challenges.running != "" and Challenges.running != challenge_id
	row.add_child(MenuPanel.button("Start challenge!" if not busy else "Another challenge is running", func():
		var r := runner
		closed.emit()
		if r:
			r.start.call_deferred(), 280, busy or runner == null))
	row.add_child(MenuPanel.button("Not now", func(): closed.emit(), 160))
