# Copyright (C) 2021 Victor Soupday
# This file is part of CC/iC Blender Tools <https://github.com/soupday/cc_blender_tools>
#
# CC/iC Blender Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CC/iC Blender Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CC/iC Blender Tools.  If not, see <https://www.gnu.org/licenses/>.

import os

import bpy

from . import imageutils, jsonutils, nodeutils, utils, params, vars


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
    prefs = vars.prefs()
    material_name = mat.name.lower()
    hints = prefs.hair_scalp_hint.split(",")
    detect = detect_key_words(hints, material_name)
    if detect == "Deny":
        utils.log_info(f"{mat.name}: has deny keywords, defininately not scalp!")
    elif detect == "True":
        utils.log_info(f"{mat.name}: has keywords, is scalp.")
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


def detect_body_object(chr_cache, obj):
    name = obj.name.lower()
    if "base_body" in name or "game_body" in name:
        return True
    return False


def detect_smart_hair_maps(mat, tex_dirs, base_dir):

    if (imageutils.find_image_file(base_dir, tex_dirs, mat, "HAIRFLOW") is not None or
        imageutils.find_image_file(base_dir, tex_dirs, mat, "HAIRROOT") is not None or
        imageutils.find_image_file(base_dir, tex_dirs, mat, "HAIRID") is not None or
        imageutils.find_image_file(base_dir, tex_dirs, mat, "HAIRVERTEXCOLOR") is not None):
        return "True"
    return "False"


def detect_sss_maps(mat, tex_dirs, base_dir):
    if (imageutils.find_image_file(base_dir, tex_dirs, mat, "SSS") is not None or
        imageutils.find_image_file(base_dir, tex_dirs, mat, "TRANSMISSION") is not None or
        imageutils.find_image_file(base_dir, tex_dirs, mat, "RGBAMASK") is not None or
        imageutils.find_image_file(base_dir, tex_dirs, mat, "MICRONORMAL") is not None or
        imageutils.find_image_file(base_dir, tex_dirs, mat, "MICRONMASK") is not None):
        return "True"
    return "False"


def detect_hair_material(obj, mat, tex_dirs, base_dir, mat_json = None):
    prefs = vars.prefs()
    hints = prefs.hair_hint.split(",")

    material_name = mat.name.lower()

    if mat_json:
        shader = jsonutils.get_custom_shader(mat_json)
        if shader == "RLHair":
            return "True"
        else:
            return "False"

    # try to find one of the new hair maps: "Flow Map" or "Root Map"
    if detect_smart_hair_maps(mat, tex_dirs, base_dir) == "True":
        utils.log_info(f"{obj.name} / {mat.name}: has hair shader textures, is hair.")
        return "True"

    detect_mat = detect_key_words(hints, material_name)

    if detect_mat == "Deny":
        utils.log_info(f"{obj.name} / {mat.name}: Material has deny keywords, definitely not hair!")
        return "Deny"

    if detect_mat == "True":
        utils.log_info(f"{obj.name} / {mat.name}: Material has hair keywords, is hair.")
        return "True"

    return "False"


def detect_hair_object(obj, tex_dirs, base_dir, obj_json = None):
    prefs = vars.prefs()
    hints = prefs.hair_hint.split(",")
    object_name = obj.name.lower()

    if obj_json:
        for mat in obj.data.materials:
            if mat:
                mat_json = jsonutils.get_material_json(obj_json, mat)
                shader = jsonutils.get_custom_shader(mat_json)
                if shader == "RLHair":
                    utils.log_info(f"{obj.name} / {mat.name}: Hair material found in JSON data, Object is hair.")
                    return "True"

        return "False"

    # with no Json data, attempt to identify hair object by object and material names...

    for mat in obj.data.materials:
        if mat:
            mat_json = jsonutils.get_material_json(obj_json, mat)
            detect_mat = detect_hair_material(obj, mat, tex_dirs, base_dir, mat_json)
            if detect_mat == "True":
                utils.log_info(f"{obj.name} / {mat.name}: Hair material found, Object is hair.")
                return "True"

    detect_obj = detect_key_words(hints, object_name)

    if detect_obj == "Deny":
        utils.log_info(f"{obj.name} / {mat.name}: Object has deny keywords, definitely not hair!")
        return "Deny"

    if detect_obj == "True":
        utils.log_info(f"{obj.name} / {mat.name}: Object has hair keywords, is hair.")
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


