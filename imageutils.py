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
import filecmp
import bpy

from . import params, utils


def check_max_size(image):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    width = image.size[0]
    height = image.size[1]

    if width > prefs.max_texture_size or height > prefs.max_texture_size:
        image.scale(min(width, prefs.max_texture_size), min(height, prefs.max_texture_size))


# load an image from a file, but try to find it in the existing images first
def load_image(filename, color_space, processed_images = None):

    i: bpy.types.Image = None
    # TODO: should the de-duplication only consider images brough in from the import.
    #       (but then the rebuild won't work...)
    #       or only consider images with the characters folder as a common path...
    for i in bpy.data.images:
        if i.type == "IMAGE" and i.filepath != "":

            if os.path.normcase(os.path.abspath(i.filepath)) == os.path.normcase(os.path.abspath(filename)):
                utils.log_info("Using existing image: " + i.filepath)
                found = False
                image_md5 = None
                image_path = bpy.path.abspath(i.filepath)
                if processed_images is not None and os.path.exists(image_path):
                    image_md5 = utils.md5sum(image_path)
                    for p in processed_images:
                        if p[0] == image_md5:
                            utils.log_info("Skipping duplicate existing image, reusing: " + p[1].filepath)
                            i = p[1]
                            found = True
                if i.depth == 32 and i.alpha_mode != "CHANNEL_PACKED":
                    i.alpha_mode = "CHANNEL_PACKED"
                if processed_images is not None and i and image_md5 and not found:
                    processed_images.append([image_md5, i])
                return i

    try:
        image_md5 = None
        if processed_images is not None and os.path.exists(filename):
            image_md5 = utils.md5sum(filename)
            for p in processed_images:
                if p[0] == image_md5:
                    utils.log_info("Skipping duplicate image, reusing: " + p[1].filepath)
                    return p[1]
        utils.log_info("Loading new image: " + filename)
        image = bpy.data.images.load(filename)
        image.colorspace_settings.name = color_space
        if image.depth == 32:
            image.alpha_mode = "CHANNEL_PACKED"
        #check_max_size(image)
        if processed_images is not None and image and image_md5:
            processed_images.append([image_md5, image])
        return image
    except Exception as e:
        utils.log_error("Unable to load image: " + filename, e)
        return None


## Search the directory for an image filename that contains the search substring
def find_image_file(base_dir, dirs, mat, texture_type):
    suffix_list = get_image_type_suffix_list(texture_type)
    material_name = utils.strip_name(mat.name).lower()
    last = ""

    for dir in dirs:

        if dir:

            # if the texture folder does not exist, (e.g. files have been moved)
            # remap the relative path to the current blend file directory to try and find the images there
            if not os.path.exists(dir):
                dir = utils.local_repath(dir, base_dir)

            if os.path.exists(dir):

                if last != dir and dir != "" and os.path.normcase(dir) != os.path.normcase(last):
                    last = dir
                    files = os.listdir(dir)
                    for file in files:
                        file_name = file.lower()
                        if file_name.startswith(material_name):
                            for suffix in suffix_list:
                                search = "_" + suffix + "."
                                if search in file_name:
                                    return os.path.join(dir, file)
    return None


def is_image_type_srgb(texture_type):
    if texture_type == "DIFFUSE" or texture_type == "SCLERA" or texture_type == "EMISSION":
        return True
    return False


def get_image_type_suffix_list(texture_type):
    for tex in params.TEXTURE_TYPES:
        if tex[0] == texture_type:
            return tex[2]
    return []


def get_image_type_json_id(texture_type):
    for tex in params.TEXTURE_TYPES:
        if tex[0] == texture_type:
            return tex[1]
    return None


def search_image_in_material_dirs(chr_cache, mat_cache, mat, texture_type):
    return find_image_file(chr_cache.import_dir, [mat_cache.get_tex_dir(chr_cache), chr_cache.get_tex_dir()], mat, texture_type)


