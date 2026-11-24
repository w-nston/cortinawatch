// Patek Philippe Ref. 5057: the Cortina Jubilee watches.
//   5057R (1997, Cortina Watch 25th Jubilee): 18K rose gold, white dial, black print and hands
//   5057G (Cortina Watch 50th anniversary):   white gold, slate grey sunburst dial, white print
//
// Built in millimetres (front coordinates: +X toward the crown at 3, +Y toward
// 12, +Z out of the dial). The dial layout is measured from photographs of the
// 5057G: Roman numerals, power reserve at 10–11, pointer date around the moon
// phase at 7, small seconds at 4–5. The hobnail ("Clous de Paris") bezel is
// real geometry: each pyramid is an instance that catches light on its own.
// The calibre 240 behind the sapphire caseback is in cal240.js.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import * as G from './lib/geo.js';
import { normalFromHeight } from './lib/materials.js';
import { buildCal240 } from './cal240.js';

const { TAU, DEG } = G;
const SYNODIC = 29.530588853;

// ---------------------------------------------------------------- layout (mm)
const CASE_R = 18;
const DIAL_R = 15.4;
const PR = [-6.5, 6.4]; // power reserve pivot
const DATE = [-3.55, -6.95]; // date hand & moon disc pivot
const SECS = [7.7, -6.9]; // small seconds
const MOON_WIN = { cx: -3.6, cy: -6.6, R: 3.85 };
const Z = { dial: 0.7, dialT: 0.3, moon: 0.55, subHand: 1.12, hour: 1.3, minute: 1.48, bezel: 1.6, crystal: 3.0 };

export const VARIANTS = {
  '5057G': {
    metal: 0xdcdddf, metalSatin: 0xcfd0d2,
    dial: 'slate', ink: '#eeeeea', inkSoft: 'rgba(238,238,234,0.9)', ring: '#17181a',
    hands: 'metal', strap: 0x0b0c0f, lining: 0x8e8a86,
    print: { kind: 'block', lines: ['Cortina Watch', '50th Anniversary', 'Since 1972'] },
  },
  '5057R': {
    metal: 0xeab08e, metalSatin: 0xdca486,
    dial: 'white', ink: '#121212', inkSoft: 'rgba(18,18,18,0.92)', ring: null,
    hands: 'black', strap: 0x0d0d10, lining: 0xb39b78,
    print: { kind: 'arc', text: 'CORTINA JUBILEE WATCH' },
  },
};

const SANS = '"Jost", "Futura", "Helvetica Neue", Arial, sans-serif';
const ROMAN = '"Times New Roman", Times, "Liberation Serif", "Cormorant Garamond", serif';
const PRINT_SERIF = '"Times New Roman", Times, "Liberation Serif", serif';

function canvas(w, h = w) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
function tex(c, srgb = true) { const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 16; return t; }

