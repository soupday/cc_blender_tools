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

from random import random
import bpy
import addon_utils
import math
import re
from . import utils, vars
from . import geom
from . import meshutils
from . import properties
from . import modifiers
from . import springbones, rigidbody
from . import physics
from . import drivers, bones
from . import rigutils
from . import rigify_mapping_data
from mathutils import Vector, Matrix, Quaternion

BONEMAP_METARIG_NAME = 0 # metarig bone name or rigify rig basename
BONEMAP_CC_HEAD = 1      # CC rig source bone and (head) postion of head bone
BONEMAP_CC_TAIL = 2      # CC rig bone (head) position of tail
BONEMAP_LERP_FROM = 3    # how far from cc_head to cc_tail to place the metarig bone head (optional)
BONEMAP_LERP_TO = 4      # how far from cc_head to cc_tail to place the metarig bone tail (optional)
BONEMAP_ALT_NAMES = 5    # index of alternative bones to map if CC_HEAD is missing from source (i.e. missing fingers) (optional)


class BoundingBox:
    box_min = [ float('inf'), float('inf'), float('inf')]
    box_max = [-float('inf'),-float('inf'),-float('inf')]

    def __init__(self):
        for i in range(0,3):
            self.box_min[i] =  float('inf')
            self.box_max[i] = -float('inf')

    def add(self, coord):
        for i in range(0,3):
            if coord[i] < self.box_min[i]:
                self.box_min[i] = coord[i]
            if coord[i] > self.box_max[i]:
                self.box_max[i] = coord[i]

    def pad(self, padding):
        for i in range(0,3):
            self.box_min[i] -= padding
            self.box_max[i] += padding

    def relative(self, coord):
        r = [0,0,0]
        for i in range(0,3):
            r[i] = (coord[i] - self.box_min[i]) / (self.box_max[i] - self.box_min[i])
        return r

    def coord(self, relative):
        c = [0,0,0]
        for i in range(0,3):
            c[i] = relative[i] * (self.box_max[i] - self.box_min[i]) + self.box_min[i]
        return c

    def debug(self):
        utils.log_always("BOX:")
        utils.log_always("Min:", self.box_min)
        utils.log_always("Max:", self.box_max)


def prune_meta_rig(meta_rig):
    """Removes some meta rig bones that have no corresponding match in the CC3 rig.
       (And are safe to remove)
    """

    if rigutils.edit_rig(meta_rig):
        pelvis_r = bones.get_edit_bone(meta_rig, "pelvis.R")
        pelvis_l = bones.get_edit_bone(meta_rig, "pelvis.L")
        if pelvis_r and pelvis_l:
            meta_rig.data.edit_bones.remove(pelvis_r)
            pelvis_l.name = "pelvis"


def fix_rigify_bones(chr_cache, rigify_rig):
    # align roll to +Z on
    BONES = {
        "ORG-eye.R": "+Z",
        "MCH-eye.R": "+Z",
        "ORG-eye.R": "+Z",
        "MCH-eye.R": "+Z",
        "ORG-eye.L": "+Z",
        "MCH-eye.L": "+Z",
        "ORG-eye.L": "+Z",
        "MCH-eye.L": "+Z",
        "jaw_master": "-Z",
        "MCH-mouth_lockg": "-Z",
        "MCH-jaw_master": "-Z",
        "MCH-jaw_master.001": "-Z",
        "MCH-jaw_master.002": "-Z",
        "MCH-jaw_master.003": "-Z",
    }

    if rigutils.edit_rig(rigify_rig):
        ZUP = Vector((0,0,1))
        ZDOWN = Vector((0,0,-1))
        for bone_name in BONES:
            bone_dir = BONES[bone_name]
            edit_bone = bones.get_edit_bone(rigify_rig, bone_name)
            if edit_bone:
                if bone_dir == "+Z":
                    edit_bone.align_roll(ZUP)
                elif bone_dir == "-Z":
                    edit_bone.align_roll(ZDOWN)


def add_def_bones(chr_cache, cc3_rig, rigify_rig):
    """Adds and parents twist deformation bones to the rigify deformation bones.
       Twist bones are parented to their corresponding limb bones.
       The main limb bones are not vertex weighted in the meshes but the twist bones are,
       so it's important the twist bones move (and stretch) with the parent limb.

       Also adds some missing toe bones and finger bones.
       (See: ADD_DEF_BONES array)
    """

    utils.log_info("Adding addition control bones to Rigify Control Rig:")
    utils.log_indent()

    for def_copy in rigify_mapping_data.ADD_DEF_BONES:
        src_bone_name = def_copy[0]
        dst_bone_name = def_copy[1]
        dst_bone_parent_name = def_copy[2]
        relation_flags = def_copy[3]
        layer = def_copy[4]
        collection = def_copy[5]
        deform = dst_bone_name[:3] == "DEF"
        scale = 1
        ref = None
        arg = None
        if len(def_copy) > 6:
            scale = def_copy[6]
        if len(def_copy) > 7:
            ref = def_copy[7]
        if len(def_copy) > 8:
            arg = def_copy[8]

        utils.log_info(f"Adding/Processing: {dst_bone_name}")

        # reparent an existing deformation bone
        if src_bone_name == "-":
            reparented_bone = bones.reparent_edit_bone(rigify_rig, dst_bone_name, dst_bone_parent_name)
            if reparented_bone and relation_flags:
                bones.set_edit_bone_flags(reparented_bone, relation_flags, deform)
                bones.set_bone_collection(rigify_rig, reparented_bone, collection, None, layer)

        # add a custom DEF, ORG or MCH bone
        elif src_bone_name[:3] == "DEF" or src_bone_name[:3] == "ORG" or src_bone_name[:3] == "MCH":
            new_bone = bones.copy_edit_bone(rigify_rig, src_bone_name, dst_bone_name, dst_bone_parent_name, scale)
            if new_bone:
                bones.set_edit_bone_flags(new_bone, relation_flags, deform)
                bones.set_bone_collection(rigify_rig, new_bone, collection, None, layer)
            # partial rotation copy for share bones
            if ref and arg is not None:
                bones.add_copy_rotation_constraint(rigify_rig, rigify_rig, ref, dst_bone_name, arg)

        # or make a copy of a bone from the original character rig
        else:
            new_bone = bones.copy_rl_edit_bone(cc3_rig, rigify_rig, src_bone_name, dst_bone_name, dst_bone_parent_name, scale)
            if new_bone:
                bones.set_edit_bone_flags(new_bone, relation_flags, deform)
                bones.set_bone_collection(rigify_rig, new_bone, collection, None, layer)

    utils.log_recess()


def add_extension_bones(chr_cache, cc3_rig, rigify_rig, bone_mapping, vertex_group_map):
    # find all the accessories in the armature
    accessory_bone_names = bones.find_accessory_bones(bone_mapping, cc3_rig)
    spring_rig_names = springbones.get_spring_rig_names(chr_cache, cc3_rig)

    # copy the accessory bone trees into the rigify rig
    for bone_name in accessory_bone_names:
        bone = cc3_rig.data.bones[bone_name]
        is_spring_rig = bone_name in spring_rig_names

        # fix old spring rig bone name
        if is_spring_rig and bone_name.startswith("RL_"):
            bone.name = "RLS_" + bone_name[3:]
            bone_name = bone.name
            utils.log_info(f"Updating spring rig name to {bone_name}")

        if is_spring_rig:
            prefix = "RLS_"
        else:
            prefix = "RLA_"

        if bone:
            if is_spring_rig:
                utils.log_info(f"Processing Spring Rig root bone: {bone_name}")
            else:
                utils.log_info(f"Processing Accessory root bone: {bone_name}")

            cc3_parent_name = None
            rigify_parent_name = None

            if bone.parent:
                cc3_parent_name = bone.parent.name
                rigify_parent_name = bones.get_rigify_meta_bone(rigify_rig, bone_mapping, cc3_parent_name)

            if not (rigify_parent_name and rigify_parent_name in rigify_rig.data.bones):
                utils.log_error(f"Unable to find matching accessory/spring bone tree parent: {cc3_parent_name} in rigify bones!")

            if is_spring_rig:
                utils.log_info(f"Copying Spring Rig bone tree into rigify rig: {bone.name} parent: {rigify_parent_name}")
            else:
                utils.log_info(f"Copying Accessory bone tree into rigify rig: {bone.name} parent: {rigify_parent_name}")

            if bone.name.startswith(prefix):
                dst_name = bone.name
            else:
                dst_name = f"{prefix}{bone.name}"

            bones.copy_rl_edit_bone_subtree(cc3_rig, rigify_rig, bone.name,
                                            dst_name, rigify_parent_name, "DEF-",
                                            "DEF", vars.DEF_BONE_LAYER, vertex_group_map)


def lookup_bone_def_parent(bone_defs, def_bone):
    if def_bone.parent:
        def_bone_parent_name = def_bone.parent.name
        for bone_def in bone_defs:
            if bone_def[4] == def_bone_parent_name:
                return bone_def
    return None


def lookup_bone_def_child(bone_defs, def_bone):
    if def_bone.children:
        def_bone_child_name = def_bone.children[0].name
        for bone_def in bone_defs:
            if bone_def[4] == def_bone_child_name:
                return bone_def
    return None


def rigify_spring_chain(rig, spring_root, length, def_bone, bone_defs, ik_targets, mch_root = None):

    length += 1

    base_name = def_bone.name
    if base_name.startswith("DEF-"):
        base_name = base_name[4:]

    if mch_root is None:
        mch_root = bones.copy_edit_bone(rig, def_bone.name, f"MCH-{base_name}_parent", spring_root.name, 1.0)
        bones.set_bone_collection(rig, mch_root, "MCH", None, vars.MCH_BONE_LAYER)
        mch_root.parent = spring_root

    parent_def = lookup_bone_def_parent(bone_defs, def_bone)
    if not parent_def:
        parent_def = [mch_root.name, mch_root.name, mch_root.name, "", "", spring_root.name, 0]

    fk_bone = bones.copy_edit_bone(rig, def_bone.name, f"{base_name}_fk", parent_def[0], 1.0)
    mch_bone = bones.copy_edit_bone(rig, def_bone.name, f"MCH-{base_name}_ik", parent_def[1], 1.0)
    org_bone = bones.copy_edit_bone(rig, def_bone.name, f"ORG-{base_name}", parent_def[2], 1.0)
    twk_bone = bones.copy_edit_bone(rig, def_bone.name, f"{base_name}_tweak", org_bone.name, 1.0)
    sim_bone = bones.copy_edit_bone(rig, def_bone.name, f"SIM-{base_name}", parent_def[5], 1.0)
    if not def_bone.name.startswith("DEF-"):
        def_bone.name = f"DEF-{def_bone.name}"
    bone_def = [fk_bone.name, mch_bone.name, org_bone.name, twk_bone.name, def_bone.name, sim_bone.name, length]
    bones.set_bone_collection(rig, fk_bone, "Spring (FK)", None, vars.SPRING_FK_LAYER, color="FK")
    bones.set_bone_collection(rig, mch_bone, "MCH", None, vars.MCH_BONE_LAYER)
    bones.set_bone_collection(rig, org_bone, "ORG", None, vars.ORG_BONE_LAYER)
    bones.set_bone_collection(rig, twk_bone, "Spring (Tweak)", None, vars.SPRING_TWEAK_LAYER, color="TWEAK")
    bones.set_bone_collection(rig, def_bone, "DEF", None, vars.DEF_BONE_LAYER)
    bones.set_bone_collection(rig, sim_bone, "Simulation", None, vars.SIM_BONE_LAYER, color="SIM")
    fk_bone.use_connect = True if length > 1 else False
    mch_bone.use_connect = True if length > 1 else False
    bone_defs.append(bone_def)

    for child_def_bone in def_bone.children:
        rigify_spring_chain(rig, spring_root, length, child_def_bone, bone_defs, ik_targets, mch_root = mch_root)

    if len(def_bone.children) == 0 and length > 0:
        ik_target_name = mch_root.name[4:-7]
        ik_target_bone = bones.new_edit_bone(rig, f"{ik_target_name}_target_ik", mch_bone.name)
        ik_target_bone.head = def_bone.tail
        ik_target_bone.tail = def_bone.tail + 0.5 * (def_bone.tail - def_bone.head)
        ik_target_bone.roll = def_bone.roll
        ik_target_bone.parent = mch_root
        ik_targets.append([mch_bone.name, ik_target_bone.name, length])

    return mch_root.name


def process_spring_groups(rig, spring_rig, ik_groups):
    scale = 1.0

    if rigutils.edit_rig(rig):
        for group_name in ik_groups:
            ik_names = ik_groups[group_name]["targets"]
            if len(ik_names) > 1:
                pos_head = Vector((0,0,0))
                pos_tail = Vector((0,0,0))
                for ik_bone_name in ik_names:
                    ik_bone = rig.data.edit_bones[ik_bone_name]
                    pos_head += ik_bone.head
                    pos_tail += ik_bone.tail
                pos_head /= len(ik_names)
                pos_tail /= len(ik_names)

                radius = 0
                for ik_bone_name in ik_names:
                    ik_bone = rig.data.edit_bones[ik_bone_name]
                    r = (ik_bone.head - pos_head).length
                    if r > radius:
                        radius = r

                radius = max(0.05, r)

                group_ik_bone = bones.new_edit_bone(rig, f"{group_name}_group_ik", spring_rig.name)
                group_ik_bone.head = pos_head
                bones.set_bone_collection(rig, group_ik_bone, "Spring (IK)", None, vars.SPRING_IK_LAYER, color="IK")
                dir = pos_tail - pos_head
                dir[0] = 0
                group_ik_bone.tail = pos_head + dir
                ik_groups[group_name]["control"] = { "bone_name": group_ik_bone.name, "radius": radius }
                for ik_bone_name in ik_names:
                    ik_bone = rig.data.edit_bones[ik_bone_name]
                    ik_bone.parent = group_ik_bone
                    ik_bone.inherit_scale = 'NONE'


def set_spring_rig_constraints(rig, bone_defs, ik_groups, ik_targets, mch_roots):
    fk_bone : bpy.types.PoseBone
    twk_bone : bpy.types.PoseBone

    rigidbody.add_simulation_bone_collection(rig)

    shape_fk = bones.generate_spring_widget(rig, "SpringBoneFK", "FK", 0.5)
    shape_ik = bones.generate_spring_widget(rig, "SpringBoneIK", "IK", 0.025)
    shape_grp = bones.generate_spring_widget(rig, "SpringBoneGRP", "GRP", 0.025)
    shape_twk = bones.generate_spring_widget(rig, "SpringBoneTWK", "TWK", 0.0125)

    if rigutils.select_rig(rig):

        for group_name in ik_groups:
            if ik_groups[group_name]["control"]:
                ik_group_bone_name = ik_groups[group_name]["control"]["bone_name"]
                ik_group_bone_radius = ik_groups[group_name]["control"]["radius"]
                ik_group_bone = rig.pose.bones[ik_group_bone_name]
                ik_group_bone.custom_shape = shape_grp
                ik_group_bone.use_custom_shape_bone_size = False
                ik_group_bone.lock_scale[1] = True
                scale = (ik_group_bone_radius + 0.05) / 0.025
                rigutils.set_bone_shape_scale(ik_group_bone, scale)
                bones.set_pose_bone_lock(ik_group_bone, lock_scale = [0,1,0])
                bones.set_bone_collection(rig, ik_group_bone, "Spring (IK)", "IK", vars.SPRING_IK_LAYER, color="IK")
                #drivers.add_custom_float_property(ik_group_bone, "IK_FK", 0.0, 0.0, 1.0, description="Group FK Influence")
                #drivers.add_custom_float_property(ik_group_bone, "SIM", 0.0, 0.0, 1.0, description="Group Simulation Influence")

        for chain_root_name in bone_defs:

            # find the ik group the chain belongs and it's IK->FK data path
            #group_ik_fk_data_path = None
            #group_sim_data_path = None
            #for group_name in ik_groups:
            #    for crn in ik_groups[group_name]["chain_root_names"]:
            #        if crn == chain_root_name:
            #            if ik_groups[group_name]["control"]:
            #                ik_group_bone_name = ik_groups[group_name]["control"]["bone_name"]
            #                group_ik_fk_data_path = bones.get_data_path_pose_bone_property(ik_group_bone_name, "IK_FK")
            #                group_sim_data_path = bones.get_data_path_pose_bone_property(ik_group_bone_name, "SIM")

            chain_bone_defs = bone_defs[chain_root_name]
            mch_root_name = mch_roots[chain_root_name]
            mch_root = bones.get_pose_bone(rig, mch_root_name)
            bones.set_bone_collection(rig, mch_root, "MCH", None, vars.MCH_BONE_LAYER)
            drivers.add_custom_float_property(mch_root, "IK_FK", 0.0, 0.0, 1.0, description="FK Influence")
            drivers.add_custom_float_property(mch_root, "SIM", 0.0, 0.0, 1.0, description="Simulation Influence")
            ik_fk_data_path = bones.get_data_path_pose_bone_property(mch_root_name, "IK_FK")
            sim_data_path = bones.get_data_path_pose_bone_property(mch_root_name, "SIM")
            for bone_def in chain_bone_defs:
                fk_bone_name = bone_def[0]
                mch_bone_name = bone_def[1]
                org_bone_name = bone_def[2]
                twk_bone_name = bone_def[3]
                def_bone_name = bone_def[4]
                sim_bone_name = bone_def[5]
                length = bone_def[6]
                fk_bone = rig.pose.bones[fk_bone_name]
                twk_bone = rig.pose.bones[twk_bone_name]
                mch_bone = rig.pose.bones[mch_bone_name]
                org_bone = rig.pose.bones[org_bone_name]
                def_bone = rig.pose.bones[def_bone_name]
                sim_bone = rig.pose.bones[sim_bone_name]
                fk_bone.custom_shape = shape_fk
                fk_bone.use_custom_shape_bone_size = True
                twk_bone.custom_shape = shape_twk
                twk_bone.use_custom_shape_bone_size = False
                if length == 1:
                    bones.set_pose_bone_lock(fk_bone, lock_location=[1,1,1], lock_scale=[0,1,0])
                else:
                    bones.set_pose_bone_lock(fk_bone, lock_scale=[0,1,0])
                bones.set_pose_bone_lock(mch_bone, lock_location = [1,1,1], lock_rotation = [1,1,1,1], lock_scale=[1,1,1])
                bones.set_pose_bone_lock(twk_bone, lock_rotation = [1,0,1,1], lock_scale = [0,1,0])
                bones.set_bone_collection(rig, fk_bone, "Spring (FK)", "FK", vars.SPRING_FK_LAYER, color="FK")
                bones.set_bone_collection(rig, twk_bone, "Spring (Tweak)", "Tweak", vars.SPRING_TWEAK_LAYER, color="TWEAK")
                bones.set_bone_collection(rig, sim_bone, "Simulation", "Simulation", vars.SIM_BONE_LAYER, color="SIM")
                bones.set_bone_collection(rig, mch_bone, "MCH", None, vars.MCH_BONE_LAYER)
                bones.set_bone_collection(rig, org_bone, "ORG", None, vars.ORG_BONE_LAYER)
                bones.set_bone_collection(rig, def_bone, "DEF", None, vars.DEF_BONE_LAYER)
                # sim > fk (influence driver)
                simc = bones.add_copy_transforms_constraint(rig, rig, sim_bone_name, fk_bone_name, 0.0)
                simc_driver = drivers.make_driver(simc, "influence", "SCRIPTED", "sim")
                drivers.make_driver_var(simc_driver, "SINGLE_PROP", "sim", rig, "OBJECT", sim_data_path)
                # fk -> org
                fkc = bones.add_copy_transforms_constraint(rig, rig, fk_bone_name, org_bone_name, 1.0)
                # mch -> org (influence driver)
                mchc = bones.add_copy_transforms_constraint(rig, rig, mch_bone_name, org_bone_name, 1.0)
                expr = "(1.0 - ikfk)*(1.0 - sim)"
                mchc_driver = drivers.make_driver(mchc, "influence", "SCRIPTED", expr)
                drivers.make_driver_var(mchc_driver, "SINGLE_PROP", "ikfk", rig, "OBJECT", ik_fk_data_path)
                drivers.make_driver_var(mchc_driver, "SINGLE_PROP", "sim", rig, "OBJECT", sim_data_path)
                # twk (parented to mch) -> def
                defc1 = bones.add_copy_transforms_constraint(rig, rig, twk_bone_name, def_bone_name, 1.0)
                # finally: def > stretch_to def.child:twk
                if len(def_bone.children) > 0:
                    child_def = lookup_bone_def_child(chain_bone_defs, def_bone)
                    if child_def:
                        twk_child_bone_name = child_def[3]
                        defc2 = bones.add_stretch_to_constraint(rig, rig, twk_child_bone_name, def_bone_name, 1.0)


        for group_name in ik_groups:
            ik_names = ik_groups[group_name]["targets"]
            for chain_root_name in ik_targets:
                ik_target_def = ik_targets[chain_root_name]
                for mch_bone_name, ik_bone_name, length in ik_target_def:
                    if ik_bone_name in ik_names:
                        ik_bone = rig.pose.bones[ik_bone_name]
                        ik_bone.custom_shape = shape_ik
                        ik_bone.use_custom_shape_bone_size = False
                        ik_bone.lock_scale[1] = True
                        bones.set_bone_collection(rig, ik_bone, "Spring (IK)", "IK", vars.SPRING_IK_LAYER, color="IK")
                        bones.add_inverse_kinematic_constraint(rig, rig, ik_bone_name, mch_bone_name,
                                                        use_tail=True, use_stretch=True, influence=1.0,
                                                        use_location=True, use_rotation=True,
                                                        orient_weight=1.0, chain_count=length)
                        drivers.add_custom_string_property(ik_bone, "ik_root", str(mch_bone_name))


