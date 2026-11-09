class_name OutlineOverlay
extends MeshInstance3D
## Full-screen quad that draws the screen-space cartoon outlines. Add as a child of a Camera3D.

const SHADER := preload("res://shaders/outline_post.gdshader")

var material: ShaderMaterial


func _ready() -> void:
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	q.flip_faces = true
	mesh = q
	material = ShaderMaterial.new()
	material.shader = SHADER
	material.render_priority = 10
	material_override = material
	extra_cull_margin = 16384.0
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	position = Vector3(0, 0, -0.5)
	_apply_settings()
	if Engine.has_singleton("Settings") or has_node("/root/Settings"):
		get_node("/root/Settings").changed.connect(_apply_settings)


func _apply_settings() -> void:
	var s := get_node_or_null("/root/Settings")
	visible = s == null or s.outlines
	if s:
		material.set_shader_parameter("thickness", 1.0 if s.render_scale < 0.9 else 1.25)
