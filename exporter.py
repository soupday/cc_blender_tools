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

from . import (hik, rigging, rigutils, bake, shaders, physics, rigidbody, wrinkle, bones, modifiers,
               imageutils, meshutils, nodeutils, jsonutils, utils, params, vars)

UNPACK_INDEX = 1001


def get_export_armature(chr_cache, objects):
    arm = None
    if chr_cache:
        arm = chr_cache.get_armature()
        if arm:
            return arm

    arm = utils.get_armature_from_objects(objects)
    return arm

def check_valid_export_fbx(chr_cache, objects):
    report = []
    check_valid = True
    check_warn = False
    arm = get_export_armature(chr_cache, objects)

    standard = False
    if chr_cache:
        standard = chr_cache.is_standard()

    if not objects:
        message = f"ERROR: Nothing to export!"
        report.append(message)
        utils.log_warn(message)
        check_valid = False

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


def remove_modifiers_for_export(chr_cache, objects, reset_pose, rig=None):
    if not rig:
        rig = get_export_armature(chr_cache, objects)
    if not rig:
        return
    rig.data.pose_position = "POSE"
    obj : bpy.types.Object
    for obj in objects:
        if reset_pose:
            if obj.type == "MESH" and obj.data.shape_keys and obj.data.shape_keys.key_blocks:
                utils.safe_set_action(obj.data.shape_keys, None)
        if chr_cache:
            obj_cache = chr_cache.get_object_cache(obj)
            if obj_cache:
                if obj_cache.object_type == "OCCLUSION" or obj_cache.object_type == "TEARLINE" or obj_cache.object_type == "EYE":
                    mod : bpy.types.Modifier
                    for mod in obj.modifiers:
                        if vars.NODE_PREFIX in mod.name:
                            obj.modifiers.remove(mod)
    if reset_pose:
        utils.safe_set_action(rig, None)
        bones.clear_pose(rig)


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


