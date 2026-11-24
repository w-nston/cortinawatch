# Generates the alligator-scale maps for the strap (run with system python: numpy + Pillow).
#   croc_normal.png  tangent-space normal map
#   croc_orm.png     G = roughness (glossy scales, duller grooves), B = metalness (0)
# U runs across the strap (0..1 = full width), V along it (1 unit = 40 mm, tiles).
import numpy as np, os
from PIL import Image

W, H = 1024, 2048
rng = np.random.default_rng(5057)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")

# columns across the strap: small scales at the edges, large rectangular ones in the middle
cols = np.array([0.1, 0.13, 0.17, 0.2, 0.17, 0.13, 0.1])
cols = cols / cols.sum()
row_len = np.array([0.055, 0.07, 0.095, 0.115, 0.095, 0.07, 0.055])  # in V units (×40 mm)

u = (np.arange(W) + 0.5) / W
v = (np.arange(H) + 0.5) / H
height = np.zeros((H, W), np.float32)
edges_u = np.concatenate([[0], np.cumsum(cols)])
for c in range(len(cols)):
    u0, u1 = edges_u[c], edges_u[c + 1]
    xs = np.where((u >= u0) & (u < u1))[0]
    # rows of slightly varying length, wrapping in V
    bounds = [0.0]
    while bounds[-1] < 1.0:
        bounds.append(bounds[-1] + row_len[c] * rng.uniform(0.75, 1.25))
    bounds = np.array(bounds) * (1.0 / bounds[-1])  # make the column tile exactly
    off = rng.uniform(0, 1)
    vv = (v + off) % 1.0
    ri = np.searchsorted(bounds, vv, side="right") - 1
    v0, v1 = bounds[ri], bounds[ri + 1]
    fv = (vv - v0) / (v1 - v0)
    fu = (u[xs] - u0) / (u1 - u0)
    # per-scale jitter of the groove lines makes the grid look organic
    jit = rng.uniform(-0.08, 0.08, size=len(bounds))
    fvj = np.clip(fv[:, None] + jit[ri][:, None] * (fu[None, :] - 0.5), 0, 1)  # slightly slanted grooves
    du = np.minimum(fu, 1 - fu)[None, :] * (u1 - u0) * 20       # mm to the side groove (strap ~20 mm)
    dv = np.minimum(fvj, 1 - fvj) * (v1 - v0)[:, None] * 40      # mm to the row groove
    d = np.minimum(du, dv)
    dome = np.clip(d / 0.55, 0, 1) ** 0.5                        # rounded scale, sharp groove
    bulge = (1 - ((fu[None, :] - 0.5) * 2) ** 2) * (1 - ((fvj - 0.5) * 2) ** 2)
    height[:, xs] = dome * (0.75 + 0.25 * bulge) + rng.uniform(-0.03, 0.03, size=(H, len(xs))) * dome

# fine pore noise
noise = rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
noise = np.array(Image.fromarray(noise).resize((W, H), Image.BICUBIC))
height += noise * 0.015

# normal from height (tileable gradients)
strength = 6.0
dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * strength
dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * strength
n = np.stack([-dx, dy, np.ones_like(height)], -1)
n /= np.linalg.norm(n, axis=-1, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).save(os.path.join(OUT, "croc_normal.png"))

rough = 0.42 - 0.22 * np.clip(height, 0, 1)                      # grooves 0.42, scale tops 0.2
orm = np.zeros((H, W, 3), np.uint8)
orm[..., 0] = 255
orm[..., 1] = (rough * 255).astype(np.uint8)
Image.fromarray(orm).save(os.path.join(OUT, "croc_orm.png"))
print("ok", height.min(), height.max())
