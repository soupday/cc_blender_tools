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
import textwrap
import os

from . import addon_updater_ops, rigging, rigutils
from . import (link, rigify_mapping_data, bones, characters, sculpting, springbones,
               bake, rigidbody, physics, colorspace, modifiers, channel_mixer, nodeutils,
               utils, params, vars)

PIPELINE_TAB_NAME = "CC/iC Pipeline"
CREATE_TAB_NAME = "CC/iC Create"
LINK_TAB_NAME = "CC/iC Link"

# Panel functions and classes
#

def fake_drop_down(row, label, prop_name, prop_bool_value, icon = "TRIA_DOWN", icon_closed = "TRIA_RIGHT"):
    props = bpy.context.scene.CC3ImportProps
    row.alignment="LEFT"

    if prop_bool_value:
        row.prop(props, prop_name, icon=icon, text=label, emboss=False)
    else:
        row.prop(props, prop_name, icon=icon_closed, text=label, emboss=False)

    if icon != "TRIA_DOWN":
        if prop_bool_value:
            row.prop(props, prop_name, icon="TRIA_DOWN", icon_only=True, emboss=False)
        else:
            row.prop(props, prop_name, icon="TRIA_RIGHT", icon_only=True, emboss=False)
    return prop_bool_value


def get_layout_width(context=None, region_type="UI"):
    ui_shelf = None
    if not context:
        context = bpy.context
    area = context.area
    width = 15
    for region in area.regions:
        if region.type == region_type:
            ui_shelf = region
            width = int(ui_shelf.width / 8)
    return width


def wrapped_text_box(layout, info_text, width, alert = False, icon = None):
    wrapper = textwrap.TextWrapper(width=width)
    info_list = wrapper.wrap(info_text)

    box = layout.box()
    box.alert = alert
    first = True
    for text in info_list:
        if first and icon:
            box.label(text=text, icon=icon)
        else:
            box.label(text=text)
        first = False


def warn_icon(row, icon = "ERROR"):
    col = row.column()
    col.alert = True
    col.label(text="", icon=icon)


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

    box = layout.box()
    if is_character:
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
        box.row().label(text=f"No Character")

    return box


def reconnect_character_ui(context, layout: bpy.types.UILayout, chr_cache):
    width = get_layout_width(context, "UI")
    rig = utils.get_context_armature(context)
    if not context.selected_objects:
        rig = None
    wrapped_text_box(layout, "Linking", width, alert=False, icon="LINKED")
    if not chr_cache and rig and rigutils.is_rl_rigify_armature(rig):
        row = layout.row()
        row.scale_y = 1.5
        op = row.operator("ccic.characterlink", icon="OUTLINER_OB_ARMATURE", text="Connect Rigified").param = "CONNECT"
    elif not chr_cache and rig and rigutils.is_rl_armature(rig):
        row = layout.row()
        row.scale_y = 1.5
        op = row.operator("ccic.characterlink", icon="ARMATURE_DATA", text="Connect Character").param = "CONNECT"
    else:
        row = layout.row(align=True)
        row.scale_y = 1.5
        op = row.operator("ccic.characterlink", icon="LINKED", text="Link").param = "LINK"
        op = row.operator("ccic.characterlink", icon="APPEND_BLEND", text="Append").param = "APPEND"


def pipeline_export_group(chr_cache, chr_rig, layout: bpy.types.UILayout):
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

    #layout.separator()
    #
    ## export to Unreal
    # character_export_unreal_button(chr_cache, layout)


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


def character_export_button(chr_cache, chr_rig, layout : bpy.types.UILayout, scale=2, warn=True):
    # export to CC3
    text = "Export to CC3/4"
    icon = "MOD_ARMATURE"

    standard_export = chr_cache and chr_cache.is_standard()
    non_standard_export = (chr_cache and chr_cache.is_non_standard()) or (chr_rig and not standard_export)

    if chr_cache:
        row = layout.row()
        row.scale_y = scale
        if chr_cache and chr_cache.is_import_type("OBJ"):
            text = "Export Morph Target"
            icon = "ARROW_LEFTRIGHT"
        row.operator("cc3.exporter", icon=icon, text=text).param = "EXPORT_CC3"
        if not chr_cache.can_export():
            row.enabled = False
            if warn and not chr_cache.get_import_has_key():
                if chr_cache.is_import_type("FBX"):
                    layout.row().label(text="No Fbx-Key file!", icon="ERROR")
                elif chr_cache.is_import_type("OBJ"):
                    layout.row().label(text="No Obj-Key file!", icon="ERROR")

    elif chr_rig:
        row = layout.row()
        row.scale_y = scale
        text = "Export Non-Standard"
        icon = "MONKEY"
        row.operator("cc3.exporter", icon=icon, text=text).param = "EXPORT_NON_STANDARD"

    else:
        row = layout.row()
        row.scale_y = scale
        row.operator("cc3.exporter", icon=icon, text=text).param = "EXPORT_CC3"
        row.enabled = False
        if warn:
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
    if not chr_cache or not chr_cache.is_import_type("FBX") or chr_cache.rigified:
        column.enabled = False


def character_export_unreal_button(chr_cache, layout):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    column = layout.column()

    # export button
    row = column.row()
    row.scale_y = 2
    row.operator("cc3.exporter", icon="EVENT_U", text="Export To Unreal").param = "EXPORT_UNREAL"

    # disable if no character, or not an fbx import
    if not chr_cache or not chr_cache.is_import_type("FBX") or chr_cache.rigified:
        column.enabled = False


def rigid_body_sim_ui(chr_cache, arm, obj, layout : bpy.types.UILayout,
                      fixed_parent=False, only_parent_mode=None,
                      show_selector=True, enabled=True):

    props = bpy.context.scene.CC3ImportProps

    if not chr_cache or not arm:
        return

    rigid_body = rigidbody.get_rigid_body(chr_cache, obj)
    rigid_body_sim = None
    parent_mode = chr_cache.available_spring_rigs
    if fixed_parent:
        parent_mode = only_parent_mode
    prefix = springbones.get_spring_rig_prefix(parent_mode)
    rigid_body_sim = rigidbody.get_spring_rigid_body_system(arm, prefix)
    has_spring_rig = springbones.has_spring_rig(chr_cache, arm, parent_mode)

    box = layout.box()
    if fake_drop_down(box.row(),
            "Rigid Body Sim",
            "section_rigidbody_spring_ui",
            props.section_rigidbody_spring_ui,
            icon="BLENDER", icon_closed="BLENDER"):

        column = box.column()
        column.enabled = enabled

        if not fixed_parent and show_selector:
            split = column.split(factor=0.45)
            split.column().label(text="Hair System")
            #split.column().prop(props, "hair_rig_bone_root", text="")
            split.column().prop(chr_cache, "available_spring_rigs", text="")

        if not has_spring_rig:
            row = column.row()
            row.label(text = "No Spring Rig", icon="ERROR")

        if rigid_body_sim:
            split = column.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Influence")
            col_2.prop(rigid_body_sim, "[\"rigid_body_influence\"]", text="", slider=True)
            col_1.label(text="Restrain")
            col_2.prop(rigid_body_sim, "[\"rigid_body_limit\"]", text="", slider=True)
            col_1.label(text="Curve")
            col_2.prop(rigid_body_sim, "[\"rigid_body_curve\"]", text="", slider=True)
            col_1.label(text="Mass")
            col_2.prop(rigid_body_sim, "[\"rigid_body_mass\"]", text="", slider=True)
            col_1.label(text="Margin")
            col_2.prop(rigid_body_sim, "[\"rigid_body_margin\"]", text="", slider=True)
            col_1.label(text="Dampening")
            col_2.prop(rigid_body_sim, "[\"rigid_body_dampening\"]", text="", slider=True)
            col_1.label(text="Stiffness")
            col_2.prop(rigid_body_sim, "[\"rigid_body_stiffness\"]", text="", slider=True)
            col_1.label(text="Angle Range")
            col_2.prop(rigid_body_sim, "[\"rigid_body_angle_limit\"]", text="", slider=True)

            column.separator()

        if parent_mode:
            if not rigid_body_sim:
                row = column.row()
                row.scale_y = 2.0
                row.operator("cc3.springbones", icon=utils.check_icon("CON_KINEMATIC"), text="Build Simulation").param = "MAKE_RIGID_BODY_SYSTEM"
                column.separator()
                if not has_spring_rig:
                    row.enabled = False
            else:
                row = column.row()
                row.scale_y = 2.0
                warn_icon(row, "X")
                row.operator("cc3.springbones", icon=utils.check_icon("X"), text="Remove Simulation").param = "REMOVE_RIGID_BODY_SYSTEM"
                column.separator()
        else:
            column.row().label(text = "No spring rig selected", icon="ERROR")

        column.row().label(text="Rigid Body Colliders:")

        if rigidbody.has_rigid_body_colliders(arm):
            row = column.row(align=True)
            colliders_visible = rigidbody.colliders_visible(arm)
            row.operator("cc3.springbones", icon=utils.check_icon("HIDE_OFF"), text="", depress=colliders_visible).param = "TOGGLE_SHOW_COLLIDERS"
            is_pose_position = rigging.is_rig_rest_position(chr_cache)
            row.operator("cc3.rigifier", icon="OUTLINER_OB_ARMATURE", text="", depress=is_pose_position).param = "TOGGLE_SHOW_RIG_POSE"
            row.operator("cc3.springbones", icon=utils.check_icon("X"), text="Remove Colliders").param = "REMOVE_COLLIDERS"
            #column.row().prop(rigid_body, "collision_margin", text="Collision Margin", slider=True)
        else:
            column.row().operator("cc3.springbones", icon=utils.check_icon("META_CAPSULE"), text="Add Colliders").param = "BUILD_COLLIDERS"

        column.separator()

        # Cache
        has_rigidbody, rigidbody_baked, rigidbody_baking, rigidbody_point_cache = springbones.rigidbody_state()

        column.row().label(text="Animation Range:")
        row = column.row(align=True)
        row.prop(bpy.context.scene, "use_preview_range", text="", toggle=True)
        grid = row.grid_flow(columns=2, align=True)
        grid.operator("cc3.scene", icon="FULLSCREEN_ENTER", text="Expand").param = "ANIM_RANGE_EXPAND"
        grid.operator("cc3.scene", icon="FULLSCREEN_EXIT", text="Fit").param = "ANIM_RANGE_FIT"
        column.row().label(text="Rigid Body Cache:")
        row = column.row()
        row.operator("cc3.springbones", icon=utils.check_icon("LOOP_BACK"), text="Reset Simulation").param = "RESET_PHYSICS"
        row = column.row()
        row.scale_y = 1.5
        row.context_pointer_set("point_cache", rigidbody_point_cache)
        depress = rigidbody_baking
        row.alert = rigidbody_baked
        if rigidbody_baked:
            row.operator("ptcache.free_bake", text="Free Simulation", icon="REC")
        else:
            row.operator("ptcache.bake", text="Bake Simulation", icon="REC", depress=rigidbody_baking).bake = True


