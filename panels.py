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

from cmath import exp
import bpy
import textwrap

from . import addon_updater_ops
from . import rigging, rigify_mapping_data, characters, sculpting, physics, modifiers, channel_mixer, nodeutils, utils, params, vars

PIPELINE_TAB_NAME = "CC/iC Pipeline"
CREATE_TAB_NAME = "CC/iC Create"

# Panel button functions and operator
#

def context_character(context, exact = False):
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_context_character_cache(context, exact = exact)

    obj = None
    mat = None
    obj_cache = None
    mat_cache = None

    if chr_cache:
        obj = context.object
        mat = utils.context_material(context)
        obj_cache = chr_cache.get_object_cache(obj)
        mat_cache = chr_cache.get_material_cache(mat)

    return chr_cache, obj, mat, obj_cache, mat_cache


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


def get_layout_width(region_type = "UI"):
    ui_shelf = None
    area = bpy.context.area
    width = 15
    for region in area.regions:
        if region.type == region_type:
            ui_shelf = region
            width = int(ui_shelf.width / 8)
    return width


def wrapped_text_box(layout, info_text, width, alert = False):
    wrapper = textwrap.TextWrapper(width=width)
    info_list = wrapper.wrap(info_text)

    box = layout.box()
    box.alert = alert
    for text in info_list:
        box.label(text=text)


def character_info_box(chr_cache, chr_rig, layout, show_name = True, show_type = True, show_type_selector = True):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    is_character = False
    is_non_standard = True
    is_morph = False
    if chr_cache:
        character_name = chr_cache.character_name
        is_non_standard = chr_cache.is_non_standard()
        if chr_cache.is_standard():
            type_text = f"Standard ({chr_cache.generation})"
        else:
            if "NonStandard" in chr_cache.generation:
                generation = chr_cache.generation[11:]
                if not generation:
                    generation = "Any"
                type_text = f"Non-Standard ({generation})"
            else:
                type_text = f"Non-Standard ({chr_cache.generation})"
        is_character = True
        if chr_cache.is_morph():
            is_morph = True
            is_non_standard = False
            type_text = "Obj/Morph"
    elif chr_rig:
        character_name = chr_rig.name
        type_text = "Generic"
        is_non_standard = True
        is_character = True

    if is_character:
        box = layout.box()
        if show_name:
            box.row().label(text=f"Character: {character_name}")
        if show_type:
            box.row().label(text=f"Type: {type_text}")
        if show_type_selector:
            if is_non_standard:
                row = box.row()
                if chr_cache:
                    row.prop(chr_cache, "non_standard_type", expand=True)
                elif chr_rig:
                    row.prop(prefs, "export_non_standard_mode", expand=True)

    else:
        box = layout.box()
        box.row().label(text=f"No Character")


def pipeline_export_group(chr_cache, chr_rig, layout):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    character_info_box(chr_cache, chr_rig, layout)

    if chr_cache and chr_cache.rigified:
        row = layout.row()
        row.alert = True
        row.label(text="Export from Rigging & Animation", icon="ERROR")

    # export to CC3
    character_export_button(chr_cache, chr_rig, layout)

    layout.separator()

    # export to Unity
    character_export_unity_button(chr_cache, layout)


def rigify_export_group(chr_cache, layout):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    row = layout.row()
    row.label(text="Include T-Pose")
    row.prop(props, "bake_unity_t_pose", text="")

    row = layout.row()
    row.scale_y = 2
    if props.export_rigify_mode == "MESH":
        row.operator("cc3.exporter", icon="ARMATURE_DATA", text="Export Mesh").param = "EXPORT_RIGIFY"
    elif props.export_rigify_mode == "MOTION":
        row.operator("cc3.exporter", icon="ARMATURE_DATA", text="Export Motion").param = "EXPORT_RIGIFY"
    else:
        row.operator("cc3.exporter", icon="ARMATURE_DATA", text="Export Mesh & Motion").param = "EXPORT_RIGIFY"
    layout.row().prop(props, "export_rigify_mode", expand=True)


def character_export_button(chr_cache, chr_rig, layout):
    # export to CC3
    text = "Export to CC3/4"
    icon = "MOD_ARMATURE"

    standard_export = chr_cache and chr_cache.is_standard()
    non_standard_export = (chr_cache and chr_cache.is_non_standard()) or (chr_rig and not standard_export)

    if chr_cache:
        row = layout.row()
        row.scale_y = 2
        if chr_cache and utils.is_file_ext(chr_cache.import_type, "OBJ"):
            text = "Export Morph Target"
            icon = "ARROW_LEFTRIGHT"
        op = row.operator("cc3.exporter", icon=icon, text=text).param = "EXPORT_CC3"
        if not chr_cache.can_export():
            row.enabled = False
            if not chr_cache.import_has_key:
                if utils.is_file_ext(chr_cache.import_type, "FBX"):
                    layout.row().label(text="No Fbx-Key file!", icon="ERROR")
                elif utils.is_file_ext(chr_cache.import_type, "OBJ"):
                    layout.row().label(text="No Obj-Key file!", icon="ERROR")

    elif chr_rig:
        row = layout.row()
        row.scale_y = 2
        text = "Export Non-Standard"
        icon = "MONKEY"
        op = row.operator("cc3.exporter", icon=icon, text=text).param = "EXPORT_NON_STANDARD"

    else:
        row = layout.row()
        row.scale_y = 2
        row.operator("cc3.exporter", icon=icon, text=text).param = "EXPORT_CC3"
        row.enabled = False
        row = layout.row()
        row.alert = True
        row.label(text="No current character!", icon="ERROR")


def character_export_unity_button(chr_cache, layout):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    column = layout.column()

    # export button
    row = column.row()
    row.scale_y = 2
    if props.is_unity_project():
        row.operator("cc3.exporter", icon="CUBE", text="Update Unity Project").param = "UPDATE_UNITY"
    else:
        row.operator("cc3.exporter", icon="CUBE", text="Export To Unity").param = "EXPORT_UNITY"
        # export mode
        column.row().prop(prefs, "export_unity_mode", expand=True)

    # disable if no character, or not an fbx import
    if not chr_cache or not utils.is_file_ext(chr_cache.import_type, "FBX") or chr_cache.rigified:
        column.enabled = False


