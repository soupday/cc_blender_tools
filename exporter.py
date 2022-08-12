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
import mathutils
import math

import bpy
from filecmp import cmp

from . import bake, shaders, physics, rigging, bones, modifiers, nodeutils, imageutils, jsonutils, utils, params, vars

UNPACK_INDEX = 1001


def check_valid_export_fbx(chr_cache, objects):

    report = []
    check_valid = True
    check_warn = False
    arm = utils.get_armature_in_objects(objects)
    standard = False
    if chr_cache:
        standard = chr_cache.is_standard()

    if standard and not arm:
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
                if standard:
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
                # doesn't seem to be an issue anymore
                if False and obj.type == "MESH" and obj.data and len(obj.data.vertices) < 150:
                    message = f"WARNING: Object: {obj.name} has a low number of vertices (less than 150), this is can cause CTD issues with CC3's importer."
                    report.append(message)
                    utils.log_warn(message)
                    message = f" (if CC3 crashes when importing this character, consider increasing vertex count or joining this object to another.)"
                    report.append(message)
                    utils.log_warn(message)
                    check_warn = True

    return check_valid, check_warn, report


INVALID_EXPORT_CHARACTERS = "`¬!\"£$%^&*()+-=[]{}:@~;'#<>?,./\| "


def is_invalid_export_name(name):
    for char in INVALID_EXPORT_CHARACTERS:
        if char in name:
            return True
    return False


def safe_export_name(name):
    for char in INVALID_EXPORT_CHARACTERS:
        if char in name:
            name = name.replace(char, "_")
    return name


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