def prep_export(context, chr_cache, new_name, objects, json_data, old_path, new_path,
                copy_textures, revert_duplicates, apply_fixes, as_blend_file, bake_values,
                materials=None, sync=False, force_bake=False):
    prefs = vars.prefs()

    if sync:
        revert_duplicates=False
        apply_fixes = False
        as_blend_file = False
        bake_values = True
        copy_textures = False

    bake_nodes = prefs.export_bake_nodes
    bake_bump_to_normal = prefs.export_bake_bump_to_normal
    if force_bake:
        bake_nodes = True
        bake_bump_to_normal = True

    utils.log_info(f"Prepping Export: {new_name}")

    if as_blend_file:
        if prefs.export_unity_remove_objects:
            # remove everything not part of the character for blend file exports.
            arm = get_export_armature(chr_cache, objects)
            for obj in bpy.data.objects:
                if not (obj == arm or obj.parent == arm or chr_cache.has_object(obj)):
                    utils.log_info(f"Removing {obj.name} from blend file")
                    bpy.data.objects.remove(obj)

    if not chr_cache or not json_data:
        return None

    objects_map = {}
    physics_map = {}
    mats_processed = {}
    images_processed = {}

    # old path might be blank, so try to use blend file path or export target path
    base_path = old_path
    if not base_path:
        base_path = utils.local_path()
        if not base_path:
            base_path = new_path

    # reset and unlock shape keys
    if not sync:
        utils.reset_shape_keys(objects)

    # update character name in json data
    old_name = chr_cache.get_character_id()
    if new_name != old_name:
        if (old_name in json_data.keys() and
            old_name in json_data[old_name]["Object"].keys() and
            new_name not in json_data.keys()):
            # rename the object and character keys
            json_data[old_name]["Object"][new_name] = json_data[old_name]["Object"].pop(chr_cache.get_character_id())
            json_data[new_name] = json_data.pop(old_name)

    chr_json = json_data[new_name]["Object"][new_name]

    # create soft physics json if none
    physics_json = jsonutils.add_json_path(chr_json, "Physics/Soft Physics/Meshes")

    # set custom JSON data
    json_data[new_name]["Blender_Project"] = True
    if not copy_textures:
        json_data[new_name]["Import_Dir"] = chr_cache.get_import_dir()
        json_data[new_name]["Import_Name"] = chr_cache.get_character_id()
    else:
        json_data[new_name].pop("Import_Dir", None)
        json_data[new_name].pop("Import_Name", None)

    if not chr_cache.link_id:
        chr_cache.link_id = utils.generate_random_id(20)
    json_data[new_name]["Link_ID"] = chr_cache.link_id

    if chr_cache.is_non_standard():
        set_non_standard_generation(json_data, new_name, chr_cache.non_standard_type, chr_cache.generation)

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
            mat_safe_name = utils.safe_export_name(utils.strip_name(mat_name), is_material=True)
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

    obj_names = []
    obj : bpy.types.Object
    for obj in objects:

        if not utils.object_exists_is_mesh(obj):
            continue

        utils.log_info(f"Object: {obj.name} / {obj.data.name}")
        utils.log_indent()

        obj_name = obj.name
        obj_cache = chr_cache.get_object_cache(obj)
        is_split = chr_cache.is_split_object(obj)
        split_source_name = obj_cache.source_name if (is_split and obj_cache) else None
        source_changed = False
        is_new_object = False

        if obj_cache and not is_split:
            obj_expected_source_name = utils.safe_export_name(utils.strip_name(obj_name))
            obj_source_name = obj_cache.source_name
            utils.log_info(f"Object source name: {obj_source_name}")
            source_changed = obj_expected_source_name != obj_source_name
            if source_changed:
                obj_safe_name = utils.safe_export_name(obj_name)
                utils.log_info(f"Object name changed from source, using: {obj_safe_name}")
            else:
                obj_safe_name = obj_source_name
        else:
            is_new_object = True
            obj_safe_name = utils.safe_export_name(obj_name, is_split=is_split)
            obj_source_name = obj_safe_name
            obj["rl_do_not_restore_name"] = True

        # if the Object name has been changed in some way
        if obj_name != obj_safe_name or obj.data.name != obj_safe_name:
            new_obj_name = obj_safe_name
            if is_new_object or source_changed or new_obj_name in obj_names:
                new_obj_name = utils.make_unique_name_in(obj_safe_name, bpy.data.objects.keys())
            elif new_obj_name in obj_names:
                # if multiple objects imported had the same name there will be duplicate source names:
                # so if the new name is already in use, create a new unique name
                # this will also trigger a new json object to be created which is needed
                # as json object names should be unique and it's not possible in Blender to export
                # two different objects with the same name.
                new_obj_name = utils.make_unique_name_in(obj_safe_name, bpy.data.objects.keys())
            utils.log_info(f"Using new safe Object & Mesh name: {obj_name} to {new_obj_name}")
            if source_changed:
                if jsonutils.rename_json_key(chr_json["Meshes"], obj_source_name, new_obj_name):
                    utils.log_info(f"Updating Object source json name: {obj_source_name} to {new_obj_name}")
                if physics_json and jsonutils.rename_json_key(physics_json, obj_source_name, new_obj_name):
                    utils.log_info(f"Updating Physics Object source json name: {obj_source_name} to {new_obj_name}")
                obj_source_name = new_obj_name
            if not sync:
                utils.force_object_name(obj, new_obj_name)
                utils.force_mesh_name(obj.data, new_obj_name)
            obj_name = new_obj_name
            obj_safe_name = new_obj_name

        obj_names.append(obj_name)

        # fetch or create the object json
        obj_json = jsonutils.get_object_json(chr_json, obj_source_name)
        physics_mesh_json = jsonutils.get_physics_mesh_json(physics_json, obj_source_name)
        if not obj_json:
            utils.log_info(f"Adding Object Json: {obj_name}")
            obj_json = copy.deepcopy(params.JSON_MESH_DATA)
            chr_json["Meshes"][obj_name] = obj_json
        if not physics_mesh_json and obj_cache and obj_cache.cloth_physics == "ON":
            utils.log_info(f"Adding Physics Object Json: {obj_name}")
            physics_mesh_json = copy.deepcopy(params.JSON_PHYSICS_MESH)
            physics_json[obj_name] = physics_mesh_json

        # store the json keys
        obj_key = jsonutils.get_object_json_key(chr_json, obj_json)
        objects_map.setdefault(obj_key, [])
        if physics_mesh_json:
            physics_mesh_key = jsonutils.get_physics_mesh_json_key(physics_json, physics_mesh_json)
            physics_map.setdefault(physics_mesh_key, [])

        for slot in obj.material_slots:
            mat = slot.material
            if mat is None: continue
            if materials and mat not in materials: continue
            mat_name = mat.name
            mat_cache = chr_cache.get_material_cache(mat)
            source_changed = False
            new_material = False

            utils.log_info(f"Material: {mat.name}")
            utils.log_indent()

            if mat.name not in mats_processed.keys():
                mats_processed[mat.name] = { "processed": False, "write_back": False, "copied": False, "remapped": False }
            mat_data = mats_processed[mat.name]

            if mat_cache:
                mat_expected_source_name = (utils.safe_export_name(utils.strip_name(mat_name), is_material=True)
                                            if revert_duplicates else
                                            utils.safe_export_name(mat_name, is_material=True))
                mat_source_name = mat_cache.source_name
                source_changed = mat_expected_source_name != mat_source_name
                if source_changed:
                    mat_safe_name = utils.safe_export_name(mat_name, is_material=True)
                else:
                    mat_safe_name = mat_source_name
            else:
                new_material = True
                mat_safe_name = utils.safe_export_name(mat_name, is_material=True)
                mat_source_name = mat_safe_name

            if mat_name != mat_safe_name:
                new_mat_name = mat_safe_name
                if new_material or source_changed:
                    new_mat_name = utils.make_unique_name_in(mat_safe_name, bpy.data.materials.keys())
                utils.log_info(f"Using new safe Material name: {mat_name} to {new_mat_name}")
                if source_changed:
                    if jsonutils.rename_json_key(obj_json["Materials"], mat_source_name, new_mat_name):
                        utils.log_info(f"Updating material json name: {mat_source_name} to {new_mat_name}")
                    if physics_mesh_json and jsonutils.rename_json_key(physics_mesh_json["Materials"], mat_source_name, new_mat_name):
                        utils.log_info(f"Updating physics material json name: {mat_source_name} to {new_mat_name}")
                if not sync:
                    utils.force_material_name(mat, new_mat_name)
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

            # the object and materials may have been split from it's origin,
            # so try to find the material in the source object json
            if obj_cache and mat_cache and not mat_json and split_source_name:
                split_obj_json = jsonutils.get_object_json(chr_json, split_source_name)
                if split_obj_json:
                    split_mat_json = jsonutils.get_material_json(split_obj_json, mat_source_name)
                    if split_mat_json:
                        utils.log_info(f"Copying Material Json: {mat_safe_name} from split source material: {split_source_name} / {mat_source_name}")
                        mat_json = copy.deepcopy(split_mat_json)
                if mat_json:
                    obj_json["Materials"][mat_safe_name] = mat_json
                    write_json = True
                    write_textures = True

            # then look for same material in source character objects
            if mat_cache and not mat_json:
                for other_obj_cache in chr_cache.object_cache:
                    other = other_obj_cache.get_object()
                    if utils.object_exists_is_mesh(other):
                        if mat.name in other.data.materials:
                            other_source_name = other_obj_cache.source_name
                            other_obj_json = jsonutils.get_object_json(chr_json, other_source_name)
                            if other_obj_json:
                                other_mat_json = jsonutils.get_material_json(other_obj_json, mat_source_name)
                                if other_mat_json:
                                    utils.log_info(f"Copying Material Json: {mat_safe_name} from existing material Json in Obj: {other_source_name} / {mat_source_name}")
                                    mat_json = copy.deepcopy(other_mat_json)
                                    break
                if mat_json:
                    obj_json["Materials"][mat_safe_name] = mat_json
                    write_json = True
                    write_textures = True

            # finally try to find a mat_json of the same shader type
            # with the same source material name in any mesh in the json
            if mat_cache and not mat_json:
                for o_json_name, o_json in chr_json["Meshes"].items():
                    for m_json_name, m_json in o_json["Materials"].items():
                        if m_json_name.lower() == mat_source_name.lower():
                            shader_name = params.get_rl_shader_name(mat_cache)
                            m_shader_name = jsonutils.get_custom_shader(m_json)
                            if shader_name == m_shader_name:
                                utils.log_info(f"Copying Material Json: {mat_safe_name} from existing material Json of same name and type: {o_json_name} / {m_json_name}")
                                mat_json = copy.deepcopy(m_json)
                                break
                    if mat_json:
                        break
                if mat_json:
                    obj_json["Materials"][mat_safe_name] = mat_json
                    write_json = True
                    write_textures = True

            # if still no json, try to create the material json data from the mat_cache shader def
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

            # store the json keys
            mat_key = jsonutils.get_material_json_key(obj_json, mat_json)
            objects_map[obj_key].append(mat_key)
            if physics_mat_json:
                physics_mat_key = jsonutils.get_physics_material_json_key(physics_mesh_json, physics_mat_json)
                physics_map[physics_mesh_key].append(physics_mat_key)

            if mat_cache:
                utils.log_info("Writing Json:")
                utils.log_indent()
                # update the json parameters with any changes
                if write_textures:
                    write_back_textures(context, mat_json, mat, mat_cache, base_path, old_name, bake_values, mat_data,
                                        bake_nodes, bake_bump_to_normal, images_processed)
                if write_json:
                    write_back_json(mat_json, mat, mat_cache)
                if write_physics_json:
                    # there isn't a meaningful way to convert between Blender physics and RL PhysX
                    pass
                if write_physics_textures:
                    write_back_physics_weightmap(physics_mat_json, obj, mat, mat_cache, base_path, old_name, mat_data)
                if not sync and revert_duplicates:
                    # replace duplicate materials with a reference to a single source material
                    # (this is to ensure there are no duplicate suffixes in the fbx export)
                    if mat_count[mat_safe_name] > 1:
                        new_mat = mat_remap[mat_safe_name]
                        slot.material = new_mat
                        mat = new_mat
                        mat_name = new_mat.name
                    if mat_name != mat_safe_name:
                        utils.log_info(f"Reverting material name: {mat_name} to {mat_safe_name}")
                        utils.force_material_name(mat, mat_safe_name)
                utils.log_recess()
            else:
                # add pbr material to json for non-cached base object/material
                write_pbr_material_to_json(context, mat, mat_json, base_path, old_name, bake_values)

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
                if "Wrinkle" in mat_json.keys():
                    for channel in mat_json["Wrinkle"]["Textures"].keys():
                        copy_and_update_texture_path(mat_json["Wrinkle"]["Textures"][channel], "Texture Path", old_path, new_path, old_name, new_name, as_blend_file, mat_name, mat_data, images_copied)

            else:
                for channel in mat_json["Textures"].keys():
                    remap_texture_path(mat_json["Textures"][channel], "Texture Path", old_path, new_path, mat_data)
                if "Custom Shader" in mat_json.keys():
                    for channel in mat_json["Custom Shader"]["Image"].keys():
                        remap_texture_path(mat_json["Custom Shader"]["Image"][channel], "Texture Path", old_path, new_path, mat_data)
                if physics_mat_json:
                    remap_texture_path(physics_mat_json, "Weight Map Path", old_path, new_path, mat_data)
                if "Wrinkle" in mat_json.keys():
                    for channel in mat_json["Wrinkle"]["Textures"].keys():
                        remap_texture_path(mat_json["Wrinkle"]["Textures"][channel], "Texture Path", old_path, new_path, mat_data)

            mat_data["processed"] = True
            # texure paths
            utils.log_recess()

            # material
            utils.log_recess()

        # object
        utils.log_recess()

    if apply_fixes and prefs.export_legacy_bone_roll_fix:
        if obj.type == "ARMATURE":
            if utils.object_mode():
                utils.set_active_object(obj)
                if utils.set_mode("EDIT"):
                    utils.log_info("Applying upper and lower teeth bones roll fix.")
                    bone = obj.data.edit_bones["CC_Base_Teeth01"]
                    bone.roll = 0
                    bone = obj.data.edit_bones["CC_Base_Teeth02"]
                    bone.roll = 0
                    utils.object_mode()

    if sync:
        # find all mesh/material keys not used
        meshes_json = jsonutils.get_json(json_data, f"{new_name}/Object/{new_name}/Meshes")
        del_keys = []
        for obj_key in objects_map:
            mat_keys = objects_map[obj_key]
            obj_json = jsonutils.get_json(json_data, f"{new_name}/Object/{new_name}/Meshes/{obj_key}")
            for key in obj_json["Materials"]:
                if key not in mat_keys:
                    utils.log_detail(f"Removing: material {obj_key}/{key}")
                    del_keys.append((obj_json["Materials"], key))
        for key in meshes_json:
            if key not in objects_map:
                utils.log_detail(f"Removing: object {key}")
                del_keys.append((meshes_json, key))
        # find all physics mesh/material keys not used
        physics_meshes_json = jsonutils.get_json(json_data, f"{new_name}/Object/{new_name}/Physics/Soft Physics/Meshes")
        for physics_mesh_key in physics_map:
            physics_mat_keys = physics_map[physics_mesh_key]
            physics_mesh_json = jsonutils.get_json(json_data, f"{new_name}/Object/{new_name}/Physics/Soft Physics/Meshes/{physics_mesh_key}")
            for key in physics_mesh_json["Materials"]:
                if key not in physics_mat_keys:
                    utils.log_detail(f"Removing: physics material {physics_mesh_key}/{key}")
                    del_keys.append((physics_mesh_json["Materials"], key))
        for key in physics_meshes_json:
            if key not in physics_map:
                utils.log_detail(f"Removing: physics object {key}")
                del_keys.append((physics_meshes_json, key))
        # remove the keys
        for dictionary, key in del_keys:
            if key in dictionary:
                del(dictionary[key])


    # as the baking system can deselect everything, reselect the export objects here.
    utils.try_select_objects(objects, True)


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
            utils.log_info(f"Remapping JSON texture path to: {tex_info[path_key]}")
    return