def rigify_spring_rig(chr_cache, rigify_rig, parent_mode):
    pose_position = rigify_rig.data.pose_position
    rigify_rig.data.pose_position = "REST"

    if rigutils.edit_rig(rigify_rig):
        spring_rig = springbones.get_spring_rig(chr_cache, rigify_rig, parent_mode, mode = "EDIT")
        if not spring_rig:
            return
        spring_rig_name = spring_rig.name
        bone_defs = {}
        ik_targets = {}
        ik_groups = {}
        mch_roots = {}
        for chain_root in spring_rig.children:
            chain_bone_defs = []
            chain_ik_targets = []
            mch_root_name = rigify_spring_chain(rigify_rig, spring_rig, 0, chain_root, chain_bone_defs, chain_ik_targets)
            bone_defs[chain_root.name] = chain_bone_defs
            ik_targets[chain_root.name] = chain_ik_targets
            mch_roots[chain_root.name] = mch_root_name
            if chain_bone_defs and chain_ik_targets:
                names = [ bone_def[4] for bone_def in chain_bone_defs ]
                chain_name = utils.get_common_name(names)
                if not chain_name:
                    chain_name = "NONE"
                if chain_name.startswith("DEF-"):
                    chain_name = chain_name[4:]
                if chain_name not in ik_groups:
                    ik_groups[chain_name] = { "targets": [],
                                              "chain_root_names": [],
                                              "control": None }
                ik_groups[chain_name]["targets"].extend([ ik_target_def[1] for ik_target_def in chain_ik_targets ])
                ik_groups[chain_name]["chain_root_names"].append(chain_root.name)
        process_spring_groups(rigify_rig, spring_rig, ik_groups)
        set_spring_rig_constraints(rigify_rig, bone_defs, ik_groups, ik_targets, mch_roots)
        drivers.add_custom_float_property(rigify_rig.pose.bones[spring_rig_name], "rigified", 1.0)
        bones.set_bone_collection_visibility(rigify_rig, "Spring (FK)", vars.SPRING_FK_LAYER, True)
        bones.set_bone_collection_visibility(rigify_rig, "Spring (IK)", vars.SPRING_IK_LAYER, True)
        bones.set_bone_collection_visibility(rigify_rig, "Spring (Tweak)", vars.SPRING_TWEAK_LAYER, True)
        bones.set_bone_collection_visibility(rigify_rig, "Spring (Edit)", vars.SPRING_EDIT_LAYER, False)
        bones.set_bone_collection_visibility(rigify_rig, "Simulation", vars.SIM_BONE_LAYER, False)

    rigify_rig.data.pose_position = pose_position


def rigify_spring_rigs(chr_cache, cc3_rig, rigify_rig, bone_mapping):
    props = vars.props()
    rigutils.select_rig(rigify_rig)
    pose_position = rigify_rig.data.pose_position
    rigify_rig.data.pose_position = "REST"
    spring_rigs = springbones.get_spring_rigs(chr_cache, rigify_rig, mode = "POSE")
    if spring_rigs:
        for parent_mode in spring_rigs:
            rigify_spring_rig(chr_cache, rigify_rig, parent_mode)
        props.section_rigify_spring = True
    rigify_rig.data.pose_position = pose_position



def derigify_spring_rig(chr_cache, rigify_rig, parent_mode):
    to_remove = []
    to_layer = []
    DRIVER_PROPS = [ "influence" ]

    if rigutils.select_rig(rigify_rig):
        spring_rig = springbones.get_spring_rig(chr_cache, rigify_rig, parent_mode, mode = "POSE")
        child_bones = bones.get_bone_children(spring_rig, include_root=False)
        for bone in child_bones:
            # keep only the DEF bones (and the RL_ spring root):
            if bone.name.startswith("DEF-"):
                bone.name = bone.name[4:]
                bones.set_bone_collection(rigify_rig, bone, "Spring (Edit)", None, vars.SPRING_EDIT_LAYER)
                to_layer.append(bone.name)
            else:
                to_remove.append(bone.name)
                # remove any drivers on the contraints
                for c in bone.constraints:
                    for prop in DRIVER_PROPS:
                        c.driver_remove(prop)

            # remove all constraints from the spring rig bones
            while bone.constraints:
                bone.constraints.remove(bone.constraints[0])

        if rigutils.edit_rig(rigify_rig):
            for bone_name in to_remove:
                utils.log_info(f"Removing spring rigify bone: {bone_name}")
                bone = rigify_rig.data.edit_bones[bone_name]
                rigify_rig.data.edit_bones.remove(bone)
            for bone_name in to_layer:
                utils.log_info(f"Keeping spring rig bone: {bone_name}")
                bones.set_bone_collection(rigify_rig, bone, "Spring (Edit)", None, vars.SPRING_EDIT_LAYER)

        if "rigified" in spring_rig:
            spring_rig["rigified"] = False

        rigutils.select_rig(rigify_rig)
        bones.set_bone_collection_visibility(rigify_rig, "Spring (Edit)", vars.SPRING_EDIT_LAYER, True)


def group_props_to_value(chr_cache, group_pose_bone, prop, value):
    arm = None
    if chr_cache:
        arm = chr_cache.get_armature()
    if group_pose_bone and arm:
        for child_pose_bone in group_pose_bone.children:
            if "ik_root" in child_pose_bone:
                search_bone_name = child_pose_bone["ik_root"]
            else:
                search_bone_name = child_pose_bone.name
            spring_rig_def, mch_root_name, parent_mode = springbones.get_spring_rig_from_child(chr_cache, arm, search_bone_name)
            mch_root = arm.pose.bones[mch_root_name]
            if prop in mch_root:
                mch_root[prop] = value
    # set a bone value to force an update:
    l = group_pose_bone.location
    group_pose_bone.location = l


def rl_vertex_group(obj, group):
    """Find the vertex group in the object, either with a prefixed CC_Base_ or without."""
    if group in obj.vertex_groups:
        return group
    # remove "CC_Base_" from name and try again.
    if len(group) > 8:
        group = group[8:]
        if group in obj.vertex_groups:
            return group
    return None


def rename_vertex_groups(cc3_rig, rigify_rig, vertex_groups, acc_vertex_group_map):
    """Rename the CC3 rig vertex weight groups to the Rigify deformation bone names,
       removes matching existing vertex groups created by parent with automatic weights.
       Thus leaving just the automatic face rig weights.
    """

    utils.log_info("Remapping original Deformation vertex groups to the new Rigify bones:")
    utils.log_indent()

    obj : bpy.types.Object
    for obj in rigify_rig.children:

        utils.log_info(f"Remapping groups for: {obj.name}")

        # remove the destination vertex groups (these will have been created by the parenting operation)
        # and rename the source vertex groups to the destination groups
        for vgrn in vertex_groups:

            vg_to = vgrn[0]
            vg_from = rl_vertex_group(obj, vgrn[1])

            if vg_from:

                try:
                    if vg_to in obj.vertex_groups:
                        obj.vertex_groups.remove(obj.vertex_groups[vg_to])
                except:
                    pass

                try:
                    if vg_from in obj.vertex_groups:
                        obj.vertex_groups[vg_from].name = vg_to
                except:
                    pass

        # rename accessory vertex groups
        for vg in obj.vertex_groups:
            if vg.name in acc_vertex_group_map:
                dst_vg_name = acc_vertex_group_map[vg.name]
                vg.name = dst_vg_name

        for mod in obj.modifiers:
            if mod.type == "ARMATURE":
                mod.object = rigify_rig
                mod.use_deform_preserve_volume = False

    utils.log_recess()


def store_relative_mappings(meta_rig, coords):
    """Store bone positions relative to a bounding box of control bones.
    """

    if rigutils.edit_rig(meta_rig):
        for mapping in rigify_mapping_data.RELATIVE_MAPPINGS:
            bone_name = mapping[0]
            bone = bones.get_edit_bone(meta_rig, bone_name)
            if bone:
                bone_head_pos = meta_rig.matrix_world @ bone.head
                bone_tail_pos = meta_rig.matrix_world @ bone.tail
                box = BoundingBox()
                for i in range(2, len(mapping)):
                    rel_name = mapping[i]
                    rel_bone = bones.get_edit_bone(meta_rig, rel_name)
                    if rel_bone:
                        head_pos = meta_rig.matrix_world @ rel_bone.head
                        tail_pos = meta_rig.matrix_world @ rel_bone.tail
                        box.add(head_pos)
                        #box.add(tail_pos)
                box.pad(rigify_mapping_data.BOX_PADDING)
                coords[bone_name] = [box.relative(bone_head_pos), box.relative(bone_tail_pos)]


def restore_relative_mappings(meta_rig, coords):
    """Restore bone positions relative to a bounding box of control bones.
    """

    if rigutils.edit_rig(meta_rig):
        for mapping in rigify_mapping_data.RELATIVE_MAPPINGS:
            bone_name = mapping[0]
            bone = bones.get_edit_bone(meta_rig, bone_name)
            if bone:
                box = BoundingBox()
                for i in range(2, len(mapping)):
                    rel_name = mapping[i]
                    rel_bone = bones.get_edit_bone(meta_rig, rel_name)
                    if rel_bone:
                        head_pos = meta_rig.matrix_world @ rel_bone.head
                        tail_pos = meta_rig.matrix_world @ rel_bone.tail
                        box.add(head_pos)
                        #box.add(tail_pos)
                box.pad(rigify_mapping_data.BOX_PADDING)
                rc = coords[bone_name]
                if (mapping[1] == "HEAD" or mapping[1] == "BOTH"):
                    bone.head = box.coord(rc[0])
                if (mapping[1] == "TAIL" or mapping[1] == "BOTH"):
                    bone.tail = box.coord(rc[1])


def store_bone_roll(cc3_rig, meta_rig, roll_store, rigify_data: rigify_mapping_data.RigifyData):
    """Store the bone roll and roll axis (z_axis) for each bone in the meta rig.
    """

    prefs = vars.prefs()

    cc3_bone_store = {}
    bone: bpy.types.EditBone
    if rigutils.edit_rig(cc3_rig):
        for bone in cc3_rig.data.edit_bones:
            cc3_bone_store[bone.name] = (cc3_rig.matrix_world @ bone.z_axis)

    if rigutils.edit_rig(meta_rig):
        for bone in meta_rig.data.edit_bones:
            source_name = rigify_data.get_source_bone(bone.name)
            if prefs.rigify_align_bones == "CC" and source_name and source_name in cc3_bone_store:
                z_axis: Vector = cc3_bone_store[source_name]
                z_axis.normalize()
                roll_store[bone.name] = [bone.roll, z_axis]
            else:
                z_axis: Vector = (meta_rig.matrix_world @ bone.z_axis)
                z_axis.normalize()
                roll_store[bone.name] = [bone.roll, z_axis]


def restore_bone_roll(meta_rig, roll_store):
    """Restore the bone roll for each bone in the meta rig, after the positions have matched
       to the CC3 rig.
    """

    prefs = vars.prefs()

    if rigutils.edit_rig(meta_rig):

        steep_a_pose = False
        world_x = Vector((1, 0, 0))

        # test upper arm for a steep A-pose (arms at more than 45 degrees down)
        arm_l = bones.get_edit_bone(meta_rig, "upper_arm.L")
        y_axis = arm_l.y_axis.normalized()
        if world_x.dot(y_axis) < 0.707:
            steep_a_pose = True

        # test lower arm for a steep A-pose (for good measure)
        arm_l = bones.get_edit_bone(meta_rig, "forearm.L")
        y_axis = arm_l.y_axis.normalized()
        if world_x.dot(y_axis) < 0.707:
            steep_a_pose = True

        bone: bpy.types.EditBone
        for bone in meta_rig.data.edit_bones:
            if bone.name in roll_store:
                bone_roll = roll_store[bone.name][0]
                bone_z_axis = roll_store[bone.name][1]
                bone.align_roll(bone_z_axis)
                if prefs.rigify_align_bones == "METARIG":
                    for correction in rigify_mapping_data.ROLL_CORRECTION:
                        if correction[0] == bone.name:
                            if steep_a_pose:
                                axis = correction[2]
                            else:
                                axis = correction[1]
                            bones.align_edit_bone_roll(bone, axis)


def set_rigify_params(meta_rig):
    """Apply custom Rigify parameters to bones in the meta rig.
    """

    if rigutils.select_rig(meta_rig):
        for params in rigify_mapping_data.RIGIFY_PARAMS:
            bone_name = params[0]
            bone_param = params[1]
            bone_value = params[2]
            pose_bone = bones.get_pose_bone(meta_rig, bone_name)
            if pose_bone:
                try:
                    exec(f"pose_bone.rigify_parameters.{bone_param} = bone_value", None, locals())
                except:
                    pass


def map_face_bones(cc3_rig, meta_rig, cc3_head_bone):
    """Map positions of special face bones.
    """

    obj : bpy.types.Object = None
    for child in cc3_rig.children:
        if child.name.lower().endswith("base_eye"):
            obj = child
    length = 0.375

    if rigutils.edit_rig(meta_rig):

        # left and right eyes

        left_eye = bones.get_edit_bone(meta_rig, "eye.L")
        left_eye_source = bones.get_rl_bone(cc3_rig, "CC_Base_L_Eye")
        right_eye = bones.get_edit_bone(meta_rig, "eye.R")
        right_eye_source = bones.get_rl_bone(cc3_rig, "CC_Base_R_Eye")

        if left_eye and left_eye_source:
            head_position = cc3_rig.matrix_world @ left_eye_source.head_local
            tail_position = cc3_rig.matrix_world @ left_eye_source.tail_local
            dir : Vector = tail_position - head_position
            left_eye.tail = head_position - (dir * length)

        if right_eye and right_eye_source:
            head_position = cc3_rig.matrix_world @ right_eye_source.head_local
            tail_position = cc3_rig.matrix_world @ right_eye_source.tail_local
            dir : Vector = tail_position - head_position
            right_eye.tail = head_position - (dir * length)

        # head bone

        spine6 = bones.get_edit_bone(meta_rig, "spine.006")
        head_bone_source = bones.get_rl_bone(cc3_rig, cc3_head_bone)

        if spine6 and head_bone_source:
            head_position = cc3_rig.matrix_world @ head_bone_source.head_local
            length = 0
            n = 0
            if left_eye_source:
                left_eye_position = cc3_rig.matrix_world @ left_eye_source.head_local
                length += left_eye_position.z - head_position.z
                n += 1
            if right_eye_source:
                right_eye_position = cc3_rig.matrix_world @ right_eye_source.head_local
                length += right_eye_position.z - head_position.z
                n += 1
            if n > 0:
                length *= 2.65 / n
            else:
                length = 0.25
            tail_position = head_position + Vector((0,0,1)) * length
            spine6.tail = tail_position

        # teeth bones
        face_bone = bones.get_edit_bone(meta_rig, "face")
        teeth_t_bone = bones.get_edit_bone(meta_rig, "teeth.T")
        teeth_t_source_bone = bones.get_rl_bone(cc3_rig, "CC_Base_Teeth01")
        teeth_b_bone = bones.get_edit_bone(meta_rig, "teeth.B")
        teeth_b_source_bone = bones.get_rl_bone(cc3_rig, "CC_Base_Teeth02")

        if face_bone and teeth_t_bone and teeth_t_source_bone:
            face_dir = face_bone.tail - face_bone.head
            teeth_t_bone.head = (cc3_rig.matrix_world @ teeth_t_source_bone.head_local) + face_dir * 0.5
            teeth_t_bone.tail = (cc3_rig.matrix_world @ teeth_t_source_bone.head_local)

        if face_bone and teeth_b_bone and teeth_b_source_bone:
            face_dir = face_bone.tail - face_bone.head
            teeth_b_bone.head = (cc3_rig.matrix_world @ teeth_b_source_bone.head_local) + face_dir * 0.5
            teeth_b_bone.tail = (cc3_rig.matrix_world @ teeth_b_source_bone.head_local)


def fix_jaw_pivot(cc3_rig, meta_rig):
    """Set the exact jaw bone position by setting the YZ coordinates of the jaw left and right bones.
    """

    if rigutils.edit_rig(meta_rig):
        jaw_l_bone = bones.get_edit_bone(meta_rig, "jaw.L")
        jaw_r_bone = bones.get_edit_bone(meta_rig, "jaw.R")
        jaw_source_bone = bones.get_rl_bone(cc3_rig, "CC_Base_JawRoot")
        if jaw_source_bone:
            jaw_xyz = cc3_rig.matrix_world @ jaw_source_bone.head_local
            if jaw_l_bone:
                jaw_l_bone.head.z = jaw_xyz.z
                jaw_l_bone.head.y = jaw_xyz.y
            if jaw_r_bone:
                jaw_r_bone.head.z = jaw_xyz.z
                jaw_r_bone.head.y = jaw_xyz.y


def report_uv_face_targets(obj, meta_rig):
    """For reprting the UV coords of the face bones in the meta rig.
    """

    if rigutils.edit_rig(meta_rig):
        mat_slot = get_head_material_slot(obj)
        mesh = obj.data
        t_mesh = geom.get_triangulated_bmesh(mesh)
        bone : bpy.types.EditBone
        for bone in meta_rig.data.edit_bones:

            if bone.name != "face":
                head_world = bone.head
                tail_world = bone.tail
                head_uv = geom.get_uv_from_world(obj, t_mesh, mat_slot, head_world, project=True)
                tail_uv = geom.get_uv_from_world(obj, t_mesh, mat_slot, tail_world, project=True)
                utils.log_always(f"{bone.name} - uv: {head_uv} -> {tail_uv}")


def map_uv_targets(chr_cache, cc3_rig, meta_rig):
    """Fetch spacial coordinates for bone positions from UV coordinates.
    """

    obj = meshutils.get_head_body_object(chr_cache)
    if obj is None:
        utils.log_error("Cannot find BODY mesh for uv targets!")
        return

    if not rigutils.edit_rig(meta_rig):
        return

    mat_slot = get_head_material_slot(obj)
    mesh = obj.data
    t_mesh = geom.get_triangulated_bmesh(mesh)

    TARGETS = None
    if chr_cache.generation == "G3Plus":
        TARGETS = rigify_mapping_data.UV_TARGETS_G3PLUS
    elif chr_cache.generation == "G3":
        TARGETS = rigify_mapping_data.UV_TARGETS_G3
    if not TARGETS:
        return

    for uvt in TARGETS:
        name = uvt[0]
        type = uvt[1]
        num_targets = len(uvt) - 2
        bone = bones.get_edit_bone(meta_rig, name)
        if bone:
            last = None
            m_bone = None
            m_last = None

            if name.endswith(".R"):
                m_name = name[:-2] + ".L"
                m_bone = bones.get_edit_bone(meta_rig, m_name)

            if type == "CONNECTED":
                for index in range(0, num_targets):
                    uv_target = uvt[index + 2]
                    uv_target.append(0)

                    world = geom.get_world_from_uv(obj, t_mesh, mat_slot, uv_target, rigify_mapping_data.UV_THRESHOLD)
                    if m_bone or m_last:
                        m_uv_target = mirror_uv_target(uv_target)
                        m_world = geom.get_world_from_uv(obj, t_mesh, mat_slot, m_uv_target, rigify_mapping_data.UV_THRESHOLD)

                    if world:
                        if last:
                            last.tail = world
                            if m_last:
                                m_last.tail = m_world
                        if bone:
                            bone.head = world
                            if m_bone:
                                m_bone.head = m_world

                    if bone is None:
                        break

                    index += 1
                    last = bone
                    m_last = m_bone
                    # follow the connected chain of bones
                    if len(bone.children) > 0 and bone.children[0].use_connect:
                        bone = bone.children[0]
                        if m_bone:
                            m_bone = m_bone.children[0]
                    else:
                        bone = None
                        m_bone = None

            elif type == "DISCONNECTED":
                for index in range(0, num_targets):
                    target_uvs = uvt[index + 2]
                    uv_head = target_uvs[0]
                    uv_tail = target_uvs[1]
                    uv_head.append(0)
                    uv_tail.append(0)

                    world_head = geom.get_world_from_uv(obj, t_mesh, mat_slot, uv_head, rigify_mapping_data.UV_THRESHOLD)
                    world_tail = geom.get_world_from_uv(obj, t_mesh, mat_slot, uv_tail, rigify_mapping_data.UV_THRESHOLD)

                    if m_bone:
                        muv_head = mirror_uv_target(uv_head)
                        muv_tail = mirror_uv_target(uv_tail)
                        mworld_head = geom.get_world_from_uv(obj, t_mesh, mat_slot, muv_head, rigify_mapping_data.UV_THRESHOLD)
                        mworld_tail = geom.get_world_from_uv(obj, t_mesh, mat_slot, muv_tail, rigify_mapping_data.UV_THRESHOLD)

                    if bone and world_head:
                        bone.head = world_head
                        if m_bone:
                            m_bone.head = mworld_head
                    if bone and world_tail:
                        bone.tail = world_tail
                        if m_bone:
                            m_bone.tail = mworld_tail

                    index += 1
                    # follow the chain of bones
                    if len(bone.children) > 0:
                        bone = bone.children[0]
                        if m_bone:
                            m_bone = m_bone.children[0]
                    else:
                        break

            elif type == "HEAD":
                uv_target = uvt[2]
                uv_target.append(0)

                world = geom.get_world_from_uv(obj, t_mesh, mat_slot, uv_target, rigify_mapping_data.UV_THRESHOLD)
                if world:
                    bone.head = world

            elif type == "TAIL":
                uv_target = uvt[2]
                uv_target.append(0)

                world = geom.get_world_from_uv(obj, t_mesh, mat_slot, uv_target, rigify_mapping_data.UV_THRESHOLD)
                if world:
                    bone.tail = world


