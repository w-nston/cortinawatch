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
  - Movement: the 5057G's own cal. 240 with real finishing. Layout from the caseback photo
    (`blender/movement_from_photo.py` → `blender/movement.json`: bridge outlines, jewels, screws, the train,
    sinkings); finishes from `blender/movement_finish.py` (`textures/movement_finish_*`, `circular_graining_normal`,
    `snailing_normal`): rhodium bridges with Côtes de Genève and polished chamfers (anglage), a perlaged baseplate
    with 0.5 mm sinkings, gilt engravings lifted from the photo and recessed (PATEK PHILIPPE GENEVE SWISS,
    ADJUSTED…, 240, regulator marks). Procedural 3D gears: gold centre/third/fourth wheels (rounded teeth,
    spokes, polished hubs, circular graining), snailed steel crown wheels and ratchet. Jewels bored into the
    bridges (polished countersink, domed ruby with its oil sink); slotted screws. Balance: Gyromax-style
    glucydur rim and arm with four inertia blocks, staff in the cock, blue Spiromax-style hairspring. The 22K mini-rotor is a separate part on its own pivot
    (`movement_rotor`: gold sector with Côtes de Genève, the Calatrava cross engraved 0.12 mm deep with a matte
    floor, steel hub);
    the photo's rotor was removed and the area it covered filled with the mechanism opposite the pivot.
    Caseback window measured at r 13.4 mm. The sapphire print is still baked into the photo (it also shows,
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
  than black, with broad low softboxes for the case and bezel. The viewer lights mainly by it, with a weak key
  light for shadows.
- `dev/glb.html`: three.js viewer for the GLB (static hands; drag to rotate). Each hand is still its own node
  (`hand_hour`, `hand_minute`, `hand_seconds`, `hand_date`, `hand_power`) pivoting about local Z.
  `vendor/three/addons/loaders/GLTFLoader.js` (+ `utils/SkeletonUtils.js`) were added from three r186.

Still open for the Blender model: 5057R variant (rose gold, white dial, its own caseback photo); escape wheel
and pallet fork (not modelled); the "Cortina Watch 50th Anniversary" sapphire print as a decal on the caseback
glass (the finished movement no longer carries the photo, so the print is currently absent); strap
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

Photos shared in chat are not in the repo. Put the ones you want used or matched in
`reference/` (or `assets/` if they should ship), e.g. 5057R front/back, 5057G
front/back, the Dome Clock.
