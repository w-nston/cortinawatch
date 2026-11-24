# Builds the 5057R dial textures from its photograph (white dial, black print), like
# dial_from_photo.py does for the 5057G, but simpler: the dial layout is the 5057G's (same pivots), so
# the photo is registered by an affine fit of its four hand pivots to the known pivots, and the hands
# are filled with the white of the dial round them. The 3D hands stand exactly where the photo's
# stood (POSE in build_5057.py), so the filled ground stays under them.
#
#   photo  "watch photos/5057r/patek-philippe-calatrava-cortina-jubilee-power-reserve-rose-gold-watch-5057-51455_5d593_md.jpg"
#          straight-on, 900 px (~21 px/mm on the dial)
#   writes dial_5057R_photo_color.jpg (4096², sRGB) and dial_5057R_photo_orm.png, spanning r = 15.4 mm
#   prints the hands' angles (for build_5057.py's 5057R pose)
#
# Run with system python (numpy, scipy, Pillow):  python3 blender/dial_5057r_from_photo.py
import glob, os, math, numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = glob.glob(os.path.join(HERE, "..", "watch photos", "5057r", "patek-philippe-calatrava-cortina-jubilee-*_md.jpg"))[0]
OUT = os.path.join(HERE, "textures")
SCR = os.environ.get("SCRATCH")

N = 4096
R = 15.4
K = N / (2 * R)
# pivots in dial mm (the 5057G's, fitted to its printed scales) and as read on the 5057R photo (px)
PIVOTS_MM = [(0.0, 0.0), (-6.273, 6.279), (-3.529, -6.128), (7.369, -6.272)]
PIVOTS_PX = [(437.5, 452.5), (301.5, 326.0), (361.5, 586.0), (592.5, 580.0)]
HUB_PX = [9, 6, 6, 6]        # hub radii in the photo, for refining the pivots
# hands as photographed: pivot index and tip (photo px) give the angle; the footprint is the 3D hand's
# own (build_5057.py leaf_hand: length, full width, tail, neck, hub radius, peak)
HANDS = [
    dict(p=0, tip=(255.0, 325.0), L=10.5, wmax=1.0, tail=1.4, neck=0.3, hub=1.0, peak=0.72),     # hour
    dict(p=0, tip=(687.5, 340.0), L=12.85, wmax=0.62, tail=1.8, neck=0.24, hub=0.7, peak=0.55),  # minute
    dict(p=1, tip=(382.5, 306.0), L=4.05, wmax=0.46, tail=0.9, neck=0.14, hub=0.55, peak=0.58),  # power reserve
    dict(p=2, tip=(327.5, 500.0), L=5.25, wmax=0.44, tail=0.9, neck=0.13, hub=0.55, peak=0.58),  # date
    dict(p=3, tip=(615.0, 650.0), L=3.75, wmax=0.3, tail=0.9, neck=0.1, hub=0.5, peak=0.58),     # seconds
]


def leaf_width(h, u):
    """Full width of the leaf hand at distance u along it (as build_5057.leaf_hand)."""
    L, wmax, tail, neck, peak = h["L"], h["wmax"], h["tail"], h["neck"], h["peak"]
    tail_w = neck * (0.55 + 0.45 * (1 + np.clip(u, -tail, 0) / tail))
    t = np.clip(u / L, 0, 1)
    rise = np.maximum(neck, wmax * np.maximum(0, np.sin(0.5 * np.pi * np.minimum(t, peak) / peak)) ** 1.2)
    fall = wmax * np.maximum(0, (1 - t) / (1 - peak)) ** 0.85
    w = np.where(u < 0, tail_w, np.where(t < peak, rise, fall))
    return np.where((u < -tail) | (u > L), 0, w)


def refine(photo_L, px, r):
    """Hub centre: the spot where a dark disc of radius r is darkest against its ring."""
    best = None
    yy, xx = np.mgrid[-r * 3:r * 3 + 1, -r * 3:r * 3 + 1]
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            cx, cy = int(round(px[0])) + dx, int(round(px[1])) + dy
            win = photo_L[cy - r * 3:cy + r * 3 + 1, cx - r * 3:cx + r * 3 + 1]
            d = np.hypot(xx, yy)
            inner, ring = win[d <= r * 0.8].mean(), win[(d > r * 1.4) & (d < r * 2.2)].mean()
            sc = ring - inner
            if best is None or sc > best[0]:
                best = (sc, cx, cy)
    return float(best[1]), float(best[2])


