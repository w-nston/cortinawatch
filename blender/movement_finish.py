# Real finishing for the 5057G's calibre 240, as material maps (glTF-friendly: plain textures).
#
#   movement_finish_{color.jpg, orm.png, normal.png}   over the movement (same planar mapping as
#       the photo: photo-view mm, half-size 14.06): rhodium bridges with Côtes de Genève (straight
#       bands 2.6 mm wide, each a shallow cylinder, as measured on the photo: under its light every
#       band runs bright to dark, a sawtooth, and the band edges line up across all the bridges, at
#       photo-view x = 2.0 + 2.6 k), with the grinding wheel's fine hairlines; baseplate and
#       sinkings with perlage (overlapping spots of circular graining), and the gilt engravings
#       lifted from the caseback photo (lettering, PP seal, regulator marks, "240"), recessed and
#       gold-filled.
#   circular_graining_normal.png   concentric graining for the gold train wheels (wheel-local UV)
#   snailing_normal.png            spiral snailing for the steel ratchet and crown wheels
#
# Needs blender/movement.json (bridges) and textures/movement_5057G_color.jpg (for the gilt mask);
# run after movement_from_photo.py.  python3 blender/movement_finish.py
import json, math, os, numpy as np
from PIL import Image
from scipy import ndimage
from matplotlib.path import Path

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "textures")
data = json.load(open(os.path.join(HERE, "movement.json")))
R = data["texture_half_size"]
N = 2048
K = N / (2 * R)
mm = (np.arange(N) + 0.5) / K - R
X, Y = np.meshgrid(mm, -mm)


def normal_from_height(h, strength):
    gx = ndimage.sobel(h, 1) / 8 * K
    gy = ndimage.sobel(h, 0) / 8 * K
    n = np.stack([-gx * strength, gy * strength, np.ones_like(h)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def to_png(n):   # dithered: smooth slopes (Côtes) would band in mirror-like reflections
    d = np.random.default_rng(5057).uniform(-0.5, 0.5, n.shape)
    return Image.fromarray(np.clip(np.round((n * 0.5 + 0.5) * 255 + d), 0, 255).astype(np.uint8))


# ---- regions
pts = np.c_[X.ravel(), Y.ravel()]
bridge = np.zeros(X.shape, bool)
for outline in data["bridges"].values():
    bridge |= Path(outline).contains_points(pts).reshape(X.shape)

photo = np.asarray(Image.open(os.path.join(TEX, "movement_5057G_color.jpg")).convert("RGB")).astype(np.float32)
r, g, b = photo[..., 0], photo[..., 1], photo[..., 2]
sat = (photo.max(2) - photo.min(2)) / (photo.max(2) + 1)
gold = (r > g + 12) & (g > b + 12) & (sat > 0.16)
gilt = gold & ndimage.binary_erosion(bridge, iterations=4)
lab, n = ndimage.label(gilt)
sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)) / K ** 2
keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if 0.004 < s < 4.0])  # lettering and seals, not wheels
gilt = ndimage.binary_closing(keep, iterations=1)
# not engravings: the photo's gold chatons and the balance seen past the cock's head and the pallet bridge
for cx_, cy_, r_, _ in data.get("chatons", []):
    gilt &= np.hypot(X - cx_, Y - cy_) > r_ + 0.25
bx_, by_ = data["chatons"][-1][:2] if data.get("chatons") else (0.52, -9.38)
gilt &= np.hypot(X - bx_, Y - by_) > 2.05
if "pallet_bridge" in data["bridges"]:
    gilt &= ~Path(data["bridges"]["pallet_bridge"]).contains_points(pts).reshape(X.shape)
print(f"gilt engravings: {gilt.sum() / K ** 2:.1f} mm² in {len([s for s in sizes if 0.004 < s < 4.0])} marks")

