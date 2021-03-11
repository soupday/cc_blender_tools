# Version: 0.2.x
#   DONE
#   - When no texture maps are present for an advanced node group, does not generate the node group.
#   - When exporting morph characters with .fbxkey or .objkey files, the key file is copied along with the export.
#   - Function added to reset preferences to default values.
#   - Alpha blend settings and back face culling settings can be applied to materials in the object now.
#   - Option to apply alpha blend settings to whole object(s) or just active materal.
#   - Remembers the applied alpha blend settings and re-applies when rebuilding materials.
#   - Reorganised the code in modules.
#
#   Physics:
#   - Uses the physX weight maps to auto-generate vertex pin weights for cloth/hair physics (Optional in the preferences).
#   - Automatically sets up cloth/hair physics modifiers (Optional in the preferences)
#   - Physics cloth presets can be applied to the selected object(s) and are remembered with rebuilding materials.
#   - Weightmaps can be added/removed to the individual materials of the objects.
#   - Operator to setup and begin texture painting of the per material weight maps.
#
# TODO
#   - Operator to save any modified weight maps to disk.
#   - Prefs for physics settings.
#   - Pick Scalp Material (Is there an eye dropper for materials?).
#   - Button to auto transfer skin weights to accessories.
#
# FUTURE PLANS
#   - Get all search strings to identify material type: skin, eyelashes, body, hair etc... from preferences the user can customise.
#       (Might help with Daz conversions and/or 3rd party characters that have non-standard or unexpected material names.)
#   - Automatically generate full IK rig with Rigify or Auto-Rig Pro (Optional in the preferences)
#       (Not sure if this is possible to invoke these add-ons from code...)
#
# --------------------------------------------------------------
# Primary modules: importer, exporter, scene, parameters, ui
#

import bpy

from .cache import CC3MaterialCache, CC3ObjectCache
from .exporter import CC3Export
from .importer import CC3Import
from .parameters import (CC3ImportProps, CC3ObjectPointer, CC3QuickSet,
                        CC3ToolsAddonPreferences)
from .scene import CC3Scene
from .ui import (CC3ToolsMaterialSettingsPanel, CC3ToolsPhysicsPanel,
                CC3ToolsPipelinePanel, CC3ToolsScenePanel,
                MATERIAL_UL_weightedmatslots)

bl_info = {
    "name": "CC3 Tools",
    "author": "Victor Soupday",
    "version": (0, 2, 1),
    "blender": (2, 80, 0),
    "category": "Characters",
    "location": "3D View > Properties> CC3",
    "description": "Automatic import and material setup of CC3 characters.",
}

classes = (CC3ObjectPointer, CC3MaterialCache, CC3ObjectCache, CC3ImportProps,
           CC3ToolsPipelinePanel, CC3ToolsMaterialSettingsPanel, CC3ToolsPhysicsPanel,
           CC3ToolsScenePanel, MATERIAL_UL_weightedmatslots,
           CC3Import, CC3Export, CC3Scene, CC3QuickSet, CC3ToolsAddonPreferences)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.CC3ImportProps = bpy.props.PointerProperty(type=CC3ImportProps)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del(bpy.types.Scene.CC3ImportProps)
