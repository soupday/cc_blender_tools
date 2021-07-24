# Copyright (C) 2021 Victor Soupday
# This file is part of CC3_Blender_Tools <https://github.com/soupday/cc3_blender_tools>
#
# CC3_Blender_Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CC3_Blender_Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CC3_Blender_Tools.  If not, see <https://www.gnu.org/licenses/>.

import bpy
import os
import shutil
import math
from . import materials
from . import shaderutils
from . import nodeutils
from . import meshutils
from . import modutils
from . import linkutils
from . import utils
from . import params
from . import vars
from . import addon_updater_ops


debug_counter = 0
block_update = False


def detect_skin_material(mat):
    name = mat.name.lower()
    if "std_skin_" in name or "ga_skin_" in name:
        return True
    return False


def detect_key_words(hints, text):
    for hint in hints:
        h = hint.strip()
        starts = False
        ends = False
        deny = False
        if h != "":
            if h[0] == "!":
                h = h[1:]
                deny = True
            if h[0] == "^":
                h = h[1:]
                starts = True
            if h[-1] == "$":
                h = h[0:-1]
                ends = True
            if starts and ends and text.startswith(h) and text.endswith(h):
                if deny:
                    return "Deny"
                else:
                    return "True"
            elif starts and text.startswith(h):
                if deny:
                    return "Deny"
                else:
                    return "True"
            elif ends and text.endswith(h):
                if deny:
                    return "Deny"
                else:
                    return "True"
            elif h in text:
                if deny:
                    return "Deny"
                else:
                    return "True"
    return "False"


def detect_scalp_material(mat):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    material_name = mat.name.lower()
    hints = prefs.hair_scalp_hint.split(",")
    detect = detect_key_words(hints, material_name)
    if detect == "Deny":
        utils.log_info(mat.name + ": has deny keywords, defininately not scalp!")
    elif detect == "True":
        utils.log_info(mat.name + ": has keywords, is scalp.")
    return detect


def detect_eyelash_material(mat):
    name = mat.name.lower()
    if "std_eyelash" in name or "ga_eyelash" in name:
        return True
    return False


def detect_teeth_material(mat):
    name = mat.name.lower()
    if "std_upper_teeth" in name:
        return True
    elif "std_lower_teeth" in name:
        return True
    return False


def detect_tongue_material(mat):
    name = mat.name.lower()
    if "std_tongue" in name or "ga_tongue" in name:
        return True
    return False


def detect_nails_material(mat):
    name = mat.name.lower()
    if "std_nails" in name or "ga_nails" in name:
        return True
    return False


def detect_body_object(obj):
    name = obj.name.lower()
    if "base_body" in name or "game_body" in name:
        return True
    return False


def detect_smart_hair_maps(mat_cache):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    props = bpy.context.scene.CC3ImportProps

    mat = mat_cache.material

    if (find_image_file([mat_cache.dir, props.import_main_tex_dir], mat, vars.MOD_HAIR_FLOW_MAP) is not None or
        find_image_file([mat_cache.dir, props.import_main_tex_dir], mat, vars.MOD_HAIR_ROOT_MAP) is not None or
        find_image_file([mat_cache.dir, props.import_main_tex_dir], mat, vars.MOD_HAIR_ID_MAP) is not None or
        find_image_file([mat_cache.dir, props.import_main_tex_dir], mat, vars.MOD_HAIR_VERTEX_COLOR_MAP) is not None):
        return "True"
    return False


