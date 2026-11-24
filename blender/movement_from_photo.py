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
# screw heads: circle detection on the photo's edges, checked by eye (jewels, hubs and the engraved
# regulator mark rejected; three missed heads added)
SCREWS = [(-4.36, 11.22), (1.27, 11.97), (9.34, 8.19), (-11.83, 1.64), (-9.32, -3.0), (-10.62, -5.75),
          (6.95, -9.54), (11.65, 3.59), (-5.22, -10.84), (-1.42, -10.8, 0.36), (0.06, -11.6, 0.36)]   # last two: the cock head's small screws
# the two round "screws" on the rotor in the photo are wheel 1497's screws (51497) seen through
# holes in the rotor 1143 (parts diagram); they stay put while the rotor's holes sweep past
ROTOR_SCREWS = [(4.46, -0.91), (8.64, -0.94)]
EXTRA_JEWELS = [(3.62, 11.6, 0.42), (4.91, 8.57, 0.42),   # darker rubies the colour test missed
                (-10.86, 2.62, 0.3)]                      # beside the barrel bridge's cutout
# Shapes the edge tracer cannot see, read on 1 mm-gridded close-ups of the photo (x, y, r):
#   the barrel bridge's curved cutout at 9 o'clock (beside "SWISS"): a round bite out of its edge
#   down to the plate, next to the screw at (-11.83, 1.64);
#   the balance cock runs on under the rotor's rest position to the window's edge.
CUTOUTS = {"bridge_train": [(-12.16, 3.48, 1.14)]}
RIM_BAND = 12.4          # a bridge reaching past this radius runs on to the window (the photo blurs there)
# the automatic bridge's tail runs under its end screw to the rim (the tracer stops at the screw head)
PATCHES = {"bridge_centre": [[(8.9, 7.62), (10.55, 7.12), (11.4, 7.6), (10.3, 8.7), (9.6, 8.4)]]}
# the cock's head, drawn clean (the tracer frays on the balance under it): a disc round the balance
# jewel and the arm between its straight edges. The crescent below it with two small screws is the
# pallet bridge 125 (parts diagram), kept clear of the head.
COCK_HEAD = {"centre": (0.52, -9.38), "r": 1.8, "arm_top": -7.48, "arm_bottom": -11.15, "replace_r": 2.7}
COCK_WEDGE = [(5.0, -11.45), (5.35, -11.6), (7.5, -14.5), (16.0, -9.0), (10.6, -6.25)]
ROTOR_PIT = 7.35          # every bridge stops at this radius round the rotor's pivot: the rotor turns in a pit
# Small finishing details (x, y, r):
#   polished countersunk holes (steady-pin and tool holes) in the bridges;
#   gold chatons: rubies (or the barrel arbor's steel pivot) set in polished gold rings.
PIN_HOLES = [(0.94, 2.7, 0.2), (-9.86, -0.17, 0.25), (-12.19, -2.33, 0.2), (5.56, -8.19, 0.3), (9.44, -7.62, 0.3), (5.53, -10.69, 0.3)]
CHATONS = [(-5.77, 5.14, 0.42, "steel"),     # barrel arbor bushing, barrel bridge 105
           (-4.79, -7.63, 0.73, "ruby"),     # train bridge 110
           (0.52, -9.38, 0.62, "ruby")]      # balance cock 121: the balance jewel, with its shock spring
ROTOR_PIVOT = (6.47, 0.06)  # the hub's bearing ring (r 1.55) and the cross and two holes are symmetric about x 6.5
SCREW_R = 0.62
# The visible train, photo-view mm (centre x, y, tip radius, teeth, spokes). Circles fitted to the gold
# teeth seen past the barrel bridge's edge (residuals < 0.05 mm): the long toothed arc beside "ADJUSTED"
# is the mainspring barrel's rim (415, on the barrel bridge's bushing, r 5.1 to the tooth roots); below it
# the wheel it drives (200, r 2.67, its pinion on the barrel's teeth: centres 6.4 mm apart). The fourth
# wheel carries the small seconds: on the train bridge's jewel (-7.14, -6.06), meshing with the escape pinion.
# Names are Patek Philippe's part numbers from the Calibre 240 parts diagram ("watch photos/240 movement.jpg").
GOLD_GEARS = {"200_centre_wheel": (-3.62, -0.91, 2.67, 72, 5), "1481_reduction_wheel": (1.95, 6.55, 2.6, 64, 5),
              "210_third_wheel": (-3.02, -3.32, 1.95, 56, 6), "220_fourth_wheel": (-7.14, -6.06, 2.56, 80, 4)}
