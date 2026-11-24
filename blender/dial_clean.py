# Takes the photographed hands out of both dial textures, so the 3D hands can show any time.
#
# Every photograph of the 5057R has its hands near 10:10, so the dial under its hour and minute hands
# was never photographed; the 5057G's centre is clean (dial_from_photo.py took it from a photo with the
# hands elsewhere), but its sub-dials still carry smudges of their hands. The two dials share one printed
# layout (the 2022 watch is the 1997 one reinterpreted), and the textures are registered to the same
# frame, so each dial is rebuilt under its own hands from the other's print: the print is separated from
# the ground (white lacquer / slate sunburst) by a grey closing or opening, lined up by phase correlation,
# and repainted in this dial's ink on this dial's ground, filled in from round the hand.
# Where both dials' hands lie over the same place (the power reserve hands), only the ground is filled.
#
#   python3 blender/dial_clean.py   (reads textures/dial_5057{G,R}_photo_{color.jpg,orm.png})
#   writes textures/dial_5057{G,R}_clean_{color.jpg,orm.png}; build_5057.py's VARIANTS use them
import math, os, numpy as np
from PIL import Image
from scipy import ndimage
from skimage.feature import match_template

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "textures")
SCR = os.environ.get("SCRATCH")
N, R = 4096, 15.4                      # the dial textures span r = 15.4 mm (DIAL_TEX_R)
K = N / (2 * R)
PIV = dict(c=(0.0, 0.0), power=(-6.273, 6.279), date=(-3.529, -6.128), seconds=(7.369, -6.272))
# the leaf hands (build_5057.py leaf_hand: length, full width, tail, neck, hub, peak) and their pivots
HANDS = dict(
    hour=dict(p="c", L=10.5, wmax=1.0, tail=1.4, neck=0.3, hub=1.0, peak=0.72),
    minute=dict(p="c", L=12.85, wmax=0.62, tail=1.8, neck=0.24, hub=0.7, peak=0.55),
    power=dict(p="power", L=4.05, wmax=0.46, tail=0.9, neck=0.14, hub=0.55, peak=0.58),
    date=dict(p="date", L=5.25, wmax=0.44, tail=0.9, neck=0.13, hub=0.55, peak=0.58),
    seconds=dict(p="seconds", L=3.75, wmax=0.3, tail=0.9, neck=0.1, hub=0.5, peak=0.58),
)
# where each photo's hands stood (build_5057.py VARIANTS pose: degrees from 3 o'clock, anticlockwise)
POSES = {
    "5057G": dict(hour=143.6, minute=29.3, power=16.0, date=220.0, seconds=96.5),
    "5057R": dict(hour=143.0, minute=22.3, power=11.6, date=111.0, seconds=-73.2),
}
# which hands left marks in the texture (the 5057G's centre was cleaned from another photo)
MARKED = {"5057G": ("power", "date", "seconds"), "5057R": ("hour", "minute", "power", "date", "seconds")}
CORE, ZONE = 0.15, 1.0                 # mm round each hand: always cleaned / cleaned where not print
# what print looks like on each dial (black on the white 5057R, white on the slate 5057G): within ZONE of
# a hand, only pixels that are off the ground but are not print are the hand's (outline, glint, shadow)
OFF = {"5057R": 5, "5057G": 7}         # how far from the dial's tone a pixel must be to count as the hand
PRINTLIKE = {"5057R": lambda L, t: L < 105, "5057G": lambda L, t: (L > 170) & (t > 0.5)}

mm = (np.arange(N) + 0.5) / K - R
X, Y = np.meshgrid(mm, -mm)


def leaf_width(h, u):
    L, wmax, tail, neck, peak = h["L"], h["wmax"], h["tail"], h["neck"], h["peak"]
    tail_w = neck * (0.55 + 0.45 * (1 + np.clip(u, -tail, 0) / tail))
    t = np.clip(u / L, 0, 1)
    rise = np.maximum(neck, wmax * np.maximum(0, np.sin(0.5 * np.pi * np.minimum(t, peak) / peak)) ** 1.2)
    fall = wmax * np.maximum(0, (1 - t) / (1 - peak)) ** 0.85
    w = np.where(u < 0, tail_w, np.where(t < peak, rise, fall))
    return np.where((u < -tail) | (u > L), 0, w)


def hand_mask(variant, names, grow=CORE):
    GROW = grow
    m = np.zeros(X.shape, bool)
    for k in names:
        h = HANDS[k]
        cx, cy = PIV[h["p"]]
        a = math.radians(POSES[variant][k])
        u = (X - cx) * math.cos(a) + (Y - cy) * math.sin(a)
        v = -(X - cx) * math.sin(a) + (Y - cy) * math.cos(a)
        w = leaf_width(h, u)
        m |= (w > 0) & (np.abs(v) < w / 2 + GROW)
        m |= np.hypot(X - cx, Y - cy) < h["hub"] + max(GROW, 0.45)   # the photographed caps are larger
        m |= (u > -h["tail"] - GROW) & (u < h["L"] + GROW) & (np.abs(v) < h["neck"] / 2 + GROW)   # the tips
    return m