STD_MATERIAL_TYPES = {
    "Std_Tongue": "TONGUE",
    "Std_Skin_Head": "SKIN_HEAD",
    "Std_Skin_Body": "SKIN_BODY",
    "Std_Skin_Arm": "SKIN_ARM",
    "Std_Skin_Leg": "SKIN_LEG",
    "Std_Nails": "NAILS",
    "Std_Eyelash": "EYELASH",
    "Std_Tearline_R": "TEARLINE_RIGHT",
    "Std_Tearline_L": "TEARLINE_LEFT",
    "Std_Eye_Occlusion_R": "OCCLUSION_RIGHT",
    "Std_Eye_Occlusion_L": "OCCLUSION_LEFT",
    "Std_Upper_Teeth": "TEETH_UPPER",
    "Std_Lower_Teeth": "TEETH_LOWER",
    "Std_Eye_R": "EYE_RIGHT",
    "Std_Eye_L": "EYE_LEFT",
    "Std_Cornea_R": "CORNEA_RIGHT",
    "Std_Cornea_L": "CORNEA_LEFT",
}


def detect_materials_by_name(chr_cache, obj, mat):

    mat_name = mat.name.lower()
    material_type = "DEFAULT"
    object_type = "DEFAULT"
    tex_dirs = imageutils.get_material_tex_dirs(chr_cache, obj, mat)

    if chr_cache.is_import_type("OBJ"):
        if chr_cache.get_import_has_key():
            base_name = utils.strip_name(mat.name)
            if base_name in STD_MATERIAL_TYPES:
                material_type = STD_MATERIAL_TYPES[base_name]
                object_type = "BODY"
                utils.log_info(f"Material: {mat_name} detected from morph as: {material_type}")
                return object_type, material_type

    if detect_hair_object(obj, tex_dirs, chr_cache.get_import_dir()) == "True":
        object_type = "HAIR"
        if detect_scalp_material(mat) == "True":
            material_type = "SCALP"
        elif detect_hair_material(obj, mat, tex_dirs, chr_cache.get_import_dir()) == "Deny":
            material_type = "DEFAULT"
        else:
            material_type = "HAIR"

    elif detect_body_object(chr_cache, obj):
        object_type = "BODY"
        if detect_skin_material(mat):
            if "head" in mat_name:
                material_type = "SKIN_HEAD"
            elif "body" in mat_name:
                material_type = "SKIN_BODY"
            elif "arm" in mat_name:
                material_type = "SKIN_ARM"
            elif "leg" in mat_name:
                material_type = "SKIN_LEG"
        elif detect_nails_material(mat):
            material_type = "NAILS"
        elif detect_eyelash_material(mat):
            material_type = "EYELASH"

    elif detect_cornea_material(mat):
        object_type = "EYE"
        if detect_material_side(mat, "LEFT"):
            material_type = "CORNEA_LEFT"
        else:
            material_type = "CORNEA_RIGHT"

    elif detect_eye_occlusion_material(mat): # detect occlusion before eye
        object_type = "OCCLUSION"
        if detect_material_side(mat, "LEFT"):
            material_type = "OCCLUSION_LEFT"
        else:
            material_type = "OCCLUSION_RIGHT"

    elif detect_eye_material(mat):
        object_type = "EYE"
        if detect_material_side(mat, "LEFT"):
            material_type = "EYE_LEFT"
        else:
            material_type = "EYE_RIGHT"

    elif detect_tearline_material(mat):
        object_type = "TEARLINE"
        if detect_material_side(mat, "LEFT"):
            material_type = "TEARLINE_LEFT"
        else:
            material_type = "TEARLINE_RIGHT"

    elif detect_teeth_material(mat):
        object_type = "TEETH"
        if detect_material_side(mat, "UPPER"):
            material_type = "TEETH_UPPER"
        else:
            material_type = "TEETH_LOWER"

    elif detect_tongue_material(mat):
        object_type = "TONGUE"
        material_type = "TONGUE"

    elif detect_sss_maps(mat, tex_dirs, chr_cache.get_import_dir()) == "True":
        material_type = "SSS"

    utils.log_info(f"Material: {mat_name} detected by name as: {material_type}")
    return object_type, material_type


