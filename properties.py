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

from . import (channel_mixer, imageutils, meshutils, sculpting, materials,
               springbones, rigify_mapping_data, modifiers, nodeutils, shaders,
               params, physics, basic, jsonutils, utils, vars)
from .meshutils import get_head_body_object_quick


def open_mouth_update(self, context):
    props: CC3ImportProps = vars.props()
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
    props: CC3ImportProps = vars.props()
    chr_cache = props.get_context_character_cache(context)
    value = chr_cache.eye_close

    if chr_cache:
        objects = chr_cache.get_cache_objects()
        BLINK_SHAPES = ["Eye_Blink", "Eye_Blink_L", "Eye_Blink_R"]

        for obj in objects:
            obj_cache = chr_cache.get_object_cache(obj)
            if obj_cache and not obj_cache.disabled and obj_cache.is_mesh():
                if (obj_cache.object_type == "BODY" or
                    obj_cache.object_type == "EYE_OCCLUSION" or
                    obj_cache.object_type == "TEARLINE"):
                    if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
                        for key in BLINK_SHAPES:
                            if key in obj.data.shape_keys.key_blocks:
                                try:
                                    obj.data.shape_keys.key_blocks[key].value = value
                                except:
                                    pass


def adjust_lighting_brightness(self, context):
    props = vars.props()
    for light in bpy.data.objects:
        if light.type == "LIGHT":
            if not props.lighting_brightness_all and not utils.has_ccic_id(light):
                continue
            current_brightness = light.data.energy
            if "rl_default_brightness" not in light.data:
                light.data["rl_default_brightness"] = current_brightness
            if "rl_last_brightness" not in light.data:
                light.data["rl_last_brightness"] = current_brightness
            last_brightness = light.data["rl_last_brightness"]
            # if the brightness has been changed by the user, update the custom props
            if abs(current_brightness-last_brightness) >= 0.001:
                light.data["rl_default_brightness"] = current_brightness
                light.data["rl_last_brightness"] = current_brightness
            base_energy = light.data["rl_default_brightness"]
            new_brightness = base_energy * props.lighting_brightness
            light.data.energy = new_brightness
            light.data["rl_last_brightness"] = new_brightness


def adjust_world_brightness(self, context):
    props = vars.props()
    nodes = context.scene.world.node_tree.nodes
    for node in nodes:
        if node.type == "BACKGROUND" and "(rl_background_node)" in node.name:
            current_strength = node.inputs["Strength"].default_value
            if "rl_default_strength" not in node:
                node["rl_default_strength"] = current_strength
            if "rl_last_strength" not in node:
                node["rl_last_strength"] = current_strength
            last_strength = node["rl_last_strength"]
            # if the node strength has been changed by the user, update the custom props
            if abs(current_strength - last_strength) >= 0.001:
                node["rl_default_strength"] = current_strength
                node["rl_last_strength"] = current_strength
            base_strength = node["rl_default_strength"]
            new_strength = base_strength * props.world_brightness
            node.inputs["Strength"].default_value = new_strength
            node["rl_last_strength"] = new_strength


def update_property(self, context, prop_name, update_mode = None):
    props = vars.props()

    if vars.block_property_update: return

    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)

    if chr_cache:

        context_obj = context.object
        context_mat = utils.get_context_material(context)
        context_mat_cache = chr_cache.get_material_cache(context_mat)
        linked_materials = get_linked_materials(chr_cache, context_mat, props.update_mode)

        for mat_cache in linked_materials:
            if mat_cache.material == context_mat:
                update_shader_property(context_obj, mat_cache, prop_name)
            else:
                set_linked_property(prop_name, context_mat_cache, mat_cache)
                update_shader_property(context_obj, mat_cache, prop_name)

        # these properties will cause the eye displacement vertex group to change...
        if prop_name in ["eye_iris_depth_radius", "eye_iris_scale", "eye_iris_radius"]:
            meshutils.rebuild_eye_vertex_groups(chr_cache)


def update_basic_property(self, context, prop_name, update_mode=None):
    if vars.block_property_update: return

    props = vars.props()
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)
    if chr_cache:
        all_materials_cache = chr_cache.get_all_materials_cache()
        for mat_cache in all_materials_cache:
            mat = mat_cache.material
            if mat:
                basic.update_basic_material(mat, mat_cache, prop_name)


def update_material_property(self, context, prop_name, update_mode=None):
    if vars.block_property_update: return
    props = vars.props()
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
    props = vars.props()
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


def update_shader_property(obj, mat_cache, prop_name):
    props = vars.props()

    if not mat_cache: return

    mat = mat_cache.material

    if mat and mat.node_tree:
        shader_name = params.get_shader_name(mat_cache)
        bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader_name)
        shader_def = params.get_shader_def(shader_name)

        if shader_def:

            if "inputs" in shader_def.keys():
                update_shader_input(shader_node, mat_cache, prop_name, shader_def["inputs"])

            if "bsdf" in shader_def.keys():
                bsdf_nodes = nodeutils.get_custom_bsdf_nodes(bsdf_node)
                for bsdf_node in bsdf_nodes:
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


def update_wrinkle_strength_all(self, context):
    if vars.block_property_update: return
    props = vars.props()
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)
    obj = get_head_body_object_quick(chr_cache)
    if obj:
        value = props.wrinkle_strength
        prop_name = "wrinkle_regions"
        for i in range(0,13):
            if prop_name in obj:
                obj[prop_name][i] = value
    return


def update_wrinkle_curve_all(self, context):
    if vars.block_property_update: return
    props = vars.props()
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)
    obj = get_head_body_object_quick(chr_cache)
    if obj:
        value = props.wrinkle_curve
        prop_name = "wrinkle_curves"
        for i in range(0,13):
            if prop_name in obj:
                obj[prop_name][i] = value
    return


