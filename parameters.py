import bpy

from .materials import *
from .nodes import *
from .physics import *
from .utils import *
from .vars import *


def set_node_from_property(node):
    props = bpy.context.scene.CC3ImportProps
    name = node.name

    # BASE COLOR
    #
    if "(color_" in name and "_mixer)" in name:
        # color_skin_<part>_mixer
        if "_skin_" in name:
            set_node_input(node, "AO Strength", props.skin_ao)
            set_node_input(node, "Blend Strength", props.skin_blend)
            set_node_input(node, "Mouth AO", props.skin_mouth_ao)
            set_node_input(node, "Nostril AO", props.skin_nostril_ao)
            set_node_input(node, "Lips AO", props.skin_lips_ao)
        # color_eye_mixer
        elif "_eye_" in name:
            set_node_input(node, "AO Strength", props.eye_ao)
            set_node_input(node, "Blend Strength", props.eye_blend)
            set_node_input(node, "Shadow Radius", props.eye_shadow_radius)
            set_node_input(node, "Shadow Hardness", props.eye_shadow_hardness * props.eye_shadow_radius * 0.99)
            set_node_input(node, "Corner Shadow", props.eye_shadow_color)
            set_node_input(node, "Sclera Brightness", props.eye_sclera_brightness)
            set_node_input(node, "Iris Brightness", props.eye_iris_brightness)
        # color_hair_mixer
        elif "_hair_" in name or "_scalp_" in name:
            set_node_input(node, "AO Strength", props.hair_ao)
            set_node_input(node, "Blend Strength", props.hair_blend)
        # color_teeth_mixer
        elif "_teeth_" in name:
            set_node_input(node, "AO Strength", props.teeth_ao)
            set_node_input(node, "Front", props.teeth_front)
            set_node_input(node, "Rear", props.teeth_rear)
            set_node_input(node, "Teeth Brightness", props.teeth_teeth_brightness)
            set_node_input(node, "Teeth Saturation", 1 - props.teeth_teeth_desaturation)
            set_node_input(node, "Gums Brightness", props.teeth_gums_brightness)
            set_node_input(node, "Gums Saturation", 1 - props.teeth_gums_desaturation)
        # color_tongue_mixer
        elif "_tongue_" in name:
            set_node_input(node, "AO Strength", props.tongue_ao)
            set_node_input(node, "Front", props.tongue_front)
            set_node_input(node, "Rear", props.tongue_rear)
            set_node_input(node, "Brightness", props.tongue_brightness)
            set_node_input(node, "Saturation", 1 - props.tongue_desaturation)
        # color_nails_mixer
        elif "_nails_" in name:
            set_node_input(node, "AO Strength", props.nails_ao)
        # color_default_mixer
        elif "_default_" in name:
            set_node_input(node, "AO Strength", props.default_ao)
            set_node_input(node, "Blend Strength", props.default_blend)


    # SUBSURFACE
    #
    elif "(subsurface_" in name and "_mixer)" in name:
        # subsurface_skin_<part>_mixer
        if "_skin_" in name:
            set_node_input(node, "Radius", props.skin_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff", props.skin_sss_falloff)
        # subsurface_eye_mixer
        elif "_eye_" in name:
            set_node_input(node, "Radius1", props.eye_sss_radius * UNIT_SCALE)
            set_node_input(node, "Radius2", props.eye_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff1", props.eye_sss_falloff)
            set_node_input(node, "Falloff2", props.eye_sss_falloff)
        # subsurface_hair_mixer
        elif "_hair_" in name or "_scalp_" in name:
            set_node_input(node, "Radius", props.hair_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff", props.hair_sss_falloff)
        # subsurface_teeth_mixer
        elif "_teeth_" in name:
            set_node_input(node, "Radius1", props.teeth_sss_radius * UNIT_SCALE)
            set_node_input(node, "Radius2", props.teeth_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff1", props.teeth_sss_falloff)
            set_node_input(node, "Falloff2", props.teeth_sss_falloff)
            set_node_input(node, "Scatter1", props.teeth_gums_sss_scatter)
            set_node_input(node, "Scatter2", props.teeth_teeth_sss_scatter)
        # subsurface_tongue_mixer
        elif "_tongue_" in name:
            set_node_input(node, "Scatter", props.tongue_sss_scatter)
            set_node_input(node, "Radius", props.tongue_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff", props.tongue_sss_falloff)
        # subsurface_nails_mixer
        elif "_nails_" in name:
            set_node_input(node, "Radius", props.nails_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff", props.nails_sss_falloff)
        # subsurface_default_mixer
        elif "_default_" in name:
            set_node_input(node, "Radius", props.default_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff", props.default_sss_falloff)


    # MSR
    #
    elif "(msr_" in name and "_mixer)" in name:
        # msr_skin_<part>_mixer
        if "_skin_" in name:
            set_node_input(node, "Roughness Remap", props.skin_roughness)
            set_node_input(node, "Specular", props.skin_specular)
        # msr_eye_mixer
        elif "_eye_" in name:
            set_node_input(node, "Specular1", props.eye_specular)
            set_node_input(node, "Specular2", props.eye_specular)
            set_node_input(node, "Roughness1", props.eye_sclera_roughness)
            set_node_input(node, "Roughness2", props.eye_iris_roughness)
        # msr_hair_mixer
        elif "_hair_" in name:
            set_node_input(node, "Roughness Remap", props.hair_roughness)
            set_node_input(node, "Specular", props.hair_specular)
        # msr_scalp_mixer
        elif "_scalp_" in name:
            set_node_input(node, "Roughness Remap", props.hair_scalp_roughness)
            set_node_input(node, "Specular", props.hair_scalp_specular)
        # msr_teeth_mixer
        elif "_teeth_" in name:
            set_node_input(node, "Specular2", props.teeth_specular)
        # msr_tongue_mixer
        elif "_tongue_" in name:
            set_node_input(node, "Specular2", props.tongue_specular)
        # msr_nails_mixer
        elif "_nails_" in name:
            set_node_input(node, "Roughness Remap", props.nails_roughness)
            set_node_input(node, "Specular", props.nails_specular)
        elif "_default_" in name:
            set_node_input(node, "Roughness Remap", props.default_roughness)

    elif "teeth_roughness" in name:
        set_node_input(node, 1, props.teeth_roughness)
    elif "tongue_roughness" in name:
        set_node_input(node, 1, props.tongue_roughness)

    # NORMAL
    #
    elif "(normal_" in name and "_mixer)" in name:
        # normal_skin_<part>_mixer
        if "skin_head" in name:
            set_node_input(node, "Normal Blend Strength", props.skin_normal_blend)
            set_node_input(node, "Micro Normal Strength", props.skin_head_micronormal)
        elif "skin_body" in name:
            set_node_input(node, "Normal Blend Strength", props.skin_normal_blend)
            set_node_input(node, "Micro Normal Strength", props.skin_body_micronormal)
        elif "skin_arm" in name:
            set_node_input(node, "Normal Blend Strength", props.skin_normal_blend)
            set_node_input(node, "Micro Normal Strength", props.skin_arm_micronormal)
        elif "skin_leg" in name:
            set_node_input(node, "Normal Blend Strength", props.skin_normal_blend)
            set_node_input(node, "Micro Normal Strength", props.skin_leg_micronormal)
        # normal_eye_mixer
        elif "_eye_" in name:
            set_node_input(node, "Micro Normal Strength", 1 - props.eye_sclera_normal)
        # normal_hair_mixer
        elif "_hair_" in name or "_scalp_" in name:
            set_node_input(node, "Bump Map Height", props.hair_bump / 1000)
        # normal_teeth_mixer
        elif "_teeth_" in name:
            set_node_input(node, "Micro Normal Strength", props.teeth_micronormal)
        # normal_tongue_mixer
        elif "_tongue_" in name:
            set_node_input(node, "Micro Normal Strength", props.tongue_micronormal)
        # normal_nails_mixer
        elif "_nails_" in name:
            set_node_input(node, "Micro Normal Strength", props.nails_micronormal)
        # normal_default_mixer
        elif "_default_" in name:
            set_node_input(node, "Normal Blend Strength", props.default_normal_blend)
            set_node_input(node, "Micro Normal Strength", props.default_micronormal)
            set_node_input(node, "Bump Map Height", props.default_bump / 1000)

    # TILING
    #
    elif "(tiling_" in name and "_mapping)" in name:
        # tiling_skin_<part>_mapping
        if "skin_head" in name:
            set_node_input(node, "Tiling", props.skin_head_tiling)
        elif "skin_body" in name:
            set_node_input(node, "Tiling", props.skin_body_tiling)
        elif "skin_arm" in name:
            set_node_input(node, "Tiling", props.skin_arm_tiling)
        elif "skin_leg" in name:
            set_node_input(node, "Tiling", props.skin_leg_tiling)
        # tiling_sclera_normal_mapping
        elif "_normal_sclera_" in name:
            set_node_input(node, "Tiling", props.eye_sclera_tiling)
        # tiling_sclera_color_mapping
        elif "_color_sclera_" in name:
            set_node_input(node, "Tiling", 1.0 / props.eye_sclera_scale)
        # tiling_teeth_mapping
        elif "_teeth_" in name:
            set_node_input(node, "Tiling", props.teeth_tiling)
        # tiling_tongue_mapping
        elif "_tongue_" in name:
            set_node_input(node, "Tiling", props.tongue_tiling)
        # tiling_nails_mapping
        elif "_nails_" in name:
            set_node_input(node, "Tiling", props.nails_tiling)
        # tiling_default_mapping
        elif "_default_" in name:
            set_node_input(node, "Tiling", props.default_tiling)

    # MASKS
    #
    elif "iris_mask" in name:
        set_node_input(node, "Scale", 1.0 / props.eye_iris_scale)
        set_node_input(node, "Radius", props.eye_iris_radius)
        set_node_input(node, "Hardness", props.eye_iris_radius * props.eye_iris_hardness * 0.99)
    elif "eye_occlusion_mask" in name:
        set_node_input(node, "Strength", props.eye_occlusion)

    # BASIC
    #
    elif "skin_ao" in name:
        set_node_output(node, "Value", props.skin_ao)
    elif "skin_basic_specular" in name:
        set_node_output(node, "Value", props.skin_basic_specular)
    elif "skin_basic_roughness" in name:
        set_node_input(node, "To Min", props.skin_basic_roughness)
    elif "eye_specular" in name:
        set_node_output(node, "Value", props.eye_specular)
    elif "teeth_specular" in name:
        set_node_output(node, "Value", props.teeth_specular)
    elif "teeth_roughess" in name:
        set_node_input(node, 1, props.teeth_roughness)
    elif "tongue_specular" in name:
        set_node_output(node, "Value", props.tongue_specular)
    elif "nails_specular" in name:
        set_node_output(node, "Value", props.nails_specular)
    elif "eye_basic_roughness" in name:
        set_node_output(node, "Value", props.eye_basic_roughness)
    elif "eye_basic_normal" in name:
        set_node_output(node, "Value", props.eye_basic_normal)
    elif "eye_basic_hsv" in name:
        set_node_input(node, "Value", props.eye_basic_brightness)
    elif "hair_ao" in name:
        set_node_output(node, "Value", props.hair_ao)
    elif "hair_specular" in name:
        set_node_output(node, "Value", props.hair_specular)
    elif "scalp_specular" in name:
        set_node_output(node, "Value", props.hair_scalp_specular)
    elif "hair_bump" in name:
        set_node_output(node, "Value", props.hair_bump / 1000)
    elif "default_ao" in name:
        set_node_output(node, "Value", props.default_ao)
    elif "default_bump" in name:
        set_node_output(node, "Value", props.default_bump / 1000)

    # Other
    elif "eye_tearline_shader" in name:
        set_node_input(node, "Alpha", props.eye_tearline_alpha)
        set_node_input(node, "Roughness", props.eye_tearline_roughness)


def refresh_parameters(mat):

    if (mat.node_tree is None):
        log_warn("No node tree!")
        return

    for node in mat.node_tree.nodes:

        if NODE_PREFIX in node.name:
            set_node_from_property(node)

def reset_preferences():
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    prefs.lighting = "ENABLED"
    prefs.physics = "ENABLED"
    prefs.quality_lighting = "STUDIO"
    prefs.pipeline_lighting = "CC3"
    prefs.morph_lighting = "MATCAP"
    prefs.quality_mode = "ADVANCED"
    prefs.pipeline_mode = "BASIC"
    prefs.morph_mode = "COMPAT"
    prefs.log_level = "ERRORS"

def reset_parameters(context = bpy.context):
    global block_update
    props = bpy.context.scene.CC3ImportProps

    block_update = True

    props.skin_ao = 1.0
    props.skin_blend = 0.0
    props.skin_normal_blend = 0.0
    props.skin_roughness = 0.15
    props.skin_specular = 0.4
    props.skin_basic_specular = 0.4
    props.skin_basic_roughness = 0.15
    props.skin_sss_radius = 1.5
    props.skin_sss_falloff = (1.0, 0.112, 0.072, 1.0)
    props.skin_head_micronormal = 0.5
    props.skin_body_micronormal = 0.8
    props.skin_arm_micronormal = 1.0
    props.skin_leg_micronormal = 1.0
    props.skin_head_tiling = 25
    props.skin_body_tiling = 20
    props.skin_arm_tiling = 20
    props.skin_leg_tiling = 20
    props.skin_mouth_ao = 2.5
    props.skin_nostril_ao = 2.5
    props.skin_lips_ao = 2.5

    props.eye_ao = 0.2
    props.eye_blend = 0.0
    props.eye_specular = 0.8
    props.eye_sclera_roughness = 0.2
    props.eye_iris_roughness = 0.0
    props.eye_iris_scale = 1.0
    props.eye_sclera_scale = 1.0
    props.eye_iris_radius = 0.13
    props.eye_iris_hardness = 0.85
    props.eye_sss_radius = 1.0
    props.eye_sss_falloff = (1.0, 1.0, 1.0, 1.0)
    props.eye_sclera_normal = 0.9
    props.eye_sclera_tiling = 2.0
    props.eye_basic_roughness = 0.05
    props.eye_basic_normal = 0.1
    props.eye_shadow_radius = 0.3
    props.eye_shadow_hardness = 0.5
    props.eye_shadow_color = (1.0, 0.497, 0.445, 1.0)
    props.eye_occlusion = 0.5
    props.eye_sclera_brightness = 0.75
    props.eye_iris_brightness = 1.0
    props.eye_basic_brightness = 0.9
    props.eye_tearline_alpha = 0.05
    props.eye_tearline_roughness = 0.15

    props.teeth_ao = 1.0
    props.teeth_gums_brightness = 0.9
    props.teeth_teeth_brightness = 0.7
    props.teeth_gums_desaturation = 0.0
    props.teeth_teeth_desaturation = 0.1
    props.teeth_front = 1.0
    props.teeth_rear = 0.0
    props.teeth_specular = 0.25
    props.teeth_roughness = 0.4
    props.teeth_gums_sss_scatter = 1.0
    props.teeth_teeth_sss_scatter = 0.5
    props.teeth_sss_radius = 1.0
    props.teeth_sss_falloff = (0.381, 0.198, 0.13, 1.0)
    props.teeth_micronormal = 0.3
    props.teeth_tiling = 10

    props.tongue_ao = 1.0
    props.tongue_brightness = 1.0
    props.tongue_desaturation = 0.05
    props.tongue_front = 1.0
    props.tongue_rear = 0.0
    props.tongue_specular = 0.259
    props.tongue_roughness = 1.0
    props.tongue_sss_scatter = 1.0
    props.tongue_sss_radius = 1.0
    props.tongue_sss_falloff = (1,1,1, 1.0)
    props.tongue_micronormal = 0.5
    props.tongue_tiling = 4

    props.nails_ao = 1.0
    props.nails_specular = 0.4
    props.nails_roughness = 0.0
    props.nails_sss_radius = 1.5
    props.nails_sss_falloff = (1.0, 0.112, 0.072, 1.0)
    props.nails_micronormal = 1.0
    props.nails_tiling = 42

    props.hair_ao = 1.0
    props.hair_blend = 0.0
    props.hair_specular = 0.5
    props.hair_roughness = 0.0
    props.hair_scalp_specular = 0.0
    props.hair_scalp_roughness = 0.0
    props.hair_sss_radius = 1.0
    props.hair_sss_falloff = (1.0, 1.0, 1.0, 1.0)
    props.hair_bump = 1

    props.default_ao = 1.0
    props.default_blend = 0.0
    props.default_roughness = 0.0
    props.default_normal_blend = 0.0
    props.default_sss_radius = 1.0
    props.default_sss_falloff = (1.0, 1.0, 1.0, 1.0)

    props.default_micronormal = 0.5
    props.default_tiling = 10
    props.default_bump = 5

    block_update = False
    quick_set_execute("UPDATE_ALL", context)

    return


def quick_set_update(self, context):
    global block_update
    if not block_update:
        quick_set_execute("UPDATE_ALL", context)


def physics_strength_update(self, context):
    props = bpy.context.scene.CC3ImportProps

    if bpy.context.mode == "PAINT_TEXTURE":
        s = props.physics_strength
        bpy.context.scene.tool_settings.unified_paint_settings.color = (s, s, s)


class CC3ObjectPointer(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)


class CC3ImportProps(bpy.types.PropertyGroup):

    node_id: bpy.props.IntProperty(default=1000)

    setup_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic","Build basic PBR materials."),
                        ("ADVANCED","Advanced","Build advanced materials with blend maps, subsurface, and micro normals, specular and roughness control and includes layered eye, teeth and tongue materials.")
                    ], default="BASIC")

    build_mode: bpy.props.EnumProperty(items=[
                        ("IMPORTED","All Imported","Build materials for all the imported objects."),
                        ("SELECTED","Only Selected","Build materials only for the selected objects.")
                    ], default="IMPORTED")

    blend_mode: bpy.props.EnumProperty(items=[
                        ("BLEND","Alpha Blend","Setup any non opaque materials as basic Alpha Blend"),
                        ("HASHED","Alpha Hashed","Setup non opaque materials as alpha hashed (Resolves Z sorting issues, but may need more samples)")
                    ], default="BLEND")

    update_mode: bpy.props.EnumProperty(items=[
                        ("UPDATE_ALL","All Imported","Update the shader parameters for all objects from the last import"),
                        ("UPDATE_SELECTED","Selected Only","Update the shader parameters only in the selected objects")
                    ], default="UPDATE_ALL")

    open_mouth: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=open_mouth_update)
    physics_strength: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=physics_strength_update)
    physics_tex_size: bpy.props.EnumProperty(items=[
                        ("64","64 x 64","64 x 64 texture size"),
                        ("128","128 x 128","128 x 128 texture size"),
                        ("256","256 x 256","256 x 256 texture size"),
                        ("512","512 x 512","512 x 512 texture size"),
                        ("1024","1024 x 1024","1024 x 1024 texture size"),
                        ("2048","2048 x 2048","2048 x 2048 texture size"),
                        ("4096","4096 x 4096","4096 x 4096 texture size"),
                    ], default="1024")

    import_file: bpy.props.StringProperty(default="", subtype="FILE_PATH")
    import_objects: bpy.props.CollectionProperty(type=CC3ObjectPointer)
    material_cache: bpy.props.CollectionProperty(type=CC3MaterialCache)
    object_cache: bpy.props.CollectionProperty(type=CC3ObjectCache)
    import_type: bpy.props.StringProperty(default="")
    import_name: bpy.props.StringProperty(default="")
    import_dir: bpy.props.StringProperty(default="")
    import_embedded: bpy.props.BoolProperty(default=False)
    import_main_tex_dir: bpy.props.StringProperty(default="")
    import_space_in_name: bpy.props.BoolProperty(default=False)
    import_haskey: bpy.props.BoolProperty(default=False)
    import_key_file: bpy.props.StringProperty(default="")

    paint_object: bpy.props.PointerProperty(type=bpy.types.Object)
    paint_material: bpy.props.PointerProperty(type=bpy.types.Material)
    paint_image: bpy.props.PointerProperty(type=bpy.types.Image)

    quick_set_mode: bpy.props.EnumProperty(items=[
                        ("OBJECT","Object","Set the alpha blend mode and backface culling to all materials on the selected object(s)"),
                        ("MATERIAL","Material","Set the alpha blend mode and backface culling only to the selected material on the active object"),
                    ], default="OBJECT")
    paint_store_render: bpy.props.StringProperty(default="")

    lighting_mode: bpy.props.EnumProperty(items=[
                        ("OFF","No Lighting","No automatic lighting and render settings."),
                        ("ON","Lighting","Automatically sets lighting and render settings, depending on use."),
                    ], default="OFF")
    physics_mode: bpy.props.EnumProperty(items=[
                        ("OFF","No Physics","No generated physics."),
                        ("ON","Physics","Automatically generates physics vertex groups and settings."),
                    ], default="ON")

    stage1: bpy.props.BoolProperty(default=True)
    stage1_details: bpy.props.BoolProperty(default=False)
    stage2: bpy.props.BoolProperty(default=True)
    stage3: bpy.props.BoolProperty(default=True)
    stage4: bpy.props.BoolProperty(default=True)
    stage5: bpy.props.BoolProperty(default=True)
    stage6: bpy.props.BoolProperty(default=True)

    skin_basic_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    skin_basic_roughness: bpy.props.FloatProperty(default=0.15, min=0, max=1, update=quick_set_update)
    eye_basic_roughness: bpy.props.FloatProperty(default=0.05, min=0, max=1, update=quick_set_update)
    eye_basic_normal: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=quick_set_update)
    eye_basic_brightness: bpy.props.FloatProperty(default=0.9, min=0, max=2, update=quick_set_update)

    skin_toggle: bpy.props.BoolProperty(default=True)
    skin_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    skin_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    skin_normal_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    skin_roughness: bpy.props.FloatProperty(default=0.15, min=0, max=1, update=quick_set_update)
    skin_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    skin_sss_radius: bpy.props.FloatProperty(default=1.5, min=0.1, max=5, update=quick_set_update)
    skin_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 0.112, 0.072, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    skin_head_micronormal: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    skin_body_micronormal: bpy.props.FloatProperty(default=0.8, min=0, max=1, update=quick_set_update)
    skin_arm_micronormal: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    skin_leg_micronormal: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    skin_head_tiling: bpy.props.FloatProperty(default=25, min=0, max=50, update=quick_set_update)
    skin_body_tiling: bpy.props.FloatProperty(default=20, min=0, max=50, update=quick_set_update)
    skin_arm_tiling: bpy.props.FloatProperty(default=20, min=0, max=50, update=quick_set_update)
    skin_leg_tiling: bpy.props.FloatProperty(default=20, min=0, max=50, update=quick_set_update)
    skin_mouth_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=quick_set_update)
    skin_nostril_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=quick_set_update)
    skin_lips_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=quick_set_update)


    eye_toggle: bpy.props.BoolProperty(default=True)
    eye_ao: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=quick_set_update)
    eye_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    eye_specular: bpy.props.FloatProperty(default=0.8, min=0, max=2, update=quick_set_update)
    eye_sclera_roughness: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=quick_set_update)
    eye_iris_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    eye_iris_scale: bpy.props.FloatProperty(default=1.0, min=0.5, max=1.5, update=quick_set_update)
    eye_iris_radius: bpy.props.FloatProperty(default=0.13, min=0.1, max=0.15, update=quick_set_update)
    eye_iris_hardness: bpy.props.FloatProperty(default=0.85, min=0, max=1, update=quick_set_update)
    eye_sclera_scale: bpy.props.FloatProperty(default=1.0, min=0.5, max=1.5, update=quick_set_update)
    eye_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=quick_set_update)
    eye_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    eye_sclera_normal: bpy.props.FloatProperty(default=0.9, min=0, max=1, update=quick_set_update)
    eye_sclera_tiling: bpy.props.FloatProperty(default=2.0, min=0, max=10, update=quick_set_update)
    eye_shadow_hardness: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    eye_shadow_radius: bpy.props.FloatProperty(default=0.3, min=0, max=0.5, update=quick_set_update)
    eye_shadow_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 0.497, 0.445, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    eye_occlusion: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    eye_sclera_brightness: bpy.props.FloatProperty(default=0.75, min=0, max=5, update=quick_set_update)
    eye_iris_brightness: bpy.props.FloatProperty(default=1.0, min=0, max=5, update=quick_set_update)

    eye_tearline_alpha: bpy.props.FloatProperty(default=0.05, min=0, max=0.2, update=quick_set_update)
    eye_tearline_roughness: bpy.props.FloatProperty(default=0.15, min=0, max=0.5, update=quick_set_update)

    teeth_toggle: bpy.props.BoolProperty(default=True)
    teeth_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    teeth_gums_brightness: bpy.props.FloatProperty(default=0.9, min=0, max=2, update=quick_set_update)
    teeth_teeth_brightness: bpy.props.FloatProperty(default=0.7, min=0, max=2, update=quick_set_update)
    teeth_gums_desaturation: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    teeth_teeth_desaturation: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=quick_set_update)
    teeth_front: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    teeth_rear: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    teeth_specular: bpy.props.FloatProperty(default=0.25, min=0, max=2, update=quick_set_update)
    teeth_roughness: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    teeth_gums_sss_scatter: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=quick_set_update)
    teeth_teeth_sss_scatter: bpy.props.FloatProperty(default=0.5, min=0, max=2, update=quick_set_update)
    teeth_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=quick_set_update)
    teeth_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(0.381, 0.198, 0.13, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    teeth_micronormal: bpy.props.FloatProperty(default=0.3, min=0, max=1, update=quick_set_update)
    teeth_tiling: bpy.props.FloatProperty(default=10, min=0, max=50, update=quick_set_update)

    tongue_toggle: bpy.props.BoolProperty(default=True)
    tongue_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    tongue_brightness: bpy.props.FloatProperty(default=1, min=0, max=2, update=quick_set_update)
    tongue_desaturation: bpy.props.FloatProperty(default=0.05, min=0, max=1, update=quick_set_update)
    tongue_front: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    tongue_rear: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    tongue_specular: bpy.props.FloatProperty(default=0.259, min=0, max=2, update=quick_set_update)
    tongue_roughness: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=quick_set_update)
    tongue_sss_scatter: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=quick_set_update)
    tongue_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=quick_set_update)
    tongue_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(1, 1, 1, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    tongue_micronormal: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    tongue_tiling: bpy.props.FloatProperty(default=4, min=0, max=50, update=quick_set_update)

    nails_toggle: bpy.props.BoolProperty(default=True)
    nails_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    nails_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    nails_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    nails_sss_radius: bpy.props.FloatProperty(default=1.5, min=0.1, max=3, update=quick_set_update)
    nails_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(1.0, 0.112, 0.072, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    nails_micronormal: bpy.props.FloatProperty(default=1, min=0, max=1, update=quick_set_update)
    nails_tiling: bpy.props.FloatProperty(default=42, min=0, max=50, update=quick_set_update)

    hair_toggle: bpy.props.BoolProperty(default=True)
    hair_hint: bpy.props.StringProperty(default="hair,beard", update=quick_set_update)
    hair_object: bpy.props.PointerProperty(type=bpy.types.Object, update=quick_set_update)
    hair_scalp_hint: bpy.props.StringProperty(default="scalp,base", update=quick_set_update)
    hair_specular: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    hair_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_scalp_specular: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_scalp_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    hair_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    hair_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=quick_set_update)
    hair_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    hair_bump: bpy.props.FloatProperty(default=1, min=0, max=10, update=quick_set_update)

    default_toggle: bpy.props.BoolProperty(default=True)
    default_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    default_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    default_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    default_normal_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    default_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=3, update=quick_set_update)
    default_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    default_micronormal: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    default_tiling: bpy.props.FloatProperty(default=10, min=0, max=100, update=quick_set_update)
    default_bump: bpy.props.FloatProperty(default=5, min=0, max=10, update=quick_set_update)


