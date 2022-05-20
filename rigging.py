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
import mathutils
import addon_utils
import math
import re
from . import utils
from . import geom
from . import meshutils
from . import properties
from . import modifiers
from . import physics
from . import bones
from . import rigify_mapping_data


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


def prune_meta_rig(meta_rig):
    """Removes some meta rig bones that have no corresponding match in the CC3 rig.
       (And are safe to remove)
    """

    if edit_rig(meta_rig):
        pelvis_r = bones.get_edit_bone(meta_rig, "pelvis.R")
        pelvis_l = bones.get_edit_bone(meta_rig, "pelvis.L")
        if pelvis_r and pelvis_l:
            meta_rig.data.edit_bones.remove(pelvis_r)
            pelvis_l.name = "pelvis"


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
        deform = dst_bone_name[:3] == "DEF"
        scale = 1
        ref = None
        arg = None
        if len(def_copy) > 5:
            scale = def_copy[5]
        if len(def_copy) > 6:
            ref = def_copy[6]
        if len(def_copy) > 7:
            arg = def_copy[7]

        utils.log_info(f"Adding/Processing: {dst_bone_name}")

        # reparent an existing deformation bone
        if src_bone_name == "-":
            reparented_bone = bones.reparent_edit_bone(rigify_rig, dst_bone_name, dst_bone_parent_name)
            if reparented_bone:
                bones.set_edit_bone_flags(reparented_bone, relation_flags, deform)
                bones.set_bone_layer(rigify_rig, dst_bone_name, layer)

        # add a custom DEF or ORG bone
        elif src_bone_name[:3] == "DEF" or src_bone_name[:3] == "ORG":
            def_bone = bones.copy_edit_bone(rigify_rig, src_bone_name, dst_bone_name, dst_bone_parent_name, scale)
            if def_bone:
                bones.set_edit_bone_flags(def_bone, relation_flags, deform)
                bones.set_bone_layer(rigify_rig, dst_bone_name, layer)
            # partial rotation copy for share bones
            if "_share" in dst_bone_name and ref:
                bones.add_copy_rotation_constraint(rigify_rig, rigify_rig, ref, dst_bone_name, arg)

        # or make a copy of a bone from the original character rig
        else:
            def_bone = bones.copy_rl_edit_bone(cc3_rig, rigify_rig, src_bone_name, dst_bone_name, dst_bone_parent_name, scale)
            if def_bone:
                bones.set_edit_bone_flags(def_bone, relation_flags, deform)
                bones.set_bone_layer(rigify_rig, dst_bone_name, layer)

    utils.log_recess()


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


def rename_vertex_groups(cc3_rig, rigify_rig, vertex_groups):
    """Rename the CC3 rig vertex weight groups to the Rigify deformation bone names,
       removes matching existing vertex groups created by parent with automatic weights.
       Thus leaving just the automatic face rig weights.
    """

    utils.log_info("Remapping original Deformation vertex groups to the new Rigify bones:")
    utils.log_indent()

    obj : bpy.types.Object
    for obj in rigify_rig.children:

        utils.log_info(f"Remapping groups for: {obj.name}")

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

        for mod in obj.modifiers:
            if mod.type == "ARMATURE":
                mod.object = rigify_rig
                mod.use_deform_preserve_volume = False

    utils.log_recess()


def store_relative_mappings(meta_rig, coords):
    """Store bone positions relative to a bounding box of control bones.
    """

    if edit_rig(meta_rig):
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

    if edit_rig(meta_rig):
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


def store_bone_roll(meta_rig, roll_store):
    """Store the bone roll and roll axis (z_axis) for each bone in the meta rig.
    """

    if edit_rig(meta_rig):
        for bone in meta_rig.data.edit_bones:
            roll_store[bone.name] = [bone.roll, bone.z_axis]


def restore_bone_roll(meta_rig, roll_store):
    """Restore the bone roll for each bone in the meta rig, after the positions have matched
       to the CC3 rig.
    """

    if edit_rig(meta_rig):
        for bone in meta_rig.data.edit_bones:
            if bone.name in roll_store:
                bone_roll = roll_store[bone.name][0]
                bone_z_axis = roll_store[bone.name][1]
                bone.align_roll(bone_z_axis)
                for correction in rigify_mapping_data.ROLL_CORRECTION:
                    if correction[0] == bone.name:
                        axis = correction[1]
                        if axis == "X":
                            bone.align_roll(mathutils.Vector((1,0,0)))
                        if axis == "Y":
                            bone.align_roll(mathutils.Vector((0,1,0)))
                        if axis == "Z":
                            bone.align_roll(mathutils.Vector((0,0,1)))
                        if axis == "-X":
                            bone.align_roll(mathutils.Vector((-1,0,0)))
                        if axis == "-Y":
                            bone.align_roll(mathutils.Vector((0,-1,0)))
                        if axis == "-Z":
                            bone.align_roll(mathutils.Vector((0,0,-1)))


def set_rigify_params(meta_rig):
    """Apply custom Rigify parameters to bones in the meta rig.
    """

    if select_rig(meta_rig):
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

    if edit_rig(meta_rig):

        # left and right eyes

        left_eye = bones.get_edit_bone(meta_rig, "eye.L")
        left_eye_source = bones.get_rl_bone(cc3_rig, "CC_Base_L_Eye")
        right_eye = bones.get_edit_bone(meta_rig, "eye.R")
        right_eye_source = bones.get_rl_bone(cc3_rig, "CC_Base_R_Eye")

        if left_eye and left_eye_source:
            head_position = cc3_rig.matrix_world @ left_eye_source.head_local
            tail_position = cc3_rig.matrix_world @ left_eye_source.tail_local
            dir : mathutils.Vector = tail_position - head_position
            left_eye.tail = head_position - (dir * length)

        if right_eye and right_eye_source:
            head_position = cc3_rig.matrix_world @ right_eye_source.head_local
            tail_position = cc3_rig.matrix_world @ right_eye_source.tail_local
            dir : mathutils.Vector = tail_position - head_position
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
            tail_position = head_position + mathutils.Vector((0,0,1)) * length
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

    if edit_rig(meta_rig):
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

    if edit_rig(meta_rig):
        mat_slot = get_head_material_slot(obj)
        mesh = obj.data
        t_mesh = geom.get_triangulated_bmesh(mesh)
        bone : bpy.types.EditBone
        for bone in meta_rig.data.edit_bones:
            if bone.layers[0] and bone.name != "face":
                head_world = bone.head
                tail_world = bone.tail
                head_uv = geom.get_uv_from_world(obj, t_mesh, mat_slot, head_world)
                tail_uv = geom.get_uv_from_world(obj, t_mesh, mat_slot, tail_world)
                utils.log_always(f"{bone.name} - uv: {head_uv} -> {tail_uv}")


def map_uv_targets(chr_cache, cc3_rig, meta_rig):
    """Fetch spacial coordinates for bone positions from UV coordinates.
    """

    obj = chr_cache.get_body()
    if obj is None:
        utils.log_error("Cannot find BODY mesh for uv targets!")
        return

    if not edit_rig(meta_rig):
        return

    mat_slot = get_head_material_slot(obj)
    mesh = obj.data
    t_mesh = geom.get_triangulated_bmesh(mesh)

    TARGETS = None
    if chr_cache.generation == "G3Plus":
        TARGETS = rigify_mapping_data.UV_TARGETS_G3PLUS
    elif chr_cache.generation == "G3":
        TARGETS = rigify_mapping_data.UV_TARGETS_G3
    else:
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
        if slot.material is not None:
            if "Std_Skin_Head" in slot.material.name:
                return i
    return -1


def map_bone(cc3_rig, meta_rig, mapping):
    """Maps the head and tail of a bone in the destination
    rig, to the positions of the head and tail of bones in
    the source rig.

    Must be in edit mode with the destination rig active.
    """

    if not edit_rig(meta_rig):
        return

    dst_bone_name = mapping[0]
    src_bone_head_name = mapping[1]
    src_bone_tail_name = mapping[2]

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
            if src_bone:
                if reverse:
                    tail_position = cc3_rig.matrix_world @ src_bone.head_local
                else:
                    tail_position = cc3_rig.matrix_world @ src_bone.tail_local
            else:
                utils.log_error(f"source tail bone: {src_bone_tail_name} not found!")

        # lerp the start and end positions if supplied
        if src_bone:

            if len(mapping) == 5 and src_bone_head_name != "" and src_bone_tail_name != "":
                start = mapping[3]
                end = mapping[4]
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


