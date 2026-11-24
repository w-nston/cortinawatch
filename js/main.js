// The Anniversary Watches (index.html). One watch fills the screen, and it is two watches: a seam runs
// down it, the 1997 Ref. 5057R (rose gold, white dial) on its left and the 2022 Ref. 5057G (white gold,
// slate dial) on its right, the same model twenty-five years apart. Slide the seam to cross the years;
// turn the watch, zoom into it, look at the movement through the strap's loop, or lay it down and take
// it apart (Anatomy). Its hands keep Singapore time.
//
// The watches are the Blender builds (assets/models/5057R.glb, 5057G.glb, blender/build_5057.py), in
// millimetres, +Z out of the dial, +Y toward 12 o'clock, built in the same frame, so the two line up part
// for part. The seam is a clipping plane through the eye: each watch keeps its own side of it.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { studioEnvironment } from './studio.js?v=4';
import { RotorPhysics } from './rotor_physics.js?v=1';
import { site, chapters, watches } from './content.js?v=3';   // bump ?v= when the copy changes (browsers cache modules)

const $ = (s) => document.querySelector(s);
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (x) => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };
const damp = (a, b, k, dt) => a + (b - a) * (1 - Math.exp(-k * dt));
const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));

const W = Object.fromEntries(watches.map((w) => [w.id, w]));
const SYNODIC = 29.530588853;                      // days from new moon to new moon
const LEFT = W['5057r'], RIGHT = W['5057g'];       // left of the seam 1997, right of it 2022
const stage = $('#vitrine'), canvasBox = $('#stage');

// ------------------------------------------------------------------ captions and the history sheet
const captions = $('#captions'), sheet = $('#sheet'), plaque = $('#plaque');
for (const w of [LEFT, RIGHT]) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'cap';
  b.dataset.id = w.id;
  b.innerHTML = `<span class="cap-yr">${w.year}</span><span class="cap-ref">${w.label}</span><span class="cap-more">Its story</span>`;
  b.setAttribute('aria-label', `${w.year}, ${w.label}: show this watch and read its story`);
  b.addEventListener('click', () => { showWhole(w.id); openSheet(w); });
  captions.append(b);
}
// photographs from the Cortina Watch page (assets/cortina/)
const photo = (im, eager = false) => im ? `<figure class="photo"><img src="${im.src}" alt="${im.alt}" width="${im.w}" height="${im.h}"${eager ? '' : ' loading="lazy"'} decoding="async"></figure>` : '';
const plaqueHTML = (w) => `
  ${photo(w.image, true)}
  <p class="kicker">${w.kicker}</p>
  <h2 id="sheet-title">${w.title}</h2>
  ${w.history.map((p) => `<p>${p}</p>`).join('')}
  <dl>${w.details.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>`;
let sheetFor = null;
function openSheet(w) {
  plaque.innerHTML = plaqueHTML(w);
  sheet.hidden = false;
  sheet.scrollTop = 0;
  sheetFor = w.id;
  vitrine?.relayout();
}
function closeSheet() {
  if (sheet.hidden) return;
  sheet.hidden = true;
  sheetFor = null;
  vitrine?.relayout();
}
$('#sheet-close').addEventListener('click', closeSheet);
addEventListener('keydown', (e) => { if (e.key === 'Escape') closeSheet(); });

// ------------------------------------------------------------------ the vitrine
const vitrine = createVitrine();
function showWhole(id) { vitrine?.setSeam(id === LEFT.id ? 1 : 0); }

