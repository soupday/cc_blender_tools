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

# lists of the suffixes used by the input maps
BASE_COLOR_MAP = ["diffuse", "albedo"]
SUBSURFACE_MAP = ["sssmap", "sss"]
METALLIC_MAP = ["metallic"]
SPECULAR_MAP = ["specular"]
ROUGHNESS_MAP = ["roughness"]
EMISSION_MAP = ["glow", "emission"]
ALPHA_MAP = ["opacity", "alpha"]
NORMAL_MAP = ["normal"]
BUMP_MAP = ["bump", "height"]
SCLERA_MAP = ["sclera"]
SCLERA_NORMAL_MAP = ["scleran", "scleranormal"]
IRIS_NORMAL_MAP = ["irisn", "irisnormal"]
MOUTH_GRADIENT_MAP = ["gradao", "gradientao"]
TEETH_GUMS_MAP = ["gumsmask"]
WEIGHT_MAP = ["weightmap"]

# lists of the suffixes used by the modifier maps
# (not connected directly to input but modify base inputs)
MOD_AO_MAP = ["ao", "ambientocclusion", "ambient occlusion"]
MOD_BASECOLORBLEND_MAP = ["bcbmap", "basecolorblend2"]
MOD_MCMAO_MAP = ["mnaomask", "mouthcavitymaskandao"]
MOD_SPECMASK_MAP = ["specmask", "hspecmap", "specularmask", "hairspecularmaskmap"]
MOD_TRANSMISSION_MAP = ["transmap", "transmissionmap"]
MOD_NORMALBLEND_MAP = ["nbmap", "normalmapblend"]
MOD_MICRONORMAL_MAP = ["micron", "micronormal"]
MOD_MICRONORMALMASK_MAP = ["micronmask", "micronormalmask"]
MOD_HAIR_BLEND_MULTIPLY = ["blend_multiply"]
MOD_HAIR_FLOW_MAP = ["hair flow map"]
MOD_HAIR_ID_MAP = ["hair id map"]
MOD_HAIR_ROOT_MAP = ["hair root map"]
MOD_HAIR_VERTEX_COLOR_MAP = ["vertexcolormap"]
MOD_RGBA_MAP = ["rgbamask"]
MOD_NMUIL_MAP = ["nmuilmask"]
MOD_CFULC_MAP = ["cfulcmask"]
MOD_EN_MAP = ["enmask"]

# blender uses metres, CC3 uses centimetres
UNIT_SCALE = 0.01

# https://docs.blender.org/manual/en/latest/files/media/image_formats.html
IMAGE_TYPES = [".bmp", ".sgi", ".rgb", ".bw", ".png", ".jpg", ".jpeg", ".jp2", ".j2c",
               ".tga", ".cin", ".dpx", ".exr", ".hdr", ".tif", ".tiff"]

# base names of all node groups in the library blend file
NODE_GROUPS = ["color_ao_mixer", "color_blend_ao_mixer", "color_refractive_eye_mixer", "color_eye_mixer", "color_teeth_mixer", "color_tongue_mixer", "color_head_mixer",
               "color_hair_mixer", "subsurface_mixer", "subsurface_overlay_mixer",
               "msr_mixer", "msr_skin_mixer", "msr_overlay_mixer",
               "normal_micro_mask_blend_mixer", "normal_micro_mask_mixer", "bump_mixer", "fake_bump_mixer",
               "normal_refractive_cornea_mixer", "normal_refractive_eye_mixer",
               "eye_occlusion_mask", "iris_refractive_mask", "iris_mask", "tiling_pivot_mapping", "tiling_mapping",
               "rl_eye_occlusion_shader"]


MATERIAL_TYPES = [
                        ("DEFAULT", "Default", "Default material"),
                        ("SKIN_HEAD", "Head", "Head skin material"),
                        ("SKIN_BODY", "Body", "Body skin material"),
                        ("SKIN_ARM", "Arm", "Arm skin material"),
                        ("SKIN_LEG", "Leg", "Leg skin material"),
                        ("TEETH_UPPER", "Upper Teeth", "Upper teeth material"),
                        ("TEETH_LOWER", "Lower Teeth", "Lower teeth material"),
                        ("TONGUE", "Tongue", "Tongue material"),
                        ("HAIR", "Hair", "Hair material"),
                        ("SMART_HAIR", "Smart Hair", "Smart Hair material"),
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

NODE_PREFIX = "cc3iid_"

GRID_SIZE = 300

OCCLUSION_GROUP_INNER = "CC_EyeOcclusion_Inner"
OCCLUSION_GROUP_OUTER = "CC_EyeOcclusion_Outer"
OCCLUSION_GROUP_TOP = "CC_EyeOcclusion_Top"
OCCLUSION_GROUP_BOTTOM = "CC_EyeOcclusion_Bottom"
OCCLUSION_GROUP_ALL = "CC_EyeOcclusion_All"

TEARLINE_GROUP_INNER = "CC_Tearline_Inner"
TEARLINE_GROUP_ALL = "CC_Tearline_All"