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

from . import materials, modifiers, physics, preferences, properties, nodeutils, utils, params, vars

# Panel button functions and opertator
#

def set_physics_settings(param, context = bpy.context):
    props = bpy.context.scene.CC3ImportProps

    if param == "PHYSICS_ADD_CLOTH":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                physics.enable_cloth_physics(obj)
    elif param == "PHYSICS_REMOVE_CLOTH":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                physics.disable_cloth_physics(obj)
    elif param == "PHYSICS_ADD_COLLISION":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                physics.enable_collision_physics(obj)
    elif param == "PHYSICS_REMOVE_COLLISION":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                physics.disable_collision_physics(obj)
    elif param == "PHYSICS_ADD_WEIGHTMAP":
        if context.object is not None and context.object.type == "MESH":
            physics.enable_material_weight_map(context.object, utils.context_material(context))
    elif param == "PHYSICS_REMOVE_WEIGHTMAP":
        if context.object is not None and context.object.type == "MESH":
            physics.disable_material_weight_map(context.object, utils.context_material(context))
    elif param == "PHYSICS_HAIR":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                physics.apply_cloth_settings(obj, "HAIR")
    elif param == "PHYSICS_COTTON":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                physics.apply_cloth_settings(obj, "COTTON")
    elif param == "PHYSICS_DENIM":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                physics.apply_cloth_settings(obj, "DENIM")
    elif param == "PHYSICS_LEATHER":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                physics.apply_cloth_settings(obj, "LEATHER")
    elif param == "PHYSICS_RUBBER":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                physics.apply_cloth_settings(obj, "RUBBER")
    elif param == "PHYSICS_SILK":
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                physics.apply_cloth_settings(obj, "SILK")
    elif param == "PHYSICS_PAINT":
        if context.object is not None and context.object.type == "MESH":
            physics.begin_paint_weight_map(context)
    elif param == "PHYSICS_DONE_PAINTING":
        physics.end_paint_weight_map()
    elif param == "PHYSICS_SAVE":
        physics.save_dirty_weight_maps(bpy.context.selected_objects)
    elif param == "PHYSICS_DELETE":
        physics.delete_selected_weight_map(context.object, utils.context_material(context))
    elif param == "PHYSICS_SEPARATE":
        physics.separate_physics_materials(context)
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


class CC3OperatorPhysics(bpy.types.Operator):
    """Physics Settings Functions"""
    bl_idname = "cc3.setphysics"
    bl_label = "Physics Settings Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):

        set_physics_settings(self.param, context)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "PHYSICS_ADD_CLOTH":
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


def quick_set_fix(param, obj, context, objects_processed):
    props = bpy.context.scene.CC3ImportProps
    ob = context.object

    if obj is not None and obj not in objects_processed:
        if obj.type == "MESH":
            objects_processed.append(obj)

            if props.quick_set_mode == "OBJECT":
                for mat in obj.data.materials:
                    if mat is not None:
                        if param == "OPAQUE" or param == "BLEND" or param == "HASHED" or param == "CLIP":
                            materials.apply_alpha_override(obj, mat, param)
                        elif param == "SINGLE_SIDED":
                            materials.apply_backface_culling(obj, mat, 1)
                        elif param == "DOUBLE_SIDED":
                            materials.apply_backface_culling(obj, mat, 2)

            elif ob is not None and ob.type == "MESH" and ob.active_material_index <= len(ob.data.materials):
                mat = utils.context_material(context)
                if mat is not None:
                    if param == "OPAQUE" or param == "BLEND" or param == "HASHED" or param == "CLIP":
                        materials.apply_alpha_override(obj, mat, param)
                    elif param == "SINGLE_SIDED":
                        materials.apply_backface_culling(obj, mat, 1)
                    elif param == "DOUBLE_SIDED":
                        materials.apply_backface_culling(obj, mat, 2)

        elif obj.type == "ARMATURE":
            for child in obj.children:
                quick_set_fix(param, child, context, objects_processed)


