# RuneWire asset specification

This is the contract between the asset generators (Blender, GIMP, audio scripts) and the Godot game code. **Names, sizes, pivots and node names below are load-bearing:** game code looks them up. If a spec looks wrong, say so in your report rather than silently deviating.

Read `AGENTS.md` first. It covers the machine quirks, how to run Blender and GIMP headless, and the art direction (cartoon).

## Global conventions (all 3D models)

- **Generator scripts.** Each model is built by a script, `art/blender/<category>/<asset>.py`, using `art/blender/rwlib.py`. `art/blender/parts/part_crate.py` is the reference example and sets the quality bar.
  - Run headless only (`blender --background --factory-startup --python …`).
  - Don't use the Blender MCP/GUI; it's shared.
  - Don't edit `rwlib.py`. If you need a variant of a helper, copy it into your own script or into a helper module in your category folder.
- **Script output.** End every script with `rw.finish(asset, category, icon=…)`. It writes:
  - `art/blender/<category>/<asset>.blend`
  - `assets/models/<category>/<asset>.glb`
  - preview renders in `art/previews/<category>/`
  - optionally a UI icon in `assets/icons/`

  Look at the previews with the image viewer (Read tool) and iterate until the model looks good.
- **Units and orientation.** Units are metres, and Blender +Z is up. **The front faces Blender −Y.** A character's **left** (`…L` nodes) is at Blender **+X**.
- **Clean transforms.** Every node keeps only a location; rotation and scale are applied (rwlib primitives do this for you).
  - Animated sub-parts must have their **origin at the pivot** (`rw.set_origin(obj, pivot)`), and must be parented to their parent part (`rw.set_parent`).
  - Node names must match the spec exactly; the glTF node name is the Blender object name.
  - Join static detail into as few objects as possible.
- **Materials.**
  - Use library materials `M_<Name>` (optionally tinted, `M_<Name>__rrggbb`) for anything that should get a hand-painted texture in game.
  - Use `rw.flat()` / `rw.glow()` for small flat-colour or emissive details (eyes, lamps, paint accents).
  - Library: `M_WoodPlanks M_WoodDark M_Bark M_Leaves M_Stone M_StoneRough M_Cobble M_Plaster M_RoofTiles M_Brass M_Copper M_Steel M_PaintedMetal M_DarkMetal M_Rust M_Rubber M_Leather M_Fabric M_Skin M_Glass M_RuneGlow M_TechGlow M_EmberGlow M_Crystal`.
- **UVs.** `rw.finish()` box-projects world-scale UVs (1 UV unit = 2 m), so don't unwrap by hand.
- **Style.** Cartoon:
  - Chunky, rounded shapes with exaggerated proportions and bevels on everything.
  - Readable silhouettes and lots of small charming details: rivets, bolts, straps, gears, glowing runes.
  - No realism, no thin fiddly geometry under ~1.5 cm.
- **Triangle budgets** (Godot generates LODs automatically):

  | Asset type | Max triangles |
  |---|---|
  | Parts | 6k |
  | Viewmodels | 8k |
  | Enemies | 15k |
  | Bosses | 25k |
  | NPCs | 12k |
  | Buildings | 20k |
  | Props | 4k |
  | Trees | 4k |
  | Rocks | 1.5k |
  | Grass and flowers | 300 |

- **Collision.** Parts, enemies, NPCs and viewmodels need **no collision geometry**; Godot builds it from the sizes below. **Environment and nature models need collision proxies**: simple boxes or cylinders made with `rw.collision_box()` / `rw.collision_cylinder()`. These become `-colonly` / `-convcolonly` nodes, which Godot turns into static collision.

## Batch A: build parts and first-person viewmodels

### Build parts (`art/blender/parts/`, `assets/models/parts/`, `icon=True`)

Pass `icon=True` for every part; the icon becomes the build catalogue image.

The origin is the **bounding-box centre** unless noted. Sizes are Blender X × Y × Z (width × depth × height) and must match within ±3 %, because collision is generated from them.

