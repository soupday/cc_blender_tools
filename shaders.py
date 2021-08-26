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

from platform import node
import bpy
import math

from . import imageutils, jsonutils, materials, nodeutils, params, utils, vars


def get_prop_value(mat_cache, prop_name):
    parameters = mat_cache.parameters
    try:
        return eval("parameters." + prop_name, None, locals())
    except:
        return None


def exec_var_param(var_def, mat_cache, mat_json):
    try:
        parameters = mat_cache.parameters

        prop_name = var_def[0]
        default_value = var_def[1]
        func = var_def[2]
        args = var_def[3:]

        exec_expression = str(default_value)

        if mat_json:

            if func == "" or func == "=":
                # expression is json var value
                json_value = jsonutils.get_material_json_var(mat_json, args[0])
                if json_value is not None:
                    exec_expression = str(json_value)

            elif func != "DEF":
                # construct eval function code
                func_expression = func + "("
                first = True
                missing_args = False
                for arg in args:
                    if not first:
                        func_expression += ", "
                    first = False
                    arg_value = jsonutils.get_material_json_var(mat_json, arg)
                    if arg_value is None:
                        missing_args = True
                    func_expression += str(arg_value)
                func_expression += ")"
                if not missing_args:
                    exec_expression = func_expression

        exec_code = "parameters." + prop_name + " = " + exec_expression
        exec(exec_code, None, locals())
        utils.log_info("    Applying: " + exec_code)
    except:
        utils.log_error("exec_var_param(): error in expression: " + exec_code)
        utils.log_error(str(var_def))


def eval_input_param(input_def, mat_cache):
    try:
        parameters = mat_cache.parameters

        input_socket = input_def[0]
        func = input_def[1]
        args = input_def[2:]

        if func == "" or func == "=":
            # expression is mat_cache parameter
            exec_expression = "parameters." + args[0]

        else:
            # construct eval function code
            exec_expression = func + "("
            first = True
            for arg in args:
                if not first:
                    exec_expression += ", "
                first = False
                exec_expression += "parameters." + arg
            exec_expression += ")"

        return eval(exec_expression, None, locals())
    except:
        utils.log_error("eval_input_param(): error in expression: " + exec_expression)
        return None


def eval_tiling_param(texture_def, mat_cache):
    try:
        parameters = mat_cache.parameters

        func = texture_def[4]
        args = texture_def[5:]

        if func == "" or func == "=":
            # expression is mat_cache parameter
            exec_expression = "parameters." + args[0]

        else:
            # construct eval function code
            exec_expression = func + "("
            first = True
            for arg in args:
                if not first:
                    exec_expression += ", "
                first = False
                exec_expression += "parameters." + arg
            exec_expression += ")"

        return eval(exec_expression, None, locals())
    except:
        utils.log_error("eval_tiling_param(): error in expression: " + exec_expression)
        return None


def eval_prop(prop_name, mat_cache):
    try:
        parameters = mat_cache.parameters
        exec_expression = "parameters." + prop_name
        return eval(exec_expression, None, locals())
    except:
        utils.log_error("eval_prop(): error in expression: " + exec_expression)
        return None


def exec_prop(prop_name, mat_cache, value):
    try:
        parameters = mat_cache.parameters
        exec_expression = "parameters." + prop_name + " = " + str(value)
        exec(exec_expression, None, locals())
    except:
        utils.log_error("exec_prop(): error in expression: " + exec_expression)
        return None


def fetch_prop_defaults(mat_cache, mat_json):
    vars.block_property_update = True
    shader = params.get_shader_lookup(mat_cache)
    matrix_group = params.get_shader_def(shader)
    if matrix_group and "vars" in matrix_group.keys():
        for var_def in matrix_group["vars"]:
            exec_var_param(var_def, mat_cache, mat_json)
    vars.block_property_update = False


def apply_prop_matrix(node, mat_cache, shader_name):
    matrix_group = params.get_shader_def(shader_name)
    if matrix_group and "inputs" in matrix_group.keys():
        for input in matrix_group["inputs"]:
            if input[0] in node.inputs:
                prop_value = eval_input_param(input, mat_cache)
                if prop_value is not None:
                    nodeutils.set_node_input(node, input[0], prop_value)


