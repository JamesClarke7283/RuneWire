class_name EnemySpawner
extends Node3D
## Keeps a population of enemies around a point (or fixed points), respawning them over time.
## Spawns out of the player's immediate view and only within a sensible range of the player.

var spawner_id: String = ""
var center: Vector2 = Vector2.ZERO
var radius: float = 30.0
var types: Dictionary = {}
var max_alive: int = 4
var respawn_time: float = 30.0
var condition: Callable = Callable()
var fixed_points: Array = []
var level: int = 1              # area level of the foes it spawns (see Enemy.level)
var world: World

var alive: Array = []
var _timer: float = 2.0
var _used_points: Dictionary = {}


func _process(delta: float) -> void:
	if not Game.started:
		return
	_timer -= delta
	if _timer > 0.0:
		return
	_timer = 1.5
	if condition.is_valid() and not bool(condition.call()):
		return
	alive = alive.filter(func(e): return is_instance_valid(e) and not e.dead)
	if alive.size() >= max_alive:
		return
	var player := get_tree().get_first_node_in_group("player") as Player
	if player == null:
		return
	var pdist := Vector2(player.global_position.x, player.global_position.z).distance_to(center)
	if pdist > 170.0:
		return
	if _respawn_wait > 0.0:
		_respawn_wait -= 1.5
		return
	_spawn_one(player)


var _respawn_wait: float = 0.0


## Champions (elites) start appearing once the apprentice has finished their first job.
func _roll_elite() -> bool:
	return Quests.is_done("q_arrival") and randf() < Catalog.ELITE_CHANCE


func _pick_type() -> String:
	var total := 0.0
	for k in types:
		total += float(types[k])
	var r := randf() * total
	for k in types:
		r -= float(types[k])
		if r <= 0.0:
			return k
	return types.keys()[0]


func _spawn_one(player: Player) -> void:
	var k := _pick_type()
	var pos2: Vector2
	if not fixed_points.is_empty():
		var free_points := []
		for i in fixed_points.size():
			if not _used_points.has(i) or not is_instance_valid(_used_points[i]) or _used_points[i].dead:
				free_points.append(i)
		if free_points.is_empty():
			return
		var idx: int = free_points[randi() % free_points.size()]
		pos2 = fixed_points[idx]
		var e0 := Enemy.spawn(k, world, world.ground_point(pos2.x, pos2.y, 0.1), _roll_elite(), level)
		if e0:
			_used_points[idx] = e0
			_register(e0)
		return
	for attempt in 6:
		var a := randf() * TAU
		var r := sqrt(randf()) * radius
		pos2 = center + Vector2(cos(a), sin(a)) * r
		var p3 := world.ground_point(pos2.x, pos2.y)
		if p3.y < 0.5:
			continue
		if p3.distance_to(player.global_position) < 18.0:
			continue
		var flying := bool(Catalog.enemy(k).get("flying", false))
		var e := Enemy.spawn(k, world, p3 + Vector3.UP * (3.0 if flying else 0.3), _roll_elite(), level)
		if e:
			_register(e)
		return


func _register(e: Enemy) -> void:
	e.spawner = self
	e.home = e.global_position
	e.leash = maxf(radius + 25.0, 40.0)
	alive.append(e)


func on_enemy_died(_e: Enemy) -> void:
	_respawn_wait = respawn_time
