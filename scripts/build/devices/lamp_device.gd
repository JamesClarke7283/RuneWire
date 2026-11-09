class_name LampDevice
extends Device
## Brass lantern: a warm light, toggled with F while piloting or with the Rune Toolkit.

var light: OmniLight3D


func _ready() -> void:
	light = OmniLight3D.new()
	light.light_color = Color(1.0, 0.78, 0.42)
	light.light_energy = 2.2
	light.omni_range = 11.0
	light.shadow_enabled = false
	var lp := part.model.find_child("LightPoint", true, false) as Node3D
	if lp:
		lp.add_child(light)
	else:
		add_child(light)


func toggle() -> void:
	super.toggle()
	set_on(enabled)


func set_on(on: bool) -> void:
	enabled = on
	if light:
		light.visible = on


func load_data(d: Dictionary) -> void:
	super.load_data(d)
	set_on.call_deferred(enabled)
