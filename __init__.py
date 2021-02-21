import bpy
import os
import mathutils

# TODO
#   3. prefs for setting lighting automatically etc...
#   6. defaults for node group inputs

bl_info = {
    "name": "CC3 Tools",
    "author": "Victor Soupday",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "category": "Characters",
    "location": "3D View > Properties> CC3",
    "description": "Automatic import and material setup of CC3 characters.",
}

VERSION_STRING = "v1.0.0"

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

NODE_PREFIX = "cc3iid_"

GRID_SIZE = 300
cursor = mathutils.Vector((0,0))
cursor_top = mathutils.Vector((0,0))
max_cursor = mathutils.Vector((0,0))
new_nodes = []

LOG_LEVEL = 1

def log_info(msg):
    """Log an info message to console."""
    if LOG_LEVEL >= 2:
        print(msg)

def log_warn(msg):
    """Log a warning message to console."""
    if LOG_LEVEL >= 1:
        print("Warning: " + msg)

def log_error(msg):
    """Log an error message to console and raise an exception."""
    print("Error: " + msg)

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
def find_image_file(dir, mat, suffix_list):

    material_name = strip_name(mat.name).lower()

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
    for p in props.material_cache:
        if p.material == mat:
            # there is a a bug in the blender fbx and obj importers, files with spaces in the name
            # sometimes don't import the images correctly, so we can only trust the imported images
            # in the material_cache if they were embedded in the fbx.
            if props.import_embedded:
                if "diffuse" in suffix_list:
                    return p.diffuse
                elif "specular" in suffix_list:
                    return p.specular
                elif "opacity" in suffix_list:
                    return p.alpha
                elif "normal" in suffix_list:
                    return p.normal
                elif "bump" in suffix_list:
                    return p.bump
            # otherwise find the files directly in the material directory
            image_file = find_image_file(p.dir, p.material, suffix_list)
            # failing that look in the main tex directory (if different)
            if image_file is None and \
               props.import_main_tex_dir != "" and \
               os.path.normcase(p.dir) != os.path.normcase(props.import_main_tex_dir):
                image_file = find_image_file(props.import_main_tex_dir, p.material, suffix_list)
            if image_file is not None:
                return load_image(image_file, color_space)
            break
    return None


def apply_alpha_override(obj, mat, method):
    input = get_shader_input(mat, "Alpha")
    if input is None:
        return
    if is_input_connected(input):
        set_material_alpha(mat, method)
    elif input.default_value < 1.0:
        set_material_alpha(mat, method)
    else:
        set_material_alpha(mat, "OPAQUE")
    return


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
            log_warn("Unable to set input: " + node.name + "[" + str(socket) + "]")

def set_node_output(node, socket, value):
    if node is not None:
        try:
            node.outputs[socket].default_value = value
        except:
            log_warn("Unable to set output: " + node.name + "[" + str(socket) + "]")

