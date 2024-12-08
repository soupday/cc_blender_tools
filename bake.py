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
import os
from mathutils import Vector
from . import normal, colorspace, imageutils, wrinkle, nodeutils, properties, materials, utils, params, vars
from .exporter import get_export_objects

BAKE_SAMPLES = 4
BAKE_INDEX = 1001
BUMP_BAKE_MULTIPLIER = 2.0
NODE_CURSOR = Vector((0, 0))

def init_bake(id = 1001):
    global BAKE_INDEX
    BAKE_INDEX = id


def set_cycles_samples(context, samples, adaptive_samples = -1, denoising = False, time_limit = 0, use_gpu = False):
    if not context:
        context = bpy.context

    context.scene.cycles.samples = samples
    if utils.B300():
        context.scene.cycles.device = 'GPU' if use_gpu else 'CPU'
        context.scene.cycles.preview_samples = samples
        context.scene.cycles.use_adaptive_sampling = adaptive_samples >= 0
        context.scene.cycles.adaptive_threshold = adaptive_samples
        context.scene.cycles.use_preview_adaptive_sampling = adaptive_samples >= 0
        context.scene.cycles.preview_adaptive_threshold = adaptive_samples
        context.scene.cycles.use_denoising = denoising
        context.scene.cycles.use_preview_denoising = denoising
        context.scene.cycles.use_auto_tile = False
        context.scene.cycles.time_limit = time_limit


def prep_bake(context, mat: bpy.types.Material=None, samples=BAKE_SAMPLES, image_format="PNG", make_surface=True):
    bake_state = {}
    if not context:
        context = bpy.context

    # cycles settings
    bake_state["samples"] = context.scene.cycles.samples
    # Blender 3.0
    if utils.B300():
        bake_state["preview_samples"] = context.scene.cycles.preview_samples
        bake_state["use_adaptive_sampling"] = context.scene.cycles.use_adaptive_sampling
        bake_state["use_preview_adaptive_sampling"] = context.scene.cycles.use_preview_adaptive_sampling
        bake_state["use_denoising"] = context.scene.cycles.use_denoising
        bake_state["use_preview_denoising"] = context.scene.cycles.use_preview_denoising
        bake_state["use_auto_tile"] =  context.scene.cycles.use_auto_tile
    # render settings
    bake_state["file_format"] = context.scene.render.image_settings.file_format
    bake_state["color_depth"] = context.scene.render.image_settings.color_depth
    bake_state["color_mode"] = context.scene.render.image_settings.color_mode
    bake_state["use_bake_multires"] = context.scene.render.use_bake_multires
    bake_state["use_selected_to_active"] = context.scene.render.bake.use_selected_to_active
    bake_state["use_pass_direct"] = context.scene.render.bake.use_pass_direct
    bake_state["use_pass_indirect"] = context.scene.render.bake.use_pass_indirect
    bake_state["margin"] = context.scene.render.bake.margin
    bake_state["use_clear"] = context.scene.render.bake.use_clear
    bake_state["image_format"] = context.scene.render.image_settings.file_format
    # Blender 2.92
    if utils.B292():
        bake_state["target"] = context.scene.render.bake.target
    # color management
    bake_state["view_transform"] = context.scene.view_settings.view_transform
    bake_state["look"] = context.scene.view_settings.look
    bake_state["gamma"] = context.scene.view_settings.gamma
    bake_state["exposure"] = context.scene.view_settings.exposure
    bake_state["colorspace"] = context.scene.sequencer_colorspace_settings.name

    context.scene.cycles.samples = samples
    context.scene.render.image_settings.file_format = image_format
    context.scene.render.use_bake_multires = False
    context.scene.render.bake.use_selected_to_active = False
    context.scene.render.bake.use_pass_direct = False
    context.scene.render.bake.use_pass_indirect = False
    context.scene.render.bake.margin = 16
    context.scene.render.bake.use_clear = True
    # color management settings affect the baked output so set them to standard/raw defaults:
    context.scene.view_settings.view_transform = 'Standard'
    context.scene.view_settings.look = 'None'
    context.scene.view_settings.gamma = 1
    context.scene.view_settings.exposure = 0
    colorspace.set_sequencer_color_space("Raw")

    # Blender 3.0
    if utils.B300():
        context.scene.cycles.preview_samples = samples
        context.scene.cycles.use_adaptive_sampling = False
        context.scene.cycles.use_preview_adaptive_sampling = False
        context.scene.cycles.use_denoising = False
        context.scene.cycles.use_preview_denoising = False
        context.scene.cycles.use_auto_tile = False

    # Blender 2.92
    if utils.B292():
        context.scene.render.bake.target = 'IMAGE_TEXTURES'

    # go into wireframe mode (so Blender doesn't update or recompile the material shaders while
    # we manipulate them for baking, and also so Blender doesn't fire up the cycles viewport...):
    shading: bpy.types.View3DShading = utils.get_view_3d_shading(context)
    if shading:
        bake_state["shading"] = shading.type
        shading.type = 'WIREFRAME'
    else:
        bake_state["shading"] = 'MATERIAL'
        shading.type = 'WIREFRAME'
    # set cycles rendering mode for baking
    bake_state["engine"] = context.scene.render.engine
    context.scene.render.engine = 'CYCLES'
    bake_state["cycles_bake_type"] = context.scene.cycles.bake_type
    bake_state["render_bake_type"] = context.scene.render.bake_type
    context.scene.cycles.bake_type = "COMBINED"


    if make_surface:

        # deselect everything
        bpy.ops.object.select_all(action='DESELECT')
        # create the baking plane, a single quad baking surface for an even sampling across the entire texture
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        bake_surface = utils.get_active_object()
        bake_state["bake_surface"] = bake_surface
        set_bake_material(bake_state, mat)
        # replicate any material node UV layers in bake surface
        if mat and mat.node_tree and mat.node_tree.nodes:
            for node in mat.node_tree.nodes:
                if node.type == "UVMAP":
                    uv_name = node.uv_map
                    mesh: bpy.types.Mesh = bake_surface.data
                    if uv_name not in mesh.uv_layers:
                        mesh.uv_layers.new(name=uv_name)

    return bake_state


def set_bake_material(bake_state, mat):
    if mat and bake_state and "bake_surface" in bake_state:
        bake_surface = bake_state["bake_surface"]
        if bake_surface:
            # attach the material to bake to the baking surface plane
            # (the baking plane also ensures that only one material is baked onto only one target image)
            if len(bake_surface.data.materials) == 0:
                bake_surface.data.materials.append(mat)
            else:
                bake_surface.data.materials[0] = mat
            bake_state["bake_material"] = mat
            return True
    return False


def post_bake(context, state):
    if not context:
        context = bpy.context

    # cycles settings
    context.scene.cycles.samples = state["samples"]
    # Blender 3.0
    if utils.B300():
        context.scene.cycles.preview_samples = state["preview_samples"]
        context.scene.cycles.use_adaptive_sampling = state["use_adaptive_sampling"]
        context.scene.cycles.use_preview_adaptive_sampling = state["use_preview_adaptive_sampling"]
        context.scene.cycles.use_denoising = state["use_denoising"]
        context.scene.cycles.use_preview_denoising = state["use_preview_denoising"]
        context.scene.cycles.use_auto_tile = state["use_auto_tile"]
    # render settings
    context.scene.render.image_settings.file_format = state["file_format"]
    context.scene.render.image_settings.color_depth = state["color_depth"]
    context.scene.render.image_settings.color_mode = state["color_mode"]
    context.scene.render.use_bake_multires = state["use_bake_multires"]
    context.scene.render.bake.use_selected_to_active = state["use_selected_to_active"]
    context.scene.render.bake.use_pass_direct = state["use_pass_direct"]
    context.scene.render.bake.use_pass_indirect = state["use_pass_indirect"]
    context.scene.render.bake.margin = state["margin"]
    context.scene.render.bake.use_clear = state["use_clear"]
    context.scene.render.image_settings.file_format = state["image_format"]
    # Blender 2.92
    if utils.B292():
        context.scene.render.bake.target = state["target"]
    # color management
    context.scene.view_settings.view_transform = state["view_transform"]
    context.scene.view_settings.look = state["look"]
    context.scene.view_settings.gamma = state["gamma"]
    context.scene.view_settings.exposure = state["exposure"]
    context.scene.sequencer_colorspace_settings.name = state["colorspace"]
    # render engine
    context.scene.render.engine = state["engine"]
    # viewport shading
    shading = utils.get_view_3d_shading(context)
    if shading:
        shading.type = state["shading"]

    # bake type
    context.scene.cycles.bake_type = state["cycles_bake_type"]
    context.scene.render.bake_type = state["render_bake_type"]

    # remove the bake surface
    if "bake_surface" in state:
        bpy.data.objects.remove(state["bake_surface"])


def get_existing_bake_image(mat, channel_id, width, height,
                            shader_node, socket,
                            bake_dir, name_prefix="",
                            force_srgb=False,
                            channel_pack=False,
                            exact_name=False):
    return None


def get_bake_image(mat, channel_id, width, height, shader_node, socket, bake_dir,
                   name_prefix="", force_srgb=False, channel_pack=False,
                   exact_name=False, underscores=True, unique_name=False, image_format="PNG"):
    """Makes an image and image file to bake the shader socket to and returns the image and image name
    """

    global BAKE_INDEX

    sep = " "
    if underscores:
        sep = "_"
    prefix_sep = ""
    if name_prefix:
        prefix_sep = sep

    # determine image name and color space
    socket_name = nodeutils.safe_socket_name(socket)
    if exact_name:
        image_name = name_prefix + prefix_sep + mat.name + sep + channel_id
    else:
        image_name = "EXPORT_BAKE" + sep + name_prefix + prefix_sep + mat.name + sep + channel_id + sep + str(BAKE_INDEX)
        BAKE_INDEX += 1

    is_data = True
    alpha = False
    rgb_sockets = [ "Diffuse", "Diffuse Map", "Base Color", "Emission", "Emission Color", "Subsurface Color" ]
    rgb_channels = [ "Diffuse", "Emission", "BaseMap", "Base Color", "Glow" ]
    if socket_name in rgb_sockets:
        is_data = False
    if channel_id in rgb_channels:
        is_data = False
    if force_srgb:
        is_data = False
    if channel_pack:
        alpha = True

    # make (and save) the target image
    image, exists = get_image_target(image_name, width, height, bake_dir, is_data, alpha,
                                     channel_packed=channel_pack, format=image_format)

    # make sure we don't reuse an image as the target, that is also in the nodes we are baking from...
    i = 0
    base_name = image_name
    if shader_node and socket:
        while nodeutils.is_image_node_connected_to_socket(shader_node, socket, image, []):
            i += 1
            old_name = image_name
            image_name = base_name + "_" + str(i)
            utils.log_info(f"Image: {old_name} in use, trying: {image_name}")
            image, exists = get_image_target(image_name, width, height, bake_dir, is_data, alpha,
                                             channel_packed=channel_pack, format=image_format)

    return image, image_name, exists


def bake_node_socket_input(context, node, socket, mat, channel_id, bake_dir, name_prefix="",
                           override_size=0, size_override_node=None, size_override_socket=None,
                           exact_name=False, underscores=True, unique_name=False,
                           no_prep=False, image_format="PNG"):
    """Bakes the input to the supplied node and socket to an appropriate image.\n
       Image size is determined by the sizes of the connected image nodes (or overriden).\n
       Image name and path is determined by the texture channel id and material name and name prefix.\n
       An alternative size override node and socket can be supplied to determine the size.
       (e.g. matching image sizes with another texture channel)\n
       Returns the image baked."""

    # determine the size of the image to bake onto
    size_node = node
    size_socket = socket
    if size_override_node:
        size_node = size_override_node
    if size_override_socket:
        size_socket = size_override_socket
    width, height = get_connected_texture_size(size_node, override_size, size_socket)

    # get the node and output socket to bake from
    source_node, source_socket = nodeutils.get_node_and_socket_connected_to_input(node, socket)

    # bake the source node output onto the target image and re-save it
    image, image_name, exists = get_bake_image(mat, channel_id, width, height, node, socket, bake_dir,
                                               name_prefix=name_prefix, exact_name=exact_name, unique_name=unique_name,
                                               underscores=underscores, image_format=image_format)
    image_node = cycles_bake_color_output(context, mat, source_node, source_socket, image, image_name,
                                          no_prep=no_prep, image_format=image_format)

    # remove the image node
    if image_node:
        nodes = mat.node_tree.nodes
        nodes.remove(image_node)

    return image


def bake_node_socket_output(context, node, socket, mat, channel_id, bake_dir, name_prefix = "",
                            override_size = 0, size_override_node=None, size_override_socket=None,
                            exact_name=False, underscores=True, unique_name=False,
                            no_prep=False, image_format="PNG"):
    """Bakes the output of the supplied node and socket to an appropriate image.\n
       Image size is determined by the sizes of the connected image nodes (or overriden).\n
       Image name and path is determined by the texture channel id, material name, bake dir and name prefix.\n
       An alternative size override node and socket can be supplied to determine the size.
       (e.g. matching image sizes with another texture channel)\n
       Returns the image baked."""

    # determine the size of the image to bake onto
    size_node = node
    size_socket = socket
    if size_override_node:
        size_node = size_override_node
    if size_override_socket:
        size_socket = size_override_socket
    width, height = get_connected_texture_size(size_node, override_size, size_socket)

    # bake the source node output onto the target image and re-save it
    image, image_name, exists = get_bake_image(mat, channel_id, width, height, node, socket, bake_dir,
                                               name_prefix=name_prefix, exact_name=exact_name, unique_name=unique_name,
                                               underscores=underscores, image_format=image_format)
    image_node = cycles_bake_color_output(context, mat, node, socket, image, image_name,
                                          no_prep=no_prep, image_format=image_format)

    # remove the image node
    if image_node:
        nodes = mat.node_tree.nodes
        nodes.remove(image_node)

    return image


