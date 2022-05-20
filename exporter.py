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

import os
import copy
import shutil
import re

import bpy
from filecmp import cmp

from . import bake, shaders, rigging, bones, modifiers, nodeutils, jsonutils, utils, params, vars

UNPACK_INDEX = 1001


def check_valid_export_fbx(chr_cache, objects):

    report = []
    check_valid = True
    check_warn = False
    arm = utils.get_armature_in_objects(objects)

    if not arm:

        if chr_cache:
            message = f"ERROR: Character {chr_cache.character_name} has no armature!"
        else:
            message = f"ERROR: Character has no armature!"
        report.append(message)
        utils.log_warn(message)
        check_valid = False

    else:

        obj : bpy.types.Object
        for obj in objects:
            if obj != arm and utils.object_exists_is_mesh(obj):
                armature_mod : bpy.types.ArmatureModifier = modifiers.get_object_modifier(obj, "ARMATURE")
                if armature_mod is None:
                    message = f"ERROR: Object: {obj.name} does not have an armature modifier."
                    report.append(message)
                    utils.log_warn(message)
                    check_valid = False
                if obj.parent != arm:
                    message = f"ERROR: Object: {obj.name} is not parented to character armature."
                    report.append(message)
                    utils.log_warn(message)
                    check_valid = False
                if armature_mod and armature_mod.object != arm:
                    message = f"ERROR: Object: {obj.name}'s armature modifier is not set to this character's armature."
                    report.append(message)
                    utils.log_warn(message)
                    check_valid = False
                if len(obj.vertex_groups) == 0:
                    message = f"ERROR: Object: {obj.name} has no vertex groups."
                    report.append(message)
                    utils.log_warn(message)
                    check_valid = False
                if obj.type == "MESH" and obj.data and len(obj.data.vertices) < 150:
                    message = f"WARNING: Object: {obj.name} has a low number of vertices (less than 150), this is can cause CTD issues with CC3's importer."
                    report.append(message)
                    utils.log_warn(message)
                    message = f" (if CC3 crashes when importing this character, consider increasing vertex count or joining this object to another.)"
                    report.append(message)
                    utils.log_warn(message)
                    check_warn = True

    return check_valid, check_warn, report


def fix_for_pbr_export_name(name):
    return name.replace('.', '_').replace(' ', '_').replace('(', '_').replace(')', '_')


def remove_modifiers_for_export(chr_cache, objects, reset_pose):
    arm = utils.get_armature_in_objects(objects)
    arm.data.pose_position = "POSE"
    if reset_pose:
        utils.safe_set_action(arm, None)
        bones.clear_pose(arm)
    obj : bpy.types.Object
    for obj in objects:
        if chr_cache:
            obj_cache = chr_cache.get_object_cache(obj)
            if obj_cache:
                if obj_cache.object_type == "OCCLUSION" or obj_cache.object_type == "TEARLINE" or obj_cache.object_type == "EYE":
                    mod : bpy.types.Modifier
                    for mod in obj.modifiers:
                        if vars.NODE_PREFIX in mod.name:
                            obj.modifiers.remove(mod)


def restore_modifiers(chr_cache, objects):
    obj : bpy.types.Object
    for obj in objects:
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache:
            if obj_cache.object_type == "OCCLUSION":
                modifiers.add_eye_occlusion_modifiers(obj)
            elif obj_cache.object_type == "TEARLINE":
                modifiers.add_tearline_modifiers(obj)
            elif obj_cache.object_type == "EYE":
                modifiers.add_eye_modifiers(obj)


def rescale_for_unity(chr_cache, objects):
    """Do not use. Causes more problems than it solves..."""
    if utils.set_mode("OBJECT"):
        arm : bpy.types.Object = utils.get_armature_in_objects(objects)
        if arm.scale != 1.0:
            utils.try_select_object(arm, True)
            bpy.ops.object.transform_apply(location = False, rotation = False, scale = True, properties = False)
        object_list = []
        obj : bpy.types.Object
        for obj in objects:
            if obj.type == "MESH" and obj.scale != 1.0:
                object_list.append(obj)
        if len(object_list) > 0:
            utils.try_select_objects(object_list, True)
            bpy.ops.object.transform_apply(location = False, rotation = False, scale = True, properties = False)


