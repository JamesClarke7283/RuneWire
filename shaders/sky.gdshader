// Stylised cartoon sky: painted gradient, soft sun disc with halo, puffy two-tone clouds,
// stars and a moon at night. Colours are driven by scripts/world/day_night.gd.
shader_type sky;
render_mode use_half_res_pass;

uniform vec4 top_color : source_color = vec4(0.24, 0.50, 0.92, 1.0);
uniform vec4 horizon_color : source_color = vec4(0.70, 0.86, 1.0, 1.0);
uniform vec4 ground_color : source_color = vec4(0.36, 0.42, 0.52, 1.0);
uniform vec4 sun_color : source_color = vec4(1.0, 0.95, 0.80, 1.0);
uniform vec4 cloud_light : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform vec4 cloud_shadow : source_color = vec4(0.62, 0.68, 0.86, 1.0);
uniform sampler2D cloud_noise : filter_linear_mipmap, repeat_enable;
uniform float cloud_coverage : hint_range(0.0, 1.0) = 0.48;
uniform float cloud_speed = 0.004;
uniform float night : hint_range(0.0, 1.0) = 0.0;
uniform float sun_size = 0.035;
uniform vec3 moon_dir = vec3(0.3, 0.6, -0.7);

float hash(vec3 p) {
	return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

void sky() {
	vec3 dir = normalize(EYEDIR);
	float h = dir.y;
	vec3 col = mix(horizon_color.rgb, top_color.rgb, smoothstep(0.0, 0.55, h));
	col = mix(col, ground_color.rgb, smoothstep(0.0, -0.25, h));
	if (LIGHT0_ENABLED) {
		float sd = distance(dir, LIGHT0_DIRECTION);
		float disc = smoothstep(sun_size, sun_size * 0.82, sd);
		float halo = pow(max(1.0 - sd, 0.0), 6.0) * 0.45 + pow(max(1.0 - sd, 0.0), 40.0) * 0.6;
		col += sun_color.rgb * (disc * 3.0 + halo) * (1.0 - night);
		// warm horizon glow towards the sun
		col += sun_color.rgb * 0.25 * pow(max(dot(dir, LIGHT0_DIRECTION), 0.0), 3.0) * (1.0 - smoothstep(0.0, 0.4, h));
	}
	if (night > 0.0 && h > 0.0) {
		vec3 sp = floor(dir * 220.0);
		float star = step(0.9965, hash(sp)) * smoothstep(0.0, 0.25, h);
		float tw = 0.6 + 0.4 * sin(TIME * 3.0 + hash(sp + 3.1) * 40.0);
		col += vec3(1.0, 0.97, 0.9) * star * tw * night * 1.4;
		float md = distance(dir, normalize(moon_dir));
		col += vec3(0.95, 0.95, 1.0) * smoothstep(0.045, 0.04, md) * night * 1.6;
		col += vec3(0.4, 0.5, 0.9) * pow(max(1.0 - md, 0.0), 30.0) * night * 0.4;
	}
	if (h > 0.0 && !AT_CUBEMAP_PASS) {
		vec2 cuv = dir.xz / (h + 0.18) * 0.22;
		vec2 drift = vec2(TIME * cloud_speed, TIME * cloud_speed * 0.4);
		float n = texture(cloud_noise, cuv + drift).r * 0.65 + texture(cloud_noise, cuv * 2.3 - drift * 1.7).r * 0.35;
		float body = smoothstep(1.0 - cloud_coverage, 1.0 - cloud_coverage + 0.08, n);
		float n2 = texture(cloud_noise, cuv + drift + vec2(0.012, 0.02)).r * 0.65 + texture(cloud_noise, (cuv + vec2(0.012, 0.02)) * 2.3 - drift * 1.7).r * 0.35;
		float lit = smoothstep(1.0 - cloud_coverage + 0.02, 1.0 - cloud_coverage + 0.16, n2);
		vec3 ccol = mix(cloud_shadow.rgb, cloud_light.rgb, lit);
		ccol = mix(ccol, ccol * 0.35 + vec3(0.05, 0.06, 0.12), night);
		float fade = smoothstep(0.0, 0.18, h);
		col = mix(col, ccol, body * fade * 0.95);
	} else if (h > 0.0 && AT_CUBEMAP_PASS) {
		col = mix(col, cloud_light.rgb * (1.0 - night * 0.7), 0.15 * smoothstep(0.0, 0.3, h));
	}
	COLOR = col;
}
