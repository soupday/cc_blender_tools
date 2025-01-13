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

import os
import bpy
import mathutils

from . import nodeutils, imageutils, meshutils, geom, materials, bake, modifiers, utils, params, vars

LAYER_TARGET_SCULPT = "BODY"
LAYER_TARGET_DETAIL = "DETAIL"
BAKE_TYPE_NORMALS = "NORMALS"
BAKE_TYPE_DISPLACEMENT = "DISPLACEMENT"
BAKE_TYPE_AO = "AO"
LAYER_MIX_SUFFIX = "Layer_Mix"
BAKE_NORMAL_SUFFIX = "Bake_Normal"
BAKE_DISPLACEMENT_SUFFIX = "Bake_Displacement"
BAKE_AO_SUFFIX = "Bake_AO"
LAYER_NORMAL_SUFFIX = "Layer_Normal"
LAYER_DISPLACEMENT_SUFFIX = "Layer_Displacement"
LAYER_AO_SUFFIX = "Layer_AO"
BAKE_FOLDER = "Sculpt Bake"
SKINGEN_FOLDER = "Skingen"


def set_multi_res_level(obj, view_level = -1, sculpt_level = -1, render_level = -1):
    if obj:
        mod : bpy.types.MultiresModifier
        mod = modifiers.get_object_modifier(obj, modifiers.MOD_MULTIRES, modifiers.MOD_MULTIRES_NAME)
        if mod:
            utils.log_info(f"Setting Multi-res modifier to levels: {view_level}/{sculpt_level}/{render_level}")
            if view_level >= 0:
                mod.levels = max(0, min(view_level, mod.total_levels))
            if sculpt_level >= 0:
                mod.sculpt_levels = max(0, min(sculpt_level, mod.total_levels))
            if render_level >= 0:
                mod.render_levels = max(0, min(render_level, mod.total_levels))


def apply_multi_res_shape(body):
    # applying base shape distorts the displacement maps
    # so it must be done after the displacement map is baked, and it must be final,
    # displacement map masks will no longer work after this
    if utils.object_mode() and utils.set_only_active_object(body):

        # removing all shape keys
        utils.log_info("Removing all shape keys")
        try:
            bpy.ops.object.shape_key_remove(all=True)
        except:
            pass

        # applying base shape
        mod = modifiers.get_object_modifier(body, modifiers.MOD_MULTIRES, modifiers.MOD_MULTIRES_NAME)
        if mod and utils.set_only_active_object(body):
            utils.log_info("Applying base shape")
            bpy.ops.object.multires_base_apply(modifier=mod.name)


def displacement_map_func(value):
    return abs(value - 0.5)


def copy_base_shape(multi_res_object, source_body_obj, layer_target, by_vertex_group = False):
    utils.log_info("Copying shape to source body.")

    if by_vertex_group:

        # generate vertex weights for mesh copy
        for mat in multi_res_object.data.materials:
            displacement_map = nodeutils.get_node_by_id_and_type(mat.node_tree.nodes,
                                                                 f"{layer_target}_{BAKE_DISPLACEMENT_SUFFIX}",
                                                                 "TEX_IMAGE")

            geom.map_image_to_vertex_weights(multi_res_object, mat, displacement_map.image,
                                             "DISPLACEMENT_MASKED", displacement_map_func)

        # copy to source body using vertex weights as a copy mask
        geom.copy_vert_positions_by_uv_id(multi_res_object, source_body_obj, accuracy = 5,
                                          vertex_group = "DISPLACEMENT_MASKED", threshold = 0.0038,
                                          flatten_udim=True)

    else:

        # copy to source body
        geom.copy_vert_positions_by_uv_id(multi_res_object, source_body_obj, accuracy = 5,
                                          flatten_udim=True)

    return


