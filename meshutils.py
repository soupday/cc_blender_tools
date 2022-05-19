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

import bpy

from . import materials, utils, vars


def add_vertex_group(obj, name):
    if name not in obj.vertex_groups:
        return obj.vertex_groups.new(name = name)
    else:
        #group = obj.vertex_groups[name]
        #clear_vertex_group(obj, group)
        return obj.vertex_groups[name]


def get_vertex_group(obj, name):
    if name not in obj.vertex_groups:
        None
    else:
        #group = obj.vertex_groups[name]
        #clear_vertex_group(obj, group)
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
            weight = 1.0 - utils.smoothstep(0, 0.1, abs(uv.x - 0.5))

            slot = obj.material_slots[poly.material_index]
            if slot.material == mat_left:
                vertex_group_inner_l.add([vertex.index], weight, 'REPLACE')
                vertex_group_all_l.add([vertex.index], 1.0, 'REPLACE')

            elif slot.material == mat_right:
                vertex_group_inner_r.add([vertex.index], weight, 'REPLACE')
                vertex_group_all_r.add([vertex.index], 1.0, 'REPLACE')


def rebuild_eye_vertex_groups(chr_cache):
    for cache in chr_cache.object_cache:
        obj = cache.object
        if cache.is_eye():
            mat_left, mat_right = materials.get_left_right_eye_materials(obj)
            cache_left = chr_cache.get_material_cache(mat_left)
            cache_right = chr_cache.get_material_cache(mat_right)

            if cache_left and cache_right:
                # Re-create the eye displacement group
                generate_eye_vertex_groups(obj, mat_left, mat_right, cache_left, cache_right)


def generate_eye_vertex_groups(obj, mat_left, mat_right, cache_left, cache_right):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    vertex_group_l = add_vertex_group(obj, prefs.eye_displacement_group + "_L")
    vertex_group_r = add_vertex_group(obj, prefs.eye_displacement_group + "_R")

    mesh = obj.data
    ul = mesh.uv_layers[0]
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_entry = mesh.loops[loop_index]
            vertex = mesh.vertices[loop_entry.vertex_index]
            uv = ul.data[loop_entry.index].uv
            x = uv.x - 0.5
            y = uv.y - 0.5
            radial = math.sqrt(x * x + y * y)

            slot = obj.material_slots[poly.material_index]
            if slot.material == mat_left:
                iris_scale = cache_left.parameters.eye_iris_scale
                iris_radius = cache_left.parameters.eye_iris_radius
                depth_radius = cache_left.parameters.eye_iris_depth_radius
                radius = iris_scale * iris_radius * depth_radius
                #weight = 1.0 - utils.saturate(utils.smoothstep(0, radius, radial))
                weight = utils.saturate(utils.remap(0, radius, 1.0, 0.0, radial))
                vertex_group_l.add([vertex.index], weight, 'REPLACE')

            elif slot.material == mat_right:
                iris_scale = cache_right.parameters.eye_iris_scale
                iris_radius = cache_right.parameters.eye_iris_radius
                depth_radius = cache_right.parameters.eye_iris_depth_radius
                radius = iris_scale * iris_radius * depth_radius
                #weight = 1.0 - utils.saturate(utils.smoothstep(0, radius, radial))
                weight = utils.saturate(utils.remap(0, radius, 1.0, 0.0, radial))
                vertex_group_r.add([vertex.index], weight, 'REPLACE')


def get_material_vertex_indices(obj, mat):
    vert_indices = []
    mesh = obj.data
    for poly in mesh.polygons:
        poly_mat = obj.material_slots[poly.material_index].material
        if poly_mat == mat:
            for vert_index in poly.vertices:
                if vert_index not in vert_indices:
                    vert_indices.append(vert_index)
    return vert_indices


def get_material_vertices(obj, mat):
    verts = []
    mesh = obj.data
    for poly in mesh.polygons:
        poly_mat = obj.material_slots[poly.material_index].material
        if poly_mat == mat:
            for vert_index in poly.vertices:
                if vert_index not in verts:
                    verts.append(mesh.vertices[vert_index])
    return verts


def remove_material_verts(obj, mat):
    mesh = obj.data
    utils.clear_selected_objects()
    if utils.edit_mode_to(obj):
        bpy.ops.mesh.select_all(action="DESELECT")
    if utils.object_mode_to(obj):
        for vert in mesh.vertices:
            vert.select = False
        for poly in mesh.polygons:
            poly_mat = obj.material_slots[poly.material_index].material
            if poly_mat == mat:
                for vert_index in poly.vertices:
                    mesh.vertices[vert_index].select = True
    if utils.edit_mode_to(obj):
        bpy.ops.mesh.delete(type='VERT')
    utils.object_mode_to(obj)


def find_shape_key(obj : bpy.types.Object, shape_key_name):
    if obj.type == "MESH":
        if obj.data and obj.data.shape_keys:
            for key_block in obj.data.shape_keys.key_blocks:
                if key_block.name == shape_key_name:
                    return key_block
    return None