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
from . import nodeutils, utils, params, vars

MIXER_CHANNELS = [
                    "RGB_HEADER",
                        ["Red Channel (Skin)", "rgb_red_enabled", "RGB_RED"],
                        ["Green Channel (Hair)", "rgb_green_enabled", "RGB_GREEN"],
                        ["Blue Channel (Mouth)", "rgb_blue_enabled", "RGB_BLUE"],

                     "ID_HEADER",
                        ["Red Color", "id_red_enabled", "ID_RED"],
                        ["Green Color", "id_green_enabled", "ID_GREEN"],
                        ["Blue Color", "id_blue_enabled", "ID_BLUE"],
                        ["Cyan Color", "id_cyan_enabled", "ID_CYAN"],
                        ["Yellow Color", "id_yellow_enabled", "ID_YELLOW"],
                        ["Magenta Color", "id_magenta_enabled", "ID_MAGENTA"],
                    ]

MIXER_UI = [
    ["PROP", "Threshold", "threshold"],
    ["PROP", "Intensity", "intensity"],
    ["PROP", "Normal", "normal"],
    ["HEADER",  "Base Color", "COLOR"],
    ["PROP", "Brightness", "color_brightness"],
    ["PROP", "Contrast", "color_contrast"],
    ["PROP", "Hue", "color_hue"],
    ["PROP", "Saturation", "color_saturation"],
    ["PROP", "Value", "color_value"],
    ["HEADER",  "Metallic", "SURFACE_DATA"],
    ["PROP", "Brightness", "metallic_brightness"],
    ["PROP", "Contrast", "metallic_contrast"],
    ["HEADER",  "Specular", "SURFACE_DATA"],
    ["PROP", "Brightness", "specular_brightness"],
    ["PROP", "Contrast", "specular_contrast"],
    ["HEADER",  "Roughness", "SURFACE_DATA"],
    ["PROP", "Brightness", "roughness_brightness"],
    ["PROP", "Contrast", "roughness_contrast"],
    ["HEADER",  "Emission", "LIGHT"],
    ["PROP", "Brightness", "emission_brightness"],
    ["PROP", "Contrast", "emission_contrast"],
]

MIXER_INPUTS = ["Base Color", "Metallic", "Specular", "Roughness", "Alpha", "Emission", "Normal"]

MIXER_PARAMS = [
    ["Mask Threshold", "threshold"],
    ["Intensity", "intensity"],
    ["Color Brightness", "color_brightness"],
    ["Color Contrast", "color_contrast"],
    ["Color Hue", "color_hue"],
    ["Color Saturation", "color_saturation"],
    ["Color Value", "color_value"],
    ["Metallic Brightness", "metallic_brightness"],
    ["Metallic Contrast", "metallic_contrast"],
    ["Specular Brightness", "specular_brightness"],
    ["Specular Contrast", "specular_contrast"],
    ["Roughness Brightness", "roughness_brightness"],
    ["Roughness Contrast", "roughness_contrast"],
    ["Emission Brightness", "emission_brightness"],
    ["Emission Contrast", "emission_contrast"],
    ["Normal Strength", "normal"],
]

MIXER_MASKS = {
    "RGB_RED": (1,0,0,1),
    "RGB_GREEN": (0,1,0,1),
    "RGB_BLUE": (0,0,1,1),
    "ID_RED": (1,0,0,1),
    "ID_GREEN": (0,1,0,1),
    "ID_BLUE": (0,0,1,1),
    "ID_CYAN": (0,1,1,1),
    "ID_YELLOW": (1,1,0,1),
    "ID_MAGENTA": (1,0,1,1),
}


def update_mixer(mixer, context, field):
    props = bpy.context.scene.CC3ImportProps

    mixer_type_channel = f"{mixer.type}_{mixer.channel}"

    # find the current character and material in context
    chr_cache = props.get_context_character_cache(context)
    if chr_cache:
        mat = utils.context_material(context)
        if mat and mat.use_nodes:
            mixer_node = nodeutils.find_node_by_type_and_keywords(mat.node_tree.nodes, "GROUP", mixer_type_channel)
            if mixer_node:
                apply_mixer(mixer, mixer_node)