def detect_hair_object(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    hints = prefs.hair_hint.split(",")
    object_name = obj.name.lower()
    material_name = mat.name.lower()

    # try to find one of the new hair maps: "Flow Map" or "Root Map"
    cache = get_material_cache(mat)
    if detect_smart_hair_maps(cache):
        cache.smart_hair = True
        utils.log_info(obj.name + "/" + mat.name + ": has hair shader textures, is hair.")
        return "True"
    else:
        cache.smart_hair = False

    detect_obj = detect_key_words(hints, object_name)
    detect_mat =  detect_key_words(hints, material_name)

    if detect_obj == "Deny" or detect_mat == "Deny":
        utils.log_info(obj.name + "/" + mat.name + ": has deny keywords, definitely not hair!")
        return "Deny"

    if detect_obj == "True" or detect_mat == "True":
        utils.log_info(obj.name + "/" + mat.name + ": has hair keywords, is hair.")
        return "True"

    return "False"


def detect_cornea_material(mat):
    if "std_cornea_" in mat.name.lower():
        return True
    return False


def detect_eye_material(mat):
    if "std_eye_" in mat.name.lower():
        return True
    return False


def detect_material_side(mat, side):
    name = mat.name.lower()
    if side == "RIGHT":
        return "_r" in name
    elif side == "LEFT":
        return "_l" in name
    elif side == "UPPER":
        return "upper_" in name
    elif side == "LOWER":
        return "lower_" in name


def detect_tearline_material(mat):
    if "std_tearline_" in mat.name.lower():
        return True
    return False


def detect_eye_occlusion_material(mat):
    if "std_eye_occlusion_" in mat.name.lower():
        return True
    return False


def get_material_group(mat_cache):
    """Returns the lowercase material group.
    This group is used to identify the property group the material belongs to
    and thus which input values to change when material parameters are changed.
    See function: set_node_from_property(node)
    """
    mt = mat_cache.material_type
    return mt.lower()


def get_bump_strength(cache):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_hair() or cache.is_eyelash() or cache.is_scalp():
        return "hair_bump", cache.parameters.hair_bump
    return "default_bump", cache.parameters.default_bump


def get_alpha_strength(cache):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_hair():
        return "hair_opacity", cache.parameters.hair_opacity
    elif cache.is_scalp():
        return "hair_scalp_opacity", cache.parameters.hair_scalp_opacity
    elif cache.is_eyelash():
        return "hair_eyelash_opacity", cache.parameters.hair_scalp_opacity
    return "default_opacity", cache.parameters.default_opacity



def get_micronormal_strength(cache):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_head():
        return "skin_head_micronormal", cache.parameters.skin_head_micronormal
    elif cache.is_body():
        return "skin_body_micronormal", cache.parameters.skin_body_micronormal
    elif cache.is_arm():
        return "skin_arm_micronormal", cache.parameters.skin_arm_micronormal
    elif cache.is_leg():
        return "skin_leg_micronormal", cache.parameters.skin_leg_micronormal
    elif cache.is_teeth():
        return "teeth_micronormal", cache.parameters.teeth_micronormal
    elif cache.is_nails():
        return "nails_micronormal", cache.parameters.nails_micronormal
    elif cache.is_tongue():
        return "tongue_micronormal", cache.parameters.tongue_micronormal
    elif cache.is_cornea():
        return "eye_sclera_normal", 1 - cache.parameters.eye_sclera_normal
    return "default_micronormal", cache.parameters.default_micronormal


def get_micronormal_tiling(cache):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_head():
        return "skin_head_tiling", cache.parameters.skin_head_tiling
    elif cache.is_body():
        return "skin_body_tiling", cache.parameters.skin_body_tiling
    elif cache.is_arm():
        return "skin_arm_tiling", cache.parameters.skin_arm_tiling
    elif cache.is_leg():
        return "skin_leg_tiling", cache.parameters.skin_leg_tiling
    elif cache.is_teeth():
        return "teeth_tiling", cache.parameters.teeth_tiling
    elif cache.is_tongue():
        return "tongue_tiling", cache.parameters.tongue_tiling
    elif cache.is_tongue():
        return "nails_tiling", cache.parameters.nails_tiling
    elif cache.is_cornea():
        return "eye_sclera_tiling", cache.parameters.eye_sclera_tiling
    return "default_tiling", cache.parameters.default_tiling


def get_specular_strength(cache, shader):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_cornea():
        return "eye_specular", cache.parameters.eye_specular
    elif cache.is_skin():
        if props.setup_mode == "ADVANCED":
            return "skin_specular", cache.parameters.skin_specular
        else:
            return "skin_basic_specular", cache.parameters.skin_basic_specular
    elif cache.is_hair():
        return "hair_specular", cache.parameters.hair_specular
    elif cache.is_scalp():
        return "hair_scalp_specular", cache.parameters.hair_scalp_specular
    elif cache.is_eyelash():
        return "hair_eyelash_specular", cache.parameters.hair_eyelash_specular
    elif cache.is_nails():
        return "nails_specular", cache.parameters.nails_specular
    elif cache.is_teeth():
        return "teeth_specular", cache.parameters.teeth_specular
    elif cache.is_tongue():
        return "tongue_specular", cache.parameters.tongue_specular
    return "default_specular", nodeutils.get_node_input(shader, "Specular", 0.5)


def get_roughness_remap(cache):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_skin():
        if props.setup_mode == "ADVANCED":
            return "skin_roughness", cache.parameters.skin_roughness
        else:
            return "skin_basic_roughness", cache.parameters.skin_basic_roughness
    elif cache.is_hair():
        return "hair_roughness", cache.parameters.hair_roughness
    elif cache.is_scalp():
        return "hair_scalp_roughness", cache.parameters.hair_scalp_roughness
    elif cache.is_eyelash():
        return "hair_eyelash_roughness", cache.parameters.hair_eyelash_roughness
    elif cache.is_nails():
        return "nails_roughness", cache.parameters.nails_roughness
    elif cache.is_teeth():
        return "teeth_roughness", cache.parameters.teeth_roughness
    elif cache.is_tongue():
        return "tongue_roughness", cache.parameters.tongue_roughness
    return "default_roughness", cache.parameters.default_roughness


def get_roughness_power(cache):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_skin() and props.setup_mode == "ADVANCED":
        return "skin_roughness_power", cache.parameters.skin_roughness_power
    return "none", 1.0


def get_ao_strength(cache):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_cornea():
        return "eye_ao", cache.parameters.eye_ao
    elif cache.is_skin():
        return "skin_ao", cache.parameters.skin_ao
    elif cache.is_hair() or cache.is_scalp() or cache.is_eyelash():
        return "hair_ao", cache.parameters.hair_ao
    elif cache.is_nails():
        return "nails_ao", cache.parameters.nails_ao
    elif cache.is_teeth():
        return "teeth_ao", cache.parameters.teeth_ao
    elif cache.is_tongue():
        return "tongue_ao", cache.parameters.tongue_ao
    return "default_ao", cache.parameters.default_ao


def get_blend_strength(cache):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_cornea():
        return "eye_blend", cache.parameters.eye_blend
    elif cache.is_skin():
        return "skin_blend", cache.parameters.skin_blend
    elif cache.is_hair() or cache.is_scalp() or cache.is_eyelash():
        return "hair_blend", cache.parameters.hair_blend
    return "default_blend", cache.parameters.default_blend


def get_normal_blend_strength(cache):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_skin():
        return "skin_normal_blend", cache.parameters.skin_normal_blend
    return "default_normal_blend", cache.parameters.default_normal_blend


def get_sss_radius(cache):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_cornea():
        return "eye_sss_radius", cache.parameters.eye_sss_radius
    elif cache.is_skin():
        return "skin_sss_radius", cache.parameters.skin_sss_radius
    elif cache.is_hair() or cache.is_scalp() or cache.is_eyelash():
        return "hair_sss_radius", cache.parameters.hair_sss_radius
    elif cache.is_nails():
        return "nails_sss_radius", cache.parameters.nails_sss_radius
    elif cache.is_teeth():
        return "teeth_sss_radius", cache.parameters.teeth_sss_radius
    elif cache.is_tongue():
        return "tongue_sss_radius", cache.parameters.tongue_sss_radius
    return "default_sss_radius", cache.parameters.default_sss_radius


def get_sss_falloff(cache):
    props = bpy.context.scene.CC3ImportProps

    if cache.is_cornea():
        return "eye_sss_falloff", cache.parameters.eye_sss_falloff
    elif cache.is_skin():
        return "skin_sss_falloff", cache.parameters.skin_sss_falloff
    elif cache.is_hair() or cache.is_scalp() or cache.is_eyelash():
        return "hair_sss_falloff", cache.parameters.hair_sss_falloff
    elif cache.is_nails():
        return "nails_sss_falloff", cache.parameters.nails_sss_falloff
    elif cache.is_teeth():
        return "teeth_sss_falloff", cache.parameters.teeth_sss_falloff
    elif cache.is_tongue():
        return "tongue_sss_falloff", cache.parameters.tongue_sss_falloff
    return "default_sss_falloff", cache.parameters.default_sss_falloff



# load an image from a file, but try to find it in the existing images first
def load_image(filename, color_space):

    for i in bpy.data.images:
        if (i.type == "IMAGE" and i.filepath != ""):
            try:
                if os.path.normcase(i.filepath) == os.path.normcase(filename):
                    utils.log_info("    Using existing image: " + i.filepath)
                    return i
            except:
                pass

    try:
        utils.log_info("    Loading new image: " + filename)
        image = bpy.data.images.load(filename)
        image.colorspace_settings.name = color_space
        return image
    except Exception as e:
        utils.log_error("Unable to load image: " + filename, e)
        return None


# remove any .001 from the material name
def strip_name(name):
    if name[-3:].isdigit() and name[-4] == ".":
        name = name[:-4]
    return name

## Search the directory for an image filename that contains the search substring
def find_image_file(dirs, mat, suffix_list):
    material_name = strip_name(mat.name).lower()
    last = ""
    for dir in dirs:
        if last != dir and dir != "" and os.path.normcase(dir) != os.path.normcase(last) and \
                os.path.exists(dir):
            last = dir
            files = os.listdir(dir)
            for file in files:
                file_name = file.lower()
                if file_name.startswith(material_name):
                    for suffix in suffix_list:
                        search = "_" + suffix + "."
                        if search in file_name:
                            return os.path.join(dir, file)
    return None


def find_material_image(mat, suffix_list):
    """Try to find the texture for a material input by searching for the material name
       appended with the possible suffixes e.g. Vest_diffuse or Hair_roughness
    """
    props = bpy.context.scene.CC3ImportProps
    cache = get_material_cache(mat)

    # try to find the image in the files first
    image_file = find_image_file([cache.dir, props.import_main_tex_dir], mat, suffix_list)
    if image_file:
        color_space = "Non-Color"
        if "diffuse" in suffix_list or "sclera" in suffix_list:
            color_space = "sRGB"
        return load_image(image_file, color_space)

    # then try to find the image from the material cache
    if cache is not None:
        if "diffuse" in suffix_list:
            return cache.diffuse
        elif "specular" in suffix_list:
            return cache.specular
        elif "opacity" in suffix_list:
            return cache.alpha
        elif "normal" in suffix_list:
            return cache.normal
        elif "bump" in suffix_list:
            return cache.bump
        elif "weightmap" in suffix_list and cache.temp_weight_map is not None:
            return cache.temp_weight_map

    return None


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

    set_material_alpha(mat, method)

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
    elif method == "CLIP":
        mat.blend_method = "CLIP"
        mat.shadow_method = "CLIP"
        mat.use_backface_culling = False
        mat.alpha_threshold = 0.5
    else:
        mat.blend_method = "OPAQUE"
        mat.shadow_method = "OPAQUE"
        mat.use_backface_culling = False


def connect_tearline_material(obj, mat, shader):
    mat_cache = get_material_cache(mat)
    props = bpy.context.scene.CC3ImportProps
    nodeutils.set_node_input(shader, "Base Color", (1.0, 1.0, 1.0, 1.0))
    nodeutils.set_node_input(shader, "Metallic", 1.0)
    nodeutils.set_node_input(shader, "Specular", 1.0)
    nodeutils.set_node_input(shader, "Roughness", mat_cache.parameters.tearline_roughness)
    nodeutils.set_node_input(shader, "Alpha", mat_cache.parameters.tearline_alpha)
    shader.name = utils.unique_name("eye_tearline_shader")
    set_material_alpha(mat, props.blend_mode)
    mat.shadow_method = "NONE"


def connect_eye_occlusion_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader.name = utils.unique_name("eye_occlusion_shader")
    nodeutils.set_node_input(shader, "Base Color", mat_cache.parameters.eye_occlusion_color)
    nodeutils.set_node_input(shader, "Metallic", 0.0)
    nodeutils.set_node_input(shader, "Specular", 0.0)
    nodeutils.set_node_input(shader, "Roughness", 1.0)

    nodeutils.reset_cursor()

    # groups
    group = nodeutils.get_node_group("eye_occlusion_mask")
    occ_node = nodeutils.make_node_group_node(nodes, group, "Eye Occulsion Alpha", "eye_occlusion_mask")
    # values
    params.set_from_prop_matrix(occ_node, mat_cache, "eye_occlusion_mask")
    # links
    nodeutils.link_nodes(links, occ_node, "Alpha", shader, "Alpha")

    set_material_alpha(mat, props.blend_mode)
    mat.shadow_method = "NONE"


def connect_eye_occlusion_shader(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader = shaderutils.replace_shader_node(nodes, links, shader, "Eye Occlusion Shader", "rl_eye_occlusion_shader")

    nodeutils.reset_cursor()

    params.set_from_prop_matrix(shader, mat_cache, "rl_eye_occlusion_shader")

    set_material_alpha(mat, props.blend_mode)
    mat.shadow_method = "NONE"


def connect_basic_eye_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Base Color
    #
    nodeutils.reset_cursor()
    diffuse_image =  find_material_image(mat, vars.BASE_COLOR_MAP)
    if diffuse_image is not None:
        diffuse_node = nodeutils.make_image_node(nodes, diffuse_image, "diffuse_tex")
        nodeutils.advance_cursor(1.0)
        hsv_node = nodeutils.make_shader_node(nodes, "ShaderNodeHueSaturation", 0.6)
        hsv_node.label = "HSV"
        hsv_node.name = utils.unique_name("eye_basic_hsv")
        nodeutils.set_node_input(hsv_node, "Value", mat_cache.parameters.eye_basic_brightness)
        # links
        nodeutils.link_nodes(links, diffuse_node, "Color", hsv_node, "Color")
        nodeutils.link_nodes(links, hsv_node, "Color", shader, "Base Color")

    # Metallic
    #
    nodeutils.reset_cursor()
    metallic_node = nodeutils.make_value_node(nodes, "Eye Metallic", "eye_metallic", 0.0)
    nodeutils.link_nodes(links, metallic_node, "Value", shader, "Metallic")

    # Specular
    #
    nodeutils.reset_cursor()
    specular_node = nodeutils.make_value_node(nodes, "Eye Specular", "eye_specular", mat_cache.parameters.eye_specular)
    nodeutils.link_nodes(links, specular_node, "Value", shader, "Specular")

    # Roughness
    #
    nodeutils.reset_cursor()
    roughness_node = nodeutils.make_value_node(nodes, "Eye Roughness", "eye_basic_roughness", mat_cache.parameters.eye_basic_roughness)
    nodeutils.link_nodes(links, roughness_node, "Value", shader, "Roughness")

    # Alpha
    #
    nodeutils.set_node_input(shader, "Alpha", 1.0)

    # Normal
    #
    nodeutils.reset_cursor()
    normal_image = find_material_image(mat, vars.SCLERA_NORMAL_MAP)
    if normal_image is not None:
        strength_node = nodeutils.make_value_node(nodes, "Normal Strength", "eye_basic_normal", mat_cache.parameters.eye_basic_normal)
        normal_node = nodeutils.make_image_node(nodes, normal_image, "normal_tex")
        nodeutils.advance_cursor()
        normalmap_node = nodeutils.make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        nodeutils.link_nodes(links, strength_node, "Value", normalmap_node, "Strength")
        nodeutils.link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        nodeutils.link_nodes(links, normalmap_node, "Normal", shader, "Normal")

    # Clearcoat
    #
    nodeutils.set_node_input(shader, "Clearcoat", 1.0)
    nodeutils.set_node_input(shader, "Clearcoat Roughness", 0.15)
    mat.use_screen_refraction = False

    return


def connect_adv_eye_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Iris Mask
    nodeutils.reset_cursor()
    # groups
    group = nodeutils.get_node_group("iris_mask")
    iris_mask_node = nodeutils.make_node_group_node(nodes, group, "Iris Mask", "iris_mask")
    # values
    params.set_from_prop_matrix(iris_mask_node, mat_cache, "iris_mask")
    # move
    nodeutils.move_new_nodes(-3000, 0)
    nodeutils.clear_cursor()

    # Base Color
    nodeutils.reset_cursor()
    # maps
    diffuse_image = find_material_image(mat, vars.BASE_COLOR_MAP)
    sclera_image = find_material_image(mat, vars.SCLERA_MAP)
    blend_image = find_material_image(mat, vars.MOD_BASECOLORBLEND_MAP)
    ao_image = find_material_image(mat, vars.MOD_AO_MAP)
    diffuse_node = sclera_node = blend_node = ao_node = iris_tiling_node = sclera_tiling_node = None
    nodeutils.advance_cursor(-utils.count_maps(diffuse_image, sclera_image, blend_image, ao_image))
    if diffuse_image is not None:
        nodeutils.advance_cursor(-1)
        nodeutils.drop_cursor(0.75)
        group = nodeutils.get_node_group("tiling_pivot_mapping")
        iris_tiling_node = nodeutils.make_node_group_node(nodes, group, "Iris Scaling", "tiling_color_iris_mapping")
        nodeutils.set_node_input(iris_tiling_node, "Pivot", (0.5, 0.5, 0))
        nodeutils.advance_cursor()
        diffuse_node = nodeutils.make_image_node(nodes, diffuse_image, "diffuse_tex")
        nodeutils.step_cursor()
    if sclera_image is not None:
        nodeutils.advance_cursor(-1)
        nodeutils.drop_cursor(0.75)
        group = nodeutils.get_node_group("tiling_pivot_mapping")
        sclera_tiling_node = nodeutils.make_node_group_node(nodes, group, "Sclera Scaling", "tiling_color_sclera_mapping")
        nodeutils.set_node_input(sclera_tiling_node, "Pivot", (0.5, 0.5, 0))
        nodeutils.set_node_input(sclera_tiling_node, "Tiling", 1.0 / mat_cache.parameters.eye_sclera_scale)
        nodeutils.advance_cursor()
        sclera_node = nodeutils.make_image_node(nodes, sclera_image, "sclera_tex")
        sclera_node.extension = "EXTEND"
        nodeutils.step_cursor()
    if ao_image is not None:
        ao_node = nodeutils.make_image_node(nodes, ao_image, "ao_tex")
        nodeutils.step_cursor()
    if blend_image is not None:
        blend_node = nodeutils.make_image_node(nodes, blend_image, "blend_tex")
        nodeutils.step_cursor()
    # groups
    group = nodeutils.get_node_group("color_eye_mixer")
    color_node = nodeutils.make_node_group_node(nodes, group, "Eye Base Color", "color_eye_mixer")
    # values
    params.set_from_prop_matrix(color_node, mat_cache, "color_eye_mixer")
    # links
    nodeutils.link_nodes(links, iris_mask_node, "Mask", color_node, "Iris Mask")
    if diffuse_image is not None:
        nodeutils.link_nodes(links, iris_mask_node, "Scale", iris_tiling_node, "Tiling")
        nodeutils.link_nodes(links, iris_tiling_node, "Vector", diffuse_node, "Vector")
        nodeutils.link_nodes(links, diffuse_node, "Color", color_node, "Cornea Diffuse")
    if sclera_image is not None:
        nodeutils.link_nodes(links, sclera_tiling_node, "Vector", sclera_node, "Vector")
        nodeutils.link_nodes(links, sclera_node, "Color", color_node, "Sclera Diffuse")
    else:
        nodeutils.link_nodes(links, diffuse_node, "Color", color_node, "Sclera Diffuse")
    if blend_image is not None:
        nodeutils.link_nodes(links, blend_node, "Color", color_node, "Blend")
    if ao_image is not None:
        nodeutils.link_nodes(links, ao_node, "Color", color_node, "AO")
    nodeutils.link_nodes(links, color_node, "Base Color", shader, "Base Color")

    # SSS
    nodeutils.drop_cursor(0.65)
    nodeutils.reset_cursor()
    # groups
    group = nodeutils.get_node_group("subsurface_overlay_mixer")
    sss_node = nodeutils.make_node_group_node(nodes, group, "Eye Subsurface", "subsurface_eye_mixer")
    # values
    params.set_from_prop_matrix(sss_node, mat_cache, "subsurface_eye_mixer")
    nodeutils.set_node_input(sss_node, "Scatter1", 1.0)
    nodeutils.set_node_input(sss_node, "Scatter2", 0.0)
    # links
    nodeutils.link_nodes(links, iris_mask_node, "Mask", sss_node, "Mask")
    nodeutils.link_nodes(links, color_node, "Base Color", sss_node, "Diffuse")
    nodeutils.link_nodes(links, sss_node, "Subsurface", shader, "Subsurface")
    nodeutils.link_nodes(links, sss_node, "Subsurface Radius", shader, "Subsurface Radius")
    nodeutils.link_nodes(links, sss_node, "Subsurface Color", shader, "Subsurface Color")

    # MSR
    nodeutils.drop_cursor(0.1)
    nodeutils.reset_cursor()
    # groups
    group = nodeutils.get_node_group("msr_overlay_mixer")
    msr_node = nodeutils.make_node_group_node(nodes, group, "Eye MSR", "msr_cornea_mixer")
    # values
    params.set_from_prop_matrix(msr_node, mat_cache, "msr_cornea_mixer")
    nodeutils.set_node_input(msr_node, "Metallic1", 0)
    nodeutils.set_node_input(msr_node, "Metallic2", 0)
    # links
    nodeutils.link_nodes(links, iris_mask_node, "Mask", msr_node, "Mask")
    nodeutils.link_nodes(links, msr_node, "Metallic", shader, "Metallic")
    nodeutils.link_nodes(links, msr_node, "Specular", shader, "Specular")
    nodeutils.link_nodes(links, msr_node, "Roughness", shader, "Roughness")

    # emission and alpha
    nodeutils.set_node_input(shader, "Alpha", 1.0)
    connect_emission_alpha(obj, mat, shader)

    # Normal
    nodeutils.drop_cursor(0.1)
    nodeutils.reset_cursor()
    snormal_image = find_material_image(mat, vars.SCLERA_NORMAL_MAP)
    snormal_node = snormal_tiling_node = None
    # space
    nodeutils.advance_cursor(-utils.count_maps(snormal_image))
    # maps
    if snormal_image is not None:
        nodeutils.advance_cursor(-1)
        nodeutils.drop_cursor(0.75)
        group = nodeutils.get_node_group("tiling_mapping")
        snormal_tiling_node = nodeutils.make_node_group_node(nodes, group, "Sclera Normal Tiling", "tiling_normal_sclera_mapping")
        nodeutils.set_node_input(snormal_tiling_node, "Tiling", mat_cache.parameters.eye_sclera_tiling)
        nodeutils.advance_cursor()
        snormal_node = nodeutils.make_image_node(nodes, snormal_image, "sclera_normal_tex")
        nodeutils.step_cursor()
    # groups
    group = nodeutils.get_node_group("normal_micro_mask_mixer")
    nm_group = nodeutils.make_node_group_node(nodes, group, "Eye Normals", "normal_eye_mixer")
    # values
    params.set_from_prop_matrix(nm_group, mat_cache, "normal_eye_mixer")
    # links
    nodeutils.link_nodes(links, iris_mask_node, "Inverted Mask", nm_group, "Micro Normal Mask")
    if snormal_image is not None:
        nodeutils.link_nodes(links, snormal_node, "Color", nm_group, "Micro Normal")
        nodeutils.link_nodes(links, snormal_tiling_node, "Vector", snormal_node, "Vector")
    nodeutils.link_nodes(links, nm_group, "Normal", shader, "Normal")

    # Clearcoat
    #
    nodeutils.set_node_input(shader, "Clearcoat", 1.0)
    nodeutils.set_node_input(shader, "Clearcoat Roughness", 0.15)
    mat.use_screen_refraction = False

    return


def get_cornea_mat(obj, eye_mat, eye_mat_cache):
    props = bpy.context.scene.CC3ImportProps

    if eye_mat_cache.is_eye("LEFT"):
        side = "LEFT"
    else:
        side = "RIGHT"

    # try to find the matching cornea material in the objects materials
    #for mat in obj.data.materials:
    #    mat_cache = get_material_cache(mat)
    #    if mat_cache.is_cornea(side):
    #        return mat

    # then try to find in the material cache
    for cache in props.material_cache:
        if cache.is_cornea(side):
            return cache.material

    utils.log_error("Unable to find the " + side + " cornea material!")

    return None


def connect_refractive_eye_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # to build eye materials we need some textures from the cornea...
    cornea_mat = mat
    is_cornea = True
    is_eye = False
    if mat_cache.is_eye():
        is_cornea = False
        is_eye = True
        cornea_mat = get_cornea_mat(obj, mat, mat_cache)

    # Iris Mask
    nodeutils.reset_cursor()
    # groups
    group = nodeutils.get_node_group("iris_refractive_mask")
    iris_mask_node = nodeutils.make_node_group_node(nodes, group, "Iris Mask", "iris_mask")
    # values
    params.set_from_prop_matrix(iris_mask_node, mat_cache, "iris_mask")
    # Links
    if is_cornea:
        nodeutils.link_nodes(links, iris_mask_node, "Mask", shader, "Transmission")
    # move
    nodeutils.move_new_nodes(-3000, 0)
    nodeutils.clear_cursor()

    # Base Color
    nodeutils.reset_cursor()
    # maps
    diffuse_image = find_material_image(cornea_mat, vars.BASE_COLOR_MAP)
    sclera_image = find_material_image(cornea_mat, vars.SCLERA_MAP)
    blend_image = find_material_image(cornea_mat, vars.MOD_BASECOLORBLEND_MAP)
    ao_image = find_material_image(cornea_mat, vars.MOD_AO_MAP)
    diffuse_node = sclera_node = blend_node = ao_node = iris_tiling_node = sclera_tiling_node = None
    nodeutils.advance_cursor(-utils.count_maps(diffuse_image, sclera_image, blend_image, ao_image))
    if diffuse_image is not None:
        nodeutils.advance_cursor(-1)
        nodeutils.drop_cursor(0.75)
        group = nodeutils.get_node_group("tiling_pivot_mapping")
        iris_tiling_node = nodeutils.make_node_group_node(nodes, group, "Iris Scaling", "tiling_color_iris_mapping")
        nodeutils.set_node_input(iris_tiling_node, "Pivot", (0.5, 0.5, 0))
        nodeutils.advance_cursor()
        diffuse_node = nodeutils.make_image_node(nodes, diffuse_image, "diffuse_tex")
        nodeutils.step_cursor()
    if sclera_image is not None:
        nodeutils.advance_cursor(-1)
        nodeutils.drop_cursor(0.75)
        group = nodeutils.get_node_group("tiling_pivot_mapping")
        sclera_tiling_node = nodeutils.make_node_group_node(nodes, group, "Sclera Scaling", "tiling_color_sclera_mapping")
        nodeutils.set_node_input(sclera_tiling_node, "Pivot", (0.5, 0.5, 0))
        nodeutils.set_node_input(sclera_tiling_node, "Tiling", 1.0 / mat_cache.parameters.eye_sclera_scale)
        nodeutils.advance_cursor()
        sclera_node = nodeutils.make_image_node(nodes, sclera_image, "sclera_tex")
        sclera_node.extension = "EXTEND"
        nodeutils.step_cursor()
    if ao_image is not None:
        ao_node = nodeutils.make_image_node(nodes, ao_image, "ao_tex")
        nodeutils.step_cursor()
    if blend_image is not None:
        blend_node = nodeutils.make_image_node(nodes, blend_image, "blend_tex")
        nodeutils.step_cursor()
    # groups
    group = nodeutils.get_node_group("color_refractive_eye_mixer")
    color_node = nodeutils.make_node_group_node(nodes, group, "Eye Base Color", "color_eye_mixer")
    # values
    params.set_from_prop_matrix(color_node, mat_cache, "color_eye_mixer")
    # links
    nodeutils.link_nodes(links, iris_mask_node, "Mask", color_node, "Iris Mask")
    if is_eye:
        nodeutils.link_nodes(links, iris_mask_node, "Limbus Mask", color_node, "Limbus Mask")
    if diffuse_image is not None:
        nodeutils.link_nodes(links, iris_mask_node, "Scale", iris_tiling_node, "Tiling")
        nodeutils.link_nodes(links, iris_tiling_node, "Vector", diffuse_node, "Vector")
        nodeutils.link_nodes(links, diffuse_node, "Color", color_node, "Cornea Diffuse")
    if sclera_image is not None:
        nodeutils.link_nodes(links, sclera_tiling_node, "Vector", sclera_node, "Vector")
        nodeutils.link_nodes(links, sclera_node, "Color", color_node, "Sclera Diffuse")
    else:
        nodeutils.link_nodes(links, diffuse_node, "Color", color_node, "Sclera Diffuse")
    if blend_image is not None:
        nodeutils.link_nodes(links, blend_node, "Color", color_node, "Blend")
    if ao_image is not None:
        nodeutils.link_nodes(links, ao_node, "Color", color_node, "AO")
    if is_cornea:
        nodeutils.link_nodes(links, color_node, "Cornea Base Color", shader, "Base Color")
    else:
        nodeutils.link_nodes(links, color_node, "Eye Base Color", shader, "Base Color")

    # SSS
    nodeutils.drop_cursor(0.65)
    nodeutils.reset_cursor()
    # groups
    group = nodeutils.get_node_group("subsurface_overlay_mixer")
    sss_node = nodeutils.make_node_group_node(nodes, group, "Eye Subsurface", "subsurface_eye_mixer")
    # values
    params.set_from_prop_matrix(sss_node, mat_cache, "subsurface_eye_mixer")
    nodeutils.set_node_input(sss_node, "Scatter1", 1.0)
    nodeutils.set_node_input(sss_node, "Scatter2", 0.0)
    # links
    nodeutils.link_nodes(links, iris_mask_node, "Mask", sss_node, "Mask")
    if is_cornea:
        nodeutils.link_nodes(links, color_node, "Cornea Base Color", sss_node, "Diffuse")
    else:
        nodeutils.link_nodes(links, color_node, "Eye Base Color", sss_node, "Diffuse")
    nodeutils.link_nodes(links, sss_node, "Subsurface", shader, "Subsurface")
    nodeutils.link_nodes(links, sss_node, "Subsurface Radius", shader, "Subsurface Radius")
    nodeutils.link_nodes(links, sss_node, "Subsurface Color", shader, "Subsurface Color")

    # MSR
    nodeutils.drop_cursor(0.1)
    nodeutils.reset_cursor()
    # groups
    group = nodeutils.get_node_group("msr_overlay_mixer")
    msr_name = "msr_eye_mixer"
    if is_cornea:
        msr_name = "msr_cornea_mixer"
    msr_node = nodeutils.make_node_group_node(nodes, group, "Eye MSR", msr_name)
    # values
    params.set_from_prop_matrix(msr_node, mat_cache, msr_name)
    nodeutils.set_node_input(msr_node, "Metallic1", 0)
    nodeutils.set_node_input(msr_node, "Metallic2", 0)
    if not is_cornea:
        nodeutils.set_node_input(msr_node, "Specular2", 0.2)
        nodeutils.set_node_input(msr_node, "Roughness2", 1.0)
    # links
    nodeutils.link_nodes(links, iris_mask_node, "Mask", msr_node, "Mask")
    nodeutils.link_nodes(links, msr_node, "Metallic", shader, "Metallic")
    nodeutils.link_nodes(links, msr_node, "Specular", shader, "Specular")
    nodeutils.link_nodes(links, msr_node, "Roughness", shader, "Roughness")

    # emission and alpha
    nodeutils.set_node_input(shader, "Alpha", 1.0)
    connect_emission_alpha(obj, mat, shader)

    # Normal
    nodeutils.drop_cursor(0.1)
    nodeutils.reset_cursor()
    snormal_image = find_material_image(mat, vars.SCLERA_NORMAL_MAP)
    snormal_node = snormal_tiling_node = None
    # space
    nodeutils.advance_cursor(-utils.count_maps(snormal_image))
    # maps
    if snormal_image is not None:
        nodeutils.advance_cursor(-1)
        nodeutils.drop_cursor(0.75)
        group = nodeutils.get_node_group("tiling_mapping")
        snormal_tiling_node = nodeutils.make_node_group_node(nodes, group, "Sclera Normal Tiling", "tiling_normal_sclera_mapping")
        nodeutils.set_node_input(snormal_tiling_node, "Tiling", mat_cache.parameters.eye_sclera_tiling)
        nodeutils.advance_cursor()
        snormal_node = nodeutils.make_image_node(nodes, snormal_image, "sclera_normal_tex")
        nodeutils.step_cursor()
    # groups
    if is_cornea:
        group = nodeutils.get_node_group("normal_refractive_cornea_mixer")
    else:
        group = nodeutils.get_node_group("normal_refractive_eye_mixer")
    nm_group = nodeutils.make_node_group_node(nodes, group, "Eye Normals", "normal_eye_mixer")
    # values
    params.set_from_prop_matrix(nm_group, mat_cache, "normal_eye_mixer")
    # links
    nodeutils.link_nodes(links, iris_mask_node, "Inverted Mask", nm_group, "Sclera Mask")
    nodeutils.link_nodes(links, sclera_node, "Color", nm_group, "Sclera Map")
    nodeutils.link_nodes(links, diffuse_node, "Color", nm_group, "Cornea Map")
    if snormal_image is not None:
        nodeutils.link_nodes(links, snormal_node, "Color", nm_group, "Sclera Normal")
        nodeutils.link_nodes(links, snormal_tiling_node, "Vector", snormal_node, "Vector")
    nodeutils.link_nodes(links, nm_group, "Normal", shader, "Normal")

    # Clearcoat and material settings
    if is_cornea:
        nodeutils.set_node_input(shader, "Clearcoat", 1.0)
        nodeutils.set_node_input(shader, "Clearcoat Roughness", 0.15)
        mat.use_screen_refraction = True
        mat.refraction_depth = mat_cache.parameters.eye_refraction_depth / 1000
        nodeutils.set_default_shader_input(mat, "IOR", mat_cache.parameters.eye_ior)
    else:
        nodeutils.set_node_input(shader, "Clearcoat", 0.0)
        nodeutils.set_node_input(shader, "Specular Tint", 1.0)
        nodeutils.set_node_input(shader, "Clearcoat Roughness", 0.0)
        mat.use_screen_refraction = False

    return




def connect_adv_mouth_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Gums Mask and Gradient AO
    nodeutils.reset_cursor()
    nodeutils.advance_cursor(-2)
    # maps
    mask_image = None
    mask_node = None
    teeth = mat_cache.is_teeth()
    if teeth:
        mask_image = find_material_image(mat, vars.TEETH_GUMS_MAP)
        # if no gums mask file is found for the teeth,
        # just connect as default advanced material
        if mask_image is None:
            connect_advanced_material(obj, mat, shader, mat_cache)
            return
    # if no gradient ao file is found for the teeth or tongue
    # just connect as default advanced material
    gradient_image = find_material_image(mat, vars.MOUTH_GRADIENT_MAP)
    gradient_node = None
    if gradient_image is None:
        connect_advanced_material(obj, mat, shader, mat_cache)
        return
    nodeutils.advance_cursor(2 - utils.count_maps(mask_image, gradient_image))
    if mask_image is not None:
        mask_node = nodeutils.make_image_node(nodes, mask_image, "gums_mask_tex")
        nodeutils.step_cursor()
    if gradient_image is not None:
        gradient_node = nodeutils.make_image_node(nodes, gradient_image, "gradient_ao_tex")
        nodeutils.step_cursor()
        # nodes
        gradientrgb_node = nodeutils.make_shader_node(nodes, "ShaderNodeSeparateRGB")
        # links
        nodeutils.link_nodes(links, gradient_node, "Color", gradientrgb_node, "Image")
    # move
    nodeutils.move_new_nodes(-2000, 0)
    nodeutils.clear_cursor()

    # Base Color
    nodeutils.reset_cursor()
    nodeutils.advance_cursor(-2)
    # maps
    diffuse_image = find_material_image(mat, vars.BASE_COLOR_MAP)
    ao_image = find_material_image(mat, vars.MOD_AO_MAP)
    diffuse_node = ao_node = None
    nodeutils.advance_cursor(2 - utils.count_maps(diffuse_image, ao_image))
    if diffuse_image is not None:
        diffuse_node = nodeutils.make_image_node(nodes, diffuse_image, "diffuse_tex")
        nodeutils.step_cursor()
    if ao_image is not None:
        ao_node = nodeutils.make_image_node(nodes, ao_image, "ao_tex")
        nodeutils.step_cursor()
    # groups
    if teeth:
        group = nodeutils.get_node_group("color_teeth_mixer")
        color_node = nodeutils.make_node_group_node(nodes, group, "Teeth Base Color", "color_teeth_mixer")
    else:
        group = nodeutils.get_node_group("color_tongue_mixer")
        color_node = nodeutils.make_node_group_node(nodes, group, "Tongue Base Color", "color_tongue_mixer")
    base_colour_node = group
    # values
    if teeth:
        nodeutils.set_node_input(color_node, "AO Strength", mat_cache.parameters.teeth_ao)
        nodeutils.set_node_input(color_node, "Front", mat_cache.parameters.teeth_front)
        nodeutils.set_node_input(color_node, "Rear", mat_cache.parameters.teeth_rear)
        nodeutils.set_node_input(color_node, "Gums Brightness", mat_cache.parameters.teeth_gums_brightness)
        nodeutils.set_node_input(color_node, "Teeth Brightness", mat_cache.parameters.teeth_teeth_brightness)
        nodeutils.set_node_input(color_node, "Gums Saturation", 1 - mat_cache.parameters.teeth_gums_desaturation)
        nodeutils.set_node_input(color_node, "Teeth Saturation", 1 - mat_cache.parameters.teeth_teeth_desaturation)
    else:
        nodeutils.set_node_input(color_node, "AO Strength", mat_cache.parameters.tongue_ao)
        nodeutils.set_node_input(color_node, "Front", mat_cache.parameters.tongue_front)
        nodeutils.set_node_input(color_node, "Rear", mat_cache.parameters.tongue_rear)
        nodeutils.set_node_input(color_node, "Brightness", mat_cache.parameters.tongue_brightness)
        nodeutils.set_node_input(color_node, "Saturation", 1 - mat_cache.parameters.tongue_desaturation)
    # links
    if teeth:
        gao_socket = "G"
        if "std_lower_teeth" in mat.name.lower():
            gao_socket = "R"
        nodeutils.link_nodes(links, mask_node, "Color", color_node, "Gums Mask")
        nodeutils.link_nodes(links, gradientrgb_node, gao_socket, color_node, "Gradient AO")
        nodeutils.link_nodes(links, diffuse_node, "Color", color_node, "Diffuse")
        nodeutils.link_nodes(links, ao_node, "Color", color_node, "AO")
        nodeutils.link_nodes(links, color_node, "Base Color", shader, "Base Color")
    else:
        gao_socket = "B"
        nodeutils.link_nodes(links, gradientrgb_node, gao_socket, color_node, "Gradient AO")
        nodeutils.link_nodes(links, diffuse_node, "Color", color_node, "Diffuse")
        nodeutils.link_nodes(links, ao_node, "Color", color_node, "AO")
        nodeutils.link_nodes(links, color_node, "Base Color", shader, "Base Color")

    # SSS
    nodeutils.drop_cursor(0.35)
    nodeutils.reset_cursor()
    # groups
    if teeth:
        group = nodeutils.get_node_group("subsurface_overlay_mixer")
        sss_node = nodeutils.make_node_group_node(nodes, group, "Teeth Subsurface", "subsurface_teeth_mixer")
    else:
        group = nodeutils.get_node_group("subsurface_mixer")
        sss_node = nodeutils.make_node_group_node(nodes, group, "Tongue Subsurface", "subsurface_tongue_mixer")
    # values
    if teeth:
        nodeutils.set_node_input(sss_node, "Scatter1", mat_cache.parameters.teeth_gums_sss_scatter)
        nodeutils.set_node_input(sss_node, "Radius1", mat_cache.parameters.teeth_sss_radius * vars.UNIT_SCALE * 3)
        nodeutils.set_node_input(sss_node, "Falloff1", mat_cache.parameters.teeth_sss_falloff)
        nodeutils.set_node_input(sss_node, "Scatter2", mat_cache.parameters.teeth_teeth_sss_scatter)
        nodeutils.set_node_input(sss_node, "Radius2", mat_cache.parameters.teeth_sss_radius * vars.UNIT_SCALE * 3)
        nodeutils.set_node_input(sss_node, "Falloff2", mat_cache.parameters.teeth_sss_falloff)
    else:
        nodeutils.set_node_input(sss_node, "Scatter", mat_cache.parameters.tongue_sss_scatter)
        nodeutils.set_node_input(sss_node, "Radius", mat_cache.parameters.tongue_sss_radius * vars.UNIT_SCALE * 3)
        nodeutils.set_node_input(sss_node, "Falloff", mat_cache.parameters.tongue_sss_falloff)
    # links
    nodeutils.link_nodes(links, mask_node, "Color", sss_node, "Mask")
    nodeutils.link_nodes(links, color_node, "Base Color", sss_node, "Diffuse")
    nodeutils.link_nodes(links, sss_node, "Subsurface", shader, "Subsurface")
    nodeutils.link_nodes(links, sss_node, "Subsurface Radius", shader, "Subsurface Radius")
    nodeutils.link_nodes(links, sss_node, "Subsurface Color", shader, "Subsurface Color")

    # MSR
    nodeutils.drop_cursor(0.1)
    nodeutils.reset_cursor()
    nodeutils.advance_cursor(-2.7)
    # props
    metallic = 0
    specprop, specular = get_specular_strength(mat_cache, shader)
    roughprop, roughness = get_roughness_remap(mat_cache)
    # maps
    metallic_image = find_material_image(mat, vars.METALLIC_MAP)
    roughness_image = find_material_image(mat, vars.ROUGHNESS_MAP)
    metallic_node = roughness_node = roughness_mult_node = None
    if metallic_image is not None:
        metallic_node = nodeutils.make_image_node(nodes, metallic_image, "metallic_tex")
        nodeutils.step_cursor()
    else:
        nodeutils.advance_cursor()
    if roughness_image is not None:
        roughness_node = nodeutils.make_image_node(nodes, roughness_image, "roughness_tex")
        nodeutils.advance_cursor()
        roughness_mult_node = nodeutils.make_math_node(nodes, "MULTIPLY", 1, roughness)
        if teeth:
            roughness_mult_node.name = utils.unique_name("teeth_roughness")
        else:
            roughness_mult_node.name = utils.unique_name("tongue_roughness")
        nodeutils.step_cursor(0.7)
    else:
        nodeutils.advance_cursor(1.7)
    # groups
    group = nodeutils.get_node_group("msr_overlay_mixer")
    if teeth:
        msr_node = nodeutils.make_node_group_node(nodes, group, "Teeth MSR", "msr_teeth_mixer")
    else:
        msr_node = nodeutils.make_node_group_node(nodes, group, "Tongue MSR", "msr_tongue_mixer")
    # values
    nodeutils.set_node_input(msr_node, "Metallic1", metallic)
    nodeutils.set_node_input(msr_node, "Metallic2", metallic)
    nodeutils.set_node_input(msr_node, "Roughness1", 1)
    nodeutils.set_node_input(msr_node, "Roughness2", roughness)
    nodeutils.set_node_input(msr_node, "Specular1", 0)
    nodeutils.set_node_input(msr_node, "Specular2", specular)
    # links
    nodeutils.link_nodes(links, gradientrgb_node, gao_socket, msr_node, "Mask")
    nodeutils.link_nodes(links, metallic_node, "Color", msr_node, "Metallic1")
    nodeutils.link_nodes(links, metallic_node, "Color", msr_node, "Metallic2")
    nodeutils.link_nodes(links, roughness_node, "Color", roughness_mult_node, 0)
    nodeutils.link_nodes(links, roughness_mult_node, "Value", msr_node, "Roughness2")
    nodeutils.link_nodes(links, gradientrgb_node, gao_socket, msr_node, "Mask")
    nodeutils.link_nodes(links, msr_node, "Metallic", shader, "Metallic")
    nodeutils.link_nodes(links, msr_node, "Specular", shader, "Specular")
    nodeutils.link_nodes(links, msr_node, "Roughness", shader, "Roughness")

    # emission and alpha
    nodeutils.set_node_input(shader, "Alpha", 1.0)
    connect_emission_alpha(obj, mat, shader)

    # Normal
    connect_normal(obj, mat, shader, base_colour_node)

    # Clearcoat
    #
    nodeutils.set_node_input(shader, "Clearcoat", 0)
    nodeutils.set_node_input(shader, "Clearcoat Roughness", 0)

    return


def connect_advanced_material(obj, mat, shader, mat_cache):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    props = bpy.context.scene.CC3ImportProps

    if mat_cache.is_hair() and prefs.new_hair_shader and mat_cache.smart_hair:
        base_colour_node = connect_hair_base_color(obj, mat, shader)
    else:
        base_colour_node = connect_base_color(obj, mat, shader)
    connect_subsurface(obj, mat, shader, base_colour_node)
    connect_msr(obj, mat, shader)
    connect_emission_alpha(obj, mat, shader)
    connect_normal(obj, mat, shader, base_colour_node)
    return


def connect_basic_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Base Color
    #
    nodeutils.reset_cursor()
    diffuse_image = find_material_image(mat, vars.BASE_COLOR_MAP)
    ao_image = find_material_image(mat, vars.MOD_AO_MAP)
    diffuse_node = ao_node = None
    if (diffuse_image is not None):
        diffuse_node = nodeutils.make_image_node(nodes, diffuse_image, "diffuse_tex")
        if ao_image is not None:
            prop, ao_strength = get_ao_strength(mat_cache)
            fac_node = nodeutils.make_value_node(nodes, "Ambient Occlusion Strength", prop, ao_strength)
            ao_node = nodeutils.make_image_node(nodes, ao_image, "ao_tex")
            nodeutils.advance_cursor(1.5)
            nodeutils.drop_cursor(0.75)
            mix_node = nodeutils.make_mixrgb_node(nodes, "MULTIPLY")
            nodeutils.link_nodes(links, diffuse_node, "Color", mix_node, "Color1")
            nodeutils.link_nodes(links, ao_node, "Color", mix_node, "Color2")
            nodeutils.link_nodes(links, fac_node, "Value", mix_node, "Fac")
            nodeutils.link_nodes(links, mix_node, "Color", shader, "Base Color")
        else:
            nodeutils.link_nodes(links, diffuse_node, "Color", shader, "Base Color")

    # Metallic
    #
    nodeutils.reset_cursor()
    metallic_image = find_material_image(mat, vars.METALLIC_MAP)
    metallic_node = None
    if metallic_image is not None:
        metallic_node = nodeutils.make_image_node(nodes, metallic_image, "metallic_tex")
        nodeutils.link_nodes(links, metallic_node, "Color", shader, "Metallic")

    # Specular
    #
    nodeutils.reset_cursor()
    specular_image = find_material_image(mat, vars.SPECULAR_MAP)
    mask_image = find_material_image(mat, vars.MOD_SPECMASK_MAP)
    prop_spec, spec = get_specular_strength(mat_cache, shader)
    specular_node = mask_node = mult_node = None
    if specular_image is not None:
        specular_node = nodeutils.make_image_node(nodes, specular_image, "specular_tex")
        nodeutils.link_nodes(links, specular_node, "Color", shader, "Specular")
    # always make a specular value node for skin or if there is a mask (but no map)
    elif prop_spec != "default_specular":
        specular_node = nodeutils.make_value_node(nodes, "Specular Strength", prop_spec, spec)
        nodeutils.link_nodes(links, specular_node, "Value", shader, "Specular")
    elif mask_image is not None:
        specular_node = nodeutils.make_value_node(nodes, "Specular Strength", "default_basic_specular", shader.inputs["Specular"].default_value)
        nodeutils.link_nodes(links, specular_node, "Value", shader, "Specular")
    if mask_image is not None:
        mask_node = nodeutils.make_image_node(nodes, mask_image, "specular_mask_tex")
        nodeutils.advance_cursor()
        mult_node = nodeutils.make_math_node(nodes, "MULTIPLY")
        if specular_node.type == "VALUE":
            nodeutils.link_nodes(links, specular_node, "Value", mult_node, 0)
        else:
            nodeutils.link_nodes(links, specular_node, "Color", mult_node, 0)
        nodeutils.link_nodes(links, mask_node, "Color", mult_node, 1)
        nodeutils.link_nodes(links, mult_node, "Value", shader, "Specular")

    # Roughness
    #
    nodeutils.reset_cursor()
    roughness_image = find_material_image(mat, vars.ROUGHNESS_MAP)
    roughness_node = None
    if roughness_image is not None:
        roughness_node = nodeutils.make_image_node(nodes, roughness_image, "roughness_tex")
        rprop_name, rprop_val = get_roughness_remap(mat_cache)
        if mat_cache.material_type.startswith("SKIN"):
            nodeutils.advance_cursor()
            remap_node = nodeutils.make_shader_node(nodes, "ShaderNodeMapRange")
            remap_node.name = utils.unique_name(rprop_name)
            nodeutils.set_node_input(remap_node, "To Min", rprop_val)
            nodeutils.make_shader_node(links, roughness_node, "Color", remap_node, "Value")
            nodeutils.link_nodes(links, remap_node, "Result", shader, "Roughness")
        elif mat_cache.material_type.startswith("TEETH") or mat_cache.material_type == "TONGUE":
            nodeutils.advance_cursor()
            rmult_node = nodeutils.make_math_node(nodes, "MULTIPLY", 1, rprop_val)
            rmult_node.name = utils.unique_name(rprop_name)
            nodeutils.link_nodes(links, roughness_node, "Color", rmult_node, 0)
            nodeutils.link_nodes(links, rmult_node, "Value", shader, "Roughness")
        else:
            nodeutils.link_nodes(links, roughness_node, "Color", shader, "Roughness")

    # Emission
    #
    nodeutils.reset_cursor()
    emission_image = find_material_image(mat, vars.EMISSION_MAP)
    emission_node = None
    if emission_image is not None:
        emission_node = nodeutils.make_image_node(nodes, emission_image, "emission_tex")
        nodeutils.link_nodes(links, emission_node, "Color", shader, "Emission")

    # Alpha
    #
    nodeutils.reset_cursor()
    alpha_image = find_material_image(mat, vars.ALPHA_MAP)
    alpha_node = None
    if alpha_image is not None:
        alpha_node = nodeutils.make_image_node(nodes, alpha_image, "opacity_tex")
        dir,file = os.path.split(alpha_image.filepath)
        if "_diffuse." in file.lower() or "_albedo." in file.lower():
            nodeutils.link_nodes(links, alpha_node, "Alpha", shader, "Alpha")
        else:
            nodeutils.link_nodes(links, alpha_node, "Color", shader, "Alpha")
    # material alpha blend settings
    if obj_cache.is_hair() or mat_cache.is_eyelash():
        set_material_alpha(mat, "HASHED")
    elif shader.inputs["Alpha"].default_value < 1.0:
        set_material_alpha(mat, props.blend_mode)
    else:
        set_material_alpha(mat, "OPAQUE")

    # Normal
    #
    nodeutils.reset_cursor()
    normal_image = find_material_image(mat, vars.NORMAL_MAP)
    bump_image = find_material_image(mat, vars.BUMP_MAP)
    normal_node = bump_node = normalmap_node = bumpmap_node = None
    if normal_image is not None:
        normal_node = nodeutils.make_image_node(nodes, normal_image, "normal_tex")
        nodeutils.advance_cursor()
        normalmap_node = nodeutils.make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        nodeutils.link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        nodeutils.link_nodes(links, normalmap_node, "Normal", shader, "Normal")
    if bump_image is not None:
        prop_bump, bump_strength = get_bump_strength(mat_cache)
        bump_strength_node = nodeutils.make_value_node(nodes, "Bump Strength", prop_bump, bump_strength / 1000)
        bump_node = nodeutils.make_image_node(nodes, bump_image, "bump_tex")
        nodeutils.advance_cursor()
        bumpmap_node = nodeutils.make_shader_node(nodes, "ShaderNodeBump", 0.7)
        nodeutils.advance_cursor()
        nodeutils.link_nodes(links, bump_strength_node, "Value", bumpmap_node, "Distance")
        nodeutils.link_nodes(links, bump_node, "Color", bumpmap_node, "Height")
        if normal_image is not None:
            nodeutils.link_nodes(links, normalmap_node, "Normal", bumpmap_node, "Normal")
        nodeutils.link_nodes(links, bumpmap_node, "Normal", shader, "Normal")

    return

# the 'Compatible' material is the bare minimum required to export the corrent textures with the FBX
# it will connect just the diffuse, metallic, specular, roughness, opacity and normal/bump
def connect_compat_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Base Color
    #
    nodeutils.reset_cursor()
    diffuse_image = find_material_image(mat, vars.BASE_COLOR_MAP)
    if (diffuse_image is not None):
        diffuse_node = nodeutils.make_image_node(nodes, diffuse_image, "diffuse_tex")
        nodeutils.link_nodes(links, diffuse_node, "Color", shader, "Base Color")

    # Metallic
    #
    nodeutils.reset_cursor()
    metallic_image = find_material_image(mat, vars.METALLIC_MAP)
    metallic_node = None
    if metallic_image is not None:
        metallic_node = nodeutils.make_image_node(nodes, metallic_image, "metallic_tex")
        nodeutils.link_nodes(links, metallic_node, "Color", shader, "Metallic")

    # Specular
    #
    nodeutils.reset_cursor()
    specular_image = find_material_image(mat, vars.SPECULAR_MAP)
    if specular_image is not None:
        specular_node = nodeutils.make_image_node(nodes, specular_image, "specular_tex")
        nodeutils.link_nodes(links, specular_node, "Color", shader, "Specular")
    if mat_cache.is_skin():
        nodeutils.set_node_input(shader, "Specular", 0.2)
    if mat_cache.is_cornea():
        nodeutils.set_node_input(shader, "Specular", 0.8)

    # Roughness
    #
    nodeutils.reset_cursor()
    roughness_image = find_material_image(mat, vars.ROUGHNESS_MAP)
    if roughness_image is not None:
        roughness_node = nodeutils.make_image_node(nodes, roughness_image, "roughness_tex")
        nodeutils.link_nodes(links, roughness_node, "Color", shader, "Roughness")
    if mat_cache.is_cornea():
        nodeutils.set_node_input(shader, "Roughness", 0)

    # Emission
    #
    nodeutils.reset_cursor()
    emission_image = find_material_image(mat, vars.EMISSION_MAP)
    emission_node = None
    if emission_image is not None:
        emission_node = nodeutils.make_image_node(nodes, emission_image, "emission_tex")
        nodeutils.link_nodes(links, emission_node, "Color", shader, "Emission")

    # Alpha
    #
    nodeutils.reset_cursor()
    alpha_image = find_material_image(mat, vars.ALPHA_MAP)
    alpha_node = None
    if alpha_image is not None:
        alpha_node = nodeutils.make_image_node(nodes, alpha_image, "opacity_tex")
        file = os.path.split(alpha_image.filepath)[1]
        if "_diffuse." in file.lower() or "_albedo." in file.lower():
            nodeutils.link_nodes(links, alpha_node, "Alpha", shader, "Alpha")
        else:
            nodeutils.link_nodes(links, alpha_node, "Color", shader, "Alpha")
    # material alpha blend settings
    if obj_cache.is_hair() or mat_cache.is_eyelash():
        set_material_alpha(mat, "HASHED")
    elif mat_cache.is_eye_occlusion() or mat_cache.is_tearline():
        set_material_alpha(mat, props.blend_mode)
    elif shader.inputs["Alpha"].default_value < 1.0:
        set_material_alpha(mat, props.blend_mode)
    else:
        set_material_alpha(mat, "OPAQUE")

    # Normal
    #
    nodeutils.reset_cursor()
    normal_image = find_material_image(mat, vars.NORMAL_MAP)
    bump_image = find_material_image(mat, vars.BUMP_MAP)
    normal_node = bump_node = normalmap_node = bumpmap_node = None
    if normal_image is not None:
        normal_node = nodeutils.make_image_node(nodes, normal_image, "normal_tex")
        nodeutils.advance_cursor()
        normalmap_node = nodeutils.make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        nodeutils.link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        nodeutils.link_nodes(links, normalmap_node, "Normal", shader, "Normal")
    elif bump_image is not None:
        bump_node = nodeutils.make_image_node(nodes, bump_image, "bump_tex")
        nodeutils.advance_cursor()
        normalmap_node = nodeutils.make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        nodeutils.link_nodes(links, bump_node, "Color", normalmap_node, "Color")
        nodeutils.link_nodes(links, normalmap_node, "Normal", shader, "Normal")

    return

def connect_base_color(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    diffuse_image = find_material_image(mat, vars.BASE_COLOR_MAP)
    blend_image = find_material_image(mat, vars.MOD_BASECOLORBLEND_MAP)
    ao_image = find_material_image(mat, vars.MOD_AO_MAP)
    mcmao_image = find_material_image(mat, vars.MOD_MCMAO_MAP)
    prop_blend, blend_value = get_blend_strength(mat_cache)
    prop_ao, ao_value = get_ao_strength(mat_cache)
    prop_group = get_material_group(mat_cache)

    count = utils.count_maps(diffuse_image, ao_image, blend_image, mcmao_image)
    if count == 0:
        return None

    nodeutils.reset_cursor()
    # space
    nodeutils.advance_cursor(-count)
    # maps
    ao_node = blend_node = diffuse_node = mcmao_node = None
    if mcmao_image is not None:
        mcmao_node = nodeutils.make_image_node(nodes, mcmao_image, "mcmao_tex")
        nodeutils.step_cursor()
    if ao_image is not None:
        ao_node = nodeutils.make_image_node(nodes, ao_image, "ao_tex")
        nodeutils.step_cursor()
    if blend_image is not None:
        blend_node = nodeutils.make_image_node(nodes, blend_image, "blend_tex")
        nodeutils.step_cursor()
    if diffuse_image is not None:
        diffuse_node = nodeutils.make_image_node(nodes, diffuse_image, "diffuse_tex")
        nodeutils.step_cursor()
    # groups
    if mcmao_image is not None:
        group = nodeutils.get_node_group("color_head_mixer")
        group_node = nodeutils.make_node_group_node(nodes, group, "Base Color Head Mixer", "color_" + prop_group + "_mixer")
        nodeutils.drop_cursor(0.3)
    elif blend_image is not None:
        group = nodeutils.get_node_group("color_blend_ao_mixer")
        group_node = nodeutils.make_node_group_node(nodes, group, "Base Color Mixer", "color_" + prop_group + "_mixer")
    else:
        group = nodeutils.get_node_group("color_ao_mixer")
        group_node = nodeutils.make_node_group_node(nodes, group, "Base Color Mixer", "color_" + prop_group + "_mixer")
    # values
    if diffuse_image is None:
        nodeutils.set_node_input(group_node, "Diffuse", shader.inputs["Base Color"].default_value)
    if blend_image is not None:
        nodeutils.set_node_input(group_node, "Blend Strength", blend_value)
    if mcmao_image is not None:
        nodeutils.set_node_input(group_node, "Mouth AO", mat_cache.parameters.skin_mouth_ao)
        nodeutils.set_node_input(group_node, "Nostril AO", mat_cache.parameters.skin_nostril_ao)
        nodeutils.set_node_input(group_node, "Lips AO", mat_cache.parameters.skin_lips_ao)
    nodeutils.set_node_input(group_node, "AO Strength", ao_value)
    # links
    if mcmao_image is not None:
        nodeutils.link_nodes(links, mcmao_node, "Color", group_node, "MCMAO")
        nodeutils.link_nodes(links, mcmao_node, "Alpha", group_node, "LLAO")
    if diffuse_image is not None:
        nodeutils.link_nodes(links, diffuse_node, "Color", group_node, "Diffuse")
    if blend_image is not None:
        nodeutils.link_nodes(links, blend_node, "Color", group_node, "Blend")
    if ao_image is not None:
        nodeutils.link_nodes(links, ao_node, "Color", group_node, "AO")
    nodeutils.link_nodes(links, group_node, "Base Color", shader, "Base Color")

    return group_node


def connect_hair_base_color(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    diffuse_image = find_material_image(mat, vars.BASE_COLOR_MAP)
    ao_image = find_material_image(mat, vars.MOD_AO_MAP)
    root_image = find_material_image(mat, vars.MOD_HAIR_ROOT_MAP)
    id_image = find_material_image(mat, vars.MOD_HAIR_ID_MAP)
    vcol_image = find_material_image(mat, vars.MOD_HAIR_VERTEX_COLOR_MAP)
    flow_image = find_material_image(mat, vars.MOD_HAIR_FLOW_MAP)
    depth_image = find_material_image(mat, vars.MOD_HAIR_BLEND_MULTIPLY)

    count = utils.count_maps(diffuse_image, ao_image, root_image, id_image, vcol_image, flow_image, depth_image)
    if count == 0:
        return None

    nodeutils.reset_cursor()
    # space
    nodeutils.advance_cursor(-count)
    # maps
    ao_node = diffuse_node = depth_node = flow_node = vcol_node = id_node = root_node = None
    if depth_image is not None:
        depth_node = nodeutils.make_image_node(nodes, depth_image, "depth_tex")
        nodeutils.step_cursor()
    if flow_image is not None:
        flow_node = nodeutils.make_image_node(nodes, flow_image, "flow_tex")
        nodeutils.step_cursor()
    if vcol_image is not None:
        vcol_node = nodeutils.make_image_node(nodes, vcol_image, "vcol_tex")
        nodeutils.step_cursor()
    if id_image is not None:
        id_node = nodeutils.make_image_node(nodes, id_image, "id_tex")
        nodeutils.step_cursor()
    if root_image is not None:
        root_node = nodeutils.make_image_node(nodes, root_image, "root_tex")
        nodeutils.step_cursor()
    if ao_image is not None:
        ao_node = nodeutils.make_image_node(nodes, ao_image, "ao_tex")
        nodeutils.step_cursor()
    if diffuse_image is not None:
        diffuse_node = nodeutils.make_image_node(nodes, diffuse_image, "diffuse_tex")
        nodeutils.step_cursor()
    # groups
    group = nodeutils.get_node_group("color_hair_mixer")
    group_node = nodeutils.make_node_group_node(nodes, group, "Base Color Head Mixer", "color_hair_mixer")
    nodeutils.drop_cursor(2.3)
    # values
    if diffuse_image is None:
        nodeutils.set_node_input(group_node, "Diffuse", shader.inputs["Base Color"].default_value)
    nodeutils.set_node_input(group_node, "Diffuse Bright", mat_cache.parameters.hair_brightness)
    nodeutils.set_node_input(group_node, "Diffuse Contrast", mat_cache.parameters.hair_contrast)
    nodeutils.set_node_input(group_node, "Diffuse Hue", mat_cache.parameters.hair_hue)
    nodeutils.set_node_input(group_node, "Diffuse Saturation", mat_cache.parameters.hair_saturation)
    nodeutils.set_node_input(group_node, "Aniso Strength", mat_cache.parameters.hair_aniso_strength)
    nodeutils.set_node_input(group_node, "Aniso Strength Cycles", mat_cache.parameters.hair_aniso_strength_cycles)
    nodeutils.set_node_input(group_node, "Aniso Color", mat_cache.parameters.hair_aniso_color)
    nodeutils.set_node_input(group_node, "Base Color Strength", mat_cache.parameters.hair_vertex_color_strength)
    nodeutils.set_node_input(group_node, "Base Color Map Strength", mat_cache.parameters.hair_base_color_map_strength)
    nodeutils.set_node_input(group_node, "AO Strength", mat_cache.parameters.hair_ao)
    nodeutils.set_node_input(group_node, "Depth Blend Strength", mat_cache.parameters.hair_depth_strength)
    nodeutils.set_node_input(group_node, "Diffuse Strength", mat_cache.parameters.hair_diffuse_strength)
    nodeutils.set_node_input(group_node, "Global Strength", mat_cache.parameters.hair_global_strength)
    nodeutils.set_node_input(group_node, "Root Color", gamma_correct(mat_cache.parameters.hair_root_color))
    nodeutils.set_node_input(group_node, "End Color", gamma_correct(mat_cache.parameters.hair_end_color))
    nodeutils.set_node_input(group_node, "Root Color Strength", mat_cache.parameters.hair_root_strength)
    nodeutils.set_node_input(group_node, "End Color Strength", mat_cache.parameters.hair_end_strength)
    nodeutils.set_node_input(group_node, "Invert Root and End Color", mat_cache.parameters.hair_invert_strand)
    nodeutils.set_node_input(group_node, "Highlight A Start", mat_cache.parameters.hair_a_start)
    nodeutils.set_node_input(group_node, "Highlight A Mid", mat_cache.parameters.hair_a_mid)
    nodeutils.set_node_input(group_node, "Highlight A End", mat_cache.parameters.hair_a_end)
    nodeutils.set_node_input(group_node, "Highlight A Strength", mat_cache.parameters.hair_a_strength)
    nodeutils.set_node_input(group_node, "Highlight A Overlap End", mat_cache.parameters.hair_a_overlap)
    nodeutils.set_node_input(group_node, "Highlight Color A", gamma_correct(mat_cache.parameters.hair_a_color))
    nodeutils.set_node_input(group_node, "Highlight B Start", mat_cache.parameters.hair_b_start)
    nodeutils.set_node_input(group_node, "Highlight B Mid", mat_cache.parameters.hair_b_mid)
    nodeutils.set_node_input(group_node, "Highlight B End", mat_cache.parameters.hair_b_end)
    nodeutils.set_node_input(group_node, "Highlight B Strength", mat_cache.parameters.hair_b_strength)
    nodeutils.set_node_input(group_node, "Highlight B Overlap End", mat_cache.parameters.hair_b_overlap)
    nodeutils.set_node_input(group_node, "Highlight Color B", gamma_correct(mat_cache.parameters.hair_b_color))
    # links
    if flow_image is not None:
        nodeutils.link_nodes(links, flow_node, "Color", group_node, "Flow Map")
    if root_image is not None:
        nodeutils.link_nodes(links, root_node, "Color", group_node, "Root Map")
    if id_image is not None:
        nodeutils.link_nodes(links, id_node, "Color", group_node, "ID Map")
    if depth_image is not None:
        nodeutils.link_nodes(links, depth_node, "Color", group_node, "Depth Map")
    if vcol_image is not None:
        nodeutils.link_nodes(links, vcol_node, "Color", group_node, "Vertex Color Base")
    if diffuse_image is not None:
        nodeutils.link_nodes(links, diffuse_node, "Color", group_node, "Diffuse Map")
    if ao_image is not None:
        nodeutils.link_nodes(links, ao_node, "Color", group_node, "AO Map")

    nodeutils.link_nodes(links, group_node, "Base Color", shader, "Base Color")

    nodeutils.link_nodes(links, group_node, "Base Color", shader, "Base Color")
    nodeutils.link_nodes(links, group_node, "Aniso Angle Cycles", shader, "Anisotropic Rotation")
    nodeutils.link_nodes(links, group_node, "Aniso Strength", shader, "Anisotropic")

    return group_node


def connect_subsurface(obj, mat, shader, diffuse_node):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    sss_image = find_material_image(mat, vars.SUBSURFACE_MAP)
    trans_image = find_material_image(mat, vars.MOD_TRANSMISSION_MAP)
    prop_radius, sss_radius = get_sss_radius(mat_cache)
    prop_falloff, sss_falloff = get_sss_falloff(mat_cache)
    prop_group = get_material_group(mat_cache)

    count = utils.count_maps(trans_image, sss_image)
    if count == 0 and not mat_cache.is_hair() and not mat_cache.is_skin():
        return None

    nodeutils.reset_cursor()
    # space
    nodeutils.advance_cursor(-count)
    # maps
    sss_node = trans_node = None
    if trans_image is not None:
        trans_node = nodeutils.make_image_node(nodes, trans_image, "transmission_tex")
        nodeutils.step_cursor()
    if sss_image is not None:
        sss_node = nodeutils.make_image_node(nodes, sss_image, "sss_tex")
        nodeutils.step_cursor()
    # group
    group = nodeutils.get_node_group("subsurface_mixer")
    group_node = nodeutils.make_node_group_node(nodes, group, "Subsurface Mixer", "subsurface_" + prop_group + "_mixer")
    # values
    nodeutils.set_node_input(group_node, "Radius", sss_radius * vars.UNIT_SCALE)
    nodeutils.set_node_input(group_node, "Falloff", sss_falloff)
    if diffuse_node is None:
        nodeutils.set_node_input(group_node, "Diffuse", shader.inputs["Base Color"].default_value)
    # links
    else:
        nodeutils.link_nodes(links, diffuse_node, "Base Color", group_node, "Diffuse")
        nodeutils.link_nodes(links, diffuse_node, "Color", group_node, "Diffuse")
    nodeutils.link_nodes(links, sss_node, "Color", group_node, "Scatter")
    nodeutils.link_nodes(links, trans_node, "Color", group_node, "Transmission")
    nodeutils.link_nodes(links, group_node, "Subsurface", shader, "Subsurface")
    nodeutils.link_nodes(links, group_node, "Subsurface Radius", shader, "Subsurface Radius")
    nodeutils.link_nodes(links, group_node, "Subsurface Color", shader, "Subsurface Color")

    # subsurface translucency
    if mat_cache.is_skin() or mat_cache.is_hair():
        mat.use_sss_translucency = True
    else:
        mat.use_sss_translucency = False

    return group_node


def connect_msr(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    metallic_image = find_material_image(mat, vars.METALLIC_MAP)
    specular_image = find_material_image(mat, vars.SPECULAR_MAP)
    mask_image = find_material_image(mat, vars.MOD_SPECMASK_MAP)
    roughness_image = find_material_image(mat, vars.ROUGHNESS_MAP)
    prop_spec, specular_strength = get_specular_strength(mat_cache, shader)
    prop_roughness, roughness_remap = get_roughness_remap(mat_cache)
    prop_roughness_power, roughness_power = get_roughness_power(mat_cache)
    prop_group = get_material_group(mat_cache)

    count = utils.count_maps(mask_image, specular_image, roughness_image, metallic_image)
    if count == 0:
        return None

    nodeutils.reset_cursor()
    # space
    nodeutils.advance_cursor(-count)
    # maps
    metallic_node = specular_node = roughness_node = mask_node = None
    if roughness_image is not None:
        roughness_node = nodeutils.make_image_node(nodes, roughness_image, "roughness_tex")
        nodeutils.step_cursor()
    if mask_image is not None:
        mask_node = nodeutils.make_image_node(nodes, mask_image, "specular_mask_tex")
        nodeutils.step_cursor()
    if specular_image is not None:
        specular_node = nodeutils.make_image_node(nodes, specular_image, "specular_tex")
        nodeutils.step_cursor()
    if metallic_image is not None:
        metallic_node = nodeutils.make_image_node(nodes, metallic_image, "metallic_tex")
        nodeutils.step_cursor()
    # groups
    if mat_cache.is_skin():
        group = nodeutils.get_node_group("msr_skin_mixer")
    else:
        group = nodeutils.get_node_group("msr_mixer")
    group_node = nodeutils.make_node_group_node(nodes, group, "Metallic, Specular & Roughness Mixer", "msr_" + prop_group + "_mixer")
    # values
    nodeutils.set_node_input(group_node, "Specular", specular_strength)
    nodeutils.set_node_input(group_node, "Roughness Remap", roughness_remap)
    nodeutils.set_node_input(group_node, "Roughness Power", roughness_power)
    # links
    nodeutils.link_nodes(links, metallic_node, "Color", group_node, "Metallic")
    nodeutils.link_nodes(links, specular_node, "Color", group_node, "Specular")
    nodeutils.link_nodes(links, mask_node, "Color", group_node, "Specular Mask")
    nodeutils.link_nodes(links, roughness_node, "Color", group_node, "Roughness")
    nodeutils.link_nodes(links, group_node, "Metallic", shader, "Metallic")
    nodeutils.link_nodes(links, group_node, "Specular", shader, "Specular")
    nodeutils.link_nodes(links, group_node, "Roughness", shader, "Roughness")

    return group_node


def connect_emission_alpha(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    emission_image = find_material_image(mat, vars.EMISSION_MAP)
    alpha_image = find_material_image(mat, vars.ALPHA_MAP)
    prop_alpha, alpha_strength = get_alpha_strength(mat_cache)

    emission_node = alpha_node = None
    # emission
    nodeutils.reset_cursor()
    if emission_image is not None:
        emission_node = nodeutils.make_image_node(nodes, emission_image, "emission_tex")
        nodeutils.link_nodes(links, emission_node, "Color", shader, "Emission")
    # alpha
    nodeutils.reset_cursor()
    if alpha_image is not None:
        has_opacity_control = False
        if mat_cache.is_hair() or mat_cache.is_scalp() or mat_cache.is_eyelash():
            has_opacity_control = True
            nodeutils.advance_cursor(-0.6)
        alpha_node = nodeutils.make_image_node(nodes, alpha_image, "opacity_tex")
        dir,file = os.path.split(alpha_image.filepath)
        if "_diffuse." in file.lower() or "_albedo." in file.lower():
            alpha_socket = "Alpha"
        else:
            alpha_socket = "Color"
        if has_opacity_control:
            nodeutils.advance_cursor()
            mm_node = nodeutils.make_math_node(nodes, "MULTIPLY", 1, alpha_strength)
            mm_node.name = utils.unique_name(prop_alpha)
            nodeutils.link_nodes(links, alpha_node, alpha_socket, mm_node, 0)
            nodeutils.link_nodes(links, mm_node, "Value", shader, "Alpha")
        else:
            nodeutils.link_nodes(links, alpha_node, alpha_socket, shader, "Alpha")
    # material settings
    if mat_cache.is_hair() or mat_cache.is_scalp() or mat_cache.is_eyelash():
        set_material_alpha(mat, "HASHED")
    elif shader.inputs["Alpha"].default_value < 1.0:
        set_material_alpha(mat, props.blend_mode)
    else:
        set_material_alpha(mat, "OPAQUE")


def connect_normal(obj, mat, shader, base_color_node):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    normal_node = bump_node = blend_node = micro_node = mask_node = tiling_node = None
    normal_image = find_material_image(mat, vars.NORMAL_MAP)
    bump_image = find_material_image(mat, vars.BUMP_MAP)
    blend_image = find_material_image(mat, vars.MOD_NORMALBLEND_MAP)
    micro_image = find_material_image(mat, vars.MOD_MICRONORMAL_MAP)
    mask_image = find_material_image(mat, vars.MOD_MICRONORMALMASK_MAP)
    prop_bump, bump_strength = get_bump_strength(mat_cache)
    prop_blend, blend_strength = get_normal_blend_strength(mat_cache)
    prop_micronormal, micronormal_strength = get_micronormal_strength(mat_cache)
    prop_tiling, micronormal_tiling = get_micronormal_tiling(mat_cache)
    prop_group = get_material_group(mat_cache)

    count = utils.count_maps(bump_image, mask_image, micro_image, blend_image, normal_image)
    if count == 0 and not (mat_cache.is_hair() and prefs.fake_hair_bump == True):
        return None

    nodeutils.reset_cursor()
    # space
    nodeutils.advance_cursor(-count)
    # maps
    if bump_image is not None:
        bump_node = nodeutils.make_image_node(nodes, bump_image, "bump_tex")
        nodeutils.step_cursor()
    if mask_image is not None:
        mask_node = nodeutils.make_image_node(nodes, mask_image, "micro_normal_mask_tex")
        nodeutils.step_cursor()
    if micro_image is not None:
        nodeutils.advance_cursor(-1)
        nodeutils.drop_cursor(0.75)
        group = nodeutils.get_node_group("tiling_mapping")
        tiling_node = nodeutils.make_node_group_node(nodes, group, "Micro Normal Tiling", "tiling_" + prop_group + "_mapping")
        nodeutils.advance_cursor()
        micro_node = nodeutils.make_image_node(nodes, micro_image, "micro_normal_tex")
        nodeutils.step_cursor()
    if blend_image is not None:
        blend_node = nodeutils.make_image_node(nodes, blend_image, "normal_blend_tex")
        nodeutils.step_cursor()
    if normal_image is not None:
        normal_node = nodeutils.make_image_node(nodes, normal_image, "normal_tex")
        nodeutils.step_cursor()
    # groups
    if (mat_cache.is_hair() and bump_image is None
        and normal_image is None and prefs.fake_hair_bump == True):
        # fake the normal with a b&w diffuse...
        group = nodeutils.get_node_group("fake_bump_mixer")
    elif bump_image is not None:
        group = nodeutils.get_node_group("bump_mixer")
    elif normal_image is not None and bump_image is None and mask_image is None and \
            micro_image is None and blend_image is None:
        normalmap_node = nodeutils.make_shader_node(nodes, "ShaderNodeNormalMap")
        nodeutils.link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        nodeutils.link_nodes(links, normalmap_node, "Normal", shader, "Normal")
        return normalmap_node
    elif blend_image is not None:
        group = nodeutils.get_node_group("normal_micro_mask_blend_mixer")
    else:
        group =  nodeutils.get_node_group("normal_micro_mask_mixer")
    group_node = nodeutils.make_node_group_node(nodes, group, "Normal Mixer", "normal_" + prop_group + "_mixer")
    nodeutils.set_node_input(group, "Bump Map Midpoint", mat_cache.parameters.hair_fake_bump_midpoint)
    # values
    nodeutils.set_node_input(group_node, "Normal Blend Strength", blend_strength)
    nodeutils.set_node_input(group_node, "Micro Normal Strength", micronormal_strength)
    nodeutils.set_node_input(group_node, "Bump Map Height", bump_strength / 1000)
    nodeutils.set_node_input(tiling_node, "Tiling", micronormal_tiling)
    # links
    nodeutils.link_nodes(links, group_node, "Normal", shader, "Normal")
    nodeutils.link_nodes(links, normal_node, "Color", group_node, "Normal")
    nodeutils.link_nodes(links, bump_node, "Color", group_node, "Bump Map")
    nodeutils.link_nodes(links, blend_node, "Color", group_node, "Normal Blend")
    nodeutils.link_nodes(links, micro_node, "Color", group_node, "Micro Normal")
    nodeutils.link_nodes(links, tiling_node, "Vector", micro_node, "Vector")
    nodeutils.link_nodes(links, mask_node, "Color", group_node, "Micro Normal Mask")
    nodeutils.link_nodes(links, base_color_node, "Color", group_node, "Fake Map")
    nodeutils.link_nodes(links, base_color_node, "Diffuse", group_node, "Fake Map")
    return group_node


def apply_cloth_settings(obj, cloth_type):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    mod = modutils.get_cloth_physics_mod(obj)
    if mod is None:
        return
    cache = get_object_cache(obj)
    cache.cloth_settings = cloth_type

    utils.log_info("Setting " + obj.name + " cloth settings to: " + cloth_type)
    mod.settings.vertex_group_mass = prefs.physics_group + "_Pin"
    mod.settings.time_scale = 1
    if cloth_type == "HAIR":
        mod.settings.quality = 4
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.15
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 5
        mod.settings.compression_stiffness = 5
        mod.settings.shear_stiffness = 5
        mod.settings.bending_stiffness = 5
        # dampening
        mod.settings.tension_damping = 0
        mod.settings.compression_damping = 0
        mod.settings.shear_damping = 0
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 2
    elif cloth_type == "SILK":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.25
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 5
        mod.settings.compression_stiffness = 5
        mod.settings.shear_stiffness = 5
        mod.settings.bending_stiffness = 10
        # dampening
        mod.settings.tension_damping = 0
        mod.settings.compression_damping = 0
        mod.settings.shear_damping = 0
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    elif cloth_type == "DENIM":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 1
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 40
        mod.settings.compression_stiffness = 40
        mod.settings.shear_stiffness = 40
        mod.settings.bending_stiffness = 60
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 10
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    elif cloth_type == "LEATHER":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.4
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 80
        mod.settings.compression_stiffness = 80
        mod.settings.shear_stiffness = 80
        mod.settings.bending_stiffness = 80
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 10
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    elif cloth_type == "RUBBER":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 3
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 15
        mod.settings.compression_stiffness = 15
        mod.settings.shear_stiffness = 15
        mod.settings.bending_stiffness = 40
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    else: #cotton
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.3
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 20
        mod.settings.compression_stiffness = 20
        mod.settings.shear_stiffness = 20
        mod.settings.bending_stiffness = 20
        # dampening
        mod.settings.tension_damping = 5
        mod.settings.compression_damping = 5
        mod.settings.shear_damping = 5
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4


def add_collision_physics(obj):
    """Adds a Collision modifier to the object, depending on the object cache settings.

    Does not overwrite or re-create any existing Collision modifier.
    """

    cache = get_object_cache(obj)
    if (cache.collision_physics == "ON"
        or (cache.collision_physics == "DEFAULT"
            and "Base_Body" in obj.name)):

        if modutils.get_collision_physics_mod(obj) is None:
            collision_mod = obj.modifiers.new(utils.unique_name("Collision"), type="COLLISION")
            collision_mod.settings.thickness_outer = 0.005
            utils.log_info("Collision Modifier: " + collision_mod.name + " applied to " + obj.name)
    elif cache.collision_physics == "OFF":
        utils.log_info("Collision Physics disabled for: " + obj.name)


def remove_collision_physics(obj):
    """Removes the Collision modifier from the object.
    """

    for mod in obj.modifiers:
        if mod.type == "COLLISION":
            utils.log_info("Removing Collision modifer: " + mod.name + " from: " + obj.name)
            obj.modifiers.remove(mod)


def add_cloth_physics(obj):
    """Adds a Cloth modifier to the object depending on the object cache settings.

    Does not overwrite or re-create any existing Cloth modifier.
    Sets the cache bake range to the same as any action on the character's armature.
    Applies cloth settings based on the object cache settings.
    Repopulates the existing weight maps, depending on their cache settings.
    """

    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    props = bpy.context.scene.CC3ImportProps

    obj_cache = get_object_cache(obj)

    if obj_cache.cloth_physics == "ON" and modutils.get_cloth_physics_mod(obj) is None:

        # Create the Cloth modifier
        cloth_mod = obj.modifiers.new(utils.unique_name("Cloth"), type="CLOTH")
        utils.log_info("Cloth Modifier: " + cloth_mod.name + " applied to " + obj.name)

        # Create the physics pin vertex group if it doesn't exist
        pin_group = prefs.physics_group + "_Pin"
        if pin_group not in obj.vertex_groups:
            obj.vertex_groups.new(name = pin_group)

        # Set cache bake frame range
        frame_count = 250
        if obj.parent is not None and obj.parent.animation_data is not None and \
                obj.parent.animation_data.action is not None:
            frame_start = math.floor(obj.parent.animation_data.action.frame_range[0])
            frame_count = math.ceil(obj.parent.animation_data.action.frame_range[1])
        utils.log_info("Setting " + obj.name + " bake cache frame range to [1-" + str(frame_count) + "]")
        cloth_mod.point_cache.frame_start = frame_start
        cloth_mod.point_cache.frame_end = frame_count

        # Apply cloth settings
        if obj_cache.cloth_settings != "DEFAULT":
            apply_cloth_settings(obj, obj_cache.cloth_settings)
        elif obj_cache.object_type == "HAIR":
            apply_cloth_settings(obj, "HAIR")
        else:
            apply_cloth_settings(obj, "COTTON")

        # Add any existing weight maps
        for mat in obj.data.materials:
            add_material_weight_map(obj, mat, create = False)

        # fix mod order
        modutils.move_mod_last(obj, cloth_mod)

    elif obj_cache.cloth_physics == "OFF":
        utils.log_info("Cloth Physics disabled for: " + obj.name)


def remove_cloth_physics(obj):
    """Removes the Cloth modifier from the object.

    Also removes any active weight maps and also removes the weight map vertex group.
    """

    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    # Remove the Cloth modifier
    for mod in obj.modifiers:
        if mod.type == "CLOTH":
            utils.log_info("Removing Cloth modifer: " + mod.name + " from: " + obj.name)
            obj.modifiers.remove(mod)

    # Remove any weight maps
    for mat in obj.data.materials:
        if mat is not None:
            remove_material_weight_maps(obj, mat)
            weight_group = prefs.physics_group + "_" + strip_name(mat.name)
            if weight_group in obj.vertex_groups:
                obj.vertex_groups.remove(obj.vertex_groups[weight_group])

    # If there are no weight maps left on the object, remove the vertex group
    mods = 0
    for mod in obj.modifiers:
        if mod.type == "VERTEX_WEIGHT_EDIT" and vars.NODE_PREFIX in mod.name:
            mods += 1

    pin_group = prefs.physics_group + "_Pin"
    if mods == 0 and pin_group in obj.vertex_groups:
        utils.log_info("Removing vertex group: " + pin_group + " from: " + obj.name)
        obj.vertex_groups.remove(obj.vertex_groups[pin_group])


def remove_all_physics_mods(obj):
    """Removes all physics modifiers from the object.

    Used when (re)building the character materials.
    """

    utils.log_info("Removing all related physics modifiers from: " + obj.name)
    for mod in obj.modifiers:
        if mod.type == "VERTEX_WEIGHT_EDIT" and vars.NODE_PREFIX in mod.name:
            obj.modifiers.remove(mod)
        elif mod.type == "VERTEX_WEIGHT_MIX" and vars.NODE_PREFIX in mod.name:
            obj.modifiers.remove(mod)
        elif mod.type == "CLOTH":
            obj.modifiers.remove(mod)
        elif mod.type == "COLLISION":
            obj.modifiers.remove(mod)


def enable_collision_physics(obj):
    cache = get_object_cache(obj)
    cache.collision_physics = "ON"
    utils.log_info("Enabling Collision physics for: " + obj.name)
    add_collision_physics(obj)


def disable_collision_physics(obj):
    cache = get_object_cache(obj)
    cache.collision_physics = "OFF"
    utils.log_info("Disabling Collision physics for: " + obj.name)
    remove_collision_physics(obj)


def enable_cloth_physics(obj):
    cache = get_object_cache(obj)
    cache.cloth_physics = "ON"
    utils.log_info("Enabling Cloth physics for: " + obj.name)
    add_cloth_physics(obj)


def disable_cloth_physics(obj):
    cache = get_object_cache(obj)
    cache.cloth_physics = "OFF"
    utils.log_info("Removing cloth physics for: " + obj.name)
    remove_cloth_physics(obj)


def get_weight_map_image(obj, mat, create = False):
    """Returns the weight map image for the material.

    Fetches the Image for the given materials weight map, if it exists.
    If not, the image can be created and packed into the blend file and stored
    in the material cache as a temporary weight map image.
    """

    props = bpy.context.scene.CC3ImportProps
    weight_map = find_material_image(mat, vars.WEIGHT_MAP)

    if weight_map is None and create:
        cache = get_material_cache(mat)
        name = strip_name(mat.name) + "_WeightMap"
        tex_size = int(props.physics_tex_size)
        weight_map = bpy.data.images.new(name, tex_size, tex_size, is_data=True)
        # make the image 'dirty' so it converts to a file based image which can be saved:
        weight_map.pixels[0] = 0.0
        weight_map.file_format = "PNG"
        weight_map.filepath_raw = os.path.join(cache.dir, name + ".png")
        weight_map.save()
        # keep track of which weight maps we created:
        cache.temp_weight_map = weight_map
        utils.log_info("Weight-map image: " + weight_map.name + " created and saved.")

    return weight_map


def add_material_weight_map(obj, mat, create = False):
    """Adds a weight map 'Vertex Weight Edit' modifier for the object's material.

    Gets or creates (if instructed) the material's weight map then creates
    or re-creates the modifier to generate the physics 'Pin' vertex group.
    """

    if cloth_physics_available(obj, mat):
        if create:
            weight_map = get_weight_map_image(obj, mat, create)
        else:
            weight_map = find_material_image(mat, vars.WEIGHT_MAP)

        remove_material_weight_maps(obj, mat)
        if weight_map is not None:
            attach_material_weight_map(obj, mat, weight_map)
    else:
        utils.log_info("Cloth Physics has been disabled for: " + obj.name)
        return


def remove_material_weight_maps(obj, mat):
    """Removes the weight map 'Vertex Weight Edit' modifier for the object's material.

    This does not remove or delete the weight map image or temporary packed image,
    or the texture based on the weight map image, just the modifier.
    """

    edit_mod, mix_mod = modutils.get_material_weight_map_mods(obj, mat)
    if edit_mod is not None:
        utils.log_info("    Removing weight map vertex edit modifer: " + edit_mod.name)
        obj.modifiers.remove(edit_mod)
    if mix_mod is not None:
        utils.log_info("    Removing weight map vertex mix modifer: " + mix_mod.name)
        obj.modifiers.remove(mix_mod)


def enable_material_weight_map(obj, mat):
    """Enables the weight map for the object's material and (re)creates the Vertex Weight Edit modifier.
    """

    cache = get_material_cache(mat)
    if cache.cloth_physics == "OFF":
        cache.cloth_physics = "ON"
    add_material_weight_map(obj, mat, True)
    # fix mod order
    cloth_mod = modutils.get_cloth_physics_mod(obj)
    modutils.move_mod_last(obj, cloth_mod)


def disable_material_weight_map(obj, mat):
    """Disables the weight map for the object's material and removes the Vertex Weight Edit modifier.
    """

    cache = get_material_cache(mat)
    cache.cloth_physics = "OFF"
    remove_material_weight_maps(obj, mat)
    pass


def collision_physics_available(obj):
    obj_cache = get_object_cache(obj)
    collision_mod = modutils.get_collision_physics_mod(obj)
    if collision_mod is None:
        if obj_cache.collision_physics == "OFF":
            return False
    return True


def cloth_physics_available(obj, mat):
    """Is cloth physics allowed on this object and material?
    """

    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    cloth_mod = modutils.get_cloth_physics_mod(obj)
    if cloth_mod is None:
        if obj_cache.cloth_physics == "OFF":
            return False
        if mat_cache is not None and mat_cache.cloth_physics == "OFF":
            return False
    else:
        # if cloth physics was disabled by the add-on,
        # but re-enabled in the physics panel,
        # correct the object cache setting:
        if obj_cache.cloth_physics == "OFF":
            obj_cache.cloth_physics == "ON"
    return True


def get_material_vertices(obj, mat):
    verts = []
    mesh = obj.data
    for poly in mesh.polygons:
        poly_mat = obj.material_slots[poly.material_index].material
        if poly_mat == mat:
            for vert in poly.vertices:
                if vert not in verts:
                    verts.append(vert)
    return verts


def attach_material_weight_map(obj, mat, weight_map):
    """Attaches a weight map to the object's material via a 'Vertex Weight Edit' modifier.

    This will attach the supplied weight map or will try to find an existing weight map,
    but will not create a new weight map if it doesn't already exist.
    """

    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if weight_map is not None:
        # Make a texture based on the weight map image
        mat_name = strip_name(mat.name)
        tex_name = mat_name + "_Weight"
        tex = None
        for t in bpy.data.textures:
            if t.name.startswith(vars.NODE_PREFIX + tex_name):
                tex = t
        if tex is None:
            tex = bpy.data.textures.new(utils.unique_name(tex_name), "IMAGE")
            utils.log_info("Texture: " + tex.name + " created for weight map transfer")
        else:
            utils.log_info("Texture: " + tex.name + " already exists for weight map transfer")
        tex.image = weight_map

        # Create the physics pin vertex group and the material weightmap group if they don't exist:
        pin_group = prefs.physics_group + "_Pin"
        material_group = prefs.physics_group + "_" + mat_name
        if pin_group not in obj.vertex_groups:
            pin_vertex_group = obj.vertex_groups.new(name = pin_group)
        else:
            pin_vertex_group = obj.vertex_groups[pin_group]
        if material_group not in obj.vertex_groups:
            weight_vertex_group = obj.vertex_groups.new(name = material_group)
        else:
            weight_vertex_group = obj.vertex_groups[material_group]
        # The material weight map group should contain only those verteces affected by the material, default weight to 1.0
        meshutils.clear_vertex_group(obj, weight_vertex_group)
        mat_verts = get_material_vertices(obj, mat)
        weight_vertex_group.add(mat_verts, 1.0, 'ADD')
        # The pin group should contain all verteces in the mesh default weighted to 1.0
        meshutils.set_vertex_group(obj, pin_vertex_group, 1.0)

        # set the pin group in the cloth physics modifier
        mod_cloth = modutils.get_cloth_physics_mod(obj)
        if mod_cloth is not None:
            mod_cloth.settings.vertex_group_mass = pin_group

        # re-create create the Vertex Weight Edit modifier and the Vertex Weight Mix modifer
        remove_material_weight_maps(obj, mat)
        edit_mod = obj.modifiers.new(utils.unique_name(mat_name + "_WeightEdit"), "VERTEX_WEIGHT_EDIT")
        mix_mod = obj.modifiers.new(utils.unique_name(mat_name + "_WeightMix"), "VERTEX_WEIGHT_MIX")
        # Use the texture as the modifiers vertex weight source
        edit_mod.mask_texture = tex
        # Setup the modifier to generate the inverse of the weight map in the vertex group
        edit_mod.use_add = False
        edit_mod.use_remove = False
        edit_mod.add_threshold = 0.01
        edit_mod.remove_threshold = 0.01
        edit_mod.vertex_group = material_group
        edit_mod.default_weight = 1
        edit_mod.falloff_type = 'LINEAR'
        edit_mod.invert_falloff = True
        edit_mod.mask_constant = 1
        edit_mod.mask_tex_mapping = 'UV'
        edit_mod.mask_tex_use_channel = 'INT'
        # The Vertex Weight Mix modifier takes the material weight map group and mixes it into the pin weight group:
        # (this allows multiple weight maps from different materials and UV layouts to combine in the same mesh)
        mix_mod.vertex_group_a = pin_group
        mix_mod.vertex_group_b = material_group
        mix_mod.invert_mask_vertex_group = True
        mix_mod.default_weight_a = 1
        mix_mod.default_weight_b = 1
        mix_mod.mix_set = 'B' #'ALL'
        mix_mod.mix_mode = 'SET'
        mix_mod.invert_mask_vertex_group = False
        utils.log_info("Weight map: " + weight_map.name + " applied to: " + obj.name + "/" + mat.name)


def count_weightmaps(objects):
    num_maps = 0
    num_dirty = 0
    for obj in objects:
        if obj.type == "MESH":
            for mod in obj.modifiers:
                if mod.type == "VERTEX_WEIGHT_EDIT" and vars.NODE_PREFIX in mod.name:
                    if mod.mask_texture is not None and mod.mask_texture.image is not None:
                        num_maps += 1
                        image = mod.mask_texture.image
                        if image.is_dirty:
                            num_dirty += 1
    return num_maps, num_dirty


def get_dirty_weightmaps(objects):
    maps = []
    for obj in objects:
        if obj.type == "MESH":
            for mod in obj.modifiers:
                if mod.type == "VERTEX_WEIGHT_EDIT" and vars.NODE_PREFIX in mod.name:
                    if mod.mask_texture is not None and mod.mask_texture.image is not None:
                        image = mod.mask_texture.image
                        if image.filepath != "" and (image.is_dirty or not os.path.exists(image.filepath)):
                            maps.append(image)
    return maps


def begin_paint_weight_map(context):
    obj = context.object
    mat = context_material(context)
    props = bpy.context.scene.CC3ImportProps
    if obj is not None and mat is not None:
        props.paint_store_render = bpy.context.space_data.shading.type

        if bpy.context.mode != "PAINT_TEXTURE":
            bpy.ops.object.mode_set(mode="TEXTURE_PAINT")

        if bpy.context.mode == "PAINT_TEXTURE":
            physics_paint_strength_update(None, context)
            weight_map = get_weight_map_image(obj, mat)
            props.paint_object = obj
            props.paint_material = mat
            props.paint_image = weight_map
            if weight_map is not None:
                bpy.context.scene.tool_settings.image_paint.mode = 'IMAGE'
                bpy.context.scene.tool_settings.image_paint.canvas = weight_map
                bpy.context.space_data.shading.type = 'SOLID'


def end_paint_weight_map():
    try:
        props = bpy.context.scene.CC3ImportProps
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.space_data.shading.type = props.paint_store_render
        #props.paint_image.save()
    except Exception as e:
        utils.log_error("Something went wrong restoring object mode from paint mode!", e)


def save_dirty_weight_maps(objects):
    """Saves all altered active weight map images to their respective material folders.

    Also saves any missing weight maps.
    """

    maps = get_dirty_weightmaps(objects)

    for weight_map in maps:
        if weight_map.is_dirty:
            utils.log_info("Dirty weight map: " + weight_map.name + " : " + weight_map.filepath)
            weight_map.save()
            utils.log_info("Weight Map: " + weight_map.name + " saved to: " + weight_map.filepath)
        if not os.path.exists(weight_map.filepath):
            utils.log_info("Missing weight map: " + weight_map.name + " : " + weight_map.filepath)
            weight_map.save()
            utils.log_info("Weight Map: " + weight_map.name + " saved to: " + weight_map.filepath)


def delete_selected_weight_map(obj, mat):
    if obj is not None and obj.type == "MESH" and mat is not None:
        edit_mod, mix_mod = modutils.get_material_weight_map_mods(obj, mat)
        if edit_mod is not None and edit_mod.mask_texture is not None and edit_mod.mask_texture.image is not None:
            image = edit_mod.mask_texture.image
            try:
                if image.filepath != "" and os.path.exists(image.filepath):
                    utils.log_info("Removing weight map file: " + image.filepath)
                    os.remove(image.filepath)
            except Exception as e:
                utils.log_error("Removing weight map file: " + image.filepath, e)
        if edit_mod is not None:
            utils.log_info("Removing 'Vertex Weight Edit' modifer")
            obj.modifiers.remove(edit_mod)
        if mix_mod is not None:
            utils.log_info("Removing 'Vertex Weight Mix' modifer")
            obj.modifiers.remove(mix_mod)


def set_physics_bake_range(obj, start, end):
    cloth_mod = modutils.get_cloth_physics_mod(obj)

    if cloth_mod is not None:
        if obj.parent is not None and obj.parent.type == "ARMATURE":
            arm = obj.parent
            if arm.animation_data is not None and arm.animation_data.action is not None:
                frame_start = math.floor(arm.animation_data.action.frame_range[0])
                frame_end = math.ceil(arm.animation_data.action.frame_range[1])
                if frame_start < start:
                    start = frame_start
                if frame_end > end:
                    end = frame_end

            utils.log_info("Setting " + obj.name + " bake cache frame range to [" + str(start) + " -" + str(end) + "]")
            cloth_mod.point_cache.frame_start = start
            cloth_mod.point_cache.frame_end = end
            return True
    return False

def prepare_physics_bake(context):
    props = bpy.context.scene.CC3ImportProps

    for p in props.import_objects:
        if p.object is not None and p.object.type == "MESH":
            obj = p.object
            set_physics_bake_range(obj, context.scene.frame_start, context.scene.frame_end)


def separate_physics_materials(context):
    obj = context.object
    if (obj is not None
        and obj.type == "MESH"
        and context.mode == "OBJECT"):

        # remember which materials have active weight maps
        temp = []
        for mat in obj.data.materials:
            edit_mod, mix_mod = modutils.get_material_weight_map_mods(obj, mat)
            if edit_mod is not None:
                temp.append(mat)

        # remove cloth physics from the object
        disable_cloth_physics(obj)

        # split the mesh by materials
        tag_objects()
        obj.tag = False
        bpy.ops.mesh.separate(type='MATERIAL')
        split_objects = untagged_objects()

        # re-apply cloth physics to the materials which had weight maps
        for split in split_objects:
            for mat in split.data.materials:
                if mat in temp:
                    enable_cloth_physics(split)
                    break
        temp = None


def should_separate_materials(context):
    """Check to see if the current object has a weight map for each material.
    If not separating the mesh by material could improve performance.
    """
    obj = context.object
    if obj is not None and obj.type == "MESH":

        cloth_mod = modutils.get_cloth_physics_mod(obj)
        if cloth_mod is not None:
            edit_mods, mix_mods = modutils.get_weight_map_mods(obj)
            if len(edit_mods) != len(obj.data.materials):
                return True
        return False


def fetch_anim_range(context):
    """Fetch anim range from character animation.
    """
    props = bpy.context.scene.CC3ImportProps

    for p in props.import_objects:
        if p.object is not None and p.object.type == "ARMATURE":
            obj = p.object
            if obj.animation_data is not None and \
               obj.animation_data.action is not None:
                frame_start = math.floor(obj.animation_data.action.frame_range[0])
                frame_end = math.ceil(obj.animation_data.action.frame_range[1])
                context.scene.frame_start = frame_start
                context.scene.frame_end = frame_end
                return


def render_image(context):
    # TODO
    pass


def render_animation(context):
    # TODO
    pass


def fix_eye_mod_order(obj):
    """Moves the armature modifier to the end of the list
    """
    edit_mod = get_object_modifier(obj, "VERTEX_WEIGHT_EDIT", "Eye_WeightEdit")
    displace_mod = get_object_modifier(obj, "DISPLACE", "Eye_Displace")
    warp_mod = get_object_modifier(obj, "UV_WARP", "Eye_UV_Warp")
    modutils.move_mod_first(warp_mod)
    modutils.move_mod_first(displace_mod)
    modutils.move_mod_first(edit_mod)


def remove_eye_modifiers(obj):
    if obj and obj.type == "MESH":
        for mod in obj.modifiers:
            if vars.NODE_PREFIX in mod.name:
                if mod.type == "DISPLACE" or mod.type == "UV_WARP" or mod.type == "VERTEX_WEIGHT_EDIT":
                    obj.modifiers.remove(mod)


def rebuild_eye_vertex_groups():
    props = bpy.context.scene.CC3ImportProps

    for cache in props.object_cache:
        obj = cache.object
        if cache.is_eye():
            mat_left, mat_right = materials.get_left_right_eye_materials(obj)
            cache_left = get_material_cache(mat_left)
            cache_right = get_material_cache(mat_right)

            print(mat_left.name + ":" + mat_right.name)

            if cache_left and cache_right:
                # Re-create the eye displacement group
                meshutils.generate_eye_vertex_groups(obj, mat_left, mat_right, cache_left, cache_right)


def add_eye_modifiers(obj):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    # fetch the eye materials (not the cornea materials)
    mat_left, mat_right = materials.get_left_right_eye_materials(obj)
    cache_left = get_material_cache(mat_left)
    cache_right = get_material_cache(mat_right)

    if cache_left is None or cache_right is None:
        return

    # Create the eye displacement group
    meshutils.generate_eye_vertex_groups(obj, mat_left, mat_right, cache_left, cache_right)

    remove_eye_modifiers(obj)
    displace_mod_l = obj.modifiers.new(utils.unique_name("Eye_Displace_L"), "DISPLACE")
    displace_mod_r = obj.modifiers.new(utils.unique_name("Eye_Displace_R"), "DISPLACE")
    warp_mod_l = obj.modifiers.new(utils.unique_name("Eye_UV_Warp_L"), "UV_WARP")
    warp_mod_r = obj.modifiers.new(utils.unique_name("Eye_UV_Warp_R"), "UV_WARP")

    modutils.init_displacement_mod(obj, displace_mod_l, prefs.eye_displacement_group + "_L", "Y", cache_left.parameters.eye_iris_depth)
    modutils.init_displacement_mod(obj, displace_mod_r, prefs.eye_displacement_group + "_R", "Y", cache_right.parameters.eye_iris_depth)

    warp_mod_l.center = (0.5, 0.5)
    warp_mod_l.axis_u = "X"
    warp_mod_l.axis_v = "Y"
    warp_mod_l.vertex_group = prefs.eye_displacement_group + "_L"
    warp_mod_l.scale = (1.0 / cache_left.parameters.eye_pupil_scale, 1.0 / cache_left.parameters.eye_pupil_scale)

    warp_mod_r.center = (0.5, 0.5)
    warp_mod_r.axis_u = "X"
    warp_mod_r.axis_v = "Y"
    warp_mod_r.vertex_group = prefs.eye_displacement_group + "_R"
    warp_mod_r.scale = (1.0 / cache_right.parameters.eye_pupil_scale, 1.0 / cache_right.parameters.eye_pupil_scale)

    modutils.move_mod_first(obj, warp_mod_l)
    modutils.move_mod_first(obj, displace_mod_l)
    modutils.move_mod_first(obj, warp_mod_r)
    modutils.move_mod_first(obj, displace_mod_r)

    utils.log_info("Eye Displacement modifiers applied to: " + obj.name)


def add_eye_occlusion_modifiers(obj):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    mat_left, mat_right = materials.get_left_right_materials(obj)
    cache_left = get_material_cache(mat_left)
    cache_right = get_material_cache(mat_right)

    if cache_left is None or cache_right is None:
        return

    # generate the vertex groups for occlusion displacement
    meshutils.generate_eye_occlusion_vertex_groups(obj, mat_left, mat_right)

    # re-create create the displacement modifiers
    remove_eye_modifiers(obj)
    displace_mod_inner_l = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Inner_L"), "DISPLACE")
    displace_mod_outer_l = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Outer_L"), "DISPLACE")
    displace_mod_top_l = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Top_L"), "DISPLACE")
    displace_mod_bottom_l = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Bottom_L"), "DISPLACE")
    displace_mod_all_l = obj.modifiers.new(utils.unique_name("Occlusion_Displace_All_L"), "DISPLACE")

    displace_mod_inner_r = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Inner_R"), "DISPLACE")
    displace_mod_outer_r = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Outer_R"), "DISPLACE")
    displace_mod_top_r = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Top_R"), "DISPLACE")
    displace_mod_bottom_r = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Bottom_R"), "DISPLACE")
    displace_mod_all_r = obj.modifiers.new(utils.unique_name("Occlusion_Displace_All_R"), "DISPLACE")

    # initialise displacement mods
    modutils.init_displacement_mod(obj, displace_mod_inner_l, vars.OCCLUSION_GROUP_INNER + "_L", "NORMAL", cache_left.parameters.eye_occlusion_inner)
    modutils.init_displacement_mod(obj, displace_mod_outer_l, vars.OCCLUSION_GROUP_OUTER + "_L", "NORMAL", cache_left.parameters.eye_occlusion_outer)
    modutils.init_displacement_mod(obj, displace_mod_top_l, vars.OCCLUSION_GROUP_TOP + "_L", "NORMAL", cache_left.parameters.eye_occlusion_top)
    modutils.init_displacement_mod(obj, displace_mod_bottom_l, vars.OCCLUSION_GROUP_BOTTOM + "_L", "NORMAL", cache_left.parameters.eye_occlusion_bottom)
    modutils.init_displacement_mod(obj, displace_mod_all_l, vars.OCCLUSION_GROUP_ALL + "_L", "NORMAL", cache_left.parameters.eye_occlusion_displace)

    modutils.init_displacement_mod(obj, displace_mod_inner_r, vars.OCCLUSION_GROUP_INNER + "_R", "NORMAL", cache_right.parameters.eye_occlusion_inner)
    modutils.init_displacement_mod(obj, displace_mod_outer_r, vars.OCCLUSION_GROUP_OUTER + "_R", "NORMAL", cache_right.parameters.eye_occlusion_outer)
    modutils.init_displacement_mod(obj, displace_mod_top_r, vars.OCCLUSION_GROUP_TOP + "_R", "NORMAL", cache_right.parameters.eye_occlusion_top)
    modutils.init_displacement_mod(obj, displace_mod_bottom_r, vars.OCCLUSION_GROUP_BOTTOM + "_R", "NORMAL", cache_right.parameters.eye_occlusion_bottom)
    modutils.init_displacement_mod(obj, displace_mod_all_r, vars.OCCLUSION_GROUP_ALL + "_R", "NORMAL", cache_right.parameters.eye_occlusion_displace)

    # fix mod order
    modutils.move_mod_first(obj, displace_mod_inner_l)
    modutils.move_mod_first(obj, displace_mod_outer_l)
    modutils.move_mod_first(obj, displace_mod_top_l)
    modutils.move_mod_first(obj, displace_mod_bottom_l)
    modutils.move_mod_first(obj, displace_mod_all_l)
    modutils.move_mod_first(obj, displace_mod_inner_r)
    modutils.move_mod_first(obj, displace_mod_outer_r)
    modutils.move_mod_first(obj, displace_mod_top_r)
    modutils.move_mod_first(obj, displace_mod_bottom_r)
    modutils.move_mod_first(obj, displace_mod_all_r)

    utils.log_info("Eye Occlusion Displacement modifiers applied to: " + obj.name)


def add_tearline_modifiers(obj):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    mat_left, mat_right = materials.get_left_right_materials(obj)
    cache_left = get_material_cache(mat_left)
    cache_right = get_material_cache(mat_right)

    if cache_left is None or cache_right is None:
        return

    # generate the vertex groups for tearline displacement
    meshutils.generate_tearline_vertex_groups(obj, mat_left, mat_right)

    # re-create create the displacement modifiers
    remove_eye_modifiers(obj)
    displace_mod_inner_l = obj.modifiers.new(utils.unique_name("Tearline_Displace_Inner_L"), "DISPLACE")
    displace_mod_all_l = obj.modifiers.new(utils.unique_name("Tearline_Displace_All_L"), "DISPLACE")
    displace_mod_inner_r = obj.modifiers.new(utils.unique_name("Tearline_Displace_Inner_R"), "DISPLACE")
    displace_mod_all_r = obj.modifiers.new(utils.unique_name("Tearline_Displace_All_R"), "DISPLACE")

    # initialise displacement mods
    modutils.init_displacement_mod(obj, displace_mod_inner_l, vars.TEARLINE_GROUP_INNER + "_L", "Y", -cache_left.parameters.tearline_inner)
    modutils.init_displacement_mod(obj, displace_mod_all_l, vars.TEARLINE_GROUP_ALL + "_L", "Y", -cache_left.parameters.tearline_displace)
    modutils.init_displacement_mod(obj, displace_mod_inner_r, vars.TEARLINE_GROUP_INNER + "_R", "Y", -cache_right.parameters.tearline_inner)
    modutils.init_displacement_mod(obj, displace_mod_all_r, vars.TEARLINE_GROUP_ALL + "_R", "Y", -cache_right.parameters.tearline_displace)

    # fix mod order
    modutils.move_mod_first(obj, displace_mod_inner_l)
    modutils.move_mod_first(obj, displace_mod_all_l)
    modutils.move_mod_first(obj, displace_mod_inner_r)
    modutils.move_mod_first(obj, displace_mod_all_r)

    utils.log_info("Tearline Displacement modifiers applied to: " + obj.name)



def clean_colletion(collection):
    for item in collection:
        if (item.use_fake_user and item.users == 1) or item.users == 0:
            collection.remove(item)

def delete_object(obj):
    if obj is None:
        return

    # remove any armature actions
    if obj.type == "ARMATURE":
        if obj.animation_data is not None:
            if obj.animation_data.action is not None:
                bpy.data.actions.remove(obj.animation_data.action)

    # remove any shape key actions and remove the shape keys
    if obj.type == "MESH":
        if obj.data.shape_keys is not None:
            if obj.data.shape_keys.animation_data is not None:
                if obj.data.shape_keys.animation_data.action is not None:
                    bpy.data.actions.remove(obj.data.shape_keys.animation_data.action)
        obj.shape_key_clear()

        # remove materials->nodes->images
        for mat in obj.data.materials:
            if mat.node_tree is not None:
                nodes = mat.node_tree.nodes
                for node in nodes:
                    if node.type == "TEX_IMAGE" and node.image is not None:
                        image = node.image
                        bpy.data.images.remove(image)
                    nodes.remove(node)

            # remove physics weight maps and texture masks
            edit_mod, mix_mod = modutils.get_material_weight_map_mods(obj, mat)
            if mix_mod is not None:
                obj.modifiers.remove(mix_mod)
            if edit_mod is not None:
                tex = edit_mod.mask_texture
                obj.modifiers.remove(edit_mod)
                if tex is not None:
                    if tex.image is not None:
                        image = tex.image
                        bpy.data.images.remove(image)
                    bpy.data.textures.remove(tex)

            bpy.data.materials.remove(mat)

    if obj.type == "ARMATURE":
        bpy.data.armatures.remove(obj.data)
    else:
        bpy.data.objects.remove(obj)

    #except:
    #    utils.log_error("Something went wrong deleting object...")


def delete_character():
    props = bpy.context.scene.CC3ImportProps

    for p in props.import_objects:
        delete_object(p.object)

    props.import_objects.clear()
    props.import_file = ""
    props.import_type = ""
    props.import_name = ""
    props.import_dir = ""
    props.import_main_tex_dir = ""
    props.import_space_in_name = False
    props.import_embedded = False
    props.import_has_key = False
    props.import_key_file = ""
    props.material_cache.clear()
    props.object_cache.clear()

    props.paint_object = None
    props.paint_material = None
    props.paint_image = None

    clean_colletion(bpy.data.materials)
    clean_colletion(bpy.data.textures)
    clean_colletion(bpy.data.images)
    clean_colletion(bpy.data.meshes)
    clean_colletion(bpy.data.node_groups)


def process_material(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    mat_cache = get_material_cache(mat)
    nodeutils.reset_nodes(mat)
    node_tree = mat.node_tree
    nodes = node_tree.nodes
    shader = None

    # find the Principled BSDF shader node
    for n in nodes:
        if (n.type == "BSDF_PRINCIPLED"):
            shader = n
            break

    # create one if it does not exist
    if shader is None:
        shader = nodes.new("ShaderNodeBsdfPrincipled")

    nodeutils.clear_cursor()

    if prefs.compat_mode:
        connect_compat_material(obj, mat, shader)

        nodeutils.move_new_nodes(-600, 0)

    elif mat_cache.is_cornea():

        if props.setup_mode == "BASIC":
            connect_basic_eye_material(obj, mat, shader)

        elif props.setup_mode == "ADVANCED":
            if prefs.refractive_eyes:
                connect_refractive_eye_material(obj, mat, shader)
            else:
                connect_adv_eye_material(obj, mat, shader)

        nodeutils.move_new_nodes(-600, 0)

    elif mat_cache.is_eye() and prefs.refractive_eyes:

        connect_refractive_eye_material(obj, mat, shader)
        nodeutils.move_new_nodes(-600, 0)

    elif mat_cache.is_tearline():

        connect_tearline_material(obj, mat, shader)

    elif mat_cache.is_eye_occlusion():

        if props.setup_mode == "ADVANCED" and prefs.use_advanced_eye_occlusion:
            connect_eye_occlusion_shader(obj, mat, shader)
        else:
            connect_eye_occlusion_material(obj, mat, shader)

        nodeutils.move_new_nodes(-600, 0)

    elif (mat_cache.is_teeth() or mat_cache.is_tongue()) and props.setup_mode == "ADVANCED":

        connect_adv_mouth_material(obj, mat, shader)
        nodeutils.move_new_nodes(-600, 0)

    else:

        if props.setup_mode == "BASIC":
            connect_basic_material(obj, mat, shader)

        elif props.setup_mode == "ADVANCED":
            connect_advanced_material(obj, mat, shader, mat_cache)

        nodeutils.move_new_nodes(-600, 0)

    # apply cached alpha settings
    if props.generation == "ACTORCORE":
        set_material_alpha(mat, "CLIP")
    elif mat_cache is not None:
        if mat_cache.alpha_mode != "NONE":
            apply_alpha_override(obj, mat, mat_cache.alpha_mode)
        if mat_cache.culling_sides > 0:
            apply_backface_culling(obj, mat, mat_cache.culling_sides)


def process_object(obj, objects_processed):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if obj is None or obj in objects_processed:
        return

    objects_processed.append(obj)

    utils.log_info("Processing Object: " + obj.name + ", Type: " + obj.type)

    cache = get_object_cache(obj)

    if obj.type == "MESH":
        # when rebuilding materials remove all the physics modifiers
        # they don't seem to like having their settings changed...
        remove_all_physics_mods(obj)

        # remove any modifiers for refractive eyes
        remove_eye_modifiers(obj)

        # process any materials found in the mesh object
        for mat in obj.data.materials:
            if mat is not None:
                utils.log_info("Processing Material: " + mat.name)
                process_material(obj, mat)
                if prefs.physics == "ENABLED" and props.physics_mode == "ON":
                    add_material_weight_map(obj, mat, create = False)

        # setup default physics
        if prefs.physics == "ENABLED" and props.physics_mode == "ON":
            add_collision_physics(obj)
            edit_mods, mix_mods = modutils.get_weight_map_mods(obj)
            if len(edit_mods) > 0:
                enable_cloth_physics(obj)

        # setup special modifiers for displacement, UV warp, etc...
        if props.setup_mode == "ADVANCED":
            if prefs.refractive_eyes and cache.is_eye():
                add_eye_modifiers(obj)
            elif prefs.use_advanced_eye_occlusion and cache.is_eye_occlusion():
                add_eye_occlusion_modifiers(obj)
            elif cache.is_tearline():
                add_tearline_modifiers(obj)


    elif obj.type == "ARMATURE":

        # set the frame range of the scene to the active action on the armature
        if prefs.physics == "ENABLED" and props.physics_mode == "ON":
            fetch_anim_range(bpy.context)


def get_material_dir(base_dir, character_name, import_type, obj, mat):
    props = bpy.context.scene.CC3ImportProps

    if import_type == "fbx":
        object_name = strip_name(obj.name)
        mesh_name = strip_name(obj.data.name)
        material_name = strip_name(mat.name)
        if "cc_base_" in object_name.lower() or props.generation == "ACTORCORE":
            path = os.path.join(base_dir, "textures", character_name, character_name, mesh_name, material_name)
            if os.path.exists(path):
                return path
        path = os.path.join(base_dir, "textures", character_name, object_name, mesh_name, material_name)
        if os.path.exists(path):
            return path
        return os.path.join(base_dir, character_name + ".fbm")

    elif import_type == "obj":
        return os.path.join(base_dir, character_name)


def get_object_cache(obj, no_create = False):
    """Returns the object cache for this object.

    Fetches or creates an object cache for the object. Always returns an object cache collection.
    """

    cache = None
    props = bpy.context.scene.CC3ImportProps
    if obj is not None:
        for cache in props.object_cache:
            if cache.object == obj:
                return cache
        if not no_create:
            utils.log_info("Creating Object Cache for: " + obj.name)
            cache = props.object_cache.add()
            cache.object = obj
    return cache


def get_material_cache(mat, no_create = False):
    """Returns the material cache for this material.

    Fetches the material cache for the material. Returns None if the material is not in the cache.
    """

    cache = None
    props = bpy.context.scene.CC3ImportProps
    if mat is not None:
        for cache in props.material_cache:
            if cache.material == mat:
                return cache
        if not no_create:
            utils.log_info("Creating Material Cache for: " + mat.name)
            cache = props.material_cache.add()
            cache.material = mat
    return cache


def cache_object_materials(obj):
    props = bpy.context.scene.CC3ImportProps
    main_tex_dir = props.import_main_tex_dir
    base_dir, file_name = os.path.split(props.import_file)
    type = file_name[-3:].lower()
    character_name = file_name[:-4]

    if obj is None:
        return

    obj_cache = get_object_cache(obj)

    if obj.type == "MESH":
        for mat in obj.data.materials:
            if mat.node_tree is not None:
                mat_name = mat.name.lower()
                mat_cache = get_material_cache(mat)
                mat_cache.material = mat
                mat_cache.dir = get_material_dir(base_dir, character_name, type, obj, mat)
                nodes = mat.node_tree.nodes

                # determine object and material types:
                if props.generation == "ACTORCORE":
                    obj_cache.object_type = "DEFAULT"
                    mat_cache.material_type = "DEFAULT"
                    mat_cache.parameters.default_roughness = 0.1
                elif detect_hair_object(obj, mat) == "True":
                    obj_cache.object_type = "HAIR"
                    # hold off detecting scalp meshes as the hair mesh might not be detected
                    # at the first material, the hair mesh needs a second material pass...
                elif detect_body_object(obj):
                    obj_cache.object_type = "BODY"
                    if detect_skin_material(mat):
                        if "head" in mat_name:
                            mat_cache.material_type = "SKIN_HEAD"
                        elif "body" in mat_name:
                            mat_cache.material_type = "SKIN_BODY"
                        elif "arm" in mat_name:
                            mat_cache.material_type = "SKIN_ARM"
                        elif "leg" in mat_name:
                            mat_cache.material_type = "SKIN_LEG"
                    elif detect_nails_material(mat):
                        mat_cache.material_type = "NAILS"
                    elif detect_eyelash_material(mat):
                        mat_cache.material_type = "EYELASH"
                elif detect_cornea_material(mat):
                    obj_cache.object_type = "EYE"
                    if detect_material_side(mat, "LEFT"):
                        mat_cache.material_type = "CORNEA_LEFT"
                    else:
                        mat_cache.material_type = "CORNEA_RIGHT"
                elif detect_eye_occlusion_material(mat): # detect occlusion before eye
                    obj_cache.object_type = "OCCLUSION"
                    if detect_material_side(mat, "LEFT"):
                        mat_cache.material_type = "OCCLUSION_LEFT"
                    else:
                        mat_cache.material_type = "OCCLUSION_RIGHT"
                elif detect_eye_material(mat):
                    obj_cache.object_type = "EYE"
                    if detect_material_side(mat, "LEFT"):
                        mat_cache.material_type = "EYE_LEFT"
                    else:
                        mat_cache.material_type = "EYE_RIGHT"
                elif detect_tearline_material(mat):
                    obj_cache.object_type = "TEARLINE"
                    if detect_material_side(mat, "LEFT"):
                        mat_cache.material_type = "TEARLINE_LEFT"
                    else:
                        mat_cache.material_type = "TEARLINE_RIGHT"
                elif detect_teeth_material(mat):
                    obj_cache.object_type = "TEETH"
                    if detect_material_side(mat, "UPPER"):
                        mat_cache.material_type = "TEETH_UPPER"
                    else:
                        mat_cache.material_type = "TEETH_LOWER"
                elif detect_tongue_material(mat):
                    obj_cache.object_type = "TONGUE"
                    mat_cache.material_type = "TONGUE"

                # detect embedded textures
                for node in nodes:
                    if node.type == "TEX_IMAGE" and node.image is not None:
                        filepath = node.image.filepath
                        dir, name = os.path.split(filepath)
                        # detect incorrect image paths for non packed (not embedded) images and attempt to correct...
                        if node.image.packed_file is None:
                            if os.path.normcase(dir) != os.path.normcase(main_tex_dir):
                                utils.log_warn("Import bug! Wrong image path detected: " + dir)
                                utils.log_warn("    Attempting to correct...")
                                correct_path = os.path.join(main_tex_dir, name)
                                if os.path.exists(correct_path):
                                    utils.log_warn("    Correct image path found: " + correct_path)
                                    node.image.filepath = correct_path
                                else:
                                    correct_path = os.path.join(mat_cache.dir, name)
                                    if os.path.exists(correct_path):
                                        utils.log_warn("    Correct image path found: " + correct_path)
                                        node.image.filepath = correct_path
                                    else:
                                        utils.log_error("    Unable to find correct image!")
                        name = name.lower()
                        socket = nodeutils.get_input_connected_to(node, "Color")
                        # the fbx importer in 2.91 makes a total balls up of the opacity
                        # and connects the alpha output to the socket and not the color output
                        alpha_socket = nodeutils.get_input_connected_to(node, "Alpha")
                        if socket == "Base Color":
                            mat_cache.diffuse = node.image
                        elif socket == "Specular":
                            mat_cache.specular = node.image
                        elif socket == "Alpha" or alpha_socket == "Alpha":
                            mat_cache.alpha = node.image
                            if "diffuse" in name or "albedo" in name:
                                mat_cache.alpha_is_diffuse = True
                        elif socket == "Color":
                            if "bump" in name:
                                mat_cache.bump = node.image
                            else:
                                mat_cache.normal = node.image

        # second material pass for hair meshes
        if obj_cache.is_hair():
            for mat in obj.data.materials:
                mat_cache = get_material_cache(mat)
                if detect_hair_object(obj, mat) == "Deny":
                    mat_cache.material_type = "DEFAULT"
                else:
                    detect = detect_scalp_material(mat)
                    if detect == "Deny":
                        mat_cache.material_type = "DEFAULT"
                    elif detect == "True":
                        mat_cache.material_type = "SCALP"
                    else:
                        mat_cache.material_type = "HAIR"



def tag_objects():
    for obj in bpy.data.objects:
        obj.tag = True


def untagged_objects():
    untagged = []
    for obj in bpy.data.objects:
        if obj.tag == False:
            untagged.append(obj)
        obj.tag = False
    return untagged


def reconstruct_obj_materials(obj):
    mesh = obj.data
    # remove all materials
    mesh.materials.clear()
    # add new materials
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
    # figure out which polygon belongs to which material from the vertex groups and uv coords
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
            # head/eyes/tongue/teeth - determine from vertex group
            if group == 0: # tongue
                poly.material_index = 8
            elif group == 1: # body (head)
                poly.material_index = 0
            elif group == 2: # eye
                # can't easily differentiate between the eye parts, set all to right cornea
                poly.material_index = 11
            elif group == 3: # teeth
                # same with the teeth, set both to upper teeth
                poly.material_index = 6

def select_all_child_objects(obj):
    if obj.type == "ARMATURE" or obj.type == "MESH":
        obj.select_set(True)
    for child in obj.children:
        select_all_child_objects(child)

class CC3Import(bpy.types.Operator):
    """Import CC3 Character and build materials"""
    bl_idname = "cc3.importer"
    bl_label = "Import"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(
        name="Filepath",
        description="Filepath of the fbx or obj to import.",
        subtype="FILE_PATH"
        )

    filter_glob: bpy.props.StringProperty(
        default="*.fbx;*.obj",
        options={"HIDDEN"},
        )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    use_anim: bpy.props.BoolProperty(name = "Import Animation", description = "Import animation with character.\nWarning: long animations take a very long time to import in Blender 2.83", default = True)

    running = False
    imported = False
    built = False
    lighting = False
    timer = None
    clock = 0
    invoked = False

    def import_character(self):
        props = bpy.context.scene.CC3ImportProps

        utils.start_timer()

        import_anim = self.use_anim
        # don't import animation data if importing for morph/accessory
        if self.param == "IMPORT_MORPH":
            import_anim = False
        props.import_file = self.filepath
        dir, name = os.path.split(self.filepath)
        props.import_objects.clear()
        props.material_cache.clear()
        type = name[-3:].lower()
        name = name[:-4]
        props.import_type = type
        props.import_name = name
        props.import_dir = dir
        props.import_space_in_name = " " in name

        if type == "fbx":
            # determine the main texture dir
            props.import_main_tex_dir = os.path.join(dir, name + ".fbm")
            if os.path.exists(props.import_main_tex_dir):
                props.import_embedded = False
            else:
                props.import_main_tex_dir = ""
                props.import_embedded = True

            # invoke the fbx importer
            tag_objects()
            bpy.ops.import_scene.fbx(filepath=self.filepath, directory=dir, use_anim=import_anim)

            # process imported objects
            imported = untagged_objects()

            # detect generation
            props.generation = detect_generation(imported)
            utils.log_info("Generation: " + props.generation)

            for obj in imported:
                if obj.type == "ARMATURE":
                    p = props.import_objects.add()
                    p.object = obj
                if obj.type == "MESH":
                    p = props.import_objects.add()
                    p.object = obj
                    cache_object_materials(obj)

            utils.log_timer("Done .Fbx Import.")

        elif type == "obj":
            # determine the main texture dir
            props.import_main_tex_dir = os.path.join(dir, name)
            props.import_embedded = False
            if not os.path.exists(props.import_main_tex_dir):
                props.import_main_tex_dir = ""

            # invoke the obj importer
            tag_objects()
            if self.param == "IMPORT_MORPH":
                bpy.ops.import_scene.obj(filepath = self.filepath, split_mode = "OFF",
                        use_split_objects = False, use_split_groups = False,
                        use_groups_as_vgroups = True)
            else:
                bpy.ops.import_scene.obj(filepath = self.filepath, split_mode = "ON",
                        use_split_objects = True, use_split_groups = True,
                        use_groups_as_vgroups = False)

            # process imported objects
            imported = untagged_objects()

            # detect generation
            props.generation = detect_generation(imported)
            utils.log_info("Generation: " + props.generation)

            for obj in imported:
                # scale obj import by 1/100
                obj.scale = (0.01, 0.01, 0.01)
                if obj.type == "MESH":
                    p = props.import_objects.add()
                    p.object = obj
                    if self.param == "IMPORT_MORPH":
                        if props.import_main_tex_dir != "":
                            #reconstruct_obj_materials(obj)
                            pass
                    else:
                        cache_object_materials(obj)

            utils.log_timer("Done .Obj Import.")

    def build_materials(self):
        objects_processed = []
        props = bpy.context.scene.CC3ImportProps

        utils.start_timer()

        nodeutils.check_node_groups()

        if props.build_mode == "IMPORTED":
            for p in props.import_objects:
                if p.object is not None:
                    process_object(p.object, objects_processed)

        elif props.build_mode == "SELECTED":
            for obj in bpy.context.selected_objects:
                process_object(obj, objects_processed)

        utils.log_timer("Done Build.", "s")

    def run_import(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        # use basic materials for morph/accessory editing as it has better viewport performance
        if self.param == "IMPORT_MORPH":
            props.setup_mode = prefs.morph_mode
        elif self.param == "IMPORT_ACCESSORY":
            props.setup_mode = prefs.pipeline_mode
        # use advanced materials for quality/rendering
        elif self.param == "IMPORT_QUALITY":
            props.setup_mode = prefs.quality_mode

        self.import_character()

        # check for fbxkey
        if props.import_type == "fbx":
            props.import_key_file = os.path.join(props.import_dir, props.import_name + ".fbxkey")
            props.import_has_key = os.path.exists(props.import_key_file)
            if self.param == "IMPORT_MORPH" and not props.import_has_key:
                utils.message_box("This character export does not have an .fbxkey file, it cannot be used to create character morphs in CC3.", "FBXKey Warning")


        # check for objkey
        if props.import_type == "obj":
            props.import_key_file = os.path.join(props.import_dir, props.import_name + ".ObjKey")
            props.import_has_key = os.path.exists(props.import_key_file)
            if self.param == "IMPORT_MORPH" and not props.import_has_key:
                utils.message_box("This character export does not have an .ObjKey file, it cannot be used to create character morphs in CC3.", "OBJKey Warning")

        self.imported = True

    def run_build(self, context):
        self.build_materials()
        self.built = True

    def run_finish(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        # for any objects with shape keys expand the slider range to -1.0 <> 1.0
        # Character Creator and iClone both use negative ranges extensively.
        for p in props.import_objects:
            init_shape_key_range(p.object)

        # use the cc3 lighting for morph/accessory editing
        if self.param == "IMPORT_MORPH" or self.param == "IMPORT_ACCESSORY":
            if prefs.lighting == "ENABLED" and props.lighting_mode == "ON":
                if props.import_type == "fbx":
                    setup_scene_default(prefs.pipeline_lighting)
                else:
                    setup_scene_default(prefs.morph_lighting)

            # for any objects with shape keys select basis and enable show in edit mode
            for p in props.import_objects:
                init_character_for_edit(p.object)

        # use portrait lighting for quality mode
        elif self.param == "IMPORT_QUALITY":
            if prefs.lighting == "ENABLED" and props.lighting_mode == "ON":
                setup_scene_default(prefs.quality_lighting)

        if prefs.refractive_eyes:
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True

        zoom_to_character()
        self.lighting = True

    def modal(self, context, event):

        # 60 second timeout
        if event.type == 'TIMER':
            self.clock = self.clock + 1
            if self.clock > 60:
                self.cancel(context)
                self.report({'INFO'}, "Import operator timed out!")
                return {'CANCELLED'}

        if event.type == 'TIMER' and not self.running:
            if not self.imported:
                self.running = True
                self.run_import(context)
                self.clock = 0
                self.running = False
            elif not self.built:
                self.running = True
                self.run_build(context)
                self.clock = 0
                self.running = False
            elif not self.lighting:
                self.running = True
                self.run_finish(context)
                self.clock = 0
                self.running = False

            if self.imported and self.built and self.lighting:
                self.cancel(context)
                self.report({'INFO'}, "All done!")
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):
        if self.timer is not None:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        # import character
        if "IMPORT" in self.param:
            if self.filepath != "" and os.path.exists(self.filepath):
                if self.invoked and self.timer is None:
                    self.imported = False
                    self.built = False
                    self.lighting = False
                    self.running = False
                    self.clock = 0
                    self.report({'INFO'}, "Importing Character, please wait for import to finish and materials to build...")
                    bpy.context.window_manager.modal_handler_add(self)
                    self.timer = context.window_manager.event_timer_add(1.0, window = bpy.context.window)
                    return {'PASS_THROUGH'}
                elif not self.invoked:
                    self.run_import(context)
                    self.run_build(context)
                    self.run_finish(context)
                    return {'FINISHED'}
            else:
                utils.log_error("No valid filepath to import!")

        # build materials
        elif self.param == "BUILD":
            self.build_materials()

        # rebuild the node groups for advanced materials
        elif self.param == "REBUILD_NODE_GROUPS":
            nodeutils.rebuild_node_groups()

        elif self.param == "DELETE_CHARACTER":
            delete_character()

        return {"FINISHED"}

    def invoke(self, context, event):
        if "IMPORT" in self.param:
            context.window_manager.fileselect_add(self)
            self.invoked = True
            return {"RUNNING_MODAL"}

        return self.execute(context)

    @classmethod
    def description(cls, context, properties):
        if properties.param == "IMPORT":
            return "Import a new .fbx or .obj character exported by Character Creator 3"
        elif properties.param == "REIMPORT":
            return "Rebuild the materials from the last import with the current settings"
        elif properties.param == "IMPORT_MORPH":
            return "Import .fbx or .obj character from CC3 for morph creation. This does not import any animation data.\n" \
                   "Notes for exporting from CC3:\n" \
                   "1. For best results for morph creation export FBX: 'Mesh Only' or OBJ: Nude Character in Bind Pose, as these guarantee .fbxkey or .objkey generation.\n" \
                   "2. OBJ export 'Nude Character in Bind Pose' .obj does not export any materials.\n" \
                   "3. OBJ export 'Character with Current Pose' does not create an .objkey and cannot be used for morph creation.\n" \
                   "4. FBX export with motion in 'Current Pose' or 'Custom Motion' also does not export an .fbxkey and cannot be used for morph creation"
        elif properties.param == "IMPORT_ACCESSORY":
            return "Import .fbx or .obj character from CC3 for accessory creation. This will import current pose or animation.\n" \
                   "Notes for exporting from CC3:\n" \
                   "1. OBJ or FBX exports in 'Current Pose' are good for accessory creation as they import back into CC3 in exactly the right place"
        elif properties.param == "IMPORT_QUALITY":
            return "Import .fbx or .obj character from CC3 for rendering"
        elif properties.param == "BUILD":
            return "Build (or Rebuild) materials for the current imported character with the current build settings"
        elif properties.param == "DELETE_CHARACTER":
            return "Removes the character and any associated objects, meshes, materials, nodes, images, armature actions and shapekeys. Basically deletes everything not nailed down.\n**Do not press this if there is anything you want to keep!**"
        elif properties.param == "REBUILD_NODE_GROUPS":
            return "Rebuilds the shader node groups for the advanced and eye materials."
        return ""


class CC3Export(bpy.types.Operator):
    """Export CC3 Character"""
    bl_idname = "cc3.exporter"
    bl_label = "Export"
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        maxlen=1024,
        subtype='FILE_PATH',
        )

    filename_ext = ".fbx"  # ExportHelper mixin class uses this

    filter_glob: bpy.props.StringProperty(
        default="*.fbx;*.obj",
        options={"HIDDEN"},
        )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    use_anim: bpy.props.BoolProperty(name = "Export Animation", default = True)


    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps

        if self.param == "EXPORT_MORPH" or self.param == "EXPORT":
            export_anim = self.use_anim and self.param != "EXPORT_MORPH"
            props.import_file = self.filepath
            dir, name = os.path.split(self.filepath)
            type = name[-3:].lower()
            name = name[:-4]

            # store selection
            old_selection = bpy.context.selected_objects
            old_active = bpy.context.active_object

            if type == "fbx":

                # don't bring anything else with a morph export
                if self.param == "EXPORT_MORPH" and props.import_has_key:
                    bpy.ops.object.select_all(action='DESELECT')

                for p in props.import_objects:
                    if p.object is not None:
                        if p.object.type == "ARMATURE":
                            select_all_child_objects(p.object)
                        else:
                            p.object.select_set(True)

                bpy.ops.export_scene.fbx(filepath=self.filepath,
                        use_selection = True,
                        bake_anim = export_anim,
                        add_leaf_bones=False)

                if props.import_has_key:
                    try:
                        key_dir, key_file = os.path.split(props.import_key_file)
                        old_name, key_type = os.path.splitext(key_file)
                        new_key_path = os.path.join(dir, name + key_type)
                        if not utils.is_same_path(new_key_path, props.import_key_file):
                            shutil.copyfile(props.import_key_file, new_key_path)
                    except Exception as e:
                        utils.log_error("Unable to copy keyfile: " + props.import_key_file + " to: " + new_key_path, e)

            else:

                # don't bring anything else with a morph export
                if self.param == "EXPORT_MORPH" and props.import_has_key:
                    bpy.ops.object.select_all(action='DESELECT')

                # select all the imported objects
                for p in props.import_objects:
                    if p.object is not None and p.object.type == "MESH":
                        p.object.select_set(True)

                if self.param == "EXPORT_MORPH":
                    bpy.ops.export_scene.obj(filepath=self.filepath,
                            use_selection = True,
                            global_scale = 100,
                            use_materials = False,
                            keep_vertex_order = True,
                            use_vertex_groups = True)
                else:
                    bpy.ops.export_scene.obj(filepath=self.filepath,
                            use_selection = True,
                            global_scale = 100,
                            use_materials = True,
                            keep_vertex_order = True,
                            use_vertex_groups = True)

                if props.import_has_key:
                    try:
                        key_dir, key_file = os.path.split(props.import_key_file)
                        old_name, key_type = os.path.splitext(key_file)
                        new_key_path = os.path.join(dir, name + key_type)
                        if not utils.is_same_path(new_key_path, props.import_key_file):
                            shutil.copyfile(props.import_key_file, new_key_path)
                    except Exception as e:
                        utils.log_error("Unable to copy keyfile: " + props.import_key_file + "\n    to: " + new_key_path, e)

            # restore selection
            #bpy.ops.object.select_all(action='DESELECT')
            #for obj in old_selection:
            #    obj.select_set(True)
            #bpy.context.view_layer.objects.active = old_active

        elif self.param == "EXPORT_ACCESSORY":
            props.import_file = self.filepath
            dir, name = os.path.split(self.filepath)
            type = name[-3:].lower()
            name = name[:-4]

            # store selection
            old_selection = bpy.context.selected_objects
            old_active = bpy.context.active_object

            if props.import_type == "fbx":
                bpy.ops.export_scene.fbx(filepath=self.filepath,
                        use_selection = True,
                        bake_anim = False,
                        add_leaf_bones=False)
            else:
                bpy.ops.export_scene.obj(filepath=self.filepath,
                        global_scale=100,
                        use_selection=True,
                        use_animation=False,
                        use_materials=True,
                        use_mesh_modifiers=True,
                        keep_vertex_order=True)

            # restore selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in old_selection:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = old_active


        return {"FINISHED"}

    def invoke(self, context, event):
        self.get_type()

        if self.filename_ext == ".none":
            return {"FINISHED"}

        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if not blend_filepath:
                if self.param == "EXPORT_ACCESSORY":
                    blend_filepath = "accessory"
                else:
                    blend_filepath = "untitled"
            else:
                blend_filepath = os.path.splitext(blend_filepath)[0]
            self.filepath = blend_filepath + self.filename_ext

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def get_type(self):
        props = bpy.context.scene.CC3ImportProps
        # export accessories as the same file type as imported
        if self.param == "EXPORT_ACCESSORY":
            self.filename_ext = "." + props.import_type
        # exporting for pipeline depends on what was imported...
        elif self.param == "EXPORT_MORPH" or self.param == "EXPORT":
            self.filename_ext = "." + props.import_type
        else:
            self.filename_ext = ".none"

    def check(self, context):
        change_ext = False
        filepath = self.filepath
        if os.path.basename(filepath):
            base, ext = os.path.splitext(filepath)
            if ext != self.filename_ext:
                filepath = bpy.path.ensure_ext(base, self.filename_ext)
            else:
                filepath = bpy.path.ensure_ext(filepath, self.filename_ext)
            if filepath != self.filepath:
                self.filepath = filepath
                change_ext = True
        return change_ext

    @classmethod
    def description(cls, context, properties):

        if properties.param == "EXPORT_MORPH":
            return "Export full character to import back into CC3"
        elif properties.param == "EXPORT_ACCESSORY":
            return "Export selected object(s) for import into CC3 as accessories"
        return ""

def add_target(name, location):
    bpy.ops.object.empty_add(type="PLAIN_AXES", radius = 0.1,
        location = location)
    target = bpy.context.active_object
    target.name = utils.unique_name(name, True)
    return target

def set_contact_shadow(light, distance, thickness):
    light.data.use_contact_shadow = True
    light.data.contact_shadow_distance = distance
    light.data.contact_shadow_thickness = thickness

def track_to(obj, target):
    constraint = obj.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"

def add_spot_light(name, location, rotation, energy, blend, size, distance, radius):
    bpy.ops.object.light_add(type="SPOT",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = utils.unique_name(name, True)
    light.data.energy = energy
    light.data.shadow_soft_size = radius
    light.data.spot_blend = blend
    light.data.spot_size = size
    light.data.use_custom_distance = True
    light.data.cutoff_distance = distance
    return light

def add_area_light(name, location, rotation, energy, size):
    bpy.ops.object.light_add(type="AREA",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = utils.unique_name(name, True)
    light.data.shape = "DISK"
    light.data.size = size
    light.data.energy = energy
    return light

def add_point_light(name, location, rotation, energy, size):
    bpy.ops.object.light_add(type="POINT",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = utils.unique_name(name, True)
    light.data.shadow_soft_size = size
    light.data.energy = energy
    return light

def remove_all_lights(inc_camera = False):
    for obj in bpy.data.objects:
        if vars.NODE_PREFIX in obj.name:
            if obj.type == "LIGHT":
                bpy.data.objects.remove(obj)

            elif inc_camera and obj.type == "EMPTY" and "CameraTarget" in obj.name:
                bpy.data.objects.remove(obj)

            elif obj.type == "EMPTY" and \
                ("KeyTarget" in obj.name or \
                "FillTarget" in obj.name or \
                "BackTarget" in obj.name):
                bpy.data.objects.remove(obj)

            elif inc_camera and obj.type == "CAMERA":
                bpy.data.objects.remove(obj)
        else:
            if obj.type == "LIGHT":
                obj.hide_set(True)

            elif inc_camera and obj.type == "EMPTY" and "CameraTarget" in obj.name:
                obj.hide_set(True)

            elif obj.type == "EMPTY" and \
                ("KeyTarget" in obj.name or \
                "FillTarget" in obj.name or \
                "BackTarget" in obj.name):
                obj.hide_set(True)

            elif inc_camera and obj.type == "CAMERA":
                obj.hide_set(True)


def restore_hidden_camera():
    # enable the first hidden camera
    for obj in bpy.data.objects:
        if obj.type == "CAMERA" and not obj.visible_get():
            obj.hide_set(False)
            bpy.context.scene.camera = obj
            return


def camera_setup(camera_loc, target_loc):
    # find an active camera
    camera = None
    target = None
    for obj in bpy.data.objects:
        if camera is None and vars.NODE_PREFIX in obj.name and obj.type == "CAMERA" and obj.visible_get():
            camera = obj
            camera.location = camera_loc
        if target is None and vars.NODE_PREFIX in obj.name and obj.type == "EMPTY" and obj.visible_get() and "CameraTarget" in obj.name:
            target = obj
            target.location = target_loc
    if camera is None:
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=camera_loc)
        camera = bpy.context.active_object
        camera.name = utils.unique_name("Camera", True)
    if target is None:
        target = add_target("CameraTarget", target_loc)

    track_to(camera, target)
    camera.data.lens = 80
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = target
    camera.data.dof.aperture_fstop = 2.8
    camera.data.dof.aperture_blades = 5
    camera.data.dof.aperture_rotation = 0
    camera.data.dof.aperture_ratio = 1
    camera.data.display_size = 0.2
    camera.data.show_limits = True

    camera_auto_target(camera, target)

    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 2560
    bpy.context.scene.render.resolution_percentage = 100

    return camera, target

def camera_auto_target(camera, target):
    props = bpy.context.scene.CC3ImportProps
    arm = None
    for p in props.import_objects:
        obj = p.object
        if (obj.type == "ARMATURE"):
            arm = obj
            break

    if arm is not None:
        left_eye = find_pose_bone("CC_Base_L_Eye", "L_Eye")
        right_eye = find_pose_bone("CC_Base_R_Eye", "R_Eye")
        head = find_pose_bone("CC_Base_FacialBone", "FacialBone")

        if left_eye is None or right_eye is None or head is None:
            return

        head_location = arm.matrix_world @ head.head
        head_dir = (arm.matrix_world @ head.vector).normalized()
        target_location = arm.matrix_world @ ((left_eye.head + right_eye.head) * 0.5)
        target.location = target_location + head_dir * 0.03
        camera.location = head_location + head_dir * 2

def compositor_setup():
    bpy.context.scene.use_nodes = True
    nodes = bpy.context.scene.node_tree.nodes
    links = bpy.context.scene.node_tree.links
    nodes.clear()
    rlayers_node = nodeutils.make_shader_node(nodes, "CompositorNodeRLayers")
    c_node = nodeutils.make_shader_node(nodes, "CompositorNodeComposite")
    glare_node = nodeutils.make_shader_node(nodes, "CompositorNodeGlare")
    lens_node = nodeutils.make_shader_node(nodes, "CompositorNodeLensdist")
    rlayers_node.location = (-780,260)
    c_node.location = (150,140)
    glare_node.location = (-430,230)
    lens_node.location = (-100,150)
    glare_node.glare_type = 'FOG_GLOW'
    glare_node.quality = 'HIGH'
    glare_node.threshold = 0.85
    lens_node.use_fit = True
    lens_node.inputs["Dispersion"].default_value = 0.025
    nodeutils.link_nodes(links, rlayers_node, "Image", glare_node, "Image")
    nodeutils.link_nodes(links, glare_node, "Image", lens_node, "Image")
    nodeutils.link_nodes(links, lens_node, "Image", c_node, "Image")

def world_setup():
    bpy.context.scene.world.use_nodes = True
    nodes = bpy.context.scene.world.node_tree.nodes
    links = bpy.context.scene.world.node_tree.links
    nodes.clear()
    tc_node = nodeutils.make_shader_node(nodes, "ShaderNodeTexCoord")
    mp_node = nodeutils.make_shader_node(nodes, "ShaderNodeMapping")
    et_node = nodeutils.make_shader_node(nodes, "ShaderNodeTexEnvironment")
    bg_node = nodeutils.make_shader_node(nodes, "ShaderNodeBackground")
    wo_node = nodeutils.make_shader_node(nodes, "ShaderNodeOutputWorld")
    tc_node.location = (-820,350)
    mp_node.location = (-610,370)
    et_node.location = (-300,320)
    bg_node.location = (10,300)
    wo_node.location = (300,300)
    nodeutils.set_node_input(bg_node, "Strength", 0.5)
    nodeutils.link_nodes(links, tc_node, "Generated", mp_node, "Vector")
    nodeutils.link_nodes(links, mp_node, "Vector", et_node, "Vector")
    nodeutils.link_nodes(links, et_node, "Color", bg_node, "Color")
    nodeutils.link_nodes(links, bg_node, "Background", wo_node, "Surface")
    bin_dir, bin_file = os.path.split(bpy.app.binary_path)
    version = bpy.app.version_string[:4]
    hdri_path = os.path.join(bin_dir, version, "datafiles", "studiolights", "world", "forest.exr")
    et_node.image = load_image(hdri_path, "Linear")


def init_character_for_edit(obj):
    #bpy.context.active_object.data.shape_keys.key_blocks['Basis']
    if obj.type == "MESH":
        shape_keys = obj.data.shape_keys
        if shape_keys is not None:
            blocks = shape_keys.key_blocks
            if blocks is not None:
                if len(blocks) > 0:
                    set_shape_key_edit(obj)


def init_shape_key_range(obj):
    #bpy.context.active_object.data.shape_keys.key_blocks['Basis']
    if obj.type == "MESH":
        shape_keys = obj.data.shape_keys
        if shape_keys is not None:
            blocks = shape_keys.key_blocks
            if blocks is not None:
                if len(blocks) > 0:
                    for block in blocks:
                        # expand the range of the shape key slider to include negative values...
                        block.slider_min = -1.0


def set_shape_key_edit(obj):
    try:
        #current_mode = bpy.context.mode
        #if current_mode != "OBJECT":
        #    bpy.ops.object.mode_set(mode="OBJECT")
        #bpy.context.view_layer.objects.active = object
        obj.active_shape_key_index = 0
        obj.show_only_shape_key = True
        obj.use_shape_key_edit_mode = True

    except Exception as e:
        utils.log_error("Unable to set shape key edit mode!", e)


def setup_scene_default(scene_type):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    # store selection and mode
    current_selected = bpy.context.selected_objects
    current_active = bpy.context.active_object
    current_mode = bpy.context.mode
    # go to object mode
    try:
        if current_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        if scene_type == "BLENDER":

            bpy.context.scene.eevee.use_gtao = False
            bpy.context.scene.eevee.gtao_distance = 0.2
            bpy.context.scene.eevee.gtao_factor = 1.0
            bpy.context.scene.eevee.use_bloom = False
            bpy.context.scene.eevee.bloom_threshold = 0.8
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 6.5
            bpy.context.scene.eevee.bloom_intensity = 0.05
            if prefs.refractive_eyes:
                bpy.context.scene.eevee.use_ssr = True
                bpy.context.scene.eevee.use_ssr_refraction = True
            else:
                bpy.context.scene.eevee.use_ssr = False
                bpy.context.scene.eevee.use_ssr_refraction = False
            bpy.context.scene.eevee.bokeh_max_size = 32
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "None"
            bpy.context.scene.view_settings.exposure = 0.0
            bpy.context.scene.view_settings.gamma = 1.0
            bpy.context.scene.cycles.transparent_max_bounces = 12


            remove_all_lights(True)
            restore_hidden_camera()

            key1 = add_point_light("Light",
                    (4.076245307922363, 1.0054539442062378, 5.903861999511719),
                    (0.6503279805183411, 0.055217113345861435, 1.8663908243179321),
                    1000, 0.1)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'forest.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 0
            bpy.context.space_data.shading.studiolight_intensity = 1
            bpy.context.space_data.shading.studiolight_background_alpha = 0
            bpy.context.space_data.shading.studiolight_background_blur = 0
            bpy.context.space_data.clip_start = 0.1

        elif scene_type == "MATCAP":

            remove_all_lights(True)
            restore_hidden_camera()

            bpy.context.space_data.shading.type = 'SOLID'
            bpy.context.space_data.shading.light = 'MATCAP'
            bpy.context.space_data.shading.studio_light = 'basic_1.exr'
            bpy.context.space_data.shading.show_cavity = True

        elif scene_type == "CC3":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 2.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "Medium Contrast"
            bpy.context.scene.view_settings.exposure = 0.5
            bpy.context.scene.view_settings.gamma = 0.5
            bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            restore_hidden_camera()

            key1 = add_spot_light("Key1",
                    (0.71149, -1.49019, 2.04134),
                    (1.2280241250991821, 0.4846124053001404, 0.3449903726577759),
                    100, 0.5, 2.095, 9.7, 0.25)

            key2 = add_spot_light("Key2",
                    (0.63999, -1.3600, 0.1199),
                    (1.8845493793487549, 0.50091552734375, 0.6768553256988525),
                    100, 0.5, 2.095, 9.7, 0.25)

            back = add_spot_light("Back",
                    (0.0, 2.0199, 1.69),
                    (-1.3045594692230225, 0.11467886716127396, 0.03684665635228157),
                    100, 0.5, 1.448, 9.14, 0.25)

            #set_contact_shadow(key1, 0.1, 0.001)
            #set_contact_shadow(key2, 0.1, 0.005)

            bpy.context.space_data.shading.type = 'SOLID'
            bpy.context.space_data.shading.light = 'MATCAP'
            bpy.context.space_data.shading.studio_light = 'basic_1.exr'
            bpy.context.space_data.shading.show_cavity = True
            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'studio.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 0
            bpy.context.space_data.shading.studiolight_intensity = 0.75
            bpy.context.space_data.shading.studiolight_background_alpha = 0
            bpy.context.space_data.shading.studiolight_background_blur = 0
            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "STUDIO":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 2.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "High Contrast"
            bpy.context.scene.view_settings.exposure = 0.5
            bpy.context.scene.view_settings.gamma = 1.0
            bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            restore_hidden_camera()

            key = add_spot_light("Key",
                    (0.3088499903678894, -4.569439888000488, 2.574970006942749),
                    (0.39095374941825867, 1.3875367641448975, -1.1152653694152832),
                    400, 0.75, 0.75, 7.5, 0.4)

            right = add_area_light("Right",
                    (2.067525863647461, 0.8794340491294861, 1.1529420614242554),
                    (3.115412712097168, 1.7226399183273315, 9.79827880859375),
                    50, 2)

            back = add_spot_light("Ear",
                    (0.6740000247955322, 1.906999945640564, 1.6950000524520874),
                    (-0.03316125646233559, 1.3578661680221558, 1.1833332777023315),
                    100, 1, 1.0996, 9.1, 0.5)

            set_contact_shadow(key, 0.1, 0.01)
            set_contact_shadow(right, 0.1, 0.01)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'studio.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 0.0
            bpy.context.space_data.shading.studiolight_intensity = 0.2
            bpy.context.space_data.shading.studiolight_background_alpha = 0.5
            bpy.context.space_data.shading.studiolight_background_blur = 0.5
            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "COURTYARD":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 2.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "Medium High Contrast"
            bpy.context.scene.view_settings.exposure = 0.5
            bpy.context.scene.view_settings.gamma = 0.6
            bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            restore_hidden_camera()

            key = add_area_light("Key",
                    (-1.5078026056289673, -1.0891118049621582, 2.208820104598999),
                    (1.0848181247711182, -0.881056010723114, -0.5597077012062073),
                    40, 2)

            fill = add_area_light("Fill",
                    (2.28589, -1.51410, 1.40742),
                    (1.4248263835906982, 0.9756063222885132, 0.8594209551811218),
                    20, 2)

            back = add_area_light("Back",
                    (0.36789, 0.61511, 2.36201),
                    (-0.7961875796318054, 0.4831638038158417, -0.12343151122331619),
                    20, 1)

            set_contact_shadow(key, 0.1, 0.01)
            set_contact_shadow(fill, 0.1, 0.01)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'courtyard.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 2.00713
            bpy.context.space_data.shading.studiolight_intensity = 0.35
            bpy.context.space_data.shading.studiolight_background_alpha = 0.5
            bpy.context.space_data.shading.studiolight_background_blur = 0.5

            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "TEMPLATE":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.5
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 5.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "Medium High Contrast"
            bpy.context.scene.view_settings.exposure = 0.6
            bpy.context.scene.view_settings.gamma = 0.6
            bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            camera, camera_target = camera_setup((0.1, -0.75, 1.6), (0, 0, 1.5))
            bpy.context.scene.camera = camera

            key = add_area_light("Key",
                    (-1.5078026056289673, -1.0891118049621582, 2.208820104598999),
                    (1.0848181247711182, -0.881056010723114, -0.5597077012062073),
                    40, 1)
            target_key = add_target("KeyTarget", (-0.006276353262364864, -0.004782751202583313, 1.503425121307373))
            track_to(key, target_key)

            fill = add_area_light("Fill",
                    (2.28589, -1.51410, 1.40742),
                    (1.4248263835906982, 0.9756063222885132, 0.8594209551811218),
                    10, 1)
            target_fill = add_target("FillTarget", (0.013503191992640495, 0.005856933072209358, 1.1814184188842773))
            track_to(fill, target_fill)

            back = add_area_light("Back",
                    (0.36789, 0.61511, 2.36201),
                    (-0.7961875796318054, 0.4831638038158417, -0.12343151122331619),
                    40, 0.5)
            target_back = add_target("BackTarget", (0.0032256320118904114, 0.06994983553886414, 1.6254671812057495))
            track_to(back, target_back)

            set_contact_shadow(key, 0.1, 0.01)
            set_contact_shadow(fill, 0.1, 0.01)

            bpy.context.space_data.shading.type = 'RENDERED'
            bpy.context.space_data.shading.use_scene_lights_render = True
            bpy.context.space_data.shading.use_scene_world_render = True

            bpy.context.space_data.clip_start = 0.01

    except Exception as e:
        utils.log_error("Something went wrong adding lights...", e)

    # restore selection
    bpy.ops.object.select_all(action='DESELECT')
    for obj in current_selected:
        try:
            obj.select_set(True)
        except:
            pass
    try:
        bpy.context.view_layer.objects.active = current_active
        if current_mode != "OBJECT":
            bpy.ops.object.mode_set(mode=current_mode)
    except:
        pass

# zoom view to imported character
def zoom_to_character():
    props = bpy.context.scene.CC3ImportProps
    try:
        bpy.ops.object.select_all(action='DESELECT')
        for p in props.import_objects:
            p.object.select_set(True)
        bpy.ops.view3d.view_selected()
    except:
        pass

class CC3Scene(bpy.types.Operator):
    """Scene Tools"""
    bl_idname = "cc3.scene"
    bl_label = "Scene Tools"
    bl_options = {"REGISTER", "UNDO"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):
        if self.param == "RENDER_IMAGE":
            render_image(context)
        elif self.param == "RENDER_ANIMATION":
            render_animation(context)
        elif self.param == "ANIM_RANGE":
            fetch_anim_range(context)
        elif self.param == "PHYSICS_PREP":
            prepare_physics_bake(context)
        else:
            setup_scene_default(self.param)
            if (self.param == "TEMPLATE"):
                compositor_setup()
                world_setup()
                utils.message_box("World nodes and compositor template set up.")
        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "BLENDER":
            return "Restore the render settings and lighting to the Blender defaults"
        elif properties.param == "MATCAP":
            return "Use solid shading with matcap rendering"
        elif properties.param == "CC3":
            return "Use material shading with render settings and lighting to a replica of the default CC3 lighting"
        elif properties.param == "STUDIO":
            return "Use rendered shading with the Studio HDRI and left sided 3 point lighting"
        elif properties.param == "COURTYARD":
            return "Use rendered shading with the Courtyard HDRI and right sided 3 point lighting"
        elif properties.param == "TEMPLATE":
            return "Sets up a rendering template with rendered shading and world lighting. Sets up the Compositor and World nodes with a basic setup and adds tracking lights, a tracking camera and targetting objects"
        elif properties.param == "RENDER_IMAGE":
            return "Renders a single image"
        elif properties.param == "RENDER_ANIMATION":
            return "Renders the current animation range"
        elif properties.param == "ANIM_RANGE":
            return "Sets the animation range to the same range as the Action on the current character"
        elif properties.param == "PHYSICS_PREP":
            return "Sets all the physics bake ranges to the same as the current scene animation range."

        return ""

def context_material(context):
    try:
        return context.object.material_slots[context.object.active_material_index].material
    except:
        return None

def quick_set_fix(param, obj, context, objects_processed):
    props = bpy.context.scene.CC3ImportProps
    ob = context.object

    if obj is not None and obj not in objects_processed:
        if obj.type == "MESH":
            objects_processed.append(obj)

            if props.quick_set_mode == "OBJECT":
                for mat in obj.data.materials:
                    if mat is not None:
                        if param == "OPAQUE" or param == "BLEND" or param == "HASHED":
                            apply_alpha_override(obj, mat, param)
                        elif param == "SINGLE_SIDED":
                            apply_backface_culling(obj, mat, 1)
                        elif param == "DOUBLE_SIDED":
                            apply_backface_culling(obj, mat, 2)

            elif ob is not None and ob.type == "MESH" and ob.active_material_index <= len(ob.data.materials):
                mat = context_material(context)
                if mat is not None:
                    if param == "OPAQUE" or param == "BLEND" or param == "HASHED":
                        apply_alpha_override(obj, mat, param)
                    elif param == "SINGLE_SIDED":
                        apply_backface_culling(obj, mat, 1)
                    elif param == "DOUBLE_SIDED":
                        apply_backface_culling(obj, mat, 2)

        elif obj.type == "ARMATURE":
            for child in obj.children:
                quick_set_fix(param, child, context, objects_processed)


def quick_set_execute(param, context = bpy.context):
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
                begin_paint_weight_map(context)
        elif param == "PHYSICS_DONE_PAINTING":
            end_paint_weight_map()
        elif param == "PHYSICS_SAVE":
            save_dirty_weight_maps(bpy.context.selected_objects)
        elif param == "PHYSICS_DELETE":
            delete_selected_weight_map(context.object, context_material(context))
        elif param == "PHYSICS_SEPARATE":
            separate_physics_materials(context)
        elif param == "PHYSICS_FIX_DEGENERATE":
            if context.object is not None:
                if bpy.context.object.mode != "EDIT" and bpy.context.object.mode != "OBJECT":
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                if bpy.context.object.mode != "EDIT":
                    bpy.ops.object.mode_set(mode = 'EDIT')
                if bpy.context.object.mode == "EDIT":
                    bpy.ops.mesh.select_all(action = 'SELECT')
                    bpy.ops.mesh.dissolve_degenerate()
                bpy.ops.object.mode_set(mode = 'OBJECT')

    elif param == "RESET":
        reset_parameters(context)

    elif param == "RESET_PREFS":
        reset_preferences()

    elif param == "UPDATE_LINKED" or param == "UPDATE_SELECTED":
        update_all_properties(context, param)

    else: # blend modes or single/double sided...
        objects_processed = []
        if props.quick_set_mode == "OBJECT":
            for obj in bpy.context.selected_objects:
                quick_set_fix(param, obj, context, objects_processed)
        else:
            quick_set_fix(param, context.object, context, objects_processed)


def find_pose_bone(*name):
    props = bpy.context.scene.CC3ImportProps

    for p in props.import_objects:
        obj = p.object
        if (obj.type == "ARMATURE"):
            for n in name:
                if n in obj.pose.bones:
                    return obj.pose.bones[n]
    return None


def open_mouth_update(self, context):
    props = bpy.context.scene.CC3ImportProps

    bone = find_pose_bone("CC_Base_JawRoot", "JawRoot")
    if bone is not None:
        constraint = None

        for con in bone.constraints:
            if "iCC3_open_mouth_contraint" in con.name:
                constraint = con

        if props.open_mouth == 0:
            if constraint is not None:
                constraint.influence = props.open_mouth
                bone.constraints.remove(constraint)
        else:
            if constraint is None:
                constraint = bone.constraints.new(type="LIMIT_ROTATION")
                constraint.name = "iCC3_open_mouth_contraint"
                constraint.use_limit_z = True
                constraint.min_z = 0.43633
                constraint.max_z = 0.43633
                constraint.owner_space = "LOCAL"
            constraint.influence = props.open_mouth

def s2lin(x):
    a = 0.055
    if x <= 0.04045:
        y = x * (1.0/12.92)
    else:
        y = pow((x + a)*(1.0/(1 + a)), 2.4)
    return y

def lin2s(x):
    a = 0.055
    if x <= 0.0031308:
        y = x * 12.92
    else:
        y = (1 + a)*pow(x, 1/2.4) - a
    return y

def physics_paint_strength_update(self, context):
    props = bpy.context.scene.CC3ImportProps

    if bpy.context.mode == "PAINT_TEXTURE":
        ups = context.tool_settings.unified_paint_settings
        prop_owner = ups if ups.use_unified_color else context.tool_settings.image_paint.brush
        s = props.physics_paint_strength
        prop_owner.color = (s, s, s)

def weight_strength_update(self, context):
    props = bpy.context.scene.CC3ImportProps

    strength = props.weight_map_strength
    influence = 1 - math.pow(1 - strength, 3)
    edit_mod, mix_mod = modutils.get_material_weight_map_mods(context.object, context_material(context))
    mix_mod.mask_constant = influence


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

        if properties.param == "UPDATE_LINKED":
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

        elif properties.param == "PHYSICS_ADD_CLOTH":
            return "Add Cloth physics to the selected objects."
        elif properties.param == "PHYSICS_REMOVE_CLOTH":
            return "Remove Cloth physics from the selected objects and remove all weight map modifiers and physics vertex groups"
        elif properties.param == "PHYSICS_ADD_COLLISION":
            return "Add Collision physics to the selected objects"
        elif properties.param == "PHYSICS_REMOVE_COLLISION":
            return "Remove Collision physics from the selected objects"
        elif properties.param == "PHYSICS_ADD_WEIGHTMAP":
            return "Add a physics weight map to the material on the current object. " \
                   "If there is no existing weight map, a new blank weight map will be created. " \
                   "Modifiers to generate the physics vertex groups will be added to the object"
        elif properties.param == "PHYSICS_REMOVE_WEIGHTMAP":
            return "Removes the physics weight map, modifiers and physics vertex groups for this material from the object"
        elif properties.param == "PHYSICS_HAIR":
            return "Sets the cloth physics settings for this object to simulate Hair.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_COTTON":
            return "Sets the cloth physics settings for this object to simulate Cotton.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_DENIM":
            return "Sets the cloth physics settings for this object to simulate Denim.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_LEATHER":
            return "Sets the cloth physics settings for this object to simulate Leather.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_RUBBER":
            return "Sets the cloth physics settings for this object to simulate Rubber.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_SILK":
            return "Sets the cloth physics settings for this object to simulate Silk.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_PAINT":
            return "Switches to texture paint mode and begins painting the current materials PhysX weight map"
        elif properties.param == "PHYSICS_DONE_PAINTING":
            return "Ends painting and returns to Object mode"
        elif properties.param == "PHYSICS_SAVE":
            return "Saves all changes to the weight maps to the source texture files\n" \
                   "**Warning: This will overwrite the existing weightmap files if you have altered them!**"
        elif properties.param == "PHYSICS_DELETE":
            return "Removes the weight map, modifiers and physics vertex groups from the objects, " \
                   "and then deletes the weight map texture file.\n" \
                   "**Warning: This will delete any existing weightmap file for this object and material!**"
        elif properties.param == "PHYSICS_SEPARATE":
            return "Separates the object by material and applies physics to the separated objects that have weight maps.\n" \
                   "Note: Some objects with many verteces and materials but only a small amount is cloth simulated " \
                   "may see performance benefits from being separated."
        elif properties.param == "PHYSICS_FIX_DEGENERATE":
            return "Removes degenerate mesh elements from the object.\n" \
                   "Note: Meshes with degenerate elements, loose verteces, orphaned edges, zero length edges etc...\n" \
                   "might not simulate properly. If the mesh misbehaves badly under simulation, try this."

        return ""


def gamma_correct(color):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if prefs.hair_gamma_correct:

        # this is in fact a linear to sRGB color space conversion
        # the hair shader material parameters in CC3 are in linear color space
        # this is an optional way to correct the colours if copying directly from CC3 settings.

        r = color[0]
        g = color[1]
        b = color[2]

        if r < 0: r = 0
        if g < 0: g = 0
        if b < 0: b = 0

        r = max(1.055 * pow(r, 0.416666667) - 0.055, 0)
        g = max(1.055 * pow(g, 0.416666667) - 0.055, 0)
        b = max(1.055 * pow(b, 0.416666667) - 0.055, 0)

        return (r, g, b, 1)

    else:
        return color

def update_all_properties(context, update_mode = None):
    global block_update
    if block_update: return

    props = bpy.context.scene.CC3ImportProps
    utils.start_timer()

    if update_mode is None:
        update_mode = props.update_mode

    if props.setup_mode == "ADVANCED":

        # update all property matrix properties
        for mixer in params.PROP_MATRIX:
            for group in mixer["groups"]:
                for input in group["inputs"]:
                    matrix = [[mixer, group, input]]
                    for cache in props.material_cache:
                        mat = cache.material
                        if mat is not None:
                            update_advanced_material(mat, cache, matrix)

        # update all modifier matrix properties
        for matrix in params.MODIFIER_MATRIX:
            prop_name = matrix[0]
            material_type = matrix[1]
            for p in props.import_objects:
                obj = p.object
                if obj.type == "MESH":
                    for mat in obj.data.materials:
                        cache = get_material_cache(mat)
                        if cache.material_type == material_type:
                            update_object_modifier(obj, cache, prop_name)

        # update all material properies
        mat_prop_names = ["eye_ior", "eye_refraction_depth"]
        for prop_name in mat_prop_names:
            for cache in props.material_cache:
                mat = cache.material
                if mat is not None:
                    update_material_settings(mat, cache, prop_name)


    elif props.setup_mode == "BASIC":

        for cache in props.material_cache:
            mat = cache.material
            if mat is not None:
                update_basic_material(mat, cache, "ALL")

    utils.log_timer("update_all_properties()", "ms")


def update_material_settings(mat, cache, prop_name):
    props = bpy.context.scene.CC3ImportProps
    params = cache.parameters

    if prop_name == "eye_refraction_depth":
        if cache.is_cornea():
            mat.refraction_depth = params.eye_refraction_depth / 1000.0

    if prop_name == "eye_ior":
        if cache.is_cornea() and mat.node_tree:
            nodeutils.set_default_shader_input(mat, "IOR", params.eye_ior)


def update_material(self, context, prop_name, update_mode = None):
    global block_update
    if block_update: return

    props = bpy.context.scene.CC3ImportProps
    active_mat = context_material(context)
    active_cache = get_material_cache(active_mat)
    if not active_mat or not active_cache: return
    linked = get_linked_material_types(active_cache)
    paired = get_paired_material_types(active_cache)
    print(paired)
    if prop_name in params.FORCE_LINKED_PROPS:
        update_mode = "UPDATE_LINKED"
    if active_cache and active_cache.material_type in params.FORCE_LINKED_TYPES:
        update_mode = "UPDATE_LINKED"

    utils.start_timer()

    if update_mode is None:
        update_mode = props.update_mode

    if props.setup_mode == "ADVANCED":

        for cache in props.material_cache:
            mat = cache.material

            if mat:

                if mat == active_mat:
                    update_material_settings(mat, cache, prop_name)

                elif cache.material_type in paired:
                    set_linked_property(prop_name, active_cache, cache)
                    update_material_settings(mat, cache, prop_name)

                elif update_mode == "UPDATE_LINKED":
                    # Update all other linked materials in the imported objects material cache:
                    for linked_type in linked:
                        if cache.material_type == linked_type:
                            set_linked_property(prop_name, active_cache, cache)
                            update_material_settings(mat, cache, prop_name)

    if prop_name in params.PROP_DEPENDANTS:
        deps = params.PROP_DEPENDANTS[prop_name]
        for dep_name in deps:
            update_material(self, context, dep_name, update_mode)

    utils.log_timer("update_material()", "ms")


def get_object_modifier(obj, type, name = ""):
    if obj is not None:
        for mod in obj.modifiers:
            if name == "":
                if mod.type == type:
                    return mod
            else:
                if mod.type == type and mod.name.startswith(vars.NODE_PREFIX) and name in mod.name:
                    return mod
    return None


def update_object_modifier(obj, cache, prop_name):
    props = bpy.context.scene.CC3ImportProps

    for matrix in params.MODIFIER_MATRIX:
        if matrix[0] == prop_name:
            material_type = matrix[1]
            mod_type = matrix[2]
            mod_name = matrix[3]
            code = matrix[4]

            if cache.material_type == material_type:
                mod = get_object_modifier(obj, mod_type, mod_name)
                if mod:
                    parameters = cache.parameters
                    exec(code, None, locals())


def update_modifier(self, context, prop_name, update_mode = None):
    global block_update
    if block_update: return

    props = bpy.context.scene.CC3ImportProps
    active_mat = context_material(context)
    active_cache = get_material_cache(active_mat)
    if not active_mat or not active_cache: return
    linked = get_linked_material_types(active_cache)
    paired = get_paired_material_types(active_cache)
    if prop_name in params.FORCE_LINKED_PROPS:
        update_mode = "UPDATE_LINKED"
    if active_cache and active_cache.material_type in params.FORCE_LINKED_TYPES:
        update_mode = "UPDATE_LINKED"

    utils.start_timer()

    if update_mode is None:
        update_mode = props.update_mode

    if props.setup_mode == "ADVANCED":

        for p in props.import_objects:
            obj = p.object

            if obj.type == "MESH":
                for mat in obj.data.materials:
                    cache = get_material_cache(mat)

                    if mat == active_mat:
                            # Always update the currently active material
                            update_object_modifier(obj, cache, prop_name)

                    elif cache.material_type in paired:
                        # Update paired materials
                        set_linked_property(prop_name, active_cache, cache)
                        update_object_modifier(obj, cache, prop_name)

                    elif update_mode == "UPDATE_LINKED":
                        # Update all other linked materials in the imported objects material cache:
                        for linked_type in linked:
                            if cache.material_type == linked_type:
                                set_linked_property(prop_name, active_cache, cache)
                                update_object_modifier(obj, cache, prop_name)

    if prop_name in params.PROP_DEPENDANTS:
        deps = params.PROP_DEPENDANTS[prop_name]
        for dep_name in deps:
            update_modifier(self, context, dep_name, update_mode)

    utils.log_timer("update_modifier()", "ms")


def update_property(self, context, prop_name, update_mode = None):
    global block_update
    if block_update: return

    props = bpy.context.scene.CC3ImportProps
    active_mat = context_material(context)
    active_cache = get_material_cache(active_mat)
    if not active_mat or not active_cache: return
    linked = get_linked_material_types(active_cache)
    paired = get_paired_material_types(active_cache)
    if prop_name in params.FORCE_LINKED_PROPS:
        update_mode = "UPDATE_LINKED"
    if active_cache and active_cache.material_type in params.FORCE_LINKED_TYPES:
        update_mode = "UPDATE_LINKED"

    utils.start_timer()

    if update_mode is None:
        update_mode = props.update_mode

    if props.setup_mode == "ADVANCED":

        matrix = params.get_prop_matrix(prop_name)

        if len(matrix) > 0:

            for cache in props.material_cache:
                mat = cache.material

                if mat:

                    if mat == active_mat:
                        # Always update the currently active material
                        update_advanced_material(mat, cache, matrix)

                    elif cache.material_type in paired:
                        # Update paired materials
                        set_linked_property(prop_name, active_cache, cache)
                        update_advanced_material(mat, cache, matrix)

                    elif update_mode == "UPDATE_LINKED":
                        # Update all other linked materials in the imported objects material cache:
                        for linked_type in linked:
                            if cache.material_type == linked_type:
                                set_linked_property(prop_name, active_cache, cache)
                                update_advanced_material(mat, cache, matrix)

        # these properties will cause the eye displacement vertex group to change...
        if prop_name in ["eye_iris_depth_radius", "eye_iris_scale", "eye_iris_radius"]:
            # eye_iris_depth_radius has no material node property, but it needs a prop_matric entry so it fires set_linked_property above...
            rebuild_eye_vertex_groups()

    elif props.setup_mode == "BASIC":

        for cache in props.material_cache:
            mat = cache.material

            if mat:

                if mat == active_mat:
                    # Always update the currently active material
                    update_basic_material(mat, cache, prop_name)

                elif cache.material_type in paired:
                    # Update paired materials
                    set_linked_property(prop_name, active_cache, cache)
                    update_basic_material(mat, cache, prop_name)

                elif linked and update_mode == "UPDATE_LINKED":
                    # Update all other linked materials in the imported objects material cache:
                    for linked_type in linked:
                        if cache.material_type == linked_type:
                            set_linked_property(prop_name, active_cache, cache)
                            update_basic_material(mat, cache, prop_name)

    if prop_name in params.PROP_DEPENDANTS:
        deps = params.PROP_DEPENDANTS[prop_name]
        for dep_name in deps:
            update_property(self, context, dep_name, update_mode)

    utils.log_timer("update_property_matrix()", "ms")


def get_linked_material_types(cache):
    if cache:
        for linked in params.LINKED_MATERIALS:
            if cache.material_type in linked:
                return linked
        return [cache.material_type]
    return []


def get_paired_material_types(cache):
    if cache:
        for paired in params.PAIRED_MATERIALS:
            if cache.material_type in paired:
                return paired
    return []


def set_linked_property(prop_name, active_cache, cache):
    global block_update
    block_update = True
    code = ""

    try:
        code = "cache.parameters." + prop_name + " = active_cache.parameters." + prop_name
        exec(code, None, locals())
    except Exception as e:
        utils.log_error("set_linked_property(): Unable to evaluate: " + code, e)

    block_update = False


def update_advanced_material(mat, cache, matrix):
    props = bpy.context.scene.CC3ImportProps
    parameters = cache.parameters
    scope = locals()
    if mat is not None and mat.node_tree is not None and len(matrix) > 0:
        for m in matrix:
            mixer = m[0]
            group = m[1]
            input = m[2]
            nodes = mat.node_tree.nodes

            try:
                if len(input) == 3:
                    prop_eval = input[2]
                else:
                    prop_eval = "parameters." + input[1]

                prop_value = eval(prop_eval, None, scope)

                for node in nodes:
                    if ((mixer["start"] == "" or mixer["start"] in node.name) and
                        (mixer["end"] == "" or mixer["end"] in node.name)):

                        if type(group["name"]) is list:
                            for name in group["name"]:
                                if name in node.name:
                                    nodeutils.set_node_input(node, input[0], prop_value)
                        else:
                            if group["name"] in node.name:
                                nodeutils.set_node_input(node, input[0], prop_value)
            except Exception as e:
                utils.log_error("update_advanced_materials(): Unable to evaluate or set: " + prop_eval, e)


def update_basic_material(mat, cache, prop):
    props = bpy.context.scene.CC3ImportProps
    parameters = cache.parameters
    scope = locals()

    if mat is not None and mat.node_tree is not None:

        nodes = mat.node_tree.nodes
        for node in nodes:

            for prop_info in params.BASIC_PROPS:

                prop_name = prop_info[3]
                prop_node = prop_info[2]
                if prop_node == "":
                    prop_node = prop_name

                if prop_node in node.name and (prop == "ALL" or prop == prop_name):
                    prop_dir = prop_info[0]
                    prop_socket = prop_info[1]

                    try:
                        if len(prop_info) == 5:
                            prop_eval = prop_info[4]
                        else:
                            prop_eval = "parameters." + prop_name

                        prop_value = eval(prop_eval, None, scope)

                        if prop_dir == "IN":
                            nodeutils.set_node_input(node, prop_socket, prop_value)
                        elif prop_dir == "OUT":
                            nodeutils.set_node_output(node, prop_socket, prop_value)
                    except Exception as e:
                        utils.log_error("update_basic_materials(): Unable to evaluate or set: " + prop_eval, e)


def reset_material_parameters(cache):
    props = bpy.context.scene.CC3ImportProps
    params = cache.parameters

    params.skin_ao = 1.0
    params.skin_blend = 0.0
    params.skin_normal_blend = 0.0
    params.skin_roughness = 0.1
    params.skin_roughness_power = 0.8
    params.skin_specular = 0.4
    params.skin_basic_specular = 0.4
    params.skin_basic_roughness = 0.15
    params.skin_sss_radius = 1.5
    params.skin_sss_falloff = (1.0, 0.112, 0.072, 1.0)
    params.skin_head_micronormal = 0.5
    params.skin_body_micronormal = 0.8
    params.skin_arm_micronormal = 1.0
    params.skin_leg_micronormal = 1.0
    params.skin_head_tiling = 25
    params.skin_body_tiling = 20
    params.skin_arm_tiling = 20
    params.skin_leg_tiling = 20
    params.skin_mouth_ao = 2.5
    params.skin_nostril_ao = 2.5
    params.skin_lips_ao = 2.5

    params.eye_ao = 0.2
    params.eye_blend = 0.0
    params.eye_specular = 0.8
    params.eye_sclera_roughness = 0.2
    params.eye_iris_roughness = 0.0
    params.eye_iris_scale = 1.0
    params.eye_sclera_scale = 1.0
    params.eye_iris_radius = 0.14
    params.eye_iris_hardness = 0.85
    params.eye_limbus_radius = 0.125
    params.eye_limbus_hardness = 0.80
    params.eye_limbus_color = (0.2, 0.2, 0.2, 1.0)
    params.eye_sss_radius = 1.0
    params.eye_sss_falloff = (1.0, 1.0, 1.0, 1.0)
    params.eye_sclera_normal = 0.9
    params.eye_sclera_tiling = 2.0
    params.eye_basic_roughness = 0.05
    params.eye_basic_normal = 0.1
    params.eye_shadow_radius = 0.3
    params.eye_shadow_hardness = 0.5
    params.eye_shadow_color = (1.0, 0.497, 0.445, 1.0)
    params.eye_occlusion = 0.5
    params.eye_occlusion_color = (0, 0, 0, 1.0)
    params.eye_occlusion_hardness = 0.5
    params.eye_sclera_brightness = 0.75
    params.eye_iris_brightness = 1.0
    params.eye_sclera_hue = 0.5
    params.eye_iris_hue = 0.5
    params.eye_sclera_saturation = 1.0
    params.eye_iris_saturation = 1.0
    params.eye_basic_brightness = 0.9
    params.eye_iris_depth = 0.25
    params.eye_pupil_scale = 1.0
    params.eye_refraction_depth = 1.0
    params.eye_ior = 1.42
    params.eye_blood_vessel_height = 0.5
    params.eye_iris_bump_height = 1

    params.eye_occlusion_strength = 0.4
    params.eye_occlusion_power = 1.5
    params.eye_occlusion_top_min = 0.215
    params.eye_occlusion_top_max = 1.0
    params.eye_occlusion_top_curve = 0.7
    params.eye_occlusion_bottom_min = 0.04
    params.eye_occlusion_bottom_max = 0.335
    params.eye_occlusion_bottom_curve = 2.0
    params.eye_occlusion_inner_min = 0.25
    params.eye_occlusion_inner_max = 0.625
    params.eye_occlusion_outer_min = 0.16
    params.eye_occlusion_outer_max = 0.6
    params.eye_occlusion_2nd_strength = 0.9
    params.eye_occlusion_2nd_top_min = 0.12
    params.eye_occlusion_2nd_top_max = 1.0
    params.eye_occlusion_tear_duct_position = 0.8
    params.eye_occlusion_tear_duct_width = 0.5
    params.eye_occlusion_inner = 0
    params.eye_occlusion_outer = 0
    params.eye_occlusion_top = 0
    params.eye_occlusion_bottom = 0
    params.eye_occlusion_displace = 0.02

    params.tearline_alpha = 0.05
    params.tearline_roughness = 0.15
    params.tearline_displace = 0.1
    params.tearline_inner = 0.0


    params.teeth_ao = 1.0
    params.teeth_gums_brightness = 0.9
    params.teeth_teeth_brightness = 0.7
    params.teeth_gums_desaturation = 0.0
    params.teeth_teeth_desaturation = 0.1
    params.teeth_front = 1.0
    params.teeth_rear = 0.0
    params.teeth_specular = 0.25
    params.teeth_roughness = 0.4
    params.teeth_gums_sss_scatter = 1.0
    params.teeth_teeth_sss_scatter = 0.5
    params.teeth_sss_radius = 1.0
    params.teeth_sss_falloff = (0.381, 0.198, 0.13, 1.0)
    params.teeth_micronormal = 0.3
    params.teeth_tiling = 10

    params.tongue_ao = 1.0
    params.tongue_brightness = 1.0
    params.tongue_desaturation = 0.05
    params.tongue_front = 1.0
    params.tongue_rear = 0.0
    params.tongue_specular = 0.259
    params.tongue_roughness = 1.0
    params.tongue_sss_scatter = 1.0
    params.tongue_sss_radius = 1.0
    params.tongue_sss_falloff = (1,1,1, 1.0)
    params.tongue_micronormal = 0.5
    params.tongue_tiling = 4

    params.nails_ao = 1.0
    params.nails_specular = 0.4
    params.nails_roughness = 0.0
    params.nails_sss_radius = 1.5
    params.nails_sss_falloff = (1.0, 0.112, 0.072, 1.0)
    params.nails_micronormal = 1.0
    params.nails_tiling = 42

    params.hair_ao = 1.0
    params.hair_blend = 0.0
    params.hair_specular = 0.5
    params.hair_roughness = 0.0
    params.hair_scalp_specular = 0.0
    params.hair_scalp_roughness = 0.0
    params.hair_eyelash_specular = 0.0
    params.hair_eyelash_roughness = 0.0
    params.hair_sss_radius = 1.0
    params.hair_sss_falloff = (1.0, 1.0, 1.0, 1.0)
    params.hair_bump = 1

    params.hair_brightness = 0.0
    params.hair_contrast = 0.0
    params.hair_hue = 0.5
    params.hair_saturation = 1.0
    params.hair_aniso_strength = 0
    params.hair_aniso_strength_cycles = 0
    params.hair_aniso_color = (0.050000, 0.038907, 0.032500, 1.000000)
    params.hair_vertex_color_strength = 0.0
    params.hair_base_color_map_strength = 1.0
    params.hair_depth_strength = 1.0
    params.hair_diffuse_strength = 1.0
    params.hair_global_strength = 0.0
    params.hair_root_color = (0.144129, 0.072272, 0.046665, 1.0)
    params.hair_end_color = (0.332452, 0.184475, 0.122139, 1.0)
    params.hair_root_strength = 1.0
    params.hair_end_strength = 1.0
    params.hair_invert_strand = 0.0
    params.hair_a_start = 0.1
    params.hair_a_mid = 0.2
    params.hair_a_end = 0.3
    params.hair_a_strength = 0
    params.hair_a_overlap = 1.0
    params.hair_a_color = (0.502886, 0.323143, 0.205079, 1.0)
    params.hair_b_start = 0.1
    params.hair_b_mid = 0.2
    params.hair_b_end = 0.3
    params.hair_b_strength = 0.0
    params.hair_b_overlap = 1.0
    params.hair_b_color = (1.000000, 1.000000, 1.000000, 1.000000)
    params.hair_fake_bump_midpoint = 0.5
    params.hair_opacity = 1
    params.hair_scalp_opacity = 1
    params.hair_eyelash_opacity = 1

    params.default_ao = 1.0
    params.default_blend = 0.0
    params.default_roughness = 0.0
    params.default_normal_blend = 0.0
    params.default_sss_radius = 1.0
    params.default_sss_falloff = (1.0, 1.0, 1.0, 1.0)

    params.default_micronormal = 0.5
    params.default_tiling = 10
    params.default_bump = 5
    params.default_opacity = 1


def reset_parameters(context = bpy.context):
    global block_update

    props = bpy.context.scene.CC3ImportProps

    block_update = True

    active_mat = context_material(context)
    active_cache = get_material_cache(active_mat)
    linked = get_linked_material_types(active_cache)
    paired = get_paired_material_types(active_cache)

    for mat_cache in props.material_cache:

        if mat_cache.material == active_mat:
            reset_material_parameters(mat_cache)

        elif mat_cache.material_type in paired:
            reset_material_parameters(mat_cache)

        elif props.update_mode == "UPDATE_LINKED":
            for linked_type in linked:
                if mat_cache.material_type == linked_type:
                    reset_material_parameters(mat_cache)

    block_update = False

    update_all_properties(context)

    return


def detect_bone(armature, *name):
    if (armature.type == "ARMATURE"):
        for n in name:
            if n in armature.pose.bones:
                return True
    return False


def detect_generation(objects):

    for arm in objects:
        if arm.type == "ARMATURE":
            if find_pose_bone(arm, "RootNode_0_", "RL_BoneRoot"):
                return "ACTORCORE"
            elif find_pose_bone(arm, "CC_Base_L_Pinky3"):
                return "G3"
            elif find_pose_bone(arm, "pinky_03_l"):
                return "GAMEBASE"
            elif find_pose_bone(arm, "CC_Base_L_Finger42"):
                return "G1"

    for obj in objects:
        if (obj.type == "MESH"):
            name = obj.name.lower()
            if "cc_game_body" in name or "cc_game_tongue" in name:
                if utils.object_has_material(obj, "character"):
                    return "ACTORCORE"
                else:
                    return "GAMEBASE"
            elif "cc_base_body" in name:
                if utils.object_has_material(obj, "ga_skin_body"):
                    return "GAMEBASE"
                elif utils.object_has_material(obj, "std_skin_body"):
                    return "G3"
                elif utils.object_has_material(obj, "skin_body"):
                    return "G1"
                elif utils.object_has_material(obj, "character"):
                    return "ACTORCORE"

    return "UNKNOWN"


class CC3ObjectPointer(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)



class CC3MaterialParameters(bpy.types.PropertyGroup):
    # Basic
    skin_basic_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_basic_specular"))
    skin_basic_roughness: bpy.props.FloatProperty(default=0.15, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_basic_roughness"))
    eye_basic_roughness: bpy.props.FloatProperty(default=0.05, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_basic_roughness"))
    eye_basic_normal: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_basic_normal"))
    eye_basic_brightness: bpy.props.FloatProperty(default=0.9, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_basic_brightness"))


    # Skin
    skin_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_ao"))
    skin_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_blend"))
    skin_mouth_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=lambda s,c: update_property(s,c,"skin_mouth_ao"))
    skin_nostril_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=lambda s,c: update_property(s,c,"skin_nostril_ao"))
    skin_lips_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=lambda s,c: update_property(s,c,"skin_lips_ao"))
    skin_normal_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_normal_blend"))
    skin_roughness_power: bpy.props.FloatProperty(default=0.8, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_roughness_power"))
    skin_roughness: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_roughness"))
    skin_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_specular"))
    skin_sss_radius: bpy.props.FloatProperty(default=1.5, min=0.1, max=5, update=lambda s,c: update_property(s,c,"skin_sss_radius"))
    skin_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 0.112, 0.072, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"skin_sss_falloff"))
    skin_head_micronormal: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_head_micronormal"))
    skin_body_micronormal: bpy.props.FloatProperty(default=0.8, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_body_micronormal"))
    skin_arm_micronormal: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_arm_micronormal"))
    skin_leg_micronormal: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_leg_micronormal"))
    skin_head_tiling: bpy.props.FloatProperty(default=25, min=0, max=50, update=lambda s,c: update_property(s,c,"skin_head_tiling"))
    skin_body_tiling: bpy.props.FloatProperty(default=20, min=0, max=50, update=lambda s,c: update_property(s,c,"skin_body_tiling"))
    skin_arm_tiling: bpy.props.FloatProperty(default=20, min=0, max=50, update=lambda s,c: update_property(s,c,"skin_arm_tiling"))
    skin_leg_tiling: bpy.props.FloatProperty(default=20, min=0, max=50, update=lambda s,c: update_property(s,c,"skin_leg_tiling"))


    # Eye
    eye_ao: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_ao"))
    eye_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_blend"))
    eye_shadow_radius: bpy.props.FloatProperty(default=0.3, min=0, max=0.5, update=lambda s,c: update_property(s,c,"eye_shadow_radius"))
    eye_shadow_hardness: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_shadow_hardness"))
    eye_shadow_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 0.497, 0.445, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_shadow_color"))
    eye_sclera_brightness: bpy.props.FloatProperty(default=0.75, min=0, max=5, update=lambda s,c: update_property(s,c,"eye_sclera_brightness"))
    eye_iris_brightness: bpy.props.FloatProperty(default=1.0, min=0, max=5, update=lambda s,c: update_property(s,c,"eye_iris_brightness"))
    eye_sclera_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_sclera_hue"))
    eye_iris_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_iris_hue"))
    eye_sclera_saturation: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_sclera_saturation"))
    eye_iris_saturation: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_iris_saturation"))
    eye_specular: bpy.props.FloatProperty(default=0.8, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_specular"))
    eye_sclera_roughness: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_sclera_roughness"))
    eye_iris_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_iris_roughness"))
    eye_iris_scale: bpy.props.FloatProperty(default=1.0, min=0.65, max=2.0, update=lambda s,c: update_property(s,c,"eye_iris_scale"))
    eye_iris_radius: bpy.props.FloatProperty(default=0.14, min=0.1, max=0.15, update=lambda s,c: update_property(s,c,"eye_iris_radius"))
    eye_iris_hardness: bpy.props.FloatProperty(default=0.85, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_iris_hardness"))
    eye_sclera_scale: bpy.props.FloatProperty(default=1.0, min=0.5, max=1.5, update=lambda s,c: update_property(s,c,"eye_sclera_scale"))
    eye_limbus_radius: bpy.props.FloatProperty(default=0.125, min=0.1, max=0.15, update=lambda s,c: update_property(s,c,"eye_limbus_radius"))
    eye_limbus_hardness: bpy.props.FloatProperty(default=0.8, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_limbus_hardness"))
    eye_limbus_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.2, 0.2, 0.2, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_limbus_color"))
    eye_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=lambda s,c: update_property(s,c,"eye_sss_radius"))
    eye_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_sss_falloff"))
    eye_sclera_normal: bpy.props.FloatProperty(default=0.9, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_sclera_normal"))
    eye_sclera_tiling: bpy.props.FloatProperty(default=2.0, min=0, max=10, update=lambda s,c: update_property(s,c,"eye_sclera_tiling"))
    eye_refraction_depth: bpy.props.FloatProperty(default=1, min=0, max=5, update=lambda s,c: update_material(s,c,"eye_refraction_depth"))
    eye_ior: bpy.props.FloatProperty(default=1.42, min=1.01, max=2.5, update=lambda s,c: update_material(s,c,"eye_ior"))
    eye_blood_vessel_height: bpy.props.FloatProperty(default=0.5, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_blood_vessel_height"))
    eye_iris_bump_height: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_iris_bump_height"))

    eye_iris_depth: bpy.props.FloatProperty(default=0.25, min=0.0, max=1.0, update=lambda s,c: update_modifier(s,c,"eye_iris_depth"))
    eye_iris_depth_radius: bpy.props.FloatProperty(default=0.8, min=0.0, max=1.0, update=lambda s,c: update_property(s,c,"eye_iris_depth_radius"))
    eye_pupil_scale: bpy.props.FloatProperty(default=1.0, min=0.65, max=2.0, update=lambda s,c: update_modifier(s,c,"eye_pupil_scale"))

    # Eye Occlusion Basic
    eye_occlusion: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion"))
    eye_occlusion_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.057805, 0.006512, 0.003347, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_occlusion_color"))
    eye_occlusion_hardness: bpy.props.FloatProperty(default=0.5, min=0.5, max=1.5, update=lambda s,c: update_property(s,c,"eye_occlusion_hardness"))

    # Eye Occlusion Advanced
    eye_occlusion_strength: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_occlusion_strength"))
    eye_occlusion_power: bpy.props.FloatProperty(default=1.5, min=0.1, max=4, update=lambda s,c: update_property(s,c,"eye_occlusion_power"))
    eye_occlusion_top_min: bpy.props.FloatProperty(default=0.215, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_top_min"))
    eye_occlusion_top_max: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_top_max"))
    eye_occlusion_top_curve: bpy.props.FloatProperty(default=0.7, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_occlusion_top_curve"))
    eye_occlusion_bottom_min: bpy.props.FloatProperty(default=0.04, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_bottom_min"))
    eye_occlusion_bottom_max: bpy.props.FloatProperty(default=0.335, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_bottom_max"))
    eye_occlusion_bottom_curve: bpy.props.FloatProperty(default=2.0, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_occlusion_bottom_curve"))
    eye_occlusion_inner_min: bpy.props.FloatProperty(default=0.25, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_inner_min"))
    eye_occlusion_inner_max: bpy.props.FloatProperty(default=0.625, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_inner_max"))
    eye_occlusion_outer_min: bpy.props.FloatProperty(default=0.16, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_outer_min"))
    eye_occlusion_outer_max: bpy.props.FloatProperty(default=0.6, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_outer_max"))
    eye_occlusion_2nd_strength: bpy.props.FloatProperty(default=0.9, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_occlusion_2nd_strength"))
    eye_occlusion_2nd_top_min: bpy.props.FloatProperty(default=0.12, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_2nd_top_min"))
    eye_occlusion_2nd_top_max: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_2nd_top_max"))
    eye_occlusion_tear_duct_position: bpy.props.FloatProperty(default=0.8, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_tear_duct_position"))
    eye_occlusion_tear_duct_width: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_tear_duct_width"))
    eye_occlusion_inner: bpy.props.FloatProperty(default=0, min=-0.1, max=0.1, update=lambda s,c: update_modifier(s,c,"eye_occlusion_inner"))
    eye_occlusion_outer: bpy.props.FloatProperty(default=0, min=-0.1, max=0.1, update=lambda s,c: update_modifier(s,c,"eye_occlusion_outer"))
    eye_occlusion_top: bpy.props.FloatProperty(default=0, min=-0.1, max=0.1, update=lambda s,c: update_modifier(s,c,"eye_occlusion_top"))
    eye_occlusion_bottom: bpy.props.FloatProperty(default=0, min=-0.1, max=0.1, update=lambda s,c: update_modifier(s,c,"eye_occlusion_bottom"))
    eye_occlusion_displace: bpy.props.FloatProperty(default=0.02, min=-0.1, max=0.1, update=lambda s,c: update_modifier(s,c,"eye_occlusion_displace"))

    # Tearline
    tearline_alpha: bpy.props.FloatProperty(default=0.05, min=0, max=0.2, update=lambda s,c: update_property(s,c,"tearline_alpha"))
    tearline_roughness: bpy.props.FloatProperty(default=0.15, min=0, max=0.5, update=lambda s,c: update_property(s,c,"tearline_roughness"))
    tearline_inner: bpy.props.FloatProperty(default=0, min=-0.2, max=0.2, update=lambda s,c: update_modifier(s,c,"tearline_inner"))
    tearline_displace: bpy.props.FloatProperty(default=0.1, min=-0.2, max=0.2, update=lambda s,c: update_modifier(s,c,"tearline_displace"))

    # Teeth
    teeth_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_ao"))
    teeth_gums_brightness: bpy.props.FloatProperty(default=0.9, min=0, max=2, update=lambda s,c: update_property(s,c,"teeth_gums_brightness"))
    teeth_teeth_brightness: bpy.props.FloatProperty(default=0.7, min=0, max=2, update=lambda s,c: update_property(s,c,"teeth_teeth_brightness"))
    teeth_gums_desaturation: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_gums_desaturation"))
    teeth_teeth_desaturation: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_teeth_desaturation"))
    teeth_front: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_front"))
    teeth_rear: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_rear"))
    teeth_specular: bpy.props.FloatProperty(default=0.25, min=0, max=2, update=lambda s,c: update_property(s,c,"teeth_specular"))
    teeth_roughness: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=lambda s,c: update_property(s,c,"teeth_roughness"))
    teeth_gums_sss_scatter: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"teeth_gums_sss_scatter"))
    teeth_teeth_sss_scatter: bpy.props.FloatProperty(default=0.5, min=0, max=2, update=lambda s,c: update_property(s,c,"teeth_teeth_sss_scatter"))
    teeth_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=lambda s,c: update_property(s,c,"teeth_sss_radius"))
    teeth_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(0.381, 0.198, 0.13, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"teeth_sss_falloff"))
    teeth_micronormal: bpy.props.FloatProperty(default=0.3, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_micronormal"))
    teeth_tiling: bpy.props.FloatProperty(default=10, min=0, max=50, update=lambda s,c: update_property(s,c,"teeth_tiling"))


    # Tongue
    tongue_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_ao"))
    tongue_brightness: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"tongue_brightness"))
    tongue_desaturation: bpy.props.FloatProperty(default=0.05, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_desaturation"))
    tongue_front: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_front"))
    tongue_rear: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_rear"))
    tongue_specular: bpy.props.FloatProperty(default=0.259, min=0, max=2, update=lambda s,c: update_property(s,c,"tongue_specular"))
    tongue_roughness: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"tongue_roughness"))
    tongue_sss_scatter: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"tongue_sss_scatter"))
    tongue_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=lambda s,c: update_property(s,c,"tongue_sss_radius"))
    tongue_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(1, 1, 1, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"tongue_sss_falloff"))
    tongue_micronormal: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_micronormal"))
    tongue_tiling: bpy.props.FloatProperty(default=4, min=0, max=50, update=lambda s,c: update_property(s,c,"tongue_tiling"))


    # Nails
    nails_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"nails_ao"))
    nails_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=lambda s,c: update_property(s,c,"nails_specular"))
    nails_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"nails_roughness"))
    nails_sss_radius: bpy.props.FloatProperty(default=1.5, min=0.1, max=3, update=lambda s,c: update_property(s,c,"nails_sss_radius"))
    nails_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(1.0, 0.112, 0.072, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"nails_sss_falloff"))
    nails_micronormal: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"nails_micronormal"))
    nails_tiling: bpy.props.FloatProperty(default=42, min=0, max=50, update=lambda s,c: update_property(s,c,"nails_tiling"))


    # Hair
    hair_specular: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_specular"))
    hair_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_roughness"))
    hair_scalp_specular: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_scalp_specular"))
    hair_scalp_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_scalp_roughness"))
    hair_eyelash_specular: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_eyelash_specular"))
    hair_eyelash_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_eyelash_roughness"))
    hair_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_ao"))
    hair_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_blend"))
    hair_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_specular"))
    hair_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=lambda s,c: update_property(s,c,"hair_sss_radius"))
    hair_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_sss_falloff"))
    hair_bump: bpy.props.FloatProperty(default=1, min=0, max=10, update=lambda s,c: update_property(s,c,"hair_bump"))
    hair_opacity: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_opacity"))
    hair_scalp_opacity: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_scalp_opacity"))
    hair_eyelash_opacity: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_eyelash_opacity"))
    hair_brightness: bpy.props.FloatProperty(default=0, min=-2, max=2, update=lambda s,c: update_property(s,c,"hair_brightness"))
    hair_contrast: bpy.props.FloatProperty(default=0, min=-2, max=2, update=lambda s,c: update_property(s,c,"hair_contrast"))
    hair_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_hue"))
    hair_saturation: bpy.props.FloatProperty(default=1, min=0, max=4, update=lambda s,c: update_property(s,c,"hair_saturation"))
    hair_diffuse_strength: bpy.props.FloatProperty(default=1.0, min=0, max=4, update=lambda s,c: update_property(s,c,"hair_diffuse_strength"))
    hair_aniso_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.050000, 0.038907, 0.032500, 1.000000), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_aniso_color"))
    hair_aniso_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_aniso_strength"))
    hair_aniso_strength_cycles: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_aniso_strength_cycles"))
    hair_vertex_color_strength: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_vertex_color_strength"))
    hair_base_color_map_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_base_color_map_strength"))
    hair_depth_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_depth_strength"))
    hair_global_strength: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_global_strength"))
    hair_root_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.144129, 0.072272, 0.046665, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_root_color"))
    hair_end_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.332452, 0.184475, 0.122139, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_end_color"))
    hair_root_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_root_strength"))
    hair_end_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_end_strength"))
    hair_invert_strand: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_invert_strand"))
    hair_a_start: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_a_start"))
    hair_a_mid: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_a_mid"))
    hair_a_end: bpy.props.FloatProperty(default=0.3, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_a_end"))
    hair_a_strength: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_a_strength"))
    hair_a_overlap: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_a_overlap"))
    hair_a_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.502886, 0.323143, 0.205079, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_a_color"))
    hair_b_start: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_b_start"))
    hair_b_mid: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_b_mid"))
    hair_b_end: bpy.props.FloatProperty(default=0.3, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_b_end"))
    hair_b_strength: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_b_strength"))
    hair_b_overlap: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_b_overlap"))
    hair_b_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.000000, 1.000000, 1.000000, 1.000000), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_b_color"))
    hair_fake_bump_midpoint: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_fake_bump_midpoint"))


    # Default
    default_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_ao"))
    default_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_blend"))
    default_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_roughness"))
    default_normal_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_normal_blend"))
    default_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=3, update=lambda s,c: update_property(s,c,"default_sss_radius"))
    default_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"default_sss_falloff"))
    default_micronormal: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"default_micronormal"))
    default_tiling: bpy.props.FloatProperty(default=10, min=0, max=100, update=lambda s,c: update_property(s,c,"default_tiling"))
    default_bump: bpy.props.FloatProperty(default=5, min=0, max=10, update=lambda s,c: update_property(s,c,"default_bump"))
    default_opacity: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_opacity"))


