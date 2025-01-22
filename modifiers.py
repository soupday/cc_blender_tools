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

from . import geom, materials, meshutils, utils, vars

MOD_MULTIRES = "MULTIRES"
MOD_MULTIRES_NAME = "Multi_Res_Sculpt"

def get_object_modifier(obj, type, name = "", before_type=None):
    if obj is not None:
        for mod in obj.modifiers:
            if before_type and mod.type == before_type:
                return None
            if name == "":
                if mod.type == type:
                    return mod
            else:
                if mod.type == type and mod.name.startswith(vars.NODE_PREFIX) and name in mod.name:
                    return mod
    return None


def remove_object_modifiers(obj, modifier_type=None, modifier_name="", except_mods: list = None):
    to_remove = []
    if except_mods:
        keep_names = [mod.name for mod in except_mods]
    else:
        keep_names = []
    if obj is not None:
        for mod in obj.modifiers:
            if mod.name in keep_names:
                continue
            if modifier_name == "":
                if not modifier_type or mod.type == modifier_type:
                    to_remove.append(mod)
            else:
                if (not modifier_type or mod.type == modifier_type) and mod.name.startswith(vars.NODE_PREFIX) and modifier_name in mod.name:
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
            max = len(obj.modifiers) + 1
            while obj.modifiers.find(mod.name) < num_mods - 1:
                bpy.ops.object.modifier_move_down(modifier=mod.name)
                if max == 0:
                    return True
                max -= 1
    except Exception as e:
        utils.log_error("Unable to move to last, modifier: " + mod.name, e)
    return False


def move_mod_first(obj, mod):
    try:
        if bpy.context.view_layer.objects.active is not obj:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        if mod is not None:
            max = len(obj.modifiers) + 1
            while obj.modifiers.find(mod.name) > 0:
                bpy.ops.object.modifier_move_up(modifier=mod.name)
                if max == 0:
                    return True
                max -= 1
    except Exception as e:
        utils.log_error("Unable to move to first, modifier: " + mod.name, e)
    return False


def get_armature_modifier(obj, create=False, armature=None):
    mod = None
    if obj is not None:
        for m in obj.modifiers:
            if m.type == "ARMATURE":
                mod = m
                break
    if create and not mod:
        mod = obj.modifiers.new(name="Armature", type="ARMATURE")
    if mod and armature:
        mod.object = armature
    return mod


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


def has_cloth_weight_map_mods(obj):
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == "VERTEX_WEIGHT_EDIT" and vars.NODE_PREFIX in mod.name:
                return True
            if mod.type == "VERTEX_WEIGHT_MIX" and vars.NODE_PREFIX in mod.name:
                return True
    return False


def get_material_weight_map_mods(obj, mat):
    edit_mod = None
    mix_mod = None
    if obj is not None and mat is not None:
        mat_name = utils.safe_export_name(mat.name)
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
    props = vars.props()
    prefs = vars.prefs()

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
        init_displacement_mod(obj, displace_mod_l, prefs.eye_displacement_group + "_L", "Y", 1.5 * cache_left.parameters.eye_iris_depth)
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
        init_displacement_mod(obj, displace_mod_r, prefs.eye_displacement_group + "_R", "Y", 1.5 * cache_right.parameters.eye_iris_depth)
        warp_mod_r.center = (0.5, 0.5)
        warp_mod_r.axis_u = "X"
        warp_mod_r.axis_v = "Y"
        warp_mod_r.vertex_group = prefs.eye_displacement_group + "_R"
        warp_mod_r.scale = (1.0 / cache_right.parameters.eye_pupil_scale, 1.0 / cache_right.parameters.eye_pupil_scale)
        move_mod_first(obj, warp_mod_r)
        move_mod_first(obj, displace_mod_r)

    utils.log_info("Eye Displacement modifiers applied to: " + obj.name)


def add_eye_occlusion_modifiers(obj):
    props = vars.props()
    prefs = vars.prefs()

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
    props = vars.props()
    prefs = vars.prefs()

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


