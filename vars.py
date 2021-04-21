
VERSION_STRING = "v0.5.2"

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
MOD_HAIR_BLEND_MULTIPLY = ["blend_multiply"]
MOD_HAIR_FLOW_MAP = ["hair flow map"]
MOD_HAIR_ID_MAP = ["hair id map"]
MOD_HAIR_ROOT_MAP = ["hair root map"]
MOD_HAIR_VERTEX_COLOR_MAP = ["vertexcolormap"]

# blender uses metres, CC3 uses centimetres
UNIT_SCALE = 0.01

HAIR_GAMMA = 0.485
HAIR_SAT = 1.05
HAIR_VAL = 1.0

# https://docs.blender.org/manual/en/latest/files/media/image_formats.html
IMAGE_TYPES = [".bmp", ".sgi", ".rgb", ".bw", ".png", ".jpg", ".jpeg", ".jp2", ".j2c",
               ".tga", ".cin", ".dpx", ".exr", ".hdr", ".tif", ".tiff"]

# base names of all node groups in the library blend file
NODE_GROUPS = ["color_ao_mixer", "color_blend_ao_mixer", "color_refractive_eye_mixer", "color_eye_mixer", "color_teeth_mixer", "color_tongue_mixer", "color_head_mixer",
               "color_hair_mixer", "subsurface_mixer", "subsurface_overlay_mixer",
               "msr_mixer", "msr_skin_mixer", "msr_overlay_mixer",
               "normal_micro_mask_blend_mixer", "normal_micro_mask_mixer", "bump_mixer", "fake_bump_mixer",
               "normal_refractive_cornea_mixer", "normal_refractive_eye_mixer",
               "eye_occlusion_mask", "iris_refractive_mask", "iris_mask", "tiling_pivot_mapping", "tiling_mapping"]

# material types that share parameters
MATERIAL_PARAM_GROUPS = [
    ["SKIN_HEAD", "SKIN_BODY", "SKIN_ARM", "SKIN_LEG"],
    ["TEETH_UPPER", "TEETH_LOWER"],
    ["HAIR", "SCALP", "EYELASH"],
    ["CORNEA", "EYE", "TEARLINE", "OCCLUSION"],
    ["NAILS"],
    ["TONGUE"],
    ["DEFAULT"],
]

NODE_PREFIX = "cc3iid_"

GRID_SIZE = 300