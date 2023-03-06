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
def make_image_node(nodes, image, name, scale = 1.0):
    if image is None:
        return None
    image_node = make_shader_node(nodes, "ShaderNodeTexImage", scale)
    image_node.image = image
    image_node.name = utils.unique_name(name)
    return image_node


def make_separate_rgb_node(nodes, label, name):
    value_node = make_shader_node(nodes, "ShaderNodeSeparateRGB")
    value_node.label = label
    value_node.name = utils.unique_name(name)
    return value_node


def make_value_node(nodes, label, name, value = 0.0):
    value_node = make_shader_node(nodes, "ShaderNodeValue", 0.4)
    value_node.label = label
    value_node.name = utils.unique_name(name)
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


def make_bump_node(nodes, strength, distance):
    bump_node : bpy.types.ShaderNodeBump = make_shader_node(nodes, "ShaderNodeBump")
    bump_node.inputs["Strength"].default_value = strength
    bump_node.inputs["Distance"].default_value = distance
    return bump_node


def make_normal_map_node(nodes, strength):
    normal_map_node : bpy.types.ShaderNodeBump = make_shader_node(nodes, "ShaderNodeNormalMap")
    normal_map_node.inputs["Strength"].default_value = strength
    return normal_map_node


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


## Node Socket Functions
#


def safe_node_output_socket(node, socket_or_name):
    """Return the node's socket or named output socket."""

    try:
        if type(socket_or_name) == str or type(socket_or_name) == int:
            return node.outputs[socket_or_name]
        else:
            return socket_or_name
    except:
        return None


def safe_node_input_socket(node, socket_or_name):
    """Return the node's socket or named input socket."""

    try:
        if type(socket_or_name) == str or type(socket_or_name) == int:
            return node.inputs[socket_or_name]
        else:
            return socket_or_name
    except:
        return None


def safe_socket_name(socket_or_name):
    """Return the supplied name or socket's name."""

    try:
        if type(socket_or_name) == str:
            return socket_or_name
        elif type(socket_or_name) == int:
            return int(socket_or_name)
        else:
            return socket_or_name.name
    except:
        return None


def get_node_input_value(node : bpy.types.Node, socket, default = None):
    """Returns the node's socket or named input sockets default value
       or if linked to, the connecting node's default output value.\n
       Returns the supplied default value if node/socket is invalid."""

    socket = safe_node_input_socket(node, socket)
    if node and socket:
        try:
            if socket.is_linked:
                connecting_node, connecting_socket = get_node_and_socket_connected_to_input(node, socket)
                return get_node_output_value(connecting_node, connecting_socket, default)
            return socket.default_value
        except:
            return default
    return default


def get_node_output_value(node, socket, default):
    """Returns the node's socket or named output sockets default value.\n
       Returns the supplied default value if node/socket is invalid."""

    socket = safe_node_output_socket(node, socket)
    if node and socket:
        try:
            return socket.default_value
        except:
            return default
    return default


def set_node_input_value(node, socket, value):
    """Sets the node's socket or named input socket's default value.\n
       If the socket's value is multidimensional the value will be set in each dimension."""

    socket = safe_node_input_socket(node, socket)
    if node and socket:
        try:
            socket.default_value = utils.match_dimensions(socket.default_value, value)
        except:
            utils.log_detail("Unable to set input: " + node.name + "[" + str(socket) + "]")


def set_node_output_value(node, socket, value):
    """Sets the node's socket or named output socket's default value.\n
       If the socket's value is multidimensional the value will be set in each dimension."""

    socket = safe_node_output_socket(node, socket)
    if node and socket:
        try:
            socket.default_value = utils.match_dimensions(socket.default_value, value)
        except:
            utils.log_detail("Unable to set output: " + node.name + "[" + str(socket) + "]")


