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
from . import utils, bones, vars


HEAD_RIG_NAME = "RL_Hair_Rig_Head"
JAW_RIG_NAME = "RL_Hair_Rig_Jaw"
HAIR_BONE_PREFIX = "RL_Hair"
BEARD_BONE_PREFIX = "RL_Beard"
HEAD_BONE_NAMES = ["ORG-spine.006", "CC_Base_Head", "RL_Head", "Head", "head"]
JAW_BONE_NAMES = ["ORG-jaw", "CC_Base_JawRoot", "RL_JawRoot", "JawRoot", "teeth.B"]
EYE_BONE_NAMES = ["ORG-eye.R", "ORG-eye.L", "CC_Base_R_Eye", "CC_Base_L_Eye", "CC_Base_R_Eye", "CC_Base_L_Eye"]
ROOT_BONE_NAMES = HEAD_BONE_NAMES.copy().extend(JAW_BONE_NAMES.copy())

AVAILABLE_SPRING_RIG_LIST = []


def get_spring_rig_name(parent_mode):
    if parent_mode == "JAW":
        hair_rig_name = JAW_RIG_NAME
    else:
        hair_rig_name = HEAD_RIG_NAME
    return hair_rig_name


def has_spring_rig(chr_cache, arm, parent_mode):
    hair_rig_name = get_spring_rig_name(parent_mode)
    hair_rig = bones.get_bone(arm, hair_rig_name)
    return hair_rig is not None


def get_spring_rigs(chr_cache, arm, parent_modes : list = None, mode = "POSE"):
    """Returns { parent_mode: {
                    "name": rig_name,
                    "bone_name": rig_root.name,
                    "bone": rig_root
               } }
       The bone will be either the edit bone, pose bone or bone depending on which mode Blender is in.
       (or the pose if preferred)
       """
    if not parent_modes:
        parent_modes = ["HEAD", "JAW"]
    spring_rigs = {}
    for parent_mode in parent_modes:
        rig_name = get_spring_rig_name(parent_mode)
        rig_root = get_spring_rig(chr_cache, arm, parent_mode, mode)
        if rig_root:
            spring_rigs[parent_mode] = { "name": rig_name,
                                         "bone_name" : rig_root.name,
                                         "bone": rig_root }
    return spring_rigs


def get_spring_rig_from_child(chr_cache, arm, bone_name, prefer_pose = True):

    try:
        if prefer_pose or utils.get_mode() == "POSE":
            bone = arm.pose.bones[bone_name]
        elif utils.get_mode() == "EDIT":
            bone = arm.data.edit_bones[bone_name]
        else:
            bone = arm.data.bones[bone_name]
    except:
        bone = None

    if bone:

        spring_rigs = get_spring_rigs(chr_cache, arm, mode = "POSE")

        while bone.parent:
            for parent_mode in spring_rigs:
                if spring_rigs[parent_mode]["bone"] == bone.parent:
                    return spring_rigs[parent_mode], bone.name
            bone = bone.parent

    return None, None


def get_spring_rig(chr_cache, arm, parent_mode, mode = "POSE", create_if_missing = False):
    """This will return either the edit bone, pose bone or bone depending on which mode Blender is in.
       (or the pose if preferred)
       """
    spring_rig_name = get_spring_rig_name(parent_mode)
    spring_rig = None
    if mode == "EDIT" and utils.get_mode() != "EDIT":
        utils.edit_mode_to(arm)
    if mode == "POSE" or utils.get_mode() == "POSE":
        if spring_rig_name in arm.pose.bones:
            return arm.pose.bones[spring_rig_name]
    elif mode == "EDIT" and utils.get_mode() == "EDIT":
        if spring_rig_name in arm.data.edit_bones:
            spring_rig = arm.data.edit_bones[spring_rig_name]
        if not spring_rig and create_if_missing:
            root_bone_name = get_spring_root_name(chr_cache, arm, parent_mode)
            center_position = get_spring_rig_position(chr_cache, arm, parent_mode)
            spring_rig = bones.new_edit_bone(arm, spring_rig_name, root_bone_name)
            spring_rig.head = arm.matrix_world.inverted() @ center_position
            spring_rig.tail = arm.matrix_world.inverted() @ (center_position + Vector((0,1/32,0)))
            spring_rig.align_roll(Vector((0,0,1)))
            bones.set_edit_bone_layer(arm, spring_rig_name, 24)
        return spring_rig
    else:
        if spring_rig_name in arm.data.bones:
            return arm.data.bones[spring_rig_name]
    return None