| Asset | Size (m) | Description and required nodes |
|---|---|---|
| `part_crate` | 1 × 1 × 1 | **Done.** The reference example. |
| `part_plank` | 2.0 × 0.5 × 0.12 | Wooden plank made of two boards with a groove, end battens and nail heads. `M_WoodPlanks`. |
| `part_beam` | 3.0 × 0.3 × 0.3 | Steel I-beam: flanges and web, rivet rows, chipped orange paint. `M_PaintedMetal` + `M_Steel` rivets. |
| `part_plate` | 2.0 × 2.0 × 0.08 | Riveted steel plate with an inset panel line and brass rivets around the border. |
| `part_platform` | 4.0 × 4.0 × 0.2 | Deck of wooden planks inside a brass trim frame, with corner bolts. |
| `part_barrel` | Ø 0.7 × 1.0 high | Volatile mana barrel: dark-wood staves, steel hoops, a glowing violet rune band (`M_RuneGlow`) and a little crystal cap on top. It looks explosive. |
| `part_glass` | 2.0 × 0.08 × 2.0 | Upright glass panel (`M_Glass`) in a brass frame (frame 0.08 thick). |
| `part_stone_block` | 1 × 1 × 1 | Chiselled stone block (`M_Stone`) with a faint rune carving (`M_RuneGlow`) on the front face. |
| `part_wheel` | Ø 0.9, width 0.3 along **X** | Chunky rubber tyre with big treads, a brass hub with 5 spokes and an axle cap. A **single mesh object named `Wheel`**, origin at the wheel centre. In Godot it spins about X. |
| `part_big_wheel` | Ø 1.6, width 0.45 along X | The same design, bigger and more rugged. Single object named `Wheel`. |
| `part_thruster` | 0.45 × 0.9 × 0.45 (long axis Y) | Brass steam/jet thruster: a rounded front cap at −Y, a body with copper coils, and a flared nozzle bell at +Y. **Empty `Exhaust`** at the nozzle exit centre. Thrust pushes the craft toward −Y (its front). |
| `part_rotor` | span Ø 2.4, hub 0.5 × 0.5 × 0.35 | Motor hub (brass/steel) at the origin. Three wooden blades with brass tips form a **separate object `Blades`**, child of the hub, origin on the spin axis (spins about Z). |
| `part_seat` | 0.8 × 0.8 × 1.2 | Pilot seat facing −Y: leather cushion, brass frame, tall backrest at +Y, two control levers in front and little dials. **Empty `SitPoint`** at the cushion top centre. |
| `part_lamp` | 0.35 × 0.35 × 0.6 | Brass lantern: glass panes, a glowing core (`M_EmberGlow`) and a ring handle on top. **Empty `LightPoint`** at the core. |
| `part_hover_stone` | 0.8 × 0.8 × 0.6 | Levitation rune stone: a chunky carved floating stone (`M_Stone`) with deep glowing rune grooves (`M_RuneGlow`) and brass bands. |
| `part_arcane_turret` | 0.7 × 0.7 × 0.9 | Brass round base. Children: **`Yaw`** (pivot at the base top centre) carrying a fork, then **`Pitch`** (child of Yaw, pivot on the fork axis) holding a crystal emitter (`M_Crystal`) with brass rings pointing −Y, then **empty `Muzzle`** (child of Pitch) at the emitter tip. |
| `part_rivet_turret` | 0.7 × 0.8 × 0.9 | Tech gatling turret. Children: base, then **`Yaw`**, then **`Pitch`**, then **`Barrels`** (child of Pitch: six-barrel cluster pointing −Y, origin on the barrel axis, spins about Y), plus **empty `Muzzle`** (child of Pitch) at the barrel tips. |
| `part_ward_pylon` | 0.6 × 0.6 × 1.7 | Stone and brass base with three brass prongs, and a floating crystal **`Crystal`** (separate object, origin at its centre, about 1.45 m up) between the prongs. |
| `part_spring_pad` | Ø 1.2 × 0.4 high | Steel base disc, a visible copper coil spring, and a red/yellow padded top. The top is a **separate object `Top`** with its origin at its centre. |

### Viewmodels (`art/blender/weapons/`, `assets/models/weapons/`, `icon=True`)

These are first-person items. **The muzzle or emitter points toward Blender −Y.** Put the origin at the **hand grip centre**.

Each one includes a chunky cartoon right-hand **glove**: brown leather with a blue sleeve cuff. The glove grips the handle, with the wrist toward +Y and slightly down. Model the glove once with a shared helper and reuse it in every script; the gauntlet is the exception, since it is the hand itself. Length is about 0.4–0.6 m (cartoon chunky).

The icon goes to `assets/icons/items/<asset>.png`.