def bake_rl_bump_and_normal(context, shader_node, bsdf_node, mat, channel_id, bake_dir,
                            normal_socket_name="Normal Map", bump_socket_name="Bump Map",
                            normal_strength_socket_name="Normal Strength",
                            bump_distance_socket_name="Bump Strength",
                            name_prefix="", override_size=0, no_prep=False, image_format="PNG"):
    """Bakes the normal map and bump map inputs to the supplied RL master shader node, to a combined
       normal map image which takes the normal and bump strengths into account.\n
       If supplied socket names are empty they will not be included in the bake.\n
       Image size is determined by the sizes of the connected image nodes (or overriden).\n
       Image name and path is determined by the texture channel id, material name, bake dir and name prefix.\n
       An alternative size override node and socket can be supplied to determine the size.
       (e.g. matching image sizes with another texture channel)\n
       Returns the normal image baked."""

    # determine the size of the image to bake onto
    width, height = get_connected_texture_size(shader_node, override_size, normal_socket_name, bump_socket_name)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # store original links to BSDF normal socket
    bsdf_normal_node, bsdf_normal_socket = nodeutils.get_node_and_socket_connected_to_input(bsdf_node, "Normal")
    #
    normal_source_node = None
    normal_source_socket = None
    bump_source_node = None
    bump_source_socket = None
    bump_distance = 0.01
    normal_strength = 1.0
    bump_map_node = None
    normal_map_node = None
    if normal_socket_name:
        if normal_strength_socket_name:
            normal_strength = nodeutils.get_node_input_value(shader_node, normal_strength_socket_name, 1.0)
        normal_source_node, normal_source_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, normal_socket_name)
        normal_map_node = nodeutils.make_normal_map_node(nodes, normal_strength)
        nodeutils.link_nodes(links, normal_source_node, normal_source_socket, normal_map_node, "Color")
        nodeutils.link_nodes(links, normal_map_node, "Normal", bsdf_node, "Normal")
    if bump_socket_name:
        if bump_distance_socket_name:
            bump_distance = nodeutils.get_node_input_value(shader_node, bump_distance_socket_name, 0.01) * BUMP_BAKE_MULTIPLIER
        bump_source_node, bump_source_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, bump_socket_name)
        # the bump map bakes to a normal map quite a bit weaker than it looks on the bump node, so increase it's strength here
        bump_map_node = nodeutils.make_bump_node(nodes, 1, bump_distance)
        nodeutils.link_nodes(links, bump_source_node, bump_source_socket, bump_map_node, "Height")
        if normal_map_node:
            nodeutils.link_nodes(links, normal_map_node, "Normal", bump_map_node, "Normal")
        nodeutils.link_nodes(links, bump_map_node, "Normal", bsdf_node, "Normal")

    # bake the source node output onto the target image and re-save it
    image, image_name, exists = get_bake_image(mat, channel_id, width, height,
                                               shader_node, normal_socket_name, bake_dir,
                                               name_prefix=name_prefix, image_format=image_format)
    image_node = cycles_bake_normal_output(context, mat, bsdf_node, image, image_name,
                                           no_prep=no_prep, image_format=image_format)

    # remove the bake nodes and restore the normal links to the bsdf
    if bump_map_node:
        nodes.remove(bump_map_node)
    if normal_map_node:
        nodes.remove(normal_map_node)
    if image_node:
        nodes.remove(image_node)
    nodeutils.link_nodes(links, bsdf_normal_node, bsdf_normal_socket, bsdf_node, "Normal")

    return image


def bake_bsdf_normal(context, bsdf_node, mat, channel_id, bake_dir,
                     name_prefix = "", override_size = 0,
                     no_prep = False, image_format="PNG"):
    """Bakes the normal output of the supplied BSDF shader node, to a normal map image.\n
       Image size is determined by the sizes of the connected image nodes (or overriden).\n
       Image name and path is determined by the texture channel id, material name, bake dir and name prefix.\n
       Returns the normal image baked."""

    # determine the size of the image to bake onto
    width, height = get_connected_texture_size(bsdf_node, override_size, "Normal")

    # get the node and output socket to bake from
    nodes = mat.node_tree.nodes

    # double the bump distance for baking
    bump_distance = 0.01
    normal_input_node, normal_input_socket = nodeutils.get_node_and_socket_connected_to_input(bsdf_node, "Normal")
    if normal_input_node and normal_input_node.type == "BUMP":
        bump_distance = nodeutils.get_node_input_value(normal_input_node, "Distance", bump_distance)
        nodeutils.set_node_input_value(normal_input_node, "Distance", bump_distance * BUMP_BAKE_MULTIPLIER)

    # bake the source node output onto the target image and re-save it
    image, image_name, exists = get_bake_image(mat, channel_id, width, height, bsdf_node, "Normal", bake_dir,
                                               name_prefix=name_prefix, image_format=image_format)
    image_node = cycles_bake_normal_output(context, mat, bsdf_node, image, image_name,
                                           no_prep=no_prep, image_format=image_format)

    if normal_input_node and normal_input_node.type == "BUMP":
        nodeutils.set_node_input_value(normal_input_node, "Distance", bump_distance)

    if image_node:
        nodes.remove(image_node)

    return image


def pack_value_image(value, mat, channel_id, bake_dir,
                     name_prefix="", size=64, image_format="PNG"):
    """Generates a 64 x 64 texture of a single value. Linear or sRGB depending on channel id.\n
       Image name and path is determined by the texture channel id, material name, bake dir and name prefix."""

    width = size
    height = size
    image, image_name, exists = get_bake_image(mat, channel_id, width, height, None, "", bake_dir,
                                               name_prefix=name_prefix, image_format=image_format)

    image_pixels = list(image.pixels)

    l = len(image_pixels)
    for i in range(0, l, 4):
        image_pixels[i + 0] = value
        image_pixels[i + 1] = value
        image_pixels[i + 2] = value
        image_pixels[i + 3] = 1

    # replace-in-place all the pixels from the list:
    image.pixels[:] = image_pixels
    image.update()
    image.save()
    return image



def pack_RGBA(mat, channel_id, pack_mode, bake_dir,
              image_r=None, image_g=None, image_b=None, image_a=None,
              value_r=0, value_g=0, value_b=0, value_a=0,
              name_prefix="", min_size=64, srgb=False, max_size=0,
              reuse_existing=False, image_format="PNG"):
    """pack_mode = RGB_A, R_G_B_A"""

    width = min_size
    height = min_size

    # get the largest dimensions
    img : bpy.types.Image
    for img in [ image_r, image_g, image_b, image_a ]:
        if img:
            if img.size[0] > width:
                width = img.size[0]
            if img.size[1] > height:
                height = img.size[1]

    if max_size > 0:
        if width > max_size:
            width = max_size
        if height > max_size:
            height = max_size

    utils.log_info(f"Packing {mat.name} for {channel_id} ({width}x{height})")

    # get the bake image
    image, image_name, exists = get_bake_image(mat, channel_id, width, height, None, "", bake_dir,
                                               name_prefix=name_prefix, force_srgb=srgb,
                                               channel_pack=True, exact_name=True,
                                               image_format=image_format)

    # if we are reusing an existing image, return this now
    if image and reuse_existing and exists:
        utils.log_info(f"Resuing existing texture pack {image.name}, not baking.")
        return image

    remove_after = []

    # if all images are not the same size, use resized copies
    if image_r and (image_r.size[0] != width or image_r.size[1] != height):
        image_r = image_r.copy()
        utils.log_info(f"Resizing {image_r.name} for {channel_id}")
        image_r.scale(width, height)
        remove_after.append(image_r)

    if image_g and (image_g.size[0] != width or image_g.size[1] != height):
        image_g = image_g.copy()
        utils.log_info(f"Resizing {image_g.name} for {channel_id}")
        image_g.scale(width, height)
        remove_after.append(image_g)

    if image_b and (image_b.size[0] != width or image_b.size[1] != height):
        image_b = image_b.copy()
        utils.log_info(f"Resizing {image_b.name} for {channel_id}")
        image_b.scale(width, height)
        remove_after.append(image_b)

    if image_a and (image_a.size[0] != width or image_a.size[1] != height):
        image_a = image_a.copy()
        utils.log_info(f"Resizing {image_a.name} for {channel_id}")
        image_a.scale(width, height)
        remove_after.append(image_a)

    r_data = None
    g_data = None
    b_data = None
    a_data = None

    if image_r:
        r_data = image_r.pixels[:]
    if image_g:
        g_data = image_g.pixels[:]
    if image_b:
        b_data = image_b.pixels[:]
    if image_a:
        a_data = image_a.pixels[:]

    image_pixels = list(image.pixels)

    l = len(image_pixels)

    if pack_mode == "RGB_A":
        for i in range(0, l, 4):
            if r_data:
                image_pixels[i] = r_data[i]
                image_pixels[i + 1] = r_data[i + 1]
                image_pixels[i + 2] = r_data[i + 2]
            else:
                image_pixels[i] = value_r
                image_pixels[i + 1] = value_g
                image_pixels[i + 2] = value_b
            if a_data:
                image_pixels[i + 3] = a_data[i]
            else:
                image_pixels[i + 2] = value_a

    elif pack_mode == "R_G_B_A":
        for i in range(0, l, 4):
            if r_data:
                image_pixels[i] = r_data[i]
            else:
                image_pixels[i] = value_r
            if g_data:
                image_pixels[i + 1] = g_data[i]
            else:
                image_pixels[i + 1] = value_g
            if b_data:
                image_pixels[i + 2] = b_data[i]
            else:
                image_pixels[i + 2] = value_b
            if a_data:
                image_pixels[i + 3] = a_data[i]
            else:
                image_pixels[i + 3] = value_a

    image.pixels[:] = image_pixels
    image.update()
    image.save()

    for img in remove_after:
        bpy.data.images.remove(img)

    return image


def cycles_bake_color_output(context, mat, source_node, source_socket,
                             image: bpy.types.Image, image_name,
                             no_prep=False, image_format="PNG"):
    """Runs a cycles bake of the supplied source node and socket output onto the supplied image.\n
       Returns a new image node with the image."""

    if not (utils.material_exists(mat) and source_node and source_socket and image):
        return None

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")
    output_source, output_source_socket = nodeutils.get_node_and_socket_connected_to_input(output_node, "Surface")

    image_node = nodeutils.make_image_node(nodes, image, "bake")
    image_node.name = image_name

    utils.log_info(f"Baking: {image_name} / {source_node.name} / {nodeutils.safe_socket_name(source_socket)}")

    if not no_prep:
        bake_state = prep_bake(context, mat=mat, image_format=image_format, make_surface=True)

    nodeutils.link_nodes(links, source_node, source_socket, output_node, "Surface")
    image_node.select = True
    nodes.active = image_node

    bpy.ops.object.bake(type='COMBINED')

    context.scene.render.image_settings.color_depth = '8'
    context.scene.render.image_settings.color_mode = 'RGB' if image.depth == 24 else 'RGBA'

    image.save_render(filepath = bpy.path.abspath(image.filepath), scene = context.scene)
    image.reload()

    if output_source:
        nodeutils.link_nodes(links, output_source, output_source_socket, output_node, "Surface")

    if not no_prep:
        post_bake(context, bake_state)

    return image_node


def cycles_bake_normal_output(context, mat, bsdf_node, image, image_name,
                              no_prep=False, image_format="PNG"):
    """Runs a cycles bake of the normal output of the supplied BSDF shader node to the supplied image.
       Returns a new image node with the image."""

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")

    image_node = nodeutils.make_image_node(nodes, image, "bake")
    image_node.name = image_name

    utils.log_info("Baking normal: " + image_name)

    if not no_prep:
        bake_state = prep_bake(context, mat=mat, image_format=image_format, make_surface=True)

    nodeutils.link_nodes(links, bsdf_node, "BSDF", output_node, "Surface")
    image_node.select = True
    nodes.active = image_node

    bpy.ops.object.bake(type='NORMAL')

    context.scene.render.image_settings.color_depth = '8'
    context.scene.render.image_settings.color_mode = 'RGB' if image.depth == 24 else 'RGBA'
    image.save_render(filepath = bpy.path.abspath(image.filepath), scene = context.scene)
    image.reload()

    if not no_prep:
        post_bake(context, bake_state)

    return image_node


def get_largest_texture_to_node(node, done):
    """Recursively traverses the input sockets to the supplied node and
       returns the largest found texture dimensions, or [0, 0] if nothing found."""

    largest_width = 0
    largest_height = 0
    for socket in node.inputs:
        if socket.is_linked:
            width, height = get_largest_texture_to_socket(node, socket, done)
            if width > largest_width:
                largest_width = width
            if height > largest_height:
                largest_height = height
    return largest_width, largest_height


def get_largest_texture_to_socket(node, socket, done):
    """Recursively traverses the nodes connected to the supplied node's input socket and
       returns the largest found texture dimensions, or [0, 0] if nothing found."""

    connected_node = nodeutils.get_node_connected_to_input(node, socket)
    if not connected_node or connected_node in done:
        return 0, 0

    done.append(connected_node)

    if connected_node.type == "TEX_IMAGE":
        if connected_node.image:
            return connected_node.image.size[0], connected_node.image.size[1]
        else:
            return 0, 0
    else:
        return get_largest_texture_to_node(connected_node, done)


def get_connected_texture_size(node, override_size, *sockets):
    """Recursively searches through all connected image nodes to the supplied node's input socket(s)
       and returns the largest image dimensions found.\n
       If no connected image nodes found then returns the preferences minimum export texture size.\n
       Returned width and height can be overridden with override_size."""

    prefs = vars.prefs()
    width = 0
    height = 0
    if override_size > 0:
        return override_size, override_size
    for socket in sockets:
        if socket:
            w, h = get_largest_texture_to_socket(node, socket, [])
            if w > width:
                width = w
            if h > height:
                height = h
    if width == 0:
        width = int(prefs.export_texture_size)
    if height == 0:
        height = int(prefs.export_texture_size)
    return width, height


def get_image_target(image_name, width, height, image_dir,
                     is_data = True, has_alpha = False, force_new = False, channel_packed = False,
                     format="PNG"):
    """Returns (image, exists)"""
    depth = 24
    if has_alpha:
        depth = 32
    color_space = "sRGB"
    if is_data:
        color_space = "Non-Color"

    img : bpy.types.Image

    # find an existing image in the same folder, with the same name to reuse:
    if not force_new:
        for img in bpy.data.images:
            # it is expected that the image name is a vary particular prefixed and suffixed name based on the
            # material and texture channel and bake index, thus any duplication of this should mean the same intended image.
            if img and utils.is_name_or_duplication(img.name, image_name):

                img_folder, img_file = os.path.split(bpy.path.abspath(img.filepath))
                same_folder = False
                try:
                    if os.path.samefile(image_dir, img_folder):
                        same_folder = True
                except:
                    same_folder = False

                if same_folder:
                    try:
                        if img.file_format == format and img.depth == depth and img.size[0] == width and img.size[1] == height:
                            utils.log_info(f"Reusing image: {image_name} - {color_space} - {img.file_format}")
                            colorspace.set_image_color_space(img, color_space)
                            if len(img.pixels) > 0:
                                return img, True
                    except:
                        utils.log_info("Bad image: " + img.name)
                    if img:
                        utils.log_info(f"Wrong format: {img.name} / format: {img.file_format} == {format} ?  depth: {str(depth)} == {str(img.depth)} ?")
                        bpy.data.images.remove(img)

    # or if the image file exists (but not in blender yet)
    file = imageutils.find_file_by_name(image_dir, image_name)
    if file:
        img = imageutils.load_image(file, color_space, reuse_existing = False)
        try:
            if img.file_format == format and img.depth == depth and img.size[0] == width and img.size[1] == height:
                colorspace.set_image_color_space(img, color_space)
                utils.log_info(f"Reusing found image file: {img.filepath} - {img.colorspace_settings.name} - {img.format}")
                if len(img.pixels) > 0:
                    return img, True
        except:
            utils.log_info("Bad found image file: " + img.name)
        if img:
            utils.log_info(f"Wrong format: {img.name} / format: {img.file_format} == {format} ?  depth: {str(depth)} == {str(img.depth)} ?")
            bpy.data.images.remove(img)

    # or just make a new one:
    utils.log_info(f"Creating new image: {image_name} size: {str(width)} format: {format}")
    img = imageutils.make_new_image(image_name, width, height, format, image_dir, is_data, has_alpha, channel_packed)
    colorspace.set_image_color_space(img, color_space)
    return img, False