def prep_export_cc3(chr_cache, new_name, objects, json_data, old_path, new_path):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if not chr_cache or not json_data:
        return None

    # if the old import dir path does not exist, try using the current blend file path instead.
    if not os.path.exists(old_path):
        old_path = utils.local_path("//")

    changes = []

    old_name = chr_cache.import_name
    if new_name != old_name:
        # rename the object and character keys
        json_data[old_name]["Object"][new_name] = json_data[old_name]["Object"].pop(chr_cache.character_id)
        json_data[new_name] = json_data.pop(old_name)

    chr_json = json_data[new_name]["Object"][new_name]

    # unpack embedded textures.
    if chr_cache.import_embedded:
        unpack_embedded_textures(chr_cache, chr_json, objects, old_path)

    # get a list of all cached materials in the export back to CC3
    export_mats = []
    for obj in objects:
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and obj.type == "MESH":
            for mat in obj.data.materials:
                mat_cache = chr_cache.get_material_cache(mat)
                if mat and mat_cache and mat not in export_mats:
                    export_mats.append(mat)

    # CC3 will replace any ' ' or '.' with underscores on export, so the only .00X suffix is from Blender
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
        obj_cache = chr_cache.get_object_cache(obj)
        obj_name = obj.name
        if obj_cache:
            obj_source_name = utils.strip_name(obj.name)
        else:
            obj_source_name = fix_for_pbr_export_name(obj.name)

        # if the name has been changed since it was cached, change it in the json
        cache_source_name = obj_source_name
        if obj_cache:
            cache_source_name = obj_cache.source_name
        if obj_source_name != cache_source_name:
            new_obj_name = obj_name.replace('.', '_')
            if cache_source_name in chr_json["Meshes"].keys():
                utils.log_info(f"Updating Object json name: {cache_source_name} to {new_obj_name}")
                chr_json["Meshes"][new_obj_name] = chr_json["Meshes"].pop(cache_source_name)
            changes.append(["OBJECT_RENAME", obj, obj.name, obj.data.name])
            obj.name = new_obj_name
            obj.data.name = new_obj_name
            obj_name = new_obj_name
            obj_source_name = new_obj_name

        # object name may have been changed by Blender (or may need to be changed for CC)
        mesh_name = obj.data.name
        if obj_name != obj_source_name or mesh_name != obj_source_name:
            utils.log_info(f"Reverting object & mesh name: {obj_name} to {obj_source_name}")
            obj.name = obj_source_name
            obj.data.name = obj_source_name
            changes.append(["OBJECT_RENAME", obj, obj_name, mesh_name])

        obj_json = jsonutils.get_object_json(chr_json, obj)

        # add blank object json data if user added mesh
        if not obj_json:
            utils.log_info(f"Adding Object Json: {obj_source_name}")
            obj_json = copy.deepcopy(params.JSON_MESH_DATA)
            chr_json["Meshes"][obj_source_name] = obj_json

        if obj_json and utils.object_exists_is_mesh(obj):

            for slot in obj.material_slots:
                mat = slot.material
                mat_name = mat.name
                mat_cache = chr_cache.get_material_cache(mat)
                mat_json = jsonutils.get_material_json(obj_json, mat)
                if mat_cache:
                    mat_source_name = utils.strip_name(mat.name)
                else:
                    mat_source_name = fix_for_pbr_export_name(mat.name)

                if mat_cache:
                    # if the name has been changed since it was cached, change it in the json
                    cache_source_name = None
                    if mat_cache:
                        cache_source_name = mat_cache.source_name
                    if not cache_source_name:
                        cache_source_name = mat_source_name
                    if mat_source_name != cache_source_name:
                        new_mat_name = mat_name.replace('.', '_')
                        if cache_source_name in obj_json["Materials"].keys():
                            utils.log_info(f"Updating material json name: {cache_source_name} to {new_mat_name}")
                            obj_json["Materials"][new_mat_name] = obj_json["Materials"].pop(cache_source_name)
                        changes.append(["MATERIAL_RENAME", mat, mat.name])
                        mat.name = new_mat_name
                        mat_name = new_mat_name
                        mat_source_name = new_mat_name

                    if mat_cache:
                        if mat_cache.user_added:
                            # add new material json data if user added
                            mat_json = copy.deepcopy(params.JSON_PBR_MATERIAL)
                            obj_json["Materials"][mat_source_name] = mat_json
                        if prefs.export_json_changes:
                            write_back_json(mat_json, mat, mat_cache)
                        if prefs.export_texture_changes:
                            write_back_textures(mat_json, mat, mat_cache, old_path, old_name, True)
                    if mat_json:
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
                else:
                    # add pbr material to json for non-cached base object/material
                    utils.log_info(f"Adding Material Json: {mat.name}")
                    if mat_source_name != mat.name:
                        utils.log_info(f"Updating Material name: {mat.name} to {mat_source_name}")
                        mat.name = mat_source_name
                        changes.append(["MATERIAL_RENAME", mat, mat.name])
                    mat_json = copy.deepcopy(params.JSON_PBR_MATERIAL)
                    obj_json["Materials"][mat.name] = mat_json
                    write_pbr_material_to_json(mat, mat_json, old_path, old_name, True)

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
        rel_path = utils.relpath(abs_path, new_path)
        tex_info["Texture Path"] = os.path.normpath(rel_path)
    return


def prep_export_unity(chr_cache, new_name, objects, json_data, old_path, new_path, as_blend_file):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    # remove everything not part of the character for blend file exports.
    if as_blend_file:
        arm = utils.get_armature_in_objects(objects)
        for obj in bpy.data.objects:
            if obj != arm and obj.parent != arm and not chr_cache.has_object(obj):
                bpy.data.objects.remove(obj)

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

    json_data[new_name]["Blender_Project"] = True

    # unpack embedded textures.
    if chr_cache.import_embedded:
        unpack_embedded_textures(chr_cache, chr_json, objects, old_path)

    obj : bpy.types.Object
    for obj in objects:
        obj_cache = chr_cache.get_object_cache(obj)
        obj_name = obj.name
        obj_source_name = utils.strip_name(obj.name)

        # if the name has been changed since it was cached, change it in the json
        cache_source_name = None
        if obj_cache:
            cache_source_name = obj_cache.source_name
        if not cache_source_name:
            cache_source_name = obj_source_name
        if obj_source_name != cache_source_name:
            new_obj_name = obj_name.replace('.', '_')
            if cache_source_name in chr_json["Meshes"].keys():
                utils.log_info(f"Updating Object json name: {cache_source_name} to {new_obj_name}")
                chr_json["Meshes"][new_obj_name] = chr_json["Meshes"].pop(cache_source_name)
            changes.append(["OBJECT_RENAME", obj, obj.name, obj.data.name])
            obj.name = new_obj_name
            obj.data.name = new_obj_name
            obj_name = new_obj_name
            obj_source_name = new_obj_name

        # object name may have been changed by Blender
        mesh_name = obj.data.name
        if obj_name != obj_source_name or mesh_name != obj_source_name:
            utils.log_info(f"Reverting object & mesh name: {obj_name} to {obj_source_name}")
            obj.name = obj_source_name
            obj.data.name = obj_source_name
            changes.append(["OBJECT_RENAME", obj, obj_name, mesh_name])

        obj_json = jsonutils.get_object_json(chr_json, obj)

        # add blank object json data if user added mesh
        if not obj_json or (obj_cache and obj_cache.user_added):
            obj_json = copy.deepcopy(params.JSON_MESH_DATA)
            chr_json["Meshes"][obj_source_name] = obj_json

        if obj_json and utils.object_exists_is_mesh(obj):

            for slot in obj.material_slots:
                mat = slot.material
                mat_name = mat.name
                mat_source_name = utils.strip_name(mat.name)
                mat_cache = chr_cache.get_material_cache(mat)

                # if the name has been changed since it was cached, change it in the json
                cache_source_name = None
                if mat_cache:
                    cache_source_name = mat_cache.source_name
                if not cache_source_name:
                    cache_source_name = mat_source_name
                if mat_source_name != cache_source_name:
                    new_mat_name = mat_name.replace('.', '_')
                    if cache_source_name in obj_json["Materials"].keys():
                        utils.log_info(f"Updating material json name: {cache_source_name} to {new_mat_name}")
                        obj_json["Materials"][new_mat_name] = obj_json["Materials"].pop(cache_source_name)
                    changes.append(["MATERIAL_RENAME", mat, mat.name])
                    mat.name = new_mat_name
                    mat_name = new_mat_name
                    mat_source_name = new_mat_name

                # if the material name has duplicate suffix, generate a new name and
                # update the json with the new name:
                if mat_name != mat_source_name:
                    utils.log_info(f"Removing blender duplication suffix from material: {mat_name}")
                    new_mat_name = utils.make_unique_name(mat_source_name, bpy.data.materials.keys())
                    if mat_source_name in obj_json["Materials"].keys():
                        utils.log_info(f"Updating material json name: {mat_source_name} to {new_mat_name}")
                        obj_json["Materials"][new_mat_name] = obj_json["Materials"].pop(mat_source_name)
                    mat.name = new_mat_name
                    mat_name = new_mat_name
                    mat_source_name = new_mat_name
                mat_json = None
                if mat_name in obj_json["Materials"]:
                    mat_json = obj_json["Materials"][mat_name]
                # update the json parameters with any changes
                if mat_cache:
                    if mat_cache.user_added:
                        # add new material json data if user added
                        mat_json = copy.deepcopy(params.JSON_PBR_MATERIAL)
                        obj_json["Materials"][mat_source_name] = mat_json
                    if prefs.export_json_changes:
                        write_back_json(mat_json, mat, mat_cache)
                    if prefs.export_texture_changes:
                        write_back_textures(mat_json, mat, mat_cache, old_path, chr_cache.import_name, True)
                if mat_json:
                    # when saving the export to a new location, the texture paths need to point back to the
                    # original texture locations, either by new relative paths or absolute paths
                    # pbr textures:
                    for channel in mat_json["Textures"].keys():
                        update_texture_path(mat_json["Textures"][channel], old_path, new_path, chr_cache.import_name, new_name, as_blend_file, mat_name)
                    # custom shader textures:
                    if "Custom Shader" in mat_json.keys():
                        for channel in mat_json["Custom Shader"]["Image"].keys():
                            update_texture_path(mat_json["Custom Shader"]["Image"][channel], old_path, new_path, chr_cache.import_name, new_name, as_blend_file, mat_name)

    # as the baking system can deselect everything, reselect the export objects here.
    utils.try_select_objects(objects, True)
    return changes


