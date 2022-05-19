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