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
from . import colorspace, imageutils, wrinkle, nodeutils, utils, params, vars

BAKE_SAMPLES = 4
IMAGE_FORMAT = "PNG"
BAKE_INDEX = 1001
BUMP_BAKE_MULTIPLIER = 2.0
NODE_CURSOR = Vector((0, 0))

def init_bake(id = 1001):
    global BAKE_INDEX
    BAKE_INDEX = id


def set_cycles_samples(samples, adaptive_samples = -1, denoising = False, time_limit = 0, use_gpu = False):
    bpy.context.scene.cycles.samples = samples
    if utils.is_blender_version("3.0.0"):
        bpy.context.scene.cycles.device = 'GPU' if use_gpu else 'CPU'
        bpy.context.scene.cycles.preview_samples = samples
        bpy.context.scene.cycles.use_adaptive_sampling = adaptive_samples >= 0
        bpy.context.scene.cycles.adaptive_threshold = adaptive_samples
        bpy.context.scene.cycles.use_preview_adaptive_sampling = adaptive_samples >= 0
        bpy.context.scene.cycles.preview_adaptive_threshold = adaptive_samples
        bpy.context.scene.cycles.use_denoising = denoising
        bpy.context.scene.cycles.use_preview_denoising = denoising
        bpy.context.scene.cycles.use_auto_tile = False
        bpy.context.scene.cycles.time_limit = time_limit


def prep_bake(mat = None, samples = BAKE_SAMPLES, image_format = IMAGE_FORMAT, make_surface = True):
    state = {}

    # cycles settings
    state["samples"] = bpy.context.scene.cycles.samples
    # Blender 3.0
    if utils.is_blender_version("3.0.0"):
        state["preview_samples"] = bpy.context.scene.cycles.preview_samples
        state["use_adaptive_sampling"] = bpy.context.scene.cycles.use_adaptive_sampling
        state["use_preview_adaptive_sampling"] = bpy.context.scene.cycles.use_preview_adaptive_sampling
        state["use_denoising"] = bpy.context.scene.cycles.use_denoising
        state["use_preview_denoising"] = bpy.context.scene.cycles.use_preview_denoising
        state["use_auto_tile"] =  bpy.context.scene.cycles.use_auto_tile
    # render settings
    state["file_format"] = bpy.context.scene.render.image_settings.file_format
    state["color_depth"] = bpy.context.scene.render.image_settings.color_depth
    state["color_mode"] = bpy.context.scene.render.image_settings.color_mode
    state["use_bake_multires"] =bpy.context.scene.render.use_bake_multires
    state["use_selected_to_active"] = bpy.context.scene.render.bake.use_selected_to_active
    state["use_pass_direct"] = bpy.context.scene.render.bake.use_pass_direct
    state["use_pass_indirect"] = bpy.context.scene.render.bake.use_pass_indirect
    state["margin"] = bpy.context.scene.render.bake.margin
    state["use_clear"] = bpy.context.scene.render.bake.use_clear
    # Blender 2.92
    if utils.is_blender_version("2.92.0"):
        state["target"] = bpy.context.scene.render.bake.target
    # color management
    state["view_transform"] = bpy.context.scene.view_settings.view_transform
    state["look"] = bpy.context.scene.view_settings.look
    state["gamma"] = bpy.context.scene.view_settings.gamma
    state["exposure"] = bpy.context.scene.view_settings.exposure
    state["colorspace"] = bpy.context.scene.sequencer_colorspace_settings.name

    bpy.context.scene.cycles.samples = samples
    bpy.context.scene.render.image_settings.file_format = image_format
    bpy.context.scene.render.use_bake_multires = False
    bpy.context.scene.render.bake.use_selected_to_active = False
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.margin = 16
    bpy.context.scene.render.bake.use_clear = True
    # color management settings affect the baked output so set them to standard/raw defaults:
    bpy.context.scene.view_settings.view_transform = 'Standard'
    bpy.context.scene.view_settings.look = 'None'
    bpy.context.scene.view_settings.gamma = 1
    bpy.context.scene.view_settings.exposure = 0
    colorspace.set_sequencer_color_space("Raw")

    # Blender 3.0
    if utils.is_blender_version("3.0.0"):
        bpy.context.scene.cycles.preview_samples = samples
        bpy.context.scene.cycles.use_adaptive_sampling = False
        bpy.context.scene.cycles.use_preview_adaptive_sampling = False
        bpy.context.scene.cycles.use_denoising = False
        bpy.context.scene.cycles.use_preview_denoising = False
        bpy.context.scene.cycles.use_auto_tile = False

    # Blender 2.92
    if utils.is_blender_version("2.92.0"):
        bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'

    # go into wireframe mode (so Blender doesn't update or recompile the material shaders while
    # we manipulate them for baking, and also so Blender doesn't fire up the cycles viewport...):
    state["shading"] = bpy.context.space_data.shading.type
    bpy.context.space_data.shading.type = 'WIREFRAME'
    # set cycles rendering mode for baking
    state["engine"] = bpy.context.scene.render.engine
    bpy.context.scene.render.engine = 'CYCLES'
    state["cycles_bake_type"] = bpy.context.scene.cycles.bake_type
    state["render_bake_type"] = bpy.context.scene.render.bake_type
    bpy.context.scene.cycles.bake_type = "COMBINED"


    if make_surface:

        # deselect everything
        bpy.ops.object.select_all(action='DESELECT')
        # create the baking plane, a single quad baking surface for an even sampling across the entire texture
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        bake_surface = bpy.context.active_object

        # attach the material to bake to the baking surface plane
        # (the baking plane also ensures that only one material is baked onto only one target image)
        if len(bake_surface.data.materials) == 0:
            bake_surface.data.materials.append(mat)
        else:
            bake_surface.data.materials[0] = mat
        state["bake_surface"] = bake_surface

    return state


