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
import re
import os

from . import (materials, modifiers, meshutils, geom, bones, physics, rigutils,
               shaders, basic, imageutils, nodeutils, jsonutils, utils, vars)

from mathutils import Vector, Matrix, Quaternion

MANDATORY_OBJECTS = ["BODY", "TEETH", "TONGUE", "TEARLINE", "OCCLUSION", "EYE"]


def get_character_objects(arm):
    """Fetch all the objects in the character (or try to)"""
    objects = []
    if arm.type == "ARMATURE":
        objects.append(arm)
        for obj in arm.children:
            if utils.object_exists_is_mesh(obj):
                if obj not in objects:
                    objects.append(obj)
    return objects


def get_generic_rig(objects):
    props = bpy.context.scene.CC3ImportProps
    arm = utils.get_armature_from_objects(objects)
    if arm:
        chr_cache = props.get_character_cache(arm, None)
        if not chr_cache:
            return arm
    return None


def make_prop_armature(objects):

    utils.set_mode("OBJECT")

    # find the all the root empties and determine if there is one single root
    roots = []
    single_empty_root = None
    for obj in objects:

        # reset all transforms
        #bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # find single root
        if obj.parent is None or obj.parent not in objects:
            if obj.type == "EMPTY":
                roots.append(obj)
                single_empty_root = obj
                if len(roots) > 1:
                    single_empty_root = False
                    single_empty_root = None
            else:
                single_empty_root = None

    arm_name = "Prop"
    if single_empty_root:
        arm_name = single_empty_root.name

    arm_data = bpy.data.armatures.new(arm_name)
    arm = bpy.data.objects.new(arm_name, arm_data)
    bpy.context.collection.objects.link(arm)
    if single_empty_root:
        arm.location = utils.object_world_location(single_empty_root)
    utils.clear_selected_objects()

    root_bone : bpy.types.EditBone = None
    bone : bpy.types.EditBone = None
    root_bone_name = None
    tail_vector = Vector((0,0,0.1))
    tail_translate = Matrix.Translation(-tail_vector)

    if utils.edit_mode_to(arm):

        if single_empty_root:
            root_bone = arm.data.edit_bones.new(single_empty_root.name)
            root_bone.head = arm.matrix_local @ utils.object_world_location(single_empty_root)
            root_bone.tail = arm.matrix_local @ utils.object_world_location(single_empty_root, tail_vector)
            root_bone.roll = 0
            root_bone_name = root_bone.name
        else:
            root_bone = arm.data.edit_bones.new("Root")
            root_bone.head = Vector((0,0,0))
            root_bone.tail = Vector((0,0,0)) + tail_vector
            root_bone.roll = 0
            root_bone_name = root_bone.name

        for obj in objects:
            if obj.type == "EMPTY" and obj.name not in arm.data.edit_bones:
                bone = arm.data.edit_bones.new(obj.name)
                bone.head = arm.matrix_local @ utils.object_world_location(obj)
                bone.tail = arm.matrix_local @ utils.object_world_location(obj, tail_vector)

        for obj in objects:
            if obj.type == "EMPTY" and obj.parent:
                bone = arm.data.edit_bones[obj.name]
                if obj.parent.name in arm.data.edit_bones:
                    parent = arm.data.edit_bones[obj.parent.name]
                    bone.parent = parent
                elif bone != bone.parent:
                    bone.parent = root_bone
                else:
                    bone.parent = None

    utils.object_mode_to(arm)

    obj : bpy.types.Object
    for obj in objects:
        if obj.type == "MESH":
            if obj.parent and obj.parent.name in arm.data.bones:
                parent_name = obj.parent.name
                parent_bone : bpy.types.Bone = arm.data.bones[parent_name]
                omw = obj.matrix_world.copy()
                obj.parent = arm
                obj.parent_type = 'BONE'
                obj.parent_bone = parent_name
                # by re-applying (a copy of) the original matrix_world, blender
                # works out the correct parent inverse transforms from the bone
                obj.matrix_world = omw
            elif root_bone_name:
                parent_bone = arm.data.bones[root_bone_name]
                omw = obj.matrix_world.copy()
                obj.parent = arm
                obj.parent_type = 'BONE'
                obj.parent_bone = root_bone_name
                # by re-applying (a copy of) the original matrix_world, blender
                # works out the correct parent inverse transforms from the bone
                obj.matrix_world = omw

    # remove the empties and move all objects into the same collection as the armature
    collections = utils.get_object_scene_collections(arm)
    for obj in objects:
        if obj.type == "EMPTY":
            bpy.data.objects.remove(obj)
        else:
            utils.move_object_to_scene_collections(obj, collections)

    # finally force the armature name again (as it may have been taken by the original object)
    arm.name = arm_name

    return arm


def create_prop_rig(objects):
    arm_name = "Prop"
    bone_name = "Root"
    utils.set_mode("OBJECT")

    arm = make_prop_armature(objects)

    #utils.try_select_objects(objects, True)
    #utils.set_active_object(arm)
    #bpy.ops.object.parent_set(type = "ARMATURE", keep_transform = True)
    #obj : bpy.types.Object
    #for obj in objects:
    #    if obj.type == "MESH":
    #        vg = meshutils.add_vertex_group(obj, bone_name)
    #        meshutils.set_vertex_group(obj, vg, 1.0)
    return arm


def convert_generic_to_non_standard(objects, file_path = None):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    non_chr_objects = [ obj for obj in objects if props.get_object_cache(obj, strict=True) is None ]

    # select all child objects of the current selected objects (Humanoid)
    utils.try_select_objects(non_chr_objects, True)
    for obj in non_chr_objects:
        utils.try_select_child_objects(obj)

    objects = bpy.context.selected_objects

    # try to find a character armature
    chr_rig = utils.get_armature_from_objects(objects)
    chr_type = "HUMANOID"

    # if not generate one from the objects and empty parent transforms (Prop Only)
    if not chr_rig:
        chr_rig = create_prop_rig(objects)
        chr_type = "PROP"

    if not chr_rig:
        return None

    # now treat the armature as any generic character
    objects = get_character_objects(chr_rig)

    utils.log_info("")
    utils.log_info("Detecting Generic Character:")
    utils.log_info("----------------------------")

    ext = ".fbx"
    if file_path:
        dir, file = os.path.split(file_path)
        name, ext = os.path.splitext(file)
        chr_rig.name = utils.unique_object_name(name, chr_rig)
        full_name = chr_rig.name
    else:
        full_name = chr_rig.name
        name = utils.strip_name(full_name)
        dir = ""

    chr_cache = props.import_cache.add()
    chr_cache.import_file = ""
    chr_cache.character_name = full_name
    chr_cache.import_embedded = False
    chr_cache.generation = "Unknown"
    chr_cache.non_standard_type = chr_type

    chr_cache.add_object_cache(chr_rig)

    # add child objects to chr_cache
    for obj in objects:
        if utils.object_exists_is_mesh(obj):
            add_object_to_character(chr_cache, obj, reparent=False)

    return chr_cache


