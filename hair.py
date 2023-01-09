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

import bpy, bmesh
import os, math, random
from mathutils import Vector
from . import utils, jsonutils, bones, meshutils


HAIR_BONE_PREFIX = "RL_Hair"
HEAD_BONE_NAME = "CC_Base_Head"


def begin_hair_sculpt(chr_cache):
    return


def end_hair_sculpt(chr_cache):
    return


def find_obj_cache(chr_cache, obj):
    if chr_cache and obj and obj.type == "MESH":
        # try to find directly
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache:
            return obj_cache
        # obj might be part of a split or a copy from original character object
        # so will have the same name but with duplication suffixes
        possible = []
        source_name = utils.strip_name(obj.name)
        for obj_cache in chr_cache.object_cache:
            if obj_cache.source_name == source_name:
                possible.append(obj_cache)
        # if only one possibility return that
        if possible and len(possible) == 1:
            return possible[0]
        # try to find the correct object cache by matching the materials
        if obj_cache.object.type == "MESH":
            # try matching all the materials first
            for obj_cache in possible:
                found = True
                for mat in obj.data.materials:
                    if mat not in obj_cache.object.data.materials:
                        found = False
                if found:
                    return obj_cache
            # then try just matching any
            for obj_cache in possible:
                found = True
                for mat in obj.data.materials:
                    if mat in obj_cache.object.data.materials:
                        return obj_cache
    return None


def clear_particle_systems(obj):
    if utils.set_mode("OBJECT") and utils.set_only_active_object(obj):
        for i in range(0, len(obj.particle_systems)):
            bpy.ops.object.particle_system_remove()
        return True
    return False


def convert_hair_group_to_particle_systems(obj, curves):
    if clear_particle_systems(obj):
        for c in curves:
            if utils.set_only_active_object(c):
                bpy.ops.curves.convert_to_particle_system()


def export_blender_hair(op, chr_cache, objects, base_path):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    utils.expand_with_child_objects(objects)

    folder, name = os.path.split(base_path)
    file, ext = os.path.splitext(name)

    parents = []
    for obj in objects:
        if obj.type == "CURVES":
            if obj.parent:
                if obj.parent not in parents:
                    parents.append(obj.parent)
            else:
                op.report({'ERROR'}, f"Curve: {obj.data.name} has no parent!")

    json_data = { "Hair": { "Objects": { } } }
    export_id = 0

    for parent in parents:

        groups = {}

        obj_cache = find_obj_cache(chr_cache, parent)

        if obj_cache:

            parent_name = utils.determine_object_export_name(chr_cache, parent, obj_cache)

            json_data["Hair"]["Objects"][parent_name] = { "Groups": {} }

            if prefs.hair_export_group_by == "CURVE":
                for obj in objects:
                    if obj.type == "CURVES" and obj.parent == parent:
                        group = [obj]
                        name = obj.data.name
                        groups[name] = group
                        utils.log_info(f"Group: {name}, Object: {obj.data.name}")

            elif prefs.hair_export_group_by == "NAME":
                for obj in objects:
                    if obj.type == "CURVES" and obj.parent == parent:
                        name = utils.strip_name(obj.data.name)
                        if name not in groups.keys():
                            groups[name] = []
                        groups[name].append(obj)
                        utils.log_info(f"Group: {name}, Object: {obj.data.name}")

            else: #prefs.hair_export_group_by == "NONE":
                if "Hair" not in groups.keys():
                    groups["Hair"] = []
                for obj in objects:
                    if obj.type == "CURVES" and obj.parent == parent:
                        groups["Hair"].append(obj)
                        utils.log_info(f"Group: Hair, Object: {obj.data.name}")

            for group_name in groups.keys():
                file_name = f"{file}_{export_id}.abc"
                file_path = os.path.join(folder, file_name)
                export_id += 1
                for o in groups[group_name]:
                    print(group_name, o.name)

                convert_hair_group_to_particle_systems(parent, groups[group_name])

                utils.try_select_objects(groups[group_name], True)
                utils.set_active_object(parent)

                json_data["Hair"]["Objects"][parent_name]["Groups"][group_name] = { "File": file_name }

                bpy.ops.wm.alembic_export(
                        filepath=file_path,
                        check_existing=False,
                        global_scale=100.0,
                        start=1, end=1,
                        use_instancing = False,
                        selected=True,
                        visible_objects_only=True,
                        evaluation_mode = "RENDER",
                        packuv=False,
                        export_hair=True,
                        export_particles=True)

                clear_particle_systems(parent)

        else:
            op.report({'ERROR'}, f"Unable to find source mesh object in character for: {parent.name}!")

    new_json_path = os.path.join(folder, file + ".json")
    jsonutils.write_json(json_data, new_json_path)

    utils.try_select_objects(objects, True)


