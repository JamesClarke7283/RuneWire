class_name EquipBase
extends Node
## Base class for hotbar equipment (tools, spells, guns, melee). Weapons get `data` = the final
## stats of their weapon instance (Catalog.weapon_stats), tools their Catalog.TOOLS entry.

var player: Player
var id: String = ""        # weapon base / tool id
var uid: int = 0           # weapon instance uid (0 for tools)
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


## Ammo / readiness fill 0..1 for the hotbar slot meter (-1 = no meter).
func meter() -> float:
	return -1.0


## A DamageInfo from the player that carries this weapon's stats (for perks and kill tracking).
func hit(amount: float, dmg_type: String, pos: Vector3, dir: Vector3, knock: float = 1.0) -> DamageInfo:
	return DamageInfo.make(amount, dmg_type, player, pos, dir, knock, true).with_weapon(data)
