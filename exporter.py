import os
import shutil

import bpy

from .utils import *
from .vars import *


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

        if self.param == "EXPORT_MORPH" or self.param == "EXPORT":
            export_anim = self.use_anim and self.param != "EXPORT_MORPH"
            props.import_file = self.filepath
            dir, name = os.path.split(self.filepath)
            type = name[-3:].lower()
            name = name[:-4]

            # store selection
            old_selection = bpy.context.selected_objects
            old_active = bpy.context.active_object

            if type == "fbx":

                # don't bring anything else with a morph export
                if self.param == "EXPORT_MORPH" and props.import_haskey:
                    bpy.ops.object.select_all(action='DESELECT')

                for p in props.import_objects:
                    if p.object is not None and p.object.type == "ARMATURE":
                        select_all_child_objects(p.object)

                bpy.ops.export_scene.fbx(filepath=self.filepath,
                        use_selection = True,
                        bake_anim = export_anim,
                        add_leaf_bones=False)

                if props.import_haskey:
                    try:
                        key_dir, key_file = os.path.split(props.import_key_file)
                        old_name, key_type = os.path.splitext(key_file)
                        new_key_path = os.path.join(dir, name + key_type)
                        shutil.copyfile(props.import_key_file, new_key_path)
                    except:
                        log_error("Unable to copy keyfile: " + props.import_key_file + " to: " + new_key_path)

            else:

                # don't bring anything else with a morph export
                if self.param == "EXPORT_MORPH" and props.import_haskey:
                    bpy.ops.object.select_all(action='DESELECT')

                # select all the imported objects
                for p in props.import_objects:
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

                if props.import_haskey:
                    try:
                        key_dir, key_file = os.path.split(props.import_key_file)
                        old_name, key_type = os.path.splitext(key_file)
                        new_key_path = os.path.join(dir, name + key_type)
                        shutil.copyfile(props.import_key_file, new_key_path)
                    except:
                        log_error("Unable to copy keyfile: " + props.import_key_file + "\n    to: " + new_key_path)

            # restore selection
            #bpy.ops.object.select_all(action='DESELECT')
            #for obj in old_selection:
            #    obj.select_set(True)
            #bpy.context.view_layer.objects.active = old_active

        elif self.param == "EXPORT_ACCESSORY":
            props.import_file = self.filepath
            dir, name = os.path.split(self.filepath)
            type = name[-3:].lower()
            name = name[:-4]

            # store selection
            old_selection = bpy.context.selected_objects
            old_active = bpy.context.active_object

            bpy.ops.export_scene.fbx(filepath=self.filepath,
                        use_selection = True,
                        bake_anim = False,
                        add_leaf_bones=False)

            # restore selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in old_selection:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = old_active


        return {"FINISHED"}

    def invoke(self, context, event):
        self.get_type()

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

    def get_type(self):
        props = bpy.context.scene.CC3ImportProps
        # export accessories as the same file type as imported
        if self.param == "EXPORT_ACCESSORY":
            self.filename_ext = "." + props.import_type
        # exporting for pipeline depends on what was imported...
        elif self.param == "EXPORT_MORPH" or self.param == "EXPORT":
            self.filename_ext = "." + props.import_type
        else:
            self.filename_ext = ".none"

    def check(self, context):
        change_ext = False
        filepath = self.filepath
        if os.path.basename(filepath):
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
