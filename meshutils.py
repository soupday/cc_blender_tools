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

import bpy, bmesh, mathutils

from . import materials, geom, jsonutils, utils, vars


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


def set_vertex_group(obj, vertex_group, value):
    if type(vertex_group) is str:
        try:
            vertex_group = obj.vertex_groups[vertex_group]
        except:
            vertex_group = None
    if vertex_group:
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
    expressionProfile = "UNKNOWN"
    visemeProfile = "UNKNOWN"

    for obj in objects:

        if obj.type != "MESH": continue

        if (find_shape_key(obj, "Move_Jaw_Down") or
            find_shape_key(obj, "Turn_Jaw_Down") or
            find_shape_key(obj, "Move_Jaw_Down") or
            find_shape_key(obj, "Move_Jaw_Down")):
            expressionProfile = "TRA"

        if (find_shape_key(obj, "A01_Brow_Inner_Up") or
            find_shape_key(obj, "A06_Eye_Look_Up_Left") or
            find_shape_key(obj, "A15_Eye_Blink_Right") or
            find_shape_key(obj, "A25_Jaw_Open") or
            find_shape_key(obj, "A37_Mouth_Close")):
            if (expressionProfile == "UNKNOWN"):
                expressionProfile = "TRA"

        if (find_shape_key(obj, "Ear_Up_L") or
            find_shape_key(obj, "Ear_Up_R") or
            find_shape_key(obj, "Eyelash_Upper_Up_L") or
            find_shape_key(obj, "Eyelash_Upper_Up_R") or
            find_shape_key(obj, "Eye_L_Look_L") or
            find_shape_key(obj, "Eye_R_Look_R")):
            if (expressionProfile == "UNKNOWN" or
                expressionProfile == "STD"):
                expressionProfile = "EXT"

        if (find_shape_key(obj, "Mouth_L") or
            find_shape_key(obj, "Mouth_R") or
            find_shape_key(obj, "Eye_Wide_L") or
            find_shape_key(obj, "Eye_Wide_R") or
            find_shape_key(obj, "Mouth_Smile") or
            find_shape_key(obj, "Eye_Blink")):
            if expressionProfile == "UNKNOWN":
                expressionProfile = "STD"

        if (find_shape_key(obj, "V_Open") or
            find_shape_key(obj, "V_Tight") or
            find_shape_key(obj, "V_Tongue_up") or
            find_shape_key(obj, "V_Tongue_Raise")):
            visemeProfile = "PAIRS4"

        if (find_shape_key(obj, "Open") or
            find_shape_key(obj, "Tight") or
            find_shape_key(obj, "Tongue_up") or
            find_shape_key(obj, "Tongue_Raise")):
            if (visemeProfile == "PAIRS4" or
                visemeProfile == "DIRECT"):
                visemeProfile = "PAIRS3"

        if (find_shape_key(obj, "AE") or
            find_shape_key(obj, "EE") or
            find_shape_key(obj, "Er") or
            find_shape_key(obj, "Oh")):
            if visemeProfile == "UNKNOWN":
                visemeProfile = "DIRECT"

    return expressionProfile, visemeProfile


def set_facial_profile(objects, facial_profile, viseme_profile):
    for obj in objects:
        if obj.type != "MESH": continue
        if facial_profile != "NONE" and facial_profile != "UNKNOWN":
            if (find_shape_key(obj, "Move_Jaw_Down") or
                find_shape_key(obj, "Turn_Jaw_Down") or
                find_shape_key(obj, "Move_Jaw_Down") or
                find_shape_key(obj, "Move_Jaw_Down") or
                find_shape_key(obj, "A01_Brow_Inner_Up") or
                find_shape_key(obj, "A06_Eye_Look_Up_Left") or
                find_shape_key(obj, "A15_Eye_Blink_Right") or
                find_shape_key(obj, "A25_Jaw_Open") or
                find_shape_key(obj, "A37_Mouth_Close") or
                find_shape_key(obj, "Ear_Up_L") or
                find_shape_key(obj, "Ear_Up_R") or
                find_shape_key(obj, "Eyelash_Upper_Up_L") or
                find_shape_key(obj, "Eyelash_Upper_Up_R") or
                find_shape_key(obj, "Eye_L_Look_L") or
                find_shape_key(obj, "Eye_R_Look_R") or
                find_shape_key(obj, "Mouth_L") or
                find_shape_key(obj, "Mouth_R") or
                find_shape_key(obj, "Eye_Wide_L") or
                find_shape_key(obj, "Eye_Wide_R") or
                find_shape_key(obj, "Mouth_Smile") or
                find_shape_key(obj, "Eye_Blink")):
                utils.set_prop(obj, "rl_facial_profile", facial_profile)
        if viseme_profile != "NONE" and viseme_profile != "UNKNOWN":
            if (find_shape_key(obj, "V_Open") or
                find_shape_key(obj, "V_Tight") or
                find_shape_key(obj, "V_Tongue_up") or
                find_shape_key(obj, "V_Tongue_Raise") or
                find_shape_key(obj, "Open") or
                find_shape_key(obj, "Tight") or
                find_shape_key(obj, "Tongue_up") or
                find_shape_key(obj, "Tongue_Raise") or
                find_shape_key(obj, "AE") or
                find_shape_key(obj, "EE") or
                find_shape_key(obj, "Er") or
                find_shape_key(obj, "Oh")):
                utils.set_prop(obj, "rl_viseme_profile", viseme_profile)


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
                        for o in bpy.context.selected_objects:
                            if o != obj:
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


