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

from dataclasses import dataclass

@dataclass
class RigifyData:
    """Class for keeping all data relating to bones mapping for rigify."""
    head_bone: str
    bone_mapping: list
    face_bones: list
    add_def_bones: list
    vertex_group_rename: list
    roll_copy: list


def get_default():
    return RigifyData("CC_Base_Head", G3_BONE_MAPPINGS, FACE_BONES, ADD_DEF_BONES, G3_VERTEX_GROUP_RENAME, G3_ROLL_COPY)


#   METARIG_BONE, CC_BONE_HEAD, CC_BONE_TAIL, LERP_FROM, LERP_TO
#   '-' before CC_BONE_HEAD means to copy the tail position, not the head
#   '-' before CC_BONE_TAIL means to copy the head position, not the tail
BONE_MAPPINGS = [

    # Spine, Neck & Head:
    # spine chain
    ["spine", "CC_Base_Hip", ""],
    ["spine.001", "CC_Base_Waist", ""],
    ["spine.002", "CC_Base_Spine01", ""],
    ["spine.003", "CC_Base_Spine02", "-CC_Base_NeckTwist01"],
    ["spine.004", "CC_Base_NeckTwist01", ""],
    ["spine.005", "CC_Base_NeckTwist02", ""],
    ["spine.006", "CC_Base_Head", "CC_Base_Head"], # special case
    ["face", "CC_Base_FacialBone", "CC_Base_FacialBone"], # special case
    ["pelvis", "CC_Base_Pelvis", "CC_Base_Pelvis"],

    # Left Breast
    ["breast.L", "CC_Base_L_Breast", "CC_Base_L_Breast"],
    # Right Breast
    ["breast.R", "CC_Base_R_Breast", "CC_Base_R_Breast"],

    # Left Leg:
    ["thigh.L", "CC_Base_L_Thigh", ""],
    ["shin.L", "CC_Base_L_Calf", ""],
    ["foot.L", "CC_Base_L_Foot", ""],
    ["toe.L", "CC_Base_L_ToeBase", "CC_Base_L_ToeBase"],

    # Left Arm:
    ["shoulder.L", "CC_Base_L_Clavicle", "CC_Base_L_Clavicle"],
    # chain
    ["upper_arm.L", "CC_Base_L_Upperarm", ""],
    ["forearm.L", "CC_Base_L_Forearm", ""],
    ["hand.L", "CC_Base_L_Hand", "CC_Base_L_Hand", 0, 0.75],
    ["palm.01.L", "CC_Base_L_Hand", "-CC_Base_L_Index1", 0.35, 1],
    ["palm.02.L", "CC_Base_L_Hand", "-CC_Base_L_Mid1", 0.35, 1],
    ["palm.03.L", "CC_Base_L_Hand", "-CC_Base_L_Ring1", 0.35, 1],
    ["palm.04.L", "CC_Base_L_Hand", "-CC_Base_L_Pinky1", 0.35, 1],
    # Left Hand Fingers, chains
    ["thumb.01.L", "CC_Base_L_Thumb1", ""],
    ["f_index.01.L", "CC_Base_L_Index1", ""],
    ["f_middle.01.L", "CC_Base_L_Mid1", ""],
    ["f_ring.01.L", "CC_Base_L_Ring1", ""],
    ["f_pinky.01.L", "CC_Base_L_Pinky1", ""],
    ["thumb.02.L", "CC_Base_L_Thumb2", ""],
    ["f_index.02.L", "CC_Base_L_Index2", ""],
    ["f_middle.02.L", "CC_Base_L_Mid2", ""],
    ["f_ring.02.L", "CC_Base_L_Ring2", ""],
    ["f_pinky.02.L", "CC_Base_L_Pinky2", ""],
    ["thumb.03.L", "CC_Base_L_Thumb3", "CC_Base_L_Thumb3"],
    ["f_index.03.L", "CC_Base_L_Index3", "CC_Base_L_Index3"],
    ["f_middle.03.L", "CC_Base_L_Mid3", "CC_Base_L_Mid3"],
    ["f_ring.03.L", "CC_Base_L_Ring3", "CC_Base_L_Ring3"],
    ["f_pinky.03.L", "CC_Base_L_Pinky3", "CC_Base_L_Pinky3"],

    # Right Leg, chain
    ["thigh.R", "CC_Base_R_Thigh", ""],
    ["shin.R", "CC_Base_R_Calf", ""],
    ["foot.R", "CC_Base_R_Foot", ""],
    ["toe.R", "CC_Base_R_ToeBase", "CC_Base_R_ToeBase"],

    # Right Arm:
    ["shoulder.R", "CC_Base_R_Clavicle", "CC_Base_R_Clavicle"],
    ["upper_arm.R", "CC_Base_R_Upperarm", ""],
    ["forearm.R", "CC_Base_R_Forearm", ""],
    ["hand.R", "CC_Base_R_Hand", "CC_Base_R_Hand", 0, 0.75],
    ["palm.01.R", "CC_Base_R_Hand", "-CC_Base_R_Index1", 0.35, 1],
    ["palm.02.R", "CC_Base_R_Hand", "-CC_Base_R_Mid1", 0.35, 1],
    ["palm.03.R", "CC_Base_R_Hand", "-CC_Base_R_Ring1", 0.35, 1],
    ["palm.04.R", "CC_Base_R_Hand", "-CC_Base_R_Pinky1", 0.35, 1],
    # Right Hand Fingers, chains
    ["thumb.01.R", "CC_Base_R_Thumb1", ""],
    ["f_index.01.R", "CC_Base_R_Index1", ""],
    ["f_middle.01.R", "CC_Base_R_Mid1", ""],
    ["f_ring.01.R", "CC_Base_R_Ring1", ""],
    ["f_pinky.01.R", "CC_Base_R_Pinky1", ""],
    ["thumb.02.R", "CC_Base_R_Thumb2", ""],
    ["f_index.02.R", "CC_Base_R_Index2", ""],
    ["f_middle.02.R", "CC_Base_R_Mid2", ""],
    ["f_ring.02.R", "CC_Base_R_Ring2", ""],
    ["f_pinky.02.R", "CC_Base_R_Pinky2", ""],
    ["thumb.03.R", "CC_Base_R_Thumb3", "CC_Base_R_Thumb3"],
    ["f_index.03.R", "CC_Base_R_Index3", "CC_Base_R_Index3"],
    ["f_middle.03.R", "CC_Base_R_Mid3", "CC_Base_R_Mid3"],
    ["f_ring.03.R", "CC_Base_R_Ring3", "CC_Base_R_Ring3"],
    ["f_pinky.03.R", "CC_Base_R_Pinky3", "CC_Base_R_Pinky3"],

    ["tongue", "CC_Base_Tongue03", "CC_Base_Tongue02"],
    ["tongue.001", "CC_Base_Tongue02", "CC_Base_Tongue01"],
    ["tongue.002", "CC_Base_Tongue01", "CC_Base_JawRoot", 0, 0.65],

    ["teeth.T", "CC_Base_Teeth01", "CC_Base_Teeth01"],
    ["teeth.B", "CC_Base_Teeth02", "CC_Base_Teeth02"],

    ["eye.R", "CC_Base_R_Eye", ""],
    ["eye.L", "CC_Base_L_Eye", ""],

    ["eye.L", "CC_Base_L_Eye", ""],

    # only when using the basic face rig, a jaw bone is created that needs positioning...
    ["jaw", "CC_Base_JawRoot", "CC_Base_Tongue03", 0, 1.35],
]

