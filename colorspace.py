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


import bpy
from . import utils, vars


ALL_COLORSPACES = []
DATA_COLORSPACES = []


def is_aces():
    context = vars.get_context()
    return context.scene.display_settings.display_device == "ACES"


def try_set_color_space(image : bpy.types.Image, color_space_ref):
    prefs = vars.prefs()

    try:
        image.colorspace_settings.name = color_space_ref
        return True
    except:
        pass

    if color_space_ref == "sRGB" or color_space_ref == prefs.aces_srgb_override:
        rgb_color_spaces = ["sRGB", "srgb", "role_matte_paint", "Utility - Linear - sRGB"]
        for color_space in rgb_color_spaces:
            try:
                image.colorspace_settings.name = color_space
                return True
            except:
                pass

    else:
        rgb_color_spaces = ["Non-Color", "non-color", "role_data", "Linear", "linear", "Utility - Raw",
                            "Generic Data", "generic data", "Linear BT.709", "Raw", "raw",
                            "Linear Tristimulus", "linear tristimulus"]
        for color_space in rgb_color_spaces:
            try:
                image.colorspace_settings.name = color_space
                return True
            except:
                pass

    utils.log_error(f"Unable to set color space: {color_space}")

    return False


def set_image_color_space(image : bpy.types.Image, ref_colorspace : str):
    prefs = vars.prefs()

    if is_aces():
        if ref_colorspace == "Non-Color":
            try_set_color_space(image, prefs.aces_data_override)
        else:
            try_set_color_space(image, prefs.aces_srgb_override)

    else:
        try_set_color_space(image, ref_colorspace)


def try_set_view_transform(view_transform):
    context = vars.get_context()

    try:
        context.scene.view_settings.view_transform = view_transform
        return True
    except:
        pass

    try:
        context.scene.view_settings.view_transform = "sRGB"
        return True
    except:
        pass

    return False


def try_set_look(look):
    context = vars.get_context()

    try:
        context.scene.view_settings.look = look
        return True
    except:
        pass

    try:
        context.scene.view_settings.look = "NONE"
        return True
    except:
        pass

    return False




def set_view_settings(view_transform, look, exposure, gamma):
    prefs = vars.prefs()
    context = vars.get_context()

    if is_aces():
        try_set_view_transform("sRGB")
        try_set_look("None")
        context.scene.view_settings.exposure = 0.0
        context.scene.view_settings.gamma = 1.0

    else:
        if view_transform == "AgX":
            if look == "Medium Contrast":
                look = "AgX - Base Contrast"
            elif look != "None":
                look = "AgX - " + look
        try_set_view_transform(view_transform)
        try_set_look(look)
        context.scene.view_settings.exposure = exposure
        context.scene.view_settings.gamma = gamma


def fetch_all_color_spaces(self, context):
    global ALL_COLORSPACES
    if not ALL_COLORSPACES:
        i = 0
        keys = bpy.types.Image.bl_rna.properties['colorspace_settings'].fixed_type.properties['name'].enum_items.keys()
        if "role_matte_paint" in keys:
            ALL_COLORSPACES.append(("role_matte_paint", "sRGB", "Default Aces Color (Utility - Linear - sRGB or role_matte_paint)", i))
            i += 1
        for key in keys:
            if key != key.lower():
                ALL_COLORSPACES.append((key, key, key, i))
                i += 1
    return ALL_COLORSPACES


def fetch_data_color_spaces(self, context):
    global DATA_COLORSPACES
    if not DATA_COLORSPACES:
        i = 0
        keys = bpy.types.Image.bl_rna.properties['colorspace_settings'].fixed_type.properties['name'].enum_items.keys()
        if "role_data" in keys:
            DATA_COLORSPACES.append(("role_data", "Raw", "Default Aces Non-Color (Utility - Raw or role_data)", i))
            i += 1
        for key in keys:
            key_lower = key.lower()
            if key != key_lower:
                if ("data" in key_lower or "raw" in key_lower or "linear" in key_lower or
                    "xyz" in key_lower or "non-color" in key_lower):
                    DATA_COLORSPACES.append((key, key, key, i))
                    i += 1
    return DATA_COLORSPACES


def set_sequencer_color_space(color_space):
    context = vars.get_context()
    if is_aces():
        if color_space == "Raw":
            context.scene.sequencer_colorspace_settings.name = "Utility - Raw"
        else:
            context.scene.sequencer_colorspace_settings.name = "Utility - Linear - sRGB"
    else:
        if utils.B400() and color_space == "Raw":
            context.scene.sequencer_colorspace_settings.name = "Non-Color"
        else:
            context.scene.sequencer_colorspace_settings.name = color_space
