# The 5057R's movement engravings lifted from a sharp photograph of a 1990s calibre 240 (the same older
# engraving as the 5057R's): "watch photos/5057r/best movement photo.jpg", 1626 x 2033 px, ~53 px/mm on
# the movement. PATEK PHILIPPE / GENEVE SWISS, TWENTY-NINE / JEWELS, 240/164 and the Geneva Seal are
# the photo's own gold-filled strokes, so the letterforms are the engraver's.
#
# Registered to the movement's photo-view frame by a homography fitted to seven pivots and jewels
# (rotor pivot, balance jewel, barrel bushing, four jewels on the barrel and train bridges; residuals
# <= 0.09 mm). Only the barrel and train bridges carry engraving. The photo's serial is partly covered by
# a red box: its visible "3165" is kept and the hidden digits are completed with the photo's own "164"
# glyphs from the 240/164 line beside it, scaled to the serial's smaller size (3165164, a placeholder,
# not the watch's number), so the line stays in the engraver's lettering.
# The Geneva Seal is also the photo's own pixels (its relief shows), in engravings_5057R_seal.png. This
# photo's movement has it low on the left of the barrel bridge, but the Cortina Jubilee 5057R itself
# (45723_ext4_3377.jpg) has it just past the P of PATEK, by the rim, clear of the caseback's print, so
# the photographed seal is carried round the lettering's arc to there.
#   python3 blender/engravings_5057r_photo.py  ->  textures/engravings_5057R.png, engravings_5057R_seal.png
# then VARIANT=5057R python3 blender/movement_finish.py
import json, math, os, numpy as np
from PIL import Image
from scipy import ndimage
from matplotlib.path import Path

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "textures")
SCR = os.environ.get("SCRATCH")
PHOTO = os.path.join(HERE, "..", "watch photos", "5057r", "best movement photo.jpg")
R, N = 14.06, 2048
K = N / (2 * R)
P_PX = np.array([(1020, 1223), (420, 1350), (773, 597), (1100, 630), (593, 863), (300, 1090), (277, 959)], float)
P_MM = np.array([(6.47, 0.06), (0.52, -9.38), (-5.77, 5.14), (-1.11, 8.83), (-4.28, -0.75), (-4.79, -7.63), (-7.14, -6.06)])
# the serial and 240/164 lines, in a frame along them: origin, angle (deg), measured on the registered photo
LINE = dict(origin=(-7.8, -8.4), angle=-47.8)
# "164" of 240/164 (glyph centres u, line centre v) -> the three hidden serial places after "3165"
COPY_164 = dict(src_u=(0.42, 1.11, 1.83), src_v=-0.33, dst_u=(0.22, 0.80, 1.38), dst_v=0.68,
                scale=0.70, half_u=0.34, half_v=0.5)
# the seal: where it is in this photo, where the 5057R has it, and the centre of the PATEK PHILIPPE arc
SEAL = dict(src=(-11.3, -2.7), r=0.6, dst=(-2.03, 11.25), arc_centre=(8.19, -7.05))


def homography(src, dst):
    rows = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        rows.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, _, vt = np.linalg.svd(np.array(rows))
    return vt[-1].reshape(3, 3) / vt[-1][-1]


