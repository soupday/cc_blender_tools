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

LOC_AXES = {
        "x": ("location", "LOC_X", 0),
        "y": ("location", "LOC_Y", 1),
        "z": ("location", "LOC_Z", 2),
    }

ROT_AXES = {
    "x": ("rotation_euler", "ROT_X", 0),
    "y": ("rotation_euler", "ROT_Y", 1),
    "z": ("rotation_euler", "ROT_Z", 2),
}


FACERIG_EXT_CONFIG = {
    "CTRL_L_eye_blink":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [107, 110],
        "strength": False,
        "blendshapes":
        {
            "Eye_Blink_L": 1.0,
            "Eye_Wide_L": -1.0
        }
    },
    "CTRL_R_eye_blink":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [10, 13],
        "strength": False,
        "blendshapes":
        {
            "Eye_Blink_R": 1.0,
            "Eye_Wide_R": -1.0
        }
    },
    "CTRL_eye_pupil":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [168, 169],
        "strength": False,
        "blendshapes":
        {
            "Eye_Pupil_Dilate": 1.0,
            "Eye_Pupil_Contract": -1.0
        }
    },
    "CTRL_L_eye_squintInner":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [115, 116],
        "blendshapes": {"Eye_Squint_L": 1.0}
    },
    "CTRL_R_eye_squintInner":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [18, 19],
        "blendshapes": {"Eye_Squint_R": 1.0}
    },
    "CTRL_L_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_parent": "CTRL_C_eye",
        "y_parent": "CTRL_C_eye",
        "strength": False,
        "indices": [188, 189, 190, 191],
        "blendshapes":
        {
            "x":
            {
                "Eye_L_Look_L": 1.0,
                "Eye_L_Look_R": -1.0
            },
            "y":
            {
                "Eye_L_Look_Up": -1.0,
                "Eye_L_Look_Down": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [40.0, -30.0],
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.L",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [40.0, -30.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.L",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                }
            ]
        }

    },
    "CTRL_R_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_parent": "CTRL_C_eye",
        "y_parent": "CTRL_C_eye",
        "strength": False,
        "indices": [175, 174, 173, 172],
        "blendshapes":
        {
            "x":
            {
                "Eye_R_Look_L": 1.0,
                "Eye_R_Look_R": -1.0
            },
            "y":
            {
                "Eye_R_Look_Up": -1.0,
                "Eye_R_Look_Down": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [30.0, -40.0],
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [30.0, -40.0],
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                }
            ]
        }
    },
    "CTRL_C_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_method": "AVERAGE",
        "y_method": "AVERAGE",
        "strength": False,
        "indices": [176, 177, 178, 179],  #+172
        "blendshapes":
        {
            "x":
            {
                "Eye_R_Look_L": 1.0,
                "Eye_R_Look_R": -1.0,
                "Eye_L_Look_L": 1.0,
                "Eye_L_Look_R": -1.0
            },
            "y":
            {
                "Eye_R_Look_Up": -1.0,
                "Eye_R_Look_Down": 1.0,
                "Eye_L_Look_Up": -1.0,
                "Eye_L_Look_Down": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [30.0, -40.0]
                },
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [40.0, -30.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                },
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [30.0, -40.0]
                },
                {
                    "bone": "MCH-eye.L",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [40.0, -30.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                },
                {
                    "bone": "MCH-eye.L",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                }
            ]
        }
    },
    "CTRL_C_mouth":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [184, 187, 186, 185],
        "blendshapes":
        {
            "x":
            {
                "Mouth_L": 1.0,
                "Mouth_R": -1.0
            },
            "y":
            {
                "Mouth_Up": -1.0,
                "Mouth_Down": 1.0
            }
        }
    },
    "CTRL_C_jaw":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [0.0, 1.0],
        "y_invert": True,
        "indices": [202, 203, 204, 205],
        "blendshapes":
        {
            "x":
            {
                "Jaw_L": 1.0,
                "Jaw_R": -1.0
            },
            "y":
            {
                "Jaw_Open": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_JawRoot",
                    "axis": "y",
                    "offset": 0,
                    "translation": -0.658
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_JawRoot",
                    "axis": "z",
                    "offset": 0, # 90.0,
                    "rotation": 30.0
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "jaw_master",
                    "axis": "x",
                    "cc_axis": "y",
                    "offset": 0,
                    "translation": 0.658
                }
            ],
            "vertical":
            [
                {
                    "bone": "jaw_master",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0.0,
                    "rotation": 30.0
                }
            ]
        }
    },
    "CTRL_R_brow_lateral":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [2, 7],
        "blendshapes":
        {
            "Brow_Compress_R": 1.0
        }
    },
    "CTRL_L_brow_lateral":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [99, 104],
        "blendshapes":
        {
            "Brow_Compress_L": 1.0
        }
    },
    "CTRL_R_brow_down":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [4, 8],
        "blendshapes":
        {
            "Brow_Drop_R": 1.0
        }
    },
    "CTRL_L_brow_down":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [101, 105],
        "blendshapes":
        {
            "Brow_Drop_L": 1.0
        }
    },
    "CTRL_L_brow_raiseOut":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [97, 102],
        "blendshapes":
        {
            "Brow_Raise_Outer_L": 1.0
        }
    },
    "CTRL_L_brow_raiseIn":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [98, 103],
        "blendshapes":
        {
            "Brow_Raise_Inner_L": 1.0
        }
    },
    "CTRL_R_brow_raiseOut":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [0, 5],
        "blendshapes":
        {
            "Brow_Raise_Outer_R": 1.0
        }
    },
    "CTRL_R_brow_raiseIn":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [1, 6],
        "blendshapes":
        {
            "Brow_Raise_Inner_R": 1.0
        }
    },
    "CTRL_R_ear_up":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [15, 16],
        "blendshapes":
        {
            "Ear_Up_R": 1.0
        }
    },
    "CTRL_L_ear_up":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [112, 113],
        "blendshapes":
        {
            "Ear_Up_L": 1.0
        }
    },
    "CTRL_L_nose_wrinkleUpper":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [106, 133],
        "blendshapes":
        {
            "Nose_Sneer_L": 1.0
        }
    },
    "CTRL_R_nose_wrinkleUpper":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [9, 94],
        "blendshapes":
        {
            "Nose_Sneer_R": 1.0
        }
    },
    "CTRL_L_eye_cheekRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [111, 114],
        "blendshapes":
        {
            "Cheek_Raise_L": 1.0
        }
    },
    "CTRL_R_eye_cheekRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [14, 17],
        "blendshapes":
        {
            "Cheek_Raise_R": 1.0
        }
    },
    "CTRL_R_nose":
    {
        "widget_type": "rect",
        "x_range": [1.0, -1.0],
        "y_range": [1.0, -1.0],
        "y_invert": True,
        "x_mirror": True,
        "x_invert": True,
        "indices": [180, 181, 182, 183],
        "blendshapes":
        {
            "x":
            {
                "Nose_Nostril_Dilate_R": 1.0,
                "Nose_Nostril_In_R": -1.0
            },
            "y":
            {
                "Nose_Nostril_Raise_R": 1.0,
                "Nose_Nostril_Down_R": -1.0
            }
        }
    },
    "CTRL_L_nose":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "indices": [181, 192, 193, 182],
        "blendshapes":
        {
            "x":
            {
                "Nose_Nostril_Dilate_L": 1.0,
                "Nose_Nostril_In_L": -1.0
            },
            "y":
            {
                "Nose_Nostril_Raise_L": -1.0,
                "Nose_Nostril_Down_L": 1.0
            }
        }
    },
    "CTRL_L_mouth_lowerLipDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [126, 132],
        "blendshapes":
        {
            "Mouth_Down_Lower_L": 1.0
        }
    },
    "CTRL_R_mouth_lowerLipDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [27, 33],
        "blendshapes":
        {
            "Mouth_Down_Lower_R": 1.0
        }
    },
    "CTRL_L_mouth_cornerDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [124, 130],
        "blendshapes":
        {
            "Mouth_Frown_L": 1.0
        }
    },
    "CTRL_R_mouth_cornerDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [25, 31],
        "blendshapes":
        {
            "Mouth_Frown_R": 1.0
        }
    },
    "CTRL_L_mouth_cornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [122, 128],
        "blendshapes":
        {
            "Mouth_Smile_L": 1.0
        }
    },
    "CTRL_R_mouth_cornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [23, 29],
        "blendshapes":
        {
            "Mouth_Smile_R": 1.0
        }
    },
    "CTRL_L_mouth_upperLipRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [120, 119],
        "blendshapes":
        {
            "Mouth_Up_Upper_L": 1.0
        }
    },
    "CTRL_R_mouth_upperLipRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [21, 20],
        "blendshapes":
        {
            "Mouth_Up_Upper_R": 1.0
        }
    },
    "CTRL_L_mouth_sharpCornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [121, 127],
        "blendshapes":
        {
            "Mouth_Smile_Sharp_L": 1.0
        }
    },
    "CTRL_R_mouth_sharpCornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [22, 28],
        "blendshapes":
        {
            "Mouth_Smile_Sharp_R": 1.0
        }
    },
    "CTRL_L_mouth_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [125, 131],
        "blendshapes":
        {
            "Mouth_Stretch_L": 1.0
        }
    },
    "CTRL_R_mouth_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [26, 32],
        "blendshapes":
        {
            "Mouth_Stretch_R": 1.0
        }
    },
    "CTRL_L_mouth_dimple":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [123, 129],
        "blendshapes":
        {
            "Mouth_Dimple_L": 1.0
        }
    },
    "CTRL_R_mouth_dimple":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [24, 30],
        "blendshapes":
        {
            "Mouth_Dimple_R": 1.0
        }
    },
    "CTRL_R_mouth_towardsU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [61, 65],
        "blendshapes":
        {
            "Mouth_Push_Upper_R": 1.0
        }
    },
    "CTRL_R_mouth_towardsD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [59, 63],
        "blendshapes":
        {
            "Mouth_Push_Lower_R": 1.0
        }
    },
    "CTRL_L_mouth_towardsU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [60, 64],
        "blendshapes":
        {
            "Mouth_Push_Upper_L": 1.0
        }
    },
    "CTRL_L_mouth_towardsD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [58, 62],
        "blendshapes":
        {
            "Mouth_Push_Lower_L": 1.0
        }
    },
    "CTRL_R_mouth_purseU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [54, 69],
        "blendshapes":
        {
            "Mouth_Pucker_Up_R": 1.0
        }
    },
    "CTRL_R_mouth_purseD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [56, 67],
        "blendshapes":
        {
            "Mouth_Pucker_Down_R": 1.0
        }
    },
    "CTRL_L_mouth_purseU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [55, 68],
        "blendshapes":
        {
            "Mouth_Pucker_Up_L": 1.0
        }
    },
    "CTRL_L_mouth_purseD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [57, 66],
        "blendshapes":
        {
            "Mouth_Pucker_Down_L": 1.0
        }
    },
    "CTRL_R_mouth_funnelU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [70, 77],
        "blendshapes":
        {
            "Mouth_Funnel_Up_R": 1.0
        }
    },
    "CTRL_R_mouth_funnelD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [72, 75],
        "blendshapes":
        {
            "Mouth_Funnel_Down_R": 1.0
        }
    },
    "CTRL_L_mouth_funnelU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [71, 76],
        "blendshapes":
        {
            "Mouth_Funnel_Up_L": 1.0
        }
    },
    "CTRL_L_mouth_funnelD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [73, 74],
        "blendshapes":
        {
            "Mouth_Funnel_Down_L": 1.0
        }
    },
    "CTRL_R_mouth_lipBiteU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [78, 90],
        "blendshapes":
        {
            "Mouth_Roll_In_Upper_R": 1.0
        }
    },
    "CTRL_R_mouth_lipBiteD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [80, 92],
        "blendshapes":
        {
            "Mouth_Roll_In_Lower_R": 1.0
        }
    },
    "CTRL_L_mouth_lipBiteU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [79, 91],
        "blendshapes":
        {
            "Mouth_Roll_In_Upper_L": 1.0
        }
    },
    "CTRL_L_mouth_lipBiteD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [81, 93],
        "blendshapes":
        {
            "Mouth_Roll_In_Lower_L": 1.0
        }
    },
    "CTRL_R_mouth_tighten":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [82, 86],
        "blendshapes":
        {
            "Mouth_Tighten_R": 1.0
        }
    },
    "CTRL_L_mouth_tighten":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [83, 87],
        "blendshapes":
        {
            "Mouth_Tighten_L": 1.0
        }
    },
    "CTRL_C_jaw_chinRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [95, 96],
        "blendshapes":
        {
            "Mouth_Chin_Up": 1.0
        }
    },
    "CTRL_C_jaw_fwdBack":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [144, 145],
        "blendshapes":
        {
            "Jaw_Forward": 1.0,
            "Jaw_Backward": -1.0
        },
        "bones":
        [
            {
                "bone": "CC_Base_JawRoot",
                "axis": "x",
                "offset": 0, # 1.8288450241088867,
                "translation": [0.75, -0.5],
            }
        ],
        "rigify":
        [
            {
                "bone": "MCH-jaw_move",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "translation": [-0.75, 0.5],
            }
        ]
    },
    "CTRL_L_mouth_suckBlow":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [44, 42],
        "blendshapes":
        {
            "Cheek_Suck_L": 1.0,
            "Cheek_Puff_L": -1.0
        }
    },
    "CTRL_R_mouth_suckBlow":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [43, 45],
        "blendshapes":
        {
            "Cheek_Suck_R": 1.0,
            "Cheek_Puff_R": -1.0
        }
    },
    "CTRL_L_neck_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [149, 147],
        "blendshapes":
        {
            "Neck_Tighten_L": 1.0
        }
    },
    "CTRL_R_neck_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [148, 146],
        "blendshapes":
        {
            "Neck_Tighten_R": 1.0
        }
    },
    "CTRL_C_mouth_lipsTogether":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [152, 153],
        "soft": True,
        "blendshapes":
        {
            "Mouth_Close": 0.2
        }
    },
    "CTRL_R_mouth_press":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [84, 88],
        "blendshapes":
        {
            "Mouth_Press_R": 1.0
        }
    },
    "CTRL_L_mouth_press":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [85, 89],
        "blendshapes":
        {
            "Mouth_Press_L": 1.0
        }
    },
    "CTRL_C_tongue":  #270, 380
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [214, 215, 216, 217],
        "blendshapes":
        {
            "x":
            {
                "Tongue_L": 1.0,
                "Tongue_R": -1.0
            },
            "y":
            {
                "Tongue_Up": -1.0,
                "Tongue_Down": 1.0
            }
        }
    },
    "CTRL_C_tongue_inOut":  #250, 380
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [165, 164],
        "blendshapes":
        {
            "Tongue_In": 1.0,
            "Tongue_Out": -1.0
        }
    },
    "CTRL_C_tongue_tip":  #330, 380
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [218, 219, 220, 221],
        "blendshapes":
        {
            "x":
            {
                "Tongue_Tip_L": 1.0,
                "Tongue_Tip_R": -1.0
            },
            "y":
            {
                "Tongue_Tip_Up": -1.0,
                "Tongue_Tip_Down": 1.0
            }
        }
    },
    "CTRL_C_tongue_roll":  #370, 380
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [219, 222, 223, 220],
        "blendshapes":
        {
            "x":
            {
                "Tongue_Twist_L": 1.0,
                "Tongue_Twist_R": -1.0
            },
            "y":
            {
                "V_Tongue_Curl_U": -1.0,
                "V_Tongue_Curl_D": 1.0
            }
        }
    },
    "CTRL_C_tongue_press":  #310, 380
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [167, 166],
        "blendshapes":
        {
            "Tongue_Mid_Up": 1.0
        }
    },
    "CTRL_L_mouth_lipsBlow":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [156, 157],
        "blendshapes":
        {
            "Mouth_Blow_L": 1.0
        }
    },
    "CTRL_R_mouth_lipsBlow":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [154, 155],
        "blendshapes":
        {
            "Mouth_Blow_R": 1.0
        }
    },
    "CTRL_mouth_shrugDropU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [238, 239],
        "blendshapes":
        {
            "Mouth_Shrug_Upper": -1.0,
            "Mouth_Drop_Upper": 1.0,
        }
    },
    "CTRL_mouth_shrugDropD":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [240, 241],
        "blendshapes":
        {
            "Mouth_Shrug_Lower": -1.0,
            "Mouth_Drop_Lower": 1.0,
        }
    },
    "CTRL_C_tongue_narrowWide":  #300, 360
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [162, 163],
        "blendshapes":
        {
            "Tongue_Wide": 1.0,
            "Tongue_Narrow": -1.0
        }
    },
    "CTRL_R_nose_nasolabialDeepen":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [11, 12],
        "blendshapes":
        {
            "Nose_Crease_R": 1.0
        }
    },
    "CTRL_L_nose_nasolabialDeepen":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [108, 109],
        "blendshapes":
        {
            "Nose_Crease_L": 1.0
        }
    },
    "CTRL_R_mouth_lipsRollU":
    {
        "widget_type": "slider",
        "retarget": ["Mouth_Roll_Out_Upper_R"],
        "range": [-1.0, 1.0],
        "indices": [34, 36],
        "blendshapes":
        {
            "Mouth_Roll_In_Upper_R": 1.0,
            "Mouth_Roll_Out_Upper_R": -1.0
        }
    },
    "CTRL_R_mouth_lipsRollD":
    {
        "widget_type": "slider",
        "retarget": ["Mouth_Roll_Out_Lower_R"],
        "range": [-1.0, 1.0],
        "indices": [40, 38],
        "blendshapes":
        {
            "Mouth_Roll_In_Lower_R": 1.0,
            "Mouth_Roll_Out_Lower_R": -1.0
        }
    },
    "CTRL_L_mouth_lipsRollU":
    {
        "widget_type": "slider",
        "retarget": ["Mouth_Roll_Out_Upper_L"],
        "range": [-1.0, 1.0],
        "indices": [35, 37],
        "blendshapes":
        {
            "Mouth_Roll_In_Upper_L": 1.0,
            "Mouth_Roll_Out_Upper_L": -1.0
        }
    },
    "CTRL_L_mouth_lipsRollD":
    {
        "widget_type": "slider",
        "retarget": ["Mouth_Roll_Out_Lower_L"],
        "range": [-1.0, 1.0],
        "indices": [41, 39],
        "blendshapes":
        {
            "Mouth_Roll_In_Lower_L": 1.0,
            "Mouth_Roll_Out_Lower_L": -1.0
        }
    },
    "CTRL_R_mouth_corner":
    {
        "widget_type": "rect",
        "x_range": [1.0, -1.0],
        "y_range": [1.0, -1.0],
        "y_invert": True,
        "x_mirror": True,
        "x_invert": True,
        "retarget": [],
        "indices": [206, 207, 208, 209],
        "blendshapes":
        {
            "x":
            {
                "Mouth_Tighten_R": -1.0,
                "Mouth_Stretch_R": 1.0
            },
            "y":
            {
                "Mouth_Smile_Sharp_R": 1.0,
                "Mouth_Frown_R": -1.0
            }
        }
    },
    "CTRL_L_mouth_corner":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "retarget": [],
        "indices": [210, 211, 212, 213],
        "blendshapes":
        {
            "x":
            {
                "Mouth_Tighten_L": -1.0,
                "Mouth_Stretch_L": 1.0
            },
            "y":
            {
                "Mouth_Smile_Sharp_L": -1.0,
                "Mouth_Frown_L": 1.0
            }
        }
    },
    "CTRL_C_mouth_lipShiftU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [158, 159],
        "blendshapes":
        {
            "Mouth_Upper_L": 1.0,
            "Mouth_Upper_R": -1.0
        }
    },
    "CTRL_C_mouth_lipShiftD":
    {

        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [160, 161],
        "blendshapes":
        {
            "Mouth_Lower_L": 1.0,
            "Mouth_Lower_R": -1.0
        }
    },
    "CTRL_R_mouth_pushPullU":
    {

        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [50, 46],
        "blendshapes":
        {
            "Mouth_Push_Upper_R": -1.0,
            "Mouth_Pull_Upper_R": 1.0
        }
    },
    "CTRL_R_mouth_pushPullD":
    {

        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [52, 48],
        "blendshapes":
        {
            "Mouth_Push_Lower_R": -1.0,
            "Mouth_Pull_Lower_R": 1.0
        }
    },
    "CTRL_L_mouth_pushPullU":
    {

        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [51, 47],
        "blendshapes":
        {
            "Mouth_Push_Upper_L": -1.0,
            "Mouth_Pull_Upper_L": 1.0
        }
    },
    "CTRL_L_mouth_pushPullD":
    {

        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [53, 49],
        "blendshapes":
        {
            "Mouth_Push_Lower_L": -1.0,
            "Mouth_Pull_Lower_L": 1.0
        }
    },
    "CTRL_C_teethD":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "strength": False,
        "indices": [198, 199, 200, 201],
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_Teeth02",
                    "axis": "z",
                    "offset": 0, # -0.04119798541069031,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_Teeth02",
                    "axis": "y",
                    "offset": 0, # 1.249316930770874,
                    "translation": 1.0,
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "teeth.B",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "teeth.B",
                    "axis": "z",
                    "cc_axis": "y",
                    "offset": 0,
                    "translation": -1.0,
                }
            ]
        }
    },
    "CTRL_C_teethU":
    {

        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "strength": False,
        "indices": [194, 195, 196, 197],
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_Teeth01",
                    "axis": "z",
                    "offset": 0, # -0.03492468595504761,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_Teeth01",
                    "axis": "y",
                    "offset": 0, # -0.06047694757580757,
                    "translation": 1.0,
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "teeth.T",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "teeth.T",
                    "axis": "z",
                    "cc_axis": "y",
                    "offset": 0,
                    "translation": -1.0,
                }
            ]
        }
    },
    "CTRL_C_teeth_fwdBackD":
    {

        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "strength": False,
        "indices": [117, 134],
        "bones":
        [
            {
                "bone": "CC_Base_Teeth02",
                "axis": "x",
                "offset": 0, # 2.879988670349121,
                "translation": 1.0
            }
        ],
        "rigify":
        [
            {
                "bone": "teeth.B",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "translation": -1.0
            }
        ]
    },
    "CTRL_C_teeth_fwdBackU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "strength": False,
        "indices": [118, 135],
        "bones":
        [
            {
                "bone": "CC_Base_Teeth01",
                "axis": "x",
                "offset": 0, # -0.16094255447387695,
                "translation": 1.0
            }
        ],
        "rigify":
        [
            {
                "bone": "teeth.T",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "translation": -1.0
            }
        ]
    },
    "CTRL_R_eyelashU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [136, 138],
        "strength": False,
        "blendshapes":
        {
            "Eyelash_Upper_Up_R": -1.0,
            "Eyelash_Upper_Down_R": 1.0
        }
    },
    "CTRL_R_eyelashD":
    {

        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [142, 140],
        "strength": False,
        "blendshapes":
        {
            "Eyelash_Lower_Up_R": 1.0,
            "Eyelash_Lower_Down_R": -1.0
        }
    },
    "CTRL_L_eyelashU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [137, 139],
        "strength": False,
        "blendshapes":
        {
            "Eyelash_Upper_Up_L": -1.0,
            "Eyelash_Upper_Down_L": 1.0
        }
    },
    "CTRL_L_eyelashD":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [143, 141],
        "strength": False,
        "blendshapes":
        {
            "Eyelash_Lower_Up_L": 1.0,
            "Eyelash_Lower_Down_L": -1.0
        }
    },
    "CTRL_C_mouth_thickness":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [150, 151],
        "blendshapes":
        {
            "Mouth_Contract": 0.4
        }
    }
}


