class ARMATURE_UL_List(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name if item else "", translate=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        for i, item in enumerate(items):
            item_name = utils.strip_name(item.name)
            allowed = False
            if item.type == "ARMATURE": # only list armatures
                if "_Rigify" not in item_name: # don't list rigified armatures
                    if "_Retarget" not in item_name: # don't list retarget armatures
                        if len(item.data.bones) > 0:
                            for allowed_bone in rigify_mapping_data.ALLOWED_RIG_BONES: # only list armatures of the allowed sources
                                if allowed_bone in item.data.bones:
                                    allowed = True
            if not allowed:
                    filtered[i] &= ~self.bitflag_filter_item
            else:
                if self.filter_name and self.filter_name != "*":
                    if self.filter_name not in item.name:
                        filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered


class ACTION_UL_List(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name if item else "", translate=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

    def filter_items(self, context, data, propname):
        props = bpy.context.scene.CC3ImportProps
        filtered = []
        ordered = []
        arm_name = None
        arm_object = utils.collection_at_index(props.armature_list_index, bpy.data.objects)
        if arm_object and arm_object.type == "ARMATURE":
            arm_name = arm_object.name
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        item : bpy.types.Action
        for i, item in enumerate(items):
            if props.armature_action_filter and arm_object:
                if arm_name and item.name.startswith(arm_name + "|A|"):
                    if self.filter_name and self.filter_name != "*":
                        if self.filter_name not in item.name:
                            filtered[i] &= ~self.bitflag_filter_item
                elif arm_name and item.name.startswith(arm_name + "|") and not item.name.startswith(arm_name + "|K"):
                    if self.filter_name and self.filter_name != "*":
                        if self.filter_name not in item.name:
                            filtered[i] &= ~self.bitflag_filter_item
                else:
                    filtered[i] &= ~self.bitflag_filter_item
            else:
                if len(item.fcurves) == 0: # no fcurves, no animation...
                    filtered[i] &= ~self.bitflag_filter_item
                elif item.fcurves[0].data_path.startswith("key_blocks"): # only shapekey actions have key blocks...
                    filtered[i] &= ~self.bitflag_filter_item
                else:
                    if self.filter_name and self.filter_name != "*":
                        if self.filter_name not in item.name:
                            filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered


class UNITY_ACTION_UL_List(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name if item else "", translate=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        item : bpy.types.Action
        for i, item in enumerate(items):
            if "_Unity" in item.name and "|A|" in item.name:
                if len(item.fcurves) == 0: # no fcurves, no animation...
                    filtered[i] &= ~self.bitflag_filter_item
                elif item.fcurves[0].data_path.startswith("key_blocks"): # only shapekey actions have key blocks...
                    filtered[i] &= ~self.bitflag_filter_item
                    if self.filter_name and self.filter_name != "*":
                        if self.filter_name not in item.name:
                            filtered[i] &= ~self.bitflag_filter_item
            else:
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered


class CC3CharacterSettingsPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Character_Settings_Panel"
    bl_label = "Character Build Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PIPELINE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        chr_cache, obj, mat, obj_cache, mat_cache = context_character(context)

        mesh_in_selection = False
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                mesh_in_selection = True

        box = layout.box()
        #op = box.operator("cc3.importer", icon="IMPORT", text="Import Character")
        #op.param ="IMPORT"
        # import details
        if chr_cache:
            if fake_drop_down(box.row(), "Import Details", "stage1_details", props.stage1_details):
                box.label(text="Name: " + chr_cache.character_name)
                box.label(text="Type: " + chr_cache.import_type.upper())
                split = box.split(factor=0.4)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Generation")
                col_2.prop(chr_cache, "generation", text="")
                col_1.label(text="Key File")
                col_2.prop(chr_cache, "import_has_key", text="")
                box.prop(chr_cache, "import_file", text="")
                for obj_cache in chr_cache.object_cache:
                    if obj_cache.object:
                        box.prop(obj_cache, "object", text="")
                box.label(text="Collision Mesh")
                box.prop(chr_cache, "collision_body", text="")

            else:
                box.label(text="Name: " + chr_cache.character_name)
        else:
            box.label(text="No Character")

        # Build Settings

        layout.box().label(text="Build Settings", icon="TOOL_SETTINGS")
        if prefs.physics == "ENABLED":
            layout.prop(props, "physics_mode", expand=True)
        layout.prop(prefs, "render_target", expand=True)
        layout.prop(prefs, "refractive_eyes", expand=True)
        split = layout.split(factor=0.9)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text="De-duplicate Materials")
        col_2.prop(prefs, "import_deduplicate", text="")
        col_1.label(text="Auto Convert Generic")
        col_2.prop(prefs, "import_auto_convert", text="")

        # Cycles Prefs

        if prefs.render_target == "CYCLES":
            box = layout.box()
            if fake_drop_down(box.row(),
                    "Cycles Prefs",
                    "cycles_options",
                    props.cycles_options):
                column = box.column()
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text = "Skin SSS")
                col_2.prop(prefs, "cycles_sss_skin_v118", text = "")
                col_1.label(text = "Hair SSS")
                col_2.prop(prefs, "cycles_sss_hair_v118", text = "")
                col_1.label(text = "Teeth SSS")
                col_2.prop(prefs, "cycles_sss_teeth", text = "")
                col_1.label(text = "Tongue SSS")
                col_2.prop(prefs, "cycles_sss_tongue", text = "")
                col_1.label(text = "Eyes SSS")
                col_2.prop(prefs, "cycles_sss_eyes", text = "")
                col_1.label(text = "Default SSS")
                col_2.prop(prefs, "cycles_sss_default", text = "")

        # Build Button
        if chr_cache:
            box = layout.box()
            box.row().label(text="Rebuild Materials", icon="MOD_BUILD")
            row = box.row()
            row.scale_y = 2
            if chr_cache.setup_mode == "ADVANCED":
                op = row.operator("cc3.importer", icon="SHADING_TEXTURE", text="Rebuild Advanced Materials")
            else:
                op = row.operator("cc3.importer", icon="NODE_MATERIAL", text="Rebuild Basic Materials")
            op.param ="BUILD"
            row = box.row()
            row.prop(chr_cache, "setup_mode", expand=True)
            row = box.row()
            row.prop(props, "build_mode", expand=True)
            box.row().operator("cc3.importer", icon="MOD_BUILD", text="Rebuild Node Groups").param ="REBUILD_NODE_GROUPS"

        # Material Setup
        layout.box().label(text="Object & Material Setup", icon="MATERIAL")
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


class CC3ObjectManagementPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Object_Management_Panel"
    bl_label = "Object Management"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        chr_cache, obj, mat, obj_cache, mat_cache = context_character(context, exact = True)
        chr_rig = None
        if chr_cache:
            chr_rig = chr_cache.get_armature()
        elif context.selected_objects:
            chr_rig = utils.get_generic_character_rig(context.selected_objects)

        mesh_in_selection = False
        all_mesh_in_selection = True
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                mesh_in_selection = True
            else:
                all_mesh_in_selection = False

        missing_object = False
        removable_object = False
        missing_material = False
        weight_transferable = False
        show_clean_up = chr_cache is not None
        if bpy.context.selected_objects and bpy.context.active_object:
            if chr_cache and obj_cache is None and obj and obj.type == "MESH":
                missing_object = True
            if obj != chr_rig and obj.parent != chr_rig:
                missing_object = True
            if chr_cache and obj_cache and obj.parent == chr_rig:
                if (obj_cache.object_type != "BODY" and obj_cache.object_type != "EYE" and
                    obj_cache.object_type != "TEETH" and obj_cache.object_type != "TONGUE"):
                    removable_object = True
            if chr_cache and obj and obj.type == "MESH" and not chr_cache.has_all_materials(obj.data.materials):
                missing_material = True
            if all_mesh_in_selection: # and arm.data.pose_position == "REST":
                weight_transferable = True
                if obj_cache and obj_cache.object_type == "BODY":
                    weight_transferable = False

        column = layout.column()

        # Converting

        column.box().label(text="Converting", icon="DRIVER")

        character_info_box(chr_cache, chr_rig, column)

        row = column.row()
        row.operator("cc3.character", icon="MESH_MONKEY", text="Convert to Non-standard").param = "CONVERT_TO_NON_STANDARD"
        if not chr_cache or chr_cache.is_non_standard():
            row.enabled = False

        row = column.row()
        if chr_rig:
            row.operator("cc3.character", icon="COMMUNITY", text="Convert from Generic").param = "CONVERT_FROM_GENERIC"
        else:
            row.operator("cc3.character", icon="COMMUNITY", text="Convert from Objects").param = "CONVERT_FROM_GENERIC"
        if chr_cache or not bpy.context.selected_objects:
            row.enabled = False

        column.separator()

        # Accessory Management

        column.box().label(text="Accessories", icon="GROUP_BONE")

        accessory_root = characters.get_accessory_root(chr_cache, obj)
        if accessory_root:

            #column.box().label(text = f"Accessory: {accessory_root.name}")
            box = column.box()
            split = box.split(factor=0.375)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Accessory:")
            col_2.prop(accessory_root, "name", text="")
            col_1.label(text="Parent:")
            col_2.prop(accessory_root, "parent", text="")
        else:
            split = None
            if chr_cache and chr_rig:
                split = column.split(factor=0.375)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Parent:")
                col_2.prop_search(chr_cache, "accessory_parent_bone", chr_rig.data, "bones", text="")
            row = column.row()
            row.operator("cc3.character", icon="CONSTRAINT_BONE", text="Convert to Accessory").param = "CONVERT_ACCESSORY"
            if not chr_cache or not obj or obj.type != "MESH" or (obj_cache and obj_cache.object_type == "BODY"):
                row.enabled = False
                if split:
                    split.enabled = False

        column.separator()

        # Checking

        column.box().label(text="Checking", icon="SHADERFX")

        row = column.row()
        row.operator("cc3.exporter", icon="CHECKMARK", text="Check Export").param = "CHECK_EXPORT"

        row = column.row()
        row.operator("cc3.character", icon="REMOVE", text="Clean Up Data").param = "CLEAN_UP_DATA"
        if not show_clean_up:
            row.enabled = False

        column.separator()

        # Export Settings

        column.box().label(text="Export Settings", icon="EXPORT")

        split = column.split(factor=0.5)
        split.column().label(text = "Texture Size")
        split.column().prop(prefs, "export_texture_size", text = "")

        column.separator()

        # Objects & Materials

        column.box().label(text="Objects & Materials", icon="OBJECT_HIDDEN")

        row = column.row()
        row.operator("cc3.character", icon="ADD", text="Add To Character").param = "ADD_PBR"
        if not missing_object:
            row.enabled = False

        row = column.row()
        row.operator("cc3.character", icon="REMOVE", text="Remove From Character").param = "REMOVE_OBJECT"
        if not removable_object:
            row.enabled = False

        row = column.row()
        row.operator("cc3.character", icon="ADD", text="Add New Materials").param = "ADD_MATERIALS"
        if not missing_material:
            row.enabled = False

        column.separator()

        # Armature & Weights

        column.box().label(text = "Armature & Weights", icon = "ARMATURE_DATA")

        if chr_rig:
            column.row().prop(chr_rig.data, "pose_position", expand=True)

        row = column.row()
        row.operator("cc3.character", icon="MOD_DATA_TRANSFER", text="Transfer Weights").param = "TRANSFER_WEIGHTS"
        if not weight_transferable:
            row.enabled = False

        row = column.row()
        row.operator("cc3.character", icon="ORIENTATION_NORMAL", text="Normalize Weights").param = "NORMALIZE_WEIGHTS"
        if not weight_transferable:
            row.enabled = False


class CC3HairPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Hair_Panel"
    bl_label = "Hair (Experimental)"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        chr_cache, obj, mat, obj_cache, mat_cache = context_character(context, exact = True)

        # Blender Curve Hair

        if fake_drop_down(layout.box().row(),
                "Blender Curve Hair",
                "section_hair_blender_curve",
                props.section_hair_blender_curve):

            column = layout.column()
            column.box().label(text="Exporting", icon="EXPORT")
            column.row().operator("cc3.export_hair", icon=utils.check_icon("HAIR"), text="Export Hair")
            column.row().prop(prefs, "hair_export_group_by", expand=True)

            if not bpy.context.selected_objects:
                column.enabled = False

        # Hair Cards & Spring Bone Rig

        if fake_drop_down(layout.box().row(),
                "Hair Rigging",
                "section_hair_rigging",
                props.section_hair_rigging):

            column = layout.column()
            column.row().prop(prefs, "hair_curve_dir", text="")
            column.row().prop(prefs, "hair_curve_dir_threshold", text="Alignment Threshold", slider=True)

            column.separator()

            column = layout.column()
            column.box().label(text="Hair Spring Rig", icon="FORCE_MAGNETIC")
            column.row().prop(prefs, "hair_rig_bone_length", text="Bone Length (cm)", slider=True)
            column.row().prop(prefs, "hair_rig_bind_skip_count", text="Skip First Bones", slider=True)
            column.separator()
            row = column.row()
            row.scale_y = 1.5
            row.operator("cc3.hair", icon=utils.check_icon("GROUP_BONE"), text="Add Hair Bones").param = "ADD_BONES"
            row = column.row()
            column.separator()
            row.scale_y = 1.5
            row.operator("cc3.hair", icon=utils.check_icon("X"), text="Clear Hair Bones").param = "REMOVE_HAIR_BONES"
            column.separator()
            column.row().prop(prefs, "hair_rig_bind_card_mode", expand=True)
            column.row().prop(prefs, "hair_rig_bind_bone_mode", expand=True)
            column.row().prop(prefs, "hair_rig_bind_bone_radius", text="Bind Radius (cm)", slider=True)
            column.row().prop(prefs, "hair_rig_bind_bone_count", text="Bind Bones", slider=True)
            column.row().prop(prefs, "hair_rig_bind_bone_weight", text="Weight Scale", slider=True)
            column.row().prop(prefs, "hair_rig_bind_bone_variance", text="Weight Variance", slider=True)
            column.row().prop(prefs, "hair_rig_bind_existing_scale", text="Scale Body Weights", slider=True)
            column.row().prop(prefs, "hair_rig_bind_seed", text="Random Seed", slider=True)
            column.separator()
            row = column.row()
            row.scale_y = 1.5
            row.operator("cc3.hair", icon=utils.check_icon("MOD_VERTEX_WEIGHT"), text="Bind Hair").param = "BIND_TO_BONES"

            column.separator()

            # Hair curve extraction
            column = layout.column()
            column.box().label(text="Extract Curves", icon="EXPORT")
            column.row().prop(prefs, "hair_curve_merge_loops", text="")
            column.row().operator("cc3.hair", icon=utils.check_icon("HAIR"), text="Test").param = "CARDS_TO_CURVES"

            if not bpy.context.selected_objects:
                column.enabled = False




class CC3MaterialParametersPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Parameters_Panel"
    bl_label = "Material Parameters"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PIPELINE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        chr_cache, obj, mat, obj_cache, mat_cache = context_character(context)
        shader = "NONE"
        parameters = None
        if mat_cache:
            parameters = mat_cache.parameters

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
            row = column.row()
            row.prop(props, "update_mode", expand=True)

            linked = props.update_mode == "UPDATE_LINKED"
            has_key = chr_cache.import_has_key

            if chr_cache.setup_mode == "ADVANCED":

                shader = params.get_shader_name(mat_cache)
                bsdf_node, shader_node, mix_node = nodeutils.get_shader_nodes(mat, shader)
                matrix = params.get_shader_def(shader)

                if matrix and "ui" in matrix.keys():

                    ui_matrix = matrix["ui"]

                    column.separator()

                    box = column.box()
                    box.row().label(text = matrix["label"] + " Parameters", icon="MOD_HUE_SATURATION")
                    box.row().label(text = f"Material: {mat.name}", icon="SHADING_TEXTURE")


                    for ui_row in ui_matrix:

                        split = False
                        col_1 = None
                        col_2 = None

                        if ui_row[0] == "HEADER":
                            column.box().label(text= ui_row[1], icon=utils.check_icon(ui_row[2]))

                        elif ui_row[0] == "PROP":

                            show_prop = True
                            label = ui_row[1]
                            prop = ui_row[2]
                            is_slider = ui_row[3]
                            conditions = ui_row[4:]
                            alert = False
                            if len(label) > 0 and label.startswith("*"):
                                if has_key:
                                    alert = True
                                label = label[1:]

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
                                col_1.alert = alert
                                col_1.label(text=label)
                                #col_2.alert = alert
                                col_2.prop(parameters, prop, text="", slider=is_slider)

                        elif ui_row[0] == "OP":

                            show_op = True
                            label = ui_row[1]
                            op_id = ui_row[2]
                            icon = utils.check_icon(ui_row[3])
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

        # Channel Mixers

        if chr_cache and mat_cache and chr_cache.setup_mode == "ADVANCED":

            mixer_settings = mat_cache.mixer_settings

            if chr_cache and mat_cache and fake_drop_down(layout.box().row(),
                    "Texture Channel Mixer",
                    "stage_remapper",
                    props.stage_remapper):

                column = layout.column()

                show_channels = False

                for mixer_ref in channel_mixer.MIXER_CHANNELS:

                    if type(mixer_ref) == str:

                        if mixer_ref == "RGB_HEADER":
                            column.box().label(text="RGB Mask", icon="RESTRICT_COLOR_ON")
                            column.label(text = "RGB Mask Image:")
                            if mixer_settings.rgb_image:
                                column.template_ID_preview(mixer_settings, "rgb_image", open="image.open")
                                show_channels = True
                            else:
                                column.template_ID(mixer_settings, "rgb_image", open="image.open", live_icon=True)
                                show_channels = False

                        elif mixer_ref == "ID_HEADER":
                            column.separator()
                            column.box().label(text="Color ID Mask", icon="GROUP_VCOL")
                            column.label(text = "Color ID Mask Image:")
                            if mixer_settings.id_image:
                                column.template_ID_preview(mixer_settings, "id_image", open="image.open")
                                show_channels = True
                            else:
                                column.template_ID(mixer_settings, "id_image", open="image.open", live_icon=True)
                                show_channels = False

                    elif show_channels:

                        mixer_label = mixer_ref[0]
                        mixer_on_prop = mixer_ref[1]
                        mixer_type_channel = mixer_ref[2]
                        mixer_type, mixer_channel = mixer_type_channel.split("_")
                        mixer = mixer_settings.get_mixer(mixer_type, mixer_channel)

                        column = layout.column()
                        box = column.box()
                        split = box.split(factor=0.75)
                        col_1 = split.column()
                        col_2 = split.column()

                        expanded = False
                        if mixer:
                            expanded = mixer.expanded

                        row = col_1.row()
                        if expanded:
                            row.prop(mixer, "expanded", icon="TRIA_DOWN", icon_only=True, emboss=False)
                        elif mixer:
                            row.prop(mixer, "expanded", icon="TRIA_RIGHT", icon_only=True, emboss=False)
                        row.label(text=mixer_label)
                        row = col_2.row()
                        row.prop(mixer_settings, mixer_on_prop, text="", slider=True)
                        if mixer:
                            op = row.operator("cc3.mixer", icon="PANEL_CLOSE", text = "", emboss = False)
                            op.param = "REMOVE"
                            op.type_channel = mixer_type_channel

                        if mixer and mixer.enabled and expanded:

                            main_column = layout.column()
                            split = main_column.split(factor=0.01)
                            gutter = split.column()
                            column = split.column()

                            for ui_row in channel_mixer.MIXER_UI:

                                split = False
                                col_1 = None
                                col_2 = None

                                if ui_row[0] == "HEADER":
                                    column.box().label(text= ui_row[1], icon=ui_row[2])

                                elif ui_row[0] == "PROP":

                                    label = ui_row[1]
                                    prop = ui_row[2]

                                    if not split:
                                        row = column.row()
                                        split = row.split(factor=0.5)
                                        col_1 = row.column()
                                        col_2 = row.column()
                                        split = True
                                    col_1.label(text=label)
                                    col_2.prop(mixer, prop, text="", slider=True)

        # Utilities

        layout.box().label(text="Utilities", icon="MODIFIER_DATA")
        column = layout.column()
        if not chr_cache:
            column.enabled = False
        if chr_cache and utils.is_file_ext(chr_cache.import_type, "FBX"):
            split = column.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Open Mouth")
            if chr_cache:
                col_2.prop(chr_cache, "open_mouth", text="", slider=True)
            else:
                col_2.prop(props, "dummy_slider", text="", slider=True)

            col_1.label(text="Eye Close")
            if chr_cache:
                col_2.prop(chr_cache, "eye_close", text="", slider=True)
            else:
                col_2.prop(props, "dummy_slider", text="", slider=True)

        column = layout.column()
        if not chr_cache:
            column.enabled = False
        op = column.operator("cc3.setproperties", icon="DECORATE_OVERRIDE", text="Reset Parameters")
        op.param = "RESET"


class CC3RigifyPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Rigify_Panel"
    bl_label = "Rigging & Animation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PIPELINE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        chr_cache, obj, mat, obj_cache, mat_cache = context_character(context)
        missing_materials = False
        if chr_cache:
            for obj_cache in chr_cache.object_cache:
                obj = obj_cache.object
                if obj and obj.type == "MESH" and not chr_cache.has_all_materials(obj.data.materials):
                    missing_materials = True

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        width = get_layout_width("UI")

        rigify_installed = rigging.is_rigify_installed()

        if rigify_installed:

            if chr_cache:

                rig = chr_cache.get_armature()

                box = layout.box()
                split = box.split(factor=0.4)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text = "Character:")
                col_2.label(text = chr_cache.character_name)
                col_1.label(text = "Generation:")
                col_2.label(text = chr_cache.generation)
                if chr_cache.rigified:
                    col_1.label(text = "Rig Type:")
                    col_2.label(text = "Rigify")
                    col_1.label(text = "Face Rig:")
                    col_2.label(text = "Full" if chr_cache.rigified_full_face_rig else "Basic")

                if chr_cache.generation == "ActorCore":
                    box.row().operator("cc3.character", icon="MATERIAL", text="Match Existing Materials").param = "MATCH_MATERIALS"
                    if missing_materials:
                        box.row().operator("cc3.character", icon="ADD", text="Convert Materials").param = "ADD_MATERIALS"

                layout.separator()

                if fake_drop_down(layout.box().row(),
                                          "Rigify Setup",
                                          "section_rigify_setup",
                                          props.section_rigify_setup):

                    row = layout.row()
                    row.prop(chr_cache, "rig_mode", expand=True)

                    layout.separator()

                    if chr_cache.rigified:

                        if chr_cache.rigified_full_face_rig:

                            layout.row().label(text = "Face Rig Re-Parenting", icon = "INFO")

                            if chr_cache.rig_mode == "ADVANCED":

                                row = layout.row()
                                row.operator("cc3.rigifier", icon="LOCKED", text="Lock Non-Face VGroups").param = "LOCK_NON_FACE_VGROUPS"
                                row.enabled = chr_cache is not None

                                row = layout.row()
                                row.operator("cc3.rigifier", icon="MESH_DATA", text="Clean Body Mesh").param = "CLEAN_BODY_MESH"
                                row.enabled = chr_cache is not None

                                row = layout.row()
                                row.operator("cc3.rigifier", icon="ANIM_DATA", text="Reparent Auto Weights").param = "REPARENT_RIG"
                                row.enabled = chr_cache is not None

                                row = layout.row()
                                row.operator("cc3.rigifier", icon="UNLOCKED", text="Unlock VGroups").param = "UNLOCK_VGROUPS"
                                row.enabled = chr_cache is not None

                            else:

                                row = layout.row()
                                row.operator("cc3.rigifier", icon="ANIM_DATA", text="With Automatic Weights").param = "REPARENT_RIG_SEPARATE_HEAD_QUICK"
                                row.enabled = chr_cache is not None

                                if rigging.is_surface_heat_voxel_skinning_installed():
                                    row = layout.row()
                                    row.operator("cc3.rigifier_modal", icon="COMMUNITY", text="Voxel Skinning").param = "VOXEL_SKINNING"
                                    row.enabled = chr_cache is not None

                            layout.separator()

                        else:

                            layout.row().label(text = "Rigging Done.", icon = "INFO")
                            layout.separator()

                    elif chr_cache.can_be_rigged():

                        if chr_cache.rig_mode == "ADVANCED" or chr_cache.can_rig_full_face():
                            row = layout.row()
                            split = row.split(factor=0.5)
                            split.column().label(text = "Full Face Rig")
                            split.column().prop(chr_cache, "rig_face_rig", text = "")
                            if not chr_cache.can_rig_full_face() and chr_cache.rig_face_rig:
                                wrapped_text_box(layout, "Note: Full face rig cannot be auto-detected for this character.", width)

                        if chr_cache.rig_mode == "QUICK":

                            row = layout.row()
                            row.scale_y = 2
                            row.operator("cc3.rigifier", icon="OUTLINER_OB_ARMATURE", text="Rigify").param = "ALL"
                            row.enabled = chr_cache is not None

                        else:

                            row = layout.row()
                            row.scale_y = 2
                            row.operator("cc3.rigifier", icon="MOD_ARMATURE", text="Attach Meta-Rig").param = "META_RIG"
                            row.enabled = chr_cache is not None

                            row = layout.row()
                            row.scale_y = 2
                            row.operator("cc3.rigifier", icon="OUTLINER_OB_ARMATURE", text="Generate Rigify").param = "RIGIFY_META"
                            row.enabled = chr_cache is not None

                        #row = layout.row()
                        #row.scale_y = 2
                        #row.operator("cc3.rigifier", icon="MOD_ARMATURE", text="REPORT FACE TARGETS").param = "REPORT_FACE_TARGETS"
                        #row.enabled = chr_cache is not None

                    else:
                        wrapped_text_box(layout, "This character can not be rigged.", width)

                if chr_cache.rigified:

                    if fake_drop_down(layout.box().row(),
                                        "Rig Controls",
                                        "section_rigify_controls",
                                        props.section_rigify_controls):

                        split = layout.split(factor=0.6)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_3 = split.column()

                        for control_name in rigify_mapping_data.IKFK_RIG_CONTROLS:
                            control_def = rigify_mapping_data.IKFK_RIG_CONTROLS[control_name]
                            if len(control_def) == 3 and type(control_def[0]) is str:
                                col_1.label(text=control_def[0])
                                col_2.label(text=control_def[1])
                                col_3.label(text=control_def[2])
                            else:
                                prop_def_1 = control_def[0]
                                prop_def_2 = None
                                prop_def_3 = None
                                if len(control_def) >= 2:
                                    prop_def_2 = control_def[1]
                                if len(control_def) >= 3:
                                    prop_def_3 = control_def[2]

                                if prop_def_1:
                                    col_1.prop(rig.pose.bones[prop_def_1[0]], f"[\"{prop_def_1[1]}\"]", text=control_name, slider=True)
                                else:
                                    col_1.label(text="")
                                if prop_def_2:
                                    col_2.prop(rig.pose.bones[prop_def_2[0]], f"[\"{prop_def_2[1]}\"]", text="", slider=True)
                                else:
                                    col_2.label(text="")
                                if prop_def_3:
                                    col_3.prop(rig.pose.bones[prop_def_3[0]], f"[\"{prop_def_3[1]}\"]", text="", slider=True)
                                else:
                                    col_3.label(text="")

                    if fake_drop_down(layout.box().row(),
                                        "Retargeting",
                                        "section_rigify_retarget",
                                        props.section_rigify_retarget):
                        row = layout.row()
                        row.scale_y = 2
                        #row.operator("cc3.importer", icon="OUTLINER_OB_ARMATURE", text="Imp. Character").param = "IMPORT"
                        row.operator("cc3.anim_importer", icon="ARMATURE_DATA", text="Import Animations")

                        layout.label(text="Source Armature:")

                        layout.template_list("ARMATURE_UL_List", "bake_armature_list", bpy.data, "objects", props, "armature_list_index", rows=1, maxrows=4)

                        split = layout.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Source Action:")
                        col_2.prop(props, "armature_action_filter", text="Filter by Rig")

                        layout.template_list("ACTION_UL_List", "bake_action_list", bpy.data, "actions", props, "action_list_index", rows=1, maxrows=5)

                        armature_list_object = utils.collection_at_index(props.armature_list_index, bpy.data.objects)
                        action_list_action = utils.collection_at_index(props.action_list_index, bpy.data.actions)
                        source_type = "Unknown"
                        if armature_list_object:
                            source_type, source_label = rigging.get_armature_action_source_type(armature_list_object, action_list_action)
                            if source_type:
                                layout.box().label(text = f"{source_label} Animation", icon = "ARMATURE_DATA")

                        layout.label(text="Limb Correction:")
                        column = layout.column()
                        split = column.split(factor=0.5)
                        col_1 = split.column()
                        col_2 = split.column()
                        col_1.label(text="Arms")
                        col_2.prop(chr_cache, "retarget_arm_correction_angle", text="", slider=True)
                        col_1.label(text="Legs")
                        col_2.prop(chr_cache, "retarget_leg_correction_angle", text="", slider=True)
                        col_1.label(text="Heels")
                        col_2.prop(chr_cache, "retarget_heel_correction_angle", text="", slider=True)
                        col_1.label(text="Height")
                        col_2.prop(chr_cache, "retarget_z_correction_height", text="", slider=True)
                        layout.separator()

                        # retarget and bake armature actions
                        row = layout.row()
                        row.label(text="Preview Shape-keys")
                        row.prop(props, "retarget_preview_shape_keys", text="")
                        row = layout.row()
                        row.operator("cc3.rigifier", icon="ANIM_DATA", text="Preview Retarget").param = "RETARGET_CC_PAIR_RIGS"
                        row.enabled = source_type != "Unknown"
                        row = layout.row()
                        row.operator("cc3.rigifier", icon="X", text="Stop Preview").param = "RETARGET_CC_REMOVE_PAIR"
                        row.enabled = chr_cache.rig_retarget_rig is not None
                        row = layout.row()
                        row.operator("cc3.rigifier", icon="ANIM_DATA", text="Bake Retarget").param = "RETARGET_CC_BAKE_ACTION"
                        if source_type == "Unknown" and chr_cache.rig_retarget_rig is None:
                            row.enabled = False
                        layout.separator()

                        # retarget shape keys to character
                        row = layout.row()
                        row.operator("cc3.rigifier", icon="KEYINGSET", text="Retarget Shapekeys").param = "RETARGET_SHAPE_KEYS"
                        row.enabled = source_type != "Unknown"
                        layout.separator()

                        # nla bake
                        row = layout.row()
                        row.label(text="Bake Shape-keys")
                        row.prop(props, "bake_nla_shape_keys", text="")
                        row = layout.row()
                        row.operator("cc3.rigifier", icon="ANIM_DATA", text="Bake NLA").param = "NLA_CC_BAKE"
                        row.enabled = chr_cache.rig_retarget_rig is None

                        layout.separator()

                    if fake_drop_down(layout.box().row(),
                                        "Export",
                                        "section_rigify_export",
                                        props.section_rigify_export):

                        export_bake_action, export_bake_source_type = rigging.get_bake_action(chr_cache)
                        box = layout.box()
                        if export_bake_source_type == "RIGIFY":
                            box.label(text="Export from: Rigify Action")
                        elif export_bake_source_type == "RETARGET":
                            box.label(text="Export from: Retarget Action")
                        else:
                            box.label(text="Export from: NLA")
                        if export_bake_action:
                            box.row().label(text=export_bake_action.name)

                        rigify_export_group(chr_cache, layout)

            else:
                wrapped_text_box(layout, "No current character!", width, True)

        else:
            wrapped_text_box(layout, "Rigify add-on is not installed.", width, True)