def link_or_append_rl_character(blend_file, link=False):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    utils.log_info("")
    utils.log_info("Link/Append Reallusion Character")
    utils.log_info("--------------------------------")

    # link or append character data from blend file
    with bpy.data.libraries.load(blend_file, link=link) as (src, dst):
        dst.scenes = src.scenes
        dst.objects = src.objects

    ignore = []
    keep = []

    # find the add-on character data in the blend file
    src_props = None
    for scene in dst.scenes:
        if "CC3ImportProps" in scene:
            src_props = scene.CC3ImportProps
            utils.log_info(f"Found Add-on Import Properties")
            break

    if src_props:

        for src_cache in src_props.import_cache:

            character_name = src_cache.character_name
            import_file = src_cache.import_file
            chr_rig = src_cache.get_armature()
            meta_rig = src_cache.rig_meta_rig
            src_rig = src_cache.rig_original_rig
            widgets = []
            objects = []

            utils.log_info(f"Character Data Found: {character_name}")

            # keep the character rig
            utils.log_info(f"Character rig: {chr_rig.name}")
            keep.append(chr_rig)
            objects.append(chr_rig)

            # keep the meta rig
            if meta_rig:
                utils.log_info(f"Meta-rig: {chr_rig.name}")
                keep.append(meta_rig)
                objects.append(meta_rig)

            # ignore the source rig
            if src_rig:
                ignore.append(src_rig)

            # keep all child objects of the rigify rig
            for obj in dst.objects:
                if obj in chr_rig.children:
                    utils.log_info(f" - Character Object: {obj.name}")
                    keep.append(obj)
                    objects.append(obj)

            # find the widgets
            widget_prefix = f"WGT-{character_name}_rig"
            widget_collection_name = f"WGT_{character_name}_rig"
            for obj in dst.objects:
                if obj.name.startswith(widget_prefix):
                    keep.append(obj)
                    widgets.append(obj)

            # TODO remove all actions or keep them? or get all of them?

            # put all the character objects in the character collection
            character_collection = utils.create_collection(character_name)
            for obj in objects:
                character_collection.objects.link(obj)

            # put the widgets in the widget sub-collection
            if widgets:
                widget_collection = utils.create_collection(widget_collection_name,
                                                            existing=False,
                                                            parent_collection=character_collection)
                for widget in widgets:
                    widget_collection.objects.link(widget)
                    widget.hide_set(True)

                # hide the widget sub-collection
                lc = utils.find_layer_collection(widget_collection.name)
                lc.exclude = True

            # hide the meta rig
            if meta_rig:
                meta_rig.hide_set(True)

            # create the character cache and rebuild from the source data
            chr_cache = props.add_character_cache(copy_from=src_cache)
            rebuild_character_cache(chr_cache, chr_rig, src_cache)

    # clean up unused objects
    for obj in dst.objects:
        if obj not in keep:
            utils.delete_object(obj)


def reconnect_rl_character_to_fbx(chr_rig, fbx_path):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    objects = get_character_objects(chr_rig)

    utils.log_info("")
    utils.log_info("Re-connecting Character to Source FBX")
    utils.log_info("-------------------------------------")

    chr_cache = props.add_character_cache()

    rig_name = chr_rig.name
    character_name = rig_name
    if character_name.endswith("_Rigify"):
        character_name = rig_name[:-7]

    utils.log_info(f"Using character name: {character_name}")

    if "rl_generation" in chr_rig:
        generation = chr_rig["rl_generation"]
    else:
        generation = rigutils.get_rig_generation(chr_rig)

    meta_rig_name = character_name + "_metarig"
    meta_rig = None
    if meta_rig_name in bpy.data.objects:
        if utils.object_exists_is_armature(bpy.data.objects[meta_rig_name]):
            meta_rig = bpy.data.objects[meta_rig_name]

    chr_cache.import_file = fbx_path
    chr_cache.character_name = character_name
    chr_cache.import_embedded = False
    chr_cache.generation = generation
    chr_cache.non_standard_type = "HUMANOID"
    chr_cache.rigified = True
    chr_cache.rig_meta_rig = meta_rig
    chr_cache.rigified_full_face_rig = character_has_bones(chr_rig, ["nose", "lip.T", "lip.B"])
    chr_cache.add_object_cache(chr_rig)

    rebuild_character_cache(chr_cache, chr_rig)

    return chr_cache


def reconnect_rl_character_to_blend(chr_rig, blend_file):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    objects = get_character_objects(chr_rig)

    utils.log_info("")
    utils.log_info("Re-connecting Character to Blend File:")
    utils.log_info("--------------------------------------")

    rig_name = chr_rig.name
    character_name = rig_name
    if character_name.endswith("_Rigify"):
        character_name = rig_name[:-7]
    utils.log_info(f"Using character name: {character_name}")

    # link or append character data from blend file
    with bpy.data.libraries.load(blend_file) as (src, dst):
        dst.scenes = src.scenes

    # find the add-on character data in the blend file
    src_props = None
    src_cache = None
    for scene in dst.scenes:
        if "CC3ImportProps" in scene:
            src_props = scene.CC3ImportProps
            utils.log_info(f"Found Add-on Import Properties")
            break

    if src_props:

        # try to find the source cache by import file
        if "rl_import_file" in chr_rig:
            import_file = chr_rig["rl_import_file"]
            for chr_cache in src_props.import_cache:
                if chr_cache.import_file == import_file:
                    utils.log_info(f"Found matching source character fbx: {chr_cache.character_name}")
                    src_cache = chr_cache
                    break

        # try to find the source cache by character name
        for chr_cache in src_props.import_cache:
            if chr_cache.character_name == character_name:
                utils.log_info(f"Found matching source character name: {chr_cache.character_name}")
                src_cache = chr_cache
                break

    if src_cache:

        # create the character cache and rebuild from the source data
        chr_cache = props.add_character_cache(copy_from=src_cache)
        # can't match objects accurately, so don't try (as they are no longer the same linked objects)
        rebuild_character_cache(chr_cache, chr_rig, src_cache=src_cache)
        return chr_cache

    return None


def rebuild_character_cache(chr_cache, chr_rig, src_cache=None):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    chr_cache.add_object_cache(chr_rig)
    objects = get_character_objects(chr_rig)

    utils.log_info("")
    utils.log_info("Re-building Character Cache:")
    utils.log_info("----------------------------")

    errors = []
    json_data = jsonutils.read_json(chr_cache.import_file, errors)
    chr_json = jsonutils.get_character_json(json_data, chr_cache.get_character_id())

    # add child objects to chr_cache
    processed = []
    defaults = []
    for obj in objects:
        obj_id = obj["rl_object_id"] if "rl_object_id" in obj else None
        if utils.object_exists_is_mesh(obj) and obj not in processed:
            processed.append(obj)
            src_obj_cache = src_cache.get_object_cache(obj, by_id=obj_id) if src_cache else None
            utils.log_info(f"Object: {obj.name} {obj_id} {src_obj_cache}")
            obj_json = jsonutils.get_object_json(chr_json, obj)
            obj_cache = chr_cache.add_object_cache(obj, copy_from=src_obj_cache)
            for mat in obj.data.materials:
                if mat and mat.node_tree is not None:
                    mat_id = mat["rl_material_id"] if "rl_material_id" in mat else None
                    src_mat_cache = src_cache.get_material_cache(mat, by_id=mat_id) if src_cache else None
                    utils.log_info(f"Material: {mat.name} {mat_id} {src_mat_cache}")
                    if src_obj_cache and src_mat_cache:
                        object_type = src_obj_cache.object_type
                        material_type = src_mat_cache.material_type
                    elif "rl_object_type" in obj and "rl_material_type" in mat:
                        object_type = obj["rl_object_type"]
                        material_type = mat["rl_material_type"]
                    else:
                        object_type, material_type = materials.detect_materials(chr_cache, obj, mat, obj_json)
                    if obj_cache.object_type != "BODY":
                        obj_cache.set_object_type(object_type)
                    if mat not in processed:
                        mat_cache = chr_cache.add_material_cache(mat, material_type, copy_from=src_mat_cache)
                        mat_cache.dir = imageutils.get_material_tex_dir(chr_cache, obj, mat)
                        physics.detect_physics(chr_cache, obj, obj_cache, mat, mat_cache, chr_json)
                        processed.append(mat)
                    if not src_obj_cache or not src_mat_cache:
                        defaults.append(mat)

    # re-initialize the shader parameters (if not copied over)
    if defaults:
        shaders.init_character_property_defaults(chr_cache, chr_json, only=defaults)
    if not src_cache:
        basic.init_basic_default(chr_cache)

    return chr_cache


