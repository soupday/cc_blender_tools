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

import bpy, os, socket
from mathutils import Vector

from . import (link, channel_mixer, imageutils, meshutils, sculpting, materials,
               springbones, rigify_mapping_data, modifiers, nodeutils, shaders,
               params, physics, basic, jsonutils, utils, vars)


def open_mouth_update(self, context):
    props: CC3ImportProps = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_context_character_cache(context)

    bone = utils.find_pose_bone(chr_cache, "CC_Base_JawRoot", "JawRoot")
    if bone is not None:
        constraint = None

        for con in bone.constraints:
            if "iCC3_open_mouth_contraint" in con.name:
                constraint = con

        if chr_cache.open_mouth == 0:
            if constraint is not None:
                constraint.influence = chr_cache.open_mouth
                bone.constraints.remove(constraint)
        else:
            if constraint is None:
                constraint = bone.constraints.new(type="LIMIT_ROTATION")
                constraint.name = "iCC3_open_mouth_contraint"
                constraint.use_limit_z = True
                constraint.min_z = 0.43633
                constraint.max_z = 0.43633
                constraint.owner_space = "LOCAL"
            constraint.influence = chr_cache.open_mouth


def eye_close_update(self, context):
    props: CC3ImportProps = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_context_character_cache(context)
    value = chr_cache.eye_close

    objects = []
    for obj_cache in chr_cache.object_cache:
        if obj_cache.is_mesh():
            if obj_cache.object_type == "BODY":
                objects.append(obj_cache.get_object())
            elif obj_cache.object_type == "EYE_OCCLUSION":
                objects.append(obj_cache.get_object())
            elif obj_cache.object_type == "TEARLINE":
                objects.append(obj_cache.get_object())

    blink_shapes = ["Eye_Blink", "Eye_Blink_L", "Eye_Blink_R"]

    for obj in objects:
        if obj and obj.data.shape_keys and obj.data.shape_keys.key_blocks:
            for key in blink_shapes:
                if key in obj.data.shape_keys.key_blocks:
                    try:
                        obj.data.shape_keys.key_blocks[key].value = value
                    except:
                        pass


def update_property(self, context, prop_name, update_mode = None):
    if vars.block_property_update: return

    props = bpy.context.scene.CC3ImportProps
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)

    if chr_cache:

        # get the context (currently active) material
        context_obj = context.object
        context_mat = utils.get_context_material(context)
        context_mat_cache = chr_cache.get_material_cache(context_mat)

        if context_obj and context_mat and context_mat_cache:

            if update_mode is None:
                update_mode = props.update_mode

            all_materials_cache = chr_cache.get_all_materials_cache()
            linked_types = get_linked_material_types(context_mat_cache)
            paired_types = get_paired_material_types(context_mat_cache)
            linked_names = get_linked_material_names(context_mat_cache.get_base_name())

            for mat_cache in all_materials_cache:
                mat = mat_cache.material

                if mat:

                    if mat == context_mat:
                        # Always update the currently active material
                        update_shader_property(context_obj, mat, mat_cache, prop_name)

                    elif mat_cache.material_type in paired_types:
                        # Update paired materials
                        set_linked_property(prop_name, context_mat_cache, mat_cache)
                        update_shader_property(context_obj, mat, mat_cache, prop_name)

                    elif update_mode == "UPDATE_LINKED":
                        # Update all other linked materials in the imported objects material cache:
                        if mat_cache.material_type in linked_types or mat_cache.get_base_name() in linked_names:
                            set_linked_property(prop_name, context_mat_cache, mat_cache)
                            update_shader_property(context_obj, mat, mat_cache, prop_name)

            # these properties will cause the eye displacement vertex group to change...
            if prop_name in ["eye_iris_depth_radius", "eye_iris_scale", "eye_iris_radius"]:
                meshutils.rebuild_eye_vertex_groups(chr_cache)


def update_basic_property(self, context, prop_name, update_mode=None):
    if vars.block_property_update: return

    props = bpy.context.scene.CC3ImportProps
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)
    if chr_cache:
        all_materials_cache = chr_cache.get_all_materials_cache()
        for mat_cache in all_materials_cache:
            mat = mat_cache.material
            if mat:
                basic.update_basic_material(mat, mat_cache, prop_name)


def update_material_property(self, context, prop_name, update_mode=None):
    if vars.block_property_update: return
    props = bpy.context.scene.CC3ImportProps
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)
    if chr_cache:
        context_obj = context.object
        context_mat = utils.get_context_material(context)
        context_mat_cache = chr_cache.get_material_cache(context_mat)
        if context_mat_cache:
            try:
                value = eval("context_mat_cache." + prop_name, None, locals())
                context_mat["rl_" + prop_name] = value
            except:
                pass


def update_object_property(self, context, prop_name, update_mode=None):
    if vars.block_property_update: return
    props = bpy.context.scene.CC3ImportProps
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)
    if chr_cache:
        context_obj = context.object
        context_obj_cache = chr_cache.get_object_cache(context_obj)
        if context_obj_cache:
            try:
                value = eval("context_obj_cache." + prop_name, None, locals())
                context_obj["rl_" + prop_name] = value
            except:
                pass


def get_linked_material_types(mat_cache):
    if mat_cache:
        for linked in params.LINKED_MATERIALS:
            if mat_cache.material_type in linked:
                return linked
    return []


def get_paired_material_types(mat_cache):
    if mat_cache:
        for paired in params.PAIRED_MATERIALS:
            if mat_cache.material_type in paired:
                return paired
    return []


def get_linked_material_names(mat_name):
    for linked in params.LINKED_MATERIAL_NAMES:
        if mat_name in linked:
            return linked
    return []


def set_linked_property(prop_name, active_mat_cache, mat_cache):
    vars.block_property_update = True
    code = ""

    try:
        parameters = mat_cache.parameters
        active_parameters = active_mat_cache.parameters
        code = "parameters." + prop_name + " = active_parameters." + prop_name
        exec(code, None, locals())
    except Exception as e:
        utils.log_error("set_linked_property(): Unable to evaluate: " + code, e)

    vars.block_property_update = False


def update_shader_property(obj, mat, mat_cache, prop_name):
    props = bpy.context.scene.CC3ImportProps

    if mat and mat.node_tree and mat_cache:

        shader_name = params.get_shader_name(mat_cache)
        bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader_name)
        shader_def = params.get_shader_def(shader_name)

        if shader_def:

            if "inputs" in shader_def.keys():
                update_shader_input(shader_node, mat_cache, prop_name, shader_def["inputs"])

            if "bsdf" in shader_def.keys():
                if bsdf_node:
                    if bsdf_node.type == "GROUP":
                        bsdf_nodes = nodeutils.get_custom_bsdf_nodes(bsdf_node)
                        for bsdf_node in bsdf_nodes:
                            update_bsdf_input(bsdf_node, mat_cache, prop_name, shader_def["bsdf"])
                    else:
                        update_bsdf_input(bsdf_node, mat_cache, prop_name, shader_def["bsdf"])


            if "textures" in shader_def.keys():
                update_shader_tiling(shader_name, mat, mat_cache, prop_name, shader_def["textures"])

            if "mapping" in shader_def.keys():
                update_shader_mapping(shader_name, mat, mat_cache, prop_name, shader_def["mapping"])

            if "modifiers" in shader_def.keys():
                update_object_modifier(obj, mat_cache, prop_name, shader_def["modifiers"])

            if "settings" in shader_def.keys():
                update_material_setting(mat, mat_cache, prop_name, shader_def["settings"])

        else:
            utils.log_error("No shader definition for: " + shader_name)


def update_shader_input(shader_node, mat_cache, prop_name, input_defs):
    if shader_node:
        for input_def in input_defs:
            if prop_name in input_def[2:]:
                nodeutils.set_node_input_value(shader_node, input_def[0], shaders.eval_input_param(input_def, mat_cache))


def update_bsdf_input(bsdf_node, mat_cache, prop_name, bsdf_defs):
    if bsdf_node:
        for input_def in bsdf_defs:
            if prop_name in input_def[2:]:
                nodeutils.set_node_input_value(bsdf_node,
                                               input_def[0],
                                               shaders.eval_input_param(input_def, mat_cache))


def update_shader_tiling(shader_name, mat, mat_cache, prop_name, texture_defs):
    for texture_def in texture_defs:
        if len(texture_def) > 5:
            tiling_props = texture_def[5:]
            texture_type = texture_def[2]
            if prop_name in tiling_props:
                tiling_node = nodeutils.get_tiling_node(mat, shader_name, texture_type)
                nodeutils.set_node_input_value(tiling_node, "Tiling", shaders.eval_tiling_param(texture_def, mat_cache))


def update_shader_mapping(shader_name, mat, mat_cache, prop_name, mapping_defs):
    mapping_node = None
    for mapping_def in mapping_defs:
        if len(mapping_def) == 1:
            texture_type = mapping_def[0]
            mapping_node = nodeutils.get_tiling_node(mat, shader_name, texture_type)
        elif mapping_node:
            tiling_props = mapping_def[3:]
            if prop_name in tiling_props:
                socket_name = mapping_def[1]
                nodeutils.set_node_input_value(mapping_node, socket_name, shaders.eval_tiling_param(mapping_def, mat_cache, 2))


def update_object_modifier(obj, mat_cache, prop_name, mod_defs):
    for mod_def in mod_defs:
        if mod_def[0] == prop_name:
            material_type = mod_def[1]
            mod_type = mod_def[2]
            mod_name = mod_def[3]
            code = mod_def[4]

            if mat_cache.material_type == material_type:
                mod = modifiers.get_object_modifier(obj, mod_type, mod_name)
                if mod:
                    try:
                        parameters = mat_cache.parameters
                        exec(code, None, locals())
                    except:
                        utils.log_error("update_object_modifier(): unable to execute: " + code)


def update_material_setting(mat, mat_cache, prop_name, setting_defs):
    # mat is used in the exec code expression so keep it!
    for setting_def in setting_defs:
        if setting_def[0] == prop_name:
            material_type = setting_def[1]
            code = setting_def[2]

            if mat_cache.material_type == material_type:
                try:
                    parameters = mat_cache.parameters
                    exec(code, None, locals())
                except:
                    utils.log_error("update_material_setting(): unable to execute: " + code)


def reset_parameters(context = bpy.context):

    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_context_character_cache(context)
    chr_json = chr_cache.get_character_json()

    if chr_cache:

        vars.block_property_update = True

        shaders.init_character_property_defaults(chr_cache, chr_json)
        basic.init_basic_default(chr_cache)

        vars.block_property_update = False

        update_all_properties(context)

    return


def update_all_properties(context, update_mode = None):
    if vars.block_property_update: return

    utils.start_timer()

    props = bpy.context.scene.CC3ImportProps
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)

    if chr_cache:

        processed = []

        for obj_cache in chr_cache.object_cache:
            obj = obj_cache.get_object()
            if obj_cache.is_mesh() and obj not in processed:

                processed.append(obj)

                for mat in obj.data.materials:
                    if mat and mat not in processed:
                        processed.append(mat)
                        mat_cache = chr_cache.get_material_cache(mat)

                        if chr_cache.setup_mode == "BASIC":

                            basic.update_basic_material(mat, mat_cache, "ALL")

                        else:

                            shader_name = params.get_shader_name(mat_cache)
                            bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader_name)
                            shader_def = params.get_shader_def(shader_name)

                            shaders.apply_prop_matrix(bsdf_node, shader_node, mat_cache, shader_name)

                            if "textures" in shader_def.keys():
                                for tex_def in shader_def["textures"]:
                                    tiling_props = tex_def[5:]
                                    for prop_name in tiling_props:
                                        update_shader_property(obj, mat, mat_cache, prop_name)

                            if "modifiers" in shader_def.keys():
                                for mod_def in shader_def["modifiers"]:
                                    prop_name = mod_def[0]
                                    update_shader_property(obj, mat, mat_cache, prop_name)

                            if "settings" in shader_def.keys():
                                for mat_def in shader_def["settings"]:
                                    prop_name = mat_def[0]
                                    update_shader_property(obj, mat, mat_cache, prop_name)

                if obj_cache.is_eye():
                    meshutils.rebuild_eye_vertex_groups(chr_cache)

    utils.log_timer("update_all_properties()", "ms")


def init_material_property_defaults(obj, mat, obj_cache, mat_cache, obj_json, mat_json):
    if obj and obj_cache and mat and mat_cache:
        utils.log_info("Re-Initializing Material Property Defaults: " + mat.name + " (" + mat_cache.material_type + ")")
        if mat_cache.is_eye():
            cornea_mat, cornea_mat_cache = materials.get_cornea_mat(obj, mat, mat_cache)
            mat_json = jsonutils.get_material_json(obj_json, cornea_mat)
        shaders.fetch_prop_defaults(obj, mat_cache, mat_json)


def update_sculpt_mix_node(self, context, prop_name):
    if vars.block_property_update: return
    props = bpy.context.scene.CC3ImportProps
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)
    body = chr_cache.get_body()
    if chr_cache:
        if prop_name == "detail_normal_strength":
            sculpting.update_layer_nodes(body, "DETAIL", "Normal Strength", chr_cache.detail_normal_strength * 1)
        elif prop_name == "body_normal_strength":
            sculpting.update_layer_nodes(body, "BODY", "Normal Strength", chr_cache.body_normal_strength * 1)
        elif prop_name == "detail_ao_strength":
            sculpting.update_layer_nodes(body, "DETAIL", "AO Strength", chr_cache.detail_ao_strength * 1)
        elif prop_name == "body_ao_strength":
            sculpting.update_layer_nodes(body, "BODY", "AO Strength", chr_cache.body_ao_strength * 1)
        elif prop_name == "detail_normal_definition":
            sculpting.update_layer_nodes(body, "DETAIL", "Definition", chr_cache.detail_normal_definition * 1)
        elif prop_name == "body_normal_definition":
            sculpting.update_layer_nodes(body, "BODY", "Definition", chr_cache.body_normal_definition * 1)
        elif prop_name == "detail_mix_mode":
            sculpting.update_layer_nodes(body, "DETAIL", "Mix Mode", (1.0 if chr_cache.detail_mix_mode == "REPLACE" else 0.0))
        elif prop_name == "body_mix_mode":
            sculpting.update_layer_nodes(body, "BODY", "Mix Mode", (1.0 if chr_cache.body_mix_mode == "REPLACE" else 0.0))


