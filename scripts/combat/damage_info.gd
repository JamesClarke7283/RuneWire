class_name DamageInfo
extends RefCounted
## A single hit: amount, damage type (arcane, fire, shock, kinetic), where it came from.

var amount: float = 0.0
var damage_type: String = "kinetic"
var source: Node = null
var position: Vector3 = Vector3.ZERO
var direction: Vector3 = Vector3.ZERO
var knockback: float = 0.0
var from_player: bool = false


static func make(p_amount: float, p_type: String = "kinetic", p_source: Node = null, p_position: Vector3 = Vector3.ZERO,
		p_direction: Vector3 = Vector3.ZERO, p_knockback: float = 0.0, p_from_player: bool = false) -> DamageInfo:
	var d := DamageInfo.new()
	d.amount = p_amount
	d.damage_type = p_type
	d.source = p_source
	d.position = p_position
	d.direction = p_direction
	d.knockback = p_knockback
	d.from_player = p_from_player
	return d


func copy() -> DamageInfo:
	return DamageInfo.make(amount, damage_type, source, position, direction, knockback, from_player)
