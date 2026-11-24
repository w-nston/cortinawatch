# Patek Philippe Ref. 5057G-010 "Cortina Watch 50th Anniversary", built in Blender.
#
# Run inside Blender (Scripting tab, or via the MCP):
#   exec(open("/path/to/cortinawatch/blender/build_5057.py").read())
#
# Units: millimetres (scene unit scale 0.001). Front coordinates match js/watch5057.js:
# +X toward the crown at 3, +Y toward 12, +Z out of the dial. z = 0 is the dial surface.
# Measured from the reference photos in "watch photos/5057G" (front: 16.2 px/mm,
# side profile: 30.2 px/mm) and the published specs: 36.15 mm diameter, 9.14 mm high.
#
# Everything is rebuilt into the "Watch5057G" collection each run. The dial is the real dial,
# photographed (blender/dial_from_photo.py), and the hands are posed exactly where they stand in
# that photograph (10:09, date 20, ~39 h of reserve), so the watch is shown static. Each hand is
# still its own object with its origin on its pivot (rotate about Z to move it):
#   hand_hour, hand_minute, hand_seconds, hand_date, hand_power
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

TAU = math.tau
DEG = math.pi / 180
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else None
ROOT = globals().get("CORTINA_ROOT") or (os.path.dirname(HERE) if HERE else None)
TEX = os.path.join(ROOT, "blender", "textures")
PHOTOS = os.path.join(ROOT, "watch photos", "5057G")

# ------------------------------------------------------------------ dimensions (mm)
Z_BACK = -6.9          # caseback bottom
Z_JOINT = -4.35        # caseback / case middle joint
Z_BEZEL = -0.4         # case middle / bezel joint
Z_CRYSTAL = 2.24       # crystal top (9.14 mm overall)
R_BEZEL = 18.075       # 36.15 mm
R_FLANK = 17.85
HOB = dict(r0=18.0, z0=-0.15, r1=15.05, z1=1.5, rows=4, n=88, h=0.34)
R_DIAL = 14.25
DIAL_TEX_R = 15.4      # the baked dial texture spans this radius (js DIAL_R)
# sub-dial pivots, fitted to the printed scales on the rectified photo (dial_from_photo.py)
PR = (-6.273, 6.279)   # power reserve (dot circle r 3.909)
DATE = (-3.529, -6.128)  # pointer date (dot circle r 4.804)
SECS = (7.369, -6.272)   # small seconds (tick ring r 3.38)
# hand angles as photographed (degrees from +X, counter-clockwise), corrected for parallax
POSE = dict(hour=143.6, minute=29.3, power=16.0, date=220.0, seconds=96.5)
CROWN_Z = -3.3
R_WIN = 13.4           # caseback window (measured on the caseback photo)
# movement levels (z; the bridge side faces the caseback, i.e. -Z)
Z_PLATE = -4.95        # baseplate surface
Z_SINK = -4.45         # floor of the sinkings cut into the baseplate round the wheels (0.5 mm deep)
Z_BRIDGE = -5.45       # bridge surfaces (0.5 mm proud of the plate)
Z_WHEEL = -5.14        # visible gold wheels
Z_PIT = 0.6            # the balance/escapement pit goes this much deeper than the sinkings
Z_ROTOR = -5.15        # mini-rotor underside: it turns in a pit in the bridges, its face (-5.45) flush with them
LUG_X = 11.0           # lug centre (20 mm between lugs)