def link_nodes(links, from_node, from_socket, to_node, to_socket):
    """Create's a link between the supplied from_node and to_node's sockets (or named sockets)."""

    if from_node and to_node:
        try:
            from_socket = safe_node_output_socket(from_node, from_socket)
            to_socket = safe_node_input_socket(to_node, to_socket)
            if from_socket and to_socket:
                links.new(from_socket, to_socket)
        except:
            utils.log_detail(f"Unable to link: {from_node.name} [{str(from_socket)}] to {to_node.name} [{str(to_socket)}]")


def unlink_node_output(links, node, socket):
    """Removes the link from the socket (or the node's named output socket)."""

    socket = safe_node_output_socket(node, socket)
    if node and socket:
        try:
            for link in socket.links:
                if link is not None:
                    links.remove(link)
        except:
            utils.log_info("Unable to remove links from: " + node.name + "[" + str(socket) + "]")


def unlink_node_input(links, node, socket):
    """Removes the link from the socket (or the node's named output socket)."""

    socket = safe_node_input_socket(node, socket)
    if node and socket:
        try:
            for link in socket.links:
                if link is not None:
                    links.remove(link)
        except:
            utils.log_info("Unable to remove links from: " + node.name + "[" + str(socket) + "]")


def get_socket_connected_to_output(node, socket):
    """Returns the *first* linked socket connected from the supplied node's output socket (or named output socket)."""

    socket = safe_node_output_socket(node, socket)
    try:
        return socket.links[0].to_socket
    except:
        return None


def get_socket_connected_to_input(node, socket):
    """Returns the linked socket connected to the supplied node's input socket (or named input socket)."""

    socket = safe_node_input_socket(node, socket)
    try:
        return socket.links[0].from_socket
    except:
        return None


def get_node_connected_to_output(node, socket):
    """Returns the *first* linked node connected from the supplied node's input socket (or named input socket)."""

    socket = safe_node_output_socket(node, socket)
    try:
        return socket.links[0].to_node
    except:
        return None


def get_node_connected_to_input(node, socket):
    """Returns the linked node connected to the supplied node's input socket (or named input socket)."""

    socket = safe_node_input_socket(node, socket)
    try:
        return socket.links[0].from_node
    except:
        return None


def get_node_and_socket_connected_to_output(node, socket):
    """Returns the *first* linked node and socket connected from the supplied node's output socket
       (or named output socket)."""

    socket = safe_node_output_socket(node, socket)
    try:
        return socket.links[0].to_node, socket.links[0].to_socket
    except:
        return None, None


def get_node_and_socket_connected_to_input(node, socket):
    """Returns the linked node and socket connected to the the supplied node's input socket
       (or named input socket)."""

    socket = safe_node_input_socket(node, socket)
    try:
        return socket.links[0].from_node, socket.links[0].from_socket
    except:
        return None, None


def has_connected_input(node, socket):
    """Returns True if the node's input socket (or named input socket) is linked to from another node."""

    socket = safe_node_input_socket(node, socket)
    try:
        return socket.is_linked
    except:
        pass
    return False


def is_image_node_connected_to_node(node, image, done):
    """Returns True if there is a linked image node with the supplied image connecting the this node."""

    for socket in node.inputs:
        if socket.is_linked:
            found = is_image_node_connected_to_socket(node, socket, image, done)
            if found:
                return True
    return False


def is_image_node_connected_to_socket(node, socket, image, done):
    """Returns True if there is a linked image node with the supplied image connecting the this node and socket."""

    connected_node = get_node_connected_to_input(node, socket)
    if not connected_node or connected_node in done:
        return False

    done.append(connected_node)

    if connected_node.type == "TEX_IMAGE" and connected_node.image == image:
        return True
    else:
        return is_image_node_connected_to_node(node, image, done)


def get_node_by_id(nodes, id_string):
    """Find a node with a particular id string."""

    for node in nodes:
        if vars.NODE_PREFIX in node.name and id_string in node.name:
            return node
    return None


