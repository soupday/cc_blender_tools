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

import bpy, re

from . import drivers, meshutils, nodeutils, lib, utils, params, vars

WRINKLE_SHADER_NAME="rl_wrinkle_shader"
WRINKLE_STRENGTH_PROP = "wrinkle_strength"
WRINKLE_REGIONS_PROP = "wrinkle_regions"
WRINKLE_STRENGTH_VAR = "str"
WRINKLE_CURVES_PROP = "wrinkle_curves"
WRINKLE_CURVE_PROP_OLD = "wrinkle_curve"
WRINKLE_CURVE_PREFIX = "crv"
WRINKLE_VAR_PREFIX = "var"
WRINKLE_REGION_PREFIX = "reg"

def get_wrinkle_shader_node(mat):
    if mat and mat.node_tree:
        nodes = mat.node_tree.nodes
        wrinkle_shader_id = "(rl_wrinkle_shader)"
        for node in nodes:
            if vars.NODE_PREFIX in node.name:
                if wrinkle_shader_id in node.name:
                    return node


def get_wrinkle_shader(obj, mat, mat_json, shader_name="rl_wrinkle_shader",
                       create=True, remove=True, add_mappings=False):

    shader_id = "(" + str(shader_name) + ")"
    wrinkle_node = None

    # find existing wrinkle shader group node and remove any old or impostors
    to_remove = []
    if mat and mat.node_tree:
        nodes = mat.node_tree.nodes
        for n in nodes:
            if n.type == "GROUP":
                if shader_id in n.name and shader_name in n.node_tree.name:
                    wrinkle_node = n
                    if lib.is_version(n) and lib.is_version(n.node_tree):
                        ...
                    elif remove:
                        if wrinkle_node == n:
                            wrinkle_node = None
                        to_remove.append(n)

    if remove:
        for n in to_remove:
            nodes.remove(n)

    # create a new wrinkle shader group node if none
    if create and not wrinkle_node:
        group = lib.get_node_group(shader_name)
        wrinkle_node = nodeutils.make_node_group_node(nodes, group, "Wrinkle Map System", utils.unique_name(shader_id))
        wrinkle_node.width = 240
        utils.log_info("Created new wrinkle system shader group: " + wrinkle_node.name)

    if wrinkle_node and add_mappings:
        add_wrinkle_mappings(mat, wrinkle_node, obj, mat_json)

    return wrinkle_node


def clear_wrinkle_props(chr_cache, exclude=None):
    body_objects = chr_cache.get_objects_of_type("BODY")
    for obj in body_objects:
        if WRINKLE_CURVE_PROP_OLD in obj:
            del obj[WRINKLE_CURVE_PROP_OLD]
        if exclude and exclude == obj: continue
        if WRINKLE_STRENGTH_PROP in obj:
            del obj[WRINKLE_STRENGTH_PROP]
        if WRINKLE_CURVES_PROP in obj:
            del obj[WRINKLE_CURVES_PROP]
        if WRINKLE_REGIONS_PROP in obj:
            del obj[WRINKLE_REGIONS_PROP]


def add_wrinkle_shader(chr_cache, links, mat, mat_json, main_shader_name, wrinkle_shader_name=WRINKLE_SHADER_NAME):
    body_obj = meshutils.get_head_body_object(chr_cache)
    clear_wrinkle_props(chr_cache, body_obj)
    wrinkle_shader_node = get_wrinkle_shader(body_obj, mat, mat_json,
                                             shader_name=wrinkle_shader_name,
                                             create=True, remove=True, add_mappings=True)
    bsdf_node, main_shader_node, mix_node = nodeutils.get_shader_nodes(mat, main_shader_name)
    wrinkle_shader_node.location = (-2400, 0)
    nodeutils.link_nodes(links, wrinkle_shader_node, "Diffuse Map", main_shader_node, "Diffuse Map")
    nodeutils.link_nodes(links, wrinkle_shader_node, "Roughness Map", main_shader_node, "Roughness Map")
    nodeutils.link_nodes(links, wrinkle_shader_node, "Normal Map", main_shader_node, "Normal Map")
    if nodeutils.has_connected_input(main_shader_node, "Displacement Map"):
        nodeutils.link_nodes(links, wrinkle_shader_node, "Displacement Map", main_shader_node, "Displacement Map")
        nodeutils.link_nodes(links, wrinkle_shader_node, "Displacement Delta", main_shader_node, "Displacement Delta")
    return wrinkle_shader_node


def build_wrinkle_drivers(chr_cache, chr_json, wrinkle_shader_name=WRINKLE_SHADER_NAME):
    body_obj = meshutils.get_head_body_object(chr_cache)
    clear_wrinkle_props(chr_cache, body_obj)
    head_mat, head_mat_json = meshutils.get_head_material_and_json(chr_cache, chr_json)
    if body_obj and head_mat and head_mat_json:
        wrinkle_shader_node = get_wrinkle_shader(body_obj, head_mat, head_mat_json,
                                                 shader_name=wrinkle_shader_name,
                                                 create=False, remove=False,
                                                 add_mappings=True)