class CC3ToolsAddonPreferences(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__.partition(".")[0]

    lighting: bpy.props.EnumProperty(items=[
                        ("DISABLED","Disabled","No automatic lighting and render settings."),
                        ("ENABLED","Enabled","Allows automatic lighting and render settings."),
                    ], default="ENABLED", name = "Automatic Lighting")

    physics: bpy.props.EnumProperty(items=[
                        ("DISABLED","Disabled","No physics auto setup."),
                        ("ENABLED","Enabled","Allows automatic physics setup from physX weight maps."),
                    ], default="ENABLED", name = "Generate Physics")

    quality_lighting: bpy.props.EnumProperty(items=[
                        ("BLENDER","Blender Default","Blenders default lighting setup"),
                        ("MATCAP","Solid Matcap","Solid shading matcap lighting for sculpting / mesh editing"),
                        ("CC3","CC3 Default","Replica of CC3 default lighting setup"),
                        ("STUDIO","Studio Right","Right facing 3 point lighting with the studio hdri"),
                        ("COURTYARD","Courtyard Left","Left facing soft 3 point lighting with the courtyard hdri"),
                    ], default="STUDIO", name = "Render / Quality Lighting")

    pipeline_lighting: bpy.props.EnumProperty(items=[
                        ("BLENDER","Blender Default","Blenders default lighting setup"),
                        ("MATCAP","Solid Matcap","Solid shading matcap lighting for sculpting / mesh editing"),
                        ("CC3","CC3 Default","Replica of CC3 default lighting setup"),
                        ("STUDIO","Studio Right","Right facing 3 point lighting with the studio hdri"),
                        ("COURTYARD","Courtyard Left","Left facing soft 3 point lighting with the courtyard hdri"),
                    ], default="CC3", name = "(FBX) Accessory Editing Lighting")

    morph_lighting: bpy.props.EnumProperty(items=[
                        ("BLENDER","Blender Default","Blenders default lighting setup"),
                        ("MATCAP","Solid Matcap","Solid shading matcap lighting for sculpting / mesh editing"),
                        ("CC3","CC3 Default","Replica of CC3 default lighting setup"),
                        ("STUDIO","Studio Right","Right facing 3 point lighting with the studio hdri"),
                        ("COURTYARD","Courtyard Left","Left facing soft 3 point lighting with the courtyard hdri"),
                    ], default="MATCAP", name = "(OBJ) Morph Edit Lighting")

    quality_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic Materials","Build basic PBR materials for quality / rendering"),
                        ("ADVANCED","Advanced Materials","Build advanced materials for quality / rendering"),
                    ], default="ADVANCED", name = "Render / Quality Material Mode")

    # = accessory_mode
    pipeline_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic Materials","Build basic PBR materials for character morph / accessory editing"),
                        ("ADVANCED","Advanced Materials","Build advanced materials for character morph / accessory editing"),
                    ], default="BASIC", name = "Accessory Material Mode")

    morph_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic Materials","Build basic PBR materials for character morph / accessory editing"),
                        ("ADVANCED","Advanced Materials","Build advanced materials for character morph / accessory editing"),
                    ], default="BASIC", name = "Character Morph Material Mode")

    log_level: bpy.props.EnumProperty(items=[
                        ("ALL","All","Log everything to console."),
                        ("WARN","Warnings & Errors","Log warnings and error messages to console."),
                        ("ERRORS","Just Errors","Log only errors to console."),
                    ], default="ERRORS", name = "(Debug) Log Level")

    debug_mode: bpy.props.BoolProperty(default=False)

    physics_group: bpy.props.StringProperty(default="CC_Physics_Weight", name="Physics Vertex Group Name")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.label(text="Material settings:")
        layout.prop(self, "quality_mode")
        layout.prop(self, "pipeline_mode")
        layout.prop(self, "morph_mode")
        layout.label(text="Lighting:")
        layout.prop(self, "lighting")
        if self.lighting == "ENABLED":
            layout.prop(self, "quality_lighting")
            layout.prop(self, "pipeline_lighting")
            layout.prop(self, "morph_lighting")
        layout.label(text="Physics:")
        layout.prop(self, "physics")
        layout.prop(self, "physics_group")
        layout.label(text="Debug Settings:")
        layout.prop(self, "log_level")
        layout.prop(self, "debug_mode")
        op = layout.operator("cc3.quickset", icon="FILE_REFRESH", text="Reset to Defaults")
        op.param = "RESET_PREFS"


