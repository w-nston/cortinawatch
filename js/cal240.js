// Patek Philippe calibre 240 (bridge side), as fitted to the Ref. 5057.
//
// Adapted from the calibre 240 Q model in w-nston/3DWatch: a photograph of the
// real movement is projected onto modelled 3D parts (plate, going-train bridge,
// balance cock, 22K gold mini-rotor), so the finish is real: Côtes de Genève,
// circular graining, gold-filled engravings and the Patek Philippe Seal.
// On top of the photograph sit modelled, moving parts: the going train, the
// balance at 3 Hz with its spring, the mini-rotor and ruby jewels.
//
// The photo's luminance is turned into a roughness map and a normal map, so
// polished bevels, screws and the côtes catch the gallery lights as you turn
// the watch.
//
// Units: millimetres. Front coordinates (+X toward the crown, +Y toward 12),
// movement seated with its dial side at z = 0 and its bridges toward -Z.
import * as THREE from 'three';
import * as G from './lib/geo.js';
import { RotorPhysics } from './rotor_physics.js';

const { TAU, DEG, polar, dist } = G;

export const R_MVT = 13.75;
const PLATE_T = 1.2;
const ROTOR = [6.47, -0.88], ROTOR_R = 6.8;
const BAL = [1.48, 10.33], BAL_R = 3.05;
const Z = { bridge: -2.3, bridgeT: 0.42 };

// photo -> movement mapping (measured: movement radius = 411 px in a 1280 px photo)
const PHOTO_SIZE = 1280;
const PX = R_MVT / 411;
const BACK = { cx: 648.3, cy: 641.8 };
const fromPx = (px, py) => [-(px - BACK.cx) * PX, -(py - BACK.cy) * PX];

function photoUV(geo, at) {
  const pos = geo.attributes.position;
  const uv = new Float32Array(pos.count * 2);
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i) + at[0], y = pos.getY(i) + at[1];
    uv[i * 2] = (BACK.cx - x / PX) / PHOTO_SIZE;
    uv[i * 2 + 1] = 1 - (BACK.cy - y / PX) / PHOTO_SIZE;
  }
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  return geo;
}

// Jewels found in the photograph (px centre, px diameter).
const JEWELS = [
  [644, 362, 24], [727, 392, 19], [799, 409, 23], [866, 451, 22], [840, 530, 20],
  [720, 594, 19], [784, 621, 30], [596, 867, 24], [506, 904, 20], [691, 911, 30], [546, 1002, 20],
];

const loadImage = (url) => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = url; });

// Build colour / roughness / normal textures from the photograph.
function photoTextures(url) {
  const N = PHOTO_SIZE;
  const mk = (n = N) => { const c = document.createElement('canvas'); c.width = c.height = n; return c; };
  const rawC = mk(), plateC = mk(), roughC = mk(512);
  const tex = (c, srgb = true) => { const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
  const raw = tex(rawC), plate = tex(plateC), rough = tex(roughC, false);
  const normal = new THREE.DataTexture(new Uint8Array(512 * 512 * 4).fill(128), 512, 512);
  normal.needsUpdate = true;

  const ready = loadImage(url).then((im) => {
    rawC.getContext('2d').drawImage(im, 0, 0, N, N);
    raw.needsUpdate = true;

    // plate copy with the rotor and balance painted out, so the moving 3D
    // rotor and balance never reveal a frozen copy beneath them
    const ctx = plateC.getContext('2d');
    ctx.drawImage(im, 0, 0, N, N);
    const rx = BACK.cx - ROTOR[0] / PX, ry = BACK.cy - ROTOR[1] / PX, rr = ROTOR_R / PX + 8;
    ctx.save();
    ctx.beginPath(); ctx.arc(rx, ry, rr, 0, TAU); ctx.clip();
    ctx.fillStyle = '#a9acb0';
    ctx.fillRect(rx - rr, ry - rr, rr * 2, rr * 2);
    for (let r = 4; r < rr; r += 3) {
      ctx.strokeStyle = `rgba(255,255,255,${0.05 + 0.05 * Math.sin(r * 0.7)})`;
      ctx.beginPath(); ctx.arc(rx, ry, r, 0, TAU); ctx.stroke();
    }
    ctx.restore();
    const bx = BACK.cx - BAL[0] / PX, by = BACK.cy - BAL[1] / PX, br = BAL_R / PX + 8;
    const gg = ctx.createRadialGradient(bx, by, 0, bx, by, br);
    gg.addColorStop(0, '#5d6065'); gg.addColorStop(1, '#8e9196');
    ctx.fillStyle = gg;
    ctx.beginPath(); ctx.arc(bx, by, br, 0, TAU); ctx.fill();
    plate.needsUpdate = true;

    // luminance -> roughness (bright = polished) and height -> normal map
    const S = 512;
    const rc = roughC.getContext('2d');
    rc.drawImage(im, 0, 0, S, S);
    const img = rc.getImageData(0, 0, S, S);
    const lum = new Float32Array(S * S);
    for (let i = 0; i < S * S; i++) {
      const d = img.data;
      lum[i] = (0.2126 * d[i * 4] + 0.7152 * d[i * 4 + 1] + 0.0722 * d[i * 4 + 2]) / 255;
      const r = Math.max(0.08, Math.min(0.62, 0.62 - 0.55 * Math.pow(lum[i], 1.6)));
      d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = r * 255;
      d[i * 4 + 3] = 255;
    }
    rc.putImageData(img, 0, 0);
    rough.needsUpdate = true;
    const nd = normal.image.data;
    const at = (x, y) => lum[Math.min(S - 1, Math.max(0, y)) * S + Math.min(S - 1, Math.max(0, x))];
    for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
      const dx = (at(x + 1, y) - at(x - 1, y)) * 2.2;
      const dy = (at(x, y - 1) - at(x, y + 1)) * 2.2;
      const l = Math.hypot(dx, dy, 1);
      const i = (y * S + x) * 4;
      nd[i] = (-dx / l * 0.5 + 0.5) * 255;
      nd[i + 1] = (-dy / l * 0.5 + 0.5) * 255;
      nd[i + 2] = (1 / l * 0.5 + 0.5) * 255;
      nd[i + 3] = 255;
    }
    normal.needsUpdate = true;
  });
  return { raw, plate, rough, normal, ready };
}

