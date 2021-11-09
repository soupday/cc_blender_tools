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

# [system_id, json_id, suffix_list]
TEXTURE_TYPES = [
    # pbr textures
    ["DIFFUSE", "Base Color", ["diffuse", "albedo"]],
    ["AO", "AO", ["ao", "ambientocclusion", "ambient occlusion"]],
    ["BLEND1", "Blend", ["blend_multiply"]],
    ["SPECULAR", "Specular", ["specular"]],
    ["METALLIC", "Metallic", ["metallic"]],
    ["ROUGHNESS", "Roughness", ["roughness"]],
    ["EMISSION", "Glow", ["glow", "emission"]],
    ["ALPHA", "Opacity", ["opacity", "alpha"]],
    ["NORMAL", "Normal", ["normal"]],
    ["BUMP", "Bump", ["bump", "height"]],
    ["DISPLACE", "Displacement", ["displacement"]],
    # custom shader textures
    ["SSS", "SSS Map", ["sssmap", "sss"]],
    ["TRANSMISSION", "Transmission Map", ["transmap", "transmissionmap"]],
    ["BLEND2", "BaseColor Blend2", ["bcbmap", "basecolorblend2"]],
    ["SPECMASK", "Specular Mask", ["specmask", "hspecmap", "specularmask", "hairspecularmaskmap"]],
    ["NORMALBLEND", "NormalMap Blend", ["nbmap", "normalmapblend"]],
    ["MICRONORMAL", "MicroNormal", ["micron", "micronormal"]],
    ["MICRONMASK", "MicroNormalMask", ["micronmask", "micronormalmask"]],
    ["MCMAOMASK", "Mouth Cavity Mask and AO", ["mnaomask", "mouthcavitymaskandao"]],
    ["GRADIENTAO", "Gradient AO", ["gradao", "gradientao"]],
    ["GUMSMASK", "Gums Mask", ["gumsmask"]],
    ["RGBAMASK", "RGBA Area Mask", ["rgbamask"]],
    ["NMUILMASK", "Nose Mouth UpperInnerLid Mask", ["nmuilmask"]],
    ["CFULCMASK", "Cheek Fore UpperLip Chin Mask", ["cfulcmask"]],
    ["ENNASK", "Ear Neck Mask", ["enmask"]],
    ["IRISNORMAL", "Iris Normal", ["irisn", "irisnormal"]],
    ["SCLERANORMAL", "Sclera Normal", ["scleran", "scleranormal"]],
    ["EYEBLEND", "EyeBlendMap2", ["bcbmap", "basecolorblend2"]],
    ["INNERIRISMASK", "Inner Iris Mask", ["irismask"]],
    ["SCLERA", "Sclera", ["sclera"]],
    ["HAIRROOT", "Hair Root Map", ["hair root map"]],
    ["HAIRID", "Hair ID Map", ["hair id map"]],
    ["HAIRFLOW", "Hair Flow Map", ["hair flow map"]],
    ["HAIRVERTEXCOLOR", None, ["vertexcolormap"]],
    # physics textures
    ["WEIGHTMAP", "Weight Map", ["weightmap"]],
]

# when updating linked materials, attempt to update the properties in all the material types in the same list:
LINKED_MATERIALS = [
    ["SKIN_HEAD", "SKIN_BODY", "SKIN_ARM", "SKIN_LEG"],
    ["EYE_RIGHT", "CORNEA_RIGHT", "EYE_LEFT", "CORNEA_LEFT"],
    ["OCCLUSION_RIGHT", "OCCLUSION_LEFT"],
    ["TEARLINE_RIGHT", "TEARLINE_LEFT"],
    ["TEETH_UPPER", "TEETH_LOWER"],
    ["HAIR"],
    ["SCALP"],
]

# These material types must be updated together as they share the same properties:
PAIRED_MATERIALS = [
    ["EYE_RIGHT", "CORNEA_RIGHT"],
    ["EYE_LEFT", "CORNEA_LEFT"],
]

