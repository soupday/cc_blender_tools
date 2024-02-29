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

import bpy
import math
import mathutils
from mathutils import Vector
import bmesh
from . import utils

# Code derived from: https://blenderartists.org/t/get-3d-location-of-mesh-surface-point-from-uv-parameter/649486/2

def get_triangulated_bmesh(mesh):
    """Be in object mode"""
    bm = bmesh.new()
    bm.from_mesh(mesh)
    # viewport seems to use fixed / clipping instead of beauty
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    return bm


def get_bmesh(mesh):
    """Be in object mode"""
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    return bm


def get_world_from_uv(obj, t_mesh, mat_slot, uv_target, threshold):
    world = mesh_world_point_from_uv(obj, t_mesh, mat_slot, uv_target)
    if world is None: # if the point is outside the UV island(s), just find the nearest vertex.
        world = nearest_vert_from_uv(obj, t_mesh, mat_slot, uv_target, threshold)
    if world is None:
        utils.log_error("Unable to locate uv target: " + str(uv_target))
    return world


def get_uv_from_world(obj, t_mesh, mat_slot, world_co):
    uv = mesh_uv_from_world_point(obj, t_mesh, mat_slot, world_co)
    if uv is None:
        utils.log_error("Unable to local point inside UV islands.")
        uv = mathutils.Vector((0,0,0))
    return uv


def find_coord(obj, ul, uv, face):
    u, v, w = [l[ul].uv.to_3d() for l in face.loops]
    x, y, z = [v.co for v in face.verts]
    co = mathutils.geometry.barycentric_transform(uv, u, v, w, x, y, z)
    return obj.matrix_world * co


def mesh_world_point_from_uv(obj, mesh, mat_slot, uv):
    ul = mesh.loops.layers.uv[0]
    for face in mesh.faces:
        if face.material_index == mat_slot:
            u, v, w = [l[ul].uv.to_3d() for l in face.loops]
            if mathutils.geometry.intersect_point_tri_2d(uv, u, v, w):
                x, y, z = [vert.co for vert in face.verts]
                co = mathutils.geometry.barycentric_transform(uv, u, v, w, x, y, z)
                return obj.matrix_world @ co
    return None


def mesh_uv_from_world_point(obj, mesh, mat_slot, co):
    local_co = obj.matrix_world.inverted() @ co
    return mesh_uv_from_local_point(obj, mesh, mat_slot, local_co)


def mesh_uv_from_local_point(obj, mesh, mat_slot, co):
    co = obj.closest_point_on_mesh(co)[1]
    ul = mesh.loops.layers.uv[0]
    best_uv = None
    best_z = 1
    face : bmesh.types.BMFace
    for face in mesh.faces:
        if face.material_index == mat_slot:
            x, y, z = [vert.co for vert in face.verts]
            u, v, w = [l[ul].uv.to_3d() for l in face.loops]
            uv = mathutils.geometry.barycentric_transform(co, x, y, z, u, v, w)
            if mathutils.geometry.intersect_point_tri_2d(uv, u, v, w):
                d = abs(mathutils.geometry.distance_point_to_plane(co, x, face.normal))
                if mathutils.geometry.intersect_point_tri(co, x, y, z) and d < 0.01:
                    return uv
                if abs(uv.z) < best_z:
                    best_uv = uv
                    best_z = abs(uv.z)
    return best_uv


def nearest_vert_from_uv(obj, mesh, mat_slot, uv, thresh = 0):
    thresh = 2 * thresh * thresh
    ul = mesh.loops.layers.uv[0]
    near = None
    near_dist = math.inf
    for face in mesh.faces:
        if face.material_index == mat_slot:
            for i in range(0, len(face.loops)):
                l = face.loops[i]
                luv = l[ul].uv
                du = luv[0] - uv[0]
                dv = luv[1] - uv[1]
                dsq = du * du + dv * dv
                if dsq < thresh:
                    return obj.matrix_world @ face.verts[i].co
                if near_dist < dsq:
                    near = face.verts[i]
                    near_dist = dsq
    if near:
        return obj.matrix_world @ near.co
    else:
        return None


