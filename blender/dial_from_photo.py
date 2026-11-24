# Builds the 5057G dial textures from two photographs of the real dial.
#
#   main  "watch photos/5057G/AS…--1_….webp"  straight-on, 2500 px (~34 px/mm on the dial)
#   alt   "watch photos/5057G/dial-angle-hands-elsewhere.webp"  angled, hands in other places
#
#   1. main -> dial millimetres. Centre and scale from ellipse fits (blender/dial_register.py):
#      the railway's inner white line gives the centre, the bezel's outer edge (36.15 mm) the
#      scale; the photo is 2.8 % foreshortened vertically and turned 0.77°.
#   2. alt -> dial millimetres by a homography fitted to nine numeral strokes (max residual
#      0.25 px), so its print lands on the main photo's print.
#   3. Where the main photo has a hand and the angled photo does not, the angled photo fills in,
#      blended in the gradient domain: alt + a smooth (harmonic) correction that matches the main
#      photo all round the edge, so the light and the sunburst blend without a seam.
#   4. Where both photos have a hand (hour hand, hubs, the inner date hand), the dial is filled
#      smoothly and the print is rebuilt from the same print elsewhere on this dial: power-reserve
#      dots one step over, date dots two days over, the 24 h dot from the 12 h dot, the "2" of
#      "24" from the "2" of "12" (the labels are set radially), the arm of the X from its other arm.
#   5. Writes dial_5057G_photo_color.jpg (4096², sRGB) and dial_5057G_photo_orm.png
#      (G roughness, B metalness), both spanning r = 15.4 mm like js drawDial().
#
# Run with system python (numpy, scipy, Pillow):  python3 blender/dial_from_photo.py
import glob, os, math, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(HERE, "..", "watch photos", "5057G")
OUT = os.path.join(HERE, "textures")
SCR = os.environ.get("SCRATCH")  # optional: debug images

N = 4096
R = 15.4                          # texture spans [-R, R] mm
K = N / (2 * R)                   # px per mm in the texture

# main photo registration
CX, CY = 1259.2, 1249.4           # dial centre in the photo
SX = 622.2 / 18.075               # photo px/mm across
SY = SX * 435.5 / 448.0           # photo px/mm vertically
ROT = -0.77                       # degrees

# angled photo: numeral-stroke centroids, dial mm (from the main photo) -> alt px
ALT_PAIRS = [((5.64, 9.746), (1100.5, 558.7)),      # I
             ((11.294, 0.717), (1084.5, 867.8)),    # III, three bars
             ((11.291, -0.053), (1071.2, 886.3)),
             ((11.301, -0.823), (1057.9, 904.9)),
             ((-11.251, 0.538), (520.2, 498.6)),    # IX: X, I
             ((-11.252, -0.673), (499.4, 527.1)),
             ((-9.7, 5.804), (650.1, 400.2)),       # X
             ((-5.913, 9.642), (810.4, 372.1)),     # XI: X, I
             ((-4.863, 10.247), (846.9, 375.0))]

# dial layout measured on the rectified main photo (mm, +X to 3, +Y to 12)
PR = (-6.273, 6.279)              # power reserve: dot circle r 3.909, 0 h at 20.8°, 3 h per 8.47°
DATE = (-3.529, -6.128)           # pointer date: dot circle r 4.804, 2 days per 23.2°
SECS = (7.369, -6.272)            # small seconds: tick ring r 3.38
MOON = dict(cx=-3.465, cy=-6.215, R=3.906, d=2.15, r=1.57)  # window: outer arc, two scallops