def detect_materials_from_json(chr_cache, obj, mat, obj_json, mat_json):
    shader = jsonutils.get_custom_shader(mat_json)
    mat_name = mat.name.lower()

    material_type = "DEFAULT"
    object_type = "DEFAULT"
    tex_dirs = imageutils.get_material_tex_dirs(chr_cache, obj, mat)

    utils.log_info(f"Material Shader: {shader}")

    if shader == "Pbr" or shader == "Tra":
        # PBR materials can also refer to the scalp/base on hair objects,
        # the eyelashes on the body or the eye(iris) materials on the eyes.
        if detect_hair_object(obj, tex_dirs, chr_cache.get_import_dir(), obj_json) == "True":
            object_type = "HAIR"
            if detect_hair_material(obj, mat, tex_dirs, chr_cache.get_import_dir(), mat_json) == "True":
                material_type = "HAIR"
            elif detect_scalp_material(mat) == "True":
                material_type = "SCALP"
            else:
                material_type = "DEFAULT"

        elif detect_eyelash_material(mat):
            object_type = "BODY"
            material_type = "EYELASH"

        elif detect_eye_material(mat):
            object_type = "EYE"
            if detect_material_side(mat, "LEFT"):
                material_type = "EYE_LEFT"
            else:
                material_type = "EYE_RIGHT"

        else:
            material_type = "DEFAULT"

    elif shader == "RLSSS":
        material_type = "SSS"

    elif shader == "RLTongue":
        object_type = "TONGUE"
        material_type = "TONGUE"

    elif shader == "RLSkin":
        object_type = "BODY"
        if "body" in mat_name:
            material_type = "SKIN_BODY"
        elif "arm" in mat_name:
            material_type = "SKIN_ARM"
        elif "leg" in mat_name:
            material_type = "SKIN_LEG"
        elif detect_nails_material(mat):
            material_type = "NAILS"

    elif shader == "RLHead":
        object_type = "BODY"
        material_type = "SKIN_HEAD"

    elif shader == "RLEye":
        object_type = "EYE"
        if detect_material_side(mat, "LEFT"):
            material_type = "CORNEA_LEFT"
        else:
            material_type = "CORNEA_RIGHT"

    elif shader == "RLTeethGum":
        object_type = "TEETH"
        if detect_material_side(mat, "UPPER"):
            material_type = "TEETH_UPPER"
        else:
            material_type = "TEETH_LOWER"

    elif shader == "RLEyeOcclusion":
        object_type = "OCCLUSION"
        if detect_material_side(mat, "LEFT"):
            material_type = "OCCLUSION_LEFT"
        else:
            material_type = "OCCLUSION_RIGHT"

    elif shader == "RLEyeTearline":
        object_type = "TEARLINE"
        if detect_material_side(mat, "LEFT"):
            material_type = "TEARLINE_LEFT"
        else:
            material_type = "TEARLINE_RIGHT"

    elif shader == "RLHair":
        object_type = "HAIR"
        material_type = "HAIR"

    else:
        object_type = "DEFAULT"
        material_type = "DEFAULT"

    utils.log_info(f"Material: {mat_name} detected from Json data as: {material_type}")
    return object_type, material_type


def detect_materials(chr_cache, obj, mat, obj_json):
    if chr_cache.is_actor_core():
        return "BODY", "DEFAULT"
    mat_json = jsonutils.get_material_json(obj_json, mat)
    if mat_json:
        return detect_materials_from_json(chr_cache, obj, mat, obj_json, mat_json)
    else:
        return detect_materials_by_name(chr_cache, obj, mat)


