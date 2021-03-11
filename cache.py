import bpy

from .vars import *


class CC3MaterialCache(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(type=bpy.types.Material)
    compat: bpy.props.PointerProperty(type=bpy.types.Material)
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    dir: bpy.props.StringProperty(default="")
    diffuse: bpy.props.PointerProperty(type=bpy.types.Image)
    normal: bpy.props.PointerProperty(type=bpy.types.Image)
    bump: bpy.props.PointerProperty(type=bpy.types.Image)
    alpha: bpy.props.PointerProperty(type=bpy.types.Image)
    specular: bpy.props.PointerProperty(type=bpy.types.Image)
    temp_weight_map: bpy.props.PointerProperty(type=bpy.types.Image)
    alpha_is_diffuse: bpy.props.BoolProperty(default=False)
    alpha_mode: bpy.props.StringProperty(default="NONE") # NONE, BLEND, HASHED, OPAQUE
    culling_sides: bpy.props.IntProperty(default=0) # 0 - default, 1 - single sided, 2 - double sided
    # bit of a misnomer, this means enabled/disabled weight maps.
    cloth_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON


class CC3ObjectCache(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    collision_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON
    cloth_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON
    cloth_settings: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, HAIR, COTTON, DENIM, LEATHER, RUBBER, SILK


def get_object_cache(obj):
    """Returns the object cache for this object.

    Fetches or creates an object cache for the object. Always returns an object cache collection.
    """

    props = bpy.context.scene.CC3ImportProps
    for cache in props.object_cache:
        if cache.object == obj:
            return cache
    cache = props.object_cache.add()
    cache.object = obj
    return cache


def get_material_cache(mat):
    """Returns the material cache for this material.

    Fetches the material cache for the material. Returns None if the material is not in the cache.
    """

    props = bpy.context.scene.CC3ImportProps
    for cache in props.material_cache:
        if cache.material == mat:
            return cache
    return None
