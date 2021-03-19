# Version: 0.2.2
#   DONE
#   - When no texture maps are present for an advanced node group, does not generate the node group.
#   - When exporting morph characters with .fbxkey or .objkey files, the key file is copied along with the export.
#   - Function added to reset preferences to default values.
#   - Alpha blend settings and back face culling settings can be applied to materials in the object now.
#   - Option to apply alpha blend settings to whole object(s) or just active materal.
#   - Remembers the applied alpha blend settings and re-applies when rebuilding materials.
#   - Option to pick Scalp Material.
#   - Only scans once on import for hair object and scalp material, so it can be cleared if it gets it wrong and wont keep putting it back.
#   - FBX import keeps track of the objects as well as the armature in case the armature is replaced.
#
#   Physics:
#   - Uses the physX weight maps to auto-generate vertex pin weights for cloth/hair physics (Optional)
#   - Automatically sets up cloth/hair physics modifiers (Optional)
#   - Physics cloth presets can be applied to the selected object(s) and are remembered with rebuilding materials.
#   - Weightmaps can be added/removed to the individual materials of the objects.
#   - Weight map painting added.
#   - Saving of modified weight maps and Deleting weight map functions added.
#
# TODO
#   - FINISH THE TOOLTIPS!
#   (these can wait for now)
#   - Prefs for physics settings.
#   - Button to auto transfer skin weights to accessories.
#   - limits on node group inputs in _LIB.
#   - OBJ import to be rigged later... do we need to keep track of any new armature?
#
# FUTURE PLANS
#   - Get all search strings to identify material type: skin, eyelashes, body, hair etc... from preferences the user can customise.
#       (Might help with Daz conversions and/or 3rd party characters that have non-standard or unexpected material names.)
#   - Automatically generate full IK rig with Rigify or Auto-Rig Pro (Optional in the preferences)
#       (Not sure if this is possible to invoke these add-ons from code...)
#
# --------------------------------------------------------------

import bpy
import os
import mathutils
import shutil
import math

bl_info = {
    "name": "CC3 Tools",
    "author": "Victor Soupday",
    "version": (0, 2, 2),
    "blender": (2, 80, 0),
    "category": "Characters",
    "location": "3D View > Properties> CC3",
    "description": "Automatic import and material setup of CC3 characters.",
}

VERSION_STRING = "v" + str(bl_info["version"][0]) \
               + "." + str(bl_info["version"][1]) \
               + "." + str(bl_info["version"][2])

# lists of the suffixes used by the input maps
BASE_COLOR_MAP = ["diffuse", "albedo"]
SUBSURFACE_MAP = ["sssmap", "sss"]
METALLIC_MAP = ["metallic"]
SPECULAR_MAP = ["specular"]
ROUGHNESS_MAP = ["roughness"]
EMISSION_MAP = ["glow", "emission"]
ALPHA_MAP = ["opacity", "alpha"]
NORMAL_MAP = ["normal"]
BUMP_MAP = ["bump", "height"]
SCLERA_MAP = ["sclera"]
SCLERA_NORMAL_MAP = ["scleran", "scleranormal"]
IRIS_NORMAL_MAP = ["irisn", "irisnormal"]
MOUTH_GRADIENT_MAP = ["gradao", "gradientao"]
TEETH_GUMS_MAP = ["gumsmask"]
WEIGHT_MAP = ["weightmap"]

# lists of the suffixes used by the modifier maps
# (not connected directly to input but modify base inputs)
MOD_AO_MAP = ["ao", "ambientocclusion", "ambient occlusion"]
MOD_BASECOLORBLEND_MAP = ["bcbmap", "basecolorblend2"]
MOD_MCMAO_MAP = ["mnaomask", "mouthcavitymaskandao"]
MOD_SPECMASK_MAP = ["specmask", "hspecmap", "specularmask", "hairspecularmaskmap"]
MOD_TRANSMISSION_MAP = ["transmap", "transmissionmap"]
MOD_NORMALBLEND_MAP = ["nbmap", "normalmapblend"]
MOD_MICRONORMAL_MAP = ["micron", "micronormal"]
MOD_MICRONORMALMASK_MAP = ["micronmask", "micronormalmask"]

# blender uses metres, CC3 uses centimetres
UNIT_SCALE = 0.01

# https://docs.blender.org/manual/en/latest/files/media/image_formats.html
IMAGE_TYPES = [".bmp", ".sgi", ".rgb", ".bw", ".png", ".jpg", ".jpeg", ".jp2", ".j2c",
               ".tga", ".cin", ".dpx", ".exr", ".hdr", ".tif", ".tiff"]

# base names of all node groups in the library blend file
NODE_GROUPS = ["color_ao_mixer", "color_blend_ao_mixer", "color_eye_mixer", "color_teeth_mixer", "color_tongue_mixer", "color_head_mixer",
               "subsurface_mixer", "subsurface_overlay_mixer",
               "msr_mixer", "msr_overlay_mixer",
               "normal_micro_mask_blend_mixer", "normal_micro_mask_mixer", "bump_mixer",
               "eye_occlusion_mask", "iris_mask", "tiling_pivot_mapping", "tiling_mapping"]

NODE_PREFIX = "cc3iid_"

GRID_SIZE = 300



cursor = mathutils.Vector((0,0))
cursor_top = mathutils.Vector((0,0))
max_cursor = mathutils.Vector((0,0))
new_nodes = []
debug_counter = 0


def log_info(msg):
    prefs = bpy.context.preferences.addons[__name__].preferences
    """Log an info message to console."""
    if prefs.log_level == "ALL":
        print(msg)


def log_warn(msg):
    prefs = bpy.context.preferences.addons[__name__].preferences
    """Log a warning message to console."""
    if prefs.log_level == "ALL" or prefs.log_level == "WARN":
        print("Warning: " + msg)


def log_error(msg):
    """Log an error message to console and raise an exception."""
    print("Error: " + msg)