function createVitrine() {
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  } catch {
    stage.classList.add('no-webgl');
    $('#loader').hidden = true;
    return null;
  }
  const small = Math.min(screen.width, screen.height) < 600;
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);               // the room is the page's own brown (css)
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.localClippingEnabled = true;               // the seam
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const canvas = renderer.domElement;
  canvas.setAttribute('role', 'img');
  canvas.setAttribute('aria-label', 'The Ref. 5057 in 3D: the 1997 rose gold watch on the left of the seam, the 2022 white gold watch on its right. Drag to turn it.');
  canvasBox.append(canvas);

  const scene = new THREE.Scene();
  scene.environment = studioEnvironment(renderer, { warm: true });   // softboxes both sides, a warm room
  const camera = new THREE.PerspectiveCamera(24, 1, 5, 4000);
  // a spot above the visitor's shoulder: sparkle on the hobnails, the hands' shadows on the dial
  const spot = new THREE.SpotLight(0xfff2e2, 1.6, 0, 0.42, 0.9, 0);
  spot.position.set(-140, 260, 330);
  spot.castShadow = true;
  spot.shadow.mapSize.setScalar(small ? 1024 : 2048);
  spot.shadow.bias = -0.0002;
  spot.shadow.normalBias = 0.2;
  spot.shadow.camera.near = 200;
  spot.shadow.camera.far = 700;
  scene.add(spot, spot.target);

  // pivot: turns the watch about one of its own points (the case's centre; the stack's when taken apart)
  const pivot = new THREE.Group();
  const holder = new THREE.Group();
  pivot.add(holder);
  scene.add(pivot);

  // the seam: a plane through the eye and a vertical line on the screen
  const planeL = new THREE.Plane(), planeR = new THREE.Plane();

  // ---- taking it apart: each top-level part moves along the watch's axis by its layer
  const LAYERS = [   // [test, offset mm]: outermost first
    [/^crystal$/, 34], [/^bezel/, 25], [/^hand_/, 17], [/^(dial|numeral_|moon_|rehaut)/, 9],
    [/^(case_middle|lug_|crown|corrector|springbar_|casing_ring)/, 0],
    [/^(movement_plate|movement_sink_floor|movement_pit_floor)/, -10],
    [/^(200_|210_|220_|415_|1480_|1481_|1497_|escape_wheel|pallet_lever|balance|hairspring)/, -17],
    [/^(105_|110_|121_|125_|1149_|screw_|jewel|chaton_|pin_hole_)/, -25],
    [/^(movement_rotor|1143_)/, -33],
    [/^caseback/, -44],
  ];
  const STRAP = /^(strap_|clasp_)/;                  // fades away as the watch is laid down
  // the parts, top to bottom, as the visitor can pick them out: [test on the node's name, key, name,
  // Patek Philippe part number (the calibre 240 parts diagram), a line about it]
  const PARTS = [
    [/^crystal$/, 'crystal', 'Sapphire crystal', '', 'The domed sapphire over the dial.'],
    [/^bezel/, 'bezel', 'Hobnail bezel', '', 'Rows of tiny pyramids, the hobnail or Clous de Paris pattern, that catch the light as the wrist turns.'],
    [/^hand_hour/, 'hand_hour', 'Hour hand', '', 'A faceted leaf hand, set here to Singapore time.'],
    [/^hand_minute/, 'hand_minute', 'Minute hand', '', 'A faceted leaf hand, set here to Singapore time.'],
    [/^hand_seconds/, 'hand_seconds', 'Small seconds hand', '', 'At four o’clock, stepping six times a second with the balance.'],
    [/^hand_power/, 'hand_power', 'Power reserve hand', '', 'Shows how much of the mainspring’s 48 hours is left.'],
    [/^hand_date/, 'hand_date', 'Date hand', '', 'Points to the date, round the moon phase at seven o’clock.'],
    [/^dial$/, 'dial', 'Dial', '', 'Power reserve at half past ten, pointer date and moon phase at seven, small seconds at four.'],
    [/^numeral_/, 'numerals', 'Applied numerals', '', 'Roman numerals in white gold, applied to the 2022 dial; the 1997 dial has them printed.'],
    [/^moon_/, 'moon', 'Moon phase disc', '', 'Two moons on a starry disc that turns behind the window at seven o’clock.'],
    [/^rehaut/, 'rehaut', 'Rehaut', '', 'The ring between the dial and the crystal.'],
    [/^(case_middle|lug_)/, 'case', 'Case middle and lugs', '', 'The case, 36 mm across, with straight lugs for a 20 mm strap.'],
    [/^crown/, 'crown', 'Crown', '', 'Winds the mainspring by hand and sets the time.'],
    [/^corrector/, 'correctors', 'Correctors', '', 'Recessed in the case flank, for setting the date and the moon phase.'],
    [/^springbar_/, 'springbars', 'Spring bars', '', 'Hold the strap between the lugs.'],
    [/^casing_ring/, 'casing_ring', 'Casing ring', '', 'Holds the movement in the case.'],
    [/^movement_(plate|sink_floor|pit_floor)/, 'plate', 'Mainplate', '', 'The calibre’s foundation, its surface grained with perlage.'],
    [/^415_/, '415', 'Barrel', '415', 'Holds the mainspring that drives the watch, for up to 48 hours.'],
    [/^200_/, '200', 'Centre wheel', '200', 'The first wheel of the going train, driven by the barrel.'],
    [/^210_/, '210', 'Third wheel', '210', 'Carries the power on from the centre wheel to the fourth.'],
    [/^220_/, '220', 'Fourth wheel', '220', 'Turns once a minute and carries the small seconds.'],
    [/^escape_wheel/, 'escape', 'Escape wheel', '702', 'Lets the train turn one tooth at a time, six times a second.'],
    [/^pallet_lever/, 'pallet', 'Pallet lever', '710', 'Locks and unlocks the escape wheel and gives the balance its impulse.'],
    [/^balance/, 'balance', 'Gyromax balance', '', 'Swings at 3 Hz, 21,600 times an hour, timed by the weights on its rim rather than a regulator.'],
    [/^hairspring/, 'hairspring', 'Hairspring', '', 'Coils and uncoils with every swing of the balance.'],
    [/^(1480|1481|1497)_/, 'winding', 'Winding wheels', '1480 · 1481 · 1497', 'Carry the mini-rotor’s turns down to the barrel.'],
    [/^105_/, '105', 'Barrel bridge', '105', 'Holds the barrel. Côtes de Genève, and the gilded engraving PATEK PHILIPPE GENEVE.'],
    [/^110_/, '110', 'Train bridge', '110', 'Holds the going train. Côtes de Genève, engraved and gilded.'],
    [/^121_/, '121', 'Balance cock', '121', 'Holds the balance by its upper pivot.'],
    [/^125_/, '125', 'Pallet bridge', '125', 'Holds the pallet lever.'],
    [/^1149_/, '1149', 'Automatic bridge', '1149', 'Holds the winding wheels.'],
    [/^(jewel|chaton_)/, 'jewels', 'Jewels and gold chatons', '', 'Rubies at the pivots, some set in gold chatons; the calibre has 29.'],
    [/^(screw_|pin_hole_)/, 'screws', 'Screws', '', 'Polished screws holding the bridges to the mainplate.'],
    [/^1143_/, 'bearing', 'Rotor bearing', '1143', 'The bearing the mini-rotor turns on.'],
    [/^movement_rotor/, 'rotor', '22K gold mini-rotor', '1143', 'Sunk into the movement so the calibre stays thin; it winds the watch as the wrist moves.'],
    [/^caseback/, 'caseback', 'Sapphire caseback', '', 'Printed “Cortina Jubilee Watch” on the 1997 watch, “Cortina Watch · 50th Anniversary · Since 1972” on the 2022.'],
  ];
  const STRAP_PART = [STRAP, 'strap', 'Strap and clasp', '', ''];
  const comps = new Map();                            // key -> { name, no, note, nodes, meshes, vis }
  const compOf = (def) => {
    if (!comps.has(def[1])) {
      comps.set(def[1], { key: def[1], name: def[2], no: def[3], note: def[4], order: PARTS.indexOf(def),
        nodes: [], meshes: [], vis: 1, applied: 1 });
    }
    return comps.get(def[1]);
  };
  const LABELS = [   // [name, z of the part in the watch, its layer offset, the part it opens]
    ['Sapphire', 1.8, 34, 'crystal'], ['Hobnail bezel', 0.9, 25, 'bezel'], ['Hands', 0.5, 17, 'hand_hour'],
    ['Dial', 0, 9, 'dial'], ['Case', -2.2, 0, 'case'], ['Mainplate', -4.9, -10, 'plate'],
    ['Gear train', -5.1, -17, '415'], ['Bridges', -5.5, -25, '105'], ['22K rotor', -5.3, -33, 'rotor'],
    ['Caseback', -6.9, -44, 'caseback'],
  ];
  const labelEls = LABELS.map(([name, , , key], i) => {
    const el = document.createElement('button');
    el.type = 'button';
    el.className = `label${i % 2 ? ' is-left' : ''}`;
    el.textContent = name;
    el.addEventListener('click', () => focusPart(key));
    $('#labels').append(el);
    return el;
  });

  // ---- the two watches
  const models = {};
  // the models' meshes are Draco-compressed (blender/export_glb.py); the decoder is vendored with three.js
  const loader = new GLTFLoader().setDRACOLoader(new DRACOLoader().setDecoderPath('vendor/three/addons/libs/draco/gltf/'));
  const progress = { [LEFT.id]: 0, [RIGHT.id]: 0 };
  const fill = $('#loader-fill');
  function load(w, plane) {
    return new Promise((resolve, reject) => loader.load(w.model, (gltf) => resolve(prepare(gltf, plane, plane === planeL ? 'left' : 'right')), (e) => {
      if (e.total) { progress[w.id] = e.loaded / e.total; fill.style.width = `${Math.round(50 * (progress[LEFT.id] + progress[RIGHT.id]))}%`; }
    }, reject));
  }
  function prepare(gltf, plane, side) {
    const root = gltf.scene;
    // the parts hang under one node, the watch's root ("watch_5057R" / "watch_5057G")
    const body = root.children.find((c) => c.name.startsWith('watch_')) ?? root;
    const parts = [];
    root.traverse((o) => {
      if (!o.isMesh) return;
      o.castShadow = o.receiveShadow = true;
      o.userData.side = side;
      // each mesh its own materials, so that one part can be shown while the rest fade
      o.material = Array.isArray(o.material) ? o.material.map((m) => m.clone()) : o.material.clone();
      for (const m of [].concat(o.material)) {
        if (m.metalness === 1 && m.roughness < 0.15) m.envMapIntensity = 1.5;   // polished gold
        m.clippingPlanes = [plane];
        m.clipShadows = true;
      }
    });
    for (const n of ['crystal', 'caseback_glass']) {
      const o = root.getObjectByName(n);
      if (o) { o.castShadow = false; o.renderOrder = 5; }
    }
    const print = root.getObjectByName('caseback_print');
    if (print) { print.castShadow = print.receiveShadow = false; print.renderOrder = 4; print.material.depthWrite = false; }
    for (const c of body.children) {
      const layer = LAYERS.find(([re]) => re.test(c.name));
      if (layer) parts.push({ o: c, z0: c.position.z, dz: layer[1] });
      const def = STRAP.test(c.name) ? STRAP_PART : PARTS.find(([re]) => re.test(c.name));
      if (!def) continue;
      const comp = compOf(def);
      comp.nodes.push({ o: c, side });
      c.traverse((o) => { if (o.isMesh) { o.userData.comp = comp.key; comp.meshes.push(o); } });
    }
    root.traverse((o) => {
      if (o.isMesh) for (const m of [].concat(o.material)) m.userData.base = { opacity: m.opacity, transparent: m.transparent, depthWrite: m.depthWrite };
    });
    const mixer = new THREE.AnimationMixer(root);
    for (const clip of gltf.animations) if (clip.name !== 'rotor_spin') mixer.clipAction(clip).play();
    const rotorNode = root.getObjectByName('movement_rotor');
    const hands = Object.fromEntries(['hour', 'minute', 'seconds', 'date'].map((k) => [k, root.getObjectByName(`hand_${k}`)]));
    return { root, parts, mixer, hands, moon: root.getObjectByName('moon_disc'), rotor: rotorNode ? new RotorPhysics(rotorNode) : null };
  }

  Promise.all([load(LEFT, planeL), load(RIGHT, planeR)]).then(([l, r]) => {
    models.left = l; models.right = r;
    holder.add(l.root, r.root);
    holder.updateMatrixWorld(true);
    l.rotor?.settle(); r.rotor?.settle();
    $('#loader').hidden = true;
    stage.classList.add('is-ready');
    startIntro();
  }).catch((err) => {
    $('#loader-text').textContent = 'The watches could not be loaded';
    console.error(err);
  });

  // ---- state
  const DIAL_YAW = -0.32;                            // three-quarter, crown toward the visitor
  // the movement: the watch turned round, a little off square so the case's depth shows; the closed strap
  // and its clasp fade away whenever the back is toward the visitor, so nothing stands in front of it
  const MOVEMENT_YAW = Math.PI - (14 * Math.PI) / 180;
  let backness = 0;                                  // 0 dial toward the visitor .. 1 caseback
  const TILT = (65 * Math.PI) / 180;                 // laid down for Anatomy: the dial up, toward the eye
  let yaw = DIAL_YAW, yawT = DIAL_YAW, pitch = 0, pitchT = 0;
  let spin = 0.35, anat = 0, anatT = 0;
  let zoom = 1, zoomT = 1;
  let seam = 0.5, seamT = 0.5, seamDrag = false;
  let idle = 0, time = 0;
  let offX = 0, offY = 0, offXT = 0, offYT = 0;
  let mode = 'dial', closeUp = 1;                   // closer in for the movement
  let focusKey = null, tiltOff = 0, tiltOffT = 0, camDist = null;
  const pp = new THREE.Vector3(0, 0, -3);             // the watch's point the pivot turns about
  const GHOST = 0.045;                                 // what is left of the other parts round one shown alone

  function setMode(m) {
    if (m !== 'anatomy') focusPart(null);
    mode = m;
    idle = 0;
    if (m === 'anatomy') { anatT = 1; spinT = spin; }
    else {
      anatT = 0;
      const base = m === 'movement' ? MOVEMENT_YAW : DIAL_YAW;
      yawT = yaw + wrap(base - yaw);                 // the short way round
      pitchT = 0;
    }
    stage.classList.toggle('is-anatomy', m === 'anatomy');
    syncModes();
  }
  let spinT = spin;
  let shownMode = 'dial';
  function syncModes() {
    let shown = mode;
    if (mode !== 'anatomy') {                        // a turn by hand can bring the movement round
      const d = (a) => Math.abs(wrap(yaw - a));
      shown = d(MOVEMENT_YAW) < 0.9 ? 'movement' : d(DIAL_YAW) < 1.2 ? 'dial' : '';
    }
    if (shown === shownMode) return;
    shownMode = shown;
    for (const b of document.querySelectorAll('.modes button')) b.setAttribute('aria-pressed', String(b.dataset.mode === shown));
  }
  for (const b of document.querySelectorAll('.modes button')) b.addEventListener('click', () => setMode(b.dataset.mode));

  // ---- turning and zooming by hand
  const pointers = new Map();
  let drag = null, pinch = null;
  let tap = null;
  canvas.addEventListener('pointerdown', (e) => {
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    tap = pointers.size === 1 ? { x: e.clientX, y: e.clientY, t: performance.now() } : null;
    canvas.setPointerCapture(e.pointerId);
    beginGesture(e.pointerType);
    clearTimeout(hold);
    if (loupeMode) { if (pointers.size === 1) { drag = null; tap = null; loupeMove(e.clientX, e.clientY); } return; }
    if (pointers.size === 1 && !focusKey) hold = setTimeout(() => loupeStart(e.clientX, e.clientY), 380);
  });
  canvas.addEventListener('pointermove', (e) => {
    if (loupeMode && e.pointerType === 'mouse' && !pointers.size) { loupeMove(e.clientX, e.clientY, true); return; }
    if (!pointers.has(e.pointerId)) return;
    pointers.get(e.pointerId).x = e.clientX;
    pointers.get(e.pointerId).y = e.clientY;
    idle = 0;
    if (loupeOn && !pinch) { loupeMove(e.clientX, e.clientY); return; }
    if (tap && Math.hypot(e.clientX - tap.x, e.clientY - tap.y) > 8) clearTimeout(hold);
    if (pinch && pointers.size >= 2) {
      const [a, b] = [...pointers.values()];
      zoomT = clamp(pinch.zoom * (Math.hypot(a.x - b.x, a.y - b.y) / pinch.d), 1, 4);
      return;
    }
    if (!drag) return;
    const p = pointers.get(e.pointerId);
    const dx = p.x - drag.x, dy = p.y - drag.y;
    if (mode === 'anatomy') {
      spin = spinT = drag.spin + dx * 0.007;
      if (drag.mouse || focusKey) tiltOff = tiltOffT = clamp(drag.tiltOff + dy * 0.006, -1.2, 1.0);
    } else {
      yaw = yawT = drag.yaw + dx * 0.007;
      if (drag.mouse) pitch = pitchT = clamp(drag.pitch + dy * 0.005, -0.6, 0.6);
      syncModes();
    }
  });
  const endPointer = (e) => {
    clearTimeout(hold);
    const p = pointers.get(e.pointerId);
    if (loupeOn && !loupeMode) { loupeEnd(); tap = null; }
    if (loupeMode) tap = null;
    if (e.type === 'pointerup' && p && pointers.size === 1 && tap && Math.hypot(p.x - tap.x, p.y - tap.y) < 8
      && performance.now() - tap.t < 500 && mode === 'anatomy') pick(p.x, p.y);
    pointers.delete(e.pointerId);
    pinch = null;
    drag = null;
    if (pointers.size === 1) beginGesture('touch');
  };
  canvas.addEventListener('pointerup', endPointer);
  canvas.addEventListener('pointercancel', endPointer);
  function beginGesture(type) {
    if (pointers.size >= 2) {
      const [a, b] = [...pointers.values()];
      pinch = { d: Math.max(1, Math.hypot(a.x - b.x, a.y - b.y)), zoom: zoomT };
      drag = null;
      clearTimeout(hold);
    } else if (pointers.size === 1) {
      const p = [...pointers.values()][0];
      drag = { x: p.x, y: p.y, yaw, pitch, spin, tiltOff, mouse: type === 'mouse' };
    }
  }
  // a trackpad pinch (ctrl + wheel) zooms; an ordinary wheel scrolls the page
  canvas.addEventListener('wheel', (e) => {
    if (!e.ctrlKey) return;
    e.preventDefault();
    zoomT = clamp(zoomT * Math.exp(-e.deltaY * 0.01), 1, 4);
    idle = 0;
  }, { passive: false });
  canvas.addEventListener('dblclick', () => { if (mode !== 'anatomy') { zoomT = zoomT > 1.5 ? 1 : 2.6; idle = 0; } });

  // ---- the opening, once a visit: the 1997 watch alone, turning into view; the seam sweeps across it and
  // it is the 2022 watch; the seam comes back to the middle and it is both. About seven seconds; a tap,
  // a key or the Skip button ends it.
  const introEl = $('#intro');
  let intro = null, introZ = 1;
  function startIntro() {
    let seen = false;
    try { seen = sessionStorage.getItem('intro-seen') === '1'; } catch {}
    if (reduced || seen || location.hash) return;
    intro = { t: 0 };
    stage.classList.add('is-intro');
    seam = seamT = 1;
  }
  function endIntro(why = 'done') {
    if (!intro) return;
    stage.dataset.introEnd = why;
    intro = null;
    try { sessionStorage.setItem('intro-seen', '1'); } catch {}
    stage.classList.remove('is-intro');
    introEl.dataset.step = '0';
    seamT = 0.5;
    yawT = DIAL_YAW;
  }
  function runIntro(dt) {
    const t = (intro.t += dt);
    introEl.dataset.step = String(t < 0.6 ? 0 : t < 2.7 ? 1 : t < 3.4 ? 0 : t < 5.2 ? 2 : t < 5.6 ? 0 : t < 7.1 ? 3 : 0);
    seam = seamT = t < 2.9 ? 1 : t < 4.9 ? 1 - smooth((t - 2.9) / 2) : t < 5.5 ? 0 : 0.5 * smooth((t - 5.5) / 1.4);
    yaw = yawT = DIAL_YAW - 0.75 * (1 - smooth(t / 6.5));   // turning into its three-quarter view
    introZ = 1 + 0.35 * (1 - smooth(t / 6.8));               // and coming closer
    if (t > 7.5) endIntro('done');
  }
  $('#intro-skip').addEventListener('click', () => endIntro('skip'));
  canvas.addEventListener('pointerdown', () => endIntro('tap'));
  addEventListener('keydown', (e) => { if (!e.repeat && !['Shift', 'Control', 'Alt', 'Meta'].includes(e.key)) endIntro('key'); });
  addEventListener('wheel', (e) => { if (Math.abs(e.deltaY) > 4) endIntro('wheel'); }, { passive: true });

  // ---- tilt: the phone's own tilt turns the watch, so its rotor swings as it would on the wrist; a shake
  // jolts it. Android gives the sensors freely; iOS asks once, on a tap of the tilt button.
  const tiltBtn = $('#tilt');
  let tiltOn = false, base = null, tY = 0, tP = 0, tYT = 0, tPT = 0;
  const jolt = new THREE.Vector3(), joltV = new THREE.Vector3();
  const onOrient = (e) => {
    if (e.beta == null || e.gamma == null) return;
    const ang = (screen.orientation && screen.orientation.angle) || 0;
    const [x, y] = ang === 90 ? [e.beta, -e.gamma] : ang === 270 || ang === -90 ? [-e.beta, e.gamma] : [e.gamma, e.beta];
    if (!base) base = { x, y };
    base.x += (x - base.x) * 0.004; base.y += (y - base.y) * 0.004;   // slowly re-centres on how it is held
    tYT = clamp((x - base.x) / 35, -1, 1) * 0.75;
    tPT = clamp((y - base.y) / 35, -1, 1) * 0.5;
    idle = 0;
  };
  let kick = 0;                                      // a sideways shake sets the rotor spinning
  const onMotion = (e) => {
    const a = e.acceleration;
    if (!a || a.x == null) return;
    const k = 0.03;                                   // m/s² of the phone -> mm/s of the watch's jolt
    joltV.x += clamp(a.x, -30, 30) * k; joltV.y += clamp(a.y, -30, 30) * k; joltV.z += clamp(a.z, -30, 30) * k;
    if (Math.abs(a.x) > 6) kick += clamp(a.x, -30, 30) * 0.03;
  };
  function setTilt(on) {
    tiltOn = on;
    base = null;
    tiltBtn.setAttribute('aria-pressed', String(on));
    tiltBtn.classList.remove('is-asking');
    const f = on ? addEventListener : removeEventListener;
    f('deviceorientation', onOrient);
    f('devicemotion', onMotion);
  }
  const asks = typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function';
  if (typeof DeviceOrientationEvent !== 'undefined' && matchMedia('(pointer: coarse)').matches) {
    tiltBtn.hidden = false;
    if (asks) tiltBtn.classList.add('is-asking');   // iOS: needs a tap to allow motion
    else setTilt(true);                              // Android: on from the start
  }
  tiltBtn.addEventListener('click', async () => {
    if (tiltOn) return setTilt(false);
    if (asks) {
      try {
        const r = await DeviceOrientationEvent.requestPermission();
        if (typeof DeviceMotionEvent !== 'undefined' && DeviceMotionEvent.requestPermission) await DeviceMotionEvent.requestPermission().catch(() => {});
        if (r !== 'granted') return;
      } catch { return; }
    }
    setTilt(true);
  });

  // ---- the loupe: press and hold anywhere on the watch; it follows the finger, magnifying 3.5x
  const loupe = $('#loupe'), lens = $('#loupe-lens'), lctx = lens.getContext('2d');
  const MAG = 3.5;
  let loupeOn = false, loupeAt = { x: 0, y: 0 }, hold = null;
  function loupeStart(x, y, exact = false) {
    loupeOn = true;
    drag = null;
    stage.classList.add('loupe-used');
    loupe.classList.add('is-on');
    loupeMove(x, y, exact);
  }
  function loupeMove(x, y, exact = false) {
    const r = canvas.getBoundingClientRect();
    const touch = !exact && matchMedia('(pointer: coarse)').matches;
    loupeAt = { x: x - r.left, y: y - r.top - (touch ? loupe.offsetHeight * 0.62 : 0) };   // above the finger
    loupe.style.translate = `${loupeAt.x}px ${loupeAt.y}px`;
  }
  function loupeEnd() { loupeOn = false; loupe.classList.remove('is-on'); }
  // the Loupe button keeps it out: it follows the mouse, or a finger dragging on the watch, until turned off
  const loupeBtn = $('#loupe-btn');
  let loupeMode = false;
  function setLoupeMode(on) {
    loupeMode = on;
    loupeBtn.setAttribute('aria-pressed', String(on));
    if (on) { const r = canvas.getBoundingClientRect(); loupeStart(r.left + r.width / 2, r.top + r.height * 0.46, true); }
    else loupeEnd();
  }
  loupeBtn.addEventListener('click', () => setLoupeMode(!loupeMode));
  addEventListener('keydown', (e) => { if (e.key === 'Escape' && loupeMode) setLoupeMode(false); });
  // no page scroll and no callout while the loupe is held
  canvas.addEventListener('touchmove', (e) => { if (loupeOn) e.preventDefault(); }, { passive: false });
  canvas.addEventListener('contextmenu', (e) => e.preventDefault());
  // draw the magnified view: the same eye, a narrower window round the loupe's centre, rendered in the
  // canvas's corner and copied into the lens before the full view is drawn over it
  function renderLoupe() {
    const size = loupe.offsetWidth * 0.87, dpr = renderer.getPixelRatio();
    const w = size / MAG;
    if (lens.width !== Math.round(size * dpr)) { lens.width = lens.height = Math.round(size * dpr); }
    camera.setViewOffset(W_, H_, offX + loupeAt.x - w / 2, offY + loupeAt.y - w / 2, w, w);
    renderer.setViewport(0, H_ - size, size, size);
    renderer.setScissor(0, H_ - size, size, size);
    renderer.setScissorTest(true);
    renderer.render(scene, camera);
    lctx.clearRect(0, 0, lens.width, lens.height);
    lctx.drawImage(canvas, 0, 0, size * dpr, size * dpr, 0, 0, lens.width, lens.height);
    renderer.setScissorTest(false);
    renderer.setViewport(0, 0, W_, H_);
    camera.setViewOffset(W_, H_, offX, offY, W_, H_);
  }

  // ---- one part on its own: tap it (or its name) in Anatomy
  const raycaster = new THREE.Raycaster(), ndcP = new THREE.Vector2();
  function pick(x, y) {
    if (!models.left) return;
    const r = canvas.getBoundingClientRect();
    ndcP.set(((x - r.left) / r.width) * 2 - 1, -((y - r.top) / r.height) * 2 + 1);
    raycaster.setFromCamera(ndcP, camera);
    const roots = [models.left.root, models.right.root].filter((o) => o.visible);
    const hits = raycaster.intersectObjects(roots, true).filter((h) => {
      const k = h.object.userData.comp;
      if (!k || k === 'strap' || !h.object.visible) return false;
      return (h.object.userData.side === 'left' ? planeL : planeR).distanceToPoint(h.point) >= 0;   // its side of the seam
    });
    if (!hits.length) return;
    const hit = hits.find((h) => comps.get(h.object.userData.comp).vis > 0.5) ?? hits[0];
    if (hit.object.userData.comp !== focusKey) focusPart(hit.object.userData.comp);
  }
  const partCard = $('#part');
  const order = () => [...comps.values()].filter((c) => c.key !== 'strap' && c.nodes.length).sort((a, b) => a.order - b.order);
  $('#parts-go').addEventListener('click', () => focusPart(order()[0].key));   // from the crystal down
  function focusPart(key) {
    if (key && mode !== 'anatomy') setMode('anatomy');
    focusKey = key;
    idle = 0;
    stage.classList.toggle('is-focus', !!key);
    if (key) {
      stage.classList.add('part-used');
      const list = order(), i = list.findIndex((c) => c.key === key), c = list[i];
      $('#part-kicker').textContent = `${c.no ? `No. ${c.no} · ` : ''}${i + 1} of ${list.length}`;
      $('#part-name').textContent = c.name;
      $('#part-note').textContent = c.note;
      zoomT = 1;
    } else tiltOffT = 0;
    partCard.hidden = !key;
    measure();
  }
  function stepPart(d) {
    const list = order(), i = list.findIndex((c) => c.key === focusKey);
    focusPart(list[(i + d + list.length) % list.length].key);
  }
  for (const btn of document.querySelectorAll('.part-step')) btn.addEventListener('click', () => stepPart(+btn.dataset.step));
  $('#part-all').addEventListener('click', () => focusPart(null));
  addEventListener('keydown', (e) => {
    if (!focusKey) return;
    if (e.key === 'Escape') focusPart(null);
    else if (e.key === 'ArrowRight' && e.target === document.body) stepPart(1);
    else if (e.key === 'ArrowLeft' && e.target === document.body) stepPart(-1);
  });
  for (const b of document.querySelectorAll('.zoom button')) {
    b.addEventListener('click', () => { zoomT = clamp(zoomT * (b.dataset.zoom === 'in' ? 1.45 : 1 / 1.45), 1, 4); idle = 0; });
  }

  // ---- the seam: dragged by its handle, or by the arrow keys
  const handle = $('#seam-handle');
  handle.addEventListener('pointerdown', (e) => { seamDrag = true; handle.setPointerCapture(e.pointerId); stage.classList.add('seam-used'); });
  handle.addEventListener('pointermove', (e) => {
    if (!seamDrag) return;
    const r = stage.getBoundingClientRect();
    seam = seamT = clamp((e.clientX - r.left) / r.width, 0, 1);
  });
  const endSeam = () => { seamDrag = false; };
  handle.addEventListener('pointerup', endSeam);
  handle.addEventListener('pointercancel', endSeam);
  handle.addEventListener('keydown', (e) => {
    const step = { ArrowLeft: -0.05, ArrowRight: 0.05, ArrowDown: -0.05, ArrowUp: 0.05 }[e.key];
    if (step) seamT = clamp(seamT + step, 0, 1);
    else if (e.key === 'Home') seamT = 0;
    else if (e.key === 'End') seamT = 1;
    else return;
    e.preventDefault();
    stage.classList.add('seam-used');
  });

  // ---- framing: the watch in the free part of the screen (above the controls, beside the sheet)
  let W_ = 1, H_ = 1, topPad = 0, botPad = 0, freeBot = 0;
  function resize() {
    W_ = canvasBox.clientWidth; H_ = canvasBox.clientHeight;
    if (!W_ || !H_) return;
    renderer.setSize(W_, H_, false);
    camera.aspect = W_ / H_;
    measure();
  }
  let rail = { left: 1e9, top: 0, bottom: 0 };       // the tool rail, which labels keep clear of
  function measure() {
    const sr = stage.getBoundingClientRect();
    const zr = $('.zoom').getBoundingClientRect();
    rail = { left: zr.left - sr.left, top: zr.top - sr.top, bottom: zr.bottom - sr.top };
    topPad = $('.masthead').getBoundingClientRect().height;
    const tops = [captions, partCard].filter((el) => !el.hidden).map((el) => el.getBoundingClientRect().top);
    botPad = sr.bottom - Math.min(...tops);
    relayout();
  }
  function relayout() {
    const wideSheet = !sheet.hidden && getComputedStyle(sheet).left !== '0px';
    const sh = sheet.hidden ? 0 : sheet.getBoundingClientRect().height;
    offXT = wideSheet ? sheet.getBoundingClientRect().width / 2 : 0;
    freeBot = !sheet.hidden && !wideSheet ? sh : botPad;   // a phone's sheet covers the lower screen
    offYT = (freeBot - topPad) / 2;
  }
  new ResizeObserver(resize).observe(canvasBox);
  resize();

  // ---- every frame
  const qN = new THREE.Quaternion(), qA = new THREE.Quaternion(), qT = new THREE.Quaternion();
  const X = new THREE.Vector3(1, 0, 0), Y = new THREE.Vector3(0, 1, 0), Z = new THREE.Vector3(0, 0, 1);
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), v = new THREE.Vector3();
  const fc = new THREE.Vector3(), box = new THREE.Box3();
  const lead = { left: null, right: null };
  function update(dt) {
    time += dt;
    idle += dt;
    // the pose
    if (!drag) {
      yaw = damp(yaw, yawT, 5, dt);
      pitch = damp(pitch, idle > 5 ? 0 : pitchT, idle > 5 ? 1 : 5, dt);
      spin = damp(spin, spinT, 5, dt);
    }
    anat = reduced ? anatT : clamp(anat + Math.sign(anatT - anat) * dt / 1.8, Math.min(anat, anatT), Math.max(anat, anatT));
    const tilt = smooth(anat / 0.55), explode = smooth((anat - 0.3) / 0.7);
    const sway = reduced ? 0 : smooth((idle - 6) / 3) * 0.06 * Math.sin(time * 0.35);   // alive when left alone
    tY = damp(tY, tiltOn ? tYT : 0, 6, dt); tP = damp(tP, tiltOn ? tPT : 0, 6, dt);
    qN.setFromAxisAngle(Y, yaw + sway + tY).multiply(qT.setFromAxisAngle(X, pitch + tP));
    tiltOff = drag ? tiltOff : damp(tiltOff, tiltOffT, 4, dt);
    qA.setFromAxisAngle(X, -TILT + tiltOff + tP * 0.8).multiply(qT.setFromAxisAngle(Z, spin + sway + tY));
    pivot.quaternion.slerpQuaternions(qN, qA, tilt);
    // the point turned about: the case's centre, the stack's when taken apart, a part's when shown alone
    let radius = 0;
    if (focusKey && models.left) {
      box.makeEmpty();
      for (const n of comps.get(focusKey).nodes) if (models[n.side].root.visible) box.expandByObject(n.o);
      if (box.isEmpty()) for (const n of comps.get(focusKey).nodes) box.expandByObject(n.o);
      radius = Math.max(3.5, box.getSize(c).length() / 2);
      holder.worldToLocal(box.getCenter(fc));
    } else fc.set(0, 0, -3 - 4 * explode);
    pp.set(damp(pp.x, fc.x, 5, dt), damp(pp.y, fc.y, 5, dt), damp(pp.z, fc.z, 5, dt));
    holder.position.copy(pp).negate();
    // a shake of the phone jolts the watch a little (a damped spring), and the rotor feels it
    joltV.addScaledVector(jolt, -90 * dt).multiplyScalar(Math.exp(-9 * dt));
    jolt.addScaledVector(joltV, dt);
    pivot.position.copy(jolt);
    // the seam
    seam = seamDrag ? seam : damp(seam, seamT, 6, dt);
    stage.style.setProperty('--seam', seam.toFixed(4));
    handle.setAttribute('aria-valuenow', String(Math.round(seam * 100)));
    handle.setAttribute('aria-valuetext', seam > 0.97 ? 'The 1997 Ref. 5057R' : seam < 0.03 ? 'The 2022 Ref. 5057G' : '1997 on the left, 2022 on the right');
    const l = seam >= 0.5;
    if (lead.left !== l) {
      lead.left = l;
      for (const el of captions.children) el.classList.toggle('is-lead', (el.dataset.id === LEFT.id) === l);
    }
    // the camera: back far enough for the watch (or its parts) to fit the free part of the screen
    const t = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    const freeH = Math.max(120, H_ - topPad - freeBot), freeW = W_ - 2 * offX;
    const halfH = THREE.MathUtils.lerp(44, 62, tilt), halfW = THREE.MathUtils.lerp(30, small ? 58 : 54, tilt);
    const dist = Math.max((halfH / t) * (H_ / freeH), halfW / (t * (freeW / H_)));
    zoom = damp(zoom, zoomT, 8, dt);
    const nearMovement = 1 - smooth(Math.abs(wrap(yaw - MOVEMENT_YAW)) / 0.9);
    // how far the caseback faces the visitor, whichever way the watch was turned
    backness = smooth((-Math.cos(yaw + sway + tY) * Math.cos(pitch + tP) - 0.25) / 0.45) * (1 - tilt);
    closeUp = damp(closeUp, 1 + 0.55 * nearMovement * (1 - tilt), 3, dt);
    // a part alone fills the free part of the screen
    if (intro) runIntro(dt); else introZ = damp(introZ, 1, 3, dt);
    const want = (radius ? (radius * 1.05) / (t * (Math.min(freeH, freeW) / H_)) / zoom : dist / (zoom * closeUp)) * introZ;
    camDist = camDist === null ? want : damp(camDist, want, 4, dt);
    camera.near = clamp(camDist * 0.02, 0.5, 5);
    camera.position.set(0, 0, 0).addScaledVector(v.set(0, 0.1, 1).normalize(), camDist);
    syncModes();
    camera.lookAt(0, 0, 0);
    offX = damp(offX, offXT, 6, dt); offY = damp(offY, offYT, 6, dt);
    camera.setViewOffset(W_, H_, offX, offY, W_, H_);
    camera.updateMatrixWorld();
    // clipping planes from the seam's line on the screen
    const ndc = seam * 2 - 1;
    a.set(ndc, -1, 0.5).unproject(camera); b.set(ndc, 1, 0.5).unproject(camera);
    planeL.setFromCoplanarPoints(camera.position, a, b);
    if (planeL.distanceToPoint(c.set(ndc - 0.5, 0, 0.5).unproject(camera)) < 0) planeL.negate();
    planeR.copy(planeL).negate();
    if (!models.left) return { explode };
    models.left.root.visible = seam > 0.002;
    models.right.root.visible = seam < 0.998;
    return { explode, tilt };
  }

  // the time shown: 10:10 (the watchmakers' display time, the hands framing the name) or Singapore's own,
  // the seconds stepping six times a second as the 3 Hz balance does. Between the two the hands are
  // wound round the short way, quickly, as when the watch is set.
  const TEN_TEN = 10 * 3600 + 10 * 60 + 35;          // 10:10:35, the seconds clear of the subdial's text
  let clockT = TEN_TEN, timeMode = 'tenten';
  function tickClock(dt) {
    const now = new Date(Date.now() + site.timeZoneOffsetHours * 3600e3);
    const live = (now.getUTCHours() % 12) * 3600 + now.getUTCMinutes() * 60
      + Math.floor((now.getUTCSeconds() + now.getUTCMilliseconds() / 1000) * 6) / 6;
    const target = timeMode === 'live' ? live : TEN_TEN;
    const d = ((((target - clockT) % 43200) + 64800) % 43200) - 21600;   // signed, the short way round
    clockT = Math.abs(d) < 0.3 || reduced ? target : clockT + d * (1 - Math.exp(-dt * 3.2));
    clockT = ((clockT % 43200) + 43200) % 43200;
  }
  for (const b of document.querySelectorAll('.clock button')) {
    b.addEventListener('click', () => {
      timeMode = b.dataset.time;
      for (const o of document.querySelectorAll('.clock button')) o.setAttribute('aria-pressed', String(o === b));
    });
  }
  function setTime(m) {
    const now = new Date(Date.now() + site.timeZoneOffsetHours * 3600e3);
    if (m.hands.hour) m.hands.hour.rotation.z = -(clockT / 43200) * Math.PI * 2;
    if (m.hands.minute) m.hands.minute.rotation.z = -((clockT % 3600) / 3600) * Math.PI * 2;
    if (m.hands.seconds) m.hands.seconds.rotation.z = -((clockT % 60) / 60) * Math.PI * 2;
    // the pointer date: the date ring runs clockwise from 1 o'clock-ish, 11.6° a day (both photos agree:
    // the 5057G's hand on the 20th, the 5057R's on the 29th)
    if (m.hands.date) m.hands.date.rotation.z = THREE.MathUtils.degToRad(80.4 - (now.getUTCDate() - 1) * 11.6 - 90);
    // the moon: each of the disc's two moons rises from the left scallop (new), crosses the top of the
    // window (full) and sets into the right one, once a lunation; built where the photo had it (54.2°)
    if (m.moon) {
      const age = (((Date.now() - Date.UTC(2000, 0, 6, 18, 14)) / 86400000) % SYNODIC + SYNODIC) % SYNODIC;
      m.moon.rotation.z = THREE.MathUtils.degToRad(180 - (age / SYNODIC) * 180 - 54.2);
    }
  }

  function animateModel(m, dt, explode) {
    m.mixer.update(dt);
    for (const p of m.parts) p.o.position.z = p.z0 + explode * p.dz;
    setTime(m);
    m.rotor?.update(dt);
  }

  // the strap fades as the watch is laid down; round a part shown alone, the rest fade to a ghost
  function fadeParts(dt, tilt) {
    const strap = 1 - Math.max(smooth(tilt / 0.6), backness);   // out of the way: Anatomy, or the back shown
    for (const comp of comps.values()) {
      if (comp.key === 'strap') comp.vis = strap;
      else comp.vis = damp(comp.vis, focusKey ? (comp.key === focusKey ? 1 : GHOST) : 1, 6, dt);
      if (Math.abs(comp.vis - comp.applied) < 0.002 && !(comp.vis === 1 && comp.applied !== 1)) continue;
      if (comp.vis > 0.997) comp.vis = 1;
      comp.applied = comp.vis;
      for (const o of comp.meshes) {
        o.visible = comp.vis > 0.01;
        o.castShadow = comp.vis > 0.5;
        for (const mat of [].concat(o.material)) {
          const base = mat.userData.base;
          const tr = base.transparent || comp.vis < 1;
          if (mat.transparent !== tr) { mat.transparent = tr; mat.needsUpdate = true; }
          mat.opacity = base.opacity * comp.vis;
          mat.depthWrite = base.depthWrite && comp.vis > 0.5;
        }
      }
    }
  }

  // part names beside the watch taken apart, alternately right and left of it
  function placeLabels(explode) {
    const on = explode > 0.92 && !focusKey;
    const pxPerMm = H_ / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)));
    LABELS.forEach(([, z, dz], i) => {
      const el = labelEls[i];
      el.classList.toggle('is-on', on);
      if (!on) return;
      v.set(0, 0, z + explode * dz);
      holder.localToWorld(v);
      const depth = v.distanceTo(camera.position);
      v.project(camera);
      const x = (v.x * 0.5 + 0.5) * W_, y = (-v.y * 0.5 + 0.5) * H_;
      const r = (21 * pxPerMm) / depth + 6;
      const w = el.offsetWidth, m = 10;
      const right = y > rail.top - 12 && y < rail.bottom + 12 ? rail.left - 8 : W_ - m;   // clear of the rail
      el.style.transform = i % 2
        ? `translate(${Math.max(m, x - r - w)}px, ${y}px) translate(0, -50%)`
        : `translate(${Math.min(right - w, x + r)}px, ${y}px) translate(0, -50%)`;
    });
  }

  // render only while the stage is on screen
  let onScreen = true;
  new IntersectionObserver(([e]) => { onScreen = e.isIntersecting; }).observe(stage);
  const clock = new THREE.Clock();
  renderer.setAnimationLoop(() => {
    const dt = Math.min(clock.getDelta(), 1 / 20);
    if (!onScreen || document.hidden) return;
    const { explode = 0, tilt = 0 } = update(dt);
    if (models.left) {
      tickClock(dt);
      for (const m of [models.left, models.right]) if (m.rotor) m.rotor.omega += kick;
      kick = 0;
      if (models.left.root.visible) animateModel(models.left, dt, explode);
      if (models.right.root.visible) animateModel(models.right, dt, explode);
      fadeParts(dt, tilt);
    }
    placeLabels(explode);
    if (loupeOn) renderLoupe();
    renderer.render(scene, camera);
  });

  return {
    setSeam(s) { seamT = s; stage.classList.add('seam-used'); },
    relayout,
  };
}

