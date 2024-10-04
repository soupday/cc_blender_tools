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
from . import physics, rigidbody, springbones, modifiers, geom, utils, jsonutils, bones, meshutils, vars


STROKE_JOIN_THRESHOLD = 1.0 / 100.0 # 1cm
BONE_SMOOTH_LEVEL_CUSTOM_PROP = "rl_generated_smoothing_level"

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
            if obj_cache.is_mesh() and obj_cache.source_name == source_name:
                possible.append(obj_cache)
        # if only one possibility return that
        if possible and len(possible) == 1:
            return possible[0]
        # try to find the correct object cache by matching the materials
        # try matching all the materials first
        for obj_cache in possible:
            o = obj_cache.get_object()
            if o:
                found = True
                for mat in obj.data.materials:
                    if mat not in o.data.materials:
                        found = False
                if found:
                    return obj_cache
        # then try just matching any
        for obj_cache in possible:
            o = obj_cache.get_object()
            if o:
                found = True
                for mat in obj.data.materials:
                    if mat in o.data.materials:
                        return obj_cache
    return None


def clear_particle_systems(obj):
    if utils.object_mode() and utils.set_only_active_object(obj):
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
    props = vars.props()
    prefs = vars.prefs()

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

            if props.hair_export_group_by == "CURVE":
                for obj in objects:
                    if obj.type == "CURVES" and obj.parent == parent:
                        group = [obj]
                        name = obj.data.name
                        groups[name] = group
                        utils.log_info(f"Group: {name}, Object: {obj.data.name}")

            elif props.hair_export_group_by == "NAME":
                for obj in objects:
                    if obj.type == "CURVES" and obj.parent == parent:
                        name = utils.strip_name(obj.data.name)
                        if name not in groups.keys():
                            groups[name] = []
                        groups[name].append(obj)
                        utils.log_info(f"Group: {name}, Object: {obj.data.name}")

            else: #props.hair_export_group_by == "NONE":
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


def card_dir_from_uv_map(card_dirs, uv_map):
    # analyse uv bounds
    uv_min, uv_max = geom.get_uv_bounds(uv_map)
    uv_extent = uv_max - uv_min
    uv_aspect = uv_extent.x / uv_extent.y

    # only deal with vertical or horizontal cards
    # squarish cards are patches of hair that shouldn't be weighted
    if uv_aspect >= 2.0:
        uv_orient = "HORIZONTAL"
    elif uv_aspect <= 0.5:
        uv_orient = "VERTICAL"
    else:
        uv_orient = "SQUARE"
    return card_dirs[uv_orient]


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


def grid_to_loops(obj, bm, island, card_dirs, one_loop_per_card):
    props = vars.props()

    # each island has a unique UV map
    uv_map = geom.get_uv_island_map(bm, 0, island)

    card_dir = card_dir_from_uv_map(card_dirs, uv_map)

    # get all edges aligned with the card dir in the island
    edges = geom.get_uv_aligned_edges(bm, island, card_dir, uv_map, dir_threshold=props.hair_card_dir_threshold)
    utils.log_info(f"{len(edges)} aligned edges.")

    # map connected edges
    edge_map = geom.get_linked_edge_map(bm, edges)

    # separate into ordered vertex loops
    loops = get_ordered_coordinate_loops(obj, bm, edges, card_dir, uv_map, edge_map)

    utils.log_info(f"{len(loops)} ordered loops.")

    # (merge and) generate poly curves
    if one_loop_per_card:
        loop = merge_length_coordinate_loops(loops)
        if loop:
            return [loop]
        else:
            utils.log_info("Loops have differing lengths, grid extraction failed.")
            return None
    else:
        return loops

    return True


def get_vert_loop_to(obj, bm, from_index, to_index, edges, reverse = False):
    verts = []
    co_loop = []
    following = False
    for edge_index in edges:
        if edge_index == from_index:
            following = True
        if edge_index == to_index:
            following = False
        if following:
            edge = bm.edges[edge_index]
            for vert in edge.verts:
                if vert.index not in verts:
                    verts.append(vert.index)
                    if reverse:
                        co_loop.insert(0, obj.matrix_world @ vert.co)
                    else:
                        co_loop.append(obj.matrix_world @ vert.co)
    return verts, co_loop


def sort_boundary_edges(bm, edges : set, start_index):
    edge = bm.edges[start_index]
    vert = edge.verts[1]
    edge_loop = [start_index]
    edges.remove(start_index)
    following = True
    while following:
        following = False
        for next_edge in vert.link_edges:
            if next_edge != edge and next_edge.index in edges:
                edge_loop.append(next_edge.index)
                edges.remove(next_edge.index)
                for next_vert in next_edge.verts:
                    if next_vert.index != vert.index:
                        edge = next_edge
                        vert = next_vert
                        following = True
                        break
            if following:
                break
    return edge_loop


def split_boundary_loops(obj, bm, boundary_edges, card_dir, uv_map):
    edge : bmesh.types.BMEdge
    min_proj = math.inf
    max_proj = -math.inf
    list_edges = list(boundary_edges)
    min_edge_index = list_edges[0]
    max_edge_index = list_edges[-1]
    for edge_index in boundary_edges:
        edge = bm.edges[edge_index]
        vert = edge.verts[0]
        uv = uv_map[vert.index]
        proj = -card_dir.dot(uv)
        if proj < min_proj:
            min_proj = proj
            min_edge_index = edge.index
        if proj > max_proj:
            max_proj = proj
            max_edge_index = edge.index
    # sort the boundary edges in order, starting from max_edge (the top most UV edge)
    num_edges = len(boundary_edges)
    edge_loop = sort_boundary_edges(bm, boundary_edges, max_edge_index)
    # return nothing if the sorted boundary edge does not contain all the edges
    # (i.e. there are breaks in the edges)
    if len(edge_loop) != num_edges:
        utils.log_info(f"Unable to sort boundary edges: {len(edge_loop)} != {num_edges}")
        return None, None
    # extract the left and right coordinate loops
    left_verts, left_coords = get_vert_loop_to(obj, bm, max_edge_index, min_edge_index, edge_loop)
    right_verts, right_coords = get_vert_loop_to(obj, bm, min_edge_index, max_edge_index, edge_loop, reverse=True)
    # need to reverse the order of one of these... but which one

    return left_coords, right_coords


def get_projection_on_loop(loop, co):
    p0 = loop[0]
    min_distance = math.inf
    projected_point = p0
    projected_length = 0.0
    length = 0.0
    for i in range(1, len(loop)):
        p1 = loop[i]
        segment_length = (p1 - p0).length
        dist, fac = distance_from_line(co, p0, p1)
        if dist < min_distance:
            min_distance = dist
            projected_point = p0 * (1.0 - fac) + p1 * fac
            projected_length = length + segment_length * fac
        length += segment_length
        p0 = p1
    return projected_point, projected_length


def proj_loop_sort_func(co_len_pair):
    return co_len_pair[1]


def project_boundary_loop(src_loop, dst_loop):
    """Projects the source loop onto the destination loop."""
    sort_points = []
    # add the original points & lengths
    for i in range(0, len(dst_loop)):
        sort_points.append([dst_loop[i], loop_length(dst_loop, i)])
    # add the projected points & lengths
    for co in src_loop:
        projected_point, projected_length = get_projection_on_loop(dst_loop, co)
        sort_points.append([projected_point, projected_length])
    # sort by length
    sort_points.sort(key=proj_loop_sort_func)
    # return the coordinate loop
    loop = [ pair[0] for pair in sort_points ]
    return loop