BARREL = (-5.77, 5.14, 5.4, 112)   # centre (the bushing), tooth tips, teeth; drum r 5.05
# steel: crown wheel, the large ratchet/reduction wheel of the automatic winding, its partner
STEEL_WHEELS = [(7.53, 5.22, 1.86), (6.22, 0.0, 3.8)]   # 1480 (under the automatic bridge), 1497 (under the rotor)
# Gyromax balance: rim fitted to the photo's gold pixels (outer r 3.95, centre on the cock's jewel);
# four arms (photo-view angles 81°, 171°, 261°, 351°), a slotted gold weight at each arm's end
BALANCE = (0.52, -9.38, 3.95)
BALANCE_ARMS = 82.0
# Escapement, read on the photo with the parts diagram (702 escape wheel, 710 pallet lever, 125 pallet
# bridge). The escape wheel turns under the train bridge's gold chaton (its jewel; 2.9 mm from the
# seconds wheel's jewel at (-7.14, -6.06), the right distance to mesh with it). The pallet lever pivots
# in the round jewel left of the balance (the pallet bridge's lobe). Its stones, as photographed: the
# exit stone lies flat in its "⊐" socket, tip toward the wheel; the entry stone is long and upright, its
# back showing at (-2.9, -10.1) and its tip under the balance's weight. Both tips sit just inside the
# teeth (2.25 mm out).
ESCAPE = (-4.77, -7.66, 2.25)
ESC_TEETH = 20
PALLET_PIVOT = (-2.22, -8.59)
STONES = {"exit": ((-2.65, -7.72), (-2.17, -7.72)),       # (tip, back)
          "entry": ((-3.0, -8.95), (-2.9, -10.42))}
