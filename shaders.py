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

import bpy
import math
import os
from mathutils import Vector, Color

from . import imageutils, jsonutils, meshutils, materials, modifiers, wrinkle, nodeutils, params, lib, utils, vars


def get_prop_value(mat_cache, prop_name):
    parameters = mat_cache.parameters
    try:
        return eval("parameters." + prop_name, None, locals())
    except:
        return None


def eval_texture_rules(tex_type):
    prefs = vars.prefs()

    if tex_type in params.TEXTURE_RULES:
        tex_rule = params.TEXTURE_RULES[tex_type]
        try:
            return eval(tex_rule, None, locals())
        except:
            return False
    else:
        return True


def exec_var_param(var_def, mat_cache, mat_json):
    try:
        parameters = mat_cache.parameters

        prop_name = var_def[0]
        default_value = var_def[1]
        func = var_def[2]
        args = var_def[3:]

        if type(default_value) is list:
            material_type = jsonutils.get_json(mat_json, "Material Type")
            if material_type == "Tra":
                default_value = default_value[1]
            else:
                default_value = default_value[0]

        exec_expression = str(default_value)

        if mat_json:

            if func == "" or func == "=":
                # expression is json var value
                json_value = jsonutils.get_material_json_var(mat_json, args[0])
                if json_value is not None:
                    exec_expression = str(json_value)

            elif func != "DEF" and not args:
                exec_expression = func + f"({default_value})"

            elif func != "DEF" and args:
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
        utils.log_info("Applying: " + exec_code)
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


def eval_tiling_param(texture_def, mat_cache, start_index = 4):
    try:
        parameters = mat_cache.parameters

        func = texture_def[start_index]
        args = texture_def[start_index + 1:]

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


def eval_parameters_func(parameters, func, args, default = None):
    try:
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
        utils.log_error("eval_parameters_func(): error in expression: " + exec_expression)
        return default


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


def fetch_prop_defaults(obj, mat_cache, mat_json):
    vars.block_property_update = True
    shader = params.get_shader_name(mat_cache)
    matrix_group = params.get_shader_def(shader)
    if matrix_group and "vars" in matrix_group.keys():
        for var_def in matrix_group["vars"]:
            exec_var_param(var_def, mat_cache, mat_json)
    if shader == "rl_hair_shader":
        check_legacy_hair(obj, mat_cache, mat_json)
    #if mat_cache.get_base_name() in vars.GAME_BASE_SKIN_NAMES:
    #    mat_cache.parameters.default_roughness_power = 0.75
    vars.block_property_update = False


def check_legacy_hair(obj, mat_cache, mat_json):
    root_map_path = None
    id_map_path = None
    flow_map_path = None

    try:
        root_map_path = mat_json["Custom Shader"]["Image"]["Hair Root Map"]["Texture Path"]
    except:
        pass

    try:
        id_map_path = mat_json["Custom Shader"]["Image"]["Hair ID Map"]["Texture Path"]
    except:
        pass

    try:
        flow_map_path = mat_json["Custom Shader"]["Image"]["Hair Flow Map"]["Texture Path"]
    except:
        pass

    if not meshutils.has_vertex_color_data(obj):
        mat_cache.parameters.hair_vertex_color_strength = 0.0

    # if hair does not have a root map or id map or flow map, then it is (probably) legacy and needs adjusting
    if not root_map_path and not id_map_path and not flow_map_path:
        mat_cache.parameters.hair_enable_color = 0.0
        mat_cache.parameters.hair_vertex_color_strength = 0.0
        mat_cache.parameters.hair_specular_blend = 1.0
        mat_cache.parameters.hair_anisotropic_roughness = 0.05
        mat_cache.parameters.hair_anisotropic_strength = 0.15
        mat_cache.parameters.hair_anisotropic_strength2 = 0.15

    return


def apply_prop_matrix(bsdf_node, group_node, mat_cache, shader_name):
    matrix_group = params.get_shader_def(shader_name)

    if group_node and matrix_group and "inputs" in matrix_group.keys():
        for input_def in matrix_group["inputs"]:
            socket_name = input_def[0]
            socket = nodeutils.input_socket(group_node, socket_name)
            if socket:
                prop_value = eval_input_param(input_def, mat_cache)
                if prop_value is not None:
                    nodeutils.set_node_input_value(group_node, socket, prop_value)

    if bsdf_node and matrix_group and "bsdf" in matrix_group.keys():
        bsdf_nodes = nodeutils.get_custom_bsdf_nodes(bsdf_node)
        for input_def in matrix_group["bsdf"]:
            socket_name = input_def[0]
            for n in bsdf_nodes:
                socket = nodeutils.input_socket(n, socket_name)
                if socket:
                    prop_value = eval_input_param(input_def, mat_cache)
                    if prop_value is not None:
                        nodeutils.set_node_input_value(n, socket, prop_value)


def apply_basic_prop_matrix(node: bpy.types.Node, mat_cache, shader_name):
    matrix_group = params.get_shader_def(shader_name)
    if matrix_group and "inputs" in matrix_group.keys():
        for input_def in matrix_group["inputs"]:
            socket_name = input_def[0]
            socket = nodeutils.input_socket(node, socket_name)
            if socket:
                prop_value = eval_input_param(input_def, mat_cache)
                if prop_value is not None:
                    nodeutils.set_node_input_value(node, socket, prop_value)


# Prop matrix eval, parameter conversion functions
#