def mesh_to_loops(obj, bm, island, card_dirs):
    props = vars.props()

    # each island has a unique UV map
    uv_map = geom.get_uv_island_map(bm, 0, island)

    card_dir = card_dir_from_uv_map(card_dirs, uv_map)

    # find the boundary edges
    boundary_edges = geom.get_boundary_edges(bm, island)

    # check for minimum bound edges
    if len(boundary_edges) < 4:
        return None

    # the top most UV in the boundary edge is the start of the left hand side
    # the bottom most UV in the boundary edge is the end of the right hand side
    # split the boundary edge into two loops left and right
    left_loop, right_loop = split_boundary_loops(obj, bm, boundary_edges, card_dir, uv_map)

    if left_loop and right_loop:

        # project each vertex in loop_left into loop_right, order by projected length
        projected_right_loop = project_boundary_loop(left_loop, right_loop)

        # project each vertex in loop_right into loop_left, order by projected length
        projected_left_loop = project_boundary_loop(right_loop, left_loop)

        # the two loops should now be the same length and each index in the loops represents
        # a point in one loop and/or it's projection in the other
        # now average the loops into one loop representing the mesh hair card
        loop = merge_length_coordinate_loops([projected_left_loop, projected_right_loop])

        if loop:
            return [loop]

    utils.log_info("Loops have differing lengths or breaks, mesh extraction failed.")
    return None


def selected_cards_to_length_loops(chr_cache, obj, card_dirs, one_loop_per_card = True, card_selection_mode = "SELECTED"):
    prefs = vars.prefs()
    props = vars.props()

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
    bm = geom.get_bmesh(mesh)

    # get lists of the faces in each selected island
    islands = geom.get_uv_islands(bm, 0, use_selected=True)

    utils.log_info(f"{len(islands)} islands selected.")

    all_loops = []
    cards = []

    for island in islands:

        utils.log_info(f"Processing island, faces: {len(island)}")
        utils.log_indent()

        is_grid = geom.is_island_grid(bm, island)
        loops = None
        if is_grid:
            loops = grid_to_loops(obj, bm, island, card_dirs, one_loop_per_card)

        if not loops:
            is_grid = False
            loops = mesh_to_loops(obj, bm, island, card_dirs)

        if is_grid:
            utils.log_info("Grid")
        else:
            utils.log_info("Polymesh")

        face : bmesh.types.BMFace
        verts = set()
        for face_index in island:
            face = bm.faces[face_index]
            for vert in face.verts:
                verts.add(vert.index)

        card = { "verts": verts, "loops": loops }
        cards.append(card)

        utils.log_recess()

    return cards, bm


def debug_loop(loop):
    curve = create_curve()
    add_poly_spline(loop, curve)


def selected_cards_to_curves(chr_cache, obj, card_dirs, one_loop_per_card = True):
    curve = create_curve()
    cards, bm = selected_cards_to_length_loops(chr_cache, obj, card_dirs, one_loop_per_card)
    for card in cards:
        loops = card["loops"]
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
        if fl > 0 and fac <= f1 and fac >= f0:
            df = fac - f0
            return p0 + v * (df / fl)
        f0 = f1
        p0 = p1
        f1 += fl
    return p0


def is_on_loop(co, loop, threshold = 0.001):
    """Is the coordinate on the loop.
       (All coordintes should be in world space)"""
    p0 = loop[0]
    min_distance = threshold + 1.0
    for i in range(1, len(loop)):
        p1 = loop[i]
        dist, fac = distance_from_line(co, p0, p1)
        if dist < min_distance:
            min_distance = dist
        if min_distance < threshold:
            return True
        p0 = p1
    return min_distance < threshold


def clear_hair_bone_weights(chr_cache, arm, objects, card_mode, bone_mode, parent_mode):
    utils.object_mode_to(arm)

    bone_chain_defs = get_bone_chain_defs(chr_cache, arm, bone_mode, parent_mode)

    hair_bones = []
    for bone_chain in bone_chain_defs:
        for bone_def in bone_chain:
            hair_bones.append(bone_def["name"])

    if not objects:
        objects = meshutils.get_child_objects_with_vertex_groups(arm, hair_bones)

    for obj in objects:
        remove_hair_bone_weights(obj, hair_bones, card_mode)

    arm.data.pose_position = "POSE"
    utils.pose_mode_to(arm)


def remove_hair_bones(chr_cache, arm, bone_mode, parent_mode):
    utils.object_mode_to(arm)

    hair_bones = []
    bone_chain_defs = get_bone_chain_defs(chr_cache, arm, bone_mode, parent_mode)
    for bone_chain in bone_chain_defs:
        for bone_def in bone_chain:
            hair_bones.append(bone_def["name"])

    # remove the bones in edit mode
    if hair_bones and utils.edit_mode_to(arm, True):
        for bone_name in hair_bones:
            arm.data.edit_bones.remove(arm.data.edit_bones[bone_name])

    # remove the spring rig if there are no child bones left
    if utils.edit_mode_to(arm):
        spring_rig = springbones.get_spring_rig(chr_cache, arm, parent_mode, mode = "EDIT")
        if spring_rig and not spring_rig.children:
            arm.data.edit_bones.remove(spring_rig)

    #use all mesh objects in the character with matching vertex groups
    objects = meshutils.get_child_objects_with_vertex_groups(arm, hair_bones)

    #remove the weights from the character meshes
    for obj in objects:
        remove_hair_bone_weights(obj, hair_bones, "ALL")

    utils.object_mode_to(arm)


def rename_hair_bones(chr_cache, arm, base_name, parent_mode):
    utils.object_mode_to(arm)

    bone_remap = {}
    bone_chain_defs = None

    hair_bones = []
    bone_chain_defs = get_bone_chain_defs(chr_cache, arm, "SELECTED", parent_mode)
    for bone_chain in bone_chain_defs:
        for bone_def in bone_chain:
            hair_bones.append(bone_def["name"])

    utils.edit_mode_to(arm)
    loop_index = 1
    for bone_chain in bone_chain_defs:
        loop_index = find_unused_hair_bone_index(arm, loop_index, base_name)
        chain_index = 0
        for bone_def in bone_chain:
            old_name = bone_def["name"]
            new_name = f"{base_name}_{loop_index}_{chain_index}"
            edit_bone : bpy.types.EditBone
            edit_bone = arm.data.edit_bones[old_name]
            edit_bone.name = new_name
            edit_bone.select = True
            bone_remap[old_name] = edit_bone.name
            chain_index += 1

    utils.object_mode_to(arm)

    #if no objects selected, use all mesh objects in the character with matching vertex groups
    objects = meshutils.get_child_objects_with_vertex_groups(arm, hair_bones)

    # now rename the vertex groups in all the objects...
    for obj in objects:
        for vg in obj.vertex_groups:
            if vg.name in bone_remap:
                vg.name = bone_remap[vg.name]


def contains_hair_bone_chain(arm, loop_index, prefix):
    """Edit mode"""
    for bone in arm.data.edit_bones:
        if bone.name.startswith(f"{prefix}_{loop_index}_"):
            return True
    return False


def find_unused_hair_bone_index(arm, loop_index, prefix):
    """Edit mode"""
    while contains_hair_bone_chain(arm, loop_index, prefix):
        loop_index += 1
    return loop_index


def is_nearby_bone(arm, world_pos):
    """Edit mode"""
    for edit_bone in arm.data.edit_bones:
        length = (world_pos - arm.matrix_world @ edit_bone.head).length
        if length < 0.01:
            return True
    return False