def copy_vertex_positions_and_weights(src_obj : bpy.types.Object, dst_obj : bpy.types.Object):
    vg_indices = {}
    dst_obj.vertex_groups.clear()
    src_vg : bpy.types.VertexGroup
    for src_vg in src_obj.vertex_groups:
        dst_vg = dst_obj.vertex_groups.new(name=src_vg.name)
        vg_indices[src_vg.index] = dst_vg.index

    src_mesh : bpy.types.Mesh = src_obj.data
    dst_mesh : bpy.types.Mesh  = dst_obj.data

    src_bm = bmesh.new()
    dst_bm = bmesh.new()

    src_bm.from_mesh(src_mesh)
    src_bm.faces.ensure_lookup_table()
    src_bm.verts.ensure_lookup_table()

    dst_bm.from_mesh(dst_mesh)
    dst_bm.faces.ensure_lookup_table()
    dst_bm.verts.ensure_lookup_table()

    matching_vert_count = len(src_bm.verts) == len(dst_bm.verts)

    if matching_vert_count:

        src_bm.verts.layers.deform.verify()
        dst_bm.verts.layers.deform.verify()
        src_dl = src_bm.verts.layers.deform.active
        dst_dl = dst_bm.verts.layers.deform.active

        for src_vert in src_bm.verts:
            i = src_vert.index
            dst_vert : bmesh.types.BMVert = dst_bm.verts[i]
            for src_vg_index in vg_indices:
                dst_vg_index = vg_indices[src_vg_index]
                if src_vg_index in src_vert[src_dl]:
                    dst_vert.co = src_vert.co
                    dst_vert[dst_dl][dst_vg_index] = src_vert[src_dl][src_vg_index]

    dst_bm.to_mesh(dst_mesh)



def copy_vert_positions_by_uv_id(src_obj, dst_obj, accuracy = 5, vertex_group = None, threshold = 0.004, shape_key_name = None):

    mesh : bpy.types.Mesh = dst_obj.data
    if shape_key_name:
        if not mesh.shape_keys:
            dst_obj.shape_key_add(name = "Basis")
        if shape_key_name not in mesh.shape_keys.key_blocks:
            shape_key = dst_obj.shape_key_add(name = shape_key_name)
            shape_key_name = shape_key.name

    src_mesh = src_obj.data
    dst_mesh = dst_obj.data

    src_bm = bmesh.new()
    dst_bm = bmesh.new()

    src_bm.from_mesh(src_mesh)
    src_bm.faces.ensure_lookup_table()
    src_bm.verts.ensure_lookup_table()

    dst_bm.from_mesh(dst_mesh)
    dst_bm.faces.ensure_lookup_table()
    dst_bm.verts.ensure_lookup_table()

    src_map = {}
    mat_map = {}
    overlapping = {}

    matching_vert_count = len(src_bm.verts) == len(dst_bm.verts)

    for i, src_mat in enumerate(src_mesh.materials):
        for j, dst_mat in enumerate(dst_mesh.materials):
            if src_mat == dst_mat:
                mat_map[i] = j
            elif utils.strip_name(src_mat.name) == utils.strip_name(dst_mat.name):
                mat_map[i] = j

    if len(src_mesh.materials) == 0:
        mat_map[0] = 0

    vg_index = -1
    if vertex_group and vertex_group in src_obj.vertex_groups:
        vg_index = src_obj.vertex_groups[vertex_group].index

    ul = src_bm.loops.layers.uv[0]
    src_bm.verts.layers.deform.verify()
    dl = src_bm.verts.layers.deform.active
    face : bmesh.types.BMFace
    loop : bmesh.types.BMLoop

    for face in src_bm.faces:
        if face.material_index in mat_map:
            dst_material_idx = mat_map[face.material_index]
            for loop in face.loops:
                if vg_index >= 0:
                    vert = src_bm.verts[loop.vert.index]
                    weight = vert[dl][vg_index]
                    if weight < threshold:
                        continue
                uv = loop[ul].uv
                uv.x -= int(uv.x)
                uv_id = uv.to_tuple(accuracy), dst_material_idx
                if uv_id in src_map and src_map[uv_id] != loop.vert.index:
                    overlapping[uv_id] = True
                src_map[uv_id] = loop.vert.index

    ul = dst_bm.loops.layers.uv[0]
    sl = None
    if shape_key_name:
        sl = dst_bm.verts.layers.shape.get(shape_key_name)
    for face in dst_bm.faces:
        for loop in face.loops:
            uv = loop[ul].uv
            uv.x -= int(uv.x)
            uv_id = uv.to_tuple(accuracy), face.material_index
            # overlapping UV's can't be detected correctly so try to copy from just the index position
            if matching_vert_count and uv_id in overlapping:
                vert_index = loop.vert.index
                src_pos = src_bm.verts[vert_index].co
                if sl:
                    loop.vert[sl] = src_pos
                else:
                    loop.vert.co = src_pos
            elif uv_id in src_map:
                src_vert = src_map[uv_id]
                src_pos = src_bm.verts[src_vert].co
                if sl:
                    loop.vert[sl] = src_pos
                else:
                    loop.vert.co = src_pos

    dst_bm.to_mesh(dst_mesh)