def get_linked_materials(chr_cache, context_mat, update_mode):
    props = vars.props()
    linked_mats = set()
    if chr_cache:
        context_mat_cache = chr_cache.get_material_cache(context_mat)
        if context_mat and context_mat_cache:
            linked_mats.add(context_mat_cache)
            all_materials_cache = chr_cache.get_all_materials_cache()
            # linked materials are the same material type which need to be updated
            # at the same time with the same values (but only when updating as linked)
            linked_types = get_linked_material_types(context_mat_cache)
            # paired materials are linked materials that must *always* be updated at the same time
            # regardless of updating linked or not. e.g. Eye_L, Cornea_L
            paired_types = get_paired_material_types(context_mat_cache)
            # linked names are linked materials of common default types (pbr/sss) that are usually linked.
            linked_names = get_linked_material_names(context_mat_cache.get_base_name())
            all_materials_cache = chr_cache.get_all_materials_cache()
            for mat_cache in all_materials_cache:
                mat = mat_cache.material
                if mat:
                    if mat_cache.material_type in paired_types:
                        linked_mats.add(mat_cache)
                    elif update_mode == "UPDATE_LINKED":
                        if mat_cache.material_type in linked_types or mat_cache.get_base_name() in linked_names:
                            linked_mats.add(mat_cache)
    return [mc for mc in linked_mats]


def reset_parameters(context = bpy.context, all=False):
    props = vars.props()
    chr_cache = props.get_context_character_cache(context)
    chr_json = chr_cache.get_character_json()

    if chr_cache:

        vars.block_property_update = True
        if all:
            shaders.init_character_property_defaults(chr_cache, chr_json)
        else:
            context_mat = utils.get_context_material(context)
            linked_mats = get_linked_materials(chr_cache, context_mat, props.update_mode)
            if linked_mats:
                mats = [mat_cache.material for mat_cache in linked_mats]
                shaders.init_character_property_defaults(chr_cache, chr_json, only=mats)
        basic.init_basic_default(chr_cache)
        vars.block_property_update = False

        update_all_properties(context)


def update_all_properties(context, update_mode = None):
    if vars.block_property_update: return

    utils.start_timer()

    props = vars.props()
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)

    if chr_cache:

        processed = []

        for obj in chr_cache.get_cache_objects():
            obj_cache = chr_cache.get_object_cache(obj)
            if obj_cache and not obj_cache.disabled and obj_cache.is_mesh() and obj not in processed:

                processed.append(obj)

                for mat in obj.data.materials:
                    already_processed = mat in processed
                    mat_cache = chr_cache.get_material_cache(mat)

                    if chr_cache.setup_mode == "BASIC":

                        if not already_processed:
                            basic.update_basic_material(mat, mat_cache, "ALL")

                    else: # ADVANCED

                        shader_name = params.get_shader_name(mat_cache)
                        bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader_name)
                        shader_def = params.get_shader_def(shader_name)

                        if not already_processed:
                            shaders.apply_prop_matrix(bsdf_node, shader_node, mat_cache, shader_name)

                            if "textures" in shader_def.keys():
                                for tex_def in shader_def["textures"]:
                                    tiling_props = tex_def[5:]
                                    for prop_name in tiling_props:
                                        update_shader_property(obj, mat_cache, prop_name)

                        # modifiers need updating even if material already processed for split objects
                        if "modifiers" in shader_def.keys():
                            for mod_def in shader_def["modifiers"]:
                                prop_name = mod_def[0]
                                update_shader_property(obj, mat_cache, prop_name)

                        if not already_processed:
                            if "settings" in shader_def.keys():
                                for mat_def in shader_def["settings"]:
                                    prop_name = mat_def[0]
                                    update_shader_property(obj, mat_cache, prop_name)

                    processed.append(mat)

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
    props = vars.props()
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)
    if chr_cache:
        if prop_name == "detail_normal_strength":
            sculpting.update_layer_nodes(context, chr_cache, sculpting.LAYER_TARGET_DETAIL, "Normal Strength", chr_cache.detail_normal_strength * 1)
        elif prop_name == "body_normal_strength":
            sculpting.update_layer_nodes(context, chr_cache, sculpting.LAYER_TARGET_SCULPT, "Normal Strength", chr_cache.body_normal_strength * 1)
        elif prop_name == "detail_ao_strength":
            sculpting.update_layer_nodes(context, chr_cache, sculpting.LAYER_TARGET_DETAIL, "AO Strength", chr_cache.detail_ao_strength * 1)
        elif prop_name == "body_ao_strength":
            sculpting.update_layer_nodes(context, chr_cache, sculpting.LAYER_TARGET_SCULPT, "AO Strength", chr_cache.body_ao_strength * 1)
        elif prop_name == "detail_normal_definition":
            sculpting.update_layer_nodes(context, chr_cache, sculpting.LAYER_TARGET_DETAIL, "Definition", chr_cache.detail_normal_definition * 1)
        elif prop_name == "body_normal_definition":
            sculpting.update_layer_nodes(context, chr_cache, sculpting.LAYER_TARGET_SCULPT, "Definition", chr_cache.body_normal_definition * 1)
        elif prop_name == "detail_mix_mode":
            sculpting.update_layer_nodes(context, chr_cache, sculpting.LAYER_TARGET_DETAIL, "Mix Mode", (1.0 if chr_cache.detail_mix_mode == "REPLACE" else 0.0))
        elif prop_name == "body_mix_mode":
            sculpting.update_layer_nodes(context, chr_cache, sculpting.LAYER_TARGET_SCULPT, "Mix Mode", (1.0 if chr_cache.body_mix_mode == "REPLACE" else 0.0))


def update_rig_target(self, context):
    props = vars.props()
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
    link_props = vars.link_props()
    if link_props.link_target == "BLENDER":
        link_props.link_port = 9334
    elif link_props.link_target == "CCIC":
        link_props.link_port = 9333
    elif link_props.link_target == "UNITY":
        link_props.link_port = 9335
    else:
        link_props.link_port = 9333


def update_link_host(self, context):
    link_props = vars.link_props()
    host = link_props.link_host
    if host:
        try:
            link_props.link_host_ip = socket.gethostbyname(host)
        except:
            link_props.link_host_ip = "127.0.0.1"