FACERIG_STD_CONFIG = {
    "CTRL_L_eye_blink":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [47, 48],
        "strength": False,
        "blendshapes":
        {
            "Eye_Blink_L": 1.0,
            "Eye_Wide_L": -1.0
        }
    },
    "CTRL_R_eye_blink":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [8, 9],
        "strength": False,
        "blendshapes":
        {
            "Eye_Blink_R": 1.0,
            "Eye_Wide_R": -1.0
        }
    },
    "CTRL_L_eye_squintInner":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [51, 52],
        "blendshapes": {"Eye_Squint_L": 1.0}
    },
    "CTRL_R_eye_squintInner":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [12, 13],
        "blendshapes": {"Eye_Squint_R": 1.0}
    },
    "CTRL_L_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_parent": "CTRL_C_eye",
        "y_parent": "CTRL_C_eye",
        "strength": False,
        "indices": [86, 87, 88, 89],
        "blendshapes":
        {
            "x":
            {
                "Eye_L_Look_L": 1.0,
                "Eye_L_Look_R": -1.0
            },
            "y":
            {
                "Eye_L_Look_Up": -1.0,
                "Eye_L_Look_Down": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [40.0, -30.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.L",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [40.0, -30.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.L",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                }
            ]
        }

    },
    "CTRL_R_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_parent": "CTRL_C_eye",
        "y_parent": "CTRL_C_eye",
        "strength": False,
        "indices": [81,80,79,78],
        "blendshapes":
        {
            "x":
            {
                "Eye_R_Look_L": 1.0,
                "Eye_R_Look_R": -1.0
            },
            "y":
            {
                "Eye_R_Look_Up": -1.0,
                "Eye_R_Look_Down": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [30.0, -40.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [30.0, -40.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                }
            ]
        }
    },
    "CTRL_C_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_method": "AVERAGE",
        "y_method": "AVERAGE",
        "strength": False,
        "indices": [83, 84, 85, 82],
        "blendshapes":
        {
            "x":
            {
                "Eye_R_Look_L": 1.0,
                "Eye_R_Look_R": -1.0,
                "Eye_L_Look_L": 1.0,
                "Eye_L_Look_R": -1.0
            },
            "y":
            {
                "Eye_R_Look_Up": -1.0,
                "Eye_R_Look_Down": 1.0,
                "Eye_L_Look_Up": -1.0,
                "Eye_L_Look_Down": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [30.0, -40.0]
                },
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [40.0, -30.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                },
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [30.0, -40.0]
                },
                {
                    "bone": "MCH-eye.L",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [40.0, -30.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                },
                {
                    "bone": "MCH-eye.L",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                }
            ]
        }
    },
    "CTRL_C_mouth_Std":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [120, 121],
        "blendshapes":
        {
            "Mouth_L": 1.0,
            "Mouth_R": -1.0,
        },
    },
    "CTRL_C_jaw":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [0.0, 1.0],
        "y_invert": True,
        "indices": [99, 100, 101, 98],
        "blendshapes":
        {
            "x":
            {
                "Jaw_L": 1.0,
                "Jaw_R": -1.0
            },
            "y":
            {
                "Jaw_Open": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_JawRoot",
                    "axis": "y",
                    "offset": 0,
                    "translation": -0.658
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_JawRoot",
                    "axis": "z",
                    "offset": 0, # 90.0,
                    "rotation": 30.0
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "jaw_master",
                    "axis": "x",
                    "cc_axis": "y",
                    "offset": 0,
                    "translation": 0.658
                }
            ],
            "vertical":
            [
                {
                    "bone": "jaw_master",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0.0,
                    "rotation": 30.0
                }
            ]
        }
    },
    "CTRL_R_brow_down":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [3, 6],
        "blendshapes":
        {
            "Brow_Drop_R": 1.0
        }
    },
    "CTRL_L_brow_down":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [42, 45],
        "blendshapes":
        {
            "Brow_Drop_L": 1.0
        }
    },
    "CTRL_L_brow_raiseOut":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [39, 43],
        "blendshapes":
        {
            "Brow_Raise_Outer_L": 1.0
        }
    },
    "CTRL_L_brow_raiseIn":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [40, 44],
        "blendshapes":
        {
            "Brow_Raise_Inner_L": 1.0
        }
    },
    "CTRL_R_brow_raiseOut":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [0, 4],
        "blendshapes":
        {
            "Brow_Raise_Outer_R": 1.0
        }
    },
    "CTRL_R_brow_raiseIn":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [1, 5],
        "blendshapes":
        {
            "Brow_Raise_Inner_R": 1.0
        }
    },
    "CTRL_L_nose_wrinkleUpper":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [46, 67],
        "blendshapes":
        {
            "Nose_Sneer_L": 1.0
        }
    },
    "CTRL_R_nose_wrinkleUpper":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [7, 38],
        "blendshapes":
        {
            "Nose_Sneer_R": 1.0
        }
    },
    "CTRL_L_eye_cheekRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [49, 50],
        "blendshapes":
        {
            "Cheek_Raise_L": 1.0
        }
    },
    "CTRL_R_eye_cheekRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [10, 11],
        "blendshapes":
        {
            "Cheek_Raise_R": 1.0
        }
    },
    "CTRL_L_mouth_lowerLipDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [61, 66],
        "blendshapes":
        {
            "Mouth_Down_Lower_L": 1.0
        }
    },
    "CTRL_R_mouth_lowerLipDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [20, 25],
        "blendshapes":
        {
            "Mouth_Down_Lower_R": 1.0
        }
    },
    "CTRL_L_mouth_cornerDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [59, 64],
        "blendshapes":
        {
            "Mouth_Frown_L": 1.0
        }
    },
    "CTRL_R_mouth_cornerDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [18, 23],
        "blendshapes":
        {
            "Mouth_Frown_R": 1.0
        }
    },
    "CTRL_L_mouth_cornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [57, 62],
        "blendshapes":
        {
            "Mouth_Smile_L": 1.0
        }
    },
    "CTRL_R_mouth_cornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [16, 21],
        "blendshapes":
        {
            "Mouth_Smile_R": 1.0
        }
    },
    "CTRL_L_mouth_upperLipRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [56, 55],
        "blendshapes":
        {
            "Mouth_Up_Upper_L": 1.0
        }
    },
    "CTRL_R_mouth_upperLipRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [15, 14],
        "blendshapes":
        {
            "Mouth_Up_Upper_R": 1.0
        }
    },
    "CTRL_L_mouth_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [60, 65],
        "blendshapes":
        {
            "Mouth_Stretch_L": 1.0
        }
    },
    "CTRL_R_mouth_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [19, 24],
        "blendshapes":
        {
            "Mouth_Stretch_R": 1.0
        }
    },
    "CTRL_L_mouth_dimple":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [58, 63],
        "blendshapes":
        {
            "Mouth_Dimple_L": 1.0
        }
    },
    "CTRL_R_mouth_dimple":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [17, 22],
        "blendshapes":
        {
            "Mouth_Dimple_R": 1.0
        }
    },
    "CTRL_mouth_purse_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [30, 31],
        "blendshapes":
        {
            "Mouth_Pucker": 1.0
        }
    },
    "CTRL_mouth_funnel_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [32, 33],
        "blendshapes":
        {
            "Mouth_Funnel": 1.0
        }
    },
    "CTRL_mouth_lipBiteU_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [122, 123],
        "blendshapes":
        {
            "Mouth_Roll_In_Upper": 1.0
        }
    },
    "CTRL_mouth_lipBiteD_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [125, 124],
        "blendshapes":
        {
            "Mouth_Roll_In_Lower": 1.0
        }
    },
    "CTRL_C_jaw_fwdBack_Std":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [70, 71],
        "blendshapes":
        {
            "Jaw_Forward": 1.0,
        },
        "bones":
        [
            {
                "bone": "CC_Base_JawRoot",
                "axis": "x",
                "offset": 0, # 1.8288450241088867,
                "translation": [0.75, -0.5],
            }
        ],
        "rigify":
        [
            {
                "bone": "MCH-jaw_move",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "translation": [-0.75, 0.5],
            }
        ]
    },
    "CTRL_L_mouth_puff_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [26, 28],
        "blendshapes":
        {
            "Cheek_Puff_L": 1.0
        }
    },
    "CTRL_R_mouth_puff_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [29, 27],
        "blendshapes":
        {
            "Cheek_Puff_R": 1.0
        }
    },
    "CTRL_C_mouth_lipsTogether":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [72, 73],
        "soft": True,
        "blendshapes":
        {
            "Mouth_Close": 0.2
        }
    },
    "CTRL_R_mouth_press":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [34, 36],
        "blendshapes":
        {
            "Mouth_Press_R": 1.0
        }
    },
    "CTRL_L_mouth_press":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [35, 37],
        "blendshapes":
        {
            "Mouth_Press_L": 1.0
        }
    },
    "CTRL_C_tongue":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [110, 111, 112, 113],
        "blendshapes":
        {
            "x":
            {
                "Tongue_L": 1.0,
                "Tongue_R": -1.0
            },
            "y":
            {
                "Tongue_Up": -1.0,
                "Tongue_Down": 1.0
            }
        }
    },
    "CTRL_C_tongue_Out_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [76, 77],
        "blendshapes":
        {
            "Tongue_Out": 1.0
        }
    },
    "CTRL_C_tongue_tip_upDown_Std":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [126, 127],
        "blendshapes":
        {
            "Tongue_Tip_Up": -1.0,
            "Tongue_Tip_Down": 1.0
        }
    },
    "CTRL_C_tongue_roll_Std":  #370, 380
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_invert": False,
        "indices": [114, 116, 117, 115],
        "blendshapes":
        {
            "x":
            {
                "Tongue_Roll": 1.0,
            },
            "y":
            {
                "V_Tongue_Curl_U": -1.0,
                "V_Tongue_Curl_D": 1.0
            }
        }
    },
    "CTRL_mouth_shrugU_Std":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [133, 132],
        "blendshapes":
        {
            "Mouth_Shrug_Upper": 1.0,
        },
    },
    "CTRL_mouth_shrugD_Std":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [135, 134],
        "blendshapes":
        {
            "Mouth_Shrug_Lower": 1.0,
        }
    },
    "CTRL_C_tongue_narrowWide":  #300, 360
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [74, 75],
        "blendshapes":
        {
            "Tongue_Wide": 1.0,
            "Tongue_Narrow": -1.0
        }
    },
    "CTRL_mouth_lipsRollU_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [128, 129],
        "retarget": [],
        "blendshapes":
        {
            "Mouth_Roll_In_Upper": 1.0,
        }
    },
    "CTRL_mouth_lipsRollD_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [131, 130],
        "retarget": [],
        "blendshapes":
        {
            "Mouth_Roll_In_Lower": 1.0,
        }
    },
    "CTRL_R_mouth_corner_Std":
    {
        "widget_type": "rect",
        "x_range": [1.0, -1.0],
        "y_range": [1.0, -1.0],
        "y_invert": True,
        "x_mirror": True,
        "x_invert": True,
        "retarget": [],
        "negative": True,
        "indices": [102, 103, 104, 105],
        "blendshapes":
        {
            "x":
            {
                "Mouth_Stretch_R": 1.0
            },
            "y":
            {
                "Mouth_Frown_R": -1.0
            }
        }
    },
    "CTRL_L_mouth_corner_Std":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "retarget": [],
        "negative": True,
        "indices": [106, 107, 108, 109],
        "blendshapes":
        {
            "x":
            {
                "Mouth_Stretch_L": 1.0
            },
            "y":
            {
                "Mouth_Frown_L": 1.0
            }
        }
    },
    "CTRL_C_teethD":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "strength": False,
        "indices": [94, 95, 96, 97],
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_Teeth02",
                    "axis": "z",
                    "offset": 0, # -0.04119798541069031,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_Teeth02",
                    "axis": "y",
                    "offset": 0, # 1.249316930770874,
                    "translation": 1.0,
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "teeth.B",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "teeth.B",
                    "axis": "z",
                    "cc_axis": "y",
                    "offset": 0,
                    "translation": -1.0,
                }
            ]
        }
    },
    "CTRL_C_teethU":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "strength": False,
        "indices": [90, 91, 92, 93],
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_Teeth01",
                    "axis": "z",
                    "offset": 0, # -0.03492468595504761,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_Teeth01",
                    "axis": "y",
                    "offset": 0, # -0.06047694757580757,
                    "translation": 1.0,
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "teeth.T",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "teeth.T",
                    "axis": "z",
                    "cc_axis": "y",
                    "offset": 0,
                    "translation": -1.0,
                }
            ]
        }
    },
    "CTRL_C_teeth_fwdBackD":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "strength": False,
        "indices": [53, 68],
        "bones":
        [
            {
                "bone": "CC_Base_Teeth02",
                "axis": "x",
                "offset": 0, # 2.879988670349121,
                "translation": 1.0
            }
        ],
        "rigify":
        [
            {
                "bone": "teeth.B",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "translation": -1.0
            }
        ]
    },
    "CTRL_C_teeth_fwdBackU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "strength": False,
        "indices": [54, 69],
        "bones":
        [
            {
                "bone": "CC_Base_Teeth01",
                "axis": "x",
                "offset": 0, # -0.16094255447387695,
                "translation": 1.0
            }
        ],
        "rigify":
        [
            {
                "bone": "teeth.T",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "translation": -1.0
            }
        ]
    },
}































