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

from . import bake, shaders, nodeutils, jsonutils, utils, params


def prep_export(chr_cache, new_name, objects, json_data, old_path, new_path):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if not chr_cache or not json_data:
        return None

    # if the old import dir path does not exist, try using the current blend file path instead.
    if not os.path.exists(old_path):
        old_path = utils.local_path("//")

    changes = []

    if new_name != chr_cache.import_name:
        # rename the object and character keys
        json_data[chr_cache.import_name]["Object"][new_name] = json_data[chr_cache.import_name]["Object"].pop(chr_cache.character_id)
        json_data[new_name] = json_data.pop(chr_cache.import_name)

    chr_json = json_data[new_name]["Object"][new_name]

    # get a list of all materials in the export back to CC3
    export_mats = []
    for obj in objects:
        if obj.type == "MESH":
            for mat in obj.data.materials:
                if mat and mat not in export_mats:
                    export_mats.append(mat)

    # get a use count of each material source name (stripped of any blender duplicate name suffixes)
    mat_count = {}
    for mat in export_mats:
        mat_name = mat.name
        mat_source_name = utils.strip_name(mat_name)
        if mat_source_name in mat_count.keys():
            mat_count[mat_source_name] += 1
        else:
            mat_count[mat_source_name] = 1

    # determine a single source of any duplicate material names, prefer an exact match
    mat_remap = {}
    for mat_source_name in mat_count.keys():
        count = mat_count[mat_source_name]
        if count > 1:
            for mat in export_mats:
                if mat.name == mat_source_name:
                    mat_remap[mat_source_name] = mat
                    break
                elif mat.name.startswith(mat_source_name):
                    mat_remap[mat_source_name] = mat

    obj : bpy.types.Object
    for obj in objects:
        obj_json = jsonutils.get_object_json(chr_json, obj)

        if obj_json and utils.still_exists(obj):

            if obj.type == "MESH":

                obj_name = obj.name
                mesh_name = obj.data.name
                obj_source_name = utils.strip_name(obj.name)

                if obj_name != obj_source_name or mesh_name != obj_source_name:
                    utils.log_info(f"Reverting object & mesh name: {obj_name} to {obj_source_name}")
                    obj.name = obj_source_name
                    obj.data.name = obj_source_name
                    changes.append(["OBJECT_RENAME", obj, obj_name, mesh_name])

                for slot in obj.material_slots:
                    mat = slot.material
                    mat_name = mat.name
                    mat_source_name = utils.strip_name(mat.name)
                    mat_json = jsonutils.get_material_json(obj_json, mat)
                    # update the json parameters with any changes
                    mat_cache = chr_cache.get_material_cache(mat)
                    if mat_cache:
                        if prefs.export_json_changes:
                            write_back_json(mat_json, mat, mat_cache)
                        if prefs.export_texture_changes:
                            write_back_textures(mat_json, mat, mat_cache, old_path)
                    # replace duplicate materials with a reference to a single source material
                    # (this is to ensure there are no duplicate suffixes in the fbx export)
                    if mat_count[mat_source_name] > 1:
                        new_mat = mat_remap[mat_source_name]
                        slot.material = new_mat
                        utils.log_info("Replacing material: " + mat.name + " with " + new_mat.name)
                        changes.append(["MATERIAL_SLOT_REPLACE", slot, mat])
                        mat = new_mat
                        mat_name = new_mat.name
                    # strip any blender numerical suffixes
                    if mat_name != mat_source_name:
                        utils.log_info(f"Reverting material name: {mat_name} to {mat_source_name}")
                        mat.name = mat_source_name
                        changes.append(["MATERIAL_RENAME", mat, mat_name])
                    # when saving the export to a new location, the texture paths need to point back to the
                    # original texture locations, either by new relative paths or absolute paths
                    # pbr textures:
                    for channel in mat_json["Textures"].keys():
                        remap_texture_path(mat_json["Textures"][channel], old_path, new_path)
                    # custom shader textures:
                    if "Custom Shader" in mat_json.keys():
                        for channel in mat_json["Custom Shader"]["Image"].keys():
                            remap_texture_path(mat_json["Custom Shader"]["Image"][channel], old_path, new_path)

        if prefs.export_bone_roll_fix:
            if obj.type == "ARMATURE":
                if utils.set_mode("OBJECT"):
                    utils.set_active_object(obj)
                    if utils.set_mode("EDIT"):
                        utils.log_info("Applying upper and lower teeth bones roll fix.")
                        bone = obj.data.edit_bones["CC_Base_Teeth01"]
                        bone.roll = 0
                        bone = obj.data.edit_bones["CC_Base_Teeth02"]
                        bone.roll = 0
                        utils.set_mode("OBJECT")

    # as the baking system can deselect everything, reselect the export objects here.
    utils.try_select_objects(objects, True)
    return changes