def update_texture_path(tex_info, old_path, new_path, old_name, new_name, as_blend_file, mat_name):
    """keep the same relative folder structure and copy the textures to their target folder.
       update the images in the blend file with the new location."""
    sep = os.path.sep
    old_tex_base = os.path.join(old_path, f"textures{sep}{old_name}")
    old_fbm_base = os.path.join(old_path, f"{old_name}.fbm")
    tex_path : str = tex_info["Texture Path"]
    if tex_path:
        old_abs_path = os.path.normpath(bpy.path.abspath(os.path.join(old_path, tex_path)))
        if utils.path_is_parent(old_tex_base, old_abs_path) or utils.path_is_parent(old_fbm_base, old_abs_path):
            # only remap the tex_path if it is inside the expected texture folders
            if old_name != new_name:
                tex_path = os.path.normpath(tex_path)
                tex_path = tex_path.replace(f"textures{sep}{old_name}{sep}{old_name}{sep}", f"textures{sep}{new_name}{sep}{new_name}{sep}")
                tex_path = tex_path.replace(f"textures{sep}{old_name}{sep}", f"textures{sep}{new_name}{sep}")
                tex_path = tex_path.replace(f"{old_name}.fbm{sep}", f"{new_name}.fbm{sep}")
                tex_info["Texture Path"] = tex_path
                utils.log_info("Updating Json texture path to: " + tex_path)
        else:
            # otherwise put the textures in folders in the textures/CHARACTER_NAME/extras/MATERIAL_NAME/ folder
            dir, file = os.path.split(tex_path)
            extras_dir = f"textures{sep}{new_name}{sep}Blender_Extras{sep}{mat_name}"
            tex_path = os.path.join(extras_dir, file)
            tex_info["Texture Path"] = tex_path
            utils.log_info("Texture outside character folders, updating Json texture path to: " + tex_path)

        new_abs_path = os.path.normpath(bpy.path.abspath(os.path.join(new_path, tex_path)))

        copy_file = False
        if os.path.exists(old_abs_path):
            if os.path.exists(new_abs_path):
                if not cmp(old_abs_path, new_abs_path):
                    copy_file = True
            else:
                copy_file = True

        if copy_file:
            # make sure path exists
            dir_path = os.path.dirname(new_abs_path)
            os.makedirs(dir_path, exist_ok=True)
            # copy the texture
            shutil.copyfile(old_abs_path, new_abs_path)
            image : bpy.types.Image

        # update images with changed file path (if it changed, and only if exporting as blend file)
        if as_blend_file:
            if os.path.normpath(old_abs_path) != os.path.normpath(new_abs_path):
                for image in bpy.data.images:
                    if image and image.filepath and os.path.samefile(bpy.path.abspath(image.filepath), old_abs_path):
                        utils.log_info(f"Updating image {image.name} filepath to: {new_abs_path}")
                        image.filepath = new_abs_path


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

    if mat_json is None:
        return

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


