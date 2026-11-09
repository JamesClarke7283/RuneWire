class_name ArenaChallenge
extends ChallengeRunner
## Arena of Echoes: endless waves of conjured magic and tech foes. Each cleared wave pays gold.

var center: Vector3 = Vector3.ZERO
var radius: float = 28.0
var wave: int = 0
var cleared: int = 0
var alive: Array = []
var _between: float = 0.0
var _outside_t: float = 0.0
var _portals: Array = []


func _ready() -> void:
	super._ready()
	challenge_id = "arena"
	time_limit = 0.0


func _begin() -> void:
	wave = 0
	cleared = 0
	alive.clear()
	_between = 3.0
	objective = "Get ready..."
	Events.toast("The crowd roars! Wave 1 incoming...", "quest")


func status_text() -> String:
	if _between > 0.0:
		return "Wave %d in %d  ·  Cleared: %d" % [wave + 1, int(ceil(_between)), cleared]
	return "Wave %d  ·  Foes left: %d  ·  Cleared: %d" % [wave, alive.size(), cleared]


func _wave_kinds(n: int) -> Array:
	var magic := ["wisp", "wisp", "cultist", "wraith"]
	var tech := ["drone", "crawler", "crawler", "drone"]
	var kinds := []
	var count := 2 + n
	for i in count:
		var pool := magic if (i + n) % 2 == 0 else tech
		kinds.append(pool[randi() % pool.size()])
	if n >= 4:
		kinds.append("golem" if n % 2 == 0 else "crawler")
	if n >= 7:
		kinds.append("wraith")
		kinds.append("drone")
	if n % 5 == 0:
		kinds.append("golem")
	return kinds


func _spawn_wave() -> void:
	wave += 1
	objective = "Wave %d" % wave
	AudioManager.play_2d("quest_accept", -4.0, 0.8)
	Events.toast("Wave %d!" % wave, "warn")
	var kinds := _wave_kinds(wave)
	for i in kinds.size():
		var a := TAU * float(i) / kinds.size() + randf() * 0.4
		var p := center + Vector3(cos(a), 0, sin(a)) * radius * 0.75
		p.y = _world.ground_y(p.x, p.z) + (3.0 if Catalog.enemy(kinds[i]).get("flying", false) else 0.3)
		VFX.ring(self, p, Color(0.7, 0.5, 1.0), 2.5, 0.6)
		VFX.sparkle(self, p, Color(1.0, 0.8, 0.4), 10, 0.3)
		var e := Enemy.spawn(kinds[i], _world, p)
		if e:
			e.home = center
			e.leash = radius + 15.0
			e.aggro = true
			alive.append(e)


func _tick(delta: float) -> void:
	alive = alive.filter(func(e): return is_instance_valid(e) and not e.dead)
	var p := player()
	if p:
		var d := Vector2(p.global_position.x - center.x, p.global_position.z - center.z).length()
		if d > radius + 8.0:
			_outside_t += delta
			if _outside_t > 6.0:
				_end()
				return
		else:
			_outside_t = 0.0
	if _between > 0.0:
		_between -= delta
		if _between <= 0.0:
			_spawn_wave()
		return
	if alive.is_empty():
		cleared = wave
		var gold := 15 * wave
		Game.add_gold(gold, "Arena wave %d cleared" % wave)
		_between = 5.0
		if wave >= 12:
			_end()


func _end() -> void:
	complete(float(cleared))


func _on_player_died() -> void:
	_end()


func abort(reason: String = "") -> void:
	if cleared > 0 and running:
		_end()
		return
	super.abort(reason)


func _cleanup() -> void:
	for e in alive:
		if is_instance_valid(e) and not e.dead:
			VFX.puffs(self, e.aim_point(), Color(0.6, 0.5, 0.8), 6, 0.6, 0.8, 1.0)
			e.queue_free()
	alive.clear()