def parent_to_rig(rig, obj):
    """For if the object is not parented to the rig and/or does not have an armature modifier set to the rig.
    """

    if rig and obj and rig.type == "ARMATURE" and obj.type == "MESH":

        if obj.parent != rig:

            # clear any parenting
            if obj.parent:
                if utils.set_active_object(obj):
                        bpy.ops.object.parent_clear(type = "CLEAR_KEEP_TRANSFORM")

            # parent to rig
            if rig:
                if utils.try_select_objects([rig, obj]):
                    if utils.set_active_object(rig):
                        bpy.ops.object.parent_set(type = "OBJECT", keep_transform = True)

        # add or update armature modifier
        arm_mod = modifiers.get_object_modifier(obj, "ARMATURE")
        if not arm_mod:
            arm_mod: bpy.types.ArmatureModifier = modifiers.get_armature_modifier(obj, create=True, armature=rig)
            modifiers.move_mod_first(obj, arm_mod)

        # update armature modifier rig
        if arm_mod and arm_mod.object != rig:
            arm_mod.object = rig

        utils.clear_selected_objects()
        utils.set_active_object(obj)


def add_object_to_character(chr_cache, obj : bpy.types.Object, reparent=True, no_materials=False):
    props = bpy.context.scene.CC3ImportProps

    if chr_cache and utils.object_exists_is_mesh(obj):

        obj_cache = chr_cache.get_object_cache(obj)

        if not obj_cache:

            # convert the object name to remove any duplicate suffixes:
            obj_name = utils.unique_object_name(obj.name, obj)
            if obj.name != obj_name:
                obj.name = obj_name

            # add the object into the object cache
            obj_cache = chr_cache.add_object_cache(obj)
            if "rl_object_type" in obj:
                obj_cache.set_object_type(obj["rl_object_type"])
            else:
                obj_cache.set_object_type("DEFAULT")
            obj_cache.user_added = True

        obj_cache.disabled = False

        if not no_materials:
            add_missing_materials_to_character(chr_cache, obj, obj_cache)

        utils.clear_selected_objects()

        if reparent:
            arm = chr_cache.get_armature()
            if arm:
                parent_to_rig(arm, obj)


def remove_object_from_character(chr_cache, obj):
    props = bpy.context.scene.CC3ImportProps

    if utils.object_exists_is_mesh(obj):

        obj_cache = chr_cache.get_object_cache(obj)

        if obj_cache and obj_cache.object_type not in MANDATORY_OBJECTS:

            obj_cache.disabled = True

            # unparent from character
            arm = chr_cache.get_armature()
            if arm:
                if utils.try_select_objects([arm, obj]):
                    if utils.set_active_object(arm):
                        bpy.ops.object.parent_clear(type = "CLEAR_KEEP_TRANSFORM")

                        # remove armature modifier
                        arm_mod : bpy.types.ArmatureModifier = modifiers.get_object_modifier(obj, "ARMATURE")
                        if arm_mod:
                            obj.modifiers.remove(arm_mod)

                        #obj.hide_set(True)

                        utils.clear_selected_objects()
                        # don't reselect the removed object as this may cause
                        # onfusion when using checking function immediately after...
                        #utils.set_active_object(obj)


def copy_objects_character_to_character(context_obj, chr_cache, objects, reparent = True):
    props = bpy.context.scene.CC3ImportProps

    arm = chr_cache.get_armature()
    if not arm:
        return

    context_collections = utils.get_object_scene_collections(context_obj)

    to_copy = {}
    for obj in objects:
        if utils.object_exists_is_mesh(obj):
            cc = props.get_character_cache(obj, None)
            if cc != chr_cache:
                if cc not in to_copy:
                    to_copy[cc] = []
                to_copy[cc].append(obj)

    copied_objects = []

    for cc in to_copy:
        for o in to_copy[cc]:
            oc = cc.get_object_cache(o)

            # copy object
            obj = utils.duplicate_object(o)
            utils.move_object_to_scene_collections(obj, context_collections)
            copied_objects.append(obj)

            # convert the object name to remove any duplicate suffixes:
            obj_name = utils.unique_object_name(obj.name, obj)
            if obj.name != obj_name:
                obj.name = obj_name

            # add the object into the object cache
            obj_cache = chr_cache.add_object_cache(obj, copy_from=oc, user=True)
            obj_cache.user_added = True
            obj_cache.disabled = False

            add_missing_materials_to_character(chr_cache, obj, obj_cache)

            if reparent:
                parent_to_rig(arm, obj)

    utils.clear_selected_objects()
    utils.try_select_objects(copied_objects, make_active=True)


def get_accessory_root(chr_cache, object):
    """Accessories can be identified by them having only vertex groups not listed in the bone mappings for this generation."""

    if not chr_cache or not object:
        return None

    # none of this works if rigified...
    if chr_cache.rigified:
        return None

    if not chr_cache or not object or not utils.object_exists_is_mesh(object):
        return None

    rig = chr_cache.get_armature()
    bone_mapping = chr_cache.get_rig_bone_mapping()

    if not rig or not bone_mapping:
        return None

    accessory_root = None

    # accessories can be identified by them having only vertex groups not listed in the bone mappings for this generation.
    for vg in object.vertex_groups:

        # if even one vertex groups belongs to the character bones, it will not import into cc4 as an accessory
        if bones.bone_mapping_contains_bone(bone_mapping, vg.name):
            return None

        else:
            bone = bones.get_bone(rig, vg.name)
            if bone:
                root = bones.get_accessory_root_bone(bone_mapping, bone)
                if root:
                    accessory_root = root

    return accessory_root


