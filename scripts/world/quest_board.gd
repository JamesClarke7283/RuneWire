class_name QuestBoard
extends Node3D
## The Emberwick bounty board: repeatable bounties for gold.


func _ready() -> void:
	var body := StaticBody3D.new()
	body.collision_layer = 32
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = Vector3(2.6, 2.4, 0.9)
	cs.shape = bs
	cs.position = Vector3(0, 1.3, 0)
	body.add_child(cs)
	add_child(body)


func get_interact_text() -> String:
	var ready := Quests.ready_for("board").size()
	return "[E] Read the Bounty Board" + ("  (%d to turn in!)" % ready if ready > 0 else "")


func interact(_player: Player) -> void:
	var ui := get_tree().get_first_node_in_group("game_ui")
	if ui:
		ui.open_board()