def create_curve():
    curve = bpy.data.curves.new("Hair Curve", type="CURVE")
    curve.dimensions = "3D"
    obj = bpy.data.objects.new("Hair Curve", curve)
    bpy.context.collection.objects.link(obj)
    return curve


def create_hair_curves():
    curves = bpy.data.hair_curves.new("Hair Curves")
    obj = bpy.data.objects.new("Hair Curves", curves)
    bpy.context.collection.objects.link(obj)
    return curves


def add_poly_spline(points, curve):
    """Create a poly curve from a list of Vectors
    """
    spline : bpy.types.Spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for i in range(0, len(points)):
        co = points[i]
        spline.points[i].co = (co.x, co.y, co.z, 1.0)


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


def get_island_uv_map(bm, ul, island):
    """Fetch the UV coords of each vertex in the UV/Mesh island.
       Each island has a unique UV map so this must be called per island.
    """
    uv_map = {}
    for face_index in island:
        face = bm.faces[face_index]
        for loop in face.loops:
            uv_map[loop.vert.index] = loop[ul].uv
    return uv_map


def get_hair_card_islands(bm, ul, use_selected = True):
    face_map = {}
    vert_map = {}
    uv_map = {}

    if use_selected:
        faces = [f for f in bm.faces if f.select]
    else:
        faces = [f for f in bm.faces]

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


def get_aligned_edges(bm, island, dir, uv_map, get_non_aligned = False):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    edge : bmesh.types.BMEdge
    face : bmesh.types.BMFace

    edges = set()

    for i in island:
        face = bm.faces[i]
        for edge in face.edges:
            edges.add(edge.index)

    aligned = set()

    DIR_THRESHOLD = prefs.hair_curve_dir_threshold

    for e in edges:
        edge = bm.edges[e]
        uv0 = uv_map[edge.verts[0].index]
        uv1 = uv_map[edge.verts[1].index]
        V = Vector(uv1) - Vector(uv0)
        V.normalize()
        dot = dir.dot(V)

        if get_non_aligned:
            if abs(dot) < DIR_THRESHOLD:
                aligned.add(e)
        else:
            if abs(dot) >= DIR_THRESHOLD:
                aligned.add(e)

    return aligned


def get_aligned_edge_map(bm, edges):
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


def parse_loop(bm, edge_index, edges_left, loop, edge_map):
    """Returns a set of vertex indices in the edge loop
    """
    if edge_index in edges_left:
        edges_left.remove(edge_index)
        edge = bm.edges[edge_index]
        loop.add(edge.verts[0].index)
        loop.add(edge.verts[1].index)
        if edge.index in edge_map:
            for ce in edge_map[edge.index]:
                parse_loop(bm, ce, edges_left, loop, edge_map)


def sort_func_u(vert_uv_pair):
    return vert_uv_pair[-1].x


def sort_func_v(vert_uv_pair):
    return vert_uv_pair[-1].y


def sort_verts_by_uv(obj, bm, loop, uv_map, dir):
    sorted = []
    for vert in loop:
        uv = uv_map[vert]
        sorted.append([vert, uv])
    if dir.x > 0:
        sorted.sort(reverse=False, key=sort_func_u)
    elif dir.x < 0:
        sorted.sort(reverse=True, key=sort_func_u)
    elif dir.y > 0:
        sorted.sort(reverse=False, key=sort_func_v)
    else:
        sorted.sort(reverse=True, key=sort_func_v)
    return [ obj.matrix_world @ bm.verts[v].co for v, uv in sorted]


