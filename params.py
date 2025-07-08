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

# [system_id, json_id, is_srgb, suffix_list, <library_file_name>]
TEXTURE_TYPES = [
    # pbr textures
    ["DIFFUSE", "Base Color", True, ["diffuse", "albedo"]],
    ["AO", "AO", False, ["ao", "ambientocclusion", "ambient occlusion"]],
    ["BLEND1", "Blend", False, ["blend_multiply"]],
    ["SPECULAR", "Specular", False, ["specular"]],
    ["METALLIC", "Metallic", False, ["metallic"]],
    ["ROUGHNESS", "Roughness", False, ["roughness"]],
    ["EMISSION", "Glow", True, ["glow", "emission"]],
    ["ALPHA", "Opacity", False, ["opacity", "alpha"]],
    ["NORMAL", "Normal", False, ["normal"]],
    ["BUMP", "Bump", False, ["bump", "height", "resourcemap_height"]],
    ["DISPLACE", "Displacement", False, ["displacement"]],
    # custom shader textures
    ["SSS", "SSS Map", False, ["sssmap", "sss"]],
    ["TRANSMISSION", "Transmission Map", False, ["transmap", "transmissionmap"]],
    ["BLEND2", "BaseColor Blend2", False, ["bcbmap", "basecolorblend2"]],
    ["SPECMASK", "Specular Mask", False, ["specmask", "hspecmap", "specularmask", "hairspecularmaskmap"]],
    ["NORMALBLEND", "NormalMap Blend", False, ["nbmap", "normalmapblend"]],
    ["MICRONORMAL", "MicroNormal", False, ["micron", "micronormal"]],
    ["MICRONMASK", "MicroNormalMask", False, ["micronmask", "micronormalmask"]],
    ["MCMAOMASK", "Mouth Cavity Mask and AO", False, ["mnaomask", "mouthcavitymaskandao"]],
    ["GRADIENTAO", "Gradient AO", False, ["gradao", "gradientao"]],
    ["GUMSMASK", "Gums Mask", False, ["gumsmask"]],
    ["RGBAMASK", "RGBA Area Mask", False, ["rgbamask"]],
    ["NMUILMASK", "Nose Mouth UpperInnerLid Mask", False, ["nmuilmask"]],
    ["CFULCMASK", "Cheek Fore UpperLip Chin Mask", False, ["cfulcmask"]],
    ["ENNASK", "Ear Neck Mask", False, ["enmask"]],
    ["IRISNORMAL", "Iris Normal", False, ["irisn", "irisnormal"]],
    ["SCLERANORMAL", "Sclera Normal", False, ["scleran", "scleranormal"]],
    ["EYEBLEND", "EyeBlendMap2", False, ["bcbmap", "basecolorblend2"]],
    ["INNERIRISMASK", "Inner Iris Mask", False, ["irismask"]],
    ["SCLERA", "Sclera", True, ["sclera"]],
    ["HAIRROOT", "Hair Root Map", False, ["hair root map"]],
    ["HAIRID", "Hair ID Map", False, ["hair id map"]],
    ["HAIRFLOW", "Hair Flow Map", False, ["hair flow map"]],
    ["HAIRVERTEXCOLOR", "", False, ["vertexcolormap"]],
    ["CAVITY", "Cavity Map", False, ["cavitymap"]],
    # physics textures
    ["WEIGHTMAP", "Weight Map", True, ["weightmap"]],
    # mixer mask textures
    ["COLORID", "ColorID", False, ["colorid"]],
    ["RGBMASK", "RGBMask", False, ["rgbmask"]],
    # wrinkle maps
    ["WRINKLEDIFFUSE1", "Diffuse_1", True, ["wrinkle_diffuse1"]],
    ["WRINKLEDIFFUSE2", "Diffuse_2", True, ["wrinkle_diffuse2"]],
    ["WRINKLEDIFFUSE3", "Diffuse_3", True, ["wrinkle_diffuse3"]],
    ["WRINKLEROUGHNESS1", "Roughness_1", False, ["wrinkle_roughness1"]],
    ["WRINKLEROUGHNESS2", "Roughness_2", False, ["wrinkle_roughness2"]],
    ["WRINKLEROUGHNESS3", "Roughness_3", False, ["wrinkle_roughness3"]],
    ["WRINKLENORMAL1", "Normal_1", False, ["wrinkle_normal1"]],
    ["WRINKLENORMAL2", "Normal_2", False, ["wrinkle_normal2"]],
    ["WRINKLENORMAL3", "Normal_3", False, ["wrinkle_normal3"]],
    ["WRINKLEFLOW1", "Flow_1", False, ["wrinkle_flow1"]],
    ["WRINKLEFLOW2", "Flow_2", False, ["wrinkle_flow2"]],
    ["WRINKLEFLOW3", "Flow_3", False, ["wrinkle_flow3"]],
    ["WRINKLEMASK1A", "", False, [], "RL_WrinkleMask_Set1A"],
    ["WRINKLEMASK1B", "", False, [], "RL_WrinkleMask_Set1B"],
    ["WRINKLEMASK2", "", False, [], "RL_WrinkleMask_Set2"],
    ["WRINKLEMASK3", "", False, [], "RL_WrinkleMask_Set3"],
    ["WRINKLEMASK123", "", False, [], "RL_WrinkleMask_Set123"],
    ["WRINKLEDISPLACEMENT1", "Wrinkle Dis 1", False, ["resourcemap_wrinkle dis 1"]],
    ["WRINKLEDISPLACEMENT2", "Wrinkle Dis 2", False, ["resourcemap_wrinkle dis 2"]],
    ["WRINKLEDISPLACEMENT3", "Wrinkle Dis 3", False, ["resourcemap_wrinkle dis 3"]],
    # dual specular skin micro cavity mask
    ["SKINSPECDETAIL", "", False, [], "RL_SkinSpecDetail"],
    #["SKINSPECDETAIL", "", False, [], "RL_SkinMicroCavityMap"],
]

TEXTURE_RULES = {
    "SKINSPECDETAIL": "prefs.build_skin_shader_dual_spec",
}

PBR_TYPES = [
    "DIFFUSE", "AO", "BLEND1", "SPECULAR", "METALLIC", "ROUGHNESS",
    "EMISSION", "ALPHA", "NORMAL", "BUMP", "DISPLACE"
]

# when updating linked materials, attempt to update the properties in all the material types in the same list:
LINKED_MATERIALS = [
    ["SKIN_HEAD", "SKIN_BODY", "SKIN_ARM", "SKIN_LEG"],
    ["EYE_RIGHT", "CORNEA_RIGHT", "EYE_LEFT", "CORNEA_LEFT"],
    ["OCCLUSION_RIGHT", "OCCLUSION_LEFT"],
    ["OCCLUSION_PLUS_RIGHT", "OCCLUSION_PLUS_LEFT"],
    ["TEARLINE_RIGHT", "TEARLINE_LEFT"],
    ["TEARLINE_PLUS_RIGHT", "TEARLINE_PLUS_LEFT"],
    ["TEETH_UPPER", "TEETH_LOWER"],
    ["HAIR"],
    ["SCALP"],
]

# These material types must be updated together as they share the same properties:
PAIRED_MATERIALS = [
    ["EYE_RIGHT", "CORNEA_RIGHT"],
    ["EYE_LEFT", "CORNEA_LEFT"],
]

LINKED_MATERIAL_NAMES = [
    ["Ga_Skin_Arm", "Ga_Skin_Body", "Ga_Skin_Head", "Ga_Skin_Leg"],
    ["Std_Eye_R", "Std_Eye_L"],
    ["Std_Cornea_R", "Std_Cornea_L"],
]