def enable_disable_mixer_image(mixer_settings, context):
    props = bpy.context.scene.CC3ImportProps

    # find the current character and material in context
    chr_cache = props.get_context_character_cache(context)
    if chr_cache:
        context_mat = utils.context_material(context)
        if context_mat:
            rebuild_mixers(chr_cache, context_mat, mixer_settings)


def enable_disable_mixer(mixer_settings, context, type_channel):
    props = bpy.context.scene.CC3ImportProps

    # find an existing mixer
    mixer_type, mixer_channel = type_channel.split("_")
    mixer = mixer_settings.get_mixer(mixer_type, mixer_channel)

    enabled = False
    if type_channel == "RGB_RED": enabled = mixer_settings.rgb_red_enabled
    elif type_channel == "RGB_GREEN": enabled = mixer_settings.rgb_green_enabled
    elif type_channel == "RGB_BLUE": enabled = mixer_settings.rgb_blue_enabled
    elif type_channel == "ID_RED": enabled = mixer_settings.id_red_enabled
    elif type_channel == "ID_GREEN": enabled = mixer_settings.id_green_enabled
    elif type_channel == "ID_BLUE": enabled = mixer_settings.id_blue_enabled
    elif type_channel == "ID_CYAN": enabled = mixer_settings.id_cyan_enabled
    elif type_channel == "ID_YELLOW": enabled = mixer_settings.id_yellow_enabled
    elif type_channel == "ID_MAGENTA": enabled = mixer_settings.id_magenta_enabled

    # add or remove the given mixer
    if mixer:
        mixer.enabled = enabled
    elif not mixer and enabled:
        mixer = mixer_settings.add_mixer(mixer_type, mixer_channel)

    # find the current character and material in context
    chr_cache = props.get_context_character_cache(context)
    if chr_cache:
        context_mat = utils.context_material(context)
        if context_mat:
            rebuild_mixers(chr_cache, context_mat, mixer_settings)


def remove_mixer(chr_cache, mat, mixer_settings, type_channel):
    mixer_type, mixer_channel = type_channel.split("_")

    if type_channel == "RGB_RED": mixer_settings.rgb_red_enabled = False
    elif type_channel == "RGB_GREEN": mixer_settings.rgb_green_enabled = False
    elif type_channel == "RGB_BLUE": mixer_settings.rgb_blue_enabled = False
    elif type_channel == "ID_RED": mixer_settings.id_red_enabled = False
    elif type_channel == "ID_GREEN": mixer_settings.id_green_enabled = False
    elif type_channel == "ID_BLUE": mixer_settings.id_blue_enabled = False
    elif type_channel == "ID_CYAN": mixer_settings.id_cyan_enabled = False
    elif type_channel == "ID_YELLOW": mixer_settings.id_yellow_enabled = False
    elif type_channel == "ID_MAGENTA": mixer_settings.id_magenta_enabled = False

    mixer_settings.remove_mixer(mixer_type, mixer_channel)
    rebuild_mixers(chr_cache, mat, mixer_settings)

    pass


