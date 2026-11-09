class_name NightLight
extends OmniLight3D
## Warm lamp light that only exists at night (group "night_lights", driven by EnvironmentRig).
## Hidden during the day so the clustered renderer doesn't pay for dozens of idle lights.

var on_energy: float = 1.6


func _ready() -> void:
	on_energy = light_energy
	shadow_enabled = false
	omni_attenuation = 1.2
	distance_fade_enabled = true
	distance_fade_begin = 60.0
	distance_fade_length = 20.0
	add_to_group("night_lights")
	var rig := get_tree().get_first_node_in_group("environment_rig")
	var night: bool = rig != null and rig.is_night
	visible = night
	light_energy = on_energy if night else 0.0


func set_night(is_night: bool) -> void:
	var tw := create_tween()
	if is_night:
		visible = true
		tw.tween_property(self, "light_energy", on_energy, 2.0)
	else:
		tw.tween_property(self, "light_energy", 0.0, 2.0)
		tw.tween_callback(func(): visible = false)
