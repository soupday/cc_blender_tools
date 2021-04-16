

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
                    ["Shadow Hardness", "eye_shadow_hardness", "props.eye_shadow_hardness * props.eye_shadow_radius * 0.99"],
                    ["Corner Shadow", "eye_shadow_color"],
                    ["Sclera Brightness", "eye_sclera_brightness"],
                    ["Iris Brightness", "eye_iris_brightness"],
                    ["Sclera Hue", "eye_sclera_hue"],
                    ["Iris Hue", "eye_iris_hue"],
                    ["Sclera Saturation", "eye_sclera_saturation"],
                    ["Iris Saturation", "eye_iris_saturation"],
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
                    ["Base Color Strength", "hair_vertex_color_strength"],
                    ["Base Color Strength", "hair_vertex_color_strength"],
                    ["Base Color Map Strength", "hair_base_color_map_strength"],
                    ["Depth Blend Strength", "hair_depth_strength"],
                    ["Diffuse Strength", "hair_diffuse_strength"],
                    ["Global Strength", "hair_global_strength"],
                    ["Root Color", "hair_root_color", "gamma_correct(props.hair_root_color, HAIR_GAMMA, HAIR_SAT, HAIR_VAL)"],
                    ["End Color", "hair_end_color", "gamma_correct(props.hair_end_color, HAIR_GAMMA, HAIR_SAT, HAIR_VAL)"],
                    ["Root Color Strength", "hair_root_strength"],
                    ["End Color Strength", "hair_end_strength"],
                    ["Invert Root and End Color", "hair_invert_strand"],
                    ["Highlight A Start", "hair_a_start"],
                    ["Highlight A Mid", "hair_a_mid"],
                    ["Highlight A End", "hair_a_end"],
                    ["Highlight A Strength", "hair_a_strength"],
                    ["Highlight A Overlap End", "hair_a_overlap"],
                    ["Highlight Color A", "hair_a_color", "gamma_correct(props.hair_a_color, HAIR_GAMMA, HAIR_SAT, HAIR_VAL)"],
                    ["Highlight B Start", "hair_b_start"],
                    ["Highlight B Mid", "hair_b_mid"],
                    ["Highlight B End", "hair_b_end"],
                    ["Highlight B Strength", "hair_b_strength"],
                    ["Highlight B Overlap End", "hair_b_overlap"],
                    ["Highlight Color B", "hair_b_color", "gamma_correct(props.hair_b_color, HAIR_GAMMA, HAIR_SAT, HAIR_VAL)"],
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
                    ["Teeth Saturation", "teeth_teeth_desaturation", "1 - props.teeth_teeth_desaturation"],
                    ["Gums Brightness", "teeth_gums_brightness"],
                    ["Gums Saturation", "teeth_gums_desaturation", "1 - props.teeth_gums_desaturation"],
                ],
            },

            {   "name": "_tongue_",
                "inputs": [
                    ["AO Strength", "tongue_ao"],
                    ["Front", "tongue_front"],
                    ["Rear", "tongue_rear"],
                    ["Brightness", "tongue_brightness"],
                    ["Saturation", "tongue_desaturation", "1 - props.tongue_desaturation"],
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
                    ["Radius", "skin_sss_radius", "props.skin_sss_radius * UNIT_SCALE"],
                    ["Falloff", "skin_sss_falloff"],
                ],
            },

            {   "name": "_eye_",
                "inputs": [
                    ["Radius1", "eye_sss_radius", "props.eye_sss_radius * UNIT_SCALE"],
                    ["Radius2", "eye_sss_radius", "props.eye_sss_radius * UNIT_SCALE"],
                    ["Falloff1", "eye_sss_falloff"],
                    ["Falloff2", "eye_sss_falloff"],
                ],
            },

            {   "name": "_hair_",
                "inputs": [
                    ["Radius", "hair_sss_radius", "props.hair_sss_radius * UNIT_SCALE"],
                    ["Falloff", "hair_sss_falloff"],
                ],
            },

            {   "name": "_teeth_",
                "inputs": [
                    ["Radius1", "teeth_sss_radius", "props.teeth_sss_radius * UNIT_SCALE"],
                    ["Radius2", "teeth_sss_radius", "props.teeth_sss_radius * UNIT_SCALE"],
                    ["Falloff1", "teeth_sss_falloff"],
                    ["Falloff2", "teeth_sss_falloff"],
                    ["Scatter1", "teeth_gums_sss_scatter"],
                    ["Scatter2", "teeth_teeth_sss_scatter"],
                ],
            },

            {   "name": "_tongue_",
                "inputs": [
                    ["Scatter", "tongue_sss_scatter"],
                    ["Radius", "tongue_sss_radius", "props.tongue_sss_radius * UNIT_SCALE"],
                    ["Falloff", "tongue_sss_falloff"],
                ],
            },

            {   "name": "_nails_",
                "inputs": [
                    ["Radius", "nails_sss_radius", "props.nails_sss_radius * UNIT_SCALE"],
                    ["Falloff", "nails_sss_falloff"],
                ],
            },

            {   "name": "_default_",
                "inputs": [
                    ["Radius", "default_sss_radius", "props.default_sss_radius * UNIT_SCALE"],
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
                    ["Roughness Remap", "skin_roughness"],
                    ["Specular", "skin_specular"],
                ],
            },

            {   "name": "_eye_",
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
                    ["Micro Normal Strength", "eye_sclera_normal", "1 - props.eye_sclera_normal"],
                ],
            },

            {   "name": ["_hair_", "_scalp_", "_eyelash_"],
                "inputs": [
                    ["Bump Map Height", "hair_bump", "props.hair_bump / 1000"],
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
                    ["Bump Map Height", "default_bump", "props.default_bump / 1000"],
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
                    ["Tiling", "eye_sclera_scale", "1.0 / props.eye_sclera_scale"],
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
                    ["Scale", "eye_iris_scale", "1.0 / props.eye_iris_scale"],
                    ["Radius", "eye_iris_radius"],
                    ["Hardness", "eye_iris_hardness", "props.eye_iris_radius * props.eye_iris_hardness * 0.99"],
                ],
            },

            {   "name": "(eye_occlusion_mask)",
                "inputs": [
                    ["Strength", "eye_occlusion"],
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
                    ["Alpha", "eye_tearline_alpha"],
                    ["Roughness", "eye_tearline_roughness"],
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
    ["OUT", "Value",    "", "hair_bump", "props.hair_bump / 1000"],
    ["OUT", "Value",    "", "default_ao"],
    ["OUT", "Value",    "", "default_bump", "props.default_bump / 1000"],
    ["IN", "Alpha",     "eye_tearline_shader", "eye_tearline_alpha"],
    ["IN", "Roughness", "eye_tearline_shader", "eye_tearline_roughness"],
]