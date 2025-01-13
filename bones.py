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
import mathutils
from math import pi, atan

from . import drivers, utils, vars
from rna_prop_ui import rna_idprop_ui_create


def cmp_rl_bone_names(name, bone_name):
    """Reduce supplied bone names to their base form without prefixes and compare."""
    if bone_name.startswith("RL_"):
        bone_name = bone_name[3:]
    elif bone_name.startswith("CC_Base_"):
        bone_name = bone_name[8:]
    if name.startswith("RL_"):
        name = name[3:]
    elif name.startswith("CC_Base_"):
        name = name[8:]
    return name == bone_name


def get_rl_edit_bone(rig, name) -> bpy.types.EditBone:
    if name:
        if name in rig.data.edit_bones:
            return rig.data.edit_bones[name]
        # remove "CC_Base_" from start of bone name and try again...
        if name.startswith("CC_Base_"):
            name = name[8:]
            if name in rig.data.edit_bones:
                return rig.data.edit_bones[name]
        if name.startswith("RL_"):
            name = name[3:]
            if name in rig.data.edit_bones:
                return rig.data.edit_bones[name]
    return None


def get_rl_bone(rig, name):
    if name:
        if name in rig.data.bones:
            return rig.data.bones[name]
        # remove "CC_Base_" from start of bone name and try again...
        if name.startswith("CC_Base_"):
            name = name[8:]
            if name in rig.data.bones:
                return rig.data.bones[name]
        if name.startswith("RL_"):
            name = name[3:]
            if name in rig.data.bones:
                return rig.data.bones[name]
    return None


def get_rl_pose_bone(rig, name) -> bpy.types.PoseBone:
    if name:
        if name in rig.pose.bones:
            return rig.pose.bones[name]
        # remove "CC_Base_" from start of bone name and try again...
        if name.startswith("CC_Base_"):
            name = name[8:]
            if name in rig.pose.bones:
                return rig.pose.bones[name]
        if name.startswith("RL_"):
            name = name[3:]
            if name in rig.pose.bones:
                return rig.pose.bones[name]
    return None


def get_edit_bone(rig, name) -> bpy.types.EditBone:
    if name:
        if type(name) is list:
            for n in name:
                if n in rig.data.edit_bones:
                    return rig.data.edit_bones[n]
        else:
            if name in rig.data.edit_bones:
                return rig.data.edit_bones[name]
    return None


def get_bone(rig, name) -> bpy.types.Bone:
    if name:
        if type(name) is list:
            for n in name:
                if n in rig.data.bones:
                    return rig.data.bones[n]
        else:
            if name in rig.data.bones:
                return rig.data.bones[name]
    return None


def get_pose_bone(rig, name) -> bpy.types.PoseBone:
    if name:
        if type(name) is list:
            for n in name:
                if n in rig.pose.bones:
                    return rig.pose.bones[n]
        else:
            if name in rig.pose.bones:
                return rig.pose.bones[name]
    return None


def find_target_pose_bone(rig, rl_bone_name, bone_mapping = None) -> bpy.types.PoseBone:
    target_bone_name = find_target_bone_name(rig, rl_bone_name, bone_mapping)
    if target_bone_name in rig.pose.bones:
        return rig.pose.bones[target_bone_name]
    return None


def is_target_bone_name(bone_name, target_name):
    if not bone_name or not target_name:
        return False
    if target_name == bone_name:
        return True
    if cmp_rl_bone_names(target_name, bone_name):
        return True
    target_name = rl_export_bone_name(target_name)
    if target_name == bone_name:
        return True
    if cmp_rl_bone_names(target_name, bone_name):
        return True


def rl_export_bone_name(bone_name):
    bone_name = bone_name.replace(' ', '_')
    bone_name = bone_name.replace('(', '_')
    bone_name = bone_name.replace(')', '_')
    bone_name = bone_name.replace('&', '_')
    return bone_name


def find_target_bone_name(rig, rl_bone_name, bone_mapping=None):
    if not rig or not rl_bone_name:
        return None
    target_bone_name = None
    if bone_mapping:
        target_bone_name = get_rigify_meta_bone(rig, bone_mapping, rl_bone_name)
    else:
        target_bone_name = rl_bone_name
    if target_bone_name in rig.pose.bones:
        return target_bone_name
    for pose_bone in rig.pose.bones:
        if cmp_rl_bone_names(target_bone_name, pose_bone.name):
            return pose_bone.name
    target_bone_name = rl_export_bone_name(target_bone_name)
    for pose_bone in rig.pose.bones:
        if cmp_rl_bone_names(target_bone_name, pose_bone.name):
            return pose_bone.name
    return None


def find_pivot_bone(rig, bone_name):
    if bone_name in rig.data.bones:
        bone: bpy.types.Bone = rig.data.bones[bone_name]
        for child in bone.children:
            if child.name.startswith("CC_Base_Pivot"):
                return child
    return None


def get_rigify_meta_bone(rigify_rig, bone_mapping, cc3_bone_name):
    if cc3_bone_name == "RL_BoneRoot" or cc3_bone_name == "CC_Base_BoneRoot":
        return "root"
    for bone_map in bone_mapping:
        if bone_map[1] == cc3_bone_name:
            # try to find the parent in the ORG bones
            org_bone_name = f"ORG-{bone_map[0]}"
            if org_bone_name in rigify_rig.data.bones:
                return org_bone_name
            # then try the DEF bones
            def_bone_name = f"DEF-{bone_map[0]}"
            if def_bone_name in rigify_rig.data.bones:
                return def_bone_name
    return None


def get_rigify_meta_bones(rigify_rig, bone_mapping, cc3_bone_name):
    meta_bone_names = []
    if cc3_bone_name == "RL_BoneRoot" or cc3_bone_name == "CC_Base_BoneRoot":
        return ["root"]
    for bone_map in bone_mapping:
        if bone_map[1] == cc3_bone_name:
            # try to find the parent in the ORG bones
            org_bone_name = f"ORG-{bone_map[0]}"
            if org_bone_name in rigify_rig.data.bones:
                meta_bone_names.append(org_bone_name)
            # then try the DEF bones
            def_bone_name = f"DEF-{bone_map[0]}"
            if def_bone_name in rigify_rig.data.bones:
                meta_bone_names.append(def_bone_name)
    return meta_bone_names


def get_align_vector(axis):
    if axis == "X":
        return mathutils.Vector((1,0,0))
    if axis == "Y":
        return mathutils.Vector((0,1,0))
    if axis == "Z":
        return mathutils.Vector((0,0,1))
    if axis == "-X":
        return mathutils.Vector((-1,0,0))
    if axis == "-Y":
        return mathutils.Vector((0,-1,0))
    if axis == "-Z":
        return mathutils.Vector((0,0,-1))
    return None


