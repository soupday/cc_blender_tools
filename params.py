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

import bpy
from . import nodeutils
from . import utils
from . import vars

# when updating linked materials, attempt to update the properties in all the material types in the same list:
LINKED_MATERIALS = [
    ["SKIN_HEAD", "SKIN_BODY", "SKIN_ARM", "SKIN_LEG"],
    ["EYE_RIGHT", "CORNEA_RIGHT", "OCCLUSION_RIGHT", "TEARLINE_RIGHT",
     "EYE_LEFT", "CORNEA_LEFT", "OCCLUSION_LEFT", "TEARLINE_LEFT"],
    ["TEETH_UPPER", "TEETH_LOWER"],
    ["HAIR", "SMART_HAIR", "SCALP", "EYELASH"]
]

# These material types must be updated together as they share the same properties:
PAIRED_MATERIALS = [
    ["EYE_RIGHT", "CORNEA_RIGHT"],
    ["EYE_LEFT", "CORNEA_LEFT"],
]

# These properties must be updated as linked as they are duplicated across the linked materials and must be kept in sync:
FORCE_LINKED_PROPS = ["skin_blend", "skin_normal_blend", "skin_mouth_ao", "skin_nostril_ao", "skin_lips_ao",
                      "skin_head_micronormal", "skin_body_micronormal", "skin_arm_micronormal", "skin_leg_micronormal",
                      "skin_head_tiling", "skin_body_tiling", "skin_arm_tiling", "skin_leg_tiling",]

# TODO will need to work something out to separate left from right eye materials...
FORCE_LINKED_TYPES = []
#["EYE", "CORNEA", "OCCLUSION", "TEARLINE"]


PROP_DEPENDANTS = {
    "eye_shadow_radius": ["eye_shadow_hardness"],
    "eye_iris_radius": ["eye_iris_hardness"],
}