def link_nodes(links, from_node, from_socket, to_node, to_socket):
    if from_node is not None and to_node is not None:
        try:
            links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])
        except:
            log_warn("Unable to link: " + from_node.name + "[" + str(from_socket) + "] to " +
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
        elif is_teeth_material(mat):
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


def connect_base_color(obj, mat, shader):
    props = bpy.context.scene.CC3ImportProps

    diffuse_image = find_material_image(mat, BASE_COLOR_MAP)
    blend_image = find_material_image(mat, MOD_BASECOLORBLEND_MAP)
    ao_image = find_material_image(mat, MOD_AO_MAP)
    mcmao_image = find_material_image(mat, MOD_MCMAO_MAP)
    prop_blend, blend_value = get_blend_strength(obj, mat)
    prop_ao, ao_value = get_ao_strength(obj, mat)
    prop_group = get_material_group(obj, mat)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    reset_cursor()
    # space
    advance_cursor(-count_maps(diffuse_image, ao_image, blend_image, mcmao_image))
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

    if sss_image is None and trans_image is None and not is_hair_object(obj, mat) and not is_skin_material(mat):
        return None

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    reset_cursor()
    # space
    advance_cursor(-count_maps(trans_image, sss_image))
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
    # links
    link_nodes(links, diffuse_node, "Base Color", group_node, "Diffuse")
    #link_nodes(links, diffuse_node, "Diffuse", group_node, "Diffuse")
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

    reset_cursor()
    # space
    advance_cursor(-count_maps(mask_image, specular_image, roughness_image, metallic_image))
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

    reset_cursor()

    advance_cursor(-5)
    # space
    advance_cursor(5 - count_maps(bump_image, mask_image, micro_image, blend_image, normal_image))
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


# base names of all node groups in the library blend file
node_groups = ["color_ao_mixer", "color_blend_ao_mixer", "color_eye_mixer", "color_teeth_mixer", "color_tongue_mixer", "color_head_mixer",
               "subsurface_mixer", "subsurface_overlay_mixer",
               "msr_mixer", "msr_overlay_mixer",
               "normal_micro_mask_blend_mixer", "normal_micro_mask_mixer", "bump_mixer",
               "eye_occlusion_mask", "iris_mask", "tiling_pivot_mapping", "tiling_mapping"]


def get_node_group(name):
    for group in bpy.data.node_groups:
        if NODE_PREFIX in group.name and name in group.name:
            if VERSION_STRING in group.name:
                return group
    return fetch_node_group(name)


def check_node_groups():
    for name in node_groups:
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

    try:
        for child in obj.children:
            delete_object(child)

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
        for slot in obj.material_slots:
            mat = slot.material
            if mat.node_tree is not None:
                nodes = mat.node_tree.nodes
                for node in nodes:
                    if node.type == "TEX_IMAGE":
                        image = node.image
                        bpy.data.images.remove(image)
                    nodes.remove(node)
            bpy.data.materials.remove(mat)

        if obj.type == "ARMATURE":
            bpy.data.armatures.remove(obj.data)
        else:
            bpy.data.objects.remove(obj)

    except:
        log_error("Something went wrong deleting object...")

def delete_character():
    props = bpy.context.scene.CC3ImportProps

    for p in props.import_objects:
        delete_object(p.object)

    props.import_objects.clear()
    props.import_file = ""
    props.material_cache.clear()

    clean_colletion(bpy.data.materials)
    clean_colletion(bpy.data.images)
    clean_colletion(bpy.data.meshes)
    clean_colletion(bpy.data.node_groups)

def process_material(obj, mat):
    props = bpy.context.scene.CC3ImportProps

    reset_nodes(mat)

    node_tree = mat.node_tree
    nodes = node_tree.nodes
    shader = None

    if props.hair_object is None and is_hair_object(obj, mat):
        props.hair_object = obj

    # find the Principled BSDF shader node
    for n in nodes:
        if (n.type == "BSDF_PRINCIPLED"):
            shader = n
            break

    # create one if it does not exist
    if shader is None:
        shader = nodes.new("ShaderNodeBsdfPrincipled")

    clear_cursor()

    if is_eye_material(mat):

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

def process_material_slots(obj):

    for slot in obj.material_slots:
        log_info("Processing Material: " + slot.material.name)
        process_material(obj, slot.material)


def scan_for_hair_object(obj):
    for slot in obj.material_slots:
        if slot.material is not None:
            if is_hair_object(obj, slot.material):
                return obj
    return None

def process_object(obj, objects_processed):
    props = bpy.context.scene.CC3ImportProps

    if obj is None or obj in objects_processed:
        return

    objects_processed.append(obj)

    log_info("Processing Object: " + obj.name + ", Type: " + obj.type)

    # try to determine if this is the hair object, if not set
    if props.hair_object is None:
        props.hair_object = scan_for_hair_object(obj)

    # process any materials found in a mesh object
    if obj.type == "MESH":
        process_material_slots(obj)

    # process child objects
    for child in obj.children:
        process_object(child, objects_processed)



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


def cache_object_materials(obj):
    global image_list
    props = bpy.context.scene.CC3ImportProps
    base_dir, file_name = os.path.split(props.import_file)
    type = file_name[-3:].lower()
    character_name = file_name[:-4]

    if obj is None:
        return

    if obj.type == "MESH":
        for slot in obj.material_slots:
            if slot.material.node_tree is not None:
                cache = props.material_cache.add()
                cache.material = slot.material
                cache.dir = get_material_dir(base_dir, character_name, type, obj, slot.material)
                nodes = slot.material.node_tree.nodes
                for node in nodes:
                    if node.type == "TEX_IMAGE":
                        if node.image is not None:
                            filepath = node.image.filepath
                            dir, name = os.path.split(filepath)
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

def tag_objects(default = True):
    for obj in bpy.data.objects:
        obj.tag = default


def untagged_objects(default = True):

    untagged = []

    for obj in bpy.data.objects:
        if not obj.tag == default:
            untagged.append(obj)
        obj.tag = default

    return untagged


def select_all_child_objects(obj):
    if obj.type == "ARMATURE" or obj.type == "MESH":
        obj.select_set(True)
    for child in obj.children:
        select_all_child_objects(child)

class CC3Import(bpy.types.Operator):
    """Import CC3 Character and build materials"""
    bl_idname = "cc3.importer"
    bl_label = "Import CC3 Character"
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

    def import_character(self):
        props = bpy.context.scene.CC3ImportProps

        import_anim = self.use_anim
        # don't import animation data if importing for morph/accessory
        if self.param == "IMPORT_PIPELINE":
            import_anim = False
        props.import_file = self.filepath
        dir, name = os.path.split(self.filepath)
        props.import_objects.clear()
        props.material_cache.clear()
        type = name[-3:].lower()
        name = name[:-4]
        props.import_type = type
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
            imported = untagged_objects()
            for obj in imported:
                if obj.type == "ARMATURE":
                    p = props.import_objects.add()
                    p.object = obj
                elif obj.type == "MESH":
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
            if self.param == "IMPORT_PIPELINE":
                bpy.ops.import_scene.obj(filepath = self.filepath, split_mode = "OFF",
                        use_split_objects = False, use_split_groups = False,
                        use_groups_as_vgroups = True)
            else:
                bpy.ops.import_scene.obj(filepath = self.filepath, split_mode = "ON",
                        use_split_objects = True, use_split_groups = True,
                        use_groups_as_vgroups = False)
            imported = untagged_objects()
            for obj in imported:
                # scale obj import by 1/100
                obj.scale = (0.01, 0.01, 0.01)
                if obj.type == "MESH":
                    p = props.import_objects.add()
                    p.object = obj
                    cache_object_materials(obj)
            log_info("Done .Obj Import.")

        self.build_materials()



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


    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = context.preferences.addons[__name__].preferences

        # import character
        if self.param == "IMPORT" or self.param == "IMPORT_PIPELINE" or self.param == "IMPORT_QUALITY":

            # use basic materials for morph/accessory editing as it has better viewport performance
            if self.param == "IMPORT_PIPELINE":
                props.setup_mode = "BASIC"

            # use advanced materials for quality/rendering
            elif self.param == "IMPORT_QUALITY":
                props.setup_mode = "ADVANCED"

            self.import_character()

            # use the cc3 lighting for morph/accessory editing
            if self.param == "IMPORT_PIPELINE":
                if prefs.auto_lighting:
                    setup_scene_default("CC3_DEFAULT")
                # for any objects with shape keys select basis and enable show in edit mode
                for p in props.import_objects:
                    init_character_for_edit(p.object)

            # use portrait lighting for quality mode
            elif self.param == "IMPORT_QUALITY":
                if prefs.auto_lighting:
                    setup_scene_default("COURTYARD_LEFT")

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
        if self.param == "IMPORT" or self.param == "IMPORT_PIPELINE" or self.param == "IMPORT_QUALITY":
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

        return self.execute(context)

    @classmethod
    def description(cls, context, properties):
        if properties.param == "IMPORT":
            return "Import a new .fbx or .obj character exported by Character Creator 3"
        elif properties.param == "REIMPORT":
            return "Rebuild the materials from the last import with the current settings"
        elif properties.param == "IMPORT_PIPELINE":
            return "Import .fbx or .obj character from CC3 for morph or accessory creation.\n" \
                   "For best results for morph creation, in CC3, export mesh only fbx to blender, or obj nude character in bind pose.\n" \
                   "Note: nude character in bind pose .obj does not export any materials"
        elif properties.param == "IMPORT_QUALITY":
            return "Import .fbx or .obj character from CC3 for rendering.\n"
        return ""


class CC3Export(bpy.types.Operator):
    """Export CC3 Character"""
    bl_idname = "cc3.exporter"
    bl_label = "Export CC3 Character"
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

        if self.param == "EXPORT_PIPELINE" or self.param == "EXPORT":
            export_anim = self.use_anim
            mode = props.export_mode
            if self.param == "EXPORT_PIPELINE":
                export_anim = False
                mode = props.pipeline_mode
            props.import_file = self.filepath
            dir, name = os.path.split(self.filepath)
            type = name[-3:].lower()
            name = name[:-4]

            # store selection
            old_selection = bpy.context.selected_objects
            old_active = bpy.context.active_object

            if type == "fbx":

                if mode == "IMPORTED":
                    bpy.ops.object.select_all(action='DESELECT')
                    for p in props.import_objects:
                        if p.object is not None:
                            if p.object.type == "ARMATURE":
                                select_all_child_objects(p.object)
                elif mode == "SELECTED":
                    for obj in bpy.context.selected_objects:
                        if obj.type == "ARMATURE":
                            select_all_child_objects(obj)
                elif mode == "BOTH":
                    for obj in bpy.context.selected_objects:
                        if obj.type == "ARMATURE":
                            select_all_child_objects(obj)
                    for p in props.import_objects:
                        if p.object is not None:
                            if p.object.type == "ARMATURE":
                                select_all_child_objects(p.object)

                bpy.ops.export_scene.fbx(filepath=self.filepath,
                        use_selection = True,
                        bake_anim = export_anim,
                        add_leaf_bones=False)

            else:

                if mode == "IMPORTED":
                    for p in props.import_objects:
                        if p.object is not None:
                            if p.object.type == "MESH":
                                p.object.select_set(True)

                if self.param == "EXPORT_PIPELINE":
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

            # restore selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in old_selection:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = old_active

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
        elif self.param == "EXPORT_PIPELINE" or self.param == "EXPORT":
            mode = props.export_mode
            if self.param == "EXPORT_PIPELINE":
                mode = props.pipeline_mode
            # exporting imported or both, use the same file type as imported
            if mode == "IMPORTED" or mode == "BOTH":
                self.filename_ext = "." + props.import_type
            # exporting selected, use fbx only if there is an armature present
            elif mode == "SELECTED":
                self.filename_ext = ".obj"
                for obj in bpy.context.selected_objects:
                    if obj.type == "ARMATURE":
                        self.filename_ext = ".fbx"
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

        if properties.param == "EXPORT_PIPELINE":
            return "Export .fbx character for re-import into CC3 or .obj character for morph slider creation.\nIf exporting from selected: selecting an armature will export as .fbx and selecting just objects will export as .obj"
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

def remove_all_lights():
    for obj in bpy.data.objects:
        if obj.type == "LIGHT" and not obj.hide_viewport:
            bpy.data.objects.remove(obj)

def init_fbx_edit():
    props = bpy.context.scene.CC3ImportProps

def init_character_for_edit(obj):
    #bpy.context.active_object.data.shape_keys.key_blocks['Basis']
    if obj.type == "MESH":
        shape_keys = obj.data.shape_keys
        if shape_keys is not None:
            blocks = shape_keys.key_blocks
            if blocks is not None:
                if len(blocks) > 0:
                    set_shape_key_edit(obj)

    if obj.type == "ARMATURE":
        for child in obj.children:
            init_character_for_edit(child)


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
    # store selection and mode
    current_selected = bpy.context.selected_objects
    current_active = bpy.context.active_object
    current_mode = bpy.context.mode
    # go to object mode
    try:
        if current_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        bpy.context.space_data.lens = 120


        if scene_type == "BLENDER_DEFAULT":

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
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "None"
            bpy.context.scene.view_settings.exposure = 0.0
            bpy.context.scene.view_settings.gamma = 1.0

            remove_all_lights()

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
            bpy.context.space_data.lens = 50
            bpy.context.space_data.clip_start = 0.1


        elif scene_type == "CC3_DEFAULT":

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

            remove_all_lights()

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

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'studio.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 0
            bpy.context.space_data.shading.studiolight_intensity = 0.75
            bpy.context.space_data.shading.studiolight_background_alpha = 0
            bpy.context.space_data.shading.studiolight_background_blur = 0
            bpy.context.space_data.lens = 80
            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "STUDIO_RIGHT":

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
            bpy.context.scene.view_settings.look = "High Contrast"
            bpy.context.scene.view_settings.exposure = 0.5
            bpy.context.scene.view_settings.gamma = 1.0

            remove_all_lights()

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
            set_contact_shadow(right, 0.1, 0.005)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'studio.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 0.0
            bpy.context.space_data.shading.studiolight_intensity = 0.2
            bpy.context.space_data.shading.studiolight_background_alpha = 0.5
            bpy.context.space_data.shading.studiolight_background_blur = 0.5
            bpy.context.space_data.lens = 80
            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "COURTYARD_LEFT":

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
            bpy.context.scene.view_settings.look = "Medium High Contrast"
            bpy.context.scene.view_settings.exposure = 0.5
            bpy.context.scene.view_settings.gamma = 0.6

            remove_all_lights()

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

            set_contact_shadow(key, 0.1, 0.001)
            set_contact_shadow(fill, 0.1, 0.005)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'courtyard.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 2.00713
            bpy.context.space_data.shading.studiolight_intensity = 0.35
            bpy.context.space_data.shading.studiolight_background_alpha = 0.5
            bpy.context.space_data.shading.studiolight_background_blur = 0.5

            bpy.context.space_data.lens = 80
            bpy.context.space_data.clip_start = 0.01

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
        setup_scene_default(self.param)
        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "BLENDER_DEFAULT":
            return "Restore the render settings and lighting to the Blender defaults"
        elif properties.param == "CC3_DEFAULT":
            return "Set the render settings and lighting to a facsimile of the default CC3 lighting"
        elif properties.param == "PORTRAIT LIGHTS":
            return "Set the render settings and lighting to a soft 3 point lighting setup focused on the face"
        return ""


def quick_set_process_object(param, obj, objects_processed):
    if obj is not None and obj not in objects_processed:
        if obj.type == "MESH":
            objects_processed.append(obj)
            for slot in obj.material_slots:
                if slot.material is not None:
                    mat = slot.material
                    if param == "OPAQUE" or param == "BLEND" or param == "HASHED":
                        apply_alpha_override(obj, mat, param)
                    elif param == "SINGLE_SIDED":
                        mat.use_backface_culling = True
                    elif param == "DOUBLE_SIDED":
                        mat.use_backface_culling = False
                    elif param == "UPDATE_SELECTED" or param == "UPDATE_ALL":
                        refresh_parameters(mat)

        for child in obj.children:
            quick_set_process_object(param, child, objects_processed)


def quick_set_execute(param):
    objects_processed = []
    props = bpy.context.scene.CC3ImportProps

    if param == "RESET":
        reset_parameters()

    elif param == "UPDATE_ALL":
        for p in props.import_objects:
            if p.object is not None:
                quick_set_process_object(param, p.object, objects_processed)
    else:
        for obj in bpy.context.selected_objects:
            quick_set_process_object(param, obj, objects_processed)

block_update = False

def quick_set_update(self, context):
    global block_update
    if not block_update:
        quick_set_execute("UPDATE_ALL")

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
            if con.name == "iCC3_open_mouth_contraint":
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
        quick_set_execute(self.param)
        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "UPDATE_ALL":
            return "Update all objects from the last import, with the current parameters"
        elif properties.param == "UPDATE_SELECTED":
            return "Update only the currently selected objects, with the current parameters"
        elif properties.param == "OPAQUE":
            return "Set blend mode of all selected objects with alpha channels to opaque"
        elif properties.param == "BLEND":
            return "Set blend mode of all selected objects with alpha channels to alpha blend"
        elif properties.param == "HASHED":
            return "Set blend mode of all selected objects with alpha channels to alpha hashed"
        elif properties.param == "FETCH":
            return "Fetch the parameters from the selected objects."
        elif properties.param == "RESET":
            return "Reset parameters to the defaults."
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


def reset_parameters():
    global block_update
    props = bpy.context.scene.CC3ImportProps

    block_update = True

    props.skin_ao = 1.0
    props.skin_blend = 0.0
    props.skin_normal_blend = 0.0
    props.skin_roughness = 0.2
    props.skin_specular = 0.4
    props.skin_basic_specular = 0.4
    props.skin_basic_roughness = 0.2
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
    props.eye_shadow_hardness = 0.75
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
    props.hair_sss_radius = 2.0
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
    quick_set_execute("UPDATE_ALL")

    return

class CC3ObjectPointer(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)

class CC3MaterialCache(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(type=bpy.types.Material)
    dir: bpy.props.StringProperty(default="")
    diffuse: bpy.props.PointerProperty(type=bpy.types.Image)
    normal: bpy.props.PointerProperty(type=bpy.types.Image)
    bump: bpy.props.PointerProperty(type=bpy.types.Image)
    alpha: bpy.props.PointerProperty(type=bpy.types.Image)
    specular: bpy.props.PointerProperty(type=bpy.types.Image)
    alpha_is_diffuse: bpy.props.BoolProperty(default=False)

class CC3ImportProps(bpy.types.PropertyGroup):

    node_id: bpy.props.IntProperty(default=1000)

    setup_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic Materials","Build basic PBR materials."),
                        ("ADVANCED","Adv. Materials","Build advanced materials with blend maps, subsurface, and micro normals, specular and roughness control and includes layered eye, teeth and tongue materials.")
                    ], default="BASIC")

    build_mode: bpy.props.EnumProperty(items=[
                        ("IMPORTED","All Imported","Build materials for all the imported objects."),
                        ("SELECTED","Only Selected","Build materials only for the selected objects.")
                    ], default="IMPORTED")

    export_mode: bpy.props.EnumProperty(items=[
                        ("IMPORTED","Imported","Export only the last imported character"),
                        ("SELECTED","Selected","Export only the selected objects"),
                        ("BOTH","Both","Export the last imported character and any additional selected objects")
                    ], default="IMPORTED")

    pipeline_mode: bpy.props.EnumProperty(items=[
                        ("IMPORTED","Imported","Export only the last imported character"),
                        ("SELECTED","Selected","Export only the selected objects"),
                        ("BOTH","Both","Export the last imported character and any additional selected objects")
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

    import_file: bpy.props.StringProperty(default="", subtype="FILE_PATH")
    import_objects: bpy.props.CollectionProperty(type=CC3ObjectPointer)
    material_cache: bpy.props.CollectionProperty(type=CC3MaterialCache)
    import_type: bpy.props.StringProperty(default="")
    import_embedded: bpy.props.BoolProperty(default=False)
    import_main_tex_dir: bpy.props.StringProperty(default="")
    import_space_in_name: bpy.props.BoolProperty(default=False)

    stage1: bpy.props.BoolProperty(default=True)
    stage1_details: bpy.props.BoolProperty(default=False)
    stage2: bpy.props.BoolProperty(default=True)
    stage3: bpy.props.BoolProperty(default=True)
    stage4: bpy.props.BoolProperty(default=True)
    stage5: bpy.props.BoolProperty(default=True)
    stage6: bpy.props.BoolProperty(default=True)

    skin_basic_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    skin_basic_roughness: bpy.props.FloatProperty(default=0.2, min=0, max=2, update=quick_set_update)
    eye_basic_roughness: bpy.props.FloatProperty(default=0.05, min=0, max=1, update=quick_set_update)
    eye_basic_normal: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=quick_set_update)
    eye_basic_brightness: bpy.props.FloatProperty(default=0.9, min=0, max=2, update=quick_set_update)

    skin_toggle: bpy.props.BoolProperty(default=True)
    skin_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    skin_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    skin_normal_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    skin_roughness: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=quick_set_update)
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
    eye_shadow_hardness: bpy.props.FloatProperty(default=0.75, min=0, max=1, update=quick_set_update)
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
    hair_scalp_hint: bpy.props.StringProperty(default="scalp,base", update=quick_set_update)
    hair_specular: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=quick_set_update)
    hair_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_scalp_specular: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_scalp_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=quick_set_update)
    hair_blend: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=quick_set_update)
    hair_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)
    hair_sss_radius: bpy.props.FloatProperty(default=2.0, min=0.1, max=5, update=quick_set_update)
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


class MyPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Import_Settings_Panel"
    bl_label = "CC3 Import Character"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"

    def draw(self, context):
        layout = self.layout

        obj = context.object
        props = bpy.context.scene.CC3ImportProps

        if fake_drop_down(layout.box().row(),
                "1. Import Character",
                "stage1",
                props.stage1):
            box = layout.box()
            op = box.operator("cc3.importer", icon="IMPORT", text="Import Character")
            op.param ="IMPORT"
            # import details
            if props.import_file != "" or len(props.import_objects) > 0:
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

        layout.separator()
        if fake_drop_down(layout.box().row(),
                "2. Build Materials",
                "stage2",
                props.stage2):
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
            col_1.separator()
            col_2.separator()
            if props.import_file != "":
                box = layout.box()
                if props.setup_mode == "ADVANCED":
                    text = "Build Advanced Materials"
                else:
                    text = "Build Basic Materials"
                op = box.operator("cc3.importer", icon="MATERIAL", text=text)
                op.param ="BUILD"

        layout.separator()
        if fake_drop_down(layout.box().row(),
                "3. Fix Alpha Blending",
                "stage3",
                props.stage3):
            split = layout.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="")
            col_1.label(text="Quick Set Alpha")
            col_1.label(text="")
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


        layout.separator()
        if fake_drop_down(layout.box().row(),
                "4. Adjust Parameters",
                "stage4",
                props.stage4):
            layout.prop(props, "update_mode", expand=True)
            if props.setup_mode == "ADVANCED":
                # Skin Settings
                layout.separator()
                split = layout.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                if props.update_mode == "UPDATE_ALL":
                    col_1.label(text="Update All")
                else:
                    col_1.label(text="Update Selected")
                op = col_2.operator("cc3.quickset", icon="FILE_REFRESH", text="Update")
                op.param = props.update_mode
                layout.separator()
                if fake_drop_down(layout.row(),
                        "Skin Parameters",
                        "skin_toggle",
                        props.skin_toggle):
                    layout.separator()
                    split = layout.split(factor=0.5)
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
                layout.separator()
                if fake_drop_down(layout.row(),
                        "Eye Parameters",
                        "eye_toggle",
                        props.eye_toggle):
                    layout.separator()
                    split = layout.split(factor=0.5)
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
                layout.separator()
                if fake_drop_down(layout.row(),
                        "Teeth Parameters",
                        "teeth_toggle",
                        props.teeth_toggle):
                    layout.separator()
                    split = layout.split(factor=0.5)
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
                layout.separator()
                if fake_drop_down(layout.row(),
                        "Tongue Parameters",
                        "tongue_toggle",
                        props.tongue_toggle):
                    layout.separator()
                    split = layout.split(factor=0.5)
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
                layout.separator()
                if fake_drop_down(layout.row(),
                        "Nails Parameters",
                        "nails_toggle",
                        props.nails_toggle):
                    layout.separator()
                    split = layout.split(factor=0.5)
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
                layout.separator()
                if fake_drop_down(layout.row(),
                        "Hair Parameters",
                        "hair_toggle",
                        props.hair_toggle):
                    layout.separator()
                    split = layout.split(factor=0.5)
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
                layout.separator()
                if fake_drop_down(layout.row(),
                        "Default Parameters",
                        "default_toggle",
                        props.default_toggle):
                    layout.separator()
                    split = layout.split(factor=0.5)
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
                layout.separator()
                split = layout.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Parameters")
                op = col_2.operator("cc3.quickset", icon="FILE_REFRESH", text="Update")
                op.param = props.update_mode
                layout.separator()
                split = layout.split(factor=0.5)
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

        layout.separator()

        if fake_drop_down(layout.box().row(),
                "5. Utilities",
                "stage5",
                props.stage5):
            layout.separator()
            split = layout.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Open Mouth")
            col_2.prop(props, "open_mouth", text="", slider=True)

            op = layout.operator("cc3.quickset", icon="DECORATE_OVERRIDE", text="Reset Parameters")
            op.param = "RESET"

            op = layout.operator("cc3.importer", icon="MOD_BUILD", text="Rebuild Node Groups")
            op.param ="REBUILD_NODE_GROUPS"

            op = layout.operator("cc3.importer", icon="REMOVE", text="Remove Character")
            op.param ="DELETE_CHARACTER"

            layout.separator()
            split = layout.split(factor=0.5)
            layout.separator()

        layout.separator_spacer()


