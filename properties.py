# Copyright (C) 2021 Victor Soupday
# This file is part of CC3_Blender_Tools <https://github.com/soupday/cc3_blender_tools>
#
# CC3_Blender_Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CC3_Blender_Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CC3_Blender_Tools.  If not, see <https://www.gnu.org/licenses/>.

import bpy

from . import meshutils, materials, modifiers, nodeutils, shaders, params, physics, jsonutils, utils, vars


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


def reset_material_parameters(cache):
    props: CC3ImportProps = bpy.context.scene.CC3ImportProps
    params = cache.parameters


def update_property(self, context, prop_name, update_mode = None):
    if vars.block_property_update: return

    utils.start_timer()

    props = bpy.context.scene.CC3ImportProps
    chr_cache: CC3CharacterCache = props.get_context_character_cache(context)

    if chr_cache:

        # get the context (currently active) material
        context_obj = context.object
        context_mat = utils.context_material(context)
        context_mat_cache = chr_cache.get_material_cache(context_mat)

        if context_obj and context_mat and context_mat_cache:

            if update_mode is None:
                update_mode = props.update_mode

            all_materials_cache = chr_cache.get_all_materials_cache()
            linked = get_linked_material_types(context_mat_cache)
            paired = get_paired_material_types(context_mat_cache)

            for mat_cache in all_materials_cache:
                mat = mat_cache.material

                if mat:

                    if mat == context_mat:
                        # Always update the currently active material
                        update_shader_property(context_obj, mat, mat_cache, prop_name)

                    elif mat_cache.material_type in paired:
                        # Update paired materials
                        set_linked_property(prop_name, context_mat_cache, mat_cache)
                        update_shader_property(context_obj, mat, mat_cache, prop_name)

                    elif update_mode == "UPDATE_LINKED":
                        # Update all other linked materials in the imported objects material cache:
                        if mat_cache.material_type in linked:
                            set_linked_property(prop_name, context_mat_cache, mat_cache)
                            update_shader_property(context_obj, mat, mat_cache, prop_name)

            # these properties will cause the eye displacement vertex group to change...
            if prop_name in ["eye_iris_depth_radius", "eye_iris_scale", "eye_iris_radius"]:
                meshutils.rebuild_eye_vertex_groups(chr_cache)

    utils.log_timer("update_property()", "ms")


def get_linked_material_types(cache):
    if cache:
        for linked in params.LINKED_MATERIALS:
            if cache.material_type in linked:
                return linked
        return [cache.material_type]
    return []


def get_paired_material_types(cache):
    if cache:
        for paired in params.PAIRED_MATERIALS:
            if cache.material_type in paired:
                return paired
    return []


def set_linked_property(prop_name, active_cache, cache):
    vars.block_property_update = True
    code = ""

    try:
        code = "cache.parameters." + prop_name + " = active_cache.parameters." + prop_name
        exec(code, None, locals())
    except Exception as e:
        utils.log_error("set_linked_property(): Unable to evaluate: " + code, e)

    vars.block_property_update = False


def update_shader_property(obj, mat, mat_cache, prop_name):
    props = bpy.context.scene.CC3ImportProps

    if mat and mat.node_tree and mat_cache:

        shader_name = params.get_shader_lookup(mat_cache)
        shader_node = nodeutils.get_shader_node(mat, shader_name)
        shader_def = params.get_shader_def(shader_name)

        if shader_def:

            if "inputs" in shader_def.keys():
                update_shader_input(shader_node, mat_cache, prop_name, shader_def["inputs"])

            if "textures" in shader_def.keys():
                update_shader_tiling(shader_name, mat, mat_cache, prop_name, shader_def["textures"])

            if "modifiers" in shader_def.keys():
                update_object_modifier(obj, mat_cache, prop_name, shader_def["modifiers"])

            if "settings" in shader_def.keys():
                update_material_setting(mat, mat_cache, prop_name, shader_def["settings"])

        else:
            utils.log_error("No shader definition for: " + shader_name)


