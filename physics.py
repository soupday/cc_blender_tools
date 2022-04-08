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

import math
import os

import bpy

from . import imageutils, meshutils, modifiers, utils, vars


def apply_cloth_settings(obj, cloth_type):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    mod = modifiers.get_cloth_physics_mod(obj)
    if mod is None:
        return
    cache = props.get_object_cache(obj)
    cache.cloth_settings = cloth_type

    utils.log_info("Setting " + obj.name + " cloth settings to: " + cloth_type)
    mod.settings.vertex_group_mass = prefs.physics_group + "_Pin"
    mod.settings.time_scale = 1
    if cloth_type == "HAIR":
        mod.settings.quality = 4
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.15
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 5
        mod.settings.compression_stiffness = 5
        mod.settings.shear_stiffness = 5
        mod.settings.bending_stiffness = 5
        # dampening
        mod.settings.tension_damping = 0
        mod.settings.compression_damping = 0
        mod.settings.shear_damping = 0
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 2
    elif cloth_type == "SILK":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.25
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 5
        mod.settings.compression_stiffness = 5
        mod.settings.shear_stiffness = 5
        mod.settings.bending_stiffness = 10
        # dampening
        mod.settings.tension_damping = 0
        mod.settings.compression_damping = 0
        mod.settings.shear_damping = 0
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    elif cloth_type == "DENIM":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 1
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 40
        mod.settings.compression_stiffness = 40
        mod.settings.shear_stiffness = 40
        mod.settings.bending_stiffness = 60
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 10
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    elif cloth_type == "LEATHER":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.4
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 80
        mod.settings.compression_stiffness = 80
        mod.settings.shear_stiffness = 80
        mod.settings.bending_stiffness = 80
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 10
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    elif cloth_type == "RUBBER":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 3
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 15
        mod.settings.compression_stiffness = 15
        mod.settings.shear_stiffness = 15
        mod.settings.bending_stiffness = 40
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    else: #cotton
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.3
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 20
        mod.settings.compression_stiffness = 20
        mod.settings.shear_stiffness = 20
        mod.settings.bending_stiffness = 20
        # dampening
        mod.settings.tension_damping = 5
        mod.settings.compression_damping = 5
        mod.settings.shear_damping = 5
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4


def add_collision_physics(obj):
    """Adds a Collision modifier to the object, depending on the object cache settings.

    Does not overwrite or re-create any existing Collision modifier.
    """
    props = bpy.context.scene.CC3ImportProps

    cache = props.get_object_cache(obj)
    if (cache.collision_physics == "ON"
        or (cache.collision_physics == "DEFAULT"
            and "Base_Body" in obj.name)):

        if modifiers.get_collision_physics_mod(obj) is None:
            collision_mod = obj.modifiers.new(utils.unique_name("Collision"), type="COLLISION")
            collision_mod.settings.thickness_outer = 0.005
            utils.log_info("Collision Modifier: " + collision_mod.name + " applied to " + obj.name)
    elif cache.collision_physics == "OFF":
        utils.log_info("Collision Physics disabled for: " + obj.name)


def remove_collision_physics(obj):
    """Removes the Collision modifier from the object.
    """

    for mod in obj.modifiers:
        if mod.type == "COLLISION":
            utils.log_info("Removing Collision modifer: " + mod.name + " from: " + obj.name)
            obj.modifiers.remove(mod)


def add_cloth_physics(obj):
    """Adds a Cloth modifier to the object depending on the object cache settings.

    Does not overwrite or re-create any existing Cloth modifier.
    Sets the cache bake range to the same as any action on the character's armature.
    Applies cloth settings based on the object cache settings.
    Repopulates the existing weight maps, depending on their cache settings.
    """

    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    props = bpy.context.scene.CC3ImportProps

    obj_cache = props.get_object_cache(obj)

    if obj_cache.cloth_physics == "ON" and modifiers.get_cloth_physics_mod(obj) is None:

        # Create the Cloth modifier
        cloth_mod = obj.modifiers.new(utils.unique_name("Cloth"), type="CLOTH")
        utils.log_info("Cloth Modifier: " + cloth_mod.name + " applied to " + obj.name)

        # Create the physics pin vertex group if it doesn't exist
        pin_group = prefs.physics_group + "_Pin"
        if pin_group not in obj.vertex_groups:
            obj.vertex_groups.new(name = pin_group)

        # Set cache bake frame range
        frame_count = 250
        if obj.parent is not None and obj.parent.animation_data is not None and \
                obj.parent.animation_data.action is not None:
            frame_start = math.floor(obj.parent.animation_data.action.frame_range[0])
            frame_count = math.ceil(obj.parent.animation_data.action.frame_range[1])
        utils.log_info("Setting " + obj.name + " bake cache frame range to [1-" + str(frame_count) + "]")
        cloth_mod.point_cache.frame_start = frame_start
        cloth_mod.point_cache.frame_end = frame_count

        # Apply cloth settings
        if obj_cache.cloth_settings != "DEFAULT":
            apply_cloth_settings(obj, obj_cache.cloth_settings)
        elif obj_cache.object_type == "HAIR":
            apply_cloth_settings(obj, "HAIR")
        else:
            apply_cloth_settings(obj, "COTTON")

        # Add any existing weight maps
        for mat in obj.data.materials:
            if mat:
                add_material_weight_map(obj, mat, create = False)

        # fix mod order
        modifiers.move_mod_last(obj, cloth_mod)

    elif obj_cache.cloth_physics == "OFF":
        utils.log_info("Cloth Physics disabled for: " + obj.name)