def message_box(message = "", title = "Info", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text = message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def unique_name(name):
    """Generate a unique name for the node or property to quickly
       identify texture nodes or nodes with parameters."""
    props = bpy.context.scene.CC3ImportProps
    name = NODE_PREFIX + name + "_" + VERSION_STRING + "_" + str(props.node_id)
    props.node_id = props.node_id + 1
    return name


def is_skin_material(mat):
    if "std_skin_" in mat.name.lower():
        return True
    return False


def is_scalp_material(mat):
    props = bpy.context.scene.CC3ImportProps
    if props.scalp_material is not None and mat == props.scalp_material:
        return True
    hints = props.hair_scalp_hint.split(",")
    for hint in hints:
        h = hint.strip()
        if h != "":
            if h in mat.name.lower():
                return True
    return False


def is_eyelash_material(mat):
    if "std_eyelash" in mat.name.lower():
        return True
    return False


def is_mouth_material(mat):
    name = mat.name.lower()
    if "std_upper_teeth" in name:
        return True
    elif "std_lower_teeth" in name:
        return True
    elif "std_tongue" in name:
        return True
    return False


def is_teeth_material(mat):
    name = mat.name.lower()
    if "std_upper_teeth" in name:
        return True
    elif "std_lower_teeth" in name:
        return True
    return False


def is_tongue_material(mat):
    name = mat.name.lower()
    if "std_tongue" in name:
        return True
    return False


def is_nails_material(mat):
    name = mat.name.lower()
    if "std_nails" in name:
        return True
    return False


def is_hair_object(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if props.hair_object is not None and obj == props.hair_object:
        return True
    hints = props.hair_hint.split(",")
    object_name = obj.name.lower()
    material_name = mat.name.lower()
    for hint in hints:
        h = hint.strip()
        if h != "":
            if h in object_name:
                return True
            elif h in material_name:
                return True
    return False

def is_eye_material(mat):
    if "std_cornea_" in mat.name.lower():
        return True
    return False

def is_tearline_material(mat):
    if "std_tearline_" in mat.name.lower():
        return True
    return False

def is_eye_occlusion_material(mat):
    if "std_eye_occlusion_" in mat.name.lower():
        return True
    return False

def get_material_group(obj, mat):
    name = mat.name.lower()
    if "std_skin_head" in name:
        return "skin_head"
    elif "std_skin_body" in name:
        return "skin_body"
    elif "std_skin_arm" in name:
        return "skin_arm"
    elif "std_skin_leg" in name:
        return "skin_leg"
    elif "std_upper_teeth" in name:
        return "teeth_upper"
    elif "std_lower_teeth" in name:
        return "teeth_lower"
    elif "std_nails" in name:
        return "nails"
    elif "std_tongue" in name:
        return "tongue"
    elif is_hair_object(obj, mat):
        if is_scalp_material(mat):
            return "scalp"
        return "hair"
    elif is_eye_material(mat):
        return "eye"
    else:
        return "default"

def get_shader_input(mat, input):
    if mat.node_tree is not None:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                if input in n.inputs:
                    return n.inputs[input]
    return None

def get_input_connected_to(node, socket):
    try:
        return node.outputs[socket].links[0].to_socket.name
    except:
        return None

def get_node_by_id(mat, id):
    if mat.node_tree is not None:
        nodes = mat.node_tree.nodes
        for node in nodes:
            if id in node.name:
                return node
    return None


def get_default_shader_input(mat, input):
    if mat.node_tree is not None:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                if input in n.inputs:
                    return n.inputs[input].default_value
    return 0.0

def get_bump_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_hair_object(obj, mat):
        return "hair_bump", props.hair_bump
    return "default_bump", props.default_bump

def get_micronormal_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    name = mat.name.lower()
    if "std_skin_head" in name:
        return "skin_head_micronormal", props.skin_head_micronormal
    elif "std_skin_body" in name:
        return "skin_body_micronormal", props.skin_body_micronormal
    elif "std_skin_arm" in name:
        return "skin_arm_micronormal", props.skin_arm_micronormal
    elif "std_skin_leg" in name:
        return "skin_leg_micronormal", props.skin_leg_micronormal
    elif "std_upper_teeth" in name:
        return "teeth_upper_micronormal", props.teeth_micronormal
    elif "std_lower_teeth" in name:
        return "teeth_lower_micronormal", props.teeth_micronormal
    elif "std_nails" in name:
        return "nails_micronormal", props.nails_micronormal
    elif "std_tongue" in name:
        return "tongue_micronormal", props.tongue_micronormal
    elif is_eye_material(mat):
        return "eye_sclera_normal", 1 - props.eye_sclera_normal
    return "default_micronormal", props.default_micronormal

def get_micronormal_tiling(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    name = mat.name.lower()
    if "std_skin_head" in name:
        return "skin_head_tiling", props.skin_head_tiling
    elif "std_skin_body" in name:
        return "skin_body_tiling", props.skin_body_tiling
    elif "std_skin_arm" in name:
        return "skin_arm_tiling", props.skin_arm_tiling
    elif "std_skin_leg" in name:
        return "skin_leg_tiling", props.skin_leg_tiling
    elif "std_upper_teeth" in name:
        return "teeth_upper_tiling", props.teeth_tiling
    elif "std_lower_teeth" in name:
        return "teeth_lower_tiling", props.teeth_tiling
    elif "std_tongue" in name:
        return "tongue_tiling", props.tongue_tiling
    elif "std_nails" in name:
        return "nails_tiling", props.nails_tiling
    elif is_eye_material(mat):
        return "eye_sclera_tiling", props.eye_sclera_tiling
    return "default_tiling", props.default_tiling

def get_specular_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_eye_material(mat):
        return "eye_specular", props.eye_specular
    elif is_skin_material(mat):
        if props.setup_mode == "ADVANCED":
            return "skin_specular", props.skin_specular
        else:
            return "skin_basic_specular", props.skin_basic_specular
    elif is_hair_object(obj, mat):
        if is_scalp_material(mat):
            return "hair_scalp_specular", props.hair_scalp_specular
        return "hair_specular", props.hair_specular
    elif is_nails_material(mat):
        return "nails_specular", props.nails_specular
    elif is_teeth_material(mat):
        return "teeth_specular", props.teeth_specular
    elif is_tongue_material(mat):
        return "tongue_specular", props.tongue_specular
    return "default_specular", get_default_shader_input(mat, "Specular")

def get_roughness_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_skin_material(mat):
        if props.setup_mode == "ADVANCED":
            return "skin_roughness", props.skin_roughness
        else:
            return "skin_basic_roughness", props.skin_basic_roughness
    elif is_hair_object(obj, mat):
        if is_scalp_material(mat):
            return "hair_scalp_roughness", props.hair_scalp_roughness
        return "hair_roughness", props.hair_roughness
    elif is_nails_material(mat):
        return "nails_roughness", props.nails_roughness
    elif is_teeth_material(mat):
        return "teeth_roughness", props.teeth_roughness
    elif is_tongue_material(mat):
        return "tongue_roughness", props.tongue_roughness
    return "default_roughness", props.default_roughness

def get_ao_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_eye_material(mat):
        return "eye_ao", props.eye_ao
    elif is_skin_material(mat):
        return "skin_ao", props.skin_ao
    elif is_hair_object(obj, mat):
        return "hair_ao", props.hair_ao
    elif is_nails_material(mat):
        return "nails_ao", props.nails_ao
    elif is_teeth_material(mat):
        return "teeth_ao", props.teeth_ao
    elif is_tongue_material(mat):
        return "tongue_ao", props.tongue_ao
    return "default_ao", props.default_ao

def get_blend_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_eye_material(mat):
        return "eye_blend", props.eye_blend
    elif is_skin_material(mat):
        return "skin_blend", props.skin_blend
    elif is_hair_object(obj, mat):
        return "hair_blend", props.hair_blend
    return "default_blend", props.default_blend

def get_normal_blend_strength(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_skin_material(mat):
        return "skin_normal_blend", props.skin_normal_blend
    return "default_normal_blend", props.default_normal_blend

def get_sss_radius(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_eye_material(mat):
        return "eye_sss_radius", props.eye_sss_radius
    elif is_skin_material(mat):
        return "skin_sss_radius", props.skin_sss_radius
    elif is_hair_object(obj, mat):
        return "hair_sss_radius", props.hair_sss_radius
    elif is_nails_material(mat):
        return "nails_sss_radius", props.nails_sss_radius
    elif is_teeth_material(mat):
        return "teeth_sss_radius", props.teeth_sss_radius
    elif is_tongue_material(mat):
        return "tongue_sss_radius", props.tongue_sss_radius
    return "default_sss_radius", props.default_sss_radius

def get_sss_falloff(obj, mat):
    props = bpy.context.scene.CC3ImportProps
    if is_eye_material(mat):
        return "eye_sss_falloff", props.eye_sss_falloff
    elif is_skin_material(mat):
        return "skin_sss_falloff", props.skin_sss_falloff
    elif is_hair_object(obj, mat):
        return "hair_sss_falloff", props.hair_sss_falloff
    elif is_nails_material(mat):
        return "nails_sss_falloff", props.nails_sss_falloff
    elif is_teeth_material(mat):
        return "teeth_sss_falloff", props.teeth_sss_falloff
    elif is_tongue_material(mat):
        return "tongue_sss_falloff", props.tongue_sss_falloff
    return "default_sss_falloff", props.default_sss_falloff

def is_input_connected(input):
    if len(input.links) > 0:
        return True
    return False

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

def clear_cursor():
    cursor_top.x = 0
    cursor_top.y = 0
    cursor.x = 0
    cursor.y = 0
    max_cursor.x = 0
    max_cursor.y = 0
    new_nodes.clear()

def reset_cursor():
    cursor_top.y = max_cursor.y
    cursor_top.x = 0
    cursor.x = 0
    cursor.y = cursor_top.y

def advance_cursor(scale = 1.0):
    cursor.y = cursor_top.y - cursor_top.x
    cursor.x += GRID_SIZE * scale
    if (cursor.x > max_cursor.x):
        max_cursor.x = cursor.x

def drop_cursor(scale = 1.0):
    cursor.y -= GRID_SIZE * scale
    if cursor.y < max_cursor.y:
        max_cursor.y = cursor.y

def step_cursor(scale = 1.0, drop = 0.25):
    cursor_top.x += GRID_SIZE * drop
    cursor.y = cursor_top.y - cursor_top.x
    cursor.x += GRID_SIZE * scale
    if (cursor.x > max_cursor.x):
        max_cursor.x = cursor.x

def step_cursor_if(thing, scale = 1.0, drop = 0.25):
    if thing is not None:
        step_cursor(scale, drop)

def move_new_nodes(dx, dy):

    width = max_cursor.x
    height = -max_cursor.y - GRID_SIZE

    for node in new_nodes:
        node.location.x += (dx) - width
        node.location.y += (dy) + (height / 2)

    clear_cursor()

def make_shader_node(nodes, type, scale = 1.0):
    shader_node = nodes.new(type)
    shader_node.location = cursor
    new_nodes.append(shader_node)
    drop_cursor(scale)
    return shader_node

## color_space: Non-Color, sRGB
def make_image_node(nodes, image, prop, scale = 1.0):
    if image is None:
        return None
    image_node = make_shader_node(nodes, "ShaderNodeTexImage", scale)
    image_node.image = image
    image_node.name = unique_name(prop)
    return image_node


def make_value_node(nodes, label, prop, value = 0.0):
    value_node = make_shader_node(nodes, "ShaderNodeValue", 0.4)
    value_node.label = label
    value_node.name = unique_name(prop)
    value_node.outputs["Value"].default_value = value
    return value_node

def make_mixrgb_node(nodes, blend_type):
    mix_node = make_shader_node(nodes, "ShaderNodeMixRGB", 0.8)
    mix_node.blend_type = blend_type
    return mix_node

def make_math_node(nodes, operation, value1 = 0.5, value2 = 0.5):
    math_node = make_shader_node(nodes, "ShaderNodeMath", 0.6)
    math_node.operation = operation
    math_node.inputs[0].default_value = value1
    math_node.inputs[1].default_value = value2
    return math_node

def make_rgb_node(nodes, label, value = [1.0, 1.0, 1.0, 1.0]):
    rgb_node = make_shader_node(nodes, "ShaderNodeRGB", 0.8)
    rgb_node.label = label
    rgb_node.outputs["Color"].default_value = value
    return rgb_node

def make_vectormath_node(nodes, operation):
    vm_node = make_shader_node(nodes, "ShaderNodeVectorMath", 0.6)
    vm_node.operation = operation
    return vm_node

def make_node_group_node(nodes, group, label, name):
    group_node = make_shader_node(nodes, "ShaderNodeGroup")
    group_node.node_tree = group
    group_node.label = label
    group_node.width = 240
    group_node.name = unique_name("(" + name + ")")
    return group_node

# remove any .001 from the material name
def strip_name(name):
    if name[-3:].isdigit() and name[-4] == ".":
        name = name[:-4]
    return name

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
                if file_name.startswith(material_name):
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


def apply_backface_culling(obj, mat, sides):
    cache = get_material_cache(mat)
    if cache is not None:
        cache.culling_sides = sides
    if sides == 1:
        mat.use_backface_culling = True
    else:
        mat.use_backface_culling = False

def apply_alpha_override(obj, mat, method):
    cache = get_material_cache(mat)
    if cache is not None:
        cache.alpha_mode = method
    input = get_shader_input(mat, "Alpha")
    if input is None:
        return
    if is_input_connected(input):
        set_material_alpha(mat, method)
    elif input.default_value < 1.0:
        set_material_alpha(mat, method)
    else:
        set_material_alpha(mat, "OPAQUE")

def set_material_alpha(mat, method):
    if method == "HASHED":
        mat.blend_method = "HASHED"
        mat.shadow_method = "HASHED"
        mat.use_backface_culling = False
    elif method == "BLEND":
        mat.blend_method = "BLEND"
        mat.shadow_method = "CLIP"
        mat.use_backface_culling = True
        mat.show_transparent_back = True
        mat.alpha_threshold = 0.5
    else:
        mat.blend_method = "OPAQUE"
        mat.shadow_method = "OPAQUE"
        mat.use_backface_culling = False


def get_node_input(node, input, default):
    if node is not None:
        try:
            return node.inputs[input].default_value
        except:
            return default
    return default

def get_node_output(node, output, default):
    if node is not None:
        try:
            return node.outputs[output].default_value
        except:
            return default
    return default

def set_node_input(node, socket, value):
    if node is not None:
        try:
            node.inputs[socket].default_value = value
        except:
            log_info("Unable to set input: " + node.name + "[" + str(socket) + "]")

def set_node_output(node, socket, value):
    if node is not None:
        try:
            node.outputs[socket].default_value = value
        except:
            log_info("Unable to set output: " + node.name + "[" + str(socket) + "]")

def link_nodes(links, from_node, from_socket, to_node, to_socket):
    if from_node is not None and to_node is not None:
        try:
            links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])
        except:
            log_info("Unable to link: " + from_node.name + "[" + str(from_socket) + "] to " +
                  to_node.name + "[" + str(to_socket) + "]")

def count_maps(*maps):
    count = 0
    for map in maps:
        if map is not None:
            count += 1
    return count

def connect_tearline_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    set_node_input(shader, "Base Color", (1.0, 1.0, 1.0, 1.0))
    set_node_input(shader, "Metallic", 1.0)
    set_node_input(shader, "Specular", 1.0)
    set_node_input(shader, "Roughness", props.eye_tearline_roughness)
    set_node_input(shader, "Alpha", props.eye_tearline_alpha)
    shader.name = unique_name("eye_tearline_shader")
    set_material_alpha(mat, props.blend_mode)
    mat.shadow_method = "NONE"


def connect_eye_occlusion_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    set_node_input(shader, "Base Color", (0.0, 0.0, 0.0, 1.0))
    set_node_input(shader, "Metallic", 0.0)
    set_node_input(shader, "Specular", 0.0)
    set_node_input(shader, "Roughness", 1.0)

    reset_cursor()

    # groups
    group = get_node_group("eye_occlusion_mask")
    occ_node = make_node_group_node(nodes, group, "Eye Occulsion Alpha", "eye_occlusion_mask")
    # values
    set_node_input(occ_node, "Strength", props.eye_occlusion)
    # links
    link_nodes(links, occ_node, "Alpha", shader, "Alpha")

    set_material_alpha(mat, props.blend_mode)
    mat.shadow_method = "NONE"


def connect_basic_eye_material(obj, mat, shader):

    props = bpy.context.scene.CC3ImportProps

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Base Color
    #
    reset_cursor()
    diffuse_image =  find_material_image(mat, BASE_COLOR_MAP)
    if diffuse_image is not None:
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        advance_cursor(1.0)
        hsv_node = make_shader_node(nodes, "ShaderNodeHueSaturation", 0.6)
        hsv_node.label = "HSV"
        hsv_node.name = unique_name("eye_basic_hsv")
        set_node_input(hsv_node, "Value", props.eye_basic_brightness)
        # links
        link_nodes(links, diffuse_node, "Color", hsv_node, "Color")
        link_nodes(links, hsv_node, "Color", shader, "Base Color")

    # Metallic
    #
    reset_cursor()
    metallic_node = make_value_node(nodes, "Eye Metallic", "eye_metallic", 0.0)
    link_nodes(links, metallic_node, "Value", shader, "Metallic")

    # Specular
    #
    reset_cursor()
    specular_node = make_value_node(nodes, "Eye Specular", "eye_specular", props.eye_specular)
    link_nodes(links, specular_node, "Value", shader, "Specular")

    # Roughness
    #
    reset_cursor()
    roughness_node = make_value_node(nodes, "Eye Roughness", "eye_basic_roughness", props.eye_basic_roughness)
    link_nodes(links, roughness_node, "Value", shader, "Roughness")

    # Alpha
    #
    set_node_input(shader, "Alpha", 1.0)

    # Normal
    #
    reset_cursor()
    normal_image = find_material_image(mat, SCLERA_NORMAL_MAP)
    if normal_image is not None:
        strength_node = make_value_node(nodes, "Normal Strength", "eye_basic_normal", props.eye_basic_normal)
        normal_node = make_image_node(nodes, normal_image, "normal_tex")
        advance_cursor()
        normalmap_node = make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        link_nodes(links, strength_node, "Value", normalmap_node, "Strength")
        link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        link_nodes(links, normalmap_node, "Normal", shader, "Normal")

    # Clearcoat
    #
    set_node_input(shader, "Clearcoat", 1.0)
    set_node_input(shader, "Clearcoat Roughness", 0.15)

    return


def connect_adv_eye_material(obj, mat, shader):

    props = bpy.context.scene.CC3ImportProps

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Iris Mask
    reset_cursor()
    # groups
    group = get_node_group("iris_mask")
    iris_mask_node = make_node_group_node(nodes, group, "Iris Mask", "iris_mask")
    # values
    set_node_input(iris_mask_node, "Scale", 1.0 / props.eye_iris_scale)
    set_node_input(iris_mask_node, "Radius", props.eye_iris_radius)
    set_node_input(iris_mask_node, "Hardness", props.eye_iris_hardness * props.eye_iris_radius * 0.99)
    # move
    move_new_nodes(-3000, 0)
    clear_cursor()

    # Base Color
    reset_cursor()
    # maps
    diffuse_image = find_material_image(mat, BASE_COLOR_MAP)
    sclera_image = find_material_image(mat, SCLERA_MAP)
    blend_image = find_material_image(mat, MOD_BASECOLORBLEND_MAP)
    ao_image = find_material_image(mat, MOD_AO_MAP)
    diffuse_node = sclera_node = blend_node = ao_node = iris_tiling_node = sclera_tiling_node = None
    advance_cursor(-count_maps(diffuse_image, sclera_image, blend_image, ao_image))
    if diffuse_image is not None:
        advance_cursor(-1)
        drop_cursor(0.75)
        group = get_node_group("tiling_pivot_mapping")
        iris_tiling_node = make_node_group_node(nodes, group, "Iris Scaling", "tiling_color_iris_mapping")
        set_node_input(iris_tiling_node, "Pivot", (0.5, 0.5, 0))
        advance_cursor()
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        step_cursor()
    if sclera_image is not None:
        advance_cursor(-1)
        drop_cursor(0.75)
        group = get_node_group("tiling_pivot_mapping")
        sclera_tiling_node = make_node_group_node(nodes, group, "Sclera Scaling", "tiling_color_sclera_mapping")
        set_node_input(sclera_tiling_node, "Pivot", (0.5, 0.5, 0))
        set_node_input(sclera_tiling_node, "Tiling", 1.0 / props.eye_sclera_scale)
        advance_cursor()
        sclera_node = make_image_node(nodes, sclera_image, "sclera_tex")
        sclera_node.extension = "EXTEND"
        step_cursor()
    if ao_image is not None:
        ao_node = make_image_node(nodes, ao_image, "ao_tex")
        step_cursor()
    if blend_image is not None:
        blend_node = make_image_node(nodes, blend_image, "blend_tex")
        step_cursor()
    # groups
    group = get_node_group("color_eye_mixer")
    color_node = make_node_group_node(nodes, group, "Eye Base Color", "color_eye_mixer")
    # values
    set_node_input(color_node, "Shadow Hardness", props.eye_shadow_hardness * props.eye_shadow_radius * 0.99)
    set_node_input(color_node, "Shadow Radius", props.eye_shadow_radius)
    set_node_input(color_node, "Blend Strength", props.eye_blend)
    set_node_input(color_node, "AO Strength", props.eye_ao)
    set_node_input(color_node, "Iris Brightness", props.eye_iris_brightness)
    set_node_input(color_node, "Sclera Brightness", props.eye_sclera_brightness)
    # links
    link_nodes(links, iris_mask_node, "Mask", color_node, "Iris Mask")
    if diffuse_image is not None:
        link_nodes(links, iris_mask_node, "Scale", iris_tiling_node, "Tiling")
        link_nodes(links, iris_tiling_node, "Vector", diffuse_node, "Vector")
        link_nodes(links, diffuse_node, "Color", color_node, "Cornea Diffuse")
    if sclera_image is not None:
        link_nodes(links, sclera_tiling_node, "Vector", sclera_node, "Vector")
        link_nodes(links, sclera_node, "Color", color_node, "Sclera Diffuse")
    else:
        link_nodes(links, diffuse_node, "Color", color_node, "Sclera Diffuse")
    if blend_image is not None:
        link_nodes(links, blend_node, "Color", color_node, "Blend")
    if ao_image is not None:
        link_nodes(links, ao_node, "Color", color_node, "AO")
    link_nodes(links, color_node, "Base Color", shader, "Base Color")

    # SSS
    drop_cursor(0.65)
    reset_cursor()
    # groups
    group = get_node_group("subsurface_overlay_mixer")
    sss_node = make_node_group_node(nodes, group, "Eye Subsurface", "subsurface_eye_mixer")
    # values
    set_node_input(sss_node, "Scatter1", 1.0)
    set_node_input(sss_node, "Scatter2", 0.0)
    set_node_input(sss_node, "Radius1", props.eye_sss_radius * UNIT_SCALE)
    set_node_input(sss_node, "Radius2", props.eye_sss_radius * UNIT_SCALE)
    set_node_input(sss_node, "Falloff1", props.eye_sss_falloff)
    set_node_input(sss_node, "Falloff2", props.eye_sss_falloff)
    # links
    link_nodes(links, iris_mask_node, "Mask", sss_node, "Mask")
    link_nodes(links, color_node, "Base Color", sss_node, "Diffuse")
    link_nodes(links, sss_node, "Subsurface", shader, "Subsurface")
    link_nodes(links, sss_node, "Subsurface Radius", shader, "Subsurface Radius")
    link_nodes(links, sss_node, "Subsurface Color", shader, "Subsurface Color")

    # MSR
    drop_cursor(0.1)
    reset_cursor()
    # groups
    group = get_node_group("msr_overlay_mixer")
    msr_node = make_node_group_node(nodes, group, "Eye MSR", "msr_eye_mixer")
    # values
    set_node_input(msr_node, "Metallic1", 0)
    set_node_input(msr_node, "Metallic2", 0)
    set_node_input(msr_node, "Specular1", props.eye_specular)
    set_node_input(msr_node, "Specular2", props.eye_specular)
    set_node_input(msr_node, "Roughness1", props.eye_sclera_roughness)
    set_node_input(msr_node, "Roughness2", props.eye_iris_roughness)
    # links
    link_nodes(links, iris_mask_node, "Mask", msr_node, "Mask")
    link_nodes(links, msr_node, "Metallic", shader, "Metallic")
    link_nodes(links, msr_node, "Specular", shader, "Specular")
    link_nodes(links, msr_node, "Roughness", shader, "Roughness")

    # emission and alpha
    set_node_input(shader, "Alpha", 1.0)
    connect_emission_alpha(obj, mat, shader)

    # Normal
    drop_cursor(0.1)
    reset_cursor()
    snormal_image = find_material_image(mat, SCLERA_NORMAL_MAP)
    snormal_node = snormal_tiling_node = None
    # space
    advance_cursor(-count_maps(snormal_image))
    # maps
    if snormal_image is not None:
        advance_cursor(-1)
        drop_cursor(0.75)
        group = get_node_group("tiling_mapping")
        snormal_tiling_node = make_node_group_node(nodes, group, "Sclera Normal Tiling", "tiling_normal_sclera_mapping")
        set_node_input(snormal_tiling_node, "Tiling", props.eye_sclera_tiling)
        advance_cursor()
        snormal_node = make_image_node(nodes, snormal_image, "sclera_normal_tex")
        step_cursor()
    # groups
    group = get_node_group("normal_micro_mask_mixer")
    nm_group = make_node_group_node(nodes, group, "Eye Normals", "normal_eye_mixer")
    # values
    set_node_input(nm_group, "Micro Normal Strength", 1 - props.eye_sclera_normal)
    # links
    link_nodes(links, iris_mask_node, "Inverted Mask", nm_group, "Micro Normal Mask")
    if snormal_image is not None:
        link_nodes(links, snormal_node, "Color", nm_group, "Micro Normal")
        link_nodes(links, snormal_tiling_node, "Vector", snormal_node, "Vector")
    link_nodes(links, nm_group, "Normal", shader, "Normal")

    # Clearcoat
    #
    set_node_input(shader, "Clearcoat", 1.0)
    set_node_input(shader, "Clearcoat Roughness", 0.15)

    return


def connect_adv_mouth_material(obj, mat, shader):

    props = bpy.context.scene.CC3ImportProps

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Gums Mask and Gradient AO
    reset_cursor()
    advance_cursor(-2)
    # maps
    mask_image = None
    mask_node = None
    teeth = is_teeth_material(mat)
    if teeth:
        mask_image = find_material_image(mat, TEETH_GUMS_MAP)
        # if no gums mask file is found for the teeth,
        # just connect as default advanced material
        if mask_image is None:
            connect_advanced_material(obj, mat, shader)
            return
    # if no gradient ao file is found for the teeth or tongue
    # just connect as default advanced material
    gradient_image = find_material_image(mat, MOUTH_GRADIENT_MAP)
    gradient_node = None
    if gradient_image is None:
        connect_advanced_material(obj, mat, shader)
        return
    advance_cursor(2 - count_maps(mask_image, gradient_image))
    if mask_image is not None:
        mask_node = make_image_node(nodes, mask_image, "gums_mask_tex")
        step_cursor()
    if gradient_image is not None:
        gradient_node = make_image_node(nodes, gradient_image, "gradient_ao_tex")
        step_cursor()
        # nodes
        gradientrgb_node = make_shader_node(nodes, "ShaderNodeSeparateRGB")
        # links
        link_nodes(links, gradient_node, "Color", gradientrgb_node, "Image")
    # move
    move_new_nodes(-2000, 0)
    clear_cursor()

    # Base Color
    reset_cursor()
    advance_cursor(-2)
    # maps
    diffuse_image = find_material_image(mat, BASE_COLOR_MAP)
    ao_image = find_material_image(mat, MOD_AO_MAP)
    diffuse_node = ao_node = None
    advance_cursor(2 - count_maps(diffuse_image, ao_image))
    if diffuse_image is not None:
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        step_cursor()
    if ao_image is not None:
        ao_node = make_image_node(nodes, ao_image, "ao_tex")
        step_cursor()
    # groups
    if teeth:
        group = get_node_group("color_teeth_mixer")
        color_node = make_node_group_node(nodes, group, "Teeth Base Color", "color_teeth_mixer")
    else:
        group = get_node_group("color_tongue_mixer")
        color_node = make_node_group_node(nodes, group, "Tongue Base Color", "color_tongue_mixer")
    # values
    if teeth:
        set_node_input(color_node, "AO Strength", props.teeth_ao)
        set_node_input(color_node, "Front", props.teeth_front)
        set_node_input(color_node, "Rear", props.teeth_rear)
        set_node_input(color_node, "Gums Brightness", props.teeth_gums_brightness)
        set_node_input(color_node, "Teeth Brightness", props.teeth_teeth_brightness)
        set_node_input(color_node, "Gums Saturation", 1 - props.teeth_gums_desaturation)
        set_node_input(color_node, "Teeth Saturation", 1 - props.teeth_teeth_desaturation)
    else:
        set_node_input(color_node, "AO Strength", props.tongue_ao)
        set_node_input(color_node, "Front", props.tongue_front)
        set_node_input(color_node, "Rear", props.tongue_rear)
        set_node_input(color_node, "Brightness", props.tongue_brightness)
        set_node_input(color_node, "Saturation", 1 - props.tongue_desaturation)
    # links
    if teeth:
        gao_socket = "G"
        if "std_lower_teeth" in mat.name.lower():
            gao_socket = "R"
        link_nodes(links, mask_node, "Color", color_node, "Gums Mask")
        link_nodes(links, gradientrgb_node, gao_socket, color_node, "Gradient AO")
        link_nodes(links, diffuse_node, "Color", color_node, "Diffuse")
        link_nodes(links, ao_node, "Color", color_node, "AO")
        link_nodes(links, color_node, "Base Color", shader, "Base Color")
    else:
        gao_socket = "B"
        link_nodes(links, gradientrgb_node, gao_socket, color_node, "Gradient AO")
        link_nodes(links, diffuse_node, "Color", color_node, "Diffuse")
        link_nodes(links, ao_node, "Color", color_node, "AO")
        link_nodes(links, color_node, "Base Color", shader, "Base Color")

    # SSS
    drop_cursor(0.35)
    reset_cursor()
    # groups
    if teeth:
        group = get_node_group("subsurface_overlay_mixer")
        sss_node = make_node_group_node(nodes, group, "Teeth Subsurface", "subsurface_teeth_mixer")
    else:
        group = get_node_group("subsurface_mixer")
        sss_node = make_node_group_node(nodes, group, "Tongue Subsurface", "subsurface_tongue_mixer")
    # values
    if teeth:
        set_node_input(sss_node, "Scatter1", props.teeth_gums_sss_scatter)
        set_node_input(sss_node, "Radius1", props.teeth_sss_radius * UNIT_SCALE * 3)
        set_node_input(sss_node, "Falloff1", props.teeth_sss_falloff)
        set_node_input(sss_node, "Scatter2", props.teeth_teeth_sss_scatter)
        set_node_input(sss_node, "Radius2", props.teeth_sss_radius * UNIT_SCALE * 3)
        set_node_input(sss_node, "Falloff2", props.teeth_sss_falloff)
    else:
        set_node_input(sss_node, "Scatter", props.tongue_sss_scatter)
        set_node_input(sss_node, "Radius", props.tongue_sss_radius * UNIT_SCALE * 3)
        set_node_input(sss_node, "Falloff", props.tongue_sss_falloff)
    # links
    link_nodes(links, mask_node, "Color", sss_node, "Mask")
    link_nodes(links, color_node, "Base Color", sss_node, "Diffuse")
    link_nodes(links, sss_node, "Subsurface", shader, "Subsurface")
    link_nodes(links, sss_node, "Subsurface Radius", shader, "Subsurface Radius")
    link_nodes(links, sss_node, "Subsurface Color", shader, "Subsurface Color")

    # MSR
    drop_cursor(0.1)
    reset_cursor()
    advance_cursor(-2.7)
    # props
    metallic = 0
    specprop, specular = get_specular_strength(obj, mat)
    roughprop, roughness = get_roughness_strength(obj, mat)
    # maps
    metallic_image = find_material_image(mat, METALLIC_MAP)
    roughness_image = find_material_image(mat, ROUGHNESS_MAP)
    metallic_node = roughness_node = roughness_mult_node = None
    if metallic_image is not None:
        metallic_node = make_image_node(nodes, metallic_image, "metallic_tex")
        step_cursor()
    else:
        advance_cursor()
    if roughness_image is not None:
        roughness_node = make_image_node(nodes, roughness_image, "roughness_tex")
        advance_cursor()
        roughness_mult_node = make_math_node(nodes, "MULTIPLY", 1, roughness)
        if teeth:
            roughness_mult_node.name = unique_name("teeth_roughness")
        else:
            roughness_mult_node.name = unique_name("tongue_roughness")
        step_cursor(0.7)
    else:
        advance_cursor(1.7)
    # groups
    group = get_node_group("msr_overlay_mixer")
    if teeth:
        msr_node = make_node_group_node(nodes, group, "Teeth MSR", "msr_teeth_mixer")
    else:
        msr_node = make_node_group_node(nodes, group, "Tongue MSR", "msr_tongue_mixer")
    # values
    set_node_input(msr_node, "Metallic1", metallic)
    set_node_input(msr_node, "Metallic2", metallic)
    set_node_input(msr_node, "Roughness1", 1)
    set_node_input(msr_node, "Roughness2", roughness)
    set_node_input(msr_node, "Specular1", 0)
    set_node_input(msr_node, "Specular2", specular)
    # links
    link_nodes(links, gradientrgb_node, gao_socket, msr_node, "Mask")
    link_nodes(links, metallic_node, "Color", msr_node, "Metallic1")
    link_nodes(links, metallic_node, "Color", msr_node, "Metallic2")
    link_nodes(links, roughness_node, "Color", roughness_mult_node, 0)
    link_nodes(links, roughness_mult_node, "Value", msr_node, "Roughness2")
    link_nodes(links, gradientrgb_node, gao_socket, msr_node, "Mask")
    link_nodes(links, msr_node, "Metallic", shader, "Metallic")
    link_nodes(links, msr_node, "Specular", shader, "Specular")
    link_nodes(links, msr_node, "Roughness", shader, "Roughness")

    # emission and alpha
    set_node_input(shader, "Alpha", 1.0)
    connect_emission_alpha(obj, mat, shader)

    # Normal
    connect_normal(obj, mat, shader)

    # Clearcoat
    #
    set_node_input(shader, "Clearcoat", 0)
    set_node_input(shader, "Clearcoat Roughness", 0)

    return


def connect_advanced_material(obj, mat, shader):
    base_colour_node = connect_base_color(obj, mat, shader)
    connect_subsurface(obj, mat, shader, base_colour_node)
    connect_msr(obj, mat, shader)
    connect_emission_alpha(obj, mat, shader)
    connect_normal(obj, mat, shader)
    return


def connect_basic_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Base Color
    #
    reset_cursor()
    diffuse_image = find_material_image(mat, BASE_COLOR_MAP)
    ao_image = find_material_image(mat, MOD_AO_MAP)
    diffuse_node = ao_node = None
    if (diffuse_image is not None):
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        if ao_image is not None:
            prop, ao_strength = get_ao_strength(obj, mat)
            fac_node = make_value_node(nodes, "Ambient Occlusion Strength", prop, ao_strength)
            ao_node = make_image_node(nodes, ao_image, "ao_tex")
            advance_cursor(1.5)
            drop_cursor(0.75)
            mix_node = make_mixrgb_node(nodes, "MULTIPLY")
            link_nodes(links, diffuse_node, "Color", mix_node, "Color1")
            link_nodes(links, ao_node, "Color", mix_node, "Color2")
            link_nodes(links, fac_node, "Value", mix_node, "Fac")
            link_nodes(links, mix_node, "Color", shader, "Base Color")
        else:
            link_nodes(links, diffuse_node, "Color", shader, "Base Color")

    # Metallic
    #
    reset_cursor()
    metallic_image = find_material_image(mat, METALLIC_MAP)
    metallic_node = None
    if metallic_image is not None:
        metallic_node = make_image_node(nodes, metallic_image, "metallic_tex")
        link_nodes(links, metallic_node, "Color", shader, "Metallic")

    # Specular
    #
    reset_cursor()
    specular_image = find_material_image(mat, SPECULAR_MAP)
    mask_image = find_material_image(mat, MOD_SPECMASK_MAP)
    prop_spec, spec = get_specular_strength(obj, mat)
    specular_node = mask_node = mult_node = None
    if specular_image is not None:
        specular_node = make_image_node(nodes, specular_image, "specular_tex")
        link_nodes(links, specular_node, "Color", shader, "Specular")
    # always make a specular value node for skin or if there is a mask (but no map)
    elif prop_spec != "default_specular":
        specular_node = make_value_node(nodes, "Specular Strength", prop_spec, spec)
        link_nodes(links, specular_node, "Value", shader, "Specular")
    elif mask_image is not None:
        specular_node = make_value_node(nodes, "Specular Strength", "default_basic_specular", shader.inputs["Specular"].default_value)
        link_nodes(links, specular_node, "Value", shader, "Specular")
    if mask_image is not None:
        mask_node = make_image_node(nodes, mask_image, "specular_mask_tex")
        advance_cursor()
        mult_node = make_math_node(nodes, "MULTIPLY")
        if specular_node.type == "VALUE":
            link_nodes(links, specular_node, "Value", mult_node, 0)
        else:
            link_nodes(links, specular_node, "Color", mult_node, 0)
        link_nodes(links, mask_node, "Color", mult_node, 1)
        link_nodes(links, mult_node, "Value", shader, "Specular")

    # Roughness
    #
    reset_cursor()
    roughness_image = find_material_image(mat, ROUGHNESS_MAP)
    roughness_node = None
    if roughness_image is not None:
        roughness_node = make_image_node(nodes, roughness_image, "roughness_tex")
        rprop_name, rprop_val = get_roughness_strength(obj, mat)
        if is_skin_material(mat):
            advance_cursor()
            remap_node = make_shader_node(nodes, "ShaderNodeMapRange")
            remap_node.name = unique_name(rprop_name)
            set_node_input(remap_node, "To Min", rprop_val)
            link_nodes(links, roughness_node, "Color", remap_node, "Value")
            link_nodes(links, remap_node, "Result", shader, "Roughness")
        elif is_teeth_material(mat) or is_tongue_material(mat):
            advance_cursor()
            rmult_node = make_math_node(nodes, "MULTIPLY", 1, rprop_val)
            rmult_node.name = unique_name(rprop_name)
            link_nodes(links, roughness_node, "Color", rmult_node, 0)
            link_nodes(links, rmult_node, "Value", shader, "Roughness")
        else:
            link_nodes(links, roughness_node, "Color", shader, "Roughness")

    # Emission
    #
    reset_cursor()
    emission_image = find_material_image(mat, EMISSION_MAP)
    emission_node = None
    if emission_image is not None:
        emission_node = make_image_node(nodes, emission_image, "emission_tex")
        link_nodes(links, emission_node, "Color", shader, "Emission")

    # Alpha
    #
    reset_cursor()
    alpha_image = find_material_image(mat, ALPHA_MAP)
    alpha_node = None
    if alpha_image is not None:
        alpha_node = make_image_node(nodes, alpha_image, "opacity_tex")
        dir,file = os.path.split(alpha_image.filepath)
        if "_diffuse." in file.lower() or "_albedo." in file.lower():
            link_nodes(links, alpha_node, "Alpha", shader, "Alpha")
        else:
            link_nodes(links, alpha_node, "Color", shader, "Alpha")
    # material alpha blend settings
    if is_hair_object(obj, mat) or is_eyelash_material(mat):
        set_material_alpha(mat, "HASHED")
    elif shader.inputs["Alpha"].default_value < 1.0:
        set_material_alpha(mat, props.blend_mode)
    else:
        set_material_alpha(mat, "OPAQUE")

    # Normal
    #
    reset_cursor()
    normal_image = find_material_image(mat, NORMAL_MAP)
    bump_image = find_material_image(mat, BUMP_MAP)
    normal_node = bump_node = normalmap_node = bumpmap_node = None
    if normal_image is not None:
        normal_node = make_image_node(nodes, normal_image, "normal_tex")
        advance_cursor()
        normalmap_node = make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        link_nodes(links, normalmap_node, "Normal", shader, "Normal")
    if bump_image is not None:
        prop_bump, bump_strength = get_bump_strength(obj, mat)
        bump_strength_node = make_value_node(nodes, "Bump Strength", prop_bump, bump_strength / 1000)
        bump_node = make_image_node(nodes, bump_image, "bump_tex")
        advance_cursor()
        bumpmap_node = make_shader_node(nodes, "ShaderNodeBump", 0.7)
        advance_cursor()
        link_nodes(links, bump_strength_node, "Value", bumpmap_node, "Distance")
        link_nodes(links, bump_node, "Color", bumpmap_node, "Height")
        if normal_image is not None:
            link_nodes(links, normalmap_node, "Normal", bumpmap_node, "Normal")
        link_nodes(links, bumpmap_node, "Normal", shader, "Normal")

    return

# the 'Compatible' material is the bare minimum required to export the corrent textures with the FBX
# it will connect just the diffuse, metallic, specular, roughness, opacity and normal/bump
def connect_compat_material(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Base Color
    #
    reset_cursor()
    diffuse_image = find_material_image(mat, BASE_COLOR_MAP)
    if (diffuse_image is not None):
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        link_nodes(links, diffuse_node, "Color", shader, "Base Color")

    # Metallic
    #
    reset_cursor()
    metallic_image = find_material_image(mat, METALLIC_MAP)
    metallic_node = None
    if metallic_image is not None:
        metallic_node = make_image_node(nodes, metallic_image, "metallic_tex")
        link_nodes(links, metallic_node, "Color", shader, "Metallic")

    # Specular
    #
    reset_cursor()
    specular_image = find_material_image(mat, SPECULAR_MAP)
    if specular_image is not None:
        specular_node = make_image_node(nodes, specular_image, "specular_tex")
        link_nodes(links, specular_node, "Color", shader, "Specular")
    if is_skin_material(mat):
        set_node_input(shader, "Specular", 0.2)
    if is_eye_material(mat):
        set_node_input(shader, "Specular", 0.8)

    # Roughness
    #
    reset_cursor()
    roughness_image = find_material_image(mat, ROUGHNESS_MAP)
    if roughness_image is not None:
        roughness_node = make_image_node(nodes, roughness_image, "roughness_tex")
        link_nodes(links, roughness_node, "Color", shader, "Roughness")
    if is_eye_material(mat):
        set_node_input(shader, "Roughness", 0)

    # Emission
    #
    reset_cursor()
    emission_image = find_material_image(mat, EMISSION_MAP)
    emission_node = None
    if emission_image is not None:
        emission_node = make_image_node(nodes, emission_image, "emission_tex")
        link_nodes(links, emission_node, "Color", shader, "Emission")

    # Alpha
    #
    reset_cursor()
    alpha_image = find_material_image(mat, ALPHA_MAP)
    alpha_node = None
    if alpha_image is not None:
        alpha_node = make_image_node(nodes, alpha_image, "opacity_tex")
        file = os.path.split(alpha_image.filepath)[1]
        if "_diffuse." in file.lower() or "_albedo." in file.lower():
            link_nodes(links, alpha_node, "Alpha", shader, "Alpha")
        else:
            link_nodes(links, alpha_node, "Color", shader, "Alpha")
    # material alpha blend settings
    if is_hair_object(obj, mat) or is_eyelash_material(mat):
        set_material_alpha(mat, "HASHED")
    elif is_eye_occlusion_material(mat) or is_tearline_material(mat):
        set_material_alpha(mat, props.blend_mode)
    elif shader.inputs["Alpha"].default_value < 1.0:
        set_material_alpha(mat, props.blend_mode)
    else:
        set_material_alpha(mat, "OPAQUE")

    # Normal
    #
    reset_cursor()
    normal_image = find_material_image(mat, NORMAL_MAP)
    bump_image = find_material_image(mat, BUMP_MAP)
    normal_node = bump_node = normalmap_node = bumpmap_node = None
    if normal_image is not None:
        normal_node = make_image_node(nodes, normal_image, "normal_tex")
        advance_cursor()
        normalmap_node = make_shader_node(nodes, "ShaderNodeNormalMap", 0.6)
        link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        link_nodes(links, normalmap_node, "Normal", shader, "Normal")
    elif bump_image is not None:
        bump_node = make_image_node(nodes, bump_image, "bump_tex")
        advance_cursor()
        bumpmap_node = make_shader_node(nodes, "ShaderNodeBump", 0.7)
        advance_cursor()
        set_node_input(bumpmap_node, "Distance", 0.002)
        link_nodes(links, bump_node, "Color", bumpmap_node, "Height")
        link_nodes(links, bumpmap_node, "Normal", shader, "Normal")

    return

def connect_base_color(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps

    diffuse_image = find_material_image(mat, BASE_COLOR_MAP)
    blend_image = find_material_image(mat, MOD_BASECOLORBLEND_MAP)
    ao_image = find_material_image(mat, MOD_AO_MAP)
    mcmao_image = find_material_image(mat, MOD_MCMAO_MAP)
    prop_blend, blend_value = get_blend_strength(obj, mat)
    prop_ao, ao_value = get_ao_strength(obj, mat)
    prop_group = get_material_group(obj, mat)

    count = count_maps(diffuse_image, ao_image, blend_image, mcmao_image)
    if count == 0:
        return None

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    reset_cursor()
    # space
    advance_cursor(-count)
    # maps
    ao_node = blend_node = diffuse_node = mcmao_node = None
    if mcmao_image is not None:
        mcmao_node = make_image_node(nodes, mcmao_image, "mcmao_tex")
        step_cursor()
    if ao_image is not None:
        ao_node = make_image_node(nodes, ao_image, "diffuse_tex")
        step_cursor()
    if blend_image is not None:
        blend_node = make_image_node(nodes, blend_image, "diffuse_tex")
        step_cursor()
    if diffuse_image is not None:
        diffuse_node = make_image_node(nodes, diffuse_image, "diffuse_tex")
        step_cursor()
    # groups
    if mcmao_image is not None:
        group = get_node_group("color_head_mixer")
        group_node = make_node_group_node(nodes, group, "Base Color Head Mixer", "color_" + prop_group + "_mixer")
        drop_cursor(0.3)
    elif blend_image is not None:
        group = get_node_group("color_blend_ao_mixer")
        group_node = make_node_group_node(nodes, group, "Base Color Mixer", "color_" + prop_group + "_mixer")
    else:
        group = get_node_group("color_ao_mixer")
        group_node = make_node_group_node(nodes, group, "Base Color Mixer", "color_" + prop_group + "_mixer")
    # values
    if diffuse_image is None:
        set_node_input(group_node, "Diffuse", shader.inputs["Base Color"].default_value)
    if blend_image is not None:
        set_node_input(group_node, "Blend Strength", blend_value)
    if mcmao_image is not None:
        set_node_input(group_node, "Mouth AO", props.skin_mouth_ao)
        set_node_input(group_node, "Nostril AO", props.skin_nostril_ao)
        set_node_input(group_node, "Lips AO", props.skin_lips_ao)
    set_node_input(group_node, "AO Strength", ao_value)
    # links
    if mcmao_image is not None:
        link_nodes(links, mcmao_node, "Color", group_node, "MCMAO")
        link_nodes(links, mcmao_node, "Alpha", group_node, "LLAO")
    if diffuse_image is not None:
        link_nodes(links, diffuse_node, "Color", group_node, "Diffuse")
    if blend_image is not None:
        link_nodes(links, blend_node, "Color", group_node, "Blend")
    if ao_image is not None:
        link_nodes(links, ao_node, "Color", group_node, "AO")
    link_nodes(links, group_node, "Base Color", shader, "Base Color")

    return group_node


def connect_subsurface(obj, mat, shader, diffuse_node):
    props = bpy.context.scene.CC3ImportProps

    sss_image = find_material_image(mat, SUBSURFACE_MAP)
    trans_image = find_material_image(mat, MOD_TRANSMISSION_MAP)
    prop_radius, sss_radius = get_sss_radius(obj, mat)
    prop_falloff, sss_falloff = get_sss_falloff(obj, mat)
    prop_group = get_material_group(obj, mat)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    count = count_maps(trans_image, sss_image)
    if count == 0 and not is_hair_object(obj, mat) and not is_skin_material(mat):
        return None

    reset_cursor()
    # space
    advance_cursor(-count)
    # maps
    sss_node = trans_node = None
    if trans_image is not None:
        trans_node = make_image_node(nodes, trans_image, "transmission_tex")
        step_cursor()
    if sss_image is not None:
        sss_node = make_image_node(nodes, sss_image, "sss_tex")
        step_cursor()
    # group
    group = get_node_group("subsurface_mixer")
    group_node = make_node_group_node(nodes, group, "Subsurface Mixer", "subsurface_" + prop_group + "_mixer")
    # values
    set_node_input(group_node, "Radius", sss_radius * UNIT_SCALE)
    set_node_input(group_node, "Falloff", sss_falloff)
    if diffuse_node is None:
        set_node_input(group_node, "Diffuse", shader.inputs["Base Color"].default_value)
    # links
    else:
        link_nodes(links, diffuse_node, "Base Color", group_node, "Diffuse")
        link_nodes(links, diffuse_node, "Color", group_node, "Diffuse")
    link_nodes(links, sss_node, "Color", group_node, "Scatter")
    link_nodes(links, trans_node, "Color", group_node, "Transmission")
    link_nodes(links, group_node, "Subsurface", shader, "Subsurface")
    link_nodes(links, group_node, "Subsurface Radius", shader, "Subsurface Radius")
    link_nodes(links, group_node, "Subsurface Color", shader, "Subsurface Color")

    # subsurface translucency
    if is_skin_material(mat) or is_hair_object(obj, mat):
        mat.use_sss_translucency = True
    else:
        mat.use_sss_translucency = False

    return group_node


def connect_msr(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps

    metallic_image = find_material_image(mat, METALLIC_MAP)
    specular_image = find_material_image(mat, SPECULAR_MAP)
    mask_image = find_material_image(mat, MOD_SPECMASK_MAP)
    roughness_image = find_material_image(mat, ROUGHNESS_MAP)
    prop_spec, specular_strength = get_specular_strength(obj, mat)
    prop_roughness, roughness_remap = get_roughness_strength(obj, mat)
    prop_group = get_material_group(obj, mat)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    count = count_maps(mask_image, specular_image, roughness_image, metallic_image)
    if count == 0:
        return None

    reset_cursor()
    # space
    advance_cursor(-count)
    # maps
    metallic_node = specular_node = roughness_node = mask_node = None
    if roughness_image is not None:
        roughness_node = make_image_node(nodes, roughness_image, "roughness_tex")
        step_cursor()
    if mask_image is not None:
        mask_node = make_image_node(nodes, mask_image, "specular_mask_tex")
        step_cursor()
    if specular_image is not None:
        specular_node = make_image_node(nodes, specular_image, "specular_tex")
        step_cursor()
    if metallic_image is not None:
        metallic_node = make_image_node(nodes, metallic_image, "metallic_tex")
        step_cursor()
    # groups
    group = get_node_group("msr_mixer")
    group_node = make_node_group_node(nodes, group, "Metallic, Specular & Roughness Mixer", "msr_" + prop_group + "_mixer")
    # values
    set_node_input(group_node, "Specular", specular_strength)
    set_node_input(group_node, "Roughness Remap", roughness_remap)
    # links
    link_nodes(links, metallic_node, "Color", group_node, "Metallic")
    link_nodes(links, specular_node, "Color", group_node, "Specular")
    link_nodes(links, mask_node, "Color", group_node, "Specular Mask")
    link_nodes(links, roughness_node, "Color", group_node, "Roughness")
    link_nodes(links, group_node, "Metallic", shader, "Metallic")
    link_nodes(links, group_node, "Specular", shader, "Specular")
    link_nodes(links, group_node, "Roughness", shader, "Roughness")

    return group_node


def connect_emission_alpha(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps

    emission_image = find_material_image(mat, EMISSION_MAP)
    alpha_image = find_material_image(mat, ALPHA_MAP)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    emission_node = alpha_node = None
    # emission
    reset_cursor()
    if emission_image is not None:
        emission_node = make_image_node(nodes, emission_image, "emission_tex")
        link_nodes(links, emission_node, "Color", shader, "Emission")
    # alpha
    reset_cursor()
    if alpha_image is not None:
        alpha_node = make_image_node(nodes, alpha_image, "opacity_tex")
        dir,file = os.path.split(alpha_image.filepath)
        if "_diffuse." in file.lower() or "_albedo." in file.lower():
            link_nodes(links, alpha_node, "Alpha", shader, "Alpha")
        else:
            link_nodes(links, alpha_node, "Color", shader, "Alpha")
    # material settings
    if is_hair_object(obj, mat) or is_eyelash_material(mat):
        set_material_alpha(mat, "HASHED")
    elif shader.inputs["Alpha"].default_value < 1.0:
        set_material_alpha(mat, props.blend_mode)
    else:
        set_material_alpha(mat, "OPAQUE")


def connect_normal(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps

    normal_node = bump_node = blend_node = micro_node = mask_node = tiling_node = None
    normal_image = find_material_image(mat, NORMAL_MAP)
    bump_image = find_material_image(mat, BUMP_MAP)
    blend_image = find_material_image(mat, MOD_NORMALBLEND_MAP)
    micro_image = find_material_image(mat, MOD_MICRONORMAL_MAP)
    mask_image = find_material_image(mat, MOD_MICRONORMALMASK_MAP)
    prop_bump, bump_strength = get_bump_strength(obj, mat)
    prop_blend, blend_strength = get_normal_blend_strength(obj, mat)
    prop_micronormal, micronormal_strength = get_micronormal_strength(obj, mat)
    prop_tiling, micronormal_tiling = get_micronormal_tiling(obj, mat)
    prop_group = get_material_group(obj, mat)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    count = count_maps(bump_image, mask_image, micro_image, blend_image, normal_image)
    if count == 0:
        return None

    reset_cursor()
    # space
    advance_cursor(-count)
    # maps
    if bump_image is not None:
        bump_node = make_image_node(nodes, bump_image, "bump_tex")
        step_cursor()
    if mask_image is not None:
        mask_node = make_image_node(nodes, mask_image, "micro_normal_mask_tex")
        step_cursor()
    if micro_image is not None:
        advance_cursor(-1)
        drop_cursor(0.75)
        group = get_node_group("tiling_mapping")
        tiling_node = make_node_group_node(nodes, group, "Micro Normal Tiling", "tiling_" + prop_group + "_mapping")
        advance_cursor()
        micro_node = make_image_node(nodes, micro_image, "micro_normal_tex")
        step_cursor()
    if blend_image is not None:
        blend_node = make_image_node(nodes, blend_image, "normal_blend_tex")
        step_cursor()
    if normal_image is not None:
        normal_node = make_image_node(nodes, normal_image, "normal_tex")
        step_cursor()
    # groups
    if bump_image is not None:
        group = get_node_group("bump_mixer")
    elif normal_image is not None and bump_image is None and mask_image is None and \
            micro_image is None and blend_image is None:
        normalmap_node = make_shader_node(nodes, "ShaderNodeNormalMap")
        link_nodes(links, normal_node, "Color", normalmap_node, "Color")
        link_nodes(links, normalmap_node, "Normal", shader, "Normal")
        return normalmap_node
    elif blend_image is not None:
        group = get_node_group("normal_micro_mask_blend_mixer")
    else:
        group =  get_node_group("normal_micro_mask_mixer")
    group_node = make_node_group_node(nodes, group, "Normal Mixer", "normal_" + prop_group + "_mixer")
    # values
    set_node_input(group_node, "Normal Blend Strength", blend_strength)
    set_node_input(group_node, "Micro Normal Strength", micronormal_strength)
    set_node_input(group_node, "Bump Map Height", bump_strength / 1000)
    set_node_input(tiling_node, "Tiling", micronormal_tiling)
    # links
    link_nodes(links, group_node, "Normal", shader, "Normal")
    link_nodes(links, normal_node, "Color", group_node, "Normal")
    link_nodes(links, bump_node, "Color", group_node, "Bump Map")
    link_nodes(links, blend_node, "Color", group_node, "Normal Blend")
    link_nodes(links, micro_node, "Color", group_node, "Micro Normal")
    link_nodes(links, tiling_node, "Vector", micro_node, "Vector")
    link_nodes(links, mask_node, "Color", group_node, "Micro Normal Mask")

    return group_node


def apply_cloth_settings(obj, cloth_type):
    prefs = bpy.context.preferences.addons[__name__].preferences
    mod = get_cloth_physics_mod(obj)
    if mod is None:
        return
    cache = get_object_cache(obj)
    cache.cloth_settings = cloth_type

    log_info("Setting " + obj.name + " cloth settings to: " + cloth_type)
    mod.settings.vertex_group_mass = prefs.physics_group + "_Pin"
    mod.settings.time_scale = 1
    if cloth_type == "HAIR":
        mod.settings.quality = 4
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.15
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 5
        mod.settings.compression_stiffness = 5
        mod.settings.shear_stiffness = 5
        mod.settings.bending_stiffness = 5
        # dampening
        mod.settings.tension_damping = 0
        mod.settings.compression_damping = 0
        mod.settings.shear_damping = 0
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 2
    elif cloth_type == "SILK":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.25
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 5
        mod.settings.compression_stiffness = 5
        mod.settings.shear_stiffness = 5
        mod.settings.bending_stiffness = 10
        # dampening
        mod.settings.tension_damping = 0
        mod.settings.compression_damping = 0
        mod.settings.shear_damping = 0
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    elif cloth_type == "DENIM":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 1
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 40
        mod.settings.compression_stiffness = 40
        mod.settings.shear_stiffness = 40
        mod.settings.bending_stiffness = 60
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 10
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    elif cloth_type == "LEATHER":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.4
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 80
        mod.settings.compression_stiffness = 80
        mod.settings.shear_stiffness = 80
        mod.settings.bending_stiffness = 80
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 10
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    elif cloth_type == "RUBBER":
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 3
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 15
        mod.settings.compression_stiffness = 15
        mod.settings.shear_stiffness = 15
        mod.settings.bending_stiffness = 40
        # dampening
        mod.settings.tension_damping = 25
        mod.settings.compression_damping = 25
        mod.settings.shear_damping = 25
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4
    else: #cotton
        mod.settings.quality = 8
        mod.settings.pin_stiffness = 1
        # physical properties
        mod.settings.mass = 0.3
        mod.settings.air_damping = 1
        mod.settings.bending_model = 'ANGULAR'
        # stiffness
        mod.settings.tension_stiffness = 20
        mod.settings.compression_stiffness = 20
        mod.settings.shear_stiffness = 20
        mod.settings.bending_stiffness = 20
        # dampening
        mod.settings.tension_damping = 5
        mod.settings.compression_damping = 5
        mod.settings.shear_damping = 5
        mod.settings.bending_damping = 0
        # collision
        mod.collision_settings.distance_min = 0.005
        mod.collision_settings.collision_quality = 4


def get_cloth_physics_mod(obj):
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == "CLOTH":
                return mod
    return None


def get_collision_physics_mod(obj):
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == "COLLISION":
                return mod
    return None


def get_weight_map_mods(obj):
    edit_mods = []
    mix_mods = []
    if obj is not None:
        for mod in obj.modifiers:
            if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name:
                edit_mods.append(mod)
            if mod.type == "VERTEX_WEIGHT_MIX" and NODE_PREFIX in mod.name:
                mix_mods.append(mod)
    return edit_mods, mix_mods


def get_material_weight_map_mods(obj, mat):
    edit_mod = None
    mix_mod = None
    if obj is not None and mat is not None:
        for mod in obj.modifiers:
            if mod.type == "VERTEX_WEIGHT_EDIT" and (NODE_PREFIX + mat.name + "_WeightEdit") in mod.name:
                edit_mod = mod
            if mod.type == "VERTEX_WEIGHT_MIX" and (NODE_PREFIX + mat.name + "_WeightMix") in mod.name:
                mix_mod = mod
    return edit_mod, mix_mod


def add_collision_physics(obj):
    """Adds a Collision modifier to the object, depending on the object cache settings.

    Does not overwrite or re-create any existing Collision modifier.
    """

    cache = get_object_cache(obj)
    if (cache.collision_physics == "ON"
        or (cache.collision_physics == "DEFAULT"
            and "Base_Body" in obj.name)):

        if get_collision_physics_mod(obj) is None:
            collision_mod = obj.modifiers.new(unique_name("Collision"), type="COLLISION")
            collision_mod.settings.thickness_outer = 0.005
            log_info("Collision Modifier: " + collision_mod.name + " applied to " + obj.name)
    elif cache.collision_physics == "OFF":
        log_info("Collision Physics disabled for: " + obj.name)


def remove_collision_physics(obj):
    """Removes the Collision modifier from the object.
    """

    for mod in obj.modifiers:
        if mod.type == "COLLISION":
            log_info("Removing Collision modifer: " + mod.name + " from: " + obj.name)
            obj.modifiers.remove(mod)


def add_cloth_physics(obj):
    """Adds a Cloth modifier to the object depending on the object cache settings.

    Does not overwrite or re-create any existing Cloth modifier.
    Sets the cache bake range to the same as any action on the character's armature.
    Applies cloth settings based on the object cache settings.
    Repopulates the existing weight maps, depending on their cache settings.
    """

    prefs = bpy.context.preferences.addons[__name__].preferences
    props = bpy.context.scene.CC3ImportProps

    cache = get_object_cache(obj)

    if cache.cloth_physics == "ON" and get_cloth_physics_mod(obj) is None:

        # Create the Cloth modifier
        cloth_mod = obj.modifiers.new(unique_name("Cloth"), type="CLOTH")
        log_info("Cloth Modifier: " + cloth_mod.name + " applied to " + obj.name)

        # Create the physics pin vertex group if it doesn't exist
        pin_group = prefs.physics_group + "_Pin"
        if pin_group not in obj.vertex_groups:
            obj.vertex_groups.new(name = pin_group)

        # Set cache bake frame range
        frame_count = 250
        if obj.parent is not None and obj.parent.animation_data is not None and \
                obj.parent.animation_data.action is not None:
            frame_count = math.ceil(obj.parent.animation_data.action.frame_range[1])
        log_info("Setting " + obj.name + " bake cache frame range to [1-" + str(frame_count) + "]")
        cloth_mod.point_cache.frame_start = 1
        cloth_mod.point_cache.frame_end = frame_count

        # Apply cloth settings
        if cache.cloth_settings != "DEFAULT":
            apply_cloth_settings(obj, cache.cloth_settings)
        elif obj == props.hair_object:
            apply_cloth_settings(obj, "HAIR")
        else:
            apply_cloth_settings(obj, "COTTON")

        # Add any existing weight maps
        for mat in obj.data.materials:
            add_material_weight_map(obj, mat, create = False)

        fix_physics_mod_order(obj)

    elif cache.cloth_physics == "OFF":
        log_info("Cloth Physics disabled for: " + obj.name)


def remove_cloth_physics(obj):
    """Removes the Cloth modifier from the object.

    Also removes any active weight maps and also removes the weight map vertex group.
    """

    prefs = bpy.context.preferences.addons[__name__].preferences

    # Remove the Cloth modifier
    for mod in obj.modifiers:
        if mod.type == "CLOTH":
            log_info("Removing Cloth modifer: " + mod.name + " from: " + obj.name)
            obj.modifiers.remove(mod)

    # Remove any weight maps
    for mat in obj.data.materials:
        if mat is not None:
            remove_material_weight_maps(obj, mat)
            weight_group = prefs.physics_group + "_" + strip_name(mat.name)
            if weight_group in obj.vertex_groups:
                obj.vertex_groups.remove(obj.vertex_groups[weight_group])

    # If there are no weight maps left on the object, remove the vertex group
    mods = 0
    for mod in obj.modifiers:
        if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name:
            mods += 1

    pin_group = prefs.physics_group + "_Pin"
    if mods == 0 and pin_group in obj.vertex_groups:
        log_info("Removing vertex group: " + pin_group + " from: " + obj.name)
        obj.vertex_groups.remove(obj.vertex_groups[pin_group])


def remove_all_physics_mods(obj):
    """Removes all physics modifiers from the object.

    Used when (re)building the character materials.
    """

    log_info("Removing all related physics modifiers from: " + obj.name)
    for mod in obj.modifiers:
        if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name:
            obj.modifiers.remove(mod)
        elif mod.type == "VERTEX_WEIGHT_MIX" and NODE_PREFIX in mod.name:
            obj.modifiers.remove(mod)
        elif mod.type == "CLOTH":
            obj.modifiers.remove(mod)
        elif mod.type == "COLLISION":
            obj.modifiers.remove(mod)


def enable_collision_physics(obj):
    cache = get_object_cache(obj)
    cache.collision_physics = "ON"
    log_info("Enabling Collision physics for: " + obj.name)
    add_collision_physics(obj)


def disable_collision_physics(obj):
    cache = get_object_cache(obj)
    cache.collision_physics = "OFF"
    log_info("Disabling Collision physics for: " + obj.name)
    remove_collision_physics(obj)


def enable_cloth_physics(obj):
    cache = get_object_cache(obj)
    cache.cloth_physics = "ON"
    log_info("Enabling Cloth physics for: " + obj.name)
    add_cloth_physics(obj)


def disable_cloth_physics(obj):
    cache = get_object_cache(obj)
    cache.cloth_physics = "OFF"
    log_info("Removing cloth physics for: " + obj.name)
    remove_cloth_physics(obj)


def get_weight_map_image(obj, mat, create = False):
    """Returns the weight map image for the material.

    Fetches the Image for the given materials weight map, if it exists.
    If not, the image can be created and packed into the blend file and stored
    in the material cache as a temporary weight map image.
    """

    props = bpy.context.scene.CC3ImportProps
    weight_map = find_material_image(mat, WEIGHT_MAP)

    if weight_map is None and create:
        cache = get_material_cache(mat)
        name = strip_name(mat.name) + "_WeightMap"
        tex_size = int(props.physics_tex_size)
        weight_map = bpy.data.images.new(name, tex_size, tex_size, is_data=True)
        # make the image 'dirty' so it converts to a file based image which can be saved:
        weight_map.pixels[0] = 0.0
        weight_map.file_format = "PNG"
        weight_map.filepath_raw = os.path.join(cache.dir, name + ".png")
        weight_map.save()
        # keep track of which weight maps we created:
        cache.temp_weight_map = weight_map
        log_info("Weight-map image: " + weight_map.name + " created and saved.")

    return weight_map


def add_material_weight_map(obj, mat, create = False):
    """Adds a weight map 'Vertex Weight Edit' modifier for the object's material.

    Gets or creates (if instructed) the material's weight map then creates
    or re-creates the modifier to generate the physics 'Pin' vertex group.
    """

    if cloth_physics_available(obj, mat):
        if create:
            weight_map = get_weight_map_image(obj, mat, create)
        else:
            weight_map = find_material_image(mat, WEIGHT_MAP)

        remove_material_weight_maps(obj, mat)
        if weight_map is not None:
            attach_material_weight_map(obj, mat, weight_map)
    else:
        log_info("Cloth Physics has been disabled for: " + obj.name)
        return


def fix_physics_mod_order(obj):
    """Moves any cloth modifier to the end of the list, so it is operates
    on all the 'Vertex Weight Edit' modifiers.
    """

    try:
        if bpy.context.view_layer.objects.active is not obj:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
        num_mods = len(obj.modifiers)
        cloth_mod = get_cloth_physics_mod(obj)
        max = 50
        if cloth_mod is not None:
            while obj.modifiers.find(cloth_mod.name) < num_mods - 1:
                print("Shifting: " + cloth_mod.name)
                bpy.ops.object.modifier_move_down(modifier=cloth_mod.name)
            max -= 1
            if max == 0:
                return
    except:
        log_error("Something went wrong fixing cloth modifier order...")



def remove_material_weight_maps(obj, mat):
    """Removes the weight map 'Vertex Weight Edit' modifier for the object's material.

    This does not remove or delete the weight map image or temporary packed image,
    or the texture based on the weight map image, just the modifier.
    """

    edit_mod, mix_mod = get_material_weight_map_mods(obj, mat)
    if edit_mod is not None:
        log_info("    Removing weight map vertex edit modifer: " + edit_mod.name)
        obj.modifiers.remove(edit_mod)
    if mix_mod is not None:
        log_info("    Removing weight map vertex mix modifer: " + mix_mod.name)
        obj.modifiers.remove(mix_mod)


def enable_material_weight_map(obj, mat):
    """Enables the weight map for the object's material and (re)creates the Vertex Weight Edit modifier.
    """

    cache = get_material_cache(mat)
    if cache.cloth_physics == "OFF":
        cache.cloth_physics = "ON"
    add_material_weight_map(obj, mat, True)
    fix_physics_mod_order(obj)


def disable_material_weight_map(obj, mat):
    """Disables the weight map for the object's material and removes the Vertex Weight Edit modifier.
    """

    cache = get_material_cache(mat)
    cache.cloth_physics = "OFF"
    remove_material_weight_maps(obj, mat)
    pass


def collision_physics_available(obj):
    obj_cache = get_object_cache(obj)
    collision_mod = get_collision_physics_mod(obj)
    if collision_mod is None:
        if obj_cache.collision_physics == "OFF":
            return False
    return True


def cloth_physics_available(obj, mat):
    """Is cloth physics allowed on this object and material?
    """

    obj_cache = get_object_cache(obj)
    mat_cache = get_material_cache(mat)
    cloth_mod = get_cloth_physics_mod(obj)
    if cloth_mod is None:
        if obj_cache.cloth_physics == "OFF":
            return False
        if mat_cache is not None and mat_cache.cloth_physics == "OFF":
            return False
    else:
        # if cloth physics was disabled by the add-on,
        # but re-enabled in the physics panel,
        # correct the object cache setting:
        if obj_cache.cloth_physics == "OFF":
            obj_cache.cloth_physics == "ON"
    return True


def get_material_vertices(obj, mat):
    verts = []
    mesh = obj.data
    for poly in mesh.polygons:
        poly_mat = obj.material_slots[poly.material_index].material
        if poly_mat == mat:
            for vert in poly.vertices:
                if vert not in verts:
                    verts.append(vert)
    return verts


def clear_vertex_group(obj, vertex_group):
    all_verts = []
    for v in obj.data.vertices:
        all_verts.append(v.index)
    vertex_group.remove(all_verts)


def set_vertex_group(obj, vertex_group, value):
    all_verts = []
    for v in obj.data.vertices:
        all_verts.append(v.index)
    vertex_group.add(all_verts, value, 'ADD')


def attach_material_weight_map(obj, mat, weight_map):
    """Attaches a weight map to the object's material via a 'Vertex Weight Edit' modifier.

    This will attach the supplied weight map or will try to find an existing weight map,
    but will not create a new weight map if it doesn't already exist.
    """

    prefs = bpy.context.preferences.addons[__name__].preferences

    if weight_map is not None:
        # Make a texture based on the weight map image
        mat_name = strip_name(mat.name)
        tex_name = mat_name + "_Weight"
        tex = None
        for t in bpy.data.textures:
            if t.name.startswith(NODE_PREFIX + tex_name):
                tex = t
        if tex is None:
            tex = bpy.data.textures.new(unique_name(tex_name), "IMAGE")
            log_info("Texture: " + tex.name + " created for weight map transfer")
        else:
            log_info("Texture: " + tex.name + " already exists for weight map transfer")
        tex.image = weight_map

        # Create the physics pin vertex group and the material weightmap group if they don't exist:
        pin_group = prefs.physics_group + "_Pin"
        material_group = prefs.physics_group + "_" + mat_name
        if pin_group not in obj.vertex_groups:
            pin_vertex_group = obj.vertex_groups.new(name = pin_group)
        else:
            pin_vertex_group = obj.vertex_groups[pin_group]
        if material_group not in obj.vertex_groups:
            weight_vertex_group = obj.vertex_groups.new(name = material_group)
        else:
            weight_vertex_group = obj.vertex_groups[material_group]
        # The material weight map group should contain only those verteces affected by the material, default weight to 1.0
        clear_vertex_group(obj, weight_vertex_group)
        mat_verts = get_material_vertices(obj, mat)
        weight_vertex_group.add(mat_verts, 1.0, 'ADD')
        # The pin group should contain all verteces in the mesh default weighted to 1.0
        set_vertex_group(obj, pin_vertex_group, 1.0)

        # set the pin group in the cloth physics modifier
        mod_cloth = get_cloth_physics_mod(obj)
        if mod_cloth is not None:
            mod_cloth.settings.vertex_group_mass = pin_group

        # re-create create the Vertex Weight Edit modifier and the Vertex Weight Mix modifer
        remove_material_weight_maps(obj, mat)
        edit_mod = obj.modifiers.new(unique_name(mat_name + "_WeightEdit"), "VERTEX_WEIGHT_EDIT")
        mix_mod = obj.modifiers.new(unique_name(mat_name + "_WeightMix"), "VERTEX_WEIGHT_MIX")
        # Use the texture as the modifiers vertex weight source
        edit_mod.mask_texture = tex
        # Setup the modifier to generate the inverse of the weight map in the vertex group
        edit_mod.use_add = False
        edit_mod.use_remove = False
        edit_mod.add_threshold = 0.01
        edit_mod.remove_threshold = 0.01
        edit_mod.vertex_group = material_group
        edit_mod.default_weight = 1
        edit_mod.falloff_type = 'LINEAR'
        edit_mod.invert_falloff = True
        edit_mod.mask_constant = 1
        edit_mod.mask_tex_mapping = 'UV'
        edit_mod.mask_tex_use_channel = 'INT'
        # The Vertex Weight Mix modifier takes the material weight map group and mixes it into the pin weight group:
        # (this allows multiple weight maps from different materials and UV layouts to combine in the same mesh)
        mix_mod.vertex_group_a = pin_group
        mix_mod.vertex_group_b = material_group
        mix_mod.invert_mask_vertex_group = True
        mix_mod.default_weight_a = 1
        mix_mod.default_weight_b = 1
        mix_mod.mix_set = 'B' #'ALL'
        mix_mod.mix_mode = 'SET'
        mix_mod.invert_mask_vertex_group = False
        log_info("Weight map: " + weight_map.name + " applied to: " + obj.name + "/" + mat.name)


def count_weightmaps(objects):
    num_maps = 0
    num_dirty = 0
    for obj in objects:
        if obj.type == "MESH":
            for mod in obj.modifiers:
                if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name:
                    if mod.mask_texture is not None and mod.mask_texture.image is not None:
                        num_maps += 1
                        image = mod.mask_texture.image
                        if image.is_dirty:
                            num_dirty += 1
    return num_maps, num_dirty


def get_dirty_weightmaps(objects):
    maps = []
    for obj in objects:
        if obj.type == "MESH":
            for mod in obj.modifiers:
                if mod.type == "VERTEX_WEIGHT_EDIT" and NODE_PREFIX in mod.name:
                    if mod.mask_texture is not None and mod.mask_texture.image is not None:
                        image = mod.mask_texture.image
                        if image.filepath != "" and (image.is_dirty or not os.path.exists(image.filepath)):
                            maps.append(image)
    return maps


def begin_paint_weight_map(context):
    obj = context.object
    mat = context_material(context)
    props = bpy.context.scene.CC3ImportProps
    if obj is not None and mat is not None:
        props.paint_store_render = bpy.context.space_data.shading.type

        if bpy.context.mode != "PAINT_TEXTURE":
            bpy.ops.object.mode_set(mode="TEXTURE_PAINT")

        if bpy.context.mode == "PAINT_TEXTURE":
            physics_paint_strength_update(None, context)
            weight_map = get_weight_map_image(obj, mat)
            props.paint_object = obj
            props.paint_material = mat
            props.paint_image = weight_map
            if weight_map is not None:
                bpy.context.scene.tool_settings.image_paint.mode = 'IMAGE'
                bpy.context.scene.tool_settings.image_paint.canvas = weight_map
                bpy.context.space_data.shading.type = 'SOLID'


def end_paint_weight_map():
    try:
        props = bpy.context.scene.CC3ImportProps
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.space_data.shading.type = props.paint_store_render
        #props.paint_image.save()
    except:
        log_error("Something went wrong restoring object mode from paint mode!")


def save_dirty_weight_maps(objects):
    """Saves all altered active weight map images to their respective material folders.

    Also saves any missing weight maps.
    """

    maps = get_dirty_weightmaps(objects)

    for weight_map in maps:
        if weight_map.is_dirty:
            log_info("Dirty weight map: " + weight_map.name + " : " + weight_map.filepath)
            weight_map.save()
            log_info("Weight Map: " + weight_map.name + " saved to: " + weight_map.filepath)
        if not os.path.exists(weight_map.filepath):
            log_info("Missing weight map: " + weight_map.name + " : " + weight_map.filepath)
            weight_map.save()
            log_info("Weight Map: " + weight_map.name + " saved to: " + weight_map.filepath)


def delete_selected_weight_map(obj, mat):
    if obj is not None and obj.type == "MESH" and mat is not None:
        edit_mod, mix_mod = get_material_weight_map_mods(obj, mat)
        if edit_mod is not None and edit_mod.mask_texture is not None and edit_mod.mask_texture.image is not None:
            image = edit_mod.mask_texture.image
            try:
                if image.filepath != "" and os.path.exists(image.filepath):
                    log_info("Removing weight map file: " + image.filepath)
                    os.remove(image.filepath)
            except:
                log_error("Removing weight map file: " + image.filepath)
        if edit_mod is not None:
            log_info("Removing 'Vertex Weight Edit' modifer")
            obj.modifiers.remove(edit_mod)
        if mix_mod is not None:
            log_info("Removing 'Vertex Weight Mix' modifer")
            obj.modifiers.remove(mix_mod)


def set_physics_bake_range(obj, start, end):
    cloth_mod = get_cloth_physics_mod(obj)
    if cloth_mod is not None:
        cloth_mod.point_cache.frame_start = start
        cloth_mod.point_cache.frame_end = end
        return True
    return False

def prepare_physics_bake(context):
    # Set cache bake frame range
    #frame_count = 250
    #if obj.parent is not None and obj.parent.animation_data is not None and \
    #        obj.parent.animation_data.action is not None:
    #    frame_count = math.ceil(obj.parent.animation_data.action.frame_range[1])
    #log_info("Setting " + obj.name + " bake cache frame range to [1-" + str(frame_count) + "]")
    #cloth_mod.point_cache.frame_start = 1
    #cloth_mod.point_cache.frame_end = frame_count
    props = bpy.context.scene.CC3ImportProps

    #if bpy.context.mode != "OBJECT":
    #        bpy.ops.object.mode_set(mode="OBJECT")

    #bpy.ops.ptcache.free_bake_all()

    baking = False
    for p in props.import_objects:
        if p.object is not None and p.object.type == "MESH":
            obj = p.object
            set_physics_bake_range(obj, context.scene.frame_start, context.scene.frame_end)


def separate_physics_materials(context):
    if context.object is None: return
    if context.object.type != "MESH": return
    if context.object.data.materials is None: return
    if context.mode != "OBJECT": return

    # remember which materials have active weight maps
    temp = []
    for mat in context.object.data.materials:
        edit_mod, mix_mod = get_material_weight_map_mods(context.object, mat)
        if edit_mod is not None:
            temp.append(mat)

    # remove cloth physics from the object
    disable_cloth_physics(context.object)

    # split the mesh by materials
    tag_objects()
    context.object.tag = False
    bpy.ops.mesh.separate(type='MATERIAL')
    objects = untagged_objects()

    # re-apply cloth physics to the materials which had weight maps
    for obj in objects:
        for mat in obj.data.materials:
            if mat in temp:
                enable_cloth_physics(obj)
                break
    temp = None


def should_separate_materials(context):
    """Check to see if the current object has a weight map for each material.
    If not separating the mesh by material could improve performance.
    """
    if context.object is None: return
    if context.object.data.materials is None: return
    obj = context.object

    cloth_mod = get_cloth_physics_mod(obj)
    if cloth_mod is not None:
        edit_mods, mix_mods = get_weight_map_mods(obj)
        if len(edit_mods) != len(obj.data.materials):
            return True
    return False


def fetch_anim_range(context):
    props = bpy.context.scene.CC3ImportProps

    for p in props.import_objects:
        if p.object is not None and p.object.type == "ARMATURE":
            obj = p.object
            if obj.animation_data is not None and \
               obj.animation_data.action is not None:
                frame_start = math.floor(obj.animation_data.action.frame_range[0])
                frame_end = math.ceil(obj.animation_data.action.frame_range[1])
                context.scene.frame_start = frame_start
                context.scene.frame_end = frame_end
                return


def render_image(context):
    # TODO
    pass


def render_animation(context):
    # TODO
    pass


def get_node_group(name):
    for group in bpy.data.node_groups:
        if NODE_PREFIX in group.name and name in group.name:
            if VERSION_STRING in group.name:
                return group
    return fetch_node_group(name)


def check_node_groups():
    for name in NODE_GROUPS:
        get_node_group(name)


def remove_all_groups():
    for group in bpy.data.node_groups:
        if NODE_PREFIX in group.name:
            bpy.data.node_groups.remove(group)


def rebuild_node_groups():
    remove_all_groups()
    check_node_groups()
    return


def append_node_group(path, object_name):
    for g in bpy.data.node_groups:
        g.tag = True

    filename = "_LIB.blend"
    datablock = "NodeTree"
    file = os.path.join(path, filename)
    if os.path.exists(file):
        bpy.ops.wm.append(directory=os.path.join(path, filename, datablock), filename=object_name, set_fake=False, link=False)

    appended_group = None
    for g in bpy.data.node_groups:
        if not g.tag and object_name in g.name:
            appended_group = g
            g.name = unique_name(object_name)
        g.tag = False
    return appended_group


def fetch_node_group(name):

    paths = [bpy.path.abspath("//"),
             os.path.dirname(os.path.realpath(__file__)),
             ]
    for path in paths:
        log_info("Trying to append: " + path + " > " + name)
        if os.path.exists(path):
            group = append_node_group(path, name)
            if group is not None:
                return group
    log_error("Trying to append group: " + name + ", _LIB.blend library file not found?")
    raise ValueError("Unable to append node group from library file!")


def clean_colletion(collection):
    for item in collection:
        if (item.use_fake_user and item.users == 1) or item.users == 0:
            collection.remove(item)

def delete_object(obj):
    if obj is None:
        return

    # remove any armature actions
    if obj.type == "ARMATURE":
        if obj.animation_data is not None:
            if obj.animation_data.action is not None:
                bpy.data.actions.remove(obj.animation_data.action)

    # remove any shape key actions and remove the shape keys
    if obj.type == "MESH":
        if obj.data.shape_keys is not None:
            if obj.data.shape_keys.animation_data is not None:
                if obj.data.shape_keys.animation_data.action is not None:
                    bpy.data.actions.remove(obj.data.shape_keys.animation_data.action)
        obj.shape_key_clear()

        # remove materials->nodes->images
        for mat in obj.data.materials:
            if mat.node_tree is not None:
                nodes = mat.node_tree.nodes
                for node in nodes:
                    if node.type == "TEX_IMAGE" and node.image is not None:
                        image = node.image
                        bpy.data.images.remove(image)
                    nodes.remove(node)

            # remove physics weight maps and texture masks
            edit_mod, mix_mod = get_material_weight_map_mods(obj, mat)
            if mix_mod is not None:
                obj.modifiers.remove(mix_mod)
            if edit_mod is not None:
                tex = edit_mod.mask_texture
                obj.modifiers.remove(edit_mod)
                if tex is not None:
                    if tex.image is not None:
                        image = tex.image
                        bpy.data.images.remove(image)
                    bpy.data.textures.remove(tex)

            bpy.data.materials.remove(mat)

    if obj.type == "ARMATURE":
        bpy.data.armatures.remove(obj.data)
    else:
        bpy.data.objects.remove(obj)

    #except:
    #    log_error("Something went wrong deleting object...")

def delete_character():
    props = bpy.context.scene.CC3ImportProps

    for p in props.import_objects:
        delete_object(p.object)

    props.import_objects.clear()
    props.import_file = ""
    props.import_type = ""
    props.import_name = ""
    props.import_dir = ""
    props.import_main_tex_dir = ""
    props.import_space_in_name = False
    props.import_embedded = False
    props.import_has_key = False
    props.import_key_file = ""
    props.material_cache.clear()
    props.object_cache.clear()

    props.paint_object = None
    props.paint_material = None
    props.paint_image = None

    clean_colletion(bpy.data.materials)
    clean_colletion(bpy.data.textures)
    clean_colletion(bpy.data.images)
    clean_colletion(bpy.data.meshes)
    clean_colletion(bpy.data.node_groups)

def process_material(obj, mat):
    props = bpy.context.scene.CC3ImportProps

    reset_nodes(mat)

    node_tree = mat.node_tree
    nodes = node_tree.nodes
    shader = None
    cache = get_material_cache(mat)

    # find the Principled BSDF shader node
    for n in nodes:
        if (n.type == "BSDF_PRINCIPLED"):
            shader = n
            break

    # create one if it does not exist
    if shader is None:
        shader = nodes.new("ShaderNodeBsdfPrincipled")

    clear_cursor()

    if props.setup_mode == "COMPAT":
        connect_compat_material(obj, mat, shader)

        move_new_nodes(-600, 0)

    elif is_eye_material(mat):

        if props.setup_mode == "BASIC":
            connect_basic_eye_material(obj, mat, shader)

        elif props.setup_mode == "ADVANCED":
            connect_adv_eye_material(obj, mat, shader)

        move_new_nodes(-600, 0)

    elif is_tearline_material(mat):

        connect_tearline_material(obj, mat, shader)

    elif is_eye_occlusion_material(mat):

        connect_eye_occlusion_material(obj, mat, shader)
        move_new_nodes(-600, 0)

    elif is_mouth_material(mat) and props.setup_mode == "ADVANCED":

        connect_adv_mouth_material(obj, mat, shader)
        move_new_nodes(-600, 0)

    else:

        if props.setup_mode == "BASIC":
            connect_basic_material(obj, mat, shader)

        elif props.setup_mode == "ADVANCED":
            connect_advanced_material(obj, mat, shader)

        move_new_nodes(-600, 0)

    # apply cached alpha settings
    if cache is not None:
        if cache.alpha_mode != "NONE":
            apply_alpha_override(obj, mat, cache.alpha_mode)
        if cache.culling_sides > 0:
            apply_backface_culling(obj, mat, cache.culling_sides)

def scan_for_hair_object(obj):
    if obj.type == "MESH":
        for mat in obj.data.materials:
            if is_hair_object(obj, mat):
                return obj
    return None

def process_object(obj, objects_processed):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__].preferences

    if obj is None or obj in objects_processed:
        return

    objects_processed.append(obj)

    log_info("Processing Object: " + obj.name + ", Type: " + obj.type)

    cache = get_object_cache(obj)

    # try to determine if this is the hair object, if not set
    if props.hair_object is None:
        props.hair_object = scan_for_hair_object(obj)

    # when rebuilding materials remove all the physics modifiers
    # they don't seem to like having their settings changed...
    remove_all_physics_mods(obj)
    if obj.type == "MESH":

        # process any materials found in the mesh object
        for mat in obj.data.materials:
            if mat is not None:
                log_info("Processing Material: " + mat.name)
                process_material(obj, mat)
                if prefs.physics == "ENABLED" and props.physics_mode == "ON":
                    add_material_weight_map(obj, mat, create = False)

        # setup default physics
        if prefs.physics == "ENABLED" and props.physics_mode == "ON":
            add_collision_physics(obj)
            edit_mods, mix_mods = get_weight_map_mods(obj)
            if len(edit_mods) > 0:
                enable_cloth_physics(obj)

    elif obj.type == "ARMATURE":

        # set the frame range of the scene to the active action on the armature
        if obj.animation_data is not None and obj.animation_data.action is not None:
            frame_count = math.ceil(obj.animation_data.action.frame_range[1])
            bpy.context.scene.frame_end = frame_count


def reset_nodes(mat):
    if not mat.use_nodes:
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    links.clear()

    for n in nodes:
        if n.type != "BSDF_PRINCIPLED":
            nodes.remove(n)

    if len(nodes) == 0:
        shader = nodes.new("ShaderNodeBsdfPrincipled")
    else:
        shader = nodes[0]

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location.x += 400

    link_nodes(links, shader, "BSDF", out, "Surface")

def get_material_dir(base_dir, character_name, import_type, obj, mat):
    if import_type == "fbx":
        object_name = strip_name(obj.name)
        mesh_name = strip_name(obj.data.name)
        material_name = strip_name(mat.name)
        if "cc_base_" in object_name.lower():
            path = os.path.join(base_dir, "textures", character_name, character_name, mesh_name, material_name)
            if os.path.exists(path):
                return path
        path = os.path.join(base_dir, "textures", character_name, object_name, mesh_name, material_name)
        if os.path.exists(path):
            return path
        return os.path.join(base_dir, character_name + ".fbm")

    elif import_type == "obj":
        return os.path.join(base_dir, character_name)


def get_object_cache(obj):
    """Returns the object cache for this object.

    Fetches or creates an object cache for the object. Always returns an object cache collection.
    """

    props = bpy.context.scene.CC3ImportProps
    for cache in props.object_cache:
        if cache.object == obj:
            return cache
    cache = props.object_cache.add()
    cache.object = obj
    return cache


def get_material_cache(mat):
    """Returns the material cache for this material.

    Fetches the material cache for the material. Returns None if the material is not in the cache.
    """

    props = bpy.context.scene.CC3ImportProps
    for cache in props.material_cache:
        if cache.material == mat:
            return cache
    return None

def cache_object_materials(obj):
    props = bpy.context.scene.CC3ImportProps
    main_tex_dir = props.import_main_tex_dir
    base_dir, file_name = os.path.split(props.import_file)
    type = file_name[-3:].lower()
    character_name = file_name[:-4]

    if obj is None:
        return

    if obj.type == "MESH":
        for mat in obj.data.materials:
            if mat.node_tree is not None:

                # firstly determine if this obj+mat combination is the hair object
                if props.hair_object is None and is_hair_object(obj, mat):
                    props.hair_object = obj
                    # and if the mat is the scalp material
                    if props.scalp_material is None and is_scalp_material(mat):
                        props.scalp_material = mat

                cache = props.material_cache.add()
                cache.material = mat
                cache.object = obj
                cache.dir = get_material_dir(base_dir, character_name, type, obj, mat)
                nodes = mat.node_tree.nodes
                # weight maps

                for node in nodes:
                    if node.type == "TEX_IMAGE" and node.image is not None:
                        filepath = node.image.filepath
                        dir, name = os.path.split(filepath)
                        # detect incorrent image paths for non packed (not embedded) images and attempt to correct...
                        if node.image.packed_file is None:
                            if os.path.normcase(dir) != os.path.normcase(main_tex_dir):
                                log_warn("Import bug! Wrong image path detected: " + dir)
                                log_warn("    Attempting to correct...")
                                correct_path = os.path.join(main_tex_dir, name)
                                if os.path.exists(correct_path):
                                    log_warn("    Correct image path found: " + correct_path)
                                    node.image.filepath = correct_path
                                else:
                                    correct_path = os.path.join(cache.dir, name)
                                    if os.path.exists(correct_path):
                                        log_warn("    Correct image path found: " + correct_path)
                                        node.image.filepath = correct_path
                                    else:
                                        log_error("    Unable to find correct image!")
                        name = name.lower()
                        socket = get_input_connected_to(node, "Color")
                        # the fbx importer in 2.91 makes a total balls up of the opacity
                        # and connects the alpha output to the socket and not the color output
                        alpha_socket = get_input_connected_to(node, "Alpha")
                        if socket == "Base Color":
                            cache.diffuse = node.image
                        elif socket == "Specular":
                            cache.specular = node.image
                        elif socket == "Alpha" or alpha_socket == "Alpha":
                            cache.alpha = node.image
                            if "diffuse" in name or "albedo" in name:
                                cache.alpha_is_diffuse = True
                        elif socket == "Color":
                            if "bump" in name:
                                cache.bump = node.image
                            else:
                                cache.normal = node.image


def tag_objects():
    for obj in bpy.data.objects:
        obj.tag = True


def untagged_objects():
    untagged = []
    for obj in bpy.data.objects:
        if obj.tag == False:
            untagged.append(obj)
        obj.tag = False
    return untagged

def reconstruct_obj_materials(obj):
    mesh = obj.data
    # remove all materials
    mesh.materials.clear()
    # add new materials
    #  head/body/arm/leg/nails/eyelash/teeth/tongue
    mat_head = bpy.data.materials.new("Std_Skin_Head") #0
    mat_body = bpy.data.materials.new("Std_Skin_Body") #1
    mat_arm = bpy.data.materials.new("Std_Skin_Arm") #2
    mat_leg = bpy.data.materials.new("Std_Skin_Leg") #3
    mat_nails = bpy.data.materials.new("Std_Nails") #4
    mat_eyelash = bpy.data.materials.new("Std_Eyelash") #5
    mat_uteeth= bpy.data.materials.new("Std_Upper_Teeth") #6
    mat_lteeth = bpy.data.materials.new("Std_Lower_Teeth") #7
    mat_tongue = bpy.data.materials.new("Std_Tongue") #8
    mat_reye = bpy.data.materials.new("Std_Eye_R") #9
    mat_leye = bpy.data.materials.new("Std_Eye_L") #10
    mat_rcornea = bpy.data.materials.new("Std_Cornea_R") #11
    mat_lcornea = bpy.data.materials.new("Std_Cornea_L") #12
    mesh.materials.append(mat_head)
    mesh.materials.append(mat_body)
    mesh.materials.append(mat_arm)
    mesh.materials.append(mat_leg)
    mesh.materials.append(mat_nails)
    mesh.materials.append(mat_eyelash)
    mesh.materials.append(mat_uteeth)
    mesh.materials.append(mat_lteeth)
    mesh.materials.append(mat_tongue)
    mesh.materials.append(mat_reye)
    mesh.materials.append(mat_leye)
    mesh.materials.append(mat_rcornea)
    mesh.materials.append(mat_lcornea)
    ul = mesh.uv_layers[0]
    # figure out which polygon belongs to which material from the vertex groups, uv coords and polygon indices
    for poly in mesh.polygons:
        loop_index = poly.loop_indices[0]
        loop_entry = mesh.loops[loop_index]
        vertex = mesh.vertices[loop_entry.vertex_index]
        group = vertex.groups[0].group
        uv = ul.data[loop_entry.index].uv
        x = uv[0]
        if x > 5:
            poly.material_index = 5 # eyelash
        elif x > 4:
            poly.material_index = 4 # nails
        elif x > 3:
            poly.material_index = 3 # legs
        elif x > 2:
            poly.material_index = 2 # arms
        elif x > 1:
            poly.material_index = 1 # body
        else:
            # head/eyes/tongue/teeth
            # vertex groups: 0 - tongue, 1 - body(head), 2 - eye, 3 - teeth
            if group == 0:
                poly.material_index = 8
            elif group == 1:
                poly.material_index = 0
            elif group == 2:
                # assign by polygon index (and hope these stay the same across exports)
                # eye_r: 14342-14501
                # cornea_r: 14502-14661
                # eye_l: 14662-14821
                # cornea_l: 14822-14981
                if poly.index >= 14822:
                    poly.material_index = 12
                elif poly.index >= 14662:
                    poly.material_index = 10
                elif poly.index >= 14502:
                    poly.material_index = 11
                else:
                    poly.material_index = 9
            else: #3
                # upper teeth: 14982-16162
                # lower teeth: 16163-17402
                if poly.index >= 16163:
                    poly.material_index = 7
                else:
                    poly.material_index = 6

def select_all_child_objects(obj):
    if obj.type == "ARMATURE" or obj.type == "MESH":
        obj.select_set(True)
    for child in obj.children:
        select_all_child_objects(child)

class CC3Import(bpy.types.Operator):
    """Import CC3 Character and build materials"""
    bl_idname = "cc3.importer"
    bl_label = "Import"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(
        name="Filepath",
        description="Select the root directory to search for the textures.",
        subtype="FILE_PATH"
        )

    filter_glob: bpy.props.StringProperty(
        default="*.fbx;*.obj",
        options={"HIDDEN"},
        )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    use_anim: bpy.props.BoolProperty(name = "Import Animation", description = "Import animation with character.\nWarning: long animations take a very long time to import in Blender 2.83", default = True)

    running = False
    imported = False
    built = False
    lighting = False
    timer = None
    clock = 0

    def import_character(self):
        props = bpy.context.scene.CC3ImportProps

        import_anim = self.use_anim
        # don't import animation data if importing for morph/accessory
        if self.param == "IMPORT_MORPH":
            import_anim = False
        props.import_file = self.filepath
        dir, name = os.path.split(self.filepath)
        props.import_objects.clear()
        props.material_cache.clear()
        type = name[-3:].lower()
        name = name[:-4]
        props.import_type = type
        props.import_name = name
        props.import_dir = dir
        props.import_space_in_name = " " in name

        if type == "fbx":
            # determine the main texture dir
            props.import_main_tex_dir = os.path.join(dir, name + ".fbm")
            if os.path.exists(props.import_main_tex_dir):
                props.import_embedded = False
            else:
                props.import_main_tex_dir = ""
                props.import_embedded = True

            # invoke the fbx importer
            tag_objects()
            bpy.ops.import_scene.fbx(filepath=self.filepath, directory=dir, use_anim=import_anim)

            # process imported objects
            imported = untagged_objects()
            for obj in imported:
                if obj.type == "ARMATURE":
                    p = props.import_objects.add()
                    p.object = obj
                if obj.type == "MESH":
                    p = props.import_objects.add()
                    p.object = obj
                    cache_object_materials(obj)
            log_info("Done .Fbx Import.")

        elif type == "obj":
            # determine the main texture dir
            props.import_main_tex_dir = os.path.join(dir, name)
            props.import_embedded = False
            if not os.path.exists(props.import_main_tex_dir):
                props.import_main_tex_dir = ""

            # invoke the obj importer
            tag_objects()
            if self.param == "IMPORT_MORPH":
                bpy.ops.import_scene.obj(filepath = self.filepath, split_mode = "OFF",
                        use_split_objects = False, use_split_groups = False,
                        use_groups_as_vgroups = True)
            else:
                bpy.ops.import_scene.obj(filepath = self.filepath, split_mode = "ON",
                        use_split_objects = True, use_split_groups = True,
                        use_groups_as_vgroups = False)

            # process imported objects
            imported = untagged_objects()
            for obj in imported:
                # scale obj import by 1/100
                obj.scale = (0.01, 0.01, 0.01)
                if obj.type == "MESH":
                    p = props.import_objects.add()
                    p.object = obj
                    if self.param == "IMPORT_MORPH":
                        if props.import_main_tex_dir != "":
                            #reconstruct_obj_materials(obj)
                            pass
                    else:
                        cache_object_materials(obj)
            log_info("Done .Obj Import.")

    def build_materials(self):
        objects_processed = []
        props = bpy.context.scene.CC3ImportProps

        check_node_groups()

        if props.build_mode == "IMPORTED":
            for p in props.import_objects:
                if p.object is not None:
                    process_object(p.object, objects_processed)

        elif props.build_mode == "SELECTED":
            for obj in bpy.context.selected_objects:
                process_object(obj, objects_processed)

        log_info("Done Build.")

    def run_import(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = context.preferences.addons[__name__].preferences

        # use basic materials for morph/accessory editing as it has better viewport performance
        if self.param == "IMPORT_MORPH":
            props.setup_mode = prefs.morph_mode
        elif self.param == "IMPORT_ACCESSORY":
            props.setup_mode = prefs.pipeline_mode
        # use advanced materials for quality/rendering
        elif self.param == "IMPORT_QUALITY":
            props.setup_mode = prefs.quality_mode

        self.import_character()

        # check for fbxkey
        if props.import_type == "fbx":
            props.import_key_file = os.path.join(props.import_dir, props.import_name + ".fbxkey")
            props.import_has_key = os.path.exists(props.import_key_file)
            if self.param == "IMPORT_MORPH" and not props.import_has_key:
                message_box("This character export does not have an .fbxkey file, it cannot be used to create character morphs in CC3.", "FBXKey Warning")


        # check for objkey
        if props.import_type == "obj":
            props.import_key_file = os.path.join(props.import_dir, props.import_name + ".ObjKey")
            props.import_has_key = os.path.exists(props.import_key_file)
            if self.param == "IMPORT_MORPH" and not props.import_has_key:
                message_box("This character export does not have an .ObjKey file, it cannot be used to create character morphs in CC3.", "OBJKey Warning")

        self.imported = True

    def run_build(self, context):
        self.build_materials()
        self.built = True

    def run_finish(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = context.preferences.addons[__name__].preferences

        # use the cc3 lighting for morph/accessory editing
        if self.param == "IMPORT_MORPH" or self.param == "IMPORT_ACCESSORY":
            if prefs.lighting == "ENABLED" and props.lighting_mode == "ON":
                if props.import_type == "fbx":
                    setup_scene_default(prefs.pipeline_lighting)
                else:
                    setup_scene_default(prefs.morph_lighting)

            # for any objects with shape keys select basis and enable show in edit mode
            for p in props.import_objects:
                init_character_for_edit(p.object)

        # use portrait lighting for quality mode
        elif self.param == "IMPORT_QUALITY":
            if prefs.lighting == "ENABLED" and props.lighting_mode == "ON":
                setup_scene_default(prefs.quality_lighting)

        zoom_to_character()
        self.lighting = True

    def modal(self, context, event):

        # 60 second timeout
        if event.type == 'TIMER':
            self.clock = self.clock + 1
            if self.clock > 60:
                self.cancel(context)
                self.report({'INFO'}, "Import operator timed out!")
                return {'CANCELLED'}

        if event.type == 'TIMER' and not self.running:
            if not self.imported:
                self.running = True
                self.run_import(context)
                self.clock = 0
                self.running = False
            elif not self.built:
                self.running = True
                self.run_build(context)
                self.clock = 0
                self.running = False
            elif not self.lighting:
                self.running = True
                self.run_finish(context)
                self.clock = 0
                self.running = False

            if self.imported and self.built and self.lighting:
                self.cancel(context)
                self.report({'INFO'}, "All done!")
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def cancel(self, context):
        if self.timer is not None:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = context.preferences.addons[__name__].preferences

        # import character
        if "IMPORT" in self.param:
            if self.timer is None:
                self.imported = False
                self.built = False
                self.lighting = False
                self.running = False
                self.clock = 0
                self.report({'INFO'}, "Importing Character, please wait for import to finish and materials to build...")
                context.window_manager.modal_handler_add(self)
                self.timer = context.window_manager.event_timer_add(1.0, window = context.window)
                return {'PASS_THROUGH'}

        # build materials
        elif self.param == "BUILD":
            self.build_materials()

        # rebuild the node groups for advanced materials
        elif self.param == "REBUILD_NODE_GROUPS":
            rebuild_node_groups()

        elif self.param == "DELETE_CHARACTER":
            delete_character()

        return {"FINISHED"}

    def invoke(self, context, event):
        if "IMPORT" in self.param:
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

        return self.execute(context)

    @classmethod
    def description(cls, context, properties):
        if properties.param == "IMPORT":
            return "Import a new .fbx or .obj character exported by Character Creator 3"
        elif properties.param == "REIMPORT":
            return "Rebuild the materials from the last import with the current settings"
        elif properties.param == "IMPORT_MORPH":
            return "Import .fbx or .obj character from CC3 for morph creation. This does not import any animation data.\n" \
                   "Notes for exporting from CC3:\n" \
                   "1. For best results for morph creation export FBX: 'Mesh Only' or OBJ: Nude Character in Bind Pose, as these guarantee .fbxkey or .objkey generation.\n" \
                   "2. OBJ export 'Nude Character in Bind Pose' .obj does not export any materials.\n" \
                   "3. OBJ export 'Character with Current Pose' does not create an .objkey and cannot be used for morph creation.\n" \
                   "4. FBX export with motion in 'Current Pose' or 'Custom Motion' also does not export an .fbxkey and cannot be used for morph creation"
        elif properties.param == "IMPORT_ACCESSORY":
            return "Import .fbx or .obj character from CC3 for accessory creation. This will import current pose or animation.\n" \
                   "Notes for exporting from CC3:\n" \
                   "1. OBJ or FBX exports in 'Current Pose' are good for accessory creation as they import back into CC3 in exactly the right place"
        elif properties.param == "IMPORT_QUALITY":
            return "Import .fbx or .obj character from CC3 for rendering"
        elif properties.param == "BUILD":
            return "Build (or Rebuild) materials for the current imported character with the current build settings"
        elif properties.param == "DELETE_CHARACTER":
            return "Removes the character and any associated objects, meshes, materials, nodes, images, armature actions and shapekeys. Basically deletes everything not nailed down.\n**Do not press this if there is anything you want to keep!**"
        elif properties.param == "REBUILD_NODE_GROUPS":
            return "Rebuilds the shader node groups for the advanced and eye materials."
        return ""


class CC3Export(bpy.types.Operator):
    """Export CC3 Character"""
    bl_idname = "cc3.exporter"
    bl_label = "Export"
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        maxlen=1024,
        subtype='FILE_PATH',
        )

    filename_ext = ".fbx"  # ExportHelper mixin class uses this

    filter_glob: bpy.props.StringProperty(
        default="*.fbx;*.obj",
        options={"HIDDEN"},
        )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    use_anim: bpy.props.BoolProperty(name = "Export Animation", default = True)


    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps

        if self.param == "EXPORT_MORPH" or self.param == "EXPORT":
            export_anim = self.use_anim and self.param != "EXPORT_MORPH"
            props.import_file = self.filepath
            dir, name = os.path.split(self.filepath)
            type = name[-3:].lower()
            name = name[:-4]

            # store selection
            old_selection = bpy.context.selected_objects
            old_active = bpy.context.active_object

            if type == "fbx":

                # don't bring anything else with a morph export
                if self.param == "EXPORT_MORPH" and props.import_has_key:
                    bpy.ops.object.select_all(action='DESELECT')

                for p in props.import_objects:
                    if p.object is not None:
                        if p.object.type == "ARMATURE":
                            select_all_child_objects(p.object)
                        else:
                            p.object.select_set(True)

                bpy.ops.export_scene.fbx(filepath=self.filepath,
                        use_selection = True,
                        bake_anim = export_anim,
                        add_leaf_bones=False)

                if props.import_has_key:
                    try:
                        key_dir, key_file = os.path.split(props.import_key_file)
                        old_name, key_type = os.path.splitext(key_file)
                        new_key_path = os.path.join(dir, name + key_type)
                        shutil.copyfile(props.import_key_file, new_key_path)
                    except:
                        log_error("Unable to copy keyfile: " + props.import_key_file + " to: " + new_key_path)

            else:

                # don't bring anything else with a morph export
                if self.param == "EXPORT_MORPH" and props.import_has_key:
                    bpy.ops.object.select_all(action='DESELECT')

                # select all the imported objects
                for p in props.import_objects:
                    if p.object is not None and p.object.type == "MESH":
                        p.object.select_set(True)

                if self.param == "EXPORT_MORPH":
                    bpy.ops.export_scene.obj(filepath=self.filepath,
                            use_selection = True,
                            global_scale = 100,
                            use_materials = False,
                            keep_vertex_order = True,
                            use_vertex_groups = True)
                else:
                    bpy.ops.export_scene.obj(filepath=self.filepath,
                            use_selection = True,
                            global_scale = 100,
                            use_materials = True,
                            keep_vertex_order = True,
                            use_vertex_groups = True)

                if props.import_has_key:
                    try:
                        key_dir, key_file = os.path.split(props.import_key_file)
                        old_name, key_type = os.path.splitext(key_file)
                        new_key_path = os.path.join(dir, name + key_type)
                        shutil.copyfile(props.import_key_file, new_key_path)
                    except:
                        log_error("Unable to copy keyfile: " + props.import_key_file + "\n    to: " + new_key_path)

            # restore selection
            #bpy.ops.object.select_all(action='DESELECT')
            #for obj in old_selection:
            #    obj.select_set(True)
            #bpy.context.view_layer.objects.active = old_active

        elif self.param == "EXPORT_ACCESSORY":
            props.import_file = self.filepath
            dir, name = os.path.split(self.filepath)
            type = name[-3:].lower()
            name = name[:-4]

            # store selection
            old_selection = bpy.context.selected_objects
            old_active = bpy.context.active_object

            bpy.ops.export_scene.fbx(filepath=self.filepath,
                        use_selection = True,
                        bake_anim = False,
                        add_leaf_bones=False)

            # restore selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in old_selection:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = old_active


        return {"FINISHED"}

    def invoke(self, context, event):
        self.get_type()

        if self.filename_ext == ".none":
            return {"FINISHED"}

        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if not blend_filepath:
                if self.param == "EXPORT_ACCESSORY":
                    blend_filepath = "accessory"
                else:
                    blend_filepath = "untitled"
            else:
                blend_filepath = os.path.splitext(blend_filepath)[0]
            self.filepath = blend_filepath + self.filename_ext

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def get_type(self):
        props = bpy.context.scene.CC3ImportProps
        # export accessories as the same file type as imported
        if self.param == "EXPORT_ACCESSORY":
            self.filename_ext = "." + props.import_type
        # exporting for pipeline depends on what was imported...
        elif self.param == "EXPORT_MORPH" or self.param == "EXPORT":
            self.filename_ext = "." + props.import_type
        else:
            self.filename_ext = ".none"

    def check(self, context):
        change_ext = False
        filepath = self.filepath
        if os.path.basename(filepath):
            filepath = bpy.path.ensure_ext(filepath, self.filename_ext)
            if filepath != self.filepath:
                self.filepath = filepath
                change_ext = True
        return change_ext

    @classmethod
    def description(cls, context, properties):

        if properties.param == "EXPORT_MORPH":
            return "Export full character to import back into CC3"
        elif properties.param == "EXPORT_ACCESSORY":
            return "Export selected object(s) for import into CC3 as accessories"
        return ""

def add_target(name, location):
    bpy.ops.object.empty_add(type="PLAIN_AXES", radius = 0.1,
        location = location)
    target = bpy.context.active_object
    target.name = name
    return target

def set_contact_shadow(light, distance, thickness):
    light.data.use_contact_shadow = True
    light.data.contact_shadow_distance = distance
    light.data.contact_shadow_thickness = thickness

def track_to(obj, target):
    constraint = obj.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"

def add_spot_light(name, location, rotation, energy, blend, size, distance, radius):
    bpy.ops.object.light_add(type="SPOT",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = name
    light.data.energy = energy
    light.data.shadow_soft_size = radius
    light.data.spot_blend = blend
    light.data.spot_size = size
    light.data.use_custom_distance = True
    light.data.cutoff_distance = distance
    return light

def add_area_light(name, location, rotation, energy, size):
    bpy.ops.object.light_add(type="AREA",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = name
    light.data.shape = "DISK"
    light.data.size = size
    light.data.energy = energy
    return light

def add_point_light(name, location, rotation, energy, size):
    bpy.ops.object.light_add(type="POINT",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = name
    light.data.shadow_soft_size = size
    light.data.energy = energy
    return light

def remove_all_lights(inc_camera = False):
    for obj in bpy.data.objects:
        if obj.type == "LIGHT" and not obj.hide_viewport:
            bpy.data.objects.remove(obj)

        elif inc_camera and obj.type == "EMPTY" and "CameraTarget" in obj.name:
            bpy.data.objects.remove(obj)

        elif obj.type == "EMPTY" and \
            ("KeyTarget" in obj.name or \
             "FillTarget" in obj.name or \
             "BackTarget" in obj.name):
            bpy.data.objects.remove(obj)

        elif inc_camera and obj.type == "CAMERA":
            bpy.data.objects.remove(obj)



def camera_setup(camera_loc, target_loc):
    # find an active camera
    camera = None
    target = None
    for obj in bpy.data.objects:
        if camera is None and obj.type == "CAMERA" and obj.visible_get():
            camera = obj
            camera.location = camera_loc
        if target is None and obj.type == "EMPTY" and obj.visible_get() and "CameraTarget" in obj.name:
            target = obj
            target.location = target_loc
    if camera is None:
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=camera_loc)
        camera = bpy.context.active_object
    if target is None:
        target = add_target("CameraTarget", target_loc)

    track_to(camera, target)
    camera.data.lens = 80
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = target
    camera.data.dof.aperture_fstop = 2.8
    camera.data.dof.aperture_blades = 5
    camera.data.dof.aperture_rotation = 0
    camera.data.dof.aperture_ratio = 1
    camera.data.display_size = 0.2
    camera.data.show_limits = True

    camera_auto_target(camera, target)

    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 2560
    bpy.context.scene.render.resolution_percentage = 100

    return camera, target

def camera_auto_target(camera, target):
    props = bpy.context.scene.CC3ImportProps
    arm = None
    for p in props.import_objects:
        obj = p.object
        if (obj.type == "ARMATURE"):
            arm = obj
            break

    if arm is not None:
        left_eye = find_pose_bone("CC_Base_L_Eye", "L_Eye")
        right_eye = find_pose_bone("CC_Base_R_Eye", "R_Eye")
        head = find_pose_bone("CC_Base_FacialBone", "FacialBone")

        if left_eye is None or right_eye is None or head is None:
            return

        head_location = arm.matrix_world @ head.head
        head_dir = (arm.matrix_world @ head.vector).normalized()
        print(head_dir)
        target_location = arm.matrix_world @ ((left_eye.head + right_eye.head) * 0.5)
        target.location = target_location + head_dir * 0.03
        camera.location = head_location + head_dir * 2

def compositor_setup():
    bpy.context.scene.use_nodes = True
    nodes = bpy.context.scene.node_tree.nodes
    links = bpy.context.scene.node_tree.links
    nodes.clear()
    rlayers_node = make_shader_node(nodes, "CompositorNodeRLayers")
    c_node = make_shader_node(nodes, "CompositorNodeComposite")
    glare_node = make_shader_node(nodes, "CompositorNodeGlare")
    lens_node = make_shader_node(nodes, "CompositorNodeLensdist")
    rlayers_node.location = (-780,260)
    c_node.location = (150,140)
    glare_node.location = (-430,230)
    lens_node.location = (-100,150)
    glare_node.glare_type = 'FOG_GLOW'
    glare_node.quality = 'HIGH'
    glare_node.threshold = 0.85
    lens_node.use_fit = True
    lens_node.inputs["Dispersion"].default_value = 0.025
    link_nodes(links, rlayers_node, "Image", glare_node, "Image")
    link_nodes(links, glare_node, "Image", lens_node, "Image")
    link_nodes(links, lens_node, "Image", c_node, "Image")

def world_setup():
    bpy.context.scene.world.use_nodes = True
    nodes = bpy.context.scene.world.node_tree.nodes
    links = bpy.context.scene.world.node_tree.links
    nodes.clear()
    tc_node = make_shader_node(nodes, "ShaderNodeTexCoord")
    mp_node = make_shader_node(nodes, "ShaderNodeMapping")
    et_node = make_shader_node(nodes, "ShaderNodeTexEnvironment")
    bg_node = make_shader_node(nodes, "ShaderNodeBackground")
    wo_node = make_shader_node(nodes, "ShaderNodeOutputWorld")
    tc_node.location = (-820,350)
    mp_node.location = (-610,370)
    et_node.location = (-300,320)
    bg_node.location = (10,300)
    wo_node.location = (300,300)
    set_node_input(bg_node, "Strength", 0.5)
    link_nodes(links, tc_node, "Generated", mp_node, "Vector")
    link_nodes(links, mp_node, "Vector", et_node, "Vector")
    link_nodes(links, et_node, "Color", bg_node, "Color")
    link_nodes(links, bg_node, "Background", wo_node, "Surface")
    bin_dir, bin_file = os.path.split(bpy.app.binary_path)
    version = bpy.app.version_string[:4]
    hdri_path = os.path.join(bin_dir, version, "datafiles", "studiolights", "world", "forest.exr")
    et_node.image = load_image(hdri_path, "Linear")


def init_character_for_edit(obj):
    #bpy.context.active_object.data.shape_keys.key_blocks['Basis']
    if obj.type == "MESH":
        shape_keys = obj.data.shape_keys
        if shape_keys is not None:
            blocks = shape_keys.key_blocks
            if blocks is not None:
                if len(blocks) > 0:
                    set_shape_key_edit(obj)


def set_shape_key_edit(obj):
    try:
        #current_mode = bpy.context.mode
        #if current_mode != "OBJECT":
        #    bpy.ops.object.mode_set(mode="OBJECT")
        #bpy.context.view_layer.objects.active = object
        obj.active_shape_key_index = 0
        obj.show_only_shape_key = True
        obj.use_shape_key_edit_mode = True
    except:
        log_error("Unable to set shape key edit mode!")


def setup_scene_default(scene_type):
    props = bpy.context.scene.CC3ImportProps

    # store selection and mode
    current_selected = bpy.context.selected_objects
    current_active = bpy.context.active_object
    current_mode = bpy.context.mode
    # go to object mode
    try:
        if current_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        if scene_type == "BLENDER":

            bpy.context.scene.eevee.use_gtao = False
            bpy.context.scene.eevee.gtao_distance = 0.2
            bpy.context.scene.eevee.gtao_factor = 1.0
            bpy.context.scene.eevee.use_bloom = False
            bpy.context.scene.eevee.bloom_threshold = 0.8
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 6.5
            bpy.context.scene.eevee.bloom_intensity = 0.05
            bpy.context.scene.eevee.use_ssr = False
            bpy.context.scene.eevee.use_ssr_refraction = False
            bpy.context.scene.eevee.bokeh_max_size = 32
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "None"
            bpy.context.scene.view_settings.exposure = 0.0
            bpy.context.scene.view_settings.gamma = 1.0

            remove_all_lights(True)

            key1 = add_point_light("Light",
                    (4.076245307922363, 1.0054539442062378, 5.903861999511719),
                    (0.6503279805183411, 0.055217113345861435, 1.8663908243179321),
                    1000, 0.1)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'forest.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 0
            bpy.context.space_data.shading.studiolight_intensity = 1
            bpy.context.space_data.shading.studiolight_background_alpha = 0
            bpy.context.space_data.shading.studiolight_background_blur = 0
            bpy.context.space_data.clip_start = 0.1

        elif scene_type == "MATCAP":

            remove_all_lights(True)

            bpy.context.space_data.shading.type = 'SOLID'
            bpy.context.space_data.shading.light = 'MATCAP'
            bpy.context.space_data.shading.studio_light = 'basic_1.exr'
            bpy.context.space_data.shading.show_cavity = True

        elif scene_type == "CC3":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 2.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "Medium Contrast"
            bpy.context.scene.view_settings.exposure = 0.5
            bpy.context.scene.view_settings.gamma = 0.5

            remove_all_lights(True)

            key1 = add_spot_light("Key1",
                    (0.71149, -1.49019, 2.04134),
                    (1.2280241250991821, 0.4846124053001404, 0.3449903726577759),
                    100, 0.5, 2.095, 9.7, 0.25)

            key2 = add_spot_light("Key2",
                    (0.63999, -1.3600, 0.1199),
                    (1.8845493793487549, 0.50091552734375, 0.6768553256988525),
                    100, 0.5, 2.095, 9.7, 0.25)

            back = add_spot_light("Back",
                    (0.0, 2.0199, 1.69),
                    (-1.3045594692230225, 0.11467886716127396, 0.03684665635228157),
                    100, 0.5, 1.448, 9.14, 0.25)

            #set_contact_shadow(key1, 0.1, 0.001)
            #set_contact_shadow(key2, 0.1, 0.005)

            bpy.context.space_data.shading.type = 'SOLID'
            bpy.context.space_data.shading.light = 'MATCAP'
            bpy.context.space_data.shading.studio_light = 'basic_1.exr'
            bpy.context.space_data.shading.show_cavity = True
            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'studio.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 0
            bpy.context.space_data.shading.studiolight_intensity = 0.75
            bpy.context.space_data.shading.studiolight_background_alpha = 0
            bpy.context.space_data.shading.studiolight_background_blur = 0
            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "STUDIO":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 2.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "High Contrast"
            bpy.context.scene.view_settings.exposure = 0.5
            bpy.context.scene.view_settings.gamma = 1.0

            remove_all_lights(True)

            key = add_spot_light("Key",
                    (0.3088499903678894, -4.569439888000488, 2.574970006942749),
                    (0.39095374941825867, 1.3875367641448975, -1.1152653694152832),
                    400, 0.75, 0.75, 7.5, 0.4)

            right = add_area_light("Right",
                    (2.067525863647461, 0.8794340491294861, 1.1529420614242554),
                    (3.115412712097168, 1.7226399183273315, 9.79827880859375),
                    50, 2)

            back = add_spot_light("Ear",
                    (0.6740000247955322, 1.906999945640564, 1.6950000524520874),
                    (-0.03316125646233559, 1.3578661680221558, 1.1833332777023315),
                    100, 1, 1.0996, 9.1, 0.5)

            set_contact_shadow(key, 0.1, 0.01)
            set_contact_shadow(right, 0.1, 0.01)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'studio.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 0.0
            bpy.context.space_data.shading.studiolight_intensity = 0.2
            bpy.context.space_data.shading.studiolight_background_alpha = 0.5
            bpy.context.space_data.shading.studiolight_background_blur = 0.5
            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "COURTYARD":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 2.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "Medium High Contrast"
            bpy.context.scene.view_settings.exposure = 0.5
            bpy.context.scene.view_settings.gamma = 0.6

            remove_all_lights(True)

            key = add_area_light("Key",
                    (-1.5078026056289673, -1.0891118049621582, 2.208820104598999),
                    (1.0848181247711182, -0.881056010723114, -0.5597077012062073),
                    40, 2)

            fill = add_area_light("Fill",
                    (2.28589, -1.51410, 1.40742),
                    (1.4248263835906982, 0.9756063222885132, 0.8594209551811218),
                    20, 2)

            back = add_area_light("Back",
                    (0.36789, 0.61511, 2.36201),
                    (-0.7961875796318054, 0.4831638038158417, -0.12343151122331619),
                    20, 1)

            set_contact_shadow(key, 0.1, 0.01)
            set_contact_shadow(fill, 0.1, 0.01)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'courtyard.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 2.00713
            bpy.context.space_data.shading.studiolight_intensity = 0.35
            bpy.context.space_data.shading.studiolight_background_alpha = 0.5
            bpy.context.space_data.shading.studiolight_background_blur = 0.5

            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "TEMPLATE":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.5
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 5.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "Medium High Contrast"
            bpy.context.scene.view_settings.exposure = 0.6
            bpy.context.scene.view_settings.gamma = 0.6

            remove_all_lights()
            camera_setup((0.1, -0.75, 1.6), (0, 0, 1.5))

            key = add_area_light("Key",
                    (-1.5078026056289673, -1.0891118049621582, 2.208820104598999),
                    (1.0848181247711182, -0.881056010723114, -0.5597077012062073),
                    40, 1)
            target_key = add_target("KeyTarget", (-0.006276353262364864, -0.004782751202583313, 1.503425121307373))
            track_to(key, target_key)

            fill = add_area_light("Fill",
                    (2.28589, -1.51410, 1.40742),
                    (1.4248263835906982, 0.9756063222885132, 0.8594209551811218),
                    10, 1)
            target_fill = add_target("FillTarget", (0.013503191992640495, 0.005856933072209358, 1.1814184188842773))
            track_to(fill, target_fill)

            back = add_area_light("Back",
                    (0.36789, 0.61511, 2.36201),
                    (-0.7961875796318054, 0.4831638038158417, -0.12343151122331619),
                    40, 0.5)
            target_back = add_target("BackTarget", (0.0032256320118904114, 0.06994983553886414, 1.6254671812057495))
            track_to(back, target_back)

            set_contact_shadow(key, 0.1, 0.01)
            set_contact_shadow(fill, 0.1, 0.01)

            bpy.context.space_data.shading.type = 'RENDERED'
            bpy.context.space_data.shading.use_scene_lights_render = True
            bpy.context.space_data.shading.use_scene_world_render = True

            bpy.context.space_data.clip_start = 0.01

    except Exception as e:
        print(e)
    except:
        log_error("Something went wrong adding lights... wrong editor context?")

    # restore selection
    bpy.ops.object.select_all(action='DESELECT')
    for obj in current_selected:
        try:
            obj.select_set(True)
        except:
            pass
    try:
        bpy.context.view_layer.objects.active = current_active
        if current_mode != "OBJECT":
            bpy.ops.object.mode_set(mode=current_mode)
    except:
        pass

# zoom view to imported character
def zoom_to_character():
    props = bpy.context.scene.CC3ImportProps
    try:
        bpy.ops.object.select_all(action='DESELECT')
        for p in props.import_objects:
            p.object.select_set(True)
        bpy.ops.view3d.view_selected()
    except:
        pass

class CC3Scene(bpy.types.Operator):
    """Scene Tools"""
    bl_idname = "cc3.scene"
    bl_label = "Scene Tools"
    bl_options = {"REGISTER", "UNDO"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):
        if self.param == "RENDER_IMAGE":
            render_image(context)
        elif self.param == "RENDER_ANIMATION":
            render_animation(context)
        elif self.param == "ANIM_RANGE":
            fetch_anim_range(context)
        elif self.param == "PHYSICS_PREP":
            prepare_physics_bake(context)
        else:
            setup_scene_default(self.param)
            if (self.param == "TEMPLATE"):
                compositor_setup()
                world_setup()
                message_box("World nodes and compositor template set up.")
        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "BLENDER":
            return "Restore the render settings and lighting to the Blender defaults"
        elif properties.param == "MATCAP":
            return "Use solid shading with matcap rendering"
        elif properties.param == "CC3":
            return "Use material shading with render settings and lighting to a replica of the default CC3 lighting"
        elif properties.param == "STUDIO":
            return "Use rendered shading with the Studio HDRI and left sided 3 point lighting"
        elif properties.param == "COURTYARD":
            return "Use rendered shading with the Courtyard HDRI and right sided 3 point lighting"
        elif properties.param == "TEMPLATE":
            return "Sets up a rendering template with rendered shading and world lighting. Sets up the Compositor and World nodes with a basic setup and adds tracking lights, a tracking camera and targetting objects"
        elif properties.param == "RENDER_IMAGE":
            return "Renders a single image"
        elif properties.param == "RENDER_ANIMATION":
            return "Renders the current animation range"
        elif properties.param == "ANIM_RANGE":
            return "Sets the animation range to the same range as the Action on the current character"
        elif properties.param == "PHYSICS_PREP":
            return "Sets all the physics bake ranges to the same as the current scene animation range."

        return ""

def context_material(context):
    try:
        return context.object.material_slots[context.object.active_material_index].material
    except:
        return None

def quick_set_fix(param, obj, context, objects_processed):
    props = bpy.context.scene.CC3ImportProps
    ob = context.object

    if obj is not None and obj not in objects_processed:
        if obj.type == "MESH":
            objects_processed.append(obj)

            if props.quick_set_mode == "OBJECT":
                for mat in obj.data.materials:
                    if param == "OPAQUE" or param == "BLEND" or param == "HASHED":
                        apply_alpha_override(obj, mat, param)
                    elif param == "SINGLE_SIDED":
                        apply_backface_culling(obj, mat, 1)
                    elif param == "DOUBLE_SIDED":
                        apply_backface_culling(obj, mat, 2)

            elif ob is not None and ob.active_material_index <= len(ob.data.materials):
                mat = context_material(context)
                if param == "OPAQUE" or param == "BLEND" or param == "HASHED":
                    apply_alpha_override(obj, mat, param)
                elif param == "SINGLE_SIDED":
                    apply_backface_culling(obj, mat, 1)
                elif param == "DOUBLE_SIDED":
                    apply_backface_culling(obj, mat, 2)

        elif obj.type == "ARMATURE":
            for child in obj.children:
                quick_set_fix(param, child, context, objects_processed)

def quick_set_params(param, obj, context, objects_processed):
    props = bpy.context.scene.CC3ImportProps
    ob = context.object

    if obj is not None and obj not in objects_processed:
        if obj.type == "MESH":
            objects_processed.append(obj)

            for mat in obj.data.materials:
                refresh_parameters(mat)

def quick_set_execute(param, context = bpy.context):
    objects_processed = []
    props = bpy.context.scene.CC3ImportProps

    if "PHYSICS_" in param:

        if param == "PHYSICS_ADD_CLOTH":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    enable_cloth_physics(obj)
        elif param == "PHYSICS_REMOVE_CLOTH":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    disable_cloth_physics(obj)
        elif param == "PHYSICS_ADD_COLLISION":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    enable_collision_physics(obj)
        elif param == "PHYSICS_REMOVE_COLLISION":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    disable_collision_physics(obj)
        elif param == "PHYSICS_ADD_WEIGHTMAP":
            if context.object is not None and context.object.type == "MESH":
                enable_material_weight_map(context.object, context_material(context))
        elif param == "PHYSICS_REMOVE_WEIGHTMAP":
            if context.object is not None and context.object.type == "MESH":
                disable_material_weight_map(context.object, context_material(context))
        elif param == "PHYSICS_HAIR":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "HAIR")
        elif param == "PHYSICS_COTTON":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "COTTON")
        elif param == "PHYSICS_DENIM":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "DENIM")
        elif param == "PHYSICS_LEATHER":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "LEATHER")
        elif param == "PHYSICS_RUBBER":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "RUBBER")
        elif param == "PHYSICS_SILK":
            for obj in bpy.context.selected_objects:
                if obj.type == "MESH":
                    apply_cloth_settings(obj, "SILK")
        elif param == "PHYSICS_PAINT":
            if context.object is not None and context.object.type == "MESH":
                begin_paint_weight_map(context)
        elif param == "PHYSICS_DONE_PAINTING":
            end_paint_weight_map()
        elif param == "PHYSICS_SAVE":
            save_dirty_weight_maps(bpy.context.selected_objects)
        elif param == "PHYSICS_DELETE":
            delete_selected_weight_map(context.object, context_material(context))
        elif param == "PHYSICS_SEPARATE":
            separate_physics_materials(context)
        elif param == "PHYSICS_FIX_DEGENERATE":
            if context.object is not None:
                if bpy.context.object.mode != "EDIT" and bpy.context.object.mode != "OBJECT":
                    bpy.ops.object.mode_set(mode = 'OBJECT')
                if bpy.context.object.mode != "EDIT":
                    bpy.ops.object.mode_set(mode = 'EDIT')
                if bpy.context.object.mode == "EDIT":
                    bpy.ops.mesh.select_all(action = 'SELECT')
                    bpy.ops.mesh.dissolve_degenerate()
                bpy.ops.object.mode_set(mode = 'OBJECT')

    elif param == "RESET":
        reset_parameters(context)

    elif param == "RESET_PREFS":
        reset_preferences()

    elif param == "UPDATE_ALL":
        for p in props.import_objects:
            if p.object is not None:
                quick_set_params(param, p.object, context, objects_processed)

    elif param == "UPDATE_SELECTED":
        for obj in bpy.context.selected_objects:
            quick_set_params(param, obj, context, objects_processed)

    else: # blend modes or single/double sided...
        if props.quick_set_mode == "OBJECT":
            for obj in bpy.context.selected_objects:
                quick_set_fix(param, obj, context, objects_processed)
        else:
            quick_set_fix(param, context.object, context, objects_processed)

block_update = False

def quick_set_update(self, context):
    global block_update
    if not block_update:
        quick_set_execute("UPDATE_ALL", context)

def find_pose_bone(*name):
    props = bpy.context.scene.CC3ImportProps

    for p in props.import_objects:
        obj = p.object
        if (obj.type == "ARMATURE"):
            for n in name:
                if n in obj.pose.bones:
                    return obj.pose.bones[n]
    return None

def open_mouth_update(self, context):
    props = bpy.context.scene.CC3ImportProps

    bone = find_pose_bone("CC_Base_JawRoot", "JawRoot")
    if bone is not None:
        constraint = None

        for con in bone.constraints:
            if "iCC3_open_mouth_contraint" in con.name:
                constraint = con

        if props.open_mouth == 0:
            if constraint is not None:
                constraint.influence = props.open_mouth
                bone.constraints.remove(constraint)
        else:
            if constraint is None:
                constraint = bone.constraints.new(type="LIMIT_ROTATION")
                constraint.name = "iCC3_open_mouth_contraint"
                constraint.use_limit_z = True
                constraint.min_z = 0.43633
                constraint.max_z = 0.43633
                constraint.owner_space = "LOCAL"
            constraint.influence = props.open_mouth

def s2lin(x):
    a = 0.055
    if x <= 0.04045:
        y = x * (1.0/12.92)
    else:
        y = pow((x + a)*(1.0/(1 + a)), 2.4)
    return y

def lin2s(x):
    a = 0.055
    if x <= 0.0031308:
        y = x * 12.92
    else:
        y = (1 + a)*pow(x, 1/2.4) - a
    return y

def physics_paint_strength_update(self, context):
    props = bpy.context.scene.CC3ImportProps

    if bpy.context.mode == "PAINT_TEXTURE":
        ups = context.tool_settings.unified_paint_settings
        prop_owner = ups if ups.use_unified_color else context.tool_settings.image_paint.brush
        s = props.physics_paint_strength
        prop_owner.color = (s, s, s)

def weight_strength_update(self, context):
    props = bpy.context.scene.CC3ImportProps

    strength = props.weight_map_strength
    influence = 1 - math.pow(1 - strength, 3)
    edit_mod, mix_mod = get_material_weight_map_mods(context.object, context_material(context))
    mix_mod.mask_constant = influence


class CC3QuickSet(bpy.types.Operator):
    """Quick Set Functions"""
    bl_idname = "cc3.quickset"
    bl_label = "Quick Set Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):

        quick_set_execute(self.param, context)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "UPDATE_ALL":
            return "Update all objects from the last import, with the current parameters"
        elif properties.param == "UPDATE_SELECTED":
            return "Update the currently selected objects, with the current parameters"
        elif properties.param == "OPAQUE":
            return "Set blend mode of all selected objects with alpha channels to opaque"
        elif properties.param == "BLEND":
            return "Set blend mode of all selected objects with alpha channels to alpha blend"
        elif properties.param == "HASHED":
            return "Set blend mode of all selected objects with alpha channels to alpha hashed"
        elif properties.param == "FETCH":
            return "Fetch the parameters from the selected objects"
        elif properties.param == "RESET":
            return "Reset parameters to the defaults"
        elif properties.param == "SINGLE_SIDED":
            return "Set material to be single sided, only visible from front facing"
        elif properties.param == "DOUBLE_SIDED":
            return "Set material to be double sided, visible from both sides"

        elif properties.param == "PHYSICS_ADD_CLOTH":
            return "Add Cloth physics to the selected objects."
        elif properties.param == "PHYSICS_REMOVE_CLOTH":
            return "Remove Cloth physics from the selected objects and remove all weight map modifiers and physics vertex groups"
        elif properties.param == "PHYSICS_ADD_COLLISION":
            return "Add Collision physics to the selected objects"
        elif properties.param == "PHYSICS_REMOVE_COLLISION":
            return "Remove Collision physics from the selected objects"
        elif properties.param == "PHYSICS_ADD_WEIGHTMAP":
            return "Add a physics weight map to the material on the current object. " \
                   "If there is no existing weight map, a new blank weight map will be created. " \
                   "Modifiers to generate the physics vertex groups will be added to the object"
        elif properties.param == "PHYSICS_REMOVE_WEIGHTMAP":
            return "Removes the physics weight map, modifiers and physics vertex groups for this material from the object"
        elif properties.param == "PHYSICS_HAIR":
            return "Sets the cloth physics settings for this object to simulate Hair.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_COTTON":
            return "Sets the cloth physics settings for this object to simulate Cotton.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_DENIM":
            return "Sets the cloth physics settings for this object to simulate Denim.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_LEATHER":
            return "Sets the cloth physics settings for this object to simulate Leather.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_RUBBER":
            return "Sets the cloth physics settings for this object to simulate Rubber.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_SILK":
            return "Sets the cloth physics settings for this object to simulate Silk.\n" \
                   "Note: These settings are pure guess work and largely untested"
        elif properties.param == "PHYSICS_PAINT":
            return "Switches to texture paint mode and begins painting the current materials PhysX weight map"
        elif properties.param == "PHYSICS_DONE_PAINTING":
            return "Ends painting and returns to Object mode"
        elif properties.param == "PHYSICS_SAVE":
            return "Saves all changes to the weight maps to the source texture files\n" \
                   "**Warning: This will overwrite the existing weightmap files if you have altered them!**"
        elif properties.param == "PHYSICS_DELETE":
            return "Removes the weight map, modifiers and physics vertex groups from the objects, " \
                   "and then deletes the weight map texture file.\n" \
                   "**Warning: This will delete any existing weightmap file for this object and material!**"
        elif properties.param == "PHYSICS_SEPARATE":
            return "Separates the object by material and applies physics to the separated objects that have weight maps.\n" \
                   "Note: Some objects with many verteces and materials but only a small amount is cloth simulated " \
                   "may see performance benefits from being separated."
        elif properties.param == "PHYSICS_FIX_DEGENERATE":
            return "Removes degenerate mesh elements from the object.\n" \
                   "Note: Meshes with degenerate elements, loose verteces, orphaned edges, zero length edges etc...\n" \
                   "might not simulate properly. If the mesh misbehaves badly under simulation, try this."

        return ""


def set_node_from_property(node):

    props = bpy.context.scene.CC3ImportProps
    name = node.name

    # BASE COLOR
    #
    if "(color_" in name and "_mixer)" in name:
        # color_skin_<part>_mixer
        if "_skin_" in name:
            set_node_input(node, "AO Strength", props.skin_ao)
            set_node_input(node, "Blend Strength", props.skin_blend)
            set_node_input(node, "Mouth AO", props.skin_mouth_ao)
            set_node_input(node, "Nostril AO", props.skin_nostril_ao)
            set_node_input(node, "Lips AO", props.skin_lips_ao)
        # color_eye_mixer
        elif "_eye_" in name:
            set_node_input(node, "AO Strength", props.eye_ao)
            set_node_input(node, "Blend Strength", props.eye_blend)
            set_node_input(node, "Shadow Radius", props.eye_shadow_radius)
            set_node_input(node, "Shadow Hardness", props.eye_shadow_hardness * props.eye_shadow_radius * 0.99)
            set_node_input(node, "Corner Shadow", props.eye_shadow_color)
            set_node_input(node, "Sclera Brightness", props.eye_sclera_brightness)
            set_node_input(node, "Iris Brightness", props.eye_iris_brightness)
        # color_hair_mixer
        elif "_hair_" in name or "_scalp_" in name:
            set_node_input(node, "AO Strength", props.hair_ao)
            set_node_input(node, "Blend Strength", props.hair_blend)
        # color_teeth_mixer
        elif "_teeth_" in name:
            set_node_input(node, "AO Strength", props.teeth_ao)
            set_node_input(node, "Front", props.teeth_front)
            set_node_input(node, "Rear", props.teeth_rear)
            set_node_input(node, "Teeth Brightness", props.teeth_teeth_brightness)
            set_node_input(node, "Teeth Saturation", 1 - props.teeth_teeth_desaturation)
            set_node_input(node, "Gums Brightness", props.teeth_gums_brightness)
            set_node_input(node, "Gums Saturation", 1 - props.teeth_gums_desaturation)
        # color_tongue_mixer
        elif "_tongue_" in name:
            set_node_input(node, "AO Strength", props.tongue_ao)
            set_node_input(node, "Front", props.tongue_front)
            set_node_input(node, "Rear", props.tongue_rear)
            set_node_input(node, "Brightness", props.tongue_brightness)
            set_node_input(node, "Saturation", 1 - props.tongue_desaturation)
        # color_nails_mixer
        elif "_nails_" in name:
            set_node_input(node, "AO Strength", props.nails_ao)
        # color_default_mixer
        elif "_default_" in name:
            set_node_input(node, "AO Strength", props.default_ao)
            set_node_input(node, "Blend Strength", props.default_blend)


    # SUBSURFACE
    #
    elif "(subsurface_" in name and "_mixer)" in name:
        # subsurface_skin_<part>_mixer
        if "_skin_" in name:
            set_node_input(node, "Radius", props.skin_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff", props.skin_sss_falloff)
        # subsurface_eye_mixer
        elif "_eye_" in name:
            set_node_input(node, "Radius1", props.eye_sss_radius * UNIT_SCALE)
            set_node_input(node, "Radius2", props.eye_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff1", props.eye_sss_falloff)
            set_node_input(node, "Falloff2", props.eye_sss_falloff)
        # subsurface_hair_mixer
        elif "_hair_" in name or "_scalp_" in name:
            set_node_input(node, "Radius", props.hair_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff", props.hair_sss_falloff)
        # subsurface_teeth_mixer
        elif "_teeth_" in name:
            set_node_input(node, "Radius1", props.teeth_sss_radius * UNIT_SCALE)
            set_node_input(node, "Radius2", props.teeth_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff1", props.teeth_sss_falloff)
            set_node_input(node, "Falloff2", props.teeth_sss_falloff)
            set_node_input(node, "Scatter1", props.teeth_gums_sss_scatter)
            set_node_input(node, "Scatter2", props.teeth_teeth_sss_scatter)
        # subsurface_tongue_mixer
        elif "_tongue_" in name:
            set_node_input(node, "Scatter", props.tongue_sss_scatter)
            set_node_input(node, "Radius", props.tongue_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff", props.tongue_sss_falloff)
        # subsurface_nails_mixer
        elif "_nails_" in name:
            set_node_input(node, "Radius", props.nails_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff", props.nails_sss_falloff)
        # subsurface_default_mixer
        elif "_default_" in name:
            set_node_input(node, "Radius", props.default_sss_radius * UNIT_SCALE)
            set_node_input(node, "Falloff", props.default_sss_falloff)


    # MSR
    #
    elif "(msr_" in name and "_mixer)" in name:
        # msr_skin_<part>_mixer
        if "_skin_" in name:
            set_node_input(node, "Roughness Remap", props.skin_roughness)
            set_node_input(node, "Specular", props.skin_specular)
        # msr_eye_mixer
        elif "_eye_" in name:
            set_node_input(node, "Specular1", props.eye_specular)
            set_node_input(node, "Specular2", props.eye_specular)
            set_node_input(node, "Roughness1", props.eye_sclera_roughness)
            set_node_input(node, "Roughness2", props.eye_iris_roughness)
        # msr_hair_mixer
        elif "_hair_" in name:
            set_node_input(node, "Roughness Remap", props.hair_roughness)
            set_node_input(node, "Specular", props.hair_specular)
        # msr_scalp_mixer
        elif "_scalp_" in name:
            set_node_input(node, "Roughness Remap", props.hair_scalp_roughness)
            set_node_input(node, "Specular", props.hair_scalp_specular)
        # msr_teeth_mixer
        elif "_teeth_" in name:
            set_node_input(node, "Specular2", props.teeth_specular)
        # msr_tongue_mixer
        elif "_tongue_" in name:
            set_node_input(node, "Specular2", props.tongue_specular)
        # msr_nails_mixer
        elif "_nails_" in name:
            set_node_input(node, "Roughness Remap", props.nails_roughness)
            set_node_input(node, "Specular", props.nails_specular)
        elif "_default_" in name:
            set_node_input(node, "Roughness Remap", props.default_roughness)

    elif "teeth_roughness" in name:
        set_node_input(node, 1, props.teeth_roughness)
    elif "tongue_roughness" in name:
        set_node_input(node, 1, props.tongue_roughness)

    # NORMAL
    #
    elif "(normal_" in name and "_mixer)" in name:
        # normal_skin_<part>_mixer
        if "skin_head" in name:
            set_node_input(node, "Normal Blend Strength", props.skin_normal_blend)
            set_node_input(node, "Micro Normal Strength", props.skin_head_micronormal)
        elif "skin_body" in name:
            set_node_input(node, "Normal Blend Strength", props.skin_normal_blend)
            set_node_input(node, "Micro Normal Strength", props.skin_body_micronormal)
        elif "skin_arm" in name:
            set_node_input(node, "Normal Blend Strength", props.skin_normal_blend)
            set_node_input(node, "Micro Normal Strength", props.skin_arm_micronormal)
        elif "skin_leg" in name:
            set_node_input(node, "Normal Blend Strength", props.skin_normal_blend)
            set_node_input(node, "Micro Normal Strength", props.skin_leg_micronormal)
        # normal_eye_mixer
        elif "_eye_" in name:
            set_node_input(node, "Micro Normal Strength", 1 - props.eye_sclera_normal)
        # normal_hair_mixer
        elif "_hair_" in name or "_scalp_" in name:
            set_node_input(node, "Bump Map Height", props.hair_bump / 1000)
        # normal_teeth_mixer
        elif "_teeth_" in name:
            set_node_input(node, "Micro Normal Strength", props.teeth_micronormal)
        # normal_tongue_mixer
        elif "_tongue_" in name:
            set_node_input(node, "Micro Normal Strength", props.tongue_micronormal)
        # normal_nails_mixer
        elif "_nails_" in name:
            set_node_input(node, "Micro Normal Strength", props.nails_micronormal)
        # normal_default_mixer
        elif "_default_" in name:
            set_node_input(node, "Normal Blend Strength", props.default_normal_blend)
            set_node_input(node, "Micro Normal Strength", props.default_micronormal)
            set_node_input(node, "Bump Map Height", props.default_bump / 1000)

    # TILING
    #
    elif "(tiling_" in name and "_mapping)" in name:
        # tiling_skin_<part>_mapping
        if "skin_head" in name:
            set_node_input(node, "Tiling", props.skin_head_tiling)
        elif "skin_body" in name:
            set_node_input(node, "Tiling", props.skin_body_tiling)
        elif "skin_arm" in name:
            set_node_input(node, "Tiling", props.skin_arm_tiling)
        elif "skin_leg" in name:
            set_node_input(node, "Tiling", props.skin_leg_tiling)
        # tiling_sclera_normal_mapping
        elif "_normal_sclera_" in name:
            set_node_input(node, "Tiling", props.eye_sclera_tiling)
        # tiling_sclera_color_mapping
        elif "_color_sclera_" in name:
            set_node_input(node, "Tiling", 1.0 / props.eye_sclera_scale)
        # tiling_teeth_mapping
        elif "_teeth_" in name:
            set_node_input(node, "Tiling", props.teeth_tiling)
        # tiling_tongue_mapping
        elif "_tongue_" in name:
            set_node_input(node, "Tiling", props.tongue_tiling)
        # tiling_nails_mapping
        elif "_nails_" in name:
            set_node_input(node, "Tiling", props.nails_tiling)
        # tiling_default_mapping
        elif "_default_" in name:
            set_node_input(node, "Tiling", props.default_tiling)

    # MASKS
    #
    elif "iris_mask" in name:
        set_node_input(node, "Scale", 1.0 / props.eye_iris_scale)
        set_node_input(node, "Radius", props.eye_iris_radius)
        set_node_input(node, "Hardness", props.eye_iris_radius * props.eye_iris_hardness * 0.99)
    elif "eye_occlusion_mask" in name:
        set_node_input(node, "Strength", props.eye_occlusion)

    # BASIC
    #
    elif "skin_ao" in name:
        set_node_output(node, "Value", props.skin_ao)
    elif "skin_basic_specular" in name:
        set_node_output(node, "Value", props.skin_basic_specular)
    elif "skin_basic_roughness" in name:
        set_node_input(node, "To Min", props.skin_basic_roughness)
    elif "eye_specular" in name:
        set_node_output(node, "Value", props.eye_specular)
    elif "teeth_specular" in name:
        set_node_output(node, "Value", props.teeth_specular)
    elif "teeth_roughess" in name:
        set_node_input(node, 1, props.teeth_roughness)
    elif "tongue_specular" in name:
        set_node_output(node, "Value", props.tongue_specular)
    elif "nails_specular" in name:
        set_node_output(node, "Value", props.nails_specular)
    elif "eye_basic_roughness" in name:
        set_node_output(node, "Value", props.eye_basic_roughness)
    elif "eye_basic_normal" in name:
        set_node_output(node, "Value", props.eye_basic_normal)
    elif "eye_basic_hsv" in name:
        set_node_input(node, "Value", props.eye_basic_brightness)
    elif "hair_ao" in name:
        set_node_output(node, "Value", props.hair_ao)
    elif "hair_specular" in name:
        set_node_output(node, "Value", props.hair_specular)
    elif "scalp_specular" in name:
        set_node_output(node, "Value", props.hair_scalp_specular)
    elif "hair_bump" in name:
        set_node_output(node, "Value", props.hair_bump / 1000)
    elif "default_ao" in name:
        set_node_output(node, "Value", props.default_ao)
    elif "default_bump" in name:
        set_node_output(node, "Value", props.default_bump / 1000)

    # Other
    elif "eye_tearline_shader" in name:
        set_node_input(node, "Alpha", props.eye_tearline_alpha)
        set_node_input(node, "Roughness", props.eye_tearline_roughness)


def refresh_parameters(mat):

    if (mat.node_tree is None):
        log_warn("No node tree!")
        return

    for node in mat.node_tree.nodes:

        if NODE_PREFIX in node.name:
            set_node_from_property(node)

def reset_preferences():
    prefs = bpy.context.preferences.addons[__name__].preferences
    prefs.lighting = "ENABLED"
    prefs.physics = "ENABLED"
    prefs.quality_lighting = "STUDIO"
    prefs.pipeline_lighting = "CC3"
    prefs.morph_lighting = "MATCAP"
    prefs.quality_mode = "ADVANCED"
    prefs.pipeline_mode = "BASIC"
    prefs.morph_mode = "COMPAT"
    prefs.log_level = "ERRORS"

def reset_parameters(context = bpy.context):
    global block_update
    props = bpy.context.scene.CC3ImportProps

    block_update = True

    props.skin_ao = 1.0
    props.skin_blend = 0.0
    props.skin_normal_blend = 0.0
    props.skin_roughness = 0.15
    props.skin_specular = 0.4
    props.skin_basic_specular = 0.4
    props.skin_basic_roughness = 0.15
    props.skin_sss_radius = 1.5
    props.skin_sss_falloff = (1.0, 0.112, 0.072, 1.0)
    props.skin_head_micronormal = 0.5
    props.skin_body_micronormal = 0.8
    props.skin_arm_micronormal = 1.0
    props.skin_leg_micronormal = 1.0
    props.skin_head_tiling = 25
    props.skin_body_tiling = 20
    props.skin_arm_tiling = 20
    props.skin_leg_tiling = 20
    props.skin_mouth_ao = 2.5
    props.skin_nostril_ao = 2.5
    props.skin_lips_ao = 2.5

    props.eye_ao = 0.2
    props.eye_blend = 0.0
    props.eye_specular = 0.8
    props.eye_sclera_roughness = 0.2
    props.eye_iris_roughness = 0.0
    props.eye_iris_scale = 1.0
    props.eye_sclera_scale = 1.0
    props.eye_iris_radius = 0.13
    props.eye_iris_hardness = 0.85
    props.eye_sss_radius = 1.0
    props.eye_sss_falloff = (1.0, 1.0, 1.0, 1.0)
    props.eye_sclera_normal = 0.9
    props.eye_sclera_tiling = 2.0
    props.eye_basic_roughness = 0.05
    props.eye_basic_normal = 0.1
    props.eye_shadow_radius = 0.3
    props.eye_shadow_hardness = 0.5
    props.eye_shadow_color = (1.0, 0.497, 0.445, 1.0)
    props.eye_occlusion = 0.5
    props.eye_sclera_brightness = 0.75
    props.eye_iris_brightness = 1.0
    props.eye_basic_brightness = 0.9
    props.eye_tearline_alpha = 0.05
    props.eye_tearline_roughness = 0.15

    props.teeth_ao = 1.0
    props.teeth_gums_brightness = 0.9
    props.teeth_teeth_brightness = 0.7
    props.teeth_gums_desaturation = 0.0
    props.teeth_teeth_desaturation = 0.1
    props.teeth_front = 1.0
    props.teeth_rear = 0.0
    props.teeth_specular = 0.25
    props.teeth_roughness = 0.4
    props.teeth_gums_sss_scatter = 1.0
    props.teeth_teeth_sss_scatter = 0.5
    props.teeth_sss_radius = 1.0
    props.teeth_sss_falloff = (0.381, 0.198, 0.13, 1.0)
    props.teeth_micronormal = 0.3
    props.teeth_tiling = 10

    props.tongue_ao = 1.0
    props.tongue_brightness = 1.0
    props.tongue_desaturation = 0.05
    props.tongue_front = 1.0
    props.tongue_rear = 0.0
    props.tongue_specular = 0.259
    props.tongue_roughness = 1.0
    props.tongue_sss_scatter = 1.0
    props.tongue_sss_radius = 1.0
    props.tongue_sss_falloff = (1,1,1, 1.0)
    props.tongue_micronormal = 0.5
    props.tongue_tiling = 4

    props.nails_ao = 1.0
    props.nails_specular = 0.4
    props.nails_roughness = 0.0
    props.nails_sss_radius = 1.5
    props.nails_sss_falloff = (1.0, 0.112, 0.072, 1.0)
    props.nails_micronormal = 1.0
    props.nails_tiling = 42

    props.hair_ao = 1.0
    props.hair_blend = 0.0
    props.hair_specular = 0.5
    props.hair_roughness = 0.0
    props.hair_scalp_specular = 0.0
    props.hair_scalp_roughness = 0.0
    props.hair_sss_radius = 1.0
    props.hair_sss_falloff = (1.0, 1.0, 1.0, 1.0)
    props.hair_bump = 1

    props.default_ao = 1.0
    props.default_blend = 0.0
    props.default_roughness = 0.0
    props.default_normal_blend = 0.0
    props.default_sss_radius = 1.0
    props.default_sss_falloff = (1.0, 1.0, 1.0, 1.0)

    props.default_micronormal = 0.5
    props.default_tiling = 10
    props.default_bump = 5

    block_update = False
    quick_set_execute("UPDATE_ALL", context)

    return


class CC3ObjectPointer(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)


class CC3MaterialCache(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(type=bpy.types.Material)
    compat: bpy.props.PointerProperty(type=bpy.types.Material)
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    dir: bpy.props.StringProperty(default="")
    diffuse: bpy.props.PointerProperty(type=bpy.types.Image)
    normal: bpy.props.PointerProperty(type=bpy.types.Image)
    bump: bpy.props.PointerProperty(type=bpy.types.Image)
    alpha: bpy.props.PointerProperty(type=bpy.types.Image)
    specular: bpy.props.PointerProperty(type=bpy.types.Image)
    temp_weight_map: bpy.props.PointerProperty(type=bpy.types.Image)
    alpha_is_diffuse: bpy.props.BoolProperty(default=False)
    alpha_mode: bpy.props.StringProperty(default="NONE") # NONE, BLEND, HASHED, OPAQUE
    culling_sides: bpy.props.IntProperty(default=0) # 0 - default, 1 - single sided, 2 - double sided
    cloth_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON


class CC3ObjectCache(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    collision_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON
    cloth_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON
    cloth_settings: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, HAIR, COTTON, DENIM, LEATHER, RUBBER, SILK


class CC3ImportProps(bpy.types.PropertyGroup):

    node_id: bpy.props.IntProperty(default=1000)

    setup_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic","Build basic PBR materials."),
                        ("ADVANCED","Advanced","Build advanced materials with blend maps, subsurface, and micro normals, specular and roughness control and includes layered eye, teeth and tongue materials.")
                    ], default="BASIC")

    build_mode: bpy.props.EnumProperty(items=[
                        ("IMPORTED","All Imported","Build materials for all the imported objects."),
                        ("SELECTED","Only Selected","Build materials only for the selected objects.")
                    ], default="IMPORTED")

    blend_mode: bpy.props.EnumProperty(items=[
                        ("BLEND","Alpha Blend","Setup any non opaque materials as basic Alpha Blend"),
                        ("HASHED","Alpha Hashed","Setup non opaque materials as alpha hashed (Resolves Z sorting issues, but may need more samples)")
                    ], default="BLEND")

    update_mode: bpy.props.EnumProperty(items=[
                        ("UPDATE_ALL","All Imported","Update the shader parameters for all objects from the last import"),
                        ("UPDATE_SELECTED","Selected Only","Update the shader parameters only in the selected objects")
                    ], default="UPDATE_ALL")

    open_mouth: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=open_mouth_update)
    physics_paint_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=physics_paint_strength_update)
    weight_map_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=weight_strength_update)
    physics_tex_size: bpy.props.EnumProperty(items=[
                        ("64","64 x 64","64 x 64 texture size"),
                        ("128","128 x 128","128 x 128 texture size"),
                        ("256","256 x 256","256 x 256 texture size"),
                        ("512","512 x 512","512 x 512 texture size"),
                        ("1024","1024 x 1024","1024 x 1024 texture size"),
                        ("2048","2048 x 2048","2048 x 2048 texture size"),
                        ("4096","4096 x 4096","4096 x 4096 texture size"),
                    ], default="1024")

    import_file: bpy.props.StringProperty(default="", subtype="FILE_PATH")
    import_objects: bpy.props.CollectionProperty(type=CC3ObjectPointer)
    material_cache: bpy.props.CollectionProperty(type=CC3MaterialCache)
    object_cache: bpy.props.CollectionProperty(type=CC3ObjectCache)
    import_type: bpy.props.StringProperty(default="")
    import_name: bpy.props.StringProperty(default="")
    import_dir: bpy.props.StringProperty(default="")
    import_embedded: bpy.props.BoolProperty(default=False)
    import_main_tex_dir: bpy.props.StringProperty(default="")
    import_space_in_name: bpy.props.BoolProperty(default=False)
    import_has_key: bpy.props.BoolProperty(default=False)
    import_key_file: bpy.props.StringProperty(default="")

    paint_object: bpy.props.PointerProperty(type=bpy.types.Object)
    paint_material: bpy.props.PointerProperty(type=bpy.types.Material)
    paint_image: bpy.props.PointerProperty(type=bpy.types.Image)
    paint_store_render: bpy.props.StringProperty(default="")

    quick_set_mode: bpy.props.EnumProperty(items=[
                        ("OBJECT","Object","Set the alpha blend mode and backface culling to all materials on the selected object(s)"),
                        ("MATERIAL","Material","Set the alpha blend mode and backface culling only to the selected material on the active object"),
                    ], default="MATERIAL")

    lighting_mode: bpy.props.EnumProperty(items=[
                        ("OFF","No Lighting","No automatic lighting and render settings."),
                        ("ON","Lighting","Automatically sets lighting and render settings, depending on use."),
                    ], default="OFF")
    physics_mode: bpy.props.EnumProperty(items=[
                        ("OFF","No Physics","No generated physics."),
                        ("ON","Physics","Automatically generates physics vertex groups and settings."),
                    ], default="OFF")

    stage1: bpy.props.BoolProperty(default=True)
    stage1_details: bpy.props.BoolProperty(default=False)
    stage2: bpy.props.BoolProperty(default=True)
    stage3: bpy.props.BoolProperty(default=True)
    stage4: bpy.props.BoolProperty(default=True)
    stage5: bpy.props.BoolProperty(default=True)
    stage6: bpy.props.BoolProperty(default=True)

    skin_basic_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    skin_basic_roughness: bpy.props.FloatProperty(default=0.15, min=0, max=1, update=quick_set_update)
    eye_basic_roughness: bpy.props.FloatProperty(default=0.05, min=0, max=1, update=quick_set_update)
    eye_basic_normal: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=quick_set_update)
    eye_basic_brightness: bpy.props.FloatProperty(default=0.9, min=0, max=2, update=quick_set_update)

    skin_toggle: bpy.props.BoolProperty(default=True)
    skin_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    skin_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    skin_normal_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    skin_roughness: bpy.props.FloatProperty(default=0.15, min=0, max=1, update=quick_set_update)
    skin_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    skin_sss_radius: bpy.props.FloatProperty(default=1.5, min=0.1, max=5, update=quick_set_update)
    skin_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 0.112, 0.072, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    skin_head_micronormal: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    skin_body_micronormal: bpy.props.FloatProperty(default=0.8, min=0, max=1, update=quick_set_update)
    skin_arm_micronormal: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    skin_leg_micronormal: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    skin_head_tiling: bpy.props.FloatProperty(default=25, min=0, max=50, update=quick_set_update)
    skin_body_tiling: bpy.props.FloatProperty(default=20, min=0, max=50, update=quick_set_update)
    skin_arm_tiling: bpy.props.FloatProperty(default=20, min=0, max=50, update=quick_set_update)
    skin_leg_tiling: bpy.props.FloatProperty(default=20, min=0, max=50, update=quick_set_update)
    skin_mouth_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=quick_set_update)
    skin_nostril_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=quick_set_update)
    skin_lips_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=quick_set_update)


    eye_toggle: bpy.props.BoolProperty(default=True)
    eye_ao: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=quick_set_update)
    eye_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    eye_specular: bpy.props.FloatProperty(default=0.8, min=0, max=2, update=quick_set_update)
    eye_sclera_roughness: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=quick_set_update)
    eye_iris_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    eye_iris_scale: bpy.props.FloatProperty(default=1.0, min=0.5, max=1.5, update=quick_set_update)
    eye_iris_radius: bpy.props.FloatProperty(default=0.13, min=0.1, max=0.15, update=quick_set_update)
    eye_iris_hardness: bpy.props.FloatProperty(default=0.85, min=0, max=1, update=quick_set_update)
    eye_sclera_scale: bpy.props.FloatProperty(default=1.0, min=0.5, max=1.5, update=quick_set_update)
    eye_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=quick_set_update)
    eye_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    eye_sclera_normal: bpy.props.FloatProperty(default=0.9, min=0, max=1, update=quick_set_update)
    eye_sclera_tiling: bpy.props.FloatProperty(default=2.0, min=0, max=10, update=quick_set_update)
    eye_shadow_hardness: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    eye_shadow_radius: bpy.props.FloatProperty(default=0.3, min=0, max=0.5, update=quick_set_update)
    eye_shadow_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 0.497, 0.445, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    eye_occlusion: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    eye_sclera_brightness: bpy.props.FloatProperty(default=0.75, min=0, max=5, update=quick_set_update)
    eye_iris_brightness: bpy.props.FloatProperty(default=1.0, min=0, max=5, update=quick_set_update)

    eye_tearline_alpha: bpy.props.FloatProperty(default=0.05, min=0, max=0.2, update=quick_set_update)
    eye_tearline_roughness: bpy.props.FloatProperty(default=0.15, min=0, max=0.5, update=quick_set_update)

    teeth_toggle: bpy.props.BoolProperty(default=True)
    teeth_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    teeth_gums_brightness: bpy.props.FloatProperty(default=0.9, min=0, max=2, update=quick_set_update)
    teeth_teeth_brightness: bpy.props.FloatProperty(default=0.7, min=0, max=2, update=quick_set_update)
    teeth_gums_desaturation: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    teeth_teeth_desaturation: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=quick_set_update)
    teeth_front: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    teeth_rear: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    teeth_specular: bpy.props.FloatProperty(default=0.25, min=0, max=2, update=quick_set_update)
    teeth_roughness: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    teeth_gums_sss_scatter: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=quick_set_update)
    teeth_teeth_sss_scatter: bpy.props.FloatProperty(default=0.5, min=0, max=2, update=quick_set_update)
    teeth_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=quick_set_update)
    teeth_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(0.381, 0.198, 0.13, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    teeth_micronormal: bpy.props.FloatProperty(default=0.3, min=0, max=1, update=quick_set_update)
    teeth_tiling: bpy.props.FloatProperty(default=10, min=0, max=50, update=quick_set_update)

    tongue_toggle: bpy.props.BoolProperty(default=True)
    tongue_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    tongue_brightness: bpy.props.FloatProperty(default=1, min=0, max=2, update=quick_set_update)
    tongue_desaturation: bpy.props.FloatProperty(default=0.05, min=0, max=1, update=quick_set_update)
    tongue_front: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    tongue_rear: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    tongue_specular: bpy.props.FloatProperty(default=0.259, min=0, max=2, update=quick_set_update)
    tongue_roughness: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=quick_set_update)
    tongue_sss_scatter: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=quick_set_update)
    tongue_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=quick_set_update)
    tongue_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(1, 1, 1, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    tongue_micronormal: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    tongue_tiling: bpy.props.FloatProperty(default=4, min=0, max=50, update=quick_set_update)

    nails_toggle: bpy.props.BoolProperty(default=True)
    nails_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    nails_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    nails_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    nails_sss_radius: bpy.props.FloatProperty(default=1.5, min=0.1, max=3, update=quick_set_update)
    nails_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(1.0, 0.112, 0.072, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    nails_micronormal: bpy.props.FloatProperty(default=1, min=0, max=1, update=quick_set_update)
    nails_tiling: bpy.props.FloatProperty(default=42, min=0, max=50, update=quick_set_update)

    hair_toggle: bpy.props.BoolProperty(default=True)
    hair_hint: bpy.props.StringProperty(default="hair,beard", update=quick_set_update)
    hair_object: bpy.props.PointerProperty(type=bpy.types.Object, update=quick_set_update)
    scalp_material: bpy.props.PointerProperty(type=bpy.types.Material)
    hair_scalp_hint: bpy.props.StringProperty(default="scalp,base", update=quick_set_update)
    hair_specular: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    hair_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_scalp_specular: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_scalp_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    hair_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    hair_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=quick_set_update)
    hair_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    hair_bump: bpy.props.FloatProperty(default=1, min=0, max=10, update=quick_set_update)

    default_toggle: bpy.props.BoolProperty(default=True)
    default_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    default_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    default_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    default_normal_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    default_sss_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=3, update=quick_set_update)
    default_sss_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=quick_set_update)
    default_micronormal: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    default_tiling: bpy.props.FloatProperty(default=10, min=0, max=100, update=quick_set_update)
    default_bump: bpy.props.FloatProperty(default=5, min=0, max=10, update=quick_set_update)


