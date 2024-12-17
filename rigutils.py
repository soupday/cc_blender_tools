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
from mathutils import Vector, Matrix, Quaternion, Euler
from random import random
import re
from . import springbones, bones, modifiers, rigify_mapping_data, utils, vars


def edit_rig(rig):
    if rig and utils.edit_mode_to(rig):
        return True
    utils.log_error(f"Unable to edit rig: {rig}!")
    return False


def select_rig(rig):
    if rig and utils.object_mode_to(rig):
        return True
    utils.log_error(f"Unable to select rig: {rig}!")
    return False


def pose_rig(rig):
    if rig and utils.pose_mode_to(rig):
        return True
    utils.log_error(f"Unable to pose rig: {rig}!")
    return False


def name_in_data_paths(action, name):
    for fcurve in action.fcurves:
        if name in fcurve.data_path:
            return True
    return False


def name_in_pose_bone_data_paths_regex(action, name):
    name = ".*" + name
    for fcurve in action.fcurves:
        if re.match(name, fcurve.data_path):
            return True
    return False


def bone_name_in_armature_regex(arm, name):
    for bone in arm.data.bones:
        if re.match(name, bone.name):
            return True
    return False


def is_G3_action(action):
    if action:
        if len(action.fcurves) > 0:
            for bone_name in rigify_mapping_data.CC3_BONE_NAMES:
                if not name_in_data_paths(action, bone_name):
                    return False
            return True
    return False


def is_G3_armature(armature):
    if armature:
        if len(armature.data.bones) > 0:
            for bone_name in rigify_mapping_data.CC3_BONE_NAMES:
                if bone_name not in armature.data.bones:
                    return False
            return True
    return False


def is_iClone_action(action):
    if action:
        if len(action.fcurves) > 0:
            for bone_name in rigify_mapping_data.ICLONE_BONE_NAMES:
                if not name_in_data_paths(action, bone_name):
                    return False
            return True
    return False


def is_iClone_armature(armature):
    if armature:
        if len(armature.data.bones) > 0:
            for bone_name in rigify_mapping_data.ICLONE_BONE_NAMES:
                if bone_name not in armature.data.bones:
                    return False
            return True
    return False


def is_ActorCore_action(action):
    if action:
        if len(action.fcurves) > 0:
            for bone_name in rigify_mapping_data.ACTOR_CORE_BONE_NAMES:
                if not name_in_data_paths(action, bone_name):
                    return False
            return True
    return False


def is_ActorCore_armature(armature):
    if armature:
        if len(armature.data.bones) > 0:
            for bone_name in rigify_mapping_data.ACTOR_CORE_BONE_NAMES:
                if bone_name not in armature.data.bones:
                    return False
            return True
    return False


def is_GameBase_action(action):
    if action:
        if len(action.fcurves) > 0:
            for bone_name in rigify_mapping_data.GAME_BASE_BONE_NAMES:
                if not name_in_data_paths(action, bone_name):
                    return False
            return True
    return False


def is_GameBase_armature(armature):
    if armature:
        if len(armature.data.bones) > 0:
            for bone_name in rigify_mapping_data.GAME_BASE_BONE_NAMES:
                if bone_name not in armature.data.bones:
                    return False
            return True
    return False


def is_Mixamo_action(action):
    if action:
        if len(action.fcurves) > 0:
            for bone_name in rigify_mapping_data.MIXAMO_BONE_NAMES:
                if not name_in_pose_bone_data_paths_regex(action, bone_name):
                    return False
            return True
    return False


def is_Mixamo_armature(armature):
    if armature:
        if len(armature.data.bones) > 0:
            for bone_name in rigify_mapping_data.MIXAMO_BONE_NAMES:
                if not bone_name_in_armature_regex(armature, bone_name):
                    return False
            return True
    return False


def is_rigify_action(action):
    if action:
        if len(action.fcurves) > 0:
            for bone_name in rigify_mapping_data.RIGIFY_BONE_NAMES:
                if not name_in_data_paths(action, bone_name):
                    return False
            return True
    return False


def is_rigify_armature(armature):
    if armature:
        if len(armature.data.bones) > 0:
            for bone_name in rigify_mapping_data.RIGIFY_BONE_NAMES:
                if bone_name not in armature.data.bones:
                    return False
            return True
    return False


def is_rl_rigify_action(action):
    if action:
        if len(action.fcurves) > 0:
            for bone_name in rigify_mapping_data.RL_RIGIFY_BONE_NAMES:
                if not name_in_data_paths(action, bone_name):
                    return False
            return True
    return False


def is_rl_rigify_armature(armature):
    if armature:
        if len(armature.data.bones) > 0:
            for bone_name in rigify_mapping_data.RL_RIGIFY_BONE_NAMES:
                if bone_name not in armature.data.bones:
                    return False
            return True
    return False


def is_rl_armature(armature):
    if (is_ActorCore_armature(armature) or
        is_G3_armature(armature) or
        is_GameBase_armature(armature) or
        is_iClone_armature(armature)):
        return True
    return False


def get_rig_generation(armature):
    if is_ActorCore_armature(armature):
        return "ActorCore"
    elif is_G3_armature(armature):
        return "G3"
    elif is_GameBase_armature(armature):
        return "GameBase"
    elif is_iClone_armature(armature):
        return "G3"
    else:
        return "Unknown"


def is_unity_action(action):
    return "_Unity" in action.name and "|A|" in action.name


def get_armature_action_source_type(armature, action=None):
    if armature and not action and armature.type == "ARMATURE":
        if is_G3_armature(armature):
            return "G3", "G3 (CC3/CC3+)"
        if is_iClone_armature(armature):
            return "G3", "G3 (iClone)"
        if is_ActorCore_armature(armature):
            return "G3", "G3 (ActorCore)"
        if is_GameBase_armature(armature):
            return "GameBase", "GameBase (CC3/CC3+)"
        if is_Mixamo_armature(armature):
            return "Mixamo", "Mixamo"
        if is_rl_rigify_armature(armature):
            return "Rigify+", "Rigify+"
        if is_rigify_armature(armature):
            return "Rigify", "Rigify"
    if armature and action and armature.type == "ARMATURE":
        if is_G3_armature(armature) and is_G3_action(action):
            return "G3", "G3 (CC3/CC3+)"
        if is_iClone_armature(armature) and is_iClone_action(action):
            return "G3", "G3 (iClone)"
        if is_ActorCore_armature(armature) and is_ActorCore_action(action):
            return "G3", "G3 (ActorCore)"
        if is_GameBase_armature(armature) and is_GameBase_action(action):
            return "GameBase", "GameBase (CC3/CC3+)"
        if is_Mixamo_armature(armature) and is_Mixamo_action(action):
            return "Mixamo", "Mixamo"
        if is_rl_rigify_armature(armature) and is_rl_rigify_action(action):
            return "Rigify+", "Rigify+"
        if is_rigify_armature(armature) and is_rigify_action(action):
            return "Rigify", "Rigify"
    # detect other types as they become available...
    return "Unknown", "Unknown"


def find_source_actions(source_action, source_rig=None):
    src_set_id, src_set_gen, src_type_id, src_object_id = get_motion_set(source_action)
    src_prefix, src_rig_id, src_type_id, src_object_id, src_motion_id = decode_action_name(source_action)
    if not src_motion_id:
        src_motion_id = get_action_motion_id(source_action)

    actions = {
        "motion_info": {
            "prefix": src_prefix,
            "rig_id": src_rig_id,
            "motion_id": src_motion_id,
            "set_id": src_set_id,
            "set_generation": src_set_gen,
        },
        "count": 0,
        "armature": None,
        "keys": {},
    }

    # try matching actions by set_id (disabled for now: testing name patterns first)
    if src_set_id:
        utils.log_info(f"Looking for motion set id: {src_set_id}")
        for action in bpy.data.actions:
            if "rl_set_id" in action:
                set_id, set_gen, type_id, object_id = get_motion_set(action)
                if set_id == src_set_id:
                    if type_id == "KEY":
                        utils.log_info(f" - Found shape-key action: {action.name} for {object_id}")
                        actions["keys"][object_id] = action
                    elif type_id == "ARM":
                        if not actions["armature"]:
                            utils.log_info(f" - Found armature action: {action.name}")
                            actions["armature"] = action
        return actions

    # try matching actions by action name pattern
    if src_type_id and src_motion_id:
        # match actions by name pattern
        utils.log_info(f"Looking for shape-key actions matching: [<{src_prefix}>|]{src_rig_id}|[K|A]|[<obj>|]{src_motion_id}")
        for action in bpy.data.actions:
            motion_prefix, rig_id, type_id, object_id, motion_id = decode_action_name(action)
            if (motion_id and object_id not in actions and
                motion_prefix == src_prefix and
                rig_id == src_rig_id and
                utils.partial_match(motion_id, src_motion_id)):
                if type_id == "K":
                    utils.log_info(f" - Found shape-key action: {action.name} for {object_id}")
                    actions["keys"][object_id] = action
                elif type_id == "A":
                    utils.log_info(f" - Found armature action: {action.name}")
                    actions["armature"] = action
        return actions

    # try to fetch shape-key actions from source armature child objects, if supplied
    elif source_rig:
        utils.log_info(f"Looking for shape-key actions in armature child objects: {source_rig.name}")
        action = utils.safe_get_action(source_rig)
        if action:
            utils.log_info(f" - Found armature action: {action.name}")
            actions["armature"] = action
        for obj in source_rig.children:
            obj_id = get_action_obj_id(obj)
            if obj.type == "MESH":
                action = utils.safe_get_action(obj.data.shape_keys)
                if action:
                    utils.log_info(f" - Found shape-key action: {action.name} for {obj_id}")
                    actions["keys"][obj_id] = action
        return actions

    return actions


