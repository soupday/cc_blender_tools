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

import bpy, bmesh, bpy_extras.mesh_utils
import os, math
from mathutils import Vector
from . import utils, jsonutils


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


def get_selected_islands(obj):

    utils.edit_mode_to(obj, only_this=True)
    bpy.ops.mesh.select_linked(delimit={'UV'})
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

    utils.object_mode_to(obj)

    mesh = obj.data
    island = []
    for i in range(0, len(mesh.polygons)):
        if mesh.polygons[i].select:
            island.append(i)
    #island = [ i for i, poly in mesh.polygons if poly.select ]

    utils.edit_mode_to(obj, only_this=True)
    bpy.ops.mesh.select_all(action="DESELECT")

    utils.object_mode_to(obj)

    return [ island ]



DIR_THRESHOLD = 0.8


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


def parse_island(bm, face_index, faces_left, island, face_map, vert_map):
    if face_index in faces_left:
        faces_left.remove(face_index)
        island.append(face_index)
        for uv_id in face_map[face_index]:
            connected_faces = vert_map[uv_id]
            if connected_faces:
                for cf in connected_faces:
                    parse_island(bm, cf, faces_left, island, face_map, vert_map)


def get_selected_islands(bm, ul):
    face_map = {}
    vert_map = {}
    uv_map = {}

    selected_faces = [f for f in bm.faces if f.select]

    for face in selected_faces:
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
        parse_island(bm, face_index, faces_left, current_island, face_map, vert_map)
        islands.append(current_island)

    return islands, uv_map


def get_aligned_edges(bm, island, dir, uv_map):
    edge : bmesh.types.BMEdge
    face : bmesh.types.BMFace

    edges = set()

    for i in island:
        face = bm.faces[i]
        for edge in face.edges:
            edges.add(edge.index)

    to_remove = []
    for e in edges:
        edge = bm.edges[e]
        uv0 = uv_map[edge.verts[0].index]
        uv1 = uv_map[edge.verts[1].index]
        V = Vector(uv1) - Vector(uv0)
        dot = dir.dot(V.normalized())
        if abs(dot) < DIR_THRESHOLD:
            to_remove.append(e)

    for e in to_remove:
        edges.remove(e)

    return edges


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
    if edge_index in edges_left:
        edges_left.remove(edge_index)
        edge = bm.edges[edge_index]
        loop.add(edge.verts[0].index)
        loop.add(edge.verts[1].index)
        if edge.index in edge_map:
            for ce in edge_map[edge.index]:
                parse_loop(bm, ce, edges_left, loop, edge_map)


def sort_func_u(vert_uv_pair):
    return vert_uv_pair[1].x


def sort_func_v(vert_uv_pair):
    return vert_uv_pair[1].y


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


def get_ordered_vertex_loops(obj, bm, edges, dir, uv_map, edge_map):
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


def merge_loops(loops):
    size = len(loops[0])

    for loop in loops:
        if len(loop) != size:
            return None

    num = len(loops)
    loop = []

    for i in range(0, size):
        co = Vector((0,0,0))
        for l in range(0, num):
            co += loops[l][i]
        co /= num
        loop.append(co)

    return loop


def selected_cards_to_loops(obj, card_dir : Vector, one_loop_per_card = True):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    # normalize card dir
    card_dir.normalize()

    # select linked and set to edge mode
    utils.edit_mode_to(obj, only_this=True)
    bpy.ops.mesh.select_linked(delimit={'UV'})
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')

    # object mode to save edit changes
    utils.object_mode_to(obj)

    # get the bmesh
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    ul = bm.loops.layers.uv[0]

    # get lists of the faces in each selected island
    islands, uv_map = get_selected_islands(bm, ul)

    utils.log_info(f"{len(islands)} islands selected.")

    all_loops = []

    for island in islands:

        utils.log_info(f"Processing island, faces: {len(island)}")
        utils.log_indent()

        # get all edges aligned with the card dir in the island
        edges = get_aligned_edges(bm, island, card_dir, uv_map)

        utils.log_info(f"{len(edges)} aligned edges.")

        # map connected edges
        edge_map = get_aligned_edge_map(bm, edges)

        # separate into ordered vertex loops
        loops = get_ordered_vertex_loops(obj, bm, edges, card_dir, uv_map, edge_map)

        utils.log_info(f"{len(loops)} ordered loops.")

        # (merge and) generate poly curves
        if one_loop_per_card:
            loop = merge_loops(loops)
            if loop:
                all_loops.append(loop)
            else:
                utils.log_info("Loops have differing lengths, skipping.")
        else:
            for loop in loops:
                all_loops.append(loop)

        utils.log_recess()

    return all_loops


def selected_cards_to_curves(obj, card_dir : Vector, one_loop_per_card = True):
    curve = create_curve()
    loops = selected_cards_to_loops(obj, card_dir, one_loop_per_card)
    for loop in loops:
        add_poly_spline(loop, curve)


class CC3OperatorHair(bpy.types.Operator):
    """Blender Hair Functions"""
    bl_idname = "cc3.hair"
    bl_label = "Blender Hair Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        if self.param == "TEST":
            selected_cards_to_curves(bpy.context.active_object, Vector((0, -1)), True)

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