def post_bake(state):
    # cycles settings
    bpy.context.scene.cycles.samples = state["samples"]
    # Blender 3.0
    if utils.is_blender_version("3.0.0"):
        bpy.context.scene.cycles.preview_samples = state["preview_samples"]
        bpy.context.scene.cycles.use_adaptive_sampling = state["use_adaptive_sampling"]
        bpy.context.scene.cycles.use_preview_adaptive_sampling = state["use_preview_adaptive_sampling"]
        bpy.context.scene.cycles.use_denoising = state["use_denoising"]
        bpy.context.scene.cycles.use_preview_denoising = state["use_preview_denoising"]
        bpy.context.scene.cycles.use_auto_tile = state["use_auto_tile"]
    # render settings
    bpy.context.scene.render.image_settings.file_format = state["file_format"]
    bpy.context.scene.render.image_settings.color_depth = state["color_depth"]
    bpy.context.scene.render.image_settings.color_mode = state["color_mode"]
    bpy.context.scene.render.use_bake_multires = state["use_bake_multires"]
    bpy.context.scene.render.bake.use_selected_to_active = state["use_selected_to_active"]
    bpy.context.scene.render.bake.use_pass_direct = state["use_pass_direct"]
    bpy.context.scene.render.bake.use_pass_indirect = state["use_pass_indirect"]
    bpy.context.scene.render.bake.margin = state["margin"]
    bpy.context.scene.render.bake.use_clear = state["use_clear"]
    # Blender 2.92
    if utils.is_blender_version("2.92.0"):
        bpy.context.scene.render.bake.target = state["target"]
    # color management
    bpy.context.scene.view_settings.view_transform = state["view_transform"]
    bpy.context.scene.view_settings.look = state["look"]
    bpy.context.scene.view_settings.gamma = state["gamma"]
    bpy.context.scene.view_settings.exposure = state["exposure"]
    bpy.context.scene.sequencer_colorspace_settings.name = state["colorspace"]
    # render engine
    bpy.context.scene.render.engine = state["engine"]
    # viewport shading
    bpy.context.space_data.shading.type = state["shading"]
    # bake type
    bpy.context.scene.cycles.bake_type = state["cycles_bake_type"]
    bpy.context.scene.render.bake_type = state["render_bake_type"]

    # remove the bake surface
    if "bake_surface" in state:
        bpy.data.objects.remove(state["bake_surface"])


def get_existing_bake_image(mat, channel_id, width, height, shader_node, socket, bake_dir, name_prefix = "", force_srgb = False, channel_pack = False, exact_name = False):



    return None


