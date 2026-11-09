// Shared cartoon lighting for every RuneWire surface shader.
// Two soft bands plus a bright cap, cool tinted shadows (key light leaks a tinted fill into the
// shadow side), a coloured rim on the lit side and a crisp toon specular blob.

uniform vec4 shadow_color : source_color = vec4(0.40, 0.38, 0.62, 1.0);
uniform float shadow_light : hint_range(0.0, 1.0) = 0.30;
uniform float band_softness : hint_range(0.001, 0.5) = 0.05;
uniform float mid_band : hint_range(0.0, 1.0) = 0.78;
uniform float rim_strength : hint_range(0.0, 2.0) = 0.28;
uniform float rim_width : hint_range(0.0, 1.0) = 0.32;
uniform float specular_strength : hint_range(0.0, 2.0) = 0.22;
uniform float metallic_look : hint_range(0.0, 1.0) = 0.0;
uniform float glossiness : hint_range(0.0, 1.0) = 0.3;

void light() {
	float ndl = dot(NORMAL, LIGHT);
	float band = smoothstep(0.0, band_softness, ndl);
	float atten = LIGHT_IS_DIRECTIONAL ? smoothstep(0.25, 0.75, ATTENUATION) : ATTENUATION;
	float lit = band * atten;
	float tone = mix(mid_band, 1.0, smoothstep(0.42, 0.42 + band_softness, ndl));
	vec3 lc = LIGHT_COLOR / PI;
	vec3 diffuse;
	if (LIGHT_IS_DIRECTIONAL) {
		diffuse = lc * mix(shadow_color.rgb * shadow_light, vec3(tone), lit);
	} else {
		diffuse = lc * lit * tone;
	}
	diffuse *= 1.0 - metallic_look * 0.3;
	float ndv = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float rim = smoothstep(1.0 - rim_width, 1.0 - rim_width + 0.06, 1.0 - ndv);
	rim *= rim_strength * smoothstep(-0.1, 0.35, ndl) * atten;
	DIFFUSE_LIGHT += diffuse + lc * rim;
	vec3 h = normalize(LIGHT + VIEW);
	float shin = mix(10.0, 160.0, glossiness);
	float spec = pow(max(dot(NORMAL, h), 0.0), shin);
	float specb = smoothstep(0.45, 0.55, spec) * specular_strength * lit;
	SPECULAR_LIGHT += lc * specb * mix(vec3(1.0), ALBEDO * 1.6, metallic_look);
}
