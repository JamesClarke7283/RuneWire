class_name QuestNav
## Works out where the player should head for a quest (for the compass marker).

const KILL_AREAS := {
	"wisp": "woods", "wraith": "woods", "cultist": "shrine", "golem": "shrine", "archon": "shrine",
	"drone": "foundry", "crawler": "foundry", "sentry": "foundry", "ironclad": "foundry",
	"faction:magic": "shrine", "faction:tech": "foundry",
}
const ITEM_AREAS := {"ember_essence": "woods", "scrap_gear": "foundry", "rune_shard": "shrine"}


static func area_pos(area: String) -> Vector3:
	match area:
		"woods":
			var w: Vector2 = WorldLayout.WOODS["pos"]
			return Vector3(w.x, 0, w.y)
	if WorldLayout.POIS.has(area):
		var p: Vector2 = WorldLayout.POIS[area]["pos"]
		return Vector3(p.x, 0, p.y)
	if WorldLayout.LEY_STONES.has(area):
		var l: Vector2 = WorldLayout.LEY_STONES[area]
		return Vector3(l.x, 0, l.y)
	return Vector3.ZERO


static func npc_pos(tree: SceneTree, npc_id: String) -> Variant:
	if npc_id == "board":
		return Vector3(9, 6, 13)
	for n in tree.get_nodes_in_group("npcs"):
		if n.npc_id == npc_id:
			return n.global_position
	return null


static func target_for(q: String, tree: SceneTree) -> Variant:
	var d := Quests.def(q)
	if d.is_empty():
		return null
	if Quests.status(q) == "ready":
		return npc_pos(tree, d["turn_in"])
	for i in d["objectives"].size():
		if Quests.objective_done(q, i):
			continue
		var o: Dictionary = d["objectives"][i]
		var t: String = o.get("target", "")
		match o["type"]:
			"reach":
				if t == "shrine_altar":
					return area_pos("shrine")
				if t == "watchtower":
					return area_pos("watchtower")
				return area_pos(t)
			"kill":
				return area_pos(KILL_AREAS.get(t, "foundry"))
			"collect":
				return area_pos(ITEM_AREAS.get(t, "town"))
			"deliver":
				if Quests.is_active("q_cargo"):
					for c in tree.get_nodes_in_group("contraptions"):
						for p in (c as Contraption).parts:
							if p.part_id == "cargo":
								var player := tree.get_first_node_in_group("player") as Player
								if player and player.global_position.distance_to(p.global_position) > 12.0:
									return p.global_position
				return area_pos("watchtower")
			"challenge":
				var w := tree.get_first_node_in_group("world")
				if w and w.pois and w.pois.challenges.has(t):
					return (w.pois.challenges[t] as Node3D).global_position
				return null
			"talk":
				return npc_pos(tree, t)
	return null
