class_name ExplosiveDevice
extends Device
## Volatile mana barrel: explodes when destroyed. Chain reactions encouraged.

var _exploded: bool = false


func on_destroyed() -> void:
	if _exploded:
		return
	_exploded = true
	var pos := part.global_position
	var ctx := get_tree().get_first_node_in_group("vfx_root") as Node3D
	if ctx == null:
		ctx = part
	# defer so the destroyed part is gone before neighbours are damaged
	var tree := get_tree()
	tree.create_timer(0.05).timeout.connect(func():
		Combat.explode(ctx, pos, 6.5, 90.0, "fire", null, false, true, 1.2))