def custom_bone(chr_cache, arm, parent_mode, loop_index, bone_length, new_bones):
    """Must be in edit mode on the armature."""

    props = vars.props()

    hair_rig = springbones.get_spring_rig(chr_cache, arm, parent_mode, create_if_missing=True, mode = "EDIT")

    hair_bone_prefix = props.hair_rig_group_name

    if hair_rig:

        parent_bone = hair_rig

        bone_name = f"{hair_bone_prefix}_{loop_index}_0"
        bone : bpy.types.EditBone = bones.new_edit_bone(arm, bone_name, parent_bone.name)
        new_bones.append(bone_name)
        bone.select = True
        bone.select_head = True
        bone.select_tail = True
        world_origin = arm.matrix_world @ hair_rig.head
        world_pos = world_origin + Vector((0, 0.05, 0.15))
        while is_nearby_bone(arm, world_pos):
            world_pos += Vector((0, 0.0175, 0))
        world_head = world_pos
        world_tail = world_pos + Vector((0, 0, bone_length))
        bone.head = arm.matrix_world.inverted() @ world_head
        bone.tail = arm.matrix_world.inverted() @ world_tail
        bone_z = (((world_head + world_tail) * 0.5) - world_origin).normalized()
        bone.align_roll(bone_z)
        # set bone layer to 25, so we can show only the added hair bones 'in front'
        bones.set_bone_collection(arm, bone, "Spring (Edit)", None, vars.SPRING_EDIT_LAYER)
        # don't directly connect first bone in a chain
        bone.use_connect = False
        return True

    return False


def get_linked_bones(edit_bone, bone_list):
    if edit_bone.name not in bone_list:
        bone_list.append(edit_bone.name)
        for child_bone in edit_bone.children:
            get_linked_bones(child_bone, bone_list)
    return bone_list


def bone_chains_match(arm, bone_list_a, bone_list_b, tolerance = 0.001):

    tolerance /= ((arm.scale[0] + arm.scale[1] + arm.scale[2]) / 3.0)

    for bone_name_a in bone_list_a:
        edit_bone_a = arm.data.edit_bones[bone_name_a]
        has_match = False
        for bone_name_b in bone_list_b:
            edit_bone_b = arm.data.edit_bones[bone_name_b]
            delta = (edit_bone_a.head - edit_bone_b.head).length + (edit_bone_a.tail - edit_bone_b.tail).length
            if (delta < tolerance):
                has_match = True
        if not has_match:
            return False
    return True


def bone_chain_matches_loop(arm, bone_list, loop, threshold = 0.001):
    for bone_name in bone_list:
        if bone_name in arm.data.edit_bones:
            edit_bone = arm.data.edit_bones[bone_name]
            if not is_on_loop(arm.matrix_world @ edit_bone.head, loop, threshold):
                return False
            if not is_on_loop(arm.matrix_world @ edit_bone.tail, loop, threshold):
                return False
        else:
            return False
    return True


def remove_existing_loop_bones(chr_cache, arm, smoothed_loops):
    """Removes any bone chains in the hair rig that align with the loops"""

    props = vars.props()
    bone_selection_mode = props.hair_rig_bind_bone_mode

    if bone_selection_mode == "SELECTED":
        # select all linked bones
        utils.edit_mode_to(arm)
        bpy.ops.armature.select_linked()
        utils.object_mode_to(arm)

    utils.edit_mode_to(arm)

    hair_rigs = springbones.get_spring_rigs(chr_cache, arm, ["HEAD", "JAW"], mode="EDIT")

    remove_bone_list = []
    remove_loop_set_list = []
    removed_roots = []

    for parent_mode in hair_rigs:

        hair_rig = hair_rigs[parent_mode]["bone"]
        if hair_rig:

            for chain_root in hair_rig.children:
                chain_root : bpy.types.EditBone
                if chain_root not in removed_roots:
                    chain_bones = get_linked_bones(chain_root, [])
                    for smoothed_loop_set in smoothed_loops:
                        bone_smooth_level = 0
                        if BONE_SMOOTH_LEVEL_CUSTOM_PROP in chain_root:
                            bone_smooth_level = chain_root[BONE_SMOOTH_LEVEL_CUSTOM_PROP]
                        bone_smooth_loop = smoothed_loop_set[bone_smooth_level]
                        # compare the bone chain with the loop at it's generated smoothing level
                        if bone_chain_matches_loop(arm, chain_bones, bone_smooth_loop, 0.001):
                            remove_bones = False
                            remove_loop = False
                            if bone_selection_mode == "SELECTED":
                                if chain_root.select:
                                    # if the chain is selected, then it is to be replaced, so remove it.
                                    remove_bones = True
                                else:
                                    # otherwise remove the loop, so it won't generate new bones over the existing bones.
                                    remove_loop = True
                            else:
                                remove_bones = True

                            if remove_bones:
                                utils.log_info(f"Existing bone chain starting: {chain_root.name} is to be re-generated.")
                                remove_bone_list.extend(chain_bones)
                                removed_roots.append(chain_root)
                            if remove_loop:
                                utils.log_info(f"Existing bone chain starting: {chain_root.name} will not be replaced.")
                                remove_loop_set_list.append(smoothed_loop_set)

        if remove_bone_list:
            for bone_name in remove_bone_list:
                if bone_name in arm.data.edit_bones:
                    utils.log_info(f"Removing bone on generating loop: {bone_name}")
                    arm.data.edit_bones.remove(arm.data.edit_bones[bone_name])
                else:
                    utils.log_info(f"Already deleted: {bone_name} ?")

        if remove_loop_set_list:
            for smoothed_loop_set in remove_loop_set_list:
                if smoothed_loop_set in smoothed_loops:
                    smoothed_loops.remove(smoothed_loop_set)
                    utils.log_info(f"Removing loop from generation list")

    return


def remove_duplicate_bones(chr_cache, arm):
    """Remove any duplicate bone chains"""

    remove_list = []
    removed_roots = []

    utils.edit_mode_to(arm)

    hair_rigs = springbones.get_spring_rigs(chr_cache, arm, ["HEAD", "JAW"], mode = "EDIT")

    for parent_mode in hair_rigs:

        hair_rig = hair_rigs[parent_mode]["bone"]
        if hair_rig:

            for chain_root in hair_rig.children:
                if chain_root not in removed_roots:
                    chain_bones = get_linked_bones(chain_root, [])
                    for i in range(len(hair_rig.children)-1, 0, -1):
                        test_chain_root = hair_rig.children[i]
                        if test_chain_root not in removed_roots:
                            test_chain_bones = get_linked_bones(test_chain_root, [])
                            if chain_root == test_chain_root:
                                break
                            if bone_chains_match(arm, test_chain_bones, chain_bones, 0.001):
                                remove_list.extend(test_chain_bones)
                                removed_roots.append(test_chain_root)

    if remove_list:
        for bone_name in remove_list:
            if bone_name in arm.data.edit_bones:
                utils.log_info(f"Removing duplicate bone: {bone_name}")
                arm.data.edit_bones.remove(arm.data.edit_bones[bone_name])
            else:
                utils.log_info(f"Already deleted: {bone_name} ?")

    # object mode to save changes to edit bones
    utils.object_mode_to(arm)

    return