def rebuild_mixers(chr_cache, context_mat, mixer_settings):

    nodes = context_mat.node_tree.nodes
    links = context_mat.node_tree.links

    mixer_nodes = []

    rgb_enabled = mixer_settings.rgb_image is not None
    id_enabled = mixer_settings.id_image is not None
    rgb_image_node = None
    id_image_node = None

    rgb_image_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", vars.NODE_PREFIX, "MIXER_RGB_MASK")
    if rgb_enabled and not rgb_image_node:
        rgb_image_node = nodeutils.make_image_node(nodes, mixer_settings.rgb_image, "MIXER_RGB_MASK")
    elif not rgb_enabled and rgb_image_node:
        nodes.remove(rgb_image_node)
        rgb_image_node = None
    if rgb_image_node:
        rgb_image_node.location = (-100, -900)

    id_image_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", vars.NODE_PREFIX, "MIXER_ID_MASK")
    if id_enabled and not id_image_node:
        id_image_node = nodeutils.make_image_node(nodes, mixer_settings.id_image, "MIXER_ID_MASK")
    elif not id_enabled and id_image_node:
        nodes.remove(id_image_node)
        id_image_node = None
    if id_image_node:
        id_image_node.location = (-100, -1200)

    for channel_ref in MIXER_CHANNELS:

        if type(channel_ref) == list:

            mixer_type_channel = channel_ref[2]
            mixer_type, mixer_channel = mixer_type_channel.split("_")
            show_mixer_type = False
            if mixer_type == "RGB":
                show_mixer_type = rgb_enabled
            elif mixer_type == "ID":
                show_mixer_type = id_enabled

            mixer = mixer_settings.get_mixer(mixer_type, mixer_channel)
            mixer_node = nodeutils.find_node_by_type_and_keywords(nodes, "GROUP", mixer_type_channel)

            if mixer:
                if show_mixer_type:
                    if mixer.enabled and not mixer_node:
                        mixer_node = add_mixer_node(nodes, mixer_type, mixer_channel)
                    elif not mixer.enabled and mixer_node:
                        nodes.remove(mixer_node)
                        mixer_node = None
                else:
                    if mixer_node:
                        nodes.remove(mixer_node)
                        mixer_node = None

            if mixer and mixer_node:
                apply_mixer(mixer, mixer_node)
                mixer_nodes.append(mixer_node)

    connect_mixers(chr_cache, context_mat, mixer_nodes, rgb_image_node, id_image_node, mixer_settings)


def apply_mixer(mixer, mixer_node):
    for param in MIXER_PARAMS:
        socket = param[0]
        prop = param[1]
        eval_code = ""
        try:
            eval_code = f"mixer.{prop}"
            value = eval(eval_code, None, locals())
            nodeutils.set_node_input(mixer_node, socket, value)
        except:
            utils.log_error("Unable to evaluate: " + eval_code)
        nodeutils.set_node_input(mixer_node, "Mask Color", mixer.mask)
        nodeutils.set_node_input(mixer_node, "Id Color", mixer.mask)


def add_mixer_node(nodes, remap_type, remap_channel):
    label = f"Mixer {remap_type}/{remap_channel}"
    name = f"rl_mixer_{remap_type}_{remap_channel}"

    group = None
    mixer_node = None
    if remap_type == "RGB":
        group = nodeutils.get_node_group("rl_rgb_mixer")
    elif remap_type == "ID":
        group = nodeutils.get_node_group("rl_id_mixer")

    if group:
        mixer_node = nodeutils.make_node_group_node(nodes, group, label, name)

    return mixer_node


def connect_mixers(chr_cache, mat, mixer_nodes, rgb_image_node, id_image_node, mixer_config):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    mat_cache = chr_cache.get_material_cache(mat)
    shader = params.get_shader_lookup(mat_cache)
    bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader)
    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")
    # daisy chain and position the mixers from the shader_node > mixers > bsdf_node
    mixer_nodes.append(bsdf_node)
    left_node = shader_node
    location = [200, -500]
    for mixer_node in mixer_nodes:
        if "Mask Map" in mixer_node.inputs and rgb_image_node:
            nodeutils.link_nodes(links, rgb_image_node, "Color", mixer_node, "Mask Map")
        elif "Id Map" in mixer_node.inputs and id_image_node:
            nodeutils.link_nodes(links, id_image_node, "Color", mixer_node, "Id Map")
        mixer_node.location = location.copy()
        location[0] += 300
        right_node = mixer_node
        for input in MIXER_INPUTS:
            nodeutils.link_nodes(links, left_node, input, right_node, input)
        left_node = mixer_node
    location[1] = 400
    bsdf_node.location = location
    location[0] += 700
    location[1] = -400
    output_node.location = location