def cache_timeline_physics_ui(chr_cache, layout : bpy.types.UILayout):
    if not chr_cache:
        return
    layout.box().label(text="Timeline & Physics Cache", icon="PREVIEW_RANGE")
    layout.row().label(text="Animation Range:")
    row = layout.row(align=True)
    row.prop(bpy.context.scene, "use_preview_range", text="", toggle=True)
    grid = row.grid_flow(columns=2, align=True)
    grid.operator("cc3.scene", icon="FULLSCREEN_ENTER", text="Expand").param = "ANIM_RANGE_EXPAND"
    grid.operator("cc3.scene", icon="FULLSCREEN_EXIT", text="Fit").param = "ANIM_RANGE_FIT"

    layout.separator()

    """
    if not bpy.data.filepath:
        row = layout.row()
        row.alert = True
        row.label(text="Blendfile should be saved", icon="ERROR")
        row = layout.row()
        row.alert = True
        row.label(text="before baking physics", icon="REMOVE")
        layout.separator()
    """

    if bpy.context.object:
        layout.label(text=bpy.context.object.name, icon="OBJECT_DATA")

    has_cloth, cloth_baked, cloth_baking, cloth_point_cache = physics.cloth_physics_state(bpy.context.object)
    has_rigidbody, rigidbody_baked, rigidbody_baking, rigidbody_point_cache = springbones.rigidbody_state()

    grid = layout.grid_flow(row_major=True, columns=2)

    grid_column = grid.column(align=True)
    grid_column.label(text="Cloth Physics", icon="MOD_CLOTH")

    row = grid_column.row(align=True)
    row.operator("cc3.scene", icon="LOOP_BACK", text="Reset").param = "PHYSICS_PREP_CLOTH"
    row = grid_column.row(align=True)
    row.context_pointer_set("point_cache", cloth_point_cache)
    row.scale_y = 1.5
    row.alert = cloth_baked
    if cloth_baked:
        row.operator("ptcache.free_bake", text="Free", icon="REC")
    else:
        row.operator("ptcache.bake", text="Bake", icon="REC", depress=cloth_baking).bake = True

    if not has_cloth:
        grid_column.enabled = False

    grid_column = grid.column(align=True)
    grid_column.label(text="Spring Physics", icon="CON_KINEMATIC")

    row = grid_column.row(align=True)
    row.operator("cc3.scene", icon="LOOP_BACK", text="Reset").param = "PHYSICS_PREP_RBW"
    row = grid_column.row(align=True)
    row.context_pointer_set("point_cache", rigidbody_point_cache)
    row.scale_y = 1.5
    row.alert = rigidbody_baked
    if rigidbody_baked:
        row.operator("ptcache.free_bake", text="Free", icon="REC")
    else:
        row.operator("ptcache.bake", text="Bake", icon="REC", depress=rigidbody_baking).bake = True

    if not has_rigidbody:
        grid_column.enabled = False

    layout.separator()

    has_cloth, has_collision, has_rigidbody, all_baked, any_baked, all_baking, any_baking = physics.get_scene_physics_state()

    layout.label(text="All Dynamics:", icon="PHYSICS")

    column = layout.column(align=True)
    column.operator("cc3.scene", icon="LOOP_BACK", text="Reset All").param = "PHYSICS_PREP_ALL"
    row = column.row(align=True)
    row.scale_y = 1.5
    row.alert = all_baked
    all_depress = all_baking
    if any_baked:
        row.operator("ptcache.free_bake_all", text="Free All Dynamics", icon="REC")
    else:
        row.operator("ptcache.bake_all", text="Bake All Dynamics", icon="REC", depress=all_depress).bake = True



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
        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)

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
                box.label(text="Type: " + chr_cache.get_import_type().upper())
                split = box.split(factor=0.4)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Generation")
                col_2.prop(chr_cache, "generation", text="")
                col_1.label(text="Key File")
                col_2.prop(chr_cache, "import_has_key", text="")
                box.prop(chr_cache, "import_file", text="")
                for obj_cache in chr_cache.object_cache:
                    o = obj_cache.get_object()
                    if o:
                        box.prop(obj_cache, "object", text="")
            else:
                box.label(text="Name: " + chr_cache.character_name)
        else:
            box.label(text="No Character")

        # Build Settings

        # Build prefs in title
        box = layout.box()
        if fake_drop_down(box.row(), "Build Settings", "show_build_prefs2", props.show_build_prefs2,
                          icon="TOOL_SETTINGS", icon_closed="TOOL_SETTINGS"):
            split = box.split(factor=0.9)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="De-duplicate Materials")
            col_2.prop(prefs, "import_deduplicate", text="")
            col_1.label(text="Auto Convert Generic")
            col_2.prop(prefs, "import_auto_convert", text="")
            col_1.label(text="Limit Textures")
            col_2.prop(prefs, "build_limit_textures", text="")
            col_1.label(text="Pack Texture Channels")
            col_2.prop(prefs, "build_pack_texture_channels", text="")
            col_1.label(text="Reuse Channel Packs")
            col_2.prop(prefs, "build_reuse_baked_channel_packs", text="")
            col_1.label(text="Use Edit Modifier")
            col_2.prop(prefs, "build_armature_edit_modifier", text="")
            col_1.label(text="Use Preserve Volume")
            col_2.prop(prefs, "build_armature_preserve_volume", text="")
            col_1.label(text="Dual Specular Skin")
            col_2.prop(prefs, "build_skin_shader_dual_spec", text="")
            col_1.separator()
            col_2.separator()
            col_1.label(text="Shape Keys Drive Jaw Bone")
            col_2.prop(prefs, "build_shape_key_bone_drivers_jaw", text="")
            col_1.label(text="Shape Keys Drive Eye Bones")
            col_2.prop(prefs, "build_shape_key_bone_drivers_eyes", text="")
            col_1.label(text="Shape Keys Drive Head Bone")
            col_2.prop(prefs, "build_shape_key_bone_drivers_head", text="")
            col_1.separator()
            col_2.separator()
            col_1.label(text="Body Shape Keys Drive All")
            col_2.prop(prefs, "build_body_key_drivers", text="")

        column = layout.column(align=True)
        row = column.row(align=True)
        row.prop(props, "physics_mode", toggle=True, text="Build Physics")
        row.prop(props, "wrinkle_mode", toggle=True, text="Wrinkles")
        row = column.row(align=True)
        row.prop(chr_cache if chr_cache else props, "setup_mode", expand=True)
        row = column.row(align=True)
        row.prop(prefs, "render_target", expand=True)
        row = column.row(align=True)
        row.prop(prefs, "refractive_eyes", expand=True)

        # ACES Prefs
        if colorspace.is_aces():
            layout.box().label(text="ACES Settings", icon="COLOR")
            split = layout.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="sRGB Override")
            col_2.prop(prefs, "aces_srgb_override", text="")
            col_1.label(text="Data Override")
            col_2.prop(prefs, "aces_data_override", text="")

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
                col_2.prop(prefs, "cycles_sss_skin_v203", text = "")
                col_1.label(text = "Hair SSS")
                col_2.prop(prefs, "cycles_sss_hair_v203", text = "")
                col_1.label(text = "Teeth SSS")
                col_2.prop(prefs, "cycles_sss_teeth_v203", text = "")
                col_1.label(text = "Tongue SSS")
                col_2.prop(prefs, "cycles_sss_tongue_v203", text = "")
                col_1.label(text = "Eyes SSS")
                col_2.prop(prefs, "cycles_sss_eyes_v203", text = "")
                col_1.label(text = "Default SSS")
                col_2.prop(prefs, "cycles_sss_default_v203", text = "")

        # Build Button
        if chr_cache:
            box = layout.box()
            box.row().label(text="Rebuild Materials", icon="MOD_BUILD")
            row = box.row()
            row.scale_y = 2
            if chr_cache.setup_mode == "ADVANCED":
                op = row.operator("cc3.importer", icon="SHADING_TEXTURE", text="Rebuild Materials")
            else:
                op = row.operator("cc3.importer", icon="NODE_MATERIAL", text="Rebuild Materials")
            op.param ="BUILD"
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
    bl_label = "Character Management"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)
        strict_chr_cache = chr_cache if obj and obj_cache else None
        non_chr_objects = [ obj for obj in context.selected_objects if props.get_object_cache(obj, strict=True) is None ]

        generic_rig = None
        arm = None
        if chr_cache:
            arm = chr_cache.get_armature()
        else:
            generic_rig = characters.get_generic_rig(context.selected_objects)
            if generic_rig:
                arm = generic_rig

        rigified = chr_cache and chr_cache.rigified
        is_standard = chr_cache and chr_cache.is_standard()
        num_meshes_in_selection = 0
        weight_transferable = False
        removable_objects = False
        missing_materials = False
        objects_addable = False
        is_character = chr_cache is not None
        from_other_character = False
        for o in bpy.context.selected_objects:
            if o.type == "MESH":
                num_meshes_in_selection += 1
                if chr_cache:
                    oc = chr_cache.get_object_cache(o)
                    if oc and not oc.disabled:
                        if oc.object_type == "DEFAULT" or oc.object_type == "HAIR":
                            weight_transferable = True
                            removable_objects = True
                        if not chr_cache.has_all_materials(o.data.materials):
                            missing_materials = True
                    if not oc or oc.disabled:
                        objects_addable = True
                    if not from_other_character:
                        cc = props.get_character_cache(o, None)
                        if cc is not None and cc != chr_cache:
                            from_other_character = True

        column = layout.column()

        # Converting

        if not rigified:

            column.box().label(text="Converting", icon="DRIVER")

            if chr_cache:

                box = character_info_box(chr_cache, arm, column)

                if chr_cache.is_standard():

                    row = box.row()
                    row.operator("cc3.character", icon="MESH_MONKEY", text="Convert to Non-standard").param = "CONVERT_TO_NON_STANDARD"
                    if not chr_cache or chr_cache.is_non_standard():
                        row.enabled = False

            if generic_rig or non_chr_objects:

                obj_text = "Objects: "
                for i, obj in enumerate(non_chr_objects):
                    if i > 0:
                        obj_text += ", "
                    obj_text += obj.name
                if len(non_chr_objects) == 0:
                    obj_text += "None"

                column.box().label(text=obj_text)

                row = column.row()
                if generic_rig:
                    row.operator("cc3.character", icon="COMMUNITY", text="Convert from Generic").param = "CONVERT_FROM_GENERIC"
                else:
                    row.operator("cc3.character", icon="COMMUNITY", text="Convert from Objects").param = "CONVERT_FROM_GENERIC"
                if not (generic_rig or non_chr_objects):
                    row.enabled = False

            column.separator()

        # Accessory Management

        if not rigified and is_standard:

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
                if chr_cache and arm:
                    split = column.split(factor=0.375)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Parent:")
                    col_2.prop_search(chr_cache, "accessory_parent_bone", arm.data, "bones", text="")
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
        if not is_character:
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

        if from_other_character:
            row = column.row()
            row.operator("cc3.character", icon="PASTEDOWN", text="Copy to Character").param = "COPY_TO_CHARACTER"
            if not objects_addable:
                row.enabled = False
        else:
            row = column.row()
            row.operator("cc3.character", icon="ADD", text="Add to Character").param = "ADD_PBR"
            if not objects_addable:
                row.enabled = False

        row = column.row()
        row.operator("cc3.character", icon="REMOVE", text="Remove from Character").param = "REMOVE_OBJECT"
        if not removable_objects:
            row.enabled = False

        row = column.row()
        row.operator("cc3.character", icon="ADD", text="Add New Materials").param = "ADD_MATERIALS"
        if not missing_materials:
            row.enabled = False

        column.separator()

        row = column.row()
        row.operator("cc3.character", icon="MATERIAL", text="Match Materials").param = "MATCH_MATERIALS"

        column.separator()

        # Armature & Weights

        column.box().label(text = "Armature & Weights", icon = "ARMATURE_DATA")

        if arm:
            column.row().prop(arm.data, "pose_position", expand=True)

        row = column.row()
        row.operator("cc3.character", icon="MOD_DATA_TRANSFER", text="Transfer Weights").param = "TRANSFER_WEIGHTS"
        if not weight_transferable:
            row.enabled = False

        row = column.row()
        row.operator("cc3.character", icon="ORIENTATION_NORMAL", text="Normalize Weights").param = "NORMALIZE_WEIGHTS"
        if not weight_transferable:
            row.enabled = False