def func_iris_brightness(v):
    prefs = vars.prefs()
    if prefs.render_target == "CYCLES" and prefs.refractive_eyes == "SSR":
        if utils.B410():
            v = v * prefs.cycles_ssr_iris_brightness_b410
        else:
            v = v * prefs.cycles_ssr_iris_brightness_b341
    elif prefs.render_target == "EEVEE" and prefs.refractive_eyes == "SSR":
        if utils.B420():
            v = v * prefs.eevee_ssr_iris_brightness_b420
        else:
            v = v * prefs.eevee_ssr_iris_brightness_b341
    return v

def func_sss_skin(s):
    prefs = vars.prefs()
    if prefs.render_target == "CYCLES":
        if utils.B400():
            s = s * prefs.cycles_sss_skin_b410
        else:
            s = s * prefs.cycles_sss_skin_b341
    else:
        if utils.B420():
            s = s * prefs.eevee_sss_skin_b420
        else:
            s = s * prefs.eevee_sss_skin_b341
    return s

def func_sss_hair(s):
    prefs = vars.prefs()
    if prefs.render_target == "CYCLES":
        if utils.B400():
            s = s * prefs.cycles_sss_hair_b410
        else:
            s = s * prefs.cycles_sss_hair_b341
    else:
        if utils.B420():
            s = s * prefs.eevee_sss_hair_b420
        else:
            s = s * prefs.eevee_sss_hair_b341
    return s

def func_sss_teeth(s):
    prefs = vars.prefs()
    if prefs.render_target == "CYCLES":
        if utils.B400():
            s = s * prefs.cycles_sss_teeth_b410
        else:
            s = s * prefs.cycles_sss_teeth_b341
    else:
        if utils.B420():
            s = s * prefs.eevee_sss_teeth_b420
        else:
            s = s * prefs.eevee_sss_teeth_b341
    return s

def func_sss_tongue(s):
    prefs = vars.prefs()
    if prefs.render_target == "CYCLES":
        if utils.B400():
            s = s * prefs.cycles_sss_tongue_b410
        else:
            s = s * prefs.cycles_sss_tongue_b341
    else:
        if utils.B420():
            s = s * prefs.eevee_sss_tongue_b420
        else:
            s = s * prefs.eevee_sss_tongue_b341
    return s

def func_sss_eyes(s):
    prefs = vars.prefs()
    if prefs.render_target == "CYCLES":
        if utils.B400():
            s = s * prefs.cycles_sss_eyes_b410
        else:
            s = s * prefs.cycles_sss_eyes_b341
    else:
        if utils.B420():
            s = s * prefs.eevee_sss_eyes_b420
        else:
            s = s * prefs.eevee_sss_eyes_b341
    return s

def func_sss_default(s):
    prefs = vars.prefs()
    if prefs.render_target == "CYCLES":
        if utils.B400():
            s = s * prefs.cycles_sss_default_b410
        else:
            s = s * prefs.cycles_sss_default_b341
    else:
        if utils.B420():
            s = s * prefs.eevee_sss_default_b420
        else:
            s = s * prefs.eevee_sss_default_b341
    return s

def func_sss_falloff_saturated(f, s):
    falloff = Color((f[0], f[1], f[2]))
    falloff.s *= s
    return [falloff.r, falloff.g, falloff.b, 1.0]

def func_sss_radius_eyes_cycles(r):
    prefs = vars.prefs()
    r = r * vars.EYES_SSS_RADIUS_SCALE
    return r

def func_sss_radius_eyes_eevee(r, f):
    prefs = vars.prefs()
    r = r * vars.EYES_SSS_RADIUS_SCALE
    return [f[0] * r, f[1] * r, f[2] * r]

def func_sss_radius_hair_cycles(r):
    prefs = vars.prefs()
    r = r * vars.HAIR_SSS_RADIUS_SCALE
    return r

def func_sss_radius_hair_eevee(r, f, s):
    prefs = vars.prefs()
    r = r * vars.HAIR_SSS_RADIUS_SCALE
    falloff = Color((f[0], f[1], f[2]))
    falloff.s *= s
    return [falloff.r * r, falloff.g * r, falloff.b * r]

def func_sss_radius_teeth_eevee(r, f):
    prefs = vars.prefs()
    r = r * vars.TEETH_SSS_RADIUS_SCALE
    return [f[0] * r, f[1] * r, f[2] * r]

def func_sss_radius_tongue_eevee(r, f):
    prefs = vars.prefs()
    r = r * vars.TONGUE_SSS_RADIUS_SCALE
    return [f[0] * r, f[1] * r, f[2] * r]

def func_sss_radius_default_eevee(r, f):
    prefs = vars.prefs()
    r = r * vars.DEFAULT_SSS_RADIUS_SCALE
    return [f[0] * r, f[1] * r, f[2] * r]

def func_sss_radius_skin_cycles(r):
    prefs = vars.prefs()
    r = r * vars.SKIN_SSS_RADIUS_SCALE
    #if utils.B400():
    #    r *= 2/3
    return r

def func_sss_radius_skin_eevee(r, f, s):
    prefs = vars.prefs()
    r = r * vars.SKIN_SSS_RADIUS_SCALE
    falloff = Color((f[0], f[1], f[2]))
    falloff.s *= s
    return [falloff.r * r, falloff.g * r, falloff.b * r]

