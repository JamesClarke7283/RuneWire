extends Node
## Global signal bus. Gameplay systems emit here; quests, challenges, UI and audio listen.

signal enemy_killed(enemy_type: String, faction: String, position: Vector3)
signal enemy_damaged(enemy: Node, amount: float, position: Vector3, damage_type: String)
signal item_collected(item_id: String, count: int)
signal location_reached(location_id: String)
signal npc_talked(npc_id: String)
signal part_spawned(part_id: String, part: Node)
signal part_purchased(part_id: String, count: int)
signal item_purchased(item_id: String)
signal parts_welded(contraption: Node)
signal contraption_driven(contraption: Node, meters: float)
signal contraption_altitude(contraption: Node, altitude: float)
signal contraption_built(contraption: Node, tags: Array)
signal cargo_delivered(cargo_id: String, zone_id: String)
signal challenge_started(challenge_id: String)
signal challenge_finished(challenge_id: String, result: Dictionary)
signal notify(text: String, kind: String)
signal player_damaged(amount: float, damage_type: String)
signal player_died()
signal player_respawned()
signal game_started(new_game: bool)
signal menu_opened(menu_name: String)
signal menu_closed(menu_name: String)
signal boss_started(boss: Node, display_name: String)
signal boss_ended(boss: Node)
signal screen_shake(strength: float, duration: float)


func toast(text: String, kind: String = "info") -> void:
	notify.emit(text, kind)