// ---------------------------------------------------------------- dial print
// Draws the dial in mm space onto a square canvas (planar UV over the dial disc).
export function drawDial(ctx, W, v, mode) {
  // mode: 'color' (full colour), 'orm' (G = roughness, B = metalness)
  const s = W / (DIAL_R * 2);
  const P = (x, y) => [W / 2 + x * s, W / 2 - y * s];
  const ink = mode === 'color' ? v.ink : 'rgb(0,150,0)'; // printed: rough-ish, not metallic
  ctx.save();
  if (mode === 'color') {
    if (v.dial === 'slate') {
      const g = ctx.createRadialGradient(W / 2, W / 2, 0, W / 2, W / 2, W / 2);
      g.addColorStop(0, '#5a5e63');
      g.addColorStop(0.55, '#45484d');
      g.addColorStop(1, '#2c2e32');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, W);
      // faint sunburst brushing (the moving highlight comes from the anisotropic material)
      ctx.translate(W / 2, W / 2);
      for (let i = 0; i < 1400; i++) {
        const a = Math.random() * TAU;
        ctx.strokeStyle = `rgba(${Math.random() < 0.5 ? '255,255,255' : '0,0,0'},${0.015 + Math.random() * 0.03})`;
        ctx.lineWidth = 0.6 + Math.random();
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a) * W, Math.sin(a) * W); ctx.stroke();
      }
      ctx.setTransform(1, 0, 0, 1, 0, 0);
    } else {
      const g = ctx.createRadialGradient(W / 2, W / 2, 0, W / 2, W / 2, W / 2);
      g.addColorStop(0, '#f7f6f1');
      g.addColorStop(1, '#ecebe4');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, W);
    }
  } else {
    // base: G roughness, B metalness
    ctx.fillStyle = v.dial === 'slate' ? 'rgb(0,95,165)' : 'rgb(0,70,0)';
    ctx.fillRect(0, 0, W, W);
  }

  // chapter ring (railway minute track)
  const r0 = 13.65, r1 = 15.1;
  if (v.ring && mode === 'color') {
    ctx.fillStyle = v.ring;
    ctx.beginPath(); ctx.arc(W / 2, W / 2, r1 * s, 0, TAU); ctx.arc(W / 2, W / 2, r0 * s, 0, TAU, true); ctx.fill();
  }
  ctx.strokeStyle = ink;
  ctx.fillStyle = ink;
  ctx.lineWidth = 0.08 * s;
  [r0, r1].forEach((r) => { ctx.beginPath(); ctx.arc(W / 2, W / 2, r * s, 0, TAU); ctx.stroke(); });
  for (let i = 0; i < 60; i++) {
    const a = Math.PI / 2 - (i / 60) * TAU;
    ctx.lineWidth = (i % 5 === 0 ? 0.16 : 0.1) * s;
    const [x0, y0] = P(Math.cos(a) * r0, Math.sin(a) * r0), [x1, y1] = P(Math.cos(a) * r1, Math.sin(a) * r1);
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
  }
  // SWISS cartouche at 6
  {
    const [x, y] = P(0, -14.38);
    ctx.fillStyle = mode === 'color' ? (v.ring || '#efeee8') : 'rgb(0,150,0)';
    ctx.fillRect(x - 1.0 * s, y - 0.36 * s, 2.0 * s, 0.72 * s);
    ctx.fillStyle = ink;
    ctx.lineWidth = 0.06 * s;
    ctx.strokeRect(x - 0.95 * s, y - 0.32 * s, 1.9 * s, 0.64 * s);
    ctx.font = `500 ${0.46 * s}px ${SANS}`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('SWISS', x, y + 0.02 * s);
  }

  // text helper: centred, horizontally fitted to a target width (mm)
  const fitText = (t, x, y, size, width, font, weight = 600, rot = 0) => {
    ctx.save();
    const [px, py] = P(x, y);
    ctx.translate(px, py);
    ctx.rotate(rot);
    ctx.font = `${weight} ${size * s}px ${font}`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    if (width) ctx.scale((width * s) / ctx.measureText(t).width, 1);
    ctx.fillStyle = ink;
    ctx.fillText(t, 0, 0);
    ctx.restore();
  };

  // Roman numerals, radially oriented
  const romans = { 12: 'XII', 1: 'I', 2: 'II', 3: 'III', 9: 'IX', 10: 'X', 11: 'XI' };
  for (const [h, t] of Object.entries(romans)) {
    const a = Math.PI / 2 - (h / 12) * TAU;
    const w = { XII: 2.55, I: 0.62, II: 1.45, III: 2.2, IX: 2.25, X: 1.55, XI: 2.05 }[t];
    fitText(t, Math.cos(a) * 10.85, Math.sin(a) * 10.85, 2.75, w, ROMAN, 700, -a + Math.PI / 2);
  }

  // power reserve: 0 h (top) to 48 h, dots every 4 h, numerals every 12 h
  const prAng = (h) => (16 - (h * 131) / 48) * DEG;
  for (let h = 0; h <= 48; h += 4) {
    const a = prAng(h);
    const [x, y] = P(PR[0] + Math.cos(a) * 3.95, PR[1] + Math.sin(a) * 3.95);
    ctx.beginPath(); ctx.arc(x, y, (h % 12 === 0 ? 0.19 : 0.1) * s, 0, TAU); ctx.fill();
  }
  [[12, 5.0], [24, 5.0], [36, 5.05], [48, 4.95]].forEach(([h, r]) => {
    const a = prAng(h);
    fitText(String(h), PR[0] + Math.cos(a) * r, PR[1] + Math.sin(a) * r - 0.15, 1.15, null, SANS, 500);
  });

  // pointer date ring: odd dates as numerals, even dates as dots
  for (let d = 1; d <= 31; d++) {
    const a = (86 - (d - 1) * 11.6) * DEG;
    const x = DATE[0] + Math.cos(a) * 4.62, y = DATE[1] + Math.sin(a) * 4.62;
    if (d % 2) fitText(String(d), x, y, 1.12, null, SANS, 500, -a + Math.PI / 2);
    else { const [px, py] = P(x, y); ctx.beginPath(); ctx.arc(px, py, 0.1 * s, 0, TAU); ctx.fill(); }
  }

  // small seconds
  {
    const [cx, cy] = P(...SECS);
    if (mode === 'color') {
      for (let r = 0.2; r < 2.8; r += 0.05) {
        ctx.strokeStyle = v.dial === 'slate' ? `rgba(0,0,0,${0.05 + 0.04 * Math.sin(r * 60)})` : `rgba(120,110,90,${0.03 + 0.02 * Math.sin(r * 60)})`;
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.arc(cx, cy, r * s, 0, TAU); ctx.stroke();
      }
    }
    ctx.strokeStyle = ink;
    for (let i = 0; i < 60; i++) {
      const a = Math.PI / 2 - (i / 60) * TAU;
      const big = i % 5 === 0;
      ctx.lineWidth = (big ? 0.17 : 0.09) * s;
      const ri = big ? 2.55 : 3.0, ro = 3.62;
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(a) * ri * s, cy - Math.sin(a) * ri * s);
      ctx.lineTo(cx + Math.cos(a) * ro * s, cy - Math.sin(a) * ro * s);
      ctx.stroke();
    }
  }

  // signature
  fitText('PATEK PHILIPPE', 4.45, 2.95, 1.5, 8.3, SANS, 600);
  fitText('GENEVE', 4.5, 1.75, 0.98, 3.0, SANS, 600);
  ctx.restore();
}