REGION_RULES = {
    # Brow Raise
    "01": ["head_wm1_normal_head_wm1_browRaiseInner_L",
           "head_wm1_normal_head_wm1_browRaiseOuter_L",
           "head_wm1_normal_head_wm1_browRaiseInner_R",
           "head_wm1_normal_head_wm1_browRaiseOuter_R"],
    # Brow Drop
    "02": ["head_wm2_normal_head_wm2_browsDown_L",
           "head_wm2_normal_head_wm2_browsLateral_L",
           "head_wm2_normal_head_wm2_browsDown_R",
           "head_wm2_normal_head_wm2_browsLateral_R"],
    # Blink
    "03": ["head_wm1_normal_head_wm1_blink_L",
           "head_wm1_normal_head_wm1_blink_R"],
    # Squint
    "04": ["head_wm1_normal_head_wm1_squintInner_L",
           "head_wm1_normal_head_wm1_squintInner_R"],
    # Nose
    "05": ["head_wm2_normal_head_wm2_noseWrinkler_L",
           "head_wm2_normal_head_wm2_noseWrinkler_R"],
    # Cheek Raise
    "06": ["head_wm3_normal_head_wm3_cheekRaiseInner_L",
           "head_wm3_normal_head_wm3_cheekRaiseInner_R",
           "head_wm3_normal_head_wm3_cheekRaiseOuter_L",
           "head_wm3_normal_head_wm3_cheekRaiseOuter_R",
           "head_wm3_normal_head_wm3_cheekRaiseUpper_L",
           "head_wm3_normal_head_wm3_cheekRaiseUpper_R"],
    # Nostril Crease
    "07": ["head_wm2_normal_head_wm2_noseCrease_L",
           "head_wm2_normal_head_wm2_noseCrease_R"],
    # Purse Lips
    "08": ["head_wm1_normal_head_wm1_purse_DL",
           "head_wm1_normal_head_wm1_purse_DR",
           "head_wm1_normal_head_wm1_purse_UL",
           "head_wm1_normal_head_wm1_purse_UR",
           "head_wm1_normal_head_wm13_lips_DL",
           "head_wm1_normal_head_wm13_lips_DR",
           "head_wm1_normal_head_wm13_lips_UL",
           "head_wm1_normal_head_wm13_lips_UR"],
    # Smile Lip Stretch
    "09": ["head_wm3_normal_head_wm3_smile_L",
           "head_wm3_normal_head_wm13_lips_DL",
           "head_wm3_normal_head_wm13_lips_UL",
           "head_wm3_normal_head_wm3_smile_R",
           "head_wm3_normal_head_wm13_lips_DR",
           "head_wm3_normal_head_wm13_lips_UR"],
    # Mouth Stretch
    "10": ["head_wm2_normal_head_wm2_mouthStretch_L",
           "head_wm2_normal_head_wm2_mouthStretch_R"],
    # Chin
    "11": ["head_wm1_normal_head_wm1_chinRaise_L",
           "head_wm1_normal_head_wm1_chinRaise_R"],
    # Jaw
    "12": ["head_wm1_normal_head_wm1_jawOpen"],
    # Neck Stretch
    "13": ["head_wm2_normal_head_wm2_neckStretch_L",
           "head_wm2_normal_head_wm2_neckStretch_R"],
}


def get_wrinkle_params(mat_json):
    wrinkle_params = {}
    overall_weight = 1.0
    region_weights = {}

    if "Wrinkle" in mat_json.keys():

        wrinkle_json = mat_json["Wrinkle"]

        if ("WrinkleRules" in wrinkle_json.keys() and
            "WrinkleEaseStrength" in wrinkle_json.keys() and
            "WrinkleRuleWeights" in wrinkle_json.keys()):

            rule_names = wrinkle_json["WrinkleRules"]
            ease_strengths = wrinkle_json["WrinkleEaseStrength"]
            weights = wrinkle_json["WrinkleRuleWeights"]

            for i in range(0, len(rule_names)):
                wrinkle_params[rule_names[i]] = { "ease_strength": ease_strengths[i], "weight": weights[i] }

            if "WrinkleOverallWeight" in wrinkle_json.keys():
                overall_weight = wrinkle_json["WrinkleOverallWeight"]

            # fetch the region weights from the WrinkleRuleWeights
            for region in REGION_RULES:
                for rule_name in REGION_RULES[region]:
                    if rule_name in wrinkle_params:
                        if region not in region_weights:
                            region_weights[region] = wrinkle_params[rule_name]["weight"]
                        else:
                            region_weights[region] += wrinkle_params[rule_name]["weight"]
                if region in region_weights:
                    region_weights[region] /= len(REGION_RULES[region])

    return wrinkle_params, overall_weight, region_weights


def get_wrinkle_mappings(body_obj):
    blocks = body_obj.data.shape_keys.key_blocks
    if "Brow_Down_L" in blocks or "Brow_Down_R" in blocks:
        return WRINKLE_MAPPINGS_MH
    else:
        return WRINKLE_MAPPINGS_STD