def func_roughness_power(p):
    prefs = vars.prefs()
    #if prefs.build_skin_shader_dual_spec:
    #    return p * 1.0
    #else:
    #    return p
    if prefs.render_target == "CYCLES":
        if utils.B410():
            return p * prefs.cycles_roughness_power_b410
        else:
            return p * prefs.cycles_roughness_power_b341
    else:
        if utils.B420():
            return p * prefs.eevee_roughness_power_b420
        else:
            return p * prefs.eevee_roughness_power_b341

def func_a(a, b, c):
    return a

def func_b(a, b, c):
    return b

def func_b(a, b, c):
    return c

def func_mul(a, b):
    return a * b

def func_tiling(scale):
    return 1.0 / scale

def func_emission_scale(v):
    return v * vars.EMISSION_SCALE

def func_color_bytes(jc: list):
    return [ jc[0] / 255.0, jc[1] / 255.0, jc[2] / 255.0, 1.0 ]

def func_color_vector(jc: list):
    if type(jc) == list:
        for i in range(0, len(jc)):
            jc[i] /= 255.0
    return jc

def func_export_byte3(c):
    return [c[0] * 255.0, c[1] * 255.0, c[2] * 255.0]

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

def func_pow_2(v):
    return math.pow(v, 2.0)

def func_sclera_brightness(b):
    prefs = vars.prefs()
    if prefs.render_target == "CYCLES":
        b *= 1.0
    return b

def func_iris_scale(i):
    return i * 1.00

def func_parallax_iris_scale(i, s):
    return (func_iris_scale(i) * s)

def func_parallax_iris_tiling(i, s):
    return 1.0 / (func_parallax_iris_scale(i, s))

def func_get_iris_scale(iris_uv_radius):
    return 0.16 / iris_uv_radius

def func_half(s):
    return s * 0.5

def func_third(s):
    return s * 0.3333

def func_two_third(s):
    return s * 0.6666

def func_divide_1000(v):
    return v / 1000.0

def func_divide_100(v):
    return v / 100.0

def func_divide_200(v):
    return v / 200.0

def func_divide_2(v):
    return v / 2.0

def func_mul_1000(v):
    return v * 1000.0

def func_mul_100(v):
    return v * 100.0

def func_mul_2(v):
    return v * 2.0

def func_limbus_dark_radius(limbus_dark_scale):
    #return 1 / limbus_dark_scale
    #t = utils.inverse_lerp(0.0, 10.0, limbus_dark_scale)
    #return utils.lerp(0.155, 0.08, t) + 0.025
    limbus_dark_scale = max(limbus_dark_scale, 0.01)
    ds = pow(0.01, 0.2) / limbus_dark_scale
    dm = pow(0.5, 0.2) / limbus_dark_scale
    de = dm + (dm - ds)
    return de

def func_limbus_dark_width(limbus_dark_scale):
    #return 1 / limbus_dark_scale
    #t = utils.inverse_lerp(0.0, 10.0, limbus_dark_scale)
    #return utils.lerp(0.155, 0.08, t) + 0.025
    limbus_dark_scale = max(limbus_dark_scale, 0.01)
    ds = pow(0.01, 0.2) / limbus_dark_scale
    dm = pow(0.5, 0.2) / limbus_dark_scale
    de = dm + (dm - ds)
    return ds / de

def func_export_limbus_dark_scale(ldr):
    #return 1 / limbus_dark_radius
    #t = utils.inverse_lerp(0.155, 0.08, limbus_dark_radius - 0.025)
    #return utils.clamp(utils.lerp(0.0, 10.0, t), 0, 10)
    M = pow(0.5, 0.2)
    S = pow(0.01, 0.2)
    lds = (2 * M - S) / ldr
    return lds

def func_brightness(b):
    """Shader brightness adjust"""
    if b <= 1.0:
        return b
    B = (b - 1)*4 + 1
    return B

def func_export_brightness(B):
    """Shader brightness adjust"""
    if B <= 1.0:
        return B
    b = (B - 1)/4 + 1
    return b

def func_saturation(s):
    """Shader saturation adjust"""
    if s <= 1.0:
        return s
    S = (s - 1)*3 + 1
    return S

def func_export_saturation(S):
    """Shader saturation adjust"""
    if S <= 1.0:
        return S
    s = (S - 1)/3 + 1
    return s

def func_brightness_mod(b):
    """Brightness adjust to be used directly in modify color BCHS"""
    B = (b - 1)*5 + 1
    return B

def func_export_brightness_mod(B):
    """Brightness adjust to be used directly in modify color BCHS"""
    b = (B - 1)/5 + 1
    return b

def func_saturation_mod(s):
    """Saturation adjust to be used directly in modify color BCHS"""
    S = (s - 1)*3 + 1
    return S

def func_export_saturation_mod(S):
    """Saturation adjust to be used directly in modify color BCHS"""
    s = (S - 1)/3 + 1

    return s

def func_get_eye_depth(depth):
    return (depth / 3.0)

def func_export_eye_depth(depth):
    return (depth) * 3.0

def func_set_eye_depth(depth):
    return depth * 1.5

def func_set_parallax_iris_depth(depth):
    return depth * 1.5

def func_index_1(values: list):
    return values[0] / 255.0

def func_index_2(values: list):
    return values[1] / 255.0

def func_index_3(values: list):
    return values[2] / 255.0

def func_export_combine_xyz(x, y, z):
    return [x * 255.0, y * 255.0, z * 255.0]

def func_normal_strength(s):
    prefs = vars.prefs()
    if prefs.render_target == "CYCLES":
        if utils.B400():
            s = s * prefs.cycles_normal_b410
        else:
            s = s * prefs.cycles_normal_b341
    else:
        if utils.B420():
            s = s * prefs.eevee_normal_b420
        else:
            s = s * prefs.eevee_normal_b341
    return s