def copy_and_update_texture_path(tex_info, path_key, old_path, new_path, old_name, new_name, as_blend_file, mat_name, mat_data, images_copied):
    """keep the same relative folder structure and copy the textures to their target folder.
       update the images in the blend file with the new location."""

    # at this point all the image paths have been re-written as absolute paths
    sep = os.path.sep
    old_tex_base = os.path.join(old_path, f"textures{sep}{old_name}")
    old_fbm_base = os.path.join(old_path, f"{old_name}.fbm")

    if path_key in tex_info.keys():

        tex_path : str = tex_info[path_key]
        if tex_path:

            if not os.path.isabs(tex_path):
                tex_path = os.path.normpath(os.path.join(old_path, tex_path))

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

                utils.log_info(f"Remapping JSON texture path to: {new_rel_path}")

            else:

                # otherwise put the textures in folders in the textures/CHARACTER_NAME/Extras/MATERIAL_NAME/ folder
                dir, file = os.path.split(tex_path)
                extras_dir = f"textures{sep}{new_name}{sep}Extras{sep}{mat_name}"
                new_rel_path = os.path.normpath(os.path.join(extras_dir, file))
                new_abs_path = os.path.normpath(os.path.join(new_path, new_rel_path))

                utils.log_info(f"Setting JSON texture path to: {new_rel_path}")

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
            utils.force_object_name(obj, info[2])
            if obj.type == "MESH" and obj.data:
                utils.force_mesh_name(obj.data, info[3])
            if obj.type == "ARMATURE" and obj.data:
                utils.force_armature_name(obj.data, info[3])
        elif op == "MATERIAL_RENAME":
            mat = info[1]
            utils.force_material_name(mat, info[2])
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


def write_back_textures(context, mat_json: dict, mat, mat_cache, base_path, old_name, bake_values, mat_data,
                        bake_nodes, bake_bump_to_normal, images_processed):
    global UNPACK_INDEX
    prefs = vars.prefs()

    if mat_json is None:
        return

    shader_name = params.get_shader_name(mat_cache)
    rl_shader_name = params.get_rl_shader_name(mat_cache)
    shader_def = params.get_shader_def(shader_name)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader_name)
    has_custom_shader = "Custom Shader" in mat_json.keys()

    unpack_path = os.path.join(base_path, "textures", old_name, "Unpack")
    bake_path = os.path.join(base_path, "textures", old_name, "Baked")
    custom_path = os.path.join(base_path, "textures", old_name, "Custom")

    bake.init_bake()
    UNPACK_INDEX = 1001

    # determine if we are combining bump maps into normal maps:
    normal_socket = params.get_shader_texture_socket(shader_def, "NORMAL")
    bump_socket = params.get_shader_texture_socket(shader_def, "BUMP")
    normal_connected = normal_socket and nodeutils.has_connected_input(shader_node, normal_socket)
    bump_combining = False
    if bake_bump_to_normal and bake_nodes:
        bump_combining = normal_connected and bump_socket and nodeutils.has_connected_input(shader_node, bump_socket)

    if shader_def and shader_node:

        if "textures" in shader_def.keys():

            for tex_def in shader_def["textures"]:
                tex_type = tex_def[2]
                shader_socket = tex_def[0]
                tex_id = params.get_texture_json_id(tex_type)
                is_pbr_texture = tex_type in params.PBR_TYPES
                is_pbr_shader = shader_name == "rl_pbr_shader" or shader_name == "rl_sss_shader"
                tex_node = nodeutils.get_node_connected_to_input(shader_node, shader_socket)

                tex_info = None
                bake_value_texture = False
                bake_shader_socket = ""
                bake_value_size = 64

                roughness_modified = False
                if tex_type == "ROUGHNESS":
                    roughness = 0.5
                    if not nodeutils.has_connected_input(shader_node, "Roughness Map"):
                        roughness = nodeutils.get_node_input_value(shader_node, "Roughness Map", 0.5)
                    def_min = 0
                    def_max = 1
                    def_pow = 1
                    #if shader_name == "rl_sss_shader":
                    #    def_pow = 0.75
                    roughness_min = nodeutils.get_node_input_value(shader_node, "Roughness Min", def_min)
                    roughness_max = nodeutils.get_node_input_value(shader_node, "Roughness Max", def_max)
                    roughness_pow = nodeutils.get_node_input_value(shader_node, "Roughness Power", def_pow)
                    if roughness_min != def_min or roughness_max != def_max or roughness != 0.5:
                        roughness_modified = True

                # find or generate tex_info json.
                if is_pbr_texture:

                    # CC3 cannot set metallic or roughness values without textures, so must bake a small value texture
                    if not tex_node:

                        if tex_type == "DIFFUSE":
                            if bake_values:
                                bake_value_texture = True
                                bake_shader_socket = "Base Color"

                        if tex_type == "ROUGHNESS":
                            if bake_values and roughness_modified:
                                bake_value_texture = True
                                bake_shader_socket = "Roughness"
                            elif not bake_values:
                                mat_json["Roughness_Value"] = roughness

                        elif tex_type == "METALLIC":
                            metallic = nodeutils.get_node_input_value(shader_node, "Metallic Map", 0)
                            if bake_values and metallic > 0:
                                bake_value_texture = True
                                bake_shader_socket = "Metallic"
                            elif not bake_values:
                                mat_json["Metallic_Value"] = metallic

                    # fetch the tex_info data for the channel
                    if tex_id in mat_json["Textures"]:
                        tex_info = mat_json["Textures"][tex_id]

                    # or create a new tex_info if missing or baking a new texture
                    elif tex_node or bake_value_texture:
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
                        processed_image = mat_data[tex_type]
                        if processed_image:
                            utils.log_info(f"Reusing already processed material image: {processed_image.name}")

                    if tex_node or bake_value_texture:

                        image : bpy.types.Image = None

                        # re-use the already processed image if available
                        if processed_image:
                            image = processed_image

                        else:

                            # if it needs a value texture, bake the value
                            if bake_value_texture:

                                # turn off ao for diffuse bakes
                                if tex_type == "DIFFUSE":
                                    ao = nodeutils.get_node_input_value(shader_node, "AO Strength", 1.0)
                                    nodeutils.set_node_input_value(shader_node, "AO Strength", 0)

                                image = bake.bake_node_socket_input(context, bsdf_node, bake_shader_socket,
                                                                    mat, tex_id, bake_path,
                                                                    override_size=bake_value_size)

                                if tex_type == "DIFFUSE":
                                    ao = nodeutils.get_node_input_value(shader_node, "AO Strength", ao)

                            elif nodeutils.is_texture_pack_system(tex_node):

                                utils.log_info(f"Texture: {tex_id} for socket: {shader_socket} is connected to a texture pack. Skipping.")
                                continue

                            elif wrinkle.is_wrinkle_system(tex_node):

                                utils.log_info(f"Texture: {tex_id} for socket: {shader_socket} is connected to the wrinkle shader. Skipping.")
                                continue

                            # if there is an image texture link to the socket
                            elif tex_node and tex_node.type == "TEX_IMAGE":

                                # bake roughnesss min/max adjustments (but not power)
                                if tex_type == "ROUGHNESS" and roughness_modified:
                                    roughness_pow = nodeutils.get_node_input_value(shader_node, "Roughness Power", def_pow)
                                    nodeutils.set_node_input_value(shader_node, "Roughness Power", 1.0)
                                    image = bake.bake_node_socket_input(context, bsdf_node, "Roughness",
                                                                        mat, tex_id, bake_path,
                                                                        size_override_node=shader_node,
                                                                        size_override_socket="Roughness Map")
                                    nodeutils.set_node_input_value(shader_node, "Roughness Power", roughness_pow)

                                # if there is a normal and a bump map connected, combine into a normal
                                elif bake_nodes and tex_type == "NORMAL" and bump_combining:
                                    image = bake.bake_rl_bump_and_normal(context, shader_node, bsdf_node,
                                                                         mat, tex_id, bake_path,
                                                                         normal_socket_name=shader_socket,
                                                                         bump_socket_name=bump_socket)

                                # otherwise use the image texture
                                else:
                                    image = tex_node.image

                            elif bake_nodes:

                                # if something is connected to the shader socket but is not a texture image
                                # and baking is enabled: then bake the socket input into a texture for exporting:
                                if tex_type == "NORMAL" and bump_combining:
                                    image = bake.bake_rl_bump_and_normal(context, shader_node, bsdf_node, mat, tex_id, bake_path,
                                                                         normal_socket_name = shader_socket,
                                                                         bump_socket_name = bump_socket)
                                else:

                                    utils.log_info(f"Baking Socket Input: {shader_node.name} {shader_socket}")
                                    image = bake.bake_node_socket_input(context, shader_node, shader_socket,
                                                                        mat, tex_id, bake_path)

                        tex_info["Texture Path"] = ""
                        mat_data[tex_type] = image

                        if image:

                            try_unpack_image(image, unpack_path, True)

                            if not image.filepath:
                                try:
                                    # image is not saved?
                                    if image.file_format:
                                        format = image.file_format
                                    else:
                                        format = "PNG"
                                    imageutils.save_image_to_format_dir(image, format, custom_path, image.name)
                                except:
                                    utils.log_warn(f"Unable to save unsaved image: {image.name} to custom image dir!")

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

                    elif not tex_node:
                        tex_info["Texture Path"] = ""


            mat_data["write_back"] = True