def get_node_by_id_and_type(nodes, id, type):
    """Find a node with a particular id string and node type."""

    for node in nodes:
        if vars.NODE_PREFIX in node.name and id in node.name and node.type == type:
            return node
    return None


def reset_shader(mat_cache, nodes, links, shader_label, shader_name, shader_group, mix_shader_group):
    shader_id = "(" + str(shader_name) + ")"
    bsdf_id = "(" + str(shader_name) + "_BSDF)"
    mix_id = "(" + str(shader_name) + "_MIX)"
    wrinkle_id = "(rl_wrinkle_shader)"

    group_node: bpy.types.Node = None
    mix_node: bpy.types.Node = None
    bsdf_node: bpy.types.Node = None
    output_node: bpy.types.Node = None
    wrinkle_node: bpy.types.Node = None

    has_group_node = shader_group is not None and shader_group != ""
    has_bsdf = has_group_node
    has_mix_node = mix_shader_group is not None and mix_shader_group != ""

    links.clear()

    for n in nodes:

        if n.type == "BSDF_PRINCIPLED" and has_bsdf and shader_name in n.name:

            if not bsdf_node:
                utils.log_info("Keeping old BSDF: " + n.name)
                bsdf_node = n
            else:
                nodes.remove(n)

        elif n.type == "GROUP" and n.node_tree and shader_name in n.name and vars.VERSION_STRING in n.node_tree.name:

            if wrinkle_id in n.node_tree.name:
                utils.log_info("Keeping old wrinkle shader group: " + n.name)
                wrinkle_node = n

            elif has_group_node and shader_group in n.node_tree.name:
                if not group_node:
                    utils.log_info("Keeping old shader group: " + n.name)
                    group_node = n
                else:
                    nodes.remove(n)

            elif has_mix_node and mix_shader_group in n.node_tree.name:
                if not mix_node:
                    utils.log_info("Keeping old mix shader group: " + n.name)
                    mix_node = n
                else:
                    nodes.remove(n)

            else:
                nodes.remove(n)

        elif n.type == "OUTPUT_MATERIAL":

            if output_node:
                nodes.remove(n)
            else:
                output_node = n

        elif n.type == "TEX_IMAGE":

            if vars.NODE_PREFIX in n.name:
                # keep images
                pass

            elif not mat_cache.user_added:
                # keep all images if it is a user added material
                nodes.remove(n)

        else:
            nodes.remove(n)

    if has_group_node and not group_node:
        group = get_node_group(shader_group)
        group_node = nodes.new("ShaderNodeGroup")
        group_node.node_tree = group
        group_node.name = utils.unique_name(shader_id)
        group_node.label = shader_label
        group_node.width = 240
        utils.log_info("Creating new shader group: " + group_node.name)

    if has_mix_node and not mix_node:
        group = get_node_group(mix_shader_group)
        mix_node = nodes.new("ShaderNodeGroup")
        mix_node.node_tree = group
        mix_node.name = utils.unique_name(mix_id)
        mix_node.label = shader_label
        mix_node.width = 240
        utils.log_info("Creating new mix shader group: " + mix_node.name)

    # if the mix node has no BSDF input, then it doesn't need the Principled BSDF to mix:
    if has_mix_node and has_bsdf:
        if "BSDF" not in mix_node.inputs:
            has_bsdf = False
            if bsdf_node:
                nodes.remove(bsdf_node)
                bsdf_node = None

    if has_bsdf and not bsdf_node:
        bsdf_node = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf_node.name = utils.unique_name(bsdf_id)
        bsdf_node.label = shader_label
        bsdf_node.width = 240
        utils.log_info("Creating new BSDF: " + bsdf_node.name)

    if not output_node:
        output_node = nodes.new("ShaderNodeOutputMaterial")

    if has_bsdf:
        if has_group_node:
            bsdf_node.location = (200, 400)
        else:
            bsdf_node.location = (0,0)

    if has_group_node:
        group_node.location = (-400, 0)

    if has_mix_node:
        mix_node.location = (500, -500)

    output_node.location = (900, -400)

    # connect all group_node outputs to BSDF inputs:
    if has_group_node and has_bsdf:
        for socket in group_node.outputs:
            link_nodes(links, group_node, socket.name, bsdf_node, socket.name)

    # connect group_node outputs to any mix_node inputs:
    if has_mix_node and has_group_node:
        for socket in mix_node.inputs:
            link_nodes(links, group_node, socket.name, mix_node, socket.name)

    # connect up the BSDF to the mix_node:
    if has_mix_node and has_bsdf:
        link_nodes(links, bsdf_node, "BSDF", mix_node, "BSDF")

    # connect the shader to the output
    if has_mix_node:
        link_nodes(links, mix_node, "BSDF", output_node, "Surface")
    elif has_bsdf:
        link_nodes(links, bsdf_node, "BSDF", output_node, "Surface")

    # connect the displacement to the output
    if has_group_node:
        link_nodes(links, group_node, "Displacement", output_node, "Displacement")

    # don't do anything with the old wrinkle shader node yet

    return bsdf_node, group_node


