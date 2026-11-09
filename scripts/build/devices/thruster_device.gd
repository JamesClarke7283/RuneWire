class_name ThrusterDevice
extends Device
## Pushes the contraption toward the thruster's front (+Z). Fires on its key channel.

var force: float = 2600.0
var _flame: MeshInstance3D
var _particles: GPUParticles3D
var _light: OmniLight3D
var _snd: AudioStreamPlayer3D
var _level: float = 0.0
var _exhaust: Node3D


func supports_binding() -> bool:
	return true


func _ready() -> void:
	force = float(part.def.get("force", 2600.0))
	_exhaust = part.model.find_child("Exhaust", true, false) as Node3D
	var ex_pos := Vector3(0, 0, -0.5)
	if _exhaust:
		ex_pos = part.to_local(_exhaust.global_position)
	var holder := Node3D.new()
	holder.position = ex_pos
	add_child(holder)
	_flame = MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.0
	cm.bottom_radius = 0.17
	cm.height = 0.9
	cm.radial_segments = 10
	_flame.mesh = cm
	_flame.material_override = VFX.glow_mat(Color(1.0, 0.62, 0.25), 4.0)
	_flame.rotation = Vector3(-PI / 2, 0, 0)
	_flame.position = Vector3(0, 0, -0.45)
	_flame.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_flame.visible = false
	holder.add_child(_flame)
	_particles = GPUParticles3D.new()
	_particles.amount = 24
	_particles.lifetime = 0.5
	_particles.emitting = false
	_particles.local_coords = false
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3(0, 0, -1)
	pm.spread = 12.0
	pm.initial_velocity_min = 4.0
	pm.initial_velocity_max = 7.0
	pm.gravity = Vector3(0, 1.5, 0)
	pm.scale_min = 0.25
	pm.scale_max = 0.45
	VFX._curves()
	pm.scale_curve = VFX._grow_curve
	pm.color = Color(0.85, 0.85, 0.9)
	_particles.process_material = pm
	_particles.draw_pass_1 = VFX._puff_mesh
	_particles.material_override = VFX.puff_mat()
	holder.add_child(_particles)
	_light = OmniLight3D.new()
	_light.light_color = Color(1.0, 0.6, 0.3)
	_light.light_energy = 0.0
	_light.omni_range = 5.0
	holder.add_child(_light)
	_snd = AudioManager.attach_loop(self, "thruster_loop", -80.0, 7.0)


func on_recomputed() -> void:
	if binding == "auto":
		pass


func resolved_channel() -> String:
	if binding != "auto":
		return binding
	if contraption == null:
		return "off"
	var b := contraption.pilot_basis()
	var push := part.global_transform.basis.z.normalized()
	var f := push.dot(b.z)
	var u := push.dot(b.y)
	var r := push.dot(-b.x)
	var m := maxf(absf(f), maxf(absf(u), absf(r)))
	if m == absf(u):
		return "up" if u > 0 else "down"
	if m == absf(f):
		return "forward" if f > 0 else "back"
	return "right" if r > 0 else "left"


func describe() -> String:
	var s := part.display_name() + "  ·  key: " + binding_name()
	if binding == "auto":
		s += " → " + CHANNEL_NAMES.get(resolved_channel(), "")
	return s + ("" if enabled else "  ·  OFF")


func physics_step(delta: float, ctl: Dictionary, piloted: bool) -> void:
	var ch := resolved_channel()
	var v := 0.0
	if piloted or ch == "always":
		v = channel_value(ch, ctl)
	if ctl.get("boost", false):
		v *= 1.5
	_level = lerpf(_level, v, 1.0 - exp(-10.0 * delta))
	if v > 0.01 and contraption:
		var dir := part.global_transform.basis.z.normalized()
		contraption.apply_force(dir * force * v, part.global_position - contraption.global_position)
	var on := _level > 0.05
	_flame.visible = on
	_flame.scale = Vector3(1.0, 1.0, 1.0) * clampf(_level, 0.0, 1.5) * randf_range(0.85, 1.15)
	_particles.emitting = on
	_light.light_energy = _level * 2.5
	if _snd:
		_snd.volume_db = linear_to_db(clampf(_level, 0.0001, 1.0)) - 2.0
		_snd.pitch_scale = 0.8 + _level * 0.4
