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

import math
import os
import mathutils

import bpy

from . import geom, bones, imageutils, meshutils, materials, modifiers, utils, jsonutils, vars

COLLISION_THICKESS = 0.001
HAIR_THICKNESS = 0.001
CLOTH_THICKNESS = 0.004


def apply_cloth_settings(obj, cloth_type, self_collision = False):
    props = vars.props()
    prefs = vars.prefs()

    mod = modifiers.get_cloth_physics_mod(obj)
    if mod is None:
        return
    obj_cache = props.get_object_cache(obj)
    obj_cache.cloth_settings = cloth_type

    utils.log_info("Setting " + obj.name + " cloth settings to: " + cloth_type)
    mod.settings.vertex_group_mass = prefs.physics_group + "_Pin"
    mod.settings.time_scale = 1
    mod.collision_settings.use_self_collision = self_collision

    cloth_area = geom.get_area(obj)
    air_dampening_mod = cloth_area / 2.0
    utils.log_info(f"Using cloth area: {cloth_area} sqm, air dampening mod: {air_dampening_mod}")
    BASE_GSM = 1.0 / 2666

    if cloth_type == "HAIR":
        mod.settings.quality = 6
        mod.settings.pin_stiffness = 0.025
        # physical properties
        mod.settings.mass = 0.05
        mod.settings.air_damping = 1.0
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 5.0
        mod.settings.compression_stiffness = 5.0
        mod.settings.shear_stiffness = 5.0
        mod.settings.bending_stiffness = 5.0
        # dampening
        mod.settings.tension_damping = 0.0
        mod.settings.compression_damping = 0.0
        mod.settings.shear_damping = 0.0
        mod.settings.bending_damping = 0.0
        # collision
        mod.collision_settings.distance_min = HAIR_THICKNESS
        mod.collision_settings.collision_quality = 4
        mod.collision_settings.self_distance_min = 0.0005 # 0.5mm
        mod.collision_settings.self_friction = 1.0

    elif cloth_type == "DENIM":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 0.5
        # physical properties
        mod.settings.mass = 400 * BASE_GSM
        mod.settings.air_damping = 1.0 + 0.35 * air_dampening_mod
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 40.0
        mod.settings.compression_stiffness = 40.0
        mod.settings.shear_stiffness = 40.0
        mod.settings.bending_stiffness = 60.0
        # dampening
        mod.settings.tension_damping = 25.0
        mod.settings.compression_damping = 25.0
        mod.settings.shear_damping = 25.0
        mod.settings.bending_damping = 10.0
        # collision
        mod.collision_settings.distance_min = CLOTH_THICKNESS
        mod.collision_settings.collision_quality = 4
        mod.collision_settings.self_distance_min = 0.005 # 5mm
        mod.collision_settings.self_friction = 10.0

    elif cloth_type == "LEATHER":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 0.5
        # physical properties
        mod.settings.mass = 800 * BASE_GSM
        mod.settings.air_damping = 1.0 + 0.25 * air_dampening_mod
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 80.0
        mod.settings.compression_stiffness = 80.0
        mod.settings.shear_stiffness = 80.0
        mod.settings.bending_stiffness = 80.0
        # dampening
        mod.settings.tension_damping = 25.0
        mod.settings.compression_damping = 25.0
        mod.settings.shear_damping = 25.0
        mod.settings.bending_damping = 10.0
        # collision
        mod.collision_settings.distance_min = CLOTH_THICKNESS
        mod.collision_settings.collision_quality = 4
        mod.collision_settings.self_distance_min = 0.0025 # 5mm
        mod.collision_settings.self_friction = 15.0

    elif cloth_type == "RUBBER":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 0.25
        # physical properties
        mod.settings.mass = 650 * BASE_GSM
        mod.settings.air_damping = 1.0 + 0.25 * air_dampening_mod
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 15.0
        mod.settings.compression_stiffness = 15.0
        mod.settings.shear_stiffness = 15.0
        mod.settings.bending_stiffness = 40.0
        # dampening
        mod.settings.tension_damping = 25.0
        mod.settings.compression_damping = 25.0
        mod.settings.shear_damping = 25.0
        mod.settings.bending_damping = 0.0
        # collision
        mod.collision_settings.distance_min = CLOTH_THICKNESS
        mod.collision_settings.collision_quality = 4
        mod.collision_settings.self_distance_min = 0.0025 # 2.5mm
        mod.collision_settings.self_friction = 20.0

    elif cloth_type == "LINEN":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 0.1
        # physical properties
        mod.settings.mass = 160 * BASE_GSM
        mod.settings.air_damping = 1.0 + 0.5 * air_dampening_mod
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 5.0
        mod.settings.compression_stiffness = 5.0
        mod.settings.shear_stiffness = 5.0
        mod.settings.bending_stiffness = 20.0
        # dampening
        mod.settings.tension_damping = 5.0
        mod.settings.compression_damping = 5.0
        mod.settings.shear_damping = 5.0
        mod.settings.bending_damping = 0.0
        # collision
        mod.collision_settings.distance_min = CLOTH_THICKNESS
        mod.collision_settings.collision_quality = 4
        mod.collision_settings.self_distance_min = 0.0025 # 2.5mm
        mod.collision_settings.self_friction = 5.0

    elif cloth_type == "COTTON":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 0.075
        # physical properties
        mod.settings.mass = 140 * BASE_GSM
        mod.settings.air_damping = 1.0 + 0.75 * air_dampening_mod
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 2.0
        mod.settings.compression_stiffness = 2.0
        mod.settings.shear_stiffness = 2.0
        mod.settings.bending_stiffness = 10.0
        # dampening
        mod.settings.tension_damping = 2.0
        mod.settings.compression_damping = 2.0
        mod.settings.shear_damping = 2.0
        mod.settings.bending_damping = 0.0
        # collision
        mod.collision_settings.distance_min = CLOTH_THICKNESS
        mod.collision_settings.collision_quality = 4
        mod.collision_settings.self_distance_min = 0.0025 # 2.5mm
        mod.collision_settings.self_friction = 5.0

    elif cloth_type == "SILK":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 0.05
        # physical properties
        mod.settings.mass = 120 * BASE_GSM
        mod.settings.air_damping = 1.0 + 1.0 * air_dampening_mod
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 0.5
        mod.settings.compression_stiffness = 0.5
        mod.settings.shear_stiffness = 0.5
        mod.settings.bending_stiffness = 1.0
        # dampening
        mod.settings.tension_damping = 0.0
        mod.settings.compression_damping = 0.0
        mod.settings.shear_damping = 0.0
        mod.settings.bending_damping = 0.0
        # collision
        mod.collision_settings.distance_min = CLOTH_THICKNESS
        mod.collision_settings.collision_quality = 4
        mod.collision_settings.self_distance_min = 0.0025 # 2.5mm
        mod.collision_settings.self_friction = 1.0


def uses_collision_physics(chr_cache, obj):
    obj_cache = chr_cache.get_object_cache(obj)
    collision_setting = "OFF"
    if obj == obj_cache.get_object():
        collision_setting = obj_cache.collision_physics
    if "rl_collision_physics" in obj:
        collision_setting = obj["rl_collision_physics"]
    if collision_setting == "ON" or collision_setting == "PROXY":
        return True
    # Body objects should use collision physics by default
    if collision_setting == "DEFAULT" and \
        (obj_cache.object_type == "BODY" or obj_cache.object_type == "OCCLUSION"):
        return True
    return False