def match_meta_rig(chr_cache, cc3_rig, meta_rig, rigify_data):
    """Map the bones of the meta rig to match the CC3 rig.
    """

    relative_coords = {}
    roll_store = {}

    if edit_rig(cc3_rig):
        # store all the meta-rig bone roll axes
        store_bone_roll(meta_rig, roll_store)
        #
        if edit_rig(meta_rig):
            # remove unnecessary bones
            prune_meta_rig(meta_rig)
            # store the relative positions of certain bones (face & heel)
            store_relative_mappings(meta_rig, relative_coords)
            # map all CC3 bones to Meta-rig bones
            for mapping in rigify_data.bone_mapping:
                map_bone(cc3_rig, meta_rig, mapping)
            # determine positions of face bones (eyes, head and teeth)
            map_face_bones(cc3_rig, meta_rig, rigify_data.head_bone)
            # restore and apply the relative positions of certain bones (face & heel)
            restore_relative_mappings(meta_rig, relative_coords)
            # fix the jaw pivot
            fix_jaw_pivot(cc3_rig, meta_rig)
            # map the face rig bones by UV map if possible
            if chr_cache.rig_full_face():
                if chr_cache.can_rig_full_face():
                    map_uv_targets(chr_cache, cc3_rig, meta_rig)
            else: # or hide them
                hide_face_bones(meta_rig)
            # restore meta-rig bone roll axes
            restore_bone_roll(meta_rig, roll_store)
            # set rigify rig params
            set_rigify_params(meta_rig)


def fix_bend(meta_rig, bone_one_name, bone_two_name, dir : mathutils.Vector):
    """Determine if the bend between two bones is sufficient to generate an accurate pole in the rig,
       by calculating where the middle joint lies on the line between the start and end points and
       determining if the distance to that line is large enough and in the right direction.
       Recalculating the joint position if not.
    """

    dir.normalize()
    if edit_rig(meta_rig):
        one : bpy.types.EditBone = utils.find_edit_bone_in_armature(meta_rig, bone_one_name)
        two : bpy.types.EditBone = utils.find_edit_bone_in_armature(meta_rig, bone_two_name)
        if one and two:
            start : mathutils.Vector = one.head
            mid : mathutils.Vector = one.tail
            end : mathutils.Vector = two.tail
            u : mathutils.Vector = end - start
            v : mathutils.Vector = mid - start
            u.normalize()
            l = u.dot(v)
            line_mid : mathutils.Vector = u * l + start
            disp : mathutils.Vector = mid - line_mid
            d = disp.length
            if dir.dot(disp) < 0 or d < 0.001:
                utils.log_info(f"Bend between {bone_one_name} and {bone_two_name} is too shallow or negative, fixing.")
                new_mid_dir : mathutils.Vector = dir - u.dot(dir) * u
                new_mid_dir.normalize()
                new_mid = line_mid + new_mid_dir * 0.001
                utils.log_info(f"New joint position: {new_mid}")
                one.tail = new_mid
                two.head = new_mid


def hide_face_bones(meta_rig):
    """Move all the non basic face rig bones into a hidden layer.
    """

    if edit_rig(meta_rig):
        for b in rigify_mapping_data.NON_BASIC_FACE_BONES:
            bone = bones.get_edit_bone(meta_rig, b)
            if bone:
                bone.layers[0] = False
                bone.layers[31] = True
    if select_rig(meta_rig):
        for b in rigify_mapping_data.NON_BASIC_FACE_BONES:
            bone = bones.get_bone(meta_rig, b)
            if bone:
                bone.layers[0] = False
                bone.layers[31] = True


def convert_to_basic_face_rig(rigify_rig):
    if edit_rig(rigify_rig):
        for b in rigify_mapping_data.NON_BASIC_FACE_BONES:
            bone_names = [b, f"DEF-{b}", f"ORG-{b}", f"MCH-{b}"]
            for bone_name in bone_names:
                bone = bones.get_edit_bone(rigify_rig, bone_name)
                if bone:
                    rigify_rig.data.edit_bones.remove(bone)
    select_rig(rigify_rig)


def add_shape_key_drivers(chr_cache, rig):
    for obj in rig.children:
        if obj.type == "MESH" and obj.parent == rig:
            obj_cache = chr_cache.get_object_cache(obj)
            if is_face_object(obj_cache, obj):
                for skd_def in rigify_mapping_data.SHAPE_KEY_DRIVERS:
                    flags = skd_def[0]
                    if "Bfr" in flags and chr_cache.rigified_full_face_rig:
                        continue
                    shape_key_name = skd_def[1]
                    driver_def = skd_def[2]
                    var_def = skd_def[3]
                    add_shape_key_driver(rig, obj, shape_key_name, driver_def, var_def)


def add_shape_key_driver(rig, obj, shape_key_name, driver_def, var_def):
    if utils.set_mode("OBJECT"):
        shape_key = meshutils.find_shape_key(obj, shape_key_name)
        if shape_key:
            fcurve : bpy.types.FCurve
            fcurve = shape_key.driver_add("value")
            driver : bpy.types.Driver = fcurve.driver
            driver.type = driver_def[0]
            if driver.type == "SCRIPTED":
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


def correct_meta_rig(meta_rig):
    """Add a slight displacement (if needed) to the knee and elbow to ensure the poles are the right way.
    """

    utils.log_info("Correcting Meta-Rig, Knee and Elbow bends.")
    utils.log_indent()

    fix_bend(meta_rig, "thigh.L", "shin.L", mathutils.Vector((0,-1,0)))
    fix_bend(meta_rig, "thigh.R", "shin.R", mathutils.Vector((0,-1,0)))
    fix_bend(meta_rig, "upper_arm.L", "forearm.L", mathutils.Vector((0,1,0)))
    fix_bend(meta_rig, "upper_arm.R", "forearm.R", mathutils.Vector((0,1,0)))

    utils.set_mode("OBJECT")

    utils.log_recess()


def modify_rigify_rig(rigify_rig):
    """Resize and reposition Rigify control bones to make them easier to find.
       Note: scale, location, rotation modifiers for custom control shapes is Blender 3.0.0+ only
    """

    # turn off deformation for palm bones
    if edit_rig(rigify_rig):
        for edit_bone in rigify_rig.data.edit_bones:
            if edit_bone.name.startswith("DEF-palm"):
                edit_bone.use_deform = False

    if utils.is_blender_version("3.0.0"):
        if select_rig(rigify_rig):
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
                    bone.custom_shape_scale_xyz = scale
                    bone.custom_shape_translation = translation
                    bone.custom_shape_rotation_euler = rotation
            utils.log_recess()


def reparent_to_rigify(self, chr_cache, cc3_rig, rigify_rig):
    """Unparent (with transform) from the original CC3 rig and reparent to the new rigify rig (with automatic weights for the body),
       setting the armature modifiers to the new rig.

       The automatic weights will generate vertex weights for the additional face bones in the new rig.
       (But only for the Body mesh)
    """

    utils.log_info("Reparenting character objects to new Rigify Control Rig:")
    utils.log_indent()

    props = bpy.context.scene.CC3ImportProps
    result = 1

    if utils.set_mode("OBJECT"):

        for obj in cc3_rig.children:
            if obj.type == "MESH" and obj.parent == cc3_rig:

                hidden = not obj.visible_get()
                if hidden:
                    obj.hide_set(False)
                obj_cache = chr_cache.get_object_cache(obj)

                if utils.try_select_object(obj, True) and utils.set_active_object(obj):
                    bpy.ops.object.parent_clear(type = "CLEAR_KEEP_TRANSFORM")

                # only the body and face objects will generate the automatic weights for the face rig.
                if (chr_cache.rigified_full_face_rig and
                    utils.object_exists_is_mesh(obj) and
                    len(obj.data.vertices) >= 2 and
                    is_face_object(obj_cache, obj)):

                    obj_result = try_parent_auto(chr_cache, rigify_rig, obj)
                    if obj_result < result:
                        result = obj_result

                else:

                    if utils.try_select_object(rigify_rig) and utils.set_active_object(rigify_rig):
                        bpy.ops.object.parent_set(type = "OBJECT", keep_transform = True)

                    arm_mod : bpy.types.ArmatureModifier = modifiers.add_armature_modifier(obj, True)
                    if arm_mod:
                        arm_mod.object = rigify_rig

                if hidden:
                    obj.hide_set(True)

    utils.log_recess()
    return result