def write_back_textures(mat_json : dict, mat, mat_cache, old_path, old_name, bake_values):
    global UNPACK_INDEX
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if mat_json is None:
        return

    shader_name = params.get_shader_lookup(mat_cache)
    shader_def = params.get_shader_def(shader_name)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader_name)
    has_custom_shader = "Custom Shader" in mat_json.keys()
    unpack_path = os.path.join(old_path, "textures", old_name, "Unpack")
    bake_path = os.path.join(old_path, "textures", old_name, "Baked")
    bake.init_bake()
    UNPACK_INDEX = 1001

    # determine if we are combining bump maps into normal maps:
    normal_socket = params.get_shader_texture_socket(shader_def, "NORMAL")
    bump_socket = params.get_shader_texture_socket(shader_def, "BUMP")
    normal_connected = normal_socket and nodeutils.has_connected_input(shader_node, normal_socket)
    bump_combining = False
    if prefs.export_bake_bump_to_normal and prefs.export_bake_nodes:
        bump_combining = normal_connected and bump_socket and nodeutils.has_connected_input(shader_node, bump_socket)

    if shader_def and shader_node:

        if "textures" in shader_def.keys():

            for tex_def in shader_def["textures"]:
                tex_type = tex_def[2]
                shader_socket = tex_def[0]
                tex_id = params.get_texture_json_id(tex_type)
                is_pbr = tex_type in params.PBR_TYPES
                tex_node = nodeutils.get_node_connected_to_input(shader_node, shader_socket)

                tex_info = None
                bake_shader_output = False
                bake_shader_socket = ""
                bake_shader_size = 64

                # find or generate tex_info json.
                if is_pbr:
                    # CC3 cannot set metallic or roughness values with no texture, so must bake a small value texture
                    if not tex_node and prefs.export_bake_nodes:

                        if tex_type == "ROUGHNESS":
                            roughness = nodeutils.get_node_input(shader_node, "Roughness Map", 0)
                            roughness_min = nodeutils.get_node_input(shader_node, "Roughness Min", 0)
                            roughness_max = nodeutils.get_node_input(shader_node, "Roughness Max", 1)
                            roughness_pow = nodeutils.get_node_input(shader_node, "Roughness Power", 1)
                            if bake_values and (roughness_min > 0 or roughness_max < 1 or roughness_pow != 1.0 or roughness != 0.5):
                                bake_shader_output = True
                                bake_shader_socket = "Roughness"
                            elif not bake_values:
                                mat_json["Roughness_Value"] = roughness

                        elif tex_type == "METALLIC":
                            metallic = nodeutils.get_node_input(shader_node, "Metallic Map", 0)
                            if bake_values and metallic > 0:
                                bake_shader_output = True
                                bake_shader_socket = "Metallic"
                            elif not bake_values:
                                mat_json["Metallic_Value"] = metallic

                    if tex_id in mat_json["Textures"]:
                        tex_info = mat_json["Textures"][tex_id]

                    elif tex_node or bake_shader_output:
                        tex_info = copy.deepcopy(params.JSON_PBR_TEX_INFO)
                        location, rotation, scale = nodeutils.get_image_node_mapping(tex_node)
                        tex_info["Tiling"] = [scale[0], scale[1]]
                        tex_info["Offset"] = [location[0], location[1]]
                        mat_json["Textures"][tex_id] = tex_info
                        strength = 100
                        if mat_cache:
                            if tex_type == "NORMAL":
                                strength = int(mat_cache.parameters.default_normal_strength * 100)
                            elif tex_type == "BUMP":
                                strength = int(mat_cache.parameters.default_bump_strength * 200)
                        tex_info["Strength"] = strength

                elif has_custom_shader:
                    if tex_id in mat_json["Custom Shader"]["Image"]:
                        tex_info = mat_json["Custom Shader"]["Image"][tex_id]
                    elif tex_node:
                        tex_info = copy.deepcopy(params.JSON_CUSTOM_TEX_INFO)
                        mat_json["Custom Shader"]["Image"][tex_id] = tex_info

                # if bump and normal are connected and we are combining them,
                # remove bump maps from the Json and don't process it:
                if tex_info and tex_type == "BUMP" and bump_combining:
                    tex_info = None
                    del mat_json["Textures"][tex_id]

                if tex_info:

                    if tex_node or bake_shader_output:

                        image : bpy.types.Image = None

                        if bake_shader_output:
                            image = bake.bake_node_socket_input(bsdf_node, bake_shader_socket, mat, tex_id, bake_path, bake_shader_size)

                        elif tex_node and tex_node.type == "TEX_IMAGE":
                            if prefs.export_bake_nodes and tex_type == "NORMAL" and bump_combining:
                                image = bake.bake_rl_bump_and_normal(shader_node, bsdf_node, shader_socket, bump_socket, "Normal Strength", "Bump Strength", mat, tex_id, bake_path)
                            else:
                                image = tex_node.image

                        elif prefs.export_bake_nodes:
                            # if something is connected to the shader socket but is not a texture image
                            # and baking is enabled: then bake the socket input into a texture for exporting:
                            if tex_type == "NORMAL" and bump_combining:
                                image = bake.bake_rl_bump_and_normal(shader_node, bsdf_node, shader_socket, bump_socket, "Normal Strength", "Bump Strength", mat, tex_id, bake_path)
                                tex_info["Strength"] = 100
                            else:
                                image = bake.bake_node_socket_input(shader_node, shader_socket, mat, tex_id, bake_path)

                        if image:
                            try_unpack_image(image, unpack_path, True)
                            image_path = bpy.path.abspath(image.filepath)
                            rel_path = os.path.normpath(utils.relpath(image_path, old_path))
                            if os.path.normpath(tex_info["Texture Path"]) != rel_path:
                                utils.log_info(mat.name + "/" + tex_id + ": Using new texture path: " + rel_path)
                                tex_info["Texture Path"] = rel_path


def get_unique_path(path):
    if os.path.exists(path):
        dir, file = os.path.split(path)
        name, ext = os.path.splitext(file)
        index = 1001
        file = name + "_" + str(index) + ext
        path = os.path.join(dir, file)
        while os.path.exists(path):
            index += 1
            file = name + "_" + str(index) + ext
            path = os.path.join(dir, file)
    return path


def try_unpack_image(image, folder, index_suffix = False):
    global UNPACK_INDEX
    try:
        if image.packed_file:
            if image.filepath:
                temp_dir, name = os.path.split(bpy.path.abspath(image.filepath))
            else:
                name = image.name
                if image.file_format == "PNG":
                    name = name + ".png"
                elif image.file_format == "JPEG":
                    name = name + ".jpg"
                else:
                    name = name + "." + image.file_format.lower()
            if index_suffix:
                root, ext = os.path.splitext(name)
                name = root + "_" + str(UNPACK_INDEX) + ext
                UNPACK_INDEX += 1
            image_path = os.path.join(folder, name)
            utils.log_info(f"Unpacking image: {name}")
            if not os.path.exists(folder):
                os.makedirs(folder)
            image.unpack(method = "REMOVE")
            image.filepath_raw = image_path
            image.save()
            return True
    except:
        utils.log_warn(f"Unable to unpack image: {name}")
        return False


def unpack_embedded_textures(chr_cache, chr_json, objects, old_path):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    fbm_folder = os.path.join(chr_cache.import_dir, chr_cache.import_name + ".fbm")
    if not os.path.exists(fbm_folder):
        os.mkdir(fbm_folder)

    obj : bpy.types.Object
    for obj in objects:
        obj_json = jsonutils.get_object_json(chr_json, obj)

        if obj_json and utils.object_exists_is_mesh(obj):

            for slot in obj.material_slots:
                mat = slot.material
                mat_json = jsonutils.get_material_json(obj_json, mat)
                mat_cache = chr_cache.get_material_cache(mat)
                if mat_cache and mat_json:
                    for tex_mapping in mat_cache.texture_mappings:
                        image : bpy.types.Image = tex_mapping.image

                        if image:
                            try_unpack_image(image, fbm_folder)
                            image_path = bpy.path.abspath(image.filepath)

                            # fix the texture json data path:
                            try:
                                tex_type = tex_mapping.texture_type
                                tex_id = params.get_texture_json_id(tex_type)
                                if tex_id in mat_json["Textures"]:
                                    tex_info = mat_json["Textures"][tex_id]

                                    # the fbx importer will assign the diffuse alpha to the opacity channel, even if
                                    # there is an opacity texture present.
                                    # this means it will incorrectly set the opacity with the diffuse
                                    # though this will be corrected later by the texture write back,
                                    # if no write back this will be wrong, so remove the opacity Json data
                                    if not prefs.export_texture_changes:
                                        dir, name = os.path.split(image_path)
                                        if "_Diffuse" in name and tex_type == "ALPHA":
                                            utils.log_info(f"Diffuse connected to Alpha, removing Opacity data from Json.")
                                            del mat_json["Textures"][tex_id]
                                            tex_info = None

                                    if tex_info:
                                        tex_path = os.path.join(old_path, tex_info["Texture Path"])
                                        if not utils.is_same_path(tex_path, image_path):
                                            rel_path = os.path.normpath(utils.relpath(image_path, old_path))
                                            tex_info["Texture Path"] = rel_path
                                            utils.log_info(f"Updating embedded image Json data: {rel_path}")
                            except:
                                utils.log_warn(f"Unable to update embedded image Json: {image.name}")


