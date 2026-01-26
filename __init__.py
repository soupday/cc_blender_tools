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
    importlib.reload(lib)
    importlib.reload(cc)
    importlib.reload(jsonutils)
    importlib.reload(nodeutils)
    importlib.reload(imageutils)
    importlib.reload(channel_mixer)
    importlib.reload(materials)
    importlib.reload(characters)
    importlib.reload(hik)
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
    importlib.reload(rigidbody)
    importlib.reload(springbones)
    importlib.reload(drivers)
    importlib.reload(wrinkle)
    importlib.reload(facerig_data)
    importlib.reload(facerig)
    importlib.reload(rigify_mapping_data)
    importlib.reload(rigging)
    importlib.reload(rigutils)
    importlib.reload(sculpting)
    importlib.reload(hair)
    importlib.reload(colorspace)
    importlib.reload(world)
    importlib.reload(normal)
    importlib.reload(link)
    importlib.reload(proportion)
    importlib.reload(iconutils)
    importlib.reload(rlx)

import bpy

from . import addon_updater_ops
from . import preferences
from . import vars
from . import params
from . import utils
from . import lib
from . import cc
from . import jsonutils
from . import nodeutils
from . import imageutils
from . import channel_mixer
from . import materials
from . import characters
from . import hik
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
from . import rigidbody
from . import springbones
from . import drivers
from . import wrinkle
from . import facerig_data
from . import facerig
from . import rigify_mapping_data
from . import rigging
from . import rigutils
from . import sculpting
from . import hair
from . import colorspace
from . import world
from . import normal
from . import link
from . import proportion
from . import iconutils
from . import rlx


bl_info = {
    "name": "CC/iC Tools",
    "author": "Victor Soupday",
    "version": (2, 4, 0),
    "blender": (3, 4, 1),
    "category": "Characters",
    "location": "3D View > Properties > CC/iC Pipeline",
    "description": "Automatic import and material setup of CC3/4-iClone7/8 characters.",
    "wiki_url": "https://soupday.github.io/cc_blender_tools/index.html",
    "tracker_url": "https://github.com/soupday/cc_blender_tools/issues",
}

vars.set_version_string(bl_info)

classes = (
    preferences.CC3ToolsAddonPreferences,
    preferences.MATERIAL_UL_weightedmatslots,

    channel_mixer.CC3RGBMixer,
    channel_mixer.CC3IDMixer,
    channel_mixer.CC3MixerSettings,

    properties.CCICLinkProps,
    properties.CCICBakeCache,
    properties.CCICBakeMaterialSettings,
    properties.CCICBakeProps,
    properties.CC3ActionList,
    properties.CC3ArmatureList,
    properties.CCIC_UI_MixItem,
    properties.CCIC_UI_MixList,
    properties.CCICActionStore,
    properties.CCICActionOptions,
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
    properties.CCICExpressionData,
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
    bake.CCICBakeSettings,
    bake.CCICBaker,
    bake.CCICJpegify,

    springbones.CC3OperatorSpringBones,
    physics.CC3OperatorPhysics,
    materials.CC3OperatorMaterial,
    characters.CC3OperatorCharacter,
    characters.CCICWeightTransferBlend,
    properties.CC3OperatorProperties,
    preferences.CC3OperatorPreferences,
    channel_mixer.CC3OperatorChannelMixer,
    characters.CC3OperatorTransferCharacterGeometry,
    characters.CC3OperatorTransferMeshGeometry,
    characters.CCICCharacterRename,
    characters.CCICCharacterConvertGeneric,
    sculpting.CC3OperatorSculpt,
    sculpting.CC3OperatorSculptExport,
    hair.CC3OperatorHair,
    hair.CC3ExportHair,
    link.CCICDataLink,
    link.CCICLinkConfirmDialog,
    link.CCICLinkTest,
    characters.CCICCharacterLink,
    proportion.CCICCharacterProportions,
    rigutils.CCICMotionSetFunctions,
    rigutils.CCICMotionSetRename,
    rigutils.CCICMotionSetInfo,
    rigutils.CCICRigUtils,
    rigutils.CCIC_ImportMixBones_UL_List,
    rigutils.CCIC_RigMixBones_UL_List,
    rigutils.CCICActionImportFunctions,
    rigutils.CCICActionImportOptions,
    facerig.CCICImportARKitCSV,

    panels.ARMATURE_UL_List,
    panels.ACTION_UL_List,
    panels.ACTION_SET_UL_List,
    panels.UNITY_ACTION_UL_List,
    # pipeline panels
    panels.CC3ToolsPipelineImportPanel,
    panels.CC3ToolsPipelineExportPanel,
    panels.CC3CharacterSettingsPanel,
    panels.CC3MaterialParametersPanel,
    panels.CC3RigifyPanel,
    panels.CCICBakePanel,
    panels.CC3PipelineScenePanel,
    # NLA panels
    panels.CCICNLASetsPanel,
    panels.CCICNLABakePanel,
    # create panels
    panels.CC3ToolsCreatePanel,
    panels.CC3ObjectManagementPanel,
    panels.CC3WeightPaintPanel,
    panels.CC3ToolsPhysicsPanel,
    panels.CC3SpringRigPanel,
    panels.CC3ToolsSculptingPanel,
    panels.CCICProportionPanel,
    panels.CC3HairPanel,
    # link panels
    panels.CCICDataLinkPanel,
    panels.CCICAnimationToolsPanel,
    panels.CCICLinkScenePanel,
    # control panels
    panels.CC3SpringControlPanel,
    # test panels
    panels.CC3ToolsUtilityPanel,
)



def register():

    addon_updater_ops.register(bl_info)

    for cls in classes:
        bpy.utils.register_class(cls)

    iconutils.register()

    bpy.types.Scene.CC3ImportProps = bpy.props.PointerProperty(type=properties.CC3ImportProps)
    bpy.types.Scene.CCICBakeProps = bpy.props.PointerProperty(type=properties.CCICBakeProps)
    bpy.types.Scene.CCICLinkProps = bpy.props.PointerProperty(type=properties.CCICLinkProps)
    bpy.types.TOPBAR_MT_file_import.append(importer.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(importer.menu_func_import_animation)
    bpy.types.TOPBAR_MT_file_export.append(exporter.menu_func_export)

    if link.disconnect not in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.append(link.disconnect)
    if link.reconnect not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(link.reconnect)

    bpy.app.timers.register(link.reconnect, first_interval=0.5, persistent=False)


def unregister():

    link.disconnect()

    addon_updater_ops.unregister()

    bpy.types.TOPBAR_MT_file_import.remove(importer.menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(importer.menu_func_import_animation)
    bpy.types.TOPBAR_MT_file_export.remove(exporter.menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)

    iconutils.unregister()

    del(bpy.types.Scene.CC3ImportProps)
    del(bpy.types.Scene.CCICBakeProps)
    del(bpy.types.Scene.CCICLinkProps)

    if link.disconnect in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.remove(link.disconnect)
    if link.reconnect in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(link.reconnect)