def apply_collision_physics(chr_cache, obj, obj_cache):
    """Adds a Collision modifier to the object, depending on the object cache settings.
       Does not overwrite or re-create any existing Collision modifier.
    """

    if not (chr_cache and obj and obj_cache):
        return

    # physics seem to apply better if done in rest pose
    arm = chr_cache.get_armature()
    if arm:
        pose_position = arm.data.pose_position
        arm.data.pose_position = "REST"

    has_cloth = modifiers.get_cloth_physics_mod(obj) is not None

    if uses_collision_physics(chr_cache, obj):
        if obj_cache.use_collision_proxy and not has_cloth:
            proxy = chr_cache.get_collision_proxy(obj)
            if not proxy:
                proxy = create_collision_proxy(chr_cache, obj_cache, obj)
            if proxy:
                obj = proxy
        else:
            remove_collision_proxy(chr_cache, obj)
        collision_mod = modifiers.get_collision_physics_mod(obj)
        if not collision_mod:
            collision_mod = obj.modifiers.new(utils.unique_name("Collision"), type="COLLISION")
        collision_mod.settings.thickness_outer = COLLISION_THICKESS
        utils.log_info("Collision Modifier: " + collision_mod.name + " applied to " + obj.name)

    elif obj_cache.collision_physics == "OFF":
        remove_collision_physics(chr_cache, obj)
        utils.log_info("Collision Physics disabled for: " + obj.name)

    if arm:
        arm.data.pose_position = pose_position


def remove_collision_physics(chr_cache, obj):
    """Removes the Collision modifier from the object.
    """

    if chr_cache and obj:

        proxy = chr_cache.get_collision_proxy(obj)
        if proxy:
            utils.delete_mesh_object(proxy)

        for mod in obj.modifiers:
            if mod.type == "COLLISION":
                utils.log_info("Removing Collision modifer: " + mod.name + " from: " + obj.name)
                obj.modifiers.remove(mod)


def add_cloth_physics(chr_cache, obj, add_weight_maps = False):
    """Adds a Cloth modifier to the object depending on the object cache settings.

    Does not overwrite or re-create any existing Cloth modifier.
    Sets the cache bake range to the same as any action on the character's armature.
    Applies cloth settings based on the object cache settings.
    Repopulates the existing weight maps, depending on their cache settings.
    """

    prefs = vars.prefs()
    props = vars.props()

    if not (chr_cache and obj):
        return

    obj_cache = chr_cache.get_object_cache(obj)

    if (obj_cache and
        obj_cache.cloth_physics == "ON"):

        utils.object_mode_to(obj)

        # Add weight maps
        if add_weight_maps:
            for mat in obj.data.materials:
                if mat:
                    add_material_weight_map(chr_cache, obj, mat, create = False)
            if modifiers.has_cloth_weight_map_mods(obj):
                attach_cloth_weight_map_remap(obj, prefs.physics_weightmap_curve)

        cloth_mod = modifiers.get_cloth_physics_mod(obj)

        if not cloth_mod:
            # Create the Cloth modifier
            cloth_mod : bpy.types.ClothModifier
            cloth_mod_id = utils.unique_name("Cloth")
            cloth_mod = obj.modifiers.new(cloth_mod_id, type="CLOTH")
            utils.log_info("Cloth Modifier: " + cloth_mod.name + " applied to " + obj.name)

        # Set cache bake frame range
        frame_start, frame_end = utils.get_scene_frame_range()
        utils.log_info(f"Setting {obj.name} bake cache frame range to [{str(frame_start)} - {str(frame_end)}]")
        cloth_mod.point_cache.frame_start = frame_start
        cloth_mod.point_cache.frame_end = frame_end
        if not cloth_mod.point_cache.name:
            random_id = utils.generate_random_id(10)
            cache_id = f"{obj.name}_{random_id}"
            cloth_mod.point_cache.name = cache_id

        # Apply cloth settings
        if obj_cache.cloth_settings != "DEFAULT":
            apply_cloth_settings(obj,
                                 obj_cache.cloth_settings,
                                 self_collision = obj_cache.cloth_self_collision)
        elif obj_cache.object_type == "HAIR":
            apply_cloth_settings(obj, "HAIR")
        else:
            apply_cloth_settings(obj, "COTTON")

        # fix mod order
        arrange_physics_modifiers(obj)

    elif obj_cache.cloth_physics == "OFF":
        utils.log_info("Cloth Physics disabled for: " + obj.name)


def remove_cloth_physics(obj):
    """Removes the Cloth modifier from the object.

    Also removes any active weight maps and also removes the weight map vertex group.
    """

    if not obj:
        return

    prefs = vars.prefs()

    utils.object_mode_to(obj)

    # Remove the Cloth modifier
    for mod in obj.modifiers:
        if mod.type == "CLOTH":
            utils.log_info("Removing Cloth modifer: " + mod.name + " from: " + obj.name)
            obj.modifiers.remove(mod)

    # Remove any weight maps
    for mat in obj.data.materials:
        if mat:
            remove_material_weight_maps(obj, mat)
            weight_group = prefs.physics_group + "_" + utils.strip_name(mat.name)
            if weight_group in obj.vertex_groups:
                obj.vertex_groups.remove(obj.vertex_groups[weight_group])
        remove_cloth_weight_map_remap(obj)

    # If there are no weight maps left on the object, remove the vertex group
    mods = 0
    for mod in obj.modifiers:
        if mod.type == "VERTEX_WEIGHT_EDIT" and vars.NODE_PREFIX in mod.name:
            mods += 1

    pin_group = prefs.physics_group + "_Pin"
    if mods == 0 and pin_group in obj.vertex_groups:
        utils.log_info("Removing vertex group: " + pin_group + " from: " + obj.name)
        obj.vertex_groups.remove(obj.vertex_groups[pin_group])


def remove_all_physics_mods(obj):
    """Removes all physics modifiers from the object.

    Used when (re)building the character materials.
    """

    utils.log_info("Removing all related physics modifiers from: " + obj.name)
    for mod in obj.modifiers:
        if mod.type == "VERTEX_WEIGHT_EDIT" and vars.NODE_PREFIX in mod.name:
            obj.modifiers.remove(mod)
        elif mod.type == "VERTEX_WEIGHT_MIX" and vars.NODE_PREFIX in mod.name:
            obj.modifiers.remove(mod)
        elif mod.type == "CLOTH":
            obj.modifiers.remove(mod)
        elif mod.type == "COLLISION":
            obj.modifiers.remove(mod)


def enable_collision_physics(chr_cache, obj):
    props = vars.props()
    if chr_cache and utils.object_exists_is_mesh(obj):
        obj, proxy, is_proxy = chr_cache.get_related_physics_objects(obj)
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache:
            has_cloth = modifiers.get_cloth_physics_mod(obj) is not None
            collision_mode = "PROXY" if (obj_cache.use_collision_proxy and not has_cloth) else "ON"
            if obj == obj_cache.get_object():
                obj_cache.collision_physics = collision_mode
            obj["rl_collision_physics"] = collision_mode
            utils.log_info("Enabling Collision physics for: " + obj.name)
            apply_collision_physics(chr_cache, obj, obj_cache)


