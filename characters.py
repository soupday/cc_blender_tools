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
import mathutils
import os

from . import materials, modifiers, meshutils, bones, shaders, nodeutils, utils, vars


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


def make_prop_armature(objects):

    utils.set_mode("OBJECT")

    # find the all the root empties and determine if there is one single root
    roots = []
    single_empty_root = None
    for obj in objects:

        # reset all transforms
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

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
    utils.clear_selected_objects()

    root_bone = None
    root_bone_name = None
    tail_vector = mathutils.Vector((0,0,0.1))
    tail_translate = mathutils.Matrix.Translation(-tail_vector)

    if utils.edit_mode_to(arm):

        if single_empty_root:
            root_bone = arm.data.edit_bones.new(single_empty_root.name)
            root_bone.head = single_empty_root.location
            root_bone.tail = single_empty_root.location + tail_vector
            root_bone.roll = 0
            root_bone_name = root_bone.name
        else:
            root_bone = arm.data.edit_bones.new("Root")
            root_bone.head = (0,0,0)
            root_bone.tail = (0,0,0.1)
            root_bone.roll = 0
            root_bone_name = root_bone.name

        for obj in objects:
            if obj.type == "EMPTY" and obj.name not in arm.data.edit_bones:
                bone = arm.data.edit_bones.new(obj.name)
                bone.head = obj.location
                bone.tail = obj.location + tail_vector

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
            print(obj.name)
            if obj.parent: print(obj.parent.name)
            if obj.parent and obj.parent.name in arm.data.bones:
                parent_name = obj.parent.name
                parent_bone : bpy.types.Bone = arm.data.bones[parent_name]
                obj.parent = arm
                obj.parent_type = 'BONE'
                obj.parent_bone = parent_name
                obj.matrix_parent_inverse = parent_bone.matrix_local.inverted() @ tail_translate
            elif root_bone_name:
                parent_bone = arm.data.bones[root_bone_name]
                obj.parent = arm
                obj.parent_type = 'BONE'
                obj.parent_bone = root_bone_name
                obj.matrix_parent_inverse = parent_bone.matrix_local.inverted() @ tail_translate

    # remove the empties and move all objects into the same collection as the armature
    collection = utils.get_object_collection(arm)
    for obj in objects:
        if obj.type == "EMPTY":
            bpy.data.objects.remove(obj)
        else:
            utils.move_object_to_collection(obj, collection)

    # finally force the armature name again (as it may have been taken by the original object)
    arm.name = arm_name

    return arm


def add_child_objects(obj, objects):
    for child in obj.children:
        if child not in objects:
            print(f"adding {child.name}")
            objects.append(child)
            add_child_objects(child, objects)


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

    # select all child objects of the current selected objects (Humanoid)
    utils.try_select_objects(objects, True)
    for obj in objects:
        utils.try_select_child_objects(obj)

    objects = bpy.context.selected_objects

    # try to find a character armature
    chr_rig = utils.get_generic_character_rig(objects)
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
    chr_cache.import_type = ext[1:]
    chr_cache.import_name = name
    chr_cache.import_dir = dir
    chr_cache.import_space_in_name = False
    chr_cache.character_index = 0
    chr_cache.character_name = full_name
    chr_cache.character_id = name
    chr_cache.import_key_file = ""
    chr_cache.import_has_key = False
    chr_cache.import_main_tex_dir = ""
    chr_cache.import_embedded = False
    chr_cache.generation = "NonStandardGeneric"
    chr_cache.non_standard_type = chr_type

    chr_cache.add_object_cache(chr_rig)

    # add child objects to object_cache
    for obj in objects:
        if utils.object_exists_is_mesh(obj):
            add_object_to_character(chr_cache, obj, reparent=False)

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
            arm_mod : bpy.types.ArmatureModifier = modifiers.add_armature_modifier(obj, True)
            modifiers.move_mod_first(obj, arm_mod)

        # update armature modifier rig
        if arm_mod and arm_mod.object != rig:
            arm_mod.object = rig

        utils.clear_selected_objects()
        utils.set_active_object(obj)