def add_wrinkle_mappings(mat, node, body_obj, mat_json):

    utils.log_info(f"Building Wrinkle map system drivers: {mat.name} / {node.name}")

    if not body_obj.data.shape_keys or not body_obj.data.shape_keys.key_blocks:
        return

    wrinkle_defs = {}

    wrinkle_params, overall_weight, region_weights = get_wrinkle_params(mat_json)

    if WRINKLE_STRENGTH_PROP not in body_obj:
        drivers.add_custom_float_property(body_obj, WRINKLE_STRENGTH_PROP, overall_weight, value_min=0.0, value_max=2.0,
                                          description="Overall wrinkle influence")

    curve_values = [1.0]*13
    if WRINKLE_CURVES_PROP not in body_obj:
        drivers.add_custom_float_array_property(body_obj, WRINKLE_CURVES_PROP, curve_values, value_min=0.25, value_max=2.0,
                                          description="How quickly or slowly the wrinkle maps build up to full strength for each region (Power Curve)")

    region_values = list(region_weights.values())
    if WRINKLE_REGIONS_PROP not in body_obj:
        drivers.add_custom_float_array_property(body_obj, WRINKLE_REGIONS_PROP, region_values, value_min=0.0, value_max=2.0,
                                                description="Wrinkle map region strengths")

    for wrinkle_name in WRINKLE_RULES.keys():
        weight, func, region = WRINKLE_RULES[wrinkle_name]
        if wrinkle_name in wrinkle_params.keys():
            weight *= wrinkle_params[wrinkle_name]["weight"]
        wrinkle_def = { "weight": weight, "func": func, "keys": [], "region": region }
        wrinkle_defs[wrinkle_name] = wrinkle_def

    WRINKLE_MAPPINGS = get_wrinkle_mappings(body_obj)
    for regex, wrinkle_name, range_min, range_max in WRINKLE_MAPPINGS:
        for key in body_obj.data.shape_keys.key_blocks:
            if re.match(regex, key.name):
                if wrinkle_name in WRINKLE_RULES.keys():
                    weight, func, region = WRINKLE_RULES[wrinkle_name]
                    key_def = [key.name, range_min * weight, range_max * weight, region]
                    wrinkle_defs[wrinkle_name]["keys"].append(key_def)
                else:
                    utils.log_error(f"Wrinkle Morph Name: {wrinkle_name} not found in Wrinkle Rules!")
            utils.log_detail(f"Skipping shape key: {regex}, not found in body mesh.")

    for socket_name in WRINKLE_DRIVERS:
        expr_macro = WRINKLE_DRIVERS[socket_name]
        add_wrinkle_node_driver(mat, node, socket_name, body_obj, expr_macro, wrinkle_defs, overall_weight)


def add_wrinkle_node_driver(mat, node, socket_name, obj, expr_macro : str, wrinkle_defs, overall_weight):

    s = expr_macro.find(r"{")
    if s == -1:
        utils.log_error(f"No braces in wrinkle macro expression! {expr_macro}")
        return

    var_defs = []

    while s > -1:
        e = expr_macro.find(r"}", s)
        if e > -1:
            rule_name = expr_macro[s+1:e]
            expr = get_driver_expression(obj, mat, rule_name, wrinkle_defs, var_defs)
            expr_macro = expr_macro.replace(r"{" + rule_name + r"}", expr)
            s = expr_macro.find(r"{", s + len(expr))
        else:
            utils.log_error(f"No end braces in wrinkle macro expression! {expr_macro}")
            return

    if len(var_defs) == 0:
        return

    socket: bpy.types.NodeSocket = node.inputs[socket_name]
    expr_code = f"{WRINKLE_STRENGTH_VAR} * ({expr_macro})"
    driver = drivers.make_driver(socket, "default_value", "SCRIPTED", expr_code)

    # global vars
    drivers.make_driver_var(driver, "SINGLE_PROP", WRINKLE_STRENGTH_VAR, obj,
                            data_path = f"[\"{WRINKLE_STRENGTH_PROP}\"]")

    #drivers.make_driver_var(driver, "SINGLE_PROP", WRINKLE_CURVE_PREFIX, obj,
    #                        data_path = f"[\"{WRINKLE_CURVE_PROP}\"]")

    # add driver variables
    for i, var_def in enumerate(var_defs):
        drivers.make_driver_var(driver, "SINGLE_PROP", var_def["name"], var_def["target"],
                                target_type = var_def["target_type"], data_path = var_def["data_path"])
        if "curve" in var_def:
            drivers.make_driver_var(driver, "SINGLE_PROP", var_def["curve"], var_def["target"],
                                    target_type = var_def["target_type"], data_path = var_def["curve_data_path"])



def get_driver_expression(obj, mat, rule_name, wrinkle_defs : dict, var_defs : list):
    # wrinkle_defs = { wrinkle_name: { "weight": weight, "func": func, "keys": [ [shape_key_name, range_min, range_max], ] } }
    # var_defs = [ { "name": name, "shape_key": shape_key_name, "target": target, "target_type": type, "data_path": data_path }, ]

    if rule_name in wrinkle_defs:
        var_id = len(var_defs) + 1
        var_code = ""
        wrinkle_def = wrinkle_defs[rule_name]
        weight = wrinkle_def["weight"]
        func = wrinkle_def["func"]
        key_defs = wrinkle_def["keys"]
        region = wrinkle_def["region"]

        region_var_def = {}
        for vdef in var_defs:
            if "region" in vdef and vdef["region"] == region:
                region_var_def = vdef
                break
        if not region_var_def:
            region_var_def["name"] = f"{WRINKLE_REGION_PREFIX}{region}"
            region_var_def["curve"] = f"{WRINKLE_CURVE_PREFIX}{region}"
            region_var_def["region"] = region
            region_var_def["target"] = obj
            region_var_def["target_type"] = "OBJECT"
            region_var_def["data_path"] = f"[\"{WRINKLE_REGIONS_PROP}\"][{int(region)-1}]"
            region_var_def["curve_data_path"] = f"[\"{WRINKLE_CURVES_PROP}\"][{int(region)-1}]"
            var_defs.append(region_var_def)

        region_var_name = None
        curve_var_name = None

        for i, key_def in enumerate(key_defs):
            shape_key_name = key_def[0]
            range_min = key_def[1]
            range_max = key_def[2]
            region = key_def[3]
            var_def = {}
            for vdef in var_defs:
                if "shape_key" in vdef and vdef["shape_key"] == shape_key_name:
                    var_def = vdef
                    break
            if not var_def:
                var_def["name"] = f"{WRINKLE_VAR_PREFIX}{var_id}"
                var_id += 1
                var_def["shape_key"] = shape_key_name
                var_def["target"] = obj.data
                var_def["target_type"] = "MESH"
                var_def["data_path"] = f"shape_keys.key_blocks[\"{shape_key_name}\"].value"
                var_defs.append(var_def)

            var_name = var_def["name"]
            region_var_name = region_var_def["name"]
            curve_var_name = region_var_def["curve"]

            if i > 0:
                if func == "MAX" or func == "MIN":
                    var_code += ","
                elif func == "ADD":
                    var_code += "+"

            if range_min == 0 and range_max == 1:
                var_range_expr = f"{var_name}"
            elif range_min == 0:
                var_range_expr = f"{range_max * weight}*{var_name}"
            else:
                var_range_expr = f"({range_min * weight}+({range_max * weight}-{range_min * weight})*{var_name})"

            var_code += var_range_expr

        # add a driver for the node socket input value: node.inputs[socket_name].default_value
        if func == "MAX":
            expr = f"max({var_code})"
        elif func == "MIN":
            expr = f"min({var_code})"
        elif func == "ADD":
            expr = f"({var_code})"

        if region_var_name and curve_var_name:
            return f"max(0, pow({expr}*{region_var_name}, {curve_var_name}))"

    return "0"