def clean_unused_image_nodes(nodes):
    to_remove = []
    for node in nodes:
        if node.type == "TEX_IMAGE":
            is_linked = False
            for output in node.outputs:
                if output.is_linked:
                    is_linked = True
            if not is_linked:
                to_remove.append(node)

    for node in to_remove:
        utils.log_info("Removing unused image node: " + node.name)
        nodes.remove(node)


def is_texture_pack_system(node):
    if (vars.PACK_DIFFUSEROUGHNESS_ID in node.name or
        vars.PACK_DIFFUSEROUGHNESSBLEND1_ID in node.name or
        vars.PACK_DIFFUSEROUGHNESSBLEND2_ID in node.name or
        vars.PACK_DIFFUSEROUGHNESSBLEND3_ID in node.name or
        vars.PACK_DIFFUSEALPHA_ID in node.name or
        vars.PACK_MRSO_ID in node.name or
        vars.PACK_SSTM_ID in node.name or
        vars.PACK_MSMNAO_ID in node.name or
        vars.PACK_WRINKLEROUGHNESS_ID in node.name or
        vars.PACK_ROOTID_ID in node.name or
        vars.PACK_SSTMMNM_ID in node.name or
        "PACK_SPLIT" in node.name):
        return True
    else:
        return False


def get_node_group(name):
    for group in bpy.data.node_groups:
        if vars.NODE_PREFIX in group.name and name in group.name:
            if vars.VERSION_STRING in group.name:
                return group
    return fetch_node_group(name)


def get_lib_image(name):
    for image in bpy.data.images:
        if vars.NODE_PREFIX in image.name and name in image.name:
            if vars.VERSION_STRING in image.name:
                return image
    return fetch_lib_image(name)


def check_node_groups():
    for name in vars.NODE_GROUPS:
        get_node_group(name)


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
                break
        if match:
            return node
    return None


def find_node_by_type(nodes, type):
    for n in nodes:
        if n.type == type:
            return n
    return None


def find_node_by_type_and_keywords(nodes, type, *keywords):
    for node in nodes:
        if node.type == type:
            match = True
            for keyword in keywords:
                if not keyword in node.name:
                    match = False
                    break
            if match:
                return node
    return None


def find_node_group_by_keywords(nodes, *keywords):
    for node in nodes:
        if node.type == "GROUP" and node.node_tree and node.node_tree.nodes:
            match = True
            for keyword in keywords:
                if not keyword in node.node_tree.name:
                    match = False
                    break
            if match:
                return node
    return None


