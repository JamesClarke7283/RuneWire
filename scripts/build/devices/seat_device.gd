class_name SeatDevice
extends Device
## Pilot seat: press E to sit and drive everything welded to it.


func interact(player: Player) -> void:
	if contraption == null:
		return
	if contraption.pilot and contraption.pilot != player:
		return
	player.sit(part)
	AudioManager.play("tool_configure", part.global_position, -4.0, 0.8)


func get_interact_text() -> String:
	if contraption and contraption.pilot:
		return ""
	return "[E] Sit in Pilot Seat"
