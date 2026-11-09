class_name CargoZone
extends Area3D
## Delivery zone: completes when a contraption carrying the Ley Crystal cargo enters it.

signal delivered(contraption: Contraption)

var zone_id: String = ""
var radius: float = 5.0
var cargo_part: String = "cargo"


func _ready() -> void:
	collision_layer = 0
	collision_mask = 4
	var cs := CollisionShape3D.new()
	var s := SphereShape3D.new()
	s.radius = radius
	cs.shape = s
	add_child(cs)
	body_entered.connect(_on_body)


func _on_body(b: Node) -> void:
	if not (b is Contraption):
		return
	var c := b as Contraption
	for p in c.parts.duplicate():
		if p.part_id == cargo_part:
			if not Quests.is_active("q_cargo"):
				Events.toast("Odda hasn't asked for this delivery yet.", "info")
				return
			Events.cargo_delivered.emit(cargo_part, zone_id)
			delivered.emit(c)
			VFX.sparkle(self, p.global_position, Color(0.35, 0.95, 0.9), 40, 0.5)
			VFX.ring(self, global_position, Color(0.35, 0.95, 0.9), 7.0, 0.8)
			AudioManager.play_2d("quest_complete", -4.0)
			Events.toast("Ley Crystal delivered! The watchtower lamp blazes to life.", "quest")
			c.remove_part(p, false)
			p.queue_free()
			return