def prep_export(chr_cache, new_name, objects, json_data, old_path, new_path,
                copy_textures, revert_duplicates, apply_fixes, as_blend_file, bake_values):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if as_blend_file:
        if prefs.export_unity_remove_objects:
            # remove everything not part of the character for blend file exports.
            arm = utils.get_armature_in_objects(objects)
            for obj in bpy.data.objects:
                if not (obj == arm or obj.parent == arm or chr_cache.has_object(obj)):
                    utils.log_info(f"Removing {obj.name} from blend file")
                    bpy.data.objects.remove(obj)

    if not chr_cache or not json_data:
        return None

    mats_processed = {}
    images_processed = {}

    # old path might be blank, so try to use blend file path or export target path
    base_path = old_path
    if not base_path:
        base_path = utils.local_path()
        if not base_path:
            base_path = new_path

    changes = []
    done = []
    for obj in objects:
        if obj not in done:
            changes.append(["OBJECT_RENAME", obj, obj.name, obj.data.name])
            done.append(obj)
        if obj.type == "MESH":
            for mat in obj.data.materials:
                if mat not in done:
                    changes.append(["MATERIAL_RENAME", mat, mat.name])
                    done.append(mat)
    done.clear()

    old_name = chr_cache.import_name
    if new_name != old_name:
        if (old_name in json_data.keys() and
            old_name in json_data[old_name]["Object"].keys() and
            new_name not in json_data.keys()):
            # rename the object and character keys
            json_data[old_name]["Object"][new_name] = json_data[old_name]["Object"].pop(chr_cache.character_id)
            json_data[new_name] = json_data.pop(old_name)

    chr_json = json_data[new_name]["Object"][new_name]

    # create soft physics json if none
    physics_json = jsonutils.add_json_path(chr_json, "Physics/Soft Physics/Meshes")

    json_data[new_name]["Blender_Project"] = True
    if chr_cache.is_non_standard():
        set_non_standard_generation(json_data, chr_cache.non_standard_type, new_name)

    # unpack embedded textures.
    if chr_cache.import_embedded:
        unpack_embedded_textures(chr_cache, chr_json, objects, base_path)

    if revert_duplicates:
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
            mat_safe_name = safe_export_name(utils.strip_name(mat_name))
            if mat_safe_name in mat_count.keys():
                mat_count[mat_safe_name] += 1
            else:
                mat_count[mat_safe_name] = 1

        # determine a single source of any duplicate material names, prefer an exact match
        mat_remap = {}
        for mat_safe_name in mat_count.keys():
            count = mat_count[mat_safe_name]
            if count > 1:
                for mat in export_mats:
                    if mat.name == mat_safe_name:
                        mat_remap[mat_safe_name] = mat
                        break
                    elif mat.name.startswith(mat_safe_name):
                        mat_remap[mat_safe_name] = mat

    obj : bpy.types.Object
    for obj in objects:

        if not utils.object_exists_is_mesh(obj):
            continue

        if chr_cache.collision_body == obj:
            continue

        utils.log_info(f"Obejct: {obj.name}")
        utils.log_indent()

        obj_name = obj.name
        obj_cache = chr_cache.get_object_cache(obj)
        source_changed = False
        is_new_object = False
        if obj_cache:
            obj_expected_source_name = safe_export_name(utils.strip_name(obj_name))
            obj_source_name = obj_cache.source_name
            source_changed = obj_expected_source_name != obj_source_name
            if source_changed:
                obj_safe_name = safe_export_name(obj_name)
            else:
                obj_safe_name = obj_source_name
        else:
            is_new_object = True
            obj_safe_name = safe_export_name(obj_name)
            obj_source_name = obj_safe_name

        # if the Object name has been changed in some way
        if obj_name != obj_safe_name or obj.data.name != obj_safe_name:
            new_obj_name = obj_safe_name
            if is_new_object or source_changed:
                new_obj_name = utils.make_unique_name(obj_safe_name, bpy.data.objects.keys())
            utils.log_info(f"Using new safe Object & Mesh name: {obj_name} to {new_obj_name}")
            if source_changed:
                if jsonutils.rename_json_key(chr_json["Meshes"], obj_source_name, new_obj_name):
                    utils.log_info(f"Updating Object source json name: {obj_source_name} to {new_obj_name}")
                if physics_json and jsonutils.rename_json_key(physics_json, obj_source_name, new_obj_name):
                    utils.log_info(f"Updating Physics Object source json name: {obj_source_name} to {new_obj_name}")
            obj.name = new_obj_name
            obj.name = new_obj_name
            obj.data.name = new_obj_name
            obj.data.name = new_obj_name
            obj_name = new_obj_name
            obj_safe_name = new_obj_name
            obj_source_name = new_obj_name

        # fetch or create the object json
        obj_json = jsonutils.get_object_json(chr_json, obj)
        physics_mesh_json = jsonutils.get_physics_mesh_json(physics_json, obj)
        if not obj_json:
            utils.log_info(f"Adding Object Json: {obj_name}")
            obj_json = copy.deepcopy(params.JSON_MESH_DATA)
            chr_json["Meshes"][obj_name] = obj_json
        if not physics_mesh_json and obj_cache and obj_cache.cloth_physics == "ON":
            utils.log_info(f"Adding Physics Object Json: {obj_name}")
            physics_mesh_json = copy.deepcopy(params.JSON_PHYSICS_MESH)
            physics_json[obj_name] = physics_mesh_json

        for slot in obj.material_slots:
            mat = slot.material
            mat_name = mat.name
            mat_cache = chr_cache.get_material_cache(mat)
            source_changed = False
            new_material = False

            utils.log_info(f"Material: {mat.name}")
            utils.log_indent()

            if mat not in mats_processed.keys():
                mats_processed[mat.name] = { "processed": False, "write_back": False, "copied": False, "remapped": False }
            mat_data = mats_processed[mat.name]

            if mat_cache:
                mat_expected_source_name = (safe_export_name(utils.strip_name(mat_name))
                                            if revert_duplicates else
                                            safe_export_name(mat_name))
                mat_source_name = mat_cache.source_name
                source_changed = mat_expected_source_name != mat_source_name
                if source_changed:
                    mat_safe_name = safe_export_name(mat_name)
                else:
                    mat_safe_name = mat_source_name
            else:
                new_material = True
                mat_safe_name = safe_export_name(mat_name)
                mat_source_name = mat_safe_name

            if mat_name != mat_safe_name:
                new_mat_name = mat_safe_name
                if new_material or source_changed:
                    new_mat_name = utils.make_unique_name(mat_safe_name, bpy.data.materials.keys())
                utils.log_info(f"Using new safe Material name: {mat_name} to {new_mat_name}")
                if source_changed:
                    if jsonutils.rename_json_key(obj_json["Materials"], mat_source_name, new_mat_name):
                        utils.log_info(f"Updating material json name: {mat_source_name} to {new_mat_name}")
                    if physics_mesh_json and jsonutils.rename_json_key(physics_mesh_json["Materials"], mat_source_name, new_mat_name):
                        utils.log_info(f"Updating physics material json name: {mat_source_name} to {new_mat_name}")
                mat.name = new_mat_name
                mat.name = new_mat_name
                mat_name = new_mat_name
                mat_safe_name = new_mat_name
                mat_source_name = new_mat_name

            # fetch or create the material json
            write_json = prefs.export_json_changes
            write_physics_json = write_json
            write_textures = prefs.export_texture_changes
            write_physics_textures = write_textures
            mat_json = jsonutils.get_material_json(obj_json, mat)
            physics_mat_json = jsonutils.get_physics_material_json(physics_mesh_json, mat)

            # try to create the material json data from the mat_cache shader def
            if mat_cache and not mat_json:
                shader_name = params.get_shader_name(mat_cache)
                json_template = params.get_mat_shader_template(mat_cache)
                utils.log_info(f"Adding Material Json: {mat_name} for Shader: {shader_name}")
                if json_template:
                    mat_json = copy.deepcopy(json_template)
                    obj_json["Materials"][mat_safe_name] = mat_json
                    write_json = True
                    write_textures = True

            # fallback default to PBR material json data
            if not mat_json:
                utils.log_info(f"Adding Default PBR Material Json: {mat_name}")
                mat_json = copy.deepcopy(params.JSON_PBR_MATERIAL)
                obj_json["Materials"][mat_safe_name] = mat_json
                write_json = True
                write_textures = True

            material_physics_enabled = physics.is_cloth_physics_enabled(mat_cache, mat, obj)
            if physics_mesh_json and not physics_mat_json and material_physics_enabled:
                physics_mat_json = copy.deepcopy(params.JSON_PHYSICS_MATERIAL)
                physics_mesh_json["Materials"][mat_safe_name] = physics_mat_json
                write_physics_json = True
                write_physics_textures = True

            if mat_cache:
                utils.log_info("Writing Json:")
                utils.log_indent()
                # update the json parameters with any changes
                if write_textures:
                    write_back_textures(mat_json, mat, mat_cache, base_path, old_name, bake_values, mat_data, images_processed)
                if write_json:
                    write_back_json(mat_json, mat, mat_cache)
                if write_physics_json:
                    # there isn't a meaningful way to convert between Blender physics and RL PhysX
                    pass
                if write_physics_textures:
                    write_back_physics_weightmap(physics_mat_json, obj, mat, mat_cache, base_path, old_name, mat_data)
                if revert_duplicates:
                    # replace duplicate materials with a reference to a single source material
                    # (this is to ensure there are no duplicate suffixes in the fbx export)
                    if mat_count[mat_safe_name] > 1:
                        new_mat = mat_remap[mat_safe_name]
                        slot.material = new_mat
                        utils.log_info("Replacing material: " + mat.name + " with " + new_mat.name)
                        changes.append(["MATERIAL_SLOT_REPLACE", slot, mat])
                        mat = new_mat
                        mat_name = new_mat.name
                    if mat_name != mat_safe_name:
                        utils.log_info(f"Reverting material name: {mat_name} to {mat_safe_name}")
                        mat.name = mat_safe_name
                        mat.name = mat_safe_name
                utils.log_recess()
            else:
                # add pbr material to json for non-cached base object/material
                write_pbr_material_to_json(mat, mat_json, old_path, old_name, bake_values)

            # copy or remap the texture paths
            utils.log_info("Finalizing Texture Paths:")
            utils.log_indent()
            if copy_textures:
                images_copied = []
                for channel in mat_json["Textures"].keys():
                    copy_and_update_texture_path(mat_json["Textures"][channel], "Texture Path", old_path, new_path, old_name, new_name, as_blend_file, mat_name, mat_data, images_copied)
                if "Custom Shader" in mat_json.keys():
                    for channel in mat_json["Custom Shader"]["Image"].keys():
                        copy_and_update_texture_path(mat_json["Custom Shader"]["Image"][channel], "Texture Path", old_path, new_path, old_name, new_name, as_blend_file, mat_name, mat_data, images_copied)
                if physics_mat_json:
                    copy_and_update_texture_path(physics_mat_json, "Weight Map Path", old_path, new_path, old_name, new_name, as_blend_file, mat_name, mat_data, images_copied)

            else:
                for channel in mat_json["Textures"].keys():
                    remap_texture_path(mat_json["Textures"][channel], "Texture Path", old_path, new_path, mat_data)
                if "Custom Shader" in mat_json.keys():
                    for channel in mat_json["Custom Shader"]["Image"].keys():
                        remap_texture_path(mat_json["Custom Shader"]["Image"][channel], "Texture Path", old_path, new_path, mat_data)
                if physics_mat_json:
                    remap_texture_path(physics_mat_json, "Weight Map Path", old_path, new_path, mat_data)

            mat_data["processed"] = True
            # texure paths
            utils.log_recess()

            # material
            utils.log_recess()

        # object
        utils.log_recess()

    if apply_fixes and prefs.export_bone_roll_fix:
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