def mirror_uv_target(uv):
    muv = uv.copy()
    x = muv[0]
    muv[0] = 1 - x
    return muv


def get_head_material_slot(obj):
    for i in range(0, len(obj.material_slots)):
        slot = obj.material_slots[i]
        if slot.material:
            if "Std_Skin_Head" in slot.material.name:
                return i
    return -1


def map_bone(cc3_rig, meta_rig, bone_mapping):
    """Maps the head and tail of a bone in the destination
    rig, to the positions of the head and tail of bones in
    the source rig.

    Must be in edit mode with the destination rig active.
    """

    if not rigutils.edit_rig(meta_rig):
        return

    if not bone_mapping[BONEMAP_METARIG_NAME]:
        return

    dst_bone_name = bone_mapping[BONEMAP_METARIG_NAME]
    src_bone_head_name = bone_mapping[BONEMAP_CC_HEAD]
    src_bone_tail_name = bone_mapping[BONEMAP_CC_TAIL]

    utils.log_info(f"Mapping: {dst_bone_name} from: {src_bone_head_name}/{src_bone_tail_name}")

    dst_bone : bpy.types.EditBone
    dst_bone = bones.get_edit_bone(meta_rig, dst_bone_name)
    src_bone = None

    if dst_bone:

        head_position = dst_bone.head
        tail_position = dst_bone.tail

        # fetch the target start point
        if src_bone_head_name != "":
            reverse = False
            if src_bone_head_name[0] == "-":
                src_bone_head_name = src_bone_head_name[1:]
                reverse = True
            src_bone = bones.get_rl_bone(cc3_rig, src_bone_head_name)
            if not src_bone and len(bone_mapping) > BONEMAP_ALT_NAMES:
                for alt_name in bone_mapping[BONEMAP_ALT_NAMES]:
                    src_bone = bones.get_rl_bone(cc3_rig, alt_name)
                    if src_bone:
                        break
            if src_bone:
                if reverse:
                    head_position = cc3_rig.matrix_world @ src_bone.tail_local
                else:
                    head_position = cc3_rig.matrix_world @ src_bone.head_local
            else:
                utils.log_error(f"source head bone: {src_bone_head_name} not found!")

        # fetch the target end point
        if src_bone_tail_name != "":
            reverse = False
            if src_bone_tail_name[0] == "-":
                src_bone_tail_name = src_bone_tail_name[1:]
                reverse = True
            src_bone = bones.get_rl_bone(cc3_rig, src_bone_tail_name)
            if not src_bone and len(bone_mapping) > BONEMAP_ALT_NAMES:
                for alt_name in bone_mapping[BONEMAP_ALT_NAMES]:
                    src_bone = bones.get_rl_bone(cc3_rig, alt_name)
                    if src_bone:
                        break
            if src_bone:
                if reverse:
                    tail_position = cc3_rig.matrix_world @ src_bone.head_local
                else:
                    tail_position = cc3_rig.matrix_world @ src_bone.tail_local
            else:
                utils.log_error(f"source tail bone: {src_bone_tail_name} not found!")

        # lerp the start and end positions if supplied
        if src_bone:

            if (len(bone_mapping) > BONEMAP_LERP_TO and
                bone_mapping[BONEMAP_LERP_FROM] is not None and
                bone_mapping[BONEMAP_LERP_TO] is not None and
                src_bone_head_name != "" and
                src_bone_tail_name != ""):

                start = bone_mapping[BONEMAP_LERP_FROM]
                end = bone_mapping[BONEMAP_LERP_TO]
                vec = tail_position - head_position
                org = head_position
                head_position = org + vec * start
                tail_position = org + vec * end

            # set the head position
            if src_bone_head_name != "":
                dst_bone.head = head_position

            # set the tail position
            if src_bone_tail_name != "":
                dst_bone.tail = tail_position

    else:
        utils.log_error(f"destination bone: {dst_bone_name} not found!")


def fix_bend(meta_rig, bone_one_name, bone_two_name, dir : Vector):
    """Determine if the bend between two bones is sufficient to generate an accurate pole in the rig,
       by calculating where the middle joint lies on the line between the start and end points and
       determining if the distance to that line is large enough and in the right direction.
       Recalculating the joint position if not.
    """

    dir.normalize()
    if rigutils.edit_rig(meta_rig):
        one : bpy.types.EditBone = utils.find_edit_bone_in_armature(meta_rig, bone_one_name)
        two : bpy.types.EditBone = utils.find_edit_bone_in_armature(meta_rig, bone_two_name)
        if one and two:
            start : Vector = one.head
            mid : Vector = one.tail
            end : Vector = two.tail
            u : Vector = end - start
            v : Vector = mid - start
            u.normalize()
            l = u.dot(v)
            line_mid : Vector = u * l + start
            disp : Vector = mid - line_mid
            d = disp.length
            if dir.dot(disp) < 0 or d < 0.001:
                utils.log_info(f"Bend between {bone_one_name} and {bone_two_name} is too shallow or negative, fixing.")
                new_mid_dir : Vector = dir - u.dot(dir) * u
                new_mid_dir.normalize()
                new_mid = line_mid + new_mid_dir * 0.001
                utils.log_info(f"New joint position: {new_mid}")
                one.tail = new_mid
                two.head = new_mid


def hide_face_bones(meta_rig):
    """Move all the non basic face rig bones into a hidden layer.
    """

    if rigutils.edit_rig(meta_rig):
        for b in rigify_mapping_data.NON_BASIC_FACE_BONES:
            bone = bones.get_edit_bone(meta_rig, b)
            if bone:
                bones.set_bone_collection(meta_rig, bone, "Hidden", None, 31)
    if rigutils.select_rig(meta_rig):
        for b in rigify_mapping_data.NON_BASIC_FACE_BONES:
            bone = bones.get_bone(meta_rig, b)
            if bone:
                bones.set_bone_collection(meta_rig, bone, "Hidden", None, 31)


def convert_to_basic_face_rig(rigify_rig):
    if rigutils.edit_rig(rigify_rig):
        for b in rigify_mapping_data.NON_BASIC_FACE_BONES:
            bone_names = [b, f"DEF-{b}", f"ORG-{b}", f"MCH-{b}"]
            for bone_name in bone_names:
                bone = bones.get_edit_bone(rigify_rig, bone_name)
                if bone:
                    rigify_rig.data.edit_bones.remove(bone)
    rigutils.select_rig(rigify_rig)


def add_shape_key_drivers(chr_cache, rig):
    """Add drivers from the rig bones to facial expressions"""

    head_body_obj = meshutils.get_head_body_object(chr_cache)

    # remove existing shape key drivers on the head body object
    if utils.object_has_shape_keys(head_body_obj):
        obj_key: bpy.types.ShapeKey
        for obj_key in head_body_obj.data.shape_keys.key_blocks:
            try:
                obj_key.driver_remove("value")
            except: ...

    # add drivers from the rig bones to facial expressions
    for skd_def in rigify_mapping_data.SHAPE_KEY_DRIVERS:
        flags = skd_def[0]
        scale = 1.0
        # "Bfr" == Basic face rig
        # Using the full shape key strength is a bit strong with the full face rig in effect
        if "Bfr" in flags and chr_cache.rigified_full_face_rig:
            scale = 0.5
        shape_key_name = skd_def[1]
        driver_def = skd_def[2]
        var_def = skd_def[3]

        add_shape_key_driver(rig, head_body_obj, shape_key_name, driver_def, var_def, scale)

    # drive the shape keys on any other body objects from the head body object
    drivers.add_body_shape_key_drivers(chr_cache, True)

    # seems to be fixed now
    #if utils.B310():
    #    left_data_path = bones.get_data_rigify_limb_property("LEFT_LEG", "IK_Stretch")
    #    right_data_path = bones.get_data_rigify_limb_property("RIGHT_LEG", "IK_Stretch")
    #    expression = "pow(ik_stretch, 3)"
    #    bones.add_constraint_scripted_influence_driver(rig, "DEF-foot.L", left_data_path, "ik_stretch",
    #                                                   constraint_type="STRETCH_TO", expression=expression)
    #    bones.add_constraint_scripted_influence_driver(rig, "DEF-foot.R", right_data_path, "ik_stretch",
    #                                                   constraint_type="STRETCH_TO", expression=expression)


def add_shape_key_driver(rig, obj, shape_key_name, driver_def, var_def, scale=1.0):
    if utils.object_mode():
        shape_key = meshutils.find_shape_key(obj, shape_key_name)
        if shape_key:
            fcurve : bpy.types.FCurve
            fcurve = shape_key.driver_add("value")
            driver : bpy.types.Driver = fcurve.driver
            driver.type = driver_def[0]
            if driver.type == "SCRIPTED":
                if scale != 1.0:
                    driver.expression = f"{driver_def[1]}*{scale}"
                else:
                    driver.expression = driver_def[1]
            var : bpy.types.DriverVariable = driver.variables.new()
            var.name = var_def[0]
            var.type = var_def[1]
            if var_def[1] == "TRANSFORMS":
                #var.targets[0].id_type = "OBJECT"
                var.targets[0].id = rig.id_data
                var.targets[0].bone_target = var_def[2]
                var.targets[0].rotation_mode = "AUTO"
                var.targets[0].transform_type = var_def[3]
                var.targets[0].transform_space = var_def[4]


def adjust_rigify_constraints(chr_cache, rigify_rig):
    # { bone name: [ constraint type, subtarget name, attribute, value ], }
    ADJUST = {
        # adjust MCH jaw to avoid stretching the lips down too much
        "MCH-jaw_master.001": ["COPY_TRANSFORMS", "jaw_master", "influence", 0.9],
    }

    if rigutils.select_rig(rigify_rig):
        for bone_name in ADJUST:
            constraint_type = ADJUST[bone_name][0]
            subtarget = ADJUST[bone_name][1]
            attribute = ADJUST[bone_name][2]
            value = ADJUST[bone_name][3]
            pose_bone = bones.get_pose_bone(rigify_rig, bone_name)
            if pose_bone:
                con = bones.find_constraint(pose_bone, of_type=constraint_type, with_subtarget=subtarget)
                if con:
                    if hasattr(con, attribute):
                        setattr(con, attribute, value)
    return


def correct_meta_rig(meta_rig):
    """Add a slight displacement (if needed) to the knee and elbow to ensure the poles are the right way.
    """

    utils.log_info("Correcting Meta-Rig, Knee and Elbow bends.")
    utils.log_indent()

    fix_bend(meta_rig, "thigh.L", "shin.L", Vector((0,-1,0)))
    fix_bend(meta_rig, "thigh.R", "shin.R", Vector((0,-1,0)))
    fix_bend(meta_rig, "upper_arm.L", "forearm.L", Vector((0,1,0)))
    fix_bend(meta_rig, "upper_arm.R", "forearm.R", Vector((0,1,0)))

    utils.object_mode()

    utils.log_recess()


def store_source_bone_data(cc3_rig, rigify_rig, rigify_data):
    """Store source bone data from the cc3 rig in the org and def bones of rigify rig.
       This data can be used to reconstruct elements of the source rig for retargetting and exporting.
    """

    source_data = {}
    if rigutils.edit_rig(cc3_rig):
        for cc3_bone in cc3_rig.data.edit_bones:
            orig_dir = (cc3_rig.matrix_world @ cc3_bone.tail) - (cc3_rig.matrix_world @ cc3_bone.head)
            orig_z_axis = (cc3_rig.matrix_world @ cc3_bone.z_axis).normalized()
            source_data[cc3_bone.name] = [orig_dir, orig_z_axis]

    if rigutils.edit_rig(rigify_rig):
        for orig_bone_name in source_data:

            if orig_bone_name == "CC_Base_JawRoot":
                meta_bone_names = ["jaw_master"]
            else:
                meta_bone_names = bones.get_rigify_meta_bones(rigify_rig, rigify_data.bone_mapping, orig_bone_name)

            for name in meta_bone_names:
                if name in rigify_rig.data.edit_bones:
                    edit_bone: bpy.types.EditBone = rigify_rig.data.edit_bones[name]
                    orig_dir = source_data[orig_bone_name][0]
                    orig_dir_array = [orig_dir.x, orig_dir.y, orig_dir.z]
                    orig_z_axis = source_data[orig_bone_name][1]
                    orig_z_axis_array = [orig_z_axis.x, orig_z_axis.y, orig_z_axis.z]
                    utils.log_info(f"storing source bone data in {name} from {orig_bone_name}")
                    drivers.add_custom_float_array_property(edit_bone, "orig_dir", orig_dir_array)
                    drivers.add_custom_float_array_property(edit_bone, "orig_z_axis", orig_z_axis_array)
                    drivers.add_custom_string_property(edit_bone, "orig_name", orig_bone_name)
                else:
                    utils.log_error(f"Unable to find edit_bone: {name}")


def modify_rigify_controls(cc3_rig, rigify_rig, rigify_data):
    """Resize and reposition Rigify control bones to make them easier to find.
       Note: scale, location, rotation modifiers for custom control shapes is Blender 3.0.0+ only
    """

    # turn off deformation for palm bones
    if rigutils.edit_rig(rigify_rig):
        for edit_bone in rigify_rig.data.edit_bones:
            if edit_bone.name.startswith("DEF-palm"):
                edit_bone.use_deform = False

    if utils.B300():
        if rigutils.select_rig(rigify_rig):
            utils.log_info("Resizing and Repositioning rig controls:")
            utils.log_indent()
            for mod in rigify_mapping_data.CONTROL_MODIFY:
                bone_name = mod[0]
                scale = mod[1]
                translation = mod[2]
                rotation = mod[3]
                bone = bones.get_pose_bone(rigify_rig, bone_name)
                if bone:
                    utils.log_info(f"Altering: {bone.name}")
                    rigutils.set_bone_shape_scale(bone, scale)
                    bone.custom_shape_translation = translation
                    bone.custom_shape_rotation_euler = rotation
            utils.log_recess()

    # hide control rig bones if RL chain parent bones missing from CC3 rig
    if rigify_data.hide_chains and rigutils.select_rig(rigify_rig):
        bone_list = []
        for chain_def in rigify_data.hide_chains:
            rl_bone_name = chain_def[0]
            rigify_regex_list = chain_def[1]
            metarig_regex_list = chain_def[2]
            # if the chain parent is missing from the cc3 rig, hide the control rig in rigify
            if not bones.get_rl_bone(cc3_rig, rl_bone_name):
                utils.log_info(f"Chain Parent missing from CC3 Rig: {rl_bone_name}")
                utils.log_indent()
                for regex in rigify_regex_list:
                    for bone in rigify_rig.data.bones:
                        if re.match(regex, bone.name):
                            utils.log_info(f"Hiding control rig bone: {bone.name}")
                            bones.set_bone_collection(rigify_rig, bone, "Hidden", None, vars.HIDE_BONE_LAYER)
                            bone_list.append(bone.name)
                utils.log_recess()
        if bone_list and rigutils.edit_rig(rigify_rig):
            for bone_name in bone_list:
                bones.set_bone_collection(rigify_rig, bone, "Hidden", None, vars.HIDE_BONE_LAYER)
            rigutils.select_rig(rigify_rig)


def reparent_to_rigify(self, chr_cache, cc3_rig, rigify_rig, bone_mapping):
    """Unparent (with transform) from the original CC3 rig and reparent to the new rigify rig (with automatic weights for the body),
       setting the armature modifiers to the new rig.

       The automatic weights will generate vertex weights for the additional face bones in the new rig.
       (But only for the Body mesh)
    """

    utils.log_info("Reparenting character objects to new Rigify Control Rig:")
    utils.log_indent()

    props = vars.props()
    result = 1

    if utils.object_mode():

        # first move rigidbody colliders over
        rigidbody.convert_colliders_to_rigify(chr_cache, cc3_rig, rigify_rig, bone_mapping)

        for obj in cc3_rig.children:
            if utils.object_exists_is_mesh(obj) and obj.parent == cc3_rig:

                hidden = not obj.visible_get()
                if hidden:
                    utils.unhide(obj)
                obj_cache = chr_cache.get_object_cache(obj)

                if utils.try_select_object(obj, True) and utils.set_active_object(obj):
                    bpy.ops.object.parent_clear(type = "CLEAR_KEEP_TRANSFORM")

                # only the body and face objects will generate the automatic weights for the face rig.
                if (chr_cache.rigified_full_face_rig and
                    utils.object_exists_is_mesh(obj) and
                    len(obj.data.vertices) >= 2 and
                    is_face_object(obj_cache, obj) and
                    obj.name != "CC_Base_Tongue"):

                    obj_result = try_parent_auto(chr_cache, rigify_rig, obj)
                    if obj_result < result:
                        result = obj_result

                else:

                    if utils.try_select_object(rigify_rig) and utils.set_active_object(rigify_rig):
                        bpy.ops.object.parent_set(type = "OBJECT", keep_transform = True)

                    arm_mod: bpy.types.ArmatureModifier = modifiers.get_armature_modifier(obj, create=True, armature=rigify_rig)
                    if arm_mod:
                        arm_mod.object = rigify_rig

                if hidden:
                    utils.hide(obj)

    utils.log_recess()
    return result


def clean_up(chr_cache, cc3_rig, rigify_rig, meta_rig, remove_meta = False):
    """Rename the rigs, hide the original CC3 Armature and remove the meta rig.
       Set the new rig into pose mode.
    """

    utils.log_info("Cleaning Up...")
    rig_name = cc3_rig.name
    utils.hide(cc3_rig)
    # don't delete the meta_rig in advanced mode
    if remove_meta:
        utils.delete_armature_object(meta_rig)
        chr_cache.rig_meta_rig = None
    else:
        utils.hide(meta_rig)
    rigify_rig.name = rig_name + "_Rigify"
    rigify_rig.data.name = rig_name + "_Rigify"
    if utils.object_mode():
        # delesect all bones (including the hidden ones)
        # Rigimap will bake and clear constraints on the ORG bones if we don't do this...
        for bone in rigify_rig.data.bones:
            bone.select = False
        utils.clear_selected_objects()
        if utils.try_select_object(rigify_rig, True):
            utils.set_active_object(rigify_rig)
    chr_cache.set_rigify_armature(rigify_rig)
    rigify_rig["rl_import_file"] = chr_cache.import_file
    rigify_rig["rl_generation"] = chr_cache.generation


# Skinning face rigs
#
#


def is_face_object(obj_cache, obj):
    if obj and obj.type == "MESH":
        if obj_cache and obj_cache.object_type in rigify_mapping_data.BODY_TYPES:
            return True
        if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
            for shape_key in obj.data.shape_keys.key_blocks:
                if shape_key.name in rigify_mapping_data.FACE_TEST_SHAPEKEYS:
                    return True
    return False


def is_face_def_bone(bvg):
    for face_def_prefix in rigify_mapping_data.FACE_DEF_BONE_PREFIX:
        if bvg.name.startswith(face_def_prefix):
            return True
    return False


def has_facial_expression_shape_keys(obj):
    if obj and obj.type == "MESH":
        if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
            for shape_key in obj.data.shape_keys.key_blocks:
                if shape_key.name in rigify_mapping_data.FACE_TEST_SHAPEKEYS:
                    return True
    return False


