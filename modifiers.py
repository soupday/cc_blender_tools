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

from . import materials, meshutils, utils, vars


def get_object_modifier(obj, type, name = ""):
    if obj is not None:
        for mod in obj.modifiers:
            if name == "":
                if mod.type == type:
                    return mod
            else:
                if mod.type == type and mod.name.startswith(vars.NODE_PREFIX) and name in mod.name:
                    return mod
    return None


def remove_object_modifiers(obj, type, name = ""):
    to_remove = []
    if obj is not None:
        for mod in obj.modifiers:
            if name == "":
                if mod.type == type:
                    to_remove.append(mod)
            else:
                if mod.type == type and mod.name.startswith(vars.NODE_PREFIX) and name in mod.name:
                    to_remove.append(mod)

    for mod in to_remove:
        obj.modifiers.remove(mod)

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
                return True
    except Exception as e:
        utils.log_error("Unable to move to last, modifier: " + mod.name, e)
    return False


def move_mod_first(obj, mod):
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
                return True
    except Exception as e:
        utils.log_error("Unable to move to first, modifier: " + mod.name, e)
    return False


def add_armature_modifier(obj, create = False):
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == "ARMATURE":
                return mod
    return obj.modifiers.new(name = "Armature", type = "ARMATURE")


# Physics modifiers
#

def get_cloth_physics_mod(obj):
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == "CLOTH":
                return mod
    return None


def get_collision_physics_mod(chr_cache, obj):
    obj_cache = chr_cache.get_object_cache(obj)
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == "COLLISION":
                return mod
        if obj_cache and obj_cache.object_type == "BODY":
            if chr_cache.collision_body:
                try:
                    for mod in chr_cache.collision_body.modifiers:
                        if mod.type == "COLLISION":
                            return mod
                except:
                    pass
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
        mat_name = utils.strip_name(mat.name)
        for mod in obj.modifiers:
            if mod.type == "VERTEX_WEIGHT_EDIT" and (vars.NODE_PREFIX + mat_name + "_WeightEdit") in mod.name:
                edit_mod = mod
            if mod.type == "VERTEX_WEIGHT_MIX" and (vars.NODE_PREFIX + mat_name + "_WeightMix") in mod.name:
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


def fix_eye_mod_order(obj):
    """Moves the armature modifier to the end of the list
    """
    edit_mod = get_object_modifier(obj, "VERTEX_WEIGHT_EDIT", "Eye_WeightEdit")
    displace_mod = get_object_modifier(obj, "DISPLACE", "Eye_Displace")
    warp_mod = get_object_modifier(obj, "UV_WARP", "Eye_UV_Warp")
    move_mod_first(warp_mod)
    move_mod_first(displace_mod)
    move_mod_first(edit_mod)


def remove_eye_modifiers(obj):
    if obj and obj.type == "MESH":
        for mod in obj.modifiers:
            if vars.NODE_PREFIX in mod.name:
                if mod.type == "DISPLACE" or mod.type == "UV_WARP" or mod.type == "VERTEX_WEIGHT_EDIT":
                    obj.modifiers.remove(mod)