PROP_MATRIX = [
    # Base Color groups
    {   "start": "(color_",
        "end": "_mixer)",
        "groups": [

            {   "name": "_skin_",
                "inputs": [
                    ["AO Strength", "skin_ao"],
                    ["Blend Strength", "skin_blend"],
                    ["Mouth AO", "skin_mouth_ao"],
                    ["Nostril AO", "skin_nostril_ao"],
                    ["Lips AO", "skin_lips_ao"],
                ],
            },

            {   "name": "_eye_",
                "inputs": [
                    ["AO Strength", "eye_ao"],
                    ["Blend Strength", "eye_blend"],
                    ["Shadow Radius", "eye_shadow_radius"],
                    ["Shadow Hardness", "eye_shadow_hardness", "parameters.eye_shadow_hardness * parameters.eye_shadow_radius * 0.99"],
                    ["Corner Shadow", "eye_shadow_color"],
                    ["Sclera Brightness", "eye_sclera_brightness"],
                    ["Iris Brightness", "eye_iris_brightness"],
                    ["Sclera Hue", "eye_sclera_hue"],
                    ["Iris Hue", "eye_iris_hue"],
                    ["Sclera Saturation", "eye_sclera_saturation"],
                    ["Iris Saturation", "eye_iris_saturation"],
                    ["Limbus Color", "eye_limbus_color"],
                ],
            },

            {   "name": "_hair_",
                "inputs": [
                    ["AO Strength", "hair_ao"],
                    ["Blend Strength", "hair_blend"],
                    ["Diffuse Bright", "hair_brightness"],
                    ["Diffuse Contrast", "hair_contrast"],
                    ["Diffuse Hue", "hair_hue"],
                    ["Diffuse Saturation", "hair_saturation"],
                    ["Aniso Color", "hair_aniso_color"],
                    ["Aniso Strength", "hair_aniso_strength"],
                    ["Aniso Strength Cycles", "hair_aniso_strength_cycles"],
                    ["Base Color Strength", "hair_vertex_color_strength"],
                    ["Base Color Strength", "hair_vertex_color_strength"],
                    ["Base Color Map Strength", "hair_base_color_map_strength"],
                    ["Depth Blend Strength", "hair_depth_strength"],
                    ["Diffuse Strength", "hair_diffuse_strength"],
                    ["Global Strength", "hair_global_strength"],
                    ["Root Color", "hair_root_color", "gamma_correct(parameters.hair_root_color)"],
                    ["End Color", "hair_end_color", "gamma_correct(parameters.hair_end_color)"],
                    ["Root Color Strength", "hair_root_strength"],
                    ["End Color Strength", "hair_end_strength"],
                    ["Invert Root and End Color", "hair_invert_strand"],
                    ["Highlight A Start", "hair_a_start"],
                    ["Highlight A Mid", "hair_a_mid"],
                    ["Highlight A End", "hair_a_end"],
                    ["Highlight A Strength", "hair_a_strength"],
                    ["Highlight A Overlap End", "hair_a_overlap"],
                    ["Highlight Color A", "hair_a_color", "gamma_correct(parameters.hair_a_color)"],
                    ["Highlight B Start", "hair_b_start"],
                    ["Highlight B Mid", "hair_b_mid"],
                    ["Highlight B End", "hair_b_end"],
                    ["Highlight B Strength", "hair_b_strength"],
                    ["Highlight B Overlap End", "hair_b_overlap"],
                    ["Highlight Color B", "hair_b_color", "gamma_correct(parameters.hair_b_color)"],
                ],
            },

            {   "name": "_eyelash_",
                "inputs": [
                    ["AO Strength", "hair_ao"],
                ],
            },

            {   "name": "_teeth_",
                "inputs": [
                    ["AO Strength", "teeth_ao"],
                    ["Front", "teeth_front"],
                    ["Rear", "teeth_rear"],
                    ["Teeth Brightness", "teeth_teeth_brightness"],
                    ["Teeth Saturation", "teeth_teeth_desaturation", "1 - parameters.teeth_teeth_desaturation"],
                    ["Gums Brightness", "teeth_gums_brightness"],
                    ["Gums Saturation", "teeth_gums_desaturation", "1 - parameters.teeth_gums_desaturation"],
                ],
            },

            {   "name": "_tongue_",
                "inputs": [
                    ["AO Strength", "tongue_ao"],
                    ["Front", "tongue_front"],
                    ["Rear", "tongue_rear"],
                    ["Brightness", "tongue_brightness"],
                    ["Saturation", "tongue_desaturation", "1 - parameters.tongue_desaturation"],
                ],
            },

            {   "name": "_nails_",
                "inputs": [
                    ["AO Strength", "nails_ao"],
                ],
            },

            {   "name": "_default_",
                "inputs": [
                    ["AO Strength", "default_ao"],
                    ["Blend Strength", "default_blend"],
                ],
            },
        ],
    },

    # Subsurface groups
    {   "start": "(subsurface_",
        "end": "_mixer)",
        "groups": [

            {   "name": "_skin_",
                "inputs": [
                    ["Radius", "skin_sss_radius", "parameters.skin_sss_radius * vars.UNIT_SCALE"],
                    ["Falloff", "skin_sss_falloff"],
                ],
            },

            {   "name": "_eye_",
                "inputs": [
                    ["Radius1", "eye_sss_radius", "parameters.eye_sss_radius * vars.UNIT_SCALE"],
                    ["Radius2", "eye_sss_radius", "parameters.eye_sss_radius * vars.UNIT_SCALE"],
                    ["Falloff1", "eye_sss_falloff"],
                    ["Falloff2", "eye_sss_falloff"],
                ],
            },

            {   "name": "_hair_",
                "inputs": [
                    ["Radius", "hair_sss_radius", "parameters.hair_sss_radius * vars.UNIT_SCALE"],
                    ["Falloff", "hair_sss_falloff"],
                ],
            },

            {   "name": "_teeth_",
                "inputs": [
                    ["Radius1", "teeth_sss_radius", "parameters.teeth_sss_radius * vars.UNIT_SCALE"],
                    ["Radius2", "teeth_sss_radius", "parameters.teeth_sss_radius * vars.UNIT_SCALE"],
                    ["Falloff1", "teeth_sss_falloff"],
                    ["Falloff2", "teeth_sss_falloff"],
                    ["Scatter1", "teeth_gums_sss_scatter"],
                    ["Scatter2", "teeth_teeth_sss_scatter"],
                ],
            },

            {   "name": "_tongue_",
                "inputs": [
                    ["Scatter", "tongue_sss_scatter"],
                    ["Radius", "tongue_sss_radius", "parameters.tongue_sss_radius * vars.UNIT_SCALE"],
                    ["Falloff", "tongue_sss_falloff"],
                ],
            },

            {   "name": "_nails_",
                "inputs": [
                    ["Radius", "nails_sss_radius", "parameters.nails_sss_radius * vars.UNIT_SCALE"],
                    ["Falloff", "nails_sss_falloff"],
                ],
            },

            {   "name": "_default_",
                "inputs": [
                    ["Radius", "default_sss_radius", "parameters.default_sss_radius * vars.UNIT_SCALE"],
                    ["Falloff", "default_sss_falloff"],
                ],
            },
        ],
    },

    # MSR groups
    {   "start": "(msr_",
        "end": "_mixer)",
        "groups": [

            {   "name": ["_skin_head_", "_skin_body_", "_skin_arm_", "_skin_leg_"],
                "inputs": [
                    ["Roughness Power", "skin_roughness_power"],
                    ["Roughness Remap", "skin_roughness"],
                    ["Specular", "skin_specular"],
                ],
            },

            {   "name": "_eye_",
                "inputs": [
                    ["Specular1", "eye_specular"],
                    ["Roughness1", "eye_sclera_roughness"],
                ],
            },

            {   "name": "_cornea_",
                "inputs": [
                    ["Specular1", "eye_specular"],
                    ["Specular2", "eye_specular"],
                    ["Roughness1", "eye_sclera_roughness"],
                    ["Roughness2", "eye_iris_roughness"],
                ],
            },

            {   "name": "_hair_",
                "inputs": [
                    ["Roughness Remap", "hair_roughness"],
                    ["Specular", "hair_specular"],
                ],
            },

            {   "name": "_scalp_",
                "inputs": [
                    ["Roughness Remap", "hair_scalp_roughness"],
                    ["Specular", "hair_scalp_specular"],
                ],
            },

            {   "name": "_eyelash_",
                "inputs": [
                    ["Roughness Remap", "hair_eyelash_roughness"],
                    ["Specular", "hair_eyelash_specular"],
                ],
            },

            {   "name": "_teeth_",
                "inputs": [
                    ["Specular2", "teeth_specular"],
                ],
            },

            {   "name": "_tongue_",
                "inputs": [
                    ["Specular2", "tongue_specular"],
                    ["Roughness2", "tongue_roughness"],
                ],
            },

            {   "name": "_nails_",
                "inputs": [
                    ["Roughness Remap", "nails_roughness"],
                    ["Specular", "nails_specular"],
                ],
            },

            {   "name": "_default_",
                "inputs": [
                    ["Roughness Remap", "default_roughness"],
                ],
            },
        ],
    },

    # Normal groups
    {   "start": "(normal_",
        "end": "_mixer)",
        "groups": [

            {   "name": "_skin_head_",
                "inputs": [
                    ["Normal Blend Strength", "skin_normal_blend"],
                    ["Micro Normal Strength", "skin_head_micronormal"],
                ],
            },

            {   "name": "_skin_body_",
                "inputs": [
                    ["Normal Blend Strength", "skin_normal_blend"],
                    ["Micro Normal Strength", "skin_body_micronormal"],
                ],
            },

            {   "name": "_skin_arm_",
                "inputs": [
                    ["Normal Blend Strength", "skin_normal_blend"],
                    ["Micro Normal Strength", "skin_arm_micronormal"],
                ],
            },

            {   "name": "_skin_leg_",
                "inputs": [
                    ["Normal Blend Strength", "skin_normal_blend"],
                    ["Micro Normal Strength", "skin_leg_micronormal"],
                ],
            },

            {   "name": "_eye_",
                "inputs": [
                    ["Micro Normal Strength", "eye_sclera_normal", "1 - parameters.eye_sclera_normal"],
                    ["Sclera Normal Strength", "eye_sclera_normal", "1 - parameters.eye_sclera_normal"],
                    ["Blood Vessel Height", "eye_blood_vessel_height", "parameters.eye_blood_vessel_height/1000"],
                    ["Iris Bump Height", "eye_iris_bump_height", "parameters.eye_iris_bump_height/1000"],
                ],
            },

            {   "name": ["_hair_", "_scalp_", "_eyelash_"],
                "inputs": [
                    ["Bump Map Height", "hair_bump", "parameters.hair_bump / 1000"],
                    ["Bump Map Midpoint", "hair_fake_bump_midpoint"],
                ],
            },

            {   "name": "_teeth_",
                "inputs": [
                    ["Micro Normal Strength", "teeth_micronormal"],
                ],
            },

            {   "name": "_tongue_",
                "inputs": [
                    ["Micro Normal Strength", "tongue_micronormal"],
                ],
            },

            {   "name": "_nails_",
                "inputs": [
                    ["Micro Normal Strength", "nails_micronormal"],
                ],
            },

            {   "name": "_default_",
                "inputs": [
                    ["Normal Blend Strength", "default_normal_blend"],
                    ["Micro Normal Strength", "default_micronormal"],
                    ["Bump Map Height", "default_bump", "parameters.default_bump / 1000"],
                ],
            },
        ],
    },

    # Tiling groups
    {   "start": "(tiling_",
        "end": "_mapping)",
        "groups": [

            {   "name": "_skin_head_",
                "inputs": [
                    ["Tiling", "skin_head_tiling"],
                ],
            },

            {   "name": "_skin_body_",
                "inputs": [
                    ["Tiling", "skin_body_tiling"],
                ],
            },

            {   "name": "_skin_arm_",
                "inputs": [
                    ["Tiling", "skin_arm_tiling"],
                ],
            },

            {   "name": "_skin_leg_",
                "inputs": [
                    ["Tiling", "skin_leg_tiling"],
                ],
            },

            # TODO: this could be part of the iris mask group and linked...
            {   "name": "_normal_sclera_",
                "inputs": [
                    ["Tiling", "eye_sclera_tiling"],
                ],
            },

            # TODO: this could be part of the iris mask group and linked...
            {   "name": "_color_sclera_",
                "inputs": [
                    ["Tiling", "eye_sclera_scale", "1.0 / parameters.eye_sclera_scale"],
                ],
            },

            {   "name": "_teeth_",
                "inputs": [
                    ["Tiling", "teeth_tiling"],
                ],
            },

            {   "name": "_tongue_",
                "inputs": [
                    ["Tiling", "tongue_tiling"],
                ],
            },

            {   "name": "_nails_",
                "inputs": [
                    ["Tiling", "nails_tiling"],
                ],
            },

            {   "name": "_default_",
                "inputs": [
                    ["Tiling", "default_tiling"],
                ],
            },
        ],
    },

    # Mask groups
    {   "start": "(",
        "end": "_mask)",
        "groups": [

            {   "name": "(iris_mask)",
                "inputs": [
                    ["Scale", "eye_iris_scale", "1.0 / parameters.eye_iris_scale"],
                    ["Radius", "eye_iris_radius"],
                    ["Hardness", "eye_iris_hardness", "parameters.eye_iris_radius * parameters.eye_iris_hardness * 0.99"],
                    ["Limbus Radius", "eye_limbus_radius"],
                    ["Limbus Hardness", "eye_limbus_hardness"],
                ],
            },

            {   "name": "(eye_occlusion_mask)",
                "inputs": [
                    ["Strength", "eye_occlusion"],
                    ["Hardness", "eye_occlusion_hardness"],
                ],
            },

            {   "name": "(eye_occlusion_adv_mask)",
                "inputs": [
                    ["Strength", "eye_occlusion_strength"],
                    ["Strength2", "eye_occlusion_2nd_strength"],
                    ["Power", "eye_occlusion_power"],
                    ["Top Min", "eye_occlusion_top_min"],
                    ["Top Max", "eye_occlusion_top_max"],
                    ["Top Curve", "eye_occlusion_top_curve"],
                    ["Bottom Min", "eye_occlusion_bottom_min"],
                    ["Bottom Max", "eye_occlusion_bottom_max"],
                    ["Bottom Curve", "eye_occlusion_bottom_curve"],
                    ["Inner Min", "eye_occlusion_inner_min"],
                    ["Inner Max", "eye_occlusion_inner_max"],
                    ["Outer Min", "eye_occlusion_outer_min"],
                    ["Outer Max", "eye_occlusion_outer_max"],
                    ["Top2 Min", "eye_occlusion_2nd_top_min"],
                    ["Top2 Max", "eye_occlusion_2nd_top_max"],
                    ["Tear Duct Position", "eye_occlusion_tear_duct_position"],
                    ["Tear Duct Width", "eye_occlusion_tear_duct_width"],
                ],
            },
        ],
    },

    # Shaders
    {   "start": "(rl_",
        "end": "_shader)",
        "groups": [

            {   "name": "eye_occlusion_shader",
                "inputs": [
                    ["Color", "eye_occlusion_color"],
                    ["Strength", "eye_occlusion_strength"],
                    ["Strength2", "eye_occlusion_2nd_strength"],
                    ["Power", "eye_occlusion_power"],
                    ["Top Min", "eye_occlusion_top_min"],
                    ["Top Max", "eye_occlusion_top_max"],
                    ["Top Curve", "eye_occlusion_top_curve"],
                    ["Bottom Min", "eye_occlusion_bottom_min"],
                    ["Bottom Max", "eye_occlusion_bottom_max"],
                    ["Bottom Curve", "eye_occlusion_bottom_curve"],
                    ["Inner Min", "eye_occlusion_inner_min"],
                    ["Inner Max", "eye_occlusion_inner_max"],
                    ["Outer Min", "eye_occlusion_outer_min"],
                    ["Outer Max", "eye_occlusion_outer_max"],
                    ["Top2 Min", "eye_occlusion_2nd_top_min"],
                    ["Top2 Max", "eye_occlusion_2nd_top_max"],
                    ["Tear Duct Position", "eye_occlusion_tear_duct_position"],
                    ["Tear Duct Width", "eye_occlusion_tear_duct_width"],
                ],
            },

            {   "name": "skin_body_shader",
                "inputs": [
                    ["AO Strength", "skin_ao"],
                    ["Subsurface Falloff", "skin_sss_falloff"],
                    ["Subsurface Radius", "skin_sss_radius", "parameters.skin_sss_radius * vars.UNIT_SCALE"],
                    ["Roughness Power", "skin_roughness_power"],
                    ["Roughness Min", "skin_roughness"],
                    ["Roughness Max", "skin_roughness_max"],
                    ["Normal Strength", "skin_normal_strength"],
                    ["Micro Normal Strength", "skin_body_micronormal"],
                    ["Subsurface Scale", "skin_sss_scale"],
                    ["Unmasked Scatter Scale", "skin_unmasked_sss_scale"],
                    ["R Scatter Scale", "skin_r_sss_scale"],
                    ["G Scatter Scale", "skin_g_sss_scale"],
                    ["B Scatter Scale", "skin_b_sss_scale"],
                    ["A Scatter Scale", "skin_a_sss_scale"],
                    ["Micro Roughness Mod", "skin_micro_roughness_mod"],
                    ["Unmasked Roughness Mod", "skin_unmasked_roughness_mod"],
                    ["R Roughness Mod", "skin_r_roughness_mod"],
                    ["G Roughness Mod", "skin_g_roughness_mod"],
                    ["B Roughness Mod", "skin_b_roughness_mod"],
                    ["A Roughness Mod", "skin_a_roughness_mod"],
                    ["Emissive Color", "skin_emissive_color"],
                    ["Emission Strength", "skin_emission_strength"],
                ],
            },

            {   "name": "skin_arm_shader",
                "inputs": [
                    ["AO Strength", "skin_ao"],
                    ["Subsurface Falloff", "skin_sss_falloff"],
                    ["Subsurface Radius", "skin_sss_radius", "parameters.skin_sss_radius * vars.UNIT_SCALE"],
                    ["Roughness Power", "skin_roughness_power"],
                    ["Roughness Min", "skin_roughness"],
                    ["Roughness Max", "skin_roughness_max"],
                    ["Normal Strength", "skin_normal_strength"],
                    ["Micro Normal Strength", "skin_arm_micronormal"],
                    ["Subsurface Scale", "skin_sss_scale"],
                    ["Unmasked Scatter Scale", "skin_unmasked_sss_scale"],
                    ["R Scatter Scale", "skin_r_sss_scale"],
                    ["G Scatter Scale", "skin_g_sss_scale"],
                    ["B Scatter Scale", "skin_b_sss_scale"],
                    ["A Scatter Scale", "skin_a_sss_scale"],
                    ["Micro Roughness Mod", "skin_micro_roughness_mod"],
                    ["Unmasked Roughness Mod", "skin_unmasked_roughness_mod"],
                    ["R Roughness Mod", "skin_r_roughness_mod"],
                    ["G Roughness Mod", "skin_g_roughness_mod"],
                    ["B Roughness Mod", "skin_b_roughness_mod"],
                    ["A Roughness Mod", "skin_a_roughness_mod"],
                    ["Emissive Color", "skin_emissive_color"],
                    ["Emission Strength", "skin_emission_strength"],
                ],
            },

            {   "name": "skin_leg_shader",
                "inputs": [
                    ["AO Strength", "skin_ao"],
                    ["Subsurface Falloff", "skin_sss_falloff"],
                    ["Subsurface Radius", "skin_sss_radius", "parameters.skin_sss_radius * vars.UNIT_SCALE"],
                    ["Roughness Power", "skin_roughness_power"],
                    ["Roughness Min", "skin_roughness"],
                    ["Roughness Max", "skin_roughness_max"],
                    ["Normal Strength", "skin_normal_strength"],
                    ["Micro Normal Strength", "skin_leg_micronormal"],
                    ["Subsurface Scale", "skin_sss_scale"],
                    ["Unmasked Scatter Scale", "skin_unmasked_sss_scale"],
                    ["R Scatter Scale", "skin_r_sss_scale"],
                    ["G Scatter Scale", "skin_g_sss_scale"],
                    ["B Scatter Scale", "skin_b_sss_scale"],
                    ["A Scatter Scale", "skin_a_sss_scale"],
                    ["Micro Roughness Mod", "skin_micro_roughness_mod"],
                    ["Unmasked Roughness Mod", "skin_unmasked_roughness_mod"],
                    ["R Roughness Mod", "skin_r_roughness_mod"],
                    ["G Roughness Mod", "skin_g_roughness_mod"],
                    ["B Roughness Mod", "skin_b_roughness_mod"],
                    ["A Roughness Mod", "skin_a_roughness_mod"],
                    ["Emissive Color", "skin_emissive_color"],
                    ["Emission Strength", "skin_emission_strength"],
                ],
            },

            {   "name": "skin_head_shader",
                "inputs": [
                    ["Cavity AO Strength", "skin_cavity_ao_strength"],
                    ["Blend Strength", "skin_blend"],
                    ["AO Strength", "skin_ao"],
                    ["Mouth AO", "skin_mouth_ao"],
                    ["Nostril AO", "skin_nostril_ao"],
                    ["Lip AO", "skin_lips_ao"],
                    ["Subsurface Falloff", "skin_sss_falloff"],
                    ["Subsurface Radius", "skin_sss_radius", "parameters.skin_sss_radius * vars.UNIT_SCALE"],
                    ["Roughness Power", "skin_roughness_power"],
                    ["Roughness Min", "skin_roughness"],
                    ["Roughness Max", "skin_roughness_max"],
                    ["Normal Strength", "skin_normal_strength"],
                    ["Micro Normal Strength", "skin_head_micronormal"],
                    ["Normal Blend Strength", "skin_normal_blend"],
                    ["Subsurface Scale", "skin_sss_scale"],
                    ["Unmasked Scatter Scale", "skin_unmasked_sss_scale"],
                    ["Nose Scatter Scale", "skin_nose_sss_scale"],
                    ["Mouth Scatter Scale", "skin_mouth_sss_scale"],
                    ["Upper Lid Scatter Scale", "skin_upperlid_sss_scale"],
                    ["Inner Lid Scatter Scale", "skin_innerlid_sss_scale"],
                    ["Cheek Scatter Scale", "skin_cheek_sss_scale"],
                    ["Forehead Scatter Scale", "skin_forehead_sss_scale"],
                    ["Upper Lip Scatter Scale", "skin_upperlip_sss_scale"],
                    ["Chin Scatter Scale", "skin_chin_sss_scale"],
                    ["Ear Scatter Scale", "skin_ear_sss_scale"],
                    ["Neck Scatter Scale", "skin_neck_sss_scale"],
                    ["Micro Roughness Mod", "skin_micro_roughness_mod"],
                    ["Unmasked Roughness Mod", "skin_unmasked_roughness_mod"],
                    ["Nose Roughness Mod", "skin_nose_roughness_mod"],
                    ["Mouth Roughness Mod", "skin_mouth_roughness_mod"],
                    ["Upper Lid Roughness Mod", "skin_upperlid_roughness_mod"],
                    ["Inner Lid Roughness Mod", "skin_innerlid_roughness_mod"],
                    ["Cheek Roughness Mod", "skin_cheek_roughness_mod"],
                    ["Forehead Roughness Mod", "skin_forehead_roughness_mod"],
                    ["Upper Lip Roughness Mod", "skin_upperlip_roughness_mod"],
                    ["Chin Roughness Mod", "skin_chin_roughness_mod"],
                    ["Ear Roughness Mod", "skin_ear_roughness_mod"],
                    ["Neck Roughness Mod", "skin_neck_roughness_mod"],
                    ["Emissive Color", "skin_emissive_color"],
                    ["Emission Strength", "skin_emission_strength"],
                ],
            },

        ],
    },

    # Individual nodes
    {   "start": "",
        "end": "",
        "groups": [

            {   "name": "teeth_roughness",
                "inputs": [
                    [1, "teeth_roughness"],
                ],
            },

            {   "name": "eye_tearline_shader",
                "inputs": [
                    ["Alpha", "tearline_alpha"],
                    ["Roughness", "tearline_roughness"],
                ],
            },

            {   "name": "eye_occlusion_shader",
                "inputs": [
                    ["Base Color", "eye_occlusion_color"],
                ],
            },

            {   "name": "eye_occlusion_adv_shader",
                "inputs": [
                    ["Base Color", "eye_occlusion_color"],
                ],
            },

            {   "name": "hair_opacity",
                "inputs": [
                    [1, "hair_opacity"],
                ],
            },

            {   "name": "scalp_opacity",
                "inputs": [
                    [1, "hair_scalp_opacity"],
                ],
            },

            {   "name": "eyelash_opacity",
                "inputs": [
                    [1, "hair_eyelash_opacity"],
                ],
            },

            {   "name": "default_opacity",
                "inputs": [
                    [1, "default_opacity"],
                ],
            },

            # dummy entry so that 'eye_iris_depth_radius' wil update linked materials...
            {   "name": "_CC3IID_DO_NOT_MATCH_",
                "inputs": [
                    [0, "eye_iris_depth_radius"],
                ],
            },
        ],
    },
]

