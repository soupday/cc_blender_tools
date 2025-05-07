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
import shutil
import bpy
from enum import IntEnum, IntFlag

from . import (rlx, characters, hik, rigging, rigutils, bones, bake, imageutils, jsonutils, materials,
               facerig, modifiers, wrinkle, drivers, meshutils, nodeutils, physics,
               rigidbody, colorspace, scene, channel_mixer, shaders,
               basic, properties, lib, utils, vars)

debug_counter = 0


def delete_import(chr_cache):
    props = vars.props()
    chr_cache.invalidate()
    chr_cache.delete()
    chr_cache.clean_up()
    utils.remove_from_collection(props.import_cache, chr_cache)
    utils.clean_up_unused()


def process_material(chr_cache, obj_cache, obj, mat, obj_json, processed_images):
    props = vars.props()
    prefs = vars.prefs()

    mat_cache = chr_cache.get_material_cache(mat)
    mat_json = jsonutils.get_material_json(obj_json, mat)

    if not mat_cache: return

    # don't process user added materials
    if mat_cache.user_added: return

    if not mat.use_nodes:
        mat.use_nodes = True

    # store the material type and id
    mat_cache.check_id()

    if chr_cache.setup_mode == "ADVANCED":

        if mat_cache.is_cornea() or mat_cache.is_eye():
            shaders.connect_eye_shader(obj_cache, obj, mat, obj_json, mat_json, processed_images)

        elif mat_cache.is_tearline():
            shaders.connect_tearline_shader(obj_cache, obj, mat, mat_json, processed_images)

        elif mat_cache.is_eye_occlusion():
            shaders.connect_eye_occlusion_shader(obj_cache, obj, mat, mat_json, processed_images)

        elif mat_cache.is_skin() or mat_cache.is_nails():
            shaders.connect_skin_shader(chr_cache, obj_cache, obj, mat, mat_json, processed_images)

        elif mat_cache.is_teeth():
            shaders.connect_teeth_shader(obj_cache, obj, mat, mat_json, processed_images)

        elif mat_cache.is_tongue():
            shaders.connect_tongue_shader(obj_cache, obj, mat, mat_json, processed_images)

        elif mat_cache.is_hair():
            shaders.connect_hair_shader(obj_cache, obj, mat, mat_json, processed_images)

        elif mat_cache.is_sss():
            shaders.connect_sss_shader(obj_cache, obj, mat, mat_json, processed_images)

        else:
            shaders.connect_pbr_shader(obj_cache, obj, mat, mat_json, processed_images)

        # optional pack channels
        if prefs.build_limit_textures or prefs.build_pack_texture_channels:
            bake.pack_shader_channels(chr_cache, mat_cache)
        elif props.wrinkle_mode and mat_json and "Wrinkle" in mat_json.keys():
            bake.pack_shader_channels(chr_cache, mat_cache)

    else:

        nodeutils.clear_cursor()
        nodeutils.reset_cursor()

        if mat_cache.is_eye_occlusion():
            basic.connect_eye_occlusion_material(obj, mat, mat_json, processed_images)

        elif mat_cache.is_tearline():
            basic.connect_tearline_material(obj, mat, mat_json, processed_images)

        elif mat_cache.is_cornea():
            basic.connect_basic_eye_material(obj, mat, mat_json, processed_images)

        else:
            basic.connect_basic_material(obj, mat, mat_json, processed_images)

        nodeutils.move_new_nodes(-600, 0)

    # apply cached alpha settings
    if mat_cache is not None:
        if mat_cache.alpha_mode != "NONE":
            materials.apply_alpha_override(obj, mat, mat_cache.alpha_mode)
        if mat_cache.culling_sides > 0:
            materials.apply_backface_culling(obj, mat, mat_cache.culling_sides)

    # apply any channel mixers
    if mat_cache is not None:
        if mat_cache.mixer_settings:
                mixer_settings = mat_cache.mixer_settings
                if mixer_settings.rgb_image or mixer_settings.id_image:
                    channel_mixer.rebuild_mixers(chr_cache, mat, mixer_settings)


def process_object(chr_cache, obj, obj_cache, objects_processed, chr_json, processed_materials, processed_images):
    props = vars.props()
    prefs = vars.prefs()

    if obj is None or obj in objects_processed:
        return

    objects_processed.append(obj)

    obj_json = jsonutils.get_object_json(chr_json, obj_cache.source_name)
    physics_json = None

    utils.log_info("")
    utils.log_info("Processing Object: " + obj.name + ", Type: " + obj.type)
    utils.log_indent()

    if obj.type == "MESH":

        mesh : bpy.types.Mesh = obj.data

        # Turn off auto smoothing
        if not utils.B401():
            mesh.use_auto_smooth = False

        # Auto apply armature modifier settings
        if prefs.build_armature_edit_modifier or prefs.build_armature_preserve_volume:
            mod_arm = modifiers.get_object_modifier(obj, "ARMATURE")
            if mod_arm:
                if prefs.build_armature_edit_modifier:
                    mod_arm.show_in_editmode = True
                    mod_arm.show_on_cage = True
                if prefs.build_armature_preserve_volume:
                    mod_arm.use_deform_preserve_volume = True

        # Set to smooth shading (disabled as may not be needed anymore)
        #meshutils.set_shading(obj, True)

        # remove any modifiers for refractive eyes
        modifiers.remove_eye_modifiers(obj)

        # store the object type and id
        # store the material type and id
        if obj_cache:
            obj_cache.check_id()

        # process any materials found in the mesh object
        for slot in obj.material_slots:
            mat = slot.material
            if mat and mat not in objects_processed:
                utils.log_info("")
                utils.log_info("Processing Material: " + mat.name)
                utils.log_indent()

                process_material(chr_cache, obj_cache, obj, mat, obj_json, processed_images)
                if processed_materials is not None:
                    first = materials.find_duplicate_material(chr_cache, mat, processed_materials)
                    if first:
                        utils.log_info(f"Found duplicate material, re-using {first.name} instead.")
                        slot.material = first
                    else:
                        processed_materials.append(mat)

                utils.log_recess()
                objects_processed.append(mat)

        # setup special modifiers for displacement, UV warp, etc...
        if obj_cache and chr_cache.setup_mode == "ADVANCED":
            if obj_cache.is_eye():
                modifiers.add_eye_modifiers(obj)
            elif obj_cache.is_eye_occlusion():
                modifiers.add_eye_occlusion_modifiers(obj)
            elif obj_cache.is_tearline():
                modifiers.add_tearline_modifiers(obj)

    elif obj.type == "ARMATURE":

        # set the frame range of the scene to the active action on the armature
        if props.physics_mode:
            scene.fetch_anim_range(bpy.context, expand=True)

        obj["rl_import_file"] = chr_cache.import_file
        obj["rl_generation"] = chr_cache.generation

    utils.log_recess()


def cache_object_materials(chr_cache, obj, chr_json, processed):
    props = vars.props()

    if obj is None or obj in processed:
        return

    obj_json = jsonutils.get_object_json(chr_json, obj)
    obj_cache = chr_cache.add_object_cache(obj)

    if obj.type == "MESH":

        utils.log_info(f"Caching Object: {obj.name}")
        utils.log_indent()

        for mat in obj.data.materials:

            if mat and mat.node_tree is not None:

                object_type, material_type = materials.detect_materials(chr_cache, obj, mat, obj_json)
                if obj_cache.object_type != "BODY":
                    obj_cache.set_object_type(object_type)

                if mat not in processed:
                    mat_cache = chr_cache.add_material_cache(mat, material_type)
                    mat_cache.dir = imageutils.get_material_tex_dir(chr_cache, obj, mat)
                    utils.log_indent()
                    materials.detect_embedded_textures(chr_cache, obj, obj_cache, mat, mat_cache)
                    materials.detect_mixer_masks(chr_cache, obj, obj_cache, mat, mat_cache)
                    physics.detect_physics(chr_cache, obj, obj_cache, mat, mat_cache, chr_json)
                    utils.log_recess()
                    processed.append(mat)

        utils.log_recess()

    processed.append(obj)


