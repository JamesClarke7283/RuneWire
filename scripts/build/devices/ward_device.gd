class_name WardDevice
extends Device
## Ward pylon: a shimmering dome that destroys enemy projectiles entering it.

const DOME_SHADER := """
shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 color : source_color = vec4(0.35, 0.85, 1.0, 1.0);
uniform float pulse = 0.0;
void fragment() {
	float fres = pow(1.0 - abs(dot(NORMAL, VIEW)), 3.0);
	float bands = smoothstep(0.92, 1.0, sin(UV.y * 80.0 - TIME * 2.0) * 0.5 + 0.5) * 0.25;
	ALBEDO = color.rgb;
	ALPHA = clamp(fres * 0.65 + bands * fres + pulse * 0.4, 0.0, 1.0);
}
"""

var radius: float = 7.0
var dome: MeshInstance3D
var _mat: ShaderMaterial
var _crystal: Node3D
var _t: float = 0.0
static var _shader: Shader


func _ready() -> void:
	radius = float(part.def.get("radius", 7.0))
	add_to_group("wards")
	dome = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = radius
	sm.height = radius * 2.0
	sm.radial_segments = 32
	sm.rings = 16
	dome.mesh = sm
	if _shader == null:
		_shader = Shader.new()
		_shader.code = DOME_SHADER
	_mat = ShaderMaterial.new()
	_mat.shader = _shader
	dome.material_override = _mat
	dome.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(dome)
	_crystal = part.model.find_child("Crystal", true, false) as Node3D


func blocks(p: Vector3) -> bool:
	return enabled and contraption != null and p.distance_to(global_position) < radius


func on_block(_p: Vector3) -> void:
	_mat.set_shader_parameter("pulse", 1.0)
	AudioManager.play("spell_arcane_hit", _p, -6.0, 1.3)


func toggle() -> void:
	super.toggle()
	dome.visible = enabled


func _process(delta: float) -> void:
	_t += delta
	dome.visible = enabled and contraption != null
	var p: float = _mat.get_shader_parameter("pulse")
	if p > 0.0:
		_mat.set_shader_parameter("pulse", maxf(0.0, p - delta * 2.5))
	if _crystal:
		_crystal.rotation.y += delta * 1.2
		_crystal.position.y = sin(_t * 2.0) * 0.05