PREP_VGROUP_VALUE_A = 0.5
PREP_VGROUP_VALUE_B = 1.0

def init_face_vgroups(rig, obj):
    global PREP_VGROUP_VALUE_A, PREP_VGROUP_VALUE_B
    PREP_VGROUP_VALUE_A = random()
    PREP_VGROUP_VALUE_B = random()

    utils.object_mode()
    all_verts = []
    for v in obj.data.vertices:
        all_verts.append(v.index)
    for bone in rig.data.bones:
        if is_face_def_bone(bone):
            # for each face bone in each face object,
            # create or re-use a vertex group for it and clear it
            vertex_group = meshutils.add_vertex_group(obj, bone.name)
            vertex_group.remove(all_verts)
            # weight the last vertex in the object to this bone with a test value
            last_vertex = obj.data.vertices[-1]
            first_vertex = obj.data.vertices[0]
            vertex_group.add([first_vertex.index], PREP_VGROUP_VALUE_A, 'ADD')
            vertex_group.add([last_vertex.index], PREP_VGROUP_VALUE_B, 'ADD')


def test_face_vgroups(rig, obj):
    for bone in rig.data.bones:
        if is_face_def_bone(bone):
            vertex_group : bpy.types.VertexGroup = meshutils.get_vertex_group(obj, bone.name)
            if vertex_group:
                first_vertex : bpy.types.MeshVertex = obj.data.vertices[0]
                last_vertex : bpy.types.MeshVertex = obj.data.vertices[-1]
                first_weight = -1
                last_weight = -1
                for vge in first_vertex.groups:
                    if vge.group == vertex_group.index:
                        first_weight = vge.weight
                for vge in last_vertex.groups:
                    if vge.group == vertex_group.index:
                        last_weight = vge.weight
                # if the test weights still exist in any vertex group in the mesh, the auto weights failed
                if utils.float_equals(first_weight, PREP_VGROUP_VALUE_A) and utils.float_equals(last_weight, PREP_VGROUP_VALUE_B):
                    return False
    return True


def store_non_face_vgroups(chr_cache):
    utils.log_info("Storing non face vertex weights.")
    for obj in chr_cache.get_cache_objects():
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and not obj_cache.disabled and obj_cache.is_mesh():
            if is_face_object(obj_cache, obj):
                for vg in obj.vertex_groups:
                    if not is_face_def_bone(vg):
                        vg.name = "_tmp_shift_" + vg.name


def restore_non_face_vgroups(chr_cache):
    utils.log_info("Restoring non face vertex weights.")
    for obj in chr_cache.get_cache_objects():
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and not obj_cache.disabled and obj_cache.is_mesh():
            if is_face_object(obj_cache, obj):
                for vg in obj.vertex_groups:
                    if vg.name.startswith("_tmp_shift_"):
                        unshifted_name = vg.name[11:]
                        if unshifted_name in obj.vertex_groups:
                            imposter_vertex_group = obj.vertex_groups[unshifted_name]
                            obj.vertex_groups.remove(imposter_vertex_group)
                        vg.name = unshifted_name


def lock_non_face_vgroups(chr_cache):
    utils.log_info("Locking non face vertex weights.")
    body = None
    for obj in chr_cache.get_cache_objects():
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and not obj_cache.disabled and obj_cache.is_mesh():
            if is_face_object(obj_cache, obj):
                if obj_cache.object_type == "BODY":
                    body = obj
                vg : bpy.types.VertexGroup
                for vg in obj.vertex_groups:
                    vg.lock_weight = not is_face_def_bone(vg)
    # turn off deform for the teeth and eyes, as they will get autoweighted too
    utils.log_info("Turning off Deform in jaw and eye bones.")
    arm = chr_cache.get_armature()
    if arm:
        for bone in arm.data.bones:
            if bone.name in rigify_mapping_data.FACE_DEF_BONE_PREPASS:
                bone.use_deform = False
    # select body mesh and active rig
    if body and arm and utils.object_mode():
        utils.try_select_objects([body, arm], True)
        utils.set_active_object(arm)


def unlock_vgroups(chr_cache):
    utils.log_info("Unlocking non face vertex weights.")
    for obj in chr_cache.get_cache_objects():
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and not obj_cache.disabled and obj_cache.object_type in rigify_mapping_data.BODY_TYPES:
            if obj_cache.is_mesh():
                vg : bpy.types.VertexGroup
                for vg in obj.vertex_groups:
                    vg.lock_weight = False
    # turn on deform for the teeth and the eyes
    utils.log_info("Restoring Deform in jaw and eye bones.")
    arm = chr_cache.get_armature()
    if arm:
        for bone in arm.data.bones:
            if bone.name in rigify_mapping_data.FACE_DEF_BONE_PREPASS:
                bone.use_deform = True
    # select active rig
    if arm and utils.object_mode():
        utils.try_select_object(arm, True)
        utils.set_active_object(arm)