def get_ordered_coordinate_loops(obj, bm, edges, dir, uv_map, edge_map):
    edges_left = set(edges)
    loops = []

    # separate edges into vertex loops
    while len(edges_left) > 0:
        loop = set()
        edge_index = list(edges_left)[0]
        parse_loop(bm, edge_index, edges_left, loop, edge_map)
        sorted = sort_verts_by_uv(obj, bm, loop, uv_map, dir)
        loops.append(sorted)

    return loops


def get_vert_loops(obj, bm, edges, edge_map):
    edges_left = set(edges)
    vert_loops = []

    # separate edges into vertex loops
    while len(edges_left) > 0:
        loop = set()
        edge_index = list(edges_left)[0]
        parse_loop(bm, edge_index, edges_left, loop, edge_map)
        verts = [ index for index in loop]
        vert_loops.append(verts)

    return vert_loops


def merge_length_coordinate_loops(loops):

    size = len(loops[0])

    for merged in loops:
        if len(merged) != size:
            return None

    num = len(loops)
    merged = []

    for i in range(0, size):
        co = Vector((0,0,0))
        for l in range(0, num):
            co += loops[l][i]
        co /= num
        merged.append(co)

    return merged


def sort_lateral_card(obj, bm, loops, uv_map, dir):

    sorted = []
    card = {}

    for loop in loops:
        co = Vector((0,0,0))
        uv = Vector((0,0))
        count = 0
        for vert_index in loop:
            co += obj.matrix_world @ bm.verts[vert_index].co
            uv += uv_map[vert_index]
            count += 1
        co /= count
        uv /= count
        sorted.append([co, loop, uv])

    if dir.x > 0:
        sorted.sort(reverse=False, key=sort_func_u)
    elif dir.x < 0:
        sorted.sort(reverse=True, key=sort_func_u)
    elif dir.y > 0:
        sorted.sort(reverse=False, key=sort_func_v)
    else:
        sorted.sort(reverse=True, key=sort_func_v)

    card["median"] = [ co for co, loop, uv in sorted ]
    card["loops"] = [ loop for co, loop, uv in sorted ]
    return card


def selected_cards_to_length_loops(chr_cache, obj, card_dir : Vector, one_loop_per_card = True):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    # normalize card dir
    card_dir.normalize()

    # select linked and set to edge mode
    utils.edit_mode_to(obj, only_this=True)
    bpy.ops.mesh.select_linked(delimit={'UV'})
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    # object mode to save edit changes
    utils.object_mode_to(obj)

    deselect_invalid_materials(chr_cache, obj)

    # get the bmesh
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    ul = bm.loops.layers.uv[0]

    # get lists of the faces in each selected island
    islands = get_hair_card_islands(bm, ul, use_selected=True)

    utils.log_info(f"{len(islands)} islands selected.")

    all_loops = []

    for island in islands:

        utils.log_info(f"Processing island, faces: {len(island)}")
        utils.log_indent()

        # each island has a unique UV map
        uv_map = get_island_uv_map(bm, ul, island)

        # get all edges aligned with the card dir in the island
        edges = get_aligned_edges(bm, island, card_dir, uv_map)

        utils.log_info(f"{len(edges)} aligned edges.")

        # map connected edges
        edge_map = get_aligned_edge_map(bm, edges)

        # separate into ordered vertex loops
        loops = get_ordered_coordinate_loops(obj, bm, edges, card_dir, uv_map, edge_map)

        utils.log_info(f"{len(loops)} ordered loops.")

        # (merge and) generate poly curves
        if one_loop_per_card:
            loop = merge_length_coordinate_loops(loops)
            if loop:
                all_loops.append(loop)
            else:
                utils.log_info("Loops have differing lengths, skipping.")
        else:
            for loop in loops:
                all_loops.append(loop)

        utils.log_recess()

    #for face in bm.faces: face.select = False
    #for edge in bm.edges: edge.select = False
    #for vert in bm.verts: vert.select = False
    #for e in edges:
    #    bm.edges[e].select = True

    bm.to_mesh(mesh)

    return all_loops


