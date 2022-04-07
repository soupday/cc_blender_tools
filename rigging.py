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

from random import random
import bpy
import mathutils
import addon_utils
import time
from . import utils
from . import geom
from . import meshutils
from . import properties
from . import modifiers
from . import bones
from . import characters

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

# relative mappings: calculate the head/tail position of the first index,
#     defined by the second index
#     relative to a bounding box containing the proceding bones
#     may need to specify a minimum box dimension to avoid flat boxes.
# after everything else has been placed, restore the relative mappings
RELATIVE_MAPPINGS = [
    ["heel.02.L", "BOTH", "foot.L", "toe.L"],
    ["heel.02.R", "BOTH", "foot.R", "toe.R"],
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

EXPORT_RIG = [
    # Spine, Neck & Head:
    ["DEF-pelvis", "DEF-spine", "P"],
    ["DEF-spine", "root", "P"],
    ["DEF-spine.001", "DEF-spine", "P"],
    ["DEF-spine.002", "DEF-spine.001", "P"],
    ["DEF-spine.003", "DEF-spine.002", "P"],
    ["DEF-spine.004", "DEF-spine.003", "P"],
    ["DEF-spine.005", "DEF-spine.004", "P"],
    ["DEF-spine.006", "DEF-spine.005", "P"],
    # Left Breast:
    ["DEF-breast_twist.L", "DEF-spine.003", "P"],
    ["DEF-breast.L", "DEF-breast_twist.L", "P"],
    # Right Breast:
    ["DEF-breast_twist.R", "DEF-spine.003", "P"],
    ["DEF-breast.R", "DEF-breast_twist.R", "P"],
    # Left Leg:
    ["DEF-thigh.L", "DEF-pelvis", "P"],
    ["DEF-thigh.L.001", "DEF-thigh.L", "P"],
    ["DEF-knee_share.L", "DEF-shin.L", "P"],
    ["DEF-shin.L", "DEF-thigh.L.001", "P"],
    ["DEF-shin.L.001", "DEF-shin.L", "P"],
    ["DEF-foot.L", "DEF-shin.L.001", "P"],
    ["DEF-toe.L", "DEF-foot.L", "P"],
    # Left Foot:
    ["DEF-toe_big.L", "DEF-toe.L", "P"],
    ["DEF-toe_index.L", "DEF-toe.L", "P"],
    ["DEF-toe_mid.L", "DEF-toe.L", "P"],
    ["DEF-toe_ring.L", "DEF-toe.L", "P"],
    ["DEF-toe_pinky.L", "DEF-toe.L", "P"],
    # Left Arm:
    ["DEF-shoulder.L", "DEF-spine.003", "P"],
    ["DEF-upper_arm.L", "DEF-shoulder.L", "P"],
    ["DEF-upper_arm.L.001", "DEF-upper_arm.L", "P"],
    ["DEF-elbow_share.L", "DEF-forearm.L", "P"],
    ["DEF-forearm.L", "DEF-shoulder.L", "P"],
    ["DEF-forearm.L.001", "DEF-forearm.L", "P"],
    ["DEF-hand.L", "DEF-forearm.L.001", "P"],
    # Left Hand Fingers:
    ["DEF-thumb.01.L", "DEF-hand.L", "P"],
    ["DEF-f_index.01.L", "DEF-hand.L", "P"],
    ["DEF-f_middle.01.L", "DEF-hand.L", "P"],
    ["DEF-f_ring.01.L", "DEF-hand.L", "P"],
    ["DEF-f_pinky.01.L", "DEF-hand.L", "P"],
    ["DEF-thumb.02.L", "DEF-thumb.01.L", "P"],
    ["DEF-f_index.02.L", "DEF-f_index.01.L", "P"],
    ["DEF-f_middle.02.L", "DEF-f_middle.01.L", "P"],
    ["DEF-f_ring.02.L", "DEF-f_ring.01.L", "P"],
    ["DEF-f_pinky.02.L", "DEF-f_pinky.01.L", "P"],
    ["DEF-thumb.03.L", "DEF-thumb.02.L", "P"],
    ["DEF-f_index.03.L", "DEF-f_index.02.L", "P"],
    ["DEF-f_middle.03.L", "DEF-f_middle.02.L", "P"],
    ["DEF-f_ring.03.L", "DEF-f_ring.02.L", "P"],
    ["DEF-f_pinky.03.L", "DEF-f_pinky.02.L", "P"],
    # Right Leg:
    ["DEF-thigh.R", "DEF-pelvis", "P"],
    ["DEF-thigh.R.001", "DEF-thigh.R", "P"],
    ["DEF-knee_share.R", "DEF-shin.R", "P"],
    ["DEF-shin.R", "DEF-thigh.R.001", "P"],
    ["DEF-shin.R.001", "DEF-shin.R", "P"],
    ["DEF-foot.R", "DEF-shin.R.001", "P"],
    ["DEF-toe.R", "DEF-foot.R", "P"],
    # Right Foot:
    ["DEF-toe_big.R", "DEF-toe.R", "P"],
    ["DEF-toe_index.R", "DEF-toe.R", "P"],
    ["DEF-toe_mid.R", "DEF-toe.R", "P"],
    ["DEF-toe_ring.R", "DEF-toe.R", "P"],
    ["DEF-toe_pinky.R", "DEF-toe.R", "P"],
    # Right Arm:
    ["DEF-shoulder.R", "DEF-spine.003", "P"],
    ["DEF-upper_arm.R", "DEF-shoulder.R", "P"],
    ["DEF-upper_arm.R.001", "DEF-upper_arm.R", "P"],
    ["DEF-elbow_share.R", "DEF-forearm.R", "P"],
    ["DEF-forearm.R", "DEF-shoulder.R", "P"],
    ["DEF-forearm.R.001", "DEF-forearm.R", "P"],
    ["DEF-hand.R", "DEF-forearm.R.001", "P"],
    # Right Hand Fingers:
    ["DEF-thumb.01.R", "DEF-hand.R", "P"],
    ["DEF-f_index.01.R", "DEF-hand.R", "P"],
    ["DEF-f_middle.01.R", "DEF-hand.R", "P"],
    ["DEF-f_ring.01.R", "DEF-hand.R", "P"],
    ["DEF-f_pinky.01.R", "DEF-hand.R", "P"],
    ["DEF-thumb.02.R", "DEF-thumb.01.R", "P"],
    ["DEF-f_index.02.R", "DEF-f_index.01.R", "P"],
    ["DEF-f_middle.02.R", "DEF-f_middle.01.R", "P"],
    ["DEF-f_ring.02.R", "DEF-f_ring.01.R", "P"],
    ["DEF-f_pinky.02.R", "DEF-f_pinky.01.R", "P"],
    ["DEF-thumb.03.R", "DEF-thumb.02.R", "P"],
    ["DEF-f_index.03.R", "DEF-f_index.02.R", "P"],
    ["DEF-f_middle.03.R", "DEF-f_middle.02.R", "P"],
    ["DEF-f_ring.03.R", "DEF-f_ring.02.R", "P"],
    ["DEF-f_pinky.03.R", "DEF-f_pinky.02.R", "P"],
    # Tongue:
    ["DEF-tongue", "DEF-jaw", "P"],
    ["DEF-tongue.001", "DEF-tongue", "P"],
    ["DEF-tongue.002", "DEF-tongue.001", "P"],
    # Teeth:
    ["DEF-teeth.T", "DEF-spine.006", "P"],
    ["DEF-teeth.B", "DEF-jaw", "P"],
    # Eyes:
    ["DEF-eye.R", "DEF-spine.006", "P"],
    ["DEF-eye.L", "DEF-spine.006", "P"],
    # Jaw:
    ["DEF-jaw", "DEF-spine.006", "P"],
]

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

RIGIFY_PARAMS = [
    ["upper_arm.R", "x"],
    ["upper_arm.L", "x"],
    ["thigh.R", "x"],
    ["thigh.L", "x"],
]

UV_THRESHOLD = 0.001

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

BODY_TYPES = ["BODY", "TEARLINE", "OCCLUSION"]

FACE_DEF_BONE_PREFIX = [
    "DEF-forehead.", "DEF-brow.", "DEF-lid.", "DEF-cheek.",
    "DEF-temple.", "DEF-jaw.", "DEF-lip.", "DEF-ear.",
    "DEF-nose", "DEF-chin", # don't use DEF-Jaw as this is based on the original CC3 weights.
]

FACE_DEF_BONE_PREPASS = [
    "DEF-eye.L", "DEF-eye.R", "DEF-teeth.T", "DEF-teeth.B", "DEF-jaw",
]

FACE_TEST_SHAPEKEYS = [
    "Eye_Wide_L", "Eye_Wide_R", "Eye_Blink_L", "Eye_Blink_R",
    "Nose_Scrunch", "Nose_Flank_Raise_L", "Nose_Flank_Raise_R",
    "Mouth_Smile_L", "Mouth_Smile_R", "Mouth_Open",
    "Brow_Raise_L", "Brow_Raise_R",
    "Cheek_Blow_L", "Cheek_Blow_R",
]

# the minimum size of the relative mapping bounding box
BOX_PADDING = 0.25

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
        print("BOX:")
        print("Min:", self.box_min)
        print("Max:", self.box_max)


def prune_meta_rig(meta_rig):
    """Removes some meta rig bones that have no corresponding match in the CC3 rig.
       (And are safe to remove)
    """

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

    for def_copy in ADD_DEF_BONES:
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

        if src_bone_name == "-": # means to reparent an existing deformation bone
            reparented_bone = bones.reparent_edit_bone(rigify_rig, dst_bone_name, dst_bone_parent_name)
            if reparented_bone:
                bones.set_edit_bone_flags(reparented_bone, relation_flags, deform)
                bones.set_bone_layer(rigify_rig, dst_bone_name, layer)

        elif src_bone_name == "+MCHEyeParent":
            mch_bone = bones.copy_edit_bone(rigify_rig, dst_bone_parent_name, dst_bone_name, "root", 0.25)
            if mch_bone:
                bones.set_edit_bone_flags(mch_bone, relation_flags, deform)
                bones.add_copy_transforms_constraint(rigify_rig, mch_bone.name, dst_bone_parent_name, 1.0)
                bones.set_bone_layer(rigify_rig, dst_bone_name, layer)

        elif src_bone_name == "+EyeControl":
            eyes_bone = bones.new_edit_bone(rigify_rig, dst_bone_name, dst_bone_parent_name)
            if eyes_bone:
                # ref = list of bones to copy average positions from
                # scale = displace scale of above bones along their (normalized) direction
                distance = 0
                is_eye_parent = len(ref) == 2
                if is_eye_parent:
                    distance = bones.get_distance_between(rigify_rig, ref[0], ref[1])
                bones.copy_position(rigify_rig, dst_bone_name, ref, scale)
                eye_scale = 0.015
                eyes_bone.tail = eyes_bone.head + mathutils.Vector((0, 0, eye_scale))
                bones.set_bone_group(rigify_rig, dst_bone_name, "FK")
                if not is_eye_parent:
                    bones.add_damped_track_constraint(rigify_rig, ref[0], dst_bone_name, 1.0)
                bones.generate_eye_widget(rigify_rig, dst_bone_name, ref, distance, eye_scale)
                if is_eye_parent:
                    bones.add_pose_bone_custom_property(rigify_rig, dst_bone_name, "eyes_follow", 1.0)
                    bones.add_constraint_influence_driver(rigify_rig, dst_bone_parent_name, dst_bone_name, "eyes_follow", "COPY_TRANSFORMS")

        elif src_bone_name == "#RenameBasicFace":

            if not chr_cache.rig_full_face():
                bones.rename_bone(rigify_rig, dst_bone_name, dst_bone_parent_name)

        elif src_bone_name[:3] == "DEF" or src_bone_name[:3] == "ORG":
            def_bone = bones.copy_edit_bone(rigify_rig, src_bone_name, dst_bone_name, dst_bone_parent_name, scale)
            if def_bone:
                bones.set_edit_bone_flags(def_bone, relation_flags, deform)
                bones.set_bone_layer(rigify_rig, dst_bone_name, layer)
            # partial rotation copy for share bones
            if "_share" in dst_bone_name and ref:
                bones.add_copy_rotation_constraint(rigify_rig, dst_bone_name, ref, arg)

        else:
            def_bone = bones.copy_rl_edit_bone(cc3_rig, rigify_rig, src_bone_name, dst_bone_name, dst_bone_parent_name, scale)
            if def_bone:
                bones.set_edit_bone_flags(def_bone, relation_flags, deform)
                bones.set_bone_layer(rigify_rig, dst_bone_name, layer)


def rl_vertex_group(obj, group):
    if group in obj.vertex_groups:
        return group
    # remove "CC_Base_" from name and try again.
    group = group[8:]
    if group in obj.vertex_groups:
        return group
    return None


def rename_vertex_groups(cc3_rig, rigify_rig):
    """Rename the CC3 rig vertex weight groups to the Rigify deformation bone names,
       removes matching existing vertex groups created by parent with automatic weights.
       Thus leaving just the automatic face rig weights.
    """

    obj : bpy.types.Object
    for obj in rigify_rig.children:

        for vgrn in VERTEX_GROUP_RENAME:

            vg_to = vgrn[0]
            vg_from = rl_vertex_group(obj, vgrn[1])

            if vg_from:

                try:
                    if vg_to in obj.vertex_groups:
                        utils.log_info(f"removing {vg_to}")
                        obj.vertex_groups.remove(obj.vertex_groups[vg_to])
                except:
                    pass

                try:
                    if vg_from in obj.vertex_groups:
                        utils.log_info(f"renaming {vg_from} to {vg_to}")
                        obj.vertex_groups[vg_from].name = vg_to
                except:
                    pass

        for mod in obj.modifiers:
            if mod.type == "ARMATURE":
                mod.object = rigify_rig
                mod.use_deform_preserve_volume = True


def store_relative_mappings(meta_rig, coords):
    for mapping in RELATIVE_MAPPINGS:
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
                    box.add(tail_pos)

            box.pad(BOX_PADDING)
            coords[bone_name] = [box.relative(bone_head_pos), box.relative(bone_tail_pos)]


def restore_relative_mappings(meta_rig, coords):
    for mapping in RELATIVE_MAPPINGS:
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
                    box.add(tail_pos)

            box.pad(BOX_PADDING)

            rc = coords[bone_name]
            if (mapping[1] == "HEAD" or mapping[1] == "BOTH"):
                bone.head = box.coord(rc[0])

            if (mapping[1] == "TAIL" or mapping[1] == "BOTH"):
                bone.tail = box.coord(rc[1])


def store_bone_roll(cc3_rig, roll_store):

    for roll in ROLL_COPY:

        target_name = roll[0]
        roll_mod = roll[1]
        source_name = roll[2]

        bone = bones.get_rl_edit_bone(cc3_rig, source_name)
        if bone:
            roll_store[target_name] = bone.roll


def restore_bone_roll(meta_rig, roll_store):

    for roll in ROLL_COPY:

        target_name = roll[0]
        roll_mod = roll[1]
        source_name = roll[2]

        bone = bones.get_edit_bone(meta_rig, target_name)
        if bone:
            bone.roll = roll_store[target_name] + roll_mod * 0.0174532925199432957


def set_rigify_params(rigify_rig):
    #e.g. bpy.context.active_object.pose.bones['upper_arm.R'].rigify_parameters.rotation_axis = "z"

    for params in RIGIFY_PARAMS:
        bone_name = params[0]
        bone_rot_axis = params[1]
        pose_bone = bones.get_pose_bone(rigify_rig, bone_name)
        if pose_bone:
            pose_bone.rigify_parameters.rotation_axis = bone_rot_axis


def map_face(cc3_rig, meta_rig):

    obj : bpy.types.Object = None
    for child in cc3_rig.children:
        if child.name.lower().endswith("base_eye"):
            obj = child
    length = 0.375

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
    head_bone_source = bones.get_rl_bone(cc3_rig, "CC_Base_Head")

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


def report_uv_face_targets(obj, meta_rig):

    mat_slot = get_head_material_slot(obj)
    mesh = obj.data
    t_mesh = geom.get_triangulated_bmesh(mesh)

    if utils.edit_mode_to(meta_rig):

        bone : bpy.types.EditBone
        for bone in meta_rig.data.edit_bones:
            if bone.layers[0] and bone.name != "face":
                head_world = bone.head
                tail_world = bone.tail

                head_uv = geom.get_uv_from_world(obj, t_mesh, mat_slot, head_world)
                tail_uv = geom.get_uv_from_world(obj, t_mesh, mat_slot, tail_world)

                print (f"{bone.name} - uv: {head_uv} -> {tail_uv}")
    return


def map_uv_targets(chr_cache, cc3_rig, meta_rig):
    obj = None
    for obj_cache in chr_cache.object_cache:
        if obj_cache.object_type == "BODY":
            obj = obj_cache.object
    if obj is None:
        utils.log_error("Cannot find BODY mesh for uv targets!")
        return

    mat_slot = get_head_material_slot(obj)
    mesh = obj.data
    t_mesh = geom.get_triangulated_bmesh(mesh)

    TARGETS = None
    if chr_cache.generation == "G3Plus":
        TARGETS = UV_TARGETS_G3PLUS
    elif chr_cache.generation == "G3":
        TARGETS = UV_TARGETS_G3
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

                    world = geom.get_world_from_uv(obj, t_mesh, mat_slot, uv_target, UV_THRESHOLD)
                    if m_bone or m_last:
                        m_uv_target = mirror_uv_target(uv_target)
                        m_world = geom.get_world_from_uv(obj, t_mesh, mat_slot, m_uv_target, UV_THRESHOLD)

                    if world:
                        if last:
                            utils.log_info(last.name + ": Tail: " + str(world))
                            last.tail = world
                            if m_last:
                                m_last.tail = m_world
                        if bone:
                            utils.log_info(bone.name + ": Head: " + str(world))
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

                    world_head = geom.get_world_from_uv(obj, t_mesh, mat_slot, uv_head, UV_THRESHOLD)
                    world_tail = geom.get_world_from_uv(obj, t_mesh, mat_slot, uv_tail, UV_THRESHOLD)

                    if m_bone:
                        muv_head = mirror_uv_target(uv_head)
                        muv_tail = mirror_uv_target(uv_tail)
                        mworld_head = geom.get_world_from_uv(obj, t_mesh, mat_slot, muv_head, UV_THRESHOLD)
                        mworld_tail = geom.get_world_from_uv(obj, t_mesh, mat_slot, muv_tail, UV_THRESHOLD)

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

                world = geom.get_world_from_uv(obj, t_mesh, mat_slot, uv_target, UV_THRESHOLD)
                if world:
                    bone.head = world

            elif type == "TAIL":
                uv_target = uvt[2]
                uv_target.append(0)

                world = geom.get_world_from_uv(obj, t_mesh, mat_slot, uv_target, UV_THRESHOLD)
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

    dst_bone_name = mapping[0]
    src_bone_head_name = mapping[1]
    src_bone_tail_name = mapping[2]

    utils.log_info(f"Mapping: {dst_bone_name} from: {src_bone_head_name}/{src_bone_tail_name}")

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


def match_meta_rig(chr_cache, cc3_rig, meta_rig):
    """Only call in bone edit mode...
    """
    relative_coords = {}
    roll_store = {}

    if utils.set_mode("OBJECT"):
        utils.set_active_object(cc3_rig)

        if utils.set_mode("EDIT"):
            store_bone_roll(cc3_rig, roll_store)

            if utils.set_mode("OBJECT"):
                utils.set_active_object(meta_rig)

                if utils.set_mode("EDIT"):

                    prune_meta_rig(meta_rig)
                    store_relative_mappings(meta_rig, relative_coords)

                    for mapping in BONE_MAPPINGS:
                        map_bone(cc3_rig, meta_rig, mapping)

                    restore_relative_mappings(meta_rig, relative_coords)
                    restore_bone_roll(meta_rig, roll_store)
                    set_rigify_params(meta_rig)
                    if chr_cache.rig_full_face():
                        map_uv_targets(chr_cache, cc3_rig, meta_rig)
                    map_face(cc3_rig, meta_rig)
                    return

    utils.log_error("Unable to match meta rig.")


def fix_bend(meta_rig, bone_one_name, bone_two_name, dir : mathutils.Vector):
    """Determine if the bend between two bones is sufficient to generate an accurate pole in the rig,
       by calculating where the middle joint lies on the line between the start and end points and
       determining if the distance to that line is large enough and in the right direction.
       Recalculating the joint position if not.
    """

    dir.normalize()

    utils.log_info(f"Fix Bend: {bone_one_name}, {bone_two_name}")

    if utils.set_mode("OBJECT") and utils.set_active_object(meta_rig) and utils.set_mode("EDIT"):

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

    return


def convert_to_basic_face_rig(meta_rig):

    if utils.set_mode("OBJECT") and utils.set_active_object(meta_rig) and utils.set_mode("EDIT"):

        delete_bones = []

        # remove all meta-rig bones in layer[0] (the face bones)
        bone : bpy.types.EditBone
        for bone in meta_rig.data.edit_bones:
            if bone.layers[0]:
                delete_bones.append(bone)

        for bone in delete_bones:
            meta_rig.data.edit_bones.remove(bone)

        y = 0
        # add the needed face bones (eyes and jaw)
        for face_bone_def in FACE_BONES:

            bone_name = face_bone_def[0]
            parent_name = face_bone_def[1]
            relation_flags = face_bone_def[2]
            layer = face_bone_def[3]
            mode = "NONE"
            if len(face_bone_def) > 4:
                mode = face_bone_def[4]
            print("MODE: " + mode)

            utils.log_info(f"Adding bone: {bone_name}")

            # make a new bone
            face_bone = meta_rig.data.edit_bones.new(bone_name)

            # give the bone a non zero length otherwise the bone will be deleted as invalid when exiting edit mode...
            # (the bone will be positioned correctly later acording to the bone mappings)
            face_bone.head = (0, y, 0)
            # and make sure chains of bones don't overlap and become invalid...
            y -= 0.1
            face_bone.tail = (0, y, 0)

            # set the bone parent
            bone_parent = bones.get_edit_bone(meta_rig, parent_name)
            if bone_parent:
                utils.log_info(f"Parenting bone: {bone_name} to {parent_name}")
                face_bone.parent = bone_parent

            # set the bone flags
            face_bone.use_connect = True if "C" in relation_flags else False
            face_bone.use_local_location = True if "L" in relation_flags else False
            face_bone.use_inherit_rotation = True if "R" in relation_flags else False
            face_bone.layers[layer] = True

            # set pose bone rigify types
            pose_bone = bones.get_pose_bone(meta_rig, bone_name)
            if pose_bone:
                if mode == "JAW":
                    try:
                        pose_bone.rigify_type = 'basic.pivot'
                        pose_bone.rigify_parameters.make_extra_control = True
                        pose_bone.rigify_parameters.pivot_master_widget_type = "jaw"
                        pose_bone.rigify_parameters.make_control = False
                        pose_bone.rigify_parameters.make_extra_deform = True
                    except:
                        utils.log_error("Unable to set rigify Jaw type.")
                elif mode == "TONGUE":
                    try:
                        pose_bone.rigify_type = 'face.basic_tongue'
                    except:
                        utils.log_error("Unable to set rigify Tongue type.")
                else:
                    pose_bone.rigify_type = ""


def correct_meta_rig(meta_rig):
    """Add a slight displacement (if needed) to the knee and elbow to ensure the poles are the right way.
    """

    fix_bend(meta_rig, "thigh.L", "shin.L", mathutils.Vector((0,-1,0)))
    fix_bend(meta_rig, "thigh.R", "shin.R", mathutils.Vector((0,-1,0)))
    fix_bend(meta_rig, "upper_arm.L", "forearm.L", mathutils.Vector((0,1,0)))
    fix_bend(meta_rig, "upper_arm.R", "forearm.R", mathutils.Vector((0,1,0)))


def modify_controls(rigify_rig):

    # scale, location, rotation modifiers for custom control shapes is Blender 3.0.0+ only
    if utils.is_blender_version("3.0.0"):

        if utils.set_mode("OBJECT"):

            for mod in CONTROL_MODIFY:
                bone_name = mod[0]
                scale = mod[1]
                translation = mod[2]
                rotation = mod[3]

                bone = bones.get_pose_bone(rigify_rig, bone_name)
                if bone:
                    bone.custom_shape_scale_xyz = scale
                    bone.custom_shape_translation = translation
                    bone.custom_shape_rotation_euler = rotation


def reparent_to_rigify(self, chr_cache, cc3_rig, rigify_rig):
    """Unparent (with transform) from the original CC3 rig and reparent to the new rigify rig (with automatic weights for the body),
       setting the armature modifiers to the new rig.

       The automatic weights will generate vertex weights for the additional face bones in the new rig.
       (But only for the Body mesh)
    """

    props = bpy.context.scene.CC3ImportProps

    show_warning = False
    result = 1

    if utils.set_mode("OBJECT"):

        for obj in cc3_rig.children:
            if obj.type == "MESH" and obj.parent == cc3_rig:

                obj_cache = chr_cache.get_object_cache(obj)

                if utils.try_select_object(obj, True) and utils.set_active_object(obj):
                    bpy.ops.object.parent_clear(type = "CLEAR_KEEP_TRANSFORM")

                # only the body and face objects will generate the automatic weights for the face rig.
                if (chr_cache.rigified_full_face_rig and
                    utils.object_exists_is_mesh(obj) and
                    len(obj.data.vertices) >= 2 and
                    is_face_object(obj_cache, obj)):

                    if not show_warning:
                        print("")
                        print("Attemping to parent the Body mesh to the Face Rig:")
                        print("If this fails, the face rig will not work and will need to re-parented by other means.")
                        print("")
                        show_warning = True

                    obj_result = try_parent_auto(chr_cache, rigify_rig, obj)
                    if obj_result < result:
                        result = obj_result

                else:

                    if utils.try_select_object(rigify_rig) and utils.set_active_object(rigify_rig):
                        bpy.ops.object.parent_set(type = "OBJECT", keep_transform = True)

                    arm_mod : bpy.types.ArmatureModifier = modifiers.add_armature_modifier(obj, True)
                    if arm_mod:
                        arm_mod.object = rigify_rig

    return result


def clean_up(chr_cache, cc3_rig, rigify_rig, meta_rig):
    """Rename the rigs, hide the original CC3 Armature and remove the meta rig.
       Set the new rig into pose mode.
    """

    rig_name = cc3_rig.name
    cc3_rig.name = rig_name + "_OldCC"
    cc3_rig.hide_set(True)
    bpy.data.objects.remove(meta_rig)
    rigify_rig.name = rig_name + "_Rigify"

    if utils.set_mode("OBJECT"):
        utils.clear_selected_objects()
        if utils.try_select_object(rigify_rig, True):
            if utils.set_active_object(rigify_rig):
                utils.set_mode("POSE")

    chr_cache.set_rigify_armature(rigify_rig)


def prep_export(rigigy_rig):
    pass


def is_face_object(obj_cache, obj):
    if obj and obj.type == "MESH":
        if obj_cache and obj_cache.object_type in BODY_TYPES:
            return True
        if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
            for shape_key in obj.data.shape_keys.key_blocks:
                if shape_key.name in FACE_TEST_SHAPEKEYS:
                    return True
    return False


def is_face_def_bone(bvg):
    for face_def_prefix in FACE_DEF_BONE_PREFIX:
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


def lock_non_face_vgroups(chr_cache):
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
    arm = chr_cache.get_armature()
    if arm:
        for bone in arm.data.bones:
            if bone.name in FACE_DEF_BONE_PREPASS:
                bone.use_deform = False
    # select body mesh and active rig
    if body and arm and utils.set_mode("OBJECT"):
        utils.try_select_objects([body, arm], True)
        utils.set_active_object(arm)


def unlock_vgroups(chr_cache):
    for obj_cache in chr_cache.object_cache:
        if obj_cache.object_type in BODY_TYPES:
            obj = obj_cache.object
            vg : bpy.types.VertexGroup
            for vg in obj.vertex_groups:
                vg.lock_weight = False
    # turn on deform for the teeth and the eyes
    arm = chr_cache.get_armature()
    if arm:
        for bone in arm.data.bones:
            if bone.name in FACE_DEF_BONE_PREPASS:
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
        print(f" - Parenting: {obj.name}")
        bpy.ops.object.parent_set(type = "ARMATURE_AUTO", keep_transform = True)
        if not test_face_vgroups(rig, obj):
            return False
    return True


def try_parent_auto(chr_cache, rig, obj):
    modifiers.remove_object_modifiers(obj, "ARMATURE")

    result = 1

    # first attempt

    if parent_set_with_test(rig, obj):
        print(f"Success!")
    else:
        print(f" - Parent with automatic weights failed: attempting mesh clean up...")
        mesh_clean_up(obj)
        if result == 1:
            result = 0

        # second attempt

        if parent_set_with_test(rig, obj):
            print(f"Success!")
        else:
            body = chr_cache.get_body()

            # third attempt

            if obj == body:
                print(f" - Parent with automatic weights failed again: trying just the head mesh...")
                head = separate_head(obj)

                if parent_set_with_test(rig, head):
                    print(f"Success!")
                else:
                    print(f"Automatic weights failed for {obj.name}, will need to re-parented by other means!")
                    result = -1

                rejoin_head(head, body)

            else:

                print(f" - Parent with automatic weights failed again: transferring weights from body mesh.")
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

                print(f"   vertex weights will need to be checked.")

    return result


def attempt_reparent_auto_character(chr_cache):
    utils.set_mode("OBJECT")
    utils.clear_selected_objects()
    result = 1
    rig = chr_cache.get_armature()
    print("Attemping to parent the Body mesh to the Face Rig:")
    print("If this fails, the face rig may not work and will need to re-parented by other means.")
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
            bpy.data.scenes["Scene"].surface_resolution = 512
            bpy.data.scenes["Scene"].surface_loops = 5
            bpy.data.scenes["Scene"].surface_samples = 128
            bpy.data.scenes["Scene"].surface_influence = 24
            bpy.data.scenes["Scene"].surface_falloff = 0.15
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
        if utils.set_mode("OBJECT"):
            bpy.ops.object.armature_human_metarig_add()
            self.meta_rig = utils.get_active_object()
            if self.meta_rig is not None:
                self.meta_rig.location = (0,0,0)
                if self.cc3_rig is not None:
                    self.cc3_rig.location = (0,0,0)
                    self.cc3_rig.data.pose_position = "REST"
                    if not chr_cache.rig_full_face():
                        convert_to_basic_face_rig(self.meta_rig)
                    match_meta_rig(chr_cache, self.cc3_rig, self.meta_rig)
                    chr_cache.rigified_full_face_rig = chr_cache.rig_full_face()
                else:
                    utils.log_error("Unable to locate imported CC3 rig!", self)
            else:
                utils.log_error("Unable to create meta rig!", self)
        else:
            utils.log_error("Not in OBJECT mode!", self)

    def execute(self, context):
        props: properties.CC3ImportProps = bpy.context.scene.CC3ImportProps
        chr_cache = props.get_context_character_cache(context)

        self.cc3_rig = None
        self.meta_rig = None
        self.rigify_rig = None
        self.auto_weight_failed = False
        self.auto_weight_report = ""

        if chr_cache:

            self.cc3_rig = chr_cache.get_armature()

            if self.param == "ALL":

                if self.cc3_rig:
                    self.add_meta_rig(chr_cache)

                    if self.meta_rig:
                        correct_meta_rig(self.meta_rig)
                        bpy.ops.pose.rigify_generate()
                        self.rigify_rig = bpy.context.active_object

                        if self.rigify_rig:
                            modify_controls(self.rigify_rig)
                            face_result = reparent_to_rigify(self, chr_cache, self.cc3_rig, self.rigify_rig)
                            add_def_bones(chr_cache, self.cc3_rig, self.rigify_rig)
                            rename_vertex_groups(self.cc3_rig, self.rigify_rig)
                            clean_up(chr_cache, self.cc3_rig, self.rigify_rig, self.meta_rig)

                    chr_cache.rig_meta_rig = None
                    if face_result == 1:
                        self.report({'INFO'}, "Rigify Complete! No errors detected.")
                    elif face_result == 0:
                        self.report({'WARNING'}, "Rigify Complete! Some issues with the face rig were detected and fixed automatically. See console log.")
                    else:
                        self.report({'ERROR'}, "Rigify Incomplete! Face rig weighting Failed!. See console log.")

            elif self.param == "META_RIG":

                if self.cc3_rig:
                    self.add_meta_rig(chr_cache)

                    if self.meta_rig:
                        chr_cache.rig_meta_rig = self.meta_rig
                        correct_meta_rig(self.meta_rig)

                        self.report({'INFO'}, "Meta-rig generated!")

            elif self.param == "RIGIFY_META":

                self.meta_rig = chr_cache.rig_meta_rig

                if self.cc3_rig and self.meta_rig:

                    if utils.set_mode("OBJECT") and utils.try_select_object(self.meta_rig) and utils.set_active_object(self.meta_rig):
                        bpy.ops.pose.rigify_generate()
                        self.rigify_rig = bpy.context.active_object

                        if self.rigify_rig:
                            modify_controls(self.rigify_rig)
                            face_result = reparent_to_rigify(self, chr_cache, self.cc3_rig, self.rigify_rig)
                            add_def_bones(chr_cache, self.cc3_rig, self.rigify_rig)
                            rename_vertex_groups(self.cc3_rig, self.rigify_rig)
                            clean_up(chr_cache, self.cc3_rig, self.rigify_rig, self.meta_rig)

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
        if bl_options:
            return True
        else:
            return False
    except:
        return False

