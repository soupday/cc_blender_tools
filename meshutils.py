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

import bpy, bmesh

from . import materials, utils, vars


def add_vertex_group(obj, name):
    if name not in obj.vertex_groups:
        return obj.vertex_groups.new(name = name)
    else:
        #group = obj.vertex_groups[name]
        #clear_vertex_group(obj, group)
        return obj.vertex_groups[name]


def remove_vertex_group(obj : bpy.types.Object, name):
    if name in obj.vertex_groups:
        obj.vertex_groups.remove(obj.vertex_groups[name])


def get_vertex_group(obj, names) -> bpy.types.VertexGroup:
    if type(names) is str:
        names = [ names ]
    for name in names:
        if name in obj.vertex_groups:
            return obj.vertex_groups[name]
    return None


def clear_vertex_group(obj, vertex_group: bpy.types.VertexGroup):
    all_verts = []
    for v in obj.data.vertices:
        all_verts.append(v.index)
    vertex_group.remove(all_verts)


def set_vertex_group(obj, vertex_group: bpy.types.VertexGroup, value):
    all_verts = []
    for v in obj.data.vertices:
        all_verts.append(v.index)
    vertex_group.add(all_verts, value, 'ADD')


def count_vertex_group(obj, vertex_group: bpy.types.VertexGroup):
    if type(vertex_group) is str or type(vertex_group) is list:
        vertex_group = get_vertex_group(obj, vertex_group)
    count = 0
    if vertex_group:
        vg_idx = vertex_group.index
        for vert in obj.data.vertices:
            for g in vert.groups:
                if g.group == vg_idx:
                    count += 1
    return count


def total_vertex_group_weight(obj, vertex_group: bpy.types.VertexGroup):
    if type(vertex_group) is str or type(vertex_group) is list:
        vertex_group = get_vertex_group(obj, vertex_group)
    weight = 0.0
    if vertex_group:
        vg_idx = vertex_group.index
        for vert in obj.data.vertices:
            for g in vert.groups:
                if g.group == vg_idx:
                    weight += g.weight
    return weight


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
    if chr_cache:
        for obj in chr_cache.get_cache_objects():
            obj_cache = chr_cache.get_object_cache(obj)
            if obj and obj_cache and obj_cache.is_eye() and not obj_cache.disabled:
                mat_left, mat_right = materials.get_left_right_eye_materials(obj)
                cache_left = chr_cache.get_material_cache(mat_left)
                cache_right = chr_cache.get_material_cache(mat_right)

                if cache_left and cache_right:
                    # Re-create the eye displacement group
                    generate_eye_vertex_groups(obj, mat_left, mat_right, cache_left, cache_right)


def generate_eye_vertex_groups(obj, mat_left, mat_right, cache_left, cache_right):
    prefs = vars.prefs()

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
    """Mesh Edit Mode"""
    verts = []
    mesh = obj.data
    for poly in mesh.polygons:
        poly_mat = obj.material_slots[poly.material_index].material
        if poly_mat == mat:
            for vert_index in poly.vertices:
                if vert_index not in verts:
                    verts.append(mesh.vertices[vert_index])
    return verts


def select_material_faces(obj, mat, select = True, deselect_first = False, include_edges = True, include_vertices = True):
    mesh : bpy.types.Mesh = obj.data
    poly : bpy.types.MeshPolygon
    for poly in mesh.polygons:

        poly_mat = obj.material_slots[poly.material_index].material

        if deselect_first:
            poly.select = False
        if poly_mat == mat:
            poly.select = select

        if include_edges:
            for edge_key in poly.edge_keys:
                for edge_index in edge_key:
                    edge = mesh.edges[edge_index]
                    if deselect_first:
                        edge.select = False
                    if poly_mat == mat:
                        edge.select = select

        if include_vertices:
            for vertex_index in poly.vertices:
                vertex = mesh.vertices[vertex_index]
                if deselect_first:
                    vertex.select = False
                if poly_mat == mat:
                    vertex.select = select


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
    try:
        return obj.data.shape_keys.key_blocks[shape_key_name]
    except:
        return None


def objects_have_shape_key(objects, shape_key_name):
    for obj in objects:
        if find_shape_key(obj, shape_key_name) is not None:
            return True
    return False


def get_viseme_profile(objects):
    for key_name in vars.CC4_VISEME_NAMES:
        if objects_have_shape_key(objects, key_name):
            return vars.CC4_VISEME_NAMES

    for key_name in vars.DIRECT_VISEME_NAMES:
        if objects_have_shape_key(objects, key_name):
            return vars.DIRECT_VISEME_NAMES

    # there is some overlap between CC4 facial expression names and CC3 viseme names
    # so consider CC3 visemes last
    return vars.CC3_VISEME_NAMES


