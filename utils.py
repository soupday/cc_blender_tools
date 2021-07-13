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

import os

def is_same_path(pa, pb):
    return os.path.normcase(os.path.realpath(pa)) == os.path.normcase(os.path.realpath(pb))

def is_in_path(pa, pb):
    return os.path.normcase(os.path.realpath(pa)) in os.path.normcase(os.path.realpath(pb))

def object_has_material(obj, name):
    name = name.lower()
    if obj.type == "MESH":
        for mat in obj.data.materials:
            if name in mat.name.lower():
                return True
    return False