def make_accessory(chr_cache, objects):

    rig = chr_cache.get_armature()

    # store parent objects (as the parenting is destroyed when adding objects to character)
    obj_data = {}
    for obj in objects:
        if obj.type == "MESH":
            obj_data[obj] = {}
            obj_data[obj]["parent_object"] = obj.parent

    # add any non character objects to character
    for obj in objects:
        obj_cache = chr_cache.get_object_cache(obj)
        if not obj_cache:
            utils.log_info(f"Adding {obj.name} to character.")
            add_object_to_character(chr_cache, obj, True)
            obj_cache = chr_cache.get_object_cache(obj)
        else:
            parent_to_rig(rig, obj)

    cursor_pos = bpy.context.scene.cursor.location
    if utils.try_select_objects(objects, True, "MESH", True):
        if utils.set_mode("EDIT"):
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.view3d.snap_cursor_to_selected()

            if rig and utils.edit_mode_to(rig, only_this = True):

                # add accessory named bone to rig
                accessory_root = rig.data.edit_bones.new("Accessory")
                root_head = rig.matrix_world.inverted() @ bpy.context.scene.cursor.location
                root_tail = rig.matrix_world.inverted() @ (bpy.context.scene.cursor.location + Vector((0, 1/4, 0)))
                piv_tail = rig.matrix_world.inverted() @ (bpy.context.scene.cursor.location + Vector((0, 1/10000, 0)))
                utils.log_info(f"Adding accessory root bone: {accessory_root.name}/({root_head})")
                accessory_root.head = root_head
                accessory_root.tail = root_tail

                default_parent = bones.get_rl_edit_bone(rig, chr_cache.accessory_parent_bone)
                accessory_root.parent = default_parent

                for obj in objects:
                    if obj.type == "MESH":

                        # add object bone to rig
                        obj_bone = rig.data.edit_bones.new(obj.name)
                        obj_head = rig.matrix_world.inverted() @ (obj.matrix_world @ Vector((0, 0, 0)))
                        obj_tail = rig.matrix_world.inverted() @ ((obj.matrix_world @ Vector((0, 0, 0))) + Vector((0, 1/8, 0)))
                        utils.log_info(f"Adding object bone: {obj_bone.name}/({obj_head})")
                        obj_bone.head = obj_head
                        obj_bone.tail = obj_tail

                        # add pivot bone to rig
                        #piv_bone = rig.data.edit_bones.new("CC_Base_Pivot")
                        #utils.log_info(f"Adding pivot bone: {piv_bone.name}/({root_head})")
                        #piv_bone.head = root_head + Vector((0, 1/100, 0))
                        #piv_bone.tail = piv_tail + Vector((0, 1/100, 0))
                        #piv_bone.parent = obj_bone

                        # add deformation bone to rig
                        def_bone = rig.data.edit_bones.new(obj.name)
                        utils.log_info(f"Adding deformation bone: {def_bone.name}/({obj_head})")
                        def_head = rig.matrix_world.inverted() @ ((obj.matrix_world @ Vector((0, 0, 0))) + Vector((0, 1/32, 0)))
                        def_tail = rig.matrix_world.inverted() @ ((obj.matrix_world @ Vector((0, 0, 0))) + Vector((0, 1/32 + 1/16, 0)))
                        def_bone.head = def_head
                        def_bone.tail = def_tail
                        def_bone.parent = obj_bone

                        # remove all vertex groups from object
                        obj.vertex_groups.clear()

                        # add vertex groups for object bone
                        vg = meshutils.add_vertex_group(obj, def_bone.name)
                        meshutils.set_vertex_group(obj, vg, 1.0)

                        obj_data[obj]["bone"] = obj_bone
                        obj_data[obj]["def_bone"] = def_bone

                utils.object_mode_to(rig)

                # parent the object bone to the accessory bone (or object transform parent bone)
                for obj in objects:
                    if obj.type == "MESH" and obj in obj_data.keys():
                        # fetch the object's bone
                        obj_bone = obj_data[obj]["bone"]
                        # find the parent bone to the object (if exists)
                        parent_bone = None
                        obj_parent = obj_data[obj]["parent_object"]
                        if obj_parent and obj_parent in obj_data.keys():
                            parent_bone = obj_data[obj_parent]["bone"]
                        # parent the bone
                        if parent_bone:
                            utils.log_info(f"Parenting {obj.name} to {parent_bone.name}")
                            obj_bone.parent = parent_bone
                        else:
                            utils.log_info(f"Parenting {obj.name} to {accessory_root.name}")
                            obj_bone.parent = accessory_root

        # object mode to save new bones
        utils.set_mode("OBJECT")


    bpy.context.scene.cursor.location = cursor_pos


    return



def clean_up_character_data(chr_cache):

    props = bpy.context.scene.CC3ImportProps

    current_mats = []
    current_objects = []
    arm = chr_cache.get_armature()
    report = []

    if arm:

        for obj in arm.children:
            if utils.object_exists_is_mesh(obj):
                current_objects.append(obj)
                for mat in obj.data.materials:
                    if mat and mat not in current_mats:
                        current_mats.append(mat)

        delete_objects = []
        unparented_objects = []
        unparented_materials = []

        for obj_cache in chr_cache.object_cache:

            obj = obj_cache.get_object()

            if not obj_cache.is_valid():
                    delete_objects.append(obj_cache.get_object(return_invalid = True))

            elif obj != arm:

                if obj_cache.is_mesh():

                    # be sure not to delete object and material cache data for objects still existing in the scene,
                    # but not currently attached to the character
                    if obj not in current_objects:
                        unparented_objects.append(obj)
                        utils.log_info(f"Keeping unparented Object data: {obj.name}")
                        for mat in obj.data.materials:
                            if mat and mat not in unparented_materials:
                                unparented_materials.append(mat)
                                utils.log_info(f"Keeping unparented Material data: {mat.name}")

                else:

                    # add any invalid cached objects to the delete list
                    delete_objects.append(obj)

        for obj in delete_objects:
            if obj and obj not in unparented_objects:
                report.append(f"Removing deleted/invalid Object from cache data.")
                chr_cache.remove_object_cache(obj)

        cache_mats = chr_cache.get_all_materials()
        delete_mats = []

        for mat in cache_mats:
            if mat and mat not in current_mats:
                delete_mats.append(mat)

        for mat in delete_mats:
            if mat not in unparented_materials:
                report.append(f"Removing Material: {mat.name} from cache data.")
                chr_cache.remove_mat_cache(mat)

        if len(report) > 0:
            utils.message_box_multi("Cleanup Report", "INFO", report)
        else:
            utils.message_box("Nothing to clean up.", "Cleanup Report", "INFO")


def has_missing_materials(chr_cache):
    missing_materials = False
    if chr_cache:
        for obj_cache in chr_cache.object_cache:
            obj = obj_cache.get_mesh()
            if obj and not chr_cache.has_all_materials(obj.data.materials):
                missing_materials = True
    return missing_materials


def add_missing_materials_to_character(chr_cache, obj, obj_cache):
    props  = bpy.context.scene.CC3ImportProps

    if chr_cache and obj and obj_cache and obj.type == "MESH":

        obj_name = obj.name

        # add a default material if none exists...
        if len(obj.data.materials) == 0:
            mat_name = utils.unique_material_name(obj_name)
            mat = bpy.data.materials.new(mat_name)
            obj.data.materials.append(mat)

        for mat in obj.data.materials:
            if mat:
                mat_cache = chr_cache.get_material_cache(mat)

                if not mat_cache:
                    add_material_to_character(chr_cache, obj, obj_cache, mat, update_name=True)


def add_material_to_character(chr_cache, obj, obj_cache, mat, update_name = False):
    props = bpy.context.scene.CC3ImportProps

    if chr_cache and obj and obj_cache and mat:

        # find existing cache in character
        mat_cache = chr_cache.get_material_cache(mat)
        if mat_cache:
            return mat_cache

        # find existing cache in any other character
        existing_mat_cache = props.get_material_cache(mat)
        if existing_mat_cache:
            # copy it
            mat_cache = chr_cache.add_material_cache(mat, copy_from=existing_mat_cache)
            return mat_cache

        if materials.is_rl_material(mat):
            mat_cache = materials.reconstruct_material_cache(chr_cache, mat)
            return mat_cache

        # convert the material name to remove any duplicate suffixes:
        if update_name:
            mat_name = utils.unique_material_name(mat.name, mat)
            if mat.name != mat_name:
                mat.name = mat_name

        # make sure there are nodes:
        if not mat.use_nodes:
            mat.use_nodes = True

        # add the material into the material cache
        mat_cache = chr_cache.add_material_cache(mat, "DEFAULT")
        mat_cache.user_added = True

        # convert any existing PrincipledBSDF based material to a rl_pbr shader material
        # can treat existing textures as embedded textures, so they will be picked up by the material builder.
        materials.detect_embedded_textures(chr_cache, obj, obj_cache, mat, mat_cache)
        # finally connect up the pbr shader...
        #shaders.connect_pbr_shader(obj, mat, None)
        convert_to_rl_pbr(mat, mat_cache)

        return mat_cache


