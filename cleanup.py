import bpy

from .utils import *
from .vars import *


def delete_character_object(obj):
    if obj is None:
        return

    for child in obj.children:
        delete_character_object(child)

    # remove any armature actions
    if obj.type == "ARMATURE":
        if obj.animation_data is not None:
            if obj.animation_data.action is not None:
                bpy.data.actions.remove(obj.animation_data.action)

    # remove any shape key actions and remove the shape keys
    if obj.type == "MESH":
        if obj.data.shape_keys is not None:
            if obj.data.shape_keys.animation_data is not None:
                if obj.data.shape_keys.animation_data.action is not None:
                    bpy.data.actions.remove(obj.data.shape_keys.animation_data.action)
        obj.shape_key_clear()

        # remove materials->nodes->images
        for mat in obj.data.materials:
            if mat.node_tree is not None:
                nodes = mat.node_tree.nodes
                for node in nodes:
                    if node.type == "TEX_IMAGE" and node.image is not None:
                        image = node.image
                        bpy.data.images.remove(image)
                    nodes.remove(node)
            bpy.data.materials.remove(mat)

    if obj.type == "ARMATURE":
        bpy.data.armatures.remove(obj.data)
    else:
        bpy.data.objects.remove(obj)

    #except:
    #    log_error("Something went wrong deleting object...")

def delete_character():
    props = bpy.context.scene.CC3ImportProps

    for p in props.import_objects:
        delete_character_object(p.object)

    props.import_objects.clear()
    props.import_file = ""
    props.import_type = ""
    props.import_name = ""
    props.import_dir = ""
    props.import_main_tex_dir = ""
    props.import_space_in_name = False
    props.import_embedded = False
    props.import_haskey = ""
    props.import_key_file = ""
    props.material_cache.clear()
    props.object_cache.clear()

    clean_colletion(bpy.data.materials)
    clean_colletion(bpy.data.images)
    clean_colletion(bpy.data.meshes)
    clean_colletion(bpy.data.node_groups)