# property_name, material_type, modifer_type, modifer_name, eval_code
MODIFIER_MATRIX = [
    [ "eye_iris_depth", "EYE_RIGHT", "DISPLACE", "Eye_Displace_R", "mod.strength = parameters.eye_iris_depth"],
    [ "eye_pupil_scale", "EYE_RIGHT", "UV_WARP", "Eye_UV_Warp_R", "mod.scale = (1.0 / parameters.eye_pupil_scale, 1.0 / parameters.eye_pupil_scale)" ],

    [ "eye_iris_depth", "EYE_LEFT", "DISPLACE", "Eye_Displace_L", "mod.strength = parameters.eye_iris_depth"],
    [ "eye_pupil_scale", "EYE_LEFT", "UV_WARP", "Eye_UV_Warp_L", "mod.scale = (1.0 / parameters.eye_pupil_scale, 1.0 / parameters.eye_pupil_scale)" ],

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

    [ "tearline_displace", "TEARLINE_RIGHT", "DISPLACE", "Tearline_Displace_All_R", "mod.strength = -parameters.tearline_displace"],
    [ "tearline_inner", "TEARLINE_RIGHT", "DISPLACE", "Tearline_Displace_Inner_R", "mod.strength = -parameters.tearline_inner"],

    [ "tearline_displace", "TEARLINE_LEFT", "DISPLACE", "Tearline_Displace_All_L", "mod.strength = -parameters.tearline_displace"],
    [ "tearline_inner", "TEARLINE_LEFT", "DISPLACE", "Tearline_Displace_Inner_L", "mod.strength = -parameters.tearline_inner"],

]

