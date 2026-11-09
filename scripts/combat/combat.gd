class_name Combat
## Damage routing, explosions and shared combat helpers.

const MASK_WORLD := 1
const MASK_PLAYER := 2
const MASK_PARTS := 4
const MASK_ENEMIES := 8
const MASK_DEBRIS := 128

const TYPE_COLORS := {
	"arcane": Color(0.72, 0.5, 1.0),
	"fire": Color(1.0, 0.6, 0.2),
	"shock": Color(0.45, 0.9, 1.0),
	"kinetic": Color(1.0, 0.92, 0.7),
	"frost": Color(0.6, 0.9, 1.0),
	"none": Color(1, 1, 1),
}


## Deliver damage to whatever was hit (ray/shape result `hit` or a node).
static func damage_hit(hit: Dictionary, info: DamageInfo) -> bool:
	if hit.is_empty():
		return false
	var col: Object = hit.get("collider")
	if col is Contraption:
		var part: Part = (col as Contraption).part_from_shape(int(hit.get("shape", 0)))
		if part:
			part.apply_damage(info)
			return true
		return false
	return damage_node(col, info)


static func damage_node(n: Object, info: DamageInfo) -> bool:
	var node := n as Node
	var depth := 0
	while node and depth < 5:
		if node.has_method("apply_damage"):
			node.apply_damage(info)
			return true
		node = node.get_parent()
		depth += 1
	return false


static func is_enemy(n: Object) -> bool:
	var node := n as Node
	return node != null and node.is_in_group("enemies")


## Area damage with linear falloff, physics impulses and the explosion effect.
static func explode(ctx: Node3D, pos: Vector3, radius: float, damage: float, dmg_type: String, source: Node = null,
		from_player: bool = false, hurt_player: bool = true, visual_scale: float = 1.0, weapon: Dictionary = {},
		is_proc: bool = false) -> void:
	var space := ctx.get_world_3d().direct_space_state
	var shape := SphereShape3D.new()
	shape.radius = radius
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = shape
	q.transform = Transform3D(Basis(), pos)
	q.collision_mask = MASK_PLAYER | MASK_PARTS | MASK_ENEMIES | MASK_DEBRIS
	var results := space.intersect_shape(q, 48)
	var done := {}
	for r in results:
		var col: Object = r["collider"]
		var key := str(col.get_instance_id()) + ":" + str(r.get("shape", 0)) if col is Contraption else str(col.get_instance_id())
		if done.has(key):
			continue
		done[key] = true
		var cpos: Vector3 = (col as Node3D).global_position
		if col is Contraption:
			var part: Part = (col as Contraption).part_from_shape(int(r.get("shape", 0)))
			if part:
				cpos = part.global_position
		var dist := cpos.distance_to(pos)
		var fall := clampf(1.0 - dist / radius, 0.15, 1.0)
		var dir := (cpos - pos).normalized()
		if dir.length_squared() < 0.01:
			dir = Vector3.UP
		if col is Player:
			if not hurt_player:
				continue
			var pi := DamageInfo.make(damage * fall * (0.5 if from_player else 1.0), dmg_type, source, pos, dir + Vector3.UP * 0.4, 9.0 * fall)
			(col as Player).apply_damage(pi)
			continue
		var info := DamageInfo.make(damage * fall, dmg_type, source, pos, dir, 6.0 * fall, from_player)
		info.weapon = weapon
		info.proc = is_proc
		if col is Contraption:
			var c := col as Contraption
			var part2: Part = c.part_from_shape(int(r.get("shape", 0)))
			if part2:
				part2.apply_damage(info)
			if is_instance_valid(c) and not c.freeze:
				c.apply_impulse((dir + Vector3.UP * 0.5).normalized() * c.mass * 7.0 * fall, cpos - c.global_position)
		elif col is RigidBody3D:
			(col as RigidBody3D).apply_central_impulse((dir + Vector3.UP * 0.5).normalized() * (col as RigidBody3D).mass * 8.0 * fall)
			damage_node(col, info)
		else:
			damage_node(col, info)
	VFX.explosion(ctx, pos, radius * visual_scale, TYPE_COLORS.get(dmg_type, Color(1, 0.6, 0.2)))
	AudioManager.play("explosion_big" if radius >= 4.5 else "explosion_fire", pos, 2.0 if radius >= 4.5 else 0.0, 1.0, 0.1, 14.0)
	var pl := ctx.get_tree().get_first_node_in_group("player") as Player
	if pl:
		var d := pl.global_position.distance_to(pos)
		if d < radius * 5.0:
			pl.shake(clampf(1.0 - d / (radius * 5.0), 0.1, 1.0) * 0.9, 0.4)


## Closest enemy to a point within range (optionally requiring line of sight from `from`).
static func nearest_enemy(ctx: Node3D, pos: Vector3, max_range: float, need_los: bool = true, exclude: Array = []) -> Node3D:
	var best: Node3D = null
	var best_d := max_range
	for e in ctx.get_tree().get_nodes_in_group("enemies"):
		if not is_instance_valid(e) or e in exclude or e.get("dead"):
			continue
		var n := e as Node3D
		var aim: Vector3 = n.aim_point() if n.has_method("aim_point") else n.global_position
		var d := aim.distance_to(pos)
		if d < best_d:
			if need_los and not has_los(ctx, pos, aim, [n]):
				continue
			best_d = d
			best = n
	return best


static func has_los(ctx: Node3D, from: Vector3, to: Vector3, ignore: Array = []) -> bool:
	var q := PhysicsRayQueryParameters3D.create(from, to, MASK_WORLD)
	var ex: Array[RID] = []
	for i in ignore:
		if i is CollisionObject3D:
			ex.append(i.get_rid())
	q.exclude = ex
	var hit := ctx.get_world_3d().direct_space_state.intersect_ray(q)
	return hit.is_empty()