// Anisotropy directions for a radially brushed (sunburst) dial.
function sunburstAnisotropy(N = 256) {
  const data = new Uint8Array(N * N * 4);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    let dx = (x + 0.5) / N - 0.5, dy = (y + 0.5) / N - 0.5;
    const l = Math.hypot(dx, dy) || 1;
    dx /= l; dy /= l;
    const i = (y * N + x) * 4;
    data[i] = (dx * 0.5 + 0.5) * 255;
    data[i + 1] = (dy * 0.5 + 0.5) * 255;
    data[i + 2] = 255;
    data[i + 3] = 255;
  }
  const t = new THREE.DataTexture(data, N, N);
  t.needsUpdate = true;
  return t;
}

function moonDiscTexture() {
  const c = canvas(1024);
  const ctx = c.getContext('2d');
  const W = 1024, R = 4.3, s = W / (R * 2);
  const g = ctx.createRadialGradient(W / 2, W / 2, 0, W / 2, W / 2, W / 2);
  g.addColorStop(0, '#1d3a8c'); g.addColorStop(1, '#0c1d55');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, W);
  const star = (x, y, r) => {
    ctx.beginPath();
    for (let i = 0; i < 10; i++) {
      const a = -Math.PI / 2 + (i * Math.PI) / 5, rr = i % 2 ? r * 0.45 : r;
      ctx.lineTo(W / 2 + (x + Math.cos(a) * rr) * s, W / 2 - (y - Math.sin(a) * rr) * s);
    }
    ctx.closePath();
    ctx.fill();
  };
  const moon = (a) => {
    const x = Math.cos(a) * 2.8, y = Math.sin(a) * 2.8;
    const mg = ctx.createRadialGradient(W / 2 + (x - 0.3) * s, W / 2 - (y + 0.3) * s, 0, W / 2 + x * s, W / 2 - y * s, 1.05 * s);
    mg.addColorStop(0, '#f4f4f2'); mg.addColorStop(1, '#c9cacd');
    ctx.fillStyle = mg;
    ctx.beginPath(); ctx.arc(W / 2 + x * s, W / 2 - y * s, 1.02 * s, 0, TAU); ctx.fill();
    // frosted texture
    for (let i = 0; i < 400; i++) {
      const rr = Math.sqrt(Math.random()) * 1.0, aa = Math.random() * TAU;
      ctx.fillStyle = `rgba(${Math.random() < 0.5 ? '255,255,255' : '120,120,130'},0.25)`;
      ctx.fillRect(W / 2 + (x + Math.cos(aa) * rr) * s, W / 2 - (y + Math.sin(aa) * rr) * s, 2, 2);
    }
  };
  ctx.fillStyle = '#e9e9ec';
  // two moons opposite each other, with stars between them
  moon(0); moon(Math.PI);
  [[0.5, 1.6, 0.42], [-0.6, 2.4, 0.36], [-1.4, 1.3, 0.3], [0.9, 3.0, 0.28], [-0.5, -1.6, 0.42], [0.6, -2.4, 0.36], [1.4, -1.3, 0.3], [-0.9, -3.0, 0.28]].forEach(([x, y, r]) => { ctx.fillStyle = '#eceef2'; star(x, y, r); });
  return tex(c);
}