def write_back_physics_weightmap(physics_mat_json : dict, obj, mat, mat_cache, base_path, old_name, mat_data):
    global UNPACK_INDEX
    prefs = vars.prefs()

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
    prefs = vars.prefs()

    unpack_folder = None
    if chr_cache:
        unpack_folder = os.path.join(base_path, "textures", chr_cache.get_character_id(), "Unpack")
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
                    if mat is None: continue
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


def get_export_objects(chr_cache, include_selected = True, only_objects=None):
    """Fetch all the objects in the character (or try to)"""
    collider_collection = rigidbody.get_rigidbody_collider_collection()
    objects = []
    selected = bpy.context.selected_objects.copy()

    if chr_cache:
        arm = chr_cache.get_armature()
        if arm:
            utils.unhide(arm)
            if arm not in objects:
                objects.append(arm)
            chr_objects = chr_cache.get_cache_objects()
            for obj in chr_objects:
                obj_cache = chr_cache.get_object_cache(obj)
                if obj_cache.is_mesh() and not obj_cache.disabled:
                    if obj.parent == arm:
                        utils.unhide(obj)
                        if obj not in objects:
                            utils.log_info(f"   Found Character Object: {obj.name}")
                            objects.append(obj)

            child_objects = utils.get_child_objects(arm)
            for obj in child_objects:
                if utils.object_exists_is_mesh(obj):
                    # add child mesh objects
                    if obj not in objects:
                        utils.log_info(f"   Found Child Mesh Object: {obj.name}")
                        objects.append(obj)
                elif utils.object_exists_is_empty(obj):
                    utils.log_info(f"   Found Child Empty Transform: {obj.name}")
                    objects.append(obj)

    else:
        arm = utils.get_armature_from_objects(objects)
        if arm:
            utils.unhide(arm)
            if arm not in objects:
                objects.append(arm)
            utils.log_info(f"Character Armature: {arm.name}")
            child_objects = utils.get_child_objects(arm)
            for obj in child_objects:
                if utils.object_exists_is_mesh(obj):
                    if obj not in objects:
                        utils.log_info(f"   Found Child Object: {obj.name}")
                        objects.append(obj)
                elif utils.object_exists_is_empty(obj):
                    utils.log_info(f"   Found Child Empty Transform: {obj.name}")
                    objects.append(obj)

    # include selected objects last
    if include_selected:
        for obj in selected:
            if obj not in objects:
                objects.append(obj)

    # exclude non-exportable objects
    to_remove = []
    for obj in objects:
        # exclude rigid body colliders (parented to armature)
        if collider_collection and obj.name in collider_collection.objects:
            utils.log_info(f"   Excluding Rigidbody Collider Object: {obj.name}")
            to_remove.append(obj)
            continue
        # exclude collider proxies
        if chr_cache and chr_cache.is_collision_object(obj):
            utils.log_info(f"   Excluding Collider Proxy Object: {obj.name}")
            to_remove.append(obj)
            continue
        # exclude sculpt objects
        if chr_cache and chr_cache.is_sculpt_object(obj):
            utils.log_info(f"   Excluding Sculpt Object: {obj.name}")
            to_remove.append(obj)
            continue
    for o in to_remove:
        objects.remove(o)

    # make sure all export objects are valid
    clean_objects = [ obj for obj in objects
                        if utils.object_exists(obj) and
                            (obj == arm or obj.type == "MESH" or obj.type == "EMPTY") ]

    if only_objects:
        to_remove = [ o for o in clean_objects if o not in only_objects ]
        for o in to_remove:
            clean_objects.remove(o)

    for obj in clean_objects:
        utils.log_info(f"Export Object: {obj.name} ({obj.type})")

    return clean_objects


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
            if chr_json:
                chr_json["Bind_Pose"] = "APose"
            return True
        if chr_json:
            chr_json["Bind_Pose"] = "TPose"
    return False


def clear_animation_data(obj: bpy.types.Object):
    if obj.type == "ARMATURE" or obj.type == "MESH":
        # remove action
        utils.safe_set_action(obj, None)
        # remove strips
        # this removes drivers too...
        #obj.animation_data_clear()
        ad = obj.animation_data
        if ad:
            while ad.nla_tracks:
                ad.nla_tracks.remove(ad.nla_tracks[0])
    if obj.type == "MESH":
        # remove shape key action
        utils.safe_set_action(obj.data.shape_keys, None)
        # remove shape key strips
        if obj.data.shape_keys and obj.data.shape_keys.animation_data:
            obj.data.shape_keys.animation_data_clear()
            ad = obj.data.shape_keys.animation_data
            if ad:
                while ad.nla_tracks:
                    ad.nla_tracks.remove(ad.nla_tracks[0])


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

        bones.select_all_bones(arm, select=True, clear_active=True)

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
        set_standard_generation(json_data, name, chr_cache.generation)
    else:
        set_non_standard_generation(json_data, name, chr_cache.non_standard_type, chr_cache.generation)


def set_non_standard_generation(json_data, character_id, character_type, generation):
    RL_HUMANOID_GENERATIONS = [
        "ActorCore", "ActorBuild", "ActorScan", "AccuRig", "GameBase"
    ]
    if character_type == "HUMANOID":
        if generation not in RL_HUMANOID_GENERATIONS:
            generation = "Humanoid"
    elif character_type == "CREATURE":
        generation = "Creature"
    elif character_type == "PROP":
        generation = "Prop"
    else:
        generation = "Unknown"

    utils.log_info(f"Generation: {generation}")
    jsonutils.set_character_generation_json(json_data, character_id, generation)


def set_standard_generation(json_data, character_id, generation):
    # currently is doesn't really matter what the standard generation string is
    # generation in the CC4 plugin is only used to detect non-standard characters.
    jsonutils.set_character_generation_json(json_data, character_id, generation)


def prep_non_standard_export(context, objects, dir, name, character_type):
    global UNPACK_INDEX
    bake.init_bake()
    UNPACK_INDEX = 5001

    # prefer to bake and unpack textures next to blend file, otherwise at the destination.
    blend_path = utils.local_path()
    if blend_path:
        dir = blend_path
    utils.log_info(f"Texture Root Dir: {dir}")

    json_data = jsonutils.generate_character_base_json_data(name)

    set_non_standard_generation(json_data, name, character_type, "Unknown")

    done = {}
    objects_json = json_data[name]["Object"][name]["Meshes"]

    for obj in objects:

        if obj.type == "MESH" and obj not in done.keys():

            utils.log_info(f"Adding Object Json: {obj.name}")
            export_name = utils.safe_export_name(obj.name)

            if export_name != obj.name:
                utils.log_info(f"Updating Object name: {obj.name} to {export_name}")
                obj.name = export_name

            mesh_json = copy.deepcopy(params.JSON_MESH_DATA)
            done[obj] = mesh_json
            objects_json[obj.name] = mesh_json

            for slot in obj.material_slots:

                mat = slot.material
                if mat is None: continue

                if mat not in done.keys():

                    utils.log_info(f"Adding Material Json: {mat.name}")

                    export_name = utils.safe_export_name(mat.name, is_material=True)
                    if export_name != mat.name:
                        utils.log_info(f"Updating Material name: {mat.name} to {export_name}")
                        mat.name = export_name

                    mat_json = copy.deepcopy(params.JSON_PBR_MATERIAL)
                    done[mat] = mat_json

                    mesh_json["Materials"][mat.name] = mat_json

                    write_pbr_material_to_json(context, mat, mat_json, dir, name, True)

                else:

                    mesh_json["Materials"][mat.name] = done[mat]

    # select all the export objects
    utils.try_select_objects(objects, True)

    return json_data

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