def get_bake_dir(chr_cache):
    bake_path = os.path.join(chr_cache.get_import_dir(), "textures", chr_cache.get_character_id(), "Blender_Baked")
    return bake_path


def combine_normal(context, chr_cache, mat_cache):
    """Combines the normal and bump maps by baking and connecting a new normal map."""

    init_bake(5001)

    mat = mat_cache.material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    mat_name = utils.strip_name(mat.name)
    shader = params.get_shader_name(mat_cache)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader)
    bake_path = get_bake_dir(chr_cache)

    selection = context.selected_objects.copy()
    active = utils.get_active_object()

    if mat_cache.material_type == "DEFAULT" or mat_cache.material_type == "SSS":

        nodeutils.clear_cursor()

        normal_node, normal_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, "Normal Map")
        bump_node, bump_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, "Bump Map")

        if normal_node and bump_node:

            normal_image = bake_rl_bump_and_normal(context, shader_node, bsdf_node, mat, "Normal", bake_path)
            normal_image_name = utils.unique_name("(NORMAL)")
            normal_image_node = nodeutils.make_image_node(nodes, normal_image, normal_image_name)
            nodeutils.link_nodes(links, normal_image_node, "Color", shader_node, "Normal Map")
            nodeutils.unlink_node_output(links, shader_node, "Bump Map")
            mat_cache.parameters.default_normal_strength = 1.0
            nodeutils.set_node_input_value(shader_node, "Normal Strength", 1.0)

        elif bump_node:

            normal_image = bake_rl_bump_and_normal(context, shader_node, bsdf_node, mat, "Normal", bake_path,
                                                   normal_socket_name = "", bump_socket_name = "")
            normal_image_name = utils.unique_name("(NORMAL)")
            normal_image_node = nodeutils.make_image_node(nodes, normal_image, normal_image_name)
            nodeutils.link_nodes(links, normal_image_node, "Color", shader_node, "Normal Map")
            nodeutils.unlink_node_output(links, shader_node, "Bump Map")
            mat_cache.parameters.default_normal_strength = 1.0
            nodeutils.set_node_input_value(shader_node, "Normal Strength", 1.0)

        elif normal_node and normal_node.type != "TEX_IMAGE":

            normal_image = bake_rl_bump_and_normal(context, shader_node, bsdf_node, mat, "Normal", bake_path,
                                                   bump_socket_name = "", bump_distance_socket_name = "")
            normal_image_name = utils.unique_name("(NORMAL)")
            normal_image_node = nodeutils.make_image_node(nodes, normal_image, normal_image_name)
            nodeutils.link_nodes(links, normal_image_node, "Color", shader_node, "Normal Map")
            mat_cache.parameters.default_normal_strength = 1.0
            nodeutils.set_node_input_value(shader_node, "Normal Strength", 1.0)

    utils.try_select_objects(selection, True)
    if active:
        utils.set_active_object(active)


def bake_flow_to_normal(context, chr_cache, mat_cache):
    """Convert's a hair shader's flow map into an approximate normal map."""

    init_bake(4001)

    mat = mat_cache.material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    mat_name = utils.strip_name(mat.name)
    shader = params.get_shader_name(mat_cache)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader)
    bake_dir = mat_cache.get_tex_dir(chr_cache)

    if mat_cache.material_type == "HAIR":

        nodeutils.clear_cursor()

        mode_selection = utils.store_mode_selection_state()

        # get the flow map
        flow_node = nodeutils.get_node_connected_to_input(shader_node, "Flow Map")
        flow_image: bpy.types.Image = flow_node.image

        width = flow_image.size[0]
        height = flow_image.size[1]

        normal_node = None
        normal_image = None

        # try to re-use normal map
        if nodeutils.has_connected_input(shader_node, "Normal Map"):
            normal_node = nodeutils.get_node_connected_to_input(shader_node, "Normal Map")

            if normal_node and normal_node.image:
                normal_image: bpy.types.Image = normal_node.image

                try:

                    utils.log_info("Found existing normal image: " + normal_image.name + ": " + normal_image.filepath)
                    if normal_image.size[0] != width or normal_image.size[1] != height:
                        utils.log_info("Resizing normal image: " + str(width) + " x " + str(height))
                        normal_image.scale(width, height)

                except:

                    utils.log_info("Removing bad normal image: " + normal_image.name)
                    bpy.data.images.remove(normal_image)

        # if no existing normal image, create one and link it to the shader
        if not normal_image:
            utils.log_info("Creating new normal image.")
            normal_image = imageutils.make_new_image(mat_name + "_Normal", width, height, "PNG", bake_dir, True, False, False)
        if not normal_node:
            utils.log_info("Creating new normal image node.")
            normal_node = nodeutils.make_image_node(nodes, normal_image, "Generated Normal Map")
            nodeutils.link_nodes(links, normal_node, "Color", shader_node, "Normal Map")

        # convert the flow map to a normal map
        tangent = mat_cache.parameters.hair_tangent_vector
        flip_y = mat_cache.parameters.hair_tangent_flip_green > 0
        utils.log_info("Converting Flow Map to Normal Map...")
        convert_flow_to_normal(flow_image, normal_image, tangent, flip_y)

        utils.restore_mode_selection_state(mode_selection)


def convert_flow_to_normal(flow_image: bpy.types.Image, normal_image: bpy.types.Image, tangent, flip_y):

    # fetching a copy of the normal pixels as a list gives us the fastest write speed:
    normal_pixels = list(normal_image.pixels)
    # fetching the flow pixels as a tuple with slice notation gives the fastest read speed:
    flow_pixels = flow_image.pixels[:]

    #tangent_vector = Vector(tangent)

    if flip_y:
        flip = -1
    else:
        flip = 1

    l = len(flow_pixels)
    for i in range(0, l, 4):

        # rgb -> flow_vector
        flow_vector = Vector((flow_pixels[i + 0] * 2 - 1,
                             (flow_pixels[i + 1] * 2 - 1) * flip,
                              flow_pixels[i + 2] * 2 - 1))
        tangent_vector = Vector((-flow_vector.y, flow_vector.x, 0))

        # calculate normal vector
        normal_vector = flow_vector.cross(tangent_vector)
        normal_vector.x *= 0.35
        normal_vector.y *= 0.35
        normal_vector.normalize()

        # normal_vector -> rgb
        normal_pixels[i + 0] = (normal_vector[0] + 1) / 2
        normal_pixels[i + 1] = (normal_vector[1] + 1) / 2
        normal_pixels[i + 2] = (normal_vector[2] + 1) / 2
        normal_pixels[i + 3] = 1

    # replace-in-place all the pixels from the list:
    normal_image.pixels[:] = normal_pixels
    normal_image.update()
    normal_image.save()




def pack_rgb_a(mat, bake_dir, channel_id, shader_node, pack_node_id,
               rgb_id, a_id, rgb_socket, a_socket, rgb_default, a_default,
               srgb=False, max_size=0, reuse_existing=False, image_format="PNG"):
    """Pack 2 textures into the RGB and A channels of a single texture."""

    global NODE_CURSOR

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    rgb_node = None
    a_node = None
    pack_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", f"({pack_node_id})")

    if rgb_id:
        rgb_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", f"({rgb_id})")
    if a_id:
        a_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", f"({a_id})")

    if rgb_node and a_node:

        rgb_tiling_node = nodeutils.get_node_connected_to_input(rgb_node, "Vector")
        a_tiling_node = nodeutils.get_node_connected_to_input(a_node, "Vector")

        if not pack_node:
            if rgb_node and a_node:
                image = pack_RGBA(mat, channel_id, "RGB_A", bake_dir,
                                  image_r=rgb_node.image, image_a=a_node.image,
                                  value_r=rgb_default, value_g=rgb_default,
                                  value_b=rgb_default, value_a=a_default,
                                  srgb=srgb, max_size=max_size, reuse_existing=reuse_existing,
                                  image_format=image_format)
                pack_node = nodeutils.make_image_node(nodes, image, f"({pack_node_id})")

        n = nodeutils.closest_to(shader_node, Vector((-1, -0.25)), rgb_node, a_node)
        pack_node.location = n.location
        if rgb_node:
            nodeutils.link_nodes(links, pack_node, "Color", shader_node, rgb_socket)
            rgb_node.location = NODE_CURSOR
            NODE_CURSOR += Vector((0,-300))
        if a_node:
            nodeutils.link_nodes(links, pack_node, "Alpha", shader_node, a_socket)
            a_node.location = NODE_CURSOR
            NODE_CURSOR += Vector((0,-300))

        tiling_node = None
        if rgb_tiling_node and a_tiling_node:
            nodes.remove(a_tiling_node)
            tiling_node = rgb_tiling_node
            nodeutils.unlink_node_output(links, tiling_node, "Vector")
        elif rgb_tiling_node:
            tiling_node = rgb_tiling_node
        else:
            tiling_node = a_tiling_node

        if tiling_node:
            tiling_node.location = pack_node.location + Vector((-300,0))
            nodeutils.link_nodes(links, tiling_node, "Vector", pack_node, "Vector")


def pack_r_g_b_a(mat, bake_dir, channel_id, shader_node, pack_node_id,
                 r_id, g_id, b_id, a_id,
                 r_socket, g_socket, b_socket, a_socket,
                 r_default, g_default, b_default, a_default,
                 srgb=False, max_size=0, reuse_existing=False,
                 image_format="PNG"):
    """Pack 4 textures into the RGBA channels of a single texture."""

    global NODE_CURSOR
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    r_node = None
    g_node = None
    b_node = None
    a_node = None
    r_image = None
    g_image = None
    b_image = None
    a_image = None
    pack_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", f"({pack_node_id})")
    sep_node = nodeutils.find_node_by_keywords(nodes, pack_node_id + "_SPLIT")

    if r_id:
        r_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", f"({r_id})")
        if r_node:
            r_image = r_node.image
    if g_id:
        g_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", f"({g_id})")
        if g_node:
            g_image = g_node.image
    if b_id:
        b_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", f"({b_id})")
        if b_node:
            b_image = b_node.image
    if a_id:
        a_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", f"({a_id})")
        if a_node:
            a_image = a_node.image

    if utils.count_maps(r_node, g_node, b_node, a_node) > 1:

        if not pack_node:
            image = pack_RGBA(mat, channel_id, "R_G_B_A", bake_dir,
                              image_r=r_image, image_g=g_image,
                              image_b=b_image, image_a=a_image,
                              value_r=r_default, value_g=g_default,
                              value_b=b_default, value_a=a_default,
                              srgb=srgb, max_size=max_size, reuse_existing=reuse_existing,
                              image_format=image_format)
            pack_node = nodeutils.make_image_node(nodes, image, f"({pack_node_id})")

        if not sep_node:
            sep_node = nodeutils.make_separate_rgb_node(nodes, "Pack Split", f"({pack_node_id}_SPLIT)")

        n = nodeutils.closest_to(shader_node, Vector((-1, -0.25)), r_node, g_node, b_node, a_node)
        pack_node.location = n.location
        sep_node.location = pack_node.location + Vector((275, 69))
        nodeutils.link_nodes(links, pack_node, "Color", sep_node, "Image")
        if r_node:
            nodeutils.link_nodes(links, sep_node, "R", shader_node, r_socket)
            r_node.location = NODE_CURSOR
            NODE_CURSOR += Vector((0,-300))
        if g_node:
            nodeutils.link_nodes(links, sep_node, "G", shader_node, g_socket)
            g_node.location = NODE_CURSOR
            NODE_CURSOR += Vector((0,-300))
        if b_node:
            nodeutils.link_nodes(links, sep_node, "B", shader_node, b_socket)
            b_node.location = NODE_CURSOR
            NODE_CURSOR += Vector((0,-300))
        if a_node:
            nodeutils.link_nodes(links, pack_node, "Alpha", shader_node, a_socket)
            a_node.location = NODE_CURSOR
            NODE_CURSOR += Vector((0,-300))


def unlink_texture_nodes(mat, *tex_ids):
    global NODE_CURSOR
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    for tex_id in tex_ids:
        tex_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", f"({tex_id})")
        if tex_node:
            nodeutils.unlink_node_output(links, tex_node, "Color")
            nodeutils.unlink_node_output(links, tex_node, "Alpha")
            tex_node.location = NODE_CURSOR
            NODE_CURSOR += Vector((0,-300))