// Translucent print on the sapphire caseback (seen from behind).
function casebackPrintTexture(print, r) {
  const W = 2048, c = canvas(W), ctx = c.getContext('2d');
  const s = W / (r * 2);
  ctx.translate(W / 2, W / 2);
  ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
  if (print.kind === 'block') {
    // as printed on the 5057G: white serif, large, slightly translucent
    const line = (t, y, size, sup) => {
      ctx.font = `400 ${size * s}px ${PRINT_SERIF}`;
      ctx.fillStyle = 'rgba(255,255,255,0.62)';
      if (sup) {
        const [a, b, rest] = sup;
        const wa = ctx.measureText(a).width;
        ctx.font = `400 ${size * 0.55 * s}px ${PRINT_SERIF}`;
        const wb = ctx.measureText(b).width;
        ctx.font = `400 ${size * s}px ${PRINT_SERIF}`;
        const wr = ctx.measureText(rest).width;
        const total = wa + wb + wr;
        let x = -total / 2;
        ctx.textAlign = 'left';
        ctx.fillText(a, x, -y * s); x += wa;
        ctx.font = `400 ${size * 0.55 * s}px ${PRINT_SERIF}`;
        ctx.fillText(b, x, -y * s - size * 0.42 * s); x += wb;
        ctx.font = `400 ${size * s}px ${PRINT_SERIF}`;
        ctx.fillText(rest, x, -y * s);
        ctx.textAlign = 'center';
      } else ctx.fillText(t, 0, -y * s);
    };
    line('Cortina Watch', 2.2, 3.35);
    line(null, -1.75, 3.35, ['50', 'th', ' Anniversary']);
    line('Since 1972', -5.7, 3.35);
  } else {
    // as printed on the 5057R: black serif capitals following the window's edge
    // (seen from behind: starts at 9 o'clock, runs down and round the bottom, ends near 3)
    const text = [...print.text];
    ctx.font = `400 ${2.35 * s}px ${PRINT_SERIF}`;
    ctx.fillStyle = 'rgba(10,10,10,0.92)';
    const rr = (r - 1.75) * s;
    const glyph = text.map((ch) => ctx.measureText(ch).width);
    const span = 192 * DEG * rr;
    const track = (span - glyph.reduce((a, b) => a + b, 0)) / (text.length - 1);
    const widths = glyph.map((w, i) => w + (i < text.length - 1 ? track : 0));
    let a = 166 * DEG;
    text.forEach((ch, i) => {
      a += glyph[i] / 2 / rr;
      ctx.save();
      ctx.rotate(-a);
      ctx.translate(rr, 0);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText(ch, 0, 0);
      ctx.restore();
      a += (widths[i] - glyph[i] / 2) / rr;
    });
  }
  const t = tex(c);
  return t;
}

// Crocodile-scale normal map (tiles along the strap).
let crocNormal = null;
function getCrocNormal() {
  if (crocNormal) return crocNormal;
  const rnd = (i) => { const x = Math.sin(i * 127.1) * 43758.5453; return x - Math.floor(x); };
  crocNormal = normalFromHeight(512, (u, v) => {
    // 4 columns across, rows of varying length; scales are larger in the middle
    const cols = 4;
    const cu = u * cols, ci = Math.floor(cu), fu = cu - ci;
    const rows = 6 + (ci === 0 || ci === 3 ? 2 : 0);
    const off = rnd(ci + 1) * 0.5;
    const cv = (v + off) * rows, ri = Math.floor(cv), fv = cv - ri;
    const j = rnd(ci * 31 + ri * 7) * 0.12;
    const e = Math.min(fu, 1 - fu, fv + j, 1 - fv + j);
    return Math.min(1, e * 9) * 0.9 + rnd(ci * 13 + ri) * 0.08;
  }, 3.2);
  return crocNormal;
}