def write_pbr_material_to_json(context, mat, mat_json, path, name, bake_values):
    if not mat.node_tree or not mat.node_tree.nodes:
        return

    unpack_path = os.path.join(path, "textures", name, "Unpack")
    bake_path = os.path.join(path, "textures", name, "Baked")
    bsdf_node = nodeutils.get_bsdf_node(mat)
    gltf_node = nodeutils.find_node_group_by_keywords(mat.node_tree.nodes, "glTF Settings", "glTF Material Output")

    if bsdf_node:
        try:
            base_color_socket = nodeutils.input_socket(bsdf_node, "Base Color")
            clearcoat_socket = nodeutils.input_socket(bsdf_node, "Clearcoat")
            roughness_socket = nodeutils.input_socket(bsdf_node, "Roughness")
            metallic_socket = nodeutils.input_socket(bsdf_node, "Metallic")
            specular_socket = nodeutils.input_socket(bsdf_node, "Specular")
            alpha_socket = nodeutils.input_socket(bsdf_node, "Alpha")
            emission_socket = nodeutils.input_socket(bsdf_node, "Emission")
            emission_strength_socket = nodeutils.input_socket(bsdf_node, "Emission Strength")

            roughness_value = roughness_socket.default_value
            metallic_value = metallic_socket.default_value
            bake_roughness = False
            bake_metallic = False
            specular_value = specular_socket.default_value
            diffuse_color = (1,1,1,1)
            alpha_value = 1.0
            if not base_color_socket.is_linked:
                diffuse_color = base_color_socket.default_value
            if not alpha_socket.is_linked:
                alpha_value = alpha_socket.default_value
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


        write_or_bake_tex_data_to_json(context, socket_mapping, mat, mat_json, bsdf_node, path, bake_path, unpack_path)

    else:
        # if there is no BSDF shader node, try to match textures by name (both image node name and image name)
        socket_mapping = {}
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                for tex_id in BSDF_TEXTURE_KEYWORDS:
                    for key in BSDF_TEXTURE_KEYWORDS[tex_id]:
                        if re.match(key, node.image.name.lower()) or re.match(key, node.label.lower()) or re.match(key, node.name.lower()):
                            socket_mapping[tex_id] = [node, "Color", False, 100.0]

        write_or_bake_tex_data_to_json(context, socket_mapping, mat, mat_json, None, path, bake_path, unpack_path)

    return


def write_or_bake_tex_data_to_json(context, socket_mapping, mat, mat_json, bsdf_node, path, bake_path, unpack_path):

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

        node, socket_name, bake_value, strength = socket_mapping[tex_id]
        socket = nodeutils.input_socket(node, socket_name)
        utils.log_info(f"Adding Texture Channel: {tex_id} strength - {strength}")

        tex_node = None
        image = None
        if node.type == "TEX_IMAGE":
            tex_node = node
            image = node.image
            try_unpack_image(image, unpack_path, True)

        else:
            if tex_id == "Normal" and combine_normals:
                image = bake.bake_bsdf_normal(context, bsdf_node, mat, tex_id, bake_path)
            else:
                if bake_value:
                    image = bake.pack_value_image(socket.default_value, mat, tex_id, bake_path)
                else:
                    image = bake.bake_node_socket_output(context, node, socket, mat, tex_id, bake_path)

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


def update_facial_profile_json(chr_cache, all_objects, json_data, chr_name):

    # for standard characters, ignore clothing, accessories and hair objects
    objects = []
    if chr_cache:
        for obj in all_objects:
            if utils.object_exists_is_mesh(obj):
                obj_cache = chr_cache.get_object_cache(obj)
                if obj_cache and (obj_cache.object_type == "DEFAULT" or
                    obj_cache.object_type == "HAIR"):
                    continue
                objects.append(obj)

    # non-standard characters, consider everything
    else:
        for obj in all_objects:
            if utils.object_exists_is_mesh(obj):
                objects.append(obj)

    categories_json = jsonutils.get_facial_profile_categories_json(json_data, chr_name)
    new_categories = {}
    done_shapes = []

    # cull existing facial expressions
    if categories_json:
        for category in categories_json.keys():
            new_shapes = []
            new_categories[category] = new_shapes
            shape_names = categories_json[category]
            for shape_name in shape_names:
                if shape_name not in done_shapes:
                    if meshutils.objects_have_shape_key(objects, shape_name):
                        new_shapes.append(shape_name)
                        done_shapes.append(shape_name)

    # add visemes
    visemes = []
    VISEME_NAMES = meshutils.get_viseme_profile(objects)
    for viseme_name in VISEME_NAMES:
        if viseme_name not in done_shapes:
            if meshutils.objects_have_shape_key(objects, viseme_name):
                visemes.append(viseme_name)
                done_shapes.append(viseme_name)
    if visemes:
        new_categories["Visemes"] = visemes

    # all remaining shapes go into custom expressions
    custom = []
    for obj in objects:
        if obj.type == "MESH" and obj.data.shape_keys:
            i = 0
            for key_block in obj.data.shape_keys.key_blocks:
                shape_name = key_block.name
                # ignore tearline and eye occlusion adjustment shape keys (these are not facial expressions)
                if chr_cache and (shape_name.startswith("TL ") or shape_name.startswith("EO ")):
                    continue
                if i > 0 and shape_name not in done_shapes:
                    custom.append(shape_name)
                    done_shapes.append(shape_name)
                i += 1
    if custom:
        new_categories["Custom"] = custom

    # apply changes
    jsonutils.set_facial_profile_categories_json(json_data, chr_name, new_categories)


def export_copy_asset_file(chr_cache, dir, name, ext, old_path=None):
    try:
        try_paths = [
            old_path,
            os.path.join(chr_cache.get_import_dir(), chr_cache.get_character_id() + ext),
            utils.local_path(chr_cache.get_character_id() + ext),
        ]
        for old_path in try_paths:
            if old_path and os.path.exists(old_path):
                new_path = os.path.join(dir, name + ext)
                if not utils.is_same_path(new_path, old_path):
                    utils.log_info(f"Copying {ext} file: {old_path} to: {new_path}")
                    shutil.copyfile(old_path, new_path)
                return os.path.relpath(new_path, dir)
    except Exception as e:
        utils.log_error(f"Unable to copy {ext} file: {old_path} to: {new_path}", e)
    return None


def is_arp_installed():
    try:
        bl_options = bpy.ops.arp.arp_export_fbx_panel.bl_options
        if bl_options is not None:
            utils.log_info("ARP is installed.")
            return True
        else:
            utils.log_info("ARP is NOT installed.")
            return False
    except:
        utils.log_info("ARP is NOT installed.")
        return False


def is_arp_rig(rig):
    if utils.object_exists_is_armature(rig):
        if "c_pos" in rig.data.bones and "c_traj" in rig.data.bones and "c_root.x" in rig.data.bones:
            utils.log_info("Rig is ARP")
            return True
    utils.log_info("Rig is NOT ARP")
    return False


def export_arp(file_path, arm, objects):
    utils.log_info("Attempting to export ARP rig...")
    try:
        bpy.data.scenes["Scene"].arp_engine_type = "UNITY"
        bpy.data.scenes["Scene"].arp_export_rig_type = "HUMANOID"
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
        bpy.ops.arp.arp_export_fbx_panel(filepath=file_path, check_existing = False)
        return True
    except Exception as e:
        utils.log_info(f"ARP export failed: {str(e)}")
        return False


def obj_export(file_path, use_selection=False, use_animation=False, global_scale=100,
                          use_vertex_colors=False, use_vertex_groups=False, apply_modifiers=True,
                          keep_vertex_order=False, use_materials=False):
    if utils.B330():
        bpy.ops.wm.obj_export(filepath=file_path,
                              global_scale=global_scale,
                              export_selected_objects=use_selection,
                              export_animation=use_animation,
                              export_materials=use_materials,
                              export_colors=use_vertex_colors,
                              export_vertex_groups=use_vertex_groups,
                              apply_modifiers=apply_modifiers)
    else:
        bpy.ops.export_scene.obj(filepath=file_path,
                                 global_scale=global_scale,
                                 use_selection=use_selection,
                                 use_materials=use_materials,
                                 use_animation=use_animation,
                                 use_vertex_groups=use_vertex_groups,
                                 use_mesh_modifiers=apply_modifiers,
                                 keep_vertex_order=keep_vertex_order)