def quick_set_fix(param, obj, context, objects_processed):
    props = bpy.context.scene.CC3ImportProps
    ob = context.object

    if obj is not None and obj not in objects_processed:
        if obj.type == "MESH":
            objects_processed.append(obj)

            if props.quick_set_mode == "OBJECT":
                for mat in obj.data.materials:
                    if param == "OPAQUE" or param == "BLEND" or param == "HASHED":
                        apply_alpha_override(obj, mat, param)
                    elif param == "SINGLE_SIDED":
                        apply_backface_culling(obj, mat, 1)
                    elif param == "DOUBLE_SIDED":
                        apply_backface_culling(obj, mat, 2)

            elif ob is not None and ob.active_material_index <= len(ob.data.materials):
                mat = context_material(context)
                if param == "OPAQUE" or param == "BLEND" or param == "HASHED":
                    apply_alpha_override(obj, mat, param)
                elif param == "SINGLE_SIDED":
                    apply_backface_culling(obj, mat, 1)
                elif param == "DOUBLE_SIDED":
                    apply_backface_culling(obj, mat, 2)

        elif obj.type == "ARMATURE":
            for child in obj.children:
                quick_set_fix(param, child, context, objects_processed)

def quick_set_params(param, obj, context, objects_processed):
    props = bpy.context.scene.CC3ImportProps
    ob = context.object

    if obj is not None and obj not in objects_processed:
        if obj.type == "MESH":
            objects_processed.append(obj)

            for mat in obj.data.materials:
                refresh_parameters(mat)

        elif obj.type == "ARMATURE":
            for child in obj.children:
                quick_set_params(param, child, context, objects_processed)