def remap_texture_path(tex_info, path_key, old_path, new_path, mat_data):

    # at this point all the image paths have been re-written as absolute paths
    # (except those not used in the Blender material shaders)

    if path_key in tex_info.keys():
        if tex_info[path_key]:
            tex_path = tex_info[path_key]
            if os.path.isabs(tex_path):
                abs_path = tex_path
            else:
                abs_path = os.path.normpath(os.path.join(old_path, tex_path))
            rel_path = utils.relpath(abs_path, new_path)
            tex_info[path_key] = os.path.normpath(rel_path)

    mat_data["remapped"] = True

    return





def copy_and_update_texture_path(tex_info, path_key, old_path, new_path, old_name, new_name, as_blend_file, mat_name, mat_data, images_copied):
    """keep the same relative folder structure and copy the textures to their target folder.
       update the images in the blend file with the new location."""

    # at this point all the image paths have been re-written as absolute paths

    # TODO: this needs to cope with materials being reused across multiple meshes
    #       currently it is stacking relative paths each time it's called...

    sep = os.path.sep
    old_tex_base = os.path.join(old_path, f"textures{sep}{old_name}")
    old_fbm_base = os.path.join(old_path, f"{old_name}.fbm")

    if path_key in tex_info.keys():

        tex_path : str = tex_info[path_key]
        if not os.path.isabs(tex_path):
            tex_path = os.path.normpath(os.path.join(old_path, tex_path))

        if tex_path:

            old_abs_path = os.path.normpath(tex_path)

            # old_path will only be set from a successful import from CC/iC
            # so it should have expected the CC/iC folder structure
            if old_path:

                rel_tex_path = utils.relpath(os.path.normpath(tex_path), old_path)

                # only remap the tex_path if it is inside the expected texture folders
                if utils.path_is_parent(old_tex_base, old_abs_path) or utils.path_is_parent(old_fbm_base, old_abs_path):
                    if old_name != new_name:
                        rel_tex_path = rel_tex_path.replace(f"textures{sep}{old_name}{sep}{old_name}{sep}", f"textures{sep}{new_name}{sep}{new_name}{sep}")
                        rel_tex_path = rel_tex_path.replace(f"textures{sep}{old_name}{sep}", f"textures{sep}{new_name}{sep}")
                        rel_tex_path = rel_tex_path.replace(f"{old_name}.fbm{sep}", f"{new_name}.fbm{sep}")

                new_abs_path = os.path.normpath(os.path.join(new_path, rel_tex_path))
                new_rel_path = os.path.normpath(utils.relpath(new_abs_path, new_path))

                utils.log_info("Remapping JSON texture path to: " + new_rel_path)

            else:

                # otherwise put the textures in folders in the textures/CHARACTER_NAME/Extras/MATERIAL_NAME/ folder
                dir, file = os.path.split(tex_path)
                extras_dir = f"textures{sep}{new_name}{sep}Extras{sep}{mat_name}"
                new_rel_path = os.path.normpath(os.path.join(extras_dir, file))
                new_abs_path = os.path.normpath(os.path.join(new_path, new_rel_path))

                utils.log_info("Setting JSON texture path to: " + new_rel_path)

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
                utils.log_info(f"Copying texture: {old_abs_path}")
                utils.log_info(f"             to: {new_abs_path}")
                shutil.copyfile(old_abs_path, new_abs_path)

            # update the json texture path with the new relative path
            tex_info[path_key] = new_rel_path

            # update images with changed file path (if it changed, and only if exporting as blend file)
            if as_blend_file and os.path.exists(old_abs_path) and os.path.exists(new_abs_path):
                # if the original path and new path are different
                if os.path.normpath(old_abs_path) != os.path.normpath(new_abs_path):
                    image : bpy.types.Image
                    for image in bpy.data.images:
                        # for each image not already copied
                        if image and image.filepath and image not in images_copied:
                            image_file_path = bpy.path.abspath(image.filepath)
                            if os.path.exists(image_file_path):
                                # if this is the image specified in the json path
                                if os.path.samefile(image_file_path, old_abs_path):
                                    utils.log_info(f"Updating .blend Image: {image.name}")
                                    utils.log_info(f"                   to: {new_abs_path}")
                                    image.filepath = new_abs_path
                                    images_copied.append(image)