def do_multires_bake(context, chr_cache, multires_mesh, layer_target, apply_shape=False, source_body=None):
    prefs = vars.prefs()

    utils.log_info(f"Begin Multi-Res Bake: Layer = {layer_target}")
    utils.log_indent()

    if utils.B292():
        bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'

    # store object render visibility state
    rv_state = utils.store_render_visibility_state()

    # prep for baking directly onto body mesh surface
    bake_state = bake.prep_bake(context, samples=32, make_surface=False)

    # AO Baking (full res on body mesh)
    select_bake_images(multires_mesh, BAKE_TYPE_AO, layer_target)

    ao_body = utils.duplicate_object(multires_mesh)
    ao_body.name = multires_mesh.name + "_AOBAKE"
    materials.normalize_udim_uvs(ao_body)
    utils.set_only_render_visible(ao_body)
    utils.object_mode_to(ao_body)
    utils.set_only_active_object(ao_body)
    set_multi_res_level(ao_body, view_level=9, sculpt_level=9, render_level=9)
    utils.log_info(f"Baking {layer_target} AO...")
    bpy.context.scene.render.use_bake_multires = False
    # *cycles* bake type to AO
    bpy.context.scene.cycles.bake_type = "AO"
    if prefs.bake_use_gpu:
        bake.set_cycles_samples(context, samples=2048, adaptive_samples=0.1, time_limit=15, use_gpu=True)
    else:
        bake.set_cycles_samples(context, samples=16, time_limit=30, use_gpu=False)
    bpy.ops.object.bake(type="AO")
    utils.delete_mesh_object(ao_body)

    # Displacement Baking
    select_bake_images(multires_mesh, BAKE_TYPE_DISPLACEMENT, layer_target)

    bpy.context.scene.render.use_bake_multires = True
    bake.set_cycles_samples(context, samples=2)

    # copy the body for displacement baking
    utils.log_info("Duplicating body for displacement baking")
    utils.unhide(multires_mesh)
    disp_body = utils.duplicate_object(multires_mesh)
    disp_body.name = multires_mesh.name + "_DISPBAKE"
    materials.normalize_udim_uvs(disp_body)

    # displacement masks *will not* bake if multiple overlapping materials in the mesh,
    # so split by materials and bake each separately.
    utils.log_info(f"Baking {layer_target} displacement...")
    utils.clear_selected_objects()
    utils.set_only_active_object(disp_body)
    utils.edit_mode_to(disp_body)
    bpy.ops.mesh.separate(type='MATERIAL')
    objects = bpy.context.selected_objects.copy()
    for obj in objects:
        utils.set_only_render_visible(obj)
        utils.object_mode_to(obj)
        utils.set_only_active_object(obj)
        # copying or splitting the mesh resets the multi-res levels...
        set_multi_res_level(obj, view_level=0, sculpt_level=9, render_level=9)
        # bake the displacement mask
        utils.log_info(f"Baking {layer_target} sub displacement {obj.name}")
        bpy.context.scene.render.bake_type = BAKE_TYPE_DISPLACEMENT
        bpy.ops.object.bake_image()
        utils.delete_mesh_object(obj)

    # Normal Baking
    select_bake_images(multires_mesh, BAKE_TYPE_NORMALS, layer_target)

    # copy the body for normal baking
    utils.set_only_render_visible(multires_mesh)
    utils.log_info("Duplicating body for normal baking")
    norm_body = utils.duplicate_object(multires_mesh)
    norm_body.name = multires_mesh.name + "_NORMBAKE"
    materials.normalize_udim_uvs(norm_body)
    utils.set_only_render_visible(norm_body)
    utils.object_mode_to(norm_body)
    utils.set_only_active_object(norm_body)
    apply_multi_res_shape(norm_body)

    # set multi-res levels for normal baking
    utils.log_info("Setting multi-res levels for baking")
    set_multi_res_level(norm_body, view_level=0, sculpt_level=9, render_level=9)

    # bake the normals
    utils.log_info(f"Baking {layer_target} normals...")
    bpy.context.scene.render.bake_type = BAKE_TYPE_NORMALS
    bpy.ops.object.bake_image()

    utils.log_recess()
    utils.log_info("Baking complete!")

    utils.delete_mesh_object(norm_body)

    if layer_target == LAYER_TARGET_SCULPT and apply_shape and source_body:

        utils.log_info("Transfering sculpt base shape to source body...")

        utils.unhide(multires_mesh)
        utils.unhide(source_body)
        copy_base_shape(multires_mesh, source_body, layer_target, True)

        # if there is a detail sculpt body, update that with the new base shape too
        detail_body = chr_cache.get_detail_body(context_object=source_body)
        if detail_body:
            copy_base_shape(multires_mesh, detail_body, layer_target, True)

    # restore render engine
    bake.post_bake(context, bake_state)

    # restore object render visibilty state
    utils.restore_render_visibility_state(rv_state)


def save_skin_gen_bake(chr_cache, body, layer_target):
    base_dir = utils.local_path()
    if not base_dir:
        base_dir = chr_cache.get_import_dir()

    bake_dir = os.path.join(base_dir, BAKE_FOLDER)
    utils.log_info(f"Texture save path: {bake_dir}")
    os.makedirs(bake_dir, exist_ok=True)

    character_name = chr_cache.character_name

    if body:
        for mat in body.data.materials:

            normal_image_name = f"{character_name}_{mat.name}_{layer_target}_{BAKE_NORMAL_SUFFIX}"
            displacement_image_name = f"{character_name}_{mat.name}_{layer_target}_{BAKE_DISPLACEMENT_SUFFIX}"
            ao_image_name = f"{character_name}_{mat.name}_{layer_target}_{BAKE_AO_SUFFIX}"

            if normal_image_name in bpy.data.images:
                normal_image = bpy.data.images[normal_image_name]

            if displacement_image_name in bpy.data.images:
                displacement_image = bpy.data.images[displacement_image_name]

            if ao_image_name in bpy.data.images:
                ao_image = bpy.data.images[ao_image_name]

            images = [
                [normal_image, normal_image_name, 'PNG', '8'],
                [ao_image, ao_image_name, 'PNG', '8'],
                [displacement_image, displacement_image_name, 'PNG', '16'],
            ]

            image : bpy.types.Image
            for image, image_name, file_format, color_depth in images:
                if image:
                    image_file = image_name + ".png"
                    image_path = os.path.normpath(os.path.join(bake_dir, image_file))

                    if image_path:
                        imageutils.save_scene_image(image, image_path, file_format, color_depth)
                        utils.log_info(f"Saved baked Image: {image_path}")


def select_bake_images(body, bake_type, layer_target):
    if body:
        for mat in body.data.materials:
            nodes = mat.node_tree.nodes
            for node in nodes:
                node.select = False

            if bake_type == BAKE_TYPE_NORMALS:
                bake_node_name = f"{layer_target}_{BAKE_NORMAL_SUFFIX}"
            elif bake_type == BAKE_TYPE_AO:
                bake_node_name = f"{layer_target}_{BAKE_AO_SUFFIX}"
            else:
                bake_node_name = f"{layer_target}_{BAKE_DISPLACEMENT_SUFFIX}"

            bake_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", bake_node_name)

            if bake_node:
                utils.log_info(f"Selecting image {bake_node.name} for bake.")
                bake_node.select = True
                nodes.active = bake_node
            else:
                utils.log_error(f"Could not find image node: {bake_node_name}!")


def has_overlay_nodes(body, layer_target):
    mix_node_name = f"{layer_target}_{LAYER_MIX_SUFFIX}"
    if body:
        for mat in body.data.materials:
            nodes = mat.node_tree.nodes
            mix_node = nodeutils.find_node_by_type_and_keywords(nodes, "GROUP", mix_node_name)
            if mix_node:
                return True
    return False


def has_body_multires_mod(body):
    if body:
        mod = modifiers.get_object_modifier(body, modifiers.MOD_MULTIRES, modifiers.MOD_MULTIRES_NAME)
        if mod:
            return True
    return False


