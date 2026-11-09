class_name ToolkitTool
extends EquipBase
## Rune Toolkit. R cycles modes: Weld · Detach · Dismantle · Configure · Paint.

enum Mode { WELD, DETACH, DISMANTLE, CONFIGURE, PAINT }
const MODE_NAMES := ["Weld", "Detach", "Dismantle", "Configure", "Paint"]
const MODE_COLORS := [Color(1.0, 0.75, 0.3), Color(0.5, 0.85, 1.0), Color(1.0, 0.45, 0.4), Color(0.7, 0.55, 1.0), Color(0.5, 1.0, 0.6)]
const PALETTE := [Color.WHITE, Color("ff5a5f"), Color("ff9a3c"), Color("ffd84a"), Color("6fdc6a"), Color("39d5c4"),
	Color("4d8dff"), Color("9a66ff"), Color("ff7ad9"), Color("4a4a55"), Color("f4ecd8"), Color("a86a32")]
const RANGE := 26.0

var mode: int = Mode.WELD
var selected: Part = null
var paint_idx: int = 1


func on_unequip() -> void:
	_clear_selection()
	super.on_unequip()


func hint() -> String:
	match mode:
		Mode.WELD:
			return "LMB select part, then LMB another to weld · RMB clear · R next mode" if selected == null else "LMB the part to weld to · RMB cancel"
		Mode.DETACH:
			return "LMB detach a part from its contraption · R next mode"
		Mode.DISMANTLE:
			return "LMB dismantle part (returns to inventory) · RMB dismantle whole contraption · R next mode"
		Mode.CONFIGURE:
			return "LMB cycle key binding · RMB toggle on/off · R next mode"
		Mode.PAINT:
			return "LMB paint part (Shift: whole contraption) · RMB next colour · R next mode"
	return ""


func status() -> String:
	return "Mode: %s" % MODE_NAMES[mode]


func mode_color() -> Color:
	return PALETTE[paint_idx] if mode == Mode.PAINT else MODE_COLORS[mode]


func reload() -> void:
	mode = (mode + 1) % MODE_NAMES.size()
	_clear_selection()
	AudioManager.play_2d("tool_configure", -6.0, 1.0 + mode * 0.08)
	Events.toast("Toolkit: %s mode" % MODE_NAMES[mode], "tool")


func _aim_part() -> Dictionary:
	var hit := player.aim_ray(RANGE, 4)
	if hit and hit["collider"] is Contraption:
		var p := (hit["collider"] as Contraption).part_from_shape(hit["shape"])
		if p:
			return {"part": p, "pos": hit["position"]}
	return {}


func aim_info() -> String:
	var a := _aim_part()
	if a.is_empty():
		return ""
	var p: Part = a["part"]
	var s := p.device.describe() if p.device else p.display_name()
	s += "  ·  HP %d/%d" % [int(maxf(p.hp, 0)), int(p.max_hp)]
	if p.contraption:
		s += "  ·  " + p.contraption.describe()
	return s


func _zap(to: Vector3) -> void:
	VFX.beam(player, player.viewmodel.muzzle_position(), to, mode_color(), 0.025, 0.12)
	player.viewmodel.kick(0.02, 3.0)


func primary(pressed: bool) -> void:
	if not pressed:
		return
	var a := _aim_part()
	if a.is_empty():
		return
	var part: Part = a["part"]
	var bm := player._build_manager()
	_zap(a["pos"])
	match mode:
		Mode.WELD:
			if selected == null or not is_instance_valid(selected):
				selected = part
				MaterialLib.flash(part.model, 0.35)
				AudioManager.play_2d("tool_configure", -6.0, 1.2)
			elif selected == part:
				_clear_selection()
			else:
				var a_part := selected
				_clear_selection()
				if bm:
					bm.weld(a_part, part)
		Mode.DETACH:
			if bm and not bm.detach(part):
				Events.toast("That part isn't welded to anything", "info")
		Mode.DISMANTLE:
			if bm:
				bm.dismantle(part)
		Mode.CONFIGURE:
			if part.device and part.device.supports_binding():
				part.device.cycle_binding(1)
				Events.toast(part.device.describe(), "tool")
			elif part.device:
				part.device.toggle()
				Events.toast(part.device.describe(), "tool")
			else:
				Events.toast("%s has nothing to configure" % part.display_name(), "info")
			AudioManager.play("tool_configure", part.global_position, -4.0)
		Mode.PAINT:
			var col: Color = PALETTE[paint_idx]
			if Input.is_key_pressed(KEY_SHIFT) and part.contraption:
				for p in part.contraption.parts:
					p.set_paint(col)
			else:
				part.set_paint(col)
			VFX.burst(player, a["pos"], col, 10, 2.5, 0.18, 0.5, -4.0, "star")
			AudioManager.play("tool_spawn", a["pos"], -8.0, 1.4)


func secondary(pressed: bool) -> void:
	if not pressed:
		return
	match mode:
		Mode.WELD:
			_clear_selection()
		Mode.DISMANTLE:
			var a := _aim_part()
			if not a.is_empty():
				var bm := player._build_manager()
				if bm:
					bm.dismantle_contraption((a["part"] as Part).contraption)
		Mode.CONFIGURE:
			var a2 := _aim_part()
			if not a2.is_empty() and (a2["part"] as Part).device:
				(a2["part"] as Part).device.toggle()
				Events.toast((a2["part"] as Part).device.describe(), "tool")
		Mode.PAINT:
			paint_idx = (paint_idx + 1) % PALETTE.size()
			AudioManager.play_2d("ui_click", -6.0, 1.3)


func _clear_selection() -> void:
	if selected and is_instance_valid(selected):
		MaterialLib.flash(selected.model, 0.0)
	selected = null