def update_shader_input(shader_node, mat_cache, prop_name, input_defs):
    for input_def in input_defs:
        if prop_name in input_def[2:]:
            nodeutils.set_node_input(shader_node, input_def[0], shaders.eval_input_param(input_def, mat_cache))


def update_shader_tiling(shader_name, mat, mat_cache, prop_name, texture_defs):
    for texture_def in texture_defs:
        if len(texture_def) > 5:
            tiling_props = texture_def[5:]
            texture_type = texture_def[2]
            if prop_name in tiling_props:
                tiling_node = nodeutils.get_tiling_node(mat, shader_name, texture_type)
                nodeutils.set_node_input(tiling_node, "Tiling", shaders.eval_tiling_param(texture_def, mat_cache))


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

        init_material_property_defaults(chr_cache, chr_json)

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
            obj = obj_cache.object
            if obj not in processed:
                processed.append(obj)
                if obj.type == "MESH":
                    for mat in obj.data.materials:
                        if mat not in processed:
                            processed.append(mat)
                            mat_cache = chr_cache.get_material_cache(mat)
                            shader_name = params.get_shader_lookup(mat_cache)
                            shader_node = nodeutils.get_shader_node(mat, shader_name)
                            shader_def = params.get_shader_def(shader_name)

                            shaders.apply_prop_matrix(shader_node, mat_cache, shader_name)

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


def init_material_property_defaults(chr_cache, chr_json):
    processed = []

    utils.log_info("")
    utils.log_info("Initializing Material Property Defaults:")
    utils.log_info("----------------------------------------")
    if chr_json:
        utils.log_info("(Using Json Data)")
    else:
        utils.log_info("(No Json Data)")

    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
        if obj.type == "MESH" and obj not in processed:
            processed.append(obj)

            obj_json = jsonutils.get_object_json(chr_json, obj)
            utils.log_info("Object: " + obj.name + " (" + obj_cache.object_type + ")")

            for mat in obj.data.materials:
                if mat not in processed:
                    processed.append(mat)

                    mat_cache = chr_cache.get_material_cache(mat)
                    if mat_cache:

                        mat_json = jsonutils.get_material_json(obj_json, mat)
                        utils.log_info("  Material: " + mat.name + " (" + mat_cache.material_type + ")")

                        if mat_cache.is_eye():
                            cornea_mat, cornea_mat_cache = materials.get_cornea_mat(obj, mat, mat_cache)
                            mat_json = jsonutils.get_material_json(obj_json, cornea_mat)

                        shaders.fetch_prop_defaults(mat_cache, mat_json)


class CC3HeadParameters(bpy.types.PropertyGroup):
    # shader (rl_head_shader)
    skin_cavity_ao_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_cavity_ao_strength"))
    skin_blend_overlay_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_blend_overlay_strength"))
    skin_ao_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_ao_strength"))
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
    skin_normal_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_normal_strength"))
    skin_micro_normal_strength: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_micro_normal_strength"))
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
                            default=(0, 0, 0, 1.0), min = 0.0, max = 1.0,
                            update=lambda s,c: update_property(s,c,"skin_emissive_color"))
    skin_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_emission_strength"))
    # tiling (rl_head_shader_skin_micro_normal_tiling)
    skin_micro_normal_tiling: bpy.props.FloatProperty(default=20, min=0, max=50, update=lambda s,c: update_property(s,c,"skin_micro_normal_tiling"))