class CC3MaterialCache(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(type=bpy.types.Material)
    material_type: bpy.props.EnumProperty(items=vars.MATERIAL_TYPES, default="DEFAULT")
    parameters: bpy.props.PointerProperty(type=CC3MaterialParameters)
    smart_hair: bpy.props.BoolProperty(default=False)
    compat: bpy.props.PointerProperty(type=bpy.types.Material)
    dir: bpy.props.StringProperty(default="")
    diffuse: bpy.props.PointerProperty(type=bpy.types.Image)
    normal: bpy.props.PointerProperty(type=bpy.types.Image)
    bump: bpy.props.PointerProperty(type=bpy.types.Image)
    alpha: bpy.props.PointerProperty(type=bpy.types.Image)
    specular: bpy.props.PointerProperty(type=bpy.types.Image)
    temp_weight_map: bpy.props.PointerProperty(type=bpy.types.Image)
    alpha_is_diffuse: bpy.props.BoolProperty(default=False)
    alpha_mode: bpy.props.StringProperty(default="NONE") # NONE, BLEND, HASHED, OPAQUE
    culling_sides: bpy.props.IntProperty(default=0) # 0 - default, 1 - single sided, 2 - double sided
    cloth_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON

    def is_skin(self):
        return (self.material_type == "SKIN_HEAD"
                or self.material_type == "SKIN_BODY"
                or self.material_type == "SKIN_ARM"
                or self.material_type == "SKIN_LEG")

    def is_head(self):
        return self.material_type == "SKIN_HEAD"

    def is_body(self):
        return self.material_type == "SKIN_BODY"

    def is_arm(self):
        return self.material_type == "SKIN_ARM"

    def is_leg(self):
        return self.material_type == "SKIN_LEG"

    def is_teeth(self):
        return (self.material_type == "TEETH_UPPER"
                or self.material_type == "TEETH_LOWER")

    def is_tongue(self):
        return self.material_type == "TONGUE"

    def is_hair(self):
        return self.material_type == "HAIR"

    def is_scalp(self):
        return self.material_type == "SCALP"

    def is_eyelash(self):
        return self.material_type == "EYELASH"

    def is_nails(self):
        return self.material_type == "NAILS"

    def is_eye(self, side = "ANY"):
        if side == "RIGHT":
            return self.material_type == "EYE_RIGHT"
        elif side == "LEFT":
            return self.material_type == "EYE_LEFT"
        else:
            return (self.material_type == "EYE_RIGHT"
                    or self.material_type == "EYE_LEFT")

    def is_cornea(self, side = "ANY"):
        if side == "RIGHT":
            return self.material_type == "CORNEA_RIGHT"
        elif side == "LEFT":
            return self.material_type == "CORNEA_LEFT"
        else:
            return (self.material_type == "CORNEA_RIGHT"
                    or self.material_type == "CORNEA_LEFT")

    def is_eye_occlusion(self):
        return (self.material_type == "OCCLUSION_RIGHT"
                or self.material_type == "OCCLUSION_LEFT")

    def is_tearline(self):
        return (self.material_type == "TEARLINE_RIGHT"
                or self.material_type == "TEARLINE_LEFT")


class CC3ObjectCache(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    object_type: bpy.props.EnumProperty(items=vars.OBJECT_TYPES, default="DEFAULT")
    collision_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON
    cloth_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON
    cloth_settings: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, HAIR, COTTON, DENIM, LEATHER, RUBBER, SILK

    def is_body(self):
        return self.object_type == "BODY"

    def is_teeth(self):
        return self.object_type == "TEETH"

    def is_tongue(self):
        return self.object_type == "TONGUE"

    def is_hair(self):
        return self.object_type == "HAIR"

    def is_eye(self):
        return self.object_type == "EYE"

    def is_eye_occlusion(self):
        return self.object_type == "OCCLUSION"

    def is_tearline(self):
        return self.object_type == "TEARLINE"


class CC3ImportProps(bpy.types.PropertyGroup):

    node_id: bpy.props.IntProperty(default=1000)

    setup_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic","Build basic PBR materials."),
                        ("ADVANCED","Advanced","Build advanced materials with blend maps, subsurface, and micro normals, specular and roughness control and includes layered eye, teeth and tongue materials.")
                    ], default="ADVANCED")

    build_mode: bpy.props.EnumProperty(items=[
                        ("IMPORTED","All Imported","Build materials for all the imported objects."),
                        ("SELECTED","Only Selected","Build materials only for the selected objects.")
                    ], default="IMPORTED")

    blend_mode: bpy.props.EnumProperty(items=[
                        ("BLEND","Alpha Blend","Setup any non opaque materials as basic Alpha Blend"),
                        ("HASHED","Alpha Hashed","Setup non opaque materials as alpha hashed (Resolves Z sorting issues, but may need more samples)")
                    ], default="BLEND")

    update_mode: bpy.props.EnumProperty(items=[
                        ("UPDATE_LINKED","Linked","Update the shader parameters for all materials of the same type in all the objects from the last import"),
                        ("UPDATE_SELECTED","Selected","Update the shader parameters only in the selected object and material")
                    ], default="UPDATE_LINKED")

    open_mouth: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=open_mouth_update)
    physics_paint_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=physics_paint_strength_update)
    weight_map_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=weight_strength_update)
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
    import_has_key: bpy.props.BoolProperty(default=False)
    import_key_file: bpy.props.StringProperty(default="")

    paint_object: bpy.props.PointerProperty(type=bpy.types.Object)
    paint_material: bpy.props.PointerProperty(type=bpy.types.Material)
    paint_image: bpy.props.PointerProperty(type=bpy.types.Image)
    paint_store_render: bpy.props.StringProperty(default="")

    quick_set_mode: bpy.props.EnumProperty(items=[
                        ("OBJECT","Object","Set the alpha blend mode and backface culling to all materials on the selected object(s)"),
                        ("MATERIAL","Material","Set the alpha blend mode and backface culling only to the selected material on the active object"),
                    ], default="MATERIAL")

    lighting_mode: bpy.props.EnumProperty(items=[
                        ("OFF","No Lighting","No automatic lighting and render settings."),
                        ("ON","Lighting","Automatically sets lighting and render settings, depending on use."),
                    ], default="OFF")
    physics_mode: bpy.props.EnumProperty(items=[
                        ("OFF","No Physics","No generated physics."),
                        ("ON","Physics","Automatically generates physics vertex groups and settings."),
                    ], default="OFF")

    stage1: bpy.props.BoolProperty(default=True)
    stage1_details: bpy.props.BoolProperty(default=False)
    stage4: bpy.props.BoolProperty(default=True)

    skin_toggle: bpy.props.BoolProperty(default=True)
    eye_toggle: bpy.props.BoolProperty(default=True)
    teeth_toggle: bpy.props.BoolProperty(default=True)
    tongue_toggle: bpy.props.BoolProperty(default=True)
    nails_toggle: bpy.props.BoolProperty(default=True)
    hair_toggle: bpy.props.BoolProperty(default=True)
    default_toggle: bpy.props.BoolProperty(default=True)

    generation: bpy.props.StringProperty(default="None")


