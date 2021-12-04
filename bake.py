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

import bpy
import os
from mathutils import Vector
from . import nodeutils, utils, params

old_samples = 64
old_file_format = "PNG"
old_view_transform = "Standard"
old_look = "None"
old_gamma = 1
old_exposure = 0
old_colorspace = "Raw"
BAKE_SAMPLES = 4
IMAGE_FORMAT = "PNG"
IMAGE_EXT = ".png"
BAKE_INDEX = 1001


def init_bake():
    global BAKE_INDEX
    BAKE_INDEX = 1001


def prep_bake():
    global old_samples, old_file_format
    global old_view_transform, old_look, old_gamma, old_exposure, old_colorspace

    old_samples = bpy.context.scene.cycles.samples
    old_file_format = bpy.context.scene.render.image_settings.file_format
    old_view_transform = bpy.context.scene.view_settings.view_transform
    old_look = bpy.context.scene.view_settings.look
    old_gamma = bpy.context.scene.view_settings.gamma
    old_exposure = bpy.context.scene.view_settings.exposure
    old_colorspace = bpy.context.scene.sequencer_colorspace_settings.name

    bpy.context.scene.cycles.samples = BAKE_SAMPLES
    bpy.context.scene.render.use_bake_multires = False
    bpy.context.scene.render.bake.use_selected_to_active = False
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    if utils.is_blender_version("2.92.0"):
        bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'
    bpy.context.scene.render.bake.margin = 16
    bpy.context.scene.render.bake.use_clear = True
    bpy.context.scene.render.image_settings.file_format = IMAGE_FORMAT
    # color management settings affect the baked output so set them to standard/raw defaults:
    bpy.context.scene.view_settings.view_transform = 'Standard'
    bpy.context.scene.view_settings.look = 'None'
    bpy.context.scene.view_settings.gamma = 1
    bpy.context.scene.view_settings.exposure = 0
    bpy.context.scene.sequencer_colorspace_settings.name = 'Raw'


def post_bake():
    global old_samples, old_file_format
    global old_view_transform, old_look, old_gamma, old_exposure, old_colorspace

    bpy.context.scene.cycles.samples = old_samples
    bpy.context.scene.render.image_settings.file_format = old_file_format
    bpy.context.scene.view_settings.view_transform = old_view_transform
    bpy.context.scene.view_settings.look = old_look
    bpy.context.scene.view_settings.gamma = old_gamma
    bpy.context.scene.view_settings.exposure = old_exposure
    bpy.context.scene.sequencer_colorspace_settings.name = old_colorspace


def bake_socket_input(node, socket_name, mat, channel_id, bake_dir):
    global BAKE_INDEX

    # determine the size of the image to bake onto
    width, height = get_largest_texture_to_socket(node, socket_name)
    if width == 0:
        width = 1024
    if height == 0:
        height = 1024

    # determine image name and color space
    image_name = "EXPORT_BAKE_" + mat.name + "_" + channel_id + "_" + str(BAKE_INDEX)
    BAKE_INDEX += 1
    is_data = True
    if "Diffuse Map" in socket_name:
        is_data = False

    # deselect everything
    bpy.ops.object.select_all(action='DESELECT')
    # create the baking plane, a single quad baking surface for an even sampling across the entire texture
    bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bake_surface = bpy.context.active_object

    # go into wireframe mode (so Blender doesn't update or recompile the material shaders while
    # we manipulate them for baking, and also so Blender doesn't fire up the cycles viewport...):
    shading = bpy.context.space_data.shading.type
    bpy.context.space_data.shading.type = 'WIREFRAME'
    # set cycles rendering mode for baking
    engine = bpy.context.scene.render.engine
    bpy.context.scene.render.engine = 'CYCLES'

    # attach the material to bake to the baking surface plane
    # (the baking plane also ensures that only one material is baked onto only one target image)
    if len(bake_surface.data.materials) == 0:
        bake_surface.data.materials.append(mat)
    else:
        bake_surface.data.materials[0] = mat

    # get the node and output socket to bake from
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    source_node, source_socket = nodeutils.get_node_and_socket_connected_to_input(node, socket_name)

    # make (and save) the target image
    image = get_image_target(image_name, width, height, bake_dir, is_data, True)

    # bake the source node output onto the target image and re-save it
    image_node = bake_output(mat, source_node, source_socket, image, image_name)

    # reconnect the custom nodes to the shader socket
    nodes.remove(image_node)
    nodeutils.link_nodes(mat.node_tree.links, source_node, source_socket, node, socket_name)

    # remove the bake surface and restore the render settings
    bpy.data.objects.remove(bake_surface)
    bpy.context.scene.render.engine = engine
    bpy.context.space_data.shading.type = shading

    return image