def update_rig_target(self, context):
    props = bpy.context.scene.CC3ImportProps
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)
    if chr_cache:
        if self.hair_rig_target == "CC4":
            self.hair_rig_bone_length = 7.5
            self.hair_rig_bind_skip_length = 0.0
            self.hair_rig_bind_trunc_length = 0.5
            self.hair_rig_bind_bone_radius = 11.25
            self.hair_rig_bind_existing_scale = 0.0
            self.hair_rig_bind_bone_count = 2
            self.hair_rig_bind_bone_weight = 1.0
            self.hair_rig_bind_smoothing = 5
            self.hair_rig_bind_weight_curve = 0.5
            self.hair_rig_bind_bone_variance = 0.75
        elif self.hair_rig_target == "UNITY":
            self.hair_rig_bone_length = 7.5
            self.hair_rig_bind_skip_length = 7.5
            self.hair_rig_bind_trunc_length = 0.5
            self.hair_rig_bind_bone_radius = 11.25
            self.hair_rig_bind_existing_scale = 0.1
            self.hair_rig_bind_bone_count = 2
            self.hair_rig_bind_bone_weight = 1.0
            self.hair_rig_bind_smoothing = 5
            self.hair_rig_bind_weight_curve = 0.5
            self.hair_rig_bind_bone_variance = 0.75
        elif self.hair_rig_target == "BLENDER":
            self.hair_rig_bone_length = 7.5
            self.hair_rig_bind_skip_length = 7.5/2.0
            self.hair_rig_bind_trunc_length = 2.5
            self.hair_rig_bind_bone_radius = 11.25
            self.hair_rig_bind_existing_scale = 0.1
            self.hair_rig_bind_bone_count = 2
            self.hair_rig_bind_bone_weight = 1.0
            self.hair_rig_bind_smoothing = 5
            self.hair_rig_bind_weight_curve = 0.5
            self.hair_rig_bind_bone_variance = 0.75

def update_link_target(self, context):
    link_props = bpy.context.scene.CCICLinkProps
    if link_props.link_target == "BLENDER":
        link_props.link_port = 9334
    elif link_props.link_target == "CCIC":
        link_props.link_port = 9333
    elif link_props.link_target == "UNITY":
        link_props.link_port = 9335
    else:
        link_props.link_port = 9333


def update_link_host(self, context):
    link_props = bpy.context.scene.CCICLinkProps
    host = link_props.link_host
    if host:
        try:
            link_props.link_host_ip = socket.gethostbyname(host)
        except:
            link_props.link_host_ip = "127.0.0.1"


def update_link_host_ip(self, context):
    link_props = bpy.context.scene.CCICLinkProps
    host_ip = link_props.link_host_ip
    if host_ip:
        try:
            link_props.link_host = socket.gethostbyaddr(host_ip)
        except:
            link_props.link_host = ""


class CC3OperatorProperties(bpy.types.Operator):
    """CC3 Property Functions"""
    bl_idname = "cc3.setproperties"
    bl_label = "CC3 Property Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):

        if self.param == "RESET":
            reset_parameters(context)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "RESET":
            return "Reset parameters to the defaults"
        return ""


class CC3ActionList(bpy.types.PropertyGroup):
    action: bpy.props.PointerProperty(type=bpy.types.Armature)
    action_type: bpy.props.EnumProperty(items=vars.ENUM_ACTION_TYPES, default="NONE")
    armature_type: bpy.props.EnumProperty(items=vars.ENUM_ARMATURE_TYPES, default="NONE")


class CC3ArmatureList(bpy.types.PropertyGroup):
    armature: bpy.props.PointerProperty(type=bpy.types.Armature)
    armature_type: bpy.props.EnumProperty(items=vars.ENUM_ARMATURE_TYPES, default="NONE")
    actions: bpy.props.CollectionProperty(type=CC3ActionList)


class CC3HeadParameters(bpy.types.PropertyGroup):
    # shader (rl_head_shader)
    skin_diffuse_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1, 1, 1, 1), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"skin_diffuse_color"))
    skin_diffuse_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_diffuse_hue"))
    skin_diffuse_brightness: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_diffuse_brightness"))
    skin_diffuse_saturation: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_diffuse_saturation"))
    skin_diffuse_hsv_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_diffuse_hsv_strength"))
    skin_cavity_ao_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_cavity_ao_strength"))
    skin_blend_overlay_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_blend_overlay_strength"))
    skin_ao_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_ao_strength"))
    skin_ao_power: bpy.props.FloatProperty(default=1, min=0, max=8, update=lambda s,c: update_property(s,c,"skin_ao_power"))
    skin_mouth_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=lambda s,c: update_property(s,c,"skin_mouth_ao"))
    skin_nostril_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=lambda s,c: update_property(s,c,"skin_nostril_ao"))
    skin_lips_ao: bpy.props.FloatProperty(default=2.5, min=0, max=5, update=lambda s,c: update_property(s,c,"skin_lips_ao"))
    skin_subsurface_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1.0, 0.112, 0.072, 1.0), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"skin_subsurface_falloff"))
    skin_subsurface_radius: bpy.props.FloatProperty(default=1.5, min=0, max=3, update=lambda s,c: update_property(s,c,"skin_subsurface_radius"))
    skin_specular_scale: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_specular_scale"))
    skin_roughness_power: bpy.props.FloatProperty(default=0.8, min=0.01, max=2, update=lambda s,c: update_property(s,c,"skin_roughness_power"))
    skin_roughness_min: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_roughness_min"))
    skin_roughness_max: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_roughness_max"))
    # dual specular
    skin_specular_detail_mask: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_specular_detail_mask"))
    skin_specular_detail_min: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_specular_detail_min"))
    skin_specular_detail_max: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_specular_detail_max"))
    skin_specular_detail_power: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_specular_detail_power"))
    skin_secondary_specular_scale: bpy.props.FloatProperty(default=0.35, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_secondary_specular_scale"))
    skin_secondary_roughness_power: bpy.props.FloatProperty(default=2.0, min=0.0, max=4.0, update=lambda s,c: update_property(s,c,"skin_secondary_roughness_power"))
    skin_specular_mix: bpy.props.FloatProperty(default=0.4, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_specular_mix"))

    skin_normal_strength: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_normal_strength"))
    skin_micro_normal_strength: bpy.props.FloatProperty(default=0.5, min=0, max=1.0, update=lambda s,c: update_property(s,c,"skin_micro_normal_strength"))
    skin_normal_blend_strength: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_normal_blend_strength"))
    skin_unmasked_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_unmasked_scatter_scale"))
    skin_nose_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_nose_scatter_scale"))
    skin_mouth_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_mouth_scatter_scale"))
    skin_upper_lid_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_upper_lid_scatter_scale"))
    skin_inner_lid_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_inner_lid_scatter_scale"))
    skin_cheek_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_cheek_scatter_scale"))
    skin_forehead_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_forehead_scatter_scale"))
    skin_upper_lip_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_upper_lip_scatter_scale"))
    skin_chin_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_chin_scatter_scale"))
    skin_ear_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_ear_scatter_scale"))
    skin_neck_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_neck_scatter_scale"))
    skin_subsurface_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_subsurface_scale"))
    skin_micro_roughness_mod: bpy.props.FloatProperty(default=0.05, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_micro_roughness_mod"))
    skin_unmasked_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_unmasked_roughness_mod"))
    skin_nose_roughness_mod: bpy.props.FloatProperty(default=0.119, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_nose_roughness_mod"))
    skin_mouth_roughness_mod: bpy.props.FloatProperty(default=0.034, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_mouth_roughness_mod"))
    skin_upper_lid_roughness_mod: bpy.props.FloatProperty(default=-0.3, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_upper_lid_roughness_mod"))
    skin_inner_lid_roughness_mod: bpy.props.FloatProperty(default=-0.574, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_inner_lid_roughness_mod"))
    skin_cheek_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_cheek_roughness_mod"))
    skin_forehead_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_forehead_roughness_mod"))
    skin_upper_lip_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_upper_lip_roughness_mod"))
    skin_chin_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_chin_roughness_mod"))
    skin_ear_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_ear_roughness_mod"))
    skin_neck_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_neck_roughness_mod"))
    skin_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0,
                            update=lambda s,c: update_property(s,c,"skin_emissive_color"))
    skin_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_emission_strength"))
    # tiling (rl_head_shader_skin_micro_normal_tiling)
    skin_micro_normal_tiling: bpy.props.FloatProperty(default=20, min=0, max=50, update=lambda s,c: update_property(s,c,"skin_micro_normal_tiling"))
    skin_height_scale: bpy.props.FloatProperty(default=0.3, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_height_scale"))
    skin_height_delta_scale: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_height_delta_scale"))

class CC3SkinParameters(bpy.types.PropertyGroup):
    # shader (rl_skin_shader)
    skin_diffuse_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1, 1, 1, 1), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"skin_diffuse_color"))
    skin_diffuse_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_diffuse_hue"))
    skin_diffuse_brightness: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_diffuse_brightness"))
    skin_diffuse_saturation: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_diffuse_saturation"))
    skin_diffuse_hsv_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_diffuse_hsv_strength"))
    skin_ao_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_ao_strength"))
    skin_ao_power: bpy.props.FloatProperty(default=1, min=0, max=8, update=lambda s,c: update_property(s,c,"skin_ao_power"))
    skin_subsurface_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1.0, 0.112, 0.072, 1.0), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"skin_subsurface_falloff"))
    skin_subsurface_radius: bpy.props.FloatProperty(default=1.5, min=0, max=3, update=lambda s,c: update_property(s,c,"skin_subsurface_radius"))
    skin_specular_scale: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_specular_scale"))
    skin_roughness_power: bpy.props.FloatProperty(default=0.8, min=0.01, max=2, update=lambda s,c: update_property(s,c,"skin_roughness_power"))
    skin_roughness_min: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_roughness_min"))
    skin_roughness_max: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_roughness_max"))
    # dual specular
    skin_specular_detail_mask: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_specular_detail_mask"))
    skin_specular_detail_min: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_specular_detail_min"))
    skin_specular_detail_max: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_specular_detail_max"))
    skin_specular_detail_power: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_specular_detail_power"))
    skin_secondary_specular_scale: bpy.props.FloatProperty(default=0.35, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_secondary_specular_scale"))
    skin_secondary_roughness_power: bpy.props.FloatProperty(default=2.0, min=0.0, max=4.0, update=lambda s,c: update_property(s,c,"skin_secondary_roughness_power"))
    skin_specular_mix: bpy.props.FloatProperty(default=0.4, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_specular_mix"))

    skin_normal_strength: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_normal_strength"))
    skin_micro_normal_strength: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_micro_normal_strength"))
    skin_subsurface_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_subsurface_scale"))
    skin_unmasked_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_unmasked_scatter_scale"))
    skin_r_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_r_scatter_scale"))
    skin_g_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_g_scatter_scale"))
    skin_b_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_b_scatter_scale"))
    skin_a_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"skin_a_scatter_scale"))
    skin_micro_roughness_mod: bpy.props.FloatProperty(default=0.05, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_micro_roughness_mod"))
    skin_unmasked_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_unmasked_roughness_mod"))
    skin_r_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_r_roughness_mod"))
    skin_g_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_g_roughness_mod"))
    skin_b_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_b_roughness_mod"))
    skin_a_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"skin_a_roughness_mod"))
    skin_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0,
                            update=lambda s,c: update_property(s,c,"skin_emissive_color"))
    skin_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_emission_strength"))
    # tiling (rl_skin_shader_skin_micro_normal_tiling)
    skin_micro_normal_tiling: bpy.props.FloatProperty(default=25, min=0, max=50, update=lambda s,c: update_property(s,c,"skin_micro_normal_tiling"))