class CC3SkinParameters(bpy.types.PropertyGroup):
    # shader (rl_skin_shader)
    skin_ao_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_ao_strength"))
    skin_subsurface_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1.0, 0.112, 0.072, 1.0), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"skin_subsurface_falloff"))
    skin_subsurface_radius: bpy.props.FloatProperty(default=1.5, min=0, max=3, update=lambda s,c: update_property(s,c,"skin_subsurface_radius"))
    skin_specular_scale: bpy.props.FloatProperty(default=0.4, min=0, max=2, update=lambda s,c: update_property(s,c,"skin_specular_scale"))
    skin_roughness_power: bpy.props.FloatProperty(default=0.8, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_roughness_power"))
    skin_roughness_min: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_roughness_min"))
    skin_roughness_max: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_roughness_max"))
    skin_normal_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_normal_strength"))
    skin_micro_normal_strength: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"skin_micronormal_strength"))
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
                            default=(0, 0, 0, 1.0), min = 0.0, max = 1.0,
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
    eye_limbus_width: bpy.props.FloatProperty(default=0.055, min=0.01, max=0.2, update=lambda s,c: update_property(s,c,"eye_limbus_width"))
    eye_limbus_dark_radius: bpy.props.FloatProperty(default=0.1, min=0.01, max=0.2, update=lambda s,c: update_property(s,c,"eye_limbus_dark_radius"))
    eye_limbus_dark_width: bpy.props.FloatProperty(default=0.025, min=0.01, max=0.1, update=lambda s,c: update_property(s,c,"eye_limbus_dark_width"))
    eye_limbus_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.0, 0.0, 0.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_limbus_color"))
    eye_shadow_radius: bpy.props.FloatProperty(default=0.3, min=0.0, max=0.5, update=lambda s,c: update_property(s,c,"eye_shadow_radius"))
    eye_shadow_hardness: bpy.props.FloatProperty(default=0.5, min=0.01, max=0.99, update=lambda s,c: update_property(s,c,"eye_shadow_hardness"))
    eye_corner_shadow_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 0.497, 0.445, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"eye_corner_shadow_color"))
    eye_color_blend_strength: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_color_blend_strength"))
    eye_sclera_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0, 0, 0, 1.0), min=0.0, max=1.0, update=lambda s,c: update_property(s,c,"eye_sclera_emissive_color"))
    eye_sclera_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_sclera_emission_strength"))
    eye_iris_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0, 0, 0, 1.0), min=0.0, max=1.0, update=lambda s,c: update_property(s,c,"eye_iris_emissive_color"))
    eye_iris_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_iris_emission_strength"))
    eye_sclera_normal_strength: bpy.props.FloatProperty(default=0.1, min=0, max=1, update=lambda s,c: update_property(s,c,"eye_sclera_normal_strength"))
    eye_sclera_normal_tiling: bpy.props.FloatProperty(default=2.0, min=0, max=10, update=lambda s,c: update_property(s,c,"eye_sclera_normal_tiling"))
    # non shader properties
    eye_refraction_depth: bpy.props.FloatProperty(default=1, min=0, max=5, update=lambda s,c: update_property(s,c,"eye_refraction_depth"))
    eye_ior: bpy.props.FloatProperty(default=1.4, min=1.01, max=2.5, update=lambda s,c: update_property(s,c,"eye_ior"))
    eye_blood_vessel_height: bpy.props.FloatProperty(default=0.5, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_blood_vessel_height"))
    eye_iris_bump_height: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"eye_iris_bump_height"))
    eye_iris_depth: bpy.props.FloatProperty(default=0.9, min=0.0, max=2.5, update=lambda s,c: update_property(s,c,"eye_iris_depth"))
    eye_iris_depth_radius: bpy.props.FloatProperty(default=0.8, min=0.0, max=1.0, update=lambda s,c: update_property(s,c,"eye_iris_depth_radius"))
    eye_pupil_scale: bpy.props.FloatProperty(default=0.8, min=0.25, max=2.0, update=lambda s,c: update_property(s,c,"eye_pupil_scale"))


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
                        default=(0, 0, 0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"teeth_emissive_color"))
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
                        default=(0, 0, 0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"tongue_emissive_color"))
    tongue_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"tongue_emission_strength"))