def is_wrinkle_system(node):
    wrinkle_shader_id = "(rl_wrinkle_shader)"
    if wrinkle_shader_id in node.name:
        return True
    else:
        return False




# { socket_name: expr_macro,  }
WRINKLE_DRIVERS = {
    "Value 1AXL": r"{head_wm1_normal_head_wm1_blink_L}",
    "Value 1AXL": r"{head_wm1_normal_head_wm1_blink_L}",
    "Value 1AXR": r"{head_wm1_normal_head_wm1_blink_R}",

    "Value 1AYL": r"{head_wm1_normal_head_wm1_browRaiseInner_L} - min({head_wm1_normal_head_wm1_browRaiseInner_L}, {head_wm2_normal_head_wm2_browsLateral_L})",
    "Value 1AYR": r"{head_wm1_normal_head_wm1_browRaiseInner_R} - min({head_wm1_normal_head_wm1_browRaiseInner_R}, {head_wm2_normal_head_wm2_browsLateral_R})",

    "Value 1AZL": r"{head_wm1_normal_head_wm1_purse_DL}",
    "Value 1AZR": r"{head_wm1_normal_head_wm1_purse_DR}",

    "Value 1AWL": r"{head_wm1_normal_head_wm1_purse_UL}",
    "Value 1AWR": r"{head_wm1_normal_head_wm1_purse_UR}",

    # Set 1B L/R
    "Value 1BXL": r"{head_wm1_normal_head_wm1_browRaiseOuter_L}",
    "Value 1BXR": r"{head_wm1_normal_head_wm1_browRaiseOuter_R}",

    "Value 1BYL": r"{head_wm1_normal_head_wm1_chinRaise_L}",
    "Value 1BYR": r"{head_wm1_normal_head_wm1_chinRaise_R}",

    "Value 1BZL": r"{head_wm1_normal_head_wm1_jawOpen_L}",
    "Value 1BZR": r"{head_wm1_normal_head_wm1_jawOpen_R}",

    "Value 1BWL": r"{head_wm1_normal_head_wm1_squintInner_L}",
    "Value 1BWR": r"{head_wm1_normal_head_wm1_squintInner_R}",

    # Set 2 L/R
    "Value 2XL": r"{head_wm2_normal_head_wm2_browsDown_L}",
    "Value 2XR": r"{head_wm2_normal_head_wm2_browsDown_R}",

    "Value 2YL": r"{head_wm2_normal_head_wm2_browsLateral_L} - min({head_wm1_normal_head_wm1_browRaiseInner_L}, {head_wm2_normal_head_wm2_browsLateral_L})",
    "Value 2YR": r"{head_wm2_normal_head_wm2_browsLateral_R} - min({head_wm1_normal_head_wm1_browRaiseInner_R}, {head_wm2_normal_head_wm2_browsLateral_R})",

    "Value 2ZL": r"{head_wm2_normal_head_wm2_mouthStretch_L}",
    "Value 2ZR": r"{head_wm2_normal_head_wm2_mouthStretch_R}",

    "Value 2WL": r"{head_wm2_normal_head_wm2_neckStretch_L}",
    "Value 2WR": r"{head_wm2_normal_head_wm2_neckStretch_R}",

    # Set 3 L/R
    "Value 3XL": r"{head_wm3_normal_head_wm3_cheekRaiseInner_L}",
    "Value 3XR": r"{head_wm3_normal_head_wm3_cheekRaiseInner_R}",

    "Value 3YL": r"{head_wm3_normal_head_wm3_cheekRaiseOuter_L}",
    "Value 3YR": r"{head_wm3_normal_head_wm3_cheekRaiseOuter_R}",

    "Value 3ZL": r"{head_wm3_normal_head_wm3_cheekRaiseUpper_L}",
    "Value 3ZR": r"{head_wm3_normal_head_wm3_cheekRaiseUpper_R}",

    "Value 3WL": r"{head_wm3_normal_head_wm3_smile_L}",
    "Value 3WR": r"{head_wm3_normal_head_wm3_smile_R}",

    # Set 12C L/R
    "Value 12CXL": r"{head_wm1_normal_head_wm13_lips_DL}",
    "Value 12CXR": r"{head_wm1_normal_head_wm13_lips_DR}",

    "Value 12CYL": r"{head_wm1_normal_head_wm13_lips_UL}",
    "Value 12CYR": r"{head_wm1_normal_head_wm13_lips_UR}",

    "Value 12CZL": r"{head_wm2_normal_head_wm2_noseWrinkler_L}",
    "Value 12CZR": r"{head_wm2_normal_head_wm2_noseWrinkler_R}",

    "Value 12CWL": r"{head_wm2_normal_head_wm2_noseCrease_L}",
    "Value 12CWR": r"{head_wm2_normal_head_wm2_noseCrease_R}",

    # Set 3D
    "Value 3DXL": r"{head_wm3_normal_head_wm13_lips_DL}",
    "Value 3DYL": r"{head_wm3_normal_head_wm13_lips_DR}",

    "Value 3DZR": r"{head_wm3_normal_head_wm13_lips_UL}",
    "Value 3DWR": r"{head_wm3_normal_head_wm13_lips_UR}",

    "Value BCCL": r"min({head_wm1_normal_head_wm1_browRaiseInner_L}, {head_wm2_normal_head_wm2_browsLateral_L})",
    "Value BCCR": r"min({head_wm1_normal_head_wm1_browRaiseInner_R}, {head_wm2_normal_head_wm2_browsLateral_R})",
}