def func_skin_normal_strength(s):
    prefs = vars.prefs()
    if prefs.render_target == "CYCLES":
        if utils.B400():
            s = s * prefs.cycles_normal_skin_b410
        else:
            s = s * prefs.cycles_normal_skin_b341
    else:
        if utils.B420():
            s = s * prefs.eevee_normal_skin_b420
        else:
            s = s * prefs.eevee_normal_skin_b341
    return s

def func_micro_normal_strength(s):
    prefs = vars.prefs()
    if prefs.render_target == "CYCLES":
        if utils.B400():
            s = s * prefs.cycles_micro_normal_b410
        else:
            s = s * prefs.cycles_micro_normal_b341
    else:
        if utils.B420():
            s = s * prefs.eevee_micro_normal_b420
        else:
            s = s * prefs.eevee_micro_normal_b341
    return s

#
# End Prop matrix eval, parameter conversion functions

def set_image_node_tiling(nodes, links, node, mat_cache, texture_def, shader, tex_json):
    prefs = vars.prefs()

    tex_type = texture_def[2]
    tiling_mode = "NONE"
    if len(texture_def) > 3:
        tiling_mode = texture_def[3]

    tiling = (1, 1, 1)
    offset = (0, 0, 0)
    rotation = (0, 0, 0)

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
    elif mat_cache:
        for tex_mapping in mat_cache.texture_mappings:
            if tex_mapping:
                if tex_mapping.image == node.image:
                    tiling = tex_mapping.scale
                    offset = tex_mapping.location
                    rotation = tex_mapping.rotation
                    tiling_mode = "OFFSET"
                    break

    # evaluate any tiling parameter from the texture def
    if len(texture_def) > 5:
        tiling_value = eval_tiling_param(texture_def, mat_cache)
        if tiling_value is not None:
            tiling = (tiling_value, tiling_value, 1)

    node_name = "tiling_" + shader + "_" + tex_type + "_mapping"
    node_label = tex_type + " Mapping"
    location = node.location
    location = (location[0] - 900, location[1] - 100)

    if tiling_mode == "EYE_PARALLAX":
        if prefs.refractive_eyes == "SSR" or mat_cache.is_eye():
            tiling_mode = "CENTERED"

    if tiling_mode == "CENTERED":
        node_group = lib.get_node_group("tiling_pivot_mapping")
        tiling_node = nodeutils.make_node_group_node(nodes, node_group, node_label, node_name)
        tiling_node.location = location
        nodeutils.set_node_input_value(tiling_node, "Tiling", tiling)
        nodeutils.set_node_input_value(tiling_node, "Pivot", (0.5, 0.5, 0))
        nodeutils.link_nodes(links, tiling_node, "Vector", node, "Vector")

    elif tiling_mode == "OFFSET":
        node_group = lib.get_node_group("tiling_offset_mapping")
        tiling_node = nodeutils.make_node_group_node(nodes, node_group, node_label, node_name)
        tiling_node.location = location
        nodeutils.set_node_input_value(tiling_node, "Tiling", tiling)
        nodeutils.set_node_input_value(tiling_node, "Offset", offset)
        nodeutils.link_nodes(links, tiling_node, "Vector", node, "Vector")

    elif tiling_mode == "EYE_PARALLAX":
        node_group = lib.get_node_group("tiling_cornea_parallax_mapping")
        mapping_node = nodeutils.make_node_group_node(nodes, node_group, node_label, node_name)
        mapping_node.location = location
        nodeutils.link_nodes(links, mapping_node, "Vector", node, "Vector")
        shader_name = params.get_shader_name(mat_cache)
        shader_def = params.get_shader_def(shader_name)
        if "mapping" in shader_def.keys():
            mapping_defs = shader_def["mapping"]
            for mapping_def in mapping_defs:
                if len(mapping_def) > 1:
                    socket_name = mapping_def[1]
                    nodeutils.set_node_input_value(mapping_node, socket_name, eval_tiling_param(mapping_def, mat_cache, 2))


def init_character_property_defaults(chr_cache, chr_json, only:list=None):
    prefs = vars.prefs()
    processed = []

    utils.log_info("")
    utils.log_info("Initializing Material Property Defaults:")
    utils.log_info("----------------------------------------")
    if chr_json:
        utils.log_info("(Using Json Data)")
    else:
        utils.log_info("(No Json Data)")

    # Advanced properties
    for obj in chr_cache.get_cache_objects():
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and not obj_cache.disabled and obj_cache.is_mesh() and obj not in processed:
            processed.append(obj)

            obj_json = jsonutils.get_object_json(chr_json, obj)
            utils.log_info("Object: " + obj.name + " (" + obj_cache.object_type + ")")
            utils.log_indent()

            for mat in obj.data.materials:
                if only and mat not in only: continue
                if mat and mat not in processed:
                    processed.append(mat)

                    mat_cache = chr_cache.get_material_cache(mat)
                    if mat_cache and not mat_cache.user_added:

                        mat_json = jsonutils.get_material_json(obj_json, mat)
                        utils.log_info("Material: " + mat.name + " (" + mat_cache.material_type + ")")
                        utils.log_indent()

                        if mat_cache.is_eye():
                            cornea_mat, cornea_mat_cache = materials.get_cornea_mat(obj, mat, mat_cache)
                            if cornea_mat:
                                mat_json = jsonutils.get_material_json(obj_json, cornea_mat)

                        fetch_prop_defaults(obj, mat_cache, mat_json)

                        if chr_json is None and chr_cache.is_actor_core():
                            try:
                                mat_cache.parameters.default_ao_strength = 0.4
                                mat_cache.parameters.default_ao_power = 1.0
                                mat_cache.parameters.default_specular_scale = 0.4
                            except:
                                pass

                        if mat_cache.source_name.startswith("Ga_Skin_"):
                            try:
                                if prefs.render_target == "EEVEE":
                                    mat_cache.parameters.default_roughness_power = 0.5
                                else:
                                    mat_cache.parameters.default_roughness_power = 0.75
                            except:
                                pass

                        utils.log_recess()
            utils.log_recess()


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