def fake_drop_down(row, label, prop_name, prop_bool_value):
    props = bpy.context.scene.CC3ImportProps
    if prop_bool_value:
        row.prop(props, prop_name, icon="TRIA_DOWN", icon_only=True, emboss=False)
    else:
        row.prop(props, prop_name, icon="TRIA_RIGHT", icon_only=True, emboss=False)
    row.label(text=label)
    return prop_bool_value


class CC3ToolsMaterialSettingsPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Material_Settings_Panel"
    bl_label = "Materials & Build Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        props = bpy.context.scene.CC3ImportProps
        prefs = context.preferences.addons[__name__].preferences
        mesh_in_selection = False
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                mesh_in_selection = True
                break

        box = layout.box()
        #op = box.operator("cc3.importer", icon="IMPORT", text="Import Character")
        #op.param ="IMPORT"
        # import details
        if props.import_file != "" or len(props.import_objects) > 0:
            box.label(text="Name: " + props.import_name)
            box.label(text="Type: " + props.import_type.upper())
            if props.import_has_key:
                box.label(text="Key File: Yes")
            else:
                box.label(text="Key File: No")

            split = layout.split(factor=0.05)
            col_1 = split.column()
            col_2 = split.column()
            box = col_2.box()
            if fake_drop_down(box.row(), "Import Details", "stage1_details", props.stage1_details):
                if props.import_file != "":
                    box.prop(props, "import_file", text="")
                if len(props.import_objects) > 0:
                    for p in props.import_objects:
                        if p.object is not None:
                            box.prop(p, "object", text="")
        else:
            box.label(text="No Character")

        # Build Settings
        layout.box().label(text="1. Build Settings", icon="MOD_BUILD")
        layout.prop(props, "setup_mode", expand=True)
        layout.prop(props, "blend_mode", expand=True)
        layout.prop(props, "build_mode", expand=True)
        layout.separator()
        split = layout.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text="Hair Hint")
        col_2.prop(props, "hair_hint", text="")
        col_1.label(text="Scalp Hint")
        col_2.prop(props, "hair_scalp_hint", text="")
        if props.hair_object is None:
            col_1.label(text="** Hair Object **")
        else:
            col_1.label(text="Hair Object")
        col_2.prop_search(props, "hair_object",  context.scene, "objects", text="")
        if context.object is not None and context.object.type == "MESH":
            col_1.label(text="Scalp Material")
            col_2.prop_search(props, "scalp_material",  context.object.data, "materials", text="")
        else:
            col_1.label(text="Scalp Material")
            col_2.prop(props, "scalp_material", text="")
        col_1.separator()
        col_2.separator()
        if props.import_file != "":
            box = layout.box()
            if props.setup_mode == "ADVANCED":
                op = box.operator("cc3.importer", icon="SHADING_TEXTURE", text="Build Advanced Materials")
            else:
                op = box.operator("cc3.importer", icon="NODE_MATERIAL", text="Build Basic Materials")
            op.param ="BUILD"

        # Material Setup
        layout.box().label(text="2. Material Setup", icon="MATERIAL")
        column = layout.column()
        if not mesh_in_selection:
            column.enabled = False
        ob = context.object
        if ob is not None:
            column.template_list("MATERIAL_UL_weightedmatslots", "", ob, "material_slots", ob, "active_material_index", rows=1)
        split = column.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text="Quick Set To:")
        col_1.prop(props, "quick_set_mode", expand=True)
        op = col_2.operator("cc3.quickset", icon="SHADING_SOLID", text="Opaque")
        op.param = "OPAQUE"
        op = col_2.operator("cc3.quickset", icon="SHADING_WIRE", text="Blend")
        op.param = "BLEND"
        op = col_2.operator("cc3.quickset", icon="SHADING_RENDERED", text="Hashed")
        op.param = "HASHED"
        col_1.separator()
        col_2.separator()
        op = col_1.operator("cc3.quickset", icon="NORMALS_FACE", text="Single Sided")
        op.param = "SINGLE_SIDED"
        op = col_2.operator("cc3.quickset", icon="XRAY", text="Double Sided")
        op.param = "DOUBLE_SIDED"

        # Parameters
        if fake_drop_down(layout.box().row(),
                "3. Adjust Parameters",
                "stage4",
                props.stage4):
            column = layout.column()
            if props.import_name == "":
                column.enabled = False

            row = column.row()
            row.prop(props, "update_mode", expand=True)
            if props.setup_mode == "ADVANCED":
                # Skin Settings
                column.separator()
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                if props.update_mode == "UPDATE_ALL":
                    col_1.label(text="Update All")
                else:
                    col_1.label(text="Update Selected")
                op = col_2.operator("cc3.quickset", icon="FILE_REFRESH", text="Update")
                op.param = props.update_mode
                column.separator()
                if fake_drop_down(column.row(),
                        "Skin Parameters",
                        "skin_toggle",
                        props.skin_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Skin AO")
                    col_2.prop(props, "skin_ao", text="", slider=True)
                    col_1.label(text="Skin Color Blend")
                    col_2.prop(props, "skin_blend", text="", slider=True)
                    col_1.label(text="Skin Normal Blend")
                    col_2.prop(props, "skin_normal_blend", text="", slider=True)
                    col_1.label(text="*Skin Roughness")
                    col_2.prop(props, "skin_roughness", text="", slider=True)
                    col_1.label(text="Skin Specular")
                    col_2.prop(props, "skin_specular", text="", slider=True)
                    col_1.label(text="Skin SSS Radius")
                    col_2.prop(props, "skin_sss_radius", text="", slider=True)
                    col_1.label(text="Skin SSS Faloff")
                    col_2.prop(props, "skin_sss_falloff", text="")
                    col_1.label(text="Head Micro Normal")
                    col_2.prop(props, "skin_head_micronormal", text="", slider=True)
                    col_1.label(text="Body Micro Normal")
                    col_2.prop(props, "skin_body_micronormal", text="", slider=True)
                    col_1.label(text="Arm Micro Normal")
                    col_2.prop(props, "skin_arm_micronormal", text="", slider=True)
                    col_1.label(text="Leg Micro Normal")
                    col_2.prop(props, "skin_leg_micronormal", text="", slider=True)
                    col_1.label(text="Head MNormal Tiling")
                    col_2.prop(props, "skin_head_tiling", text="", slider=True)
                    col_1.label(text="Body MNormal Tiling")
                    col_2.prop(props, "skin_body_tiling", text="", slider=True)
                    col_1.label(text="Arm MNormal Tiling")
                    col_2.prop(props, "skin_arm_tiling", text="", slider=True)
                    col_1.label(text="Leg MNormal Tiling")
                    col_2.prop(props, "skin_leg_tiling", text="", slider=True)
                    col_1.label(text="Mouth AO")
                    col_2.prop(props, "skin_mouth_ao", text="", slider=True)
                    col_1.label(text="Nostril AO")
                    col_2.prop(props, "skin_nostril_ao", text="", slider=True)
                    col_1.label(text="Lips AO")
                    col_2.prop(props, "skin_lips_ao", text="", slider=True)

                # Eye settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Eye Parameters",
                        "eye_toggle",
                        props.eye_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Eye AO")
                    col_2.prop(props, "eye_ao", text="", slider=True)
                    col_1.label(text="Eye Color Blend")
                    col_2.prop(props, "eye_blend", text="", slider=True)
                    col_1.label(text="Eye Specular")
                    col_2.prop(props, "eye_specular", text="", slider=True)
                    col_1.label(text="Iris Roughness")
                    col_2.prop(props, "eye_iris_roughness", text="", slider=True)
                    col_1.label(text="Sclera Roughness")
                    col_2.prop(props, "eye_sclera_roughness", text="", slider=True)
                    col_1.label(text="Iris Scale")
                    col_2.prop(props, "eye_iris_scale", text="", slider=True)
                    col_1.label(text="Sclera Scale")
                    col_2.prop(props, "eye_sclera_scale", text="", slider=True)
                    col_1.label(text="*Iris Mask Radius")
                    col_2.prop(props, "eye_iris_radius", text="", slider=True)
                    col_1.label(text="*Iris Mask Hardness")
                    col_2.prop(props, "eye_iris_hardness", text="", slider=True)
                    col_1.label(text="SS Radius (cm)")
                    col_2.prop(props, "eye_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Faloff")
                    col_2.prop(props, "eye_sss_falloff", text="")
                    col_1.label(text="Sclera Normal Flatten")
                    col_2.prop(props, "eye_sclera_normal", text="", slider=True)
                    col_1.label(text="Sclera Normal Tiling")
                    col_2.prop(props, "eye_sclera_tiling", text="", slider=True)
                    col_1.label(text="Shadow Radius")
                    col_2.prop(props, "eye_shadow_radius", text="", slider=True)
                    col_1.label(text="Shadow Hardness")
                    col_2.prop(props, "eye_shadow_hardness", text="", slider=True)
                    col_1.label(text="Shadow Color")
                    col_2.prop(props, "eye_shadow_color", text="")
                    col_1.label(text="Eye Occlusion")
                    col_2.prop(props, "eye_occlusion", text="", slider=True)
                    col_1.label(text="*Tearline Alpha")
                    col_2.prop(props, "eye_tearline_alpha", text="", slider=True)
                    col_1.label(text="*Tearline Roughness")
                    col_2.prop(props, "eye_tearline_roughness", text="", slider=True)
                    col_1.label(text="Sclera Brightness")
                    col_2.prop(props, "eye_sclera_brightness", text="", slider=True)
                    col_1.label(text="Iris Brightness")
                    col_2.prop(props, "eye_iris_brightness", text="", slider=True)

                # Teeth settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Teeth Parameters",
                        "teeth_toggle",
                        props.teeth_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Teeth AO")
                    col_2.prop(props, "teeth_ao", text="", slider=True)
                    col_1.label(text="Teeth Specular")
                    col_2.prop(props, "teeth_specular", text="", slider=True)
                    col_1.label(text="Gums Brightness")
                    col_2.prop(props, "teeth_gums_brightness", text="", slider=True)
                    col_1.label(text="Gums Desaturation")
                    col_2.prop(props, "teeth_gums_desaturation", text="", slider=True)
                    col_1.label(text="Teeth Brightness")
                    col_2.prop(props, "teeth_teeth_brightness", text="", slider=True)
                    col_1.label(text="Teeth Desaturation")
                    col_2.prop(props, "teeth_teeth_desaturation", text="", slider=True)
                    col_1.label(text="Front AO")
                    col_2.prop(props, "teeth_front", text="", slider=True)
                    col_1.label(text="Rear AO")
                    col_2.prop(props, "teeth_rear", text="", slider=True)
                    col_1.label(text="Teeth Roughness")
                    col_2.prop(props, "teeth_roughness", text="", slider=True)
                    col_1.label(text="Gums SSS Scatter")
                    col_2.prop(props, "teeth_gums_sss_scatter", text="", slider=True)
                    col_1.label(text="Teeth SSS Scatter")
                    col_2.prop(props, "teeth_teeth_sss_scatter", text="", slider=True)
                    col_1.label(text="SSS Radius (cm)")
                    col_2.prop(props, "teeth_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Falloff")
                    col_2.prop(props, "teeth_sss_falloff", text="", slider=True)
                    col_1.label(text="Micro Normal")
                    col_2.prop(props, "teeth_micronormal", text="", slider=True)
                    col_1.label(text="Micro Normal Tiling")
                    col_2.prop(props, "teeth_tiling", text="", slider=True)

                # Tongue settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Tongue Parameters",
                        "tongue_toggle",
                        props.tongue_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Tongue AO")
                    col_2.prop(props, "tongue_ao", text="", slider=True)
                    col_1.label(text="Tongue Specular")
                    col_2.prop(props, "tongue_specular", text="", slider=True)
                    col_1.label(text="Tongue Brightness")
                    col_2.prop(props, "tongue_brightness", text="", slider=True)
                    col_1.label(text="Tongue Desaturation")
                    col_2.prop(props, "tongue_desaturation", text="", slider=True)
                    col_1.label(text="Front AO")
                    col_2.prop(props, "tongue_front", text="", slider=True)
                    col_1.label(text="Rear AO")
                    col_2.prop(props, "tongue_rear", text="", slider=True)
                    col_1.label(text="Tongue Roughness")
                    col_2.prop(props, "tongue_roughness", text="", slider=True)
                    col_1.label(text="SSS Scatter")
                    col_2.prop(props, "tongue_sss_scatter", text="", slider=True)
                    col_1.label(text="SSS Radius (cm)")
                    col_2.prop(props, "tongue_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Falloff")
                    col_2.prop(props, "tongue_sss_falloff", text="", slider=True)
                    col_1.label(text="Micro Normal")
                    col_2.prop(props, "tongue_micronormal", text="", slider=True)
                    col_1.label(text="Micro Normal Tiling")
                    col_2.prop(props, "tongue_tiling", text="", slider=True)

                # Nails settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Nails Parameters",
                        "nails_toggle",
                        props.nails_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Nails AO")
                    col_2.prop(props, "nails_ao", text="", slider=True)
                    col_1.label(text="Nails Specular")
                    col_2.prop(props, "nails_specular", text="", slider=True)
                    col_1.label(text="*Nails Roughness")
                    col_2.prop(props, "nails_roughness", text="", slider=True)
                    col_1.label(text="SSS Radius (cm)")
                    col_2.prop(props, "nails_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Falloff")
                    col_2.prop(props, "nails_sss_falloff", text="", slider=True)
                    col_1.label(text="Micro Normal")
                    col_2.prop(props, "nails_micronormal", text="", slider=True)
                    col_1.label(text="Micro Normal Tiling")
                    col_2.prop(props, "nails_tiling", text="", slider=True)


                # Hair settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Hair Parameters",
                        "hair_toggle",
                        props.hair_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Hair AO")
                    col_2.prop(props, "hair_ao", text="", slider=True)
                    col_1.label(text="*Hair Specular")
                    col_2.prop(props, "hair_specular", text="", slider=True)
                    col_1.label(text="*Hair Roughness")
                    col_2.prop(props, "hair_roughness", text="", slider=True)
                    col_1.label(text="*Scalp Specular")
                    col_2.prop(props, "hair_scalp_specular", text="", slider=True)
                    col_1.label(text="*Scalp Roughness")
                    col_2.prop(props, "hair_scalp_roughness", text="", slider=True)
                    col_1.label(text="SSS Radius (cm)")
                    col_2.prop(props, "hair_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Falloff")
                    col_2.prop(props, "hair_sss_falloff", text="")
                    col_1.label(text="*Bump Height (mm)")
                    col_2.prop(props, "hair_bump", text="", slider=True)

                # Defauls settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Default Parameters",
                        "default_toggle",
                        props.default_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Default AO")
                    col_2.prop(props, "default_ao", text="", slider=True)
                    col_1.label(text="Default Color Blend")
                    col_2.prop(props, "default_blend", text="", slider=True)
                    col_1.label(text="*Default Roughness")
                    col_2.prop(props, "default_roughness", text="", slider=True)
                    col_1.label(text="SSS Radius (cm)")
                    col_2.prop(props, "default_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Falloff")
                    col_2.prop(props, "default_sss_falloff", text="")
                    col_1.label(text="Micro Normal")
                    col_2.prop(props, "default_micronormal", text="", slider=True)
                    col_1.label(text="Micro Normal Tiling")
                    col_2.prop(props, "default_tiling", text="", slider=True)
                    col_1.label(text="*Bump Height (mm)")
                    col_2.prop(props, "default_bump", text="", slider=True)
            else:
                column.separator()
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Parameters")
                op = col_2.operator("cc3.quickset", icon="FILE_REFRESH", text="Update")
                op.param = props.update_mode
                column.separator()
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Skin AO")
                col_2.prop(props, "skin_ao", text="", slider=True)
                col_1.label(text="Skin Specular")
                col_2.prop(props, "skin_basic_specular", text="", slider=True)
                col_1.label(text="Skin Roughness")
                col_2.prop(props, "skin_basic_roughness", text="", slider=True)
                col_1.label(text="Eye Specular")
                col_2.prop(props, "eye_specular", text="", slider=True)
                col_1.label(text="Eye Roughness")
                col_2.prop(props, "eye_basic_roughness", text="", slider=True)
                col_1.label(text="Eye Normal")
                col_2.prop(props, "eye_basic_normal", text="", slider=True)
                col_1.label(text="Eye Occlusion")
                col_2.prop(props, "eye_occlusion", text="", slider=True)
                col_1.label(text="Eye Brightness")
                col_2.prop(props, "eye_basic_brightness", text="", slider=True)
                col_1.label(text="Teeth Specular")
                col_2.prop(props, "teeth_specular", text="", slider=True)
                col_1.label(text="Teeth Roughness")
                col_2.prop(props, "teeth_roughness", text="", slider=True)
                col_1.label(text="Tongue Specular")
                col_2.prop(props, "tongue_specular", text="", slider=True)
                col_1.label(text="Tongue Roughness")
                col_2.prop(props, "tongue_roughness", text="", slider=True)
                col_1.label(text="Nails Specular")
                col_2.prop(props, "nails_specular", text="", slider=True)
                col_1.label(text="Hair AO")
                col_2.prop(props, "hair_ao", text="", slider=True)
                col_1.label(text="Hair Specular")
                col_2.prop(props, "hair_specular", text="", slider=True)
                col_1.label(text="Scalp Specular")
                col_2.prop(props, "hair_scalp_specular", text="", slider=True)
                col_1.label(text="Hair Bump Height (mm)")
                col_2.prop(props, "hair_bump", text="", slider=True)
                col_1.label(text="Default AO")
                col_2.prop(props, "default_ao", text="", slider=True)
                col_1.label(text="Default Bump Height (mm)")
                col_2.prop(props, "default_bump", text="", slider=True)

        layout.box().label(text="4. Utilities", icon="MODIFIER_DATA")
        column = layout.column()
        if props.import_name == "":
            column.enabled = False
        split = column.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text="Open Mouth")
        col_2.prop(props, "open_mouth", text="", slider=True)

        column = layout.column()
        op = column.operator("cc3.quickset", icon="DECORATE_OVERRIDE", text="Reset Parameters")
        op.param = "RESET"
        op = column.operator("cc3.importer", icon="MOD_BUILD", text="Rebuild Node Groups")
        op.param ="REBUILD_NODE_GROUPS"