def loop_to_bones(chr_cache, arm, parent_mode, loop, loop_index, bone_length,
                  skip_length, trunc_length, smooth_level, new_bones):
    """Generate hair rig bones from vertex loops. Must be in edit mode on armature."""

    props = vars.props()

    if len(loop) < 2:
        return False

    length = loop_length(loop)

    # maximum skip length of half the length
    skip_length = min(skip_length, length / 2.0)
    # maximum trunc length of half the remaining length
    trunc_length = min(trunc_length, (length - skip_length) / 2.0)

    # skip zero length loops
    if length < 0.001:
        return False

    segments = max(1, round((length - skip_length - trunc_length) / bone_length))

    fac = skip_length / length
    max_fac = (length - trunc_length) / length
    df = (max_fac - fac) / segments
    chain = []
    first = True

    hair_rig = springbones.get_spring_rig(chr_cache, arm, parent_mode, create_if_missing=True, mode = "EDIT")

    hair_bone_prefix = props.hair_rig_group_name

    if hair_rig:

        parent_bone = hair_rig

        for s in range(0, segments):
            bone_name = f"{hair_bone_prefix}_{loop_index}_{s}"
            bone : bpy.types.EditBone = bones.new_edit_bone(arm, bone_name, parent_bone.name)
            bone[BONE_SMOOTH_LEVEL_CUSTOM_PROP] = smooth_level
            new_bones.append(bone_name)
            bone.select = True
            bone.select_head = True
            bone.select_tail = True
            world_head = eval_loop_at(loop, length, fac)
            world_tail = eval_loop_at(loop, length, fac + df)
            bone.head = arm.matrix_world.inverted() @ world_head
            bone.tail = arm.matrix_world.inverted() @ world_tail
            world_origin = arm.matrix_world @ hair_rig.head
            bone_z = (((world_head + world_tail) * 0.5) - world_origin).normalized()
            bone.align_roll(bone_z)
            parent_bone = bone
            # set bone layer to 25, so we can show only the added hair bones 'in front'
            bones.set_bone_collection(arm, bone, "Spring (Edit)", None, vars.SPRING_EDIT_LAYER)
            chain.append(bone_name)
            if first:
                bone.use_connect = False
                first = False
            else:
                bone.use_connect = True
            first = False
            fac += df

        return True

    return False


def get_smoothed_loops_set(loops):
    smoothed_loops_set = []
    for loop in loops:
        smoothed_loops_set.append(generate_smoothed_loop_levels(loop))
    return smoothed_loops_set


def selected_cards_to_bones(chr_cache, arm, obj, parent_mode, card_dirs,
                            one_loop_per_card = True, bone_length = 0.075,
                            skip_length = 0.075, trunc_length = 0.0, smooth_level = 0):
    """Lengths in world space units (m)."""

    props = vars.props()

    mode_selection = utils.store_mode_selection_state()
    arm_pose = set_rest_pose(arm)

    springbones.realign_spring_bones_axis(chr_cache, arm)

    springbones.show_spring_bone_edit_layer(chr_cache, arm, True)

    hair_bone_prefix = props.hair_rig_group_name

    # check anchor bone exists...
    anchor_bone_name = springbones.get_spring_anchor_name(chr_cache, arm, parent_mode)
    anchor_bone = bones.get_pose_bone(arm, anchor_bone_name)
    if anchor_bone:
        cards, bm = selected_cards_to_length_loops(chr_cache, obj, card_dirs, one_loop_per_card)
        utils.edit_mode_to(arm)
        smoothed_loops_set = []
        for card in cards:
            loops = card["loops"]
            card_smoothed_loops_set = get_smoothed_loops_set(loops)
            smoothed_loops_set.extend(card_smoothed_loops_set)
        remove_existing_loop_bones(chr_cache, arm, smoothed_loops_set)
        for edit_bone in arm.data.edit_bones:
                edit_bone.select_head = False
                edit_bone.select_tail = False
                edit_bone.select = False
        loop_index = 1
        new_bones = []
        for smoothed_loop in smoothed_loops_set:
            loop = smoothed_loop[smooth_level]
            loop_index = find_unused_hair_bone_index(arm, loop_index, hair_bone_prefix)
            if loop_to_bones(chr_cache, arm, parent_mode, loop, loop_index,
                                bone_length, skip_length, trunc_length, smooth_level, new_bones):
                loop_index += 1

    remove_duplicate_bones(chr_cache, arm)

    utils.object_mode_to(arm)

    restore_pose(arm, arm_pose)
    utils.restore_mode_selection_state(mode_selection)
    utils.try_select_object(arm)


def get_hair_cards_lateral(chr_cache, obj, card_dirs, card_selection_mode):
    prefs = vars.prefs()
    props = vars.props()

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
    bm = geom.get_bmesh(mesh)

    # get lists of the faces in each selected island
    islands = geom.get_uv_islands(bm, 0, use_selected=True)

    utils.log_info(f"{len(islands)} islands selected.")

    cards = []

    for island in islands:

        utils.log_info(f"Processing island, faces: {len(island)}")
        utils.log_indent()

        # each island has a unique UV map
        uv_map = geom.get_uv_island_map(bm, 0, island)

        card_dir = card_dir_from_uv_map(card_dirs, uv_map)

        # get all edges NOT aligned with the card dir in the island, i.e. the lateral edges
        edges = geom.get_uv_aligned_edges(bm, island, card_dir, uv_map,
                                          get_non_aligned=True, dir_threshold=props.hair_card_dir_threshold)

        utils.log_info(f"{len(edges)} non-aligned edges.")

        # map connected edges
        edge_map = geom.get_linked_edge_map(bm, edges)

        # separate into lateral vertex loops
        vert_loops = get_vert_loops(obj, bm, edges, edge_map)

        utils.log_info(f"{len(vert_loops)} lateral loops.")

        # generate hair card info
        # a median coordinate loop representing the median positions of the hair card
        card = sort_lateral_card(obj, bm, vert_loops, uv_map, card_dir)
        cards.append(card)

        utils.log_recess()

    return bm, cards


def distance_from_line(co, start, end):
    """Returns the distance from the line and where along the line it is closest."""
    line = end - start
    dir = line.normalized()
    length = line.length
    from_start : Vector = co - start
    from_end : Vector = co - end
    if line.dot(from_start) <= 0:
        return (co - start).length, 0.0
    elif line.dot(from_end) >= 0:
        return (co - end).length, 1.0
    else:
        return (line.cross(from_start) / length).length, min(1.0, max(0.0, dir.dot(from_start) / length))