def restore_export(export_changes : list):
    if not export_changes:
        return
    # undo everything prep_export did
    # (but don't bother with the json data as it is temporary)
    for info in export_changes:
        op = info[0]
        if op == "OBJECT_RENAME":
            obj = info[1]
            obj.name = info[2]
            obj.name = info[2]
            obj.data.name = info[3]
            obj.data.name = info[3]
        elif op == "MATERIAL_RENAME":
            mat = info[1]
            mat.name = info[2]
            mat.name = info[2]
        elif op == "MATERIAL_SLOT_REPLACE":
            slot = info[1]
            slot.material = info[2]
            slot.material = info[2]
    return


def get_prop_value(mat_cache, prop_name, default):
    parameters = mat_cache.parameters
    try:
        return eval("parameters." + prop_name, None, locals())
    except:
        return default


def write_back_json(mat_json, mat, mat_cache):
    shader_name = params.get_shader_name(mat_cache)
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


def write_back_textures(mat_json : dict, mat, mat_cache, base_path, old_name, bake_values, mat_data, images_processed):
    global UNPACK_INDEX
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if mat_json is None:
        return

    shader_name = params.get_shader_name(mat_cache)
    rl_shader_name = params.get_rl_shader_name(mat_cache)
    shader_def = params.get_shader_def(shader_name)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader_name)
    has_custom_shader = "Custom Shader" in mat_json.keys()

    unpack_path = os.path.join(base_path, "textures", old_name, "Unpack")
    bake_path = os.path.join(base_path, "textures", old_name, "Baked")

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

                    # fetch the tex_info data for the channel
                    if tex_id in mat_json["Textures"]:
                        tex_info = mat_json["Textures"][tex_id]

                    # or create a new tex_info if missing or baking a new texture
                    elif tex_node or bake_shader_output:
                        tex_info = copy.deepcopy(params.JSON_PBR_TEX_INFO)
                        location, rotation, scale = nodeutils.get_image_node_mapping(tex_node)
                        tex_info["Tiling"] = [scale[0], scale[1]]
                        tex_info["Offset"] = [location[0], location[1]]
                        mat_json["Textures"][tex_id] = tex_info

                    # note: strength values for textures defined in the shader vars are written after in write_back_json()

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

                    processed_image = None
                    if tex_type in mat_data.keys():
                        processed_image = mat_data[tex_type]["image"]
                        utils.log_info(f"Resusing already processed material image: {processed_image.name}")

                    if tex_node or bake_shader_output:

                        image : bpy.types.Image = None

                        # re-use the already processed image if available
                        if processed_image:
                            image = processed_image

                        else:
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
                                else:
                                    image = bake.bake_node_socket_input(shader_node, shader_socket, mat, tex_id, bake_path)

                        tex_info["Texture Path"] = ""

                        if image:

                            mat_data[tex_type] = image

                            try_unpack_image(image, unpack_path, True)

                            if image.filepath:

                                image_data = None
                                if image in images_processed.keys():
                                    image_data = images_processed[image]
                                else:
                                    abs_image_path = os.path.normpath(bpy.path.abspath(image.filepath))
                                    image_data = { "old_path": abs_image_path }
                                    images_processed[image] = image_data

                                abs_image_path = image_data["old_path"]

                                tex_info["Texture Path"] = abs_image_path
                                utils.log_info(f"{mat.name}/{tex_id}: Source texture path: {abs_image_path}")

            mat_data["write_back"] = True


def write_back_physics_weightmap(physics_mat_json : dict, obj, mat, mat_cache, base_path, old_name, mat_data):
    global UNPACK_INDEX
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if physics_mat_json is None:
        return

    unpack_path = os.path.join(base_path, "textures", old_name, "Unpack")
    UNPACK_INDEX = 1001

    image = physics.get_weight_map_from_modifiers(obj, mat)

    if image:

        mat_data["WEIGHTMAP"] = image

        try_unpack_image(image, unpack_path, True)

        if image.filepath:
            abs_image_path = bpy.path.abspath(image.filepath)
            if abs_image_path:
                utils.log_info(f"{mat.name}: Using new weight map texture path: {abs_image_path}")
                physics_mat_json["Weight Map Path"] = abs_image_path


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


def unpack_embedded_textures(chr_cache, chr_json, objects, base_path):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    unpack_folder = None
    if chr_cache:
        unpack_folder = os.path.join(base_path, "textures", chr_cache.import_name, "Unpack")
    else:
        unpack_folder = os.path.join(base_path, "textures", "Unpack")

    if unpack_folder:
        utils.log_info(f"Unpacking embedded textures to: {unpack_folder}")
        if not os.path.exists(unpack_folder):
            os.makedirs(unpack_folder, exist_ok=True)

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
                                try_unpack_image(image, unpack_folder)
                                abs_image_path = bpy.path.abspath(image.filepath)

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
                                            dir, name = os.path.split(abs_image_path)
                                            if "_Diffuse" in name and tex_type == "ALPHA":
                                                utils.log_info(f"Diffuse connected to Alpha, removing Opacity data from Json.")
                                                del mat_json["Textures"][tex_id]
                                                tex_info = None

                                        if tex_info:
                                            tex_info["Texture Path"] = abs_image_path
                                            utils.log_info(f"Updating embedded image Json data: {abs_image_path}")
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
            for obj in arm.children:
                    if utils.object_exists_is_mesh(obj): # and obj.visible_get():
                        if obj not in objects:
                            objects.append(obj)
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


