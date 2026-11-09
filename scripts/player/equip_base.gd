class_name EquipBase
extends Node
## Base class for hotbar equipment (tools, spells, weapons).

var player: Player
var id: String = ""
var data: Dictionary = {}
var active: bool = false


func on_equip() -> void:
	active = true


func on_unequip() -> void:
	active = false


func primary(_pressed: bool) -> void:
	pass


func secondary(_pressed: bool) -> void:
	pass


func reload() -> void:
	pass


## Return true when the scroll wheel was consumed (otherwise it switches hotbar slots).
func scroll(_dir: int) -> bool:
	return false


## Return true when mouse motion was consumed (e.g. rotating a held object).
func mouse_motion(_rel: Vector2) -> bool:
	return false


func tick(_delta: float) -> void:
	pass


## Control hints shown above the hotbar.
func hint() -> String:
	return ""


## Short status (ammo, mode) shown next to the hotbar.
func status() -> String:
	return ""


func aim_info() -> String:
	return ""
