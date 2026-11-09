extends Node
## Root of the game scene: builds the world behind the title screen, then starts or continues a
## game, spawns the player and drives pause / menus.

var world: World
var player: Player
var ui: GameUI
var menu_cam: Camera3D
var playing: bool = false
var _menu_t: float = 0.0


func _ready() -> void:
	get_tree().root.theme = UIStyle.build_theme()
	ui = GameUI.new()
	ui.name = "UI"
	add_child(ui)
	ui.show_loading("Loading", 0.0)
	world = World.new()
	world.name = "World"
	add_child(world)
	world.build_progress.connect(func(step, f): ui.show_loading(step, f))
	await world.build()
	menu_cam = Camera3D.new()
	menu_cam.name = "MenuCamera"
	menu_cam.fov = 60.0
	menu_cam.far = 900.0
	add_child(menu_cam)
	menu_cam.add_child(OutlineOverlay.new())
	menu_cam.current = true
	_update_menu_cam(0.0)
	ui.hide_loading()
	if Dev.has("autostart"):
		start_game(true)
	elif Dev.has("continue") and SaveSystem.has_save():
		start_game(false)
	else:
		ui.show_main_menu()
		AudioManager.play_music("music_menu")


func _process(delta: float) -> void:
	if not playing and menu_cam:
		_menu_t += delta
		_update_menu_cam(_menu_t)


func _update_menu_cam(t: float) -> void:
	var ang := t * 0.04 + 0.6
	var r := 52.0
	var target := Vector3(0, 9, 0)
	var pos := Vector3(sin(ang) * r, 0, cos(ang) * r)
	pos.y = world.ground_y(pos.x, pos.z) + 16.0
	menu_cam.global_position = pos
	menu_cam.look_at(target, Vector3.UP)


func start_game(new_game: bool) -> void:
	if new_game:
		SaveSystem.new_game()
	else:
		if not SaveSystem.load_game():
			SaveSystem.new_game()
			new_game = true
	player = Player.new()
	player.name = "Player"
	world.add_child(player)
	if Game.has_player_transform and not new_game:
		player.teleport(Game.player_transform.origin, rad_to_deg(Game.player_transform.basis.get_euler().y), 0.0)
	else:
		player.teleport(world.spawn_point(), 0.0, -5.0)
	player.camera.current = true
	menu_cam.current = false
	playing = true
	Game.started = true
	world.on_game_started()
	ui.on_game_started(player)
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	Events.game_started.emit(new_game)
	AudioManager.play_music("music_town")
	AudioManager.play_ambience("amb_birds_loop")
	if new_game and not Dev.has("no-intro"):
		ui.show_intro()
	Dev.on_game_started(self)


func save_now() -> void:
	if player:
		player.save_state()
	if SaveSystem.save_game():
		Events.toast("Game saved", "save")


func quit_to_menu() -> void:
	save_now()
	get_tree().paused = false
	Game.started = false
	get_tree().reload_current_scene()


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST and playing:
		save_now()
