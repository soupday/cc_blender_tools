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

import os

import bpy
import mathutils

from . import utils, vars

cursor = mathutils.Vector((0,0))
cursor_top = mathutils.Vector((0,0))
max_cursor = mathutils.Vector((0,0))
new_nodes = []

def get_shader_input(mat, input):
    if mat.node_tree is not None:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                if input in n.inputs:
                    return n.inputs[input]
    return None


def get_socket_connected_to_output(node, socket):
    try:
        return node.outputs[socket].links[0].to_socket.name
    except:
        return None


def get_socket_connected_to_input(node, socket):
    try:
        return node.inputs[socket].links[0].from_socket.name
    except:
        return None


def get_node_connected_to_output(node, socket):
    try:
        return node.outputs[socket].links[0].to_node
    except:
        return None


def get_node_connected_to_input(node, socket):
    try:
        return node.inputs[socket].links[0].from_node
    except:
        return None


def has_connected_input(node, socket):
    try:
        if len(node.inputs[socket].links) > 0:
            return True
    except:
        pass
    return False


def get_node_by_id(nodes, id):
    for node in nodes:
        if vars.NODE_PREFIX in node.name and id in node.name:
            return node
    return None


def get_default_shader_input(mat, input):
    if mat.node_tree is not None:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                if input in n.inputs:
                    return n.inputs[input].default_value
    return 0.0

def set_default_shader_input(mat, input, value):
    if mat.node_tree is not None:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                if input in n.inputs:
                    n.inputs[input].default_value = value


def is_input_connected(input):
    if len(input.links) > 0:
        return True
    return False


def clear_cursor():
    cursor_top.x = 0
    cursor_top.y = 0
    cursor.x = 0
    cursor.y = 0
    max_cursor.x = 0
    max_cursor.y = 0
    new_nodes.clear()

def reset_cursor():
    cursor_top.y = max_cursor.y
    cursor_top.x = 0
    cursor.x = 0
    cursor.y = cursor_top.y

def advance_cursor(scale = 1.0):
    cursor.y = cursor_top.y - cursor_top.x
    cursor.x += vars.GRID_SIZE * scale
    if (cursor.x > max_cursor.x):
        max_cursor.x = cursor.x

def drop_cursor(scale = 1.0):
    cursor.y -= vars.GRID_SIZE * scale
    if cursor.y < max_cursor.y:
        max_cursor.y = cursor.y

def step_cursor(scale = 1.0, drop = 0.25):
    cursor_top.x += vars.GRID_SIZE * drop
    cursor.y = cursor_top.y - cursor_top.x
    cursor.x += vars.GRID_SIZE * scale
    if (cursor.x > max_cursor.x):
        max_cursor.x = cursor.x

def step_cursor_if(thing, scale = 1.0, drop = 0.25):
    if thing is not None:
        step_cursor(scale, drop)

def move_new_nodes(dx, dy):

    width = max_cursor.x
    height = -max_cursor.y - vars.GRID_SIZE

    for node in new_nodes:
        node.location.x += (dx) - width
        node.location.y += (dy) + (height / 2)

    clear_cursor()

def make_shader_node(nodes, type, scale = 1.0):
    shader_node = nodes.new(type)
    shader_node.location = cursor
    new_nodes.append(shader_node)
    drop_cursor(scale)
    return shader_node

## color_space: Non-Color, sRGB
def make_image_node(nodes, image, prop, scale = 1.0):
    if image is None:
        return None
    image_node = make_shader_node(nodes, "ShaderNodeTexImage", scale)
    image_node.image = image
    image_node.name = utils.unique_name(prop)
    return image_node


def make_value_node(nodes, label, prop, value = 0.0):
    value_node = make_shader_node(nodes, "ShaderNodeValue", 0.4)
    value_node.label = label
    value_node.name = utils.unique_name(prop)
    value_node.outputs["Value"].default_value = value
    return value_node

def make_mixrgb_node(nodes, blend_type):
    mix_node = make_shader_node(nodes, "ShaderNodeMixRGB", 0.8)
    mix_node.blend_type = blend_type
    return mix_node

def make_math_node(nodes, operation, value1 = 0.5, value2 = 0.5):
    math_node = make_shader_node(nodes, "ShaderNodeMath", 0.6)
    math_node.operation = operation
    math_node.inputs[0].default_value = value1
    math_node.inputs[1].default_value = value2
    return math_node

def make_rgb_node(nodes, label, value = [1.0, 1.0, 1.0, 1.0]):
    rgb_node = make_shader_node(nodes, "ShaderNodeRGB", 0.8)
    rgb_node.label = label
    rgb_node.outputs["Color"].default_value = value
    return rgb_node

def make_vectormath_node(nodes, operation):
    vm_node = make_shader_node(nodes, "ShaderNodeVectorMath", 0.6)
    vm_node.operation = operation
    return vm_node

def make_node_group_node(nodes, group, label, name):
    group_node = make_shader_node(nodes, "ShaderNodeGroup")
    group_node.node_tree = group
    group_node.label = label
    group_node.width = 240
    group_node.name = utils.unique_name("(" + name + ")")
    return group_node

def get_node_input(node, input, default):
    if node is not None:
        try:
            return node.inputs[input].default_value
        except:
            return default
    return default

def get_node_output(node, output, default):
    if node is not None:
        try:
            return node.outputs[output].default_value
        except:
            return default
    return default

def set_node_input(node, socket, value):

    if node is not None:
        try:
            node.inputs[socket].default_value = utils.match_dimensions(node.inputs[socket].default_value, value)
        except:
            utils.log_info("Unable to set input: " + node.name + "[" + str(socket) + "]")