def pack_skin_shader(chr_cache, mat_cache, shader_node, limit_textures = False):
    prefs = vars.prefs()

    mat = mat_cache.material
    wrinkle_node = wrinkle.get_wrinkle_shader_node(mat)
    bake_dir = mat_cache.get_tex_dir(chr_cache)
    reuse = chr_cache.build_count > 0 and prefs.build_reuse_baked_channel_packs

    if prefs.build_limit_textures:
        unlink_texture_nodes(mat, "BLEND2", "NORMALBLEND", "CFULCMASK", "ENNASK")

    if wrinkle_node:

        if prefs.build_pack_wrinkle_diffuse_roughness:

            # this can free up 1 more texture, but takes longer.
            pack_rgb_a(mat, bake_dir, vars.PACK_DIFFUSEROUGHNESS_NAME, wrinkle_node, vars.PACK_DIFFUSEROUGHNESS_ID,
                    "DIFFUSE", "ROUGHNESS",
                    "Diffuse Map", "Roughness Map", 1.0, 0.5, srgb = True,
                    reuse_existing = reuse)

            pack_rgb_a(mat, bake_dir, vars.PACK_DIFFUSEROUGHNESSBLEND1_NAME, wrinkle_node, vars.PACK_DIFFUSEROUGHNESSBLEND1_ID,
                    "WRINKLEDIFFUSE1", "WRINKLEROUGHNESS1",
                    "Diffuse Blend Map 1", "Roughness Blend Map 1", 1.0, 0.5, srgb = True,
                    reuse_existing = reuse)

            pack_rgb_a(mat, bake_dir, vars.PACK_DIFFUSEROUGHNESSBLEND2_NAME, wrinkle_node, vars.PACK_DIFFUSEROUGHNESSBLEND2_ID,
                    "WRINKLEDIFFUSE2", "WRINKLEROUGHNESS2",
                    "Diffuse Blend Map 2", "Roughness Blend Map 2", 1.0, 0.5, srgb = True,
                    reuse_existing = reuse)

            pack_rgb_a(mat, bake_dir, vars.PACK_DIFFUSEROUGHNESSBLEND3_NAME, wrinkle_node, vars.PACK_DIFFUSEROUGHNESSBLEND3_ID,
                    "WRINKLEDIFFUSE3", "WRINKLEROUGHNESS3",
                    "Diffuse Blend Map 3", "Roughness Blend Map 3", 1.0, 0.5, srgb = True,
                    reuse_existing = reuse)
        else:

            # otherwise pack the 4 roughness channels into a single RGBA texture
            pack_r_g_b_a(mat, bake_dir, vars.PACK_WRINKLEROUGHNESS_NAME, wrinkle_node, vars.PACK_WRINKLEROUGHNESS_ID,
                        "WRINKLEROUGHNESS1", "WRINKLEROUGHNESS2", "WRINKLEROUGHNESS3", "ROUGHNESS",
                        "Roughness Blend Map 1", "Roughness Blend Map 2", "Roughness Blend Map 3", "Roughness Map",
                        0.5, 0.5, 0.5, 0.5,
                        reuse_existing = reuse)

    pack_r_g_b_a(mat, bake_dir, vars.PACK_WRINKLEFLOW_NAME, wrinkle_node, vars.PACK_WRINKLEFLOW_ID,
                        "WRINKLEFLOW1", "WRINKLEFLOW2", "WRINKLEFLOW3", "",
                        "Flow Map 1", "Flow Map 2", "Flow Map 3", "",
                        1.0, 1.0, 1.0, 1.0,
                        reuse_existing = reuse)

    # pack SSS and Transmission
    pack_rgb_a(mat, bake_dir, vars.PACK_SSTM_NAME, shader_node, vars.PACK_SSTM_ID,
               "SSS", "TRANSMISSION",
               "Subsurface Map", "Transmission Map", 1.0, 0.0, max_size = 1024,
                reuse_existing = reuse)

    # pack Metallic, Specular Mask, Micro Normal Mask and AO
    pack_r_g_b_a(mat, bake_dir, vars.PACK_MSMNAO_NAME, shader_node, vars.PACK_MSMNAO_ID,
                 "METALLIC", "SPECMASK", "MICRONMASK", "AO",
                 "Metallic Map", "Specular Mask", "Micro Normal Mask", "AO Map",
                 0.0, 1.0, 1.0, 1.0,
                reuse_existing = reuse)

    if prefs.build_skin_shader_dual_spec:
        # pack SSS and Transmission
        pack_rgb_a(mat, bake_dir, vars.PACK_MICRODETAIL_NAME, shader_node, vars.PACK_MICRODETAIL_ID,
                   "MICRONORMAL", "SKINSPECDETAIL",
                   "Micro Normal Map", "Specular Detail Mask", 1.0, 1.0,
                   reuse_existing = reuse)


def pack_default_shader(chr_cache, mat_cache, shader_node):
    prefs = vars.prefs()

    mat = mat_cache.material
    bake_dir = mat_cache.get_tex_dir(chr_cache)
    reuse = chr_cache.build_count > 0 and prefs.build_reuse_baked_channel_packs

    # pack diffuse + alpha
    pack_rgb_a(mat, bake_dir, vars.PACK_DIFFUSEALPHA_NAME, shader_node, vars.PACK_DIFFUSEALPHA_ID,
               "DIFFUSE", "ALPHA",
               "Diffuse Map", "Alpha Map",
               1.0, 1.0, srgb = True,
               reuse_existing = reuse)

    # pack Metallic, Specular Mask, Micro Normal Mask and AO
    pack_r_g_b_a(mat, bake_dir, vars.PACK_MRSO_NAME, shader_node, vars.PACK_MRSO_ID,
                 "METALLIC", "ROUGHNESS", "SPECULAR", "AO",
                 "Metallic Map", "Roughness Map", "Specular Map", "AO Map",
                 0.0, 0.5, 1.0, 1.0,
                 reuse_existing = reuse)


def pack_sss_shader(chr_cache, mat_cache, shader_node):
    prefs = vars.prefs()

    mat = mat_cache.material
    bake_dir = mat_cache.get_tex_dir(chr_cache)
    reuse = chr_cache.build_count > 0 and prefs.build_reuse_baked_channel_packs

    # pack diffuse + alpha
    pack_rgb_a(mat, bake_dir, vars.PACK_DIFFUSEALPHA_NAME, shader_node, vars.PACK_DIFFUSEALPHA_ID,
               "DIFFUSE", "ALPHA",
               "Diffuse Map", "Alpha Map",
               1.0, 1.0, srgb = True,
               reuse_existing = reuse)

    # pack Metallic, Specular Mask, Micro Normal Mask and AO
    pack_r_g_b_a(mat, bake_dir, vars.PACK_MRSO_NAME, shader_node, vars.PACK_MRSO_ID,
                 "METALLIC", "ROUGHNESS", "SPECULAR", "AO",
                 "Metallic Map", "Roughness Map", "Specular Map", "AO Map",
                 0.0, 0.5, 1.0, 1.0,
                 reuse_existing = reuse)

    # pack SSS, Transmission, Micro Normal Mask
    pack_r_g_b_a(mat, bake_dir, vars.PACK_SSTMMNM_NAME, shader_node, vars.PACK_SSTMMNM_ID,
                 "SSS", "TRANSMISSION", "MICRONMASK", "",
                 "Subsurface Map", "Transmission Map", "Micro Normal Mask", "",
                 0.0, 1.0, 1.0, 1.0,
                 reuse_existing = reuse)


def pack_hair_shader(chr_cache, mat_cache, shader_node):
    prefs = vars.prefs()

    mat = mat_cache.material
    bake_dir = mat_cache.get_tex_dir(chr_cache)
    reuse = chr_cache.build_count > 0 and prefs.build_reuse_baked_channel_packs

    # pack diffuse + alpha
    pack_rgb_a(mat, bake_dir, vars.PACK_DIFFUSEALPHA_NAME, shader_node, vars.PACK_DIFFUSEALPHA_ID,
               "DIFFUSE", "ALPHA",
               "Diffuse Map", "Alpha Map",
               1.0, 1.0, srgb = True,
               reuse_existing = reuse)

    # pack Metallic, Roughness, Specular and AO
    pack_r_g_b_a(mat, bake_dir, vars.PACK_MRSO_NAME, shader_node, vars.PACK_MRSO_ID,
                 "METALLIC", "ROUGHNESS", "SPECULAR", "AO",
                 "Metallic Map", "Roughness Map", "Specular Map", "AO Map",
                 0.0, 0.5, 1.0, 1.0,
                 reuse_existing = reuse)

    # pack Root map, ID map
    pack_rgb_a(mat, bake_dir, vars.PACK_ROOTID_NAME, shader_node, vars.PACK_ROOTID_ID,
               "HAIRROOT", "HAIRID",
               "Root Map", "ID Map",
               0.5, 0.5,
               reuse_existing = reuse)


def pack_shader_channels(chr_cache, mat_cache):
    global NODE_CURSOR
    prefs = vars.prefs()

    init_bake(5001)

    nodeutils.clear_cursor()
    NODE_CURSOR = Vector((-4500, 400))

    mode_selection = utils.store_mode_selection_state()

    shader = params.get_shader_name(mat_cache)
    mat = mat_cache.material
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader)
    if not shader_node:
        # fall back to default shader
        shader = "rl_pbr_shader"
        bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader)

    if shader_node:

        if shader == "rl_head_shader":
            if prefs.build_limit_textures:
                pack_skin_shader(chr_cache, mat_cache, shader_node, limit_textures = True)
            else:
                pack_skin_shader(chr_cache, mat_cache, shader_node)

        elif shader == "rl_skin_shader":
            pack_skin_shader(chr_cache, mat_cache, shader_node)

        elif shader == "rl_hair_shader":
            pack_hair_shader(chr_cache, mat_cache, shader_node)

        elif shader == "rl_sss_shader":
            pack_sss_shader(chr_cache, mat_cache, shader_node)

        elif shader == "rl_tearline_shader" or shader == "rl_eye_occlusion_shader":
            # no textures to pack for these.
            pass

        else:
            # everything else can be packed as default shader
            pack_default_shader(chr_cache, mat_cache, shader_node)


    utils.restore_mode_selection_state(mode_selection)


class CC3BakeOperator(bpy.types.Operator):
    """Bake Operator"""
    bl_idname = "cc3.bake"
    bl_label = "Bake Operator"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):
        props = vars.props()

        if self.param == "BAKE_FLOW_NORMAL":
            mat = utils.get_context_material(context)
            chr_cache = props.get_context_character_cache(context)
            mat_cache = chr_cache.get_material_cache(mat)
            bake_flow_to_normal(context, chr_cache, mat_cache)

        if self.param == "BAKE_BUMP_NORMAL":
            mat = utils.get_context_material(context)
            chr_cache = props.get_context_character_cache(context)
            mat_cache = chr_cache.get_material_cache(mat)
            combine_normal(context, chr_cache, mat_cache)

        if self.param == "BUILD_DISPLACEMENT":
            mat = utils.get_context_material(context)
            chr_cache = props.get_context_character_cache(context)
            mat_cache = chr_cache.get_material_cache(mat)
            normal.build_displacement_system(chr_cache, mat_cache)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "BAKE_FLOW_NORMAL":
            return "Generates a normal map from the flow map and connects it"
        if properties.param == "BAKE_BUMP_NORMAL":
            return "Combines the Bump and Normal maps into a single normal map"
        return ""





#####################################################
# BAKE TOOL OPERATORS


def get_export_bake_image_format():
    props = vars.bake_props()
    format = props.target_format
    ext = ".jpg"

    if format == "PNG":
        ext = ".png"
    elif format == "JPEG":
        ext = ".jpg"

    return format, ext


def get_bake_path():
    props = vars.bake_props()

    base_dir = os.path.join(bpy.path.abspath("//"))
    bake_path = props.bake_path
    try:
        if os.path.isabs(bake_path):
            path = bake_path
        else:
            path = os.path.join(base_dir, bake_path)
    except:
        path = os.path.join(base_dir, "Bake")

    return path


def copy_image_target(image_node, name, width, height, data = True, alpha = False):
    props = vars.bake_props()

    # return None if it's a bad image source
    if image_node is None or image_node.image is None:
        return None
    if image_node.image.size[0] == 0 or image_node.image.size[1] == 0:
        return None

    format, ext = get_export_bake_image_format()
    depth = 24
    if alpha:
        format = "PNG"
        ext = ".png"
        depth = 32

    path = get_bake_path()

    # find an old image with the same name to reuse:
    for img in bpy.data.images:
        if img.name.startswith(name) and img.name.endswith(name):

            img_path, img_file = os.path.split(img.filepath)
            same_path = False
            try:
                if os.path.samefile(path, img_path):
                    same_path = True
            except:
                same_path = False

            if same_path:
                utils.log_info("Removing existing copy: " + img.name)
                bpy.data.images.remove(img)

    utils.log_info("Copying existing image: " + image_node.image.name)
    img = image_node.image.copy()
    img.name = name
    if img.size[0] != width or img.size[1] != height:
        utils.log_info(f"Resizing image: {width} x {height})")
        img.scale(width, height)
    if img.file_format != format:
        if utils.B300():
            utils.log_info("Changing image format: " + format)
            img.file_format = format
        else:
            utils.log_info("Not changing image format of copy in Blender <= 2.93 (causes crash): " + format)

    dir = os.path.join(bpy.path.abspath("//"), path)
    os.makedirs(dir, exist_ok=True)
    img.filepath_raw = os.path.join(dir, name + ext)
    img.save()

    return img


def copy_target(source_mat, mat, source_node, map_suffix, data):
    image_name = get_bake_image_name(mat, map_suffix)
    width, height = nodeutils.get_tex_image_size(source_node)
    width, height = apply_override_size(source_mat, map_suffix, width, height)
    utils.log_info("Copying direct image source: " + source_node.name)
    image = copy_image_target(source_node, image_name, width, height, data)
    return image


def get_bake_image_name(mat, map_suffix):
    target_suffix = get_target_map_suffix(map_suffix)
    mat_name = utils.strip_name(mat.name)
    image_name = f"{mat_name}_{target_suffix}"
    return image_name


def get_bake_image_node_name(mat, global_suffix):
    image_node_name = f"({global_suffix})"
    return image_node_name


def export_bake_shader_normal(context, source_mat, mat):
    """Bake bsdf normal output for export bake operator.
       Uses bake props target format for image file format."""
    props = vars.bake_props()

    nodes = mat.node_tree.nodes
    suffix = "Normal"
    target_suffix = get_target_map_suffix(suffix)
    bsdf_node = nodeutils.get_bsdf_node(mat)
    path = get_bake_path()

    #target_size = get_target_map_size(source_mat, suffix)
    #source_size = detect_bake_size_from_suffix(source_mat, suffix)
    #if props.scale_maps and target_size < source_size:
    #    size = source_size
    #else:
    #    size = target_size

    image = bake_bsdf_normal(context, bsdf_node, mat, target_suffix, path,
                             no_prep=True, image_format=props.target_format)

    image_node = None
    if image:
        image_node_name = get_bake_image_node_name(mat, suffix)
        image_node = nodeutils.make_image_node(nodes, image, image_node_name)

    #if props.scale_maps and target_size < source_size:
    #    image.scale(target_size, target_size)

    return image_node


def export_bake_socket_input(context, source_mat, source_mat_cache, mat,
                             to_node, to_socket, suffix,
                             data=True):
    """Bake node socket input for export bake operator.
       Uses bake props target format for image file format."""
    from_node = nodeutils.get_node_connected_to_input(to_node, to_socket)
    from_socket = nodeutils.get_socket_connected_to_input(to_node, to_socket)
    return export_bake_socket_output(context, source_mat, source_mat_cache, mat,
                                     from_node, from_socket, suffix,
                                     data=data)