FACE_BONES = [
    ["face", "spine.006", "LR", 0],
    ["eye.L", "face", "LR", 0],
    ["eye.R", "face", "LR", 0],
    ["jaw", "face", "LR", 0, "JAW"],
    ["teeth.T", "face", "LR", 0],
    ["teeth.B", "jaw", "LR", 0],
    ["tongue", "jaw", "LR", 0, "TONGUE"],
    ["tongue.001", "tongue", "CLR", 0],
    ["tongue.002", "tongue.001", "CLR", 0],
]

# additional bones to copy from the cc3 or rigify rigs to generate rigify deformation, mech or control bones
# [source_bone, new_rigify_bone, rigify_parent, flags, layer, scale, ref, arg]
# flags C=Connected, L=Local location, R=Inherit rotation
# layers: 31 = ORG bones, 30 = MCH bones, 29 = DEF bones
# ref: reference bone(s) for position generation or constraints
# arg: constraint args (influence)
ADD_DEF_BONES = [

    ["ORG-eye.R", "DEF-eye.R", "ORG-eye.R", "LR", 29],
    ["ORG-eye.L", "DEF-eye.L", "ORG-eye.L", "LR", 29],

    ["ORG-teeth.T", "DEF-teeth.T", "ORG-teeth.T", "LR", 29],
    ["ORG-teeth.B", "DEF-teeth.B", "ORG-teeth.B", "LR", 29],

    ["CC_Base_L_RibsTwist", "DEF-breast_twist.L", "ORG-breast.L", "LR", 29],
    ["CC_Base_R_RibsTwist", "DEF-breast_twist.R", "ORG-breast.R", "LR", 29],
    # "-" instructs to re-parent the existing DEF-breast bones to the new DEF-breast_twist bones.
    ["-", "DEF-breast.L", "DEF-breast_twist.L", "LR", 29],
    ["-", "DEF-breast.R", "DEF-breast_twist.R", "LR", 29],

    ["DEF-forearm.L", "DEF-elbow_share.L", "DEF-forearm.L", "LR", 29, 0.667, "DEF-upper_arm.L.001", 0.95],
    ["DEF-shin.L", "DEF-knee_share.L", "DEF-shin.L", "LR", 29, 0.667, "DEF-thigh.L.001", 0.5],

    ["CC_Base_L_BigToe1", "DEF-toe_big.L", "DEF-toe.L", "LR", 29],
    ["CC_Base_L_IndexToe1", "DEF-toe_index.L", "DEF-toe.L", "LR", 29],
    ["CC_Base_L_MidToe1", "DEF-toe_mid.L", "DEF-toe.L", "LR", 29],
    ["CC_Base_L_RingToe1", "DEF-toe_ring.L", "DEF-toe.L", "LR", 29],
    ["CC_Base_L_PinkyToe1", "DEF-toe_pinky.L", "DEF-toe.L", "LR", 29],

    ["DEF-forearm.R", "DEF-elbow_share.R", "DEF-forearm.R", "LR", 29, 0.667, "DEF-upper_arm.R.001", 0.95],
    ["DEF-shin.R", "DEF-knee_share.R", "DEF-shin.R", "LR", 29, 0.667, "DEF-thigh.R.001", 0.5],

    ["CC_Base_R_BigToe1", "DEF-toe_big.R", "DEF-toe.R", "LR", 29],
    ["CC_Base_R_IndexToe1", "DEF-toe_index.R", "DEF-toe.R", "LR", 29],
    ["CC_Base_R_MidToe1", "DEF-toe_mid.R", "DEF-toe.R", "LR", 29],
    ["CC_Base_R_RingToe1", "DEF-toe_ring.R", "DEF-toe.R", "LR", 29],
    ["CC_Base_R_PinkyToe1", "DEF-toe_pinky.R", "DEF-toe.R", "LR", 29],

    ["+MCHEyeParent", "MCH-eyes_parent", "ORG-face", "LR", 30],
    ["+EyeControl", "eyes", "MCH-eyes_parent", "LR", 1, 0.2, ["ORG-eye.L", "ORG-eye.R"]],
    ["+EyeControl", "eye.L", "eyes", "LR", 1,           0.2, ["ORG-eye.L"]],
    ["+EyeControl", "eye.R", "eyes", "LR", 1,           0.2, ["ORG-eye.R"]],
    ["#RenameBasicFace", "jaw", "jaw_master", "", 1],
]

