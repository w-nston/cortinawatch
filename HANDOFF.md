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
