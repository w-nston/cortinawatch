# Preview studio for the 5057 build: softbox area lights, dark backdrop, camera.
# Lives in the "Studio" collection, which the GLB export leaves out.
import bpy, math
from mathutils import Vector


def studio():
    name = "Studio"
    c = bpy.data.collections.get(name)
    if c:
        for o in list(c.all_objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    for n in ("Light", "Camera"):
        o = bpy.data.objects.get(n)
        if o and o.users_collection and o.users_collection[0].name == "Scene Collection":
            bpy.data.objects.remove(o, do_unlink=True)

    def area(name, loc, size, power, color=(1, 1, 1), shape="RECTANGLE", size_y=None):
        d = bpy.data.lights.new(name, "AREA")
        d.shape = shape
        d.size = size
        if size_y:
            d.size_y = size_y
        d.energy = power
        d.color = color
        o = bpy.data.objects.new(name, d)
        c.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        return o

    # power scales with distance squared, so these are large: the scene is in mm
    K = 0.35e6  # calibrated so matte surfaces (dial print, strap lining) expose like the photos
    key = area("key_softbox", (-90, 70, 160), 120, 1.0 * K, size_y=60)
    key.visible_glossy = False  # keeps a big white square out of the crystal
    area("fill_strip", (140, -40, 60), 25, 0.25 * K, size_y=180)
    area("rim_strip", (-30, -150, 50), 25, 0.3 * K, size_y=160)
    area("top_strip", (60, 120, 120), 20, 0.2 * K, size_y=140)
    under = area("under_strip", (-60, 40, -150), 20, 0.25 * K, size_y=160)
    under.visible_glossy = False  # keeps a white bar out of the caseback sapphire

    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        if n.type not in ("BACKGROUND", "OUTPUT_WORLD"):
            nt.nodes.remove(n)
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    # studio sweep for reflections: a bright ring of softbox light between 30° and 70°
    # elevation, a dark "black card" straight overhead (so a dial seen face-on stays dark,
    # as in product photography) and a dark floor; the camera sees a near-black backdrop
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    stops = [(0.0, 0.012), (0.2, 0.15), (0.42, 0.18), (0.52, 0.07), (0.62, 0.33), (0.72, 0.57), (0.9, 0.36), (0.96, 0.03), (1.0, 0.012)]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (stops[0][1],) * 3 + (1,)
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], (stops[-1][1],) * 3 + (1,)
    for p, v in stops[1:-1]:
        e = cr.elements.new(p)
        e.color = (v, v, v * 1.03, 1)
    mapr = nt.nodes.new("ShaderNodeMapRange")
    mapr.inputs["From Min"].default_value = -1
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mapr.inputs["Value"])
    nt.links.new(mapr.outputs["Result"], ramp.inputs["Fac"])
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.inputs[2].default_value = (0.008, 0.008, 0.01, 1)
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(ramp.outputs["Color"], mix.inputs[1])
    nt.links.new(mix.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 1.0
    nt.links.new(bg.outputs[0], out.inputs[0])

    cd = bpy.data.cameras.new("cam")
    cd.lens = 100
    cd.clip_start = 1
    cd.clip_end = 5000
    cam = bpy.data.objects.new("cam", cd)
    c.objects.link(cam)
    bpy.context.scene.camera = cam
    set_view("front")

    sc = bpy.context.scene
    try:
        sc.render.engine = "CYCLES"
    except TypeError as e:
        print(e)
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 1200
    sc.render.resolution_y = 1200
    sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else sc.view_settings.view_transform
    for a in bpy.context.screen.areas if bpy.context.screen else []:
        if a.type == "VIEW_3D":
            for s in a.spaces:
                if s.type == "VIEW_3D":
                    s.clip_start, s.clip_end = 0.5, 10000


VIEWS = {
    "front": ((0, 0, 260), (0, 0, 0)),
    "back": ((0, 0, -260), (0, 0, -3)),
    "angle": ((95, -85, 200), (0, 0, -1)),
    "side": ((260, 0, -2.3), (0, 0, -2.3)),
    "macro": ((-40, -45, 70), (-4, -5, 0)),
    "lug": ((80, 120, 60), (8, 14, -2)),
}


def set_view(v):
    cam = bpy.data.objects["cam"]
    loc, tgt = VIEWS[v]
    cam.location = loc
    up = "Y" if v not in ("side",) else "Z"
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", up).to_euler()


studio()