def export_skingen(context, chr_cache, layer_target, export_path):

    export_dir, export_file = os.path.split(export_path)
    export_name, export_ext = os.path.splitext(export_file)

    utils.log_info(f"Texture save path: {export_dir}")
    os.makedirs(export_dir, exist_ok=True)

    source_obj = utils.get_context_mesh(context)

    if layer_target == LAYER_TARGET_DETAIL:
        channel_id = "Detail"
    else:
        channel_id = "Body"

    if source_obj:

        mix_node_name = f"{layer_target}_{LAYER_MIX_SUFFIX}"

        for mat in source_obj.data.materials:

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            mix_node = nodeutils.find_node_by_type_and_keywords(nodes, "GROUP", mix_node_name)

            if mix_node:
                bake.bake_node_socket_output(context, mix_node, "Normal Layer", mat, channel_id + " Normal", export_dir,
                                             name_prefix = export_name, exact_name=True, underscores=False)

                bake.bake_node_socket_output(context, mix_node, "AO Layer", mat, channel_id + " AO", export_dir,
                                             name_prefix = export_name, exact_name=True, underscores=False)

                bake.bake_node_socket_output(context, mix_node, "Mask", mat, channel_id + " Mask", export_dir,
                                             name_prefix = export_name, exact_name=True, underscores=False)


def update_layer_nodes(context, chr_cache, layer_target, socket, value):
    context = vars.get_context(context)
    source_obj = utils.get_context_mesh(context)
    if chr_cache and source_obj:
        mix_node_name = f"{layer_target}_{LAYER_MIX_SUFFIX}"
        for mat in source_obj.data.materials:
            nodes = mat.node_tree.nodes
            mix_node = nodeutils.find_node_by_type_and_keywords(nodes, "GROUP", mix_node_name)
            nodeutils.set_node_input_value(mix_node, socket, value)

def get_bake_dir(chr_cache):
    base_dir = utils.local_path()
    if not base_dir:
        base_dir = chr_cache.get_import_dir()
    bake_dir = os.path.join(base_dir, BAKE_FOLDER)
    utils.log_info(f"Texture save path: {bake_dir}")
    os.makedirs(bake_dir, exist_ok=True)
    return bake_dir