def disable_collision_physics(chr_cache, obj):
    if chr_cache and utils.object_exists_is_mesh(obj):
        obj, proxy, is_proxy = chr_cache.get_related_physics_objects(obj)
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache:
            if obj == obj_cache.get_object():
                obj_cache.collision_physics = "OFF"
            obj["rl_collision_physics"] = "OFF"
            utils.log_info("Disabling Collision physics for: " + obj.name)
            remove_collision_physics(chr_cache, obj)


def show_hide_collision_proxies(context, chr_cache, show, select=False, use_local=False):
    if chr_cache:
        objects = []
        proxies = []
        # get all character objects with proxies
        for obj in chr_cache.get_cache_objects():
            obj, proxy, is_proxy = chr_cache.get_related_physics_objects(obj)
            if obj and proxy:
                objects.append(obj)
                proxies.append(proxy)
        # show / hide all proxy objects
        if show:
            if proxies:
                for proxy in proxies:
                    utils.unhide(proxy)
                utils.object_mode()
                if select or use_local:
                    utils.try_select_objects(proxies, clear_selection=True)
                if use_local and not utils.is_local_view(context):
                    bpy.ops.view3d.localview()
            return True
        else:
            if proxies:
                for proxy in proxies:
                    utils.hide(proxy)
                utils.object_mode()
                if select:
                    utils.try_select_objects(objects, clear_selection=True)
                if use_local and utils.is_local_view(context):
                    bpy.ops.view3d.localview()
            return False


def enable_cloth_physics(chr_cache, obj, add_weight_maps = True):
    props = vars.props()
    if chr_cache and obj:
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache:
            obj_cache.cloth_physics = "ON"
            utils.log_info("Enabling Cloth physics for: " + obj.name)
            add_cloth_physics(chr_cache, obj, add_weight_maps)


def disable_cloth_physics(chr_cache, obj):
    props = vars.props()
    if chr_cache and obj:
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache:
            obj_cache.cloth_physics = "OFF"
            utils.log_info("Removing cloth physics for: " + obj.name)
            remove_cloth_physics(obj)


def remove_collision_proxy(chr_cache, obj):
    proxy = chr_cache.get_collision_proxy(obj)
    if proxy:
        utils.log_info(f"Removing collision proxy: {proxy.name}")
        utils.delete_mesh_object(proxy)


def create_collision_proxy(chr_cache, obj_cache, obj):
    utils.log_info(f"Creating collision proxy mesh from: {obj.name}")
    # remove old proxy
    remove_collision_proxy(chr_cache, obj)
    # clone obj to proxy
    collision_proxy = utils.duplicate_object(obj)
    collision_proxy.name = obj.name + ".Collision_Proxy"
    collision_proxy["rl_collision_proxy"] = obj.name
    if utils.object_mode_to(collision_proxy) and utils.set_only_active_object(collision_proxy):
        # remove shape keys
        collision_proxy.shape_key_clear()
        # remove eye-lashes
        eye_lash_mat = materials.get_material_by_type(chr_cache, collision_proxy, "EYELASH")
        if eye_lash_mat:
            meshutils.remove_material_verts(collision_proxy, eye_lash_mat)
        # remove materials
        collision_proxy.data.materials.clear()
        # delete loose
        utils.edit_mode_to(collision_proxy)
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=True)
        utils.object_mode_to(collision_proxy)
        if obj_cache.collision_proxy_decimate < 1.0:
            # add decimate modifier
            mod = modifiers.add_decimate_modifier(collision_proxy,
                                                  obj_cache.collision_proxy_decimate,
                                                  "Decimate_Collision_Body")
            modifiers.move_mod_first(collision_proxy, mod)
            # apply decimate modifier
            bpy.ops.object.modifier_apply(modifier=mod.name)

    utils.log_info(f"Storing collision mesh: {collision_proxy.name}")
    obj_cache.use_collision_proxy = True
    obj_cache.collision_physics = "PROXY"
    utils.hide(collision_proxy)
    collision_proxy.hide_render = True
    utils.set_only_active_object(obj)
    return collision_proxy


def get_weight_map_from_modifiers(obj, mat):
    mat_name = "_" + utils.strip_name(mat.name) + "_"
    if obj.type == "MESH":
        for mod in obj.modifiers:
            if mod.type == "VERTEX_WEIGHT_EDIT" and vars.NODE_PREFIX in mod.name and mat_name in mod.name:
                if mod.mask_texture is not None and mod.mask_texture.image is not None:
                    image = mod.mask_texture.image
                    return image
    return None


def get_weight_map_image(chr_cache, obj, mat, create = False):
    """Returns the weight map image for the material.

    Fetches the Image for the given materials weight map, if it exists.
    If not, the image can be created and packed into the blend file and stored
    in the material cache as a temporary weight map image.
    """

    props = vars.props()
    mat_cache = props.get_material_cache(mat)
    weight_map = imageutils.find_material_image(mat, "WEIGHTMAP")

    if mat_cache:

        if weight_map:
            if weight_map.size[0] == 0 or weight_map.size[1] == 0:
                weight_map = None
            else:
                mat_cache.temp_weight_map = weight_map

        if weight_map is None and create:
            name = utils.strip_name(mat.name) + "_WeightMap"
            tex_size = int(props.physics_tex_size)
            weight_map = bpy.data.images.new(name, tex_size, tex_size, is_data=False)
            # make the image 'dirty' so it converts to a file based image which can be saved:
            weight_map.pixels[0] = 0.0
            weight_map.file_format = "PNG"
            weight_map.filepath_raw = os.path.join(mat_cache.get_tex_dir(chr_cache), name + ".png")
            weight_map.save()
            # keep track of which weight maps we created:
            mat_cache.temp_weight_map = weight_map
            utils.log_info("Weight-map image: " + weight_map.name + " created and saved.")

    return weight_map


def add_material_weight_map(chr_cache, obj, mat, create = False):
    """Adds a weight map 'Vertex Weight Edit' modifier for the object's material.

    Gets or creates (if instructed) the material's weight map then creates
    or re-creates the modifier to generate the physics 'Pin' vertex group.
    """

    if chr_cache and obj and mat:

        if cloth_physics_available(chr_cache, obj, mat):
            if create:
                weight_map = get_weight_map_image(chr_cache, obj, mat, create)
            else:
                weight_map = imageutils.find_material_image(mat, "WEIGHTMAP")

            remove_material_weight_maps(obj, mat)
            if weight_map is not None:
                attach_material_weight_map(obj, mat, weight_map)
        else:
            utils.log_info("Cloth Physics has been disabled for: " + obj.name)


def remove_material_weight_maps(obj, mat):
    """Removes the weight map 'Vertex Weight Edit' modifier for the object's material.

    This does not remove or delete the weight map image or temporary packed image,
    or the texture based on the weight map image, just the modifier.
    """

    if obj and mat:

        edit_mod, mix_mod = modifiers.get_material_weight_map_mods(obj, mat)
        if edit_mod is not None:
            utils.log_info("Removing weight map vertex edit modifer: " + edit_mod.name)
            obj.modifiers.remove(edit_mod)
        if mix_mod is not None:
            utils.log_info("Removing weight map vertex mix modifer: " + mix_mod.name)
            obj.modifiers.remove(mix_mod)