def get_bake_image(mat, channel_id, width, height, shader_node, socket, bake_dir,
                  name_prefix = "", force_srgb = False, channel_pack = False, exact_name = False, underscores = True):
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
    if "Diffuse Map" in socket_name or channel_id == "Base Color" or force_srgb:
        is_data = False
    if channel_pack:
        alpha = True

    # make (and save) the target image
    image, exists = get_image_target(image_name, width, height, bake_dir, is_data, alpha, channel_packed = channel_pack)

    # make sure we don't reuse an image as the target, that is also in the nodes we are baking from...
    i = 0
    base_name = image_name
    if shader_node and socket:
        while nodeutils.is_image_node_connected_to_socket(shader_node, socket, image, []):
            i += 1
            old_name = image_name
            image_name = base_name + "_" + str(i)
            utils.log_info(f"Image: {old_name} in use, trying: {image_name}")
            image, exists = get_image_target(image_name, width, height, bake_dir, is_data, alpha, channel_packed = channel_pack)

    return image, image_name, exists


def bake_node_socket_input(node, socket, mat, channel_id, bake_dir, name_prefix = "",
                           override_size = 0, size_override_node = None, size_override_socket = None,
                           exact_name = False, underscores = True):
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
                                               name_prefix = name_prefix, exact_name = exact_name, underscores = underscores)
    image_node = cycles_bake_color_output(mat, source_node, source_socket, image, image_name)

    # remove the image node
    nodes = mat.node_tree.nodes
    nodes.remove(image_node)

    return image


def bake_node_socket_output(node, socket, mat, channel_id, bake_dir, name_prefix = "",
                            override_size = 0, size_override_node = None, size_override_socket = None,
                            exact_name = False, underscores = True):
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
                                               name_prefix = name_prefix, exact_name = exact_name, underscores = underscores)
    image_node = cycles_bake_color_output(mat, node, socket, image, image_name)

    # remove the image node
    nodes = mat.node_tree.nodes
    nodes.remove(image_node)

    return image


def bake_rl_bump_and_normal(shader_node, bsdf_node, mat, channel_id, bake_dir,
                            normal_socket_name = "Normal Map", bump_socket_name = "Bump Map",
                            normal_strength_socket_name = "Normal Strength", bump_distance_socket_name = "Bump Strength",
                            name_prefix = "", override_size = 0):
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
    image, image_name, exists = get_bake_image(mat, channel_id, width, height, shader_node, normal_socket_name, bake_dir, name_prefix = name_prefix)
    image_node = cycles_bake_normal_output(mat, bsdf_node, image, image_name)

    # remove the bake nodes and restore the normal links to the bsdf
    if bump_map_node:
        nodes.remove(bump_map_node)
    if normal_map_node:
        nodes.remove(normal_map_node)
    if image_node:
        nodes.remove(image_node)
    nodeutils.link_nodes(links, bsdf_normal_node, bsdf_normal_socket, bsdf_node, "Normal")

    return image


def bake_bsdf_normal(bsdf_node, mat, channel_id, bake_dir, name_prefix = "", override_size = 0):
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
        bump_distance = normal_input_node.inputs["Distance"].default_value
        normal_input_node.inputs["Distance"].default_value = bump_distance * BUMP_BAKE_MULTIPLIER

    # bake the source node output onto the target image and re-save it
    image, image_name, exists = get_bake_image(mat, channel_id, width, height, bsdf_node, "Normal", bake_dir, name_prefix = name_prefix)
    image_node = cycles_bake_normal_output(mat, bsdf_node, image, image_name)

    if normal_input_node and normal_input_node.type == "BUMP":
        normal_input_node.inputs["Distance"].default_value = bump_distance

    if image_node:
        nodes.remove(image_node)

    return image


def pack_value_image(value, mat, channel_id, bake_dir, name_prefix = "", size = 64):
    """Generates a 64 x 64 texture of a single value. Linear or sRGB depending on channel id.\n
       Image name and path is determined by the texture channel id, material name, bake dir and name prefix."""

    width = size
    height = size
    image, image_name, exists = get_bake_image(mat, channel_id, width, height, None, "", bake_dir, name_prefix = name_prefix)

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
              image_r = None, image_g = None, image_b = None, image_a = None,
              value_r = 0, value_g = 0, value_b = 0, value_a = 0,
              name_prefix = "", min_size = 64, srgb = False, max_size = 0, reuse_existing = False):
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
    image, image_name, exists = get_bake_image(mat, channel_id, width, height, None, "", bake_dir, name_prefix = name_prefix,
                                               force_srgb=srgb, channel_pack=True, exact_name=True)

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


