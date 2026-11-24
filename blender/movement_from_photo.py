# Prepares the 5057G's calibre 240 for a layered 3D build, from the straight-on caseback photo
# ("watch photos/5057G/AS…--4_….webp").
#
#   texture  the movement is cropped centred on the caseback window (fitted by hand on pixel grids:
#            x 788–1703, y 840–1690 px), at 34.0 px/mm across and 33.05 px/mm vertically (the photo
#            is foreshortened like the front one); the sliver the window wall hides at top and
#            bottom is stretched out to the rim.
#   rotor    the 22K gold mini-rotor is found by colour, its arc fitted for the pivot and radius,
#            and removed: the area it covered is filled with the mechanism on the opposite side of
#            the pivot (turned 180°), so a separate 3D rotor can turn over it.
#   layers   bridges are hand-traced polygons (mm, measured on gridded crops); gold wheels are the
#            gold pixels outside the bridges (gilt engravings on the bridges stay flat print);
#            jewels by colour; screws listed by hand.
#   maps     roughness/metal (ORM) and a fine relief normal map from the photo's luminance, so the
#            Côtes de Genève, perlage, bevels and screw slots answer the light.
#
# Writes blender/textures/movement_5057G_{color.jpg,orm.png,normal.png} and blender/movement.json.
# Run with system python (numpy, scipy, scikit-image, Pillow):  python3 blender/movement_from_photo.py
import glob, json, math, os, numpy as np
from PIL import Image
from scipy import ndimage
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = glob.glob(os.path.join(HERE, "..", "watch photos", "5057G", "AS*--4_*"))[0]
OUT = os.path.join(HERE, "textures")
SCR = os.environ.get("SCRATCH")

N = 2048
R = 14.06                      # texture spans [-R, R] mm (matches build_5057.py)
K = N / (2 * R)
CX, CY = 1245.5, 1265.0        # window centre in the photo (px)
SX, SY = 34.0, 33.05           # px/mm across / vertically
A_VIS, B_VIS = 13.45, 12.86    # visible movement half-axes in the photo (mm)
R_WIN = 13.4                   # caseback window radius used by the model (measured: 457 px / 34 px/mm)

# Everything below is in photo-view millimetres: as seen from the back, x to the right
# (toward 9 o'clock on the watch), y up (12 o'clock). build_5057.py mirrors x into the
# watch's front frame.
# Hand-traced on 1 mm-gridded crops of the first crop (centre 1256, 1296 px, 33.43 px/mm);
# OLD() converts those readings into this frame.
def OLD(pts):
    out = []
    for xo, yo in pts:
        px, py = 1256 + xo * 33.43, 1296 - yo * 33.43
        out.append(((px - CX) / SX, (CY - py) / SY))
    return out


