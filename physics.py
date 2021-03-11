import math
import os

import bpy

from .cache import *
from .images import *
from .utils import *
from .vars import *


def get_cloth_physics_mod(obj):
    for mod in obj.modifiers:
        if mod.type == "CLOTH" and NODE_PREFIX in mod.name:
            return mod
    return None


def get_collision_physics_mod(obj):
    for mod in obj.modifiers:
        if mod.type == "COLLISION" and NODE_PREFIX in mod.name:
            return mod
    return None


def get_weight_map_mods(obj):
    mods = []
    for mod in obj.modifiers:
        if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name:
            mods.append(mod)
    return mods


def get_weight_map_mod(obj, mat):
    if obj is None or mat is None: return None
    for mod in obj.modifiers:
        if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name and (mat.name + "_WeightMix") in mod.name:
            return mod
    return None


def add_collision_physics(obj):
    """Adds a Collision modifier to the object, depending on the object cache settings.

    Does not overwrite or re-create any existing Collision modifier.
    """

    cache = get_object_cache(obj)
    if (cache.collision_physics == "ON"
        or (cache.collision_physics == "DEFAULT"
            and "Base_Body" in obj.name)):

        if get_collision_physics_mod(obj) is None:
            collision_mod = obj.modifiers.new(name=unique_name("Collision"), type="COLLISION")
            collision_mod.settings.thickness_outer = 0.005
            log_info("Collision Modifier: " + collision_mod.name + " applied to " + obj.name)
    elif cache.collision_physics == "OFF":
        log_info("Collision Physics disabled for: " + obj.name)


def remove_collision_physics(obj):
    """Removes the Collision modifier from the object.
    """

    for mod in obj.modifiers:
        if mod.type == "COLLISION" and NODE_PREFIX in mod.name:
            log_info("Removing Collision modifer: " + mod.name + " from: " + obj.name)
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

    cache = get_object_cache(obj)

    if cache.cloth_physics == "ON" and get_cloth_physics_mod(obj) is None:

        # Create the Cloth modifier
        cloth_mod = obj.modifiers.new(name=unique_name("Cloth"), type="CLOTH")
        log_info("Cloth Modifier: " + cloth_mod.name + " applied to " + obj.name)

        # Create the physics pin vertex group if it doesn't exist
        if prefs.physics_group not in obj.vertex_groups:
            obj.vertex_groups.new(name = prefs.physics_group)

        # Set cache bake frame range
        frame_count = 250
        if obj.parent is not None and obj.parent.animation_data is not None and \
                obj.parent.animation_data.action is not None:
            frame_count = math.ceil(obj.parent.animation_data.action.frame_range[1])
        log_info("Setting " + obj.name + " bake cache frame range to [1-" + str(frame_count) + "]")
        cloth_mod.point_cache.frame_start = 1
        cloth_mod.point_cache.frame_end = frame_count

        # Apply cloth settings
        if cache.cloth_settings != "NONE":
            apply_cloth_settings(obj, cache.cloth_settings)
        elif obj == props.hair_object:
            apply_cloth_settings(obj, "HAIR")
        else:
            apply_cloth_settings(obj, "COTTON")

        # Add any existing weight maps
        for mat in obj.data.materials:
            add_material_weight_map(obj, mat, create = False)

    elif cache.cloth_physics == "OFF":
        log_info("Cloth Physics disabled for: " + obj.name)


def remove_cloth_physics(obj):
    """Removes the Cloth modifier from the object.

    Also removes any active weight maps and also removes the weight map vertex group.
    """

    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    # Remove the Cloth modifier
    for mod in obj.modifiers:
        if mod.type == "CLOTH" and NODE_PREFIX in mod.name:
            log_info("Removing Cloth modifer: " + mod.name + " from: " + obj.name)
            obj.modifiers.remove(mod)

    # Remove any weight maps
    for mat in obj.data.materials:
        if mat is not None:
            remove_material_weight_map(obj, mat)

    # If there are no weight maps left on the object, remove the vertex group
    mods = 0
    for mod in obj.modifiers:
        if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name:
            mods += 1
    if mods == 0 and prefs.physics_group in obj.vertex_groups:
        log_info("Removing vertex group: " + prefs.physics_group + " from: " + obj.name)
        obj.vertex_groups.remove(obj.vertex_groups[prefs.physics_group])


