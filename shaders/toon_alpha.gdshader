shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back;

#define TOON_ALPHA
#include "res://shaders/toon_core.gdshaderinc"