def enable_material_weight_map(chr_cache, obj, mat):
    """Enables the weight map for the object's material and (re)creates the Vertex Weight Edit modifier.
    """

    prefs = vars.prefs()
    props = vars.props()

    if chr_cache and obj and mat:

        mat_cache = chr_cache.get_material_cache(mat)
        if mat_cache:
            if mat_cache.cloth_physics == "OFF":
                mat_cache.cloth_physics = "ON"
            add_material_weight_map(chr_cache, obj, mat, True)
            if modifiers.has_cloth_weight_map_mods(obj):
                attach_cloth_weight_map_remap(obj, prefs.physics_weightmap_curve)
            # fix mod order
            arrange_physics_modifiers(obj)


def disable_material_weight_map(chr_cache, obj, mat):
    """Disables the weight map for the object's material and removes the Vertex Weight Edit modifier.
    """

    if chr_cache and obj and mat:

        mat_cache = chr_cache.get_material_cache(mat)
        mat_cache.cloth_physics = "OFF"
        remove_material_weight_maps(obj, mat)


def collision_physics_available(chr_cache, obj):
    """Is cloth collisions physics allowed on the character object?"""

    if chr_cache and obj:

        obj_cache = chr_cache.get_object_cache(obj)
        collision_mod = modifiers.get_collision_physics_mod(obj)
        if collision_mod is None:
            if obj_cache.collision_physics == "OFF":
                return False
        return True

    return False


def cloth_physics_available(chr_cache, obj, mat):
    """Is cloth physics allowed on this character object and material?"""

    if chr_cache and obj and mat:

        obj_cache = chr_cache.get_object_cache(obj)
        mat_cache = chr_cache.get_material_cache(mat)
        cloth_mod = modifiers.get_cloth_physics_mod(obj)
        if cloth_mod is None:
            if obj_cache.cloth_physics == "OFF":
                return False
            if mat_cache is not None and mat_cache.cloth_physics == "OFF":
                return False
        else:
            # if cloth physics was disabled by the add-on,
            # but re-enabled in the physics panel,
            # correct the object cache setting:
            if obj_cache.cloth_physics == "OFF":
                obj_cache.cloth_physics == "ON"
        return True

    return False


def is_cloth_physics_enabled(mat_cache, mat, obj):
    """Is cloth physics enabled on this character object and material?"""

    if mat_cache and obj and mat:

        cloth_mod = modifiers.get_cloth_physics_mod(obj)
        edit_mods, mix_mods = modifiers.get_material_weight_map_mods(obj, mat)
        if cloth_mod and edit_mods and mix_mods:
            if mat_cache and mat_cache.cloth_physics != "OFF":
                return True
        return False

    return False


def attach_cloth_weight_map_remap(obj, replace = True, curve_power = 5.0):
    """Attach the final remap vertex weight edit to convert the physx weight
       map values to something more blender physics friendly."""

    prefs = vars.prefs()
    remap_mod : bpy.types.VertexWeightEditModifier

    if replace:
        modifiers.remove_object_modifiers(obj, "VERTEX_WEIGHT_EDIT", "_WeightEditRemap")
    else:
        remap_mod = modifiers.get_object_modifier(obj, "VERTEX_WEIGHT_EDIT", "_WeightEditRemap")
        if remap_mod:
            return

    pin_group = prefs.physics_group + "_Pin"
    obj_name = utils.safe_export_name(obj.name)

    remap_mod = obj.modifiers.new(utils.unique_name(obj_name + "_WeightEditRemap"), "VERTEX_WEIGHT_EDIT")
    remap_mod.use_add = False
    remap_mod.use_remove = False
    remap_mod.vertex_group = pin_group
    remap_mod.default_weight = 0.0
    remap_mod.falloff_type = 'CURVE'
    remap_mod.invert_falloff = False
    #remap_mod.map_curve.curves[0].points.new(0.25, pow(0.25, curve_power))
    #remap_mod.map_curve.curves[0].points.new(0.5, pow(0.5, curve_power))
    remap_mod.map_curve.curves[0].points.new(0.75, pow(0.75, curve_power))
    remap_mod.map_curve.update()


def remove_cloth_weight_map_remap(obj):
    modifiers.remove_object_modifiers(obj, "VERTEX_WEIGHT_EDIT", "_WeightEditRemap")


def attach_material_weight_map(obj, mat, weight_map):
    """Attaches a weight map to the object's material via a 'Vertex Weight Edit' modifier.

    This will attach the supplied weight map or will try to find an existing weight map,
    but will not create a new weight map if it doesn't already exist.
    """

    prefs = vars.prefs()

    if obj and mat and weight_map:

        # Make a texture based on the weight map image
        # As we are matching names to find existing textures,
        # get a name that keeps the duplication suffix
        mat_name = utils.safe_export_name(mat.name)
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
        pin_group = prefs.physics_group + "_Pin"
        material_group = prefs.physics_group + "_" + mat_name
        if pin_group not in obj.vertex_groups:
            pin_vertex_group = obj.vertex_groups.new(name = pin_group)
        else:
            pin_vertex_group = obj.vertex_groups[pin_group]
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
        mod_cloth = modifiers.get_cloth_physics_mod(obj)
        if mod_cloth is not None:
            mod_cloth.settings.vertex_group_mass = pin_group

        # re-create create the Vertex Weight Edit modifier and the Vertex Weight Mix modifer
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
            edit_mod.normalize = False
        except:
            pass
        # The Vertex Weight Mix modifier takes the material weight map group and mixes it into the pin weight group:
        # (this allows multiple weight maps from different materials and UV layouts to combine in the same mesh)
        mix_mod.vertex_group_a = pin_group
        mix_mod.vertex_group_b = material_group
        mix_mod.invert_mask_vertex_group = True
        mix_mod.default_weight_a = 1
        mix_mod.default_weight_b = 1
        mix_mod.mix_set = 'B' #'ALL'
        mix_mod.mix_mode = 'SET'
        mix_mod.invert_mask_vertex_group = False
        utils.log_info("Weight map: " + weight_map.name + " applied to: " + obj.name + "/" + mat.name)


def get_physx_weight_range(obj):
    """Get the range (min, max) of weights for physics pin group"""

    props = vars.props()
    prefs = vars.prefs()

    weight_min = 1.0
    weight_max = 0.0

    if obj:

        vertex_group_name = prefs.physics_group + "_Pin"

        if obj.type == "MESH" and vertex_group_name in obj.vertex_groups:

            if utils.set_active_object(obj):

                # normalize pin vertex group range
                pin_vg = obj.vertex_groups[vertex_group_name]
                pin_vg_index = pin_vg.index

                # determine range
                for vertex in obj.data.vertices:
                    for vg in vertex.groups:
                        if vg.group == pin_vg_index:
                            w = vg.weight
                            weight_min = min(w, weight_min)
                            weight_max = max(w, weight_max)

    return weight_min, weight_max


def count_weightmaps(objects):
    num_maps = 0
    num_dirty = 0
    for obj in objects:
        if obj.type == "MESH":
            for mod in obj.modifiers:
                if mod.type == "VERTEX_WEIGHT_EDIT" and vars.NODE_PREFIX in mod.name:
                    if mod.mask_texture is not None and mod.mask_texture.image is not None:
                        num_maps += 1
                        image = mod.mask_texture.image
                        if image.is_dirty:
                            num_dirty += 1
    return num_maps, num_dirty