def get_main_body_action(source_actions):
    # find the "Body" action
    for obj_id in source_actions["keys"]:
        action: bpy.types.Action = source_actions["keys"][obj_id]
        l_name = obj_id.lower()
        if l_name == "body":
            utils.log_info(f" - Using main body action: {action.name}")
            return action
    # find the action with the most shape keys
    action_with_most_keys = None
    num_keys = 0
    for obj_id in source_actions["keys"]:
        action = source_actions["keys"][obj_id]
        if len(action.fcurves) > num_keys:
            num_keys = len(action.fcurves)
            action_with_most_keys = action
    if action_with_most_keys:
        utils.log_info(f" - Using action with most shape keys: {action_with_most_keys.name}")
    else:
        utils.log_info(f" - No shape key actions in this Motion set!")
    return action_with_most_keys


def apply_source_armature_action(dst_rig, source_actions, copy=False,
                                 motion_id=None, motion_prefix=None,
                                 set_id=None, set_generation=None):
    obj_used = []
    actions_used = []
    rig_id = get_rig_id(dst_rig)
    rl_arm_id = utils.get_rl_object_id(dst_rig)
    if not motion_id:
        motion_id = source_actions["motion_info"]["motion_id"]
    if motion_prefix is None:
        motion_prefix = source_actions["motion_info"]["prefix"]
    utils.log_info(f"Applying source armature action:")
    action = source_actions["armature"]
    if action:
        if copy and motion_id:
            action_name = make_armature_action_name(rig_id, motion_id, motion_prefix)
            utils.log_info(f" - Copying action: {action.name} to {action_name}")
            action = utils.copy_action(action, action_name)
            if set_id and set_generation:
                add_motion_set_data(action, set_id, set_generation, rl_arm_id=rl_arm_id)
        utils.log_info(f" - Applying action: {action.name} to {rig_id}")
        utils.safe_set_action(dst_rig, action)
        obj_used.append(dst_rig)
        actions_used.append(action)
    return obj_used, actions_used


def apply_source_key_actions(dst_rig, source_actions, all_matching=False, copy=False,
                             motion_id=None, motion_prefix=None,
                             set_id=None, set_generation=None,
                             filter=None):
    obj_used = []
    key_actions = {}
    rig_id = get_rig_id(dst_rig)
    if motion_id == "" or motion_id == "TEMP":
        motion_id = "TEMP_" + utils.generate_random_id(12)
    if motion_id is None:
        motion_id = source_actions["motion_info"]["motion_id"]
    if motion_prefix is None:
        motion_prefix = source_actions["motion_info"]["prefix"]

    # TODO this should really collect all named shape key animation tracks across all source objects
    #      and create actions specific to each target object.
    #      e.g. facial hair meshes have tongue shape keys which the body action alone doesn't have.

    # apply to exact matches first
    utils.log_info(f"Applying source key actions: (copy={copy}, motion_id={motion_id})")
    objects = utils.get_child_objects(dst_rig)
    for obj in objects:
        if filter and obj not in filter: continue
        if obj.type == "MESH":
            if utils.object_has_shape_keys(obj):
                obj_id = get_action_obj_id(obj)
                if (obj_id in source_actions["keys"] and
                    obj_has_action_shape_keys(obj, source_actions["keys"][obj_id])):
                    action = source_actions["keys"][obj_id]
                    if copy and motion_id:
                        action_name = make_key_action_name(rig_id, motion_id, obj_id, motion_prefix)
                        utils.log_info(f" - Copying action: {action.name} to {action_name}")
                        action = utils.copy_action(action, action_name)
                        if set_id and set_generation:
                            add_motion_set_data(action, set_id, set_generation, obj_id=obj_id)
                    utils.log_info(f" - Applying action: {action.name} to {obj_id}")
                    utils.safe_set_action(obj.data.shape_keys, action)
                    obj_used.append(obj)
                    key_actions[obj_id] = action
                else:
                    utils.safe_set_action(obj.data.shape_keys, None)

    # apply to other compatible shape key objects
    if all_matching:
        utils.log_info(f"Applying other matching source key actions:")
        body_action = get_main_body_action(source_actions)
        for obj in objects:
            if filter and obj not in filter: continue
            if obj not in obj_used and utils.object_has_shape_keys(obj):
                obj_id = get_action_obj_id(obj)
                if body_action:
                    if obj_has_action_shape_keys(obj, body_action):
                        action = body_action
                        if copy and motion_id:
                            action_name = make_key_action_name(rig_id, motion_id, obj_id, motion_prefix)
                            utils.log_info(f" - Copying action: {action.name} to {action_name}")
                            action = utils.copy_action(action, action_name)
                            if set_id and set_generation:
                                add_motion_set_data(action, set_id, set_generation, obj_id=obj_id)
                        utils.log_info(f" - Applying action: {action.name} to {obj_id}")
                        utils.safe_set_action(obj.data.shape_keys, action)
                        obj_used.append(obj)
                        key_actions[obj_id] = action
    return key_actions


def obj_has_action_shape_keys(obj, action: bpy.types.Action):
    if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
        for key in obj.data.shape_keys.key_blocks:
            for fcurve in action.fcurves:
                if key.name in fcurve.data_path:
                    return True
    return False


def get_rig_id(rig):
    rig_id = utils.strip_name(rig.name.strip()).replace("|", "_")
    return rig_id


def decode_action_name(action):
    """Decode action name into prefix, rig_id, type("A"|"K"), object_id, motion_id.
       if the action name does not follow this naming pattern all values return None."""
    if type(action) is str:
        action_name = action
    else:
        action_name = action.name
    #utils.log_detail(f"Decoding Action name: {action_name}")
    try:
        ids = action_name.split("|")
        for i, id in enumerate(ids):
            ids[i] = id.strip()
        if ids[1] == "A":
            type_id = "A"
            prefix = ""
            rig_id = ids[0]
            obj_id = ""
        elif ids[2] == "A":
            type_id = "A"
            prefix = ids[0]
            rig_id = ids[1]
            obj_id = ""
        elif ids[1] == "K":
            type_id = "K"
            prefix = ""
            rig_id = ids[0]
            obj_id = ids[2]
        elif ids[2] == "K":
            type_id = "K"
            prefix = ids[0]
            rig_id = ids[1]
            obj_id = ids[3]
        motion_id = ids[-1]
        if type_id != "A" and type_id != "K":
            motion_id = None
            raise Exception("Invalid action type id!")
        #utils.log_detail(f"rig_id: {rig_id}, type_id: {type_id}, obj_id: {obj_id}, motion_id: {motion_id}, prefix: {prefix}")
    except Exception as e:
        prefix = None
        rig_id = None
        type_id = None
        obj_id = None
        motion_id = None
        #utils.log_detail("Invalid motion action name!")
    return prefix, rig_id, type_id, obj_id, motion_id


def get_action_motion_id(action, default_name="Motion"):
    if action:
        motion_id = action.name.split("|")[-1].strip()
    else:
        motion_id = ""
    if not motion_id and default_name:
        motion_id = f"{default_name}_{utils.generate_random_id(8)}"
    return motion_id


def get_motion_prefix(action, default_prefix=""):
    prefix, rig_id, type_id, obj_id, motion_id = decode_action_name(action)
    prefix = prefix.strip()
    if not prefix:
        return default_prefix
    else:
        return prefix


def get_action_obj_id(obj):
    obj_id = utils.strip_cc_base_name(obj.name).replace("|", "_")
    return obj_id


def get_formatted_prefix(motion_prefix):
    motion_prefix = motion_prefix.strip().replace("|", "_")
    while motion_prefix.endswith("_"):
        motion_prefix = motion_prefix[:-1]
    if motion_prefix and not motion_prefix.endswith("|"):
        motion_prefix += "|"
    return motion_prefix


def get_unique_set_motion_id(rig_id, motion_id, motion_prefix, exclude_set_id=None):
    test_name = make_armature_action_name(rig_id, motion_id, motion_prefix)
    base_name = test_name
    num_suffix = 0
    while test_name in bpy.data.actions:
        if exclude_set_id and "rl_set_id" in bpy.data.actions[test_name]:
            if exclude_set_id == bpy.data.actions[test_name]["rl_set_id"]:
                break
        num_suffix += 1
        test_name = f"{base_name}_{num_suffix:03d}"
    if num_suffix > 0:
        motion_id += f"_{num_suffix:03d}"
    return motion_id


def make_armature_action_name(rig_id, motion_id, motion_prefix):
    f_prefix = get_formatted_prefix(motion_prefix)
    return f"{f_prefix}{rig_id}|A|{motion_id}"


def make_key_action_name(rig_id, motion_id, obj_id, motion_prefix):
    f_prefix = get_formatted_prefix(motion_prefix)
    return f"{f_prefix}{rig_id}|K|{obj_id}|{motion_id}"


def set_armature_action_name(action, rig_id, motion_id, motion_prefix):
    action.name = make_armature_action_name(rig_id, motion_id, motion_prefix)


def set_key_action_name(action, rig_id, motion_id, obj_id, motion_prefix):
    action.name = make_key_action_name(rig_id, motion_id, obj_id, motion_prefix)


def generate_motion_set(rig, motion_id, motion_prefix):
    f_prefix = get_formatted_prefix(motion_prefix)
    rl_set_id = utils.generate_random_id(32)
    rl_set_generation, source_label = get_armature_action_source_type(rig)
    if "rl_set_generation" not in rig:
        rig["rl_set_generation"] = rl_set_generation
    return rl_set_id, rl_set_generation


def get_motion_set(action):
    set_id = None
    set_generation = None
    action_type_id = None
    key_object = None
    try:
        if "rl_set_id" in action:
            set_id = action["rl_set_id"]
        if "rl_set_generation" in action:
            set_generation = action["rl_set_generation"]
        if "rl_key_object" in action:
            key_object = action["rl_key_object"]
        if "rl_action_type" in action:
            action_type_id = action["rl_action_type"]
    except:
        set_id = None
        set_generation = None
        action_type_id = None
        key_object = None
    return set_id, set_generation, action_type_id, key_object


def add_motion_set_data(action, set_id, set_generation, obj_id=None, rl_arm_id=None):
    action["rl_set_id"] = set_id
    action["rl_set_generation"] = set_generation
    if obj_id is not None:
        action["rl_action_type"] = "KEY"
        action["rl_key_object"] = obj_id
    else:
        action["rl_action_type"] = "ARM"
    if rl_arm_id is not None:
        action["rl_armature_id"] = rl_arm_id