def remove_all_physics_mods(obj):
    """Removes all physics modifiers from the object.

    Used when (re)building the character materials.
    """

    log_info("Removing all related physics modifiers from: " + obj.name)
    for mod in obj.modifiers:
        if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name:
            obj.modifiers.remove(mod)
        elif mod.type == "CLOTH" and NODE_PREFIX in mod.name:
            obj.modifiers.remove(mod)
        elif mod.type == "COLLISION" and NODE_PREFIX in mod.name:
            obj.modifiers.remove(mod)


def enable_collision_physics(obj):
    cache = get_object_cache(obj)
    cache.collision_physics = "ON"
    log_info("Enabling Collision physics for: " + obj.name)
    add_collision_physics(obj)


def disable_collision_physics(obj):
    cache = get_object_cache(obj)
    cache.collision_physics = "OFF"
    log_info("Disabling Collision physics for: " + obj.name)
    remove_collision_physics(obj)


def enable_cloth_physics(obj):
    cache = get_object_cache(obj)
    cache.cloth_physics = "ON"
    log_info("Enabling Cloth physics for: " + obj.name)
    add_cloth_physics(obj)
    for mat in obj.data.materials:
        add_material_weight_map(obj, mat, create = False)


def disable_cloth_physics(obj):
    cache = get_object_cache(obj)
    cache.cloth_physics = "OFF"
    log_info("Removing cloth physics for: " + obj.name)
    remove_cloth_physics(obj)


def get_weight_map_image(obj, mat, create = False):
    """Returns the weight map image for the material.

    Fetches the Image for the given materials weight map, if it exists.
    If not, the image can be created and packed into the blend file and stored
    in the material cache as a temporary weight map image.
    """

    props = bpy.context.scene.CC3ImportProps
    weight_map = find_material_image(mat, WEIGHT_MAP)

    if weight_map is None and create:
        tex_size = int(props.physics_tex_size)
        weight_map = bpy.data.images.new(mat.name + "_WeightMap", tex_size, tex_size, is_data=True)
        # make the image 'dirty' so it can be packed
        weight_map.pixels[0] = 0.0
        weight_map.pack()

        cache = get_material_cache(mat)
        if cache is not None:
            cache.temp_weight_map = weight_map

        log_info("Weight-map image: " + weight_map.name + " created and packed")

    return weight_map


def add_material_weight_map(obj, mat, create = False):
    """Adds a weight map 'Vertex Weight Edit' modifier for the object's material.

    Gets or creates (if instructed) the material's weight map then creates
    or re-creates the modifier to generate the physics 'Pin' vertex group.
    """
    if create:
        weight_map = get_weight_map_image(obj, mat, create)
    else:
        weight_map = find_material_image(mat, WEIGHT_MAP)
    cache = get_material_cache(mat)

    remove_material_weight_map(obj, mat)
    if cache.cloth_physics != "OFF":
        if weight_map is not None:
            attach_material_weight_map(obj, mat, weight_map)


def remove_material_weight_map(obj, mat):
    """Removes the weight map 'Vertex Weight Edit' modifier for the object's material.

    This does not remove or delete the weight map image or temporary packed image,
    or the texture based on the weight map image, just the modifier.
    """

    for mod in obj.modifiers:
        if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name:
            if mat.name + "_WeightMix" in mod.name:
                log_info("    Removing weight map vertex edit modifer: " + mod.name)
                obj.modifiers.remove(mod)


def enable_material_weight_map(obj, mat):
    """Enables the weight map for the object's material and (re)creates the Vertex Weight Edit modifier.
    """

    cache = get_material_cache(mat)
    if cache.cloth_physics == "OFF":
        cache.cloth_physics = "ON"
    add_material_weight_map(obj, mat, True)


def disable_material_weight_map(obj, mat):
    """Disables the weight map for the object's material and removes the Vertex Weight Edit modifier.
    """

    cache = get_material_cache(mat)
    cache.cloth_physics = "OFF"
    remove_material_weight_map(obj, mat)
    pass