def update_link_host_ip(self, context):
    link_props = vars.link_props()
    host_ip = link_props.link_host_ip
    if host_ip:
        try:
            link_props.link_host = socket.gethostbyaddr(host_ip)
        except:
            link_props.link_host = ""


def clean_collection_property(collection_prop):
    """Remove any item.disabled items from validatable objects in collection property."""
    repeat = True
    while repeat:
        repeat = False
        for item in collection_prop:
            valid_func = getattr(item, "validate", None)
            if callable(valid_func):
                if item.disabled:
                    repeat = True
                    utils.remove_from_collection(collection_prop, item)
                    break


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
            reset_parameters(context, all=False)

        if self.param == "RESET_ALL":
            reset_parameters(context, all=True)

        if self.param == "APPLY_ALL":
            update_all_properties(context)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "RESET":
            return "Reset parameters to the defaults for this material and any linked materials if in linked mode"
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
    skin_subsurface_saturation: bpy.props.FloatProperty(default=1.5, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_subsurface_saturation"))
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
    skin_height_scale: bpy.props.FloatProperty(default=0.3, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_height_scale"))
    skin_bump_scale: bpy.props.FloatProperty(default=0.3, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_bump_scale"))
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
    skin_subsurface_saturation: bpy.props.FloatProperty(default=1.5, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_subsurface_saturation"))
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
    skin_height_scale: bpy.props.FloatProperty(default=0.3, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_height_scale"))
    skin_bump_scale: bpy.props.FloatProperty(default=0.3, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_bump_scale"))


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
    eye_sclera_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_sclera_color"))
    eye_iris_inner_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_iris_inner_color"))
    eye_iris_cloudy_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.0, 0.0, 0.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_iris_cloudy_color"))
    eye_iris_inner_scale: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_iris_inner_scale"))
    eye_iris_transmission_opacity: bpy.props.FloatProperty(default=0.85, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_iris_transmission_opacity"))
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
    tearline_glossiness: bpy.props.FloatProperty(default=0.85, min=0, max=1.0, update=lambda s,c: update_property(s,c,"tearline_glossiness"))
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
    hair_anisotropic_roughness: bpy.props.FloatProperty(default=0.0375, min=0.0, max=0.15, update=lambda s,c: update_property(s,c,"hair_anisotropic_roughness"))
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
    hair_subsurface_saturation: bpy.props.FloatProperty(default=1.5, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_subsurface_saturation"))
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
    hair_alpha_power: bpy.props.FloatProperty(default=1, min=0.01, max=2, update=lambda s,c: update_property(s,c,"hair_alpha_power"))
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
    disabled: bpy.props.BoolProperty(default=False)

    def validate(self, report=None):
        if not self.disabled and not utils.image_exists(self.image):
            rep = f"Texture mapping: {self.texture_type} is no longer valid."
            utils.log_info(rep)
            if report is not None:
                report.append(rep)
            self.invalidate()
        return not self.disabled

    def invalidate(self):
        utils.log_detail(f" - Invalidating Texture mapping: {self.texture_type}")
        self.disabled = True

    def delete(self):
        if self.disabled and utils.image_exists(self.image):
            utils.log_detail(f" - Deleting texture mapping image: {self.image.name}")
            utils.purge_image(self.image)

    def clean_up(self):
        if self.disabled and utils.image_exists(self.image):
            utils.log_detail(f" - Cleaning up texture mapping: {self.image.name}")
            self.image = None


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

    def validate(self, report=None):
        if not self.disabled and not utils.material_exists(self.material):
            rep = f"Material: {self.source_name} no longer valid."
            utils.log_info(rep)
            if report is not None:
                report.append(rep)
            self.invalidate()
        else:
            tex_mapping: CC3TextureMapping
            for tex_mapping in self.texture_mappings:
                tex_mapping.validate(report)
            self.mixer_settings.validate(report)
        return not self.disabled

    def invalidate(self):
        utils.log_info(f"Invalidating Material cache: {self.source_name}")
        self.disabled = True
        tex_mapping: CC3TextureMapping
        for tex_mapping in self.texture_mappings:
            tex_mapping.invalidate()
        self.mixer_settings.invalidate()

    def delete(self):
        tex_mapping: CC3TextureMapping
        for tex_mapping in self.texture_mappings:
            tex_mapping.delete()
        self.mixer_settings.delete()
        if self.disabled:
            if utils.material_exists(self.material):
                utils.log_detail(f"Deleting Material: {self.material.name}")
                bpy.data.materials.remove(self.material)
            if utils.image_exists(self.temp_weight_map):
                utils.log_detail(f" - Deleting Temporary weight map image: {self.temp_weight_map.name}")
                utils.purge_image(self.temp_weight_map)

    def clean_up(self):
        tex_mapping: CC3TextureMapping
        for tex_mapping in self.texture_mappings:
            tex_mapping.clean_up()
        self.mixer_settings.clean_up()
        if self.disabled:
            utils.log_detail(f"Cleaning up material cache: {self.source_name}")
            self.texture_mappings.clear()
            self.material = None
            self.temp_weight_map = None


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
    use_collision_proxy: bpy.props.BoolProperty(default=False)
    collision_proxy_decimate: bpy.props.FloatProperty(default=0.125, min=0.0, max=1.0)
    vertex_count: bpy.props.IntProperty(default=0)
    face_count: bpy.props.IntProperty(default=0)
    edge_count: bpy.props.IntProperty(default=0)
    disabled: bpy.props.BoolProperty(default=False)
    json_path: bpy.props.StringProperty(default="")

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

    def get_object(self, return_invalid=False):
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

    def check_id(self):
        if self.object_id == "":
            self.object_id = utils.generate_random_id(20)
        if self.object:
            utils.set_rl_object_id(self.object, self.object_id)
            self.object["rl_object_type"] = self.object_type

    def validate(self, report=None, split_objects=None):
        objects_exist = utils.object_exists(self.object)
        if not objects_exist and split_objects:
            for split_obj in split_objects:
                if utils.object_exists(split_obj):
                    objects_exist = True
                    break
        if not self.disabled and not objects_exist:
            rep = f"Object: {self.source_name} no longer valid."
            utils.log_info(rep)
            if report is not None:
                report.append(rep)
            self.invalidate()
        return not self.disabled

    def invalidate(self):
        utils.log_info(f"Invalidating Object cache: {self.source_name}")
        self.disabled = True

    def delete(self):
        if self.disabled:
            if utils.object_exists(self.object):
                utils.log_info(f"Deleting Object: {self.object}")
                utils.delete_object_tree(self.object)

    def clean_up(self):
        if self.disabled:
            utils.log_info(f"Cleaning up Object: {self.source_name}")
            pass

    def validate_topography(self):
        obj = self.get_object()
        if utils.object_exists_is_mesh(obj):
            return (self.vertex_count == len(obj.data.vertices) and
                    self.face_count == len(obj.data.polygons) and
                    self.edge_count == len(obj.data.edges))


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
    # auto index
    auto_index: bpy.props.IntProperty(default=0)

    setup_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic","Build basic PBR materials."),
                        ("ADVANCED","Advanced","Build advanced materials with blend maps, subsurface, and micro normals, specular and roughness control and includes layered eye, teeth and tongue materials.")
                    ], default="ADVANCED")

    render_target: bpy.props.EnumProperty(items=[
                        ("EEVEE","Eevee","Build shaders for Eevee rendering."),
                        ("CYCLES","Cycles","Build shaders for Cycles rendering."),
                    ], default="EEVEE", name = "Target Renderer")

    physics_disabled: bpy.props.BoolProperty(default=False)
    physics_applied: bpy.props.BoolProperty(default=False)

    rigified: bpy.props.BoolProperty(default=False)
    rigified_full_face_rig: bpy.props.BoolProperty(default=False)
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

    disabled: bpy.props.BoolProperty(default=False)

    def get_auto_index(self):
        self.auto_index += 1
        return self.auto_index

    def select(self, only=True):
        arm = self.get_armature()
        if arm:
            utils.try_select_object(arm, clear_selection=only)
            utils.set_active_object(arm)
        else:
            self.select_all()

    def select_all(self, only=True):
        objects = self.get_all_objects(include_armature=True,
                                       include_children=True)
        utils.try_select_objects(objects, clear_selection=only)
        arm = self.get_armature()
        if arm:
            utils.set_active_object(arm)

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

    def can_standard_export(self):
        prefs = vars.prefs()
        result = True
        if prefs.export_require_key:
            if self.generation in vars.STANDARD_GENERATIONS and not self.get_import_has_key():
                result = False
        if self.rigified:
            result = False
        return result

    def can_go_cc(self):
        if self.rigified:
            return False
        if self.is_standard() and self.get_import_has_key():
            return True
        if self.is_morph():
            return True
        if self.is_non_standard():
            return True
        if self.is_prop():
            return True
        return False

    def can_go_ic(self):
        if self.is_prop():
            return True
        return False

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

    def cache_type(self):
        if self.is_avatar():
            return "AVATAR"
        else:
            return "PROP"
        return "NONE"

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
            self.generation == "ActorBuild" or
            self.generation == "AccuRig"):
            return True
        elif self.generation == "GameBase":
            return True
        return False

    def can_be_rigged(self):
        """Returns True if the character can be rigified."""
        if self.rigified:
            return False
        if (self.generation == "G3" or
            self.generation == "G3Plus" or
            self.generation == "NonStandardG3" or
            self.generation == "ActorBuild" or
            self.generation == "AccuRig"):
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
        prefs = vars.prefs()
        if self.rig_mode == "ADVANCED":
            return prefs.rigify_build_face_rig
        else:
            if self.can_rig_full_face():
                return prefs.rigify_build_face_rig
            else:
                return False

    def get_rig_mapping_data(self):
        return rigify_mapping_data.get_mapping_for_generation(self.generation)

    def get_rig_bone_mapping(self):
        rigify_data = rigify_mapping_data.get_mapping_for_generation(self.generation)
        if rigify_data:
            return rigify_data.bone_mapping
        return None

    def get_all_materials_cache(self, include_disabled=False):
        cache_all = []
        for mat_cache in self.tongue_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                cache_all.append(mat_cache)
        for mat_cache in self.teeth_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                cache_all.append(mat_cache)
        for mat_cache in self.head_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                cache_all.append(mat_cache)
        for mat_cache in self.skin_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                cache_all.append(mat_cache)
        for mat_cache in self.tearline_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                cache_all.append(mat_cache)
        for mat_cache in self.eye_occlusion_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                cache_all.append(mat_cache)
        for mat_cache in self.eye_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                cache_all.append(mat_cache)
        for mat_cache in self.hair_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                cache_all.append(mat_cache)
        for mat_cache in self.pbr_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                cache_all.append(mat_cache)
        for mat_cache in self.sss_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                cache_all.append(mat_cache)
        return cache_all

    def get_all_materials(self, include_disabled=False):
        materials = []
        for mat_cache in self.tongue_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                materials.append(mat_cache.material)
        for mat_cache in self.teeth_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                materials.append(mat_cache.material)
        for mat_cache in self.head_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                materials.append(mat_cache.material)
        for mat_cache in self.skin_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                materials.append(mat_cache.material)
        for mat_cache in self.tearline_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                materials.append(mat_cache.material)
        for mat_cache in self.eye_occlusion_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                materials.append(mat_cache.material)
        for mat_cache in self.eye_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                materials.append(mat_cache.material)
        for mat_cache in self.hair_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                materials.append(mat_cache.material)
        for mat_cache in self.pbr_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                materials.append(mat_cache.material)
        for mat_cache in self.sss_material_cache:
            if mat_cache.material and (include_disabled or not mat_cache.disabled):
                materials.append(mat_cache.material)
        return materials

    def is_sculpt_object(self, obj):
        return ("rl_multires_BODY" in obj or "rl_multires_DETAIL" in obj or
                obj == self.detail_multires_body or obj == self.sculpt_multires_body)

    def is_collision_object(self, obj):
        source, proxy, is_proxy = self.get_related_physics_objects(obj)
        result = ("rl_collision_proxy" in obj or obj.name.endswith("_Collision_Proxy") or is_proxy)
        return result

    def get_all_objects(self,
                        include_armature=True,
                        include_cache=True,
                        include_children=False,
                        include_disabled=False,
                        include_split=True,
                        include_proxy=False,
                        include_sculpt=False,
                        of_type="ALL",
                        only_selected=False):

        objects = []

        # cached objects
        for obj_cache in self.object_cache:
            if obj_cache.disabled and not include_disabled: continue
            obj = obj_cache.get_object()
            if obj and obj not in objects:
                if obj.type == "ARMATURE":
                    include = include_armature
                else:
                    include = include_cache
                if only_selected and obj not in bpy.context.selected_objects:
                    include = False
                if include:
                    if of_type == "ALL" or of_type == obj.type:
                        objects.append(obj)

        # non cached objects
        arm = self.get_armature()
        if arm:
            for child in arm.children:
                if child not in objects and utils.object_exists(child):
                    include = include_children
                    if include_proxy and self.is_collision_object(child):
                        include = True
                    if include_sculpt and self.is_sculpt_object(child):
                        include = True
                    if include_split and self.is_split_object(child):
                        include = True
                    if only_selected and child not in bpy.context.selected_objects:
                        include = False
                    if include:
                        if of_type == "ALL" or child.type == of_type:
                            objects.append(child)

        if include_sculpt:
            if self.sculpt_multires_body and self.sculpt_multires_body not in objects:
                objects.append(self.sculpt_multires_body)
            if self.detail_multires_body and self.detail_multires_body not in objects:
                objects.append(self.detail_multires_body)

        return objects

    def get_cache_objects(self):
        return self.get_all_objects(include_armature=True,
                                    include_cache=True,
                                    include_children=False,
                                    include_disabled=False,
                                    include_split=True,
                                    include_proxy=False,
                                    include_sculpt=False,
                                    of_type="ALL",
                                    only_selected=False)

    def get_collision_proxy(self, obj):
        obj_cache = self.get_object_cache(obj)
        arm = self.get_armature()
        for child in arm.children:
            if obj_cache.object_id == utils.get_rl_object_id(child):
                if "rl_collision_proxy" in child and child["rl_collision_proxy"] == obj.name:
                    return child
        proxy_name = obj.name + ".Collision_Proxy"
        for child in arm.children:
            if child.name == proxy_name:
                return child
        return None

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

    def is_split_object(self, obj) -> bool:
        obj_cache = self.get_object_cache(obj, strict=False)
        if obj_cache:
            return obj_cache.get_object() != obj
        return False

    def get_object_cache(self, obj, include_disabled=False, by_id=None, strict=False) -> CC3ObjectCache:
        """Returns the object cache for this object.
        """
        if obj:
            # by object
            if not strict and not by_id:
                by_id = utils.get_rl_object_id(obj)
            for obj_cache in self.object_cache:
                if include_disabled or not obj_cache.disabled:
                    cache_object = obj_cache.get_object()
                    if cache_object and cache_object == obj:
                        return obj_cache
            # by id
            if by_id:
                for obj_cache in self.object_cache:
                    if include_disabled or not obj_cache.disabled:
                        if obj_cache.object_id == by_id:
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

    def has_cache_objects(self, objects, include_disabled=False):
        """Returns True if *any* of the objects are actively the object cache.
        """
        object_ids = [ utils.get_rl_object_id(o) for o in objects ]
        for obj_cache in self.object_cache:
            if include_disabled or not obj_cache.disabled:
                cache_object = obj_cache.get_object()
                if cache_object in objects:
                    return True
                if obj_cache.object_id and obj_cache.object_id in object_ids:
                    return True
        return False

    def has_child_objects(self, objects):
        arm = self.get_armature()
        if arm:
            for obj in objects:
                if obj.parent == arm:
                    return True
        return False

    def has_object(self, obj, include_disabled=False):
        """Returns True if the object is in the object cache.
        """
        if obj:
            object_id = utils.get_rl_object_id(obj)
            for obj_cache in self.object_cache:
                if include_disabled or not obj_cache.disabled:
                    cache_object = obj_cache.get_object()
                    cache_object_id = utils.get_rl_object_id(cache_object)
                    if cache_object == obj or cache_object_id == object_id:
                        return True
        return False

    def get_split_objects(self, obj):
        split_objects = []
        if type(obj) is CC3ObjectCache:
            obj = obj.get_object()
        if obj:
            split_objects.append(obj)
            obj_id = utils.get_rl_object_id(obj)
            arm = self.get_armature()
            if arm:
                for child in arm.children:
                    if child not in split_objects:
                        child_id = utils.get_rl_object_id(child)
                        if child_id == obj_id:
                            split_objects.append(obj)
        return split_objects

    def get_armature(self, include_disabled=False):
        try:
            for obj_cache in self.object_cache:
                if include_disabled or not obj_cache.disabled:
                    cache_object = obj_cache.get_object()
                    if utils.object_exists_is_armature(cache_object):
                        return cache_object
        except:
            pass
        return None

    def get_body(self):
        return self.get_object_of_type("BODY")

    def get_body_cache(self):
        return self.get_cache_of_type("BODY")

    def get_objects_of_type(self, object_type):
        objects = []
        for obj_cache in self.object_cache:
            if obj_cache.object_type == object_type:
                body_id = obj_cache.object_id
                chr_objects = self.get_cache_objects()
                for obj in chr_objects:
                    if utils.get_rl_object_id(obj) == body_id:
                        objects.append(obj)
        return objects

    def get_object_of_type(self, object_type, include_disabled=False):
        try:
            for obj_cache in self.object_cache:
                if include_disabled or not obj_cache.disabled:
                    cache_object = obj_cache.get_object()
                    if cache_object and obj_cache.object_type == object_type:
                        return cache_object
        except:
            pass
        return None

    def get_cache_of_type(self, object_type, include_disabled=False):
        try:
            for obj_cache in self.object_cache:
                if include_disabled or not obj_cache.disabled:
                    if obj_cache.object_type == object_type:
                        return obj_cache
        except:
            pass
        return None

    def set_rigify_armature(self, new_arm):
        self.rigified = True
        try:
            for obj_cache in self.object_cache:
                if not obj_cache.disabled:
                    cache_object = obj_cache.get_object()
                    if cache_object.type == "ARMATURE":
                        self.rig_original_rig = cache_object
                        obj_cache.set_object(new_arm)
                        # update the object id
                        obj_cache.object_id = utils.generate_random_id(20)
                        utils.set_rl_object_id(new_arm, obj_cache.object_id)
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
            if obj.type == "MESH":
                obj_cache.vertex_count = len(obj.data.vertices)
                obj_cache.face_count = len(obj.data.polygons)
                obj_cache.edge_count = len(obj.data.edges)
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

    def count_material(self, mat):
        count = 0
        for obj_cache in self.object_cache:
            objects = self.get_split_objects(obj_cache)
            for obj in objects:
                if obj and obj.type == "MESH":
                    for m in obj.data.materials:
                        if m == mat:
                            count += 1
        return count

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


    def add_material_cache(self, mat,
                           create_type = "DEFAULT",
                           is_user=False,
                           copy_from=None):

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
                if is_user:
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

    def get_sculpt_objects(self):
        sculpt_objects = self.get_all_objects(include_armature=False,
                                              include_cache=False,
                                              include_children=False,
                                              include_disabled=False,
                                              include_split=False,
                                              include_proxy=False,
                                              include_sculpt=True,
                                              of_type="MESH")
        return sculpt_objects

    def get_sculpt_source(self, multires_mesh, layer_target):
        prop_name = f"rl_multires_{layer_target}"
        if prop_name in multires_mesh:
            source_name = multires_mesh[prop_name]
            if source_name in bpy.data.objects:
                return bpy.data.objects[source_name]
        return None

    def get_detail_body(self, context_object=None):
        sculpt_objects = self.get_sculpt_objects()
        if context_object:
            for obj in sculpt_objects:
                source = self.get_sculpt_source(obj, sculpting.LAYER_TARGET_DETAIL)
                if obj == context_object or source == context_object:
                    return obj
            return None
        # detail_multires_body contains the last edited detail sculpt object
        if utils.object_exists_is_mesh(self.detail_multires_body):
            return self.detail_multires_body
        else:
            return None

    def get_sculpt_body(self, context_object=None):
        sculpt_objects = self.get_sculpt_objects()
        if context_object:
            for obj in sculpt_objects:
                source = self.get_sculpt_source(obj, sculpting.LAYER_TARGET_SCULPT)
                if obj == context_object or source == context_object:
                    return obj
            return None
        # sculpt_multires_body contains the last edited body sculpt object
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
        obj_cache = self.get_object_cache(obj)
        if obj_cache:
            proxy = self.get_collision_proxy(obj)
            if proxy:
                is_proxy = False
                return obj, proxy, is_proxy
            if "rl_collision_proxy" in obj or obj.name.endswith(".Collision_Proxy"):
                proxy = obj
                is_proxy = True
                obj = self.find_object_from_proxy(proxy)
                return obj, proxy, is_proxy
        return obj, proxy, is_proxy

    def find_object_from_proxy(self, proxy, include_disabled=False):
        if "rl_collision_proxy" in proxy:
            proxy_object_id = utils.get_rl_object_id(proxy)
            for obj in self.get_cache_objects():
                obj_cache = self.get_object_cache(obj)
                if include_disabled or not obj_cache.disabled:
                    if utils.get_rl_object_id(obj) == proxy_object_id and obj.name == proxy["rl_collision_proxy"]:
                        return obj
        if proxy.name.endswith(".Collision_Proxy"):
            obj_name = proxy.name[:-16]
            for obj in self.get_cache_objects():
                obj_cache = self.get_object_cache(obj)
                if include_disabled or not obj_cache.disabled:
                    if obj.name == obj_name:
                        return obj
        return None

    def is_valid_for_export(self):
        """If the character is a standard cc3+ character, is the body topology valid for export"""
        if self.is_standard():
            body = None
            body_cache = None
            for obj_cache in self.object_cache:
                if obj_cache.object_type == "BODY":
                    body = obj_cache.get_object()
                    if body:
                        body_cache = obj_cache
                        break
                    else:
                        body_cache = None
            if body and body_cache:
                if self.generation == "G3":
                    if (len(body.data.vertices) == 13286 and
                        len(body.data.edges) == 26374 and
                        len(body.data.polygons) == 13100):
                        return True
                elif self.generation == "G3Plus":
                    if (len(body.data.vertices) == 14164 and
                        len(body.data.edges) == 28202 and
                        len(body.data.polygons) == 14046):
                        return True
            return False
        else:
            return True

    def get_link_id(self):
        if not self.link_id:
            self.link_id = utils.generate_random_id(20)
        return self.link_id

    def validate(self, report=None):
        """Checks character objects and materials are still valid.
           Returns True if any objects in the character are still valid"""
        obj_cache: CC3ObjectCache
        mat_cache: CC3MaterialCache
        any_valid = False
        for obj_cache in self.object_cache:
            split_objects = self.get_split_objects(obj_cache)
            obj_valid = obj_cache.validate(report=report, split_objects=split_objects)
            any_valid = any_valid or obj_valid
        all_materials_cache = self.get_all_materials_cache(True)
        for mat_cache in all_materials_cache:
            mat_valid = mat_cache.validate(report)
        if not any_valid:
            rep = f"Character Cache: {self.character_name} is no longer valid!"
            utils.log_info(rep)
            if report is not None:
                report.append(rep)
            self.invalidate()
        return not self.disabled

    def invalidate(self):
        utils.log_info(f"Invalidating Character cache: {self.character_name}")
        self.disabled = True
        obj_cache: CC3ObjectCache
        mat_cache: CC3MaterialCache
        for obj_cache in self.object_cache:
            obj_cache.invalidate()
        all_materials_cache = self.get_all_materials_cache(include_disabled=True)
        for mat_cache in all_materials_cache:
            mat_cache.invalidate()

    def delete(self):
        obj_cache: CC3ObjectCache
        mat_cache: CC3MaterialCache
        for obj in self.get_cache_objects():
            proxy = self.get_collision_proxy(obj)
            if proxy:
                utils.delete_object_tree(proxy)
        for obj_cache in self.object_cache:
            obj_cache.delete()
        all_materials_cache = self.get_all_materials_cache(include_disabled=True)
        for mat_cache in all_materials_cache:
            mat_cache.delete()
        if self.disabled:
            utils.log_info(f"Deleting Character Meta Objects: {self.character_name}")
            utils.delete_object_tree(self.rig_meta_rig)
            utils.delete_object_tree(self.rig_export_rig)
            utils.delete_object_tree(self.rig_original_rig)
            utils.delete_object_tree(self.rig_retarget_rig)
            utils.delete_object_tree(self.rig_datalink_rig)
            utils.delete_object_tree(self.rig_retarget_source_rig)
            utils.delete_object(self.detail_multires_body)
            utils.delete_object(self.sculpt_multires_body)

    def clean_up(self):
        obj_cache: CC3ObjectCache
        mat_cache: CC3MaterialCache
        for obj_cache in self.object_cache:
            obj_cache.clean_up()
        all_materials_cache = self.get_all_materials_cache(include_disabled=True)
        for mat_cache in all_materials_cache:
            mat_cache.clean_up()
        if self.disabled:
            utils.log_detail(f"Clearing object cache.")
            self.object_cache.clear()
            utils.log_detail(f"Clearing all material cache.")
            self.tongue_material_cache.clear()
            self.teeth_material_cache.clear()
            self.head_material_cache.clear()
            self.skin_material_cache.clear()
            self.tearline_material_cache.clear()
            self.eye_occlusion_material_cache.clear()
            self.eye_material_cache.clear()
            self.hair_material_cache.clear()
            self.pbr_material_cache.clear()
            self.sss_material_cache.clear()
            self.proportion_editing_actions.clear()
        else:
            utils.log_detail(f"Cleaning up object cache.")
            clean_collection_property(self.object_cache)
            utils.log_detail(f"Cleaning up all material cache.")
            clean_collection_property(self.tongue_material_cache)
            clean_collection_property(self.teeth_material_cache)
            clean_collection_property(self.head_material_cache)
            clean_collection_property(self.skin_material_cache)
            clean_collection_property(self.tearline_material_cache)
            clean_collection_property(self.eye_occlusion_material_cache)
            clean_collection_property(self.eye_material_cache)
            clean_collection_property(self.hair_material_cache)
            clean_collection_property(self.pbr_material_cache)
            clean_collection_property(self.sss_material_cache)


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
    eevee_options: bpy.props.BoolProperty(default=False)
    stage1: bpy.props.BoolProperty(default=True)
    stage1_details: bpy.props.BoolProperty(default=False)
    stage4: bpy.props.BoolProperty(default=True)
    stage_remapper: bpy.props.BoolProperty(default=False)
    show_build_prefs: bpy.props.BoolProperty(default=False)
    show_build_prefs2: bpy.props.BoolProperty(default=False)
    section_rigify_setup: bpy.props.BoolProperty(default=True)
    section_rigify_retarget: bpy.props.BoolProperty(default=True)
    section_rigify_action_sets: bpy.props.BoolProperty(default=True)
    section_rigify_controls: bpy.props.BoolProperty(default=False)
    section_rigify_spring: bpy.props.BoolProperty(default=False)
    section_rigidbody_spring_ui: bpy.props.BoolProperty(default=True)
    section_physics_cloth_settings: bpy.props.BoolProperty(default=False)
    section_physics_collision_settings: bpy.props.BoolProperty(default=False)
    show_data_link_prefs: bpy.props.BoolProperty(default=False)
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


    # rigify
    rigify_retarget_use_fake_user: bpy.props.BoolProperty(default=True, name="Fake User")
    rigify_retarget_motion_prefix: bpy.props.StringProperty(default="", name="Rigify Retarget Motion Prefix",
                                                   description="Motion prefix for retargeted motions.")
    rigify_bake_use_fake_user: bpy.props.BoolProperty(default=True, name="Fake User")
    rigify_bake_motion_prefix: bpy.props.StringProperty(default="", name="Rigify Bake Motion Prefix",
                                                   description="Motion prefix for baked NLA motions.")
    rigify_bake_motion_name: bpy.props.StringProperty(default="NLA_Bake", name="Rigify Bake Motion Name",
                                                   description="Motion name for baked NLA motions.")
    filter_motion_set: bpy.props.BoolProperty(default=True, name="Filter",
                                                  description="Show only motion sets compatible with the current character")

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
    action_set_list_index: bpy.props.IntProperty(default=-1)
    action_set_list_action: bpy.props.PointerProperty(type=bpy.types.Action)
    armature_list_index: bpy.props.IntProperty(default=-1)
    armature_list_object: bpy.props.PointerProperty(type=bpy.types.Object)
    unity_action_list_index: bpy.props.IntProperty(default=-1)
    unity_action_list_action: bpy.props.PointerProperty(type=bpy.types.Action)
    rigified_action_list_index: bpy.props.IntProperty(default=-1)
    rigified_action_list_action: bpy.props.PointerProperty(type=bpy.types.Action)

    wrinkle_regions: bpy.props.EnumProperty(items=[
                        ("ALL", "All", "All Regions"),
                        ("01", " 1 - Brow Raise", "Brow Raise"),
                        ("02", " 2 - Brow Drop", "Brow Drop"),
                        ("03", " 3 - Blink", "Blink"),
                        ("04", " 4 - Squint", "Squint"),
                        ("05", " 5 - Nose", "Nose"),
                        ("06", " 6 - Cheek Raise", "Cheek Raise"),
                        ("07", " 7 - Nostril Crease", "Nostril Crease"),
                        ("08", " 8 - Purse Lips", "Purse Lips"),
                        ("09", " 9 - Smile Lip Stretch", "Smile Lip Stretch"),
                        ("10", "10 - Mouth Stretch", "Mouth Stretch"),
                        ("11", "11 - Chin", "Chin"),
                        ("12", "12 - Jaw", "Jaw"),
                        ("13", "13 - Neck Stretch", "Neck Stretch"),
                    ], default="ALL", name = "Wrinkle Region")
    wrinkle_strength: bpy.props.FloatProperty(default=1.0, min=0.0, max=2.0, name = "Wrinkle Strength",
                                              update=update_wrinkle_strength_all)
    wrinkle_curve: bpy.props.FloatProperty(default=1.0, min=0.1, max=2.0, name = "Wrinkle Curve",
                                              update=update_wrinkle_curve_all)

    #
    light_filter: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                                default=(1.0, 1.0, 1.0, 1.0),
                                                min = 0.0, max = 1.0)
    lighting_setup_compositor: bpy.props.BoolProperty(default=False)
    lighting_setup_camera: bpy.props.BoolProperty(default=False)
    lighting_brightness_all: bpy.props.BoolProperty(default=False,
                                                    name="All Lights",
                                                    description="Adjust all lights with the lighting brightness slider, not just the ones created by this add-on")
    lighting_brightness: bpy.props.FloatProperty(default=1.0, min=0.0, max=2.0,
                                                 name="Lighting Brightness",
                                                 description="Adjust the lighting brightness of all lights created by this add-on",
                                                 update=adjust_lighting_brightness)
    world_brightness: bpy.props.FloatProperty(default=1.0, min=0.0, max=2.0,
                                                 name="World Brightness",
                                                 description="Adjust the world background brightness if the world setup was created by this add-on",
                                                 update=adjust_world_brightness)


    def add_character_cache(self, copy_from=None):
        chr_cache = self.import_cache.add()
        if copy_from:
            exclude_list = ["*_material_cache", "object_cache"]
            utils.copy_property_group(copy_from, chr_cache, exclude=exclude_list)
        return chr_cache

    def get_character_cache_from_objects(self, objects, search_materials=False):
        chr_cache : CC3CharacterCache

        if objects:
            for chr_cache in self.import_cache:
                if not chr_cache.disabled:
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
                    if not chr_cache.disabled and chr_cache.has_any_materials(materials):
                        return chr_cache
        return None

    def get_character_cache(self, obj, mat, by_id=None):
        if obj:
            if not by_id:
                by_id = utils.get_rl_object_id(obj)
            for chr_cache in self.import_cache:
                if not chr_cache.disabled:
                    obj_cache = chr_cache.get_object_cache(obj, by_id=by_id)
                    if obj_cache and not obj_cache.disabled:
                        return chr_cache
        if mat:
            for chr_cache in self.import_cache:
                if not chr_cache.disabled:
                    mat_cache = chr_cache.get_material_cache(mat)
                    if mat_cache and not mat_cache.disabled:
                        return chr_cache
        return None

    def get_characters_by_link_id(self, character_ids):
        characters = []
        for chr_cache in self.import_cache:
            if chr_cache.link_id in character_ids:
                characters.append(chr_cache)
        return characters

    def get_avatars(self):
        avatars = []
        chr_cache: CC3CharacterCache
        for chr_cache in self.import_cache:
            if not chr_cache.disabled and chr_cache.is_avatar():
                avatars.append(chr_cache)
        return avatars

    def get_first_avatar(self):
        chr_cache: CC3CharacterCache
        for chr_cache in self.import_cache:
            if not chr_cache.disabled and chr_cache.is_avatar():
                return chr_cache
        return None

    def find_character_by_name(self, name):
        if name:
            for chr_cache in self.import_cache:
                if not chr_cache.disabled and chr_cache.character_name == name:
                    return chr_cache
        return None

    def find_character_by_link_id(self, link_id):
        if link_id:
            for chr_cache in self.import_cache:
                if not chr_cache.disabled and chr_cache.link_id == link_id:
                    return chr_cache
        return None

    def get_context_character_cache(self, context=None, strict=False):
        context = vars.get_context(context)

        chr_cache = None

        # if there is only one character in the scene, this is the only possible character cache:
        if not strict and len(self.import_cache) == 1:
            return self.import_cache[0]

        obj = context.object

        # otherwise determine the context character cache:
        chr_cache = self.get_character_cache(obj, None)

        # try to find a character from the selected objects
        if chr_cache is None and len(context.selected_objects) > 1:
            chr_cache = self.get_character_cache_from_objects(context.selected_objects, False)

        return chr_cache

    def get_object_cache(self, obj, include_disabled=False):
        if obj:
            for chr_cache in self.import_cache:
                obj_cache = chr_cache.get_object_cache(obj, include_disabled=include_disabled)
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
        prefs = vars.prefs()
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
        self.action_set_list_action = utils.collection_at_index(self.action_set_list_index, bpy.data.actions)
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

    def validate(self, report=None):
        validation = True
        chr_cache: CC3CharacterCache
        for chr_cache in self.import_cache:
            if not chr_cache.validate(report):
                chr_cache.invalidate()
                validation = False
        return validation

    def clean_up(self):
        chr_cache: CC3CharacterCache
        for chr_cache in self.import_cache:
            chr_cache.clean_up()
        clean_collection_property(self.import_cache)

    def validate_and_clean_up(self):
        self.validate()
        self.clean_up()


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
                    ], default="CCIC", name = "DataLink Target", update=update_link_target)
    link_port: bpy.props.IntProperty(default=9333)
    link_status: bpy.props.StringProperty(default="")
    remote_app: bpy.props.StringProperty(default="")
    remote_version: bpy.props.StringProperty(default="")
    remote_path: bpy.props.StringProperty(default="")
    remote_exe: bpy.props.StringProperty(default="")
    connected: bpy.props.BoolProperty(default=False)