def apply_basic_prop_matrix(node: bpy.types.Node, mat_cache, shader_name):
    matrix_group = params.get_shader_def(shader_name)
    if matrix_group and "inputs" in matrix_group.keys():
        for input in matrix_group["inputs"]:
            if input[0] in node.inputs:
                prop_value = eval_input_param(input, mat_cache)
                if prop_value is not None:
                    nodeutils.set_node_input(node, input[0], prop_value)


# Prop matrix eval, parameter conversion functions
#

def func_skin_sss(r):
    return r * vars.SKIN_SSS_RADIUS_SCALE

def func_eye_sss(r):
    return r * vars.EYE_SSS_RADIUS_SCALE

def func_hair_sss(r):
    return r * vars.HAIR_SSS_RADIUS_SCALE

def func_recip(v):
    return 1.0 / v

def func_emission_scale(v):
    return v * 100.0

def func_color_linear(jc: list):
    return [ jc[0] / 255.0, jc[1] / 255.0, jc[2] / 255.0, 1.0 ]

# Blender wants the colours in linear color space, but most of the color
# parameters in the json files are in sRGB, so they need to be converted...
# (Only the hair shader colors appear to be in linear color space.)
def func_color_srgb(jc: list):
    #return utils.srgb_to_linear(func_color_linear(jc))
    return func_color_linear(jc)

def func_color_vector(jc: list):
    if type(jc) == list:
        for i in range(0, len(jc)):
            jc[i] /= 255.0
    return jc

def func_occlusion_range(r, m):
    return utils.lerp(m, 1.0, r)

def func_occlusion_strength(s):
    return pow(s, 1.0 / 3.0)

def func_occlusion_color(c):
    return utils.lerp_color(c, (0,0,0,1), 0.75)

def func_one_minus(v):
    return 1.0 - v

def func_sqrt(v):
    return math.sqrt(v)

def func_corner_shadow_radius(v, u):
    # 0.3 -> 0.275 = 0.91, ln(0.275)/ln(0.3) = 1.0723
    # 0.13 -> 0.11 = 0.85,
    #t = utils.inverse_lerp(0.13, 0.3, v)
    #return utils.lerp(0.11, 0.275, t)
    return v * u

def func_iris_radius(v):
    #return 0.15 * (0.16 / v)
    return v

def func_iris_scale(v, u):
    return u * 0.16 / v

def func_scale_1000(v):
    return v / 1000.0

def func_scale_100(v):
    return v / 100.0

def func_scale_10(v):
    return v / 10.0

def func_scale_2(v):
    return v / 2.0

def func_scale_x10(v):
    return v * 10.0

def func_hair_ao(ao, occ):
    return (ao + occ) / 2.0

def func_limbus_dark_radius(limbus_dark_scale):
    t = utils.inverse_lerp(0.0, 10.0, limbus_dark_scale)
    return utils.lerp(0.155, 0.08, t)

def func_eye_depth(depth):
    return depth / 3.0

def func_index_1(values: list):
    return values[0] / 255.0

def func_index_2(values: list):
    return values[1] / 255.0

def func_index_3(values: list):
    return values[2] / 255.0

#
# End Prop matrix eval, parameter conversion functions