def detect_embedded_textures(chr_cache, obj, obj_cache, mat, mat_cache):
    main_tex_dir = chr_cache.get_tex_dir()
    nodes = mat.node_tree.nodes

    # detect embedded textures
    for node in nodes:
        if node.type == "TEX_IMAGE" and node.image is not None:
            filepath = bpy.path.abspath(node.image.filepath)
            dir, name = os.path.split(filepath)

            # presence of packed images means that the fbx had embedded textures
            if node.image.packed_file:
                chr_cache.import_embedded = True

            # detect incorrect image paths for non packed (not embedded) images and attempt to correct...
            # (don't do this for user added materials)
            if not mat_cache.user_added and node.image.packed_file is None:
                if os.path.normpath(dir) != os.path.normpath(main_tex_dir):
                    utils.log_warn("Import bug! Wrong image path detected: " + dir)
                    correct_path = os.path.join(main_tex_dir, name)
                    utils.log_warn(f"Attempting to correct to: {correct_path}")
                    if os.path.exists(correct_path):
                        utils.log_warn(f"Correct image path found: {correct_path}")
                        node.image.filepath = correct_path
                    else:
                        correct_path = os.path.join(mat_cache.get_tex_dir(chr_cache), name)
                        utils.log_warn(f"Attempting to correct to: {correct_path}")
                        if os.path.exists(correct_path):
                            utils.log_warn(f"Correct image path found: {correct_path}")
                            node.image.filepath = correct_path
                        else:
                            utils.log_error("Unable to find correct image!")
                            continue

            name = name.lower()
            color_node, color_socket = nodeutils.get_node_and_socket_connected_to_output(node, "Color")
            alpha_node, alpha_socket = nodeutils.get_node_and_socket_connected_to_output(node, "Alpha")

            if color_node and color_socket:

                if color_node.type == "BSDF_PRINCIPLED":

                    if color_socket.name == "Base Color":
                        nodeutils.store_texture_mapping(node, mat_cache, "DIFFUSE")

                    elif color_socket.name in ["Specular", "Specular IOR Level"]:
                        nodeutils.store_texture_mapping(node, mat_cache, "SPECULAR")

                    elif color_socket.name == "Metallic":
                        nodeutils.store_texture_mapping(node, mat_cache, "METALLIC")

                    elif color_socket.name == "Roughness":
                        nodeutils.store_texture_mapping(node, mat_cache, "ROUGHNESS")

                    elif color_socket.name in ["Emission", "Emission Color"]:
                        nodeutils.store_texture_mapping(node, mat_cache, "EMISSION")

                    elif color_socket.name == "Alpha":
                        nodeutils.store_texture_mapping(node, mat_cache, "ALPHA")
                        if "diffuse" in name or "albedo" in name:
                            mat_cache.alpha_is_diffuse = True

                    elif color_socket.name in ["Subsurface", "Subsurface Weight"]:
                        nodeutils.store_texture_mapping(node, mat_cache, "SSS")

                elif color_node.type == "NORMAL_MAP":

                    if "_bump" in name: # fbx import plugs bump maps into the normal map node...
                        nodeutils.store_texture_mapping(node, mat_cache, "BUMP")
                    else:
                        nodeutils.store_texture_mapping(node, mat_cache, "NORMAL")

                elif color_node.type == "BUMP":

                    nodeutils.store_texture_mapping(node, mat_cache, "BUMP")

                else:
                    #if color_node.type == "EMISSION":
                    if node.label == "BASE COLOR":
                        nodeutils.store_texture_mapping(node, mat_cache, "DIFFUSE")
                        if nodeutils.get_node_connected_to_output(node, "Alpha"):
                            nodeutils.store_texture_mapping(node, mat_cache, "ALPHA")
                            mat_cache.alpha_is_diffuse = True

            elif alpha_node and alpha_socket:

                if alpha_node.type == "BSDF_PRINCIPLED":

                    if alpha_socket.name == "Alpha":
                        nodeutils.store_texture_mapping(node, mat_cache, "ALPHA")
                        if "diffuse" in name or "albedo" in name:
                            mat_cache.alpha_is_diffuse = True


def detect_mixer_masks(chr_cache, obj, obj_cache, mat, mat_cache):
    main_tex_dir = chr_cache.get_tex_dir()
    mat_tex_dir = mat_cache.get_tex_dir(chr_cache)

    rgb_mask : bpy.types.Image = imageutils.find_material_image(mat, "RGBMASK")
    color_id_mask : bpy.types.Image = imageutils.find_material_image(mat, "COLORID")

    if rgb_mask or color_id_mask:
        mixer_settings = mat_cache.mixer_settings

        if rgb_mask:
            utils.log_info(f"Mixer RGB Mask found: {rgb_mask.filepath}")
            mixer_settings.rgb_image = rgb_mask
            rgb_mask.use_fake_user = True

        if color_id_mask:
            utils.log_info(f"Mixer Color Id Mask found: {color_id_mask.filepath}")
            mixer_settings.id_image = color_id_mask
            color_id_mask.use_fake_user = True