def cycles_bake_color_output(mat, source_node, source_socket, image : bpy.types.Image, image_name):
    """Runs a cycles bake of the supplied source node and socket output onto the supplied image.\n
       Returns a new image node with the image."""

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")
    output_source, output_source_socket = nodeutils.get_node_and_socket_connected_to_input(output_node, "Surface")

    image_node = nodeutils.make_image_node(nodes, image, "bake")
    image_node.name = image_name

    bpy.context.scene.cycles.samples = BAKE_SAMPLES
    utils.log_info("Baking: " + image_name)

    bake_surface = prep_bake(mat=mat, make_surface=True)

    nodeutils.link_nodes(links, source_node, source_socket, output_node, "Surface")
    image_node.select = True
    nodes.active = image_node
    bpy.ops.object.bake(type='COMBINED')

    bpy.context.scene.render.image_settings.color_depth = '8'
    bpy.context.scene.render.image_settings.color_mode = 'RGB' if image.depth == 24 else 'RGBA'

    image.save_render(filepath = bpy.path.abspath(image.filepath), scene = bpy.context.scene)
    image.reload()

    if output_source:
        nodeutils.link_nodes(links, output_source, output_source_socket, output_node, "Surface")

    post_bake(bake_surface)

    return image_node


def cycles_bake_normal_output(mat, bsdf_node, image, image_name):
    """Runs a cycles bake of the normal output of the supplied BSDF shader node to the supplied image.
       Returns a new image node with the image."""

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")

    image_node = nodeutils.make_image_node(nodes, image, "bake")
    image_node.name = image_name

    bpy.context.scene.cycles.samples = BAKE_SAMPLES
    utils.log_info("Baking normal: " + image_name)

    bake_surface = prep_bake(mat=mat, make_surface=True)

    nodeutils.link_nodes(links, bsdf_node, "BSDF", output_node, "Surface")
    image_node.select = True
    nodes.active = image_node

    bpy.ops.object.bake(type='NORMAL')

    bpy.context.scene.render.image_settings.color_depth = '8'
    bpy.context.scene.render.image_settings.color_mode = 'RGB' if image.depth == 24 else 'RGBA'
    image.save_render(filepath = bpy.path.abspath(image.filepath), scene = bpy.context.scene)
    image.reload()

    post_bake(bake_surface)

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

    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
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


def get_image_target(image_name, width, height, image_dir, is_data = True, has_alpha = False, force_new = False, channel_packed = False):
    format = IMAGE_FORMAT
    depth = 24
    if has_alpha:
        depth = 32

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
                    if img.file_format == format and img.depth == depth:
                        utils.log_info("Reusing image: " + image_name)
                        try:
                            if img.size[0] != width or img.size[1] != height:
                                img.scale(width, height)
                            return img, True
                        except:
                            utils.log_info("Bad image: " + img.name)
                    else:
                        utils.log_info("Wrong format: " + img.name + ", " + img_folder + "==" + image_dir + "?, " + img.file_format + "==" + format + "?, depth: " + str(depth) + "==" + str(img.depth) + "?")
                    if img:
                        bpy.data.images.remove(img)

    # or if the image file exists (but not in blender yet)
    file = imageutils.find_file_by_name(image_dir, image_name)
    if file:
        if is_data:
            color_space = "Non-Color"
        else:
            color_space = "sRGB"
        img = imageutils.load_image(file, color_space, reuse_existing = False)
        try:
            if img.file_format == format and img.depth == depth:
                utils.log_info("Reusing found image file: " + img.filepath)
                if img.size[0] != width or img.size[1] != height:
                    img.scale(width, height)
                return img, True
        except:
            utils.log_info("Bad found image file: " + img.name)
        if img:
            bpy.data.images.remove(img)

    # or just make a new one:
    utils.log_info("Creating new image: " + image_name + " size: " + str(width))
    img = imageutils.make_new_image(image_name, width, height, format, image_dir, is_data, has_alpha, channel_packed)
    return img, False


def get_bake_dir(chr_cache):
    bake_path = os.path.join(chr_cache.import_dir, "textures", chr_cache.import_name, "Blender_Baked")
    return bake_path