def main():
    H = homography(P_PX, P_MM)                     # photo px -> movement mm
    Hi = np.linalg.inv(H)
    mm = (np.arange(N) + 0.5) / K - R
    X, Y = np.meshgrid(mm, -mm)
    w = Hi[2, 0] * X + Hi[2, 1] * Y + Hi[2, 2]
    px, py = (Hi[0, 0] * X + Hi[0, 1] * Y + Hi[0, 2]) / w, (Hi[1, 0] * X + Hi[1, 1] * Y + Hi[1, 2]) / w
    src = np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float32)
    c = np.stack([ndimage.map_coordinates(src[..., k], [py, px], order=3, mode="constant") for k in range(3)], -1)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    # the gold fill: warm against the grey rhodium; not the red redaction box
    gold = (r - b > 55) & (r > 110) & (g > b + 20) & (r - g < 95)
    red = ndimage.binary_dilation((r > 170) & (r - g > 110) & (r - b > 110), iterations=int(0.25 * K))
    data = json.load(open(os.path.join(HERE, "movement.json")))
    pts = np.c_[X.ravel(), Y.ravel()]
    bridge = np.zeros(X.shape, bool)
    for name in ("bridge_train", "bridge_wheels"):          # barrel bridge 105 and train bridge 110
        bridge |= Path(data["bridges"][name]).contains_points(pts).reshape(X.shape)
    inside = ndimage.binary_erosion(bridge, iterations=5) & ~red & (np.hypot(X, Y) < 12.6)
    # letters in shadow (the end of SWISS, the serial's 3 and 1) are a duller gold: grow the strokes
    # from the bright gold into connected, weaker gold
    for cx_, cy_, r_, _ in data.get("chatons", []):          # not the jewels' gold-toned rims
        inside &= np.hypot(X - cx_, Y - cy_) > r_ + 0.3
    weak = (r - b > 42) & (g > b + 15) & (r > 90) & inside
    gilt = ndimage.binary_propagation(gold & inside, mask=weak)
    # keep strokes and seals, drop specks and anything large (a wheel seen past an edge)
    lab, n = ndimage.label(gilt)
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)) / K ** 2
    gilt = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if 0.003 < s < 2.5])
    gilt = ndimage.gaussian_filter(gilt.astype(np.float32), 0.9) > 0.42      # smooth the 53 px/mm edges
    # only whole words and the seal: drop specks (jewel rims, a wheel's edge) away from any lettering
    words, n = ndimage.label(ndimage.binary_dilation(gilt, iterations=int(0.3 * K)))
    area = ndimage.sum(gilt, words, range(1, n + 1)) / K ** 2
    gilt &= np.isin(words, [i + 1 for i, s in enumerate(area) if s > 0.3])
    # the serial's hidden digits: "164" from 240/164, each glyph scaled to the serial's size
    ca, sa = math.cos(math.radians(LINE["angle"])), math.sin(math.radians(LINE["angle"]))
    ox, oy = LINE["origin"]
    u = (X - ox) * ca + (Y - oy) * sa
    v = -(X - ox) * sa + (Y - oy) * ca
    src_f = gilt.astype(np.float32)
    cp = COPY_164
    for su, du in zip(cp["src_u"], cp["dst_u"]):
        win = (np.abs(u - du) < cp["half_u"] * cp["scale"]) & (np.abs(v - cp["dst_v"]) < cp["half_v"] * cp["scale"])
        us = su + (u[win] - du) / cp["scale"]
        vs = cp["src_v"] + (v[win] - cp["dst_v"]) / cp["scale"]
        xs, ys = ox + us * ca - vs * sa, oy + us * sa + vs * ca
        val = ndimage.map_coordinates(src_f, [(R - ys) * K - 0.5, (xs + R) * K - 0.5], order=1)
        gilt[win] |= val > 0.5
    # the Geneva Seal as photographed, carried round the arc (a rotation about its centre, then a step
    # out to the 5057R's radius), with its own colour and relief and a soft edge
    sx, sy = SEAL["src"]
    seal_m = ndimage.binary_dilation(gilt & (np.hypot(X - sx, Y - sy) < SEAL["r"]), iterations=2)
    gilt &= ~seal_m
    acx, acy = SEAL["arc_centre"]
    th_s, th_d = math.atan2(sy - acy, sx - acx), math.atan2(SEAL["dst"][1] - acy, SEAL["dst"][0] - acx)
    r_s, r_d = math.hypot(sx - acx, sy - acy), math.hypot(SEAL["dst"][0] - acx, SEAL["dst"][1] - acy)
    dth = th_s - th_d                                         # destination -> source
    rr, tt = np.hypot(X - acx, Y - acy), np.arctan2(Y - acy, X - acx)
    win = np.hypot(X - SEAL["dst"][0], Y - SEAL["dst"][1]) < SEAL["r"] + 0.2
    xs = acx + (rr[win] - r_d + r_s) * np.cos(tt[win] + dth)
    ys = acy + (rr[win] - r_d + r_s) * np.sin(tt[win] + dth)
    ij = [(R - ys) * K - 0.5, (xs + R) * K - 0.5]
    alpha = np.zeros(X.shape, np.float32)
    alpha[win] = ndimage.map_coordinates(ndimage.gaussian_filter(seal_m.astype(np.float32), 1.0), ij, order=1)
    rgba = np.zeros(X.shape + (4,), np.float32)
    for k in range(3):
        rgba[..., k][win] = ndimage.map_coordinates(c[..., k], ij, order=3)
    rgba[..., 3] = alpha * 255
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8)).save(os.path.join(TEX, "engravings_5057R_seal.png"))
    gilt |= alpha > 0.5
    Image.fromarray((gilt * 255).astype(np.uint8)).save(os.path.join(TEX, "engravings_5057R.png"))
    if SCR:
        Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).save(os.path.join(SCR, "best_warp.png"))
    print(f"wrote engravings_5057R.png: {gilt.sum() / K ** 2:.1f} mm² of gilt engraving")


if __name__ == "__main__":
    main()