def get_cornea_mat(obj, eye_mat, eye_mat_cache):
    props = vars.props()
    chr_cache = props.get_character_cache(obj, eye_mat)

    if eye_mat_cache.is_eye("LEFT"):
        side = "LEFT"
    else:
        side = "RIGHT"

    # then try to find in the material cache
    for mat_cache in chr_cache.eye_material_cache:
        if not mat_cache.disabled and mat_cache.is_cornea(side):
            return mat_cache.material, mat_cache

    utils.log_error("Unable to find the " + side + " cornea material!")

    return None, None


def get_left_right_materials(obj):

    left = None
    right = None

    for idx in range(0, len(obj.material_slots)):
        slot = obj.material_slots[idx]
        if slot.material:
            name = slot.name.lower()
            if "_l" in name:
                left = slot.material
            elif "_r" in name:
                right = slot.material

    return left, right


def get_left_right_eye_materials(obj):
    """Eye, (not cornea)"""
    left = None
    right = None

    for idx in range(0, len(obj.material_slots)):
        slot = obj.material_slots[idx]
        if slot.material:
            name = slot.name.lower()
            if "std_eye_l" in name:
                left = slot.material
            elif "std_eye_r" in name:
                right = slot.material

    return left, right

def is_left_material(mat):
    if "_l" in mat.name.lower():
        return True
    return False

def is_right_material(mat):
    if "_r" in mat.name.lower():
        return True
    return False


def is_material_in_objects(mat, objects):
    if mat:
        for obj in objects:
            if obj.type == "MESH":
                if mat.name in obj.data.materials:
                    return True
    return False


def apply_backface_culling(obj, mat, sides):
    props = vars.props()
    mat_cache = props.get_material_cache(mat)
    if mat_cache is not None:
        mat_cache.culling_sides = sides
    if sides == 1:
        mat.use_backface_culling = True
    else:
        mat.use_backface_culling = False


def apply_alpha_override(obj, mat, method):
    props = vars.props()
    mat_cache = props.get_material_cache(mat)
    if mat_cache is not None:
        mat_cache.alpha_mode = method

    set_material_alpha(mat, method)


def determine_material_alpha(obj_cache, mat_cache, mat_json):
    is_alpha = False
    is_blend = False

    if mat_json:
        if "Opacity" in mat_json.keys():
            if mat_json["Opacity"] < 1.0:
                is_alpha = True
        opacity_info = jsonutils.get_texture_info(mat_json, "Opacity")
        if opacity_info and "Texture Path" in opacity_info.keys() and opacity_info["Texture Path"]:
            is_alpha = True

    name = mat_cache.source_name

    if utils.name_contains_distinct_keywords(name, "Transparency", "Alpha", "Opacity"):
        is_alpha = True

    if utils.name_contains_distinct_keywords(name, "Blend", "Lenses", "Lens", "Glass", "Glasses"):
        is_blend = True

    if utils.name_contains_distinct_keywords(name, "Base", "Scalp", "Eyelash"):
        is_alpha = True

    if obj_cache.is_hair() or mat_cache.is_eyelash():
        is_alpha = True

    if obj_cache.is_tearline() or obj_cache.is_eye_occlusion():
        is_blend = True

    # sometimes the eye is pbr and not the digital human eye shader
    if detect_cornea_material(mat_cache.material):
        is_blend = True

    if is_blend:
        return "BLEND"
    elif is_alpha:
        return "HASHED"
    else:
        return "OPAQUE"