def clean_up(chr_cache, cc3_rig, rigify_rig, meta_rig):
    """Rename the rigs, hide the original CC3 Armature and remove the meta rig.
       Set the new rig into pose mode.
    """

    utils.log_info("Cleaning Up...")
    rig_name = cc3_rig.name
    cc3_rig.hide_set(True)
    utils.delete_armature_object(meta_rig)
    rigify_rig.name = rig_name + "_Rigify"
    rigify_rig.data.name = rig_name + "_Rigify"
    if utils.set_mode("OBJECT"):
        # delesect all bones (including the hidden ones)
        # Rigimap will bake and clear constraints on the ORG bones if we don't do this...
        for bone in rigify_rig.data.bones:
            bone.select = False
        utils.clear_selected_objects()
        if utils.try_select_object(rigify_rig, True):
            utils.set_active_object(rigify_rig)
    chr_cache.set_rigify_armature(rigify_rig)


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


PREP_VGROUP_VALUE_A = 0.5
PREP_VGROUP_VALUE_B = 1.0

def init_face_vgroups(rig, obj):
    global PREP_VGROUP_VALUE_A, PREP_VGROUP_VALUE_B
    PREP_VGROUP_VALUE_A = random()
    PREP_VGROUP_VALUE_B = random()

    utils.set_mode("OBJECT")
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
    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
        if is_face_object(obj_cache, obj):
            for vg in obj.vertex_groups:
                if not is_face_def_bone(vg):
                    vg.name = "_tmp_shift_" + vg.name


def restore_non_face_vgroups(chr_cache):
    utils.log_info("Restoring non face vertex weights.")
    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
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
    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
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
    if body and arm and utils.set_mode("OBJECT"):
        utils.try_select_objects([body, arm], True)
        utils.set_active_object(arm)


def unlock_vgroups(chr_cache):
    utils.log_info("Unlocking non face vertex weights.")
    for obj_cache in chr_cache.object_cache:
        if obj_cache.object_type in rigify_mapping_data.BODY_TYPES:
            obj = obj_cache.object
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
    if arm and utils.set_mode("OBJECT"):
        utils.try_select_object(arm, True)
        utils.set_active_object(arm)


def mesh_clean_up(obj):
    if utils.edit_mode_to(obj):
        bpy.ops.mesh.select_all(action = 'SELECT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.delete_loose()
        bpy.ops.mesh.dissolve_degenerate()
    utils.set_mode("OBJECT")


def clean_up_character_meshes(chr_cache):
    face_objects = []
    arm = chr_cache.get_armature()
    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
        if is_face_object(obj_cache, obj):
            face_objects.append(obj)
            mesh_clean_up(obj)
    # select body mesh and active rig
    if obj and arm and utils.set_mode("OBJECT"):
        face_objects.append(arm)
        utils.try_select_objects(face_objects, True)
        utils.set_active_object(arm)


def parent_set_with_test(rig, obj):
    init_face_vgroups(rig, obj)
    if utils.try_select_objects([obj, rig], True) and utils.set_active_object(rig):
        utils.log_always(f"Parenting: {obj.name}")
        bpy.ops.object.parent_set(type = "ARMATURE_AUTO", keep_transform = True)
        if not test_face_vgroups(rig, obj):
            return False
    return True


def try_parent_auto(chr_cache, rig, obj):
    modifiers.remove_object_modifiers(obj, "ARMATURE")

    result = 1

    # first attempt

    if parent_set_with_test(rig, obj):
        utils.log_always(f"Success!")
    else:
        utils.log_always(f"Parent with automatic weights failed: attempting mesh clean up...")
        mesh_clean_up(obj)
        if result == 1:
            result = 0

        # second attempt

        if parent_set_with_test(rig, obj):
            utils.log_always(f"Success!")
        else:
            body = chr_cache.get_body()

            # third attempt

            if obj == body:
                utils.log_always(f"Parent with automatic weights failed again: trying just the head mesh...")
                head = separate_head(obj)

                if parent_set_with_test(rig, head):
                    utils.log_always(f"Success!")
                else:
                    utils.log_always(f"Automatic weights failed for {obj.name}, will need to re-parented by other means!")
                    result = -1

                rejoin_head(head, body)

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
    utils.set_mode("OBJECT")
    utils.clear_selected_objects()
    result = 1
    rig = chr_cache.get_armature()
    utils.log_always("Attemping to parent the Body mesh to the Face Rig:")
    utils.log_always("If this fails, the face rig may not work and will need to re-parented by other means.")
    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
        if utils.object_exists_is_mesh(obj) and len(obj.data.vertices) >= 2 and is_face_object(obj_cache, obj):
            obj_result = try_parent_auto(chr_cache, rig, obj)
            if obj_result < result:
                result = obj_result
    return result


def attempt_reparent_voxel_skinning(chr_cache):
    utils.set_mode("OBJECT")
    utils.clear_selected_objects()
    arm = chr_cache.get_armature()
    face_objects = []
    head = None
    body = None
    dummy_cube = None
    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
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
    utils.set_mode("OBJECT")
    utils.clear_selected_objects()
    if utils.edit_mode_to(body_mesh):
        bpy.context.object.active_material_index = 0
        bpy.ops.object.material_slot_select()
        if len(body_mesh.material_slots) == 6:
            bpy.context.object.active_material_index = 5
            bpy.ops.object.material_slot_select()
        bpy.ops.mesh.separate(type="SELECTED")
        utils.set_mode("OBJECT")
        separated_head = None
        for o in bpy.context.selected_objects:
            if o != body_mesh:
                separated_head = o
        return separated_head


def rejoin_head(head_mesh, body_mesh):
    utils.set_mode("OBJECT")
    utils.try_select_objects([body_mesh, head_mesh], True)
    utils.set_active_object(body_mesh)
    bpy.ops.object.join()
    if utils.edit_mode_to(body_mesh):
        bpy.ops.mesh.select_all(action = 'SELECT')
        bpy.ops.mesh.remove_doubles()
    utils.set_mode("OBJECT")


# Animation Retargeting
#
#

def get_bone_name_regex(rig, pattern):
    if pattern:
        for bone in rig.data.bones:
            if re.match(pattern, bone.name):
                return bone.name
    return None


def generate_retargeting_rig(chr_cache, source_rig, rigify_rig, retarget_data):
    props = bpy.context.scene.CC3ImportProps

    source_rig.hide_set(False)
    source_rig.data.pose_position = "POSE"
    rigify_rig.hide_set(False)
    rigify_rig.data.pose_position = "POSE"

    retarget_rig = bpy.data.objects.new(chr_cache.character_name + "_Retarget", bpy.data.armatures.new(chr_cache.character_name + "_Retarget"))
    bpy.context.collection.objects.link(retarget_rig)
    if retarget_rig:

        ORG_BONES = {}
        RIGIFY_BONES = {}
        eyes_distance = 0.5
        face_pos = None
        eyes_pos = None

        # scan the rigify rig for origin bones
        #
        # store all the bone details from the ORG bones to reconstruct the origin rig.
        # in some cases new ORG bones are created to act as parents or animation targets from the source.
        # this way if the Rigify rig is not complex enough, the retarget rig can be made to better match the source armature.
        if edit_rig(rigify_rig):
            for retarget_def in retarget_data.retarget:
                org_bone_name = retarget_def[0]
                if not org_bone_name or org_bone_name in ORG_BONES:
                    # don't process the same ORG bone more than once
                    continue

                org_parent_bone_name = retarget_def[1]
                utils.log_info(f"Generating retarget ORG bone: {org_bone_name}")
                flags = retarget_def[4]
                head_pos = rigify_rig.matrix_world @ mathutils.Vector((0,0,0))
                tail_pos = rigify_rig.matrix_world @ mathutils.Vector((0,0,0.01))
                parent_pos = rigify_rig.matrix_world @ mathutils.Vector((0,0,0))
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
                org_parent_bone = bones.get_edit_bone(rigify_rig, org_parent_bone_name)
                if org_parent_bone:
                    parent_pos = rigify_rig.matrix_world @ org_parent_bone.head
                elif org_parent_bone_name in ORG_BONES:
                    parent_pos = ORG_BONES[org_parent_bone_name][1]
                else:
                    utils.log_error(f"Could not find parent bone: {org_parent_bone_name} in Rigify rig or ORG bones!")
                    org_parent_bone_name = ""

                # get the scale of the bone as the distance from it's parent head position
                scale = (head_pos - parent_pos).length
                if scale <= 0.00001:
                    scale = 1

                # parent retarget correction, add corrective parent bone and insert into parent chain
                if "P" in flags or "T" in flags:
                    pivot_bone_name = org_bone_name + "_pivot"
                    utils.log_info(f"Adding parent correction pivot: {pivot_bone_name} -> {org_bone_name}")
                    ORG_BONES[pivot_bone_name] = [org_parent_bone_name,
                            head_pos, tail_pos, parent_pos,
                            use_connect,
                            use_local_location,
                            use_inherit_rotation,
                            inherit_scale,
                            scale]
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
                            scale]

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
                                eyes_pos = head_pos
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
        if edit_rig(source_rig):
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
                        z_axis = source_rig.matrix_world @ mathutils.Vector((0,0,1))
                        scale = 1.0
                        if source_bone:
                            head_pos = source_rig.matrix_world @ source_bone.head
                            tail_pos = source_rig.matrix_world @ source_bone.tail

                            # z-axis is in local space, we wan't it in world space for the retarget rig
                            z_axis = source_rig.matrix_world @ source_bone.z_axis

                            # find the source bone equivalent to the ORG bones parent
                            parent_pos = source_rig.matrix_world @ mathutils.Vector((0,0,0))
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
                            scale = dir.length
                            if scale <= 0.00001: scale = 1
                        else:
                            utils.log_error(f"Could not find source bone: {source_bone_name} in source rig!")
                        org_bone_def.append(scale)
                        org_bone_def.append(z_axis)
                        if ("P" in flags or "T" in flags) and org_bone_name + "_pivot" in ORG_BONES:
                            pivot_org_bone_def = ORG_BONES[org_bone_name + "_pivot"]
                            pivot_org_bone_def.append(scale)
                            pivot_org_bone_def.append(z_axis)
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
                                    parent_pos = org_bone_def[3]
                                    scale = (head_pos - parent_pos).length
                                    if scale <= 0.00001:
                                        scale = 1
                                    ORG_BONES[org_bone_name][1] = head_pos
                                    ORG_BONES[org_bone_name][2] = tail_pos
                                    ORG_BONES[org_bone_name][8] = scale
                                else:
                                    utils.log_error(f"Could not find ref bone: {ref_bone_name} in source rig!")

                    # handle parent retarget correction:
                    # when the source bone is not in the same orientation as the ORG bone
                    # we need to parent the ORG bone to a copy of the source bone -
                    if f == "P" or f == "T":
                        if org_bone_name + "_pivot" in ORG_BONES:
                            pivot_org_bone_def = ORG_BONES[org_bone_name + "_pivot"]
                        source_bone_name = get_bone_name_regex(source_rig, source_bone_regex)
                        source_bone = bones.get_edit_bone(source_rig, source_bone_name)
                        if source_bone and org_bone_def and pivot_org_bone_def:
                            source_head = source_rig.matrix_world @ source_bone.head
                            source_tail = source_rig.matrix_world @ source_bone.tail
                            head_position = org_bone_def[1]
                            source_dir = source_tail - source_head

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
        if edit_rig(retarget_rig):

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
        if select_rig(retarget_rig):

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
                        if len(org_bone_def) >= 11:
                            scale_influence = org_bone_def[8] / org_bone_def[9]
                            scale_influence = max(0.0, min(1.0, scale_influence))
                        if org_bone_name == "ORG-hip" or org_bone_name == "ORG-hip_pivot":
                            bones.add_copy_location_constraint(source_rig, retarget_rig, source_bone_name, org_bone_name, scale_influence * influence, "LOCAL_WITH_PARENT")
                        else:
                            space = "LOCAL"
                            if utils.is_blender_version("3.1.0"):
                                space = "LOCAL_OWNER_ORIENT"
                            bones.add_copy_location_constraint(source_rig, retarget_rig, source_bone_name, org_bone_name, scale_influence * influence, space)
                        bones.add_copy_rotation_constraint(source_rig, retarget_rig, source_bone_name, org_bone_name, influence)
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
                            if utils.is_blender_version("3.1.0"):
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

        select_rig(retarget_rig)

    retarget_rig.data.display_type = "STICK"
    return retarget_rig