class CC3EyeParameters(bpy.types.PropertyGroup):
    eye_subsurface_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_subsurface_scale"))
    eye_subsurface_radius: bpy.props.FloatProperty(default=5.0, min=0.1, max=5, update=lambda s,c: update_property(s,c,"eye_subsurface_radius"))
    eye_subsurface_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_subsurface_falloff"))
    eye_cornea_specular: bpy.props.FloatProperty(default=0.8, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_cornea_specular"))
    eye_iris_specular: bpy.props.FloatProperty(default=0.2, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_iris_specular"))
    eye_sclera_roughness: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_sclera_roughness"))
    eye_iris_roughness: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_iris_roughness"))
    eye_cornea_roughness: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_cornea_roughness"))
    eye_ao_strength: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_ao_strength"))
    eye_sclera_scale: bpy.props.FloatProperty(default=1.0, min=0.25, max=2.0, update=lambda s,c: update_property(s,c,"eye_sclera_scale"))
    eye_sclera_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_sclera_hue"))
    eye_sclera_saturation: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_sclera_saturation"))
    eye_sclera_brightness: bpy.props.FloatProperty(default=0.75, min=0, max=5, update=lambda s,c: update_property(s,c,"eye_sclera_brightness"))
    eye_sclera_hsv: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_sclera_hsv"))
    eye_iris_scale: bpy.props.FloatProperty(default=1.0, min=0.25, max=2.0, update=lambda s,c: update_property(s,c,"eye_iris_scale"))
    eye_iris_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_iris_hue"))
    eye_iris_saturation: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_iris_saturation"))
    eye_iris_brightness: bpy.props.FloatProperty(default=1.0, min=0, max=5, update=lambda s,c: update_property(s,c,"eye_iris_brightness"))
    eye_iris_hsv: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_iris_hsv"))
    eye_iris_radius: bpy.props.FloatProperty(default=0.15, min=0.01, max=0.16, update=lambda s,c: update_property(s,c,"eye_iris_radius"))
    eye_iris_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_iris_color"))
    eye_iris_inner_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_iris_inner_color"))
    eye_iris_cloudy_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.0, 0.0, 0.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_iris_cloudy_color"))
    eye_iris_inner_scale: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_iris_inner_scale"))
    eye_limbus_width: bpy.props.FloatProperty(default=0.055, min=0.01, max=0.2, update=lambda s,c: update_property(s,c,"eye_limbus_width"))
    eye_limbus_dark_radius: bpy.props.FloatProperty(default=0.13125, min=0.1, max=0.2, update=lambda s,c: update_property(s,c,"eye_limbus_dark_radius"))
    eye_limbus_dark_width: bpy.props.FloatProperty(default=0.34375, min=0.01, max=0.99, update=lambda s,c: update_property(s,c,"eye_limbus_dark_width"))
    eye_limbus_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.0, 0.0, 0.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_limbus_color"))
    eye_shadow_radius: bpy.props.FloatProperty(default=0.3, min=0.0, max=0.5, update=lambda s,c: update_property(s,c,"eye_shadow_radius"))
    eye_shadow_hardness: bpy.props.FloatProperty(default=0.5, min=0.01, max=0.99, update=lambda s,c: update_property(s,c,"eye_shadow_hardness"))
    eye_corner_shadow_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 0.497, 0.445, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_corner_shadow_color"))
    eye_color_blend_strength: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_color_blend_strength"))
    eye_sclera_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_sclera_emissive_color"))
    eye_sclera_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_sclera_emission_strength"))
    eye_iris_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_iris_emissive_color"))
    eye_iris_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_iris_emission_strength"))
    eye_sclera_normal_strength: bpy.props.FloatProperty(default=0.1, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_sclera_normal_strength"))
    eye_sclera_normal_tiling: bpy.props.FloatProperty(default=2.0, min=0, max=10, update=lambda s,c: update_property(s,c,"eye_sclera_normal_tiling"))
    # non shader properties
    eye_refraction_depth: bpy.props.FloatProperty(default=1, min=0, max=5, update=lambda s,c: update_property(s,c,"eye_refraction_depth"))
    eye_ior: bpy.props.FloatProperty(default=1.4, min=1.01, max=2.5, update=lambda s,c: update_property(s,c,"eye_ior"))
    eye_blood_vessel_height: bpy.props.FloatProperty(default=0.5, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_blood_vessel_height"))
    eye_iris_bump_height: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_iris_bump_height"))
    eye_iris_depth: bpy.props.FloatProperty(default=0.45, min=0, max=1.25, update=lambda s,c: update_property(s,c,"eye_iris_depth"))
    eye_iris_depth_radius: bpy.props.FloatProperty(default=0.75, min=0.0, max=1.0, update=lambda s,c: update_property(s,c,"eye_iris_depth_radius"))
    eye_pupil_scale: bpy.props.FloatProperty(default=0.8, min=0.5, max=4.0, update=lambda s,c: update_property(s,c,"eye_pupil_scale"))


class CC3EyeOcclusionParameters(bpy.types.PropertyGroup):
    # Eye Occlusion Basic
    eye_occlusion: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion"))
    eye_occlusion_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.014451, 0.001628, 0.000837, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_occlusion_color"))
    eye_occlusion_hardness: bpy.props.FloatProperty(default=0.5, min=0.5, max=1.5, update=lambda s,c: update_property(s,c,"eye_occlusion_hardness"))
    # Eye Occlusion Advanced
    eye_occlusion_strength: bpy.props.FloatProperty(default=0.584, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_strength"))
    eye_occlusion_power: bpy.props.FloatProperty(default=1.75, min=0.1, max=4, update=lambda s,c: update_property(s,c,"eye_occlusion_power"))
    eye_occlusion_top_min: bpy.props.FloatProperty(default=0.27, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_top_min"))
    eye_occlusion_top_range: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_top_range"))
    eye_occlusion_top_curve: bpy.props.FloatProperty(default=0.7, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_occlusion_top_curve"))
    eye_occlusion_bottom_min: bpy.props.FloatProperty(default=0.05, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_bottom_min"))
    eye_occlusion_bottom_range: bpy.props.FloatProperty(default=0.335, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_bottom_range"))
    eye_occlusion_bottom_curve: bpy.props.FloatProperty(default=2.0, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_occlusion_bottom_curve"))
    eye_occlusion_inner_min: bpy.props.FloatProperty(default=0.25, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_inner_min"))
    eye_occlusion_inner_range: bpy.props.FloatProperty(default=0.625, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_inner_range"))
    eye_occlusion_outer_min: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_outer_min"))
    eye_occlusion_outer_range: bpy.props.FloatProperty(default=0.6, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_outer_range"))
    eye_occlusion_strength2: bpy.props.FloatProperty(default=0.766, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_strength2"))
    eye_occlusion_top2_min: bpy.props.FloatProperty(default=0.15, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_top2_min"))
    eye_occlusion_top2_range: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_top2_range"))
    eye_occlusion_tear_duct_position: bpy.props.FloatProperty(default=0.8, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_tear_duct_position"))
    eye_occlusion_tear_duct_width: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_occlusion_tear_duct_width"))
    eye_occlusion_inner: bpy.props.FloatProperty(default=0, min=-0.2, max=0.2, update=lambda s,c: update_property(s,c,"eye_occlusion_inner"))
    eye_occlusion_outer: bpy.props.FloatProperty(default=0, min=-0.2, max=0.2, update=lambda s,c: update_property(s,c,"eye_occlusion_outer"))
    eye_occlusion_top: bpy.props.FloatProperty(default=0, min=-0.2, max=0.2, update=lambda s,c: update_property(s,c,"eye_occlusion_top"))
    eye_occlusion_bottom: bpy.props.FloatProperty(default=0, min=-0.2, max=0.2, update=lambda s,c: update_property(s,c,"eye_occlusion_bottom"))
    eye_occlusion_displace: bpy.props.FloatProperty(default=0.02, min=-0.1, max=0.1, update=lambda s,c: update_property(s,c,"eye_occlusion_displace"))


class CC3TearlineParameters(bpy.types.PropertyGroup):
    # Tearline
    tearline_specular: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"tearline_specular"))
    tearline_glossiness: bpy.props.FloatProperty(default=0.025, min=0, max=0.05, update=lambda s,c: update_property(s,c,"tearline_glossiness"))
    tearline_alpha: bpy.props.FloatProperty(default=0.05, min=0, max=0.2, update=lambda s,c: update_property(s,c,"tearline_alpha"))
    tearline_roughness: bpy.props.FloatProperty(default=0.15, min=0, max=0.5, update=lambda s,c: update_property(s,c,"tearline_roughness"))
    tearline_inner: bpy.props.FloatProperty(default=0, min=-0.2, max=0.2, update=lambda s,c: update_property(s,c,"tearline_inner"))
    tearline_displace: bpy.props.FloatProperty(default=0.1, min=-0.2, max=0.2, update=lambda s,c: update_property(s,c,"tearline_displace"))

class CC3TeethParameters(bpy.types.PropertyGroup):
    # Teeth
    teeth_gums_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_gums_hue"))
    teeth_gums_brightness: bpy.props.FloatProperty(default=0.9, min=0, max=5, update=lambda s,c: update_property(s,c,"teeth_gums_brightness"))
    teeth_gums_saturation: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"teeth_gums_saturation"))
    teeth_gums_hsv_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_gums_hsv_strength"))
    teeth_teeth_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_teeth_hue"))
    teeth_teeth_brightness: bpy.props.FloatProperty(default=0.7, min=0, max=5, update=lambda s,c: update_property(s,c,"teeth_teeth_brightness"))
    teeth_teeth_saturation: bpy.props.FloatProperty(default=0.9, min=0, max=2, update=lambda s,c: update_property(s,c,"teeth_teeth_saturation"))
    teeth_teeth_hsv_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_teeth_hsv_strength"))
    teeth_front_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1.5, update=lambda s,c: update_property(s,c,"teeth_front_ao"))
    teeth_rear_ao: bpy.props.FloatProperty(default=0.0, min=0, max=1.5, update=lambda s,c: update_property(s,c,"teeth_rear_ao"))
    teeth_ao_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_ao_strength"))
    teeth_ao_power: bpy.props.FloatProperty(default=1, min=0, max=8, update=lambda s,c: update_property(s,c,"teeth_ao_power"))
    teeth_gums_subsurface_scatter: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_gums_subsurface_scatter"))
    teeth_teeth_subsurface_scatter: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_teeth_subsurface_scatter"))
    teeth_subsurface_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=3, update=lambda s,c: update_property(s,c,"teeth_subsurface_radius"))
    teeth_subsurface_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(0.381, 0.198, 0.13, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"teeth_subsurface_falloff"))
    teeth_front_specular: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_front_specular"))
    teeth_rear_specular: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_rear_specular"))
    teeth_front_roughness: bpy.props.FloatProperty(default=0.4, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_front_roughness"))
    teeth_rear_roughness: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_rear_roughness"))
    teeth_normal_strength: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"teeth_normal_strength"))
    teeth_micro_normal_strength: bpy.props.FloatProperty(default=0.3, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_micro_normal_strength"))
    teeth_micro_normal_tiling: bpy.props.FloatProperty(default=10, min=0, max=20, update=lambda s,c: update_property(s,c,"teeth_micro_normal_tiling"))
    teeth_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"teeth_emissive_color"))
    teeth_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"teeth_emission_strength"))


class CC3TongueParameters(bpy.types.PropertyGroup):
    # Tongue
    tongue_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_hue"))
    tongue_brightness: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"tongue_brightness"))
    tongue_saturation: bpy.props.FloatProperty(default=0.95, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_saturation"))
    tongue_hsv_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_hsv_strength"))
    tongue_front_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1.5, update=lambda s,c: update_property(s,c,"tongue_front_ao"))
    tongue_rear_ao: bpy.props.FloatProperty(default=0.0, min=0, max=1.5, update=lambda s,c: update_property(s,c,"tongue_rear_ao"))
    tongue_ao_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_ao_strength"))
    tongue_ao_power: bpy.props.FloatProperty(default=1, min=0, max=8, update=lambda s,c: update_property(s,c,"tongue_ao_power"))
    tongue_subsurface_scatter: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"tongue_subsurface_scatter"))
    tongue_subsurface_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=lambda s,c: update_property(s,c,"tongue_subsurface_radius"))
    tongue_subsurface_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                            default=(1.0, 0.112, 0.072, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"tongue_subsurface_falloff"))
    tongue_front_specular: bpy.props.FloatProperty(default=0.259, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_front_specular"))
    tongue_rear_specular: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_rear_specular"))
    tongue_front_roughness: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_front_roughness"))
    tongue_rear_roughness: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_rear_roughness"))
    tongue_normal_strength: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"tongue_normal_strength"))
    tongue_micro_normal_strength: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_micro_normal_strength"))
    tongue_micro_normal_tiling: bpy.props.FloatProperty(default=4, min=0, max=20, update=lambda s,c: update_property(s,c,"tongue_micro_normal_tiling"))
    tongue_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"tongue_emissive_color"))
    tongue_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_emission_strength"))


class CC3HairParameters(bpy.types.PropertyGroup):
    # shader
    hair_diffuse_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1, 1, 1, 1), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"hair_diffuse_color"))
    hair_diffuse_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_diffuse_hue"))
    hair_diffuse_brightness: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_diffuse_brightness"))
    hair_diffuse_saturation: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_diffuse_saturation"))
    hair_diffuse_hsv_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_diffuse_hsv_strength"))
    hair_global_strength: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_global_strength"))
    hair_root_color_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_root_color_strength"))
    hair_end_color_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_end_color_strength"))
    hair_invert_root_map: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_invert_root_map"))
    hair_base_color_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_base_color_strength"))
    hair_root_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.144129, 0.072272, 0.046665, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_root_color"))
    hair_end_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.332452, 0.184475, 0.122139, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_end_color"))
    hair_highlight_a_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.502886, 0.323143, 0.205079, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_highlight_a_color"))
    hair_highlight_a_start: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_a_start"))
    hair_highlight_a_mid: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_a_mid"))
    hair_highlight_a_end: bpy.props.FloatProperty(default=0.3, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_a_end"))
    hair_highlight_a_strength: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_a_strength"))
    hair_highlight_a_overlap_invert: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_a_overlap_invert"))
    hair_highlight_a_overlap_end: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_a_overlap_end"))
    hair_highlight_b_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1, 1, 1, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_highlight_b_color"))
    hair_highlight_b_start: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_b_start"))
    hair_highlight_b_mid: bpy.props.FloatProperty(default=0.2, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_b_mid"))
    hair_highlight_b_end: bpy.props.FloatProperty(default=0.3, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_b_end"))
    hair_highlight_b_strength: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_b_strength"))
    hair_highlight_b_overlap_invert: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_b_overlap_invert"))
    hair_highlight_b_overlap_end: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_highlight_b_overlap_end"))
    hair_vertex_color_strength: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_vertex_color_strength"))
    hair_vertex_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0, 0, 0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_vertex_color"))
    hair_anisotropic_roughness: bpy.props.FloatProperty(default=0.0375, min=0.001, max=1, update=lambda s,c: update_property(s,c,"hair_anisotropic_roughness"))
    hair_anisotropic_shift_min: bpy.props.FloatProperty(default=0, min=-1, max=1, update=lambda s,c: update_property(s,c,"hair_anisotropic_shift_min"))
    hair_anisotropic_shift_max: bpy.props.FloatProperty(default=0, min=-1, max=1, update=lambda s,c: update_property(s,c,"hair_anisotropic_shift_max"))
    hair_anisotropic: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_anisotropic"))
    hair_anisotropic_strength: bpy.props.FloatProperty(default=0.8, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_anisotropic_strength"))
    hair_specular_blend: bpy.props.FloatProperty(default=0.75, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_specular_blend"))
    hair_anisotropic_strength2: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_anisotropic_strength2"))
    hair_anisotropic_strength_cycles: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_anisotropic_strength_cycles"))
    hair_anisotropic_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.05, 0.038907, 0.0325, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_anisotropic_color"))
    hair_subsurface_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_subsurface_scale"))
    hair_subsurface_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_subsurface_falloff"))
    hair_subsurface_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=lambda s,c: update_property(s,c,"hair_subsurface_radius"))
    hair_diffuse_strength: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_diffuse_strength"))
    hair_ao_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_ao_strength"))
    hair_ao_power: bpy.props.FloatProperty(default=1, min=0, max=8, update=lambda s,c: update_property(s,c,"hair_ao_power"))
    hair_ao_occlude_all: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_ao_occlude_all"))
    hair_blend_multiply_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_blend_multiply_strength"))
    hair_specular_scale: bpy.props.FloatProperty(default=0.3, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_specular_scale"))
    hair_roughness_strength: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_roughness_strength"))
    hair_alpha_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_alpha_strength"))
    hair_opacity: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_opacity"))
    hair_normal_strength: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_normal_strength"))
    hair_bump_strength: bpy.props.FloatProperty(default=1, min=-3, max=3, update=lambda s,c: update_property(s,c,"hair_bump_strength"))
    hair_displacement_strength: bpy.props.FloatProperty(default=0, min=-3, max=3, update=lambda s,c: update_property(s,c,"hair_displacement_strength"))
    hair_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"hair_emissive_color"))
    hair_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_emission_strength"))
    # not done yet
    hair_enable_color: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_enable_color"))
    hair_tangent_vector: bpy.props.FloatVectorProperty(subtype="XYZ", size=3,
                        default=(0.0, 1.0, 0.0), min = -1.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_tangent_vector"))
    hair_tangent_flip_green: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_tangent_flip_green"))
    hair_specular_scale2: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_specular_scale2"))


class CC3PBRParameters(bpy.types.PropertyGroup):
    # Default
    default_diffuse_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1, 1, 1, 1), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"default_diffuse_color"))
    default_ao_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_ao_strength"))
    default_ao_power: bpy.props.FloatProperty(default=1, min=0, max=8, update=lambda s,c: update_property(s,c,"default_ao_power"))
    default_blend_multiply_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_blend_multiply_strength"))
    default_metallic: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_metallic"))
    default_specular: bpy.props.FloatProperty(default=0.5, min=0, max=2, update=lambda s,c: update_property(s,c,"default_specular"))
    default_roughness: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"default_roughness"))
    default_specular_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_specular_strength"))
    default_specular_scale: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_specular_scale"))
    default_specular_mask: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_specular_mask"))
    default_roughness_power: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_roughness_power"))
    default_roughness_min: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_roughness_min"))
    default_roughness_max: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_roughness_max"))
    default_alpha_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_alpha_strength"))
    default_opacity: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_opacity"))
    default_normal_strength: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_normal_strength"))
    default_bump_strength: bpy.props.FloatProperty(default=1, min=-3, max=3, update=lambda s,c: update_property(s,c,"default_bump_strength"))
    default_displacement_strength: bpy.props.FloatProperty(default=1, min=-5, max=5, update=lambda s,c: update_property(s,c,"default_displacement_strength"))
    default_displacement_base: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"default_displacement_base"))
    default_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"default_emissive_color"))
    default_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_emission_strength"))


