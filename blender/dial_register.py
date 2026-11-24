# Registers the straight-on 5057G front photo to dial millimetres.
# Fits ellipses to three edges (railway inner white line, railway outer edge, bezel outer
# edge against the white background) and prints centre and px/mm along X and Y.
import glob, os, sys, numpy as np
from PIL import Image
from scipy import ndimage

PHOTOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "watch photos", "5057G")
src = glob.glob(os.path.join(PHOTOS, "AS*--1_*"))[0]
im = np.asarray(Image.open(src).convert("L")).astype(np.float32)
cx, cy = 1258.3, 1244.6


def prof(deg, r0, r1, step=0.5, win=1.2):
    a = np.radians(deg)
    r = np.arange(r0, r1, step)
    vs = [ndimage.map_coordinates(im, [cy - r * np.sin(a + da), cx + r * np.cos(a + da)], order=1)
          for da in np.radians(np.linspace(-win, win, 7))]
    return r, ndimage.gaussian_filter1d(np.mean(vs, 0), 1.5)


def fit_ellipse(pts):
    # axis-aligned ellipse: A x^2 + B y^2 + C x + D y = 1
    P = np.array(pts)
    x, y = P[:, 0], P[:, 1]
    M = np.c_[x * x, y * y, x, y]
    A, B, C, D = np.linalg.lstsq(M, np.ones(len(x)), rcond=None)[0]
    x0, y0 = -C / (2 * A), -D / (2 * B)
    k = 1 + A * x0 * x0 + B * y0 * y0
    rx, ry = np.sqrt(k / A), np.sqrt(k / B)
    res = np.hypot((x - x0) / rx, (y - y0) / ry) - 1
    return x0, y0, rx, ry, res


def robust(pts):
    for _ in range(3):
        x0, y0, rx, ry, res = fit_ellipse(pts)
        keep = np.abs(res) < 2.5 * np.std(res) + 1e-4
        pts = [p for p, k in zip(pts, keep) if k]
    return fit_ellipse(pts) + (len(pts),)


line, band, outer = [], [], []
for d in np.arange(0, 360, 1.0):
    a = np.radians(d)
    hand = 20 <= d <= 38  # minute hand crosses the railway here
    r, v = prof(d, 420, 520)
    if not hand:
        # white inner line: brightest peak between 425 and 470 px
        m = (r > 425) & (r < 470)
        k = np.argmax(v[m])
        if v[m][k] > 90:
            rr = r[m][k]; line.append((cx + rr * np.cos(a), cy - rr * np.sin(a)))
        # band outer edge: strongest rise between 465 and 505 px
        m = (r > 465) & (r < 505)
        g = np.gradient(v)[m]
        k = np.argmax(g)
        if g[k] > 3:
            rr = r[m][k]; band.append((cx + rr * np.cos(a), cy - rr * np.sin(a)))
    clean = any(lo <= d <= hi for lo, hi in ((8, 42), (138, 172), (188, 222), (318, 352)))
    if clean:
        r, v = prof(d, 560, 700, win=0.5)
        nb = np.where(v < 238)[0]
        if len(nb):
            rr = r[nb[-1]]; outer.append((cx + rr * np.cos(a), cy - rr * np.sin(a)))

out = {}
for name, pts in (("line", line), ("band", band), ("outer", outer)):
    x0, y0, rx, ry, res, n = robust(pts)
    out[name] = (x0, y0, rx, ry)
    print(f"{name:5s} n={n:3d} centre=({x0:7.1f},{y0:7.1f}) rx={rx:6.1f} ry={ry:6.1f} rms={np.std(res) * rx:4.2f}px")
