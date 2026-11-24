# The 5057R's movement engravings, typeset crisp in place of the 22 px/mm photo (the 1997 calibre 240
# has older, thinner engraving than the 5057G's): PATEK PHILIPPE and GENEVE SWISS set on arcs down the
# barrel bridge, TWENTY-NINE / JEWELS straight beside them, the serial 3168311 and 240/164 on the train
# bridge, and the Geneva Seal (the Poinçon de Genève: a shield parted down the middle, the half eagle on
# the left, the key on the right) on the barrel bridge beside the P of PATEK, where the 5057R's caseback
# photo and a second 1990s calibre 240 show it (placed from the screw and jewel beside it).
#
# Every line's arc (or angle), size, spacing and place is fitted to "watch photos/5057r/old 240
# movement.jpg" (registered to the movement's photo-view frame as in movement_finish.py) by maximising
# the overlap of the typeset line with the photo's warm engraving strokes.
#   python3 blender/engravings_5057r.py  ->  blender/textures/engravings_5057R.png (mask, photo-view frame)
import json, math, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage, optimize

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.environ.get("SCRATCH")
FONT = "/System/Library/Fonts/Supplemental/Baskerville.ttc"      # thin, classical serif capitals
FALLBACK = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
R = 14.06
N = 2048
K = N / (2 * R)
FIT_PPM = 30                                                      # the fit runs at 30 px/mm

OLD_PX = np.array([(382, 550), (450, 307), (162, 282), (240, 173), (232, 400), (260, 555), (205, 535)], float)
OLD_MM = np.array([(0.52, -9.38), (6.47, 0.06), (-5.77, 5.14), (-1.11, 8.83), (-4.28, -0.75), (-4.79, -7.63), (-7.14, -6.06)])

# lines: text, kind, initial guess (photo-view mm), read on the registered photo
#   arc:  centre (cx, cy), baseline radius r, angle of the text's middle (deg), cap height, tracking (mm)
#         set counter-clockwise, tops toward the centre
#   line: middle (x, y), reading angle (deg), cap height, tracking; tops to the left of the reading direction
LINES = [
    # the two names follow one gentle arc (r ~21 mm, its centre off the movement to the lower right)
    dict(text="PATEK PHILIPPE", kind="arc", p=[8.06, -6.74, 20.65, 134.8, 1.0, 0.12]),
    dict(text="GENEVE SWISS", kind="arc", p=[8.06, -6.74, 22.96, 138.7, 0.62, 0.12]),
    dict(text="TWENTY-NINE", kind="line", p=[-5.8, 2.5, -114.0, 0.62, 0.08]),
    dict(text="JEWELS", kind="line", p=[-7.8, 1.35, -102.0, 0.65, 0.08], flip=False),   # reads down, as TWENTY-NINE
    dict(text="3168311", kind="line", p=[-7.95, -8.1, -50.0, 0.68, 0.06]),
    dict(text="240/164", kind="line", p=[-8.55, -8.95, -50.0, 0.85, 0.06]),
]
SEAL = dict(x=-2.03, y=11.25, h=1.0, angle=10.0)     # centre, height (mm), turn (deg): top toward the rim


def font(size_px):
    try:
        return ImageFont.truetype(FONT, size_px, index=0)
    except OSError:
        return ImageFont.truetype(FALLBACK, size_px)


def target():
    """The photo's engraving strokes, warm against the silver, in photo-view mm at FIT_PPM."""
    A_ = np.c_[OLD_PX, np.ones(len(OLD_PX))]
    Aff = np.vstack([np.linalg.lstsq(A_, OLD_MM[:, 0], rcond=None)[0], np.linalg.lstsq(A_, OLD_MM[:, 1], rcond=None)[0], [0, 0, 1]])
    Ai = np.linalg.inv(Aff)
    src = np.asarray(Image.open(os.path.join(HERE, "..", "watch photos", "5057r", "old 240 movement.jpg")).convert("RGB")).astype(np.float32)
    n = int(2 * R * FIT_PPM)
    mm = (np.arange(n) + 0.5) / FIT_PPM - R
    X, Y = np.meshgrid(mm, -mm)
    ox, oy = Ai[0, 0] * X + Ai[0, 1] * Y + Ai[0, 2], Ai[1, 0] * X + Ai[1, 1] * Y + Ai[1, 2]
    c = np.stack([ndimage.map_coordinates(src[..., k], [oy, ox], order=3, mode="nearest") for k in range(3)], -1)
    warm = c[..., 0] - c[..., 2]
    warm = warm - ndimage.median_filter(warm, size=int(1.2 * FIT_PPM))
    return np.clip(warm / 40, 0, 1), X, Y