def apply_edit_shapekeys(obj):
    """For objects with shapekeys, set the active visible and edit mode shapekey to the basis.
    """
    # shapekeys data path:
    #   utils.get_active_object().data.shape_keys.key_blocks['Basis']
    if obj.type == "MESH":
        shape_keys = obj.data.shape_keys
        if shape_keys is not None:
            blocks = shape_keys.key_blocks
            if blocks is not None:
                # if the object has shape keys
                if len(blocks) > 0:
                    try:
                        # set the active shapekey to the basis and apply shape keys in edit mode.
                        obj.active_shape_key_index = 0
                        obj.show_only_shape_key = False
                        obj.use_shape_key_edit_mode = True
                    except Exception as e:
                        utils.log_error("Unable to set shape key edit mode!", e)


def init_shape_key_range(obj):
    #utils.get_active_object().data.shape_keys.key_blocks['Basis']
    if obj.type == "MESH":
        shape_keys: bpy.types.Key = obj.data.shape_keys
        if shape_keys is not None:
            blocks = shape_keys.key_blocks
            if blocks is not None:
                if len(blocks) > 0:
                    for block in blocks:
                        # expand the range of the shape key slider to include negative values...
                        if "Eye" in block.name and "_Look_" in block.name:
                            block.slider_min = -2.0
                            block.slider_max = 2.0
                        else:
                            block.slider_min = -1.5
                            block.slider_max = 1.5

            # re-set a value in the shapekey action keyframes to force
            # the shapekey action to update to the new ranges:
            try:
                action = utils.safe_get_action(shape_keys)
                if action:
                    co = action.fcurves[0].keyframe_points[0].co
                    action.fcurves[0].keyframe_points[0].co = co
            except:
                pass


def detect_generation(chr_cache, json_data, character_id):

    generation = "Unknown"
    if json_data:
        avatar_type = jsonutils.get_json(json_data, f"{character_id}/Avatar_Type")
        json_generation = jsonutils.get_character_generation_json(json_data, chr_cache.get_character_id())

        if json_generation and json_generation in vars.CHARACTER_GENERATION:
            generation = vars.CHARACTER_GENERATION[json_generation]
        elif avatar_type == "NonHuman":
            generation = "Creature"
        elif avatar_type == "NonStandard":
            generation = "Humanoid"
        elif json_generation is not None and json_generation == "":
            generation = "Humanoid"
        elif json_generation is None:
            generation = "Prop"

    arm = chr_cache.get_armature()

    material_names = characters.get_character_material_names(arm)
    object_names = characters.get_character_object_names(arm)

    # some ActorScan characters are GameBase in disguise...
    if characters.character_has_bones(arm, ["root", "pelvis", "spine_03", "CC_Base_FacialBone"]):
        generation = "GameBase"

    if generation in ["Unknown", "Humanoid", "Creature"]:
        utils.log_info(f"Determining generation from armature...")
        if len(material_names) == 1 and rigutils.is_ActorCore_armature(arm):
            generation = "ActorScan"
            utils.log_info(" - ActorScan found!")
        elif characters.character_has_materials(arm, ["Ga_Skin_Body"]) and rigutils.is_ActorCore_armature(arm):
            generation = "ActorBuild"
            utils.log_info(" - ActorBuild found!")
        elif characters.character_has_materials(arm, ["Ga_Skin_Body"]) and rigutils.is_GameBase_armature(arm):
            generation = "GameBase"
            utils.log_info(" - GameBase found!")
        elif rigutils.is_rl_armature(arm):
            generation = "AccuRig"
            utils.log_info(" - AccuRig found!")
        else:
            utils.log_info(" - Not found...")

    if generation == "Unknown" and arm:
        if utils.find_pose_bone_in_armature(arm, "RootNode_0_", "RL_BoneRoot"):
            generation = "ActorCore"
        elif utils.find_pose_bone_in_armature(arm, "CC_Base_L_Pinky3", "L_Pinky3"):
            generation = "G3"
        elif utils.find_pose_bone_in_armature(arm, "pinky_03_l"):
            generation = "GameBase"
        elif utils.find_pose_bone_in_armature(arm, "CC_Base_L_Finger42", "L_Finger42"):
            generation = "G1"
        utils.log_info(f"Generation could be: {generation} detected from pose bones.")

    if generation == "Unknown":
        for obj_cache in chr_cache.object_cache:
            obj = obj_cache.get_object()
            if obj_cache.is_mesh():
                name = obj.name.lower()
                if "cc_game_body" in name or "cc_game_tongue" in name:
                    generation = "GameBase"
                elif "cc_base_body" in name:
                    if utils.object_has_material(obj, "ga_skin_body"):
                        generation = "GameBase"
                    elif utils.object_has_material(obj, "std_skin_body"):
                        generation = "G3"
                    elif utils.object_has_material(obj, "skin_body"):
                        generation = "G1"
        if generation != "Unknown":
            utils.log_info(f"Generation could be: {generation} detected from materials.")

    if generation == "Unknown" or generation == "G3":

        for obj_cache in chr_cache.object_cache:
            obj = obj_cache.get_object()
            if obj_cache.is_mesh() and obj.name == "CC_Base_Body":

                # try vertex count
                if len(obj.data.vertices) == 14164:
                    utils.log_info("Generation: G3Plus detected by vertex count.")
                    generation = "G3Plus"
                elif len(obj.data.vertices) == 13286:
                    utils.log_info("Generation: G3 detected by vertex count.")
                    generation = "G3"

                #try UV map test
                elif materials.test_for_material_uv_coords(obj, 0, [[0.5, 0.763], [0.7973, 0.6147], [0.1771, 0.0843], [0.912, 0.0691]]):
                    utils.log_info("Generation: G3Plus detected by UV test.")
                    generation = "G3Plus"
                elif materials.test_for_material_uv_coords(obj, 0, [[0.5, 0.034365], [0.957562, 0.393431], [0.5, 0.931725], [0.275117, 0.961283]]):
                    utils.log_info("Generation: G3 detected by UV test.")
                    generation = "G3"

    utils.log_info(f"Detected Character Generation: {generation}")
    return generation


def is_iclone_temp_motion(name : str):
    u_idx = name.find('_', 0)
    if u_idx == -1:
        return False
    if not name[:u_idx].isdigit():
       return False
    search = "TempMotion"
    if utils.partial_match(name, "TempMotion", u_idx + 1):
        return True
    else:
        return False


def purge_imported_material(mat, imported_images: list):
    if utils.material_exists(mat):
        if mat.node_tree and mat.node_tree.nodes:
            for node in mat.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    if node.image:
                        if node.image in imported_images:
                            imported_images.remove(node.image)
                            bpy.data.images.remove(node.image)
    bpy.data.materials.remove(mat)


def purge_imported_object(obj, imported_images):
    if utils.object_exists(obj):
        if obj.type == "MESH":
            for mat in obj.data.materials:
                purge_imported_material(mat, imported_images)
        utils.delete_object_tree(obj)