def copy_vert_positions_by_index(src_obj, dst_obj, vertex_group = None, threshold = 0.004, shape_key_name = None):

    mesh : bpy.types.Mesh = dst_obj.data
    if shape_key_name:
        if not mesh.shape_keys:
            dst_obj.shape_key_add(name = "Basis")
        if shape_key_name not in mesh.shape_keys.key_blocks:
            shape_key = dst_obj.shape_key_add(name = shape_key_name)
            shape_key_name = shape_key.name

    src_mesh = src_obj.data
    dst_mesh = dst_obj.data

    src_bm = bmesh.new()
    dst_bm = bmesh.new()

    src_bm.from_mesh(src_mesh)
    src_bm.faces.ensure_lookup_table()
    src_bm.verts.ensure_lookup_table()

    dst_bm.from_mesh(dst_mesh)
    dst_bm.faces.ensure_lookup_table()
    dst_bm.verts.ensure_lookup_table()

    src_verts = []

    matching_vert_count = len(src_bm.verts) == len(dst_bm.verts)
    if not matching_vert_count:
        return

    vg_index = -1
    if vertex_group and vertex_group in src_obj.vertex_groups:
        vg_index = src_obj.vertex_groups[vertex_group].index

    src_bm.verts.layers.deform.verify()
    dl = src_bm.verts.layers.deform.active
    loop : bmesh.types.BMLoop

    for vert in src_bm.verts:
        if vg_index >= 0:
            weight = vert[dl][vg_index]
            if weight < threshold:
                continue
        src_verts.append(vert.index)

    sl = None
    if shape_key_name:
        sl = dst_bm.verts.layers.shape.get(shape_key_name)
    for vert in dst_bm.verts:
        if vert.index in src_verts:
            src_pos = src_bm.verts[vert.index].co
            if sl:
                vert[sl] = src_pos
            else:
                vert.co = src_pos

    dst_bm.to_mesh(dst_mesh)


def map_image_to_vertex_weights(obj, mat, image, vertex_group, func):
    width = image.size[0]
    height = image.size[1]
    wmo = width - 1
    hmo = height - 1
    uhw = 1 / (wmo * 2)
    vhw = 1 / (hmo * 2)
    pixels = image.pixels[:]
    if vertex_group in obj.vertex_groups:
        vg = obj.vertex_groups[vertex_group]
    else:
        vg = obj.vertex_groups.new(name=vertex_group)
    vg_index = vg.index

    mat_index = -1
    for i, slot in enumerate(obj.material_slots):
        if slot.material == mat:
            mat_index = i
            break

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    ul = bm.loops.layers.uv[0]
    bm.verts.layers.deform.verify()
    dl = bm.verts.layers.deform.active
    for face in bm.faces:
        if face.material_index == mat_index:
            for loop in face.loops:
                uv = loop[ul].uv
                uv.x -= int(uv.x)
                uv.y -= int(uv.y)
                vert = bm.verts[loop.vert.index]
                x = int((uv.x + uhw) * wmo)
                y = int((uv.y + vhw) * hmo)
                pixel_value = pixels[x * 4 + y * width * 4]
                weight = func(pixel_value)
                vert[dl][vg_index] = weight

    bm.to_mesh(mesh)


