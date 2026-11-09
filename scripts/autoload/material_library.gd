extends Node
## Turns every imported model into the RuneWire cartoon look.
##
## Blender materials named "M_<Name>" (optionally "M_<Name>__rrggbb" for a tint) map to the
## hand-painted texture sets in res://assets/textures/<set>/. Any other material is a flat colour:
## its base colour / emission / alpha are converted into a toon material. Results are cached so
## identical materials share one ShaderMaterial (good for batching).

const SH_TOON := preload("res://shaders/toon.gdshader")
const SH_DOUBLE := preload("res://shaders/toon_double.gdshader")
const SH_ALPHA := preload("res://shaders/toon_alpha.gdshader")
const SH_FOLIAGE := preload("res://shaders/toon_foliage.gdshader")
const SH_VIEWMODEL := preload("res://shaders/toon_viewmodel.gdshader")
const SH_DISSOLVE := preload("res://shaders/toon_dissolve.gdshader")

const TEX_DIR := "res://assets/textures/%s/%s_%s.png"

# kind: wood, stone, metal, paint, rubber, leather, fabric, skin, glass, glow, crystal, foliage
const LIBRARY := {
	"M_WoodPlanks": {"set": "wood_planks", "color": "b8834d", "kind": "wood"},
	"M_WoodDark": {"set": "wood_dark", "color": "6e4528", "kind": "wood"},
	"M_Bark": {"set": "bark", "color": "6a4a35", "kind": "wood"},
	"M_Leaves": {"set": "leaves", "color": "5fae3e", "kind": "foliage"},
	"M_Stone": {"set": "stone_bricks", "color": "a8a397", "kind": "stone"},
	"M_StoneRough": {"set": "stone_rough", "color": "8c877d", "kind": "stone"},
	"M_Cobble": {"set": "cobble", "color": "9c968a", "kind": "stone"},
	"M_Plaster": {"set": "plaster", "color": "efe2c4", "kind": "stone"},
	"M_RoofTiles": {"set": "roof_tiles", "color": "b9533b", "kind": "stone"},
	"M_Brass": {"set": "brass", "color": "dba843", "kind": "metal"},
	"M_Copper": {"set": "copper", "color": "cc7743", "kind": "metal"},
	"M_Steel": {"set": "steel", "color": "a9b0b8", "kind": "metal"},
	"M_PaintedMetal": {"set": "painted_metal", "color": "e8762c", "kind": "paint", "default_tint": "e8762c"},
	"M_DarkMetal": {"set": "dark_metal", "color": "40454d", "kind": "metal"},
	"M_Rust": {"set": "rust", "color": "8e4c2d", "kind": "paint"},
	"M_Rubber": {"set": "rubber", "color": "2d2d31", "kind": "rubber"},
	"M_Leather": {"set": "leather", "color": "7c4b2d", "kind": "leather"},
	"M_Fabric": {"set": "fabric", "color": "e8e2d6", "kind": "fabric", "default_tint": "e8e2d6"},
	"M_Skin": {"set": "skin", "color": "f1c29b", "kind": "skin"},
	"M_Glass": {"set": "", "color": "c4e8ff", "kind": "glass"},
	"M_RuneGlow": {"set": "", "color": "9a66ff", "kind": "glow", "emission": "a97bff", "energy": 4.0},
	"M_TechGlow": {"set": "", "color": "ff8c2e", "kind": "glow", "emission": "ff9b3f", "energy": 4.0},
	"M_EmberGlow": {"set": "", "color": "ffb54a", "kind": "glow", "emission": "ffa841", "energy": 4.0},
	"M_Crystal": {"set": "crystal", "color": "70f0e2", "kind": "crystal", "emission": "5fe9ff", "energy": 1.6},
}