def load_motion_set(rig, set_armature_action):
    utils.log_info(f"Load Motion Set: {set_armature_action.name}")
    utils.log_indent()
    source_actions = find_source_actions(set_armature_action, None)
    apply_source_armature_action(rig, source_actions, copy=False)
    apply_source_key_actions(rig, source_actions, all_matching=True, copy=False)
    utils.log_recess()


def clear_motion_set(rig):
    mode_selection = utils.store_mode_selection_state()
    has_actions = utils.safe_get_action(rig)
    if not has_actions:
        reset_pose(rig)
    utils.safe_set_action(rig, None)
    objects = utils.get_child_objects(rig)
    for obj in objects:
        if obj.type == "MESH":
            if utils.object_has_shape_keys(obj):
                utils.safe_set_action(obj.data.shape_keys, None)
                if not has_actions:
                    reset_shape_keys(obj)
    utils.restore_mode_selection_state(mode_selection)


def clear_all_actions(objects):
    for obj in objects:
        if utils.object_exists_is_armature(obj):
            utils.safe_set_action(obj, None)
        elif utils.object_exists_is_mesh(obj):
            if utils.object_has_shape_keys(obj):
                utils.safe_set_action(obj.data.shape_keys, None)


def push_motion_set(rig: bpy.types.Object, set_armature_action, push_index = 0):
    source_actions = find_source_actions(set_armature_action, None)
    frame = bpy.context.scene.frame_current
    set_arm_action: bpy.types.Action = source_actions["armature"]
    length = int(set_arm_action.frame_range[1]) - int(set_arm_action.frame_range[0])
    objects = utils.get_child_objects(rig)
    # find all available NLA tracks
    nla_data = []
    if rig.animation_data.nla_tracks:
        nla_data.append(rig.animation_data.nla_tracks)
    for obj in objects:
        if obj.data.shape_keys and obj.data.shape_keys.animation_data:
            if obj.data.shape_keys.animation_data.nla_tracks:
                nla_data.append(obj.data.shape_keys.animation_data.nla_tracks)
    # count the mininum number of shared tracks across all action objects
    min_tracks = 0
    for nla_tracks in nla_data:
        l = len(nla_tracks)
        if l > 0:
            if min_tracks == 0:
                min_tracks = l
            min_tracks = min(min_tracks, l)
    # find the first available track that can fit the motion set
    available_tracks = [True] * min_tracks
    for nla_tracks in nla_data:
        for i in range(0, min_tracks):
            track: bpy.types.NlaTrack = nla_tracks[i]
            strip: bpy.types.NlaStrip
            for strip in track.strips:
                if frame >= strip.frame_start and frame < strip.frame_end:
                    available_tracks[i] = False
                elif (frame + length) >= strip.frame_start and (frame + length) < strip.frame_end:
                    available_tracks[i] = False
                elif strip.frame_start < frame and strip.frame_end >= frame + length:
                    available_tracks[i] = False
    track_index = -1
    for i, available in enumerate(available_tracks):
        if available:
            track_index = i
            break
    # push the actions
    action = source_actions["armature"]
    rig: bpy.types.Object
    if rig.animation_data is None:
        rig.animation_data_create()
    if not rig.animation_data.nla_tracks or track_index == -1:
        track = rig.animation_data.nla_tracks.new()
    else:
        track = rig.animation_data.nla_tracks[track_index]
    try:
        strip = track.strips.new(action.name, frame, action)
    except:
        track = rig.animation_data.nla_tracks.new()
        strip = track.strips.new(action.name, frame, action)
    strip.name = f"{action.name}|{push_index:03d}"
    for obj in objects:
        obj_id = get_action_obj_id(obj)
        if obj.type == "MESH" and obj_id in source_actions["keys"]:
            action = source_actions["keys"][obj_id]
            if obj.data.shape_keys:
                if not obj.data.shape_keys.animation_data:
                    obj.data.shape_keys.animation_data_create()
                if not obj.data.shape_keys.animation_data.nla_tracks or track_index == -1:
                    track = obj.data.shape_keys.animation_data.nla_tracks.new()
                else:
                    track = obj.data.shape_keys.animation_data.nla_tracks[track_index]
                try:
                    strip = track.strips.new(action.name, frame, action)
                except:
                    track = obj.data.shape_keys.animation_data.nla_tracks.new()
                    strip = track.strips.new(action.name, frame, action)
                strip.name = f"{action.name}|{push_index:03d}"


def get_nla_tracks(data):
    try:
        if data and data.animation_data and data.animation_data.nla_tracks:
            return data.animation_data.nla_tracks
    except:
        return None


def get_all_nla_strips(data, obj, strips=None):
    if strips is None:
        strips = {}
    tracks = get_nla_tracks(data)
    if tracks:
        for track in tracks:
            for strip in track.strips:
                strips[strip] = (obj, track)
    return strips


def get_strips_by_sets(set_ids: set):
    all_strips = {}
    for obj in bpy.data.objects:
        if utils.object_exists(obj):
            if obj.type == "ARMATURE":
                get_all_nla_strips(obj, obj, all_strips)
            elif obj.type == "MESH":
                get_all_nla_strips(obj.data.shape_keys, obj, all_strips)
    strip: bpy.types.NlaStrip
    strips = {}
    for strip in all_strips:
        strip_set_id = utils.custom_prop(strip.action, "rl_set_id")
        for sel_set_id, sel_auto_index in set_ids:
            if strip_set_id == sel_set_id:
                strip_auto_index = utils.get_auto_index_suffix(strip.name)
                if strip_auto_index == sel_auto_index:
                    obj, track = all_strips[strip]
                    strips[strip] = (obj, track)
    return strips


def unselect_all_but_strip(active_strip):
    all_strips = {}
    for obj in bpy.data.objects:
        if utils.object_exists(obj):
            if obj.type == "ARMATURE":
                get_all_nla_strips(obj, obj, all_strips)
            elif obj.type == "MESH":
                get_all_nla_strips(obj.data.shape_keys, obj, all_strips)
    for strip in all_strips:
        if strip != active_strip and strip.select:
            strip.select = False


def select_strips_by_set(active_strip: bpy.types.NlaStrip):
    strips = bpy.context.selected_nla_strips.copy()
    set_ids = set()
    for strip in strips:
        set_id = utils.custom_prop(strip.action, "rl_set_id")
        strip_auto_index = utils.get_auto_index_suffix(strip.name)
        if set_id and strip_auto_index:
            set_ids.add((set_id, strip_auto_index))
    if not active_strip and bpy.context.selected_nla_strips:
        active_strip = bpy.context.selected_nla_strips[0]
    if active_strip:
        unselect_all_but_strip(active_strip)
        strips = get_strips_by_sets(set_ids)
        for strip in strips:
            strip.select = True


def align_strips(strips, to_strip: bpy.types.NlaStrip=None, left=True):
    strip: bpy.types.NlaStrip
    left_frame = None if not to_strip else to_strip.frame_start
    right_frame = None if not to_strip else to_strip.frame_end
    # if no active strip, get the left most and right most frame in all strips
    if not to_strip:
        for strip in strips:
            if left_frame is None:
                left_frame = strip.frame_start
            if right_frame is None:
                right_frame = strip.frame_end
            left_frame = min(strip.frame_start, left_frame)
            right_frame = max(strip.frame_end, right_frame)
    # align strips
    # TODO sort strips in reverse order of direction
    for strip in strips:
        length = strip.frame_end - strip.frame_start
        if left:
            strip.frame_start = left_frame
            strip.frame_end = strip.frame_start + length
            strip.frame_start = strip.frame_end - length
        else:
            strip.frame_end = right_frame
            strip.frame_start = strip.frame_end - length
            strip.frame_end = strip.frame_start + length


def size_strips(strips, to_strip: bpy.types.NlaStrip=None, longest=True, reset=False):
    to_length = 0
    if to_strip:
        to_length = to_strip.frame_end - to_strip.frame_start
    min_length = None
    max_length = None
    strip: bpy.types.NlaStrip
    # find the shortest and longest strip lengths
    for strip in strips:
        length = strip.frame_end - strip.frame_start
        if min_length is None:
            min_length = length
        if max_length is None:
            max_length = length
        min_length = min(length, min_length)
        max_length = max(length, max_length)
    if not to_strip:
        to_length = max_length if longest else min_length
    for strip in strips:
        if reset:
            action_length = int(strip.action.frame_range[1] - strip.action.frame_range[0])
            strip.frame_end = strip.frame_start + action_length
            strip.frame_start = strip.frame_end - action_length
        elif to_length > 0:
            strip.frame_end = strip.frame_start + to_length
            strip.frame_start = strip.frame_end - to_length


def set_action_set_fake_user(action, use_fake_user):
    set_id = utils.custom_prop(action, "rl_set_id")
    if set_id:
        for action in bpy.data.actions:
            action_set_id = utils.custom_prop(action, "rl_set_id")
            if action_set_id == set_id:
                action.use_fake_user = use_fake_user
    utils.update_ui(all=True)


def delete_motion_set(action):
    set_id = utils.custom_prop(action, "rl_set_id")
    if set_id:
        to_remove = []
        for action in bpy.data.actions:
            action_set_id = utils.custom_prop(action, "rl_set_id")
            if action_set_id == set_id:
                to_remove.append(action)
    for action in to_remove:
        bpy.data.actions.remove(action)
    utils.update_ui(all=True)


def rename_armature(arm, name):
    armature_object = None
    armature_data = None
    try:
        armature_object = bpy.data.objects[name]
    except:
        pass
    try:
        armature_data = bpy.data.armatures[name]
    except:
        pass
    utils.force_object_name(arm, name)
    utils.force_armature_name(arm.data, name)
    return armature_object, armature_data


def restore_armature_names(armature_object, armature_data, name):
    if armature_object:
        utils.force_object_name(armature_object, name)
    if armature_data:
        utils.force_armature_name(armature_data, name)