VERTEX_GROUP_RENAME = [
    # Spine, Neck & Head:
    ["DEF-pelvis", "CC_Base_Pelvis"],
    ["DEF-spine", "CC_Base_Hip"],
    ["DEF-spine.001", "CC_Base_Waist"],
    ["DEF-spine.002", "CC_Base_Spine01"],
    ["DEF-spine.003", "CC_Base_Spine02"],
    ["DEF-spine.004", "CC_Base_NeckTwist01"],
    ["DEF-spine.005", "CC_Base_NeckTwist02"],
    ["DEF-spine.006", "CC_Base_Head"],
    # Left Breast:
    ["DEF-breast_twist.L", "CC_Base_L_RibsTwist"],
    ["DEF-breast.L", "CC_Base_L_Breast"],
    # Right Breast:
    ["DEF-breast_twist.R", "CC_Base_R_RibsTwist"],
    ["DEF-breast.R", "CC_Base_R_Breast"],
    # Left Leg:
    ["DEF-thigh.L", "CC_Base_L_ThighTwist01"],
    ["DEF-thigh.L.001", "CC_Base_L_ThighTwist02"],
    ["DEF-knee_share.L", "CC_Base_L_KneeShareBone"],
    ["DEF-shin.L", "CC_Base_L_CalfTwist01"],
    ["DEF-shin.L.001", "CC_Base_L_CalfTwist02"],
    ["DEF-foot.L", "CC_Base_L_Foot"],
    ["DEF-toe.L", "CC_Base_L_ToeBase"],
    # Left Foot:
    ["DEF-toe_big.L", "CC_Base_L_BigToe1"],
    ["DEF-toe_index.L", "CC_Base_L_IndexToe1"],
    ["DEF-toe_mid.L", "CC_Base_L_MidToe1"],
    ["DEF-toe_ring.L", "CC_Base_L_RingToe1"],
    ["DEF-toe_pinky.L", "CC_Base_L_PinkyToe1"],
    # Left Arm:
    ["DEF-shoulder.L", "CC_Base_L_Clavicle"],
    ["DEF-upper_arm.L", "CC_Base_L_UpperarmTwist01"],
    ["DEF-upper_arm.L.001", "CC_Base_L_UpperarmTwist02"],
    ["DEF-elbow_share.L", "CC_Base_L_ElbowShareBone"],
    ["DEF-forearm.L", "CC_Base_L_ForearmTwist01"],
    ["DEF-forearm.L.001", "CC_Base_L_ForearmTwist02"],
    ["DEF-hand.L", "CC_Base_L_Hand"],
    # Left Hand Fingers:
    ["DEF-thumb.01.L", "CC_Base_L_Thumb1"],
    ["DEF-f_index.01.L", "CC_Base_L_Index1"],
    ["DEF-f_middle.01.L", "CC_Base_L_Mid1"],
    ["DEF-f_ring.01.L", "CC_Base_L_Ring1"],
    ["DEF-f_pinky.01.L", "CC_Base_L_Pinky1"],
    ["DEF-thumb.02.L", "CC_Base_L_Thumb2"],
    ["DEF-f_index.02.L", "CC_Base_L_Index2"],
    ["DEF-f_middle.02.L", "CC_Base_L_Mid2"],
    ["DEF-f_ring.02.L", "CC_Base_L_Ring2"],
    ["DEF-f_pinky.02.L", "CC_Base_L_Pinky2"],
    ["DEF-thumb.03.L", "CC_Base_L_Thumb3"],
    ["DEF-f_index.03.L", "CC_Base_L_Index3"],
    ["DEF-f_middle.03.L", "CC_Base_L_Mid3"],
    ["DEF-f_ring.03.L", "CC_Base_L_Ring3"],
    ["DEF-f_pinky.03.L", "CC_Base_L_Pinky3"],
    # Right Leg:
    ["DEF-thigh.R", "CC_Base_R_ThighTwist01"],
    ["DEF-thigh.R.001", "CC_Base_R_ThighTwist02"],
    ["DEF-knee_share.R", "CC_Base_R_KneeShareBone"],
    ["DEF-shin.R", "CC_Base_R_CalfTwist01"],
    ["DEF-shin.R.001", "CC_Base_R_CalfTwist02"],
    ["DEF-foot.R", "CC_Base_R_Foot"],
    ["DEF-toe.R", "CC_Base_R_ToeBase"],
    # Right Foot:
    ["DEF-toe_big.R", "CC_Base_R_BigToe1"],
    ["DEF-toe_index.R", "CC_Base_R_IndexToe1"],
    ["DEF-toe_mid.R", "CC_Base_R_MidToe1"],
    ["DEF-toe_ring.R", "CC_Base_R_RingToe1"],
    ["DEF-toe_pinky.R", "CC_Base_R_PinkyToe1"],
    # Right Arm:
    ["DEF-shoulder.R", "CC_Base_R_Clavicle"],
    ["DEF-upper_arm.R", "CC_Base_R_UpperarmTwist01"],
    ["DEF-upper_arm.R.001", "CC_Base_R_UpperarmTwist02"],
    ["DEF-elbow_share.R", "CC_Base_R_ElbowShareBone"],
    ["DEF-forearm.R", "CC_Base_R_ForearmTwist01"],
    ["DEF-forearm.R.001", "CC_Base_R_ForearmTwist02"],
    ["DEF-hand.R", "CC_Base_R_Hand"],
    # Right Hand Fingers:
    ["DEF-thumb.01.R", "CC_Base_R_Thumb1"],
    ["DEF-f_index.01.R", "CC_Base_R_Index1"],
    ["DEF-f_middle.01.R", "CC_Base_R_Mid1"],
    ["DEF-f_ring.01.R", "CC_Base_R_Ring1"],
    ["DEF-f_pinky.01.R", "CC_Base_R_Pinky1"],
    ["DEF-thumb.02.R", "CC_Base_R_Thumb2"],
    ["DEF-f_index.02.R", "CC_Base_R_Index2"],
    ["DEF-f_middle.02.R", "CC_Base_R_Mid2"],
    ["DEF-f_ring.02.R", "CC_Base_R_Ring2"],
    ["DEF-f_pinky.02.R", "CC_Base_R_Pinky2"],
    ["DEF-thumb.03.R", "CC_Base_R_Thumb3"],
    ["DEF-f_index.03.R", "CC_Base_R_Index3"],
    ["DEF-f_middle.03.R", "CC_Base_R_Mid3"],
    ["DEF-f_ring.03.R", "CC_Base_R_Ring3"],
    ["DEF-f_pinky.03.R", "CC_Base_R_Pinky3"],
    # Tongue:
    ["DEF-tongue", "CC_Base_Tongue03"],
    ["DEF-tongue.001", "CC_Base_Tongue02"],
    ["DEF-tongue.002", "CC_Base_Tongue01"],
    # Teeth:
    ["DEF-teeth.T", "CC_Base_Teeth01"],
    ["DEF-teeth.B", "CC_Base_Teeth02"],
    # Eyes:
    ["DEF-eye.R", "CC_Base_R_Eye"],
    ["DEF-eye.L", "CC_Base_L_Eye"],
    # Jaw:
    ["DEF-jaw", "CC_Base_JawRoot"],
]