def mesh_clean_up(obj):
    if utils.edit_mode_to(obj):
        bpy.ops.mesh.select_all(action = 'SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.delete_loose()
        bpy.ops.mesh.dissolve_degenerate()
    utils.object_mode()


def clean_up_character_meshes(chr_cache):
    face_objects = []
    arm = chr_cache.get_armature()
    for obj in chr_cache.get_cache_objects():
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and not obj_cache.disabled and obj_cache.is_mesh():
            if is_face_object(obj_cache, obj):
                face_objects.append(obj)
                mesh_clean_up(obj)
    # select body mesh and active rig
    if obj and arm and utils.object_mode():
        face_objects.append(arm)
        utils.try_select_objects(face_objects, True)
        utils.set_active_object(arm)


def prep_envelope_deform(rig, meta_rig):
    """In case face rigging fails. Prep the DEF bones for envelope waights.
       Not as good as heat map weights but better than nothing"""
    bone: bpy.types.Bone = None
    meta_bone: bpy.types.Bone = None
    pose_bone: bpy.types.PoseBone = None
    for pose_bone in rig.pose.bones:
        bone = pose_bone.bone
        if bone.use_deform:
            if bone.name.startswith("DEF-"):
                meta_name = bone.name[4:]
                if meta_name in meta_rig.data.bones:
                    meta_bone = meta_rig.data.bones[meta_name]
                    length = meta_bone.length
                    bone.envelope_weight = 0.5
                    bone.envelope_distance = max(length, 0.01)
                    bone.use_envelope_multiply = False
                    # 1mm radius
                    bone.head_radius = 0.005
                    bone.tail_radius = 0.005


def fix_envelope_lips(chr_cache, rig, obj):
    """Mask out upper or lower jaw vertices (by box regions on the UV maps)
       from the face rig vertex groups"""
    jaw_group = meshutils.get_vertex_group(obj, "CC_Base_JawRoot")
    if not jaw_group:
        return

    mat_slot = -1
    for i, slot in enumerate(obj.material_slots):
        if slot.material and slot.material.name == "Std_Skin_Head":
            mat_slot = i
    if mat_slot == -1:
        return

    if chr_cache.generation == "G3Plus":
        uv_boxes = [
            # outer skin
            [0.239191, 0.0, 0.45725, 0.48796],
            [0.45725, 0.0, 0.54275, 0.48825],
            [0.54275, 0.0, 0.758507, 0.48796],
            # inner mouth
            [0.174256, 0.014343, 0.222045, 0.155825],
            [0.769057, 0.014343, 0.82557, 0.155825],
        ]
    elif chr_cache.generation == "G3":
        uv_boxes = [
            # outer skin
            [0.0, 0.0, 1.0, 0.20482],
            # inner mouth
            [0.359772, 0.789814, 0.437885, 1.0],
            [0.560676, 0.789738, 0.641371, 1.0],
        ]
    else:
        return

    utils.log_info(f"#################### Fixing Lips {chr_cache.generation}")

    upper_jaw_groups = []
    lower_jaw_groups = []
    for vg in obj.vertex_groups:
        if vg.name.startswith("DEF-"):
            if "lip.T" in vg.name or "nose" in vg.name or "cheek" in vg.name:
                upper_jaw_groups.append(vg.index)
            elif "lip.B" in vg.name or "chin" in vg.name or "jaw" in vg.name:
                lower_jaw_groups.append(vg.index)
    bm = geom.get_bmesh(obj)
    dl = bm.verts.layers.deform.active
    ul = bm.loops.layers.uv[0]
    for face in bm.faces:
        if face.material_index == mat_slot:
            for i, l in enumerate(face.loops):
                vert = face.verts[i]
                jaw_mask = 0.0
                uv = l[ul].uv
                for uv_box in uv_boxes:
                    if (uv_box[0] <= uv[0] and uv[0] < uv_box[2] and
                        uv_box[1] <= uv[1] and uv[1] < uv_box[3]):
                        jaw_mask = 1.0
                        break
                inv_mask = 1.0 - jaw_mask
                for idx in lower_jaw_groups:
                    if idx in vert[dl]:
                        w = vert[dl][idx] * jaw_mask
                        if w < 0.001:
                            del(vert[dl][idx])
                        else:
                            vert[dl][idx] = w
                for idx in upper_jaw_groups:
                    if idx in vert[dl]:
                        w = vert[dl][idx] * inv_mask
                        if w < 0.001:
                            del(vert[dl][idx])
                        else:
                            vert[dl][idx] = w
    bm.to_mesh(obj.data)


def parent_set_with_test(chr_cache, rig, obj, envelope=False):
    init_face_vgroups(rig, obj)
    if utils.try_select_objects([obj, rig], True) and utils.set_active_object(rig):
        utils.log_always(f"Parenting: {obj.name}" + (" with envelope weights" if envelope else ""))
        if envelope:
            bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE", keep_transform=True)
            if chr_cache and (chr_cache.generation == "G3" or chr_cache.generation == "G3Plus"):
                fix_envelope_lips(chr_cache, rig, obj)
        else:
            bpy.ops.object.parent_set(type="ARMATURE_AUTO", keep_transform=True)

        if not test_face_vgroups(rig, obj):
            return False
    return True


def try_parent_auto(chr_cache, rig, obj):
    modifiers.remove_object_modifiers(obj, "ARMATURE")

    result = 1

    # first attempt

    if parent_set_with_test(chr_cache, rig, obj):
        utils.log_always(f"Success!")
    else:
        utils.log_always(f"Parent with automatic weights failed: attempting mesh clean up...")
        mesh_clean_up(obj)
        result = 0

        # second attempt

        if parent_set_with_test(chr_cache, rig, obj):
            utils.log_always(f"Success!")
        else:
            body = meshutils.get_head_body_object(chr_cache)
            body_objects = chr_cache.get_objects_of_type("BODY")

            # third attempt

            if obj == body:
                utils.log_always(f"Parent with automatic weights failed again: trying just the head mesh...")
                head = separate_head(obj)

                if parent_set_with_test(chr_cache, rig, head):
                    utils.log_always(f"Success!")
                else:
                    utils.log_always(f"Automatic weights failed for head mesh {obj.name}, attempting envelope weights...")

                    # fourth attempt, parent with envelope weights
                    if parent_set_with_test(chr_cache, rig, head, envelope=True):
                        utils.log_always(f"Success!")
                    else:
                        result = -1
                        utils.log_always(f"Automatic weights failed for {obj.name}, will need to re-parented by other means!")

                rejoin_head(head, body)

            elif obj in body_objects:

                result = 1
                utils.log_always(f"Non head body object does not need to be weighted.")

            else:

                utils.log_always(f"Parent with automatic weights failed again: transferring weights from body mesh.")
                #characters.transfer_skin_weights(chr_cache, [obj])

                if utils.try_select_object(body, True) and utils.set_active_object(obj):

                    bpy.ops.object.data_transfer(use_reverse_transfer=True,
                                                data_type='VGROUP_WEIGHTS',
                                                use_create=True,
                                                vert_mapping='POLYINTERP_NEAREST',
                                                use_object_transform=True,
                                                layers_select_src='NAME',
                                                layers_select_dst='ALL',
                                                mix_mode='REPLACE')

                utils.log_always(f"Vertex weights transferred.")

    return result


def attempt_reparent_auto_character(chr_cache):
    utils.object_mode()
    utils.clear_selected_objects()
    result = 1
    rig = chr_cache.get_armature()
    utils.log_always("Attemping to parent the Body mesh to the Face Rig:")
    utils.log_always("If this fails, the face rig may not work and will need to re-parented by other means.")
    for obj in chr_cache.get_cache_objects():
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and not obj_cache.disabled:
            if utils.object_exists_is_mesh(obj) and len(obj.data.vertices) >= 2 and is_face_object(obj_cache, obj):
                obj_result = try_parent_auto(chr_cache, rig, obj)
                if obj_result < result:
                    result = obj_result
    return result


def attempt_reparent_voxel_skinning(chr_cache):
    utils.object_mode()
    utils.clear_selected_objects()
    arm = chr_cache.get_armature()
    face_objects = []
    head = None
    body = None
    dummy_cube = None
    for obj in chr_cache.get_cache_objects():
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and not obj_cache.disabled and obj_cache.is_mesh():
            if obj_cache.object_type == "BODY":
                head = separate_head(obj)
                body = obj
                face_objects.append(head)
            elif is_face_object(obj_cache, obj):
                modifiers.remove_object_modifiers(obj, "ARMATURE")
                face_objects.append(obj)
    if arm and face_objects:
        bpy.ops.mesh.primitive_cube_add(size = 0.1)
        dummy_cube = utils.get_active_object()
        face_objects.append(dummy_cube)
        face_objects.append(arm)
        if utils.try_select_objects(face_objects, True) and utils.set_active_object(arm):
            bpy.data.scenes["Scene"].surface_resolution = 1024
            bpy.data.scenes["Scene"].surface_loops = 5
            bpy.data.scenes["Scene"].surface_samples = 128
            bpy.data.scenes["Scene"].surface_influence = 24
            bpy.data.scenes["Scene"].surface_falloff = 0.2
            bpy.data.scenes["Scene"].surface_sharpness = "1"
            bpy.ops.wm.surface_heat_diffuse()
    return dummy_cube, head, body


def separate_head(body_mesh):
    utils.object_mode()
    utils.clear_selected_objects()
    if utils.edit_mode_to(body_mesh):
        bpy.context.object.active_material_index = 0
        bpy.ops.object.material_slot_select()
        if len(body_mesh.material_slots) == 6:
            bpy.context.object.active_material_index = 5
            bpy.ops.object.material_slot_select()
        bpy.ops.mesh.separate(type="SELECTED")
        utils.object_mode()
        separated_head = None
        for o in bpy.context.selected_objects:
            if o != body_mesh:
                separated_head = o
        return separated_head


def rejoin_head(head_mesh, body_mesh):
    utils.object_mode()
    utils.try_select_objects([body_mesh, head_mesh], True)
    utils.set_active_object(body_mesh)
    bpy.ops.object.join()
    if utils.edit_mode_to(body_mesh):
        bpy.ops.mesh.select_all(action = 'SELECT')
        bpy.ops.mesh.remove_doubles()
    utils.object_mode()


# Animation Retargeting
#
#

def get_bone_name_regex(rig, pattern):
    if pattern:
        for bone in rig.data.bones:
            if re.match(pattern, bone.name):
                return bone.name
    return None


def get_original_rig_data(rigify_rig, cc3_rig):
    original_rig_data = {}
    for edit_bone in rigify_rig.data.edit_bones:
        if "orig_name" in edit_bone and "orig_dir" in edit_bone and "orig_z_axis" in edit_bone:
            orig_name = edit_bone["orig_name"]

            if orig_name not in cc3_rig.data.bones:
                find_name = bones.find_target_bone_name(cc3_rig, orig_name)
                if find_name:
                    orig_name = find_name
                else:
                    utils.log_error(f"Unable to find cc3 bone: {orig_name}")
                    continue
            orig_dir = edit_bone["orig_dir"]
            orig_z_axis = edit_bone["orig_z_axis"]
            original_rig_data[orig_name] = [Vector(orig_dir),
                                            Vector(orig_z_axis),
                                            rigify_rig.matrix_world @ edit_bone.head,
                                            rigify_rig.matrix_world @ edit_bone.tail]
    return original_rig_data


def generate_retargeting_rig(chr_cache, source_rig, rigify_rig, retarget_data, to_original_rig=False):

    utils.unhide(source_rig)
    source_rig.data.pose_position = "POSE"
    utils.unhide(rigify_rig)
    rigify_rig.data.pose_position = "POSE"

    retarget_rig = bpy.data.objects.new(chr_cache.character_name + "_Retarget", bpy.data.armatures.new(chr_cache.character_name + "_Retarget"))
    bpy.context.collection.objects.link(retarget_rig)
    if retarget_rig:

        ORG_BONES = {}
        RIGIFY_BONES = {}
        eyes_distance = 0.5
        face_pos = None
        eyes_pos = None
        original_rig_data = {}

        # scan the rigify rig for origin bones
        #
        # store all the bone details from the ORG bones to reconstruct the origin rig.
        # in some cases new ORG bones are created to act as parents or animation targets from the source.
        # this way if the Rigify rig is not complex enough, the retarget rig can be made to better match the source armature.
        if rigutils.edit_rig(rigify_rig):

            if to_original_rig:
                original_rig_data = get_original_rig_data(rigify_rig, source_rig)

            for retarget_def in retarget_data.retarget:
                org_bone_name = retarget_def[0]
                if not org_bone_name or org_bone_name in ORG_BONES:
                    # don't process the same ORG bone more than once
                    continue

                org_parent_bone_name = retarget_def[1]
                utils.log_info(f"Generating retarget ORG bone: {org_bone_name}")
                flags = retarget_def[4]
                head_pos = rigify_rig.matrix_world @ Vector((0,0,0))
                tail_pos = rigify_rig.matrix_world @ Vector((0,0,0.01))
                parent_pos = rigify_rig.matrix_world @ Vector((0,0,0))
                use_connect = False
                use_inherit_rotation = True
                use_local_location = True
                inherit_scale = "FULL"

                # fetch the bone head and tail positions
                if "+" in flags:
                    ref_bone_name = retarget_def[5]
                    if ref_bone_name and ref_bone_name.startswith("rigify:"):
                        ref_bone = bones.get_edit_bone(rigify_rig, ref_bone_name[7:])
                        if ref_bone:
                            head_pos = rigify_rig.matrix_world @ ref_bone.head
                            tail_pos = rigify_rig.matrix_world @ ref_bone.tail
                        else:
                            utils.log_error(f"Could not find ref bone: {ref_bone_name} in Rigify rig!")
                else:
                    org_bone = bones.get_edit_bone(rigify_rig, org_bone_name)
                    if org_bone:
                        head_pos = rigify_rig.matrix_world @ org_bone.head
                        tail_pos = rigify_rig.matrix_world @ org_bone.tail
                    else:
                        utils.log_error(f"Could not find ORG bone: {org_bone_name} in Rigify rig!")

                # find parent bone
                org_parent_bone = None
                if org_parent_bone_name:
                    org_parent_bone = bones.get_edit_bone(rigify_rig, org_parent_bone_name)
                    if org_parent_bone:
                        parent_pos = rigify_rig.matrix_world @ org_parent_bone.head
                    elif org_parent_bone_name in ORG_BONES:
                        parent_pos = ORG_BONES[org_parent_bone_name][1]
                    else:
                        utils.log_error(f"Could not find parent bone: {org_parent_bone_name} in Rigify rig or ORG bones!")
                        org_parent_bone_name = ""

                # get the scale of the bone as the distance from it's parent head position
                length = (head_pos - parent_pos).length
                if length <= 0.00001:
                    length = 1

                # parent retarget correction, add corrective parent pivot bone and insert into parent chain
                if "P" in flags or "T" in flags:
                    pivot_bone_name = org_bone_name + "_pivot"
                    utils.log_info(f"Adding parent correction pivot: {pivot_bone_name} -> {org_bone_name}")
                    ORG_BONES[pivot_bone_name] = [org_parent_bone_name,
                            head_pos, tail_pos, parent_pos,
                            use_connect,
                            use_local_location,
                            use_inherit_rotation,
                            inherit_scale,
                            length]
                    org_parent_bone_name = pivot_bone_name

                # store the face position for eye control constraints later
                if org_bone_name == "ORG-face":
                    face_pos = head_pos

                ORG_BONES[org_bone_name] = [org_parent_bone_name,
                            head_pos, tail_pos, parent_pos,
                            use_connect,
                            use_local_location,
                            use_inherit_rotation,
                            inherit_scale,
                            length]

            # finally build a list of target control bones
            for retarget_def in retarget_data.retarget:
                org_bone_name = retarget_def[0]
                rigify_bone_name = retarget_def[3]
                if rigify_bone_name and org_bone_name:
                    if org_bone_name in ORG_BONES and rigify_bone_name not in RIGIFY_BONES:
                        rigify_bone = bones.get_edit_bone(rigify_rig, rigify_bone_name)
                        if rigify_bone:
                            head_pos = rigify_rig.matrix_world @ rigify_bone.head
                            tail_pos = rigify_rig.matrix_world @ rigify_bone.tail
                            if rigify_bone.name == "eyes":
                                eyes_pos = head_pos.copy()
                            RIGIFY_BONES[rigify_bone_name] = [org_bone_name,
                                                            head_pos, tail_pos,
                                                            rigify_bone.roll, rigify_bone.use_connect,
                                                            rigify_bone.use_local_location,
                                                            rigify_bone.use_inherit_rotation,
                                                            rigify_bone.inherit_scale]
                        else:
                            utils.log_warn(f"Could not find Rigify bone: {rigify_bone_name} in Rigify rig!")

        # scan the source rig
        #
        if rigutils.edit_rig(source_rig):
            for retarget_def in retarget_data.retarget:
                source_bone_regex = retarget_def[2]
                org_bone_name = retarget_def[0]
                org_bone_def = None
                if org_bone_name in ORG_BONES:
                    org_bone_def = ORG_BONES[org_bone_name]
                flags = retarget_def[4]
                if source_bone_regex and org_bone_def:

                    # fetch the size of the source bones (for translation retargetting)
                    if len(org_bone_def) == 9: # only append z_axis and scale once.
                        source_bone_name = get_bone_name_regex(source_rig, source_bone_regex)
                        source_bone = bones.get_edit_bone(source_rig, source_bone_name)
                        z_axis = source_rig.matrix_world @ Vector((0,0,1))
                        length = 1.0
                        if source_bone:
                            head_pos = source_rig.matrix_world @ source_bone.head
                            tail_pos = source_rig.matrix_world @ source_bone.tail

                            z_axis = None
                            if to_original_rig:
                                z_axis = original_rig_data[source_bone_name][1]
                            else:
                                # z-axis is in local space, we wan't it in world space for the retarget rig
                                z_axis = source_rig.matrix_world @ source_bone.z_axis
                            if not z_axis:
                                utils.log_error(f"unable to find source align vector: {source_bone_name}")
                                z_axis = Vector((0,-1,0))

                            # find the source bone equivalent to the ORG bones parent
                            parent_pos = source_rig.matrix_world @ Vector((0,0,0))
                            org_parent_bone_name = retarget_def[1]
                            for parent_retarget_def in retarget_data.retarget:
                                parent_org_bone_name = parent_retarget_def[0]
                                if parent_org_bone_name == org_parent_bone_name:
                                    source_parent_bone_regex = parent_retarget_def[2]
                                    if source_parent_bone_regex:
                                        source_parent_bone_name = get_bone_name_regex(source_rig, source_parent_bone_regex)
                                        source_parent_bone = bones.get_edit_bone(source_rig, source_parent_bone_name)
                                        if source_parent_bone:
                                            parent_pos = source_rig.matrix_world @ source_parent_bone.head
                                        break
                            else:
                                if source_bone.parent:
                                    parent_pos = source_rig.matrix_world @ source_bone.parent.head
                            dir = head_pos - parent_pos
                            dir.x /= source_rig.scale.x
                            dir.y /= source_rig.scale.y
                            dir.z /= source_rig.scale.z
                            length = dir.length
                            if length <= 0.00001: length = 1
                        else:
                            utils.log_error(f"Could not find source bone: {source_bone_name} in source rig!")
                        org_bone_def.append(length) # [9]
                        org_bone_def.append(z_axis) # [10]
                        if ("P" in flags or "T" in flags) and org_bone_name + "_pivot" in ORG_BONES:
                            pivot_org_bone_def = ORG_BONES[org_bone_name + "_pivot"]
                            pivot_org_bone_def.append(length) # [9]
                            pivot_org_bone_def.append(z_axis) # [10]
                else:
                    utils.log_error(f"Could not find ORG bone: {org_bone_name} in ORG_BONES!")

                # process special flags
                pidx = 5
                for f in flags:
                    if f == "C" or f == "M" or f == "I":
                        pidx += 1
                    # handle source bone copy (and re-calculate scale)
                    if f == "+":
                        if org_bone_name in ORG_BONES:
                            ref_bone_name = retarget_def[pidx]
                            pidx += 1
                            if ref_bone_name and ref_bone_name.startswith("source:"):
                                ref_bone_name = get_bone_name_regex(source_rig, ref_bone_name[7:])
                                ref_bone = bones.get_edit_bone(source_rig, ref_bone_name)
                                if ref_bone:
                                    # these need to be in world space
                                    head_pos = source_rig.matrix_world @ ref_bone.head
                                    tail_pos = source_rig.matrix_world @ ref_bone.tail
                                    parent_pos = org_bone_def[3].copy()
                                    length = (head_pos - parent_pos).length
                                    if length <= 0.00001:
                                        length = 1
                                    ORG_BONES[org_bone_name][1] = head_pos
                                    ORG_BONES[org_bone_name][2] = tail_pos
                                    ORG_BONES[org_bone_name][8] = length
                                else:
                                    utils.log_error(f"Could not find ref bone: {ref_bone_name} in source rig!")

                    # handle parent retarget correction:
                    # when the source bone is not in the same orientation as the ORG bone
                    # we need to parent the ORG bone to a copy of the source bone -
                    # except if we are using the original axes (invalid or same source bind pose)
                    if f == "P" or f == "T":
                        if org_bone_name + "_pivot" in ORG_BONES:
                            pivot_org_bone_def = ORG_BONES[org_bone_name + "_pivot"]
                        source_bone_name = get_bone_name_regex(source_rig, source_bone_regex)
                        source_bone = bones.get_edit_bone(source_rig, source_bone_name)
                        if source_bone and org_bone_def and pivot_org_bone_def:
                            if to_original_rig:
                                orig_dir, orig_z_axis, orig_head, orig_tail = original_rig_data[source_bone_name]
                                source_head = orig_head.copy()
                                source_tail = orig_head + orig_dir
                                source_dir = orig_dir.copy()
                                head_position = org_bone_def[1].copy()
                            else:
                                source_head = source_rig.matrix_world @ source_bone.head
                                source_tail = source_rig.matrix_world @ source_bone.tail
                                source_dir = source_tail - source_head
                                head_position = org_bone_def[1].copy()

                            if "t" in flags: # put the pivot at the tail
                                head_position = org_bone_def[2].copy()

                            if "V" in flags: # reverse the source_dir
                                source_dir = -source_dir

                            if f == "T": # alignment correction
                                # optional orientation adjusted by the relative rotational difference between the
                                # ORG bone and the *real* direction of the source bone which is the direction to
                                # the next/child bone specified in the parameters.
                                next_bone_name = retarget_def[pidx]
                                pidx += 1
                                use_tail = False
                                if not next_bone_name or next_bone_name == "-":
                                    use_tail = True
                                    next_bone_name = source_bone_name
                                next_bone_name = get_bone_name_regex(source_rig, next_bone_name)
                                next_bone = bones.get_edit_bone(source_rig, next_bone_name)
                                if use_tail:
                                    next_pos = source_rig.matrix_world @ next_bone.tail
                                else:
                                    next_pos = source_rig.matrix_world @ next_bone.head
                                next_bone_dir = next_pos - source_head
                                if source_dir.dot(next_bone_dir) < 0.99:
                                    org_bone_dir = org_bone_def[2] - org_bone_def[1]
                                    rot = next_bone_dir.rotation_difference(org_bone_dir)
                                    source_dir = rot @ source_dir

                            # update the pivot bone def with the new orientation
                            pivot_org_bone_def[1] = head_position.copy()
                            pivot_org_bone_def[2] = head_position + source_dir


        # ORG_BONES = { org_bone_name: [0:parent_name, 1:world_head_pos, 2:world_tail_pos, 3:parent_pos, 4:is_connected,
        #                               5:inherit_location, 6:inherit_rotation, 7:inherit_scale, 8:target_size,
        #    (optional if source_bone)  9:source_size, 10:source_bone_z_axis], }
        #
        # RIGIFY_BONES = { bone_name: [0:equivalent_org_bone_name, 1:world_head_pos, 2:world_tail_pos, 3:bone_roll,
        #                              4:is_connected, 5:inherit_location, 6:inherit_rotation, 7:inherit_scale], }

        # determine the distance for the eyes control
        if face_pos and eyes_pos:
            eyes_distance = (eyes_pos - face_pos).length

        # build the retargeting rig:
        #
        if rigutils.edit_rig(retarget_rig):

            # add the org bones:
            for org_bone_name in ORG_BONES:
                bone_def = ORG_BONES[org_bone_name]
                utils.log_info(f"Building: {org_bone_name}")
                b = retarget_rig.data.edit_bones.new(org_bone_name)
                b.head = bone_def[1]
                b.tail = bone_def[2]

                # very important to align the roll of the source and ORG bones.
                if len(bone_def) >= 11:
                    utils.log_info(f"Aligning bone roll: {org_bone_name}")
                    b.align_roll(bone_def[10])
                else:
                    utils.log_warn(f"Bone roll axis not stored for {org_bone_name}")

                b.use_connect = bone_def[4]
                b.use_local_location = bone_def[5]
                b.use_inherit_rotation = bone_def[6]
                b.inherit_scale = bone_def[7]

            # set the org bone parents:
            for org_bone_name in ORG_BONES:
                bone_def = ORG_BONES[org_bone_name]
                b = bones.get_edit_bone(retarget_rig, org_bone_name)
                b.parent = bones.get_edit_bone(retarget_rig, bone_def[0])

            # add the rigify control rig bones we want to retarget to:
            for rigify_bone_name in RIGIFY_BONES:
                utils.log_info(f"Adding Rigify target control bone {rigify_bone_name}")
                bone_def = RIGIFY_BONES[rigify_bone_name]
                b = retarget_rig.data.edit_bones.new(rigify_bone_name)
                b.parent = bones.get_edit_bone(retarget_rig, bone_def[0])
                b.head = bone_def[1]
                b.tail = bone_def[2]
                b.roll = bone_def[3]
                b.use_connect = False
                b.use_local_location = bone_def[5]
                b.use_inherit_rotation = bone_def[6]
                b.inherit_scale = "FULL"

            # add the correction control bones
            for correction_bone_name in retarget_data.retarget_corrections:
                correction_def = retarget_data.retarget_corrections[correction_bone_name]
                bone_def = correction_def["bone"]
                b = retarget_rig.data.edit_bones.new(correction_bone_name)
                b.head = bone_def[0]
                b.tail = bone_def[1]
                b.roll = 0

            # v2 correction control bones
            if False:
                for retarget_def in retarget_data.retarget:
                    org_bone_name = retarget_def[0]
                    org_parent_bone_name = retarget_def[1]
                    if org_bone_name[:3] == "ORG":
                        correction_bone_name = "COR" + org_bone_name[3:]
                        correction_parent_bone_name = "COR" + org_parent_bone_name[3:]
                        if (org_bone_name in retarget_rig.data.edit_bones and
                            correction_bone_name not in retarget_rig.data.edit_bones):
                            org_bone = bones.get_edit_bone(retarget_rig, org_bone_name)
                            correction_bone = bones.copy_edit_bone(retarget_rig, org_bone_name,
                                                    correction_bone_name, correction_parent_bone_name, 1.0)
                            correction_bone.layers[2] = True
                            CORRECTION_BONES[correction_bone_name] = [org_bone_name, org_parent_bone_name,
                                                                    correction_parent_bone_name]

        # constrain the retarget rig
        #
        if rigutils.select_rig(retarget_rig):

            # check for missing bones
            for rigify_bone_name in RIGIFY_BONES:
                if rigify_bone_name not in retarget_rig.pose.bones:
                    utils.log_error(f"{rigify_bone_name} missing from Retarget Rig!")

            # add all contraints to/from the retarget rig
            for retarget_def in retarget_data.retarget:
                org_bone_name = retarget_def[0]
                source_bone_name = get_bone_name_regex(source_rig, retarget_def[2])
                rigify_bone_name = retarget_def[3]
                flags = retarget_def[4]
                if "P" in flags or "T" in flags:
                    org_bone_name = org_bone_name + "_pivot"
                pidx = 5
                source_bone = bones.get_pose_bone(source_rig, source_bone_name)
                org_bone = bones.get_pose_bone(retarget_rig, org_bone_name)
                rigify_bone = bones.get_pose_bone(retarget_rig, rigify_bone_name)
                org_bone_def = None
                if org_bone:
                    org_bone_def = ORG_BONES[org_bone_name]
                if org_bone and source_bone and org_bone_def:
                    influence = 1.0
                    if "I" in flags:
                        influence = retarget_def[pidx]
                        pidx += 1
                    # source copy
                    if "N" not in flags:
                        scale_influence = 1.0
                        axes = None
                        if len(org_bone_def) >= 11:
                            scale_influence = org_bone_def[8] / org_bone_def[9]
                            scale_influence = max(0.0, min(1.0, scale_influence))
                        if to_original_rig:
                            space = "WORLD"
                            scale_influence = 1.0
                            influence = 1.0
                        elif org_bone_name == "root":
                            space = "WORLD"
                            axes = "Z"
                        elif org_bone_name == "ORG-hip" or org_bone_name == "ORG-hip_pivot":
                            space = "LOCAL_WITH_PARENT"
                        else:
                            space = "LOCAL"
                            if utils.B310():
                                space = "LOCAL_OWNER_ORIENT"
                        bones.add_copy_location_constraint(source_rig, retarget_rig, source_bone_name, org_bone_name, scale_influence * influence, space=space, axes=axes)
                        bones.add_copy_rotation_constraint(source_rig, retarget_rig, source_bone_name, org_bone_name, influence)
                        if not to_original_rig and org_bone_name == "root":
                            bones.add_copy_location_constraint(retarget_rig, retarget_rig, "ORG-hip", org_bone_name, 1.0, "WORLD", axes="XY")

                if rigify_bone:
                    for f in flags:

                        # add new ORG bone (not handled here, but increment the parameter index)
                        if f == "+":
                            pidx += 1

                        # parent with align correction (not handled here, but increment the parameter index)
                        if f == "T":
                            pidx += 1

                        # copy bone (not handled here, but increment the parameter index)
                        if f == "C":
                            pidx += 1

                        # copy location to target
                        if f == "L":
                            bones.add_copy_location_constraint(retarget_rig, rigify_rig, rigify_bone_name, rigify_bone_name, 1.0)

                        # copy rotation to target
                        if f == "R":
                            bones.add_copy_rotation_constraint(retarget_rig, rigify_rig, rigify_bone_name, rigify_bone_name, 1.0)

                        if f == "S":
                            bones.add_copy_scale_constraint(retarget_rig, rigify_rig, rigify_bone_name, rigify_bone_name, 1.0)

                        # average bone copy (in retarget rig)
                        if f == "A":
                            bone_1_name = retarget_def[pidx]
                            pidx += 1
                            bone_2_name = retarget_def[pidx]
                            pidx += 1
                            bone_1 = bones.get_pose_bone(retarget_rig, bone_1_name)
                            bone_2 = bones.get_pose_bone(retarget_rig, bone_2_name)
                            if bone_1 and bone_2:
                                bones.add_copy_location_constraint(retarget_rig, retarget_rig, bone_1.name, rigify_bone_name, 1.0)
                                bones.add_copy_rotation_constraint(retarget_rig, retarget_rig, bone_1.name, rigify_bone_name, 1.0)
                                bones.add_copy_location_constraint(retarget_rig, retarget_rig, bone_2.name, rigify_bone_name, 0.5)
                                bones.add_copy_rotation_constraint(retarget_rig, retarget_rig, bone_2.name, rigify_bone_name, 0.5)
                            else:
                                utils.log_warn(f"Unable to find: {bone_1_name} and/or {bone_2_name} in retarget rig!")

                        # limit distance contraint
                        if f == "D":
                            limit_bone_name = retarget_def[pidx]
                            pidx += 1
                            limit_bone = bones.get_pose_bone(retarget_rig, limit_bone_name)
                            if limit_bone:
                                bones.add_limit_distance_constraint(retarget_rig, retarget_rig, limit_bone.name, rigify_bone_name, eyes_distance, 1.0)
                            else:
                                utils.log_warn(f"Unable to find: {limit_bone_name} in retarget rig!")

                        # clone position
                        if f == "M":
                            target_bone_name = retarget_def[pidx]
                            pidx += 1
                            head_tail = 0.0
                            if target_bone_name[0] == "-":
                                head_tail = 1.0
                                target_bone_name = target_bone_name[1:]
                            target_bone = bones.get_pose_bone(retarget_rig, target_bone_name)
                            if target_bone:
                                con = bones.add_copy_location_constraint(retarget_rig, retarget_rig, target_bone_name, rigify_bone_name, 1.0)
                                if con:
                                    con.head_tail = head_tail
                            else:
                                utils.log_warn(f"Unable to find: {target_bone_name} in retarget rig!")

            # constraints and drivers for corrective bones
            #
            # v2 system...
            if False:
                for correction_bone_name in CORRECTION_BONES:
                    cdef = CORRECTION_BONES[correction_bone_name]
                    org_bone_name = cdef[0]
                    org_bone_parent_name = cdef[1]
                    correction_bone_parent_name = cdef[2]
                    space = "LOCAL"
                    if org_bone_name == "ORG-hip":
                        space = "WORLD"
                    bones.add_copy_location_constraint(retarget_rig, retarget_rig, org_bone_name, correction_bone_name, 1, space)
                    bones.add_copy_rotation_constraint(retarget_rig, retarget_rig, org_bone_name, correction_bone_name, 1, space)

            if True:
                for correction_bone_name in retarget_data.retarget_corrections:
                    correction_def = retarget_data.retarget_corrections[correction_bone_name]
                    bone_def = correction_def["bone"]
                    prop_name = bone_def[2]
                    bone_data_path = bone_def[3]
                    bone_data_index = bone_def[4]
                    correction_bone = bones.get_pose_bone(retarget_rig, correction_bone_name)
                    # rotate using Euler coords
                    if correction_bone:
                        correction_bone.rotation_mode = "XYZ"
                    # add drivers for corrective properties
                    bones.add_bone_prop_driver(retarget_rig, correction_bone_name, bone_data_path, bone_data_index, chr_cache, prop_name, prop_name + "_var")
                    # add corrective constraints
                    con_defs = correction_def["constraints"]
                    for con_def in con_defs:
                        org_bone_name, flags, axis = con_def
                        for retarget_def in retarget_data.retarget:
                            if retarget_def[0] == org_bone_name:
                                if "P" in retarget_def[4]:
                                    org_bone_name = org_bone_name + "_pivot"
                                break
                        pose_bone = bones.get_rl_pose_bone(retarget_rig, org_bone_name)
                        if pose_bone:
                            con : bpy.types.CopyLocationConstraint = None
                            space = "WORLD"
                            if "_LOCAL" in flags:
                                space = "LOCAL"
                                if utils.B310():
                                    space = "LOCAL_OWNER_ORIENT"
                            if "ROT_" in flags:
                                con = bones.add_copy_rotation_constraint(retarget_rig, retarget_rig, correction_bone_name, org_bone_name, 1.0, space)
                            if "LOC_" in flags:
                                con = bones.add_copy_location_constraint(retarget_rig, retarget_rig, correction_bone_name, org_bone_name, 1.0, space)
                            if con:
                                if "_ADD_" in flags:
                                    con.mix_mode = "ADD"
                                if "_OFF_" in flags:
                                    con.use_offset = True
                                con.use_x = "X" in axis
                                con.use_y = "Y" in axis
                                con.use_z = "Z" in axis
                                con.invert_x = "-X" in axis
                                con.invert_y = "-Y" in axis
                                con.invert_z = "-Z" in axis

        rigutils.select_rig(retarget_rig)

    retarget_rig.data.display_type = "STICK"
    return retarget_rig


def adv_retarget_remove_pair(op, chr_cache):
    props = vars.props()
    rigify_rig = chr_cache.get_armature()
    retarget_rig = chr_cache.rig_retarget_rig

    # remove all contraints on Rigify control bones
    if utils.object_exists(rigify_rig):
        utils.unhide(rigify_rig)
        if rigutils.select_rig(rigify_rig):
            for rigify_bone_name in rigify_mapping_data.RETARGET_RIGIFY_BONES:
                bones.clear_constraints(rigify_rig, rigify_bone_name)

    # remove the retarget rig
    if utils.object_exists(retarget_rig):
        utils.unhide(retarget_rig)
        utils.delete_armature_object(retarget_rig)
    chr_cache.rig_retarget_rig = None
    chr_cache.rig_retarget_source_rig = None
    utils.try_select_object(rigify_rig, True)
    utils.set_active_object(rigify_rig)
    utils.object_mode()

    # clear any animated shape keys
    reset_shape_keys(chr_cache)


def adv_preview_retarget(op, chr_cache):
    props = vars.props()
    prefs = vars.prefs()

    rigify_rig = chr_cache.get_armature()
    source_rig = props.armature_list_object
    source_action = props.action_list_action

    retarget_rig = adv_retarget_pair_rigs(op, chr_cache)
    if retarget_rig and source_action:
        start_frame = int(source_action.frame_range[0])
        end_frame = int(source_action.frame_range[1])
        bpy.context.scene.frame_start = start_frame
        bpy.context.scene.frame_end = end_frame

        if prefs.rigify_preview_shape_keys:
            adv_retarget_shape_keys(op, chr_cache)


def adv_retarget_pair_rigs(op, chr_cache, rig_override=None, action_override=None, to_original_rig=False):
    props = vars.props()
    rigify_rig = chr_cache.get_armature()
    if rig_override:
        source_rig = rig_override
        source_action = utils.safe_get_action(source_rig)
    else:
        source_rig = props.armature_list_object
        source_action = props.action_list_action
        utils.safe_set_action(source_rig, source_action)
    if action_override:
        source_action = action_override
        utils.safe_set_action(source_rig, source_action)

    if not source_rig:
        if op: op.report({'ERROR'}, "No source Armature!")
        return None
    if not rigify_rig:
        if op: op.report({'ERROR'}, "No Rigify Armature!")
        return None
    if not rigutils.is_rigify_armature(rigify_rig):
            if op: op.report({'ERROR'}, "Character Armature is not a Rigify armature!")
            return None
    if not rig_override:
        if not source_action:
            if op: op.report({'ERROR'}, "No Source Action!")
            return None
        if not check_armature_action(source_rig, source_action):
            if op: op.report({'ERROR'}, "Source Action does not match Source Armature!")
            return None

    source_type, source_label = rigutils.get_armature_action_source_type(source_rig, source_action)
    retarget_data = rigify_mapping_data.get_retarget_for_source(source_type)

    if not retarget_data:
        if op: op.report({'ERROR'}, f"Retargeting from {source_type} not supported!")
        return None

    olc = utils.set_active_layer_collection_from(rigify_rig)

    adv_retarget_remove_pair(op, chr_cache)

    temp_collection = utils.force_visible_in_scene("TMP_Retarget", source_rig, rigify_rig)

    utils.reset_object_transform(rigify_rig)
    utils.reset_object_transform(source_rig)

    utils.delete_armature_object(chr_cache.rig_retarget_rig)
    retarget_rig = generate_retargeting_rig(chr_cache, source_rig, rigify_rig,
                                            retarget_data, to_original_rig=to_original_rig)
    chr_cache.rig_retarget_rig = retarget_rig
    chr_cache.rig_retarget_source_rig = source_rig
    rigutils.select_rig(rigify_rig)
    try:
        #rigify_rig.pose.bones["upper_arm_parent.L"]["IK_FK"] = 1.0
        #rigify_rig.pose.bones["upper_arm_parent.R"]["IK_FK"] = 1.0
        #rigify_rig.pose.bones["thigh_parent.L"]["IK_FK"] = 1.0
        #rigify_rig.pose.bones["thigh_parent.R"]["IK_FK"] = 1.0
        retarget_rig.data.display_type = "STICK"
    except:
        pass

    utils.restore_visible_in_scene(temp_collection)

    utils.set_active_layer_collection(olc)

    utils.hide(retarget_rig)

    return retarget_rig


def full_retarget_source_rig_action(op, chr_cache, src_rig=None, src_action=None,
                                    use_ui_options=True):
    prefs = vars.prefs()
    props = vars.props()

    # if nothing supplied, use the selected rig and action from the rigify panel
    if not src_action and not src_rig:
        src_rig = props.armature_list_object
        src_action = props.action_list_action
    # if only the rig not supplied, use the selected rig from the rigify panel
    elif not src_rig and src_action:
        src_rig = props.armature_list_object
    # if no action supplied, get the action from the source rig
    elif src_rig and not src_action:
        src_action = utils.safe_get_action(src_rig)

    rigify_rig = chr_cache.get_armature()

    if rigify_rig and src_rig and src_action:
        armature_action = adv_bake_retarget_to_rigify(op, chr_cache,
                                        src_rig, src_action)[0]
        key_actions = adv_retarget_shape_keys(op, chr_cache,
                                        src_rig, src_action,
                                        copy=True)
        utils.log_info(f"Armature and shape key actions retargeted:")
        # assign names and set data
        rig_id = rigutils.get_rig_id(rigify_rig)
        rl_arm_id = utils.get_rl_object_id(rigify_rig)
        motion_prefix = rigutils.get_motion_prefix(src_action)
        custom_prefix = props.rigify_retarget_motion_prefix.strip()
        if use_ui_options and custom_prefix:
            motion_prefix = custom_prefix
        motion_id = rigutils.get_action_motion_id(src_action, "Retarget")
        motion_id = rigutils.get_unique_set_motion_id(rig_id, motion_id, motion_prefix)
        set_id, set_generation = rigutils.generate_motion_set(rigify_rig, motion_id, motion_prefix)
        rigutils.set_armature_action_name(armature_action, rig_id, motion_id, motion_prefix)
        rigutils.add_motion_set_data(armature_action, set_id, set_generation, rl_arm_id=rl_arm_id)
        armature_action.use_fake_user = props.rigify_retarget_use_fake_user if use_ui_options else True
        utils.log_info(f"Renaming armature action to: {armature_action.name}")
        for obj_id, key_action in key_actions.items():
            rigutils.set_key_action_name(key_action, rig_id, motion_id, obj_id, motion_prefix)
            rigutils.add_motion_set_data(key_action, set_id, set_generation, obj_id=obj_id)
            utils.log_info(f"Renaming key action ({obj_id}) to: {key_action.name}")
            key_action.use_fake_user = props.rigify_retarget_use_fake_user if use_ui_options else True


FK_BONE_GROUPS = ["FK", "Special", "Tweak", "Extra", "Root"]
FK_BONE_COLLECTIONS = ["Face", "Face (Primary)", "Face (Secondary)",
                       "Torso", "Torso (Tweak)", "Fingers", "Fingers (Detail)",
                       "Arm.L (FK)", "Arm.L (Tweak)", "Leg.L (FK)", "Leg.L (Tweak)",
                       "Arm.R (FK)", "Arm.R (Tweak)", "Leg.R (FK)", "Leg.R (Tweak)",
                       "Root",
                       "Spring (FK)", "Spring (Tweak)"]

IK_BONE_GROUPS = ["IK", "Special", "Tweak", "Extra", "Root"]
IK_BONE_COLLECTIONS = ["Face", "Face (Primary)", "Face (Secondary)",
                       "Torso", "Torso (Tweak)", "Fingers", "Fingers (Detail)",
                       "Arm.L (IK)", "Arm.L (Tweak)", "Leg.L (IK)", "Leg.L (Tweak)",
                       "Arm.R (IK)", "Arm.R (Tweak)", "Leg.R (IK)", "Leg.R (Tweak)",
                       "Root",
                       "Spring (IK)", "Spring (Tweak)"]

BOTH_BONE_GROUPS = ["FK", "IK", "Special", "Tweak", "Extra", "Root"]
BOTH_BONE_COLLECTIONS = ["Face", "Face (Primary)", "Face (Secondary)",
                         "Torso", "Torso (Tweak)", "Fingers", "Fingers (Detail)",
                         "Arm.L (IK)", "Arm.L (FK)", "Arm.L (Tweak)", "Leg.L (IK)", "Leg.L (FK)", "Leg.L (Tweak)",
                         "Arm.R (IK)", "Arm.R (FK)", "Arm.R (Tweak)", "Leg.R (IK)", "Leg.R (FK)", "Leg.R (Tweak)",
                         "Root",
                         "Spring (IK)", "Spring (FK)", "Spring (Tweak)"]


def adv_bake_retarget_to_rigify(op, chr_cache, source_rig, source_action):
    props = vars.props()
    prefs = vars.prefs()

    rigify_rig = chr_cache.get_armature()
    utils.safe_set_action(source_rig, source_action)

    # generate (or re-use) retargeting rig
    retarget_rig = adv_retarget_pair_rigs(op, chr_cache, rig_override=source_rig, action_override=source_action)

    armature_action = None
    shape_key_actions = None

    if retarget_rig:
        temp_collection = utils.force_visible_in_scene("TMP_Bake_Retarget", source_rig, retarget_rig, rigify_rig)

        rigify_settings = bones.store_armature_settings(rigify_rig)

        BONE_COLLECTIONS = BOTH_BONE_COLLECTIONS
        BONE_GROUPS = BOTH_BONE_GROUPS
        if prefs.rigify_preview_retarget_fk_ik == "FK":
            BONE_COLLECTIONS = FK_BONE_COLLECTIONS
            BONE_GROUPS = FK_BONE_GROUPS
            rigutils.set_rigify_ik_fk_influence(rigify_rig, 1.0)
        elif prefs.rigify_preview_retarget_fk_ik == "IK":
            BONE_COLLECTIONS = IK_BONE_COLLECTIONS
            BONE_GROUPS = IK_BONE_GROUPS
            rigutils.set_rigify_ik_fk_influence(rigify_rig, 0.0)

        # select just the retargeted bones in the rigify rig, to bake:
        if rigutils.select_rig(rigify_rig):
            bones.make_bones_visible(rigify_rig)
            bone : bpy.types.Bone
            for bone in rigify_rig.data.bones:
                bone.select = False
                if bone.name in rigify_mapping_data.RETARGET_RIGIFY_BONES:
                    if bones.is_bone_in_collections(rigify_rig, bone,
                                                    BONE_COLLECTIONS,
                                                    BONE_GROUPS):
                        bone.select = True


            armature_action, shape_key_actions = bake_rig_animation(chr_cache, rigify_rig, source_action,
                                                                    None, True, True, "Retarget")

        # remove retargeting rig
        adv_retarget_remove_pair(op, chr_cache)

        bones.restore_armature_settings(rigify_rig, rigify_settings)

        utils.safe_set_action(rigify_rig, armature_action)

        utils.restore_visible_in_scene(temp_collection)

        return armature_action, shape_key_actions

    return None, None


def adv_bake_NLA_to_rigify(op, chr_cache):
    props = vars.props()
    prefs = vars.prefs()

    rigify_rig = chr_cache.get_armature()
    #utils.safe_set_action(rigify_rig, None)
    #adv_retarget_remove_pair(op, chr_cache)

    armature_action = None
    shape_key_actions = None

    BONE_COLLECTIONS = BOTH_BONE_COLLECTIONS
    BONE_GROUPS = BOTH_BONE_GROUPS
    if prefs.rigify_bake_nla_fk_ik == "FK":
        BONE_COLLECTIONS = FK_BONE_COLLECTIONS
        BONE_GROUPS = FK_BONE_GROUPS
        rigutils.set_rigify_ik_fk_influence(rigify_rig, 1.0)
    elif prefs.rigify_bake_nla_fk_ik == "IK":
        BONE_COLLECTIONS = IK_BONE_COLLECTIONS
        BONE_GROUPS = IK_BONE_GROUPS
        rigutils.set_rigify_ik_fk_influence(rigify_rig, 0.0)

    if rigutils.select_rig(rigify_rig):

        rigify_settings = bones.store_armature_settings(rigify_rig)

        bone : bpy.types.Bone
        bones.make_bones_visible(rigify_rig)
        for bone in rigify_rig.data.bones:
            bone.select = False
            if bones.is_bone_in_collections(rigify_rig, bone,
                                            BONE_COLLECTIONS,
                                            BONE_GROUPS):
                bone.select = True

        shape_key_objects = []
        if prefs.rigify_bake_shape_keys:
            for child in rigify_rig.children:
                if (child.type == "MESH" and
                    child.data.shape_keys and
                    child.data.shape_keys.key_blocks and
                    len(child.data.shape_keys.key_blocks) > 0):
                    shape_key_objects.append(child)

        motion_prefix = props.rigify_bake_motion_prefix.strip()
        motion_id = props.rigify_bake_motion_name.strip()
        if not motion_id:
            motion_id = "NLA_Bake"

        armature_action, shape_key_actions = bake_rig_animation(chr_cache, rigify_rig, None,
                                                                shape_key_objects, False, True, motion_id,
                                                                motion_prefix=motion_prefix)

        armature_action.use_fake_user = props.rigify_bake_use_fake_user
        for key_action in shape_key_actions:
            key_action.use_fake_user = props.rigify_bake_use_fake_user

        bones.restore_armature_settings(rigify_rig, rigify_settings)

        utils.safe_set_action(rigify_rig, armature_action)

        # remove any retarget preview pairing
        adv_retarget_remove_pair(op, chr_cache)




# Shape-key retargeting
#
#


def reset_shape_keys(chr_cache):
    objects = chr_cache.get_all_objects(include_armature=False,
                                        include_children=True,
                                        of_type="MESH")
    utils.reset_shape_keys(objects)


def get_shape_key_name_from_data_path(data_path):
    if data_path.startswith("key_blocks[\""):
        start = data_path.find('"', 0) + 1
        end = data_path.find('"', start)
        return data_path[start:end]
    return None


def match_obj_shape_key_action_name(obj_name, shape_key_actions):
    try_names = [obj_name]
    if "CC_Base_" in obj_name:
        try_names.append("CC_Game_" + obj_name[8:])
        try_names.append(obj_name[8:])
    elif "CC_Game_" in obj_name:
        try_names.append("CC_Base_" + obj_name[8:])
        try_names.append(obj_name[10:])
    for name in try_names:
        if name in shape_key_actions:
            return shape_key_actions[name]
    return None


def adv_retarget_shape_keys(op, chr_cache,
                            source_rig=None, source_action=None,
                            copy=False):
    props = vars.props()
    rigify_rig = chr_cache.get_armature()
    if not source_rig:
        source_rig = props.armature_list_object
    if not source_action:
        source_action = props.action_list_action

    if not source_rig:
        if op: op.report({'ERROR'}, "No source Armature!")
        return
    if not rigify_rig:
        if op: op.report({'ERROR'}, "No Rigify Armature!")
        return
    if not source_action:
        if op: op.report({'ERROR'}, "No Source Action!")
        return
    if not rigutils.is_rigify_armature(rigify_rig):
        if op: op.report({'ERROR'}, "Character Armature is not a Rigify armature!")
        return
    if not check_armature_action(source_rig, source_action):
        if op: op.report({'ERROR'}, "Source Action does not match Source Armature!")
        return

    source_type, source_label = rigutils.get_armature_action_source_type(source_rig, source_action)
    retarget_data = rigify_mapping_data.get_retarget_for_source(source_type)

    if not retarget_data:
        if op: op.report({'ERROR'}, f"Retargeting from {source_type} not supported!")
        return

    source_actions = rigutils.find_source_actions(source_action, source_rig)

    if not source_actions or len(source_actions["keys"]) == 0:
        key_actions = {}
        if op: op.report({'WARNING'}, f"No shape-key actions in source animation!")
    else:
        key_actions = rigutils.apply_source_key_actions(rigify_rig, source_actions,
                                                        all_matching=True, copy=copy,
                                                        motion_id="TEMP", motion_prefix="")
        if op: op.report({'INFO'}, f"Shape-key actions retargeted to character!")

    reset_shape_keys(chr_cache)
    return key_actions


# Unity animation exporting and baking
#
#

def get_extension_export_bones(export_rig):
    accessory_bones = []
    def_bones = []
    for bone in export_rig.data.bones:
        if bone.name.startswith("RLA_") or bone.name.startswith("RLS_") or bone.name.startswith("RL_"):
            accessory_bones.append(bone.name)
            bone_list = bones.get_bone_children(bone, include_root=False)
            for b in bone_list:
                if b.name.startswith("DEF-"):
                    def_bones.append(b.name)
    return accessory_bones, def_bones


def clear_drivers_and_constraints(rig):
    # remove all drivers
    if rigutils.select_rig(rig):
        bones.clear_drivers(rig)

    # remove all constraints
    if rigutils.select_rig(rig):
        for pose_bone in rig.pose.bones:
            bones.clear_constraints(rig, pose_bone.name)
            pose_bone.custom_shape = None


def generate_export_rig(chr_cache, use_t_pose=False, t_pose_action=None,
                        link_target=False, bone_naming="CC"):
    rigify_rig = chr_cache.get_armature()
    export_rig = utils.duplicate_object(rigify_rig)

    vertex_group_map = {}
    accessory_map = {}
    if link_target:
        bone_naming = "LINK"

    if export_rig:
        utils.force_object_name(export_rig, chr_cache.character_name + "_Export")
        utils.force_armature_name(export_rig.data, chr_cache.character_name + "_Export")
    else:
        return None

    # turn all the layers on, otherwise keyframing can fail
    bones.make_bones_visible(export_rig, protected=True)

    # compile a list of all deformation bones
    export_bones = []
    for export_def in rigify_mapping_data.GENERIC_EXPORT_RIG:
        export_bones.append(export_def[0])
    accessory_bones, accessory_def_bones = get_extension_export_bones(export_rig)
    if accessory_bones:
        export_bones.extend(accessory_bones)
    if accessory_def_bones:
        export_bones.extend(accessory_def_bones)

    clear_drivers_and_constraints(export_rig)

    bind_pose_is_a_pose = False
    layer = 0

    utils.object_mode()
    utils.set_mode("EDIT")

    if rigutils.edit_rig(export_rig):

        edit_bones = export_rig.data.edit_bones

        # reparent accessory root bones to the corresponding DEF bone
        # (rigified accessories should normally be parented to ORG bones)
        for bone_name in accessory_bones:
            accessory_bone = edit_bones[bone_name]
            if accessory_bone.parent:
                parent_name = accessory_bone.parent.name
                if parent_name.startswith("ORG-"):
                    parent_name = "DEF-" + parent_name[4:]
                    if parent_name in edit_bones:
                        accessory_bone.parent = edit_bones[parent_name]

        # test for A-pose
        upper_arm_l = edit_bones['DEF-upper_arm.L']
        world_x = Vector((1, 0, 0))
        if world_x.dot(upper_arm_l.y_axis) < 0.9:
            bind_pose_is_a_pose = True

        for export_def in rigify_mapping_data.GENERIC_EXPORT_RIG:
            bone_name = export_def[0]
            parent_name = export_def[1]
            export_name = export_def[2]
            if bone_naming == "METARIG":
                if bone_name == "root": continue
                export_name = bone_name
                if bone_name.startswith("DEF-"):
                    export_name = bone_name[4:]
            elif bone_naming == "RIGIFY":
                if bone_name == "root": continue
                export_name = export_name.replace("CC_Base_", "Rigify_")
            axis = export_def[3]
            flags = export_def[4]
            bone = None
            parent_bone = None

            if bone_name in edit_bones:
                bone = edit_bones[bone_name]
                source_bone = bone

                # assign parent hierachy
                if "P" in flags:
                    parent_bone = edit_bones[parent_name]
                if parent_bone:
                    bone.parent = parent_bone
                if "T" in flags and len(export_def) > 5:
                    copy_name = export_def[5]
                    if copy_name in edit_bones:
                        copy_bone = edit_bones[copy_name]
                        bone.head = copy_bone.head
                        bone.tail = copy_bone.tail
                        bone.roll = copy_bone.roll
                        source_bone = copy_bone

                # set flags
                bones.set_edit_bone_flags(bone, flags, True)

                # align roll
                # Dont do this...
                #bones.align_edit_bone_roll(bone, axis)

                # set layer
                bones.set_bone_collection(export_rig, bone, "Export", None, layer)

                # child source bone for link targetting
                if link_target:
                    if "orig_name" in source_bone:
                        source_name = source_bone["orig_name"]
                        # should match export_name *unless rigify root bone
                        if source_name != export_name and "Rigify_BoneRoot" not in export_name:
                            utils.log_error(f"Export target names do not match: {source_name} !=  {export_name}")
                        source_dir_array = source_bone["orig_dir"]
                        source_axis_array = source_bone["orig_z_axis"]
                        source_dir = Vector(source_dir_array)
                        source_axis = Vector(source_axis_array)
                        export_bone: bpy.types.EditBone = edit_bones.new(export_name)
                        export_bone.head = bone.head
                        export_bone.tail = bone.head + source_dir
                        export_bone.align_roll(source_axis)
                        export_bone.parent = bone
                        export_bones.append(export_name)

        # remove all non-deformation bones
        for edit_bone in edit_bones:
            if edit_bone.name not in export_bones:
                edit_bones.remove(edit_bone)
        if bone_naming == "METARIG" or bone_naming == "RIGIFY":
            if "root" in edit_bones:
                edit_bones.remove(edit_bones["root"])

        # remove the DEF- tag from the accessory bone names (if needed)
        for bone_name in accessory_def_bones:
            if bone_name.startswith("DEF-"):
                export_name = bone_name[4:]
                vertex_group_map[bone_name] = export_name
                accessory_map[bone_name] = export_name
                edit_bones[bone_name].name = bone_name[4:]

        # rename bones for export
        if not link_target:
            for export_def in rigify_mapping_data.GENERIC_EXPORT_RIG:
                bone_name = export_def[0]
                export_name = export_def[2]
                if bone_naming == "METARIG":
                    export_name = bone_name
                    if bone_name.startswith("DEF-"):
                        export_name = bone_name[4:]
                elif bone_naming == "RIGIFY":
                    export_name = export_name.replace("CC_Base_", "Rigify_")
                if export_name != "" and bone_name in edit_bones:
                    vertex_group_map[bone_name] = export_name
                    edit_bones[bone_name].name = export_name

    # set bone layers
    if rigutils.select_rig(export_rig):
        for bone in export_rig.data.bones:
            bones.set_bone_collection(export_rig, bone, "Export", None, layer)

    # reset the pose
    bones.clear_pose(export_rig)

    # Force T-pose
    if use_t_pose and rigutils.pose_rig(export_rig):

        # add t-pose action to armature
        if t_pose_action:
            utils.safe_set_action(export_rig, t_pose_action)

        bones.select_all_bones(export_rig, select=True, clear_active=True)

        if bind_pose_is_a_pose:
            angle = 30.0 * math.pi / 180.0
            if bone_naming == "METARIG":
                left_arm_name = "upper_arm.L"
                right_arm_name = "upper_arm.R"
            elif bone_naming == "RIGIFY":
                left_arm_name = "Rigify_L_Upperarm"
                right_arm_name = "Rigify_R_Upperarm"
            else:
                left_arm_name = "CC_Base_L_Upperarm"
                right_arm_name = "CC_Base_R_Upperarm"
            if left_arm_name in export_rig.pose.bones and right_arm_name in export_rig.pose.bones:
                left_arm_bone : bpy.types.PoseBone = export_rig.pose.bones[left_arm_name]
                right_arm_bone : bpy.types.PoseBone  = export_rig.pose.bones[right_arm_name]
                left_arm_bone.rotation_mode = "XYZ"
                left_arm_bone.rotation_euler = [0,0,angle]
                left_arm_bone.rotation_mode = "QUATERNION"
                right_arm_bone.rotation_mode = "XYZ"
                right_arm_bone.rotation_euler = [0,0,-angle]
                right_arm_bone.rotation_mode = "QUATERNION"

        if t_pose_action:
            # make first keyframe
            bpy.data.scenes["Scene"].frame_current = 1
            bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_LocRot')

            # make a second keyframe
            bpy.data.scenes["Scene"].frame_current = 2
            bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_LocRot')

    # copy constraints for baking animations
    if rigutils.select_rig(export_rig):
        for export_def in rigify_mapping_data.GENERIC_EXPORT_RIG:
            rigify_bone_name = export_def[0]
            export_bone_name = export_def[2]
            if bone_naming == "METARIG":
                export_bone_name = rigify_bone_name
                if rigify_bone_name.startswith("DEF-"):
                    export_bone_name = rigify_bone_name[4:]
            elif bone_naming == "RIGIFY":
                export_bone_name = export_bone_name.replace("CC_Base_", "Rigify_")
            axis = export_def[3]
            flags = export_def[4]
            if export_bone_name == "":
                export_bone_name = rigify_bone_name
            if link_target:
                to_bone_name = rigify_bone_name
            else:
                to_bone_name = export_bone_name
            if "T" in flags and len(export_def) > 5:
                rigify_bone_name = export_def[5]
            bones.add_copy_rotation_constraint(rigify_rig, export_rig, rigify_bone_name, to_bone_name, 1.0)
            bones.add_copy_location_constraint(rigify_rig, export_rig, rigify_bone_name, to_bone_name, 1.0)

        # constraints for accessory/spring bones
        for rigify_bone_name in accessory_map:
            if link_target:
                to_bone_name = rigify_bone_name
            else:
                to_bone_name = accessory_map[rigify_bone_name]
            bones.add_copy_rotation_constraint(rigify_rig, export_rig, rigify_bone_name, to_bone_name, 1.0)
            bones.add_copy_location_constraint(rigify_rig, export_rig, rigify_bone_name, to_bone_name, 1.0)

    return export_rig, vertex_group_map, accessory_map


def get_bake_action(chr_cache):
    """Determines the action that is currently active on the rigify armature.
    """

    rigify_rig = chr_cache.get_armature()
    action = None
    source_type = "NONE"
    rigify_action = utils.safe_get_action(rigify_rig)
    if rigify_action:
        action = rigify_action
        source_type = "RIGIFY"
    # prefer direct retarget bakes
    # (this way it always bakes whatever is currently playing on the Rigify armature)
    retarget_action = utils.safe_get_action(chr_cache.rig_retarget_source_rig)
    if retarget_action:
        action = retarget_action
        source_type = "RETARGET"
    return action, source_type


def adv_bake_rigify_for_export(chr_cache, export_rig, accessory_map):
    props = vars.props()

    armature_action = None
    shape_key_actions = None

    #export_bake_action, export_bake_source_type = get_bake_action(chr_cache)

    # fetch rigify rig
    rigify_rig = chr_cache.get_armature()
    if rigify_rig.animation_data is None:
        rigify_rig.animation_data_create()

    rigify_settings = bones.store_armature_settings(rigify_rig)

    # disable stretch in ik constraints when exporting
    ik_store = rigutils.disable_ik_stretch(rigify_rig)

    if export_rig:
        # select all export rig bones
        if rigutils.select_rig(export_rig):
            bones.make_bones_visible(export_rig)
            for bone in export_rig.data.bones:
                bone.select = True

            # bake the action on the rigify rig into the export rig
            armature_action, shape_key_actions = bake_rig_animation(chr_cache, export_rig, None,
                                                                    None, True, True, "Export")

    # restore ik stretch settings
    rigutils.restore_ik_stretch(ik_store)

    bones.restore_armature_settings(rigify_rig, rigify_settings)

    return armature_action, shape_key_actions


def adv_export_pair_rigs(chr_cache, include_t_pose=False, t_pose_action=None, link_target=False, bone_naming="CC"):
    prefs = vars.prefs()

    # generate export rig
    utils.delete_armature_object(chr_cache.rig_export_rig)
    export_rig, vertex_group_map, accessory_map = generate_export_rig(chr_cache,
                                                                      use_t_pose=include_t_pose,
                                                                      t_pose_action=t_pose_action,
                                                                      link_target=link_target,
                                                                      bone_naming=bone_naming)
    chr_cache.rig_export_rig = export_rig

    return export_rig, vertex_group_map, accessory_map


def prep_rigify_export(chr_cache, bake_animation, baked_actions, include_t_pose = False, objects=None, bone_naming="CC"):
    prefs = vars.prefs()

    rigify_rig = chr_cache.get_armature()
    rigify_rig.location = (0,0,0)
    rigify_rig.rotation_mode = "XYZ"
    rigify_rig.rotation_euler = (0,0,0)

    action_name = "Export_NLA"
    export_bake_action, export_bake_source_type = get_bake_action(chr_cache)
    if export_bake_action:
        action_name = export_bake_action.name.split("|")[-1]

    # create empty T-Pose action
    t_pose_action: bpy.types.Action = None
    if include_t_pose:
        if "0_T-Pose" in bpy.data.actions:
            bpy.data.actions.remove(bpy.data.actions["0_T-Pose"])
        t_pose_action = bpy.data.actions.new("0_T-Pose")

    export_rig, vertex_group_map, accessory_map = adv_export_pair_rigs(chr_cache,
                                                                       include_t_pose=include_t_pose,
                                                                       t_pose_action=t_pose_action,
                                                                       link_target=False,
                                                                       bone_naming=bone_naming)
    export_rig.location = (0,0,0)
    export_rig.rotation_mode = "XYZ"
    export_rig.rotation_euler = (0,0,0)

    if rigutils.select_rig(export_rig):
        export_rig.data.pose_position = "POSE"

        # Clear the NLA track for this rig
        if len(export_rig.animation_data.nla_tracks) == 0:
            track = export_rig.animation_data.nla_tracks.new()
        else:
            track = export_rig.animation_data.nla_tracks[0]
        strips = []
        for strip in track.strips:
            strips.append(strip)
        for strip in strips:
            track.strips.remove(strip)

        if utils.set_mode("POSE"):

            if include_t_pose and t_pose_action:
                # push T-Pose to NLA first
                utils.log_info(f"Adding {t_pose_action.name} to NLA strips")
                track = export_rig.animation_data.nla_tracks[0]
                track.strips.new(t_pose_action.name, int(t_pose_action.frame_range[0]), t_pose_action)
                baked_actions.append(t_pose_action)

            # bake current timeline animation to export rig
            action = None
            if bake_animation:
                utils.log_info(f"Baking NLA timeline to export rig...")
                action, key_actions = adv_bake_rigify_for_export(chr_cache, export_rig, accessory_map)
                action.name = action_name
                baked_actions.append(action)
                export_rig = chr_cache.rig_export_rig

            utils.safe_set_action(export_rig, None)

            # push baked actions to NLA strip
            if bake_animation and action:
                utils.log_info(f"Adding {action.name} to NLA strips")
                track = export_rig.animation_data.nla_tracks.new()
                strip = track.strips.new(action.name, int(action.frame_range[0]), action)
                for key_obj in key_actions:
                    key_action = key_actions[key_obj]
                    utils.log_info(f"Adding {key_action.name} to NLA strips")
                    track = key_obj.data.shape_keys.animation_data.nla_tracks.new()
                    strip = track.strips.new(key_action.name, int(key_action.frame_range[0]), key_action)

            # reparent the child objects to the export rig
            for child in rigify_rig.children:
                if objects and child not in objects:
                    continue
                child.parent = export_rig
                mod = modifiers.get_object_modifier(child, "ARMATURE")
                if mod:
                    mod.object = export_rig
                rename_to_unity_vertex_groups(child, vertex_group_map)

    rigutils.select_rig(export_rig)

    return export_rig, vertex_group_map, t_pose_action


def select_motion_export_objects(objects):
    for obj in objects:
        if obj.type == "ARMATURE":
            utils.try_select_object(obj)
        elif obj.type == "MESH":
            if obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) > 0:
                action = utils.safe_get_action(obj)
                include = False
                if action:
                    # if there is a shape key action on this mesh, include it
                    include = True
                else:
                    # if no action, but shape keys are set, include it
                    for key in obj.data.shape_keys.key_blocks:
                        if key.value != 0.0:
                            include = True
                            break
                if include:
                    utils.try_select_object(obj)