// ------------------------------------------------------------------ the masthead: white over the white story
const masthead = $('.masthead'), story = $('#story'), colophon = $('.colophon');
function mastheadTone() {
  const y = masthead.getBoundingClientRect().height / 2;
  const over = (el) => { const r = el.getBoundingClientRect(); return r.top < y && r.bottom > y; };
  masthead.classList.toggle('on-light', over(story) || over(colophon));
}
addEventListener('scroll', mastheadTone, { passive: true });
mastheadTone();

// ------------------------------------------------------------------ the story
// The chapters were written for a walk-through hall; lines that point at its exhibits are left out here.
const hallOnly = /\s*(Inspect the watch[^.]*\.|As you approach[^.]*\.|Scroll to walk[^.]*\.)/g;
const whenOf = { '5057g': '2022', dome: '2022', craft: 'Geneva', future: 'Today' };
const timeline = $('#timeline');
for (const ch of chapters) {
  if (ch.id === 'welcome' || ch.id === 'seven-decades') continue;
  const watchId = { watch5057R: '5057r', watch5057G: '5057g' }[ch.exhibit];
  const li = document.createElement('li');
  li.innerHTML = `
    <p class="when">${whenOf[ch.id] ?? ch.nav.split(' · ')[0]}</p>
    <div>
      ${ch.images ? `<div class="photos">${ch.images.map((im) => photo(im)).join('')}</div>` : photo(ch.image)}
      <h3>${ch.title}</h3>
      <p>${ch.body.replace(hallOnly, '')}</p>
      ${watchId ? `<button type="button" class="to-vitrine" data-id="${watchId}">See the watch</button>` : ''}
    </div>`;
  timeline.append(li);
}
timeline.addEventListener('click', (e) => {
  const btn = e.target.closest('.to-vitrine');
  if (!btn) return;
  showWhole(btn.dataset.id);
  stage.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' });
});
const fin = chapters.find((ch) => ch.id === 'seven-decades');
if (fin) {
  $('#finale').innerHTML = `<div class="finale-inner">
    ${photo(fin.image)}
    <p class="eyebrow">${fin.kicker}</p>
    <h2>${fin.title}</h2>
    <p>${fin.body}</p>
    <a class="cta" href="${site.ctaHref}" target="_blank" rel="noopener">${site.ctaLabel}</a></div>`;
}

// #5057r or #5057g in the address opens on that watch, whole
const start = location.hash.slice(1).toLowerCase();
if (W[start]) showWhole(start);