def add_decimate_modifier(obj, ratio, name):
    mod: bpy.types.DecimateModifier
    mod = get_object_modifier(obj, "DECIMATE", name)
    if not mod:
        mod = obj.modifiers.new(utils.unique_name(name), "DECIMATE")
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    return mod


def add_subdivision(obj: bpy.types.Object, level, name, max_level=3, view_level=1):
    mod: bpy.types.SubsurfModifier
    mod = get_object_modifier(obj, "SUBSURF", name)
    if not mod:
        mod = obj.modifiers.new(utils.unique_name(name), "SUBSURF")
    level = min(max_level, level)
    view_level = min(view_level, level)
    mod.render_levels = level
    mod.levels = view_level
    mod.subdivision_type = "CATMULL_CLARK"
    mod.show_only_control_edges = True
    mod.uv_smooth = 'PRESERVE_BOUNDARIES'
    mod.boundary_smooth = 'PRESERVE_CORNERS'
    mod.use_creases = True
    mod.use_custom_normals = True
    return mod


def add_multi_res_modifier(obj, subdivisions, use_custom_normals = False, uv_smooth = "PRESERVE_BOUNDARIES", quality = 4):
    if utils.set_active_object(obj):
        mod : bpy.types.MultiresModifier
        mod = get_object_modifier(obj, "MULTIRES", "Multi_Res_Sculpt")
        if not mod:
            mod = obj.modifiers.new(utils.unique_name("Multi_Res_Sculpt"), "MULTIRES")
        try:
            mod.use_custom_normals = use_custom_normals
        except:
            pass
        mod.uv_smooth = uv_smooth
        mod.quality = quality
        if mod:
            for i in range(0, subdivisions):
                bpy.ops.object.multires_subdivide(modifier=mod.name, mode='CATMULL_CLARK')
    return mod


def get_multi_res_mod(obj):
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == "MULTIRES":
                return mod
    return None


def has_modifier(obj, modifier_type):
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == modifier_type:
                return True
    return False


def apply_modifier(obj, modifier=None, type=None, preserving=False):
    if obj:
        if not modifier and type:
            for mod in obj.modifiers:
                if mod.type == type:
                    modifier = mod
                    break

        if modifier:
            if preserving or utils.object_has_shape_keys(obj):
                copy = utils.duplicate_object(obj)
                utils.object_mode_to(copy)
                utils.set_only_active_object(copy)
                utils.remove_all_shape_keys(copy)
                remove_object_modifiers(copy, except_mods=[modifier])
                bpy.ops.object.modifier_apply(modifier=modifier.name)
                geom.copy_vert_positions_by_uv_id(copy, obj, flatten_udim=False)
                utils.delete_mesh_object(copy)
            else:
                utils.object_mode_to(obj)
                utils.set_only_active_object(obj)
                bpy.ops.object.modifier_apply(modifier=modifier.name)


def apply_modifier_with_shape_keys(obj, modifier=None, type=None):
    if obj:
        if not modifier and type:
            for mod in obj.modifiers:
                if mod.type == type:
                    modifier = mod
                    break
        if modifier:
            utils.object_mode_to(obj)
            utils.set_only_active_object(obj)
            copy = utils.duplicate_object(obj)
            copy.shape_key_remove()


def copy_base_shape(src_obj, dest_obj):
    geom.copy_vert_positions_by_uv_id(src_obj, dest_obj, accuracy = 5, flatten_udim=False)


def remove_material_weight_maps(obj, mat):
    """Removes the weight map 'Vertex Weight Edit' modifier for the object's material.

    This does not remove or delete the weight map image or temporary packed image,
    or the texture based on the weight map image, just the modifier.
    """

    edit_mod, mix_mod = get_material_weight_map_mods(obj, mat)
    if edit_mod is not None:
        utils.log_info("Removing weight map vertex edit modifer: " + edit_mod.name)
        obj.modifiers.remove(edit_mod)
    if mix_mod is not None:
        utils.log_info("Removing weight map vertex mix modifer: " + mix_mod.name)
        obj.modifiers.remove(mix_mod)