# Lighting style per kind.
const KIND_PARAMS := {
	"wood": {"specular_strength": 0.08, "glossiness": 0.2, "rim_strength": 0.22},
	"stone": {"specular_strength": 0.05, "glossiness": 0.15, "rim_strength": 0.2},
	"metal": {"specular_strength": 0.75, "glossiness": 0.62, "rim_strength": 0.4, "metallic_look": 1.0},
	"paint": {"specular_strength": 0.35, "glossiness": 0.45, "rim_strength": 0.3, "metallic_look": 0.15},
	"rubber": {"specular_strength": 0.15, "glossiness": 0.35, "rim_strength": 0.2},
	"leather": {"specular_strength": 0.2, "glossiness": 0.35, "rim_strength": 0.25},
	"fabric": {"specular_strength": 0.0, "glossiness": 0.1, "rim_strength": 0.38},
	"skin": {"specular_strength": 0.12, "glossiness": 0.3, "rim_strength": 0.4, "shadow_color": Color(0.72, 0.45, 0.52)},
	"glass": {"specular_strength": 1.0, "glossiness": 0.9, "rim_strength": 0.5},
	"glow": {"specular_strength": 0.0, "glossiness": 0.1, "rim_strength": 0.0},
	"crystal": {"specular_strength": 0.9, "glossiness": 0.85, "rim_strength": 0.6},
	"foliage": {"specular_strength": 0.0, "glossiness": 0.1, "rim_strength": 0.35, "band_softness": 0.12, "shadow_light": 0.38},
	"flat": {"specular_strength": 0.2, "glossiness": 0.35, "rim_strength": 0.28},
}

var _cache: Dictionary = {}
var _tex_cache: Dictionary = {}


## Apply toon materials to every MeshInstance3D under `root`.
## variant: "" (world), "viewmodel" (first-person), "dissolve" (death fx).
func apply(root: Node, variant: String = "") -> void:
	if root == null:
		return
	if root is MeshInstance3D:
		_apply_mesh(root, variant)
	for child in root.get_children():
		apply(child, variant)


func _apply_mesh(mi: MeshInstance3D, variant: String) -> void:
	if mi.mesh == null:
		return
	for i in mi.mesh.get_surface_count():
		var src: Material = mi.get_surface_override_material(i)
		if src == null:
			src = mi.mesh.surface_get_material(i)
		var m := material_for(src, variant)
		if m:
			mi.set_surface_override_material(i, m)
	if variant == "viewmodel":
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.layers = 1 << 19  # viewmodel render layer (also visible to main camera)


## Returns a toon ShaderMaterial for an imported (or library) material.
func material_for(src: Material, variant: String = "") -> Material:
	if src == null:
		return get_flat(Color(0.8, 0.8, 0.8), variant)
	if src is ShaderMaterial and (src.get_meta("rw_toon", false) as bool):
		if variant == "" or src.get_meta("rw_variant", "") == variant:
			return src
		var nm: String = src.get_meta("rw_name", "")
		if nm != "":
			return get_named(nm, variant)
	var name := src.resource_name
	if name.begins_with("M_"):
		return get_named(name, variant)
	var key := "flat|%s|%s" % [_material_signature(src), variant]
	if _cache.has(key):
		return _cache[key]
	var m := _convert_standard(src, variant)
	_cache[key] = m
	return m


func _material_signature(src: Material) -> String:
	if src is BaseMaterial3D:
		var b := src as BaseMaterial3D
		var sig := "%s_%s_%.2f_%.2f" % [src.resource_name, b.albedo_color.to_html(), b.metallic, b.roughness]
		if b.emission_enabled:
			sig += "_e%s_%.2f" % [b.emission.to_html(), b.emission_energy_multiplier]
		return sig
	return str(src.get_instance_id())


