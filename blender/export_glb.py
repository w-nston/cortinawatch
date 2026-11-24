# Export the built watch (collection Watch<VARIANT>) to assets/models/<VARIANT>.glb (5057G or 5057R).
# Keeps Blender's axes (no +Y-up conversion) so the GLB uses the same frame as js/watch5057.js:
# +X crown, +Y 12 o'clock, +Z out of the dial, 1 unit = 1 mm.
# Sized for phones (~4.2 MB instead of ~9.5): meshes Draco-compressed (positions to 14 bits, ~0.003 mm
# over the watch), the hairspring's breathing shape keys without their normals, the strap's croc grain
# at 1024 px. The page decodes Draco with vendor/three/addons/loaders/DRACOLoader.js.
import bpy, os

ROOT = globals().get("CORTINA_ROOT")
VARIANT = globals().get("VARIANT", "5057G")
out = os.path.join(ROOT, "assets", "models", f"{VARIANT}.glb")
os.makedirs(os.path.dirname(out), exist_ok=True)

for o in bpy.context.view_layer.objects:
    o.select_set(False)
for o in bpy.data.collections["Watch" + VARIANT].all_objects:
    o.hide_set(False)
    o.select_set(True)
# the strap's croc grain: half the size, no loss you can see at the strap's scale
for img in bpy.data.images:
    if img.name.startswith("croc_normal") and img.size[0] > 1024:
        img.scale(1024, 1024)

kw = dict(filepath=out, export_format="GLB", use_selection=True, export_yup=False, export_apply=True,
          export_cameras=False, export_lights=False, export_extras=False, export_image_format="WEBP",
          export_image_quality=88, export_tangents=False,
          export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
          export_anim_single_armature=False,  # the mini-rotor's spin ("rotor_spin") rides along
          export_morph_normal=False,
          export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7,
          export_draco_position_quantization=14, export_draco_normal_quantization=10,
          export_draco_texcoord_quantization=12, export_draco_color_quantization=10,
          export_draco_generic_quantization=12)
props = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
for k in [k for k in kw if k not in props]:
    print("exporter has no option", k)
    kw.pop(k)
bpy.ops.export_scene.gltf(**kw)
print("wrote", out, os.path.getsize(out) // 1024, "KB")
