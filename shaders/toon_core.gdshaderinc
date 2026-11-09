// Core of the RuneWire toon surface shaders. Variants #define:
//   TOON_ALPHA      transparent (glass, crystal, ghosts)
//   TOON_WIND       vertex wind sway (foliage)
//   TOON_VIEWMODEL  first-person items: depth squeezed toward the camera so they never clip into walls
//   TOON_DISSOLVE   death dissolve (swapped in temporarily)

uniform vec4 albedo_color : source_color = vec4(1.0);
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform bool use_albedo_texture = false;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform bool use_normal_texture = false;
uniform float normal_strength : hint_range(0.0, 3.0) = 0.8;
uniform sampler2D emission_texture : source_color, hint_default_black, filter_linear_mipmap, repeat_enable;
uniform bool use_emission_texture = false;
uniform vec4 emission_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float emission_energy : hint_range(0.0, 16.0) = 0.0;
uniform float emission_pulse : hint_range(0.0, 1.0) = 0.0;
uniform float uv_scale = 1.0;
uniform bool use_vertex_color = false;
uniform bool triplanar = false;
uniform float triplanar_scale = 0.5;
uniform float roughness : hint_range(0.0, 1.0) = 0.8;
uniform float metallic : hint_range(0.0, 1.0) = 0.0;
uniform float alpha_value : hint_range(0.0, 1.0) = 1.0;
uniform float fresnel_alpha : hint_range(0.0, 1.0) = 0.0;
uniform float wind_strength = 0.0;
uniform float wind_speed = 1.3;
uniform float wind_height = 6.0;
uniform float vm_z_scale = 0.06;

instance uniform vec4 paint_tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
instance uniform float hit_flash = 0.0;
#ifdef TOON_DISSOLVE
instance uniform float dissolve = 0.0;
uniform vec4 dissolve_color : source_color = vec4(0.7, 0.45, 1.0, 1.0);
#endif

varying vec3 v_obj_pos;
varying vec3 v_obj_normal;

#include "res://shaders/toon_light.gdshaderinc"

vec4 tri_sample(sampler2D tex, vec3 p, vec3 n) {
	vec3 w = pow(abs(n), vec3(4.0));
	w /= (w.x + w.y + w.z + 0.0001);
	return texture(tex, p.zy) * w.x + texture(tex, p.xz) * w.y + texture(tex, p.xy) * w.z;
}

void vertex() {
	v_obj_pos = VERTEX;
	v_obj_normal = NORMAL;
#ifdef TOON_WIND
	float hgt = clamp(VERTEX.y / wind_height, 0.0, 1.0);
	vec3 wpos = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float t = TIME * wind_speed + wpos.x * 0.13 + wpos.z * 0.09 + VERTEX.y * 0.4;
	float sway = wind_strength * hgt * hgt;
	VERTEX.x += (sin(t) + 0.35 * sin(t * 2.7 + VERTEX.z)) * sway;
	VERTEX.z += (cos(t * 0.83) + 0.3 * sin(t * 2.1 + VERTEX.x)) * sway * 0.6;
#endif
#ifdef TOON_VIEWMODEL
	POSITION = PROJECTION_MATRIX * MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	POSITION.z = mix(POSITION.w, POSITION.z, vm_z_scale);
#endif
}

void fragment() {
	vec2 uv = UV * uv_scale;
	vec4 base = albedo_color;
	if (use_albedo_texture) {
		if (triplanar) {
			base *= tri_sample(albedo_texture, v_obj_pos * triplanar_scale, v_obj_normal);
		} else {
			base *= texture(albedo_texture, uv);
		}
	}
	if (use_vertex_color) {
		base *= COLOR;
	}
	base.rgb *= paint_tint.rgb;
	ALBEDO = mix(base.rgb, vec3(1.0), clamp(hit_flash, 0.0, 1.0));
	if (use_normal_texture && !triplanar) {
		NORMAL_MAP = texture(normal_texture, uv).rgb;
		NORMAL_MAP_DEPTH = normal_strength;
	}
	ROUGHNESS = roughness;
	METALLIC = metallic * 0.5;
	SPECULAR = 0.3;
	vec3 em = emission_color.rgb * emission_energy;
	if (use_emission_texture) {
		em *= texture(emission_texture, uv).rgb;
	}
	if (emission_pulse > 0.0) {
		em *= 1.0 - emission_pulse * 0.5 * (1.0 + sin(TIME * 2.6 + v_obj_pos.x * 1.7 + v_obj_pos.y * 2.3));
	}
	EMISSION = em + hit_flash * vec3(0.45, 0.42, 0.38);
#ifdef TOON_DISSOLVE
	float n = fract(sin(dot(floor(v_obj_pos * 18.0), vec3(12.9898, 78.233, 37.719))) * 43758.5453);
	if (n < dissolve) {
		discard;
	}
	EMISSION += dissolve_color.rgb * step(n, dissolve + 0.07) * 4.0 * step(0.001, dissolve);
#endif
#ifdef TOON_ALPHA
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.0);
	ALPHA = clamp(alpha_value * base.a + fres * fresnel_alpha, 0.0, 1.0);
#endif
}
