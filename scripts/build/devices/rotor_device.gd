class_name RotorDevice
extends Device
## Lift rotor: spins up when piloted and provides lift through the contraption's flight assist.

var _blades: Node3D
var _spin_speed: float = 0.0
var _snd: AudioStreamPlayer3D


func _ready() -> void:
	_blades = part.model.find_child("Blades", true, false) as Node3D
	_snd = AudioManager.attach_loop(self, "rotor_loop", -80.0, 9.0)


func physics_step(delta: float, ctl: Dictionary, piloted: bool) -> void:
	var target := 0.0
	if piloted:
		target = 22.0 + float(ctl.get("lift", 0.0)) * 8.0
	_spin_speed = lerpf(_spin_speed, target, 1.0 - exp(-2.0 * delta))
	if _blades:
		_blades.rotate_object_local(Vector3.UP, _spin_speed * delta)
	if _snd:
		var lvl := clampf(_spin_speed / 26.0, 0.0001, 1.0)
		_snd.volume_db = linear_to_db(lvl) - 1.0
		_snd.pitch_scale = 0.6 + lvl * 0.6