def selected_cards_to_curves(chr_cache, obj, card_dir : Vector, one_loop_per_card = True):
    curve = create_curve()
    loops = selected_cards_to_length_loops(chr_cache, obj, card_dir, one_loop_per_card)
    for loop in loops:
        add_poly_spline(loop, curve)
    # TODO
    # Put the curve object to the same scale as the body mesh
    # With roots above the scalp plant the root of the curves into the scalp? (within tolerance)
    #   or add an new root point on the scalp...
    # With roots below the scalp, crop the loop
    # convert to curves
    # set curve render subdivision to at least 2
    # snap curves to surface


def loop_length(loop, index = -1):
    if index == -1:
        index = len(loop) - 1
    p0 = loop[0]
    d = 0
    for i in range(1, index + 1):
        p1 = loop[i]
        d += (p1 - p0).length
        p0 = p1
    return d


def eval_loop_at(loop, length, fac):
    p0 = loop[0]
    f0 = 0
    for i in range(1, len(loop)):
        p1 = loop[i]
        v = p1 - p0
        fl = v.length / length
        f1 = f0 + fl
        if fac <= f1 and fac >= f0:
            df = fac - f0
            return p0 + v * (df / fl)
        f0 = f1
        p0 = p1
        f1 += fl
    return p0


def clear_hair_bone_weights(chr_cache, arm, objects, bone_mode):
    utils.object_mode_to(arm)

    bone_chains = get_bone_chains(arm, bone_mode)

    hair_bones = []
    for bone_chain in bone_chains:
        for bone_def in bone_chain:
            hair_bones.append(bone_def["name"])

    for obj in objects:
        remove_hair_bone_weights(arm, obj, hair_bone_list=hair_bones)

    arm.data.pose_position = "POSE"
    utils.pose_mode_to(arm)


def remove_hair_bones(chr_chache, arm, objects, bone_mode):
    utils.object_mode_to(arm)

    hair_bones = []
    bone_chains = None
    if bone_mode == "SELECTED":
        # in selected bone mode, only remove the bones in the selected chains
        bone_chains = get_bone_chains(arm, bone_mode)
        for bone_chain in bone_chains:
            for bone_def in bone_chain:
                hair_bones.append(bone_def["name"])
    else:
        # otherwise remove all possible hair bones
        for bone in arm.data.bones:
            if bone.name.startswith(HAIR_BONE_PREFIX):
                hair_bones.append(bone.name)

    if hair_bones and utils.edit_mode_to(arm, True):
        # remove the bones in edit mode
        for bone_name in hair_bones:
            arm.data.edit_bones.remove(arm.data.edit_bones[bone_name])

    for obj in objects:
        #remove the weights from the selected meshes
        remove_hair_bone_weights(arm, obj, hair_bone_list=hair_bones)

    utils.object_mode_to(arm)


def contains_hair_bone_chain(arm, loop_index):
    """Edit mode"""
    for bone in arm.data.edit_bones:
        if bone.name.startswith(f"{HAIR_BONE_PREFIX}_{loop_index}_"):
            return True
    return False


def find_unused_hair_bone_index(arm, loop_index):
    """Edit mode"""
    while contains_hair_bone_chain(arm, loop_index):
        loop_index += 1
    return loop_index


def loop_to_bones(arm, head_bone, loop, loop_index, length, segments, skip_first_bones):
    """Edit mode"""
    fac = 0
    df = 1.0 / segments
    chain = []
    first = True
    parent_bone = head_bone

    for s in range(0, segments):
        if s >= skip_first_bones:
            bone_name = f"{HAIR_BONE_PREFIX}_{loop_index}_{s}"
            bone : bpy.types.EditBone = bones.new_edit_bone(arm, bone_name, parent_bone.name)
            bone.head = arm.matrix_world.inverted() @ eval_loop_at(loop, length, fac)
            bone.tail = arm.matrix_world.inverted() @ eval_loop_at(loop, length, fac + df)
            bone_z = (head_bone.head - bone.head).normalized()
            bone.align_roll(bone_z)
            parent_bone = bone
            chain.append(bone_name)
            if first:
                bone.use_connect = False
                first = False
            else:
                bone.use_connect = True
        fac += df
    return chain