def get_dirty_weightmaps(objects):
    maps = []
    for obj in objects:
        if obj.type == "MESH":
            for mod in obj.modifiers:
                if mod.type == "VERTEX_WEIGHT_EDIT" and vars.NODE_PREFIX in mod.name:
                    if mod.mask_texture is not None and mod.mask_texture.image is not None:
                        image = mod.mask_texture.image
                        abs_image_path = bpy.path.abspath(image.filepath)
                        if image.filepath != "" and (image.is_dirty or not os.path.exists(abs_image_path)):
                            maps.append(image)
    return maps


def physics_paint_strength_update(self, context):
    props = vars.props()

    if context.mode == "PAINT_TEXTURE":
        ups = context.tool_settings.unified_paint_settings
        prop_owner = ups if ups.use_unified_color else context.tool_settings.image_paint.brush
        s = props.physics_paint_strength
        prop_owner.color = (s, s, s)


def weight_strength_update(self, context):
    props = vars.props()

    strength = props.weight_map_strength
    influence = 1 - math.pow(1 - strength, 3)
    edit_mod, mix_mod = modifiers.get_material_weight_map_mods(context.object, utils.get_context_material(context))
    mix_mod.mask_constant = influence


def browse_weight_map(chr_cache, context):
    obj = context.object
    mat = utils.get_context_material(context)
    if obj and mat:
        weight_map = get_weight_map_image(chr_cache, obj, mat)
        if weight_map:
            path = bpy.path.abspath(weight_map.filepath)
            utils.show_system_file_browser(path)


def begin_paint_weight_map(context, chr_cache):
    obj = context.object
    mat = utils.get_context_material(context)
    props = vars.props()
    shading = utils.get_view_3d_shading(context)
    if obj is not None and mat is not None:
        if shading:
            props.paint_store_render = shading.type
        else:
            props.paint_store_render = "MATERIAL"

        if context.mode != "PAINT_TEXTURE":
            bpy.ops.object.mode_set(mode="TEXTURE_PAINT")

        if context.mode == "PAINT_TEXTURE":
            physics_paint_strength_update(None, context)
            weight_map = get_weight_map_image(chr_cache, obj, mat)
            weight_map.update()
            props.paint_object = obj
            props.paint_material = mat
            props.paint_image = weight_map
            shading = utils.get_view_3d_shading(context)
            if weight_map is not None:
                bpy.context.scene.tool_settings.image_paint.mode = 'IMAGE'
                bpy.context.scene.tool_settings.image_paint.canvas = weight_map
                if shading:
                    shading.type = 'SOLID'


def resize_weight_map(chr_cache, context, op):
    props = vars.props()

    if context.mode == "PAINT_TEXTURE":
        return

    obj = context.object
    mat = utils.get_context_material(context)
    props = vars.props()
    if obj is not None and mat is not None:
        weight_map : bpy.types.Image = get_weight_map_image(chr_cache, obj, mat)
        size = int(props.physics_tex_size)
        if weight_map and (weight_map.size[0] != size or weight_map.size[1] != size):
            weight_map.scale(size, size)
            # force Blender to update the image by changing a pixel value
            # otherwise it doesn't recognise the size change.
            value = weight_map.pixels[0]
            weight_map.pixels[0] = 0.0
            weight_map.pixels[0] = value
            weight_map.update()
            op.report({'INFO'}, f"Weightmap Resized to: {size} x {size}")



def end_paint_weight_map(op, context, chr_cache):
    try:
        props = vars.props()
        shading = utils.get_view_3d_shading(context)
        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        if shading:
            shading.type = props.paint_store_render
        #props.paint_image.save()
        op.report({'INFO'}, f"Weightmap painting done, Save the weightmap to preserve changes.")
    except Exception as e:
        utils.log_error("Something went wrong restoring object mode from paint mode!", e)


def save_dirty_weight_maps(chr_cache, objects):
    """Saves all altered active weight map images to their respective material folders.

    Also saves any missing weight maps.
    """

    maps = get_dirty_weightmaps(objects)

    for weight_map in maps:
        if weight_map.is_dirty:
            utils.log_info("Dirty weight map: " + weight_map.name + " : " + weight_map.filepath)
            weight_map.save()
            utils.log_info("Weight Map: " + weight_map.name + " saved to: " + weight_map.filepath)
        if not os.path.exists(weight_map.filepath):
            utils.log_info("Missing weight map: " + weight_map.name + " : " + weight_map.filepath)
            weight_map.save()
            utils.log_info("Weight Map: " + weight_map.name + " saved to: " + weight_map.filepath)


def delete_selected_weight_map(chr_cache, obj, mat):
    if obj is not None and obj.type == "MESH" and mat is not None:
        edit_mod, mix_mod = modifiers.get_material_weight_map_mods(obj, mat)
        if edit_mod is not None and edit_mod.mask_texture is not None and edit_mod.mask_texture.image is not None:
            image = edit_mod.mask_texture.image
            abs_image_path = bpy.path.abspath(image.filepath)
            try:
                if image.filepath != "" and os.path.exists(abs_image_path):
                    utils.log_info("Removing weight map file: " + abs_image_path)
                    os.remove(abs_image_path)
            except Exception as e:
                utils.log_error("Removing weight map file: " + abs_image_path, e)
        if edit_mod is not None:
            utils.log_info("Removing 'Vertex Weight Edit' modifer")
            obj.modifiers.remove(edit_mod)
        if mix_mod is not None:
            utils.log_info("Removing 'Vertex Weight Mix' modifer")
            obj.modifiers.remove(mix_mod)


def cloth_physics_point_cache_override(mod):
    override = bpy.context.copy()
    override["point_cache"] = mod.point_cache
    return override


def get_context_physics_objects(context, from_selected=False):
    props = vars.props()
    chr_cache = props.get_context_character_cache(context)
    physics_objects = []
    if chr_cache:
        if from_selected:
            objects = context.selected_objects.copy()
        else:
            objects = chr_cache.get_all_objects(include_armature=False,
                                                include_children=True,
                                                of_type="MESH")
        for obj in objects:
            cloth_mod = modifiers.get_cloth_physics_mod(obj)
            coll_mod = modifiers.get_collision_physics_mod(obj)
            if cloth_mod or coll_mod:
                physics_objects.append(obj)

    return physics_objects


def get_scene_physics_state():
    has_cloth = False
    has_collision = False
    has_rigidbody = False
    all_baked = True
    all_baking = True
    any_baked = False
    any_baking = False

    for scene in bpy.data.scenes:
        for object in scene.objects:
            for modifier in object.modifiers:
                if modifier.type == 'CLOTH':
                    has_cloth = True
                    if modifier.point_cache.is_baked:
                        any_baked = True
                    else:
                        all_baked = False
                    if modifier.point_cache.is_baking:
                        any_baking = True
                    else:
                        all_baking = False
                elif modifier.type == 'COLLISION':
                    has_collision = True

    all_baked = has_cloth and all_baked
    all_baking = has_cloth and all_baking

    if bpy.context.scene.rigidbody_world:
        rbw = bpy.context.scene.rigidbody_world
        has_rigidbody = True
        if rbw.point_cache.is_baked:
            any_baked = True
        else:
            all_baked = False
        if rbw.point_cache.is_baking:
            any_baking = True
        else:
            all_baking = False

    return has_cloth, has_collision, has_rigidbody, all_baked, any_baked, all_baking, any_baking


