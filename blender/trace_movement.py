# Traces the parts of the 5057G's calibre 240 from the caseback photograph by seeded watershed:
# a few seed points per part (photo-view mm, read on 1 mm grids of the crop), flooded over the
# photo's edge strength so each boundary settles on the real bevel line between parts.
# Writes blender/movement_parts.json (outline polygons per part, photo-view mm) and, with SCRATCH
# set, an overlay of the traced outlines on the photo for review.
#   python3 blender/trace_movement.py
import json, math, os, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage import measure, segmentation
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.environ.get("SCRATCH")
spec = importlib.util.spec_from_file_location("mfp", os.path.join(HERE, "movement_from_photo.py"))
mfp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mfp)

# part -> (class, seed points). Classes: bridge (rhodium, Côtes), plate, gold (wheels, balance),
# steel (wheels, small parts), rotor, outside.
SEEDS = {
    "bridge_train":   ("bridge", [(-7, 8), (-9, 3.5), (-5.5, 1.5), (-3.2, 11), (-11.5, 6), (-7.5, -1.2), (-9.6, -1.6), (-1.3, 10.5)]),
    "bridge_centre":  ("bridge", [(4, 10.5), (8, 10), (2, 12), (6, 8.6), (10, 8.4)]),
    "bridge_wheels":  ("bridge", [(-9, -7), (-6.5, -5.5), (-11, -6), (-6, -9.5), (-4.5, -6.5)]),
    # the cock runs on under the rotor's rest position to the window's edge (screwed down at 6.95, -9.54)
    "balance_cock":   ("bridge", [(3, -9), (6, -10), (8.5, -8), (1.6, -8.3), (8.0, -8.6), (9.2, -8.3),
                                  (10.2, -7.4), (7.6, -10.2), (8.6, -9.6), (7.6, -7.4), (6.3, -11.4)]),
    "pallet_bridge":  ("bridge", [(-1.8, -11.4)]),
    "plate":          ("plate",  [(9.5, 2.5), (11, 5), (3.5, 3.2), (11.8, 6.2), (0.8, 2.6)]),
    "gold_wheels":    ("gold",   [(2.2, 5.6), (-0.5, 5.5), (-2.0, 3.0), (-4, -3.2), (-2.8, -2.0), (1.0, 4.6)]),
    "steel_wheels":   ("steel",  [(7.3, 6.6), (4.5, 1.8), (7.8, 1.6), (5.5, 4.0)]),
    "rotor":          ("rotor",  [(6, -3), (2, -2), (10, -2), (6, -5.5)]),
    "balance":        ("gold",   [(2.5, -6.6), (-2.2, -8.2), (1.0, -7.3)]),
    "escapement":     ("steel",  [(-2.5, -9.6), (-3.2, -10.6)]),
}
R_OUT = 13.25   # beyond this is the caseback window rim


def main():
    img = mfp.crop()                      # the raw photograph (rotor included), photo-view mm
    N, R = img.shape[0], mfp.R
    K = N / (2 * R)
    mm = (np.arange(N) + 0.5) / K - R
    X, Y = np.meshgrid(mm, -mm)
    sm = ndimage.gaussian_filter(img, (1.6, 1.6, 0))
    grad = sum(np.hypot(ndimage.sobel(sm[..., c], 0), ndimage.sobel(sm[..., c], 1)) for c in range(3))
    L = sm.mean(2)
    grad = grad + 0.6 * np.hypot(ndimage.sobel(L, 0), ndimage.sobel(L, 1))
    markers = np.zeros(X.shape, np.int32)
    names = list(SEEDS) + ["outside"]
    for i, name in enumerate(SEEDS, start=1):
        for x, y in SEEDS[name][1]:
            markers[np.hypot(X - x, Y - y) < 0.22] = i
    markers[np.hypot(X, Y) > R_OUT] = len(names)
    lab = segmentation.watershed(grad, markers)
    parts = {}
    for i, name in enumerate(SEEDS, start=1):
        m = ndimage.binary_fill_holes(ndimage.binary_opening(lab == i, iterations=2))
        comps, n = ndimage.label(m)
        if n == 0:
            continue
        polys = []
        for j in range(1, n + 1):
            c = comps == j
            if c.sum() / K ** 2 < 0.3:
                continue
            cs = measure.find_contours(np.pad(c, 1).astype(float), 0.5)
            cs.sort(key=len, reverse=True)
            c0 = cs[0] - 1
            c0 = np.c_[ndimage.uniform_filter1d(c0[:, 0], 9, mode="wrap"), ndimage.uniform_filter1d(c0[:, 1], 9, mode="wrap")]
            poly = measure.approximate_polygon(c0, tolerance=0.7)   # smoothed: no watershed jaggies
            polys.append([[round(float((p[1] + 0.5) / K - R), 4), round(float(R - (p[0] + 0.5) / K), 4)] for p in poly])
        parts[name] = {"class": SEEDS[name][0], "polys": polys}
        print(f"{name:14s} {len(polys)} piece(s), {sum(1 for _ in polys)}")
    json.dump({"frame": "photo view from the back, mm (mirror x for the watch frame)", "parts": parts},
              open(os.path.join(HERE, "movement_parts.json"), "w"))
    if SCR:
        cols = {"bridge": (255, 40, 40), "plate": (60, 200, 60), "gold": (255, 200, 0), "steel": (0, 160, 255),
                "rotor": (255, 120, 0), "outside": (120, 120, 120)}
        im = Image.fromarray(img.astype(np.uint8)).resize((1400, 1400), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        k = 1400 / (2 * R)
        P = lambda x, y: ((x + R) * k, (R - y) * k)
        for name, p in parts.items():
            for poly in p["polys"]:
                d.line([P(*q) for q in poly] + [P(*poly[0])], fill=cols[p["class"]], width=3)
            x0, y0 = SEEDS[name][1][0]
            d.text(P(x0, y0), name, fill=cols[p["class"]])
        for name, (cl, pts) in SEEDS.items():
            for x, y in pts:
                cx, cy = P(x, y)
                d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=cols[cl])
        im.save(os.path.join(SCR, "trace_overlay.png"))


if __name__ == "__main__":
    main()
