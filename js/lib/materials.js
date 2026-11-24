// Adapted from w-nston/3DWatch (src/lib). Materials and procedural textures.
// Materials and procedurally generated textures (no external image assets).
import * as THREE from 'three';

function rng(seed = 1) {
  let s = seed >>> 0;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
}

// Build a tangent-space normal map from a height function h(u, v) in [0,1]².
export function normalFromHeight(size, h, strength = 1, { wrap = true } = {}) {
  const hf = new Float32Array(size * size);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) hf[y * size + x] = h((x + 0.5) / size, (y + 0.5) / size, x, y);
  const data = new Uint8Array(size * size * 4);
  const at = (x, y) => {
    if (wrap) { x = (x + size) % size; y = (y + size) % size; }
    else { x = Math.min(size - 1, Math.max(0, x)); y = Math.min(size - 1, Math.max(0, y)); }
    return hf[y * size + x];
  };
  for (let y = 0; y < size; y++)
    for (let x = 0; x < size; x++) {
      const dx = (at(x + 1, y) - at(x - 1, y)) * strength;
      const dy = (at(x, y + 1) - at(x, y - 1)) * strength;
      let nx = -dx, ny = -dy, nz = 1;
      const l = Math.hypot(nx, ny, nz);
      const i = (y * size + x) * 4;
      data[i] = ((nx / l) * 0.5 + 0.5) * 255;
      data[i + 1] = ((ny / l) * 0.5 + 0.5) * 255;
      data[i + 2] = ((nz / l) * 0.5 + 0.5) * 255;
      data[i + 3] = 255;
    }
  const t = new THREE.DataTexture(data, size, size, THREE.RGBAFormat);
  t.wrapS = t.wrapT = wrap ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
  t.generateMipmaps = true;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.magFilter = THREE.LinearFilter;
  t.anisotropy = 8;
  t.needsUpdate = true;
  return t;
}

function valueNoise(size, cells, seed) {
  const r = rng(seed);
  const g = Array.from({ length: cells * cells }, r);
  const G = (x, y) => g[((y + cells) % cells) * cells + ((x + cells) % cells)];
  return (u, v) => {
    const x = u * cells, y = v * cells;
    const xi = Math.floor(x), yi = Math.floor(y);
    let fx = x - xi, fy = y - yi;
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy);
    const a = G(xi, yi), b = G(xi + 1, yi), c = G(xi, yi + 1), d = G(xi + 1, yi + 1);
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy;
  };
}

// Sand-blasted / frosted ("sablé") finish.
function frostNormal() {
  const n1 = valueNoise(256, 64, 3), n2 = valueNoise(256, 128, 7), n3 = valueNoise(256, 32, 11);
  return normalFromHeight(256, (u, v) => n1(u, v) * 0.5 + n2(u, v) * 0.35 + n3(u, v) * 0.3, 2.2);
}

// Concentric circular graining for barrel covers and wheels (planar UV 0..1).
export function circularGrainNormal(size = 512, seed = 5) {
  const r = rng(seed);
  const rings = Array.from({ length: 2048 }, () => r());
  const n = valueNoise(size, 24, seed + 1);
  return normalFromHeight(
    size,
    (u, v) => {
      const d = Math.hypot(u - 0.5, v - 0.5) * 2;
      const k = d * 260;
      const i = Math.floor(k);
      const f = k - i;
      const a = rings[i % 2048], b = rings[(i + 1) % 2048];
      return (a + (b - a) * f) * 0.25 + n(u, v) * 0.03;
    },
    1.2,
    { wrap: false },
  );
}

// Vertical straight graining (brushed) – for rotor arm and bars.
function straightGrainNormal(size = 256) {
  const r = rng(21);
  const cols = Array.from({ length: size * 4 }, r);
  return normalFromHeight(size, (u) => cols[Math.floor(u * size * 4)] * 0.5, 2.5);
}

// Clous de Paris (hobnail) guilloché: a grid of tiny pyramids, rotated 45°.
export function clousDeParisNormal(size = 1024, count = 40, flat = null) {
  return normalFromHeight(
    size,
    (u, v) => {
      if (flat && flat(u, v)) return 0.25;
      const d = Math.hypot(u - 0.5, v - 0.5);
      if (d > 0.5) return 0.25;
      const x = (u - 0.5) * count, y = (v - 0.5) * count;
      const a = (x + y) * Math.SQRT1_2, b = (y - x) * Math.SQRT1_2;
      const fa = a - Math.floor(a) - 0.5, fb = b - Math.floor(b) - 0.5;
      return (0.5 - Math.max(Math.abs(fa), Math.abs(fb))) * 1.0;
    },
    size / count * 0.9,
    { wrap: false },
  );
}

