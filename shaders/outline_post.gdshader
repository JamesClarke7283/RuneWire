// Screen-space cartoon outlines from depth + normal discontinuities.
// Drawn on a QuadMesh that covers the screen (see scripts/vfx/outline_overlay.gd).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_disabled, fog_disabled, shadows_disabled;

uniform sampler2D depth_texture : hint_depth_texture, filter_nearest;
uniform sampler2D normal_rough_texture : hint_normal_roughness_texture, filter_nearest;
uniform vec4 outline_color : source_color = vec4(0.09, 0.06, 0.13, 1.0);
uniform float thickness = 1.0;
uniform float depth_sensitivity = 0.06;
uniform float normal_sensitivity = 0.55;
uniform float fade_start = 60.0;
uniform float fade_end = 160.0;
uniform float opacity = 0.9;
uniform int debug_mode = 0;

void vertex() {
	POSITION = vec4(VERTEX.xy * 2.0, 1.0, 1.0);
}

float lin_depth(vec2 uv, mat4 inv_proj) {
	float d = texture(depth_texture, uv).r;
	vec4 v = inv_proj * vec4(uv * 2.0 - 1.0, d, 1.0);
	return -v.z / v.w;
}

vec3 view_normal(vec2 uv) {
	return texture(normal_rough_texture, uv).xyz * 2.0 - 1.0;
}

// Grass and flowers write roughness 1.0 so they never get outlines (they'd turn into black noise).
// Works whether the buffer stores raw roughness or Godot's packed static/dynamic form
// (packed roughness 1.0 lands at 0.498 or 0.502; no other material uses roughness near 0.5).
float is_grass(vec2 uv) {
	float a = texture(normal_rough_texture, uv).a;
	return max(step(0.985, a), 1.0 - step(0.012, abs(a - 0.5)));
}

float grass_of(vec4 nr) {
	return max(step(0.985, nr.a), 1.0 - step(0.012, abs(nr.a - 0.5)));
}

void fragment() {
	vec2 px = thickness / VIEWPORT_SIZE;
	float d0 = lin_depth(SCREEN_UV, INV_PROJECTION_MATRIX);
	float d1 = lin_depth(SCREEN_UV + vec2(px.x, 0.0), INV_PROJECTION_MATRIX);
	float d2 = lin_depth(SCREEN_UV - vec2(px.x, 0.0), INV_PROJECTION_MATRIX);
	float d3 = lin_depth(SCREEN_UV + vec2(0.0, px.y), INV_PROJECTION_MATRIX);
	float d4 = lin_depth(SCREEN_UV - vec2(0.0, px.y), INV_PROJECTION_MATRIX);
	// Second-derivative depth test: flat slanted planes produce ~0, silhouettes produce a spike.
	float dd = abs(d1 + d2 - 2.0 * d0) + abs(d3 + d4 - 2.0 * d0);
	float depth_edge = smoothstep(depth_sensitivity, depth_sensitivity * 2.0, dd / max(d0, 0.05));
	vec4 r0 = texture(normal_rough_texture, SCREEN_UV);
	vec4 r1 = texture(normal_rough_texture, SCREEN_UV + vec2(px.x, 0.0));
	vec4 r3 = texture(normal_rough_texture, SCREEN_UV + vec2(0.0, px.y));
	vec3 n0 = r0.xyz * 2.0 - 1.0;
	vec3 n1 = r1.xyz * 2.0 - 1.0;
	vec3 n3 = r3.xyz * 2.0 - 1.0;
	float nd = (1.0 - dot(n0, n1)) + (1.0 - dot(n0, n3));
	float normal_edge = smoothstep(normal_sensitivity, normal_sensitivity + 0.25, nd);
	float edge = max(depth_edge, normal_edge);
	// Grass and flowers write roughness 1.0: never outline them.
	float grass = max(grass_of(r0), max(grass_of(r1), grass_of(r3)));
	edge *= 1.0 - grass;
	float fade = 1.0 - smoothstep(fade_start, fade_end, d0);
	ALBEDO = outline_color.rgb;
	ALPHA = edge * fade * opacity;
	if (debug_mode == 1) {
		ALBEDO = vec3(r0.a, grass, 0.0);
		ALPHA = 1.0;
	}
}