def adv_retarget_remove_pair(op, chr_cache):
    props = bpy.context.scene.CC3ImportProps
    rigify_rig = chr_cache.get_armature()
    retarget_rig = chr_cache.rig_retarget_rig

    # remove all contraints on Rigify control bones
    if utils.still_exists(rigify_rig):
        rigify_rig.hide_set(False)
        if select_rig(rigify_rig):
            for rigify_bone_name in rigify_mapping_data.RETARGET_RIGIFY_BONES:
                bones.clear_constraints(rigify_rig, rigify_bone_name)

    # remove the retarget rig
    if utils.still_exists(retarget_rig):
        retarget_rig.hide_set(False)
        utils.delete_armature_object(retarget_rig)
    chr_cache.rig_retarget_rig = None
    chr_cache.rig_retarget_source_rig = None
    utils.try_select_object(rigify_rig, True)
    utils.set_active_object(rigify_rig)
    utils.set_mode("OBJECT")

    # clear any animated shape keys
    reset_shape_keys(chr_cache)


def adv_preview_retarget(op, chr_cache):
    props = bpy.context.scene.CC3ImportProps
    rigify_rig = chr_cache.get_armature()
    source_rig = props.armature_list_object
    source_action = props.action_list_action

    retarget_rig = adv_retarget_pair_rigs(op, chr_cache)
    if retarget_rig and source_action:
        start_frame = int(source_action.frame_range[0])
        end_frame = int(source_action.frame_range[1])
        bpy.context.scene.frame_start = start_frame
        bpy.context.scene.frame_end = end_frame

        if props.retarget_preview_shape_keys:
            adv_retarget_shape_keys(op, chr_cache, False)


def adv_retarget_pair_rigs(op, chr_cache):
    props = bpy.context.scene.CC3ImportProps
    rigify_rig = chr_cache.get_armature()
    source_rig = props.armature_list_object
    source_action = props.action_list_action
    utils.safe_set_action(source_rig, source_action)

    if not source_rig:
        op.report({'ERROR'}, "No source Armature!")
        return None
    if not rigify_rig:
        op.report({'ERROR'}, "No Rigify Armature!")
        return None
    if not source_action:
        op.report({'ERROR'}, "No Source Action!")
        return None
    if not is_rigify_armature(rigify_rig):
        op.report({'ERROR'}, "Character Armature is not a Rigify armature!")
        return None
    if not check_armature_action(source_rig, source_action):
        op.report({'ERROR'}, "Source Action does not match Source Armature!")
        return None

    source_type, source_label = get_armature_action_source_type(source_rig, source_action)
    retarget_data = rigify_mapping_data.get_retarget_for_source(source_type)

    if not retarget_data:
        op.report({'ERROR'}, f"Retargeting from {source_type} not supported!")
        return None

    olc = utils.set_active_layer_collection_from(rigify_rig)

    adv_retarget_remove_pair(op, chr_cache)

    temp_collection = utils.force_visible_in_scene("TMP_Retarget", source_rig, rigify_rig)

    rigify_rig.location = (0,0,0)
    rigify_rig.rotation_mode = "XYZ"
    rigify_rig.rotation_euler = (0,0,0)
    source_rig.location = (0,0,0)
    source_rig.rotation_mode = "XYZ"
    #source_rig.rotation_euler = (0,0,0)

    utils.delete_armature_object(chr_cache.rig_retarget_rig)
    retarget_rig = generate_retargeting_rig(chr_cache, source_rig, rigify_rig, retarget_data)
    chr_cache.rig_retarget_rig = retarget_rig
    chr_cache.rig_retarget_source_rig = source_rig
    select_rig(rigify_rig)
    try:
        rigify_rig.pose.bones["upper_arm_parent.L"]["IK_FK"] = 1.0
        rigify_rig.pose.bones["upper_arm_parent.R"]["IK_FK"] = 1.0
        rigify_rig.pose.bones["thigh_parent.L"]["IK_FK"] = 1.0
        rigify_rig.pose.bones["thigh_parent.R"]["IK_FK"] = 1.0
        retarget_rig.data.display_type = "STICK"
    except:
        pass

    utils.restore_visible_in_scene(temp_collection)

    utils.set_active_layer_collection(olc)

    retarget_rig.hide_set(True)

    return retarget_rig


