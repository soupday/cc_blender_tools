import bpy
from . import bones, utils


def fix_armature(arm):
    if arm:
        utils.set_only_active_object(arm)
        facing = get_vrm_rig_facing(arm)
        utils.log_info(f"VRM Alignment: Forward = {facing}")
        if facing != "-Y":
            utils.log_info("Aligning armature: Forward = -Y")
            arm.rotation_mode = "XYZ"
            arm.rotation_euler = (0, 0, 3.1415926535897)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        restore_bone_display(arm)


def get_vrm_rig_facing(arm):
    """VRM1.0 aligns with forward +Y
       VRM2.0 aligns with forward -Y
       need to figure out which is which."""
    root_bone = bones.get_pose_bone(arm, "Root")
    toe_bone = bones.get_pose_bone(arm, "J_Bip_L_ToeBase")
    if not (root_bone and toe_bone):
        return "-Y"
    delta = arm.matrix_world @ toe_bone.head - arm.matrix_world @ root_bone.head
    if delta.y > 0:
        return "Y"
    else:
        return "-Y"


def restore_bone_display(arm):
    utils.object_mode_to(arm)
    pose_bone: bpy.types.PoseBone
    for pose_bone in arm.pose.bones:
        pose_bone.custom_shape = None


def pack_rotation(name, rot):
    return f"{name} = {rot.x},{rot.y},{rot.z},{rot.w},\n"


def pack_bone(arm, pose_bone: bpy.types.PoseBone):
    bone_name = pose_bone.name
    parent_bone = pose_bone.parent
    if parent_bone:
        rot = (parent_bone.matrix.inverted() @ pose_bone.matrix).to_quaternion()
    else:
        rot = pose_bone.matrix.to_quaternion()
    return pack_rotation(bone_name, rot)


def generate_hik_profile(arm, name, path, hik_template):
    bone_list = ""
    bone_list += pack_rotation(name, arm.rotation_quaternion)
    for pose_bone in arm.pose.bones:
        bone_list += pack_bone(arm, pose_bone)
    for child in arm.children:
        if child.type == "MESH":
            bone_list += pack_rotation(child.name, child.rotation_quaternion)
    hik_template = hik_template.replace("$BONE_LIST", bone_list)
    with open(path, "w") as write_file:
        utils.log_info(f"Writing VRM HIK Profile: {path}")
        write_file.write(hik_template)
    return True


RIGIFY_METARIG_PROFILE_TEMPLATE = """
[BoneMapOption]
Prefix =


[BoneMap]
f_index_01_L = LeftHandIndex1
f_index_01_R = RightHandIndex1
f_index_02_L = LeftHandIndex2
f_index_02_R = RightHandIndex2
f_index_03_L = LeftHandIndex3
f_index_03_R = RightHandIndex3
f_middle_01_L = LeftHandMiddle1
f_middle_01_R = RightHandMiddle1
f_middle_02_L = LeftHandMiddle2
f_middle_02_R = RightHandMiddle2
f_middle_03_L = LeftHandMiddle3
f_middle_03_R = RightHandMiddle3
f_pinky_01_L = LeftHandPinky1
f_pinky_01_R = RightHandPinky1
f_pinky_02_L = LeftHandPinky2
f_pinky_02_R = RightHandPinky2
f_pinky_03_L = LeftHandPinky3
f_pinky_03_R = RightHandPinky3
f_ring_01_L = LeftHandRing1
f_ring_01_R = RightHandRing1
f_ring_02_L = LeftHandRing2
f_ring_02_R = RightHandRing2
f_ring_03_L = LeftHandRing3
f_ring_03_R = RightHandRing3
foot_L = LeftFoot
foot_R = RightFoot
forearm_L = LeftForeArm
forearm_L_001 = LeftForeArmRoll
forearm_R = RightForeArm
forearm_R_001 = RightForeArmRoll
hand_L = LeftHand
hand_R = RightHand
shin_L = LeftLeg
shin_L_001 = LeftLegRoll
shin_R = RightLeg
shin_R_001 = RightLegRoll
shoulder_L = LeftShoulder
shoulder_R = RightShoulder
spine = Hips
spine_001 = Spine
spine_002 = Spine1
spine_003 = Spine2
spine_004 = Neck
spine_005 = Neck1
spine_006 = Head
thigh_L = LeftUpLeg
thigh_L_001 = LeftUpLegRoll
thigh_R = RightUpLeg
thigh_R_001 = RightUpLegRoll
thumb_01_L = LeftHandThumb1
thumb_01_R = RightHandThumb1
thumb_02_L = LeftHandThumb2
thumb_02_R = RightHandThumb2
thumb_03_L = LeftHandThumb3
thumb_03_R = RightHandThumb3
upper_arm_L = LeftArm
upper_arm_L_001 = LeftArmRoll
upper_arm_R = RightArm
upper_arm_R_001 = RightArmRoll


[BoneRotate]
$BONE_LIST


[RootTransform]
Value = 1.,1.,1.,1.,0.,0.,0.,1.,0.,0.,0.,1.,0.,0.,0.,


[FacialMap_LEye]
Bone0 = eye_L


[FacialMap_REye]
Bone0 = eye_R


[BoneTypeOfBonesUnderHead]
jaw = Facial
tongue = Facial
tongue_001 = Unused
tongue_002 = Unused
teeth_T = Facial
teeth_B = Facial
eye_R = Facial
eye_L = Facial
"""