def print_map(L, dark_ink):
    """Print coverage 0..1 and the ground under it: thin print removed by a grey closing (dark ink on
    white) or opening (light ink on slate) about 0.45 mm across, then smoothed."""
    s = int(0.45 * K) | 1
    ground = ndimage.minimum_filter(ndimage.maximum_filter(L, s), s) if dark_ink else \
        ndimage.maximum_filter(ndimage.minimum_filter(L, s), s)
    ground = ndimage.uniform_filter(ground, s)
    if dark_ink:
        t = (ground - L) / np.maximum(ground - 40.0, 1.0)
    else:
        t = (L - ground) / np.maximum(232.0 - ground, 1.0)
    return np.clip(t, 0, 1), ground


def fill_from_round(img, mask, ok, sigmas=(0.3, 0.6, 1.2, 2.4), d=8):
    """Each masked pixel takes the average of the ok pixels round it, widening until there are some.
    The ground is smooth, so this is worked out at 1/d of the size and scaled back up."""
    n = N // d
    small = lambda a: a.reshape(n, d, n, d, *a.shape[2:]).mean((1, 3))
    oks = small(ok.astype(np.float32))
    imgs = small(img * ok[..., None])
    fill = np.zeros((n, n, img.shape[2]), np.float32)
    done = np.zeros((n, n), bool)
    for s in sigmas:
        w = ndimage.gaussian_filter(oks, s * K / d)
        f = np.stack([ndimage.gaussian_filter(imgs[..., c], s * K / d) for c in range(img.shape[2])], -1) / np.maximum(w, 1e-6)[..., None]
        take = ~done & (w > 0.03)
        fill[take] = f[take]
        done |= take
    big = np.stack([ndimage.zoom(fill[..., c], d, order=1) for c in range(img.shape[2])], -1)
    return np.where(mask[..., None], big, img)


def align(src, dst, avoid, d=2, half=1.0, search=0.5):
    """Affine (3x3, in dial mm) taking src's print onto dst's, from patch matches on a grid."""
    s_, t_, av = src[::d, ::d], dst[::d, ::d], ndimage.binary_dilation(avoid[::d, ::d], iterations=int(0.3 * K / d))
    kk = K / d
    hp, sp = int(half * kk), int(search * kk)
    pts, shifts = [], []
    for cy in np.arange(-13.0, 13.1, 1.6):
        for cx in np.arange(-13.0, 13.1, 1.6):
            if math.hypot(cx, cy) > 13.6:
                continue
            i, j = int((R - cy) * kk), int((cx + R) * kk)
            tpl = s_[i - hp:i + hp, j - hp:j + hp]
            if av[i - hp:i + hp, j - hp:j + hp].any() or tpl.mean() < 0.04 or tpl.std() < 0.12:
                continue
            win = t_[i - hp - sp:i + hp + sp, j - hp - sp:j + hp + sp]
            if av[i - hp - sp:i + hp + sp, j - hp - sp:j + hp + sp].mean() > 0.02:
                continue
            r = match_template(win, tpl)
            pi, pj = np.unravel_index(np.argmax(r), r.shape)
            if r[pi, pj] < 0.6:
                continue
            di, dj = (pi - sp) / kk, (pj - sp) / kk          # mm (rows go down: -y)
            pts.append((cx, cy)); shifts.append((dj, -di))
    pts, shifts = np.array(pts), np.array(shifts)
    # least squares, then again without the worst quarter
    for _ in range(2):
        M = np.c_[pts, np.ones(len(pts))]
        cxy = np.linalg.lstsq(M, pts + shifts, rcond=None)[0]
        res = np.hypot(*(M @ cxy - pts - shifts).T)
        keep = res <= np.quantile(res, 0.75) if _ == 0 else np.ones(len(res), bool)
        pts, shifts = pts[keep], shifts[keep]
    print(f"aligned on {len(pts)} patches: mean shift {np.hypot(*shifts.T).mean():.3f} mm, "
          f"residual {res[keep].mean() if len(res) == len(keep) else res.mean():.3f} mm")
    A = np.eye(3)
    A[:2, :] = cxy.T
    return A


def warp(img, A):
    """img (dial texture) moved by the affine A (dial mm -> dial mm): out(p) = img(A^-1 p)."""
    Ai = np.linalg.inv(A)
    sx, sy = Ai[0, 0] * X + Ai[0, 1] * Y + Ai[0, 2], Ai[1, 0] * X + Ai[1, 1] * Y + Ai[1, 2]
    return ndimage.map_coordinates(img, [(R - sy) * K - 0.5, (sx + R) * K - 0.5], order=1, mode="nearest")