def fake_drop_down(row, label, prop_name, prop_bool_value):
    props = bpy.context.scene.CC3ImportProps
    if prop_bool_value:
        row.prop(props, prop_name, icon="TRIA_DOWN", icon_only=True, emboss=False)
    else:
        row.prop(props, prop_name, icon="TRIA_RIGHT", icon_only=True, emboss=False)
    row.label(text=label)
    return prop_bool_value


class CC3ToolsMaterialSettingsPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Material_Settings_Panel"
    bl_label = "Build Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        mesh_in_selection = False
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                mesh_in_selection = True
                break

        box = layout.box()
        #op = box.operator("cc3.importer", icon="IMPORT", text="Import Character")
        #op.param ="IMPORT"
        # import details
        if props.import_file != "" or len(props.import_objects) > 0:
            if fake_drop_down(box.row(), "Import Details", "stage1_details", props.stage1_details):
                box.label(text="Name: " + props.import_name)
                box.label(text="Type: " + props.import_type.upper())
                if props.import_has_key:
                    box.label(text="Key File: Yes")
                else:
                    box.label(text="Key File: No")
                if props.import_file != "":
                    box.prop(props, "import_file", text="")
                if len(props.import_objects) > 0:
                    for p in props.import_objects:
                        if p.object is not None:
                            box.prop(p, "object", text="")
        else:
            box.label(text="No Character")

        # Build Settings
        #layout.box().label(text="Build Options", icon="OPTIONS")


        obj = context.object
        mat = context_material(context)
        is_import_object = False
        if obj is not None and obj.type == "MESH":
            for p in props.import_objects:
                if p.object == obj:
                    is_import_object = True
                    break

        obj_cache = mat_cache = None
        mat_type = "NONE"
        obj_type = "NONE"
        if is_import_object:
            if obj is not None:
                obj_cache = get_object_cache(obj, True)
                obj_type = obj_cache.object_type
            if mat is not None:
                mat_cache = get_material_cache(mat, True)
                mat_type = mat_cache.material_type

        if props.import_file == "":
            layout.box().label(text="Build Materials", icon="MOD_BUILD")
        else:
            layout.box().label(text="Rebuild Materials", icon="MOD_BUILD")
        layout.prop(props, "setup_mode", expand=True)
        layout.prop(props, "blend_mode", expand=True)
        layout.prop(props, "build_mode", expand=True)

        # Prefs:
        box = layout.box()
        split = box.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text="Prefs:")
        col_2.prop(prefs, "new_hair_shader")
        col_1.prop(prefs, "refractive_eyes")
        #col_1.prop(prefs, "fake_hair_anisotropy", text="Eevee Anisotropy")
        col_2.prop(prefs, "fake_hair_bump")

        # Build Button
        box = layout.box()
        box.scale_y = 2
        if props.import_file == "":
            box.enabled = False
        if props.setup_mode == "ADVANCED":
            op = box.operator("cc3.importer", icon="SHADING_TEXTURE", text="Rebuild Advanced Materials")
        else:
            op = box.operator("cc3.importer", icon="NODE_MATERIAL", text="Rebuild Basic Materials")
        op.param ="BUILD"

        # Material Setup
        layout.box().label(text="Material Setup", icon="MATERIAL")
        column = layout.column()
        if not mesh_in_selection:
            column.enabled = False
        if obj is not None:
            column.template_list("MATERIAL_UL_weightedmatslots", "", obj, "material_slots", obj, "active_material_index", rows=1)
        split = column.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()

        if is_import_object:
            if obj is not None:
                obj_cache = get_object_cache(obj, True)
                if obj_cache is not None:
                    col_1.label(text="Object Type")
                    col_2.prop(obj_cache, "object_type", text = "")
            if mat is not None:
                mat_cache = get_material_cache(mat, True)
                if mat_cache is not None:
                    col_1.label(text="Material Type")
                    col_2.prop(mat_cache, "material_type", text = "")

        col_1.label(text="Set By:")
        col_1.prop(props, "quick_set_mode", expand=True)
        op = col_2.operator("cc3.quickset", icon="SHADING_SOLID", text="Opaque")
        op.param = "OPAQUE"
        op = col_2.operator("cc3.quickset", icon="SHADING_WIRE", text="Blend")
        op.param = "BLEND"
        op = col_2.operator("cc3.quickset", icon="SHADING_RENDERED", text="Hashed")
        op.param = "HASHED"
        col_1.separator()
        col_2.separator()
        op = col_1.operator("cc3.quickset", icon="NORMALS_FACE", text="Single Sided")
        op.param = "SINGLE_SIDED"
        op = col_2.operator("cc3.quickset", icon="XRAY", text="Double Sided")
        op.param = "DOUBLE_SIDED"


