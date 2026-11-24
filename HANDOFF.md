# Cortina Watch × Patek Philippe: 3D gallery (work in progress)

A scroll-driven 3D walk through the Cortina Watch / Patek Philippe story, built
with three.js (vendored, no build step). Copy is in `js/content.js`, sourced from
https://www.cortinawatch.com/en/patek-philippe/patek-philippe-cortina-watch/.

## Run locally

```bash
python3 -m http.server 8000
```

- Watch studio test page: http://localhost:8000/dev/watch.html?v=5057G&view=front
  - `v` = `5057G` | `5057R`
  - `view` = `front` | `back` | `angle` | `backangle` | `macro` | `side`
  - `time` = ISO time to freeze the hands, e.g. `2026-11-24T02:09:30Z`
- Dial texture only: http://localhost:8000/dev/dial.html?v=5057G (`mode=orm` shows the roughness/metalness map)

## Done

- `vendor/three/`: three.js r186 (minified) + RoomEnvironment, BufferGeometryUtils, RoundedBoxGeometry.
- `js/lib/geo.js`, `js/lib/materials.js`: adapted from w-nston/3DWatch.
- `js/cal240.js`: calibre 240 bridge side. The real movement photo
  (`assets/cal240-back.webp`, from 3DWatch) is projected onto 3D plate, bridges and
  mini-rotor. The photo's luminance drives roughness and normal maps. 3D going train,
  3 Hz balance + hairspring, moving mini-rotor and 3D rubies are placed on the
  jewels detected in the photo. `setExplode(0..1)` is there for the "craft" room.
  The movement is rotated 180° in the 5057 to match the 5057G/5057R caseback photos
  (crown left, rotor right, balance at 6 seen from the back).
