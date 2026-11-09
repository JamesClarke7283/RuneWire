class_name Water
extends MeshInstance3D
## The lake: a subdivided plane at water level with the stylised water shader.

func setup(center: Vector2, size: float) -> void:
	var pm := PlaneMesh.new()
	pm.size = Vector2(size, size)
	pm.subdivide_width = 48
	pm.subdivide_depth = 48
	mesh = pm
	position = Vector3(center.x, WorldLayout.WATER_LEVEL, center.y)
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/water.gdshader")
	var noise: Texture2D = MaterialLib.texture("res://assets/textures/fx/noise_perlin.png")
	if noise == null:
		var nt := NoiseTexture2D.new()
		nt.seamless = true
		nt.width = 256
		nt.height = 256
		var fn := FastNoiseLite.new()
		fn.frequency = 0.03
		nt.noise = fn
		noise = nt
	m.set_shader_parameter("noise_tex", noise)
	var nrm: Texture2D = MaterialLib.texture("res://assets/textures/water/water_normal.png")
	if nrm:
		m.set_shader_parameter("normal_tex", nrm)
		m.set_shader_parameter("has_normal_tex", true)
	material_override = m
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