def export_bake_socket_output(context, source_mat, source_mat_cache, mat,
                              from_node, from_socket, suffix,
                              data=True):
    """Bake node socket output for export bake operator.
       Uses bake props target format for image file format."""
    props = vars.bake_props()

    if from_node:
        image = None

        # Copy, don't bake if the input is a texture (Color socket)
        # TODO this never happens...
        if from_node.type == "TEX_IMAGE" and from_socket == "Color":
            image = copy_target(source_mat, mat, from_node, suffix, data)
        else:
            path = get_bake_path()
            image = bake_node_socket_output(context, from_node, from_socket, mat, suffix, path,
                                            exact_name=True, underscores=True,
                                            no_prep=True, image_format=props.target_format)

        if image:
            image_node_name = get_bake_image_node_name(mat, suffix)
            image_node = nodeutils.make_image_node(mat.node_tree.nodes, image, image_node_name)
            return image_node

    return None


def set_loc(node, loc):
    if node:
        node.location = loc


def prep_diffuse(mat, shader_name, shader_node, separate, ao_strength):
    props = vars.bake_props()
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    # turn off depth for cornea parallax
    parallax_tiling_node = nodeutils.find_node_by_keywords(nodes, vars.NODE_PREFIX, "(tiling_rl_cornea_shader_DIFFUSE_mapping)")
    if parallax_tiling_node:
        nodeutils.set_node_input_value(parallax_tiling_node, "Depth", 0.0)
    # for baking separate diffuse and AO, set the amount of AO to bake into the diffuse map
    if separate and shader_node:
        nodeutils.set_node_input_value(shader_node, "AO Strength", props.ao_in_diffuse * ao_strength)


def prep_ao(mat, shader_node):
    props = vars.bake_props()
    ao_strength = 1.0
    if shader_node:
        # fetch the intended ao strength
        ao_strength = nodeutils.get_node_input_value(shader_node, "AO Strength", 1.0)
        # max out the ao strength for baking
        nodeutils.set_node_input_value(shader_node, "AO Strength", 1.0)
    return ao_strength


def disable_ao(mat, shader_node):
    if shader_node:
        nodeutils.set_node_input_value(shader_node, "AO Strength", 0.0)


def prep_sss(shader_node, bsdf_node : bpy.types.Node):
    props = vars.bake_props()
    sss_radius = Vector((0.01, 0.01, 0.01))
    sss_radius = nodeutils.get_node_input_value(bsdf_node, "Subsurface Radius", sss_radius)
    return sss_radius


def prep_alpha(mat, shader_node):
    props = vars.bake_props()

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    return


def can_bake_shader_node(shader_node, bsdf_node, bsdf_socket):
    props = vars.bake_props()

    if shader_node is None:
        return False
    if nodeutils.is_mixer_connected(bsdf_node, bsdf_socket):
        return not props.bake_mixers
    return nodeutils.get_node_connected_to_input(bsdf_node, bsdf_socket) == shader_node


def bake_export_material(context, mat, source_mat, source_mat_cache):
    props = vars.bake_props()

    if not (utils.material_exists(mat) and
            utils.material_exists(source_mat) and
            source_mat_cache):
        utils.log_error("Invalid material or material cache!")
        return

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader_name = params.get_shader_name(source_mat_cache)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader_name)
    bake_maps = vars.get_bake_target_maps(props.target_mode)
    bake_path = get_bake_path()

    if not bsdf_node or not shader_node:
        utils.log_info(f"Material: {mat.name} has no RL shader")
        return

    utils.log_info(f"Baking export material {props.target_mode} / {mat.name} / {shader_name}")
    utils.log_info("")

    # Texture Map Baking
    # Note: As mat is a copy of the source material, which is repurposed into the target material
    # it's OK to change the shader inputs without restoring them

    # Diffuse Maps & AO
    diffuse_bake_node = None
    ao_bake_node = None
    ao_strength = nodeutils.get_node_input_value(shader_node, "AO Strength", 1.0)
    base_color_socket = nodeutils.input_socket(bsdf_node, "Base Color")
    if nodeutils.has_connected_input(bsdf_node, base_color_socket):
        if can_bake_shader_node(shader_node, bsdf_node, base_color_socket):
            # Note: if the shader_node does not have an "AO" output node,
            # then the AO texture is used directly.
            # Otherwise bake the AO output:
            if "AO" in bake_maps:
                ao_strength = prep_ao(mat, shader_node)
                # note: so far, nothing has an "AO" output node.
                if "AO" in shader_node.outputs:
                    ao_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat,
                                                             shader_node, "AO", "AO")
                else:
                    ao_node = nodeutils.find_shader_texture(nodes, "AO")
                    if ao_node:
                        ao_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, ao_node, "Color", "AO")
                # disable any further AO contribution
                disable_ao(mat, shader_node)
            # eye shaders use 1/8 the AO strength
            if shader_name in ["rl_cornea_shader", "rl_eye_shader"]:
                ao_strength /= 8
                # use unmodified iris brightness
                nodeutils.set_node_input_value(shader_node, "Iris Brightness", source_mat_cache.parameters.eye_iris_brightness)
            if "Diffuse" in bake_maps:
                # if there is a "Diffuse" output node, bake that, otherwise bake the "Base Color" output node.
                prep_diffuse(mat, shader_name, shader_node, "AO" in bake_maps, ao_strength)
                if "Diffuse" in shader_node.outputs and "Transmission" not in shader_node.outputs:
                    diffuse_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, shader_node, "Diffuse", "Diffuse", False)
                else:
                    diffuse_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, shader_node, "Base Color", "Diffuse", False)
        elif bsdf_node:
            # bake BSDF base color input
            diffuse_bake_node = export_bake_socket_input(context, source_mat, source_mat_cache, mat,
                                                         bsdf_node, base_color_socket, "Diffuse",
                                                         data=False)

    # Subsurface Scattering Maps
    sss_bake_node = None
    sss_radius = 1.0
    sss_socket = nodeutils.input_socket(bsdf_node, "Subsurface")
    if nodeutils.has_connected_input(bsdf_node, sss_socket):
        if "Subsurface" in bake_maps:
            sss_radius = prep_sss(mat, shader_node)
            if can_bake_shader_node(shader_node, bsdf_node, sss_socket):
                sss_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, shader_node, "Subsurface", "Subsurface")
            elif bsdf_node:
                sss_bake_node = export_bake_socket_input(context, source_mat, source_mat_cache, mat, bsdf_node, sss_socket, "Subsurface")

    # Thickness Maps (Subsurface transmission)
    # the transmission map texture is not used, but it is added to the material nodes
    thickness_bake_node = None
    if "Thickness" in bake_maps:
        utils.log_info("Processing Thickness/Transmission")
        thickness_node = nodeutils.find_shader_texture(nodes, "TRANSMISSION")
        if thickness_node:
            utils.log_info("thickness texture found...")
            thickness_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, thickness_node, "Color", "Thickness")

    # Metallic Maps
    metallic_bake_node = None
    metallic_socket = nodeutils.input_socket(bsdf_node, "Metallic")
    if nodeutils.has_connected_input(bsdf_node, metallic_socket):
        if "Metallic" in bake_maps:
            utils.log_info("Processing Metallic")
            if can_bake_shader_node(shader_node, bsdf_node, metallic_socket):
                metallic_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, shader_node, "Metallic", "Metallic")
            elif bsdf_node:
                metallic_bake_node = export_bake_socket_input(context, source_mat, source_mat_cache, mat, bsdf_node, metallic_socket, "Metallic")

    # Specular Maps
    specular_bake_node = None
    specular_socket = nodeutils.input_socket(bsdf_node, "Specular")
    if nodeutils.has_connected_input(bsdf_node, specular_socket):
        if "Specular" in bake_maps:
            utils.log_info("Processing Specular")
            if can_bake_shader_node(shader_node, bsdf_node, specular_socket):
                specular_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, shader_node, "Specular", "Specular")
            elif bsdf_node:
                specular_bake_node = export_bake_socket_input(context, source_mat, source_mat_cache, mat, bsdf_node, specular_socket, "Specular")
    specular_scale = 1.0
    if shader_node:
        specular_scale = nodeutils.get_node_input_value(shader_node, "Specular Scale", specular_scale)
        specular_scale = nodeutils.get_node_input_value(shader_node, "Front Specular", specular_scale)
    nodeutils.set_node_input_value(bsdf_node, specular_socket, 0.5 * specular_scale)

    # Roughness Maps
    roughnesss_bake_node = None
    roughness_socket = nodeutils.input_socket(bsdf_node, "Roughness")
    if nodeutils.has_connected_input(bsdf_node, roughness_socket):
        if "Roughness" in bake_maps:
            utils.log_info("Processing Roughness")
            if can_bake_shader_node(shader_node, bsdf_node, roughness_socket):
                roughnesss_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, shader_node, "Roughness", "Roughness")
            elif bsdf_node:
                roughnesss_bake_node = export_bake_socket_input(context, source_mat, source_mat_cache, mat, bsdf_node, roughness_socket, "Roughness")

    # Emission Maps
    # copy emission maps directly...
    emission_bake_node = None
    emission_strength = nodeutils.get_node_input_value(shader_node, "Emission Strength", 0.0)
    emission_socket = nodeutils.input_socket(bsdf_node, "Emission")
    if nodeutils.has_connected_input(bsdf_node, emission_socket):
        if "Emission" in bake_maps:
            utils.log_info("Processing Emission")
            emission_node = nodeutils.find_shader_texture(nodes, "EMISSION")
            if emission_node:
                if can_bake_shader_node(shader_node, bsdf_node, emission_socket):
                    emission_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, emission_node, "Color", "Emission")
                elif bsdf_node:
                    emission_bake_node = export_bake_socket_input(context, source_mat, source_mat_cache, mat, bsdf_node, emission_socket, "Emission")

    # Alpha Maps
    alpha_bake_node = None
    alpha_socket = nodeutils.input_socket(bsdf_node, "Alpha")
    # Opacity output is for baking only
    if nodeutils.has_connected_input(bsdf_node, alpha_socket) or (shader_node and "Opacity" in shader_node.outputs):
        if shader_node and ("Opacity" in shader_node.outputs or "Alpha" in shader_node.outputs) and "Alpha" in bake_maps:
            prep_alpha(mat, shader_node)
            if (can_bake_shader_node(shader_node, bsdf_node, alpha_socket)
                or (shader_node and "Opacity" in shader_node.outputs)):
                if "Opacity" in shader_node.outputs:
                    alpha_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, shader_node, "Opacity", "Alpha")
                    if utils.B430():
                        materials.set_material_alpha(mat, "DITHERED", shadows=False)
                    else:
                        materials.set_material_alpha(mat, "BLEND", shadows=False)
                else:
                    alpha_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, shader_node, "Alpha", "Alpha")
            elif bsdf_node:
                alpha_bake_node = export_bake_socket_input(context, source_mat, source_mat_cache, mat, bsdf_node, alpha_socket, "Alpha")

    # Transmission Maps (Refractive Transparency)
    transmission_bake_node = None
    transmission_socket = nodeutils.input_socket(bsdf_node, "Transmission")
    thickness = 0.0
    if shader_name == "rl_cornea_shader":
        iris_depth = nodeutils.get_node_input_value(shader_node, "Iris Depth", 0.0)
        thickness = 0.4 * iris_depth + 0.2
    if nodeutils.has_connected_input(bsdf_node, transmission_socket):
        if "Transmission" in bake_maps:
            if can_bake_shader_node(shader_node, bsdf_node, transmission_socket):
                transmission_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, shader_node, "Transmission", "Transmission")
            elif bsdf_node:
                transmission_bake_node = export_bake_socket_input(context, source_mat, source_mat_cache, mat, bsdf_node, transmission_socket, "Transmission")

    # Bump Maps
    # if shader group node has a "Bump Map" input, then copy the bump map texture directly
    bump_bake_node = None
    bump_distance = 0.01
    normal_socket = nodeutils.input_socket(bsdf_node, "Normal")
    if nodeutils.has_connected_input(bsdf_node, normal_socket):
        if "Bump" in bake_maps and props.allow_bump_maps:
            if can_bake_shader_node(shader_node, bsdf_node, normal_socket):
                bump_node = nodeutils.find_shader_texture(nodes, "BUMP")
                bump_distance = nodeutils.get_node_input_value(shader_node, "Bump Strength", 0.01)
                if bump_node:
                    bump_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, bump_node, "Color", "Bump")
            elif bsdf_node:
                input_node = nodeutils.get_node_connected_to_input(bsdf_node, normal_socket)
                if input_node.type == "BUMP":
                    height_node = nodeutils.get_node_connected_to_input(input_node, "Height")
                    if height_node:
                        bump_bake_node = export_bake_socket_input(context, source_mat, source_mat_cache, mat, input_node, "Height", "Bump")
                        bump_distance = nodeutils.get_node_input_value(input_node, "Distance", 1.0)

    # Normal Maps
    # if the shader group node has a "Blend Normal" color output, bake that,
    # otherwise copy the normal map texture directly
    # DO NOT BAKE the normal vector output.
    normal_bake_node = None
    normal_strength = 1.0
    bump_to_normal = False
    if nodeutils.has_connected_input(bsdf_node, normal_socket):
        if "Normal" in bake_maps:
            if "Bump" not in bake_maps or not props.allow_bump_maps:
                bump_to_normal = True
            if can_bake_shader_node(shader_node, bsdf_node, normal_socket):
                normal_strength = nodeutils.get_node_input_value(shader_node, "Normal Strength", 1.0)
                if "Blend Normal" in shader_node.outputs:
                    normal_strength = 1.0
                    normal_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, shader_node, "Blend Normal", "Normal")
                else:
                    normal_node = nodeutils.find_shader_texture(nodes, "NORMAL")
                    if normal_node:
                        normal_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, normal_node, "Color", "Normal")
                    else:
                        normal_bake_node = export_bake_shader_normal(context, source_mat, mat)
            elif bsdf_node:
                input_node = nodeutils.get_node_connected_to_input(bsdf_node, normal_socket)
                if input_node:
                    if input_node.type == "NORMAL_MAP":
                        # just a normal mapper, bake the entire normal input
                        normal_bake_node = export_bake_shader_normal(context, source_mat, mat)
                        normal_strength = nodeutils.get_node_input_value(input_node, "Strength", 1.0)
                    elif input_node.type == "BUMP":
                        # bump node mappers can have heightmap and normal inputs
                        normal_node = nodeutils.get_node_connected_to_input(input_node, "Normal")
                        height_node = nodeutils.get_node_connected_to_input(input_node, "Height")
                        if bump_to_normal:
                            # bake everything into the normal
                            normal_bake_node = export_bake_shader_normal(context, source_mat, mat)
                            normal_strength = 1.0
                        else:
                            # bake the normal separately
                            if normal_node:
                                normal_bake_node = export_bake_socket_input(context, source_mat, source_mat_cache, mat, input_node, "Normal", "Normal")
                                normal_strength = nodeutils.get_node_input_value(normal_node, "Strength", 1.0)
                    else:
                        # something is plugged into the normals, but can't tell what, so just bake the shader normals
                        normal_bake_node = export_bake_shader_normal(context, source_mat, mat)

    # Micro Normals
    # always copy the micro normal map texture directly
    micro_normal_bake_node = None
    micro_normal_strength = 1
    micro_normal_tiling = 20
    micro_normal_scale = Vector((1, 1, 1))
    if nodeutils.has_connected_input(bsdf_node, normal_socket):
        if "MicroNormal" in bake_maps:
            micro_normal_node = nodeutils.find_shader_texture(nodes, "MICRONORMAL")
            if micro_normal_node:
                tiling_node = nodeutils.get_node_connected_to_input(micro_normal_node, "Vector")
                if tiling_node:
                    if "Tiling" in tiling_node.inputs:
                        micro_normal_scale = nodeutils.get_node_input_value(tiling_node, "Tiling", micro_normal_scale)
                        micro_normal_tiling = micro_normal_scale[0]
                        micro_normal_scale = Vector((micro_normal_tiling, micro_normal_tiling, 1))
                    elif "Scale" in tiling_node.inputs:
                        micro_normal_scale = nodeutils.get_node_input_value(tiling_node, "Scale", micro_normal_scale)
                        micro_normal_tiling = micro_normal_scale[0]
                        micro_normal_scale = Vector((micro_normal_tiling, micro_normal_tiling, 1))
                utils.log_info(f"Tiling: {micro_normal_scale}")
                # disconnect any tiling/mapping nodes before baking the micro normal...
                nodeutils.unlink_node_input(links, micro_normal_node, "Vector")
                micro_normal_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, micro_normal_node, "Color", "MicroNormal")

    # Micro Normal Mask
    # if the shader group node as a "Normal Mask" float output, bake that,
    # otherwise copy the micro normal mask directly
    micro_normal_mask_bake_node = None
    micro_normal_stength = 1.0
    if nodeutils.has_connected_input(bsdf_node, normal_socket):
        if "MicroNormalMask" in bake_maps:
            if shader_node:
                if "Normal Mask" in shader_node.outputs:
                    micro_normal_mask_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, shader_node, "Normal Mask", "MicroNormalMask")
                    micro_normal_strength = 1.0
                else:
                    micro_normal_mask_node = nodeutils.find_shader_texture(nodes, "MICRONMASK")
                    micro_normal_strength = nodeutils.get_node_input_value(shader_node, "Micro Normal Strength", 1.0)
                    if micro_normal_mask_node:
                        micro_normal_mask_bake_node = export_bake_socket_output(context, source_mat, source_mat_cache, mat, micro_normal_mask_node, "Color", "MicroNormalMask")

    # Post processing
    #
    utils.log_info("Post Processing Textures...")
    utils.log_info("")

    if props.target_mode == "BLENDER":
        pass

    elif props.target_mode == "GODOT":
        pass

    elif props.target_mode == "SKETCHFAB":
        pass

    elif props.target_mode == "GLTF":
        if props.pack_gltf:
            # BaseMap: RGB: diffuse, A: alpha
            combine_diffuse_tex(nodes, source_mat, source_mat_cache, mat,
                    diffuse_bake_node, alpha_bake_node)
            # GLTF pack: R: Ao, G: Roughness, B: Metallic
            combine_gltf(nodes, source_mat, source_mat_cache, mat,
                         ao_bake_node, roughnesss_bake_node, metallic_bake_node)

    elif props.target_mode == "UNITY_URP":
        # BaseMap: RGB: diffuse, A: alpha
        combine_diffuse_tex(nodes, source_mat, source_mat_cache, mat,
                diffuse_bake_node, alpha_bake_node)

        # MetallicAlpha: RGB: Metallic, A: Smoothness = f(Rougness)
        make_metallic_smoothness_tex(nodes, source_mat, source_mat_cache, mat,
                                     metallic_bake_node, roughnesss_bake_node)

    elif props.target_mode == "UNITY_HDRP":
        # BaseMap: RGB: diffuse, A: alpha
        combine_diffuse_tex(nodes, source_mat, source_mat_cache, mat,
                diffuse_bake_node, alpha_bake_node)

        # Mask: R: Metallic, G: AO, B: Micro-Normal Mask, A: Smoothness = f(Roughness)
        combine_hdrp_mask_tex(nodes, source_mat, source_mat_cache, mat,
                metallic_bake_node, ao_bake_node, micro_normal_mask_bake_node, roughnesss_bake_node)

        # Detail: R: 0.5, G: Micro-Normal.R, B: 0.5, A: Micro-Normal.G
        combine_hdrp_detail_tex(nodes, source_mat, source_mat_cache, mat,
                micro_normal_bake_node)

        # invert the thickness map
        process_hdrp_subsurfaces_tex(sss_bake_node, thickness_bake_node)

    # reconnect the materials

    utils.log_info("Reconnecting baked material:")
    utils.log_info("")

    reconnect_material(mat, source_mat_cache,
                       ao_strength, sss_radius, bump_distance,
                       normal_strength, micro_normal_strength, micro_normal_scale,
                       emission_strength, thickness)