def selected_cards_to_bones(chr_cache, arm, obj, card_dir : Vector, one_loop_per_card = True, bone_length = 0.05, skip_first_bones = 0):

    mode_selection = utils.store_mode_selection()
    arm_pose = reset_pose(arm)

    repair_orphaned_hair_bones(arm)
    utils.object_mode_to(arm)

    head_bone = bones.get_pose_bone(arm, HEAD_BONE_NAME)
    if head_bone:
        loops = selected_cards_to_length_loops(chr_cache, obj, card_dir, one_loop_per_card)
        utils.edit_mode_to(arm)
        head_bone = bones.get_edit_bone(arm, HEAD_BONE_NAME)
        loop_index = 1
        for loop in loops:
            length = loop_length(loop)
            segments = round(length / bone_length)
            loop_index = find_unused_hair_bone_index(arm, loop_index)
            loop_to_bones(arm, head_bone, loop, loop_index, length, segments, skip_first_bones)
            loop_index += 1
    utils.object_mode_to(arm)

    restore_pose(arm, arm_pose)
    utils.restore_mode_selection(mode_selection)



def get_hair_cards_lateral(chr_cache, obj, card_dir : Vector, card_selection_mode):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    # normalize card dir
    card_dir.normalize()

    # select linked and set to edge mode
    utils.edit_mode_to(obj, only_this=True)
    if card_selection_mode == "ALL":
        bpy.ops.mesh.select_all(action='SELECT')
    else:
        bpy.ops.mesh.select_linked(delimit={'UV'})

    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    # object mode to save edit changes
    utils.object_mode_to(obj)

    deselect_invalid_materials(chr_cache, obj)

    # get the bmesh
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    ul = bm.loops.layers.uv[0]

    # get lists of the faces in each selected island
    islands = get_hair_card_islands(bm, ul, use_selected=True)

    utils.log_info(f"{len(islands)} islands selected.")

    cards = []

    for island in islands:

        utils.log_info(f"Processing island, faces: {len(island)}")
        utils.log_indent()

        # each island has a unique UV map
        uv_map = get_island_uv_map(bm, ul, island)

        # get all edges NOT aligned with the card dir in the island, i.e. the lateral edges
        edges = get_aligned_edges(bm, island, card_dir, uv_map, get_non_aligned=True)

        utils.log_info(f"{len(edges)} non-aligned edges.")

        # map connected edges
        edge_map = get_aligned_edge_map(bm, edges)

        # separate into lateral vertex loops
        vert_loops = get_vert_loops(obj, bm, edges, edge_map)

        utils.log_info(f"{len(vert_loops)} lateral loops.")

        # generate hair card info
        # a median coordinate loop representing the median positions of the hair card
        card = sort_lateral_card(obj, bm, vert_loops, uv_map, card_dir)
        cards.append(card)

        utils.log_recess()

    return bm, cards


def get_distance_to_bone_def(bone_def, co : Vector):
    #bone_def = { "name": pose_bone.name, "head": head, "tail": tail, "line": line, "dir": dir }
    head : Vector = bone_def["head"]
    tail : Vector = bone_def["tail"]
    line : Vector = bone_def["line"]
    dir : Vector = bone_def["dir"]
    length = bone_def["length"]
    from_head : Vector = co - head
    from_tail : Vector = co - tail
    if line.dot(from_head) <= 0:
        return (co - head).length, 0.0
    elif line.dot(from_tail) >= 0:
        return (co - tail).length, 1.0
    else:
        return (line.cross(from_head) / length).length, min(1.0, max(0.0, dir.dot(from_head) / length))


def get_closest_bone_def(bone_chain, co, max_radius):
    least_distance = max_radius * 2.0
    least_bone_def = bone_chain[0]
    least_fac = 0
    for bone_def in bone_chain:
        d, f = get_distance_to_bone_def(bone_def, co)
        if d < least_distance:
            least_distance = d
            least_bone_def = bone_def
            least_fac = f
    return least_bone_def, least_distance, least_fac


def get_weighted_bone_distance(bone_chain, max_radius, median_loop, median_length):
    weighted_distance = 0
    co_length = 0
    last_co = median_loop[0]
    for co in median_loop:
        co_length += (co - last_co).length
        factor = co_length / median_length
        bone_def, distance, fac = get_closest_bone_def(bone_chain, co, max_radius)
        weighted_distance += distance * factor * 2.0
    return weighted_distance / len(median_loop)