def reset_physics_cache(obj, start, end):
    cloth_mod : bpy.types.ClothModifier
    cloth_mod = modifiers.get_cloth_physics_mod(obj)
    if cloth_mod is not None:
        # free the baked cache
        if cloth_mod.point_cache.is_baked:
            free_cache(obj)
        # invalidate the cache
        utils.log_info("Invalidating point cache...")
        qs = cloth_mod.settings.quality
        cloth_mod.point_cache.frame_start = 1
        cloth_mod.point_cache.frame_end = 1
        cloth_mod.settings.quality = 1
        # reset the cache
        utils.log_info("Setting " + obj.name + " bake cache frame range to [" + str(start) + " - " + str(end) + "]")
        cloth_mod.point_cache.frame_start = start
        cloth_mod.point_cache.frame_end = end
        cloth_mod.settings.quality = qs
        # use disk cache if the blend file is saved
        if bpy.data.filepath:
            cloth_mod.point_cache.use_disk_cache = True
        return True
    return False


def reset_cache(context, all_objects = False):
    if bpy.context.scene.use_preview_range:
        start = bpy.context.scene.frame_preview_start
        end = bpy.context.scene.frame_preview_end
    else:
        start = bpy.context.scene.frame_start
        end = bpy.context.scene.frame_end

    if all_objects:
        objects = get_context_physics_objects(context)
    else:
        objects = [ context.object ]

    for obj in objects:
        if utils.object_exists_is_mesh(obj):
            reset_physics_cache(obj, start, end)


def free_cache(obj):
    cloth_mod = modifiers.get_cloth_physics_mod(obj)
    if cloth_mod is not None:
        # free the baked cache
        if cloth_mod.point_cache.is_baked:
            utils.log_info("Freeing point cache...")
            if utils.B320():
                with bpy.context.temp_override(point_cache=cloth_mod.point_cache):
                    bpy.ops.ptcache.free_bake()
            else:
                context_override = cloth_physics_point_cache_override(cloth_mod)
                bpy.ops.ptcache.free_bake(context_override)


def separate_physics_materials(chr_cache, obj):

    if utils.object_exists_is_mesh(obj):

        utils.object_mode_to(obj)

        # remember which materials have active weight maps
        temp = []
        for mat in obj.data.materials:
            if mat:
                edit_mod, mix_mod = modifiers.get_material_weight_map_mods(obj, mat)
                if edit_mod is not None:
                    temp.append(mat)

        # remove cloth physics from the object
        disable_cloth_physics(chr_cache, obj)

        # split the mesh by materials
        bpy.ops.mesh.separate(type='MATERIAL')
        split_objects = [ o for o in bpy.context.selected_objects if o != obj ]

        # re-apply cloth physics to the materials which had weight maps
        for split in split_objects:
            for mat in split.data.materials:
                if mat in temp:
                    enable_cloth_physics(chr_cache, split, True)
                    break
        temp = None


def disable_physics(chr_cache, physics_objects = None):
    changed_objects = []
    if not physics_objects:
        physics_objects = chr_cache.get_all_objects(include_armature=False,
                                                    include_children=True,
                                                    of_type="MESH")
    for obj in physics_objects:
        for mod in obj.modifiers:
            if mod.type == "CLOTH":
                if mod.show_render or mod.show_viewport:
                    mod.show_viewport = False
                    mod.show_render = False
                    changed_objects.append(obj)
            elif mod.type == "COLLISION":
                if obj.collision and obj.collision.use:
                    obj.collision.use = False
                    changed_objects.append(obj)
    chr_cache.physics_disabled = True
    return changed_objects


def enable_physics(chr_cache, physics_objects = None):
    prefs = vars.prefs()

    if not physics_objects:
        physics_objects = chr_cache.get_all_objects(include_armature=False,
                                                    include_children=True,
                                                    of_type="MESH")
    for obj in physics_objects:
        obj_cache = chr_cache.get_object_cache(obj)
        cloth_allowed = True
        if obj_cache:
            if ((obj_cache.is_hair() and not prefs.physics_cloth_hair) or
                (not obj_cache.is_hair() and not prefs.physics_cloth_clothing)):
                cloth_allowed = False
        for mod in obj.modifiers:
            if mod.type == "CLOTH" and cloth_allowed:
                mod.show_viewport = True
                mod.show_render = True
            elif mod.type == "COLLISION":
                if obj.collision:
                    obj.collision.use = True
    chr_cache.physics_disabled = False


def cloth_physics_state(obj):
    has_cloth = False
    is_baked = False
    is_baking = False
    point_cache = None
    mod : bpy.types.ClothModifier
    if obj:
        for mod in obj.modifiers:
            if mod.type == "CLOTH":
                point_cache = mod.point_cache
                has_cloth = True
                if point_cache.is_baked:
                    is_baked = True
                if point_cache.is_baking:
                    is_baking = True
    return has_cloth, is_baked, is_baking, point_cache


def detect_physics(chr_cache, obj, obj_cache, mat, mat_cache, chr_json):
    """Detect the physics material presets."""

    if not (obj and mat and obj_cache and mat_cache and chr_json):
        return

    physics_json = jsonutils.get_physics_json(chr_json)
    soft_physics_json = jsonutils.get_soft_physics_json(physics_json, obj, mat)
    if soft_physics_json:
        active = soft_physics_json["Activate Physics"]
        mass = soft_physics_json["Mass"]
        friction = soft_physics_json["Friction"]
        damping = soft_physics_json["Damping"]
        drag = soft_physics_json["Drag"]
        elasticity = soft_physics_json["Elasticity"]
        stretch = soft_physics_json["Stretch"]
        bending = soft_physics_json["Bending"]
        self_collision = soft_physics_json["Self Collision"]

        cmp = mathutils.Vector((elasticity, bending))
        presets = {
            "DEFAULT": mathutils.Vector((10, 30)),
            "SILK": mathutils.Vector((50, 80)),
            "COTTON": mathutils.Vector((30, 40)),
            "LINEN": mathutils.Vector((10, 0)),
            "DENIM": mathutils.Vector((1, 0)),
            "LEATHER": mathutils.Vector((10, 10)),
            "RUBBER": mathutils.Vector((20, 20)),
        }

        best_dif = 1000
        best_preset = "DEFAULT"
        for preset in presets:
            test = (cmp - presets[preset]).length
            if test < best_dif:
                best_preset = preset
                best_dif = test

        if obj_cache.object_type == "HAIR":
            best_preset = "HAIR"

        utils.log_info(f"Cloth Physics settings detected as: {best_preset}")
        obj_cache.cloth_settings = best_preset
        obj_cache.cloth_self_collision = self_collision

        if active:
            obj_cache.cloth_physics = "ON"
            mat_cache.cloth_physics = "ON"
            utils.log_info(f"Activating cloth physics on {obj.name} / {mat.name}")
        else:
            if obj_cache.cloth_physics == "DEFAULT":
                obj_cache.cloth_physics = "OFF"
                utils.log_info(f"Deactivating cloth physics on object {obj.name}")
            if mat_cache.cloth_physics == "DEFAULT":
                mat_cache.cloth_physics = "OFF"
                utils.log_info(f"Deactivating cloth physics on material {mat.name}")