def convert_to_rl_pbr(mat, mat_cache):
    shader_group = "rl_pbr_shader"
    shader_name = "rl_pbr_shader"
    shader_id = "(" + str(shader_name) + ")"
    bsdf_id = "(" + str(shader_name) + "_BSDF)"

    group_node: bpy.types.Node = None
    bsdf_node: bpy.types.Node = None
    output_node: bpy.types.Node = None
    gltf_node: bpy.types.Node = None
    too_complex = False

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    n : bpy.types.ShaderNode
    for n in nodes:

        if n.type == "BSDF_PRINCIPLED":

            if not bsdf_node:
                utils.log_info("Found BSDF: " + n.name)
                bsdf_node = n
            else:
                too_complex = True

        elif n.type == "GROUP" and n.node_tree and shader_name in n.name and vars.VERSION_STRING in n.node_tree.name:

            if not group_node:
                utils.log_info("Found Shader Node: " + n.name)
                group_node = n
            else:
                too_complex = True

        elif n.type == "GROUP" and n.node_tree and ("glTF Settings" in n.node_tree.name or
                                                    "glTF Material Output" in n.node_tree.name):
            if not gltf_node:
                gltf_node = n
                utils.log_info("GLTF settings node found: " + n.name)
            else:
                too_complex = True

        elif n.type == "OUTPUT_MATERIAL":

            if output_node:
                nodes.remove(n)
            else:
                output_node = n

    if too_complex:
        utils.log_warn(f"Material {mat.name} is too complex to convert!")
        return

    # move all the nodes back to accomodate the group shader node
    for n in nodes:
        loc = n.location
        n.location = [loc[0] - 600, loc[1]]

    # make group node if none
    # ensure correct names so find_shader_nodes can find them
    if not group_node:
        group = nodeutils.get_node_group(shader_group)
        group_node = nodes.new("ShaderNodeGroup")
        group_node.node_tree = group
    group_node.name = utils.unique_name(shader_id)
    group_node.label = "Pbr Shader"
    group_node.width = 240
    group_node.location = (-400, 0)

    # make bsdf node if none
    if not bsdf_node:
        bsdf_node = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_node.name = utils.unique_name(bsdf_id)
    bsdf_node.label = "Pbr Shader"
    bsdf_node.width = 240
    bsdf_node.location = (200, 400)

    # make output node if none
    if not output_node:
        output_node = nodes.new("ShaderNodeOutputMaterial")
    output_node.location = (900, -400)

    # remap bsdf socket inputs to shader group node sockets
    # [ [bsdf_socket_name<:parent_socket_name>, node_name_match, node_source, group_socket, strength_value_trace, prop_name], ]
    SOCKETS = [
        ["Base Color", "", "BSDF", "Diffuse Map", "", ""],
        ["Metallic", "", "BSDF", "Metallic Map", "", ""],
        ["Specular", "", "BSDF", "Specular Map", "", ""],
        ["Roughness", "", "BSDF", "Roughness Map", "", ""],
        ["Emission", "", "BSDF", "Emission Map", "", ""],
        ["Alpha", "", "BSDF", "Alpha Map", "", ""],
        ["Normal:Color", "", "BSDF", "Normal Map", "Normal:Strength", "default_normal_strength"], # normal image > normal map (Color) > BSDF (Normal)
        ["Normal:Normal:Color", "", "BSDF", "Normal Map", ["Normal:Normal:Strength", "Normal:Strength"], "default_normal_strength"], # normal image > normal map (Color) > bump map (Normal) > BSDF (Normal)
        ["Normal:Height", "", "BSDF", "Bump Map", ["Normal:Distance", "Normal:Strength"], "default_bump_strength"], # bump image > bump map (Height) > BSDF (Normal)
        ["Base Color:Color2", "ao|occlusion", "BSDF", "AO Map", "Base Color:Fac", "default_ao_strength"],
        ["Base Color:Color1", "ao|occlusion", "BSDF", "Diffuse Map", "", ""],
        #["Base Color:Color2", "#mixmultiply", "BSDF", "AO Map", "Base Color:Fac", "default_ao_strength"],
        #["Base Color:Color1", "#mixmultiply", "BSDF", "Diffuse Map", "", ""],
        # blender 3.0+
        #["Base Color:B", "#mixmultiply", "BSDF", "AO Map", "Base Color:Factor", "default_ao_strength"],
        #["Base Color:A", "#mixmultiply", "BSDF", "Diffuse Map", "", ""],
        ["Base Color:B", "ao|occlusion", "BSDF", "AO Map", "Base Color:Factor", "default_ao_strength"],
        ["Base Color:A", "ao|occlusion", "BSDF", "Diffuse Map", "", ""],
        # gltf
        ["Occlusion", "", "GLTF", "AO Map", "", ""],
        ["Occlusion:Color2", "", "GLTF", "AO Map", "Occlusion:Fac", "default_ao_strength"],
        ["Occlusion:B", "", "GLTF", "AO Map", "Occlusion:Factor", "default_ao_strength"],
    ]

    EMBEDDED = [
        ["DIFFUSE", "Diffuse Map"],
        ["SPECULAR", "Specular Map"],
        ["METALLIC", "Metallic Map"],
        ["ROUGHNESS", "Roughness Map"],
        ["EMISSION", "Emission Map"],
        ["ALPHA", "Alpha Map"],
        ["BUMP", "Bump Map"],
        ["NORMAL", "Normal Map"],
    ]

    if bsdf_node:

        try:

            base_color_socket = nodeutils.input_socket(bsdf_node, "Base Color")
            clearcoat_socket = nodeutils.input_socket(bsdf_node, "Clearcoat")
            roughness_socket = nodeutils.input_socket(bsdf_node, "Roughness")
            metallic_socket = nodeutils.input_socket(bsdf_node, "Metallic")
            specular_socket = nodeutils.input_socket(bsdf_node, "Specular")
            alpha_socket = nodeutils.input_socket(bsdf_node, "Alpha")
            emission_socket = nodeutils.input_socket(bsdf_node, "Emission")
            transmission_socket = nodeutils.input_socket(bsdf_node, "Transmission")
            emission_strength_socket = nodeutils.input_socket(bsdf_node, "Emission Strength")
            clearcoat_value = clearcoat_socket.default_value
            roughness_value = roughness_socket.default_value
            metallic_value = metallic_socket.default_value
            specular_value = specular_socket.default_value
            alpha_value = alpha_socket.default_value

            if gltf_node:
                # bug in Blender 4.0 gltf occlusion is not connected from occlusion strength node
                if utils.B400():
                    gltf_occlusion_socket = nodeutils.input_socket(gltf_node, "Occlusion")
                    occlusion_strength_node = nodeutils.find_node_by_type_and_keywords(nodes, "MIX", "Occlusion Strength")
                    if gltf_occlusion_socket and not gltf_occlusion_socket.is_linked:
                        nodeutils.link_nodes(links, occlusion_strength_node, "Result", gltf_node, gltf_occlusion_socket)

            if utils.B293():
                emission_value = nodeutils.get_node_input_value(bsdf_node, emission_strength_socket, 0.0)
            else:
                if emission_socket.is_linked:
                    emission_value = nodeutils.get_node_input_value(bsdf_node, emission_strength_socket, 1.0)
                else:
                    emission_value = 0.0
            emission_color = nodeutils.get_node_input_value(bsdf_node, emission_socket, (0,0,0))

            if not base_color_socket.is_linked:
                diffuse_color = base_color_socket.default_value
                mat_cache.parameters.default_diffuse_color = diffuse_color

            if transmission_socket.is_linked:
                nodeutils.unlink_node_input(links, bsdf_node, transmission_socket)

            mat_cache.parameters.default_roughness = roughness_value
            # a rough approximation for the clearcoat
            mat_cache.parameters.default_roughness_power = 1.0 + clearcoat_value
            mat_cache.parameters.default_metallic = metallic_value
            mat_cache.parameters.default_specular = specular_value
            mat_cache.parameters.default_emission_strength = emission_value / vars.EMISSION_SCALE
            mat_cache.parameters.default_emissive_color = emission_color
            if emission_strength_socket:
                emission_strength_socket.default_value = 1.0
            clearcoat_socket.default_value = 0.0
            if not alpha_socket.is_linked:
                mat_cache.parameters.default_opacity = alpha_value
        except:
            utils.log_warn("Unable to set material cache defaults!")

    socket_mapping = {}
    for socket_trace, match, node_type, group_socket, strength_trace, strength_prop in SOCKETS:
        if node_type == "BSDF":
            n = bsdf_node
        elif node_type == "GLTF":
            n = gltf_node
        else:
            n = None
        if n:
            linked_node, linked_socket = nodeutils.trace_input_sockets(n, socket_trace)
            linked_to = nodeutils.get_node_connected_to_output(linked_node, linked_socket)

            strength = 1.0
            if type(strength_trace) is list:
                for st in strength_trace:
                    strength *= float(nodeutils.trace_input_value(n, st, 1.0))
            else:
                strength = float(nodeutils.trace_input_value(n, strength_trace, 1.0))
            if group_socket == "Bump Map":
                strength = min(2, max(0, strength * 100.0))
            elif group_socket == "Normal Map":
                strength = min(2, max(0, strength))
            else:
                strength = min(1, max(0, strength))

            if linked_node and linked_socket:
                if match:
                    found = False
                    if match[0] == "#" and linked_to:
                        if match[1:] == "mixmultiply" and linked_to.type == "MIX" and linked_to.blend_type == "MULTIPLY":
                            found = True
                    else:
                        if re.match(match, linked_node.label) or re.match(match, linked_node.name):
                            found = True
                        elif linked_node.type == "TEX_IMAGE" and re.match(match, linked_node.image.name):
                            found = True
                    if found:
                        socket_mapping[group_socket] = [linked_node, linked_socket, strength, strength_prop]
                else:
                    socket_mapping[group_socket] = [linked_node, linked_socket, strength, strength_prop]

    for tex_type, group_socket in EMBEDDED:
        if group_socket not in socket_mapping:
            cache_mapping = mat_cache.get_texture_mapping(tex_type)
            if cache_mapping:
                linked_node = nodeutils.find_node_by_image(nodes, cache_mapping.image)
                socket = "Color"
                if tex_type == "ALPHA" and mat_cache.alpha_is_diffuse:
                    socket = "Alpha"
                socket_mapping[group_socket] = [linked_node, socket, 1.0, ""]

    # connect the shader group node sockets
    for socket_name in socket_mapping:
        linked_info = socket_mapping[socket_name]
        linked_node = linked_info[0]
        linked_socket = linked_info[1]
        strength = linked_info[2]
        strength_prop = linked_info[3]
        nodeutils.link_nodes(links, linked_node, linked_socket, group_node, socket_name)
        if strength_prop:
            utils.log_info(f"setting {strength_prop} = {strength}")
            shaders.exec_prop(strength_prop, mat_cache, strength)

    if bsdf_node and group_node and mat_cache:
        shaders.apply_prop_matrix(bsdf_node, group_node, mat_cache, "rl_pbr_shader")

    # connect all group_node outputs to BSDF inputs:
    for socket in group_node.outputs:
        to_socket = nodeutils.input_socket(bsdf_node, socket.name)
        nodeutils.link_nodes(links, group_node, socket.name, bsdf_node, to_socket)

    # connect bsdf to output node
    nodeutils.link_nodes(links, bsdf_node, "BSDF", output_node, "Surface")

    # connect the displacement to the output
    nodeutils.link_nodes(links, group_node, "Displacement", output_node, "Displacement")

    # use alpha hashing by default
    if mat.blend_method == "BLEND":
        mat.blend_method = "HASHED"
        mat.shadow_method = "HASHED"
        mat.use_backface_culling = False

    return