def adv_bake_retarget_to_rigify(op, chr_cache):
    props = bpy.context.scene.CC3ImportProps
    rigify_rig = chr_cache.get_armature()
    source_rig = props.armature_list_object
    source_action = props.action_list_action
    utils.safe_set_action(source_rig, source_action)

    retarget_rig = adv_retarget_pair_rigs(op, chr_cache)

    if retarget_rig:
        temp_collection = utils.force_visible_in_scene("TMP_Bake_Retarget", source_rig, retarget_rig, rigify_rig)

        # select just the retargeted bones in the rigify rig, to bake:
        if select_rig(rigify_rig):
            for bone in rigify_rig.data.bones:
                bone.select = False
                if bone.name in rigify_mapping_data.RETARGET_RIGIFY_BONES:
                    bone.select = True

            bake_rig_animation(chr_cache, rigify_rig, source_action, None, True, True)

            adv_retarget_remove_pair(op, chr_cache)

        utils.restore_visible_in_scene(temp_collection)


def adv_bake_NLA_to_rigify(op, chr_cache):
    props = bpy.context.scene.CC3ImportProps
    rigify_rig = chr_cache.get_armature()
    utils.safe_set_action(rigify_rig, None)
    adv_retarget_remove_pair(op, chr_cache)

    # select all possible control bones in the rigify rig, to bake:
    BAKE_BONE_GROUPS = ["FK", "IK", "Special", "Tweak", "Extra", "Root"]
    if select_rig(rigify_rig):
        bone : bpy.types.Bone
        for bone in rigify_rig.data.bones:
            bone.select = False
            pose_bone = bones.get_pose_bone(rigify_rig, bone.name)
            if pose_bone and pose_bone.bone_group:
                if pose_bone.bone_group.name in BAKE_BONE_GROUPS:
                    bone.select = True
        shape_key_objects = []
        if props.bake_nla_shape_keys:
            for child in rigify_rig.children:
                if (child.type == "MESH" and
                    child.data.shape_keys and
                    child.data.shape_keys.key_blocks and
                    len(child.data.shape_keys.key_blocks) > 0):
                    shape_key_objects.append(child)

        bake_rig_animation(chr_cache, rigify_rig, None, shape_key_objects, False, True, "NLA_Bake")


# Shape-key retargeting
#
#


def reset_shape_keys(chr_cache):
    rigify_rig = chr_cache.get_armature()
    objects = []
    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
        if obj.type == "MESH":
            objects.append(obj)
    for obj in rigify_rig.children:
        if obj.type == "MESH" and obj not in objects:
            objects.append(obj)
    for obj in objects:
        if obj.data.shape_keys:
            for key_block in obj.data.shape_keys.key_blocks:
                key_block.value = 0.0


def get_shape_key_name_from_data_path(data_path):
    if data_path.startswith("key_blocks[\""):
        start = utils.safe_index_of(data_path, '"', 0) + 1
        end = utils.safe_index_of(data_path, '"', start)
        return data_path[start:end]
    return None


def get_source_shape_key_actions(source_rig, source_action):
    actions = {}

    animation_name = None
    if source_action:
        names = source_action.name.split("|")
        if len(names) >= 3:
            if names[0] == source_rig.name and names[1] == "A":
                animation_name = names[2]

    if animation_name:

        # match actions by name (if imported using this add-on)
        utils.log_info(f"looking for shape-key actions with animation name: {source_rig.name}|K|<obj>|{animation_name}")
        for action in bpy.data.actions:
            names = action.name.split("|")
            if len(names) >= 4:
                if names[0] == source_rig.name and names[1] == "K":
                    if utils.partial_match(names[3], animation_name):
                        if names[2] not in actions:
                            utils.log_info(f"Found shape-key action: {action.name} for object {names[2]}")
                            actions[names[2]] = action
    else:

        # try and fetch shape-key actions from source armature child objects
        utils.log_info(f"looking for shape-key actions in armature child objects: {source_rig.name}")
        for obj in source_rig.children:
            obj_name = utils.get_action_shape_key_object_name(obj.name)
            if obj.type == "MESH":
                action = utils.safe_get_action(obj.data.shape_keys)
                if action:
                    utils.log_info(f"Found shape-key action: {action.name} for object {obj_name}")
                    actions[obj_name] = action

    return actions


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


def remap_shape_key_actions(chr_cache, rigify_rig, shape_key_actions):
    body_action = None
    for obj_name in shape_key_actions:
        if obj_name == "CC_Base_Body" or obj_name == "CC_Game_Body" or obj_name == "Body":
            body_action = shape_key_actions[obj_name]
            utils.log_info(f"Body Action: {body_action.name}")
    if body_action:
        for child in rigify_rig.children:
            if child.type == "MESH":
                obj_cache = chr_cache.get_object_cache(child)
                child_name = utils.strip_name(child.name)
                if child_name not in shape_key_actions and is_face_object(obj_cache, child):
                    action = match_obj_shape_key_action_name(child_name, shape_key_actions)
                    if action:
                        utils.log_info(f"Remapping Action {action.name} for object: {child_name}")
                        shape_key_actions[child_name] = action
                    else:
                        utils.log_info(f"Adding Body Action to object: {child_name}")
                        shape_key_actions[child_name] = body_action
    return shape_key_actions


def apply_shape_key_actions(rigify_rig, shape_key_actions):
    for child in rigify_rig.children:
        if child.type == "MESH":
            child_name = utils.strip_name(child.name)
            if child_name in shape_key_actions:
                utils.safe_set_action(child.data.shape_keys, shape_key_actions[child_name])
            else:
                utils.safe_set_action(child.data.shape_keys, None)


def adv_retarget_shape_keys(op, chr_cache, report):
    props = bpy.context.scene.CC3ImportProps
    rigify_rig = chr_cache.get_armature()
    source_rig = props.armature_list_object
    source_action = props.action_list_action

    if not source_rig:
        op.report({'ERROR'}, "No source Armature!")
        return
    if not rigify_rig:
        op.report({'ERROR'}, "No Rigify Armature!")
        return
    if not source_action:
        op.report({'ERROR'}, "No Source Action!")
        return
    if not is_rigify_armature(rigify_rig):
        op.report({'ERROR'}, "Character Armature is not a Rigify armature!")
        return
    if not check_armature_action(source_rig, source_action):
        op.report({'ERROR'}, "Source Action does not match Source Armature!")
        return

    source_type, source_label = get_armature_action_source_type(source_rig, source_action)
    retarget_data = rigify_mapping_data.get_retarget_for_source(source_type)

    if not retarget_data:
        op.report({'ERROR'}, f"Retargeting from {source_type} not supported!")
        return

    shape_key_actions = get_source_shape_key_actions(source_rig, source_action)

    if not shape_key_actions or len(shape_key_actions) == 0:
        if report:
            op.report({'WARNING'}, f"No shape-key actions in source animation!")
    else:
        shape_key_actions = remap_shape_key_actions(chr_cache, rigify_rig, shape_key_actions)
        apply_shape_key_actions(rigify_rig, shape_key_actions)
        if report:
            op.report({'INFO'}, f"Shape-key actions retargeted to character!")

    reset_shape_keys(chr_cache)


# Unity animation exporting and baking
#
#