# hands as seen in each photo: pivot, angle°, length, tail, half-width, tip half-width,
# shadow (extra width on the +n side if > 0, on the -n side if < 0), optional leaf bulge
HANDS_MAIN = [
    dict(p=(0.0, 0.33), a=144.3, L=10.55, tail=1.6, w=0.38, wt=0.14, sh=0.2, bulge=(0.75, 0.66)),  # hour
    dict(p=(0.0, 0.33), a=28.8, L=13.0, tail=1.8, w=0.34, wt=0.12, sh=0.16),                    # minute
    dict(p=(-6.38, 6.31), a=15.4, L=4.25, tail=1.1, w=0.27, wt=0.1, sh=-0.2),                   # power reserve
    dict(p=(-3.52, -6.05), a=220.5, L=5.35, tail=0.9, w=0.3, wt=0.12, sh=0.3),                  # date
    dict(p=(7.26, -6.27), a=95.0, L=3.8, tail=0.9, w=0.3, wt=0.1, sh=0.12),                     # seconds
]
HUBS_MAIN = [((0.0, 0.2), 1.45), ((-6.4, 6.22), 0.85), ((-3.54, -6.12), 0.85), ((7.26, -6.33), 0.8)]
HANDS_ALT = [
    dict(p=(-0.10, 0.31), a=141.3, L=10.6, tail=1.6, w=0.48, wt=0.16, sh=0.0, bulge=(0.75, 0.74)),  # hour
    dict(p=(-0.10, 0.31), a=-9.8, L=13.1, tail=1.8, w=0.38, wt=0.14, sh=0.0),                     # minute
    dict(p=(-6.47, 6.47), a=13.7, L=4.3, tail=1.1, w=0.3, wt=0.1, sh=0.0),                        # power reserve
    dict(p=(-3.59, -6.16), a=209.0, L=5.45, tail=0.9, w=0.34, wt=0.12, sh=0.0),                   # date
    dict(p=(7.19, -5.96), a=-62.0, L=3.85, tail=0.9, w=0.32, wt=0.1, sh=0.0),                     # seconds
]
HUBS_ALT = [((-0.10, 0.31), 1.4), ((-6.47, 6.47), 0.85), ((-3.59, -6.16), 0.85), ((7.19, -5.96), 0.8)]


# ------------------------------------------------------------------ helpers
def grid():
    mm = (np.arange(N) + 0.5) / K - R
    X, Y = np.meshgrid(mm, -mm)
    return X, Y


def sample(img, X, Y, order=1):
    rows, cols = (R - Y) * K - 0.5, (X + R) * K - 0.5
    if img.ndim == 2:
        return ndimage.map_coordinates(img, [rows, cols], order=order, mode="nearest")
    return np.stack([ndimage.map_coordinates(img[..., c], [rows, cols], order=order, mode="nearest")
                     for c in range(img.shape[2])], -1)


def lum(img):
    return img @ np.array([0.299, 0.587, 0.114], np.float32)


def rot_about(P, deg):
    """dst -> src mapping that copies from deg degrees *before* (src at angle θ - deg about P)."""
    c, s = math.cos(math.radians(-deg)), math.sin(math.radians(-deg))
    def f(X, Y):
        dx, dy = X - P[0], Y - P[1]
        return P[0] + c * dx - s * dy, P[1] + s * dx + c * dy
    return f


def compose(*fs):
    def f(X, Y):
        for g in fs:
            X, Y = g(X, Y)
        return X, Y
    return f


def shift(dx, dy):
    return lambda X, Y: (X + dx, Y + dy)


def print_mask(L):
    """Printed lacquer: locally bright against the dial."""
    return ndimage.binary_dilation((L - ndimage.median_filter(L, size=25)) > 30, iterations=4)


# ------------------------------------------------------------------ the two photos in dial space
def rectify_main():
    X, Y = grid()
    c, s = math.cos(math.radians(ROT)), math.sin(math.radians(ROT))
    Xr, Yr = c * X - s * Y, s * X + c * Y
    photo = np.asarray(Image.open(glob.glob(os.path.join(PHOTOS, "AS*--1_*"))[0]).convert("RGB")).astype(np.float32)
    px, py = CX + Xr * SX, CY - Yr * SY
    return np.clip(np.stack([ndimage.map_coordinates(photo[..., k], [py, px], order=3, mode="nearest")
                             for k in range(3)], -1), 0, 255)


def alt_homography():
    A = []
    for (x, y), (u, v) in ALT_PAIRS:
        A.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        A.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    H = np.linalg.svd(np.array(A))[2][-1].reshape(3, 3)
    return H / H[2, 2]


def warp_alt():
    H = alt_homography()
    X, Y = grid()
    Q = np.stack([X, Y, np.ones_like(X)], -1) @ H.T
    u, v = Q[..., 0] / Q[..., 2], Q[..., 1] / Q[..., 2]
    photo = np.asarray(Image.open(os.path.join(PHOTOS, "dial-angle-hands-elsewhere.webp")).convert("RGB")).astype(np.float32)
    return np.clip(np.stack([ndimage.map_coordinates(photo[..., k], [v, u], order=3, mode="nearest")
                             for k in range(3)], -1), 0, 255)