class CC3SSSParameters(bpy.types.PropertyGroup):
    # Default
    default_diffuse_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1, 1, 1, 1), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"default_diffuse_color"))
    default_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"default_hue"))
    default_brightness: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"default_brightness"))
    default_saturation: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_saturation"))
    default_hsv_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_hsv_strength"))
    default_ao_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_ao_strength"))
    default_ao_power: bpy.props.FloatProperty(default=1, min=0, max=8, update=lambda s,c: update_property(s,c,"default_ao_power"))
    default_blend_multiply_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_blend_multiply_strength"))
    default_metallic: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_metallic"))
    default_specular: bpy.props.FloatProperty(default=0.5, min=0, max=2, update=lambda s,c: update_property(s,c,"default_specular"))
    default_roughness: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"default_roughness"))
    default_specular_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_specular_strength"))
    default_specular_scale: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_specular_scale"))
    default_specular_mask: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_specular_mask"))
    default_roughness_power: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_roughness_power"))
    default_roughness_min: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_roughness_min"))
    default_roughness_max: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_roughness_max"))
    default_alpha_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_alpha_strength"))
    default_opacity: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_opacity"))
    default_normal_strength: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_normal_strength"))
    default_bump_strength: bpy.props.FloatProperty(default=1, min=-3, max=3, update=lambda s,c: update_property(s,c,"default_bump_strength"))
    default_displacement_strength: bpy.props.FloatProperty(default=1, min=-5, max=5, update=lambda s,c: update_property(s,c,"default_displacement_strength"))
    default_displacement_base: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"default_displacement_base"))
    default_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"default_emissive_color"))
    default_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_emission_strength"))
    default_subsurface_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1.0, 1, 1, 1.0), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"default_subsurface_falloff"))
    default_subsurface_radius: bpy.props.FloatProperty(default=1.5, min=0, max=50, update=lambda s,c: update_property(s,c,"default_subsurface_radius"))
    default_micro_normal_strength: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"default_micronormal_strength"))
    default_subsurface_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"default_subsurface_scale"))
    default_unmasked_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"default_unmasked_scatter_scale"))
    default_r_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"default_r_scatter_scale"))
    default_g_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"default_g_scatter_scale"))
    default_b_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"default_b_scatter_scale"))
    default_a_scatter_scale: bpy.props.FloatProperty(default=1.0, min=0, max=2.0, update=lambda s,c: update_property(s,c,"default_a_scatter_scale"))
    default_micro_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"default_micro_roughness_mod"))
    default_unmasked_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"default_unmasked_roughness_mod"))
    default_r_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"default_r_roughness_mod"))
    default_g_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"default_g_roughness_mod"))
    default_b_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"default_b_roughness_mod"))
    default_a_roughness_mod: bpy.props.FloatProperty(default=0, min=-1.5, max=1.5, update=lambda s,c: update_property(s,c,"default_a_roughness_mod"))
    default_micro_normal_tiling: bpy.props.FloatProperty(default=5, min=0, max=50, update=lambda s,c: update_property(s,c,"default_micro_normal_tiling"))


class CC3BasicParameters(bpy.types.PropertyGroup):
    eye_occlusion: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_basic_property(s,c,"eye_occlusion"))
    eye_occlusion_power: bpy.props.FloatProperty(default=0.5, min=0.5, max=1.5, update=lambda s,c: update_basic_property(s,c,"eye_occlusion_power"))
    eye_brightness: bpy.props.FloatProperty(default=0.9, min=0, max=2, update=lambda s,c: update_basic_property(s,c,"eye_brightness"))
    eye_specular: bpy.props.FloatProperty(default=0.8, min=0, max=2, update=lambda s,c: update_basic_property(s,c,"eye_specular"))
    eye_roughness: bpy.props.FloatProperty(default=0.05, min=0, max=1, update=lambda s,c: update_basic_property(s,c,"eye_roughness"))
    eye_normal: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_basic_property(s,c,"eye_normal"))
    skin_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_basic_property(s,c,"skin_ao"))
    hair_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_basic_property(s,c,"hair_ao"))
    default_ao: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_basic_property(s,c,"default_ao"))
    default_specular: bpy.props.FloatProperty(default=0.5, min=0, max=2, update=lambda s,c: update_basic_property(s,c,"default_specular"))
    skin_specular: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=lambda s,c: update_basic_property(s,c,"skin_specular"))
    hair_specular: bpy.props.FloatProperty(default=0.5, min=0, max=2, update=lambda s,c: update_basic_property(s,c,"hair_specular"))
    scalp_specular: bpy.props.FloatProperty(default=0.0, min=0, max=2, update=lambda s,c: update_basic_property(s,c,"scalp_specular"))
    teeth_specular: bpy.props.FloatProperty(default=0.25, min=0, max=2, update=lambda s,c: update_basic_property(s,c,"teeth_specular"))
    tongue_specular: bpy.props.FloatProperty(default=0.259, min=0, max=2, update=lambda s,c: update_basic_property(s,c,"tongue_specular"))
    skin_roughness: bpy.props.FloatProperty(default=0.15, min=0, max=1, update=lambda s,c: update_basic_property(s,c,"skin_roughness"))
    teeth_roughness: bpy.props.FloatProperty(default=0.4, min=0, max=1, update=lambda s,c: update_basic_property(s,c,"teeth_roughness"))
    tongue_roughness: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_basic_property(s,c,"tongue_roughness"))
    hair_bump: bpy.props.FloatProperty(default=1, min=0, max=10, update=lambda s,c: update_basic_property(s,c,"hair_bump"))
    default_bump: bpy.props.FloatProperty(default=5, min=0, max=10, update=lambda s,c: update_basic_property(s,c,"default_bump"))
    tearline_alpha: bpy.props.FloatProperty(default=0.05, min=0, max=0.2, update=lambda s,c: update_basic_property(s,c,"tearline_alpha"))
    tearline_roughness: bpy.props.FloatProperty(default=0.15, min=0, max=0.5, update=lambda s,c: update_basic_property(s,c,"tearline_roughness"))


class CC3TextureMapping(bpy.types.PropertyGroup):
    texture_type: bpy.props.StringProperty(default="DIFFUSE")
    texture_path: bpy.props.StringProperty(default="")
    embedded: bpy.props.BoolProperty(default=False)
    image: bpy.props.PointerProperty(type=bpy.types.Image)
    strength: bpy.props.FloatProperty(default=1.0)
    location: bpy.props.FloatVectorProperty(subtype="TRANSLATION", size=3, default=(0.0, 0.0, 0.0))
    rotation: bpy.props.FloatVectorProperty(subtype="EULER", size=3, default=(0.0, 0.0, 0.0))
    scale: bpy.props.FloatVectorProperty(subtype="XYZ", size=3, default=(1.0, 1.0, 1.0))


class CC3MaterialCache:
    material_id: bpy.props.StringProperty(default="")
    material: bpy.props.PointerProperty(type=bpy.types.Material)
    source_name: bpy.props.StringProperty(default="")
    material_type: bpy.props.EnumProperty(items=vars.ENUM_MATERIAL_TYPES, default="DEFAULT", update=lambda s,c: update_material_property(s,c,"material_type"))
    texture_mappings: bpy.props.CollectionProperty(type=CC3TextureMapping)
    #parameters: bpy.props.PointerProperty(type=CC3MaterialParameters)
    mixer_settings: bpy.props.PointerProperty(type=channel_mixer.CC3MixerSettings)
    dir: bpy.props.StringProperty(default="")
    user_added: bpy.props.BoolProperty(default=False)
    temp_weight_map: bpy.props.PointerProperty(type=bpy.types.Image)
    alpha_is_diffuse: bpy.props.BoolProperty(default=False)
    alpha_mode: bpy.props.StringProperty(default="NONE") # NONE, BLEND, HASHED, OPAQUE
    culling_sides: bpy.props.IntProperty(default=0) # 0 - default, 1 - single sided, 2 - double sided
    cloth_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON
    disabled: bpy.props.BoolProperty(default=False)

    def set_texture_mapping(self, texture_type, texture_path, embedded, image, location, rotation, scale):
        mapping = self.get_texture_mapping(texture_type)
        if mapping is None:
            mapping = self.texture_mappings.add()
        mapping.texture_type = texture_type
        mapping.texture_path = texture_path
        mapping.embedded = embedded
        mapping.image = image
        mapping.location = location
        mapping.rotation = rotation
        mapping.scale = scale

    def get_tex_dir(self, chr_cache):
        if os.path.isabs(self.dir):
            return os.path.normpath(self.dir)
        else:
            return os.path.normpath(os.path.join(chr_cache.get_import_dir(), self.dir))

    def get_texture_mapping(self, texture_type):
        for mapping in self.texture_mappings:
            if mapping.texture_type == texture_type:
                return mapping
        return None

    def is_sss(self):
        return self.material_type == "SSS"

    def is_skin(self):
        return (self.material_type == "SKIN_HEAD"
                or self.material_type == "SKIN_BODY"
                or self.material_type == "SKIN_ARM"
                or self.material_type == "SKIN_LEG")

    def is_head(self):
        return self.material_type == "SKIN_HEAD"

    def is_body(self):
        return self.material_type == "SKIN_BODY"

    def is_arm(self):
        return self.material_type == "SKIN_ARM"

    def is_leg(self):
        return self.material_type == "SKIN_LEG"

    def is_teeth(self):
        return (self.material_type == "TEETH_UPPER"
                or self.material_type == "TEETH_LOWER")

    def is_upper_teeth(self):
        return self.material_type == "TEETH_UPPER"

    def is_tongue(self):
        return self.material_type == "TONGUE"

    def is_hair(self):
        return self.material_type == "HAIR"

    def is_scalp(self):
        return self.material_type == "SCALP"

    def is_eyelash(self):
        return self.material_type == "EYELASH"

    def is_nails(self):
        return self.material_type == "NAILS"

    def is_eye(self, side = "ANY"):
        if side == "RIGHT":
            return self.material_type == "EYE_RIGHT"
        elif side == "LEFT":
            return self.material_type == "EYE_LEFT"
        else:
            return (self.material_type == "EYE_RIGHT"
                    or self.material_type == "EYE_LEFT")

    def is_cornea(self, side = "ANY"):
        if side == "RIGHT":
            return self.material_type == "CORNEA_RIGHT"
        elif side == "LEFT":
            return self.material_type == "CORNEA_LEFT"
        else:
            return (self.material_type == "CORNEA_RIGHT"
                    or self.material_type == "CORNEA_LEFT")

    def is_eye_occlusion(self):
        return (self.material_type == "OCCLUSION_RIGHT"
                or self.material_type == "OCCLUSION_LEFT")

    def is_tearline(self):
        return (self.material_type == "TEARLINE_RIGHT"
                or self.material_type == "TEARLINE_LEFT")

    def get_base_name(self):
        return utils.strip_name(self.material.name)

    def get_material_type(self):
        return self.material_type

    def get_material_id(self):
        if not self.material_id:
            self.material_id = utils.generate_random_id(20)
        return self.material_id

    def check_id(self):
        material_id = self.get_material_id()
        material_type = self.material_type
        if self.material:
            self.material["rl_material_id"] = material_id
            self.material["rl_material_type"] = material_type


class CC3EyeMaterialCache(bpy.types.PropertyGroup, CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3EyeParameters)

class CC3EyeOcclusionMaterialCache(bpy.types.PropertyGroup, CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3EyeOcclusionParameters)

class CC3TearlineMaterialCache(bpy.types.PropertyGroup, CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3TearlineParameters)

class CC3TeethMaterialCache(bpy.types.PropertyGroup, CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3TeethParameters)

class CC3TongueMaterialCache(bpy.types.PropertyGroup, CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3TongueParameters)

class CC3HairMaterialCache(bpy.types.PropertyGroup, CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3HairParameters)

class CC3HeadMaterialCache(bpy.types.PropertyGroup, CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3HeadParameters)

class CC3SkinMaterialCache(bpy.types.PropertyGroup, CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3SkinParameters)

class CC3PBRMaterialCache(bpy.types.PropertyGroup, CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3PBRParameters)

class CC3SSSMaterialCache(bpy.types.PropertyGroup, CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3SSSParameters)