def get_head_material_and_json(chr_cache, chr_json):
    head_mat = None
    head_mat_cache = None
    head_mat_json = None

    # find the head material in the character
    for mat_cache in chr_cache.head_material_cache:
        mat = mat_cache.material
        if mat_cache.material_type == "SKIN_HEAD" and utils.material_exists(mat):
            head_mat = mat
            head_mat_cache = mat_cache

    # find the head material json, from it's original json object
    # the head material may have been split from the original body mesh,
    # so we look in all the meshes for the head material
    for obj in chr_cache.get_cache_objects():
        obj_cache = chr_cache.get_object_cache(obj)
        if obj.type == "MESH":
            if head_mat.name in obj.data.materials:
                mat_json = jsonutils.get_json(chr_json, f"Meshes/{obj_cache.source_name}/Materials/{head_mat_cache.source_name}")
                if mat_json and jsonutils.get_json(mat_json, "Custom Shader/Shader Name") == "RLHead":
                    head_mat_json = mat_json
                    break

    return head_mat, head_mat_json


def get_head_body_object_quick(chr_cache):
    if chr_cache:
        body_objects = chr_cache.get_objects_of_type("BODY")
        for obj in body_objects:
            if "wrinkle_source" in obj:
                if obj["wrinkle_source"]:
                    return obj
        return get_head_body_object(chr_cache)
    return None


def get_eye_object(chr_cache):
    # TODO merged expressions and morphs....
    if chr_cache:
        return chr_cache.get_objects_of_type("EYE")
    return None


def get_tongue_object(chr_cache):
    # TODO merged expressions and morphs....
    if chr_cache:
        return chr_cache.get_objects_of_type("TONGUE")
    return None


def get_head_body_object(chr_cache):
    if not chr_cache: return None
    body_cache = chr_cache.get_body_cache()
    arm = chr_cache.get_armature()

    # collect all possible body objects together
    head_bones = [ "CC_Base_Head", "head", "spine.006" ]
    body_objects = {}

    if body_cache:
        body_id = body_cache.object_id
        for child in arm.children:
            if utils.get_rl_object_id(child) == body_id and child not in body_objects:
                body_objects[child] = total_vertex_group_weight(child, head_bones)
    else:
        for child in arm.children:
            if child not in body_objects:
                body_objects[child] = total_vertex_group_weight(child, head_bones)

    # try to find which one contains the head (contains the most weight to head bone)
    weight = -1
    body = None
    if body_objects:
        for obj in body_objects:
            try:
                del obj["wrinkle_source"]
            except: ...
            if body_objects[obj] > weight:
                weight = body_objects[obj]
                body = obj

    # fall back to the imported source body if nothing works
    if not body:
        body = chr_cache.get_body()

    if body:
        try:
            body["wrinkle_source"] = True
        except: ...

    return body


LASH_DATA = None