class CC3HairParameters(bpy.types.PropertyGroup):
    # shader
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
    hair_anisotropic_roughness: bpy.props.FloatProperty(default=1.15, min=1.0, max=2.5, update=lambda s,c: update_property(s,c,"hair_anisotropic_roughness"))
    hair_anisotropic_strength: bpy.props.FloatProperty(default=0.8, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_anisotropic_strength"))
    hair_anisotropic_strength2: bpy.props.FloatProperty(default=0.4, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_anisotropic_strength2"))
    hair_anisotropic_strength_cycles: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_anisotropic_strength_cycles"))
    hair_anisotropic_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(0.05, 0.038907, 0.0325, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_anisotropic_color"))
    hair_subsurface_scale: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_subsurface_scale"))
    hair_subsurface_falloff: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                        default=(1.0, 1.0, 1.0, 1.0), min = 0.0, max = 1.0, update=lambda s,c: update_property(s,c,"hair_subsurface_falloff"))
    hair_subsurface_radius: bpy.props.FloatProperty(default=1.0, min=0.1, max=5, update=lambda s,c: update_property(s,c,"hair_subsurface_radius"))
    hair_diffuse_strength: bpy.props.FloatProperty(default=1.0, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_diffuse_strength"))
    hair_ao_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_ao_strength"))
    hair_blend_multiply_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_blend_multiply_strength"))
    hair_specular_scale: bpy.props.FloatProperty(default=0.3, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_specular_scale"))
    hair_roughness_strength: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_roughness_strength"))
    hair_alpha_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_alpha_strength"))
    hair_opacity: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"hair_opacity"))
    hair_normal_strength: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"hair_normal_strength"))
    hair_bump_strength: bpy.props.FloatProperty(default=1, min=-3, max=3, update=lambda s,c: update_property(s,c,"hair_bump_strength"))
    hair_displacement_strength: bpy.props.FloatProperty(default=0, min=-3, max=3, update=lambda s,c: update_property(s,c,"hair_displacement_strength"))
    hair_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(0, 0, 0, 1.0), min = 0.0, max = 1.0,
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
    default_blend_multiply_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_blend_multiply_strength"))
    default_specular_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_specular_strength"))
    default_specular_scale: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_specular_scale"))
    default_specular_map: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"default_specular_map"))
    default_specular_mask: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_specular_mask"))
    default_roughness_power: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_roughness_power"))
    default_roughness_min: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_roughness_min"))
    default_roughness_max: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_roughness_max"))
    default_alpha_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_alpha_strength"))
    default_opacity: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_opacity"))
    default_normal_strength: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_normal_strength"))
    default_bump_strength: bpy.props.FloatProperty(default=1, min=-3, max=3, update=lambda s,c: update_property(s,c,"default_bump_strength"))
    default_displacement_strength: bpy.props.FloatProperty(default=1, min=-3, max=3, update=lambda s,c: update_property(s,c,"default_displacement_strength"))
    default_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(0, 0, 0, 1.0), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"default_emissive_color"))
    default_emission_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_emission_strength"))


