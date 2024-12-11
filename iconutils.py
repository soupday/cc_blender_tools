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
import bpy.utils.previews

from . import utils

ICONS: bpy.utils.previews.ImagePreviewCollection = None
ICON_WRINKLE_REGIONS = None


def register():
    global ICONS
    global ICON_WRINKLE_REGIONS

    ICONS = bpy.utils.previews.new()
    ICON_WRINKLE_REGIONS = ICONS.load("wrinkle_bg", utils.get_resource_path("icons", "wrinkle_bg.png"), "IMAGE")


def unregister():
    global ICONS
    global ICON_WRINKLE_REGIONS

    ICONS.clear()
    ICON_WRINKLE_REGIONS = None