def apply_texture_matrix(nodes, links, shader_node,
                         mat, mat_cache, shader_name, mat_json,
                         obj, processed_images,
                         offset = Vector((0,0)), sub_shader = False, textures = None):

    if textures is None:
        textures = {}

    shader_def = params.get_shader_def(shader_name)
    location = shader_node.location
    x = location[0] - 600 + offset.x
    y = location[1] + 300 + offset.y
    c = 0
    image_nodes = []

    if shader_def and "textures" in shader_def.keys():

        for shader_input in shader_node.inputs:

            for texture_def in shader_def["textures"]:

                socket_name = texture_def[0]

                if socket_name == shader_input.name:

                    alpha_socket_name = texture_def[1]
                    tex_type = texture_def[2]
                    is_lib = imageutils.is_library_tex(tex_type)

                    sample_map = len(texture_def) > 3 and texture_def[3] == "SAMPLE"

                    # check texture rules, if we should connect this texture at all
                    if not eval_texture_rules(tex_type):
                        continue

                    # there is no need to sample vertex colors for hair if there is Json Data present
                    if mat_json and sample_map and tex_type == "HAIRVERTEXCOLOR":
                        continue

                    json_id = imageutils.get_image_type_json_id(tex_type)
                    tex_json = jsonutils.get_texture_info(mat_json, json_id)
                    tex_path = None
                    suffix = None
                    image_id = "(" + tex_type + ")"
                    image_node = nodeutils.get_node_by_id(nodes, image_id)

                    # if using json, assume if no tex_json then there is no texture in this socket
                    # this should prevent rogue diffuse alpha channels getting set into alpha channels
                    # (The FBX import will do this)
                    if not is_lib and mat_json and not tex_json:
                        continue

                    # for user added materials, don't mess with the users textures...
                    image = None
                    if image_node and image_node.image and mat_cache.user_added:
                        image = image_node.image
                    elif tex_type == "HAIRVERTEXCOLOR" or tex_type == "WEIGHTMAP" or tex_type == "COLORID" or tex_type == "RGBMASK":
                        image = imageutils.find_material_image(mat, tex_type, processed_images, tex_json)
                    else:
                        image = imageutils.find_material_image(mat, tex_type, processed_images, tex_json, mat_json)

                    if image_node and image_node.image and image:
                        if image != image_node.image:
                            utils.log_info("Replacing image node image with: " + image.name)
                            image_node.image = image

                    try:
                        if image and image.filepath:
                            tex_path = image.filepath
                        else:
                            tex_path = tex_json["Texture Path"]
                        suffix = os.path.splitext(os.path.basename(tex_path))[0].split("_")[-1]
                    except:
                        tex_path = ""
                        suffix = ""

                    if sample_map:
                        # SAMPLE is a special case where the texture is sampled into a color value property:
                        # e.g Vertex Color sampled into hair_vertex_color

                        if image == None or len(obj.data.vertex_colors) == 0:
                            # if there is no sample map, set it's corresponding strength properties to zero:
                            # e.g. Vertex Color uses Vertex Color Strength with props: hair_vertex_color_strength
                            strength_socket_name = socket_name + " Strength"
                            nodeutils.set_node_input_value(shader_node, strength_socket_name, 0.0)
                            set_shader_input_props(shader_def, mat_cache, strength_socket_name, 0.0)

                        else:
                            vars.block_property_update = True
                            sample_prop = texture_def[4]
                            sample_color = [image.pixels[0], image.pixels[1], image.pixels[2], 1.0]
                            exec_prop(sample_prop, mat_cache, sample_color)
                            nodeutils.set_node_input_value(shader_node, socket_name, sample_color)
                            utils.log_detail(f"Sample Map Removing Image: {image}")
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

                        # ensure bump maps are connected to the correct socket
                        if socket_name == "Normal Map" and suffix and suffix.lower() == "bump":
                            socket_name = "Bump Map"

                        if socket_name:
                            if tex_type == "ALPHA" and "_diffuse" in image.name.lower():
                                nodeutils.link_nodes(links, image_node, "Alpha", shader_node, socket_name)
                            else:
                                nodeutils.link_nodes(links, image_node, "Color", shader_node, socket_name)

                        if alpha_socket_name:
                            nodeutils.link_nodes(links, image_node, "Alpha", shader_node, alpha_socket_name)

                    if image_node and image_node.image:
                        image_nodes.append(image_node)
                        textures[tex_type] = { "node": image_node, "image": image_node.image }

    # main shader post processing
    if not sub_shader:

        # remove any extra image nodes:
        if not mat_cache.user_added:
            for n in nodes:
                if n.type == "TEX_IMAGE" and n not in image_nodes:
                    utils.log_info("Removing unused image node: " + n.name)
                    nodes.remove(n)

        # finally disconnect bump map if normal map is also present (this is only supposed to be one, but it is possible to bug CC3 and get both):
        if nodeutils.has_connected_input(shader_node, "Bump Map") and nodeutils.has_connected_input(shader_node, "Normal Map"):
            bump_node, bump_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, "Bump Map")
            nodeutils.unlink_node_output(links, shader_node, "Bump Map")


