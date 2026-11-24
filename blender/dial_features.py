# Extracts the dial's metal parts from the cleaned dial photo (blender/textures/dial_5057G_photo_color.jpg)
# so they can be built in 3D: the Roman numerals (outlines with their counters) and the moon-phase
# layout (window, moon and stars as photographed). Writes blender/dial_features.json (mm, front view).
# Run with system python (numpy, scipy, scikit-image, Pillow):  python3 blender/dial_features.py
import json, math, os, numpy as np
from PIL import Image
from scipy import ndimage
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "textures", "dial_5057G_photo_color.jpg")
N, R = 4096, 15.4
K = N / (2 * R)
# moon window, fitted on the rectified photo (dial_from_photo.py MOON)
MOON = dict(cx=-3.465, cy=-6.215, R=3.906, d=2.15, r=1.57)

im = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
L = im.mean(2)
mm = (np.arange(N) + 0.5) / K - R
X, Y = np.meshgrid(mm, -mm)
rr = np.hypot(X, Y)
th = np.degrees(np.arctan2(Y, X))
to_mm = lambda c: [[round(float((p[1] + 0.5) / K - R), 4), round(float(R - (p[0] + 0.5) / K), 4)] for p in c]

# ---- Roman numerals: bright print in the numeral ring, one sector per hour present on the dial
ink = ndimage.binary_opening(L > 195, iterations=1)   # the numerals are the brightest print on the dial
numerals = {}
for hour in (12, 1, 2, 3, 9, 10, 11):
    a = 90 - 30 * (hour % 12)
    d = (th - a + 180) % 360 - 180
    sect = (np.abs(d) < 13) & (rr > 9.2) & (rr < 12.5) & ink
    lab, n = ndimage.label(sect)
    parts = []
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() / K ** 2 < 0.2:           # specks (numeral strokes are ≥ 0.4 mm²)
            continue
        m = ndimage.binary_closing(m, iterations=2)
        cs = sorted(measure.find_contours(np.pad(m, 1).astype(float), 0.5), key=len, reverse=True)
        outer = measure.approximate_polygon(cs[0] - 1, tolerance=0.7)
        holes = [measure.approximate_polygon(c - 1, tolerance=0.7) for c in cs[1:] if len(c) > 30]
        parts.append({"outer": to_mm(outer), "holes": [to_mm(h) for h in holes]})
    numerals[str(hour)] = parts
    print(hour, len(parts), "strokes")

# ---- moon phase as photographed: the moon and the stars inside the window
cx, cy, Rw = MOON["cx"], MOON["cy"], MOON["R"]
win = (np.hypot(X - cx, Y - cy) < Rw - 0.05) & (Y > cy + 0.05)
for s in (-1, 1):
    win &= np.hypot(X - (cx + s * MOON["d"]), Y - cy) > MOON["r"] + 0.05
bright = win & (L > 150)
lab, n = ndimage.label(bright)
blobs = []
for i in range(1, n + 1):
    m = lab == i
    a = m.sum() / K ** 2
    if a < 0.04:
        continue
    blobs.append((a, float(X[m].mean()), float(Y[m].mean())))
blobs.sort(reverse=True)
moon = blobs[0]
mx, my = moon[1], moon[2]
# the moon is cut by the window edge, so fit its circle on its outline
m = lab == [i for i in range(1, n + 1) if abs(float(X[lab == i].mean()) - mx) < 1e-6][0]
edge = m & ~ndimage.binary_erosion(m)
E = np.c_[X[edge], Y[edge]]
E = E[np.hypot(E[:, 0] - cx, E[:, 1] - cy) < Rw - 0.15]   # not the part clipped by the window
for s_ in (-1, 1):                                        # nor by the scallops
    E = E[np.hypot(E[:, 0] - (cx + s_ * MOON["d"]), E[:, 1] - cy) > MOON["r"] + 0.15]
E = E[E[:, 1] > cy + 0.15]
A = np.c_[E[:, 0], E[:, 1], np.ones(len(E))]
D, Ee, F = np.linalg.lstsq(A, -(E ** 2).sum(1), rcond=None)[0]
mcx, mcy = -D / 2, -Ee / 2
mr = math.sqrt(mcx ** 2 + mcy ** 2 - F)
stars = [[round(b[1], 4), round(b[2], 4), round(math.sqrt(b[0] / math.pi) * 1.45, 4)] for b in blobs[1:4]]
print(f"moon at ({mcx:.2f},{mcy:.2f}) r {mr:.2f}; {len(stars)} stars")

json.dump({"frame": "front view, mm, +X to 3 o'clock, +Y to 12",
           "numerals": numerals,
           "moon_window": MOON,
           "moon": {"centre": [round(mcx, 4), round(mcy, 4)], "r": round(mr, 4)},
           "stars": stars}, open(os.path.join(HERE, "dial_features.json"), "w"))
