extends Node
## Player settings (graphics, audio, controls) + the input map, persisted to user://settings.cfg.

signal changed

const PATH := "user://settings.cfg"

enum Quality { LOW, MEDIUM, HIGH }

var quality: int = Quality.MEDIUM
var render_scale: float = 1.0
var fullscreen: bool = false
var vsync: bool = true
var fov: float = 80.0
var mouse_sensitivity: float = 0.12
var invert_y: bool = false
var outlines: bool = true
var grass_density: float = 1.0
var show_fps: bool = false
var show_objective: bool = true   # the objective tracker under the compass
var volume_master: float = 0.9
var volume_music: float = 0.55
var volume_sfx: float = 0.85
var volume_ambience: float = 0.6

const ACTIONS := {
	"move_forward": [KEY_W, KEY_UP],
	"move_back": [KEY_S, KEY_DOWN],
	"move_left": [KEY_A, KEY_LEFT],
	"move_right": [KEY_D, KEY_RIGHT],
	"jump": [KEY_SPACE],
	"sprint": [KEY_SHIFT],
	"crouch": [KEY_CTRL, KEY_C],
	"interact": [KEY_E],
	"reload": [KEY_R],
	"slot_1": [KEY_1],
	"slot_2": [KEY_2],
	"slot_3": [KEY_3],
	"slot_4": [KEY_4],
	"slot_5": [KEY_5],
	"slot_6": [KEY_6],
	"slot_7": [KEY_7],
	"slot_8": [KEY_8],
	"spawn_menu": [KEY_Q],
	"inventory": [KEY_I],
	"quick_swap": [KEY_X],
	"crafting": [KEY_B],
	"talents": [KEY_K],
	"map": [KEY_M],
	"quest_log": [KEY_J],
	"character": [KEY_TAB],
	"pause": [KEY_ESCAPE],
	"undo": [KEY_Z],
	"use_health": [KEY_H],
	"use_mana": [KEY_G],
	"toggle_view": [KEY_V],
	"lights": [KEY_F],
}
const MOUSE_ACTIONS := {
	"primary": MOUSE_BUTTON_LEFT,
	"secondary": MOUSE_BUTTON_RIGHT,
	"next_slot": MOUSE_BUTTON_WHEEL_DOWN,
	"prev_slot": MOUSE_BUTTON_WHEEL_UP,
}


func _enter_tree() -> void:
	_register_input()
	load_settings()


func _ready() -> void:
	apply()


func _register_input() -> void:
	for action in ACTIONS:
		if not InputMap.has_action(action):
			InputMap.add_action(action, 0.2)
		for key in ACTIONS[action]:
			var ev := InputEventKey.new()
			ev.physical_keycode = key
			InputMap.action_add_event(action, ev)
	for action in MOUSE_ACTIONS:
		if not InputMap.has_action(action):
			InputMap.add_action(action, 0.2)
		var mb := InputEventMouseButton.new()
		mb.button_index = MOUSE_ACTIONS[action]
		InputMap.action_add_event(action, mb)


func load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(PATH) != OK:
		_detect_defaults()
		return
	quality = cfg.get_value("graphics", "quality", quality)
	render_scale = cfg.get_value("graphics", "render_scale", render_scale)
	fullscreen = cfg.get_value("graphics", "fullscreen", fullscreen)
	vsync = cfg.get_value("graphics", "vsync", vsync)
	outlines = cfg.get_value("graphics", "outlines", outlines)
	grass_density = cfg.get_value("graphics", "grass_density", grass_density)
	show_fps = cfg.get_value("graphics", "show_fps", show_fps)
	show_objective = cfg.get_value("gameplay", "show_objective", show_objective)
	fov = cfg.get_value("controls", "fov", fov)
	mouse_sensitivity = cfg.get_value("controls", "mouse_sensitivity", mouse_sensitivity)
	invert_y = cfg.get_value("controls", "invert_y", invert_y)
	volume_master = cfg.get_value("audio", "master", volume_master)
	volume_music = cfg.get_value("audio", "music", volume_music)
	volume_sfx = cfg.get_value("audio", "sfx", volume_sfx)
	volume_ambience = cfg.get_value("audio", "ambience", volume_ambience)


func _detect_defaults() -> void:
	# Integrated GPUs get the lighter preset and a little upscaling by default.
	var adapter := RenderingServer.get_video_adapter_name().to_lower()
	var integrated := adapter.contains("intel") or adapter.contains("uhd") or adapter.contains("iris") or adapter.contains("vega")
	if integrated:
		quality = Quality.MEDIUM
		render_scale = 0.8
	else:
		quality = Quality.HIGH
		render_scale = 1.0


func save_settings() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("graphics", "quality", quality)
	cfg.set_value("graphics", "render_scale", render_scale)
	cfg.set_value("graphics", "fullscreen", fullscreen)
	cfg.set_value("graphics", "vsync", vsync)
	cfg.set_value("graphics", "outlines", outlines)
	cfg.set_value("graphics", "grass_density", grass_density)
	cfg.set_value("graphics", "show_fps", show_fps)
	cfg.set_value("gameplay", "show_objective", show_objective)
	cfg.set_value("controls", "fov", fov)
	cfg.set_value("controls", "mouse_sensitivity", mouse_sensitivity)
	cfg.set_value("controls", "invert_y", invert_y)
	cfg.set_value("audio", "master", volume_master)
	cfg.set_value("audio", "music", volume_music)
	cfg.set_value("audio", "sfx", volume_sfx)
	cfg.set_value("audio", "ambience", volume_ambience)
	cfg.save(PATH)


func apply() -> void:
	var vp := get_viewport()
	if vp:
		vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR if render_scale < 0.99 else Viewport.SCALING_3D_MODE_BILINEAR
		vp.scaling_3d_scale = clampf(render_scale, 0.5, 1.0)
		vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA if quality < Quality.HIGH else Viewport.SCREEN_SPACE_AA_SMAA
		vp.msaa_3d = Viewport.MSAA_DISABLED if quality < Quality.HIGH else Viewport.MSAA_2X
		vp.positional_shadow_atlas_size = 1024 if quality == Quality.LOW else 2048
	var shadow_size := 2048 if quality < Quality.HIGH else 4096
	RenderingServer.directional_shadow_atlas_set_size(shadow_size, true)
	RenderingServer.directional_soft_shadow_filter_set_quality(
		RenderingServer.SHADOW_QUALITY_SOFT_VERY_LOW if quality == Quality.LOW else RenderingServer.SHADOW_QUALITY_SOFT_LOW)
	if not Engine.is_editor_hint() and DisplayServer.get_name() != "headless":
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
		var want_mode := DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED
		if DisplayServer.window_get_mode() != want_mode and not (want_mode == DisplayServer.WINDOW_MODE_WINDOWED and DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_MAXIMIZED):
			DisplayServer.window_set_mode(want_mode)
	_apply_audio()
	changed.emit()


func _apply_audio() -> void:
	_set_bus("Master", volume_master)
	_set_bus("Music", volume_music)
	_set_bus("SFX", volume_sfx)
	_set_bus("Ambience", volume_ambience)
	_set_bus("UI", volume_sfx)


func _set_bus(bus_name: String, v: float) -> void:
	var idx := AudioServer.get_bus_index(bus_name)
	if idx >= 0:
		AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(v, 0.0001)))
		AudioServer.set_bus_mute(idx, v <= 0.001)


func set_quality(q: int) -> void:
	quality = clampi(q, Quality.LOW, Quality.HIGH)
	apply()