class MyPanel2(bpy.types.Panel):
    bl_idname = "CC3_PT_Export_Settings_Panel"
    bl_label = "CC3 Export Character"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        layout = self.layout

        layout.separator()
        split = layout.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()

        col_1.label(text="Operate On")
        col_2.prop(props, "export_mode", text="")

        col_1.label(text="Export Character")
        op = col_2.operator("cc3.exporter", icon="EXPORT", text="To CC3")
        op.param ="EXPORT"

        layout.separator_spacer()


class MyPanel3(bpy.types.Panel):
    bl_idname = "CC3_PT_Scene_Panel"
    bl_label = "CC3 Scene Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        layout = self.layout

        layout.separator()
        split = layout.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()

        col_1.label(text="Blender Default")
        op = col_2.operator("cc3.scene", icon="LIGHT", text="Lights")
        op.param = "BLENDER_DEFAULT"

        col_1.label(text="CC3 Default")
        op = col_2.operator("cc3.scene", icon="LIGHT", text="Lights")
        op.param = "CC3_DEFAULT"

        col_1.label(text="Studio Right")
        op = col_2.operator("cc3.scene", icon="LIGHT", text="Lights")
        op.param = "STUDIO_RIGHT"

        col_1.label(text="Courtyard Left")
        op = col_2.operator("cc3.scene", icon="LIGHT", text="Lights")
        op.param = "COURTYARD_LEFT"

        layout.separator_spacer()


