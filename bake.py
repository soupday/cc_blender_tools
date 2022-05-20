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


def init_bake(id = 1001):
    global BAKE_INDEX
    BAKE_INDEX = id


def prep_bake(mat):
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

    # blender 3.0
    if utils.is_blender_version("3.0.0"):
        bpy.context.scene.cycles.preview_samples = BAKE_SAMPLES
        bpy.context.scene.cycles.use_adaptive_sampling = False
        bpy.context.scene.cycles.use_preview_adaptive_sampling = False
        bpy.context.scene.cycles.use_denoising = False
        bpy.context.scene.cycles.use_preview_denoising = False
        bpy.context.scene.cycles.use_auto_tile = False

    if utils.is_blender_version("2.92.0"):
        bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'

    bpy.context.scene.render.use_bake_multires = False
    bpy.context.scene.render.bake.use_selected_to_active = False
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.margin = 16
    bpy.context.scene.render.bake.use_clear = True
    bpy.context.scene.render.image_settings.file_format = IMAGE_FORMAT
    # color management settings affect the baked output so set them to standard/raw defaults:
    bpy.context.scene.view_settings.view_transform = 'Standard'
    bpy.context.scene.view_settings.look = 'None'
    bpy.context.scene.view_settings.gamma = 1
    bpy.context.scene.view_settings.exposure = 0
    bpy.context.scene.sequencer_colorspace_settings.name = 'Raw'

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
    return [shading, engine, bake_surface]


def post_bake(bake_store):
    global old_samples, old_file_format
    global old_view_transform, old_look, old_gamma, old_exposure, old_colorspace

    bpy.context.scene.cycles.samples = old_samples
    bpy.context.scene.render.image_settings.file_format = old_file_format
    bpy.context.scene.view_settings.view_transform = old_view_transform
    bpy.context.scene.view_settings.look = old_look
    bpy.context.scene.view_settings.gamma = old_gamma
    bpy.context.scene.view_settings.exposure = old_exposure
    bpy.context.scene.sequencer_colorspace_settings.name = old_colorspace

    # remove the bake surface and restore the render settings
    bpy.data.objects.remove(bake_store.pop())
    bpy.context.scene.render.engine = bake_store.pop()
    bpy.context.space_data.shading.type = bake_store.pop()


def get_bake_image(mat, channel_id, width, height, shader_node, socket_name, bake_dir):
    global BAKE_INDEX

    # determine image name and color space
    image_name = "EXPORT_BAKE_" + mat.name + "_" + channel_id + "_" + str(BAKE_INDEX)
    BAKE_INDEX += 1
    is_data = True
    if "Diffuse Map" in socket_name or channel_id == "Base Color":
        is_data = False
    # make (and save) the target image
    image = get_image_target(image_name, width, height, bake_dir, is_data, True)
    # make sure we don't reuse an image as the target, that is also in the nodes we are baking from...
    i = 0
    base_name = image_name
    if shader_node and socket_name:
        while is_image_node_connected_to_socket(shader_node, socket_name, image):
            i += 1
            old_name = image_name
            image_name = base_name + "_" + str(i)
            utils.log_info(f"Image: {old_name} in use, trying: {image_name}")
            image = get_image_target(image_name, width, height, bake_dir, is_data, True)

    return image, image_name


def bake_node_socket_input(node, socket_name, mat, channel_id, bake_dir, override_size = 0):
    # determine the size of the image to bake onto
    width, height = get_texture_size(node, override_size, socket_name)

    # get the node and output socket to bake from
    source_node, source_socket = nodeutils.get_node_and_socket_connected_to_input(node, socket_name)

    # bake the source node output onto the target image and re-save it
    image, image_name = get_bake_image(mat, channel_id, width, height, node, socket_name, bake_dir)
    image_node = bake_output(mat, source_node, source_socket, image, image_name)

    # remove the image node
    nodes = mat.node_tree.nodes
    nodes.remove(image_node)

    return image