class CC3SpringRigPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_SpringRig_Panel"
    bl_label = "Spring Rigging"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)
        arm = None
        can_hair_spring_rig = False
        can_spring_rig = False
        if chr_cache:
            arm = chr_cache.get_armature()
            if arm:
                can_spring_rig = True
                can_hair_spring_rig = chr_cache.can_hair_spring_rig()

        if chr_cache and not can_hair_spring_rig:
            row = layout.row()
            row.alert = True
            row.label(icon="ERROR", text="Unsupported Character")
        elif not chr_cache:
            row = layout.row()
            row.alert = True
            row.label(icon="ERROR", text="Invalid Character")

        # Hair Cards & Spring Bone Rig

        icon = utils.check_icon("OUTLINER_OB_HAIR")
        if fake_drop_down(layout.box().row(),
                "Hair Rigging",
                "section_hair_rigging",
                props.section_hair_rigging,
                icon=icon, icon_closed=icon):

            edit_enabled = True
            if (chr_cache and chr_cache.rigified and
                springbones.is_rigified(chr_cache, arm, props.hair_rig_bone_root)):
                edit_enabled = False

            valid_character = False
            if chr_cache and chr_cache.can_hair_spring_rig():
                valid_character = True

            column = layout.column()
            column.enabled = valid_character
            column.label(text="Hair Card UV Directions:", icon="OUTLINER_OB_LATTICE")
            split = column.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Vertical Cards")
            col_2.row().prop(props, "hair_card_vertical_dir", text="", expand=True)
            col_1.label(text="Horizontal Cards")
            col_2.row().prop(props, "hair_card_horizontal_dir", text="", expand=True)
            col_1.label(text="Square Cards")
            col_2.row().prop(props, "hair_card_square_dir", text="", expand=True)
            column.row().prop(props, "hair_card_dir_threshold", text="Alignment Threshold", slider=True)

            column.separator()

            box = column.box()
            box.label(text="Hair Spring Rig", icon="FORCE_MAGNETIC")
            row = box.row()
            row.prop(props, "hair_rig_target", expand=True)
            row.scale_y = 2

            column.separator()

            grid = column.grid_flow(columns=1)
            grid.prop(props, "hair_rig_bone_length", text="Bone Length (cm)", slider=True)
            grid.prop(props, "hair_rig_bind_skip_length", text="Skip Length (cm)", slider=True)
            grid.prop(props, "hair_rig_bind_trunc_length", text="Truncate Length (cm)", slider=True)
            grid.prop(props, "hair_rig_bone_smoothing", text="Smoothing Steps", slider=True)


            column.separator()

            split = column.split(factor=0.45)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Hair System")
            col_2.prop(props, "hair_rig_bone_root", text="")
            col_1.label(text="Group Name")
            col_2.prop(props, "hair_rig_group_name", text="")
            tool_row = col_1.row(align=True)
            if arm:
                depress = bones.is_bone_collection_visible(arm, "Spring (Edit)", vars.SPRING_EDIT_LAYER)
                tool_row.operator("cc3.rigifier", icon=utils.check_icon("HIDE_OFF"), text="",
                                  depress=depress).param = "TOGGLE_SHOW_SPRING_BONES"
                is_grease_pencil_tool = "builtin.annotate" in utils.get_current_tool_idname(context)
                tool_row.operator("cc3.hair", icon=utils.check_icon("GREASEPENCIL"), text="", depress=is_grease_pencil_tool).param = "TOGGLE_GREASE_PENCIL"
                is_default_bone = False
                if arm.data.display_type == 'WIRE':
                    icon = "IPO_LINEAR"
                elif arm.data.display_type == 'OCTAHEDRAL' and arm.display_type == 'SOLID':
                    icon = "PMARKER_ACT"
                    is_default_bone = True
                elif arm.data.display_type == 'OCTAHEDRAL' and arm.display_type == 'WIRE':
                    icon = "PMARKER_SEL"
                elif arm.data.display_type == 'STICK':
                    icon = "FIXED_SIZE"
                else:
                    icon = "BONE_DATA"
                tool_row.operator("cc3.hair", icon=utils.check_icon(icon), text="", depress=False).param = "CYCLE_BONE_STYLE"
                is_pose_position = rigging.is_rig_rest_position(chr_cache)
                tool_row.operator("cc3.rigifier", icon="OUTLINER_OB_ARMATURE", text="", depress=is_pose_position).param = "TOGGLE_SHOW_RIG_POSE"

            row = col_2.row()
            row.operator("cc3.hair", icon=utils.check_icon("GROUP_BONE"), text="Rename").param = "GROUP_NAME_BONES"
            row.enabled = edit_enabled
            column.separator()

            row = column.row()
            row.scale_y = 1.5
            row.operator("cc3.hair", icon=utils.check_icon("MOD_LATTICE"), text="Bones from Cards").param = "ADD_BONES"
            row.enabled = edit_enabled

            column.separator()

            row = column.row()
            row.scale_y = 1.5
            row.operator("cc3.hair", icon=utils.check_icon("GREASEPENCIL"), text="Bones from Grease Pencil").param = "ADD_BONES_GREASE"
            row.enabled = edit_enabled

            column.separator()

            row = column.row()
            row.scale_y = 1.5
            row.operator("cc3.hair", icon=utils.check_icon("GROUP_BONE"), text="Add Custom Bone").param = "ADD_BONES_CUSTOM"
            row.enabled = edit_enabled

            column.separator()

            row = column.row()
            row.scale_y = 1
            warn_icon(row, "X")
            op_text = "Clear All Hair Bones" if props.hair_rig_bind_bone_mode == "ALL" else "Clear Selected Bones"
            row.operator("cc3.hair", icon=utils.check_icon("BONE_DATA"), text=op_text).param = "REMOVE_HAIR_BONES"
            row.enabled = edit_enabled

            row = column.row()
            row.scale_y = 1
            warn_icon(row, "X")
            op_text = "Clear All Hair Weights" if props.hair_rig_bind_bone_mode == "ALL" and props.hair_rig_bind_card_mode == "ALL" else "Clear Selected Weights"
            row.operator("cc3.hair", icon=utils.check_icon("MOD_VERTEX_WEIGHT"), text=op_text).param = "CLEAR_WEIGHTS"
            row.enabled = edit_enabled

            row = column.row()
            row.scale_y = 1
            warn_icon(row, "X")
            op_text = "Clear Grease Pencil"
            row.operator("cc3.hair", icon=utils.check_icon("OUTLINER_OB_GREASEPENCIL"), text=op_text).param = "CLEAR_GREASE_PENCIL"
            row.enabled = edit_enabled

            column.separator()

            grid = column.grid_flow(columns=1)
            grid.row().prop(props, "hair_rig_bind_bone_mode", expand=True)
            grid.row().prop(props, "hair_rig_bind_card_mode", expand=True)
            grid.separator()
            grid.prop(props, "hair_rig_bind_bone_radius", text="Bind Radius (cm)", slider=True)
            grid.prop(props, "hair_rig_bind_bone_count", text="Bind Bones", slider=True)
            grid.prop(props, "hair_rig_bind_bone_weight", text="Weight Scale", slider=True)
            grid.prop(props, "hair_rig_bind_weight_curve", text="Weight Curve", slider=True)
            grid.prop(props, "hair_rig_bind_bone_variance", text="Weight Variance", slider=True)
            grid.prop(props, "hair_rig_bind_smoothing", text="Smoothing", slider=True)
            grid.prop(props, "hair_rig_bind_seed", text="Random Seed", slider=True)
            if props.hair_rig_target != "CC4":
                grid.separator()
                grid.prop(props, "hair_rig_bind_existing_scale", text="Scale Body Weights", slider=True)
            column.separator()
            row = column.row()
            row.scale_y = 2.0
            op_text = "Bind Hair" if props.hair_rig_bind_card_mode == "ALL" and props.hair_rig_bind_bone_mode == "ALL" else "Bind Selected Hair"
            row.operator("cc3.hair", icon=utils.check_icon("MOD_VERTEX_WEIGHT"), text=op_text).param = "BIND_TO_BONES"
            row.enabled = edit_enabled

            column.separator()

            if chr_cache and not chr_cache.rigified and props.hair_rig_target == "CC4":
                is_accessory = characters.get_accessory_root(chr_cache, obj) is not None
                can_make_accessory = not chr_cache.rigified and edit_enabled and not is_accessory
                column.row().label(text = "For CC4 Accessory Only", icon="INFO")
                row = column.row()
                row.operator("cc3.hair", icon=utils.check_icon("CONSTRAINT_BONE"), text="Make Accessory").param = "MAKE_ACCESSORY"
                row.enabled = can_make_accessory
                column.separator()

            if chr_cache and arm and obj:
                rigified_spring_rig = False
                if chr_cache.rigified:
                    rigified_spring_rig = springbones.is_rigified(chr_cache, arm, chr_cache.available_spring_rigs)
                    if rigified_spring_rig is not None:
                        column.row().label(text="Rigify:", icon="OUTLINER_OB_ARMATURE")
                        row = column.row()
                        row.scale_y = 2
                        if rigified_spring_rig == True:
                            warn_icon(row)
                            row.operator("cc3.rigifier", icon="X", text="Remove Control Rig").param = "REMOVE_SPRING_RIG"
                        else:
                            row.operator("cc3.rigifier", icon="MOD_SCREW", text="Build Control Rig").param = "BUILD_SPRING_RIG"
                column.separator()
                build_allowed = True
                if chr_cache.rigified and not rigified_spring_rig:
                    build_allowed = False
                rigid_body_sim_ui(chr_cache, arm, obj, column, enabled=build_allowed)


