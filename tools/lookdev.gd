extends SceneTree
## Look-development render: builds a small test scene with the cartoon environment, the
## crate model and library materials, then saves a screenshot.
## Usage: godot --path . --script res://tools/lookdev.gd -- /tmp/lookdev.png

var frames := 0
var out_path := "/tmp/rw_lookdev.png"
var cam: Camera3D


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out_path = args[0]
	var root3d := Node3D.new()
	root.add_child.call_deferred(root3d)
	await process_frame
	var ml: Node = root.get_node("MaterialLib")
	var env := WorldEnvironment.new()
	env.environment = make_env()
	root3d.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.light_color = Color(1.0, 0.95, 0.85)
	sun.light_energy = 1.35
	sun.shadow_enabled = true
	sun.rotation_degrees = Vector3(-42, -35, 0)
	root3d.add_child(sun)
	# ground
	var ground := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(80, 80)
	pm.subdivide_depth = 8
	pm.subdivide_width = 8
	ground.mesh = pm
	var tm := ShaderMaterial.new()
	tm.shader = load("res://shaders/terrain.gdshader")
	var noise_tex := NoiseTexture2D.new()
	noise_tex.seamless = true
	noise_tex.noise = FastNoiseLite.new()
	tm.set_shader_parameter("macro_noise", noise_tex)
	ground.material_override = tm
	root3d.add_child(ground)
	# crate model
	var crate: Node3D = ml.instance_model("res://assets/models/parts/part_crate.glb")
	if crate:
		crate.position = Vector3(0, 0.5, 0)
		root3d.add_child(crate)
		var c2: Node3D = ml.instance_model("res://assets/models/parts/part_crate.glb")
		c2.position = Vector3(1.15, 0.5, 0.3)
		c2.rotation_degrees.y = 20
		root3d.add_child(c2)
		var c3: Node3D = ml.instance_model("res://assets/models/parts/part_crate.glb")
		c3.position = Vector3(0.5, 1.5, 0.1)
		c3.rotation_degrees.y = -12
		root3d.add_child(c3)
	var names := ["M_Brass", "M_PaintedMetal", "M_Fabric__8a2be2", "M_RuneGlow", "M_Glass", "M_Steel", "M_Crystal", "M_Leather"]
	for i in names.size():
		var mi := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.45
		sm.height = 0.9
		mi.mesh = sm
		mi.material_override = ml.get_named(names[i])
		mi.position = Vector3(-4.0 + i * 1.1, 0.45, 2.2)
		root3d.add_child(mi)
	var cap := MeshInstance3D.new()
	cap.mesh = CapsuleMesh.new()
	cap.material_override = ml.get_named("M_Skin")
	cap.position = Vector3(-2.2, 1.0, -0.5)
	root3d.add_child(cap)
	cam = Camera3D.new()
	cam.fov = 70
	root3d.add_child(cam)
	cam.look_at_from_position(Vector3(-1.2, 2.6, 6.2), Vector3(-0.6, 0.7, 0.6))
	var ol := OutlineOverlay.new()
	cam.add_child(ol)
	process_frame.connect(_on_frame)


func make_env() -> Environment:
	var e := Environment.new()
	e.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sm := ShaderMaterial.new()
	sm.shader = load("res://shaders/sky.gdshader")
	var nt := NoiseTexture2D.new()
	nt.width = 512
	nt.height = 512
	nt.seamless = true
	var fn := FastNoiseLite.new()
	fn.frequency = 0.012
	fn.fractal_octaves = 4
	nt.noise = fn
	sm.set_shader_parameter("cloud_noise", nt)
	sky.sky_material = sm
	e.sky = sky
	e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	e.ambient_light_energy = 0.55
	e.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	e.tonemap_white = 6.0
	e.tonemap_exposure = 1.05
	e.glow_enabled = true
	e.glow_intensity = 0.55
	e.glow_bloom = 0.04
	e.glow_hdr_threshold = 1.1
	e.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	e.ssao_enabled = true
	e.ssao_radius = 1.2
	e.ssao_intensity = 1.6
	e.ssao_light_affect = 0.15
	e.fog_enabled = true
	e.fog_light_color = Color(0.72, 0.83, 0.98)
	e.fog_density = 0.0025
	e.fog_aerial_perspective = 0.4
	e.fog_sky_affect = 0.0
	e.adjustment_enabled = true
	e.adjustment_saturation = 1.12
	e.adjustment_contrast = 1.04
	return e


func _on_frame() -> void:
	frames += 1
	if frames == 30:
		var img := root.get_viewport().get_texture().get_image()
		img.save_png(out_path)
		print("LOOKDEV saved ", out_path)
		quit()
