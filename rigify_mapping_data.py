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

from dataclasses import dataclass

@dataclass
class RigifyData:
    """Class for keeping all data relating to bones mapping for rigify."""
    head_bone: str
    bone_mapping: list
    vertex_group_rename: list


@dataclass
class RetargetData:
    """Class for keeping all data relating to bones mapping for rigify."""
    retarget: list
    retarget_corrections: dict


def get_mapping_for_generation(generation):
    if generation == "GameBase":
        return RigifyData("head",
                          GAME_BASE_BONE_MAPPINGS,
                          GAME_BASE_VERTEX_GROUP_RENAME)

    elif generation == "ActorCore" or generation == "G3" or generation == "G3Plus":
        return RigifyData("CC_Base_Head",
                          G3_BONE_MAPPINGS,
                          G3_VERTEX_GROUP_RENAME)

    else:
        return None


def get_retarget_for_source(source):
    if source == "G3":
        return RetargetData(RETARGET_G3, RETARGET_CORRECTIONS)

    elif source == "GameBase":
        return RetargetData(RETARGET_GAME_BASE, RETARGET_CORRECTIONS)

    elif source == "Mixamo":
        return RetargetData(RETARGET_MIXAMO, RETARGET_CORRECTIONS)

    elif source == "Rokoko":
        return None

    elif source == "Maya":
        return None

    elif source == "ARP":
        return None

    else:
        return None


#   METARIG_BONE, CC_BONE_HEAD, CC_BONE_TAIL, LERP_FROM, LERP_TO
#   '-' before CC_BONE_HEAD means to copy the tail position, not the head
#   '-' before CC_BONE_TAIL means to copy the head position, not the tail
G3_BONE_MAPPINGS = [

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
]


GAME_BASE_BONE_MAPPINGS = [
    # Spine, Neck & Head:
    # spine chain
    ["pelvis", "pelvis", "pelvis"],
    ["spine", "pelvis", ""],
    ["spine.001", "spine_01", ""],
    ["spine.002", "spine_02", ""],
    ["spine.003", "spine_03", "-neck_01"],
    # moved spine.004 and spine.005 into a 50/50 split of neck_01
    # as retargeting animations to the neck uses spine.004 as the base of the neck
    ["spine.004", "neck_01", "neck_01", 0, 0.5],
    ["spine.005", "neck_01", "neck_01", 0.5, 1],
    ["spine.006", "head", "head"], # special case
    ["face", "CC_Base_FacialBone", "CC_Base_FacialBone"], # special case

    # Left Breast
    ["breast.L", "CC_Base_L_RibsTwist", "CC_Base_L_RibsTwist", 0, 0.2],
    # Right Breast
    ["breast.R", "CC_Base_R_RibsTwist", "CC_Base_R_RibsTwist", 0, 0.2],

    # Left Leg:
    ["thigh.L", "thigh_l", ""],
    ["shin.L", "calf_l", ""],
    ["foot.L", "foot_l", ""],
    ["toe.L", "ball_l", "ball_l"],

    # Left Arm:
    ["shoulder.L", "clavicle_l", "clavicle_l"],
    # chain
    ["upper_arm.L", "upperarm_l", ""],
    ["forearm.L", "lowerarm_l", ""],
    ["hand.L", "hand_l", "hand_l", 0, 0.75],
    ["palm.01.L", "hand_l", "-index_01_l", 0.35, 1],
    ["palm.02.L", "hand_l", "-middle_01_l", 0.35, 1],
    ["palm.03.L", "hand_l", "-ring_01_l", 0.35, 1],
    ["palm.04.L", "hand_l", "-pinky_01_l", 0.35, 1],
    # Left Hand Fingers, chains
    ["thumb.01.L", "thumb_01_l", ""],
    ["f_index.01.L", "index_01_l", ""],
    ["f_middle.01.L", "middle_01_l", ""],
    ["f_ring.01.L", "ring_01_l", ""],
    ["f_pinky.01.L", "pinky_01_l", ""],
    ["thumb.02.L", "thumb_02_l", ""],
    ["f_index.02.L", "index_02_l", ""],
    ["f_middle.02.L", "middle_02_l", ""],
    ["f_ring.02.L", "ring_02_l", ""],
    ["f_pinky.02.L", "pinky_02_l", ""],
    ["thumb.03.L", "thumb_03_l", "thumb_03_l"],
    ["f_index.03.L", "index_03_l", "index_03_l"],
    ["f_middle.03.L", "middle_03_l", "middle_03_l"],
    ["f_ring.03.L", "ring_03_l", "ring_03_l"],
    ["f_pinky.03.L", "pinky_03_l", "pinky_03_l"],

    # Right Leg, chain
    ["thigh.R", "thigh_r", ""],
    ["shin.R", "calf_r", ""],
    ["foot.R", "foot_r", ""],
    ["toe.R", "ball_r", "ball_r"],

    # Right Arm:
    ["shoulder.R", "clavicle_r", "clavicle_r"],
    ["upper_arm.R", "upperarm_r", ""],
    ["forearm.R", "lowerarm_r", ""],
    ["hand.R", "hand_r", "hand_r", 0, 0.75],
    ["palm.01.R", "hand_r", "-index_01_r", 0.35, 1],
    ["palm.02.R", "hand_r", "-middle_01_r", 0.35, 1],
    ["palm.03.R", "hand_r", "-ring_01_r", 0.35, 1],
    ["palm.04.R", "hand_r", "-pinky_01_r", 0.35, 1],
    # Right Hand Fingers, chains
    ["thumb.01.R", "thumb_01_r", ""],
    ["f_index.01.R", "index_01_r", ""],
    ["f_middle.01.R", "middle_01_r", ""],
    ["f_ring.01.R", "ring_01_r", ""],
    ["f_pinky.01.R", "pinky_01_r", ""],
    ["thumb.02.R", "thumb_02_r", ""],
    ["f_index.02.R", "index_02_r", ""],
    ["f_middle.02.R", "middle_02_r", ""],
    ["f_ring.02.R", "ring_02_r", ""],
    ["f_pinky.02.R", "pinky_02_r", ""],
    ["thumb.03.R", "thumb_03_r", "thumb_03_r"],
    ["f_index.03.R", "index_03_r", "index_03_r"],
    ["f_middle.03.R", "middle_03_r", "middle_03_r"],
    ["f_ring.03.R", "ring_03_r", "ring_03_r"],
    ["f_pinky.03.R", "pinky_03_r", "pinky_03_r"],

    ["tongue", "CC_Base_Tongue03", "CC_Base_Tongue02"],
    ["tongue.001", "CC_Base_Tongue02", "CC_Base_Tongue01"],
    ["tongue.002", "CC_Base_Tongue01", "CC_Base_JawRoot", 0, 0.65],

    ["teeth.T", "CC_Base_Teeth01", "CC_Base_Teeth01"],
    ["teeth.B", "CC_Base_Teeth02", "CC_Base_Teeth02"],

    ["eye.R", "CC_Base_R_Eye", ""],
    ["eye.L", "CC_Base_L_Eye", ""],
]