def align_edit_bone_roll(edit_bone : bpy.types.EditBone, axis):
    align_vector = get_align_vector(axis)
    if align_vector:
        edit_bone.align_roll(align_vector)


def rename_bone(rig, from_name, to_name):
    if utils.edit_mode_to(rig):
        bone = get_edit_bone(rig, from_name)
        if bone and to_name not in rig.data.edit_bones:
            bone.name = to_name
        else:
            utils.log_error(f"Bone {from_name} cannot be renamed as {to_name} already exists in rig!")


def copy_edit_bone(rig, src_name, dst_name, parent_name, scale):
    if utils.edit_mode_to(rig):
        src_bone = get_edit_bone(rig, src_name)
        if src_bone and dst_name not in rig.data.edit_bones:
            dst_bone = rig.data.edit_bones.new(dst_name)
            dst_bone.head = src_bone.head
            dst_bone.tail = src_bone.head + (src_bone.tail - src_bone.head) * scale
            dst_bone.roll = src_bone.roll
            if parent_name != "":
                if parent_name in rig.data.edit_bones:
                    dst_bone.parent = rig.data.edit_bones[parent_name]
                else:
                    utils.log_error(f"Unable to find parent bone {parent_name} in rig!")
            return dst_bone
        else:
            if src_name not in rig.data.edit_bones:
                utils.log_error(f"Unable to find source bone {src_name} in rig!")
            if dst_name in rig.data.edit_bones:
                utils.log_error(f"Destination bone {dst_name} already exists in rig!")
    else:
        utils.log_error(f"Unable to edit rig!")
    return None


def new_edit_bone(rig, bone_name, parent_name, allow_existing = True):
    if utils.edit_mode_to(rig):
        can_add = allow_existing or bone_name not in rig.data.edit_bones
        if can_add:
            bone = rig.data.edit_bones.new(bone_name)
            bone.head = mathutils.Vector((0,0,0))
            bone.tail = bone.head + mathutils.Vector((0,0,0.05))
            bone.roll = 0
            if parent_name != "":
                if parent_name in rig.data.edit_bones:
                    bone.parent = rig.data.edit_bones[parent_name]
                else:
                    utils.log_error(f"Unable to find parent bone {parent_name} in rig!")
            return bone
        else:
            utils.log_error(f"Destination bone {bone_name} already exists in rig!")
    else:
        utils.log_error(f"Unable to edit rig!")
    return None


def reparent_edit_bone(rig, bone_name, parent_name):
    if utils.edit_mode_to(rig):
        if bone_name in rig.data.bones:
            bone = rig.data.edit_bones[bone_name]
            if bone:
                if parent_name != "":
                    parent_bone = get_edit_bone(rig, parent_name)
                    if parent_bone:
                        bone.parent = parent_bone
                        return bone
                    else:
                        utils.log_error(f"Could not find parent bone: {parent_name} in Rig!")
        else:
            utils.log_error(f"Could not find target bone: {bone_name} in Rig!")
    else:
        utils.log_error(f"Unable to edit rig!")
    return None


def copy_rl_edit_bone(cc3_rig, dst_rig, cc3_name, dst_name, dst_parent_name, scale):
    if utils.edit_mode_to(cc3_rig):
        src_bone = get_rl_edit_bone(cc3_rig, cc3_name)
        if src_bone:
            # cc3 rig is usually scaled by 0.01, so calculate the world positions.
            head_pos = cc3_rig.matrix_world @ src_bone.head
            tail_pos = cc3_rig.matrix_world @ src_bone.tail
            roll = src_bone.roll
            if utils.edit_mode_to(dst_rig):
                # meta and rigify rigs are at 1.0 scale so all bones are in world space (at the origin)
                dst_bone = dst_rig.data.edit_bones.new(dst_name)
                dst_bone.head = head_pos
                dst_bone.tail = head_pos + (tail_pos - head_pos) * scale
                dst_bone.roll = roll
                if dst_parent_name != "":
                    parent_bone = get_edit_bone(dst_rig, dst_parent_name)
                    if parent_bone:
                        dst_bone.parent = parent_bone
                    else:
                        utils.log_error(f"Could not find parent bone: {dst_parent_name} in target Rig!")
                return dst_bone
            else:
                utils.log_error(f"Unable to edit target rig!")
        else:
            utils.log_error(f"Could not find bone: {cc3_name} in CC3 Rig!")
    else:
        utils.log_error(f"Unable to edit CC3 rig!")
    return None


def copy_pose(rig):
    pose = {}
    bone: bpy.types.PoseBone
    for bone in rig.pose.bones:
        pose[bone.name] = (bone.rotation_mode,
                           bone.rotation_quaternion.copy(),
                           bone.rotation_euler.copy(),
                           bone.rotation_axis_angle,
                           bone.location.copy(),
                           bone.scale.copy())
    return pose


def paste_pose(rig: bpy.types.Object, pose):
    bone: bpy.types.PoseBone
    for bone in rig.pose.bones:
        bone.rotation_mode, bone.rotation_quaternion, bone.rotation_euler, bone.rotation_axis_angle, bone.location, bone.scale = pose[bone.name]


def copy_rig_bind_pose(rig_from, rig_to):
    rig_def = {}
    utils.set_only_active_object(rig_from)
    if utils.edit_mode_to(rig_from):
        for edit_bone in rig_from.data.edit_bones:
            rig_def[edit_bone.name] = {
                "head": edit_bone.head.copy(),
                "tail": edit_bone.tail.copy(),
                "roll": edit_bone.roll,
            }
    utils.set_only_active_object(rig_to)
    if utils.edit_mode_to(rig_to):
        for edit_bone in rig_to.data.edit_bones:
            if edit_bone.name in rig_def:
                bone_def = rig_def[edit_bone.name]
                edit_bone.head = bone_def["head"].copy()
                edit_bone.tail = bone_def["tail"].copy()
                edit_bone.roll = bone_def["roll"]


def get_bone_children(bone, bone_list = None, include_root = False):
    is_root = False
    if bone_list is None:
        is_root = True
        bone_list = []
    if include_root or not is_root:
        bone_list.append(bone)
    for child in bone.children:
        get_bone_children(child, bone_list, include_root)
    return bone_list


def get_edit_bone_subtree_defs(rig, bone : bpy.types.EditBone, tree = None):

    if tree is None:
            tree = []

    # bone must have a parent for it to be a sub-tree
    if utils.edit_mode_to(rig) and bone.parent:

        bone_data = [bone.name,
                    rig.matrix_world @ bone.head,
                    rig.matrix_world @ bone.tail,
                    bone.head_radius,
                    bone.tail_radius,
                    bone.roll,
                    bone.parent.name]

        tree.append(bone_data)

        for child_bone in bone.children:
            get_edit_bone_subtree_defs(rig, child_bone, tree)

    return tree


