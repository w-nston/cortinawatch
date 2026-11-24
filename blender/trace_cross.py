# Traces the Calatrava cross of the 5057G's folding clasp from the close-up photograph
# ("watch photos/5057G/clasp-closeup.webp") and writes blender/calatrava_cross.json:
# one closed outline, arms along ±X/±Y, scaled so the arm tips (where they join the frame)
# sit on radius 1.
#
#   1. the cross is segmented inside the frame's opening (polished grey against the black
#      opening; the red reflections on the frame's inner wall are excluded)
#   2. it is turned so its arms lie on the axes (best mirror symmetry), then averaged over its
#      eight symmetries (four turns × mirror), which removes the photo's slight perspective
#   3. the 0.5 contour of the symmetric mask is simplified to a polygon
#
# Run with system python (numpy, scipy, scikit-image, Pillow):  python3 blender/trace_cross.py
import json, os, numpy as np
from PIL import Image
from scipy import ndimage
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "watch photos", "5057G", "clasp-closeup.webp")
OUT = os.path.join(HERE, "calatrava_cross.json")
SCR = os.environ.get("SCRATCH")

im = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
L = im.mean(2)
sat = im.max(2) - im.min(2)
CX, CY, R_OPEN = 1148.0, 460.0, 292.0   # opening centre and radius in the photo (px)

yy, xx = np.mgrid[: im.shape[0], : im.shape[1]]
rr = np.hypot(xx - CX, yy - CY)
m = (L > 115) & (sat < 45) & (rr < R_OPEN - 4)
m = ndimage.binary_opening(m, iterations=2)
m = ndimage.binary_closing(m, iterations=2)
lab, n = ndimage.label(m)
m = lab == lab[int(CY), int(CX)] if lab[int(CY), int(CX)] else lab == np.argmax(ndimage.sum(m, lab, range(1, n + 1))) + 1
m = ndimage.binary_fill_holes(m)

# centre the cross on its own centroid, in a square working frame
cy, cx = ndimage.center_of_mass(m)
H = int(R_OPEN * 1.1)
crop = m[int(cy) - H: int(cy) + H, int(cx) - H: int(cx) + H].astype(np.float32)


def rot(a, deg):
    return ndimage.rotate(a, deg, reshape=False, order=1)


# arms onto the axes: the angle whose mirror image matches best
best = None
for deg in np.arange(-45, 45, 0.25):
    r = rot(crop, deg)
    s = np.sum(r * r[:, ::-1]) + np.sum(r * r[::-1, :])
    if best is None or s > best[0]:
        best = (s, deg)
r = rot(crop, best[1])
# of the two mirror-axis families (arms, diagonals), the arms are the one with solid stems
c = r.shape[0] // 2
stem_axes = r[c, c + 20: c + 120].mean() + r[c + 20: c + 120, c].mean()
d = np.arange(20, 120)
stem_diag = r[c + d, c + d].mean() + r[c - d, c + d].mean()
if stem_diag > stem_axes:
    r = rot(r, 45)
sym = np.zeros_like(r)
for k in range(4):
    q = np.rot90(r, k)
    sym += q + q[:, ::-1]
sym /= 8
sym = ndimage.gaussian_filter(sym, 1.2)

cont = max(measure.find_contours(sym, 0.5), key=len)
poly = measure.approximate_polygon(cont, tolerance=0.6)
pts = np.c_[poly[:, 1] - c, c - poly[:, 0]]          # x right, y up, centred
tip = np.hypot(pts[:, 0], pts[:, 1]).max()
pts /= tip
json.dump({"source": "watch photos/5057G/clasp-closeup.webp",
           "note": "Calatrava cross outline, arms on ±X/±Y, arm tips on radius 1",
           "tip_over_opening": float(tip / R_OPEN),
           "outline": [[round(float(x), 5), round(float(y), 5)] for x, y in pts]}, open(OUT, "w"))
print(f"angle {best[1]:.2f}°, {len(pts)} points, tip {tip:.1f}px = {tip / R_OPEN:.3f} × opening")

if SCR:
    from PIL import ImageDraw
    v = Image.fromarray((np.clip(sym, 0, 1) * 255).astype(np.uint8)).convert("RGB")
    dr = ImageDraw.Draw(v)
    dr.line([tuple((p[0] * tip + c, c - p[1] * tip)) for p in pts] + [(pts[0][0] * tip + c, c - pts[0][1] * tip)], fill=(255, 0, 0), width=2)
    v.save(os.path.join(SCR, "cross_traced.png"))
    Image.fromarray((m * 255).astype(np.uint8)).crop((int(CX - H), int(CY - H), int(CX + H), int(CY + H))).save(os.path.join(SCR, "cross_mask.png"))