NOT_JEWELS = [(-2.36, -7.69), (-2.21, -8.57)]   # the exit stone and the pallet jewel: built with the escapement
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
        out.append((x * R_WIN / r, y * R_WIN / r) if r > 12.95 else (x, y))   # bridges run to the window
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
    pivot = ROTOR_PIVOT
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
    traced = os.path.join(HERE, "movement_parts.json")
    src = BRIDGES
    if os.path.exists(traced):   # outlines traced on the photograph's edges (trace_movement.py)
        tp = json.load(open(traced))["parts"]
        src = {k: max(v["polys"], key=len) for k, v in tp.items() if v["class"] == "bridge" and v["polys"]}
    for name, pts in src.items():
        _, outline = poly_mask(pts, X, Y)
        outline = refine_bridge(name, outline)
        m, outline = poly_mask(outline, X, Y)
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
    jewels += [list(j) for j in EXTRA_JEWELS]
    jewels = [j for j in jewels if all(math.hypot(j[0] - x, j[1] - y) > 0.35 for x, y in NOT_JEWELS)]
    print(f"{len(wheels)} wheel outlines, {len(jewels)} jewels, {len(bridges)} bridges")

    # ---- sinkings: the union of a circle round every wheel (gold: fitted to its outline)
    circles = [list(w) for w in STEEL_WHEELS] + [list(g_[:3]) for g_ in GOLD_GEARS.values()] + [list(BALANCE), list(ESCAPE),
                                                                                              list(BARREL[:3])]
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
    # the barrel bridge's cutout goes on down into the plate: a deep, shadowed round recess
    from shapely.geometry import Point as _Pt
    for cuts in CUTOUTS.values():
        for cx_, cy_, r_ in cuts:
            cut = _Pt(cx_, cy_).buffer(r_, 64).intersection(_Pt(0, 0).buffer(R_WIN - 0.3, 512))
            pockets.append({"outer": [[round(x, 4), round(y, 4)] for x, y in cut.exterior.coords[:-1]], "islands": []})
    print(f"{len(circles)} wheel circles -> {len(pockets)} sinkings")
    # the balance and escapement sit in a deeper pit (0.6 mm under the sinking floor): the escape wheel and
    # pallet fork run under the balance, the hairspring over its arms, as photographed
    pit = _Pt(BALANCE[0], BALANCE[1]).buffer(BALANCE[2] + 0.2, 128).union(_Pt(ESCAPE[0], ESCAPE[1]).buffer(ESCAPE[2] + 0.2, 64))
    pit = pit.intersection(_Pt(0, 0).buffer(R_WIN - 0.35, 512)).simplify(0.01)
    deep_pit = [[round(x, 4), round(y, 4)] for x, y in pit.exterior.coords[:-1]]
    escapement = escapement_layout()

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
               "gold_gears": {k: list(v) for k, v in GOLD_GEARS.items()}, "balance": list(BALANCE), "barrel": list(BARREL),
               "screws": [[round(sc[0], 4), round(sc[1], 4), sc[2] if len(sc) > 2 else SCREW_R] for sc in SCREWS],
               "balance_arms_deg": BALANCE_ARMS, "deep_pit": deep_pit,
               "hairspring_stud": [1.5, -11.37], "escapement": escapement,
               "rotor_screws": [list(p) for p in ROTOR_SCREWS], "escape": list(ESCAPE),
               "pin_holes": [list(h) for h in PIN_HOLES], "chatons": [list(c) for c in CHATONS],
               "cutouts": {k: [list(c) for c in v] for k, v in CUTOUTS.items()}},
              open(os.path.join(HERE, "movement.json"), "w"))
    if SCR:
        dbg = img2.copy()
        dbg[bmask] = dbg[bmask] * 0.6 + np.array([0, 90, 255]) * 0.4
        for w in wheels:
            for x, y in w["outer"]:
                i, j = int((R - y) * K), int((x + R) * K)
                dbg[max(0, i - 2):i + 2, max(0, j - 2):j + 2] = (255, 0, 0)
        Image.fromarray(dbg.astype(np.uint8)).resize((1024, 1024)).save(os.path.join(SCR, "mvt_layers.png"))


def refine_bridge(name, outline):
    """Cutouts, lobes and the rotor's pit on a traced bridge outline (shapely, photo-view mm)."""
    from shapely.geometry import Polygon, Point, box
    P = Polygon(outline).buffer(0)
    # run on to the window: every 0.5° ray that meets the bridge beyond RIM_BAND gets the band to the rim
    wedges = []
    band = Point(0, 0).buffer(R_WIN + 0.4, 512).difference(Point(0, 0).buffer(RIM_BAND, 512))
    near = P.intersection(band)
    for k in range(720 if name != "pallet_bridge" else 0):
        a0, a1 = math.radians(k * 0.5), math.radians(k * 0.5 + 0.5)
        w = Polygon([(0, 0), (20 * math.cos(a0), 20 * math.sin(a0)), (20 * math.cos(a1), 20 * math.sin(a1))])
        if near.intersection(w).area > 0.004:
            wedges.append(w.intersection(band))
    if wedges:
        from shapely.ops import unary_union
        P = P.union(unary_union(wedges).buffer(0.01))
    for patch in PATCHES.get(name, []):
        P = P.union(Polygon(patch))
    if name == "balance_cock":
        h = COCK_HEAD
        c = Point(*h["centre"])
        head = c.buffer(h["r"], 96).union(box(h["centre"][0], h["arm_bottom"], 3.4, h["arm_top"]))
        P = P.difference(c.buffer(h["replace_r"], 96)).union(head)
        P = P.union(Polygon(COCK_WEDGE).intersection(Point(0, 0).buffer(R_WIN + 0.5, 256)))
    if name == "pallet_bridge":
        # 125 is a ring round the balance staff (the roller turns in its hole) with a lobe for the pallet
        # jewel; it lies under the balance. The tracer sees only the crescent outside the cock's head.
        from shapely.ops import nearest_points
        B = Point(*BALANCE[:2])
        pv = Point(*PALLET_PIVOT)
        near = nearest_points(P, pv)[0]
        lobe = pv.buffer(0.45, 48).union(near.buffer(0.35, 32)).convex_hull
        P = P.union(lobe).union(B.buffer(2.0, 96)).difference(B.buffer(0.75, 64))
    P = P.buffer(0.3, 16).buffer(-0.3, 16)         # close the tracer's slits and notches
    P = P.intersection(Point(0, 0).buffer(R_WIN, 512))
    for cx, cy, r in CUTOUTS.get(name, []):       # a bite: the circle and its way out through the rim
        d = math.hypot(cx, cy)
        c = Point(cx, cy).buffer(r, 64)
        P = P.difference(c.union(Point(cx * (d + 2) / d, cy * (d + 2) / d).buffer(r, 64)).convex_hull)
    P = P.difference(Point(*ROTOR_PIVOT).buffer(ROTOR_PIT, 256))
    if P.geom_type != "Polygon":
        P = max(P.geoms, key=lambda g: g.area)
    P = P.buffer(0.08, 16).buffer(-0.08, 16)        # no slivers or knife-edge corners
    return [tuple(map(float, p)) for p in P.simplify(0.02).exterior.coords[:-1]]


