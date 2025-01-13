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
    if type(mesh) is bpy.types.Object:
        mesh = mesh.data
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
    if type(mesh) is bpy.types.Object:
        mesh = mesh.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    return bm


def get_world_from_uv(obj, t_mesh, mat_slot, uv_target, threshold):
    world = mesh_world_point_from_uv(obj, t_mesh, mat_slot, uv_target)
    if world is None: # if the point is outside the UV island(s), just find the nearest vertex.
        world = nearest_vert_from_uv(obj, t_mesh, mat_slot, uv_target, threshold, world=True)
    if world is None:
        utils.log_error("Unable to locate uv target: " + str(uv_target))
    return world


def get_local_from_uv(obj, t_mesh, mat_slot, uv_target, threshold):
    local = mesh_local_point_from_uv(t_mesh, mat_slot, uv_target)
    if local is None: # if the point is outside the UV island(s), just find the nearest vertex.
        local = nearest_vert_from_uv(obj, t_mesh, mat_slot, uv_target, threshold, world=False)
    if local is None:
        utils.log_error("Unable to locate uv target: " + str(uv_target))
    return local


def get_uv_from_world(obj, t_mesh, mat_slot, world_co, project=False):
    uv = mesh_uv_from_world_point(obj, t_mesh, mat_slot, world_co, project=project)
    if uv is None:
        utils.log_error("Unable to local point inside UV islands.")
        uv = mathutils.Vector((0,0,0))
    return uv


def get_uv_from_local(obj, t_mesh, mat_slot, local_co, project=False):
    uv = mesh_uv_from_local_point(obj, t_mesh, mat_slot, local_co, project=project)
    if uv is None:
        utils.log_error("Unable to local point inside UV islands.")
        uv = mathutils.Vector((0,0,0))
    return uv


def find_coord(obj, ul, uv, face):
    u, v, w = [l[ul].uv.to_3d() for l in face.loops]
    x, y, z = [v.co for v in face.verts]
    co = mathutils.geometry.barycentric_transform(uv, u, v, w, x, y, z)
    return obj.matrix_world * co


def mesh_local_point_from_uv(b_mesh, mat_slot, uv):
    ul = b_mesh.loops.layers.uv[0]
    for face in b_mesh.faces:
        if mat_slot == -1 or face.material_index == mat_slot:
            u, v, w = [l[ul].uv.to_3d() for l in face.loops]
            if mathutils.geometry.intersect_point_tri_2d(uv, u, v, w):
                x, y, z = [vert.co for vert in face.verts]
                co = mathutils.geometry.barycentric_transform(uv, u, v, w, x, y, z)
                return co
    return None


def mesh_world_point_from_uv(obj, b_mesh, mat_slot, uv):
    ul = b_mesh.loops.layers.uv[0]
    for face in b_mesh.faces:
        if mat_slot == -1 or face.material_index == mat_slot:
            u, v, w = [l[ul].uv.to_3d() for l in face.loops]
            if mathutils.geometry.intersect_point_tri_2d(uv, u, v, w):
                x, y, z = [vert.co for vert in face.verts]
                co = mathutils.geometry.barycentric_transform(uv, u, v, w, x, y, z)
                return obj.matrix_world @ co
    return None


def mesh_uv_from_world_point(obj, b_mesh, mat_slot, co, project=False):
    local_co = obj.matrix_world.inverted() @ co
    return mesh_uv_from_local_point(obj, b_mesh, mat_slot, local_co, project=project)


def mesh_uv_from_local_point(obj, b_mesh, mat_slot, co, project=False):
    if project:
        co = obj.closest_point_on_mesh(co)[1]
    ul = b_mesh.loops.layers.uv[0]
    best_uv = None
    best_z = 1
    face : bmesh.types.BMFace
    for face in b_mesh.faces:
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


def nearest_vert_from_uv(obj, mesh, mat_slot, uv, thresh=0, world=True):
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
                if dsq < near_dist:
                    near = face.verts[i]
                    near_dist = dsq
    if near:
        if world:
            return obj.matrix_world @ near.co
        else:
            return near.co
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


def copy_vert_positions_by_uv_id(src_obj, dst_obj, accuracy=5, vertex_group=None,
                                 threshold=0.004, shape_key_name=None, flatten_udim=False):

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
                uv = loop[ul].uv.copy()
                # why flatten the udims?
                # because the in the sculpting tools, the separate sculpting meshes
                # must flatten the udims to bake the textures correctly
                if flatten_udim:
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
            uv = loop[ul].uv.copy()
            if flatten_udim:
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
        if slot.material and slot.material == mat:
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