def place(line, p, ppm, size):
    """Glyph placements for a line: [(char, x, y, rot_deg)] in photo-view mm, rot = the glyph's up direction."""
    f = font(max(4, int(round(p[4] / 0.68 * ppm * 4)) if line["kind"] == "arc" else int(round(p[3] / 0.68 * ppm * 4))))
    cap = p[4] if line["kind"] == "arc" else p[3]
    track = p[5] if line["kind"] == "arc" else p[4]
    d = ImageDraw.Draw(Image.new("L", (4, 4)))
    xs_ = line.get("xscale", 1.0)
    widths = [d.textlength(ch, font=f) / (ppm * 4) * xs_ for ch in line["text"]]
    if "span" in line:                       # the photo's own extent: first letter's start to last's end
        t0, t1 = line["span"]
        track = (t1 - t0 - sum(widths)) / (len(widths) - 1)
        s = t0
    else:
        s = -(sum(widths) + track * (len(widths) - 1)) / 2
    out = []
    for ch, w in zip(line["text"], widths):
        m = s + w / 2
        if line["kind"] == "arc":
            cx, cy, r, mid = p[0], p[1], p[2], math.radians(p[3])
            th = mid + m / r                       # counter-clockwise
            x, y = cx + r * math.cos(th), cy + r * math.sin(th)
            up = math.degrees(th) + 180            # toward the centre
        else:
            x0, y0, a = p[0], p[1], math.radians(p[2])
            x, y = x0 + m * math.cos(a), y0 + m * math.sin(a)
            up = p[2] + 90
        out.append((ch, x, y, up))
        s += w + track
    return out, f, cap


def measure_span(line, p, tgt, X, Y):
    """Where the photo's engraving of this line starts and ends along its path (mm), and the letter
    condensing that fills it with a natural letter-spacing."""
    cap = p[4] if line["kind"] == "arc" else p[3]
    if line["kind"] == "arc":
        cx, cy, r, mid = p[0], p[1], p[2], math.radians(p[3])
        rr = np.hypot(X - cx, Y - cy)
        ang = np.arctan2(Y - cy, X - cx) - mid
        ang = (ang + np.pi) % (2 * np.pi) - np.pi
        t, v = ang * r, r - rr                    # along the arc; toward the centre = up the letters
    else:
        a = math.radians(p[2])
        t = (X - p[0]) * math.cos(a) + (Y - p[1]) * math.sin(a)
        v = -(X - p[0]) * math.sin(a) + (Y - p[1]) * math.cos(a)
    # the photo's letters for this line: clean strokes, merged into word clusters, the clusters the
    # typeset line lands on (so stray warm marks along the path do not count)
    clean = ndimage.binary_opening(tgt > 0.45, iterations=1) & (np.hypot(X, Y) < 12.5)
    words, n = ndimage.label(ndimage.binary_dilation(clean, iterations=int(0.4 * FIT_PPM)))
    typeset = ndimage.binary_dilation(render([(line, p)], FIT_PPM) > 0.3, iterations=int(0.5 * FIT_PPM))
    typeset = typeset[:X.shape[0], :X.shape[1]]
    ids = [i for i in range(1, n + 1) if (typeset & (words == i)).sum() > 0.25 * (words == i).sum()]
    m = clean & np.isin(words, ids) & (v > -0.3 * cap) & (v < 1.3 * cap)
    ts = t[m]
    if ts.size < 50:
        return None
    t0, t1 = np.percentile(ts, 1.0), np.percentile(ts, 99.0)
    f = font(int(round(cap / 0.68 * FIT_PPM * 4)))
    d = ImageDraw.Draw(Image.new("L", (4, 4)))
    nat = sum(d.textlength(ch, font=f) / (FIT_PPM * 4) for ch in line["text"])
    gaps = len(line["text"]) - 1
    xscale = min(1.0, max(0.6, (t1 - t0 - 0.1 * cap * gaps) / nat))
    return float(t0), float(t1), float(xscale)