def weight_card_to_bones(obj, bm : bmesh.types.BMesh, card, sorted_bones, max_radius, max_bones, max_weight,
                         curve, variance):

    # vertex weights are in the deform layer of the BMesh verts

    bm.verts.layers.deform.verify()
    dl = bm.verts.layers.deform.active

    median = card["median"]

    median_length = loop_length(median)

    if len(sorted_bones) < max_bones:
        max_bones = len(sorted_bones)

    bone_weight_mods = []
    min_weight = max_weight - max_weight * variance
    for i in range(0, max_bones):
        bone_weight_mods.append(random.uniform(min_weight, max_weight))

    for i, co in enumerate(median):
        ml = loop_length(median, i)
        card_length_fac = math.pow(ml / median_length, curve)
        for b in range(0, max_bones):
            bone_chain = sorted_bones[b]["bones"]
            bone_def, bone_distance, bone_fac = get_closest_bone_def(bone_chain, co, max_radius)
            weight_distance = min(max_radius, max(0, max_radius - bone_distance))
            weight = bone_weight_mods[b] * (weight_distance / max_radius) / max_bones
            if bone_def != bone_chain[0]:
                bone_fac = 1.0
            weight *= max(0, min(bone_fac, card_length_fac))
            bone_name = bone_def["name"]
            vg = meshutils.add_vertex_group(obj, bone_name)
            if vg:
                vert_loop = card["loops"][i]
                for vert_index in vert_loop:
                    vertex = bm.verts[vert_index]
                    vertex[dl][vg.index] = weight


def sort_func_weighted_distance(bone_weight_distance):
    return bone_weight_distance["distance"]


def assign_bones(obj, bm, cards, bone_chains, max_radius, max_bones, max_weight, curve, variance):
    for i, card in enumerate(cards):
        median = card["median"]
        median_length = loop_length(median)
        sorted_bones = []
        for bone_chain in bone_chains:
            weighted_distance = get_weighted_bone_distance(bone_chain, max_radius, median, median_length)
            #if weighted_distance < max_radius:
            bone_weight_distance = {"distance": weighted_distance, "bones": bone_chain}
            sorted_bones.append(bone_weight_distance)
        sorted_bones.sort(reverse=False, key=sort_func_weighted_distance)
        weight_card_to_bones(obj, bm, card, sorted_bones, max_radius, max_bones, max_weight, curve, variance)


def remove_hair_bone_weights(arm, obj : bpy.types.Object, scale_existing_weights = 1.0, hair_bone_list = None):
    """Remove all vertex groups starting with 'Hair'
    """

    utils.object_mode_to(obj)

    if hair_bone_list is None:
        hair_bone_list = []
        for vg in obj.vertex_groups:
            if vg.name.startswith(HAIR_BONE_PREFIX):
                hair_bone_list.append(vg.name)

    vg : bpy.types.VertexGroup
    for vg in obj.vertex_groups:
        if vg.name not in hair_bone_list and scale_existing_weights == 0.0:
            hair_bone_list.append(vg.name)

    for vg_name in hair_bone_list:
        meshutils.remove_vertex_group(obj, vg_name)

    utils.edit_mode_to(obj)
    utils.object_mode_to(obj)


def scale_existing_weights(obj, bm, scale):
    bm.verts.ensure_lookup_table()
    bm.verts.layers.deform.verify()
    dl = bm.verts.layers.deform.active
    for vert in bm.verts:
        for vg in obj.vertex_groups:
            if vg.index in vert[dl].keys():
                vert[dl][vg.index] *= scale


def add_bone_chain(arm, edit_bone : bpy.types.EditBone, chain):

    if edit_bone.children and len(edit_bone.children) > 1:
        return False

    head = arm.matrix_world @ edit_bone.head
    tail = arm.matrix_world @ edit_bone.tail
    line = tail - head
    dir = line.normalized()

    # extend the last bone def in the chain to ensure full overlap with hair mesh
    if not edit_bone.children:
        line *= 4
        tail = head + line

    bone_def = { "name": edit_bone.name, "head": head, "tail": tail, "line": line, "dir": dir, "length": line.length }
    chain.append(bone_def)

    if edit_bone.children and len(edit_bone.children) == 1:
        return add_bone_chain(arm, edit_bone.children[0], chain)

    return True


