class_name EnvironmentRig
extends Node3D
## Sun/moon, painted sky, fog, glow and the day/night cycle. Quality presets scale effects.

signal night_changed(is_night: bool)

const DAY_SECONDS := 1080.0   # one full day (nights pass twice as fast)

var world_env: WorldEnvironment
var env: Environment
var sun: DirectionalLight3D
var sky_mat: ShaderMaterial
var night: float = 0.0
var is_night: bool = false
var paused_time: bool = false

const PALETTES := {
	"day": {"top": Color("3f7fe0"), "horizon": Color("b4dcff"), "ground": Color("5b6b80"), "sun": Color(1.0, 0.96, 0.86), "fog": Color("b9d4f2"), "cloud_l": Color(1, 1, 1), "cloud_s": Color("9fb0d8"), "ambient": 0.55},
	"sunset": {"top": Color("4a5cb8"), "horizon": Color("ffb27a"), "ground": Color("5b4d63"), "sun": Color(1.0, 0.72, 0.45), "fog": Color("e7b39b"), "cloud_l": Color("ffd2a8"), "cloud_s": Color("a87ea8"), "ambient": 0.45},
	"night": {"top": Color("0b1030"), "horizon": Color("26305e"), "ground": Color("101320"), "sun": Color(0.6, 0.7, 1.0), "fog": Color("1d2547"), "cloud_l": Color("4a5480"), "cloud_s": Color("232a4a"), "ambient": 0.32},
}


func _ready() -> void:
	add_to_group("environment_rig")
	world_env = WorldEnvironment.new()
	env = Environment.new()
	world_env.environment = env
	add_child(world_env)
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	sky_mat = ShaderMaterial.new()
	sky_mat.shader = load("res://shaders/sky.gdshader")
	var clouds: Texture2D = MaterialLib.texture("res://assets/textures/fx/noise_clouds.png")
	if clouds == null:
		var nt := NoiseTexture2D.new()
		nt.width = 512
		nt.height = 512
		nt.seamless = true
		var fn := FastNoiseLite.new()
		fn.frequency = 0.012
		fn.fractal_octaves = 4
		nt.noise = fn
		clouds = nt
	sky_mat.set_shader_parameter("cloud_noise", clouds)
	sky.sky_material = sky_mat
	sky.process_mode = Sky.PROCESS_MODE_INCREMENTAL
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.ambient_light_sky_contribution = 1.0
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_white = 6.0
	env.tonemap_exposure = 1.05
	env.glow_enabled = true
	env.glow_intensity = 0.55
	env.glow_bloom = 0.04
	env.glow_hdr_threshold = 1.1
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	# only two blur levels: plenty for cartoon glows and much cheaper on iGPUs
	for i in 7:
		env.set_glow_level(i, 0.0)
	env.set_glow_level(2, 1.0)
	env.set_glow_level(4, 0.8)
	env.fog_enabled = true
	env.fog_density = 0.0016
	env.fog_aerial_perspective = 0.35
	env.fog_sky_affect = 0.0
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.12
	env.adjustment_contrast = 1.04
	sun = DirectionalLight3D.new()
	sun.name = "Sun"
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	sun.directional_shadow_max_distance = 110.0
	sun.directional_shadow_split_1 = 0.25
	sun.directional_shadow_blend_splits = false
	sun.shadow_bias = 0.04
	sun.shadow_normal_bias = 1.4
	sun.light_angular_distance = 0.4
	add_child(sun)
	Settings.changed.connect(apply_quality)
	apply_quality()
	update_time(0.0)


func apply_quality() -> void:
	var q: int = Settings.quality
	env.ssao_enabled = q >= Settings.Quality.MEDIUM
	env.ssao_radius = 1.2
	env.ssao_intensity = 1.5
	env.ssao_light_affect = 0.12
	env.ssil_enabled = false
	env.sdfgi_enabled = false
	env.volumetric_fog_enabled = q >= Settings.Quality.HIGH
	env.volumetric_fog_density = 0.006
	env.volumetric_fog_length = 80.0
	env.volumetric_fog_gi_inject = 0.0
	env.ssr_enabled = false
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS if q < Settings.Quality.HIGH else DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 90.0 if q == Settings.Quality.LOW else (120.0 if q == Settings.Quality.MEDIUM else 180.0)