| Asset | Description and required nodes |
|---|---|
| `vm_gauntlet` | Grav Gauntlet: the right hand in an open "grabbing" pose, palm facing −Y, fingers slightly curled. Brass/steel armour plates, a glowing teal crystal (`M_Crystal`) set in the palm, and small rings around the wrist. **Empty `Emitter`** just in front of the palm. |
| `vm_toolkit` | Rune Toolkit: a brass multitool / tuning-fork wand with a crystal lens at the front, a little dial screen on top and copper coils. The glove grips the handle. **Empty `Emitter`** at the lens tip. |
| `vm_staff` | Spell focus: a short gnarled dark-wood wand with brass ferrules and a violet crystal head (`M_Crystal__a066ff`). The glove grips it. **Empty `Emitter`** at the crystal tip. |
| `vm_arc_pistol` | Retro-futuristic pistol: brass body, copper coils, a glass tube with a glowing cyan core (`rw.glow`), wooden grip. **Empty `Muzzle`**. |
| `vm_rivet_repeater` | Chunky rivet rifle: drum magazine, steel barrel with cooling fins, brass receiver. **Empty `Muzzle`**. |
| `vm_boom_mortar` | Hand mortar: a short fat barrel (Ø about 0.16) with brass bands, a hazard stripe and a fuse. **Empty `Muzzle`**. |

## Batch B: enemies and NPCs (`art/blender/enemies|npcs/`, `icon=True`)

The **rest pose is neutral.** Animated nodes are separate objects with the origin at the joint pivot, parented exactly as listed (indentation means "child of"). Godot animates them procedurally by rotating nodes, so joints must look fine when rotated about 30–45°; add overlapping ball joints or sleeves to hide gaps.

### Magic enemies: the Hollow Choir

Their palette is violet, teal and ember, with glowing eyes and runes.

- **`enemy_wisp`** (origin at the core centre, about 0.9 m tall overall): a mischievous flame spirit. Nodes:
  - `Core`: emissive orb (`M_EmberGlow`, about 0.35 m radius).
    - `Face`: angry cartoon eyes and brows on the −Y side, dark with bright pupils.
    - `Flame_0` … `Flame_3`: teardrop flame shells (`rw.glow`, orange to yellow) rising from the core.
  - `Ember_0` … `Ember_2`: small glowing coals orbiting at about 0.6 m.
- **`enemy_golem`** (origin at the ground between the feet, about 2.8 m tall): a boulder construct held together by glowing violet rune cracks (`M_StoneRough` + `M_RuneGlow`), with moss tufts on the shoulders. Nodes:
  - `Hips` (pivot about 1.1 m)
    - `Torso` (pivot at the waist)
      - `Head` (pivot at the neck; small head sunk into huge shoulders, glowing eye slit)
      - `ArmL` (pivot at the left shoulder)
        - `ForearmL` (pivot at the elbow; big rock fist)
      - `ArmR` (pivot at the right shoulder)
        - `ForearmR` (pivot at the elbow)
    - `LegL` (pivot at the left hip; stubby rock leg)
    - `LegR`
- **`enemy_wraith`** (origin at the body centre; extends from about −1.1 m, the tattered tips, to +1.1 m, the hood top): a floating hooded shade. Dark purple tattered cloak (`M_Fabric__3b2357`), a void face with two glowing teal eyes, ghostly clawed hands. Nodes:
  - `Body`
    - `Head` (pivot at the neck)
    - `HandL` (pivot at the wrist)
    - `HandR`
- **`enemy_cultist`** (origin at the feet, about 1.9 m tall): a Choir cultist in a long crimson/dark robe (`M_Fabric__8c1c2e`, `M_Fabric__2a2233`) with a deep hood, a white porcelain mask with glowing eye slits, a belt with pouches and a rune staff. Nodes:
  - `Body` (pivot at the hips about 1.0 m; the robe reaches the ground)
    - `Head` (pivot at the neck)
    - `ArmL` (pivot at the shoulder; sleeve and hand hang down)
    - `ArmR`
      - `Staff` (in the right hand; origin at the grip)
        - empty `CastPoint` at the staff's crystal head

### Tech enemies: the Cogwork Legion

Their palette is dark iron, rust, hazard yellow/black and orange glowing eyes.