# ------------------------------------------------------------------ hand masks
def hand_mask(hands, hubs):
    m = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(m)
    P = lambda x, y: ((x + R) * K - 0.5, (R - y) * K - 0.5)
    for h in hands:
        a = math.radians(h["a"])
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        left, right = [], []
        for t in np.linspace(-h["tail"] / h["L"], 1.0, 60):
            cx, cy = h["p"][0] + dx * t * h["L"], h["p"][1] + dy * t * h["L"]
            w = h["w"] if t < 0.8 else h["w"] + (h["wt"] - h["w"]) * (t - 0.8) / 0.2
            if "bulge" in h:  # leaf: widest at bulge[0] of the length
                tb, wb = h["bulge"]
                w = max(w, wb * max(0.0, 1 - abs(t - tb) / 0.28))
            wl, wr = w + max(0.0, h["sh"]), w + max(0.0, -h["sh"])
            left.append(P(cx + nx * wl, cy + ny * wl))
            right.append(P(cx - nx * wr, cy - ny * wr))
        tip = P(h["p"][0] + dx * (h["L"] + 0.15), h["p"][1] + dy * (h["L"] + 0.15))
        d.polygon(left + [tip] + right[::-1], fill=255)
    for (x, y), r in hubs:
        cx, cy = P(x, y)
        d.ellipse((cx - r * K, cy - r * K, cx + r * K, cy + r * K), fill=255)
    return np.asarray(m) > 0


# ------------------------------------------------------------------ smooth (harmonic) fill
def _jacobi(a, u, n):
    for _ in range(n):
        p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
        avg = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) * 0.25
        a[u] = avg[u]
    return a


def _pyr(a, u):
    h, w = u.shape
    if min(h, w) <= 24 or u.all():
        known = ~u
        a[u] = a[known].mean(0) if known.any() else 0
        return _jacobi(a, u, 300)
    h2, w2 = (h + 1) // 2, (w + 1) // 2
    kw = (~u).astype(np.float32)
    A = np.zeros((h2 * 2, w2 * 2, a.shape[2]), np.float32)
    Wt = np.zeros((h2 * 2, w2 * 2), np.float32)
    A[:h, :w] = a * kw[..., None]
    Wt[:h, :w] = kw
    As = A.reshape(h2, 2, w2, 2, -1).sum((1, 3))
    Ws = Wt.reshape(h2, 2, w2, 2).sum((1, 3))
    small = As / np.maximum(Ws, 1e-6)[..., None]
    small = _pyr(small, Ws == 0)
    up = np.repeat(np.repeat(small, 2, 0), 2, 1)[:h, :w]
    a[u] = up[u]
    return _jacobi(a, u, 40)


def laplace_fill(a, U, pad=48):
    """Fill the unknown pixels U of a (H×W×C) with the harmonic interpolant of their surroundings."""
    a = a.copy()
    if not U.any():
        return a
    ys, xs = np.nonzero(U)
    r0, r1 = max(0, ys.min() - pad), min(U.shape[0], ys.max() + pad + 1)
    c0, c1 = max(0, xs.min() - pad), min(U.shape[1], xs.max() + pad + 1)
    sub, u = a[r0:r1, c0:c1].copy(), U[r0:r1, c0:c1]
    sub = _pyr(sub, u)
    a[r0:r1, c0:c1][u] = sub[u]
    return a


# ------------------------------------------------------------------ print rebuilt where both photos have a hand
class Patcher:
    def __init__(self, src, base, hmask):
        self.src, self.out, self.hmask = src, base.copy(), hmask
        self.L = lum(src)
        self.Lbg = ndimage.grey_opening(ndimage.median_filter(self.L, 3), size=(41, 41))  # dial under the print
        self.X, self.Y = grid()

    def align(self, reg, f, search=0.06):
        """Refine a src mapping by the translation that best matches the visible part of reg."""
        vis = reg & ~self.hmask
        if vis.sum() < 50:
            return f
        X, Y, tgt = self.X[vis], self.Y[vis], self.L[vis]
        st, n = 1 / K, int(search * K)
        best, bd = None, (0.0, 0.0)
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                sx, sy = f(X + i * st, Y + j * st)
                e = np.mean((sample(self.L, sx, sy) - tgt) ** 2)
                if best is None or e < best:
                    best, bd = e, (i * st, j * st)
        return compose(shift(*bd), f)

    def apply(self, reg, f, mode="print", align=False):
        if align:
            f = self.align(reg, f)
        m = reg & self.hmask
        if not m.any():
            return
        sx, sy = f(self.X[m], self.Y[m])
        s = sample(self.src, sx, sy)
        if mode == "full":
            self.out[m] = s
            return
        a = np.clip((lum(s) - sample(self.Lbg, sx, sy) - 25) / 70, 0, 1)[:, None]
        self.out[m] = self.out[m] * (1 - a) + s * a


