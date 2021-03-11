import bpy
import mathutils

from .utils import *
from .vars import *

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

def get_input_connected_to(node, socket):
    try:
        return node.outputs[socket].links[0].to_socket.name
    except:
        return None

def get_node_by_id(mat, id):
    if mat.node_tree is not None:
        nodes = mat.node_tree.nodes
        for node in nodes:
            if id in node.name:
                return node
    return None


def get_default_shader_input(mat, input):
    if mat.node_tree is not None:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                if input in n.inputs:
                    return n.inputs[input].default_value
    return 0.0

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
    cursor.x += GRID_SIZE * scale
    if (cursor.x > max_cursor.x):
        max_cursor.x = cursor.x

def drop_cursor(scale = 1.0):
    cursor.y -= GRID_SIZE * scale
    if cursor.y < max_cursor.y:
        max_cursor.y = cursor.y

def step_cursor(scale = 1.0, drop = 0.25):
    cursor_top.x += GRID_SIZE * drop
    cursor.y = cursor_top.y - cursor_top.x
    cursor.x += GRID_SIZE * scale
    if (cursor.x > max_cursor.x):
        max_cursor.x = cursor.x

def step_cursor_if(thing, scale = 1.0, drop = 0.25):
    if thing is not None:
        step_cursor(scale, drop)

def move_new_nodes(dx, dy):

    width = max_cursor.x
    height = -max_cursor.y - GRID_SIZE

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
    image_node.name = unique_name(prop)
    return image_node


def make_value_node(nodes, label, prop, value = 0.0):
    value_node = make_shader_node(nodes, "ShaderNodeValue", 0.4)
    value_node.label = label
    value_node.name = unique_name(prop)
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
    group_node.name = unique_name("(" + name + ")")
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
            node.inputs[socket].default_value = value
        except:
            log_info("Unable to set input: " + node.name + "[" + str(socket) + "]")

def set_node_output(node, socket, value):
    if node is not None:
        try:
            node.outputs[socket].default_value = value
        except:
            log_info("Unable to set output: " + node.name + "[" + str(socket) + "]")

def link_nodes(links, from_node, from_socket, to_node, to_socket):
    if from_node is not None and to_node is not None:
        try:
            links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])
        except:
            log_info("Unable to link: " + from_node.name + "[" + str(from_socket) + "] to " +
                  to_node.name + "[" + str(to_socket) + "]")

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
