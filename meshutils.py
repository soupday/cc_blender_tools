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

import bpy
from . import utils

OCCLUSION_GROUP_INNER = "CC_EyeOcclusion_Inner"
OCCLUSION_GROUP_OUTER = "CC_EyeOcclusion_Outer"
OCCLUSION_GROUP_TOP = "CC_EyeOcclusion_Top"
OCCLUSION_GROUP_BOTTOM = "CC_EyeOcclusion_Bottom"

TEARLINE_GROUP_INNER = "CC_Tearline_Inner"


def generate_eye_occlusion_vertex_groups(obj):

    if OCCLUSION_GROUP_INNER not in obj.vertex_groups:
        vertex_group_inner = obj.vertex_groups.new(name = OCCLUSION_GROUP_INNER)
    else:
        vertex_group_inner = obj.vertex_groups[OCCLUSION_GROUP_INNER]

    if OCCLUSION_GROUP_OUTER not in obj.vertex_groups:
        vertex_group_outer = obj.vertex_groups.new(name = OCCLUSION_GROUP_OUTER)
    else:
        vertex_group_outer = obj.vertex_groups[OCCLUSION_GROUP_OUTER]

    if OCCLUSION_GROUP_TOP not in obj.vertex_groups:
        vertex_group_top = obj.vertex_groups.new(name = OCCLUSION_GROUP_TOP)
    else:
        vertex_group_top = obj.vertex_groups[OCCLUSION_GROUP_TOP]

    if OCCLUSION_GROUP_BOTTOM not in obj.vertex_groups:
        vertex_group_bottom = obj.vertex_groups.new(name = OCCLUSION_GROUP_BOTTOM)
    else:
        vertex_group_bottom = obj.vertex_groups[OCCLUSION_GROUP_BOTTOM]

    mesh = obj.data
    ul = mesh.uv_layers[0]
    index = [0]
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_entry = mesh.loops[loop_index]
            vertex = mesh.vertices[loop_entry.vertex_index]
            uv = ul.data[loop_entry.index].uv
            index[0] = vertex.index
            print(uv)
            vertex_group_inner.add(index, uv.x, 'REPLACE')
            vertex_group_outer.add(index, 1.0 - uv.x, 'REPLACE')
            vertex_group_top.add(index, uv.y, 'REPLACE')
            vertex_group_bottom.add(index, 1.0 - uv.y, 'REPLACE')


def generate_tearline_vertex_groups(obj):

    if TEARLINE_GROUP_INNER not in obj.vertex_groups:
        vertex_group_inner = obj.vertex_groups.new(name = TEARLINE_GROUP_INNER)
    else:
        vertex_group_inner = obj.vertex_groups[TEARLINE_GROUP_INNER]

    mesh = obj.data
    ul = mesh.uv_layers[0]
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_entry = mesh.loops[loop_index]
            vertex = mesh.vertices[loop_entry.vertex_index]
            uv = ul.data[loop_entry.index].uv
            weight = utils.smoothstep(0, 0.05, abs(uv.x - 0.5))
            vertex_group_inner.add([vertex.index], weight, 'REPLACE')
