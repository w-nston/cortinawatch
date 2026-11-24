// Canvas textures for the gallery architecture and exhibits.
import * as THREE from 'three';

export const SERIF = '"Cormorant Garamond", "Times New Roman", Georgia, serif';
export const SANS = '"Jost", "Helvetica Neue", Arial, sans-serif';

export function canvasTexture(w, h, draw, { srgb = true, repeat = null } = {}) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat); }
  return t;
}

function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

// soft radial glow (for light pools and halos)
export function glowTexture(rgb = '255,220,170') {
  return canvasTexture(256, 256, (g, W) => {
    const r = g.createRadialGradient(W / 2, W / 2, 0, W / 2, W / 2, W / 2);
    r.addColorStop(0, `rgba(${rgb},1)`);
    r.addColorStop(0.35, `rgba(${rgb},0.45)`);
    r.addColorStop(1, `rgba(${rgb},0)`);
    g.fillStyle = r; g.fillRect(0, 0, W, W);
  });
}

// warm limestone plaster
export function stoneTexture() {
  return canvasTexture(1024, 1024, (g, W) => {
    g.fillStyle = '#5b5148'; g.fillRect(0, 0, W, W);
    const r = rng(4);
    for (let i = 0; i < 9000; i++) {
      const x = r() * W, y = r() * W, s = 1 + r() * 3;
      g.fillStyle = `rgba(${r() < 0.5 ? '255,240,220' : '20,14,10'},${0.03 + r() * 0.05})`;
      g.fillRect(x, y, s, s);
    }
    for (let i = 0; i < 60; i++) {
      const x = r() * W, y = r() * W;
      const gr = g.createRadialGradient(x, y, 0, x, y, 60 + r() * 120);
      gr.addColorStop(0, `rgba(${r() < 0.5 ? '255,235,210' : '30,20,12'},0.06)`);
      gr.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = gr; g.fillRect(0, 0, W, W);
    }
  }, { repeat: [1, 1] });
}

// polished dark stone floor with faint veining and joints
export function floorTexture() {
  return canvasTexture(1024, 1024, (g, W) => {
    g.fillStyle = '#1c1916'; g.fillRect(0, 0, W, W);
    const r = rng(9);
    for (let i = 0; i < 40; i++) {
      g.strokeStyle = `rgba(200,180,150,${0.03 + r() * 0.04})`;
      g.lineWidth = 0.5 + r() * 1.5;
      g.beginPath();
      let x = r() * W, y = r() * W;
      g.moveTo(x, y);
      for (let k = 0; k < 8; k++) { x += (r() - 0.5) * 160; y += (r() - 0.3) * 120; g.lineTo(x, y); }
      g.stroke();
    }
    g.strokeStyle = 'rgba(0,0,0,0.55)'; g.lineWidth = 3;
    g.strokeRect(0, 0, W, W);
  }, { repeat: [5, 30] });
}

export function walnutTexture() {
  return canvasTexture(512, 1024, (g, W, H) => {
    g.fillStyle = '#3b2618'; g.fillRect(0, 0, W, H);
    const r = rng(13);
    for (let i = 0; i < 260; i++) {
      const x = r() * W;
      g.strokeStyle = `rgba(${r() < 0.5 ? '120,80,50' : '20,10,5'},${0.08 + r() * 0.12})`;
      g.lineWidth = 0.5 + r() * 2.5;
      g.beginPath(); g.moveTo(x, 0);
      for (let y = 0; y <= H; y += 64) g.lineTo(x + Math.sin(y * 0.01 + i) * 6 * r(), y);
      g.stroke();
    }
  });
}