def connect_tearline_shader(obj_cache, obj, mat, mat_json, processed_images):
    props = vars.props()
    prefs = vars.prefs()

    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Tearline Shader"
    shader_name = "rl_tearline_shader"
    shader_group = "rl_tearline_shader"
    mix_shader_group = ""
    if prefs.render_target == "CYCLES":
        shader_group = "rl_tearline_cycles_shader"
        mix_shader_group = "rl_tearline_cycles_mix_shader"

    bsdf, group = nodeutils.reset_shader(mat_cache, nodes, links, shader_label, shader_name, shader_group, mix_shader_group)

    apply_prop_matrix(bsdf, group, mat_cache, shader_name)

    nodeutils.clean_unused_image_nodes(nodes)

    materials.set_material_alpha(mat, "BLEND", shadows=False)


def connect_eye_occlusion_shader(obj_cache, obj, mat, mat_json, processed_images):
    props = vars.props()
    prefs = vars.prefs()

    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Eye Occlusion Shader"
    shader_name = "rl_eye_occlusion_shader"
    shader_group = "rl_eye_occlusion_shader"
    mix_shader_group = ""
    if prefs.render_target == "CYCLES":
        mix_shader_group = "rl_eye_occlusion_cycles_mix_shader"
        shader_group = ""

    bsdf, group = nodeutils.reset_shader(mat_cache, nodes, links, shader_label, shader_name, shader_group, mix_shader_group)

    apply_prop_matrix(bsdf, group, mat_cache, shader_name)

    nodeutils.clean_unused_image_nodes(nodes)

    materials.set_material_alpha(mat, "BLEND", shadows=False)


def connect_skin_shader(chr_cache, obj_cache, obj, mat, mat_json, processed_images):
    props = vars.props()
    prefs = vars.prefs()

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
    mix_shader_group = ""

    custom_bsdf = None
    if prefs.build_skin_shader_dual_spec:
        custom_bsdf = "rl_bsdf_dual_specular"

    bsdf, group = nodeutils.reset_shader(mat_cache, nodes, links,
                                         shader_label, shader_name, shader_group, mix_shader_group,
                                         custom_bsdf)

    nodeutils.reset_cursor()

    # use shader_group here instead of shader_name
    apply_prop_matrix(bsdf, group, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, group, mat, mat_cache, shader_name, mat_json, obj, processed_images)

    if not prefs.build_limit_textures:
        if props.wrinkle_mode and mat_json and "Wrinkle" in mat_json.keys():
            utils.log_info("Applying Wrinkle System:")
            apply_wrinkle_system(chr_cache, nodes, links, group, shader_name, mat, mat_cache, mat_json, obj, processed_images)

    utils.log_info("Cleaning up unused image nodes:")
    nodeutils.clean_unused_image_nodes(nodes)

    fix_sss_method(bsdf, is_skin=True)

    if utils.B410():
        mat.displacement_method = "DISPLACEMENT"
    else:
        mat.cycles.displacement_method = "DISPLACEMENT"

    if not utils.B420():
        mat.use_sss_translucency = True

    materials.set_material_alpha(mat, "OPAQUE")


def connect_tongue_shader(obj_cache, obj, mat, mat_json, processed_images):
    props = vars.props()
    prefs = vars.prefs()

    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Tongue Shader"
    shader_name = "rl_tongue_shader"
    shader_group = "rl_tongue_shader"
    mix_shader_group = ""

    bsdf, group = nodeutils.reset_shader(mat_cache, nodes, links, shader_label, shader_name, shader_group, mix_shader_group)

    apply_prop_matrix(bsdf, group, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, group, mat, mat_cache, shader_name, mat_json, obj, processed_images)

    nodeutils.clean_unused_image_nodes(nodes)

    fix_sss_method(bsdf)

    materials.set_material_alpha(mat, "OPAQUE")

    if not utils.B420():
        mat.use_sss_translucency = True


def connect_teeth_shader(obj_cache, obj, mat, mat_json, processed_images):
    props = vars.props()
    prefs = vars.prefs()

    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Teeth Shader"
    shader_name = "rl_teeth_shader"
    shader_group = "rl_teeth_shader"
    mix_shader_group = ""

    bsdf, group = nodeutils.reset_shader(mat_cache, nodes, links, shader_label, shader_name, shader_group, mix_shader_group)

    apply_prop_matrix(bsdf, group, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, group, mat, mat_cache, shader_name, mat_json, obj, processed_images)

    if mat_cache.is_upper_teeth():
        nodeutils.set_node_input_value(group, "Is Upper Teeth", 1.0)
    else:
        nodeutils.set_node_input_value(group, "Is Upper Teeth", 0.0)

    nodeutils.clean_unused_image_nodes(nodes)

    fix_sss_method(bsdf)

    materials.set_material_alpha(mat, "OPAQUE")

    if not utils.B420():
        mat.use_sss_translucency = True