def escapement_layout():
    """Escape wheel, pallet lever (fork, arms, stone sockets) and stones at rest, photo-view mm."""
    from shapely.geometry import Polygon, Point
    from shapely.ops import unary_union
    ex, ey, re_ = ESCAPE
    E, Pv, B = np.array([ex, ey]), np.array(PALLET_PIVOT), np.array(BALANCE[:2])
    u = (B - Pv) / np.linalg.norm(B - Pv)
    n = np.array([-u[1], u[0]])
    LB = float(np.linalg.norm(B - Pv))
    rect = lambda c, d, l0, l1, w: Polygon([c + d * l0 + np.array([-d[1], d[0]]) * w / 2, c + d * l1 + np.array([-d[1], d[0]]) * w / 2,
                                            c + d * l1 - np.array([-d[1], d[0]]) * w / 2, c + d * l0 - np.array([-d[1], d[0]]) * w / 2])
    parts = [Point(*Pv).buffer(0.32, 32), rect(Pv, u, 0.0, LB - 0.8, 0.22)]           # hub, lever arm
    horns = rect(Pv, u, LB - 0.85, LB - 0.3, 0.5).difference(rect(Pv, u, LB - 0.62, LB - 0.2, 0.18))
    parts.append(horns)                                                                # fork horns round the impulse pin
    stones, slots = {}, []
    for name, (tip, back) in STONES.items():
        tip, back = np.array(tip), np.array(back)
        L = float(np.linalg.norm(back - tip))
        d = (back - tip) / L                                    # along the stone, tip to back
        w = 0.26                                                # its face as photographed: 0.26-0.30 mm
        side = np.array([-d[1], d[0]]) * w / 2
        # the stone, its impulse face slanted at the tip
        stones[name] = [list(map(float, p)) for p in (tip + side, back + side, back - side, tip + d * 0.09 - side)]
        sock = rect(tip, d, L - 0.38, L + 0.12, 0.5)            # the arm's socket round the stone's back
        sc = tip + d * (L - 0.13)
        arm = rect(Pv, (sc - Pv) / np.linalg.norm(sc - Pv), 0.0, float(np.linalg.norm(sc - Pv)), 0.3)
        parts += [sock, arm]
        slots.append(rect(tip, d, L - 0.38, L, w))              # open on the viewer's side: the stone shows in it
    lever = unary_union(parts).difference(unary_union(slots)).buffer(0.03, 8).buffer(-0.03, 8)
    if lever.geom_type != "Polygon":
        lever = max(lever.geoms, key=lambda g: g.area)
    r2 = lambda p: [round(float(p[0]), 4), round(float(p[1]), 4)]
    return {"wheel": [ex, ey, re_, ESC_TEETH], "pivot": list(PALLET_PIVOT), "balance": list(BALANCE[:2]),
            "lever": [r2(p) for p in lever.exterior.coords[:-1]],
            "lever_holes": [[r2(p) for p in h.coords[:-1]] for h in lever.interiors],
            "stones": {k: [r2(p) for p in v] for k, v in stones.items()},
            "impulse_pin_r": 0.48, "lift_deg": 7.0}


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
