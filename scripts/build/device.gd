class_name Device
extends Node3D
## Behaviour attached to a functional part (wheel, thruster, rotor, seat, lamp, turret...).

const CHANNELS := ["auto", "forward", "back", "left", "right", "up", "down", "fire", "always", "off"]
const CHANNEL_NAMES := {
	"auto": "Auto", "forward": "Forward (W)", "back": "Back (S)", "left": "Left (A)", "right": "Right (D)",
	"up": "Up (Space)", "down": "Down (Ctrl)", "fire": "Fire (LMB)", "always": "Always on", "off": "Off",
}

var part: Part
var contraption: Contraption
var binding: String = "auto"
var enabled: bool = true


static func create(kind: String) -> Device:
	match kind:
		"wheel":
			return WheelDevice.new()
		"thruster":
			return ThrusterDevice.new()
		"rotor":
			return RotorDevice.new()
		"hover":
			return HoverDevice.new()
		"seat":
			return SeatDevice.new()
		"lamp":
			return LampDevice.new()
		"spring":
			return SpringDevice.new()
		"ward":
			return WardDevice.new()
		"explosive":
			return ExplosiveDevice.new()
		"turret_arcane", "turret_rivet":
			var t := TurretDevice.new()
			t.style = "arcane" if kind == "turret_arcane" else "rivet"
			return t
	return null


func on_attached(c: Contraption) -> void:
	contraption = c


func on_detached() -> void:
	contraption = null


## Called every physics frame by the contraption.
func physics_step(_delta: float, _ctl: Dictionary, _piloted: bool) -> void:
	pass


func on_recomputed() -> void:
	pass


func on_destroyed() -> void:
	pass


func supports_binding() -> bool:
	return false


func cycle_binding(dir: int = 1) -> void:
	var i := CHANNELS.find(binding)
	binding = CHANNELS[wrapi(i + dir, 0, CHANNELS.size())]


func binding_name() -> String:
	return CHANNEL_NAMES.get(binding, binding)


func describe() -> String:
	var s := part.display_name()
	if supports_binding():
		s += "  ·  key: " + binding_name()
	if not enabled:
		s += "  ·  OFF"
	return s


func toggle() -> void:
	enabled = not enabled


## Channel value 0..1 for the current pilot input.
func channel_value(ch: String, ctl: Dictionary) -> float:
	var thr: float = ctl.get("throttle", 0.0)
	var st: float = ctl.get("steer", 0.0)
	var lf: float = ctl.get("lift", 0.0)
	match ch:
		"forward":
			return maxf(thr, 0.0)
		"back":
			return maxf(-thr, 0.0)
		"left":
			return maxf(-st, 0.0)
		"right":
			return maxf(st, 0.0)
		"up":
			return maxf(lf, 0.0)
		"down":
			return maxf(-lf, 0.0)
		"fire":
			return 1.0 if ctl.get("fire", false) else 0.0
		"always":
			return 1.0
	return 0.0


func save_data() -> Dictionary:
	return {"b": binding, "e": enabled}


func load_data(d: Dictionary) -> void:
	binding = str(d.get("b", binding))
	enabled = bool(d.get("e", true))