class CC3ToolsParametersPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Parameters_Panel"
    bl_label = "Material Parameters"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        obj = context.object
        mat = context_material(context)
        obj_cache = get_object_cache(obj, True)
        mat_cache = get_material_cache(mat, True)
        mat_type = "NONE"
        obj_type = "NONE"
        params = None
        if obj_cache is not None:
            obj_type = obj_cache.object_type
        if mat_cache is not None:
            mat_type = mat_cache.material_type
            params = mat_cache.parameters
        is_import_object = False
        is_import_material = mat_cache is not None
        if obj is not None and obj.type == "MESH":
            for p in props.import_objects:
                if p.object == obj:
                    is_import_object = True
                    break

        if not is_import_object and not is_import_material:
            layout.enabled = False

        # Parameters
        if params and fake_drop_down(layout.box().row(),
                "Adjust Parameters",
                "stage4",
                props.stage4):

            # material selector
            #column = layout.column()
            #obj_cache = mat_cache = None
            #mat_type = "NONE"
            #if obj is not None:
            #    column.template_list("MATERIAL_UL_weightedmatslots", "", obj, "material_slots", obj, "active_material_index", rows=1)

            column = layout.column()
            if props.import_name == "":
                column.enabled = False

            row = column.row()
            row.prop(props, "update_mode", expand=True)

            linked = props.update_mode == "UPDATE_LINKED"

            #column.separator()
            #split = column.split(factor=0.5)
            #col_1 = split.column()
            #col_2 = split.column()
            #if props.update_mode == "UPDATE_LINKED":
            #    col_1.label(text="Update Linked")
            #else:
            #    col_1.label(text="Update Selected")
            #op = col_2.operator("cc3.quickset", icon="FILE_REFRESH", text="Update")
            #op.param = props.update_mode

            if props.setup_mode == "ADVANCED":

                # Skin Settings
                if "SKIN" in mat_type:
                    column.separator()
                    if fake_drop_down(column.row(),
                            "Skin Parameters",
                            "skin_toggle",
                            props.skin_toggle):

                        column.box().label(text= "Base Colour", icon="COLOR")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Skin AO")
                        col_2.prop(params, "skin_ao", text="", slider=True)
                        if linked or mat_cache.is_head():
                            col_1.label(text="Mouth AO")
                            col_2.prop(params, "skin_mouth_ao", text="", slider=True)
                            col_1.label(text="Nostril AO")
                            col_2.prop(params, "skin_nostril_ao", text="", slider=True)
                            col_1.label(text="Lips AO")
                            col_2.prop(params, "skin_lips_ao", text="", slider=True)
                            col_1.label(text="Skin Color Blend")
                            col_2.prop(params, "skin_blend", text="", slider=True)

                        column.box().label(text= "Surface", icon="SURFACE_DATA")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Skin Specular")
                        col_2.prop(params, "skin_specular", text="", slider=True)
                        col_1.label(text="Roughness Power")
                        col_2.prop(params, "skin_roughness_power", text="", slider=True)
                        col_1.label(text="Roughness Remap")
                        col_2.prop(params, "skin_roughness", text="", slider=True)

                        column.box().label(text= "Sub-surface", icon="SURFACE_NSURFACE")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Skin SSS Radius")
                        col_2.prop(params, "skin_sss_radius", text="", slider=True)
                        col_1.label(text="Skin SSS Faloff")
                        col_2.prop(params, "skin_sss_falloff", text="")

                        if linked or mat_cache.is_head():
                            column.box().label(text= "Normals", icon="NORMALS_FACE")
                            split = column.split(factor=0.5)
                            col_1 = split.column()
                            col_2 = split.column()
                            col_1.label(text="Skin Normal Blend")
                            col_2.prop(params, "skin_normal_blend", text="", slider=True)

                        column.box().label(text= "Micro-normals", icon="MOD_NORMALEDIT")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        if linked or mat_cache.is_head():
                            col_1.label(text="Head Micro Normal")
                            col_2.prop(params, "skin_head_micronormal", text="", slider=True)
                        if linked or mat_cache.is_body():
                            col_1.label(text="Body Micro Normal")
                            col_2.prop(params, "skin_body_micronormal", text="", slider=True)
                        if linked or mat_cache.is_arm():
                            col_1.label(text="Arm Micro Normal")
                            col_2.prop(params, "skin_arm_micronormal", text="", slider=True)
                        if linked or mat_cache.is_leg():
                            col_1.label(text="Leg Micro Normal")
                            col_2.prop(params, "skin_leg_micronormal", text="", slider=True)
                        if linked or mat_cache.is_head():
                            col_1.label(text="Head MNormal Tiling")
                            col_2.prop(params, "skin_head_tiling", text="", slider=True)
                        if linked or mat_cache.is_body():
                            col_1.label(text="Body MNormal Tiling")
                            col_2.prop(params, "skin_body_tiling", text="", slider=True)
                        if linked or mat_cache.is_arm():
                            col_1.label(text="Arm MNormal Tiling")
                            col_2.prop(params, "skin_arm_tiling", text="", slider=True)
                        if linked or mat_cache.is_leg():
                            col_1.label(text="Leg MNormal Tiling")
                            col_2.prop(params, "skin_leg_tiling", text="", slider=True)


                # Eye settings
                elif mat_cache.is_eye() or mat_cache.is_cornea() or mat_cache.is_tearline() or mat_cache.is_eye_occlusion():
                    column.separator()
                    if fake_drop_down(column.row(),
                            "Eye Parameters",
                            "eye_toggle",
                            props.eye_toggle):
                        if linked or (mat_cache.is_eye() or mat_cache.is_cornea()):
                            column.box().label(text= "Base Color", icon="COLOR")
                            split = column.split(factor=0.5)
                            col_1 = split.column()
                            col_2 = split.column()
                            col_1.label(text="Eye AO")
                            col_2.prop(params, "eye_ao", text="", slider=True)
                            col_1.label(text="Eye Color Blend")
                            col_2.prop(params, "eye_blend", text="", slider=True)

                            col_1.separator()
                            col_2.separator()

                            col_1.label(text="Sclera Hue")
                            col_2.prop(params, "eye_sclera_hue", text="", slider=True)
                            col_1.label(text="Sclera Saturation")
                            col_2.prop(params, "eye_sclera_saturation", text="", slider=True)
                            col_1.label(text="Sclera Brightness")
                            col_2.prop(params, "eye_sclera_brightness", text="", slider=True)
                            col_1.label(text="Sclera Scale")
                            col_2.prop(params, "eye_sclera_scale", text="", slider=True)

                            col_1.separator()
                            col_2.separator()

                            col_1.label(text="Iris Hue")
                            col_2.prop(params, "eye_iris_hue", text="", slider=True)
                            col_1.label(text="Iris Saturation")
                            col_2.prop(params, "eye_iris_saturation", text="", slider=True)
                            col_1.label(text="Iris Brightness")
                            col_2.prop(params, "eye_iris_brightness", text="", slider=True)
                            col_1.label(text="Iris Scale")
                            col_2.prop(params, "eye_iris_scale", text="", slider=True)

                            col_1.separator()
                            col_2.separator()

                            col_1.label(text="Iris Mask Radius")
                            col_2.prop(params, "eye_iris_radius", text="", slider=True)
                            col_1.label(text="Iris Mask Hardness")
                            col_2.prop(params, "eye_iris_hardness", text="", slider=True)

                            if prefs.refractive_eyes:
                                col_1.separator()
                                col_2.separator()
                                col_1.label(text="Limbus Radius")
                                col_2.prop(params, "eye_limbus_radius", text="", slider=True)
                                col_1.label(text="Limbus Hardness")
                                col_2.prop(params, "eye_limbus_hardness", text="", slider=True)
                                col_1.label(text="Limbus Color")
                                col_2.prop(params, "eye_limbus_color", text="")

                            column.box().label(text= "Corner Shadow", icon="SHADING_RENDERED")
                            split = column.split(factor=0.5)
                            col_1 = split.column()
                            col_2 = split.column()
                            col_1.label(text="Shadow Radius")
                            col_2.prop(params, "eye_shadow_radius", text="", slider=True)
                            col_1.label(text="Shadow Hardness")
                            col_2.prop(params, "eye_shadow_hardness", text="", slider=True)
                            col_1.label(text="Shadow Color")
                            col_2.prop(params, "eye_shadow_color", text="")

                            column.box().label(text= "Surface", icon="SURFACE_DATA")
                            split = column.split(factor=0.5)
                            col_1 = split.column()
                            col_2 = split.column()
                            col_1.label(text="Eye Specular")
                            col_2.prop(params, "eye_specular", text="", slider=True)
                            col_1.label(text="Iris Roughness")
                            col_2.prop(params, "eye_iris_roughness", text="", slider=True)
                            col_1.label(text="Sclera Roughness")
                            col_2.prop(params, "eye_sclera_roughness", text="", slider=True)

                            if prefs.refractive_eyes:
                                column.box().label(text= "Depth & Refraction", icon="MOD_THICKNESS")
                                split = column.split(factor=0.5)
                                col_1 = split.column()
                                col_2 = split.column()
                                col_1.label(text="Iris Depth")
                                col_2.prop(params, "eye_iris_depth", text="", slider=True)
                                col_1.label(text="Iris Depth Radius")
                                col_2.prop(params, "eye_iris_depth_radius", text="", slider=True)
                                col_1.label(text="Pupil Scale")
                                col_2.prop(params, "eye_pupil_scale", text="", slider=True)
                                col_1.label(text="Eye IOR")
                                col_2.prop(params, "eye_ior", text="", slider=True)
                                col_1.label(text="Refraction Depth")
                                col_2.prop(params, "eye_refraction_depth", text="", slider=True)

                            if not prefs.refractive_eyes or bpy.context.scene.render.engine == "CYCLES":
                                column.box().label(text= "Sub-surface", icon="SURFACE_NSURFACE")
                                split = column.split(factor=0.5)
                                col_1 = split.column()
                                col_2 = split.column()
                                col_1.label(text="SSS Radius (cm)")
                                col_2.prop(params, "eye_sss_radius", text="", slider=True)
                                col_1.label(text="SSS Faloff")
                                col_2.prop(params, "eye_sss_falloff", text="")

                            column.box().label(text= "Normals", icon="NORMALS_FACE")
                            split = column.split(factor=0.5)
                            col_1 = split.column()
                            col_2 = split.column()
                            col_1.label(text="Sclera Normal Flatten")
                            col_2.prop(params, "eye_sclera_normal", text="", slider=True)
                            col_1.label(text="Sclera Normal Tiling")
                            col_2.prop(params, "eye_sclera_tiling", text="", slider=True)

                            if prefs.refractive_eyes:
                                col_1.label(text="Blood Vessel Height")
                                col_2.prop(params, "eye_blood_vessel_height", text="", slider=True)
                                col_1.label(text="Iris Bump Height")
                                col_2.prop(params, "eye_iris_bump_height", text="", slider=True)

                        if linked or mat_cache.is_eye_occlusion():
                            column.box().label(text= "Occlusion", icon="PROP_CON")
                            split = column.split(factor=0.5)
                            col_1 = split.column()
                            col_2 = split.column()

                            if (prefs.use_advanced_eye_occlusion):

                                col_1.label(text="Color")
                                col_2.prop(params, "eye_occlusion_color", text="", slider=True)
                                col_1.label(text="Power")
                                col_2.prop(params, "eye_occlusion_power", text="", slider=True)

                                col_1.separator()
                                col_2.separator()

                                col_1.label(text="Strength")
                                col_2.prop(params, "eye_occlusion_strength", text="", slider=True)
                                col_1.label(text="Top Min")
                                col_2.prop(params, "eye_occlusion_top_min", text="", slider=True)
                                col_1.label(text="Top Max")
                                col_2.prop(params, "eye_occlusion_top_max", text="", slider=True)
                                col_1.label(text="Top Curve")
                                col_2.prop(params, "eye_occlusion_top_curve", text="", slider=True)
                                col_1.label(text="Bottom Min")
                                col_2.prop(params, "eye_occlusion_bottom_min", text="", slider=True)
                                col_1.label(text="Bottom Max")
                                col_2.prop(params, "eye_occlusion_bottom_max", text="", slider=True)
                                col_1.label(text="Bottom Curve")
                                col_2.prop(params, "eye_occlusion_bottom_curve", text="", slider=True)
                                col_1.label(text="Inner Min")
                                col_2.prop(params, "eye_occlusion_inner_min", text="", slider=True)
                                col_1.label(text="Inner Max")
                                col_2.prop(params, "eye_occlusion_inner_max", text="", slider=True)
                                col_1.label(text="Outer Min")
                                col_2.prop(params, "eye_occlusion_outer_min", text="", slider=True)
                                col_1.label(text="Outer Max")
                                col_2.prop(params, "eye_occlusion_outer_max", text="", slider=True)

                                col_1.separator()
                                col_2.separator()

                                col_1.label(text="Strength Secondary")
                                col_2.prop(params, "eye_occlusion_2nd_strength", text="", slider=True)
                                col_1.label(text="2nd Top Min")
                                col_2.prop(params, "eye_occlusion_2nd_top_min", text="", slider=True)
                                col_1.label(text="2nd Top Max")
                                col_2.prop(params, "eye_occlusion_2nd_top_max", text="", slider=True)

                                col_1.separator()
                                col_2.separator()

                                col_1.label(text="Tear Duct Position")
                                col_2.prop(params, "eye_occlusion_tear_duct_position", text="", slider=True)
                                col_1.label(text="Tear Duct Width")
                                col_2.prop(params, "eye_occlusion_tear_duct_width", text="", slider=True)

                                col_1.separator()
                                col_2.separator()

                                col_1.label(text="Displace")
                                col_2.prop(params, "eye_occlusion_displace", text="", slider=True)
                                col_1.label(text="Inner")
                                col_2.prop(params, "eye_occlusion_inner", text="", slider=True)
                                col_1.label(text="Outer")
                                col_2.prop(params, "eye_occlusion_outer", text="", slider=True)
                                col_1.label(text="Top")
                                col_2.prop(params, "eye_occlusion_top", text="", slider=True)
                                col_1.label(text="Bottom")
                                col_2.prop(params, "eye_occlusion_bottom", text="", slider=True)
                            else:
                                col_1.label(text="Occlusion Strength")
                                col_2.prop(params, "eye_occlusion", text="", slider=True)
                                col_1.label(text="Occlusion Color")
                                col_2.prop(params, "eye_occlusion_color", text="", slider=True)
                                col_1.label(text="Occlusion Hardness")
                                col_2.prop(params, "eye_occlusion_hardness", text="", slider=True)

                        if linked or mat_cache.is_tearline():
                            column.box().label(text= "Tearline", icon="MATFLUID")
                            split = column.split(factor=0.5)
                            col_1 = split.column()
                            col_2 = split.column()
                            col_1.label(text="Tearline Alpha")
                            col_2.prop(params, "tearline_alpha", text="", slider=True)
                            col_1.label(text="Tearline Roughness")
                            col_2.prop(params, "tearline_roughness", text="", slider=True)
                            col_1.label(text="Displace")
                            col_2.prop(params, "tearline_displace", text="", slider=True)
                            col_1.label(text="Inner")
                            col_2.prop(params, "tearline_inner", text="", slider=True)


                # Teeth settings
                elif mat_cache.is_teeth():
                    column.separator()
                    if fake_drop_down(column.row(),
                            "Teeth Parameters",
                            "teeth_toggle",
                            props.teeth_toggle):
                        column.box().label(text= "Base Color", icon="COLOR")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Teeth AO")
                        col_2.prop(params, "teeth_ao", text="", slider=True)
                        col_1.label(text="Gums Brightness")
                        col_2.prop(params, "teeth_gums_brightness", text="", slider=True)
                        col_1.label(text="Gums Desaturation")
                        col_2.prop(params, "teeth_gums_desaturation", text="", slider=True)
                        col_1.label(text="Teeth Brightness")
                        col_2.prop(params, "teeth_teeth_brightness", text="", slider=True)
                        col_1.label(text="Teeth Desaturation")
                        col_2.prop(params, "teeth_teeth_desaturation", text="", slider=True)
                        col_1.label(text="Front AO")
                        col_2.prop(params, "teeth_front", text="", slider=True)
                        col_1.label(text="Rear AO")
                        col_2.prop(params, "teeth_rear", text="", slider=True)

                        column.box().label(text= "Surface", icon="SURFACE_DATA")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Teeth Specular")
                        col_2.prop(params, "teeth_specular", text="", slider=True)
                        col_1.label(text="Teeth Roughness")
                        col_2.prop(params, "teeth_roughness", text="", slider=True)

                        column.box().label(text= "Sub-surface", icon="SURFACE_NSURFACE")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Gums SSS Scatter")
                        col_2.prop(params, "teeth_gums_sss_scatter", text="", slider=True)
                        col_1.label(text="Teeth SSS Scatter")
                        col_2.prop(params, "teeth_teeth_sss_scatter", text="", slider=True)
                        col_1.label(text="SSS Radius (cm)")
                        col_2.prop(params, "teeth_sss_radius", text="", slider=True)
                        col_1.label(text="SSS Falloff")
                        col_2.prop(params, "teeth_sss_falloff", text="", slider=True)

                        column.box().label(text= "Micro-normals", icon="MOD_NORMALEDIT")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Micro Normal")
                        col_2.prop(params, "teeth_micronormal", text="", slider=True)
                        col_1.label(text="Micro Normal Tiling")
                        col_2.prop(params, "teeth_tiling", text="", slider=True)

                # Tongue settings
                elif mat_cache.is_tongue():
                    column.separator()
                    if fake_drop_down(column.row(),
                            "Tongue Parameters",
                            "tongue_toggle",
                            props.tongue_toggle):
                        column.box().label(text= "Base Color", icon="COLOR")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Tongue AO")
                        col_2.prop(params, "tongue_ao", text="", slider=True)
                        col_1.label(text="Tongue Brightness")
                        col_2.prop(params, "tongue_brightness", text="", slider=True)
                        col_1.label(text="Tongue Desaturation")
                        col_2.prop(params, "tongue_desaturation", text="", slider=True)
                        col_1.label(text="Front AO")
                        col_2.prop(params, "tongue_front", text="", slider=True)
                        col_1.label(text="Rear AO")
                        col_2.prop(params, "tongue_rear", text="", slider=True)

                        column.box().label(text= "Surface", icon="SURFACE_DATA")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Tongue Specular")
                        col_2.prop(params, "tongue_specular", text="", slider=True)
                        col_1.label(text="Tongue Roughness")
                        col_2.prop(params, "tongue_roughness", text="", slider=True)

                        column.box().label(text= "Sub-surface", icon="SURFACE_NSURFACE")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="SSS Scatter")
                        col_2.prop(params, "tongue_sss_scatter", text="", slider=True)
                        col_1.label(text="SSS Radius (cm)")
                        col_2.prop(params, "tongue_sss_radius", text="", slider=True)
                        col_1.label(text="SSS Falloff")
                        col_2.prop(params, "tongue_sss_falloff", text="", slider=True)

                        column.box().label(text= "Micro-normals", icon="MOD_NORMALEDIT")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Micro Normal")
                        col_2.prop(params, "tongue_micronormal", text="", slider=True)
                        col_1.label(text="Micro Normal Tiling")
                        col_2.prop(params, "tongue_tiling", text="", slider=True)

                # Nails settings
                elif mat_cache.is_nails():
                    column.separator()
                    if fake_drop_down(column.row(),
                            "Nails Parameters",
                            "nails_toggle",
                            props.nails_toggle):
                        column.box().label(text= "Base Color", icon="COLOR")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Nails AO")
                        col_2.prop(params, "nails_ao", text="", slider=True)

                        column.box().label(text= "Surface", icon="SURFACE_DATA")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Nails Specular")
                        col_2.prop(params, "nails_specular", text="", slider=True)
                        col_1.label(text="Nails Roughness")
                        col_2.prop(params, "nails_roughness", text="", slider=True)

                        column.box().label(text= "Sub-surface", icon="SURFACE_NSURFACE")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="SSS Radius (cm)")
                        col_2.prop(params, "nails_sss_radius", text="", slider=True)
                        col_1.label(text="SSS Falloff")
                        col_2.prop(params, "nails_sss_falloff", text="", slider=True)

                        column.box().label(text= "Micro-normals", icon="MOD_NORMALEDIT")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Micro Normal")
                        col_2.prop(params, "nails_micronormal", text="", slider=True)
                        col_1.label(text="Micro Normal Tiling")
                        col_2.prop(params, "nails_tiling", text="", slider=True)

                # Hair settings
                elif mat_cache.is_hair() or mat_cache.is_scalp() or mat_cache.is_eyelash():
                    column.separator()
                    if fake_drop_down(column.row(),
                            "Hair Parameters",
                            "hair_toggle",
                            props.hair_toggle):
                        column.box().label(text= "Base Color", icon="COLOR")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Hair AO")
                        col_2.prop(params, "hair_ao", text="", slider=True)
                        if mat_cache.smart_hair:
                            col_1.separator()
                            col_2.separator()
                            col_1.label(text="Diffuse Hue")
                            col_2.prop(params, "hair_hue", text="", slider=True)
                            col_1.label(text="Diffuse Saturation")
                            col_2.prop(params, "hair_saturation", text="", slider=True)
                            col_1.label(text="Diffuse Strength")
                            col_2.prop(params, "hair_diffuse_strength", text="", slider=True)
                            col_1.label(text="Diffuse Brightness")
                            col_2.prop(params, "hair_brightness", text="", slider=True)
                            col_1.label(text="Diffuse Contrast")
                            col_2.prop(params, "hair_contrast", text="", slider=True)
                            col_1.separator()
                            col_2.separator()
                            col_1.label(text="Vertex Color Strength")
                            col_2.prop(params, "hair_vertex_color_strength", text="", slider=True)
                            col_1.label(text="Base Color Strength")
                            col_2.prop(params, "hair_base_color_map_strength", text="", slider=True)
                            col_1.label(text="Depth Strength")
                            col_2.prop(params, "hair_depth_strength", text="", slider=True)

                        if mat_cache.smart_hair:
                            column.box().label(text= "Hair Strands", icon="OUTLINER_OB_HAIR")
                            split = column.split(factor=0.5)
                            col_1 = split.column()
                            col_2 = split.column()

                            col_1.label(text="Strand Global Strength")
                            col_2.prop(params, "hair_global_strength", text="", slider=True)
                            col_1.label(text="Root Color")
                            col_2.prop(params, "hair_root_color", text="")
                            col_1.label(text="End Color")
                            col_2.prop(params, "hair_end_color", text="")
                            col_1.label(text="Root Strength")
                            col_2.prop(params, "hair_root_strength", text="", slider=True)
                            col_1.label(text="End Strength")
                            col_2.prop(params, "hair_end_strength", text="", slider=True)
                            col_1.label(text="Strand Invert")
                            col_2.prop(params, "hair_invert_strand", text="", slider=True)

                        if mat_cache.smart_hair:
                            column.box().label(text= "Highlights", icon="HAIR")
                            split = column.split(factor=0.5)
                            col_1 = split.column()
                            col_2 = split.column()

                            col_1.label(text="Highlight A Start")
                            col_2.prop(params, "hair_a_start", text="", slider=True)
                            col_1.label(text="Highlight A Mid")
                            col_2.prop(params, "hair_a_mid", text="", slider=True)
                            col_1.label(text="Highlight A End")
                            col_2.prop(params, "hair_a_end", text="", slider=True)
                            col_1.label(text="Highlight A Strength")
                            col_2.prop(params, "hair_a_strength", text="", slider=True)
                            col_1.label(text="Highlight A Overlap")
                            col_2.prop(params, "hair_a_overlap", text="", slider=True)
                            col_1.label(text="Highlight A Color")
                            col_2.prop(params, "hair_a_color", text="")
                            col_1.separator()
                            col_2.separator()
                            col_1.label(text="Highlight B Start")
                            col_2.prop(params, "hair_b_start", text="", slider=True)
                            col_1.label(text="Highlight B Mid")
                            col_2.prop(params, "hair_b_mid", text="", slider=True)
                            col_1.label(text="Highlight B End")
                            col_2.prop(params, "hair_b_end", text="", slider=True)
                            col_1.label(text="Highlight B Strength")
                            col_2.prop(params, "hair_b_strength", text="", slider=True)
                            col_1.label(text="Highlight B Overlap")
                            col_2.prop(params, "hair_b_overlap", text="", slider=True)
                            col_1.label(text="Highlight B Color")
                            col_2.prop(params, "hair_b_color", text="")

                        column.box().label(text= "Surface", icon="SURFACE_DATA")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        if linked or mat_cache.is_hair():
                            col_1.label(text="Hair Specular")
                            col_2.prop(params, "hair_specular", text="", slider=True)
                            col_1.label(text="Hair Roughness")
                            col_2.prop(params, "hair_roughness", text="", slider=True)
                        if linked or mat_cache.is_scalp():
                            col_1.label(text="Base Specular")
                            col_2.prop(params, "hair_scalp_specular", text="", slider=True)
                            col_1.label(text="Base Roughness")
                            col_2.prop(params, "hair_scalp_roughness", text="", slider=True)
                        if linked or mat_cache.is_eyelash():
                            col_1.label(text="Eyelash Specular")
                            col_2.prop(params, "hair_eyelash_specular", text="", slider=True)
                            col_1.label(text="Eyelash Roughness")
                            col_2.prop(params, "hair_eyelash_roughness", text="", slider=True)
                        if mat_cache.smart_hair:
                            col_1.separator()
                            col_2.separator()
                            if bpy.context.scene.render.engine == 'BLENDER_EEVEE' and prefs.fake_hair_anisotropy:
                                col_1.label(text="Anisotropic Color")
                                col_2.prop(params, "hair_aniso_color", text="", slider=True)
                                col_1.label(text="Anisotropic Strength")
                                col_2.prop(params, "hair_aniso_strength", text="", slider=True)
                            elif bpy.context.scene.render.engine == "CYCLES":
                                col_1.label(text="Anisotropic Strength")
                                col_2.prop(params, "hair_aniso_strength_cycles", text="", slider=True)

                        column.box().label(text= "Sub-surface", icon="SURFACE_NSURFACE")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="SSS Radius (cm)")
                        col_2.prop(params, "hair_sss_radius", text="", slider=True)
                        col_1.label(text="SSS Falloff")
                        col_2.prop(params, "hair_sss_falloff", text="")

                        column.box().label(text= "Opacity", icon="IMAGE_ALPHA")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        if linked or mat_cache.is_hair():
                            col_1.label(text="Hair Opacity")
                            col_2.prop(params, "hair_opacity", text="", slider=True)
                        if linked or mat_cache.is_scalp():
                            col_1.label(text="Base Opacity")
                            col_2.prop(params, "hair_scalp_opacity", text="", slider=True)
                        if linked or mat_cache.is_eyelash():
                            col_1.label(text="Eyelash Opacity")
                            col_2.prop(params, "hair_eyelash_opacity", text="", slider=True)

                        column.box().label(text= "Normals", icon="NORMALS_FACE")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Bump Height (mm)")
                        col_2.prop(params, "hair_bump", text="", slider=True)

                        if mat_cache.smart_hair:
                            if prefs.fake_hair_bump:
                                col_1.label(text="Fake Bump Midpoint")
                                col_2.prop(params, "hair_fake_bump_midpoint", text="", slider=True)

                # Defauls settings
                else: # mat_type == "DEFAULT":
                    column.separator()
                    if fake_drop_down(column.row(),
                            "Default Parameters",
                            "default_toggle",
                            props.default_toggle):
                        column.box().label(text= "Base Color", icon="COLOR")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Default AO")
                        col_2.prop(params, "default_ao", text="", slider=True)
                        col_1.label(text="Default Color Blend")
                        col_2.prop(params, "default_blend", text="", slider=True)

                        column.box().label(text= "Surface", icon="SURFACE_DATA")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Default Roughness")
                        col_2.prop(params, "default_roughness", text="", slider=True)

                        column.box().label(text= "Sub-surface", icon="SURFACE_NSURFACE")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="SSS Radius (cm)")
                        col_2.prop(params, "default_sss_radius", text="", slider=True)
                        col_1.label(text="SSS Falloff")
                        col_2.prop(params, "default_sss_falloff", text="")

                        column.box().label(text= "Normals", icon="NORMALS_FACE")
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Micro Normal")
                        col_2.prop(params, "default_micronormal", text="", slider=True)
                        col_1.label(text="Micro Normal Tiling")
                        col_2.prop(params, "default_tiling", text="", slider=True)
                        col_1.label(text="Bump Height (mm)")
                        col_2.prop(params, "default_bump", text="", slider=True)

            else: # BASIC material
                column.separator()
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Skin AO")
                col_2.prop(params, "skin_ao", text="", slider=True)
                col_1.label(text="Skin Specular")
                col_2.prop(params, "skin_basic_specular", text="", slider=True)
                col_1.label(text="Skin Roughness")
                col_2.prop(params, "skin_basic_roughness", text="", slider=True)
                col_1.separator()
                col_2.separator()
                col_1.label(text="Eye Specular")
                col_2.prop(params, "eye_specular", text="", slider=True)
                col_1.label(text="Eye Roughness")
                col_2.prop(params, "eye_basic_roughness", text="", slider=True)
                col_1.label(text="Eye Normal")
                col_2.prop(params, "eye_basic_normal", text="", slider=True)
                col_1.label(text="Eye Occlusion")
                col_2.prop(params, "eye_occlusion", text="", slider=True)
                col_1.label(text="Eye Occlusion Color")
                col_2.prop(params, "eye_occlusion_color", text="", slider=True)
                col_1.label(text="Eye Occlusion Hardness")
                col_2.prop(params, "eye_occlusion_hardness", text="", slider=True)
                col_1.label(text="Eye Brightness")
                col_2.prop(params, "eye_basic_brightness", text="", slider=True)
                col_1.label(text="Tearline Alpha")
                col_2.prop(params, "tearline_alpha", text="", slider=True)
                col_1.label(text="Tearline Roughness")
                col_2.prop(params, "tearline_roughness", text="", slider=True)
                col_1.separator()
                col_2.separator()
                col_1.label(text="Teeth Specular")
                col_2.prop(params, "teeth_specular", text="", slider=True)
                col_1.label(text="Teeth Roughness")
                col_2.prop(params, "teeth_roughness", text="", slider=True)
                col_1.separator()
                col_2.separator()
                col_1.label(text="Tongue Specular")
                col_2.prop(params, "tongue_specular", text="", slider=True)
                col_1.label(text="Tongue Roughness")
                col_2.prop(params, "tongue_roughness", text="", slider=True)
                col_1.separator()
                col_2.separator()
                col_1.label(text="Nails Specular")
                col_2.prop(params, "nails_specular", text="", slider=True)
                col_1.separator()
                col_2.separator()
                col_1.label(text="Hair AO")
                col_2.prop(params, "hair_ao", text="", slider=True)
                col_1.label(text="Hair Specular")
                col_2.prop(params, "hair_specular", text="", slider=True)
                col_1.label(text="Scalp Specular")
                col_2.prop(params, "hair_scalp_specular", text="", slider=True)
                col_1.label(text="Hair Bump Height (mm)")
                col_2.prop(params, "hair_bump", text="", slider=True)
                col_1.separator()
                col_2.separator()
                col_1.label(text="Default AO")
                col_2.prop(params, "default_ao", text="", slider=True)
                col_1.label(text="Default Bump Height (mm)")
                col_2.prop(params, "default_bump", text="", slider=True)

        layout.box().label(text="Utilities", icon="MODIFIER_DATA")
        column = layout.column()
        if props.import_name == "":
            column.enabled = False
        split = column.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text="Open Mouth")
        col_2.prop(props, "open_mouth", text="", slider=True)

        column = layout.column()
        op = column.operator("cc3.quickset", icon="DECORATE_OVERRIDE", text="Reset Parameters")
        op.param = "RESET"
        op = column.operator("cc3.importer", icon="MOD_BUILD", text="Rebuild Node Groups")
        op.param ="REBUILD_NODE_GROUPS"