def find_material_image(mat, texture_type, processed_images = None, tex_json = None):
    """Try to find the texture for a material input by searching for the material name
       appended with the possible suffixes e.g. Vest_diffuse or Hair_roughness
    """
    props = bpy.context.scene.CC3ImportProps
    mat_cache = props.get_material_cache(mat)
    chr_cache = props.get_character_cache(None, mat)

    image_file = None
    color_space = "Non-Color"
    if is_image_type_srgb(texture_type):
        color_space = "sRGB"

    # temp weight maps in the cache override weight maps on disk
    if texture_type == "WEIGHTMAP" and mat_cache.temp_weight_map is not None:
        return mat_cache.temp_weight_map

    # try to find the image in the json data first:
    if tex_json:

        rel_path = tex_json["Texture Path"]
        if rel_path:
            image_file = os.path.join(chr_cache.import_dir, rel_path)

            # try to load image path directly
            if os.path.exists(image_file):
                return load_image(image_file, color_space, processed_images)

            # try remapping the image path relative to the local directory
            image_file = utils.local_path(rel_path)
            if image_file and os.path.exists(image_file):
                return load_image(image_file, color_space, processed_images)

            # try to find the image in the texture_mappings (all embedded images should be here)
            for tex_mapping in mat_cache.texture_mappings:
                if tex_mapping:
                    if texture_type == tex_mapping.texture_type:
                        if tex_mapping.image:
                            return tex_mapping.image
        return None

    # with no Json data, try to locate the images in the texture folders:
    else:

        image_file = search_image_in_material_dirs(chr_cache, mat_cache, mat, texture_type)
        if image_file:
            return load_image(image_file, color_space, processed_images)

        # then try to find the image in the texture_mappings (all embedded images should be here)
        for tex_mapping in mat_cache.texture_mappings:
            if tex_mapping:
                if texture_type == tex_mapping.texture_type:
                    if tex_mapping.image:
                        return tex_mapping.image
                    elif tex_mapping.texture_path is not None and tex_mapping.texture_path != "":
                        return load_image(tex_mapping.texture_path, color_space, processed_images)
        return None


def get_material_tex_dir(chr_cache, obj, mat):
    """Returns the *relative* path to the texture folder for this material.
    """

    props = bpy.context.scene.CC3ImportProps

    if utils.is_file_ext(chr_cache.import_type, "FBX"):
        object_name = utils.strip_name(obj.name)
        mesh_name = utils.strip_name(obj.data.name)
        material_name = utils.strip_name(mat.name)
        # non .fbm textures are stored in two possible locations:
        #    /textures/character_name/object_name/mesh_name/material_name
        # or /textures/character_name/character_name/mesh_name/material_name
        rel_object = os.path.join("textures", chr_cache.import_name, object_name, mesh_name, material_name)
        path_object = os.path.join(chr_cache.import_dir, rel_object)
        rel_character = os.path.join("textures", chr_cache.import_name, chr_cache.import_name, mesh_name, material_name)
        path_character = os.path.join(chr_cache.import_dir, rel_character)
        if os.path.exists(path_object):
            return rel_object
        elif os.path.exists(path_character):
            return rel_character
        else:
            return os.path.join(chr_cache.import_name + ".fbm")

    elif utils.is_file_ext(chr_cache.import_type, "OBJ"):
        return chr_cache.import_name


def get_material_tex_dirs(chr_cache, obj, mat):
    mat_dir = os.path.normpath(os.path.join(chr_cache.import_dir, get_material_tex_dir(chr_cache, obj, mat)))
    return [chr_cache.get_tex_dir(), mat_dir]


def find_texture_folder_in_objects(objects):
    for obj in objects:
        if obj.type == "MESH":
            for mat in obj.data.materials:
                if mat.node_tree:
                    nodes = mat.node_tree.nodes
                    for node in nodes:
                        if node.type == "TEX_IMAGE":
                            image = node.image
                            if image.filepath:
                                file_path = bpy.path.abspath(image.filepath)
                                folder = os.path.dirname(file_path)
                                if folder:
                                    return folder
    return None


def get_custom_image(image_name, size, alpha = False, data = True, float = False, path = ""):
    # find the image by name
    image = None
    if image_name in bpy.data.images:
        image = bpy.data.images[image_name]
        if image.size[0] != size or image.size[1] != size:
            bpy.data.images.remove(image)
            image = None
            utils.log_info(f"Deleting Custom image: {image_name}, wrong size.")
        else:
            utils.log_info(f"Reusing Custom image: {image_name}")

    # or create the bake image
    if not image:
        utils.log_info(f"Creating new Custom image: {image_name} {size}x{size}")
        image = bpy.data.images.new(image_name, size, size, alpha=alpha, is_data=data, float_buffer=float)

    if float:
        image.use_half_precision = False

    if path:
        image.filepath_raw = path
        image.save()

    return image


def save_scene_image(image : bpy.types.Image, file_path, file_format = 'PNG', color_depth = '8'):
    """To reload properly, the image must be pre-saved with image.filepath_raw = ... and image.save()"""
    scene = bpy.data.scenes.new("RL_Save_Image_Settings_Scene")
    settings = scene.render.image_settings
    settings.color_depth = color_depth
    settings.file_format = file_format
    settings.color_mode = 'RGB' if image.depth == 24 else 'RGBA'
    if not file_path and image.filepath:
        file_path = bpy.path.abspath(image.filepath)
    image.save_render(filepath = file_path, scene = scene)
    if image.filepath:
        image.reload()
    bpy.data.scenes.remove(scene)