def quick_set_execute(param, context = bpy.context):
    objects_processed = []
    props = bpy.context.scene.CC3ImportProps

    if "PHYSICS_" in param:

        if param == "PHYSICS_ADD_CLOTH":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    enable_cloth_physics(obj)
        elif param == "PHYSICS_REMOVE_CLOTH":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    disable_cloth_physics(obj)
        elif param == "PHYSICS_ADD_COLLISION":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    enable_collision_physics(obj)
        elif param == "PHYSICS_REMOVE_COLLISION":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    disable_collision_physics(obj)
        elif param == "PHYSICS_ADD_WEIGHTMAP":
            if context.object is not None and context.object.type == "MESH":
                enable_material_weight_map(context.object, context_material(context))
        elif param == "PHYSICS_REMOVE_WEIGHTMAP":
            if context.object is not None and context.object.type == "MESH":
                disable_material_weight_map(context.object, context_material(context))
        elif param == "PHYSICS_HAIR":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "HAIR")
        elif param == "PHYSICS_COTTON":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "COTTON")
        elif param == "PHYSICS_DENIM":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "DENIM")
        elif param == "PHYSICS_LEATHER":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "LEATHER")
        elif param == "PHYSICS_RUBBER":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "RUBBER")
        elif param == "PHYSICS_SILK":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "SILK")
        elif param == "PHYSICS_PAINT":
            if context.object is not None and context.object.type == "MESH":
                paint_weight_map(context.object, context.object.material_slots[context.object.active_material_index].material)
        elif param == "PHYSICS_DONE_PAINTING":
            stop_paint()
        elif param == "PHYSICS_SAVE":
            save_dirty_weight_maps()

    elif param == "RESET":
        reset_parameters(context)

    elif param == "RESET_PREFS":
        reset_preferences()

    elif param == "UPDATE_ALL":
        for p in props.import_objects:
            if p.object is not None:
                quick_set_params(param, p.object, context, objects_processed)

    elif param == "UPDATE_SELECTED":
        for obj in bpy.context.selected_objects:
            quick_set_params(param, obj, context, objects_processed)

    else: # blend modes or single/double sided...
        if props.quick_set_mode == "OBJECT":
            for obj in bpy.context.selected_objects:
                quick_set_fix(param, obj, context, objects_processed)
        else:
            quick_set_fix(param, context.object, context, objects_processed)

block_update = False

class CC3QuickSet(bpy.types.Operator):
    """Quick Set Functions"""
    bl_idname = "cc3.quickset"
    bl_label = "Quick Set Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):
        quick_set_execute(self.param, context)
        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "UPDATE_ALL":
            return "Update all objects from the last import, with the current parameters"
        elif properties.param == "UPDATE_SELECTED":
            return "Update the currently selected objects, with the current parameters"
        elif properties.param == "OPAQUE":
            return "Set blend mode of all selected objects with alpha channels to opaque"
        elif properties.param == "BLEND":
            return "Set blend mode of all selected objects with alpha channels to alpha blend"
        elif properties.param == "HASHED":
            return "Set blend mode of all selected objects with alpha channels to alpha hashed"
        elif properties.param == "FETCH":
            return "Fetch the parameters from the selected objects"
        elif properties.param == "RESET":
            return "Reset parameters to the defaults"
        elif properties.param == "SINGLE_SIDED":
            return "Set material to be single sided, only visible from front facing"
        elif properties.param == "DOUBLE_SIDED":
            return "Set material to be double sided, visible from both sides"
        return ""