def get_distance_to_bone_def(bone_def, co : Vector):
    #bone_def = { "name": pose_bone.name, "head": head, "tail": tail, "line": line, "dir": dir }
    head : Vector = bone_def["head"]
    tail : Vector = bone_def["tail"]
    return distance_from_line(co, head, tail)


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
    props = vars.props()
    CC4_SPRING_RIG = props.hair_rig_target == "CC4"

    bm.verts.layers.deform.verify()
    # vertex weights are in the deform layer of the BMesh verts
    dl = bm.verts.layers.deform.active

    card_loop = card["loops"][0]
    card_loop_length = loop_length(card_loop)

    if len(sorted_bones) < max_bones:
        max_bones = len(sorted_bones)

    min_weight = 0.01 if CC4_SPRING_RIG else 0.0
    acc_root_weight = (1.0 - max_weight) / max_bones
    bone_weight_variance_mods = []
    for i in range(0, max_bones):
        bone_weight_variance_mods.append(random.uniform(max_weight * (1 - variance), max_weight))

    first_bone_groups = []
    if CC4_SPRING_RIG:
        for b in range(0, max_bones):
            bone_chain = sorted_bones[b]["bones"]
            bone_def = bone_chain[0]
            bone_name = bone_def["name"]
            vg = meshutils.add_vertex_group(obj, bone_name)
            first_bone_groups.append(vg)

    for vert_index in card["verts"]:
        vertex : bmesh.types.BMVert = bm.verts[vert_index]
        if vertex.is_valid:
            co = obj.matrix_world @ vertex.co
            proj_point, proj_length = get_projection_on_loop(card_loop, co)
            card_length_fac = math.pow(proj_length / card_loop_length, curve)

            for b in range(0, max_bones):
                bone_chain = sorted_bones[b]["bones"]
                bone_def, bone_distance, bone_fac = get_closest_bone_def(bone_chain, co, max_radius)

                weight_distance = min(max_radius, max(0, max_radius - bone_distance))
                weight = bone_weight_variance_mods[b] * (weight_distance / max_radius) / max_bones

                # bone_fac is used to scale the weights, on the very first bone in the chain, from 0 to 1
                # (unless it's for a CC4 accessory)
                if CC4_SPRING_RIG:
                    bone_fac = 1.0
                elif bone_def != bone_chain[0]:
                    bone_fac = 1.0

                weight *= max(0, min(bone_fac, card_length_fac))
                weight = max(min_weight, weight)

                bone_name = bone_def["name"]
                vg = meshutils.add_vertex_group(obj, bone_name)
                if vg:
                    vertex[dl][vg.index] = weight
                    # if the weight's are scaled back, they need to be scaled back
                    # against the root bone's weights, unless this is for the root bone
                    # in which case we need to add the root weight
                    if CC4_SPRING_RIG:
                        first_vg = first_bone_groups[b]
                        if vg.index != first_vg.index:
                            vertex[dl][first_vg.index] = acc_root_weight
                        else:
                            vertex[dl][first_vg.index] = weight + acc_root_weight


def sort_func_weighted_distance(bone_weight_distance):
    return bone_weight_distance["distance"]


def assign_bones(obj, bm, cards, bone_chains, max_radius, max_bones, max_weight, curve, variance):
    for i, card in enumerate(cards):
        loops = card["loops"]
        if loops:
            card_loop = loops[0]
            card_loop_length = loop_length(card_loop)
            sorted_bones = []
            for bone_chain in bone_chains:
                weighted_distance = get_weighted_bone_distance(bone_chain, max_radius, card_loop, card_loop_length)
                bone_weight_distance = { "distance": weighted_distance, "bones": bone_chain }
                sorted_bones.append(bone_weight_distance)
            sorted_bones.sort(reverse=False, key=sort_func_weighted_distance)
            weight_card_to_bones(obj, bm, card, sorted_bones, max_radius, max_bones, max_weight, curve, variance)


def remove_hair_bone_weights(obj, hair_bone_list, card_mode):
    """Remove vertex groups for the given bones"""

    if card_mode == "ALL":
        # remove all hair_bone_list vertex groups from object
        utils.object_mode_to(obj)
        vg : bpy.types.VertexGroup
        for vg in obj.vertex_groups:
            if vg.name in hair_bone_list:
                meshutils.remove_vertex_group(obj, vg.name)
        utils.edit_mode_to(obj)
        utils.object_mode_to(obj)

    else:
        # select linked and set to edge mode
        utils.edit_mode_to(obj, only_this=True)
        bpy.ops.mesh.select_linked(delimit={'UV'})
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        # object mode to save edit changes
        utils.object_mode_to(obj)
        # remove weights from selected verts
        geom.remove_vertex_groups_from_selected(obj, hair_bone_list)


def scale_existing_weights(obj, bm, scale, exclude_bone_names: list = None):
    bm.verts.ensure_lookup_table()
    bm.verts.layers.deform.verify()
    dl = bm.verts.layers.deform.active

    min_weight = 1.0
    max_weight = 0.0
    for vert in bm.verts:
        weight = 0
        for vg in obj.vertex_groups:
            if exclude_bone_names and vg.name in exclude_bone_names:
                continue
            if vg.index in vert[dl].keys():
                weight += vert[dl][vg.index]
        min_weight = min(weight, min_weight)
        max_weight = max(weight, max_weight)

    if max_weight < 0.00001:
        # nothing left to scale
        return

    normalizing_scale = 1.0 / max_weight

    for vert in bm.verts:
        for vg in obj.vertex_groups:
            if exclude_bone_names and vg.name in exclude_bone_names:
                continue
            if vg.index in vert[dl].keys():
                vert[dl][vg.index] *= normalizing_scale * scale


def add_bone_chain_def(arm, edit_bone : bpy.types.EditBone, chain):

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
        return add_bone_chain_def(arm, edit_bone.children[0], chain)

    return True


def get_bone_chain_defs(chr_cache, arm, bone_selection_mode, parent_mode):
    """Get each bone chain from the spring bone rig."""

    utils.edit_mode_to(arm)

    if bone_selection_mode == "SELECTED":
        # select all linked bones
        utils.edit_mode_to(arm)
        bpy.ops.armature.select_linked()
        utils.object_mode_to(arm)
        utils.edit_mode_to(arm)

    # NOTE: remember edit bones do not survive mode changes...
    bone_chains = []

    hair_rig = springbones.get_spring_rig(chr_cache, arm, parent_mode, mode = "EDIT")
    if hair_rig:
        for child_bone in hair_rig.children:
            if arm.data.bones[child_bone.name].select or bone_selection_mode == "ALL":
                chain = []
                if not add_bone_chain_def(arm, child_bone, chain):
                    continue
                bone_chains.append(chain)

    utils.object_mode_to(arm)

    return bone_chains


def add_child_spring_bone_names(bone, names):
    for child in bone.children:
        names.append(child.name)
        add_child_spring_bone_names(child, names)


def get_all_spring_bone_names(chr_cache, arm):
    bone_names = []
    spring_rigs = springbones.get_spring_rigs(chr_cache, arm)
    for parent_mode in spring_rigs:
        spring_rig_def = spring_rigs[parent_mode]
        spring_root = spring_rig_def["bone"]
        add_child_spring_bone_names(spring_root, bone_names)
    return bone_names


def smooth_hair_bone_weights(arm, obj, bone_chains, iterations):
    props = vars.props()

    if iterations == 0:
        return

    for bone in arm.data.bones:
        bone.select = False

    # select all the bones involved
    for bone_chain in bone_chains:
        for bone_def in bone_chain:
            bone_name = bone_def["name"]
            if bone_name in arm.data.bones:
                arm.data.bones[bone_name].select = True

    # Note: BONE_SELECT group select mode is only available if the armature is also selected with the active mesh
    #       (otherwise it doesn't even exist as an enum option)
    utils.object_mode()
    utils.try_select_objects([arm, obj], True)
    utils.set_active_object(obj)
    utils.set_mode("WEIGHT_PAINT")
    try:
        bpy.ops.object.vertex_group_smooth(group_select_mode='BONE_SELECT', factor = 1.0, repeat = iterations)
    except:
        utils.log_error("Unable to smooth spring bone vertex groups: No armature modifier on hair mesh?")
    utils.object_mode_to(obj)

    # for CC4 rigs, lock rotation and position of the first bone in each chain
    for bone_chain in bone_chains:
        bone_def = bone_chain[0]
        bone_name = bone_def["name"]
        if bone_name in arm.data.bones:
            bone : bpy.types.Bone = arm.data.bones[bone_name]
            pose_bone : bpy.types.PoseBone = arm.pose.bones[bone_name]
            if props.hair_rig_target == "CC4":
                pose_bone.lock_location = [True, True, True]
                pose_bone.lock_rotation = [True, True, True]
                pose_bone.lock_scale = [True, True, True]
                pose_bone.lock_rotation_w = True
            else:
                pose_bone.lock_location = [False, False, False]
                pose_bone.lock_rotation = [False, False, False]
                pose_bone.lock_rotation_w = False
                pose_bone.lock_scale = [False, False, False]