- **`enemy_drone`** (origin at the body centre, span about 1.4 m): a scout quad-drone. Nodes:
  - `Body`: round armoured shell (`M_DarkMetal`, `M_PaintedMetal`, rivets).
    - `Eye`: big glowing lens (`M_TechGlow`) facing −Y.
    - `Rotor_0` … `Rotor_3`: blade discs on four arms at the diagonals; origin at each hub, spins about Z.
    - `Gun`: under the chin; pivot at its mount.
      - empty `Muzzle`
- **`enemy_sentry`** (origin at the ground, about 1.8 m tall): a static gun turret with hazard stripes. Nodes:
  - `Base`: heavy tripod or plinth.
    - `Yaw`: pivot at the top of the base.
      - `Lamp`: warning light, glowing orange.
      - `Pitch`: pivot at the trunnion.
        - `Barrels`: twin or gatling barrels pointing −Y; origin on the barrel axis, spins about Y.
        - empty `Muzzle`
- **`enemy_crawler`** (origin at the ground under the body; body centre at about 0.55 m): a "Clank" spider-bot with a round chassis, brass trims, mandibles and three glowing eyes. Nodes:
  - `Body` (pivot at the body centre)
    - `Head`: front, eyes.
    - Six legs, `i` = 0…5, placed radially at body angles 30°, 90°, 150° on the left (+X) and right (−X) sides. Each leg:
      - `Leg{i}_Hip`: socket ball; pivot at the socket.
        - `Leg{i}_Upper`: pivot at the socket; runs outward and up at about 35°; length 0.55.
          - `Leg{i}_Lower`: pivot at the knee; runs down to a pointed foot on the ground; length about 0.75.
- **`enemy_ironclad`** (origin at the ground, about 5 m tall): the boss walker mech, made of dark iron, brass, rust, hazard paint and a glowing orange cockpit eye. Nodes:
  - `Pelvis` (pivot about 2.6 m)
    - `Torso` (pivot at the waist; it yaws)
      - `Head`: armoured cockpit with a glowing eye.
      - `ArmL` (pivot at the shoulder): a big cannon.
        - empty `MuzzleL`
      - `ArmR` (pivot at the shoulder): a rocket pod.
        - empty `MuzzleR`
      - empties `Smoke_0` and `Smoke_1` at the tops of two back smokestacks.
    - `ThighL` (pivot at the hip)
      - `ShinL` (pivot at the knee)
        - `FootL` (pivot at the ankle; big flat foot on the ground)
    - `ThighR`
      - `ShinR`
        - `FootR`

  The legs are straight-ish in the rest pose.

### NPCs (origin at the feet, facing −Y, cartoon proportions with big heads)

Each NPC uses these nodes:

- `Body`: the legs are part of it; pivot at the hips.
  - `Head`: pivot at the neck.
  - `ArmL`: pivot at the shoulder; the arm hangs down, slightly away from the body.
  - `ArmR`

The characters:

- **`npc_odda`**: Master Artificer Odda, a stout older woman. Big round brass goggles pushed up on her forehead, a grey hair bun, a leather apron over a teal shirt, a **brass mechanical right arm**, and a tool belt with wrenches. About 1.6 m tall.
- **`npc_lirael`**: Maven Lirael, the spell vendor. Tall and slender in a flowing violet robe with star and rune trim, a very tall floppy pointed hat, a long silver braid and a glowing orb hovering over her left hand. About 1.9 m tall, plus the hat.
- **`npc_gus`**: Gus Sprocket, the tinker vendor. A small, barrel-bodied **brass robot** with one big round eye lens, a tiny top hat, spindly arms with three-finger pincers and a single wheel or tank tread base. About 1.3 m tall. The legs/tread are part of `Body`.
- **`npc_brannoc`**: Captain Brannoc, the guard captain. Burly, in rune-etched plate armour (`M_Steel` + `M_RuneGlow` lines) with a big braided beard, a red cape and a sword at the hip. About 1.95 m tall.
- **`npc_villager_a`** and **`npc_villager_b`**: townsfolk in a tunic, apron or hat, with different colours and builds. About 1.6–1.8 m tall.

## Batch C: environment (`art/blender/env/`, `assets/models/env/`)

- **Origin:** at the ground centre. The front, door or entrance faces −Y.
- **Collision:** every model needs collision proxies, one or a few boxes per wall mass, built with `rw.collision_box`. Stairs and ramps can be boxes too.
- **Light points:** add empties named `LightPoint` or `LightPoint_<n>` where warm lights should go (windows, lanterns).
- **Buildings:** solid, with no interiors; doors are decorative. Use `M_Plaster`, `M_WoodDark`, `M_RoofTiles`, `M_Stone`, `M_Brass` and `M_Copper`. Windows can glow faintly (`rw.glow` with a warm colour at strength 1.5).