def main():
    ph = np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float32)
    L = ph.mean(2)
    piv = list(PIVOTS_PX)   # read on a 2x gridded crop; refine() is pulled off-centre by the hands
    # affine photo px -> dial mm (least squares over the four pivots)
    A = np.array([[x, y, 1] for x, y in piv])
    mx = np.linalg.lstsq(A, np.array([p[0] for p in PIVOTS_MM]), rcond=None)[0]
    my = np.linalg.lstsq(A, np.array([p[1] for p in PIVOTS_MM]), rcond=None)[0]
    res = [math.hypot(*(np.array([mx @ [x, y, 1], my @ [x, y, 1]]) - np.array(q))) for (x, y), q in zip(piv, PIVOTS_MM)]
    print("pivots px", [tuple(round(v, 1) for v in p) for p in piv], "residuals mm", [round(r_, 3) for r_ in res])
    # inverse: dial mm -> photo px
    M = np.array([[mx[0], mx[1], mx[2]], [my[0], my[1], my[2]], [0, 0, 1]])
    Mi = np.linalg.inv(M)
    mm = (np.arange(N) + 0.5) / K - R
    X, Y = np.meshgrid(mm, -mm)
    px = Mi[0, 0] * X + Mi[0, 1] * Y + Mi[0, 2]
    py = Mi[1, 0] * X + Mi[1, 1] * Y + Mi[1, 2]
    img = np.stack([ndimage.map_coordinates(ph[..., c], [py, px], order=3, mode="nearest") for c in range(3)], -1)
    img = np.clip(img, 0, 255)
    to_mm = lambda p: (mx @ [p[0], p[1], 1], my @ [p[0], p[1], 1])
    # the hands: their 3D footprints (where the model's hands will stand), plus whatever is dark and
    # touching them a little beyond (the photo hands' edges and soft shadows), but no further, so the
    # print beside a hand stays
    Lt = img.mean(2)
    core = np.zeros(X.shape, bool)
    for h in HANDS:
        cx, cy = PIVOTS_MM[h["p"]]
        tx, ty = to_mm(h["tip"])
        a = math.atan2(ty - cy, tx - cx)
        h["angle"] = math.degrees(a)
        print(f"hand at pivot {h['p']}: angle {h['angle']:.1f}°, tip r {math.hypot(tx - cx, ty - cy):.2f} mm")
        u, v = (X - cx) * math.cos(a) + (Y - cy) * math.sin(a), -(X - cx) * math.sin(a) + (Y - cy) * math.cos(a)
        wv = leaf_width(h, u)
        core |= (wv > 0) & (np.abs(v) < wv / 2 + 0.05)
        core |= np.hypot(X - cx, Y - cy) < h["hub"] + 0.05
    # the dial's local tone (its light falls off across it): a wide average of the dial alone, leaving out
    # the hands and the black print
    near = ndimage.binary_dilation(core, iterations=int(0.35 * K))
    plain = (Lt > 180) & ~near
    sig = 0.8 * K
    w_ = ndimage.gaussian_filter(plain.astype(np.float32), sig)
    local = np.stack([ndimage.gaussian_filter(img[..., c] * plain, sig) for c in range(3)], -1) / np.maximum(w_, 1e-3)[..., None]
    Ll = local.mean(2)
    # only the photo's hands and their soft shadows: pixels darker than the dial there, touching the hands;
    # the rest of the 3D hands' footprint is the photo's own dial already and stays as it is
    # (a narrow band only: whole print letters touching a hand, like PHILIPPE under the minute hand, stay)
    dark = near & (Lt < Ll - 10)
    mask = dark & ndimage.binary_dilation(core, iterations=int(0.12 * K))
    mask = ndimage.binary_dilation(mask, iterations=int(0.03 * K))
    # fill with the tone just round each hand (a thin ring outside it, print left out), so the fill meets
    # the soft shadow it sits in without a seam; wider rings only where the thin one cannot reach
    ring = ndimage.binary_dilation(mask, iterations=int(0.25 * K)) & ~mask & (Lt > 150)
    fill = np.zeros(img.shape, np.float32)
    done = np.zeros(X.shape, bool)
    for sig_mm in (0.25, 0.5, 1.0, 2.0):
        w_ = ndimage.gaussian_filter(ring.astype(np.float32), sig_mm * K)
        f_ = np.stack([ndimage.gaussian_filter(img[..., c] * ring, sig_mm * K) for c in range(3)], -1) / np.maximum(w_, 1e-6)[..., None]
        take = mask & ~done & (w_ > 0.02)
        fill[take] = f_[take]
        done |= take
    fill[mask & ~done] = local[mask & ~done]
    soft = ndimage.gaussian_filter(mask.astype(np.float32), 1.2)
    img = img * (1 - soft[..., None]) + np.where(mask[..., None], fill, img) * soft[..., None]
    Image.fromarray(img.astype(np.uint8)).save(os.path.join(OUT, "dial_5057R_photo_color.jpg"), quality=93)
    # ORM: glossy white lacquer, black print a touch less glossy; not metal
    Lr = img.mean(2)
    orm = np.zeros(img.shape, np.uint8)
    orm[..., 0] = 255
    orm[..., 1] = np.where(Lr < 110, 0.32, 0.16) * 255
    orm[..., 2] = 0
    Image.fromarray(orm).save(os.path.join(OUT, "dial_5057R_photo_orm.png"))
    if SCR:
        Image.fromarray(img.astype(np.uint8)).resize((1400, 1400)).save(os.path.join(SCR, "dial_r_tex.png"))
    print("wrote dial_5057R_photo_color.jpg, dial_5057R_photo_orm.png")


if __name__ == "__main__":
    main()