def intersects_projected_face(p: Vector, PMW, f: bmesh.types.BMFace, FMW):
    PW = p @ PMW
    cw = f.calc_center_median() @ FMW
    pcw = PW - cw
    fnw = (f.normal @ FMW).normalized()
    if pcw.dot(fnw) < 0:
        return None
    d = pcw.length
    #d = mathutils.geometry.distance_point_to_plane(PW, cw, fnw)
    #if d < 0: return None
    dfn: Vector = fnw / d
    vw0 = f.verts[0].co @ FMW
    vw1 = f.verts[1].co @ FMW
    vw2 = f.verts[2].co @ FMW
    nw0 = (f.verts[0].normal @ FMW).normalized()
    nw1 = (f.verts[1].normal @ FMW).normalized()
    nw2 = (f.verts[2].normal @ FMW).normalized()
    dnw0 = dfn.dot(nw0)
    dnw1 = dfn.dot(nw1)
    dnw2 = dfn.dot(nw2)
    VW0 = vw0 + nw0 / dnw0
    VW1 = vw1 + nw1 / dnw1
    VW2 = vw2 + nw2 / dnw2

    u, v, w = barycentric_coords(PW, VW0, VW1, VW2)
    if u < 0 or u > 1 or v < 0 or v > 1 or w < 0 or w > 1:
        return None

    #diag_mesh_add_edge(cw, cw + fnw * 0.01)
    diag_mesh_add_tri(vw0, vw1, vw2)
    #diag_mesh_add_edge(f0, f0 + fnw0 * 0.01)
    #diag_mesh_add_edge(f1, f1 + fnw1 * 0.01)
    #diag_mesh_add_edge(f2, f2 + fnw2 * 0.01)

    diag_mesh_add_tri(VW0, VW1, VW2)
    diag_mesh_add_edge(vw0, VW0)
    diag_mesh_add_edge(vw1, VW1)
    diag_mesh_add_edge(vw2, VW2)

    diag_mesh_add_edge(cw, PW)

    return u, v, w, d, pcw.length



def barycentric_coords(p: Vector, a: Vector, b: Vector, c: Vector):
    v0 = b - a
    v1 = c - a
    v2 = p - a
    d00 = v0.dot(v0)
    d01 = v0.dot(v1)
    d11 = v1.dot(v1)
    d20 = v2.dot(v0)
    d21 = v2.dot(v1)
    denom = d00 * d11 - d01 * d01
    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    u = 1 - v - w
    return (u, v, w)


def barycentric_weight(b_co, w0, w1, w2):
    bc_u, bc_v, bc_w = b_co
    return bc_u * w0 + bc_v * w1 + bc_w * w2


def map_body_weight_blends(body, obj, bm_obj: bmesh.types.BMesh):
    weight_blends = {}
    v: bmesh.types.BMVert
    f: bmesh.types.BMFace
    BMW = body.matrix_world
    BMWI = BMW.inverted()
    OMW = obj.matrix_world
    # object local to body local matrix
    OLTBL = BMWI @ OMW
    for v in bm_obj.verts:
        #diag_mesh_create()
        #diag_to_bmesh()
        obj_world_co = OMW @ v.co
        body_local_co = OLTBL @ v.co
        success, closest_local_co, closest_local_no, closest_face_index = body.closest_point_on_mesh(body_local_co)
        if success:
            closest_world_co = BMW @ closest_local_co
            delta = obj_world_co - closest_world_co
            no = (BMW @ closest_local_no).normalized()
            if delta.dot(no) < 0:
                weight_blends[v.index] = 0
            else:
                weight_blends[v.index] = delta.length
            #diag_mesh_add_edge(closest_world_co, obj_world_co)
        else:
            #diag_mesh_add_vert(body_local_co)
            weight_blends[v.index] = -1
        #diag_from_bmesh()
    return weight_blends


def fetch_vertex_layer_weights(bm: bmesh.types.BMesh, layer_index):
    bm.verts.layers.deform.verify()
    dl = bm.verts.layers.deform.active
    weights = {}
    for vert in bm.verts:
        try:
            weights[vert.index] = vert[dl][layer_index]
        except:
            weights[vert.index] = 0.0
    return weights


DIAG_NAME = "DiagnosticMesh"
DIAG = None
DIAG_BM = None

def diag_mesh_create():
    global DIAG, DIAG_NAME
    if DIAG_NAME in bpy.data.objects:
        DIAG = bpy.data.objects[DIAG_NAME]
    else:
        mesh = bpy.data.meshes.new(DIAG_NAME)
        DIAG = bpy.data.objects.new(DIAG_NAME, mesh)
        DIAG.location = [0,0,0]
        bpy.context.collection.objects.link(DIAG)
        DIAG.name = DIAG_NAME
    return DIAG


def diag_to_bmesh() -> bmesh.types.BMesh:
    global DIAG_BM
    if DIAG_BM:
        return DIAG_BM
    else:
        diag = diag_mesh_create()
        DIAG_BM = get_bmesh(diag.data)
        return DIAG_BM


def diag_finish():
    global DIAG, DIAG_BM
    if DIAG and DIAG_BM:
        DIAG_BM.to_mesh(DIAG.data)


def diag_mesh_add_vert(p0: Vector):
    bm = diag_to_bmesh()
    bm.verts.new(p0)


def diag_mesh_add_edge(p0: Vector, p1: Vector):
    bm = diag_to_bmesh()
    v0 = bm.verts.new(p0)
    v1 = bm.verts.new(p1)
    bm.edges.new((v0, v1))


def diag_mesh_add_tri(p0: Vector, p1: Vector, p2: Vector):
    bm = diag_to_bmesh()
    v0 = bm.verts.new(p0)
    v1 = bm.verts.new(p1)
    v2 = bm.verts.new(p2)
    bm.faces.new((v0, v1, v2))

