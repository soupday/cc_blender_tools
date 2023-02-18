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


ALL_COLORSPACES = []
DATA_COLORSPACES = []


def is_aces():
    return bpy.context.scene.display_settings.display_device == "ACES"


def set_image_color_space(image : bpy.types.Image, ref_colorspace : str):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if is_aces():
        if ref_colorspace == "Non-Color":
            image.colorspace_settings.name = prefs.aces_data_override
        else:
            image.colorspace_settings.name = prefs.aces_srgb_override

    else:
        image.colorspace_settings.name = ref_colorspace


def set_view_settings(view_transform, look, exposure, gamma):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if is_aces():
        bpy.context.scene.view_settings.view_transform = "sRGB"
        bpy.context.scene.view_settings.look = "None"
        bpy.context.scene.view_settings.exposure = 0.0
        bpy.context.scene.view_settings.gamma = 1.0

    else:
        bpy.context.scene.view_settings.view_transform = view_transform
        bpy.context.scene.view_settings.look = look
        bpy.context.scene.view_settings.exposure = exposure
        bpy.context.scene.view_settings.gamma = gamma


def fetch_all_color_spaces(self, context):
    global ALL_COLORSPACES
    if not ALL_COLORSPACES:
        i = 0
        keys = bpy.types.Image.bl_rna.properties['colorspace_settings'].fixed_type.properties['name'].enum_items.keys()
        if "aces" in keys:
            ALL_COLORSPACES.append(("role_matte_paint", "sRGB", "Default Aces Color (Utility - sRGB or role_matte_paint)", i))
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