// Returns { group, parts, update(t), setExplode(e), ready }.
// parts carry `L` (explode layer, negative = toward the caseback).
export function buildCal240({ photoUrl = new URL('../assets/cal240-back.webp', import.meta.url).href, gold = 0xe7c27d } = {}) {
  const T = photoTextures(photoUrl);
  const P = (o) => new THREE.MeshPhysicalMaterial(o);
  const nScale = new THREE.Vector2(0.55, 0.55);
  const mat = {
    plate: P({ map: T.plate, roughnessMap: T.rough, normalMap: T.normal, normalScale: nScale, metalness: 0.62, roughness: 1, envMapIntensity: 1.25, clearcoat: 0.25, clearcoatRoughness: 0.3 }),
    bridge: P({ map: T.raw, roughnessMap: T.rough, normalMap: T.normal, normalScale: nScale, metalness: 0.68, roughness: 1, envMapIntensity: 1.35, clearcoat: 0.35, clearcoatRoughness: 0.25 }),
    rotor: P({ map: T.raw, roughnessMap: T.rough, normalMap: T.normal, normalScale: nScale, metalness: 0.9, roughness: 0.9, envMapIntensity: 1.4, clearcoat: 0.4, clearcoatRoughness: 0.2 }),
    edge: P({ color: 0xe3e5e8, metalness: 1, roughness: 0.12 }),
    goldEdge: P({ color: gold, metalness: 1, roughness: 0.14 }),
    brass: P({ color: 0xe2bd6f, metalness: 1, roughness: 0.22 }),
    gilt: P({ color: 0xf0cf86, metalness: 1, roughness: 0.16 }),
    steel: P({ color: 0xd4d7db, metalness: 1, roughness: 0.1 }),
    ruby: P({ color: 0xb0124a, metalness: 0, roughness: 0.03, clearcoat: 1, clearcoatRoughness: 0.02, transmission: 0, emissive: 0x2a0012, emissiveIntensity: 0.5, envMapIntensity: 1.6 }),
    hairspring: P({ color: 0x8b97b8, metalness: 0.9, roughness: 0.22, side: THREE.DoubleSide }),
  };
  const mesh = (g, m) => { const o = new THREE.Mesh(g, m); o.castShadow = true; o.receiveShadow = true; return o; };

  const group = new THREE.Group();
  const parts = [];
  const S_ = {};
  function part(id, L, z, at, ...children) {
    const o = new THREE.Group();
    o.position.set(at?.[0] ?? 0, at?.[1] ?? 0, z);
    children.flat().forEach((c) => c && o.add(c));
    group.add(o);
    parts.push({ id, L, z, object: o });
    return o;
  }

  // mainplate (photo, with rotor & balance pockets painted out)
  {
    const s = new THREE.Shape();
    s.absarc(0, 0, R_MVT, 0, TAU, false);
    const g = G.extrude(s, PLATE_T, { bevel: 0.05, curveSegments: 128 });
    photoUV(g, [0, 0]);
    part('mainplate', 0, -PLATE_T, null, mesh(g, [mat.plate, mat.edge]));
  }
  // bridges: outlines follow the photograph
  const bridge = (id, pts, L) => {
    const sh = G.roundedShape(pts.map(([px, py, r = 0]) => [...fromPx(px, py), r]));
    const g = G.extrude(sh, Z.bridgeT, { bevel: 0.06, curveSegments: 12 }).translate(0, 0, -Z.bridgeT);
    photoUV(g, [0, 0]);
    return part(id, L, Z.bridge + Z.bridgeT, null, mesh(g, [mat.bridge, mat.edge]));
  };
  bridge('train-bridge', [[690, 470, 30], [770, 430, 30], [900, 450, 40], [1010, 560, 30], [1050, 720, 20], [1000, 890, 30], [880, 990, 30], [730, 1030, 30], [590, 1010, 20], [575, 900, 20], [650, 850, 30], [720, 760, 30], [715, 610, 30]], -3.0);
  bridge('balance-cock', [[395, 300, 20], [520, 280, 40], [640, 300, 60], [690, 360, 50], [640, 400, 40], [520, 380, 30], [400, 360, 20]], -3.4);

  // going train (between plate and bridges)
  const mobile = (id, at, r, teeth, pinR, L) => {
    const g = new THREE.Group();
    const w = mesh(G.wheelGeometry({ teeth, r, thick: 0.13, spokes: 4, curve: 0.4, hub: 0.5, rim: 0.36, spokeW: 0.3, arbor: 0 }), mat.gilt);
    w.position.z = -0.2;
    g.add(w);
    const p = mesh(G.pinionGeometry({ leaves: 10, r: pinR, h: 0.25 }), mat.steel);
    p.position.z = -0.6;
    g.add(p, mesh(G.cylZ(0.11, 1.1, 10).translate(0, 0, -1.1), mat.steel));
    return part(id, L, -1.25, at, g);
  };
  S_.w2 = mobile('wheel-2', [-2.2, 1.6], 3.2, 72, 0.6, -1.2);
  S_.w3 = mobile('wheel-3', [-4.5, 4.4], 2.6, 64, 0.5, -1.4);
  S_.w4 = mobile('wheel-4', [-2.2, 7.3], 2.4, 60, 0.45, -1.2);
  const EW = [-0.5, 8.9];
  {
    const bg = new THREE.Group();
    bg.add(mesh(G.merge([G.extrude(G.gearShape(80, 4.0), 0.2, { bevel: 0.02, curveSegments: 4 }), G.extrude(G.annulusShape(3.9, 3.6), 0.9, { bevel: 0.02 })]), mat.steel));
    part('barrel', -1.6, -2.15, [-6.4, -4.6], bg);
    const es = new THREE.Shape();
    const pts = [];
    for (let i = 0; i < 15; i++) {
      const a = (i / 15) * TAU;
      const Pp = (r, da) => [Math.cos(a + da) * r, Math.sin(a + da) * r];
      pts.push(Pp(0.95, 0), Pp(1.3, 0.2), Pp(1.27, 0.28), Pp(0.95, 0.32));
    }
    pts.forEach(([x, y], i) => (i ? es.lineTo(x, y) : es.moveTo(x, y)));
    es.closePath();
    S_.esc = part('escape-wheel', -1.4, -1.45, EW, mesh(G.extrude(es, 0.1, { bevel: 0.01, curveSegments: 4 }), mat.steel));
    const K = polar(EW, 1.9, Math.atan2(BAL[1] - EW[1], BAL[0] - EW[0]) / DEG);
    const fk = new THREE.Group();
    const toK = (p) => [p[0] - K[0], p[1] - K[1]];
    fk.add(mesh(G.extrude(G.barShape([0, 0], toK(polar(K, dist(K, BAL) - 0.45, Math.atan2(BAL[1] - K[1], BAL[0] - K[0]) / DEG)), 0.24, 0.16), 0.09, { bevel: 0.01 }), mat.steel));
    fk.add(mesh(G.extrude(G.barShape(toK(polar(EW, 1.3, 20)), toK(polar(EW, 1.3, 120)), 0.2, 0.2), 0.09, { bevel: 0.01 }), mat.steel));
    S_.fork = part('pallet-fork', -1.5, -1.45, K, fk);
  }
  // Gyromax balance + spring, beating at 3 Hz
  {
    const bal = new THREE.Group();
    const rim = G.extrude(G.annulusShape(BAL_R, BAL_R - 0.3), 0.22, { bevel: 0.04, curveSegments: 72 });
    const arms = [0, 180].map((a) => G.extrude(G.barShape([0, 0], polar([0, 0], BAL_R - 0.15, a), 0.36, 0.28), 0.12, { bevel: 0.02 }));
    bal.add(mesh(G.merge([rim, ...arms, G.cylZ(0.34, 0.2, 18)]), mat.gilt));
    for (let i = 0; i < 4; i++) {
      const w = mesh(G.cylZ(0.22, 0.28, 12), mat.gilt);
      const p = polar([0, 0], BAL_R - 0.15, 45 + i * 90);
      w.position.set(p[0], p[1], -0.03);
      bal.add(w);
    }
    S_.bal = part('balance-wheel', -2.0, -2.0, BAL, bal);
    const hg = G.ribbonGeometry(700);
    const hs = mesh(hg, mat.hairspring);
    hs.frustumCulled = false;
    S_.hs = { geo: hg, n: 700, pts: [] };
    part('hairspring', -2.3, -2.22, BAL, hs);
  }
  // 22K gold mini-rotor: its texture is cut from the photograph, so the Calatrava cross turns with it
  {
    const top = 1.25;
    const a0 = Math.asin(top / ROTOR_R);
    const s = new THREE.Shape();
    s.absarc(0, 0, ROTOR_R, a0, Math.PI - a0 - TAU, true);
    s.closePath();
    s.holes.push(G.circlePath(0, 0, 0.45));
    const g = G.extrude(s, 0.55, { bevel: 0.09, curveSegments: 64 }).translate(0, 0, -0.55);
    photoUV(g, ROTOR);
    const hub = mesh(G.cylZ(0.9, 0.5, 32).translate(0, 0, -0.55), mat.steel);
    S_.rotor = part('mini-rotor', -3.8, Z.bridge + 0.05, ROTOR, mesh(g, [mat.rotor, mat.goldEdge]), hub);
  }
  // jewels: polished sink + domed ruby, set into the bridges
  {
    const sinks = [], rubies = [];
    for (const [px, py, d] of JEWELS) {
      const r = Math.max(0.28, (d / 2) * PX * 0.95);
      const [x, y] = fromPx(px, py);
      const { sink, ruby } = G.jewelGeometries(r);
      // both face the caseback (-Z): flip and place on the bridge surface
      for (const [g, list, dz] of [[sink, sinks, 0], [ruby, rubies, 0.01]]) {
        g.rotateX(Math.PI);
        g.translate(x, y, Z.bridge - dz);
        list.push(g);
      }
    }
    part('jewels', -3.05, 0, null, mesh(G.merge(sinks), mat.edge), mesh(G.merge(rubies), mat.ruby));
  }

  let explode = 0;
  const GAP = 2.4;
  function setExplode(e) {
    explode = e;
    for (const p of parts) p.object.position.z = p.z + p.L * GAP * e;
  }

  let rotorPhys = null, lastT = 0;
  function update(t) {
    // going train, stepping with each beat (3 Hz = 6 beats/s)
    const beats = t * 6;
    const kb = Math.floor(beats);
    const tt = (kb + 1 - Math.pow(1 - Math.min(1, (beats - kb) / 0.2), 3)) / 6;
    const aC = (-TAU * tt) / 3600;
    S_.w2.rotation.z = aC;
    S_.w3.rotation.z = -aC * 8;
    S_.w4.rotation.z = aC * 60;
    S_.esc.rotation.z = -aC * 720;
    const theta = 4.4 * Math.sin(TAU * 3 * t);
    S_.bal.rotation.z = theta;
    S_.fork.rotation.z = 0.15 * Math.max(-1, Math.min(1, -theta / 0.45));
    const pts = S_.hs.pts;
    pts.length = 0;
    for (let i = 0; i < S_.hs.n; i++) {
      const s2 = i / (S_.hs.n - 1), r = 0.35 + 1.9 * s2, a = s2 * 12 * TAU + theta * (1 - s2) * 0.9;
      pts.push([Math.cos(a) * r, Math.sin(a) * r, 0]);
    }
    G.updateRibbon(S_.hs.geo, pts, 0.09);
    // mini-rotor: swings with the watch's own motion (gravity as it tilts, its turns, its jolts)
    let top = S_.rotor;
    while (top.parent) top = top.parent;
    if (top.isScene) {                         // once it is in the scene, so "down" is known
      if (!rotorPhys) { rotorPhys = new RotorPhysics(S_.rotor); rotorPhys.settle(); }
      else rotorPhys.update(t - lastT);
      lastT = t;
    }
  }
  update(0);

  return { group, parts, update, setExplode, ready: T.ready, get explode() { return explode; } };
}