class CC3SSSParameters(bpy.types.PropertyGroup):
    # Default
    default_diffuse_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(1, 1, 1, 1), min = 0.0, max = 1.0,
                                update=lambda s,c: update_property(s,c,"default_diffuse_color"))
    default_hue: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"default_hue"))
    default_brightness: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_brightness"))
    default_saturation: bpy.props.FloatProperty(default=0.95, min=0, max=1, update=lambda s,c: update_property(s,c,"default_saturation"))
    default_hsv_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_hsv_strength"))
    default_ao_strength: bpy.props.FloatProperty(default=1.0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_ao_strength"))
    default_blend_multiply_strength: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_blend_multiply_strength"))
    default_specular_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_specular_strength"))
    default_specular_scale: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_specular_scale"))
    default_specular_map: bpy.props.FloatProperty(default=0.5, min=0, max=1, update=lambda s,c: update_property(s,c,"default_specular_map"))
    default_specular_mask: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_specular_mask"))
    default_roughness_power: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_roughness_power"))
    default_roughness_min: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_roughness_min"))
    default_roughness_max: bpy.props.FloatProperty(default=0, min=0, max=1, update=lambda s,c: update_property(s,c,"default_roughness_max"))
    default_alpha_strength: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_alpha_strength"))
    default_opacity: bpy.props.FloatProperty(default=1, min=0, max=1, update=lambda s,c: update_property(s,c,"default_opacity"))
    default_normal_strength: bpy.props.FloatProperty(default=1, min=0, max=2, update=lambda s,c: update_property(s,c,"default_normal_strength"))
    default_bump_strength: bpy.props.FloatProperty(default=1, min=-3, max=3, update=lambda s,c: update_property(s,c,"default_bump_strength"))
    default_displacement_strength: bpy.props.FloatProperty(default=1, min=-3, max=3, update=lambda s,c: update_property(s,c,"default_displacement_strength"))
    default_emissive_color: bpy.props.FloatVectorProperty(subtype="COLOR", size=4,
                                default=(0, 0, 0, 1.0), min = 0.0, max = 1.0,
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



class CC3TextureMapping(bpy.types.PropertyGroup):
    texture_type: bpy.props.StringProperty(default="Diffuse")
    texture_path: bpy.props.StringProperty(default="")
    embedded: bpy.props.BoolProperty(default=False)
    image: bpy.props.PointerProperty(type=bpy.types.Image)
    strength: bpy.props.FloatProperty(default=1.0)
    location: bpy.props.FloatVectorProperty(subtype="TRANSLATION", size=3, default=(0.0, 0.0, 0.0))
    rotation: bpy.props.FloatVectorProperty(subtype="EULER", size=3, default=(0.0, 0.0, 0.0))
    scale: bpy.props.FloatVectorProperty(subtype="XYZ", size=3, default=(1.0, 1.0, 1.0))


class CC3MaterialCache(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(type=bpy.types.Material)
    material_type: bpy.props.EnumProperty(items=vars.MATERIAL_TYPES, default="DEFAULT")
    texture_mappings: bpy.props.CollectionProperty(type=CC3TextureMapping)
    #parameters: bpy.props.PointerProperty(type=CC3MaterialParameters)
    smart_hair: bpy.props.BoolProperty(default=False)
    compat: bpy.props.PointerProperty(type=bpy.types.Material)
    dir: bpy.props.StringProperty(default="")
    temp_weight_map: bpy.props.PointerProperty(type=bpy.types.Image)
    alpha_is_diffuse: bpy.props.BoolProperty(default=False)
    alpha_mode: bpy.props.StringProperty(default="NONE") # NONE, BLEND, HASHED, OPAQUE
    culling_sides: bpy.props.IntProperty(default=0) # 0 - default, 1 - single sided, 2 - double sided
    cloth_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON

    def set_texture_mapping(self, texture_type, texture_path, embedded, image, location, rotation, scale):
        mapping = self.get_texture_mapping(texture_type)
        if mapping is None:
            mapping = self.texture_mappings.add()
        mapping.texture_type = texture_type
        mapping.textuure_path = texture_path
        mapping.embedded = embedded
        mapping.image = image
        mapping.location = location
        mapping.rotation = rotation
        mapping.scale = scale

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


class CC3EyeMaterialCache(CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3EyeParameters)

class CC3EyeOcclusionMaterialCache(CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3EyeOcclusionParameters)

class CC3TearlineMaterialCache(CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3TearlineParameters)

class CC3TeethMaterialCache(CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3TeethParameters)

class CC3TongueMaterialCache(CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3TongueParameters)

class CC3HairMaterialCache(CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3HairParameters)

class CC3HeadMaterialCache(CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3HeadParameters)

class CC3SkinMaterialCache(CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3SkinParameters)

class CC3PBRMaterialCache(CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3PBRParameters)

class CC3SSSMaterialCache(CC3MaterialCache):
    parameters: bpy.props.PointerProperty(type=CC3SSSParameters)


class CC3ObjectCache(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    object_type: bpy.props.EnumProperty(items=vars.OBJECT_TYPES, default="DEFAULT")
    collision_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON
    cloth_physics: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, OFF, ON
    cloth_settings: bpy.props.StringProperty(default="DEFAULT") # DEFAULT, HAIR, COTTON, DENIM, LEATHER, RUBBER, SILK

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

class CC3CharacterCache(bpy.types.PropertyGroup):
    open_mouth: bpy.props.FloatProperty(default=0.0, min=0, max=1, update=open_mouth_update)
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
    object_cache: bpy.props.CollectionProperty(type=CC3ObjectCache)
    import_type: bpy.props.StringProperty(default="")
    # import file name without extension
    import_name: bpy.props.StringProperty(default="")
    import_dir: bpy.props.StringProperty(default="")
    import_embedded: bpy.props.BoolProperty(default=False)
    import_main_tex_dir: bpy.props.StringProperty(default="")
    import_space_in_name: bpy.props.BoolProperty(default=False)
    import_has_key: bpy.props.BoolProperty(default=False)
    import_key_file: bpy.props.StringProperty(default="")
    # which character in the import
    character_name: bpy.props.StringProperty(default="")
    character_index: bpy.props.IntProperty(default=0)
    generation: bpy.props.StringProperty(default="None")
    parent_object: bpy.props.PointerProperty(type=bpy.types.Object)

    def get_all_materials_cache(self):
        all_materials = []
        for cache in self.tongue_material_cache:
            all_materials.append(cache)
        for cache in self.teeth_material_cache:
            all_materials.append(cache)
        for cache in self.head_material_cache:
            all_materials.append(cache)
        for cache in self.skin_material_cache:
            all_materials.append(cache)
        for cache in self.tearline_material_cache:
            all_materials.append(cache)
        for cache in self.eye_occlusion_material_cache:
            all_materials.append(cache)
        for cache in self.eye_material_cache:
            all_materials.append(cache)
        for cache in self.hair_material_cache:
            all_materials.append(cache)
        for cache in self.pbr_material_cache:
            all_materials.append(cache)
        for cache in self.sss_material_cache:
            all_materials.append(cache)
        return all_materials

    def get_object_cache(self, obj):
        """Returns the object cache for this object.

        Fetches or creates an object cache for the object. Always returns an object cache collection.
        """

        if obj is not None:
            for cache in self.object_cache:
                if cache.object == obj:
                    return cache
        return None


    def add_object_cache(self, obj):
        """Returns the object cache for this object.

        Fetches or creates an object cache for the object. Always returns an object cache collection.
        """

        cache = self.get_object_cache(obj)
        if cache is None:
            utils.log_info("Creating Object Cache for: " + obj.name)
            cache = self.object_cache.add()
            cache.object = obj
        return cache


    def get_material_cache(self, mat):
        """Returns the material cache for this material.

        Fetches the material cache for the material. Returns None if the material is not in the cache.
        """

        if mat is not None:
            for cache in self.eye_material_cache:
                if cache.material == mat:
                    return cache
            for cache in self.hair_material_cache:
                if cache.material == mat:
                    return cache
            for cache in self.head_material_cache:
                if cache.material == mat:
                    return cache
            for cache in self.skin_material_cache:
                if cache.material == mat:
                    return cache
            for cache in self.tongue_material_cache:
                if cache.material == mat:
                    return cache
            for cache in self.teeth_material_cache:
                if cache.material == mat:
                    return cache
            for cache in self.tearline_material_cache:
                if cache.material == mat:
                    return cache
            for cache in self.eye_occlusion_material_cache:
                if cache.material == mat:
                    return cache
            for cache in self.pbr_material_cache:
                if cache.material == mat:
                    return cache
            for cache in self.sss_material_cache:
                if cache.material == mat:
                    return cache
        return None


    def add_material_cache(self, mat, create_type = "DEFAULT"):
        """Returns the material cache for this material.

        Fetches the material cache for the material. Returns None if the material is not in the cache.
        """

        cache = self.get_material_cache(mat)
        if cache is None:
            utils.log_info("Creating Material Cache for: " + mat.name + " (" + create_type + ")")
            if create_type == "DEFAULT" or create_type == "SCALP" or create_type == "EYELASH":
                cache = self.pbr_material_cache.add()
            elif create_type == "SSS":
                cache = self.sss_material_cache.add()
            elif create_type == "SKIN_HEAD":
                cache = self.head_material_cache.add()
            elif (create_type == "SKIN_BODY" or create_type == "SKIN_ARM"
               or create_type == "SKIN_LEG" or create_type == "NAILS"):
                cache = self.skin_material_cache.add()
            elif create_type == "TEETH_UPPER" or create_type == "TEETH_LOWER":
                cache = self.teeth_material_cache.add()
            elif create_type == "TONGUE":
                cache = self.tongue_material_cache.add()
            elif create_type == "HAIR":
                cache = self.hair_material_cache.add()
            elif (create_type == "CORNEA_RIGHT" or create_type == "CORNEA_LEFT"
               or create_type == "EYE_RIGHT" or create_type == "EYE_LEFT"):
                cache = self.eye_material_cache.add()
            elif create_type == "OCCLUSION_RIGHT" or create_type == "OCCLUSION_LEFT":
                cache = self.eye_occlusion_material_cache.add()
            elif create_type == "TEARLINE_RIGHT" or create_type == "TEARLINE_LEFT":
                cache = self.tearline_material_cache.add()
            else:
                cache = self.pbr_material_cache.add()
                create_type = "DEFAULT"
            cache.material = mat
            cache.material_type = create_type
        return cache

    def get_character_json(self):
        json_data = jsonutils.read_json(self.import_file)
        return jsonutils.get_character_json(json_data, self.import_name, self.character_name)


class CC3ImportProps(bpy.types.PropertyGroup):

    node_id: bpy.props.IntProperty(default=1000)

    setup_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic","Build basic PBR materials."),
                        ("ADVANCED","Advanced","Build advanced materials with blend maps, subsurface, and micro normals, specular and roughness control and includes layered eye, teeth and tongue materials.")
                    ], default="ADVANCED")

    build_mode: bpy.props.EnumProperty(items=[
                        ("IMPORTED","All Imported","Build materials for all the imported objects."),
                        ("SELECTED","Only Selected","Build materials only for the selected objects.")
                    ], default="IMPORTED")

    blend_mode: bpy.props.EnumProperty(items=[
                        ("BLEND","Alpha Blend","Setup any non opaque materials as basic Alpha Blend"),
                        ("HASHED","Alpha Hashed","Setup non opaque materials as alpha hashed (Resolves Z sorting issues, but may need more samples)")
                    ], default="BLEND")

    update_mode: bpy.props.EnumProperty(items=[
                        ("UPDATE_LINKED","Linked","Update the shader parameters for all materials of the same type in all the objects from the last import"),
                        ("UPDATE_SELECTED","Selected","Update the shader parameters only in the selected object and material")
                    ], default="UPDATE_LINKED")

    import_file: bpy.props.StringProperty(default="", subtype="FILE_PATH")

    import_cache: bpy.props.CollectionProperty(type=CC3CharacterCache)

    dummy_slider: bpy.props.FloatProperty(default=0.5, min=0, max=1)

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
    stage4: bpy.props.BoolProperty(default=True)

    skin_toggle: bpy.props.BoolProperty(default=True)
    eye_toggle: bpy.props.BoolProperty(default=True)
    teeth_toggle: bpy.props.BoolProperty(default=True)
    tongue_toggle: bpy.props.BoolProperty(default=True)
    nails_toggle: bpy.props.BoolProperty(default=True)
    hair_toggle: bpy.props.BoolProperty(default=True)
    default_toggle: bpy.props.BoolProperty(default=True)

    def get_character_cache(self, obj, mat):
        if obj:
            for imp_cache in self.import_cache:
                obj_cache = imp_cache.get_object_cache(obj)
                if obj_cache:
                    return imp_cache
        if mat:
            for imp_cache in self.import_cache:
                mat_cache = imp_cache.get_material_cache(mat)
                if mat_cache:
                    return imp_cache
        return None

    def get_context_character_cache(self, context):
        obj = context.object
        mat = utils.context_material(context)
        return self.get_character_cache(obj, mat)

    def get_object_cache(self, obj):
        if obj:
            for imp_cache in self.import_cache:
                obj_cache = imp_cache.get_object_cache(obj)
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
