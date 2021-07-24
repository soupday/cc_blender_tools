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
import os
import mathutils
from . import utils


def get_left_right_materials(obj):

    left = None
    right = None

    for idx in range(0, len(obj.material_slots)):
        slot = obj.material_slots[idx]
        name = slot.name.lower()
        if "_l" in name:
            left = slot.material
        elif "_r" in name:
            right = slot.material

    return left, right

def is_left_material(mat):
    if "_l" in mat.name.lower():
        return True
    return False

def is_right_material(mat):
    if "_r" in mat.name.lower():
        return True
    return False


def is_material_in_objects(mat, objects):
    if mat is not None:
        for obj in objects:
            if obj.type == "MESH":
                if mat.name in obj.data.materials:
                    return True
    return False