class CC3ToolsScenePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Scene_Panel"
    bl_label = "Scene Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = context.preferences.addons[__name__].preferences
        layout = self.layout

        box = layout.box()
        box.label(text="Scene Lighting", icon="LIGHT")
        col = layout.column()

        op = col.operator("cc3.scene", icon="SHADING_SOLID", text="Solid Matcap")
        op.param = "MATCAP"

        op = col.operator("cc3.scene", icon="SHADING_TEXTURE", text="Blender Default")
        op.param = "BLENDER"
        op = col.operator("cc3.scene", icon="SHADING_TEXTURE", text="CC3 Default")
        op.param = "CC3"

        op = col.operator("cc3.scene", icon="SHADING_RENDERED", text="Studio Right")
        op.param = "STUDIO"
        op = col.operator("cc3.scene", icon="SHADING_RENDERED", text="Courtyard Left")
        op.param = "COURTYARD"

        box = layout.box()
        box.label(text="Scene, World & Compositor", icon="NODE_COMPOSITING")
        col = layout.column()

        op = col.operator("cc3.scene", icon="TRACKING", text="3 Point Tracking & Camera")
        op.param = "TEMPLATE"

        box = layout.box()
        box.label(text="Animation", icon="RENDER_ANIMATION")
        col = layout.column()
        scene = context.scene
        #op = col.operator("cc3.scene", icon="RENDER_STILL", text="Render Image")
        #op.param = "RENDER_IMAGE"
        #op = col.operator("cc3.scene", icon="RENDER_ANIMATION", text="Render Animation")
        #op.param = "RENDER_ANIMATION"
        split = layout.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.prop(scene, "frame_start", text="Start")
        col_2.prop(scene, "frame_end", text="End")
        col = layout.column()
        col.separator()
        op = col.operator("cc3.scene", icon="ARROW_LEFTRIGHT", text="Range From Character")
        op.param = "ANIM_RANGE"
        op = col.operator("cc3.scene", icon="ANIM", text="Sync Physics Range")
        op.param = "PHYSICS_PREP"
        col.separator()
        split = col.split(factor=0.)
        col_1 = split.column()
        col_2 = split.column()
        col_3 = split.column()
        if not context.screen.is_animation_playing:
            #op = col_1.operator("screen.animation_manager", icon="PLAY", text="Play")
            #op.mode = "PLAY"
            col_1.operator("screen.animation_play", text="Play", icon='PLAY')
        else:
            #op = col_1.operator("screen.animation_manager", icon="PAUSE", text="Pause")
            #op.mode = "PLAY"
            col_1.operator("screen.animation_play", text="Pause", icon='PAUSE')
        #op = col_2.operator("screen.animation_manager", icon="REW", text="Reset")
        #op.mode = "STOP"
        col_2.operator("screen.frame_jump", text="Start", icon='REW').end = False
        col_3.operator("screen.frame_jump", text="End", icon='FF').end = True