def copy_rl_edit_bone_subtree(cc3_rig, dst_rig, cc3_name, dst_name, dst_parent_name, dst_prefix, collection, layer, vertex_group_map):

    src_bone_defs = None

    # copy the cc3 bone sub-tree to the destination rig
    if utils.edit_mode_to(cc3_rig):
        cc3_bone = get_edit_bone(cc3_rig, cc3_name)
        src_bone_defs = get_edit_bone_subtree_defs(cc3_rig, cc3_bone)

        if utils.edit_mode_to(dst_rig):

            for bone_def in src_bone_defs:
                src_name = bone_def[0]
                if src_name == cc3_name:
                    name = dst_name
                    parent_name = dst_parent_name
                else:
                    name = f"{dst_prefix}{bone_def[0]}"
                    src_parent_name = bone_def[6]
                    parent_name = vertex_group_map[src_parent_name]
                head = bone_def[1]
                tail = bone_def[2]
                head_radius = bone_def[3]
                tail_radius = bone_def[4]
                roll = bone_def[5]

                bone : bpy.types.EditBone = dst_rig.data.edit_bones.new(name)
                bone.head = head
                bone.tail = tail
                bone.head_radius = head_radius
                bone.tail_radius = tail_radius
                bone.roll = roll

                # store the name of the newly created bone (in case Blender has changed it)
                vertex_group_map[src_name] = bone.name
                bone_def.append(bone.name)

                # set the edit bone layers
                set_bone_collection(dst_rig, bone, collection, None, layer)

                # set the bone parent
                parent_bone = get_edit_bone(dst_rig, parent_name)
                if parent_bone:
                    bone.parent = parent_bone

            # set pose bone layers
            if utils.object_mode():
                for bone_def in src_bone_defs:
                    name = bone_def[7]
                    pose_bone = dst_rig.data.bones[name]
                    set_bone_collection(dst_rig, pose_bone, collection, None, layer)

    return src_bone_defs


def add_copy_transforms_constraint(from_rig, to_rig, from_bone, to_bone, influence = 1.0, space="WORLD"):
    try:
        if utils.object_mode():
            to_pose_bone : bpy.types.PoseBone = to_rig.pose.bones[to_bone]
            c : bpy.types.CopyTransformsConstraint = to_pose_bone.constraints.new(type="COPY_TRANSFORMS")
            c.target = from_rig
            c.subtarget = from_bone
            c.head_tail = 0
            c.mix_mode = "REPLACE"
            c.target_space = space
            c.owner_space = space
            c.influence = influence
            return c
    except Exception as e:
        utils.log_error(f"Unable to add copy transforms constraint: {to_bone} {from_bone}", e)
        return None


def add_copy_rotation_constraint(from_rig, to_rig, from_bone, to_bone, influence = 1.0, space="WORLD"):
    try:
        if utils.object_mode():
            to_pose_bone : bpy.types.PoseBone = to_rig.pose.bones[to_bone]
            c : bpy.types.CopyRotationConstraint = to_pose_bone.constraints.new(type="COPY_ROTATION")
            c.target = from_rig
            c.subtarget = from_bone
            c.use_x = True
            c.use_y = True
            c.use_z = True
            c.invert_x = False
            c.invert_y = False
            c.invert_z = False
            c.mix_mode = "REPLACE"
            c.target_space = space
            if space == "LOCAL_OWNER_ORIENT":
                space = "LOCAL"
            c.owner_space = space
            c.influence = influence
            return c
    except Exception as e:
        utils.log_error(f"Unable to add copy rotation constraint: {to_bone} {from_bone}", e)
        return None


def add_copy_scale_constraint(from_rig, to_rig, from_bone, to_bone, influence = 1.0, space="WORLD"):
    try:
        if utils.object_mode():
            to_pose_bone : bpy.types.PoseBone = to_rig.pose.bones[to_bone]
            c : bpy.types.CopyScaleConstraint = to_pose_bone.constraints.new(type="COPY_SCALE")
            c.target = from_rig
            c.subtarget = from_bone
            c.use_x = True
            c.use_y = True
            c.use_z = True
            c.target_space = space
            if space == "LOCAL_OWNER_ORIENT":
                space = "LOCAL"
            c.owner_space = space
            c.influence = influence
            return c
    except Exception as e:
        utils.log_error(f"Unable to add copy scale constraint: {to_bone} {from_bone}", e)
        return None


def add_copy_location_constraint(from_rig, to_rig, from_bone, to_bone, influence = 1.0, space="WORLD", axes=None):
    try:
        if utils.object_mode():
            to_pose_bone : bpy.types.PoseBone = to_rig.pose.bones[to_bone]
            c : bpy.types.CopyLocationConstraint = to_pose_bone.constraints.new(type="COPY_LOCATION")
            c.target = from_rig
            c.subtarget = from_bone
            c.use_x = True
            c.use_y = True
            c.use_z = True
            c.invert_x = False
            c.invert_y = False
            c.invert_z = False
            c.target_space = space
            if space == "LOCAL_OWNER_ORIENT":
                space = "LOCAL"
            c.owner_space = space
            c.influence = influence
            if axes:
                c.use_x = "X" in axes
                c.use_y = "Y" in axes
                c.use_z = "Z" in axes
                c.invert_x = "-X" in axes
                c.invert_y = "-Y" in axes
                c.invert_z = "-Z" in axes
            return c
    except Exception as e:
        utils.log_error(f"Unable to add copy location constraint: {to_bone} {from_bone}", e)
        return None


def add_stretch_to_constraint(from_rig, to_rig, from_bone, to_bone, influence = 1.0, head_tail = 0.0, space="WORLD"):
    try:
        if utils.object_mode():
            to_pose_bone : bpy.types.PoseBone = to_rig.pose.bones[to_bone]
            c : bpy.types.StretchToConstraint = to_pose_bone.constraints.new(type="STRETCH_TO")
            c.target = from_rig
            c.subtarget = from_bone
            c.head_tail = head_tail
            c.target_space = space
            if space == "LOCAL_OWNER_ORIENT":
                space = "LOCAL"
            c.owner_space = space
            c.influence = influence
            return c
    except Exception as e:
        utils.log_error(f"Unable to add copy stretch to constraint: {to_bone} {from_bone}", e)
        return None


def add_damped_track_constraint(rig, bone_name, target_name, influence):
    try:
        if utils.object_mode():
            pose_bone : bpy.types.PoseBone = rig.pose.bones[bone_name]
            c : bpy.types.DampedTrackConstraint = pose_bone.constraints.new(type="DAMPED_TRACK")
            c.target = rig
            c.subtarget = target_name
            c.head_tail = 0
            c.track_axis = "TRACK_Y"
            c.influence = influence
            return c
    except Exception as e:
        utils.log_error(f"Unable to add damped track constraint: {bone_name} {target_name}", e)
        return None