FACERIG_TRA_CONFIG = {
    "CTRL_L_eye_blink":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [47, 48],
        "strength": False,
        "blendshapes":
        {
            "A14_Eye_Blink_Left": 1.0,
            "A18_Eye_Wide_Left": -1.0
        }
    },
    "CTRL_R_eye_blink":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [8, 9],
        "strength": False,
        "blendshapes":
        {
            "A15_Eye_Blink_Right": 1.0,
            "A19_Eye_Wide_Right": -1.0
        }
    },
    "CTRL_L_eye_squintInner":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [51, 52],
        "blendshapes": {"A16_Eye_Squint_Left": 1.0}
    },
    "CTRL_R_eye_squintInner":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [12, 13],
        "blendshapes": {"A17_Eye_Squint_Right": 1.0}
    },
    "CTRL_L_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_parent": "CTRL_C_eye",
        "y_parent": "CTRL_C_eye",
        "strength": False,
        "indices": [86, 87, 88, 89],
        "blendshapes":
        {
            "x":
            {
                "A10_Eye_Look_Out_Left": 1.0,
                "A11_Eye_Look_In_Left": -1.0
            },
            "y":
            {
                "A06_Eye_Look_Up_Left": -1.0,
                "A08_Eye_Look_Down_Left": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [40.0, -30.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.L",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [40.0, -30.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.L",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                }
            ]
        }

    },
    "CTRL_R_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_parent": "CTRL_C_eye",
        "y_parent": "CTRL_C_eye",
        "strength": False,
        "indices": [81,80,79,78],
        "blendshapes":
        {
            "x":
            {
                "A12_Eye_Look_In_Right": 1.0,
                "A13_Eye_Look_Out_Right": -1.0
            },
            "y":
            {
                "A07_Eye_Look_Up_Right": -1.0,
                "A09_Eye_Look_Down_Right": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [30.0, -40.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [30.0, -40.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                }
            ]
        }
    },
    "CTRL_C_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_method": "AVERAGE",
        "y_method": "AVERAGE",
        "strength": False,
        "indices": [83, 84, 85, 82],
        "blendshapes":
        {
            "x":
            {
                "A12_Eye_Look_In_Right": 1.0,
                "A13_Eye_Look_Out_Right": -1.0,
                "A10_Eye_Look_Out_Left": 1.0,
                "A11_Eye_Look_In_Left": -1.0
            },
            "y":
            {
                "A07_Eye_Look_Up_Right": -1.0,
                "A09_Eye_Look_Down_Right": 1.0,
                "A06_Eye_Look_Up_Left": -1.0,
                "A08_Eye_Look_Down_Left": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [30.0, -40.0]
                },
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "rotation": [40.0, -30.0]
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                },
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "rotation": [22.0, -20.0],
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [30.0, -40.0],
                },
                {
                    "bone": "MCH-eye.L",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "rotation": [40.0, -30.0],
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                },
                {
                    "bone": "MCH-eye.L",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "rotation": [-22.0, 20.0],
                }
            ]
        }
    },
    "CTRL_C_mouth":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [120, 121],
        "blendshapes":
        {
            "A31_Mouth_Left": 1.0,
            "A32_Mouth_Right": -1.0
        },
    },
    "CTRL_C_jaw":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [0.0, 1.0],
        "y_invert": True,
        "indices": [99, 100, 101, 98],
        "blendshapes":
        {
            "x":
            {
                "A27_Jaw_Left": 1.0,
                "A28_Jaw_Right": -1.0
            },
            "y":
            {
                "A25_Jaw_Open": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_JawRoot",
                    "axis": "y",
                    "offset": 0,
                    "translation": -0.658
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_JawRoot",
                    "axis": "z",
                    "offset": 0, # 90.0,
                    "rotation": 35.0
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "jaw_master",
                    "axis": "x",
                    "cc_axis": "y",
                    "offset": 0,
                    "translation": 0.658
                }
            ],
            "vertical":
            [
                {
                    "bone": "jaw_master",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0.0,
                    "rotation": 30.0
                }
            ]
        }
    },
    "CTRL_R_brow_down":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [3, 6],
        "blendshapes":
        {
            "A03_Brow_Down_Right": 1.0
        }
    },
    "CTRL_L_brow_down":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [42, 45],
        "blendshapes":
        {
            "A02_Brow_Down_Left": 1.0
        }
    },
    "CTRL_L_brow_raiseOut":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [39, 43],
        "blendshapes":
        {
            "A04_Brow_Outer_Up_Left": 1.0
        }
    },
    "CTRL_brow_raiseIn":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [40, 44],
        "blendshapes":
        {
            "A01_Brow_Inner_Up": 1.0
        }
    },
    "CTRL_R_brow_raiseOut":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [0, 4],
        "blendshapes":
        {
            "A05_Brow_Outer_Up_Right": 1.0
        }
    },
    "CTRL_L_nose_wrinkleUpper":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [46, 67],
        "blendshapes":
        {
            "A23_Nose_Sneer_Left": 1.0
        }
    },
    "CTRL_R_nose_wrinkleUpper":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [7, 38],
        "blendshapes":
        {
            "A24_Nose_Sneer_Right": 1.0
        }
    },
    "CTRL_L_eye_cheekRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [49, 50],
        "blendshapes":
        {
            "A21_Cheek_Squint_Left": 1.0
        }
    },
    "CTRL_R_eye_cheekRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [10, 11],
        "blendshapes":
        {
            "A22_Cheek_Squint_Right": 1.0
        }
    },
    "CTRL_L_mouth_lowerLipDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [61, 66],
        "blendshapes":
        {
            "A46_Mouth_Lower_Down_Left": 1.0
        }
    },
    "CTRL_R_mouth_lowerLipDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [20, 25],
        "blendshapes":
        {
            "A47_Mouth_Lower_Down_Right": 1.0
        }
    },
    "CTRL_L_mouth_cornerDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [59, 64],
        "blendshapes":
        {
            "A40_Mouth_Frown_Left": 1.0
        }
    },
    "CTRL_R_mouth_cornerDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [18, 23],
        "blendshapes":
        {
            "A41_Mouth_Frown_Right": 1.0
        }
    },
    "CTRL_L_mouth_cornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [57, 62],
        "blendshapes":
        {
            "A38_Mouth_Smile_Left": 1.0
        }
    },
    "CTRL_R_mouth_cornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [16, 21],
        "blendshapes":
        {
            "A39_Mouth_Smile_Right": 1.0
        }
    },
    "CTRL_L_mouth_upperLipRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [56, 55],
        "blendshapes":
        {
            "A44_Mouth_Upper_Up_Left": 1.0
        }
    },
    "CTRL_R_mouth_upperLipRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [15, 14],
        "blendshapes":
        {
            "A45_Mouth_Upper_Up_Right": 1.0
        }
    },
    "CTRL_L_mouth_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [60, 65],
        "blendshapes":
        {
            "A50_Mouth_Stretch_Left": 1.0
        }
    },
    "CTRL_R_mouth_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [19, 24],
        "blendshapes":
        {
            "A51_Mouth_Stretch_Right": 1.0
        }
    },
    "CTRL_L_mouth_dimple":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [58, 63],
        "blendshapes":
        {
            "A42_Mouth_Dimple_Left": 1.0
        }
    },
    "CTRL_R_mouth_dimple":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [17, 22],
        "blendshapes":
        {
            "A43_Mouth_Dimple_Right": 1.0
        }
    },
    "CTRL_mouth_purse_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [30, 31],
        "blendshapes":
        {
            "A30_Mouth_Pucker": 1.0
        }
    },
    "CTRL_mouth_funnel_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [32, 33],
        "blendshapes":
        {
            "A29_Mouth_Funnel": 1.0
        }
    },
    "CTRL_mouth_lipBiteU_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [122, 123],
        "blendshapes":
        {
            "A33_Mouth_Roll_Upper": 1.0
        }
    },
    "CTRL_mouth_lipBiteD_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [125, 124],
        "blendshapes":
        {
            "A34_Mouth_Roll_Lower": 1.0
        }
    },
    "CTRL_C_jaw_fwdBack_Std":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [70, 71],
        "blendshapes":
        {
            "A26_Jaw_Forward": 1.0,
        },
        "bones":
        [
            {
                "bone": "CC_Base_JawRoot",
                "axis": "x",
                "offset": 0, # 1.8288450241088867,
                "translation": [0.75, -0.5],
            }
        ],
        "rigify":
        [
            {
                "bone": "MCH-jaw_move",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "translation": [-0.75, 0.5],
            }
        ]
    },
    "CTRL_mouth_puff_Std":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [26, 28],
        "blendshapes":
        {
            "Cheeks_Suck": -1.0,
            "A20_Cheek_Puff": 1.0,
        }
    },
    "CTRL_C_mouth_lipsTogether":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [72, 73],
        "soft": True,
        "blendshapes":
        {
            "A37_Mouth_Close": 0.2
        }
    },
    "CTRL_R_mouth_press":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [34, 36],
        "blendshapes":
        {
            "A49_Mouth_Press_Right": 1.0
        }
    },
    "CTRL_L_mouth_press":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [35, 37],
        "blendshapes":
        {
            "A48_Mouth_Press_Left": 1.0
        }
    },
    "CTRL_C_tongue":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [110, 111, 112, 113],
        "blendshapes":
        {
            "x":
            {
                "T03_Tongue_Left": 1.0,
                "T04_Tongue_Right": -1.0
            },
            "y":
            {
                "T01_Tongue_Up": -1.0,
                "T02_Tongue_Down": 1.0
            }
        }
    },
    "CTRL_C_tongue_Out_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [76, 77],
        "blendshapes":
        {
            "A52_Tongue_Out": 1.0
        }
    },
    "CTRL_C_tongue_tip_upDown_Std":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [126, 127],
        "blendshapes":
        {
            "T06_Tongue_Tip_Up": -1.0,
            "T07_Tongue_Tip_Down": 1.0
        }
    },
    "CTRL_C_tongue_roll_Std":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_invert": False,
        "indices": [114, 116, 117, 115],
        "blendshapes":
        {
            "x":
            {
                "T05_Tongue_Roll": 1.0,
            },
            "y":
            {
                "V_Tongue_Curl_U": -1.0,
                "V_Tongue_Curl_D": 1.0
            }
        }
    },
    "CTRL_mouth_shrugU_Std":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [133, 132],
        "blendshapes":
        {
            "A35_Mouth_Shrug_Upper": 1.0,
        },
    },
    "CTRL_mouth_shrugD_Std":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [135, 134],
        "blendshapes":
        {
            "A36_Mouth_Shrug_Lower": 1.0,
        }
    },
    "CTRL_C_tongue_narrowWide":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [74, 75],
        "blendshapes":
        {
            "T08_Tongue_Width": 1.0,
            "V_Tongue_Narrow": -1.0
        }
    },
    "CTRL_mouth_lipsRollU_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [128, 129],
        "retarget": [],
        "blendshapes":
        {
            "A33_Mouth_Roll_Upper": 1.0,
        }
    },
    "CTRL_mouth_lipsRollD_Std":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [131, 130],
        "retarget": [],
        "blendshapes":
        {
            "A34_Mouth_Roll_Lower": 1.0,
        }
    },
    "CTRL_R_mouth_corner_Std":
    {
        "widget_type": "rect",
        "x_range": [1.0, -1.0],
        "y_range": [1.0, -1.0],
        "y_invert": True,
        "x_mirror": True,
        "x_invert": True,
        "retarget": [],
        "negative": True,
        "indices": [102, 103, 104, 105],
        "blendshapes":
        {
            "x":
            {
                "A51_Mouth_Stretch_Right": 1.0
            },
            "y":
            {
                "A41_Mouth_Frown_Right": -1.0
            }
        }
    },
    "CTRL_L_mouth_corner_Std":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "retarget": [],
        "negative": True,
        "indices": [106, 107, 108, 109],
        "blendshapes":
        {
            "x":
            {
                "A50_Mouth_Stretch_Left": 1.0
            },
            "y":
            {
                "A40_Mouth_Frown_Left": 1.0
            }
        }
    },
    "CTRL_C_teethD":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "strength": False,
        "indices": [94, 95, 96, 97],
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_Teeth02",
                    "axis": "z",
                    "offset": 0, # -0.04119798541069031,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_Teeth02",
                    "axis": "y",
                    "offset": 0, # 1.249316930770874,
                    "translation": 1.0,
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "teeth.B",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "teeth.B",
                    "axis": "z",
                    "cc_axis": "y",
                    "offset": 0,
                    "translation": -1.0,
                }
            ]
        }
    },
    "CTRL_C_teethU":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "strength": False,
        "indices": [90, 91, 92, 93],
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_Teeth01",
                    "axis": "z",
                    "offset": 0, # -0.03492468595504761,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_Teeth01",
                    "axis": "y",
                    "offset": 0, # -0.06047694757580757,
                    "translation": 1.0,
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "teeth.T",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0,
                    "translation": 1.0,
                }
            ],
            "vertical":
            [
                {
                    "bone": "teeth.T",
                    "axis": "z",
                    "cc_axis": "y",
                    "offset": 0,
                    "translation": -1.0,
                }
            ]
        }
    },
    "CTRL_C_teeth_fwdBackD":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "strength": False,
        "indices": [53, 68],
        "bones":
        [
            {
                "bone": "CC_Base_Teeth02",
                "axis": "x",
                "offset": 0, # 2.879988670349121,
                "translation": 1.0
            }
        ],
        "rigify":
        [
            {
                "bone": "teeth.B",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "translation": -1.0
            }
        ]
    },
    "CTRL_C_teeth_fwdBackU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "strength": False,
        "indices": [54, 69],
        "bones":
        [
            {
                "bone": "CC_Base_Teeth01",
                "axis": "x",
                "offset": 0, # -0.16094255447387695,
                "translation": 1.0
            }
        ],
        "rigify":
        [
            {
                "bone": "teeth.T",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "translation": -1.0
            }
        ]
    },
}


