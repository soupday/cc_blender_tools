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
    "version": (0, 6, 3),
    "blender": (2, 80, 0),
    "category": "Characters",
    "location": "3D View > Properties> CC3",
    "description": "Automatic import and material setup of CC3 characters.",
    "wiki_url": "https://soupday.github.io/cc3_blender_tools/index.html",
    "tracker_url": "https://github.com/soupday/cc3_blender_tools/issues",
}

vars.set_version_string(bl_info)

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