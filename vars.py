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

# Set by __init__.py from the bl_info dict

VERSION_STRING = ""

def set_version_string(bl_info):
    global VERSION_STRING
    VERSION_STRING = "v" + str(bl_info["version"][0]) + "." + str(bl_info["version"][1]) + "." + str(bl_info["version"][2])

# blender uses metres, CC3 uses centimetres
UNIT_SCALE = 0.01
SKIN_SSS_RADIUS_SCALE = 0.015
TEETH_SSS_RADIUS_SCALE = 0.03
HAIR_SSS_RADIUS_SCALE = 0.005
EYE_SSS_RADIUS_SCALE = 0.005

# https://docs.blender.org/manual/en/latest/files/media/image_formats.html
IMAGE_TYPES = [".bmp", ".sgi", ".rgb", ".bw", ".png", ".jpg", ".jpeg", ".jp2", ".j2c",
               ".tga", ".cin", ".dpx", ".exr", ".hdr", ".tif", ".tiff"]

# base names of all node groups in the library blend file
NODE_GROUPS = ["tiling_pivot_mapping", "tiling_mapping", "rl_tearline_shader",
               "rl_eye_occlusion_shader", "rl_skin_shader", "rl_head_shader", "rl_tongue_shader", "rl_teeth_shader",
               "rl_cornea_shader", "rl_cornea_refractive_shader", "rl_eye_shader", "rl_pbr_shader", "rl_sss_shader", "rl_hair_shader"]


MATERIAL_TYPES = [
                        ("DEFAULT", "Default", "Default material"),
                        ("SSS", "Subsurface", "Subsurface Scattering material"),
                        ("SKIN_HEAD", "Head", "Head skin material"),
                        ("SKIN_BODY", "Body", "Body skin material"),
                        ("SKIN_ARM", "Arm", "Arm skin material"),
                        ("SKIN_LEG", "Leg", "Leg skin material"),
                        ("TEETH_UPPER", "Upper Teeth", "Upper teeth material"),
                        ("TEETH_LOWER", "Lower Teeth", "Lower teeth material"),
                        ("TONGUE", "Tongue", "Tongue material"),
                        ("HAIR", "Hair", "Hair material"),
                        ("SCALP", "Scalp", "Scalp or base hair material"),
                        ("EYELASH", "Eyelash", "Eyelash material"),
                        ("NAILS", "Nails", "Finger and toe nails material"),
                        ("CORNEA_RIGHT", "Right Cornea", "Right cornea material."),
                        ("CORNEA_LEFT", "Left Cornea", "Left cornea material."),
                        ("EYE_RIGHT", "Right Eye", "Basic PBR right eye material."),
                        ("EYE_LEFT", "Left Eye", "Basic PBR left eye material."),
                        ("OCCLUSION_RIGHT", "Right Eye Occlusion", "Right eye occlusion material"),
                        ("OCCLUSION_LEFT", "Left Eye Occlusion", "Left eye occlusion material"),
                        ("TEARLINE_RIGHT", "Right Tearline", "Right tear line material"),
                        ("TEARLINE_LEFT", "Left Tearline", "Left tear line material"),
                    ]

OBJECT_TYPES = [
                        ("DEFAULT", "Default", "Default object type"),
                        ("BODY", "Body", "Base character body object"),
                        ("TEETH", "Teeth", "Teeth object"),
                        ("TONGUE", "Tongue", "Tongue object"),
                        ("HAIR", "Hair", "Hair object or object with hair"),
                        ("EYE", "Eye", "Eye object"),
                        ("OCCLUSION", "Eye Occlusion", "Eye occlusion object"),
                        ("TEARLINE", "Tearline", "Tear line object"),
                    ]

CHARACTER_GENERATION = {
    "RL_CC3_Plus": "G3Plus",
    "RL_CharacterCreator_Base_Game_G1_Divide_Eyelash_UV": "GameBase",
    "RL_CharacterCreator_Base_Game_G1_Multi_UV": "GameBase",
    "RL_CharacterCreator_Base_Game_G1_One_UV": "GameBase",
    "RL_CharacterCreator_Base_Std_G3": "G3",
    "RL_G6_Standard_Series": "G1",
    "NonStdLookAtDataCopyFromCCBase": "ActorCore",
}

NODE_PREFIX = "cc3iid_"

GRID_SIZE = 300

OCCLUSION_GROUP_INNER = "CC_EyeOcclusion_Inner"
OCCLUSION_GROUP_OUTER = "CC_EyeOcclusion_Outer"
OCCLUSION_GROUP_TOP = "CC_EyeOcclusion_Top"
OCCLUSION_GROUP_BOTTOM = "CC_EyeOcclusion_Bottom"
OCCLUSION_GROUP_ALL = "CC_EyeOcclusion_All"

TEARLINE_GROUP_INNER = "CC_Tearline_Inner"
TEARLINE_GROUP_ALL = "CC_Tearline_All"

block_property_update = False