// Strap: rounded-rectangle section swept along a path in the YZ plane, with UVs
// and vertex colours (alligator on top, leather lining underneath).
function strapGeometry(path, w0, w1, thick, top, lining) {
  const segs = path.length, sec = 16;
  const pos = [], uv = [], col = [], idx = [];
  const cTop = new THREE.Color(top), cLin = new THREE.Color(lining);
  let len = 0;
  for (let i = 0; i < segs; i++) {
    if (i) len += Math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]);
    const [y, z] = path[i];
    const [y2, z2] = path[Math.min(segs - 1, i + 1)], [y0, z0] = path[Math.max(0, i - 1)];
    let ty = y2 - y0, tz = z2 - z0;
    const l = Math.hypot(ty, tz) || 1;
    ty /= l; tz /= l;
    const ny = -tz, nz = ty;
    const w = w0 + (w1 - w0) * (i / (segs - 1));
    for (let k = 0; k <= sec; k++) {
      const a = (k / sec) * TAU;
      const cx = Math.cos(a), cy = Math.sin(a);
      const sx = Math.sign(cx) * Math.pow(Math.abs(cx), 0.2) * (w / 2);
      const sn = Math.sign(cy) * Math.pow(Math.abs(cy), 0.35) * (thick / 2);
      pos.push(sx, y + ny * sn, z + nz * sn);
      uv.push(sx / w + 0.5, len / 26);
      const c = cy >= -0.05 ? cTop : cLin;
      col.push(c.r, c.g, c.b);
    }
  }
  for (let i = 0; i < segs - 1; i++) for (let k = 0; k < sec; k++) {
    const a = i * (sec + 1) + k, b = a + 1, c = a + sec + 1, d = c + 1;
    idx.push(a, b, c, b, d, c);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

// Faceted leaf hand (two halves tilted like a roof, so a ridge catches the light).
function leafHand(len, w, tail, { neck = 0.22, hub = 0.62 } = {}) {
  const half = (side) => {
    const sh = new THREE.Shape();
    sh.moveTo(0, -tail);
    sh.lineTo(side * neck * 0.5, -tail * 0.4);
    sh.lineTo(side * neck * 0.5, len * 0.12);
    sh.quadraticCurveTo(side * w * 0.62, len * 0.5, 0, len);
    sh.lineTo(0, -tail);
    const g = G.extrude(sh, 0.05, { bevel: 0.0, curveSegments: 18 });
    g.rotateY(side * 0.2);
    return g;
  };
  const hubG = G.extrude(G.annulusShape(hub, 0.12), 0.1, { bevel: 0.02, curveSegments: 32 });
  return G.merge([half(1), half(-1), hubG]);
}

// ---------------------------------------------------------------- build
// Returns { group, update(nowDate), flip(), ready, focus }.
export function build5057(key, { tzOffset = 8 } = {}) {
  const v = VARIANTS[key];
  const P = (o) => new THREE.MeshPhysicalMaterial(o);
  const M = {
    metal: P({ color: v.metal, metalness: 1, roughness: 0.1, envMapIntensity: 1.4 }),
    satin: P({ color: v.metalSatin, metalness: 1, roughness: 0.32, envMapIntensity: 1.2 }),
    hob: P({ color: v.metal, metalness: 1, roughness: 0.07, flatShading: true, envMapIntensity: 1.6 }),
    hand: v.hands === 'metal'
      ? P({ color: 0xeceef0, metalness: 1, roughness: 0.06, envMapIntensity: 1.6 })
      : P({ color: 0x0b0b0c, metalness: 0.7, roughness: 0.18, clearcoat: 1, clearcoatRoughness: 0.08 }),
    ruby: P({ color: 0xc23a6a, metalness: 0, roughness: 0.05, clearcoat: 1 }),
    sapphire: P({ color: 0xffffff, metalness: 0, roughness: 0.02, transparent: true, opacity: 0.08, depthWrite: false, envMapIntensity: 1.4, specularIntensity: 1 }),
    steel: P({ color: 0xc7cacd, metalness: 1, roughness: 0.2 }),
  };
  const mesh = (g, m) => { const o = new THREE.Mesh(g, m); o.castShadow = true; o.receiveShadow = true; return o; };
  const root = new THREE.Group(); // spins in inspect mode
  const W = new THREE.Group(); // the watch, in mm
  root.add(W);

  // ---- case middle
  W.add(mesh(G.latheZ([[15.2, -3.9], [17.35, -3.9], [17.85, -3.45], [18.0, -2.6], [18.0, 1.6], [15.2, 1.6], [15.2, -3.9]], 256), M.metal));
  // ---- bezel: polished edges, flat top carrying the hobnail pyramids
  const bezelTop = 2.62;
  W.add(mesh(G.latheZ([[15.25, 1.6], [18.02, 1.6], [18.1, 2.05], [18.0, 2.45], [17.86, bezelTop], [15.92, bezelTop], [15.7, 2.98], [15.38, 3.0], [15.25, 2.75], [15.25, 1.6]], 256), M.metal));
  {
    const rows = 4, rIn = 15.95, rOut = 17.82, N = 228;
    const pitch = (rOut - rIn) / rows;
    const cone = new THREE.ConeGeometry(Math.SQRT1_2, 1, 4, 1, false, Math.PI / 4).rotateX(Math.PI / 2).translate(0, 0, 0.5);
    const im = new THREE.InstancedMesh(cone, M.hob, rows * N);
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3(), p = new THREE.Vector3(), zAxis = new THREE.Vector3(0, 0, 1);
    let k = 0;
    for (let r = 0; r < rows; r++) {
      const rad = rIn + pitch * (r + 0.5);
      const tw = (TAU * rad) / N;
      for (let i = 0; i < N; i++) {
        const a = ((i + (r % 2) * 0.5) / N) * TAU;
        p.set(Math.cos(a) * rad, Math.sin(a) * rad, bezelTop - 0.005);
        q.setFromAxisAngle(zAxis, a);
        sc.set(pitch * 0.995, tw * 0.995, pitch * 0.52);
        m4.compose(p, q, sc);
        im.setMatrixAt(k++, m4);
      }
    }
    im.castShadow = true; im.receiveShadow = true;
    W.add(im);
  }
  // ---- straight lugs (two per side), fused to the case middle
  {
    const lugG = new RoundedBoxGeometry(2.3, 10.4, 4.7, 3, 0.45);
    for (const sx of [1, -1]) for (const sy of [1, -1]) {
      const lug = mesh(lugG, M.metal);
      lug.position.set(sx * 11.05, sy * 18.1, -1.25);
      W.add(lug);
    }
  }
  // ---- crown, fluted
  {
    const crownG = G.latheZ([[0.001, 0], [1.9, 0], [2.25, 0.3], [2.3, 2.3], [1.9, 2.7], [0.001, 2.7]], 180);
    const cp = crownG.attributes.position;
    for (let i = 0; i < cp.count; i++) {
      const x = cp.getX(i), y = cp.getY(i), z = cp.getZ(i), r = Math.hypot(x, y);
      if (r > 2.2 && z > 0.35 && z < 2.25) {
        const d = 0.16 * (0.5 + 0.5 * Math.cos(Math.atan2(y, x) * 18));
        cp.setXY(i, (x / r) * (r - d), (y / r) * (r - d));
      }
    }
    crownG.computeVertexNormals();
    crownG.rotateY(Math.PI / 2);
    const crown = mesh(crownG, M.metal);
    crown.position.set(17.9, 0, -1.0);
    W.add(crown);
  }

  // ---- dial (with the moon window cut out)
  const DW = 2048;
  const colorC = canvas(DW), ormC = canvas(DW);
  const drawAll = () => {
    drawDial(colorC.getContext('2d'), DW, v, 'color');
    drawDial(ormC.getContext('2d'), DW, v, 'orm');
  };
  drawAll();
  const dialMap = tex(colorC), dialOrm = tex(ormC, false);
  {
    const s = new THREE.Shape();
    s.absarc(0, 0, DIAL_R, 0, TAU, false);
    const { cx, cy, R } = MOON_WIN, h = R / 2;
    const win = new THREE.Path();
    win.moveTo(cx - R, cy);
    win.absarc(cx, cy, R, Math.PI, 0, true);
    win.absarc(cx + h, cy, h, 0, Math.PI, false);
    win.absarc(cx - h, cy, h, 0, Math.PI, false);
    win.closePath();
    s.holes.push(win);
    const g = G.extrude(s, Z.dialT, { bevel: 0.03, curveSegments: 160 });
    G.planarUV(g, [0, 0], DIAL_R * 2);
    const slate = v.dial === 'slate';
    const dm = P({
      map: dialMap, roughnessMap: dialOrm, metalnessMap: dialOrm, roughness: 1, metalness: 1,
      clearcoat: slate ? 0.5 : 0.85, clearcoatRoughness: slate ? 0.12 : 0.06,
      anisotropy: slate ? 0.85 : 0, anisotropyMap: slate ? sunburstAnisotropy() : null,
      envMapIntensity: slate ? 1.2 : 0.9,
    });
    const dial = mesh(g, [dm, M.satin]);
    dial.position.z = Z.dial;
    W.add(dial);
    // dark flange between dial and bezel
    W.add(mesh(G.latheZ([[15.3, Z.dial + Z.dialT], [15.45, 1.6], [15.2, 1.6], [15.2, Z.dial]], 160), slate ? P({ color: 0x2a2c30, metalness: 0.6, roughness: 0.35 }) : P({ color: 0xe9e7e0, metalness: 0, roughness: 0.4 })));
  }
  // ---- moon disc under the window
  const moonDisc = mesh(new THREE.CircleGeometry(4.3, 96), P({ map: moonDiscTexture(), metalness: 0.35, roughness: 0.3, clearcoat: 1, clearcoatRoughness: 0.05 }));
  moonDisc.position.set(DATE[0], DATE[1], Z.moon);
  W.add(moonDisc);
  const under = mesh(new THREE.CircleGeometry(15.2, 96), P({ color: 0x0a0a0c, roughness: 0.8 }));
  under.position.z = Z.moon - 0.05;
  W.add(under);

  // ---- hands
  const hand = (geo, at, z) => { const o = mesh(geo, M.hand); o.position.set(at[0], at[1], z); W.add(o); return o; };
  const H = {
    hour: hand(leafHand(8.1, 1.25, 1.6, { neck: 0.3, hub: 0.72 }), [0, 0], Z.hour),
    minute: hand(leafHand(13.0, 1.0, 2.0, { neck: 0.26, hub: 0.62 }), [0, 0], Z.minute),
    pr: hand(leafHand(3.75, 0.7, 0.9, { neck: 0.16, hub: 0.42 }), PR, Z.subHand),
    date: hand(leafHand(4.15, 0.55, 0.9, { neck: 0.14, hub: 0.4 }), DATE, Z.subHand),
    secs: hand(leafHand(3.25, 0.38, 0.9, { neck: 0.12, hub: 0.38 }), SECS, Z.subHand),
  };
  // pivot caps with the tiny pink jewel seen in close-ups
  [[0, 0, Z.minute + 0.1, 0.62], [...PR, Z.subHand + 0.1, 0.4], [...DATE, Z.subHand + 0.1, 0.4], [...SECS, Z.subHand + 0.1, 0.36]].forEach(([x, y, z, r]) => {
    const cap = mesh(G.latheZ([[0.001, 0.2], [r * 0.6, 0.18], [r, 0.05], [r, 0], [0.001, 0]], 48), M.hand);
    cap.position.set(x, y, z);
    W.add(cap);
    const j = mesh(new THREE.SphereGeometry(r * 0.22, 16, 8), M.ruby);
    j.position.set(x, y, z + 0.2);
    W.add(j);
  });

  // ---- crystal (slightly domed sapphire)
  const crystal = mesh(G.latheZ([[0.001, 3.38], [9, 3.33], [15.45, 3.02], [15.45, 2.8], [9, 3.1], [0.001, 3.15]], 128), M.sapphire);
  crystal.castShadow = false;
  crystal.renderOrder = 5;
  W.add(crystal);

  // ---- calibre 240, rotated as it sits in the 5057 (mini-rotor toward 9 seen from the back)
  const mvt = buildCal240({ gold: v.metal });
  mvt.group.rotation.z = Math.PI;
  mvt.group.position.z = -0.1;
  W.add(mvt.group);

  // ---- caseback: satin ring with eight polished pads, sapphire window, print
  W.add(mesh(G.latheZ([[14.45, -3.9], [17.36, -3.9], [17.3, -4.55], [16.95, -4.98], [14.65, -5.02], [14.45, -4.75], [14.45, -3.9]], 256), M.satin));
  {
    const pads = [];
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * TAU + TAU / 16;
      const b = new RoundedBoxGeometry(1.0, 1.55, 0.12, 2, 0.08);
      b.rotateZ(a);
      b.translate(Math.cos(a) * 15.85, Math.sin(a) * 15.85, -5.0);
      pads.push(b);
    }
    W.add(mesh(G.merge(pads), M.metal));
  }
  const backGlass = mesh(G.cylZ(14.55, 0.45, 128).translate(0, 0, -4.95), M.sapphire);
  backGlass.renderOrder = 5;
  W.add(backGlass);
  {
    const pm = new THREE.MeshPhysicalMaterial({ map: casebackPrintTexture(v.print, 14.4), transparent: true, depthWrite: false, roughness: 0.5, metalness: 0 });
    const print = new THREE.Mesh(new THREE.CircleGeometry(14.4, 96), pm);
    print.rotation.y = Math.PI; // faces the caseback (-Z), reads correctly from behind
    print.position.z = -4.97;
    print.renderOrder = 6;
    W.add(print);
  }
  // inner case floor behind the movement edge, so no gaps show at grazing angles
  W.add(mesh(G.latheZ([[13.7, -3.9], [15.25, -3.9], [15.25, 0.7], [13.7, 0.7]], 128), P({ color: 0x77797c, metalness: 1, roughness: 0.45 })));

  // ---- straps (alligator, glossy) curving back as on a display cushion
  {
    const path = [];
    let y = 0, z = 0;
    for (let i = 0; i <= 60; i++) {
      path.push([y, z]);
      const a = -Math.pow(i / 60, 1.35) * 2.3;
      y += Math.cos(a) * 0.72;
      z += Math.sin(a) * 0.72;
    }
    const n = getCrocNormal();
    n.wrapS = n.wrapT = THREE.RepeatWrapping;
    const sm = P({ vertexColors: true, color: 0xffffff, roughness: 0.3, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.12, normalMap: n, normalScale: new THREE.Vector2(0.9, 0.9), sheen: 0.4, sheenColor: new THREE.Color(0x30343c) });
    const sg = strapGeometry(path, 19.4, 16.2, 3.1, v.strap, v.lining);
    for (const sy of [1, -1]) {
      const g = sg.clone();
      if (sy < 0) g.rotateZ(Math.PI);
      const st = mesh(g, sm);
      st.position.set(0, sy * 21.2, -1.7);
      W.add(st);
      const bar = mesh(G.cylZ(0.45, 19.6, 12).rotateY(Math.PI / 2), M.steel);
      bar.position.set(-9.8, sy * 21.2, -1.7);
      W.add(bar);
    }
  }

  // ---------------------------------------------------------------- motion
  let flipped = false;
  function update(t, now = new Date()) {
    const local = new Date(now.getTime() + (tzOffset * 60 + now.getTimezoneOffset()) * 60000);
    const sec = local.getSeconds() + local.getMilliseconds() / 1000;
    const min = local.getMinutes() + sec / 60;
    const hr = (local.getHours() % 12) + min / 60;
    H.secs.rotation.z = -Math.floor(sec * 6) / 6 / 60 * TAU; // 3 Hz: six steps a second
    H.minute.rotation.z = -(min / 60) * TAU;
    H.hour.rotation.z = -(hr / 12) * TAU;
    const d = local.getDate();
    H.date.rotation.z = (86 - (d - 1) * 11.6 - 90) * DEG;
    H.pr.rotation.z = ((16 - (38 * 131) / 48) - 90) * DEG; // ~38 h in reserve
    const age = (((local.getTime() - Date.UTC(2000, 0, 6, 18, 14)) / 86400000) % SYNODIC + SYNODIC) % SYNODIC;
    moonDisc.rotation.z = Math.PI - (age / SYNODIC) * Math.PI;
    mvt.update(t);
  }
  update(0);

  // re-draw the dial once web fonts arrive
  const fontsReady = document.fonts ? document.fonts.ready.then(() => { drawAll(); dialMap.needsUpdate = true; dialOrm.needsUpdate = true; }) : Promise.resolve();

  return {
    root, watch: W, update, movement: mvt,
    ready: Promise.all([mvt.ready, fontsReady]),
    get flipped() { return flipped; },
    set flipped(f) { flipped = f; },
  };
}
