// Adapted from w-nston/3DWatch (src/lib). Shared geometry helpers, units in mm.
// Procedural geometry helpers for watch parts.
// Convention: all units are millimetres, parts are built in the XY plane and
// extruded along +Z starting at z = 0 (so a part's "position.z" is its seat).
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const TAU = Math.PI * 2;
export const DEG = Math.PI / 180;

// ---------- 2D vector helpers (plain arrays) ----------
export const v2 = (x, y) => [x, y];
export const dirDeg = (deg) => [Math.cos(deg * DEG), Math.sin(deg * DEG)];
export const polar = (p, r, deg) => [p[0] + Math.cos(deg * DEG) * r, p[1] + Math.sin(deg * DEG) * r];
export const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
export const angleDeg = (a, b) => Math.atan2(b[1] - a[1], b[0] - a[0]) / DEG;
export const lerp2 = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];

// Intersection of two circles, returns the solution on the left (+) or right (-) of a->b.
export function circleIntersect(a, ra, b, rb, side = 1) {
  const d = dist(a, b);
  const x = (d * d + ra * ra - rb * rb) / (2 * d);
  const h = Math.sqrt(Math.max(0, ra * ra - x * x));
  const ux = (b[0] - a[0]) / d, uy = (b[1] - a[1]) / d;
  return [a[0] + ux * x - uy * h * side, a[1] + uy * x + ux * h * side];
}

// ---------- UV utilities ----------
export function scaleUV(geo, s, ox = 0, oy = 0) {
  const uv = geo.attributes.uv;
  if (!uv) return geo;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * s + ox, uv.getY(i) * s + oy);
  uv.needsUpdate = true;
  return geo;
}

// Planar projection of XY to [0,1] inside a square of `size` centred at c.
export function planarUV(geo, c = [0, 0], size = 1) {
  const pos = geo.attributes.position;
  const uv = new Float32Array(pos.count * 2);
  for (let i = 0; i < pos.count; i++) {
    uv[i * 2] = (pos.getX(i) - c[0]) / size + 0.5;
    uv[i * 2 + 1] = (pos.getY(i) - c[1]) / size + 0.5;
  }
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  return geo;
}

// ---------- Extrusion ----------
export function extrude(shape, depth, { bevel = 0.03, curveSegments = 24, uvScale = 1 } = {}) {
  const b = Math.min(bevel, depth * 0.45);
  const g = new THREE.ExtrudeGeometry(shape, {
    depth: Math.max(depth - 2 * b, 0.001),
    bevelEnabled: b > 0,
    bevelThickness: b,
    bevelSize: b,
    bevelOffset: -b,
    bevelSegments: b > 0 ? 2 : 0,
    curveSegments,
  });
  g.translate(0, 0, b);
  if (uvScale !== 1) scaleUV(g, uvScale);
  return g;
}

// Cylinder whose axis is Z, spanning z in [0, h].
export function cylZ(r, h, seg = 32, rTop = r, open = false) {
  const g = new THREE.CylinderGeometry(rTop, r, h, seg, 1, open);
  g.rotateX(Math.PI / 2);
  g.translate(0, 0, h / 2);
  return g;
}

// Lathe about Z. pts = [[r, z], ...]
export function latheZ(pts, seg = 96) {
  const g = new THREE.LatheGeometry(pts.map(([r, z]) => new THREE.Vector2(r, z)), seg);
  g.rotateX(Math.PI / 2);
  return g;
}

export function annulusShape(rOut, rIn, a0 = 0, a1 = TAU) {
  const s = new THREE.Shape();
  if (a1 - a0 >= TAU - 1e-6) {
    s.absarc(0, 0, rOut, 0, TAU, false);
    if (rIn > 0) s.holes.push(circlePath(0, 0, rIn));
  } else {
    s.absarc(0, 0, rOut, a0, a1, false);
    s.absarc(0, 0, rIn, a1, a0, true);
    s.closePath();
  }
  return s;
}