def add_material_weight_map_modifier(obj, mat, weight_map, vertex_group, normalize = False):
    """Attaches a weight map to the object's material via a 'Vertex Weight Edit' modifier.

    This will attach the supplied weight map or will try to find an existing weight map,
    but will not create a new weight map if it doesn't already exist.
    """

    if obj is None or mat is None or weight_map is None or not vertex_group:
        return

    # Make or re-use a texture based on the weight map image
    mat_name = utils.strip_name(mat.name)
    tex_name = mat_name + "_Weight"
    tex = None
    for t in bpy.data.textures:
        if t.name.startswith(vars.NODE_PREFIX + tex_name):
            tex = t
    if tex is None:
        tex = bpy.data.textures.new(utils.unique_name(tex_name), "IMAGE")
        utils.log_info("Texture: " + tex.name + " created for weight map transfer")
    else:
        utils.log_info("Texture: " + tex.name + " already exists for weight map transfer")
    tex.image = weight_map

    # Create the physics pin vertex group and the material weightmap group if they don't exist:
    mix_group = vertex_group
    material_group = vertex_group + "_" + mat_name
    if mix_group not in obj.vertex_groups:
        pin_vertex_group = obj.vertex_groups.new(name = mix_group)
    else:
        pin_vertex_group = obj.vertex_groups[mix_group]
    if material_group not in obj.vertex_groups:
        weight_vertex_group = obj.vertex_groups.new(name = material_group)
    else:
        weight_vertex_group = obj.vertex_groups[material_group]

    # The material weight map group should contain only those vertices affected by the material, default weight to 1.0
    meshutils.clear_vertex_group(obj, weight_vertex_group)
    mat_vert_indices = meshutils.get_material_vertex_indices(obj, mat)
    weight_vertex_group.add(mat_vert_indices, 1.0, 'ADD')

    # The pin group should contain all vertices in the mesh default weighted to 1.0
    meshutils.set_vertex_group(obj, pin_vertex_group, 1.0)

    # set the pin group in the cloth physics modifier
    mod_cloth = get_cloth_physics_mod(obj)
    if mod_cloth is not None:
        mod_cloth.settings.vertex_group_mass = mix_group

    # re-create or create the Vertex Weight Edit modifier and the Vertex Weight Mix modifer
    remove_material_weight_maps(obj, mat)
    edit_mod : bpy.types.VertexWeightEditModifier
    edit_mod = obj.modifiers.new(utils.unique_name(mat_name + "_WeightEdit"), "VERTEX_WEIGHT_EDIT")
    mix_mod = obj.modifiers.new(utils.unique_name(mat_name + "_WeightMix"), "VERTEX_WEIGHT_MIX")
    # Use the texture as the modifiers vertex weight source
    edit_mod.mask_texture = tex
    # Setup the modifier to generate the inverse of the weight map in the vertex group
    edit_mod.use_add = False
    edit_mod.use_remove = False
    edit_mod.add_threshold = 0.01
    edit_mod.remove_threshold = 0.01
    edit_mod.vertex_group = material_group
    edit_mod.default_weight = 1
    edit_mod.falloff_type = 'LINEAR'
    edit_mod.invert_falloff = True
    edit_mod.mask_constant = 1
    edit_mod.mask_tex_mapping = 'UV'
    edit_mod.mask_tex_use_channel = 'INT'
    try:
        if normalize:
            edit_mod.normalize = True
    except:
        pass
    # The Vertex Weight Mix modifier takes the material weight map group and mixes it into the pin weight group:
    # (this allows multiple weight maps from different materials and UV layouts to combine in the same mesh)
    mix_mod.vertex_group_a = mix_group
    mix_mod.vertex_group_b = material_group
    mix_mod.invert_mask_vertex_group = True
    mix_mod.default_weight_a = 1
    mix_mod.default_weight_b = 1
    mix_mod.mix_set = 'B' #'ALL'
    mix_mod.mix_mode = 'SET'
    mix_mod.invert_mask_vertex_group = False
    utils.log_info("Weight map: " + weight_map.name + " applied to: " + obj.name + "/" + mat.name)

    return edit_mod, mix_mod