| Asset | Footprint × height (m) | Description |
|---|---|---|
| `bld_house_a` | 6 × 5 × about 8 | Crooked cartoon timber-frame house: two floors with a jettied upper floor, a steep wonky roof, a chimney, flower boxes and a round door. |
| `bld_house_b` | 5 × 5 × about 9 | Round stone tower-house with a conical tiled roof, a little balcony and a brass weathervane. |
| `bld_workshop` | 12 × 10 × about 10 | Odda's Workshop: big open-front hangar doors (the opening shows a dark interior plane), giant decorative gears on the facade, copper pipes, a brass chimney stack, a sign board with a gear emblem. |
| `bld_magic_shop` | 7 × 7 × about 14 | Lirael's spire: a stone tower with a teal/violet dome, floating crystals (part of the mesh), glowing rune windows and a star banner. |
| `bld_tinker_shop` | 8 × 6 × about 6 | Gus's shop: a counter under a striped awning (`M_Fabric__d94a3a`), shelves of gizmos, crates, and a big gear sign on the roof. |
| `bld_watchtower` | 5 × 5 × about 16 | Stone base, timber upper frame, a roofed lookout platform and a ladder. |
| `bld_arena_wall` | about 8 wide, 8 high, 2.5 thick | **One arc segment** of the circular arena (ring radius 30 m measured to the inner face, so the segment is curved for 24 segments per ring). Stone arches with brass ley pylons on top. The origin sits at the ground centre **of the inner face**; the inner face points −Y (toward the arena centre). |
| `bld_arena_gate` | the same arc | The same segment with a big gated archway (the opening is about 5 wide and 6 high, walkable, with collision at the sides). |
| `bld_factory_shed` | 20 × 14 × 9 | Open-sided industrial shed: steel columns and trusses, a corrugated roof (`M_PaintedMetal__8a8f95`, `M_Rust`), two closed walls at +X and +Y, hanging lamps and a big gear emblem. |
| `prop_smokestack` | Ø 3 × 20 | Brick/rusted-metal smokestack with bands, a ladder and a soot-blackened top. An empty `Smoke` sits at the top. |
| `prop_tank` | Ø 4 × 6 | Riveted industrial tank on legs, with pipes and a gauge. |
| `prop_pipes` | 6 × 2 × 3 | Cluster of copper and steel pipes with valves and wheels. |
| `prop_scrap_pile` | 4 × 4 × 1.8 | Heap of gears, plates, bolts and a broken drone shell. |
| `prop_conveyor` | 8 × 1.5 × 1.2 | Conveyor belt section with rollers and crates on it. |
| `ruin_pillar` | 1.2 × 1.2 × 5 | Broken carved column with rune bands (faint `M_RuneGlow`). |
| `ruin_arch` | 6 × 1.2 × 6 | Crumbling stone arch with a keystone rune. |
| `ruin_wall` | 6 × 1 × 3 | Broken wall segment with fallen blocks at its foot. |
| `ruin_altar` | 6 × 6 × 1.2 | Stepped altar platform with a glowing rune circle inset on top and four short pillars. |
| `ley_stone` | 1.2 × 0.8 × 3.5 | Standing stone with big glowing rune glyphs (teal) and a floating mini crystal on top. |
| `prop_fountain` | Ø 6 × 4 | Town plaza fountain: a stone basin (the water is a flat glossy disc at basin height, using `rw.flat("Water", "4fb7d9")`) and a floating ley crystal on a brass armature in the middle. |
| `prop_street_lamp` | 0.6 × 0.6 × 4 | Iron lamp post with a brass lantern holding a glowing crystal. Empty `LightPoint`. |
| `prop_market_stall` | 3 × 2 × 3 | Wooden stall with a cloth awning and goods on the counter. |
| `prop_quest_board` | 2.5 × 0.6 × 2.6 | Wooden notice board with a little roof, pinned parchment notes and wanted posters. |
| `prop_signpost` | 1 × 1 × 3 | Signpost with three plank arrows. |
| `prop_fence` | 2 × 0.2 × 1.1 | Wooden fence segment. |
| `prop_bench` | 2 × 0.6 × 0.9 | Bench. |
| `prop_well` | Ø 2 × 3 | Stone well with a roof and a bucket. |
| `prop_crate_stack` | 2 × 2 × 2 | Stack of crates and sacks. |
| `prop_barrels` | 2 × 2 × 1.2 | Group of barrels. |
| `prop_cart` | 3 × 1.6 × 1.6 | Decorative wooden cart loaded with goods. |
| `prop_bridge` | 12 × 4 × 2 | Arched wooden bridge with rails. The walkable deck needs collision, built from box segments that follow the arch. |
| `prop_banner` | 1 × 0.2 × 5 | Pole with a hanging banner (`M_Fabric__2a6fdb`) and a gear+rune emblem. |
| `prop_race_ring` | Ø 9 ring, 1 thick | Big brass hoop with glowing runes around it (inner radius 4 m). The ring stands upright; its opening faces −Y/+Y. The origin sits at the ring centre (exception: not the ground). |
| `prop_target` | 1.6 × 0.4 × 2.2 | Painted target disc (red/white/gold rings) on a brass-framed stand. |
| `prop_beacon` | Ø 2 × 3 | Floating beacon: a crystal inside spinning brass rings. The origin sits at its centre (exception). |
| `prop_goal_pad` | Ø 8 × 0.3 | Delivery zone pad: a stone disc with a glowing ring and arrows. |
| `prop_challenge_terminal` | 1.2 × 1.2 × 1.6 | Pedestal with a slanted brass console and a glowing crystal button. |