// Wall lettering: big year + small caps label (transparent background).
export function wallText(big, small) {
  return canvasTexture(1600, 1000, (g, W, H) => {
    g.clearRect(0, 0, W, H);
    g.textAlign = 'center';
    g.textBaseline = 'alphabetic';
    const grad = g.createLinearGradient(0, 120, 0, 600);
    grad.addColorStop(0, '#e9d3a4'); grad.addColorStop(0.5, '#c39a5c'); grad.addColorStop(1, '#8e6a38');
    g.fillStyle = grad;
    const size = big.length > 4 ? 300 : 420;
    g.font = `500 ${size}px ${SERIF}`;
    g.fillText(big, W / 2, 560);
    g.fillStyle = 'rgba(196,160,104,0.8)';
    g.fillRect(W / 2 - 60, 640, 120, 3);
    g.fillStyle = '#e7dcc8';
    g.font = `500 54px ${SANS}`;
    const label = small.toUpperCase().split('').join('  ');
    g.fillText(label, W / 2, 760);
  });
}

// Small brass-plate label (dark text on brass).
export function plateText(lines, { w = 1024, h = 256, size = 70, color = '#2a1d0e', bg = null, font = SERIF } = {}) {
  return canvasTexture(w, h, (g, W, H) => {
    if (bg) { g.fillStyle = bg; g.fillRect(0, 0, W, H); } else g.clearRect(0, 0, W, H);
    g.fillStyle = color;
    g.textAlign = 'center'; g.textBaseline = 'middle';
    lines.forEach((l, i) => {
      g.font = `${i === 0 ? 600 : 400} ${i === 0 ? size : size * 0.6}px ${i === 0 ? font : SANS}`;
      g.fillText(l, W / 2, H / 2 + (i - (lines.length - 1) / 2) * size * 1.05);
    });
  });
}

// Lit window grid for architectural models.
export function windowsTexture(cols, rows, { lit = 0.75, warm = '255,214,150', frame = '#1a1714', seed = 3 } = {}) {
  return canvasTexture(512, 1024, (g, W, H) => {
    g.fillStyle = frame; g.fillRect(0, 0, W, H);
    const r = rng(seed);
    const cw = W / cols, rh = H / rows;
    for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
      const on = r() < lit;
      g.fillStyle = on ? `rgba(${warm},${0.55 + r() * 0.45})` : 'rgba(60,70,90,0.6)';
      g.fillRect(x * cw + cw * 0.12, y * rh + rh * 0.18, cw * 0.76, rh * 0.64);
    }
  });
}

// Enamel dome: Singapore night skyline, gold stars and fireworks (equirectangular for a hemisphere).
export function domeTexture() {
  return canvasTexture(2048, 1024, (g, W, H) => {
    const sky = g.createLinearGradient(0, 0, 0, H);
    sky.addColorStop(0, '#0a1450'); sky.addColorStop(0.6, '#1b2e8a'); sky.addColorStop(1, '#3b4fb0');
    g.fillStyle = sky; g.fillRect(0, 0, W, H);
    const r = rng(21);
    // gold stars
    for (let i = 0; i < 160; i++) {
      const x = r() * W, y = r() * H * 0.7, s = 6 + r() * 14;
      g.fillStyle = `rgba(242,205,120,${0.7 + r() * 0.3})`;
      g.beginPath();
      for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + (k * Math.PI) / 5, rr = k % 2 ? s * 0.42 : s; g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); }
      g.fill();
    }
    // fireworks in many enamel colours
    const colors = ['#ffd36b', '#ff7aa8', '#9be7ff', '#c7a6ff', '#ffef9e', '#ff9e5e', '#8effc1', '#ffffff'];
    for (let f = 0; f < 9; f++) {
      const cx = r() * W, cy = 80 + r() * H * 0.45, R = 70 + r() * 110;
      for (let k = 0; k < 90; k++) {
        const a = r() * Math.PI * 2, l = R * (0.4 + r() * 0.6);
        g.strokeStyle = colors[(f + k) % colors.length];
        g.globalAlpha = 0.5 + r() * 0.5;
        g.lineWidth = 2 + r() * 2;
        g.beginPath(); g.moveTo(cx + Math.cos(a) * l * 0.2, cy + Math.sin(a) * l * 0.2); g.lineTo(cx + Math.cos(a) * l, cy + Math.sin(a) * l); g.stroke();
      }
    }
    g.globalAlpha = 1;
  });
}