# shader definitions
SHADER_MATRIX = [

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
            ["tearline_glossiness", 0.025, "DEF"],
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
            ["PROP", "Glossiness", "tearline_glossiness", True, "#CYCLES"],
            ["PROP", "Specular", "tearline_specular", True, "#EEVEE"],
            ["PROP", "Roughness", "tearline_roughness", True],
            ["PROP", "Alpha", "tearline_alpha", True, "#EEVEE"],
            ["SPACER"],
            ["PROP", "Displace", "tearline_displace", True],
            ["PROP", "Inner Displace", "tearline_inner", True],
        ],
    },

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
            ["eye_occlusion_color", (0.014451, 0.001628, 0.000837, 1.0), "func_color_srgb", "Custom/Shadow Color"],
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
            ["eye_occlusion_power", 1.75, "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["Custom/Shadow Color", [255.0, 255.0, 255.0], "func_export_byte3", "eye_occlusion_color"],
            ["Custom/Depth Offset", 0.02, "func_mul_100", "eye_occlusion_displace"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "Color", "eye_occlusion_color", False],
            ["HEADER",  "Opacity", "MOD_OPACITY"],
            ["PROP", "Hardness", "eye_occlusion_power", True, "#EEVEE"],
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
            ["PROP", "Tear Duct Width", "eye_occlusion_tear_duct_width", True, "#EEVEE"],
            ["HEADER",  "Displacement", "MOD_DISPLACE"],
            ["PROP", "Displace", "eye_occlusion_displace", True],
            ["PROP", "Top", "eye_occlusion_top", True],
            ["PROP", "Bototm", "eye_occlusion_bottom", True],
            ["PROP", "Inner", "eye_occlusion_inner", True],
            ["PROP", "Outer", "eye_occlusion_outer", True],
        ],
    },

    {   "name": "rl_skin_shader",
        "rl_shader": "RLSkin",
        "label": "Skin (Body)",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["AO Strength", "", "skin_ao_strength"],
            ["Specular Scale", "", "skin_specular_scale"],
            ["Roughness Power", "", "skin_roughness_power"],
            ["Roughness Min", "", "skin_roughness_min"],
            ["Roughness Max", "", "skin_roughness_max"],
            ["Normal Strength", "", "skin_normal_strength"],
            ["Micro Normal Strength", "", "skin_micro_normal_strength"],
            ["Subsurface Scale", "", "skin_subsurface_scale"],
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
            ["Subsurface Radius", "func_skin_sss", "skin_subsurface_radius", "skin_subsurface_falloff"]
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
            ["Normal Map", "", "NORMAL"],
            ["Normal Blend Map", "", "NORMALBLEND"],
            ["Micro Normal Map", "", "MICRONORMAL", "OFFSET", "", "skin_micro_normal_tiling"],
            ["Micro Normal Mask", "", "MICRONMASK"],
            ["RGBA Map", "RGBA Alpha", "RGBAMASK"],
            ["Emission Map", "", "EMISSION"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["skin_micro_normal_tiling", 25, "", "Custom/MicroNormal Tiling"],
            ["skin_micro_normal_strength", 0.8, "", "Custom/MicroNormal Strength"],
            ["skin_micro_roughness_mod", 0.05, "", "Custom/Micro Roughness Scale"],
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
            ["skin_subsurface_falloff", (1.0, 0.112, 0.072, 1.0), "func_color_srgb", "SSS/Falloff"],
            ["skin_subsurface_radius", 1.5, "", "SSS/Radius"],
            # non json properties (just defaults)
            ["skin_roughness_power", 1, "DEF"],
            ["skin_roughness_min", 0.1, "DEF"],
            ["skin_roughness_max", 1, "DEF"],
            ["skin_subsurface_scale", 1, "DEF"],
            ["skin_emissive_color", (0,0,0,1), "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["SSS/Falloff", [255.0, 94.3499984741211, 76.5], "func_export_byte3", "skin_subsurface_falloff"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "AO Strength", "skin_ao_strength", True, "AO Map"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Specular Scale", "skin_specular_scale", True],
            ["PROP", "Roughness Power", "skin_roughness_power", True],
            ["PROP", "Roughness Min", "skin_roughness_min", True],
            ["PROP", "Roughness Max", "skin_roughness_max", True],
            ["SPACER"],
            ["PROP", "Micro Roughness Mod", "skin_micro_roughness_mod", True],
            ["PROP", "R Roughness Mod", "skin_r_roughness_mod", True, "RGBA Map"],
            ["PROP", "G Roughness Mod", "skin_g_roughness_mod", True, "RGBA Map"],
            ["PROP", "B Roughness Mod", "skin_b_roughness_mod", True, "RGBA Map"],
            ["PROP", "A Roughness Mod", "skin_a_roughness_mod", True, "RGBA Map"],
            ["PROP", "Unmasked Roughness Mod", "skin_unmasked_roughness_mod", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "Subsurface Falloff", "skin_subsurface_falloff", False],
            ["PROP", "Subsurface Radius", "skin_subsurface_radius", True],
            ["PROP", "Subsurface Scale", "skin_subsurface_scale", True],
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
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Emissive Color", "skin_emissive_color", False],
            ["PROP", "Emission Strength", "skin_emission_strength", True],
        ],
    },

    {   "name": "rl_head_shader",
        "rl_shader": "RLHead",
        "label": "Skin (Head)",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Cavity AO Strength", "", "skin_cavity_ao_strength"],
            ["Blend Overlay Strength", "", "skin_blend_overlay_strength"],
            ["AO Strength", "", "skin_ao_strength"],
            ["Mouth AO", "", "skin_mouth_ao"],
            ["Nostril AO", "", "skin_nostril_ao"],
            ["Lip AO", "", "skin_lips_ao"],
            ["Specular Scale", "", "skin_specular_scale"],
            ["Roughness Power", "", "skin_roughness_power"],
            ["Roughness Min", "", "skin_roughness_min"],
            ["Roughness Max", "", "skin_roughness_max"],
            ["Normal Strength", "", "skin_normal_strength"],
            ["Micro Normal Strength", "", "skin_micro_normal_strength"],
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
            ["Subsurface Scale", "", "skin_subsurface_scale"],
            ["Micro Roughness Mod", "", "skin_micro_roughness_mod"],
            ["Unmasked Roughness Mod", "", "skin_chin_roughness_mod"],
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
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_skin_sss", "skin_subsurface_radius", "skin_subsurface_falloff"]
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
            ["Normal Map", "", "NORMAL"],
            ["Normal Blend Map", "", "NORMALBLEND"],
            ["Micro Normal Map", "", "MICRONORMAL", "OFFSET", "", "skin_micro_normal_tiling"],
            ["Micro Normal Mask", "", "MICRONMASK"],
            ["NMUIL Map", "NMUIL Alpha", "NMUILMASK"],
            ["CFULC Map", "CFULC Alpha", "CFULCMASK"],
            ["EN Map", "", "ENNASK"],
            ["Emission Map", "", "EMISSION"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["skin_blend_overlay_strength", 0, "", "Custom/BaseColor Blend2 Strength"],
            ["skin_normal_blend_strength", 0, "", "Custom/NormalMap Blend Strength"],
            ["skin_micro_normal_tiling", 20, "", "Custom/MicroNormal Tiling"],
            ["skin_micro_normal_strength", 0.5, "", "Custom/MicroNormal Strength"],
            ["skin_micro_roughness_mod", 0.05, "", "Custom/Micro Roughness Scale"],
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
            ["skin_subsurface_falloff", (1.0, 0.112, 0.072, 1.0), "func_color_srgb", "SSS/Falloff"],
            ["skin_subsurface_radius", 1.5, "", "SSS/Radius"],
            # non json properties (just defaults)
            ["skin_roughness_power", 1, "DEF"],
            ["skin_roughness_min", 0.1, "DEF"],
            ["skin_roughness_max", 1, "DEF"],
            ["skin_subsurface_scale", 1, "DEF"],
            ["skin_emissive_color", (0,0,0,1), "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["SSS/Falloff", [255.0, 94.3499984741211, 76.5], "func_export_byte3", "skin_subsurface_falloff"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "AO Strength", "skin_ao_strength", True, "AO Map"],
            ["PROP", "Mouth AO", "skin_mouth_ao", True, "MCMAO Map"],
            ["PROP", "Nostrils AO", "skin_nostril_ao", True, "MCMAO Map"],
            ["PROP", "Lips AO", "skin_lips_ao", True, "MCMAO Map"],
            ["SPACER"],
            ["PROP", "Color Blend", "skin_blend_overlay_strength", True, "Blend Overlay"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Specular Scale", "skin_specular_scale", True],
            ["PROP", "Roughness Power", "skin_roughness_power", True],
            ["PROP", "Roughness Min", "skin_roughness_min", True],
            ["PROP", "Roughness Max", "skin_roughness_max", True],
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
            ["PROP", "Subsurface Falloff", "skin_subsurface_falloff", False],
            ["PROP", "Subsurface Radius", "skin_subsurface_radius", True],
            ["PROP", "Subsurface Scale", "skin_subsurface_scale", True],
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
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Emissive Color", "skin_emissive_color", False],
            ["PROP", "Emission Strength", "skin_emission_strength", True],
        ],
    },

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
            ["Subsurface Scale", "", "tongue_subsurface_scatter"],
            ["Front Specular", "", "tongue_front_specular"],
            ["Rear Specular", "", "tongue_rear_specular"],
            ["Front Roughness", "", "tongue_front_roughness"],
            ["Rear Roughness", "", "tongue_rear_roughness"],
            ["Normal Strength", "", "tongue_normal_strength"],
            ["Micro Normal Strength", "", "tongue_micro_normal_strength"],
            ["Emissive Color", "", "tongue_emissive_color"],
            ["Emission Strength", "func_emission_scale", "tongue_emission_strength"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_skin_sss", "tongue_subsurface_radius", "tongue_subsurface_falloff"]
        ],
        # texture inputs:
        # [input_socket_color, input_socket_alpha, texture_type, tiling_prop, tiling_mode]
        "textures": [
            ["Diffuse Map", "", "DIFFUSE"],
            ["Gradient AO Map", "", "GRADIENTAO"],
            ["AO Mask", "", "AO"],
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
            ["tongue_subsurface_scale", 1, "", "Custom/_Scatter"],
            ["tongue_ao_strength", 1, "", "Pbr/AO"],
            ["tongue_normal_strength", 1, "", "Pbr/Normal"],
            ["tongue_emission_strength", 0, "", "Pbr/Glow"],
            ["tongue_subsurface_falloff", (1, 1, 1, 1), "func_color_srgb", "SSS/Falloff"],
            ["tongue_subsurface_radius", 1, "", "SSS/Radius"],
            # non json properties (just defaults)
            ["tongue_hue", 0.5, "DEF"],
            ["tongue_hsv_strength", 1, "DEF"],
            ["tongue_emissive_color", (0,0,0,1), "DEF"],
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
            ["PROP", "AO Strength", "tongue_ao_strength", True, "AO Mask"],
            ["PROP", "Front AO", "tongue_front_ao", True, "Gradient AO Map"],
            ["PROP", "Back AO", "tongue_rear_ao", True, "Gradient AO Map"],
            ["SPACER"],
            ["PROP", "Hue", "tongue_hue", True, "Diffuse Map"],
            ["PROP", "Saturation", "tongue_saturation", True, "Diffuse Map"],
            ["PROP", "Brightness", "tongue_brightness", True, "Diffuse Map"],
            ["PROP", "HSV Strength", "tongue_hsv_strength", True, "Diffuse Map"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Front Roughness", "tongue_front_roughness", True],
            ["PROP", "Front Specular", "tongue_front_specular", True],
            ["PROP", "Back Roughness", "tongue_rear_roughness", True],
            ["PROP", "Back Specular", "tongue_rear_specular", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "Subsurface Falloff", "tongue_subsurface_falloff", False],
            ["PROP", "Subsurface Radius", "tongue_subsurface_radius", True],
            ["PROP", "Subsurface Scale", "tongue_subsurface_scale", True],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Normal Strength", "tongue_normal_strength", True, "Normal Map"],
            ["PROP", "Micro Normal Strength", "tongue_micro_normal_strength", True, "Micro Normal Map"],
            ["PROP", "Micro Normal Tiling", "tongue_micro_normal_tiling", True, "Micro Normal Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Emissive Color", "tongue_emissive_color", False],
            ["PROP", "Emission Strength", "tongue_emission_strength", True],
        ],
    },

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
            ["Teeth Subsurface Scale", "", "teeth_teeth_subsurface_scatter"],
            ["Gums Subsurface Scale", "", "teeth_gums_subsurface_scatter"],
            ["Front Specular", "", "teeth_front_specular"],
            ["Rear Specular", "", "teeth_rear_specular"],
            ["Front Roughness", "", "teeth_front_roughness"],
            ["Rear Roughness", "", "teeth_rear_roughness"],
            ["Normal Strength", "", "teeth_normal_strength"],
            ["Micro Normal Strength", "", "teeth_micro_normal_strength"],
            ["Emissive Color", "", "teeth_emissive_color"],
            ["Emission Strength", "func_emission_scale", "teeth_emission_strength"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_teeth_sss", "teeth_subsurface_radius", "teeth_subsurface_falloff"]
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
            ["teeth_subsurface_falloff", (0.381, 0.198, 0.13, 1.0), "func_color_srgb", "SSS/Falloff"],
            ["teeth_subsurface_radius", 1, "", "SSS/Radius"],
            # non json properties (just defaults)
            ["teeth_gums_hue", 0.5, "DEF"],
            ["teeth_gums_hsv_strength", 1, "DEF"],
            ["teeth_teeth_hue", 0.5, "DEF"],
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
            ["PROP", "Front AO", "teeth_front_ao", True, "Gradient AO Map"],
            ["PROP", "Back AO", "teeth_rear_ao", True, "Gradient AO Map"],
            ["SPACER"],
            ["PROP", "Teeth Hue", "teeth_teeth_hue", True, "Diffuse Map"],
            ["PROP", "Teeth Saturation", "teeth_teeth_saturation", True, "Diffuse Map"],
            ["PROP", "Teeth Brightness", "teeth_teeth_brightness", True, "Diffuse Map"],
            ["PROP", "Teeth HSV Strength", "teeth_teeth_hsv_strength", True, "Diffuse Map"],
            ["SPACER"],
            ["PROP", "Gums Hue", "teeth_gums_hue", True, "Diffuse Map"],
            ["PROP", "Gums Saturation", "teeth_gums_saturation", True, "Diffuse Map"],
            ["PROP", "Gums Brightness", "teeth_gums_brightness", True, "Diffuse Map"],
            ["PROP", "Gums HSV Strength", "teeth_gums_hsv_strength", True, "Diffuse Map"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Front Roughness", "teeth_front_roughness", True],
            ["PROP", "Front Specular", "teeth_front_specular", True],
            ["PROP", "Back Roughness", "teeth_rear_roughness", True],
            ["PROP", "Back Specular", "teeth_rear_specular", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "Subsurface Falloff", "teeth_subsurface_falloff", False],
            ["PROP", "Subsurface Radius", "teeth_subsurface_radius", True],
            ["PROP", "Teeth Subsurface Scale", "teeth_teeth_subsurface_scatter", True],
            ["PROP", "Gums Subsurface Scale", "teeth_gums_subsurface_scatter", True],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Normal Strength", "teeth_normal_strength", True, "Normal Map"],
            ["PROP", "Micro Normal Strength", "teeth_micro_normal_strength", True, "Micro Normal Map"],
            ["PROP", "Micro Normal Tiling", "teeth_micro_normal_tiling", True, "Micro Normal Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Emissive Color", "teeth_emissive_color", False],
            ["PROP", "Emission Strength", "teeth_emission_strength", True],
        ],
    },

    {   "name": ["rl_cornea_shader", "rl_eye_shader"],
        "rl_shader": "RLEye",
        "label": "Eye",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Subsurface Scale", "", "eye_subsurface_scale"],
            ["Cornea Specular", "", "eye_cornea_specular"],
            ["Iris Specular", "", "eye_iris_specular"],
            ["Cornea Roughness", "", "eye_cornea_roughness"],
            ["Iris Roughness", "", "eye_iris_roughness"],
            ["Sclera Roughness", "", "eye_sclera_roughness"],
            ["AO Strength", "", "eye_ao_strength"],
            ["Sclera Scale", "", "eye_sclera_scale"],
            ["Sclera Hue", "", "eye_sclera_hue"],
            ["Sclera Saturation", "", "eye_sclera_saturation"],
            ["Sclera Brightness", "", "eye_sclera_brightness"],
            ["Sclera HSV Strength", "", "eye_sclera_hsv"],
            ["Iris Scale", "", "eye_iris_scale"],
            ["Iris Hue", "", "eye_iris_hue"],
            ["Iris Saturation", "", "eye_iris_saturation"],
            ["Iris Brightness", "", "eye_iris_brightness"],
            ["Iris HSV Strength", "", "eye_iris_hsv"],
            ["Iris Radius", "", "eye_iris_radius"],
            ["Limbus Width", "", "eye_limbus_width"],
            ["Limbus Dark Radius", "", "eye_limbus_dark_radius"],
            ["Limbus Dark Width", "", "eye_limbus_dark_width"],
            ["Limbus Color", "", "eye_limbus_color"],
            ["IOR", "", "eye_ior"],
            ["Shadow Radius", "", "eye_shadow_radius"],
            ["Shadow Hardness", "", "eye_shadow_hardness"],
            ["Corner Shadow Color", "", "eye_corner_shadow_color"],
            ["Color Blend Strength", "", "eye_color_blend_strength"],
            ["Sclera Emissive Color", "", "eye_sclera_emissive_color"],
            ["Sclera Emission Strength", "func_emission_scale", "eye_sclera_emission_strength"],
            ["Iris Emissive Color",  "","eye_iris_emissive_color"],
            ["Iris Emission Strength", "func_emission_scale", "eye_iris_emission_strength"],
            ["Sclera Normal Strength", "", "eye_sclera_normal_strength"],
            ["Blood Vessel Height", "func_divide_1000", "eye_blood_vessel_height"],
            ["Iris Bump Height", "func_divide_1000", "eye_iris_bump_height"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_eye_sss", "eye_subsurface_radius", "eye_subsurface_falloff"]
        ],
        # modifier properties:
        # [prop_name, material_type, modifier_type, modifier_id, expression]
        "modifiers": [
            [ "eye_iris_depth", "EYE_RIGHT", "DISPLACE", "Eye_Displace_R", "mod.strength = parameters.eye_iris_depth"],
            [ "eye_pupil_scale", "EYE_RIGHT", "UV_WARP", "Eye_UV_Warp_R", "mod.scale = (1.0 / parameters.eye_pupil_scale, 1.0 / parameters.eye_pupil_scale)" ],
            [ "eye_iris_depth", "EYE_LEFT", "DISPLACE", "Eye_Displace_L", "mod.strength = parameters.eye_iris_depth"],
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
            ["Sclera Diffuse Map", "", "SCLERA", "CENTERED", "func_recip", "eye_sclera_scale"],
            # EYE_PARALLAX tells it to use a parallax mapping node, unless in SSR mode in which it behaves as a CENTERED mapping node
            ["Cornea Diffuse Map", "", "DIFFUSE", "EYE_PARALLAX", "func_recip_2", "eye_iris_scale", "eye_sclera_scale"],
            ["Color Blend Map", "", "EYEBLEND"],
            ["AO Map", "", "AO"],
            ["Metallic Map", "", "METALLIC"],
            ["Sclera Normal Map", "", "SCLERANORMAL", "OFFSET", "", "eye_sclera_normal_tiling"],
            ["Sclera Emission Map", "", "EMISSION"],
            ["Iris Emission Map", "", "EMISSION"],
        ],
        "mapping": [
            ["DIFFUSE"], # The Parallax mapping node is updated with these params, not the mapping params in the textures above.
            ["EYE_PARALLAX", "Iris Scale", "func_mul", "eye_iris_scale", "eye_sclera_scale"],
            ["EYE_PARALLAX", "Iris Radius", "", "eye_iris_radius"],
            ["EYE_PARALLAX", "Pupil Scale", "", "eye_pupil_scale"],
            ["EYE_PARALLAX", "Depth Radius", "", "eye_iris_depth_radius"],
            ["EYE_PARALLAX", "Depth", "", "eye_iris_depth"],
            ["EYE_PARALLAX", "IOR", "", "eye_ior"],
        ],
        # shader variables:
        # [prop_name, default_value, function, json_id_arg1, json_id_arg2...]
        "vars": [
            ["eye_color_blend_strength", 0.1, "", "Custom/BlendMap2 Strength"],
            ["eye_shadow_radius", 0.279, "", "Custom/Shadow Radius"],
            ["eye_shadow_hardness", 0.5, "", "Custom/Shadow Hardness"],
            ["eye_cornea_specular", 0.8, "", "Custom/Specular Scale"],
            ["eye_corner_shadow_color", (1.0, 0.497, 0.445, 1.0), "func_color_srgb", "Custom/Eye Corner Darkness Color"],
            ["eye_iris_depth", 0.3, "func_eye_depth", "Custom/Iris Depth Scale"],
            ["eye_cornea_roughness", 0, "", "Custom/_Iris Roughness"],
            ["eye_iris_brightness", 1, "", "Custom/Iris Color Brightness"],
            ["eye_pupil_scale", 1, "", "Custom/Pupil Scale"],
            ["eye_ior", 1.4, "", "Custom/_IoR"],
            ["eye_iris_scale", 0.93, "func_iris_scale", "Custom/Iris UV Radius"],
            ["eye_iris_radius", 0.16, "", "Custom/Iris UV Radius"],
            ["eye_limbus_width", 0.055, "", "Custom/Limbus UV Width Color"],
            ["eye_limbus_dark_radius", 0.106, "func_limbus_dark_radius", "Custom/Limbus Dark Scale"],
            ["eye_sclera_brightness", 0.650, "", "Custom/ScleraBrightness"],
            ["eye_sclera_roughness", 0.2, "", "Custom/Sclera Roughness"],
            ["eye_sclera_normal_strength", 0.1, "func_one_minus", "Custom/Sclera Flatten Normal"],
            ["eye_sclera_normal_tiling", 2, "func_recip", "Custom/Sclera Normal UV Scale"],
            ["eye_sclera_scale", 0.93, "", "Custom/Sclera UV Radius"],
            ["eye_ao_strength", 0.2, "", "Pbr/AO"],
            ["eye_normal_strength", 1, "", "Pbr/Normal"],
            ["eye_sclera_emission_strength", 0, "", "Pbr/Glow"],
            ["eye_iris_emission_strength", 0, "", "Pbr/Glow"],
            ["eye_subsurface_falloff", (1,1,1,1), "func_color_srgb", "SSS/Falloff"],
            ["eye_subsurface_radius", 5, "", "SSS/Radius"],
            # non json properties (just defaults)
            ["eye_subsurface_scale", 0.75, "DEF"],
            ["eye_iris_depth_radius", 0.88, "DEF"],
            ["eye_refraction_depth", 1, "DEF"],
            ["eye_blood_vessel_height", 0.5, "DEF"],
            ["eye_iris_bump_height", 1, "DEF"],
            ["eye_iris_roughness", 1, "DEF"],
            ["eye_sclera_hue", 0.5, "DEF"],
            ["eye_sclera_saturation", 1, "DEF"],
            ["eye_sclera_hsv", 1, "DEF"],
            ["eye_iris_hue", 0.5, "DEF"],
            ["eye_iris_saturation", 1, "DEF"],
            ["eye_iris_hsv", 1, "DEF"],
            ["eye_limbus_dark_width", 0.025, "DEF"],
            ["eye_limbus_color", (0.0, 0.0, 0.0, 1), "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]



        "export": [
            ["Custom/Limbus Dark Scale", 6.5, "func_export_limbus_dark_scale", "eye_limbus_dark_radius"],
            ["Custom/Eye Corner Darkness Color", [255.0, 188.0, 179.0], "func_export_byte3", "eye_corner_shadow_color"],
            ["Custom/Iris Depth Scale", 0.3, "func_export_eye_depth", "eye_iris_depth"],
            ["Custom/Sclera Flatten Normal", 0.9, "func_one_minus", "eye_sclera_normal_strength"],
            ["Custom/Sclera Normal UV Scale", 0.5, "func_recip", "eye_sclera_normal_tiling"],
            ["SSS/Falloff", [255.0, 255.0, 255.0], "func_export_byte3", "eye_subsurface_falloff"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "AO Strength", "eye_ao_strength", True, "AO Map"],
            ["PROP", "Color Blend", "eye_color_blend_strength", True, "Color Blend Map"],
            ["SPACER"],
            ["PROP", "Sclera Hue", "eye_sclera_hue", True, "Sclera Diffuse Map"],
            ["PROP", "Sclera Saturation", "eye_sclera_saturation", True, "Sclera Diffuse Map"],
            ["PROP", "Sclera Brightness", "eye_sclera_brightness", True, "Sclera Diffuse Map"],
            ["PROP", "Sclera HSV", "eye_sclera_hsv", True, "Sclera Diffuse Map"],
            ["SPACER"],
            ["PROP", "Iris Hue", "eye_iris_hue", True, "Cornea Diffuse Map"],
            ["PROP", "Iris Saturation", "eye_iris_saturation", True, "Cornea Diffuse Map"],
            ["PROP", "Iris Brightness", "eye_iris_brightness", True, "Cornea Diffuse Map"],
            ["PROP", "Iris HSV", "eye_iris_hsv", True, "Cornea Diffuse Map"],
            ["SPACER"],
            ["PROP", "Iris Radius", "eye_iris_radius", True],
            ["PROP", "Limbus Width", "eye_limbus_width", True],
            ["PROP", "Dark Radius", "eye_limbus_dark_radius", True],
            ["PROP", "Dark Width", "eye_limbus_dark_width", True],
            ["PROP", "Limbus Color", "eye_limbus_color", False],
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
            ["PROP", "Iris Roughness", "eye_iris_roughness", True],
            ["PROP", "Cornea Roughness", "eye_cornea_roughness", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "Subsurface Scale", "eye_subsurface_scale", True],
            ["PROP", "Subsurface Radius", "eye_subsurface_radius", True],
            ["PROP", "Subsurface Falloff", "eye_subsurface_falloff", False],
            ["HEADER",  "Depth & Refraction", "MOD_THICKNESS"],
            ["PROP", "Iris Depth", "eye_iris_depth", True],
            ["PROP", "Depth Radius", "eye_iris_depth_radius", True],
            ["PROP", "Pupil Scale", "eye_pupil_scale", True],
            ["PROP", "IOR", "eye_ior", True],
            ["PROP", "Refraction Depth", "eye_refraction_depth", True],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Sclera Normal Strength", "eye_sclera_normal_strength", True], "Sclera Normal Map",
            ["PROP", "Sclera Normal Tiling", "eye_sclera_normal_tiling", True, "Sclera Normal Map"],
            ["PROP", "Blood Vessel Height", "eye_blood_vessel_height", True, "Sclera Diffuse Map"],
            ["PROP", "Iris Bump Height", "eye_iris_bump_height", True, "Cornea Diffuse Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Sclera Emissive Color", "eye_sclera_emissive_color", False],
            ["PROP", "Sclera Emission Strength", "eye_sclera_emission_strength", True],
            ["PROP", "Iris Emissive Color", "eye_iris_emissive_color", False],
            ["PROP", "Iris Emission Strength", "eye_iris_emission_strength", True],
        ],
    },

    {   "name": "rl_pbr_shader",
        "rl_shader": "Pbr",
        "label": "PBR Material",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Diffuse Color", "", "default_diffuse_color"],
            ["AO Strength", "", "default_ao_strength"],
            ["Blend Multiply Strength", "", "default_blend_multiply_strength"],
            ["Metallic Map", "", "default_metallic"],
            ["Specular Strength", "", "default_specular_strength"],
            ["Specular Scale", "", "default_specular_scale"],
            ["Roughness Power", "", "default_roughness_power"],
            ["Roughness Min", "", "default_roughness_min"],
            ["Roughness Max", "", "default_roughness_max"],
            ["Alpha Strength", "", "default_alpha_strength"],
            ["Opacity", "", "default_opacity"],
            ["Normal Strength", "", "default_normal_strength"],
            ["Bump Strength", "func_divide_100", "default_bump_strength"],
            ["Emissive Color", "", "default_emissive_color"],
            ["Emission Strength", "func_emission_scale", "default_emission_strength"],
            ["Displacement Strength", "func_divide_100", "default_displacement_strength"],
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
            ["default_diffuse_color", (1,1,1,1), "func_color_linear", "/Diffuse Color"],
            ["default_blend_multiply_strength", 0, "", "Pbr/Blend"],
            ["default_alpha_strength", 1, "", "Pbr/Opacity"],
            ["default_opacity", 1, "", "Base/Opacity"],
            ["default_normal_strength", 1, "", "Pbr/Normal"],
            ["default_emission_strength", 0, "", "Pbr/Glow"],
            ["default_displacement_strength", 1, "", "Pbr/Displacement"],
            # non json properties (just defaults)
            ["default_bump_strength", 1, "DEF"],
            ["default_specular_strength", 1, "", "Pbr/Specular"],
            ["default_metallic", 0, "", "Pbr/Metallic"],
            ["default_specular_scale", 1.0, "DEF"],
            ["default_roughness_power", 1, "DEF"],
            ["default_roughness_min", 0, "DEF"],
            ["default_roughness_max", 1, "DEF"],
            ["default_emissive_color", (0,0,0,1), "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["/Diffuse Color", [255.0, 255.0, 255.0], "func_export_byte3", "default_diffuse_color"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "Color", "default_diffuse_color", True],
            ["PROP", "AO Strength", "default_ao_strength", True, "AO Map"],
            ["PROP", "Blend Multiply", "default_blend_multiply_strength", True, "Blend Multiply"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Metallic", "default_metallic", True, "!Metallic Map"],
            ["PROP", "Specular Map", "default_specular_strength", True, "Specular Map"],
            ["PROP", "Specular Scale", "default_specular_scale", True],
            ["PROP", "Roughness Power", "default_roughness_power", True],
            ["PROP", "Roughness Min", "default_roughness_min", True],
            ["PROP", "Roughness Max", "default_roughness_max", True],
            ["HEADER",  "Opacity", "MOD_OPACITY"],
            ["PROP", "Alpha Strength", "default_alpha_strength", True],
            ["PROP", "Opacity", "default_opacity", True],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Normal Strength", "default_normal_strength", True, "Normal Map"],
            ["PROP", "Bump Strength", "default_bump_strength", True, "Bump Map"],
            ["PROP", "Displacement", "default_displacement_strength", True, "Displacement Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Emissive Color", "default_emissive_color", False],
            ["PROP", "Emission Strength", "default_emission_strength", True],
        ],
    },

    {   "name": "rl_sss_shader",
        "rl_shader": "RLSSS",
        "label": "SSS Material",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
            ["Diffuse Color", "", "default_diffuse_color"],
            ["AO Strength", "", "default_ao_strength"],
            ["Blend Multiply Strength", "", "default_blend_multiply_strength"],
            ["Specular Strength", "", "default_specular_strength"],
            ["Specular Scale", "", "default_specular_scale"],
            ["Roughness Power", "", "default_roughness_power"],
            ["Roughness Min", "", "default_roughness_min"],
            ["Roughness Max", "", "default_roughness_max"],
            ["Alpha Strength", "", "default_alpha_strength"],
            ["Opacity", "", "default_opacity"],
            ["Normal Strength", "", "default_normal_strength"],
            ["Bump Strength", "func_divide_100", "default_bump_strength"],
            ["Emissive Color", "", "default_emissive_color"],
            ["Emission Strength", "func_emission_scale", "default_emission_strength"],
            ["Displacement Strength", "func_divide_100", "default_displacement_strength"],
            ["Micro Normal Strength", "", "default_micro_normal_strength"],
            ["Subsurface Scale", "", "default_subsurface_scale"],
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
            ["Subsurface Radius", "func_default_sss", "default_subsurface_radius", "default_subsurface_falloff"]
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
            ["default_diffuse_color", (1,1,1,1), "func_color_linear", "/Diffuse Color"],
            ["default_specular_scale", 1.0, "", "Custom/_Specular"],
            ["default_brightness", 1, "", "Custom/_BaseColorMap Brightness"],
            ["default_saturation", 1, "", "Custom/_BaseColorMap Saturation"],
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
            ["default_subsurface_falloff", (1.0, 1.0, 1.0, 1.0), "func_color_srgb", "SSS/Falloff"],
            ["default_suburface_radius", 1.5, "", "SSS/Radius"],
            ["default_specular_strength", 1, "", "Pbr/Specular"],
            ["default_metallic", 0, "", "Pbr/Metallic"],
            # non json properties (just defaults)
            ["default_hue", 0.5, "DEF"],
            ["default_hsv_strength", 1, "DEF"],
            ["default_bump_strength", 1, "DEF"],
            ["default_specular_map", 0.5, "DEF"],
            ["default_specular_mask", 1.0, "DEF"],
            ["default_specular_scale", 1.0, "DEF"],
            ["default_roughness_power", 1, "DEF"],
            ["default_roughness_min", 0, "DEF"],
            ["default_roughness_max", 1, "DEF"],
            ["default_subsurface_scale", 1, "DEF"],
            ["default_emissive_color", (0,0,0,1), "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
            ["/Diffuse Color", [255.0, 255.0, 255.0], "func_export_byte3", "default_diffuse_color"],
            ["SSS/Falloff", [255.0, 255.0, 255.0], "func_export_byte3", "default_subsurface_falloff"],
        ],
        "ui": [
            # ["HEADER", label, icon]
            # ["PROP", labe, prop_name, (slider=)True|False]
            ["HEADER",  "Base Color", "COLOR"],
            ["PROP", "Color", "default_diffuse_color", True],
            ["PROP", "Hue", "default_hue", True],
            ["PROP", "Saturation", "default_saturation", True],
            ["PROP", "Brightness", "default_brightness", True],
            ["PROP", "HSV Strength", "default_hsv_strength", True],
            ["PROP", "AO Strength", "default_ao_strength", True, "AO Map"],
            ["PROP", "Blend Multiply", "default_blend_multiply_strength", True, "Blend Multiply"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Metallic", "default_metallic", True, "!Metallic Map"],
            ["PROP", "Specular Map", "default_specular_strength", True, "Specular Map"],
            ["PROP", "Specular Scale", "default_specular_scale", True],
            ["PROP", "Roughness Power", "default_roughness_power", True],
            ["PROP", "Roughness Min", "default_roughness_min", True],
            ["PROP", "Roughness Max", "default_roughness_max", True],
            ["SPACER"],
            ["PROP", "Micro Roughness Mod", "default_micro_roughness_mod", True],
            ["PROP", "R Roughness Mod", "default_r_roughness_mod", True, "RGBA Map"],
            ["PROP", "G Roughness Mod", "default_g_roughness_mod", True, "RGBA Map"],
            ["PROP", "B Roughness Mod", "default_b_roughness_mod", True, "RGBA Map"],
            ["PROP", "A Roughness Mod", "default_a_roughness_mod", True, "RGBA Map"],
            ["PROP", "Unmasked Roughness Mod", "default_unmasked_roughness_mod", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "Subsurface Falloff", "default_subsurface_falloff", False],
            ["PROP", "Subsurface Radius", "default_subsurface_radius", True],
            ["PROP", "Subsurface Scale", "default_subsurface_scale", True],
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
            ["SPACER"],
            ["PROP", "Micro Normal Strength", "default_micro_normal_strength", True, "Micro Normal Map"],
            ["PROP", "Micro Normal Tiling", "default_micro_normal_tiling", True, "Micro Normal Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Emissive Color", "default_emissive_color", False],
            ["PROP", "Emission Strength", "default_emission_strength", True],
        ],
    },

    {   "name": "rl_hair_shader",
        "rl_shader": "RLHair",
        "cycles" : "rl_hair_cycles_shader",
        "label": "Hair",
        # property inputs:
        # [input_socket, function, property_arg1, property_arg2...]
        "inputs": [
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
            ["Anisotropic Shift", "", "hair_anisotropic_shift"],
            ["Flow Invert Green", "", "hair_tangent_flip_green"],
            ["Anisotropic Roughness", "", "hair_anisotropic_roughness"],
            ["Anisotropic Strength", "", "hair_anisotropic_strength"],
            ["Anisotropic Color", "", "hair_anisotropic_color"],
            ["Subsurface Scale", "", "hair_subsurface_scale"],
            ["Diffuse Strength", "", "hair_diffuse_strength"],
            ["AO Strength", "", "hair_ao_strength"],
            ["AO Occlude All", "", "hair_ao_occlude_all"],
            ["Blend Multiply Strength", "", "hair_blend_multiply_strength"],
            ["Specular Scale", "", "hair_specular_scale"],
            ["Roughness Strength", "", "hair_roughness_strength"],
            ["Alpha Strength", "", "hair_alpha_strength"],
            ["Opacity", "", "hair_opacity"],
            ["Normal Strength", "", "hair_normal_strength"],
            ["Bump Strength", "func_divide_100", "hair_bump_strength"],
            ["Emissive Color", "", "hair_emissive_color"],
            ["Emission Strength", "func_emission_scale", "hair_emission_strength"],
            ["Displacement Strength", "func_divide_100", "hair_displacement_strength"],
        ],
        # inputs to the bsdf that must be controlled directly (i.e. subsurface radius in Eevee)
        "bsdf": [
            ["Subsurface Radius", "func_hair_sss", "hair_subsurface_radius", "hair_subsurface_falloff"]
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
            ["hair_tangent_vector", (1, 0, 0), "func_color_vector", "Custom/TangentVectorColor"],
            ["hair_tangent_flip_green", 1, "", "Custom/TangentMapFlipGreen"],
            ["hair_diffuse_strength", 1, "", "Custom/Diffuse Strength"],
            ["hair_roughness_strength", 0.724, "func_sqrt", "Custom/Hair Roughness Map Strength"],
            ["hair_specular_scale", 0.3, "", "Custom/Hair Specular Map Strength"],
            ["hair_anisotropic_strength", 0.8, "", "Custom/Specular Strength"],
            ["hair_anisotropic_strength2", 1.0, "", "Custom/Secondary Specular Strength"],
            ["hair_vertex_color", (0,0,0,1), "func_color_linear", "Custom/VertexGrayToColor"],
            ["hair_vertex_color_strength", 0.875, "", "Custom/VertexColorStrength"],
            ["hair_enable_color", 0, "", "Custom/ActiveChangeHairColor"],
            ["hair_base_color_strength", 1, "", "Custom/BaseColorMapStrength"],
            ["hair_root_color", (0.144129, 0.072272, 0.046665, 1.0), "func_color_linear", "Custom/RootColor"],
            ["hair_end_color", (0.332452, 0.184475, 0.122139, 1.0), "func_color_linear", "Custom/TipColor"],
            ["hair_global_strength", 0, "", "Custom/UseRootTipColor"],
            ["hair_root_color_strength", 1, "", "Custom/RootColorStrength"],
            ["hair_end_color_strength", 1, "", "Custom/TipColorStrength"],
            ["hair_invert_root_map", 0, "", "Custom/InvertRootTip"],
            ["hair_highlight_a_color", (0.502886, 0.323143, 0.205079, 1.0), "func_color_linear", "Custom/_1st Dye Color"],
            ["hair_highlight_a_strength", 0.543, "", "Custom/_1st Dye Strength"],
            ["hair_highlight_a_start", 0.1, "func_index_1", "Custom/_1st Dye Distribution from Grayscale"],
            ["hair_highlight_a_mid", 0.2, "func_index_2", "Custom/_1st Dye Distribution from Grayscale"],
            ["hair_highlight_a_end", 0.3, "func_index_3", "Custom/_1st Dye Distribution from Grayscale"],
            ["hair_highlight_a_overlap_end", 0.99, "", "Custom/Mask 1st Dye by RootMap"],
            ["hair_highlight_a_overlap_invert", 0.99, "", "Custom/Invert 1st Dye RootMap Mask"],
            ["hair_highlight_b_color", (1, 1, 1, 1.0), "func_color_linear", "Custom/_2nd Dye Color"],
            ["hair_highlight_b_strength", 0, "", "Custom/_2nd Dye Strength"],
            ["hair_highlight_b_start", 0.5, "func_index_1", "Custom/_2nd Dye Distribution from Grayscale"],
            ["hair_highlight_b_mid", 0.6, "func_index_2", "Custom/_2nd Dye Distribution from Grayscale"],
            ["hair_highlight_b_end", 0.7, "func_index_3", "Custom/_2nd Dye Distribution from Grayscale"],
            ["hair_highlight_b_overlap_end", 0, "", "Custom/Mask 2nd Dye by RootMap"],
            ["hair_highlight_b_overlap_invert", 0, "", "Custom/Invert 2nd Dye RootMap Mask"],
            ["hair_ao_strength", 1, "", "Pbr/AO"],
            ["hair_ao_occlude_all", 0, "", "Custom/AO Map Occlude All Lighting"],
            ["hair_blend_multiply_strength", 0, "", "Pbr/Blend"],
            ["hair_alpha_strength", 1, "", "Pbr/Opacity"],
            ["hair_opacity", 1, "", "Base/Opacity"],
            ["hair_normal_strength", 1, "", "Pbr/Normal"],
            ["hair_emission_strength", 0, "", "Pbr/Glow"],
            ["hair_displacement_strength", 1, "", "Pbr/Displacement"],
            # non json properties (just defaults)
            ["hair_subsurface_radius", 1.5, "DEF"],
            ["hair_anisotropic_shift", 0.75, "DEF"],
            ["hair_bump_strength", 1.0, "DEF"],
            ["hair_anisotropic_roughness", 0.0375, "DEF"],
            ["hair_anisotropic_color", (1.000000, 0.798989, 0.689939, 1.000000), "DEF"],
        ],
        # export variables to update json file on export that need special conversion
        # [json_id, default_value, function, prop_arg1, prop_arg2, prop_arg3...]
        "export": [
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
            ["PROP", "AO Strength", "hair_ao_strength", True, "AO Map"],
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
            ["PROP", "Start", "hair_highlight_a_start", True, "ID Map"],
            ["PROP", "Mid", "hair_highlight_a_mid", True, "ID Map"],
            ["PROP", "End", "hair_highlight_a_end", True, "ID Map"],
            ["PROP", "Strength", "hair_highlight_a_strength", True, "ID Map"],
            ["PROP", "Overlap Invert", "hair_highlight_a_overlap_invert", True, "ID Map"],
            ["PROP", "Overlap End", "hair_highlight_a_overlap_end", True, "ID Map"],
            ["SPACER"],
            ["PROP", "Highlight B", "hair_highlight_b_color", True, "ID Map"],
            ["PROP", "Start", "hair_highlight_b_start", True, "ID Map"],
            ["PROP", "Mid", "hair_highlight_b_mid", True, "ID Map"],
            ["PROP", "End", "hair_highlight_b_end", True, "ID Map"],
            ["PROP", "Strength", "hair_highlight_b_strength", True, "ID Map"],
            ["PROP", "Overlap Invert", "hair_highlight_b_overlap_invert", True, "ID Map"],
            ["PROP", "Overlap End", "hair_highlight_b_overlap_end", True, "ID Map"],
            ["HEADER",  "Surface", "SURFACE_DATA"],
            ["PROP", "Specular Scale", "hair_specular_scale", True],
            ["PROP", "Roughness Strength", "hair_roughness_strength", True],
            ["SPACER"],
            ["PROP", "Anisotropic", "hair_anisotropic", True, "#CYCLES"],
            ["PROP", "Anisotropic Roughness", "hair_anisotropic_roughness", True, "#EEVEE"],
            ["PROP", "Anisotropic Strength", "hair_anisotropic_strength", True, "#EEVEE"],
            ["PROP", "Anisotropic Color", "hair_anisotropic_color", False, "#EEVEE"],
            ["PROP", "Anisotropic Shift", "hair_anisotropic_shift", True],
            ["PROP", "Tangent Flip Green", "hair_tangent_flip_green", True],
            ["HEADER",  "Sub-surface", "SURFACE_NSURFACE"],
            ["PROP", "Subsurface Scale", "hair_subsurface_scale", True],
            ["PROP", "Subsurface Falloff", "hair_subsurface_falloff", False],
            ["PROP", "Subsurface Radius", "hair_subsurface_radius", True],
            ["HEADER",  "Opacity", "MOD_OPACITY"],
            ["PROP", "Alpha Strength", "hair_alpha_strength", True, "Alpha Map"],
            ["PROP", "Opacity", "hair_opacity", True, "Alpha Map"],
            ["HEADER",  "Normals", "NORMALS_FACE"],
            ["PROP", "Normal Strength", "hair_normal_strength", True, "Normal Map"],
            ["PROP", "Bump Strength", "hair_bump_strength", True, "Bump Map"],
            ["PROP", "Displacement", "hair_displacement_strength", True, "Displacement Map"],
            ["OP", "Generate Normal Map", "cc3.bake", "PLAY", "BAKE_FLOW_NORMAL", "Flow Map"], #, "!Normal Map"],
            ["PROP", "Tangent Vector", "hair_tangent_vector", False, "Flow Map"],
            ["HEADER",  "Emission", "LIGHT"],
            ["PROP", "Emissive Color", "hair_emissive_color", False],
            ["PROP", "Emission Strength", "hair_emission_strength", True],
        ],
        "basic": [
            ["Roughness Strength", "Roughness Max"],
        ],
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
    ["TEARLINE_RIGHT", "RLTearline", "rl_tearline_shader"],
    ["TEARLINE_LEFT", "RLTearline", "rl_tearline_shader"],
]


def get_texture_type(json_id):
    for tex_info in TEXTURE_TYPES:
        if tex_info[1] == json_id:
            return tex_info[0]


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


def get_shader_lookup(mat_cache):
    for shader in SHADER_LOOKUP:
        if shader[0] == mat_cache.material_type:
            return shader[2]
    return "rl_pbr_shader"


def get_rl_shader_lookup(mat_cache):
    for shader in SHADER_LOOKUP:
        if shader[0] == mat_cache.material_type:
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
    for shader_def in SHADER_MATRIX:
        if shader_def["rl_shader"] == rl_shader_name:
            return shader_def
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