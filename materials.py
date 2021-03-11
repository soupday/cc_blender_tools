import os

import bpy

from .cache import *
from .groups import *
from .images import *
from .nodes import *
from .utils import *
from .vars import *


def count_maps(*maps):
    count = 0
    for map in maps:
        if map is not None:
            count += 1
    return count


def is_skin_material(mat):
    if "std_skin_" in mat.name.lower():
        return True
    return False


def is_scalp_material(mat):
    props = bpy.context.scene.CC3ImportProps
    hints = props.hair_scalp_hint.split(",")
    for hint in hints:
        h = hint.strip()
        if h != "":
            if h in mat.name.lower():
                return True
    return False


def is_eyelash_material(mat):
    if "std_eyelash" in mat.name.lower():
        return True
    return False


def is_mouth_material(mat):
    name = mat.name.lower()
    if "std_upper_teeth" in name:
        return True
    elif "std_lower_teeth" in name:
        return True
    elif "std_tongue" in name:
        return True
    return False


def is_teeth_material(mat):
    name = mat.name.lower()
    if "std_upper_teeth" in name:
        return True
    elif "std_lower_teeth" in name:
        return True
    return False


def is_tongue_material(mat):
    name = mat.name.lower()
    if "std_tongue" in name:
        return True
    return False


def is_nails_material(mat):
    name = mat.name.lower()
    if "std_nails" in name:
        return True
    return False