class CC3ObjectCache(bpy.types.PropertyGroup):
    object_id: bpy.props.StringProperty(default="")
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    source_name: bpy.props.StringProperty(default="")
    object_type: bpy.props.EnumProperty(items=vars.ENUM_OBJECT_TYPES, default="DEFAULT", update=lambda s,c: update_object_property(s,c,"object_type"))
    collision_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON, PROXY
    cloth_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON
    cloth_settings: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, HAIR, COTTON, DENIM, LEATHER, RUBBER, SILK
    cloth_self_collision: bpy.props.BoolProperty(default=False)
    user_added: bpy.props.BoolProperty(default=False)
    collision_proxy: bpy.props.PointerProperty(type=bpy.types.Object)
    use_collision_proxy: bpy.props.BoolProperty(default=False)
    collision_proxy_decimate: bpy.props.FloatProperty(default=0.125, min=0.0, max=1.0)
    disabled: bpy.props.BoolProperty(default=False)

    def is_body(self):
        return self.object_type == "BODY"

    def is_teeth(self):
        return self.object_type == "TEETH"

    def is_tongue(self):
        return self.object_type == "TONGUE"

    def is_hair(self):
        return self.object_type == "HAIR"

    def is_eye(self):
        return self.object_type == "EYE"

    def is_eye_occlusion(self):
        return self.object_type == "OCCLUSION"

    def is_tearline(self):
        return self.object_type == "TEARLINE"

    def is_mesh(self):
        return utils.object_exists_is_mesh(self.object)

    def is_armature(self):
        return utils.object_exists_is_armature(self.object)

    def is_valid(self):
        return utils.object_exists(self.object)

    def get_object(self, return_invalid = False):
        if utils.object_exists(self.object):
            return self.object
        if return_invalid:
            return self.object
        return None

    def get_base_name(self):
        return utils.strip_name(self.object.name)

    def get_mesh(self):
        if utils.object_exists_is_mesh(self.object):
            return self.object
        return None

    def set_object(self, obj):
        if obj and utils.object_exists(obj):
            self.object = obj
        elif obj is None:
            self.object = None

    def set_object_type(self, type):
        if type is not None:
            self.object_type = type
            self.object["rl_object_type"] = type
            if type == "BODY":
                self.use_collision_proxy = True

    def has_collision_physics(self):
        if self.collision_physics == "ON" or self.collision_physics == "PROXY":
            return True
        if self.collision_physics == "DEFAULT" and \
           (self.object_type == "BODY" or self.object_type == "OCCLUSION"):
            return True
        return False

    def get_collision_proxy(self):
        if utils.object_exists(self.collision_proxy):
            return self.collision_proxy
        else:
            return None

    def check_id(self):
        if self.object_id == "":
            self.object_id = utils.generate_random_id(20)
        if self.object:
            self.object["rl_object_id"] = self.object_id
            self.object["rl_object_type"] = self.object_type


