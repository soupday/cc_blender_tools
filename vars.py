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

# Set by __init__.py from the bl_info dict

import bpy

VERSION_STRING = "v2.2.6"
DEV = False
#DEV = True
PLUGIN_COMPATIBLE = [
    "2.2.4",
    "2.2.5",
    "2.2.6",
]

def set_version_string(bl_info):
    global VERSION_STRING
    VERSION_STRING = "v"
    for i, v in enumerate(bl_info["version"]):
        if i > 0:
            VERSION_STRING += "."
        VERSION_STRING += str(v)

def prefs():
    return bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

def props():
    return bpy.context.scene.CC3ImportProps

def link_props():
    return bpy.context.scene.CCICLinkProps

def bake_props():
    return bpy.context.scene.CCICBakeProps

def get_context(context=None) -> bpy.types.Context:
    if not context:
        context = bpy.context
    return context

# blender uses metres, CC3 uses centimetres
UNIT_SCALE = 0.01
SKIN_SSS_RADIUS_SCALE = 0.01
DEFAULT_SSS_RADIUS_SCALE = 0.01
TEETH_SSS_RADIUS_SCALE = 0.01
TONGUE_SSS_RADIUS_SCALE = 0.01
HAIR_SSS_RADIUS_SCALE = 0.01
EYES_SSS_RADIUS_SCALE = 0.01 / 5.0
EMISSION_SCALE = 3.0
SSS_CYCLES_MOD = 1 #0.05

# https://docs.blender.org/manual/en/latest/files/media/image_formats.html
IMAGE_TYPES = [".bmp", ".sgi", ".rgb", ".bw", ".png", ".jpg", ".jpeg", ".jp2", ".j2c",
               ".tga", ".cin", ".dpx", ".exr", ".hdr", ".tif", ".tiff"]

# base names of all node groups in the library blend file
NODE_GROUPS = ["tiling_pivot_mapping", "tiling_mapping",
               "rl_tearline_shader", "rl_eye_occlusion_shader",
               "rl_skin_shader", "rl_head_shader",
               "rl_tongue_shader", "rl_teeth_shader",
               "rl_cornea_refractive_shader", "rl_eye_refractive_shader",
               "rl_cornea_parallax_shader", "tiling_cornea_parallax_mapping",
               "rl_pbr_shader", "rl_sss_shader",
               "rl_hair_shader", "rl_hair_cycles_shader",
               "rl_eye_occlusion_cycles_mix_shader", "rl_tearline_cycles_shader", "rl_tearline_cycles_mix_shader",
               "rl_rgb_mixer", "rl_id_mixer",
               "rl_tex_mod_normal_ao_blend",
               "rl_wrinkle_shader",
               "rl_bsdf_dual_specular",
               ]