def fetch_pack_image_data(width, height, *nodes, no_rescale = False):

    utils.log_info(f"Using packed map size: {width} x {height}")

    data = []

    for node in nodes:
        pixels = None
        if node and node.image:
            image : bpy.types.Image = node.image
            utils.log_info(f"Using tex image: {image.name} - {image.size[0]} x {image.size[1]} - {image.colorspace_settings.name}")
            if image.size[0] != width or image.size[1] != height:
                utils.log_info(f" - Scaling tex image: {width} x {height}")
                scaled_image = image.copy()
                scaled_image.scale(width, height)
                pixels = list(scaled_image.pixels)
            else:
                pixels = list(image.pixels)
        data.append(pixels)

    return data


def combine_diffuse_tex(nodes, source_mat, source_mat_cache, mat,
                        diffuse_node, alpha_node, image_format="PNG"):

    diffuse_data = None
    alpha_data = None
    bsdf_node = nodeutils.get_bsdf_node(mat)
    base_color_socket = nodeutils.input_socket(bsdf_node, "Base Color")
    diffuse_value = nodeutils.get_node_input_value(bsdf_node, base_color_socket, (1,1,1,1))

    map_suffix = "BaseMap"
    path = get_bake_path()
    width, height = nodeutils.get_largest_image_size(diffuse_node, alpha_node)
    width, height = apply_override_size(mat, map_suffix, width, height)
    diffuse_data, alpha_data = fetch_pack_image_data(width, height, diffuse_node, alpha_node)

    if diffuse_data is None and alpha_data is None:
        return

    utils.log_info("Combining diffuse with alpha...")

    image_name = get_bake_image_name(mat, map_suffix)
    image_node_name = get_bake_image_node_name(mat, map_suffix)
    image, exists = get_image_target(image_name, width, height, path, is_data=False, has_alpha=True,
                                     channel_packed=True, format=image_format)
    image_node = nodeutils.make_image_node(nodes, image, image_node_name)
    image_node.select = True
    nodes.active = image_node
    # writeable list copy for fastest write speed
    image_data = list(image.pixels)
    l = len(image_data)

    for i in range(0, l, 4):
        if diffuse_data:
            image_data[i+0] = diffuse_data[i+0]
            image_data[i+1] = diffuse_data[i+1]
            image_data[i+2] = diffuse_data[i+2]
        else:
            image_data[i+0] = diffuse_value[0]
            image_data[i+1] = diffuse_value[1]
            image_data[i+2] = diffuse_value[2]

        if alpha_data:
            image_data[i+3] = alpha_data[i]
        else:
            image_data[i+3] = 1

    # replace in-place in one go.
    image.pixels[:] = image_data
    image.update()
    image.save()


def combine_hdrp_mask_tex(nodes, source_mat, source_mat_cache, mat,
                          metallic_node, ao_node, mask_node, roughness_node,
                          image_format="PNG"):
    props = vars.bake_props()

    metallic_data = None
    ao_data = None
    mask_data = None
    roughness_data = None

    map_suffix = "Mask"
    path = get_bake_path()
    width, height = nodeutils.get_largest_image_size(metallic_node, ao_node, mask_node, roughness_node)
    width, height = apply_override_size(mat, map_suffix, width, height)
    metallic_data, ao_data, mask_data, roughness_data = fetch_pack_image_data(width, height, metallic_node, ao_node, mask_node, roughness_node)

    if metallic_data is None and ao_data is None and mask_data is None and roughness_data is None:
        return

    utils.log_info("Combining Unity HDRP Mask Texture...")

    bsdf_node = nodeutils.get_bsdf_node(mat)
    metallic_socket = nodeutils.input_socket(bsdf_node, "Metallic")
    roughness_socket = nodeutils.input_socket(bsdf_node, "Roughness")
    metallic_value = nodeutils.get_node_input_value(bsdf_node, metallic_socket, 0.0)
    roughness_value = nodeutils.get_node_input_value(bsdf_node, roughness_socket, 0.0)
    ao_value = 1
    mask_value = 1

    image_name = get_bake_image_name(mat, map_suffix)
    image_node_name = get_bake_image_node_name(mat, map_suffix)
    image, exists = get_image_target(image_name, width, height, path,
                                     is_data=True, has_alpa=True, channel_packed=True,
                                     format=image_format)
    image_node = nodeutils.make_image_node(nodes, image, image_node_name)
    image_node.select = True
    nodes.active = image_node
    image_data = list(image.pixels)
    l = len(image_data)

    # Mask: R: Metallic, G: AO, B: Micro-Normal Mask, A: Smoothness = 0.5 + 0.5*(1-Roughess)^2
    for i in range(0, l, 4):

        # Red
        if metallic_data:
            image_data[i] = metallic_data[i]
        else:
            image_data[i] = metallic_value

        # Green
        if ao_data:
            image_data[i+1] = ao_data[i]
        else:
            image_data[i+1] = ao_value

        # Blue
        if mask_data:
            image_data[i+2] = mask_data[i]
        else:
            image_data[i+2] = mask_value

        # Alpha
        if roughness_data:
            roughness = roughness_data[i]
        else:
            roughness = roughness_value

        if props.smoothness_mapping == "SIR":
            smoothness = pow(1 - roughness, 2)
        elif props.smoothness_mapping == "IRS":
            smoothness = 1 - pow(roughness, 2)
        elif props.smoothness_mapping == "IRSR":
            smoothness = 1 - pow(roughness, 0.5)
        elif props.smoothness_mapping == "SRIR":
            smoothness = pow(1 - roughness, 0.5)
        elif props.smoothness_mapping == "SRIRS":
            smoothness = pow(1 - pow(roughness, 2), 0.5)
        else: # IR
            smoothness = 1 - roughness

        image_data[i+3] = smoothness

    image.pixels[:] = image_data
    image.update()
    image.save()


def combine_hdrp_detail_tex(nodes, source_mat, source_mat_cache, mat,
                            detail_normal_node, image_format="PNG"):

    detail_data = None

    map_suffix = "Detail"
    path = get_bake_path()
    width, height = nodeutils.get_largest_image_size(detail_normal_node)
    width, height = apply_override_size(mat, map_suffix, width, height)
    detail_data = fetch_pack_image_data(width, height, detail_normal_node)

    if not detail_data:
        return

    utils.log_info("Combining Unity HDRP Detail Texture...")

    image_name = get_bake_image_name(mat, map_suffix)
    image_node_name = get_bake_image_node_name(mat, map_suffix)
    image, exists = get_image_target(image_name, width, height, path,
                                     is_data=True, has_alpha=True, channel_packed=True,
                                     format=image_format)
    image_node = nodeutils.make_image_node(nodes, image, image_node_name)
    image_node.select = True
    nodes.active = image_node
    image_data = list(image.pixels)
    l = len(image_data)

    # Detail: R: 0.5, G: Micro-Normal.R, B: 0.5, A: Micro-Normal.G
    for i in range(0, l, 4):

        image_data[i+0] = 0.5
        image_data[i+2] = 0.5

        if detail_data:
            image_data[i+1] = detail_data[i+0]
            image_data[i+3] = detail_data[i+1]
        else:
            image_data[i+1] = 0.5
            image_data[i+3] = 0.5

    image.pixels[:] = image_data
    image.update()
    image.save()


def process_hdrp_subsurfaces_tex(sss_node, trans_node):

    if trans_node and trans_node.image:
        image = trans_node.image
        trans_data = list(image.pixels)
        l = len(trans_data)
        for i in range(0, l, 4):
            trans_data[i+0] = 1.0 - trans_data[i+0]
            trans_data[i+1] = 1.0 - trans_data[i+1]
            trans_data[i+2] = 1.0 - trans_data[i+2]

        image.pixels[:] = trans_data
        image.update()
        image.save()


def make_metallic_smoothness_tex(nodes, source_mat, source_mat_cache, mat,
                                 metallic_node, roughness_node,
                                 image_format="PNG"):
    props = vars.bake_props()

    metallic_data = None
    roughness_data = None

    map_suffix = "MetallicAlpha"
    path = get_bake_path()
    width, height = nodeutils.get_largest_image_size(metallic_node, roughness_node)
    width, height = apply_override_size(mat, map_suffix, width, height)
    metallic_data, roughness_data = fetch_pack_image_data(width, height, metallic_node, roughness_node)

    if metallic_data is None and roughness_data is None:
        return

    utils.log_info("Create Unity URP/3D Metallic Alpha Texture from Metallic and Roughness...")

    bsdf_node = nodeutils.get_bsdf_node(mat)
    metallic_socket = nodeutils.input_socket(bsdf_node, "Metallic")
    roughness_socket = nodeutils.input_socket(bsdf_node, "Roughness")
    metallic_value = nodeutils.get_node_input_value(bsdf_node, metallic_socket, 0)
    roughness_value = nodeutils.get_node_input_value(bsdf_node, roughness_socket, 0.5)

    image_name = get_bake_image_name(mat, map_suffix)
    image_node_name = get_bake_image_node_name(mat, map_suffix)
    image, exists = get_image_target(image_name, width, height, path,
                                     is_data=True, has_alpha=True, channel_packed=True,
                                     format=image_format)
    image_node = nodeutils.make_image_node(nodes, image, image_node_name)
    image_node.select = True
    nodes.active = image_node
    image_data = list(image.pixels)
    l = len(image_data)

    # Mask: R: Metallic, G: AO, B: Micro-Normal Mask, A: Smoothness = 0.5 + 0.5*(1-Roughess)^2
    for i in range(0, l, 4):

        if roughness_data:
            roughness = roughness_data[i]
        else:
            roughness = roughness_value

        if metallic_data:
            metallic = metallic_data[i]
        else:
            metallic = metallic_value

        if props.smoothness_mapping == "SIR":
            smoothness = pow(1 - roughness, 2)
        elif props.smoothness_mapping == "IRS":
            smoothness = 1 - pow(roughness, 2)
        elif props.smoothness_mapping == "IRSR":
            smoothness = 1 - pow(roughness, 0.5)
        elif props.smoothness_mapping == "SRIR":
            smoothness = pow(1 - roughness, 0.5)
        elif props.smoothness_mapping == "SRIRS":
            smoothness = pow(1 - pow(roughness, 2), 0.5)
        else: # IR
            smoothness = 1 - roughness

        image_data[i+0] = metallic
        image_data[i+1] = metallic
        image_data[i+2] = metallic
        image_data[i+3] = smoothness

    image.pixels[:] = image_data
    image.update()
    image.save()