class CCICActionStore(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    action: bpy.props.PointerProperty(type=bpy.types.Action)


class CC3CharacterCache(bpy.types.PropertyGroup):
    open_mouth: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=open_mouth_update)
    eye_close: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=eye_close_update)
    import_file: bpy.props.StringProperty(default="", subtype="FILE_PATH")
    #
    tongue_material_cache: bpy.props.CollectionProperty(type=CC3TongueMaterialCache)
    teeth_material_cache: bpy.props.CollectionProperty(type=CC3TeethMaterialCache)
    head_material_cache: bpy.props.CollectionProperty(type=CC3HeadMaterialCache)
    skin_material_cache: bpy.props.CollectionProperty(type=CC3SkinMaterialCache)
    tearline_material_cache: bpy.props.CollectionProperty(type=CC3TearlineMaterialCache)
    eye_occlusion_material_cache: bpy.props.CollectionProperty(type=CC3EyeOcclusionMaterialCache)
    eye_material_cache: bpy.props.CollectionProperty(type=CC3EyeMaterialCache)
    hair_material_cache: bpy.props.CollectionProperty(type=CC3HairMaterialCache)
    pbr_material_cache: bpy.props.CollectionProperty(type=CC3PBRMaterialCache)
    sss_material_cache: bpy.props.CollectionProperty(type=CC3SSSMaterialCache)
    #
    basic_parameters: bpy.props.PointerProperty(type=CC3BasicParameters)
    #
    object_cache: bpy.props.CollectionProperty(type=CC3ObjectCache)
    # import file name without extension
    import_flags: bpy.props.IntProperty(default=0)
    import_embedded: bpy.props.BoolProperty(default=False)
    # which character in the import
    link_id: bpy.props.StringProperty(default="")
    character_name: bpy.props.StringProperty(default="")
    generation: bpy.props.StringProperty(default="None")
    parent_object: bpy.props.PointerProperty(type=bpy.types.Object)
    # accessory parent bone selector
    accessory_parent_bone: bpy.props.StringProperty(default="CC_Base_Head")
    # counter (how many times have the materials been built)
    build_count: bpy.props.IntProperty(default=0)

    setup_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic","Build basic PBR materials."),
                        ("ADVANCED","Advanced","Build advanced materials with blend maps, subsurface, and micro normals, specular and roughness control and includes layered eye, teeth and tongue materials.")
                    ], default="ADVANCED")

    render_target: bpy.props.EnumProperty(items=[
                        ("EEVEE","Eevee","Build shaders for Eevee rendering."),
                        ("CYCLES","Cycles","Build shaders for Cycles rendering."),
                    ], default="EEVEE", name = "Target Renderer")

    collision_body: bpy.props.PointerProperty(type=bpy.types.Object)
    physics_disabled: bpy.props.BoolProperty(default=False)
    physics_applied: bpy.props.BoolProperty(default=False)

    rigified: bpy.props.BoolProperty(default=False)
    rigified_full_face_rig: bpy.props.BoolProperty(default=False)
    rig_face_rig: bpy.props.BoolProperty(default=True)
    rig_mode: bpy.props.EnumProperty(items=[
                        ("QUICK","Quick","Rig the character all in one go."),
                        ("ADVANCED","Advanced","Split the process so that user adjustments can be made to the meta rig before generating."),
                    ], default="QUICK", name = "Rigging Mode")
    rig_meta_rig: bpy.props.PointerProperty(type=bpy.types.Object)
    rig_export_rig: bpy.props.PointerProperty(type=bpy.types.Object)
    rig_original_rig: bpy.props.PointerProperty(type=bpy.types.Object)
    rig_retarget_rig: bpy.props.PointerProperty(type=bpy.types.Object)
    rig_datalink_rig: bpy.props.PointerProperty(type=bpy.types.Object)
    rig_retarget_source_rig: bpy.props.PointerProperty(type=bpy.types.Object)
    retarget_heel_correction_angle: bpy.props.FloatProperty(default = 0.0, min=-0.7854, max=0.7854, description="Heel pitch angle (radians)")
    retarget_arm_correction_angle: bpy.props.FloatProperty(default = 0.0, min=-0.2618, max=0.2618, description="Arm spread angle (radians)")
    retarget_leg_correction_angle: bpy.props.FloatProperty(default = 0.0, min=-0.2618, max=0.2618, description="Leg spread angle (radians)")
    retarget_z_correction_height: bpy.props.FloatProperty(default = 0.0, min=-0.2, max=0.2, description="Height Adjustment (m)")

    non_standard_type: bpy.props.EnumProperty(items=[
                    ("HUMANOID","Humanoid","Non standard character is a Humanoid"),
                    ("CREATURE","Creature","Non standard character is a Creature"),
                    ("PROP","Prop","Non standard character is a Prop"),
                ], default="HUMANOID", name = "Non-standard Character Type")

    detail_sculpt_sub_target: bpy.props.EnumProperty(items=[
                        ("HEAD","Head","Sculpt on the head only"),
                        ("BODY","Body","Sculpt on the body only"),
                        ("ALL","All","Sculpt the entire body"),
                    ], default="HEAD", name = "Sculpt Target")

    detail_multires_body: bpy.props.PointerProperty(type=bpy.types.Object)
    sculpt_multires_body: bpy.props.PointerProperty(type=bpy.types.Object)

    detail_normal_strength: bpy.props.FloatProperty(default=1.0, min = -10.0, max = 10.0,
                                                    description="Strength of the detail sculpt normal overlay.",
                                                    update=lambda s,c: update_sculpt_mix_node(s,c,"detail_normal_strength"))
    detail_ao_strength: bpy.props.FloatProperty(default=0.5, min = 0.0, max = 2.0,
                                                    description="Strength of the detail sculpt ambient occlusion overlay.",
                                                    update=lambda s,c: update_sculpt_mix_node(s,c,"detail_ao_strength"))
    detail_normal_definition: bpy.props.FloatProperty(default=10, min = 0, max = 40.0,
                                                      description="Mask definition of the detail sculpt normal overlay.\n"
                                                                  "Lower definition shrinks the mask around the sculpted areas and smooths the transition between normal layers.",
                                                      update=lambda s,c: update_sculpt_mix_node(s,c,"detail_normal_definition"))
    body_normal_strength: bpy.props.FloatProperty(default=1.0, min = -10.0, max = 10.0,
                                                  description="Strength of the body sculpt normal overlay.",
                                                  update=lambda s,c: update_sculpt_mix_node(s,c,"body_normal_strength"))
    body_ao_strength: bpy.props.FloatProperty(default=0.5, min = 0.0, max = 2.0,
                                              description="Strength of the body sculpt ambient occlusion overlay.",
                                              update=lambda s,c: update_sculpt_mix_node(s,c,"body_ao_strength"))
    body_normal_definition: bpy.props.FloatProperty(default=10, min = 0, max = 40.0,
                                                    description="Mask definition of the body sculpt normal overlay.\n"
                                                                "Lower definition shrinks the mask around the sculpted areas and smooths the transition between normal layers.",
                                                    update=lambda s,c: update_sculpt_mix_node(s,c,"body_normal_definition"))

    multires_bake_apply: bpy.props.BoolProperty(default=True, name="Apply Multi-res Base Shape",
                                                description="Copy the multi-res base shape back to original character when baking the body sculpt normals.\n"
                                                            "Only the vertices affected by the sculpt are copied back and this does not destroy the original character's shapekeys.")

    detail_mix_mode: bpy.props.EnumProperty(items=[
                        ("OVERLAY","Overlay","Sculpted normals and occlusion are overlayed on top of the base normals and occlusion."),
                        ("REPLACE","Replace","Sculpted normals and occlusion replaces the base normals and occlusion."),
                    ], default="OVERLAY", name = "Detail Mix Mode",
                    update=lambda s,c: update_sculpt_mix_node(s,c,"detail_mix_mode"))

    body_mix_mode: bpy.props.EnumProperty(items=[
                        ("OVERLAY","Overlay","Sculpted normals and occlusion are overlayed on top of the base normals and occlusion."),
                        ("REPLACE","Replace","Sculpted normals and occlusion replaces the base normals and occlusion."),
                    ], default="OVERLAY", name = "Body Mix Mode",
                    update=lambda s,c: update_sculpt_mix_node(s,c,"body_mix_mode"))

    available_spring_rigs: bpy.props.EnumProperty(items=springbones.enumerate_spring_rigs,
                    default=0,
                    name="Available Spring Rigs",
                    description="A list of all the spring rigs on the character")

    proportion_editing: bpy.props.BoolProperty(default=False)
    proportion_editing_in_front: bpy.props.BoolProperty(default=False)
    proportion_editing_actions: bpy.props.CollectionProperty(type=CCICActionStore)
    proportion_editing_scale: bpy.props.EnumProperty(items=[
                        ("FULL","Full","Full"),
                        ("FIX_SHEAR","Fix Shear","Fix Shear"),
                        ("ALIGNED","Aligned","Aligned"),
                        ("AVERAGE","Average","Average"),
                        ("NONE","None","None"),
                        ("NONE_LEGACY","None (Legacy)","None (Legacy)"),
                    ], default="FULL", name="Set bone inherit scale")

    def select(self):
        arm = self.get_armature()
        if arm:
            utils.try_select_object(arm, clear_selection=True)
        else:
            self.select_all()

    def select_all(self):
        objects = self.get_all_objects(include_armature=True, include_children=True)
        utils.try_select_objects(objects, clear_selection=True)

    def get_tex_dir(self):
        dir, file = os.path.split(self.import_file)
        name, ext = os.path.splitext(file)
        if ext.lower() == ".fbx":
            tex_dir = os.path.join(dir, name + ".fbm")
        else:
            tex_dir = os.path.join(dir, name)
        return os.path.normpath(tex_dir)

    def get_import_dir(self):
        dir, file = os.path.split(self.import_file)
        return dir

    def get_import_key_file(self):
        dir, file = os.path.split(self.import_file)
        name, ext = os.path.splitext(file)
        if ext.lower() == ".fbx":
            key_file = os.path.join(dir, name + ".fbxkey")
        else:
            key_file = os.path.join(dir, name + ".ObjKey")
        return key_file

    def get_import_has_key(self):
        key_file = self.get_import_key_file()
        return os.path.exists(key_file)

    def get_import_type(self):
        dir, file = os.path.split(self.import_file)
        name, ext = os.path.splitext(file)
        return ext[1:]

    def is_import_type(self, import_type: str):
        if import_type[0] == ".":
            import_type = import_type[1:]
        return self.get_import_type().lower() == import_type.lower()

    def get_character_id(self):
        dir, file = os.path.split(self.import_file)
        name, ext = os.path.splitext(file)
        return name

    def check_paths(self):
        local_dir = utils.local_path()
        if local_dir and self.import_file and not os.path.exists(self.import_file):
            utils.log_info(f"Import source file no longer exists: {self.import_file}")
            dir, name = os.path.split(self.import_file)
            local_file = os.path.join(local_dir, name)
            utils.log_info(f"Looking for moved source file: {local_file}")
            if os.path.exists(local_file):
                utils.log_info(f"Updating paths to source file: {local_file}")
                self.import_file = local_file

    def can_export(self):
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        result = True
        if prefs.export_require_key:
            if self.generation in vars.STANDARD_GENERATIONS and not self.get_import_has_key():
                result = False
        if self.rigified:
            result = False
        return result

    def is_morph(self):
        return self.is_import_type("OBJ") and self.get_import_has_key()

    def is_standard(self):
        return self.generation in vars.STANDARD_GENERATIONS

    def is_non_standard(self, include_props=True):
        if include_props:
            return self.generation not in vars.STANDARD_GENERATIONS
        else:
            return self.generation not in vars.STANDARD_GENERATIONS and self.generation not in vars.PROP_GENERATIONS

    def is_avatar(self):
        return not self.is_prop()

    def is_prop(self):
        if self.generation in vars.PROP_GENERATIONS:
            return True
        if self.non_standard_type == "PROP":
            return True
        return False

    def is_actor_core(self):
        if (self.generation == "ActorCore"
         or self.generation == "ActorScan"):
            return True
        return False

    def can_hair_spring_rig(self):
        """Returns True if the character can have a hair spring rig."""
        if (self.generation == "G3" or
            self.generation == "G3Plus" or
            self.generation == "NonStandardG3" or
            self.generation == "ActorBuild"):
            return True
        elif self.generation == "GameBase":
            return True
        return False

    def can_be_rigged(self):
        """Returns True if the character can be rigified."""
        if (self.generation == "G3" or
            self.generation == "G3Plus" or
            self.generation == "NonStandardG3" or
            self.generation == "ActorBuild"):
            return True
        elif self.is_actor_core():
            return True
        elif self.generation == "GameBase":
            return True
        return False

    def can_rig_full_face(self):
        if (self.generation == "G3" or
            self.generation == "G3Plus"):
            return True
        return False

    def is_rig_full_face(self):
        if self.rig_mode == "ADVANCED":
            return self.rig_face_rig
        else:
            if self.can_rig_full_face():
                return self.rig_face_rig
            else:
                return False

    def get_rig_mapping_data(self):
        return rigify_mapping_data.get_mapping_for_generation(self.generation)

    def get_rig_bone_mapping(self):
        rigify_data = rigify_mapping_data.get_mapping_for_generation(self.generation)
        if rigify_data:
            return rigify_data.bone_mapping
        return None

    def get_all_materials_cache(self):
        cache_all = []
        for mat_cache in self.tongue_material_cache:
            if mat_cache.material:
                cache_all.append(mat_cache)
        for mat_cache in self.teeth_material_cache:
            if mat_cache.material:
                cache_all.append(mat_cache)
        for mat_cache in self.head_material_cache:
            if mat_cache.material:
                cache_all.append(mat_cache)
        for mat_cache in self.skin_material_cache:
            if mat_cache.material:
                cache_all.append(mat_cache)
        for mat_cache in self.tearline_material_cache:
            if mat_cache.material:
                cache_all.append(mat_cache)
        for mat_cache in self.eye_occlusion_material_cache:
            if mat_cache.material:
                cache_all.append(mat_cache)
        for mat_cache in self.eye_material_cache:
            if mat_cache.material:
                cache_all.append(mat_cache)
        for mat_cache in self.hair_material_cache:
            if mat_cache.material:
                cache_all.append(mat_cache)
        for mat_cache in self.pbr_material_cache:
            if mat_cache.material:
                cache_all.append(mat_cache)
        for mat_cache in self.sss_material_cache:
            if mat_cache.material:
                cache_all.append(mat_cache)
        return cache_all

    def get_all_materials(self):
        materials = []
        for mat_cache in self.tongue_material_cache:
            if mat_cache.material:
                materials.append(mat_cache.material)
        for mat_cache in self.teeth_material_cache:
            if mat_cache.material:
                materials.append(mat_cache.material)
        for mat_cache in self.head_material_cache:
            if mat_cache.material:
                materials.append(mat_cache.material)
        for mat_cache in self.skin_material_cache:
            if mat_cache.material:
                materials.append(mat_cache.material)
        for mat_cache in self.tearline_material_cache:
            if mat_cache.material:
                materials.append(mat_cache.material)
        for mat_cache in self.eye_occlusion_material_cache:
            if mat_cache.material:
                materials.append(mat_cache.material)
        for mat_cache in self.eye_material_cache:
            if mat_cache.material:
                materials.append(mat_cache.material)
        for mat_cache in self.hair_material_cache:
            if mat_cache.material:
                materials.append(mat_cache.material)
        for mat_cache in self.pbr_material_cache:
            if mat_cache.material:
                materials.append(mat_cache.material)
        for mat_cache in self.sss_material_cache:
            if mat_cache.material:
                materials.append(mat_cache.material)
        return materials

    def get_all_objects(self, include_armature = True, include_children = False, of_type = "ALL"):

        objects = []
        arm = None

        for obj_cache in self.object_cache:
            obj = obj_cache.get_object()
            if obj and obj not in objects:
                if obj.type == "ARMATURE":
                    arm = obj
                    if include_armature:
                        if of_type == "ALL" or of_type == "ARMATURE":
                            objects.append(obj)
                elif of_type == "ALL" or of_type == obj.type:
                    objects.append(obj)

        if include_children and arm:
            for child in arm.children:
                if utils.object_exists(child) and child not in objects:
                    if of_type == "ALL" or child.type == of_type:
                        objects.append(child)
        return objects


    def remove_mat_cache(self, mat):
        """Removes the material cache containing this material from the relevant material cache.

           Note this will invalidate all current material cache references of the same type!
        """
        if mat:
            for mat_cache in self.tongue_material_cache:
                if mat_cache.material == mat:
                    utils.remove_from_collection(self.tongue_material_cache, mat_cache)
                    return
            for mat_cache in self.teeth_material_cache:
                if mat_cache.material == mat:
                    utils.remove_from_collection(self.teeth_material_cache, mat_cache)
                    return
            for mat_cache in self.head_material_cache:
                if mat_cache.material == mat:
                    utils.remove_from_collection(self.head_material_cache, mat_cache)
                    return
            for mat_cache in self.skin_material_cache:
                if mat_cache.material == mat:
                    utils.remove_from_collection(self.skin_material_cache, mat_cache)
                    return
            for mat_cache in self.tearline_material_cache:
                if mat_cache.material == mat:
                    utils.remove_from_collection(self.tearline_material_cache, mat_cache)
                    return
            for mat_cache in self.eye_occlusion_material_cache:
                if mat_cache.material == mat:
                    utils.remove_from_collection(self.eye_occlusion_material_cache, mat_cache)
                    return
            for mat_cache in self.eye_material_cache:
                if mat_cache.material == mat:
                    utils.remove_from_collection(self.eye_material_cache, mat_cache)
                    return
            for mat_cache in self.hair_material_cache:
                if mat_cache.material == mat:
                    utils.remove_from_collection(self.hair_material_cache, mat_cache)
                    return
            for mat_cache in self.pbr_material_cache:
                if mat_cache.material == mat:
                    utils.remove_from_collection(self.pbr_material_cache, mat_cache)
                    return
            for mat_cache in self.sss_material_cache:
                if mat_cache.material == mat:
                    utils.remove_from_collection(self.sss_material_cache, mat_cache)
                    return

    def get_object_cache(self, obj, strict=False, by_id=None):
        """Returns the object cache for this object.
        """
        if obj:
            # by object
            for obj_cache in self.object_cache:
                cache_object = obj_cache.get_object()
                if cache_object and cache_object == obj:
                    if strict:
                        if not obj_cache.disabled:
                            return obj_cache
                    else:
                        return obj_cache
            # by source name
            if by_id:
                for obj_cache in self.object_cache:
                    if obj_cache.object_id == by_id:
                        if strict:
                            if not obj_cache.disabled:
                                return obj_cache
                        else:
                            return obj_cache
        return None

    def remove_object_cache(self, obj):
        """Removes the object from the object cache.

           Note this will invalidate all current object cache references!
        """
        if obj:
            for obj_cache in self.object_cache:
                cache_object = obj_cache.get_object()
                if cache_object and cache_object == obj:
                    utils.remove_from_collection(self.object_cache, obj_cache)
                    return

    def has_cache_objects(self, objects):
        """Returns True if any of the objects are actively the object cache.
        """
        for obj_cache in self.object_cache:
            if not obj_cache.disabled:
                cache_object = obj_cache.get_object()
                if cache_object in objects:
                    return True
        return False

    def has_child_objects(self, objects):
        arm = self.get_armature()
        if arm:
            for obj in objects:
                if obj.parent == arm:
                    return True
        return False

    def has_object(self, obj):
        """Returns True if any of the objects are in the object cache.
        """
        for obj_cache in self.object_cache:
            cache_object = obj_cache.get_object()
            if cache_object == obj:
                return True
        return False

    def get_armature(self):
        try:
            for obj_cache in self.object_cache:
                cache_object = obj_cache.get_object()
                if utils.object_exists_is_armature(cache_object):
                    return cache_object
        except:
            pass
        return None

    def get_body(self):
        return self.get_object_of_type("BODY")

    def get_object_of_type(self, object_type):
        try:
            for obj_cache in self.object_cache:
                cache_object = obj_cache.get_object()
                if cache_object and obj_cache.object_type == object_type:
                    return cache_object
        except:
            pass
        return None

    def set_rigify_armature(self, new_arm):
        self.rigified = True
        try:
            for obj_cache in self.object_cache:
                cache_object = obj_cache.get_object()
                if cache_object.type == "ARMATURE":
                    self.rig_original_rig = cache_object
                    obj_cache.set_object(new_arm)
                    # update the object id
                    obj_cache.object_id = utils.generate_random_id(20)
                    new_arm["rl_object_id"] = obj_cache.object_id
        except:
            pass

    def add_object_cache(self, obj, copy_from=None, user=False):
        """Returns the object cache for this object.

        Fetches or creates an object cache for the object. Always returns an object cache collection.
        """

        obj_cache: CC3ObjectCache = self.get_object_cache(obj)
        if obj_cache is None:
            utils.log_info(f"Creating Object Cache for: {obj.name}")
            obj_cache = self.object_cache.add()
            obj_cache.object_id = utils.generate_random_id(20)
            if copy_from:
                utils.log_info(f"Copying object cache from: {copy_from}")
                utils.copy_property_group(copy_from, obj_cache)
                if user:
                    obj_cache.user_added = True
                    obj_cache.object_id = utils.generate_random_id(20)
            obj_cache.set_object(obj)
            obj_cache.source_name = utils.strip_name(obj.name)
            obj_cache.check_id()
        return obj_cache


    def has_material(self, mat):
        return (self.get_material_cache(mat) is not None)


    def has_any_materials(self, materials):
        for mat in materials:
            if mat and self.has_material(mat):
                return True
        return False

    def has_all_materials(self, materials):
        for mat in materials:
            if mat and not self.has_material(mat):
                return False
        return True


    def get_material_cache(self, mat, by_id=None):
        """Returns the material cache for this material.

        Fetches the material cache for the material. Returns None if the material is not in the cache.
        """

        mat_cache: CC3MaterialCache
        if mat is not None:
            for mat_cache in self.eye_material_cache:
                if mat_cache.material == mat:
                    return mat_cache
            for mat_cache in self.hair_material_cache:
                if mat_cache.material == mat:
                    return mat_cache
            for mat_cache in self.head_material_cache:
                if mat_cache.material == mat:
                    return mat_cache
            for mat_cache in self.skin_material_cache:
                if mat_cache.material == mat:
                    return mat_cache
            for mat_cache in self.tongue_material_cache:
                if mat_cache.material == mat:
                    return mat_cache
            for mat_cache in self.teeth_material_cache:
                if mat_cache.material == mat:
                    return mat_cache
            for mat_cache in self.tearline_material_cache:
                if mat_cache.material == mat:
                    return mat_cache
            for mat_cache in self.eye_occlusion_material_cache:
                if mat_cache.material == mat:
                    return mat_cache
            for mat_cache in self.pbr_material_cache:
                if mat_cache.material == mat:
                    return mat_cache
            for mat_cache in self.sss_material_cache:
                if mat_cache.material == mat:
                    return mat_cache

            if by_id:
                for mat_cache in self.eye_material_cache:
                    if mat_cache.material_id == by_id:
                        return mat_cache
                for mat_cache in self.hair_material_cache:
                    if mat_cache.material_id == by_id:
                        return mat_cache
                for mat_cache in self.head_material_cache:
                    if mat_cache.material_id == by_id:
                        return mat_cache
                for mat_cache in self.skin_material_cache:
                    if mat_cache.material_id == by_id:
                        return mat_cache
                for mat_cache in self.tongue_material_cache:
                    if mat_cache.material_id == by_id:
                        return mat_cache
                for mat_cache in self.teeth_material_cache:
                    if mat_cache.material_id == by_id:
                        return mat_cache
                for mat_cache in self.tearline_material_cache:
                    if mat_cache.material_id == by_id:
                        return mat_cache
                for mat_cache in self.eye_occlusion_material_cache:
                    if mat_cache.material_id == by_id:
                        return mat_cache
                for mat_cache in self.pbr_material_cache:
                    if mat_cache.material_id == by_id:
                        return mat_cache
                for mat_cache in self.sss_material_cache:
                    if mat_cache.material_id == by_id:
                        return mat_cache
        return None


    def add_or_reuse_material_cache(self, collection):
        for i in range(0, len(collection)):
            if collection[i].material is None:
                utils.log_info(f"Reusing material cache: {str(i)}")
                return collection[i]
        return collection.add()


    def get_material_cache_collection(self, material_type):
        if material_type == "DEFAULT" or material_type == "SCALP" or material_type == "EYELASH":
            return self.pbr_material_cache
        elif material_type == "SSS":
            return self.sss_material_cache
        elif material_type == "SKIN_HEAD":
            return self.head_material_cache
        elif (material_type == "SKIN_BODY" or material_type == "SKIN_ARM" or
              material_type == "SKIN_LEG" or material_type == "NAILS"):
            return self.skin_material_cache
        elif material_type == "TEETH_UPPER" or material_type == "TEETH_LOWER":
            return self.teeth_material_cache
        elif material_type == "TONGUE":
            return self.tongue_material_cache
        elif material_type == "HAIR":
            return self.hair_material_cache
        elif (material_type == "CORNEA_RIGHT" or material_type == "CORNEA_LEFT" or
              material_type == "EYE_RIGHT" or material_type == "EYE_LEFT"):
            return self.eye_material_cache
        elif material_type == "OCCLUSION_RIGHT" or material_type == "OCCLUSION_LEFT":
            return self.eye_occlusion_material_cache
        elif material_type == "TEARLINE_RIGHT" or material_type == "TEARLINE_LEFT":
            return self.tearline_material_cache
        else:
            return self.pbr_material_cache


    def add_material_cache(self, mat, create_type = "DEFAULT", user=False, copy_from=None):
        """Returns the material cache for this material.

        Fetches the material cache for the material. Returns None if the material is not in the cache.
        """

        if copy_from:
            create_type = copy_from.material_type

        mat_cache: CC3MaterialCache = self.get_material_cache(mat)
        if mat_cache is None and mat:
            utils.log_info(f"Creating Material Cache for: {mat.name} (type = {create_type})")
            collection = self.get_material_cache_collection(create_type)
            mat_cache = self.add_or_reuse_material_cache(collection)
            mat_cache.material_type = create_type
            mat_cache.material_id = utils.generate_random_id(20)
            if copy_from:
                utils.log_info(f"Copying material cache from: {copy_from}")
                utils.copy_property_group(copy_from, mat_cache)
                if user:
                    mat_cache.user_added = True
                    mat_cache.material_id = utils.generate_random_id(20)
            mat_cache.material = mat
            mat_cache.source_name = utils.strip_name(mat.name)
            mat_cache.check_id()
        return mat_cache

    def get_json_data(self):
        errors = []
        return jsonutils.read_json(self.import_file, errors)

    def write_json_data(self, json_data):
        jsonutils.write_json(json_data, self.import_file, is_fbx_path=True)

    def change_import_file(self, filepath):
        self.import_file = filepath

    def get_character_json(self):
        json_data = self.get_json_data()
        return jsonutils.get_character_json(json_data, self.get_character_id())

    def recast_type(self, collection, index, chr_json):
        mat_cache = collection[index]
        mat = mat_cache.material
        utils.log_info(f"Recasting material cache: {mat.name}")
        material_type = mat_cache.material_type
        mat["rl_material_type"] = material_type
        mat_cache.material = None
        mat_cache.source_name = ""
        new_mat_cache = self.add_material_cache(mat, material_type)
        if not chr_json:
            chr_json = self.get_character_json()
        for obj_cache in self.object_cache:
            obj = obj_cache.get_object()
            if obj_cache.is_mesh():
                for m in obj.data.materials:
                    if m and m == mat:
                        new_mat_cache.dir = imageutils.get_material_tex_dir(self, obj, mat)
                        obj_json = jsonutils.get_object_json(chr_json, obj)
                        mat_json = jsonutils.get_material_json(obj_json, mat)
                        init_material_property_defaults(obj, mat, obj_cache, new_mat_cache, obj_json, mat_json)
                        utils.log_info("Recast Complete.")
                        return

    def check_type(self, collection, recast, chr_json, *types):
        for i in range(0, len(collection)):
            if i < len(collection):
                if collection[i].material and collection[i].material_type not in types:
                    self.recast_type(collection, i, chr_json)
                    i -= 1

    def check_material_types(self, chr_json):
        recast = []
        self.check_type(self.tongue_material_cache, recast, chr_json, "TONGUE")
        self.check_type(self.teeth_material_cache, recast, chr_json, "TEETH_LOWER", "TEETH_UPPER")
        self.check_type(self.head_material_cache, recast, chr_json, "SKIN_HEAD")
        self.check_type(self.skin_material_cache, recast, chr_json, "SKIN_BODY", "SKIN_ARM", "SKIN_LEG", "NAILS")
        self.check_type(self.tearline_material_cache, recast, chr_json, "TEARLINE_LEFT", "TEARLINE_RIGHT")
        self.check_type(self.eye_occlusion_material_cache, recast, chr_json, "OCCLUSION_RIGHT", "OCCLUSION_LEFT")
        self.check_type(self.eye_material_cache, recast, chr_json, "CORNEA_RIGHT", "CORNEA_LEFT", "EYE_RIGHT", "EYE_LEFT")
        self.check_type(self.hair_material_cache, recast, chr_json, "HAIR")
        self.check_type(self.pbr_material_cache, recast, chr_json, "DEFAULT", "SCALP", "EYELASH")
        self.check_type(self.sss_material_cache, recast, chr_json, "SSS")

    def get_detail_body(self):
        if utils.object_exists_is_mesh(self.detail_multires_body):
            return self.detail_multires_body
        else:
            return None

    def get_sculpt_body(self):
        if utils.object_exists_is_mesh(self.sculpt_multires_body):
            return self.sculpt_multires_body
        else:
            return None

    def set_detail_body(self, mesh):
        self.detail_multires_body = mesh

    def set_sculpt_body(self, mesh):
        self.sculpt_multires_body = mesh

    def get_related_physics_objects(self, obj):
        proxy = None
        is_proxy = False
        if obj:
            obj_cache = self.get_object_cache(obj)
            if obj_cache:
                proxy = obj_cache.get_collision_proxy()
            else:
                proxy_obj = self.find_object_from_proxy(obj)
                if proxy_obj:
                    proxy = obj
                    obj = proxy_obj
                    is_proxy = True
        return obj, proxy, is_proxy

    def find_object_from_proxy(self, proxy):
        for obj_cache in self.object_cache:
            if obj_cache.collision_proxy == proxy:
                return obj_cache.object
        if self.collision_body == proxy:
            body = self.get_body()
            return body
        return None

    def get_link_id(self):
        if not self.link_id:
            self.link_id = utils.generate_random_id(14)
        return self.link_id