def get_export_objects(chr_cache, include_selected = True):
    """Fetch all the objects in the character (or try to)"""
    objects = []
    if include_selected:
        objects = bpy.context.selected_objects.copy()
    if chr_cache:
        arm = chr_cache.get_armature()
        if arm:
            arm.hide_set(False)
            if arm not in objects:
                objects.append(arm)
            for obj_cache in chr_cache.object_cache:
                if utils.object_exists_is_mesh(obj_cache.object):
                    if obj_cache.object.parent == arm:
                        obj_cache.object.hide_set(False)
                        if obj_cache.object not in objects:
                            objects.append(obj_cache.object)
    else:
        for arm in bpy.context.selected_objects:
            if arm.type == "ARMATURE":
                arm.hide_set(False)
                if arm not in objects:
                    objects.append(arm)
                for obj in arm.children:
                    if utils.object_exists_is_mesh(obj): # and obj.visible_get():
                        if obj not in objects:
                            objects.append(obj)
                break
    return objects


def prep_non_standard_export(objects, dir, name, character_type):
    global UNPACK_INDEX
    bake.init_bake()
    UNPACK_INDEX = 5001

    changes = []

    generation = "Humanoid"
    if character_type == "CREATURE":
        generation = "Creature"
    elif character_type == "PROP":
        generation = "Prop"

    utils.log_info(f"Generation: {generation}")

    # prefer to bake and unpack textures next to blend file, otherwise at the destination.
    blend_path = bpy.path.abspath("//")
    if blend_path:
        dir = blend_path
    utils.log_info(f"Texture Root Dir: {dir}")

    json_data = {
        name: {
            "Version": "1.10.1822.1",
            "Scene": {
                "Name": True,
                "SupportShaderSelect": True
            },
            "Object": {
                name: {
                    "Generation": generation,
                    "Meshes": {
                    },
                },
            },
        }
    }

    #arm = utils.get_armature_in_objects(objects)
    #if arm:
    #    bones.reset_root_bone(arm)

    done = []
    objects_json = json_data[name]["Object"][name]["Meshes"]
    for obj in objects:
        if obj.type == "MESH" and obj not in done:
            done.append(obj)
            utils.log_info(f"Adding Object Json: {obj.name}")
            export_name = fix_for_pbr_export_name(obj.name)
            if export_name != obj.name:
                utils.log_info(f"Updating Object name: {obj.name} to {export_name}")
                obj.name = export_name
                changes.append(["OBJECT_RENAME", obj, obj.name])
            mesh_json = copy.deepcopy(params.JSON_MESH_DATA)
            objects_json[obj.name] = mesh_json
            for slot in obj.material_slots:
                mat = slot.material
                if mat not in done:
                    done.append(mat)
                    utils.log_info(f"Adding Material Json: {mat.name}")
                    export_name = fix_for_pbr_export_name(mat.name)
                    if export_name != mat.name:
                        utils.log_info(f"Updating Material name: {mat.name} to {export_name}")
                        mat.name = export_name
                        changes.append(["MATERIAL_RENAME", mat, mat.name])
                    mat_json = copy.deepcopy(params.JSON_PBR_MATERIAL)
                    mesh_json["Materials"][mat.name] = mat_json
                    write_pbr_material_to_json(mat, mat_json, dir, name, True)

    # select all the export objects
    utils.try_select_objects(objects, True)

    return json_data, changes

BSDF_TEXTURES = [
    ["Base Color", "BSDF", "Base Color"],
    ["Metallic", "BSDF", "Metallic"],
    ["Specular", "BSDF", "Specular"],
    ["Roughness", "BSDF", "Roughness"],
    ["Emission", "BSDF", "Glow"],
    ["Alpha", "BSDF", "Opacity"],
    ["Normal:Color", "BSDF", "Normal"],
    ["Normal:Normal:Color", "BSDF", "Normal"],
    ["Normal:Height", "BSDF", "Bump"],
    ["Occlusion", "GLTF", "AO"],
]

BSDF_TEXTURE_KEYWORDS = {
    "Base Color": ["basecolor", "diffuse", "albedo", "base color", "base colour", "basecolour", ".d$", "_d$"],
    "Metallic": ["metallic", "metal", "metalness", ".m$", "_m$"],
    "Specular": ["specular", "spec", "specmap", ".s$", "_s$"],
    "Roughness": ["roughness", "rough", ".r$", "_r$"],
    "Glow": ["emissive", "emission", "glow", "emit", ".e$", "_e$", ".g$", "_g$"],
    "Opacity": ["alpha", "opacity", ".a$", "_a$"],
    "Normal": ["normal", "nrm", ".n$", "_n$"],
    "Bump": ["bump", "height", ".b$", "_b$"],
    "AO": ["occlusion", "lightmap", "intensity", ".ao$", "_ao$"],
}