def set_image_node_tiling(nodes, links, node, mat_cache, texture_def, shader, tex_json):

    tex_type = texture_def[2]
    tiling_mode = "NONE"
    if len(texture_def) > 3:
        tiling_mode = texture_def[3]

    tiling = (1, 1, 1)
    offset = (0, 0, 0)

    # fetch any tiling and offset from the json data (if available)
    if tex_json:
        if "Tiling" in tex_json.keys():
            tiling = tex_json["Tiling"]
            if len(tiling) == 2:
                tiling.append(1)
            if tiling != [1,1,1]:
                tiling_mode = "OFFSET"

        if "Offset" in tex_json.keys():
            offset = tex_json["Offset"]
            if len(offset) == 2:
                offset.append(0)
            if offset != [0,0,0]:
                tiling_mode = "OFFSET"

    # evaluate any tiling parameter from the texture def
    if len(texture_def) > 5:
        tiling_value = eval_tiling_param(texture_def, mat_cache)
        if tiling_value is not None:
            tiling = (tiling_value, tiling_value, 1)

    node_name = "tiling_" + shader + "_" + tex_type + "_mapping"
    node_label = tex_type + " Mapping"
    location = node.location
    location = (location[0] - 900, location[1] - 100)

    if tiling_mode == "CENTERED":
        node_group = nodeutils.get_node_group("tiling_pivot_mapping")
        tiling_node = nodeutils.make_node_group_node(nodes, node_group, node_label, node_name)
        tiling_node.location = location
        nodeutils.set_node_input(tiling_node, "Tiling", tiling)
        nodeutils.set_node_input(tiling_node, "Pivot", (0.5, 0.5, 0))
        nodeutils.link_nodes(links, tiling_node, "Vector", node, "Vector")

    elif tiling_mode == "OFFSET":
        node_group = nodeutils.get_node_group("tiling_offset_mapping")
        tiling_node = nodeutils.make_node_group_node(nodes, node_group, node_label, node_name)
        tiling_node.location = location
        nodeutils.set_node_input(tiling_node, "Tiling", tiling)
        nodeutils.set_node_input(tiling_node, "Offset", offset)
        nodeutils.link_nodes(links, tiling_node, "Vector", node, "Vector")


def set_shader_input_props(shader_def, mat_cache, socket, value):
    """Look up and set the properties for the shader inputs.
    """

    for texture_def in shader_def["inputs"]:
        if texture_def[0] == socket:
            props = texture_def[2:]
            for prop in props:
                vars.block_property_update = True
                exec_prop(prop, mat_cache, value)
                vars.block_property_update = False


def apply_texture_matrix(nodes, links, node, mat, mat_cache, shader_name, mat_json, obj):
    shader_def = params.get_shader_def(shader_name)
    location = node.location
    x = location[0] - 600
    y = location[1] + 300
    c = 0
    image_nodes = []

    if shader_def and "textures" in shader_def.keys():

        for shader_input in node.inputs:
            for texture_def in shader_def["textures"]:
                socket_name = texture_def[0]
                if socket_name == shader_input.name:
                    alpha_socket_name = texture_def[1]
                    tex_type = texture_def[2]

                    json_id = imageutils.get_image_type_json_id(tex_type)
                    tex_json = jsonutils.get_texture_info(mat_json, json_id)
                    image_id = "(" + tex_type + ")"

                    image = imageutils.find_material_image(mat, tex_type, tex_json)
                    image_node = nodeutils.get_node_by_id(nodes, image_id)

                    if image_node and image_node.image and image:
                        if image != image_node.image:
                            utils.log_info("Replacing image node image with: " + image.name)
                            image_node.image = image

                    if len(texture_def) == 5 and texture_def[3] == "SAMPLE":
                        # SAMPLE is a special case where the texture is sampled into a color value property:
                        # e.g Vertex Color sampled into hair_vertex_color

                        if image == None or len(obj.data.vertex_colors) == 0:
                            # if there is no sample map, set it's corresponding strength properties to zero:
                            # e.g. Vertex Color uses Vertex Color Strength with props: hair_vertex_color_strength
                            strength_socket_name = socket_name + " Strength"
                            nodeutils.set_node_input(node, strength_socket_name, 0.0)
                            set_shader_input_props(shader_def, mat_cache, strength_socket_name, 0.0)

                        else:
                            vars.block_property_update = True
                            sample_prop = texture_def[4]
                            sample_color = [image.pixels[0], image.pixels[1], image.pixels[2], 1.0]
                            exec_prop(sample_prop, mat_cache, sample_color)
                            nodeutils.set_node_input(node, socket_name, sample_color)
                            bpy.data.images.remove(image)
                            vars.block_property_update = False

                    elif image:

                        if not image_node:
                            image_node = nodeutils.make_image_node(nodes, image, image_id)

                        image_node.location = (x, y)
                        y += 100
                        x -= 300
                        c += 1
                        if c == 3:
                            c = 0
                            x += 900
                            y -= 700

                        set_image_node_tiling(nodes, links, image_node, mat_cache, texture_def,
                                            shader_name, tex_json)

                        if socket_name:
                            if tex_type == "ALPHA" and "_diffuse" in image.name.lower():
                                nodeutils.link_nodes(links, image_node, "Alpha", node, socket_name)
                            else:
                                nodeutils.link_nodes(links, image_node, "Color", node, socket_name)

                        if alpha_socket_name:
                            nodeutils.link_nodes(links, image_node, "Alpha", node, alpha_socket_name)

                    if image_node and image_node.image:
                        image_nodes.append(image_node)

    # remove any extra image nodes:
    for n in nodes:
        if n.type == "TEX_IMAGE" and n not in image_nodes:
            utils.log_info("Removing unused image node: " + n.name)
            nodes.remove(n)

    return


