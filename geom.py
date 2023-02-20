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
import bmesh
from . import utils

# Code derived from: https://blenderartists.org/t/get-3d-location-of-mesh-surface-point-from-uv-parameter/649486/2

def get_triangulated_bmesh(source_mesh):
    """Be in object mode...
    """
    bm = bmesh.new()
    bm.from_mesh(source_mesh)
    # viewport seems to use fixed / clipping instead of beauty
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
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


def copy_vert_positions_by_uv_id(src_obj, dst_obj, accuracy = 5, vertex_group = None, mid_level = 0, threshold = 0.004):

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

    for i, src_mat in enumerate(src_mesh.materials):
        for j, dst_mat in enumerate(dst_mesh.materials):
            if src_mat == dst_mat:
                mat_map[i] = j

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
                    if abs(weight - mid_level) < threshold:
                        continue
                uv = loop[ul].uv
                uv.x -= int(uv.x)
                uv_id = uv.to_tuple(accuracy), dst_material_idx
                src_map[uv_id] = loop.vert.index

    ul = dst_bm.loops.layers.uv[0]
    for face in dst_bm.faces:
        for loop in face.loops:
            uv = loop[ul].uv
            uv.x -= int(uv.x)
            uv_id = uv.to_tuple(accuracy), face.material_index
            if uv_id in src_map:
                src_vert = src_map[uv_id]
                src_pos = src_bm.verts[src_vert].co
                loop.vert.co = src_pos

    dst_bm.to_mesh(dst_mesh)