def get_rigify_ik_fk_influence(rig):
    ik_fk = 0
    num_bones = 0
    ik_fk_control_bones = ["upper_arm_parent.L", "upper_arm_parent.R", "thigh_parent.L", "thigh_parent.R"]
    for bone_name in ik_fk_control_bones:
        if bone_name in rig.pose.bones:
            num_bones += 1
            pose_bone = rig.pose.bones[bone_name]
            ik_fk += pose_bone["IK_FK"]
    if num_bones > 0:
        ik_fk /= num_bones
    return ik_fk


def set_rigify_ik_fk_influence(rig, influence):
    ik_fk_control_bones = ["upper_arm_parent.L", "upper_arm_parent.R", "thigh_parent.L", "thigh_parent.R"]
    for bone_name in ik_fk_control_bones:
        if bone_name in rig.pose.bones:
            pose_bone = rig.pose.bones[bone_name]
            pose_bone["IK_FK"] = influence


def poke_rig(rig):
    """Switches modes on the armature and sets the root pose bone location to force updates
       after changing custom paramters i.e. IK_FK on the limbs."""
    state = utils.store_mode_selection_state()
    select_rig(rig)
    pose_bone: bpy.types.PoseBone = rig.pose.bones[0]
    loc = pose_bone.location
    pose_bone.location = loc
    pose_rig(rig)
    utils.restore_mode_selection_state(state)


def set_bone_tail_length(bone: bpy.types.EditBone, tail):
    """Set the length based on a new tail position, but don't set the tail directly
       as it may cause changes in the bone roll and angles."""
    if bone and tail:
        if type(tail) is bpy.types.EditBone:
            new_tail = tail.head.copy()
        elif type(tail) is Vector:
            new_tail = tail.copy()
        length = (new_tail - bone.head).length
        bone.length = length


def set_bone_deform(bone: bpy.types.EditBone, use_deform):
    try:
        if bone:
            bone.use_deform = use_deform
    except: ...


def fix_cc3_standard_rig(cc3_rig):
    if edit_rig(cc3_rig):
        left_eye = bones.get_edit_bone(cc3_rig, "CC_Base_L_Eye")
        right_eye = bones.get_edit_bone(cc3_rig, "CC_Base_R_Eye")
        left_hand = bones.get_edit_bone(cc3_rig, ["CC_Base_L_Hand", "hand_l"])
        right_hand = bones.get_edit_bone(cc3_rig, ["CC_Base_R_Hand", "hand_r"])
        left_foot = bones.get_edit_bone(cc3_rig, ["CC_Base_L_Foot", "foot_l"])
        right_foot = bones.get_edit_bone(cc3_rig, ["CC_Base_R_Foot", "foot_r"])
        head = bones.get_edit_bone(cc3_rig, ["CC_Base_Head", "head"])
        left_upper_arm = bones.get_edit_bone(cc3_rig, ["CC_Base_L_Upperarm", "upperarm_l"])
        right_upper_arm = bones.get_edit_bone(cc3_rig, ["CC_Base_R_Upperarm", "upperarm_r"])
        left_lower_arm = bones.get_edit_bone(cc3_rig, ["CC_Base_L_Forearm", "lowerarm_l"])
        right_lower_arm = bones.get_edit_bone(cc3_rig, ["CC_Base_R_Forearm", "lowerarm_r"])
        left_thigh = bones.get_edit_bone(cc3_rig, ["CC_Base_L_Thigh", "thigh_l"])
        right_thigh = bones.get_edit_bone(cc3_rig, ["CC_Base_R_Thigh", "thigh_r"])
        left_calf = bones.get_edit_bone(cc3_rig, ["CC_Base_L_Calf", "calf_l"])
        right_calf = bones.get_edit_bone(cc3_rig, ["CC_Base_R_Calf", "calf_r"])
        hip = bones.get_edit_bone(cc3_rig, ["CC_Base_Hip", "hip"])
        root = bones.get_edit_bone(cc3_rig, ["CC_Base_BoneRoot", "RL_BoneRoot", "root"])
        # fix deform state
        set_bone_deform(left_thigh, False)
        set_bone_deform(right_thigh, False)
        set_bone_deform(left_calf, False)
        set_bone_deform(right_calf, False)
        set_bone_deform(left_upper_arm, False)
        set_bone_deform(right_upper_arm, False)
        set_bone_deform(left_lower_arm, False)
        set_bone_deform(right_lower_arm, False)
        set_bone_deform(hip, False)
        set_bone_deform(root, False)
        # eyes
        eye_z = None
        if left_eye and right_eye:
            eye_z = ((left_eye.head + right_eye.head) * 0.5).z
            # head
            if head:
                head_tail = head.tail.copy()
                head_tail.z = eye_z + (eye_z - head.head.z) * 0.5
                set_bone_tail_length(head, head_tail)
        # arms
        set_bone_tail_length(left_upper_arm, left_lower_arm)
        set_bone_tail_length(right_upper_arm, right_lower_arm)
        set_bone_tail_length(left_lower_arm, left_hand)
        set_bone_tail_length(right_lower_arm, right_hand)
        # legs
        set_bone_tail_length(left_thigh, left_calf)
        set_bone_tail_length(right_thigh, right_calf)
        set_bone_tail_length(left_calf, left_foot)
        set_bone_tail_length(right_calf, right_foot)
        select_rig(cc3_rig)


def reset_rotation_modes(rig, rotation_mode = "QUATERNION"):
    pose_bone: bpy.types.PoseBone
    for pose_bone in rig.pose.bones:
        pose_bone.rotation_mode = rotation_mode


def is_skinned_rig(rig):
    meshes = utils.get_child_objects(rig)
    for mesh in meshes:
        mod = None
        for m in mesh.modifiers:
            if m and m.type == "ARMATURE":
                mod = m
        if mod:
            return True
    return False


BASE_RIG_COLLECTION = ["Face", "Face (Primary)", "Face (Secondary)",
                       "Torso", "Torso (Tweak)", "Fingers", "Fingers (Detail)",
                       "Arm.L (IK)", "Arm.L (FK)", "Arm.L (Tweak)", "Leg.L (IK)", "Leg.L (FK)", "Leg.L (Tweak)",
                       "Arm.R (IK)", "Arm.R (FK)", "Arm.R (Tweak)", "Leg.R (IK)", "Leg.R (FK)", "Leg.R (Tweak)",
                       "Root" ]
BASE_RIG_LAYERS = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,28]
BASE_DEF_COLLECTION = ["DEF"]
BASE_DEF_LAYERS = [29]

FULL_RIG_COLLECTION = ["Face", "Face (Primary)", "Face (Secondary)",
                       "Torso", "Torso (Tweak)", "Fingers", "Fingers (Detail)",
                       "Arm.L (IK)", "Arm.L (FK)", "Arm.L (Tweak)", "Leg.L (IK)", "Leg.L (FK)", "Leg.L (Tweak)",
                       "Arm.R (IK)", "Arm.R (FK)", "Arm.R (Tweak)", "Leg.R (IK)", "Leg.R (FK)", "Leg.R (Tweak)",
                       "Root",
                       "Spring (IK)", "Spring (FK)", "Spring (Tweak)"]
FULL_RIG_LAYERS = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,28]
FULL_DEF_COLLECTION = ["DEF", "Spring (Edit)", "Spring (Root)"]
FULL_DEF_LAYERS = [24, 25, 29]

SPRING_RIG_COLLECTION = ["Spring (IK)", "Spring (FK)", "Spring (Tweak)"]
SPRING_RIG_LAYERS = [19,20,21]
SPRING_DEF_COLLECTION = ["Spring (Edit)", "Spring (Root)"]
SPRING_DEF_LAYERS = [24, 25]


def show_hide_collections_layers(rig, collections, layers, show=True):
    if rig:
        if utils.B400():
            for collection in rig.data.collections:
                if collection.name in collections:
                    collection.is_visible = show
        else:
            for i in range(0, 32):
                if i in layers:
                    rig.data.layers[i] = show


def is_full_rigify_rig_shown(rig):
    if rig:
        if utils.B400():
            for collection in rig.data.collections:
                if collection.name in FULL_RIG_COLLECTION and not collection.is_visible:
                    return False
        else:
            for i in range(0, 32):
                if i in FULL_RIG_LAYERS and rig.data.layers[i] == False:
                    return False
        return True
    else:
        return False


def toggle_show_full_rig(rig):
    if rig:
        show = not is_full_rigify_rig_shown(rig)
        if utils.B400():
            if show:
                for collection in rig.data.collections:
                    collection.is_visible = collection.name in FULL_RIG_COLLECTION
            else:
                for collection in rig.data.collections:
                    collection.is_visible = collection.name in FULL_DEF_COLLECTION
        else:
            if show:
                rig.data.layers[vars.ROOT_BONE_LAYER] = True
            else:
                rig.data.layers[vars.DEF_BONE_LAYER] = True
            for i in range(0, 32):
                if show:
                    rig.data.layers[i] = i in FULL_RIG_LAYERS
                else:
                    rig.data.layers[i] = i in FULL_DEF_LAYERS


def is_base_rig_shown(rig):
    if rig:
        if utils.B400():
            for collection in rig.data.collections:
                if collection.name in BASE_RIG_COLLECTION and not collection.is_visible:
                    return False
        else:
            for i in range(0, 32):
                if i in BASE_RIG_LAYERS and rig.data.layers[i] == False:
                    return False
        return True
    else:
        return False


def toggle_show_base_rig(rig):
    if rig:
        show = True
        if is_full_rigify_rig_shown(rig):
            show = True
        elif is_base_rig_shown(rig):
            show = False
        if utils.B400():
            if show:
                for collection in rig.data.collections:
                    collection.is_visible = collection.name in BASE_RIG_COLLECTION
            else:
                for collection in rig.data.collections:
                    collection.is_visible = collection.name in BASE_DEF_COLLECTION
        else:
            if show:
                rig.data.layers[vars.ROOT_BONE_LAYER] = True
            else:
                rig.data.layers[vars.DEF_BONE_LAYER] = True
            for i in range(0, 32):
                if show:
                    rig.data.layers[i] = i in BASE_RIG_LAYERS
                else:
                    rig.data.layers[i] = i in BASE_DEF_LAYERS