class CC3HairPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Hair_Panel"
    bl_label = "Curve Hair (WIP)"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)

        # Blender Curve Hair

        if fake_drop_down(layout.box().row(),
                "Blender Curve Hair",
                "section_hair_blender_curve",
                props.section_hair_blender_curve):

            column = layout.column()
            column.box().label(text="Exporting", icon="EXPORT")
            column.row().operator("cc3.export_hair", icon=utils.check_icon("HAIR"), text="Export Hair")
            column.row().prop(props, "hair_export_group_by", expand=True)

            if not bpy.context.selected_objects:
                column.enabled = False

            column.separator()

            # Hair curve extraction
            column = layout.column()
            column.box().label(text="Extract Curves", icon="EXPORT")
            column.row().prop(props, "hair_curve_merge_loops", text="")
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

        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)
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
            has_key = chr_cache.get_import_has_key()

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

                        elif ui_row[0] == "WRINKLE_CONTROLS":
                            body_object = chr_cache.get_body()
                            if body_object and ("wrinkle_strength" in body_object or "wrinkle_curve" in body_object):
                                column.box().label(text= ui_row[1], icon=utils.check_icon(ui_row[2]))
                                row = column.row()
                                split = row.split(factor=0.5)
                                col_1 = row.column()
                                col_2 = row.column()
                                if "wrinkle_strength" in body_object:
                                    col_1.label(text="Strength")
                                    col_2.prop(body_object, "[\"wrinkle_strength\"]", text="", slider=True)
                                if "wrinkle_curve" in body_object:
                                    col_1.label(text="Curve")
                                    col_2.prop(body_object, "[\"wrinkle_curve\"]", text="", slider=True)

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
        if chr_cache and chr_cache.is_import_type("FBX"):
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

        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)
        missing_materials = characters.has_missing_materials(chr_cache)

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        width = get_layout_width(context, "UI")

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
                                          props.section_rigify_setup,
                                          icon="OUTLINER_OB_ARMATURE", icon_closed="OUTLINER_OB_ARMATURE"):

                    row = layout.row()
                    row.prop(chr_cache, "rig_mode", expand=True)

                    layout.separator()

                    if chr_cache.rigified:

                        if obj == chr_cache.rig_meta_rig:

                            layout.row().label(text="Re-rigify", icon="INFO")
                            row = layout.row()
                            row.operator("cc3.rigifier", icon="OUTLINER_OB_ARMATURE", text="Regenerate Rigify").param = "RE_RIGIFY_META"

                            layout.separator()

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

                    has_spring_rigs = springbones.has_spring_rigs(chr_cache, rig)
                    ik_fk = rigutils.get_rigify_ik_fk_influence(rig)

                    # utility widgets minipanel
                    box_row = layout.box().row(align=True)
                    is_full_rig_show = rigging.is_full_rigify_rig_shown(chr_cache)
                    box_row.operator("cc3.rigifier", icon="HIDE_OFF", text="", depress=is_full_rig_show).param = "TOGGLE_SHOW_FULL_RIG"
                    if has_spring_rigs:
                        is_base_rig_show = rigging.is_base_rig_shown(chr_cache)
                        box_row.operator("cc3.rigifier", icon="ARMATURE_DATA", text="", depress=is_base_rig_show).param = "TOGGLE_SHOW_BASE_RIG"
                        is_spring_rig_show = rigging.is_spring_rig_shown(chr_cache)
                        box_row.operator("cc3.rigifier", icon="FORCE_MAGNETIC", text="", depress=is_spring_rig_show).param = "TOGGLE_SHOW_SPRING_RIG"
                    is_pose_position = rigging.is_rig_rest_position(chr_cache)
                    box_row.operator("cc3.rigifier", icon="OUTLINER_OB_ARMATURE", text="", depress=is_pose_position).param = "TOGGLE_SHOW_RIG_POSE"
                    box_row.operator("cc3.rigifier", icon="LOOP_BACK", text="").param = "BUTTON_RESET_POSE"
                    box_row.separator()
                    depress = True if ik_fk > 0.995 else False
                    box_row.operator("cc3.rigifier", text="FK", depress=depress).param = "SET_LIMB_FK"
                    depress = True if ik_fk < 0.005 else False
                    box_row.operator("cc3.rigifier", text="IK", depress=depress).param = "SET_LIMB_IK"


                    if has_spring_rigs:

                        if fake_drop_down(layout.box().row(),
                                    "Spring Rigs",
                                    "section_rigify_spring",
                                    props.section_rigify_spring,
                                    icon="FORCE_MAGNETIC", icon_closed="FORCE_MAGNETIC"):

                            split = layout.split(factor=0.45)
                            col_1 = split.column()
                            col_2 = split.column()
                            col_1.label(text="Spring Rig")
                            col_2.prop(chr_cache, "available_spring_rigs", text="")

                            row = layout.row()
                            row.scale_y = 2
                            rigified_control_rig = springbones.is_rigified(chr_cache, rig, chr_cache.available_spring_rigs)
                            if rigified_control_rig:
                                warn_icon(row)
                                row.operator("cc3.rigifier", icon="X", text="Remove Control Rig").param = "REMOVE_SPRING_RIG"
                            else:
                                row.operator("cc3.rigifier", icon="MOD_SCREW", text="Build Control Rig").param = "BUILD_SPRING_RIG"

                            layout.separator()

                            rigid_body_sim_ui(chr_cache, rig, obj, layout, show_selector=False, enabled=rigified_control_rig)

                            layout.separator()

                    box_row = layout.box().row()
                    if fake_drop_down(box_row,
                                        "Rig Controls",
                                        "section_rigify_controls",
                                        props.section_rigify_controls,
                                        icon="TOOL_SETTINGS", icon_closed="TOOL_SETTINGS"):

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

                    box_row = layout.box().row()
                    if fake_drop_down(box_row,
                                        "Retargeting",
                                        "section_rigify_retarget",
                                        props.section_rigify_retarget,
                                        icon="ARMATURE_DATA", icon_closed="ARMATURE_DATA"):
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

                        if True:
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
                        col = layout.column(align=True)

                        row = col.row(align=True)
                        row.prop(prefs, "rigify_preview_retarget_fk_ik", expand=True)
                        row.prop(props, "retarget_preview_shape_keys", text="", toggle=True, icon="KEYINGSET")

                        row = col.row(align=True)
                        row.scale_y = 1.5
                        retarget_rig = chr_cache.rig_retarget_rig
                        if utils.object_exists_is_armature(retarget_rig):
                            depress = True
                            row.operator("cc3.rigifier", icon="X", text="Stop Preview", depress=depress).param = "RETARGET_CC_REMOVE_PAIR"
                        else:
                            depress = False
                            row.operator("cc3.rigifier", icon="HIDE_OFF", text="Preview Retarget", depress=depress).param = "RETARGET_CC_PAIR_RIGS"
                        row.enabled = source_type != "Unknown"

                        row = col.row()
                        row.scale_y = 2
                        row.operator("cc3.rigifier", icon="ANIM_DATA", text="Bake Retarget").param = "RETARGET_CC_BAKE_ACTION"
                        if source_type == "Unknown" and chr_cache.rig_retarget_rig is None:
                            row.enabled = False

                        layout.separator()

                        # retarget shape keys to character
                        row = layout.row()
                        row.operator("cc3.rigifier", icon="KEYINGSET", text="Retarget Shapekeys").param = "RETARGET_SHAPE_KEYS"
                        row.enabled = source_type != "Unknown"
                        layout.separator()

                    # NLA bake
                    box_row = layout.box().row()
                    if fake_drop_down(box_row,
                                        "NLA Bake",
                                        "section_rigify_nla_bake",
                                        props.section_rigify_nla_bake,
                                        icon="ANIM_DATA", icon_closed="ANIM_DATA"):
                        col = layout.column(align=True)
                        row = col.row(align=True)
                        row.prop(prefs, "rigify_bake_nla_fk_ik", expand=True)
                        row.prop(props, "bake_nla_shape_keys", text="", toggle=True, icon="KEYINGSET")
                        row = col.row()
                        row.scale_y = 2
                        row.operator("cc3.rigifier", icon="ANIM_DATA", text="Bake NLA").param = "NLA_CC_BAKE"
                        #row.enabled = chr_cache.rig_retarget_rig is None

                        layout.separator()

                    if fake_drop_down(layout.box().row(),
                                        "Export",
                                        "section_rigify_export",
                                        props.section_rigify_export,
                                        icon="EXPORT", icon_closed="EXPORT"):

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

            elif not chr_cache:

                reconnect_character_ui(context, layout, chr_cache)

        else:
            wrapped_text_box(layout, "Rigify add-on is not installed.", width, True)


class CC3SpringControlPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_SpringControl_Panel"
    bl_label = "Spring Rig Properties"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        layout = self.layout

        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)

        if not chr_cache or not chr_cache.rigified:
            return

        arm = chr_cache.get_armature()

        if not arm:
            return

        #box = layout.box()
        #box.label(text="Spring Rig Layers", icon="XRAY")
        layout.row().label(text="Spring Rig Layers:", icon="XRAY")
        row = layout.row()
        row.prop(arm.data, "layers", index = vars.SPRING_FK_LAYER, text="FK", toggle=True)
        row.prop(arm.data, "layers", index = vars.SPRING_IK_LAYER, text="IK", toggle=True)
        row.prop(arm.data, "layers", index = vars.SPRING_TWEAK_LAYER, text="Tweak", toggle=True)

        control_bone = None
        active_pose_bone = context.active_pose_bone
        single_chain_bone_name = None
        chain_group_bone_name = None
        if active_pose_bone:
            if active_pose_bone.name.endswith("_target_ik"):
                single_chain_bone_name = "MCH-" + active_pose_bone.name[:-10]
            elif active_pose_bone.name.endswith("_group_ik"):
                chain_group_bone_name = active_pose_bone.name[:-9]
            else:
                single_chain_bone_name = active_pose_bone.name

        parent_mode = None

        if single_chain_bone_name:
            if "ik_root" in active_pose_bone:
                search_bone_name = active_pose_bone["ik_root"]
            else:
                search_bone_name = active_pose_bone.name
            spring_rig_def, mch_root_name, parent_mode = springbones.get_spring_rig_from_child(chr_cache, arm, search_bone_name)
            prefix = springbones.get_spring_rig_prefix(parent_mode)
            rigid_body_sim = rigidbody.get_spring_rigid_body_system(arm, prefix)
            chain_name = single_chain_bone_name
            if chain_name.startswith("MCH-"):
                chain_name = chain_name[4:]
            if chain_name.endswith("_tweak"):
                chain_name = chain_name[:-6]
            if chain_name.endswith("_fk"):
                chain_name = chain_name[:-3]
            if chain_name.startswith("DEF-"):
                chain_name = chain_name[4:]
            if spring_rig_def and "IK_FK" in arm.pose.bones[mch_root_name]:
                control_bone = arm.pose.bones[mch_root_name]
                #box = layout.box()
                #box.label(text="Spring Chain", icon="LINKED")
                layout.row().label(text="Spring Chain:", icon="LINKED")
                if rigid_body_sim:
                    layout.prop(control_bone, "[\"SIM\"]", text=f"Simulation-FK ({chain_name})", slider=True)
                layout.prop(control_bone, "[\"IK_FK\"]", text=f"IK-FK ({chain_name})", slider=True)

            layout.separator()

        if chain_group_bone_name:

            spring_rig_def, mch_root_name, parent_mode = springbones.get_spring_rig_from_child(chr_cache, arm, active_pose_bone.name)
            prefix = springbones.get_spring_rig_prefix(parent_mode)
            rigid_body_sim = rigidbody.get_spring_rigid_body_system(arm, prefix)

            layout.row().label(text="Spring Chain Group:", icon="PROP_CON")
            group_name = active_pose_bone.name
            if group_name.endswith("_group_ik"):
                group_name = group_name[:-9]
            if group_name.startswith("DEF-"):
                group_name = group_name[4:]
            row = layout.row()
            row.operator("cc3.rigifier", icon="BACK", text="IK").param = "SPRING_GROUP_TO_IK"
            row.operator("cc3.rigifier", icon="FORWARD", text="FK").param = "SPRING_GROUP_TO_FK"
            if rigid_body_sim:
                row.operator("cc3.rigifier", icon="ANIM_DATA", text="SIM").param = "SPRING_GROUP_TO_SIM"

            layout.row().label(text="Spring Chains:", icon="LINKED")
            for child in active_pose_bone.children:
                if child.name.endswith("_target_ik"):
                    child_chain_bone_name = child.name[:-10]
                    if "ik_root" in child:
                        search_bone_name = child["ik_root"]
                    else:
                        search_bone_name = child.name
                    spring_rig_def, mch_root_name, parent_mode = springbones.get_spring_rig_from_child(chr_cache, arm, search_bone_name)
                    prefix = springbones.get_spring_rig_prefix(parent_mode)
                    rigid_body_sim = rigidbody.get_spring_rigid_body_system(arm, prefix)
                    chain_name = child_chain_bone_name
                    if spring_rig_def and "IK_FK" in arm.pose.bones[mch_root_name]:
                        control_bone = arm.pose.bones[mch_root_name]
                        if rigid_body_sim:
                            layout.prop(control_bone, "[\"SIM\"]", text=f"Simulation-FK ({chain_name})", slider=True)
                        layout.prop(control_bone, "[\"IK_FK\"]", text=f"IK-FK ({chain_name})", slider=True)
                        layout.separator()

        #if chr_cache and arm and obj:
        #    if springbones.has_spring_rigs(chr_cache, arm):
        #        build_allowed = True
        #        rigified_spring_rig = springbones.is_rigified(chr_cache, arm, parent_mode)
        #        if chr_cache.rigified and not rigified_spring_rig:
        #            build_allowed = False
        #        rigid_body_sim_ui(chr_cache, arm, obj, layout, True, parent_mode, enabled=build_allowed)