def add_object_to_character(chr_cache, obj : bpy.types.Object, reparent = True):
    props = bpy.context.scene.CC3ImportProps

    if chr_cache and obj and obj.type == "MESH":

        obj_cache = chr_cache.get_object_cache(obj)

        if not obj_cache:

            # convert the object name to remove any duplicate suffixes:
            obj_name = utils.unique_object_name(obj.name, obj)
            if obj.name != obj_name:
                obj.name = obj_name

            # add the object into the object cache
            obj_cache = chr_cache.add_object_cache(obj)
            obj_cache.object_type = "DEFAULT"
            obj_cache.user_added = True

        add_missing_materials_to_character(chr_cache, obj, obj_cache)

        utils.clear_selected_objects()

        if reparent:
            arm = chr_cache.get_armature()
            parent_to_rig(arm, obj)


def remove_object_from_character(chr_cache, obj):
    props = bpy.context.scene.CC3ImportProps

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

                obj.hide_set(True)

                utils.clear_selected_objects()
                # don't reselect the removed object as this may cause confusion when using checking function immediately after...
                #utils.set_active_object(obj)


def get_accessory_root(chr_cache, object):

    if not chr_cache or not object or not utils.object_exists_is_mesh(object):
        return None

    rig = chr_cache.get_armature()
    rigify_data = chr_cache.get_rig_mapping_data()
    bone_mappings = rigify_data.bone_mapping

    if not rig or not rigify_data or not bone_mappings:
        return None

    accessory_root = None

    # accessories can be identified by them having only vertex groups not listed in the bone mappings for this generation.
    for vg in object.vertex_groups:

        # if even one vertex groups belongs to the character bones, it will not import into cc4 as an accessory
        if bones.bone_mapping_contains_bone(bone_mappings, vg.name):
            return

        else:
            bone = bones.get_bone(rig, vg.name)
            if bone:
                root = bones.get_accessory_root_bone(bone_mappings, bone)
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
                root_tail = rig.matrix_world.inverted() @ (bpy.context.scene.cursor.location + mathutils.Vector((0, 1/4, 0)))
                piv_tail = rig.matrix_world.inverted() @ (bpy.context.scene.cursor.location + mathutils.Vector((0, 1/10000, 0)))
                utils.log_info(f"Adding accessory root bone: {accessory_root.name}/({root_head})")
                accessory_root.head = root_head
                accessory_root.tail = root_tail

                default_parent = bones.get_rl_edit_bone(rig, chr_cache.accessory_parent_bone)
                accessory_root.parent = default_parent

                for obj in objects:
                    if obj.type == "MESH":

                        # add object bone to rig
                        obj_bone = rig.data.edit_bones.new(obj.name)
                        obj_head = rig.matrix_world.inverted() @ (obj.matrix_world @ mathutils.Vector((0, 0, 0)))
                        obj_tail = rig.matrix_world.inverted() @ ((obj.matrix_world @ mathutils.Vector((0, 0, 0))) + mathutils.Vector((0, 1/8, 0)))
                        utils.log_info(f"Adding object bone: {obj_bone.name}/({obj_head})")
                        obj_bone.head = obj_head
                        obj_bone.tail = obj_tail

                        # add pivot bone to rig
                        #piv_bone = rig.data.edit_bones.new("CC_Base_Pivot")
                        #utils.log_info(f"Adding pivot bone: {piv_bone.name}/({root_head})")
                        #piv_bone.head = root_head + mathutils.Vector((0, 1/100, 0))
                        #piv_bone.tail = piv_tail + mathutils.Vector((0, 1/100, 0))
                        #piv_bone.parent = obj_bone

                        # add deformation bone to rig
                        def_bone = rig.data.edit_bones.new(obj.name)
                        utils.log_info(f"Adding deformation bone: {def_bone.name}/({obj_head})")
                        def_head = rig.matrix_world.inverted() @ ((obj.matrix_world @ mathutils.Vector((0, 0, 0))) + mathutils.Vector((0, 1/32, 0)))
                        def_tail = rig.matrix_world.inverted() @ ((obj.matrix_world @ mathutils.Vector((0, 0, 0))) + mathutils.Vector((0, 1/32 + 1/16, 0)))
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

            if obj_cache.object != arm:

                if utils.object_exists_is_mesh(obj_cache.object):

                    # be sure not to delete object and material cache data for objects still existing in the scene,
                    # but not currently attached to the character
                    if obj_cache.object not in current_objects:
                        unparented_objects.append(obj_cache.object)
                        utils.log_info(f"Keeping unparented Object data: {obj_cache.object.name}")
                        for mat in obj_cache.object.data.materials:
                            if mat and mat not in unparented_materials:
                                unparented_materials.append(mat)
                                utils.log_info(f"Keeping unparented Material data: {mat.name}")

                else:

                    # add any invalid cached objects to the delete list
                    delete_objects.append(obj_cache.object)

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

        elif n.type == "GROUP" and n.node_tree and "glTF Settings" in n.node_tree.name:

            if not gltf_node:
                gltf_node = n
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
    sockets = [
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
        ["Occlusion", "", "GLTF", "AO Map", "", "default_ao_strength"],
    ]

    if bsdf_node:
        try:
            clearcoat_value = bsdf_node.inputs["Clearcoat"].default_value
            roughness_value = bsdf_node.inputs["Roughness"].default_value
            metallic_value = bsdf_node.inputs["Metallic"].default_value
            specular_value = bsdf_node.inputs["Specular"].default_value
            alpha_value = bsdf_node.inputs["Alpha"].default_value

            if bsdf_node.inputs["Emission"].is_linked:
                if utils.is_blender_version("2.93.0"):
                    emission_value = bsdf_node.inputs["Emission Strength"].default_value
                else:
                    emission_value = 1.0
            else:
                emission_value = 0.0

            if not bsdf_node.inputs["Base Color"].is_linked:
                diffuse_color = bsdf_node.inputs["Base Color"].default_value
                mat_cache.parameters.default_diffuse_color = diffuse_color

            mat_cache.parameters.default_roughness = roughness_value
            # a rough approximation for the clearcoat
            mat_cache.parameters.default_roughness_power = 1.0 + clearcoat_value
            mat_cache.parameters.default_metallic = metallic_value
            mat_cache.parameters.default_specular = specular_value
            mat_cache.parameters.default_emission_strength = emission_value / vars.EMISSION_SCALE
            mat_cache.parameters.default_emissive_color = (1.0, 1.0, 1.0, 1.0)
            bsdf_node.inputs["Emission Strength"].default_value = 1.0
            bsdf_node.inputs["Clearcoat"].default_value = 0.0
            if not bsdf_node.inputs["Alpha"].is_linked:
                mat_cache.parameters.default_opacity = alpha_value
        except:
            utils.log_warn("Unable to set material cache defaults!")

    socket_mapping = {}
    for socket_trace, match, node_type, group_socket, strength_trace, strength_prop in sockets:
        if node_type == "BSDF":
            n = bsdf_node
        elif node_type == "GLTF":
            n = gltf_node
        else:
            n = None
        if n:
            linked_node, linked_socket = nodeutils.trace_input_sockets(n, socket_trace)

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
                    if re.match(match, linked_node.label) or re.match(match, linked_node.name):
                        socket_mapping[group_socket] = [linked_node, linked_socket, strength, strength_prop]
                else:
                    socket_mapping[group_socket] = [linked_node, linked_socket, strength, strength_prop]

    # connect the shader group node sockets
    for socket_name in socket_mapping:
        linked_info = socket_mapping[socket_name]
        linked_node = linked_info[0]
        linked_socket = linked_info[1]
        strength = linked_info[2]
        strength_prop = linked_info[3]
        nodeutils.link_nodes(links, linked_node, linked_socket, group_node, socket_name)
        if strength_prop:
            print(f"setting {strength_prop} = {strength}")
            shaders.exec_prop(strength_prop, mat_cache, strength)

    if bsdf_node and group_node and mat_cache:
        shaders.apply_prop_matrix(bsdf_node, group_node, mat_cache, "rl_pbr_shader")

    # connect all group_node outputs to BSDF inputs:
    for socket in group_node.outputs:
        nodeutils.link_nodes(links, group_node, socket.name, bsdf_node, socket.name)

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