def setup_bake_nodes(context, chr_cache, multires_mesh, layer_target):
    prefs = vars.prefs()

    bake_dir = get_bake_dir(chr_cache)

    for mat in multires_mesh.data.materials:
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        utils.log_info(f"Setting up {layer_target} bake and layer nodes for {mat.name}")

        mat_cache = chr_cache.get_material_cache(mat)
        shader_name = params.get_shader_name(mat_cache)
        bsdf_node, shader_node, mixer_node = nodeutils.get_shader_nodes(mat, shader_name)

        # base the image name on the character name
        character_name = chr_cache.character_name
        mix_node_name = f"{layer_target}_{LAYER_MIX_SUFFIX}"
        sculpt_mix_node_name = f"{LAYER_TARGET_SCULPT}_{LAYER_MIX_SUFFIX}"
        detail_mix_node_name = f"{LAYER_TARGET_DETAIL}_{LAYER_MIX_SUFFIX}"
        normal_image_name = f"{character_name}_{mat.name}_{layer_target}_{BAKE_NORMAL_SUFFIX}"
        ao_image_name = f"{character_name}_{mat.name}_{layer_target}_{BAKE_AO_SUFFIX}"
        displacement_image_name = f"{character_name}_{mat.name}_{layer_target}_{BAKE_DISPLACEMENT_SUFFIX}"
        normal_bake_node_name = f"{layer_target}_{BAKE_NORMAL_SUFFIX}"
        ao_bake_node_name = f"{layer_target}_{BAKE_AO_SUFFIX}"
        displacement_bake_node_name = f"{layer_target}_{BAKE_DISPLACEMENT_SUFFIX}"
        normal_layer_node_name = f"{layer_target}_{LAYER_NORMAL_SUFFIX}"
        ao_layer_node_name = f"{layer_target}_{LAYER_AO_SUFFIX}"
        displacement_layer_node_name = f"{layer_target}_{LAYER_DISPLACEMENT_SUFFIX}"
        normal_image_file = normal_image_name + ".png"
        normal_image_path = os.path.normpath(os.path.join(bake_dir, normal_image_file))
        ao_image_file = ao_image_name + ".png"
        ao_image_path = os.path.normpath(os.path.join(bake_dir, ao_image_file))
        displacement_image_file = displacement_image_name + ".png"
        displacement_image_path = os.path.normpath(os.path.join(bake_dir, displacement_image_file))

        delta = 0
        if layer_target == LAYER_TARGET_DETAIL:
            delta = 600

        if layer_target == LAYER_TARGET_DETAIL:
            normal_image = imageutils.get_custom_image(normal_image_name, int(prefs.detail_normal_bake_size), alpha = False, data = True, path = normal_image_path)
            ao_image = imageutils.get_custom_image(ao_image_name, int(0.5 * int(prefs.detail_normal_bake_size)), alpha = False, data = True, path = ao_image_path)
            displacement_image = imageutils.get_custom_image(displacement_image_name, int(prefs.detail_normal_bake_size), alpha = False, data = True, float = True, path = displacement_image_path)
        else:
            normal_image = imageutils.get_custom_image(normal_image_name, int(prefs.body_normal_bake_size), alpha = False, data = True, path = normal_image_path)
            ao_image = imageutils.get_custom_image(ao_image_name, int(0.5 * int(prefs.body_normal_bake_size)), alpha = False, data = True, path = ao_image_path)
            displacement_image = imageutils.get_custom_image(displacement_image_name, int(prefs.body_normal_bake_size), alpha = False, data = True, float = True, path = displacement_image_path)

        normal_tex_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", "(NORMAL)")
        ao_tex_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", "(AO)")
        ref_location = mathutils.Vector((-1600, -1100))
        normal_bake_node = nodeutils.create_custom_image_node(nodes, normal_bake_node_name, normal_image, location = (1000 + delta, -1000))
        ao_bake_node = nodeutils.create_custom_image_node(nodes, ao_bake_node_name, ao_image, location = (1000 + delta, -1300))
        displacement_bake_node = nodeutils.create_custom_image_node(nodes, displacement_bake_node_name, displacement_image,
                                                                 location = (1000 + delta, -1600))
        normal_layer_node = nodeutils.create_custom_image_node(nodes, normal_layer_node_name, normal_image,
                                                     location = ref_location + mathutils.Vector((delta, -1200)))
        ao_layer_node = nodeutils.create_custom_image_node(nodes, ao_layer_node_name, ao_image,
                                                     location = ref_location + mathutils.Vector((delta, -1500)))
        displacement_layer_node = nodeutils.create_custom_image_node(nodes, displacement_layer_node_name, displacement_image,
                                                     location = ref_location + mathutils.Vector((delta, -1800)))

        # find or create the layer mix group
        mix_node = nodeutils.find_node_by_type_and_keywords(nodes, "GROUP", mix_node_name)
        if not mix_node:
            mix_group = nodeutils.get_node_group("rl_tex_mod_normal_ao_blend")
            mix_node = nodeutils.make_node_group_node(nodes, mix_group, "Normal Blend", mix_node_name)
            if layer_target == LAYER_TARGET_DETAIL:
                chr_cache.detail_normal_strength = 1.0
                chr_cache.detail_ao_strength = 0.5
                chr_cache.detail_normal_definition = 15.0
                chr_cache.detail_mix_mode = "OVERLAY"
            elif layer_target == LAYER_TARGET_SCULPT:
                chr_cache.body_normal_strength = 1.0
                chr_cache.body_ao_strength = 0.5
                chr_cache.body_normal_definition = 15.0
                chr_cache.body_mix_mode = "OVERLAY"
        if layer_target == LAYER_TARGET_DETAIL:
            nodeutils.set_node_input_value(mix_node, "Normal Strength", chr_cache.detail_normal_strength)
            nodeutils.set_node_input_value(mix_node, "AO Strength", chr_cache.detail_ao_strength)
            nodeutils.set_node_input_value(mix_node, "Definition", chr_cache.detail_normal_definition)
            nodeutils.set_node_input_value(mix_node, "Mix Mode", 0.0)
        elif layer_target == LAYER_TARGET_SCULPT:
            nodeutils.set_node_input_value(mix_node, "Normal Strength", chr_cache.body_normal_strength)
            nodeutils.set_node_input_value(mix_node, "AO Strength", chr_cache.body_ao_strength)
            nodeutils.set_node_input_value(mix_node, "Definition", chr_cache.body_normal_definition)
            nodeutils.set_node_input_value(mix_node, "Mix Mode", 0.0)

        mix_node.location = ref_location + mathutils.Vector((300 + delta, -1200))

        # if connecting the detail layer and there is also a sculpt layer, connect the normal input from the sculpt layer instead
        sculpt_mix_node = nodeutils.find_node_by_type_and_keywords(nodes, "GROUP", sculpt_mix_node_name)
        if layer_target == LAYER_TARGET_DETAIL and sculpt_mix_node:
            nodeutils.link_nodes(links, sculpt_mix_node, "Color", mix_node, "Color1")
            nodeutils.link_nodes(links, sculpt_mix_node, "AO", mix_node, "AO1")
        else:
            nodeutils.link_nodes(links, normal_tex_node, "Color", mix_node, "Color1")
            nodeutils.link_nodes(links, ao_tex_node, "Color", mix_node, "AO1")

        nodeutils.link_nodes(links, normal_layer_node, "Color", mix_node, "Color2")
        nodeutils.link_nodes(links, ao_layer_node, "Color", mix_node, "AO2")
        nodeutils.link_nodes(links, displacement_layer_node, "Color", mix_node, "Displacement Mask")

        # if connecting the sculpt layer and there is also a detail layer, connect the normal output from the sculpt layer to detail layer input
        detail_mix_node = nodeutils.find_node_by_type_and_keywords(nodes, "GROUP", detail_mix_node_name)
        if layer_target == LAYER_TARGET_SCULPT and detail_mix_node:
            nodeutils.link_nodes(links, mix_node, "Color", detail_mix_node, "Color1")
            nodeutils.link_nodes(links, mix_node, "AO", detail_mix_node, "AO1")
        else:
            nodeutils.link_nodes(links, mix_node, "Color", shader_node, "Normal Map")
            nodeutils.link_nodes(links, mix_node, "AO", shader_node, "AO Map")

        # disconnect the normals to the bsdf node (so they don't get included in the bake)
        nodeutils.unlink_node_input(links, bsdf_node, "Normal")


def finish_bake(chr_cache, detail_body, layer_target):
    if detail_body:
        for mat in detail_body.data.materials:
            utils.log_info(f"Finalizing bake node setup for {mat.name}")
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            mat_cache = chr_cache.get_material_cache(mat)
            shader_name = params.get_shader_name(mat_cache)
            bsdf_node, shader_node, mixer_node = nodeutils.get_shader_nodes(mat, shader_name)
            nodeutils.link_nodes(links, shader_node, "Normal", bsdf_node, "Normal")


