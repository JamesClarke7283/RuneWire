class_name HoverDevice
extends Device
## Levitation stone: holds its contraption at a hover height (see Contraption._flight) and glows.

var _particles: GPUParticles3D
var _light: OmniLight3D
var _snd: AudioStreamPlayer3D
var _t: float = 0.0


func _ready() -> void:
	_t = randf() * 10.0
	_particles = GPUParticles3D.new()
	_particles.amount = 10
	_particles.lifetime = 1.4
	_particles.local_coords = false
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = 0.4
	pm.direction = Vector3.DOWN
	pm.spread = 30.0
	pm.initial_velocity_min = 0.3
	pm.initial_velocity_max = 0.9
	pm.gravity = Vector3(0, -0.6, 0)
	pm.scale_min = 0.12
	pm.scale_max = 0.22
	VFX._curves()
	pm.scale_curve = VFX._scale_curve
	pm.color = Color(0.65, 0.45, 1.0)
	_particles.process_material = pm
	_particles.draw_pass_1 = VFX._quad
	_particles.material_override = VFX.additive_mat("vfx_spark")
	add_child(_particles)
	_light = OmniLight3D.new()
	_light.light_color = Color(0.65, 0.45, 1.0)
	_light.light_energy = 0.8
	_light.omni_range = 3.5
	_light.position = Vector3(0, -0.4, 0)
	add_child(_light)
	_snd = AudioManager.attach_loop(self, "hover_loop", -14.0, 4.0)


func _process(delta: float) -> void:
	_t += delta
	if _light:
		_light.light_energy = 0.7 + sin(_t * 2.4) * 0.25
