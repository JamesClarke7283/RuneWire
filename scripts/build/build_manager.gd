class_name BuildManager
extends Node3D
## Spawns, welds, detaches and dismantles parts; enforces the part limit; keeps the undo stack;
## saves and restores every placed contraption.

signal placed_changed(count: int, limit: int)

var placed_count: int = 0
var undo_stack: Array = []


func _ready() -> void:
	add_to_group("build_manager")
	SaveSystem.register_provider("build", serialize)


## Rebuild saved contraptions (called once the save game has been loaded).
func restore() -> void:
	var data: Variant = SaveSystem.take_pending("build")
	if data is Dictionary:
		deserialize(data)


func _exit_tree() -> void:
	SaveSystem.unregister_provider("build")


func limit() -> int:
	return Game.part_limit()


func _changed() -> void:
	placed_changed.emit(placed_count, limit())


# ------------------------------------------------------------------ spawning
func new_contraption(at: Vector3) -> Contraption:
	var c := Contraption.new()
	c.name = "Contraption"
	add_child(c)
	c.global_position = at
	return c


## Spawn a part the player owns at a transform. Consumes one from the inventory.
func spawn_part(part_id: String, xform: Transform3D, consume: bool = true) -> Part:
	var special := Part.SPECIAL.has(part_id)
	if not special:
		if placed_count >= limit():
			Events.toast("Part limit reached (%d). Dismantle something or buy a Workshop Permit." % limit(), "warn")
			AudioManager.play_ui("ui_error")
			return null
		if consume and not Game.take_part(part_id):
			Events.toast("You don't own any %s. Buy some in the Build Catalog [Q]." % Catalog.display_name(part_id), "warn")
			AudioManager.play_ui("ui_error")
			return null
	var part := Part.create(part_id)
	var c := new_contraption(xform.origin)
	c.add_part(part, xform)
	if not special:
		placed_count += 1
		undo_stack.append(weakref(part))
		Events.part_spawned.emit(part_id, part)
		Game.add_stat("parts_spawned")
		_changed()
	VFX.burst(self, xform.origin, Color(0.45, 0.95, 0.9), 14, 3.0, 0.25, 0.6, 2.0, "star")
	AudioManager.play("tool_spawn", xform.origin, -2.0)
	return part


## Where a part would spawn for the player's crosshair (resting on the surface, facing the player).
func placement_for(part_id: String, player: Player) -> Transform3D:
	var def := Catalog.part(part_id)
	if def.is_empty():
		def = Part.SPECIAL.get(part_id, {})
	var half := _half_extents(def)
	var hit := player.aim_ray(14.0, 1 | 4)
	var yaw := player.yaw + PI
	var basis := Basis(Vector3.UP, yaw)
	var pos: Vector3
	if hit:
		var n: Vector3 = hit["normal"]
		var extent := absf((basis * Vector3(half.x, 0, 0)).dot(n)) + absf((basis * Vector3(0, half.y, 0)).dot(n)) + absf((basis * Vector3(0, 0, half.z)).dot(n))
		pos = (hit["position"] as Vector3) + n * (extent + 0.02)
	else:
		pos = player.camera.global_position - player.camera.global_transform.basis.z * 6.0
	return Transform3D(basis, pos)


func _half_extents(def: Dictionary) -> Vector3:
	var sd: Dictionary = def.get("shape", {"type": "box", "size": Vector3.ONE})
	if sd.get("type", "box") == "cylinder":
		var r := float(sd["radius"])
		var h := float(sd["height"]) * 0.5
		match sd.get("axis", "y"):
			"x":
				return Vector3(h, r, r)
			"z":
				return Vector3(r, r, h)
		return Vector3(r, h, r)
	return (sd.get("size", Vector3.ONE) as Vector3) * 0.5


func spawn_for_player(part_id: String, player: Player) -> Part:
	return spawn_part(part_id, placement_for(part_id, player))


