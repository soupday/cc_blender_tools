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
from mathutils import Vector
from random import random
from . import bones, rigify_mapping_data, utils


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
                if not name_in_data_paths(action, bone_name):
                    return False
            return True
    return False


def is_Mixamo_armature(armature):
    if armature:
        if len(armature.data.bones) > 0:
            for bone_name in rigify_mapping_data.MIXAMO_BONE_NAMES:
                if bone_name not in armature.data.bones:
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


def is_rl_rigify_armature(armature):
    if armature:
        if len(armature.data.bones) > 0:
            for bone_name in rigify_mapping_data.RL_RIGIFY_BONE_NAMES:
                if bone_name not in armature.data.bones:
                    return False
            return True
    return False


def is_unity_action(action):
    return "_Unity" in action.name and "|A|" in action.name


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
    arm.name = name
    arm.name = name
    arm.data.name = name
    arm.data.name = name
    return armature_object, armature_data


def restore_armature_names(armature_object, armature_data, name):
    if armature_object:
        armature_object.name = name
        armature_object.name = name
    if armature_data:
        armature_data.name = name
        armature_data.name = name


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


def set_bone_tail_length(bone: bpy.types.EditBone, new_tail: Vector):
    """Set the length based on a new tail position, but don't set the tail directly
       as it may cause changes in the bone roll and angles."""
    length = (new_tail - bone.head).length
    bone.length = length


def fix_cc3_bone_sizes(cc3_rig):
    if edit_rig(cc3_rig):
        left_eye = bones.get_edit_bone(cc3_rig, "CC_Base_L_Eye")
        right_eye = bones.get_edit_bone(cc3_rig, "CC_Base_R_Eye")
        left_hand = bones.get_edit_bone(cc3_rig, "CC_Base_L_Hand")
        right_hand = bones.get_edit_bone(cc3_rig, "CC_Base_R_Hand")
        left_foot = bones.get_edit_bone(cc3_rig, "CC_Base_L_Foot")
        right_foot = bones.get_edit_bone(cc3_rig, "CC_Base_R_Foot")
        head = bones.get_edit_bone(cc3_rig, "CC_Base_Head")
        left_upper_arm = bones.get_edit_bone(cc3_rig, "CC_Base_L_Upperarm")
        right_upper_arm = bones.get_edit_bone(cc3_rig, "CC_Base_R_Upperarm")
        left_lower_arm = bones.get_edit_bone(cc3_rig, "CC_Base_L_Forearm")
        right_lower_arm = bones.get_edit_bone(cc3_rig, "CC_Base_R_Forearm")
        left_thigh = bones.get_edit_bone(cc3_rig, "CC_Base_L_Thigh")
        right_thigh = bones.get_edit_bone(cc3_rig, "CC_Base_R_Thigh")
        left_calf = bones.get_edit_bone(cc3_rig, "CC_Base_L_Calf")
        right_calf = bones.get_edit_bone(cc3_rig, "CC_Base_R_Calf")
        eye_z = ((left_eye.head + right_eye.head) * 0.5).z
        # head
        head_tail = head.tail.copy()
        head_tail.z = eye_z
        set_bone_tail_length(head, head_tail)
        # arms
        set_bone_tail_length(left_upper_arm, left_lower_arm.head)
        set_bone_tail_length(right_upper_arm, right_lower_arm.head)
        set_bone_tail_length(left_lower_arm, left_hand.head)
        set_bone_tail_length(right_lower_arm, right_hand.head)
        # legs
        set_bone_tail_length(left_thigh, left_calf.head)
        set_bone_tail_length(right_thigh, right_calf.head)
        set_bone_tail_length(left_calf, left_foot.head)
        set_bone_tail_length(right_calf, right_foot.head)


def reset_rotation_modes(rig, rotation_mode = "QUATERNION"):
    pose_bone: bpy.types.PoseBone
    for pose_bone in rig.pose.bones:
        pose_bone.rotation_mode = rotation_mode