class CC3ToolsPhysicsPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Physics_Panel"
    bl_label = "Physics Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        layout = self.layout

        missing_cloth = False
        has_cloth = False
        missing_coll = False
        cloth_mod = None
        coll_mod = None
        meshes_selected = 0
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                meshes_selected += 1
                clm = get_cloth_physics_mod(obj)
                com = get_collision_physics_mod(obj)
                if clm is None:
                    missing_cloth = True
                else:
                    if context.object == obj:
                        cloth_mod = clm
                    has_cloth = True
                if com is None:
                    missing_coll = True
                else:
                    if context.object == obj:
                        coll_mod = com

        obj = context.object
        mat = context_material(context)
        edit_mod, mix_mod = get_material_weight_map_mods(obj, mat)

        box = layout.box()
        box.label(text="Create / Remove", icon="PHYSICS")

        col = layout.column()
        if not missing_cloth:
            op = col.operator("cc3.quickset", icon="REMOVE", text="Remove Cloth Physics")
            op.param = "PHYSICS_REMOVE_CLOTH"
        else:
            op = col.operator("cc3.quickset", icon="ADD", text="Add Cloth Physics")
            op.param = "PHYSICS_ADD_CLOTH"
        if not missing_coll:
            op = col.operator("cc3.quickset", icon="REMOVE", text="Remove Collision Physics")
            op.param = "PHYSICS_REMOVE_COLLISION"
        else:
            op = col.operator("cc3.quickset", icon="ADD", text="Add Collision Physics")
            op.param = "PHYSICS_ADD_COLLISION"
        if meshes_selected == 0:
            col.enabled = False

        box = layout.box()
        box.label(text="Mesh Correction", icon="MESH_DATA")
        col = layout.column()
        op = col.operator("cc3.quickset", icon="MOD_EDGESPLIT", text="Fix Degenerate Mesh")
        op.param = "PHYSICS_FIX_DEGENERATE"
        op = col.operator("cc3.quickset", icon="FACE_MAPS", text="Separate Physics Materials")
        op.param = "PHYSICS_SEPARATE"

        # Cloth Physics Presets
        box = layout.box()
        box.label(text="Presets", icon="PRESET")
        col = layout.column()
        if cloth_mod is None:
            col.enabled = False
        op = col.operator("cc3.quickset", icon="USER", text="Hair")
        op.param = "PHYSICS_HAIR"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Cotton")
        op.param = "PHYSICS_COTTON"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Denim")
        op.param = "PHYSICS_DENIM"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Leather")
        op.param = "PHYSICS_LEATHER"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Rubber")
        op.param = "PHYSICS_RUBBER"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Silk")
        op.param = "PHYSICS_SILK"

        # Cloth Physics Settings
        if cloth_mod is not None:
            box = layout.box()
            box.label(text="Cloth Settings", icon="OPTIONS")
            col = layout.column()
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Weight")
            col_2.prop(cloth_mod.settings, "mass", text="", slider=True)
            col_1.label(text="Bend Resist")
            col_2.prop(cloth_mod.settings, "bending_stiffness", text="", slider=True)
            col_1.label(text="Pin Stiffness")
            col_2.prop(cloth_mod.settings, "pin_stiffness", text="", slider=True)
            col_1.label(text="Quality")
            col_2.prop(cloth_mod.settings, "quality", text="", slider=True)
            col_1.label(text="Collision")
            col_2.prop(cloth_mod.collision_settings, "collision_quality", text="", slider=True)
            col_1.label(text="Distance")
            col_2.prop(cloth_mod.collision_settings, "distance_min", text="", slider=True)
        # Collision Physics Settings
        if coll_mod is not None:
            box = layout.box()
            box.label(text="Collision Settings", icon="OPTIONS")
            col = layout.column()
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Damping")
            col_2.prop(coll_mod.settings, "damping", text="", slider=True)
            col_1.label(text="Outer Thickness")
            col_2.prop(coll_mod.settings, "thickness_outer", text="", slider=True)
            col_1.label(text="Inner Thickness")
            col_2.prop(coll_mod.settings, "thickness_inner", text="", slider=True)
            col_1.label(text="Friction")
            col_2.prop(coll_mod.settings, "cloth_friction", text="", slider=True)


        box = layout.box()
        box.label(text="Weight Maps", icon="TEXTURE_DATA")
        split = layout.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        if not has_cloth:
            col_1.enabled = False
            col_2.enabled = False
        col_1.label(text="WeightMap Size")
        col_2.prop(props, "physics_tex_size", text="")

        col = layout.column()
        if cloth_mod is None:
            col.enabled = False

        if obj is not None:
            col.template_list("MATERIAL_UL_weightedmatslots", "", obj, "material_slots", obj, "active_material_index", rows=1)
        if edit_mod is not None:
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Influence")
            col_2.prop(mix_mod, "mask_constant", text="", slider=True)
        col.separator()
        if bpy.context.mode == "PAINT_TEXTURE":
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Strength")
            col_2.prop(props, "physics_paint_strength", text="", slider=True)
            row = col.row()
            row.scale_y = 2
            op = row.operator("cc3.quickset", icon="CHECKMARK", text="Done Weight Painting!")
            op.param = "PHYSICS_DONE_PAINTING"
        else:
            if edit_mod is None:
                row = col.row()
                op = row.operator("cc3.quickset", icon="ADD", text="Add Weight Map")
                op.param = "PHYSICS_ADD_WEIGHTMAP"
            else:
                row = col.row()
                op = row.operator("cc3.quickset", icon="REMOVE", text="Remove Weight Map")
                op.param = "PHYSICS_REMOVE_WEIGHTMAP"
            col = layout.column()
            if edit_mod is None:
                col.enabled = False
            op = col.operator("cc3.quickset", icon="BRUSH_DATA", text="Paint Weight Map")
            op.param = "PHYSICS_PAINT"
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            op = col_1.operator("cc3.quickset", icon="FILE_TICK", text="Save")
            op.param = "PHYSICS_SAVE"
            op = col_2.operator("cc3.quickset", icon="ERROR", text="Delete")
            op.param = "PHYSICS_DELETE"