def add_eye_modifiers(obj):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    # fetch the eye materials (not the cornea materials)
    mat_left, mat_right = materials.get_left_right_eye_materials(obj)
    cache_left = props.get_material_cache(mat_left)
    cache_right = props.get_material_cache(mat_right)
    # Create the eye displacement group
    meshutils.generate_eye_vertex_groups(obj, mat_left, mat_right, cache_left, cache_right)
    remove_eye_modifiers(obj)

    if cache_left and cache_left.material_type == "EYE_LEFT":
        displace_mod_l = obj.modifiers.new(utils.unique_name("Eye_Displace_L"), "DISPLACE")
        warp_mod_l = obj.modifiers.new(utils.unique_name("Eye_UV_Warp_L"), "UV_WARP")
        init_displacement_mod(obj, displace_mod_l, prefs.eye_displacement_group + "_L", "Y", cache_left.parameters.eye_iris_depth)
        warp_mod_l.center = (0.5, 0.5)
        warp_mod_l.axis_u = "X"
        warp_mod_l.axis_v = "Y"
        warp_mod_l.vertex_group = prefs.eye_displacement_group + "_L"
        warp_mod_l.scale = (1.0 / cache_left.parameters.eye_pupil_scale, 1.0 / cache_left.parameters.eye_pupil_scale)
        move_mod_first(obj, warp_mod_l)
        move_mod_first(obj, displace_mod_l)

    if cache_right and cache_right.material_type == "EYE_RIGHT":
        displace_mod_r = obj.modifiers.new(utils.unique_name("Eye_Displace_R"), "DISPLACE")
        warp_mod_r = obj.modifiers.new(utils.unique_name("Eye_UV_Warp_R"), "UV_WARP")
        init_displacement_mod(obj, displace_mod_r, prefs.eye_displacement_group + "_R", "Y", cache_right.parameters.eye_iris_depth)
        warp_mod_r.center = (0.5, 0.5)
        warp_mod_r.axis_u = "X"
        warp_mod_r.axis_v = "Y"
        warp_mod_r.vertex_group = prefs.eye_displacement_group + "_R"
        warp_mod_r.scale = (1.0 / cache_right.parameters.eye_pupil_scale, 1.0 / cache_right.parameters.eye_pupil_scale)
        move_mod_first(obj, warp_mod_r)
        move_mod_first(obj, displace_mod_r)

    utils.log_info("Eye Displacement modifiers applied to: " + obj.name)


def add_eye_occlusion_modifiers(obj):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    mat_left, mat_right = materials.get_left_right_materials(obj)
    cache_left = props.get_material_cache(mat_left)
    cache_right = props.get_material_cache(mat_right)
    # generate the vertex groups for occlusion displacement
    meshutils.generate_eye_occlusion_vertex_groups(obj, mat_left, mat_right)
    remove_eye_modifiers(obj)

    if cache_left and cache_left.material_type == "OCCLUSION_LEFT":
        # re-create create the displacement modifiers
        displace_mod_inner_l = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Inner_L"), "DISPLACE")
        displace_mod_outer_l = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Outer_L"), "DISPLACE")
        displace_mod_top_l = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Top_L"), "DISPLACE")
        displace_mod_bottom_l = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Bottom_L"), "DISPLACE")
        displace_mod_all_l = obj.modifiers.new(utils.unique_name("Occlusion_Displace_All_L"), "DISPLACE")
        # initialise displacement mods
        init_displacement_mod(obj, displace_mod_inner_l, vars.OCCLUSION_GROUP_INNER + "_L", "NORMAL", cache_left.parameters.eye_occlusion_inner)
        init_displacement_mod(obj, displace_mod_outer_l, vars.OCCLUSION_GROUP_OUTER + "_L", "NORMAL", cache_left.parameters.eye_occlusion_outer)
        init_displacement_mod(obj, displace_mod_top_l, vars.OCCLUSION_GROUP_TOP + "_L", "NORMAL", cache_left.parameters.eye_occlusion_top)
        init_displacement_mod(obj, displace_mod_bottom_l, vars.OCCLUSION_GROUP_BOTTOM + "_L", "NORMAL", cache_left.parameters.eye_occlusion_bottom)
        init_displacement_mod(obj, displace_mod_all_l, vars.OCCLUSION_GROUP_ALL + "_L", "NORMAL", cache_left.parameters.eye_occlusion_displace)
        # fix mod order
        move_mod_first(obj, displace_mod_inner_l)
        move_mod_first(obj, displace_mod_outer_l)
        move_mod_first(obj, displace_mod_top_l)
        move_mod_first(obj, displace_mod_bottom_l)
        move_mod_first(obj, displace_mod_all_l)

    if cache_right and cache_right.material_type == "OCCLUSION_RIGHT":
        # re-create create the displacement modifiers
        displace_mod_inner_r = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Inner_R"), "DISPLACE")
        displace_mod_outer_r = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Outer_R"), "DISPLACE")
        displace_mod_top_r = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Top_R"), "DISPLACE")
        displace_mod_bottom_r = obj.modifiers.new(utils.unique_name("Occlusion_Displace_Bottom_R"), "DISPLACE")
        displace_mod_all_r = obj.modifiers.new(utils.unique_name("Occlusion_Displace_All_R"), "DISPLACE")
        # initialise displacement mods
        init_displacement_mod(obj, displace_mod_inner_r, vars.OCCLUSION_GROUP_INNER + "_R", "NORMAL", cache_right.parameters.eye_occlusion_inner)
        init_displacement_mod(obj, displace_mod_outer_r, vars.OCCLUSION_GROUP_OUTER + "_R", "NORMAL", cache_right.parameters.eye_occlusion_outer)
        init_displacement_mod(obj, displace_mod_top_r, vars.OCCLUSION_GROUP_TOP + "_R", "NORMAL", cache_right.parameters.eye_occlusion_top)
        init_displacement_mod(obj, displace_mod_bottom_r, vars.OCCLUSION_GROUP_BOTTOM + "_R", "NORMAL", cache_right.parameters.eye_occlusion_bottom)
        init_displacement_mod(obj, displace_mod_all_r, vars.OCCLUSION_GROUP_ALL + "_R", "NORMAL", cache_right.parameters.eye_occlusion_displace)
        # fix mod order
        move_mod_first(obj, displace_mod_inner_r)
        move_mod_first(obj, displace_mod_outer_r)
        move_mod_first(obj, displace_mod_top_r)
        move_mod_first(obj, displace_mod_bottom_r)
        move_mod_first(obj, displace_mod_all_r)

    utils.log_info("Eye Occlusion Displacement modifiers applied to: " + obj.name)


