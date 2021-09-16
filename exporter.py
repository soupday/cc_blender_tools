# Copyright (C) 2021 Victor Soupday
# This file is part of CC3_Blender_Tools <https://github.com/soupday/cc3_blender_tools>
#
# CC3_Blender_Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CC3_Blender_Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CC3_Blender_Tools.  If not, see <https://www.gnu.org/licenses/>.

import os
import shutil

import bpy

from . import utils


class CC3Export(bpy.types.Operator):
    """Export CC3 Character"""
    bl_idname = "cc3.exporter"
    bl_label = "Export"
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        maxlen=1024,
        subtype='FILE_PATH',
        )

    filename_ext = ".fbx"  # ExportHelper mixin class uses this

    filter_glob: bpy.props.StringProperty(
        default="*.fbx;*.obj",
        options={"HIDDEN"},
        )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    use_anim: bpy.props.BoolProperty(name = "Export Animation", default = True)


    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        chr_cache = props.get_context_character_cache(context)

        if self.param == "EXPORT_MORPH" or self.param == "EXPORT":
            export_anim = self.use_anim and self.param != "EXPORT_MORPH"
            chr_cache.import_file = self.filepath
            dir, name = os.path.split(self.filepath)
            type = name[-3:].lower()
            name = name[:-4]

            # store selection
            old_selection = bpy.context.selected_objects
            old_active = bpy.context.active_object

            if type == "fbx":

                # don't bring anything else with a morph export
                if self.param == "EXPORT_MORPH" and chr_cache.import_has_key:
                    bpy.ops.object.select_all(action='DESELECT')

                for p in chr_cache.object_cache:
                    if p.object is not None:
                        if p.object.type == "ARMATURE":
                            utils.select_all_child_objects(p.object)
                        else:
                            p.object.select_set(True)

                bpy.ops.export_scene.fbx(filepath=self.filepath,
                        use_selection = True,
                        bake_anim = export_anim,
                        add_leaf_bones=False)

                if chr_cache.import_has_key:
                    try:
                        key_dir, key_file = os.path.split(chr_cache.import_key_file)
                        old_name, key_type = os.path.splitext(key_file)
                        new_key_path = os.path.join(dir, name + key_type)
                        if not utils.is_same_path(new_key_path, chr_cache.import_key_file):
                            shutil.copyfile(chr_cache.import_key_file, new_key_path)
                    except Exception as e:
                        utils.log_error("Unable to copy keyfile: " + chr_cache.import_key_file + " to: " + new_key_path, e)

            else:

                # don't bring anything else with a morph export
                if self.param == "EXPORT_MORPH" and chr_cache.import_has_key:
                    bpy.ops.object.select_all(action='DESELECT')

                # select all the imported objects
                for p in chr_cache.object_cache:
                    if p.object is not None and p.object.type == "MESH":
                        p.object.select_set(True)

                if self.param == "EXPORT_MORPH":
                    bpy.ops.export_scene.obj(filepath=self.filepath,
                            use_selection = True,
                            global_scale = 100,
                            use_materials = False,
                            keep_vertex_order = True,
                            use_vertex_groups = True)
                else:
                    bpy.ops.export_scene.obj(filepath=self.filepath,
                            use_selection = True,
                            global_scale = 100,
                            use_materials = True,
                            keep_vertex_order = True,
                            use_vertex_groups = True)

                if chr_cache.import_has_key:
                    try:
                        key_dir, key_file = os.path.split(chr_cache.import_key_file)
                        old_name, key_type = os.path.splitext(key_file)
                        new_key_path = os.path.join(dir, name + key_type)
                        if not utils.is_same_path(new_key_path, chr_cache.import_key_file):
                            shutil.copyfile(chr_cache.import_key_file, new_key_path)
                    except Exception as e:
                        utils.log_error("Unable to copy keyfile: " + chr_cache.import_key_file + "\n    to: " + new_key_path, e)

            # restore selection
            #bpy.ops.object.select_all(action='DESELECT')
            #for obj in old_selection:
            #    obj.select_set(True)
            #bpy.context.view_layer.objects.active = old_active

        elif self.param == "EXPORT_ACCESSORY":
            dir, name = os.path.split(self.filepath)
            type = name[-3:].lower()
            name = name[:-4]

            # store selection
            old_selection = bpy.context.selected_objects
            old_active = bpy.context.active_object

            if chr_cache.import_type == "fbx":
                bpy.ops.export_scene.fbx(filepath=self.filepath,
                        use_selection = True,
                        bake_anim = False,
                        add_leaf_bones=False)
            else:
                bpy.ops.export_scene.obj(filepath=self.filepath,
                        global_scale=100,
                        use_selection=True,
                        use_animation=False,
                        use_materials=True,
                        use_mesh_modifiers=True,
                        keep_vertex_order=True)

            # restore selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in old_selection:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = old_active


        return {"FINISHED"}


    def invoke(self, context, event):
        props = bpy.context.scene.CC3ImportProps
        chr_cache = props.get_context_character_cache(context)
        self.filename_ext = "." + chr_cache.import_type

        if self.filename_ext == ".none":
            return {"FINISHED"}

        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if not blend_filepath:
                if self.param == "EXPORT_ACCESSORY":
                    blend_filepath = "accessory"
                else:
                    blend_filepath = "untitled"
            else:
                blend_filepath = os.path.splitext(blend_filepath)[0]
            self.filepath = blend_filepath + self.filename_ext

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


    def check(self, context):
        change_ext = False
        filepath = self.filepath
        if os.path.basename(filepath):
            base, ext = os.path.splitext(filepath)
            if ext != self.filename_ext:
                filepath = bpy.path.ensure_ext(base, self.filename_ext)
            else:
                filepath = bpy.path.ensure_ext(filepath, self.filename_ext)
            if filepath != self.filepath:
                self.filepath = filepath
                change_ext = True
        return change_ext

    @classmethod
    def description(cls, context, properties):

        if properties.param == "EXPORT_MORPH":
            return "Export full character to import back into CC3"
        elif properties.param == "EXPORT_ACCESSORY":
            return "Export selected object(s) for import into CC3 as accessories"
        return ""