def find_stroke_set_root(stroke_set, stroke, done : list):
    done.append(stroke)
    next_strokes, prev_strokes = stroke_set[stroke]
    if not prev_strokes:
        return stroke
    elif prev_strokes not in done:
        return find_stroke_set_root(stroke_set, prev_strokes[0], done)
    else:
        return None


def combine_strokes(strokes):
    stroke_set = {}

    for stroke in strokes:
        # if the last position is near the first position of another stroke...
        first = stroke.points[0].co
        last = stroke.points[-1].co
        next_strokes = []
        prev_strokes = []
        stroke_set[stroke] = [next_strokes, prev_strokes]
        for s in strokes:
            if s != stroke:
                if (s.points[0].co - last).length < STROKE_JOIN_THRESHOLD:
                    next_strokes.append(s)
                if (s.points[-1].co - first).length < STROKE_JOIN_THRESHOLD:
                    prev_strokes.append(s)

    stroke_roots = set()
    for stroke in strokes:
        root = find_stroke_set_root(stroke_set, stroke, [])
        if root:
            stroke_roots.add(root)

    return stroke_set, stroke_roots


def stroke_root_to_loop(stroke_set, stroke, loop : list):
    next_strokes, prev_strokes = stroke_set[stroke]
    for p in stroke.points:
        loop.append(p.co)
    if next_strokes:
        stroke_root_to_loop(stroke_set, next_strokes[0], loop)


def subdivide_loop(loop):
    subd = []
    for i in range(0, len(loop) - 1):
        l0 = loop[i]
        l2 = loop[i + 1]
        l1 = (l0 + l2) * 0.5
        subd.append(l0)
        subd.append(l1)
    subd.append(loop[-1])
    loop.clear()
    for co in subd:
        loop.append(co)


def generate_smoothed_loop_levels(loop, strength = 1.0, max_iterations = 10):
    """Returns a dictionary { iteration_level: smoothed_loop, ... } of loops smoothed by iteration level (0 to max_iterations+1)"""
    smoothed_levels = {}
    for i in range(0, max_iterations + 1):
        smooth_level = loop.copy()
        smoothed_levels[i] = smooth_level
        if i > 0:
            for l in range(1, len(loop)-1):
                smoothed = (loop[l - 1] + loop[l] + loop[l + 1]) / 3.0
                original = loop[l]
                smooth_level[l] = (smoothed - original) * strength + original
        loop = smooth_level
    return smoothed_levels


def grease_pencil_to_length_loops(bone_length):
    current_frame = bpy.context.scene.frame_current

    grease_pencil_layer = get_active_grease_pencil_layer()
    if not grease_pencil_layer:
        return

    frame = grease_pencil_layer.active_frame
    stroke_set, stroke_roots = combine_strokes(frame.strokes)

    loops = []
    for root in stroke_roots:
        loop = []
        stroke_root_to_loop(stroke_set, root, loop)
        if len(loop) > 1 and loop_length(loop) >= bone_length / 2:
            while(len(loop) < 25):
                subdivide_loop(loop)
            loops.append(loop)

    return loops


def grease_pencil_to_bones(chr_cache, arm, parent_mode, bone_length = 0.05,
                           skip_length = 0.0, trunc_length = 0.0, smooth_level = 0):
    props = vars.props()

    grease_pencil_layer = get_active_grease_pencil_layer()
    if not grease_pencil_layer:
        return

    # turn off grease pencil on current object / mode (including object mode)
    # (this is expected to be object mode on a hair mesh)
    tool_idname = utils.get_current_tool_idname(bpy.context)
    if "builtin.annotate" in tool_idname:
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        mode = utils.get_mode()
        if mode != "OBJECT":
            utils.object_mode()
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    #mode_selection = utils.store_mode_selection_state()
    arm_pose = set_rest_pose(arm)

    springbones.realign_spring_bones_axis(chr_cache, arm)

    springbones.show_spring_bone_edit_layer(chr_cache, arm, True)

    hair_bone_prefix = props.hair_rig_group_name

    # check root bone exists...
    anchor_bone_name = springbones.get_spring_anchor_name(chr_cache, arm, parent_mode)
    anchor_bone = bones.get_pose_bone(arm, anchor_bone_name)

    if anchor_bone:
        loops = grease_pencil_to_length_loops(bone_length)
        utils.edit_mode_to(arm)
        smoothed_loops_set = get_smoothed_loops_set(loops)
        remove_existing_loop_bones(chr_cache, arm, smoothed_loops_set)
        for edit_bone in arm.data.edit_bones:
            edit_bone.select_head = False
            edit_bone.select_tail = False
            edit_bone.select = False
        loop_index = 1
        new_bones = []
        for smoothed_loop in smoothed_loops_set:
            loop = smoothed_loop[smooth_level]
            loop_index = find_unused_hair_bone_index(arm, loop_index, hair_bone_prefix)
            if loop_to_bones(chr_cache, arm, parent_mode, loop, loop_index,
                             bone_length, skip_length, trunc_length, smooth_level, new_bones):
                loop_index += 1

    remove_duplicate_bones(chr_cache, arm)

    utils.object_mode_to(arm)
    # turn OFF grease pencil on armature : object mode
    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

    restore_pose(arm, arm_pose)
    #utils.restore_mode_selection_state(mode_selection)
    utils.edit_mode_to(arm)
    # turn ON grease pencil on armature : edit mode
    # (hopefully at this point grease pencil will only be on the armature in edit mode)
    bpy.ops.wm.tool_set_by_id(name="builtin.annotate")


def get_active_grease_pencil_layer():
    #current_frame = bpy.context.scene.frame_current
    #note_layer = bpy.data.grease_pencils['Annotations'].layers.active
    #frame = note_layer.active_frame
    try:
        return bpy.context.scene.grease_pencil.layers.active
    except:
        return None


def clear_grease_pencil():
    active_layer = get_active_grease_pencil_layer()
    if active_layer:
        active_layer.active_frame.clear()


def add_custom_bone(chr_cache, arm, parent_mode, bone_length = 0.05, skip_length = 0.0):
    props = vars.props()

    arm_pose = set_rest_pose(arm)

    springbones.realign_spring_bones_axis(chr_cache, arm)

    springbones.show_spring_bone_edit_layer(chr_cache, arm, True)

    hair_bone_prefix = props.hair_rig_group_name

    # check root bone exists...
    anchor_bone_name = springbones.get_spring_anchor_name(chr_cache, arm, parent_mode)
    anchor_bone = bones.get_pose_bone(arm, anchor_bone_name)

    if anchor_bone:
        utils.edit_mode_to(arm)
        for edit_bone in arm.data.edit_bones:
            edit_bone.select_head = False
            edit_bone.select_tail = False
            edit_bone.select = False
        loop_index = 1
        new_bones = []
        loop_index = find_unused_hair_bone_index(arm, loop_index, hair_bone_prefix)
        if custom_bone(chr_cache, arm, parent_mode, loop_index, bone_length, new_bones):
            loop_index += 1

    utils.object_mode_to(arm)
    restore_pose(arm, arm_pose)

    remove_duplicate_bones(chr_cache, arm)

    utils.edit_mode_to(arm)