def remap_action_names(arm, objects, actions, source_id, motion_prefix=""):
    key_map = {}
    num_keys = 0

    rig_id = rigutils.get_rig_id(arm)
    utils.log_info(f"Remap Action Names:")
    utils.log_info(f"Armature: {source_id} => {rig_id}")

    # don't change the armature id if it exists
    rl_arm_id = utils.get_rl_object_id(arm)
    if not rl_arm_id:
        rl_arm_id = utils.generate_random_id(20)
        utils.set_rl_object_id(arm, rl_arm_id)

    # find all motions for this armature
    armature_actions = []
    shapekey_actions = []
    motion_ids = set()
    motion_sets = {}
    for action in actions:
        split = action.name.split("|")
        action_arm_id = split[0]
        motion_id = split[-1]
        if action_arm_id == source_id:
            utils.log_info(f"Motion ID: {motion_id}")
            motion_ids.add(motion_id)
            armature_actions.append(action)
            motion_sets[motion_id] = rigutils.generate_motion_set(arm, motion_id,
                                                                  motion_prefix)

    # determine how each shape key id relates to each object in the import
    for obj in objects:
        if obj.type == "MESH":
            obj_id = rigutils.get_action_obj_id(obj)
            if obj.data.shape_keys:
                obj_action = utils.safe_get_action(obj.data.shape_keys)
                if obj_action:
                    actions.append(obj_action)
                    key_map[obj_id] = obj.data.shape_keys.name
                    utils.log_info(f"ShapeKey: {obj.data.shape_keys.name} belongs to: {obj_id}")
                    num_keys += 1

    # rename all actions associated with this armature and it's motions
    for action in actions:
        split = action.name.split("|")
        action_key_name = split[0]
        motion_id = split[-1]
        if motion_id in motion_ids:
            set_id, set_generation = motion_sets[motion_id]
            if action in armature_actions:
                action_name = rigutils.make_armature_action_name(rig_id, motion_id, motion_prefix)
                utils.log_info(f"Renaming action: {action.name} to {action_name}")
                action.name = action_name
                rigutils.add_motion_set_data(action, set_id, set_generation, rl_arm_id=rl_arm_id)
                armature_actions.append(action)
            else:
                for obj_id, key_name in key_map.items():
                    if action_key_name == key_name:
                        action_name = rigutils.make_key_action_name(rig_id, motion_id, obj_id, motion_prefix)
                        utils.log_info(f"Renaming action: {action.name} to {action_name}")
                        action.name = action_name
                        rigutils.add_motion_set_data(action, set_id, set_generation, obj_id=obj_id)
                        shapekey_actions.append(action)

    return armature_actions, shapekey_actions


def process_root_bones(arm, json_data, name):
    root_bones = jsonutils.get_json(json_data, f"{name}/Root Bones")
    if root_bones:
        for root_def in root_bones:
            name = root_def["Name"]
            type = root_def["Type"]
            sub_link_id = root_def["Link_ID"]
            if name in arm.pose.bones:
                pose_bone = arm.pose.bones[name]
                pose_bone["root_id"] = sub_link_id
                pose_bone["root_type"] = type


def process_rl_import(file_path, import_flags, armatures, rl_armatures, cameras, lights,
                      objects: list,
                      actions, json_data, report, link_id, only_objects=None, motion_prefix=""):
    props = vars.props()
    prefs = vars.prefs()

    utils.log_info("")
    utils.log_info("Processing Reallusion Import:")
    utils.log_info("-----------------------------")

    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)

    imported_characters = []

    if armatures and (len(armatures) > 1 or len(rl_armatures) > 1):
        report.append("Multiple armatures detected in Fbx is not fully supported!")
        utils.log_warn("Multiple armatures detected in Fbx is not fully supported!")
        utils.log_warn("Character exports from iClone to Blender do not fully support multiple characters.")
        utils.log_warn("Characters should be exported individually for best results.")

    if not objects:
        report.append("No objects in import!")
        utils.log_error("No objects in import!")
        return None

    try:
        # try to override the import dir with the directory specified in the json:
        #   when exporting from Blender without copying textures, these custom fields
        #   tell us where the textures were originally and under what name
        import_dir = json_data[name]["Import_Dir"]
        import_name = json_data[name]["Import_Name"]
        utils.log_info(f"Using original Import Dir: {import_dir}")
        utils.log_info(f"Using original Import Name: {import_name}")
    except:
        import_name = name
        import_dir = dir

    processed = []
    chr_json = jsonutils.get_character_json(json_data, name)

    multi_import = (len(rl_armatures) + len(armatures) > 1)

    if ImportFlags.FBX in import_flags:

        for i, arm in enumerate(rl_armatures):

            # actual name of character
            #   multiple character imports name the armatures after the character
            #   single character imports just name the armature 'armature' so use the file name
            character_name = name
            source_id = "Armature"
            if len(rl_armatures) > 1:
                source_id = arm.name
                character_name = utils.safe_export_name(arm.name)
            armature_objects = utils.get_child_objects(arm, include_parent=True)

            utils.log_info(f"Generating Character Data: {character_name}")
            utils.log_indent()

            chr_cache = props.import_cache.add()
            chr_cache.import_file = file_path
            chr_cache.import_flags = import_flags
            # display name of character
            chr_cache.character_name = character_name

            arm["rl_import_file"] = file_path
            rigutils.fix_cc3_standard_rig(arm)

            # root bones
            process_root_bones(arm, json_data, name)

            # determine the main texture dir
            if os.path.exists(chr_cache.get_tex_dir()):
                chr_cache.import_embedded = False
            else:
                chr_cache.import_embedded = True

            arm.name = character_name
            arm.data.name = character_name

            # in case of duplicate names: character_name contains the name currently in Blender.
            #                             get_character_id() is the original name.
            chr_cache.character_name = arm.name
            # add armature to object_cache
            chr_cache.add_object_cache(arm)
            # assign bone collections
            bones.assign_rl_base_collections(arm)

            # link_id
            json_link_id = jsonutils.get_json(json_data, f"{name}/Link_ID")
            if not link_id and json_link_id:
                link_id = json_link_id
            if multi_import or not link_id:
                link_id = utils.generate_random_id(20)
            chr_cache.set_link_id(link_id)

            # delete accessory colliders, currently they are useless as
            # accessories don't export with any physics data or weightmaps.
            physics.delete_accessory_colliders(arm, objects)

            # add child objects to object_cache
            for obj in objects:
                if obj.type == "MESH" and obj.parent and obj.parent == arm:
                    if only_objects:
                        source_name = utils.strip_name(obj.name)
                        if source_name not in only_objects:
                            continue
                    chr_cache.add_object_cache(obj)

            # remame actions
            utils.log_info("Renaming actions:")
            utils.log_indent()
            remap_action_names(arm, armature_objects, actions, source_id,
                               motion_prefix=motion_prefix)
            utils.log_recess()

            # determine character generation
            chr_cache.generation = detect_generation(chr_cache, json_data, chr_cache.get_character_id())
            utils.log_info("Generation: " + chr_cache.character_name + " (" + chr_cache.generation + ")")
            arm["rl_generation"] = chr_cache.generation

            # cache materials
            for obj_cache in chr_cache.object_cache:
                if obj_cache.is_mesh():
                    obj = obj_cache.get_object()
                    cache_object_materials(chr_cache, obj, chr_json, processed)

            shaders.init_character_property_defaults(chr_cache, chr_json)
            basic.init_basic_default(chr_cache)

            # set preserve volume on armature modifiers
            for obj in objects:
                if obj.type == "MESH":
                    arm_mod = modifiers.get_object_modifier(obj, "ARMATURE")
                    if arm_mod:
                        arm_mod.use_deform_preserve_volume = False

            # material setup mode
            chr_cache.setup_mode = props.setup_mode

            # character render target
            chr_cache.render_target = prefs.render_target

            imported_characters.append(chr_cache.link_id)

            utils.log_recess()

        # any none character armatures should be scenes or props
        for i, arm in enumerate(armatures):

            character_name = name
            source_id = "Armature"
            if len(armatures) > 1:
                source_id = arm.name
                character_name = utils.safe_export_name(arm.name)
            armature_objects = utils.get_child_objects(arm, include_parent=True)

            utils.log_info(f"Generating Scene/Prop Data: {character_name}")
            utils.log_indent()

            chr_cache = props.import_cache.add()
            chr_cache.import_file = file_path
            chr_cache.import_flags = import_flags
            # display name of character
            chr_cache.character_name = character_name
            chr_id = chr_cache.get_character_id()

            # link_id
            if multi_import:
                link_id = utils.generate_random_id(20)
            json_link_id = jsonutils.get_json(json_data, f"{name}/Link_ID")
            if not multi_import and json_link_id:
                chr_cache.set_link_id(json_link_id)
            else:
                chr_cache.set_link_id(link_id)

            # root bones
            process_root_bones(arm, json_data, name)

            # determine the main texture dir
            if os.path.exists(chr_cache.get_tex_dir()):
                chr_cache.import_embedded = False
            else:
                chr_cache.import_embedded = True

            arm.name = character_name
            arm.data.name = character_name

            # in case of duplicate names: character_name contains the name currently in Blender.
            #                             import_name contains the original name.
            chr_cache.character_name = arm.name
            # add armature to object_cache
            chr_cache.add_object_cache(arm)

            # add child objects to object_cache
            for obj in objects:
                if obj.type == "MESH" and obj.parent and obj.parent == arm:
                    chr_cache.add_object_cache(obj)

            # remame actions
            utils.log_info("Renaming actions:")
            utils.log_indent()
            remap_action_names(arm, armature_objects, actions, source_id,
                               motion_prefix=motion_prefix)
            utils.log_recess()

            # determine character generation
            chr_cache.generation = "Prop"
            chr_cache.non_standard_type = "PROP"

            # cache materials
            for obj_cache in chr_cache.object_cache:
                if obj_cache.is_mesh():
                    obj = obj_cache.get_object()
                    cache_object_materials(chr_cache, obj, chr_json, processed)

            shaders.init_character_property_defaults(chr_cache, chr_json)
            basic.init_basic_default(chr_cache)

            # material setup mode
            chr_cache.setup_mode = props.setup_mode

            # character render target
            chr_cache.render_target = prefs.render_target

            json_avatar_type = jsonutils.get_json(json_data, f"{chr_id}/Avatar_Type")
            if json_avatar_type and json_avatar_type == "Prop":
                rigutils.custom_prop_rig(arm)

            imported_characters.append(chr_cache.link_id)

            utils.log_recess()

        for camera in cameras:

            # link_id
            if multi_import:
                link_id = utils.generate_random_id(20)
            json_link_id = jsonutils.get_json(json_data, f"{name}/Link_ID")
            if not multi_import and json_link_id:
                utils.set_rl_link_id(camera, json_link_id)
            else:
                utils.set_rl_link_id(camera, link_id)

        for light in lights:

            # link_id
            if multi_import:
                link_id = utils.generate_random_id(20)
            json_link_id = jsonutils.get_json(json_data, f"{name}/Link_ID")
            if not multi_import and json_link_id:
                utils.set_rl_link_id(light, json_link_id)
            else:
                utils.set_rl_link_id(light, link_id)


    elif ImportFlags.OBJ in import_flags:

        character_name = name

        utils.log_info(f"Generating Character Data: {character_name}")
        utils.log_indent()

        chr_cache = props.import_cache.add()
        chr_cache.import_file = file_path
        chr_cache.import_flags = import_flags
        # display name of character
        chr_cache.character_name = character_name

        # link_id (OBJ exports don't have json)
        chr_cache.set_link_id(link_id)

        # determine the main texture dir
        chr_cache.import_embedded = False

        for obj in objects:
            if utils.object_exists_is_mesh(obj):
                chr_cache.add_object_cache(obj)

        for obj_cache in chr_cache.object_cache:
            # scale obj import by 1/100
            obj = obj_cache.get_object()
            if obj:
                obj.scale = (0.01, 0.01, 0.01)
                # objkey import is usually a single mesh with no materials
                # but this is overridable in the pipeline plugin
                if obj.data.materials and len(obj.data.materials) > 0:
                    cache_object_materials(chr_cache, obj, json_data, processed)

        shaders.init_character_property_defaults(chr_cache, chr_json)
        basic.init_basic_default(chr_cache)

        # material setup mode
        chr_cache.setup_mode = props.setup_mode

        # character render target
        chr_cache.render_target = prefs.render_target

        imported_characters.append(chr_cache.link_id)

    utils.log_info("")
    return imported_characters