def get_facial_profile(objects):
    expressionProfile = "None"
    visemeProfile = "None"

    for obj in objects:

        if (find_shape_key(obj, "Move_Jaw_Down") or
            find_shape_key(obj, "Turn_Jaw_Down") or
            find_shape_key(obj, "Move_Jaw_Down") or
            find_shape_key(obj, "Move_Jaw_Down")):
            expressionProfile = "Traditional"

        if (find_shape_key(obj, "A01_Brow_Inner_Up") or
            find_shape_key(obj, "A06_Eye_Look_Up_Left") or
            find_shape_key(obj, "A15_Eye_Blink_Right") or
            find_shape_key(obj, "A25_Jaw_Open") or
            find_shape_key(obj, "A37_Mouth_Close")):
            if (expressionProfile == "None" or
                expressionProfile == "Traditional"):
                expressionProfile = "ExPlus"

        if (find_shape_key(obj, "Ear_Up_L") or
            find_shape_key(obj, "Ear_Up_R") or
            find_shape_key(obj, "Eyelash_Upper_Up_L") or
            find_shape_key(obj, "Eyelash_Upper_Up_R") or
            find_shape_key(obj, "Eye_L_Look_L") or
            find_shape_key(obj, "Eye_R_Look_R")):
            if (expressionProfile == "None" or
                expressionProfile == "Std"):
                expressionProfile = "Ext"

        if (find_shape_key(obj, "Mouth_L") or
            find_shape_key(obj, "Mouth_R") or
            find_shape_key(obj, "Eye_Wide_L") or
            find_shape_key(obj, "Eye_Wide_R") or
            find_shape_key(obj, "Mouth_Smile") or
            find_shape_key(obj, "Eye_Blink")):
            if expressionProfile == "None":
                expressionProfile = "Std"


        if (find_shape_key(obj, "V_Open") or
            find_shape_key(obj, "V_Tight") or
            find_shape_key(obj, "V_Tongue_up") or
            find_shape_key(obj, "V_Tongue_Raise")):
            visemeProfile = "PairsCC4"

        if (find_shape_key(obj, "Open") or
            find_shape_key(obj, "Tight") or
            find_shape_key(obj, "Tongue_up") or
            find_shape_key(obj, "Tongue_Raise")):
            if (visemeProfile == "PairsCC4" or
                visemeProfile == "Direct"):
                visemeProfile = "PairsCC3"

        if (find_shape_key(obj, "AE") or
            find_shape_key(obj, "EE") or
            find_shape_key(obj, "Er") or
            find_shape_key(obj, "Oh")):
            if visemeProfile == "None":
                visemeProfile = "Direct"

        if (find_shape_key(obj, "Brow_Raise_Inner_Left") or
            find_shape_key(obj, "Brow_Raise_Outer_Left") or
            find_shape_key(obj, "Brow_Drop_Left") or
            find_shape_key(obj, "Brow_Raise_Right")):
            corrections = True

    return expressionProfile, visemeProfile


def set_shading(obj, smooth=True):
    if utils.object_exists_is_mesh(obj):
        for poly in obj.data.polygons:
            poly.use_smooth = smooth
            obj.data.update()


def get_child_objects_with_vertex_groups(parent, group_names, objects = None):
    if objects is None:
        objects = []

    for vg in parent.vertex_groups:
        if vg.name in group_names:
            objects.append(parent)
            break

    for child in parent.children:
        get_child_objects_with_vertex_groups(child, group_names, objects)

    return objects


def has_vertex_color_data(obj):
    if obj and obj.type == "MESH":
        if obj.data.vertex_colors and obj.data.vertex_colors.active:
            color_map = obj.data.vertex_colors.active
            for vcol_data in color_map.data:
                color = vcol_data.color
                for i in range(0,4):
                    if color[i] > 0.0:
                        return True
    return False


def count_selected_vertices(obj):
    count = 0
    if bpy.context.mode == 'EDIT_MESH':
        bm = bmesh.from_edit_mesh(obj.data)
        for v in bm.verts:
            if v.select:
                count += 1
    else:
        for v in obj.data.vertices:
            if v.select:
                count += 1
    return count


def separate_mesh_by_material_slots(obj: bpy.types.Object, slot_indices: list):
    if obj:
        if slot_indices:
            if utils.edit_mode_to(obj, only_this=True):
                bpy.ops.mesh.select_all(action='DESELECT')
                for slot_index in slot_indices:
                    if len(obj.material_slots) > slot_index:
                        bpy.context.object.active_material_index = slot_index
                        bpy.ops.object.material_slot_select()
                count = count_selected_vertices(obj)
                if count > 0 and count < len(obj.data.vertices):
                    bpy.ops.mesh.separate(type="SELECTED")
                    if utils.object_mode():
                        print(bpy.context.selected_objects)
                        for o in bpy.context.selected_objects:
                            if o != obj:
                                print(o)
                                return o
    return None


def separate_mesh_material_type(chr_cache, obj: bpy.types.Object, material_type: str):
    if chr_cache and obj:
        material_slots = []
        if utils.object_exists_is_mesh(obj):
            for slot in obj.material_slots:
                mat = slot.material
                if utils.material_exists(mat):
                    mat_cache = chr_cache.get_material_cache(mat)
                    if mat_cache and mat_cache.material_type == material_type:
                        material_slots.append(slot.slot_index)
        if material_slots:
            return separate_mesh_by_material_slots(obj, material_slots)
    return None