func _process(delta: float) -> void:
	if paused_time or get_tree().paused:
		return
	var speed := 1.0 / DAY_SECONDS
	if night > 0.5:
		speed *= 2.0
	var t := Game.time_of_day + delta * speed
	if t >= 1.0 and Game.started:
		Game.day += 1          # a new day: vendors restock their featured wares
	Game.time_of_day = fmod(t, 1.0)
	update_time(delta)


func update_time(_delta: float) -> void:
	var t := Game.time_of_day
	var ang := (t - 0.25) * TAU     # 0 at sunrise, PI/2 at noon
	var elev := sin(ang)            # -1..1
	var day_w := smoothstep(-0.08, 0.18, elev)
	var sunset_w := (1.0 - absf(elev) / 0.35) if absf(elev) < 0.35 else 0.0
	night = 1.0 - smoothstep(-0.2, 0.02, elev)
	var pal_day: Dictionary = PALETTES["day"]
	var pal_set: Dictionary = PALETTES["sunset"]
	var pal_night: Dictionary = PALETTES["night"]
	var c_top: Color = pal_night["top"].lerp(pal_day["top"], day_w).lerp(pal_set["top"], sunset_w * 0.6)
	var c_hor: Color = pal_night["horizon"].lerp(pal_day["horizon"], day_w).lerp(pal_set["horizon"], sunset_w * 0.85)
	var c_gnd: Color = pal_night["ground"].lerp(pal_day["ground"], day_w).lerp(pal_set["ground"], sunset_w * 0.5)
	var c_sun: Color = pal_night["sun"].lerp(pal_day["sun"], day_w).lerp(pal_set["sun"], sunset_w)
	var c_fog: Color = pal_night["fog"].lerp(pal_day["fog"], day_w).lerp(pal_set["fog"], sunset_w * 0.7)
	sky_mat.set_shader_parameter("top_color", c_top)
	sky_mat.set_shader_parameter("horizon_color", c_hor)
	sky_mat.set_shader_parameter("ground_color", c_gnd)
	sky_mat.set_shader_parameter("sun_color", c_sun)
	sky_mat.set_shader_parameter("night", night)
	sky_mat.set_shader_parameter("cloud_light", (pal_night["cloud_l"] as Color).lerp(pal_day["cloud_l"], day_w).lerp(pal_set["cloud_l"], sunset_w * 0.7))
	sky_mat.set_shader_parameter("cloud_shadow", (pal_night["cloud_s"] as Color).lerp(pal_day["cloud_s"], day_w).lerp(pal_set["cloud_s"], sunset_w * 0.7))
	# The directional light follows the sun by day and a soft moon by night.
	var azimuth := deg_to_rad(-35.0) + (t - 0.5) * 0.6
	var light_elev := elev
	var moon := false
	if elev < -0.05:
		light_elev = 0.55
		azimuth += PI
		moon = true
	var pitch := -asin(clampf(absf(light_elev), 0.12, 1.0))
	sun.rotation = Vector3(pitch, azimuth, 0.0)
	if moon:
		sun.light_color = Color(0.62, 0.72, 1.0)
		sun.light_energy = lerpf(0.35, 0.0, smoothstep(-0.05, -0.12, -elev - 0.1)) + 0.25
		sky_mat.set_shader_parameter("moon_dir", sun.global_transform.basis.z)
	else:
		sun.light_color = c_sun
		sun.light_energy = lerpf(0.4, 1.35, smoothstep(0.0, 0.35, elev))
	# dip the light around the sun/moon hand-over so the shadow flip is not noticeable
	sun.light_energy *= lerpf(0.15, 1.0, smoothstep(0.0, 0.07, absf(elev + 0.05)))
	env.ambient_light_energy = lerpf(float(pal_night["ambient"]), float(pal_day["ambient"]), day_w)
	env.fog_light_color = c_fog
	env.fog_light_energy = lerpf(0.6, 1.0, day_w)
	env.tonemap_exposure = lerpf(1.25, 1.05, day_w)
	var now_night := night > 0.55
	if now_night != is_night:
		is_night = now_night
		night_changed.emit(is_night)
		get_tree().call_group("night_lights", "set_night", is_night)


func set_time(t: float) -> void:
	Game.time_of_day = t
	update_time(0.0)