def obj_import(file_path, split_objects=False, split_groups=False, vgroups=False):
    split_mode="ON" if (split_objects or split_groups) else "OFF"
    if utils.B350():
        bpy.ops.wm.obj_import(filepath=file_path,
                              use_split_objects=split_objects,
                              use_split_groups=split_groups,
                              import_vertex_groups=vgroups)
    else:
        bpy.ops.import_scene.obj(filepath=file_path,
                                 split_mode=split_mode,
                                 use_split_objects=split_objects,
                                 use_split_groups=split_groups,
                                 use_groups_as_vgroups=vgroups)
#
#
class ImportFlags(IntFlag):
    NONE = 0
    FBX = 1
    OBJ = 2
    GLB = 4
    VRM = 8
    USD = 16
    RLX = 32
    RL = 1024
    KEY = 2048
    RL_FBX = RL | FBX
    RL_OBJ = RL | OBJ
    RL_RLX = RL | RLX
    RL_FBX_KEY = RL_FBX | KEY
    RL_OBJ_KEY = RL_OBJ | KEY


# Import operator
#



class CC3Import(bpy.types.Operator):
    """Import CC3 Character and build materials"""
    bl_idname = "cc3.importer"
    bl_label = "Import"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(
        name="Filepath",
        description="Filepath of the model to import.",
        subtype="FILE_PATH"
        )

    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    files: bpy.props.CollectionProperty(
            type=bpy.types.OperatorFileListElement,
            options={'HIDDEN', 'SKIP_SAVE'}
    )

    link_id: bpy.props.StringProperty(
        default="",
        name="Link ID",
        description="Link ID override",
        options={"HIDDEN"},
    )

    process_only: bpy.props.StringProperty(
        default="",
        options={"HIDDEN"},
    )

    no_build: bpy.props.BoolProperty(
        default=False,
        name="No Build",
        description="Don't build materials",
        options={"HIDDEN"},
    )

    no_rigify: bpy.props.BoolProperty(
        default=False,
        name="Don't Rigify",
        description="Don't Rigify Character",
        options={"HIDDEN"},
    )

    filter_glob: bpy.props.StringProperty(
        default="*.fbx;*.obj;*.glb;*.gltf;*.vrm;*.usd*",
        options={"HIDDEN"},
        )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    motion_prefix: bpy.props.StringProperty(
        name = "Motion Prefix",
        default = ""
    )

    use_fake_user: bpy.props.BoolProperty(
        name = "Use Fake User",
        default = True
    )

    use_anim: bpy.props.BoolProperty(name = "Import Animation", description = "Import animation with character.\nWarning: long animations take a very long time to import in Blender 2.83", default = True)

    zoom: bpy.props.BoolProperty(
        default=False,
        name="Zoom View",
        description="Zoom view to imported character",
    )

    count = 0
    running = False
    imported = False
    built = False
    lighting = False
    timer = None
    clock = 0
    invoked = False
    imported_character_ids: list = None
    imported_materials = []
    imported_images = []
    import_report = []
    import_warn_level = 0
    is_morph = False


    def read_json_data(self, file_path, stage = 0):

        # if not fbx, return no json without error
        path, ext = os.path.splitext(file_path)
        if not utils.is_file_ext(ext, "FBX"):
            return None

        errors = []
        # importer operator should always read the original intended json data
        json_data = jsonutils.read_json(file_path, errors, no_local=True)

        msg = None
        if "NO_JSON" in errors:
            msg = "Character has no Json data, using default values."
        elif "CORRUPT" in errors:
            if stage == 0:
                msg = "Corrupted Json data! \nThis character will not set up correctly!"
            else:
                msg = "Corrupted Json data! \nThis character will not have been set up correctly!"
        elif "PATH_FAILED" in errors:
            if stage == 0:
                msg = "Unable to locate Json file path! \nThis character will not set up correctly!"
            else:
                msg = "Unable to locate Json file path! \nThis character will not have been set up correctly!"

        if msg and msg not in self.import_report:
            self.import_report.append(msg)

        return json_data


    def import_character(self, context):
        props = vars.props()
        prefs = vars.prefs()

        utils.start_timer()

        utils.log_info("")
        utils.log_info("Importing Character Model:")
        utils.log_info("--------------------------")

        import_anim = self.use_anim

        # multi selected files
        file_paths = self.get_file_paths()
        for filepath in file_paths:

            # override link id only if not multi import
            if len(file_paths) > 1:
                self.link_id = ""

            import_flags, param = self.detect_import_mode_from_files(filepath)

            dir, file = os.path.split(filepath)
            name, ext = os.path.splitext(file)
            imported = None
            actions = None

            json_data = self.read_json_data(filepath, stage = 0)
            json_generation = jsonutils.get_character_generation_json(json_data, name)
            avatar_type = jsonutils.get_json(json_data, f"{name}/Avatar_Type")

            only_objects = utils.names_to_list(self.process_only, "|")

            if ImportFlags.FBX in import_flags:

                # invoke the fbx importer
                old_objects = utils.get_set(bpy.data.objects)
                old_images = utils.get_set(bpy.data.images)
                old_actions = utils.get_set(bpy.data.actions)

                # in ACES color space, this will fail trying to set up the textures as it tries to use 'Non-Color' space.
                # But the mesh is really all we need, so just keep going...
                if colorspace.is_aces():
                    try:
                        bpy.ops.import_scene.fbx(filepath=filepath, directory=dir, use_anim=import_anim, use_image_search=False, use_custom_normals=True)
                    except:
                        utils.log_warn("FBX Import Error: This may be due to color space differences. Continuing...")
                else:
                    try:
                        bpy.ops.import_scene.fbx(filepath=filepath, directory=dir, use_anim=import_anim, use_image_search=False, use_custom_normals=True)
                    except:
                        utils.log_error("FBX Import Error due to bad mesh?")

                imported = utils.get_set_new(bpy.data.objects, old_objects)
                actions = utils.get_set_new(bpy.data.actions, old_actions)
                self.imported_images = utils.get_set_new(bpy.data.images, old_images)

                remove_objects = []
                if only_objects:
                    for obj in imported:
                        if obj.type == "ARMATURE": continue
                        source_name = utils.strip_name(obj.name)
                        if source_name in only_objects: continue
                        remove_objects.append(obj)
                for obj in remove_objects:
                    imported.remove(obj)
                    purge_imported_object(obj, self.imported_images)

                for action in actions:
                    action.use_fake_user = self.use_fake_user

                armatures, rl_armatures, cameras, lights, import_flags = self.get_import_contents(imported, avatar_type, json_generation, import_flags)

                # detect characters and objects
                imported_character_ids = None
                if ImportFlags.RL in import_flags:
                    imported_character_ids = process_rl_import(filepath, import_flags, armatures, rl_armatures, cameras, lights,
                                                            imported, actions, json_data, self.import_report, self.link_id,
                                                            only_objects=only_objects,
                                                            motion_prefix=self.motion_prefix)
                elif prefs.import_auto_convert:
                    chr_cache = characters.convert_generic_to_non_standard(imported, filepath, link_id=self.link_id)
                    imported_character_ids = [chr_cache.link_id]

                # add the imported characters
                if imported_character_ids:
                    self.imported_character_ids.extend(imported_character_ids)

                if imported_character_ids and ImportFlags.RL in import_flags:
                    imported_characters = props.get_characters_by_link_id(imported_character_ids)
                    for chr_cache in imported_characters:
                        # set up the collision shapes and store their bind positions in the json data
                        rigidbody.build_rigid_body_colliders(chr_cache, json_data, first_import = True)
                        # remove the colliders for now (only needed for spring bones)
                        rigidbody.remove_rigid_body_colliders(chr_cache.get_armature())

                utils.log_timer("Done .Fbx Import.")

            elif ImportFlags.OBJ in import_flags:

                # invoke the obj importer
                old_objects = utils.get_set(bpy.data.objects)
                old_images = utils.get_set(bpy.data.images)
                if ImportFlags.RL in import_flags and param == "IMPORT_MORPH":
                    obj_import(filepath, split_objects=False, split_groups=False, vgroups=True)
                else:
                    obj_import(filepath, split_objects=True, split_groups=True, vgroups=False)

                imported = utils.get_set_new(bpy.data.objects, old_objects)
                self.imported_images = utils.get_set_new(bpy.data.images, old_images)

                # detect characters and objects
                armatures = []
                rl_armatures = []
                cameras = []
                lights = []
                imported_character_ids = None
                if ImportFlags.RL in import_flags:
                    imported_character_ids = process_rl_import(filepath, import_flags, armatures, rl_armatures, cameras, lights,
                                                            imported, actions, json_data, self.import_report, self.link_id,
                                                            motion_prefix=self.motion_prefix)
                elif prefs.import_auto_convert:
                    chr_cache = characters.convert_generic_to_non_standard(imported, filepath, link_id=self.link_id)
                    imported_character_ids = [ chr_cache.link_id ]

                # add the imported characters
                if imported_character_ids:
                    self.imported_character_ids.extend(imported_character_ids)

                #if param == "IMPORT_MORPH":
                #    if self.imported_character.get_tex_dir() != "":
                #        reconstruct_obj_materials(obj)
                #        pass

                utils.log_timer("Done .Obj Import.")

            elif ImportFlags.RLX in import_flags:
                imported = rlx.import_rlx(filepath)

            elif ImportFlags.GLB in import_flags:

                # invoke the GLTF importer
                old_images = utils.get_set(bpy.data.images)
                bpy.ops.import_scene.gltf(filepath=filepath)
                imported = bpy.context.selected_objects.copy()
                self.imported_images = utils.get_set_new(bpy.data.images, old_images)

                chr_cache = None
                if prefs.import_auto_convert:
                    chr_cache = characters.convert_generic_to_non_standard(imported, filepath, link_id=self.link_id)

                # add the imported characters
                if chr_cache:
                    self.imported_character_ids.append(chr_cache.link_id)

                utils.log_timer("Done .GLTF Import.")

            elif ImportFlags.VRM in import_flags:

                # copy .vrm to .glb
                glb_path = os.path.join(dir, name + "_temp.glb")
                shutil.copyfile(filepath, glb_path)
                filepath = glb_path

                # invoke the GLTF importer
                old_images = utils.get_set(bpy.data.images)
                bpy.ops.import_scene.gltf(filepath = filepath, bone_heuristic="TEMPERANCE")
                imported = bpy.context.selected_objects.copy()
                self.imported_images = utils.get_set_new(bpy.data.images, old_images)

                # find the armature and rotate it 180 degrees in Z
                armature : bpy.types.Object = utils.get_armature_from_objects(imported)
                hik.fix_armature(armature)
                utils.try_select_objects(imported)

                os.remove(glb_path)

                chr_cache = None
                if prefs.import_auto_convert:
                    chr_cache = characters.convert_generic_to_non_standard(imported, filepath, link_id=self.link_id)

                # add the imported characters
                if chr_cache:
                    self.imported_character_ids.append(chr_cache.link_id)

                utils.log_timer("Done .vrm Import.")

            elif ImportFlags.USD in import_flags:

                # invoke the USD importer
                old_images = utils.get_set(bpy.data.images)
                bpy.ops.wm.usd_import(filepath=filepath)
                imported = bpy.context.selected_objects.copy()
                self.imported_images = utils.get_set_new(bpy.data.images, old_images)

                chr_cache = None
                if prefs.import_auto_convert:
                    chr_cache = characters.convert_generic_to_non_standard(imported, filepath, link_id=self.link_id)

                # add the imported characters
                if chr_cache:
                    self.imported_character_ids.append(chr_cache.link_id)

                utils.log_timer("Done .USD Import?")


    def build_materials(self, context):
        objects_processed = []
        props: properties.CC3ImportProps = vars.props()
        prefs = vars.prefs()

        utils.start_timer()

        utils.log_info("")
        utils.log_info("Building Character Materials:")
        utils.log_info("-----------------------------")

        lib.check_node_groups()

        if self.imported_character_ids:
            on_import = True
            imported_characters = props.get_characters_by_link_id(self.imported_character_ids)
        else:
            on_import = False
            chr_cache = props.get_context_character_cache(context)
            imported_characters = [ chr_cache ]

        chr_cache: properties.CC3CharacterCache
        for chr_cache in imported_characters:

            if ImportFlags.RL not in ImportFlags(chr_cache.import_flags): continue

            # for any objects with shape keys expand the slider range to -1.5 - 1.5
            # Character Creator and iClone both use negative ranges extensively.
            for obj in chr_cache.get_cache_objects():
                obj_cache = chr_cache.get_object_cache(obj)
                if obj_cache and obj_cache.is_mesh():
                    init_shape_key_range(obj)

            json_data = self.read_json_data(chr_cache.import_file, stage = 1)
            if not on_import:
                # when rebuilding, use the currently selected render target
                chr_cache.render_target = prefs.render_target

            chr_json = jsonutils.get_character_json(json_data, chr_cache.get_character_id())

            if self.param == "BUILD":
                chr_cache.check_material_types(chr_json)

            # update character data props
            chr_cache.check_ids()

            if prefs.import_deduplicate:
                processed_images = []
                processed_materials = []
            else:
                processed_images = None
                processed_materials = None

            if props.build_mode == "IMPORTED":
                chr_objects = chr_cache.get_cache_objects()
                for obj in chr_objects:
                    obj_cache = chr_cache.get_object_cache(obj)
                    if obj and obj_cache:
                        process_object(chr_cache, obj, obj_cache, objects_processed,
                                       chr_json, processed_materials, processed_images)

                # setup default physics
                if props.physics_mode:
                    utils.log_info("")
                    physics.apply_all_physics(chr_cache)

                chr_cache.build_count += 1

            # only processes the selected objects that are listed in the import_cache (character)
            elif props.build_mode == "SELECTED":
                for obj in bpy.context.selected_objects:
                    obj_cache = chr_cache.get_object_cache(obj)
                    if obj_cache:
                        process_object(chr_cache, obj, obj_cache, objects_processed,
                                       chr_json, processed_materials, processed_images)

                    chr_cache.build_count += 1

        # enable SSR
        if prefs.refractive_eyes == "SSR":
            if not utils.B420():
                bpy.context.scene.eevee.use_ssr = True
                bpy.context.scene.eevee.use_ssr_refraction = True

        utils.log_timer("Done Build.", "s")


    def build_drivers(self, context, rebuild_wrinkle=False):
        props: properties.CC3ImportProps = vars.props()
        prefs = vars.prefs()

        utils.start_timer()

        utils.log_info("")
        utils.log_info("Building Character Drivers:")
        utils.log_info("---------------------------")

        if self.imported_character_ids:
            imported_characters = props.get_characters_by_link_id(self.imported_character_ids)
        else:
            chr_cache = props.get_context_character_cache(context)
            imported_characters = [ chr_cache ]

        chr_cache: properties.CC3CharacterCache
        for chr_cache in imported_characters:

            if ImportFlags.RL not in ImportFlags(chr_cache.import_flags): continue
            if ImportFlags.FBX not in ImportFlags(chr_cache.import_flags): continue

            # for any objects with shape keys expand the slider range to -1.5 - 1.5
            # Character Creator and iClone both use negative ranges extensively.
            for obj in chr_cache.get_cache_objects():
                obj_cache = chr_cache.get_object_cache(obj)
                if obj_cache and obj_cache.is_mesh():
                    init_shape_key_range(obj)

            json_data = self.read_json_data(chr_cache.import_file, stage=1)
            chr_json = jsonutils.get_character_json(json_data, chr_cache.get_character_id())

            # update character data props
            chr_cache.check_ids()

            if chr_cache.rigified:
                rigify_rig = chr_cache.get_armature()
                drivers.clear_facial_shape_key_bone_drivers(chr_cache)
                if rigutils.is_face_rig(rigify_rig):
                    facerig.build_facerig_drivers(chr_cache, rigify_rig)
                else:
                    rigging.add_shape_key_drivers(chr_cache, chr_cache.get_armature())
            else:
                facial_profile, viseme_profile = chr_cache.get_facial_profile()
                facial_name, viseme_name = chr_cache.get_facial_profile_names()
                utils.log_info(f"Facial Profile: {facial_name}")
                utils.log_info(f"Viseme Profile: {viseme_name}")
                if facial_profile == "STD" or facial_profile == "EXT" or facial_profile == "TRA":
                    drivers.add_facial_shape_key_bone_drivers(chr_cache,
                                               prefs.build_shape_key_bone_drivers_jaw,
                                               prefs.build_shape_key_bone_drivers_eyes,
                                               prefs.build_shape_key_bone_drivers_head)

            driver_objects = chr_cache.get_all_objects(include_armature=False,
                                                       of_type="MESH",
                                                       only_selected=(props.build_mode=="SELECTED"))
            drivers.add_body_shape_key_drivers(chr_cache, prefs.build_body_key_drivers, driver_objects)

            if rebuild_wrinkle:
                wrinkle.build_wrinkle_drivers(chr_cache, chr_json, wrinkle_shader_name=wrinkle.WRINKLE_SHADER_NAME)

        utils.log_timer("Done Build.", "s")


    def remove_drivers(self, context):
        props: properties.CC3ImportProps = vars.props()

        utils.start_timer()

        utils.log_info("")
        utils.log_info("Building Character Drivers:")
        utils.log_info("---------------------------")

        if self.imported_character_ids:
            imported_characters = props.get_characters_by_link_id(self.imported_character_ids)
        else:
            chr_cache = props.get_context_character_cache(context)
            imported_characters = [ chr_cache ]

        chr_cache: properties.CC3CharacterCache
        for chr_cache in imported_characters:

            if ImportFlags.RL not in ImportFlags(chr_cache.import_flags): continue

            # update character data props
            chr_cache.check_ids()

            if chr_cache.rigified:
                rigify_rig = chr_cache.get_armature()
                # by very careful removing drivers from a rigify rig ...
            else:
                drivers.clear_facial_shape_key_bone_drivers(chr_cache)

            # remove all expression based shape key drivers
            driver_objects = chr_cache.get_all_objects(include_armature=False,
                                                       of_type="MESH",
                                                       only_selected=(props.build_mode=="SELECTED"))
            #drivers.add_body_shape_key_drivers(chr_cache, False, driver_objects)
            drivers.clear_body_shape_key_drivers(chr_cache, driver_objects)

        utils.log_timer("Done Build.", "s")


    def detect_import_mode_from_files(self, filepath):
        # detect if we are importing a character for morph/accessory editing (i.e. has a key file)
        dir, file = os.path.split(filepath)
        name, ext = os.path.splitext(file)

        textures_path = os.path.join(dir, "textures", name)
        json_path = os.path.join(dir, name + ".json")

        import_flags = ImportFlags.NONE
        param = self.param

        if utils.is_file_ext(ext, "OBJ"):
            import_flags = import_flags | ImportFlags.OBJ
            obj_key_path = os.path.join(dir, name + ".ObjKey")
            if os.path.exists(obj_key_path):
                import_flags = import_flags | ImportFlags.RL
                import_flags = import_flags | ImportFlags.KEY
                param = "IMPORT_MORPH"
                self.is_morph = True
                utils.log_info("Importing as character morph with ObjKey. (nude character with bind pose)")
                return import_flags, param

        elif utils.is_file_ext(ext, "FBX"):
            import_flags = import_flags | ImportFlags.FBX
            obj_key_path = os.path.join(dir, name + ".fbxkey")
            if os.path.exists(obj_key_path):
                import_flags = import_flags | ImportFlags.RL
                import_flags = import_flags | ImportFlags.KEY
                param = "IMPORT_MORPH"
                self.is_morph = True
                utils.log_info("Importing as editable character with fbxkey.")
                return import_flags, param

        elif utils.is_file_ext(ext, "RLX"):
            import_flags = import_flags | ImportFlags.RLX
            import_flags = import_flags | ImportFlags.RL
            param = "IMPORT_RLX"
            utils.log_info("Importing RLX ...")
            return import_flags, param

        elif utils.is_file_ext(ext, "GLB") or utils.is_file_ext(ext, "GLTF"):
            import_flags = import_flags | ImportFlags.GLB
            utils.log_info("Importing generic GLB/GLTF character.")
            return import_flags, param

        elif utils.is_file_ext(ext, "VRM"):
            import_flags = import_flags | ImportFlags.VRM
            utils.log_info("Importing generic VRM character.")
            return import_flags, param

        elif utils.is_file_ext(ext, "USD") or utils.is_file_ext(ext, "USDZ"):
            import_flags = import_flags | ImportFlags.USD
            utils.log_info("Importing Universal Scene Descriptor file.")
            return import_flags, param

        if os.path.exists(json_path) or os.path.exists(textures_path):
            import_flags = import_flags | ImportFlags.RL
            utils.log_info("Importing RL character without key file.")
        else:
            utils.log_info("Importing generic character.")

        param = "IMPORT_QUALITY"

        return import_flags, param


    def get_import_contents(self, objects, avatar_type, json_generation, import_flags):
        armatures = []
        rl_armatures = []
        cameras = []
        lights = []
        if not avatar_type:
            if json_generation is not None and json_generation == "":
                avatar_type = "NoneStandard"
            elif json_generation is None:
                avatar_type = "None"
        for obj in objects:
            if utils.object_exists_is_armature(obj):
                if (avatar_type == "Standard" or
                    avatar_type == "NonHuman" or
                    avatar_type == "NonStandard" or
                    avatar_type == "StandardSeries" or
                    rigutils.is_GameBase_armature(obj) or
                    rigutils.is_ActorCore_armature(obj) or
                    rigutils.is_G3_armature(obj) or
                    rigutils.is_iClone_armature(obj)):
                    utils.log_info(f"RL character armature found: {obj.name}")
                    import_flags = import_flags | ImportFlags.RL
                    if obj not in rl_armatures:
                        rl_armatures.append(obj)
                else:
                    if obj not in armatures:
                        armatures.append(obj)
            elif utils.object_exists_is_camera(obj):
                if (avatar_type == "CAMERA" or
                    json_generation == "CAMERA"):
                    utils.log_info(f"RL Camera found: {obj.name}")
                    import_flags = import_flags | ImportFlags.RL
                if obj not in cameras:
                    cameras.append(obj)
            elif utils.object_exists_is_light(obj):
                if (avatar_type == "LIGHT" or
                    json_generation == "LIGHT"):
                    utils.log_info(f"RL Light found: {obj.name}")
                    import_flags = import_flags | ImportFlags.RL
                if obj not in lights:
                    lights.append(obj)
        return armatures, rl_armatures, cameras, lights, import_flags


    def do_import_report(self, context, stage = 0):
        if stage == 0: # FBX import and JSON report
            if self.import_report:
                utils.report_multi(self, "ERROR", self.import_report)
        elif stage == 1:
            if self.import_report:
                utils.report_multi(self, "ERROR", self.import_report)
            else:
                self.report({'INFO'}, "All Done!")
        self.import_report = []


    def run_import(self, context):
        self.import_character(context)
        self.imported = True


    def run_build(self, context):
        if self.imported_character_ids:
            self.build_materials(context)
            self.build_drivers(context)
        self.built = True


    def run_finish(self, context):
        props = vars.props()
        prefs = vars.prefs()

        if self.imported_character_ids:

            rl_import = False

            imported_characters = props.get_characters_by_link_id(self.imported_character_ids)

            for chr_cache in imported_characters:

                if ImportFlags.RL in ImportFlags(chr_cache.import_flags):
                    rl_import = True

            if rl_import:

                # use portrait lighting for quality mode
                if self.param == "IMPORT_QUALITY":
                    if props.lighting_mode:
                        scene.setup_scene_default(context, prefs.quality_lighting)

                if prefs.refractive_eyes == "SSR":
                    if not utils.B420():
                        bpy.context.scene.eevee.use_ssr = True
                        bpy.context.scene.eevee.use_ssr_refraction = True

                # set a minimum of 100 max transparency bounces:
                if bpy.context.scene.cycles.transparent_max_bounces < 100:
                    bpy.context.scene.cycles.transparent_max_bounces = 100

                bpy.ops.object.select_all(action='DESELECT')
                for chr_cache in imported_characters:
                    chr_cache.select(only=False)
                if self.zoom:
                    scene.zoom_to_selected()

                # clean up unused images from the import
                if len(self.imported_images) > 0:
                    utils.log_info("Cleaning up unused images:")
                    img: bpy.types.Image = None
                    for img in self.imported_images:
                        num_users = img.users
                        if (img.use_fake_user and img.users == 1) or img.users == 0:
                            utils.log_info("Removing Image: " + img.name)
                            bpy.data.images.remove(img)
                utils.clean_collection(bpy.data.images)

                props.lighting_mode = False

                if props.rigify_mode and not self.no_rigify:
                    for chr_cache in imported_characters:
                        if chr_cache.can_be_rigged():
                            cc3_rig = chr_cache.get_armature()
                            bpy.ops.cc3.rigifier(param="ALL")
                            rigging.full_retarget_source_rig_action(self, chr_cache, cc3_rig,
                                                                    use_ui_options=True)

        self.imported_character_ids = None
        self.imported_materials = []
        self.imported_images = []
        self.lighting = True


    def modal(self, context, event):

        # 60 second timeout
        if event.type == 'TIMER':
            self.clock = self.clock + 1
            if self.clock > 600:
                self.cancel(context)
                self.report({'INFO'}, "Import operator timed out!")
                return {'CANCELLED'}

        if event.type == 'TIMER' and self.clock > 10 and not self.running:

            self.count += 1
            if self.count > 99:
                self.count = 0
            context.window_manager.progress_update(self.count)

            if not self.imported:
                self.running = True
                self.run_import(context)
                self.do_import_report(context, stage = 0)
                self.clock = 0
                self.running = False

            elif not self.no_build and not self.built:
                self.running = True
                self.run_build(context)
                self.clock = 0
                self.running = False

            elif not self.no_build and not self.lighting:
                self.running = True
                self.run_finish(context)
                self.clock = 0
                self.running = False

            if self.imported and (self.no_build or (self.built and self.lighting)):
                self.cancel(context)
                self.do_import_report(context, stage = 1)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):
        if self.timer is not None:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None
            context.window_manager.progress_end()

    def get_file_paths(self):
        file_paths = []
        if not self.files or len(self.files) == 0:
            if os.path.exists(self.filepath):
                file_paths.append(self.filepath)
        else:
            for file in self.files:
                filepath = os.path.join(self.directory, file.name)
                if os.path.exists(filepath):
                    file_paths.append(filepath)
        return file_paths

    def execute(self, context):
        props = vars.props()
        prefs = vars.prefs()
        self.imported_character_ids = []
        self.imported_materials = []
        self.imported_images = []
        self.import_report = []

        context.window_manager.progress_begin(0, 99)
        self.count = 0

        # import character
        if "IMPORT" in self.param:
            file_paths = self.get_file_paths()
            if file_paths:
                if self.invoked and self.timer is None:
                    self.imported = False
                    self.built = False
                    self.lighting = False
                    self.running = False
                    self.clock = 0
                    self.report({'INFO'}, "Importing Character, please wait for import to finish and materials to build...")
                    bpy.context.window_manager.modal_handler_add(self)
                    self.timer = context.window_manager.event_timer_add(0.1, window = bpy.context.window)
                    return {'PASS_THROUGH'}
                elif not self.invoked:
                    self.run_import(context)
                    if not self.no_build:
                        self.run_build(context)
                    self.run_finish(context)
                    self.do_import_report(context, stage = 1)
                    return {'FINISHED'}
            else:
                utils.log_error(f"Invalid filepaths!")

        # build materials
        elif self.param == "BUILD":
            chr_cache = props.get_context_character_cache(context)
            if chr_cache:
                mode_selection = utils.store_mode_selection_state()
                utils.object_mode()
                self.build_materials(context)
                self.build_drivers(context)
                self.do_import_report(context, stage = 1)
                utils.restore_mode_selection_state(mode_selection)

        elif self.param == "BUILD_DRIVERS":
            chr_cache = props.get_context_character_cache(context)
            if chr_cache:
                mode_selection = utils.store_mode_selection_state()
                utils.object_mode()
                self.build_drivers(context, rebuild_wrinkle=True)
                self.report({"INFO"}, "Drivers Rebuilt!")
                utils.restore_mode_selection_state(mode_selection)

        elif self.param == "REMOVE_DRIVERS":
            chr_cache = props.get_context_character_cache(context)
            if chr_cache:
                mode_selection = utils.store_mode_selection_state()
                utils.object_mode()
                self.remove_drivers(context)
                self.report({"INFO"}, "Drivers Removed!")
                utils.restore_mode_selection_state(mode_selection)

        # rebuild the node groups for advanced materials
        elif self.param == "REBUILD_NODE_GROUPS":
            utils.object_mode()
            lib.rebuild_node_groups()
            utils.clean_collection(bpy.data.images)
            self.build_materials(context)
            self.build_drivers(context)
            self.do_import_report(context, stage = 1)

        elif self.param == "DELETE_CHARACTER":
            chr_cache = props.get_context_character_cache(context)
            if chr_cache:
                delete_import(chr_cache)

        elif self.param == "REBUILD_EEVEE":
            chr_cache = props.get_context_character_cache(context)
            if chr_cache:
                utils.object_mode()
                prefs.render_target = "EEVEE"
                prefs.refractive_eyes = "PARALLAX"
                if chr_cache.render_target != "EEVEE":
                    utils.log_info("Character is currently build for Cycles Rendering.")
                    utils.log_info("Rebuilding Character for Eevee Rendering...")
                    self.build_materials(context)
                    self.build_drivers(context)

        elif self.param == "REBUILD_BAKE":
            chr_cache = props.get_context_character_cache(context)
            if chr_cache:
                utils.object_mode()
                prefs.render_target = "EEVEE"
                props.wrinkle_mode = False
                if chr_cache.render_target != "EEVEE":
                    utils.log_info("Character is currently build for Cycles Rendering.")
                    utils.log_info("Rebuilding Character for Eevee Rendering...")
                    self.build_materials(context)
                    self.build_drivers(context)

        elif self.param == "REBUILD_CYCLES":
            chr_cache = props.get_context_character_cache(context)
            if chr_cache:
                utils.object_mode()
                prefs.render_target = "CYCLES"
                prefs.refractive_eyes = "SSR"
                if chr_cache.render_target != "CYCLES":
                    utils.log_info("Character is currently build for Eevee Rendering.")
                    utils.log_info("Rebuilding Character for Cycles Rendering...")
                    self.build_materials(context)
                    self.build_drivers(context)

        return {"FINISHED"}


    def invoke(self, context, event):
        if "IMPORT" in self.param:
            context.window_manager.fileselect_add(self)
            self.invoked = True
            return {"RUNNING_MODAL"}

        return self.execute(context)


    @classmethod
    def description(cls, context, properties):
        if "IMPORT" in properties.param:
            return "Import a new .fbx or .obj character exported by Character Creator 3.\n" \
                   "Notes for exporting from CC3:\n" \
                   " - For round trip-editing (exporting character back to CC3), export as FBX: 'Mesh Only' or 'Mesh and Motion' with Calibration, from CC3, as this guarantees generation of the .fbxkey file needed to re-import the character back to CC3.\n" \
                   " - For creating morph sliders, export as OBJ: Nude Character in Bind Pose from CC3, as this is the only way to generate the .ObjKey file for morph slider creation in CC3.\n" \
                   " - FBX export with motion in 'Current Pose' or 'Custom Motion' does not export an .fbxkey and cannot be exported back to CC3.\n" \
                   " - OBJ export 'Character with Current Pose' does not create an .objkey and cannot be exported back to CC3.\n" \
                   " - OBJ export 'Nude Character in Bind Pose' .obj does not export any materials"
        elif properties.param == "BUILD":
            return "Rebuild materials and drivers for the current imported character with the current build settings"
        elif properties.param == "BUILD_DRIVERS":
            return "Rebuild the facial expression shape-key and bone drivers for the current imported character with the current build settings"
        elif properties.param == "REMOVE_DRIVERS":
            return "Remove the facial expression shape-key and bone drivers for the current imported character"
        elif properties.param == "DELETE_CHARACTER":
            return "Removes the character and any associated objects, meshes, materials, nodes, images, armature actions and shapekeys. Basically deletes everything not nailed down.\n**Do not press this if there is anything you want to keep!**"
        elif properties.param == "REBUILD_NODE_GROUPS":
            return "Rebuilds the shader node groups for for all material shaders"
        return ""