class CC3ToolsScenePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Scene_Panel"
    bl_label = "Scene Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PIPELINE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        layout = self.layout

        box = layout.box()
        box.label(text="Scene Lighting", icon="LIGHT")

        column = layout.column()
        split = column.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.operator("cc3.scene", icon="SHADING_SOLID", text=" Matcap").param = "MATCAP"
        col_2.operator("cc3.scene", icon="SHADING_TEXTURE", text="Default").param = "BLENDER"
        col_1.operator("cc3.scene", icon="SHADING_TEXTURE", text="CC3").param = "CC3"
        col_2.operator("cc3.scene", icon="SHADING_RENDERED", text="Studio").param = "STUDIO"
        col_1.operator("cc3.scene", icon="SHADING_RENDERED", text="Courtyard").param = "COURTYARD"
        col_2.operator("cc3.scene", icon="SHADING_RENDERED", text="Aqua").param = "AQUA"

        box = layout.box()
        box.label(text="Scene, World & Compositor", icon="NODE_COMPOSITING")
        column = layout.column()

        op = column.operator("cc3.scene", icon="TRACKING", text="3 Point Tracking & Camera")
        op.param = "TEMPLATE"

        box = layout.box()
        box.label(text="Animation", icon="RENDER_ANIMATION")
        column = layout.column()
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
        column = layout.column()
        column.separator()
        op = column.operator("cc3.scene", icon="ARROW_LEFTRIGHT", text="Range From Character")
        op.param = "ANIM_RANGE"
        op = column.operator("cc3.scene", icon="ANIM", text="Sync Physics Range")
        op.param = "PHYSICS_PREP"
        column.separator()
        split = column.split(factor=0.0)
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
            column = layout.column()
            op = column.operator("cc3.scene", icon="PLAY", text="Cycles Setup")
            op.param = "CYCLES_SETUP"



