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

if "bpy" in locals():
    import importlib
    importlib.reload(addon_updater_ops)
    importlib.reload(preferences)
    importlib.reload(vars)
    importlib.reload(params)
    importlib.reload(utils)
    importlib.reload(jsonutils)
    importlib.reload(nodeutils)
    importlib.reload(imageutils)
    importlib.reload(channel_mixer)
    importlib.reload(materials)
    importlib.reload(characters)
    importlib.reload(meshutils)
    importlib.reload(modifiers)
    importlib.reload(shaders)
    importlib.reload(basic)
    importlib.reload(physics)
    importlib.reload(bake)
    importlib.reload(panels)
    importlib.reload(properties)
    importlib.reload(scene)
    importlib.reload(exporter)
    importlib.reload(importer)
    importlib.reload(geom)
    importlib.reload(bones)
    importlib.reload(rigify_mapping_data)
    importlib.reload(rigging)
    importlib.reload(sculpting)
    importlib.reload(hair)

import bpy

from . import addon_updater_ops
from . import preferences
from . import vars
from . import params
from . import utils
from . import jsonutils
from . import nodeutils
from . import imageutils
from . import channel_mixer
from . import materials
from . import characters
from . import meshutils
from . import modifiers
from . import shaders
from . import basic
from . import physics
from . import bake
from . import panels
from . import properties
from . import scene
from . import exporter
from . import importer
from . import geom
from . import bones
from . import rigify_mapping_data
from . import rigging
from . import sculpting
from . import hair


bl_info = {
    "name": "CC/iC Tools",
    "author": "Victor Soupday",
    "version": (1, 5, 4),
    "blender": (2, 80, 0),
    "category": "Characters",
    "location": "3D View > Properties > CC/iC Pipeline",
    "description": "Automatic import and material setup of CC3/4-iClone7/8 characters.",
    "wiki_url": "https://soupday.github.io/cc_blender_tools/index.html",
    "tracker_url": "https://github.com/soupday/cc_blender_tools/issues",
}

vars.set_version_string(bl_info)

classes = (
    channel_mixer.CC3RGBMixer,
    channel_mixer.CC3IDMixer,
    channel_mixer.CC3MixerSettings,

    properties.CC3ActionList,
    properties.CC3ArmatureList,
    properties.CC3HeadParameters,
    properties.CC3SkinParameters,
    properties.CC3EyeParameters,
    properties.CC3EyeOcclusionParameters,
    properties.CC3TearlineParameters,
    properties.CC3TeethParameters,
    properties.CC3TongueParameters,
    properties.CC3HairParameters,
    properties.CC3PBRParameters,
    properties.CC3SSSParameters,
    properties.CC3BasicParameters,
    properties.CC3TextureMapping,
    properties.CC3EyeMaterialCache,
    properties.CC3EyeOcclusionMaterialCache,
    properties.CC3TearlineMaterialCache,
    properties.CC3TeethMaterialCache,
    properties.CC3TongueMaterialCache,
    properties.CC3HairMaterialCache,
    properties.CC3HeadMaterialCache,
    properties.CC3SkinMaterialCache,
    properties.CC3PBRMaterialCache,
    properties.CC3SSSMaterialCache,
    properties.CC3ObjectCache,
    properties.CC3CharacterCache,
    properties.CC3ImportProps,

    importer.CC3Import,
    importer.CC3ImportAnimations,
    exporter.CC3Export,
    scene.CC3Scene,
    bake.CC3BakeOperator,
    rigging.CC3Rigifier,
    rigging.CC3RigifierModal,

    physics.CC3OperatorPhysics,
    materials.CC3OperatorMaterial,
    characters.CC3OperatorCharacter,
    properties.CC3OperatorProperties,
    preferences.CC3OperatorPreferences,
    channel_mixer.CC3OperatorChannelMixer,
    sculpting.CC3OperatorSculpt,
    hair.CC3OperatorHair,
    hair.CC3ExportHair,

    panels.ARMATURE_UL_List,
    panels.ACTION_UL_List,
    panels.UNITY_ACTION_UL_List,
    # pipeline panels
    panels.CC3ToolsPipelinePanel,
    panels.CC3CharacterSettingsPanel,
    panels.CC3MaterialParametersPanel,
    panels.CC3RigifyPanel,
    panels.CC3ToolsScenePanel,
    # create panels
    panels.CC3ToolsCreatePanel,
    panels.CC3ObjectManagementPanel,
    panels.CC3ToolsPhysicsPanel,
    panels.CC3ToolsSculptingPanel,
    panels.CC3ToolsUtilityPanel,
    panels.CC3HairPanel,

    preferences.CC3ToolsAddonPreferences,
    preferences.MATERIAL_UL_weightedmatslots,

)

def register():

    addon_updater_ops.register(bl_info)

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.CC3ImportProps = bpy.props.PointerProperty(type=properties.CC3ImportProps)


def unregister():

    addon_updater_ops.unregister()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del(bpy.types.Scene.CC3ImportProps)