def add_tearline_modifiers(obj):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    mat_left, mat_right = materials.get_left_right_materials(obj)
    cache_left = props.get_material_cache(mat_left)
    cache_right = props.get_material_cache(mat_right)

    # generate the vertex groups for tearline displacement
    meshutils.generate_tearline_vertex_groups(obj, mat_left, mat_right)
    remove_eye_modifiers(obj)

    if cache_left and cache_left.material_type == "TEARLINE_LEFT":
        # re-create create the displacement modifiers
        displace_mod_inner_l = obj.modifiers.new(utils.unique_name("Tearline_Displace_Inner_L"), "DISPLACE")
        displace_mod_all_l = obj.modifiers.new(utils.unique_name("Tearline_Displace_All_L"), "DISPLACE")
        # initialise displacement mods
        init_displacement_mod(obj, displace_mod_inner_l, vars.TEARLINE_GROUP_INNER + "_L", "Y", -cache_left.parameters.tearline_inner)
        init_displacement_mod(obj, displace_mod_all_l, vars.TEARLINE_GROUP_ALL + "_L", "Y", -cache_left.parameters.tearline_displace)
        # fix mod order
        move_mod_first(obj, displace_mod_inner_l)
        move_mod_first(obj, displace_mod_all_l)

    if cache_right and cache_right.material_type == "TEARLINE_RIGHT":
        # re-create create the displacement modifiers
        displace_mod_inner_r = obj.modifiers.new(utils.unique_name("Tearline_Displace_Inner_R"), "DISPLACE")
        displace_mod_all_r = obj.modifiers.new(utils.unique_name("Tearline_Displace_All_R"), "DISPLACE")
        # initialise displacement mods
        init_displacement_mod(obj, displace_mod_inner_r, vars.TEARLINE_GROUP_INNER + "_R", "Y", -cache_right.parameters.tearline_inner)
        init_displacement_mod(obj, displace_mod_all_r, vars.TEARLINE_GROUP_ALL + "_R", "Y", -cache_right.parameters.tearline_displace)
        # fix mod order
        move_mod_first(obj, displace_mod_inner_r)
        move_mod_first(obj, displace_mod_all_r)

    utils.log_info("Tearline Displacement modifiers applied to: " + obj.name)


def add_decimate_modifier(obj, ratio):
    mod : bpy.types.DecimateModifier
    mod = get_object_modifier(obj, "DECIMATE", "Decimate_Collision_Body")
    if not mod:
        mod = obj.modifiers.new(utils.unique_name("Decimate_Collision_Body"), "DECIMATE")
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    return mod


def has_modifier(obj, modifier_type):
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == modifier_type:
                return True
    return False