class CC3ToolsPipelinePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Pipeline_Panel"
    bl_label = "Import / Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"

    def draw(self, context):
        global debug_counter
        props = bpy.context.scene.CC3ImportProps
        prefs = context.preferences.addons[__name__].preferences

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        if prefs.debug_mode:
            layout.label(text="Counter: " + str(debug_counter))
            debug_counter += 1

        if prefs.lighting == "ENABLED" or prefs.physics == "ENABLED":
            box = layout.box()
            box.label(text="Settings", icon="TOOL_SETTINGS")
            if prefs.lighting == "ENABLED":
                layout.prop(props, "lighting_mode", expand=True)
            if prefs.physics == "ENABLED":
                layout.prop(props, "physics_mode", expand=True)

        box = layout.box()
        box.label(text="Render / Quality", icon="RENDER_RESULT")
        op = layout.operator("cc3.importer", icon="IMPORT", text="Import Character")
        op.param = "IMPORT_QUALITY"

        box = layout.box()
        box.label(text="Morph Editing", icon="OUTLINER_OB_ARMATURE")
        row = layout.row()
        op = row.operator("cc3.importer", icon="IMPORT", text="Import For Morph")
        op.param = "IMPORT_MORPH"
        row = layout.row()
        op = row.operator("cc3.exporter", icon="EXPORT", text="Export Character Morph")
        op.param = "EXPORT_MORPH"
        if props.import_name == "":
            row.enabled = False

        box = layout.box()
        box.label(text="Accessory Editing", icon="MOD_CLOTH")
        row = layout.row()
        op = row.operator("cc3.importer", icon="IMPORT", text="Import For Accessory")
        op.param = "IMPORT_ACCESSORY"
        row = layout.row()
        op = row.operator("cc3.exporter", icon="EXPORT", text="Export Accessory")
        op.param = "EXPORT_ACCESSORY"
        if props.import_name == "":
            row.enabled = False

        layout.separator()
        box = layout.box()
        box.label(text="Clean Up", icon="TRASH")

        row = layout.row()
        op = row.operator("cc3.importer", icon="REMOVE", text="Remove Character")
        op.param ="DELETE_CHARACTER"
        if props.import_name == "":
            row.enabled = False

