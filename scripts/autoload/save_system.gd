extends Node
## JSON save game at user://savegame.json. World systems (e.g. the build manager) register
## providers so their state (placed contraptions, world flags) is saved too.

signal saved
signal loaded

const PATH := "user://savegame.json"
const VERSION := 1
const AUTOSAVE_INTERVAL := 150.0

var providers: Dictionary = {}     # name -> Callable returning a Dictionary
var pending: Dictionary = {}       # provider data loaded from disk, waiting for its provider
var _autosave_timer: float = 0.0
var _autosave_requested: bool = false


func register_provider(provider_name: String, save_cb: Callable) -> void:
	providers[provider_name] = save_cb


func take_pending(provider_name: String) -> Variant:
	var data: Variant = pending.get(provider_name, null)
	pending.erase(provider_name)
	return data


func unregister_provider(provider_name: String) -> void:
	providers.erase(provider_name)


func has_save() -> bool:
	return FileAccess.file_exists(PATH)


func save_game() -> bool:
	if not Game.started:
		return false
	var data := {
		"version": VERSION,
		"saved_at": Time.get_datetime_string_from_system(),
		"game": Game.to_dict(),
		"quests": Quests.to_dict(),
		"challenges": Challenges.to_dict(),
		"world": {},
	}
	for p in providers:
		var cb: Callable = providers[p]
		if cb.is_valid():
			data["world"][p] = cb.call()
	var f := FileAccess.open(PATH + ".tmp", FileAccess.WRITE)
	if f == null:
		push_warning("SaveSystem: cannot write save file")
		return false
	f.store_string(JSON.stringify(data, "\t"))
	f.close()
	DirAccess.rename_absolute(ProjectSettings.globalize_path(PATH + ".tmp"), ProjectSettings.globalize_path(PATH))
	_autosave_timer = 0.0
	saved.emit()
	return true


func load_game() -> bool:
	if not has_save():
		return false
	var f := FileAccess.open(PATH, FileAccess.READ)
	if f == null:
		return false
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("SaveSystem: save file is corrupt")
		return false
	var data: Dictionary = parsed
	Game.from_dict(data.get("game", {}))
	Quests.from_dict(data.get("quests", {}))
	Challenges.from_dict(data.get("challenges", {}))
	pending = data.get("world", {})
	loaded.emit()
	return true


func delete_save() -> void:
	if has_save():
		DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH))


func new_game() -> void:
	Game.reset()
	Quests.reset()
	Challenges.reset()
	pending = {}


func request_autosave() -> void:
	_autosave_requested = true


func _process(delta: float) -> void:
	if not Game.started:
		return
	_autosave_timer += delta
	if _autosave_requested or _autosave_timer >= AUTOSAVE_INTERVAL:
		_autosave_requested = false
		if save_game():
			Events.toast("Game saved", "save")