def write_pbr_material_to_json(mat, mat_json, path, name, bake_values):
    if not mat.node_tree or not mat.node_tree.nodes:
        return

    unpack_path = os.path.join(path, "textures", name, "Unpack")
    bake_path = os.path.join(path, "textures", name, "Baked")
    bsdf_node = nodeutils.get_bsdf_node(mat)
    gltf_node = nodeutils.find_node_group_by_keywords(mat.node_tree.nodes, "glTF Settings")

    if bsdf_node:
        try:
            roughness_value = bsdf_node.inputs["Roughness"].default_value
            metallic_value = bsdf_node.inputs["Metallic"].default_value
            bake_roughness = False
            bake_metallic = False
            specular_value = bsdf_node.inputs["Specular"].default_value
            diffuse_color = (1,1,1,1)
            alpha_value = 1.0
            if not bsdf_node.inputs["Base Color"].is_linked:
                diffuse_color = bsdf_node.inputs["Base Color"].default_value
            if not bsdf_node.inputs["Alpha"].is_linked:
                alpha_value = bsdf_node.inputs["Alpha"].default_value
            mat_json["Diffuse Color"] = jsonutils.convert_from_color(diffuse_color)
            mat_json["Specular Color"] = jsonutils.convert_from_color(
                        utils.linear_to_srgb((specular_value, specular_value, specular_value, 1.0))
                    )
            mat_json["Opacity"] = alpha_value
            if bake_values:
                if roughness_value != 0.5:
                    bake_roughness = True
                if metallic_value > 0:
                    bake_metallic = True
            elif not bake_values:
                mat_json["Roughness_Value"] = roughness_value
                mat_json["Metallic_Value"] = metallic_value
        except:
            utils.log_warn("Unable to set BSDF parameters!")

        socket_mapping = {}
        for socket_trace, node_type, tex_id in BSDF_TEXTURES:
            if node_type == "BSDF":
                n = bsdf_node
            elif node_type == "GLTF":
                n = gltf_node
            else:
                n = None
            if n:
                linked_node, linked_socket = nodeutils.trace_input_sockets(n, socket_trace)
                if linked_node and linked_socket:
                    socket_mapping[tex_id] = [linked_node, linked_socket, False]
                else:
                    if tex_id == "Roughness" and bake_roughness:
                        socket_mapping[tex_id] = [bsdf_node, "Roughness", True]
                    elif tex_id == "Metallic" and bake_metallic:
                        socket_mapping[tex_id] = [bsdf_node, "Metallic", True]


        write_or_bake_tex_data_to_json(socket_mapping, mat, mat_json, bsdf_node, bake_path, unpack_path)

    else:
        # if there is no BSDF shader node, try to match textures by name (both image node name and image name)
        socket_mapping = {}
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                for tex_id in BSDF_TEXTURE_KEYWORDS:
                    for key in BSDF_TEXTURE_KEYWORDS[tex_id]:
                        if re.match(key, node.image.name.lower()) or re.match(key, node.label.lower()) or re.match(key, node.name.lower()):
                            socket_mapping[tex_id] = [node, "Color", False]

        write_or_bake_tex_data_to_json(socket_mapping, mat, mat_json, None, bake_path, unpack_path)

    return


def write_or_bake_tex_data_to_json(socket_mapping, mat, mat_json, bsdf_node, bake_path, unpack_path):

    combine_normals = False
    if bsdf_node and "Normal" in socket_mapping and "Bump" in socket_mapping:
        combine_normals = True

    for tex_id in socket_mapping:

        # don't add bump maps if combining normals
        if combine_normals and tex_id == "Bump":
            continue

        # cc3/4 only supports one normal or bump, so favor the normal map
        if tex_id == "Bump" and "Normal" in socket_mapping:
            continue

        node, socket, bake_value = socket_mapping[tex_id]
        utils.log_info(f"Adding Texture Chennel: {tex_id}")

        tex_node = None
        image = None
        if node.type == "TEX_IMAGE":
            tex_node = node
            image = node.image
            try_unpack_image(image, unpack_path, True)
        else:
            if tex_id == "Normal" and combine_normals:
                image = bake.bake_bsdf_normal(bsdf_node, mat, tex_id, bake_path)
            else:
                if bake_value:
                    image = bake.bake_value_image(node.inputs[socket].default_value, mat, tex_id, bake_path)
                else:
                    image = bake.bake_node_socket_output(node, socket, mat, tex_id, bake_path)

        tex_info = copy.deepcopy(params.JSON_PBR_TEX_INFO)
        tex_info["Texture Path"] = bpy.path.abspath(image.filepath)
        if tex_node:
            location, rotation, scale = nodeutils.get_image_node_mapping(tex_node)
            tex_info["Tiling"] = [scale[0], scale[1]]
            tex_info["Offset"] = [location[0], location[1]]
        mat_json["Textures"][tex_id] = tex_info


def export_copy_fbx_key(chr_cache, dir, name):
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


def export_copy_obj_key(chr_cache, dir, name):
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


def is_arp_installed():
    try:
        bl_options = bpy.ops.id.arp_export_fbx_panel.bl_options
        if bl_options is not None:
            return True
        else:
            return False
    except:
        return False


def is_arp_rig(rig):
    if utils.object_exists_is_armature(rig):
        if "c_pos" in rig.data.bones and "c_traj" in rig.data.bones and "c_root.x" in rig.data.bones:
            print("ARP RIG")
            return True
    return False


def export_arp(file_path):
    try:
        if "arp_engine_type" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_engine_type = "unity"
        if "arp_export_rig_type" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_export_rig_type = "humanoid"
        if "arp_bake_anim" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_bake_anim = False
        if "arp_ge_sel_only" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_ge_sel_only = True
        if "arp_keep_bend_bones" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_keep_bend_bones = False
        if "arp_export_twist" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_export_twist = True
        if "arp_export_noparent" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_export_noparent = False
        if "arp_use_tspace" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_use_tspace = False
        if "arp_fix_fbx_rot" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_fix_fbx_rot = False
        if "arp_fix_fbx_matrix" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_fix_fbx_matrix = True
        if "arp_init_fbx_rot" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_init_fbx_rot = False
        if "arp_bone_axis_primary_export" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_bone_axis_primary_export = "Y"
        if "arp_bone_axis_secondary_export" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_bone_axis_secondary_export = "X"
        if "arp_export_rig_name" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_export_rig_name = "root"
        if "arp_export_tex" in bpy.data.scenes["Scene"]:
            bpy.data.scenes["Scene"].arp_export_tex = False

        bpy.ops.id.arp_export_fbx_panel(filepath=file_path, check_existing = False)
        return True
    except:
        return False