def export_standard(self, context, chr_cache, file_path, include_selected):
    """Exports standard character (not rigified, not generic) to CC3/4 with json data,
       texture paths are relative to source character, as an .fbx file.
    """

    props = vars.props()
    prefs = vars.prefs()

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Exporting Character Model to CC:")
    utils.log_info("--------------------------------")

    utils.object_mode()

    chr_cache.check_paths()

    export_anim = False
    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    # store mode state
    mode_selection_state = utils.store_mode_selection_state()
    rv_state = utils.store_render_visibility_state()

    utils.log_info("Export to: " + file_path)
    utils.log_info("Exporting as: " + ext)

    if utils.is_file_ext(ext, "FBX"):

        json_data = chr_cache.get_json_data()
        if not json_data:
            json_data = jsonutils.generate_character_base_json_data(name)
            set_character_generation(json_data, chr_cache, name)

        # export objects
        objects = get_export_objects(chr_cache, include_selected)
        arm = get_export_armature(chr_cache, objects)

        # store states and settings
        armature_settings = bones.store_armature_settings(arm, include_pose=True)
        object_state = utils.store_object_state(objects)

        # restore quaternion rotation modes
        rigutils.reset_rotation_modes(arm)

        utils.log_info("Preparing character for export:")
        utils.log_indent()

        # avatar's should be exported back to CC4 in rest pose.
        # props should be exported back with animation.
        use_rest_pose = chr_cache.is_avatar()
        remove_modifiers_for_export(chr_cache, objects, use_rest_pose)

        revert_duplicates = prefs.export_legacy_revert_material_names
        prep_export(context, chr_cache, name, objects, json_data, chr_cache.get_import_dir(),
                    dir, self.include_textures, revert_duplicates, True, False, True)

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
                    bake_anim_simplify_factor=self.animation_simplify,
                    add_leaf_bones = False,
                    mesh_smooth_type = ("FACE" if self.export_face_smoothing else "OFF"),
                    use_mesh_modifiers = False)

        utils.log_recess()
        utils.log_info("")
        utils.log_info("Copying Fbx Key.")

        export_copy_asset_file(chr_cache, dir, name, ".fbxkey", chr_cache.get_import_key_file())
        hik_path = export_copy_asset_file(chr_cache, dir, name, ".3dxProfile")
        fac_path = export_copy_asset_file(chr_cache, dir, name, ".ccFacialProfile")
        if hik_path:
            jsonutils.set_json(json_data, "HIK/Profile_Path", hik_path)
        if fac_path:
            jsonutils.set_json(json_data, "Facial_Profile/Profile_Path", fac_path)

        utils.log_info("Writing Json Data.")

        # write HIK profile for VRM
        if chr_cache and chr_cache.is_import_type("VRM"):
            hik_path = os.path.join(dir, name + ".3dxProfile")
            if hik.generate_hik_profile(arm, name, hik_path, hik.VRM_HIK_PROFILE_TEMPLATE):
                if json_data:
                    json_data[name]["HIK"] = {}
                    json_data[name]["HIK"]["Profile_Path"] = os.path.relpath(hik_path, dir)

        if json_data:
            update_facial_profile_json(chr_cache, objects, json_data, name)
            new_json_path = os.path.join(dir, name + ".json")
            jsonutils.write_json(json_data, new_json_path)

        # restore states and settings
        utils.restore_object_state(object_state)
        bones.restore_armature_settings(arm, armature_settings, include_pose=True)

        restore_modifiers(chr_cache, objects)

    else:

        # don't bring anything else with an obj morph export
        bpy.ops.object.select_all(action='DESELECT')

        # select all the imported objects (should be just one)
        for p in chr_cache.object_cache:
            if p.object is not None and p.object.type == "MESH" and not p.disabled:
                utils.unhide(p.object)
                p.object.select_set(True)

        obj_export(file_path, use_selection=True,
                              global_scale=100,
                              use_materials=False,
                              keep_vertex_order=True,
                              use_vertex_colors=True,
                              use_vertex_groups=True,
                              apply_modifiers=True)

        #export_copy_obj_key(chr_cache, dir, name)
        export_copy_asset_file(chr_cache, dir, name, ".ObjKey", chr_cache.get_import_key_file())

    # restore mode state
    utils.restore_mode_selection_state(mode_selection_state)
    utils.restore_render_visibility_state(rv_state)

    utils.log_recess()
    utils.log_timer("Done Character Export.")


def export_non_standard(self, context, file_path, include_selected):
    """Exports non-standard character (unconverted and not rigified) to CC4 with json data and textures, as an .fbx file.
    """

    props = vars.props()
    prefs = vars.prefs()

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Exporting Non-Standard Model to CC:")
    utils.log_info("-----------------------------------")

    utils.object_mode()

    export_anim = False
    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    # store mode state
    mode_selection_state = utils.store_mode_selection_state()
    rv_state = utils.store_render_visibility_state()

    # export objects
    objects = get_export_objects(None, include_selected)
    arm = get_export_armature(None, objects)

    # store states and settings
    armature_settings = bones.store_armature_settings(arm, include_pose=True)
    object_state = utils.store_object_state(objects)

    # restore quaternion rotation modes
    rigutils.reset_rotation_modes(arm)

    utils.log_info("Generating JSON data for export:")
    utils.log_indent()
    json_data = prep_non_standard_export(context, objects, dir, name, prefs.export_non_standard_mode)

    utils.log_recess()
    utils.log_info("Preparing character for export:")
    utils.log_indent()

    remove_modifiers_for_export(None, objects, True)

    # attempt any custom exports (ARP)
    arp_export = False
    if is_arp_installed() and is_arp_rig(arm):
        arp_export = export_arp(file_path, arm, objects)

    # double check custom export
    if not os.path.exists(file_path):
        arp_export = False

    # proceed with normal export
    if not arp_export:
        bpy.ops.export_scene.fbx(filepath=file_path,
                use_selection = True,
                bake_anim = export_anim,
                bake_anim_simplify_factor=self.animation_simplify,
                add_leaf_bones = False,
                use_mesh_modifiers = True,
                mesh_smooth_type = ("FACE" if self.export_face_smoothing else "OFF"),
                use_armature_deform_only = True)

    utils.log_recess()
    utils.log_info("")

    # write json data
    if json_data:
        utils.log_info("Writing Json Data.")
        update_facial_profile_json(None, objects, json_data, name)
        new_json_path = os.path.join(dir, name + ".json")
        jsonutils.write_json(json_data, new_json_path)

    # restore states and settings
    utils.restore_object_state(object_state)
    bones.restore_armature_settings(arm, armature_settings, include_pose=True)

    # restore mode state
    utils.restore_mode_selection_state(mode_selection_state)
    utils.restore_render_visibility_state(rv_state)

    utils.log_recess()
    if arp_export:
        utils.log_timer("Done Non-standard ARP Export.")
        self.report({'INFO'}, "Export Non-standard (ARP) Done!")
    else:
        utils.log_timer("Done Non-standard Export.")
        self.report({'INFO'}, "Export Non-standard Done!")