def add_limit_distance_constraint(from_rig, to_rig, from_bone, to_bone, distance, influence = 1.0, space="WORLD"):
    try:
        if utils.object_mode():
            to_pose_bone : bpy.types.PoseBone = to_rig.pose.bones[to_bone]
            c : bpy.types.LimitDistanceConstraint = to_pose_bone.constraints.new(type="LIMIT_DISTANCE")
            c.target = from_rig
            c.subtarget = from_bone
            c.distance = distance
            c.limit_mode = "LIMITDIST_ONSURFACE"
            c.target_space = space
            c.owner_space = space
            c.influence = influence
            return c
    except Exception as e:
        utils.log_error(f"Unable to add limit distance constraint: {to_bone} {from_bone}", e)
        return None


def add_child_of_constraint(parent_rig, child_rig, parent_bone, child_bone, influence = 1.0, space="WORLD"):
    try:
        if utils.object_mode():
            to_pose_bone : bpy.types.PoseBone = child_rig.pose.bones[child_bone]
            c : bpy.types.ChildOfConstraint = to_pose_bone.constraints.new(type="CHILD_OF")
            c.target = parent_rig
            c.subtarget = parent_bone
            c.target_space = space
            c.owner_space = space
            c.influence = influence
            return c
    except Exception as e:
        utils.log_error(f"Unable to add child of constraint: {child_bone} {parent_bone}", e)
        return None


def add_inverse_kinematic_constraint(from_rig, to_rig, from_bone, to_bone, influence = 1.0, space="WORLD",
                                     use_tail = True, use_stretch = True, use_rotation = True, use_location = True,
                                     weight = 1.0, orient_weight = 0.0, chain_count = 1):
    try:
        if utils.object_mode():
            to_pose_bone : bpy.types.PoseBone = to_rig.pose.bones[to_bone]
            c : bpy.types.KinematicConstraint = to_pose_bone.constraints.new(type="IK")
            c.target = from_rig
            c.subtarget = from_bone
            c.use_tail = use_tail
            c.use_stretch = use_stretch
            c.use_rotation = use_rotation
            c.use_location = use_location
            c.weight = weight
            c.chain_count = chain_count
            c.orient_weight = orient_weight
            c.target_space = space
            c.owner_space = space
            c.influence = influence
            return c
    except Exception as e:
        utils.log_error(f"Unable to add inverse kinematic constraint: {to_bone} {from_bone}", e)
        return None


def set_pose_bone_lock(pose_bone : bpy.types.PoseBone,
                       lock_ik = [0, 0, 0],
                       lock_location = [0, 0, 0],
                       lock_rotation = [0, 0, 0, 0],
                       lock_scale = [0, 0, 0],):

    for i, lock in enumerate(lock_location):
        pose_bone.lock_location[i] = lock > 0

    for i, lock in enumerate(lock_rotation):
        if i == 3:
            pose_bone.lock_rotation_w = lock > 0
        else:
            pose_bone.lock_rotation[i] = lock > 0

    pose_bone.lock_ik_x = lock_ik[0] > 0
    pose_bone.lock_ik_y = lock_ik[1] > 0
    pose_bone.lock_ik_z = lock_ik[2] > 0

    for i, lock in enumerate(lock_scale):
        pose_bone.lock_scale[i] = lock > 0


def set_edit_bone_flags(edit_bone, flags, deform):
    edit_bone.use_connect = True if "C" in flags else False
    edit_bone.use_local_location = True if "L" in flags else False
    edit_bone.use_inherit_rotation = True if "R" in flags else False
    edit_bone.use_deform = deform


def store_armature_settings(rig, include_pose=False):
    if not rig: return None
    collections = {}
    layers = []

    if utils.B400():
        for collection in rig.data.collections:
            collections[collection.name] = collection.is_visible
    else:
        for i in range(0, 32):
            layers.append(rig.data.layers[i])

    visibility = { "layers": layers,
                   "collections": collections,
                   "show_in_front": rig.show_in_front,
                   "display_type": rig.display_type,
                   "pose_position": rig.data.pose_position,
                   "action": utils.safe_get_action(rig),
                   "location": rig.location }

    if include_pose:
        pose_data = {}
        pose_bone: bpy.types.PoseBone
        for pose_bone in rig.pose.bones:
            pose_data[pose_bone.name] = [pose_bone.location, pose_bone.rotation_axis_angle, pose_bone.rotation_euler,
                                         pose_bone.rotation_quaternion, pose_bone.scale, pose_bone.rotation_mode]
        visibility["pose"] = pose_data

    return visibility


def restore_armature_settings(rig, visibility, include_pose=False):
    if not rig: return

    if utils.B400():
        collections = visibility["collections"]
        for collection in collections:
            rig.data.collections[collection].is_visible = collections[collection]
    else:
        layers = visibility["layers"]
        for i in range(0, 32):
            rig.data.layers[i] = layers[i]
    rig.show_in_front = visibility["show_in_front"]
    rig.display_type = visibility["display_type"]
    rig.data.pose_position = visibility["pose_position"]
    utils.safe_set_action(rig, visibility["action"])
    rig.location = visibility["location"]

    if include_pose:
        pose_data = visibility["pose"]
        for bone_name in pose_data:
            rig.pose.bones[bone_name].rotation_mode = pose_data[bone_name][5]
            rig.pose.bones[bone_name].location = pose_data[bone_name][0]
            rig.pose.bones[bone_name].rotation_axis_angle = pose_data[bone_name][1]
            rig.pose.bones[bone_name].rotation_euler = pose_data[bone_name][2]
            rig.pose.bones[bone_name].rotation_quaternion = pose_data[bone_name][3]
            rig.pose.bones[bone_name].scale = pose_data[bone_name][4]


def set_rig_bind_pose(rig):
    rig.data.pose_position = "POSE"
    utils.safe_set_action(rig, None)
    clear_pose(rig)


def copy_position(rig, bone, copy_bones, offset):
    if utils.edit_mode_to(rig):
        if bone in rig.data.edit_bones:
            edit_bone = rig.data.edit_bones[bone]
            head_position = mathutils.Vector((0,0,0))
            tail_position = mathutils.Vector((0,0,0))
            num = 0
            for copy_name in copy_bones:
                if copy_name in rig.data.edit_bones:
                    copy_bone = rig.data.edit_bones[copy_name]
                    dir = (copy_bone.tail - copy_bone.head).normalized()
                    head_position += copy_bone.head + dir * offset
                    tail_position += copy_bone.tail + dir * offset
                    num += 1
            head_position /= num
            tail_position /= num
            edit_bone.head = head_position
            edit_bone.tail = tail_position
            return edit_bone
        else:
            utils.log_error(f"Cannot find bone {bone} in rig!")
    return None