- `js/watch5057.js`: 5057G and 5057R in mm. Case, polished bezel with instanced
  hobnail pyramids (4 rows × 228), straight lugs, fluted crown, domed sapphire.
  Printed dial drawn on canvas from measurements of the 5057G photo (Roman numerals,
  power reserve 0–48 h, pointer date + moon window, small seconds, railway, SWISS);
  anisotropic sunburst on the G. 3D faceted leaf hands with live Singapore time and
  the real date and moon phase. Sapphire caseback with the translucent print
  ("Cortina Watch / 50th Anniversary / Since 1972" on the G, "CORTINA JUBILEE
  WATCH" arc on the R), 8 pads on the caseback ring, croc-textured straps.
- `js/studio.js`: dark softbox reflection environment for photoreal metal.
- `js/textures.js`: gallery textures (walls, floor, wall lettering, dome enamel, map).
- `js/content.js`: all 14 chapters of copy.

## Blender model of the 5057G (replaces the procedural three.js case)

The 5057G is now modelled in Blender (driven over the Blender MCP) and exported as
`assets/models/5057G.glb` (8.2 MB, WebP textures, three animation clips). It is measured
from the photos in `watch photos/5057G/` and the published specs (36.15 mm, 9.14 mm high).
The hands are **static**, posed exactly where they stand in the dial photo (10:09, date 20, ~39 h of
reserve). The movement runs: the GLB carries three looping clips over the same 8 s (60 fps):
`rotor_spin` (22K mini-rotor, one turn), `balance_swing` (3 Hz / 21,600 vph, ~270° amplitude, 24 swings)
and `hairspring_breathe` (morph weights: the coils wind and unwind with the balance, 18 shape keys every
30° blended pairwise). `dev/glb.html` plays them all with an `AnimationMixer`.

- `blender/build_5057.py`: rebuilds the whole watch into the `Watch5057G` collection. Run in
  Blender with `exec(open(".../blender/build_5057.py").read(), {"__name__": "__main__", "CORTINA_ROOT": "/path/to/cortinawatch"})`.
  - Case: 36.15 mm bezel with 4 rows × 88 real hobnail pyramids on a 32° cone, 4 mm polished flank,
    2.5 mm brushed caseback with the 6 opening notches (60° apart) and sapphire window,
    angular lugs (20 mm strap), 5.5 mm crown sitting low across the joint (plain polished dome on a short
    scalloped collar, as in the side photos; no Calatrava cross on this model), correctors at about 4 and 8.
  - Dial: the real dial, from `blender/textures/dial_5057G_photo_color.jpg` + `_orm.png` (see below). The metal
    is 3D: applied white-gold Roman numerals traced stroke by stroke from the photo (raised 0.22 mm, satin top,
    bevelled), and the moon phase as its own part (`moon_disc`: navy lacquer disc with frosted moons and
    stars in relief) under the measured scalloped window. Faceted leaf hands sized from the photo and posed as
    photographed (`POSE`); sub-dial pivots fitted to the printed scales (power reserve −6.273, 6.279; date
    −3.529, −6.128; seconds 7.369, −6.272). `blender/dial_features.py` → `blender/dial_features.json`.
  - Movement: the 5057G's own cal. 240 with real finishing. Parts are named with Patek Philippe's numbers
    from the Calibre 240 parts diagram (105 barrel bridge, 110 train bridge, 1149 automatic bridge, 121
    balance cock, 125 pallet bridge, 1143 rotor + 51143 screw, 1481 reduction wheel, 1480 and 1497 steel
    wheels + 51497 screws seen through the rotor's holes, 200/1 centre wheel, 220 fourth wheel, 702 club-tooth
    escape wheel, 710 pallet fork with its two pallet stones, 415 barrel, 210 third and 220 fourth wheels). Bridge outlines are traced on the photograph by
    seeded watershed (`blender/trace_movement.py` → `blender/movement_parts.json`); screws found by circle
    detection and checked by eye. `refine_bridge()` in `movement_from_photo.py` then adds what the tracer cannot
    see (shapely): the barrel bridge's curved cutout at 9 o'clock beside "SWISS" (a round bite through the edge,
    sunk on into the plate as a shadowed recess), every bridge running on to the window where the photo blurs,
    the balance cock's clean round head and its arm on under the rotor to the rim (as in the parts diagram),
    the pallet bridge 125 (the crescent with two small screws) kept clear of the head, and a pit of r 7.35 round
    the rotor's pivot that no bridge enters: the rotor turns in it, its face flush with the bridges.
    Details read on 1 mm-gridded close-ups: gold chatons (barrel arbor bushing with its steel pivot, the train
    bridge's jewel, the balance jewel under its shock spring), polished steady-pin holes, a missed ruby, the
    cock head's two small screws. Layout from the caseback photo
    (`blender/movement_from_photo.py` → `blender/movement.json`: bridges, jewels, screws, the train,
    sinkings); finishes from `blender/movement_finish.py` (`textures/movement_finish_*`, `circular_graining_normal`,
    `snailing_normal`): rhodium bridges with Côtes de Genève as measured on the photo (straight bands 2.6 mm wide,
    edges aligned across all bridges at photo-view x = 2.0 + 2.6 k, each band a shallow cylinder so it runs
    bright to dark, with the grinding wheel's hairlines; normal maps dithered against 8-bit banding) and
    polished chamfers (anglage), a perlaged baseplate
    with 0.5 mm sinkings, gilt engravings lifted from the photo and recessed (PATEK PHILIPPE GENEVE SWISS,
    ADJUSTED…, 240, regulator marks). Procedural 3D gears: gold centre/third/fourth wheels (rounded teeth,
    spokes, polished hubs, circular graining), snailed steel crown wheels and ratchet. Jewels bored into the
    bridges (polished countersink, domed ruby with its oil sink); slotted screws. Balance: Patek's Gyromax,
    measured on the photo (radial and angular profiles of its gold): rim outer r 3.95, 0.24 wide; four arms at
    photo-view 82° + 90° k, ~0.45 mm wide widening to 0.6 at the weights; at each arm a weight (masselotte)
    0.66 mm across centred 3.05 mm out, a slotted gold ring round a bright domed pin with a dark gap (it reads
    as a "G", as photographed), slots set different ways; double roller with ruby impulse pin, staff in the
    cock, Spiromax-style hairspring (12 turns, r 0.45–2.2) over the arms ending at its black stud under the
    cock's edge. The balance and escapement sit in a pit 0.6 mm under the sinkings (`movement_pit_floor`,
    darker: in shadow as photographed). Escapement (`escapement_layout()` in `movement_from_photo.py`, read on
    the photo with the parts diagram): escape wheel 702 (20 club teeth, tips r 2.25, darker steel) on the train
    bridge's gold chaton (-4.77, -7.66 photo view: its jewel, 2.9 mm from the seconds wheel's jewel); pallet
    lever 710 pivoting in the round jewel left of the balance (-2.22, -8.59), fork reaching the impulse pin;
    exit stone flat in its "⊐" socket at (-2.65…-2.17, -7.72), entry stone long and upright, its back in a
    socket at (-2.9, -10.1) and its tip under the balance weight; pallet bridge 125 as in the diagram, a ring
    round the roller with a lobe for the pallet jewel, lying under the balance (its two screws flat, clear of
    the arms). Stack, deepest first: pit floor, escape wheel and stones, lever, pallet bridge, balance,
    hairspring, cock. The train, from circles fitted to the gold teeth seen past the bridges (residuals
    < 0.05 mm): the long toothed arc beside "ADJUSTED" is the barrel 415's gilt rim (steel drum, on the
    barrel bridge's bushing, teeth r 5.4); it drives the centre wheel 200 (-3.62, -0.91, r 2.67; centres
    6.4 mm apart); 210 third wheel (-3.02, -3.32); 220 fourth wheel on the train bridge's jewel (-7.14,
    -6.06, r 2.56, meshing with the escape pinion), its arbor carrying the small seconds; 1481 reduction
    wheel. All are whole wheels hidden by the plate and bridges where the photo shows them hidden.
    Animated with the balance (clips `escape_wheel_step`, `pallet_lever_flip`): at every beat
    (6 a second) the lever flips ±7° and the wheel steps half a tooth (9°); 48 beats in the 8 s loop. At t = 0 the balance stands exactly as
    photographed (the photo is ~17° off axis, so in it the cock, 0.9 mm nearer the lens, sits ~0.2 mm off the
    rim's centre; the model keeps the jewel on the balance's axis). The 22K mini-rotor is a separate part on its own pivot (`movement_rotor`,
    pivot 6.47, 0.06: half-disc with Côtes de Genève 2.57 mm wide, an edge on its axis, the Calatrava cross cut
    0.12 mm deep with a bright satin floor, a small hub notch for the polished steel hub and screw 51143, and
    its own two slotted screws in countersunk holes near the straight edge, turning with it); its
    ball bearing (dark ring with four notches round a satin race) stays fixed in the plate. The rotor's top
    layer bevel hardens its normals (an un-hardened bevel shaded a seam across the big face);
    the photo's rotor was removed and the area it covered filled with the mechanism opposite the pivot.
    Caseback window measured at r 13.4 mm. The anniversary print "Cortina Watch / 50th Anniversary / Since
    1972" sits on the sapphire's inside face (`caseback_print`, texture from `blender/caseback_print.py`):
    an old-style serif with descending 9 and 7 (Hoefler Text, as the SJX close-ups show), em 3.03 mm,
    baselines 1.7 / -1.075 / -4.15 and centres x ≈ 0.65 (photo view), fitted to the print where it reads
    over the gold rotor and the plate; white at 45 % (the movement shows through it, as photographed). The sapphire print is still baked into the photo (it also shows,
    upside down and faint, in the area under the rotor).
  - Strap: swept alligator (procedural scale normal map from `blender/gen_croc.py`) with brown calf lining
    (sampled from the clasp photos), curved back 108° as on a display cushion so the caseback stays visible
    from behind. Folding clasp as photographed (`watch photos/5057G/clasp-*`): 16 mm polished frame with a
    pointed hinge tab and pin, the openwork Calatrava cross traced from the close-up (`blender/trace_cross.py`
    → `blender/calatrava_cross.json`, symmetrised over its 8 symmetries) with its tips let into the frame,
    two keepers, the folding blade.