RIGIFY_CC_BASE_PROFILE_TEMPLATE = """
[BoneMapOption]
Prefix =


[BoneMap]
CC_Base_Head = Head
CC_Base_Hip = Hips
CC_Base_L_Calf = LeftLeg
CC_Base_L_CalfTwist = LeftLegRoll
CC_Base_L_Clavicle = LeftShoulder
CC_Base_L_Foot = LeftFoot
CC_Base_L_Forearm = LeftForeArm
CC_Base_L_ForearmTwist = LeftForeArmRoll
CC_Base_L_Hand = LeftHand
CC_Base_L_Index1 = LeftHandIndex1
CC_Base_L_Index2 = LeftHandIndex2
CC_Base_L_Index3 = LeftHandIndex3
CC_Base_L_Mid1 = LeftHandMiddle1
CC_Base_L_Mid2 = LeftHandMiddle2
CC_Base_L_Mid3 = LeftHandMiddle3
CC_Base_L_Pinky1 = LeftHandPinky1
CC_Base_L_Pinky2 = LeftHandPinky2
CC_Base_L_Pinky3 = LeftHandPinky3
CC_Base_L_Ring1 = LeftHandRing1
CC_Base_L_Ring2 = LeftHandRing2
CC_Base_L_Ring3 = LeftHandRing3
CC_Base_L_Thigh = LeftUpLeg
CC_Base_L_ThighTwist = LeftUpLegRoll
CC_Base_L_Thumb1 = LeftHandThumb1
CC_Base_L_Thumb2 = LeftHandThumb2
CC_Base_L_Thumb3 = LeftHandThumb3
CC_Base_L_Upperarm = LeftArm
CC_Base_L_UpperarmTwist = LeftArmRoll
CC_Base_NeckTwist01 = Neck
CC_Base_NeckTwist02 = Neck1
CC_Base_R_Calf = RightLeg
CC_Base_R_CalfTwist = RightLegRoll
CC_Base_R_Clavicle = RightShoulder
CC_Base_R_Foot = RightFoot
CC_Base_R_Forearm = RightForeArm
CC_Base_R_ForearmTwist = RightForeArmRoll
CC_Base_R_Hand = RightHand
CC_Base_R_Index1 = RightHandIndex1
CC_Base_R_Index2 = RightHandIndex2
CC_Base_R_Index3 = RightHandIndex3
CC_Base_R_Mid1 = RightHandMiddle1
CC_Base_R_Mid2 = RightHandMiddle2
CC_Base_R_Mid3 = RightHandMiddle3
CC_Base_R_Pinky1 = RightHandPinky1
CC_Base_R_Pinky2 = RightHandPinky2
CC_Base_R_Pinky3 = RightHandPinky3
CC_Base_R_Ring1 = RightHandRing1
CC_Base_R_Ring2 = RightHandRing2
CC_Base_R_Ring3 = RightHandRing3
CC_Base_R_Thigh = RightUpLeg
CC_Base_R_ThighTwist = RightUpLegRoll
CC_Base_R_Thumb1 = RightHandThumb1
CC_Base_R_Thumb2 = RightHandThumb2
CC_Base_R_Thumb3 = RightHandThumb3
CC_Base_R_Upperarm = RightArm
CC_Base_R_UpperarmTwist = RightArmRoll
CC_Base_Spine01 = Spine1
CC_Base_Spine02 = Spine2
CC_Base_Waist = Spine


[BoneRotate]
$BONE_LIST


[RootTransform]
Value = 1.,1.,1.,1.,0.,0.,0.,1.,0.,0.,0.,1.,0.,0.,0.,


[FacialMap_LEye]
Bone0 = CC_Base_L_Eye


[FacialMap_REye]
Bone0 = CC_Base_R_Eye


[BoneTypeOfBonesUnderHead]
CC_Base_JawRoot = Facial
CC_Base_Tongue01 = Facial
CC_Base_Tongue02 = Unused
CC_Base_Tongue03 = Unused
CC_Base_Teeth01 = Facial
CC_Base_Teeth02 = Facial
CC_Base_L_Eye = Facial
CC_Base_R_Eye = Facial
"""