def set_materials_settings(param, context = bpy.context):
    props = bpy.context.scene.CC3ImportProps

    if param == "RESET":
        properties.reset_parameters(context)

    elif param == "RESET_PREFS":
        preferences.reset_preferences()

    else: # blend modes or single/double sided...
        objects_processed = []
        if props.quick_set_mode == "OBJECT":
            for obj in bpy.context.selected_objects:
                quick_set_fix(param, obj, context, objects_processed)
        else:
            quick_set_fix(param, context.object, context, objects_processed)


class CC3OperatorMaterial(bpy.types.Operator):
    """Set Material Functions"""
    bl_idname = "cc3.setmaterials"
    bl_label = "Set Material Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):

        set_materials_settings(self.param, context)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "OPAQUE":
            return "Set blend mode of all selected objects with alpha channels to opaque"
        elif properties.param == "BLEND":
            return "Set blend mode of all selected objects with alpha channels to alpha blend"
        elif properties.param == "HASHED":
            return "Set blend mode of all selected objects with alpha channels to alpha hashed"
        elif properties.param == "CLIP":
            return "Set blend mode of all selected objects with alpha channels to alpha hashed"
        elif properties.param == "FETCH":
            return "Fetch the parameters from the selected objects"
        elif properties.param == "RESET":
            return "Reset parameters to the defaults"
        elif properties.param == "SINGLE_SIDED":
            return "Set material to be single sided, only visible from front facing"
        elif properties.param == "DOUBLE_SIDED":
            return "Set material to be double sided, visible from both sides"
        return ""




# Panel functions and classes
#

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
    bl_label = "Build Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        props: properties.CC3ImportProps = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        chr_cache: properties.CC3CharacterCache = props.get_context_character_cache(context)
        obj = context.object
        mat = None
        obj_cache = None
        mat_cache = None
        if chr_cache and obj and obj.type == "MESH":
            mat = utils.context_material(context)
            obj_cache = chr_cache.get_object_cache(obj)
            mat_cache = chr_cache.get_material_cache(mat)

        mesh_in_selection = False
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                mesh_in_selection = True
                break

        box = layout.box()
        #op = box.operator("cc3.importer", icon="IMPORT", text="Import Character")
        #op.param ="IMPORT"
        # import details
        if chr_cache:
            if fake_drop_down(box.row(), "Import Details", "stage1_details", props.stage1_details):
                box.label(text="Name: " + chr_cache.character_name)
                box.label(text="Type: " + chr_cache.import_type.upper())
                box.label(text="Generation: " + chr_cache.generation)
                if chr_cache.import_has_key:
                    box.label(text="Key File: Yes")
                else:
                    box.label(text="Key File: No")
                box.prop(chr_cache, "import_file", text="")
                for obj_cache in chr_cache.object_cache:
                    if obj_cache.object:
                        box.prop(obj_cache, "object", text="")
            else:
                box.label(text="Name: " + chr_cache.import_name)
        else:
            box.label(text="No Character")

        layout.box().label(text="Build Materials", icon="MOD_BUILD")
        layout.prop(props, "setup_mode", expand=True)
        layout.prop(prefs, "render_target", expand=True)
        #layout.prop(props, "blend_mode", expand=True)
        layout.prop(props, "build_mode", expand=True)

        # Prefs:
        box = layout.box()
        box.label(text="Eye Refraction")
        box.row().prop(prefs, "refractive_eyes", expand=True)

        # Build Button
        if chr_cache:
            box = layout.box()
            box.scale_y = 2
            if props.setup_mode == "ADVANCED":
                op = box.operator("cc3.importer", icon="SHADING_TEXTURE", text="Rebuild Advanced Materials")
            else:
                op = box.operator("cc3.importer", icon="NODE_MATERIAL", text="Rebuild Basic Materials")
            op.param ="BUILD"

        # Material Setup
        layout.box().label(text="Material Setup", icon="MATERIAL")
        column = layout.column()
        if not mesh_in_selection:
            column.enabled = False
        if obj is not None:
            column.template_list("MATERIAL_UL_weightedmatslots", "", obj, "material_slots", obj, "active_material_index", rows=1)
        split = column.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()

        if chr_cache and obj_cache:
            if obj is not None:
                obj_cache = chr_cache.get_object_cache(obj)
                if obj_cache is not None:
                    col_1.label(text="Object Type")
                    col_2.prop(obj_cache, "object_type", text = "")
            if mat is not None:
                mat_cache = chr_cache.get_material_cache(mat)
                if mat_cache is not None:
                    col_1.label(text="Material Type")
                    col_2.prop(mat_cache, "material_type", text = "")


        col_1.label(text="Set By:")
        col_1.prop(props, "quick_set_mode", expand=True)
        col_1.label(text="")
        op = col_2.operator("cc3.setmaterials", icon="SHADING_SOLID", text="Opaque")
        op.param = "OPAQUE"
        op = col_2.operator("cc3.setmaterials", icon="SHADING_WIRE", text="Blend")
        op.param = "BLEND"
        op = col_2.operator("cc3.setmaterials", icon="SHADING_RENDERED", text="Hashed")
        op.param = "HASHED"
        op = col_2.operator("cc3.setmaterials", icon="SHADING_TEXTURE", text="Clipped")
        op.param = "CLIP"
        split = column.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.separator()
        col_2.separator()
        op = col_1.operator("cc3.setmaterials", icon="NORMALS_FACE", text="Single Sided")
        op.param = "SINGLE_SIDED"
        op = col_2.operator("cc3.setmaterials", icon="XRAY", text="Double Sided")
        op.param = "DOUBLE_SIDED"


