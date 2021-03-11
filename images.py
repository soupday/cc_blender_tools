import os

import bpy

from .cache import *
from .utils import *
from .vars import *


# load an image from a file, but try to find it in the existing images first
def load_image(filename, color_space):
    for i in bpy.data.images:
        if (i.type == "IMAGE" and i.filepath != ""):
            try:
                if os.path.normcase(i.filepath) == os.path.normcase(filename):
                    log_info("    Using existing image: " + i.filepath)
                    return i
            except:
                pass

    log_info("    Loading new image: " + filename)
    image = bpy.data.images.load(filename)
    image.colorspace_settings.name = color_space
    return image


## Search the directory for an image filename that contains the search substring
def find_image_file(dirs, mat, suffix_list):
    material_name = strip_name(mat.name).lower()
    last = ""
    for dir in dirs:
        if last != dir and dir != "" and os.path.normcase(dir) != os.path.normcase(last) and \
                os.path.exists(dir):
            last = dir
            files = os.listdir(dir)
            for file in files:
                file_name = file.lower()
                if material_name in file_name:
                    for suffix in suffix_list:
                        search = "_" + suffix + "."
                        if search in file_name:
                            return os.path.join(dir, file)
    return None


# Try to find the texture for a material input by searching for the material name
# appended with the possible suffixes e.g. Vest_diffuse or Hair_roughness
def find_material_image(mat, suffix_list):
    props = bpy.context.scene.CC3ImportProps
    color_space = "Non-Color"
    if "diffuse" in suffix_list or "sclera" in suffix_list:
        color_space = "sRGB"
    # try to find the image from the material cache
    cache = get_material_cache(mat)
    if cache is not None:
        if "diffuse" in suffix_list:
            return cache.diffuse
        elif "specular" in suffix_list:
            return cache.specular
        elif "opacity" in suffix_list:
            return cache.alpha
        elif "normal" in suffix_list:
            return cache.normal
        elif "bump" in suffix_list:
            return cache.bump
        elif "weightmap" in suffix_list and cache.temp_weight_map is not None:
            return cache.temp_weight_map
        image_file = find_image_file([cache.dir, props.import_main_tex_dir], mat, suffix_list)
        if image_file is not None:
            return load_image(image_file, color_space)
    else:
        image_file = find_image_file([props.import_main_tex_dir], mat, suffix_list)
        if image_file is not None:
            return load_image(image_file, color_space)
    return None