G3_VERTEX_GROUP_RENAME = [
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
    ["DEF-thigh.L", "CC_Base_L_Thigh"],
    ["DEF-thigh.L", "CC_Base_L_ThighTwist01"],
    ["DEF-thigh.L.001", "CC_Base_L_ThighTwist02"],
    ["DEF-knee_share.L", "CC_Base_L_KneeShareBone"],
    ["DEF-shin.L", "CC_Base_L_Calf"],
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
    ["DEF-upper_arm.L", "CC_Base_L_Upperarm"],
    ["DEF-upper_arm.L", "CC_Base_L_UpperarmTwist01"],
    ["DEF-upper_arm.L.001", "CC_Base_L_UpperarmTwist02"],
    ["DEF-elbow_share.L", "CC_Base_L_ElbowShareBone"],
    ["DEF-forearm.L", "CC_Base_L_Forearm"],
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
    ["DEF-thigh.R", "CC_Base_R_Thigh"],
    ["DEF-thigh.R", "CC_Base_R_ThighTwist01"],
    ["DEF-thigh.R.001", "CC_Base_R_ThighTwist02"],
    ["DEF-knee_share.R", "CC_Base_R_KneeShareBone"],
    ["DEF-shin.R", "CC_Base_R_Calf"],
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
    ["DEF-upper_arm.R", "CC_Base_R_Upperarm"],
    ["DEF-upper_arm.R", "CC_Base_R_UpperarmTwist01"],
    ["DEF-upper_arm.R.001", "CC_Base_R_UpperarmTwist02"],
    ["DEF-elbow_share.R", "CC_Base_R_ElbowShareBone"],
    ["DEF-forearm.R", "CC_Base_R_Forearm"],
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


GAME_BASE_VERTEX_GROUP_RENAME = [
    # Spine, Neck & Head:
    ["DEF-spine", "pelvis"],
    ["DEF-spine.001", "spine_01"],
    ["DEF-spine.002", "spine_02"],
    ["DEF-spine.003", "spine_03"],
    ["DEF-spine.004", "neck_01"],
    ["DEF-spine.006", "head"],
    # Left Breast:
    ["DEF-breast_twist.L", "CC_Base_L_RibsTwist"],
    # Right Breast:
    ["DEF-breast_twist.R", "CC_Base_R_RibsTwist"],
    # Left Leg:
    ["DEF-thigh.L", "thigh_l"],
    ["DEF-thigh.L.001", "thigh_twist_01_l"],
    ["DEF-shin.L", "calf_l"],
    ["DEF-shin.L.001", "calf_twist_01_l"],
    ["DEF-foot.L", "foot_l"],
    ["DEF-toe.L", "ball_l"],
    # Left Arm:
    ["DEF-shoulder.L", "clavicle_l"],
    ["DEF-upper_arm.L", "upperarm_l"],
    ["DEF-upper_arm.L.001", "upperarm_twist_01_L"],
    ["DEF-forearm.L", "lowerarm_l"],
    ["DEF-forearm.L.001", "lowerarm_twist_01_l"],
    ["DEF-hand.L", "hand_l"],
    # Left Hand Fingers:
    ["DEF-thumb.01.L", "thumb_01_l"],
    ["DEF-f_index.01.L", "index_01_l"],
    ["DEF-f_middle.01.L", "middle_01_l"],
    ["DEF-f_ring.01.L", "ring_01_l"],
    ["DEF-f_pinky.01.L", "pinky_01_l"],
    ["DEF-thumb.02.L", "thumb_02_l"],
    ["DEF-f_index.02.L", "index_02_l"],
    ["DEF-f_middle.02.L", "middle_02_l"],
    ["DEF-f_ring.02.L", "ring_02_l"],
    ["DEF-f_pinky.02.L", "pinky_02_l"],
    ["DEF-thumb.03.L", "thumb_03_l"],
    ["DEF-f_index.03.L", "index_03_l"],
    ["DEF-f_middle.03.L", "middle_03_l"],
    ["DEF-f_ring.03.L", "ring_03_l"],
    ["DEF-f_pinky.03.L", "pinky_03_l"],
    # Right Leg:
    ["DEF-thigh.R", "thigh_r"],
    ["DEF-thigh.R.001", "thigh_twist_01_r"],
    ["DEF-shin.R", "calf_r"],
    ["DEF-shin.R.001", "calf_twist_01_r"],
    ["DEF-foot.R", "foot_r"],
    ["DEF-toe.R", "ball_r"],
    # Right Arm:
    ["DEF-shoulder.R", "clavicle_r"],
    ["DEF-upper_arm.R", "upperarm_r"],
    ["DEF-upper_arm.R.001", "upperarm_twist_01_r"],
    ["DEF-forearm.R", "lowerarm_r"],
    ["DEF-forearm.R.001", "lowerarm_twist_01_r"],
    ["DEF-hand.R", "hand_r"],
    # Right Hand Fingers:
    ["DEF-thumb.01.R", "thumb_01_r"],
    ["DEF-f_index.01.R", "index_01_r"],
    ["DEF-f_middle.01.R", "middle_01_r"],
    ["DEF-f_ring.01.R", "ring_01_r"],
    ["DEF-f_pinky.01.R", "pinky_01_r"],
    ["DEF-thumb.02.R", "thumb_02_r"],
    ["DEF-f_index.02.R", "index_02_r"],
    ["DEF-f_middle.02.R", "middle_02_r"],
    ["DEF-f_ring.02.R", "ring_02_r"],
    ["DEF-f_pinky.02.R", "pinky_02_r"],
    ["DEF-thumb.03.R", "thumb_03_r"],
    ["DEF-f_index.03.R", "index_03_r"],
    ["DEF-f_middle.03.R", "middle_03_r"],
    ["DEF-f_ring.03.R", "ring_03_r"],
    ["DEF-f_pinky.03.R", "pinky_03_r"],
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

    ["DEF-forearm.L", "DEF-elbow_share.L", "DEF-forearm.L", "LR", 29, 0.667, "DEF-upper_arm.L.001", 0.5],
    ["DEF-shin.L", "DEF-knee_share.L", "DEF-shin.L", "LR", 29, 0.667, "DEF-thigh.L.001", 0.5],
    #["DEF-toe.L", "DEF-toe_share.L", "DEF-toe.L", "LR", 29, 4.0, "DEF-foot.L", 0.5],

    ["CC_Base_L_BigToe1", "DEF-toe_big.L", "DEF-toe.L", "LR", 29],
    ["CC_Base_L_IndexToe1", "DEF-toe_index.L", "DEF-toe.L", "LR", 29],
    ["CC_Base_L_MidToe1", "DEF-toe_mid.L", "DEF-toe.L", "LR", 29],
    ["CC_Base_L_RingToe1", "DEF-toe_ring.L", "DEF-toe.L", "LR", 29],
    ["CC_Base_L_PinkyToe1", "DEF-toe_pinky.L", "DEF-toe.L", "LR", 29],

    ["DEF-forearm.R", "DEF-elbow_share.R", "DEF-forearm.R", "LR", 29, 0.667, "DEF-upper_arm.R.001", 0.5],
    ["DEF-shin.R", "DEF-knee_share.R", "DEF-shin.R", "LR", 29, 0.667, "DEF-thigh.R.001", 0.5],
    #["DEF-toe.R", "DEF-toe_share.R", "DEF-toe.R", "LR", 29, 4.0, "DEF-foot.R", 0.5],

    ["CC_Base_R_BigToe1", "DEF-toe_big.R", "DEF-toe.R", "LR", 29],
    ["CC_Base_R_IndexToe1", "DEF-toe_index.R", "DEF-toe.R", "LR", 29],
    ["CC_Base_R_MidToe1", "DEF-toe_mid.R", "DEF-toe.R", "LR", 29],
    ["CC_Base_R_RingToe1", "DEF-toe_ring.R", "DEF-toe.R", "LR", 29],
    ["CC_Base_R_PinkyToe1", "DEF-toe_pinky.R", "DEF-toe.R", "LR", 29],
]


# shape key drivers for facial blend shapes
SHAPE_KEY_DRIVERS = [
    ["Bfr", "A06_Eye_Look_Up_Left", ["SCRIPTED", "var*2.865 if var >= 0 else 0"], ["var", "TRANSFORMS", "MCH-eye.L", "ROT_X", "LOCAL_SPACE"]],
    ["Bfr", "A08_Eye_Look_Down_Left", ["SCRIPTED", "-var*2.865 if var < 0 else 0"], ["var", "TRANSFORMS", "MCH-eye.L", "ROT_X", "LOCAL_SPACE"]],
    ["Bfr", "A10_Eye_Look_Out_Left", ["SCRIPTED", "var*1.273 if var >=0 else 0"], ["var", "TRANSFORMS", "MCH-eye.L", "ROT_Z", "LOCAL_SPACE"]],
    ["Bfr", "A11_Eye_Look_In_Left", ["SCRIPTED", "-var*1.273 if var <0 else 0"], ["var", "TRANSFORMS", "MCH-eye.L", "ROT_Z", "LOCAL_SPACE"]],

    ["Bfr", "A07_Eye_Look_Up_Right", ["SCRIPTED", "var*2.865 if var >= 0 else 0"], ["var", "TRANSFORMS", "MCH-eye.R", "ROT_X", "LOCAL_SPACE"]],
    ["Bfr", "A09_Eye_Look_Down_Right", ["SCRIPTED", "-var*2.865 if var < 0 else 0"], ["var", "TRANSFORMS", "MCH-eye.R", "ROT_X", "LOCAL_SPACE"]],
    ["Bfr", "A12_Eye_Look_In_Right", ["SCRIPTED", "var*1.273 if var >=0 else 0"], ["var", "TRANSFORMS", "MCH-eye.R", "ROT_Z", "LOCAL_SPACE"]],
    ["Bfr", "A13_Eye_Look_Out_Right", ["SCRIPTED", "-var*1.273 if var <0 else 0"], ["var", "TRANSFORMS", "MCH-eye.R", "ROT_Z", "LOCAL_SPACE"]],
]


# roll is aligned directly from meta rig bone z_axis now
# we just need to apply a few corrections for better alignment i.e. hands, fingers
# [meta rig bone name, axis],
ROLL_CORRECTION = [
    # Left Hand Fingers, chains

    ["palm.01.L", "-Z"],
    ["palm.02.L", "-Z"],
    ["palm.03.L", "-Z"],
    ["palm.04.L", "-Z"],

    ["palm.01.R", "-Z"],
    ["palm.02.R", "-Z"],
    ["palm.03.R", "-Z"],
    ["palm.04.R", "-Z"],

    ["thumb.01.L", "-Z"],
    ["f_index.01.L", "-Z"],
    ["f_middle.01.L", "-Z"],
    ["f_ring.01.L", "-Z"],
    ["f_pinky.01.L", "-Z"],
    ["thumb.02.L", "-Z"],
    ["f_index.02.L", "-Z"],
    ["f_middle.02.L", "-Z"],
    ["f_ring.02.L", "-Z"],
    ["f_pinky.02.L", "-Z"],
    ["thumb.03.L", "-Z"],
    ["f_index.03.L", "-Z"],
    ["f_middle.03.L", "-Z"],
    ["f_ring.03.L", "-Z"],
    ["f_pinky.03.L", "-Z"],

    ["thumb.01.R", "-Z"],
    ["f_index.01.R", "-Z"],
    ["f_middle.01.R", "-Z"],
    ["f_ring.01.R", "-Z"],
    ["f_pinky.01.R", "-Z"],
    ["thumb.02.R", "-Z"],
    ["f_index.02.R", "-Z"],
    ["f_middle.02.R", "-Z"],
    ["f_ring.02.R", "-Z"],
    ["f_pinky.02.R", "-Z"],
    ["thumb.03.R", "-Z"],
    ["f_index.03.R", "-Z"],
    ["f_middle.03.R", "-Z"],
    ["f_ring.03.R", "-Z"],
    ["f_pinky.03.R", "-Z"],

    ["eye.L", "Z"],
    ["eye.R", "Z"],
]


# relative mappings: calculate the head/tail position of the first index,
#     defined by the second index
#     relative to a bounding box containing the proceding bones
#     may need to specify a minimum box dimension to avoid flat boxes.
#     after everything else has been placed, restore these relative mappings
#     to place these bones in approximately the right place
RELATIVE_MAPPINGS = [
    # heel mappings
    ["heel.02.L", "BOTH", "foot.L", "toe.L", "foot.R", "toe.R"],
    ["heel.02.R", "BOTH", "foot.L", "toe.L", "foot.R", "toe.R"],

    # approx face mappings
    ["jaw",             "HEAD", "eye.L", "eye.R", "spine.006"],
    ["chin",            "HEAD", "eye.L", "eye.R", "spine.006"],
    ["chin.001",        "BOTH", "eye.L", "eye.R", "spine.006"],
    #
    ["tongue",          "HEAD", "eye.L", "eye.R", "spine.006"],
    ["tongue.001",      "HEAD", "eye.L", "eye.R", "spine.006"],
    ["tongue.002",      "BOTH", "eye.L", "eye.R", "spine.006"],
    #
    ["temple.R",        "HEAD", "eye.L", "eye.R", "spine.006"],
    ["jaw.R",           "HEAD", "eye.L", "eye.R", "spine.006"],
    ["jaw.R.001",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["chin.R",          "HEAD", "eye.L", "eye.R", "spine.006"],
    ["cheek.B.R",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["cheek.B.R.001",   "HEAD", "eye.L", "eye.R", "spine.006"],
    ["brow.T.R",        "HEAD", "eye.L", "eye.R", "spine.006"],
    ["brow.T.R.001",    "HEAD", "eye.L", "eye.R", "spine.006"],
    ["brow.T.R.002",    "HEAD", "eye.L", "eye.R", "spine.006"],
    ["brow.T.R.003",    "BOTH", "eye.L", "eye.R", "spine.006"],
    #
    ["cheek.T.R",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["cheek.T.R.001",   "HEAD", "eye.L", "eye.R", "spine.006"],
    ["nose.R",          "HEAD", "eye.L", "eye.R", "spine.006"],
    ["nose.R.001",      "BOTH", "eye.L", "eye.R", "spine.006"],
    #
    ["temple.L",        "HEAD", "eye.L", "eye.R", "spine.006"],
    ["jaw.L",           "HEAD", "eye.L", "eye.R", "spine.006"],
    ["jaw.L.001",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["chin.L",          "HEAD", "eye.L", "eye.R", "spine.006"],
    ["cheek.B.L",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["cheek.B.L.001",   "HEAD", "eye.L", "eye.R", "spine.006"],
    ["brow.T.L",        "HEAD", "eye.L", "eye.R", "spine.006"],
    ["brow.T.L.001",    "HEAD", "eye.L", "eye.R", "spine.006"],
    ["brow.T.L.002",    "HEAD", "eye.L", "eye.R", "spine.006"],
    ["brow.T.L.003",    "BOTH", "eye.L", "eye.R", "spine.006"],
    #
    ["cheek.T.L",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["cheek.T.L.001",   "HEAD", "eye.L", "eye.R", "spine.006"],
    ["nose.L",          "HEAD", "eye.L", "eye.R", "spine.006"],
    ["nose.L.001",      "BOTH", "eye.L", "eye.R", "spine.006"],
    #
    ["nose",            "HEAD", "eye.L", "eye.R", "spine.006"],
    ["nose.001",        "HEAD", "eye.L", "eye.R", "spine.006"],
    ["nose.002",        "HEAD", "eye.L", "eye.R", "spine.006"],
    ["nose.003",        "HEAD", "eye.L", "eye.R", "spine.006"],
    ["nose.004",        "BOTH", "eye.L", "eye.R", "spine.006"],
    #
    ["lip.T.R",         "HEAD", "eye.L", "eye.R", "spine.006", "spine.005"],
    ["lip.T.R.001",     "BOTH", "eye.L", "eye.R", "spine.006", "spine.005"],
    #
    ["lip.T.L",         "HEAD", "eye.L", "eye.R", "spine.006", "spine.005"],
    ["lip.T.L.001",     "BOTH", "eye.L", "eye.R", "spine.006", "spine.005"],
    #
    ["lip.B.R",         "HEAD", "eye.L", "eye.R", "spine.006", "spine.005"],
    ["lip.B.R.001",     "BOTH", "eye.L", "eye.R", "spine.006", "spine.005"],
    #
    ["lip.B.L",         "HEAD", "eye.L", "eye.R", "spine.006", "spine.005"],
    ["lip.B.L.001",     "BOTH", "eye.L", "eye.R", "spine.006", "spine.005"],
    #
    ["brow.B.R",        "HEAD", "eye.L", "eye.R"],
    ["brow.B.R.001",    "HEAD", "eye.L", "eye.R"],
    ["brow.B.R.002",    "HEAD", "eye.L", "eye.R"],
    ["brow.B.R.003",    "BOTH", "eye.L", "eye.R"],
    #
    ["lid.T.R",         "HEAD", "eye.L", "eye.R"],
    ["lid.T.R.001",     "HEAD", "eye.L", "eye.R"],
    ["lid.T.R.002",     "HEAD", "eye.L", "eye.R"],
    ["lid.T.R.003",     "HEAD", "eye.L", "eye.R"],
    ["lid.B.R",         "HEAD", "eye.L", "eye.R"],
    ["lid.B.R.001",     "HEAD", "eye.L", "eye.R"],
    ["lid.B.R.002",     "HEAD", "eye.L", "eye.R"],
    ["lid.B.R.003",     "BOTH", "eye.L", "eye.R"],
    #
    ["brow.B.L",        "HEAD", "eye.L", "eye.R"],
    ["brow.B.L.001",    "HEAD", "eye.L", "eye.R"],
    ["brow.B.L.002",    "HEAD", "eye.L", "eye.R"],
    ["brow.B.L.003",    "BOTH", "eye.L", "eye.R"],
    #
    ["lid.T.L",         "HEAD", "eye.L", "eye.R"],
    ["lid.T.L.001",     "HEAD", "eye.L", "eye.R"],
    ["lid.T.L.002",     "HEAD", "eye.L", "eye.R"],
    ["lid.T.L.003",     "HEAD", "eye.L", "eye.R"],
    ["lid.B.L",         "HEAD", "eye.L", "eye.R"],
    ["lid.B.L.001",     "HEAD", "eye.L", "eye.R"],
    ["lid.B.L.002",     "HEAD", "eye.L", "eye.R"],
    ["lid.B.L.003",     "BOTH", "eye.L", "eye.R"],
    #
    ["forehead.R",      "BOTH", "eye.L", "eye.R", "spine.006"],
    ["forehead.R.001",  "BOTH", "eye.L", "eye.R", "spine.006"],
    ["forehead.R.002",  "BOTH", "eye.L", "eye.R", "spine.006"],
    ["forehead.L",      "BOTH", "eye.L", "eye.R", "spine.006"],
    ["forehead.L.001",  "BOTH", "eye.L", "eye.R", "spine.006"],
    ["forehead.L.002",  "BOTH", "eye.L", "eye.R", "spine.006"],
    #
    ["ear.R",           "HEAD", "eye.L", "eye.R", "spine.006"],
    ["ear.R.001",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["ear.R.002",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["ear.R.003",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["ear.R.004",       "BOTH", "eye.L", "eye.R", "spine.006"],
    #
    ["ear.L",           "HEAD", "eye.L", "eye.R", "spine.006"],
    ["ear.L.001",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["ear.L.002",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["ear.L.003",       "HEAD", "eye.L", "eye.R", "spine.006"],
    ["ear.L.004",       "BOTH", "eye.L", "eye.R", "spine.006"],
]


# face bones to remove from the Rigify rig for just a basic face rig.
# all prefix variations are also removed DEF-, ORG- MCH-
NON_BASIC_FACE_BONES = [
    "DEF-chin",
    "chin.002", "chin.001",
    "temple.R", "jaw.R", "jaw.R.001",
    "chin.R", "cheek.B.R", "cheek.B.R.001", "brow.T.R", "brow.T.R.001", "brow.T.R.002", "brow.T.R.003",
    "cheek.T.R", "cheek.T.R.001", "nose.R", "nose.R.001",
    "temple.L", "jaw.L", "jaw.L.001", "chin.L", "cheek.B.L", "cheek.B.L.001", "brow.T.L", "brow.T.L.001", "brow.T.L.002", "brow.T.L.003",
    "cheek.T.L", "cheek.T.L.001", "nose.L", "nose.L.001",
    "nose", "nose_master", "nose.001", "nose.002", "nose.003", "nose.004", "nose.005",
    "lips.R", "lips.L", "lip.T", "lip.B", "lip.T.R", "lip.T.R.001", "lip.T.L", "lip.T.L.001",
    "lip.B.R", "lip.B.R.001", "lip.B.L", "lip.B.L.001",
    "brow.B.R", "brow.B.R.001", "brow.B.R.002", "brow.B.R.003", "brow.B.R.004",
    "lid.T.R", "lid.T.R.001", "lid.T.R.002", "lid.T.R.003", "lid.B.R", "lid.B.R.001", "lid.B.R.002", "lid.B.R.003",
    "brow.B.L", "brow.B.L.001", "brow.B.L.002", "brow.B.L.003", "brow.B.L.004",
    "lid.T.L", "lid.T.L.001", "lid.T.L.002", "lid.T.L.003", "lid.B.L", "lid.B.L.001", "lid.B.L.002", "lid.B.L.003",
    "forehead.R", "forehead.R.001", "forehead.R.002",
    "forehead.L", "forehead.L.001", "forehead.L.002",
    "ear.R", "ear.R.001", "ear.R.002", "ear.R.003", "ear.R.004",
    "ear.L", "ear.L.001", "ear.L.002", "ear.L.003", "ear.L.004",
]


# [rigify bone name, rigify re-parent, unity bone name, instruction]
UNITY_EXPORT_RIG = [
    # Spine, Neck & Head:
    ["root", "", "CC_Base_Root", "-"],
    ["DEF-spine", "root", "CC_Base_Hip", "PLR"],
    ["DEF-pelvis", "DEF-spine", "CC_Base_Pelvis", "PLR"],
    ["DEF-spine.001", "DEF-spine", "CC_Base_Waist", "PLR"],
    ["DEF-spine.002", "DEF-spine.001", "CC_Base_Spine01", "PLR"],
    ["DEF-spine.003", "DEF-spine.002", "CC_Base_Spine02", "PLR"],
    ["DEF-spine.004", "DEF-spine.003", "CC_Base_NeckTwist01", "PLR"],
    ["DEF-spine.005", "DEF-spine.004", "CC_Base_NeckTwist02", "PLR"],
    ["DEF-spine.006", "DEF-spine.005", "CC_Base_Head", "PLR"],
    # Left Breast:
    ["DEF-breast_twist.L", "DEF-spine.003", "CC_Base_L_RibsTwist", "PLR"],
    ["DEF-breast.L", "DEF-breast_twist.L", "CC_Base_L_Breast", "PLR"],
    # Right Breast:
    ["DEF-breast_twist.R", "DEF-spine.003", "CC_Base_R_RibsTwist", "PLR"],
    ["DEF-breast.R", "DEF-breast_twist.R", "CC_Base_R_Breast", "PLR"],
    # Left Leg:
    ["DEF-thigh.L", "DEF-pelvis", "CC_Base_L_Thigh", "PLR"],
    ["DEF-thigh.L.001", "DEF-thigh.L", "CC_Base_L_ThighTwist", "PLR"],
    ["DEF-knee_share.L", "DEF-shin.L", "CC_Base_L_KneeShareBone", "PLR"],
    ["DEF-shin.L", "DEF-thigh.L.001", "CC_Base_L_Calf", "PLR"],
    ["DEF-shin.L.001", "DEF-shin.L", "CC_Base_L_CalfTwist", "PLR"],
    ["DEF-foot.L", "DEF-shin.L.001", "CC_Base_L_Foot", "PLR"],
    ["DEF-toe.L", "DEF-foot.L", "CC_Base_L_ToeBase", "PLR"],
    # Left Foot:
    ["DEF-toe_big.L", "DEF-toe.L", "CC_Base_L_BigToe1", "PLR"],
    ["DEF-toe_index.L", "DEF-toe.L", "CC_Base_L_IndexToe1", "PLR"],
    ["DEF-toe_mid.L", "DEF-toe.L", "CC_Base_L_MidToe1", "PLR"],
    ["DEF-toe_ring.L", "DEF-toe.L", "CC_Base_L_RingToe1", "PLR"],
    ["DEF-toe_pinky.L", "DEF-toe.L", "CC_Base_L_PinkyToe1", "PLR"],
    # Left Arm:
    ["DEF-shoulder.L", "DEF-spine.003", "CC_Base_L_Clavicle", "PLR"],
    ["DEF-upper_arm.L", "DEF-shoulder.L", "CC_Base_L_Upperarm", "PLRC"],
    ["DEF-upper_arm.L.001", "DEF-upper_arm.L", "CC_Base_L_UpperarmTwist", "PLR"],
    ["DEF-elbow_share.L", "DEF-forearm.L", "CC_Base_L_ElbowShareBone", "PLR"],
    ["DEF-forearm.L", "DEF-upper_arm.L.001", "CC_Base_L_Forearm", "PLR"],
    ["DEF-forearm.L.001", "DEF-forearm.L", "CC_Base_L_ForearmTwist", "PLR"],
    ["DEF-hand.L", "DEF-forearm.L.001", "CC_Base_L_Hand", "PLR"],
    # Left Hand Fingers:
    ["DEF-thumb.01.L", "DEF-hand.L", "CC_Base_L_Thumb1", "PLR"],
    ["DEF-f_index.01.L", "DEF-hand.L", "CC_Base_L_Index1", "PLR"],
    ["DEF-f_middle.01.L", "DEF-hand.L", "CC_Base_L_Mid1", "PLR"],
    ["DEF-f_ring.01.L", "DEF-hand.L", "CC_Base_L_Ring1", "PLR"],
    ["DEF-f_pinky.01.L", "DEF-hand.L", "CC_Base_L_Pinky1", "PLR"],
    ["DEF-thumb.02.L", "DEF-thumb.01.L", "CC_Base_L_Thumb2", "PLR"],
    ["DEF-f_index.02.L", "DEF-f_index.01.L", "CC_Base_L_Index2", "PLR"],
    ["DEF-f_middle.02.L", "DEF-f_middle.01.L", "CC_Base_L_Mid2", "PLR"],
    ["DEF-f_ring.02.L", "DEF-f_ring.01.L", "CC_Base_L_Ring2", "PLR"],
    ["DEF-f_pinky.02.L", "DEF-f_pinky.01.L", "CC_Base_L_Pinky2", "PLR"],
    ["DEF-thumb.03.L", "DEF-thumb.02.L", "CC_Base_L_Thumb3", "PLR"],
    ["DEF-f_index.03.L", "DEF-f_index.02.L", "CC_Base_L_Index3", "PLR"],
    ["DEF-f_middle.03.L", "DEF-f_middle.02.L", "CC_Base_L_Mid3", "PLR"],
    ["DEF-f_ring.03.L", "DEF-f_ring.02.L", "CC_Base_L_Ring3", "PLR"],
    ["DEF-f_pinky.03.L", "DEF-f_pinky.02.L", "CC_Base_L_Pinky3", "PLR"],
    # Right Leg:
    ["DEF-thigh.R", "DEF-pelvis", "CC_Base_R_Thigh", "PLR"],
    ["DEF-thigh.R.001", "DEF-thigh.R", "CC_Base_R_ThighTwist", "PLR"],
    ["DEF-knee_share.R", "DEF-shin.R", "CC_Base_R_KneeShareBone", "PLR"],
    ["DEF-shin.R", "DEF-thigh.R.001", "CC_Base_R_Calf", "PLR"],
    ["DEF-shin.R.001", "DEF-shin.R", "CC_Base_R_CalfTwist", "PLR"],
    ["DEF-foot.R", "DEF-shin.R.001", "CC_Base_R_Foot", "PLR"],
    ["DEF-toe.R", "DEF-foot.R", "CC_Base_R_ToeBase", "PLR"],
    # Right Foot:
    ["DEF-toe_big.R", "DEF-toe.R", "CC_Base_R_BigToe1", "PLR"],
    ["DEF-toe_index.R", "DEF-toe.R", "CC_Base_R_IndexToe1", "PLR"],
    ["DEF-toe_mid.R", "DEF-toe.R", "CC_Base_R_MidToe1", "PLR"],
    ["DEF-toe_ring.R", "DEF-toe.R", "CC_Base_R_RingToe1", "PLR"],
    ["DEF-toe_pinky.R", "DEF-toe.R", "CC_Base_R_PinkyToe1", "PLR"],
    # Right Arm:
    ["DEF-shoulder.R", "DEF-spine.003", "CC_Base_R_Clavicle", "PLR"],
    ["DEF-upper_arm.R", "DEF-shoulder.R", "CC_Base_R_Upperarm", "PLRC"],
    ["DEF-upper_arm.R.001", "DEF-upper_arm.R", "CC_Base_R_UpperarmTwist", "PLR"],
    ["DEF-elbow_share.R", "DEF-forearm.R", "CC_Base_R_ElbowShareBone", "PLR"],
    ["DEF-forearm.R", "DEF-upper_arm.R.001", "CC_Base_R_Forearm", "PLR"],
    ["DEF-forearm.R.001", "DEF-forearm.R", "CC_Base_R_ForearmTwist", "PLR"],
    ["DEF-hand.R", "DEF-forearm.R.001", "CC_Base_R_Hand", "PLR"],
    # Right Hand Fingers:
    ["DEF-thumb.01.R", "DEF-hand.R", "CC_Base_R_Thumb1", "PLR"],
    ["DEF-f_index.01.R", "DEF-hand.R", "CC_Base_R_Index1", "PLR"],
    ["DEF-f_middle.01.R", "DEF-hand.R", "CC_Base_R_Mid1", "PLR"],
    ["DEF-f_ring.01.R", "DEF-hand.R", "CC_Base_R_Ring1", "PLR"],
    ["DEF-f_pinky.01.R", "DEF-hand.R", "CC_Base_R_Pinky1", "PLR"],
    ["DEF-thumb.02.R", "DEF-thumb.01.R", "CC_Base_R_Thumb2", "PLR"],
    ["DEF-f_index.02.R", "DEF-f_index.01.R", "CC_Base_R_Index2", "PLR"],
    ["DEF-f_middle.02.R", "DEF-f_middle.01.R", "CC_Base_R_Mid2", "PLR"],
    ["DEF-f_ring.02.R", "DEF-f_ring.01.R", "CC_Base_R_Ring2", "PLR"],
    ["DEF-f_pinky.02.R", "DEF-f_pinky.01.R", "CC_Base_R_Pinky2", "PLR"],
    ["DEF-thumb.03.R", "DEF-thumb.02.R", "CC_Base_R_Thumb3", "PLR"],
    ["DEF-f_index.03.R", "DEF-f_index.02.R", "CC_Base_R_Index3", "PLR"],
    ["DEF-f_middle.03.R", "DEF-f_middle.02.R", "CC_Base_R_Mid3", "PLR"],
    ["DEF-f_ring.03.R", "DEF-f_ring.02.R", "CC_Base_R_Ring3", "PLR"],
    ["DEF-f_pinky.03.R", "DEF-f_pinky.02.R", "CC_Base_R_Pinky3", "PLR"],
    # Tongue:
    ["DEF-tongue", "DEF-jaw", "CC_Base_Tongue03", "LRP"],
    ["DEF-tongue.001", "DEF-tongue", "CC_Base_Tongue02", "PLR"],
    ["DEF-tongue.002", "DEF-tongue.001", "CC_Base_Tongue01", "PLR"],
    # Teeth:
    ["DEF-teeth.T", "DEF-spine.006", "CC_Base_Teeth01", "PLR"],
    ["DEF-teeth.B", "DEF-jaw", "CC_Base_Teeth02", "PLR"],
    # Eyes:
    ["DEF-eye.R", "DEF-spine.006", "CC_Base_R_Eye", "PLR"],
    ["DEF-eye.L", "DEF-spine.006", "CC_Base_L_Eye", "PLR"],
    # Jaw:
    ["DEF-jaw", "DEF-spine.006", "CC_Base_JawRoot", "PLRT", "jaw_master"],
]


# Rigify control bones to resize
CONTROL_MODIFY = [
    ["hand_ik.R", [-1, 1.5, 1.5], [0, 0, 0.0125], [0, 0, 0]],
    ["hand_ik.L", [1, 1.5, 1.5], [0, 0, 0.0125], [0, 0, 0]],

    ["foot_ik.R", [-1.25, 1.5, 1], [0, 0.05, 0], [0, 0, 0]],
    ["foot_ik.L", [1.25, 1.5, 1], [0, 0.05, 0], [0, 0, 0]],

    ["head", [1.25, 1, 1.25], [0, 0.02, 0], [0, 0, 0]],
    ["jaw", [1.25, 1.25, 1.25], [0, 0, 0], [0, 0, 0]],
    ["jaw_master", [1.25, 1.25, 1.25], [0, 0, 0], [0, 0, 0]],

    ["shoulder.R", [-1.5, 1.5, 1.5], [0, 0, 0], [0, 0, 0]],
    ["shoulder.L", [1.5, 1.5, 1.5], [0, 0, 0], [0, 0, 0]],
    ["hips", [1.35, 1.35, 1.35], [0, 0, -0.015], [0, 0, 0]],
    ["chest", [1.1, 1.5, 1.1], [0, 0.025, -0.025], [0, 0, 0]],
    ["torso", [1.2, 1.2, 1.2], [0, 0, 0], [0, 0, 0]],
    ["neck", [1.5, 1, 1.5], [0, 0, 0], [0, 0, 0]],
    ["tongue", [1.5, 1.5, 1.5], [0, 0.015, -0.01], [0, 0, 0]],
    ["tongue_master", [1.5, 1.5, 1.5], [0, 0.015, -0.01], [0, 0, 0]],

    ["foot_heel_ik.L", [1.5, 1.5, 1.5], [0, 0.015, 0], [0, 0, 0]],
    ["foot_heel_ik.R", [-1.5, 1.5, 1.5], [0, 0.015, 0], [0, 0, 0]],
]


RIGIFY_PARAMS = [
    ["upper_arm.R", "rotation_axis", "x"],
    ["upper_arm.L", "rotation_axis", "x"],
    ["thigh.R", "rotation_axis", "x"],
    ["thigh.L", "rotation_axis", "x"],

    ["f_index.01.L", "primary_rotation_axis", "X"],
    ["f_middle.01.L", "primary_rotation_axis", "X"],
    ["f_ring.01.L", "primary_rotation_axis", "X"],
    ["f_pinky.01.L", "primary_rotation_axis", "X"],

    ["f_index.01.R", "primary_rotation_axis", "X"],
    ["f_middle.01.R", "primary_rotation_axis", "X"],
    ["f_ring.01.R", "primary_rotation_axis", "X"],
    ["f_pinky.01.R", "primary_rotation_axis", "X"],
]


UV_THRESHOLD = 0.001


# G3Plus UV coordinates of the face rig bones, to reverse calculate the spacial coordinates
UV_TARGETS_G3PLUS = [
    # connected mapping: map (head)->(tail/head)->(tail/head->(tail/head)...
    ["nose", "CONNECTED",           [0.500, 0.650], [0.500, 0.597], [0.500, 0.573], [0.500, 0.550], [0.500, 0.531], [0.500, 0.516]],
    ["jaw", "CONNECTED",            [0.500, 0.339], [0.500, 0.395], [0.500, 0.432], [0.500, 0.453]],
    ["cheek.T.R", "CONNECTED",      [0.360, 0.633], [0.413, 0.593], [0.453, 0.606], [0.446, 0.559], [0.500, 0.573]],
    ["temple.R", "CONNECTED",       [0.250, 0.645], [0.289, 0.492], [0.360, 0.435], [0.429, 0.408], [0.443, 0.486], [0.363, 0.533],
                                    [0.360, 0.633], [0.371, 0.660], [0.414, 0.682], [0.458, 0.678], [0.500, 0.650]],
    ["ear.R", "CONNECTED",          [0.246, 0.566], [0.228, 0.640], [0.196, 0.623], [0.207, 0.554], [0.235, 0.534], [0.246, 0.566]],

    ["lid.T.R", "CONNECTED",        [0.398, 0.638], [0.417, 0.644], [0.431, 0.644], [0.444, 0.641],
                                    [0.450, 0.635], [0.437, 0.632], [0.422, 0.631], [0.407, 0.633], [0.398, 0.638]],
    ["brow.B.R", "CONNECTED",       [0.388, 0.646], [0.413, 0.661], [0.435, 0.662], [0.454, 0.653], [0.460, 0.638]],

    ["lip.T.R", "CONNECTED",        [0.500, 0.512], [0.468, 0.508], [0.443, 0.486]],
    ["lip.B.R", "CONNECTED",        [0.500, 0.463], [0.478, 0.467], [0.443, 0.486]],

    # disconnected mapping: map head and tail pairs
    ["forehead.R", "DISCONNECTED",  [ [0.461, 0.740], [0.458, 0.678] ],
                                    [ [0.410, 0.741], [0.414, 0.682] ],
                                    [ [0.358, 0.725], [0.371, 0.660] ] ],
    # set the top of the 'head' bone
    #["spine.006", "TAIL",           [0.688, 0.953]],
]


# G3 UV coordinates of the face rig bones, to reverse calculate the spacial coordinates
UV_TARGETS_G3 = [
    # connected mapping: map (head)->(tail/head)->(tail/head->(tail/head)...
    ["nose", "CONNECTED",           [0.4999, 0.3614], [0.5000, 0.3080], [0.5000, 0.2858], [0.5000, 0.2668], [0.5000, 0.2507], [0.5000, 0.2366]],
    ["jaw", "CONNECTED",            [0.5000, 0.0347], [0.5000, 0.1105], [0.5000, 0.1488], [0.5000, 0.1688]],
    ["cheek.T.R", "CONNECTED",      [0.3467, 0.3457], [0.4058, 0.3062], [0.4519, 0.3188], [0.4493, 0.2728], [0.5000, 0.2858]],
    ["temple.R", "CONNECTED",       [0.2028, 0.4031], [0.2418, 0.1913], [0.3349, 0.1369], [0.4211, 0.1202], [0.4378, 0.2023], [0.3414, 0.2428],
                                    [0.3467, 0.3457], [0.3625, 0.3725], [0.4110, 0.3929], [0.4557, 0.3907], [0.4999, 0.3614]],
    ["ear.R", "CONNECTED",          [0.1467, 0.3356], [0.1032, 0.4324], [0.1441, 0.4936], [0.0794, 0.3163], [0.1237, 0.2927], [0.1467, 0.3356]],

    ["lid.T.R", "CONNECTED",        [0.3884, 0.3452], [0.4095, 0.3517], [0.4262, 0.3504], [0.4423, 0.3488],
                                    [0.4474, 0.3435], [0.4343, 0.3375], [0.4169, 0.3360], [0.3987, 0.3383], [0.3884, 0.3452]],
    ["brow.B.R", "CONNECTED",       [0.3789, 0.3567], [0.4082, 0.3716], [0.4314, 0.3740], [0.4522, 0.3651], [0.4578, 0.3479]],

    ["lip.T.R", "CONNECTED",        [0.5000, 0.2316], [0.4642, 0.2281], [0.4378, 0.2023]],
    ["lip.B.R", "CONNECTED",        [0.5000, 0.1787], [0.4744, 0.1818], [0.4378, 0.2023]],

    # disconnected mapping: map head and tail pairs
    ["forehead.R", "DISCONNECTED",  [ [0.4600, 0.4592], [0.4557, 0.3907] ],
                                    [ [0.4110, 0.4565], [0.4110, 0.3929] ],
                                    [ [0.3584, 0.4407], [0.3625, 0.3725] ] ],
    # set the top of the 'head' bone
    #["spine.006", "TAIL",           [0.688, 0.953]],
]


# body object types (with facial blend shapes)
BODY_TYPES = ["BODY", "TEARLINE", "OCCLUSION"]


# deformation bone vertex group name prefixes to clear and initialise with random test weights
# (by checking for these test weights we can tell if the parent with automatic weights function succeeded or not)
FACE_DEF_BONE_PREFIX = [
    "DEF-forehead.", "DEF-brow.", "DEF-lid.", "DEF-cheek.",
    "DEF-temple.", "DEF-jaw.", "DEF-lip.", "DEF-ear.",
    "DEF-nose", "DEF-chin", # don't use DEF-Jaw as this is based on the original CC3 weights.
]


# deformation bones in the Rigify rig to turn off when re-parenting the face objects to the Rigify face rig.
FACE_DEF_BONE_PREPASS = [
    "DEF-eye.L", "DEF-eye.R", "DEF-teeth.T", "DEF-teeth.B", "DEF-jaw",
]


# ShapeKey names to look for to test if a mesh is a face object. e.g. brows / beards / tearline etc...
FACE_TEST_SHAPEKEYS = [
    "Eye_Wide_L", "Eye_Wide_R", "Eye_Blink_L", "Eye_Blink_R",
    "Nose_Scrunch", "Nose_Flank_Raise_L", "Nose_Flank_Raise_R",
    "Mouth_Smile_L", "Mouth_Smile_R", "Mouth_Open",
    "Brow_Raise_L", "Brow_Raise_R",
    "Cheek_Blow_L", "Cheek_Blow_R",
]


# bone names to test for to see if armature or action is for a CC3:G3/G3Plus/ActorCore rig.
CC3_BONE_NAMES = [
    "CC_Base_BoneRoot", "CC_Base_Hip", "CC_Base_FacialBone"
]

ACTOR_CORE_BONE_NAMES = [
    "RL_BoneRoot", "CC_Base_Hip", "CC_Base_FacialBone"
]


# bone names to test for to see if armature or action is for a iClone:G3/G3Plus/ActorCore rig.
# (iClone does not export bones with the "CC_Base_" prefix)
ICLONE_BONE_NAMES = [
    "BoneRoot", "Hip", "FacialBone"
]


# bone names to test for to see if armature or action is for a CC3:GameBase rig.
GAME_BASE_BONE_NAMES = [
    "pelvis", "spine_01", "CC_Base_FacialBone"
]


# bone names to test for to see if armature or action is for a mixamo rig
MIXAMO_BONE_NAMES = [
    "mixamorig:Hips", "mixamorig:Spine", "mixamorig:Head"
]


# bone names to test for to see if armature or action is for a rigify rig
RIGIFY_BONE_NAMES = [
    "MCH-torso.parent", "ORG-spine", "spine_fk"
]

# the minimum size of the relative mapping bounding box
# 5cm
BOX_PADDING = 0.01


ALLOWED_RIG_BONES = [
    "CC_Base_BoneRoot", "CC_Base_FacialBone", "RL_BoneRoot", "BoneRoot", "mixamorig:Hips",
]


# list of the Rigify control bones that animations are retargeted to
RETARGET_RIGIFY_BONES = [
    "root", "hips", "torso", "spine_fk", "spine_fk.001", "spine_fk.002", "chest", "spine_fk.003",
    "neck", "tweak_spine", "tweak_spine.001", "tweak_spine.002", "tweak_spine.003", "tweak_spine.004", "tweak_spine.005",
    "head", "neck",
    "breast.L", "breast.R",
    "thigh_fk.L", "shin_fk.L", "foot_fk.L", "toe_fk.L", "toe.L",
    "shoulder.L", "upper_arm_fk.L", "forearm_fk.L", "hand_fk.L",
    "thumb.01.L", "f_index.01.L", "f_middle.01.L", "f_ring.01.L", "f_pinky.01.L",
    "thumb.02.L", "f_index.02.L", "f_middle.02.L", "f_ring.02.L", "f_pinky.02.L",
    "thumb.03.L", "f_index.03.L", "f_middle.03.L", "f_ring.03.L", "f_pinky.03.L",
    "thigh_fk.R", "shin_fk.R", "foot_fk.R", "toe_fk.R", "toe.R",
    "shoulder.R", "upper_arm_fk.R", "forearm_fk.R", "hand_fk.R",
    "thumb.01.R", "f_index.01.R", "f_middle.01.R", "f_ring.01.R", "f_pinky.01.R",
    "thumb.02.R", "f_index.02.R", "f_middle.02.R", "f_ring.02.R", "f_pinky.02.R",
    "thumb.03.R", "f_index.03.R", "f_middle.03.R", "f_ring.03.R", "f_pinky.03.R",
    "eye.L", "eye.R", "eyes",
    "jaw_master", "teeth.T", "teeth.B",
    "tongue_master", "tongue", "tongue.001", "tongue.002", "tweak_tongue", "tweak_tongue.001", "tweak_tongue.002",
    "hand_ik.L", "hand_ik.R", "foot_ik.L", "foot_ik.R", "toe_ik.L", "toe_ik.R",
]


RETARGET_G3 = [
    #   flags (flags are processed in order of left to right)
    #
    #       "L" - constrain location (retarget rig to rigify rig)
    #       "R" - constrain rotation (retarget rig to rigify rig)
    #       "N" - no source -> retarget constraints (to avoid duplicate constraints)
    #       "C" - copy rigify bone positions
    #       "P" - parent retarget correction: for when source bone and org bone
    #             are not the in the same orientation
    #
    #   flags with parameters (are processed left to right and parameters are consecutive)
    #
    #       "+", copy_bone - this org bone needs be added copied from copy_bone
    #       "I", influence - multiply the influence of the source -> org copy location/rotation
    #       "T", next_bone - parent correction & align with target: like "P" but maintain alignment
    #                        between the org bone and next_bone.
    #                        for when the source and ORG bones should be in alignment but aren't
    #                        because of strange bone orientations (Mixamo!) in the source rig.
    #       "D", root_bone - maintain distance from root_bone
    #       "A", bone_1, bone_2 - copy average location and rotation from bone_1 and bone_2
    #
    # [origin_bone, orign_bone_parent,          source_bone(regex match), rigify_target_bone, flags, *params]
    #
    # hips
    ["ORG-hip", "",                             "(CC_Base_|)Hip", "", "+PLR", "rigify:ORG-spine"],
    ["ORG-spine", "ORG-hip",                    "(CC_Base_|)Pelvis", "torso", "LR"],
    ["ORG-spine", "ORG-hip",                    "(CC_Base_|)Pelvis", "spine_fk", "NLR"],
    ["ORG-pelvis", "ORG-hip",                   "(CC_Base_|)Pelvis", "hips", "PLR"],
    # spine
    ["ORG-spine.001", "ORG-spine",              "(CC_Base_|)Waist", "spine_fk.001", "LR"],
    ["ORG-spine.002", "ORG-spine.001",          "(CC_Base_|)Spine01", "spine_fk.002", "LR"],
    ["ORG-spine.002", "ORG-spine.001",          "(CC_Base_|)Spine01", "chest", "NLR"],
    ["ORG-spine.003", "ORG-spine.002",          "(CC_Base_|)Spine02", "spine_fk.003", "LR"],
    ["ORG-spine.004", "ORG-spine.003",          "(CC_Base_|)NeckTwist01", "neck", "LR"],
    ["ORG-spine.005", "ORG-spine.004",          "(CC_Base_|)NeckTwist02", "tweak_spine.005", "L"],
    ["ORG-spine.006", "ORG-spine.005",          "(CC_Base_|)Head", "head", "LR"],
    # torso
    ["ORG-breast.L", "ORG-spine.003",           "(CC_Base_|)L_RibsTwist", "breast.L", "LR"],
    ["ORG-breast.R", "ORG-spine.003",           "(CC_Base_|)R_RibsTwist", "breast.R", "LR"],
    # left leg
    ["ORG-thigh.L", "ORG-pelvis",               "(CC_Base_|)L_Thigh", "thigh_fk.L", "LR"],
    ["ORG-shin.L", "ORG-thigh.L",               "(CC_Base_|)L_Calf", "shin_fk.L", "LR"],
    ["ORG-foot.L", "ORG-shin.L",                "(CC_Base_|)L_Foot$", "foot_fk.L", "PLR"],
    ["ORG-toe.L", "ORG-foot.L",                 "(CC_Base_|)L_ToeBase$", "toe_fk.L", "LR"], #post 3.1
    ["ORG-toe.L", "ORG-foot.L",                 "(CC_Base_|)L_ToeBase$", "toe.L", "LR"], #pre 3.1
    # left arm
    ["ORG-shoulder.L", "ORG-spine.003",         "(CC_Base_|)L_Clavicle", "shoulder.L", "LR"],
    ["ORG-upper_arm.L", "ORG-shoulder.L",       "(CC_Base_|)L_Upperarm", "upper_arm_fk.L", "LR"],
    ["ORG-forearm.L", "ORG-upper_arm.L",        "(CC_Base_|)L_Forearm", "forearm_fk.L", "LR"],
    ["ORG-hand.L", "ORG-forearm.L",             "(CC_Base_|)L_Hand", "hand_fk.L", "LR"],
    # left fingers
    ["ORG-thumb.01.L", "ORG-hand.L",            "(CC_Base_|)L_Thumb1", "thumb.01.L", "LR"],
    ["ORG-f_index.01.L", "ORG-hand.L",          "(CC_Base_|)L_Index1", "f_index.01.L", "LR"],
    ["ORG-f_middle.01.L", "ORG-hand.L",         "(CC_Base_|)L_Mid1", "f_middle.01.L", "LR"],
    ["ORG-f_ring.01.L", "ORG-hand.L",           "(CC_Base_|)L_Ring1", "f_ring.01.L", "LR"],
    ["ORG-f_pinky.01.L", "ORG-hand.L",          "(CC_Base_|)L_Pinky1", "f_pinky.01.L", "LR"],
    ["ORG-thumb.02.L", "ORG-thumb.01.L",        "(CC_Base_|)L_Thumb2", "thumb.02.L", "LR"],
    ["ORG-f_index.02.L", "ORG-f_index.01.L",    "(CC_Base_|)L_Index2", "f_index.02.L", "LR"],
    ["ORG-f_middle.02.L", "ORG-f_middle.01.L",  "(CC_Base_|)L_Mid2", "f_middle.02.L", "LR"],
    ["ORG-f_ring.02.L", "ORG-f_ring.01.L",      "(CC_Base_|)L_Ring2", "f_ring.02.L", "LR"],
    ["ORG-f_pinky.02.L", "ORG-f_pinky.01.L",    "(CC_Base_|)L_Pinky2", "f_pinky.02.L", "LR"],
    ["ORG-thumb.03.L", "ORG-thumb.02.L",        "(CC_Base_|)L_Thumb3", "thumb.03.L", "LR"],
    ["ORG-f_index.03.L", "ORG-f_index.02.L",    "(CC_Base_|)L_Index3", "f_index.03.L", "LR"],
    ["ORG-f_middle.03.L", "ORG-f_middle.02.L",  "(CC_Base_|)L_Mid3", "f_middle.03.L", "LR"],
    ["ORG-f_ring.03.L", "ORG-f_ring.02.L",      "(CC_Base_|)L_Ring3", "f_ring.03.L", "LR"],
    ["ORG-f_pinky.03.L", "ORG-f_pinky.02.L",    "(CC_Base_|)L_Pinky3", "f_pinky.03.L", "LR"],
    # right leg
    ["ORG-thigh.R", "ORG-pelvis",               "(CC_Base_|)R_Thigh", "thigh_fk.R", "LR"],
    ["ORG-shin.R", "ORG-thigh.R",               "(CC_Base_|)R_Calf", "shin_fk.R", "LR"],
    ["ORG-foot.R", "ORG-shin.R",                "(CC_Base_|)R_Foot$", "foot_fk.R", "PLR"],
    ["ORG-toe.R", "ORG-foot.R",                 "(CC_Base_|)R_ToeBase$", "toe_fk.R", "LR"], #post 3.1
    ["ORG-toe.R", "ORG-foot.R",                 "(CC_Base_|)R_ToeBase$", "toe.R", "LR"], #pre 3.1
    # right arm
    ["ORG-shoulder.R", "ORG-spine.003",         "(CC_Base_|)R_Clavicle", "shoulder.R", "LR"],
    ["ORG-upper_arm.R", "ORG-shoulder.R",       "(CC_Base_|)R_Upperarm", "upper_arm_fk.R", "LR"],
    ["ORG-forearm.R", "ORG-upper_arm.R",        "(CC_Base_|)R_Forearm", "forearm_fk.R", "LR"],
    ["ORG-hand.R", "ORG-forearm.R",             "(CC_Base_|)R_Hand", "hand_fk.R", "LR"],
    # right fingers
    ["ORG-thumb.01.R", "ORG-hand.R",            "(CC_Base_|)R_Thumb1", "thumb.01.R", "LR"],
    ["ORG-f_index.01.R", "ORG-hand.R",          "(CC_Base_|)R_Index1", "f_index.01.R", "LR"],
    ["ORG-f_middle.01.R", "ORG-hand.R",         "(CC_Base_|)R_Mid1", "f_middle.01.R", "LR"],
    ["ORG-f_ring.01.R", "ORG-hand.R",           "(CC_Base_|)R_Ring1", "f_ring.01.R", "LR"],
    ["ORG-f_pinky.01.R", "ORG-hand.R",          "(CC_Base_|)R_Pinky1", "f_pinky.01.R", "LR"],
    ["ORG-thumb.02.R", "ORG-thumb.01.R",        "(CC_Base_|)R_Thumb2", "thumb.02.R", "LR"],
    ["ORG-f_index.02.R", "ORG-f_index.01.R",    "(CC_Base_|)R_Index2", "f_index.02.R", "LR"],
    ["ORG-f_middle.02.R", "ORG-f_middle.01.R",  "(CC_Base_|)R_Mid2", "f_middle.02.R", "LR"],
    ["ORG-f_ring.02.R", "ORG-f_ring.01.R",      "(CC_Base_|)R_Ring2", "f_ring.02.R", "LR"],
    ["ORG-f_pinky.02.R", "ORG-f_pinky.01.R",    "(CC_Base_|)R_Pinky2", "f_pinky.02.R", "LR"],
    ["ORG-thumb.03.R", "ORG-thumb.02.R",        "(CC_Base_|)R_Thumb3", "thumb.03.R", "LR"],
    ["ORG-f_index.03.R", "ORG-f_index.02.R",    "(CC_Base_|)R_Index3", "f_index.03.R", "LR"],
    ["ORG-f_middle.03.R", "ORG-f_middle.02.R",  "(CC_Base_|)R_Mid3", "f_middle.03.R", "LR"],
    ["ORG-f_ring.03.R", "ORG-f_ring.02.R",      "(CC_Base_|)R_Ring3", "f_ring.03.R", "LR"],
    ["ORG-f_pinky.03.R", "ORG-f_pinky.02.R",    "(CC_Base_|)R_Pinky3", "f_pinky.03.R", "LR"],
    #face
    ["ORG-face", "ORG-spine.006",               "(CC_Base_|)FacialBone", "", "PLR"],
    # eyes
    ["ORG-eye.L", "ORG-face",                   "(CC_Base_|)L_Eye", "eye.L", "PLRD", "ORG-eye.L"],
    ["ORG-eye.R", "ORG-face",                   "(CC_Base_|)R_Eye", "eye.R", "PLRD", "ORG-eye.R"],
    ["ORG-eyes", "ORG-face",                    "", "eyes", "+LRA", "rigify:eyes", "eye.R", "eye.L"],
    # jaw
    ["ORG-jaw_root", "ORG-face",                "(CC_Base_|)JawRoot", "jaw_master", "+PLR", "rigify:MCH-jaw_master"],
    ["ORG-jaw", "ORG-jaw_root",                 "", "", ""],
    # teeth
    ["ORG-teeth.T", "ORG-face",                 "(CC_Base_|)Teeth01", "teeth.T", "PLR"],
    ["ORG-teeth.B", "ORG-jaw",                  "(CC_Base_|)Teeth02", "teeth.B", "PLR"],
    # tongue (full face)
    ["ORG-tongue", "ORG-jaw",                   "(CC_Base_|)Tongue03", "tongue_master", "PLR"],
    ["ORG-tongue.001", "ORG-jaw",               "(CC_Base_|)Tongue02", "tongue.001", "PL"],
    ["ORG-tongue.002", "ORG-jaw",               "(CC_Base_|)Tongue01", "tongue.002", "PL"],
    # IK bones
    ["ORG-hand.L", "ORG-forearm.L",             "(CC_Base_|)L_Hand", "hand_ik.L", "NLR"],
    ["ORG-hand.R", "ORG-forearm.R",             "(CC_Base_|)R_Hand", "hand_ik.R", "NLR"],
    ["ORG-foot.L", "ORG-shin.L",                "(CC_Base_|)L_Foot", "foot_ik.L", "NLR"],
    ["ORG-foot.R", "ORG-shin.R",                "(CC_Base_|)R_Foot", "foot_ik.R", "NLR"],
    ["ORG-toe.L", "ORG-foot.L",                 "(CC_Base_|)L_ToeBase$", "toe_ik.L", "NLR"],
    ["ORG-toe.R", "ORG-foot.R",                 "(CC_Base_|)R_ToeBase$", "toe_ik.R", "NLR"],
]


# Note: this is retarget FROM game base actions TO the rigify rig.
RETARGET_GAME_BASE = [
    #   flags (flags are processed in order of left to right)
    #
    #       "L" - constrain location (retarget rig to rigify rig)
    #       "R" - constrain rotation (retarget rig to rigify rig)
    #       "N" - no source -> retarget constraints (to avoid duplicate constraints)
    #       "C" - copy rigify bone positions
    #       "P" - parent retarget correction: for when source bone and org bone
    #             are not the in the same orientation
    #
    #   flags with parameters (are processed left to right and parameters are consecutive)
    #
    #       "+", copy_bone - this org bone needs be added copied from copy_bone
    #       "I", influence - multiply the influence of the source -> org copy location/rotation
    #       "T", next_bone - parent correction & align with target: like "P" but maintain alignment with
    #                        org bone, for when the source and ORG bones should be in alignment but aren't
    #                        because of strange bone orientations (Mixamo!) in the source rig.
    #       "D", root_bone - maintain distance from root_bone
    #       "A", bone_1, bone_2 - copy average location and rotation from bone_1 and bone_2
    #
    # [origin_bone, orign_bone_parent,          source_bone(regex match), rigify_target_bone, flags, *params]
    #
    # hips
    ["ORG-hip", "",                             "pelvis", "", "+PLR", "rigify:ORG-spine"],
    ["ORG-spine", "ORG-hip",                    "pelvis", "torso", "NPLR"],
    ["ORG-spine", "ORG-hip",                    "pelvis", "spine_fk", "NPLR"],
    ["ORG-pelvis", "ORG-hip",                   "pelvis", "hips", "NPLR"],
    # spine
    ["ORG-spine.001", "ORG-spine",              "spine_01", "spine_fk.001", "LR"],
    ["ORG-spine.002", "ORG-spine.001",          "spine_02", "spine_fk.002", "LR"],
    ["ORG-spine.002", "ORG-spine.001",          "spine_02", "chest", "NLR"],
    ["ORG-spine.003", "ORG-spine.002",          "spine_03", "spine_fk.003", "LR"],
    ["ORG-spine.004", "ORG-spine.003",          "neck_01", "neck", "LR"],
    ["ORG-spine.006", "ORG-spine.004",          "head", "head", "LR"],
    # torso
    ["ORG-breast.L", "ORG-spine.003",           "(CC_Base_|)L_RibsTwist", "breast.L", "LR"],
    ["ORG-breast.R", "ORG-spine.003",           "(CC_Base_|)R_RibsTwist", "breast.R", "LR"],
    # left leg
    ["ORG-thigh.L", "ORG-pelvis",               "thigh_l", "thigh_fk.L", "LR"],
    ["ORG-shin.L", "ORG-thigh.L",               "calf_l", "shin_fk.L", "LR"],
    ["ORG-foot.L", "ORG-shin.L",                "foot_l", "foot_fk.L", "PLR"],
    ["ORG-toe.L", "ORG-foot.L",                 "ball_l", "toe_fk.L", "LR"], #post 3.1
    ["ORG-toe.L", "ORG-foot.L",                 "ball_l", "toe.L", "LR"], #pre 3.1
    # left arm
    ["ORG-shoulder.L", "ORG-spine.003",         "clavicle_l", "shoulder.L", "LR"],
    ["ORG-upper_arm.L", "ORG-shoulder.L",       "upperarm_l", "upper_arm_fk.L", "LR"],
    ["ORG-forearm.L", "ORG-upper_arm.L",        "lowerarm_l", "forearm_fk.L", "LR"],
    ["ORG-hand.L", "ORG-forearm.L",             "hand_l", "hand_fk.L", "LR"],
    # left fingers
    ["ORG-thumb.01.L", "ORG-hand.L",            "thumb_01_l", "thumb.01.L", "LR"],
    ["ORG-f_index.01.L", "ORG-hand.L",          "index_01_l", "f_index.01.L", "LR"],
    ["ORG-f_middle.01.L", "ORG-hand.L",         "middle_01_l", "f_middle.01.L", "LR"],
    ["ORG-f_ring.01.L", "ORG-hand.L",           "ring_01_l", "f_ring.01.L", "LR"],
    ["ORG-f_pinky.01.L", "ORG-hand.L",          "pinky_01_l", "f_pinky.01.L", "LR"],
    ["ORG-thumb.02.L", "ORG-thumb.01.L",        "thumb_02_l", "thumb.02.L", "LR"],
    ["ORG-f_index.02.L", "ORG-f_index.01.L",    "index_02_l", "f_index.02.L", "LR"],
    ["ORG-f_middle.02.L", "ORG-f_middle.01.L",  "middle_02_l", "f_middle.02.L", "LR"],
    ["ORG-f_ring.02.L", "ORG-f_ring.01.L",      "ring_02_l", "f_ring.02.L", "LR"],
    ["ORG-f_pinky.02.L", "ORG-f_pinky.01.L",    "pinky_02_l", "f_pinky.02.L", "LR"],
    ["ORG-thumb.03.L", "ORG-thumb.02.L",        "thumb_03_l", "thumb.03.L", "LR"],
    ["ORG-f_index.03.L", "ORG-f_index.02.L",    "index_03_l", "f_index.03.L", "LR"],
    ["ORG-f_middle.03.L", "ORG-f_middle.02.L",  "middle_03_l", "f_middle.03.L", "LR"],
    ["ORG-f_ring.03.L", "ORG-f_ring.02.L",      "ring_03_l", "f_ring.03.L", "LR"],
    ["ORG-f_pinky.03.L", "ORG-f_pinky.02.L",    "pinky_03_l", "f_pinky.03.L", "LR"],
    # right leg
    ["ORG-thigh.R", "ORG-pelvis",               "thigh_r", "thigh_fk.R", "LR"],
    ["ORG-shin.R", "ORG-thigh.R",               "calf_r", "shin_fk.R", "LR"],
    ["ORG-foot.R", "ORG-shin.R",                "foot_r", "foot_fk.R", "PLR"],
    ["ORG-toe.R", "ORG-foot.R",                 "ball_r", "toe_fk.R", "LR"], #post 3.1
    ["ORG-toe.R", "ORG-foot.R",                 "ball_r", "toe.R", "LR"], #pre 3.1
    # right arm
    ["ORG-shoulder.R", "ORG-spine.003",         "clavicle_r", "shoulder.R", "LR"],
    ["ORG-upper_arm.R", "ORG-shoulder.R",       "upperarm_r", "upper_arm_fk.R", "LR"],
    ["ORG-forearm.R", "ORG-upper_arm.R",        "lowerarm_r", "forearm_fk.R", "LR"],
    ["ORG-hand.R", "ORG-forearm.R",             "hand_r", "hand_fk.R", "LR"],
    # right fingers
    ["ORG-thumb.01.R", "ORG-hand.R",            "thumb_01_r", "thumb.01.R", "LR"],
    ["ORG-f_index.01.R", "ORG-hand.R",          "index_01_r", "f_index.01.R", "LR"],
    ["ORG-f_middle.01.R", "ORG-hand.R",         "middle_01_r", "f_middle.01.R", "LR"],
    ["ORG-f_ring.01.R", "ORG-hand.R",           "ring_01_r", "f_ring.01.R", "LR"],
    ["ORG-f_pinky.01.R", "ORG-hand.R",          "pinky_01_r", "f_pinky.01.R", "LR"],
    ["ORG-thumb.02.R", "ORG-thumb.01.R",        "thumb_02_r", "thumb.02.R", "LR"],
    ["ORG-f_index.02.R", "ORG-f_index.01.R",    "index_02_r", "f_index.02.R", "LR"],
    ["ORG-f_middle.02.R", "ORG-f_middle.01.R",  "middle_02_r", "f_middle.02.R", "LR"],
    ["ORG-f_ring.02.R", "ORG-f_ring.01.R",      "ring_02_r", "f_ring.02.R", "LR"],
    ["ORG-f_pinky.02.R", "ORG-f_pinky.01.R",    "pinky_02_r", "f_pinky.02.R", "LR"],
    ["ORG-thumb.03.R", "ORG-thumb.02.R",        "thumb_03_r", "thumb.03.R", "LR"],
    ["ORG-f_index.03.R", "ORG-f_index.02.R",    "index_03_r", "f_index.03.R", "LR"],
    ["ORG-f_middle.03.R", "ORG-f_middle.02.R",  "middle_03_r", "f_middle.03.R", "LR"],
    ["ORG-f_ring.03.R", "ORG-f_ring.02.R",      "ring_03_r", "f_ring.03.R", "LR"],
    ["ORG-f_pinky.03.R", "ORG-f_pinky.02.R",    "pinky_03_r", "f_pinky.03.R", "LR"],
    #face
    ["ORG-face", "ORG-spine.006",               "(CC_Base_|)FacialBone", "", "PLR"],
    # eyes
    ["ORG-eye.L", "ORG-face",                   "(CC_Base_|)L_Eye", "eye.L", "PLRD", "ORG-eye.L"],
    ["ORG-eye.R", "ORG-face",                   "(CC_Base_|)R_Eye", "eye.R", "PLRD", "ORG-eye.R"],
    ["ORG-eyes", "ORG-face",                    "", "eyes", "+LRA", "rigify:eyes", "eye.R", "eye.L"],
    # jaw
    ["ORG-jaw_root", "ORG-face",                "(CC_Base_|)JawRoot", "jaw_master", "+PLR", "rigify:MCH-jaw_master"],
    ["ORG-jaw", "ORG-jaw_root",                 "", "", ""],
    # teeth
    ["ORG-teeth.T", "ORG-face",                 "(CC_Base_|)Teeth01", "teeth.T", "PLR"],
    ["ORG-teeth.B", "ORG-jaw",                  "(CC_Base_|)Teeth02", "teeth.B", "PLR"],
    # tongue (full face)
    ["ORG-tongue", "ORG-jaw",                   "(CC_Base_|)Tongue03", "tongue_master", "PLR"],
    ["ORG-tongue.001", "ORG-jaw",               "(CC_Base_|)Tongue02", "tongue.001", "PL"],
    ["ORG-tongue.002", "ORG-jaw",               "(CC_Base_|)Tongue01", "tongue.002", "PL"],
    # IK bones
    ["ORG-hand.L", "ORG-forearm.L",             "hand_l", "hand_ik.L", "NLR"],
    ["ORG-hand.R", "ORG-forearm.R",             "hand_r", "hand_ik.R", "NLR"],
    ["ORG-foot.L", "ORG-shin.L",                "foot_l", "foot_ik.L", "NLR"],
    ["ORG-foot.R", "ORG-shin.R",                "foot_r", "foot_ik.R", "NLR"],
    ["ORG-toe.L", "ORG-foot.L",                 "ball_l", "toe_ik.L", "NLR"],
    ["ORG-toe.R", "ORG-foot.R",                 "ball_r", "toe_ik.R", "NLR"],
]


RETARGET_MIXAMO = [
    #   flags (flags are processed in order of left to right)
    #
    #       "L" - constrain location (retarget rig to rigify rig)
    #       "R" - constrain rotation (retarget rig to rigify rig)
    #       "N" - no source -> retarget constraints (to avoid duplicate constraints)
    #       "C" - copy rigify bone positions
    #       "P" - parent retarget correction: for when source bone and org bone
    #             are not the in the same orientation
    #
    #   flags with parameters (are processed left to right and parameters are consecutive)
    #
    #       "+", copy_bone - this org bone needs be added copied from copy_bone
    #       "I", influence - multiply the influence of the source -> org copy location/rotation
    #       "T", next_bone - parent correction & align with target: like "P" but maintain alignment
    #                        between the org bone and next_bone.
    #                        for when the source and ORG bones should be in alignment but aren't
    #                        because of strange bone orientations (Mixamo!) in the source rig.
    #       "D", root_bone - maintain distance from root_bone
    #       "A", bone_1, bone_2 - copy average location and rotation from bone_1 and bone_2
    #
    # [origin_bone, orign_bone_parent,          source_bone(regex match), rigify_target_bone, flags, *params]
    #
    # mixamorig:Hips = ORG-spine + ORG-spine.001
    ["ORG-hip", "",                             "mixamorig:Hips", "", "+PLR", "rigify:ORG-spine"],
    ["ORG-spine", "ORG-hip",                    "", "torso", "LR"],
    ["ORG-spine", "ORG-hip",                    "", "spine_fk", "LR"],
    ["ORG-pelvis", "ORG-spine",                 "", "hips", "LR"],
    ["ORG-spine.001", "ORG-spine",              "", "spine_fk.001", "LR"],
    # mixamorig:Spine = ORG-spine.002
    # reduce the influence of this bone, as it causes too much twisting in the abdomen
    ["ORG-spine.002", "ORG-spine.001",          "mixamorig:Spine$", "spine_fk.002", "PLRI", 0.25],
    # mixamorig:Spine1 + mixamorig:Spine2 = ORG-spine.003
    ["ORG-spine.003", "ORG-spine.002",          "mixamorig:Spine1", "spine_fk.003", "PLR"],
    ["ORG-spine.003", "ORG-spine.002",          "", "chest", "LR"],
    # mixamorig:Neck = ORG-spine.004 + ORG.spine.005
    ["ORG-spine.004", "ORG-spine.003",          "mixamorig:Neck", "neck", "PLR"],
    # head
    ["ORG-spine.006", "ORG-spine.004",          "mixamorig:Head$", "head", "PLR"],
    # left leg
    ["ORG-thigh.L", "ORG-pelvis",               "mixamorig:LeftUpLeg", "thigh_fk.L", "TLR", "mixamorig:LeftLeg"],
    ["ORG-shin.L", "ORG-thigh.L",               "mixamorig:LeftLeg", "shin_fk.L", "TLR", "mixamorig:LeftFoot"],
    ["ORG-foot.L", "ORG-shin.L",                "mixamorig:LeftFoot", "foot_fk.L", "PLR"],
    ["ORG-toe.L", "ORG-foot.L",                 "mixamorig:LeftToeBase", "toe_fk.L", "TLR", "mixamorig:LeftToe_End"], #post 3.1
    ["ORG-toe.L", "ORG-foot.L",                 "mixamorig:LeftToeBase", "toe.L", "TLR", "mixamorig:LeftToe_End"], #pre 3.1
    # left arm
    ["ORG-shoulder.L", "ORG-spine.003",         "mixamorig:LeftShoulder", "shoulder.L", "PLR"],
    ["ORG-upper_arm.L", "ORG-shoulder.L",       "mixamorig:LeftArm", "upper_arm_fk.L", "TLR", "mixamorig:LeftForeArm"],
    ["ORG-forearm.L", "ORG-upper_arm.L",        "mixamorig:LeftForeArm", "forearm_fk.L", "TLR", "mixamorig:LeftHand$"],
    ["ORG-hand.L", "ORG-forearm.L",             "mixamorig:LeftHand$", "hand_fk.L", "TLR", "mixamorig:LeftHandMiddle1"],
    # left fingers
    ["ORG-thumb.01.L", "ORG-hand.L",            "mixamorig:LeftHandThumb1", "thumb.01.L", "TLR", "mixamorig:LeftHandThumb2"],
    ["ORG-f_index.01.L", "ORG-hand.L",          "mixamorig:LeftHandIndex1", "f_index.01.L", "TLR", "mixamorig:LeftHandIndex2"],
    ["ORG-f_middle.01.L", "ORG-hand.L",         "mixamorig:LeftHandMiddle1", "f_middle.01.L", "TLR", "mixamorig:LeftHandMiddle2"],
    ["ORG-f_ring.01.L", "ORG-hand.L",           "mixamorig:LeftHandRing1", "f_ring.01.L", "TLR", "mixamorig:LeftHandRing2"],
    ["ORG-f_pinky.01.L", "ORG-hand.L",          "mixamorig:LeftHandPinky1", "f_pinky.01.L", "TLR", "mixamorig:LeftHandPinky2"],
    ["ORG-thumb.02.L", "ORG-thumb.01.L",        "mixamorig:LeftHandThumb2", "thumb.02.L", "TR", "mixamorig:LeftHandThumb3"],
    ["ORG-f_index.02.L", "ORG-f_index.01.L",    "mixamorig:LeftHandIndex2", "f_index.02.L", "TR", "mixamorig:LeftHandIndex3"],
    ["ORG-f_middle.02.L", "ORG-f_middle.01.L",  "mixamorig:LeftHandMiddle2", "f_middle.02.L", "TR", "mixamorig:LeftHandMiddle3"],
    ["ORG-f_ring.02.L", "ORG-f_ring.01.L",      "mixamorig:LeftHandRing2", "f_ring.02.L", "TR", "mixamorig:LeftHandRing3"],
    ["ORG-f_pinky.02.L", "ORG-f_pinky.01.L",    "mixamorig:LeftHandPinky2", "f_pinky.02.L", "TR", "mixamorig:LeftHandPinky3"],
    ["ORG-thumb.03.L", "ORG-thumb.02.L",        "mixamorig:LeftHandThumb3", "thumb.03.L", "TR", "mixamorig:LeftHandThumb4"],
    ["ORG-f_index.03.L", "ORG-f_index.02.L",    "mixamorig:LeftHandIndex3", "f_index.03.L", "TR", "mixamorig:LeftHandIndex4"],
    ["ORG-f_middle.03.L", "ORG-f_middle.02.L",  "mixamorig:LeftHandMiddle3", "f_middle.03.L", "TR", "mixamorig:LeftHandMiddle4"],
    ["ORG-f_ring.03.L", "ORG-f_ring.02.L",      "mixamorig:LeftHandRing3", "f_ring.03.L", "TR", "mixamorig:LeftHandRing4"],
    ["ORG-f_pinky.03.L", "ORG-f_pinky.02.L",    "mixamorig:LeftHandPinky3", "f_pinky.03.L", "TR", "mixamorig:LeftHandPinky4"],
    # right leg
    ["ORG-thigh.R", "ORG-pelvis",               "mixamorig:RightUpLeg", "thigh_fk.R", "TLR", "mixamorig:RightLeg"],
    ["ORG-shin.R", "ORG-thigh.R",               "mixamorig:RightLeg", "shin_fk.R", "TLR", "mixamorig:RightFoot"],
    ["ORG-foot.R", "ORG-shin.R",                "mixamorig:RightFoot", "foot_fk.R", "PLR"],
    ["ORG-toe.R", "ORG-foot.R",                 "mixamorig:RightToeBase", "toe_fk.R", "TLR", "mixamorig:RightToe_End"], #post 3.1
    ["ORG-toe.R", "ORG-foot.R",                 "mixamorig:RightToeBase", "toe.R", "TLR", "mixamorig:RightToe_End"], #pre 3.1
    # right arm
    ["ORG-shoulder.R", "ORG-spine.003",         "mixamorig:RightShoulder", "shoulder.R", "PLR"],
    ["ORG-upper_arm.R", "ORG-shoulder.R",       "mixamorig:RightArm", "upper_arm_fk.R", "TR", "mixamorig:RightForeArm"],
    ["ORG-forearm.R", "ORG-upper_arm.R",        "mixamorig:RightForeArm", "forearm_fk.R", "TR", "mixamorig:RightHand$"],
    ["ORG-hand.R", "ORG-forearm.R",             "mixamorig:RightHand$", "hand_fk.R", "TR", "mixamorig:RightHandMiddle1"],
    # right fingers
    ["ORG-thumb.01.R", "ORG-hand.R",            "mixamorig:RightHandThumb1", "thumb.01.R", "TLR", "mixamorig:RightHandThumb2"],
    ["ORG-f_index.01.R", "ORG-hand.R",          "mixamorig:RightHandIndex1", "f_index.01.R", "TLR", "mixamorig:RightHandIndex2"],
    ["ORG-f_middle.01.R", "ORG-hand.R",         "mixamorig:RightHandMiddle1", "f_middle.01.R", "TLR", "mixamorig:RightHandMiddle2"],
    ["ORG-f_ring.01.R", "ORG-hand.R",           "mixamorig:RightHandRing1", "f_ring.01.R", "TLR", "mixamorig:RightHandRing2"],
    ["ORG-f_pinky.01.R", "ORG-hand.R",          "mixamorig:RightHandPinky1", "f_pinky.01.R", "TLR", "mixamorig:RightHandPinky2"],
    ["ORG-thumb.02.R", "ORG-thumb.01.R",        "mixamorig:RightHandThumb2", "thumb.02.R", "TR", "mixamorig:RightHandThumb3"],
    ["ORG-f_index.02.R", "ORG-f_index.01.R",    "mixamorig:RightHandIndex2", "f_index.02.R", "TR", "mixamorig:RightHandIndex3"],
    ["ORG-f_middle.02.R", "ORG-f_middle.01.R",  "mixamorig:RightHandMiddle2", "f_middle.02.R", "TR", "mixamorig:RightHandMiddle3"],
    ["ORG-f_ring.02.R", "ORG-f_ring.01.R",      "mixamorig:RightHandRing2", "f_ring.02.R", "TR", "mixamorig:RightHandRing3"],
    ["ORG-f_pinky.02.R", "ORG-f_pinky.01.R",    "mixamorig:RightHandPinky2", "f_pinky.02.R", "TR", "mixamorig:RightHandPinky3"],
    ["ORG-thumb.03.R", "ORG-thumb.02.R",        "mixamorig:RightHandThumb3", "thumb.03.R", "TR", "mixamorig:RightHandThumb4"],
    ["ORG-f_index.03.R", "ORG-f_index.02.R",    "mixamorig:RightHandIndex3", "f_index.03.R", "TR", "mixamorig:RightHandIndex4"],
    ["ORG-f_middle.03.R", "ORG-f_middle.02.R",  "mixamorig:RightHandMiddle3", "f_middle.03.R", "TR", "mixamorig:RightHandMiddle4"],
    ["ORG-f_ring.03.R", "ORG-f_ring.02.R",      "mixamorig:RightHandRing3", "f_ring.03.R", "TR", "mixamorig:RightHandRing4"],
    ["ORG-f_pinky.03.R", "ORG-f_pinky.02.R",    "mixamorig:RightHandPinky3", "f_pinky.03.R", "TR", "mixamorig:RightHandPinky4"],
    #face
    ["ORG-face", "ORG-spine.006",               "", "", ""],
    # eyes
    ["ORG-eye.L", "ORG-face",                   "mixamorig:LeftEye", "eye.L", "PRD", "ORG-eye.L"],
    ["ORG-eye.R", "ORG-face",                   "mixamorig:RightEye", "eye.R", "PRD", "ORG-eye.R"],
    ["ORG-eyes", "ORG-face",                    "", "eyes", "+LRA", "rigify:eyes", "eye.R", "eye.L"],
    # IK bones
    ["ORG-hand.L", "ORG-forearm.L",             "mixamorig:LeftHand$", "hand_ik.L", "NTLR", "mixamorig:LeftHandMiddle1"],
    ["ORG-hand.R", "ORG-forearm.R",             "mixamorig:RightHand$", "hand_ik.R", "NTLR", "mixamorig:RightHandMiddle1"],
    ["ORG-foot.L", "ORG-shin.L",                "mixamorig:LeftFoot", "foot_ik.L", "NPLR", "mixamorig:LeftToeBase"],
    ["ORG-foot.R", "ORG-shin.R",                "mixamorig:RightFoot", "foot_ik.R", "NPLR", "mixamorig:RightToeBase"],
    ["ORG-toe.L", "ORG-foot.L",                 "mixamorig:LeftToeBase", "toe_ik.L", "NTLR", "mixamorig:LeftToe_End"],
    ["ORG-toe.R", "ORG-foot.R",                 "mixamorig:RightToeBase", "toe_ik.R", "NTLR", "mixamorig:RightToe_End"],
]


RETARGET_CORRECTIONS = {
    "Heel_Angle": {
        "bone": [(0, 0, 0), (0, 0, 0.1), "retarget_heel_correction_angle", "rotation_euler", 0],
        "constraints": [
            ["ORG-foot.L", "ROT_ADD_LOCAL", "-X"],
            ["ORG-foot.R", "ROT_ADD_LOCAL", "-X"],
        ],
    },

    "Arm_Angle": {
        "bone": [(0, 0, 0), (0, 0, 0.1), "retarget_arm_correction_angle", "rotation_euler", 2],
        "constraints": [
            ["ORG-upper_arm.L", "ROT_ADD_LOCAL", "Z"],
            ["ORG-upper_arm.R", "ROT_ADD_LOCAL", "-Z"],
        ],
    },

    "Leg_Angle": {
        "bone": [(0, 0, 0), (0, 0, 0.1), "retarget_leg_correction_angle", "rotation_euler", 2],
        "constraints": [
            ["ORG-thigh.L", "ROT_ADD_LOCAL", "Z"],
            ["ORG-thigh.R", "ROT_ADD_LOCAL", "-Z"],
        ],
    },

    "Z_Correction": {
        "bone": [(0, 0, 0), (0, 0, 0.1), "retarget_z_correction_height", "location", 1],
        "constraints": [
            ["ORG-hip", "LOC_OFF_LOCAL", "Y"],
        ],
    },
}