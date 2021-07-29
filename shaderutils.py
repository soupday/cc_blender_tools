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

from . import nodeutils

def replace_shader_node(nodes, links, shader_node, label, name, group_name):
    location = shader_node.location
    nodes.remove(shader_node)
    group = nodeutils.get_node_group(group_name)
    shader_node = nodeutils.make_node_group_node(nodes, group, label, name)
    shader_node.name = name
    shader_node.location = location
    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")
    nodeutils.link_nodes(links, shader_node, "BSDF", output_node, "Surface")
    return shader_node