class CC3ToolsCreatePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Create_Panel"
    bl_label = "Create Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        layout = self.layout

        chr_cache = props.get_context_character_cache(context)
        chr_rig = None
        if chr_cache:
            chr_rig = chr_cache.get_armature()
        elif context.selected_objects:
            chr_rig = utils.get_generic_character_rig(context.selected_objects)

        box = layout.box()
        box.label(text=f"Quick Export  ({vars.VERSION_STRING})", icon="EXPORT")
        # export to CC3
        character_export_button(chr_cache, chr_rig, layout)

        box = layout.box()
        box.label(text="Lighting Presets", icon="LIGHT")
        column = layout.column()
        split = column.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.operator("cc3.scene", icon="SHADING_SOLID", text=" Matcap").param = "MATCAP"
        col_2.operator("cc3.scene", icon="SHADING_TEXTURE", text="Default").param = "BLENDER"
        col_1.operator("cc3.scene", icon="SHADING_TEXTURE", text="CC3").param = "CC3"
        col_2.operator("cc3.scene", icon="SHADING_RENDERED", text="Studio").param = "STUDIO"
        col_1.operator("cc3.scene", icon="SHADING_RENDERED", text="Courtyard").param = "COURTYARD"
        col_2.operator("cc3.scene", icon="SHADING_RENDERED", text="Aqua").param = "AQUA"