def is_hair_object(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if props.hair_object is not None and obj == props.hair_object:
        return True
    hints = props.hair_hint.split(",")
    object_name = obj.name.lower()
    material_name = mat.name.lower()
    for hint in hints:
        h = hint.strip()
        if h != "":
            if h in object_name:
                return True
            elif h in material_name:
                return True
    return False


def is_eye_material(mat):
    if "std_cornea_" in mat.name.lower():
        return True
    return False


def is_tearline_material(mat):
    if "std_tearline_" in mat.name.lower():
        return True
    return False


def is_eye_occlusion_material(mat):
    if "std_eye_occlusion_" in mat.name.lower():
        return True
    return False


def get_material_group(obj, mat):
    name = mat.name.lower()
    if "std_skin_head" in name:
        return "skin_head"
    elif "std_skin_body" in name:
        return "skin_body"
    elif "std_skin_arm" in name:
        return "skin_arm"
    elif "std_skin_leg" in name:
        return "skin_leg"
    elif "std_upper_teeth" in name:
        return "teeth_upper"
    elif "std_lower_teeth" in name:
        return "teeth_lower"
    elif "std_nails" in name:
        return "nails"
    elif "std_tongue" in name:
        return "tongue"
    elif is_hair_object(obj, mat):
        if is_scalp_material(mat):
            return "scalp"
        return "hair"
    elif is_eye_material(mat):
        return "eye"
    else:
        return "default"


def get_bump_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_hair_object(obj, mat):
        return "hair_bump", props.hair_bump
    return "default_bump", props.default_bump


def get_micronormal_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    name = mat.name.lower()
    if "std_skin_head" in name:
        return "skin_head_micronormal", props.skin_head_micronormal
    elif "std_skin_body" in name:
        return "skin_body_micronormal", props.skin_body_micronormal
    elif "std_skin_arm" in name:
        return "skin_arm_micronormal", props.skin_arm_micronormal
    elif "std_skin_leg" in name:
        return "skin_leg_micronormal", props.skin_leg_micronormal
    elif "std_upper_teeth" in name:
        return "teeth_upper_micronormal", props.teeth_micronormal
    elif "std_lower_teeth" in name:
        return "teeth_lower_micronormal", props.teeth_micronormal
    elif "std_nails" in name:
        return "nails_micronormal", props.nails_micronormal
    elif "std_tongue" in name:
        return "tongue_micronormal", props.tongue_micronormal
    elif is_eye_material(mat):
        return "eye_sclera_normal", 1 - props.eye_sclera_normal
    return "default_micronormal", props.default_micronormal


def get_micronormal_tiling(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    name = mat.name.lower()
    if "std_skin_head" in name:
        return "skin_head_tiling", props.skin_head_tiling
    elif "std_skin_body" in name:
        return "skin_body_tiling", props.skin_body_tiling
    elif "std_skin_arm" in name:
        return "skin_arm_tiling", props.skin_arm_tiling
    elif "std_skin_leg" in name:
        return "skin_leg_tiling", props.skin_leg_tiling
    elif "std_upper_teeth" in name:
        return "teeth_upper_tiling", props.teeth_tiling
    elif "std_lower_teeth" in name:
        return "teeth_lower_tiling", props.teeth_tiling
    elif "std_tongue" in name:
        return "tongue_tiling", props.tongue_tiling
    elif "std_nails" in name:
        return "nails_tiling", props.nails_tiling
    elif is_eye_material(mat):
        return "eye_sclera_tiling", props.eye_sclera_tiling
    return "default_tiling", props.default_tiling


def get_specular_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_eye_material(mat):
        return "eye_specular", props.eye_specular
    elif is_skin_material(mat):
        if props.setup_mode == "ADVANCED":
            return "skin_specular", props.skin_specular
        else:
            return "skin_basic_specular", props.skin_basic_specular
    elif is_hair_object(obj, mat):
        if is_scalp_material(mat):
            return "hair_scalp_specular", props.hair_scalp_specular
        return "hair_specular", props.hair_specular
    elif is_nails_material(mat):
        return "nails_specular", props.nails_specular
    elif is_teeth_material(mat):
        return "teeth_specular", props.teeth_specular
    elif is_tongue_material(mat):
        return "tongue_specular", props.tongue_specular
    return "default_specular", get_default_shader_input(mat, "Specular")


def get_roughness_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_skin_material(mat):
        if props.setup_mode == "ADVANCED":
            return "skin_roughness", props.skin_roughness
        else:
            return "skin_basic_roughness", props.skin_basic_roughness
    elif is_hair_object(obj, mat):
        if is_scalp_material(mat):
            return "hair_scalp_roughness", props.hair_scalp_roughness
        return "hair_roughness", props.hair_roughness
    elif is_nails_material(mat):
        return "nails_roughness", props.nails_roughness
    elif is_teeth_material(mat):
        return "teeth_roughness", props.teeth_roughness
    elif is_tongue_material(mat):
        return "tongue_roughness", props.tongue_roughness
    return "default_roughness", props.default_roughness


def get_ao_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_eye_material(mat):
        return "eye_ao", props.eye_ao
    elif is_skin_material(mat):
        return "skin_ao", props.skin_ao
    elif is_hair_object(obj, mat):
        return "hair_ao", props.hair_ao
    elif is_nails_material(mat):
        return "nails_ao", props.nails_ao
    elif is_teeth_material(mat):
        return "teeth_ao", props.teeth_ao
    elif is_tongue_material(mat):
        return "tongue_ao", props.tongue_ao
    return "default_ao", props.default_ao


def get_blend_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_eye_material(mat):
        return "eye_blend", props.eye_blend
    elif is_skin_material(mat):
        return "skin_blend", props.skin_blend
    elif is_hair_object(obj, mat):
        return "hair_blend", props.hair_blend
    return "default_blend", props.default_blend


def get_normal_blend_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_skin_material(mat):
        return "skin_normal_blend", props.skin_normal_blend
    return "default_normal_blend", props.default_normal_blend


def get_sss_radius(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_eye_material(mat):
        return "eye_sss_radius", props.eye_sss_radius
    elif is_skin_material(mat):
        return "skin_sss_radius", props.skin_sss_radius
    elif is_hair_object(obj, mat):
        return "hair_sss_radius", props.hair_sss_radius
    elif is_nails_material(mat):
        return "nails_sss_radius", props.nails_sss_radius
    elif is_teeth_material(mat):
        return "teeth_sss_radius", props.teeth_sss_radius
    elif is_tongue_material(mat):
        return "tongue_sss_radius", props.tongue_sss_radius
    return "default_sss_radius", props.default_sss_radius


def get_sss_falloff(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_eye_material(mat):
        return "eye_sss_falloff", props.eye_sss_falloff
    elif is_skin_material(mat):
        return "skin_sss_falloff", props.skin_sss_falloff
    elif is_hair_object(obj, mat):
        return "hair_sss_falloff", props.hair_sss_falloff
    elif is_nails_material(mat):
        return "nails_sss_falloff", props.nails_sss_falloff
    elif is_teeth_material(mat):
        return "teeth_sss_falloff", props.teeth_sss_falloff
    elif is_tongue_material(mat):
        return "tongue_sss_falloff", props.tongue_sss_falloff
    return "default_sss_falloff", props.default_sss_falloff


def apply_backface_culling(obj, mat, sides):
    cache = get_material_cache(mat)
    if cache is not None:
        cache.culling_sides = sides
    if sides == 1:
        mat.use_backface_culling = True
    else:
        mat.use_backface_culling = False


def apply_alpha_override(obj, mat, method):
    cache = get_material_cache(mat)
    if cache is not None:
        cache.alpha_mode = method
    input = get_shader_input(mat, "Alpha")
    if input is None:
        return
    if is_input_connected(input):
        set_material_alpha(mat, method)
    elif input.default_value < 1.0:
        set_material_alpha(mat, method)
    else:
        set_material_alpha(mat, "OPAQUE")


def set_material_alpha(mat, method):
    if method == "HASHED":
        mat.blend_method = "HASHED"
        mat.shadow_method = "HASHED"
        mat.use_backface_culling = False
    elif method == "BLEND":
        mat.blend_method = "BLEND"
        mat.shadow_method = "CLIP"
        mat.use_backface_culling = True
        mat.show_transparent_back = True
        mat.alpha_threshold = 0.5
    else:
        mat.blend_method = "OPAQUE"
        mat.shadow_method = "OPAQUE"
        mat.use_backface_culling = False





def connect_tearline_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    set_node_input(shader, "Base Color", (1.0, 1.0, 1.0, 1.0))
    set_node_input(shader, "Metallic", 1.0)
    set_node_input(shader, "Specular", 1.0)
    set_node_input(shader, "Roughness", props.eye_tearline_roughness)
    set_node_input(shader, "Alpha", props.eye_tearline_alpha)
    shader.name = unique_name("eye_tearline_shader")
    set_material_alpha(mat, props.blend_mode)
    mat.shadow_method = "NONE"


def connect_eye_occlusion_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    set_node_input(shader, "Base Color", (0.0, 0.0, 0.0, 1.0))
    set_node_input(shader, "Metallic", 0.0)
    set_node_input(shader, "Specular", 0.0)
    set_node_input(shader, "Roughness", 1.0)

    reset_cursor()

    # groups
    group = get_node_group("eye_occlusion_mask")
    occ_node = make_node_group_node(nodes, group, "Eye Occulsion Alpha", "eye_occlusion_mask")
    # values
    set_node_input(occ_node, "Strength", props.eye_occlusion)
    # links
    link_nodes(links, occ_node, "Alpha", shader, "Alpha")

    set_material_alpha(mat, props.blend_mode)
    mat.shadow_method = "NONE"


def connect_basic_eye_material(obj, mat, shader):

    props = bpy.context.scene.CC3ImportProps

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Base Color
    #
    reset_cursor()
    diffuse_image =  find_material_image(mat, BASE_COLOR_MAP)
    if diffuse_image is not None:
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        advance_cursor(1.0)
        hsv_node = make_shader_node(nodes, "ShaderNodeHueSaturation", 0.6)
        hsv_node.label = "HSV"
        hsv_node.name = unique_name("eye_basic_hsv")
        set_node_input(hsv_node, "Value", props.eye_basic_brightness)
        # links
        link_nodes(links, diffuse_node, "Color", hsv_node, "Color")
        link_nodes(links, hsv_node, "Color", shader, "Base Color")

    # Metallic
    #
    reset_cursor()
    metallic_node = make_value_node(nodes, "Eye Metallic", "eye_metallic", 0.0)
    link_nodes(links, metallic_node, "Value", shader, "Metallic")

    # Specular
    #
    reset_cursor()
    specular_node = make_value_node(nodes, "Eye Specular", "eye_specular", props.eye_specular)
    link_nodes(links, specular_node, "Value", shader, "Specular")

    # Roughness
    #
    reset_cursor()
    roughness_node = make_value_node(nodes, "Eye Roughness", "eye_basic_roughness", props.eye_basic_roughness)
    link_nodes(links, roughness_node, "Value", shader, "Roughness")

    # Alpha
    #
    set_node_input(shader, "Alpha", 1.0)

    # Normal
    #
    reset_cursor()
    normal_image = find_material_image(mat, SCLERA_NORMAL_MAP)
    if normal_image is not None:
        strength_node = make_value_node(nodes, "Normal Strength", "eye_basic_normal", props.eye_basic_normal)
        normal_node = make_image_node(nodes, normal_image, "normal_tex")
        advance_cursor()
        normalmap_node = make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        link_nodes(links, strength_node, "Value", normalmap_node, "Strength")
        link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        link_nodes(links, normalmap_node, "Normal", shader, "Normal")

    # Clearcoat
    #
    set_node_input(shader, "Clearcoat", 1.0)
    set_node_input(shader, "Clearcoat Roughness", 0.15)

    return


def connect_adv_eye_material(obj, mat, shader):

    props = bpy.context.scene.CC3ImportProps

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Iris Mask
    reset_cursor()
    # groups
    group = get_node_group("iris_mask")
    iris_mask_node = make_node_group_node(nodes, group, "Iris Mask", "iris_mask")
    # values
    set_node_input(iris_mask_node, "Scale", 1.0 / props.eye_iris_scale)
    set_node_input(iris_mask_node, "Radius", props.eye_iris_radius)
    set_node_input(iris_mask_node, "Hardness", props.eye_iris_hardness * props.eye_iris_radius * 0.99)
    # move
    move_new_nodes(-3000, 0)
    clear_cursor()

    # Base Color
    reset_cursor()
    # maps
    diffuse_image = find_material_image(mat, BASE_COLOR_MAP)
    sclera_image = find_material_image(mat, SCLERA_MAP)
    blend_image = find_material_image(mat, MOD_BASECOLORBLEND_MAP)
    ao_image = find_material_image(mat, MOD_AO_MAP)
    diffuse_node = sclera_node = blend_node = ao_node = iris_tiling_node = sclera_tiling_node = None
    advance_cursor(-count_maps(diffuse_image, sclera_image, blend_image, ao_image))
    if diffuse_image is not None:
        advance_cursor(-1)
        drop_cursor(0.75)
        group = get_node_group("tiling_pivot_mapping")
        iris_tiling_node = make_node_group_node(nodes, group, "Iris Scaling", "tiling_color_iris_mapping")
        set_node_input(iris_tiling_node, "Pivot", (0.5, 0.5, 0))
        advance_cursor()
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        step_cursor()
    if sclera_image is not None:
        advance_cursor(-1)
        drop_cursor(0.75)
        group = get_node_group("tiling_pivot_mapping")
        sclera_tiling_node = make_node_group_node(nodes, group, "Sclera Scaling", "tiling_color_sclera_mapping")
        set_node_input(sclera_tiling_node, "Pivot", (0.5, 0.5, 0))
        set_node_input(sclera_tiling_node, "Tiling", 1.0 / props.eye_sclera_scale)
        advance_cursor()
        sclera_node = make_image_node(nodes, sclera_image, "sclera_tex")
        sclera_node.extension = "EXTEND"
        step_cursor()
    if ao_image is not None:
        ao_node = make_image_node(nodes, ao_image, "ao_tex")
        step_cursor()
    if blend_image is not None:
        blend_node = make_image_node(nodes, blend_image, "blend_tex")
        step_cursor()
    # groups
    group = get_node_group("color_eye_mixer")
    color_node = make_node_group_node(nodes, group, "Eye Base Color", "color_eye_mixer")
    # values
    set_node_input(color_node, "Shadow Hardness", props.eye_shadow_hardness * props.eye_shadow_radius * 0.99)
    set_node_input(color_node, "Shadow Radius", props.eye_shadow_radius)
    set_node_input(color_node, "Blend Strength", props.eye_blend)
    set_node_input(color_node, "AO Strength", props.eye_ao)
    set_node_input(color_node, "Iris Brightness", props.eye_iris_brightness)
    set_node_input(color_node, "Sclera Brightness", props.eye_sclera_brightness)
    # links
    link_nodes(links, iris_mask_node, "Mask", color_node, "Iris Mask")
    if diffuse_image is not None:
        link_nodes(links, iris_mask_node, "Scale", iris_tiling_node, "Tiling")
        link_nodes(links, iris_tiling_node, "Vector", diffuse_node, "Vector")
        link_nodes(links, diffuse_node, "Color", color_node, "Cornea Diffuse")
    if sclera_image is not None:
        link_nodes(links, sclera_tiling_node, "Vector", sclera_node, "Vector")
        link_nodes(links, sclera_node, "Color", color_node, "Sclera Diffuse")
    else:
        link_nodes(links, diffuse_node, "Color", color_node, "Sclera Diffuse")
    if blend_image is not None:
        link_nodes(links, blend_node, "Color", color_node, "Blend")
    if ao_image is not None:
        link_nodes(links, ao_node, "Color", color_node, "AO")
    link_nodes(links, color_node, "Base Color", shader, "Base Color")

    # SSS
    drop_cursor(0.65)
    reset_cursor()
    # groups
    group = get_node_group("subsurface_overlay_mixer")
    sss_node = make_node_group_node(nodes, group, "Eye Subsurface", "subsurface_eye_mixer")
    # values
    set_node_input(sss_node, "Scatter1", 1.0)
    set_node_input(sss_node, "Scatter2", 0.0)
    set_node_input(sss_node, "Radius1", props.eye_sss_radius * UNIT_SCALE)
    set_node_input(sss_node, "Radius2", props.eye_sss_radius * UNIT_SCALE)
    set_node_input(sss_node, "Falloff1", props.eye_sss_falloff)
    set_node_input(sss_node, "Falloff2", props.eye_sss_falloff)
    # links
    link_nodes(links, iris_mask_node, "Mask", sss_node, "Mask")
    link_nodes(links, color_node, "Base Color", sss_node, "Diffuse")
    link_nodes(links, sss_node, "Subsurface", shader, "Subsurface")
    link_nodes(links, sss_node, "Subsurface Radius", shader, "Subsurface Radius")
    link_nodes(links, sss_node, "Subsurface Color", shader, "Subsurface Color")

    # MSR
    drop_cursor(0.1)
    reset_cursor()
    # groups
    group = get_node_group("msr_overlay_mixer")
    msr_node = make_node_group_node(nodes, group, "Eye MSR", "msr_eye_mixer")
    # values
    set_node_input(msr_node, "Metallic1", 0)
    set_node_input(msr_node, "Metallic2", 0)
    set_node_input(msr_node, "Specular1", props.eye_specular)
    set_node_input(msr_node, "Specular2", props.eye_specular)
    set_node_input(msr_node, "Roughness1", props.eye_sclera_roughness)
    set_node_input(msr_node, "Roughness2", props.eye_iris_roughness)
    # links
    link_nodes(links, iris_mask_node, "Mask", msr_node, "Mask")
    link_nodes(links, msr_node, "Metallic", shader, "Metallic")
    link_nodes(links, msr_node, "Specular", shader, "Specular")
    link_nodes(links, msr_node, "Roughness", shader, "Roughness")

    # emission and alpha
    set_node_input(shader, "Alpha", 1.0)
    connect_emission_alpha(obj, mat, shader)

    # Normal
    drop_cursor(0.1)
    reset_cursor()
    snormal_image = find_material_image(mat, SCLERA_NORMAL_MAP)
    snormal_node = snormal_tiling_node = None
    # space
    advance_cursor(-count_maps(snormal_image))
    # maps
    if snormal_image is not None:
        advance_cursor(-1)
        drop_cursor(0.75)
        group = get_node_group("tiling_mapping")
        snormal_tiling_node = make_node_group_node(nodes, group, "Sclera Normal Tiling", "tiling_normal_sclera_mapping")
        set_node_input(snormal_tiling_node, "Tiling", props.eye_sclera_tiling)
        advance_cursor()
        snormal_node = make_image_node(nodes, snormal_image, "sclera_normal_tex")
        step_cursor()
    # groups
    group = get_node_group("normal_micro_mask_mixer")
    nm_group = make_node_group_node(nodes, group, "Eye Normals", "normal_eye_mixer")
    # values
    set_node_input(nm_group, "Micro Normal Strength", 1 - props.eye_sclera_normal)
    # links
    link_nodes(links, iris_mask_node, "Inverted Mask", nm_group, "Micro Normal Mask")
    if snormal_image is not None:
        link_nodes(links, snormal_node, "Color", nm_group, "Micro Normal")
        link_nodes(links, snormal_tiling_node, "Vector", snormal_node, "Vector")
    link_nodes(links, nm_group, "Normal", shader, "Normal")

    # Clearcoat
    #
    set_node_input(shader, "Clearcoat", 1.0)
    set_node_input(shader, "Clearcoat Roughness", 0.15)

    return


def connect_adv_mouth_material(obj, mat, shader):

    props = bpy.context.scene.CC3ImportProps

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Gums Mask and Gradient AO
    reset_cursor()
    advance_cursor(-2)
    # maps
    mask_image = None
    mask_node = None
    teeth = is_teeth_material(mat)
    if teeth:
        mask_image = find_material_image(mat, TEETH_GUMS_MAP)
        # if no gums mask file is found for the teeth,
        # just connect as default advanced material
        if mask_image is None:
            connect_advanced_material(obj, mat, shader)
            return
    # if no gradient ao file is found for the teeth or tongue
    # just connect as default advanced material
    gradient_image = find_material_image(mat, MOUTH_GRADIENT_MAP)
    gradient_node = None
    if gradient_image is None:
        connect_advanced_material(obj, mat, shader)
        return
    advance_cursor(2 - count_maps(mask_image, gradient_image))
    if mask_image is not None:
        mask_node = make_image_node(nodes, mask_image, "gums_mask_tex")
        step_cursor()
    if gradient_image is not None:
        gradient_node = make_image_node(nodes, gradient_image, "gradient_ao_tex")
        step_cursor()
        # nodes
        gradientrgb_node = make_shader_node(nodes, "ShaderNodeSeparateRGB")
        # links
        link_nodes(links, gradient_node, "Color", gradientrgb_node, "Image")
    # move
    move_new_nodes(-2000, 0)
    clear_cursor()

    # Base Color
    reset_cursor()
    advance_cursor(-2)
    # maps
    diffuse_image = find_material_image(mat, BASE_COLOR_MAP)
    ao_image = find_material_image(mat, MOD_AO_MAP)
    diffuse_node = ao_node = None
    advance_cursor(2 - count_maps(diffuse_image, ao_image))
    if diffuse_image is not None:
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        step_cursor()
    if ao_image is not None:
        ao_node = make_image_node(nodes, ao_image, "ao_tex")
        step_cursor()
    # groups
    if teeth:
        group = get_node_group("color_teeth_mixer")
        color_node = make_node_group_node(nodes, group, "Teeth Base Color", "color_teeth_mixer")
    else:
        group = get_node_group("color_tongue_mixer")
        color_node = make_node_group_node(nodes, group, "Tongue Base Color", "color_tongue_mixer")
    # values
    if teeth:
        set_node_input(color_node, "AO Strength", props.teeth_ao)
        set_node_input(color_node, "Front", props.teeth_front)
        set_node_input(color_node, "Rear", props.teeth_rear)
        set_node_input(color_node, "Gums Brightness", props.teeth_gums_brightness)
        set_node_input(color_node, "Teeth Brightness", props.teeth_teeth_brightness)
        set_node_input(color_node, "Gums Saturation", 1 - props.teeth_gums_desaturation)
        set_node_input(color_node, "Teeth Saturation", 1 - props.teeth_teeth_desaturation)
    else:
        set_node_input(color_node, "AO Strength", props.tongue_ao)
        set_node_input(color_node, "Front", props.tongue_front)
        set_node_input(color_node, "Rear", props.tongue_rear)
        set_node_input(color_node, "Brightness", props.tongue_brightness)
        set_node_input(color_node, "Saturation", 1 - props.tongue_desaturation)
    # links
    if teeth:
        gao_socket = "G"
        if "std_lower_teeth" in mat.name.lower():
            gao_socket = "R"
        link_nodes(links, mask_node, "Color", color_node, "Gums Mask")
        link_nodes(links, gradientrgb_node, gao_socket, color_node, "Gradient AO")
        link_nodes(links, diffuse_node, "Color", color_node, "Diffuse")
        link_nodes(links, ao_node, "Color", color_node, "AO")
        link_nodes(links, color_node, "Base Color", shader, "Base Color")
    else:
        gao_socket = "B"
        link_nodes(links, gradientrgb_node, gao_socket, color_node, "Gradient AO")
        link_nodes(links, diffuse_node, "Color", color_node, "Diffuse")
        link_nodes(links, ao_node, "Color", color_node, "AO")
        link_nodes(links, color_node, "Base Color", shader, "Base Color")

    # SSS
    drop_cursor(0.35)
    reset_cursor()
    # groups
    if teeth:
        group = get_node_group("subsurface_overlay_mixer")
        sss_node = make_node_group_node(nodes, group, "Teeth Subsurface", "subsurface_teeth_mixer")
    else:
        group = get_node_group("subsurface_mixer")
        sss_node = make_node_group_node(nodes, group, "Tongue Subsurface", "subsurface_tongue_mixer")
    # values
    if teeth:
        set_node_input(sss_node, "Scatter1", props.teeth_gums_sss_scatter)
        set_node_input(sss_node, "Radius1", props.teeth_sss_radius * UNIT_SCALE * 3)
        set_node_input(sss_node, "Falloff1", props.teeth_sss_falloff)
        set_node_input(sss_node, "Scatter2", props.teeth_teeth_sss_scatter)
        set_node_input(sss_node, "Radius2", props.teeth_sss_radius * UNIT_SCALE * 3)
        set_node_input(sss_node, "Falloff2", props.teeth_sss_falloff)
    else:
        set_node_input(sss_node, "Scatter", props.tongue_sss_scatter)
        set_node_input(sss_node, "Radius", props.tongue_sss_radius * UNIT_SCALE * 3)
        set_node_input(sss_node, "Falloff", props.tongue_sss_falloff)
    # links
    link_nodes(links, mask_node, "Color", sss_node, "Mask")
    link_nodes(links, color_node, "Base Color", sss_node, "Diffuse")
    link_nodes(links, sss_node, "Subsurface", shader, "Subsurface")
    link_nodes(links, sss_node, "Subsurface Radius", shader, "Subsurface Radius")
    link_nodes(links, sss_node, "Subsurface Color", shader, "Subsurface Color")

    # MSR
    drop_cursor(0.1)
    reset_cursor()
    advance_cursor(-2.7)
    # props
    metallic = 0
    specprop, specular = get_specular_strength(obj, mat)
    roughprop, roughness = get_roughness_strength(obj, mat)
    # maps
    metallic_image = find_material_image(mat, METALLIC_MAP)
    roughness_image = find_material_image(mat, ROUGHNESS_MAP)
    metallic_node = roughness_node = roughness_mult_node = None
    if metallic_image is not None:
        metallic_node = make_image_node(nodes, metallic_image, "metallic_tex")
        step_cursor()
    else:
        advance_cursor()
    if roughness_image is not None:
        roughness_node = make_image_node(nodes, roughness_image, "roughness_tex")
        advance_cursor()
        roughness_mult_node = make_math_node(nodes, "MULTIPLY", 1, roughness)
        if teeth:
            roughness_mult_node.name = unique_name("teeth_roughness")
        else:
            roughness_mult_node.name = unique_name("tongue_roughness")
        step_cursor(0.7)
    else:
        advance_cursor(1.7)
    # groups
    group = get_node_group("msr_overlay_mixer")
    if teeth:
        msr_node = make_node_group_node(nodes, group, "Teeth MSR", "msr_teeth_mixer")
    else:
        msr_node = make_node_group_node(nodes, group, "Tongue MSR", "msr_tongue_mixer")
    # values
    set_node_input(msr_node, "Metallic1", metallic)
    set_node_input(msr_node, "Metallic2", metallic)
    set_node_input(msr_node, "Roughness1", 1)
    set_node_input(msr_node, "Roughness2", roughness)
    set_node_input(msr_node, "Specular1", 0)
    set_node_input(msr_node, "Specular2", specular)
    # links
    link_nodes(links, gradientrgb_node, gao_socket, msr_node, "Mask")
    link_nodes(links, metallic_node, "Color", msr_node, "Metallic1")
    link_nodes(links, metallic_node, "Color", msr_node, "Metallic2")
    link_nodes(links, roughness_node, "Color", roughness_mult_node, 0)
    link_nodes(links, roughness_mult_node, "Value", msr_node, "Roughness2")
    link_nodes(links, gradientrgb_node, gao_socket, msr_node, "Mask")
    link_nodes(links, msr_node, "Metallic", shader, "Metallic")
    link_nodes(links, msr_node, "Specular", shader, "Specular")
    link_nodes(links, msr_node, "Roughness", shader, "Roughness")

    # emission and alpha
    set_node_input(shader, "Alpha", 1.0)
    connect_emission_alpha(obj, mat, shader)

    # Normal
    connect_normal(obj, mat, shader)

    # Clearcoat
    #
    set_node_input(shader, "Clearcoat", 0)
    set_node_input(shader, "Clearcoat Roughness", 0)

    return


def connect_advanced_material(obj, mat, shader):
    base_colour_node = connect_base_color(obj, mat, shader)
    connect_subsurface(obj, mat, shader, base_colour_node)
    connect_msr(obj, mat, shader)
    connect_emission_alpha(obj, mat, shader)
    connect_normal(obj, mat, shader)
    return


def connect_basic_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Base Color
    #
    reset_cursor()
    diffuse_image = find_material_image(mat, BASE_COLOR_MAP)
    ao_image = find_material_image(mat, MOD_AO_MAP)
    diffuse_node = ao_node = None
    if (diffuse_image is not None):
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        if ao_image is not None:
            prop, ao_strength = get_ao_strength(obj, mat)
            fac_node = make_value_node(nodes, "Ambient Occlusion Strength", prop, ao_strength)
            ao_node = make_image_node(nodes, ao_image, "ao_tex")
            advance_cursor(1.5)
            drop_cursor(0.75)
            mix_node = make_mixrgb_node(nodes, "MULTIPLY")
            link_nodes(links, diffuse_node, "Color", mix_node, "Color1")
            link_nodes(links, ao_node, "Color", mix_node, "Color2")
            link_nodes(links, fac_node, "Value", mix_node, "Fac")
            link_nodes(links, mix_node, "Color", shader, "Base Color")
        else:
            link_nodes(links, diffuse_node, "Color", shader, "Base Color")

    # Metallic
    #
    reset_cursor()
    metallic_image = find_material_image(mat, METALLIC_MAP)
    metallic_node = None
    if metallic_image is not None:
        metallic_node = make_image_node(nodes, metallic_image, "metallic_tex")
        link_nodes(links, metallic_node, "Color", shader, "Metallic")

    # Specular
    #
    reset_cursor()
    specular_image = find_material_image(mat, SPECULAR_MAP)
    mask_image = find_material_image(mat, MOD_SPECMASK_MAP)
    prop_spec, spec = get_specular_strength(obj, mat)
    specular_node = mask_node = mult_node = None
    if specular_image is not None:
        specular_node = make_image_node(nodes, specular_image, "specular_tex")
        link_nodes(links, specular_node, "Color", shader, "Specular")
    # always make a specular value node for skin or if there is a mask (but no map)
    elif prop_spec != "default_specular":
        specular_node = make_value_node(nodes, "Specular Strength", prop_spec, spec)
        link_nodes(links, specular_node, "Value", shader, "Specular")
    elif mask_image is not None:
        specular_node = make_value_node(nodes, "Specular Strength", "default_basic_specular", shader.inputs["Specular"].default_value)
        link_nodes(links, specular_node, "Value", shader, "Specular")
    if mask_image is not None:
        mask_node = make_image_node(nodes, mask_image, "specular_mask_tex")
        advance_cursor()
        mult_node = make_math_node(nodes, "MULTIPLY")
        if specular_node.type == "VALUE":
            link_nodes(links, specular_node, "Value", mult_node, 0)
        else:
            link_nodes(links, specular_node, "Color", mult_node, 0)
        link_nodes(links, mask_node, "Color", mult_node, 1)
        link_nodes(links, mult_node, "Value", shader, "Specular")

    # Roughness
    #
    reset_cursor()
    roughness_image = find_material_image(mat, ROUGHNESS_MAP)
    roughness_node = None
    if roughness_image is not None:
        roughness_node = make_image_node(nodes, roughness_image, "roughness_tex")
        rprop_name, rprop_val = get_roughness_strength(obj, mat)
        if is_skin_material(mat):
            advance_cursor()
            remap_node = make_shader_node(nodes, "ShaderNodeMapRange")
            remap_node.name = unique_name(rprop_name)
            set_node_input(remap_node, "To Min", rprop_val)
            link_nodes(links, roughness_node, "Color", remap_node, "Value")
            link_nodes(links, remap_node, "Result", shader, "Roughness")
        elif is_teeth_material(mat) or is_tongue_material(mat):
            advance_cursor()
            rmult_node = make_math_node(nodes, "MULTIPLY", 1, rprop_val)
            rmult_node.name = unique_name(rprop_name)
            link_nodes(links, roughness_node, "Color", rmult_node, 0)
            link_nodes(links, rmult_node, "Value", shader, "Roughness")
        else:
            link_nodes(links, roughness_node, "Color", shader, "Roughness")

    # Emission
    #
    reset_cursor()
    emission_image = find_material_image(mat, EMISSION_MAP)
    emission_node = None
    if emission_image is not None:
        emission_node = make_image_node(nodes, emission_image, "emission_tex")
        link_nodes(links, emission_node, "Color", shader, "Emission")

    # Alpha
    #
    reset_cursor()
    alpha_image = find_material_image(mat, ALPHA_MAP)
    alpha_node = None
    if alpha_image is not None:
        alpha_node = make_image_node(nodes, alpha_image, "opacity_tex")
        dir,file = os.path.split(alpha_image.filepath)
        if "_diffuse." in file.lower() or "_albedo." in file.lower():
            link_nodes(links, alpha_node, "Alpha", shader, "Alpha")
        else:
            link_nodes(links, alpha_node, "Color", shader, "Alpha")
    # material alpha blend settings
    if is_hair_object(obj, mat) or is_eyelash_material(mat):
        set_material_alpha(mat, "HASHED")
    elif shader.inputs["Alpha"].default_value < 1.0:
        set_material_alpha(mat, props.blend_mode)
    else:
        set_material_alpha(mat, "OPAQUE")

    # Normal
    #
    reset_cursor()
    normal_image = find_material_image(mat, NORMAL_MAP)
    bump_image = find_material_image(mat, BUMP_MAP)
    normal_node = bump_node = normalmap_node = bumpmap_node = None
    if normal_image is not None:
        normal_node = make_image_node(nodes, normal_image, "normal_tex")
        advance_cursor()
        normalmap_node = make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        link_nodes(links, normalmap_node, "Normal", shader, "Normal")
    if bump_image is not None:
        prop_bump, bump_strength = get_bump_strength(obj, mat)
        bump_strength_node = make_value_node(nodes, "Bump Strength", prop_bump, bump_strength / 1000)
        bump_node = make_image_node(nodes, bump_image, "bump_tex")
        advance_cursor()
        bumpmap_node = make_shader_node(nodes, "ShaderNodeBump", 0.7)
        advance_cursor()
        link_nodes(links, bump_strength_node, "Value", bumpmap_node, "Distance")
        link_nodes(links, bump_node, "Color", bumpmap_node, "Height")
        if normal_image is not None:
            link_nodes(links, normalmap_node, "Normal", bumpmap_node, "Normal")
        link_nodes(links, bumpmap_node, "Normal", shader, "Normal")

    return

# the 'Compatible' material is the bare minimum required to export the corrent textures with the FBX
# it will connect just the diffuse, metallic, specular, roughness, opacity and normal/bump
def connect_compat_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Base Color
    #
    reset_cursor()
    diffuse_image = find_material_image(mat, BASE_COLOR_MAP)
    if (diffuse_image is not None):
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        link_nodes(links, diffuse_node, "Color", shader, "Base Color")

    # Metallic
    #
    reset_cursor()
    metallic_image = find_material_image(mat, METALLIC_MAP)
    metallic_node = None
    if metallic_image is not None:
        metallic_node = make_image_node(nodes, metallic_image, "metallic_tex")
        link_nodes(links, metallic_node, "Color", shader, "Metallic")

    # Specular
    #
    reset_cursor()
    specular_image = find_material_image(mat, SPECULAR_MAP)
    if specular_image is not None:
        specular_node = make_image_node(nodes, specular_image, "specular_tex")
        link_nodes(links, specular_node, "Color", shader, "Specular")
    if is_skin_material(mat):
        set_node_input(shader, "Specular", 0.2)
    if is_eye_material(mat):
        set_node_input(shader, "Specular", 0.8)

    # Roughness
    #
    reset_cursor()
    roughness_image = find_material_image(mat, ROUGHNESS_MAP)
    if roughness_image is not None:
        roughness_node = make_image_node(nodes, roughness_image, "roughness_tex")
        link_nodes(links, roughness_node, "Color", shader, "Roughness")
    if is_eye_material(mat):
        set_node_input(shader, "Roughness", 0)

    # Emission
    #
    reset_cursor()
    emission_image = find_material_image(mat, EMISSION_MAP)
    emission_node = None
    if emission_image is not None:
        emission_node = make_image_node(nodes, emission_image, "emission_tex")
        link_nodes(links, emission_node, "Color", shader, "Emission")

    # Alpha
    #
    reset_cursor()
    alpha_image = find_material_image(mat, ALPHA_MAP)
    alpha_node = None
    if alpha_image is not None:
        alpha_node = make_image_node(nodes, alpha_image, "opacity_tex")
        file = os.path.split(alpha_image.filepath)[1]
        if "_diffuse." in file.lower() or "_albedo." in file.lower():
            link_nodes(links, alpha_node, "Alpha", shader, "Alpha")
        else:
            link_nodes(links, alpha_node, "Color", shader, "Alpha")
    # material alpha blend settings
    if is_hair_object(obj, mat) or is_eyelash_material(mat):
        set_material_alpha(mat, "HASHED")
    elif is_eye_occlusion_material(mat) or is_tearline_material(mat):
        set_material_alpha(mat, props.blend_mode)
    elif shader.inputs["Alpha"].default_value < 1.0:
        set_material_alpha(mat, props.blend_mode)
    else:
        set_material_alpha(mat, "OPAQUE")

    # Normal
    #
    reset_cursor()
    normal_image = find_material_image(mat, NORMAL_MAP)
    bump_image = find_material_image(mat, BUMP_MAP)
    normal_node = bump_node = normalmap_node = bumpmap_node = None
    if normal_image is not None:
        normal_node = make_image_node(nodes, normal_image, "normal_tex")
        advance_cursor()
        normalmap_node = make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        link_nodes(links, normalmap_node, "Normal", shader, "Normal")
    elif bump_image is not None:
        bump_node = make_image_node(nodes, bump_image, "bump_tex")
        advance_cursor()
        bumpmap_node = make_shader_node(nodes, "ShaderNodeBump", 0.7)
        advance_cursor()
        set_node_input(bumpmap_node, "Distance", 0.002)
        link_nodes(links, bump_node, "Color", bumpmap_node, "Height")
        link_nodes(links, bumpmap_node, "Normal", shader, "Normal")

    return

def connect_base_color(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps

    diffuse_image = find_material_image(mat, BASE_COLOR_MAP)
    blend_image = find_material_image(mat, MOD_BASECOLORBLEND_MAP)
    ao_image = find_material_image(mat, MOD_AO_MAP)
    mcmao_image = find_material_image(mat, MOD_MCMAO_MAP)
    prop_blend, blend_value = get_blend_strength(obj, mat)
    prop_ao, ao_value = get_ao_strength(obj, mat)
    prop_group = get_material_group(obj, mat)

    count = count_maps(diffuse_image, ao_image, blend_image, mcmao_image)
    if count == 0:
        return None

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    reset_cursor()
    # space
    advance_cursor(-count)
    # maps
    ao_node = blend_node = diffuse_node = mcmao_node = None
    if mcmao_image is not None:
        mcmao_node = make_image_node(nodes, mcmao_image, "mcmao_tex")
        step_cursor()
    if ao_image is not None:
        ao_node = make_image_node(nodes, ao_image, "diffuse_tex")
        step_cursor()
    if blend_image is not None:
        blend_node = make_image_node(nodes, blend_image, "diffuse_tex")
        step_cursor()
    if diffuse_image is not None:
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        step_cursor()
    # groups
    if mcmao_image is not None:
        group = get_node_group("color_head_mixer")
        group_node = make_node_group_node(nodes, group, "Base Color Head Mixer", "color_" + prop_group + "_mixer")
        drop_cursor(0.3)
    elif blend_image is not None:
        group = get_node_group("color_blend_ao_mixer")
        group_node = make_node_group_node(nodes, group, "Base Color Mixer", "color_" + prop_group + "_mixer")
    else:
        group = get_node_group("color_ao_mixer")
        group_node = make_node_group_node(nodes, group, "Base Color Mixer", "color_" + prop_group + "_mixer")
    # values
    if diffuse_image is None:
        set_node_input(group_node, "Diffuse", shader.inputs["Base Color"].default_value)
    if blend_image is not None:
        set_node_input(group_node, "Blend Strength", blend_value)
    if mcmao_image is not None:
        set_node_input(group_node, "Mouth AO", props.skin_mouth_ao)
        set_node_input(group_node, "Nostril AO", props.skin_nostril_ao)
        set_node_input(group_node, "Lips AO", props.skin_lips_ao)
    set_node_input(group_node, "AO Strength", ao_value)
    # links
    if mcmao_image is not None:
        link_nodes(links, mcmao_node, "Color", group_node, "MCMAO")
        link_nodes(links, mcmao_node, "Alpha", group_node, "LLAO")
    if diffuse_image is not None:
        link_nodes(links, diffuse_node, "Color", group_node, "Diffuse")
    if blend_image is not None:
        link_nodes(links, blend_node, "Color", group_node, "Blend")
    if ao_image is not None:
        link_nodes(links, ao_node, "Color", group_node, "AO")
    link_nodes(links, group_node, "Base Color", shader, "Base Color")

    return group_node


def connect_subsurface(obj, mat, shader, diffuse_node):
    props = bpy.context.scene.CC3ImportProps

    sss_image = find_material_image(mat, SUBSURFACE_MAP)
    trans_image = find_material_image(mat, MOD_TRANSMISSION_MAP)
    prop_radius, sss_radius = get_sss_radius(obj, mat)
    prop_falloff, sss_falloff = get_sss_falloff(obj, mat)
    prop_group = get_material_group(obj, mat)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    count = count_maps(trans_image, sss_image)
    if count == 0 and not is_hair_object(obj, mat) and not is_skin_material(mat):
        return None

    reset_cursor()
    # space
    advance_cursor(-count)
    # maps
    sss_node = trans_node = None
    if trans_image is not None:
        trans_node = make_image_node(nodes, trans_image, "transmission_tex")
        step_cursor()
    if sss_image is not None:
        sss_node = make_image_node(nodes, sss_image, "sss_tex")
        step_cursor()
    # group
    group = get_node_group("subsurface_mixer")
    group_node = make_node_group_node(nodes, group, "Subsurface Mixer", "subsurface_" + prop_group + "_mixer")
    # values
    set_node_input(group_node, "Radius", sss_radius * UNIT_SCALE)
    set_node_input(group_node, "Falloff", sss_falloff)
    if diffuse_node is None:
        set_node_input(group_node, "Diffuse", shader.inputs["Base Color"].default_value)
    # links
    else:
        link_nodes(links, diffuse_node, "Base Color", group_node, "Diffuse")
        link_nodes(links, diffuse_node, "Color", group_node, "Diffuse")
    link_nodes(links, sss_node, "Color", group_node, "Scatter")
    link_nodes(links, trans_node, "Color", group_node, "Transmission")
    link_nodes(links, group_node, "Subsurface", shader, "Subsurface")
    link_nodes(links, group_node, "Subsurface Radius", shader, "Subsurface Radius")
    link_nodes(links, group_node, "Subsurface Color", shader, "Subsurface Color")

    # subsurface translucency
    if is_skin_material(mat) or is_hair_object(obj, mat):
        mat.use_sss_translucency = True
    else:
        mat.use_sss_translucency = False

    return group_node


def connect_msr(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps

    metallic_image = find_material_image(mat, METALLIC_MAP)
    specular_image = find_material_image(mat, SPECULAR_MAP)
    mask_image = find_material_image(mat, MOD_SPECMASK_MAP)
    roughness_image = find_material_image(mat, ROUGHNESS_MAP)
    prop_spec, specular_strength = get_specular_strength(obj, mat)
    prop_roughness, roughness_remap = get_roughness_strength(obj, mat)
    prop_group = get_material_group(obj, mat)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    count = count_maps(mask_image, specular_image, roughness_image, metallic_image)
    if count == 0:
        return None

    reset_cursor()
    # space
    advance_cursor(-count)
    # maps
    metallic_node = specular_node = roughness_node = mask_node = None
    if roughness_image is not None:
        roughness_node = make_image_node(nodes, roughness_image, "roughness_tex")
        step_cursor()
    if mask_image is not None:
        mask_node = make_image_node(nodes, mask_image, "specular_mask_tex")
        step_cursor()
    if specular_image is not None:
        specular_node = make_image_node(nodes, specular_image, "specular_tex")
        step_cursor()
    if metallic_image is not None:
        metallic_node = make_image_node(nodes, metallic_image, "metallic_tex")
        step_cursor()
    # groups
    group = get_node_group("msr_mixer")
    group_node = make_node_group_node(nodes, group, "Metallic, Specular & Roughness Mixer", "msr_" + prop_group + "_mixer")
    # values
    set_node_input(group_node, "Specular", specular_strength)
    set_node_input(group_node, "Roughness Remap", roughness_remap)
    # links
    link_nodes(links, metallic_node, "Color", group_node, "Metallic")
    link_nodes(links, specular_node, "Color", group_node, "Specular")
    link_nodes(links, mask_node, "Color", group_node, "Specular Mask")
    link_nodes(links, roughness_node, "Color", group_node, "Roughness")
    link_nodes(links, group_node, "Metallic", shader, "Metallic")
    link_nodes(links, group_node, "Specular", shader, "Specular")
    link_nodes(links, group_node, "Roughness", shader, "Roughness")

    return group_node


def connect_emission_alpha(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps

    emission_image = find_material_image(mat, EMISSION_MAP)
    alpha_image = find_material_image(mat, ALPHA_MAP)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    emission_node = alpha_node = None
    # emission
    reset_cursor()
    if emission_image is not None:
        emission_node = make_image_node(nodes, emission_image, "emission_tex")
        link_nodes(links, emission_node, "Color", shader, "Emission")
    # alpha
    reset_cursor()
    if alpha_image is not None:
        alpha_node = make_image_node(nodes, alpha_image, "opacity_tex")
        dir,file = os.path.split(alpha_image.filepath)
        if "_diffuse." in file.lower() or "_albedo." in file.lower():
            link_nodes(links, alpha_node, "Alpha", shader, "Alpha")
        else:
            link_nodes(links, alpha_node, "Color", shader, "Alpha")
    # material settings
    if is_hair_object(obj, mat) or is_eyelash_material(mat):
        set_material_alpha(mat, "HASHED")
    elif shader.inputs["Alpha"].default_value < 1.0:
        set_material_alpha(mat, props.blend_mode)
    else:
        set_material_alpha(mat, "OPAQUE")


def connect_normal(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps

    normal_node = bump_node = blend_node = micro_node = mask_node = tiling_node = None
    normal_image = find_material_image(mat, NORMAL_MAP)
    bump_image = find_material_image(mat, BUMP_MAP)
    blend_image = find_material_image(mat, MOD_NORMALBLEND_MAP)
    micro_image = find_material_image(mat, MOD_MICRONORMAL_MAP)
    mask_image = find_material_image(mat, MOD_MICRONORMALMASK_MAP)
    prop_bump, bump_strength = get_bump_strength(obj, mat)
    prop_blend, blend_strength = get_normal_blend_strength(obj, mat)
    prop_micronormal, micronormal_strength = get_micronormal_strength(obj, mat)
    prop_tiling, micronormal_tiling = get_micronormal_tiling(obj, mat)
    prop_group = get_material_group(obj, mat)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    count = count_maps(bump_image, mask_image, micro_image, blend_image, normal_image)
    if count == 0:
        return None

    reset_cursor()
    # space
    advance_cursor(-count)
    # maps
    if bump_image is not None:
        bump_node = make_image_node(nodes, bump_image, "bump_tex")
        step_cursor()
    if mask_image is not None:
        mask_node = make_image_node(nodes, mask_image, "micro_normal_mask_tex")
        step_cursor()
    if micro_image is not None:
        advance_cursor(-1)
        drop_cursor(0.75)
        group = get_node_group("tiling_mapping")
        tiling_node = make_node_group_node(nodes, group, "Micro Normal Tiling", "tiling_" + prop_group + "_mapping")
        advance_cursor()
        micro_node = make_image_node(nodes, micro_image, "micro_normal_tex")
        step_cursor()
    if blend_image is not None:
        blend_node = make_image_node(nodes, blend_image, "normal_blend_tex")
        step_cursor()
    if normal_image is not None:
        normal_node = make_image_node(nodes, normal_image, "normal_tex")
        step_cursor()
    # groups
    if bump_image is not None:
        group = get_node_group("bump_mixer")
    elif normal_image is not None and bump_image is None and mask_image is None and \
            micro_image is None and blend_image is None:
        normalmap_node = make_shader_node(nodes, "ShaderNodeNormalMap")
        link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        link_nodes(links, normalmap_node, "Normal", shader, "Normal")
        return normalmap_node
    elif blend_image is not None:
        group = get_node_group("normal_micro_mask_blend_mixer")
    else:
        group =  get_node_group("normal_micro_mask_mixer")
    group_node = make_node_group_node(nodes, group, "Normal Mixer", "normal_" + prop_group + "_mixer")
    # values
    set_node_input(group_node, "Normal Blend Strength", blend_strength)
    set_node_input(group_node, "Micro Normal Strength", micronormal_strength)
    set_node_input(group_node, "Bump Map Height", bump_strength / 1000)
    set_node_input(tiling_node, "Tiling", micronormal_tiling)
    # links
    link_nodes(links, group_node, "Normal", shader, "Normal")
    link_nodes(links, normal_node, "Color", group_node, "Normal")
    link_nodes(links, bump_node, "Color", group_node, "Bump Map")
    link_nodes(links, blend_node, "Color", group_node, "Normal Blend")
    link_nodes(links, micro_node, "Color", group_node, "Micro Normal")
    link_nodes(links, tiling_node, "Vector", micro_node, "Vector")
    link_nodes(links, mask_node, "Color", group_node, "Micro Normal Mask")

    return group_node

def reconstruct_obj_materials(obj):
    mesh = obj.data
    # remove all materials
    mesh.materials.clear()
    # add new materials
    #  head/body/arm/leg/nails/eyelash/teeth/tongue
    mat_head = bpy.data.materials.new("Std_Skin_Head") #0
    mat_body = bpy.data.materials.new("Std_Skin_Body") #1
    mat_arm = bpy.data.materials.new("Std_Skin_Arm") #2
    mat_leg = bpy.data.materials.new("Std_Skin_Leg") #3
    mat_nails = bpy.data.materials.new("Std_Nails") #4
    mat_eyelash = bpy.data.materials.new("Std_Eyelash") #5
    mat_uteeth= bpy.data.materials.new("Std_Upper_Teeth") #6
    mat_lteeth = bpy.data.materials.new("Std_Lower_Teeth") #7
    mat_tongue = bpy.data.materials.new("Std_Tongue") #8
    mat_reye = bpy.data.materials.new("Std_Eye_R") #9
    mat_leye = bpy.data.materials.new("Std_Eye_L") #10
    mat_rcornea = bpy.data.materials.new("Std_Cornea_R") #11
    mat_lcornea = bpy.data.materials.new("Std_Cornea_L") #12
    mesh.materials.append(mat_head)
    mesh.materials.append(mat_body)
    mesh.materials.append(mat_arm)
    mesh.materials.append(mat_leg)
    mesh.materials.append(mat_nails)
    mesh.materials.append(mat_eyelash)
    mesh.materials.append(mat_uteeth)
    mesh.materials.append(mat_lteeth)
    mesh.materials.append(mat_tongue)
    mesh.materials.append(mat_reye)
    mesh.materials.append(mat_leye)
    mesh.materials.append(mat_rcornea)
    mesh.materials.append(mat_lcornea)
    ul = mesh.uv_layers[0]
    # figure out which polygon belongs to which material from the vertex groups, uv coords and polygon indices
    for poly in mesh.polygons:
        loop_index = poly.loop_indices[0]
        loop_entry = mesh.loops[loop_index]
        vertex = mesh.vertices[loop_entry.vertex_index]
        group = vertex.groups[0].group
        uv = ul.data[loop_entry.index].uv
        x = uv[0]
        if x > 5:
            poly.material_index = 5 # eyelash
        elif x > 4:
            poly.material_index = 4 # nails
        elif x > 3:
            poly.material_index = 3 # legs
        elif x > 2:
            poly.material_index = 2 # arms
        elif x > 1:
            poly.material_index = 1 # body
        else:
            # head/eyes/tongue/teeth
            # vertex groups: 0 - tongue, 1 - body(head), 2 - eye, 3 - teeth
            if group == 0:
                poly.material_index = 8
            elif group == 1:
                poly.material_index = 0
            elif group == 2:
                # assign by polygon index (and hope these stay the same across exports)
                # eye_r: 14342-14501
                # cornea_r: 14502-14661
                # eye_l: 14662-14821
                # cornea_l: 14822-14981
                if poly.index >= 14822:
                    poly.material_index = 12
                elif poly.index >= 14662:
                    poly.material_index = 10
                elif poly.index >= 14502:
                    poly.material_index = 11
                else:
                    poly.material_index = 9
            else: #3
                # upper teeth: 14982-16162
                # lower teeth: 16163-17402
                if poly.index >= 16163:
                    poly.material_index = 7
                else:
                    poly.material_index = 6