def is_bone_in_collections(rig, bone: bpy.types.Bone, collections=None, groups=None, layers=None):
    if utils.B400():
        if collections:
            for collection in collections:
                if collection in rig.data.collections:
                    if bone.name in rig.data.collections[collection].bones:
                        return True
    else:
        if groups:
            if bone.name in rig.pose.bones:
                pose_bone: bpy.types.PoseBone = rig.pose.bones[bone.name]
                if pose_bone.bone_group and pose_bone.bone_group.name in groups:
                    return True
        if layers:
            for layer in layers:
                if not bone.layers[layer]:
                    return False
            return True

    return False


def set_bone_collection(rig, bone, collection=None, group=None, layer=None, color=None):
    """Sets the bone collection (Any) (Blender 4.0+),
       or group (PoseBone only) or layer (Bone or EditBone) (< Blender 4.0)"""
    if utils.B400():
        if collection:
            if not collection in rig.data.collections:
                rig.data.collections.new(collection)
            bone_collection = rig.data.collections[collection]
            bone_collection.assign(bone)
        if color is not None:
            set_bone_color(bone, color)
    else:
        if group:
            if group not in rig.pose.bone_groups:
                rig.pose.bone_groups.new(name=group)
            group = rig.pose.bone_groups[group]
            if type(bone) is not bpy.types.PoseBone and bone.name in rig.pose.bones:
                pose_bone = rig.pose.bones[bone.name]
                pose_bone.bone_group = group
            elif type(bone) is bpy.types.PoseBone:
                bone.bone_group = group
        if layer:
            if type(bone) is bpy.types.PoseBone:
                bone = bone.bone
            bone.layers[layer] = True
            for i, l in enumerate(bone.layers):
                bone.layers[i] = i == layer

CUSTOM_COLORS = {
    "Active": (0.7686275243759155, 1.0, 1.0),
    "Select": (0.5960784554481506, 0.8980392813682556, 1.0),
    "IK": (0.8000000715255737, 0.0, 0.0),
    "FK": (0.3764706254005432, 0.7803922295570374, 0.20784315466880798),
    "SPECIAL": (0.9803922176361084, 0.9019608497619629, 0.2392157018184662),
    "SIM": (0.98, 0.24, 0.9),
    "TWEAK": (0.2196078598499298, 0.49803924560546875, 0.7843137979507446),
    "TWEAK_DISABLED": (0.270588, 0.396078, 0.521569),
    "ROOT": (0.6901960968971252, 0.46666669845581055, 0.6784313917160034),
    "DETAIL": (0.9843137860298157, 0.5372549295425415, 0.33725491166114807),
    "DEFAULT": (0.3764706254005432, 0.7803922295570374, 0.20784315466880798),
    "SKIN": (0.647059, 0.780392, 0.588235),
    "PIVOT": (0.9803922176361084, 0.9019608497619629, 0.2392157018184662),
    "MESH": (0.9803922176361084, 0.9019608497619629, 0.2392157018184662),
}

def set_bone_color(bone, color_code):
    if utils.B400():
        bone.color.palette = "CUSTOM"
        bone.color.custom.normal = CUSTOM_COLORS[color_code]
        bone.color.custom.active = CUSTOM_COLORS["Active"]
        bone.color.custom.select = CUSTOM_COLORS["Select"]


def set_bone_collection_visibility(rig, collection, layer, visible, only=False):
    if utils.B400():
        if only:
            for coll in rig.data.collections:
                coll.is_visible = False
        if collection in rig.data.collections:
            rig.data.collections[collection].is_visible = visible
    else:
        rig.data.layers[layer] = visible
        if only:
            for i in range(0, 32):
                if i != layer:
                    rig.data.layers[i] = not visible


def make_bones_visible(arm, protected=False, collections=None, layers=None):
    bone : bpy.types.Bone
    pose_bone : bpy.types.PoseBone
    for bone in arm.data.bones:
        pose_bone = get_pose_bone(arm, bone.name)
        # make all active bone layers visible so they can be unhidden and selectable
        if utils.B400():
            for collection in arm.data.collections:
                if collections:
                    collection.is_visible = collection.name in collections
                else:
                    collection.is_visible = True
                #if protected:
                #    collection.is_editable = True
        else:
            for i, l in enumerate(bone.layers):
                if l:
                    if layers:
                        arm.data.layers[i] = i in layers
                    else:
                        arm.data.layers[i] = True
                    if protected:
                        arm.data.layers_protected[i] = False
        # show and select bone
        bone.hide = False
        bone.hide_select = False

def is_bone_collection_visible(arm, collection=None, layer=None):
    if utils.B400():
        if collection in arm.data.collections:
            return arm.data.collections[collection].is_visible
        return False
    else:
        return arm.data.layers[layer]


def add_bone_collection(rig, collection):
    if collection not in rig.data.collections:
        rig.data.collections.new(collection)
    return rig.data.collections[collection]


def assign_rl_base_collections(rig):
    if utils.B400():
        if "Deform" not in rig.data.collections:
            deform = add_bone_collection(rig, "Deform")
            none = add_bone_collection(rig, "Non-Deform")
            twist = add_bone_collection(rig, "Twist")
            share = add_bone_collection(rig, "Share")

            none_deform_bones = [
                "CC_Base_R_Upperarm",
                "CC_Base_L_Upperarm",
                "CC_Base_R_Forearm",
                "CC_Base_L_Forearm",
                "CC_Base_R_Thigh",
                "CC_Base_L_Thigh",
                "CC_Base_R_Calf",
                "CC_Base_L_Calf",
                "CC_Base_FacialBone",
                "CC_Base_BoneRoot",
                "RL_BoneRoot",
            ]

            for bone in rig.data.bones:
                if "Twist" in bone.name:
                    twist.assign(bone)
                elif "ShareBone" in bone.name:
                    share.assign(bone)
                if bone.name in none_deform_bones:
                    none.assign(bone)
                else:
                    deform.assign(bone)


def get_distance_between(rig, bone_a_name, bone_b_name):
    if utils.edit_mode_to(rig):
        if bone_a_name in rig.data.edit_bones and bone_b_name in rig.data.edit_bones:
            bone_a = rig.data.edit_bones[bone_a_name]
            bone_b = rig.data.edit_bones[bone_b_name]
            delta : mathutils.Vector = bone_b.head - bone_a.head
            return delta.length
        else:
            utils.log_error(f"Could not find all bones: {bone_a_name} and {bone_b_name} in Rig!")
    else:
        utils.log_error(f"Unable to edit rig!")
    return 0