def set_T_pose(arm, chr_json):
    utils.log_info("Putting character in T-Pose.")

    if utils.edit_mode_to(arm):
        left_arm_edit = bones.get_edit_bone(arm, ["CC_Base_L_Upperarm", "L_Upperarm", "upperarm_l"])
        right_arm_edit = bones.get_edit_bone(arm, ["CC_Base_R_Upperarm", "R_Upperarm", "upperarm_r"])
        # test for A-pose
        world_x = mathutils.Vector((1, 0, 0))
        a_pose = False
        if left_arm_edit and world_x.dot(left_arm_edit.y_axis) < 0.9:
            a_pose = True
        if right_arm_edit and world_x.dot(right_arm_edit.y_axis) > -0.9:
            a_pose = True
        # Set T-pose
        if a_pose:
            bones.clear_pose(arm)
            left_arm_pose = bones.get_pose_bone(arm, ["CC_Base_L_Upperarm", "L_Upperarm", "upperarm_l"])
            right_arm_pose = bones.get_pose_bone(arm, ["CC_Base_R_Upperarm", "R_Upperarm", "upperarm_r"])
            angle = 30.0 * math.pi / 180.0
            if left_arm_pose:
                left_arm_pose.rotation_mode = "XYZ"
                left_arm_pose.rotation_euler = [0,0,angle]
                left_arm_pose.rotation_mode = "QUATERNION"
            if right_arm_pose:
                right_arm_pose.rotation_mode = "XYZ"
                right_arm_pose.rotation_euler = [0,0,-angle]
                right_arm_pose.rotation_mode = "QUATERNION"
            chr_json["Bind_Pose"] = "APose"
            return True
        chr_json["Bind_Pose"] = "TPose"
    return False


def clear_animation_data(obj):
    if obj.type == "ARMATURE" or obj.type == "MESH":
        # remove action
        utils.safe_set_action(obj, None)
        # remove strips
        obj.animation_data_clear()
    if obj.type == "MESH":
        # remove shape key action
        utils.safe_set_action(obj.data.shape_keys, None)
        # remove shape key strips
        if obj.data.shape_keys and obj.data.shape_keys.animation_data:
            obj.data.shape_keys.animation_data_clear()


def create_T_pose_action(arm, objects, export_strips):

    # remove all actions from objects
    for obj in objects:
        clear_animation_data(obj)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 2

    # create T-Pose action
    if "0_T-Pose" not in bpy.data.actions and utils.pose_mode_to(arm):
        action : bpy.types.Action = bpy.data.actions.new("0_T-Pose")
        utils.safe_set_action(arm, action)

        # go to first frame
        bpy.data.scenes["Scene"].frame_current = 1

        # apply first keyframe
        bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_LocRot')

        # make a second keyframe
        bpy.data.scenes["Scene"].frame_current = 2
        bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_LocRot')

    # or re-use T-Pose action
    else:
        action = bpy.data.actions["0_T-Pose"]
        utils.safe_set_action(arm, action)

    # push T-Pose to NLA if exporting strips
    if export_strips:
        utils.log_info(f"Adding {action.name} to NLA strips")
        if obj.animation_data is None:
            obj.animation_data_create()
        if len(obj.animation_data.nla_tracks) == 0:
            track = arm.animation_data.nla_tracks.new()
        else:
            track = arm.animation_data.nla_tracks[0]
        track.strips.new(action.name, int(action.frame_range[0]), action)
        utils.safe_set_action(arm, None)


def set_character_generation(json_data, chr_cache, name):
    if chr_cache and chr_cache.is_standard():
        set_standard_generation(json_data, chr_cache.generation, name)
    else:
        set_non_standard_generation(json_data, chr_cache.non_standard_type, name)


def set_non_standard_generation(json_data, character_type, character_id):
    generation = "Humanoid"
    if character_type == "CREATURE":
        generation = "Creature"
    elif character_type == "PROP":
        generation = "Prop"
    utils.log_info(f"Generation: {generation}")
    jsonutils.set_character_generation_json(json_data, character_id, character_id, generation)


def set_standard_generation(json_data, generation, character_id):
    # currently is doesn't really matter what the standard generation string is
    # generation in the CC4 plugin is only used to detect non-standard characters.

    json_generation = "Unknown"

    for id, gen in vars.CHARACTER_GENERATION.items():
        if gen == generation:
            json_generation = id
            break

    jsonutils.set_character_generation_json(json_data, character_id, character_id, generation)


