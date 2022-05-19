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

from . import params, utils


def check_max_size(image):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    width = image.size[0]
    height = image.size[1]

    if width > prefs.max_texture_size or height > prefs.max_texture_size:
        image.scale(min(width, prefs.max_texture_size), min(height, prefs.max_texture_size))


# load an image from a file, but try to find it in the existing images first
def load_image(filename, color_space):

    i: bpy.types.Image = None
    for i in bpy.data.images:
        if (i.type == "IMAGE" and i.filepath != ""):
            try:
                if os.path.normcase(os.path.abspath(i.filepath)) == os.path.normcase(os.path.abspath(filename)):
                    utils.log_info("Using existing image: " + i.filepath)
                    if i.depth == 32 and i.alpha_mode != "CHANNEL_PACKED":
                        i.alpha_mode = "CHANNEL_PACKED"
                    #check_max_size(i)
                    return i
            except:
                pass

    try:
        utils.log_info("Loading new image: " + filename)
        image = bpy.data.images.load(filename)
        image.colorspace_settings.name = color_space
        if image.depth == 32:
            image.alpha_mode = "CHANNEL_PACKED"
        #check_max_size(image)
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
    if texture_type == "DIFFUSE" or texture_type == "SCLERA":
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


def search_image_in_material_dirs(chr_cache, cache, mat, texture_type):
    return find_image_file(chr_cache.import_dir, [cache.dir, chr_cache.import_main_tex_dir], mat, texture_type)


def find_material_image(mat, texture_type, tex_json = None):
    """Try to find the texture for a material input by searching for the material name
       appended with the possible suffixes e.g. Vest_diffuse or Hair_roughness
    """
    props = bpy.context.scene.CC3ImportProps
    cache = props.get_material_cache(mat)
    chr_cache = props.get_character_cache(None, mat)

    image_file = None
    color_space = "Non-Color"
    if is_image_type_srgb(texture_type):
        color_space = "sRGB"

    # temp weight maps in the cache override weight maps on disk
    if texture_type == "WEIGHTMAP" and cache.temp_weight_map is not None:
        return cache.temp_weight_map

    # try to find the image in the json data first:
    if tex_json:

        rel_path = tex_json["Texture Path"]
        if rel_path:
            image_file = os.path.join(chr_cache.import_dir, rel_path)

            # try to load image path directly
            if os.path.exists(image_file):
                return load_image(image_file, color_space)

            # try remapping the image path relative to the local directory
            image_file = utils.local_path(rel_path)
            if os.path.exists(image_file):
                return load_image(image_file, color_space)

            # try to find the image in the texture_mappings (all embedded images should be here)
            for tex_mapping in cache.texture_mappings:
                if tex_mapping:
                    if texture_type == tex_mapping.texture_type:
                        if tex_mapping.image:
                            return tex_mapping.image
        return None

    # with no Json data, try to locate the images in the texture folders:
    else:

        image_file = search_image_in_material_dirs(chr_cache, cache, mat, texture_type)
        if image_file:
            return load_image(image_file, color_space)

        # then try to find the image in the texture_mappings (all embedded images should be here)
        for tex_mapping in cache.texture_mappings:
            if tex_mapping:
                if texture_type == tex_mapping.texture_type:
                    if tex_mapping.image:
                        return tex_mapping.image
                    elif tex_mapping.texture_path is not None and tex_mapping.texture_path != "":
                        return load_image(tex_mapping.texture_path, color_space)
        return None


def get_material_tex_dir(character_cache, obj, mat):
    props = bpy.context.scene.CC3ImportProps

    if character_cache.import_type == "fbx":
        object_name = utils.strip_name(obj.name)
        mesh_name = utils.strip_name(obj.data.name)
        material_name = utils.strip_name(mat.name)
        # non .fbm textures are stored in two possible locations:
        #    /textures/character_name/object_name/mesh_name/material_name
        # or /textures/character_name/character_name/mesh_name/material_name
        path_object = os.path.join(character_cache.import_dir, "textures", character_cache.import_name, object_name, mesh_name, material_name)
        path_character = os.path.join(character_cache.import_dir, "textures", character_cache.import_name, character_cache.import_name, mesh_name, material_name)
        if os.path.exists(path_object):
            return path_object
        elif os.path.exists(path_character):
            return path_character
        else:
            return os.path.join(character_cache.import_dir, character_cache.import_name + ".fbm")

    elif character_cache.import_type == "obj":
        return os.path.join(character_cache.import_dir, character_cache.import_name)


def get_material_tex_dirs(character_cache, obj, mat):
    mat_dir = get_material_tex_dir(character_cache, obj, mat)
    return [character_cache.import_main_tex_dir, mat_dir]