- `blender/dial_from_photo.py` (system python: numpy, scipy, Pillow): builds the dial texture from two photos.
  The straight-on `AS…--1_….webp` is rectified to dial millimetres (`blender/dial_register.py` fits the
  railway line and bezel edge: 34.4 px/mm, 2.8 % vertical foreshortening, 0.77° turn).
  `dial-angle-hands-elsewhere.webp` (hands in other places) is mapped onto it by a homography from nine
  numeral strokes (≤ 0.25 px residual) and fills in, gradient-blended, wherever only the main photo has a hand.
  Where both photos have a hand (hour hand, hubs, inner date hand) the dial is filled smoothly with sunburst
  streaks and the print rebuilt from its own repeats (power-reserve dots, date dots, the "2" of "24" from "12",
  the X's arm); those spots sit under the static hands. Takes ~4 minutes.
- `blender/studio.py`: preview lights/camera (the `Studio` collection, not exported).
- `blender/export_glb.py`: writes the GLB. Axes are kept as in Blender (no Y-up conversion), 1 unit = 1 mm,
  so it uses the same frame as `js/watch5057.js` (+X crown, +Y 12, +Z out of the dial).
- `blender/5057G.blend`: the saved scene (textures linked from `blender/textures/`).
- `dev/bake.html`: re-bakes the canvas-drawn dial/moon/caseback-print textures from the JS code (no longer
  used by the 5057G build; kept for the 5057R). It needs a server that accepts `POST /save?name=…`.
- Materials for three.js: the sapphires are a thin transparent coat (alpha 0.1), not transmission (three.js's
  transmission pass re-rendered the movement washed out); brushed parts carry no anisotropy (the lathed meshes
  have no UVs, and three.js smeared the highlight over the whole caseback).
- `js/studio.js`: the reflection/lighting studio is now lit on both sides (dial and caseback), dark grey rather
  than black, with broad low softboxes for the case and bezel, and a soft "light tent" panel behind the viewer
  of the caseback (face-on plates, rotor and balance reflect a soft white, as in the retail photographs). The viewer lights mainly by it, with a weak key
  light for shadows.
- `js/rotor_physics.js`: the mini-rotor moved by the watch, as on the wrist: a damped pendulum about its
  pivot (centre of mass 4R/3π off it, on the rotor's local -Y), driven by gravity in the watch's frame, the
  watch turning about its own axis (inertia) and the watch's acceleration (jolts). It reads all three from
  the rotor's parent each frame, so any motion of the watch works. Swing slowed to ~9 rad/s so it reads
  (a real rotor is ~35), damping ratio 0.07. Used by `dev/glb.html` (in place of the GLB's `rotor_spin`
  clip, which stays in the file) and by `js/cal240.js` (in place of its sine-wave "wrist motion").
- `dev/glb.html`: three.js viewer for the GLB (static hands; drag to rotate; shift-drag turns the watch
  about its own axis, and the rotor follows). `?zoom=5&at=x,y` moves the camera
  5× closer, aimed at (x, y) in the watch frame (mm), for close-ups of the movement; `?t=0` freezes the
  movement at that time (s): at 0 the rotor and balance stand as photographed. Each hand is still its own node
  (`hand_hour`, `hand_minute`, `hand_seconds`, `hand_date`, `hand_power`) pivoting about local Z.
  `vendor/three/addons/loaders/GLTFLoader.js` (+ `utils/SkeletonUtils.js`) were added from three r186.

Still open for the Blender model: 5057R variant (rose gold, white dial, its own caseback photo); strap
holes; engraving on the clasp blade; tune materials under the gallery's own lighting (the dev viewer's dark
environment makes the movement read paler than in Blender); swap `build5057('5057G')` for the GLB in the gallery.

## Next steps

1. **Watch polish** (compare against the reference photos, see below):
   - Strap reads too white: lower clearcoat/env intensity, drop sheen.
   - Chapter ring: in `drawDial` 'orm' mode, paint the ring band non-metallic so it
     stays black (it currently picks up the metallic base and looks grey).
   - Roman numerals: slightly bolder (stroke the glyphs ~0.1 mm) to match the photos.
   - Check `view=back` and `view=backangle`: movement, print legibility, pads.
   - 5057R: the 1997 movement has older-generation bridges. To match exactly, save a
     high-resolution 5057R caseback photo to `assets/` and project it like `cal240.js`.
2. **Gallery** (not written yet): `index.html`, `css/style.css`, `js/main.js`
   (hall, scroll-driven camera with dwell at each chapter, HTML text panels, chapter
   nav, click-to-inspect with drag-to-rotate + caseback flip), `js/exhibits.js`
   (arch, 1956 meeting chairs, retailer plaque, balance wheel, shop-in-shop models,
   Marina Bay Sands model, ION salon diorama, Dome Clock, exploded cal. 240,
   SE Asia map table, finale). Planned layout: hall along −Z, bays alternating left and
   right every 9 m, watches scaled ~0.014 (36 mm → 0.5 m sculpture).
3. Deep links (`#5057g`), `?embed=1` to hide the header for iframes, WebGL fallback
   that shows the text as a plain article.

## Reference photos

- `watch photos/5057G/`: the 5057G (front, sides, caseback, dial at an angle, clasp close-ups).
- `watch photos/240 movement.jpg`: Patek Philippe's exploded parts diagram of the Calibre 240, the source
  of the part numbers used for the movement's objects (105, 110, 1149, 121, 125, 1143, 1481, 1497, 702, 710…).

Photos shared in chat are not in the repo. Put the ones you want used or matched in
`reference/` (or `assets/` if they should ship), e.g. 5057R front/back, 5057G
front/back, the Dome Clock.