def set_node_output(node, socket, value):
    if node is not None:
        try:
            node.outputs[socket].default_value = utils.match_dimensions(node.outputs[socket].default_value, value)
        except:
            utils.log_info("Unable to set output: " + node.name + "[" + str(socket) + "]")

def link_nodes(links, from_node, from_socket, to_node, to_socket):
    if from_node is not None and to_node is not None:
        try:
            links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])
        except:
            utils.log_info("Unable to link: " + from_node.name + "[" + str(from_socket) + "] to " +
                  to_node.name + "[" + str(to_socket) + "]")

def unlink_node(links, node, socket):
    if node is not None:
        try:
            socket_links = node.inputs[socket].links
            for link in socket_links:
                if link is not None:
                    links.remove(link)
        except:
            utils.log_info("Unable to remove links from: " + node.name + "[" + str(socket) + "]")


def reset_nodes(mat):
    if not mat.use_nodes:
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    links.clear()

    for n in nodes:
        if n.type != "BSDF_PRINCIPLED":
            nodes.remove(n)

    if len(nodes) == 0:
        shader = nodes.new("ShaderNodeBsdfPrincipled")
    else:
        shader = nodes[0]

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location.x += 400

    link_nodes(links, shader, "BSDF", out, "Surface")


def get_node_group(name):
    for group in bpy.data.node_groups:
        if vars.NODE_PREFIX in group.name and name in group.name:
            if vars.VERSION_STRING in group.name:
                return group
    return fetch_node_group(name)


def check_node_groups():
    for name in vars.NODE_GROUPS:
        get_node_group(name)
    adjust_groups()


def adjust_groups():
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    group = get_node_group("color_hair_mixer")

    # does nothing yet...


def remove_all_groups():
    for group in bpy.data.node_groups:
        if vars.NODE_PREFIX in group.name:
            bpy.data.node_groups.remove(group)


def rebuild_node_groups():
    remove_all_groups()
    check_node_groups()
    return


def find_node_by_keywords(nodes, *keywords):
    for node in nodes:
        match = True
        for keyword in keywords:
            if not keyword in node.name:
                match = False
        if match:
            return node
    return None


def find_node_by_type(nodes, type):
    for n in nodes:
        if n.type == type:
            return n


def store_texture_mapping(image_node, mat_cache, texture_type):
    if image_node and image_node.type == "TEX_IMAGE":
        mapping_node = get_node_connected_to_input(image_node, "Vector")
        if mapping_node and mapping_node.type == "MAPPING":
            location = get_node_input(mapping_node, "Location", (0,0,0))
            rotation = get_node_input(mapping_node, "Rotation", (0,0,0))
            scale = get_node_input(mapping_node, "Scale", (1,1,1))
        else:
            location = (0,0,0)
            rotation = (0,0,0)
            scale = (1,1,1)
        texture_path = image_node.image.filepath
        embedded = image_node.image.packed_file is not None
        image = image_node.image
        mat_cache.set_texture_mapping(texture_type, texture_path, embedded, image, location, rotation, scale)
        utils.log_info("Storing texture Mapping for: " + mat_cache.material.name + " texture: " + texture_type)



# link utils

def append_node_group(path, object_name):
    for g in bpy.data.node_groups:
        g.tag = True

    filename = "_LIB.blend"
    datablock = "NodeTree"
    file = os.path.join(path, filename)
    if os.path.exists(file):
        bpy.ops.wm.append(directory=os.path.join(path, filename, datablock), filename=object_name, set_fake=False, link=False)

    appended_group = None
    for g in bpy.data.node_groups:
        if not g.tag and object_name in g.name:
            appended_group = g
            g.name = utils.unique_name(object_name)
        g.tag = False
    return appended_group


def fetch_node_group(name):

    paths = [bpy.path.abspath("//"),
             os.path.dirname(os.path.realpath(__file__)),
             ]
    for path in paths:
        utils.log_info("Trying to append: " + path + " > " + name)
        if os.path.exists(path):
            group = append_node_group(path, name)
            if group is not None:
                return group
    utils.log_error("Trying to append group: " + name + ", _LIB.blend library file not found?")
    raise ValueError("Unable to append node group from library file!")


def append_lib_image(path, object_name):
    for i in bpy.data.images:
        i.tag = True

    filename = "_LIB.blend"
    datablock = "Image"
    file = os.path.join(path, filename)
    if os.path.exists(file):
        bpy.ops.wm.append(directory=os.path.join(path, filename, datablock), filename=object_name, set_fake=False, link=False)

    appended_image = None
    for i in bpy.data.images:
        if not i.tag and object_name in i.name:
            appended_image = i
            i.name = utils.unique_name(object_name)
        i.tag = False
    return appended_image


def fetch_lib_image(name):

    paths = [bpy.path.abspath("//"),
             os.path.dirname(os.path.realpath(__file__)),
             ]
    for path in paths:
        utils.log_info("Trying to append image: " + path + " > " + name)
        if os.path.exists(path):
            image = append_lib_image(path, name)
            if image:
                return image
    utils.log_error("Trying to append image: " + name + ", _LIB.blend library file not found?")
    raise ValueError("Unable to append iamge from library file!")


def get_shader_node(mat, shader_name):
    if mat and mat.node_tree:
        nodes = mat.node_tree.nodes
        shader_id = "(" + shader_name + ")"
        return get_node_by_id(nodes, shader_id)
    return None


def get_tiling_node(mat, shader_name, texture_type):
    if mat and mat.node_tree:
        nodes = mat.node_tree.nodes
        shader_id = "(tiling_" + shader_name + "_" + texture_type + "_mapping)"
        return get_node_by_id(nodes, shader_id)
    return None