class CC3ToolsParametersPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Parameters_Panel"
    bl_label = "Material Parameters"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props: properties.CC3ImportProps = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        chr_cache = props.get_context_character_cache(context)

        obj = None
        mat = None
        obj_cache = None
        mat_cache = None
        shader = "NONE"
        parameters = None

        if chr_cache:
            obj = context.object
            mat = utils.context_material(context)
            obj_cache = chr_cache.get_object_cache(obj)
            mat_cache = chr_cache.get_material_cache(mat)
            if mat_cache:
                parameters = mat_cache.parameters

        is_import_object = obj_cache is not None
        is_import_material = mat_cache is not None

        if not is_import_object and not is_import_material:
            layout.enabled = False

        # Parameters

        if chr_cache and mat_cache and fake_drop_down(layout.box().row(),
                "Adjust Parameters",
                "stage4",
                props.stage4):

            # material selector
            #column = layout.column()
            #obj_cache = mat_cache = None
            #mat_type = "NONE"
            #if obj is not None:
            #    column.template_list("MATERIAL_UL_weightedmatslots", "", obj, "material_slots", obj, "active_material_index", rows=1)

            column = layout.column()
            if chr_cache.import_name == "":
                column.enabled = False

            row = column.row()
            row.prop(props, "update_mode", expand=True)

            linked = props.update_mode == "UPDATE_LINKED"

            if chr_cache.setup_mode == "ADVANCED":

                shader = params.get_shader_lookup(mat_cache)
                bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader)
                matrix = params.get_shader_def(shader)

                if matrix and "ui" in matrix.keys():

                    ui_matrix = matrix["ui"]

                    column.separator()

                    column.box().label(text = matrix["label"] + " Parameters:", icon="MOD_HUE_SATURATION")

                    for ui_row in ui_matrix:

                        split = False
                        col_1 = None
                        col_2 = None

                        if ui_row[0] == "HEADER":
                            column.box().label(text= ui_row[1], icon=ui_row[2])

                        elif ui_row[0] == "PROP":

                            show_prop = True
                            label = ui_row[1]
                            prop = ui_row[2]
                            is_slider = ui_row[3]
                            conditions = ui_row[4:]

                            if shader:
                                for condition in conditions:
                                    if condition == "HAS_VERTEX_COLORS":
                                        cond_res = len(obj.data.vertex_colors) > 0
                                    elif condition[0] == '#':
                                        cond_res = chr_cache.render_target == condition[1:]
                                    elif condition[0] == '!':
                                        condition = condition[1:]
                                        cond_res = not nodeutils.has_connected_input(shader_node, condition)
                                    else:
                                        cond_res = nodeutils.has_connected_input(shader_node, condition)

                                    if not cond_res:
                                        show_prop = False

                            if show_prop:
                                if not split:
                                    row = column.row()
                                    split = row.split(factor=0.5)
                                    col_1 = row.column()
                                    col_2 = row.column()
                                    split = True
                                col_1.label(text=label)
                                col_2.prop(parameters, prop, text="", slider=is_slider)

                        elif ui_row[0] == "OP":

                            show_op = True
                            label = ui_row[1]
                            op_id = ui_row[2]
                            icon = ui_row[3]
                            param = ui_row[4]
                            conditions = ui_row[5:]

                            if shader:
                                for condition in conditions:
                                    if condition[0] == '!':
                                        condition = condition[1:]
                                        cond_res = not nodeutils.has_connected_input(shader_node, condition)
                                    else:
                                        cond_res = nodeutils.has_connected_input(shader_node, condition)

                                    if not cond_res:
                                        show_op = False

                            if show_op:
                                row = column.row()
                                row.operator(op_id, icon=icon, text=label).param = param
                                split = False

                        elif ui_row[0] == "SPACER":
                            if not split:
                                row = column.row()
                                split = row.split(factor=0.5)
                                col_1 = row.column()
                                col_2 = row.column()
                                split = True
                            col_1.separator()
                            col_2.separator()

            else:

                basic_params = chr_cache.basic_parameters
                bsdf_node = nodeutils.get_shader_nodes(mat, shader)[0]

                column.separator()
                column.box().label(text = "Basic Parameters:", icon="MOD_HUE_SATURATION")

                actor_core = False
                if chr_cache.generation == "ActorCore":
                    actor_core = True

                if not actor_core:
                    column.box().label(text= "Skin", icon="OUTLINER_OB_ARMATURE")
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Skin AO")
                    col_2.prop(basic_params, "skin_ao", text="", slider=True)
                    col_1.label(text="Skin Specular")
                    col_2.prop(basic_params, "skin_specular", text="", slider=True)
                    col_1.label(text="Skin Roughness")
                    col_2.prop(basic_params, "skin_roughness", text="", slider=True)

                    column.box().label(text= "Eyes", icon="MATSPHERE")
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Eye Brightness")
                    col_2.prop(basic_params, "eye_brightness", text="", slider=True)
                    col_1.label(text="Eye Specular")
                    col_2.prop(basic_params, "eye_specular", text="", slider=True)
                    col_1.label(text="Eye Roughness")
                    col_2.prop(basic_params, "eye_roughness", text="", slider=True)
                    col_1.label(text="Eye Normal")
                    col_2.prop(basic_params, "eye_normal", text="", slider=True)

                    column.box().label(text= "Eye Occlusion", icon="PROP_CON")
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Eye Occlusion")
                    col_2.prop(basic_params, "eye_occlusion", text="", slider=True)
                    col_1.label(text="Eye Occlusion Hardness")
                    col_2.prop(basic_params, "eye_occlusion_power", text="", slider=True)

                    column.box().label(text= "Tearline", icon="MATFLUID")
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Tearline Alpha")
                    col_2.prop(basic_params, "tearline_alpha", text="", slider=True)
                    col_1.label(text="Tearline Roughness")
                    col_2.prop(basic_params, "tearline_roughness", text="", slider=True)

                    column.box().label(text= "Teeth", icon="RIGID_BODY")
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Teeth Specular")
                    col_2.prop(basic_params, "teeth_specular", text="", slider=True)
                    col_1.label(text="Teeth Roughness")
                    col_2.prop(basic_params, "teeth_roughness", text="", slider=True)

                    column.box().label(text= "Tongue", icon="INVERSESQUARECURVE")
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Tongue Specular")
                    col_2.prop(basic_params, "tongue_specular", text="", slider=True)
                    col_1.label(text="Tongue Roughness")
                    col_2.prop(basic_params, "tongue_roughness", text="", slider=True)

                    column.box().label(text= "Hair", icon="OUTLINER_OB_HAIR")
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Hair AO")
                    col_2.prop(basic_params, "hair_ao", text="", slider=True)
                    col_1.label(text="Hair Specular")
                    col_2.prop(basic_params, "hair_specular", text="", slider=True)
                    col_1.label(text="Scalp Specular")
                    col_2.prop(basic_params, "scalp_specular", text="", slider=True)
                    col_1.label(text="Hair Bump Height (mm)")
                    col_2.prop(basic_params, "hair_bump", text="", slider=True)

                if actor_core:
                    column.box().label(text= "Actor Core", icon="USER")
                else:
                    column.box().label(text= "Default", icon="CUBE")
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Default AO")
                col_2.prop(basic_params, "default_ao", text="", slider=True)
                col_1.label(text="Default Specular")
                col_2.prop(basic_params, "default_specular", text="", slider=True)
                if not actor_core:
                    col_1.label(text="Default Bump Height (mm)")
                    col_2.prop(basic_params, "default_bump", text="", slider=True)

        # Utilities

        layout.box().label(text="Utilities", icon="MODIFIER_DATA")
        column = layout.column()
        if not chr_cache:
            column.enabled = False
        if chr_cache and chr_cache.import_type == "fbx":
            split = column.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Open Mouth")
            if chr_cache:
                col_2.prop(chr_cache, "open_mouth", text="", slider=True)
            else:
                col_2.prop(props, "dummy_slider", text="", slider=True)

        column = layout.column()
        op = column.operator("cc3.setmaterials", icon="DECORATE_OVERRIDE", text="Reset Parameters")
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
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
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

        chr_cache = props.get_context_character_cache(context)
        if chr_cache and bpy.context.scene.render.engine == 'CYCLES':
            box = layout.box()
            box.label(text="Cycles", icon="SHADING_RENDERED")
            col = layout.column()
            op = col.operator("cc3.scene", icon="PLAY", text="Cycles Setup")
            op.param = "CYCLES_SETUP"