def remove_cloth_physics(obj):
    """Removes the Cloth modifier from the object.

    Also removes any active weight maps and also removes the weight map vertex group.
    """

    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

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


def enable_collision_physics(obj):
    props = bpy.context.scene.CC3ImportProps
    cache = props.get_object_cache(obj)
    cache.collision_physics = "ON"
    utils.log_info("Enabling Collision physics for: " + obj.name)
    add_collision_physics(obj)


def disable_collision_physics(obj):
    props = bpy.context.scene.CC3ImportProps
    cache = props.get_object_cache(obj)
    cache.collision_physics = "OFF"
    utils.log_info("Disabling Collision physics for: " + obj.name)
    remove_collision_physics(obj)


def enable_cloth_physics(obj):
    props = bpy.context.scene.CC3ImportProps
    cache = props.get_object_cache(obj)
    cache.cloth_physics = "ON"
    utils.log_info("Enabling Cloth physics for: " + obj.name)
    add_cloth_physics(obj)


def disable_cloth_physics(obj):
    props = bpy.context.scene.CC3ImportProps
    cache = props.get_object_cache(obj)
    cache.cloth_physics = "OFF"
    utils.log_info("Removing cloth physics for: " + obj.name)
    remove_cloth_physics(obj)


def get_weight_map_image(obj, mat, create = False):
    """Returns the weight map image for the material.

    Fetches the Image for the given materials weight map, if it exists.
    If not, the image can be created and packed into the blend file and stored
    in the material cache as a temporary weight map image.
    """

    props = bpy.context.scene.CC3ImportProps
    weight_map = imageutils.find_material_image(mat, "WEIGHTMAP")

    if weight_map is None and create:
        cache = props.get_material_cache(mat)
        name = utils.strip_name(mat.name) + "_WeightMap"
        tex_size = int(props.physics_tex_size)
        weight_map = bpy.data.images.new(name, tex_size, tex_size, is_data=True)
        # make the image 'dirty' so it converts to a file based image which can be saved:
        weight_map.pixels[0] = 0.0
        weight_map.file_format = "PNG"
        weight_map.filepath_raw = os.path.join(cache.dir, name + ".png")
        weight_map.save()
        # keep track of which weight maps we created:
        cache.temp_weight_map = weight_map
        utils.log_info("Weight-map image: " + weight_map.name + " created and saved.")

    return weight_map


def add_material_weight_map(obj, mat, create = False):
    """Adds a weight map 'Vertex Weight Edit' modifier for the object's material.

    Gets or creates (if instructed) the material's weight map then creates
    or re-creates the modifier to generate the physics 'Pin' vertex group.
    """

    if cloth_physics_available(obj, mat):
        if create:
            weight_map = get_weight_map_image(obj, mat, create)
        else:
            weight_map = imageutils.find_material_image(mat, "WEIGHTMAP")

        remove_material_weight_maps(obj, mat)
        if weight_map is not None:
            attach_material_weight_map(obj, mat, weight_map)
    else:
        utils.log_info("Cloth Physics has been disabled for: " + obj.name)
        return


def remove_material_weight_maps(obj, mat):
    """Removes the weight map 'Vertex Weight Edit' modifier for the object's material.

    This does not remove or delete the weight map image or temporary packed image,
    or the texture based on the weight map image, just the modifier.
    """

    edit_mod, mix_mod = modifiers.get_material_weight_map_mods(obj, mat)
    if edit_mod is not None:
        utils.log_info("Removing weight map vertex edit modifer: " + edit_mod.name)
        obj.modifiers.remove(edit_mod)
    if mix_mod is not None:
        utils.log_info("Removing weight map vertex mix modifer: " + mix_mod.name)
        obj.modifiers.remove(mix_mod)