def connect_eye_shader(obj_cache, obj, mat, obj_json, mat_json, processed_images):
    props = vars.props()
    prefs = vars.prefs()

    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # there is no need to set up the eye_L/R materials for parallax eyes
    if mat_cache.is_eye() and prefs.refractive_eyes == "PARALLAX":
        return

    # to build eye materials we need some textures from the cornea:
    cornea_mat = mat
    cornea_mat_cache = mat_cache
    cornea_json = mat_json
    connect_as_pbr = False
    if mat_cache.is_eye():
        connect_as_pbr = True
        if prefs.refractive_eyes == "SSR":
            cornea_mat, cornea_mat_cache = materials.get_cornea_mat(obj, mat, mat_cache)
            if cornea_mat:
                cornea_json = jsonutils.get_material_json(obj_json, cornea_mat)
                # for SSR eyes, use the textures and settings from the cornea material, if available
                connect_as_pbr = False

    if connect_as_pbr:
        connect_pbr_shader(obj_cache, obj, mat, mat_json, processed_images)
        return

    mix_shader_group = ""
    if mat_cache.is_cornea():
        if prefs.refractive_eyes == "SSR":
            shader_label = "Cornea Shader"
            shader_name = "rl_cornea_shader"
            shader_group = "rl_cornea_refractive_shader"
        else:
            shader_label = "Cornea Shader"
            shader_name = "rl_cornea_shader"
            shader_group = "rl_cornea_parallax_shader"
    else:
        if prefs.refractive_eyes == "SSR":
            shader_label = "Eye Shader"
            shader_name = "rl_eye_shader"
            shader_group = "rl_eye_refractive_shader"
        else:
            shader_label = "Eye Shader"
            shader_name = "rl_eye_shader"
            # TODO rl_eye_pbr_shader???
            shader_group = "rl_eye_refractive_shader"

    bsdf, group = nodeutils.reset_shader(mat_cache, nodes, links, shader_label, shader_name, shader_group, mix_shader_group)

    apply_prop_matrix(bsdf, group, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, group, cornea_mat, cornea_mat_cache, shader_name, cornea_json, obj, processed_images)


    nodeutils.clean_unused_image_nodes(nodes)

    fix_sss_method(bsdf, is_eyes=True)

    if not utils.B420():
        mat.use_sss_translucency = True

    if mat_cache.is_cornea():
        if prefs.refractive_eyes == "SSR":
            materials.set_material_alpha(mat, "OPAQUE",
                                         refraction=True,
                                         depth=mat_cache.parameters.eye_refraction_depth / 1000)
        else:
            materials.set_material_alpha(mat, "OPAQUE", refraction=False)
    else:
        materials.set_material_alpha(mat, "OPAQUE", refraction=False)


def connect_hair_shader(obj_cache, obj, mat, mat_json, processed_images):
    props = vars.props()
    prefs = vars.prefs()

    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Hair Shader"
    shader_name = "rl_hair_shader"
    shader_group = "rl_hair_shader"
    mix_shader_group = ""
    if prefs.render_target == "CYCLES":
        shader_group = "rl_hair_cycles_shader"

    bsdf, group = nodeutils.reset_shader(mat_cache, nodes, links, shader_label, shader_name, shader_group, mix_shader_group)

    apply_prop_matrix(bsdf, group, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, group, mat, mat_cache, shader_name, mat_json, obj, processed_images)

    nodeutils.clean_unused_image_nodes(nodes)

    fix_sss_method(bsdf, is_hair=True)

    materials.set_material_alpha(mat, "HASHED")

    if not utils.B420():
        mat.use_sss_translucency = True


def connect_pbr_shader(obj_cache, obj, mat: bpy.types.Material, mat_json, processed_images):
    props = vars.props()
    prefs = vars.prefs()

    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "Pbr Shader"
    shader_name = "rl_pbr_shader"
    shader_group = "rl_pbr_shader"
    mix_shader_group = ""

    bsdf, group = nodeutils.reset_shader(mat_cache, nodes, links, shader_label, shader_name, shader_group, mix_shader_group)

    apply_prop_matrix(bsdf, group, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, group, mat, mat_cache, shader_name, mat_json, obj, processed_images)

    nodeutils.clean_unused_image_nodes(nodes)

    # material alpha blend settings
    method = materials.determine_material_alpha(obj_cache, mat_cache, mat_json)
    materials.set_material_alpha(mat, method)

    if mat_cache.is_eyelash():
        nodeutils.set_node_input_value(group, "Specular Scale", 0.25)
        nodeutils.set_node_input_value(bsdf, "Subsurface", 0.001)
        fix_sss_method(bsdf, is_scalp=True)

    elif mat_cache.is_scalp():
        nodeutils.set_node_input_value(group, "Specular Scale", 0)
        nodeutils.set_node_input_value(bsdf, "Subsurface", 0.01)
        fix_sss_method(bsdf, is_scalp=True)

    else:
        fix_sss_method(bsdf)

    texture_path, strength, level, multiplier, base = jsonutils.get_displacement_data(mat_json)
    if texture_path and strength > 0 and level > 0:
        # add a subdivision modifer but set it to zero.
        # lots of clothing in CC/iC uses tesselation and displacement, but
        # subdividing all of it would significantly slow down blender.
        # so the modifiers are added, but the user must then set their levels.
        mod = modifiers.add_subdivision(obj, level, "Displacement_Subdiv", max_level=0, view_level=0)
        if mod:
            modifiers.move_mod_first(obj, mod)
        if utils.B410():
            mat.displacement_method = "BOTH"
        else:
            mat.cycles.displacement_method = "BOTH"