def remove_vertex_groups_from_selected(obj, vertex_groups):
    # get the bmesh
    mesh = obj.data
    bm = get_bmesh(mesh)
    bm.verts.layers.deform.verify()
    dl = bm.verts.layers.deform.active

    # get the vertex group indices
    vg_indices = []
    vg_map = {}
    for i, vg in enumerate(obj.vertex_groups):
        if vg.name in vertex_groups:
            vg_indices.append(i)
            vg_map[i] = { "name": vg.name, "sum": 0 }

    # set the weights for the vertex groups in each selected vertex to zero
    for vert in bm.verts:
        for vg_index in vg_indices:
            if vg_index in vert[dl]:
                if vert.select:
                    vert[dl][vg_index] = 0.0
                else:
                    weight = vert[dl][vg_index]
                    vg_map[vg_index]["sum"] += weight

    # apply the changes
    bm.to_mesh(mesh)

    # remove empty groups
    for vg_index in vg_map:
        if vg_map[vg_index]["sum"] < 0.0001:
            vg_name = vg_map[vg_index]["name"]
            vg = obj.vertex_groups[vg_name]
            utils.log_info(f"Removing empty vertex group: {vg_name} from: {obj.name}")
            obj.vertex_groups.remove(vg)


def parse_island_recursive(bm, face_index, faces_left, island, face_map, vert_map):
    """Recursive way to parse the UV islands.
       Can run out of recursion calls on large meshes.
    """
    if face_index in faces_left:
        faces_left.remove(face_index)
        island.append(face_index)
        for uv_id in face_map[face_index]:
            connected_faces = vert_map[uv_id]
            if connected_faces:
                for cf in connected_faces:
                    parse_island_recursive(bm, cf, faces_left, island, face_map, vert_map)


def parse_island_non_recursive(bm, face_indices, faces_left, island, face_map, vert_map):
    """Non recursive way to parse UV islands.
       Connected faces expand the island each iteration.
       A Set of all currently considered faces is maintained each iteration.
       More memory intensive, but doesn't fail.
    """
    levels = 0
    while face_indices:
        levels += 1
        next_indices = set()
        for face_index in face_indices:
            faces_left.remove(face_index)
            island.append(face_index)
        for face_index in face_indices:
            for uv_id in face_map[face_index]:
                connected_faces = vert_map[uv_id]
                if connected_faces:
                    for cf_index in connected_faces:
                        if cf_index not in island:
                            next_indices.add(cf_index)
        face_indices = next_indices


def get_uv_island_map(bm, uv_layer, island):
    """Fetch the UV coords of each vertex in the UV/Mesh island.
       Each island has a unique UV map so this must be called per island.
       uv_map = { vert_index: loop.uv, ... }
    """
    uv_map = {}
    ul = bm.loops.layers.uv[uv_layer]
    for face_index in island:
        face = bm.faces[face_index]
        for loop in face.loops:
            uv_map[loop.vert.index] = loop[ul].uv
    return uv_map


def get_uv_islands(bm, uv_layer, use_selected = True):
    """Return a list of faces in each distinct uv island."""
    face_map = {}
    vert_map = {}
    uv_map = {}
    ul = bm.loops.layers.uv[uv_layer]

    if use_selected:
        faces = [f for f in bm.faces if f.select and not f.hide]
    else:
        faces = [f for f in bm.faces if not f.hide]

    for face in faces:
        for loop in face.loops:
            uv_id = loop[ul].uv.to_tuple(5), loop.vert.index
            uv_map[loop.vert.index] = loop[ul].uv
            if face.index not in face_map:
                face_map[face.index] = set()
            if uv_id not in vert_map:
                vert_map[uv_id] = set()
            face_map[face.index].add(uv_id)
            vert_map[uv_id].add(face.index)

    islands = []
    faces_left = set(face_map.keys())

    while len(faces_left) > 0:
        current_island = []
        face_index = list(faces_left)[0]
        face_indices = set()
        face_indices.add(face_index)
        parse_island_non_recursive(bm, face_indices, faces_left, current_island, face_map, vert_map)
        islands.append(current_island)

    return islands