def is_spring_rig_shown(rig):
    if rig:
        if utils.B400():
            for collection in rig.data.collections:
                if collection.name in SPRING_RIG_COLLECTION and not collection.is_visible:
                    return False
        else:
            for i in range(0, 32):
                if i in SPRING_RIG_LAYERS and rig.data.layers[i] == False:
                    return False
        return True
    else:
        return False


def toggle_show_spring_rig(rig):
    if rig:
        show = True
        if is_full_rigify_rig_shown(rig):
            show = True
        elif is_spring_rig_shown(rig):
            show = False
        if utils.B400():
            if show:
                for collection in rig.data.collections:
                    collection.is_visible = collection.name in SPRING_RIG_COLLECTION
            else:
                for collection in rig.data.collections:
                    collection.is_visible = collection.name in SPRING_DEF_COLLECTION
        else:
            if show:
                rig.data.layers[vars.SPRING_IK_LAYER] = True
            else:
                rig.data.layers[vars.DEF_BONE_LAYER] = True

            for i in range(0, 32):
                if show:
                    rig.data.layers[i] = i in SPRING_RIG_LAYERS
                else:
                    rig.data.layers[i] = i in SPRING_DEF_LAYERS


def reset_pose(rig):
    if rig:
        utils.pose_mode_to(rig)
        rig.data.pose_position = "POSE"
        bones_data = {}
        for bone in rig.data.bones:
            bones_data[bone] = (bone.select, bone.hide, bone.hide_select)
            bone.select = True
            bone.hide = False
            bone.hide_select = False
        bpy.ops.pose.transforms_clear()
        for bone in rig.data.bones:
            bone.select, bone.hide, bone.hide_select = bones_data[bone]


def reset_shape_keys(mesh):
    if mesh and utils.object_has_shape_keys(mesh):
        key: bpy.types.ShapeKey
        for key in mesh.data.shape_keys.key_blocks:
            key.value = 0.0


def is_rig_rest_position(rig):
    if rig:
        if rig.data.pose_position == "REST":
            return True
    return False


def toggle_rig_rest_position(rig):
    if rig:
        if rig.data.pose_position == "POSE":
            rig.data.pose_position = "REST"
        else:
            rig.data.pose_position = "POSE"


def get_local_pose_bone_transform(M: Matrix, pose_bone: bpy.types.PoseBone):
    """M: Matrix - object space matrix of the transform to convert
       pose_bone: bpy.types.PoseBone - pose bone to calculate local space transform for."""
    L: Matrix   # local space matrix we want
    NL: Matrix  # non-local space matrix we want (if not using local location or inherit rotation)
    R: Matrix = pose_bone.bone.matrix_local # bone rest pose matrix
    RI: Matrix = R.inverted() # bone rest pose matrix inverted
    if pose_bone.parent:
        PI: Matrix = pose_bone.parent.matrix.inverted() # parent object space matrix inverted (after contraints and drivers)
        PR: Matrix = pose_bone.parent.bone.matrix_local # parent rest pose matrix
        L = RI @ (PR @ (PI @ M))
        NL = PI @ M
    else:
        L = RI @ M
        NL = M
    if not pose_bone.bone.use_local_location:
        loc = NL.to_translation()
    else:
        loc = L.to_translation()
    sca = L.to_scale()
    if not pose_bone.bone.use_inherit_rotation:
        rot = NL.to_quaternion()
    else:
        rot = L.to_quaternion()
    return loc, rot, sca, L, NL


def apply_as_rest_pose(rig):
    if rig and select_rig(rig):
        objects = utils.get_child_objects(rig)
        for obj in objects:
            if utils.object_exists(obj):
                vis = obj.visible_get()
                if not vis:
                    utils.unhide(obj)
                mod: bpy.types.ArmatureModifier = modifiers.get_object_modifier(obj, "ARMATURE")
                if mod:
                    # apply armature modifier with preserve settings and mod order
                    modifiers.apply_modifier(obj, modifier=mod, preserving=True)
                    modifiers.get_armature_modifier(obj, create=True, armature=rig)
                utils.hide(obj, not vis)
    if pose_rig(rig):
        bpy.ops.pose.armature_apply(selected=False)
    utils.object_mode_to(rig)


def constrain_pose_rigs(src_rig, dst_rig):
    # constrain the destination rig rest pose to the source rig pose
    constraints = {}
    if select_rig(src_rig):
        src_bone: bpy.types.PoseBone
        dst_bone: bpy.types.PoseBone
        for src_bone in src_rig.pose.bones:
            if src_bone.name in dst_rig.pose.bones:
                dst_bone = dst_rig.pose.bones[src_bone.name]
                con = bones.add_copy_transforms_constraint(src_rig, dst_rig, src_bone.name, dst_bone.name)
                constraints[dst_bone] = con
    return constraints


def unconstrain_pose_rigs(constraints):
    # remove the constraints
    for dst_bone in constraints:
        con = constraints[dst_bone]
        dst_bone.constraints.remove(con)


def retarget_rig_actions(from_rig, to_rig):
    rig_action = utils.safe_get_action(from_rig)
    source_actions = find_source_actions(rig_action, from_rig)
    apply_source_armature_action(to_rig, source_actions)
    apply_source_key_actions(to_rig, source_actions, all_matching=True)


def cmp_matrix(A: Matrix, B: Matrix):
    rows = len(A.row)
    cols = len(A.col)
    delta = 0
    for i in range(0, rows):
        for j in range(0, cols):
            delta += abs(A[i][j] - B[i][j])
    if delta < 0.001:
        return True
    return False


def is_rest_pose_same(src_rig, dst_rig):
    if len(src_rig.data.bones) != len(dst_rig.data.bones):
        return False
    src_bone: bpy.types.Bone
    dst_bone: bpy.types.Bone
    for src_bone in src_rig.data.bones:
        if src_bone.name not in dst_rig.data.bones:
            return False
        dst_bone = dst_rig.data.bones[src_bone.name]
        if not cmp_matrix(src_bone.matrix, dst_bone.matrix):
            return False
    return True


def copy_rest_pose(src_rig, dst_rig):
    # TODO make everything visible...
    temp_collection = utils.force_visible_in_scene("TMP_COPY_POSE", src_rig, dst_rig)
    TS = utils.store_object_transform(src_rig)
    TD = utils.store_object_transform(dst_rig)
    utils.reset_object_transform(src_rig)
    utils.reset_object_transform(dst_rig)
    src_action = utils.safe_get_action(src_rig)
    dst_action = utils.safe_get_action(dst_rig)
    utils.safe_set_action(src_rig, None)
    utils.safe_set_action(dst_rig, None)

    utils.try_select_objects([src_rig, dst_rig], clear_selection=True)
    bones.clear_pose(src_rig)
    bones.clear_pose(dst_rig)

    # constrain the destination rig rest pose to the source rig pose
    constraints = constrain_pose_rigs(src_rig, dst_rig)

    # apply the destination pose as rest pose
    apply_as_rest_pose(dst_rig)

    # remove the constraints
    unconstrain_pose_rigs(constraints)

    utils.restore_object_transform(src_rig, TS)
    utils.restore_object_transform(dst_rig, TD)
    utils.safe_set_action(src_rig, src_action)
    utils.safe_set_action(dst_rig, dst_action)

    utils.restore_visible_in_scene(temp_collection)


def bake_rig_action(src_rig, dst_rig):
    src_action: bpy.types.Action = utils.safe_get_action(src_rig)
    dst_action: bpy.types.Action = utils.safe_get_action(dst_rig)
    baked_action = None

    if utils.try_select_object(dst_rig, True) and utils.set_active_object(dst_rig):
        utils.log_info(f"Baking action: {src_action.name} to {dst_rig.name}")
        # frame range
        if src_action:
            start_frame = int(src_action.frame_range[0])
            end_frame = int(src_action.frame_range[1])
        else:
            start_frame = int(bpy.context.scene.frame_start)
            end_frame = int(bpy.context.scene.frame_end)

        # limit view layer to dst rig (bakes faster)
        tmp_collection, layer_collections, to_hide = utils.limit_view_layer_to_collection("TMP_BAKE", dst_rig)

        utils.set_active_object(dst_rig)
        utils.set_mode("POSE")

        # bake
        bpy.ops.nla.bake(frame_start=start_frame,
                         frame_end=end_frame,
                         only_selected=True,
                         visual_keying=True,
                         use_current_action=True,
                         clear_constraints=False,
                         clean_curves=False,
                         bake_types={'POSE'})

        # armature action
        baked_action = utils.safe_get_action(dst_rig)

        utils.object_mode()

        # restore view layers
        utils.restore_limited_view_layers(tmp_collection, layer_collections, to_hide)

    # return the baked action
    return baked_action


def bake_rig_action_from_source(src_rig, dst_rig):
    temp_collection = utils.force_visible_in_scene("TMP_Bake_Retarget", src_rig, dst_rig)
    rig_settings = bones.store_armature_settings(dst_rig)
    # constrain the destination rig rest pose to the source rig pose
    constraints = constrain_pose_rigs(src_rig, dst_rig)
    baked_action = None
    if select_rig(dst_rig):
        bones.make_bones_visible(dst_rig)
        bone : bpy.types.Bone
        for bone in dst_rig.data.bones:
            bone.select = True
        baked_action = bake_rig_action(src_rig, dst_rig)
    # remove contraints
    unconstrain_pose_rigs(constraints)
    bones.restore_armature_settings(dst_rig, rig_settings)
    utils.safe_set_action(dst_rig, baked_action)
    utils.restore_visible_in_scene(temp_collection)
    return baked_action


DISABLE_TWEAK_STRETCH_IN = [
    "DEF-thigh.R",
    "DEF-thigh.R.001",
    "DEF-shin.R",
    "DEF-shin.R.001",
    "DEF-foot.R",
    "DEF-thigh.L",
    "DEF-thigh.L.001",
    "DEF-shin.L",
    "DEF-shin.L.001",
    "DEF-foot.L",
]