def character_has_bones(arm, bone_list: list):
    if not arm: return False
    if not bone_list: return False
    for bone_name in bone_list:
        if not utils.find_pose_bone_in_armature(arm, bone_name):
            return False
    return True


def character_has_materials(arm, material_list: list):
    if not arm: return False
    if not material_list: return False
    for material_name in material_list:
        material_name = material_name.lower()
        has_material = False
        for obj in arm.children:
            if utils.object_exists_is_mesh(obj):
                for mat in obj.data.materials:
                    mat_name = utils.strip_name(mat.name).lower()
                    if mat_name == material_name:
                        has_material = True
        if not has_material:
            return False
    return True


def get_character_material_names(arm):
    mat_names = []
    if arm:
        for obj in arm.children:
            if utils.object_exists_is_mesh(obj):
                for mat in obj.data.materials:
                    mat_name = utils.strip_name(mat.name)
                    if mat_name not in mat_names:
                        mat_names.append(mat_name)
    return mat_names


def get_character_object_names(arm):
    obj_names = []
    if arm:
        for obj in arm.children:
            if utils.object_exists_is_mesh(obj):
                obj_name = utils.strip_name(obj.name)
                if obj_name not in obj_names:
                    obj_names.append(obj_name)
    return obj_names


def transfer_skin_weights(chr_cache, objects):

    if not utils.set_mode("OBJECT"):
        return

    arm = chr_cache.get_armature()
    if arm is None:
        return

    body = None
    for obj_cache in chr_cache.object_cache:
        if obj_cache.object_type == "BODY":
            body = obj_cache.get_object()

    if not body:
        return

    if body in objects:
        objects.remove(body)

    if arm.data.pose_position == "POSE":

        # Transfer weights in place (in pose mode)

        # apply pose to the body mesh (copy)
        body_copy = utils.duplicate_object(body)
        body_copy.shape_key_clear()
        modifiers.apply_modifier(body_copy, type="ARMATURE")

        # apply pose to the object meshes (copies)
        objects_copy = []
        for obj in objects:
            obj_copy = utils.duplicate_object(obj)
            obj_copy.shape_key_clear()
            modifiers.apply_modifier(obj_copy, type="ARMATURE")
            objects_copy.append(obj_copy)

            # transfer weights from body_copy to obj_copy
            utils.set_only_active_object(obj_copy)
            utils.try_select_object(body_copy)
            bpy.ops.object.data_transfer(use_reverse_transfer=True,
                                         data_type='VGROUP_WEIGHTS',
                                         use_create=True,
                                         vert_mapping='POLYINTERP_NEAREST',
                                         use_object_transform=True,
                                         layers_select_src='NAME',
                                         layers_select_dst='ALL',
                                         mix_mode='REPLACE')
            #utils.set_mode("WEIGHT_PAINT")
            #bpy.ops.object.vertex_group_smooth(group_select_mode='ALL',
            #                                   factor=0.5, repeat=6, expand=0.5)
            #utils.set_mode("OBJECT")

        # make a copy of the armature and apply the current pose as the rest pose
        arm_posed = utils.duplicate_object(arm)
        utils.set_only_active_object(arm_posed)
        utils.pose_mode_to(arm_posed)
        bpy.ops.pose.armature_apply(selected=False)

        # parent all the copied meshes to the posed armature
        utils.try_select_object(body_copy, True)
        utils.try_select_objects(objects_copy)
        utils.set_active_object(arm_posed)
        bpy.ops.object.parent_set(type="OBJECT", keep_transform=True)
        # and add armature modifiers
        modifiers.get_armature_modifier(body_copy, create=True, armature=arm_posed)
        for obj_copy in objects_copy:
            modifiers.get_armature_modifier(obj_copy, create=True, armature=arm_posed)

        # make another copy of the armature and clear the pose
        arm_rest = utils.duplicate_object(arm)
        utils.set_only_active_object(arm_rest)
        utils.safe_set_action(arm_rest, None)
        utils.pose_mode_to(arm_rest)
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.transforms_clear()

        # constrain the pose on the posed armature to the rest pose on the rest armature
        # this poses the pose armature in the original bind pose
        utils.set_only_active_object(arm_posed)
        utils.pose_mode_to(arm_posed)
        for pose_bone in arm_posed.pose.bones:
            bones.add_copy_transforms_constraint(arm_rest, arm_posed, pose_bone.name, pose_bone.name)

        # then visually apply that pose
        # (this should pose the posed armature in the same pose as the original bind pose)
        # *not needed
        #utils.pose_mode_to(arm_posed)
        #bpy.ops.pose.select_all(action='SELECT')
        #bpy.ops.pose.visual_transform_apply()

        # now apply the armature modifiers on the copied meshes
        # so their base shape is now in the original bind pose
        utils.set_only_active_object(body_copy)
        modifiers.apply_modifier(body_copy, type="ARMATURE")
        for obj_copy in objects_copy:
            utils.set_only_active_object(obj_copy)
            modifiers.apply_modifier(obj_copy, type="ARMATURE")

        # parent the objects back to the original armature
        utils.try_select_object(body_copy, True)
        utils.try_select_objects(objects_copy)
        utils.set_active_object(arm)
        bpy.ops.object.parent_set(type="OBJECT", keep_transform=True)
        # and add armature modifiers
        modifiers.get_armature_modifier(body_copy, create=True, armature=arm)
        # copy the new vertex positions and weights back to the original objects
        for obj_copy in objects_copy:
            modifiers.get_armature_modifier(obj_copy, create=True, armature=arm)
            geom.copy_vertex_positions_and_weights(obj_copy, obj)

        # done!
        utils.delete_armature_object(arm_posed)
        utils.delete_armature_object(arm_rest)
        utils.delete_mesh_object(body_copy)
        for obj_copy in objects_copy:
            utils.delete_mesh_object(obj_copy)

    else:

        for obj in objects:
            if obj.type == "MESH":

                if utils.try_select_object(body, True) and utils.set_active_object(obj):

                    bpy.ops.object.data_transfer(use_reverse_transfer=True,
                                                data_type='VGROUP_WEIGHTS',
                                                use_create=True,
                                                vert_mapping='POLYINTERP_NEAREST',
                                                use_object_transform=True,
                                                layers_select_src='NAME',
                                                layers_select_dst='ALL',
                                                mix_mode='REPLACE')

                    if obj.parent != arm:
                        if utils.try_select_objects([arm, obj]) and utils.set_active_object(arm):
                            bpy.ops.object.parent_set(type = "OBJECT", keep_transform = True)

                    # add or update armature modifier
                    arm_mod : bpy.types.ArmatureModifier = modifiers.get_armature_modifier(obj, create=True, armature=arm)
                    if arm_mod:
                        modifiers.move_mod_first(obj, arm_mod)
                        arm_mod.object = arm


