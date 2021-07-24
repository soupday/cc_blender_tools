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


# Modifier order
#

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


# Physics modifiers
#

def get_cloth_physics_mod(obj):
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == "CLOTH":
                return mod
    return None


def get_collision_physics_mod(obj):
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == "COLLISION":
                return mod
    return None


def get_weight_map_mods(obj):
    edit_mods = []
    mix_mods = []
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == "VERTEX_WEIGHT_EDIT" and vars.NODE_PREFIX in mod.name:
                edit_mods.append(mod)
            if mod.type == "VERTEX_WEIGHT_MIX" and vars.NODE_PREFIX in mod.name:
                mix_mods.append(mod)
    return edit_mods, mix_mods


def get_material_weight_map_mods(obj, mat):
    edit_mod = None
    mix_mod = None
    if obj is not None and mat is not None:
        for mod in obj.modifiers:
            if mod.type == "VERTEX_WEIGHT_EDIT" and (vars.NODE_PREFIX + mat.name + "_WeightEdit") in mod.name:
                edit_mod = mod
            if mod.type == "VERTEX_WEIGHT_MIX" and (vars.NODE_PREFIX + mat.name + "_WeightMix") in mod.name:
                mix_mod = mod
    return edit_mod, mix_mod


# Displacement mods
#

def init_displacement_mod(obj, mod, group_name, direction, strength):
    if mod and obj:
        if group_name is not None:
            mod.vertex_group = group_name
        mod.mid_level = 0
        mod.strength = strength
        mod.direction = direction
        mod.space = "LOCAL"