DISABLE_TWEAK_STRETCH_FOR = [
    "thigh_tweak.R",
    "thigh_tweak.R.001",
    "shin_tweak.R",
    "shin_tweak.R.001",
    "foot_tweak.R",
    "thigh_tweak.L",
    "thigh_tweak.L.001",
    "shin_tweak.L",
    "shin_tweak.L.001",
    "foot_tweak.L",
]


def disable_ik_stretch(rigify_rig, bone_names=None):
    con_store = {}
    for pose_bone in rigify_rig.pose.bones:
        if bone_names and pose_bone.name not in bone_names:
            continue
        for con in pose_bone.constraints:
            if con and con.type == "IK":
                con_store[con] = con.use_stretch
                con.use_stretch = False
    return con_store


def restore_ik_stretch(con_store):
    for con in con_store:
        con.use_stretch = con_store[con]


def update_avatar_rig(rig):
    prefs = vars.prefs()

    utils.log_info("Updating avatar rig...")

    if is_rigify_armature(rig):
        # disable all stretch-to tweak constraints and hide tweak bones...
        # tweak bones are not fully compatible with CC/iC animation (probably Blender only)
        # and cause positioning errors as they stretch/compress the bones.
        # NOTE: Seems to have been because of a bug in Blender 4.1, fixed in 4.2 so disabling this...
        if False:
            if prefs.datalink_disable_tweak_bones:
                disable = True
                influence = 0.0
            else:
                disable = False
                influence = 1.0
            pose_bone: bpy.types.PoseBone
            for pose_bone in rig.pose.bones:
                if pose_bone.name in DISABLE_TWEAK_STRETCH_FOR:
                    if disable:
                        bones.set_bone_color(pose_bone, "TWEAK_DISABLED")
                    else:
                        bones.set_bone_color(pose_bone, "TWEAK")
                elif prefs.datalink_disable_tweak_bones and pose_bone.name in DISABLE_TWEAK_STRETCH_IN:
                    for con in pose_bone.constraints:
                        if con.type == "STRETCH_TO":
                            if "tweak" in con.subtarget:
                                con.influence = influence
                # disable IK stretch
                if "IK_Stretch" in pose_bone:
                    pose_bone["IK_Stretch"] = 0.0
        else: # just disable IK Stretch...
            pose_bone: bpy.types.PoseBone
            for pose_bone in rig.pose.bones:
                # disable IK stretch
                if "IK_Stretch" in pose_bone:
                    pose_bone["IK_Stretch"] = 0.0


def update_prop_rig(rig):
    prefs = vars.prefs()

    if not rig: return

    utils.log_info("Updating prop rig...")

    skin_bones = set()
    rigid_bones = set()
    mesh_bones = set()
    root_bones = set()
    skinned_root_bones = set()

    root_bones.add(rig.data.bones[0])
    USE_JSON_BONE_DATA = True

    meshes = utils.get_child_objects(rig)
    for obj in meshes:
        if (obj.parent_type == "BONE" and obj.parent_bone in rig.data.bones):
            bone = rig.data.bones[obj.parent_bone]
            if (bone.parent and bone.parent.parent and
                "CC_Base_Pivot" in bone.parent.name):
                mesh_bones.add(bone.name)
                rigid_bones.add(bone.parent.parent.name)
            elif (bone.parent and
                "CC_Base_Pivot" in bone.name):
                rigid_bones.add(bone.parent.name)
            elif bone.parent:
                rigid_bones.add(bone.parent.name)
            else:
                rigid_bones.add(bone.name)

        elif (obj.parent_type == "OBJECT" and obj.vertex_groups and len(obj.vertex_groups) == 1 and
              utils.strip_name(obj.vertex_groups[0].name) == bones.rl_export_bone_name(utils.strip_name(obj.name))):
            bone = rig.data.bones[obj.vertex_groups[0].name]
            if (bone.parent and bone.parent.parent and
                "CC_Base_Pivot" in bone.parent.name):
                mesh_bones.add(bone.name)
                rigid_bones.add(bone.parent.parent.name)
            elif (bone.parent and
                "CC_Base_Pivot" in bone.name):
                rigid_bones.add(bone.parent.name)
            elif bone.parent:
                rigid_bones.add(bone.parent.name)
            else:
                rigid_bones.add(bone.name)

        elif (obj.parent_type == "OBJECT" and obj.vertex_groups and len(obj.vertex_groups) > 0):
            for vg in obj.vertex_groups:
                skin_bones.add(vg.name)
            if USE_JSON_BONE_DATA:
                first_name = obj.vertex_groups[0].name
                if first_name in rig.pose.bones:
                    pose_bone = rig.pose.bones[first_name]
                    while pose_bone.parent:
                        if "root_id" and "root_type" in pose_bone:
                            skinned_root_bones.add(pose_bone.name)
                            break
                        pose_bone = pose_bone.parent

    if USE_JSON_BONE_DATA:
        for pose_bone in rig.pose.bones:
            if "root_id" in pose_bone and "root_type" in pose_bone:
                root_bones.add(pose_bone.name)

    pose_bone: bpy.types.PoseBone
    for pose_bone in rig.pose.bones:
        bone = pose_bone.bone
        pivot_bone = "CC_Base_Pivot" in pose_bone.name
        skin_bone = bone.name in skin_bones
        rigid_bone = bone.name in rigid_bones
        mesh_bone = bone.name in mesh_bones
        root_bone = bone.name in root_bones
        dummy_bone = not (skin_bone or rigid_bone or mesh_bone) and len(bone.children) == 0
        node_bone = not (skin_bone or rigid_bone or mesh_bone) and len(bone.children) > 0
        if root_bone:
            bone.hide = False
        elif pivot_bone:
            bone.hide = True
        elif skin_bone:
            bone.hide = prefs.datalink_hide_prop_bones
        elif mesh_bone:
            bone.hide = True
        elif rigid_bone:
            bone.hide = False
        elif dummy_bone:
            bone.hide = True
        elif node_bone:
            bone.hide = prefs.datalink_hide_prop_bones

"""
import bpy

b = bpy.context.active_bone
c = b.children[0]
print(f"{b.head_local} {c.head_local} {b.length}")
hi = b.matrix_local.inverted() @ b.head_local
ti = b.matrix_local.inverted() @ b.tail_local
db = (ti - hi)/b.length
print(db)


ci = b.matrix_local.inverted() @ c.head_local
dc = (ci - hi)/b.length
print(dc)
print(db.dot(dc))
print(abs(db.length - dc.length))
q = db.rotation_difference(dc)
print(q)
print(q.to_euler())
"""

def get_bone_orientation(rig, bone_set: set):
    B: bpy.types.Bone
    C: bpy.types.Bone
    for bone_name in bone_set:
        B = rig.data.bones[bone_name]
        if B.children and B.parent:
            for C in B.children:
                if B.length > 0.01:
                    # convert heads and tail to B local space
                    bhl = B.matrix_local.inverted() @ B.head_local
                    btl = B.matrix_local.inverted() @ B.tail_local
                    chl = B.matrix_local.inverted() @ C.head_local
                    # get bone axis in B local space
                    db: Vector = (btl - bhl) / B.length
                    # get direction to child in B local space
                    dc: Vector = (chl - bhl) / B.length
                    # if the distance to the child is ~= the same as the bone length
                    # (this should mean a chain of bones)
                    if abs(db.length - dc.length) < 0.01:
                        # get the rotation difference between the bone axis and the direction to the child
                        q = db.rotation_difference(dc)
                        euler = q.to_euler()
                        return euler
    return Euler((0,0,0), "XYZ")


def get_custom_widgets():
    wgt_pivot = bones.make_axes_widget("WGT-datalink_pivot", 1)
    wgt_mesh = bones.make_cone_widget("WGT-datalink_mesh", 1)
    wgt_default = bones.make_sphere_widget("WGT-datalink_default", 1)
    wgt_root = bones.make_root_widget("WGT-datalink_root", 2.5)
    wgt_skin = bones.make_spike_widget("WGT-datalink_skin", 1)
    bones.add_widget_to_collection(wgt_pivot, "WGTS_Datalink")
    bones.add_widget_to_collection(wgt_mesh, "WGTS_Datalink")
    bones.add_widget_to_collection(wgt_default, "WGTS_Datalink")
    bones.add_widget_to_collection(wgt_root, "WGTS_Datalink")
    bones.add_widget_to_collection(wgt_skin, "WGTS_Datalink")
    widgets = {
        "pivot": wgt_pivot,
        "mesh": wgt_mesh,
        "default": wgt_default,
        "root": wgt_root,
        "skin": wgt_skin,
    }
    return widgets


def set_bone_shape_scale(pose_bone: bpy.types.PoseBone, scale):
    try:
        if type(scale) is float or type(scale) is int:
            S = Vector((scale, scale, scale))
        elif type(scale) is list or type(scale) is tuple:
            S = Vector(scale)
        elif type(scale) is Vector:
            S = scale
        else:
            return False
        pose_bone.custom_shape_scale_xyz = S
        return True
    except:
        pass
    try:
        pose_bone.custom_shape_scale = scale
        return True
    except:
        pass
    utils.log_error(f"Unable to set bone shape scale: {pose_bone.name} / {scale}")
    return False