## Batch D: nature and item pickups

**Nature** (`art/blender/nature/`, `assets/models/nature/`): origin at the base centre. Trees get a trunk collision cylinder; rocks get a box or cylinder proxy.

| Asset | Description |
|---|---|
| `tree_oak` | Cartoon broadleaf tree about 7–8 m tall: a thick curvy trunk with root flares and 3–6 big puffy cloud-like canopy blobs (`M_Leaves`). |
| `tree_oak_small` | A 4–5 m variant. |
| `tree_pine` | About 9 m tall: a stack of 4–5 droopy cone tiers (`M_Leaves__3f8a4a`) on a straight trunk. |
| `tree_crystal` | Magic tree about 6 m tall: a twisted pale trunk with glowing teal crystal clusters instead of leaves (`M_Crystal`). |
| `tree_dead` | About 6 m tall: a twisted leafless spooky tree for the shrine area. |
| `bush_round` and `bush_flower` | Puffy bushes about 1.2 m. The flower variant has small pink and yellow flowers. |
| `rock_a`, `rock_b`, `rock_c` | Chunky faceted cartoon rocks, 1–2.5 m. Flat-shaded facets with soft bevels; `M_StoneRough`. |
| `cliff_a` | Big rock formation, 10 × 6 × 8 m, layered strata. |
| `grass_clump` | Cluster of 8–12 stylised tapered blades, about 0.5 m tall, `rw.flat("Grass", "6cc24a")`. **No collision.** |
| `flower_patch` | Small cluster of flowers, about 0.4 m. No collision. |
| `mushroom_cluster` | Three cartoon mushrooms with glowing teal undersides, 0.3–0.8 m. |
| `log_fallen` | Fallen log, 4 m. |
| `stump` | Tree stump. |

**Items** (`art/blender/items/`, `assets/models/items/`, `icon=True`; the icon goes to `assets/icons/items/`): origin at the centre.

| Asset | Description |
|---|---|
| `item_coin` | Gold coin, Ø 0.25 × 0.04 (oversized for readability), with a rune/gear emblem and a raised rim (`rw.flat("Gold", "ffc93c", 0.3, 1.0)`). |
| `item_coin_pile` | Leather sack spilling gold coins, 0.6 m. |
| `item_scrap_gear` | Chunky rusty gear with a bolt, Ø 0.4. |
| `item_ember_essence` | Corked glass jar with a glowing ember inside, 0.3 m. |
| `item_rune_shard` | Glowing violet crystal shard in a stone fragment, 0.4 m. |
| `item_health_tonic` | Round red potion bottle with a cork and a label, 0.3 m. |
| `item_mana_draught` | Tall blue potion flask, 0.3 m. |
| `item_ley_cargo` | Delivery cargo, 1.2 × 1.2 × 1.2: a reinforced crate with a big glowing teal crystal visible through open slats. |
| `item_chest` | Treasure chest, 1.0 × 0.7 × 0.8, with brass corners and a lock. |

## Textures (GIMP): `art/gimp/`, `assets/textures/`