def generate_eye_widget(rig, bone_name, bones, distance, scale):
    wgt : bpy.types.Object = None
    if utils.object_mode():
        if len(bones) == 1:
            bpy.ops.mesh.primitive_circle_add(vertices=16, radius=1, rotation=[0,0,11.25])
            bpy.ops.object.transform_apply(rotation=True)
            wgt = utils.get_active_object()
        else:
            bpy.ops.mesh.primitive_circle_add(vertices=16, radius=1.35, rotation=[0,0,11.25])
            bpy.ops.object.transform_apply(rotation=True)
            wgt = utils.get_active_object()
            mesh : bpy.types.Mesh = wgt.data
            vert: bpy.types.MeshVertex
            for vert in mesh.vertices:
                if vert.co.x < -0.01:
                    vert.co.x -= 0.5 * distance / scale
                elif vert.co.x > 0.01:
                    vert.co.x += 0.5 * distance / scale
        if wgt:
            collection : bpy.types.Collection
            for collection in bpy.data.collections:
                if collection.name.startswith("WGTS_rig"):
                    collection.objects.link(wgt)
                elif wgt.name in collection.objects:
                    collection.objects.unlink(wgt)
            if bone_name in rig.pose.bones:
                pose_bone : bpy.types.PoseBone
                pose_bone = rig.pose.bones[bone_name]
                pose_bone.custom_shape = wgt
                wgt.name = "WGT-rig_" + bone_name
    return wgt


def make_widget_collection(collection_name) -> bpy.types.Collection:
    wgt_collection: bpy.types.Collection = None
    for collection in bpy.data.collections:
        if collection.name.startswith(collection_name):
            wgt_collection = collection
    if not wgt_collection:
        wgt_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(wgt_collection)
        wgt_collection.hide_render = True
        layer_collections = utils.get_view_layer_collections(search=collection_name)
        for collection in layer_collections:
            collection.exclude = True
            collection.hide_viewport = True
    return wgt_collection


def add_widget_to_collection(widget, collection_name=None, collection_suffix=None, remove_other=True):
    if collection_name:
        widget_collection = make_widget_collection(collection_name)
        if widget.name not in widget_collection.objects:
            widget_collection.objects.link(widget)
        for collection in bpy.data.collections:
            if remove_other and collection != widget_collection and widget.name in collection.objects:
                collection.objects.unlink(widget)
    if collection_suffix:
        for collection in bpy.data.collections:
            if collection.name.startswith(collection_suffix):
                collection.objects.link(widget)
            elif remove_other and widget.name in collection.objects:
                collection.objects.unlink(widget)


def make_sphere_widget(widget_name, size):
    if widget_name in bpy.data.objects:
        wgt = bpy.data.objects[widget_name]
    else:
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=size,
                                        rotation=[0,0,0], location=[0,0,0])
        wgt1 = utils.get_active_object()
        bpy.ops.object.transform_apply(rotation=True)
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=size,
                                        rotation=[1.570796,0,0], location=[0,0,0])
        wgt2 = utils.get_active_object()
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=size,
                                        rotation=[0,1.570796,0], location=[0,0,0])
        wgt3 = utils.get_active_object()
        bpy.ops.object.transform_apply(rotation=True)
        utils.try_select_objects([wgt1, wgt2, wgt3], True)
        utils.set_active_object(wgt1)
        bpy.ops.object.join()
        wgt = utils.get_active_object()
        wgt.name = widget_name
    return wgt


def make_circle_widget(widget_name, size):
    if widget_name in bpy.data.objects:
        wgt = bpy.data.objects[widget_name]
    else:
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=size,
                                        rotation=[0,0,0], location=[0,0,0])
        wgt = utils.get_active_object()
        wgt.name = widget_name
    return wgt


def make_root_widget(widget_name, size):
    if widget_name in bpy.data.objects:
        wgt = bpy.data.objects[widget_name]
    else:
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=size,
                                        rotation=[0,0,0], location=[0,0,0])
        wgt1 = utils.get_active_object()
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=size * 0.95,
                                        rotation=[0,0,0], location=[0,0,0])
        wgt2 = utils.get_active_object()
        mesh = bpy.data.meshes.new(widget_name)
        mesh.from_pydata([(-size, 0, 0), (size, 0, 0), (0, -size, 0), (0, size, 0)],
                            [(0, 1), (2,3)],
                            [])
        mesh.update()
        wgt3 = bpy.data.objects.new(widget_name, mesh)
        wgt3.location = [0,0,0]
        bpy.context.collection.objects.link(wgt3)
        utils.try_select_objects([wgt1, wgt2, wgt3], True)
        utils.set_active_object(wgt1)
        bpy.ops.object.join()
        wgt = utils.get_active_object()
        wgt.name = widget_name
    return wgt


def make_axes_widget(widget_name, size):
    if widget_name in bpy.data.objects:
        wgt = bpy.data.objects[widget_name]
    else:
        mesh = bpy.data.meshes.new(widget_name)
        mesh.from_pydata([(-size, 0, 0), (size, 0, 0), (0, -size, 0), (0, size, 0), (0, 0, -size), (0, 0, size)],
                            [(0, 1), (2,3), (4,5)],
                            [])
        mesh.update()
        wgt = bpy.data.objects.new(widget_name, mesh)
        wgt.location = [0,0,0]
        bpy.context.collection.objects.link(wgt)
        wgt.name = widget_name
    return wgt


def make_spindle_widget(widget_name, size):
    if widget_name in bpy.data.objects:
        wgt = bpy.data.objects[widget_name]
    else:
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=size,
                                            rotation=[1.570796,0,0], location=[0,size,0])
        bpy.ops.object.transform_apply(rotation=True)
        wgt1 = utils.get_active_object()
        mesh = bpy.data.meshes.new(widget_name)
        mesh.from_pydata([(0, 0, 0), (0, 1, 0)],
                            [(0, 1)],
                            [])
        mesh.update()
        wgt2 = bpy.data.objects.new(widget_name, mesh)
        wgt2.location = [0,0,0]
        bpy.context.collection.objects.link(wgt2)
        utils.try_select_objects([wgt1, wgt2], True)
        utils.set_active_object(wgt1)
        bpy.ops.object.join()
        wgt = utils.get_active_object()
        wgt.name = widget_name
    return wgt


def make_cone_spindle_widget(widget_name, size):
    if widget_name in bpy.data.objects:
        wgt = bpy.data.objects[widget_name]
    else:
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=size*0.25,
                                            rotation=[1.570796,0,0], location=[0,size*0.5,0])
        bpy.ops.object.transform_apply(rotation=True)
        wgt1 = utils.get_active_object()
        wgt2 = bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=size*0.125, radius2=0, depth=1,
                                               rotation=[-1.570796,0,0], location=[0,size*0.5,0])
        bpy.ops.object.transform_apply(rotation=True)
        wgt2 = utils.get_active_object()
        utils.try_select_objects([wgt1, wgt2], True)
        utils.set_active_object(wgt1)
        bpy.ops.object.join()
        wgt = utils.get_active_object()
        wgt.name = widget_name
    return wgt