# ------------------------------------------------------------------ editing
func weld(a: Part, b: Part) -> bool:
	if a == null or b == null or a == b or a.contraption == null or b.contraption == null:
		return false
	if a.contraption == b.contraption:
		Events.toast("Those parts are already welded together", "info")
		return false
	var ca := a.contraption
	var cb := b.contraption
	if ca.pilot or cb.pilot:
		Events.toast("Can't weld while someone is piloting", "warn")
		return false
	var big := ca if ca.parts.size() >= cb.parts.size() else cb
	var small := cb if big == ca else ca
	var mid := (a.global_position + b.global_position) * 0.5
	big.merge_from(small)
	VFX.weld_sparks(self, mid)
	AudioManager.play("tool_weld", mid, 0.0)
	Events.parts_welded.emit(big)
	Game.add_stat("welds")
	return true


func detach(part: Part) -> bool:
	var c := part.contraption
	if c == null or c.parts.size() <= 1:
		return false
	var lv := c.linear_velocity
	var xf := part.global_transform
	var was_frozen := c.freeze
	c.remove_part(part, true)
	var nc := new_contraption(xf.origin)
	nc.add_part(part, xf)
	nc.freeze = was_frozen
	nc.linear_velocity = lv
	AudioManager.play("tool_remove", xf.origin, -4.0, 1.3)
	VFX.burst(self, xf.origin, Color(1.0, 0.85, 0.5), 8, 3.0, 0.1, 0.4, -9.0, "spark")
	return true


## Remove a part and return it to the inventory.
func dismantle(part: Part) -> void:
	if part == null or not is_instance_valid(part):
		return
	var pos := part.global_position
	if part.special:
		Events.toast("That cargo can't be dismantled!", "warn")
		return
	var c := part.contraption
	if c:
		c.remove_part(part, false)
	Game.add_parts(part.part_id, 1)
	placed_count = maxi(0, placed_count - 1)
	part.queue_free()
	VFX.burst(self, pos, Color(0.45, 0.95, 0.9), 10, 2.5, 0.22, 0.5, 2.0, "star")
	AudioManager.play("tool_remove", pos, -2.0)
	_changed()


func dismantle_contraption(c: Contraption) -> void:
	if c == null:
		return
	if c.pilot:
		c.pilot.exit_seat()
	for p in c.parts.duplicate():
		if p.special:
			continue
		dismantle(p)


func undo() -> void:
	while not undo_stack.is_empty():
		var ref: WeakRef = undo_stack.pop_back()
		var p := ref.get_ref() as Part
		if p and is_instance_valid(p) and p.is_inside_tree():
			dismantle(p)
			Events.toast("Undo: removed %s" % p.display_name(), "info")
			return
	Events.toast("Nothing to undo", "info")


func on_part_destroyed(part: Part) -> void:
	if part.special:
		return
	placed_count = maxi(0, placed_count - 1)
	Events.toast("%s was destroyed!" % part.display_name(), "warn")
	_changed()


func contraptions() -> Array:
	var out := []
	for c in get_children():
		if c is Contraption and not c.is_queued_for_deletion():
			out.append(c)
	return out


# ------------------------------------------------------------------ save / load
func serialize() -> Dictionary:
	var list := []
	for c in contraptions():
		var cc := c as Contraption
		var parts := []
		for p in cc.parts:
			if p.special:
				continue
			parts.append(p.to_dict(cc))
		if parts.is_empty():
			continue
		list.append({"x": Part._xf_to_arr(cc.global_transform), "frozen": cc.freeze, "hover": cc.hover_height, "parts": parts})
	return {"contraptions": list}


func deserialize(data: Dictionary) -> void:
	for cd in data.get("contraptions", []):
		var body_xf := Part.arr_to_xf(cd["x"])
		var c := new_contraption(body_xf.origin)
		c.global_transform = body_xf
		for pd in cd.get("parts", []):
			var pid := str(pd["id"])
			if Catalog.part(pid).is_empty():
				continue
			var p := Part.create(pid)
			c.add_part(p, body_xf * Part.arr_to_xf(pd["x"]), false)
			p.hp = float(pd.get("hp", p.max_hp))
			if pd.has("paint"):
				p.set_paint(Color(str(pd["paint"])))
			if pd.has("dev") and p.device:
				p.device.load_data(pd["dev"])
			placed_count += 1
		if c.parts.is_empty():
			c.queue_free()
			continue
		c.recompute()
		c.hover_height = float(cd.get("hover", 2.5))
		c.freeze = bool(cd.get("frozen", false))
	_changed()