def export_to_unity(self, context, chr_cache, export_anim, file_path, include_selected):
    """Exports CC3/4 character (not rigified) for Unity with json data and textures,
       as either a .blend file or .fbx file.
    """

    props = vars.props()
    prefs = vars.prefs()

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Exporting Character Model to UNITY:")
    utils.log_info("-----------------------------------")

    utils.object_mode()

    chr_cache.check_paths()

    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    # store mode state
    mode_selection_state = utils.store_mode_selection_state()
    rv_state = utils.store_render_visibility_state()

    utils.log_info("Export to: " + file_path)
    utils.log_info("Exporting as: " + ext)

    json_data = chr_cache.get_json_data()
    if not json_data:
        json_data = jsonutils.generate_character_base_json_data(name)
        set_character_generation(json_data, chr_cache, name)

    utils.log_info("Preparing character for export:")
    utils.log_indent()

    # remove any collision proxies
    if utils.is_file_ext(ext, "BLEND"):
        for obj in chr_cache.get_cache_objects():
            proxy = chr_cache.get_collision_proxy(obj)
            if proxy:
                utils.delete_object_tree(proxy)

    # export objects
    objects = get_export_objects(chr_cache, include_selected)
    arm = get_export_armature(chr_cache, objects)

    # store states and settings
    armature_settings = bones.store_armature_settings(arm, include_pose=True)
    object_state = utils.store_object_state(objects)

    # restore quaternion rotation modes
    rigutils.reset_rotation_modes(arm)

    export_actions = False
    export_strips = True

    # FBX exports only T-pose as a strip
    if utils.is_file_ext(ext, "FBX"):
        export_actions = False
        export_strips = True
    # blend file exports make the T-pose as an action
    else:
        export_actions = True
        export_strips = False

    as_blend_file = utils.is_file_ext(ext, "BLEND")

    # remove custom material modifiers
    remove_modifiers_for_export(chr_cache, objects, True)

    prep_export(context, chr_cache, name, objects, json_data, chr_cache.get_import_dir(), dir, self.include_textures, False, False, as_blend_file, False)

    # make the T-pose as an action
    utils.safe_set_action(arm, None)
    chr_json = None
    if json_data:
        try:
            chr_json = json_data[name]["Object"][name]
        except: pass
    set_T_pose(arm, chr_json)
    create_T_pose_action(arm, objects, export_strips)

    if utils.is_file_ext(ext, "FBX"):
        # export as fbx
        bpy.ops.export_scene.fbx(filepath=file_path,
                use_selection = True,
                bake_anim = export_anim,
                bake_anim_use_all_actions=export_actions,
                bake_anim_use_nla_strips=export_strips,
                bake_anim_simplify_factor=self.animation_simplify,
                use_armature_deform_only=True,
                add_leaf_bones = False,
                mesh_smooth_type = ("FACE" if self.export_face_smoothing else "OFF"),
                use_mesh_modifiers = True,
                #apply_scale_options="FBX_SCALE_UNITS",
                object_types={'EMPTY', 'MESH', 'ARMATURE'},
                use_space_transform=True,
                #armature_nodetype="ROOT",
                )

        restore_modifiers(chr_cache, objects)

    elif utils.is_file_ext(ext, "BLEND"):
        # store Unity project paths
        props.unity_file_path = file_path
        props.unity_project_path = utils.search_up_path(file_path, "Assets")
        chr_cache.change_import_file(file_path)
        # save blend file at filepath
        bpy.ops.wm.save_as_mainfile(filepath=file_path)
        bpy.ops.file.make_paths_relative()
        bpy.ops.wm.save_as_mainfile(filepath=file_path)
        # restore some lighting
        shading = utils.get_view_3d_shading(context)
        if shading:
            shading.use_scene_lights = False
            shading.use_scene_world = False
            shading.studiolight_intensity = 1.0

    #export_copy_fbx_key(chr_cache, dir, name)
    export_copy_asset_file(chr_cache, dir, name, ".fbxkey", chr_cache.get_import_key_file())

    utils.log_recess()
    utils.log_info("")

    if json_data:
        utils.log_info("Writing Json Data.")
        update_facial_profile_json(chr_cache, objects, json_data, name)
        new_json_path = os.path.join(dir, name + ".json")
        jsonutils.write_json(json_data, new_json_path)

    # restore states and settings (but only for FBX export)
    if utils.is_file_ext(ext, "FBX"):
        utils.restore_object_state(object_state)
        bones.restore_armature_settings(arm, armature_settings, include_pose=True)
        # restore mode state
        utils.restore_mode_selection_state(mode_selection_state)
        utils.restore_render_visibility_state(rv_state)

    utils.log_recess()
    utils.log_timer("Done Character Export.")


def update_to_unity(self, context, chr_cache, export_anim, include_selected):
    props = vars.props()
    prefs = vars.prefs()

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Updating Character Model for UNITY:")
    utils.log_info("-----------------------------------")

    utils.object_mode()

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

    # remove any collision proxies
    if utils.is_file_ext(ext, "BLEND"):
        for obj in chr_cache.get_cache_objects():
            proxy = chr_cache.get_collision_proxy(obj)
            if proxy:
                utils.delete_object_tree(proxy)

    objects = get_export_objects(chr_cache, include_selected)

    as_blend_file = True

    # remove custom material modifiers
    remove_modifiers_for_export(chr_cache, objects, True)

    prep_export(context, chr_cache, name, objects, json_data, chr_cache.get_import_dir(), dir, True, False, False, as_blend_file, False)

    # make the T-pose as an action
    arm = get_export_armature(chr_cache, objects)
    utils.safe_set_action(arm, None)
    chr_json = None
    if json_data:
        try:
            chr_json = json_data[name]["Object"][name]
        except: pass
    set_T_pose(arm, chr_json)
    create_T_pose_action(arm, objects, False)

    # save blend file at filepath
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()

    utils.log_recess()
    utils.log_info("")

    if json_data:
        utils.log_info("Writing Json Data.")
        update_facial_profile_json(chr_cache, objects, json_data, name)
        new_json_path = os.path.join(dir, name + ".json")
        jsonutils.write_json(json_data, new_json_path)

    utils.log_recess()
    utils.log_timer("Done Character Export.")


def export_rigify(self, context, chr_cache, export_anim, file_path, include_selected):
    props = vars.props()
    prefs = vars.prefs()

    utils.start_timer()

    utils.log_info("")
    utils.log_info("Exporting Rigified Character Model:")
    utils.log_info("-----------------------------------")

    utils.object_mode()

    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    # store mode state
    mode_selection_state = utils.store_mode_selection_state()
    rv_state = utils.store_render_visibility_state()

    utils.log_info("Export to: " + file_path)
    utils.log_info("Exporting as: " + ext)

    json_data = None
    include_textures = self.include_textures
    if prefs.rigify_export_mode == "MOTION":
         include_textures = False
    else:
        json_data = chr_cache.get_json_data()

    utils.log_info("Preparing character for export:")
    utils.log_indent()

    # export objects
    objects = get_export_objects(chr_cache, include_selected)
    arm = chr_cache.get_armature()
    export_rig = None

    # store states and settings
    armature_settings = bones.store_armature_settings(arm, include_pose=True)
    object_state = utils.store_object_state(objects)

    # restore quaternion rotation modes
    rigutils.reset_rotation_modes(arm)

    export_actions = False
    export_strips = True
    baked_actions = []
    export_rig, vertex_group_map, t_pose_action = rigging.prep_rigify_export(chr_cache,
                                                            export_anim, baked_actions,
                                                            include_t_pose=prefs.rigify_export_t_pose,
                                                            objects=objects,
                                                            bone_naming = prefs.rigify_export_naming)
    if export_rig:
        rigify_rig = chr_cache.get_armature()
        objects.remove(rigify_rig)
        objects.append(export_rig)

    use_anim = export_anim
    if prefs.rigify_export_t_pose:
        use_anim = True

    # remove custom material modifiers
    remove_modifiers_for_export(chr_cache, objects, True, rig=export_rig)

    prep_export(context, chr_cache, name, objects, json_data, chr_cache.get_import_dir(), dir,
                include_textures, False, False, False, False)

    # for motion only exports, select armature and any mesh objects that have shape key animations
    if prefs.rigify_export_mode == "MOTION":
        utils.clear_selected_objects()
        rigging.select_motion_export_objects(objects)

    armature_object, armature_data = rigutils.rename_armature(export_rig, name)

    # export as fbx
    bpy.ops.export_scene.fbx(filepath=file_path,
            use_selection = True,
            bake_anim = use_anim,
            bake_anim_use_all_actions=export_actions,
            bake_anim_use_nla_strips=export_strips,
            bake_anim_simplify_factor=self.animation_simplify,
            use_armature_deform_only=True,
            add_leaf_bones = False,
            #axis_forward = "-Y",
            #axis_up = "Z",
            mesh_smooth_type = ("FACE" if self.export_face_smoothing else "OFF"),
            use_mesh_modifiers = True)

    if prefs.rigify_export_t_pose:
        bones.clear_pose(export_rig)

        # put t-pose back on armature
        utils.safe_set_action(export_rig, t_pose_action)

        bpy.context.view_layer.update()

        # write HIK profile for RIGIFY
        hik_path = os.path.join(dir, name + ".3dxProfile")
        if prefs.rigify_export_naming == "METARIG":
            hik_template = hik.RIGIFY_METARIG_PROFILE_TEMPLATE
        elif prefs.rigify_export_naming == "CC":
            hik_template = hik.RIGIFY_CC_BASE_PROFILE_TEMPLATE
        else:
            hik_template = hik.RIGIFY_BASE_PROFILE_TEMPLATE
        if hik.generate_hik_profile(export_rig, name, hik_path, hik_template):
            if json_data:
                json_data[name]["HIK"] = {}
                json_data[name]["HIK"]["Profile_Path"] = os.path.relpath(hik_path, dir)

        # clear armature actions
        utils.safe_set_action(export_rig, None)

    rigutils.restore_armature_names(armature_object, armature_data, name)

    restore_modifiers(chr_cache, objects)

    # clean up rigify export
    rigging.finish_rigify_export(chr_cache, export_rig, baked_actions, vertex_group_map,
                                 objects=objects)

    utils.log_recess()
    utils.log_info("")

    if json_data:
        utils.log_info("Writing Json Data.")
        update_facial_profile_json(chr_cache, objects, json_data, name)
        new_json_path = os.path.join(dir, name + ".json")
        jsonutils.write_json(json_data, new_json_path)

    # restore states and settings
    utils.restore_object_state(object_state)
    bones.restore_armature_settings(arm, armature_settings, include_pose=True)

    # restore mode state
    utils.restore_mode_selection_state(mode_selection_state)
    utils.restore_render_visibility_state(rv_state)

    utils.log_recess()
    utils.log_timer("Done Rigify Export.")