def make_spike_widget(widget_name, size):
    if widget_name in bpy.data.objects:
        wgt = bpy.data.objects[widget_name]
    else:
        wgt1 = bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=size*0.125, radius2=0, depth=size*0.8,
                                               rotation=[-1.570796,0,0], location=[0,size*0.6,0])
        bpy.ops.object.transform_apply(rotation=True)
        wgt1 = utils.get_active_object()
        wgt2 = bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=size*0.125, radius2=0, depth=size*0.2,
                                               end_fill_type="NOTHING",
                                               rotation=[ 1.570796,0,0], location=[0,size*0.1,0])
        bpy.ops.object.transform_apply(rotation=True)
        wgt2 = utils.get_active_object()
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=size*0.25,
                                            rotation=[1.570796,0,0], location=[0,size*0.5,0])
        bpy.ops.object.transform_apply(rotation=True)
        wgt3 = utils.get_active_object()
        utils.try_select_objects([wgt1, wgt2, wgt3], True)
        utils.set_active_object(wgt1)
        bpy.ops.object.join()

        wgt = utils.get_active_object()
        wgt.name = widget_name
    return wgt


def make_limb_widget(widget_name, size):
    if widget_name in bpy.data.objects:
        wgt = bpy.data.objects[widget_name]
    else:
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=size*0.25,
                                            rotation=[1.570796,0,0], location=[0,size*0.5,0])
        bpy.ops.object.transform_apply(rotation=True)
        wgt1 = utils.get_active_object()
        mesh = bpy.data.meshes.new(widget_name)
        mesh.from_pydata([(0, 0, 0), (0, 1, 0)],
                            [(0, 1)],
                            [])
        mesh.update()
        wgt2 = bpy.data.objects.new(widget_name, mesh)
        wgt2.location = [0,0,0]
        bpy.context.collection.objects.link(wgt2)
        utils.try_select_objects([wgt1, wgt2], True)
        utils.set_active_object(wgt1)
        bpy.ops.object.join()
        wgt = utils.get_active_object()
        wgt.name = widget_name
    return wgt


def make_cone_widget(widget_name, size):
    if widget_name in bpy.data.objects:
        wgt = bpy.data.objects[widget_name]
    else:
        bpy.ops.mesh.primitive_circle_add(vertices=32, radius=size,
                                            rotation=[1.570796,0,0], location=[0,0,0])
        bpy.ops.object.transform_apply(rotation=True)
        wgt1 = utils.get_active_object()
        mesh = bpy.data.meshes.new(widget_name)
        mesh.from_pydata([(0, size*2, 0), (0, 0, size), (size, 0, 0), (-size, 0, 0), (0, 0, -size)],
                            [(0, 1), (0, 2), (0, 3), (0, 4)],
                            [])
        mesh.update()
        wgt2 = bpy.data.objects.new(widget_name, mesh)
        wgt2.location = [0,0,0]
        bpy.context.collection.objects.link(wgt2)
        utils.try_select_objects([wgt1, wgt2], True)
        utils.set_active_object(wgt1)
        bpy.ops.object.join()
        wgt = utils.get_active_object()
        wgt.name = widget_name
    return wgt


def make_dbl_circle_widget(widget_name, size):
    if widget_name in bpy.data.objects:
        wgt = bpy.data.objects[widget_name]
    else:
        bpy.ops.mesh.primitive_circle_add(vertices=64, radius=size,
                                            rotation=[1.570796,0,0], location=[0,0,0])
        bpy.ops.object.transform_apply(rotation=True)
        wgt1 = utils.get_active_object()
        bpy.ops.mesh.primitive_circle_add(vertices=64, radius=size * 1.025,
                                        rotation=[1.570796,0,0], location=[0,0,0])
        bpy.ops.object.transform_apply(rotation=True)
        wgt2 = utils.get_active_object()
        utils.try_select_objects([wgt1, wgt2], True)
        utils.set_active_object(wgt1)
        bpy.ops.object.join()
        wgt = utils.get_active_object()
        wgt.name = widget_name
    return wgt


def generate_spring_widget(rig, name, type, size):
    wgt : bpy.types.Object = None
    wgt_name = "WGT-rig_" + name
    if wgt_name in bpy.data.objects:
        return bpy.data.objects[wgt_name]

    if utils.object_mode():

        if type == "FK":
            wgt = make_spindle_widget(wgt_name, size)

        if type == "IK":
            wgt = make_cone_widget(wgt_name, size)

        if type == "GRP":
            wgt = make_dbl_circle_widget(wgt_name, size)

        if type == "TWK":
            wgt = make_sphere_widget(wgt_name, size)

        if wgt:
            add_widget_to_collection(wgt, collection_suffix="WGTS_rig")

    return wgt


def add_pose_bone_custom_property(rig, pose_bone_name, prop_name, prop_value):
    if utils.object_mode():
        if pose_bone_name in rig.pose.bones:
            pose_bone = rig.pose.bones[pose_bone_name]
            rna_idprop_ui_create(pose_bone, prop_name, default=prop_value, overridable=True, min=0, max=1)


def add_constraint_scripted_influence_driver(rig, pose_bone_name, data_path, variable_name, constraint = None, constraint_type = "", expression = ""):
    if utils.object_mode():
        if pose_bone_name in rig.pose.bones:
            pose_bone = rig.pose.bones[pose_bone_name]
            cons = []
            if constraint:
                cons.append(constraint)
            elif constraint_type:
                for con in pose_bone.constraints:
                    if con.type == constraint_type:
                        cons.append(con)
            for con in cons:
                if expression:
                    driver = drivers.make_driver(con, "influence", "SCRIPTED", expression)
                else:
                    driver = drivers.make_driver(con, "influence", "SUM")
                if driver:
                    var = drivers.make_driver_var(driver, "SINGLE_PROP", variable_name, rig, target_type = "OBJECT", data_path = data_path)


def get_data_path_pose_bone_property(pose_bone_name, variable_name):
    data_path = f"pose.bones[\"{pose_bone_name}\"][\"{variable_name}\"]"
    return data_path