def scene_panel_draw(self : bpy.types.Panel, context : bpy.types.Context):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    layout = self.layout

    box = layout.box()
    box.label(text="Scene Lighting", icon="LIGHT")

    column = layout.column()
    grid = column.grid_flow(row_major=True, columns=2, align=True)
    grid.operator("cc3.scene", icon="SHADING_SOLID", text=" Matcap").param = "MATCAP"
    grid.operator("cc3.scene", icon="SHADING_TEXTURE", text="Default").param = "BLENDER"
    grid.operator("cc3.scene", icon="SHADING_TEXTURE", text="CC3").param = "CC3"
    grid.operator("cc3.scene", icon="SHADING_RENDERED", text="Studio").param = "STUDIO"
    grid.operator("cc3.scene", icon="SHADING_RENDERED", text="Courtyard").param = "COURTYARD"
    grid.operator("cc3.scene", icon="SHADING_RENDERED", text="Aqua").param = "AQUA"
    grid.operator("cc3.scene", icon="SHADING_RENDERED", text="Authority").param = "AUTHORITY"
    grid.operator("cc3.scene", icon="SHADING_RENDERED", text="Blur Warm").param = "BLUR_WARM"

    column.separator()

    box = layout.box()
    box.label(text="Scene, World & Compositor", icon="NODE_COMPOSITING")
    column = layout.column()

    op = column.operator("cc3.scene", icon="TRACKING", text="3 Point Tracking & Camera")
    op.param = "TEMPLATE"

    column.separator()

    chr_cache = props.get_context_character_cache(context)
    if chr_cache and bpy.context.scene.render.engine == 'CYCLES':
        box = layout.box()
        box.label(text="Cycles", icon="SHADING_RENDERED")
        column = layout.column()
        op = column.operator("cc3.scene", icon="PLAY", text="Cycles Setup")
        op.param = "CYCLES_SETUP"
        column.separator()

    cache_timeline_physics_ui(chr_cache, layout)

class CC3PipelineScenePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_PipelineScene_Panel"
    bl_label = "Scene Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PIPELINE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene_panel_draw(self, context)


class CC3CreateScenePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_CreateScene_Panel"
    bl_label = "Scene Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scene_panel_draw(self, context)


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
            chr_rig = utils.get_armature_from_objects(context.selected_objects)

        box = layout.box()
        box.label(text=f"Quick Export  ({vars.VERSION_STRING})", icon="EXPORT")
        column = layout.column(align=True)
        # export to CC3
        character_export_button(chr_cache, chr_rig, column, scale=1, warn=False)
        # export extras
        row1 = column.row(align=True)
        row1.operator("cc3.exporter", icon="MOD_CLOTH", text="Export Accessory").param = "EXPORT_ACCESSORY"
        row2 = column.row(align=True)
        row2.operator("cc3.exporter", icon="MESH_DATA", text="Export Replace Mesh").param = "EXPORT_MESH"
        if not utils.get_active_object():
            row1.enabled = False
            row2.enabled = False