def generate_unity_export_rig(chr_cache):
    rigify_rig = chr_cache.get_armature()
    export_rig = utils.duplicate_object(rigify_rig)
    if export_rig:
        export_rig.name = chr_cache.character_name + "_Unity"
        export_rig.name = chr_cache.character_name + "_Unity"
        export_rig.data.name = chr_cache.character_name + "_Unity"
        export_rig.data.name = chr_cache.character_name + "_Unity"
    else:
        return None

    # turn all the layers on, otherwise keyframing can fail
    for l in range(0, 32):
        export_rig.data.layers[l] = True
        export_rig.data.layers_protected[l] = False

    # compile a list of all deformation bones
    def_bones = []
    for export_def in rigify_mapping_data.UNITY_EXPORT_RIG:
        def_bones.append(export_def[0])

    # remove all drivers
    if select_rig(export_rig):
        bones.clear_drivers(export_rig)

    # remove all constraints
    if select_rig(export_rig):
        for pose_bone in export_rig.pose.bones:
            bones.clear_constraints(export_rig, pose_bone.name)
            pose_bone.custom_shape = None

    a_pose = False
    layer = 0

    if edit_rig(export_rig):

        edit_bones = export_rig.data.edit_bones

        # test for A-pose
        upper_arm_l = edit_bones['DEF-upper_arm.L']
        world_x = mathutils.Vector((1, 0, 0))
        if world_x.dot(upper_arm_l.y_axis) < 0.9:
            a_pose = True

        for export_def in rigify_mapping_data.UNITY_EXPORT_RIG:

            bone_name = export_def[0]
            parent_name = export_def[1]
            unity_name = export_def[2]
            flags = export_def[3]
            bone = None
            parent_bone = None

            if bone_name in edit_bones:
                bone = edit_bones[bone_name]

                # assign parent hierachy
                if "P" in flags:
                    parent_bone = edit_bones[parent_name]
                if parent_bone:
                    bone.parent = parent_bone
                if "T" in flags and len(export_def) > 4:
                    copy_name = export_def[4]
                    if copy_name in edit_bones:
                        copy_bone = edit_bones[copy_name]
                        bone.head = copy_bone.head
                        bone.tail = copy_bone.tail
                        bone.roll = copy_bone.roll

                # set flags
                bones.set_edit_bone_flags(bone, flags, True)

                # set layer
                for l in range(0, 32):
                    bone.layers[l] = l == layer

        # remove all non-deformation bones
        for edit_bone in edit_bones:
            if edit_bone.name not in def_bones:
                edit_bones.remove(edit_bone)

        # rename bones for Unity
        for export_def in rigify_mapping_data.UNITY_EXPORT_RIG:
            bone_name = export_def[0]
            unity_name = export_def[2]
            if unity_name != "" and bone_name in edit_bones:
                edit_bones[bone_name].name = unity_name

    # set pose bone layers
    if select_rig(export_rig):
        for bone in export_rig.data.bones:
            for l in range(0, 32):
                bone.layers[l] = l == layer

    # reset the pose
    bones.clear_pose(export_rig)

    # Force T-pose
    if a_pose:
        angle = 30.0 * math.pi / 180.0
        if "CC_Base_L_Upperarm" in export_rig.pose.bones and "CC_Base_R_Upperarm" in export_rig.pose.bones:
            left_arm_bone : bpy.types.PoseBone = export_rig.pose.bones["CC_Base_L_Upperarm"]
            right_arm_bone : bpy.types.PoseBone  = export_rig.pose.bones["CC_Base_R_Upperarm"]
            left_arm_bone.rotation_mode = "XYZ"
            left_arm_bone.rotation_euler = [0,0,angle]
            left_arm_bone.rotation_mode = "QUATERNION"
            right_arm_bone.rotation_mode = "XYZ"
            right_arm_bone.rotation_euler = [0,0,-angle]
            right_arm_bone.rotation_mode = "QUATERNION"

    return export_rig


def get_unity_bake_action(chr_cache):
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


def adv_bake_rigify_to_unity(op, chr_cache):

    rigify_rig = chr_cache.get_armature()
    if rigify_rig.animation_data is None:
        rigify_rig.animation_data_create()

    # determine the action on the rigify rig
    action, source_type = get_unity_bake_action(chr_cache)

    # if there is an action
    if action:

        # generate Unity export rig
        export_rig = chr_cache.rig_export_rig
        if utils.object_exists_is_armature(export_rig):
            utils.delete_armature_object(export_rig)
        export_rig = generate_unity_export_rig(chr_cache)
        chr_cache.rig_export_rig = export_rig

        if export_rig:

            # copy constraints for baking animations
            if select_rig(export_rig):
                for export_def in rigify_mapping_data.UNITY_EXPORT_RIG:
                    rigify_bone_name = export_def[0]
                    unity_bone_name = export_def[2]
                    flags = export_def[3]
                    if unity_bone_name == "":
                        unity_bone_name = rigify_bone_name
                    if "T" in flags and len(export_def) > 4:
                        rigify_bone_name = export_def[4]
                    bones.add_copy_rotation_constraint(rigify_rig, export_rig, rigify_bone_name, unity_bone_name, 1.0)
                    bones.add_copy_location_constraint(rigify_rig, export_rig, rigify_bone_name, unity_bone_name, 1.0)

                # select all export rig bones
                for bone in export_rig.data.bones:
                    bone.select = True

                # bake the action on the rigify rig into the export rig
                bake_rig_animation(chr_cache, export_rig, action, None, True, True)

            else:
                op.report({'ERROR'}, "Unable to add copy constraints to Unity export rig!")
    else:
        op.report({'ERROR'}, "Rigify rig has no valid Armature Action to bake!")


def adv_bake_rigify_NLA_to_unity(op, chr_cache):
    props = bpy.context.scene.CC3ImportProps
    rigify_rig = chr_cache.get_armature()
    utils.safe_set_action(rigify_rig, None)
    adv_retarget_remove_pair(op, chr_cache)

    # generate Unity export rig
    export_rig = chr_cache.rig_export_rig
    if utils.object_exists_is_armature(export_rig):
        utils.delete_armature_object(export_rig)
    export_rig = generate_unity_export_rig(chr_cache)
    chr_cache.rig_export_rig = export_rig

    if export_rig:

        # copy constraints for baking animations
        if select_rig(export_rig):
            for export_def in rigify_mapping_data.UNITY_EXPORT_RIG:
                rigify_bone_name = export_def[0]
                unity_bone_name = export_def[2]
                flags = export_def[3]
                if unity_bone_name == "":
                    unity_bone_name = rigify_bone_name
                if "T" in flags and len(export_def) > 4:
                    rigify_bone_name = export_def[4]
                bones.add_copy_rotation_constraint(rigify_rig, export_rig, rigify_bone_name, unity_bone_name, 1.0)
                bones.add_copy_location_constraint(rigify_rig, export_rig, rigify_bone_name, unity_bone_name, 1.0)

            # select all export rig bones
            for bone in export_rig.data.bones:
                bone.select = True

            shape_key_objects = []
            if props.bake_nla_shape_keys:
                for child in rigify_rig.children:
                    if child.data.shape_keys and len(child.data.shape_keys) > 0:
                        shape_key_objects.append(child)

            # bake the action on the rigify rig into the export rig
            bake_rig_animation(chr_cache, export_rig, None, shape_key_objects, True, True, "NLA_Bake")

        else:
            op.report({'ERROR'}, "Unable to add copy constraints to Unity export rig!")