export function skylineBandTexture() {
  // enamel cylinder band: a stylised city at night in many colours
  return canvasTexture(2048, 512, (g, W, H) => {
    const sky = g.createLinearGradient(0, 0, 0, H);
    sky.addColorStop(0, '#1f2f8c'); sky.addColorStop(0.55, '#5b4fb4'); sky.addColorStop(0.8, '#e08aa6'); sky.addColorStop(1, '#2e7bb6');
    g.fillStyle = sky; g.fillRect(0, 0, W, H);
    const r = rng(33);
    const pal = ['#2a4cc2', '#3dd3e6', '#9a5bd6', '#f2b24a', '#e85b8c', '#42c28a', '#f0e07a', '#6fa0ff', '#d46b3a', '#ffffff'];
    for (let i = 0; i < 70; i++) {
      const w = 20 + r() * 70, h = 60 + r() * 300, x = r() * W;
      g.fillStyle = pal[i % pal.length];
      g.globalAlpha = 0.85;
      g.fillRect(x, H - 90 - h, w, h);
      g.fillStyle = 'rgba(255,240,200,0.7)';
      for (let y = H - 90 - h + 8; y < H - 100; y += 14) for (let xx = x + 4; xx < x + w - 6; xx += 10) if (r() < 0.4) g.fillRect(xx, y, 4, 6);
    }
    // supertree-like silhouettes and a bridge arc
    g.globalAlpha = 1;
    for (let i = 0; i < 6; i++) {
      const x = 200 + i * 300 + r() * 80, top = H - 300 - r() * 80;
      g.strokeStyle = pal[(i * 3) % pal.length]; g.lineWidth = 10;
      g.beginPath(); g.moveTo(x, H - 90); g.lineTo(x, top); g.stroke();
      g.beginPath(); g.arc(x, top, 46, Math.PI, 0); g.stroke();
    }
    g.strokeStyle = '#f2c46a'; g.lineWidth = 6;
    g.beginPath(); g.arc(W * 0.7, H + 260, 420, Math.PI * 1.15, Math.PI * 1.85); g.stroke();
    const water = g.createLinearGradient(0, H - 90, 0, H);
    water.addColorStop(0, '#1b5aa8'); water.addColorStop(1, '#0d2a66');
    g.fillStyle = water; g.fillRect(0, H - 90, W, 90);
  });
}

// Map of Southeast Asia boutique cities (dot grid, not a coastline).
export function mapTexture(pins) {
  return canvasTexture(1600, 1000, (g, W, H) => {
    g.fillStyle = '#16120e'; g.fillRect(0, 0, W, H);
    for (let x = 30; x < W; x += 26) for (let y = 30; y < H; y += 26) {
      g.fillStyle = 'rgba(200,170,120,0.12)';
      g.beginPath(); g.arc(x, y, 2, 0, Math.PI * 2); g.fill();
    }
    g.strokeStyle = 'rgba(200,170,120,0.25)'; g.lineWidth = 2; g.setLineDash([6, 10]);
    g.beginPath();
    pins.forEach(([, u, v], i) => (i ? g.lineTo(u * W, v * H) : g.moveTo(u * W, v * H)));
    g.stroke();
    g.setLineDash([]);
    pins.forEach(([name, u, v, sub]) => {
      g.fillStyle = '#e8cf9b';
      g.font = `600 44px ${SERIF}`;
      g.textAlign = 'left'; g.textBaseline = 'middle';
      g.fillText(name, u * W + 40, v * H - 6);
      g.fillStyle = 'rgba(232,220,200,0.75)';
      g.font = `400 26px ${SANS}`;
      g.fillText(sub.toUpperCase(), u * W + 42, v * H + 32);
    });
  });
}