def normalize_skin_weights(chr_cache, objects):

    if not utils.set_mode("OBJECT"):
        return

    arm = chr_cache.get_armature()
    if arm is None:
        return

    body = None
    for obj_cache in chr_cache.object_cache:
        if obj_cache.object_type == "BODY":
            body = obj_cache.get_object()

    # don't allow normalize all to body mesh
    if body and body in objects:
        objects.remove(body)

    selected = bpy.context.selected_objects.copy()

    for obj in objects:
        if obj.type == "MESH":

            if utils.try_select_object(obj, True) and utils.set_active_object(obj):

                bpy.ops.object.vertex_group_normalize_all()

    utils.clear_selected_objects()
    utils.try_select_objects(selected)


def convert_to_non_standard(chr_cache):
    if chr_cache.generation == "G3Plus" or chr_cache.generation == "G3":
        chr_cache.generation = "ActorBuild"
    elif chr_cache.generation == "GameBase":
        chr_cache.generation = "GameBase"
    chr_cache.non_standard_type = "HUMANOID"


def match_materials(chr_cache):

    chr_objects = []
    chr_materials = []

    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.get_object()
        if obj:
            chr_objects.append(obj)
            for mat in obj.data.materials:
                chr_materials.append(mat)

    utils.log_info(f"Matching existing materials:")
    utils.log_indent()

    for obj in chr_objects:

        obj_cache = chr_cache.get_object_cache(obj)

        # objects imported from accurig will cause a duplication of names, so strip the numerical suffix
        # also accurig uses the *mesh* names, not the object names.
        mesh_source_name = utils.strip_name(obj.data.name)

        utils.log_info(f"Mesh: {obj.name} / {mesh_source_name}")
        utils.log_indent()

        for slot in obj.material_slots:
            mat = slot.material

            # again strip the numerical duplication suffix from the accurig imported material names
            mat_source_name = utils.strip_name(mat.name)

            slot_assigned = False
            assigned_mat = None

            # try to match the materials from an object with a matching source name (not part of the imported character)
            for existing_obj in bpy.data.objects:

                # convert the existing object name into a reallusion safe name
                existing_mesh_source_name = utils.safe_export_name(existing_obj.data.name)

                if (existing_mesh_source_name == mesh_source_name and
                    existing_obj not in chr_objects and
                    existing_obj.type == "MESH"):

                    utils.log_info(f"Existing mesh match: {existing_obj.name} / {existing_mesh_source_name}")

                    for existing_mat in existing_obj.data.materials:

                        # convert the existing material name into a reallusion safe name
                        existing_mat_source_name = utils.safe_export_name(existing_mat.name, True)

                        if existing_mat_source_name == mat_source_name:
                            utils.log_info(f"Assigning existing object / material: {existing_mat.name}")
                            slot.material = existing_mat
                            slot_assigned = True
                            assigned_mat = existing_mat
                            break

                    if slot_assigned:
                        break

            # failing that, try to match any existing material by name (not part of the imported character)
            if not slot_assigned:
                for existing_mat in bpy.data.materials:
                    if existing_mat not in chr_materials:
                        existing_mat_source_name = utils.safe_export_name(existing_mat.name, True)
                        if existing_mat_source_name == mat_source_name:
                            utils.log_info(f"Assigning existing material: {existing_mat.name}")
                            slot.material = existing_mat
                            slot_assigned = True
                            assigned_mat = existing_mat
                            break

            #if slot_assigned and assigned_mat:
            #    add_material_to_character(chr_cache, obj, obj_cache, assigned_mat, update_name=False)

        utils.log_recess()

    utils.log_recess()



class CC3OperatorCharacter(bpy.types.Operator):
    """CC3 Character Functions"""
    bl_idname = "cc3.character"
    bl_label = "Character Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps

        if self.param == "ADD_PBR":
            chr_cache = props.get_context_character_cache(context)
            objects = context.selected_objects.copy()
            for obj in objects:
                add_object_to_character(chr_cache, obj)

        elif self.param == "COPY_TO_CHARACTER":
            chr_cache = props.get_context_character_cache(context)
            objects = context.selected_objects.copy()
            copy_objects_character_to_character(context.object, chr_cache, objects)

        elif self.param == "REMOVE_OBJECT":
            chr_cache = props.get_context_character_cache(context)
            objects = context.selected_objects.copy()
            for obj in objects:
                remove_object_from_character(chr_cache, obj)

        elif self.param == "ADD_MATERIALS":
            chr_cache = props.get_context_character_cache(context)
            obj = context.active_object
            obj_cache = chr_cache.get_object_cache(obj)
            add_missing_materials_to_character(chr_cache, obj, obj_cache)

        elif self.param == "CLEAN_UP_DATA":
            chr_cache = props.get_context_character_cache(context)
            obj = context.active_object
            clean_up_character_data(chr_cache)

        elif self.param == "TRANSFER_WEIGHTS":
            chr_cache = props.get_context_character_cache(context)
            objects = [ obj for obj in bpy.context.selected_objects if obj.type == "MESH" ]
            mode_selection = utils.store_mode_selection_state()
            transfer_skin_weights(chr_cache, objects)
            utils.restore_mode_selection_state(mode_selection)

        elif self.param == "NORMALIZE_WEIGHTS":
            chr_cache = props.get_context_character_cache(context)
            objects = [ obj for obj in bpy.context.selected_objects if obj.type == "MESH" ]
            normalize_skin_weights(chr_cache, objects)

        elif self.param == "CONVERT_TO_NON_STANDARD":
            chr_cache = props.get_context_character_cache(context)
            convert_to_non_standard(chr_cache)
            self.report({'INFO'}, message="Convert to Non-standard complete!")

        elif self.param == "CONVERT_FROM_GENERIC":
            objects = context.selected_objects.copy()
            if convert_generic_to_non_standard(objects):
                self.report({'INFO'}, message="Generic character converted to Non-Standard!")
            else:
                self.report({'ERROR'}, message="Invalid generic character selection!")

        elif self.param == "MATCH_MATERIALS":
            chr_cache = props.get_context_character_cache(context)
            match_materials(chr_cache)

        elif self.param == "CONVERT_ACCESSORY":
            chr_cache = props.get_context_character_cache(context)
            objects = bpy.context.selected_objects.copy()
            make_accessory(chr_cache, objects)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "ADD_PBR":
            return "Add object to the character with pbr materials and parent to the character armature with an armature modifier"
        elif properties.param == "COPY_TO_CHARACTER":
            return "Copy the objects from another character into the active selected character"
        elif properties.param == "REMOVE_OBJECT":
            return "Unparent the object and remove from the character. Unparented objects will *not* be included in the export"
        elif properties.param == "ADD_MATERIALS":
            return "Add any new materials to the character data that are in this object but not in the character data"
        elif properties.param == "CLEAN_UP_DATA":
            return "Remove any objects from the character data that are no longer part of the character and remove any materials from the character that are no longer in the character objects"
        elif properties.param == "TRANSFER_WEIGHTS":
            return "Transfer skin weights from the character body to the selected objects.\n**THIS OPERATES IN ARMATURE REST MODE**"
        elif properties.param == "NORMALIZE_WEIGHTS":
            return "Recalculate the weights in the vertex groups so they all add up to 1.0 for each vertex, so each vertex is fully weighted across all the bones influencing it"
        elif properties.param == "CONVERT_TO_NON_STANDARD":
            return "Convert character to a non-standard Humanoid, Creature or Prop"
        elif properties.param == "CONVERT_FROM_GENERIC":
            return "Convert character from generic armature and objects to Non-Standard character with Reallusion materials."
        return ""