def render(lines, ppm, size_mm=2 * R, ss=4):
    n = int(round(size_mm * ppm))
    img = Image.new("L", (n, n), 0)
    for line, p in lines:
        glyphs, f, cap = place(line, p, ppm, n)
        for ch, x, y, up in glyphs:
            if ch == " ":
                continue
            box = Image.new("L", (int(cap * 3 * ppm * ss), int(cap * 3 * ppm * ss)), 0)
            dg = ImageDraw.Draw(box)
            dg.text((box.width / 2, box.height / 2 + cap / 2 * ppm * ss), ch, font=f, fill=255, anchor="ms")
            xs_ = line.get("xscale", 1.0)
            if abs(xs_ - 1) > 1e-3:              # condensed letters, as the engraver's
                w0 = box.width
                box = box.resize((max(1, int(w0 * xs_)), box.height), Image.LANCZOS)
                pad = Image.new("L", (w0, box.height), 0)
                pad.paste(box, ((w0 - box.width) // 2, 0))
                box = pad
            box = box.rotate(up - 90, resample=Image.BICUBIC)
            box = box.resize((max(1, box.width // ss), max(1, box.height // ss)), Image.LANCZOS)
            px, py = (x + R) * ppm - box.width / 2, (R - y) * ppm - box.height / 2
            img.paste(255, (int(round(px)), int(round(py))), box)
    return np.asarray(img, np.float32) / 255


def fit(line, tgt, X, Y):
    p0 = np.array(line["p"], float)
    glyphs, _, cap = place(line, p0, FIT_PPM, 0)
    xs, ys = [g[1] for g in glyphs], [g[2] for g in glyphs]
    win = (X > min(xs) - 2.5) & (X < max(xs) + 2.5) & (Y > min(ys) - 2.5) & (Y < max(ys) + 2.5)
    t = ndimage.gaussian_filter(tgt, 1.0)

    def cost(p):
        m = ndimage.gaussian_filter(render([(line, p)], FIT_PPM), 1.0)
        a, b = m[win], t[win]
        a, b = a - a.mean(), b - b.mean()
        return -float((a * b).sum() / math.sqrt((a * a).sum() * (b * b).sum() + 1e-9))

    step = np.array([0.3, 0.3, 0.3, 2.0, 0.08, 0.04] if line["kind"] == "arc" else [0.25, 0.25, 3.0, 0.08, 0.04])
    simplex = [p0] + [p0 + np.eye(len(p0))[i] * step[i] for i in range(len(p0))]
    res = optimize.minimize(cost, p0, method="Nelder-Mead", options=dict(initial_simplex=simplex, maxiter=500, xatol=1e-3, fatol=1e-4))
    return res.x, -res.fun


def seal(img, ppm):
    """The Geneva Seal, drawn: a shield parted per pale, the half eagle (crowned, one wing) on the left,
    the key, bit outward, on the right; outline and charges in relief."""
    s = SEAL["h"]
    W = 400
    g = Image.new("L", (W, W), 0)
    d = ImageDraw.Draw(g)
    u = W / 1.3                                  # px per unit (unit = shield height)
    cx, top = W / 2, W / 2 - 0.5 * u
    P = lambda x, y: (cx + x * u, top + y * u)    # shield coords: x in [-0.4, 0.4], y down in [0, 1]
    shield = [P(-0.4, 0), P(0.4, 0), P(0.4, 0.55), P(0.3, 0.8), P(0, 1.0), P(-0.3, 0.8), P(-0.4, 0.55)]
    d.polygon(shield, fill=255)
    inner = [P(-0.34, 0.05), P(0.34, 0.05), P(0.34, 0.53), P(0.26, 0.76), P(0, 0.93), P(-0.26, 0.76), P(-0.34, 0.53)]
    d.polygon(inner, fill=0)
    d.line([P(0, 0.05), P(0, 0.93)], fill=255, width=int(0.045 * u))           # parted per pale
    # half eagle: head with crown, beak to the left, one spread wing, tail
    d.ellipse([P(-0.17, 0.16), P(-0.05, 0.28)], fill=255)                       # head
    d.polygon([P(-0.17, 0.2), P(-0.25, 0.23), P(-0.16, 0.25)], fill=255)        # beak
    d.polygon([P(-0.16, 0.14), P(-0.14, 0.08), P(-0.11, 0.12), P(-0.08, 0.07), P(-0.05, 0.14)], fill=255)  # crown
    d.polygon([P(-0.02, 0.28), P(-0.3, 0.3), P(-0.31, 0.42), P(-0.24, 0.4), P(-0.29, 0.52), P(-0.2, 0.5),
               P(-0.24, 0.62), P(-0.12, 0.58), P(-0.1, 0.7), P(-0.02, 0.66)], fill=255)                  # wing
    d.polygon([P(-0.02, 0.66), P(-0.12, 0.8), P(-0.02, 0.78)], fill=255)        # tail
    # key: bow (ring) at the top, shaft, bit to the right at the bottom
    d.ellipse([P(0.07, 0.12), P(0.23, 0.28)], outline=255, width=int(0.045 * u))
    d.rectangle([P(0.13, 0.27), P(0.17, 0.78)], fill=255)
    d.rectangle([P(0.17, 0.62), P(0.27, 0.7)], fill=255)
    d.rectangle([P(0.17, 0.72), P(0.24, 0.78)], fill=255)
    g = g.rotate(SEAL["angle"], resample=Image.BICUBIC)
    px_mm = u / s                                 # shield px per mm at this drawing
    sz = max(1, int(W / px_mm * ppm))
    g = g.resize((sz, sz), Image.LANCZOS)
    img.paste(255, (int((SEAL["x"] + R) * ppm - sz / 2), int((R - SEAL["y"]) * ppm - sz / 2)), g)


def main():
    tgt, X, Y = target()
    fitted = []
    saved = os.path.join(HERE, "engravings_5057R.json")
    if os.environ.get("REFIT") != "1" and os.path.exists(saved):     # reuse the last fit (REFIT=1 redoes it)
        by_text = {d["text"]: d["p"] for d in json.load(open(saved))}
        LINES[:] = [dict(l, p=by_text.get(l["text"], l["p"]), fitted=l["text"] in by_text) for l in LINES]
    for line in LINES:
        if line.get("fitted"):
            fitted.append((line, np.array(line["p"])))
            continue
        p, score = fit(line, tgt, X, Y)
        if line["kind"] == "line" and line.get("flip", True):   # straight lines: try reading the other way too
            alt = dict(line, p=list(line["p"]))
            alt["p"][2] += 180
            p2, s2 = fit(alt, tgt, X, Y)
            if s2 > score:
                p, score = p2, s2
        print(f"{line['text']:16s} fit {score:.3f}  " + " ".join(f"{v:.3f}" for v in p))
        fitted.append((line, p))
    spanned = []
    for line, p in fitted:
        sp = measure_span(line, p, tgt, X, Y)
        if sp:
            line = dict(line, span=[sp[0], sp[1]], xscale=sp[2])
            print(f"{line['text']:16s} span {sp[0]:.2f}..{sp[1]:.2f} mm, letters x{sp[2]:.2f}")
        spanned.append((line, p))
    fitted = spanned
    img = render(fitted, K)
    out = Image.fromarray((img * 255).astype(np.uint8))
    seal(out, K)
    out.save(os.path.join(HERE, "textures", "engravings_5057R.png"))
    json.dump([dict(text=l["text"], kind=l["kind"], p=[round(float(v), 4) for v in p]) for l, p in fitted],
              open(os.path.join(HERE, "engravings_5057R.json"), "w"), indent=1)
    if SCR:
        t8 = (np.clip(tgt, 0, 1) * 255).astype(np.uint8)
        m8 = np.asarray(Image.fromarray((render(fitted, FIT_PPM) * 255).astype(np.uint8)).resize(t8.shape[::-1]))
        Image.fromarray(np.stack([np.maximum(t8, m8 // 2), t8, m8], -1)).save(os.path.join(SCR, "engr_fit.png"))
    print("wrote engravings_5057R.png")


if __name__ == "__main__":
    main()
