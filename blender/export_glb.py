# Export the Watch5057G collection to assets/models/5057G.glb.
# Keeps Blender's axes (no +Y-up conversion) so the GLB uses the same frame as js/watch5057.js:
# +X crown, +Y 12 o'clock, +Z out of the dial, 1 unit = 1 mm.
import bpy, os

ROOT = globals().get("CORTINA_ROOT")
out = os.path.join(ROOT, "assets", "models", "5057G.glb")
os.makedirs(os.path.dirname(out), exist_ok=True)

for o in bpy.context.view_layer.objects:
    o.select_set(False)
for o in bpy.data.collections["Watch5057G"].all_objects:
    o.hide_set(False)
    o.select_set(True)

kw = dict(filepath=out, export_format="GLB", use_selection=True, export_yup=False, export_apply=True,
          export_cameras=False, export_lights=False, export_extras=False, export_image_format="WEBP",
          export_image_quality=88, export_tangents=False,
          export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
          export_anim_single_armature=False)  # the mini-rotor's spin ("rotor_spin") rides along
props = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
for k in [k for k in kw if k not in props]:
    print("exporter has no option", k)
    kw.pop(k)
bpy.ops.export_scene.gltf(**kw)
print("wrote", out, os.path.getsize(out) // 1024, "KB")