def remove_bake_nodes(context, chr_cache, layer_target, multires_mesh):
    if not utils.object_exists_is_mesh(multires_mesh):
        utils.log_error("Multires mesh not found!")
        return

    for mat in multires_mesh.data.materials:
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        utils.log_info(f"Removing {layer_target} bake and layer nodes for {mat.name}")

        mix_node_name = f"{layer_target}_{LAYER_MIX_SUFFIX}"
        normal_bake_node_name = f"{layer_target}_{BAKE_NORMAL_SUFFIX}"
        ao_bake_node_name = f"{layer_target}_{BAKE_AO_SUFFIX}"
        displacement_bake_node_name = f"{layer_target}_{BAKE_DISPLACEMENT_SUFFIX}"
        normal_layer_node_name = f"{layer_target}_{LAYER_NORMAL_SUFFIX}"
        ao_layer_node_name = f"{layer_target}_{LAYER_AO_SUFFIX}"
        displacement_layer_node_name = f"{layer_target}_{LAYER_DISPLACEMENT_SUFFIX}"

        # remove the mix layer
        mix_node = nodeutils.find_node_by_type_and_keywords(nodes, "GROUP", mix_node_name)
        normal_to_node, normal_to_socket = nodeutils.get_node_and_socket_connected_to_output(mix_node, "Color")
        normal_from_node, normal_from_socket = nodeutils.get_node_and_socket_connected_to_input(mix_node, "Color1")
        ao_to_node, ao_to_socket = nodeutils.get_node_and_socket_connected_to_output(mix_node, "AO")
        ao_from_node, ao_from_socket = nodeutils.get_node_and_socket_connected_to_input(mix_node, "AO1")

        if mix_node:
            nodes.remove(mix_node)
            if normal_from_socket and normal_to_socket:
                nodeutils.link_nodes(links, normal_from_node, normal_from_socket, normal_to_node, normal_to_socket)
            if ao_from_socket and ao_to_socket:
                nodeutils.link_nodes(links, ao_from_node, ao_from_socket, ao_to_node, ao_to_socket)

        # remove the image nodes
        for node_name in [normal_bake_node_name, normal_layer_node_name,
                          ao_bake_node_name, ao_layer_node_name,
                          displacement_bake_node_name, displacement_layer_node_name]:
            node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", node_name)
            if node:
                nodes.remove(node)


def flatten_bake_layers(context, chr_cache):
    prefs = vars.prefs()

    bake_dir = get_bake_dir(chr_cache)
    prefix = chr_cache.character_name + "_Flattened"

    context_obj = utils.get_context_mesh(context)
    if context_obj:
        for mat in context_obj.data.materials:
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            sculpt_mix_node_name = f"{LAYER_TARGET_SCULPT}_{LAYER_MIX_SUFFIX}"
            detail_mix_node_name = f"{LAYER_TARGET_DETAIL}_{LAYER_MIX_SUFFIX}"
            sculpt_mix_node = nodeutils.find_node_by_type_and_keywords(nodes, "GROUP", sculpt_mix_node_name)
            detail_mix_node = nodeutils.find_node_by_type_and_keywords(nodes, "GROUP", detail_mix_node_name)
            mix_node = detail_mix_node if detail_mix_node else sculpt_mix_node

            if mix_node:

                # bake the full layer outputs
                flattened_normal_image = bake.bake_node_socket_output(context, mix_node, "Color", mat, "Normal", bake_dir,
                                            name_prefix=prefix, exact_name=True,
                                            underscores=True, unique_name=True)
                flattened_ao_image = bake.bake_node_socket_output(context, mix_node, "AO", mat, "AO", bake_dir,
                                            name_prefix=prefix, exact_name=True,
                                            underscores=True, unique_name=True)

                normal_image_node = None
                ao_image_node = None

                # determine the source Normal and AO image nodes.
                if (sculpt_mix_node and detail_mix_node) or sculpt_mix_node:
                    normal_image_node = nodeutils.get_node_connected_to_input(sculpt_mix_node, "Color1")
                    ao_image_node = nodeutils.get_node_connected_to_input(sculpt_mix_node, "AO1")
                elif detail_mix_node:
                    normal_image_node = nodeutils.get_node_connected_to_input(detail_mix_node, "Color1")
                    ao_image_node = nodeutils.get_node_connected_to_input(detail_mix_node, "AO1")

                # change the Normal image, or create a new Normal node
                if normal_image_node and normal_image_node.type == "TEX_IMAGE":
                    normal_image_node.image = flattened_normal_image
                else:
                    normal_node_name = f"FLATTENED_{LAYER_NORMAL_SUFFIX}"
                    normal_image_node = nodeutils.create_custom_image_node(nodes, normal_node_name, flattened_normal_image,
                                                     location=mathutils.Vector((-500, -1200)))

                # change the AO image, or create a new AO node
                if ao_image_node and ao_image_node.type == "TEX_IMAGE":
                    ao_image_node.image = flattened_ao_image
                else:
                    ao_node_name = f"FLATTENED_{LAYER_AO_SUFFIX}"
                    ao_image_node = nodeutils.create_custom_image_node(nodes, ao_node_name, flattened_ao_image,
                                                     location=mathutils.Vector((-500, -1500)))

                # reconnect the image nodes to the sculpt layer mix nodes
                # (these will be reconnected when cleaning up the sculpt layers)
                if (sculpt_mix_node and detail_mix_node) or sculpt_mix_node:
                    nodeutils.link_nodes(links, normal_image_node, "Color", sculpt_mix_node, "Color1")
                    nodeutils.link_nodes(links, ao_image_node, "Color", sculpt_mix_node, "AO1")
                elif detail_mix_node:
                    nodeutils.link_nodes(links, normal_image_node, "Color", detail_mix_node, "Color1")
                    nodeutils.link_nodes(links, ao_image_node, "Color", detail_mix_node, "AO1")


    clean_multires_sculpt(context, chr_cache, LAYER_TARGET_DETAIL)
    clean_multires_sculpt(context, chr_cache, LAYER_TARGET_SCULPT)


def get_layer_target_mesh(context, chr_cache, layer_target):
    mesh = None
    context_object = utils.get_context_mesh(context)
    if layer_target == LAYER_TARGET_DETAIL:
        mesh = chr_cache.get_detail_body(context_object=context_object)
    elif layer_target == LAYER_TARGET_SCULPT:
        mesh = chr_cache.get_sculpt_body(context_object=context_object)
    return mesh


