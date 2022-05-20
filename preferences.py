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

from . import addon_updater_ops, utils, vars


def reset_preferences():
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    prefs.render_target = "EEVEE"
    prefs.lighting = "ENABLED"
    prefs.physics = "ENABLED"
    prefs.quality_lighting = "CC3"
    prefs.pipeline_lighting = "CC3"
    prefs.morph_lighting = "MATCAP"
    prefs.quality_mode = "ADVANCED"
    prefs.pipeline_mode = "ADVANCED"
    prefs.morph_mode = "ADVANCED"
    prefs.log_level = "ERRORS"
    prefs.hair_hint = "hair,scalp,beard,mustache,sideburns,ponytail,braid,!bow,!band,!tie,!ribbon,!ring,!butterfly,!flower"
    prefs.hair_scalp_hint = "scalp,base,skullcap"
    prefs.debug_mode = False
    prefs.physics_group = "CC_Physics"
    prefs.refractive_eyes = "PARALLAX"
    prefs.eye_displacement_group = "CC_Eye_Displacement"
    prefs.max_texture_size = 4096
    prefs.export_json_changes = True
    prefs.export_texture_changes = True
    prefs.export_bone_roll_fix = False
    prefs.export_bake_nodes = False
    prefs.export_bake_bump_to_normal = True
    prefs.export_unity_remove_objects = True
    prefs.export_texture_size = "2048"
    prefs.export_require_key = True
    prefs.cycles_sss_skin_v118 = 0.35
    prefs.cycles_sss_hair_v118 = 0.025
    prefs.cycles_sss_teeth = 0.1
    prefs.cycles_sss_tongue = 0.1
    prefs.cycles_sss_eyes = 0.025
    prefs.cycles_sss_default = 0.1
    prefs.cycles_ssr_iris_brightness = 2.0


class CC3OperatorPreferences(bpy.types.Operator):
    """CC3 Preferences Functions"""
    bl_idname = "cc3.setpreferences"
    bl_label = "CC3 Preferences Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):

        if self.param == "RESET_PREFS":
            reset_preferences()

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "RESET_PREFS":
            return "Reset preferences to defaults"
        return ""


