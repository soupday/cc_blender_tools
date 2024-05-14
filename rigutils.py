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
from . import bones, modifiers, rigify_mapping_data, utils


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
            mod: bpy.types.ArmatureModifier = modifiers.get_object_modifier(obj, "ARMATURE")
            if mod:
                # apply armature modifier with preserve settings and mod order
                modifiers.apply_modifier(obj, modifier=mod, preserving=True)
                modifiers.get_armature_modifier(obj, create=True, armature=rig)
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


def copy_rest_pose(src_rig, dst_rig):
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

        utils.set_mode("OBJECT")

        # restore view layers
        utils.restore_limited_view_layers(tmp_collection, layer_collections, to_hide)

    # return the baked action
    return baked_action


def bake_rig_action_from_source(src_rig, dst_rig):
    temp_collection = utils.force_visible_in_scene("TMP_Bake_Retarget", src_rig, dst_rig)

    rig_settings = bones.store_armature_settings(dst_rig)

    # constrain the destination rig rest pose to the source rig pose
    constraints = constrain_pose_rigs(src_rig, dst_rig)

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


def update_prop_rig(rig):
    link_props = bpy.context.scene.CCICLinkProps

    if not rig: return

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
            bone.hide = link_props.hide_prop_bones
        elif mesh_bone:
            bone.hide = True
        elif rigid_bone:
            bone.hide = False
        elif dummy_bone:
            bone.hide = True
        elif node_bone:
            bone.hide = link_props.hide_prop_bones

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
        if B.children:
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


def custom_prop_rig(rig):
    link_props = bpy.context.scene.CCICLinkProps

    if not rig: return
    wgt_pivot = bones.make_axes_widget("WGT-datalink_pivot", 1)
    wgt_mesh = bones.make_cone_widget("WGT-datalink_mesh", 1)
    wgt_default = bones.make_sphere_widget("WGT-datalink_default", 1)
    wgt_root = bones.make_root_widget("WGT-datalink_root", 2.5)
    wgt_skin = bones.make_limb_widget("WGT-datalink_skin", 1)
    bones.add_widget_to_collection(wgt_pivot, "WGTS_Datalink")
    bones.add_widget_to_collection(wgt_mesh, "WGTS_Datalink")
    bones.add_widget_to_collection(wgt_default, "WGTS_Datalink")
    bones.add_widget_to_collection(wgt_root, "WGTS_Datalink")
    bones.add_widget_to_collection(wgt_skin, "WGTS_Datalink")
    rig.show_in_front = True #not is_skinned_rig(rig)
    rig.data.display_type = 'WIRE'

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
                    pose_bone.custom_shape = wgt_root
                    pose_bone.custom_shape_scale_xyz = Vector((20,20,20))
                else:
                    pose_bone.custom_shape = wgt_default
                    pose_bone.custom_shape_scale_xyz = Vector((15,15,15))
                bone.hide = False
                pose_bone.use_custom_shape_bone_size = False
                bones.set_bone_color(pose_bone, "ROOT")
            elif pivot_bone:
                pose_bone.custom_shape = wgt_pivot
                bone.hide = True
                pose_bone.use_custom_shape_bone_size = False
                pose_bone.custom_shape_scale_xyz = Vector((10,10,10))
                bones.set_bone_color(pose_bone, "SPECIAL")
            elif skin_bone:
                pose_bone.custom_shape = wgt_skin
                bone.hide = False
                bone.hide = link_props.hide_prop_bones
                pose_bone.use_custom_shape_bone_size = True
                pose_bone.custom_shape_rotation_euler = skin_bone_orientation
                bones.set_bone_color(pose_bone, "FK")
            elif mesh_bone:
                pose_bone.custom_shape = wgt_mesh
                bone.hide = True
                pose_bone.use_custom_shape_bone_size = False
                pose_bone.custom_shape_scale_xyz = Vector((10,10,10))
                bones.set_bone_color(pose_bone, "SPECIAL")
            elif rigid_bone:
                pose_bone.custom_shape = wgt_default
                bone.hide = False
                pose_bone.use_custom_shape_bone_size = False
                pose_bone.custom_shape_scale_xyz = Vector((10,10,10))
                bones.set_bone_color(pose_bone, "TWEAK")
            elif dummy_bone:
                pose_bone.custom_shape = wgt_pivot
                bone.hide = True
                pose_bone.use_custom_shape_bone_size = False
                pose_bone.custom_shape_scale_xyz = Vector((10,10,10))
                bones.set_bone_color(pose_bone, "IK")
            elif node_bone:
                pose_bone.custom_shape = wgt_default
                bone.hide = link_props.hide_prop_bones
                pose_bone.use_custom_shape_bone_size = False
                pose_bone.custom_shape_scale_xyz = Vector((10,10,10))
                bones.set_bone_color(pose_bone, "SPECIAL")


def de_pivot(chr_cache):
    """Removes the pivot bones and corrects the parenting of the mesh objects
       from a CC/iC character or prop"""

    if chr_cache:
        rig = chr_cache.get_armature()
        objects = chr_cache.get_all_objects(include_armature=False, of_type="MESH")

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