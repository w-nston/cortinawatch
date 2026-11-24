// A photo studio for watches, used as the reflection and lighting environment.
// Polished metal looks real when it reflects strong contrast: bright softboxes and strip
// lights against a dark room. The studio is lit on both sides, the dial side (+Z) and the
// caseback side (-Z), so the movement under the sapphire back reads as well as the dial.
// The room is dark grey rather than black, with a soft ceiling-to-floor gradient, so that
// photo-textured, partly metallic surfaces (the dial, the movement) keep their tone.
import * as THREE from 'three';

export function studioEnvironment(renderer, { warm = false } = {}) {
  const scene = new THREE.Scene();

  // room: vertical gradient, ceiling lighter than floor
  const room = new THREE.SphereGeometry(50, 48, 24);
  const top = new THREE.Color(warm ? 0x35302b : 0x313236);
  const mid = new THREE.Color(warm ? 0x1b1714 : 0x18191c);
  const low = new THREE.Color(warm ? 0x0a0807 : 0x09090a);
  const cols = [];
  const p = room.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const t = p.getY(i) / 50; // -1 floor .. 1 ceiling
    const c = t > 0 ? mid.clone().lerp(top, t) : mid.clone().lerp(low, -t);
    cols.push(c.r, c.g, c.b);
  }
  room.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
  scene.add(new THREE.Mesh(room, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide })));

  const box = (w, h, pos, intensity, color = 0xffffff) => {
    const m = new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(intensity), side: THREE.DoubleSide });
    const b = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
    b.position.set(...pos);
    b.lookAt(0, 0, 0);
    scene.add(b);
  };
  const fill = warm ? 0xffe2c0 : 0xffffff;
  const cool = warm ? 0xffd9a8 : 0xf2f4ff;
  // dial side
  box(30, 14, [0, 28, 16], 4.5);            // overhead softbox, tilted toward the dial
  box(5, 32, [-27, 6, 18], 5.5);            // left strip
  box(5, 32, [27, 4, 14], 4.5);             // right strip
  box(22, 6, [0, -10, 30], 1.3, fill);      // low front fill
  // caseback side (the movement)
  box(26, 12, [0, 26, -18], 3.8, cool);     // overhead softbox behind
  box(5, 30, [-25, 4, -22], 4.5, cool);     // left strip behind
  box(5, 30, [25, 8, -18], 3.5);            // right strip behind
  box(22, 6, [0, -10, -30], 1.1, fill);     // low back fill
  // light tent behind the viewer of the caseback: face-on metal (plates, rotor, balance) reflects a soft
  // white, as in the retail photographs; small enough that the Côtes de Genève still cross its edges
  box(26, 22, [0, 2, -46], 0.85, cool);
  // broad low softboxes either side, front and back: polished case, bezel and lugs pick these up
  box(34, 16, [-30, -12, 26], 1.5, fill);
  box(34, 16, [30, -14, 22], 1.1);
  box(34, 16, [-30, -12, -26], 1.3, cool);
  box(34, 16, [30, -14, -22], 1.0);
  // horizon bounce, all round (keeps case flanks and lugs from going black)
  box(60, 3, [0, -2, 40], 0.5);
  box(60, 3, [0, -2, -40], 0.5);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const env = pmrem.fromScene(scene, 0.02).texture;
  pmrem.dispose();
  return env;
}