class CC3ToolsAddonPreferences(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__.partition(".")[0]

    lighting: bpy.props.EnumProperty(items=[
                        ("DISABLED","Disabled","No automatic lighting and render settings."),
                        ("ENABLED","Enabled","Allows automatic lighting and render settings."),
                    ], default="ENABLED", name = "Automatic Lighting")

    physics: bpy.props.EnumProperty(items=[
                        ("DISABLED","Disabled","No physics auto setup."),
                        ("ENABLED","Enabled","Allows automatic physics setup from physX weight maps."),
                    ], default="ENABLED", name = "Generate Physics")

    quality_lighting: bpy.props.EnumProperty(items=[
                        ("BLENDER","Blender Default","Blenders default lighting setup"),
                        ("MATCAP","Solid Matcap","Solid shading matcap lighting for sculpting / mesh editing"),
                        ("CC3","CC3 Default","Replica of CC3 default lighting setup"),
                        ("STUDIO","Studio Right","Right facing 3 point lighting with the studio hdri"),
                        ("COURTYARD","Courtyard Left","Left facing soft 3 point lighting with the courtyard hdri"),
                    ], default="CC3", name = "Render / Quality Lighting")

    pipeline_lighting: bpy.props.EnumProperty(items=[
                        ("BLENDER","Blender Default","Blenders default lighting setup"),
                        ("MATCAP","Solid Matcap","Solid shading matcap lighting for sculpting / mesh editing"),
                        ("CC3","CC3 Default","Replica of CC3 default lighting setup"),
                        ("STUDIO","Studio Right","Right facing 3 point lighting with the studio hdri"),
                        ("COURTYARD","Courtyard Left","Left facing soft 3 point lighting with the courtyard hdri"),
                    ], default="CC3", name = "(FBX) Accessory Editing Lighting")

    morph_lighting: bpy.props.EnumProperty(items=[
                        ("BLENDER","Blender Default","Blenders default lighting setup"),
                        ("MATCAP","Solid Matcap","Solid shading matcap lighting for sculpting / mesh editing"),
                        ("CC3","CC3 Default","Replica of CC3 default lighting setup"),
                        ("STUDIO","Studio Right","Right facing 3 point lighting with the studio hdri"),
                        ("COURTYARD","Courtyard Left","Left facing soft 3 point lighting with the courtyard hdri"),
                    ], default="MATCAP", name = "(OBJ) Morph Edit Lighting")

    quality_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic Materials","Build basic PBR materials for quality / rendering"),
                        ("ADVANCED","Advanced Materials","Build advanced materials for quality / rendering"),
                    ], default="ADVANCED", name = "Render / Quality Material Mode")

    # = accessory_mode
    pipeline_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic Materials","Build basic PBR materials for character morph / accessory editing"),
                        ("ADVANCED","Advanced Materials","Build advanced materials for character morph / accessory editing"),
                    ], default="ADVANCED", name = "Accessory Material Mode")

    morph_mode: bpy.props.EnumProperty(items=[
                        ("BASIC","Basic Materials","Build basic PBR materials for character morph / accessory editing"),
                        ("ADVANCED","Advanced Materials","Build advanced materials for character morph / accessory editing"),
                    ], default="ADVANCED", name = "Character Morph Material Mode")

    log_level: bpy.props.EnumProperty(items=[
                        ("ALL","All","Log everything to console."),
                        ("WARN","Warnings & Errors","Log warnings and error messages to console."),
                        ("ERRORS","Just Errors","Log only errors to console."),
                    ], default="ERRORS", name = "(Debug) Log Level")

    render_target: bpy.props.EnumProperty(items=[
                        ("EEVEE","Eevee","Build shaders for Eevee rendering."),
                        ("CYCLES","Cycles","Build shaders for Cycles rendering."),
                    ], default="EEVEE", name = "Target Renderer")

    hair_hint: bpy.props.StringProperty(default="hair,scalp,beard,mustache,sideburns,ponytail,braid,!bow,!band,!tie,!ribbon,!ring,!butterfly,!flower", name="Hair detection keywords")
    hair_scalp_hint: bpy.props.StringProperty(default="scalp,base,skullcap", name="Scalp detection keywords")

    debug_mode: bpy.props.BoolProperty(default=False)

    export_require_key: bpy.props.BoolProperty(default=True, name="Export Require Key", description="Ensure that exports back to CC3 have a valid Fbx/Obj Key file")

    export_json_changes: bpy.props.BoolProperty(default=True, name="Material parameters", description="Export all material and shader parameter changes to the character Json data. Setting to False keeps original material and shader parameters.")
    export_texture_changes: bpy.props.BoolProperty(default=True, name="Textures", description="Export all texture changes to the character Json data. Setting to False keeps original textures.")
    export_bone_roll_fix: bpy.props.BoolProperty(default=False, name="Teeth bone fix", description="(Experimental) Apply zero roll to upper and lower teeth bones to fix teeth alignment problems re-importing to CC3")
    export_bake_nodes: bpy.props.BoolProperty(default=True, name="Bake custom nodes", description="(Very Experimental) Bake any custom nodes (non texture image) attached to shader texture map sockets on export.")
    export_bake_bump_to_normal: bpy.props.BoolProperty(default=True, name="Combine normals", description="(Very Experimental) When both a bump map and a normal is present, bake the bump map into the normal. (CC3 materials can only have one, normal map or bump map.)")
    export_unity_remove_objects: bpy.props.BoolProperty(default=True, name="Unity: Remove non-character objects.", description="Removes all objects not attached to the character, when exporting to Unity.")
    export_unity_mode: bpy.props.EnumProperty(items=[
                        ("BLEND","Blend File","Save the project as a blend file in a Unity project. All textures and folders will be copied to the new location and made relative to the blend file."),
                        ("FBX","FBX","Export the character as an .Fbx file to the specified location. All textures and folders will be copied."),
                    ], default="BLEND", name = "Unity Export")
    export_animation_mode: bpy.props.EnumProperty(items=[
                        ("ACTIONS","Actions", "Export all applicable actions with the character"),
                        ("STRIPS","Strips", "Export only Unity actions via NLA strips"),
                        ("BOTH","Both","Export both actions and NLA strips"),
                    ], default="STRIPS", name = "Animation Export")
    export_non_standard_mode: bpy.props.EnumProperty(items=[
                        ("HUMANOID","Humanoid","Export the selected armature and objects as a humanoid .Fbx file, with generated .json data for import into CC4 (Only)"),
                        ("CREATURE","Creature","Export the selected armature and objects as a creature .Fbx file, with generated .json data for import into CC4 (Only)"),
                        ("PROP","Prop","Export the selected objects as a prop .Fbx file, with generated .json data for import into CC4 (Only)"),
                    ], default="HUMANOID", name = "Non-standard Export")
    export_texture_size: bpy.props.EnumProperty(items=vars.ENUM_TEX_LIST, default="2048", description="Size of procedurally generated textures to bake")

    physics_group: bpy.props.StringProperty(default="CC_Physics", name="Physics Vertex Group Prefix")

    refractive_eyes: bpy.props.EnumProperty(items=[
                        ("PARALLAX","Parallax Eye","(Experimental) Approximatated Parallax Refraction in a single cornea material which is not subject to Eevee limitations on Subsurface scattering and receiving shadows."),
                        ("SSR","SSR Eye","Screen Space Refraction with a transmissive & transparent cornea material over an opaque eye (iris) material. SSR Materials do not receive full shadows and cannot have Subsurface scattering in Eevee."),
                    ], default="SSR", name = "Refractive Eyes")

    #refractive_eyes: bpy.props.BoolProperty(default=True, name="Refractive Eyes", description="Generate refractive eyes with iris depth and pupil scale parameters")
    eye_displacement_group: bpy.props.StringProperty(default="CC_Eye_Displacement", name="Eye Displacement Group", description="Eye Iris displacement vertex group name")


    max_texture_size: bpy.props.FloatProperty(default=4096, min=512, max=4096)


    cycles_sss_skin_v118: bpy.props.FloatProperty(default=0.35)
    cycles_sss_hair_v118: bpy.props.FloatProperty(default=0.025)
    cycles_sss_teeth: bpy.props.FloatProperty(default=0.1)
    cycles_sss_tongue: bpy.props.FloatProperty(default=0.1)
    cycles_sss_eyes: bpy.props.FloatProperty(default=0.025)
    cycles_sss_default: bpy.props.FloatProperty(default=0.1)
    cycles_ssr_iris_brightness: bpy.props.FloatProperty(default=2.0, min=0, max=4, description="Iris brightness mulitplier when rendering SSR eyes in Cycles.")
    # old
    cycles_sss_skin: bpy.props.FloatProperty(default=0.2)
    cycles_sss_hair: bpy.props.FloatProperty(default=0.05)

    # addon updater preferences

    auto_check_update: bpy.props.BoolProperty(
	    name="Auto-check for Update",
	    description="If enabled, auto-check for updates using an interval",
	    default=False,
	    )
    updater_intrval_months: bpy.props.IntProperty(
		name='Months',
		description="Number of months between checking for updates",
		default=0,
		min=0
		)
    updater_intrval_days: bpy.props.IntProperty(
		name='Days',
		description="Number of days between checking for updates",
		default=7,
		min=0,
		max=31
		)
    updater_intrval_hours: bpy.props.IntProperty(
		name='Hours',
		description="Number of hours between checking for updates",
		default=0,
		min=0,
		max=23
		)
    updater_intrval_minutes: bpy.props.IntProperty(
		name='Minutes',
		description="Number of minutes between checking for updates",
		default=0,
		min=0,
		max=59
		)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.label(text="Rendering:")
        layout.prop(self, "render_target")

        layout.label(text="Material settings:")
        layout.prop(self, "quality_mode")
        layout.prop(self, "pipeline_mode")
        layout.prop(self, "morph_mode")

        layout.label(text="Lighting:")
        layout.prop(self, "lighting")
        if self.lighting == "ENABLED":
            layout.prop(self, "quality_lighting")
            layout.prop(self, "pipeline_lighting")
            layout.prop(self, "morph_lighting")

        layout.label(text="Detection:")
        layout.prop(self, "hair_hint")
        layout.prop(self, "hair_scalp_hint")

        layout.label(text="Eyes:")
        layout.prop(self, "refractive_eyes")
        layout.prop(self, "eye_displacement_group")

        layout.label(text="Cycles Adjustments:")
        layout.prop(self, "cycles_sss_skin_v118")
        layout.prop(self, "cycles_sss_hair_v118")
        layout.prop(self, "cycles_sss_teeth")
        layout.prop(self, "cycles_sss_tongue")
        layout.prop(self, "cycles_sss_eyes")
        layout.prop(self, "cycles_sss_default")
        layout.prop(self, "cycles_ssr_iris_brightness")

        layout.label(text="Physics:")
        layout.prop(self, "physics")
        layout.prop(self, "physics_group")

        layout.label(text="Export:")
        layout.prop(self, "export_json_changes")
        layout.prop(self, "export_texture_changes")
        layout.prop(self, "export_bone_roll_fix")
        layout.prop(self, "export_bake_nodes")
        layout.prop(self, "export_bake_bump_to_normal")
        layout.prop(self, "export_unity_remove_objects")
        layout.prop(self, "export_texture_size")
        layout.prop(self, "export_require_key")

        layout.label(text="Debug Settings:")
        layout.prop(self, "log_level")
        op = layout.operator("cc3.setpreferences", icon="FILE_REFRESH", text="Reset to Defaults")
        op.param = "RESET_PREFS"

        addon_updater_ops.update_settings_ui(self,context)

class MATERIAL_UL_weightedmatslots(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        slot = item
        ma = slot.material
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if ma:
                layout.prop(ma, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