class CC3OperatorChannelMixer(bpy.types.Operator):
    """Channel Mixer"""
    bl_idname = "cc3.mixer"
    bl_label = "Channel Mixer"
    bl_options = {"REGISTER", "UNDO"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    type_channel: bpy.props.StringProperty(
            name = "type_channel",
            default = ""
        )

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps

        # find the current character and material in context
        chr_cache = props.get_context_character_cache(context)
        context_mat = utils.context_material(context)

        if chr_cache and context_mat:

            context_mat_cache = chr_cache.get_material_cache(context_mat)
            if context_mat_cache:

                if self.param == "REMOVE":
                    remove_mixer(chr_cache, context_mat, context_mat_cache.mixer_settings, self.type_channel)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "REMOVE":
            return "Remove and reset mixer: " + properties.type_channel
        return ""


class CC3MixerBase:
    #open_mouth: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=open_mouth_update)
    #import_file: bpy.props.StringProperty(default="", subtype="FILE_PATH")
    enabled: bpy.props.BoolProperty(default=False)
    expanded: bpy.props.BoolProperty(default=True)
    intensity: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_mixer(s,c,"intensity"))
    color_brightness: bpy.props.FloatProperty(default=0.0, min=-2, max=2, update=lambda s,c: update_mixer(s,c,"color_brightness"))
    color_contrast: bpy.props.FloatProperty(default=0.0, min=-2, max=2, update=lambda s,c: update_mixer(s,c,"color_contrast"))
    color_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_mixer(s,c,"color_hue"))
    color_saturation: bpy.props.FloatProperty(default=1.0, min=0, max=4, update=lambda s,c: update_mixer(s,c,"color_saturation"))
    color_value: bpy.props.FloatProperty(default=1.0, min=0, max=4, update=lambda s,c: update_mixer(s,c,"color_value"))
    metallic_brightness: bpy.props.FloatProperty(default=0.0, min=-2, max=2, update=lambda s,c: update_mixer(s,c,"metallic_brightness"))
    metallic_contrast: bpy.props.FloatProperty(default=0.0, min=-2, max=2, update=lambda s,c: update_mixer(s,c,"metallic_contrast"))
    specular_brightness: bpy.props.FloatProperty(default=0.0, min=-2, max=2, update=lambda s,c: update_mixer(s,c,"specular_brightness"))
    specular_contrast: bpy.props.FloatProperty(default=0.0, min=-2, max=2, update=lambda s,c: update_mixer(s,c,"specular_contrast"))
    roughness_brightness: bpy.props.FloatProperty(default=0.0, min=-2, max=2, update=lambda s,c: update_mixer(s,c,"roughness_brightness"))
    roughness_contrast: bpy.props.FloatProperty(default=0.0, min=-2, max=2, update=lambda s,c: update_mixer(s,c,"roughness_contrast"))
    emission_brightness: bpy.props.FloatProperty(default=0.0, min=-2, max=2, update=lambda s,c: update_mixer(s,c,"emission_brightness"))
    emission_contrast: bpy.props.FloatProperty(default=0.0, min=-2, max=2, update=lambda s,c: update_mixer(s,c,"emission_contrast"))
    normal: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_mixer(s,c,"intensity"))


class CC3RGBMixer(bpy.types.PropertyGroup, CC3MixerBase):
    type: bpy.props.StringProperty(default="RGB")
    channel: bpy.props.EnumProperty(items=[
                        ("RED","Red","Use the red channel as the mask"),
                        ("GREEN","Green","Use the green channel as the mask"),
                        ("BLUE","Blue","Use the blue channel as the mask"),
                    ], default="RED")
    mask: bpy.props.FloatVectorProperty(default=(0,0,0,1), subtype="COLOR", size=4)
    threshold: bpy.props.FloatProperty(default=0.75, min=0, max=0.993, update=lambda s,c: update_mixer(s,c,"mask_threshold"))