ARK_BONE_TARGETS = {
    "HeadYaw": {
        "bone": "head",
        "axis": "y",
        "rotation": 40,
    },
    "HeadPitch": {
        "bone": "head",
        "axis": "x",
        "rotation": 40,
    },
    "HeadRoll": {
        "bone": "head",
        "axis": "z",
        "rotation": 40,
    },
    "LeftEyeYaw": {
        "bone": "eye.L",
        "axis": "z",
        "rotation": -40,
    },
    "LeftEyePitch": {
        "bone": "eye.L",
        "axis": "x",
        "rotation": 40,
    },
    "LeftEyeRoll": {
        "bone": "eye.L",
        "axis": "y",
        "rotation": -40,
    },
    "RightEyeYaw": {
        "bone": "eye.R",
        "axis": "z",
        "rotation": -40,
    },
    "RightEyePitch": {
        "bone": "eye.R",
        "axis": "x",
        "rotation": 40,
    },
    "RightEyeRoll": {
        "bone": "eye.R",
        "axis": "y",
        "rotation": -40,
    },
}


ARKIT_SHAPE_KEY_TARGETS = {

    "EXT": {
        "browInnerUp": ["Brow_Raise_Inner_L", "Brow_Raise_Inner_R"],
        "browDownLeft": "Brow_Drop_L",
        "browDownRight": "Brow_Drop_R",
        "browOuterUpLeft": "Brow_Raise_Outer_L",
        "browOuterUpRight": "Brow_Raise_Outer_R",
        "eyeLookUpLeft": "Eye_L_Look_Up",
        "eyeLookUpRight": "Eye_R_Look_Up",
        "eyeLookDownLeft": "Eye_L_Look_Down",
        "eyeLookDownRight": "Eye_R_Look_Down",
        "eyeLookInLeft": "Eye_L_Look_R",
        "eyeLookInRight": "Eye_R_Look_L",
        "eyeLookOutLeft": "Eye_L_Look_L",
        "eyeLookOutRight": "Eye_R_Look_R",
        "eyeBlinkLeft": "Eye_Blink_L",
        "eyeBlinkRight": "Eye_Blink_R",
        "eyeSquintLeft": "Eye_Squint_L",
        "eyeSquintRight": "Eye_Squint_R",
        "eyeWideLeft": "Eye_Wide_L",
        "eyeWideRight": "Eye_Wide_R",
        "cheekPuff": ["Cheek_Puff_L", "Cheek_Puff_R"],
        "cheekSquintLeft": "Cheek_Raise_L",
        "cheekSquintRight": "Cheek_Raise_R",
        "noseSneerLeft": "Nose_Sneer_L",
        "noseSneerRight": "Nose_Sneer_R",
        "jawOpen": "Jaw_Open",
        "jawForward": "Jaw_Forward",
        "jawLeft": "Jaw_L",
        "jawRight": "Jaw_R",
        "mouthFunnel": ["Mouth_Funnel_Up_R", "Mouth_Funnel_Down_R", "Mouth_Funnel_Up_L", "Mouth_Funnel_Down_L"],
        "mouthPucker": ["Mouth_Pucker_Up_R", "Mouth_Pucker_Down_R", "Mouth_Pucker_Up_L", "Mouth_Pucker_Down_L"],
        "mouthLeft": "Mouth_L",
        "mouthRight": "Mouth_R",
        "mouthRollUpper": ["Mouth_Roll_In_Upper_L", "Mouth_Roll_In_Upper_R"],
        "mouthRollLower": ["Mouth_Roll_In_Lower_L", "Mouth_Roll_In_Lower_R"],
        "mouthShrugUpper": "Mouth_Shrug_Upper",
        "mouthShrugLower": "Mouth_Shrug_Lower",
        "mouthClose": "Mouth_Close",
        "mouthSmileLeft": "Mouth_Smile_L",
        "mouthSmileRight": "Mouth_Smile_R",
        "mouthFrownLeft": "Mouth_Frown_L",
        "mouthFrownRight": "Mouth_Frown_R",
        "mouthDimpleLeft": "Mouth_Dimple_L",
        "mouthDimpleRight": "Mouth_Dimple_R",
        "mouthUpperUpLeft": "Mouth_Up_Upper_L",
        "mouthUpperUpRight": "Mouth_Up_Upper_R",
        "mouthLowerDownLeft": "Mouth_Down_Lower_L",
        "mouthLowerDownRight": "Mouth_Down_Lower_R",
        "mouthPressLeft": "Mouth_Press_L",
        "mouthPressRight": "Mouth_Press_R",
        "mouthStretchLeft": "Mouth_Stretch_L",
        "mouthStretchRight": "Mouth_Stretch_R",
    },

    "STD": {
        "browInnerUp": ["Brow_Raise_Inner_L", "Brow_Raise_Inner_R"],
        "browDownLeft": "Brow_Drop_L",
        "browDownRight": "Brow_Drop_R",
        "browOuterUpLeft": "Brow_Raise_Outer_L",
        "browOuterUpRight": "Brow_Raise_Outer_R",
        "eyeLookUpLeft": "Eye_L_Look_Up",
        "eyeLookUpRight": "Eye_R_Look_Up",
        "eyeLookDownLeft": "Eye_L_Look_Down",
        "eyeLookDownRight": "Eye_R_Look_Down",
        "eyeLookInLeft": "Eye_L_Look_R",
        "eyeLookInRight": "Eye_R_Look_L",
        "eyeLookOutLeft": "Eye_L_Look_L",
        "eyeLookOutRight": "Eye_R_Look_R",
        "eyeBlinkLeft": "Eye_Blink_L",
        "eyeBlinkRight": "Eye_Blink_R",
        "eyeSquintLeft": "Eye_Squint_L",
        "eyeSquintRight": "Eye_Squint_R",
        "eyeWideLeft": "Eye_Wide_L",
        "eyeWideRight": "Eye_Wide_R",
        "cheekPuff": ["Cheek_Puff_L", "Cheek_Puff_R"],
        "cheekSquintLeft": "Cheek_Raise_L",
        "cheekSquintRight": "Cheek_Raise_R",
        "noseSneerLeft": "Nose_Sneer_L",
        "noseSneerRight": "Nose_Sneer_R",
        "jawOpen": "Jaw_Open",
        "jawForward": "Jaw_Forward",
        "jawLeft": "Jaw_L",
        "jawRight": "Jaw_R",
        "mouthFunnel": "Mouth_Funnel",
        "mouthPucker": "Mouth_Pucker",
        "mouthLeft": "Mouth_L",
        "mouthRight": "Mouth_R",
        "mouthRollUpper": "Mouth_Roll_In_Upper",
        "mouthRollLower": "Mouth_Roll_In_Lower",
        "mouthShrugUpper": "Mouth_Shrug_Upper",
        "mouthShrugLower": "Mouth_Shrug_Lower",
        "mouthClose": "Mouth_Close",
        "mouthSmileLeft": "Mouth_Smile_L",
        "mouthSmileRight": "Mouth_Smile_R",
        "mouthFrownLeft": "Mouth_Frown_L",
        "mouthFrownRight": "Mouth_Frown_R",
        "mouthDimpleLeft": "Mouth_Dimple_L",
        "mouthDimpleRight": "Mouth_Dimple_R",
        "mouthUpperUpLeft": "Mouth_Up_Upper_L",
        "mouthUpperUpRight": "Mouth_Up_Upper_R",
        "mouthLowerDownLeft": "Mouth_Down_Lower_L",
        "mouthLowerDownRight": "Mouth_Down_Lower_R",
        "mouthPressLeft": "Mouth_Press_L",
        "mouthPressRight": "Mouth_Press_R",
        "mouthStretchLeft": "Mouth_Stretch_L",
        "mouthStretchRight": "Mouth_Stretch_R",
    },

    "TRA": {
        "browInnerUp": "A01_Brow_Inner_Up",
        "browDownLeft": "A02_Brow_Down_Left",
        "browDownRight": "A03_Brow_Down_Right",
        "browOuterUpLeft": "A04_Brow_Outer_Up_Left",
        "browOuterUpRight": "A05_Brow_Outer_Up_Right",
        "eyeLookUpLeft": "A06_Eye_Look_Up_Left",
        "eyeLookUpRight": "A07_Eye_Look_Up_Right",
        "eyeLookDownLeft": "A08_Eye_Look_Down_Left",
        "eyeLookDownRight": "A09_Eye_Look_Down_Right",
        "eyeLookOutLeft": "A10_Eye_Look_Out_Left",
        "eyeLookInLeft": "A11_Eye_Look_In_Left",
        "eyeLookInRight": "A12_Eye_Look_In_Right",
        "eyeLookOutRight": "A13_Eye_Look_Out_Right",
        "eyeBlinkLeft": "A14_Eye_Blink_Left",
        "eyeBlinkRight": "A15_Eye_Blink_Right",
        "eyeSquintLeft": "A16_Eye_Squint_Left",
        "eyeSquintRight": "A17_Eye_Squint_Right",
        "eyeWideLeft": "A18_Eye_Wide_Left",
        "eyeWideRight": "A19_Eye_Wide_Right",
        "cheekPuff": "A20_Cheek_Puff",
        "cheekSquintLeft": "A21_Cheek_Squint_Left",
        "cheekSquintRight": "A22_Cheek_Squint_Right",
        "noseSneerLeft": "A23_Nose_Sneer_Left",
        "noseSneerRight": "A24_Nose_Sneer_Right",
        "jawOpen": "A25_Jaw_Open",
        "jawForward": "A26_Jaw_Forward",
        "jawLeft": "A27_Jaw_Left",
        "jawRight": "A28_Jaw_Right",
        "mouthFunnel": "A29_Mouth_Funnel",
        "mouthPucker": "A30_Mouth_Pucker",
        "mouthLeft": "A31_Mouth_Left",
        "mouthRight": "A32_Mouth_Right",
        "mouthRollUpper": "A33_Mouth_Roll_Upper",
        "mouthRollLower": "A34_Mouth_Roll_Lower",
        "mouthShrugUpper": "A35_Mouth_Shrug_Upper",
        "mouthShrugLower": "A36_Mouth_Shrug_Lower",
        "mouthClose": "A37_Mouth_Close",
        "mouthSmileLeft": "A38_Mouth_Smile_Left",
        "mouthSmileRight": "A39_Mouth_Smile_Right",
        "mouthFrownLeft": "A40_Mouth_Frown_Left",
        "mouthFrownRight": "A41_Mouth_Frown_Right",
        "mouthDimpleLeft": "A42_Mouth_Dimple_Left",
        "mouthDimpleRight": "A43_Mouth_Dimple_Right",
        "mouthUpperUpLeft": "A44_Mouth_Upper_Up_Left",
        "mouthUpperUpRight": "A45_Mouth_Upper_Up_Right",
        "mouthLowerDownLeft": "A46_Mouth_Lower_Down_Left",
        "mouthLowerDownRight": "A47_Mouth_Lower_Down_Right",
        "mouthPressLeft": "A48_Mouth_Press_Left",
        "mouthPressRight": "A49_Mouth_Press_Right",
        "mouthStretchLeft": "A50_Mouth_Stretch_Left",
        "mouthStretchRight": "A51_Mouth_Stretch_Right",
    },

}