def transfer_skin_weights(chr_cache, objects):

    if not utils.set_mode("OBJECT"):
        return

    arm = chr_cache.get_armature()
    if arm is None:
        return

    body = None
    for obj_cache in chr_cache.object_cache:
        if obj_cache.object_type == "BODY":
            body = obj_cache.object

    if not body:
        return

    if body in objects:
        objects.remove(body)

    # TODO figure out a way to transfer weights in POSE mode...
    # almost there but need to copy the armature and set the bind pose to the current pose,
    # transfer weights from the posed-bind-pose body
    # then construct the origin rest pose in the baked armature's pose by setting the bone positions/roll directly.
    # then can apply that pose to get the item into the origin rest pose.
    # (maybe transfer weights again?)
    # in pose mode, use a copy of the body with it's armature modifier applied (shapekeys must be removed for this.)
    #if arm.data.pose_position == "POSE":
    #    body_copy = body.copy()
    #    body_copy.name = body.name + "_TEMP_COPY"
    #    body_copy.data = body.data.copy()
    #    bpy.context.collection.objects.link(body_copy)
    #
    #    if utils.try_select_object(body_copy, True) and utils.set_active_object(body_copy):
    #
    #        bpy.ops.object.shape_key_remove(all=True)
    #        mod : bpy.types.Modifier
    #        for mod in body_copy.modifiers:
    #            if mod.type == "ARMATURE":
    #                bpy.ops.object.modifier_apply(modifier=mod.name)
    #
    #        body = body_copy
    #    else:
    #        return

    selected = bpy.context.selected_objects.copy()

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
                arm_mod : bpy.types.ArmatureModifier = modifiers.add_armature_modifier(obj, True)
                if arm_mod:
                    modifiers.move_mod_first(obj, arm_mod)
                    arm_mod.object = arm

    # remove the copy of the body if in pose mode
    #if arm.data.pose_position == "POSE":
    #    bpy.data.objects.remove(body)

    utils.clear_selected_objects()
    utils.try_select_objects(selected)