// ---------- Canvas textures ----------
export function canvasTexture(w, h, draw, { srgb = true } = {}) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d');
  draw(ctx, w, h);
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

const SERIF = '"Cormorant Garamond", "Times New Roman", serif';
const SCRIPT = '"Pinyon Script", "Snell Roundhand", cursive';

// Chapter ring: Roman numerals, minute track with pearled dots – drawn onto a
// square that maps to a RingGeometry via planar UV (outer radius = half size).
export function chapterRingTexture(rOut, rIn) {
  return canvasTexture(2048, 2048, (ctx, W) => {
    const c = W / 2, s = c / rOut;
    ctx.fillStyle = '#e8e6e1';
    ctx.fillRect(0, 0, W, W);
    ctx.translate(c, c);
    ctx.scale(1, -1); // planar uv: +v is +y
    // fine concentric guilloché (flinqué-like rings) for the outer chapter
    for (let r = rIn * s; r < rOut * s; r += 2.2) {
      ctx.strokeStyle = `rgba(120,120,125,${0.08 + 0.06 * Math.sin(r * 0.9)})`;
      ctx.lineWidth = 0.8;
      ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
    }
    // minute track: two thin circles with dots
    const rt1 = (rOut - 0.55) * s, rt2 = (rOut - 1.05) * s;
    ctx.strokeStyle = '#2a2a2e'; ctx.lineWidth = 2;
    [rt1, rt2].forEach((r) => { ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke(); });
    for (let i = 0; i < 60; i++) {
      const a = (i / 60) * Math.PI * 2;
      const rr = (rt1 + rt2) / 2;
      ctx.fillStyle = '#26262a';
      ctx.beginPath();
      ctx.arc(Math.sin(a) * rr, Math.cos(a) * rr, i % 5 === 0 ? 5 : 2.6, 0, Math.PI * 2);
      ctx.fill();
    }
    // inner hobnail border (a beaded ring)
    for (let i = 0; i < 180; i++) {
      const a = (i / 180) * Math.PI * 2, rr = (rIn + 0.25) * s;
      ctx.fillStyle = 'rgba(80,80,85,0.35)';
      ctx.beginPath(); ctx.arc(Math.sin(a) * rr, Math.cos(a) * rr, 2.3, 0, Math.PI * 2); ctx.fill();
    }
    // numerals, radially oriented as on Breguet chapter rings
    const numerals = ['XII', 'I', 'II', 'III', 'IIII', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI'];
    ctx.fillStyle = '#1b1b1f';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const rn = (rIn + (rOut - 1.05 - rIn) * 0.5) * s;
    numerals.forEach((n, i) => {
      const a = (i / 12) * Math.PI * 2;
      ctx.save();
      ctx.rotate(-a);
      ctx.translate(0, rn);
      ctx.scale(1, -1);
      ctx.font = `600 ${Math.round(1.55 * s)}px ${SERIF}`;
      ctx.fillText(n, 0, 0);
      ctx.restore();
    });
  });
}

// Dial centre colour map (signature cartouche and serial plaque over guilloché).
export function dialCenterTexture(radius, serial = '4056') {
  return canvasTexture(2048, 2048, (ctx, W) => {
    const c = W / 2, s = c / radius;
    ctx.fillStyle = '#e4e2dc';
    ctx.fillRect(0, 0, W, W);
    ctx.translate(c, c);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    // BREGUET cartouche (arched)
    const cartouche = (y, w, h, text, size) => {
      ctx.fillStyle = '#f1efea';
      ctx.strokeStyle = '#8c8b88';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.roundRect(-w / 2, y - h / 2, w, h, 10);
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#1b1b1f';
      ctx.font = `600 ${size}px ${SERIF}`;
      ctx.fillText(text, 0, y + 2);
    };
    cartouche(-radius * 0.5 * s, 2.9 * s, 0.95 * s, 'BREGUET', 0.62 * s);
    cartouche(radius * 0.52 * s, 2.7 * s, 0.9 * s, `Nº ${serial}`, 0.55 * s);
    ctx.fillStyle = '#3a3a3e';
    ctx.font = `500 ${0.28 * s}px ${SERIF}`;
    ctx.fillText('SWISS  GUILLOCHÉ  MAIN', 0, radius * 0.83 * s);
  });
}

// Retrograde seconds sector scale: drawn in polar coords around the sector pivot.
export function retroScaleTexture(rOut, rIn, a0, a1) {
  return canvasTexture(2048, 2048, (ctx, W) => {
    const c = W / 2, s = c / rOut;
    ctx.fillStyle = '#e6e4df';
    ctx.fillRect(0, 0, W, W);
    ctx.translate(c, c);
    ctx.scale(1, -1);
    // brushed-looking concentric lines
    for (let r = rIn * s; r < rOut * s; r += 2) {
      ctx.strokeStyle = `rgba(110,110,115,${0.05 + 0.05 * Math.sin(r * 1.3)})`;
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
    }
    const rr = (rIn + (rOut - rIn) * 0.34) * s;
    for (let i = 0; i <= 60; i++) {
      const a = a0 + ((a1 - a0) * i) / 60;
      ctx.fillStyle = '#1e1e22';
      ctx.beginPath();
      const big = i % 10 === 0;
      ctx.arc(Math.cos(a) * rr, Math.sin(a) * rr, big ? 7 : 3.4, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    [0, 30, 60].forEach((v) => {
      const a = a0 + ((a1 - a0) * v) / 60;
      const rt = (rIn + (rOut - rIn) * 0.7) * s;
      ctx.save();
      ctx.rotate(a);
      ctx.translate(rt, 0);
      ctx.rotate(Math.PI / 2);
      ctx.scale(1, -1);
      ctx.fillStyle = '#1b1b1f';
      ctx.font = `600 ${0.9 * s}px ${SERIF}`;
      ctx.fillText(String(v), 0, 0);
      ctx.restore();
    });
  });
}

// Signature engraving for the oscillating weight (planar uv over bounding square).
export function rotorTexture(size, center) {
  return canvasTexture(2048, 2048, (ctx, W) => {
    const s = W / size;
    ctx.fillStyle = '#ecebea';
    ctx.fillRect(0, 0, W, W);
    ctx.translate(W / 2, W / 2);
    ctx.scale(1, -1);
    ctx.translate(-center[0] * s, -center[1] * s);
    ctx.scale(1, -1);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = `${2.6 * s}px ${SCRIPT}`;
    ctx.fillStyle = '#6f6f72';
    ctx.fillText('Breguet', 0, 12.4 * s);
    ctx.fillStyle = '#fafafa';
    ctx.fillText('Breguet', -0.04 * s, 12.36 * s);
  });
}

// Engraved text on the back of the movement (transparent decal).
export function movementEngravingTexture(size) {
  return canvasTexture(2048, 2048, (ctx, W) => {
    const s = W / size;
    ctx.clearRect(0, 0, W, W);
    ctx.translate(W / 2, W / 2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const t = (text, x, y, sz, font = SERIF, weight = 600) => {
      ctx.font = `${weight} ${sz * s}px ${font}`;
      ctx.fillStyle = 'rgba(20,20,22,0.85)';
      ctx.fillText(text, x * s, -y * s);
      ctx.fillStyle = 'rgba(210,210,215,0.35)';
      ctx.fillText(text, x * s - 1.5, -y * s - 1.5);
    };
    // viewed from the back, so x is mirrored relative to the dial side.
    t('CAL 505SR1', 2.5, 13.2, 0.75);
    t('Breguet', 2.2, 10.6, 1.9, SCRIPT, 400);
    t('ADJUSTED', -1.0, 8.4, 0.62);
    t('SIX  ( 6 )  POSITIONS', 0.2, 6.9, 0.62);
    t('THIRTY-EIGHT', 7.0, 4.2, 0.6);
    t('( 38 )  JEWELS', 7.0, 3.2, 0.6);
  });
}

// Caseback bezel engraving (annulus, planar uv over bounding square).
export function casebackTextTexture(rOut, rIn, lines) {
  return canvasTexture(2048, 2048, (ctx, W) => {
    const c = W / 2, s = c / rOut;
    const g = ctx.createRadialGradient(c, c, rIn * s, c, c, rOut * s);
    g.addColorStop(0, '#c9c9c7'); g.addColorStop(1, '#e8e8e6');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, W);
    ctx.translate(c, c);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const rr = (rIn + rOut) / 2 * s;
    lines.forEach(({ text, at }) => {
      const chars = [...text];
      const step = 0.052;
      const start = at - ((chars.length - 1) * step) / 2;
      chars.forEach((ch, i) => {
        const a = start + i * step;
        ctx.save();
        ctx.rotate(a);
        ctx.translate(0, -rr);
        ctx.font = `700 ${1.05 * s}px ${SERIF}`;
        ctx.fillStyle = '#5a5a5c';
        ctx.fillText(ch, 0, 0);
        ctx.restore();
      });
    });
  });
}

// ---------- Material library ----------
export function createMaterials() {
  const frost = frostNormal();
  const straight = straightGrainNormal();
  const P = (o) => new THREE.MeshPhysicalMaterial(o);
  const m = {};

  m.plate = P({ color: 0x55585e, metalness: 0.95, roughness: 0.72, normalMap: frost, normalScale: new THREE.Vector2(0.3, 0.3) });
  m.bridge = P({ color: 0x676a70, metalness: 0.95, roughness: 0.64, normalMap: frost, normalScale: new THREE.Vector2(0.32, 0.32) });
  m.anglage = P({ color: 0xc9ccd0, metalness: 1, roughness: 0.12 }); // polished bevels & flanks
  m.steel = P({ color: 0xc6c9cd, metalness: 1, roughness: 0.16 });
  m.steelBrushed = P({ color: 0xc7c9cc, metalness: 1, roughness: 0.3, normalMap: straight, normalScale: new THREE.Vector2(0.35, 0.35) });
  m.rhodium = P({ color: 0xbcc0c6, metalness: 1, roughness: 0.28 });
  m.wheel = P({ color: 0xa4a8ae, metalness: 1, roughness: 0.34 });
  m.gilt = P({ color: 0xdcb870, metalness: 1, roughness: 0.3 });
  m.blued = P({ color: 0x08175a, metalness: 0.5, roughness: 0.32, clearcoat: 0.3, clearcoatRoughness: 0.15, envMapIntensity: 0.3 });
  m.ruby = P({ color: 0xc4123c, metalness: 0, roughness: 0.06, clearcoat: 1, clearcoatRoughness: 0.02, emissive: 0x3a0010, emissiveIntensity: 0.6, sheen: 0 });
  m.dark = P({ color: 0x151517, metalness: 0.4, roughness: 0.6 });
  m.whiteGold = P({ color: 0xe6e6e4, metalness: 1, roughness: 0.1, side: THREE.DoubleSide });
  m.whiteGoldSatin = P({ color: 0xdcdcda, metalness: 1, roughness: 0.28, side: THREE.DoubleSide });
  m.sapphire = P({ color: 0x000000, metalness: 0, roughness: 0.02, transparent: true, opacity: 0.1, depthWrite: false, specularIntensity: 0.3, envMapIntensity: 0.25, side: THREE.FrontSide });
  m.leather = P({ color: 0x15171f, metalness: 0, roughness: 0.62, sheen: 0.4, sheenColor: new THREE.Color(0x303848) });
  m.leatherLining = P({ color: 0xd8c3a8, metalness: 0, roughness: 0.8 });
  m.ceramic = P({ color: 0xf2f2f0, metalness: 0, roughness: 0.25, clearcoat: 0.8 });
  m.mainspring = P({ color: 0x9fa5ad, metalness: 1, roughness: 0.35 });
  m.hairspring = P({ color: 0x9aa3b8, metalness: 0.9, roughness: 0.25, side: THREE.DoubleSide });
  m.silicon = P({ color: 0x3d4466, metalness: 0.7, roughness: 0.18, iridescence: 0.6, iridescenceIOR: 1.6 });
  m.platinum = P({ color: 0xe9e9eb, metalness: 1, roughness: 0.07 });

  m.ghost = new THREE.MeshStandardMaterial({ color: 0x8e9fbf, transparent: true, opacity: 0.045, depthWrite: false, roughness: 1, metalness: 0 });
  m.ghostFaint = new THREE.MeshStandardMaterial({ color: 0x8e9fbf, transparent: true, opacity: 0.018, depthWrite: false, roughness: 1, metalness: 0 });
  m._textures = { frost, straight };
  return m;
}