export function circlePath(cx, cy, r) {
  const p = new THREE.Path();
  p.absarc(cx, cy, r, 0, TAU, true);
  return p;
}

// ---------- Gear teeth ----------
// Watch wheels use cycloidal (ogival) teeth: straight flanks with a rounded tip.
export function gearPoints(teeth, r, { add, ded, tooth = 0.46, tipSeg = 5, phase = 0, a0 = null, a1 = null } = {}) {
  const m = (2 * r) / teeth;
  const ra = r + (add ?? 1.15 * m);
  const rd = r - (ded ?? 1.45 * m);
  const p = TAU / teeth;
  const pts = [];
  const P = (rad, ang) => [Math.cos(ang) * rad, Math.sin(ang) * rad];
  for (let i = 0; i < teeth; i++) {
    const c = phase + i * p;
    if (a0 !== null && (c < a0 || c > a1)) continue;
    const hw = (p * tooth) / 2;
    const hwr = hw * 1.02;
    pts.push(P(rd, c - p / 2));
    pts.push(P(rd, c - hwr));
    pts.push(P(r, c - hw));
    for (let k = 1; k < tipSeg; k++) {
      const th = (Math.PI * k) / tipSeg;
      pts.push(P(r + (ra - r) * Math.sin(th), c - hw * Math.cos(th)));
    }
    pts.push(P(r, c + hw));
    pts.push(P(rd, c + hwr));
  }
  return { pts, ra, rd };
}

export function gearShape(teeth, r, opts = {}) {
  const { pts } = gearPoints(teeth, r, opts);
  const s = new THREE.Shape();
  pts.forEach(([x, y], i) => (i ? s.lineTo(x, y) : s.moveTo(x, y)));
  s.closePath();
  return s;
}

// Holes between (optionally curved) spokes – Breguet-style "crossings".
export function spokeHoles({ spokes = 5, rimIn, hubOut, width = 0.5, curve = 0, phase = 0, seg = 10 }) {
  const holes = [];
  const edge = (i, rho, side) => {
    const t = (rho - hubOut) / (rimIn - hubOut);
    const w = width * (1.25 - 0.4 * t);
    const c = phase + (i * TAU) / spokes + curve * t * t * 0.6 + curve * t * 0.4;
    return c + (side * w) / 2 / rho;
  };
  for (let i = 0; i < spokes; i++) {
    const path = new THREE.Path();
    const P = (rho, ang) => [Math.cos(ang) * rho, Math.sin(ang) * rho];
    const pts = [];
    for (let k = 0; k <= seg; k++) {
      const rho = hubOut + ((rimIn - hubOut) * k) / seg;
      pts.push(P(rho, edge(i, rho, +1)));
    }
    let r0 = edge(i, rimIn, +1), r1 = edge(i + 1, rimIn, -1);
    if (r1 < r0) r1 += TAU;
    for (let k = 1; k < 16; k++) pts.push(P(rimIn, r0 + ((r1 - r0) * k) / 16));
    for (let k = seg; k >= 0; k--) {
      const rho = hubOut + ((rimIn - hubOut) * k) / seg;
      pts.push(P(rho, edge(i + 1, rho, -1)));
    }
    let h0 = edge(i + 1, hubOut, -1), h1 = edge(i, hubOut, +1);
    while (h1 > h0) h1 -= TAU;
    while (h0 - h1 > TAU) h1 += TAU;
    for (let k = 1; k < 8; k++) pts.push(P(hubOut, h0 + ((h1 - h0) * k) / 8));
    pts.forEach(([x, y], j) => (j ? path.lineTo(x, y) : path.moveTo(x, y)));
    path.closePath();
    holes.push(path);
  }
  return holes;
}