def attach_material_weight_map(obj, mat, weight_map):
    """Attaches a weight map to the object's material via a 'Vertex Weight Edit' modifier.

    This will attach the supplied weight map or will try to find an existing weight map,
    but will not create a new weight map if it doesn't already exist.
    """

    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)

    # TODO These need to be in the material cache, not the object cache....
    # weight map instructions prefixed as "REMOVED" will not be attached
    if obj_cache.cloth_physics == "OFF":
        log_info("Cloth Physics has been disabled for: " + obj.name)
        return
    if mat_cache.cloth_physics == "OFF":
        log_info("Weight maps have been disabled for: " + obj.name + "/" + mat.name)
        return

    if weight_map is not None:
        # Make a texture based on the weight map image
        tex_name = mat.name + "_Weight"
        tex = None
        for t in bpy.data.textures:
            if tex_name in t.name:
                tex = t
        if tex is None:
            tex = bpy.data.textures.new(unique_name(tex_name), "IMAGE")
            log_info("Texture: " + tex.name + " created for weight map transfer")
        else:
            log_info("Texture: " + tex.name + " already exists for weight map transfer")
        tex.image = weight_map

        # Create the physics pin vertex group if it doesn't exist
        if prefs.physics_group not in obj.vertex_groups:
            obj.vertex_groups.new(name = prefs.physics_group)

        # (Re)Create create the Vertex Weight Edit modifier
        remove_material_weight_map(obj, mat)
        mod = obj.modifiers.new(unique_name(mat.name + "_WeightMix"), "VERTEX_WEIGHT_EDIT")
        # Use the texture as the modifiers vertex weight source
        mod.mask_texture = tex
        # Setup the modifier to generate the inverse of the weight map in the vertex group
        mod.use_add = True
        mod.use_remove = True
        mod.add_threshold = 0.01
        mod.remove_threshold = 0.01
        mod.vertex_group = prefs.physics_group
        mod.default_weight = 1
        mod.falloff_type = 'LINEAR'
        mod.invert_falloff = True
        mod.mask_constant = 1
        mod.mask_tex_mapping = 'UV'
        mod.mask_tex_use_channel = 'INT'
        log_info("Weight map: " + weight_map.name + " applied to: " + obj.name + "/" + mat.name)


def apply_cloth_settings(obj, cloth_type):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    mod = get_cloth_physics_mod(obj)
    cache = get_object_cache(obj)
    cache.cloth_settings = cloth_type

    log_info("Setting " + obj.name + " cloth settings to: " + cloth_type)
    mod.settings.vertex_group_mass = prefs.physics_group
    mod.settings.time_scale = 1
    if cloth_type == "HAIR":
        mod.settings.quality = 4
        mod.settings.pin_stiffness = 0.02
        # physical properties
        mod.settings.mass = 0.25
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 5
        mod.settings.compression_stiffness = 5
        mod.settings.shear_stiffness = 5
        mod.settings.bending_stiffness = 0.01
        # dampening
        mod.settings.tension_damping = 0
        mod.settings.compression_damping = 0
        mod.settings.shear_damping = 0
        mod.settings.bending_damping = 0.1
        # collision
        mod.collision_settings.distance_min = 0.005
    elif cloth_type == "SILK":
        mod.settings.quality = 4
        mod.settings.pin_stiffness = 0.2
        # physical properties
        mod.settings.mass = 0.15
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 5
        mod.settings.compression_stiffness = 5
        mod.settings.shear_stiffness = 5
        mod.settings.bending_stiffness = 0.05
        # dampening
        mod.settings.tension_damping = 0
        mod.settings.compression_damping = 0
        mod.settings.shear_damping = 0
        mod.settings.bending_damping = 0.1
        # collision
        mod.collision_settings.distance_min = 0.005
    elif cloth_type == "DENIM":
        mod.settings.quality = 4
        mod.settings.pin_stiffness = 0.2
        # physical properties
        mod.settings.mass = 1
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 40
        mod.settings.compression_stiffness = 40
        mod.settings.shear_stiffness = 40
        mod.settings.bending_stiffness = 10
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 0.1
        # collision
        mod.collision_settings.distance_min = 0.005
    elif cloth_type == "LEATHER":
        mod.settings.quality = 4
        mod.settings.pin_stiffness = 0.2
        # physical properties
        mod.settings.mass = 0.4
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 80
        mod.settings.compression_stiffness = 80
        mod.settings.shear_stiffness = 80
        mod.settings.bending_stiffness = 150
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 0.1
        # collision
        mod.collision_settings.distance_min = 0.005
    elif cloth_type == "RUBBER":
        mod.settings.quality = 4
        mod.settings.pin_stiffness = 0.2
        # physical properties
        mod.settings.mass = 3
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 15
        mod.settings.compression_stiffness = 15
        mod.settings.shear_stiffness = 15
        mod.settings.bending_stiffness = 25
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 0.1
        # collision
        mod.collision_settings.distance_min = 0.005
    else: #cotton
        mod.settings.quality = 4
        mod.settings.pin_stiffness = 0.2
        # physical properties
        mod.settings.mass = 0.3
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 15
        mod.settings.compression_stiffness = 15
        mod.settings.shear_stiffness = 15
        mod.settings.bending_stiffness = 0.5
        # dampening
        mod.settings.tension_damping = 5
        mod.settings.compression_damping = 5
        mod.settings.shear_damping = 5
        mod.settings.bending_damping = 0.1
        # collision
        mod.collision_settings.distance_min = 0.005