def rename_to_unity_vertex_groups(obj, vertex_group_map):
    for vg in obj.vertex_groups:
        if vg.name in vertex_group_map:
            vg.name = vertex_group_map[vg.name]


def restore_from_unity_vertex_groups(obj, vertex_group_map):
    for vg in obj.vertex_groups:
        for rigify_name in vertex_group_map:
            if vertex_group_map[rigify_name] == vg.name:
                vg.name = rigify_name
                break

    for export_def in rigify_mapping_data.GENERIC_EXPORT_RIG:
        rigify_bone_name = export_def[0]
        unity_bone_name = export_def[2]
        if unity_bone_name in obj.vertex_groups:
            obj.vertex_groups[unity_bone_name].name = rigify_bone_name


def finish_rigify_export(chr_cache, export_rig, export_actions, vertex_group_map, objects = None):
    rigify_rig = chr_cache.get_armature()

    # un-reparent the child objects
    for child in export_rig.children:
        if objects and child not in objects:
            continue
        child.parent = rigify_rig
        mod = modifiers.get_object_modifier(child, "ARMATURE")

        if mod:
            mod.object = rigify_rig

        restore_from_unity_vertex_groups(child, vertex_group_map)

    # remove the baked actions
    if export_actions:
        for action in export_actions:
            bpy.data.actions.remove(action)

    # remove the export rig
    utils.delete_armature_object(export_rig)
    chr_cache.rig_export_rig = None


