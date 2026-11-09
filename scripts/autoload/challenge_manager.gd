extends Node
## Challenge definitions, medal thresholds, best results and gold payouts.
## The in-world challenge stations run the actual gameplay and call start()/finish()/fail().

signal challenge_state_changed(id: String, running: bool)

const CHALLENGES := {
	"arena": {"name": "Arena of Echoes", "kind": "waves", "higher_better": true,
		"medals": [3, 6, 10], "rewards": [100, 200, 400], "unit": "waves",
		"desc": "Survive waves of conjured magic and tech foes. Each wave cleared pays 15 gold x the wave number. Bronze: 3 waves, Silver: 6, Gold: 10."},
	"race": {"name": "Valley Rally", "kind": "time", "higher_better": false,
		"medals": [150.0, 110.0, 80.0], "rewards": [80, 160, 300], "unit": "s",
		"desc": "Fly or drive through all 12 rune rings in order. Vehicles strongly recommended! Bronze under 2:30, Silver under 1:50, Gold under 1:20."},
	"targets": {"name": "Target Range", "kind": "score", "higher_better": true,
		"medals": [10, 18, 26], "rewards": [60, 120, 250], "unit": "hits",
		"desc": "Hit as many pop-up targets as you can in 60 seconds. Bronze 10, Silver 18, Gold 26."},
	"cargo": {"name": "Gorge Haul", "kind": "time", "higher_better": false,
		"medals": [240.0, 150.0, 95.0], "rewards": [100, 200, 400], "unit": "s",
		"desc": "Get the heavy crate across the gorge and onto the goal pad. Bridge it, fly it or fling it. Bronze under 4:00, Silver under 2:30, Gold under 1:35."},
	"altitude": {"name": "Skyward Beacon", "kind": "time", "higher_better": false,
		"medals": [180.0, 110.0, 60.0], "rewards": [100, 200, 400], "unit": "s",
		"desc": "Touch the ley beacon floating 40 m above the Builder's Flats. Bronze under 3:00, Silver under 1:50, Gold under 1:00."},
}

const MEDAL_NAMES := ["None", "Bronze", "Silver", "Gold"]
const MEDAL_COLORS := [Color(0.6, 0.6, 0.6), Color(0.85, 0.52, 0.28), Color(0.82, 0.86, 0.92), Color(1.0, 0.82, 0.25)]

var best: Dictionary = {}
var claimed: Dictionary = {}
var running: String = ""
var start_time: float = 0.0


func reset() -> void:
	best = {}
	claimed = {}
	running = ""


func def(id: String) -> Dictionary:
	return CHALLENGES.get(id, {})


func medal_for(id: String, value: float) -> int:
	var d := def(id)
	var medal := 0
	for i in d["medals"].size():
		var thr := float(d["medals"][i])
		if d["higher_better"]:
			if value >= thr:
				medal = i + 1
		else:
			if value <= thr:
				medal = i + 1
	return medal


func best_medal(id: String) -> int:
	if not best.has(id):
		return 0
	return medal_for(id, float(best[id]))


func format_value(id: String, value: float) -> String:
	var d := def(id)
	if d["kind"] == "time":
		var m := int(value) / 60
		var s := fmod(value, 60.0)
		return "%d:%05.2f" % [m, s]
	return "%d %s" % [int(value), d["unit"]]


func start(id: String) -> bool:
	if running != "":
		return false
	running = id
	start_time = Time.get_ticks_msec() / 1000.0
	Events.challenge_started.emit(id)
	challenge_state_changed.emit(id, true)
	return true


func elapsed() -> float:
	return Time.get_ticks_msec() / 1000.0 - start_time


func fail(id: String, reason: String = "") -> void:
	if running != id:
		return
	running = ""
	challenge_state_changed.emit(id, false)
	Events.toast("%s failed%s" % [def(id)["name"], (": " + reason) if reason != "" else ""], "warn")
	Events.challenge_finished.emit(id, {"value": 0.0, "medal": 0, "gold": 0, "failed": true})


## Finish a run with a result value (time in seconds, score, or waves). Pays out and records bests.
func finish(id: String, value: float) -> Dictionary:
	if running == id:
		running = ""
		challenge_state_changed.emit(id, false)
	var d := def(id)
	var medal := medal_for(id, value)
	var gold := 0
	var prev_claim := int(claimed.get(id, 0))
	if medal > prev_claim:
		for t in range(prev_claim, medal):
			gold += int(d["rewards"][t])
		claimed[id] = medal
	elif medal > 0:
		gold = int(round(float(d["rewards"][medal - 1]) * 0.25))
	var is_best := false
	if not best.has(id):
		is_best = true
	elif d["higher_better"] and value > float(best[id]):
		is_best = true
	elif not d["higher_better"] and value < float(best[id]):
		is_best = true
	if is_best and (medal > 0 or d["higher_better"]):
		best[id] = value
	if gold > 0:
		Game.add_gold(gold, "%s (%s)" % [d["name"], MEDAL_NAMES[medal]])
	var xp := 40 * medal
	if xp > 0:
		Game.add_xp(xp)
	var result := {"value": value, "medal": medal, "gold": gold, "best": is_best}
	Events.challenge_finished.emit(id, result)
	SaveSystem.request_autosave()
	return result


func to_dict() -> Dictionary:
	return {"best": best, "claimed": claimed}


func from_dict(d: Dictionary) -> void:
	best = {}
	claimed = {}
	for k in d.get("best", {}):
		best[str(k)] = float(d["best"][k])
	for k in d.get("claimed", {}):
		claimed[str(k)] = int(d["claimed"][k])
	running = ""