class CC3OperatorTransferCharacterGeometry(bpy.types.Operator):
    """Transfer Character Geometry:
       Copy base mesh shapes (e.g. After Sculpting) from active character to
       target character, for all *body* mesh objects in the characters, without
       destroying existing facial expression shape keys in the target Character.
       Source and target characters must have the same UV topology.
    """

    bl_idname = "cc3.transfer_character"
    bl_label = "Transfer Character Geometry"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        active = bpy.context.active_object
        selected = bpy.context.selected_objects.copy()

        shape_key_name = None
        if props.geom_transfer_layer == "SHAPE_KEY":
            shape_key_name = props.geom_transfer_layer_name

        src_chr = props.get_character_cache(active, None)
        selected_characters = []
        for dst_obj in selected:
            selected_character = props.get_character_cache(dst_obj, None)
            if selected_character not in selected_characters and selected_character != src_chr:
                selected_characters.append(selected_character)

        if src_chr and selected_characters:

            src_objects = src_chr.get_all_objects(include_armature = False, include_children = True, of_type = "MESH")
            src_arm = src_chr.get_armature()
            utils.object_mode_to(src_arm)
            utils.clear_selected_objects()
            dst_objects_transferred = []

            for src_obj in src_objects:
                src_base_name = utils.strip_name(src_obj.name)
                for dst_chr in selected_characters:
                    dst_objects = dst_chr.get_all_objects(include_armature = False, include_children = True, of_type = "MESH")
                    dst_arm = dst_chr.get_armature()
                    for dst_obj in dst_objects:
                        dst_base_name = utils.strip_name(dst_obj.name)
                        if src_base_name == dst_base_name:
                            if len(src_obj.data.vertices) == len(dst_obj.data.vertices):
                                if len(src_obj.data.polygons) == len(dst_obj.data.polygons):
                                    geom.copy_vert_positions_by_uv_id(src_obj, dst_obj, 5, shape_key_name=shape_key_name)
                                    if shape_key_name:
                                        for sk in dst_obj.data.shape_keys.key_blocks:
                                            sk.value = 0.0
                                        dst_obj.data.shape_keys.key_blocks[-1].value = 1.0
                                    dst_objects_transferred.append(dst_obj)

                    # shape key copy does not support copying the bind pose
                    if not shape_key_name:
                        bones.copy_rig_bind_pose(src_arm, dst_arm)
                        dst_objects_transferred.append(dst_arm)

            utils.object_mode_to(dst_arm)
            utils.try_select_objects(dst_objects_transferred, clear_selection=True)
            utils.set_active_object(dst_arm)

            self.report(type={"INFO"}, message="Done!")

        else:
            self.report(type={"ERROR"}, message="Needs active and other selected characters!")


        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):
        return """Transfer Character Geometry:
            Copy base mesh shapes (e.g. After Sculpting) from active character to
            target character, for all *body* mesh objects in the characters, without
            destroying existing facial expression shape keys in the target Character.
            Source and target characters must have the same UV topology"""


class CC3OperatorTransferMeshGeometry(bpy.types.Operator):
    """Transfer Mesh Geometry:
       Copy base mesh shape (e.g. After Sculpting) from active mesh to target
       mesh without destroying any existing shape keys in the target mesh.
       Source and target meshes must have the same UV topology.
    """

    bl_idname = "cc3.transfer_mesh"
    bl_label = "Transfer Mesh Geometry"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        active = bpy.context.active_object
        selected = bpy.context.selected_objects.copy()

        utils.object_mode_to(active)

        shape_key_name = None
        if props.geom_transfer_layer == "SHAPE_KEY":
            shape_key_name = props.geom_transfer_layer_name

        if active and len(selected) >= 2:
            for obj in selected:
                if obj != active:
                    geom.copy_vert_positions_by_uv_id(active, obj, 5, shape_key_name=shape_key_name)

            self.report(type={"INFO"}, message="Done!")

        else:
            self.report(type={"ERROR"}, message="Needs active and other selected meshes!")

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):
        return """Transfer Mesh Geometry:
            Copy base mesh shape (e.g. After Sculpting) from active mesh to target
            mesh without destroying any existing shape keys in the target mesh.
            Source and target meshes must have the same UV topology"""


class CCICCharacterLink(bpy.types.Operator):
    """Reconnect a linked or appended character to the source fbx and json data."""

    bl_idname = "ccic.characterlink"
    bl_label = "Character Linker"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    filepath: bpy.props.StringProperty(
            name="File Path",
            description="Filepath used for exporting the file",
            maxlen=1024,
            subtype='FILE_PATH'
        )

    filter_glob: bpy.props.StringProperty(
            default="*.blend",
            options={"HIDDEN"}
        )

    def execute(self, context):
        chr_rig = utils.get_context_armature(context)

        if self.param == "CONNECT":
            if chr_rig and self.filepath:
                path, ext = os.path.splitext(self.filepath)
                if utils.is_file_ext(ext, "BLEND"):
                    reconnect_rl_character_to_blend(chr_rig, self.filepath)
                else:
                    reconnect_rl_character_to_fbx(chr_rig, self.filepath)
        elif self.param == "LINK":
            link_or_append_rl_character(self.filepath, link=True)
        elif self.param == "APPEND":
            link_or_append_rl_character(self.filepath, link=False)
        return {"FINISHED"}


    def invoke(self, context, event):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        chr_cache = props.get_context_character_cache(context)
        chr_rig = utils.get_context_armature(context)

        if self.param == "CONNECT":
            self.filter_glob = "*.fbx;*.blend"
            if chr_rig and not chr_cache:
                context.window_manager.fileselect_add(self)
                return {"RUNNING_MODAL"}

        if self.param == "LINK" or self.param == "APPEND":
            self.filter_glob = "*.blend"
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):
        if properties.param == "CONNECT":
            return """Reconnect a linked or appended character to the source fbx and json data."""
        elif properties.param == "LINK":
            return """Link to an existing reallusion characer in a separate blend file."""
        elif properties.param == "APPEND":
            return """Append an existing reallusion characer in a separate blend file."""