def get_image_node_mapping(image_node):
    """Returns the location offset, rotation and scale vectors of any attached mapping node to the image node."""

    location = (0,0,0)
    rotation = (0,0,0)
    scale = (1,1,1)
    if image_node and image_node.type == "TEX_IMAGE":
        mapping_node = get_node_connected_to_input(image_node, "Vector")
        if mapping_node:
            if mapping_node.type == "MAPPING":
                location = get_node_input_value(mapping_node, "Location", (0,0,0))
                rotation = get_node_input_value(mapping_node, "Rotation", (0,0,0))
                scale = get_node_input_value(mapping_node, "Scale", (1,1,1))
            elif mapping_node.type == "GROUP": # custom mapping group
                location = get_node_input_value(mapping_node, "Offset", (0,0,0))
                scale = get_node_input_value(mapping_node, "Tiling", (1,1,1))
    return location, rotation, scale


def store_texture_mapping(image_node, mat_cache, texture_type):
    if image_node and image_node.type == "TEX_IMAGE":
        location, rotation, scale = get_image_node_mapping(image_node)
        texture_path = bpy.path.abspath(image_node.image.filepath)
        embedded = image_node.image.packed_file is not None
        image = image_node.image
        mat_cache.set_texture_mapping(texture_type, texture_path, embedded, image, location, rotation, scale)
        utils.log_info("Storing texture Mapping for: " + mat_cache.material.name + " texture: " + texture_type)
        image_id = "(" + texture_type + ")"
        image_node.name = utils.unique_name(image_id)


# link utils

def append_node_group(path, object_name):
    filename = "_LIB.blend"
    datablock = "NodeTree"
    file = os.path.join(path, filename)
    appended_group = None

    if os.path.exists(file):
        bpy.ops.wm.append(directory=os.path.join(path, filename, datablock), filename=object_name, set_fake=False, link=False)

        for g in bpy.data.node_groups:
            if object_name in g.name and vars.NODE_PREFIX not in g.name:
                appended_group = g
                g.name = utils.unique_name(object_name)

    return appended_group


def fetch_node_group(name):
    paths = []
    local_path = utils.local_path()
    if local_path:
        paths.append(local_path)
    paths.append(os.path.dirname(os.path.realpath(__file__)))

    for path in paths:
        utils.log_info("Trying to append: " + path + " > " + name)
        if os.path.exists(path):
            group = append_node_group(path, name)
            if group is not None:
                return group
    utils.log_error("Trying to append group: " + name + ", _LIB.blend library file not found?")
    raise ValueError(f"Unable to append node group: {name} from library file!")


def append_lib_image(path, object_name):
    filename = "_LIB.blend"
    datablock = "Image"
    file = os.path.join(path, filename)
    appended_image = None

    if os.path.exists(file):
        bpy.ops.wm.append(directory=os.path.join(path, filename, datablock), filename=object_name, set_fake=False, link=False)

        for i in bpy.data.images:
            if object_name in i.name and vars.NODE_PREFIX not in i.name:
                utils.log_info("Trying to append image: " + path + " > " + object_name)
                appended_image = i
                i.name = utils.unique_name(object_name)

    return appended_image


def fetch_lib_image(name):
    paths = []
    local_path = utils.local_path()
    if local_path:
        paths.append(local_path)
    paths.append(os.path.dirname(os.path.realpath(__file__)))

    for path in paths:
        if os.path.exists(path):
            image = append_lib_image(path, name)
            if image:
                return image
    utils.log_error("Trying to append image: " + name + ", _LIB.blend library file not found?")
    raise ValueError("Unable to append iamge from library file!")


def get_shader_nodes(mat, shader_name):
    if mat and mat.node_tree:
        nodes = mat.node_tree.nodes
        shader_id = "(" + str(shader_name) + ")"
        bsdf_id = "(" + str(shader_name) + "_BSDF)"
        mix_id = "(" + str(shader_name) + "_MIX)"
        shader_node = bsdf_node = mix_node = None
        for node in nodes:
            if vars.NODE_PREFIX in node.name:
                if shader_id in node.name:
                    shader_node = node
                elif bsdf_id in node.name:
                    bsdf_node = node
                elif mix_id in node.name:
                    mix_node = node
        return bsdf_node, shader_node, mix_node
    return None, None, None