## Library material by name, e.g. "M_Brass" or "M_Fabric__8a2be2".
func get_named(full_name: String, variant: String = "") -> ShaderMaterial:
	var key := "%s|%s" % [full_name, variant]
	if _cache.has(key):
		return _cache[key]
	var base_name := full_name
	var tint := ""
	if full_name.contains("__"):
		var parts := full_name.split("__")
		base_name = parts[0]
		tint = parts[1]
	# Blender may append ".001" etc. to duplicated material names.
	var dot := base_name.find(".")
	if dot > 0:
		base_name = base_name.substr(0, dot)
	if tint.contains("."):
		tint = tint.substr(0, tint.find("."))
	var def: Dictionary = LIBRARY.get(base_name, {})
	if def.is_empty():
		push_warning("MaterialLib: unknown library material %s" % full_name)
		def = {"set": "", "color": "cccccc", "kind": "flat"}
	var kind: String = def.get("kind", "flat")
	var shader := _shader_for(kind, variant)
	var m := ShaderMaterial.new()
	m.shader = shader
	m.resource_name = full_name
	_apply_kind(m, kind)
	var set_name: String = def.get("set", "")
	var albedo := _tex(set_name, "albedo")
	var color := Color(def.get("color", "cccccc"))
	if albedo:
		m.set_shader_parameter("albedo_texture", albedo)
		m.set_shader_parameter("use_albedo_texture", true)
		color = Color.WHITE
		if def.has("default_tint"):
			color = Color(def["default_tint"])
	if tint != "":
		var t := Color(tint)
		color = t if albedo else color.lerp(t, 0.75)
	m.set_shader_parameter("albedo_color", color)
	var normal := _tex(set_name, "normal")
	if normal:
		m.set_shader_parameter("normal_texture", normal)
		m.set_shader_parameter("use_normal_texture", true)
		m.set_shader_parameter("normal_strength", 0.9)
	var emission_tex := _tex(set_name, "emission")
	if def.has("emission"):
		# a tinted crystal / glow (e.g. M_Crystal__a066ff) glows in its tint, not the library's default
		var ecol := Color(tint) if tint != "" and kind in ["crystal", "glow"] else Color(def["emission"])
		m.set_shader_parameter("emission_color", ecol)
		m.set_shader_parameter("emission_energy", float(def.get("energy", 2.0)))
		if kind == "glow":
			m.set_shader_parameter("emission_pulse", 0.25)
	if emission_tex:
		m.set_shader_parameter("emission_texture", emission_tex)
		m.set_shader_parameter("use_emission_texture", true)
	if kind == "glass":
		m.set_shader_parameter("alpha_value", 0.28)
		m.set_shader_parameter("fresnel_alpha", 0.55)
	elif kind == "crystal":
		m.set_shader_parameter("alpha_value", 0.82)
		m.set_shader_parameter("fresnel_alpha", 0.3)
	elif kind == "foliage":
		m.set_shader_parameter("wind_strength", 0.12)
		m.set_shader_parameter("wind_height", 8.0)
	m.set_meta("rw_toon", true)
	m.set_meta("rw_name", full_name)
	m.set_meta("rw_variant", variant)
	_cache[key] = m
	return m


func _shader_for(kind: String, variant: String) -> Shader:
	match variant:
		"viewmodel":
			return SH_VIEWMODEL if kind not in ["glass", "crystal"] else SH_ALPHA
		"dissolve":
			return SH_DISSOLVE
	match kind:
		"glass", "crystal":
			return SH_ALPHA
		"foliage":
			return SH_FOLIAGE
	return SH_TOON


func _apply_kind(m: ShaderMaterial, kind: String) -> void:
	var p: Dictionary = KIND_PARAMS.get(kind, KIND_PARAMS["flat"])
	for k in p:
		m.set_shader_parameter(k, p[k])