def prep_non_standard_export(objects, dir, name, character_type):
    global UNPACK_INDEX
    bake.init_bake()
    UNPACK_INDEX = 5001

    changes = []
    done = []
    for obj in objects:
        if obj not in done:
            changes.append(["OBJECT_RENAME", obj, obj.name, obj.data.name])
            done.append(obj)
        if obj.type == "MESH":
            for mat in obj.data.materials:
                if mat not in done:
                    changes.append(["MATERIAL_RENAME", mat, mat.name])
                    done.append(mat)
    done.clear()

    # prefer to bake and unpack textures next to blend file, otherwise at the destination.
    blend_path = utils.local_path()
    if blend_path:
        dir = blend_path
    utils.log_info(f"Texture Root Dir: {dir}")

    json_data = jsonutils.generate_character_json_data(name)

    set_non_standard_generation(json_data, character_type, name)

    #arm = utils.get_armature_in_objects(objects)
    #if arm:
    #    bones.reset_root_bone(arm)

    done = []
    objects_json = json_data[name]["Object"][name]["Meshes"]
    for obj in objects:
        if obj.type == "MESH" and obj not in done:
            done.append(obj)
            utils.log_info(f"Adding Object Json: {obj.name}")
            export_name = safe_export_name(obj.name)
            if export_name != obj.name:
                utils.log_info(f"Updating Object name: {obj.name} to {export_name}")
                obj.name = export_name
            mesh_json = copy.deepcopy(params.JSON_MESH_DATA)
            objects_json[obj.name] = mesh_json
            for slot in obj.material_slots:
                mat = slot.material
                if mat not in done:
                    done.append(mat)
                    utils.log_info(f"Adding Material Json: {mat.name}")
                    export_name = safe_export_name(mat.name)
                    if export_name != mat.name:
                        utils.log_info(f"Updating Material name: {mat.name} to {export_name}")
                        mat.name = export_name
                    mat_json = copy.deepcopy(params.JSON_PBR_MATERIAL)
                    mesh_json["Materials"][mat.name] = mat_json
                    write_pbr_material_to_json(mat, mat_json, dir, name, True)

    # select all the export objects
    utils.try_select_objects(objects, True)

    return json_data, changes