def export_standard(chr_cache, file_path):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Exporting Character Model to CC:")
    utils.log_info("--------------------------------")

    utils.set_mode("OBJECT")

    export_anim = False
    dir, name = os.path.split(file_path)
    type = name[-3:].lower()
    name = name[:-4]

    # store selection
    old_selection = bpy.context.selected_objects
    old_active = bpy.context.active_object

    if type == "fbx":

        json_data = chr_cache.get_json_data()

        objects = get_export_objects(chr_cache)

        utils.log_info("Preparing character for export:")
        utils.log_indent()

        remove_modifiers_for_export(chr_cache, objects, True)

        export_changes = prep_export_cc3(chr_cache, name, objects, json_data, chr_cache.import_dir, dir)

        bpy.ops.export_scene.fbx(filepath=file_path,
                use_selection = True,
                bake_anim = export_anim,
                add_leaf_bones = False,
                use_mesh_modifiers = True)

        utils.log_recess()
        utils.log_info("")
        utils.log_info("Copying Fbx Key.")

        export_copy_fbx_key(chr_cache, dir, name)

        utils.log_info("Writing Json Data.")

        if json_data:
            new_json_path = os.path.join(dir, name + ".json")
            jsonutils.write_json(json_data, new_json_path)

        restore_export(export_changes)

        restore_modifiers(chr_cache, objects)

    else:

        # don't bring anything else with an obj morph export
        bpy.ops.object.select_all(action='DESELECT')

        # select all the imported objects (should be just one)
        for p in chr_cache.object_cache:
            if p.object is not None and p.object.type == "MESH":
                p.object.hide_set(False)
                p.object.select_set(True)

        bpy.ops.export_scene.obj(filepath=file_path,
            use_selection = True,
            global_scale = 100,
            use_materials = False,
            keep_vertex_order = True,
            use_vertex_groups = True,
            use_mesh_modifiers = True)

        export_copy_obj_key(chr_cache, dir, name)

    # restore selection
    bpy.ops.object.select_all(action='DESELECT')
    for obj in old_selection:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = old_active

    utils.log_recess()
    utils.log_timer("Done Character Export.")


def export_non_standard(file_path):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Exporting Non-Standard Model to CC:")
    utils.log_info("-----------------------------------")

    utils.set_mode("OBJECT")

    export_anim = False
    dir, name = os.path.split(file_path)
    type = name[-3:].lower()
    name = name[:-4]

    # store selection
    old_selection = bpy.context.selected_objects.copy()
    old_active = bpy.context.active_object

    objects = get_export_objects(None, True)
    arm = utils.get_armature_in_objects(objects)

    utils.log_info("Generating JSON data for export:")
    utils.log_indent()
    json_data, export_changes = prep_non_standard_export(objects, dir, name, prefs.export_non_standard_mode)

    utils.log_recess()
    utils.log_info("Preparing character for export:")
    utils.log_indent()

    remove_modifiers_for_export(None, objects, True)

    # attempt any custom exports (ARP)
    custom_export = False
    if is_arp_installed() and is_arp_rig(arm):
        custom_export = export_arp(file_path)

    # double check custom export
    if not os.path.exists(file_path):
        custom_export = False

    # proceed with normal export
    if not custom_export:
        bpy.ops.export_scene.fbx(filepath=file_path,
                use_selection = True,
                bake_anim = export_anim,
                add_leaf_bones = False,
                use_mesh_modifiers = True,
                use_armature_deform_only = True)

    utils.log_recess()
    utils.log_info("")
    utils.log_info("Writing Json Data.")

    if json_data:
        new_json_path = os.path.join(dir, name + ".json")
        jsonutils.write_json(json_data, new_json_path)

    restore_export(export_changes)

    # restore selection
    bpy.ops.object.select_all(action='DESELECT')
    for obj in old_selection:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = old_active

    utils.log_recess()
    utils.log_timer("Done Non-standard Export.")


def export_to_unity(chr_cache, export_anim, file_path):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Exporting Character Model to UNITY:")
    utils.log_info("-----------------------------------")

    utils.set_mode("OBJECT")

    dir, file = os.path.split(file_path)
    name, type = os.path.splitext(file)

    utils.log_info("Export to: " + file_path)
    utils.log_info("Exporting as: " + type)

    json_data = chr_cache.get_json_data()

    utils.log_info("Preparing character for export:")
    utils.log_indent()

    objects = get_export_objects(chr_cache, False)
    export_rig = None

    if chr_cache.rigified:
        export_rig = rigging.prep_unity_export_rig(chr_cache)
        if export_rig:
            rigify_rig = chr_cache.get_armature()
            objects.remove(rigify_rig)
            objects.append(export_rig)

    as_blend_file = False
    if type == ".blend" and prefs.export_unity_remove_objects:
        as_blend_file = True

    remove_modifiers_for_export(chr_cache, objects, True)

    prep_export_unity(chr_cache, name, objects, json_data, chr_cache.import_dir, dir, as_blend_file)

    # store Unity project paths
    if type == ".blend":
        props.unity_file_path = file_path
        props.unity_project_path = utils.search_up_path(file_path, "Assets")

    if type == ".fbx":
        # export as fbx
        export_actions = prefs.export_animation_mode == "ACTIONS" or prefs.export_animation_mode == "BOTH"
        export_strips = prefs.export_animation_mode == "STRIPS" or prefs.export_animation_mode == "BOTH"
        bpy.ops.export_scene.fbx(filepath=file_path,
                use_selection = True,
                bake_anim = export_anim,
                bake_anim_use_all_actions=export_actions,
                bake_anim_use_nla_strips=export_strips,
                use_armature_deform_only=True,
                add_leaf_bones = False,
                use_mesh_modifiers = True)

        restore_modifiers(chr_cache, objects)

    elif type == ".blend":
        chr_cache.change_import_file(file_path)
        # save blend file at filepath
        if not utils.is_same_path(utils.local_path, file_path):
            bpy.ops.wm.save_as_mainfile(filepath=file_path)
        bpy.ops.file.make_paths_relative()
        bpy.ops.wm.save_as_mainfile(filepath=file_path)

    export_copy_fbx_key(chr_cache, dir, name)

    # clean up rigify export
    if chr_cache.rigified:
        rigging.finish_unity_export(chr_cache, export_rig)

    utils.log_recess()
    utils.log_info("")
    utils.log_info("Writing Json Data.")

    if json_data:
        new_json_path = os.path.join(dir, name + ".json")
        jsonutils.write_json(json_data, new_json_path)

    utils.log_recess()
    utils.log_timer("Done Character Export.")


