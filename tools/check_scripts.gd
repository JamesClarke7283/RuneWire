extends Node
## Compiles every GDScript under res://scripts and reports failures (run as a scene so autoloads exist).
## Usage: godot --headless --path . res://tools/check_scripts.tscn

var failures := 0
var count := 0


func _ready() -> void:
	for dir in ["res://scripts", "res://tools/tests"]:
		_walk(dir)
	print("CHECK done: %d scripts, %d failed" % [count, failures])
	get_tree().quit(1 if failures > 0 else 0)


func _walk(path: String) -> void:
	var d := DirAccess.open(path)
	if d == null:
		return
	d.list_dir_begin()
	var f := d.get_next()
	while f != "":
		var full := path + "/" + f
		if d.current_is_dir():
			if not f.begins_with("."):
				_walk(full)
		elif f.ends_with(".gd"):
			count += 1
			var s: Script = ResourceLoader.load(full, "", ResourceLoader.CACHE_MODE_IGNORE)
			if s == null or not s.can_instantiate():
				failures += 1
				print("CHECK FAIL ", full)
		f = d.get_next()