# Animation baking
#
#

def bake_rig_animation(chr_cache, rig, source_action,
                       shape_key_objects,
                       clear_constraints, limit_view_layer,
                       motion_id="Bake", motion_prefix="",
                       use_random_id=True):
    """Bakes the current animation timeline on the supplied rig.
    """

    armature_action = None
    shape_key_actions = {}

    rig_id = rigutils.get_rig_id(rig)
    motion_id = rigutils.get_unique_set_motion_id(rig_id, motion_id, motion_prefix)

    if utils.try_select_object(rig, True) and utils.set_active_object(rig):
        armature_action_name = rigutils.make_armature_action_name(rig_id, motion_id, motion_prefix)
        utils.log_info(f"Baking to: {armature_action_name}")
        # frame range
        if source_action:
            start_frame = int(source_action.frame_range[0])
            end_frame = int(source_action.frame_range[1])
        else:
            start_frame = int(bpy.context.scene.frame_start)
            end_frame = int(bpy.context.scene.frame_end)
        # turn off character physics
        physics_objects = physics.disable_physics(chr_cache)
        # limit view layer (bakes faster)
        if limit_view_layer:
            tmp_collection, layer_collections, to_hide = utils.limit_view_layer_to_collection("TMP_BAKE", rig, shape_key_objects)

        utils.set_active_object(rig)
        utils.set_mode("POSE")

        # bake
        bpy.ops.nla.bake(frame_start=start_frame,
                         frame_end=end_frame,
                         only_selected=True,
                         visual_keying=True,
                         use_current_action=False,
                         clear_constraints=clear_constraints,
                         clean_curves=False,
                         bake_types={'POSE'})

        # armature action
        baked_action = utils.safe_get_action(rig)
        if baked_action:
            baked_action.name = armature_action_name
            baked_action.use_fake_user = True
            armature_action = baked_action
            utils.log_info(f"Baked armature action: {baked_action.name}")
        # shape key actions
        if shape_key_objects:
            for obj in shape_key_objects:
                obj_id = rigutils.get_action_obj_id(obj)
                baked_action = utils.safe_get_action(obj.data.shape_keys)
                if baked_action:
                    shape_key_action_name = rigutils.make_key_action_name(rig_id, motion_id, obj_id, motion_prefix)
                    baked_action.name = shape_key_action_name
                    baked_action.use_fake_user = True
                    shape_key_actions[obj] = baked_action
                    utils.log_info(f" - Baked shape-key action: {baked_action.name}")
            utils.try_select_objects(shape_key_objects)

        utils.object_mode()

        # restore view layers
        if limit_view_layer:
            utils.restore_limited_view_layers(tmp_collection, layer_collections, to_hide)
        # turn on physics
        physics.enable_physics(chr_cache, physics_objects)

    # return the baked actions
    return armature_action, shape_key_actions


# Helper functions
#
#


def get_rigify_version():
    for mod in addon_utils.modules():
        name = mod.bl_info.get('name', "")
        if name == "Rigify":
            version = mod.bl_info.get('version', (-1, -1, -1))
            return version


def is_rigify_installed():
    context = bpy.context
    if "rigify" in context.preferences.addons.keys():
        return True
    return False


def is_surface_heat_voxel_skinning_installed():
    try:
        bl_options = bpy.ops.wm.surface_heat_diffuse.bl_options
        if bl_options is not None:
            return True
        else:
            return False
    except:
        return False


def unify_cc3_bone_name(name):
    if not name.startswith("CC_Base_"):
        name = "CC_Base_" + name
    return name


def check_armature_action(armature, action):
    total = 0
    matching = 0
    if action.fcurves:
        for fcurve in action.fcurves:
            total += 1
            bone_name = bones.get_bone_name_from_data_path(fcurve.data_path)
            if bone_name and bone_name in armature.data.bones:
                matching += 1
    if total == 0 or matching == 0:
        return False
    return matching > 0