class CC3ToolsPhysicsPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Physics_Panel"
    bl_label = "Cloth Physics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        layout = self.layout

        chr_cache = props.get_context_character_cache(context)
        obj = utils.get_context_mesh(context)
        obj_cache = None
        proxy = None
        is_proxy = False
        cloth_mod = None
        coll_mod = None
        if chr_cache and obj:
            obj, proxy, is_proxy = chr_cache.get_related_physics_objects(obj)
            obj_cache = chr_cache.get_object_cache(obj)
            cloth_mod = modifiers.get_cloth_physics_mod(obj)
            if proxy:
                coll_mod = modifiers.get_collision_physics_mod(proxy)
            else:
                coll_mod = modifiers.get_collision_physics_mod(obj)


        mat = utils.get_context_material(context)
        edit_mod, mix_mod = modifiers.get_material_weight_map_mods(obj, mat)

        column = layout.column()

        if chr_cache:
            column.box().label(text="Character Physics", icon="PHYSICS")
            row = column.row(align=True)
            row.prop(prefs, "physics_cloth_hair", text="Hair", toggle=True)
            row.prop(prefs, "physics_cloth_clothing", text="Clothing", toggle=True)
            if chr_cache.physics_applied:
                column.row().operator("cc3.setphysics", icon="REMOVE", text="Remove All Physics").param = "REMOVE_PHYSICS"
            else:
                column.row().operator("cc3.setphysics", icon="ADD", text="Apply All Physics").param = "APPLY_PHYSICS"
            if chr_cache.physics_disabled:
                column.row().operator("cc3.setphysics", icon="PLAY", text="Re-enable Physics").param = "ENABLE_PHYSICS"
            else:
                column.row().operator("cc3.setphysics", icon="PAUSE", text="Disable Physics").param = "DISABLE_PHYSICS"

        column.separator()

        # Cloth Physics Foldout
        #

        if not is_proxy:

            layout.box().label(text="Cloth Simulation", icon="MOD_CLOTH")

            column = layout.column()
            if not obj_cache:
                column.enabled = False

            row = column.row()
            row.scale_y = 2.0
            if cloth_mod:
                warn_icon(row, "REMOVE")
                row.operator("cc3.setphysics", text="Remove Cloth Physics").param = "PHYSICS_REMOVE_CLOTH"
            else:
                row.operator("cc3.setphysics", icon="ADD", text="Add Cloth Physics").param = "PHYSICS_ADD_CLOTH"

            column.separator()

            # Cloth Physics Settings
            if cloth_mod is not None:

                column = layout.column()
                if not obj_cache or cloth_mod is None:
                    column.enabled = False

                # Cloth Physics Presets
                sub_column = column.column(align=True)
                sub_column.row().label(text="Presets", icon="PRESET")
                sub_column.operator("cc3.setphysics", icon="USER", text="Hair").param = "PHYSICS_HAIR"
                grid = sub_column.grid_flow(columns=2, row_major=True, align=True)
                grid.operator("cc3.setphysics", icon="MATCLOTH", text="Denim").param = "PHYSICS_DENIM"
                grid.operator("cc3.setphysics", icon="MATCLOTH", text="Leather").param = "PHYSICS_LEATHER"
                grid.operator("cc3.setphysics", icon="MATCLOTH", text="Rubber").param = "PHYSICS_RUBBER"
                grid.operator("cc3.setphysics", icon="MATCLOTH", text="Linen").param = "PHYSICS_LINEN"
                grid.operator("cc3.setphysics", icon="MATCLOTH", text="Cotton").param = "PHYSICS_COTTON"
                grid.operator("cc3.setphysics", icon="MATCLOTH", text="Silk").param = "PHYSICS_SILK"


                column.separator()

                if fake_drop_down(column.row(),
                            "Cloth Settings",
                            "section_physics_cloth_settings",
                            props.section_physics_cloth_settings,
                            icon="OPTIONS", icon_closed="OPTIONS"):

                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Weight")
                    col_2.prop(cloth_mod.settings, "mass", text="", slider=True)
                    col_1.label(text="Air Damping")
                    col_2.prop(cloth_mod.settings, "air_damping", text="", slider=True)
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
                    col_1.label(text="Self Collision")
                    col_2.prop(cloth_mod.collision_settings, "use_self_collision", text="", slider=False)
                    if cloth_mod.collision_settings.use_self_collision:
                        col_1.label(text="Friction")
                        col_2.prop(cloth_mod.collision_settings, "self_friction", text="", slider=True)
                        col_1.label(text="Distance")
                        col_2.prop(cloth_mod.collision_settings, "self_distance_min", text="", slider=True)

                column.separator()

        # Cloth Collision Physics
        layout.box().label(text="Cloth Collision", icon="MOD_PHYSICS")

        column = layout.column()
        if not obj_cache:
            column.enabled = False

        if obj_cache and cloth_mod is None:
            if proxy:
                local_view = utils.is_local_view(context) and proxy is not None and proxy.visible_get()
                column.row().operator("cc3.setphysics", icon=utils.check_icon("HIDE_OFF"), text="Show Collision Proxy",
                                  depress=local_view).param = "TOGGLE_SHOW_PROXY"
            else:
                grid = column.grid_flow(columns=2, align=True)
                grid.prop(obj_cache, "use_collision_proxy", toggle=True, text="Use Proxy")
                grid.prop(obj_cache, "collision_proxy_decimate", text="Decimate", slider=True)

        row = column.row()
        row.scale_y = 2.0
        if coll_mod:
            warn_icon(row, "REMOVE")
            row.operator("cc3.setphysics", text="Remove Cloth Collision").param = "PHYSICS_REMOVE_COLLISION"
        else:
            row.operator("cc3.setphysics", icon="ADD", text="Add Cloth Collision").param = "PHYSICS_ADD_COLLISION"

        column.separator()

        # Collision Physics Settings
        if coll_mod is not None:

            if fake_drop_down(column.row(),
                              "Collision Settings",
                              "section_physics_collision_settings",
                              props.section_physics_collision_settings,
                              icon="OPTIONS", icon_closed="OPTIONS"):
                split = column.split(factor=0.5)
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

            column.separator()

        # Cache
        box = column.box()
        box.row().label(text="Cloth Physics Cache:", icon="PREVIEW_RANGE")

        has_cloth, cloth_baked, cloth_baking, cloth_point_cache = physics.cloth_physics_state(bpy.context.object)

        column.row().label(text="Animation Range:")
        row = column.row(align=True)
        row.prop(bpy.context.scene, "use_preview_range", text="", toggle=True)
        grid = row.grid_flow(columns=2, align=True)
        grid.operator("cc3.scene", icon="FULLSCREEN_ENTER", text="Expand").param = "ANIM_RANGE_EXPAND"
        grid.operator("cc3.scene", icon="FULLSCREEN_EXIT", text="Fit").param = "ANIM_RANGE_FIT"

        column.separator()

        column.row().label(text="Cloth Simulation:")
        if bpy.context.object:
            column.label(text=bpy.context.object.name, icon="OBJECT_DATA")

        row = column.row()
        row.operator("cc3.scene", icon=utils.check_icon("LOOP_BACK"), text="Reset Simulation").param = "PHYSICS_PREP_CLOTH"
        if not has_cloth:
            row.enabled = False
        row = column.row()
        row.scale_y = 1.5
        row.context_pointer_set("point_cache", cloth_point_cache)
        depress = cloth_baking
        row.alert = cloth_baked
        if cloth_baked:
            row.operator("ptcache.free_bake", text="Free Simulation", icon="REC")
        else:
            row.operator("ptcache.bake", text="Bake Simulation", icon="REC", depress=cloth_baking).bake = True
        if not has_cloth:
            row.enabled = False

        column.separator()


        # Physics Mesh Tools
        layout.box().label(text="Mesh Correction", icon="MESH_DATA")

        column = layout.column()
        if not obj:
            column.enabled = False

        column.operator("cc3.setphysics", icon="MOD_EDGESPLIT", text="Fix Degenerate Mesh").param = "PHYSICS_FIX_DEGENERATE"
        row = column.row()
        if obj and len(obj.material_slots) < 2:
                row.enabled = False
        row.operator("cc3.setphysics", icon="FACE_MAPS", text="Separate Physics Materials").param = "PHYSICS_SEPARATE"

        column.separator()

        # Weight Maps
        if not is_proxy:

            layout.box().label(text="Weight Maps", icon="TEXTURE_DATA")

            column = layout.column()

            split = column.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            if cloth_mod is None:
                col_1.enabled = False
                col_2.enabled = False
            col_1.label(text="WeightMap Size")
            col_2.prop(props, "physics_tex_size", text="")

            column = layout.column()
            if not cloth_mod or not obj_cache:
                column.enabled = False

            weight_map = None
            not_saved = False
            if obj and mat:
                weight_map : bpy.types.Image = physics.get_weight_map_from_modifiers(obj, mat)
                if weight_map:
                    not_saved = weight_map.is_dirty
            if weight_map:
                weight_map_size = int(props.physics_tex_size)
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Current Size:")
                col_2.label(text=f"{weight_map.size[0]} x {weight_map.size[1]}")
                row = column.row()
                row.operator("cc3.setphysics", icon="MOD_LENGTH", text="Resize Weightmap").param = "PHYSICS_RESIZE_WEIGHTMAP"
                if (weight_map and
                   (weight_map.size[0] != weight_map_size or weight_map.size[1] != weight_map_size) and
                    bpy.context.mode != "PAINT_TEXTURE"):
                    row.enabled = True
                else:
                    row.enabled = False

            if obj is not None:
                column.template_list("MATERIAL_UL_weightedmatslots", "", obj, "material_slots", obj, "active_material_index", rows=1)
            if edit_mod is not None:
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Influence")
                col_2.prop(mix_mod, "mask_constant", text="", slider=True)
            column.separator()
            if bpy.context.mode == "PAINT_TEXTURE":
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Strength")
                row = col_2.row()
                row.operator("cc3.setphysics", text="", icon='TRIA_LEFT').param = "PHYSICS_DEC_STRENGTH"
                row.prop(props, "physics_paint_strength", text="", slider=True)
                row.operator("cc3.setphysics", text="", icon='TRIA_RIGHT').param = "PHYSICS_INC_STRENGTH"
                row = column.row()
                row.scale_y = 2
                op = row.operator("cc3.setphysics", icon="CHECKMARK", text="Done Weight Painting!")
                op.param = "PHYSICS_DONE_PAINTING"
            else:
                if edit_mod is None:
                    row = column.row()
                    op = row.operator("cc3.setphysics", icon="ADD", text="Add Weight Map")
                    op.param = "PHYSICS_ADD_WEIGHTMAP"
                else:
                    row = column.row()
                    op = row.operator("cc3.setphysics", icon="REMOVE", text="Remove Weight Map")
                    op.param = "PHYSICS_REMOVE_WEIGHTMAP"
                column = layout.column()
                if edit_mod is None:
                    column.enabled = False
                op = column.operator("cc3.setphysics", icon="BRUSH_DATA", text="Paint Weight Map")
                op.param = "PHYSICS_PAINT"
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                r1 = col_1.row(align=True)
                r1.operator("cc3.setphysics", icon="FILEBROWSER", text="").param = "BROWSE_WEIGHTMAP"
                r2 = r1.row()
                r2.alert = not_saved
                r2.operator("cc3.setphysics", icon="FILE_TICK", text="Save").param = "PHYSICS_SAVE"
                col_2.operator("cc3.setphysics", icon="ERROR", text="Delete").param = "PHYSICS_DELETE"


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

        target_cache = None
        if chr_cache and len(bpy.context.selected_objects) >= 2:
            for obj in bpy.context.selected_objects:
                target_cache = props.get_character_cache(obj, None)
                if target_cache != chr_cache:
                    break
                else:
                    target_cache = None

        detail_body = None
        sculpt_body = None
        detail_sculpting = False
        body_sculpting = False
        if chr_cache:
            detail_body = chr_cache.get_detail_body()
            sculpt_body = chr_cache.get_sculpt_body()
            if detail_body:
                if utils.get_active_object() == detail_body and utils.get_mode() == "SCULPT":
                    detail_sculpting = True
                if detail_body.visible_get():
                    detail_sculpting = True
            if sculpt_body:
                if utils.get_active_object() == sculpt_body and utils.get_mode() == "SCULPT":
                    body_sculpting = True
        has_body_overlay = sculpting.has_overlay_nodes(sculpt_body, sculpting.LAYER_TARGET_SCULPT)
        has_detail_overlay = sculpting.has_overlay_nodes(detail_body, sculpting.LAYER_TARGET_DETAIL)

        valid_character = True
        if not chr_cache:
            row = layout.row()
            row.alert = True
            row.label(icon="ERROR", text="Invalid Character")
            valid_character = False
        elif not chr_cache.is_standard():
            row = layout.row()
            row.alert = True
            row.label(icon="ERROR", text="Unusupported Character")
            valid_character = False

        # Full Body Sculpting

        row = layout.row()
        row.scale_y = 1.5
        row.prop(props, "sculpt_layer_tab", expand=True)

        column = layout.column()
        column.enabled = valid_character

        #if fake_drop_down(layout.box().row(), "Full Body Sculpting", "section_sculpt_body",
        #                  props.section_sculpt_body, icon = "OUTLINER_OB_ARMATURE"):
        if props.sculpt_layer_tab == "BODY":

            if fake_drop_down(column.box().row(), "Body Sculpting", "section_sculpt_setup",
                              props.section_sculpt_setup,
                              icon="OUTLINER_OB_ARMATURE", icon_closed="OUTLINER_OB_ARMATURE"):

                if not chr_cache or detail_sculpting:
                    column.enabled = False

                row = column.row()
                split = row.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text = "Multi-res Level")
                col_2.prop(prefs, "sculpt_multires_level", slider=True)
                if body_sculpting:
                    row.enabled = False

                row = column.row()
                if not sculpt_body:
                    row.scale_y = 2
                    row.operator("cc3.sculpting", icon="SCULPTMODE_HLT", text="Setup Body Sculpt").param = "BODY_SETUP"
                elif not body_sculpting:
                    row.scale_y = 2
                    row.operator("cc3.sculpting", icon="SCULPTMODE_HLT", text="Resume Body Sculpt").param = "BODY_BEGIN"
                else:
                    row.scale_y = 2
                    row.operator("cc3.sculpting", icon="PLAY_REVERSE", text="Stop Body Sculpt").param = "BODY_END"

                column.separator()

                column.row().label(text="Bake Settings:")
                column.separator()

                row = column.row()
                split = row.split(factor=0.4)
                col_1 = split.column()
                col_2 = split.column()
                col_1.prop(prefs, "bake_use_gpu", text="GPU", toggle=True)
                col_2.prop(prefs, "body_normal_bake_size", text = "")

                row = column.row(align=True)
                row.scale_y = 1.5
                row.operator("cc3.sculpting", icon="RESTRICT_RENDER_OFF", text="Bake").param = "BODY_BAKE"
                if chr_cache:
                    row.prop(chr_cache, "multires_bake_apply", text="", toggle=True, icon="MESH_ICOSPHERE")
                if not sculpt_body:
                    row.enabled = False

                column.separator()

                column.row().label(text="Layer Settings:")
                column.separator()

                grid = column.grid_flow(row_major=True, columns=2, align=True)
                if chr_cache:
                    grid.prop(chr_cache, "body_normal_strength", text="Nrm", slider=True)
                    grid.prop(chr_cache, "body_ao_strength", text="AO", slider=True)
                    grid.prop(chr_cache, "body_mix_mode", text="")
                    grid.prop(chr_cache, "body_normal_definition", text="Def", slider=True)
                if not has_body_overlay:
                    grid.enabled = False

                column.separator()

                row = column.row()
                row.scale_y = 1.5
                row.operator("cc3.sculpt_export", icon="EXPORT", text="Export Layer").param = "BODY_SKINGEN"
                if not sculpt_body or not has_body_overlay:
                    row.enabled = False

                column.separator()

        # Detail Sculpting

        #if fake_drop_down(layout.box().row(), "Detail Sculpting", "section_sculpt_detail",
        #                  props.section_sculpt_detail, icon = "POSE_HLT"):
        elif props.sculpt_layer_tab == "DETAIL":

            if fake_drop_down(column.box().row(), "Detail Sculpting", "section_sculpt_setup",
                              props.section_sculpt_setup,
                              icon="MESH_MONKEY", icon_closed="MESH_MONKEY"):

                if not chr_cache or body_sculpting:
                    column.enabled = False

                row = column.row()
                row.prop(prefs, "detail_sculpt_sub_target", expand=True)
                if detail_body or detail_sculpting:
                    row.enabled = False

                row = column.row()
                split = row.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text = "Multi-res Level")
                col_2.prop(prefs, "detail_multires_level", slider=True)
                if detail_body or detail_sculpting:
                    row.enabled = False

                row = column.row()
                row.scale_y = 2.0
                if not detail_body:
                    row.operator("cc3.sculpting", icon="SCULPTMODE_HLT", text="Setup Detail Sculpt").param = "DETAIL_SETUP"
                elif not detail_sculpting:
                    row.operator("cc3.sculpting", icon="SCULPTMODE_HLT", text="Resume Detail Sculpt").param = "DETAIL_BEGIN"
                else:
                    row.operator("cc3.sculpting", icon="PLAY_REVERSE", text="Stop Detail Sculpt").param = "DETAIL_END"

                column.separator()

                column.row().label(text="Bake Settings:")
                column.separator()

                row = column.row()
                split = row.split(factor=0.4)
                col_1 = split.column()
                col_2 = split.column()
                col_1.prop(prefs, "bake_use_gpu", text="GPU", toggle=True)
                col_2.prop(prefs, "detail_normal_bake_size", text="")

                row1 = column.row()
                row1.scale_y = 1.5
                row1.operator("cc3.sculpting", icon="RESTRICT_RENDER_OFF", text="Bake").param = "DETAIL_BAKE"
                if not detail_body:
                    row1.enabled = False

                column.separator()

                column.row().label(text="Layer Settings:")
                column.separator()

                grid = column.grid_flow(row_major=True, columns=2, align=True)
                if chr_cache:
                    grid.prop(chr_cache, "detail_normal_strength", text="Nrm", slider=True)
                    grid.prop(chr_cache, "detail_ao_strength", text="AO", slider=True)
                    grid.prop(chr_cache, "detail_mix_mode", text="")
                    grid.prop(chr_cache, "detail_normal_definition", text="Def", slider=True)
                if not has_detail_overlay:
                    grid.enabled = False

                column.separator()

                row = column.row()
                row.scale_y = 1.5
                row.operator("cc3.sculpt_export", icon="EXPORT", text="Export Layer").param = "DETAIL_SKINGEN"
                if not detail_body or not has_detail_overlay:
                    row.enabled = False

                column.separator()

        # Tools

        if fake_drop_down(layout.box().row(), "Tools", "section_sculpt_cleanup",
                          props.section_sculpt_cleanup, icon = "BRUSH_DATA"):
            column = layout.column()
            if not chr_cache:
                column.enabled = False

            column.separator()

            column.row().operator("cc3.sculpting", icon="FORWARD", text="TODO: Sync Source Shape").param = "UPDATE_SHAPE"
            column.row().operator("cc3.sculpting", icon="FORWARD", text="TODO: Reset Base Shapes").param = "RESET_SHAPE"

            column.separator()

            column.label(text="Remove Sculpts:")

            column.separator()

            row = column.row()
            warn_icon(row)
            if not sculpt_body:
                row.enabled = False
            row.operator("cc3.sculpting", icon="TRASH", text="Remove Body Sculpt").param = "BODY_CLEAN"

            row = column.row()
            warn_icon(row)
            if not detail_body:
                row.enabled = False
            row.operator("cc3.sculpting", icon="TRASH", text="Remove Detail Sculpt").param = "DETAIL_CLEAN"

            column.separator()

            column.label(text="Geometry Transfer:")

            column.separator()

            column.row().prop(props, "geom_transfer_layer", expand=True)
            if props.geom_transfer_layer == "SHAPE_KEY":
                column.row().prop(props, "geom_transfer_layer_name")

            row = column.row()
            row.operator("cc3.transfer_character", icon="OUTLINER_OB_ARMATURE", text="Transfer Character")
            if not (target_cache and chr_cache):
                row.enabled = False

            column = layout.column()
            row = column.row()
            row.operator("cc3.transfer_mesh", icon="MESH_ICOSPHERE", text="Transfer Mesh")
            if not bpy.context.active_object or len(bpy.context.selected_objects) < 2:
                row.enabled = False