def combine_gltf(nodes, source_mat, source_mat_cache, mat,
                 ao_node, roughness_node, metallic_node,
                 image_format="PNG"):

    props = vars.bake_props()

    metallic_data = None
    ao_data = None
    roughness_data = None

    map_suffix = "GLTF"
    path = get_bake_path()
    width, height = nodeutils.get_largest_image_size(ao_node, roughness_node, metallic_node)
    width, height = apply_override_size(mat, map_suffix, width, height)
    ao_data, roughness_data, metallic_data = fetch_pack_image_data(width, height, ao_node, roughness_node, metallic_node)

    if ao_data is None and roughness_data is None and metallic_data is None:
        return

    utils.log_info("Combining GLTF texture pack...")

    bsdf_node = nodeutils.get_bsdf_node(mat)
    metallic_socket = nodeutils.input_socket(bsdf_node, "Metallic")
    roughness_socket = nodeutils.input_socket(bsdf_node, "Roughness")
    metallic_value = nodeutils.get_node_input_value(bsdf_node, metallic_socket, 0.0)
    roughness_value = nodeutils.get_node_input_value(bsdf_node, roughness_socket, 0.0)
    ao_value = 1

    image_name = get_bake_image_name(mat, map_suffix)
    image_node_name = get_bake_image_node_name(mat, map_suffix)
    image, exists = get_image_target(image_name, width, height, path,
                                     is_data=True, has_alpha=False, channel_packed=False,
                                     format=image_format)
    image_node = nodeutils.make_image_node(nodes, image, image_node_name)
    image_node.select = True
    nodes.active = image_node
    image_data = list(image.pixels)
    l = len(image_data)

    # GLTF: R: AO, G: Roughness, B: Metallic
    for i in range(0, l, 4):

        # Red
        if ao_data:
            image_data[i+0] = ao_data[i]
        else:
            image_data[i+0] = ao_value

        # Green
        if roughness_data:
            image_data[i+1] = roughness_data[i]
        else:
            image_data[i+1] = roughness_value

        # Blue
        if metallic_data:
            image_data[i+2] = metallic_data[i]
        else:
            image_data[i+2] = metallic_value

    image.pixels[:] = image_data
    image.update()
    image.save()


def find_baked_image_nodes(nodes, tex_nodes, global_suffix):
    node = nodeutils.find_shader_texture(nodes, global_suffix)
    tex_nodes[global_suffix] = node


def reconnect_material(mat, mat_cache, ao_strength, sss_radius, bump_distance, normal_strength,
                       micro_normal_strength, micro_normal_scale, emission_strength, thickness):
    props = vars.bake_props()

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader_name = params.get_shader_name(mat_cache)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader_name)
    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")

    nodeutils.link_nodes(links, bsdf_node, "BSDF", output_node, "Surface")

    tex_nodes = {}
    find_baked_image_nodes(nodes, tex_nodes, "Diffuse")
    find_baked_image_nodes(nodes, tex_nodes, "BaseMap")
    find_baked_image_nodes(nodes, tex_nodes, "AO")
    find_baked_image_nodes(nodes, tex_nodes, "Subsurface")
    find_baked_image_nodes(nodes, tex_nodes, "Thickness")
    find_baked_image_nodes(nodes, tex_nodes, "Metallic")
    find_baked_image_nodes(nodes, tex_nodes, "Specular")
    find_baked_image_nodes(nodes, tex_nodes, "Roughness")
    find_baked_image_nodes(nodes, tex_nodes, "Emission")
    find_baked_image_nodes(nodes, tex_nodes, "Alpha")
    find_baked_image_nodes(nodes, tex_nodes, "Transmission")
    find_baked_image_nodes(nodes, tex_nodes, "Normal")
    find_baked_image_nodes(nodes, tex_nodes, "Bump")
    find_baked_image_nodes(nodes, tex_nodes, "MicroNormal")
    find_baked_image_nodes(nodes, tex_nodes, "MicroNormalMask")
    find_baked_image_nodes(nodes, tex_nodes, "GLTF")
    find_baked_image_nodes(nodes, tex_nodes, "Mask")
    find_baked_image_nodes(nodes, tex_nodes, "Detail")

    mix_node = None
    bump_map_node = None
    normal_map_node = None
    gltf_settings_node = None
    split_node = None
    micro_mix_node = None
    micro_mapping_node = None
    micro_texcoord_node = None
    micro_mask_mult_node = None

    base_color_socket = nodeutils.input_socket(bsdf_node, "Base Color")
    sss_socket = nodeutils.input_socket(bsdf_node, "Subsurface")
    metallic_socket = nodeutils.input_socket(bsdf_node, "Metallic")
    specular_socket = nodeutils.input_socket(bsdf_node, "Specular")
    roughness_socket = nodeutils.input_socket(bsdf_node, "Roughness")
    emission_socket = nodeutils.input_socket(bsdf_node, "Emission")
    transmission_socket = nodeutils.input_socket(bsdf_node, "Transmission")
    alpha_socket = nodeutils.input_socket(bsdf_node, "Alpha")
    normal_socket = nodeutils.input_socket(bsdf_node, "Normal")

    if shader_node:
        nodes.remove(shader_node)

    for node in nodes:
        if node != bsdf_node and node != output_node:
            if node not in tex_nodes.values():
                nodes.remove(node)

    if props.target_mode == "GLTF" and props.pack_gltf:
        if tex_nodes["Diffuse"]:
            nodes.remove(tex_nodes["Diffuse"])
            tex_nodes["Diffuse"] = None
        if tex_nodes["AO"]:
            nodes.remove(tex_nodes["AO"])
            tex_nodes["AO"] = None
        if tex_nodes["Roughness"]:
            nodes.remove(tex_nodes["Roughness"])
            tex_nodes["Roughness"] = None
        if tex_nodes["Metallic"]:
            nodes.remove(tex_nodes["Metallic"])
            tex_nodes["Metallic"] = None
        if tex_nodes["BaseMap"]:
            nodeutils.link_nodes(links, tex_nodes["BaseMap"], "Color", bsdf_node, base_color_socket)
            if tex_nodes["Alpha"]:
                nodeutils.link_nodes(links, tex_nodes["BaseMap"], "Alpha", bsdf_node, alpha_socket)
                nodes.remove(tex_nodes["Alpha"])
                tex_nodes["Alpha"] = None
        if tex_nodes["GLTF"]:
            if not gltf_settings_node:
                gltf_settings_node = nodeutils.make_gltf_settings_node(nodes)
            if utils.B330():
                split_node = nodeutils.make_shader_node(nodes, "ShaderNodeSeparateColor")
                split_node.mode = "RGB"
                nodeutils.link_nodes(links, tex_nodes["GLTF"], "Color", split_node, "Color")
                nodeutils.link_nodes(links, split_node, "Red", gltf_settings_node, "Occlusion")
                nodeutils.link_nodes(links, split_node, "Green", bsdf_node, roughness_socket)
                nodeutils.link_nodes(links, split_node, "Blue", bsdf_node, metallic_socket)
            else:
                split_node = nodeutils.make_shader_node(nodes, "ShaderNodeSeparateRGB")
                nodeutils.link_nodes(links, tex_nodes["GLTF"], "Color", split_node, "Image")
                nodeutils.link_nodes(links, split_node, "R", gltf_settings_node, "Occlusion")
                nodeutils.link_nodes(links, split_node, "G", bsdf_node, roughness_socket)
                nodeutils.link_nodes(links, split_node, "B", bsdf_node, metallic_socket)

    if tex_nodes["Diffuse"] or tex_nodes["AO"]:

        if props.target_mode == "GLTF": # unpacked GLTF diffuse & AO
            nodeutils.link_nodes(links, tex_nodes["Diffuse"], "Color", bsdf_node, base_color_socket)
            if not gltf_settings_node:
                gltf_settings_node = nodeutils.make_gltf_settings_node(nodes)
            nodeutils.link_nodes(links, tex_nodes["AO"], "Color", gltf_settings_node, "Occlusion")
        else:
            mix_node = nodeutils.make_mixrgb_node(nodes, "MULTIPLY")
            nodeutils.set_node_input_value(mix_node, "Fac", ao_strength)
            nodeutils.link_nodes(links, tex_nodes["Diffuse"], "Color", mix_node, "Color1")
            nodeutils.link_nodes(links, tex_nodes["AO"], "Color", mix_node, "Color2")
            nodeutils.link_nodes(links, mix_node, "Color", bsdf_node, base_color_socket)

    elif tex_nodes["Diffuse"]:
        nodeutils.link_nodes(links, tex_nodes["Diffuse"], "Color", bsdf_node, base_color_socket)

    if tex_nodes["Subsurface"]:
        nodeutils.link_nodes(links, tex_nodes["Subsurface"], "Color", bsdf_node, sss_socket)
        nodeutils.set_node_input_value(bsdf_node, "Subsurface Radius", sss_radius)
        if mix_node:
            nodeutils.link_nodes(links, mix_node, "Color", bsdf_node, "Subsurface Color")
        else:
            nodeutils.link_nodes(links, tex_nodes["Diffuse"], "Color", bsdf_node, "Subsurface Color")

    if tex_nodes["Metallic"]:
        nodeutils.link_nodes(links, tex_nodes["Metallic"], "Color", bsdf_node, metallic_socket)
    if tex_nodes["Specular"]:
        nodeutils.link_nodes(links, tex_nodes["Specular"], "Color", bsdf_node, specular_socket)
    if tex_nodes["Roughness"]:
        nodeutils.link_nodes(links, tex_nodes["Roughness"], "Color", bsdf_node, roughness_socket)
    if tex_nodes["Emission"]:
        nodeutils.link_nodes(links, tex_nodes["Emission"], "Color", bsdf_node, emission_socket)

    thickness_value_node = None
    if tex_nodes["Transmission"]:
        nodeutils.link_nodes(links, tex_nodes["Transmission"], "Color", bsdf_node, transmission_socket)
        if utils.B420() and thickness > 0.0:
            thickness_value_node = nodeutils.make_value_node(nodes, "Thickness", "thickness", thickness)
            nodeutils.link_nodes(links, thickness_value_node, "Value", output_node, "Thickness")
            materials.set_material_alpha(mat, "DITHERED")
    elif tex_nodes["Alpha"]:
        nodeutils.link_nodes(links, tex_nodes["Alpha"], "Color", bsdf_node, alpha_socket)

    if tex_nodes["Normal"]:
        normal_map_node = nodeutils.make_shader_node(nodes, "ShaderNodeNormalMap")
        nodeutils.link_nodes(links, tex_nodes["Normal"], "Color", normal_map_node, "Color")
        nodeutils.link_nodes(links, normal_map_node, "Normal", bsdf_node, normal_socket)
        nodeutils.set_node_input_value(normal_map_node, "Strength", normal_strength)
    elif tex_nodes["Normal"]:
        bump_map_node = nodeutils.make_shader_node(nodes, "ShaderNodeBump")
        nodeutils.link_nodes(links, tex_nodes["Normal"], "Color", bump_map_node, "Height")
        nodeutils.link_nodes(links, bump_map_node, "Normal", bsdf_node, normal_socket)
        nodeutils.set_node_input_value(bump_map_node, "Distance", bump_distance)

    if tex_nodes["MicroNormal"]:
        if normal_map_node is None:
            normal_map_node = nodeutils.make_shader_node(nodes, "ShaderNodeNormalMap")
            nodeutils.link_nodes(links, normal_map_node, "Normal", bsdf_node, normal_socket)
        micro_mix_node = nodeutils.make_mixrgb_node(nodes, "OVERLAY")
        micro_mapping_node = nodeutils.make_shader_node(nodes, "ShaderNodeMapping")
        micro_texcoord_node = nodeutils.make_shader_node(nodes, "ShaderNodeTexCoord")
        nodeutils.set_node_input_value(micro_mix_node, "Fac", micro_normal_strength)
        nodeutils.link_nodes(links, micro_texcoord_node, "UV", micro_mapping_node, "Vector")
        nodeutils.link_nodes(links, micro_mapping_node, "Vector", tex_nodes["MicroNormal"], "Vector")
        nodeutils.set_node_input_value(micro_mapping_node, "Scale", micro_normal_scale)
        if tex_nodes["MicroNormalMask"]:
            micro_mask_mult_node = nodeutils.make_math_node(nodes, "MULTIPLY", 1, micro_normal_strength)
            nodeutils.link_nodes(links, tex_nodes["MicroNormalMask"], "Color", micro_mask_mult_node, 0)
            nodeutils.link_nodes(links, micro_mask_mult_node, "Value", micro_mix_node, "Fac")
        if tex_nodes["Normal"]:
            nodeutils.link_nodes(links, tex_nodes["Normal"], "Color", micro_mix_node, "Color1")
        nodeutils.link_nodes(links, tex_nodes["MicroNormal"], "Color", micro_mix_node, "Color2")
        nodeutils.link_nodes(links, micro_mix_node, "Color", normal_map_node, "Color")

    if utils.B400():
        nodeutils.set_node_input_value(bsdf_node, "Emission Strength", emission_strength)

    set_loc(bsdf_node, (200, 400))
    set_loc(output_node, (600, 400))

    set_loc(tex_nodes["Diffuse"], (-600, 600))
    set_loc(tex_nodes["AO"], (-900, 600))
    set_loc(mix_node, (-300, 600))

    set_loc(thickness_value_node, (250, 520))

    if props.target_mode == "GLTF" and props.pack_gltf:
        set_loc(tex_nodes["BaseMap"], (-600, 600))
        set_loc(tex_nodes["GLTF"], (-900, 0))
        set_loc(split_node, (-600, 0))
        set_loc(gltf_settings_node, (200, 500))
    else:
        set_loc(gltf_settings_node, (-600, 700))
        set_loc(tex_nodes["BaseMap"], (-1800, 600))
        set_loc(tex_nodes["Mask"], (-1800, 300))
        set_loc(tex_nodes["Detail"], (-1800, 0))

    set_loc(tex_nodes["Subsurface"], (-600, 300))
    set_loc(tex_nodes["Thickness"], (-900, 300))

    set_loc(tex_nodes["Metallic"], (-1200, 0))
    set_loc(tex_nodes["Specular"], (-900, 0))
    set_loc(tex_nodes["Roughness"], (-600, 0))

    set_loc(tex_nodes["Transmission"], (-1200, -300))
    set_loc(tex_nodes["Emission"], (-900, -300))
    set_loc(tex_nodes["Alpha"], (-600, -300))

    set_loc(tex_nodes["Normal"], (-900, -600))
    set_loc(normal_map_node, (-300, -600))
    set_loc(tex_nodes["Bump"], (-900, -600))
    set_loc(bump_map_node, (-300, -600))
    set_loc(tex_nodes["MicroNormalMask"], (-1200, -600))
    set_loc(tex_nodes["MicroNormal"], (-1500, -600))

    set_loc(micro_mix_node, (-470,-690))
    set_loc(micro_mapping_node, (-1710,-600))
    set_loc(micro_texcoord_node, (-1890,-600))
    set_loc(micro_mask_mult_node, (-640,-600))


