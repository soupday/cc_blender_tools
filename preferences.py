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

from . import addon_updater_ops


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



    physics_group: bpy.props.StringProperty(default="CC_Physics", name="Physics Vertex Group Prefix")

    refractive_eyes: bpy.props.EnumProperty(items=[
                        ("PARALLAX","Parallax","Approximatated Parallax Refraction in a single cornea material which is not subject to Eevee limitations on Subsurface scattering and receiving shadows."),
                        ("SSR","SSR","Screen Space Refraction with a transmissive & transparent cornea material over an opaque eye (iris) material. SSR Materials do not receive full shadows and cannot have Subsurface scattering in Eevee."),
                    ], default="PARALLAX", name = "Refractive Eyes")

    #refractive_eyes: bpy.props.BoolProperty(default=True, name="Refractive Eyes", description="Generate refractive eyes with iris depth and pupil scale parameters")
    eye_displacement_group: bpy.props.StringProperty(default="CC_Eye_Displacement", name="Eye Displacement Group", description="Eye Iris displacement vertex group name")


    max_texture_size: bpy.props.FloatProperty(default=4096, min=512, max=4096)

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
        layout.label(text="Physics:")
        layout.prop(self, "physics")
        layout.prop(self, "physics_group")
        layout.label(text="Debug Settings:")
        layout.prop(self, "log_level")
        op = layout.operator("cc3.setmaterials", icon="FILE_REFRESH", text="Reset to Defaults")
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