def bake_bump_and_normal(shader_node, bsdf_node, normal_socket_name, bump_socket_name, bump_strength_socket_name, mat, channel_id, bake_dir):
    global BAKE_INDEX

    # determine the size of the image to bake onto
    width, height = get_largest_texture_to_socket(shader_node, normal_socket_name)
    w2, h2 = get_largest_texture_to_socket(shader_node, bump_socket_name)
    if w2 > width:
        width = w2
    if h2 > height:
        height = h2
    if width == 0:
        width = 1024
    if height == 0:
        height = 1024

    # determine image name and color space
    image_name = "EXPORT_BAKE_" + mat.name + "_" + channel_id + "_" + str(BAKE_INDEX)
    BAKE_INDEX += 1
    is_data = True

    # deselect everything
    bpy.ops.object.select_all(action='DESELECT')
    # create the baking plane, a single quad baking surface for an even sampling across the entire texture
    bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    bake_surface = bpy.context.active_object

    # go into wireframe mode (so Blender doesn't update or recompile the material shaders while
    # we manipulate them for baking, and also so Blender doesn't fire up the cycles viewport...):
    shading = bpy.context.space_data.shading.type
    bpy.context.space_data.shading.type = 'WIREFRAME'
    # set cycles rendering mode for baking
    engine = bpy.context.scene.render.engine
    bpy.context.scene.render.engine = 'CYCLES'

    # attach the material to bake to the baking surface plane
    # (the baking plane also ensures that only one material is baked onto only one target image)
    if len(bake_surface.data.materials) == 0:
        bake_surface.data.materials.append(mat)
    else:
        bake_surface.data.materials[0] = mat

    # get the node and output socket to bake from
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    normal_source_node, normal_source_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, normal_socket_name)
    bump_source_node, bump_source_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, bump_socket_name)
    bsdf_normal_node, bsdf_normal_socket = nodeutils.get_node_and_socket_connected_to_input(bsdf_node, "Normal")
    bump_strength = nodeutils.get_node_input(shader_node, bump_strength_socket_name, 0.05)
    bump_map_node = nodeutils.make_bump_node(nodes, 1, bump_strength)
    normal_map_node = nodeutils.make_normal_map_node(nodes, 1)
    nodeutils.link_nodes(links, normal_source_node, normal_source_socket, normal_map_node, "Color")
    nodeutils.link_nodes(links, normal_map_node, "Normal", bump_map_node, "Normal")
    nodeutils.link_nodes(links, bump_source_node, bump_source_socket, bump_map_node, "Height")
    nodeutils.link_nodes(links, bump_map_node, "Normal", bsdf_node, "Normal")

    # make (and save) the target image
    image = get_image_target(image_name, width, height, bake_dir, is_data, True)

    # bake the source node output onto the target image and re-save it
    image_node = bake_bsdf_normal(mat, bsdf_node, image, image_name)

    # remove the bake nodes and restore the normal links to the bsdf
    nodes.remove(bump_map_node)
    nodes.remove(normal_map_node)
    nodes.remove(image_node)
    nodeutils.link_nodes(links, bsdf_normal_node, bsdf_normal_socket, bsdf_node, "Normal")

    # remove the bake surface and restore the render settings
    bpy.data.objects.remove(bake_surface)
    bpy.context.scene.render.engine = engine
    bpy.context.space_data.shading.type = shading

    return image


def bake_output(mat, source_node, source_socket, image, image_name):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")
    output_source, output_source_socket = nodeutils.get_node_and_socket_connected_to_input(output_node, "Surface")

    image_node = nodeutils.make_image_node(nodes, image, "bake")
    image_node.name = image_name

    bpy.context.scene.cycles.samples = BAKE_SAMPLES
    utils.log_info("Baking: " + image_name)

    prep_bake()

    nodeutils.link_nodes(links, source_node, source_socket, output_node, "Surface")
    image_node.select = True
    nodes.active = image_node
    bpy.ops.object.bake(type='COMBINED')

    image.save_render(filepath = image.filepath, scene = bpy.context.scene)
    image.reload()

    post_bake()

    if output_source:
        nodeutils.link_nodes(links, output_source, output_source_socket, output_node, "Surface")

    return image_node


def bake_bsdf_normal(mat, bsdf_node, image, image_name):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")

    image_node = nodeutils.make_image_node(nodes, image, "bake")
    image_node.name = image_name

    bpy.context.scene.cycles.samples = BAKE_SAMPLES
    utils.log_info("Baking normal: " + image_name)

    prep_bake()

    nodeutils.link_nodes(links, bsdf_node, "BSDF", output_node, "Surface")
    image_node.select = True
    nodes.active = image_node

    bpy.ops.object.bake(type='NORMAL')

    image.save_render(filepath = image.filepath, scene = bpy.context.scene)
    image.reload()

    post_bake()

    return image_node


