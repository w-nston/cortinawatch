// The automatic's mini-rotor, moved by the watch as it would be on the wrist: a half-disc on a ball
// bearing, its centre of mass 4R/3π off the pivot, so it is a damped pendulum about its axle. Three
// things move it, all read from the rotor's parent each frame (so any motion of the watch works: a
// drag in the viewer, the gallery's scroll-driven moves):
//   gravity, in the watch's own frame (tilt the watch and the heavy side swings down),
//   the watch turning about its own axis (the rotor's inertia leaves it behind),
//   the watch being moved (its acceleration adds to gravity, as a jolt does on the wrist).
// The swing is slowed from a real rotor's (~35 rad/s) so it reads, and lightly damped by the bearing.
import * as THREE from 'three';

const _q = new THREE.Quaternion(), _qi = new THREE.Quaternion(), _dq = new THREE.Quaternion();
const _p = new THREE.Vector3(), _s = new THREE.Vector3(), _g = new THREE.Vector3(), _a = new THREE.Vector3();

export class RotorPhysics {
  /**
   * @param {THREE.Object3D} rotor  turns about its local Z (the watch's axis)
   * @param {object} o
   *   cmAngle   direction of its centre of mass in its own frame at rotation 0 (rad; -π/2: toward -Y)
   *   omega0    small-swing angular frequency under 1 g (rad/s)
   *   zeta      damping ratio of the bearing
   *   mmPerUnit millimetres per world unit; by default read from the parent's world scale (the
   *             rotor's own units are millimetres, in the GLB and in cal240.js)
   */
  constructor(rotor, { cmAngle = -Math.PI / 2, omega0 = 9, zeta = 0.07, mmPerUnit = null } = {}) {
    Object.assign(this, { rotor, cmAngle, omega0, zeta, mmPerUnit });
    this.theta = rotor.rotation.z;   // relative to the watch
    this.omega = 0;                  // absolute angular velocity about the watch's axis
    this.prevQ = null; this.prevPos = null; this.prevVel = null;
  }

  /** Advance by dt seconds (call once per frame). */
  update(dt) {
    if (!(dt > 0)) return;
    dt = Math.min(dt, 1 / 30);
    const parent = this.rotor.parent;
    parent.updateWorldMatrix(true, false);
    parent.matrixWorld.decompose(_p, _q, _s);
    // the watch's turn about its own axis since the last frame (twist part of the rotation)
    let dpsi = 0;
    if (this.prevQ) {
      _dq.copy(this.prevQ).invert().multiply(_q);
      dpsi = 2 * Math.atan2(_dq.z, _dq.w);
      if (dpsi > Math.PI) dpsi -= 2 * Math.PI;
      if (dpsi < -Math.PI) dpsi += 2 * Math.PI;
    }
    this.prevQ = (this.prevQ || new THREE.Quaternion()).copy(_q);
    // the watch's acceleration (m/s²), from its pivot's track
    this.rotor.getWorldPosition(_p);
    _a.set(0, 0, 0);
    if (this.prevPos) {
      const mm = this.mmPerUnit ?? 1 / (_s.x || 1);
      const vel = _p.clone().sub(this.prevPos).multiplyScalar(mm / 1000 / dt);
      if (this.prevVel) _a.copy(vel).sub(this.prevVel).divideScalar(dt).clampLength(0, 40);
      this.prevVel = vel;
    }
    this.prevPos = (this.prevPos || new THREE.Vector3()).copy(_p);
    // effective gravity (in g) in the watch's frame
    _g.set(0, -1, 0).addScaledVector(_a, -1 / 9.81).applyQuaternion(_qi.copy(_q).invert());
    // torque about the axle from the in-plane pull on the centre of mass
    const c = this.theta + this.cmAngle;
    const tau = Math.cos(c) * _g.y - Math.sin(c) * _g.x;
    const rel = this.omega - dpsi / dt;            // the bearing drags on motion relative to the watch
    this.omega += (this.omega0 ** 2 * tau - 2 * this.zeta * this.omega0 * rel) * dt;
    this.theta += this.omega * dt - dpsi;
    this.rotor.rotation.z = this.theta;
  }

  /** Let it hang at rest where gravity puts it (no swing), e.g. after a jump cut. */
  settle() {
    this.omega = 0;
    for (let i = 0; i < 600; i++) {
      this.prevQ = null; this.prevPos = null; this.prevVel = null;
      const w = this.omega0; const z = this.zeta;
      this.omega0 = 30; this.zeta = 1.0;
      this.update(1 / 120);
      this.omega0 = w; this.zeta = z;
    }
    this.omega = 0;
  }
}