def connect_sss_shader(obj_cache, obj, mat, mat_json, processed_images):
    props = vars.props()
    prefs = vars.prefs()

    mat_cache = props.get_material_cache(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    shader_label = "SSS Shader"
    shader_name = "rl_sss_shader"
    shader_group = "rl_sss_shader"
    mix_shader_group = ""

    bsdf, group = nodeutils.reset_shader(mat_cache, nodes, links, shader_label, shader_name, shader_group, mix_shader_group)

    apply_prop_matrix(bsdf, group, mat_cache, shader_name)
    apply_texture_matrix(nodes, links, group, mat, mat_cache, shader_name, mat_json, obj, processed_images)

    nodeutils.clean_unused_image_nodes(nodes)

    fix_sss_method(bsdf)

    if nodeutils.has_connected_input(group, "Alpha Map"):
        materials.set_material_alpha(mat, "HASHED")


def fix_sss_method(bsdf, is_skin=False, is_hair=False, is_eyes=False, is_scalp=False):
    prefs = vars.prefs()
    bsdf_nodes = nodeutils.get_custom_bsdf_nodes(bsdf)
    if utils.B400():

        # Blender 4.0+
        for bsdf in bsdf_nodes:
            if is_skin or is_hair or is_eyes or is_scalp:
                bsdf.subsurface_method = "RANDOM_WALK_SKIN"
                bsdf.inputs['Subsurface Scale'].default_value = 1.0
                if is_hair:
                    bsdf.inputs['Subsurface Anisotropy'].default_value = 1.0
                elif is_skin:
                    bsdf.inputs['Subsurface Anisotropy'].default_value = 0.8
                elif is_eyes:
                    bsdf.inputs['Subsurface Anisotropy'].default_value = 1.0
                    bsdf.inputs['Subsurface Scale'].default_value = 0.01
                else:
                    bsdf.inputs['Subsurface Anisotropy'].default_value = 0.5
            else:
                bsdf.subsurface_method = "BURLEY"

    else:

        # Blender 3.4 - 3.6
        if utils.B340():
            for bsdf in bsdf_nodes:
                if is_skin or is_eyes or is_scalp:
                    bsdf.subsurface_method = "RANDOM_WALK"
                    bsdf.inputs['Subsurface Anisotropy'].default_value = 0.5
                else:
                    bsdf.subsurface_method = "BURLEY"


def get_connected_textures(node: bpy.types.NodeGroup, tex_nodes: set, done=None):
    if done is None:
        done = []
    for input in node.inputs:
        n, s = nodeutils.get_node_and_socket_connected_to_input(node, input)
        if n and n not in done:
            done.append(n)
            if n.type == "TEX_IMAGE":
                tex_nodes.add(n)
            get_connected_textures(n, tex_nodes, done)
    return tex_nodes


def check_tex_count(links, shader_node, wrinkle_shader_node, max_images=32):
    tex_nodes = set()
    for node in [shader_node, wrinkle_shader_node]:
        tex_nodes = get_connected_textures(node, tex_nodes)
    active_tex_count = len(tex_nodes)
    if active_tex_count > max_images:
        if nodeutils.has_connected_input(shader_node, "Specular Map"):
            nodeutils.unlink_node_input(links, shader_node, "Specular Map")
            active_tex_count -= 1
    if active_tex_count > max_images:
        nbs = nodeutils.get_node_input_value(shader_node, "Normal Blend Strength")
        if nbs < 0.01 and nodeutils.has_connected_input(shader_node, "Normal Blend Map"):
            nodeutils.unlink_node_input(links, shader_node, "Normal Blend Map")
            active_tex_count -= 1
    if active_tex_count > max_images:
        cbs = nodeutils.get_node_input_value(shader_node, "Blend Overlay Strength")
        if cbs < 0.01 and nodeutils.has_connected_input(shader_node, "Blender Overlay"):
            nodeutils.unlink_node_input(links, shader_node, "Blender Overlay")
            active_tex_count -= 1
    if active_tex_count > max_images:
        if nodeutils.has_connected_input(shader_node, "EN Map"):
            nodeutils.unlink_node_input(links, shader_node, "EN Map")
            nodeutils.unlink_node_input(links, shader_node, "EN Alpha")
            active_tex_count -= 1
    if active_tex_count > max_images:
        if nodeutils.has_connected_input(shader_node, "CFULC Map"):
            nodeutils.unlink_node_input(links, shader_node, "CFULC Map")
            nodeutils.unlink_node_input(links, shader_node, "CFULC Alpha")
            active_tex_count -= 1
    if active_tex_count > max_images:
        if nodeutils.has_connected_input(shader_node, "NMUIL Map"):
            nodeutils.unlink_node_input(links, shader_node, "NMUIL Map")
            nodeutils.unlink_node_input(links, shader_node, "NMUIL Alpha")
            active_tex_count -= 1


def apply_wrinkle_system(chr_cache, nodes, links, shader_node, main_shader_name,
                         mat, mat_cache, mat_json, obj, processed_images, textures=None):

    wrinkle_shader_node = wrinkle.add_wrinkle_shader(chr_cache, links, mat, mat_json, main_shader_name, wrinkle_shader_name=wrinkle.WRINKLE_SHADER_NAME)
    apply_texture_matrix(nodes, links, wrinkle_shader_node, mat, mat_cache, wrinkle.WRINKLE_SHADER_NAME, mat_json, obj,
                         processed_images, sub_shader = True, textures = textures)

    max_images = 32 if not utils.B420() else 40
    check_tex_count(links, shader_node, wrinkle_shader_node, max_images=max_images)