BRIDGES = {   # points beyond the window are clamped onto it
    "bridge_train": OLD([(-0.6, 14.5), (-0.7, 12.5), (-0.8, 11.3), (-1.0, 10.1), (-1.3, 9.2), (-1.9, 8.3), (-2.6, 7.3),
                         (-3.3, 6.2), (-3.8, 5.0), (-4.1, 3.9), (-4.3, 2.8), (-4.2, 1.8), (-4.0, 0.6), (-4.5, -0.4),
                         (-5.4, -1.1), (-6.6, -1.4), (-7.6, -1.8), (-8.4, -2.4), (-9.4, -3.0), (-10.6, -3.3),
                         (-12.0, -3.3), (-14.5, -3.6), (-15.5, 0), (-15.5, 8), (-11, 15.5), (-4, 16)]),
    "bridge_wheels": OLD([(-14.5, -3.75), (-12.0, -3.5), (-10.6, -3.5), (-9.4, -3.2), (-8.4, -2.6), (-7.6, -2.0),
                          (-6.4, -1.65), (-6.0, -2.6), (-5.6, -3.6), (-5.0, -4.4), (-4.2, -5.0), (-3.9, -5.9),
                          (-4.0, -6.8), (-3.8, -7.8), (-3.9, -9.0), (-4.3, -10.0), (-4.8, -13), (-9.5, -12.5),
                          (-13.5, -8)]),
    "bridge_centre": OLD([(0.45, 14.5), (0.45, 12.5), (0.45, 11.0), (0.5, 9.2), (0.7, 8.3), (1.3, 7.7), (2.0, 7.8),
                          (3.0, 8.2), (4.0, 8.5), (5.0, 8.7), (6.0, 8.75), (7.0, 8.6), (8.0, 8.35), (9.0, 8.15),
                          (10.0, 8.05), (10.8, 8.0), (11.6, 7.5), (14.5, 9), (11, 15), (4, 16)]),
    "balance_cock": OLD([(-1.3, -7.6), (-0.8, -6.7), (0.5, -6.3), (2.5, -6.15), (5.0, -6.0), (7.5, -5.75),
                         (9.8, -5.45), (10.6, -5.6), (13.5, -6.5), (12.5, -10.5), (8.5, -13.5), (5.0, -12.0),
                         (4.8, -10.6), (2.8, -10.1), (0.6, -9.8), (-0.6, -9.3)]),
}
SCREWS = OLD([(-5.0, 12.4), (-12.8, 3.0), (-10.15, -1.95), (-11.55, -4.6), (-5.25, -10.2), (6.2, -8.3),
              (1.0, 13.2), (9.0, 9.2)])
SCREW_R = 0.62
# The visible train, photo-view mm, read on 1 mm grids of the recentred texture (centre x, y,
# tip radius, teeth, spokes). The third wheel is centred on its pivot jewel; the large wheel's
# centre is fitted to its rim (most of it runs under the rotor).
GOLD_GEARS = {"centre_wheel": (3.2, 1.19, 5.86, 96, 4), "third_wheel": (2.08, 7.58, 3.4, 75, 5),
              "fourth_wheel": (-3.6, -2.9, 2.6, 70, 5)}
# steel: crown wheel, the large ratchet/reduction wheel of the automatic winding, its partner
STEEL_WHEELS = [(7.53, 5.22, 1.86), (6.22, 0.0, 3.8), (4.85, -4.95, 1.86)]
BALANCE = (0.5, -9.25, 3.4)   # centre on the balance-staff jewel, rim outer radius
POCKET_MARGIN = 0.25   # sinkings in the baseplate round every wheel


def mm_grid():
    mm = (np.arange(N) + 0.5) / K - R
    return np.meshgrid(mm, -mm)


def crop():
    photo = np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float32)
    X, Y = mm_grid()
    e = np.hypot(X / A_VIS, Y / B_VIS)
    f = np.where(e > 0.985, 0.985 / np.maximum(e, 1e-6), 1.0)   # stretch the hidden sliver to the rim
    px, py = CX + X * f * SX, CY - Y * f * SY
    return np.clip(np.stack([ndimage.map_coordinates(photo[..., c], [py, px], order=3, mode="nearest")
                             for c in range(3)], -1), 0, 255)


def poly_mask(pts, X, Y):
    from matplotlib.path import Path
    # densify, then clamp onto the window
    dense = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 0.08))
        dense += [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n)]
    out = []
    for x, y in dense:
        r = math.hypot(x, y)
        out.append((x * R_WIN / r, y * R_WIN / r) if r > R_WIN else (x, y))
    m = Path(out).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)
    return m, out