TEXTURE_MATRIX = [
    # Shaders
    {   "start": "(rl_",
        "end": "_shader)",
        "groups": [

            {   "name": "skin_head_shader",
                "inputs": [
                    ["Diffuse Map", "", vars.BASE_COLOR_MAP, "diffuse"],
                    ["Blend Map", "", vars.MOD_BASECOLORBLEND_MAP, "color_blend"],
                    ["AO Mask", "", vars.MOD_AO_MAP, "ao"],
                    ["MCMAO Map", "MCMAO Alpha", vars.MOD_MCMAO_MAP, "mcmao"],
                    ["Subsurface Mask", "", vars.SUBSURFACE_MAP, "sss"],
                    ["Transmission Mask", "", vars.MOD_TRANSMISSION_MAP, "transmision"],
                    ["Metallic Map", "", vars.METALLIC_MAP, "metallic"],
                    ["Specular Map", "", vars.SPECULAR_MAP, "specular"],
                    ["Specular Mask", "", vars.MOD_SPECMASK_MAP, "specular_mask"],
                    ["Roughness Map", "", vars.ROUGHNESS_MAP, "roughness"],
                    ["Normal Map", "", vars.NORMAL_MAP, "normal"],
                    ["Normal Blend Map", "", vars.MOD_NORMALBLEND_MAP, "normal_blend"],
                    ["Micro Normal Map", "", vars.MOD_MICRONORMAL_MAP, "micro_normal", "skin_head_tiling"],
                    ["Micro Normal Mask", "", vars.MOD_MICRONORMALMASK_MAP, "micro_normal_mask"],
                    ["NMUIL Map", "NMUIL Alpha", vars.MOD_NMUIL_MAP, "nmuil_mask"],
                    ["CFULC Map", "CFULC Alpha", vars.MOD_CFULC_MAP, "cfulc_mask"],
                    ["EN Map", "", vars.MOD_EN_MAP, "en_mask"],
                    ["Emission Map", "", vars.EMISSION_MAP, "emission"],
                ],
            },

            {   "name": "skin_body_shader",
                "inputs": [
                    ["Diffuse Map", "", vars.BASE_COLOR_MAP, "diffuse"],
                    ["AO Mask", "", vars.MOD_AO_MAP, "ao"],
                    ["Subsurface Mask", "", vars.SUBSURFACE_MAP, "sss"],
                    ["Transmission Mask", "", vars.MOD_TRANSMISSION_MAP, "transmision"],
                    ["Metallic Map", "", vars.METALLIC_MAP, "metallic"],
                    ["Specular Map", "", vars.SPECULAR_MAP, "specular"],
                    ["Specular Mask", "", vars.MOD_SPECMASK_MAP, "specular_mask"],
                    ["Roughness Map", "", vars.ROUGHNESS_MAP, "roughness"],
                    ["Normal Map", "", vars.NORMAL_MAP, "normal"],
                    ["Normal Blend Map", "", vars.MOD_NORMALBLEND_MAP, "normal_blend"],
                    ["Micro Normal Map", "", vars.MOD_MICRONORMAL_MAP, "micro_normal", "skin_body_tiling"],
                    ["Micro Normal Mask", "", vars.MOD_MICRONORMALMASK_MAP, "micro_normal_mask"],
                    ["RGBA Map", "RGBA Alpha", vars.MOD_RGBA_MAP, "rgba_mask"],
                    ["Emission Map", "", vars.EMISSION_MAP, "emission"],
                ],
            },

            {   "name": "skin_arm_shader",
                "inputs": [
                    ["Diffuse Map", "", vars.BASE_COLOR_MAP, "diffuse"],
                    ["AO Mask", "", vars.MOD_AO_MAP, "ao"],
                    ["Subsurface Mask", "", vars.SUBSURFACE_MAP, "sss"],
                    ["Transmission Mask", "", vars.MOD_TRANSMISSION_MAP, "transmision"],
                    ["Metallic Map", "", vars.METALLIC_MAP, "metallic"],
                    ["Specular Map", "", vars.SPECULAR_MAP, "specular"],
                    ["Specular Mask", "", vars.MOD_SPECMASK_MAP, "specular_mask"],
                    ["Roughness Map", "", vars.ROUGHNESS_MAP, "roughness"],
                    ["Normal Map", "", vars.NORMAL_MAP, "normal"],
                    ["Normal Blend Map", "", vars.MOD_NORMALBLEND_MAP, "normal_blend"],
                    ["Micro Normal Map", "", vars.MOD_MICRONORMAL_MAP, "micro_normal", "skin_arm_tiling", ""],
                    ["Micro Normal Mask", "", vars.MOD_MICRONORMALMASK_MAP, "micro_normal_mask"],
                    ["RGBA Map", "RGBA Alpha", vars.MOD_RGBA_MAP, "rgba_mask"],
                    ["Emission Map", "", vars.EMISSION_MAP, "emission"],
                ],
            },

            {   "name": "skin_leg_shader",
                "inputs": [
                    ["Diffuse Map", "", vars.BASE_COLOR_MAP, "diffuse"],
                    ["AO Mask", "", vars.MOD_AO_MAP, "ao"],
                    ["Subsurface Mask", "", vars.SUBSURFACE_MAP, "sss"],
                    ["Transmission Mask", "", vars.MOD_TRANSMISSION_MAP, "transmision"],
                    ["Metallic Map", "", vars.METALLIC_MAP, "metallic"],
                    ["Specular Map", "", vars.SPECULAR_MAP, "specular"],
                    ["Specular Mask", "", vars.MOD_SPECMASK_MAP, "specular_mask"],
                    ["Roughness Map", "", vars.ROUGHNESS_MAP, "roughness"],
                    ["Normal Map", "", vars.NORMAL_MAP, "normal"],
                    ["Normal Blend Map", "", vars.MOD_NORMALBLEND_MAP, "normal_blend"],
                    ["Micro Normal Map", "", vars.MOD_MICRONORMAL_MAP, "micro_normal", "skin_leg_tiling"],
                    ["Micro Normal Mask", "", vars.MOD_MICRONORMALMASK_MAP, "micro_normal_mask"],
                    ["RGBA Map", "RGBA Alpha", vars.MOD_RGBA_MAP, "rgba_mask"],
                    ["Emission Map", "", vars.EMISSION_MAP, "emission"],
                ],
            },

        ],
    },
]

