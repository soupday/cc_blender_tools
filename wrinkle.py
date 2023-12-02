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

from . import drivers, nodeutils, utils, params, vars

WRINKLE_STRENGTH_PROP = "wrinkle_strength"
WRINKLE_STRENGTH_VAR = "varstr"
WRINKLE_CURVE_PROP = "wrinkle_curve"
WRINKLE_CURVE_VAR = "varcrv"
WRINKLE_VAR_PREFIX = "var"

def get_wrinkle_shader_node(mat):
    if mat and mat.node_tree:
        nodes = mat.node_tree.nodes
        wrinkle_shader_id = "(rl_wrinkle_shader)"
        for node in nodes:
            if vars.NODE_PREFIX in node.name:
                if wrinkle_shader_id in node.name:
                    return node


def get_wrinkle_shader(obj, mat, mat_json, shader_name = "rl_wrinkle_shader", create = True):
    shader_id = "(" + str(shader_name) + ")"
    wrinkle_node = None

    # find existing wrinkle shader group node and remove any old or impostors
    to_remove = []
    if mat and mat.node_tree:
        nodes = mat.node_tree.nodes
        for n in nodes:
            if n.type == "GROUP":
                if shader_id in n.name and shader_name in n.node_tree.name:
                    if vars.VERSION_STRING in n.name and vars.VERSION_STRING in n.node_tree.name:
                        wrinkle_node = n
                    else:
                        to_remove.append(n)

    for n in to_remove:
        nodes.remove(n)

    # create a new wrinkle shader group node if none
    if create and not wrinkle_node:
        group = nodeutils.get_node_group(shader_name)
        wrinkle_node = nodeutils.make_node_group_node(nodes, group, "Wrinkle Map System", utils.unique_name(shader_id))
        wrinkle_node.width = 240
        utils.log_info("Creating new wrinkle system shader group: " + wrinkle_node.name)
        add_wrinkle_mappings(mat, wrinkle_node, obj, mat_json)

    return wrinkle_node


def add_wrinkle_shader(nodes, links, obj, mat, mat_json, main_shader_name, wrinkle_shader_name = "rl_wrinkle_shader"):
    wrinkle_shader_node = get_wrinkle_shader(obj, mat, mat_json, shader_name = wrinkle_shader_name)
    bsdf_node, main_shader_node, mix_node = nodeutils.get_shader_nodes(mat, main_shader_name)
    wrinkle_shader_node.location = (-2400, 0)
    nodeutils.link_nodes(links, wrinkle_shader_node, "Diffuse Map", main_shader_node, "Diffuse Map")
    nodeutils.link_nodes(links, wrinkle_shader_node, "Roughness Map", main_shader_node, "Roughness Map")
    nodeutils.link_nodes(links, wrinkle_shader_node, "Normal Map", main_shader_node, "Normal Map")
    nodeutils.link_nodes(links, wrinkle_shader_node, "Height Map", main_shader_node, "Height Map")
    nodeutils.link_nodes(links, wrinkle_shader_node, "Height Delta", main_shader_node, "Height Delta")
    return wrinkle_shader_node


def get_wrinkle_params(mat_json):

    wrinkle_params = {}
    overall_weight = 1.0

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

    return wrinkle_params, overall_weight


def add_wrinkle_mappings(mat, node, body_obj, mat_json):

    if not body_obj.data.shape_keys or not body_obj.data.shape_keys.key_blocks:
        return

    wrinkle_defs = {}

    wrinkle_params, overall_weight = get_wrinkle_params(mat_json)

    drivers.add_custom_float_property(body_obj, WRINKLE_STRENGTH_PROP, overall_weight, value_min=0.0, value_max=2.0)
    drivers.add_custom_float_property(body_obj, WRINKLE_CURVE_PROP, 1.0, value_min=0.25, value_max=2.0)

    for wrinkle_name in params.WRINKLE_RULES.keys():
        weight, func = params.WRINKLE_RULES[wrinkle_name]
        if wrinkle_name in wrinkle_params.keys():
            weight *= wrinkle_params[wrinkle_name]["weight"]
        wrinkle_def = { "weight": weight, "func": func, "keys": [] }
        wrinkle_defs[wrinkle_name] = wrinkle_def

    for shape_key, wrinkle_name, range_min, range_max in params.WRINKLE_MAPPINGS:
        if shape_key in body_obj.data.shape_keys.key_blocks:
            if wrinkle_name in params.WRINKLE_RULES.keys():
                weight, func = params.WRINKLE_RULES[wrinkle_name]
                key_def = [shape_key, range_min * weight, range_max * weight]
                wrinkle_defs[wrinkle_name]["keys"].append(key_def)
            else:
                utils.log_error(f"Wrinkle Morph Name: {wrinkle_name} not found in Wrinkle Rules!")
        else:
            utils.log_info(f"Skipping shape key: {shape_key}, not found in body mesh.")

    for socket_name in params.WRINKLE_DRIVERS:
        expr_macro = params.WRINKLE_DRIVERS[socket_name]
        add_wrinkle_node_driver(mat, node, socket_name, body_obj, expr_macro, wrinkle_defs)


def add_wrinkle_node_driver(mat, node, socket_name, obj, expr_macro : str, wrinkle_defs):

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

    socket = node.inputs[socket_name]
    expr_code = f"{WRINKLE_STRENGTH_VAR} * pow({expr_macro}, {WRINKLE_CURVE_VAR})"
    driver = drivers.make_driver(socket, "default_value", "SCRIPTED", expr_code)

    # global vars
    drivers.make_driver_var(driver, "SINGLE_PROP", WRINKLE_STRENGTH_VAR, obj,
                            data_path = f"[\"{WRINKLE_STRENGTH_PROP}\"]")

    drivers.make_driver_var(driver, "SINGLE_PROP", WRINKLE_CURVE_VAR, obj,
                            data_path = f"[\"{WRINKLE_CURVE_PROP}\"]")

    # add driver variables
    for i, var_def in enumerate(var_defs):
        drivers.make_driver_var(driver, "SINGLE_PROP", var_def["name"], var_def["target"],
                                target_type = var_def["target_type"], data_path = var_def["data_path"])


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

        for i, key_def in enumerate(key_defs):
            shape_key_name = key_def[0]
            range_min = key_def[1]
            range_max = key_def[2]
            var_def = {}
            for vdef in var_defs:
                if vdef["shape_key"] == shape_key_name:
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
            if i > 0:
                if func == "MAX" or func == "MIN":
                    var_code += ", "
                elif func == "ADD":
                    var_code += " + "

            if range_min == 0 and range_max == 1:
                var_range_expr = f"{var_name}"
            elif range_min == 0:
                var_range_expr = f"{range_max * weight} * {var_name}"
            else:
                var_range_expr = f"{range_min * weight} + ({range_max * weight} - {range_min * weight}) * {var_name}"

            var_code += var_range_expr

        # add a driver for the node socket input value: node.inputs[socket_name].default_value
        if func == "MAX":
            expr = f"max({var_code})"
        elif func == "MIN":
            expr = f"min({var_code})"
        elif func == "ADD":
            expr = f"({var_code})"

        return f"max(0, {expr})"

    return "0"


def is_wrinkle_system(node):
    wrinkle_shader_id = "(rl_wrinkle_shader)"
    if wrinkle_shader_id in node.name:
        return True
    else:
        return False