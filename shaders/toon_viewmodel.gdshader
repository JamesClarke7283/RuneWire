shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, shadows_disabled;

#define TOON_VIEWMODEL
#include "res://shaders/toon_core.gdshaderinc"