def custom_prop_rig(rig):
    prefs = vars.prefs()

    if not rig: return

    utils.log_info("Applying custom prop rig...")

    widgets = get_custom_widgets()
    rig.show_in_front = True #not is_skinned_rig(rig)
    rig.data.display_type = 'WIRE'

    skin_bones = set()
    rigid_bones = set()
    mesh_bones = set()
    root_bones = set()
    skinned_root_bones = set()

    root_bones.add(rig.data.bones[0].name)
    USE_JSON_BONE_DATA = True

    meshes = utils.get_child_objects(rig)
    for obj in meshes:
        if (obj.parent_type == "BONE" and obj.parent_bone in rig.data.bones):
            bone = rig.data.bones[obj.parent_bone]
            if (bone.parent and bone.parent.parent and
                "CC_Base_Pivot" in bone.parent.name):
                mesh_bones.add(bone.name)
                rigid_bones.add(bone.parent.parent.name)
            elif (bone.parent and
                "CC_Base_Pivot" in bone.name):
                rigid_bones.add(bone.parent.name)
            elif bone.parent:
                rigid_bones.add(bone.parent.name)
            else:
                rigid_bones.add(bone.name)

        elif (obj.parent_type == "OBJECT" and obj.vertex_groups and len(obj.vertex_groups) == 1 and
              utils.strip_name(obj.vertex_groups[0].name) == bones.rl_export_bone_name(utils.strip_name(obj.name))):
            bone = rig.data.bones[obj.vertex_groups[0].name]
            if (bone.parent and bone.parent.parent and
                "CC_Base_Pivot" in bone.parent.name):
                mesh_bones.add(bone.name)
                rigid_bones.add(bone.parent.parent.name)
            elif (bone.parent and
                "CC_Base_Pivot" in bone.name):
                rigid_bones.add(bone.parent.name)
            elif bone.parent:
                rigid_bones.add(bone.parent.name)
            else:
                rigid_bones.add(bone.name)

        elif (obj.parent_type == "OBJECT" and obj.vertex_groups and len(obj.vertex_groups) > 0):
            for vg in obj.vertex_groups:
                skin_bones.add(vg.name)
            if USE_JSON_BONE_DATA:
                first_name = obj.vertex_groups[0].name
                if first_name in rig.pose.bones:
                    pose_bone = rig.pose.bones[first_name]
                    while pose_bone.parent:
                        if "root_id" and "root_type" in pose_bone:
                            skinned_root_bones.add(pose_bone.name)
                            break
                        pose_bone = pose_bone.parent

    skin_bone_orientation = get_bone_orientation(rig, skin_bones)

    if USE_JSON_BONE_DATA:
        for pose_bone in rig.pose.bones:
            if "root_id" in pose_bone and "root_type" in pose_bone:
                root_bones.add(pose_bone.name)

    if select_rig(rig):
        pose_bone: bpy.types.PoseBone
        for pose_bone in rig.pose.bones:
            bone = pose_bone.bone
            pivot_bone = "CC_Base_Pivot" in pose_bone.name
            skin_bone = bone.name in skin_bones
            rigid_bone = bone.name in rigid_bones
            mesh_bone = bone.name in mesh_bones
            root_bone = bone.name in root_bones
            dummy_bone = not (skin_bone or rigid_bone or mesh_bone) and len(bone.children) == 0
            node_bone = not (skin_bone or rigid_bone or mesh_bone) and len(bone.children) > 0
            if root_bone:
                if not pose_bone.parent:
                    pose_bone.custom_shape = widgets["root"]
                    set_bone_shape_scale(pose_bone, 20)
                else:
                    pose_bone.custom_shape = widgets["default"]
                    set_bone_shape_scale(pose_bone, 15)
                bone.hide = False
                pose_bone.use_custom_shape_bone_size = False
                bones.set_bone_color(pose_bone, "ROOT")
            elif pivot_bone:
                pose_bone.custom_shape = widgets["pivot"]
                bone.hide = True
                pose_bone.use_custom_shape_bone_size = False
                set_bone_shape_scale(pose_bone, 10)
                bones.set_bone_color(pose_bone, "SPECIAL")
            elif skin_bone:
                pose_bone.custom_shape = widgets["skin"]
                bone.hide = prefs.datalink_hide_prop_bones
                pose_bone.use_custom_shape_bone_size = True
                pose_bone.use
                #pose_bone.bone.show_wire = True
                pose_bone.custom_shape_rotation_euler = skin_bone_orientation
                bones.set_bone_color(pose_bone, "SKIN")
            elif mesh_bone:
                pose_bone.custom_shape = widgets["mesh"]
                bone.hide = True
                pose_bone.use_custom_shape_bone_size = False
                set_bone_shape_scale(pose_bone, 10)
                bones.set_bone_color(pose_bone, "SPECIAL")
            elif rigid_bone:
                pose_bone.custom_shape = widgets["default"]
                bone.hide = False
                pose_bone.use_custom_shape_bone_size = False
                set_bone_shape_scale(pose_bone, 10)
                bones.set_bone_color(pose_bone, "TWEAK")
            elif dummy_bone:
                pose_bone.custom_shape = widgets["pivot"]
                bone.hide = True
                pose_bone.use_custom_shape_bone_size = False
                set_bone_shape_scale(pose_bone, 10)
                bones.set_bone_color(pose_bone, "IK")
            elif node_bone:
                pose_bone.custom_shape = widgets["default"]
                bone.hide = prefs.datalink_hide_prop_bones
                pose_bone.use_custom_shape_bone_size = False
                set_bone_shape_scale(pose_bone, 10)
                bones.set_bone_color(pose_bone, "SPECIAL")


def custom_avatar_rig(rig):
    prefs = vars.prefs()

    if not rig: return

    utils.log_info("Applying custom avatar rig...")

    widgets = get_custom_widgets()
    rig.show_in_front = False
    rig.data.display_type = 'OCTAHEDRAL'

    skin_bones = set()
    root_bones = set()

    root_bones.add(rig.data.bones[0].name)
    for bone in rig.data.bones:
        if bone not in root_bones:
            skin_bones.add(bone.name)

    skin_bone_orientation = get_bone_orientation(rig, skin_bones)

    if select_rig(rig):
        pose_bone: bpy.types.PoseBone
        for pose_bone in rig.pose.bones:
            bone = pose_bone.bone
            if bone.parent is None:
                if not pose_bone.parent:
                    pose_bone.custom_shape = widgets["root"]
                    set_bone_shape_scale(pose_bone, 20)
                else:
                    pose_bone.custom_shape = widgets["default"]
                    set_bone_shape_scale(pose_bone, 15)
                bone.hide = False
                pose_bone.use_custom_shape_bone_size = False
                bones.set_bone_color(pose_bone, "ROOT")
            else:
                pose_bone.custom_shape = widgets["skin"]
                bone.hide = False
                pose_bone.use_custom_shape_bone_size = True
                #pose_bone.bone.show_wire = True
                pose_bone.custom_shape_rotation_euler = skin_bone_orientation
                bones.set_bone_color(pose_bone, "SKIN")


def de_pivot(chr_cache):
    """Removes the pivot bones and corrects the parenting of the mesh objects
       from a CC/iC character or prop"""

    if chr_cache:
        rig = chr_cache.get_armature()
        objects = chr_cache.get_all_objects(include_armature=False,
                                            of_type="MESH")

        if rig and objects:

            true_parents = {}
            if select_rig(rig):
                obj: bpy.types.Object
                for obj in objects:
                    if obj.parent == rig:
                        if obj.parent_type == "BONE":
                            parent_bone_name = obj.parent_bone
                            parent_bone: bpy.types.PoseBone = rig.pose.bones[parent_bone_name]
                            if "CC_Base_Pivot" in parent_bone.name:
                                true_parent = parent_bone.parent
                                M = obj.matrix_world.copy()
                                true_parents[obj] = (true_parent, M)


            to_remove = []
            if edit_rig(rig):
                for edit_bone in rig.data.edit_bones:
                    if "CC_Base_Pivot" in edit_bone.name:
                        to_remove.append(edit_bone)

            for edit_bone in to_remove:
                rig.data.edit_bones.remove(edit_bone)

            for obj in true_parents:
                true_parent, M = true_parents[obj]
                obj.parent_bone = true_parent.name
                obj.matrix_world = M

            select_rig(rig)






class CCICMotionSetRename(bpy.types.Operator):
    bl_idname = "ccic.motion_set_rename"
    bl_label = "Rename Motion Set"

    prefix: bpy.props.StringProperty(name="Motion Prefix", default="")
    rig_id: bpy.props.StringProperty(name="Character / Rig ID", default="")
    motion_id: bpy.props.StringProperty(name="Motion Name / ID", default="")
    set_id = bpy.props.StringProperty(name="Set ID", default="")

    def execute(self, context):
        props = vars.props()

        prefix = self.prefix
        rig_id = self.rig_id
        motion_id = get_unique_set_motion_id(rig_id, self.motion_id, prefix, exclude_set_id=self.set_id)

        for action in bpy.data.actions:
            if "rl_set_id" in action:
                if action["rl_set_id"] == self.set_id:
                    set_id, set_generation, action_type_id, obj_id = get_motion_set(action)
                    if action_type_id == "ARM":
                        name = make_armature_action_name(rig_id, motion_id, prefix)
                        action.name = name
                    elif action_type_id == "KEY":
                        name = make_key_action_name(rig_id, motion_id, obj_id, prefix)
                        action.name = name

        return {"FINISHED"}

    def invoke(self, context, event):
        props = vars.props()
        prefs = vars.prefs()

        props.store_ui_list_indices()
        action = props.action_set_list_action
        chr_cache = props.get_context_character_cache(context)

        if not action:
            return {"FINISHED"}

        set_id, set_generation, action_type_id, key_object = get_motion_set(action)

        if not set_id:
            return {"FINISHED"}

        self.set_id = set_id

        prefix, rig_id, type_id, obj_id, motion_id = decode_action_name(action)
        if prefix:
            self.prefix = prefix
        else:
            self.prefix = ""
        if rig_id:
            self.rig_id = rig_id
        elif chr_cache:
            self.rig_id = chr_cache.character_name
        else:
            self.rig_id = "Rig"
        if motion_id:
            self.motion_id = motion_id
        elif action.name:
            self.motion_id = action.name.split("|")[-1]
        else:
            self.motion_id = "Motion"

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout

        split = layout.split(factor=0.35)
        col_1 = split.column()
        col_2 = split.column()

        col_1.label(text="Motion Set ID:")
        col_2.label(text=self.set_id)

        col_1.separator()
        col_2.separator()

        col_1.label(text="Prefix:")
        col_2.prop(self, "prefix", text="")

        col_1.separator()
        col_2.separator()

        col_1.label(text="Character / Rig ID:")
        col_2.prop(self, "rig_id", text="")

        col_1.separator()
        col_2.separator()

        col_1.label(text="Motion Name / ID:")
        col_2.prop(self, "motion_id", text="")

        layout.separator()

    @classmethod
    def description(cls, context, properties):
        return "Change the name, prefix, and character/rig id of the motion set"