class CC3ImportProps(bpy.types.PropertyGroup):

    node_id: bpy.props.IntProperty(default=1000)

    build_mode: bpy.props.EnumProperty(items=[
                        ("IMPORTED","All Imported","Rebuild materials for all the imported objects."),
                        ("SELECTED","Only Selected","Rebuild materials only for the selected objects.")
                    ], default="IMPORTED")

    blend_mode: bpy.props.EnumProperty(items=[
                        ("BLEND","Alpha Blend","Setup any non opaque materials as basic Alpha Blend"),
                        ("HASHED","Alpha Hashed","Setup non opaque materials as alpha hashed (Resolves Z sorting issues, but may need more samples)")
                    ], default="HASHED")

    update_mode: bpy.props.EnumProperty(items=[
                        ("UPDATE_LINKED","Linked","Update the shader parameters for all materials of the same type in all the objects from the last import"),
                        ("UPDATE_SELECTED","Selected","Update the shader parameters only in the selected object and material")
                    ], default="UPDATE_LINKED")

    setup_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic","Build basic PBR materials."),
                        ("ADVANCED","Advanced","Build advanced materials with blend maps, subsurface, and micro normals, specular and roughness control and includes layered eye, teeth and tongue materials.")
                    ], default="ADVANCED")

    import_file: bpy.props.StringProperty(default="", subtype="FILE_PATH")

    import_cache: bpy.props.CollectionProperty(type=CC3CharacterCache)

    dummy_slider: bpy.props.FloatProperty(default=0.5, min=0, max=1)

    unity_file_path: bpy.props.StringProperty(default="", subtype="FILE_PATH")
    unity_project_path: bpy.props.StringProperty(default="", subtype="FILE_PATH")

    physics_paint_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=physics.physics_paint_strength_update)
    weight_map_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=physics.weight_strength_update)
    physics_tex_size: bpy.props.EnumProperty(items=[
                        ("64","64 x 64","64 x 64 texture size"),
                        ("128","128 x 128","128 x 128 texture size"),
                        ("256","256 x 256","256 x 256 texture size"),
                        ("512","512 x 512","512 x 512 texture size"),
                        ("1024","1024 x 1024","1024 x 1024 texture size"),
                        ("2048","2048 x 2048","2048 x 2048 texture size"),
                        ("4096","4096 x 4096","4096 x 4096 texture size"),
                    ], default="1024")

    paint_object: bpy.props.PointerProperty(type=bpy.types.Object)
    paint_material: bpy.props.PointerProperty(type=bpy.types.Material)
    paint_image: bpy.props.PointerProperty(type=bpy.types.Image)
    paint_store_render: bpy.props.StringProperty(default="")

    quick_set_mode: bpy.props.EnumProperty(items=[
                        ("OBJECT","Object","Set the alpha blend mode and backface culling to all materials on the selected object(s)"),
                        ("MATERIAL","Material","Set the alpha blend mode and backface culling only to the selected material on the active object"),
                    ], default="MATERIAL")

    lighting_mode: bpy.props.BoolProperty(default=False,
                                          description="Automatically sets lighting and render settings, depending on use.")
    physics_mode: bpy.props.BoolProperty(default=False,
                                         description="Automatically generates physics vertex groups and settings.")
    wrinkle_mode: bpy.props.BoolProperty(default=True,
                                         description="Automatically generates wrinkle maps for this character (if available).")
    rigify_mode: bpy.props.BoolProperty(default=False,
                                        description="Automatically rigify the character and retarget any animations or poses that came with the character.")

    export_options: bpy.props.BoolProperty(default=False)
    cycles_options: bpy.props.BoolProperty(default=False)
    stage1: bpy.props.BoolProperty(default=True)
    stage1_details: bpy.props.BoolProperty(default=False)
    stage4: bpy.props.BoolProperty(default=True)
    stage_remapper: bpy.props.BoolProperty(default=False)
    show_build_prefs: bpy.props.BoolProperty(default=False)
    show_build_prefs2: bpy.props.BoolProperty(default=False)
    section_rigify_setup: bpy.props.BoolProperty(default=True)
    section_rigify_retarget: bpy.props.BoolProperty(default=True)
    section_rigify_nla_bake: bpy.props.BoolProperty(default=True)
    section_rigify_controls: bpy.props.BoolProperty(default=False)
    section_rigify_spring: bpy.props.BoolProperty(default=False)
    section_rigidbody_spring_ui: bpy.props.BoolProperty(default=True)
    section_physics_cloth_settings: bpy.props.BoolProperty(default=False)
    section_physics_collision_settings: bpy.props.BoolProperty(default=False)
    show_data_link_prefs: bpy.props.BoolProperty(default=False)

    retarget_preview_shape_keys: bpy.props.BoolProperty(default=True, name="Retarget Shape Keys",
                                                        description="Retarget any facial expression and viseme shape key actions on the source character rig to the current character meshes on the rigify rig")
    bake_nla_shape_keys: bpy.props.BoolProperty(default=True, name="Bake Shape Keys",
                                                description="Bake facial expression and viseme shape keys to new shapekey actions on the character")
    bake_unity_t_pose: bpy.props.BoolProperty(default=True, name="Include T-Pose", description="Include a T-Pose as the first animation track. This is useful for correct avatar alignment in Unity and for importing animations back into CC4")
    export_rigify_mode: bpy.props.EnumProperty(items=[
                        ("MESH","Mesh","Export only the character mesh and materials, with no animation (other than a Unity T-pose)"),
                        ("MOTION","Motion","Export the animation only, with minimal mesh and no materials. Shapekey animations will also export their requisite mesh objects"),
                        ("BOTH","Both","Export both the character mesh with materials and the animation"),
                    ], default="MOTION")
    section_rigify_export: bpy.props.BoolProperty(default=True)

    skin_toggle: bpy.props.BoolProperty(default=True)
    eye_toggle: bpy.props.BoolProperty(default=True)
    teeth_toggle: bpy.props.BoolProperty(default=True)
    tongue_toggle: bpy.props.BoolProperty(default=True)
    nails_toggle: bpy.props.BoolProperty(default=True)
    hair_toggle: bpy.props.BoolProperty(default=True)
    default_toggle: bpy.props.BoolProperty(default=True)

    section_hair_blender_curve: bpy.props.BoolProperty(default=True)
    section_hair_rigging: bpy.props.BoolProperty(default=True)

    section_sculpt_setup: bpy.props.BoolProperty(default=True)
    section_sculpt_cleanup: bpy.props.BoolProperty(default=True)
    section_sculpt_utilities: bpy.props.BoolProperty(default=True)
    sculpt_layer_tab: bpy.props.EnumProperty(items=[
                        ("BODY","Body","Full body sculpt layer.", "OUTLINER_OB_ARMATURE", 0),
                        ("DETAIL","Detail","Detail sculpt layer.", "MESH_MONKEY", 1),
                    ], default="BODY", name = "Sculpt Layer")

    geom_transfer_layer: bpy.props.EnumProperty(items=[
                        ("BASE","Base","Transfer geometry to the base mesh."),
                        ("SHAPE_KEY","Shape Key","Transfer geometry to a new shape key. This will *not* alter the bones."),
                    ], default="BASE", name = "Transfer Layer")

    geom_transfer_layer_name: bpy.props.StringProperty(name="Name", default="New Shape",
                                                       description="Name to assign to transferred shape key")



    # Hair

    hair_export_group_by: bpy.props.EnumProperty(items=[
                        ("CURVE","Curve","Group by curve objects"),
                        ("NAME","Name","Gropu by name"),
                        ("NONE","Single","Don't export separate groups"),
                    ], default="CURVE", name = "Export Hair Grouping",
                       description="Export hair groups by...")

    hair_card_dir_threshold: bpy.props.FloatProperty(default=0.9, min=0.0, max=1.0, name="Direction Threshold")
    hair_card_vertical_dir: bpy.props.EnumProperty(items=[
                        ("DOWN","Down","Hair cards from top to bottom in UV map", "SORT_ASC", 0),
                        ("UP","Up","Hair cards from bottom to top in UV map", "SORT_DESC", 1),
                    ], default="DOWN", name = "UV Direction",
                       description="Direction of vertical hair cards in UV Map")
    hair_card_horizontal_dir: bpy.props.EnumProperty(items=[
                        ("RIGHT","Right","Hair cards from left to right in UV map", "FORWARD", 2),
                        ("LEFT","Left","Hair cards from right to left in UV map", "BACK", 3),
                    ], default="RIGHT", name = "UV Direction",
                       description="Direction of horizontal hair cards in UV Map")
    hair_card_square_dir: bpy.props.EnumProperty(items=[
                        ("DOWN","Down","Hair cards from top to bottom in UV map", "SORT_ASC", 0),
                        ("UP","Up","Hair cards from bottom to top in UV map", "SORT_DESC", 1),
                        ("RIGHT","Right","Hair cards from left to right in UV map", "FORWARD", 2),
                        ("LEFT","Left","Hair cards from right to left in UV map", "BACK", 3),
                    ], default="DOWN", name = "UV Direction",
                       description="Direction of square(ish) hair cards in UV Map")
    hair_curve_merge_loops: bpy.props.EnumProperty(items=[
                        ("ALL","Use All Edge Loops","All edge loops in the cards will be converted into curves"),
                        ("MERGE","Merge Edge Loops","Edge loops in each card will be merged into a single curve"),
                    ], default="MERGE", name = "Merge Loops",
                       description="Merge edge loops")

    hair_rig_bone_smoothing: bpy.props.IntProperty(default=5, min=0, max=10,
            description="How much to smooth the curve of the generated bones from hair cards or greased pencil")
    hair_rig_bind_skip_length: bpy.props.FloatProperty(default=3.75, min=0.0, max=20.0,
            description="How far along the hair card to start generating bones, "
            "as rooting the bones to the very start of the hair cards can produce unwanted results")
    hair_rig_bind_trunc_length: bpy.props.FloatProperty(default=2.5, min=0.0, max=10.0,
            description="How far from the end of the hair card to stop generating bones")
    hair_rig_bone_length: bpy.props.FloatProperty(default=7.5, min=2.5, max=25,
            description="How long a section of each hair card the bones should represent")
    hair_rig_bind_bone_radius: bpy.props.FloatProperty(default=7.5, min=1, max=25,
            description="How wide a radius around the bones should the hair cards bind vertex weights to")
    hair_rig_bind_bone_count: bpy.props.IntProperty(default=2, min=1, max=4,
            description="How many neighouring bones should each hair card bind to.\n\n"
            "Note: More bones may produce smoother results but add to the overall mesh skinning performance cost")
    hair_rig_bind_bone_weight: bpy.props.FloatProperty(default=1.0, min=0.0, max=1.0,
            description="How much to scale the generated weights by")
    hair_rig_bind_bone_variance: bpy.props.FloatProperty(default=0.85, min=0.0, max=1.0,
            description="How much random variation in the generated weights.\n\n"
            "Less variance will cause all the hair cards to the follow the bones more closely.\n\n"
            "More variance will cause a wider spread of the cards as the bones move which gives the appearance of more volume")
    hair_rig_bind_existing_scale: bpy.props.FloatProperty(default=0.1, min=0.01, max=1.0,
            description="How much to scale any existing body weights on the hair.\n\n"
            "Note: The spring bones vertex weights will compete with the body vertex weights. Scaling the body weights back (< 1.0) "
            "will allow the hair to follow the spring bones more closely but will then conform less to the body")
    hair_rig_bind_weight_curve: bpy.props.FloatProperty(default=0.5, min=0.25, max=4.0,
            description="How to fade in the bone weights of each hair card from root to ends.\n\n"
            "Larger values ( > 1.0) will push the weights down closer to the ends.\n\n"
            "Smaller values ( < 1.0) will push the weights up closer to the roots")
    hair_rig_bind_smoothing: bpy.props.IntProperty(default=5, min=0, max=10,
            description="How much to smooth the generated weights after binding")
    hair_rig_bind_seed: bpy.props.IntProperty(default=1, min=1, max=10000,
            description="The random seed for generating the weight variance. The same seed should produce the same results each time")
    hair_rig_bind_card_mode: bpy.props.EnumProperty(items=[
                        ("ALL","All Cards","Bind all hair cards in the selected objects"),
                        ("SELECTED","Selected Cards","Bind only the selected hair cards in each selected object"),
                    ], default="ALL", name = "Hair Card Selection Mode")
    hair_rig_bind_bone_mode: bpy.props.EnumProperty(items=[
                        ("ALL","All Bones","Operate on all bones in the hair rig"),
                        ("SELECTED","Selected Bones","Operate on only the currently selected bones of the hair rig"),
                    ], default="ALL", name = "Bone Selection Mode")
    hair_rig_bone_root: bpy.props.EnumProperty(items=[
                        ("HEAD","Head Hair","Parent generated bones to the head bone"),
                        ("JAW","Beard Hair","Parent the generated bones to the jaw bone, for beards"),
                    ], default="HEAD", name = "Root bone for generated hair bones")
    hair_rig_target: bpy.props.EnumProperty(items=[
                        ("BLENDER","Blender","Generate a spring rig for Blender"),
                        ("CC4","CC4","Generate a compatible spring rig for Character Creator and iClone.\n"
                        "For Character Creator spring rigs, all other vertex weights are removed, and the first bone of each chain is fixed in place."),
                        ("UNITY","Unity","Generate a spring rig for Unity"),
                    ], default="BLENDER", name = "Rig Target Application", update=update_rig_target)

    hair_rig_group_name: bpy.props.StringProperty(name="Group Name", default="RL_Hair",
                                                  description="Name to assign to selected bone chains as a separate group")

    hair_rigid_body_influence: bpy.props.FloatProperty(default=1.0, min=0.0, max=1.0, name = "Influence",
                                                       description = "How much of the simulation is copied into the pose bones")
    hair_rigid_body_limit: bpy.props.FloatProperty(default=25, min=0, max=50, name = "Rigid Body Dampening Range",
                                                       description = "How big a dampening range to apply to the rigid body. More range gives more movement")
    hair_rigid_body_curve: bpy.props.FloatProperty(default=0.5, min=1/8, max=2, name = "Length Dampening Curve",
                                                       description = "The dampening curve factor along the length of the spring bone chains. Less curve gives more movement near the roots")
    hair_rigid_body_mass: bpy.props.FloatProperty(default=1.0, min=0.0, max=5.0, name = "Hair Node Mass",
                                                       description = "Mass of the rigid body particles representing the bones. More mass, more inertia")
    hair_rigid_body_dampening: bpy.props.FloatProperty(default=10.0, min=0.0, max=10000.0, name = "Spring Dampening",
                                                       description = "Spring dampening. (Makes very little difference)")
    hair_rigid_body_stiffness: bpy.props.FloatProperty(default=50.0, min=0.0, max=100.0, name = "Spring Stiffness",
                                                       description = "Spring stiffness. (Makes very little difference)")
    hair_rigid_body_radius: bpy.props.FloatProperty(default=0.05, min=0.0125, max=0.1, name = "Hair Node Collision Radius",
                                                       description = "Collision radius of the rigid body partivles representing the bones. Note: Too much and the rigid body system will start colliding with itself")

    # UI List props
    armature_action_filter: bpy.props.BoolProperty(default=True)
    action_list_index: bpy.props.IntProperty(default=-1)
    action_list_action: bpy.props.PointerProperty(type=bpy.types.Action)
    armature_list_index: bpy.props.IntProperty(default=-1)
    armature_list_object: bpy.props.PointerProperty(type=bpy.types.Object)
    unity_action_list_index: bpy.props.IntProperty(default=-1)
    unity_action_list_action: bpy.props.PointerProperty(type=bpy.types.Action)
    rigified_action_list_index: bpy.props.IntProperty(default=-1)
    rigified_action_list_action: bpy.props.PointerProperty(type=bpy.types.Action)

    def add_character_cache(self, copy_from=None):
        chr_cache = self.import_cache.add()
        if copy_from:
            exclude_list = ["*_material_cache", "object_cache"]
            utils.copy_property_group(copy_from, chr_cache, exclude=exclude_list)
        return chr_cache

    def get_any_character_cache_from_objects(self, objects, search_materials = False):
        chr_cache : CC3CharacterCache

        if objects:
            for chr_cache in self.import_cache:
                if chr_cache.has_cache_objects(objects):
                    return chr_cache
                if chr_cache.rig_meta_rig and chr_cache.rig_meta_rig in objects:
                    return chr_cache

        if search_materials:
            materials = []
            for obj in objects:
                if obj.type == "MESH":
                    for mat in obj.data.materials:
                        materials.append(mat)
            if materials:
                for chr_cache in self.import_cache:
                    if chr_cache.has_any_materials(materials):
                        return chr_cache
        return None

    def get_character_cache(self, obj, mat):
        if obj:
            for chr_cache in self.import_cache:
                obj_cache = chr_cache.get_object_cache(obj)
                if obj_cache and not obj_cache.disabled:
                    return chr_cache
        if mat:
            for chr_cache in self.import_cache:
                mat_cache = chr_cache.get_material_cache(mat)
                if mat_cache and not mat_cache.disabled:
                    return chr_cache
        return None

    def get_avatars(self):
        avatars = []
        chr_cache: CC3CharacterCache
        for chr_cache in self.import_cache:
            if chr_cache.is_avatar():
                avatars.append(chr_cache)
        return avatars

    def get_first_avatar(self):
        chr_cache: CC3CharacterCache
        for chr_cache in self.import_cache:
            if chr_cache.is_avatar():
                return chr_cache
        return None

    def find_character_by_name(self, name):
        if name:
            for chr_cache in self.import_cache:
                if chr_cache.character_name == name:
                    return chr_cache
        return None

    def find_character_by_link_id(self, link_id):
        if link_id:
            for chr_cache in self.import_cache:
                if chr_cache.link_id == link_id:
                    return chr_cache
        return None

    def get_context_character_cache(self, context = None):
        if not context:
            context = bpy.context

        chr_cache = None

        # if there is only one character in the scene, this is the only possible character cache:
        if len(self.import_cache) == 1:
            return self.import_cache[0]

        obj = context.object

        # otherwise determine the context character cache:
        chr_cache = self.get_character_cache(obj, None)

        # try to find a character from the selected objects
        if chr_cache is None and len(context.selected_objects) > 1:
            chr_cache = self.get_any_character_cache_from_objects(context.selected_objects, False)

        return chr_cache

    def get_object_cache(self, obj, strict = False):
        if obj:
            for imp_cache in self.import_cache:
                obj_cache = imp_cache.get_object_cache(obj, strict=strict)
                if obj_cache:
                    return obj_cache
        return None

    def get_material_cache(self, mat):
        if mat:
            for imp_cache in self.import_cache:
                mat_cache = imp_cache.get_material_cache(mat)
                if mat_cache:
                    return mat_cache
        return None

    def is_unity_project(self):
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        local_path = utils.local_path()
        if local_path:
            if prefs.export_unity_mode == "BLEND" and self.unity_file_path and self.unity_project_path:
                if utils.is_in_path(self.unity_project_path, local_path):
                    return True
        return False

    def restore_ui_list_indices(self):
        """Restore the indices from the stored objects, because adding new objects will cause the indices to become invalid."""
        self.armature_list_index = utils.index_of_collection(self.armature_list_object, bpy.data.objects)
        self.action_list_index = utils.index_of_collection(self.action_list_action, bpy.data.actions)
        self.unity_action_list_index = utils.index_of_collection(self.unity_action_list_action, bpy.data.actions)
        self.rigified_action_list_index = utils.index_of_collection(self.rigified_action_list_action, bpy.data.actions)

    def store_ui_list_indices(self):
        """Store the indices as objects, because adding new objects will cause the indices to become invalid."""
        self.armature_list_object = utils.collection_at_index(self.armature_list_index, bpy.data.objects)
        self.action_list_action = utils.collection_at_index(self.action_list_index, bpy.data.actions)
        self.unity_action_list_action = utils.collection_at_index(self.unity_action_list_index, bpy.data.actions)
        self.rigified_action_list_action = utils.collection_at_index(self.rigified_action_list_index, bpy.data.actions)
        if self.armature_list_object and self.armature_list_object.type != "ARMATURE":
            self.armature_list_object = None
            self.armature_list_index = -1

    def hair_dir_vectors(self):
        dirs = { "VERTICAL": self.hair_card_vertical_dir,
                 "HORIZONTAL": self.hair_card_horizontal_dir,
                 "SQUARE": self.hair_card_square_dir }
        dir_vectors = {}
        for aspect in dirs:
            dir = dirs[aspect]
            vector = Vector((0,0))
            if dir == "UP":
                vector = Vector((0,1)).normalized()
            elif dir == "LEFT":
                vector = Vector((-1,0)).normalized()
            elif dir == "RIGHT":
                vector = Vector((1,0)).normalized()
            else: #if dir == "DOWN":
                vector = Vector((0,-1)).normalized()
            dir_vectors[aspect] = vector
        return dir_vectors