All textures are made **in GIMP 3** (batch mode via `gimp-console-3`, or the GIMP MCP), from scripts kept in `art/gimp/`. Don't use Pillow or numpy outside GIMP; GIMP must do the image work. GEGL operations are available, including `gegl:normal-map`, `gegl:perlin-noise`, `gegl:simplex-noise`, `gegl:cell-noise`, `gegl:noise-solid`, `gegl:plasma`, `gegl:tile-seamless`, `gegl:bump-map`, `gegl:emboss`, `gegl:oilify`, `gegl:waves` and `gegl:ripple`; run GEGL ops through `Gimp.DrawableFilter`.

**Material sets.** Each set goes in `assets/textures/<set>/`. Every set has:

- `<set>_albedo.png`: 1024², sRGB, **seamlessly tiling**, hand-painted cartoon look.
- `<set>_normal.png`: tiling, OpenGL convention (green = up).

Sets may also have:

- `<set>_roughness.png`: greyscale.
- `<set>_emission.png`: a white-on-black mask.

The style rules:

- Paint big shapes first, then soft value variation, then a few crisp painted details and edge highlights.
- Keep high-frequency noise low.
- Colours are saturated but not neon.
- **Tintable sets (`fabric`, `painted_metal`) must be light and neutral** (albedo value about 0.85) so a tint can colour them.

| Set | Notes | Used by |
|---|---|---|
| `grass` | lush green, soft clumps, lighter strokes | terrain |
| `dirt` | warm brown, blotches, painted pebbles | terrain |
| `rock` | blue-grey faceted stone with painted cracks | terrain cliffs |
| `sand` | warm beige, soft ripples | terrain |
| `forest_floor` | dark green-brown leaf litter | terrain |
| `cobble` | rounded cobbles and dark mortar | `M_Cobble`, roads |
| `snow` | white-blue soft drifts | mountain tops |
| `wood_planks` | four planks per tile along U, dark gaps, grain, knots, edge highlights | `M_WoodPlanks` |
| `wood_dark` | dark long grain | `M_WoodDark` |
| `bark` | vertical ridges | `M_Bark` |
| `leaves` | painterly leaf clumps lit from above | `M_Leaves` |
| `stone_bricks` | soft-cornered bricks, varied tints | `M_Stone` |
| `stone_rough` | boulder stone with cracks and moss specks | `M_StoneRough` |
| `plaster` | warm off-white with soft patches | `M_Plaster` |
| `roof_tiles` | scalloped terracotta rows | `M_RoofTiles` |
| `brass` | warm brass, soft brushed streaks, grime | `M_Brass` |
| `copper` | copper with teal patina spots | `M_Copper` |
| `steel` | light brushed steel with scratches | `M_Steel` |
| `painted_metal` | neutral light paint, chipped edges showing dark metal | `M_PaintedMetal` (tinted) |
| `dark_metal` | gunmetal with worn edges | `M_DarkMetal` |
| `rust` | orange-brown rust with pitting | `M_Rust` |
| `rubber` | dark rubber with subtle texture | `M_Rubber` |
| `leather` | leather grain with stitching | `M_Leather` |
| `fabric` | neutral woven cloth (tintable) | `M_Fabric` |
| `skin` | very subtle warm skin variation | `M_Skin` |
| `rune_stone` | carved glyph blocks, plus `rune_stone_emission.png` | magic stone |
| `metal_corrugated` | corrugated panels with rust streaks | factory |
| `crystal` | internal facet gradient | `M_Crystal` |
| `water` | **normal map only** (`water_normal.png`), soft waves | lake |

**Utility textures (`assets/textures/fx/`).** All are tiling greyscale or white-on-transparent; sizes are given where they matter.

| File | Contents |
|---|---|
| `noise_perlin.png` | Perlin noise. |
| `noise_cells.png` | Cell noise. |
| `noise_clouds.png` | Soft clouds for the sky. |
| `noise_streaks.png` | Streaks for fire and energy scrolling. |
| `vfx_glow.png` | Soft radial glow. |
| `vfx_spark.png` | Four-point sparkle. |
| `vfx_smoke.png` | Cartoon puff with soft inner shading. |
| `vfx_flame.png` | Flame shape. |
| `vfx_ring.png` | Ring. |
| `vfx_rune_circle.png` | Magic circle with glyphs, 1024². |
| `vfx_lightning.png` | Bolt strip. |
| `vfx_star.png` | Cartoon star. |
| `vfx_scorch.png` | Scorch decal. |