class CC3Rigifier(bpy.types.Operator):
    """Rigify CC3 Character"""
    bl_idname = "cc3.rigifier"
    bl_label = "Character Rigging"
    bl_options = {"REGISTER"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    no_face_rig: bpy.props.BoolProperty(
            name = "No Face Rig",
            default = False,
            options={"HIDDEN"}
        )

    auto_retarget: bpy.props.BoolProperty(
            name = "Auto Retarget Animation",
            default = False,
            options={"HIDDEN"}
        )

    cc3_rig = None
    meta_rig = None
    rigify_rig = None
    auto_weight_failed = False
    auto_weight_report = ""
    rigid_body_systems = {}

    def is_full_face_rig(self, chr_cache):
        return not self.no_face_rig and chr_cache.is_rig_full_face()

    def add_meta_rig(self, chr_cache):

        utils.log_info("Generating Meta-Rig:")
        utils.log_indent()

        if utils.object_mode():
            bpy.ops.object.armature_human_metarig_add()
            self.meta_rig = utils.get_active_object()
            if self.meta_rig is not None:
                utils.log_info("Meta-Rig added.")
                utils.reset_object_transform(self.meta_rig)
                if self.cc3_rig is not None:
                    self.meta_rig.name = f"{self.cc3_rig.name}_metarig"
                    utils.reset_object_transform(self.cc3_rig)
                    self.cc3_rig.data.pose_position = "REST"
                    utils.log_info("Aligning Meta-Rig.")
                    utils.log_indent()
                    self.match_meta_rig(chr_cache)
                    utils.log_recess()
                else:
                    utils.log_error("Unable to locate imported CC3 rig!", self)
            else:
                utils.log_error("Unable to create meta rig!", self)
        else:
            utils.log_error("Not in OBJECT mode!", self)

        utils.log_recess()

    def remove_cc3_rigid_body_systems(self, chr_cache):
        self.rigid_body_systems.clear()
        spring_rig_modes= springbones.get_all_parent_modes(chr_cache, self.cc3_rig)
        for parent_mode in spring_rig_modes:
            spring_rig_name = springbones.get_spring_rig_name(self.cc3_rig, parent_mode)
            spring_rig_prefix = springbones.get_spring_rig_prefix(parent_mode)
            settings = rigidbody.remove_existing_rigid_body_system(self.cc3_rig, spring_rig_prefix, spring_rig_name)
            if settings:
                self.rigid_body_systems[parent_mode] = settings

    def restore_rigify_rigid_body_systems(self, chr_cache):
        for parent_mode in self.rigid_body_systems.keys():
            rig = chr_cache.get_armature()
            spring_rig_name = springbones.get_spring_rig_name(rig, parent_mode)
            spring_rig_prefix = springbones.get_spring_rig_prefix(parent_mode)
            settings = self.rigid_body_systems[parent_mode]
            rigidbody.build_spring_rigid_body_system(chr_cache, spring_rig_prefix, spring_rig_name, settings)

    def generate_meta_rig(self, chr_cache, advanced_mode = False):

        utils.start_timer()

        utils.log_info("")
        utils.log_info("Beginning Meta-Rig Setup:")
        utils.log_info("-------------------------")

        if utils.object_exists_is_armature(self.cc3_rig):

            utils.unhide(self.cc3_rig)

            self.remove_cc3_rigid_body_systems(chr_cache)
            self.add_meta_rig(chr_cache)

            if utils.object_exists_is_armature(self.meta_rig):
                chr_cache.rig_meta_rig = self.meta_rig
                correct_meta_rig(self.meta_rig)

                self.report({'INFO'}, "Meta-rig generated!")

        utils.log_timer("Done Meta-Rig Setup!")

    def match_meta_rig(self, chr_cache):
        """Map the bones of the meta rig to match the CC3 rig.
        """

        relative_coords = {}
        roll_store = {}

        if utils.object_exists_is_armature(self.cc3_rig) and utils.object_exists_is_armature(self.meta_rig):
            utils.unhide(self.cc3_rig)
            utils.unhide(self.meta_rig)
        else:
            return

        if utils.object_exists_is_armature(self.cc3_rig) and rigutils.edit_rig(self.cc3_rig):
            # store all the meta-rig bone roll axes
            store_bone_roll(self.cc3_rig, self.meta_rig, roll_store, self.rigify_data)
            #
            if rigutils.edit_rig(self.meta_rig):
                # remove unnecessary bones
                prune_meta_rig(self.meta_rig)
                # store the relative positions of certain bones (face & heel)
                store_relative_mappings(self.meta_rig, relative_coords)
                # map all CC3 bones to Meta-rig bones
                for bone_mapping in self.rigify_data.bone_mapping:
                    map_bone(self.cc3_rig, self.meta_rig, bone_mapping)
                # determine positions of face bones (eyes, head and teeth)
                map_face_bones(self.cc3_rig, self.meta_rig, self.rigify_data.head_bone)
                # restore and apply the relative positions of certain bones (face & heel)
                restore_relative_mappings(self.meta_rig, relative_coords)
                # fix the jaw pivot
                fix_jaw_pivot(self.cc3_rig, self.meta_rig)
                # map the face rig bones by UV map if possible
                if self.is_full_face_rig(chr_cache):
                    map_uv_targets(chr_cache, self.cc3_rig, self.meta_rig)
                else: # or hide them
                    hide_face_bones(self.meta_rig)
                # restore meta-rig bone roll axes
                restore_bone_roll(self.meta_rig, roll_store)
                # set rigify rig params
                set_rigify_params(self.meta_rig)

    def rigify_meta_rig(self, chr_cache, advanced_mode = False):

        utils.start_timer()

        face_result = -1

        if utils.object_exists_is_armature(self.cc3_rig) and utils.object_exists_is_armature(self.meta_rig):

            utils.unhide(self.cc3_rig)
            utils.unhide(self.meta_rig)

            if utils.object_mode() and utils.try_select_object(self.meta_rig) and utils.set_active_object(self.meta_rig):

                utils.log_info("")
                utils.log_info("Generating Rigify Control Rig:")
                utils.log_info("------------------------------")

                utils.reset_object_transform(self.cc3_rig)
                utils.reset_object_transform(self.meta_rig)

                bpy.ops.pose.rigify_generate()
                self.rigify_rig = utils.get_active_object()

                utils.log_info("")
                utils.log_info("Finalizing Rigify Setup:")
                utils.log_info("------------------------")

                # remove any expression shape key drivers, the rig takes over these.
                drivers.clear_facial_shape_key_bone_drivers(chr_cache)

                if utils.object_exists_is_armature(self.rigify_rig):

                    if self.is_full_face_rig(chr_cache):
                        chr_cache.rigified_full_face_rig = True
                    else:
                        convert_to_basic_face_rig(self.rigify_rig)
                        chr_cache.rigified_full_face_rig = False
                    modify_rigify_controls(self.cc3_rig, self.rigify_rig, self.rigify_data)
                    prep_envelope_deform(self.rigify_rig, self.meta_rig)
                    face_result = reparent_to_rigify(self, chr_cache, self.cc3_rig, self.rigify_rig, self.rigify_data.bone_mapping)
                    acc_vertex_group_map = {}
                    fix_rigify_bones(chr_cache, self.rigify_rig)
                    add_def_bones(chr_cache, self.cc3_rig, self.rigify_rig)
                    add_extension_bones(chr_cache, self.cc3_rig, self.rigify_rig, self.rigify_data.bone_mapping, acc_vertex_group_map)
                    store_source_bone_data(self.cc3_rig, self.rigify_rig, self.rigify_data)
                    rigify_spring_rigs(chr_cache, self.cc3_rig, self.rigify_rig, self.rigify_data.bone_mapping)
                    add_shape_key_drivers(chr_cache, self.rigify_rig)
                    adjust_rigify_constraints(chr_cache, self.rigify_rig)
                    rename_vertex_groups(self.cc3_rig, self.rigify_rig, self.rigify_data.vertex_group_rename, acc_vertex_group_map)
                    clean_up(chr_cache, self.cc3_rig, self.rigify_rig, self.meta_rig, remove_meta = False) #not advanced_mode)
                    #self.restore_rigify_rigid_body_systems(chr_cache)

        utils.log_timer("Done Rigify Process!")

        # keep the meta_rig data
        #chr_cache.rig_meta_rig = None

        if face_result == 1:
            self.report({'INFO'}, "Rigify Complete! No errors detected.")
        elif face_result == 0:
            self.report({'WARNING'}, "Rigify Complete! Some issues with the face rig were detected and fixed automatically. See console log.")
        else:
            self.report({'ERROR'}, "Rigify Incomplete! Face rig weighting Failed! See console log.")


    def re_rigify_meta_rig(self, chr_cache, advanced_mode = False):

        utils.start_timer()

        face_result = -1

        if utils.object_exists_is_armature(self.cc3_rig) and utils.object_exists_is_armature(self.meta_rig):

            utils.unhide(self.cc3_rig)
            utils.unhide(self.meta_rig)

            if utils.object_mode() and utils.try_select_object(self.meta_rig) and utils.set_active_object(self.meta_rig):

                utils.log_info("")
                utils.log_info("Re-generating Rigify Control Rig:")
                utils.log_info("---------------------------------")

                utils.reset_object_transform(self.cc3_rig)
                utils.reset_object_transform(self.meta_rig)

                # regenerating the rig will replace the existing rigify rig
                # so there is no need to reparent anything
                bpy.ops.pose.rigify_generate()
                self.rigify_rig = utils.get_active_object()

                utils.log_info("")
                utils.log_info("Re-finalizing Rigify Setup:")
                utils.log_info("---------------------------")

                # remove any expression shape key drivers, the rig takes over these.
                drivers.clear_facial_shape_key_bone_drivers(chr_cache)

                if utils.object_exists_is_armature(self.rigify_rig):
                    if self.is_full_face_rig(chr_cache):
                        chr_cache.rigified_full_face_rig = True
                    else:
                        convert_to_basic_face_rig(self.rigify_rig)
                        chr_cache.rigified_full_face_rig = False
                    modify_rigify_controls(self.cc3_rig, self.rigify_rig, self.rigify_data)
                    prep_envelope_deform(self.rigify_rig, self.meta_rig)
                    if chr_cache.rigified_full_face_rig:
                        face_result = self.reparent_face_rig(chr_cache)
                    else:
                        face_result = 1
                    acc_vertex_group_map = {}
                    fix_rigify_bones(chr_cache, self.rigify_rig)
                    add_def_bones(chr_cache, self.cc3_rig, self.rigify_rig)
                    add_extension_bones(chr_cache, self.cc3_rig, self.rigify_rig, self.rigify_data.bone_mapping, acc_vertex_group_map)
                    store_source_bone_data(self.cc3_rig, self.rigify_rig, self.rigify_data)
                    rigify_spring_rigs(chr_cache, self.cc3_rig, self.rigify_rig, self.rigify_data.bone_mapping)
                    add_shape_key_drivers(chr_cache, self.rigify_rig)
                    adjust_rigify_constraints(chr_cache, self.rigify_rig)
                    utils.hide(self.cc3_rig)
                    utils.hide(self.meta_rig)

        utils.log_timer("Done Rigify Process!")

        # keep the meta_rig data
        #chr_cache.rig_meta_rig = None

        if face_result == 1:
            self.report({'INFO'}, "Re-Rigify Complete!. No errors.")
        elif face_result == 0:
            self.report({'WARNING'}, "Re-Rigify Complete!. Some issues with the face rig were detected and fixed automatically. See console log.")
        else:
            self.report({'ERROR'}, "Face Re-parent Failed!. See console log.")


    def reparent_face_rig(self, chr_cache):
        lock_non_face_vgroups(chr_cache)
        clean_up_character_meshes(chr_cache)
        result = attempt_reparent_auto_character(chr_cache)
        unlock_vgroups(chr_cache)
        return result


    def execute(self, context):
        props: properties.CC3ImportProps = vars.props()
        prefs = vars.prefs()
        chr_cache = props.get_context_character_cache(context)

        self.cc3_rig = None
        self.meta_rig = None
        self.rigify_rig = None
        self.auto_weight_failed = False
        self.auto_weight_report = ""

        if chr_cache:

            props.store_ui_list_indices()

            if chr_cache.rigified:
                self.cc3_rig = chr_cache.rig_original_rig
                self.rigify_rig = chr_cache.get_armature()
            else:
                self.cc3_rig = chr_cache.get_armature()
                self.rigify_rig = None
            self.meta_rig = chr_cache.rig_meta_rig
            self.rigify_data = chr_cache.get_rig_mapping_data()

            if self.param == "DATALINK_RIGIFY":
                olc = utils.set_active_layer_collection_from(self.cc3_rig)
                self.generate_meta_rig(chr_cache)
                self.rigify_meta_rig(chr_cache)
                utils.set_active_layer_collection(olc)
                full_retarget_source_rig_action(self, chr_cache, self.cc3_rig,
                                                use_ui_options=False)
                rigutils.update_avatar_rig(self.rigify_rig)

            if self.param == "ALL":

                olc = utils.set_active_layer_collection_from(self.cc3_rig)
                self.generate_meta_rig(chr_cache)
                self.rigify_meta_rig(chr_cache)
                utils.set_active_layer_collection(olc)
                if self.auto_retarget or prefs.rigify_auto_retarget:
                    full_retarget_source_rig_action(self, chr_cache, self.cc3_rig,
                                                    use_ui_options=not self.auto_retarget)

            elif self.param == "META_RIG":

                olc = utils.set_active_layer_collection_from(self.cc3_rig)
                self.generate_meta_rig(chr_cache, advanced_mode = True)
                utils.set_active_layer_collection(olc)

            elif self.param == "RIGIFY_META":

                olc = utils.set_active_layer_collection_from(self.cc3_rig)
                self.rigify_meta_rig(chr_cache, advanced_mode = True)
                utils.set_active_layer_collection(olc)

            elif self.param == "RE_RIGIFY_META":

                olc = utils.set_active_layer_collection_from(self.cc3_rig)
                result = self.re_rigify_meta_rig(chr_cache, advanced_mode = True)
                utils.set_active_layer_collection(olc)
                rigutils.update_avatar_rig(self.rigify_rig)

            elif self.param == "REPORT_FACE_TARGETS":

                if bpy.context.selected_objects:
                    obj = rig = None
                    for o in bpy.context.selected_objects:
                        if o.type == "ARMATURE":
                            rig = o
                        elif o.type == "MESH":
                            obj = o
                    if rig and obj:
                        report_uv_face_targets(obj, rig)

            elif self.param == "BUILD_SPRING_RIG":
                rig = chr_cache.get_armature()
                parent_mode = chr_cache.available_spring_rigs
                spring_rig_name = springbones.get_spring_rig_name(rig, parent_mode)
                if spring_rig_name in rig.data.bones:
                    spring_rig_prefix = springbones.get_spring_rig_prefix(parent_mode)
                    rigidbody.remove_existing_rigid_body_system(rig, spring_rig_prefix, spring_rig_name)
                    rigify_spring_rig(chr_cache, chr_cache.get_armature(), parent_mode)
                    springbones.show_spring_bone_rig_layers(chr_cache, rig, True)

            elif self.param == "REMOVE_SPRING_RIG":
                rig = chr_cache.get_armature()
                parent_mode = chr_cache.available_spring_rigs
                spring_rig_name = springbones.get_spring_rig_name(rig, parent_mode)
                if spring_rig_name in rig.data.bones:
                    spring_rig_prefix = springbones.get_spring_rig_prefix(parent_mode)
                    rigidbody.remove_existing_rigid_body_system(rig, spring_rig_prefix, spring_rig_name)
                    #springbones.show_spring_bone_rig_layers(chr_cache, arm, False)
                    derigify_spring_rig(chr_cache, chr_cache.get_armature(), parent_mode)


            elif self.param == "LOCK_NON_FACE_VGROUPS":
                lock_non_face_vgroups(chr_cache)
                self.report({'INFO'}, "Face groups locked!")

            elif self.param == "UNLOCK_VGROUPS":
                unlock_vgroups(chr_cache)
                self.report({'INFO'}, "Groups unlocked!")

            elif self.param == "CLEAN_BODY_MESH":
                clean_up_character_meshes(chr_cache)
                self.report({'INFO'}, "Body Mesh cleaned!")

            elif self.param == "REPARENT_RIG":
                result = attempt_reparent_auto_character(chr_cache)
                if result == 1:
                    self.report({'INFO'}, "Face Re-parent Done!. No errors.")
                elif result == 0:
                    self.report({'WARNING'}, "Face Re-parent Done!. Some issues with the face rig were detected and fixed automatically. See console log.")
                else:
                    self.report({'ERROR'}, "Face Re-parent Failed!. See console log.")

            elif self.param == "REPARENT_RIG_SEPARATE_HEAD_QUICK":
                result = self.reparent_face_rig(chr_cache)
                if result == 1:
                    self.report({'INFO'}, "Face Re-parent Done!. No errors.")
                elif result == 0:
                    self.report({'WARNING'}, "Face Re-parent Done!. Some issues with the face rig were detected and fixed automatically. See console log.")
                else:
                    self.report({'ERROR'}, "Face Re-parent Failed!. See console log.")

            elif self.param == "RETARGET_CC_PAIR_RIGS":
                adv_preview_retarget(self, chr_cache)

            elif self.param == "RETARGET_CC_REMOVE_PAIR":
                adv_retarget_remove_pair(self, chr_cache)

            elif self.param == "RETARGET_CC_BAKE_ACTION":
                full_retarget_source_rig_action(self, chr_cache, use_ui_options=True)

            elif self.param == "NLA_CC_BAKE":
                adv_bake_NLA_to_rigify(self, chr_cache)

            elif self.param == "RETARGET_SHAPE_KEYS":
                adv_retarget_shape_keys(self, chr_cache)

            elif self.param == "SPRING_GROUP_TO_IK":
                group_props_to_value(chr_cache, context.active_pose_bone, "IK_FK", 0.0)
                group_props_to_value(chr_cache, context.active_pose_bone, "SIM", 0.0)

            elif self.param == "SPRING_GROUP_TO_FK":
                group_props_to_value(chr_cache, context.active_pose_bone, "IK_FK", 1.0)
                group_props_to_value(chr_cache, context.active_pose_bone, "SIM", 0.0)

            elif self.param == "SPRING_GROUP_TO_SIM":
                group_props_to_value(chr_cache, context.active_pose_bone, "IK_FK", 1.0)
                group_props_to_value(chr_cache, context.active_pose_bone, "SIM", 1.0)

            props.restore_ui_list_indices()

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "ALL":
            return "Rigify the character, all in one go"

        elif properties.param == "DATALINK_RIGIFY":
            return "Rigify the character and retarget any existing animation on the armature"

        elif properties.param == "META_RIG":
            return "Attach and align the Rigify Meta-rig to the character"

        elif properties.param == "RIGIFY_META":
            return "Generate the Rigify Control rig from the meta-rig and attach to character"

        elif properties.param == "LOCK_NON_FACE_VGROUPS":
            return "Lock all vertex group not part of the Rigify face rig. Also removes the eyes, teeth and jaw bone from the Deformation bones, so they won't affect any custom reparenting"

        elif properties.param == "UNLOCK_VGROUPS":
            return "Unlock all vertex groups and restore the teeth, eyes and jaw deformation bone status"

        elif properties.param == "CLEAN_BODY_MESH":
            return "Removes doubles, deletes loose vertices and edges and removes any degerate mesh elements that could be preventing Blender from Bone Heat Weighting the face mesh to the face rig"

        elif properties.param == "REPARENT_RIG":
            return "Attempt to reparent the Body mesh to the face rig"

        elif properties.param == "REPARENT_RIG_SEPARATE_HEAD_QUICK":
            return "Attempt to re-parent the character's face mesh objects to the Rigify face rig by re-parenting with automatic weights. " + \
                   "Only vertex groups in the face are affected by this reparenting, all others are locked during the process. " + \
                   "Automatic Weights sometimes fails, so if detected some measures are taken to try to clean up the mesh and try again"

        elif properties.param == "BAKE_EXPORT_ANIMATION":
            return "Bake the current timeline to the export rig"

        elif properties.param == "RETARGET_CC_PAIR_RIGS":
            return "Preview the retarget action on the rigify rig, for real time correction or baking to Unity"

        elif properties.param == "RETARGET_CC_REMOVE_PAIR":
            return "Remove retargeting rig and constraints"

        elif properties.param == "RIGIFY_SET_ACTION":
            return "Set the current action on the characters Rigify rig"

        elif properties.param == "RETARGET_CC_BAKE_ACTION":
            return "Bake the selected source action from the selected source armature to the character Rigify Rig."

        elif properties.param == "RETARGET_SHAPE_KEYS":
            return "Attempt to load the shape-key actions from the selected source armature's corresponding shape-key actions onto the current Rigify character."

        elif properties.param == "NLA_CC_BAKE":
            return "Bake the NLA track to the character Rigify Rig using the global scene frame range."

        elif properties.param == "BUILD_SPRING_RIG":
            return "Builds the spring rig controls for the currently selected spring rig"

        elif properties.param == "REMOVE_SPRING_RIG":
            return "Removes the spring rig controls for the currently selected spring rig"

        return "Rigification!"


class CC3RigifierModal(bpy.types.Operator):
    """Rigify CC3 Character Model functions"""
    bl_idname = "cc3.rigifier_modal"
    bl_label = "Rigifier Modal"
    bl_options = {"REGISTER"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    timer = None
    voxel_reparenting = False
    voxel_skinning = False
    voxel_reparenting_finish = False
    voxel_skinning_finish = False
    processing = False
    dummy_cube = None
    head_mesh = None
    body_mesh = None
    chr_cache = None
    objects = []

    def modal(self, context, event):

        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER' and not self.processing:

            if self.voxel_reparenting and self.dummy_cube:
                self.processing = True
                try:
                    if self.dummy_cube.parent is not None:
                        self.voxel_reparenting = False
                        self.voxel_reparenting_finish = True
                except:
                    pass
                self.processing = False
                return {'PASS_THROUGH'}


            if self.voxel_reparenting_finish:
                self.processing = True
                self.voxel_re_parent_end(context)
                self.cancel(context)
                self.processing = False
                return {'FINISHED'}

            if self.voxel_skinning and self.objects:
                self.processing = True
                all_parented = True
                for obj in self.objects:
                    if obj.parent is None:
                        all_parented = False
                if all_parented:
                    self.voxel_skinning = False
                    self.voxel_skinning_finish = True
                self.processing = False
                return {'PASS_THROUGH'}

            if self.voxel_skinning_finish:
                self.processing = True
                self.voxel_heat_skinning_end(context)
                self.cancel(context)
                self.processing = False
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):
        if self.timer is not None:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None
            self.voxel_reparenting = False
            self.voxel_skinning = False
            self.voxel_reparenting_finish = False
            self.voxel_skinning_finish = False
            self.chr_cache = None
            self.objects = []

    def execute(self, context):
        props: properties.CC3ImportProps = vars.props()
        self.chr_cache = props.get_context_character_cache(context)

        if self.chr_cache:

            # get all selected character non-body objects
            self.objects = []
            body_objects = self.chr_cache.get_objects_of_type("BODY")
            for obj in bpy.context.selected_objects:
                if utils.object_exists_is_mesh(obj) and obj not in body_objects:
                    self.objects.append(obj)

            # an alternative to reparent with automatic weights
            # for reparenting body meshes to full rigify rigs
            if self.param == "VOXEL_SURFACE_REPARENT":
                self.voxel_re_parent_start(context)
                return {'RUNNING_MODAL'}

            if self.param == "VOXEL_HEAT_SKINNING":
                self.voxel_heat_skinning_start(context)
                return {'RUNNING_MODAL'}

        return {"FINISHED"}

    def voxel_re_parent_start(self, context):
        lock_non_face_vgroups(self.chr_cache)
        store_non_face_vgroups(self.chr_cache)
        # as we have no way of knowing when the operator finishes, we add
        # a dummy cube (unparented) to the objects being skinned and parented.
        # Since the parenting to the armature is the last thing
        # the voxel skinning operator does, we can watch for that to happen.
        self.dummy_cube, self.head_mesh, self.body_mesh = attempt_reparent_voxel_skinning(self.chr_cache)

        self.voxel_reparenting = True
        bpy.context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(1.0, window = bpy.context.window)

    def voxel_re_parent_end(self, context):
        if self.dummy_cube:
            bpy.data.objects.remove(self.dummy_cube)
            self.dummy_cube = None

        if self.head_mesh and self.body_mesh:
            rejoin_head(self.head_mesh, self.body_mesh)
            self.head_mesh = None
            self.body_mesh = None

        restore_non_face_vgroups(self.chr_cache)
        unlock_vgroups(self.chr_cache)

        arm = self.chr_cache.get_armature()
        if arm and utils.object_mode():
            if utils.try_select_object(arm, True) and utils.set_active_object(arm):
                utils.set_mode("POSE")

        self.chr_cache = None

        self.report({'INFO'}, "Voxel Face Re-parent Done!")

    def voxel_heat_skinning_start(self, context):
        # fix cc3 rig (bone lengths & deform settings)
        arm = self.chr_cache.get_armature()
        rigutils.fix_cc3_standard_rig(arm)

        # unparent object(s) keep transform
        utils.try_select_objects(self.objects, clear_selection=True)
        bpy.ops.object.parent_clear(type = "CLEAR_KEEP_TRANSFORM")
        utils.set_active_object(arm)

        # start voxel heat diffuse skinning
        # TODO set operator params...
        bpy.ops.wm.voxel_heat_diffuse()

        self.voxel_skinning = True
        bpy.context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(1.0, window = bpy.context.window)


    def voxel_heat_skinning_end(self, context):
        props: properties.CC3ImportProps = vars.props()
        # apply scale on object(s) NOT armature
        utils.try_select_objects(self.objects, clear_selection=True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


    @classmethod
    def description(cls, context, properties):
        if properties.param == "VOXEL_SURFACE_REPARENT":
            return "Attempt to re-parent the character's face objects to the Rigify face rig by using voxel surface head diffuse skinning"

        return ""

