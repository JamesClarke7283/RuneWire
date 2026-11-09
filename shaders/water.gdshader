// Stylised water: depth-tinted colour, painted foam lines along shores, gently moving normals
// and a sparkly toon highlight.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, specular_toon;

uniform sampler2D depth_texture : hint_depth_texture, filter_linear;
uniform sampler2D screen_texture : hint_screen_texture, filter_linear_mipmap;
uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap, repeat_enable;
uniform bool has_normal_tex = false;
uniform vec4 shallow_color : source_color = vec4(0.32, 0.82, 0.86, 1.0);
uniform vec4 deep_color : source_color = vec4(0.10, 0.36, 0.62, 1.0);
uniform vec4 foam_color : source_color = vec4(0.95, 0.98, 1.0, 1.0);
uniform float depth_scale = 3.5;
uniform float foam_width = 0.9;
uniform float wave_speed = 0.03;

varying vec3 v_world;

void vertex() {
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	VERTEX.y += sin(v_world.x * 0.25 + TIME * 1.2) * 0.04 + cos(v_world.z * 0.3 + TIME) * 0.04;
}

void fragment() {
	float d = texture(depth_texture, SCREEN_UV).r;
	vec4 vp = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	float scene_depth = -vp.z / vp.w;
	float water_depth = scene_depth - (-VERTEX.z);
	float t = clamp(water_depth / depth_scale, 0.0, 1.0);
	vec3 col = mix(shallow_color.rgb, deep_color.rgb, smoothstep(0.0, 1.0, t));
	vec2 uv1 = v_world.xz * 0.06 + vec2(TIME * wave_speed, TIME * wave_speed * 0.6);
	vec2 uv2 = v_world.xz * 0.09 - vec2(TIME * wave_speed * 0.7, TIME * wave_speed);
	float n = texture(noise_tex, uv1).r * 0.5 + texture(noise_tex, uv2).r * 0.5;
	float foam_line = smoothstep(foam_width, foam_width * 0.4, water_depth + (n - 0.5) * 0.6);
	float ripples = smoothstep(0.66, 0.70, n) * 0.35 * (1.0 - t * 0.5);
	col = mix(col, foam_color.rgb, clamp(foam_line + ripples, 0.0, 1.0));
	ALBEDO = col;
	ALPHA = mix(0.7, 0.95, t);
	ALPHA = max(ALPHA, foam_line);
	ROUGHNESS = 0.08;
	METALLIC = 0.0;
	SPECULAR = 0.6;
	if (has_normal_tex) {
		NORMAL_MAP = mix(texture(normal_tex, uv1 * 2.0).rgb, texture(normal_tex, uv2 * 2.0).rgb, 0.5);
		NORMAL_MAP_DEPTH = 0.5;
	}
}
