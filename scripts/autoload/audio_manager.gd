extends Node
## Sound playback: pooled 3D one-shots, UI sounds, attached loops, crossfading music and ambience.
## Missing sound files are ignored silently so the game runs before audio assets exist.

const SFX_PATH := "res://assets/audio/sfx/%s.wav"
const MUSIC_PATH := "res://assets/audio/music/%s.wav"
const POOL_3D := 24
const POOL_2D := 10

var _streams: Dictionary = {}
var _pool3d: Array[AudioStreamPlayer3D] = []
var _pool2d: Array[AudioStreamPlayer] = []
var _next3d: int = 0
var _next2d: int = 0
var _music: Array[AudioStreamPlayer] = []
var _music_idx: int = 0
var _current_music: String = ""
var _amb: Array[AudioStreamPlayer] = []
var _amb_idx: int = 0
var _current_amb: String = ""
var _last_played: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in POOL_3D:
		var p := AudioStreamPlayer3D.new()
		p.bus = &"SFX"
		p.unit_size = 8.0
		p.max_distance = 90.0
		p.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE
		p.panning_strength = 0.8
		add_child(p)
		_pool3d.append(p)
	for i in POOL_2D:
		var p2 := AudioStreamPlayer.new()
		p2.bus = &"SFX"
		add_child(p2)
		_pool2d.append(p2)
	for i in 2:
		var m := AudioStreamPlayer.new()
		m.bus = &"Music"
		m.volume_db = -80.0
		add_child(m)
		_music.append(m)
		var a := AudioStreamPlayer.new()
		a.bus = &"Ambience"
		a.volume_db = -80.0
		add_child(a)
		_amb.append(a)


func stream(sound_name: String, looped: bool = false) -> AudioStream:
	var key := sound_name + ("#loop" if looped else "")
	if _streams.has(key):
		return _streams[key]
	var path := SFX_PATH % sound_name
	if sound_name.begins_with("music_"):
		path = MUSIC_PATH % sound_name
	var s: AudioStream = null
	if ResourceLoader.exists(path):
		s = load(path)
		if looped and s is AudioStreamWAV:
			var w := (s as AudioStreamWAV).duplicate() as AudioStreamWAV
			w.loop_mode = AudioStreamWAV.LOOP_FORWARD
			w.loop_begin = 0
			w.loop_end = int(w.get_length() * w.mix_rate)
			s = w
	_streams[key] = s
	return s


## One-shot positional sound.
func play(sound_name: String, pos: Vector3, volume_db: float = 0.0, pitch: float = 1.0, pitch_var: float = 0.07, unit_size: float = 8.0) -> AudioStreamPlayer3D:
	var s := stream(sound_name)
	if s == null:
		return null
	var now := Time.get_ticks_msec()
	var key := "%s_%d_%d" % [sound_name, int(pos.x / 3.0), int(pos.z / 3.0)]
	if _last_played.has(key) and now - int(_last_played[key]) < 35:
		return null  # avoid stacking identical sounds in the same frame/place
	_last_played[key] = now
	var p := _pool3d[_next3d]
	_next3d = (_next3d + 1) % POOL_3D
	p.stop()
	p.stream = s
	p.global_position = pos
	p.volume_db = volume_db
	p.unit_size = unit_size
	p.pitch_scale = maxf(0.05, pitch * (1.0 + randf_range(-pitch_var, pitch_var)))
	p.play()
	return p


## Non-positional sound (player's own actions, UI).
func play_2d(sound_name: String, volume_db: float = 0.0, pitch: float = 1.0, pitch_var: float = 0.04, bus: StringName = &"SFX") -> void:
	var s := stream(sound_name)
	if s == null:
		return
	var p := _pool2d[_next2d]
	_next2d = (_next2d + 1) % POOL_2D
	p.stop()
	p.stream = s
	p.bus = bus
	p.volume_db = volume_db
	p.pitch_scale = maxf(0.05, pitch * (1.0 + randf_range(-pitch_var, pitch_var)))
	p.play()


func play_ui(sound_name: String, volume_db: float = -4.0) -> void:
	play_2d(sound_name, volume_db, 1.0, 0.02, &"UI")


## A looping 3D sound attached to a node. Returns the player (free it or stop it yourself).
func attach_loop(parent: Node3D, sound_name: String, volume_db: float = 0.0, unit_size: float = 6.0, autoplay: bool = true) -> AudioStreamPlayer3D:
	var s := stream(sound_name, true)
	var p := AudioStreamPlayer3D.new()
	p.bus = &"SFX"
	p.stream = s
	p.volume_db = volume_db
	p.unit_size = unit_size
	p.max_distance = 70.0
	parent.add_child(p)
	if autoplay and s:
		p.play()
	return p


func play_music(track: String, fade: float = 2.5) -> void:
	if track == _current_music:
		return
	_current_music = track
	var s := stream(track, true)
	var old := _music[_music_idx]
	_music_idx = 1 - _music_idx
	var cur := _music[_music_idx]
	var tw := create_tween().set_parallel(true)
	tw.tween_property(old, "volume_db", -80.0, fade)
	if s:
		cur.stream = s
		cur.volume_db = -40.0
		cur.play()
		tw.tween_property(cur, "volume_db", 0.0, fade)
	tw.chain().tween_callback(old.stop)


func play_ambience(track: String, fade: float = 3.0) -> void:
	if track == _current_amb:
		return
	_current_amb = track
	var s := stream(track, true)
	var old := _amb[_amb_idx]
	_amb_idx = 1 - _amb_idx
	var cur := _amb[_amb_idx]
	var tw := create_tween().set_parallel(true)
	tw.tween_property(old, "volume_db", -80.0, fade)
	if s:
		cur.stream = s
		cur.volume_db = -40.0
		cur.play()
		tw.tween_property(cur, "volume_db", -2.0, fade)
	tw.chain().tween_callback(old.stop)