def apply_all_physics(chr_cache):
    prefs = vars.prefs()
    props = vars.props()

    if chr_cache:
        utils.log_info(f"Adding all Physics modifiers to: {chr_cache.character_name}")
        utils.log_indent()
        arm = chr_cache.get_armature()
        objects = chr_cache.get_all_objects(include_armature=False,
                                            include_children=True,
                                            of_type="MESH")
        objects_processed = []
        accessory_colldiers = get_accessory_colliders(arm, objects, True)

        for obj in chr_cache.get_cache_objects():

            obj_cache = chr_cache.get_object_cache(obj)

            if obj_cache and obj_cache.is_mesh() and obj not in objects_processed and not obj_cache.disabled:

                cloth_allowed = True
                if ((obj_cache.is_hair() and not prefs.physics_cloth_hair) or
                    (not obj_cache.is_hair() and not prefs.physics_cloth_clothing)):
                    cloth_allowed = False

                utils.log_info(f"Object: {obj.name}:")
                utils.log_indent()

                remove_all_physics_mods(obj)

                if cloth_allowed:

                    for mat in obj.data.materials:
                        if mat and mat not in objects_processed:
                            add_material_weight_map(chr_cache, obj, mat, create = False)
                            objects_processed.append(mat)

                objects_processed.append(obj)

                apply_collision_physics(chr_cache, obj, obj_cache)
                if obj in accessory_colldiers:
                    apply_collision_physics(chr_cache, obj, obj_cache)

                if cloth_allowed:
                    if modifiers.has_cloth_weight_map_mods(obj):
                        attach_cloth_weight_map_remap(obj, prefs.physics_weightmap_curve)
                        enable_cloth_physics(chr_cache, obj, False)

                utils.log_recess()

        chr_cache.physics_applied = True
        utils.log_recess()


def arrange_physics_modifiers(obj):
    cloth_mod = None
    remap_mod = None
    subd_mods = []
    before_cloth = True
    for mod in obj.modifiers:
        if mod.type == "CLOTH":
            cloth_mod = mod
            before_cloth = False
        if mod.type == "SUBSURF":
            subd_mods.append([mod, before_cloth])
        if mod.type == "VERTEX_WEIGHT_EDIT" and "WeightEditRemap" in mod.name:
            remap_map = mod

    # order is:
    #       weight map edit/mix mods
    #       ...
    #       weight map edit remap mod
    #       subd mods before cloth)
    #       cloth mod
    #       subd mods after cloth

    if remap_mod:
        modifiers.move_mod_last(obj, remap_mod)
    for mod, before_cloth in subd_mods:
        if before_cloth:
            modifiers.move_mod_last(obj, mod)
    modifiers.move_mod_last(obj, cloth_mod)
    for mod, before_cloth in subd_mods:
        if not before_cloth:
            modifiers.move_mod_last(obj, mod)


def remove_all_physics(chr_cache):
    if chr_cache:
        utils.log_info(f"Removing all Physics modifiers from: {chr_cache.character_name}")
        utils.log_indent()
        objects_processed = []
        for obj in chr_cache.get_cache_objects():
            obj_cache = chr_cache.get_object_cache(obj)
            if obj_cache and obj_cache.is_mesh() and obj not in objects_processed and not obj_cache.disabled:
                remove_all_physics_mods(obj)
            remove_collision_proxy(chr_cache, obj)
        chr_cache.physics_applied = False
        utils.log_recess()


def get_accessory_colliders(arm, objects, hide = False):

    # find all collider bone names
    collider_bone_names = []
    bone : bpy.types.Bone
    pivot_bone : bpy.types.Bone
    for bone in arm.data.bones:
        if bone.name.startswith("CollisionShape"):
            for child_bone in bone.children:
                if child_bone.name.startswith(vars.ACCESORY_PIVOT_NAME):
                    pivot_bone = child_bone
                    for collider_bone in pivot_bone.children:
                        if collider_bone.name not in collider_bone_names:
                            collider_bone_names.append(collider_bone.name)
                else:
                    collider_bone = child_bone
                    if collider_bone.name not in collider_bone_names:
                        collider_bone_names.append(collider_bone.name)

    # use those names to find all the collider objects
    collider_objects = []
    for collider_bone_name in collider_bone_names:
        source_name = utils.strip_name(collider_bone_name)
        obj : bpy.types.Object
        for obj in objects:
            # this might be the right collider
            if obj.name.startswith(source_name):
                # check vertex group name to be sure
                if obj.vertex_groups and len(obj.vertex_groups) > 0:
                    for vg in obj.vertex_groups:
                        if vg.name == collider_bone_name:
                            if obj not in collider_objects:
                                collider_objects.append(obj)
                            if hide:
                                utils.hide(obj)
                            break

    return collider_objects


def delete_accessory_colliders(arm, objects):
    colliders = get_accessory_colliders(arm, objects)
    for collider in colliders:
        utils.delete_mesh_object(collider)
        objects.remove(collider)


def get_self_collision(chr_cache, obj):
    if chr_cache and obj:
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache:
            return obj_cache.cloth_self_collision
    return False


def restore_collision_proxy_view(context, chr_cache):
    """Return from local view. Hide the collision proxies.
       Any collisions proxies selected or active, select their source mesh objects instead."""
    active = utils.get_active_object()
    selection = context.selected_objects.copy()
    new_selection = []
    if active:
        active = chr_cache.get_related_physics_objects(active)[0]
    if selection:
        for obj in selection:
            obj = chr_cache.get_related_physics_objects(obj)[0]
            new_selection.append(obj)

    utils.fix_local_view(context)
    show_hide_collision_proxies(context, chr_cache, False)

    if new_selection:
        utils.try_select_objects(new_selection)
        if active:
            utils.set_active_object(active)