BASIC_PROPS = [
    ["OUT", "Value",    "", "skin_ao"],
    ["OUT", "Value",    "", "skin_basic_specular"],
    ["IN", "To Min",    "", "skin_basic_roughness"],
    ["OUT", "Value",    "", "eye_specular"],
    ["OUT", "Value",    "", "eye_basic_roughness"],
    ["OUT", "Value",    "", "eye_basic_normal"],
    ["IN", "Strength",  "", "eye_occlusion"],
    ["IN", "Value",     "eye_basic_hsv", "eye_basic_brightness"],
    ["OUT", "Value",    "", "teeth_specular"],
    ["IN", 1,           "", "teeth_roughness"],
    ["OUT", "Value",    "", "tongue_specular"],
    ["IN", 1,           "", "tongue_roughness"],
    ["OUT", "Value",    "", "nails_specular"],
    ["OUT", "Value",    "", "hair_ao"],
    ["OUT", "Value",    "", "hair_specular"],
    ["OUT", "Value",    "", "hair_scalp_specular"],
    ["OUT", "Value",    "", "hair_bump", "parameters.hair_bump / 1000"],
    ["OUT", "Value",    "", "default_ao"],
    ["OUT", "Value",    "", "default_bump", "parameters.default_bump / 1000"],
    ["IN", "Alpha",     "eye_tearline_shader", "tearline_alpha"],
    ["IN", "Roughness", "eye_tearline_shader", "tearline_roughness"],
]


def get_prop_matrix(prop_name):
    matrix = []
    for mixer in PROP_MATRIX:
        for group in mixer["groups"]:
            for input in group["inputs"]:
                if input[1] == prop_name:
                    matrix.append([mixer, group, input])
    return matrix


def get_prop_matrix_group(group_name):
    group_name = "(" + group_name + ")"
    for mixer in PROP_MATRIX:
        if mixer["start"] in group_name:
            if mixer["end"] in group_name:
                for group in mixer["groups"]:
                    if type(group["name"]) is list:
                        for name in group["name"]:
                            if name in group_name:
                                return group
                    else:
                        if group["name"] in group_name:
                            return group
    return None


def get_texture_matrix_group(group_name):
    group_name = "(" + group_name + ")"
    for mixer in TEXTURE_MATRIX:
        if mixer["start"] in group_name:
            if mixer["end"] in group_name:
                for group in mixer["groups"]:
                    if type(group["name"]) is list:
                        for name in group["name"]:
                            if name in group_name:
                                return group
                    else:
                        if group["name"] in group_name:
                            return group
    return None