class CC3ToolsPhysicsPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Physics_Panel"
    bl_label = "Physics Settings"
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
                clm = modifiers.get_cloth_physics_mod(obj)
                com = modifiers.get_collision_physics_mod(obj)
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
        mat = utils.context_material(context)
        edit_mod, mix_mod = modifiers.get_material_weight_map_mods(obj, mat)

        box = layout.box()
        box.label(text="Create / Remove", icon="PHYSICS")

        col = layout.column()
        if not missing_cloth:
            op = col.operator("cc3.setphysics", icon="REMOVE", text="Remove Cloth Physics")
            op.param = "PHYSICS_REMOVE_CLOTH"
        else:
            op = col.operator("cc3.setphysics", icon="ADD", text="Add Cloth Physics")
            op.param = "PHYSICS_ADD_CLOTH"
        if not missing_coll:
            op = col.operator("cc3.setphysics", icon="REMOVE", text="Remove Collision Physics")
            op.param = "PHYSICS_REMOVE_COLLISION"
        else:
            op = col.operator("cc3.setphysics", icon="ADD", text="Add Collision Physics")
            op.param = "PHYSICS_ADD_COLLISION"
        if meshes_selected == 0:
            col.enabled = False

        box = layout.box()
        box.label(text="Mesh Correction", icon="MESH_DATA")
        col = layout.column()
        op = col.operator("cc3.setphysics", icon="MOD_EDGESPLIT", text="Fix Degenerate Mesh")
        op.param = "PHYSICS_FIX_DEGENERATE"
        op = col.operator("cc3.setphysics", icon="FACE_MAPS", text="Separate Physics Materials")
        op.param = "PHYSICS_SEPARATE"

        # Cloth Physics Presets
        box = layout.box()
        box.label(text="Presets", icon="PRESET")
        col = layout.column()
        if cloth_mod is None:
            col.enabled = False
        op = col.operator("cc3.setphysics", icon="USER", text="Hair")
        op.param = "PHYSICS_HAIR"
        op = col.operator("cc3.setphysics", icon="MATCLOTH", text="Cotton")
        op.param = "PHYSICS_COTTON"
        op = col.operator("cc3.setphysics", icon="MATCLOTH", text="Denim")
        op.param = "PHYSICS_DENIM"
        op = col.operator("cc3.setphysics", icon="MATCLOTH", text="Leather")
        op.param = "PHYSICS_LEATHER"
        op = col.operator("cc3.setphysics", icon="MATCLOTH", text="Rubber")
        op.param = "PHYSICS_RUBBER"
        op = col.operator("cc3.setphysics", icon="MATCLOTH", text="Silk")
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
            op = row.operator("cc3.setphysics", icon="CHECKMARK", text="Done Weight Painting!")
            op.param = "PHYSICS_DONE_PAINTING"
        else:
            if edit_mod is None:
                row = col.row()
                op = row.operator("cc3.setphysics", icon="ADD", text="Add Weight Map")
                op.param = "PHYSICS_ADD_WEIGHTMAP"
            else:
                row = col.row()
                op = row.operator("cc3.setphysics", icon="REMOVE", text="Remove Weight Map")
                op.param = "PHYSICS_REMOVE_WEIGHTMAP"
            col = layout.column()
            if edit_mod is None:
                col.enabled = False
            op = col.operator("cc3.setphysics", icon="BRUSH_DATA", text="Paint Weight Map")
            op.param = "PHYSICS_PAINT"
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            op = col_1.operator("cc3.setphysics", icon="FILE_TICK", text="Save")
            op.param = "PHYSICS_SAVE"
            op = col_2.operator("cc3.setphysics", icon="ERROR", text="Delete")
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
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        chr_cache: properties.CC3CharacterCache = props.get_context_character_cache(context)
        if chr_cache:
            character_name = chr_cache.character_name
        else:
            character_name = "No Character"

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        box = layout.box()
        box.label(text="Settings", icon="TOOL_SETTINGS")
        #layout.prop(chr_cache, "setup_mode", expand=True)
        if prefs.lighting == "ENABLED" or prefs.physics == "ENABLED":
            if prefs.lighting == "ENABLED":
                layout.prop(props, "lighting_mode", expand=True)
            if prefs.physics == "ENABLED":
                layout.prop(props, "physics_mode", expand=True)

        box = layout.box()
        box.label(text="Render / Animation", icon="RENDER_RESULT")
        row = layout.row()
        row.scale_y = 2
        op = row.operator("cc3.importer", icon="IMPORT", text="Import Character")
        op.param = "IMPORT_QUALITY"

        box = layout.box()
        box.label(text="Character Editing", icon="OUTLINER_OB_ARMATURE")
        row = layout.row()
        op = row.operator("cc3.importer", icon="IMPORT", text="Import For Editing")
        op.param = "IMPORT_MORPH"
        row = layout.row()
        op = row.operator("cc3.exporter", icon="EXPORT", text="Export To CC3")
        op.param = "EXPORT_MORPH"
        # export prefs
        box = layout.box()
        if fake_drop_down(box.row(),
                "Export Prefs",
                "export_options",
                props.export_options):
            box.row().prop(prefs, "export_json_changes", expand=True)
            box.row().prop(prefs, "export_texture_changes", expand=True)
        row = layout.row()
        op = row.operator("cc3.exporter", icon="MOD_CLOTH", text="Export Accessory")
        op.param = "EXPORT_ACCESSORY"
        if not chr_cache or not chr_cache.import_has_key:
            row.enabled = False

        layout.separator()
        box = layout.box()
        box.label(text="Clean Up", icon="TRASH")

        box = layout.row()
        box.label(text = "Character: " + character_name)
        row = layout.row()
        op = row.operator("cc3.importer", icon="REMOVE", text="Remove Character")
        op.param ="DELETE_CHARACTER"
        if not chr_cache:
            row.enabled = False