def paint_weight_map(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    props.paint_store_render = bpy.context.space_data.shading.type

    if bpy.context.mode != "PAINT_TEXTURE":
        bpy.ops.object.mode_set(mode="TEXTURE_PAINT")

    if bpy.context.mode == "PAINT_TEXTURE":
        weight_map = get_weight_map_image(obj, mat)
        props.paint_object = obj
        props.paint_material = mat
        props.paint_image = weight_map
        if weight_map is not None:
            bpy.context.scene.tool_settings.image_paint.mode = 'IMAGE'
            bpy.context.scene.tool_settings.image_paint.canvas = weight_map
            bpy.context.space_data.shading.type = 'SOLID'


def has_dirty_weightmaps(objects):
    for obj in objects:
        if obj.type == "MESH":
            for mod in obj.modifiers:
                if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name:
                    if mod.mask_texture is not None and mod.mask_texture.image is not None:
                        image = mod.mask_texture.image
                        if image.is_dirty:
                            return True
    return False


def get_dirty_weightmaps(objects):
    maps = []
    for obj in objects:
        if obj.type == "MESH":
            for mod in obj.modifiers:
                if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name:
                    if mod.mask_texture is not None and mod.mask_texture.image is not None:
                        image = mod.mask_texture.image
                        if image.is_dirty:
                            maps.append(image)
    return maps


def stop_paint():
    props = bpy.context.scene.CC3ImportProps

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.space_data.shading.type = props.paint_store_render

    props.paint_image.pack()
    props.paint_image.save()


def save_temp_weight_maps():
    """Saves all active temporary weight map images to their respective material folders.

    Clears active temporary weight maps from material cache.
    """

    props = bpy.context.scene.CC3ImportProps
    for mat_cache in props.material_cache:
        obj_cache = get_object_cache(mat_cache.object)
        if (mat_cache.temp_weight_map is not None
            and obj_cache.cloth_physics != "OFF"
            and mat_cache.cloth_physics != "OFF"):

            log_info("Temporary weight map: " + mat_cache.temp_weight_map.name)
            dir = mat_cache.dir
            name = strip_name(mat_cache.material.name)
            filepath = os.path.join(dir, name + "_WeightMap.png")
            log_info("    Saved to: " + filepath)
            mat_cache.temp_weight_map.filepath = filepath
            mat_cache.temp_weight_map.save()
            mat_cache.temp_weight_map = None


def save_dirty_weight_maps(objects):
    """Saves all altered active weight map images to their respective material folders.
    """

    props = bpy.context.scene.CC3ImportProps

    maps = get_dirty_weightmaps(objects)

    for weight_map in maps:
        if weight_map.is_dirty:
            # Save all active temporary weight maps
            weight_map.save()
            log_info("Weight Map: " + weight_map.name + " saved to: " + weight_map.filepath)