#[ socket_path, node_label_match, source_type, tex_channel, strength_socket_path ]
BSDF_TEXTURES = [
    ["Base Color", "", "BSDF", "Base Color", ""],
    ["Metallic", "", "BSDF", "Metallic", ""],
    ["Specular", "", "BSDF", "Specular", ""],
    ["Roughness", "", "BSDF", "Roughness", ""],
    ["Emission", "", "BSDF", "Glow", "Emission Strength"],
    ["Alpha", "", "BSDF", "Opacity", ""],
    ["Normal:Color", "", "BSDF", "Normal", "Normal:Strength"],
    ["Normal:Normal:Color", "", "BSDF", "Normal", ["Normal:Normal:Strength", "Normal:Strength"]],
    ["Normal:Height", "", "BSDF", "Bump", ["Normal:Distance", "Normal:Strength"]],
    ["Base Color:Color2", "ao|occlusion", "BSDF", "AO", "Base Color:Fac"],
    ["Occlusion", "", "GLTF", "AO", "Occlusion:Fac"],
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
        for socket_trace, match, node_type, tex_id, strength_trace in BSDF_TEXTURES:
            if node_type == "BSDF":
                n = bsdf_node
            elif node_type == "GLTF":
                n = gltf_node
            else:
                n = None
            if n:
                linked_node, linked_socket = nodeutils.trace_input_sockets(n, socket_trace)
                strength = 1.0
                if type(strength_trace) is list:
                    for st in strength_trace:
                        strength *= float(nodeutils.trace_input_value(n, st, 1.0))
                else:
                    strength = float(nodeutils.trace_input_value(n, strength_trace, 1.0))
                if tex_id == "Bump":
                    strength = min(200, max(0, strength * 10000.0))
                elif tex_id == "Normal":
                    strength = min(200, max(0, strength * 100))
                else:
                    strength = min(100, max(0, strength * 100))
                if linked_node and linked_socket:
                    if match:
                        if re.match(match, linked_node.label) or re.match(match, linked_node.name):
                            socket_mapping[tex_id] = [linked_node, linked_socket, False, strength]
                    else:
                        socket_mapping[tex_id] = [linked_node, linked_socket, False, strength]
                else:
                    if tex_id == "Roughness" and bake_roughness:
                        socket_mapping[tex_id] = [bsdf_node, "Roughness", True, strength]
                    elif tex_id == "Metallic" and bake_metallic:
                        socket_mapping[tex_id] = [bsdf_node, "Metallic", True, strength]


        write_or_bake_tex_data_to_json(socket_mapping, mat, mat_json, bsdf_node, path, bake_path, unpack_path)

    else:
        # if there is no BSDF shader node, try to match textures by name (both image node name and image name)
        socket_mapping = {}
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                for tex_id in BSDF_TEXTURE_KEYWORDS:
                    for key in BSDF_TEXTURE_KEYWORDS[tex_id]:
                        if re.match(key, node.image.name.lower()) or re.match(key, node.label.lower()) or re.match(key, node.name.lower()):
                            socket_mapping[tex_id] = [node, "Color", False, 100.0]

        write_or_bake_tex_data_to_json(socket_mapping, mat, mat_json, None, path, bake_path, unpack_path)

    return


def write_or_bake_tex_data_to_json(socket_mapping, mat, mat_json, bsdf_node, path, bake_path, unpack_path):

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

        node, socket, bake_value, strength = socket_mapping[tex_id]
        utils.log_info(f"Adding Texture Chennel: {tex_id} strength - {strength}")

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
        if image.filepath:
            abs_image_path = bpy.path.abspath(image.filepath)
            if abs_image_path:
                utils.log_info(f"{mat.name}/{tex_id}: Using new texture path: {abs_image_path}")
                tex_info["Texture Path"] = abs_image_path
        if tex_node:
            location, rotation, scale = nodeutils.get_image_node_mapping(tex_node)
            tex_info["Tiling"] = [scale[0], scale[1]]
            tex_info["Offset"] = [location[0], location[1]]
        tex_info["Strength"] = strength
        mat_json["Textures"][tex_id] = tex_info


def export_copy_fbx_key(chr_cache, dir, name):
    if chr_cache.import_has_key:
        try:
            old_key_path = chr_cache.import_key_file
            if not os.path.exists(old_key_path):
                old_key_path = utils.local_path(chr_cache.import_name + ".fbxkey")
            if old_key_path and os.path.exists(old_key_path):
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
            if old_key_path and os.path.exists(old_key_path):
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
            return True
    return False


def export_arp(file_path, arm, objects):
    try:
        bpy.data.scenes["Scene"].arp_engine_type = "unity"
        bpy.data.scenes["Scene"].arp_export_rig_type = "humanoid"
        bpy.data.scenes["Scene"].arp_bake_anim = False
        bpy.data.scenes["Scene"].arp_ge_sel_only = True
        bpy.data.scenes["Scene"].arp_ge_sel_bones_only = False
        bpy.data.scenes["Scene"].arp_keep_bend_bones = False
        bpy.data.scenes["Scene"].arp_export_twist = True
        bpy.data.scenes["Scene"].arp_export_noparent = False
        bpy.data.scenes["Scene"].arp_export_renaming = False
        bpy.data.scenes["Scene"].arp_use_tspace = False
        bpy.data.scenes["Scene"].arp_fix_fbx_rot = False
        bpy.data.scenes["Scene"].arp_fix_fbx_matrix = True
        bpy.data.scenes["Scene"].arp_init_fbx_rot = False
        bpy.data.scenes["Scene"].arp_bone_axis_primary_export = "Y"
        bpy.data.scenes["Scene"].arp_bone_axis_secondary_export = "X"
        bpy.data.scenes["Scene"].arp_export_rig_name = "root"
        bpy.data.scenes["Scene"].arp_export_tex = False
        bpy.data.scenes["Scene"].arp_units_x100 = True
        bpy.data.scenes["Scene"].arp_global_scale = 1.0
        # select all objects
        utils.log_info(f"Selecting all character objects.")
        utils.try_select_objects(objects, True)
        # make sure the armature is active
        utils.log_info(f"Setting Armature: {arm.name} active")
        utils.set_active_object(arm)
        # invoke
        utils.log_info("Invoking ARP Export:")
        bpy.ops.id.arp_export_fbx_panel(filepath=file_path, check_existing = False)
        return True
    except:
        return False


def export_standard(chr_cache, file_path, include_selected):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Exporting Character Model to CC:")
    utils.log_info("--------------------------------")

    utils.set_mode("OBJECT")

    chr_cache.check_paths()

    export_anim = False
    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    # store selection
    old_selection = bpy.context.selected_objects
    old_active = bpy.context.active_object

    if utils.is_file_ext(ext, "FBX"):

        json_data = chr_cache.get_json_data()
        if not json_data:
            json_data = jsonutils.generate_character_json_data(name)
            set_character_generation(json_data, chr_cache, name)

        objects = get_export_objects(chr_cache, include_selected)
        arm = utils.get_armature_in_objects(objects)

        utils.log_info("Preparing character for export:")
        utils.log_indent()

        remove_modifiers_for_export(chr_cache, objects, True)

        revert_duplicates = prefs.export_revert_names
        copy_textures = chr_cache.generation == "NonStandardGeneric"
        export_changes = prep_export(chr_cache, name, objects, json_data, chr_cache.import_dir,
                                     dir, copy_textures, revert_duplicates, True, False, True)

        # attempt any custom exports (ARP)
        custom_export = False
        if is_arp_installed() and is_arp_rig(arm):
            custom_export = export_arp(file_path, arm, objects)

        # double check custom export
        if not os.path.exists(file_path):
            custom_export = False

        # proceed with normal export
        if not custom_export:
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


def export_non_standard(file_path, include_selected):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Exporting Non-Standard Model to CC:")
    utils.log_info("-----------------------------------")

    utils.set_mode("OBJECT")

    export_anim = False
    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    # store selection
    old_selection = bpy.context.selected_objects.copy()
    old_active = bpy.context.active_object

    objects = get_export_objects(None, include_selected)
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
        custom_export = export_arp(file_path, arm, objects)

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


def export_to_unity(chr_cache, export_anim, file_path, include_selected):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Exporting Character Model to UNITY:")
    utils.log_info("-----------------------------------")

    utils.set_mode("OBJECT")

    chr_cache.check_paths()

    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    utils.log_info("Export to: " + file_path)
    utils.log_info("Exporting as: " + ext)

    json_data = chr_cache.get_json_data()

    utils.log_info("Preparing character for export:")
    utils.log_indent()

    # remove the collision mesh proxy
    if utils.is_file_ext(ext, "BLEND"):
        if utils.object_exists_is_mesh(chr_cache.collision_body):
            utils.delete_mesh_object(chr_cache.collision_body)
            chr_cache.collision_body = None


    objects = get_export_objects(chr_cache, include_selected)
    export_rig = None

    if chr_cache.rigified:
        export_rig = rigging.prep_unity_export_rig(chr_cache)
        if export_rig:
            rigify_rig = chr_cache.get_armature()
            objects.remove(rigify_rig)
            objects.append(export_rig)

    as_blend_file = utils.is_file_ext(ext, "BLEND")

    # remove custom material modifiers
    remove_modifiers_for_export(chr_cache, objects, True)

    prep_export(chr_cache, name, objects, json_data, chr_cache.import_dir, dir, True, False, False, as_blend_file, False)

    export_actions = prefs.export_animation_mode == "ACTIONS" or prefs.export_animation_mode == "BOTH"
    export_strips = prefs.export_animation_mode == "STRIPS" or prefs.export_animation_mode == "BOTH"

    if not chr_cache.rigified:
        # non rigified FBX exports export only T-pose as a strip
        if utils.is_file_ext(ext, "FBX"):
            export_actions = False
            export_strips = True
        # blend file exports make the T-pose as an action
        else:
            export_actions = True
            export_strips = False
        arm = utils.get_armature_in_objects(objects)
        utils.safe_set_action(arm, None)
        set_T_pose(arm, json_data[name]["Object"][name])
        create_T_pose_action(arm, objects, export_strips)

    # store Unity project paths
    if utils.is_file_ext(ext, "BLEND"):
        props.unity_file_path = file_path
        props.unity_project_path = utils.search_up_path(file_path, "Assets")

    if utils.is_file_ext(ext, "FBX"):
        # export as fbx
        bpy.ops.export_scene.fbx(filepath=file_path,
                use_selection = True,
                bake_anim = export_anim,
                bake_anim_use_all_actions=export_actions,
                bake_anim_use_nla_strips=export_strips,
                use_armature_deform_only=True,
                add_leaf_bones = False,
                use_mesh_modifiers = True)

        restore_modifiers(chr_cache, objects)

    elif utils.is_file_ext(ext, "BLEND"):
        chr_cache.change_import_file(file_path)
        # save blend file at filepath
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


def update_to_unity(chr_cache, export_anim, include_selected):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Updating Character Model for UNITY:")
    utils.log_info("-----------------------------------")

    utils.set_mode("OBJECT")

    chr_cache.check_paths()

    # update the file path (it may have been moved inside the unity project)
    if props.unity_file_path.lower().endswith(".fbx"):
        pass
    else:
        props.unity_file_path = bpy.data.filepath
        props.unity_project_path = utils.search_up_path(props.unity_file_path, "Assets")

    dir, name = os.path.split(props.unity_file_path)
    name, ext = os.path.splitext(name)

    # keep the file paths up to date with the blend file location
    # Note: the textures and json file *must* maintain their relative paths to the blend/model file
    if not utils.is_file_ext(ext, "BLEND"):
        utils.log_error("Update to Unity can only be called for Blend file exports!")
        return

    chr_cache.change_import_file(props.unity_file_path)

    json_data = chr_cache.get_json_data()

    utils.log_info("Preparing character for export:")
    utils.log_indent()

    # remove the collision mesh proxy
    if utils.object_exists_is_mesh(chr_cache.collision_body):
        utils.delete_mesh_object(chr_cache.collision_body)
        chr_cache.collision_body = None

    objects = get_export_objects(chr_cache, include_selected)

    as_blend_file = True

    # remove custom material modifiers
    remove_modifiers_for_export(chr_cache, objects, True)

    prep_export(chr_cache, name, objects, json_data, chr_cache.import_dir, dir, True, False, False, as_blend_file, False)

    arm = utils.get_armature_in_objects(objects)
    utils.safe_set_action(arm, None)
    set_T_pose(arm, json_data[name]["Object"][name])
    # make the T-pose as an action
    create_T_pose_action(arm, objects, False)

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
    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    # store selection
    old_selection = bpy.context.selected_objects
    old_active = bpy.context.active_object

    if utils.is_file_ext(ext, "FBX"):
        bpy.ops.export_scene.fbx(filepath=file_path,
                use_selection = True,
                bake_anim = False,
                add_leaf_bones=False)
    elif utils.is_file_ext(ext, "OBJ"):
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


def export_as_replace_mesh(file_path):
    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    # store selection
    old_selection = bpy.context.selected_objects
    old_active = bpy.context.active_object

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

            export_standard(chr_cache, self.filepath, self.include_selected)
            self.report({'INFO'}, "Export to CC3 Done!")
            self.error_report()

        elif chr_cache and self.param == "EXPORT_UNITY":

            export_to_unity(chr_cache, self.include_anim, self.filepath, self.include_selected)
            self.report({'INFO'}, "Export to Unity Done!")
            self.error_report()

        elif self.param == "UPDATE_UNITY":

            # only called when updating .blend file exports
            update_to_unity(chr_cache, self.include_anim, True)
            self.report({'INFO'}, "Update to Unity Done!")
            self.error_report()

        elif self.param == "EXPORT_NON_STANDARD":

            export_non_standard(self.filepath, self.include_selected)
            self.report({'INFO'}, "Export Non-standard Done!")
            self.error_report()


        elif self.param == "EXPORT_ACCESSORY":

            export_as_accessory(self.filepath, self.filename_ext)
            self.report({'INFO'}, message="Export Accessory Done!")

        elif self.param == "EXPORT_MESH":

            export_as_replace_mesh(self.filepath)
            self.report({'INFO'}, message="Export Mesh Replacement Done!")

        elif self.param == "CHECK_EXPORT":

            if chr_cache and utils.is_file_ext(chr_cache.import_type, "FBX"):
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
        if self.param == "EXPORT_MESH":
            export_format = "obj"
        elif self.param == "EXPORT_NON_STANDARD":
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
                elif self.param == "EXPORT_MESH":
                    if chr_cache:
                        default_file_path = chr_cache.import_name + "_mesh"
                    else:
                        default_file_path = "mesh"
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
            return "Export to / Save in Unity project.\n" \
                   "**Note: Non-rigified exports to Unity are exporting without animations, with a T-Pose only**"
        elif properties.param == "EXPORT_ACCESSORY":
            return "Export selected object(s) for import into CC3 as accessories"
        elif properties.param == "EXPORT_MESH":
            return "Export selected object as a mesh replacement. Use with Mesh > Replace Mesh, with the desired mesh to replace selected in CC4.\n" \
                   "**Mesh must have the same number of vertices as the original mesh to replace**"
        elif properties.param == "CHECK_EXPORT":
            return "Check for issues with the character for export. *Note* This will also test any selected objects as well as all objects attached to the character, as selected objects can also be exported with the character"
        return ""