# ---- Côtes de Genève on the bridges: straight bands across x, each a shallow cylinder
W_BAND, X0_BAND = 2.6, 2.0
u = (X - X0_BAND) / W_BAND
f = u - np.floor(u)
cotes = 1 - (2 * f - 1) ** 2                          # cylinder: the slope runs evenly across the band
# the grinding wheel's hairlines: fine streaks at -50° (as in the photo), from directional noise
rng = np.random.default_rng(240)
ang = math.radians(-50)
hl_u = X * math.cos(ang) + Y * math.sin(ang)          # along the streaks
hl_v = -X * math.sin(ang) + Y * math.cos(ang)         # across them
hair = np.zeros(X.shape, np.float32)
for k, (freq, amp) in enumerate(((14.0, 1.0), (23.0, 0.5), (9.0, 0.45))):   # lines per mm
    ph = rng.uniform(0, 2 * np.pi, 64)
    seg = np.floor(hl_u / 0.9).astype(int) % 64      # streaks break every ~0.9 mm along their length
    hair += amp * np.sin(hl_v * freq * 2 * np.pi + ph[seg] + 3.1 * np.sin(hl_u * 1.7 + k))
hair /= 1.95

# ---- perlage on the plate: overlapping spots, each finely grained in rings
perl = np.zeros(X.shape, np.float32)
S, RS = 0.46, 0.36                                    # spacing and spot radius (mm)
rows = np.arange(-R, R + S, S)
for j, yc in enumerate(rows[::-1]):                   # later spots overlap earlier ones
    off = (j % 2) * S / 2
    for xc in np.arange(-R - off, R + S, S):
        i0, i1 = int((R - yc - RS) * K), int((R - yc + RS) * K) + 1
        j0, j1 = int((xc - RS + R) * K), int((xc + RS + R) * K) + 1
        i0, j0 = max(i0, 0), max(j0, 0)
        if i0 >= N or j0 >= N or i1 <= 0 or j1 <= 0:
            continue
        xs, ys = X[i0:i1, j0:j1], Y[i0:i1, j0:j1]
        rr = np.hypot(xs - xc, ys - yc)
        m = rr < RS
        spot = 0.6 + 0.35 * np.cos(rr / 0.075 * 2 * np.pi) - 0.45 * (rr / RS) ** 2
        perl[i0:i1, j0:j1][m] = spot[m]

# ---- height, colour, roughness/metal
h = np.where(bridge, cotes * 4.5 + hair * 0.05, perl * 0.55)   # Côtes: ±5° across each band, subtle as photographed
h = np.where(gilt, h - 0.9, h)                         # engraved
h = ndimage.gaussian_filter(h, 0.9)
nrm = normal_from_height(h, 0.012)
col = np.zeros(X.shape + (3,), np.float32)
col[:] = (212, 214, 217)                               # rhodium-plated plate
col[bridge] = (226, 228, 231)                          # rhodium-plated bridges
col[gilt] = (206, 152, 82)                             # gold-filled engravings
rough = np.where(bridge, 0.2 + 0.04 * hair, 0.34)
rough = np.where(gilt, 0.45, rough)
orm = np.zeros(X.shape + (3,), np.uint8)
orm[..., 0] = 255
orm[..., 1] = (rough * 255).astype(np.uint8)
orm[..., 2] = 255
Image.fromarray(col.astype(np.uint8)).save(os.path.join(TEX, "movement_finish_color.jpg"), quality=92)
Image.fromarray(orm).save(os.path.join(TEX, "movement_finish_orm.png"))
to_png(nrm).save(os.path.join(TEX, "movement_finish_normal.png"))

# ---- wheel finishes (1024², UV square = the wheel's diameter)
n2 = 1024
v = (np.arange(n2) + 0.5) / n2 * 2 - 1
U, V = np.meshgrid(v, -v)
rho, th = np.hypot(U, V), np.arctan2(V, U)
ring = 0.5 + 0.5 * np.cos(rho * 2 * np.pi * 110)       # concentric graining
to_png(normal_from_height(ndimage.gaussian_filter(ring, 0.6), 0.0009 * N / n2)).save(os.path.join(TEX, "circular_graining_normal.png"))
snail = 0.5 + 0.5 * np.cos((rho * 60 + th / (2 * np.pi) * 6) * 2 * np.pi)   # six-start spiral
to_png(normal_from_height(ndimage.gaussian_filter(snail, 0.6), 0.0012 * N / n2)).save(os.path.join(TEX, "snailing_normal.png"))
print("wrote movement_finish_*, circular_graining_normal.png, snailing_normal.png")