def enable_material_weight_map(obj, mat):
    """Enables the weight map for the object's material and (re)creates the Vertex Weight Edit modifier.
    """
    props = bpy.context.scene.CC3ImportProps
    cache = props.get_material_cache(mat)
    if cache.cloth_physics == "OFF":
        cache.cloth_physics = "ON"
    add_material_weight_map(obj, mat, True)
    # fix mod order
    cloth_mod = modifiers.get_cloth_physics_mod(obj)
    modifiers.move_mod_last(obj, cloth_mod)


def disable_material_weight_map(obj, mat):
    """Disables the weight map for the object's material and removes the Vertex Weight Edit modifier.
    """
    props = bpy.context.scene.CC3ImportProps
    cache = props.get_material_cache(mat)
    cache.cloth_physics = "OFF"
    remove_material_weight_maps(obj, mat)
    pass


def collision_physics_available(obj):
    props = bpy.context.scene.CC3ImportProps
    obj_cache = props.get_object_cache(obj)
    collision_mod = modifiers.get_collision_physics_mod(obj)
    if collision_mod is None:
        if obj_cache.collision_physics == "OFF":
            return False
    return True


def cloth_physics_available(obj, mat):
    """Is cloth physics allowed on this object and material?
    """
    props = bpy.context.scene.CC3ImportProps
    obj_cache = props.get_object_cache(obj)
    mat_cache = props.get_material_cache(mat)
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


def attach_material_weight_map(obj, mat, weight_map):
    """Attaches a weight map to the object's material via a 'Vertex Weight Edit' modifier.

    This will attach the supplied weight map or will try to find an existing weight map,
    but will not create a new weight map if it doesn't already exist.
    """

    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if weight_map is not None:
        # Make a texture based on the weight map image
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
        mat_verts = meshutils.get_material_vertices(obj, mat)
        weight_vertex_group.add(mat_verts, 1.0, 'ADD')
        # The pin group should contain all vertices in the mesh default weighted to 1.0
        meshutils.set_vertex_group(obj, pin_vertex_group, 1.0)

        # set the pin group in the cloth physics modifier
        mod_cloth = modifiers.get_cloth_physics_mod(obj)
        if mod_cloth is not None:
            mod_cloth.settings.vertex_group_mass = pin_group

        # re-create create the Vertex Weight Edit modifier and the Vertex Weight Mix modifer
        remove_material_weight_maps(obj, mat)
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
    props = bpy.context.scene.CC3ImportProps

    if bpy.context.mode == "PAINT_TEXTURE":
        ups = context.tool_settings.unified_paint_settings
        prop_owner = ups if ups.use_unified_color else context.tool_settings.image_paint.brush
        s = props.physics_paint_strength
        prop_owner.color = (s, s, s)

def weight_strength_update(self, context):
    props = bpy.context.scene.CC3ImportProps

    strength = props.weight_map_strength
    influence = 1 - math.pow(1 - strength, 3)
    edit_mod, mix_mod = modifiers.get_material_weight_map_mods(context.object, utils.context_material(context))
    mix_mod.mask_constant = influence



def begin_paint_weight_map(context):
    obj = context.object
    mat = utils.context_material(context)
    props = bpy.context.scene.CC3ImportProps
    if obj is not None and mat is not None:
        props.paint_store_render = bpy.context.space_data.shading.type

        if bpy.context.mode != "PAINT_TEXTURE":
            bpy.ops.object.mode_set(mode="TEXTURE_PAINT")

        if bpy.context.mode == "PAINT_TEXTURE":
            physics_paint_strength_update(None, context)
            weight_map = get_weight_map_image(obj, mat)
            props.paint_object = obj
            props.paint_material = mat
            props.paint_image = weight_map
            if weight_map is not None:
                bpy.context.scene.tool_settings.image_paint.mode = 'IMAGE'
                bpy.context.scene.tool_settings.image_paint.canvas = weight_map
                bpy.context.space_data.shading.type = 'SOLID'


def end_paint_weight_map():
    try:
        props = bpy.context.scene.CC3ImportProps
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.space_data.shading.type = props.paint_store_render
        #props.paint_image.save()
    except Exception as e:
        utils.log_error("Something went wrong restoring object mode from paint mode!", e)


def save_dirty_weight_maps(objects):
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


def delete_selected_weight_map(obj, mat):
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