def bake_character(context, chr_cache):
    props = vars.bake_props()
    prefs = vars.prefs()

    utils.log_info("")
    utils.log_info("Baking Selected Objects:")
    utils.log_info("")

    if prefs.bake_objects_mode == "SELECTED":
        selected_objects = [ o for o in context.selected_objects if utils.object_exists_is_mesh(o) ]
    else:
        selected_objects = None
    objects = get_export_objects(chr_cache, only_objects=selected_objects)

    bake_state = prep_bake(context, samples=props.bake_samples,
                           image_format=props.target_format,
                           make_surface=True)

    if prefs.bake_use_gpu:
        set_cycles_samples(context, samples=props.bake_samples, adaptive_samples=0.01, use_gpu=True, denoising=False)

    materials_done = []
    obj : bpy.types.Object
    for obj in objects:
        if obj.type == "MESH":
            bake_character_object(context, chr_cache, obj, bake_state, materials_done)
    materials_done.clear()

    post_bake(context, bake_state)


def next_uid():
    props = vars.bake_props()
    uid = props.auto_increment
    props.auto_increment += 1
    return uid


def get_target_map(suffix):
    props = vars.bake_props()

    bake_maps = vars.get_bake_target_maps(props.target_mode)

    if suffix in bake_maps:
        return bake_maps[suffix]

    utils.log_error("No matching target map for suffix: " + suffix)
    return None


def get_target_map_suffix(suffix):
    target_map = get_target_map(suffix)
    if target_map:
        return target_map[0]

    utils.log_error("No matching target map suffix: " + suffix)
    return "None"


def get_int_prop_by_name(props, prop_name):
    scope = locals()
    prop_val = eval("props." + prop_name)
    return int(prop_val)


def get_max_texture_size(mat, mat_cache, tex_list, input_list):
    """
    Attempts to get the largest texture size from the given named texure nodes (CC3 materials),
    then falls back to finding the largest texture connected to the given list of inputs to the BSDF shader
    """
    if mat is None or mat.node_tree is None or mat.node_tree.nodes is None:
        return vars.NO_SIZE

    max_size = 0

    if mat_cache is not None and tex_list is not None:
        for t in tex_list:
            tex_node = nodeutils.find_shader_texture(mat.node_tree.nodes, t)
            if tex_node is not None:
                size = nodeutils.get_tex_image_size(tex_node)
                utils.log_info("Found CC3 texture: " + t + " size: " + str(size))
                if size > max_size:
                    max_size = size

    elif input_list is not None and max_size == 0:
        bsdf_node = nodeutils.get_bsdf_node(mat)
        max_size = 0
        size = get_connected_texture_size(bsdf_node, 0, input_list)
        utils.log_info("Detected largest texture size: " + str(size))
        max_size = size

    # here we can override the result based on the mat_cache.material_type and the looked for tex_list
    if mat_cache is not None:
        if mat_cache.material_type in vars.TEX_SIZE_OVERRIDE:
            mat_overrides = vars.TEX_SIZE_OVERRIDE[mat_cache.material_type]
            for t in tex_list:
                if t in mat_overrides:
                    utils.log_info("Overriding size for material: " + mat.name + " texture: " + t + " size: " + str(mat_overrides[t]))
                    size = mat_overrides[t]
                    if size > max_size:
                        max_size = size

    if max_size == 0:
        max_size = vars.NO_SIZE

    utils.log_info("Max texture size: " + str(max_size))

    return max_size


# suffix as defined in: vars.py *_MAPS
def detect_bake_size_from_suffix(mat, mat_cache, suffix):
    props = vars.bake_props()

    target_map = get_target_map(suffix)
    if target_map:
        target_size = target_map[1]
        if target_size in vars.TEX_SIZE_DETECT:
            tex_size_detect = vars.TEX_SIZE_DETECT[target_size]
            tex_list = tex_size_detect[0]
            input_list = tex_size_detect[1]
            return get_max_texture_size(mat, mat_cache, tex_list, input_list)

    # otherwise just return the default of 1024
    return vars.DEFAULT_SIZE


def apply_override_size(mat, global_suffix, width, height):

    # get either the global default props or the material specific props if they exist...
    props = vars.bake_props()
    p = get_material_bake_settings(mat)
    if p is None:
        p = props

    max_size = int(props.max_size)

    # if overriding with custom max sizes:
    if props.custom_sizes:
        bake_maps = vars.get_bake_target_maps(props.target_mode)
        if global_suffix in bake_maps:
            max_size = get_int_prop_by_name(p, bake_maps[global_suffix][1])
            utils.log_info(f"{global_suffix} map {props.target_mode} maximum map size: {width} x {height}")

    if width > max_size:
        width = max_size
    if height > max_size:
        height = max_size

    return width, height


def get_bake_target_material_name(name, uid):
    props = vars.bake_props()

    # Sketchfab recommends no spaces or symbols in the texture names...
    if props.target_mode == "SKETCHFAB":
        text = name.replace("_", "").replace("-", "").replace(".", "")
        text += "B" + str(uid)
    else:
        text = name + "_B" + str(uid)
    return text


def bake_character_object(context, chr_cache, obj, bake_state, materials_done):
    props = vars.bake_props()

    if not utils.object_exists_is_mesh(obj):
        utils.log_warn(f"Object doesn't exist!")
        return

    for slot in obj.material_slots:
        source_mat = slot.material
        if source_mat is None: continue
        bake_cache = get_export_bake_cache(source_mat)

        # in case we haven't reverted to the source materials get the real source_mat:
        if (bake_cache and
            bake_cache.source_material is not None and
            bake_cache.source_material != source_mat):
            utils.log_info("Using cached source material!")
            source_mat = bake_cache.source_material

        if not utils.material_exists(source_mat):
            utils.log_warn(f"No Material in slot!")
            continue

        source_mat_cache = chr_cache.get_material_cache(source_mat)
        if not source_mat_cache:
            utils.log_warn(f"Material has no character data: {source_mat.name}. Skipping!")
            continue

        # if there is no BSDF node, don't process.
        bsdf_node = None
        if source_mat and source_mat.node_tree:
            bsdf_node = nodeutils.get_bsdf_node(source_mat)
        if bsdf_node is None:
            utils.log_warn(f"Material has no BSDF node: {source_mat.name}. Skipping!")
            continue

        # only process each material once:
        if source_mat not in materials_done:
            materials_done.append(source_mat)

            old_mat = None
            if bake_cache is None:
                uid = next_uid()
            else:
                uid = bake_cache.uid
                if bake_cache.baked_material:
                    old_mat = bake_cache.baked_material

            bake_mat_name = get_bake_target_material_name(source_mat.name, uid)

            # copy the source material
            bake_mat = source_mat.copy()
            bake_mat.name = "TEMP_" + bake_mat_name

            # try to find any old baked material by name
            if old_mat is None:
                for m in bpy.data.materials:
                    if m.name == bake_mat_name:
                        old_mat = m

            # replace all of the old baked materials with the new copy:
            if old_mat:
                for o in context.scene.objects:
                    if o != obj and o.type == "MESH" and o.data.materials:
                        for s in o.material_slots:
                            if s.material and s.material == old_mat:
                                s.material = bake_mat
                # remove the old material once all copies of it have been replaced...
                bpy.data.materials.remove(old_mat)

            # give the new copy the correct name
            bake_mat.name = bake_mat_name

            # add/update the bake cache
            add_material_bake_cache(uid, source_mat, bake_mat)

            # attach the bake material to the bake surface plane
            set_bake_material(bake_state, bake_mat)

            try:
                bake_export_material(context, bake_mat, source_mat, source_mat_cache)
                slot.material = bake_mat
            except Exception as e:
               utils.log_error("Bake Character Object: Something went horribly wrong!", e)

        else:
            # if the material has already been baked elsewhere, replace the material here
            if bake_cache and slot.material != bake_cache.baked_material:
                slot.material = bake_cache.baked_material


def get_export_bake_cache(mat):
    props = vars.bake_props()
    for bc in props.bake_cache:
        if bc.source_material == mat or bc.baked_material == mat:
            return bc
    return None


def add_material_bake_cache(uid, source_mat, bake_mat):
    props = vars.bake_props()
    bc = get_export_bake_cache(source_mat)
    if bc is None:
        bc = props.bake_cache.add()
        bc.uid = uid
        bc.source_material = source_mat
    bc.baked_material = bake_mat
    return bc


def remove_material_bake_cache(mat):
    props = vars.bake_props()
    bc = get_export_bake_cache(mat)
    if bc:
        utils.remove_from_collection(props.bake_cache, bc)


def get_material_bake_settings(mat):
    props = vars.bake_props()
    if mat:
        for ms in props.material_settings:
            if ms.material == mat:
                return ms
    return None


def add_material_bake_settings(mat):
    props = vars.bake_props()
    ms = get_material_bake_settings(mat)
    if ms is None:
        ms = props.material_settings.add()
        ms.material = mat
        ms.diffuse_size = props.diffuse_size
        ms.ao_size = props.ao_size
        ms.sss_size = props.sss_size
        ms.thickness_size = props.thickness_size
        ms.transmission_size = props.transmission_size
        ms.metallic_size = props.metallic_size
        ms.specular_size = props.specular_size
        ms.roughness_size = props.roughness_size
        ms.emissive_size = props.emissive_size
        ms.alpha_size = props.alpha_size
        ms.normal_size = props.normal_size
        ms.bump_size = props.bump_size
        ms.mask_size = props.mask_size
        ms.detail_size = props.detail_size
    return ms


def remove_material_bake_settings(mat):
    props = vars.bake_props()
    for ms in props.material_settings:
        if ms.material == mat:
            utils.remove_from_collection(props.material_settings, ms)


def revert_baked_materials(chr_cache):

    objects = get_export_objects(chr_cache)

    for obj in objects:
        if obj.type == "MESH":
            for i in range(0, len(obj.data.materials)):
                mat = obj.data.materials[i]
                bc = get_export_bake_cache(mat)
                if bc and bc.baked_material == mat:
                    obj.data.materials[i] = bc.source_material


def restore_baked_materials(chr_cache):

    objects = get_export_objects(chr_cache)

    for obj in objects:
        if obj.type == "MESH":
            for i in range(0, len(obj.data.materials)):
                mat = obj.data.materials[i]
                bc = get_export_bake_cache(mat)
                if bc and bc.source_material == mat:
                    obj.data.materials[i] = bc.baked_material


class CCICBaker(bpy.types.Operator):
    """Bake CC/iC Character For Export"""
    bl_idname = "ccic.baker"
    bl_label = "Baker"
    bl_options = {"REGISTER"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    def execute(self, context):
        props = vars.props()
        prefs = vars.prefs()

        mode_selection = utils.store_mode_selection_state()

        chr_cache = props.get_context_character_cache(context)

        if not chr_cache:
            self.report({"ERROR"}, "No current character!")
            return {"FINISHED"}

        utils.start_timer()

        if self.param == "BAKE":
            bake_character(context, chr_cache)
            utils.restore_mode_selection_state(mode_selection)

        utils.log_timer("Baking Completed!", "m")

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "BAKE":
            return "Bake Textures..."
        return ""


class CCICBakeSettings(bpy.types.Operator):
    """Bake Settings"""
    bl_idname = "ccic.bakesettings"
    bl_label = "Bake Settings"
    bl_options = {"REGISTER"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    def execute(self, context):
        props = vars.props()
        prefs = vars.prefs()

        obj = context.object
        mat = utils.get_context_material(context)
        mat_settings = get_material_bake_settings(mat)
        chr_cache = props.get_context_character_cache(context)

        if obj and obj.type == "MESH" and mat:

            if self.param == "ADD":
                add_material_bake_settings(mat)

            if self.param == "REMOVE":
                remove_material_bake_settings(mat)

            if self.param == "SOURCE":
                revert_baked_materials(chr_cache)

            if self.param == "BAKED":
                restore_baked_materials(chr_cache)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "ADD":
            return "Add custom bake settings for this material."
        if properties.param == "REMOVE":
            return "Remove custom bake settings for this material."
        if properties.param == "SOURCE":
            return "Revert to the source materials."
        if properties.param == "BAKED":
            return "Restore the baked materials."
        if properties.param == "DEFAULTS":
            return "Attempt to assign default settings to each material in the selected objects."
        return ""


JPEGIFY_FORMATS = [
    "BMP",
    "PNG",
    "TARGA",
    "TARGA_RAW",
    "TIFF",
]


class CCICJpegify(bpy.types.Operator):
    """Jpegifyer"""
    bl_idname = "ccic.jpegify"
    bl_label = "Jpegify"
    bl_options = {"REGISTER"}

    def execute(self, context):
        props = vars.bake_props()

        bake_path = get_bake_path()
        os.makedirs(bake_path, exist_ok=True)
        context.scene.render.image_settings.quality = props.jpeg_quality

        for img in bpy.data.images:

            try:
                if img and img.size[0] > 0 and img.size[1] > 0:
                    if img.file_format in JPEGIFY_FORMATS:
                        img.file_format = "JPEG"
                        dir, file = os.path.split(img.filepath)
                        root, ext = os.path.splitext(file)
                        new_path = os.path.join(bake_path, root + ".jpg")
                        img.filepath_raw = new_path
                        img.save()
                    else:
                        if not os.path.normcase(os.path.realpath(bake_path)) in os.path.normcase(os.path.realpath(img.filepath)):
                            dir, file = os.path.split(img.filepath)
                            new_path = os.path.join(bake_path, file)
                            img.filepath_raw = new_path
                            img.save()
                            img.reload()
            except:
                utils.log_error("ERROR")

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):
        return "Makes all suitable texture maps jpegs and puts them all in the bake folder."

