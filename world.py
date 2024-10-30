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

import math
import os
import bpy
from mathutils import Vector, Quaternion, Matrix, Euler, Color

from . import colorspace, imageutils, nodeutils, rigidbody, physics, modifiers, utils, vars


def get_default_hdri_path(hdri_name):
    bin_dir, bin_file = os.path.split(bpy.app.binary_path)
    version = bpy.app.version_string[:4]
    hdri_path = os.path.join(bin_dir, version, "datafiles", "studiolights", "world", hdri_name)
    return hdri_path


def copy_material_to_render_world(context):
    shading = utils.get_view_3d_shading(context)
    if shading:
        studio_light = shading.selected_studio_light
        ibl_path = studio_light.path
        loc = Vector((0,0,0))
        rot_z = shading.studiolight_rotate_z
        rot = Vector((0, 0, rot_z))
        str = shading.studiolight_intensity
        col = (1,1,1,1)
        world_setup(context, ibl_path, col, loc, rot, 1.0, str)


def world_setup(context, hdri_path: str, ambient_color, loc: Vector, rot: Vector, sca: float, str: float):
    if type(ambient_color) is Color:
        ambient_color = (ambient_color.r, ambient_color.g, ambient_color.b, 1.0)
    shading = utils.get_view_3d_shading(context)
    if hdri_path and os.path.exists(hdri_path):
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
        bg_node.name = utils.unique_name("(rl_background_node)")
        nodeutils.set_node_input_value(bg_node, "Strength", str)
        nodeutils.set_node_input_value(bg_node, "Color", ambient_color)
        nodeutils.set_node_input_value(mp_node, "Location", loc)
        nodeutils.set_node_input_value(mp_node, "Rotation", rot)
        nodeutils.set_node_input_value(mp_node, "Scale", Vector((sca, sca, sca)))
        nodeutils.link_nodes(links, tc_node, "Generated", mp_node, "Vector")
        nodeutils.link_nodes(links, mp_node, "Vector", et_node, "Vector")
        nodeutils.link_nodes(links, et_node, "Color", bg_node, "Color")
        nodeutils.link_nodes(links, bg_node, "Background", wo_node, "Surface")
        et_node.image = imageutils.load_image(hdri_path, "Linear")
        if shading:
            shading.use_scene_world = False
            shading.use_scene_world_render = True
    else:
        bpy.context.scene.world.use_nodes = True
        nodes = bpy.context.scene.world.node_tree.nodes
        links = bpy.context.scene.world.node_tree.links
        nodes.clear()
        bg_node = nodeutils.make_shader_node(nodes, "ShaderNodeBackground")
        wo_node = nodeutils.make_shader_node(nodes, "ShaderNodeOutputWorld")
        bg_node.location = (10,300)
        wo_node.location = (300,300)
        bg_node.name = utils.unique_name("(rl_background_node)")
        nodeutils.set_node_input_value(bg_node, "Strength", str)
        nodeutils.set_node_input_value(bg_node, "Color", ambient_color)
        nodeutils.link_nodes(links, bg_node, "Background", wo_node, "Surface")
        if shading:
            shading.use_scene_world = False
            shading.use_scene_world_render = True