def set_physics_settings(op, context, param):
    props = vars.props()
    chr_cache = props.get_context_character_cache(context)
    obj = None
    if context.object and context.object.type == "MESH":
        obj = context.object

    if param == "PHYSICS_ADD_CLOTH":
        restore_collision_proxy_view(context, chr_cache)
        for obj in context.selected_objects:
            enable_cloth_physics(chr_cache, obj, True)

    elif param == "PHYSICS_REMOVE_CLOTH":
        restore_collision_proxy_view(context, chr_cache)
        for obj in context.selected_objects:
            disable_cloth_physics(chr_cache, obj)

    elif param == "PHYSICS_ADD_COLLISION":
        restore_collision_proxy_view(context, chr_cache)
        objects = context.selected_objects
        for obj in objects:
            enable_collision_physics(chr_cache, obj)
        show_hide_collision_proxies(context, chr_cache, False)

    elif param == "PHYSICS_REMOVE_COLLISION":
        restore_collision_proxy_view(context, chr_cache)
        objects = context.selected_objects
        for obj in objects:
            disable_collision_physics(chr_cache, obj)
        show_hide_collision_proxies(context, chr_cache, False)

    elif param == "PHYSICS_ADD_WEIGHTMAP":
        if obj:
            enable_material_weight_map(chr_cache, obj, utils.get_context_material(context))

    elif param == "PHYSICS_REMOVE_WEIGHTMAP":
        if obj:
            disable_material_weight_map(chr_cache, obj, utils.get_context_material(context))

    elif param == "PHYSICS_RESIZE_WEIGHTMAP":
        if obj:
            resize_weight_map(chr_cache, context, op)

    elif param == "PHYSICS_HAIR":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "HAIR", False)

    elif param == "PHYSICS_DENIM":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "DENIM", get_self_collision(chr_cache, obj))

    elif param == "PHYSICS_LEATHER":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "LEATHER", get_self_collision(chr_cache, obj))

    elif param == "PHYSICS_RUBBER":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "RUBBER", get_self_collision(chr_cache, obj))

    elif param == "PHYSICS_SILK":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "SILK", get_self_collision(chr_cache, obj))

    elif param == "PHYSICS_COTTON":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "COTTON", get_self_collision(chr_cache, obj))

    elif param == "PHYSICS_LINEN":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "LINEN", get_self_collision(chr_cache, obj))

    elif param == "PHYSICS_PAINT":
        if obj:
            begin_paint_weight_map(context, chr_cache)

    elif param == "PHYSICS_DONE_PAINTING":
        end_paint_weight_map(op, context, chr_cache)

    elif param == "PHYSICS_SAVE":
        save_dirty_weight_maps(chr_cache, bpy.context.selected_objects)

    elif param == "BROWSE_WEIGHTMAP":
        browse_weight_map(chr_cache, context)

    elif param == "PHYSICS_DELETE":
        if obj:
            delete_selected_weight_map(chr_cache, obj, utils.get_context_material(context))

    elif param == "PHYSICS_SEPARATE":
        separate_physics_materials(chr_cache, obj)

    elif param == "PHYSICS_FIX_DEGENERATE":
        if obj:
            if context.object.mode != "EDIT" and context.object.mode != "OBJECT":
                bpy.ops.object.mode_set(mode = 'OBJECT')
            if context.object.mode != "EDIT":
                bpy.ops.object.mode_set(mode = 'EDIT')
            if context.object.mode == "EDIT":
                bpy.ops.mesh.select_all(action = 'SELECT')
                bpy.ops.mesh.dissolve_degenerate()
            bpy.ops.object.mode_set(mode = 'OBJECT')
            op.report({'INFO'}, f"Degenerate elements removed for {obj.name}")

    elif param == "DISABLE_PHYSICS":
        if chr_cache:
            restore_collision_proxy_view(context, chr_cache)
            disable_physics(chr_cache)
            op.report({'INFO'}, f"Physics disabled for {chr_cache.character_name}")

    elif param == "ENABLE_PHYSICS":
        if chr_cache:
            restore_collision_proxy_view(context, chr_cache)
            enable_physics(chr_cache)
            op.report({'INFO'}, f"Physics enabled for {chr_cache.character_name}")

    elif param == "REMOVE_PHYSICS":
        if chr_cache:
            restore_collision_proxy_view(context, chr_cache)
            remove_all_physics(chr_cache)
            op.report({'INFO'}, f"Physics removed for {chr_cache.character_name}")

    elif param == "APPLY_PHYSICS":
        if chr_cache:
            restore_collision_proxy_view(context, chr_cache)
            apply_all_physics(chr_cache)
            op.report({'INFO'}, f"Physics applied to {chr_cache.character_name}")

    elif param == "PHYSICS_INC_STRENGTH":
        strength = float(round(props.physics_paint_strength * 10)) / 10.0
        props.physics_paint_strength = min(1.0, max(0.0, strength + 0.1))

    elif param == "PHYSICS_DEC_STRENGTH":
        strength = float(round(props.physics_paint_strength * 10)) / 10.0
        props.physics_paint_strength = min(1.0, max(0.0, strength - 0.1))

    elif param == "TOGGLE_SHOW_PROXY":
        if chr_cache and obj:
            context_object, context_proxy, context_is_proxy = chr_cache.get_related_physics_objects(obj)
            if context_object and context_proxy:
                proxy_visible = context_proxy.visible_get()
                if show_hide_collision_proxies(context, chr_cache,
                                               not proxy_visible,
                                               select=False,
                                               use_local=True):
                    utils.set_active_object(context_proxy)
                else:
                    utils.set_active_object(context_object)


class CC3OperatorPhysics(bpy.types.Operator):
    """Physics Settings Functions"""
    bl_idname = "cc3.setphysics"
    bl_label = "Physics Settings Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):

        set_physics_settings(self, context, self.param)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "PHYSICS_ADD_CLOTH":
            return "Add Cloth physics to the selected objects."
        elif properties.param == "PHYSICS_REMOVE_CLOTH":
            return "Remove Cloth physics from the selected objects and remove all weight map modifiers and physics vertex groups"
        elif properties.param == "PHYSICS_ADD_COLLISION":
            return "Add Collision physics to the selected objects"
        elif properties.param == "PHYSICS_REMOVE_COLLISION":
            return "Remove Collision physics from the selected objects"
        elif properties.param == "PHYSICS_ADD_WEIGHTMAP":
            return "Add a physics weight map to the material on the current object. " \
                   "If there is no existing weight map, a new blank weight map will be created. " \
                   "Modifiers to generate the physics vertex groups will be added to the object"
        elif properties.param == "PHYSICS_REMOVE_WEIGHTMAP":
            return "Removes the physics weight map, modifiers and physics vertex groups for this material from the object"
        elif properties.param == "PHYSICS_RESIZE_WEIGHTMAP":
            return "Resizes the physics weightmap to the current size"
        elif properties.param == "PHYSICS_HAIR":
            return "Sets the cloth physics settings for this object to simulate Hair.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_COTTON":
            return "Sets the cloth physics settings for this object to simulate Cotton.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_DENIM":
            return "Sets the cloth physics settings for this object to simulate Denim.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_LEATHER":
            return "Sets the cloth physics settings for this object to simulate Leather.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_RUBBER":
            return "Sets the cloth physics settings for this object to simulate Rubber.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_SILK":
            return "Sets the cloth physics settings for this object to simulate Silk.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_PAINT":
            return "Switches to texture paint mode and begins painting the current materials PhysX weight map"
        elif properties.param == "PHYSICS_DONE_PAINTING":
            return "Ends painting and returns to Object mode"
        elif properties.param == "PHYSICS_SAVE":
            return "Saves all changes to the weight maps to the source texture files\n" \
                   "**Warning: This will overwrite the existing weightmap files if you have altered them!**"
        elif properties.param == "PHYSICS_DELETE":
            return "Removes the weight map, modifiers and physics vertex groups from the objects, " \
                   "and then deletes the weight map texture file.\n" \
                   "**Warning: This will delete any existing weightmap file for this object and material!**"
        elif properties.param == "PHYSICS_SEPARATE":
            return "Separates the object by material and applies physics to the separated objects that have weight maps.\n" \
                   "Note: Some objects with many vertices and materials but only a small amount is cloth simulated " \
                   "may see performance benefits from being separated."
        elif properties.param == "PHYSICS_FIX_DEGENERATE":
            return "Removes degenerate mesh elements from the object.\n" \
                   "Note: Meshes with degenerate elements, loose vertices, orphaned edges, zero length edges etc...\n" \
                   "might not simulate properly. If the mesh misbehaves badly under simulation, try this."
        elif properties.param == "DISABLE_PHYSICS":
            return "Temporarily disable all physics modifiers for the characater."
        elif properties.param == "ENABLE_PHYSICS":
            return "Re-enable all physics modifiers for the characater."
        elif properties.param == "REMOVE_PHYSICS":
            return "Remove all physics modifiers for the characater."
        elif properties.param == "APPLY_PHYSICS":
            return "Add all possible physics modifiers for the characater."
        elif properties.param == "PHYSICS_INC_STRENGTH":
            return "Increase weight paint strength by 10%"
        elif properties.param == "PHYSICS_DEC_STRENGTH":
            return "Decrease weight paint strength by 10%"

        return ""