class CC3ToolsPhysicsPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Physics_Panel"
    bl_label = "Physics Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        layout = self.layout

        chr_cache = props.get_context_character_cache(context)
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
                com = modifiers.get_collision_physics_mod(chr_cache, obj)
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

        if chr_cache:
            layout.box().label(text="Character Physics", icon="FORCE_CURVE")
            if chr_cache.physics_applied:
                layout.row().operator("cc3.setphysics", icon="REMOVE", text="Remove All Physics").param = "REMOVE_PHYSICS"
            else:
                layout.row().operator("cc3.setphysics", icon="ADD", text="Apply All Physics").param = "APPLY_PHYSICS"
            if chr_cache.physics_disabled:
                layout.row().operator("cc3.setphysics", icon="PLAY", text="Re-enable Physics").param = "ENABLE_PHYSICS"
            else:
                layout.row().operator("cc3.setphysics", icon="PAUSE", text="Disable Physics").param = "DISABLE_PHYSICS"

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

        weight_map : bpy.types.Image = physics.get_weight_map_from_modifiers(obj, mat)
        weight_map_size = int(props.physics_tex_size)
        if weight_map:
            split = col.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Current Size:")
            col_2.label(text=f"{weight_map.size[0]} x {weight_map.size[1]}")
            row = col.row()
            row.operator("cc3.setphysics", icon="MOD_LENGTH", text="Resize Weightmap").param = "PHYSICS_RESIZE_WEIGHTMAP"
            if (weight_map and
               (weight_map.size[0] != weight_map_size or weight_map.size[1] != weight_map_size) and
               bpy.context.mode != "PAINT_TEXTURE"):
                row.enabled = True
            else:
                row.enabled = False

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
            row = col_2.row()
            row.operator("cc3.setphysics", text="", icon='TRIA_LEFT').param = "PHYSICS_DEC_STRENGTH"
            row.prop(props, "physics_paint_strength", text="", slider=True)
            row.operator("cc3.setphysics", text="", icon='TRIA_RIGHT').param = "PHYSICS_INC_STRENGTH"
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