def bind_cards_to_bones(chr_cache, arm, objects, card_dirs,
                        max_radius, max_bones, max_weight,
                        curve, variance, existing_scale,
                        card_mode, bone_mode, smoothing, parent_mode):

    utils.object_mode_to(arm)
    set_rest_pose(arm)
    remove_duplicate_bones(chr_cache, arm)

    springbones.realign_spring_bones_axis(chr_cache, arm)

    bone_chain_defs = get_bone_chain_defs(chr_cache, arm, bone_mode, parent_mode)
    all_spring_bone_names = get_all_spring_bone_names(chr_cache, arm)

    if bone_chain_defs:

        hair_bones = []
        for bone_chain in bone_chain_defs:
            for bone_def in bone_chain:
                hair_bones.append(bone_def["name"])

        # if no meshes selected, get a list of all hair objects
        if not objects:
            objects = []
            chr_objects = chr_cache.get_cache_objects()
            for obj in chr_objects:
                obj_cache = chr_cache.get_object_cache(obj)
                if obj_cache and not obj_cache.disabled and obj not in objects:
                    for mat in obj.data.materials:
                        mat_cache = chr_cache.get_material_cache(mat)
                        if mat_cache and mat_cache.material_type == "HAIR":
                            objects.append(obj)
                            break

        for obj in objects:
            # ensure an armature modifier with this armature (otherwise weight smooth fails)
            arm_mod = modifiers.get_armature_modifier(obj, create=True, armature=arm)
            #
            remove_hair_bone_weights(obj, hair_bones, card_mode)
            cards, bm = selected_cards_to_length_loops(chr_cache, obj, card_dirs,
                                                    one_loop_per_card=True, card_selection_mode=card_mode)
            scale_existing_weights(obj, bm, existing_scale, all_spring_bone_names)
            assign_bones(obj, bm, cards, bone_chain_defs, max_radius, max_bones, max_weight, curve, variance)
            bm.to_mesh(obj.data)

            smooth_hair_bone_weights(arm, obj, bone_chain_defs, smoothing)

    else:

        utils.log_error("No bones selected!")

    arm.data.pose_position = "POSE"
    utils.pose_mode_to(arm)


def deselect_invalid_materials(chr_cache, obj):
    """Mesh polygon selection only works in OBJECT mode"""
    if utils.object_exists_is_mesh(obj):
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None: continue
            mat_cache = chr_cache.get_material_cache(mat)
            if mat_cache:
                if mat_cache.material_type == "SCALP":
                    meshutils.select_material_faces(obj, mat, False)


def set_rest_pose(arm):
    arm_pose = arm.data.pose_position
    arm.data.pose_position = "REST"
    return arm_pose


def restore_pose(arm, arm_pose):
    arm.data.pose_position = arm_pose