def set_physics_bake_range(obj, start, end):
    cloth_mod = modifiers.get_cloth_physics_mod(obj)

    if cloth_mod is not None:
        if obj.parent is not None and obj.parent.type == "ARMATURE":
            arm = obj.parent
            if arm.animation_data is not None and arm.animation_data.action is not None:
                frame_start = math.floor(arm.animation_data.action.frame_range[0])
                frame_end = math.ceil(arm.animation_data.action.frame_range[1])
                if frame_start < start:
                    start = frame_start
                if frame_end > end:
                    end = frame_end

            utils.log_info("Setting " + obj.name + " bake cache frame range to [" + str(start) + " -" + str(end) + "]")
            cloth_mod.point_cache.frame_start = start
            cloth_mod.point_cache.frame_end = end
            return True
    return False

def prepare_physics_bake(context):
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_context_character_cache(context)

    if chr_cache:
        for obj_cache in chr_cache.object_cache:
            if obj_cache.object is not None and obj_cache.object.type == "MESH":
                obj = obj_cache.object
                set_physics_bake_range(obj, context.scene.frame_start, context.scene.frame_end)


def separate_physics_materials(context):
    obj = context.object
    if (obj is not None
        and obj.type == "MESH"
        and context.mode == "OBJECT"):

        # remember which materials have active weight maps
        temp = []
        for mat in obj.data.materials:
            if mat:
                edit_mod, mix_mod = modifiers.get_material_weight_map_mods(obj, mat)
                if edit_mod is not None:
                    temp.append(mat)

        # remove cloth physics from the object
        disable_cloth_physics(obj)

        # split the mesh by materials
        utils.tag_objects()
        obj.tag = False
        bpy.ops.mesh.separate(type='MATERIAL')
        split_objects = utils.untagged_objects()

        # re-apply cloth physics to the materials which had weight maps
        for split in split_objects:
            for mat in split.data.materials:
                if mat in temp:
                    enable_cloth_physics(split)
                    break
        temp = None


def should_separate_materials(context):
    """Check to see if the current object has a weight map for each material.
    If not separating the mesh by material could improve performance.
    """
    obj = context.object
    if obj is not None and obj.type == "MESH":

        cloth_mod = modifiers.get_cloth_physics_mod(obj)
        if cloth_mod is not None:
            edit_mods, mix_mods = modifiers.get_weight_map_mods(obj)
            if len(edit_mods) != len(obj.data.materials):
                return True
        return False



def set_physics_settings(param, context = bpy.context):
    props = bpy.context.scene.CC3ImportProps

    if param == "PHYSICS_ADD_CLOTH":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                enable_cloth_physics(obj)
    elif param == "PHYSICS_REMOVE_CLOTH":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                disable_cloth_physics(obj)
    elif param == "PHYSICS_ADD_COLLISION":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                enable_collision_physics(obj)
    elif param == "PHYSICS_REMOVE_COLLISION":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                disable_collision_physics(obj)
    elif param == "PHYSICS_ADD_WEIGHTMAP":
        if context.object is not None and context.object.type == "MESH":
            enable_material_weight_map(context.object, utils.context_material(context))
    elif param == "PHYSICS_REMOVE_WEIGHTMAP":
        if context.object is not None and context.object.type == "MESH":
            disable_material_weight_map(context.object, utils.context_material(context))
    elif param == "PHYSICS_HAIR":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "HAIR")
    elif param == "PHYSICS_COTTON":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "COTTON")
    elif param == "PHYSICS_DENIM":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "DENIM")
    elif param == "PHYSICS_LEATHER":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "LEATHER")
    elif param == "PHYSICS_RUBBER":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "RUBBER")
    elif param == "PHYSICS_SILK":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                apply_cloth_settings(obj, "SILK")
    elif param == "PHYSICS_PAINT":
        if context.object is not None and context.object.type == "MESH":
            begin_paint_weight_map(context)
    elif param == "PHYSICS_DONE_PAINTING":
        end_paint_weight_map()
    elif param == "PHYSICS_SAVE":
        save_dirty_weight_maps(bpy.context.selected_objects)
    elif param == "PHYSICS_DELETE":
        delete_selected_weight_map(context.object, utils.context_material(context))
    elif param == "PHYSICS_SEPARATE":
        separate_physics_materials(context)
    elif param == "PHYSICS_FIX_DEGENERATE":
        if context.object is not None:
            if bpy.context.object.mode != "EDIT" and bpy.context.object.mode != "OBJECT":
                bpy.ops.object.mode_set(mode = 'OBJECT')
            if bpy.context.object.mode != "EDIT":
                bpy.ops.object.mode_set(mode = 'EDIT')
            if bpy.context.object.mode == "EDIT":
                bpy.ops.mesh.select_all(action = 'SELECT')
                bpy.ops.mesh.dissolve_degenerate()
            bpy.ops.object.mode_set(mode = 'OBJECT')


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

        set_physics_settings(self.param, context)

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

        return ""