class MyPanel4(bpy.types.Panel):
    bl_idname = "CC3_PT_Pipeline_Panel"
    bl_label = "CC3 Pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps

        layout = self.layout

        box = layout.box()
        box.label(text="Render / Quality", icon="INFO")

        op = layout.operator("cc3.importer", icon="IMPORT", text="Import Character")
        op.param = "IMPORT_QUALITY"

        layout.separator()

        box = layout.box()
        box.label(text="Morph / Accessory", icon="INFO")

        op = layout.operator("cc3.importer", icon="IMPORT", text="Import Morph Character")
        op.param = "IMPORT_PIPELINE"

        op = layout.operator("cc3.exporter", icon="EXPORT", text="Export Morph Character")
        op.param = "EXPORT_PIPELINE"

        op = layout.operator("cc3.exporter", icon="EXPORT", text="Export Accessory")
        op.param = "EXPORT_ACCESSORY"

        layout.separator_spacer()


class CC3NodeCoord(bpy.types.Panel):
    bl_label = "Node Coordinates panel"
    bl_idname = "CC3I_PT_NodeCoord"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    def draw(self, context):

        if context.active_node is not None:
            layout = self.layout
            layout.separator()
            row = layout.box().row()
            coords = context.active_node.location
            row.label(text=str(int(coords.x/10)*10) + ", " + str(int(coords.y/10)*10))



