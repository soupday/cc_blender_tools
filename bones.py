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

import bpy
import mathutils
from . import utils
from rna_prop_ui import rna_idprop_ui_create


def get_rl_edit_bone(rig, name):
    if name in rig.data.edit_bones:
        return rig.data.edit_bones[name]
    # remove "CC_Base_" from start of bone name and try again...
    name = name[8:]
    if name in rig.data.edit_bones:
        return rig.data.edit_bones[name]
    return None


def get_rl_bone(rig, name):
    if name in rig.data.bones:
        return rig.data.bones[name]
    # remove "CC_Base_" from start of bone name and try again...
    name = name[8:]
    if name in rig.data.bones:
        return rig.data.bones[name]
    return None


def get_rl_pose_bone(rig, name):
    if name in rig.pose.bones:
        return rig.pose.bones[name]
    # remove "CC_Base_" from start of bone name and try again...
    name = name[8:]
    if name in rig.pose.bones:
        return rig.pose.bones[name]
    return None


def get_edit_bone(rig, name):
    if name in rig.data.edit_bones:
        return rig.data.edit_bones[name]
    return None


def get_bone(rig, name):
    if name in rig.data.bones:
        return rig.data.bones[name]
    return None


def get_pose_bone(rig, name):
    if name in rig.pose.bones:
        return rig.pose.bones[name]
    return None


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


def new_edit_bone(rig, bone_name, parent_name):
    if utils.edit_mode_to(rig):
        if bone_name not in rig.data.edit_bones:
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
            head_pos = cc3_rig.matrix_world @ src_bone.head
            tail_pos = cc3_rig.matrix_world @ src_bone.tail
            roll = src_bone.roll
            if utils.edit_mode_to(dst_rig):
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


def add_copy_transforms_constraint(rig, to_bone, from_bone):
    try:
        if utils.set_mode("OBJECT"):
            to_pose_bone : bpy.types.PoseBone = rig.pose.bones[to_bone]
            c : bpy.types.CopyTransformsConstraint = to_pose_bone.constraints.new(type="COPY_TRANSFORMS")
            c.target = rig
            c.subtarget = from_bone
            c.head_tail = 0
            c.mix_mode = "REPLACE"
            c.target_space = "WORLD"
            c.owner_space = "WORLD"
            c.influence = 1.0
    except:
        utils.log_error(f"Unable to add copy transforms constraint: {to_bone} {from_bone}")


def add_damped_track_constraint(rig, bone_name, target_name):
    try:
        if utils.set_mode("OBJECT"):
            pose_bone : bpy.types.PoseBone = rig.pose.bones[bone_name]
            c : bpy.types.DampedTrackConstraint = pose_bone.constraints.new(type="DAMPED_TRACK")
            c.target = rig
            c.subtarget = target_name
            c.head_tail = 0
            c.track_axis = "Y"
            c.influence = 1.0
    except:
        utils.log_error(f"Unable to add damped track constraint: {bone_name} {target_name}")


def set_edit_bone_flags(edit_bone, flags, deform):
    edit_bone.use_connect = True if "C" in flags else False
    edit_bone.use_local_location = True if "L" in flags else False
    edit_bone.use_inherit_rotation = True if "R" in flags else False
    edit_bone.use_deform = deform


def set_bone_layer(rig, bone_name, layer):
    if utils.edit_mode_to(rig):
        edit_bone = rig.data.edit_bones[bone_name]
        for l in range(0, 32):
            edit_bone.layers[l] = l == layer
    if utils.set_mode("OBJECT"):
        pose_bone = rig.data.bones[bone_name]
        for l in range(0, 32):
            pose_bone.layers[l] = l == layer



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


def set_bone_group(rig, bone, group):
    if utils.set_mode("OBJECT"):
        if bone in rig.pose.bones:
            bone_group = rig.pose.bone_groups[group]
            rig.pose.bones[bone].bone_group = bone_group
            return True
        else:
            utils.log_error(f"Cannot find pose bone {bone} in rig!")
    else:
        utils.log_error("Unable to edit rig!")


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
    if utils.set_mode("OBJECT"):
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
    return wgt


def add_pose_bone_custom_property(rig, pose_bone_name, prop_name, prop_value):
    if utils.set_mode("OBJECT"):
        if pose_bone_name in rig.pose.bones:
            pose_bone = rig.pose.bones[pose_bone_name]
            rna_idprop_ui_create(pose_bone, prop_name, default=prop_value, overridable=True, min=0, max=1)


def add_constraint_influence_driver(rig, pose_bone_name, target_pose_bone_name, variable_name, constraint_type):
    if utils.set_mode("OBJECT"):
        if pose_bone_name in rig.pose.bones:
            pose_bone = rig.pose.bones[pose_bone_name]
            constraint = None
            for con in pose_bone.constraints:
                if con.type == constraint_type:
                    constraint = con
                    fcurve = constraint.driver_add("influence")
                    driver : bpy.types.Driver = fcurve.driver
                    driver.type = "SUM"
                    var : bpy.types.DriverVariable = driver.variables.new()
                    var.name = variable_name
                    var.type = "SINGLE_PROP"
                    var.targets[0].id = rig.id_data
                    var.targets[0].data_path = f"pose.bones[\"{target_pose_bone_name}\"][\"{variable_name}\"]"