def export_as_accessory(file_path, filename_ext):
    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    # store selection
    old_selection = bpy.context.selected_objects
    old_active = utils.get_active_object()

    if utils.is_file_ext(ext, "FBX"):
        bpy.ops.export_scene.fbx(filepath=file_path,
                use_selection = True,
                bake_anim = False,
                add_leaf_bones=False,
                )
    elif utils.is_file_ext(ext, "OBJ"):
        obj_export(file_path, use_selection=True,
                              global_scale=100,
                              use_animation=False,
                              use_materials=True,
                              keep_vertex_order=True,
                              use_vertex_colors=True,
                              use_vertex_groups=False,
                              apply_modifiers=True)

    # restore selection
    bpy.ops.object.select_all(action='DESELECT')
    for obj in old_selection:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = old_active


def export_as_replace_mesh(file_path):
    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    # store selection
    state = utils.store_mode_selection_state()

    obj_export(file_path, use_selection=True,
                          global_scale=100,
                          use_animation=False,
                          use_materials=True,
                          keep_vertex_order=True,
                          use_vertex_colors=True,
                          use_vertex_groups=False,
                          apply_modifiers=True)

    # restore selection
    utils.restore_mode_selection_state(state)


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

    filter_glob: bpy.props.StringProperty(
        default="*.fbx;*.obj;*.blend",
        options={"HIDDEN"},
        )

    animation_simplify: bpy.props.FloatProperty(
        default=1.0,
        min=0.0, max=10.0,
        name="Simplify Animation",
        description="How much to simplify baked values (0.0 to disable, higher values for more simplification)",
    )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    filename_ext = ".fbx"  # ExportHelper mixin class uses this

    link_id_override: bpy.props.StringProperty(
            name = "link_id_override",
            default = "",
            options={"HIDDEN"}
        )

    include_anim: bpy.props.BoolProperty(name = "Export Animation", default = True,
        description="Export current timeline animation with the character")
    include_selected: bpy.props.BoolProperty(name = "Include Selected", default = True,
        description="Include any additional selected objects with the character. Note: They will need to be correctly parented and weighted")
    include_textures: bpy.props.BoolProperty(name = "Include Textures", default = False,
        description="Copy textures with the character, if exporting to a new location")
    export_face_smoothing: bpy.props.BoolProperty(name = "Face Smoothing Groups", default = False,
        description="Export FBX with face smoothing groups. (Can solve blocky faces / split normals issues in game engines)")

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
        props = vars.props()
        prefs = vars.prefs()
        chr_cache = props.get_context_character_cache(context)
        if self.link_id_override:
            chr_cache = props.find_character_by_link_id(self.link_id_override)
            self.include_selected = False

        if chr_cache and self.param == "EXPORT_CC3":

            export_standard(self, context, chr_cache, self.filepath, self.include_selected)
            self.report({'INFO'}, "Export to CC3 Done!")
            self.error_report()

        elif chr_cache and self.param == "EXPORT_UNITY":

            export_to_unity(self, context, chr_cache, self.include_anim, self.filepath, self.include_selected)
            self.report({'INFO'}, "Export to Unity Done!")
            self.error_report()

        elif self.param == "UPDATE_UNITY":

            # only called when updating .blend file exports
            update_to_unity(self, context, chr_cache, self.include_anim, True)
            self.report({'INFO'}, "Update to Unity Done!")
            self.error_report()

        elif chr_cache and self.param == "EXPORT_RIGIFY":

            export_rigify(self, context, chr_cache, self.include_anim, self.filepath, self.include_selected)
            self.report({'INFO'}, "Export from Rigified Done!")
            self.error_report()

        elif self.param == "EXPORT_NON_STANDARD":

            export_non_standard(self, context, self.filepath, self.include_selected)
            self.error_report()


        elif self.param == "EXPORT_ACCESSORY":

            export_as_accessory(self.filepath, self.filename_ext)
            self.report({'INFO'}, message="Export Accessory Done!")

        elif self.param == "EXPORT_MESH":

            export_as_replace_mesh(self.filepath)
            self.report({'INFO'}, message="Export Mesh Replacement Done!")

        elif self.param == "CHECK_EXPORT":

            if chr_cache and chr_cache.is_import_type("FBX"):
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
        prefs = vars.prefs()

        self.check_report = []
        self.check_valid = True
        self.check_warn = False

        # bypass modal for direct functions
        if self.param == "UPDATE_UNITY":
            return self.execute(context)

        if self.param == "CHECK_EXPORT":
            return self.execute(context)

        props = vars.props()
        chr_cache = props.get_context_character_cache(context)
        if self.link_id_override:
            chr_cache = props.find_character_by_link_id(self.link_id_override)

        # menu export
        if self.param == "EXPORT_MENU":
            if chr_cache and chr_cache.rigified:
                self.param = "EXPORT_RIGIFY"
            else:
                self.param = "EXPORT_CC3"

        # determine export format
        export_format = "fbx"
        export_suffix = ""
        if self.param == "EXPORT_MESH":
            export_format = "obj"
            export_suffix = "_mesh"
        elif self.param == "EXPORT_ACCESSORY":
            export_suffix = "_accessory"
        elif self.param == "EXPORT_NON_STANDARD":
            export_format = "fbx"
        elif self.param == "EXPORT_RIGIFY":
            export_format = "fbx"
            if prefs.rigify_export_mode == "MOTION":
                export_suffix = "_motion"
        elif self.param == "EXPORT_UNITY":
            if prefs.export_unity_mode == "FBX":
                export_format = "fbx"
            else:
                export_format = "blend"
        elif chr_cache:
            export_format = utils.get_file_ext(chr_cache.get_import_type())
            if export_format != "obj":
                export_format = "fbx"
            if chr_cache.rigified:
                export_format = "fbx"
        self.filename_ext = "." + export_format

        if chr_cache and (chr_cache.generation == "Generic" or
                          chr_cache.generation == "NonStandardGeneric" or
                          chr_cache.generation == "Unknown"):
            self.include_textures = True

        if self.param == "EXPORT_UNITY":
            self.include_textures = True
            if export_format == "fbx":
                self.export_face_smoothing = True

        if self.param == "EXPORT_RIGIFY":
            if prefs.rigify_export_mode == "MOTION":
                self.include_textures = False
                self.include_anim = True
            elif prefs.rigify_export_mode == "MESH":
                self.include_textures = True
                self.include_anim = False
                self.export_face_smoothing = True
            else:
                self.include_textures = True
                self.include_anim = True
                self.export_face_smoothing = True

        # perform checks and validation
        require_export_check = (self.param == "EXPORT_CC3" or
                                self.param == "EXPORT_UNITY" or
                                self.param == "EXPORT_RIGIFY" or
                                self.param == "UPDATE_UNITY" or
                                self.param == "EXPORT_NON_STANDARD")
        require_valid_export = (self.param == "EXPORT_CC3" or
                                self.param == "EXPORT_NON_STANDARD")
        if require_export_check:
            rv_state = utils.store_render_visibility_state()
            objects = get_export_objects(chr_cache, self.include_selected)
            utils.restore_render_visibility_state(rv_state)
            if export_format == "fbx":
                self.check_valid, self.check_warn, self.check_report = check_valid_export_fbx(chr_cache, objects)
            if require_valid_export:
                if not self.check_valid:
                    self.error_report()
                    return {"FINISHED"}

        # determine default file name
        if not self.filepath:
            default_file_path = context.blend_data.filepath
            if default_file_path:
                default_file_path = os.path.splitext(default_file_path)[0]
            else:
                if chr_cache:
                    default_file_path = chr_cache.get_character_id()
                else:
                    default_file_path = "untitled"

            self.filepath = default_file_path + export_suffix + self.filename_ext

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
                   "**Note: Pipeline Exports to Unity are exported as character only, without animations, with a T-Pose**"
        elif properties.param == "EXPORT_RIGIFY":
            return "Export rigified character and/or animation.\n"
        elif properties.param == "EXPORT_ACCESSORY":
            return "Export selected object(s) for import into CC3 as accessories"
        elif properties.param == "EXPORT_MESH":
            return "Export selected object as a mesh replacement. Use with Mesh > Replace Mesh, with the desired mesh to replace selected in CC4.\n" \
                   "**Mesh must have the same number of vertices as the original mesh to replace**"
        elif properties.param == "CHECK_EXPORT":
            return "Check for issues with the character for export. *Note* This will also test any selected objects as well as all objects attached to the character, as selected objects can also be exported with the character"
        elif properties.param == "EXPORT_CC3_INVALID":
            return "This standard character has altered topology of the base body mesh and will not re-import into Character Creator"
        return ""


def menu_func_export(self, context):
    self.layout.operator(CC3Export.bl_idname, text="Reallusion Character (.fbx, .obj)").param = "EXPORT_MENU"