def get_spring_rig_prefix(parent_mode):
    if parent_mode == "HAIR":
        return HAIR_BONE_PREFIX
    elif parent_mode == "JAW":
        return BEARD_BONE_PREFIX
    else:
        return "NONE"


def get_spring_root_name(chr_cache, arm, parent_mode):
    if parent_mode == "HEAD":
        possible_head_bones = HEAD_BONE_NAMES
        for name in possible_head_bones:
            if name in arm.data.bones:
                return name
        return None
    elif parent_mode == "JAW":
        possible_jaw_bones = JAW_BONE_NAMES
        for name in possible_jaw_bones:
            if name in arm.data.bones:
                return name
        return None


def get_spring_rig_position(chr_cache, arm, root_mode):
    """Returns the approximate position inside the head between the ears at nose height."""

    head_edit_bone = get_root_edit_bone(chr_cache, arm, "HEAD")

    if head_edit_bone:
        head_pos = arm.matrix_world @ head_edit_bone.head

        eye_pos = Vector((0,0,0))
        count = 0
        for eye_bone_name in EYE_BONE_NAMES:
            eye_edit_bone = bones.get_edit_bone(arm, eye_bone_name)
            if eye_edit_bone:
                count += 1
                eye_pos += arm.matrix_world @ eye_edit_bone.head

        if count > 0:
            eye_pos /= count

            if root_mode == "HEAD":
                return Vector((head_pos[0], head_pos[1], eye_pos[2]))
            elif root_mode == "JAW":
                return Vector((head_pos[0], (head_pos[1] + 2 * eye_pos[1]) / 3, head_pos[2]))
        else:
            return head_pos

    return None


def get_root_edit_bone(chr_cache, arm, parent_mode):
    try:
        return arm.data.edit_bones[get_spring_root_name(chr_cache, arm, parent_mode)]
    except:
        return None


def is_hair_bone(bone_name):
    if bone_name.startswith(HAIR_BONE_PREFIX) or bone_name.startswith(BEARD_BONE_PREFIX):
        return True
    else:
        return False


def is_hair_rig_bone(bone_name):
    if bone_name.startswith(HEAD_RIG_NAME) or bone_name.startswith(JAW_RIG_NAME):
        return True
    else:
        return False


def realign_spring_bones_axis(chr_cache, arm):

    utils.edit_mode_to(arm, True)

    # align z-axis away from the spring roots
    spring_rigs = get_spring_rigs(chr_cache, arm, mode = "EDIT")
    for parent_mode in spring_rigs:
        spring_root = spring_rigs[parent_mode]["bone"]
        spring_bones = bones.get_bone_children(spring_root)
        for bone in spring_bones:
            if bone != spring_root:
                head = arm.matrix_world @ bone.head
                tail = arm.matrix_world @ bone.tail
                origin = arm.matrix_world @ spring_root.head
                z_axis = (((head + tail) * 0.5) - origin).normalized()
                bone.align_roll(z_axis)

    # save edit mode changes
    utils.object_mode_to(arm)


def enumerate_spring_rigs(self, context):
    global AVAILABLE_SPRING_RIG_LIST
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_context_character_cache(context)

    if chr_cache:
        arm = chr_cache.get_armature()

        spring_rigs = get_spring_rigs(chr_cache, arm, mode = "POSE")
        AVAILABLE_SPRING_RIG_LIST.clear()
        for i, parent_mode in enumerate(spring_rigs):
            list_entry = (parent_mode, f"{parent_mode} Rig", f"{parent_mode} Rig")
            AVAILABLE_SPRING_RIG_LIST.append(list_entry)

    return AVAILABLE_SPRING_RIG_LIST