class CC3ToolsScenePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Scene_Panel"
    bl_label = "Scene Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        layout = self.layout

        box = layout.box()
        box.label(text="Scene Lighting", icon="LIGHT")
        col = layout.column()

        op = col.operator("cc3.scene", icon="SHADING_SOLID", text="Solid Matcap")
        op.param = "MATCAP"

        op = col.operator("cc3.scene", icon="SHADING_TEXTURE", text="Blender Default")
        op.param = "BLENDER"
        op = col.operator("cc3.scene", icon="SHADING_TEXTURE", text="CC3 Default")
        op.param = "CC3"

        op = col.operator("cc3.scene", icon="SHADING_RENDERED", text="Studio Right")
        op.param = "STUDIO"
        op = col.operator("cc3.scene", icon="SHADING_RENDERED", text="Courtyard Left")
        op.param = "COURTYARD"

        box = layout.box()
        box.label(text="Scene, World & Compositor", icon="NODE_COMPOSITING")
        col = layout.column()

        op = col.operator("cc3.scene", icon="TRACKING", text="3 Point Tracking & Camera")
        op.param = "TEMPLATE"

        box = layout.box()
        box.label(text="Animation", icon="RENDER_ANIMATION")
        col = layout.column()
        scene = context.scene
        #op = col.operator("cc3.scene", icon="RENDER_STILL", text="Render Image")
        #op.param = "RENDER_IMAGE"
        #op = col.operator("cc3.scene", icon="RENDER_ANIMATION", text="Render Animation")
        #op.param = "RENDER_ANIMATION"
        split = layout.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.prop(scene, "frame_start", text="Start")
        col_2.prop(scene, "frame_end", text="End")
        col = layout.column()
        col.separator()
        op = col.operator("cc3.scene", icon="ARROW_LEFTRIGHT", text="Range From Character")
        op.param = "ANIM_RANGE"
        op = col.operator("cc3.scene", icon="ANIM", text="Sync Physics Range")
        op.param = "PHYSICS_PREP"
        col.separator()
        split = col.split(factor=0.)
        col_1 = split.column()
        col_2 = split.column()
        col_3 = split.column()
        if not context.screen.is_animation_playing:
            #op = col_1.operator("screen.animation_manager", icon="PLAY", text="Play")
            #op.mode = "PLAY"
            col_1.operator("screen.animation_play", text="Play", icon='PLAY')
        else:
            #op = col_1.operator("screen.animation_manager", icon="PAUSE", text="Pause")
            #op.mode = "PLAY"
            col_1.operator("screen.animation_play", text="Pause", icon='PAUSE')
        #op = col_2.operator("screen.animation_manager", icon="REW", text="Reset")
        #op.mode = "STOP"
        col_2.operator("screen.frame_jump", text="Start", icon='REW').end = False
        col_3.operator("screen.frame_jump", text="End", icon='FF').end = True