def set_material_alpha(mat, method, shadows=True, refraction=False, depth=0.0):

    if utils.B410():
        mat.use_raytrace_refraction = refraction
    else:
        mat.use_screen_refraction = refraction
        mat.refraction_depth = depth

    if method == "HASHED" or method == "DITHERED":

        if utils.B420():
            mat.surface_render_method = "DITHERED"
        else:
            mat.blend_method = "HASHED"
            mat.shadow_method = "HASHED" if shadows else "NONE"

        set_backface_culling(mat, False)

    elif method == "BLEND":

        if utils.B420():
            mat.surface_render_method = "BLENDED"
        else:
            mat.blend_method = "BLEND"
            mat.shadow_method = "CLIP" if shadows else "NONE"
            mat.alpha_threshold = 0.5

        set_backface_culling(mat, True)

    elif method == "CLIP":

        if utils.B420():
            mat.surface_render_method = "BLENDED"
        else:
            mat.blend_method = "CLIP"
            mat.shadow_method = "CLIP" if shadows else "NONE"
            mat.alpha_threshold = 0.5

        set_backface_culling(mat, False)

    else:

        if utils.B420():
            mat.surface_render_method = "DITHERED"
        else:
            mat.blend_method = "OPAQUE"
            mat.shadow_method = "OPAQUE"

        set_backface_culling(mat, False)


def set_backface_culling(mat, backface_culling=True):
    try:
        mat.use_backface_culling = backface_culling
    except: ...
    try:
        mat.use_backface_culling_shadow = backface_culling
    except: ...

def test_for_material_uv_coords(obj, mat_slot, uvs):
    mesh = obj.data
    ul = mesh.uv_layers[0]
    for poly in mesh.polygons:
        if poly.material_index == mat_slot:
            for loop_index in poly.loop_indices:
                loop_entry = mesh.loops[loop_index]
                poly_uv = ul.data[loop_entry.index].uv
                for uv in uvs:
                    du = uv[0] - poly_uv[0]
                    dv = uv[1] - poly_uv[1]
                    if abs(du) < 0.01 and abs(dv) < 0.01:
                        return True
    return False


def get_material_slot_by_type(chr_cache, obj, material_type):
    if obj.type == "MESH":
        for index, slot in enumerate(obj.material_slots):
            mat = slot.material
            if mat:
                mat_cache = chr_cache.get_material_cache(mat)
                if mat_cache and mat_cache.material_type == material_type:
                    return index
    return -1


def get_material_by_type(chr_cache, obj, material_type):
    if obj.type == "MESH":
        for mat in obj.data.materials:
            mat_cache = chr_cache.get_material_cache(mat)
            if mat_cache and mat_cache.material_type == material_type:
                return mat
    return None


def has_same_textures(mat_a, mat_b):
    if mat_a.node_tree and mat_b.node_tree:
        nodes_a = mat_a.node_tree.nodes
        nodes_b = mat_b.node_tree.nodes
        if nodes_a and nodes_b:
            for a in nodes_a:
                if a.type == "TEX_IMAGE":
                    has_image = False
                    for b in nodes_b:
                        if b.type == "TEX_IMAGE":
                            if a.image == b.image:
                                has_image = True
                    if not has_image:
                        return False
            return True
    return False


def has_same_parameters(cache_a, cache_b):
    if cache_a and cache_b:
        if cache_a.material_type == cache_b.material_type:
            params_a = cache_a.parameters
            params_b = cache_b.parameters
            items_a = params_a.items()
            items_b = params_b.items()
            # put the property group items into lists
            #     [(prop_name, value), (prop_name, value), ...]
            # (because items are not subscriptable)
            list_a = [ i for i in items_a ]
            list_b = [ i for i in items_b ]
            for i in range(0, len(list_a)):
                # compare prop names
                if list_a[i][0] != list_b[i][0]:
                    return False
                # compare prop values
                try:
                    # try as array first
                    if len(list_a[i][1]) == len(list_b[i][1]):
                        for j in range(0, len(list_a[i][1])):
                            if list_a[i][1][j] != list_b[i][1][j]:
                                return False
                    else:
                        return False
                except:
                    # then as a value
                    if list_a[i][1] != list_b[i][1]:
                        return False
            return True
    return False