class CCICMotionSetInfo(bpy.types.Operator):
    bl_idname = "ccic.motion_set_info"
    bl_label = "Motion Set Info"

    prefix: bpy.props.StringProperty(name="Motion Prefix", default="")
    rig_id: bpy.props.StringProperty(name="Character / Rig ID", default="")
    motion_id: bpy.props.StringProperty(name="Motion Name / ID", default="")
    set_id: bpy.props.StringProperty(name="Set ID", default="")

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        props = vars.props()
        prefs = vars.prefs()

        props.store_ui_list_indices()
        action = props.action_set_list_action
        chr_cache = props.get_context_character_cache(context)

        self.delete_me = False
        # TODO make delete an op button?
        # TODO use_fake_user button

        if not action:
            return {"FINISHED"}

        set_id, set_generation, action_type_id, key_object = get_motion_set(action)

        if not set_id:
            return {"FINISHED"}

        self.set_id = set_id

        prefix, rig_id, type_id, obj_id, motion_id = decode_action_name(action)
        if prefix:
            self.prefix = prefix
        if rig_id:
            self.rig_id = rig_id
        elif chr_cache:
            self.rig_id = chr_cache.character_name
        else:
            self.rig_id = "Rig"
        if motion_id:
            self.motion_id = motion_id
        elif action.name:
            self.motion_id = action.name.split("|")[-1]
        else:
            self.motion_id = "Motion"

        return context.window_manager.invoke_popup(self, width=600)

    def draw(self, context):
        layout = self.layout

        split = layout.split(factor=0.25)
        col_1 = split.column()
        col_2 = split.column()

        col_1.label(text="Motion Set ID:")
        col_2.label(text=self.set_id)

        col_1.separator()
        col_2.separator()

        col_1.label(text="Prefix:")
        col_2.label(text=self.prefix if self.prefix else "(None)")
        col_1.label(text="Character / Rig ID:")
        col_2.label(text=self.rig_id if self.rig_id else "(None)")
        col_1.label(text="Motion Name / ID:")
        col_2.label(text=self.motion_id if self.motion_id else "(None)")

        layout.separator()

        layout.label(text="Actions:")

        split = layout.split(factor=0.25)
        col_1 = split.column()
        col_2 = split.column()
        for action in bpy.data.actions:
            action_set_id = utils.custom_prop(action, "rl_set_id")
            action_type = utils.custom_prop(action, "rl_action_type")
            if action_set_id == self.set_id:
                if action_type == "ARM":
                    col_1.label(text="Armature")
                elif action_type == "KEY":
                    obj_id = utils.custom_prop(action, "rl_key_object", "(None)")
                    col_1.label(text=obj_id)
                else:
                    col_1.label(text="?")
                col_2.label(text=action.name)
        col_1.separator()
        col_2.separator()
        col_1.separator()
        row = col_2.split(factor=0.5).column().row()
        row.alert = True
        row.scale_y = 1.5
        row.operator("ccic.rigutils", text="Delete Motion Set", icon="ERROR").param = "DELETE_MOTION_SET"
        layout.separator()
        layout.separator()
        layout.separator()

    @classmethod
    def description(cls, context, properties):
        return "Show motion set info"


class CCICRigUtils(bpy.types.Operator):
    """Rig Utilities"""
    bl_idname = "ccic.rigutils"
    bl_label = "Rig Utils"
    bl_options = {"REGISTER"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    def execute(self, context):
        props = vars.props()
        prefs = vars.prefs()
        chr_cache = props.get_context_character_cache(context)

        if chr_cache:

            props.store_ui_list_indices()
            rig = chr_cache.get_armature()

            if rig:
                if self.param == "TOGGLE_SHOW_FULL_RIG":
                    toggle_show_full_rig(rig)

                elif self.param == "TOGGLE_SHOW_BASE_RIG":
                    toggle_show_base_rig(rig)

                elif self.param == "TOGGLE_SHOW_SPRING_RIG":
                    toggle_show_spring_rig(rig)

                elif self.param == "TOGGLE_SHOW_RIG_POSE":
                    toggle_rig_rest_position(rig)

                elif self.param == "TOGGLE_SHOW_SPRING_BONES":
                    springbones.toggle_show_spring_bones(rig)

                elif self.param == "BUTTON_RESET_POSE":
                    mode_selection = utils.store_mode_selection_state()
                    reset_pose(rig)
                    utils.restore_mode_selection_state(mode_selection)

                elif self.param == "SET_LIMB_FK":
                    if chr_cache.rigified:
                        set_rigify_ik_fk_influence(rig, 1.0)
                        poke_rig(rig)

                elif self.param == "SET_LIMB_IK":
                    if chr_cache.rigified:
                        set_rigify_ik_fk_influence(rig, 0.0)
                        poke_rig(rig)

                elif self.param == "LOAD_ACTION_SET":
                    action = props.action_set_list_action
                    load_motion_set(rig, action)

                elif self.param == "PUSH_ACTION_SET":
                    action = props.action_set_list_action
                    auto_index = chr_cache.get_auto_index()
                    push_motion_set(rig, action, auto_index)

                elif self.param == "CLEAR_ACTION_SET":
                    clear_motion_set(rig)

            if self.param == "SELECT_SET_STRIPS":
                strip = context.active_nla_strip
                select_strips_by_set(strip)

            elif self.param == "NLA_ALIGN_LEFT":
                strips = context.selected_nla_strips
                align_strips(strips, left=True)

            elif self.param == "NLA_ALIGN_TO_LEFT":
                strips = context.selected_nla_strips
                active_strip = context.active_nla_strip
                align_strips(strips, to_strip=active_strip, left=True)

            elif self.param == "NLA_ALIGN_RIGHT":
                strips = context.selected_nla_strips
                align_strips(strips, left=False)

            elif self.param == "NLA_ALIGN_TO_RIGHT":
                strips = context.selected_nla_strips
                active_strip = context.active_nla_strip
                align_strips(strips, to_strip=active_strip, left=False)

            elif self.param == "NLA_SIZE_SHORTEST":
                strips = context.selected_nla_strips
                size_strips(strips, longest=False)

            elif self.param == "NLA_SIZE_LONGEST":
                strips = context.selected_nla_strips
                size_strips(strips, longest=True)

            elif self.param == "NLA_SIZE_TO":
                strips = context.selected_nla_strips
                active_strip = context.active_nla_strip
                size_strips(strips, to_strip=active_strip)

            elif self.param == "NLA_RESET_SIZE":
                strips = context.selected_nla_strips
                size_strips(strips, reset=True)

            elif self.param == "SET_FAKE_USER_ON":
                action = props.action_set_list_action
                set_action_set_fake_user(action, True)

            elif self.param == "SET_FAKE_USER_OFF":
                action = props.action_set_list_action
                set_action_set_fake_user(action, False)

            elif self.param == "DELETE_MOTION_SET":
                action = props.action_set_list_action
                delete_motion_set(action)

            props.restore_ui_list_indices()

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "TOGGLE_SHOW_SPRING_BONES":
            return "Quick toggle for the armature layers to show just the spring bones or just the body bones"

        elif properties.param == "TOGGLE_SHOW_FULL_RIG":
            return "Toggles showing all the rig controls"

        elif properties.param == "TOGGLE_SHOW_BASE_RIG":
            return "Toggles showing the base rig controls"

        elif properties.param == "TOGGLE_SHOW_SPRING_RIG":
            return "Toggles showing just the spring rig controls"

        elif properties.param == "TOGGLE_SHOW_RIG_POSE":
            return "Toggles the rig between pose mode and rest pose"

        elif properties.param == "BUTTON_RESET_POSE":
            return "Clears all pose transforms"

        elif properties.param == "LOAD_ACTION_SET":
            return "Loads the chosen motion set (armature and shape key actions) into the all the character objects"

        elif properties.param == "PUSH_ACTION_SET":
            return "Pushes the chosen motion set (armature and shape key actions) into the NLA tracks of all the character objects at the current frame. " \
                   "A suitable track will be chosen to fit the actions. If there is no room available a new track will be added to contain the actions"

        elif properties.param == "CLEAR_ACTION_SET":
            return "Removes all actions from the character"

        elif properties.param == "SELECT_SET_STRIPS":
            return "Selects all the strips belonging to the same motion set and strip index"

        elif properties.param == "NLA_ALIGN_LEFT":
            return "Aligns all selected strips to the left most of frame of all selected strips"

        elif properties.param == "NLA_ALIGN_RIGHT":
            return "Aligns all selected strips to right most of frame of all selected strips"

        elif properties.param == "NLA_ALIGN_TO_LEFT":
            return "Aligns all selected strips to the left hand frame of the active strip"

        elif properties.param == "NLA_ALIGN_TO_RIGHT":
            return "Aligns all selected strips to the right hand frame of the active strip"

        elif properties.param == "NLA_SIZE_SHORTEST":
            return "Sets the frame lengths of all selected strips to the length of the shortest strip in the selection"

        elif properties.param == "NLA_SIZE_TO":
            return "Sets the frame lengths of all selected strips to the length of the active strip"

        elif properties.param == "NLA_SIZE_LONGEST":
            return "Sets the frame lengths of all selected strips to the length of the longest strip in the selection"

        elif properties.param == "NLA_RESET_SIZE":
            return "Resets the frame lengths of all selected strips to the length of the underlying action"

        elif properties.param == "SET_FAKE_USER_ON":
            return "Set fake user on all actions in the motion set"

        elif properties.param == "SET_FAKE_USER_OFF":
            return "Clear fake user on all actions in the motion set"

        elif properties.param == "DELETE_MOTION_SET":
            return "Delete all actions in the motion set"

        return ""