def bake_rl_bump_and_normal(shader_node, bsdf_node, normal_socket_name, bump_socket_name,
                            normal_strength_socket_name, bump_strength_socket_name,
                            mat, channel_id, bake_dir, override_size = 0):
    # determine the size of the image to bake onto
    width, height = get_texture_size(shader_node, override_size, normal_socket_name, bump_socket_name)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # store original links to BSDF normal socket
    bsdf_normal_node, bsdf_normal_socket = nodeutils.get_node_and_socket_connected_to_input(bsdf_node, "Normal")
    #
    normal_source_node = normal_source_socket = None
    bump_source_node = bump_source_socket = None
    bump_strength = 0.05
    normal_strength = 1.0
    bump_map_node = normal_map_node = None
    if bump_strength_socket_name:
        bump_strength = nodeutils.get_node_input(shader_node, bump_strength_socket_name, 0.05)
    if normal_strength_socket_name:
        normal_strength = nodeutils.get_node_input(shader_node, normal_strength_socket_name, 1.0)
    if normal_socket_name:
        normal_source_node, normal_source_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, normal_socket_name)
        normal_map_node = nodeutils.make_normal_map_node(nodes, normal_strength)
        nodeutils.link_nodes(links, normal_source_node, normal_source_socket, normal_map_node, "Color")
        nodeutils.link_nodes(links, normal_map_node, "Normal", bsdf_node, "Normal")
    if bump_socket_name:
        bump_source_node, bump_source_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, bump_socket_name)
        # the bump map bakes to a normal map quite a bit weaker than it looks on the bump node, so increase it's strength here
        bump_map_node = nodeutils.make_bump_node(nodes, 1, bump_strength * 3.0)
        nodeutils.link_nodes(links, bump_source_node, bump_source_socket, bump_map_node, "Height")
        if normal_map_node:
            nodeutils.link_nodes(links, normal_map_node, "Normal", bump_map_node, "Normal")
        nodeutils.link_nodes(links, bump_map_node, "Normal", bsdf_node, "Normal")

    # bake the source node output onto the target image and re-save it
    image, image_name = get_bake_image(mat, channel_id, width, height, shader_node, normal_socket_name, bake_dir)
    image_node = bake_normal_output(mat, bsdf_node, image, image_name)

    # remove the bake nodes and restore the normal links to the bsdf
    if bump_map_node:
        nodes.remove(bump_map_node)
    if normal_map_node:
        nodes.remove(normal_map_node)
    if image_node:
        nodes.remove(image_node)
    nodeutils.link_nodes(links, bsdf_normal_node, bsdf_normal_socket, bsdf_node, "Normal")

    return image


def bake_node_socket_output(node, socket_name, mat, channel_id, bake_dir, override_size = 0):
    # determine the size of the image to bake onto
    width, height = get_texture_size(node, override_size, socket_name)

    # bake the source node output onto the target image and re-save it
    image, image_name = get_bake_image(mat, channel_id, width, height, node, socket_name, bake_dir)
    image_node = bake_output(mat, node, socket_name, image, image_name)

    # remove the image node
    nodes = mat.node_tree.nodes
    nodes.remove(image_node)

    return image


def bake_bsdf_normal(bsdf_node, mat, channel_id, bake_dir, override_size = 0):
    # determine the size of the image to bake onto
    width, height = get_texture_size(bsdf_node, override_size, "Normal")

    # get the node and output socket to bake from
    nodes = mat.node_tree.nodes

    # bake the source node output onto the target image and re-save it
    image, image_name = get_bake_image(mat, channel_id, width, height, bsdf_node, "Normal", bake_dir)
    image_node = bake_normal_output(mat, bsdf_node, image, image_name)

    if image_node:
        nodes.remove(image_node)

    return image


def bake_value_image(value, mat, channel_id, bake_dir, size = 64):
    width = height = size
    image, image_name = get_bake_image(mat, channel_id, width, height, None, "", bake_dir)

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


def bake_output(mat, source_node, source_socket, image, image_name):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")
    output_source, output_source_socket = nodeutils.get_node_and_socket_connected_to_input(output_node, "Surface")

    image_node = nodeutils.make_image_node(nodes, image, "bake")
    image_node.name = image_name

    bpy.context.scene.cycles.samples = BAKE_SAMPLES
    utils.log_info("Baking: " + image_name)

    bake = prep_bake(mat)

    nodeutils.link_nodes(links, source_node, source_socket, output_node, "Surface")
    image_node.select = True
    nodes.active = image_node
    bpy.ops.object.bake(type='COMBINED')

    image.save_render(filepath = bpy.path.abspath(image.filepath), scene = bpy.context.scene)
    image.reload()

    if output_source:
        nodeutils.link_nodes(links, output_source, output_source_socket, output_node, "Surface")

    post_bake(bake)

    return image_node


def bake_normal_output(mat, bsdf_node, image, image_name):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")

    image_node = nodeutils.make_image_node(nodes, image, "bake")
    image_node.name = image_name

    bpy.context.scene.cycles.samples = BAKE_SAMPLES
    utils.log_info("Baking normal: " + image_name)

    bake = prep_bake(mat)

    nodeutils.link_nodes(links, bsdf_node, "BSDF", output_node, "Surface")
    image_node.select = True
    nodes.active = image_node

    bpy.ops.object.bake(type='NORMAL')

    image.save_render(filepath = bpy.path.abspath(image.filepath), scene = bpy.context.scene)
    image.reload()

    post_bake(bake)

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


def get_texture_size(node, override_size, *sockets):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    width = 0
    height = 0
    for socket_name in sockets:
        w, h = get_largest_texture_to_socket(node, socket_name)
        if w > width:
            width = w
        if h > height:
            height = h
    if width == 0:
        width = int(prefs.export_texture_size)
    if height == 0:
        height = int(prefs.export_texture_size)
    if override_size > 0:
        width = override_size
        height = override_size
    return width, height