class CCICBakeCache(bpy.types.PropertyGroup):
    uid: bpy.props.IntProperty(default=0)
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    source_material: bpy.props.PointerProperty(type=bpy.types.Material)
    baked_material: bpy.props.PointerProperty(type=bpy.types.Material)


class CCICBakeMaterialSettings(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(type=bpy.types.Material)
    max_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="4096")
    diffuse_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    ao_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    sss_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    transmission_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    thickness_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    metallic_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    specular_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    roughness_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    emissive_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    alpha_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    normal_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="4096")
    micronormal_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    micronormalmask_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    bump_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    mask_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    detail_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")


class CCICBakeProps(bpy.types.PropertyGroup):
    auto_increment: bpy.props.IntProperty(default=100)
    jpeg_quality: bpy.props.IntProperty(default=90, min=0, max=100)
    png_compression: bpy.props.IntProperty(default=15, min=0, max=100)

    target_mode: bpy.props.EnumProperty(items=vars.BAKE_TARGETS, default="BLENDER")

    target_format: bpy.props.EnumProperty(items=vars.TARGET_FORMATS, default="JPEG")

    bake_samples: bpy.props.IntProperty(default=5, min=1, max=64, description="The number of texture samples per pixel to bake. As there are no ray traced effects involved, 1 to 5 samples is usually enough.")
    ao_in_diffuse: bpy.props.FloatProperty(default=0, min=0, max=1, description="How much of the ambient occlusion to bake into the diffuse")

    smoothness_mapping: bpy.props.EnumProperty(items=vars.CONVERSION_FUNCTIONS, default="IR", description="Roughness to smoothness calculation")

    allow_bump_maps: bpy.props.BoolProperty(default=True, description="Allow separate Bump and Normal Maps")
    scale_maps: bpy.props.BoolProperty(default=False)
    pack_gltf: bpy.props.BoolProperty(default=True, description="Pack AO, Roughness and Metallic into a single Texture for GLTF")

    custom_sizes: bpy.props.BoolProperty(default=False)
    bake_mixers: bpy.props.BoolProperty(default=True, description="Bake the result of any Color ID/RGB mask mixers on the materials")
    max_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="4096")
    diffuse_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    ao_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    sss_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    transmission_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    thickness_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    metallic_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    specular_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    roughness_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    emissive_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    alpha_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    normal_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="4096")
    micronormal_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    micronormalmask_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    bump_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    mask_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    detail_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")

    bake_path: bpy.props.StringProperty(default="Bake", subtype="DIR_PATH")
    material_settings: bpy.props.CollectionProperty(type=CCICBakeMaterialSettings)
    bake_cache: bpy.props.CollectionProperty(type=CCICBakeCache)


class CCICLinkProps(bpy.types.PropertyGroup):
    # Data link props
    link_host: bpy.props.StringProperty(default="localhost", update=update_link_host)
    link_host_ip: bpy.props.StringProperty(default="127.0.0.1")
    link_target: bpy.props.EnumProperty(items=[
                        ("BLENDER","Blender","Connect to another Blender instance running on another machine"),
                        ("CCIC","CC4/iClone","Connect to Character Creator 4 or iClone"),
                        ("UNITY","Unity","Connect to Unity"),
                    ], default="CCIC", name = "Data Link Target", update=update_link_target)
    link_port: bpy.props.IntProperty(default=9333)
    link_status: bpy.props.StringProperty(default="")
    link_auto_start: bpy.props.BoolProperty(default=False)
    sequence_frame_sync: bpy.props.BoolProperty(default=False)
    sequence_preview_shape_keys: bpy.props.BoolProperty(default=True)
    match_client_rate: bpy.props.BoolProperty(default=True)
    remote_app: bpy.props.StringProperty(default="")
    remote_version: bpy.props.StringProperty(default="")
    remote_path: bpy.props.StringProperty(default="")
    remote_exe: bpy.props.StringProperty(default="")
    connected: bpy.props.BoolProperty(default=False)