class CC3ToolsUtilityPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Utility_Panel"
    bl_label = "Utilities"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("cc3.character", icon="MATERIAL", text="Match Materials").param = "MATCH_MATERIALS"


class CCICDataLinkPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_DataLink_Panel"
    bl_label = "Data Link (WIP)"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = LINK_TAB_NAME
    #bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        link_props = bpy.context.scene.CCICLinkProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        layout = self.layout
        chr_cache = props.get_context_character_cache(context)

        link_service = link.get_link_service()
        connected = link_service and link_service.is_connected
        listening = link_service and link_service.is_listening
        connecting = link_service and link_service.is_connecting
        is_cc = link_props.remote_app == "Character Creator"
        is_iclone = link_props.remote_app == "iClone"

        column = layout.column()
        column.prop(link_props, "link_host", text="Host")
        column.prop(link_props, "link_target", text="Target")
        if listening or connected:
            column.enabled = False

        layout.separator()
        row = layout.row()
        row.prop(link_props, "link_status", text="")
        row.enabled = False

        column = layout.column(align=True)
        row = column.row(align=True)
        text = "Connect"
        depressed = False
        row.scale_y = 2
        param = "START"
        if connected:
            row.alert = True
            text = "Linked"
            param = "DISCONNECT"
        elif connecting:
            row.alert = False
            depressed = True
            text = "Connecting..."
        elif listening:
            row.alert = False
            depressed = True
            text = "Listening..."
        row.operator("ccic.datalink", icon="LINKED", text=text, depress=depressed).param = param
        if connected or connecting:
            row.operator("ccic.datalink", icon="X", text="").param = "STOP"

        # Datalink prefs
        box = layout.box()
        if fake_drop_down(box.row(), "Data-Link Options", "show_data_link_prefs", props.show_data_link_prefs,
                          icon="PREFERENCES", icon_closed="PREFERENCES"):
            split = box.split(factor=0.9)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Auto-Start Connection")
            col_2.prop(link_props, "link_auto_start", text="")
            col_1.label(text="Preview Frame Sync")
            col_2.prop(link_props, "sequence_frame_sync", text="")
            col_1.label(text="Preview Shape Keys")
            col_2.prop(link_props, "sequence_preview_shape_keys", text="")
            col_1.label(text="Match Client Rate")
            col_2.prop(link_props, "match_client_rate", text="")

        if True:

            row = layout.row()
            text = ""
            if is_cc:
                text = "Character Creator"
            elif is_iclone:
                text = "iClone"
            else:
                text = "Not connected..."
            if (is_cc or is_iclone) and not connected:
                text += " (Disconnected)"
            row.label(text=text)
            row.operator("ccic.datalink", icon="FILE_FOLDER", text="").param = "SHOW_PROJECT_FILES"

            col = layout.column(align=True)
            grid = col.grid_flow(row_major=True, columns=2, align=True)
            grid.scale_y = 2.0
            grid.operator("ccic.datalink", icon="ARMATURE_DATA", text="Pose").param = "SEND_POSE"
            grid.operator("ccic.datalink", icon="PLAY", text="Sequence").param = "SEND_ANIM"
            # can't set the preview camera transform in CC4...
            #grid.operator("ccic.datalink", icon="CAMERA_DATA", text="Sync Camera").param = "SYNC_CAMERA"

            if is_cc and chr_cache and (chr_cache.get_import_has_key() or chr_cache.is_non_standard()):
                grid = col.grid_flow(row_major=True, columns=1, align=True)
                grid.scale_y = 2.0
                if chr_cache.is_morph():
                    grid.operator("ccic.datalink", icon="MESH_ICOSPHERE", text="Go CC").param = "SEND_MORPH"
                else:
                    grid.operator("ccic.datalink", icon="COMMUNITY", text="Go CC").param = "SEND_ACTOR"


            #grid.operator("ccic.datalink", icon="ARMATURE_DATA", text="TEST").param = "TEST"

        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)
        if chr_cache:
            row = layout.row()
            row.label(text=f"link id: {chr_cache.link_id}")
            row.operator("ccic.datalink", icon="FILE_FOLDER", text="").param = "SHOW_ACTOR_FILES"


class CCICProportionPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Proportion_Panel"
    bl_label = "Proportion Edit"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CREATE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        layout = self.layout
        chr_cache = props.get_context_character_cache(context)

        if chr_cache:
            row = layout.row()
            row.scale_y = 2.0
            if chr_cache.proportion_editing:
                row.operator("ccic.characterproportions", icon="ARMATURE_DATA", text="Apply Proportions", depress=True).param = "END"
            else:
                row.operator("ccic.characterproportions", icon="ARMATURE_DATA", text="Edit Proportions").param = "BEGIN"

        if chr_cache and utils.get_mode() == "POSE":
            pose_bone = bpy.context.active_pose_bone
            box = layout.box()
            box.label(text=pose_bone.name, icon="BONE_DATA")
            inherit_scale = None
            for child_bone in pose_bone.children:
                bone_name = child_bone.name
                if "ShareBone" in bone_name or ("Twist" in bone_name and "NeckTwist" not in bone_name):
                    continue
                if inherit_scale is None:
                    inherit_scale = child_bone.bone.inherit_scale
                elif inherit_scale != child_bone.bone.inherit_scale:
                    inherit_scale = "MIXED"
                    break
            box.label(text=f"Child Bones Inherit Scale:")
            grid = box.grid_flow(row_major=True, columns=2, align=True)
            grid.operator("ccic.characterproportions", text="Full", depress=True if inherit_scale=="FULL" else False).param = "INHERIT_SCALE_FULL"
            grid.operator("ccic.characterproportions", text="Average", depress=True if inherit_scale=="AVERAGE" else False).param = "INHERIT_SCALE_AVERAGE"
            grid.operator("ccic.characterproportions", text="Shear", depress=True if inherit_scale=="FIX_SHEAR" else False).param = "INHERIT_SCALE_FIX_SHEAR"
            grid.operator("ccic.characterproportions", text="Aligned", depress=True if inherit_scale=="ALIGNED" else False).param = "INHERIT_SCALE_ALIGNED"
            grid.operator("ccic.characterproportions", text="None", depress=True if inherit_scale=="NONE" else False).param = "INHERIT_SCALE_NONE"
            grid.operator("ccic.characterproportions", text="Legacy", depress=True if inherit_scale=="NONE_LEGACY" else False).param = "INHERIT_SCALE_NONE_LEGACY"
            row = layout.row()
            row.scale_y = 1.5
            row.operator("ccic.characterproportions", text="Reset All").param = "RESET"








class CC3ToolsPipelineImportPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Pipeline_Import_Panel"
    bl_label = "Import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PIPELINE_TAB_NAME

    def draw(self, context):
        global debug_counter
        PROPS = bpy.context.scene.CC3ImportProps
        PREFS = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        addon_updater_ops.check_for_update_background()
        if addon_updater_ops.updater.update_ready == True:
            addon_updater_ops.update_notice_box_ui(self, context)

        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)

        if chr_cache:
            character_name = chr_cache.character_name
        else:
            character_name = "No Character"

        chr_rig = None

        if chr_cache:
            chr_rig = chr_cache.get_armature()
        else:
            if context.selected_objects:
                chr_rig = utils.get_armature_from_objects(context.selected_objects)
            elif context.object:
                chr_rig = utils.get_armature_from_object(context.object)
            if chr_rig:
                character_name = chr_rig.name

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        box = layout.box()
        box.label(text=f"Settings  ({vars.VERSION_STRING})", icon="TOOL_SETTINGS")

        grid = layout.grid_flow(columns=2, align=True)
        grid.prop(PROPS, "lighting_mode", toggle=True, text="Lighting")
        grid.prop(PROPS, "physics_mode", toggle=True, text="Physics")
        grid.prop(PROPS, "wrinkle_mode", toggle=True, text="Wrinkles")
        grid.prop(PROPS, "rigify_mode", toggle=True, text="Rigify")

        # Build prefs in title
        box = layout.box()
        if fake_drop_down(box.row(), "Importing", "show_build_prefs", PROPS.show_build_prefs,
                          icon="IMPORT", icon_closed="IMPORT"):
            split = box.split(factor=0.9)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="De-duplicate Materials")
            col_2.prop(PREFS, "import_deduplicate", text="")
            col_1.label(text="Auto Convert Generic")
            col_2.prop(PREFS, "import_auto_convert", text="")
            col_1.label(text="Limit Textures")
            col_2.prop(PREFS, "build_limit_textures", text="")
            col_1.label(text="Pack Texture Channels")
            col_2.prop(PREFS, "build_pack_texture_channels", text="")
            col_1.label(text="Reuse Channel Packs")
            col_2.prop(PREFS, "build_reuse_baked_channel_packs", text="")
            col_1.label(text="Use Edit Modifier")
            col_2.prop(PREFS, "build_armature_edit_modifier", text="")
            col_1.label(text="Use Preserve Volume")
            col_2.prop(PREFS, "build_armature_preserve_volume", text="")
            col_1.label(text="Clothing Physics")
            col_2.prop(PREFS, "physics_cloth_clothing", text="")
            col_1.label(text="Hair Cloth Physics")
            col_2.prop(PREFS, "physics_cloth_hair", text="")
            col_1.label(text="Dual Specular Skin")
            col_2.prop(PREFS, "build_skin_shader_dual_spec", text="")
            col_1.separator()
            col_2.separator()
            col_1.label(text="Shape Keys Drive Jaw Bone")
            col_2.prop(PREFS, "build_shape_key_bone_drivers_jaw", text="")
            col_1.label(text="Shape Keys Drive Eye Bones")
            col_2.prop(PREFS, "build_shape_key_bone_drivers_eyes", text="")
            col_1.label(text="Shape Keys Drive Head Bone")
            col_2.prop(PREFS, "build_shape_key_bone_drivers_head", text="")
            col_1.separator()
            col_2.separator()
            col_1.label(text="Body Shape Keys Drive All")
            col_2.prop(PREFS, "build_body_key_drivers", text="")

        row = layout.row()
        row.scale_y = 2
        op = row.operator("cc3.importer", icon="OUTLINER_OB_ARMATURE", text="Import Character")
        op.param = "IMPORT"
        row = layout.row()
        row.scale_y = 2
        op = row.operator("cc3.anim_importer", icon="ARMATURE_DATA", text="Import Animations")

        if chr_cache and chr_cache.rigified:
            export_label = "Exporting (Rigify)"
        else:
            export_label = "Exporting"

        # reconnect and link character
        reconnect_character_ui(context, layout, chr_cache)

        # clean up
        box = layout.box()
        box.label(text="Clean Up", icon="TRASH")

        box = layout.row()
        box.label(text = "Character: " + character_name)
        row = layout.row()
        warn_icon(row)
        if not chr_cache:
            row.enabled = False
        row.operator("cc3.importer", icon="REMOVE", text="Remove Character").param ="DELETE_CHARACTER"


