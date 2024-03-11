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
from mathutils import Vector

from . import addon_updater_ops, colorspace, utils, vars

def reset_preferences():
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    prefs.render_target = "EEVEE"
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
    prefs.export_revert_names = True
    prefs.cycles_sss_skin_v203 = 0.5
    prefs.cycles_sss_hair_v203 = 0.1
    prefs.cycles_sss_teeth_v203 = 1.0
    prefs.cycles_sss_tongue_v203 = 1.0
    prefs.cycles_sss_eyes_v203 = 1.0
    prefs.cycles_sss_default_v203 = 1.0
    prefs.cycles_ssr_iris_brightness = 2.0
    prefs.import_auto_convert = True
    prefs.import_deduplicate = True
    prefs.build_pack_texture_channels = False
    prefs.build_pack_wrinkle_diffuse_roughness = False
    prefs.build_reuse_baked_channel_packs = True
    prefs.build_limit_textures = False
    prefs.build_skin_shader_dual_spec = False
    prefs.build_shape_key_bone_drivers_jaw = False
    prefs.build_shape_key_bone_drivers_eyes = False
    prefs.build_shape_key_bone_drivers_head = False
    prefs.build_body_key_drivers = False
    prefs.bake_use_gpu = False
    prefs.build_armature_edit_modifier = True
    prefs.build_armature_preserve_volume = False
    prefs.physics_weightmap_curve = 5.0


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
                        ("DETAILS","Details","All including details."),
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
    export_revert_names: bpy.props.BoolProperty(default=True, name="Revert names", description="Revert object and material names to match their original names from the source Json.")
    export_unity_mode: bpy.props.EnumProperty(items=[
                        ("BLEND","Blend File","Save the project as a blend file in a Unity project. All textures and folders will be copied to the new location and made relative to the blend file."),
                        ("FBX","FBX","Export the character as an .Fbx file to the specified location. All textures and folders will be copied."),
                    ], default="BLEND", name = "Unity Export")
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

    detail_sculpt_sub_target: bpy.props.EnumProperty(items=[
                        ("HEAD","Head","Sculpt on the head only"),
                        ("BODY","Body","Sculpt on the body only"),
                        ("ALL","All","Sculpt the entire body"),
                    ], default="HEAD", name = "Sculpt Target")

    detail_multires_level: bpy.props.IntProperty(default=4, min = 1, max = 6, name="Level",
                                                 description="Starting multi-resolution level for detail sculpting")
    sculpt_multires_level: bpy.props.IntProperty(default=2, min = 1, max = 6, name="Level",
                                                 description="Starting multi-resolution level for body sculpting")

    detail_normal_bake_size: bpy.props.EnumProperty(items=vars.ENUM_TEX_LIST, default="4096", description="Resolution of detail sculpt normals to bake")
    body_normal_bake_size: bpy.props.EnumProperty(items=vars.ENUM_TEX_LIST, default="2048", description="Resolution of full body sculpt normals to bake")

    aces_srgb_override: bpy.props.EnumProperty(items=colorspace.fetch_all_color_spaces, default=0, description="ACES Color space to override for sRGB textures")
    aces_data_override: bpy.props.EnumProperty(items=colorspace.fetch_data_color_spaces, default=0, description="ACES Color space to override for Non-Color or Linear textures")

    #refractive_eyes: bpy.props.BoolProperty(default=True, name="Refractive Eyes", description="Generate refractive eyes with iris depth and pupil scale parameters")
    eye_displacement_group: bpy.props.StringProperty(default="CC_Eye_Displacement", name="Eye Displacement Group", description="Eye Iris displacement vertex group name")

    build_limit_textures: bpy.props.BoolProperty(default=False, name="Limit Textures",
                description="Attempt to limit the number of imported textures to 8 or less. This is to attempt to address problems with OSX hardware limitations allowing only 8 active textures in a material.\n"
                            "Note: This will mean the head material will be simpler than intended and no wrinkle map system is possible. "
                            "Also this will force on texture channel packing to reduce textures on all materials, which will slow down imports significantly")
    build_pack_texture_channels: bpy.props.BoolProperty(default=False, name="Pack Texture Channels",
                description="Pack compatible linear texture channels to reduce texture lookups.\n\n"
                            "Note: This will significantly increase import time.\n\n"
                            "Note: Wrinkle map textures are always channel packed to reduce texture load")
    build_pack_wrinkle_diffuse_roughness: bpy.props.BoolProperty(default=False, name="Wrinkle Maps into Diffuse Alpha",
                description="Packs wrinkle map roughness channels into the diffuse alpha channels. This will free up one more texture slot in the skin head material")
    build_reuse_baked_channel_packs: bpy.props.BoolProperty(default=True, name="Reuse Channel Packs",
                description="Reuse existing channel packs on material rebuild, otherwise rebake the texture channel packs")


    build_armature_edit_modifier: bpy.props.BoolProperty(default=True, name="Use Edit Modifier",
                                                         description="Automatically set to use armature modifier in mesh edit mode for all armature modifiers in the character. (i.e. edit in place)")
    build_armature_preserve_volume: bpy.props.BoolProperty(default=False, name="Preserve Volume",
                                                         description="Automatically set use preserve volume for all armature modifiers in the character.")
    build_skin_shader_dual_spec: bpy.props.BoolProperty(default=False, name="Dual Specular Skin",
                                                         description="Use a dual specular skin shader arrangement.")
    build_shape_key_bone_drivers_jaw: bpy.props.BoolProperty(default=True, name="Shape Keys Drive Jaw Bone",
                                                         description="Add drivers to the jaw bone from facial expression shape keys.")
    build_shape_key_bone_drivers_eyes: bpy.props.BoolProperty(default=True, name="Shape Keys Drive Eye Bones",
                                                         description="Add drivers to the eye bones from facial expression shape keys.")
    build_shape_key_bone_drivers_head: bpy.props.BoolProperty(default=False, name="Shape Keys Drive Head Bone",
                                                         description="Add drivers to the head bone from facial expression shape keys.")
    build_body_key_drivers: bpy.props.BoolProperty(default=True, name="Body Shape Keys Drive All",
                                                         description="Add drivers so that all shape keys on the character are driven by the body shape keys. " \
                                                                     "(So that only the body shape keys need to be animated or controlled)")

    max_texture_size: bpy.props.FloatProperty(default=4096, min=512, max=4096)

    import_deduplicate: bpy.props.BoolProperty(default=True, name="De-duplicate Materials",
                description="Detects and re-uses duplicate textures and consolidates materials with same name, textures and parameters into a single material")
    import_auto_convert: bpy.props.BoolProperty(default=True, name="Auto Convert Generic",
                description="When importing generic characters (GLTF, GLB, VRM or OBJ) automatically convert to Reallusion Non-Standard characters or props."
                "Which sets up Reallusion import compatible materials and material parameters")

    cycles_ssr_iris_brightness: bpy.props.FloatProperty(default=2.0, min=0, max=4, description="Iris brightness mulitplier when rendering SSR eyes in Cycles")
    #
    cycles_sss_skin_v203: bpy.props.FloatProperty(default=0.5)
    cycles_sss_hair_v203: bpy.props.FloatProperty(default=0.1)
    cycles_sss_teeth_v203: bpy.props.FloatProperty(default=1.0)
    cycles_sss_tongue_v203: bpy.props.FloatProperty(default=1.0)
    cycles_sss_eyes_v203: bpy.props.FloatProperty(default=1.0)
    cycles_sss_default_v203: bpy.props.FloatProperty(default=1.0)
    # old
    cycles_sss_skin_v118: bpy.props.FloatProperty(default=0.5)
    cycles_sss_hair_v118: bpy.props.FloatProperty(default=0.1)
    cycles_sss_teeth: bpy.props.FloatProperty(default=1.0)
    cycles_sss_tongue: bpy.props.FloatProperty(default=1.0)
    cycles_sss_eyes: bpy.props.FloatProperty(default=1.0)
    cycles_sss_default: bpy.props.FloatProperty(default=1.0)
    # older
    cycles_sss_skin: bpy.props.FloatProperty(default=0.2)
    cycles_sss_hair: bpy.props.FloatProperty(default=0.05)

    bake_use_gpu: bpy.props.BoolProperty(default=False, description="Bake on the GPU for faster more accurate baking.", name="GPU Bake")

    physics_cloth_hair: bpy.props.BoolProperty(default=True, description="Set up cloth physics on the hair objects.", name="Hair Cloth Physics")
    physics_cloth_clothing: bpy.props.BoolProperty(default=True, description="Set up cloth physics on the clothing and accessory objects.", name="Clothing Cloth Physics")
    physics_weightmap_curve: bpy.props.FloatProperty(default=5.0, min=1.0, max=10.0, name="Physics Weightmap Curve",
                                                     description="Power curve used to convert PhysX weightmaps to blender vertex pin weights.")

    # rigify prefs
    rigify_preview_retarget_fk_ik: bpy.props.EnumProperty(items=[
                        ("FK","FK","Retarget to FK controls only"),
                        ("IK","IK","Retarget to IK controls only"),
                        ("BOTH","Both","Retarget to both FK and IK controls"),
                    ], default="BOTH", name = "Retarget to FK/IK")
    rigify_bake_nla_fk_ik: bpy.props.EnumProperty(items=[
                        ("FK","FK","Bake FK controls only"),
                        ("IK","IK","Bake IK controls only"),
                        ("BOTH","Both","Bake both FK and IK and controls"),
                    ], default="BOTH", name = "Bake NLA to FK/IK")

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

        layout.label(text="Import:")
        layout.prop(self, "import_deduplicate")
        layout.prop(self, "import_auto_convert")
        layout.prop(self, "build_limit_textures")
        layout.prop(self, "build_pack_texture_channels")
        layout.prop(self, "build_pack_wrinkle_diffuse_roughness")
        layout.prop(self, "build_armature_edit_modifier")
        layout.prop(self, "build_armature_preserve_volume")
        layout.prop(self, "build_skin_shader_dual_spec")
        layout.separator()
        layout.prop(self, "build_shape_key_bone_drivers_jaw")
        layout.prop(self, "build_shape_key_bone_drivers_eyes")
        layout.prop(self, "build_shape_key_bone_drivers_head")
        layout.prop(self, "build_body_key_drivers")

        layout.label(text="Rendering:")
        layout.prop(self, "render_target")
        layout.prop(self, "bake_use_gpu")

        if colorspace.is_aces():
            layout.label(text="OpenColorIO ACES")
            layout.prop(self, "aces_srgb_override")
            layout.prop(self, "aces_data_override")

        layout.label(text="Material settings:")
        layout.prop(self, "quality_mode")
        layout.prop(self, "pipeline_mode")
        layout.prop(self, "morph_mode")

        layout.label(text="Lighting:")
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
        layout.prop(self, "cycles_sss_skin_v203")
        layout.prop(self, "cycles_sss_hair_v203")
        layout.prop(self, "cycles_sss_teeth_v203")
        layout.prop(self, "cycles_sss_tongue_v203")
        layout.prop(self, "cycles_sss_eyes_v203")
        layout.prop(self, "cycles_sss_default_v203")
        layout.prop(self, "cycles_ssr_iris_brightness")

        layout.label(text="Physics:")
        layout.prop(self, "physics_group")
        layout.prop(self, "physics_weightmap_curve")

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