def set_layer_target_mesh(chr_cache, layer_target, mesh):
    if layer_target == LAYER_TARGET_DETAIL:
        chr_cache.set_detail_body(mesh)
    elif layer_target == LAYER_TARGET_SCULPT:
        chr_cache.set_sculpt_body(mesh)
    return mesh


def set_sculpt_source(multires_mesh, layer_target, source_object):
    prop_name = f"rl_multires_{layer_target}"
    if utils.object_exists_is_mesh(source_object) and utils.object_exists_is_mesh(multires_mesh):
        multires_mesh[prop_name] = source_object.name


def bake_multires_sculpt(context, chr_cache, layer_target, apply_shape=False):
    multires_mesh = get_layer_target_mesh(context, chr_cache, layer_target)
    multires_source = chr_cache.get_sculpt_source(multires_mesh, layer_target)
    utils.unhide(multires_mesh)
    # make sure to go into object mode otherwise the sculpt is not applied.
    if utils.object_mode_to(multires_mesh):
        setup_bake_nodes(context, chr_cache, multires_mesh, layer_target)
        do_multires_bake(context, chr_cache, multires_mesh, layer_target, apply_shape=apply_shape, source_body=multires_source)
        save_skin_gen_bake(chr_cache, multires_mesh, layer_target)
        finish_bake(chr_cache, multires_mesh, layer_target)
        end_multires_sculpting(context, chr_cache, layer_target, show_baked = True)


def set_hide_character(chr_cache, hide):
    arm = chr_cache.get_armature()
    for obj in chr_cache.get_all_objects(include_armature=True,
                                         include_children=True):
        if not hide and chr_cache.is_sculpt_object(obj):
            # always hide the sculpt objects
            utils.hide(obj, True)
        else:
            utils.hide(obj, hide)
    utils.hide(arm, hide)


def begin_multires_sculpting(context, chr_cache, layer_target):
    # get the context sculpt target
    multi_res_mesh = get_layer_target_mesh(context, chr_cache, layer_target)
    # update the last used sculpt target
    set_layer_target_mesh(chr_cache, layer_target, multi_res_mesh)
    # begin
    if utils.object_exists_is_mesh(multi_res_mesh):
        set_hide_character(chr_cache, True)
        utils.unhide(multi_res_mesh)
        utils.object_mode()
        utils.set_only_active_object(multi_res_mesh)
        #bpy.ops.view3d.view_selected()
        # TODO mute the detail normal mix nodes (so the normal overlay isn't shown when sculpting)
        utils.set_mode("SCULPT")
        shading = utils.get_view_3d_shading(context)
        if shading:
            try:
                shading.type = 'SOLID'
                shading.light = 'MATCAP'
                shading.studio_light = 'basic_1.exr'
                shading.show_cavity = True
            except: ...


def end_multires_sculpting(context, chr_cache, layer_target, multires_mesh=None, show_baked = False):
    if not multires_mesh:
        multires_mesh = get_layer_target_mesh(context, chr_cache, layer_target)
    if utils.object_exists_is_mesh(multires_mesh):
        sculpt_source = chr_cache.get_sculpt_source(multires_mesh, layer_target)
        body_objects = chr_cache.get_objects_of_type(LAYER_TARGET_SCULPT)
        if show_baked:
            set_multi_res_level(multires_mesh, view_level=0)
        else:
            set_multi_res_level(multires_mesh, view_level=9)
        utils.object_mode()
        set_hide_character(chr_cache, False)
        utils.hide(multires_mesh)
        if sculpt_source:
            utils.set_only_active_object(sculpt_source)
        else:
            utils.try_select_objects(body_objects)
        shading = utils.get_view_3d_shading(context)
        if shading:
            shading.type = 'MATERIAL'


def clean_multires_sculpt(context, chr_cache, layer_target):
    multires_mesh = get_layer_target_mesh(context, chr_cache, layer_target)
    if multires_mesh:
        end_multires_sculpting(context, chr_cache, layer_target, multires_mesh=multires_mesh, show_baked = True)
        remove_bake_nodes(context, chr_cache, layer_target, multires_mesh)
        remove_multires_body(context, chr_cache, layer_target, multires_mesh)


def remove_multires_body(context, chr_cache, layer_target, multires_mesh):
    if multires_mesh:
        utils.delete_mesh_object(multires_mesh)
    if layer_target == LAYER_TARGET_DETAIL and chr_cache.detail_multires_body == multires_mesh:
        chr_cache.set_detail_body(None)
    elif layer_target == LAYER_TARGET_SCULPT and chr_cache.sculpt_multires_body == multires_mesh:
        chr_cache.set_sculpt_body(None)


def hide_body_parts(chr_cache):
    prefs = vars.prefs()

    body_objects = chr_cache.get_objects_of_type("BODY")

    for body in body_objects:
        hide_slots = []

        for i in range(0, len(body.material_slots)):
            slot = body.material_slots[i]
            mat = slot.material
            if mat:
                mat_cache = chr_cache.get_material_cache(mat)
                # hide eyelashes and nails
                if (mat_cache.material_type == "NAILS" or
                    mat_cache.material_type == "EYELASH"):
                    hide_slots.append(i)

        utils.object_mode()
        utils.clear_selected_objects()
        if utils.edit_mode_to(body):
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            bpy.ops.mesh.select_all(action='DESELECT')
            for slot_index in hide_slots:
                bpy.context.object.active_material_index = slot_index
                bpy.ops.object.material_slot_select()
                bpy.ops.mesh.hide(unselected=False)
        utils.object_mode()