def connect_tearline_shader(obj, mat, mat_json):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = props.get_object_cache(obj)
    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Tearline Shader"
    shader_name = "rl_tearline_shader"
    shader_group = "rl_tearline_shader"

    shader = nodeutils.reset_shader(nodes, links, shader_label, shader_name, shader_group)

    apply_prop_matrix(shader, mat_cache, shader_name)

    nodeutils.clean_unused_image_nodes(nodes)

    materials.set_material_alpha(mat, "BLEND")
    mat.shadow_method = "NONE"


def connect_eye_occlusion_shader(obj, mat, mat_json):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = props.get_object_cache(obj)
    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Eye Occlusion Shader"
    shader_name = "rl_eye_occlusion_shader"
    shader_group = "rl_eye_occlusion_shader"

    shader = nodeutils.reset_shader(nodes, links, shader_label, shader_name, shader_group)

    apply_prop_matrix(shader, mat_cache, shader_name)

    nodeutils.clean_unused_image_nodes(nodes)

    materials.set_material_alpha(mat, "BLEND")
    mat.shadow_method = "NONE"


def connect_skin_shader(obj, mat, mat_json):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = props.get_object_cache(obj)
    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    if mat_cache.is_head():
        shader_label = "Skin Head Shader"
        shader_name = "rl_head_shader"
        shader_group = "rl_head_shader"
    elif mat_cache.is_body():
        shader_label = "Skin Body Shader"
        shader_name = "rl_skin_shader"
        shader_group = "rl_skin_shader"
    elif mat_cache.is_arm():
        shader_label = "Skin Arm Shader"
        shader_name = "rl_skin_shader"
        shader_group = "rl_skin_shader"
    else: #if mat_cache.is_leg():
        shader_label = "Skin Leg Shader"
        shader_name = "rl_skin_shader"
        shader_group = "rl_skin_shader"

    shader = nodeutils.reset_shader(nodes, links, shader_label, shader_name, shader_group)

    nodeutils.reset_cursor()

    # use shader_group here instead of shader_name
    apply_prop_matrix(shader, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, shader, mat, mat_cache, shader_name, mat_json, obj)

    nodeutils.clean_unused_image_nodes(nodes)

    materials.set_material_alpha(mat, "OPAQUE")


def connect_tongue_shader(obj, mat, mat_json):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = props.get_object_cache(obj)
    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Tongue Shader"
    shader_name = "rl_tongue_shader"
    shader_group = "rl_tongue_shader"

    shader = nodeutils.reset_shader(nodes, links, shader_label, shader_name, shader_group)

    apply_prop_matrix(shader, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, shader, mat, mat_cache, shader_name, mat_json, obj)

    nodeutils.clean_unused_image_nodes(nodes)

    materials.set_material_alpha(mat, "OPAQUE")


def connect_teeth_shader(obj, mat, mat_json):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = props.get_object_cache(obj)
    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Teeth Shader"
    shader_name = "rl_teeth_shader"
    shader_group = "rl_teeth_shader"

    shader = nodeutils.reset_shader(nodes, links, shader_label, shader_name, shader_group)

    apply_prop_matrix(shader, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, shader, mat, mat_cache, shader_name, mat_json, obj)

    if mat_cache.is_upper_teeth():
        nodeutils.set_node_input(shader, "Is Upper Teeth", 1.0)
    else:
        nodeutils.set_node_input(shader, "Is Upper Teeth", 0.0)

    nodeutils.clean_unused_image_nodes(nodes)

    materials.set_material_alpha(mat, "OPAQUE")