def blob_centroid(L, X, Y, near, rad, thr=150):
    m = (np.hypot(X - near[0], Y - near[1]) < rad) & (L > thr)
    return float(X[m].mean()), float(Y[m].mean())


# ------------------------------------------------------------------ build
def build():
    img, alt = rectify_main(), warp_alt()
    X, Y = grid()
    rr = np.hypot(X, Y)
    L, La = lum(img), lum(alt)
    pr, pra = print_mask(L), print_mask(La)
    hm = ndimage.binary_dilation(hand_mask(HANDS_MAIN, HUBS_MAIN), iterations=16)  # + 0.12 mm: edges, shadows
    ha = ndimage.binary_dilation(hand_mask(HANDS_ALT, HUBS_ALT), iterations=16)
    A = hm & ~ha    # covered in the main photo only: take the angled photo
    B = hm & ha     # covered in both

    # 3. gradient-domain blend: correction = harmonic interpolant of (main - alt) from clean dial
    unknown = hm | ha | pr | pra
    d = img - alt
    kw = (~unknown).astype(np.float32)
    sig = 0.08 * K
    d = ndimage.gaussian_filter(d * kw[..., None], (sig, sig, 0)) / np.maximum(ndimage.gaussian_filter(kw, sig), 1e-3)[..., None]
    c = laplace_fill(d, unknown)
    out = img.copy()
    out[A] = alt[A] + c[A]
    # the angled photo's hands are a little wider than their masks: any borrowed pixel clearly
    # darker than the smooth dial (and not near print) is hand or shadow, so it counts as covered
    smooth = laplace_fill(img, hm | pr)
    near_alt_hands = ndimage.binary_dilation(ha, iterations=int(0.35 * K))
    dark = A & near_alt_hands & ((lum(out) - lum(smooth)) < -12) & ~ndimage.binary_dilation(pra | pr, iterations=3)
    dark = ndimage.binary_opening(dark, iterations=2)
    dark = ndimage.binary_dilation(dark, iterations=8) & hm
    B = B | dark
    A = hm & ~B
    out = img.copy()
    out[A] = alt[A] + c[A]

    # 4. covered in both: smooth fill (ignoring nearby print), then rebuild the print
    U = B | (pr & ndimage.binary_dilation(B, iterations=40) & ~A)
    filled = laplace_fill(out, U)
    # sunburst streaks for the smooth fill: high-pass detail from a copy turned a few degrees about
    # the dial centre (the streaks are radial, so they stay radial), from wherever is clean
    hp = out - ndimage.gaussian_filter(out, (4, 4, 0))
    bad = hm | ha | pr | pra
    detail = np.zeros_like(out)
    left = B.copy()
    for deg in (9.0, -9.0, 18.0, -18.0):
        sx, sy = rot_about((0, 0), deg)(X[left], Y[left])
        ok = sample(bad.astype(np.float32), sx, sy, order=0) < 0.5
        idx = np.flatnonzero(left.ravel())[ok]
        detail.reshape(-1, 3)[idx] = sample(hp, sx[ok], sy[ok])
        left.ravel()[idx] = False
    out[B] = filled[B] + np.clip(detail[B], -20, 20)
    P = Patcher(img.copy(), out, B)
    P.src[A] = out[A]  # sources come from the combined image
    P.L = lum(P.src)
    P.Lbg = ndimage.grey_opening(ndimage.median_filter(P.L, 3), size=(41, 41))
    # date dots, two days over
    dd = np.hypot(X - DATE[0], Y - DATE[1])
    P.apply((dd > 4.25) & (dd < 5.45), rot_about(DATE, 23.2), mode="full")
    # power-reserve dots, one or two steps over, from wherever is clean
    dp = np.hypot(X - PR[0], Y - PR[1])
    ring = (dp > 3.55) & (dp < 4.3)
    todo = B.copy()
    for step in (8.47, 16.94, -16.94):
        f = rot_about(PR, step)
        sx, sy = f(X, Y)
        clean = sample(B.astype(np.float32), sx, sy, order=0) < 0.5
        P.hmask = todo
        P.apply(ring & clean, f, mode="full")
        todo = todo & ~(ring & clean)
    P.hmask = B
    # 24 h dot from the 12 h dot
    P.apply(np.hypot(X + 3.61, Y - 3.42) < 0.3, rot_about(PR, -34.0), mode="full")
    # the "2" of "24", from the "2" of "12": turn the "12" label onto the "24" label, then slide
    # the "2" from the second digit place to the first
    c1 = blob_centroid(P.L, X, Y, (-1.881, 4.913), 0.3)   # "1" of 12
    c2 = blob_centroid(P.L, X, Y, (-1.687, 5.411), 0.3)   # "2" of 12
    c4 = blob_centroid(P.L, X, Y, (-2.888, 3.110), 0.35)  # "4" of 24
    ang = lambda q: math.degrees(math.atan2(q[1] - PR[1], q[0] - PR[0]))
    dlt = ang(c4) - ang(c2)
    tx, ty = rot_about(PR, -dlt)(np.array(c1[0]), np.array(c1[1]))
    tx, ty = float(tx), float(ty)
    cc, ss = math.cos(math.radians(-dlt)), math.sin(math.radians(-dlt))
    two = lambda Xd, Yd: (c2[0] + cc * (Xd - tx) - ss * (Yd - ty), c2[1] + ss * (Xd - tx) + cc * (Yd - ty))
    P.apply(np.hypot(X - tx, Y - ty) < 0.42, two)
    # X at 10: the hour-hand tips cover an arm; point-mirror through the numeral's centre
    xc = blob_centroid(P.L, X, Y, (-9.7, 5.804), 0.9)
    P.apply(np.hypot(X - xc[0], Y - xc[1]) < 1.0, lambda a, b: (2 * xc[0] - a, 2 * xc[1] - b), align=True)
    out = P.out

    # centre: under both hubs and the hub shadow. A sunburst is radial streaks converging on the
    # centre, so each angle's value is carried inwards from a clean ring just outside
    hub = rr < 1.75
    ring_r = 1.85
    acc = np.zeros((hub.sum(), 3), np.float32)
    for dr in np.linspace(0.0, 0.12, 5):
        f = (ring_r + dr) / np.maximum(rr[hub], 1e-3)
        acc += sample(out, X[hub] * f, Y[hub] * f)
    out[hub] = acc / 5

    # outside the railway: carry the band out to the dial edge (the bevel is not dial)
    edge = rr > 14.12
    out[edge] = sample(out, X[edge] * 14.08 / rr[edge], Y[edge] * 14.08 / rr[edge])
    if SCR:
        dbg = np.zeros(hm.shape + (3,), np.uint8)
        dbg[A] = (0, 160, 255)
        dbg[B] = (255, 60, 0)
        Image.fromarray(dbg).resize((1024, 1024)).save(os.path.join(SCR, "dial_masks.png"))
        Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)).save(os.path.join(SCR, "alt_rect.png"))
        Image.fromarray(img.astype(np.uint8)).save(os.path.join(SCR, "dial_rect.png"))
    return out