def add_multires_mesh(context, chr_cache, layer_target, sub_target = "ALL"):
    prefs = vars.prefs()
    context = vars.get_context(context=context)

    # duplicate the body
    context_object = utils.get_context_mesh(context)
    body_cache = chr_cache.get_body_cache()
    body_id = body_cache.object_id if body_cache else None
    body_objects = chr_cache.get_objects_of_type("BODY")
    cache_objects = chr_cache.get_cache_objects()
    is_body_type = body_id and utils.get_rl_object_id(context_object) == body_id

    multires_mesh = None
    multires_source = None

    # if the body object has been split, assume the user wants to keep their split
    # for sculpting, only split the object when the full body is present.

    if len(body_objects) == 1 and is_body_type:

        body = body_objects[0]
        multires_mesh = utils.duplicate_object(body)
        multires_source = body

        # split the objects by material
        utils.clear_selected_objects()
        utils.edit_mode_to(multires_mesh)
        bpy.ops.mesh.separate(type='MATERIAL')
        objects = context.selected_objects.copy()
        rejoin = []

        # delete the material parts not wanted by the sculpt target
        for obj in objects:
            if len(obj.material_slots) > 0:
                mat = obj.material_slots[0].material
                mat_cache = chr_cache.get_material_cache(mat)
                remove = False

                if mat and mat_cache:

                    # always remove eyelashes and nails
                    if (mat_cache.material_type == "NAILS" or
                        mat_cache.material_type == "EYELASH"):
                        remove = True

                    if sub_target == "BODY":
                        # remove head
                        if mat_cache.material_type == "SKIN_HEAD":
                            remove = True

                    elif sub_target == "HEAD":
                        # remove everything but head
                        if mat_cache.material_type != "SKIN_HEAD":
                            remove = True

                if remove:
                    utils.delete_mesh_object(obj)
                else:
                    rejoin.append(obj)

        # rejoin the remaining objects
        utils.try_select_objects(rejoin, True)
        multires_mesh = rejoin[0]
        utils.set_active_object(multires_mesh)
        bpy.ops.object.join()

    else:

        if context_object in cache_objects:
            body = context_object
            multires_mesh = utils.duplicate_object(body)
            multires_source = body

    if multires_mesh and utils.set_only_active_object(multires_mesh):

        # remove doubles
        if utils.edit_mode_to(multires_mesh):
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()

        if utils.object_mode_to(multires_mesh):

            # remove all modifiers
            multires_mesh.modifiers.clear()

            # remove all shapekeys
            if utils.object_has_shape_keys(multires_mesh):
                bpy.ops.object.shape_key_remove(all=True)

            # unparent and keep transform
            #bpy.ops.object.parent_clear(type = "CLEAR_KEEP_TRANSFORM")

            if layer_target == LAYER_TARGET_DETAIL:
                sculpt_level = prefs.detail_multires_level
            elif layer_target == LAYER_TARGET_SCULPT:
                sculpt_level = prefs.sculpt_multires_level
            else:
                sculpt_level = 2

            # add multi-res modifier
            modifiers.add_multi_res_modifier(multires_mesh, sculpt_level, use_custom_normals=True, quality=6)

        # store the references
        set_layer_target_mesh(chr_cache, layer_target, multires_mesh)
        if layer_target == LAYER_TARGET_DETAIL:
            chr_cache.detail_sculpt_sub_target = sub_target

        multires_mesh.name = body.name + "_" + layer_target
        set_sculpt_source(multires_mesh, layer_target, multires_source)

    return multires_mesh


def setup_multires_sculpt(context, chr_cache, layer_target):
    props = vars.props()
    prefs = vars.prefs()

    if chr_cache:

        multires_mesh = get_layer_target_mesh(context, chr_cache, layer_target)

        if layer_target == LAYER_TARGET_DETAIL:

            detail_sculpt_sub_target = chr_cache.detail_sculpt_sub_target

            if multires_mesh and detail_sculpt_sub_target == prefs.detail_sculpt_sub_target:
                begin_multires_sculpting(context, chr_cache, layer_target)

            elif multires_mesh and detail_sculpt_sub_target != prefs.detail_sculpt_sub_target:
                remove_multires_body(context, chr_cache, layer_target, multires_mesh)
                multires_mesh = add_multires_mesh(context, chr_cache, layer_target, prefs.detail_sculpt_sub_target)
                begin_multires_sculpting(context, chr_cache, layer_target)

            elif multires_mesh is None:
                multires_mesh = add_multires_mesh(context, chr_cache, layer_target, prefs.detail_sculpt_sub_target)
                begin_multires_sculpting(context, chr_cache, layer_target)

        elif layer_target == LAYER_TARGET_SCULPT:

            if multires_mesh:
                begin_multires_sculpting(context, chr_cache, layer_target)

            else:
                multires_mesh = add_multires_mesh(context, chr_cache, layer_target)
                begin_multires_sculpting(context, chr_cache, layer_target)