// A complete wheel: toothed rim + crossings + arbor hole.
export function wheelGeometry({ teeth, r, thick = 0.15, spokes = 5, rim = 0.55, hub = 0.7, spokeW = 0.45, curve = 0.5, arbor = 0.12, bevel = 0.015, phase = 0 }) {
  const s = gearShape(teeth, r, { phase });
  const { rd } = gearPoints(teeth, r);
  if (spokes > 0) spokeHoles({ spokes, rimIn: rd - rim, hubOut: hub, width: spokeW, curve }).forEach((h) => s.holes.push(h));
  if (arbor > 0) s.holes.push(circlePath(0, 0, arbor));
  return extrude(s, thick, { bevel, curveSegments: 6, uvScale: 1 });
}

export function pinionGeometry({ leaves, r, h, arbor = 0 }) {
  const s = gearShape(leaves, r, { tooth: 0.5, add: r * 0.28, ded: r * 0.32, tipSeg: 6 });
  if (arbor > 0) s.holes.push(circlePath(0, 0, arbor));
  return extrude(s, h, { bevel: Math.min(0.02, h * 0.1), curveSegments: 6 });
}

// ---------- Rounded polygons & bars ----------
export function roundedShape(pts, target = null) {
  const s = target || new THREE.Shape();
  const n = pts.length;
  for (let i = 0; i < n; i++) {
    const [x, y, r = 0] = pts[i];
    const prev = pts[(i - 1 + n) % n], next = pts[(i + 1) % n];
    const l1 = Math.hypot(prev[0] - x, prev[1] - y), l2 = Math.hypot(next[0] - x, next[1] - y);
    const d = Math.min(r, l1 * 0.48, l2 * 0.48);
    const a = [x + ((prev[0] - x) / l1) * d, y + ((prev[1] - y) / l1) * d];
    const b = [x + ((next[0] - x) / l2) * d, y + ((next[1] - y) / l2) * d];
    if (i === 0) s.moveTo(a[0], a[1]);
    else s.lineTo(a[0], a[1]);
    if (d > 0) s.quadraticCurveTo(x, y, b[0], b[1]);
  }
  s.closePath();
  return s;
}

export function roundedPath(pts) {
  return roundedShape(pts, new THREE.Path());
}

// A bar with semicircular ends from a to b (widths wa, wb).
export function barShape(a, b, wa, wb = wa, target = null) {
  const s = target || new THREE.Shape();
  const th = Math.atan2(b[1] - a[1], b[0] - a[0]);
  const nx = -Math.sin(th), ny = Math.cos(th);
  s.moveTo(a[0] + (nx * wa) / 2, a[1] + (ny * wa) / 2);
  s.lineTo(b[0] + (nx * wb) / 2, b[1] + (ny * wb) / 2);
  s.absarc(b[0], b[1], wb / 2, th + Math.PI / 2, th - Math.PI / 2, true);
  s.lineTo(a[0] - (nx * wa) / 2, a[1] - (ny * wa) / 2);
  s.absarc(a[0], a[1], wa / 2, th - Math.PI / 2, th - (3 * Math.PI) / 2, true);
  s.closePath();
  return s;
}

// ---------- Small standard components ----------
// Slotted screw with a domed head; returns merged geometries per material slot.
export function screwGeometry(r = 0.45, h = 0.32, slot = 0.1) {
  const base = cylZ(r, h * 0.45, 28);
  const a = Math.acos(slot / 2 / r);
  const half = new THREE.Shape();
  half.moveTo(slot / 2, -Math.sin(a) * r);
  half.lineTo(slot / 2, Math.sin(a) * r);
  half.absarc(0, 0, r, a, -a, true);
  half.closePath();
  const top1 = extrude(half, h * 0.55, { bevel: Math.min(0.06, r * 0.18), curveSegments: 16 });
  const top2 = top1.clone();
  top2.rotateZ(Math.PI);
  [top1, top2].forEach((g) => g.translate(0, 0, h * 0.45));
  const shank = cylZ(r * 0.5, 0.6, 12);
  shank.translate(0, 0, -0.6);
  return mergeGeometries([base, top1.toNonIndexed(), top2.toNonIndexed(), shank].map((g) => (g.index ? g.toNonIndexed() : g)).map(stripGroups));
}