def is_image_node_connected_to_node(node, image, done):
    socket : bpy.types.NodeSocket
    for socket in node.inputs:
        if socket.is_linked:
            found = is_image_node_connected_to_socket(node, socket.name, image, done)
            if found:
                return True
    return False


def is_image_node_connected_to_socket(node, socket, image, done = None):
    if done is None:
        done = []

    connected_node = nodeutils.get_node_connected_to_input(node, socket)
    if connected_node is None or connected_node in done:
        return False

    done.append(connected_node)

    if connected_node.type == "TEX_IMAGE" and connected_node.image == image:
        return True
    else:
        return is_image_node_connected_to_node(node, image, done)


def get_tex_image_size(node):
    if node is not None:
        return node.image.size[0], node.image.size[1]
    return 0, 0


def get_image_target(image_name, width, height, dir, data = True, alpha = False, force_new = False):
    format = IMAGE_FORMAT
    ext = IMAGE_EXT
    depth = 32

    # find an old image with the same name to reuse:
    if not force_new:
        for img in bpy.data.images:
            if img and img.name == image_name:

                img_path, img_file = os.path.split(bpy.path.abspath(img.filepath))
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


def get_bake_dir(chr_cache):
    bake_path = os.path.join(chr_cache.import_dir, "textures", chr_cache.import_name, "Blender_Baked")
    return bake_path


def combine_normal(chr_cache, mat_cache):

    init_bake(5001)

    mat = mat_cache.material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    mat_name = utils.strip_name(mat.name)
    shader = params.get_shader_lookup(mat_cache)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader)
    bake_path = get_bake_dir(chr_cache)

    selection = bpy.context.selected_objects.copy()
    active = bpy.context.active_object

    if mat_cache.material_type == "DEFAULT" or mat_cache.material_type == "SSS":

        nodeutils.clear_cursor()

        normal_node, normal_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, "Normal Map")
        bump_node, bump_socket = nodeutils.get_node_and_socket_connected_to_input(shader_node, "Bump Map")

        if normal_node and bump_node:

            normal_image = bake_rl_bump_and_normal(shader_node, bsdf_node, "Normal Map", "Bump Map", "Normal Strength", "Bump Strength", mat, "Normal", bake_path)
            normal_image_name = utils.unique_name("(NORMAL)")
            normal_image_node = nodeutils.make_image_node(nodes, normal_image, normal_image_name)
            nodeutils.link_nodes(links, normal_image_node, "Color", shader_node, "Normal Map")
            nodeutils.unlink_node(links, shader_node, "Bump Map")
            mat_cache.parameters.default_normal_strength = 1.0
            nodeutils.set_node_input(shader_node, "Normal Strength", 1.0)

        elif bump_node:

            normal_image = bake_rl_bump_and_normal(shader_node, bsdf_node, "", "Bump Map", "", "Bump Strength", mat, "Normal", bake_path)
            normal_image_name = utils.unique_name("(NORMAL)")
            normal_image_node = nodeutils.make_image_node(nodes, normal_image, normal_image_name)
            nodeutils.link_nodes(links, normal_image_node, "Color", shader_node, "Normal Map")
            nodeutils.unlink_node(links, shader_node, "Bump Map")
            mat_cache.parameters.default_normal_strength = 1.0
            nodeutils.set_node_input(shader_node, "Normal Strength", 1.0)

        elif normal_node and normal_node.type != "TEX_IMAGE":

            normal_image = bake_rl_bump_and_normal(shader_node, bsdf_node, "Normal Map", "", "Normal Strength", "", mat, "Normal", bake_path)
            normal_image_name = utils.unique_name("(NORMAL)")
            normal_image_node = nodeutils.make_image_node(nodes, normal_image, normal_image_name)
            nodeutils.link_nodes(links, normal_image_node, "Color", shader_node, "Normal Map")
            mat_cache.parameters.default_normal_strength = 1.0
            nodeutils.set_node_input(shader_node, "Normal Strength", 1.0)

    utils.try_select_objects(selection, True)
    if active:
        utils.set_active_object(active)


def bake_flow_to_normal(mat_cache):

    init_bake(4001)

    mat = mat_cache.material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    mat_name = utils.strip_name(mat.name)
    shader = params.get_shader_lookup(mat_cache)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader)

    if mat_cache.material_type == "HAIR":

        nodeutils.clear_cursor()

        selection = bpy.context.selected_objects.copy()
        active = bpy.context.active_object

        # get the flow map
        flow_node = nodeutils.get_node_connected_to_input(shader_node, "Flow Map")
        flow_image: bpy.types.Image = flow_node.image

        width = flow_image.size[0]
        height = flow_image.size[1]

        normal_node = None
        normal_image = None

        # try to reuse normal map
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

        utils.try_select_objects(selection, True)
        if active:
            utils.set_active_object(active)


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