**UI (`assets/textures/ui/`).** The theme is warm parchment plus brass, with dark slate panels for the HUD. 9-slice files must be drawn so a 48 px margin works.

| File | Contents |
|---|---|
| `ui_panel.png` | Parchment panel with brass corners, 256², 9-slice. |
| `ui_panel_dark.png` | Dark slate panel with brass trim, 256², 9-slice. |
| `ui_button.png`, `ui_button_hover.png`, `ui_button_pressed.png` | Buttons, 192×64, 9-slice. |
| `ui_slot.png`, `ui_slot_selected.png` | Hotbar slots, 128². |
| `ui_bar_frame.png`, `ui_bar_fill.png` | Bar frame and fill, 9-slice. |
| `ui_coin.png` | Gold coin icon, 128². |
| `ui_crosshair.png` | Crosshair, 64². |
| `ui_quest_marker.png`, `ui_quest_turnin.png` | Exclamation and question markers in a shield, 128². |
| `ui_title_logo.png` | "RUNEWIRE" logo, about 1400×420, transparent, using `assets/fonts/LilitaOne.ttf`: brass gradient fill, dark outline, violet/teal rune glow, a small gear or rune motif. |
| `icon_spell_arcane_bolt.png`, `icon_spell_fireball.png`, `icon_spell_chain_lightning.png`, `icon_spell_mending_ward.png` | Spell icons, 256², painted, transparent background. |
| `icon_upgrade_vitality.png`, `icon_upgrade_arcana.png`, `icon_upgrade_engineering.png`, `icon_upgrade_capacity.png`, `icon_upgrade_mana_regen.png` | Upgrade icons, 256², painted, transparent background. |

## Audio: `art/audio/`, `assets/audio/`

Synthesise everything procedurally with Python scripts in `art/audio/`. Blender's bundled Python has numpy: run `blender --background --factory-startup --python art/audio/x.py`. Do not download sounds.

- **SFX** go to `assets/audio/sfx/<name>.wav`: 16-bit, 44.1 kHz, mono, peak about −1 dBFS, short fades so nothing clicks.
- **Loops** (`*_loop`) must loop seamlessly.
- **Style:** punchy, cartoon-adventure, clean. Not harsh.

| Group | Files |
|---|---|
| UI | `ui_click`, `ui_hover`, `ui_buy`, `ui_error`, `ui_open`, `ui_close` |
| Rewards | `coin_pickup`, `coin_shower`, `quest_accept`, `quest_complete` (short fanfare), `level_up` (jingle), `notify` |
| Movement | `footstep_grass_1`…`4`, `footstep_stone_1`…`4`, `jump`, `land` |
| Spells | `spell_arcane_cast`, `spell_arcane_hit`, `spell_fireball_cast`, `explosion_fire`, `spell_lightning`, `spell_heal`, `mana_empty` |
| Weapons | `gun_arc_pistol`, `gun_rivet`, `gun_mortar`, `explosion_big`, `reload` |
| Tools | `tool_grab_loop` (hum), `tool_grab_start`, `tool_freeze`, `tool_weld`, `tool_remove`, `tool_spawn` (pop), `tool_configure` (beep) |
| Contraptions | `thruster_loop`, `engine_loop`, `rotor_loop`, `hover_loop`, `impact_wood`, `impact_metal`, `impact_stone`, `spring_boing`, `turret_arcane`, `turret_rivet` |
| Enemies | `wisp_loop`, `wisp_attack`, `golem_step`, `golem_slam`, `wraith_shriek`, `cultist_cast`, `drone_loop`, `drone_shoot`, `sentry_shoot`, `crawler_skitter`, `crawler_bite`, `ironclad_step`, `ironclad_rocket`, `hit_magic`, `hit_metal`, `death_magic` (sparkly poof), `death_tech` (crunch and pop) |
| Ambience | `amb_wind_loop`, `amb_birds_loop`, `amb_night_loop`, `amb_magic_loop`, `amb_factory_loop` |

**Music** goes to `assets/audio/music/<name>.wav`: 16-bit, 44.1 kHz, stereo, seamless loops of 60–90 s.

- `music_town`: cheerful, whimsical adventure; plucked strings, flute-like lead, soft pads, light percussion.
- `music_combat`: driving, tense but fun.
- `music_menu`: calm and magical.
