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
from . import vars


def add_vertex_group(obj, name):
    if name not in obj.vertex_groups:
        return obj.vertex_groups.new(name = name)
    else:
        group = obj.vertex_groups[name]
        clear_vertex_group(group)
        return obj.vertex_groups[name]


def clear_vertex_group(obj, vertex_group):
    all_verts = []
    for v in obj.data.vertices:
        all_verts.append(v.index)
    vertex_group.remove(all_verts)


def set_vertex_group(obj, vertex_group, value):
    all_verts = []
    for v in obj.data.vertices:
        all_verts.append(v.index)
    vertex_group.add(all_verts, value, 'ADD')


def generate_eye_occlusion_vertex_groups(obj, mat_left, mat_right):

    vertex_group_inner_l = add_vertex_group(obj, vars.OCCLUSION_GROUP_INNER + "_L")
    vertex_group_outer_l = add_vertex_group(obj, vars.OCCLUSION_GROUP_OUTER + "_L")
    vertex_group_top_l = add_vertex_group(obj, vars.OCCLUSION_GROUP_TOP + "_L")
    vertex_group_bottom_l = add_vertex_group(obj, vars.OCCLUSION_GROUP_BOTTOM + "_L")
    vertex_group_all_l = add_vertex_group(obj, vars.OCCLUSION_GROUP_ALL + "_L")

    vertex_group_inner_r = add_vertex_group(obj, vars.OCCLUSION_GROUP_INNER + "_R")
    vertex_group_outer_r = add_vertex_group(obj, vars.OCCLUSION_GROUP_OUTER + "_R")
    vertex_group_top_r = add_vertex_group(obj, vars.OCCLUSION_GROUP_TOP + "_R")
    vertex_group_bottom_r = add_vertex_group(obj, vars.OCCLUSION_GROUP_BOTTOM + "_R")
    vertex_group_all_r = add_vertex_group(obj, vars.OCCLUSION_GROUP_ALL + "_R")

    mesh = obj.data
    ul = mesh.uv_layers[0]
    index = [0]
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_entry = mesh.loops[loop_index]
            vertex = mesh.vertices[loop_entry.vertex_index]
            uv = ul.data[loop_entry.index].uv
            index[0] = vertex.index

            slot = obj.material_slots[poly.material_index]
            if slot.material == mat_left:
                vertex_group_inner_l.add(index, uv.x, 'REPLACE')
                vertex_group_outer_l.add(index, 1.0 - uv.x, 'REPLACE')
                vertex_group_top_l.add(index, uv.y, 'REPLACE')
                vertex_group_bottom_l.add(index, 1.0 - uv.y, 'REPLACE')
                vertex_group_all_l.add([vertex.index], 1.0, 'REPLACE')
            elif slot.material == mat_right:
                vertex_group_inner_r.add(index, uv.x, 'REPLACE')
                vertex_group_outer_r.add(index, 1.0 - uv.x, 'REPLACE')
                vertex_group_top_r.add(index, uv.y, 'REPLACE')
                vertex_group_bottom_r.add(index, 1.0 - uv.y, 'REPLACE')
                vertex_group_all_r.add([vertex.index], 1.0, 'REPLACE')


def generate_tearline_vertex_groups(obj, mat_left, mat_right):

    vertex_group_inner_l = add_vertex_group(obj, vars.TEARLINE_GROUP_INNER + "_L")
    vertex_group_all_l = add_vertex_group(obj, vars.TEARLINE_GROUP_ALL + "_L")
    vertex_group_inner_r = add_vertex_group(obj, vars.TEARLINE_GROUP_INNER + "_R")
    vertex_group_all_r = add_vertex_group(obj, vars.TEARLINE_GROUP_ALL + "_R")

    mesh = obj.data
    ul = mesh.uv_layers[0]
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_entry = mesh.loops[loop_index]
            vertex = mesh.vertices[loop_entry.vertex_index]
            uv = ul.data[loop_entry.index].uv
            weight = 1.0 - utils.smoothstep(0, 0.05, abs(uv.x - 0.5))

            slot = obj.material_slots[poly.material_index]
            if slot.material == mat_left:
                vertex_group_inner_l.add([vertex.index], weight, 'REPLACE')
                vertex_group_all_l.add([vertex.index], 1.0, 'REPLACE')
            elif slot.material == mat_right:
                vertex_group_inner_r.add([vertex.index], weight, 'REPLACE')
                vertex_group_all_r.add([vertex.index], 1.0, 'REPLACE')