def normalize_skin_weights(chr_cache, objects):

    if not utils.set_mode("OBJECT"):
        return

    arm = chr_cache.get_armature()
    if arm is None:
        return

    body = None
    for obj_cache in chr_cache.object_cache:
        if obj_cache.object_type == "BODY":
            body = obj_cache.object

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
        chr_cache.generation = "NonStandardG3"
    elif chr_cache.generation == "GameBase":
        chr_cache.generation = "NonStandardGameBase"
    chr_cache.non_standard_type = "HUMANOID"


def match_materials(chr_cache):

    chr_objects = []
    chr_materials = []

    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
        if utils.object_exists_is_mesh(obj):
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
            obj = context.active_object
            add_object_to_character(chr_cache, obj)

        if self.param == "REMOVE_OBJECT":
            chr_cache = props.get_context_character_cache(context)
            obj = context.active_object
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
            objects = bpy.context.selected_objects.copy()
            transfer_skin_weights(chr_cache, objects)

        elif self.param == "NORMALIZE_WEIGHTS":
            chr_cache = props.get_context_character_cache(context)
            objects = bpy.context.selected_objects.copy()
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
        elif properties.param == "REMOVE_OBJECT":
            return "Unparent the object from the character and automatically hide it. Unparented objects will *not* be included in the export"
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