def main():
    img = crop()
    X, Y = mm_grid()
    rr = np.hypot(X, Y)
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    mx, mn = img.max(2), img.min(2)
    sat = (mx - mn) / (mx + 1)
    gold = (r > g + 12) & (g > b + 12) & (sat > 0.16) & (rr < R_WIN)
    ruby = (r > g + 20) & (b > g + 10) & (rr < R_WIN)

    # ---- the rotor: the gold half-disc under the straight edge. Centre and radius by grid search
    # for the best overlap with the gold pixels (the balance wheel touches it, so a free fit drifts)
    top = 0.06                                       # straight edge, read off the photo grid
    lower = (Y <= top) & (Y > top - 8.5) & (X > -2)
    gl = gold & lower
    best = None
    for cx in np.arange(5.6, 7.8, 0.05):
        for r0 in np.arange(5.8, 8.2, 0.05):
            hd = lower & (np.hypot(X - cx, Y - top) <= r0)
            inter = (hd & gl).sum()
            iou = inter / (hd.sum() + gl.sum() - inter)
            if best is None or iou > best[0]:
                best = (iou, cx, r0)
    _, px0, rr0 = best
    py0 = top
    pivot = (float(px0), top)
    rot = (np.hypot(X - px0, Y - top) <= rr0 + 0.06) & (Y <= top + 0.05)
    print(f"rotor: pivot ({px0:.2f},{top:.2f}) r {rr0:.2f} (IoU {best[0]:.3f})")

    # ---- fill under the rotor with the mechanism opposite the pivot (turned 180°)
    under = ndimage.binary_dilation(rot, iterations=6)
    sx, sy = 2 * pivot[0] - X[under], 2 * pivot[1] - Y[under]
    rows, cols = (R - sy) * K - 0.5, (sx + R) * K - 0.5
    fill = np.stack([ndimage.map_coordinates(img[..., c], [rows, cols], order=1, mode="nearest") for c in range(3)], -1)
    srcbad = ndimage.map_coordinates(under.astype(np.float32), [rows, cols], order=0) > 0.5
    img2 = img.copy()
    img2[under] = fill
    # anything the turned copy could not supply: smooth from the surroundings
    left = np.zeros_like(under)
    left[under] = srcbad
    if left.any():
        img2 = laplace(img2, left)
    # soften the seam
    seam = under & ~ndimage.binary_erosion(under, iterations=4)
    blur = ndimage.gaussian_filter(img2, (2, 2, 0))
    img2[seam] = blur[seam]

    # ---- bridges, wheels, jewels
    bridges = {}
    bmask = np.zeros_like(rot)
    for name, pts in BRIDGES.items():
        m, outline = poly_mask(pts, X, Y)
        bmask |= m
        bridges[name] = [[round(x, 4), round(y, 4)] for x, y in outline]
    gold2 = gold & ~under
    lab, n = ndimage.label(gold2)
    wheels = []
    for i in range(1, n + 1):
        m = lab == i
        area = m.sum() / K ** 2
        if area < 0.25:
            continue
        inside = (m & bmask).sum() / m.sum()
        if inside > 0.6:          # gilt engraving on a bridge: stays flat print
            continue
        mm_ = ndimage.binary_closing(m, iterations=2)
        cs = [c for c in measure.find_contours(np.pad(mm_, 1).astype(float), 0.5) if len(c) >= 20]
        if not cs:
            continue
        to_mm = lambda c: [[round(float((cc[1] + 0.5) / K - R), 4), round(float(R - (cc[0] + 0.5) / K), 4)]
                           for cc in measure.approximate_polygon(c - 1, tolerance=0.8)]
        cs.sort(key=len, reverse=True)
        outer, holes = cs[0], cs[1:]  # the longest contour is the rim; the rest are windows between spokes
        wheels.append({"outer": to_mm(outer), "holes": [to_mm(h) for h in holes if len(h) > 24]})
    lab, n = ndimage.label(ndimage.binary_opening(ruby, iterations=1))
    jewels = []
    for i in range(1, n + 1):
        m = lab == i
        a = m.sum() / K ** 2
        if a < 0.05:
            continue
        jewels.append([round(float(X[m].mean()), 4), round(float(Y[m].mean()), 4), round(math.sqrt(a / math.pi), 4)])
    print(f"{len(wheels)} wheel outlines, {len(jewels)} jewels, {len(bridges)} bridges")

    # ---- sinkings: the union of a circle round every wheel (gold: fitted to its outline)
    circles = [list(w) for w in STEEL_WHEELS] + [list(g_[:3]) for g_ in GOLD_GEARS.values()] + [list(BALANCE)]
    pk = np.zeros_like(rot)
    for cx_, cy_, r_ in circles:
        pk |= np.hypot(X - cx_, Y - cy_) < r_ + POCKET_MARGIN
    pk &= rr < R_WIN - 0.25
    pk = ndimage.binary_opening(pk, iterations=3)
    pockets = []
    lab, n = ndimage.label(pk)
    for i in range(1, n + 1):
        cs = sorted(measure.find_contours(np.pad(lab == i, 1).astype(float), 0.5), key=len, reverse=True)
        tm = lambda c: [[round(float((p_[1] - 1 + 0.5) / K - R), 4), round(float(R - (p_[0] - 1 + 0.5) / K), 4)]
                        for p_ in measure.approximate_polygon(c, tolerance=0.9)]
        pockets.append({"outer": tm(cs[0]), "islands": [tm(c) for c in cs[1:] if len(c) > 30]})
    print(f"{len(circles)} wheel circles -> {len(pockets)} sinkings")

    # ---- maps
    L = img2.mean(2)
    hp = L - ndimage.gaussian_filter(L, 3)
    h = np.clip(hp / 40, -1, 1)
    gx, gy = ndimage.sobel(h, 1), ndimage.sobel(h, 0)
    nrm = np.stack([-gx * 0.6, gy * 0.6, np.ones_like(h)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    rough = np.clip(0.44 - (L - L.mean()) / 255 * 0.4, 0.22, 0.6)   # bright stripes/bevels: more polished
    # half-metal: the photograph already carries the light the photographer gave the movement, so
    # its colour stays visible; the geometry adds reflections and shading on top
    metal = np.where(ruby, 0.0, 0.3)
    orm = np.zeros(L.shape + (3,), np.uint8)
    orm[..., 0] = 255
    orm[..., 1] = (rough * 255).astype(np.uint8)
    orm[..., 2] = (metal * 255).astype(np.uint8)

    Image.fromarray(img2.astype(np.uint8)).save(os.path.join(OUT, "movement_5057G_color.jpg"), quality=92)
    Image.fromarray(orm).save(os.path.join(OUT, "movement_5057G_orm.png"))
    Image.fromarray(((nrm * 0.5 + 0.5) * 255).astype(np.uint8)).save(os.path.join(OUT, "movement_5057G_normal.png"))
    json.dump({"frame": "photo view from the back, mm: x right (toward 9 o'clock), y up (12); mirror x for the front frame",
               "texture_half_size": R, "window_r": R_WIN,
               "rotor": {"pivot": pivot, "radius": round(rr0, 4), "arc_centre": [round(float(px0), 4), round(float(py0), 4)]},
               "bridges": bridges, "wheels": wheels, "jewels": jewels,
               "steel_wheels": [list(w) for w in STEEL_WHEELS], "pockets": pockets,
               "gold_gears": {k: list(v) for k, v in GOLD_GEARS.items()}, "balance": list(BALANCE),
               "screws": [[round(x, 4), round(y, 4), SCREW_R] for x, y in SCREWS]},
              open(os.path.join(HERE, "movement.json"), "w"))
    if SCR:
        dbg = img2.copy()
        dbg[bmask] = dbg[bmask] * 0.6 + np.array([0, 90, 255]) * 0.4
        for w in wheels:
            for x, y in w["outer"]:
                i, j = int((R - y) * K), int((x + R) * K)
                dbg[max(0, i - 2):i + 2, max(0, j - 2):j + 2] = (255, 0, 0)
        Image.fromarray(dbg.astype(np.uint8)).resize((1024, 1024)).save(os.path.join(SCR, "mvt_layers.png"))


def laplace(a, U, iters=400):
    a = a.copy()
    known = ~U
    a[U] = a[known].mean(0)
    for _ in range(iters):
        p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
        avg = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) * 0.25
        a[U] = avg[U]
    return a


if __name__ == "__main__":
    main()