def main():
    col = {v: np.asarray(Image.open(os.path.join(TEX, f"dial_{v}_photo_color.jpg")).convert("RGB")).astype(np.float32) for v in POSES}
    orm = {v: np.asarray(Image.open(os.path.join(TEX, f"dial_{v}_photo_orm.png")).convert("RGB")).astype(np.float32) for v in POSES}
    dark = {"5057R": True, "5057G": False}
    t, ground = {}, {}
    for v in POSES:
        t[v], ground[v] = print_map(col[v].mean(2), dark[v])
    # line the two prints up: many small patches of print (numerals, scales, lettering), each matched
    # within half a millimetre, then an affine fitted to them (the two photos were registered separately)
    every = hand_mask("5057G", POSES["5057G"].keys(), ZONE) | hand_mask("5057R", POSES["5057R"].keys(), ZONE)
    A = align(t["5057G"], t["5057R"], every)
    onto = {"5057R": A, "5057G": np.linalg.inv(A)}           # the other dial onto this one
    other = {"5057R": "5057G", "5057G": "5057R"}
    t_on = {v: warp(t[other[v]], onto[v]) for v in POSES}
    # what is the hand: inside its own outline, everything; round it (ZONE), what is off the ground and
    # is not print, print being what the other dial has there (or, where its hands were too, what looks
    # like print). The photographed hands' dark edges look like the 5057R's black print, so the other
    # dial is the better judge.
    core = {v: hand_mask(v, MARKED[v]) for v in POSES}
    masks, tone = {}, {}
    for v in POSES:
        L = col[v].mean(2)
        # the dial's own tone, from the dial alone (away from every hand, no print), smoothed: the white
        # hand bodies are as light as the grey closing makes the ground, but lighter than this
        zone = hand_mask(v, MARKED[v], ZONE)
        bare = ~ndimage.binary_dilation(zone, iterations=int(0.2 * K)) & (t[v] < 0.05)
        tone[v] = fill_from_round(L[..., None], np.ones(L.shape, bool), bare, sigmas=(0.6, 1.2, 2.4, 4.8))[..., 0]
        off = np.abs(L - tone[v]) > OFF[v]
        ref_ok = warp(core[other[v]].astype(np.float32), onto[v]) < 0.5
        is_print = np.where(ref_ok, ndimage.maximum_filter(t_on[v], 5) > 0.25, PRINTLIKE[v](L, t[v]))
        masks[v] = ndimage.binary_dilation(core[v] | (zone & off & ~is_print), iterations=3)
    other_bad = {v: warp(masks[other[v]].astype(np.float32), onto[v]) > 0.5 for v in POSES}
    centre = np.hypot(X, Y) < 1.9           # no print by the centre (the sunburst's rays are not print)
    for v in POSES:
        m = masks[v]
        img = col[v]
        # this dial's ground, filled in from round the hands (print left out), and its ink colour
        # ground: no print, and none of the photo's glints off the hands (brighter than the ground)
        plain = ~m & (t[v] < 0.08) & (np.abs(img.mean(2) - tone[v]) < OFF[v])
        g = fill_from_round(img, m, plain)
        inkpx = ~m & (t[v] > 0.85)
        ink = np.median(img[inkpx], axis=0)
        # the print under the hands: the other dial's, where its own hands did not cover it
        tt = np.where(other_bad[v] | centre, 0.0, t_on[v])
        new = g * (1 - tt[..., None]) + ink * tt[..., None]
        soft = ndimage.gaussian_filter(m.astype(np.float32), 1.5)[..., None]
        out = img * (1 - soft) + new * soft
        Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(TEX, f"dial_{v}_clean_color.jpg"), quality=93)
        # ORM likewise: the ground's from round about, the print's where there is print
        o = orm[v]
        og = fill_from_round(o, m, plain)
        oink = np.median(o[inkpx], axis=0)
        onew = og * (1 - tt[..., None]) + oink * tt[..., None]
        oout = o * (1 - soft) + onew * soft
        Image.fromarray(np.clip(oout, 0, 255).astype(np.uint8)).save(os.path.join(TEX, f"dial_{v}_clean_orm.png"))
        both = m & other_bad[v]
        print(f"{v}: {m.sum() / K ** 2:.1f} mm² cleaned, {both.sum() / K ** 2:.1f} mm² of it under both watches' hands (ground only)")
        if SCR:
            Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((1200, 1200), Image.LANCZOS).save(os.path.join(SCR, f"dial_clean_{v}.jpg"))


if __name__ == "__main__":
    main()