def remap_texture_path(tex_info, old_path, new_path):
    if os.path.normpath(old_path) != os.path.normpath(new_path):
        tex_path = tex_info["Texture Path"]
        abs_path = os.path.join(old_path, tex_path)
        rel_path = os.path.relpath(abs_path, new_path)
        tex_info["Texture Path"] = os.path.normpath(rel_path)
    return


def restore_export(export_changes : list):
    if not export_changes:
        return
    # undo everything prep_export did (in reverse order)...
    # (but don't bother with the json data as it is temporary)
    while export_changes:
        info = export_changes.pop()
        op = info[0]
        if op == "OBJECT_RENAME":
            obj = info[1]
            obj.name = info[2]
            obj.data.name = info[3]
        elif op == "MATERIAL_RENAME":
            mat = info[1]
            mat.name = info[2]
        elif op == "MATERIAL_SLOT_REPLACE":
            slot = info[1]
            slot.material = info[2]
    return


def get_prop_value(mat_cache, prop_name, default):
    parameters = mat_cache.parameters
    try:
        return eval("parameters." + prop_name, None, locals())
    except:
        return default


def write_back_json(mat_json, mat, mat_cache):
    shader_name = params.get_shader_lookup(mat_cache)
    shader_def = params.get_shader_def(shader_name)
    if shader_def:
        if "vars" in shader_def.keys():
            for var_def in shader_def["vars"]:
                prop_name = var_def[0]
                prop_default = var_def[1]
                func = var_def[2]
                if func == "":
                    args = var_def[3:]
                    json_var = args[0]
                    if json_var and json_var != "":
                        prop_value = get_prop_value(mat_cache, prop_name, prop_default)
                        jsonutils.set_material_json_var(mat_json, json_var, prop_value)

        if "export" in shader_def.keys():
            for export_def in shader_def["export"]:
                json_var = export_def[0]
                json_default = export_def[1]
                func = export_def[2]
                args = export_def[3:]
                json_value = shaders.eval_parameters_func(mat_cache.parameters, func, args, json_default)
                jsonutils.set_material_json_var(mat_json, json_var, json_value)