def update_to_unity(chr_cache, export_anim):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Updating Character Model for UNITY:")
    utils.log_info("-----------------------------------")

    utils.set_mode("OBJECT")

    # update the file path (it may have been moved inside the unity project)
    if props.unity_file_path.lower().endswith(".fbx"):
        pass
    else:
        props.unity_file_path = bpy.data.filepath
        props.unity_project_path = utils.search_up_path(props.unity_file_path, "Assets")

    dir, name = os.path.split(props.unity_file_path)
    name, type = os.path.splitext(name)

    # keep the file paths up to date with the blend file location
    # Note: the textures and json file *must* maintain their relative paths to the blend/model file
    if type == ".blend":
        chr_cache.change_import_file(props.unity_file_path)

    json_data = chr_cache.get_json_data()

    utils.log_info("Preparing character for export:")
    utils.log_indent()

    objects = get_export_objects(chr_cache, False)

    as_blend_file = False
    if type == ".blend" and prefs.export_unity_remove_objects:
        as_blend_file = True

    remove_modifiers_for_export(chr_cache, objects, True)

    prep_export_unity(chr_cache, name, objects, json_data, chr_cache.import_dir, dir, as_blend_file)

    if type == ".fbx":
        # export as fbx
        export_actions = prefs.export_animation_mode == "ACTIONS" or prefs.export_animation_mode == "BOTH"
        export_strips = prefs.export_animation_mode == "STRIPS" or prefs.export_animation_mode == "BOTH"
        bpy.ops.export_scene.fbx(filepath=props.unity_file_path,
                use_selection = True,
                bake_anim = export_anim,
                bake_anim_use_all_actions=export_actions,
                bake_anim_use_nla_strips=export_strips,
                use_armature_deform_only=True,
                add_leaf_bones = False,
                use_mesh_modifiers = True)

        restore_modifiers(chr_cache, objects)

    elif type == ".blend":
        # save blend file at filepath
        bpy.ops.file.make_paths_relative()
        bpy.ops.wm.save_mainfile()

    utils.log_recess()
    utils.log_info("")
    utils.log_info("Writing Json Data.")

    if json_data:
        new_json_path = os.path.join(dir, name + ".json")
        jsonutils.write_json(json_data, new_json_path)

    utils.log_recess()
    utils.log_timer("Done Character Export.")


def export_as_accessory(file_path, filename_ext):
    dir, name = os.path.split(file_path)
    type = name[-3:].lower()
    name = name[:-4]

    # store selection
    old_selection = bpy.context.selected_objects
    old_active = bpy.context.active_object

    if filename_ext == ".fbx":
        bpy.ops.export_scene.fbx(filepath=file_path,
                use_selection = True,
                bake_anim = False,
                add_leaf_bones=False)
    else:
        bpy.ops.export_scene.obj(filepath=file_path,
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
        default="*.fbx;*.obj;*.blend",
        options={"HIDDEN"},
        )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    include_anim: bpy.props.BoolProperty(name = "Export Animation", default = True)
    include_selected: bpy.props.BoolProperty(name = "Include Selected", default = True)

    check_valid = True
    check_report = []
    check_warn = False

    def error_report(self):
        # error report
        if not self.check_valid:
            utils.message_box_multi("Export Check: Invalid Export", "ERROR", self.check_report)
        elif self.check_warn:
            utils.message_box_multi("Export Check: Some Warnings", "INFO", self.check_report)

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        chr_cache = props.get_context_character_cache(context)

        if chr_cache and self.param == "EXPORT_CC3":

            export_standard(chr_cache, self.filepath)
            self.report({'INFO'}, "Export to CC3 Done!")
            self.error_report()

        elif chr_cache and self.param == "EXPORT_UNITY":

            export_to_unity(chr_cache, self.include_anim, self.filepath)
            self.report({'INFO'}, "Export to Unity Done!")
            self.error_report()

        elif self.param == "UPDATE_UNITY":

            update_to_unity(chr_cache, self.include_anim)
            self.report({'INFO'}, "Update to Unity Done!")
            self.error_report()

        elif self.param == "EXPORT_NON_STANDARD":

            export_non_standard(self.filepath)
            self.report({'INFO'}, "Export Non-standard Done!")
            self.error_report()


        elif self.param == "EXPORT_ACCESSORY":

            export_as_accessory(self.filepath, self.filename_ext)
            self.report(type="INFO", message="Export Accessory Done!")

        elif self.param == "CHECK_EXPORT":

            if chr_cache.import_type == "fbx":
                chr_cache = props.get_context_character_cache(context)
                objects = get_export_objects(chr_cache, True)
                self.check_valid, self.check_warn, self.check_report = check_valid_export_fbx(chr_cache, objects)
                if not self.check_valid or self.check_warn:
                    self.error_report()
                else:
                    utils.message_box("No issues detected.", "Export Check", "INFO")

            else:
                pass

        return {"FINISHED"}


    def invoke(self, context, event):
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        self.check_report = []
        self.check_valid = True
        self.check_warn = False

        # bypass modal for direct functions
        if self.param == "UPDATE_UNITY":
            return self.execute(context)

        if self.param == "CHECK_EXPORT":
            return self.execute(context)

        props = bpy.context.scene.CC3ImportProps
        chr_cache = props.get_context_character_cache(context)

        # determine export format
        export_format = "fbx"
        if self.param == "EXPORT_NON_STANDARD":
            export_format = "fbx"
        elif self.param == "EXPORT_UNITY":
            if prefs.export_unity_mode == "FBX" or chr_cache.rigified:
                export_format = "fbx"
            else:
                export_format = "blend"
        elif chr_cache:
            export_format = chr_cache.import_type
        self.filename_ext = "." + export_format

        # perform checks and validation
        require_export_check = (self.param == "EXPORT_CC3" or
                                self.param == "EXPORT_UNITY" or
                                self.param == "UPDATE_UNITY" or
                                self.param == "EXPORT_NON_STANDARD")
        require_valid_export = (self.param == "EXPORT_CC3" or
                                self.param == "EXPORT_NON_STANDARD")
        if require_export_check:
            objects = get_export_objects(chr_cache, self.include_selected)
            if export_format == "fbx":
                self.check_valid, self.check_warn, self.check_report = check_valid_export_fbx(chr_cache, objects)
            if require_valid_export:
                if not self.check_valid:
                    self.error_report()
                    return {"FINISHED"}

        # determine default file name
        if not self.filepath:
            default_file_path = context.blend_data.filepath
            if not default_file_path:
                if self.param == "EXPORT_ACCESSORY":
                    if chr_cache:
                        default_file_path = chr_cache.import_name + "_accessory"
                    else:
                        default_file_path = "accessory"
                else:
                    if chr_cache:
                        default_file_path = chr_cache.import_name + "_export"
                    else:
                        default_file_path = "untitled"
            else:
                default_file_path = os.path.splitext(default_file_path)[0]
            self.filepath = default_file_path + self.filename_ext

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
        elif properties.param == "EXPORT_NON_STANDARD":
            return "Export selected objects as a non-standard character (Humanoid, Creature or Prop) to CC4"
        elif properties.param == "EXPORT_UNITY":
            return "Export to / Save in Unity project"
        elif properties.param == "EXPORT_ACCESSORY":
            return "Export selected object(s) for import into CC3 as accessories"
        elif properties.param == "CHECK_EXPORT":
            return "Check for issues with the character for export. *Note* This will also test any selected objects as well as all objects attached to the character, as selected objects can also be exported with the character."
        return ""
