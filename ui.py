import bpy

from .physics import *
from .utils import *
from .vars import *

debug_counter = 0

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
    bl_label = "CC3 Material Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"

    def draw(self, context):
        layout = self.layout

        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        mesh_in_selection = False
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                mesh_in_selection = True
                break

        if fake_drop_down(layout.box().row(),
                "1. Import Details",
                "stage1",
                props.stage1):
            box = layout.box()
            #op = box.operator("cc3.importer", icon="IMPORT", text="Import Character")
            #op.param ="IMPORT"
            # import details
            if props.import_file != "" or len(props.import_objects) > 0:
                box.label(text="Name: " + props.import_name)
                box.label(text="Type: " + props.import_type.upper())
                if props.import_haskey:
                    box.label(text="Key File: Yes")
                else:
                    box.label(text="Key File: No")

                split = layout.split(factor=0.05)
                col_1 = split.column()
                col_2 = split.column()
                box = col_2.box()
                if fake_drop_down(box.row(), "Import Details", "stage1_details", props.stage1_details):
                    if props.import_file != "":
                        box.prop(props, "import_file", text="")
                    if len(props.import_objects) > 0:
                        for p in props.import_objects:
                            if p.object is not None:
                                box.prop(p, "object", text="")
            else:
                box.label(text="No Character")

        layout.separator()
        if fake_drop_down(layout.box().row(),
                "2. Build Materials",
                "stage2",
                props.stage2):
            layout.prop(props, "setup_mode", expand=True)
            layout.prop(props, "blend_mode", expand=True)
            layout.prop(props, "build_mode", expand=True)
            layout.separator()
            split = layout.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Hair Hint")
            col_2.prop(props, "hair_hint", text="")
            col_1.label(text="Scalp Hint")
            col_2.prop(props, "hair_scalp_hint", text="")
            if props.hair_object is None:
                col_1.label(text="** Hair Object **")
            else:
                col_1.label(text="Hair Object")
            col_2.prop_search(props, "hair_object",  context.scene, "objects", text="")
            col_1.separator()
            col_2.separator()
            if props.import_file != "":
                box = layout.box()
                if props.setup_mode == "ADVANCED":
                    text = "Build Advanced Materials"
                elif props.setup_mode == "COMPAT":
                    text = "Build Compatible Materials"
                else:
                    text = "Build Basic Materials"
                op = box.operator("cc3.importer", icon="MATERIAL", text=text)
                op.param ="BUILD"

        layout.separator()
        if fake_drop_down(layout.box().row(),
                "3. Fix Alpha Blending",
                "stage3",
                props.stage3):
            column = layout.column()
            if not mesh_in_selection:
                column.enabled = False

            ob = context.object
            if ob is not None:
                column.template_list("MATERIAL_UL_weightedmatslots", "", ob, "material_slots", ob, "active_material_index", rows=1)
            split = column.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Quick Set Alpha")
            col_1.prop(props, "quick_set_mode", expand=True)
            op = col_2.operator("cc3.quickset", icon="SHADING_SOLID", text="Opaque")
            op.param = "OPAQUE"
            op = col_2.operator("cc3.quickset", icon="SHADING_WIRE", text="Blend")
            op.param = "BLEND"
            op = col_2.operator("cc3.quickset", icon="SHADING_RENDERED", text="Hashed")
            op.param = "HASHED"
            col_1.separator()
            col_2.separator()
            op = col_1.operator("cc3.quickset", icon="NORMALS_FACE", text="Single Sided")
            op.param = "SINGLE_SIDED"
            op = col_2.operator("cc3.quickset", icon="XRAY", text="Double Sided")
            op.param = "DOUBLE_SIDED"


        layout.separator()
        if fake_drop_down(layout.box().row(),
                "4. Adjust Parameters",
                "stage4",
                props.stage4):
            column = layout.column()
            if props.import_name == "":
                column.enabled = False

            row = column.row()
            row.prop(props, "update_mode", expand=True)
            if props.setup_mode == "ADVANCED":
                # Skin Settings
                column.separator()
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                if props.update_mode == "UPDATE_ALL":
                    col_1.label(text="Update All")
                else:
                    col_1.label(text="Update Selected")
                op = col_2.operator("cc3.quickset", icon="FILE_REFRESH", text="Update")
                op.param = props.update_mode
                column.separator()
                if fake_drop_down(column.row(),
                        "Skin Parameters",
                        "skin_toggle",
                        props.skin_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Skin AO")
                    col_2.prop(props, "skin_ao", text="", slider=True)
                    col_1.label(text="Skin Color Blend")
                    col_2.prop(props, "skin_blend", text="", slider=True)
                    col_1.label(text="Skin Normal Blend")
                    col_2.prop(props, "skin_normal_blend", text="", slider=True)
                    col_1.label(text="*Skin Roughness")
                    col_2.prop(props, "skin_roughness", text="", slider=True)
                    col_1.label(text="Skin Specular")
                    col_2.prop(props, "skin_specular", text="", slider=True)
                    col_1.label(text="Skin SSS Radius")
                    col_2.prop(props, "skin_sss_radius", text="", slider=True)
                    col_1.label(text="Skin SSS Faloff")
                    col_2.prop(props, "skin_sss_falloff", text="")
                    col_1.label(text="Head Micro Normal")
                    col_2.prop(props, "skin_head_micronormal", text="", slider=True)
                    col_1.label(text="Body Micro Normal")
                    col_2.prop(props, "skin_body_micronormal", text="", slider=True)
                    col_1.label(text="Arm Micro Normal")
                    col_2.prop(props, "skin_arm_micronormal", text="", slider=True)
                    col_1.label(text="Leg Micro Normal")
                    col_2.prop(props, "skin_leg_micronormal", text="", slider=True)
                    col_1.label(text="Head MNormal Tiling")
                    col_2.prop(props, "skin_head_tiling", text="", slider=True)
                    col_1.label(text="Body MNormal Tiling")
                    col_2.prop(props, "skin_body_tiling", text="", slider=True)
                    col_1.label(text="Arm MNormal Tiling")
                    col_2.prop(props, "skin_arm_tiling", text="", slider=True)
                    col_1.label(text="Leg MNormal Tiling")
                    col_2.prop(props, "skin_leg_tiling", text="", slider=True)
                    col_1.label(text="Mouth AO")
                    col_2.prop(props, "skin_mouth_ao", text="", slider=True)
                    col_1.label(text="Nostril AO")
                    col_2.prop(props, "skin_nostril_ao", text="", slider=True)
                    col_1.label(text="Lips AO")
                    col_2.prop(props, "skin_lips_ao", text="", slider=True)

                # Eye settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Eye Parameters",
                        "eye_toggle",
                        props.eye_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Eye AO")
                    col_2.prop(props, "eye_ao", text="", slider=True)
                    col_1.label(text="Eye Color Blend")
                    col_2.prop(props, "eye_blend", text="", slider=True)
                    col_1.label(text="Eye Specular")
                    col_2.prop(props, "eye_specular", text="", slider=True)
                    col_1.label(text="Iris Roughness")
                    col_2.prop(props, "eye_iris_roughness", text="", slider=True)
                    col_1.label(text="Sclera Roughness")
                    col_2.prop(props, "eye_sclera_roughness", text="", slider=True)
                    col_1.label(text="Iris Scale")
                    col_2.prop(props, "eye_iris_scale", text="", slider=True)
                    col_1.label(text="Sclera Scale")
                    col_2.prop(props, "eye_sclera_scale", text="", slider=True)
                    col_1.label(text="*Iris Mask Radius")
                    col_2.prop(props, "eye_iris_radius", text="", slider=True)
                    col_1.label(text="*Iris Mask Hardness")
                    col_2.prop(props, "eye_iris_hardness", text="", slider=True)
                    col_1.label(text="SS Radius (cm)")
                    col_2.prop(props, "eye_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Faloff")
                    col_2.prop(props, "eye_sss_falloff", text="")
                    col_1.label(text="Sclera Normal Flatten")
                    col_2.prop(props, "eye_sclera_normal", text="", slider=True)
                    col_1.label(text="Sclera Normal Tiling")
                    col_2.prop(props, "eye_sclera_tiling", text="", slider=True)
                    col_1.label(text="Shadow Radius")
                    col_2.prop(props, "eye_shadow_radius", text="", slider=True)
                    col_1.label(text="Shadow Hardness")
                    col_2.prop(props, "eye_shadow_hardness", text="", slider=True)
                    col_1.label(text="Shadow Color")
                    col_2.prop(props, "eye_shadow_color", text="")
                    col_1.label(text="Eye Occlusion")
                    col_2.prop(props, "eye_occlusion", text="", slider=True)
                    col_1.label(text="*Tearline Alpha")
                    col_2.prop(props, "eye_tearline_alpha", text="", slider=True)
                    col_1.label(text="*Tearline Roughness")
                    col_2.prop(props, "eye_tearline_roughness", text="", slider=True)
                    col_1.label(text="Sclera Brightness")
                    col_2.prop(props, "eye_sclera_brightness", text="", slider=True)
                    col_1.label(text="Iris Brightness")
                    col_2.prop(props, "eye_iris_brightness", text="", slider=True)

                # Teeth settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Teeth Parameters",
                        "teeth_toggle",
                        props.teeth_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Teeth AO")
                    col_2.prop(props, "teeth_ao", text="", slider=True)
                    col_1.label(text="Teeth Specular")
                    col_2.prop(props, "teeth_specular", text="", slider=True)
                    col_1.label(text="Gums Brightness")
                    col_2.prop(props, "teeth_gums_brightness", text="", slider=True)
                    col_1.label(text="Gums Desaturation")
                    col_2.prop(props, "teeth_gums_desaturation", text="", slider=True)
                    col_1.label(text="Teeth Brightness")
                    col_2.prop(props, "teeth_teeth_brightness", text="", slider=True)
                    col_1.label(text="Teeth Desaturation")
                    col_2.prop(props, "teeth_teeth_desaturation", text="", slider=True)
                    col_1.label(text="Front AO")
                    col_2.prop(props, "teeth_front", text="", slider=True)
                    col_1.label(text="Rear AO")
                    col_2.prop(props, "teeth_rear", text="", slider=True)
                    col_1.label(text="Teeth Roughness")
                    col_2.prop(props, "teeth_roughness", text="", slider=True)
                    col_1.label(text="Gums SSS Scatter")
                    col_2.prop(props, "teeth_gums_sss_scatter", text="", slider=True)
                    col_1.label(text="Teeth SSS Scatter")
                    col_2.prop(props, "teeth_teeth_sss_scatter", text="", slider=True)
                    col_1.label(text="SSS Radius (cm)")
                    col_2.prop(props, "teeth_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Falloff")
                    col_2.prop(props, "teeth_sss_falloff", text="", slider=True)
                    col_1.label(text="Micro Normal")
                    col_2.prop(props, "teeth_micronormal", text="", slider=True)
                    col_1.label(text="Micro Normal Tiling")
                    col_2.prop(props, "teeth_tiling", text="", slider=True)

                # Tongue settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Tongue Parameters",
                        "tongue_toggle",
                        props.tongue_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Tongue AO")
                    col_2.prop(props, "tongue_ao", text="", slider=True)
                    col_1.label(text="Tongue Specular")
                    col_2.prop(props, "tongue_specular", text="", slider=True)
                    col_1.label(text="Tongue Brightness")
                    col_2.prop(props, "tongue_brightness", text="", slider=True)
                    col_1.label(text="Tongue Desaturation")
                    col_2.prop(props, "tongue_desaturation", text="", slider=True)
                    col_1.label(text="Front AO")
                    col_2.prop(props, "tongue_front", text="", slider=True)
                    col_1.label(text="Rear AO")
                    col_2.prop(props, "tongue_rear", text="", slider=True)
                    col_1.label(text="Tongue Roughness")
                    col_2.prop(props, "tongue_roughness", text="", slider=True)
                    col_1.label(text="SSS Scatter")
                    col_2.prop(props, "tongue_sss_scatter", text="", slider=True)
                    col_1.label(text="SSS Radius (cm)")
                    col_2.prop(props, "tongue_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Falloff")
                    col_2.prop(props, "tongue_sss_falloff", text="", slider=True)
                    col_1.label(text="Micro Normal")
                    col_2.prop(props, "tongue_micronormal", text="", slider=True)
                    col_1.label(text="Micro Normal Tiling")
                    col_2.prop(props, "tongue_tiling", text="", slider=True)

                # Nails settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Nails Parameters",
                        "nails_toggle",
                        props.nails_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Nails AO")
                    col_2.prop(props, "nails_ao", text="", slider=True)
                    col_1.label(text="Nails Specular")
                    col_2.prop(props, "nails_specular", text="", slider=True)
                    col_1.label(text="*Nails Roughness")
                    col_2.prop(props, "nails_roughness", text="", slider=True)
                    col_1.label(text="SSS Radius (cm)")
                    col_2.prop(props, "nails_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Falloff")
                    col_2.prop(props, "nails_sss_falloff", text="", slider=True)
                    col_1.label(text="Micro Normal")
                    col_2.prop(props, "nails_micronormal", text="", slider=True)
                    col_1.label(text="Micro Normal Tiling")
                    col_2.prop(props, "nails_tiling", text="", slider=True)


                # Hair settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Hair Parameters",
                        "hair_toggle",
                        props.hair_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Hair AO")
                    col_2.prop(props, "hair_ao", text="", slider=True)
                    col_1.label(text="*Hair Specular")
                    col_2.prop(props, "hair_specular", text="", slider=True)
                    col_1.label(text="*Hair Roughness")
                    col_2.prop(props, "hair_roughness", text="", slider=True)
                    col_1.label(text="*Scalp Specular")
                    col_2.prop(props, "hair_scalp_specular", text="", slider=True)
                    col_1.label(text="*Scalp Roughness")
                    col_2.prop(props, "hair_scalp_roughness", text="", slider=True)
                    col_1.label(text="SSS Radius (cm)")
                    col_2.prop(props, "hair_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Falloff")
                    col_2.prop(props, "hair_sss_falloff", text="")
                    col_1.label(text="*Bump Height (mm)")
                    col_2.prop(props, "hair_bump", text="", slider=True)

                # Defauls settings
                column.separator()
                if fake_drop_down(column.row(),
                        "Default Parameters",
                        "default_toggle",
                        props.default_toggle):
                    column.separator()
                    split = column.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Default AO")
                    col_2.prop(props, "default_ao", text="", slider=True)
                    col_1.label(text="Default Color Blend")
                    col_2.prop(props, "default_blend", text="", slider=True)
                    col_1.label(text="*Default Roughness")
                    col_2.prop(props, "default_roughness", text="", slider=True)
                    col_1.label(text="SSS Radius (cm)")
                    col_2.prop(props, "default_sss_radius", text="", slider=True)
                    col_1.label(text="SSS Falloff")
                    col_2.prop(props, "default_sss_falloff", text="")
                    col_1.label(text="Micro Normal")
                    col_2.prop(props, "default_micronormal", text="", slider=True)
                    col_1.label(text="Micro Normal Tiling")
                    col_2.prop(props, "default_tiling", text="", slider=True)
                    col_1.label(text="*Bump Height (mm)")
                    col_2.prop(props, "default_bump", text="", slider=True)
            else:
                column.separator()
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Parameters")
                op = col_2.operator("cc3.quickset", icon="FILE_REFRESH", text="Update")
                op.param = props.update_mode
                column.separator()
                split = column.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()
                col_1.label(text="Skin AO")
                col_2.prop(props, "skin_ao", text="", slider=True)
                col_1.label(text="Skin Specular")
                col_2.prop(props, "skin_basic_specular", text="", slider=True)
                col_1.label(text="Skin Roughness")
                col_2.prop(props, "skin_basic_roughness", text="", slider=True)
                col_1.label(text="Eye Specular")
                col_2.prop(props, "eye_specular", text="", slider=True)
                col_1.label(text="Eye Roughness")
                col_2.prop(props, "eye_basic_roughness", text="", slider=True)
                col_1.label(text="Eye Normal")
                col_2.prop(props, "eye_basic_normal", text="", slider=True)
                col_1.label(text="Eye Occlusion")
                col_2.prop(props, "eye_occlusion", text="", slider=True)
                col_1.label(text="Eye Brightness")
                col_2.prop(props, "eye_basic_brightness", text="", slider=True)
                col_1.label(text="Teeth Specular")
                col_2.prop(props, "teeth_specular", text="", slider=True)
                col_1.label(text="Teeth Roughness")
                col_2.prop(props, "teeth_roughness", text="", slider=True)
                col_1.label(text="Tongue Specular")
                col_2.prop(props, "tongue_specular", text="", slider=True)
                col_1.label(text="Tongue Roughness")
                col_2.prop(props, "tongue_roughness", text="", slider=True)
                col_1.label(text="Nails Specular")
                col_2.prop(props, "nails_specular", text="", slider=True)
                col_1.label(text="Hair AO")
                col_2.prop(props, "hair_ao", text="", slider=True)
                col_1.label(text="Hair Specular")
                col_2.prop(props, "hair_specular", text="", slider=True)
                col_1.label(text="Scalp Specular")
                col_2.prop(props, "hair_scalp_specular", text="", slider=True)
                col_1.label(text="Hair Bump Height (mm)")
                col_2.prop(props, "hair_bump", text="", slider=True)
                col_1.label(text="Default AO")
                col_2.prop(props, "default_ao", text="", slider=True)
                col_1.label(text="Default Bump Height (mm)")
                col_2.prop(props, "default_bump", text="", slider=True)

        layout.separator()

        if fake_drop_down(layout.box().row(),
                "5. Utilities",
                "stage5",
                props.stage5):
            column = layout.column()
            if props.import_name == "":
                column.enabled = False
            split = column.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()
            col_1.label(text="Open Mouth")
            col_2.prop(props, "open_mouth", text="", slider=True)

            column = layout.column()
            op = column.operator("cc3.quickset", icon="DECORATE_OVERRIDE", text="Reset Parameters")
            op.param = "RESET"
            op = column.operator("cc3.importer", icon="MOD_BUILD", text="Rebuild Node Groups")
            op.param ="REBUILD_NODE_GROUPS"

class CC3ToolsScenePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Scene_Panel"
    bl_label = "CC3 Scene Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        layout = self.layout

        box = layout.box()
        box.label(text="Scene Lighting", icon="INFO")
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
        box.label(text="Scene, World & Compositor", icon="INFO")
        col = layout.column()

        op = col.operator("cc3.scene", icon="TRACKING", text="3 Point Tracking & Camera")
        op.param = "TEMPLATE"

class CC3ToolsPhysicsPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Physics_Panel"
    bl_label = "CC3 Physics Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"

    def draw(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
        layout = self.layout

        missing_cloth = False
        has_cloth = False
        missing_coll = False
        has_coll = False
        has_temp_weight = False
        weight_maps = 0
        active_has_cloth = False
        meshes_selected = 0
        for obj in bpy.context.selected_objects:
            if obj.type == "MESH":
                meshes_selected += 1
                cloth_mod = get_cloth_physics_mod(obj)
                coll_mod = get_collision_physics_mod(obj)
                if cloth_mod is None:
                    missing_cloth = True
                else:
                    weight_mods = get_weight_map_mods(obj)
                    if context.object == obj:
                        weight_maps = len(weight_mods)
                        active_has_cloth = True
                    for mod in weight_mods:
                        if mod.mask_texture is not None and \
                        mod.mask_texture.image is not None and \
                        mod.mask_texture.image.packed_file is not None:
                            has_temp_weight = True
                    has_cloth = True
                if coll_mod is None:
                    missing_coll = True
                else:
                    has_coll = True

        box = layout.box()
        box.label(text="Create / Remove", icon="PHYSICS")
        col = layout.column()
        if missing_cloth:
            op = col.operator("cc3.quickset", icon="ADD", text="Add Cloth Physics")
            op.param = "PHYSICS_ADD_CLOTH"
        if has_cloth:
            op = col.operator("cc3.quickset", icon="REMOVE", text="Remove Cloth Physics")
            op.param = "PHYSICS_REMOVE_CLOTH"
        if missing_cloth or has_cloth:
            col.separator()
        if missing_coll:
            op = col.operator("cc3.quickset", icon="ADD", text="Add Collision Physics")
            op.param = "PHYSICS_ADD_COLLISION"
        if has_coll:
            op = col.operator("cc3.quickset", icon="REMOVE", text="Remove Collision Physics")
            op.param = "PHYSICS_REMOVE_COLLISION"
        if meshes_selected == 0:
            col.label(text="Select a mesh object...")


        box = layout.box()
        box.label(text="Presets", icon="OPTIONS")
        col = layout.column()
        op = col.operator("cc3.quickset", icon="USER", text="Hair")
        op.param = "PHYSICS_HAIR"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Cotton")
        op.param = "PHYSICS_COTTON"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Denim")
        op.param = "PHYSICS_DENIM"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Leather")
        op.param = "PHYSICS_LEATHER"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Rubber")
        op.param = "PHYSICS_RUBBER"
        op = col.operator("cc3.quickset", icon="MATCLOTH", text="Silk")
        op.param = "PHYSICS_SILK"

        box = layout.box()
        box.label(text="Weight Maps", icon="TEXTURE_DATA")

        if not active_has_cloth:
            col = layout.column()
            col.label(text="No Cloth physics on object...")

        split = layout.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text="WeightMap Size")
        col_2.prop(props, "physics_tex_size", text="")

        if active_has_cloth:
            col = layout.column()
            ob = context.object
            col.template_list("MATERIAL_UL_weightedmatslots", "", ob, "material_slots", ob, "active_material_index", rows=1)
            if get_weight_map_mod(obj, context_material(context)) is None:
                op = col.operator("cc3.quickset", icon="ADD", text="Add Weight Map")
                op.param = "PHYSICS_ADD_WEIGHTMAP"
            else:
                op = col.operator("cc3.quickset", icon="REMOVE", text="Remove Weight Map")
                op.param = "PHYSICS_REMOVE_WEIGHTMAP"
                if bpy.context.mode == "PAINT_TEXTURE":
                    split = col.split(factor=0.5)
                    col_1 = split.column()
                    col_2 = split.column()
                    col_1.label(text="Strength")
                    col_2.prop(props, "physics_strength", text="", slider=True)
                    op = col.operator("cc3.quickset", icon="CHECKMARK", text="Done Weight Painting!")
                    op.param = "PHYSICS_DONE_PAINTING"
                else:
                    op = col.operator("cc3.quickset", icon="BRUSH_DATA", text="Paint Weight Map")
                    op.param = "PHYSICS_PAINT"
        if has_temp_weight or has_dirty_weightmaps(bpy.context.selected_objects):
            col = layout.column()
            op = col.operator("cc3.quickset", icon="FILE_TICK", text="Save Weight Maps")
            op.param = "PHYSICS_SAVE"

class CC3ToolsPipelinePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Pipeline_Panel"
    bl_label = "CC3 Pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3"

    def draw(self, context):
        global debug_counter
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        if prefs.debug_mode:
            layout.label(text="Counter: " + str(debug_counter))
            debug_counter += 1

        if prefs.lighting == "ENABLED" or prefs.physics == "ENABLED":
            box = layout.box()
            box.label(text="Settings", icon="TOOL_SETTINGS")
            if prefs.lighting == "ENABLED":
                layout.prop(props, "lighting_mode", expand=True)
            if prefs.physics == "ENABLED":
                layout.prop(props, "physics_mode", expand=True)

        box = layout.box()
        box.label(text="Render / Quality", icon="RENDER_RESULT")
        op = layout.operator("cc3.importer", icon="IMPORT", text="Import Character")
        op.param = "IMPORT_QUALITY"

        box = layout.box()
        box.label(text="Morph Editing", icon="OUTLINER_OB_ARMATURE")
        row = layout.row()
        op = row.operator("cc3.importer", icon="IMPORT", text="Import For Morph")
        op.param = "IMPORT_MORPH"
        row = layout.row()
        op = row.operator("cc3.exporter", icon="EXPORT", text="Export Character Morph")
        op.param = "EXPORT_MORPH"
        if props.import_name == "":
            row.enabled = False

        box = layout.box()
        box.label(text="Accessory Editing", icon="MOD_CLOTH")
        row = layout.row()
        op = row.operator("cc3.importer", icon="IMPORT", text="Import For Accessory")
        op.param = "IMPORT_ACCESSORY"
        row = layout.row()
        op = row.operator("cc3.exporter", icon="EXPORT", text="Export Accessory")
        op.param = "EXPORT_ACCESSORY"
        if props.import_name == "":
            row.enabled = False

        layout.separator()
        box = layout.box()
        box.label(text="Clean Up", icon="TRASH")

        row = layout.row()
        op = row.operator("cc3.importer", icon="REMOVE", text="Remove Character")
        op.param ="DELETE_CHARACTER"
        if props.import_name == "":
            row.enabled = False


#class CC3NodeCoord(bpy.types.Panel):
#    bl_label = "Node Coordinates panel"
#    bl_idname = "CC3I_PT_NodeCoord"
#    bl_space_type = "NODE_EDITOR"
#    bl_region_type = "UI"
#
#    def draw(self, context):
#
#        if context.active_node is not None:
#            layout = self.layout
#            layout.separator()
#            row = layout.box().row()
#            coords = context.active_node.location
#            row.label(text=str(int(coords.x/10)*10) + ", " + str(int(coords.y/10)*10))


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