class CC3ToolsAddonPreferences(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    #import_type: bpy.props.StringProperty(default="")
    #stage1: bpy.props.BoolProperty(default=True)
    #skin_basic_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=quick_set_update)

    auto_lighting: bpy.props.BoolProperty(name="Auto Lighting", default=True, description="Automatically change lighting on quick import.")

    quality_lighting: bpy.props.EnumProperty(items=[
                        ("BLENDER_DEFAULT","Blender Default","Blenders default lighting setup"),
                        ("CC3_DEFAULT","CC3 Default","Replica of CC3 default lighting setup"),
                        ("STUDIO_RIGHT","Studio Right","Right facing 3 point lighting with the studio hdri"),
                        ("COURTYARD_LEFT","Courtyard Left","Left facing soft 3 point lighting with the courtyard hdri")
                    ], default="COURTYARD_LEFT", name = "Render / Quality Lighting")

    pipeline_lighting: bpy.props.EnumProperty(items=[
                        ("BLENDER_DEFAULT","Blender Default","Blenders default lighting setup"),
                        ("CC3_DEFAULT","CC3 Default","Replica of CC3 default lighting setup"),
                        ("STUDIO_RIGHT","Studio Right","Right facing 3 point lighting with the studio hdri"),
                        ("COURTYARD_LEFT","Courtyard Left","Left facing soft 3 point lighting with the courtyard hdri")
                    ], default="CC3_DEFAULT", name = "Morph / Accessory Editing Lighting")

    def draw(self, context):
        layout = self.layout
        layout.label(text="This is a preferences view for our add-on")
        layout.prop(self, "auto_lighting")
        layout.prop(self, "quality_lighting")
        layout.prop(self, "pipeline_lighting")




def register():
    bpy.utils.register_class(CC3NodeCoord)
    bpy.utils.register_class(CC3ObjectPointer)
    bpy.utils.register_class(CC3MaterialCache)
    bpy.utils.register_class(CC3ImportProps)
    bpy.utils.register_class(MyPanel4)
    bpy.utils.register_class(MyPanel)
    bpy.utils.register_class(MyPanel2)
    bpy.utils.register_class(MyPanel3)
    bpy.utils.register_class(CC3Import)
    bpy.utils.register_class(CC3Export)
    bpy.utils.register_class(CC3Scene)
    bpy.utils.register_class(CC3QuickSet)
    bpy.utils.register_class(CC3ToolsAddonPreferences)
    bpy.types.Scene.CC3ImportProps = bpy.props.PointerProperty(type=CC3ImportProps)

def unregister():
    bpy.utils.unregister_class(CC3NodeCoord)
    bpy.utils.unregister_class(CC3ObjectPointer)
    bpy.utils.unregister_class(CC3MaterialCache)
    bpy.utils.unregister_class(CC3ImportProps)
    bpy.utils.unregister_class(MyPanel)
    bpy.utils.unregister_class(MyPanel2)
    bpy.utils.unregister_class(MyPanel3)
    bpy.utils.unregister_class(MyPanel4)
    bpy.utils.unregister_class(CC3Import)
    bpy.utils.unregister_class(CC3Export)
    bpy.utils.unregister_class(CC3Scene)
    bpy.utils.unregister_class(CC3QuickSet)
    bpy.utils.unregister_class(CC3ToolsAddonPreferences)

    del(bpy.types.Scene.CC3ImportProps)


# This allows you to run the script directly from Blender"s Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()