def repair_orphaned_hair_bones(arm):
    # find orphaned hair bones and reparent
    reparent_list = []
    for bone in arm.pose.bones:
        if bone.name.startswith(HAIR_BONE_PREFIX):
            if not bone.parent:
                reparent_list.append(bone.name)

    if reparent_list and utils.edit_mode_to(arm, True):
        head_edit_bone = bones.get_edit_bone(arm, HEAD_BONE_NAME)
        for bone_name in reparent_list:
            arm.data.edit_bones[bone_name].parent = head_edit_bone
        utils.object_mode_to(arm)


def get_bone_chains(arm, bone_selection_mode):
    """Get each bone chain from the armature that contains the keyword HAIR_BONE_PREFIX, child of HEAD_BONE_NAME
    """

    repair_orphaned_hair_bones(arm)

    utils.edit_mode_to(arm)

    bone_chains = []
    head_bone : bpy.types.PoseBone = bones.get_edit_bone(arm, HEAD_BONE_NAME)

    child_bone : bpy.types.Bone
    for child_bone in head_bone.children:
        if child_bone.name.startswith(HAIR_BONE_PREFIX):
            use_this = arm.data.bones[child_bone.name].select or bone_selection_mode == "ALL"
            if use_this:
                chain = []
                if not add_bone_chain(arm, child_bone, chain):
                    continue
                bone_chains.append(chain)

    utils.object_mode_to(arm)

    return bone_chains


def smooth_hair_bone_weights(arm, obj, bone_chains, iterations):
    if iterations == 0:
        return

    for bone in arm.data.bones:
        bone.select = False

    for bone_chain in bone_chains:
        for bone_def in bone_chain:
            bone_name = bone_def["name"]
            arm.data.bones[bone_name].select = True

    # Note: BONE_SELECT group select mode is only available if the armature is also selected with the active mesh
    #       (otherwise it doesn't even exist as an enum option)
    utils.set_mode("OBJECT")
    utils.try_select_objects([arm, obj], True)
    utils.set_active_object(obj)
    utils.set_mode("WEIGHT_PAINT")
    bpy.ops.object.vertex_group_smooth(group_select_mode='BONE_SELECT', factor = 1.0, repeat = iterations)
    utils.object_mode_to(obj)


def bind_cards_to_bones(chr_cache, arm, objects, card_dir : Vector, max_radius, max_bones, max_weight, curve, variance, existing_scale, card_mode, bone_mode, smoothing):

    reset_pose(arm)

    utils.object_mode_to(arm)
    bone_chains = get_bone_chains(arm, bone_mode)

    hair_bones = []
    for bone_chain in bone_chains:
        for bone_def in bone_chain:
            hair_bones.append(bone_def["name"])

    for obj in objects:
        remove_hair_bone_weights(arm, obj, hair_bone_list=hair_bones)
        bm, cards = get_hair_cards_lateral(chr_cache, obj, card_dir, card_mode)
        scale_existing_weights(obj, bm, existing_scale)
        assign_bones(obj, bm, cards, bone_chains, max_radius, max_bones, max_weight, curve, variance)
        bm.to_mesh(obj.data)

        smooth_hair_bone_weights(arm, obj, bone_chains, smoothing)

    arm.data.pose_position = "POSE"
    utils.pose_mode_to(arm)


def deselect_invalid_materials(chr_cache, obj):
    """Mesh polygon selection only works in OBJECT mode"""
    if utils.object_exists_is_mesh(obj):
        for slot in obj.material_slots:
            mat = slot.material
            mat_cache = chr_cache.get_material_cache(mat)
            if mat_cache:
                if mat_cache.material_type == "SCALP":
                    meshutils.select_material_faces(obj, mat, False)


def reset_pose(arm):
    arm_pose = arm.data.pose_position
    arm.data.pose_position = "REST"
    return arm_pose


def restore_pose(arm, arm_pose):
    arm.data.pose_position = arm_pose