ENUM_MATERIAL_TYPES = [
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

ENUM_OBJECT_TYPES = [
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
    "G3Plus": "G3Plus",
    "RL_CharacterCreator_Base_Game_G1_Divide_Eyelash_UV": "GameBase",
    "RL_CharacterCreator_Base_Game_G1_Multi_UV": "GameBase",
    "RL_CharacterCreator_Base_Game_G1_One_UV": "GameBase",
    "GameBase": "GameBase",
    "RL_CharacterCreator_Base_Std_G3": "G3",
    "G3": "G3",
    "RL_G6_Standard_Series": "G1",
    "G1": "G1",
    "NonStdLookAtDataCopyFromCCBase": "ActorCore",
    "ActorCore": "ActorCore",
    "ActorBuild": "ActorBuild",
    "ActorScan": "ActorScan",
    "AccuRig": "AccuRig",
    "Humanoid": "Humanoid",
    "Creature": "Creature",
    "Prop": "Prop",
    "NonStandardG3": "ActorBuild",
    "NonStandardGameBase": "GameBase",
    "NonStandardGeneric": "Unknown",
    "Generic": "Unknown",
    "NonStandard" : "Unknown",
}

# character generations considered standard humans and require FBX/OBJ keys to export
STANDARD_GENERATIONS = [
    "G3Plus", "G3",
]

PROP_GENERATIONS = [
    "Prop",
]

ENUM_TEX_LIST = [
        ("64","64 x 64","64 x 64 texture size"),
        ("128","128 x 128","128 x 128 texture size"),
        ("256","256 x 256","256 x 256 texture size"),
        ("512","512 x 512","512 x 512 texture size"),
        ("1024","1024 x 1024","1024 x 1024 texture size"),
        ("2048","2048 x 2048","2048 x 2048 texture size"),
        ("4096","4096 x 4096","4096 x 4096 texture size"),
        ("8192","8192 x 8192","8192 x 8192 texture size"),
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

ENUM_ARMATURE_TYPES = [
    ("NONE","Unknown","Unknown structure"),
    ("CC3","CC3","CC3, CC3+, iClone / ActorCore"),
    ("RIGIFY","Rigify","Rigify control rig structure"),
]

ENUM_ACTION_TYPES = [
    ("NONE","Unknown","Unknown action"),
    ("ARMATURE","Armature","Armature Action"),
    ("KEY","Shapekey","Shapekey Action"),
]

ACCESORY_PIVOT_NAME = "CC_Base_Pivot"


CC3_VISEME_NAMES = [
    "Open", "Explosive", "Dental_Lip", "Tight-O", "Tight", "Wide", "Affricate", "Lip_Open",
    "Tongue_up", "Tongue_Raise", "V_Tongue_Raise", "Tongue_Out", "Tongue_Narrow", "Tongue_Lower", "Tongue_Curl-U", "Tongue_Curl-D",
]

CC4_VISEME_NAMES = [
    "V_Open", "V_Explosive", "V_Dental_Lip", "V_Tight_O", "V_Tight", "V_Wide", "V_Affricate", "V_Lip_Open",
    "V_Tongue_up", "V_Tongue_Raise", "V_Tongue_Out", "V_Tongue_Narrow", "V_Tongue_Lower", "V_Tongue_Curl_U", "V_Tongue_Curl_D",
]

DIRECT_VISEME_NAMES = [
    "EE", "Er", "IH", "Ah", "Oh", "W_OO", "S_Z", "Ch_J", "F_V", "TH", "T_L_D_N", "B_M_P", "K_G_H_NG", "AE", "R",
]

# channel packing node names and id's
PACK_DIFFUSEROUGHNESS_NAME = "DR Pack"
PACK_DIFFUSEROUGHNESS_ID = "DR_PACK"
PACK_DIFFUSEROUGHNESSBLEND1_NAME = "DRB1 Pack"
PACK_DIFFUSEROUGHNESSBLEND1_ID = "DRB1_PACK"
PACK_DIFFUSEROUGHNESSBLEND2_NAME = "DRB1 Pack"
PACK_DIFFUSEROUGHNESSBLEND2_ID = "DRB1_PACK"
PACK_DIFFUSEROUGHNESSBLEND3_NAME = "DRB1 Pack"
PACK_DIFFUSEROUGHNESSBLEND3_ID = "DRB1_PACK"
PACK_WRINKLEROUGHNESS_NAME = "Roughness Pack"
PACK_WRINKLEROUGHNESS_ID = "ROUGHNESS_PACK"
PACK_WRINKLEFLOW_NAME = "Flow Pack"
PACK_WRINKLEFLOW_ID = "FLOW_PACK"
PACK_SSTM_NAME = "SSTM Pack"
PACK_SSTM_ID = "SSTM_PACK"
PACK_MICRODETAIL_NAME = "MICRODetail Pack"
PACK_MICRODETAIL_ID = "MICRODETAIL_PACK"
PACK_MSMNAO_NAME = "MSMNAO Pack"
PACK_MSMNAO_ID = "MSMNAO_PACK"
PACK_DIFFUSEALPHA_NAME = "DiffuseAlpha Pack"
PACK_DIFFUSEALPHA_ID = "DIFFUSEALPHA_PACK"
PACK_ROOTID_NAME = "RootID Pack"
PACK_ROOTID_ID = "ROOTID_PACK"
PACK_MRSO_NAME = "MRSO Pack"
PACK_MRSO_ID = "MRSO_PACK"
PACK_SSTMMNM_NAME = "SSTMMNM Pack"
PACK_SSTMMNM_ID = "SSTMMNM_PACK"


GAME_BASE_SKIN_NAMES = ["Ga_Skin_Arm", "Ga_Skin_Body", "Ga_Skin_Head", "Ga_Skin_Leg"]

#########################################################
# BAKE TOOL VARS

BAKE_PREFIX = "bakeutil_"

NO_SIZE = 64
DEFAULT_SIZE = 1024

BAKE_TARGETS = [
    ("NONE", "None", "Don't bake anything"),
    ("BLENDER","Blender", "Bake textures for Blender. The baked textures should be more performant than the complex node materials"),
    ("RL","Reallusion", "Bake textures for iClone / Character Creator"),
    ("SKETCHFAB","Sketchfab", "Bake and name the textures for Sketchfab. Uploading the baked textures with the .blend file to Sketchfab should auto connect the textures to the materials"),
    ("GLTF","GLTF", "Bake the relevant textures to be compatible with the GLTF exporter"),
    ("UNITY_HDRP","Unity HDRP","Bake and pack the textures for the Unity HDRP/Lit shader. Once baked only the BaseMap, Mask and Detail, Subsurface, Thickness and Emission textures are needed"),
    ("UNITY_URP","Unity 3D/URP","Bake the textures for Unity 3D Standard shader or for URP/Lit shader"),
    ("GODOT","Godot Engine","Bake the textures to be compatible with Godot Blender Exporter add-on"),
]

TARGET_FORMATS = [
    ("PNG","PNG", "Bake textures to PNG Format."),
    ("JPEG","JPEG", "Bake textures to JPEG Format."),
]

CONVERSION_FUNCTIONS = [
    ("IR","1 - R", "Inverted Roughness"),
    ("SIR","(1 - R)^2", "Squared Inverted Roughnes"),
    ("IRS","1 - R^2", "Inverted Roughness Squared"),
    ("IRSR","1 - sqrt(R)","Inverted Roughness Square Root"),
    ("SRIR","sqrt(1 - R)","Square Root of Inverted Roughness"),
    ("SRIRS","sqrt(1 - R^2)","Square Root of Inverted Roughness Squared"),
]

def get_bake_target_maps(target):
    if target == "SKETCHFAB":
        return SKETCHFAB_MAPS
    elif target == "GLTF":
        return GLTF_MAPS
    elif target == "UNITY_URP":
        return UNITY_URP_MAPS
    elif target == "UNITY_HDRP":
        return UNITY_HDRP_MAPS
    elif target == "RL":
        return RL_MAPS
    elif target == "GODOT":
        return GODOT_MAPS
    return BLENDER_MAPS

# global_suffix: ['target_suffix', 'prop_name']
RL_MAPS = {
    "Diffuse": ["Diffuse", "diffuse_size"],
    "AO": ["AO", "ao_size"],
    "Blend": ["BlendMultiply", "diffuse_size"],
    "Subsurface": ["SSS", "sss_size"],
    "Thickness": ["Transmission", "thickness_size"],
    "Metallic": ["Metallic", "metallic_size"],
    "Specular": ["Specular", "specular_size"],
    "Roughness": ["Roughness", "roughness_size"],
    "Emission": ["Emission", "emissive_size"],
    "Alpha": ["Alpha", "alpha_size"],
    "Normal": ["Normal", "normal_size"],
    "Bump": ["Bump", "bump_size"],
    "MicroNormal": ["MicroNormal", "micronormal_size"],
    "MicroNormalMask": ["MicroNormalMask", "micronormalmask_size"],
}

BLENDER_MAPS = {
    "Diffuse": ["Diffuse", "diffuse_size"],
    "Subsurface": ["Subsurface", "sss_size"],
    "Metallic": ["Metallic", "metallic_size"],
    "Specular": ["Specular", "specular_size"],
    "Roughness": ["Roughness", "roughness_size"],
    "Emission": ["Emission", "emissive_size"],
    "Alpha": ["Alpha", "alpha_size"],
    "Transmission": ["Transmission", "transmission_size"],
    "Normal": ["Normal", "normal_size"],
    "Bump": ["Bump", "bump_size"],
    "MicroNormal": ["MicroNormal", "micronormal_size"],
    "MicroNormalMask": ["MicroNormalMask", "micronormalmask_size"],
}

GODOT_MAPS = {
    "Diffuse": ["Diffuse", "diffuse_size"],
    "Subsurface": ["Subsurface", "sss_size"],
    "Metallic": ["Metallic", "metallic_size"],
    "Specular": ["Specular", "specular_size"],
    "Roughness": ["Roughness", "roughness_size"],
    "Emission": ["Emission", "emissive_size"],
    "Alpha": ["Alpha", "alpha_size"],
    "Transmission": ["Transmission", "transmission_size"],
    "Normal": ["Normal", "normal_size"],
    "Bump": ["Bump", "bump_size"],
}

SKETCHFAB_MAPS = {
    "Diffuse": ["diffuse", "diffuse_size"],
    "AO": ["ao", "ao_size"],
    "Subsurface": ["subsurface", "sss_size"],
    "Thickness": ["thickness", "thickness_size"],
    "Metallic": ["metallic", "metallic_size"],
    "Specular": ["specularf0", "specular_size"],
    "Roughness": ["roughness", "roughness_size"],
    "Emission": ["emission", "emissive_size"],
    "Alpha": ["opacity", "alpha_size"],
    "Normal": ["normal", "normal_size"],
    "Bump": ["bump", "bump_size"],
}

GLTF_MAPS = {
    "Diffuse": ["baseColor", "basemap_size"],
    "AO": ["occlusion", "gltf_size"],
    "Metallic": ["metallic", "gltf_size"],
    "Roughness": ["roughness", "gltf_size"],
    "Emission": ["emission", "emissive_size"],
    "Alpha": ["alpha", "basemap_size"],
    "Normal": ["normal", "normal_size"],
    # packed maps
    "BaseMap": ["baseMap", "basemap_size"],
    "GLTF": ["glTF", "gltf_size"],
}

UNITY_URP_MAPS = {
    "Diffuse": ["Diffuse", "basemap_size"],
    "AO": ["Occlusion", "ao_size"],
    "Metallic": ["Metallic", "metallic_alpha_size"],
    "Roughness": ["Roughness", "metallic_alpha_size"],
    "Emission": ["Emission", "emission_size"],
    "Alpha": ["Opacity", "basemap_size"],
    "Normal": ["Normal", "normal_size"],
    "Bump": ["bump", "bump_size"],
    "MicroNormal": ["Mask", "micronormalmask_size"],
    "MicroNormalMask": ["Detail", "detail_size"],
    # packed maps
    "BaseMap": ["BaseMap", "basemap_size"],
    "MetallicAlpha": ["MetallicAlpha", "metallic_alpha_size"],
}

UNITY_HDRP_MAPS = {
    "Diffuse": ["Diffuse", "basemap_size"],
    "AO": ["Occlusion", "mask_size"],
    "Subsurface": ["Subsurface", "sss_size"],
    "Thickness": ["Thickness", "thickness_size"],
    "Metallic": ["Metallic", "mask_size"],
    "Roughness": ["Roughness", "mask_size"],
    "Emission": ["Emission", "emission_size"],
    "Alpha": ["Opacity", "basemap_size"],
    "Normal": ["Normal", "normal_size"],
    "Bump": ["bump", "bump_size"],
    "MicroNormal": ["MicroNormal", "detail_size"],
    "MicroNormalMask": ["MicroNormalMask", "mask_size"],
    # packed maps
    "BaseMap": ["BaseMap", "basemap_size"],
    "Mask": ["Mask", "mask_size"],
    "Detail": ["Detail", "detail_size"],
}


TEX_LIST = [
        ("64","64 x 64","64 x 64 texture size"),
        ("128","128 x 128","128 x 128 texture size"),
        ("256","256 x 256","256 x 256 texture size"),
        ("512","512 x 512","512 x 512 texture size"),
        ("1024","1024 x 1024","1024 x 1024 texture size"),
        ("2048","2048 x 2048","2048 x 2048 texture size"),
        ("4096","4096 x 4096","4096 x 4096 texture size"),
        ("8192","8192 x 8192","8192 x 8192 texture size"),
    ]


TEX_SIZE_DETECT = {
    "diffuse_size": [
        ["DIFFUSE"], ["Base Color:DIFFUSE"]
    ],

    "ao_size": [
        ["AO"], ["Base Color:AO"]
    ],

    "blend_size": [
        ["BLEND1"], ["Base Color:BLEND"]
    ],

    "sss_size": [
        ["SSS"], None
    ],

    "thickness_size": [
        ["TRANSMISSION"], None
    ],

    "transmission_size": [
        ["TRANSMISSION_OVERRIDE"], ["Transmission"]
        # note: there is no '_TRANSMISSION_B', it's just a key to override the
        # transmission texture size in the TEX_SIZE_OVERRIDE list...
    ],

    "specular_size": [
        ["SPECULAR", "SPECMASK"], ["Specular"]
    ],

    "metallic_size": [
        ["METALLIC"], ["Metallic"]
    ],

    "roughness_size": [
        ["ROUGHNESS"], ["Roughness"]
    ],

    "smoothness_size": [
        ["ROUGHNESS"], ["Roughness"]
    ],

    "emission_size": [
        ["EMISSION"], ["Emission"]
    ],

    "alpha_size": [
        ["ALPHA"], ["Alpha"]
    ],

    "normal_size": [
        ["NORMAL", "NORMALBLEND", "SCLERANORMAL"], ["Normal:NORMAL"]
    ],

    "bump_size": [
        ["BUMP"], ["Normal:BUMP"]
    ],

    "detail_size": [
        ["MICRONORMAL"], None
    ],

    "micronormalmask_size": [
        ["MICRONMASK"], None
    ],

    "micronormal_size": [
        ["MICRONORMAL"], None
    ],

    "mask_size": [
        ["ROUGHNESS", "AO", "METALLIC", "MICRONMASK"],
        ["Base Color:AO", "Roughness", "Metallic"]
    ],

    "metallic_alpha_size": [
        ["ROUGHNESS", "METALLIC"],
        ["Roughness", "Metallic"]
    ],

    "gltf_size": [
        ["AO", "ROUGHNESS", "METALLIC"],
        ["Base Color:AO", "Roughness", "Metallic"]
    ],

    "basemap_size": [
        ["DIFFUSE", "ALPHA"],
        ["Base Color:DIFFUSE", "Alpha"]
    ],
}


# override the texture size for procedurally generated maps
TEX_SIZE_OVERRIDE = {
    "CORNEA_LEFT": {
        "ROUGHNESS": 256,
        "SSS": 256,
        "SPECULAR": 256,
        "ALPHA": 256,
        "TRANSMISSION_OVERRIDE": 256,
    },

    "CORNEA_RIGHT": {
        "ROUGHNESS": 256,
        "SSS": 256,
        "SPECULAR": 256,
        "ALPHA": 256,
        "TRANSMISSION_OVERRIDE": 256,
    },

    "EYE_LEFT": {
        "ROUGHNESS": 256,
        "SSS": 256,
        "SPECULAR": 256,
    },

    "EYE_RIGHT": {
        "ROUGHNESS": 256,
        "SSS": 256,
        "SPECULAR": 256,
    },

    "OCCLUSION_LEFT": {
        "ALPHA": 256,
    },

    "OCCLUSION_RIGHT": {
        "ALPHA": 256,
    },

    "HAIR": {
        "BUMP": 2048,
    },

    "SMART_HAIR": {
        "BUMP": 2048,
    },

    "SCALP": {
        "BUMP": 2048,
    },
}

SPRING_IK_LAYER = 19
SPRING_FK_LAYER = 20
SPRING_TWEAK_LAYER = 21
ORG_BONE_LAYER = 31
MCH_BONE_LAYER = 30
DEF_BONE_LAYER = 29
ROOT_BONE_LAYER = 28
SIM_BONE_LAYER = 27
HIDE_BONE_LAYER = 23
SPRING_EDIT_LAYER = 25
SPRING_ROOT_LAYER = 24

block_property_update = False