def write_back_textures(mat_json : dict, mat, mat_cache, old_path):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    shader_name = params.get_shader_lookup(mat_cache)
    shader_def = params.get_shader_def(shader_name)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader_name)
    has_custom_shader = "Custom Shader" in mat_json.keys()

    # determine if we are combining bump maps into normal maps:
    normal_socket = params.get_shader_texture_socket(shader_def, "NORMAL")
    bump_socket = params.get_shader_texture_socket(shader_def, "BUMP")
    normal_connected = normal_socket and nodeutils.has_connected_input(shader_node, normal_socket)
    bump_combining = normal_connected and bump_socket and nodeutils.has_connected_input(shader_node, bump_socket)
    if not prefs.export_bake_bump_to_normal:
        bump_combining = False

    if shader_def and shader_node:

        if "textures" in shader_def.keys():

            for tex_def in shader_def["textures"]:
                tex_type = tex_def[2]
                shader_socket = tex_def[0]
                tex_id = params.get_texture_json_id(tex_type)
                is_pbr = tex_type in params.PBR_TYPES
                tex_node = nodeutils.get_node_connected_to_input(shader_node, shader_socket)

                tex_info = None

                if is_pbr:
                    if tex_id in mat_json["Textures"].keys():
                        tex_info = mat_json["Textures"][tex_id]
                    elif tex_node:
                        tex_info = params.JSON_PBR_TEX_INFO.copy()
                        location, rotation, scale = nodeutils.get_image_node_mapping(tex_node)
                        tex_info["Tiling"] = [scale[0], scale[1]]
                        tex_info["Offset"] = [location[0], location[1]]
                        mat_json["Textures"][tex_id] = tex_info

                elif has_custom_shader:
                    if tex_id in mat_json["Custom Shader"]["Image"].keys():
                        tex_info = mat_json["Custom Shader"]["Image"][tex_id]
                    elif tex_node:
                        tex_info = params.JSON_CUSTOM_TEX_INFO.copy()
                        mat_json["Custom Shader"]["Image"][tex_id] = tex_info

                # if bump and normal are connect and we are combining them, remove bump maps from the Json and don't process it:
                if tex_info and tex_type == "BUMP" and bump_combining:
                    tex_info = None
                    del mat_json["Textures"][tex_id]

                if tex_info:

                    if tex_node:
                        image : bpy.types.Image = None
                        if tex_node.type == "TEX_IMAGE":
                            if tex_type == "NORMAL" and bump_combining:
                                image = bake.bake_bump_and_normal(shader_node, bsdf_node, shader_socket, bump_socket, "Bump Strength", mat, tex_id, old_path)
                            else:
                                image = tex_node.image
                        elif prefs.export_bake_nodes:
                            # if something is connected to the shader socket but is not a texture image
                            # and baking is enabled: then bake the socket input into a texture for exporting:
                            if tex_type == "NORMAL" and bump_combining:
                                image = bake.bake_bump_and_normal(shader_node, bsdf_node, shader_socket, bump_socket, "Bump Strength", mat, tex_id, old_path)
                            else:
                                image = bake.bake_socket_input(shader_node, shader_socket, mat, tex_id, old_path)
                        if image:
                            image_path = bpy.path.abspath(image.filepath)
                            rel_path = os.path.normpath(os.path.relpath(image_path, old_path))
                            if os.path.normpath(tex_info["Texture Path"]) != rel_path:
                                utils.log_info(mat.name + "/" + tex_id + ": Using new texture path: " + rel_path)
                                tex_info["Texture Path"] = rel_path


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

        if self.param == "EXPORT_CC3":
            export_anim = False
            dir, name = os.path.split(self.filepath)
            type = name[-3:].lower()
            name = name[:-4]

            # store selection
            old_selection = bpy.context.selected_objects
            old_active = bpy.context.active_object

            if type == "fbx":

                json_data = chr_cache.get_json_data()

                # select all the objects in the character (or try to)
                for p in chr_cache.object_cache:
                    if utils.still_exists(p.object):
                        if p.object.type == "ARMATURE":
                            p.object.hide_set(False)
                            utils.try_select_child_objects(p.object)
                        else:
                            p.object.hide_set(False)
                            utils.try_select_object(p.object)

                export_changes = prep_export(chr_cache, name, bpy.context.selected_objects, json_data, chr_cache.import_dir, dir)

                bpy.ops.export_scene.fbx(filepath=self.filepath,
                        use_selection = True,
                        bake_anim = export_anim,
                        add_leaf_bones = False,
                        use_mesh_modifiers = False)

                if chr_cache.import_has_key:
                    try:
                        old_key_path = chr_cache.import_key_file
                        if not os.path.exists(old_key_path):
                            old_key_path = utils.local_path(chr_cache.import_name + ".fbxkey")
                        if os.path.exists(old_key_path):
                            key_dir, key_file = os.path.split(old_key_path)
                            old_name, key_type = os.path.splitext(key_file)
                            new_key_path = os.path.join(dir, name + key_type)
                            if not utils.is_same_path(new_key_path, old_key_path):
                                shutil.copyfile(old_key_path, new_key_path)
                    except Exception as e:
                        utils.log_error("Unable to copy keyfile: " + old_key_path + " to: " + new_key_path, e)

                if json_data:
                    new_json_path = os.path.join(dir, name + ".json")
                    jsonutils.write_json(json_data, new_json_path)

                restore_export(export_changes)

            else:

                # don't bring anything else with an obj morph export
                bpy.ops.object.select_all(action='DESELECT')

                # select all the imported objects (should be just one)
                for p in chr_cache.object_cache:
                    if p.object is not None and p.object.type == "MESH":
                        p.object.hide_set(False)
                        p.object.select_set(True)

                bpy.ops.export_scene.obj(filepath=self.filepath,
                    use_selection = True,
                    global_scale = 100,
                    use_materials = False,
                    keep_vertex_order = True,
                    use_vertex_groups = True,
                    use_mesh_modifiers = False)

                # export options for full obj character
                #bpy.ops.export_scene.obj(filepath=self.filepath,
                #    use_selection = True,
                #    global_scale = 100,
                #    use_materials = True,
                #    keep_vertex_order = True,
                #    use_vertex_groups = True)

                if chr_cache.import_has_key:
                    try:
                        old_key_path = chr_cache.import_key_file
                        if not os.path.exists(old_key_path):
                            old_key_path = utils.local_path(chr_cache.import_name + ".ObjKey")
                        if os.path.exists(old_key_path):
                            key_dir, key_file = os.path.split(old_key_path)
                            old_name, key_type = os.path.splitext(key_file)
                            new_key_path = os.path.join(dir, name + key_type)
                            if not utils.is_same_path(new_key_path, old_key_path):
                                shutil.copyfile(old_key_path, new_key_path)
                    except Exception as e:
                        utils.log_error("Unable to copy keyfile: " + old_key_path + "\n    to: " + new_key_path, e)

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

        if properties.param == "EXPORT_CC3":
            return "Export full character to import back into CC3"
        elif properties.param == "EXPORT_ACCESSORY":
            return "Export selected object(s) for import into CC3 as accessories"
        return ""