class CC3OperatorSculpt(bpy.types.Operator):
    """Sculpt Functions"""
    bl_idname = "cc3.sculpting"
    bl_label = "Sculpting Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):
        props = vars.props()
        prefs = vars.prefs()

        chr_cache = props.get_context_character_cache(context)

        if self.param == "DETAIL_SETUP":
            setup_multires_sculpt(context, chr_cache, LAYER_TARGET_DETAIL)

        elif self.param == "DETAIL_BEGIN":
            begin_multires_sculpting(context, chr_cache, LAYER_TARGET_DETAIL)

        elif self.param == "DETAIL_END":
            end_multires_sculpting(context, chr_cache, LAYER_TARGET_DETAIL)

        elif self.param == "DETAIL_BAKE":
            bake_multires_sculpt(context, chr_cache, LAYER_TARGET_DETAIL)

        elif self.param == "DETAIL_CLEAN":
            clean_multires_sculpt(context, chr_cache, LAYER_TARGET_DETAIL)

        if self.param == "BODY_SETUP":
            setup_multires_sculpt(context, chr_cache, LAYER_TARGET_SCULPT)

        elif self.param == "BODY_BEGIN":
            begin_multires_sculpting(context, chr_cache, LAYER_TARGET_SCULPT)

        elif self.param == "BODY_END":
            end_multires_sculpting(context, chr_cache, LAYER_TARGET_SCULPT)

        elif self.param == "BODY_BAKE":
            if chr_cache.multires_bake_apply:
                bake_multires_sculpt(context, chr_cache, LAYER_TARGET_SCULPT,
                                     apply_shape=True)
            else:
                bake_multires_sculpt(context, chr_cache, LAYER_TARGET_SCULPT)

        elif self.param == "BODY_CLEAN":
            clean_multires_sculpt(context, chr_cache, LAYER_TARGET_SCULPT)

        elif self.param == "FLATTEN_LAYERS":
            flatten_bake_layers(context, chr_cache)
            pass

        elif self.param == "RESET_FROM_SOURCE":
            pass

        elif self.param == "STORE_LASH":
            meshutils.store_lash_data(chr_cache)

        elif self.param == "FIX_LASH":
            meshutils.restore_lash_data(chr_cache)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "DETAIL_SETUP":
            return "Set up and begin detail sculpting for the character.\n\n" \
                   "Detail sculpting is done on a reduced copy of the character and sculpted normals are baked back and overlayed on the original character.\n\n" \
                   "Note: This does not make any changes to the mesh of the original character.\n\n" \
                   "Warning: It is very important that you *do not* apply the base shape yourself in the multi-res modifier"
        elif properties.param == "DETAIL_BEGIN":
            return "Resume detail sculpting for the character.\n\n" \
                   "Detail sculpting is done on a reduced copy of the character and sculpted normals are baked back and overlayed on the original character.\n\n" \
                   "Note: This does not make any changes to the mesh of the original character.\n\n" \
                   "Warning: It is very important that you *do not* apply the base shape yourself in the multi-res modifier"
        elif properties.param == "DETAIL_END":
            return "Stop detail sculpting and return to the original character"
        elif properties.param == "DETAIL_BAKE":
            return "Bake the detail sculpt normals and masks and overlay on the original character.\n\n" \
                   "The original character's mesh is *not* altered.\n\n" \
                   "The normal overlays are masked to show only the areas that have been sculpted on, so minor changes due to multi-res subdivision should not cause any additional distortion.\n\n" \
                   "Once baked, the detail normals can be exported as a separate layer for Skin-Gen in Charactrer Creator"
        elif properties.param == "DETAIL_CLEAN":
            return "Removes the detail sculpt and normal layers"

        elif properties.param == "BODY_SETUP":
            return "Set up and begin full body sculpting for the character.\n\n" \
                   "Body sculpting is done on a reduced copy of the character (Only the Head, Body, Arms and Legs) and sculpted normals are baked back and overlayed on the original character.\n\n" \
                   "Note: This does not make any changes to the mesh of the original character.\n\n" \
                   "Warning: It is very important that you *do not* apply the base shape yourself in the multi-res modifier"
        elif properties.param == "BODY_BEGIN":
            return "Resume full body sculpting for the character.\n\n" \
                   "Body sculpting is done on a reduced copy of the character (Only the Head, Body, Arms and Legs) and sculpted normals are baked back and overlayed on the original character.\n\n" \
                   "Note: This does not make any changes to the mesh of the original character.\n\n" \
                   "Warning: It is very important that you *do not* apply the base shape yourself in the multi-res modifier"
        elif properties.param == "BODY_END":
            return "Stop body sculpting and return to the original character"
        elif properties.param == "BODY_BAKE":
            return "Bake the body sculpt normals and masks and overlay on the original character.\n\n" \
                   "Optionally, the multi-res base shape can by copied back to the original character, in a way that does not destroy the shape-keys.\n\n" \
                   "The normal overlays are masked to show only the areas that have been sculpted on, so minor changes due to multi-res subdivision should not cause any additional distortion.\n\n" \
                   "Once baked, the body normals can be exported as a separate layer for Skin-Gen in Charactrer Creator"
        elif properties.param == "BODY_CLEAN":
            return "Removes the body sculpt and normal layers"

        return ""


class CC3OperatorSculptExport(bpy.types.Operator):
    """Export Sculpt Layers"""
    bl_idname = "cc3.sculpt_export"
    bl_label = "Export Layer"
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting the layers",
        maxlen=1024,
        subtype='FILE_PATH',
        )

    filename_ext = ".png"  # ExportHelper mixin class uses this

    filter_glob: bpy.props.StringProperty(
        default="*.png;*.jpg",
        options={"HIDDEN"},
        )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    def execute(self, context):
        props = vars.props()
        prefs = vars.prefs()

        chr_cache = props.get_context_character_cache(context)

        if self.param == "DETAIL_SKINGEN":
            export_skingen(context, chr_cache, LAYER_TARGET_DETAIL, self.filepath)

        elif self.param == "BODY_SKINGEN":
            export_skingen(context, chr_cache, LAYER_TARGET_SCULPT, self.filepath)

        return {"FINISHED"}


    def invoke(self, context, event):
        prefs = vars.prefs()
        props = vars.props()
        chr_cache = props.get_context_character_cache(context)

        export_format = "png"

        # determine default file name
        if not self.filepath:
            default_file_path = context.blend_data.filepath
            if not default_file_path:
                if self.param == "DETAIL_SKINGEN":
                    default_file_path = "detail_layer"
                else:
                    default_file_path = "body_layer"
            else:
                default_file_path = os.path.splitext(default_file_path)[0]
            self.filepath = default_file_path + self.filename_ext

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


    def check(self, context):
        change_ext = False
        filepath = self.filepath
        if os.path.basename(filepath):
            base, ext = os.path.splitext(filepath)
            if ext != self.filename_ext:
                filepath = bpy.path.ensure_ext(base, self.filename_ext)
            else:
                filepath = bpy.path.ensure_ext(filepath, self.filename_ext)
            if filepath != self.filepath:
                self.filepath = filepath
                change_ext = True
        return change_ext

    @classmethod
    def description(cls, context, properties):

        if properties.param == "DETAIL_SKINGEN":
            return "Export the detail sculpt layer normal maps and masks"
        elif properties.param == "BODY_SKINGEN":
            return "Export the body sculpt normal normal maps and masks"
        return ""