RIGIFY_BASE_PROFILE_TEMPLATE = """
[BoneMapOption]
Prefix =


[BoneMap]
Rigify_Head = Head
Rigify_Hip = Hips
Rigify_L_Calf = LeftLeg
Rigify_L_CalfTwist = LeftLegRoll
Rigify_L_Clavicle = LeftShoulder
Rigify_L_Foot = LeftFoot
Rigify_L_Forearm = LeftForeArm
Rigify_L_ForearmTwist = LeftForeArmRoll
Rigify_L_Hand = LeftHand
Rigify_L_Index1 = LeftHandIndex1
Rigify_L_Index2 = LeftHandIndex2
Rigify_L_Index3 = LeftHandIndex3
Rigify_L_Mid1 = LeftHandMiddle1
Rigify_L_Mid2 = LeftHandMiddle2
Rigify_L_Mid3 = LeftHandMiddle3
Rigify_L_Pinky1 = LeftHandPinky1
Rigify_L_Pinky2 = LeftHandPinky2
Rigify_L_Pinky3 = LeftHandPinky3
Rigify_L_Ring1 = LeftHandRing1
Rigify_L_Ring2 = LeftHandRing2
Rigify_L_Ring3 = LeftHandRing3
Rigify_L_Thigh = LeftUpLeg
Rigify_L_ThighTwist = LeftUpLegRoll
Rigify_L_Thumb1 = LeftHandThumb1
Rigify_L_Thumb2 = LeftHandThumb2
Rigify_L_Thumb3 = LeftHandThumb3
Rigify_L_Upperarm = LeftArm
Rigify_L_UpperarmTwist = LeftArmRoll
Rigify_NeckTwist01 = Neck
Rigify_NeckTwist02 = Neck1
Rigify_R_Calf = RightLeg
Rigify_R_CalfTwist = RightLegRoll
Rigify_R_Clavicle = RightShoulder
Rigify_R_Foot = RightFoot
Rigify_R_Forearm = RightForeArm
Rigify_R_ForearmTwist = RightForeArmRoll
Rigify_R_Hand = RightHand
Rigify_R_Index1 = RightHandIndex1
Rigify_R_Index2 = RightHandIndex2
Rigify_R_Index3 = RightHandIndex3
Rigify_R_Mid1 = RightHandMiddle1
Rigify_R_Mid2 = RightHandMiddle2
Rigify_R_Mid3 = RightHandMiddle3
Rigify_R_Pinky1 = RightHandPinky1
Rigify_R_Pinky2 = RightHandPinky2
Rigify_R_Pinky3 = RightHandPinky3
Rigify_R_Ring1 = RightHandRing1
Rigify_R_Ring2 = RightHandRing2
Rigify_R_Ring3 = RightHandRing3
Rigify_R_Thigh = RightUpLeg
Rigify_R_ThighTwist = RightUpLegRoll
Rigify_R_Thumb1 = RightHandThumb1
Rigify_R_Thumb2 = RightHandThumb2
Rigify_R_Thumb3 = RightHandThumb3
Rigify_R_Upperarm = RightArm
Rigify_R_UpperarmTwist = RightArmRoll
Rigify_Spine01 = Spine1
Rigify_Spine02 = Spine2
Rigify_Waist = Spine


[BoneRotate]
$BONE_LIST


[RootTransform]
Value = 1.,1.,1.,1.,0.,0.,0.,1.,0.,0.,0.,1.,0.,0.,0.,


[FacialMap_LEye]
Bone0 = Rigify_L_Eye


[FacialMap_REye]
Bone0 = Rigify_R_Eye


[BoneTypeOfBonesUnderHead]
Rigify_JawRoot = Facial
Rigify_Tongue01 = Facial
Rigify_Tongue02 = Unused
Rigify_Tongue03 = Unused
Rigify_Teeth01 = Facial
Rigify_Teeth02 = Facial
Rigify_L_Eye = Facial
Rigify_R_Eye = Facial
"""


