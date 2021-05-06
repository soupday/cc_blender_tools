if "bpy" in locals():
    import importlib
    importlib.reload(vars)
    importlib.reload(utils)
    importlib.reload(params)
    importlib.reload(importer)

import bpy
from . import addon_updater_ops
from . import importer
from . import params
from . import utils
from . import vars

bl_info = {
    "name": "CC3 Tools",
    "author": "Victor Soupday",
    "version": (0, 6, 1),
    "blender": (2, 80, 0),
    "category": "Characters",
    "location": "3D View > Properties> CC3",
    "description": "Automatic import and material setup of CC3 characters.",
}

classes = (
    importer.CC3MaterialParameters,
    importer.CC3ObjectPointer, importer.CC3MaterialCache, importer.CC3ObjectCache, importer.CC3ImportProps,
           importer.CC3ToolsPipelinePanel, importer.CC3ToolsMaterialSettingsPanel,
           importer.CC3ToolsParametersPanel, importer.CC3ToolsPhysicsPanel,
           importer.CC3ToolsScenePanel, importer.MATERIAL_UL_weightedmatslots,
           importer.CC3Import, importer.CC3Export, importer.CC3Scene, importer.CC3QuickSet,
           importer.CC3ToolsAddonPreferences)

def register():

    addon_updater_ops.register(bl_info)

    for cls in classes:
        bpy.utils.register_class(cls)

    #bpy.types.Material.cc3_params = bpy.props.CollectionProperty(type=params.CC3MaterialParameters)
    bpy.types.Scene.CC3ImportProps = bpy.props.PointerProperty(type=importer.CC3ImportProps)

def unregister():

    addon_updater_ops.unregister()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    #del bpy.types.Material.cc3_params
    del(bpy.types.Scene.CC3ImportProps)