def find_duplicate_material(chr_cache, mat, processed_materials):
    source_name = utils.strip_name(mat.name)
    mat_cache = chr_cache.get_material_cache(mat)
    if mat_cache and processed_materials is not None:
        for processed_mat in processed_materials:
            if mat != processed_mat:
                processed_name = utils.strip_name(processed_mat.name)
                # only consider materials with the same base name
                if processed_name == source_name:
                    processed_cache = chr_cache.get_material_cache(processed_mat)
                    if processed_cache:
                        # with the same material type
                        if mat_cache.material_type == processed_cache.material_type:
                            # that use the same textures
                            if has_same_textures(mat, processed_mat):
                                # and have the same parameters
                                if has_same_parameters(mat_cache, processed_cache):
                                    # if there is a matching material that is the base name,
                                    # then set the first material name to this base name
                                    if mat.name == source_name:
                                        utils.force_material_name(processed_mat, source_name)
                                    return processed_mat
    return None


def normalize_udim_uvs(obj):
    """Restore UDIM uv's to into range 0.0 - 1.0
    """
    mesh = obj.data
    ul = mesh.uv_layers[0]
    for uv_loop in ul.data:
        uv = uv_loop.uv
        x = int(uv[0])
        y = int(uv[1])
        uv[0] -= x
        uv[1] -= y


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


def set_materials_setting(param, obj, context, objects_processed):
    props = vars.props()
    ob = context.object

    if obj is not None and obj not in objects_processed:
        if obj.type == "MESH":
            objects_processed.append(obj)

            if props.quick_set_mode == "OBJECT":
                for mat in obj.data.materials:
                    if mat:
                        if param == "OPAQUE" or param == "BLEND" or param == "HASHED" or param == "CLIP":
                            apply_alpha_override(obj, mat, param)
                        elif param == "SINGLE_SIDED":
                            apply_backface_culling(obj, mat, 1)
                        elif param == "DOUBLE_SIDED":
                            apply_backface_culling(obj, mat, 2)

            elif ob is not None and ob.type == "MESH" and ob.active_material_index <= len(ob.data.materials):
                mat = utils.context_material(context)
                if mat:
                    if param == "OPAQUE" or param == "BLEND" or param == "HASHED" or param == "CLIP":
                        apply_alpha_override(obj, mat, param)
                    elif param == "SINGLE_SIDED":
                        apply_backface_culling(obj, mat, 1)
                    elif param == "DOUBLE_SIDED":
                        apply_backface_culling(obj, mat, 2)

        elif obj.type == "ARMATURE":
            for child in obj.children:
                set_materials_setting(param, child, context, objects_processed)


def is_rl_material(mat):
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat)
    if bsdf_node and shader_node:
        return True
    return False


def reconstruct_material_cache(chr_cache, mat):
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat)
    if bsdf_node and shader_node:
        for shader_def in params.SHADER_MATRIX:
            shader_name = shader_def["name"]
            if f"({shader_name})" in shader_node.name:
                mat_cache = chr_cache.add_material_cache(mat)
                #input_defs = shader_def["inputs"]
                #for input_def in input_defs:
                #    socket_name = input_def[0]
                #    func = input_def[1]
                #    param_name = input_def[2]
                #    params = input_def[3:]
                return mat_cache
    return None




class CC3OperatorMaterial(bpy.types.Operator):
    """CC3 Material Functions"""
    bl_idname = "cc3.setmaterials"
    bl_label = "CC3 Material Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):

        props = vars.props()

        objects_processed = []
        if props.quick_set_mode == "OBJECT":
            for obj in bpy.context.selected_objects:
                set_materials_setting(self.param, obj, context, objects_processed)
        else:
            set_materials_setting(self.param, context.object, context, objects_processed)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "OPAQUE":
            return "Set blend mode of all selected objects with alpha channels to opaque"
        elif properties.param == "BLEND":
            return "Set blend mode of all selected objects with alpha channels to alpha blend"
        elif properties.param == "HASHED":
            return "Set blend mode of all selected objects with alpha channels to alpha hashed"
        elif properties.param == "CLIP":
            return "Set blend mode of all selected objects with alpha channels to alpha hashed"
        elif properties.param == "FETCH":
            return "Fetch the parameters from the selected objects"
        elif properties.param == "SINGLE_SIDED":
            return "Set material to be single sided, only visible from front facing"
        elif properties.param == "DOUBLE_SIDED":
            return "Set material to be double sided, visible from both sides"
        return ""