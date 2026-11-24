// A dark photo studio with softboxes, used as the reflection environment.
// Polished metal looks real when it reflects strong contrast: bright strip
// lights against black, as in watch product photography.
import * as THREE from 'three';

export function studioEnvironment(renderer, { warm = false } = {}) {
  const scene = new THREE.Scene();
  const room = new THREE.Mesh(new THREE.SphereGeometry(50, 32, 16), new THREE.MeshBasicMaterial({ color: warm ? 0x0d0a08 : 0x080809, side: THREE.BackSide }));
  scene.add(room);
  const box = (w, h, pos, intensity, color = 0xffffff) => {
    const m = new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(intensity), side: THREE.DoubleSide });
    const p = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
    p.position.set(...pos);
    p.lookAt(0, 0, 0);
    scene.add(p);
  };
  box(30, 14, [0, 30, 6], 5.5); // overhead softbox
  box(5, 34, [-28, 4, 10], 7); // left strip
  box(5, 34, [28, 6, -6], 6); // right strip
  box(22, 6, [0, -8, 30], 1.6, warm ? 0xffe2c0 : 0xffffff); // low front fill
  box(14, 14, [-14, 10, -30], 3.2, warm ? 0xffd9a8 : 0xf2f4ff); // back kicker
  box(40, 2, [0, -26, -10], 0.6); // floor bounce line
  const pmrem = new THREE.PMREMGenerator(renderer);
  const env = pmrem.fromScene(scene, 0.02).texture;
  pmrem.dispose();
  return env;
}