class CC3ToolsPhysicsPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Physics_Panel"
    bl_label = "Physics Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        layout = self.layout

        missing_cloth = False
        has_cloth = False
        missing_coll = False
        cloth_mod = None
        coll_mod = None
        meshes_selected = 0
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                meshes_selected += 1
                clm = modutils.get_cloth_physics_mod(obj)
                com = modutils.get_collision_physics_mod(obj)
                if clm is None:
                    missing_cloth = True
                else:
                    if context.object == obj:
                        cloth_mod = clm
                    has_cloth = True
                if com is None:
                    missing_coll = True
                else:
                    if context.object == obj:
                        coll_mod = com

        obj = context.object
        mat = context_material(context)
        edit_mod, mix_mod = modutils.get_material_weight_map_mods(obj, mat)

        box = layout.box()
        box.label(text="Create / Remove", icon="PHYSICS")

        col = layout.column()
        if not missing_cloth:
            op = col.operator("cc3.quickset", icon="REMOVE", text="Remove Cloth Physics")
            op.param = "PHYSICS_REMOVE_CLOTH"
        else:
            op = col.operator("cc3.quickset", icon="ADD", text="Add Cloth Physics")
            op.param = "PHYSICS_ADD_CLOTH"
        if not missing_coll:
            op = col.operator("cc3.quickset", icon="REMOVE", text="Remove Collision Physics")
            op.param = "PHYSICS_REMOVE_COLLISION"
        else:
            op = col.operator("cc3.quickset", icon="ADD", text="Add Collision Physics")
            op.param = "PHYSICS_ADD_COLLISION"
        if meshes_selected == 0:
            col.enabled = False

        box = layout.box()
        box.label(text="Mesh Correction", icon="MESH_DATA")
        col = layout.column()
        op = col.operator("cc3.quickset", icon="MOD_EDGESPLIT", text="Fix Degenerate Mesh")
        op.param = "PHYSICS_FIX_DEGENERATE"
        op = col.operator("cc3.quickset", icon="FACE_MAPS", text="Separate Physics Materials")
        op.param = "PHYSICS_SEPARATE"

        # Cloth Physics Presets
        box = layout.box()
        box.label(text="Presets", icon="PRESET")
        col = layout.column()
        if cloth_mod is None:
            col.enabled = False
        op = col.operator("cc3.quickset", icon="USER", text="Hair")
        op.param = "PHYSICS_HAIR"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Cotton")
        op.param = "PHYSICS_COTTON"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Denim")
        op.param = "PHYSICS_DENIM"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Leather")
        op.param = "PHYSICS_LEATHER"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Rubber")
        op.param = "PHYSICS_RUBBER"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Silk")
        op.param = "PHYSICS_SILK"

        # Cloth Physics Settings
        if cloth_mod is not None:
            box = layout.box()
            box.label(text="Cloth Settings", icon="OPTIONS")
            col = layout.column()
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Weight")
            col_2.prop(cloth_mod.settings, "mass", text="", slider=True)
            col_1.label(text="Bend Resist")
            col_2.prop(cloth_mod.settings, "bending_stiffness", text="", slider=True)
            col_1.label(text="Pin Stiffness")
            col_2.prop(cloth_mod.settings, "pin_stiffness", text="", slider=True)
            col_1.label(text="Quality")
            col_2.prop(cloth_mod.settings, "quality", text="", slider=True)
            col_1.label(text="Collision")
            col_2.prop(cloth_mod.collision_settings, "collision_quality", text="", slider=True)
            col_1.label(text="Distance")
            col_2.prop(cloth_mod.collision_settings, "distance_min", text="", slider=True)
        # Collision Physics Settings
        if coll_mod is not None:
            box = layout.box()
            box.label(text="Collision Settings", icon="OPTIONS")
            col = layout.column()
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Damping")
            col_2.prop(coll_mod.settings, "damping", text="", slider=True)
            col_1.label(text="Outer Thickness")
            col_2.prop(coll_mod.settings, "thickness_outer", text="", slider=True)
            col_1.label(text="Inner Thickness")
            col_2.prop(coll_mod.settings, "thickness_inner", text="", slider=True)
            col_1.label(text="Friction")
            col_2.prop(coll_mod.settings, "cloth_friction", text="", slider=True)

        box = layout.box()
        box.label(text="Weight Maps", icon="TEXTURE_DATA")
        split = layout.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        if not has_cloth:
            col_1.enabled = False
            col_2.enabled = False
        col_1.label(text="WeightMap Size")
        col_2.prop(props, "physics_tex_size", text="")

        col = layout.column()
        if cloth_mod is None:
            col.enabled = False

        if obj is not None:
            col.template_list("MATERIAL_UL_weightedmatslots", "", obj, "material_slots", obj, "active_material_index", rows=1)
        if edit_mod is not None:
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Influence")
            col_2.prop(mix_mod, "mask_constant", text="", slider=True)
        col.separator()
        if bpy.context.mode == "PAINT_TEXTURE":
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Strength")
            col_2.prop(props, "physics_paint_strength", text="", slider=True)
            row = col.row()
            row.scale_y = 2
            op = row.operator("cc3.quickset", icon="CHECKMARK", text="Done Weight Painting!")
            op.param = "PHYSICS_DONE_PAINTING"
        else:
            if edit_mod is None:
                row = col.row()
                op = row.operator("cc3.quickset", icon="ADD", text="Add Weight Map")
                op.param = "PHYSICS_ADD_WEIGHTMAP"
            else:
                row = col.row()
                op = row.operator("cc3.quickset", icon="REMOVE", text="Remove Weight Map")
                op.param = "PHYSICS_REMOVE_WEIGHTMAP"
            col = layout.column()
            if edit_mod is None:
                col.enabled = False
            op = col.operator("cc3.quickset", icon="BRUSH_DATA", text="Paint Weight Map")
            op.param = "PHYSICS_PAINT"
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            op = col_1.operator("cc3.quickset", icon="FILE_TICK", text="Save")
            op.param = "PHYSICS_SAVE"
            op = col_2.operator("cc3.quickset", icon="ERROR", text="Delete")
            op.param = "PHYSICS_DELETE"