# ------------------------------------------------------------------ roughness / metalness
def orm_map(out):
    X, Y = grid()
    L = lum(out)
    rr = np.hypot(X, Y)
    printm = ndimage.binary_dilation((L - ndimage.median_filter(L, size=25)) > 35, iterations=1)
    rough = np.full(L.shape, 0.38, np.float32)
    metal = np.full(L.shape, 0.4, np.float32)           # galvanic slate sunburst (light is in the photo)
    band = (rr > 13.0) & (rr < 14.25)                   # printed black railway band
    rough[band], metal[band] = 0.45, 0.0
    rough[printm], metal[printm] = 0.55, 0.0             # lacquer print
    o = np.zeros(L.shape + (3,), np.uint8)
    o[..., 0] = 255
    o[..., 1] = (rough * 255).astype(np.uint8)
    o[..., 2] = (metal * 255).astype(np.uint8)
    return o


if __name__ == "__main__":
    out = build()
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "dial_5057G_photo_color.jpg"), quality=93)
    Image.fromarray(orm_map(out)).save(os.path.join(OUT, "dial_5057G_photo_orm.png"))
    if SCR:
        Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((1400, 1400), Image.LANCZOS).save(os.path.join(SCR, "dial_clean.png"))
    print("wrote dial_5057G_photo_color.jpg / _orm.png")
