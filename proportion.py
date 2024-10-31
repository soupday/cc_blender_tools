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
import os
from mathutils import Vector
from . import rigutils, modifiers, bones, utils, vars


def hide_sub_bones(rig, hide=True):
    """Hides twist and share bones"""
    bone: bpy.types.Bone
    for bone in rig.data.bones:
        bone_name: str = bone.name
        if "ShareBone" in bone_name or ("Twist" in bone_name and "NeckTwist" not in bone_name) or "_twist_" in bone_name:
            bone.hide = hide
            bone.select = False


def convert_to_blender_bone_names(chr_cache):
    if chr_cache and not chr_cache.rigified and not chr_cache.proportion_editing:
        rig = chr_cache.get_armature()
        objects = chr_cache.get_all_objects(include_armature=False,
                                            include_children=True,
                                            of_type="MESH")

        bone_remap = {}

        for bone in rig.data.bones:
            source_name: str = bone.name
            bone_name = source_name
            if "_L_" in bone.name:
                bone_name = bone_name.replace("_L_", "_X_") + ".l"
                bone_remap[bone.name] = bone_name
                bone.name = bone_name
            if "_R_" in bone.name:
                bone_name = bone_name.replace("_R_", "_X_") + ".r"
                bone_remap[bone.name] = bone_name
                bone.name = bone_name

        for obj in objects:
            for vg in obj.vertex_groups:
                if vg.name in bone_remap:
                    vg.name = bone_remap[vg.name]

        chr_cache.proportion_editing = True


def restore_cc_bone_names(chr_cache):
    if chr_cache and not chr_cache.rigified and chr_cache.proportion_editing:
        rig = chr_cache.get_armature()
        objects = chr_cache.get_all_objects(include_armature=False,
                                            include_children=True,
                                            of_type="MESH")

        bone_restore = {}

        for bone in rig.data.bones:
            bone_name: str = bone.name
            if "_X_" in bone.name and bone.name.endswith(".l"):
                bone_name = bone_name.replace("_X_", "_L_")[:-2]
                bone_restore[bone.name] = bone_name
                bone.name = bone_name
            if "_X_" in bone.name and bone.name.endswith(".r"):
                bone_name = bone_name.replace("_X_", "_R_")[:-2]
                bone_restore[bone.name] = bone_name
                bone.name = bone_name

        for obj in objects:
            for vg in obj.vertex_groups:
                if vg.name in bone_restore:
                    vg.name = bone_restore[vg.name]

        chr_cache.proportion_editing = False


def prep_rig(chr_cache):
    if chr_cache:
        rig = chr_cache.get_armature()
        rigutils.fix_cc3_standard_rig(rig)
        rigutils.select_rig(rig)
        if rig:
            chr_cache.proportion_editing_in_front = rig.show_in_front
            rig_action = utils.safe_get_action(rig)
            chr_cache.proportion_editing_actions.clear()
            if rig_action:
                action_store = chr_cache.proportion_editing_actions.add()
                action_store.object = rig
                action_store.action = rig_action
                utils.safe_set_action(rig, None)
            rig.pose.use_mirror_x = True
            bones.clear_pose(rig)
            utils.pose_mode_to(rig)
            hide_sub_bones(rig)
            rigutils.reset_rotation_modes(rig)
            rig.show_in_front = True
            # reset all shape keys
            objects = chr_cache.get_all_objects(include_armature=False,
                                                include_children=True,
                                                of_type="MESH")
            for obj in objects:
                if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
                    key_action = utils.safe_get_action(obj.data.shape_keys)
                    if key_action:
                        action_store = chr_cache.proportion_editing_actions.add()
                        action_store.object = obj
                        action_store.action = key_action
                        utils.safe_set_action(obj.data.shape_keys, None)
                    key: bpy.types.ShapeKey
                    for key in obj.data.shape_keys.key_blocks:
                        key.value = 0.0


def restore_rig(chr_cache):
    if chr_cache:
        rig = chr_cache.get_armature()
        if rig:
            # restore actions
            for action_store in chr_cache.proportion_editing_actions:
                obj = action_store.object
                action = action_store.action
                if utils.object_exists_is_armature(obj):
                    utils.safe_set_action(obj, action)
                elif utils.object_exists_is_mesh(obj):
                    utils.safe_set_action(obj.data.shape_keys, action)
            chr_cache.proportion_editing_actions.clear()
            # restore rig
            utils.object_mode_to(rig)
            hide_sub_bones(rig, False)
            rig.show_in_front = chr_cache.proportion_editing_in_front
            chr_cache.proportion_editing_action = None


def apply_proportion_pose(chr_cache):
    if chr_cache:
        rig = chr_cache.get_armature()
        if rig:
            hide_sub_bones(rig, False)
            rigutils.apply_as_rest_pose(rig)


def set_child_inherit_scale(rig, pose_bone: bpy.types.PoseBone, inherit_scale):
    child_bone: bpy.types.PoseBone
    pose_bones = [pose_bone]
    if rig.pose.use_mirror_x:
        mirror_name = None
        if pose_bone.name.endswith(".r"):
            mirror_name = pose_bone.name[:-1] + "l"
        elif pose_bone.name.endswith(".R"):
            mirror_name = pose_bone.name[:-1] + "L"
        elif pose_bone.name.endswith(".l"):
            mirror_name = pose_bone.name[:-1] + "r"
        elif pose_bone.name.endswith(".L"):
            mirror_name = pose_bone.name[:-1] + "R"
        if mirror_name and mirror_name in rig.pose.bones:
            pose_bones.append(rig.pose.bones[mirror_name])
    for pose_bone in pose_bones:
        for child_bone in pose_bone.children:
            bone_name = child_bone.name
            if "ShareBone" in bone_name or ("Twist" in bone_name and "NeckTwist" not in bone_name):
                child_bone.bone.inherit_scale = "FULL"
            else:
                child_bone.bone.inherit_scale = inherit_scale


def reset_proportions(rig):
    for pose_bone in rig.pose.bones:
        pose_bone.bone.inherit_scale = "FULL"
        pose_bone.scale = Vector((1,1,1))


class CCICCharacterProportions(bpy.types.Operator):
    """Edit a characters proportions to generate a new bind pose shape"""
    bl_idname = "ccic.characterproportions"
    bl_label = "Character Proportions"
    bl_options = {"REGISTER", "UNDO"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    def execute(self, context):
        props = vars.props()
        chr_cache = props.get_context_character_cache(context)

        if chr_cache and not chr_cache.rigified:

            if self.param == "BEGIN":
                prep_rig(chr_cache)
                convert_to_blender_bone_names(chr_cache)

            elif self.param == "END":
                apply_proportion_pose(chr_cache)
                restore_rig(chr_cache)
                restore_cc_bone_names(chr_cache)

            elif self.param.startswith("INHERIT_SCALE"):
                inherit_scale = self.param[14:]
                if utils.get_mode() == "POSE" and utils.get_active_object() and bpy.context.active_pose_bone:
                    set_child_inherit_scale(utils.get_active_object(), bpy.context.active_pose_bone, inherit_scale)

            elif self.param == "RESET":
                if utils.get_mode() == "POSE" and utils.get_active_object():
                    reset_proportions(utils.get_active_object())

        return {"FINISHED"}


    @classmethod
    def description(cls, context, properties):
        if properties.param == "BEGIN":
            return """Begin character proportion editing"""
        elif properties.param == "END":
            return """End character proportion editing"""
        return ""