# the rigify meta rig and the cc3 bones don't always match for roll angles,
# correct them by copying from the cc3 bones and adjusting to match the orientation the meta rig expects.
# ["meta rig name", roll_adjust, "cc3 rig name"],
ROLL_COPY = [
    # Spine, Neck & Head:
    # spine chain
    ["spine", 0, "CC_Base_Pelvis"],
    ["spine.001", 0, "CC_Base_Waist"],
    ["spine.002", 0, "CC_Base_Spine01"],
    ["spine.003", 0, "CC_Base_Spine02"],
    ["spine.004", 0, "CC_Base_NeckTwist01"],
    ["spine.005", 0, "CC_Base_NeckTwist02"],
    ["spine.006", 0, "CC_Base_Head"], # todo
    ["face", 0, "CC_Base_FacialBone"], # todo
    ["pelvis", -180, "CC_Base_Pelvis"],

    # Left Breast
    ["breast.L", 0, "CC_Base_L_Breast"],
    # Right Breast
    ["breast.R", 0, "CC_Base_R_Breast"],

    # Left Leg:
    ["thigh.L", 180, "CC_Base_L_Thigh"],
    ["shin.L", 180, "CC_Base_L_Calf"],
    ["foot.L", 180, "CC_Base_L_Foot"],
    ["toe.L", 0, "CC_Base_L_ToeBaseShareBone"],

    # Left Arm:
    ["shoulder.L", -90, "CC_Base_L_Clavicle"],
    # chain
    ["upper_arm.L", 0, "CC_Base_L_Upperarm"],
    ["forearm.L", 0, "CC_Base_L_Forearm"],
    ["hand.L", 0, "CC_Base_L_Hand"],
    ["palm.01.L", 90, "CC_Base_L_Hand"],
    ["palm.02.L", 90, "CC_Base_L_Hand"],
    ["palm.03.L", 90, "CC_Base_L_Hand"],
    ["palm.04.L", 90, "CC_Base_L_Hand"],
    # Left Hand Fingers, chains
    ["thumb.01.L", 180, "CC_Base_L_Thumb1"],
    ["f_index.01.L", 90, "CC_Base_L_Index1"],
    ["f_middle.01.L", 90, "CC_Base_L_Mid1"],
    ["f_ring.01.L", 90, "CC_Base_L_Ring1"],
    ["f_pinky.01.L", 90, "CC_Base_L_Pinky1"],
    ["thumb.02.L", 180, "CC_Base_L_Thumb2"],
    ["f_index.02.L", 90, "CC_Base_L_Index2"],
    ["f_middle.02.L", 90, "CC_Base_L_Mid2"],
    ["f_ring.02.L", 90, "CC_Base_L_Ring2"],
    ["f_pinky.02.L", 90, "CC_Base_L_Pinky2"],
    ["thumb.03.L", 180, "CC_Base_L_Thumb3"],
    ["f_index.03.L", 90, "CC_Base_L_Index3"],
    ["f_middle.03.L", 90, "CC_Base_L_Mid3"],
    ["f_ring.03.L", 90, "CC_Base_L_Ring3"],
    ["f_pinky.03.L", 90, "CC_Base_L_Pinky3"],

    # Right Leg, chain
    ["thigh.R", -180, "CC_Base_R_Thigh"],
    ["shin.R", -180, "CC_Base_R_Calf"],
    ["foot.R", -180, "CC_Base_R_Foot"],
    ["toe.R", 0, "CC_Base_R_ToeBaseShareBone"],

    # Right Arm:
    ["shoulder.R", 90, "CC_Base_R_Clavicle"],
    ["upper_arm.R", 0, "CC_Base_R_Upperarm"],
    ["forearm.R", 0, "CC_Base_R_Forearm"],
    ["hand.R", 0, "CC_Base_R_Hand"],
    ["palm.01.R", -90, "CC_Base_R_Hand"],
    ["palm.02.R", -90, "CC_Base_R_Hand"],
    ["palm.03.R", -90, "CC_Base_R_Hand"],
    ["palm.04.R", -90, "CC_Base_R_Hand"],
    # Right Hand Fingers, chains
    ["thumb.01.R", -180, "CC_Base_R_Thumb1"],
    ["f_index.01.R", -90, "CC_Base_R_Index1"],
    ["f_middle.01.R", -90, "CC_Base_R_Mid1"],
    ["f_ring.01.R", -90, "CC_Base_R_Ring1"],
    ["f_pinky.01.R", -90, "CC_Base_R_Pinky1"],
    ["thumb.02.R", -180, "CC_Base_R_Thumb2"],
    ["f_index.02.R", -90, "CC_Base_R_Index2"],
    ["f_middle.02.R", -90, "CC_Base_R_Mid2"],
    ["f_ring.02.R", -90, "CC_Base_R_Ring2"],
    ["f_pinky.02.R", -90, "CC_Base_R_Pinky2"],
    ["thumb.03.R", -180, "CC_Base_R_Thumb3"],
    ["f_index.03.R", -90, "CC_Base_R_Index3"],
    ["f_middle.03.R", -90, "CC_Base_R_Mid3"],
    ["f_ring.03.R", -90, "CC_Base_R_Ring3"],
    ["f_pinky.03.R", -90, "CC_Base_R_Pinky3"],
]