def combine_normal(chr_cache, mat_cache):
    """Combines the normal and bump maps by baking and connecting a new normal map."""

    init_bake(5001)

    mat = mat_cache.material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    mat_name = utils.strip_name(mat.name)
    shader = params.get_shader_name(mat_cache)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader)
    bake_path = get_bake_dir(chr_cache)

    selection = bpy.context.selected_objects.copy()
    active = bpy.context.active_object

    if mat_cache.material_type == "DEFAULT" or mat_cache.material_type == "SSS":

        nodeutils.clear_cursor()

        normal_node, normal_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, "Normal Map")
        bump_node, bump_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, "Bump Map")

        if normal_node and bump_node:

            normal_image = bake_rl_bump_and_normal(shader_node, bsdf_node, mat, "Normal", bake_path)
            normal_image_name = utils.unique_name("(NORMAL)")
            normal_image_node = nodeutils.make_image_node(nodes, normal_image, normal_image_name)
            nodeutils.link_nodes(links, normal_image_node, "Color", shader_node, "Normal Map")
            nodeutils.unlink_node_output(links, shader_node, "Bump Map")
            mat_cache.parameters.default_normal_strength = 1.0
            nodeutils.set_node_input_value(shader_node, "Normal Strength", 1.0)

        elif bump_node:

            normal_image = bake_rl_bump_and_normal(shader_node, bsdf_node, mat, "Normal", bake_path,
                                                   normal_socket_name = "", bump_socket_name = "")
            normal_image_name = utils.unique_name("(NORMAL)")
            normal_image_node = nodeutils.make_image_node(nodes, normal_image, normal_image_name)
            nodeutils.link_nodes(links, normal_image_node, "Color", shader_node, "Normal Map")
            nodeutils.unlink_node_output(links, shader_node, "Bump Map")
            mat_cache.parameters.default_normal_strength = 1.0
            nodeutils.set_node_input_value(shader_node, "Normal Strength", 1.0)

        elif normal_node and normal_node.type != "TEX_IMAGE":

            normal_image = bake_rl_bump_and_normal(shader_node, bsdf_node, mat, "Normal", bake_path,
                                                   bump_socket_name = "", bump_distance_socket_name = "")
            normal_image_name = utils.unique_name("(NORMAL)")
            normal_image_node = nodeutils.make_image_node(nodes, normal_image, normal_image_name)
            nodeutils.link_nodes(links, normal_image_node, "Color", shader_node, "Normal Map")
            mat_cache.parameters.default_normal_strength = 1.0
            nodeutils.set_node_input_value(shader_node, "Normal Strength", 1.0)

    utils.try_select_objects(selection, True)
    if active:
        utils.set_active_object(active)


def bake_flow_to_normal(chr_cache, mat_cache):
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
               srgb = False, max_size = 0, reuse_existing = False):
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
                                  image_r = rgb_node.image, image_a = a_node.image,
                                  value_r = rgb_default, value_g = rgb_default,
                                  value_b = rgb_default, value_a = a_default,
                                  srgb = srgb, max_size = max_size, reuse_existing = reuse_existing)
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
                 srgb = False, max_size = 0, reuse_existing = False):
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
                              image_r = r_image, image_g = g_image,
                              image_b = b_image, image_a = a_image,
                              value_r = r_default, value_g = g_default,
                              value_b = b_default, value_a = a_default,
                              srgb = srgb, max_size = max_size, reuse_existing = reuse_existing)
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
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

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
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

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
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

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
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

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
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

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
        props = bpy.context.scene.CC3ImportProps

        if self.param == "BAKE_FLOW_NORMAL":
            mat = utils.context_material(context)
            chr_cache = props.get_context_character_cache(context)
            mat_cache = chr_cache.get_material_cache(mat)
            bake_flow_to_normal(chr_cache, mat_cache)

        if self.param == "BAKE_BUMP_NORMAL":
            mat = utils.context_material(context)
            chr_cache = props.get_context_character_cache(context)
            mat_cache = chr_cache.get_material_cache(mat)
            combine_normal(chr_cache, mat_cache)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "BAKE_FLOW_NORMAL":
            return "Generates a normal map from the flow map and connects it"
        if properties.param == "BAKE_BUMP_NORMAL":
            return "Combines the Bump and Normal maps into a single normal map"
        return ""