def prep_unity_export_rig(chr_cache):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    rigify_rig = chr_cache.get_armature()

    # generate Unity export rig
    export_rig = chr_cache.rig_export_rig
    if utils.object_exists_is_armature(export_rig):
        utils.delete_armature_object(export_rig)
    export_rig = generate_unity_export_rig(chr_cache)
    chr_cache.rig_export_rig = export_rig

    if select_rig(export_rig):
        export_rig.data.pose_position = "POSE"

        # Clear the NLA track for this rig
        if prefs.export_animation_mode == "STRIPS":
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

            # create T-Pose action
            if "0_T-Pose" in bpy.data.actions:
                bpy.data.actions.remove(bpy.data.actions["0_T-Pose"])
            action : bpy.types.Action = bpy.data.actions.new("0_T-Pose")
            utils.safe_set_action(export_rig, action)

            # go to first frame
            bpy.data.scenes["Scene"].frame_current = 1

            # apply first keyframe
            bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_LocRot')

            # make a second keyframe
            bpy.data.scenes["Scene"].frame_current = 2
            bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_LocRot')

            # push T-Pose to NLA if exporting only strips
            if prefs.export_animation_mode == "STRIPS":
                utils.log_info(f"Adding {action.name} to NLA strips")
                track = export_rig.animation_data.nla_tracks[0]
                track.strips.new(action.name, int(action.frame_range[0]), action)
                #export_rig.animation_data.action = None

            # push Unity action strips to NLA
            if prefs.export_animation_mode == "STRIPS" or prefs.export_animation_mode == "BOTH":
                for action in bpy.data.actions:
                    if is_unity_action(action):
                        utils.log_info(f"Adding {action.name} to NLA strips")
                        track = export_rig.animation_data.nla_tracks.new()
                        strip = track.strips.new(action.name, int(action.frame_range[0]), action)

            # reparent the child objects
            for child in rigify_rig.children:
                child.parent = export_rig
                mod = modifiers.get_object_modifier(child, "ARMATURE")
                mod.object = export_rig
                rename_to_unity_vertex_groups(child)

    select_rig(export_rig)

    return export_rig


def rename_to_unity_vertex_groups(obj):
    for export_def in rigify_mapping_data.UNITY_EXPORT_RIG:
        rigify_bone_name = export_def[0]
        unity_bone_name = export_def[2]
        if rigify_bone_name in obj.vertex_groups:
            obj.vertex_groups[rigify_bone_name].name = unity_bone_name


def restore_from_unity_vertex_groups(obj):
    for export_def in rigify_mapping_data.UNITY_EXPORT_RIG:
        rigify_bone_name = export_def[0]
        unity_bone_name = export_def[2]
        if unity_bone_name in obj.vertex_groups:
            obj.vertex_groups[unity_bone_name].name = rigify_bone_name


def finish_unity_export(chr_cache, export_rig):
    rigify_rig = chr_cache.get_armature()
    # un-reparent the child objects
    for child in export_rig.children:
        child.parent = rigify_rig
        mod = modifiers.get_object_modifier(child, "ARMATURE")
        mod.object = rigify_rig
        restore_from_unity_vertex_groups(child)
    # remove the t_pose_action and the export rig
    #t_pose_action = utils.safe_get_action(export_rig)
    #if t_pose_action:
    #    bpy.data.actions.remove(t_pose_action)


# Animation baking
#
#

def bake_rig_animation(chr_cache, rig, action, shape_key_objects, clear_constraints, limit_view_layer, action_name = ""):
    if utils.try_select_object(rig, True) and utils.set_active_object(rig):
        if action_name == "" and action:
            action_name = action.name
        name = action_name.split("|")[-1]
        # armature action
        baked_action = bpy.data.actions.new(f"{rig.name}|A|{name}")
        baked_action.use_fake_user = True
        utils.safe_set_action(rig, baked_action)
        # shape key actions
        if shape_key_objects:
            for obj in shape_key_objects:
                obj_name = utils.get_action_shape_key_object_name(obj.name)
                baked_action = bpy.data.actions.new(f"{rig.name}|K|{obj_name}|{name}")
                baked_action.use_fake_user = True
                utils.safe_set_action(obj.data.shape_keys, baked_action)
            utils.try_select_objects(shape_key_objects)
        # frame range
        if action:
            start_frame = int(action.frame_range[0])
            end_frame = int(action.frame_range[1])
        else:
            start_frame = int(bpy.context.scene.frame_start)
            end_frame = int(bpy.context.scene.frame_end)
        # turn off character physics
        physics_objects = physics.disable_physics(chr_cache)
        # limit view layer (bakes faster)
        if limit_view_layer:
            tmp_collection, layer_collections, to_hide = utils.limit_view_layer_to_collection("TMP_BAKE", rig, shape_key_objects)
        # bake
        bpy.ops.nla.bake(frame_start=start_frame,
                         frame_end=end_frame,
                         only_selected=True,
                         visual_keying=True,
                         use_current_action=True,
                         clear_constraints=clear_constraints,
                         clean_curves=False)
        # restore view layers
        if limit_view_layer:
            utils.restore_limited_view_layers(tmp_collection, layer_collections, to_hide)
        # turn on physics
        physics.enable_physics(chr_cache, physics_objects)


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


def is_unity_action(action):
    return "_Unity" in action.name and "|A|" in action.name


def check_armature_action(armature, action):
    total = 0
    matching = 0
    for fcurve in action.fcurves:
        total += 1
        bone_name = bones.get_bone_name_from_data_path(fcurve.data_path)
        if bone_name and bone_name in armature.data.bones:
            matching += 1
    return matching / total > 0


def get_armature_action_source_type(armature, action):
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
    # detect other types as they become available...
    return "Unknown", "Unknown"


