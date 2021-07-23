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
from . import utils



def move_mod_last(obj, mod):
    try:
        if bpy.context.view_layer.objects.active is not obj:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        num_mods = len(obj.modifiers)
        if mod is not None:
            max = 50
            while obj.modifiers.find(mod.name) < num_mods - 1:
                bpy.ops.object.modifier_move_down(modifier=mod.name)
            max -= 1
            if max == 0:
                return
    except Exception as e:
        utils.log_error("Unable to move to last, modifier: " + mod.name, e)


def move_mod_first(obj, mod):
    print(mod)
    try:
        if bpy.context.view_layer.objects.active is not obj:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        if mod is not None:
            max = 50
            while obj.modifiers.find(mod.name) > 0:
                bpy.ops.object.modifier_move_up(modifier=mod.name)
            max -= 1
            if max == 0:
                return
    except Exception as e:
        utils.log_error("Unable to move to first, modifier: " + mod.name, e)