class CC3IDMixer(bpy.types.PropertyGroup, CC3MixerBase):
    type: bpy.props.StringProperty(default="ID")
    channel: bpy.props.EnumProperty(items=[
                        ("RED","Red","Use the red color as the mask"),
                        ("GREEN","Green","Use the green color as the mask"),
                        ("BLUE","Blue","Use the blue color as the mask"),
                        ("CYAN","Cyan","Use the cyan color as the mask"),
                        ("YELLOW","Yellow","Use the yellow color as the mask"),
                        ("MAGENTA","Magenta","Use the magenta color as the mask"),
                    ], default="RED")
    mask: bpy.props.FloatVectorProperty(default=(0,0,0,1), subtype="COLOR", size=4)
    threshold: bpy.props.FloatProperty(default=0.6, min=0, max=0.993, update=lambda s,c: update_mixer(s,c,"mask_threshold"))


class CC3MixerSettings(bpy.types.PropertyGroup):
    rgb_mixers: bpy.props.CollectionProperty(type=CC3RGBMixer)
    id_mixers: bpy.props.CollectionProperty(type=CC3IDMixer)
    rgb_image: bpy.props.PointerProperty(type=bpy.types.Image, update=enable_disable_mixer_image)
    id_image: bpy.props.PointerProperty(type=bpy.types.Image, update=enable_disable_mixer_image)
    rgb_red_enabled: bpy.props.BoolProperty(default=False, update=lambda s,c: enable_disable_mixer(s,c,"RGB_RED"))
    rgb_green_enabled: bpy.props.BoolProperty(default=False, update=lambda s,c: enable_disable_mixer(s,c,"RGB_GREEN"))
    rgb_blue_enabled: bpy.props.BoolProperty(default=False, update=lambda s,c: enable_disable_mixer(s,c,"RGB_BLUE"))
    id_red_enabled: bpy.props.BoolProperty(default=False, update=lambda s,c: enable_disable_mixer(s,c,"ID_RED"))
    id_green_enabled: bpy.props.BoolProperty(default=False, update=lambda s,c: enable_disable_mixer(s,c,"ID_GREEN"))
    id_blue_enabled: bpy.props.BoolProperty(default=False, update=lambda s,c: enable_disable_mixer(s,c,"ID_BLUE"))
    id_cyan_enabled: bpy.props.BoolProperty(default=False, update=lambda s,c: enable_disable_mixer(s,c,"ID_CYAN"))
    id_yellow_enabled: bpy.props.BoolProperty(default=False, update=lambda s,c: enable_disable_mixer(s,c,"ID_YELLOW"))
    id_magenta_enabled: bpy.props.BoolProperty(default=False, update=lambda s,c: enable_disable_mixer(s,c,"ID_MAGENTA"))

    def get_mixer(self, type, channel):
        if type == "RGB":
            for remap in self.rgb_mixers:
                if remap.channel == channel:
                    return remap
        else:
            for remap in self.id_mixers:
                if remap.channel == channel:
                    return remap
        return None

    def add_mixer(self, type, channel):
        remap = self.get_mixer(type, channel)

        if remap is None:
            if type == "RGB":
                remap = self.rgb_mixers.add()
            else:
                remap = self.id_mixers.add()
            remap.mask = MIXER_MASKS[f"{type}_{channel}"]
            remap.channel = channel
            remap.enabled = True
            return remap
        else:
            remap.enabled = True

        return remap

    def disable_mixer(self, type, channel):
        remap = self.get_mixer(type, channel)
        if remap:
            remap.enabled = False

    def remove_mixer(self, type, channel):
        if type == "RGB":
            for index in range(0, len(self.rgb_mixers)):
                remap = self.rgb_mixers[index]
                if remap.channel == channel:
                    self.rgb_mixers.remove(index)
                    return True
        else:
            for index in range(0, len(self.id_mixers)):
                remap = self.id_mixers[index]
                if remap.channel == channel:
                    self.id_mixers.remove(index)
                    return True
        return False