class CC3Rigifier(bpy.types.Operator):
    """Rigify CC3 Character"""
    bl_idname = "cc3.rigifier"
    bl_label = "Rigifier"
    bl_options = {"REGISTER"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    cc3_rig = None
    meta_rig = None
    rigify_rig = None
    auto_weight_failed = False
    auto_weight_report = ""

    def add_meta_rig(self, chr_cache):

        utils.log_info("Generating Meta-Rig:")
        utils.log_indent()

        if utils.set_mode("OBJECT"):
            bpy.ops.object.armature_human_metarig_add()
            self.meta_rig = utils.get_active_object()
            if self.meta_rig is not None:
                utils.log_info("Meta-Rig added.")
                self.meta_rig.location = (0,0,0)
                if self.cc3_rig is not None:
                    self.cc3_rig.location = (0,0,0)
                    self.cc3_rig.data.pose_position = "REST"
                    utils.log_info("Aligning Meta-Rig.")
                    utils.log_indent()
                    match_meta_rig(chr_cache, self.cc3_rig, self.meta_rig, self.rigify_data)
                    utils.log_recess()
                else:
                    utils.log_error("Unable to locate imported CC3 rig!", self)
            else:
                utils.log_error("Unable to create meta rig!", self)
        else:
            utils.log_error("Not in OBJECT mode!", self)

        utils.log_recess()

    def execute(self, context):
        props: properties.CC3ImportProps = bpy.context.scene.CC3ImportProps
        chr_cache = props.get_context_character_cache(context)

        self.cc3_rig = None
        self.meta_rig = None
        self.rigify_rig = None
        self.auto_weight_failed = False
        self.auto_weight_report = ""

        if chr_cache:

            props.store_ui_list_indices()

            self.cc3_rig = chr_cache.get_armature()
            self.rigify_data = rigify_mapping_data.get_mapping_for_generation(chr_cache.generation)

            if self.param == "ALL":

                utils.start_timer()

                utils.log_info("")
                utils.log_info("Beginning Rigify Process:")
                utils.log_info("-------------------------")

                if self.cc3_rig:

                    olc = utils.set_active_layer_collection_from(self.cc3_rig)

                    self.add_meta_rig(chr_cache)

                    if self.meta_rig:
                        correct_meta_rig(self.meta_rig)

                        utils.log_timer("Done Meta-Rig Setup!")
                        utils.start_timer()

                        utils.log_info("")
                        utils.log_info("Generating Rigify Control Rig:")
                        utils.log_info("------------------------------")

                        bpy.ops.pose.rigify_generate()
                        self.rigify_rig = bpy.context.active_object

                        utils.log_info("")
                        utils.log_info("Finalizing Rigify Setup:")
                        utils.log_info("------------------------")

                        if self.rigify_rig:
                            if chr_cache.rig_full_face():
                                chr_cache.rigified_full_face_rig = True
                            else:
                                convert_to_basic_face_rig(self.rigify_rig)
                                chr_cache.rigified_full_face_rig = False
                            modify_rigify_rig(self.rigify_rig)
                            face_result = reparent_to_rigify(self, chr_cache, self.cc3_rig, self.rigify_rig)
                            add_def_bones(chr_cache, self.cc3_rig, self.rigify_rig)
                            add_shape_key_drivers(chr_cache, self.rigify_rig)
                            rename_vertex_groups(self.cc3_rig, self.rigify_rig, self.rigify_data.vertex_group_rename)
                            clean_up(chr_cache, self.cc3_rig, self.rigify_rig, self.meta_rig)

                    chr_cache.rig_meta_rig = None
                    if face_result == 1:
                        self.report({'INFO'}, "Rigify Complete! No errors detected.")
                    elif face_result == 0:
                        self.report({'WARNING'}, "Rigify Complete! Some issues with the face rig were detected and fixed automatically. See console log.")
                    else:
                        self.report({'ERROR'}, "Rigify Incomplete! Face rig weighting Failed!. See console log.")

                    utils.set_active_layer_collection(olc)

                utils.log_timer("Done Rigify Process!")

            elif self.param == "META_RIG":

                utils.start_timer()

                utils.log_info("")
                utils.log_info("Beginning Meta-Rig Setup:")
                utils.log_info("---------------==--------")

                if self.cc3_rig:

                    olc = utils.set_active_layer_collection_from(self.cc3_rig)

                    self.add_meta_rig(chr_cache)

                    if self.meta_rig:
                        chr_cache.rig_meta_rig = self.meta_rig
                        correct_meta_rig(self.meta_rig)

                        self.report({'INFO'}, "Meta-rig generated!")

                    utils.set_active_layer_collection(olc)

                utils.log_timer("Done Meta-Rig Setup!")

            elif self.param == "RIGIFY_META":

                self.meta_rig = chr_cache.rig_meta_rig

                if self.cc3_rig and self.meta_rig:

                    utils.start_timer()

                    olc = utils.set_active_layer_collection_from(self.cc3_rig)

                    if utils.set_mode("OBJECT") and utils.try_select_object(self.meta_rig) and utils.set_active_object(self.meta_rig):

                        utils.log_info("")
                        utils.log_info("Generating Rigify Control Rig:")
                        utils.log_info("------------------------------")

                        bpy.ops.pose.rigify_generate()
                        self.rigify_rig = bpy.context.active_object

                        utils.log_info("")
                        utils.log_info("Finalizing Rigify Setup:")
                        utils.log_info("------------------------")

                        if self.rigify_rig:
                            if chr_cache.rig_full_face():
                                chr_cache.rigified_full_face_rig = True
                            else:
                                convert_to_basic_face_rig(self.rigify_rig)
                                chr_cache.rigified_full_face_rig = False
                            modify_rigify_rig(self.rigify_rig)
                            face_result = reparent_to_rigify(self, chr_cache, self.cc3_rig, self.rigify_rig)
                            add_def_bones(chr_cache, self.cc3_rig, self.rigify_rig)
                            add_shape_key_drivers(chr_cache, self.rigify_rig)
                            rename_vertex_groups(self.cc3_rig, self.rigify_rig, self.rigify_data.vertex_group_rename)
                            clean_up(chr_cache, self.cc3_rig, self.rigify_rig, self.meta_rig)

                    utils.set_active_layer_collection(olc)

                utils.log_timer("Done Rigify Process!")

                chr_cache.rig_meta_rig = None
                if face_result == 1:
                    self.report({'INFO'}, "Rigify Complete! No errors detected.")
                elif face_result == 0:
                    self.report({'WARNING'}, "Rigify Complete! Some issues with the face rig were detected and fixed automatically. See console log.")
                else:
                    self.report({'ERROR'}, "Rigify Incomplete! Face rig weighting Failed!. See console log.")

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
                lock_non_face_vgroups(chr_cache)
                clean_up_character_meshes(chr_cache)
                result = attempt_reparent_auto_character(chr_cache)
                unlock_vgroups(chr_cache)
                if result == 1:
                    self.report({'INFO'}, "Face Re-parent Done!. No errors.")
                elif result == 0:
                    self.report({'WARNING'}, "Face Re-parent Done!. Some issues with the face rig were detected and fixed automatically. See console log.")
                else:
                    self.report({'ERROR'}, "Face Re-parent Failed!. See console log.")

            elif self.param == "BAKE_UNITY_ANIMATION":
                adv_bake_rigify_to_unity(self, chr_cache)

            elif self.param == "RETARGET_CC_PAIR_RIGS":
                adv_preview_retarget(self, chr_cache)

            elif self.param == "RETARGET_CC_REMOVE_PAIR":
                adv_retarget_remove_pair(self, chr_cache)

            elif self.param == "RETARGET_CC_BAKE_ACTION":
                adv_bake_retarget_to_rigify(self, chr_cache)

            elif self.param == "NLA_CC_BAKE":
                adv_bake_NLA_to_rigify(self, chr_cache)

            elif self.param == "NLA_CC_BAKE_UNITY":
                adv_bake_rigify_NLA_to_unity(self, chr_cache)

            elif self.param == "RETARGET_SHAPE_KEYS":
                adv_retarget_shape_keys(self, chr_cache, True)

            props.restore_ui_list_indices()

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "ALL":
            return "Rigify the character, all in one go"

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

        elif properties.param == "BAKE_UNITY_ANIMATION":
            return "Bake the current Rigify action (or Retarget action) to the Unity export rig"

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

        elif properties.param == "NLA_CC_BAKE_UNITY":
            return "Bake the NLA track to to the Unity export rig using the global scene frame range."

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
    voxel_skinning = False
    voxel_skinning_finish = False
    processing = False
    dummy_cube = None
    head_mesh = None
    body_mesh = None

    def modal(self, context, event):

        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER' and not self.processing:

            if self.voxel_skinning and self.dummy_cube:
                self.processing = True
                try:
                    if self.dummy_cube.parent is not None:
                        self.voxel_skinning = False
                        self.voxel_skinning_finish = True
                except:
                    pass
                self.processing = False
                return {'PASS_THROUGH'}


            if self.voxel_skinning_finish:
                self.processing = True
                self.voxel_re_parent_two(context)
                self.cancel(context)
                self.processing = False
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):
        if self.timer is not None:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None
            self.voxel_skinning = False
            voxel_skinning_finish = False

    def execute(self, context):
        props: properties.CC3ImportProps = bpy.context.scene.CC3ImportProps
        chr_cache = props.get_context_character_cache(context)

        if chr_cache:
            if self.param == "VOXEL_SKINNING":
                self.voxel_re_parent_one(context)
                return {'RUNNING_MODAL'}

        return {"FINISHED"}

    def voxel_re_parent_one(self, context):
        props: properties.CC3ImportProps = bpy.context.scene.CC3ImportProps
        chr_cache = props.get_context_character_cache(context)

        lock_non_face_vgroups(chr_cache)
        store_non_face_vgroups(chr_cache)
        # as we have no way of knowing when the operator finishes, we add
        # a dummy cube (unparented) to the objects being skinned and parented.
        # Since the parenting to the armature is the last thing
        # the voxel skinning operator does, we can watch for that to happen.
        self.dummy_cube, self.head_mesh, self.body_mesh = attempt_reparent_voxel_skinning(chr_cache)

        self.voxel_skinning = True
        bpy.context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(1.0, window = bpy.context.window)

    def voxel_re_parent_two(self, context):
        props: properties.CC3ImportProps = bpy.context.scene.CC3ImportProps
        chr_cache = props.get_context_character_cache(context)

        if self.dummy_cube:
            bpy.data.objects.remove(self.dummy_cube)
            self.dummy_cube = None

        if self.head_mesh and self.body_mesh:
            rejoin_head(self.head_mesh, self.body_mesh)
            self.head_mesh = None
            self.body_mesh = None

        restore_non_face_vgroups(chr_cache)
        unlock_vgroups(chr_cache)

        arm = chr_cache.get_armature()
        if arm and utils.set_mode("OBJECT"):
            if utils.try_select_object(arm, True) and utils.set_active_object(arm):
                utils.set_mode("POSE")

        self.report({'INFO'}, "Voxel Face Re-parent Done!")

    @classmethod
    def description(cls, context, properties):
        if properties.param == "VOXEL_SKINNING":
            return "Attempt to re-parent the character's face objects to the Rigify face rig by using voxel surface head diffuse skinning"

        return ""