class CC3OperatorHair(bpy.types.Operator):
    """Blender Hair Functions"""
    bl_idname = "cc3.hair"
    bl_label = "Blender Hair Functions"
    #bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        if self.param == "CARDS_TO_CURVES":

            chr_cache = props.get_context_character_cache(context)
            selected_cards_to_curves(chr_cache, bpy.context.active_object,
                                     prefs.hair_dir_vector(),
                                     one_loop_per_card = prefs.hair_curve_merge_loops == "MERGE")

        if self.param == "ADD_BONES":

            chr_cache = props.get_context_character_cache(context)
            arm = chr_cache.get_armature()
            hair_obj = bpy.context.active_object

            if utils.object_exists_is_mesh(hair_obj) and utils.object_exists_is_armature(arm):
                selected_cards_to_bones(chr_cache, arm,
                                        hair_obj,
                                        prefs.hair_dir_vector(),
                                        one_loop_per_card = True,
                                        bone_length = prefs.hair_rig_bone_length / 100,
                                        skip_first_bones = prefs.hair_rig_bind_skip_count)
            else:
                self.report({"ERROR"}, "Active Object must be a mesh!")

        if self.param == "REMOVE_HAIR_BONES":

            chr_cache = props.get_context_character_cache(context)
            arm = utils.get_armature_in_objects(bpy.context.selected_objects)
            if not arm:
                arm = chr_cache.get_armature()

            objects = [ obj for obj in bpy.context.selected_objects if utils.object_exists_is_mesh(obj) ]

            if utils.object_exists_is_armature(arm):
                remove_hair_bones(chr_cache, arm, objects, prefs.hair_rig_bind_bone_mode)

        if self.param == "BIND_TO_BONES":

            chr_cache = props.get_context_character_cache(context)
            arm = utils.get_armature_in_objects(bpy.context.selected_objects)
            if not arm:
                arm = chr_cache.get_armature()

            objects = [ obj for obj in bpy.context.selected_objects if utils.object_exists_is_mesh(obj) ]

            seed = prefs.hair_rig_bind_seed
            random.seed(seed)

            if utils.object_exists_is_armature(arm) and objects:
                bind_cards_to_bones(chr_cache, arm,
                                    objects,
                                    prefs.hair_dir_vector(),
                                    prefs.hair_rig_bind_bone_radius / 100,
                                    prefs.hair_rig_bind_bone_count,
                                    prefs.hair_rig_bind_bone_weight,
                                    prefs.hair_rig_bind_weight_curve,
                                    prefs.hair_rig_bind_bone_variance,
                                    prefs.hair_rig_bind_existing_scale,
                                    prefs.hair_rig_bind_card_mode,
                                    prefs.hair_rig_bind_bone_mode,
                                    prefs.hair_rig_bind_smoothing)
            else:
                self.report({"ERROR"}, "Selected Object(s) to bind must be Meshes!")

            prefs.hair_rig_bind_existing_scale = 1.0

        if self.param == "CLEAR_WEIGHTS":

            chr_cache = props.get_context_character_cache(context)
            arm = utils.get_armature_in_objects(bpy.context.selected_objects)
            if not arm:
                arm = chr_cache.get_armature()

            objects = [ obj for obj in bpy.context.selected_objects if utils.object_exists_is_mesh(obj) ]

            if utils.object_exists_is_armature(arm) and objects:
                clear_hair_bone_weights(chr_cache, arm, objects, prefs.hair_rig_bind_bone_mode)
            else:
                self.report({"ERROR"}, "Selected Object(s) to clear weights must be Meshes!")


        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "":
            return ""

        return ""


class CC3ExportHair(bpy.types.Operator):
    """Export Hair Curves"""
    bl_idname = "cc3.export_hair"
    bl_label = "Export Hair"
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Base filepath used for exporting the hair curves",
        maxlen=1024,
        subtype='FILE_PATH',
        )

    filename_ext = ""  # ExportHelper mixin class uses this

    #filter_glob: bpy.props.StringProperty(
    #    default="*.fbx;*.obj;*.blend",
    #    options={"HIDDEN"},
    #    )

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        objects = bpy.context.selected_objects.copy()
        chr_cache = props.get_any_character_cache_from_objects(objects, True)
        print(chr_cache)

        export_blender_hair(self, chr_cache, objects, self.filepath)

        return {"FINISHED"}


    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


    @classmethod
    def description(cls, context, properties):
        return "Export the hair curves to Alembic."