class CC3OperatorHair(bpy.types.Operator):
    """Hair Spring Rigging"""
    bl_idname = "cc3.hair"
    bl_label = "Hair Spring Rigging"
    #bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):
        props = vars.props()
        prefs = vars.prefs()

        mode_selection = utils.store_mode_selection_state()

        chr_cache = props.get_context_character_cache(context)

        if not chr_cache:
            self.report({"ERROR"}, "No current character!")
            return {"FINISHED"}

        arm = chr_cache.get_armature()
        hair_mesh = utils.get_selected_mesh()

        if self.param == "CARDS_TO_CURVES":

            if hair_mesh:
                selected_cards_to_curves(chr_cache, utils.get_active_object(),
                                         props.hair_dir_vectors(),
                                         one_loop_per_card = props.hair_curve_merge_loops == "MERGE")

        if self.param == "ADD_BONES":

            if arm and hair_mesh:
                utils.unhide(arm)
                selected_cards_to_bones(chr_cache, arm,
                                        hair_mesh,
                                        props.hair_rig_bone_root,
                                        props.hair_dir_vectors(),
                                        one_loop_per_card = True,
                                        bone_length = props.hair_rig_bone_length / 100.0,
                                        skip_length = props.hair_rig_bind_skip_length / 100.0,
                                        trunc_length = props.hair_rig_bind_trunc_length / 100.0,
                                        smooth_level = props.hair_rig_bone_smoothing)
            else:
                self.report({"ERROR"}, "Active Object must be a mesh!")

        if self.param == "ADD_BONES_GREASE":

            if arm:
                utils.unhide(arm)
                grease_pencil_to_bones(chr_cache, arm, props.hair_rig_bone_root,
                                       bone_length = props.hair_rig_bone_length / 100.0,
                                       skip_length = props.hair_rig_bind_skip_length / 100.0,
                                       trunc_length = props.hair_rig_bind_trunc_length / 100.0,
                                       smooth_level = props.hair_rig_bone_smoothing)
            else:
                self.report({"ERROR"}, "Active Object be part of the character!")

        if self.param == "ADD_BONES_CUSTOM":

            if arm:
                utils.unhide(arm)
                add_custom_bone(chr_cache, arm, props.hair_rig_bone_root,
                                bone_length = props.hair_rig_bone_length / 100.0)

            else:
                self.report({"ERROR"}, "Active Object be part of the character!")

        if self.param == "REMOVE_HAIR_BONES":

            if arm:
                utils.unhide(arm)
                remove_hair_bones(chr_cache, arm,
                                  props.hair_rig_bind_bone_mode,
                                  props.hair_rig_bone_root)

                utils.restore_mode_selection_state(mode_selection)

        if self.param == "BIND_TO_BONES":

            objects = utils.get_selected_meshes(context)

            seed = props.hair_rig_bind_seed
            random.seed(seed)

            existing_scale = props.hair_rig_bind_existing_scale
            if props.hair_rig_target == "CC4":
                existing_scale = 0.0

            if arm and objects:
                utils.unhide(arm)
                bind_cards_to_bones(chr_cache, arm,
                                    objects,
                                    props.hair_dir_vectors(),
                                    props.hair_rig_bind_bone_radius / 100.0,
                                    props.hair_rig_bind_bone_count,
                                    props.hair_rig_bind_bone_weight,
                                    props.hair_rig_bind_weight_curve,
                                    props.hair_rig_bind_bone_variance,
                                    existing_scale,
                                    props.hair_rig_bind_card_mode,
                                    props.hair_rig_bind_bone_mode,
                                    props.hair_rig_bind_smoothing,
                                    props.hair_rig_bone_root)

                if props.hair_rig_target == "CC4":
                    #props.hair_rig_bind_existing_scale = 0.0

                    # for CC4 rigs, convert the hair meshes to accesories
                    springbones.convert_spring_rig_to_accessory(chr_cache, arm, props.hair_rig_bone_root)
                else:
                    #props.hair_rig_bind_existing_scale = 1.0
                    pass

            else:
                self.report({"ERROR"}, "Selected Object(s) to bind must be Meshes!")

        if self.param == "CLEAR_WEIGHTS":

            objects = utils.get_selected_meshes(context)

            if arm:
                utils.unhide(arm)
                clear_hair_bone_weights(chr_cache, arm, objects,
                                        props.hair_rig_bind_card_mode,
                                        props.hair_rig_bind_bone_mode,
                                        props.hair_rig_bone_root)
                utils.restore_mode_selection_state(mode_selection)

        if self.param == "CLEAR_GREASE_PENCIL":

            clear_grease_pencil()

        if self.param == "MAKE_ACCESSORY":

            objects = utils.get_selected_meshes(context)

            if arm and objects:
                utils.unhide(arm)
                springbones.convert_spring_rig_to_accessory(chr_cache, arm, props.hair_rig_bone_root)

        if self.param == "GROUP_NAME_BONES":

            group_name = props.hair_rig_group_name
            parent_mode = props.hair_rig_bone_root

            objects = utils.get_selected_meshes(context)
            if arm:
                utils.unhide(arm)
                rename_hair_bones(chr_cache, arm, group_name, parent_mode)

            utils.restore_mode_selection_state(mode_selection)

        if self.param == "SPRING_BONES_TOGGLE":
            if arm:
                springbones.show_spring_bone_edit_layer(chr_cache, arm, False)

        if self.param == "SPRING_BONES_SHOW":
            if arm:
                springbones.show_spring_bone_edit_layer(chr_cache, arm, True)

        if self.param == "ARMATURE_SHOW_POSE":
            if arm:
                arm.data.pose_position = "POSE"

        if self.param == "ARMATURE_SHOW_REST":
            if arm:
                arm.data.pose_position = "REST"

        if self.param == "CYCLE_BONE_STYLE":
            if arm:
                if arm.data.display_type == 'WIRE':
                    arm.data.display_type = 'OCTAHEDRAL'
                    arm.display_type = 'SOLID'
                elif arm.data.display_type == 'OCTAHEDRAL' and arm.display_type == 'SOLID':
                    arm.data.display_type = 'OCTAHEDRAL'
                    arm.display_type = 'WIRE'
                elif arm.data.display_type == 'OCTAHEDRAL' and arm.display_type == 'WIRE':
                    arm.data.display_type = 'STICK'
                    arm.display_type = 'SOLID'
                elif arm.data.display_type == 'STICK':
                    arm.data.display_type = 'WIRE'
                    arm.display_type = 'SOLID'
                else:
                    arm.data.display_type = 'OCTAHEDRAL'
                    arm.display_type = 'SOLID'

        if self.param == "TOGGLE_GREASE_PENCIL":
            tool_idname = utils.get_current_tool_idname(context)
            if "builtin.annotate" in tool_idname:
                mode = utils.get_mode()
                if mode != "OBJECT":
                    utils.object_mode()
                    bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                    utils.set_mode(mode)
                bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
                if arm:
                    arm.data.pose_position = "POSE"
            else:
                mode = utils.get_mode()
                if mode != "OBJECT":
                    utils.object_mode()
                    bpy.ops.wm.tool_set_by_id(name="builtin.annotate")
                    utils.set_mode(mode)
                bpy.ops.wm.tool_set_by_id(name="builtin.annotate")
                bpy.context.scene.tool_settings.annotation_stroke_placement_view3d = 'SURFACE'
                try:
                    props = bpy.context.workspace.tools["builtin.annotate"].operator_properties("gpencil.annotate")
                    props.use_stabilizer = True
                except:
                    pass
                # only use rest position to draw grease pencil on surface of hair
                if arm:
                    arm.data.pose_position = "REST"

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):
        props = vars.props()

        if properties.param == "ADD_BONES":
            return "Add bones to the hair rig, generated from the selected hair cards in the active mesh"
        elif properties.param == "ADD_BONES_CUSTOM":
            return "Add a single custom bone to the hair rig"
        elif properties.param == "ADD_BONES_GREASE":
            return "Add bones generated from grease pencil lines drawn in the current annotation layer.\n\n" \
                   "Note: For best results draw lines onto the hair in Surface placement mode."
        elif properties.param == "REMOVE_HAIR_BONES":
                if props.hair_rig_bind_bone_mode == "ALL":
                    return "Remove all bones from the hair rig.\n\n" \
                           "All associated vertex weights will also be removed from the hair meshes"
                else:
                    return "Remove only the selected bones from the hair rig.\n\n" \
                           "The vertex weights for the removed bones will also be removed from the hair meshes\n\n" \
                           "Note: Selecting any bone in a chain will use the entire chain of bones"
        elif properties.param == "BIND_TO_BONES":
            if props.hair_rig_bind_card_mode == "ALL":
                if props.hair_rig_bind_bone_mode == "ALL":
                    return "Bind the selected hair meshes to all of the hair rig bones.\n\n" \
                           "If no meshes are selected then *all* meshes in the character will be considered"
                else:
                    return "Bind the selected hair meshes to only the selected hair rig bones.\n\n" \
                           "If no meshes are selected then *all* meshes in the character will be considered.\n\n" \
                           "Note: Selecting any bone in a chain will use the entire chain of bones"
            else:
                if props.hair_rig_bind_bone_mode == "ALL":
                    return "Bind only the selected hair cards in the selected hair meshes to all of the hair rig bones.\n\n" \
                           "If no meshes are selected then *all* meshes in the character will be considered.\n\n" \
                           "Note: Selecting any part of a hair card will use the entire card island"
                else:
                    return "Bind only the selected hair cards in the selected hair meshes to only the selected hair rig bones.\n\n" \
                           "If no meshes are selected then *all* meshes in the character will be considered.\n\n" \
                           "Note: Selecting any bone in a chain will use the entire chain of bones and selecting any part of a hair card will select the whole har card island"
        elif properties.param == "CLEAR_WEIGHTS":
            if props.hair_rig_bind_card_mode == "ALL":
                if props.hair_rig_bind_bone_mode == "ALL":
                    return "Clear all the hair rig bone vertex weights from the selected hair meshes.\n\n" \
                           "If no meshes are selected then *all* meshes in the character will be considered"
                else:
                    return "Clear only the selected hair rig bone vertex weights from the selected hair meshes.\n\n" \
                           "If no meshes are selected then *all* meshes in the character will be considered.\n\n" \
                           "Note: Selecting any bone in a chain will use the entire chain of bones"
            else:
                if props.hair_rig_bind_bone_mode == "ALL":
                    return "Clear all the hair rig bone vertex weights from only the selected hair cards in the selected meshes.\n\n" \
                           "If no meshes are selected then *all* meshes in the character will be considered.\n\n" \
                           "Note: Selecting any part of a hair card will select the whole har card island"
                else:
                    return "Clear only the selected hair rig bone vertex weights from only the selected hair cards in the selected meshes.\n\n" \
                           "If no meshes are selected then *all* meshes in the character will be considered.\n\n" \
                           "Note: Selecting any bone in a chain will use the entire chain of bones and selecting any part of a hair card will select the whole har card island"

        elif properties.param == "CLEAR_GREASE_PENCIL":
            return "Remove all grease pencil lines from the current annotation layer"
        elif properties.param == "CARDS_TO_CURVES":
            return "Convert all the hair cards into curves"
        elif properties.param == "MAKE_ACCESSORY":
            return "Removes all none hair rig vertex groups from objects so that CC4 recognizes them as accessories and not cloth or hair.\n\n" \
                   "Accessories are categorized by:\n" \
                   "    1. A bone representing the accessory parented to a CC Base bone.\n" \
                   "    2. Child accessory deformation bone(s) parented to the accessory bone in 1.\n" \
                   "    3. Object(s) with vertex weights to ONLY these accessory deformation bones in 2.\n" \
                   "    4. All vertices in the accessory must be weighted"

        elif properties.param == "GROUP_NAME_BONES":
            return "Rename the bones in the selected chain so they all belong to the same group name"

        elif properties.param == "TOGGLE_GREASE_PENCIL":
            return "Quick toggle grease pencil mode with surface draw and stabilze stroke"

        elif properties.param == "CYCLE_BONE_STYLE":
            return "Cycle through armature bone styles"

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
        props = vars.props()
        prefs = vars.prefs()

        objects = bpy.context.selected_objects.copy()
        chr_cache = props.get_character_cache_from_objects(objects, True)

        export_blender_hair(self, chr_cache, objects, self.filepath)

        return {"FINISHED"}


    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


    @classmethod
    def description(cls, context, properties):
        return "Export the hair curves to Alembic."