class CC3ToolsSculptingPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Sculpting_Panel"
    bl_label = "Sculpting"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        layout = self.layout
        chr_cache = props.get_context_character_cache(context)

        detail_body = None
        body = None
        detail_sculpting = False
        body_sculpting = False
        if chr_cache:
            detail_body = chr_cache.get_detail_body()
            body = chr_cache.get_body()
            if detail_body:
                if utils.get_active_object() == detail_body and utils.get_mode() == "SCULPT":
                    detail_sculpting = True
                if detail_body.visible_get():
                    detail_sculpting = True
            if body:
                if utils.get_active_object() == body and utils.get_mode() == "SCULPT":
                    body_sculpting = True
        has_body_overlay = sculpting.has_overlay_nodes(body, sculpting.LAYER_TARGET_SCULPT)
        has_detail_overlay = sculpting.has_overlay_nodes(detail_body, sculpting.LAYER_TARGET_DETAIL)
        has_body_mod = sculpting.has_body_multires_mod(body)

        # Full Body Sculpting

        layout.box().label(text = "Full Body Sculpting", icon = "OUTLINER_OB_ARMATURE")
        column = layout.column()
        if not chr_cache:
            column.enabled = False

        row = column.row()
        split = row.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text = "Multi-res Level")
        col_2.prop(prefs, "body_sculpt_level", slider=True)
        if body_sculpting:
            row.enabled = False

        row = column.row()
        row.scale_y = 2.0
        if not has_body_mod:
            row.operator("cc3.sculpting", icon="SCULPTMODE_HLT", text="Setup Body Sculpt").param = "BODY_SETUP"
        elif not body_sculpting:
            row.operator("cc3.sculpting", icon="SCULPTMODE_HLT", text="Begin Body Sculpt").param = "BODY_BEGIN"
        else:
            row.operator("cc3.sculpting", icon="X", text="End Body Sculpt").param = "BODY_END"

        row = column.row()
        row.operator("cc3.sculpting", icon="TRASH", text="Remove Body Sculpt").param = "BODY_CLEAN"
        if not has_body_mod:
            row.enabled = False

        row = column.row()
        split = row.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text = "Bake Size")
        col_2.prop(prefs, "body_normal_bake_size", text = "")

        row = column.row()
        split = row.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.operator("cc3.sculpting", icon="SCULPTMODE_HLT", text="Bake").param = "BODY_BAKE"
        if not has_body_mod:
            col_1.enabled = False
        if chr_cache:
            col_2.prop(chr_cache, "body_normal_strength", text="", slider=True)
            if not has_body_overlay:
                col_2.enabled = False

        column.separator()

        row = column.row()
        row.scale_y = 2
        row.operator("cc3.sculpting", icon="EXPORT", text="Export Layer").param = "BODY_SKINGEN"
        if not has_body_mod or not has_body_overlay:
            row.enabled = False

        column.separator()


        # Detail Sculpting

        layout.box().label(text = "Detail Sculpting", icon = "POSE_HLT")
        column = layout.column()
        if not chr_cache:
            column.enabled = False

        row = column.row()
        row.prop(prefs, "detail_sculpt_target", expand=True)
        if detail_body or detail_sculpting:
            row.enabled = False

        row = column.row()
        split = row.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text = "Multi-res Level")
        col_2.prop(prefs, "detail_sculpt_level", slider=True)
        if detail_body or detail_sculpting:
            row.enabled = False

        row = column.row()
        row.scale_y = 2.0
        if not detail_body:
            row.operator("cc3.sculpting", icon="SCULPTMODE_HLT", text="Setup Detail Sculpt").param = "DETAIL_SETUP"
        elif not detail_sculpting:
            row.operator("cc3.sculpting", icon="SCULPTMODE_HLT", text="Begin Detail Sculpt").param = "DETAIL_BEGIN"
        else:
            row.operator("cc3.sculpting", icon="X", text="End Detail Sculpt").param = "DETAIL_END"

        row = column.row()
        row.operator("cc3.sculpting", icon="TRASH", text="Remove Detail Sculpt").param = "DETAIL_CLEAN"
        if not detail_body:
            row.enabled = False

        row = column.row()
        split = row.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text = "Bake Size")
        col_2.prop(prefs, "detail_normal_bake_size", text = "")

        row = column.row()
        split = row.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.operator("cc3.sculpting", icon="SCULPTMODE_HLT", text="Bake").param = "DETAIL_BAKE"
        if not detail_body:
            col_1.enabled = False
        if chr_cache:
            col_2.prop(chr_cache, "detail_normal_strength", text="", slider=True)
            if not has_detail_overlay:
                col_2.enabled = False

        column.separator()

        row = column.row()
        row.scale_y = 2
        row.operator("cc3.sculpting", icon="EXPORT", text="Export Layer").param = "DETAIL_SKINGEN"
        if not detail_body or not has_detail_overlay:
            row.enabled = False

        column.separator()


