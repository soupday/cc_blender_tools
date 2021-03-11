# All the global constants for the add-on...
#

VERSION_STRING = "v0.2.0"

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