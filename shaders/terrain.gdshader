// Cartoon terrain: grass / dirt / rock / sand / forest floor / snow blended from a splat map
// (R = dirt path, G = sand, B = forest floor, A = cobble) plus automatic rock on slopes and
// snow on peaks. World-space UVs; rock is triplanar. Shares the toon light model.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

uniform sampler2D splat_map : filter_linear, repeat_disable;
uniform vec2 terrain_origin = vec2(-320.0, -320.0);
uniform vec2 terrain_size = vec2(640.0, 640.0);
uniform float tile_size = 8.0;

uniform sampler2D grass_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D dirt_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rock_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D sand_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D forest_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D cobble_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D snow_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D macro_noise : filter_linear_mipmap, repeat_enable;
uniform bool has_textures = false;

uniform vec4 grass_col : source_color = vec4(0.42, 0.72, 0.30, 1.0);
uniform vec4 grass_col2 : source_color = vec4(0.58, 0.80, 0.33, 1.0);
uniform vec4 dirt_col : source_color = vec4(0.62, 0.45, 0.30, 1.0);
uniform vec4 rock_col : source_color = vec4(0.55, 0.55, 0.60, 1.0);
uniform vec4 sand_col : source_color = vec4(0.90, 0.80, 0.58, 1.0);
uniform vec4 forest_col : source_color = vec4(0.30, 0.45, 0.24, 1.0);
uniform vec4 cobble_col : source_color = vec4(0.62, 0.60, 0.56, 1.0);
uniform vec4 snow_col : source_color = vec4(0.94, 0.97, 1.0, 1.0);
uniform float snow_height = 62.0;
uniform float rock_slope = 0.72;

varying vec3 v_world;
varying vec3 v_wnormal;

#include "res://shaders/toon_light.gdshaderinc"

vec3 tri(sampler2D t, vec3 p, vec3 n) {
	vec3 w = pow(abs(n), vec3(4.0));
	w /= (w.x + w.y + w.z + 0.0001);
	return texture(t, p.zy).rgb * w.x + texture(t, p.xz).rgb * w.y + texture(t, p.xy).rgb * w.z;
}

void vertex() {
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_wnormal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec2 suv = (v_world.xz - terrain_origin) / terrain_size;
	vec4 splat = texture(splat_map, suv);
	vec2 tuv = v_world.xz / tile_size;
	float macro = texture(macro_noise, v_world.xz / 90.0).r;
	// Work out the layer weights first, then only sample the textures that contribute.
	float w_forest = smoothstep(0.3, 0.7, splat.b);
	float w_sand = smoothstep(0.3, 0.7, splat.g);
	float w_dirt = smoothstep(0.35, 0.65, splat.r + (macro - 0.5) * 0.25);
	float w_cobble = smoothstep(0.4, 0.6, splat.a);
	float slope = 1.0 - v_wnormal.y;
	float w_rock = smoothstep(1.0 - rock_slope - 0.04, 1.0 - rock_slope + 0.04, slope + (macro - 0.5) * 0.08);
	float w_snow = smoothstep(snow_height - 4.0, snow_height + 4.0, v_world.y + (macro - 0.5) * 10.0) * (1.0 - w_rock * 0.6);
	vec3 col;
	if (has_textures) {
		col = texture(grass_tex, tuv).rgb * mix(vec3(0.92, 0.98, 0.9), vec3(1.08, 1.05, 0.92), macro);
		if (w_forest > 0.001) { col = mix(col, texture(forest_tex, tuv).rgb, w_forest); }
		if (w_sand > 0.001) { col = mix(col, texture(sand_tex, tuv).rgb, w_sand); }
		if (w_dirt > 0.001) { col = mix(col, texture(dirt_tex, tuv).rgb, w_dirt); }
		if (w_cobble > 0.001) { col = mix(col, texture(cobble_tex, v_world.xz / 4.0).rgb, w_cobble); }
		if (w_rock > 0.001) {
			// cheap biplanar: the two dominant side projections are enough for cliffs
			vec3 n = abs(v_wnormal);
			vec3 rock = n.x > n.z ? texture(rock_tex, v_world.zy / 10.0).rgb : texture(rock_tex, v_world.xy / 10.0).rgb;
			if (n.y > 0.6) { rock = texture(rock_tex, v_world.xz / 10.0).rgb; }
			col = mix(col, rock, w_rock);
		}
		if (w_snow > 0.001) { col = mix(col, texture(snow_tex, tuv).rgb, w_snow); }
	} else {
		col = mix(grass_col.rgb, grass_col2.rgb, smoothstep(0.35, 0.65, macro));
		col = mix(col, forest_col.rgb, w_forest);
		col = mix(col, sand_col.rgb, w_sand);
		col = mix(col, dirt_col.rgb, w_dirt);
		col = mix(col, cobble_col.rgb, w_cobble);
		col = mix(col, rock_col.rgb, w_rock);
		col = mix(col, snow_col.rgb, w_snow);
	}
	ALBEDO = col;
	ROUGHNESS = 0.9;
	SPECULAR = 0.2;
}
