import bpy
from . import bones, utils


def fix_armature(arm):
    if arm:
        utils.set_only_active_object(arm)
        facing = get_arm_facing(arm)
        utils.log_info(f"VRM Alignment: Forward = {facing}")
        if facing != "-Y":
            utils.log_info("Aligning armature: Forward = -Y")
            arm.rotation_mode = "XYZ"
            arm.rotation_euler = (0, 0, 3.1415926535897)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        restore_bone_display(arm)


def get_arm_facing(arm):
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


def generate_hik_profile(arm, name, path):
    hik = HIK_PROFILE_TEMPLATE
    bone_list = ""
    bone_list += pack_rotation(name, arm.rotation_quaternion)
    for pose_bone in arm.pose.bones:
        bone_list += pack_bone(arm, pose_bone)
    for child in arm.children:
        if child.type == "MESH":
            bone_list += pack_rotation(child.name, child.rotation_quaternion)
    hik = hik.replace("$BONE_LIST", bone_list)
    with open(path, "w") as write_file:
        utils.log_info(f"Writing VRM HIK Profile: {path}")
        write_file.write(hik)
    return True


HIK_PROFILE_TEMPLATE = """
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


[FloorContact]
HandBottom = 5.761833191
HandBack = 9.282436371
HandMiddle = 0.
HandFront = 12.67779541
HandIn = 6.756534576
HandOut = 6.511818886
FootBottom = 11.55122375
FootBack = 4.564089775
FootMiddle = 0.
FootFront = 16.02571487
FootIn = 4.078876495
FootOut = 4.569028378


[Property]
AnkleHeight = 0.
AnkleSpacing = 0.
HipsForward = 0.
AutoAnkleHeight = true
AutoAnkleSpacing = true
RollExtractionMode = false


[RootTransform]
Value = 1.,100.,100.,100.,0.,0.,0.,1.,0.,0.,0.,1.,0.,0.,0.,


[BoneTypeOfBonesUnderHead]
J_Adj_L_FaceEye = Facial
J_Adj_R_FaceEye = Facial
"""