def get_uv_aligned_edges(bm, island, card_dir, uv_map, get_non_aligned = False, dir_threshold = 0.9):
    edge : bmesh.types.BMEdge
    face : bmesh.types.BMFace
    edges = set()

    for i in island:
        face = bm.faces[i]
        for edge in face.edges:
            edges.add(edge.index)

    aligned = set()

    for e in edges:
        edge = bm.edges[e]
        uv0 = uv_map[edge.verts[0].index]
        uv1 = uv_map[edge.verts[1].index]
        V = Vector(uv1) - Vector(uv0)
        V.normalize()
        dot = card_dir.dot(V)

        if get_non_aligned:
            if abs(dot) < dir_threshold:
                aligned.add(e)
        else:
            if abs(dot) >= dir_threshold:
                aligned.add(e)

    return aligned


def get_linked_edge_map(bm, edges):
    edge_map = {}
    for e in edges:
        edge = bm.edges[e]
        for vert in edge.verts:
            for linked_edge in vert.link_edges:
                if linked_edge != edge and linked_edge.index in edges:
                    if e not in edge_map:
                        edge_map[e] = set()
                    edge_map[e].add(linked_edge.index)
    return edge_map


def get_boundary_edges(bm, island):
    face : bmesh.types.BMFace
    edge : bmesh.types.BMEdge
    edges = set()
    for face_index in island:
        face = bm.faces[face_index]
        for edge in face.edges:
            if edge.is_boundary:
                edges.add(edge.index)
    return edges


def count_adjacent_faces(face : bmesh.types.BMFace):
    edge : bmesh.types.BMEdge
    count = 0
    for edge in face.edges:
        for f in edge.link_faces:
            if f != face:
                count += 1
    return count


def get_uv_bounds(uv_map):
    min = Vector((9999,9999))
    max = Vector((-9999,-9999))
    for vert_index in uv_map:
        uv = uv_map[vert_index]
        if uv.x < min.x: min.x = uv.x
        if uv.x > max.x: max.x = uv.x
        if uv.y < min.y: min.y = uv.y
        if uv.y > max.y: max.y = uv.y
    return min, max



def is_island_grid(bm : bmesh.types.BMesh, island : list):
    """island: list of face indices"""
    adjacent_count = {}
    for face_index in island:
        face = bm.faces[face_index]
        count = count_adjacent_faces(face)
        if count not in adjacent_count:
            adjacent_count[count] = 0
        adjacent_count[count] += 1

    num_faces = len(island)

    # test for a 1 x N strip
    if len(adjacent_count) == 2 and 1 in adjacent_count and 2 in adjacent_count:
        if adjacent_count[1] == 2 and adjacent_count[2] == num_faces - 2:
            return True

    # test for a 2 x N grid
    elif len(adjacent_count) == 2 and 2 in adjacent_count and 3 in adjacent_count:
        if adjacent_count[2] == 4 and adjacent_count[3] == num_faces - 4:
            return True

    # test for a N x M grid
    elif len(adjacent_count) == 3 and 2 in adjacent_count and 3 in adjacent_count and 4 in adjacent_count:
        if adjacent_count[2] == 4 and adjacent_count[3] + adjacent_count [4] == num_faces - 4:
            return True

    return False


def get_average_edge_length(obj):
    avg = 0.0
    if utils.object_exists_is_mesh(obj):
        bm = get_bmesh(obj.data)
        edge : bmesh.types.BMEdge
        l = 0.0
        n = 0
        for edge in bm.edges:
            l += edge.calc_length()
            n += 1
        if n > 0:
            avg = l / n
        bm.free()
        avg *= obj.matrix_world.median_scale
    return avg


def get_area(obj):
    area = 0.0
    if utils.object_exists_is_mesh(obj):
        bm = get_bmesh(obj.data)
        face : bmesh.types.BMFace
        for face in bm.faces:
            area += face.calc_area()
        bm.free()
        area *= pow(obj.matrix_world.median_scale, 2)
    return area