# shader definitions
SHADER_MATRIX = [

    # Tearline Shader
    #######################################

    {   "name": "rl_tearline_shader",
        "rl_shader": "RLEyeTearline",
        "label": "Tearline",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Specular", "", "tearline_specular"],
            ["Glossiness", "", "tearline_glossiness"],
            ["Alpha", "", "tearline_alpha"],
            ["Roughness", "", "tearline_roughness"],
        ],
        # modifier properties:
        # [prop_name, material_type, modifier_type, modifier_id, expression]
        "modifiers": [
            ["tearline_displace", "TEARLINE_RIGHT", "DISPLACE", "Tearline_Displace_All_R", "mod.strength = -parameters.tearline_displace"],
            ["tearline_inner", "TEARLINE_RIGHT", "DISPLACE", "Tearline_Displace_Inner_R", "mod.strength = -parameters.tearline_inner"],
            ["tearline_displace", "TEARLINE_LEFT", "DISPLACE", "Tearline_Displace_All_L", "mod.strength = -parameters.tearline_displace"],
            ["tearline_inner", "TEARLINE_LEFT", "DISPLACE", "Tearline_Displace_Inner_L", "mod.strength = -parameters.tearline_inner"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["tearline_alpha", 0.05, "DEF"],
            ["tearline_specular", 1, "DEF"],
            ["tearline_glossiness", 0.85, "DEF"],
            ["tearline_roughness", 0.15, "", "Custom/_Roughness"],
            ["tearline_inner", 0, "DEF"],
            ["tearline_displace", 0.1, "", "Custom/Depth Offset"],
        ],
        # export variables to update json file on export that require special functions to convert
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Tearline", "MATFLUID"],
            ["PROP", "*Glossiness", "tearline_glossiness", True, "#CYCLES"],
            ["PROP", "*Specular", "tearline_specular", True, "#EEVEE"],
            ["PROP", "Roughness", "tearline_roughness", True],
            ["PROP", "*Alpha", "tearline_alpha", True, "#EEVEE"],
            ["SPACER"],
            ["PROP", "Displace", "tearline_displace", True],
            ["PROP", "*Inner Displace", "tearline_inner", True],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Two Side": True,
            "Diffuse Color": [ 255.0, 255.0, 255.0 ],
            "Ambient Color": [ 0.0, 0.0, 0.0 ],
            "Specular Color": [ 0.0, 0.0, 0.0 ],
            "Opacity": 1.0,
            "Self Illumination": 0.0,
            "Textures": {},
            "Custom Shader": {
                "Shader Name": "RLEyeTearline",
                "Image": {},
                "Variable": {},
            }
        },
    },

    {   "name": "rl_tearline_plus_shader",
        "rl_shader": "RLEyeTearline_Plus",
        "label": "Tearline Plus",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Specular", "", "tearline_specular"],
            ["IOR", "", "tearline_ior"],
            ["Alpha", "", "tearline_alpha"],
            ["Roughness", "func_half", "tearline_roughness"],
            ["Depth", "", "tearline_displace"],
            ["Detail", "", "tearline_detail"],
            ["U Tiling", "", "tearline_tiling_u"],
            ["V Tiling", "", "tearline_tiling_v"],
            ["Micro Normal Strength", "", "tearline_normal_strength"],
            ["Micro Normal Scale", "", "tearline_normal_scale"],
            ["Edge Fadeout", "", "tearline_edge_fadeout"],
        ],
        # modifier properties:
        # [prop_name, material_type, modifier_type, modifier_id, expression]
        "modifiers": [
            ["tearline_displace", "TEARLINE_PLUS_RIGHT", "DISPLACE", "Tearline_Displace_All_R", "mod.strength = -parameters.tearline_displace"],
            ["tearline_inner", "TEARLINE_PLUS_RIGHT", "DISPLACE", "Tearline_Displace_Inner_R", "mod.strength = -parameters.tearline_inner"],
            ["tearline_displace", "TEARLINE_PLUS_LEFT", "DISPLACE", "Tearline_Displace_All_L", "mod.strength = -parameters.tearline_displace"],
            ["tearline_inner", "TEARLINE_PLUS_LEFT", "DISPLACE", "Tearline_Displace_Inner_L", "mod.strength = -parameters.tearline_inner"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["tearline_alpha", 0.4, "func_mul_10", "Custom/_Opacity"],
            ["tearline_specular", 2.0, "DEF"],
            ["tearline_ior", 2.0, "DEF"],
            ["tearline_roughness", 0.15, "", "Custom/_Roughness"],
            ["tearline_inner", 0, "DEF"],
            ["tearline_displace", 0.05, "", "Custom/Depth Offset"],
            ["tearline_detail", 0, "", "Custom/Detail Amount"],
            ["tearline_tiling_u", 0, "", "Custom/Detail U Tiling"],
            ["tearline_tiling_v", 0, "", "Custom/Detail V Tiling"],
            ["tearline_normal_strength", 0, "", "Custom/Micro Normal Strength"],
            ["tearline_normal_scale", 0, "", "Custom/Micro Normal Scale"],
            ["tearline_edge_fadeout", 0, "", "Custom/Edge Fadeout"],
        ],
        # export variables to update json file on export that require special functions to convert
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["Custom/_Opacity", 0.04, "func_divide_10", "tearline_alpha"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Tearline", "MATFLUID"],
            ["PROP", "*IOR", "tearline_ior", True],
            ["PROP", "*Specular", "tearline_specular", True],
            ["PROP", "Roughness", "tearline_roughness", True],
            ["PROP", "*Alpha", "tearline_alpha", True],
            ["PROP", "Edge Fadeout", "tearline_edge_fadeout", True],
            ["HEADER",  "Normals", "MATFLUID"],
            ["PROP", "Details", "tearline_detail", True],
            ["PAIR", "Tiling", "tearline_tiling_u", "tearline_tiling_v", True],
            ["PROP", "Strength", "tearline_normal_strength", True],
            ["PROP", "Scale", "tearline_normal_scale", True],
            ["SPACER"],
            ["PROP", "Displace", "tearline_displace", True],
            ["PROP", "*Inner Displace", "tearline_inner", True],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Two Side": True,
            "Diffuse Color": [ 255.0, 255.0, 255.0 ],
            "Ambient Color": [ 0.0, 0.0, 0.0 ],
            "Specular Color": [ 0.0, 0.0, 0.0 ],
            "Opacity": 1.0,
            "Self Illumination": 0.0,
            "Textures": {},
            "Custom Shader": {
                "Shader Name": "RLEyeTearline_Plus",
                "Image": {},
                "Variable": {},
            }
        },
    },

    # Eye Occlusion Shader
    #########################################

    {   "name": "rl_eye_occlusion_shader",
        "rl_shader": "RLEyeOcclusion",
        "label": "Eye Occlusion",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Color", "func_occlusion_color", "eye_occlusion_color"],
            ["Strength", "func_occlusion_strength", "eye_occlusion_strength"],
            ["Strength2", "func_occlusion_strength", "eye_occlusion_strength2"],
            ["Power", "", "eye_occlusion_power"],
            ["Top Min", "", "eye_occlusion_top_min"],
            ["Top Max", "func_occlusion_range", "eye_occlusion_top_range", "eye_occlusion_top_min"],
            ["Top Curve", "", "eye_occlusion_top_curve"],
            ["Bottom Min", "", "eye_occlusion_bottom_min"],
            ["Bottom Max", "func_occlusion_range", "eye_occlusion_bottom_range", "eye_occlusion_bottom_min"],
            ["Bottom Curve", "", "eye_occlusion_bottom_curve"],
            ["Inner Min", "", "eye_occlusion_inner_min"],
            ["Inner Max", "func_occlusion_range", "eye_occlusion_inner_range", "eye_occlusion_inner_min"],
            ["Outer Min", "", "eye_occlusion_outer_min"],
            ["Outer Max", "func_occlusion_range", "eye_occlusion_outer_range", "eye_occlusion_outer_min"],
            ["Top2 Min", "", "eye_occlusion_top2_min"],
            ["Top2 Max", "func_occlusion_range", "eye_occlusion_top2_range", "eye_occlusion_top2_min"],
            ["Tear Duct Position", "", "eye_occlusion_tear_duct_position"],
            ["Tear Duct Width", "", "eye_occlusion_tear_duct_width"],
        ],
        # modifier properties:
        # [prop_name, material_type, modifier_type, modifier_id, expression]
        "modifiers": [
            [ "eye_occlusion_displace", "OCCLUSION_RIGHT", "DISPLACE", "Occlusion_Displace_All_R", "mod.strength = parameters.eye_occlusion_displace"],
            [ "eye_occlusion_inner", "OCCLUSION_RIGHT", "DISPLACE", "Occlusion_Displace_Inner_R", "mod.strength = parameters.eye_occlusion_inner"],
            [ "eye_occlusion_outer", "OCCLUSION_RIGHT", "DISPLACE", "Occlusion_Displace_Outer_R", "mod.strength = parameters.eye_occlusion_outer"],
            [ "eye_occlusion_top", "OCCLUSION_RIGHT", "DISPLACE", "Occlusion_Displace_Top_R", "mod.strength = parameters.eye_occlusion_top"],
            [ "eye_occlusion_bottom", "OCCLUSION_RIGHT", "DISPLACE", "Occlusion_Displace_Bottom_R", "mod.strength = parameters.eye_occlusion_bottom"],
            [ "eye_occlusion_displace", "OCCLUSION_LEFT", "DISPLACE", "Occlusion_Displace_All_L", "mod.strength = parameters.eye_occlusion_displace"],
            [ "eye_occlusion_inner", "OCCLUSION_LEFT", "DISPLACE", "Occlusion_Displace_Inner_L", "mod.strength = parameters.eye_occlusion_inner"],
            [ "eye_occlusion_outer", "OCCLUSION_LEFT", "DISPLACE", "Occlusion_Displace_Outer_L", "mod.strength = parameters.eye_occlusion_outer"],
            [ "eye_occlusion_top", "OCCLUSION_LEFT", "DISPLACE", "Occlusion_Displace_Top_L", "mod.strength = parameters.eye_occlusion_top"],
            [ "eye_occlusion_bottom", "OCCLUSION_LEFT", "DISPLACE", "Occlusion_Displace_Bottom_L", "mod.strength = parameters.eye_occlusion_bottom"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["eye_occlusion_tear_duct_position", 0.8, "", "Custom/Tear Duct Position"],
            ["eye_occlusion_color", (0.014451, 0.001628, 0.000837, 1.0), "func_color_bytes_linear", "Custom/Shadow Color"],
            ["eye_occlusion_strength", 0.2, "", "Custom/Shadow Strength"],
            ["eye_occlusion_top_min", 0.27, "", "Custom/Shadow Top"],
            ["eye_occlusion_top_range", 1, "", "Custom/Shadow Top Range"],
            ["eye_occlusion_top_curve", 0.7, "", "Custom/Shadow Top Arc"],
            ["eye_occlusion_bottom_min", 0.05, "", "Custom/Shadow Bottom"],
            ["eye_occlusion_bottom_range", 0.335, "", "Custom/Shadow Bottom Range"],
            ["eye_occlusion_bottom_curve", 2.0, "", "Custom/Shadow Bottom Arc"],
            ["eye_occlusion_inner_min", 0.25, "", "Custom/Shadow Inner Corner"],
            ["eye_occlusion_inner_range", 0.625, "", "Custom/Shadow Inner Corner Range"],
            ["eye_occlusion_outer_min", 0.2, "", "Custom/Shadow Outer Corner"],
            ["eye_occlusion_outer_range", 0.6, "", "Custom/Shadow Outer Corner Range"],
            ["eye_occlusion_strength2", 0.4, "", "Custom/Shadow2 Strength"],
            ["eye_occlusion_top2_min", 0.15, "", "Custom/Shadow2 Top"],
            ["eye_occlusion_top2_range", 1, "", "Custom/Shadow2 Top Range"],
            ["eye_occlusion_displace", 0.02, "func_divide_100", "Custom/Depth Offset"],
            ["eye_occlusion_top", 0, "", "Custom/Top Offset"],
            ["eye_occlusion_bottom", 0, "", "Custom/Bottom Offset"],
            ["eye_occlusion_inner", 0, "", "Custom/Inner Corner Offset"],
            ["eye_occlusion_outer", 0.07, "", "Custom/Outer Corner Offset"],
            # non json properties (just defaults)
            ["eye_occlusion_tear_duct_width", 0.5, "DEF"],
            ["eye_occlusion_power", 4, "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["Custom/Shadow Color", [255.0, 255.0, 255.0], "func_export_byte3_linear", "eye_occlusion_color"],
            ["Custom/Depth Offset", 0.02, "func_mul_100", "eye_occlusion_displace"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "Color", "eye_occlusion_color", False],
            ["HEADER",  "Opacity", "MOD_OPACITY"],
            ["PROP", "*Hardness", "eye_occlusion_power", True, "#EEVEE"],
            ["PROP", "Strength", "eye_occlusion_strength", True, "#EEVEE"],
            ["PROP", "Top", "eye_occlusion_top_min", True, "#EEVEE"],
            ["PROP", "Top Range", "eye_occlusion_top_range", True, "#EEVEE"],
            ["PROP", "Top Curve", "eye_occlusion_top_curve", True, "#EEVEE"],
            ["PROP", "Bottom", "eye_occlusion_bottom_min", True, "#EEVEE"],
            ["PROP", "Bottom Range", "eye_occlusion_bottom_range", True, "#EEVEE"],
            ["PROP", "Bottom Curve", "eye_occlusion_bottom_curve", True, "#EEVEE"],
            ["PROP", "Inner", "eye_occlusion_inner_min", True, "#EEVEE"],
            ["PROP", "Inner Range", "eye_occlusion_inner_range", True, "#EEVEE"],
            ["PROP", "Outer", "eye_occlusion_outer_min", True, "#EEVEE"],
            ["PROP", "Outer Range", "eye_occlusion_outer_range", True, "#EEVEE"],
            ["SPACER"],
            ["PROP", "2nd Strength", "eye_occlusion_strength2", True, "#EEVEE"],
            ["PROP", "2nd Top", "eye_occlusion_top2_min", True, "#EEVEE"],
            ["PROP", "2nd Top Range", "eye_occlusion_top2_range", True, "#EEVEE"],
            ["SPACER"],
            ["PROP", "Tear Duct Position", "eye_occlusion_tear_duct_position", True, "#EEVEE"],
            ["PROP", "*Tear Duct Width", "eye_occlusion_tear_duct_width", True, "#EEVEE"],
            ["HEADER",  "Displacement", "MOD_DISPLACE"],
            ["PROP", "Displace", "eye_occlusion_displace", True],
            ["PROP", "Top", "eye_occlusion_top", True],
            ["PROP", "Bototm", "eye_occlusion_bottom", True],
            ["PROP", "Inner", "eye_occlusion_inner", True],
            ["PROP", "Outer", "eye_occlusion_outer", True],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Two Side": True,
            "Diffuse Color": [ 255.0, 255.0, 255.0 ],
            "Ambient Color": [ 0.0, 0.0, 0.0 ],
            "Specular Color": [ 0.0, 0.0, 0.0 ],
            "Opacity": 1.0,
            "Self Illumination": 0.0,
            "Textures": {},
            "Custom Shader": {
                "Shader Name": "RLEyeOcclusion",
                "Image": {},
                "Variable": {},
            }
        },
    },

    # Eye Occlusion Plus Shader
    #########################################

    {   "name": "rl_eye_occlusion_plus_shader",
        "rl_shader": "RLEyeOcclusion_Plus",
        "label": "Eye Occlusion Plus",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Shadow Color", "func_occlusion_color", "eye_occlusion_color"],
            ["Shadow Strength", "", "eye_occlusion_strength"],
            ["Shadow Top Min", "", "eye_occlusion_top_min"],
            ["Shadow Top Max", "", "eye_occlusion_top_max"],
            ["Shadow Top Min Contrast", "", "eye_occlusion_top_in"],
            ["Shadow Top Max Contrast", "", "eye_occlusion_top_out"],
            ["Shadow Bottom Min", "", "eye_occlusion_bottom_min"],
            ["Shadow Bottom Max", "", "eye_occlusion_bottom_max"],
            ["Shadow Bottom Min Contrast", "", "eye_occlusion_bottom_in"],
            ["Shadow Bottom Max Contrast", "", "eye_occlusion_bottom_out"],
            ["Shadow Inner Min", "", "eye_occlusion_inner_min"],
            ["Shadow Inner Max", "", "eye_occlusion_inner_max"],
            ["Shadow Inner Min Contrast", "", "eye_occlusion_inner_in"],
            ["Shadow Inner Max Contrast", "", "eye_occlusion_inner_out"],
            ["Shadow Outer Min", "", "eye_occlusion_outer_min"],
            ["Shadow Outer Max", "", "eye_occlusion_outer_max"],
            ["Shadow Outer Min Contrast", "", "eye_occlusion_outer_in"],
            ["Shadow Outer Max Contrast", "", "eye_occlusion_outer_out"],
            ["Show Blur Range", "", "eye_occlusion_blur_show"],
            ["Blur Color", "func_occlusion_color", "eye_occlusion_blur_color"],
            ["Blur Strength", "", "eye_occlusion_blur_strength"],
            ["Blur IOR", "", "eye_occlusion_blur_ior"],
            ["Blur Top Min", "", "eye_occlusion_blur_top_min"],
            ["Blur Top Max", "", "eye_occlusion_blur_top_max"],
            ["Blur Top Min Contrast", "func_one_minus", "eye_occlusion_blur_top_in"],
            ["Blur Top Max Contrast", "", "eye_occlusion_blur_top_out"],
            ["Blur Bottom Min", "", "eye_occlusion_blur_bottom_min"],
            ["Blur Bottom Max", "", "eye_occlusion_blur_bottom_max"],
            ["Blur Bottom Min Contrast", "func_one_minus", "eye_occlusion_blur_bottom_in"],
            ["Blur Bottom Max Contrast", "", "eye_occlusion_blur_bottom_out"],
            ["Blur Inner Min", "", "eye_occlusion_blur_inner_min"],
            ["Blur Inner Max", "", "eye_occlusion_blur_inner_max"],
            ["Blur Inner Min Contrast", "func_one_minus", "eye_occlusion_blur_inner_in"],
            ["Blur Inner Max Contrast", "", "eye_occlusion_blur_inner_out"],
            ["Blur Outer Min", "", "eye_occlusion_blur_outer_min"],
            ["Blur Outer Max", "", "eye_occlusion_blur_outer_max"],
            ["Blur Outer Min Contrast", "func_one_minus", "eye_occlusion_blur_outer_in"],
            ["Blur Outer Max Contrast", "", "eye_occlusion_blur_outer_out"],
            ["Edge Width", "", "eye_occlusion_edge_width"],
        ],
        "shape_keys": [
            [ "EO Bulge L", "OCCLUSION_LEFT", "eye_occlusion_bulge" ],
            [ "EO Bulge R", "OCCLUSION_RIGHT", "eye_occlusion_bulge" ],
            [ "EO Depth L", "OCCLUSION_LEFT", "eye_occlusion_displace" ],
            [ "EO Depth R", "OCCLUSION_RIGHT", "eye_occlusion_displace" ],
            [ "EO Upper Depth L", "OCCLUSION_LEFT", "eye_occlusion_top" ],
            [ "EO Upper Depth R", "OCCLUSION_RIGHT", "eye_occlusion_top" ],
            [ "EO Lower Depth L", "OCCLUSION_LEFT", "eye_occlusion_bottom" ],
            [ "EO Lower Depth R", "OCCLUSION_RIGHT", "eye_occlusion_bottom" ],
            [ "EO Inner Depth L", "OCCLUSION_LEFT", "eye_occlusion_inner" ],
            [ "EO Inner Depth R", "OCCLUSION_RIGHT", "eye_occlusion_inner" ],
            [ "EO Outer Depth L", "OCCLUSION_LEFT", "eye_occlusion_outer" ],
            [ "EO Outer Depth R", "OCCLUSION_RIGHT", "eye_occlusion_outer" ],
            [ "EO Bulge L", "OCCLUSION_PLUS_LEFT", "eye_occlusion_bulge" ],
            [ "EO Bulge R", "OCCLUSION_PLUS_RIGHT", "eye_occlusion_bulge" ],
            [ "EO Depth L", "OCCLUSION_PLUS_LEFT", "eye_occlusion_displace" ],
            [ "EO Depth R", "OCCLUSION_PLUS_RIGHT", "eye_occlusion_displace" ],
            [ "EO Upper Depth L", "OCCLUSION_PLUS_LEFT", "eye_occlusion_top" ],
            [ "EO Upper Depth R", "OCCLUSION_PLUS_RIGHT", "eye_occlusion_top" ],
            [ "EO Lower Depth L", "OCCLUSION_PLUS_LEFT", "eye_occlusion_bottom" ],
            [ "EO Lower Depth R", "OCCLUSION_PLUS_RIGHT", "eye_occlusion_bottom" ],
            [ "EO Inner Depth L", "OCCLUSION_PLUS_LEFT", "eye_occlusion_inner" ],
            [ "EO Inner Depth R", "OCCLUSION_PLUS_RIGHT", "eye_occlusion_inner" ],
            [ "EO Outer Depth L", "OCCLUSION_PLUS_LEFT", "eye_occlusion_outer" ],
            [ "EO Outer Depth R", "OCCLUSION_PLUS_RIGHT", "eye_occlusion_outer" ],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            # Shadow
            ["eye_occlusion_strength", 0.5, "", "Custom/Shadow Strength"],
            ["eye_occlusion_color", (0.5, 0.5, 0.5, 1.0), "func_color_bytes_linear", "Custom/Shadow Color"],
            ["eye_occlusion_top_min", 0.0, "func_index_f0", "Custom/Shadow Top Range"],
            ["eye_occlusion_top_max", 0.25, "func_index_f1", "Custom/Shadow Top Range"],
            ["eye_occlusion_top_in", 0.5, "", "Custom/Shadow Top Edge Fadeout Contrast"],
            ["eye_occlusion_top_out", 0.5, "", "Custom/Shadow Top Contrast"],
            ["eye_occlusion_bottom_min", 0.0, "func_index_f0", "Custom/Shadow Bottom Range"],
            ["eye_occlusion_bottom_max", 0.25, "func_index_f1", "Custom/Shadow Bottom Range"],
            ["eye_occlusion_bottom_in", 0.5, "", "Custom/Shadow Bottom Edge Fadeout Contrast"],
            ["eye_occlusion_bottom_out", 0.5, "", "Custom/Shadow Bottom Contrast"],
            ["eye_occlusion_inner_min", 0.0, "func_index_f0", "Custom/Shadow Inner Range"],
            ["eye_occlusion_inner_max", 0.25, "func_index_f1", "Custom/Shadow Inner Range"],
            ["eye_occlusion_inner_in", 0.5, "", "Custom/Shadow Inner Edge Fadeout Contrast"],
            ["eye_occlusion_inner_out", 0.5, "", "Custom/Shadow Inner Contrast"],
            ["eye_occlusion_outer_min", 0.0, "func_index_f0", "Custom/Shadow Outer Range"],
            ["eye_occlusion_outer_max", 0.25, "func_index_f1", "Custom/Shadow Outer Range"],
            ["eye_occlusion_outer_in", 0.5, "", "Custom/Shadow Outer Edge Fadeout Contrast"],
            ["eye_occlusion_outer_out", 0.5, "", "Custom/Shadow Outer Contrast"],
            # Blur
            ["eye_occlusion_blur_show", 0.0, "", "Custom/Display Blur Range"],
            ["eye_occlusion_blur_strength", 0.2, "", "Custom/Blur Strength"],
            ["eye_occlusion_blur_color", (1.0, 0.0, 0.0, 1.0), "func_color_bytes_linear", "Custom/Blur Color"],
            ["eye_occlusion_blur_top_min", 0.0, "func_index_f0", "Custom/Top Blur Range"],
            ["eye_occlusion_blur_top_max", 0.25, "func_index_f1", "Custom/Top Blur Range"],
            ["eye_occlusion_blur_top_in", 0.5, "", "Custom/Top Blur Edge Fadeout Contrast"],
            ["eye_occlusion_blur_top_out", 0.5, "", "Custom/Top Blur Contrast"],
            ["eye_occlusion_blur_bottom_min", 0.0, "func_index_f0", "Custom/Bottom Blur Range"],
            ["eye_occlusion_blur_bottom_max", 0.25, "func_index_f1", "Custom/Bottom Blur Range"],
            ["eye_occlusion_blur_bottom_in", 0.5, "", "Custom/Bottom Blur Edge Fadeout Contrast"],
            ["eye_occlusion_blur_bottom_out", 0.5, "", "Custom/Bottom Blur Contrast"],
            ["eye_occlusion_blur_inner_min", 0.0, "func_index_f0", "Custom/Inner Blur Range"],
            ["eye_occlusion_blur_inner_max", 0.25, "func_index_f1", "Custom/Inner Blur Range"],
            ["eye_occlusion_blur_inner_in", 0.5, "", "Custom/Inner Blur Edge Fadeout Contrast"],
            ["eye_occlusion_blur_inner_out", 0.5, "", "Custom/Inner Blur Contrast"],
            ["eye_occlusion_blur_outer_min", 0.0, "func_index_f0", "Custom/Outer Blur Range"],
            ["eye_occlusion_blur_outer_max", 0.25, "func_index_f1", "Custom/Outer Blur Range"],
            ["eye_occlusion_blur_outer_in", 0.5, "", "Custom/Outer Blur Edge Fadeout Contrast"],
            ["eye_occlusion_blur_outer_out", 0.5, "", "Custom/Outer Blur Contrast"],
            # Shape
            ["eye_occlusion_displace", 0, "", "Custom/Depth Offset"],
            ["eye_occlusion_top", 0, "", "Custom/Top Offset"],
            ["eye_occlusion_bottom", 0, "", "Custom/Bottom Offset"],
            ["eye_occlusion_inner", 0, "", "Custom/Inner Corner Offset"],
            ["eye_occlusion_outer", 0, "", "Custom/Outer Corner Offset"],
            # Custom
            ["eye_occlusion_blur_ior", 0.5, "DEF"],
            ["eye_occlusion_bulge", 0.0, "DEF"],
            ["eye_occlusion_edge_width", 0.25, "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["Custom/Shadow Color", [255.0, 255.0, 255.0], "func_export_byte3_linear", "eye_occlusion_color"],
            ["Custom/Blur Color", [255.0, 255.0, 255.0], "func_export_byte3_linear", "eye_occlusion_blur_color"],
            ["Custom/Depth Offset", 0.02, "func_mul_100", "eye_occlusion_displace"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Shadow", "COLOR"],
            ["PROP", "Color", "eye_occlusion_color", False],
            ["PROP", "Strength", "eye_occlusion_strength", True],
            ["PAIR", "Top", "eye_occlusion_top_min", "eye_occlusion_top_max", True],
            ["PAIR", "Contrast", "eye_occlusion_top_in", "eye_occlusion_top_out", True],
            ["PAIR", "Bottom", "eye_occlusion_bottom_min", "eye_occlusion_bottom_max", True],
            ["PAIR", "Contrast", "eye_occlusion_bottom_in", "eye_occlusion_bottom_out", True],
            ["PAIR", "Inner", "eye_occlusion_inner_min", "eye_occlusion_inner_max", True],
            ["PAIR", "Contrast", "eye_occlusion_inner_in", "eye_occlusion_inner_out", True],
            ["PAIR", "Outer", "eye_occlusion_outer_min", "eye_occlusion_outer_max", True],
            ["PAIR", "Contrast", "eye_occlusion_outer_in", "eye_occlusion_outer_out", True],
            ["HEADER",  "Blur", "MOD_OPACITY"],
            ["PROP", "Show", "eye_occlusion_blur_show", True],
            ["PROP", "Color", "eye_occlusion_blur_color", False],
            ["PROP", "Strength", "eye_occlusion_blur_strength", True],
            ["PROP", "IOR", "eye_occlusion_blur_ior", True],
            ["PAIR", "Top", "eye_occlusion_blur_top_min", "eye_occlusion_blur_top_max", True],
            ["PAIR", "Contrast", "eye_occlusion_blur_top_in", "eye_occlusion_blur_top_out", True],
            ["PAIR", "Bottom", "eye_occlusion_blur_bottom_min", "eye_occlusion_blur_bottom_max", True],
            ["PAIR", "Contrast", "eye_occlusion_blur_bottom_in", "eye_occlusion_blur_bottom_out", True],
            ["PAIR", "Inner", "eye_occlusion_blur_inner_min", "eye_occlusion_blur_inner_max", True],
            ["PAIR", "Contrast", "eye_occlusion_blur_inner_in", "eye_occlusion_blur_inner_out", True],
            ["PAIR", "Outer", "eye_occlusion_blur_outer_min", "eye_occlusion_blur_outer_max", True],
            ["PAIR", "Contrast", "eye_occlusion_blur_outer_in", "eye_occlusion_blur_outer_out", True],
            ["SPACER"],
            ["PROP", "Edge Width", "eye_occlusion_edge_width", True],
            ["HEADER",  "Displacement", "MOD_DISPLACE"],
            ["PROP", "Displace", "eye_occlusion_displace", True],
            ["PROP", "Top", "eye_occlusion_top", True],
            ["PROP", "Bottom", "eye_occlusion_bottom", True],
            ["PROP", "Inner", "eye_occlusion_inner", True],
            ["PROP", "Outer", "eye_occlusion_outer", True],
            ["PROP", "Bulge", "eye_occlusion_bulge", True],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Two Side": True,
            "Diffuse Color": [ 255.0, 255.0, 255.0 ],
            "Ambient Color": [ 0.0, 0.0, 0.0 ],
            "Specular Color": [ 0.0, 0.0, 0.0 ],
            "Opacity": 1.0,
            "Self Illumination": 0.0,
            "Textures": {},
            "Custom Shader": {
                "Shader Name": "RLEyeOcclusion_Plus",
                "Image": {},
                "Variable": {},
            }
        },
    },

    # Skin Shader
    ########################################

    {   "name": "rl_skin_shader",
        "rl_shader": "RLSkin",
        "label": "Skin (Body)",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Diffuse Color", "", "skin_diffuse_color"],
            ["Diffuse Hue", "", "skin_diffuse_hue"],
            ["Diffuse Saturation", "", "skin_diffuse_saturation"],
            ["Diffuse Brightness", "", "skin_diffuse_brightness"],
            ["Diffuse HSV", "", "skin_diffuse_hsv_strength"],
            ["AO Strength", "", "skin_ao_strength"],
            ["AO Power", "", "skin_ao_power"],
            ["Specular Scale", "", "skin_specular_scale"],
            ["Secondary Specular Scale", "", "skin_secondary_specular_scale"],
            ["Roughness Power", "func_roughness_power", "skin_roughness_power"],
            ["Roughness Min", "", "skin_roughness_min"],
            ["Roughness Max", "", "skin_roughness_max"],
            ["Original Roughness", "", "skin_original_roughness"],
            ["Cavity Strength", "", "skin_cavity_strength"],
            ["Secondary Roughness", "", "skin_secondary_roughness_scale"],
            ["Normal Strength", "func_skin_normal_strength", "skin_normal_strength"],
            ["Micro Normal Strength", "func_micro_normal_strength", "skin_micro_normal_strength"],
            ["Bump Scale", "", "skin_bump_scale"],
            ["Height Scale", "", "skin_height_scale"],
            ["Subsurface Falloff", "func_sss_falloff_saturated", "skin_subsurface_falloff", "skin_subsurface_saturation"],
            ["Subsurface Radius", "func_sss_radius_skin_cycles", "skin_subsurface_radius"],
            ["Subsurface Scale", "func_sss_skin", "skin_subsurface_scale"],
            ["Unmasked Scatter Scale", "", "skin_unmasked_scatter_scale"],
            ["R Scatter Scale", "", "skin_r_scatter_scale"],
            ["G Scatter Scale", "", "skin_g_scatter_scale"],
            ["B Scatter Scale", "", "skin_b_scatter_scale"],
            ["A Scatter Scale", "", "skin_a_scatter_scale"],
            ["Micro Roughness Mod", "", "skin_micro_roughness_mod"],
            ["Unmasked Roughness Mod", "", "skin_unmasked_roughness_mod"],
            ["R Roughness Mod", "", "skin_r_roughness_mod"],
            ["G Roughness Mod", "", "skin_g_roughness_mod"],
            ["B Roughness Mod", "", "skin_b_roughness_mod"],
            ["A Roughness Mod", "", "skin_a_roughness_mod"],
            ["Emissive Color", "", "skin_emissive_color"],
            ["Emission Strength", "func_emission_scale", "skin_emission_strength"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_sss_radius_skin_eevee", "skin_subsurface_radius", "skin_subsurface_falloff", "skin_subsurface_saturation"],
        ],
        # texture inputs:
        # [input_socket_color, input_socket_alpha, texture_type, tiling_prop, tiling_mode]
        "textures": [
            ["Diffuse Map", "", "DIFFUSE"],
            ["AO Map", "", "AO"],
            ["Subsurface Map", "", "SSS"],
            ["Transmission Map", "", "TRANSMISSION"],
            ["Metallic Map", "", "METALLIC"],
            ["Specular Map", "", "SPECULAR"],
            ["Roughness Map", "", "ROUGHNESS"],
            ["Cavity Map", "", "CAVITY"],
            ["Normal Map", "", "NORMAL"],
            ["Normal Blend Map", "", "NORMALBLEND"],
            ["Micro Normal Map", "", "MICRONORMAL", "OFFSET", "", "skin_micro_normal_tiling"],
            ["Micro Normal Mask", "", "MICRONMASK"],
            ["RGBA Map", "RGBA Alpha", "RGBAMASK"],
            ["Emission Map", "", "EMISSION"],
            ["Height Map", "", "DISPLACE"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["skin_diffuse_color", (1,1,1,1), "func_color_bytes", "/Diffuse Color"],
            ["skin_micro_normal_tiling", 25, "", "Custom/MicroNormal Tiling"],
            ["skin_micro_normal_strength", 0.8, "", "Custom/MicroNormal Strength"],
            ["skin_micro_roughness_mod", 0.20, "", "Custom/Micro Roughness Scale"],
            ["skin_r_roughness_mod", 0.0, "", "Custom/R Channel Roughness Scale"],
            ["skin_g_roughness_mod", 0.0, "", "Custom/G Channel Roughness Scale"],
            ["skin_b_roughness_mod", 0.0, "", "Custom/B Channel Roughness Scale"],
            ["skin_a_roughness_mod", 0.0, "", "Custom/A Channel Roughness Scale"],
            ["skin_unmasked_roughness_mod", 0.0, "", "Custom/Unmasked Roughness Scale"],
            ["skin_specular_scale", 0.4, "", "Custom/_Specular"],
            ["skin_r_scatter_scale", 1, "", "Custom/R Channel Scatter Scale"],
            ["skin_g_scatter_scale", 1, "", "Custom/G Channel Scatter Scale"],
            ["skin_b_scatter_scale", 1, "", "Custom/B Channel Scatter Scale"],
            ["skin_a_scatter_scale", 1, "", "Custom/A Channel Scatter Scale"],
            ["skin_unmasked_scatter_scale", 1, "", "Custom/Unmasked Scatter Scale"],
            ["skin_ao_strength", 1, "", "Pbr/AO"],
            ["skin_normal_strength", 1, "", "Pbr/Normal"],
            ["skin_emission_strength", 0, "", "Pbr/Glow"],
            ["skin_subsurface_falloff", (1.0, 0.112, 0.072, 1.0), "func_color_bytes", "SSS/Falloff"],
            ["skin_subsurface_radius", 1.5, "", "SSS/Radius"],
            ["skin_original_roughness", 1, "", "Custom/Original Roughness Strength"],
            ["skin_cavity_strength", 0, "", "Custom/Cavity Strength"],
            ["skin_height_scale", 0.0, "", "Pbr/Displacement"],
            ["skin_bump_scale", 0.0, "DEF"],
            # non json properties (just defaults)
            ["skin_ao_power", 2.0, "DEF"],
            ["skin_diffuse_hue", 0.5, "", "/Diffuse Hue"],
            ["skin_diffuse_saturation", 1, "func_saturation_mod", "/Diffuse Saturation"],
            ["skin_diffuse_brightness", 1, "func_brightness_mod", "/Diffuse Brightness"],
            ["skin_subsurface_saturation", 1.0, "DEF"],
            ["skin_diffuse_hsv_strength", 1, "DEF"],
            ["skin_roughness_power", 1.0, "DEF"],
            ["skin_roughness_min", 0, "DEF"],
            ["skin_roughness_max", 1, "DEF"],
            ["skin_subsurface_scale", 1, "DEF"],
            ["skin_emissive_color", (1,1,1,1), "DEF"],
            ["skin_secondary_specular_scale", 0.5, "DEF"],
            ["skin_secondary_roughness_scale", 0.5, "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["/Diffuse Color", [255.0, 255.0, 255.0], "func_export_byte3", "skin_diffuse_color"],
            ["/Diffuse Brightness", 1.0, "func_export_brightness_mod", "skin_diffuse_brightness"],
            ["/Diffuse Saturation", 1.0, "func_export_saturation_mod", "skin_diffuse_saturation"],
            ["/Diffuse HSV", 1.0, "", "skin_diffuse_hsv_strength"],
            ["SSS/Falloff", [255.0, 94.3499984741211, 76.5], "func_export_byte3", "skin_subsurface_falloff"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "Color", "skin_diffuse_color", True],
            ["TRIPLET", "HSV", "skin_diffuse_hue", "skin_diffuse_saturation", "skin_diffuse_brightness", True, "Diffuse Map"],
            ["PROP", "*HSV Strength", "skin_diffuse_hsv_strength", True, "Diffuse Map"],
            ["SPACER"],
            ["PROP", "AO Strength", "skin_ao_strength", True, "AO Map"],
            ["PROP", "AO Darken", "skin_ao_power", True, "AO Map"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Specular Scale", "skin_specular_scale", True],
            ["PROP", "*Roughness Power", "skin_roughness_power", True],
            ["PAIR", "Roughness Range", "skin_roughness_min", "skin_roughness_max", True],
            ["PROP", "Original Roughness", "skin_original_roughness", True],
            ["PROP", "Cavity Strength", "skin_cavity_strength", True, "Cavity Map"],
            ["PROP", "*Sec. Specular", "skin_secondary_specular_scale", True],
            ["PROP", "*Sec. Roughness", "skin_secondary_roughness_scale", True],
            ["SPACER"],
            ["PROP", "Micro Roughness Mod", "skin_micro_roughness_mod", True],
            ["PROP", "R Roughness Mod", "skin_r_roughness_mod", True, "RGBA Map"],
            ["PROP", "G Roughness Mod", "skin_g_roughness_mod", True, "RGBA Map"],
            ["PROP", "B Roughness Mod", "skin_b_roughness_mod", True, "RGBA Map"],
            ["PROP", "A Roughness Mod", "skin_a_roughness_mod", True, "RGBA Map"],
            ["PROP", "Unmasked Roughness Mod", "skin_unmasked_roughness_mod", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "*Weight", "skin_subsurface_scale", True],
            ["PROP", "Falloff", "skin_subsurface_falloff", False],
            ["PROP", "*Saturation", "skin_subsurface_saturation", True],
            ["PROP", "Radius", "skin_subsurface_radius", True],
            ["SPACER"],
            ["PROP", "R Scatter Scale", "skin_r_scatter_scale", True, "RGBA Map"],
            ["PROP", "G Scatter Scale", "skin_g_scatter_scale", True, "RGBA Map"],
            ["PROP", "B Scatter Scale", "skin_b_scatter_scale", True, "RGBA Map"],
            ["PROP", "A Scatter Scale", "skin_a_scatter_scale", True, "RGBA Map"],
            ["PROP", "Unmasked Scatter Scale", "skin_unmasked_scatter_scale", True],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Normal Strength", "skin_normal_strength", True, "Normal Map"],
            ["PROP", "Micro Normal Strength", "skin_micro_normal_strength", True, "Micro Normal Map"],
            ["PROP", "Micro Normal Tiling", "skin_micro_normal_tiling", True, "Micro Normal Map"],
            ["PROP", "Bump Scale", "skin_bump_scale", True, "Height Map"],
            ["PROP", "Displacement Scale", "skin_height_scale", True, "Height Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "*Emissive Color", "skin_emissive_color", False],
            ["PROP", "Emission Strength", "skin_emission_strength", True],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Two Side": True,
            "Diffuse Color": [ 255.0, 255.0, 255.0 ],
            "Ambient Color": [ 125.0, 125.0, 125.0 ],
            "Specular Color": [ 68.7, 68.7, 68.7 ],
            "Opacity": 1.0,
            "Self Illumination": 0.0,
            "Textures": {},
            "Custom Shader": {
                "Shader Name": "RLSkin",
                "Image": {},
                "Variable": {},
            },
            "Subsurface Scatter": {
                "Falloff": [ 255.0, 94.35, 76.5 ],
                "Radius": 1.5,
                "Distribution": 0.4,
                "IOR": 3.0,
                "DecayScale": 0.15,
                "Lerp": 0.85
            }
        },
    },

    # Head Shader
    ##########################################

    {   "name": "rl_head_shader",
        "rl_shader": "RLHead",
        "label": "Skin (Head)",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Diffuse Color", "", "skin_diffuse_color"],
            ["Diffuse Hue", "", "skin_diffuse_hue"],
            ["Diffuse Saturation", "", "skin_diffuse_saturation"],
            ["Diffuse Brightness", "", "skin_diffuse_brightness"],
            ["Diffuse HSV", "", "skin_diffuse_hsv_strength"],
            ["Cavity AO Strength", "", "skin_cavity_ao_strength"],
            ["Blend Overlay Strength", "", "skin_blend_overlay_strength"],
            ["AO Strength", "", "skin_ao_strength"],
            ["AO Power", "", "skin_ao_power"],
            ["Mouth AO", "", "skin_mouth_ao"],
            ["Nostril AO", "", "skin_nostril_ao"],
            ["Lip AO", "", "skin_lips_ao"],
            ["Specular Scale", "", "skin_specular_scale"],
            ["Secondary Specular Scale", "", "skin_secondary_specular_scale"],
            ["Roughness Power", "func_roughness_power", "skin_roughness_power"],
            ["Roughness Min", "", "skin_roughness_min"],
            ["Roughness Max", "", "skin_roughness_max"],
            ["Original Roughness", "", "skin_original_roughness"],
            ["Cavity Strength", "", "skin_cavity_strength"],
            ["Secondary Roughness", "", "skin_secondary_roughness_scale"],
            ["Normal Strength", "func_skin_normal_strength", "skin_normal_strength"],
            ["Micro Normal Strength", "func_micro_normal_strength", "skin_micro_normal_strength"],
            ["Normal Blend Strength", "", "skin_normal_blend_strength"],
            ["Unmasked Scatter Scale", "", "skin_unmasked_scatter_scale"],
            ["Nose Scatter Scale", "", "skin_nose_scatter_scale"],
            ["Mouth Scatter Scale", "", "skin_mouth_scatter_scale"],
            ["Upper Lid Scatter Scale", "", "skin_upper_lid_scatter_scale"],
            ["Inner Lid Scatter Scale", "", "skin_inner_lid_scatter_scale"],
            ["Cheek Scatter Scale", "", "skin_cheek_scatter_scale"],
            ["Forehead Scatter Scale", "", "skin_forehead_scatter_scale"],
            ["Upper Lip Scatter Scale", "", "skin_upper_lip_scatter_scale"],
            ["Chin Scatter Scale", "", "skin_chin_scatter_scale"],
            ["Ear Scatter Scale", "", "skin_ear_scatter_scale"],
            ["Neck Scatter Scale", "", "skin_neck_scatter_scale"],
            ["Subsurface Falloff", "func_sss_falloff_saturated", "skin_subsurface_falloff", "skin_subsurface_saturation"],
            ["Subsurface Radius", "func_sss_radius_skin_cycles", "skin_subsurface_radius"],
            ["Subsurface Scale", "func_sss_skin", "skin_subsurface_scale"],
            ["Micro Roughness Mod", "", "skin_micro_roughness_mod"],
            ["Unmasked Roughness Mod", "", "skin_unmasked_roughness_mod"],
            ["Nose Roughness Mod", "", "skin_nose_roughness_mod"],
            ["Mouth Roughness Mod", "", "skin_mouth_roughness_mod"],
            ["Upper Lid Roughness Mod", "", "skin_upper_lid_roughness_mod"],
            ["Inner Lid Roughness Mod", "", "skin_inner_lid_roughness_mod"],
            ["Cheek Roughness Mod", "", "skin_cheek_roughness_mod"],
            ["Forehead Roughness Mod", "", "skin_forehead_roughness_mod"],
            ["Upper Lip Roughness Mod", "", "skin_upper_lip_roughness_mod"],
            ["Chin Roughness Mod", "", "skin_chin_roughness_mod"],
            ["Ear Roughness Mod", "", "skin_ear_roughness_mod"],
            ["Neck Roughness Mod", "", "skin_neck_roughness_mod"],
            ["Emissive Color", "", "skin_emissive_color"],
            ["Emission Strength", "func_emission_scale", "skin_emission_strength"],
            ["Height Scale", "", "skin_height_scale"],
            ["Bump Scale", "", "skin_bump_scale"],
            ["Height Delta Scale", "", "skin_height_delta_scale"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_sss_radius_skin_eevee", "skin_subsurface_radius", "skin_subsurface_falloff", "skin_subsurface_saturation"],
        ],
        # texture inputs:
        # [input_socket_color, input_socket_alpha, texture_type, tiling_prop, tiling_mode]
        "textures": [
            ["Diffuse Map", "", "DIFFUSE"],
            ["Blend Overlay", "", "BLEND2"],
            ["AO Map", "", "AO"],
            ["MCMAO Map", "MCMAO Alpha", "MCMAOMASK"],
            ["Subsurface Map", "", "SSS"],
            ["Transmission Map", "", "TRANSMISSION"],
            ["Metallic Map", "", "METALLIC"],
            ["Specular Map", "", "SPECULAR"],
            ["Specular Mask", "", "SPECMASK"],
            ["Roughness Map", "", "ROUGHNESS"],
            ["Cavity Map", "", "CAVITY"],
            ["Normal Map", "", "NORMAL"],
            ["Normal Blend Map", "", "NORMALBLEND"],
            ["Micro Normal Map", "", "MICRONORMAL", "OFFSET", "", "skin_micro_normal_tiling"],
            ["Micro Normal Mask", "", "MICRONMASK"],
            ["NMUIL Map", "NMUIL Alpha", "NMUILMASK"],
            ["CFULC Map", "CFULC Alpha", "CFULCMASK"],
            ["EN Map", "", "ENNASK"],
            ["Emission Map", "", "EMISSION"],
            ["Height Map", "", "DISPLACE"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["skin_diffuse_color", (1,1,1,1), "func_color_bytes", "/Diffuse Color"],
            ["skin_blend_overlay_strength", 0, "", "Custom/BaseColor Blend2 Strength"],
            ["skin_normal_blend_strength", 0, "", "Custom/NormalMap Blend Strength"],
            ["skin_micro_normal_tiling", 20, "", "Custom/MicroNormal Tiling"],
            ["skin_micro_normal_strength", 0.5, "", "Custom/MicroNormal Strength"],
            ["skin_micro_roughness_mod", 0.20, "", "Custom/Micro Roughness Scale"],
            ["skin_nose_roughness_mod", 0.119, "", "Custom/Nose Roughness Scale"],
            ["skin_mouth_roughness_mod", 0.034, "", "Custom/Mouth Roughness Scale"],
            ["skin_upper_lid_roughness_mod", -0.3, "", "Custom/UpperLid Roughness Scale"],
            ["skin_inner_lid_roughness_mod", -0.574, "", "Custom/InnerLid Roughness Scale"],
            ["skin_ear_roughness_mod", 0.0, "", "Custom/Ear Roughness Scale"],
            ["skin_neck_roughness_mod", 0.0, "", "Custom/Neck Roughness Scale"],
            ["skin_cheek_roughness_mod", 0.0, "", "Custom/Cheek Roughness Scale"],
            ["skin_forehead_roughness_mod", 0.0, "", "Custom/Forehead Roughness Scale"],
            ["skin_upper_lip_roughness_mod", 0.0, "", "Custom/UpperLip Roughness Scale"],
            ["skin_chin_roughness_mod", 0.0, "", "Custom/Chin Roughness Scale"],
            ["skin_unmasked_roughness_mod", 0.0, "", "Custom/Unmasked Roughness Scale"],
            ["skin_specular_scale", 0.4, "", "Custom/_Specular"],
            ["skin_mouth_ao", 2.5, "", "Custom/Inner Mouth Ao"],
            ["skin_nostril_ao", 2.5, "", "Custom/Nostril Ao"],
            ["skin_lips_ao", 2.5, "", "Custom/Lips Gap Ao"],
            ["skin_nose_scatter_scale", 1, "", "Custom/Nose Scatter Scale"],
            ["skin_mouth_scatter_scale", 1, "", "Custom/Mouth Scatter Scale"],
            ["skin_upper_lid_scatter_scale", 1, "", "Custom/UpperLid Scatter Scale"],
            ["skin_inner_lid_scatter_scale", 1, "", "Custom/InnerLid Scatter Scale"],
            ["skin_ear_scatter_scale", 1, "", "Custom/Ear Scatter Scale"],
            ["skin_neck_scatter_scale", 1, "", "Custom/Neck Scatter Scale"],
            ["skin_cheek_scatter_scale", 1, "", "Custom/Cheek Scatter Scale"],
            ["skin_forehead_scatter_scale", 1, "", "Custom/Forehead Scatter Scale"],
            ["skin_upper_lip_scatter_scale", 1, "", "Custom/UpperLip Scatter Scale"],
            ["skin_chin_scatter_scale", 1, "", "Custom/Chin Scatter Scale"],
            ["skin_unmasked_scatter_scale", 1, "", "Custom/Unmasked Scatter Scale"],
            ["skin_ao_strength", 1, "", "Pbr/AO"],
            ["skin_normal_strength", 1, "", "Pbr/Normal"],
            ["skin_emission_strength", 0, "", "Pbr/Glow"],
            ["skin_subsurface_falloff", (1.0, 0.112, 0.072, 1.0), "func_color_bytes", "SSS/Falloff"],
            ["skin_subsurface_radius", 1.5, "", "SSS/Radius"],
            ["skin_original_roughness", 1, "", "Custom/Original Roughness Strength"],
            ["skin_cavity_strength", 0, "", "Custom/Cavity Strength"],
            ["skin_height_scale", 0.0, "", "Pbr/Displacement"],
            ["skin_bump_scale", 0.0, "DEF"],
            # non json properties (just defaults)
            ["skin_ao_power", 2.0, "DEF"],
            ["skin_diffuse_hue", 0.5, "", "/Diffuse Hue"],
            ["skin_diffuse_saturation", 1, "func_saturation_mod", "/Diffuse Saturation"],
            ["skin_diffuse_brightness", 1, "func_brightness_mod", "/Diffuse Brightness"],
            ["skin_diffuse_hsv_strength", 1, "DEF"],
            ["skin_subsurface_saturation", 1.0, "DEF"],
            ["skin_roughness_power", 1.0, "DEF"],
            ["skin_roughness_min", 0, "DEF"],
            ["skin_roughness_max", 1, "DEF"],
            ["skin_subsurface_scale", 1, "DEF"],
            ["skin_emissive_color", (1,1,1,1), "DEF"],
            ["skin_secondary_specular_scale", 0.5, "DEF"],
            ["skin_secondary_roughness_scale", 0.5, "DEF"],
            ["skin_height_delta_scale", 1.0, "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["/Diffuse Color", [255.0, 255.0, 255.0], "func_export_byte3", "skin_diffuse_color"],
            ["/Diffuse Brightness", 1.0, "func_export_brightness_mod", "skin_diffuse_brightness"],
            ["/Diffuse Saturation", 1.0, "func_export_saturation_mod", "skin_diffuse_saturation"],
            ["/Diffuse HSV", 1.0, "", "skin_diffuse_hsv_strength"],
            ["SSS/Falloff", [255.0, 94.3499984741211, 76.5], "func_export_byte3", "skin_subsurface_falloff"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["WRINKLE_CONTROLS",  "Wrinkle Maps", "MOD_INSTANCE"],
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "Color", "skin_diffuse_color", True],
            ["TRIPLET", "HSV", "skin_diffuse_hue", "skin_diffuse_saturation", "skin_diffuse_brightness", True, "Diffuse Map"],
            ["PROP", "*HSV Strength", "skin_diffuse_hsv_strength", True, "Diffuse Map"],
            ["SPACER"],
            ["PROP", "AO Strength", "skin_ao_strength", True, "AO Map"],
            ["PROP", "AO Darken", "skin_ao_power", True, "AO Map"],
            ["PROP", "Mouth AO", "skin_mouth_ao", True, "MCMAO Map"],
            ["PROP", "Nostrils AO", "skin_nostril_ao", True, "MCMAO Map"],
            ["PROP", "Lips AO", "skin_lips_ao", True, "MCMAO Map"],
            ["SPACER"],
            ["PROP", "Color Blend", "skin_blend_overlay_strength", True, "Blend Overlay"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Specular Scale", "skin_specular_scale", True],
            ["PROP", "*Roughness Power", "skin_roughness_power", True],
            ["PAIR", "Roughness Range", "skin_roughness_min", "skin_roughness_max", True],
            ["PROP", "Original Roughness", "skin_original_roughness", True],
            ["PROP", "Cavity Strength", "skin_cavity_strength", True, "Cavity Map"],
            ["PROP", "*Sec. Specular", "skin_secondary_specular_scale", True],
            ["PROP", "*Sec. Roughness", "skin_secondary_roughness_scale", True],
            ["SPACER"],
            ["PROP", "Micro Roughness Mod", "skin_micro_roughness_mod", True],
            ["PROP", "Nose Rougness Mod", "skin_nose_roughness_mod", True, "NMUIL Map"],
            ["PROP", "Mouth Rougness Mod", "skin_mouth_roughness_mod", True, "NMUIL Map"],
            ["PROP", "Upper Lid Rougness Mod", "skin_upper_lid_roughness_mod", True, "NMUIL Map"],
            ["PROP", "Inner Lid Rougness Mod", "skin_inner_lid_roughness_mod", True, "NMUIL Map"],
            ["PROP", "Ear Rougness Mod", "skin_ear_roughness_mod", True, "EN Map"],
            ["PROP", "Neck Rougness Mod", "skin_neck_roughness_mod", True, "EN Map"],
            ["PROP", "Cheek Rougness Mod", "skin_cheek_roughness_mod", True, "CFULC Map"],
            ["PROP", "Forehead Rougness Mod", "skin_forehead_roughness_mod", True, "CFULC Map"],
            ["PROP", "Upper Lip Rougness Mod", "skin_upper_lip_roughness_mod", True, "CFULC Map"],
            ["PROP", "Chin Rougness Mod", "skin_chin_roughness_mod", True, "CFULC Map"],
            ["PROP", "Unmasked Roughness Mod", "skin_unmasked_roughness_mod", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "*Weight", "skin_subsurface_scale", True],
            ["PROP", "Falloff", "skin_subsurface_falloff", False],
            ["PROP", "*Saturation", "skin_subsurface_saturation", True],
            ["PROP", "Radius", "skin_subsurface_radius", True],
            ["SPACER"],
            ["PROP", "Nose Scatter Scale", "skin_nose_scatter_scale", True, "NMUIL Map"],
            ["PROP", "Mouth Scatter Scale", "skin_mouth_scatter_scale", True, "NMUIL Map"],
            ["PROP", "Upper Lid Scatter Scale", "skin_upper_lid_scatter_scale", True, "NMUIL Map"],
            ["PROP", "Inner Lid Scatter Scale", "skin_inner_lid_scatter_scale", True, "NMUIL Map"],
            ["PROP", "Ear Scatter Scale", "skin_ear_scatter_scale", True, "EN Map"],
            ["PROP", "Neck Scatter Scale", "skin_neck_scatter_scale", True, "EN Map"],
            ["PROP", "Cheek Scatter Scale", "skin_cheek_scatter_scale", True, "CFULC Map"],
            ["PROP", "Forehead Scatter Scale", "skin_forehead_scatter_scale", True, "CFULC Map"],
            ["PROP", "Upper Lip Scatter Scale", "skin_upper_lip_scatter_scale", True, "CFULC Map"],
            ["PROP", "Chin Scatter Scale", "skin_chin_scatter_scale", True, "CFULC Map"],
            ["PROP", "Unmasked Scatter Scale", "skin_unmasked_scatter_scale", True],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Normal Strength", "skin_normal_strength", True, "Normal Map"],
            ["PROP", "Normal Blend", "skin_normal_blend_strength", True, "Normal Blend Map"],
            ["PROP", "Micro Normal Strength", "skin_micro_normal_strength", True, "Micro Normal Map"],
            ["PROP", "Micro Normal Tiling", "skin_micro_normal_tiling", True, "Micro Normal Map"],
            ["PROP", "Bump Scale", "skin_bump_scale", True, "Height Map"],
            ["PROP", "Displacement Scale", "skin_height_scale", True, "Height Map"],
            ["PROP", "Wrinkle Displacement", "skin_height_delta_scale", True, "Height Delta"],
            #["OP", "Build Displacement", "cc3.bake", "PLAY", "BUILD_DISPLACEMENT", "Normal Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "*Emissive Color", "skin_emissive_color", False],
            ["PROP", "Emission Strength", "skin_emission_strength", True],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Two Side": True,
            "Diffuse Color": [ 255.0, 255.0, 255.0 ],
            "Ambient Color": [ 125.0, 125.0, 125.0 ],
            "Specular Color": [ 68.7, 68.7, 68.7 ],
            "Opacity": 1.0,
            "Self Illumination": 0.0,
            "Textures": {},
            "Custom Shader": {
                "Shader Name": "RLHead",
                "Image": {},
                "Variable": {},
            },
            "Subsurface Scatter": {
                "Falloff": [ 255.0, 94.35, 76.5 ],
                "Radius": 1.5,
                "Distribution": 0.4,
                "IOR": 3.0,
                "DecayScale": 0.15,
                "Lerp": 0.85
            }
        },
    },

    # Tongue Shader
    #########################################

    {   "name": "rl_tongue_shader",
        "rl_shader": "RLTongue",
        "label": "Tongue",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Hue", "", "tongue_hue"],
            ["Saturation", "", "tongue_saturation"],
            ["Brightness", "", "tongue_brightness"],
            ["HSV Strength", "", "tongue_hsv_strength"],
            ["Front AO", "", "tongue_front_ao"],
            ["Rear AO", "", "tongue_rear_ao"],
            ["AO Strength", "", "tongue_ao_strength"],
            ["AO Power", "", "tongue_ao_power"],
            ["Subsurface Scale", "func_sss_tongue", "tongue_subsurface_scatter"],
            ["Front Specular", "", "tongue_front_specular"],
            ["Rear Specular", "", "tongue_rear_specular"],
            ["Front Roughness", "", "tongue_front_roughness"],
            ["Rear Roughness", "", "tongue_rear_roughness"],
            ["Normal Strength", "func_normal_strength", "tongue_normal_strength"],
            ["Micro Normal Strength", "func_micro_normal_strength", "tongue_micro_normal_strength"],
            ["Emissive Color", "", "tongue_emissive_color"],
            ["Emission Strength", "func_emission_scale", "tongue_emission_strength"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_sss_radius_tongue_eevee", "tongue_subsurface_radius", "tongue_subsurface_falloff"]
        ],
        # texture inputs:
        # [input_socket_color, input_socket_alpha, texture_type, tiling_prop, tiling_mode]
        "textures": [
            ["Diffuse Map", "", "DIFFUSE"],
            ["Gradient AO Map", "", "GRADIENTAO"],
            ["AO Map", "", "AO"],
            ["Metallic Map", "", "METALLIC"],
            ["Roughness Map", "", "ROUGHNESS"],
            ["Normal Map", "", "NORMAL"],
            ["Micro Normal Map", "", "MICRONORMAL", "OFFSET", "", "tongue_micro_normal_tiling"],
            ["Emission Map", "", "EMISSION"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["tongue_micro_normal_tiling", 4, "", "Custom/MicroNormal Tiling"],
            ["tongue_micro_normal_strength", 0.5, "", "Custom/MicroNormal Strength"],
            ["tongue_brightness", 1, "", "Custom/_Brightness"],
            ["tongue_saturation", 0.95, "func_one_minus", "Custom/_Desaturation"],
            ["tongue_front_roughness", 1, "", "Custom/Front Roughness"],
            ["tongue_front_specular", 0.259, "", "Custom/Front Specular"],
            ["tongue_rear_roughness", 1, "", "Custom/Back Roughness"],
            ["tongue_rear_specular", 0, "", "Custom/Back Specular"],
            ["tongue_front_ao", 1, "", "Custom/Front AO"],
            ["tongue_rear_ao", 0, "", "Custom/Back AO"],
            ["tongue_subsurface_scatter", 1, "", "Custom/_Scatter"],
            ["tongue_ao_strength", 1, "", "Pbr/AO"],
            ["tongue_normal_strength", 1, "", "Pbr/Normal"],
            ["tongue_emission_strength", 0, "", "Pbr/Glow"],
            ["tongue_subsurface_falloff", (1, 1, 1, 1), "func_color_bytes", "SSS/Falloff"],
            ["tongue_subsurface_radius", 1, "", "SSS/Radius"],
            # non json properties (just defaults)
            ["tongue_ao_power", 1, "DEF"],
            ["tongue_hue", 0.5, "", "/Diffuse Hue"],
            ["tongue_hsv_strength", 1, "DEF"],
            ["tongue_emissive_color", (1,1,1,1), "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["Custom/_Desaturation", 0.05, "func_one_minus", "tongue_saturation"],
            ["SSS/Falloff", [255.0, 255.0, 255.0], "func_export_byte3", "tongue_subsurface_falloff"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "AO Strength", "tongue_ao_strength", True, "AO Map"],
            ["PROP", "AO Darken", "tongue_ao_power", True, "AO Map"],
            ["PROP", "Front AO", "tongue_front_ao", True, "Gradient AO Map"],
            ["PROP", "Back AO", "tongue_rear_ao", True, "Gradient AO Map"],
            ["SPACER"],
            ["TRIPLET", "HSV", "tongue_hue", "tongue_saturation", "tongue_brightness", True, "Diffuse Map"],
            ["PROP", "*HSV Strength", "tongue_hsv_strength", True, "Diffuse Map"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Front Roughness", "tongue_front_roughness", True],
            ["PROP", "Front Specular", "tongue_front_specular", True],
            ["PROP", "Back Roughness", "tongue_rear_roughness", True],
            ["PROP", "Back Specular", "tongue_rear_specular", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "Weight", "tongue_subsurface_scatter", True],
            ["PROP", "Falloff", "tongue_subsurface_falloff", False],
            ["PROP", "Radius", "tongue_subsurface_radius", True],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Normal Strength", "tongue_normal_strength", True, "Normal Map"],
            ["PROP", "Micro Normal Strength", "tongue_micro_normal_strength", True, "Micro Normal Map"],
            ["PROP", "Micro Normal Tiling", "tongue_micro_normal_tiling", True, "Micro Normal Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "*Emissive Color", "tongue_emissive_color", False],
            ["PROP", "Emission Strength", "tongue_emission_strength", True],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Two Side": True,
            "Diffuse Color": [ 255.0, 255.0, 255.0 ],
            "Ambient Color": [ 125.0, 125.0, 125.0 ],
            "Specular Color": [ 229.5, 229.5, 229.5 ],
            "Opacity": 1.0,
            "Self Illumination": 0.0,
            "Textures": {},
            "Custom Shader": {
                "Shader Name": "RLTongue",
                "Image": {},
                "Variable": {}
            },
            "Subsurface Scatter": {
                "Falloff": [ 255.0, 255.0, 255.0 ],
                "Radius": 1.0,
                "Distribution": 0.93,
                "IOR": 1.55,
                "DecayScale": 0.15,
                "Lerp": 0.9
            }
        },
    },

    # Teeth Shader
    ########################################

    {   "name": "rl_teeth_shader",
        "rl_shader": "RLTeethGums",
        "label": "Teeth & Gums",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Gums Hue", "", "teeth_gums_hue"],
            ["Gums Saturation", "", "teeth_gums_saturation"],
            ["Gums Brightness", "", "teeth_gums_brightness"],
            ["Gums HSV Strength", "", "teeth_gums_hsv_strength"],
            ["Teeth Hue", "", "teeth_teeth_hue"],
            ["Teeth Saturation", "", "teeth_teeth_saturation"],
            ["Teeth Brightness", "", "teeth_teeth_brightness"],
            ["Teeth HSV Strength", "", "teeth_teeth_hsv_strength"],
            ["Front AO", "", "teeth_front_ao"],
            ["Rear AO", "", "teeth_rear_ao"],
            ["AO Strength", "", "teeth_ao_strength"],
            ["AO Power", "", "teeth_ao_power"],
            ["Teeth Subsurface Scale", "func_sss_teeth", "teeth_teeth_subsurface_scatter"],
            ["Gums Subsurface Scale", "func_sss_teeth", "teeth_gums_subsurface_scatter"],
            ["Front Specular", "", "teeth_front_specular"],
            ["Rear Specular", "", "teeth_rear_specular"],
            ["Front Roughness", "", "teeth_front_roughness"],
            ["Rear Roughness", "", "teeth_rear_roughness"],
            ["Normal Strength", "func_normal_strength", "teeth_normal_strength"],
            ["Micro Normal Strength", "func_micro_normal_strength", "teeth_micro_normal_strength"],
            ["Emissive Color", "", "teeth_emissive_color"],
            ["Emission Strength", "func_emission_scale", "teeth_emission_strength"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_sss_radius_teeth_eevee", "teeth_subsurface_radius", "teeth_subsurface_falloff"]
        ],
        # texture inputs:
        # [input_socket_color, input_socket_alpha, texture_type, tiling_prop, tiling_mode]
        "textures": [
            ["Diffuse Map", "", "DIFFUSE"],
            ["Gradient AO Map", "", "GRADIENTAO"],
            ["Gums Mask", "", "GUMSMASK"],
            ["AO Map", "", "AO"],
            ["Metallic Map", "", "METALLIC"],
            ["Roughness Map", "", "ROUGHNESS"],
            ["Normal Map", "", "NORMAL"],
            ["Micro Normal Map", "", "MICRONORMAL", "OFFSET", "", "teeth_micro_normal_tiling"],
            ["Emission Map", "", "EMISSION"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["teeth_micro_normal_tiling", 10, "", "Custom/Teeth MicroNormal Tiling"],
            ["teeth_micro_normal_strength", 0.3, "", "Custom/Teeth MicroNormal Strength"],
            ["teeth_teeth_brightness", 0.7, "", "Custom/Teeth Brightness"],
            ["teeth_teeth_saturation", 0.9, "func_one_minus", "Custom/Teeth Desaturation"],
            ["teeth_gums_brightness", 0.9, "", "Custom/Gums Brightness"],
            ["teeth_gums_saturation", 1, "func_one_minus", "Custom/Gums Desaturation"],
            ["teeth_front_roughness", 0.4, "", "Custom/Front Roughness"],
            ["teeth_front_specular", 0.1, "", "Custom/Front Specular"],
            ["teeth_front_ao", 1, "", "Custom/Front AO"],
            ["teeth_rear_ao", 0, "", "Custom/Back AO"],
            ["teeth_rear_roughness", 1, "", "Custom/Back Roughness"],
            ["teeth_rear_specular", 0, "", "Custom/Back Specular"],
            ["teeth_gums_subsurface_scatter", 1, "", "Custom/Gums Scatter"],
            ["teeth_teeth_subsurface_scatter", 0.5, "", "Custom/Teeth Scatter"],
            ["teeth_ao_strength", 1, "", "Pbr/AO"],
            ["teeth_normal_strength", 1, "", "Pbr/Normal"],
            ["teeth_emission_strength", 0, "", "Pbr/Glow"],
            ["teeth_subsurface_falloff", (0.381, 0.198, 0.13, 1.0), "func_color_bytes", "SSS/Falloff"],
            ["teeth_subsurface_radius", 1, "", "SSS/Radius"],
            # non json properties (just defaults)
            ["teeth_ao_power", 1, "DEF"],
            ["teeth_gums_hue", 0.5, "", "/Diffuse Hue"],
            ["teeth_gums_hsv_strength", 1, "DEF"],
            ["teeth_teeth_hsv_strength", 1, "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["Custom/Teeth Desaturation", 0.1, "func_one_minus", "teeth_teeth_saturation"],
            ["Custom/Gums Desaturation", 0.0, "func_one_minus", "teeth_gums_saturation"],
            ["SSS/Falloff", [116.0, 123.0, 101.0], "func_export_byte3", "teeth_subsurface_falloff"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "AO Strength", "teeth_ao_strength", True, "AO Map"],
            ["PROP", "AO Darken", "teeth_ao_power", True, "AO Map"],
            ["PROP", "Front AO", "teeth_front_ao", True, "Gradient AO Map"],
            ["PROP", "Back AO", "teeth_rear_ao", True, "Gradient AO Map"],
            ["SPACER"],
            ["TRIPLET", "Teeth HSV", "teeth_teeth_hue", "teeth_teeth_saturation", "teeth_teeth_brightness", True, "Diffuse Map"],
            ["PROP", "*Teeth HSV Strength", "teeth_teeth_hsv_strength", True, "Diffuse Map"],
            ["SPACER"],
            ["TRIPLET", "Gums HSV", "teeth_gums_hue", "teeth_gums_saturation", "teeth_gums_brightness", True, "Diffuse Map"],
            ["PROP", "*Gums HSV Strength", "teeth_gums_hsv_strength", True, "Diffuse Map"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Front Roughness", "teeth_front_roughness", True],
            ["PROP", "Front Specular", "teeth_front_specular", True],
            ["PROP", "Back Roughness", "teeth_rear_roughness", True],
            ["PROP", "Back Specular", "teeth_rear_specular", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "Teeth Subsurface Weight", "teeth_teeth_subsurface_scatter", True],
            ["PROP", "Gums Subsurface Weight", "teeth_gums_subsurface_scatter", True],
            ["PROP", "Subsurface Falloff", "teeth_subsurface_falloff", False],
            ["PROP", "Subsurface Radius", "teeth_subsurface_radius", True],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Normal Strength", "teeth_normal_strength", True, "Normal Map"],
            ["PROP", "Micro Normal Strength", "teeth_micro_normal_strength", True, "Micro Normal Map"],
            ["PROP", "Micro Normal Tiling", "teeth_micro_normal_tiling", True, "Micro Normal Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "*Emissive Color", "teeth_emissive_color", False],
            ["PROP", "Emission Strength", "teeth_emission_strength", True],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Two Side": False,
            "Diffuse Color": [ 225.0, 225.0, 225.0 ],
            "Ambient Color": [ 125.0, 125.0, 125.0 ],
            "Specular Color": [ 229.5, 229.5, 229.5 ],
            "Opacity": 1.0,
            "Self Illumination": 0.0,
            "Textures": {},
            "Custom Shader": {
                "Shader Name": "RLTeethGum",
                "Image": {},
                "Variable": {},
            },
            "Subsurface Scatter": {
                "Falloff": [ 166.0, 123.0, 101.0 ],
                "Radius": 1.0,
                "Distribution": 0.93,
                "IOR": 1.55,
                "DecayScale": 1.0,
                "Lerp": 0.9
            }
        },
    },

    # Eye Shader
    ##################################

    {   "name": ["rl_cornea_shader", "rl_eye_shader"],
        "rl_shader": "RLEye",
        "label": "Eye",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Subsurface Scale", "func_sss_eyes", "eye_subsurface_scale"],
            ["Subsurface Falloff", "", "eye_subsurface_falloff"],
            ["Subsurface Radius", "func_sss_radius_eyes_cycles", "eye_subsurface_radius"],
            ["Cornea Specular", "", "eye_cornea_specular"],
            ["Iris Specular", "", "eye_iris_specular"],
            ["Cornea Roughness", "", "eye_cornea_roughness"],
            ["Iris Roughness", "", "eye_iris_roughness"],
            ["Sclera Roughness", "", "eye_sclera_roughness"],
            ["AO Strength", "", "eye_ao_strength"],
            ["Sclera Scale", "", "eye_sclera_scale"],
            ["Sclera Color", "", "eye_sclera_color"],
            ["Sclera Hue", "", "eye_sclera_hue"],
            ["Sclera Saturation", "", "eye_sclera_saturation"],
            ["Sclera Brightness", "func_sclera_brightness", "eye_sclera_brightness"],
            ["Sclera HSV Strength", "", "eye_sclera_hsv"],
            ["Iris Scale", "func_iris_scale", "eye_iris_scale"],
            ["Iris Color", "", "eye_iris_color"],
            ["Iris Hue", "", "eye_iris_hue"],
            ["Iris Saturation", "", "eye_iris_saturation"],
            ["Iris Brightness", "func_iris_brightness", "eye_iris_brightness"],
            ["Iris HSV Strength", "", "eye_iris_hsv"],
            ["Iris Radius", "", "eye_iris_radius"],
            ["Iris Cloudy Color", "", "eye_iris_cloudy_color"],
            ["Iris Depth", "func_set_eye_depth", "eye_iris_depth"],
            ["Transmission Opacity", "", "eye_iris_transmission_opacity"],
            ["Limbus Width", "", "eye_limbus_width"],
            ["Limbus Dark Radius", "", "eye_limbus_dark_radius"],
            ["Limbus Dark Width", "", "eye_limbus_dark_width"],
            ["Limbus Color", "", "eye_limbus_color"],
            ["Limbus Shading", "", "eye_limbus_shading"],
            ["IOR", "", "eye_ior"],
            ["Shadow Radius", "", "eye_shadow_radius"],
            ["Shadow Hardness", "", "eye_shadow_hardness"],
            ["Corner Shadow Color", "", "eye_corner_shadow_color"],
            ["Color Blend Strength", "func_half", "eye_color_blend_strength"],
            ["Sclera Emissive Color", "", "eye_sclera_emissive_color"],
            ["Sclera Emission Strength", "func_emission_scale", "eye_sclera_emission_strength"],
            ["Iris Emissive Color",  "","eye_iris_emissive_color"],
            ["Iris Emission Strength", "func_emission_scale", "eye_iris_emission_strength"],
            ["Sclera Normal Strength", "func_normal_strength", "eye_sclera_normal_strength"],
            ["Blood Vessel Height", "func_divide_1000", "eye_blood_vessel_height"],
            ["Iris Bump Height", "func_divide_1000", "eye_iris_bump_height"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_sss_radius_eyes_eevee", "eye_subsurface_radius", "eye_subsurface_falloff"]
        ],
        # modifier properties:
        # [prop_name, material_type, modifier_type, modifier_id, expression]
        "modifiers": [
            [ "eye_iris_depth", "EYE_RIGHT", "DISPLACE", "Eye_Displace_R", "mod.strength = 1.5 * parameters.eye_iris_depth"],
            [ "eye_pupil_scale", "EYE_RIGHT", "UV_WARP", "Eye_UV_Warp_R", "mod.scale = (1.0 / parameters.eye_pupil_scale, 1.0 / parameters.eye_pupil_scale)" ],
            [ "eye_iris_depth", "EYE_LEFT", "DISPLACE", "Eye_Displace_L", "mod.strength = 1.5 * parameters.eye_iris_depth"],
            [ "eye_pupil_scale", "EYE_LEFT", "UV_WARP", "Eye_UV_Warp_L", "mod.scale = (1.0 / parameters.eye_pupil_scale, 1.0 / parameters.eye_pupil_scale)" ],
        ],
        # material setting properties:
        # [prop_name, material_type, expression]
        "settings": [
            ["eye_refraction_depth", "CORNEA_LEFT", "mat.refraction_depth = parameters.eye_refraction_depth / 1000.0"],
            ["eye_refraction_depth", "CORNEA_RIGHT", "mat.refraction_depth = parameters.eye_refraction_depth / 1000.0"],
        ],
        # texture inputs:
        # [input_socket_color, input_socket_alpha, texture_type, tiling_prop, tiling_mode]
        "textures": [
            ["Sclera Diffuse Map", "", "SCLERA", "CENTERED", "func_tiling", "eye_sclera_scale"],
            # EYE_PARALLAX tells it to use a parallax mapping node, unless in SSR mode in which it behaves as a CENTERED mapping node
            ["Cornea Diffuse Map", "", "DIFFUSE", "EYE_PARALLAX", "func_parallax_iris_tiling", "eye_iris_scale", "eye_sclera_scale"],
            ["Color Blend Map", "", "EYEBLEND"],
            ["AO Map", "", "AO"],
            ["Metallic Map", "", "METALLIC"],
            ["Sclera Normal Map", "", "SCLERANORMAL", "OFFSET", "", "eye_sclera_normal_tiling"],
            ["Sclera Emission Map", "", "EMISSION"],
            ["Iris Emission Map", "", "EMISSION"],
        ],
        "mapping": [
            ["DIFFUSE"], # The Parallax mapping node is updated with these params, not the mapping params in the textures above.
            ["EYE_PARALLAX", "Iris Scale", "func_parallax_iris_scale", "eye_iris_scale", "eye_sclera_scale"],
            ["EYE_PARALLAX", "Iris Radius", "", "eye_iris_radius"],
            ["EYE_PARALLAX", "Pupil Scale", "", "eye_pupil_scale"],
            ["EYE_PARALLAX", "Depth Radius", "", "eye_iris_depth_radius"],
            ["EYE_PARALLAX", "Depth", "func_set_parallax_iris_depth", "eye_iris_depth"],
            ["EYE_PARALLAX", "IOR", "", "eye_ior"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["eye_color_blend_strength", 0.1, "", "Custom/BlendMap2 Strength"],
            ["eye_shadow_radius", 0.279, "", "Custom/Shadow Radius"],
            ["eye_shadow_hardness", 0.5, "", "Custom/Shadow Hardness"],
            ["eye_cornea_specular", 0.8, "", "Custom/Specular Scale"],
            ["eye_corner_shadow_color", (1.0, 0.497, 0.445, 1.0), "func_color_bytes", "Custom/Eye Corner Darkness Color"],
            ["eye_iris_depth", 0.5, "func_get_eye_depth", "Custom/Iris Depth Scale"],
            ["eye_cornea_roughness", 0, "", "Custom/_Iris Roughness"],
            ["eye_iris_brightness", 1, "", "Custom/Iris Color Brightness"],
            ["eye_pupil_scale", 1, "", "Custom/Pupil Scale"],
            ["eye_ior", 1.4, "", "Custom/_IoR"],
            ["eye_iris_scale", 1, "func_get_iris_scale", "Custom/Iris UV Radius"],
            ["eye_iris_radius", 0.16, "", "Custom/Iris UV Radius"],
            ["eye_iris_color", (1.0, 1.0, 1.0, 1.0), "func_color_bytes", "Custom/Iris Color"],
            ["eye_iris_inner_color", (1.0, 1.0, 1.0, 1.0), "func_color_bytes", "Custom/Iris Inner Color"],
            ["eye_iris_inner_scale", 0, "", "Custom/Iris Inner Scale"],
            ["eye_iris_cloudy_color", (0, 0, 0, 1.0), "func_color_bytes", "Custom/Iris Cloudy Color"],
            ["eye_limbus_width", 0.055, "", "Custom/Limbus UV Width Color"],
            ["eye_limbus_dark_radius", 0.13125, "func_limbus_dark_radius", "Custom/Limbus Dark Scale"],
            ["eye_limbus_dark_width", 1.0 - 0.34375, "func_limbus_dark_width", "Custom/Limbus Dark Scale"],
            ["eye_sclera_brightness", 0.650, "", "Custom/ScleraBrightness"],
            ["eye_sclera_roughness", 0.2, "", "Custom/Sclera Roughness"],
            ["eye_sclera_normal_strength", 0.1, "func_one_minus", "Custom/Sclera Flatten Normal"],
            ["eye_sclera_normal_tiling", 2, "func_tiling", "Custom/Sclera Normal UV Scale"],
            ["eye_sclera_scale", 0.93, "", "Custom/Sclera UV Radius"],
            ["eye_ao_strength", 0.2, "", "Pbr/AO"],
            ["eye_normal_strength", 1, "", "Pbr/Normal"],
            ["eye_sclera_emission_strength", 0, "", "Pbr/Glow"],
            ["eye_iris_emission_strength", 0, "", "Pbr/Glow"],
            ["eye_subsurface_falloff", (1,1,1,1), "func_color_bytes", "SSS/Falloff"],
            ["eye_subsurface_radius", 5, "", "SSS/Radius"],
            # non json properties (just defaults)
            ["eye_subsurface_scale", 1.0, "DEF"],
            ["eye_iris_depth_radius", 0.88, "DEF"],
            ["eye_refraction_depth", 2.5, "DEF"],
            ["eye_blood_vessel_height", 0.5, "DEF"],
            ["eye_iris_bump_height", 1, "DEF"],
            ["eye_iris_roughness", 1, "DEF"],
            ["eye_iris_transmission_opacity", 0.85, "DEF"],
            ["eye_sclera_hue", 0.5, "DEF"],
            ["eye_sclera_saturation", 1, "DEF"],
            ["eye_sclera_hsv", 1, "DEF"],
            ["eye_iris_hue", 0.5, "", "/Diffuse Hue"],
            ["eye_iris_saturation", 1, "func_saturation_mod", "/Diffuse Saturation"],
            ["eye_iris_hsv", 1, "DEF"],
            ["eye_limbus_shading", 0.2, "DEF"],
            #["eye_limbus_dark_width", 1.0 - 0.34375, "DEF"],
            ["eye_limbus_color", (0.0, 0.0, 0.0, 1), "DEF"],
            ["eye_sclera_color", (1.0, 1.0, 1.0, 1), "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["Custom/Limbus Dark Scale", 6.5, "func_export_limbus_dark_scale", "eye_limbus_dark_radius"],
            ["Custom/Eye Corner Darkness Color", [255.0, 188.0, 179.0], "func_export_byte3", "eye_corner_shadow_color"],
            ["Custom/Iris Color", [255.0, 255.0, 255.0], "func_export_byte3", "eye_iris_color"],
            ["Custom/Iris Color Brightness", 1.0, "func_export_brightness", "eye_iris_brightness"],
            ["/Diffuse Saturation", 1.0, "func_export_saturation_mod", "eye_iris_saturation"],
            ["Custom/Iris Inner Color", [255.0, 255.0, 255.0], "func_export_byte3", "eye_iris_inner_color"],
            ["Custom/Iris Cloudy Color", [0, 0, 0], "func_export_byte3", "eye_iris_cloudy_color"],
            ["Custom/Iris Depth Scale", 0.5, "func_export_eye_depth", "eye_iris_depth"],
            ["Custom/Sclera Flatten Normal", 0.9, "func_one_minus", "eye_sclera_normal_strength"],
            ["Custom/Sclera Normal UV Scale", 0.5, "func_tiling", "eye_sclera_normal_tiling"],
            ["SSS/Falloff", [255.0, 255.0, 255.0], "func_export_byte3", "eye_subsurface_falloff"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "AO Strength", "eye_ao_strength", True, "AO Map"],
            ["PROP", "Color Blend", "eye_color_blend_strength", True, "Color Blend Map"],
            ["SPACER"],
            ["PROP", "*Sclera Color", "eye_sclera_color", False],
            ["TRIPLET", "*Sclera HSV", "eye_sclera_hue", "eye_sclera_saturation", "eye_sclera_brightness", True],
            ["PROP", "*Sclera HSV Strength", "eye_sclera_hsv", True],
            ["SPACER"],
            ["PROP", "Iris Color", "eye_iris_color", False],
            ["TRIPLET", "Iris HSV", "eye_iris_hue", "eye_iris_saturation", "eye_iris_brightness", True],
            ["PROP", "*Iris HSV Strength", "eye_iris_hsv", True],
            ["SPACER"],
            ["PROP", "Iris Cloudy Color", "eye_iris_cloudy_color", False],
            ["PROP", "Iris Radius", "eye_iris_radius", True],
            ["PROP", "Limbus Width", "eye_limbus_width", True],
            ["PROP", "Dark Radius", "eye_limbus_dark_radius", True],
            ["PROP", "*Dark Width", "eye_limbus_dark_width", True],
            ["PROP", "*Limbus Color", "eye_limbus_color", False],
            ["PROP", "*Limbus Shading", "eye_limbus_shading", True],
            ["HEADER",  "Eye Shape", "SPHERE"],
            ["PROP", "Sclera Scale", "eye_sclera_scale", True],
            ["PROP", "Iris Scale", "eye_iris_scale", True],
            ["HEADER",  "Corner Shadow", "SHADING_RENDERED"],
            ["PROP", "Shadow Radius", "eye_shadow_radius", True],
            ["PROP", "Shadow Hardness", "eye_shadow_hardness", True],
            ["PROP", "Shadow Color", "eye_corner_shadow_color", False],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Cornea Specular", "eye_cornea_specular", True],
            ["PROP", "Iris Specular", "eye_iris_specular", True],
            ["PROP", "Sclera Roughness", "eye_sclera_roughness", True],
            ["PROP", "*Iris Roughness", "eye_iris_roughness", True],
            ["PROP", "Cornea Roughness", "eye_cornea_roughness", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "*Weight", "eye_subsurface_scale", True],
            ["PROP", "Falloff", "eye_subsurface_falloff", False],
            ["PROP", "Radius", "eye_subsurface_radius", True],
            ["HEADER",  "Depth & Refraction", "MOD_THICKNESS"],
            ["PROP", "Iris Depth", "eye_iris_depth", True],
            ["PROP", "*Transmission Opacity", "eye_iris_transmission_opacity", True, ">Transmission Alpha"],
            ["PROP", "*Depth Radius", "eye_iris_depth_radius", True],
            ["PROP", "Pupil Scale", "eye_pupil_scale", True],
            ["PROP", "IOR", "eye_ior", True],
            ["PROP", "*Refraction Depth", "eye_refraction_depth", True],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Sclera Normal Strength", "eye_sclera_normal_strength", True], "Sclera Normal Map",
            ["PROP", "Sclera Normal Tiling", "eye_sclera_normal_tiling", True, "Sclera Normal Map"],
            ["PROP", "*Blood Vessel Height", "eye_blood_vessel_height", True, "Sclera Diffuse Map"],
            ["PROP", "*Iris Bump Height", "eye_iris_bump_height", True, "Cornea Diffuse Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Sclera Emissive Color", "eye_sclera_emissive_color", False],
            ["PROP", "Sclera Emission Strength", "eye_sclera_emission_strength", True],
            ["PROP", "Iris Emissive Color", "eye_iris_emissive_color", False],
            ["PROP", "Iris Emission Strength", "eye_iris_emission_strength", True],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Two Side": False,
            "Diffuse Color": [ 255.0, 255.0, 255.0 ],
            "Ambient Color": [ 50.0, 50.0, 50.0 ],
            "Specular Color": [ 0.0, 0.0, 0.0 ],
            "Opacity": 0.8,
            "Self Illumination": 0.0,
            "Textures": {},
            "Custom Shader": {
                "Shader Name": "RLEye",
                "Image": {},
                "Variable": {}
            },
            "Subsurface Scatter": {
                "Falloff": [ 255.0, 255.0, 255.0 ],
                "Radius": 5.0,
                "Distribution": 0.93,
                "IOR": 1.55,
                "DecayScale": 1.0,
                "Lerp": 0.85
            }
        },
    },

    # PBR Shader
    ############################################################

    {   "name": "rl_pbr_shader",
        "rl_shader": "Pbr",
        "label": "PBR Material",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Diffuse Color", "", "default_diffuse_color"],
            ["AO Strength", "", "default_ao_strength"],
            ["AO Power", "", "default_ao_power"],
            ["Blend Multiply Strength", "", "default_blend_multiply_strength"],
            ["Metallic Map", "", "default_metallic"],
            ["Specular Map", "", "default_specular"],
            ["Roughness Map", "", "default_roughness"],
            ["Specular Strength", "", "default_specular_strength"],
            ["Specular Scale", "", "default_specular_scale"],
            ["Roughness Power", "", "default_roughness_power"],
            ["Roughness Min", "", "default_roughness_min"],
            ["Roughness Max", "", "default_roughness_max"],
            ["Alpha Strength", "", "default_alpha_strength"],
            ["Opacity", "", "default_opacity"],
            ["Normal Strength", "func_normal_strength", "default_normal_strength"],
            ["Bump Strength", "func_divide_100", "default_bump_strength"],
            ["Emissive Color", "", "default_emissive_color"],
            ["Emission Strength", "func_emission_scale", "default_emission_strength"],
            ["Displacement Strength", "func_divide_200", "default_displacement_strength"],
            ["Displacement Base", "", "default_displacement_base"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Clearcoat", "", "default_reflection_strength"],
            ["Clearcoat Roughness", "", "default_reflection_blur"],
        ],
        # texture inputs:
        # [input_socket_color, input_socket_alpha, texture_type, tiling_prop, tiling_mode]
        "textures": [
            ["Diffuse Map", "", "DIFFUSE"],
            ["AO Map", "", "AO"],
            ["Blend Multiply", "", "BLEND1"],
            ["Metallic Map", "", "METALLIC"],
            ["Specular Map", "", "SPECULAR"],
            ["Roughness Map", "", "ROUGHNESS"],
            ["Alpha Map", "", "ALPHA"],
            ["Normal Map", "", "NORMAL"],
            ["Bump Map", "", "BUMP"],
            ["Emission Map", "", "EMISSION"],
            ["Displacement Map", "", "DISPLACE"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["default_ao_strength", 1, "", "Pbr/AO"],
            ["default_diffuse_color", (1,1,1,1), "func_color_bytes", "/Diffuse Color"],
            ["default_blend_multiply_strength", 0, "", "Pbr/Blend"],
            ["default_alpha_strength", 1, "", "Pbr/Opacity"],
            ["default_opacity", 1, "", "Base/Opacity"],
            ["default_normal_strength", 1, "", "Pbr/Normal"],
            ["default_emission_strength", 0, "", "Pbr/Glow"],
            ["default_displacement_strength", 0, "", "Pbr/Displacement"],
            ["default_displacement_base", 0.5, "", "Pbr/Displacement/Gray-scale Base Value"],
            ["default_bump_strength", 1, "func_divide_2", "Pbr/Bump"],
            ["default_specular_strength", 1, "", "Pbr/Specular"],
            ["default_metallic", 0, "", "Pbr/Metallic"],
            ["default_reflection_strength", 0, "", "Reflection/Reflection Strength"],
            ["default_reflection_blur", 0, "", "Reflection/Reflection Blur"],
            # non json properties (just defaults)
            ["default_ao_power", 1, "DEF"],
            ["default_specular_scale", 1.0, "DEF"],
            ["default_roughness_power", 1, "DEF"],
            ["default_roughness_min", 0, "DEF"],
            ["default_roughness_max", 1, "DEF"],
            ["default_emissive_color", (1,1,1,1), "DEF"],
            ["default_specular", [0.5, 1.0], "DEF"],
            ["default_roughness", [0.0, 0.25], "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["/Diffuse Color", [255.0, 255.0, 255.0], "func_export_byte3", "default_diffuse_color"],
            ["Pbr/Bump", 1.0, "func_mul_2", "default_bump_strength"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "Color", "default_diffuse_color", True],
            ["PROP", "AO Strength", "default_ao_strength", True, "AO Map"],
            ["PROP", "AO Darken", "default_ao_power", True, "AO Map"],
            ["PROP", "Blend Multiply", "default_blend_multiply_strength", True, "Blend Multiply"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Metallic", "default_metallic", True, "!Metallic Map"],
            ["PROP", "*Specular", "default_specular", True, "!Specular Map"],
            ["PROP", "Specular Map", "default_specular_strength", True, "Specular Map"],
            ["PROP", "*Specular Scale", "default_specular_scale", True],
            ["PROP", "Roughness", "default_roughness", True, "!Roughness Map"],
            ["PROP", "*Roughness Power", "default_roughness_power", True],
            ["PAIR", "Roughness Range", "default_roughness_min", "default_roughness_max", True],
            ["PROP", "Coat Strength", "default_reflection_strength", True],
            ["PROP", "Coat Roughness", "default_reflection_blur", True],
            ["HEADER",  "Opacity", "MOD_OPACITY"],
            ["PROP", "Alpha Strength", "default_alpha_strength", True],
            ["PROP", "Opacity", "default_opacity", True],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Normal Strength", "default_normal_strength", True, "Normal Map"],
            ["PROP", "Bump Strength", "default_bump_strength", True, "Bump Map"],
            ["PROP", "Displacement", "default_displacement_strength", True, "Displacement Map"],
            ["PROP", "Displacement Base", "default_displacement_base", True, "Displacement Map"],
            ["OP", "Convert Bump", "cc3.bake", "PLAY", "BAKE_BUMP_NORMAL", "Bump Map", "!Normal Map"],
            ["OP", "Combine Normals", "cc3.bake", "PLAY", "BAKE_BUMP_NORMAL", "Bump Map", "Normal Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Emissive Color", "default_emissive_color", False],
            ["PROP", "Emission Strength", "default_emission_strength", True],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Two Side": True,
            "Diffuse Color": [ 150.0, 150.0, 150.0 ],
            "Ambient Color": [ 150.0, 150.0, 150.0 ],
            "Specular Color": [ 229.5, 229.5, 229.5 ],
            "Opacity": 1.0,
            "Self Illumination": 0.0,
            "Textures": {}
        },
    },

    # SSS Shader
    #########################################

    {   "name": "rl_sss_shader",
        "rl_shader": "RLSSS",
        "label": "SSS Material",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Diffuse Color", "", "default_diffuse_color"],
            ["AO Strength", "", "default_ao_strength"],
            ["AO Power", "", "default_ao_power"],
            ["Blend Multiply Strength", "", "default_blend_multiply_strength"],
            ["Metallic Map", "", "default_metallic"],
            ["Specular Map", "", "default_specular"],
            ["Roughness Map", "", "default_roughness"],
            ["Specular Strength", "", "default_specular_strength"],
            ["Specular Scale", "", "default_specular_scale"],
            ["Roughness Power", "", "default_roughness_power"],
            ["Roughness Min", "", "default_roughness_min"],
            ["Roughness Max", "", "default_roughness_max"],
            ["Alpha Strength", "", "default_alpha_strength"],
            ["Opacity", "", "default_opacity"],
            ["Normal Strength", "func_normal_strength", "default_normal_strength"],
            ["Bump Strength", "func_divide_100", "default_bump_strength"],
            ["Emissive Color", "", "default_emissive_color"],
            ["Emission Strength", "func_emission_scale", "default_emission_strength"],
            ["Displacement Strength", "func_divide_200", "default_displacement_strength"],
            ["Displacement Base", "", "default_displacement_base"],
            ["Micro Normal Strength", "func_micro_normal_strength", "default_micro_normal_strength"],
            ["Subsurface Scale", "func_sss_default", "default_subsurface_scale"],
            ["Unmasked Scatter Scale", "", "default_unmasked_scatter_scale"],
            ["R Scatter Scale", "", "default_r_scatter_scale"],
            ["G Scatter Scale", "", "default_g_scatter_scale"],
            ["B Scatter Scale", "", "default_b_scatter_scale"],
            ["A Scatter Scale", "", "default_a_scatter_scale"],
            ["Micro Roughness Mod", "", "default_micro_roughness_mod"],
            ["Unmasked Roughness Mod", "", "default_unmasked_roughness_mod"],
            ["R Roughness Mod", "", "default_r_roughness_mod"],
            ["G Roughness Mod", "", "default_g_roughness_mod"],
            ["B Roughness Mod", "", "default_b_roughness_mod"],
            ["A Roughness Mod", "", "default_a_roughness_mod"],
            ["Hue", "", "default_hue"],
            ["Brightness", "", "default_brightness"],
            ["Saturation", "", "default_saturation"],
            ["HSV Strength", "", "default_hsv_strength"],
            ["Metallic Map", "", "default_metallic"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_sss_radius_default_eevee", "default_subsurface_radius", "default_subsurface_falloff"],
            ["Clearcoat", "", "default_reflection_strength"],
            ["Clearcoat Roughness", "", "default_reflection_blur"],
        ],
        # texture inputs:
        # [input_socket_color, input_socket_alpha, texture_type, tiling_prop, tiling_mode]
        "textures": [
            ["Diffuse Map", "", "DIFFUSE"],
            ["AO Map", "", "AO"],
            ["Blend Multiply", "", "BLEND1"],
            ["Metallic Map", "", "METALLIC"],
            ["Specular Map", "", "SPECULAR"],
            ["Roughness Map", "", "ROUGHNESS"],
            ["Alpha Map", "", "ALPHA"],
            ["Normal Map", "", "NORMAL"],
            ["Bump Map", "", "BUMP"],
            ["Emission Map", "", "EMISSION"],
            ["Displacement Map", "", "DISPLACE"],
            ["Subsurface Map", "", "SSS"],
            ["Transmission Map", "", "TRANSMISSION"],
            ["Micro Normal Map", "", "MICRONORMAL", "OFFSET", "", "default_micro_normal_tiling"],
            ["Micro Normal Mask", "", "MICRONMASK"],
            ["RGBA Map", "RGBA Alpha", "RGBAMASK"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["default_diffuse_color", (1,1,1,1), "func_color_bytes", "/Diffuse Color"],
            ["default_specular_scale", 1.0, "", "Custom/_Specular"],
            #["default_brightness", 1, "", "Custom/_BaseColorMap Brightness"],
            #["default_saturation", 1, "", "Custom/_BaseColorMap Saturation"],
            ["default_ao_strength", 1, "", "Pbr/AO"],
            ["default_blend_multiply_strength", 0, "", "Pbr/Blend"],
            ["default_alpha_strength", 1, "", "Pbr/Opacity"],
            ["default_opacity", 1, "", "Base/Opacity"],
            ["default_normal_strength", 1, "", "Pbr/Normal"],
            ["default_emission_strength", 0, "", "Pbr/Glow"],
            ["default_displacement_strength", 1, "", "Pbr/Displacement"],
            ["default_micro_normal_tiling", 25, "", "Custom/MicroNormal Tiling"],
            ["default_micro_normal_strength", 0.8, "", "Custom/MicroNormal Strength"],
            ["default_micro_roughness_mod", 0.05, "", "Custom/Micro Roughness Scale"],
            ["default_r_roughness_mod", 0.0, "", "Custom/R Channel Roughness Scale"],
            ["default_g_roughness_mod", 0.0, "", "Custom/G Channel Roughness Scale"],
            ["default_b_roughness_mod", 0.0, "", "Custom/B Channel Roughness Scale"],
            ["default_a_roughness_mod", 0.0, "", "Custom/A Channel Roughness Scale"],
            ["default_unmasked_roughness_mod", 0.0, "", "Custom/Unmasked Roughness Scale"],
            ["default_r_scatter_scale", 1, "", "Custom/R Channel Scatter Scale"],
            ["default_g_scatter_scale", 1, "", "Custom/G Channel Scatter Scale"],
            ["default_b_scatter_scale", 1, "", "Custom/B Channel Scatter Scale"],
            ["default_a_scatter_scale", 1, "", "Custom/A Channel Scatter Scale"],
            ["default_unmasked_scatter_scale", 1, "", "Custom/Unmasked Scatter Scale"],
            ["default_subsurface_falloff", (1.0, 1.0, 1.0, 1.0), "func_color_bytes", "SSS/Falloff"],
            ["default_suburface_radius", 1.5, "", "SSS/Radius"],
            ["default_specular_strength", 1, "", "Pbr/Specular"],
            ["default_metallic", 0, "", "Pbr/Metallic"],
            ["default_displacement_strength", 0, "", "Pbr/Displacement"],
            ["default_displacement_base", 0.5, "", "Pbr/Displacement/Gray-scale Base Value"],
            ["default_bump_strength", 1, "func_divide_2", "Pbr/Bump"],
            ["default_reflection_strength", 0, "", "Reflection/Reflection Strength"],
            ["default_reflection_blur", 0, "", "Reflection/Reflection Blur"],
            # non json properties (just defaults)
            ["default_ao_power", 1, "DEF"],
            ["default_specular", [0.5, 1.0], "DEF"],
            ["default_roughness", [0.0, 0.25], "DEF"],
            ["default_hue", 0.5, "", "/Diffuse Hue"],
            ["default_saturation", 1.0, "func_saturation_mod", "/Diffuse Saturation"],
            ["default_brightness", 1.0, "func_brightness_mod", "/Diffuse Brightness"],
            ["default_hsv_strength", 1, "DEF"],
            ["default_specular_mask", 1.0, "DEF"],
            ["default_roughness_power", 1.0, "DEF"],
            ["default_roughness_min", 0, "DEF"],
            ["default_roughness_max", 1, "DEF"],
            ["default_subsurface_scale", 1, "DEF"],
            ["default_emissive_color", (1,1,1,1), "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["/Diffuse Color", [255.0, 255.0, 255.0], "func_export_byte3", "default_saturation"],
            ["/Diffuse Brightness", 1.0, "func_export_brightness_mod", "default_brightness"],
            ["/Diffuse Saturation", 1.0, "func_export_saturation_mod", "default_saturation"],
            ["SSS/Falloff", [255.0, 255.0, 255.0], "func_export_byte3", "default_subsurface_falloff"],
            ["Pbr/Bump", 1.0, "func_mul_2", "default_bump_strength"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "Color", "default_diffuse_color", True],
            ["TRIPLET", "HSV", "default_hue", "default_saturation", "default_brightness", True],
            ["PROP", "*HSV Strength", "default_hsv_strength", True],
            ["PROP", "AO Strength", "default_ao_strength", True, "AO Map"],
            ["PROP", "AO Darken", "default_ao_power", True, "AO Map"],
            ["PROP", "Blend Multiply", "default_blend_multiply_strength", True, "Blend Multiply"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Metallic", "default_metallic", True, "!Metallic Map"],
            ["PROP", "*Specular", "default_specular", True, "!Specular Map"],
            ["PROP", "Specular Map", "default_specular_strength", True, "Specular Map"],
            ["PROP", "Specular Scale", "default_specular_scale", True],
            ["PROP", "Roughness", "default_roughness", True, "!Roughness Map"],
            ["PROP", "*Roughness Power", "default_roughness_power", True],
            ["PAIR", "Roughness Range", "default_roughness_min", "default_roughness_max", True],
            ["PROP", "Coat Strength", "default_reflection_strength", True],
            ["PROP", "Coat Roughness", "default_reflection_blur", True],
            ["SPACER"],
            ["PROP", "Micro Roughness Mod", "default_micro_roughness_mod", True],
            ["PROP", "R Roughness Mod", "default_r_roughness_mod", True, "RGBA Map"],
            ["PROP", "G Roughness Mod", "default_g_roughness_mod", True, "RGBA Map"],
            ["PROP", "B Roughness Mod", "default_b_roughness_mod", True, "RGBA Map"],
            ["PROP", "A Roughness Mod", "default_a_roughness_mod", True, "RGBA Map"],
            ["PROP", "Unmasked Roughness Mod", "default_unmasked_roughness_mod", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "Weight", "default_subsurface_scale", True],
            ["PROP", "Falloff", "default_subsurface_falloff", False],
            ["PROP", "Radius", "default_subsurface_radius", True],
            ["SPACER"],
            ["PROP", "R Scatter Scale", "default_r_scatter_scale", True, "RGBA Map"],
            ["PROP", "G Scatter Scale", "default_g_scatter_scale", True, "RGBA Map"],
            ["PROP", "B Scatter Scale", "default_b_scatter_scale", True, "RGBA Map"],
            ["PROP", "A Scatter Scale", "default_a_scatter_scale", True, "RGBA Map"],
            ["PROP", "Unmasked Scatter Scale", "default_unmasked_scatter_scale", True],
            ["HEADER",  "Opacity", "MOD_OPACITY"],
            ["PROP", "Alpha Strength", "default_alpha_strength", True],
            ["PROP", "Opacity", "default_opacity", True],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Normal Strength", "default_normal_strength", True, "Normal Map"],
            ["PROP", "Bump Strength", "default_bump_strength", True, "Bump Map"],
            ["PROP", "Displacement", "default_displacement_strength", True, "Displacement Map"],
            ["PROP", "Displacement Base", "default_displacement_base", True, "Displacement Map"],
            ["OP", "Convert Bump", "cc3.bake", "PLAY", "BAKE_BUMP_NORMAL", "Bump Map", "!Normal Map"],
            ["OP", "Combine Normals", "cc3.bake", "PLAY", "BAKE_BUMP_NORMAL", "Bump Map", "Normal Map"],
            ["SPACER"],
            ["PROP", "Micro Normal Strength", "default_micro_normal_strength", True, "Micro Normal Map"],
            ["PROP", "Micro Normal Tiling", "default_micro_normal_tiling", True, "Micro Normal Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Emissive Color", "default_emissive_color", False],
            ["PROP", "Emission Strength", "default_emission_strength", True],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Two Side": True,
            "Diffuse Color": [ 255.0, 255.0, 255.0 ],
            "Ambient Color": [ 255.0, 255.0, 255.0 ],
            "Specular Color": [ 229.0, 229.0, 229.0 ],
            "Opacity": 1.0,
            "Self Illumination": 0.0,
            "Textures": {},
            "Custom Shader": {
                "Shader Name": "RLSSS",
                "Image": {},
                "Variable": {},
            },
            "Subsurface Scatter": {
                "Falloff": [ 255.0, 255.0, 255.0 ],
                "Radius": 13.0,
                "Distribution": 0.85,
                "IOR": 1.55,
                "DecayScale": 0.05,
                "Lerp": 0.5
            }
        },
    },

    # Hair Shader
    #####################################

    {   "name": "rl_hair_shader",
        "rl_shader": "RLHair",
        "cycles": "rl_hair_cycles_shader",
        "label": "Hair",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Diffuse Color", "", "hair_diffuse_color"],
            ["Diffuse Hue", "", "hair_diffuse_hue"],
            ["Diffuse Saturation", "", "hair_diffuse_saturation"],
            ["Diffuse Brightness", "", "hair_diffuse_brightness"],
            ["Diffuse HSV", "", "hair_diffuse_hsv_strength"],
            ["Enable Color", "", "hair_enable_color"],
            ["Global Strength", "", "hair_global_strength"],
            ["Root Color Strength", "", "hair_root_color_strength"],
            ["End Color Strength", "", "hair_end_color_strength"],
            ["Invert Root Map", "", "hair_invert_root_map"],
            ["Base Color Strength", "", "hair_base_color_strength"],
            ["Root Color", "", "hair_root_color"],
            ["End Color", "", "hair_end_color"],
            ["Highlight A Color", "", "hair_highlight_a_color"],
            ["Highlight A Start", "", "hair_highlight_a_start"],
            ["Highlight A Mid", "", "hair_highlight_a_mid"],
            ["Highlight A End", "", "hair_highlight_a_end"],
            ["Highlight A Strength", "", "hair_highlight_a_strength"],
            ["Highlight A Overlap Invert", "", "hair_highlight_a_overlap_invert"],
            ["Highlight A Overlap End", "", "hair_highlight_a_overlap_end"],
            ["Highlight B Color", "", "hair_highlight_b_color"],
            ["Highlight B Start", "", "hair_highlight_b_start"],
            ["Highlight B Mid", "", "hair_highlight_b_mid"],
            ["Highlight B End", "", "hair_highlight_b_end"],
            ["Highlight B Strength", "", "hair_highlight_b_strength"],
            ["Highlight B Overlap Invert", "", "hair_highlight_b_overlap_invert"],
            ["Highlight B Overlap End", "", "hair_highlight_b_overlap_end"],
            ["Vertex Color Strength", "", "hair_vertex_color_strength"],
            ["Vertex Color", "", "hair_vertex_color"],
            ["Anisotropic", "", "hair_anisotropic"],
            ["Anisotropic Shift Min", "", "hair_anisotropic_shift_min"],
            ["Anisotropic Shift Max", "", "hair_anisotropic_shift_max"],
            ["Flow Invert Green", "", "hair_tangent_flip_green"],
            ["Anisotropic Roughness", "", "hair_anisotropic_roughness"],
            ["Anisotropic Strength", "", "hair_anisotropic_strength"],
            ["Specular Blend", "", "hair_specular_blend"],
            ["Anisotropic Color", "", "hair_anisotropic_color"],
            ["Subsurface Falloff", "func_sss_falloff_saturated", "hair_subsurface_falloff", "hair_subsurface_saturation"],
            ["Subsurface Scale", "func_sss_hair", "hair_subsurface_scale"],
            ["Subsurface Radius", "func_sss_radius_hair_cycles", "hair_subsurface_radius"],
            ["Diffuse Strength", "", "hair_diffuse_strength"],
            ["AO Strength", "", "hair_ao_strength"],
            ["AO Power", "", "hair_ao_power"],
            ["AO Occlude All", "", "hair_ao_occlude_all"],
            ["Blend Multiply Strength", "", "hair_blend_multiply_strength"],
            ["Specular Scale", "", "hair_specular_scale"],
            ["Roughness Strength", "", "hair_roughness_strength"],
            ["Alpha Strength", "", "hair_alpha_strength"],
            ["Alpha Power", "", "hair_alpha_power"],
            ["Opacity", "", "hair_opacity"],
            ["Normal Strength", "func_normal_strength", "hair_normal_strength"],
            ["Bump Strength", "func_divide_100", "hair_bump_strength"],
            ["Emissive Color", "", "hair_emissive_color"],
            ["Emission Strength", "func_emission_scale", "hair_emission_strength"],
            ["Displacement Strength", "func_divide_100", "hair_displacement_strength"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_sss_radius_hair_eevee", "hair_subsurface_radius", "hair_subsurface_falloff", "hair_subsurface_saturation"],
        ],
        # texture inputs:
        # [input_socket_color, input_socket_alpha, texture_type, tiling_prop, tiling_mode]
        "textures": [
            ["Diffuse Map", "", "DIFFUSE"],
            ["AO Map", "", "AO"],
            ["Blend Multiply", "", "BLEND1"],
            ["Metallic Map", "", "METALLIC"],
            ["Specular Map", "", "SPECULAR"],
            ["Specular Mask", "", "SPECMASK"],
            ["Roughness Map", "", "ROUGHNESS"],
            ["Alpha Map", "", "ALPHA"],
            ["Normal Map", "", "NORMAL"],
            ["Bump Map", "", "BUMP"],
            ["Emission Map", "", "EMISSION"],
            ["Displacement Map", "", "DISPLACE"], # use displacement for bump map in hair
            ["Root Map", "", "HAIRROOT"],
            ["ID Map", "", "HAIRID"],
            ["Flow Map", "", "HAIRFLOW"],
            ["Vertex Color", "", "HAIRVERTEXCOLOR", "SAMPLE", "hair_vertex_color"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["hair_diffuse_color", (1,1,1,1), "func_color_bytes", "/Diffuse Color"],
            ["hair_tangent_vector", (1, 0, 0), "func_color_vector", "Custom/TangentVectorColor"],
            ["hair_tangent_flip_green", 1, "", "Custom/TangentMapFlipGreen"],
            ["hair_anisotropic_shift_min", 0, "", "Custom/BlackColor Reflection Offset Z"],
            ["hair_anisotropic_shift_max", 0, "", "Custom/WhiteColor Reflection Offset Z"],
            ["hair_diffuse_strength", 1, "", "Custom/Diffuse Strength"],
            ["hair_roughness_strength", 0.724, "func_sqrt", "Custom/Hair Roughness Map Strength"],
            ["hair_specular_scale", 0.3, "", "Custom/Hair Specular Map Strength"],
            ["hair_anisotropic_strength", 0.8, "func_half", "Custom/Specular Strength"],
            ["hair_anisotropic_strength2", 1.0, "", "Custom/Secondary Specular Strength"],
            ["hair_vertex_color", (0,0,0,1), "func_color_bytes", "Custom/VertexGrayToColor"],
            ["hair_vertex_color_strength", 0, "", "Custom/VertexColorStrength"],
            ["hair_enable_color", 0, "", "Custom/ActiveChangeHairColor"],
            ["hair_base_color_strength", 1, "", "Custom/BaseColorMapStrength"],
            ["hair_root_color", (0.144129, 0.072272, 0.046665, 1.0), "func_color_bytes", "Custom/RootColor"],
            ["hair_end_color", (0.332452, 0.184475, 0.122139, 1.0), "func_color_bytes", "Custom/TipColor"],
            ["hair_global_strength", 0, "", "Custom/UseRootTipColor"],
            ["hair_root_color_strength", 1, "", "Custom/RootColorStrength"],
            ["hair_end_color_strength", 1, "", "Custom/TipColorStrength"],
            ["hair_invert_root_map", 0, "", "Custom/InvertRootTip"],
            ["hair_highlight_a_color", (0.502886, 0.323143, 0.205079, 1.0), "func_color_bytes", "Custom/_1st Dye Color"],
            ["hair_highlight_a_strength", 0.543, "", "Custom/_1st Dye Strength"],
            ["hair_highlight_a_start", 0.1, "func_index_b0", "Custom/_1st Dye Distribution from Grayscale"],
            ["hair_highlight_a_mid", 0.2, "func_index_b1", "Custom/_1st Dye Distribution from Grayscale"],
            ["hair_highlight_a_end", 0.3, "func_index_b2", "Custom/_1st Dye Distribution from Grayscale"],
            ["hair_highlight_a_overlap_end", 0.99, "", "Custom/Mask 1st Dye by RootMap"],
            ["hair_highlight_a_overlap_invert", 0.99, "", "Custom/Invert 1st Dye RootMap Mask"],
            ["hair_highlight_b_color", (1, 1, 1, 1.0), "func_color_bytes", "Custom/_2nd Dye Color"],
            ["hair_highlight_b_strength", 0, "", "Custom/_2nd Dye Strength"],
            ["hair_highlight_b_start", 0.5, "func_index_b0", "Custom/_2nd Dye Distribution from Grayscale"],
            ["hair_highlight_b_mid", 0.6, "func_index_b1", "Custom/_2nd Dye Distribution from Grayscale"],
            ["hair_highlight_b_end", 0.7, "func_index_b2", "Custom/_2nd Dye Distribution from Grayscale"],
            ["hair_highlight_b_overlap_end", 0, "", "Custom/Mask 2nd Dye by RootMap"],
            ["hair_highlight_b_overlap_invert", 0, "", "Custom/Invert 2nd Dye RootMap Mask"],
            ["hair_ao_strength", 1, "", "Pbr/AO"],
            ["hair_ao_occlude_all", 0, "", "Custom/AO Map Occlude All Lighting"],
            ["hair_blend_multiply_strength", 0, "", "Pbr/Blend"],
            ["hair_alpha_strength", 1, "", "Pbr/Opacity"],
            ["hair_opacity", 1, "", "Base/Opacity"],
            ["hair_normal_strength", 1.0, "", "Pbr/Normal"],
            ["hair_bump_strength", 1.0, "", "Pbr/Normal"],
            ["hair_emission_strength", 0, "", "Pbr/Glow"],
            ["hair_displacement_strength", 1, "", "Pbr/Displacement"],
            # non json properties (just defaults)
            ["hair_ao_power", 1, "DEF"],
            ["hair_diffuse_hue", 0.5, "", "/Diffuse Hue"],
            ["hair_diffuse_saturation", 1, "func_saturation_mod", "/Diffuse Saturation"],
            ["hair_diffuse_brightness", 1, "func_brightness_mod", "/Diffuse Brightness"],
            ["hair_subsurface_saturation", 1.0, "DEF"],
            ["hair_diffuse_hsv_strength", 1, "DEF"],
            ["hair_subsurface_radius", 1.5, "DEF"],
            ["hair_alpha_power", 1.0, "DEF"],
            ["hair_anisotropic_roughness", 0.0375, "DEF"],
            ["hair_specular_blend", 0.9, "DEF"],
            ["hair_anisotropic_color", (1.000000, 0.798989, 0.689939, 1.000000), "DEF"],
            ["hair_subsurface_falloff", (1.000000, 0.815931, 0.739236, 1.000000), "DEF"],

            ["hair_subsurface_falloff_mix", 0.5, "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["/Diffuse Color", [255.0, 255.0, 255.0], "func_export_byte3", "hair_diffuse_color"],
            ["/Diffuse Saturation", 1.0, "func_export_saturation_mod", "hair_diffuse_saturation"],
            ["/Diffuse Brightness", 1.0, "func_export_brightness_mod", "hair_diffuse_brightness"],
            ["/Diffuse HSV", 1.0, "", "hair_diffuse_hsv_strength"],
            ["Custom/TangentVectorColor", [255, 0, 0], "func_export_byte3", "hair_tangent_vector"],
            ["Custom/Hair Roughness Map Strength", 0.524, "func_pow_2", "hair_roughness_strength"],
            ["Custom/VertexGrayToColor", [0, 0, 0], "func_export_byte3", "hair_vertex_color"],
            ["Custom/RootColor", [37, 18, 11], "func_export_byte3", "hair_root_color"],
            ["Custom/TipColor", [86, 48, 31], "func_export_byte3", "hair_end_color"],
            ["Custom/_1st Dye Color", [182, 125, 79], "func_export_byte3", "hair_highlight_a_color"],
            ["Custom/_2nd Dye Color", [255, 255, 255], "func_export_byte3", "hair_highlight_b_color"],
            ["Custom/_1st Dye Distribution from Grayscale", [25.5, 51, 76.5], "func_export_combine_xyz", "hair_highlight_a_start", "hair_highlight_a_mid", "hair_highlight_a_end"],
            ["Custom/_2nd Dye Distribution from Grayscale", [25.5, 51, 76.5], "func_export_combine_xyz", "hair_highlight_b_start", "hair_highlight_b_mid", "hair_highlight_b_end"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "Color", "hair_diffuse_color", True],
            ["TRIPLET", "HSV", "hair_diffuse_hue", "hair_diffuse_saturation", "hair_diffuse_brightness", True],
            ["PROP", "*HSV Strength", "hair_diffuse_hsv_strength", True],
            ["SPACER"],
            ["PROP", "AO Strength", "hair_ao_strength", True, "AO Map"],
            ["PROP", "AO Occlude All", "hair_ao_occlude_all", True, "AO Map"],
            ["PROP", "AO Darken", "hair_ao_power", True, "AO Map"],
            ["PROP", "Blend Multiply", "hair_blend_multiply_strength", True, "Blend Multiply"],
            ["SPACER"],
            ["PROP", "Enable Color", "hair_enable_color", True, "Root Map"],
            ["SPACER"],
            ["PROP", "Diffuse Strength", "hair_diffuse_strength", True, "Diffuse Map"],
            ["PROP", "Vertex Color Strength", "hair_vertex_color_strength", True],
            ["PROP", "Vertex Color", "hair_vertex_color", False],
            ["PROP", "Base Color Strength", "hair_base_color_strength", True, "Root Map"],
            ["HEADER",  "Hair Strands", "OUTLINER_OB_HAIR"],
            ["PROP", "Global Strength", "hair_global_strength", True, "Root Map"],
            ["PROP", "Root Strength", "hair_root_color_strength", True, "Root Map"],
            ["PROP", "End Strength", "hair_end_color_strength", True, "Root Map"],
            ["PROP", "Invert Root Map", "hair_invert_root_map", True, "Root Map"],
            ["PROP", "Root Color", "hair_root_color", False, "Root Map"],
            ["PROP", "End Color", "hair_end_color", False, "Root Map"],
            ["HEADER",  "Highlights", "HAIR"],
            ["PROP", "Highlight A", "hair_highlight_a_color", True, "ID Map"],
            ["TRIPLET", "Range", "hair_highlight_a_start", "hair_highlight_a_mid", "hair_highlight_a_end", True, "ID Map"],
            ["PROP", "Strength", "hair_highlight_a_strength", True, "ID Map"],
            ["PROP", "Overlap Invert", "hair_highlight_a_overlap_invert", True, "ID Map"],
            ["PROP", "Overlap End", "hair_highlight_a_overlap_end", True, "ID Map"],
            ["SPACER"],
            ["PROP", "Highlight B", "hair_highlight_b_color", True, "ID Map"],
            ["TRIPLET", "Range", "hair_highlight_b_start", "hair_highlight_b_mid", "hair_highlight_b_end", True, "ID Map"],
            ["PROP", "Strength", "hair_highlight_b_strength", True, "ID Map"],
            ["PROP", "Overlap Invert", "hair_highlight_b_overlap_invert", True, "ID Map"],
            ["PROP", "Overlap End", "hair_highlight_b_overlap_end", True, "ID Map"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Specular Scale", "hair_specular_scale", True],
            ["PROP", "Roughness Strength", "hair_roughness_strength", True],
            ["SPACER"],
            ["PROP", "Anisotropic", "hair_anisotropic", True, "#CYCLES"],
            ["PROP", "*Anisotropic Roughness", "hair_anisotropic_roughness", True, "#EEVEE"],
            ["PROP", "Anisotropic Strength", "hair_anisotropic_strength", True, "#EEVEE"],
            ["PROP", "*Specular Blend", "hair_specular_blend", True, "#EEVEE"],
            ["PROP", "*Anisotropic Color", "hair_anisotropic_color", False, "#EEVEE"],
            ["PAIR", "Anisotropic Shift", "hair_anisotropic_shift_min", "hair_anisotropic_shift_max", True],
            ["PROP", "Tangent Flip Green", "hair_tangent_flip_green", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "*Weight", "hair_subsurface_scale", True],
            ["PROP", "*Falloff", "hair_subsurface_falloff", False],
            ["PROP", "*Saturation", "hair_subsurface_saturation", True],
            ["PROP", "*Radius", "hair_subsurface_radius", True],
            ["HEADER",  "Opacity", "MOD_OPACITY"],
            ["PROP", "Strength", "hair_alpha_strength", True, "Alpha Map"],
            ["PROP", "Compression", "hair_alpha_power", True, "Alpha Map"],
            ["PROP", "Opacity", "hair_opacity", True, "Alpha Map"],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Normal Strength", "hair_normal_strength", True, "Normal Map"],
            ["PROP", "*Bump Strength", "hair_bump_strength", True, "Bump Map"],
            ["PROP", "Displacement", "hair_displacement_strength", True, "Displacement Map"],
            ["OP", "Generate Normal Map", "cc3.bake", "PLAY", "BAKE_FLOW_NORMAL", "Flow Map"], #, "!Normal Map"],
            #["PROP", "Tangent Vector", "hair_tangent_vector", False, "Flow Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Emissive Color", "hair_emissive_color", False],
            ["PROP", "Emission Strength", "hair_emission_strength", True],
        ],
        "basic": [
            ["Roughness Strength", "Roughness Max"],
        ],
        "json_template": {
            "Material Type": "Pbr",
            "MultiUV Index": 0,
            "Node Type": "Hair",
            "Two Side": True,
            "Diffuse Color": [ 255.0, 255.0, 255.0 ],
            "Ambient Color": [ 149.99, 149.99, 149.99 ],
            "Specular Color": [ 229.5, 229.5, 229.5 ],
            "Opacity": 1.0,
            "Self Illumination": 0.0,
            "Textures": {},
            "Custom Shader": {
                "Shader Name": "RLHair",
                "Image": {},
                "Variable": {},
            },
        },


    },

    # Wrinkle Shader
    #####################################

    {   "name": "rl_wrinkle_shader",
        "rl_shader": "Wrinkle",
        "label": "Wrinkle Maps",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
        ],
        # texture inputs:
        # [input_socket_color, input_socket_alpha, texture_type, tiling_prop, tiling_mode]
        "textures": [
            ["Diffuse Map", "", "DIFFUSE"],
            ["Roughness Map", "", "ROUGHNESS"],
            ["Normal Map", "", "NORMAL"],
            ["Height Map", "", "DISPLACE"],
            ["Diffuse Blend Map 1", "", "WRINKLEDIFFUSE1"],
            ["Diffuse Blend Map 2", "", "WRINKLEDIFFUSE2"],
            ["Diffuse Blend Map 3", "", "WRINKLEDIFFUSE3"],
            ["Roughness Blend Map 1", "", "WRINKLEROUGHNESS1"],
            ["Roughness Blend Map 2", "", "WRINKLEROUGHNESS2"],
            ["Roughness Blend Map 3", "", "WRINKLEROUGHNESS3"],
            ["Normal Blend Map 1", "", "WRINKLENORMAL1"],
            ["Normal Blend Map 2", "", "WRINKLENORMAL2"],
            ["Normal Blend Map 3", "", "WRINKLENORMAL3"],
            ["Flow Map 1", "", "WRINKLEFLOW1"],
            ["Flow Map 2", "", "WRINKLEFLOW2"],
            ["Flow Map 3", "", "WRINKLEFLOW3"],
            ["Height Map 1", "", "WRINKLEDISPLACEMENT1"],
            ["Height Map 2", "", "WRINKLEDISPLACEMENT2"],
            ["Height Map 3", "", "WRINKLEDISPLACEMENT3"],
            ["Mask 1A RGB", "Mask 1A A", "WRINKLEMASK1A"],
            ["Mask 1B RGB", "Mask 1B A", "WRINKLEMASK1B"],
            ["Mask 2 RGB", "Mask 2 A", "WRINKLEMASK2"],
            ["Mask 3 RGB", "Mask 3 A", "WRINKLEMASK3"],
            ["Mask 123 RGB", "Mask 123 A", "WRINKLEMASK123"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
        ],
        "ui": [
        ],
        "basic": [
        ],
        "json_template": {
        },
    },
]

# material_type, rl_shader, blender_shader
SHADER_LOOKUP = [
    ["DEFAULT", "Pbr", "rl_pbr_shader"],
    ["SSS", "SSS", "rl_sss_shader"],
    ["SKIN_HEAD", "RLHead", "rl_head_shader"],
    ["SKIN_BODY", "RLSkin", "rl_skin_shader"],
    ["SKIN_ARM", "RLSkin", "rl_skin_shader"],
    ["SKIN_LEG", "RLSkin", "rl_skin_shader"],
    ["TEETH_UPPER", "RLTeethGum", "rl_teeth_shader"],
    ["TEETH_LOWER", "RLTeethGum", "rl_teeth_shader"],
    ["TONGUE", "RLTongue", "rl_tongue_shader"],
    ["HAIR", "RLHair", "rl_hair_shader"],
    ["SCALP", "Pbr", "rl_pbr_shader"],
    ["EYELASH", "Pbr", "rl_pbr_shader"],
    ["NAILS", "RLSkin", "rl_skin_shader"],
    ["CORNEA_RIGHT", "RLEye", "rl_cornea_shader"],
    ["CORNEA_LEFT", "RLEye", "rl_cornea_shader"],
    ["EYE_RIGHT", "RLEye", "rl_eye_shader"],
    ["EYE_LEFT", "RLEye", "rl_eye_shader"],
    ["OCCLUSION_RIGHT", "RLEyeOcclusion", "rl_eye_occlusion_shader"],
    ["OCCLUSION_LEFT", "RLEyeOcclusion", "rl_eye_occlusion_shader"],
    ["OCCLUSION_PLUS_RIGHT", "RLEyeOcclusion_Plus", "rl_eye_occlusion_plus_shader"],
    ["OCCLUSION_PLUS_LEFT", "RLEyeOcclusion_Plus", "rl_eye_occlusion_plus_shader"],
    ["TEARLINE_RIGHT", "RLTearline", "rl_tearline_shader"],
    ["TEARLINE_LEFT", "RLTearline", "rl_tearline_shader"],
    ["TEARLINE_PLUS_RIGHT", "RLTearline_Plus", "rl_tearline_plus_shader"],
    ["TEARLINE_PLUS_LEFT", "RLTearline_Plus", "rl_tearline_plus_shader"],
    ["DEFAULT", "Tra", "rl_pbr_shader"],
]


def get_texture_type(json_id):
    for tex_info in TEXTURE_TYPES:
        if tex_info[1] == json_id:
            return tex_info[0]
    return "NONE"


def get_texture_json_id(tex_type):
    for tex_info in TEXTURE_TYPES:
        if tex_info[0] == tex_type:
            return tex_info[1]
    return None


def get_shader_texture_socket(shader_def, tex_type):
    if "textures" in shader_def.keys():
        for tex_def in shader_def["textures"]:
            if tex_def[2] == tex_type:
                return tex_def[0]
    return None


def get_shader_name(mat_cache):
    if mat_cache:
        material_type = mat_cache.get_material_type()
        for shader in SHADER_LOOKUP:
            if shader[0] == material_type:
                return shader[2]
    return "rl_pbr_shader"


def get_rl_shader_name(mat_cache):
    if mat_cache:
        material_type = mat_cache.get_material_type()
        for shader in SHADER_LOOKUP:
            if shader[0] == material_type:
                return shader[1]
    return "Pbr"


def get_prop_matrix(prop_name):
    matrix = []
    for shader in SHADER_MATRIX:
        for input in shader["inputs"]:
            if input[1] == prop_name:
                matrix.append([shader, input])
    return matrix


def get_shader_def(shader_name):
    for shader_def in SHADER_MATRIX:
        if type(shader_def["name"]) is list:
            for name in shader_def["name"]:
                if name in shader_name:
                    return shader_def
        else:
            if shader_def["name"] in shader_name:
                return shader_def
    return None


def get_rl_shader_def(rl_shader_name):
    if rl_shader_name == "Tra":
        rl_shader_name = "Pbr"
    for shader_def in SHADER_MATRIX:
        if shader_def["rl_shader"] == rl_shader_name:
            return shader_def
    return None


def get_mat_shader_def(mat_cache):
    shader_name = get_shader_name(mat_cache)
    return get_shader_def(shader_name)


def get_mat_shader_template(mat_cache):
    shader_name = get_shader_name(mat_cache)
    shader_def = get_shader_def(shader_name)
    if "json_template" in shader_def.keys():
        return shader_def["json_template"]
    return None


BASIC_PROPS = [

    ["IN", "Strength",  "eye_occlusion_mask", "eye_occlusion", 0.5],
    ["IN", "Hardness",  "eye_occlusion_mask", "eye_occlusion_power", 0.5],

    ["IN", "Value",     "eye_basic_hsv", "eye_brightness", 0.9],
    ["OUT", "Value",    "", "eye_specular", 0.8],
    ["OUT", "Value",    "", "eye_roughness", 0.05],
    ["OUT", "Value",    "", "eye_normal", 0.1],

    ["OUT", "Value",    "", "skin_ao", 1],
    ["OUT", "Value",    "", "hair_ao", 1],
    ["OUT", "Value",    "", "default_ao", 1],

    ["OUT", "Value",    "", "default_specular", 0.5],
    ["OUT", "Value",    "", "skin_specular", 0.4],
    ["OUT", "Value",    "", "hair_specular", 0.5],
    ["OUT", "Value",    "", "scalp_specular", 0.0],
    ["OUT", "Value",    "", "teeth_specular", 0.25],
    ["OUT", "Value",    "", "tongue_specular", 0.259],

    ["IN", "To Min",    "", "skin_roughness", 0.15],
    ["IN", 1,           "", "teeth_roughness", 0.4],
    ["IN", 1,           "", "tongue_roughness", 1.0],

    ["OUT", "Value",    "", "hair_bump", 1, "parameters.hair_bump / 1000"],
    ["OUT", "Value",    "", "default_bump", 5, "parameters.default_bump / 1000"],

    ["IN", "Alpha",     "eye_tearline_shader", "tearline_alpha", 0.05],
    ["IN", "Roughness", "eye_tearline_shader", "tearline_roughness", 0.15],
]


JSON_MESH_DATA = { "Materials": {} }


JSON_PBR_TEX_INFO = {
    "Texture Path": "",
    "Strength": 100.0,
    "Offset": [ 0.0, 0.0 ],
    "Tiling": [ 1.0, 1.0 ]
}


JSON_CUSTOM_TEX_INFO = {
    "Texture Path": ""
}


JSON_PBR_MATERIAL = {
    "Material Type": "Pbr",
    "MultiUV Index": 0,
    "Two Side": True,
    "Diffuse Color": [ 150.0, 150.0, 150.0 ],
    "Ambient Color": [ 150.0, 150.0, 150.0 ],
    "Specular Color": [ 229.5, 229.5, 229.5 ],
    "Opacity": 1.0,
    "Self Illumination": 0.0,
    "Textures": {}
}

JSON_PHYSICS_MESH = {
    "Materials": {}
}

JSON_PHYSICS_MATERIAL = {
    "Activate Physics": True,
    "Use Global Gravity": True,
    "Weight Map Path": "",
    "Mass": 1.0,
    "Friction": 0.2,
    "Damping": 0.2,
    "Drag": 0.1,
    "Solver Frequency": 120.0,
    "Tether Limit": 1.1,
    "Elasticity": 1.0,
    "Stretch": 0.0,
    "Bending": 0.0,
    "Inertia": [
        8.0,
        8.0,
        8.0
    ],
    "Soft Vs Rigid Collision": True,
    "Soft Vs Rigid Collision_Margin": 2.0,
    "Self Collision": False,
    "Self Collision Margin": 0.0,
    "Stiffness Frequency": 10.0
}

# { socket_name: expr_macro,  }
WRINKLE_DRIVERS = {
    "Value 1AXL": r"{head_wm1_normal_head_wm1_blink_L}",
    "Value 1AXL": r"{head_wm1_normal_head_wm1_blink_L}",
    "Value 1AXR": r"{head_wm1_normal_head_wm1_blink_R}",

    "Value 1AYL": r"{head_wm1_normal_head_wm1_browRaiseInner_L} - min({head_wm1_normal_head_wm1_browRaiseInner_L}, {head_wm2_normal_head_wm2_browsLateral_L})",
    "Value 1AYR": r"{head_wm1_normal_head_wm1_browRaiseInner_R} - min({head_wm1_normal_head_wm1_browRaiseInner_R}, {head_wm2_normal_head_wm2_browsLateral_R})",

    "Value 1AZL": r"{head_wm1_normal_head_wm1_purse_DL}",
    "Value 1AZR": r"{head_wm1_normal_head_wm1_purse_DR}",

    "Value 1AWL": r"{head_wm1_normal_head_wm1_purse_UL}",
    "Value 1AWR": r"{head_wm1_normal_head_wm1_purse_UR}",

    # Set 1B L/R
    "Value 1BXL": r"{head_wm1_normal_head_wm1_browRaiseOuter_L}",
    "Value 1BXR": r"{head_wm1_normal_head_wm1_browRaiseOuter_R}",

    "Value 1BYL": r"{head_wm1_normal_head_wm1_chinRaise_L}",
    "Value 1BYR": r"{head_wm1_normal_head_wm1_chinRaise_R}",

    "Value 1BZL": r"{head_wm1_normal_head_wm1_jawOpen_L}",
    "Value 1BZR": r"{head_wm1_normal_head_wm1_jawOpen_R}",

    "Value 1BWL": r"{head_wm1_normal_head_wm1_squintInner_L}",
    "Value 1BWR": r"{head_wm1_normal_head_wm1_squintInner_R}",

    # Set 2 L/R
    "Value 2XL": r"{head_wm2_normal_head_wm2_browsDown_L}",
    "Value 2XR": r"{head_wm2_normal_head_wm2_browsDown_R}",

    "Value 2YL": r"{head_wm2_normal_head_wm2_browsLateral_L} - min({head_wm1_normal_head_wm1_browRaiseInner_L}, {head_wm2_normal_head_wm2_browsLateral_L})",
    "Value 2YR": r"{head_wm2_normal_head_wm2_browsLateral_R} - min({head_wm1_normal_head_wm1_browRaiseInner_R}, {head_wm2_normal_head_wm2_browsLateral_R})",

    "Value 2ZL": r"{head_wm2_normal_head_wm2_mouthStretch_L}",
    "Value 2ZR": r"{head_wm2_normal_head_wm2_mouthStretch_R}",

    "Value 2WL": r"{head_wm2_normal_head_wm2_neckStretch_L}",
    "Value 2WR": r"{head_wm2_normal_head_wm2_neckStretch_R}",

    # Set 3 L/R
    "Value 3XL": r"{head_wm3_normal_head_wm3_cheekRaiseInner_L}",
    "Value 3XR": r"{head_wm3_normal_head_wm3_cheekRaiseInner_R}",

    "Value 3YL": r"{head_wm3_normal_head_wm3_cheekRaiseOuter_L}",
    "Value 3YR": r"{head_wm3_normal_head_wm3_cheekRaiseOuter_R}",

    "Value 3ZL": r"{head_wm3_normal_head_wm3_cheekRaiseUpper_L}",
    "Value 3ZR": r"{head_wm3_normal_head_wm3_cheekRaiseUpper_R}",

    "Value 3WL": r"{head_wm3_normal_head_wm3_smile_L}",
    "Value 3WR": r"{head_wm3_normal_head_wm3_smile_R}",

    # Set 12C L/R
    "Value 12CXL": r"{head_wm1_normal_head_wm13_lips_DL}",
    "Value 12CXR": r"{head_wm1_normal_head_wm13_lips_DR}",

    "Value 12CYL": r"{head_wm1_normal_head_wm13_lips_UL}",
    "Value 12CYR": r"{head_wm1_normal_head_wm13_lips_UR}",

    "Value 12CZL": r"{head_wm2_normal_head_wm2_noseWrinkler_L}",
    "Value 12CZR": r"{head_wm2_normal_head_wm2_noseWrinkler_R}",

    "Value 12CWL": r"{head_wm2_normal_head_wm2_noseCrease_L}",
    "Value 12CWR": r"{head_wm2_normal_head_wm2_noseCrease_R}",

    # Set 3D
    "Value 3DXL": r"{head_wm3_normal_head_wm13_lips_DL}",
    "Value 3DYL": r"{head_wm3_normal_head_wm13_lips_DR}",

    "Value 3DZR": r"{head_wm3_normal_head_wm13_lips_UL}",
    "Value 3DWR": r"{head_wm3_normal_head_wm13_lips_UR}",

    "Value BCCL": r"min({head_wm1_normal_head_wm1_browRaiseInner_L}, {head_wm2_normal_head_wm2_browsLateral_L})",
    "Value BCCR": r"min({head_wm1_normal_head_wm1_browRaiseInner_R}, {head_wm2_normal_head_wm2_browsLateral_R})",
}

# the rules that map each wrinkle morph to the socket on the wrinkle shader node.
# { wrinkle_morph_name: [node_socket, weight, <blend_func>, extra_data], }
WRINKLE_RULES = {

    # Set 1A L/R
    "head_wm1_normal_head_wm1_blink_L": [1, "ADD", "03"],
    "head_wm1_normal_head_wm1_blink_R": [1, "ADD", "03"],

    "head_wm1_normal_head_wm1_browRaiseInner_L": [1, "ADD", "01"],
    "head_wm1_normal_head_wm1_browRaiseInner_R": [1, "ADD", "01"],

    "head_wm1_normal_head_wm1_purse_DL": [1, "ADD", "08"],
    "head_wm1_normal_head_wm1_purse_DR": [1, "ADD", "08"],

    "head_wm1_normal_head_wm1_purse_UL": [1, "ADD", "08"],
    "head_wm1_normal_head_wm1_purse_UR": [1, "ADD", "08"],

    # Set 1B L/R
    "head_wm1_normal_head_wm1_browRaiseOuter_L": [1, "ADD", "01"],
    "head_wm1_normal_head_wm1_browRaiseOuter_R": [1, "ADD", "01"],

    "head_wm1_normal_head_wm1_chinRaise_L": [1, "ADD", "11"],
    "head_wm1_normal_head_wm1_chinRaise_R": [1, "ADD", "11"],

    "head_wm1_normal_head_wm1_jawOpen_L": [1, "ADD", "12"],
    "head_wm1_normal_head_wm1_jawOpen_R": [1, "ADD", "12"],

    "head_wm1_normal_head_wm1_squintInner_L": [1, "ADD", "04"],
    "head_wm1_normal_head_wm1_squintInner_R": [1, "ADD", "04"],

    # Set 2 L/R
    "head_wm2_normal_head_wm2_browsDown_L": [1, "ADD", "02"],
    "head_wm2_normal_head_wm2_browsDown_R": [1, "ADD", "02"],

    "head_wm2_normal_head_wm2_browsLateral_L": [1, "ADD", "02"],
    "head_wm2_normal_head_wm2_browsLateral_R": [1, "ADD", "02"],

    "head_wm2_normal_head_wm2_mouthStretch_L": [1, "ADD", "10"],
    "head_wm2_normal_head_wm2_mouthStretch_R": [1, "ADD", "10"],

    "head_wm2_normal_head_wm2_neckStretch_L": [1, "ADD", "13"],
    "head_wm2_normal_head_wm2_neckStretch_R": [1, "ADD", "13"],

    # Set 3 L/R
    "head_wm3_normal_head_wm3_cheekRaiseInner_L": [1, "ADD", "06"],
    "head_wm3_normal_head_wm3_cheekRaiseInner_R": [1, "ADD", "06"],

    "head_wm3_normal_head_wm3_cheekRaiseOuter_L": [1, "ADD", "06"],
    "head_wm3_normal_head_wm3_cheekRaiseOuter_R": [1, "ADD", "06"],

    "head_wm3_normal_head_wm3_cheekRaiseUpper_L": [1, "ADD", "06"],
    "head_wm3_normal_head_wm3_cheekRaiseUpper_R": [1, "ADD", "06"],

    "head_wm3_normal_head_wm3_smile_L": [1, "ADD", "09"],
    "head_wm3_normal_head_wm3_smile_R": [1, "ADD", "09"],

    # Set 12C L/R
    "head_wm1_normal_head_wm13_lips_DL": [1, "ADD", "08"],
    "head_wm1_normal_head_wm13_lips_DR": [1, "ADD", "08"],

    "head_wm1_normal_head_wm13_lips_UL": [1, "ADD", "08"],
    "head_wm1_normal_head_wm13_lips_UR": [1, "ADD", "08"],

    "head_wm2_normal_head_wm2_noseWrinkler_L": [1, "ADD", "05"],
    "head_wm2_normal_head_wm2_noseWrinkler_R": [1, "ADD", "05"],

    "head_wm2_normal_head_wm2_noseCrease_L": [1, "ADD", "07"],
    "head_wm2_normal_head_wm2_noseCrease_R": [1, "ADD", "07"],

    # Set 3D
    "head_wm3_normal_head_wm13_lips_DL": [1, "ADD", "09"],
    "head_wm3_normal_head_wm13_lips_DR": [1, "ADD", "09"],

    "head_wm3_normal_head_wm13_lips_UL": [1, "ADD", "09"],
    "head_wm3_normal_head_wm13_lips_UR": [1, "ADD", "09"],
}

# How each shape_key on the body mesh maps to each wrinkle morph.
# When multiple shape_keys drive the same wrinkle morph, the result is averaged.
# [ ["shape_key", "rule_name", range_min, range_max], ]
WRINKLE_MAPPINGS_STD = [

    ["Brow_Raise_Inner_L", "head_wm1_normal_head_wm1_browRaiseInner_L", 0.0, 1.0],
    ["Brow_Raise_Inner_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 0.03],

    ["Brow_Raise_Inner_R", "head_wm1_normal_head_wm1_browRaiseInner_R", 0.0, 1.0],
    ["Brow_Raise_Inner_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 0.03],

    ["Brow_Raise_Outer_L", "head_wm1_normal_head_wm1_browRaiseOuter_L", 0.0, 1.0],

    ["Brow_Raise_Outer_R", "head_wm1_normal_head_wm1_browRaiseOuter_R", 0.0, 1.0],

    ["Brow_Drop_L", "head_wm2_normal_head_wm2_browsDown_L", 0.0, 0.1],
    ["Brow_Drop_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 1.0],

    ["Brow_Drop_R", "head_wm2_normal_head_wm2_browsDown_R", 0.0, 0.1],
    ["Brow_Drop_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 1.0],

    ["Brow_Compress_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 1.0],

    ["Brow_Compress_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 1.0],

    ["Eye_Blink_L", "head_wm1_normal_head_wm1_blink_L", 0.0, 1.0],
    ["Eye_Blink_L", "head_wm1_normal_head_wm1_squintInner_L", 0.0, 0.3],

    ["Eye_Blink_R", "head_wm1_normal_head_wm1_blink_R", 0.0, 1.0],
    ["Eye_Blink_R", "head_wm1_normal_head_wm1_squintInner_R", 0.0, 0.3],

    ["Eye_Squint_L", "head_wm1_normal_head_wm1_squintInner_L", 0.0, 1.0],
    ["Eye_Squint_R", "head_wm1_normal_head_wm1_squintInner_R", 0.0, 1.0],

    ["Eye_L_Look_Down", "head_wm1_normal_head_wm1_blink_L", 0.0, 1.0],
    ["Eye_R_Look_Down", "head_wm1_normal_head_wm1_blink_R", 0.0, 1.0],

    ["Nose_Sneer_L", "head_wm2_normal_head_wm2_browsDown_L", 0.0, 0.7],
    ["Nose_Sneer_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 0.6],
    ["Nose_Sneer_L", "head_wm2_normal_head_wm2_noseWrinkler_L", 0.0, 1.0],

    ["Nose_Sneer_R", "head_wm2_normal_head_wm2_browsDown_R", 0.0, 0.7],
    ["Nose_Sneer_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 0.6],
    ["Nose_Sneer_R", "head_wm2_normal_head_wm2_noseWrinkler_R", 0.0, 1.0],

    ["Nose_Nostril_Raise_L", "head_wm2_normal_head_wm2_noseWrinkler_L", 0.0, 0.6],
    ["Nose_Nostril_Raise_R", "head_wm2_normal_head_wm2_noseWrinkler_R", 0.0, 0.6],

    ["Nose_Crease_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],
    ["Nose_Crease_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 1.0],
    ["Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 1.0],
    ["Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseUpper_L", 0.0, 1.0],

    ["Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 1.0],
    ["Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 1.0],
    ["Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseUpper_R", 0.0, 1.0],

    ["Jaw_Open", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 1.0],
    ["Jaw_Open", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 1.0],

    ["Jaw_L", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 1.0],
    ["Jaw_R", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 1.0],

    ["Mouth_Up", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Mouth_Up", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["Mouth_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.8],
    ["Mouth_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.6],
    ["Mouth_L", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["Mouth_L", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],
    ["Mouth_L", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["Mouth_L", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],

    ["Mouth_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.8],
    ["Mouth_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.6],
    ["Mouth_R", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["Mouth_R", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],
    ["Mouth_R", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["Mouth_R", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],

    ["Mouth_Smile_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.6],
    ["Mouth_Smile_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.6],
    ["Mouth_Smile_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 1.0],
    ["Mouth_Smile_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 1.0],
    ["Mouth_Smile_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 1.0],
    ["Mouth_Smile_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],

    ["Mouth_Smile_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.6],
    ["Mouth_Smile_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.6],
    ["Mouth_Smile_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 1.0],
    ["Mouth_Smile_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 1.0],
    ["Mouth_Smile_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 1.0],
    ["Mouth_Smile_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Mouth_Smile_Sharp_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.4],
    ["Mouth_Smile_Sharp_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.4],
    ["Mouth_Smile_Sharp_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.8],
    ["Mouth_Smile_Sharp_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.8],
    ["Mouth_Smile_Sharp_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.8],
    ["Mouth_Smile_Sharp_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],

    ["Mouth_Smile_Sharp_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.4],
    ["Mouth_Smile_Sharp_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.4],
    ["Mouth_Smile_Sharp_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.8],
    ["Mouth_Smile_Sharp_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.8],
    ["Mouth_Smile_Sharp_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.8],
    ["Mouth_Smile_Sharp_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.15],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.15],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.3],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.3],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.3],

    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.15],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.15],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.3],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.3],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.3],

    ["Mouth_Stretch_L", "head_wm2_normal_head_wm2_mouthStretch_L", 0.0, 1.0],
    ["Mouth_Stretch_R", "head_wm2_normal_head_wm2_mouthStretch_R", 0.0, 1.0],

    ["Mouth_Pucker_Up_L", "head_wm1_normal_head_wm1_purse_UL", 0.0, 1.0],
    ["Mouth_Pucker_Up_L", "head_wm1_normal_head_wm13_lips_UL", 0.0, 1.0],

    ["Mouth_Pucker_Up_R", "head_wm1_normal_head_wm1_purse_UR", 0.0, 1.0],
    ["Mouth_Pucker_Up_R", "head_wm1_normal_head_wm13_lips_UR", 0.0, 1.0],

    ["Mouth_Pucker_Down_L", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 0.5],
    ["Mouth_Pucker_Down_L", "head_wm1_normal_head_wm1_purse_DL", 0.0, 1.0],
    ["Mouth_Pucker_Down_L", "head_wm1_normal_head_wm13_lips_DL", 0.0, 1.0],

    ["Mouth_Pucker_Down_R", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 0.5],
    ["Mouth_Pucker_Down_R", "head_wm1_normal_head_wm1_purse_DR", 0.0, 1.0],
    ["Mouth_Pucker_Down_R", "head_wm1_normal_head_wm13_lips_DR", 0.0, 1.0],

    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_DL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_DR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_UL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_UR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_DL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_DR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_UL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_UR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 0.5],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 0.5],

    ["Mouth_Chin_Up", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Mouth_Chin_Up", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["Mouth_Up_Upper_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 1.0],

    ["Mouth_Up_Upper_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 1.0],

    ["Neck_Tighten_L", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 1.0],

    ["Neck_Tighten_R", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 1.0],

    ["Head_Turn_L", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 0.6],

    ["Head_Turn_R", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 0.6],

    ["Head_Tilt_L", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 0.75],

    ["Head_Tilt_R", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 0.75],

    ["Head_Backward", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.5],
    ["Head_Backward", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.5],

    ["Mouth_Frown_L", "head_wm2_normal_head_wm2_mouthStretch_L", 0.0, 1.0],

    ["Mouth_Frown_R", "head_wm2_normal_head_wm2_mouthStretch_R", 0.0, 1.0],

    ["Mouth_Shrug_Lower", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Mouth_Shrug_Lower", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["V_Open", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 1.0],
    ["V_Open", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 1.0],

    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["V_Tight", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["V_Wide", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["AE", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.24],
    ["AE", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.24],

    ["Ah", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6],
    ["Ah", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.6],

    ["EE", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["Ih", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.15],
    ["Ih", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.15],

    ["K_G_H_NG", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.065],
    ["K_G_H_NG", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.065],

    ["Oh", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6025],
    ["Oh", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6025],
    ["Oh", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.56],

    ["R", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.1],
    ["R", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.1],
    ["R", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.63],

    ["S_Z", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.14],

    ["T_L_D_N", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.0426],
    ["T_L_D_N", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.0426],

    ["Th", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.1212],
    ["Th", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.1212],

    ["W_OO", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.56],
]

WRINKLE_MAPPINGS_MH = [

    ["Brow_Raise_In_L", "head_wm1_normal_head_wm1_browRaiseInner_L", 0.0, 1.0],
    ["Brow_Raise_In_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 0.03],

    ["Brow_Raise_In_R", "head_wm1_normal_head_wm1_browRaiseInner_R", 0.0, 1.0],
    ["Brow_Raise_In_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 0.03],

    ["Brow_Raise_Outer_L", "head_wm1_normal_head_wm1_browRaiseOuter_L", 0.0, 1.0],

    ["Brow_Raise_Outer_R", "head_wm1_normal_head_wm1_browRaiseOuter_R", 0.0, 1.0],

    ["Brow_Down_L", "head_wm2_normal_head_wm2_browsDown_L", 0.0, 0.0],
    ["Brow_Down_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 1.0],

    ["Brow_Down_R", "head_wm2_normal_head_wm2_browsDown_R", 0.0, 0.0],
    ["Brow_Down_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 1.0],

    ["Brow_Lateral_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 1.0],

    ["Brow_Lateral_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 1.0],

    ["Eye_Blink_L", "head_wm1_normal_head_wm1_blink_L", 0.0, 1.0],
    ["Eye_Blink_L", "head_wm1_normal_head_wm1_squintInner_L", 0.0, 0.3],

    ["Eye_Blink_R", "head_wm1_normal_head_wm1_blink_R", 0.0, 1.0],
    ["Eye_Blink_R", "head_wm1_normal_head_wm1_squintInner_R", 0.0, 0.3],

    ["Eye_Squint_Inner_L", "head_wm1_normal_head_wm1_squintInner_L", 0.0, 1.0],
    ["Eye_Squint_Inner_R", "head_wm1_normal_head_wm1_squintInner_R", 0.0, 1.0],

    ["Eye_Look_Down_L", "head_wm1_normal_head_wm1_blink_L", 0.0, 1.0],
    ["Eye_Look_Down_R", "head_wm1_normal_head_wm1_blink_R", 0.0, 1.0],

    ["Nose_Wrinkle_L", "head_wm2_normal_head_wm2_browsDown_L", 0.0, 0.8],
    ["Nose_Wrinkle_L", "head_wm2_normal_head_wm2_browsLateral_L", 0.0, 0.0],
    ["Nose_Wrinkle_L", "head_wm2_normal_head_wm2_noseWrinkler_L", 0.0, 1.0],

    ["Nose_Wrinkle_R", "head_wm2_normal_head_wm2_browsDown_R", 0.0, 0.8],
    ["Nose_Wrinkle_R", "head_wm2_normal_head_wm2_browsLateral_R", 0.0, 0.0],
    ["Nose_Wrinkle_R", "head_wm2_normal_head_wm2_noseWrinkler_R", 0.0, 1.0],

    ["Nose_Nostril_Raise_L", "head_wm2_normal_head_wm2_noseWrinkler_L", 0.0, 0.6],
    ["Nose_Nostril_Raise_R", "head_wm2_normal_head_wm2_noseWrinkler_R", 0.0, 0.6],

    ["Nose_Nasolabial_Deepen_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],
    ["Nose_Nasolabial_Deepen_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Eye_Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.3],
    ["Eye_Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.7],
    ["Eye_Cheek_Raise_L", "head_wm3_normal_head_wm3_cheekRaiseUpper_L", 0.0, 1.0],

    ["Eye_Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.3],
    ["Eye_Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.7],
    ["Eye_Cheek_Raise_R", "head_wm3_normal_head_wm3_cheekRaiseUpper_R", 0.0, 1.0],

    ["Jaw_Open", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 1.0],
    ["Jaw_Open", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 1.0],

    ["Jaw_Left", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 1.0],
    ["Jaw_Right", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 1.0],

    ["Mouth_Up", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Mouth_Up", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["Mouth_Left", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.8],
    ["Mouth_Left", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.6],
    ["Mouth_Left", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["Mouth_Left", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],
    ["Mouth_Left", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["Mouth_Left", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],

    ["Mouth_Right", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.8],
    ["Mouth_Right", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.6],
    ["Mouth_Right", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["Mouth_Right", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],
    ["Mouth_Right", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["Mouth_Right", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],

    ["Mouth_Corner_Pull_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.6],
    ["Mouth_Corner_Pull_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.6],
    ["Mouth_Corner_Pull_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 1.0],
    ["Mouth_Corner_Pull_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 1.0],
    ["Mouth_Corner_Pull_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 1.0],
    ["Mouth_Corner_Pull_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],

    ["Mouth_Corner_Pull_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.6],
    ["Mouth_Corner_Pull_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.6],
    ["Mouth_Corner_Pull_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 1.0],
    ["Mouth_Corner_Pull_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 1.0],
    ["Mouth_Corner_Pull_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 1.0],
    ["Mouth_Corner_Pull_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Mouth_SharpCorner_Pull_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.4],
    ["Mouth_SharpCorner_Pull_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.4],
    ["Mouth_SharpCorner_Pull_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 0.7],

    ["Mouth_SharpCorner_Pull_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.4],
    ["Mouth_SharpCorner_Pull_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.4],
    ["Mouth_SharpCorner_Pull_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.8],
    ["Mouth_SharpCorner_Pull_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 0.7],

    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_cheekRaiseInner_L", 0.0, 0.15],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_cheekRaiseOuter_L", 0.0, 0.15],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm3_smile_L", 0.0, 0.3],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.3],
    ["Mouth_Dimple_L", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.3],

    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_cheekRaiseInner_R", 0.0, 0.15],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_cheekRaiseOuter_R", 0.0, 0.15],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm3_smile_R", 0.0, 0.3],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.3],
    ["Mouth_Dimple_R", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.3],

    ["Mouth_Stretch_L", "head_wm2_normal_head_wm2_mouthStretch_L", 0.0, 1.0],
    ["Mouth_StretchLips_Close_L", "head_wm2_normal_head_wm2_mouthStretch_L", 0.0, 1.0],
    ["Mouth_Stretch_R", "head_wm2_normal_head_wm2_mouthStretch_R", 0.0, 1.0],
    ["Mouth_StretchLips_Close_R", "head_wm2_normal_head_wm2_mouthStretch_R", 0.0, 1.0],

    ["Mouth_Lips_Purse_UL", "head_wm1_normal_head_wm1_purse_UL", 0.0, 1.0],
    ["Mouth_Lips_Purse_UL", "head_wm1_normal_head_wm13_lips_UL", 0.0, 1.0],

    ["Mouth_Lips_Purse_UR", "head_wm1_normal_head_wm1_purse_UR", 0.0, 1.0],
    ["Mouth_Lips_Purse_UR", "head_wm1_normal_head_wm13_lips_UR", 0.0, 1.0],

    ["Mouth_Lips_Purse_DL", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 0.5],
    ["Mouth_Lips_Purse_DL", "head_wm1_normal_head_wm1_purse_DL", 0.0, 1.0],
    ["Mouth_Lips_Purse_DL", "head_wm1_normal_head_wm13_lips_DL", 0.0, 1.0],

    ["Mouth_Lips_Purse_DR", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 0.5],
    ["Mouth_Lips_Purse_DR", "head_wm1_normal_head_wm1_purse_DR", 0.0, 1.0],
    ["Mouth_Lips_Purse_DR", "head_wm1_normal_head_wm13_lips_DR", 0.0, 1.0],

    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_DL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_DR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_UL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_purse_UR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_DL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_DR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_UL", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm13_lips_UR", 0.0, 1.0],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 0.5],
    ["Mouth_Pucker", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 0.5],

    ["Mouth_Chin_Up", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Mouth_Chin_Up", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["Mouth_UpperLip_Raise_L", "head_wm2_normal_head_wm2_noseCrease_L", 0.0, 1.0],

    ["Mouth_UpperLip_Raise_R", "head_wm2_normal_head_wm2_noseCrease_R", 0.0, 1.0],

    ["Neck_Stretch_L", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 1.0],

    ["Neck_Stretch_R", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 1.0],

    ["Head_Turn_L", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 0.6],

    ["Head_Turn_R", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 0.6],

    ["Head_Tilt_L", "head_wm2_normal_head_wm2_neckStretch_R", 0.0, 0.75],

    ["Head_Tilt_R", "head_wm2_normal_head_wm2_neckStretch_L", 0.0, 0.75],

    ["Head_Backward", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.5],
    ["Head_Backward", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.5],

    ["Mouth_Corner_Depress_L", "head_wm2_normal_head_wm2_mouthStretch_L", 0.0, 1.0],

    ["Mouth_Corner_Depress_R", "head_wm2_normal_head_wm2_mouthStretch_R", 0.0, 1.0],

    ["Jaw_Chin_Raise_DL", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Jaw_Chin_Raise_DL", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],
    ["Jaw_Chin_Raise_DR", "head_wm1_normal_head_wm1_chinRaise_L", 0.0, 1.0],
    ["Jaw_Chin_Raise_DR", "head_wm1_normal_head_wm1_chinRaise_R", 0.0, 1.0],

    ["V_Open", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6],
    ["V_Open", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.6],

    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Tight_O", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["V_Tight", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Tight", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["V_Wide", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["V_Wide", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["AE", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.24],
    ["AE", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.24],

    ["Ah", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6],
    ["Ah", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.6],

    ["EE", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.7],
    ["EE", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.7],

    ["Ih", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.15],
    ["Ih", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.15],

    ["K_G_H_NG", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.065],
    ["K_G_H_NG", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.065],

    ["Oh", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6025],
    ["Oh", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.6025],
    ["Oh", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.56],
    ["Oh", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.56],

    ["R", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.1],
    ["R", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.1],
    ["R", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.63],
    ["R", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.63],

    ["S_Z", "head_wm3_normal_head_wm13_lips_DL", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_DR", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_UL", 0.0, 0.14],
    ["S_Z", "head_wm3_normal_head_wm13_lips_UR", 0.0, 0.14],

    ["T_L_D_N", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.0426],
    ["T_L_D_N", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.0426],

    ["Th", "head_wm1_normal_head_wm1_jawOpen_L", 0.0, 0.1212],
    ["Th", "head_wm1_normal_head_wm1_jawOpen_R", 0.0, 0.1212],

    ["W_OO", "head_wm1_normal_head_wm1_purse_DL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_DR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_UL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm1_purse_UR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_DL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_DR", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_UL", 0.0, 0.56],
    ["W_OO", "head_wm1_normal_head_wm13_lips_UR", 0.0, 0.56],
]