class CC3ToolsUtilityPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Utility_Panel"
    bl_label = "Utilities"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        layout = self.layout
        chr_cache = props.get_context_character_cache(context)

        row = layout.row()
        row.operator("cc3.character", icon="MATERIAL", text="Match Materials").param = "MATCH_MATERIALS"



class CC3ToolsPipelinePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Pipeline_Panel"
    bl_label = "Import / Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PIPELINE_TAB_NAME

    def draw(self, context):
        global debug_counter
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        addon_updater_ops.check_for_update_background()
        if addon_updater_ops.updater.update_ready == True:
            addon_updater_ops.update_notice_box_ui(self, context)

        chr_cache = props.get_context_character_cache(context)
        if chr_cache:
            character_name = chr_cache.character_name
        else:
            character_name = "No Character"
        chr_rig = None
        if chr_cache:
            chr_rig = chr_cache.get_armature()
        elif context.selected_objects:
            chr_rig = utils.get_generic_character_rig(context.selected_objects)

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        box = layout.box()
        box.label(text=f"Settings  ({vars.VERSION_STRING})", icon="TOOL_SETTINGS")

        if prefs.lighting == "ENABLED" or prefs.physics == "ENABLED":
            if prefs.lighting == "ENABLED":
                layout.prop(props, "lighting_mode", expand=True)
            if prefs.physics == "ENABLED":
                layout.prop(props, "physics_mode", expand=True)

        box = layout.box()
        box.label(text="Importing", icon="IMPORT")
        row = layout.row()
        row.scale_y = 2
        op = row.operator("cc3.importer", icon="OUTLINER_OB_ARMATURE", text="Import Character")
        op.param = "IMPORT"
        layout.separator()
        row = layout.row()
        row.scale_y = 2
        op = row.operator("cc3.anim_importer", icon="ARMATURE_DATA", text="Import Animations")

        if chr_cache and chr_cache.rigified:
            box = layout.box()
            box.label(text="Exporting (Rigify)", icon="EXPORT")
            rigify_export_group(chr_cache, layout)
        else:
            box = layout.box()
            box.label(text="Exporting", icon="EXPORT")
            pipeline_export_group(chr_cache, chr_rig, layout)

        # export prefs
        box = layout.box()
        if fake_drop_down(box.row(),
                "Export Prefs",
                "export_options",
                props.export_options):
            box.row().prop(prefs, "export_json_changes", expand=True)
            box.row().prop(prefs, "export_texture_changes", expand=True)
            if prefs.export_texture_changes:
                box.row().prop(prefs, "export_bake_nodes", expand=True)
                if prefs.export_bake_nodes:
                    box.row().prop(prefs, "export_bake_bump_to_normal", expand=True)
            box.row().prop(prefs, "export_bone_roll_fix", expand=True)
            box.row().prop(prefs, "export_revert_names", expand=True)
        row = layout.row()

        # export extras
        op = layout.row().operator("cc3.exporter", icon="MOD_CLOTH", text="Export Accessory").param = "EXPORT_ACCESSORY"
        op = layout.row().operator("cc3.exporter", icon="MESH_DATA", text="Export Replace Mesh").param = "EXPORT_MESH"

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