#class CC3NodeCoord(bpy.types.Panel):
#    bl_label = "Node Coordinates panel"
#    bl_idname = "CC3I_PT_NodeCoord"
#    bl_space_type = "NODE_EDITOR"
#    bl_region_type = "UI"
#
#    def draw(self, context):
#
#        if context.active_node is not None:
#            layout = self.layout
#            layout.separator()
#            row = layout.box().row()
#            coords = context.active_node.location
#            row.label(text=str(int(coords.x/10)*10) + ", " + str(int(coords.y/10)*10))



class CC3ToolsAddonPreferences(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    lighting: bpy.props.EnumProperty(items=[
                        ("DISABLED","Disabled","No automatic lighting and render settings."),
                        ("ENABLED","Enabled","Allows automatic lighting and render settings."),
                    ], default="ENABLED", name = "Automatic Lighting")

    physics: bpy.props.EnumProperty(items=[
                        ("DISABLED","Disabled","No physics auto setup."),
                        ("ENABLED","Enabled","Allows automatic physics setup from physX weight maps."),
                    ], default="ENABLED", name = "Generate Physics")

    quality_lighting: bpy.props.EnumProperty(items=[
                        ("BLENDER","Blender Default","Blenders default lighting setup"),
                        ("MATCAP","Solid Matcap","Solid shading matcap lighting for sculpting / mesh editing"),
                        ("CC3","CC3 Default","Replica of CC3 default lighting setup"),
                        ("STUDIO","Studio Right","Right facing 3 point lighting with the studio hdri"),
                        ("COURTYARD","Courtyard Left","Left facing soft 3 point lighting with the courtyard hdri"),
                    ], default="CC3", name = "Render / Quality Lighting")

    pipeline_lighting: bpy.props.EnumProperty(items=[
                        ("BLENDER","Blender Default","Blenders default lighting setup"),
                        ("MATCAP","Solid Matcap","Solid shading matcap lighting for sculpting / mesh editing"),
                        ("CC3","CC3 Default","Replica of CC3 default lighting setup"),
                        ("STUDIO","Studio Right","Right facing 3 point lighting with the studio hdri"),
                        ("COURTYARD","Courtyard Left","Left facing soft 3 point lighting with the courtyard hdri"),
                    ], default="CC3", name = "(FBX) Accessory Editing Lighting")

    morph_lighting: bpy.props.EnumProperty(items=[
                        ("BLENDER","Blender Default","Blenders default lighting setup"),
                        ("MATCAP","Solid Matcap","Solid shading matcap lighting for sculpting / mesh editing"),
                        ("CC3","CC3 Default","Replica of CC3 default lighting setup"),
                        ("STUDIO","Studio Right","Right facing 3 point lighting with the studio hdri"),
                        ("COURTYARD","Courtyard Left","Left facing soft 3 point lighting with the courtyard hdri"),
                    ], default="MATCAP", name = "(OBJ) Morph Edit Lighting")

    quality_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic Materials","Build basic PBR materials for quality / rendering"),
                        ("ADVANCED","Advanced Materials","Build advanced materials for quality / rendering"),
                    ], default="ADVANCED", name = "Render / Quality Material Mode")

    # = accessory_mode
    pipeline_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic Materials","Build basic PBR materials for character morph / accessory editing"),
                        ("ADVANCED","Advanced Materials","Build advanced materials for character morph / accessory editing"),
                    ], default="ADVANCED", name = "Accessory Material Mode")

    morph_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic Materials","Build basic PBR materials for character morph / accessory editing"),
                        ("ADVANCED","Advanced Materials","Build advanced materials for character morph / accessory editing"),
                    ], default="ADVANCED", name = "Character Morph Material Mode")

    log_level: bpy.props.EnumProperty(items=[
                        ("ALL","All","Log everything to console."),
                        ("WARN","Warnings & Errors","Log warnings and error messages to console."),
                        ("ERRORS","Just Errors","Log only errors to console."),
                    ], default="ERRORS", name = "(Debug) Log Level")

    debug_mode: bpy.props.BoolProperty(default=False)

    physics_group: bpy.props.StringProperty(default="CC_Physics", name="Physics Vertex Group Prefix")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.label(text="Material settings:")
        layout.prop(self, "quality_mode")
        layout.prop(self, "pipeline_mode")
        layout.prop(self, "morph_mode")
        layout.label(text="Lighting:")
        layout.prop(self, "lighting")
        if self.lighting == "ENABLED":
            layout.prop(self, "quality_lighting")
            layout.prop(self, "pipeline_lighting")
            layout.prop(self, "morph_lighting")
        layout.label(text="Physics:")
        layout.prop(self, "physics")
        layout.prop(self, "physics_group")
        layout.label(text="Debug Settings:")
        layout.prop(self, "log_level")
        layout.prop(self, "debug_mode")
        op = layout.operator("cc3.quickset", icon="FILE_REFRESH", text="Reset to Defaults")
        op.param = "RESET_PREFS"

class MATERIAL_UL_weightedmatslots(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        slot = item
        ma = slot.material
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if ma:
                layout.prop(ma, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

classes = (CC3ObjectPointer, CC3MaterialCache, CC3ObjectCache, CC3ImportProps,
           CC3ToolsPipelinePanel, CC3ToolsMaterialSettingsPanel, CC3ToolsPhysicsPanel, CC3ToolsScenePanel,
           MATERIAL_UL_weightedmatslots,
           CC3Import, CC3Export, CC3Scene, CC3QuickSet, CC3ToolsAddonPreferences)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.CC3ImportProps = bpy.props.PointerProperty(type=CC3ImportProps)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del(bpy.types.Scene.CC3ImportProps)


# This allows you to run the script directly from Blender"s Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()