export function stripGroups(g) {
  g.clearGroups();
  // keep only attributes common to all our generated geometry
  for (const k of Object.keys(g.attributes)) if (!['position', 'normal', 'uv'].includes(k)) g.deleteAttribute(k);
  return g;
}

export function merge(geos) {
  return mergeGeometries(geos.map((g) => stripGroups(g.index ? g.toNonIndexed() : g)));
}

// Jewel set in a polished countersink ("olive-drilled" ruby with oil sink).
export function jewelGeometries(r = 0.36) {
  const sink = extrude(annulusShape(r * 1.55, r * 0.98), 0.06, { bevel: 0.02 });
  const ruby = latheZ(
    [
      [0.001, 0.0],
      [r, 0.0],
      [r, 0.05],
      [r * 0.86, 0.1],
      [r * 0.32, 0.1],
      [r * 0.2, 0.06],
      [0.001, 0.06],
    ],
    32,
  );
  return { sink, ruby };
}

// Flat spiral ribbon (hairspring-like), returns a BufferGeometry whose positions
// can be updated every frame with `updateSpiral`.
export function ribbonGeometry(n) {
  const g = new THREE.BufferGeometry();
  const pos = new Float32Array(n * 2 * 3);
  const nor = new Float32Array(n * 2 * 3);
  const idx = [];
  for (let i = 0; i < n - 1; i++) {
    const a = i * 2, b = a + 1, c = a + 2, d = a + 3;
    idx.push(a, c, b, b, c, d);
  }
  g.setIndex(idx);
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  return g;
}

export function updateRibbon(g, pts, height) {
  // pts: array of [x, y, z]
  const pos = g.attributes.position.array;
  const nor = g.attributes.normal.array;
  const n = pts.length;
  for (let i = 0; i < n; i++) {
    const p = pts[i];
    const q = pts[Math.min(n - 1, i + 1)], o = pts[Math.max(0, i - 1)];
    let tx = q[0] - o[0], ty = q[1] - o[1];
    const l = Math.hypot(tx, ty) || 1;
    tx /= l; ty /= l;
    const k = i * 6;
    pos[k] = p[0]; pos[k + 1] = p[1]; pos[k + 2] = p[2];
    pos[k + 3] = p[0]; pos[k + 4] = p[1]; pos[k + 5] = p[2] + height;
    nor[k] = nor[k + 3] = ty;
    nor[k + 1] = nor[k + 4] = -tx;
    nor[k + 2] = nor[k + 5] = 0;
  }
  g.attributes.position.needsUpdate = true;
  g.attributes.normal.needsUpdate = true;
  g.computeBoundingSphere();
}

// Sweep a rounded-rectangle section along a 2D path in the YZ plane (for straps).
export function strapGeometry(path, width0, width1, thick) {
  const segs = path.length;
  const sec = 12;
  const pos = [];
  const idx = [];
  for (let i = 0; i < segs; i++) {
    const [y, z] = path[i];
    const [y2, z2] = path[Math.min(segs - 1, i + 1)];
    const [y0, z0] = path[Math.max(0, i - 1)];
    let ty = y2 - y0, tz = z2 - z0;
    const l = Math.hypot(ty, tz) || 1;
    ty /= l; tz /= l;
    const ny = -tz, nz = ty; // in-plane normal
    const w = width0 + (width1 - width0) * (i / (segs - 1));
    for (let k = 0; k < sec; k++) {
      const a = (k / sec) * TAU;
      const cx = Math.cos(a), cy = Math.sin(a);
      // superellipse-ish section
      const sx = Math.sign(cx) * Math.pow(Math.abs(cx), 0.25) * (w / 2);
      const sn = Math.sign(cy) * Math.pow(Math.abs(cy), 0.5) * (thick / 2);
      pos.push(sx, y + ny * sn, z + nz * sn);
    }
  }
  for (let i = 0; i < segs - 1; i++)
    for (let k = 0; k < sec; k++) {
      const a = i * sec + k, b = i * sec + ((k + 1) % sec), c = a + sec, d = b + sec;
      idx.push(a, b, c, b, d, c);
    }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}