# the rules that map each wrinkle morph to the socket on the wrinkle shader node.
# { wrinkle_morph_name: [node_socket, weight, <blend_func>, extra_data], }
WRINKLE_RULES = {

    # Set 1A L/R
    "head_wm1_normal_head_wm1_blink_L": [1, "ADD", "03"],
    "head_wm1_normal_head_wm1_blink_R": [1, "ADD", "03"],

    "head_wm1_normal_head_wm1_browRaiseInner_L": [1, "ADD", "01"],
    "head_wm1_normal_head_wm1_browRaiseInner_R": [1, "ADD", "01"],

    "head_wm1_normal_head_wm1_purse_DL": [1, "ADD", "08"],
    "head_wm1_normal_head_wm1_purse_DR": [1, "ADD", "08"],

    "head_wm1_normal_head_wm1_purse_UL": [1, "ADD", "08"],
    "head_wm1_normal_head_wm1_purse_UR": [1, "ADD", "08"],

    # Set 1B L/R
    "head_wm1_normal_head_wm1_browRaiseOuter_L": [1, "ADD", "01"],
    "head_wm1_normal_head_wm1_browRaiseOuter_R": [1, "ADD", "01"],

    "head_wm1_normal_head_wm1_chinRaise_L": [1, "ADD", "11"],
    "head_wm1_normal_head_wm1_chinRaise_R": [1, "ADD", "11"],

    "head_wm1_normal_head_wm1_jawOpen_L": [1, "ADD", "12"],
    "head_wm1_normal_head_wm1_jawOpen_R": [1, "ADD", "12"],

    "head_wm1_normal_head_wm1_squintInner_L": [1, "ADD", "04"],
    "head_wm1_normal_head_wm1_squintInner_R": [1, "ADD", "04"],

    # Set 2 L/R
    "head_wm2_normal_head_wm2_browsDown_L": [1, "ADD", "02"],
    "head_wm2_normal_head_wm2_browsDown_R": [1, "ADD", "02"],

    "head_wm2_normal_head_wm2_browsLateral_L": [1, "ADD", "02"],
    "head_wm2_normal_head_wm2_browsLateral_R": [1, "ADD", "02"],

    "head_wm2_normal_head_wm2_mouthStretch_L": [1, "ADD", "10"],
    "head_wm2_normal_head_wm2_mouthStretch_R": [1, "ADD", "10"],

    "head_wm2_normal_head_wm2_neckStretch_L": [1, "ADD", "13"],
    "head_wm2_normal_head_wm2_neckStretch_R": [1, "ADD", "13"],

    # Set 3 L/R
    "head_wm3_normal_head_wm3_cheekRaiseInner_L": [1, "ADD", "06"],
    "head_wm3_normal_head_wm3_cheekRaiseInner_R": [1, "ADD", "06"],

    "head_wm3_normal_head_wm3_cheekRaiseOuter_L": [1, "ADD", "06"],
    "head_wm3_normal_head_wm3_cheekRaiseOuter_R": [1, "ADD", "06"],

    "head_wm3_normal_head_wm3_cheekRaiseUpper_L": [1, "ADD", "06"],
    "head_wm3_normal_head_wm3_cheekRaiseUpper_R": [1, "ADD", "06"],

    "head_wm3_normal_head_wm3_smile_L": [1, "ADD", "09"],
    "head_wm3_normal_head_wm3_smile_R": [1, "ADD", "09"],

    # Set 12C L/R
    "head_wm1_normal_head_wm13_lips_DL": [1, "ADD", "08"],
    "head_wm1_normal_head_wm13_lips_DR": [1, "ADD", "08"],

    "head_wm1_normal_head_wm13_lips_UL": [1, "ADD", "08"],
    "head_wm1_normal_head_wm13_lips_UR": [1, "ADD", "08"],

    "head_wm2_normal_head_wm2_noseWrinkler_L": [1, "ADD", "05"],
    "head_wm2_normal_head_wm2_noseWrinkler_R": [1, "ADD", "05"],

    "head_wm2_normal_head_wm2_noseCrease_L": [1, "ADD", "07"],
    "head_wm2_normal_head_wm2_noseCrease_R": [1, "ADD", "07"],

    # Set 3D
    "head_wm3_normal_head_wm13_lips_DL": [1, "ADD", "09"],
    "head_wm3_normal_head_wm13_lips_DR": [1, "ADD", "09"],

    "head_wm3_normal_head_wm13_lips_UL": [1, "ADD", "09"],
    "head_wm3_normal_head_wm13_lips_UR": [1, "ADD", "09"],
}