def get_data_rigify_limb_property(limb_id, variable_name):
    """
    limb_id = "LEFT_LEFT", "RIGHT_LEFT", "LEFT_ARM", "RIGHT_ARM", "TORSO", "JAW", "EYES"\n
    variable_name = "IK_Stretch", "IK_FK", "neck_follow", "head_follow", "mouth_lock", "eyes_follow"
    """
    if limb_id == "LEFT_LEG":
        return get_data_path_pose_bone_property("thigh_parent.L", variable_name)
    elif limb_id == "RIGHT_LEFT":
        return get_data_path_pose_bone_property("thigh_parent.R", variable_name)
    elif limb_id == "LEFT_ARM":
        return get_data_path_pose_bone_property("upper_arm_parent.L", variable_name)
    elif limb_id == "RIGHT_ARM":
        return get_data_path_pose_bone_property("upper_arm_parent.R", variable_name)
    elif limb_id == "TORSO":
        return get_data_path_pose_bone_property("torso", variable_name)
    elif limb_id == "JAW":
        return get_data_path_pose_bone_property("jaw_master", variable_name)
    elif limb_id == "EYES":
        return get_data_path_pose_bone_property("eyes", variable_name)
    return ""


def add_bone_prop_driver(rig, pose_bone_name, bone_data_path, bone_data_index, props, prop_name, variable_name):
    if utils.object_mode():
        pose_bone : bpy.types.PoseBone
        if pose_bone_name in rig.pose.bones:
            pose_bone = rig.pose.bones[pose_bone_name]
            fcurve : bpy.types.FCurve
            fcurve = pose_bone.driver_add(bone_data_path, bone_data_index)
            driver : bpy.types.Driver = fcurve.driver
            driver.type = "SUM"
            var : bpy.types.DriverVariable = driver.variables.new()
            var.name = variable_name
            var.type = "SINGLE_PROP"
            var.targets[0].id_type = "SCENE"
            var.targets[0].id = props.id_data
            var.targets[0].data_path = props.path_from_id(prop_name)


def clear_constraints(rig, pose_bone_name):
    if pose_bone_name:
        if utils.object_mode():
            if pose_bone_name in rig.pose.bones:
                pose_bone = rig.pose.bones[pose_bone_name]
                constraints = []
                for con in pose_bone.constraints:
                    constraints.append(con)
                for con in constraints:
                    pose_bone.constraints.remove(con)


def find_constraint(pose_bone: bpy.types.PoseBone, of_type, with_subtarget=None) -> bpy.types.Constraint:
    if pose_bone:
        con: bpy.types.Constraint
        for con in pose_bone.constraints:
            if con.type == of_type:
                if with_subtarget and hasattr(con, "subtarget"):
                    if con.subtarget != with_subtarget:
                        continue
                return con
    return None

def clear_drivers(rig):
    # rig object drivers (pose bone drivers)
    drivers = rig.animation_data.drivers
    if drivers:
        fcurves = []
        for fc in drivers:
            fcurves.append(fc)
        for fc in fcurves:
            drivers.remove(fc)

    # rig armature drivers (bone drivers)
    drivers = rig.data.animation_data.drivers
    if drivers:
        fcurves = []
        for fc in drivers:
            fcurves.append(fc)
        for fc in fcurves:
            drivers.remove(fc)


def select_all_bones(arm, select = True, clear_active = True):
    mode = utils.get_mode()
    data = arm.data.bones
    if mode == "EDIT":
        data = arm.data.edit_bones
    if data:
        for bone in data:
            bone.select_head = select
            bone.select_tail = select
            bone.select = select
        if clear_active:
            data.active = None
        return True
    else:
        return False


def set_active_bone(arm, bone_name, deselect_all = True):
    if deselect_all:
        select_all_bones(arm, select=False, clear_active=True)
    mode = utils.get_mode()
    data = arm.data.bones
    if mode == "EDIT":
        data = arm.data.edit_bones
    if bone_name in data:
        bone = data[bone_name]
        bone.select_head = True
        bone.select_tail = True
        bone.select = True
        data.active = bone
        return True
    else:
        return False


def get_bone_name_from_data_path(data_path : str):
    if data_path.startswith("pose.bones[\""):
        start = data_path.find('"', 0) + 1
        end = data_path.find('"', start)
        return data_path[start:end]
    return None


def get_roll(bone):
    mat = bone.matrix_local.to_3x3()
    quat = mat.to_quaternion()
    if abs(quat.w) < 1e-4:
        roll = pi
    else:
        roll = 2*atan(quat.y/quat.w)
    return roll


def clear_pose(arm):
    """Clears the pose, makes all bones visible and clears the bone selections."""

    # select all bones in pose mode
    arm.data.pose_position = "POSE"
    utils.pose_mode_to(arm)
    bone : bpy.types.Bone
    make_bones_visible(arm)
    for bone in arm.data.bones:
        # show and select bone
        bone.hide = False
        bone.hide_select = False
        bone.select = True
        bone.select_head = True
        bone.select_tail = True

    # unlock the bones
    pose_bone : bpy.types.PoseBone
    for pose_bone in arm.pose.bones:
        pose_bone.lock_location = [False, False, False]
        pose_bone.lock_rotation = [False, False, False]
        pose_bone.lock_rotation_w = False
        pose_bone.lock_scale = [False, False, False]

    # clear pose
    bpy.ops.pose.transforms_clear()

    # clear bone selections
    for bone in arm.data.bones:
        bone.select = False
        bone.select_head = False
        bone.select_tail = False

    utils.object_mode_to(arm)


def reset_root_bone(arm):
    if utils.edit_mode_to(arm):
        root_bone = arm.data.edit_bones[0]
        if "root" in root_bone.name.lower():
            head = root_bone.head
            length = root_bone.length
            tail = head + mathutils.Vector((0,-1,0)) * length
            root_bone.tail = tail
            root_bone.align_roll(mathutils.Vector((0,0,1)))
    utils.object_mode()


def bone_mapping_contains_bone(bone_mapping, bone_name):
    for bone_mapping in bone_mapping:
            if cmp_rl_bone_names(bone_mapping[1], bone_name):
                return True
    return False


def get_accessory_root_bone(bone_mapping, bone):
    root = None
    if not bone_mapping_contains_bone(bone_mapping, bone.name):
        while bone.parent:
            if not bone_mapping_contains_bone(bone_mapping, bone.parent.name):
                root = bone.parent
            bone = bone.parent
    return root


def bone_parent_in_list(bone_list, bone):
    if bone:
        while bone.parent:
            if bone.parent.name in bone_list:
                return True
            bone = bone.parent
    return False


def find_accessory_bones(bone_mapping, cc3_rig):
    accessory_bones = []
    for bone in cc3_rig.data.bones:
        bone_name = bone.name
        if not bone_mapping_contains_bone(bone_mapping, bone_name):
            if bone_name not in accessory_bones and not bone_parent_in_list(accessory_bones, bone):
                utils.log_info(f"Accessory Bone: {bone_name}")
                accessory_bones.append(bone_name)
    return accessory_bones