def connect_eye_shader(obj, mat, obj_json, mat_json):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    obj_cache = props.get_object_cache(obj)
    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # to build eye materials we need some textures from the cornea:
    cornea_mat = mat
    cornea_mat_cache = mat_cache
    cornea_json = mat_json
    # the eye mesh uses textures and settings from the cornea:
    if mat_cache.is_eye():
        cornea_mat, cornea_mat_cache = materials.get_cornea_mat(obj, mat, mat_cache)
        cornea_json = jsonutils.get_material_json(obj_json, cornea_mat)

    if mat_cache.is_cornea():
        if prefs.refractive_eyes:
            shader_label = "Cornea Shader"
            shader_name = "rl_cornea_shader"
            shader_group = "rl_cornea_refractive_shader"
        else:
            shader_label = "Cornea Shader"
            shader_name = "rl_cornea_shader"
            shader_group = "rl_cornea_shader"
    else:
        shader_label = "Eye Shader"
        shader_name = "rl_eye_shader"
        shader_group = "rl_eye_shader"

    shader_node = nodeutils.reset_shader(nodes, links, shader_label, shader_name, shader_group)

    apply_prop_matrix(shader_node, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, shader_node, cornea_mat, cornea_mat_cache, shader_name, cornea_json, obj)

    nodeutils.clean_unused_image_nodes(nodes)

    if mat_cache.is_cornea():
        if prefs.refractive_eyes:
            materials.set_material_alpha(mat, "OPAQUE")
            mat.use_screen_refraction = True
            mat.refraction_depth = mat_cache.parameters.eye_refraction_depth / 1000
        else:
            materials.set_material_alpha(mat, "BLEND")
            mat.use_screen_refraction = False
    else:
        materials.set_material_alpha(mat, "OPAQUE")


def connect_hair_shader(obj, mat, mat_json):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = props.get_object_cache(obj)
    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Hair Shader"
    shader_name = "rl_hair_shader"
    shader_group = "rl_hair_shader"

    shader = nodeutils.reset_shader(nodes, links, shader_label, shader_name, shader_group)

    apply_prop_matrix(shader, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, shader, mat, mat_cache, shader_name, mat_json, obj)

    nodeutils.clean_unused_image_nodes(nodes)

    materials.set_material_alpha(mat, "HASHED")
    mat.use_sss_translucency = True



def connect_pbr_shader(obj, mat, mat_json):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = props.get_object_cache(obj)
    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Pbr Shader"
    shader_name = "rl_pbr_shader"
    shader_group = "rl_pbr_shader"

    shader = nodeutils.reset_shader(nodes, links, shader_label, shader_name, shader_group)

    apply_prop_matrix(shader, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, shader, mat, mat_cache, shader_name, mat_json, obj)

    nodeutils.clean_unused_image_nodes(nodes)

    if mat_cache.is_eyelash():
        materials.set_material_alpha(mat, "HASHED")
        nodeutils.set_node_input(shader, "Specular Scale", 0.25)
    if mat_cache.is_scalp():
        materials.set_material_alpha(mat, "HASHED")
        nodeutils.set_node_input(shader, "Specular Scale", 0)
        #nodeutils.set_node_input(shader, "Opacity", 0.65)
    else:
        if nodeutils.has_connected_input(shader, "Alpha Map"):
            materials.set_material_alpha(mat, "HASHED")


def connect_sss_shader(obj, mat, mat_json):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = props.get_object_cache(obj)
    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "SSS Shader"
    shader_name = "rl_sss_shader"
    shader_group = "rl_sss_shader"

    shader = nodeutils.reset_shader(nodes, links, shader_label, shader_name, shader_group)

    apply_prop_matrix(shader, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, shader, mat, mat_cache, shader_name, mat_json, obj)

    nodeutils.clean_unused_image_nodes(nodes)

    if nodeutils.has_connected_input(shader, "Alpha Map"):
        materials.set_material_alpha(mat, "HASHED")