def store_lash_data(chr_cache):
    global LASH_DATA
    # copy body
    body_obj = utils.duplicate_object(get_head_body_object(chr_cache))
    head_obj = separate_mesh_material_type(chr_cache, body_obj, "SKIN_HEAD")
    lash_obj = separate_mesh_material_type(chr_cache, body_obj, "EYELASH")
    print(f"HEAD: {head_obj.name}")
    print(f"LASH: {lash_obj.name}")
    utils.delete_object(body_obj)

    mesh = lash_obj.data
    head_mesh = head_obj.data
    ul = mesh.uv_layers[0]
    verts_done = set()
    verts = {}
    i = 0
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            loop_entry = mesh.loops[loop_index]
            if loop_entry.vertex_index not in verts_done:
                i += 1
                verts_done.add(loop_entry.vertex_index)
                vertex = mesh.vertices[loop_entry.vertex_index]
                lash_co = vertex.co
                lash_uv = ul.data[loop_entry.index].uv
                uv_id = lash_uv.to_tuple(5)
                success, closest_local_co, closest_local_no, closest_face_index = head_obj.closest_point_on_mesh(lash_co)
                head_co = closest_local_co
                dir: mathutils.Vector = (lash_co - head_co)
                head_dist = dir.length
                head_dir = dir.normalized()
                head_uv = uv_from_point(head_mesh, head_co, closest_face_index)
                verts[uv_id] = (lash_uv.copy(), head_uv.copy(), head_dist, head_dir)
    utils.delete_object(lash_obj)
    utils.delete_object(head_obj)
    LASH_DATA = verts


def restore_lash_data(chr_cache):
    diag = geom.diag_mesh_create()
    global LASH_DATA
    body_obj = get_head_body_object(chr_cache)
    lash_index = materials.get_material_slot_by_type(chr_cache, body_obj, "EYELASH")
    head_index = materials.get_material_slot_by_type(chr_cache, body_obj, "SKIN_HEAD")
    body_tm = geom.get_triangulated_bmesh(body_obj)
    mesh: bpy.types.Mesh = body_obj.data
    ul = mesh.uv_layers[0]
    verts_done = set()
    poly: bpy.types.MeshPolygon
    vertex: bpy.types.MeshVertex
    for poly in mesh.polygons:
        if poly.material_index == lash_index:
            for loop_index in poly.loop_indices:
                loop_entry = mesh.loops[loop_index]
                if loop_entry.vertex_index not in verts_done:
                    verts_done.add(loop_entry.vertex_index)
                    vertex = mesh.vertices[loop_entry.vertex_index]
                    lash_uv = ul.data[loop_entry.index].uv.copy()
                    uv_id = lash_uv.to_tuple(5)
                    if uv_id in LASH_DATA:
                        old_lash_uv, head_uv, head_dist, head_dir = LASH_DATA[uv_id]
                        head_co = geom.get_local_from_uv(body_obj, body_tm, head_index, head_uv.to_3d(), 0.001)
                        geom.diag_mesh_add_vert(head_co)
                        target_co = head_co + (head_dir * head_dist)
                        vertex.co = target_co.copy()
    geom.diag_finish()
    mesh.update()


def uv_from_point(mesh: bpy.types.Mesh, co, face_index):
    ul = mesh.uv_layers[0]
    poly: bpy.types.MeshPolygon = mesh.polygons[face_index]
    num_verts = len(poly.loop_indices)
    num_tris = num_verts - 2
    loop0 = mesh.loops[poly.loop_indices[0]]
    v0 = mesh.vertices[loop0.vertex_index].co
    uv0 = ul.data[loop0.index].uv.to_3d()
    for i in range(0, num_tris):
        j = i + 1
        k = i + 2
        loopj = mesh.loops[poly.loop_indices[j]]
        vj = mesh.vertices[loopj.vertex_index].co
        uvj = ul.data[loopj.index].uv.to_3d()
        loopk = mesh.loops[poly.loop_indices[k]]
        vk = mesh.vertices[loopk.vertex_index].co
        uvk = ul.data[loopk.index].uv.to_3d()
        uv = mathutils.geometry.barycentric_transform(co, v0, vj, vk, uv0, uvj, uvk)
        if mathutils.geometry.intersect_point_tri_2d(uv, uv0, uvj, uvk):
            uv = mathutils.Vector((uv.x, uv.y))
            return uv
    # otherwise return the uv coords of the face vertex nearest to the co
    d = (v0 - co).length
    uv = ul.data[loop0.index].uv
    for i in range(1, num_verts):
        loopi = mesh.loops[poly.loop_indices[i]]
        vi = mesh.vertices[loopi.vertex_index].co
        di = (vi - co).length
        if di < d:
            d = di
            uv = ul.data[loopi.index].uv
    return uv