func _convert_standard(src: Material, variant: String) -> ShaderMaterial:
	var color := Color(0.8, 0.8, 0.8)
	var metal := 0.0
	var rough := 0.7
	var emission := Color.BLACK
	var energy := 0.0
	var alpha := 1.0
	var tex: Texture2D = null
	if src is BaseMaterial3D:
		var b := src as BaseMaterial3D
		color = b.albedo_color
		metal = b.metallic
		rough = b.roughness
		tex = b.albedo_texture
		if b.emission_enabled:
			emission = b.emission
			energy = b.emission_energy_multiplier
		alpha = color.a
		if b.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED:
			alpha = 1.0
	var lname := src.resource_name.to_lower()
	var kind := "flat"
	if energy > 0.01 and emission.get_luminance() > 0.01:
		kind = "glow"
	elif alpha < 0.98:
		kind = "glass"
	elif metal > 0.5:
		kind = "metal"
	if lname.contains("grass") or lname.contains("leaf") or lname.contains("leaves") or lname.contains("foliage") or lname.contains("flower") or lname.contains("petal"):
		kind = "foliage"
	var m := ShaderMaterial.new()
	m.shader = _shader_for(kind, variant)
	m.resource_name = src.resource_name
	_apply_kind(m, kind)
	color.a = 1.0
	m.set_shader_parameter("albedo_color", color)
	if tex:
		m.set_shader_parameter("albedo_texture", tex)
		m.set_shader_parameter("use_albedo_texture", true)
	if kind == "glow":
		m.set_shader_parameter("emission_color", emission)
		m.set_shader_parameter("emission_energy", maxf(energy, 1.0))
	if kind == "glass":
		m.set_shader_parameter("alpha_value", alpha)
		m.set_shader_parameter("fresnel_alpha", 0.4)
	if kind == "foliage":
		var small := lname.contains("grass") or lname.contains("flower") or lname.contains("petal")
		m.set_shader_parameter("wind_strength", 0.07 if small else 0.12)
		m.set_shader_parameter("wind_height", 0.7 if small else 8.0)
	if kind == "metal" or kind == "flat":
		m.set_shader_parameter("glossiness", clampf(1.0 - rough, 0.1, 0.9))
	m.set_meta("rw_toon", true)
	m.set_meta("rw_variant", variant)
	return m


## A plain toon material of a given colour (cached).
func get_flat(color: Color, variant: String = "", kind: String = "flat") -> ShaderMaterial:
	var key := "plain|%s|%s|%s" % [color.to_html(), variant, kind]
	if _cache.has(key):
		return _cache[key]
	var m := ShaderMaterial.new()
	m.shader = _shader_for(kind, variant)
	_apply_kind(m, kind)
	m.set_shader_parameter("albedo_color", color)
	m.set_meta("rw_toon", true)
	m.set_meta("rw_variant", variant)
	_cache[key] = m
	return m


## A glowing (emissive) toon material (cached).
func get_glow(color: Color, energy: float = 3.0, pulse: float = 0.0) -> ShaderMaterial:
	var key := "glow|%s|%.2f|%.2f" % [color.to_html(), energy, pulse]
	if _cache.has(key):
		return _cache[key]
	var m := ShaderMaterial.new()
	m.shader = SH_TOON
	_apply_kind(m, "glow")
	m.set_shader_parameter("albedo_color", color.darkened(0.3))
	m.set_shader_parameter("emission_color", color)
	m.set_shader_parameter("emission_energy", energy)
	m.set_shader_parameter("emission_pulse", pulse)
	m.set_meta("rw_toon", true)
	_cache[key] = m
	return m


func _tex(set_name: String, map: String) -> Texture2D:
	if set_name == "":
		return null
	var path := TEX_DIR % [set_name, set_name, map]
	if _tex_cache.has(path):
		return _tex_cache[path]
	var t: Texture2D = null
	if ResourceLoader.exists(path):
		t = load(path)
	_tex_cache[path] = t
	return t


func texture(path: String) -> Texture2D:
	if _tex_cache.has(path):
		return _tex_cache[path]
	var t: Texture2D = null
	if ResourceLoader.exists(path):
		t = load(path)
	_tex_cache[path] = t
	return t


## Flash an object white briefly (hit feedback). Uses the per-instance shader parameter.
func flash(root: Node, amount: float = 1.0) -> void:
	_set_instance_param(root, "hit_flash", amount)


func set_paint(root: Node, color: Color) -> void:
	_set_instance_param(root, "paint_tint", color)


func _set_instance_param(root: Node, param: String, value: Variant) -> void:
	if root is GeometryInstance3D:
		(root as GeometryInstance3D).set_instance_shader_parameter(param, value)
	for c in root.get_children():
		_set_instance_param(c, param, value)


## Instantiate a model scene (e.g. a .glb) with toon materials applied.
func instance_model(path: String, variant: String = "") -> Node3D:
	if not ResourceLoader.exists(path):
		return null
	var ps: PackedScene = load(path)
	if ps == null:
		return null
	var n := ps.instantiate() as Node3D
	apply(n, variant)
	return n