def get_bsdf_node(mat):
    if mat and mat.node_tree:
        nodes = mat.node_tree.nodes
        for node in nodes:
            if node.type == "BSDF_PRINCIPLED":
                return node
    return None


def get_tiling_node(mat, shader_name, texture_type):
    if mat and mat.node_tree:
        nodes = mat.node_tree.nodes
        shader_id = "(tiling_" + shader_name + "_" + texture_type + "_mapping)"
        return get_node_by_id(nodes, shader_id)
    return None


def get_tiling_node_from_nodes(nodes, shader_name, texture_type):
    shader_id = "(tiling_" + shader_name + "_" + texture_type + "_mapping)"
    return get_node_by_id(nodes, shader_id)


def create_custom_image_node(nodes, node_name, image, location = (0, 0)):
    # find or create the bake image node
    image_node = find_node_by_type_and_keywords(nodes, "TEX_IMAGE", node_name)
    if not image_node:
        image_node = make_image_node(nodes, image, node_name)
    if image_node.image != image:
        image_node.image = image
    image_node.location = location
    return image_node


# e.g.
# Normal:Height
# Normal:Color
# Normal:Normal:Color
def trace_input_sockets(node, socket_trace : str):
    sockets = socket_trace.split(":")
    trace_node = None
    trace_socket = None
    if node and socket_trace:
        try:
            if sockets:
                trace_node : bpy.types.Node = node
                for socket_name in sockets:
                    if socket_name in trace_node.inputs and trace_node.inputs[socket_name].is_linked:
                        socket : bpy.types.NodeSocket = trace_node.inputs[socket_name]
                        link = socket.links[0]
                        trace_node = link.from_node
                        trace_socket = link.from_socket.name
                    else:
                        trace_node = None
                        trace_socket = None
                        break
        except:
            trace_node = None
            trace_socket = None

    return trace_node, trace_socket


def trace_input_value(node, socket_trace, default_value):
    if node and socket_trace:
        sockets = socket_trace.split(":")
        try:
            value_socket = sockets[-1]
            sockets = sockets[:-1]
            trace_node : bpy.types.Node = node
            if sockets:
                for socket_name in sockets:
                    if socket_name in trace_node.inputs and trace_node.inputs[socket_name].is_linked:
                        socket : bpy.types.NodeSocket = trace_node.inputs[socket_name]
                        link = socket.links[0]
                        trace_node = link.from_node
                    else:
                        trace_node = None
                        break
            if trace_node:
                return trace_node.inputs[value_socket].default_value
        except:
            pass
    return default_value


def set_trace_input_value(node, socket_trace, value):
    if node and socket_trace:
        sockets = socket_trace.split(":")
        try:
            value_socket = sockets[-1]
            sockets = sockets[:-1]
            trace_node : bpy.types.Node = node
            if sockets:
                for socket_name in sockets:
                    if socket_name in trace_node.inputs and trace_node.inputs[socket_name].is_linked:
                        socket : bpy.types.NodeSocket = trace_node.inputs[socket_name]
                        link = socket.links[0]
                        trace_node = link.from_node
                    else:
                        trace_node = None
                        break
            if trace_node:
                trace_node.inputs[value_socket].default_value = value
                return True
        except:
            pass
    return False


def furthest_from(n0, dir, *nodes):
    dir.normalize()
    most = 0
    result = n0
    for n in nodes:
        if n and n0:
            dn = (n.location - n0.location)
            proj = dir.dot(dn)
            if proj > most:
                most = proj
                result = n
    return result


def closest_to(n0, dir, *nodes):
    dir.normalize()
    least = 9999
    result = n0
    for n in nodes:
        if n and n0:
            dn = (n.location - n0.location)
            proj = dir.dot(dn)
            if proj < least:
                least = proj
                result = n
    return result