class CC3ToolsPipelinePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Pipeline_Panel"
    bl_label = "Import / Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"

    def draw(self, context):
        global debug_counter
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        if prefs.debug_mode:
            layout.label(text="Counter: " + str(debug_counter))
            debug_counter += 1

        box = layout.box()
        box.label(text="Settings", icon="TOOL_SETTINGS")
        #layout.prop(props, "setup_mode", expand=True)
        if prefs.lighting == "ENABLED" or prefs.physics == "ENABLED":
            if prefs.lighting == "ENABLED":
                layout.prop(props, "lighting_mode", expand=True)
            if prefs.physics == "ENABLED":
                layout.prop(props, "physics_mode", expand=True)

        box = layout.box()
        box.label(text="Render / Animation", icon="RENDER_RESULT")
        row = layout.row()
        row.scale_y = 2
        op = row.operator("cc3.importer", icon="IMPORT", text="Import Character")
        op.param = "IMPORT_QUALITY"

        box = layout.box()
        box.label(text="Morph Editing", icon="OUTLINER_OB_ARMATURE")
        row = layout.row()
        op = row.operator("cc3.importer", icon="IMPORT", text="Import For Morph")
        op.param = "IMPORT_MORPH"
        row = layout.row()
        op = row.operator("cc3.exporter", icon="EXPORT", text="Export Character Morph")
        op.param = "EXPORT_MORPH"
        if props.import_name == "":
            row.enabled = False

        box = layout.box()
        box.label(text="Accessory Editing", icon="MOD_CLOTH")
        row = layout.row()
        op = row.operator("cc3.importer", icon="IMPORT", text="Import For Accessory")
        op.param = "IMPORT_ACCESSORY"
        row = layout.row()
        op = row.operator("cc3.exporter", icon="EXPORT", text="Export Accessory")
        op.param = "EXPORT_ACCESSORY"
        if props.import_name == "":
            row.enabled = False

        layout.separator()
        box = layout.box()
        box.label(text="Clean Up", icon="TRASH")

        row = layout.row()
        op = row.operator("cc3.importer", icon="REMOVE", text="Remove Character")
        op.param ="DELETE_CHARACTER"
        if props.import_name == "":
            row.enabled = False


# class to show node coords in shader editor...
#class CC3NodeCoord(bpy.types.Panel):
#    bl_label = "Node Coordinates panel"
#    bl_idname = "CC3I_PT_NodeCoord"
#    bl_space_type = "NODE_EDITOR"
#    bl_region_type = "UI"
#
#    def draw(self, context):
#        if context.active_node is not None:
#            layout = self.layout
#            layout.separator()
#            row = layout.box().row()
#            coords = context.active_node.location
#            row.label(text=str(int(coords.x/10)*10) + ", " + str(int(coords.y/10)*10))


def reset_preferences():
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    prefs.lighting = "ENABLED"
    prefs.physics = "ENABLED"
    prefs.quality_lighting = "CC3"
    prefs.pipeline_lighting = "CC3"
    prefs.morph_lighting = "MATCAP"
    prefs.quality_mode = "ADVANCED"
    prefs.pipeline_mode = "ADVANCED"
    prefs.morph_mode = "ADVANCED"
    prefs.log_level = "ERRORS"
    prefs.hair_hint = "hair,scalp,beard,mustache,sideburns,ponytail,braid,!bow,!band,!tie,!ribbon,!ring,!butterfly,!flower"
    prefs.hair_scalp_hint = "scalp,base,skullcap"
    prefs.debug_mode = False
    prefs.compat_mode = False
    prefs.physics_group = "CC_Physics"
    prefs.new_hair_shader = True
    prefs.hair_gamma_correct = False
    prefs.fake_hair_anisotropy = True
    prefs.fake_hair_bump = True
    prefs.refractive_eyes = True
    prefs.eye_displacement_group = "CC_Eye_Displacement"
    prefs.use_advanced_eye_occlusion = True


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
                    ], default="CC3", name = "Render / Quality Lighting")

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
                    ], default="ADVANCED", name = "Accessory Material Mode")

    morph_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic Materials","Build basic PBR materials for character morph / accessory editing"),
                        ("ADVANCED","Advanced Materials","Build advanced materials for character morph / accessory editing"),
                    ], default="ADVANCED", name = "Character Morph Material Mode")

    log_level: bpy.props.EnumProperty(items=[
                        ("ALL","All","Log everything to console."),
                        ("WARN","Warnings & Errors","Log warnings and error messages to console."),
                        ("ERRORS","Just Errors","Log only errors to console."),
                    ], default="ERRORS", name = "(Debug) Log Level")

    hair_hint: bpy.props.StringProperty(default="hair,scalp,beard,mustache,sideburns,ponytail,braid,!bow,!band,!tie,!ribbon,!ring,!butterfly,!flower", name="Hair detection keywords")
    hair_scalp_hint: bpy.props.StringProperty(default="scalp,base,skullcap", name="Scalp detection keywords")

    debug_mode: bpy.props.BoolProperty(default=False)
    compat_mode: bpy.props.BoolProperty(default=False)

    physics_group: bpy.props.StringProperty(default="CC_Physics", name="Physics Vertex Group Prefix")

    new_hair_shader: bpy.props.BoolProperty(default=True, name="Smart Hair", description="Generate materials for the new hair shader")
    hair_gamma_correct: bpy.props.BoolProperty(default=False, name="Gamma Correct", description="Correct hair shader colours to be more like CC3 colours")
    fake_hair_anisotropy: bpy.props.BoolProperty(default=True, name="Eevee Anisotropic Highlights", description="Add fake anisotropic higlights to the hair in Eevee")
    fake_hair_bump: bpy.props.BoolProperty(default=False, name="Fake Hair Bump", description="Fake hair bump map from the diffuse map if there is no normal or bump map present")

    refractive_eyes: bpy.props.BoolProperty(default=True, name="Refractive Eyes", description="Generate refractive eyes with iris depth and pupil scale parameters")
    eye_displacement_group: bpy.props.StringProperty(default="CC_Eye_Displacement", name="Eye Displacement Group", description="Eye Iris displacement vertex group name")
    use_advanced_eye_occlusion: bpy.props.BoolProperty(default=True, name="Use Advanced Eye Occlusion Shader")

    # addon updater preferences

    auto_check_update: bpy.props.BoolProperty(
	    name="Auto-check for Update",
	    description="If enabled, auto-check for updates using an interval",
	    default=False,
	    )
    updater_intrval_months: bpy.props.IntProperty(
		name='Months',
		description="Number of months between checking for updates",
		default=0,
		min=0
		)
    updater_intrval_days: bpy.props.IntProperty(
		name='Days',
		description="Number of days between checking for updates",
		default=7,
		min=0,
		max=31
		)
    updater_intrval_hours: bpy.props.IntProperty(
		name='Hours',
		description="Number of hours between checking for updates",
		default=0,
		min=0,
		max=23
		)
    updater_intrval_minutes: bpy.props.IntProperty(
		name='Minutes',
		description="Number of minutes between checking for updates",
		default=0,
		min=0,
		max=59
		)

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
        layout.label(text="Detection:")
        layout.prop(self, "hair_hint")
        layout.prop(self, "hair_scalp_hint")
        layout.label(text="Hair:")
        layout.prop(self, "new_hair_shader")
        layout.prop(self, "hair_gamma_correct")
        layout.prop(self, "fake_hair_anisotropy")
        layout.prop(self, "fake_hair_bump")
        layout.label(text="Eyes:")
        layout.prop(self, "refractive_eyes")
        layout.prop(self, "eye_displacement_group")
        layout.prop(self, "use_advanced_eye_occlusion")
        layout.label(text="Physics:")
        layout.prop(self, "physics")
        layout.prop(self, "physics_group")
        layout.label(text="Debug Settings:")
        layout.prop(self, "log_level")
        layout.prop(self, "debug_mode")
        if self.debug_mode:
            layout.prop(self, "compat_mode")
        op = layout.operator("cc3.quickset", icon="FILE_REFRESH", text="Reset to Defaults")
        op.param = "RESET_PREFS"

        addon_updater_ops.update_settings_ui(self,context)

class MATERIAL_UL_weightedmatslots(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        slot = item
        ma = slot.material
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if ma:
                layout.prop(ma, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