# How each shape_key on the body mesh maps to each wrinkle morph.
# When multiple shape_keys drive the same wrinkle morph, the result is averaged.
# [ ["shape_key", "rule_name", range_min, range_max], ]
WRINKLE_MAPPINGS_STD = [

    ["Brow_Raise_Inner_L", "head_wm1_normal_head_wm1_browRaiseInner_L", 0.0, 1.0],
    ["Brow_Raise_Inner_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 0.03],

    ["Brow_Raise_Inner_R", "head_wm1_normal_head_wm1_browRaiseInner_R", 0.0, 1.0],
    ["Brow_Raise_Inner_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 0.03],

    ["Brow_Raise_Outer_L", "head_wm1_normal_head_wm1_browRaiseOuter_L", 0.0, 1.0],

    ["Brow_Raise_Outer_R", "head_wm1_normal_head_wm1_browRaiseOuter_R", 0.0, 1.0],

    ["Brow_Drop_L", "head_wm2_normal_head_wm2_browsDown_L", 0.0, 0.1],
    ["Brow_Drop_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 1.0],

    ["Brow_Drop_R", "head_wm2_normal_head_wm2_browsDown_R", 0.0, 0.1],
    ["Brow_Drop_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 1.0],

    ["Brow_Compress_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 1.0],

    ["Brow_Compress_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 1.0],

    ["Eye_Blink_L", "head_wm1_normal_head_wm1_blink_L", 0.0, 1.0],
    ["Eye_Blink_L", "head_wm1_normal_head_wm1_squintInner_L", 0.0, 0.3],

    ["Eye_Blink_R", "head_wm1_normal_head_wm1_blink_R", 0.0, 1.0],
    ["Eye_Blink_R", "head_wm1_normal_head_wm1_squintInner_R", 0.0, 0.3],

    ["Eye_Squint_L", "head_wm1_normal_head_wm1_squintInner_L", 0.0, 1.0],
    ["Eye_Squint_R", "head_wm1_normal_head_wm1_squintInner_R", 0.0, 1.0],

    ["Eye_L_Look_Down", "head_wm1_normal_head_wm1_blink_L", 0.0, 1.0],
    ["Eye_R_Look_Down", "head_wm1_normal_head_wm1_blink_R", 0.0, 1.0],

    ["Nose_Sneer_L", "head_wm2_normal_head_wm2_browsDown_L", 0.0, 0.7],
    ["Nose_Sneer_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 0.6],
    ["Nose_Sneer_L", "head_wm2_normal_head_wm2_noseWrinkler_L", 0.0, 1.0],

    ["Nose_Sneer_R", "head_wm2_normal_head_wm2_browsDown_R", 0.0, 0.7],
    ["Nose_Sneer_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 0.6],
    ["Nose_Sneer_R", "head_wm2_normal_head_wm2_noseWrinkler_R", 0.0, 1.0],

    ["Nose_Nostril_Raise_L", "head_wm2_normal_head_wm2_noseWrinkler_L", 0.0, 0.6],
    ["Nose_Nostril_Raise_R", "head_wm2_normal_head_wm2_noseWrinkler_R", 0.0, 0.6],

    ["Nose_Crease_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],
    ["Nose_Crease_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.3],
    ["Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.7],
    ["Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseUpper_L", 0.0, 1.0],

    ["Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.3],
    ["Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.7],
    ["Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseUpper_R", 0.0, 1.0],

    ["Jaw_Open", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 1.0],
    ["Jaw_Open", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 1.0],

    ["Jaw_L", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 1.0],
    ["Jaw_R", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 1.0],

    ["Mouth_Up", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Mouth_Up", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["Mouth_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.8],
    ["Mouth_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.6],
    ["Mouth_L", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["Mouth_L", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],
    ["Mouth_L", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["Mouth_L", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],

    ["Mouth_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.8],
    ["Mouth_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.6],
    ["Mouth_R", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["Mouth_R", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],
    ["Mouth_R", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["Mouth_R", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],

    ["Mouth_Smile_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.6],
    ["Mouth_Smile_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.6],
    ["Mouth_Smile_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 1.0],
    ["Mouth_Smile_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 1.0],
    ["Mouth_Smile_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 1.0],
    ["Mouth_Smile_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],

    ["Mouth_Smile_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.6],
    ["Mouth_Smile_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.6],
    ["Mouth_Smile_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 1.0],
    ["Mouth_Smile_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 1.0],
    ["Mouth_Smile_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 1.0],
    ["Mouth_Smile_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Mouth_Smile_Sharp_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.4],
    ["Mouth_Smile_Sharp_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.4],
    ["Mouth_Smile_Sharp_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.8],
    ["Mouth_Smile_Sharp_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.8],
    ["Mouth_Smile_Sharp_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.8],
    ["Mouth_Smile_Sharp_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],

    ["Mouth_Smile_Sharp_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.4],
    ["Mouth_Smile_Sharp_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.4],
    ["Mouth_Smile_Sharp_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.8],
    ["Mouth_Smile_Sharp_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.8],
    ["Mouth_Smile_Sharp_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.8],
    ["Mouth_Smile_Sharp_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.15],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.15],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.3],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.3],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.3],

    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.15],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.15],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.3],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.3],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.3],

    ["Mouth_Stretch_L", "head_wm2_normal_head_wm2_mouthStretch_L", 0.0, 1.0],
    ["Mouth_Stretch_R", "head_wm2_normal_head_wm2_mouthStretch_R", 0.0, 1.0],

    ["Mouth_Pucker_Up_L", "head_wm1_normal_head_wm1_purse_UL", 0.0, 1.0],
    ["Mouth_Pucker_Up_L", "head_wm1_normal_head_wm13_lips_UL", 0.0, 1.0],

    ["Mouth_Pucker_Up_R", "head_wm1_normal_head_wm1_purse_UR", 0.0, 1.0],
    ["Mouth_Pucker_Up_R", "head_wm1_normal_head_wm13_lips_UR", 0.0, 1.0],

    ["Mouth_Pucker_Down_L", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 0.5],
    ["Mouth_Pucker_Down_L", "head_wm1_normal_head_wm1_purse_DL", 0.0, 1.0],
    ["Mouth_Pucker_Down_L", "head_wm1_normal_head_wm13_lips_DL", 0.0, 1.0],

    ["Mouth_Pucker_Down_R", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 0.5],
    ["Mouth_Pucker_Down_R", "head_wm1_normal_head_wm1_purse_DR", 0.0, 1.0],
    ["Mouth_Pucker_Down_R", "head_wm1_normal_head_wm13_lips_DR", 0.0, 1.0],

    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_DL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_DR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_UL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_UR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_DL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_DR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_UL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_UR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 0.5],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 0.5],

    ["Mouth_Chin_Up", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Mouth_Chin_Up", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["Mouth_Up_Upper_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 1.0],

    ["Mouth_Up_Upper_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 1.0],

    ["Neck_Tighten_L", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 1.0],

    ["Neck_Tighten_R", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 1.0],

    ["Head_Turn_L", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 0.6],

    ["Head_Turn_R", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 0.6],

    ["Head_Tilt_L", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 0.75],

    ["Head_Tilt_R", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 0.75],

    ["Head_Backward", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.5],
    ["Head_Backward", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.5],

    ["Mouth_Frown_L", "head_wm2_normal_head_wm2_mouthStretch_L", 0.0, 1.0],

    ["Mouth_Frown_R", "head_wm2_normal_head_wm2_mouthStretch_R", 0.0, 1.0],

    ["Mouth_Shrug_Lower", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Mouth_Shrug_Lower", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["V_Open", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 1.0],
    ["V_Open", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 1.0],

    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["V_Tight", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["V_Wide", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["AE", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.24],
    ["AE", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.24],

    ["Ah", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6],
    ["Ah", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.6],

    ["EE", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["Ih", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.15],
    ["Ih", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.15],

    ["K_G_H_NG", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.065],
    ["K_G_H_NG", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.065],

    ["Oh", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6025],
    ["Oh", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6025],
    ["Oh", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.56],

    ["R", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.1],
    ["R", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.1],
    ["R", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.63],

    ["S_Z", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.14],

    ["T_L_D_N", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.0426],
    ["T_L_D_N", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.0426],

    ["Th", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.1212],
    ["Th", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.1212],

    ["W_OO", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.56],
]

WRINKLE_MAPPINGS_MH = [

    ["Brow_Raise_In_L", "head_wm1_normal_head_wm1_browRaiseInner_L", 0.0, 1.0],
    ["Brow_Raise_In_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 0.03],

    ["Brow_Raise_In_R", "head_wm1_normal_head_wm1_browRaiseInner_R", 0.0, 1.0],
    ["Brow_Raise_In_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 0.03],

    ["Brow_Raise_Outer_L", "head_wm1_normal_head_wm1_browRaiseOuter_L", 0.0, 1.0],

    ["Brow_Raise_Outer_R", "head_wm1_normal_head_wm1_browRaiseOuter_R", 0.0, 1.0],

    ["Brow_Down_L", "head_wm2_normal_head_wm2_browsDown_L", 0.0, 0.1],
    ["Brow_Down_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 1.0],

    ["Brow_Down_R", "head_wm2_normal_head_wm2_browsDown_R", 0.0, 0.1],
    ["Brow_Down_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 1.0],

    ["Brow_Lateral_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 1.0],

    ["Brow_Lateral_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 1.0],

    ["Eye_Blink_L", "head_wm1_normal_head_wm1_blink_L", 0.0, 1.0],
    ["Eye_Blink_L", "head_wm1_normal_head_wm1_squintInner_L", 0.0, 0.3],

    ["Eye_Blink_R", "head_wm1_normal_head_wm1_blink_R", 0.0, 1.0],
    ["Eye_Blink_R", "head_wm1_normal_head_wm1_squintInner_R", 0.0, 0.3],

    ["Eye_Squint_Inner_L", "head_wm1_normal_head_wm1_squintInner_L", 0.0, 1.0],
    ["Eye_Squint_Inner_R", "head_wm1_normal_head_wm1_squintInner_R", 0.0, 1.0],

    ["Eye_Look_Down_L", "head_wm1_normal_head_wm1_blink_L", 0.0, 1.0],
    ["Eye_Look_Down_R", "head_wm1_normal_head_wm1_blink_R", 0.0, 1.0],

    ["Nose_Wrinkle_L", "head_wm2_normal_head_wm2_browsDown_L", 0.0, 0.7],
    ["Nose_Wrinkle_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 0.6],
    ["Nose_Wrinkle_L", "head_wm2_normal_head_wm2_noseWrinkler_L", 0.0, 1.0],

    ["Nose_Wrinkle_R", "head_wm2_normal_head_wm2_browsDown_R", 0.0, 0.7],
    ["Nose_Wrinkle_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 0.6],
    ["Nose_Wrinkle_R", "head_wm2_normal_head_wm2_noseWrinkler_R", 0.0, 1.0],

    ["Nose_Nostril_Raise_L", "head_wm2_normal_head_wm2_noseWrinkler_L", 0.0, 0.6],
    ["Nose_Nostril_Raise_R", "head_wm2_normal_head_wm2_noseWrinkler_R", 0.0, 0.6],

    ["Nose_Nasolabial_Deepen_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],
    ["Nose_Nasolabial_Deepen_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Eye_Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.3],
    ["Eye_Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.7],
    ["Eye_Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseUpper_L", 0.0, 1.0],

    ["Eye_Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.3],
    ["Eye_Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.7],
    ["Eye_Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseUpper_R", 0.0, 1.0],

    ["Jaw_Open", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 1.0],
    ["Jaw_Open", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 1.0],

    ["Jaw_Left", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 1.0],
    ["Jaw_Right", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 1.0],

    ["Mouth_Up", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Mouth_Up", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["Mouth_Left", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.8],
    ["Mouth_Left", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.6],
    ["Mouth_Left", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["Mouth_Left", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],
    ["Mouth_Left", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["Mouth_Left", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],

    ["Mouth_Right", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.8],
    ["Mouth_Right", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.6],
    ["Mouth_Right", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["Mouth_Right", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],
    ["Mouth_Right", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["Mouth_Right", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],

    ["Mouth_Corner_Pull_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.6],
    ["Mouth_Corner_Pull_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.6],
    ["Mouth_Corner_Pull_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 1.0],
    ["Mouth_Corner_Pull_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 1.0],
    ["Mouth_Corner_Pull_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 1.0],
    ["Mouth_Corner_Pull_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],

    ["Mouth_Corner_Pull_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.6],
    ["Mouth_Corner_Pull_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.6],
    ["Mouth_Corner_Pull_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 1.0],
    ["Mouth_Corner_Pull_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 1.0],
    ["Mouth_Corner_Pull_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 1.0],
    ["Mouth_Corner_Pull_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Mouth_SharpCorner_Pull_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.4],
    ["Mouth_SharpCorner_Pull_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.4],
    ["Mouth_SharpCorner_Pull_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],

    ["Mouth_SharpCorner_Pull_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.4],
    ["Mouth_SharpCorner_Pull_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.4],
    ["Mouth_SharpCorner_Pull_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.15],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.15],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.3],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.3],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.3],

    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.15],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.15],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.3],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.3],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.3],

    ["Mouth_Stretch_L", "head_wm2_normal_head_wm2_mouthStretch_L", 0.0, 1.0],
    ["Mouth_StretchLips_Close_L", "head_wm2_normal_head_wm2_mouthStretch_L", 0.0, 1.0],
    ["Mouth_Stretch_R", "head_wm2_normal_head_wm2_mouthStretch_R", 0.0, 1.0],
    ["Mouth_StretchLips_Close_R", "head_wm2_normal_head_wm2_mouthStretch_R", 0.0, 1.0],

    ["Mouth_Lips_Purse_UL", "head_wm1_normal_head_wm1_purse_UL", 0.0, 1.0],
    ["Mouth_Lips_Purse_UL", "head_wm1_normal_head_wm13_lips_UL", 0.0, 1.0],

    ["Mouth_Lips_Purse_UR", "head_wm1_normal_head_wm1_purse_UR", 0.0, 1.0],
    ["Mouth_Lips_Purse_UR", "head_wm1_normal_head_wm13_lips_UR", 0.0, 1.0],

    ["Mouth_Lips_Purse_DL", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 0.5],
    ["Mouth_Lips_Purse_DL", "head_wm1_normal_head_wm1_purse_DL", 0.0, 1.0],
    ["Mouth_Lips_Purse_DL", "head_wm1_normal_head_wm13_lips_DL", 0.0, 1.0],

    ["Mouth_Lips_Purse_DR", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 0.5],
    ["Mouth_Lips_Purse_DR", "head_wm1_normal_head_wm1_purse_DR", 0.0, 1.0],
    ["Mouth_Lips_Purse_DR", "head_wm1_normal_head_wm13_lips_DR", 0.0, 1.0],

    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_DL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_DR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_UL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_UR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_DL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_DR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_UL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_UR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 0.5],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 0.5],

    ["Mouth_Chin_Up", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Mouth_Chin_Up", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["Mouth_UpperLip_Raise_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 1.0],

    ["Mouth_UpperLip_Raise_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 1.0],

    ["Neck_Stretch_L", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 1.0],

    ["Neck_Stretch_R", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 1.0],

    ["Head_Turn_L", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 0.6],

    ["Head_Turn_R", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 0.6],

    ["Head_Tilt_L", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 0.75],

    ["Head_Tilt_R", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 0.75],

    ["Head_Backward", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.5],
    ["Head_Backward", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.5],

    ["Mouth_Corner_Depress_L", "head_wm2_normal_head_wm2_mouthStretch_L", 0.0, 1.0],

    ["Mouth_Corner_Depress_R", "head_wm2_normal_head_wm2_mouthStretch_R", 0.0, 1.0],

    ["Jaw_Chin_Raise_DL", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Jaw_Chin_Raise_DL", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],
    ["Jaw_Chin_Raise_DR", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Jaw_Chin_Raise_DR", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["V_Open", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6],
    ["V_Open", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.6],

    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["V_Tight", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["V_Wide", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["AE", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.24],
    ["AE", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.24],

    ["Ah", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6],
    ["Ah", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.6],

    ["EE", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["Ih", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.15],
    ["Ih", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.15],

    ["K_G_H_NG", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.065],
    ["K_G_H_NG", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.065],

    ["Oh", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6025],
    ["Oh", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6025],
    ["Oh", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.56],

    ["R", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.1],
    ["R", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.1],
    ["R", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.63],

    ["S_Z", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.14],

    ["T_L_D_N", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.0426],
    ["T_L_D_N", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.0426],

    ["Th", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.1212],
    ["Th", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.1212],

    ["W_OO", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.56],
]