# ------------------------------------------------------------------ helpers
def coll():
    name = "Watch5057G"
    c = bpy.data.collections.get(name)
    if c:
        for o in list(c.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for ch in list(c.children):
            bpy.data.collections.remove(ch)
        for me in list(bpy.data.meshes):  # drop the previous run's meshes so names stay clean
            if me.users == 0:
                bpy.data.meshes.remove(me)
    else:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def new_obj(name, me, mat=None, parent=None, smooth_angle=None, flat=False):
    o = bpy.data.objects.new(name, me)
    C.objects.link(o)
    if mat is not None:
        mats = mat if isinstance(mat, (list, tuple)) else [mat]
        for m in mats:
            me.materials.append(m)
    if flat:
        for p in me.polygons:
            p.use_smooth = False
    else:
        for p in me.polygons:
            p.use_smooth = True
        if smooth_angle is not None:
            me.set_sharp_from_angle(angle=smooth_angle)
    if parent:
        o.parent = parent
    return o


def bm_to_obj(bm, name, mat=None, **kw):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return new_obj(name, me, mat, **kw)


def lathe(profile, segs=256, name="lathe", mat=None, close=False, smooth_angle=35 * DEG, start=0.0, sweep=TAU):
    """Revolve [(r, z), ...] about Z. Points with r == 0 become poles."""
    bm = bmesh.new()
    full = abs(sweep - TAU) < 1e-6
    n = segs if full else segs + 1
    rings = []
    for (r, z) in profile:
        if r <= 1e-6:
            v = bm.verts.new((0, 0, z))
            rings.append([v] * n)
        else:
            rings.append([bm.verts.new((r * math.cos(start + sweep * i / segs), r * math.sin(start + sweep * i / segs), z)) for i in range(n)])
    pairs = list(zip(rings, rings[1:]))
    if close:
        pairs.append((rings[-1], rings[0]))
    for a, b in pairs:
        for i in range(segs):
            j = (i + 1) % n
            vs = [a[i], a[j], b[j], b[i]]
            uniq = []
            for v in vs:
                if v not in uniq:
                    uniq.append(v)
            if len(uniq) >= 3:
                try:
                    bm.faces.new(uniq)
                except ValueError:
                    pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_obj(bm, name, mat, smooth_angle=smooth_angle)


def mat(name, color, metal=0.0, rough=0.5, **kw):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    for k, v in kw.items():
        bsdf.inputs[k].default_value = v
    m.diffuse_color = (*color, 1)
    m.metallic = metal
    m.roughness = rough
    return m


def srgb(h):
    c = [((h >> s) & 255) / 255 for s in (16, 8, 0)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ------------------------------------------------------------------ materials
def materials():
    M = {}
    wg = srgb(0xE4E5E7)
    M["polish"] = mat("WG polished", wg, 1, 0.07)
    M["hob"] = mat("WG hobnail", wg, 1, 0.05)
    # no anisotropy: the lathed parts carry no UVs, and without a tangent direction three.js smears
    # an anisotropic highlight over the whole surface
    M["satin"] = mat("WG brushed", srgb(0xD6D7DA), 1, 0.3, **{"Anisotropic": 0.0})
    M["dark"] = mat("Rehaut grey", srgb(0x34363A), 0.7, 0.32)
    M["black"] = mat("Black", srgb(0x0A0A0C), 0.0, 0.6)
    M["hand"] = mat("Hands WG", srgb(0xF0F1F3), 1, 0.05)
    M["ruby"] = mat("Ruby", srgb(0xB02A55), 0, 0.05, **{"Coat Weight": 1.0})
    # sapphire as a thin transparent coat rather than transmission: crisp under it, and cheap in
    # three.js (no transmission pass re-rendering the movement and dial at lower quality)
    g = mat("Sapphire", (1, 1, 1), 0, 0.0, **{"Transmission Weight": 0.0, "IOR": 1.77, "Alpha": 0.1,
                                              "Specular IOR Level": 0.25})
    if hasattr(g, "surface_render_method"):
        g.surface_render_method = "BLENDED"
    M["glass"] = g
    return M


# ------------------------------------------------------------------ case
def build_case(M):
    # case middle: straight polished flank
    lathe([(15.2, Z_JOINT + 0.05), (17.55, Z_JOINT + 0.05), (17.78, Z_JOINT + 0.22), (R_FLANK, Z_JOINT + 0.55),
           (R_FLANK, Z_BEZEL - 0.12), (17.92, Z_BEZEL), (15.2, Z_BEZEL)], name="case_middle", mat=M["polish"], close=True)

    # bezel: thin polished edge, the hobnail cone, polished inner bevel down to the crystal
    H = HOB
    lathe([(15.3, Z_BEZEL), (R_BEZEL - 0.05, Z_BEZEL), (R_BEZEL, Z_BEZEL + 0.05), (R_BEZEL, H["z0"] - 0.03),
           (H["r0"], H["z0"]), (H["r1"], H["z1"]), (14.95, H["z1"] + 0.02), (14.5, 1.38), (14.45, 1.25), (14.45, 0.9),
           (15.3, 0.9)], name="bezel", mat=M["polish"], close=True, smooth_angle=25 * DEG)

    # hobnail pyramids ("clous de Paris") on the cone
    bm = bmesh.new()
    sr, sz = H["r1"] - H["r0"], H["z1"] - H["z0"]
    L = math.hypot(sr, sz)
    nr, nz = sz / L, -sr / L  # outward/up normal of the cone in (r, z)
    pt = lambda t: (H["r0"] + sr * t, H["z0"] + sz * t)
    for row in range(H["rows"]):
        t0, t1 = row / H["rows"], (row + 1) / H["rows"]
        (ra, za), (rb, zb), (rm, zm) = pt(t0), pt(t1), pt((t0 + t1) / 2)
        for j in range(H["n"]):
            a0, a1, am = TAU * j / H["n"], TAU * (j + 1) / H["n"], TAU * (j + 0.5) / H["n"]
            P = lambda r, z, a: bm.verts.new((r * math.cos(a), r * math.sin(a), z))
            v00, v01 = P(ra, za, a0), P(ra, za, a1)
            v10, v11 = P(rb, zb, a0), P(rb, zb, a1)
            ap = P(rm + nr * H["h"], zm + nz * H["h"], am)
            for f in ((v00, v01, ap), (v01, v11, ap), (v11, v10, ap), (v10, v00, ap)):
                bm.faces.new(f)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm_to_obj(bm, "bezel_hobnail", M["hob"], flat=True)

    # lugs: angular bars, side profile in (y, z), 1.9 mm wide
    prof = [(14.8, -0.55), (19.3, -0.75), (20.4, -1.15), (23.3, -3.55), (23.35, -4.35), (22.6, -4.9),
            (21.2, -4.95), (19.0, -4.75), (14.8, -4.75)]
    for sx in (1, -1):
        for sy in (1, -1):
            bm = bmesh.new()
            vs = []
            for x in (-0.95, 0.95):
                vs.append([bm.verts.new((LUG_X * sx + x, y * sy, z)) for (y, z) in prof])
            n = len(prof)
            bm.faces.new(vs[0][::-1] if sy > 0 else vs[0])
            bm.faces.new(vs[1] if sy > 0 else vs[1][::-1])
            for i in range(n):
                j = (i + 1) % n
                bm.faces.new((vs[0][i], vs[0][j], vs[1][j], vs[1][i]))
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            o = bm_to_obj(bm, f"lug_{'R' if sx > 0 else 'L'}{'12' if sy > 0 else '6'}", M["polish"], smooth_angle=30 * DEG)
            b = o.modifiers.new("bevel", "BEVEL")
            b.width, b.segments, b.limit_method = 0.22, 3, "ANGLE"
            b.harden_normals = True
    # spring bars
    for sy in (1, -1):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.45, radius2=0.45, depth=20.2,
                              matrix=Matrix.Translation((0, 21.6 * sy, -3.75)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
        bm_to_obj(bm, f"springbar_{'12' if sy > 0 else '6'}", M["satin"], smooth_angle=40 * DEG)

    # crown: 5.5 mm, sitting low across the case/back joint. As photographed from the side: a plain
    # polished dome (no engraving) on a short collar with a scalloped edge
    lobes = 16
    dome_r, dome_base, apex = 2.6, 1.4, 3.0
    R_d = (dome_r ** 2 + (apex - dome_base) ** 2) / (2 * (apex - dome_base))  # sphere through base rim and apex
    phi0 = math.asin(dome_r / R_d)
    dome = [(R_d * math.sin(phi0 * (1 - i / 14)), apex - R_d + R_d * math.cos(phi0 * (1 - i / 14))) for i in range(15)]
    prof = [(0, 0.0), (1.25, 0.0), (1.25, 0.4), (2.45, 0.45), (2.7, 0.62), (2.75, 0.85), (2.75, 1.22), (2.66, 1.36)] + dome
    prof[-1] = (0, apex)
    o = lathe(prof, segs=lobes * 16, name="crown", mat=M["polish"], smooth_angle=70 * DEG)
    for v in o.data.vertices:  # rounded scallops round the collar
        x, y, z = v.co
        r = math.hypot(x, y)
        if r > 2.6 and 0.55 < z < 1.3:
            a = math.atan2(y, x)
            d = 0.22 * (0.5 + 0.5 * math.cos(a * lobes))
            v.co.x, v.co.y = x / r * (r - d), y / r * (r - d)
    o.rotation_euler = (0, math.pi / 2, 0)
    o.location = (R_FLANK - 0.45, 0, CROWN_Z)

    # correctors (date / moon) at about 4 and 8 o'clock
    for a in (-35 * DEG, 215 * DEG):
        prof = [(0, 0.12), (0.45, 0.12), (0.52, 0.05), (0.6, 0.05), (0.62, -0.05), (0.85, -0.05), (0.95, 0.0), (1.0, -0.4), (0, -0.4)]
        o = lathe(prof, segs=48, name="corrector", mat=M["polish"], smooth_angle=40 * DEG)
        o.matrix_world = Matrix.Translation((R_FLANK * math.cos(a), R_FLANK * math.sin(a), CROWN_Z - 0.1)) @ \
            Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")

    # caseback: brushed ring with six opening notches, sapphire display window
    lathe([(17.6, Z_JOINT), (17.65, Z_JOINT - 0.5), (17.45, -5.55), (17.0, -6.3), (16.4, -6.78), (16.0, Z_BACK),
           (13.85, Z_BACK), (13.5, Z_BACK + 0.12), (13.4, Z_BACK + 0.3), (13.4, Z_JOINT), (17.6, Z_JOINT)],
          name="caseback", mat=M["satin"], close=True, smooth_angle=20 * DEG)
    # notches: shallow recessed slots (dark, polished floor) on the back ring
    bm = bmesh.new()
    for k in range(6):
        a = math.pi - (21 + 60 * k) * DEG  # measured on the back photo, mirrored to front coordinates
        m = Matrix.Translation((15.55 * math.cos(a), 15.55 * math.sin(a), Z_BACK + 0.06)) @ Matrix.Rotation(a, 4, "Z")
        bmesh.ops.create_cube(bm, size=1.0, matrix=m @ Matrix.Diagonal((1.25, 2.6, 0.14, 1)))
    bm_to_obj(bm, "caseback_notches", M["dark"], flat=True)


# ------------------------------------------------------------------ textures / textured materials
def image(name, colorspace="sRGB"):
    path = os.path.join(TEX, name)
    im = bpy.data.images.get(name)
    if im is None:
        im = bpy.data.images.load(path)
    else:
        im.reload()
    im.colorspace_settings.name = colorspace
    return im


def tex_mat(name, color_img, rough=0.5, metal=0.0, orm_img=None, emission=0.0, coat=0.0, coat_rough=0.05, aniso=0.0):
    """Principled material with an image colour map; ORM image: G = roughness, B = metalness
    (the layout the glTF exporter packs)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL"):
            nt.nodes.remove(n)
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = image(color_img)
    t.interpolation = "Cubic"
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if orm_img:
        o = nt.nodes.new("ShaderNodeTexImage")
        o.image = image(orm_img, "Non-Color")
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(o.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
    if emission:
        nt.links.new(t.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emission
    if coat:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = coat_rough
    if aniso:
        bsdf.inputs["Anisotropic"].default_value = aniso
    return m


def planar_uv(me, cx, cy, half, flip_u=False):
    uv = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        u = (co.x - cx) / (2 * half)
        uv.data[loop.index].uv = (0.5 - u if flip_u else 0.5 + u, 0.5 + (co.y - cy) / (2 * half))


def arc(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n)]


def _inside(pt, poly):
    x, y = pt
    c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def _dedupe(lp, eps=2e-3):
    out = []
    for p in lp:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > eps:
            out.append(p)
    while len(out) > 2 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


def flat_plate(outline, holes, z_top, thick, name, mats, uv=None):
    """Extruded plate from a 2D outline (with holes); top face material 0, sides/bottom material 1.
    Faces are oriented explicitly (caps by height, walls by which side is outside the outline),
    so traced outlines with near-duplicate points cannot leave it inside-out."""
    outline = _dedupe(outline)
    holes = [_dedupe(h) for h in holes]
    bm = bmesh.new()
    edges = []
    for lp in [outline] + holes:
        vs = [bm.verts.new((x, y, z_top)) for (x, y) in lp]
        edges += [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges, normal=(0, 0, 1))
    ex = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))
    bmesh.ops.translate(bm, vec=(0, 0, -thick), verts=[g for g in ex["geom"] if isinstance(g, bmesh.types.BMVert)])
    z_bot = z_top - thick

    def solid(x, y):  # inside the outline and outside every hole
        return _inside((x, y), outline) and not any(_inside((x, y), h) for h in holes)

    for f in bm.faces:
        f.normal_update()
        c = f.calc_center_median()
        if abs(c.z - z_top) < 1e-5:
            want = 1
        elif abs(c.z - z_bot) < 1e-5:
            want = -1
        else:
            n = f.normal
            probe = (c.x + n.x * 0.02, c.y + n.y * 0.02)
            want = 0 if not solid(*probe) else None   # wall: its normal must leave the solid
            if want is None:
                f.normal_flip()
            continue
        if f.normal.z * want < 0:
            f.normal_flip()
    for f in bm.faces:
        f.normal_update()
        f.material_index = 0 if (f.normal.z > 0.9 and abs(f.calc_center_median().z - z_top) < 1e-5) else 1
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if uv:
        planar_uv(me, *uv)
    return new_obj(name, me, mats, smooth_angle=30 * DEG)


# ------------------------------------------------------------------ dial, hands, crystal, movement
def leaf_hand(name, length, wmax, tail, neck, hub, mat_, at, z, ridge=0.07, thick=0.06, peak=0.58):
    """Faceted leaf (feuille) hand pointing +Y, origin on the pivot."""
    bm = bmesh.new()
    n = 48
    ys = [-tail + (length + tail) * (i / n) for i in range(n + 1)]

    def width(y):
        if y < 0:  # counterweight tail
            return neck * (0.55 + 0.45 * (1 + y / tail))
        t = y / length
        if t < peak:
            s = max(0.0, math.sin(0.5 * math.pi * t / peak))
            return max(neck, wmax * s ** 1.2)
        s = max(0.0, (1 - t) / (1 - peak))
        return max(0.0, wmax * (s ** 0.85))

    L, Cn, R_, Lb, Rb = [], [], [], [], []
    for y in ys:
        w = width(y) / 2
        L.append(bm.verts.new((-w, y, 0)))
        R_.append(bm.verts.new((w, y, 0)))
        Cn.append(bm.verts.new((0, y, ridge * min(1.0, w / (wmax / 2) + 0.35))))
        Lb.append(bm.verts.new((-w, y, -thick)))
        Rb.append(bm.verts.new((w, y, -thick)))
    for i in range(n):
        bm.faces.new((L[i], L[i + 1], Cn[i + 1], Cn[i]))
        bm.faces.new((Cn[i], Cn[i + 1], R_[i + 1], R_[i]))
        bm.faces.new((Lb[i], Lb[i + 1], L[i + 1], L[i]))
        bm.faces.new((R_[i], R_[i + 1], Rb[i + 1], Rb[i]))
        bm.faces.new((Rb[i], Rb[i + 1], Lb[i + 1], Lb[i]))
    bm.faces.new((L[0], Cn[0], R_[0], Rb[0], Lb[0]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    # hub
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=hub, radius2=hub * 0.92, depth=0.16,
                          matrix=Matrix.Translation((0, 0, 0.0)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = bm_to_obj(bm, name, mat_, smooth_angle=20 * DEG)
    o.location = (at[0], at[1], z)
    return o


def dial_features():
    import json
    return json.load(open(os.path.join(ROOT, "blender", "dial_features.json")))


def moon_window(w, n=64):
    """The moon aperture as measured: the upper half of a circle, minus two scallops on its base."""
    cx, cy, R, d, r = w["cx"], w["cy"], w["R"], w["d"], w["r"]
    pts = arc(cx, cy, R, math.pi, 0, n)                                   # top arc, left to right
    pts += [(cx + R, cy), (cx + d + r, cy)]
    pts += arc(cx + d, cy, r, 0, math.pi, n // 2)[1:]                     # right scallop
    pts += [(cx + d - r, cy), (cx - d + r, cy)]
    pts += arc(cx - d, cy, r, 0, math.pi, n // 2)[1:]                     # left scallop
    pts += [(cx - d - r, cy)]
    return pts


def star(cx, cy, r, rot=90.0, inner=0.42):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(math.radians(rot + 36 * i)),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(math.radians(rot + 36 * i))) for i in range(10)]


def build_moon_disc(M, f):
    """Moon phase as a separate part under its window: navy lacquer disc, frosted white-gold moons
    and polished stars in relief, set at the phase photographed (rotate moon_disc about Z to change it)."""
    w = f["moon_window"]
    cx, cy = w["cx"], w["cy"]
    navy = mat("Moon disc lacquer", srgb(0x0E1830), 0, 0.12, **{"Coat Weight": 1.0, "Coat Roughness": 0.05})
    frost = mat("Moon frosted white gold", srgb(0xE3E5E8), 1, 0.5)
    star_m = mat("Stars white gold", srgb(0xEEF0F2), 1, 0.3)
    root = bpy.data.objects.new("moon_disc", None)
    root.empty_display_size = 2
    C.objects.link(root)
    root.location = (cx, cy, -0.4)
    o = flat_plate(arc(0, 0, w["R"] + 0.5, 0, TAU, 128), [], -0.06, 0.15, "moon_disc_plate", [navy, navy])
    o.parent = root
    mx, my = f["moon"]["centre"][0] - cx, f["moon"]["centre"][1] - cy
    for k, sgn in enumerate((1, -1)):                         # two moons, opposite each other
        o = flat_plate(arc(sgn * mx, sgn * my, f["moon"]["r"], 0, TAU, 72), [], 0.02, 0.08, f"moon_{k + 1}", [frost, frost])
        o.parent = root
        for j, (sx, sy, sr) in enumerate(f["stars"]):
            o = flat_plate(star(sgn * (sx - cx), sgn * (sy - cy), sr, 90 if sgn > 0 else 270), [], 0.0, 0.06,
                           f"moon_star_{k + 1}_{j + 1}", [star_m, star_m])
            o.parent = root


def build_numerals(M, f):
    """Applied white-gold Roman numerals, traced stroke by stroke from the photographed dial."""
    wg = mat("Numerals white gold", srgb(0xF2F3F5), 1, 0.3)   # satin top: catches light from any side
    for hour, parts in f["numerals"].items():
        for i, p in enumerate(parts):
            o = flat_plate(p["outer"], p["holes"], 0.22, 0.22, f"numeral_{hour}_{i + 1}", [wg, M["polish"]])
            bv = o.modifiers.new("bevel", "BEVEL")
            bv.width, bv.segments, bv.limit_method, bv.angle_limit = 0.04, 2, "ANGLE", 40 * DEG


def build_inside(M):
    # dial: the photographed dial (two photos, hands removed; blender/dial_from_photo.py),
    # including its moon phase, since the watch is shown static
    dial_m = tex_mat("Dial 5057G (photo)", "dial_5057G_photo_color.jpg", orm_img="dial_5057G_photo_orm.png",
                     coat=0.35, coat_rough=0.1, aniso=0.5, emission=0.12)
    feats = dial_features()
    outline = arc(0, 0, R_DIAL, 0, TAU, 360)
    flat_plate(outline, [moon_window(feats["moon_window"])], 0.0, 0.4, "dial", [dial_m, dial_m], uv=(0, 0, DIAL_TEX_R))
    build_moon_disc(M, feats)
    build_numerals(M, feats)
    # rehaut: the narrow grey wall between the dial and the crystal
    lathe([(R_DIAL - 0.02, -0.4), (R_DIAL - 0.02, 0.02), (14.47, 1.26), (14.6, 1.26), (14.6, -0.4)], name="rehaut",
          mat=M["dark"], close=True, smooth_angle=20 * DEG)

    # hands, sized from the photo (tip radii: hour 10.6, minute 12.9, power 4.1, date 5.3,
    # seconds 3.8 mm; hour hub ~2 mm across) and posed where they stand in it
    hands = {
        "hand_hour": leaf_hand("hand_hour", 10.5, 1.0, 1.4, 0.3, 1.0, M["hand"], (0, 0), 0.45, peak=0.72),
        "hand_minute": leaf_hand("hand_minute", 12.85, 0.62, 1.8, 0.24, 0.7, M["hand"], (0, 0), 0.68, peak=0.55),
        "hand_power": leaf_hand("hand_power", 4.05, 0.46, 0.9, 0.14, 0.55, M["hand"], PR, 0.2, ridge=0.05),
        "hand_date": leaf_hand("hand_date", 5.25, 0.44, 0.9, 0.13, 0.55, M["hand"], DATE, 0.2, ridge=0.05),
        "hand_seconds": leaf_hand("hand_seconds", 3.75, 0.3, 0.9, 0.1, 0.5, M["hand"], SECS, 0.2, ridge=0.04),
    }
    for key, name in (("hour", "hand_hour"), ("minute", "hand_minute"), ("power", "hand_power"),
                      ("date", "hand_date"), ("seconds", "hand_seconds")):
        hands[name].rotation_euler.z = (POSE[key] - 90) * DEG  # hands are built pointing +Y
    # pivot caps with the small pink jewel seen in close-ups
    for (x, y, z, r, parent) in [(0, 0, 0.78, 0.55, "hand_minute"), (*PR, 0.3, 0.38, "hand_power"),
                                 (*DATE, 0.3, 0.38, "hand_date"), (*SECS, 0.3, 0.34, "hand_seconds")]:
        cap = lathe([(0, 0.16), (r * 0.55, 0.15), (r, 0.05), (r, 0), (0, 0)], segs=48, name=f"{parent}_cap", mat=M["hand"])
        j = lathe([(0, 0.2), (r * 0.18, 0.19), (r * 0.25, 0.14), (r * 0.25, 0.1), (0, 0.1)], segs=24, name=f"{parent}_jewel", mat=M["ruby"])
        for o in (cap, j):
            o.parent = hands[parent]
            o.location = (0, 0, z - hands[parent].location.z + 0.06)

    # domed sapphire crystal
    lathe([(0, Z_CRYSTAL), (7.0, Z_CRYSTAL - 0.17), (12.0, Z_CRYSTAL - 0.47), (14.47, 1.62), (14.47, 1.27),
           (12.0, 1.12), (7.0, 1.36), (0, 1.42)], segs=192, name="crystal", mat=M["glass"], close=True, smooth_angle=60 * DEG)

    build_movement(M)
    # movement casing ring and inner case wall, so no gaps show at grazing angles
    lathe([(R_WIN, -4.95), (R_WIN, -0.45), (15.25, -0.45), (15.25, -4.95)], name="casing_ring", mat=M["satin"], close=True)
    # caseback sapphire
    lathe([(0, Z_BACK + 0.28), (R_WIN + 0.02, Z_BACK + 0.28), (R_WIN + 0.02, Z_BACK + 1.0), (0, Z_BACK + 1.0)], segs=192,
          name="caseback_glass", mat=M["glass"], close=True, smooth_angle=60 * DEG)
    # the anniversary print, on the sapphire's inside face: "Cortina Watch / 50th Anniversary / Since 1972"
    # in translucent white (blender/caseback_print.py, measured on the caseback photograph)
    if os.path.exists(os.path.join(TEX, "caseback_print_5057G.png")):
        pm = mat("Caseback print", (1, 1, 1), 0, 0.55)
        nt = pm.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = image("caseback_print_5057G.png")
        t.interpolation = "Cubic"
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(t.outputs["Alpha"], bsdf.inputs["Alpha"])
        if hasattr(pm, "surface_render_method"):
            pm.surface_render_method = "BLENDED"
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=True, segments=192, radius=R_WIN)
        for f in bm.faces:
            f.normal_flip()                    # faces the caseback side, where it is read
        o = bm_to_obj(bm, "caseback_print", pm)
        o.data.transform(Matrix.Translation((0, 0, Z_BACK + 1.0 + 0.004)))
        planar_uv(o.data, 0, 0, 14.06, flip_u=True)   # the movement textures' photo-view frame


# ------------------------------------------------------------------ calibre 240 (3D, from the caseback photo)
def _world_mesh(o):
    """Bake an object's transform into its mesh (planar photo UVs are taken in watch space)."""
    o.data.transform(o.matrix_basis)
    o.matrix_basis = Matrix.Identity(4)
    return o


def _cotes_normal():
    """Côtes de Genève for the rotor (rotor UV space, 14.8 mm square on the pivot): bands 2.57 mm wide,
    one edge on the rotor's axis, each a shallow cylinder (±8°), as on the photographed rotor."""
    name = "rotor_cotes_2p6_normal.png"
    path = os.path.join(TEX, name)
    if not os.path.exists(path):
        import numpy as np
        n = 1024
        u = (np.arange(n) + 0.5) / n
        x = u * 2 * 7.4 - 7.4                            # mm from the rotor's axis
        band = (x / 2.57) % 1.0
        dh = (1 - 2 * band) * 0.14                        # cylinder: the slope runs evenly across the band
        nx = -dh / np.sqrt(1 + dh * dh)
        nz = 1 / np.sqrt(1 + dh * dh)
        img = np.zeros((n, n, 4), np.float32)
        dither = np.random.default_rng(1143).uniform(-0.5, 0.5, (n, n)) / 255   # no 8-bit banding in the reflections
        img[..., 0] = (nx * 0.5 + 0.5)[None, :] + dither
        img[..., 1] = 0.5
        img[..., 2] = (nz * 0.5 + 0.5)[None, :]
        img[..., 3] = 1
        im = bpy.data.images.new(name, n, n)
        im.pixels.foreach_set(img.ravel())
        im.filepath_raw = path
        im.file_format = "PNG"
        im.save()
        bpy.data.images.remove(im)
    return image(name, "Non-Color")


def gear_outline(cx, cy, r_tip, n, kind="cycloid"):
    """Wheel outline with n teeth: rounded (ogival) watch-wheel teeth, or a ratchet's saw teeth."""
    pitch = TAU / n
    depth = min(0.3, 0.55 * pitch * r_tip) if kind == "cycloid" else min(0.28 if kind == "club" else 0.22, 0.4 * pitch * r_tip)
    r0 = r_tip - depth
    prof = ([(-0.5, r0), (-0.3, r0), (-0.22, r0 + depth * 0.55), (-0.13, r_tip), (0.13, r_tip), (0.22, r0 + depth * 0.55), (0.3, r0)]
            if kind == "cycloid" else
            [(-0.5, r0), (0.05, r0 + depth * 0.15), (0.3, r_tip), (0.42, r_tip - depth * 0.15), (0.5, r0)] if kind == "club" else
            [(-0.5, r0), (0.38, r_tip), (0.42, r_tip - depth * 0.2), (0.5, r0)])
    pts = []
    for i in range(n):
        for f, rr in (prof if kind == "cycloid" else prof[:-1]):   # a ratchet's last point is the next tooth's first
            a = (i + 0.5 + f) * pitch
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def spoke_windows(cx, cy, r_hub, r_rim, k, w, phase=0.0, n=14):
    """The windows between k straight spokes of width w, from the hub to the rim."""
    wins = []
    for i in range(k):
        a0, a1 = phase + TAU * i / k, phase + TAU * (i + 1) / k
        mo, mi = math.asin(min(0.99, w / 2 / r_rim)), math.asin(min(0.99, w / 2 / r_hub))
        outer = arc(cx, cy, r_rim, a0 + mo, a1 - mo, n) + [(cx + r_rim * math.cos(a1 - mo), cy + r_rim * math.sin(a1 - mo))]
        inner = arc(cx, cy, r_hub, a1 - mi, a0 + mi, n // 2) + [(cx + r_hub * math.cos(a0 + mi), cy + r_hub * math.sin(a0 + mi))]
        wins.append((outer + inner)[::-1])
    return wins


def _normal_mat(name, color, metal, rough, normal_img, strength):
    m = mat(name, color, metal, rough)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for n in [n for n in nt.nodes if n.type in ("TEX_IMAGE", "NORMAL_MAP")]:
        nt.nodes.remove(n)
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = image(normal_img, "Non-Color")
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = strength
    nt.links.new(t.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


PART_NAMES = {"bridge_train": "105_barrel_bridge", "bridge_wheels": "110_train_bridge",
              "bridge_centre": "1149_automatic_bridge", "balance_cock": "121_balance_cock",
              "pallet_bridge": "125_pallet_bridge"}   # Patek Philippe's part numbers ("watch photos/240 movement.jpg")


def build_movement(M):
    """The 5057G's own calibre 240, built with real finishing: rhodium-plated bridges with Côtes de
    Genève and polished chamfers (anglage), a perlaged baseplate with sinkings, gilt engravings,
    gold train wheels with circular graining, snailed steel wheels, jewels in polished countersinks,
    screws, a 22K gold mini-rotor that turns and a balance that swings on its hairspring. Layout from
    the caseback photograph (blender/movement_from_photo.py), finishes from blender/movement_finish.py."""
    import json
    data = json.load(open(os.path.join(ROOT, "blender", "movement.json")))
    H = data["texture_half_size"]
    W = lambda pts: [(-x, y) for x, y in pts]          # photo view (from the back) -> watch frame
    mv = tex_mat("Movement finish (rhodium)", "movement_finish_color.jpg", orm_img="movement_finish_orm.png")
    nt = mv.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.0
    ni = nt.nodes.new("ShaderNodeTexImage")
    ni.image = image("movement_finish_normal.png", "Non-Color")
    nt.links.new(ni.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    gold_w = mat("Gold wheels polished", srgb(0xDDA866), 1, 0.08)
    gold_grain = _normal_mat("Gold wheels circular graining", srgb(0xD9A35E), 1, 0.24, "circular_graining_normal.png", 0.6)
    steel_snail = _normal_mat("Steel snailed", srgb(0xD4D6DA), 1, 0.18, "snailing_normal.png", 0.7)
    glucydur = mat("Balance glucydur", srgb(0xF2C274), 1, 0.36)   # satin yellow: reads bright gold, as photographed
    spring_m = mat("Hairspring Spiromax", srgb(0x8F98AE), 1, 0.25)
    slot_m = mat("Screw slot", srgb(0x0C0C0E), 0, 0.6)
    steel = mat("Steel polished", srgb(0xE2E3E6), 1, 0.08)
    sink_m = mat("Countersink polished", srgb(0xE4E6EA), 1, 0.17)   # softer than mirror: reads as in the photo
    ruby = mat("Ruby jewel", srgb(0x9C2C6E), 0, 0.03, **{"Coat Weight": 1.0, "Transmission Weight": 0.35})  # synthetic ruby

    def photo_faces(o, face_mat=1, other=0):
        for f in o.data.polygons:
            f.material_index = face_mat if f.normal.z < -0.9 else other
        planar_uv(o.data, 0, 0, H, flip_u=True)

    # baseplate, with sinkings (0.5 mm) round the wheels; perlage on the plate and the sinking floors
    pockets = [W(pk["outer"]) for pk in data["pockets"]]
    plate_pins = [arc(-x, y, r + 0.12, TAU, 0, 32) for x, y, r in data.get("pin_holes", [])
                  if not any(_inside((-x, y), W(b)) for b in data["bridges"].values())
                  and not any(_inside((-x, y), pk) for pk in pockets)]
    pockets += plate_pins
    o = flat_plate(arc(0, 0, R_WIN, 0, TAU, 256), pockets, Z_SINK, Z_SINK - Z_PLATE, "movement_plate", [M["satin"], mv])
    photo_faces(o)
    # the sinkings' floor, with a deeper pit for the balance and escapement (escape wheel and pallet fork
    # under the balance, hairspring over its arms)
    pit = W(data["deep_pit"]) if data.get("deep_pit") else None
    o = flat_plate(arc(0, 0, R_WIN - 0.05, 0, TAU, 192), [pit] if pit else [], Z_SINK + Z_PIT, Z_PIT, "movement_sink_floor", [mv, mv])
    planar_uv(o.data, 0, 0, H, flip_u=True)
    if pit:
        pit_m = mat("Pit floor (in shadow)", srgb(0x7E8186), 1, 0.42)   # deep under the balance: darker, as photographed
        o = flat_plate(pit, [], Z_SINK + Z_PIT + 0.05, 0.05, "movement_pit_floor", [pit_m, pit_m])
        planar_uv(o.data, 0, 0, H, flip_u=True)

    def face_viewer(o):  # open lathe surfaces: make every face look toward the caseback (-Z)
        for f in o.data.polygons:
            if f.normal.z > 0:
                f.flip()
        o.data.update()

    # jewels: ruby, dome and oil sink, at the bottom of a polished countersink bored into its bridge
    bridges = {k: W(v) for k, v in data["bridges"].items()}
    chatons = [((-x, y), r, kind) for x, y, r, kind in data.get("chatons", [])]
    pin_holes = [((-x, y), r) for x, y, r in data.get("pin_holes", [])]
    jewels = []
    for x, y, r in sorted(data["jewels"], key=lambda j: -j[2]):    # largest first; merge split detections
        if any(math.hypot(-x - q[0][0], y - q[0][1]) < 0.6 + q[1] for q in jewels):
            continue
        if any(math.hypot(-x - c[0][0], y - c[0][1]) < c[1] for c in chatons):
            continue    # set in a gold chaton, built below
        rj = min(max(r * 1.0, 0.24), 0.6)
        jewels.append(((-x, y), rj, rj + 0.24))   # countersink: a narrow polished ring, as photographed
    in_bridge = {}
    for name, outline in bridges.items():
        in_bridge[name] = [j for j in jewels
                           if all(_inside((j[0][0] + j[2] * 1.15 * math.cos(a), j[0][1] + j[2] * 1.15 * math.sin(a)), outline)
                                  for a in [k * TAU / 12 for k in range(12)])]

    # bridges: visible face toward the caseback, polished chamfer round every edge, jewel holes
    ring_in = lambda pt, r, outline: all(_inside((pt[0] + r * 1.15 * math.cos(a), pt[1] + r * 1.15 * math.sin(a)), outline)
                                         for a in [k * TAU / 12 for k in range(12)])
    Z_PB = Z_SINK + 0.03                     # pallet bridge 125: its face, under the balance
    pj = ((-data["escapement"]["pivot"][0], data["escapement"]["pivot"][1]), 0.26, 0.48) if data.get("escapement") else None
    for name, outline in bridges.items():
        holes = [arc(pt[0], pt[1], rs, TAU, 0, 40) for pt, rj, rs in in_bridge[name]]
        if name == "pallet_bridge":
            holes += [arc(pj[0][0], pj[0][1], pj[2], TAU, 0, 40)] if pj else []
            o = flat_plate(outline, holes, Z_SINK + 0.2, 0.17, PART_NAMES.get(name, name), [M["polish"], mv])
            photo_faces(o)
            bv = o.modifiers.new("anglage", "BEVEL")
            bv.width, bv.segments, bv.limit_method, bv.angle_limit, bv.material = 0.06, 2, "ANGLE", 40 * DEG, 0
            bv.harden_normals = True
            continue
        holes += [arc(pt[0], pt[1], r, TAU, 0, 48) for pt, r, _ in chatons if ring_in(pt, r, outline)]
        holes += [arc(pt[0], pt[1], r + 0.12, TAU, 0, 32) for pt, r in pin_holes if ring_in(pt, r + 0.12, outline)]
        o = flat_plate(outline, holes, Z_PLATE, Z_PLATE - Z_BRIDGE, PART_NAMES.get(name, name), [M["polish"], mv])
        photo_faces(o)
        bv = o.modifiers.new("anglage", "BEVEL")
        bv.width, bv.segments, bv.limit_method, bv.angle_limit = 0.14, 3, "ANGLE", 40 * DEG   # polished anglage
        bv.material = 0
        bv.harden_normals = True

    if pj:   # the pallet jewel, in its countersink in the pallet bridge's lobe
        (px, py), rj, rs = pj
        o = lathe([(rs, 0.0), (rj + 0.04, 0.12), (0.0, 0.13)], segs=48, name="125_pallet_jewel_sink", mat=sink_m, smooth_angle=60 * DEG)
        o.matrix_basis = Matrix.Translation((px, py, Z_PB))
        _world_mesh(o)
        face_viewer(o)
        o = lathe([(0.0, 0.07), (0.07, 0.05), (0.12, 0.04), (rj * 0.62, 0.045), (rj * 0.92, 0.09), (rj, 0.12)], segs=48,
                  name="125_pallet_jewel", mat=ruby, smooth_angle=70 * DEG)
        o.matrix_basis = Matrix.Translation((px, py, Z_PB))
        _world_mesh(o)
        face_viewer(o)
    set_jewels = {id(j) for js in in_bridge.values() for j in js}
    for i, j in enumerate(jewels):
        (px, py), rj, rs = j
        sunk = id(j) in set_jewels
        z0 = Z_BRIDGE if sunk else (Z_BRIDGE if any(_inside((px, py), b) for b in bridges.values()) else Z_PLATE) - 0.14
        # countersink: polished cone from the bridge face down to the jewel (z grows into the bridge)
        o = lathe([(rs, 0.0), (rj + 0.04, 0.14), (0.0, 0.15)], segs=48, name=f"jewel_sink_{i + 1}", mat=sink_m,
                  smooth_angle=60 * DEG)
        o.matrix_basis = Matrix.Translation((px, py, z0))
        _world_mesh(o)
        face_viewer(o)
        # the ruby: a low dome with the oil sink round its pivot hole
        o = lathe([(0.0, 0.08), (0.07, 0.055), (0.13, 0.045), (rj * 0.62, 0.05), (rj * 0.92, 0.1), (rj, 0.14)], segs=48,
                  name=f"jewel_{i + 1}", mat=ruby, smooth_angle=70 * DEG)
        o.matrix_basis = Matrix.Translation((px, py, z0))
        _world_mesh(o)
        face_viewer(o)

    # gold chatons: a polished gold ring pressed into the bridge, holding a ruby (the balance jewel
    # under its shock spring) or the barrel arbor's polished steel pivot
    chaton_gold = mat("Chaton gold polished", srgb(0xE6AC74), 1, 0.07)
    for i, ((px, py), ro, kind) in enumerate(chatons):
        z0 = Z_BRIDGE if any(ring_in((px, py), ro, b) for b in bridges.values()) else Z_PLATE
        ri = ro * 0.62
        o = lathe([(ri, 0.3), (ri, 0.03), (ri + 0.04, -0.005), (ro * 0.86, -0.03), (ro - 0.03, -0.015), (ro, 0.02), (ro, 0.3)],
                  segs=64, name=f"chaton_{i + 1}", mat=chaton_gold, close=True, smooth_angle=50 * DEG)
        o.matrix_basis = Matrix.Translation((px, py, z0))
        if kind == "ruby":
            o = lathe([(0.0, 0.08), (0.07, 0.055), (0.13, 0.045), (ri * 0.62, 0.05), (ri * 0.92, 0.08), (ri, 0.1)], segs=48,
                      name=f"chaton_{i + 1}_jewel", mat=ruby, smooth_angle=70 * DEG)
            o.matrix_basis = Matrix.Translation((px, py, z0))
            _world_mesh(o)
            face_viewer(o)
            if ro < 0.7:   # the balance jewel: a shock spring's two arms over it
                for side in (0, 1):
                    a0 = math.radians(25 + 180 * side)
                    band = arc(px, py, ri * 0.98, a0, a0 + math.radians(130), 24) + arc(px, py, ri * 0.72, a0 + math.radians(130), a0, 24)
                    flat_plate(band, [], z0 + 0.02, 0.04, f"chaton_{i + 1}_spring_{side + 1}", [steel, steel])
        else:
            o = lathe([(0.0, 0.06), (0.07, 0.06), (0.09, 0.03), (ri * 0.8, 0.02), (ri, 0.06)], segs=40,
                      name=f"chaton_{i + 1}_pivot", mat=steel, smooth_angle=60 * DEG)
            o.matrix_basis = Matrix.Translation((px, py, z0))
            _world_mesh(o)
            face_viewer(o)

    # steady-pin and tool holes: polished countersinks bored into the bridges (or the plate)
    for i, ((px, py), r) in enumerate(pin_holes):
        on_bridge = any(ring_in((px, py), r + 0.12, b) for b in bridges.values())
        z0, depth = (Z_BRIDGE, 0.48) if on_bridge else (Z_PLATE, 0.4)
        o = lathe([(r + 0.12, 0.0), (r + 0.02, 0.1), (r, 0.14), (r, depth)], segs=40, name=f"pin_hole_{i + 1}",
                  mat=sink_m, smooth_angle=60 * DEG)
        o.matrix_basis = Matrix.Translation((px, py, z0))
        _world_mesh(o)
        face_viewer(o)
        o = lathe([(0.0, depth), (r, depth)], segs=40, name=f"pin_hole_{i + 1}_bottom", mat=slot_m)
        o.matrix_basis = Matrix.Translation((px, py, z0))
        _world_mesh(o)
        face_viewer(o)

    # the mainspring barrel 415 on the barrel bridge's bushing: a steel drum, its toothed rim gilt; only a
    # crescent of it shows past the barrel bridge's edge (beside "ADJUSTED"), as photographed
    if data.get("barrel"):
        bx_, by_, br_, bn_ = -data["barrel"][0], data["barrel"][1], data["barrel"][2], data["barrel"][3]
        o = flat_plate(gear_outline(bx_, by_, br_, bn_), [arc(bx_, by_, br_ - 0.36, TAU, 0, 192)], Z_SINK - 0.02, 0.28,
                       "415_barrel", [gold_w, gold_grain])
        for f in o.data.polygons:
            f.material_index = 1 if f.normal.z < -0.9 else 0
        planar_uv(o.data, bx_, by_, br_)
        drum_m = mat("Barrel drum steel", srgb(0xC9CCD1), 1, 0.3)
        o = flat_plate(arc(bx_, by_, br_ - 0.35, 0, TAU, 192), [], Z_SINK - 0.02, 0.26, "415_barrel_drum", [drum_m, drum_m])
    # gold train wheels: real teeth, spokes, polished hub; each on its own level so meshing teeth clear
    # (the centre wheel rides over the barrel, just under the plate's face)
    gear_z = {"200_centre_wheel": Z_SINK - 0.34, "1481_reduction_wheel": Z_SINK - 0.14, "210_third_wheel": Z_SINK - 0.14,
              "220_fourth_wheel": Z_SINK - 0.3}
    for name, (x, y, r, teeth, spokes) in data["gold_gears"].items():
        cx, cy = -x, y
        rim_in = r - 0.3 - max(0.18, r * 0.07)
        hub = max(0.45, r * 0.16)
        o = flat_plate(gear_outline(cx, cy, r, teeth), spoke_windows(cx, cy, hub, rim_in, spokes, max(0.22, r * 0.065), 0.3),
                       gear_z[name], 0.12, name, [gold_w, gold_grain])
        for f in o.data.polygons:
            f.material_index = 1 if f.normal.z < -0.9 else 0
        planar_uv(o.data, cx, cy, r)
        o = lathe([(0, -0.1), (hub * 0.55, -0.1), (hub * 0.8, -0.07), (hub * 0.85, 0.0), (0, 0.0)], segs=40,
                  name=f"{name}_hub", mat=gold_w, smooth_angle=50 * DEG)
        o.matrix_basis = Matrix.Translation((cx, cy, gear_z[name] - 0.12))
        o = lathe([(0, -0.32), (0.17, -0.3), (0.17, 0.0), (0, 0.0)], segs=24, name=f"{name}_arbor", mat=steel)
        o.matrix_basis = Matrix.Translation((cx, cy, gear_z[name] - 0.12))
        if name == "220_fourth_wheel":   # its arbor runs on through the dial: the small seconds hand
            o = lathe([(0.12, 0.0), (0.12, 0.6), (0.0, 0.6)], segs=16, name="220_fourth_wheel_seconds_arbor", mat=steel)
            o.matrix_basis = Matrix.Translation((cx, cy, gear_z[name]))

    # steel wheels of the automatic winding: snailed, toothed; the large one is the ratchet
    for i, (x, y, r) in enumerate(data["steel_wheels"]):
        big = r > 3
        top = Z_SINK - (0.27 if big else 0.38)
        wname = "1497_winding_wheel" if big else "1480_wheel"
        o = flat_plate(gear_outline(-x, y, r, 100 if big else 40, "ratchet" if big else "cycloid"),
                       [arc(-x, y, 0.42, TAU, 0, 24)], top, 0.1, wname, [steel, steel_snail])
        for f in o.data.polygons:
            f.material_index = 1 if f.normal.z < -0.9 else 0
        planar_uv(o.data, -x, y, r)
        o = lathe([(0.42, -0.08), (0.75, -0.08), (0.85, -0.03), (0.85, 0.0), (0.42, 0.0)], segs=40,
                  name=f"{wname}_collar", mat=steel, close=True)
        o.matrix_basis = Matrix.Translation((-x, y, top - 0.1))

    # ---- escapement, in the balance's pit (as photographed, with the parts diagram): the escape wheel 702
    # under the train bridge's gold chaton (its jewel), the pallet lever 710 pivoting in the pallet bridge's
    # jewel, its exit stone flat in a "⊐" socket and its long entry stone upright, the fork reaching to the
    # balance's impulse pin. Stacked under the balance: escape wheel and stones, lever, pallet bridge 125.
    es = data["escapement"]
    ex_, ey_, er_, nt_ = -es["wheel"][0], es["wheel"][1], es["wheel"][2], es["wheel"][3]
    pvx, pvy = -es["pivot"][0], es["pivot"][1]

    def pivoted(name, x, y):
        e = bpy.data.objects.new(name, None)
        e.empty_display_size = 1
        C.objects.link(e)
        e.location = (x, y, 0.0)
        return e

    def onto(o, e):   # a part built in watch space, re-hung on its pivot
        o.data.transform(Matrix.Translation((-e.location.x, -e.location.y, 0.0)))
        o.parent = e
        return o

    esc = pivoted("escape_wheel", ex_, ey_)
    esc_m = mat("Escape wheel steel", srgb(0x7A7E86), 1, 0.28)   # deep in the pit it reads dark, as photographed
    o = flat_plate(gear_outline(ex_, ey_, er_, nt_, "club"), spoke_windows(ex_, ey_, 0.36, er_ - 0.55, 5, 0.14, 0.2),
                   Z_SINK + 0.38, 0.08, "702_escape_wheel", [esc_m, esc_m])
    onto(o, esc)
    o = lathe([(0, -0.5), (0.11, -0.5), (0.11, 0.3), (0.28, 0.32), (0.28, 0.45), (0, 0.45)], segs=24,
              name="702_escape_pinion", mat=steel, close=True)                       # arbor up to its jewel, pinion below
    o.matrix_basis = Matrix.Translation((0, 0, Z_SINK))
    o.parent = esc
    lev = pivoted("pallet_lever", pvx, pvy)
    o = flat_plate(W(es["lever"]), [W(h) for h in es.get("lever_holes", [])], Z_SINK + 0.30, 0.09, "710_pallet_lever",
                   [steel, steel])
    onto(o, lev)
    for k, st in es["stones"].items():
        onto(flat_plate(W(st), [], Z_SINK + 0.38, 0.12, f"710_pallet_stone_{k}", [ruby, ruby]), lev)
    o = lathe([(0, 0.03), (0.1, 0.03), (0.1, 0.55), (0, 0.55)], segs=16, name="710_pallet_arbor", mat=steel, close=True)
    o.matrix_basis = Matrix.Translation((0, 0, Z_SINK))
    o.parent = lev

    # screws: polished steel heads with their slots
    def level(pt):
        if "pallet_bridge" in bridges and _inside(pt, bridges["pallet_bridge"]):
            return Z_PB, 0.05
        return (Z_BRIDGE if any(_inside(pt, b) for n_, b in bridges.items() if n_ != "pallet_bridge") else Z_PLATE), 0.13
    for i, (x, y, r) in enumerate(data["screws"]):
        pt = (-x, y)
        z0, hh = level(pt)
        o = lathe([(0, -hh), (r * 0.7, -hh * 0.77), (r, -hh * 0.23), (r, 0.0), (0, 0.0)], segs=40, name=f"screw_{i + 1}",
                  mat=steel, smooth_angle=60 * DEG)
        o.matrix_basis = Matrix.Translation((pt[0], pt[1], z0))
        a = 0.6 + i * 1.7
        ca, sa = math.cos(a), math.sin(a)
        slot = [(pt[0] + ca * u - sa * v, pt[1] + sa * u + ca * v) for u, v in
                ((-r * 0.92, -0.06), (r * 0.92, -0.06), (r * 0.92, 0.06), (-r * 0.92, 0.06))]
        flat_plate(slot, [], z0 - hh * 0.69, hh * 0.38, f"screw_{i + 1}_slot", [slot_m, slot_m])

    # ---- the balance: Gyromax-style glucydur wheel under its cock, swinging on its hairspring
    bx, by, br = -data["balance"][0], data["balance"][1], data["balance"][2]
    bal = bpy.data.objects.new("balance", None)
    bal.empty_display_size = 2
    C.objects.link(bal)
    bal.location = (bx, by, Z_SINK)
    # Patek's Gyromax: a thin glucydur rim on four tapered arms; at each arm's end a slotted gold
    # weight (masselotte) turning on a polished pin, the rate set by turning them (no regulator)
    r_in = br - 0.24
    parts = []
    o = flat_plate(arc(0, 0, br, 0, TAU, 192), [arc(0, 0, r_in, TAU, 0, 192)], -0.02, 0.27, "balance_rim", [glucydur, glucydur])
    bv = o.modifiers.new("chamfer", "BEVEL")
    bv.width, bv.segments, bv.limit_method, bv.angle_limit, bv.harden_normals = 0.03, 2, "ANGLE", 40 * DEG, True
    parts.append(o)
    phase = math.radians(180 - data.get("balance_arms_deg", 81.0))   # photo view -> watch frame
    # measured on the photo: arms ~0.5 mm wide, weights 0.64 mm across centred 3.15 mm out, their
    # slots set different ways (photo-view directions, one per arm)
    rw, wr = 3.05, 0.33
    weight_m = mat("Balance weights gold", srgb(0xFADA9C), 1, 0.18)
    slot_dirs = data.get("balance_weight_slots_deg", [0.0, 10.0, 330.0, 45.0])
    for k in range(4):
        a = phase + k * TAU / 4
        ca, sa = math.cos(a), math.sin(a)
        rot = lambda u, v: (ca * u - sa * v, sa * u + ca * v)
        arm = [(0.35, -0.18), (2.2, -0.22), (rw - 0.25, -0.29), (r_in + 0.06, -0.3),
               (r_in + 0.06, 0.3), (rw - 0.25, 0.29), (2.2, 0.22), (0.35, 0.18)]
        parts.append(flat_plate([rot(u, v) for u, v in arm], [], -0.06, 0.15, f"balance_arm_{k + 1}", [glucydur, glucydur]))
        # the weight, as photographed: a slotted gold ring (a "G") round a bright centre pin, dark between
        wx, wy = rw * ca, rw * sa
        so = math.radians(180 - slot_dirs[k % len(slot_dirs)])     # photo view -> watch frame
        ri_w = 0.17
        do, di = math.asin(0.065 / wr), math.asin(0.065 / ri_w)
        cshape = arc(wx, wy, wr, so + do, so + TAU - do, 48) + arc(wx, wy, ri_w, so + TAU - di, so + di, 20)
        o = flat_plate(cshape, [], -0.05, 0.26, f"balance_weight_{k + 1}", [weight_m, weight_m])
        bv = o.modifiers.new("round", "BEVEL")   # rounded edges catch the light, as on the photo
        bv.width, bv.segments, bv.limit_method, bv.angle_limit, bv.harden_normals = 0.06, 3, "ANGLE", 40 * DEG, True
        parts.append(o)
        cs_, sn_ = math.cos(so), math.sin(so)    # the slot reads dark, as on the photo: a shadowed floor in it
        slot = arc(wx, wy, ri_w + 0.005, so + di, so + TAU - di, 20) + \
            [(wx + cs_ * (wr - 0.02) + sn_ * 0.07, wy + sn_ * (wr - 0.02) - cs_ * 0.07),
             (wx + cs_ * (wr - 0.02) - sn_ * 0.07, wy + sn_ * (wr - 0.02) + cs_ * 0.07)]
        parts.append(flat_plate(slot, [], -0.212, 0.006, f"balance_weight_{k + 1}_slot", [slot_m, slot_m]))
        o = lathe([(0, -0.33), (0.06, -0.325), (0.09, -0.3), (0.09, 0.0), (0, 0.0)], segs=24,
                  name=f"balance_weight_{k + 1}_pin", mat=weight_m, smooth_angle=60 * DEG)   # bright domed centre
        o.matrix_basis = Matrix.Translation((wx, wy, 0.0))
        parts.append(o)
    parts.append(flat_plate(arc(0, 0, 0.5, 0, TAU, 40), [], -0.08, 0.14, "balance_hub", [glucydur, glucydur]))
    # the double roller under the hub, its ruby impulse pin reaching to the pallet fork
    o = lathe([(0.12, 0.2), (0.55, 0.2), (0.6, 0.17), (0.6, 0.06), (0.12, 0.06)], segs=40, name="balance_roller",
              mat=steel, close=True, smooth_angle=40 * DEG)
    parts.append(o)
    ux0, uy0 = (pvx - bx), (pvy - by)
    ul = math.hypot(ux0, uy0)
    o = lathe([(0, 0.12), (0.06, 0.12), (0.06, 0.3), (0, 0.3)], segs=16, name="balance_impulse_pin", mat=ruby, close=True)
    o.matrix_basis = Matrix.Translation((ux0 / ul * 0.48, uy0 / ul * 0.48, 0.0))
    parts.append(o)
    o = lathe([(0, -0.62), (0.12, -0.6), (0.12, -0.36), (0.32, -0.34), (0.32, -0.1), (0, -0.1)], segs=32,
              name="balance_staff", mat=steel)
    parts.append(o)
    for o in parts:
        o.parent = bal
    # hairspring: a flat spiral, inner end on the collet (turns with the balance), outer end at the stud
    turns, r0s, r1s, wid, z_lo, z_hi = 12, 0.45, 2.2, 0.05, -0.3, -0.37   # outer end at the stud, 2.2 mm out
    nseg = turns * 48
    bm = bmesh.new()
    rings = []
    for i in range(nseg + 1):
        t = i / nseg
        a = TAU * turns * t
        rr = r0s + (r1s - r0s) * t
        ring = []
        for dr, z in ((-wid / 2, z_lo), (wid / 2, z_lo), (wid / 2, z_hi), (-wid / 2, z_hi)):
            ring.append(bm.verts.new(((rr + dr) * math.cos(a), (rr + dr) * math.sin(a), z)))
        rings.append(ring)
    for i in range(nseg):
        for k in range(4):
            kk = (k + 1) % 4
            bm.faces.new((rings[i][k], rings[i][kk], rings[i + 1][kk], rings[i + 1][k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    hs = bm_to_obj(bm, "hairspring", spring_m, smooth_angle=50 * DEG)
    hs.location = (bx, by, Z_SINK)
    if data.get("hairspring_stud"):   # the black stud holding the hairspring's outer end, under the cock's edge
        sx_, sy_ = -data["hairspring_stud"][0], data["hairspring_stud"][1]
        ta = math.atan2(sy_ - by, sx_ - bx) + math.pi / 2
        ct_, st_ = math.cos(ta), math.sin(ta)
        blk = [(sx_ + ct_ * u - st_ * v, sy_ + st_ * u + ct_ * v) for u, v in ((-0.3, -0.17), (0.3, -0.17), (0.3, 0.17), (-0.3, 0.17))]
        stud_m = mat("Stud blackened steel", srgb(0x1C1D20), 1, 0.3)
        flat_plate(blk, [], Z_SINK - 0.34, 0.16, "hairspring_stud", [stud_m, stud_m])
    # shape keys every 30°: the coils wind by A·(1 - t) (t: 0 at the collet, 1 at the stud)
    hs.shape_key_add(name="Basis", from_mix=False)
    fr = [min(1.0, i // 4 / nseg) for i in range(len(hs.data.vertices))]
    keys = {}
    for k in [k for k in range(-9, 10) if k]:
        sk = hs.shape_key_add(name=f"wind{k * 30:+d}", from_mix=False)
        ang = math.radians(k * 30)
        for i, v in enumerate(hs.data.vertices):
            phi = ang * (1 - fr[i])
            c, s_ = math.cos(phi), math.sin(phi)
            sk.data[i].co = (v.co.x * c - v.co.y * s_, v.co.x * s_ + v.co.y * c, v.co.z)
        keys[k] = sk

    # ---- the 22K gold mini-rotor, on its own pivot so it can turn
    rp = data["rotor"]
    pv = (-rp["pivot"][0], rp["pivot"][1])
    rr = min(rp["radius"], R_WIN - abs(complex(*pv)) - 0.15)  # clear of the caseback wall at any angle
    rotor = bpy.data.objects.new("movement_rotor", None)
    rotor.empty_display_size = 3
    C.objects.link(rotor)
    rotor.location = (pv[0], pv[1], Z_ROTOR)
    _cotes_normal()  # make sure the stripe map exists before the material loads it
    g22 = tex_mat("Rotor 22K gold", _cotes_normal().name, rough=0.3, metal=1.0, aniso=0.0)
    nt = g22.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    t = next(n for n in nt.nodes if n.type == "TEX_IMAGE")
    t.image = _cotes_normal()
    for l in list(t.outputs["Color"].links):
        nt.links.remove(l)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.0
    nt.links.new(t.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Base Color"].default_value = (*srgb(0xF0CC8E), 1)
    b.inputs["Roughness"].default_value = 0.3
    gold_pol = mat("Rotor gold polished", srgb(0xE8B985), 1, 0.06)
    # a half-disc with a small round notch for the hub; the cross engraved on its axis, 3.3 mm out
    sector = arc(0, 0, rr, math.pi, TAU, 128) + [(rr, 0.0), (0.82, 0.0)] + arc(0, 0, 0.82, 0, -math.pi, 24)[1:] + [(-0.82, 0.0)]
    cross = [(x, y - 3.3) for x, y in calatrava_cross(2.1)]
    ENGRAVE = 0.12
    # top layer, pierced by the cross; its visible face is the striped gold
    holes = [arc(-sx_ - pv[0], sy_ - pv[1], 0.6, TAU, 0, 32) for sx_, sy_ in data.get("rotor_screws", [])]
    o = flat_plate(sector, [cross[::-1]] + holes, -0.3 + ENGRAVE, ENGRAVE, "1143_rotor", [gold_pol, g22])
    for f in o.data.polygons:
        f.material_index = 1 if f.normal.z < -0.9 else 0
    planar_uv(o.data, 0, 0, 7.4)
    bv = o.modifiers.new("anglage", "BEVEL")
    bv.width, bv.segments, bv.limit_method, bv.angle_limit, bv.material = 0.09, 3, "ANGLE", 40 * DEG, 0
    bv.harden_normals = True     # flat faces stay flat: no shading seams across the big face
    o.parent = rotor
    # body under it: its exposed face inside the cross is the engraving's matte floor
    engraved = mat("Rotor gold engraved", srgb(0xF8DCA8), 1, 0.3)   # the cross's cut: bright satin gold
    o = flat_plate(sector, holes, 0.0, 0.3 - ENGRAVE, "1143_rotor_body", [gold_pol, engraved])
    for f in o.data.polygons:
        f.material_index = 1 if f.normal.z < -0.9 else 0
    o.parent = rotor
    o = lathe([(0, -0.34), (0.6, -0.34), (0.74, -0.31), (0.78, -0.26), (0.78, 0.0), (0, 0.0)], segs=48,
              name="rotor_hub", mat=steel)
    o.parent = rotor
    o = lathe([(0, -0.46), (0.3, -0.45), (0.42, -0.39), (0.44, -0.34), (0, -0.34)], segs=32, name="51143_rotor_screw",
              mat=steel, smooth_angle=60 * DEG)   # the rotor's central screw
    o.parent = rotor
    # its two slotted screws, set in countersunk holes near the straight edge (they turn with it)
    for j, (sx_, sy_) in enumerate(data.get("rotor_screws", [])):
        hx, hy = -sx_ - pv[0], sy_ - pv[1]
        o = lathe([(0, -0.33), (0.4, -0.325), (0.52, -0.3), (0.54, -0.27), (0.54, 0.0), (0, 0.0)], segs=40,
                  name=f"1143_rotor_screw_{j + 1}", mat=steel, smooth_angle=60 * DEG)
        o.matrix_basis = Matrix.Translation((hx, hy, 0.0))
        o.parent = rotor
        aa = math.radians(28 + 75 * j)
        ca, sa = math.cos(aa), math.sin(aa)
        sl = [(hx + ca * u - sa * v, hy + sa * u + ca * v) for u, v in ((-0.48, -0.05), (0.48, -0.05), (0.48, 0.05), (-0.48, 0.05))]
        o = flat_plate(sl, [], -0.3, 0.045, f"1143_rotor_screw_{j + 1}_slot", [slot_m, slot_m])
        o.parent = rotor
    sl = [(u, v) for u, v in ((-0.4, -0.05), (0.4, -0.05), (0.4, 0.05), (-0.4, 0.05))]
    o = flat_plate(sl, [], -0.43, 0.04, "51143_rotor_screw_slot", [slot_m, slot_m])
    o.parent = rotor
    # its ball bearing, fixed in the plate: a dark outer ring with four notches round a satin race,
    # seen beside the rotor's straight edge
    bearing_dark = mat("Bearing ring", srgb(0x2E3034), 1, 0.22)
    o = lathe([(1.42, 0.3), (1.42, 0.0), (1.6, 0.0), (1.6, 0.3)], segs=96, name="1143_bearing_ring", mat=bearing_dark,
              close=True, smooth_angle=40 * DEG)
    o.matrix_basis = Matrix.Translation((pv[0], pv[1], Z_ROTOR + 0.03))
    o = lathe([(0.8, 0.3), (0.8, 0.08), (1.42, 0.08), (1.42, 0.3)], segs=96, name="1143_bearing_race",
              mat=M["satin"], close=True, smooth_angle=40 * DEG)
    o.matrix_basis = Matrix.Translation((pv[0], pv[1], Z_ROTOR + 0.03))
    for k in range(4):
        a = math.radians(30 + 90 * k)
        ca, sa = math.cos(a), math.sin(a)
        nb = [(pv[0] + ca * u - sa * v, pv[1] + sa * u + ca * v) for u, v in ((1.38, -0.07), (1.64, -0.07), (1.64, 0.07), (1.38, 0.07))]
        flat_plate(nb, [], Z_ROTOR + 0.33, 0.31, f"1143_bearing_notch_{k + 1}", [M["satin"], M["satin"]])
    # it turns: one revolution every 8 s, looping (baked into the GLB as an animation clip)
    sc = bpy.context.scene
    sc.render.fps = 60
    sc.frame_start, sc.frame_end = 1, 480
    rotor.rotation_mode = "XYZ"
    rotor.animation_data_clear()
    for a_ in [a_ for a_ in bpy.data.actions if a_.name.startswith("rotor_spin")]:
        bpy.data.actions.remove(a_)  # earlier builds' copies (keeps the clip named rotor_spin)
    rotor.rotation_euler.z = 0.0
    rotor.keyframe_insert("rotation_euler", index=2, frame=1)
    rotor.rotation_euler.z = -TAU
    rotor.keyframe_insert("rotation_euler", index=2, frame=481)
    act = rotor.animation_data.action
    fcs = []
    try:
        fcs = list(act.fcurves)
    except AttributeError:  # layered actions (Blender 4.4+)
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    fcs += list(bag.fcurves)
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
        fc.modifiers.new("CYCLES")
    act.name = "rotor_spin"
    rotor.rotation_euler.z = 0.0

    # the balance: 21,600 vph = 3 Hz, ~270° amplitude, 24 swings in the 8 s loop; the hairspring
    # coils follow through their shape keys (adjacent 30° keys blended)
    AMP, HZ = math.radians(270), 3.0
    for a_ in [a_ for a_ in bpy.data.actions if a_.name.startswith(("balance_swing", "hairspring_breathe"))]:
        bpy.data.actions.remove(a_)
    bal.animation_data_clear()
    if hs.data.shape_keys.animation_data:
        hs.data.shape_keys.animation_data_clear()
    bal.rotation_mode = "XYZ"
    for f in range(1, 482):
        th = AMP * math.sin(TAU * HZ * (f - 1) / 60.0)
        bal.rotation_euler.z = th
        bal.keyframe_insert("rotation_euler", index=2, frame=f)
        steps = math.degrees(th) / 30.0
        k0 = math.floor(steps)
        w1 = steps - k0
        for k, sk in keys.items():
            wv = (1 - w1) if k == k0 else (w1 if k == k0 + 1 else 0.0)
            sk.value = wv
            sk.keyframe_insert("value", frame=f)
    bal.animation_data.action.name = "balance_swing"
    # each beat (the balance through its centre, every 10 frames at 6 beats/s) the lever flips across and
    # the escape wheel steps half a tooth; 48 beats in the 8 s loop: 432° = 6 turns of its 5 spokes' symmetry
    lift = math.radians(es.get("lift_deg", 7.0))
    for o_, nm in ((lev, "pallet_lever_flip"), (esc, "escape_wheel_step")):
        for a_ in [a_ for a_ in bpy.data.actions if a_.name.startswith(nm)]:
            bpy.data.actions.remove(a_)
        o_.animation_data_clear()
        o_.rotation_mode = "XYZ"
    half = TAU / nt_ / 2
    for k in range(49):
        f0 = 1 + 10 * k
        s_ = 1 if k % 2 == 0 else -1
        for f, v in ((f0, 0.0), (f0 + 1, s_ * lift), (f0 + 9, s_ * lift)):
            if f <= 481:
                lev.rotation_euler.z = v
                lev.keyframe_insert("rotation_euler", index=2, frame=f)
        for f, v in ((f0, -half * (k + 0.5)), (f0 + 1, -half * (k + 1)), (f0 + 9, -half * (k + 1))):
            if f <= 481:
                esc.rotation_euler.z = v
                esc.keyframe_insert("rotation_euler", index=2, frame=f)
    for o_, nm in ((lev, "pallet_lever_flip"), (esc, "escape_wheel_step")):
        act_ = o_.animation_data.action
        act_.name = nm
        try:
            fcs_ = list(act_.fcurves)
        except AttributeError:
            fcs_ = [fc for layer in act_.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
        for fc in fcs_:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        o_.rotation_euler.z = 0.0
    hs.data.shape_keys.animation_data.action.name = "hairspring_breathe"
    for owner in (bal.animation_data.action, hs.data.shape_keys.animation_data.action):
        try:
            fcs_ = list(owner.fcurves)
        except AttributeError:
            fcs_ = [fc for layer in owner.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
        for fc in fcs_:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    bal.rotation_euler.z = 0.0
    for sk in keys.values():
        sk.value = 0.0


# ------------------------------------------------------------------ strap and folding clasp
def strap_path(segments, start=(18.05, -3.75), heading=-8 * DEG, step=0.4):
    """[(length, turn_degrees), ...] -> samples (s, y, z, ty, tz) in the YZ plane, going +Y."""
    y, z, h, s = start[0], start[1], heading, 0.0
    out = [(s, y, z, math.cos(h), math.sin(h))]
    for length, turn in segments:
        n = max(1, int(length / step))
        dh = -turn * DEG / n  # positive turn bends the strap downward
        for _ in range(n):
            h += dh / 2
            y += math.cos(h) * length / n
            z += math.sin(h) * length / n
            h += dh / 2
            s += length / n
            out.append((s, y, z, math.cos(h), math.sin(h)))
    return out


def strap(name, path, w0, w1, t0, t1, tip, mats, mirror=False, sec=24):
    """Sweep a padded strap section along path. Top (material 0) is alligator, underside
    (material 1) the leather lining. The case end is cut to the case's curve."""
    L = path[-1][0]
    bm = bmesh.new()
    uv_rows, rings = [], []
    for (s, y, z, ty, tz) in path:
        f = s / L
        w = w0 + (w1 - w0) * f
        t = t0 + (t1 - t0) * f
        if tip and s > L - tip:  # rounded tip
            k = (s - (L - tip)) / tip
            w *= max(0.12, math.sqrt(max(0.0, 1 - k * k)))
            t *= 1 - 0.35 * k
        ny, nz = -tz, ty
        ring = []
        for k in range(sec):
            a = TAU * k / sec
            ca, sa = math.cos(a), math.sin(a)
            x = math.copysign(abs(ca) ** 0.22, ca) * w / 2
            n = math.copysign(abs(sa) ** 0.45, sa) * t / 2
            yy, zz = y + ny * n, z + nz * n
            if s < 4.0:  # follow the case's curve at the attachment end
                yy += (math.sqrt(max(0.0, 18.05 ** 2 - x * x)) - 18.05) * (1 - s / 4.0)
            ring.append(bm.verts.new((x, -yy if mirror else yy, zz)))
        rings.append(ring)
        uv_rows.append([(x_ / 1.0) for x_ in range(sec)])
    bm.verts.ensure_lookup_table()
    uvl = bm.loops.layers.uv.new("UVMap")
    for i in range(len(rings) - 1):
        for k in range(sec):
            kk = (k + 1) % sec
            fa = bm.faces.new((rings[i][k], rings[i][kk], rings[i + 1][kk], rings[i + 1][k]))
            mid = math.sin(TAU * (k + 0.5) / sec)
            fa.material_index = 0 if mid > -0.05 else 1
            for lp, (ri, ki) in zip(fa.loops, ((i, k), (i, kk), (i + 1, kk), (i + 1, k))):
                co = rings[ri][ki].co
                w = w0 + (w1 - w0) * path[ri][0] / L
                lp[uvl].uv = (co.x / w0 + 0.5, path[ri][0] / 40.0)
    # end caps
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm_to_obj(bm, name, mats, smooth_angle=60 * DEG)


def frame_at(path, s, mirror=False):
    """Matrix placing local (x across, y along, z out of the strap's top) at arc length s."""
    p = min(path, key=lambda q: abs(q[0] - s))
    _, y, z, ty, tz = p
    T = Vector((0, ty, tz))
    N = Vector((0, -tz, ty))
    X = Vector((1, 0, 0))
    m = Matrix((X, T, N)).transposed().to_4x4()
    m.translation = (0, y, z)
    if mirror:
        m = Matrix.Diagonal((1, -1, 1, 1)) @ m
    return m


def calatrava_cross(arm_tip=5.4):
    """The Calatrava cross outline traced from the clasp close-up (blender/trace_cross.py):
    one closed polygon, arms along ±X/±Y, scaled so the arm tips sit on radius arm_tip."""
    import json
    data = json.load(open(os.path.join(ROOT, "blender", "calatrava_cross.json")))
    return [(x * arm_tip, y * arm_tip) for x, y in data["outline"]]


def keeper(name, w, t, length, wall, mat_):
    """Leather keeper loop round a strap of width w and thickness t; local X across, Y along, Z up."""
    def rrect(hw, ht, r, n=6):
        pts = []
        for cx, cy, a0 in ((hw - r, ht - r, 0), (-hw + r, ht - r, 90), (-hw + r, -ht + r, 180), (hw - r, -ht + r, 270)):
            pts += [(cx + r * math.cos(math.radians(a0 + 90 * i / n)), cy + r * math.sin(math.radians(a0 + 90 * i / n)))
                    for i in range(n + 1)]
        return pts
    inner = rrect(w / 2 + 0.15, t / 2 + 0.15, t / 2 + 0.1)
    outer = rrect(w / 2 + 0.15 + wall, t / 2 + 0.15 + wall, t / 2 + 0.1 + wall)
    o = flat_plate(outer, [inner[::-1]], length / 2, length, name, [mat_, mat_])
    o.data.transform(Matrix.Rotation(math.pi / 2, 4, "X"))  # extrusion -> along the strap
    return o


def build_strap(M):
    top = tex_mat("Alligator black", "croc_orm.png", rough=0.25, coat=0.45, coat_rough=0.18)
    nt = top.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    # colour: deep black; the ORM image drives roughness only
    img = next(n for n in nt.nodes if n.type == "TEX_IMAGE")
    img.image.colorspace_settings.name = "Non-Color"
    for l in list(img.outputs["Color"].links):
        nt.links.remove(l)
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(img.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
    nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
    bsdf.inputs["Base Color"].default_value = (*srgb(0x060608), 1)
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 0.6
    nimg = nt.nodes.new("ShaderNodeTexImage")
    nimg.image = image("croc_normal.png", "Non-Color")
    nt.links.new(nimg.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    lining = mat("Lining calf brown", srgb(0x947C66), 0, 0.65)  # sampled from the clasp photos (lit: ~156,138,123)

    # curled back as on a display cushion, but only 108° so the tails stay clear of the caseback
    # when the watch is seen from behind
    p12 = strap_path([(5, 0), (36, 108), (26, 0)])
    p6 = strap_path([(5, 0), (36, 108), (30, 0)])
    strap("strap_12", p12, 20.0, 16.0, 3.4, 2.6, 8.0, [top, lining])
    strap("strap_6", p6, 20.0, 16.0, 3.4, 2.6, 0, [top, lining], mirror=True)

    # Folding clasp on the 6 o'clock tail, as photographed (watch photos/5057G/clasp-*): a polished
    # round frame (16 mm, opening 70 % of it) with a pointed hinge tab and pin, the openwork Calatrava
    # cross set below the frame's top with its arm tips let into the frame's inner wall, the strap
    # showing through; two keepers on the watch side; the folding blade under the tail.
    L6 = p6[-1][0]
    s_clasp = L6 - 11.0
    m = frame_at(p6, s_clasp, mirror=True)         # local +Y points to the strap's free end
    t_top = 2.6 / 2
    RO, RI = 8.0, 5.6
    parts = []
    o = lathe([(RI, 0.2), (RI, 1.45), (RI + 0.28, 1.76), (RO - 0.55, 1.86), (RO - 0.15, 1.68), (RO, 1.3),
               (RO, 0.18), (RO - 0.22, 0.0), (RI + 0.3, 0.0), (RI, 0.2)], segs=128, name="clasp_frame",
              mat=M["polish"], close=True, smooth_angle=40 * DEG)
    parts.append((o, t_top - 0.25))
    # hinge tab: a pointed lug on the frame's edge, toward the blade's hinge, with its pin
    tab = [(-1.75, RO - 1.4), (-1.25, RO + 0.6)] + arc(0, RO + 1.55, 0.62, math.radians(180), 0, 14) + \
          [(1.25, RO + 0.6), (1.75, RO - 1.4)]
    o = flat_plate(tab, [], 1.78, 1.6, "clasp_tab", [M["polish"], M["polish"]])
    bv = o.modifiers.new("bevel", "BEVEL")
    bv.width, bv.segments, bv.limit_method = 0.25, 3, "ANGLE"
    parts.append((o, t_top - 0.25))
    o = lathe([(0, 0.12), (0.3, 0.1), (0.36, 0.0), (0, 0.0)], segs=24, name="clasp_pin", mat=M["satin"])
    o.location = (0, RO + 1.55, 1.78)
    parts.append((o, t_top - 0.25))
    # the cross (brushed top, like the photos), arm tips 0.15 mm into the frame
    satin = mat("WG satin (clasp cross)", srgb(0xDADBDE), 1, 0.2)
    o = flat_plate(calatrava_cross(RI + 0.15), [], 1.2, 0.55, "clasp_cross", [satin, M["polish"]])
    parts.append((o, t_top - 0.25))
    # keepers, watch side of the frame
    keep_m = mat("Keeper alligator black", srgb(0x060608), 0, 0.28, **{"Coat Weight": 0.45, "Coat Roughness": 0.18})
    for i, ds in enumerate((-RO - 3.2, -RO - 7.0)):
        o = keeper(f"strap_keeper_{i + 1}", 16.0, 2.6, 3.2, 0.75, keep_m)
        o.matrix_world = frame_at(p6, s_clasp + ds, mirror=True)
    # folding blade under the tail
    blade = [(x, y) for (x, y) in arc(0, 10.5, 6.2, 0, math.pi, 24)] + [(x, y) for (x, y) in arc(0, -10.5, 6.2, math.pi, TAU, 24)]
    hole = arc(0, 8.0, 1.7, TAU, 0, 32)
    o = flat_plate(blade, [hole], 0.0, 0.9, "clasp_blade", [M["polish"], M["polish"]])
    parts.append((o, -t_top - 0.15))
    for o, dz in parts:
        o.matrix_world = m @ Matrix.Translation((0, 0, dz)) @ o.matrix_basis


def build():
    global C
    C = coll()
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = "MILLIMETERS"
    M = materials()
    build_case(M)
    build_inside(M)
    build_strap(M)
    # one root node for the whole watch (identity transform, so nothing moves)
    root = bpy.data.objects.new("watch_5057G", None)
    root.empty_display_size = 20
    C.objects.link(root)
    for o in C.objects:
        if o is not root and o.parent is None:
            o.parent = root
    return M


if __name__ == "__main__" or True:
    M = build()
    print("built", len(C.all_objects), "objects")