def get_largest_texture_to_node(node, done):
    largest_width = 0
    largest_height = 0
    socket : bpy.types.NodeSocket
    for socket in node.inputs:
        if socket.is_linked:
            width, height = get_largest_texture_to_socket(node, socket.name, done)
            if width > largest_width:
                largest_width = width
            if height > largest_height:
                largest_height = height
    return largest_width, largest_height


def get_largest_texture_to_socket(node, socket, done = None):
    if done is None:
        done = []

    connected_node = nodeutils.get_node_connected_to_input(node, socket)
    if connected_node is None or connected_node in done:
        return 0, 0

    done.append(connected_node)

    if connected_node.type == "TEX_IMAGE":
        return get_tex_image_size(connected_node)
    else:
        return get_largest_texture_to_node(connected_node, done)


def get_tex_image_size(node):
    if node is not None:
        return node.image.size[0], node.image.size[1]
    return 0, 0


def get_image_target(image_name, width, height, dir, data = True, alpha = False):
    format = IMAGE_FORMAT
    ext = IMAGE_EXT
    depth = 32

    # find an old image with the same name to reuse:
    for img in bpy.data.images:
        if img and img.name == image_name:

            img_path, img_file = os.path.split(img.filepath)
            same_path = False
            try:
                if os.path.samefile(dir, img_path):
                    same_path = True
            except:
                same_path = False

            if img.file_format == format and img.depth == depth and same_path:
                utils.log_info("Reusing image: " + image_name)
                try:
                    if img.size[0] != width or img.size[1] != height:
                        img.scale(width, height)
                    return img
                except:
                    utils.log_info("Bad image: " + img.name)
                    bpy.data.images.remove(img)
            else:
                utils.log_info("Wrong path or format: " + img.name + ", " + img_path + "==" + dir + "?, " + img.file_format + "==" + format + "?, depth: " + str(depth) + "==" + str(img.depth) + "?")
                bpy.data.images.remove(img)

    # or just make a new one:
    utils.log_info("Creating new image: " + image_name + " size: " + str(width))
    img = make_new_image(image_name, width, height, format, ext, dir, data, alpha)
    return img


def make_new_image(name, width, height, format, ext, dir, data, has_alpha):
    img = bpy.data.images.new(name, width, height, alpha=has_alpha, is_data=data)
    img.pixels[0] = 0
    img.file_format = format
    dir = os.path.join(utils.local_path(), dir)
    os.makedirs(dir, exist_ok=True)
    img.filepath_raw = os.path.join(dir, name + ext)
    img.save()
    return img


def bake_flow_to_normal(mat_cache):

    mat = mat_cache.material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    mat_name = utils.strip_name(mat.name)
    shader = params.get_shader_lookup(mat_cache)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader)

    if mat_cache.material_type == "HAIR":

        # get the flow map
        flow_node = nodeutils.get_node_connected_to_input(shader_node, "Flow Map")
        flow_image: bpy.types.Image = flow_node.image

        width = flow_image.size[0]
        height = flow_image.size[1]

        normal_node = None
        normal_image = None

        # try to reuse normal map
        if nodeutils.has_connected_input(shader, "Normal Map"):
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
            normal_image = make_new_image(mat_name + "_Normal", width, height, "PNG", ".png", mat_cache.dir, True, False)
        if not normal_node:
            utils.log_info("Creating new normal image node.")
            normal_node = nodeutils.make_image_node(nodes, normal_image, "Generated Normal Map")
            nodeutils.link_nodes(links, normal_node, "Color", shader_node, "Normal Map")

        # convert the flow map to a normal map
        tangent = mat_cache.parameters.hair_tangent_vector
        flip_y = mat_cache.parameters.hair_tangent_flip_green > 0
        utils.log_info("Converting Flow Map to Normal Map...")
        convert_flow_to_normal(flow_image, normal_image, tangent, flip_y)


def convert_flow_to_normal(flow_image: bpy.types.Image, normal_image: bpy.types.Image, tangent, flip_y):

    # fetching a copy of the normal pixels as a list gives us the fastest write speed:
    normal_pixels = list(normal_image.pixels)
    # fetching the flow pixels as a tuple with slice notation gives the fastest read speed:
    flow_pixels = flow_image.pixels[:]

    tangent_vector = Vector(tangent)

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

        # calculate normal vector
        normal_vector = tangent_vector.cross(flow_vector).normalized()

        # normal_vector -> rgb
        normal_pixels[i + 0] = (normal_vector[0] + 1) / 2
        normal_pixels[i + 1] = (normal_vector[1] + 1) / 2
        normal_pixels[i + 2] = (normal_vector[2] + 1) / 2
        normal_pixels[i + 3] = 1

    # replace-in-place all the pixels from the list:
    normal_image.pixels[:] = normal_pixels
    normal_image.update()
    normal_image.save()


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
            bake_flow_to_normal(mat_cache)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "BAKE_FLOW_NORMAL":
            return "Generates a normal map from the flow map and connects it."
        return ""