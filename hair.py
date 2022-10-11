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
import os
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
                op.report({'ERROR'}, f"Curve: {obj.name} has no parent!")

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
                        name = obj.name
                        groups[name] = group
                        utils.log_info(f"Group: {name}, Object: {obj.name}")

            elif prefs.hair_export_group_by == "NAME":
                for obj in objects:
                    if obj.type == "CURVES" and obj.parent == parent:
                        name = utils.strip_name(obj.name)
                        if name not in groups.keys():
                            groups[name] = []
                        groups[name].append(obj)
                        utils.log_info(f"Group: {name}, Object: {obj.name}")

            else: #prefs.hair_export_group_by == "NONE":
                if "Hair" not in groups.keys():
                    groups["Hair"] = []
                for obj in objects:
                    if obj.type == "CURVES" and obj.parent == parent:
                        groups["Hair"].append(obj)
                        utils.log_info(f"Group: Hair, Object: {obj.name}")

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