class CC3ImportAnimations(bpy.types.Operator):
    """Import CC3 animations"""
    bl_idname = "cc3.anim_importer"
    bl_label = "Import Animations"
    bl_options = {"REGISTER", "UNDO", 'PRESET'}

    filepath: bpy.props.StringProperty(
        name="Filepath",
        description="Filepath of the fbx to import.",
        subtype="FILE_PATH"
    )

    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    files: bpy.props.CollectionProperty(
            type=bpy.types.OperatorFileListElement,
            options={'HIDDEN', 'SKIP_SAVE'}
    )

    filter_glob: bpy.props.StringProperty(
        default="*.fbx",
        options={"HIDDEN"}
    )

    remove_meshes: bpy.props.BoolProperty(
        default = True,
        description="Remove all imported mesh objects.",
        name="Remove Meshes",
    )

    remove_materials_images: bpy.props.BoolProperty(
        default = True,
        description="Remove all imported materials and image textures.",
        name="Remove Materials & Images",
    )

    remove_shape_keys: bpy.props.BoolProperty(
        default = False,
        description="Remove Shapekey actions along with their meshes.",
        name="Remove Shapekey Actions",
    )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
    )

    motion_prefix: bpy.props.StringProperty(
        name = "Motion Prefix",
        default = ""
    )

    use_fake_user: bpy.props.BoolProperty(
        name = "Use Fake User",
        default = True
    )

    def import_animation_fbx(self, dir, file):
        path = os.path.join(dir, file)
        name = file[:-4]

        utils.log_info(f"Importing Fbx file: {path}")

        # invoke the fbx importer
        old_objects = utils.get_set(bpy.data.objects)
        old_images = utils.get_set(bpy.data.images)
        old_actions = utils.get_set(bpy.data.actions)
        old_materials = utils.get_set(bpy.data.materials)
        bpy.ops.import_scene.fbx(filepath=path, directory=dir, use_anim=True, use_image_search=False)
        objects = utils.get_set_new(bpy.data.objects, old_objects)
        actions = utils.get_set_new(bpy.data.actions, old_actions)
        images = utils.get_set_new(bpy.data.images, old_images)
        materials = utils.get_set_new(bpy.data.materials, old_materials)

        for action in actions:
            action.use_fake_user = self.use_fake_user

        utils.log_info("Renaming actions:")
        utils.log_indent()

        # find all armatures
        armatures = []
        for obj in objects:
            if obj.type == "ARMATURE":
                armatures.append(obj)

        # assign animation sets
        for arm in armatures:
            armature_objects = utils.get_child_objects(arm)
            source_id = arm.name
            # just one armature is always named 'Armature'
            if len(armatures) == 1:
                arm.name = name
                arm.data.name = name
            shapekey_actions = remap_action_names(arm, armature_objects, actions, source_id,
                                                  motion_prefix=self.motion_prefix)[1]
        utils.log_recess()

        utils.log_info("Cleaning up:")
        utils.log_indent()

        for obj in objects:
            if obj.type == "ARMATURE":
                obj.name = name
                if obj.data:
                    obj.data.name = name

        if self.remove_meshes:
            # only interested in actions, delete the rest
            for obj in objects:
                if obj.type != "ARMATURE":
                    utils.log_info(f"Removing Object: {obj.name}")
                    utils.delete_mesh_object(obj)
            # and optionally remove the shape keys
            if self.remove_shape_keys:
                for action in shapekey_actions:
                    utils.log_info(f"Removing Shapekey Action: {action.name}")
                    bpy.data.actions.remove(action)

        if self.remove_materials_images:
            for img in images:
                utils.log_info(f"Removing Image: {img.name}")
                bpy.data.images.remove(img)

            for mat in materials:
                utils.log_info(f"Removing Material: {mat.name}")
                bpy.data.materials.remove(mat)

        utils.log_recess()

        return

    def execute(self, context):
        props = vars.props()
        prefs = vars.prefs()

        utils.start_timer()

        utils.log_info("")
        utils.log_info("Importing FBX Animations:")
        utils.log_info("-------------------------")

        for fbx_file in self.files:
            self.import_animation_fbx(self.directory, fbx_file.name)

        if not self.files and self.filepath:
            dir, file = os.path.split(self.filepath)
            self.import_animation_fbx(dir, file)

        utils.log_timer("Done Build.", "s")

        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    @classmethod
    def description(cls, context, properties):
        return ""


def menu_func_import(self, context):
    self.layout.operator(CC3Import.bl_idname, text="Reallusion Character (.fbx, .obj, .vrm)").param = "IMPORT_MENU"


def menu_func_import_animation(self, context):
    self.layout.operator(CC3ImportAnimations.bl_idname, text="Reallusion Animation (.fbx)")