VRM_HIK_PROFILE_TEMPLATE = """
[BoneMapOption]
Prefix =


[BoneMap]
J_Bip_C_Chest = Spine1
J_Bip_C_Head = Head
J_Bip_C_Hips = Hips
J_Bip_C_Neck = Neck
J_Bip_C_Spine = Spine
J_Bip_C_UpperChest = Spine2
J_Bip_L_Foot = LeftFoot
J_Bip_L_Hand = LeftHand
J_Bip_L_Index1 = LeftHandIndex1
J_Bip_L_Index2 = LeftHandIndex2
J_Bip_L_Index3 = LeftHandIndex3
J_Bip_L_Little1 = LeftHandPinky1
J_Bip_L_Little2 = LeftHandPinky2
J_Bip_L_Little3 = LeftHandPinky3
J_Bip_L_LowerArm = LeftForeArm
J_Bip_L_LowerLeg = LeftLeg
J_Bip_L_Middle1 = LeftHandMiddle1
J_Bip_L_Middle2 = LeftHandMiddle2
J_Bip_L_Middle3 = LeftHandMiddle3
J_Bip_L_Ring1 = LeftHandRing1
J_Bip_L_Ring2 = LeftHandRing2
J_Bip_L_Ring3 = LeftHandRing3
J_Bip_L_Shoulder = LeftShoulder
J_Bip_L_Thumb1 = LeftHandThumb1
J_Bip_L_Thumb2 = LeftHandThumb2
J_Bip_L_Thumb3 = LeftHandThumb3
J_Bip_L_UpperArm = LeftArm
J_Bip_L_UpperLeg = LeftUpLeg
J_Bip_R_Foot = RightFoot
J_Bip_R_Hand = RightHand
J_Bip_R_Index1 = RightHandIndex1
J_Bip_R_Index2 = RightHandIndex2
J_Bip_R_Index3 = RightHandIndex3
J_Bip_R_Little1 = RightHandPinky1
J_Bip_R_Little2 = RightHandPinky2
J_Bip_R_Little3 = RightHandPinky3
J_Bip_R_LowerArm = RightForeArm
J_Bip_R_LowerLeg = RightLeg
J_Bip_R_Middle1 = RightHandMiddle1
J_Bip_R_Middle2 = RightHandMiddle2
J_Bip_R_Middle3 = RightHandMiddle3
J_Bip_R_Ring1 = RightHandRing1
J_Bip_R_Ring2 = RightHandRing2
J_Bip_R_Ring3 = RightHandRing3
J_Bip_R_Shoulder = RightShoulder
J_Bip_R_Thumb1 = RightHandThumb1
J_Bip_R_Thumb2 = RightHandThumb2
J_Bip_R_Thumb3 = RightHandThumb3
J_Bip_R_UpperArm = RightArm
J_Bip_R_UpperLeg = RightUpLeg


[BoneRotate]
$BONE_LIST


[RootTransform]
Value = 1.,100.,100.,100.,0.,0.,0.,1.,0.,0.,0.,1.,0.,0.,0.,


[BoneTypeOfBonesUnderHead]
J_Adj_L_FaceEye = Facial
J_Adj_R_FaceEye = Facial
"""