class CC3ToolsPipelineExportPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Pipeline_Export_Panel"
    bl_label = "Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PIPELINE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        global debug_counter
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        addon_updater_ops.check_for_update_background()
        if addon_updater_ops.updater.update_ready == True:
            addon_updater_ops.update_notice_box_ui(self, context)

        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)

        if chr_cache:
            character_name = chr_cache.character_name
        else:
            character_name = "No Character"

        chr_rig = None

        if chr_cache:
            chr_rig = chr_cache.get_armature()
        else:
            if context.selected_objects:
                chr_rig = utils.get_armature_from_objects(context.selected_objects)
            elif context.object:
                chr_rig = utils.get_armature_from_object(context.object)
            if chr_rig:
                character_name = chr_rig.name

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        if chr_cache and chr_cache.rigified:
            export_label = "Exporting (Rigify)"
        else:
            export_label = "Exporting"

        # export prefs in box title
        box = layout.box()
        if fake_drop_down(box.row(),
                export_label,
                "export_options",
                props.export_options, icon="EXPORT", icon_closed="EXPORT"):
            box.row().prop(prefs, "export_json_changes", expand=True)
            box.row().prop(prefs, "export_texture_changes", expand=True)
            if prefs.export_texture_changes:
                box.row().prop(prefs, "export_bake_nodes", expand=True)
                if prefs.export_bake_nodes:
                    box.row().prop(prefs, "export_bake_bump_to_normal", expand=True)
            box.row().prop(prefs, "export_bone_roll_fix", expand=True)
            box.row().prop(prefs, "export_revert_names", expand=True)

        if chr_cache and chr_cache.rigified:
            rigify_export_group(chr_cache, layout)
        else:
            pipeline_export_group(chr_cache, chr_rig, layout)

        layout.separator()

        # export extras
        layout.row().operator("cc3.exporter", icon="MOD_CLOTH", text="Export Accessory").param = "EXPORT_ACCESSORY"
        layout.row().operator("cc3.exporter", icon="MESH_DATA", text="Export Replace Mesh").param = "EXPORT_MESH"






#################################################
# BAKE TOOL PANELS


class CCICBakePanel(bpy.types.Panel):
    bl_idname = "CCIC_PT_Bake_Panel"
    bl_label = "Export Bake"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = PIPELINE_TAB_NAME
    bl_options = {"DEFAULT_CLOSED"}

    def draw_size_props(self, context, props, bake_maps, col_1, col_2):

        if props.target_mode == "UNITY_HDRP":
            col_1.label(text="Diffuse Size")
            col_2.prop(props, "diffuse_size", text="")
            col_1.label(text="Mask Size")
            col_2.prop(props, "mask_size", text="")
            col_1.label(text="Detail Size")
            col_2.prop(props, "detail_size", text="")
            col_1.label(text="Normal Size")
            col_2.prop(props, "normal_size", text="")
            col_1.separator()
            col_2.separator()
            col_1.label(text="Emission Size")
            col_2.prop(props, "emissive_size", text="")
            col_1.label(text="SSS Size")
            col_2.prop(props, "sss_size", text="")
            col_1.label(text="Transmission Size")
            col_2.prop(props, "thickness_size", text="")

        else:
            if "Diffuse" in bake_maps:
                col_1.label(text="Diffuse Size")
                col_2.prop(props, "diffuse_size", text="")
            if "AO" in bake_maps:
                col_1.label(text="AO Size")
                col_2.prop(props, "ao_size", text="")
            if "Subsurface" in bake_maps:
                col_1.label(text="SSS Size")
                col_2.prop(props, "sss_size", text="")
            if "Thickness" in bake_maps:
                col_1.label(text="Thickness Size")
                col_2.prop(props, "thickness_size", text="")
            if "Metallic" in bake_maps:
                col_1.label(text="Metallic Size")
                col_2.prop(props, "metallic_size", text="")
            if "Specular" in bake_maps:
                col_1.label(text="Specular Size")
                col_2.prop(props, "specular_size", text="")
            if "Roughness" in bake_maps:
                col_1.label(text="Roughness Size")
                col_2.prop(props, "roughness_size", text="")
            if "Emission" in bake_maps:
                col_1.label(text="Emission Size")
                col_2.prop(props, "emissive_size", text="")
            if "Alpha" in bake_maps:
                col_1.label(text="Alpha Size")
                col_2.prop(props, "alpha_size", text="")
            if "Transmission" in bake_maps:
                col_1.label(text="Transmission Size")
                col_2.prop(props, "transmission_size", text="")
            if "Normal" in bake_maps:
                col_1.label(text="Normal Size")
                col_2.prop(props, "normal_size", text="")
            if "Bump" in bake_maps:
                col_1.label(text="Bump Size")
                col_2.prop(props, "bump_size", text="")
            if "MicroNormal" in bake_maps:
                col_1.label(text="Micro Normal Size")
                col_2.prop(props, "micronormal_size", text="")
            if "MicroNormalMask" in bake_maps:
                col_1.label(text="Micro Normal Mask Size")
                col_2.prop(props, "micronormalmask_size", text="")

    def draw(self, context):
        props = bpy.context.scene.CCICBakeProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        addon_updater_ops.check_for_update_background()
        if addon_updater_ops.updater.update_ready == True:
            addon_updater_ops.update_notice_box_ui(self, context)

        box = layout.box()
        box.label(text=f"Export Bake Settings", icon="TOOL_SETTINGS")

        bake_maps = vars.get_bake_target_maps(props.target_mode)

        split = layout.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text="Target")
        col_2.prop(props, "target_mode", text="", slider = True)
        col_1.label(text="Bake Samples")

        crow = col_2.row(align=True)
        crow.prop(props, "bake_samples", text="", slider = True)
        crow.prop(prefs, "bake_use_gpu", text="GPU", toggle=True)

        col_1.label(text="Format")
        col_2.prop(props, "target_format", text="", slider = True)
        if props.target_format == "JPEG":
            col_1.label(text="JPEG Quality")
            col_2.prop(props, "jpeg_quality", text="", slider = True)
        if props.target_format == "PNG":
            col_1.label(text="PNG Compression")
            col_2.prop(props, "png_compression", text="", slider = True)
        col_1.label(text="Max Size")
        col_2.prop(props, "max_size", text="")
        col_1.label(text="Bake Mixers")
        col_2.prop(props, "bake_mixers", text="")
        if "Bump" in bake_maps:
            col_1.label(text="Allow Bump Maps")
            col_2.prop(props, "allow_bump_maps", text="")
        if "AO" in bake_maps:
            col_1.label(text="AO in Diffuse")
            col_2.prop(props, "ao_in_diffuse", text="", slider = True)
        if props.target_mode == "UNITY_HDRP" or props.target_mode == "UNITY_URP":
            col_1.label(text="Smoothness Mapping")
            col_2.prop(props, "smoothness_mapping", text="")
        if props.target_mode == "GLTF":
            col_1.label(text="Pack GLTF")
            col_2.prop(props, "pack_gltf", text="")
        col_1.label(text="Bake Folder")
        col_2.prop(props, "bake_path", text="")
        col_1.separator()
        col_2.separator()

        col_1.label(text="Max Sizes By Type")
        col_2.prop(props, "custom_sizes", text="")

        obj = context.object
        mat = utils.get_context_material(context)
        bake_cache = bake.get_export_bake_cache(mat)

        if props.custom_sizes:

            layout.row().box().label(text = "Maximum Texture Sizes")

            split = layout.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()

            self.draw_size_props(context, props, bake_maps, col_1, col_2)

            if obj is not None:
                row = layout.row()
                row.template_list("MATERIAL_UL_weightedmatslots", "", obj, "material_slots", obj, "active_material_index", rows=1)

            if bake_cache and bake_cache.source_material != mat:
                mat_settings = bake.get_material_bake_settings(bake_cache.source_material)
                row = layout.row()
                row.label(text = "(*Source Material Settings)")
            else:
                mat_settings = bake.get_material_bake_settings(mat)

            if mat_settings is not None:
                row = layout.row()
                row.operator("ccic.bakesettings", icon="REMOVE", text="Remove Material Settings").param = "REMOVE"

                split = layout.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()

                self.draw_size_props(context, mat_settings, bake_maps, col_1, col_2)

            else:
                row = layout.row()
                row.operator("ccic.bakesettings", icon="ADD", text="Add Material Settings").param = "ADD"

        if bake_cache:
            if bake_cache.source_material == mat:
                row = layout.row()
                row.operator("ccic.bakesettings", icon="LOOP_FORWARDS", text="Restore Baked Materials").param = "BAKED"
            elif bake_cache.baked_material == mat:
                row = layout.row()
                row.operator("ccic.bakesettings", icon="LOOP_BACK", text="Revert Source Materials").param = "SOURCE"

        valid_bake_path = False
        if os.path.isabs(props.bake_path) or bpy.data.is_saved:
            valid_bake_path = True

        layout.box().label(text="Select objects to bake", icon="INFO")

        row = layout.row()
        row.scale_y = 2
        row.operator("ccic.baker", icon="PLAY", text="Bake").param = "BAKE"
        if not valid_bake_path:
            row.enabled = False
            box = layout.box()
            box.alert = True
            box.label(text="Warning:", icon="ERROR")
            box.label(text="SAVE Blend file before baking")
            box.label(text="or use absolute bake path!")

        layout.separator()

        layout.box().label(text="Utils", icon="INFO")

        row = layout.row()
        row.scale_y = 1
        row.operator("ccic.jpegify", icon="PLAY", text="Jpegify")

