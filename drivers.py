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
from . import meshutils, jsonutils, utils, vars
from rna_prop_ui import rna_idprop_ui_create

def make_driver_var(driver, var_type, var_name, target, target_type = "OBJECT", data_path = "", bone_target = "", transform_type = "", transform_space = ""):
    """
    var_type = "SINGLE_PROP", "TRANSFORMS"\n
    var_name = variable name\n
    target = target object/rig\n
    SINGLE_PROP:\n
    target_type = "OBJECT", "MESH"...\n
    target_data_path = "shape_keys.key_blocks[\"key_name\"].value"\n
    TRANSFORMS:\n
    bone_target = pose bone name\n
    transform_type = "LOC_X", "ROT_X" ...\n
    transform_space = "LOCAL", "WORLD" ...
    """
    var : bpy.types.DriverVariable = driver.variables.new()
    var.name = var_name
    var.type = var_type
    if var_type == "SINGLE_PROP":
        var.targets[0].id_type = target_type
        var.targets[0].id = target.id_data
        var.targets[0].data_path = data_path
    elif var_type == "TRANSFORMS":
        var.targets[0].id = target.id_data
        var.targets[0].bone_target = bone_target
        var.targets[0].rotation_mode = "AUTO"
        var.targets[0].transform_type = transform_type
        var.targets[0].transform_space = transform_space
    return var


def make_dummy_var(driver, var_name):
    var : bpy.types.DriverVariable = driver.variables.new()
    var.name = var_name


def make_driver(source, prop_name, driver_type, driver_expression = "", index = -1):
    """
    prop_name = "value", "influence"\n
    driver_type = "SUM", "SCRIPTED", "AVERAGE"\n
    driver_expression = "..."
    """
    driver = None
    if source:
        fcurve : bpy.types.FCurve
        if index > -1:
            source.driver_remove(prop_name, index)
            fcurve = source.driver_add(prop_name, index)
        else:
            source.driver_remove(prop_name)
            fcurve = source.driver_add(prop_name)
        driver : bpy.types.Driver = fcurve.driver
        if driver_type == "SUM" or driver_type == "AVERAGE":
            driver.type = driver_type
        elif driver_type == "SCRIPTED":
            driver.type = driver_type
            driver.expression = driver_expression
    return driver


def add_custom_float_property(obj, prop_name, prop_value : float,
                              value_min : float = 0.0, value_max : float = 1.0,
                              soft_min = None, soft_max = None,
                              overridable = True, subtype=None, precision=3,
                              description : str = ""):

    if prop_name not in obj:

        prop_value = float(prop_value)
        if value_min is not None:
            value_min = float(value_min)
        if value_max is not None:
            value_max = float(value_max)
        if soft_max is None:
            soft_max = value_max
        if soft_min is None:
            soft_min = value_min

        if utils.B360():
            rna_idprop_ui_create(obj, prop_name,
                                 default=prop_value,
                                 overridable=overridable,
                                 min=value_min, max=value_max,
                                 soft_min=soft_min, soft_max=soft_max,
                                 subtype=subtype,
                                 precision=precision,
                                 description=description)
        else:
            rna_idprop_ui_create(obj, prop_name,
                                 default=prop_value,
                                 overridable=overridable,
                                 min=value_min, max=value_max,
                                 soft_min=soft_min, soft_max=soft_max,
                                 subtype=subtype,
                                 description=description)


def add_custom_int_property(obj, prop_name, prop_value: int,
                              value_min: int = 0, value_max: int = 1.0,
                              soft_min= None, soft_max= None,
                              overridable= True,
                              description: str = ""):

    if prop_name not in obj:

        prop_value = int(prop_value)
        if value_min is not None:
            value_min = int(value_min)
        if value_max is not None:
            value_max = int(value_max)
        if soft_max is None:
            soft_max = value_max
        if soft_min is None:
            soft_min = value_min

        rna_idprop_ui_create(obj, prop_name,
                             default=prop_value,
                             overridable=overridable,
                             min=value_min, max=value_max,
                             soft_min=soft_min, soft_max=soft_max,
                             description=description)


def add_custom_string_property(obj, prop_name, prop_value: str,
                              overridable=True,
                              description: str=""):
    """subtype = NONE, FILE_PATH, DIR_PATH"""

    if prop_name not in obj:

        if utils.B360():
            rna_idprop_ui_create(obj, prop_name,
                                 default=prop_value,
                                 overridable=overridable,
                                 description=description)
        else:
            obj[prop_name] = prop_value

            try:
                id_props = obj.id_properties_ui(prop_name)
                id_props.update(default=prop_value, description=description)
            except:
                pass


def add_custom_float_array_property(obj, prop_name, prop_value : list,
                                     value_min : float = 0.0, value_max : float = 1.0,
                                     soft_min = None, soft_max = None,
                                     overridable = True,
                                     description : str = ""):

    if prop_name not in obj:

        if soft_max is None:
            soft_max = value_max
        if soft_min is None:
            soft_min = value_min

        rna_idprop_ui_create(obj, prop_name,
                             default=prop_value,
                             overridable=overridable,
                             min=value_min, max=value_max,
                             soft_min=soft_min, soft_max=soft_max,
                             description=description)


SHAPE_KEY_DRIVERS = {

    # values taken from Neutral base character, zero values are *not* driven.

    "V_Open": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0,0,18.0],
    },

    # no rotations on: "B_M_P", "Ch_J", "F_V", "S_Z", "W_OO",

    "Ah": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0,0,10.5],
    },

    "Oh": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0,0,9.6],
    },

    "EE": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0,0,1.2],
    },

    "Er": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0,0,5.7],
    },

    "IH": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0,0,4.9],
    },

    "K_G_H_NG": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0,0,3.0],
    },

    "AE": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0,0,9.0],
    },

    "R": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0,0,1.65],
    },

    "T_L_D_N": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0,0,4.7],
    },

    "TH": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0,0,4.0],
    },

    # - Jaw_Open / CC_Base_Tongue01 = (0.1863, 0.0206, -9.2686)
    # - Jaw_Open / CC_Base_Teeth02 = (-0.0109, -0.0038, 8.9977)
    # - Jaw_Open / CC_Base_JawRoot = (0.0000, -0.0000, 30.0881) FACE DRIVER

    "Jaw_Open": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0.0001,0.0001,0.0001], #using non zero values to lock translation in place
        "rotate": [0,0,30],
    },

    "Jaw_Open.001": {
        "bone": ["CC_Base_Teeth02"],
        "range": 100.0,
        "translate": [0.0001,0.0001,0.0001], #using non zero values to lock translation in place
        "rotate": [0,0,9],
    },

    "Jaw_Open.002": {
        "bone": ["CC_Base_Tongue01"],
        "range": 100.0,
        "translate": [0.0001,0.0001,0.0001], #using non zero values to lock translation in place
        "rotate": [0,0,-9],
    },

    "Jaw_Forward": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0.75,0,0],
        "rotate": [0,0,0],
    },

    "Jaw_Backward": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [-0.5,0,0],
        "rotate": [0,0,0],
    },

    "Jaw_L": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0.658],
        "rotate": [0,0,0],
    },

    "Jaw_R": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,-0.658],
        "rotate": [0,0,0],
    },

    "Jaw_Up": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,-0.25,0],
        "rotate": [0,0,0],
    },

    "Jaw_Down": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0.55,0],
        "rotate": [0,0,0],
    },



    "Head_Turn_Up": {
        "bone": ["CC_Base_Head","head","spine.006"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [-31, 0, 0],
    },

    "Head_Turn_Down": {
        "bone": ["CC_Base_Head","head","spine.006"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [17, 0, 0],
    },

    "Head_Turn_L": {
        "bone": ["CC_Base_Head","head","spine.006"],
        "range": 100.0,
        "translate": [1.68, 0, 0],
        "rotate": [0, 51, 0],
    },

    "Head_Turn_R": {
        "bone": ["CC_Base_Head","head","spine.006"],
        "range": 100.0,
        "translate": [-1.68, 0, 0],
        "rotate": [0, -51, 0],
    },

    "Head_Tilt_L": {
        "bone": ["CC_Base_Head","head","spine.006"],
        "range": 100.0,
        "translate": [0.64, 0, 0],
        "rotate": [0, 0, 23.33],
    },

    "Head_Tilt_R": {
        "bone": ["CC_Base_Head","head","spine.006"],
        "range": 100.0,
        "translate": [-0.64, 0, 0],
        "rotate": [0, 0, 23.33],
    },

    "Head_L": {
        "bone": ["CC_Base_Head","head","spine.006"],
        "range": 100.0,
        "translate": [2,0,0],
        "rotate": [0,0,0],
    },

    "Head_R": {
        "bone": ["CC_Base_Head","head","spine.006"],
        "range": 100.0,
        "translate": [-2,0,0],
        "rotate": [0,0,0],
    },

    "Head_Forward": {
        "bone": ["CC_Base_Head","head","spine.006"],
        "range": 100.0,
        "translate": [0, 0, 2.95],
        "rotate": [0,0,0],
    },

    "Head_Backward": {
        "bone": ["CC_Base_Head","head","spine.006"],
        "range": 100.0,
        "translate": [0, 0, -2.6],
        "rotate": [0,0,0],
    },

    "Eye_L_Look_L": {
        "bone": ["CC_Base_L_Eye","eye.L"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0, 0, 40],
    },

    "Eye_R_Look_L": {
        "bone": ["CC_Base_R_Eye","eye.R"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0, 0, 30],
    },

    "Eye_L_Look_R": {
        "bone": ["CC_Base_L_Eye","eye.L"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0, 0, -30],
    },

    "Eye_R_Look_R": {
        "bone": ["CC_Base_R_Eye","eye.R"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0, 0, -40],
    },

    "Eye_L_Look_Up": {
        "bone": ["CC_Base_L_Eye","eye.L"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [-20, 0, 0],
    },

    "Eye_R_Look_Up": {
        "bone": ["CC_Base_R_Eye","eye.R"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [-20, 0, 0],
    },

    "Eye_L_Look_Down": {
        "bone": ["CC_Base_L_Eye","eye.L"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [22, 0, 0],
    },

    "Eye_R_Look_Down": {
        "bone": ["CC_Base_R_Eye","eye.R"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [22, 0, 0],
    },


    "Mouth_Open": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0, 0, 17],
    },

    "A25_Jaw_Open": {
        "bone": ["CC_Base_JawRoot","jaw_master"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0, 0, 35],
    },

    "A10_Eye_Look_Out_Left": {
        "bone": ["CC_Base_L_Eye","eye.L"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0, 0, 40],
    },

    "A12_Eye_Look_In_Right": {
        "bone": ["CC_Base_R_Eye","eye.R"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0, 0, 30],
    },

    "A11_Eye_Look_In_Left": {
        "bone": ["CC_Base_L_Eye","eye.L"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0, 0, -30],
    },

    "A13_Eye_Look_Out_Right": {
        "bone": ["CC_Base_R_Eye","eye.R"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [0, 0, -40],
    },

    "A06_Eye_Look_Up_Left": {
        "bone": ["CC_Base_L_Eye","eye.L"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [-20, 0, 0],
    },

    "A07_Eye_Look_Up_Right": {
        "bone": ["CC_Base_R_Eye","eye.R"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [-20, 0, 0],
    },

    "A08_Eye_Look_Down_Left": {
        "bone": ["CC_Base_L_Eye","eye.L"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [22, 0, 0],
    },

    "A09_Eye_Look_Down_Right": {
        "bone": ["CC_Base_R_Eye","eye.R"],
        "range": 100.0,
        "translate": [0,0,0],
        "rotate": [22, 0, 0],
    },
}


def has_facial_shape_key_bone_drivers(chr_cache):
    arm = chr_cache.get_armature()
    if not arm: return False
    for drv in arm.animation_data.drivers:
        for key_name in SHAPE_KEY_DRIVERS.keys():
            bone_names = SHAPE_KEY_DRIVERS[key_name]["bone"]
            translate = SHAPE_KEY_DRIVERS[key_name]["translate"]
            rotate = SHAPE_KEY_DRIVERS[key_name]["rotate"]
            key_name = utils.strip_name(key_name)
            shape_key_path = f"shape_keys.key_blocks[\"{key_name}\"]"
            for bone_name in bone_names:
                if bone_name in arm.pose.bones:
                    bone: bpy.types.Bone = arm.pose.bones[bone_name]
                    for i,v in enumerate(translate):
                        if v != 0:
                            data_path = f"pose.bones[\"{bone_name}\"].location"
                            if drv.data_path == data_path and drv.array_index == i:
                                for var in drv.driver.variables:
                                    for target in var.targets:
                                        if shape_key_path in target.data_path:
                                            return True
                    for i,v in enumerate(rotate):
                        if v != 0:
                            data_path = f"pose.bones[\"{bone_name}\"].rotation_euler"
                            if drv.data_path == data_path and drv.array_index == i:
                                for var in drv.driver.variables:
                                    for target in var.targets:
                                        if shape_key_path in target.data_path:
                                            return True
    return False


def clear_facial_shape_key_bone_drivers(chr_cache):
    """clear drivers for the jaw, eye and head bones (optional) based on the facial
       expression shape keys.
    """

    arm = chr_cache.get_armature()

    if not arm: return

    bone_names_done = []

    utils.object_mode_to(arm)

    # remove existing drivers
    if "facerig" in arm.pose.bones:
        ...
    else:
        # remove existing drivers
        for expression_cache in chr_cache.expression_set:
            bone_name = expression_cache.bone_name
            key_name = expression_cache.key_name
            if bone_name in arm.pose.bones and bone_name not in bone_names_done:
                bone_names_done.append(bone_name)
                pose_bone = arm.pose.bones[bone_name]
                pose_bone.rotation_mode = "QUATERNION"
                utils.log_info(f"Removing drivers for: {bone_name}")
                pose_bone.driver_remove("location", 0)
                pose_bone.driver_remove("location", 1)
                pose_bone.driver_remove("location", 2)
                pose_bone.driver_remove("rotation_euler", 0)
                pose_bone.driver_remove("rotation_euler", 1)
                pose_bone.driver_remove("rotation_euler", 2)
                pose_bone.driver_remove("rotation_quaternion", 0)
                pose_bone.driver_remove("rotation_quaternion", 1)
                pose_bone.driver_remove("rotation_quaternion", 2)
                pose_bone.driver_remove("rotation_quaternion", 3)
                pose_bone.driver_remove("rotation_axis_angle", 0)
                pose_bone.driver_remove("rotation_axis_angle", 1)
                pose_bone.driver_remove("rotation_axis_angle", 2)
                pose_bone.driver_remove("rotation_axis_angle", 3)
                pose_bone.driver_remove("scale", 0)
                pose_bone.driver_remove("scale", 1)
                pose_bone.driver_remove("scale", 2)


def get_head_body_object(chr_cache):
    return meshutils.get_head_body_object(chr_cache)


def add_facial_shape_key_bone_drivers(chr_cache, jaw, eye_look, head):
    """Add drivers for the jaw, eye and head bones (optional) based on the facial
       expression shape keys.
    """

    body = meshutils.get_head_body_object(chr_cache)
    arm = chr_cache.get_armature()

    if not body or not arm:
        return

    bone_drivers = {}
    bone_names_done = []

    utils.object_mode_to(arm)

    # remove existing drivers
    for expression_cache in chr_cache.expression_set:
        bone_name = expression_cache.bone_name
        key_name = expression_cache.key_name
        if bone_name in arm.pose.bones and bone_name not in bone_names_done:
            bone_names_done.append(bone_name)
            pose_bone = arm.pose.bones[bone_name]
            utils.log_info(f"Removing drivers for: {bone_name}")
            pose_bone.rotation_mode = "QUATERNION"
            pose_bone.driver_remove("location", 0)
            pose_bone.driver_remove("location", 1)
            pose_bone.driver_remove("location", 2)
            pose_bone.driver_remove("rotation_euler", 0)
            pose_bone.driver_remove("rotation_euler", 1)
            pose_bone.driver_remove("rotation_euler", 2)
            pose_bone.driver_remove("rotation_quaternion", 0)
            pose_bone.driver_remove("rotation_quaternion", 1)
            pose_bone.driver_remove("rotation_quaternion", 2)
            pose_bone.driver_remove("rotation_quaternion", 3)
            pose_bone.driver_remove("rotation_axis_angle", 0)
            pose_bone.driver_remove("rotation_axis_angle", 1)
            pose_bone.driver_remove("rotation_axis_angle", 2)
            pose_bone.driver_remove("rotation_axis_angle", 3)
            pose_bone.driver_remove("scale", 0)
            pose_bone.driver_remove("scale", 1)
            pose_bone.driver_remove("scale", 2)

    # refactor shape key driver list by bone_name, property and array property index
    for expression_cache in chr_cache.expression_set:
        bone_name = expression_cache.bone_name
        key_name = expression_cache.key_name
        translate = expression_cache.translation
        rotate = expression_cache.rotation

        if bone_name not in arm.pose.bones:
            continue

        if not meshutils.find_shape_key(body, key_name):
            utils.log_info(f"Shape-key: {key_name} not found, skipping.")
            continue

        if ((key_name.startswith("Jaw_") and not jaw) or
            (key_name.startswith("V_") and not jaw) or
            (key_name == "Ah" and not jaw) or
            (key_name == "Oh" and not jaw) or
            (key_name.startswith("Eye_") and not eye_look) or
            (key_name.startswith("Head_") and not head) or
            # do *not* add bone drivers from constraints
            (key_name.startswith("C_"))):
            continue

        # find the bone specified from the list of possible bones in the shape_key driver def
        for i,v in enumerate(translate):
            #if i == 1 and (bone_name == "CC_Base_JawRoot" or bone_name == "CC_Base_Teeth02"):
            #    v *= 1.185
            if abs(v) > 0.0001: # 1/10 of a mm
                driver_id = bone_name, "location", i
                if driver_id not in bone_drivers.keys():
                    bone_drivers[driver_id] = { "bone_name": bone_name,
                                                "prop": "location",
                                                "index": i,
                                                "shape_keys": [] }
                bone_drivers[driver_id]["shape_keys"].append({ "shape_key": key_name,
                                                                "value": v })
        for i,v in enumerate(rotate):
            if abs(v) > 0.001: # 1/10 of a degree
                driver_id = bone_name, "rotation_euler", i
                if driver_id not in bone_drivers.keys():
                    bone_drivers[driver_id] = { "bone_name": bone_name,
                                                "prop": "rotation_euler",
                                                "index": i,
                                                "shape_keys": [] }
                bone_drivers[driver_id]["shape_keys"].append({ "shape_key": key_name,
                                                               "value": v })

    # create drivers for each (bone, property, index) driven by shape keys
    for driver_id in bone_drivers.keys():
        bone_driver_def = bone_drivers[driver_id]
        bone_name = bone_driver_def["bone_name"]
        pose_bone : bpy.types.PoseBone
        pose_bone = arm.pose.bones[bone_name]
        if driver_id[1] == "rotation_euler":
            pose_bone.rotation_mode = "XYZ"
        prop = bone_driver_def["prop"]
        index = bone_driver_def["index"]
        shape_key_defs = bone_driver_def["shape_keys"]

        # build driver expression
        expr = "("
        for i, key_def in enumerate(shape_key_defs):
            var_name = f"var{i}"
            shape_key_name = key_def["shape_key"]
            fac = "{:.6f}".format(key_def["value"])
            if i > 0:
                expr += "+"
            expr += f"{var_name}*{fac}"
        expr += ")"
        #if len(shape_key_defs) > 1:
        #    expr += f"/{len(shape_key_defs)}"

        # make driver
        utils.log_detail(f"Adding driver to {driver_id}: expr = {expr}")
        driver = make_driver(pose_bone, prop, "SCRIPTED", driver_expression=expr, index=index)

        # make driver vars
        if driver:
            for i, key_def in enumerate(shape_key_defs):
                var_name = f"var{i}"
                shape_key_name = key_def["shape_key"]
                data_path = f"shape_keys.key_blocks[\"{shape_key_name}\"].value"
                var = make_driver_var(driver,
                                        "SINGLE_PROP",
                                        var_name,
                                        body.data,
                                        target_type="MESH",
                                        data_path=data_path)


def get_shape_key(obj, key_name) -> bpy.types.ShapeKey:
    try:
        return obj.data.shape_keys.key_blocks[key_name]
    except:
        return None


def clear_body_shape_key_drivers(chr_cache, objects=None):

    body_objects = chr_cache.get_objects_of_type("BODY")
    body_objects.extend(chr_cache.get_objects_of_type("TONGUE"))
    body_objects.extend(chr_cache.get_objects_of_type("EYE"))

    arm = chr_cache.get_armature()

    if not body_objects or not arm:
        return

    body_keys = []
    for body in body_objects:
        if utils.object_has_shape_keys(body):
            for key_block in body.data.shape_keys.key_blocks:
                if key_block.name not in body_keys:
                    body_keys.append(key_block.name)
    if body_keys:
        if not objects:
            objects = chr_cache.get_cache_objects()
        for obj in objects:
            if utils.object_has_shape_keys(obj):
                obj_key : bpy.types.ShapeKey
                for obj_key in obj.data.shape_keys.key_blocks:
                    if obj_key.name in body_keys:
                        obj_key.driver_remove("value")


def add_body_shape_key_drivers(chr_cache, add_drivers, only_objects=None):
    """Drive all expression shape keys on non-body objects from the body shape keys.
    """

    arm = chr_cache.get_armature()
    body = meshutils.get_head_body_object(chr_cache)
    tongue = meshutils.get_tongue_object(chr_cache)
    eye = meshutils.get_eye_object(chr_cache)

    if not body and not tongue:
        return

    utils.log_info(f"Using head mesh: {body.name} for driver source")

    key_sources = {}
    if utils.object_has_shape_keys(eye):
        for key in eye.data.shape_keys.key_blocks:
            if key.name.startswith("Eye_Pupil_"):
                print(f"EYE: {key.name}")
                key_sources[key.name] = eye
    if utils.object_has_shape_keys(tongue):
        for key in tongue.data.shape_keys.key_blocks:
            if key.name.startswith("V_Tongue_") or key.name.startswith("Tongue_"):
                print(f"TONGUE: {key.name}")
                key_sources[key.name] = tongue
    if utils.object_has_shape_keys(body):
        for key in body.data.shape_keys.key_blocks:
            if key.name not in key_sources:
                print(f"BODY: {key.name}")
                key_sources[key.name] = body

    for obj in chr_cache.get_cache_objects():
        if only_objects and obj not in only_objects:
            continue
        if utils.object_has_shape_keys(obj):
            obj_key : bpy.types.ShapeKey
            for obj_key in obj.data.shape_keys.key_blocks:
                if obj_key.name in key_sources and key_sources[obj_key.name] != obj:
                    src_obj = key_sources[obj_key.name]
                    obj_key.driver_remove("value")
                    if add_drivers:
                        # make driver
                        utils.log_detail(f"Adding driver to {obj.name} for expression key: {obj_key.name}")
                        driver = make_driver(obj_key, "value", "SUM")
                        # make driver var
                        if driver:
                            data_path = f"shape_keys.key_blocks[\"{obj_key.name}\"].value"
                            make_driver_var(driver,
                                            "SINGLE_PROP",
                                            "key_value",
                                            src_obj.data,
                                            target_type="MESH",
                                            data_path=data_path)


def get_id_type(obj):
    T = type(obj)
    if T is bpy.types.Mesh:
        return "MESH"
    return "OBJECT"


def make_custom_prop_var_def(var_name, source_obj, prop_name):
    data_path = f"{source_obj.path_from_id()}[\"{prop_name}\"]"
    var_def = [var_name,
               "SINGLE_PROP",
               source_obj,
               data_path]
    return var_def


def find_custom_prop_var_def(var_defs, source_obj, prop_name):
    data_path = f"{source_obj.path_from_id()}[\"{prop_name}\"]"
    for var_def in var_defs:
        if (len(var_def) == 4 and
            var_def[1] == "SINGLE_PROP" and
            var_def[2] == source_obj and
            var_def[3] == data_path):
            return var_def[0]
    return None


def make_bone_transform_var_def(var_name, source_rig, bone_name, transform_axis, space="LOCAL_SPACE"):
    var_def = [var_name,
               "TRANSFORMS",
               source_rig,
               bone_name,
               transform_axis,
               space]
    return var_def


def find_bone_transform_var_def(var_defs, source_rig, bone_name, transform_axis, space="LOCAL_SPACE"):
    for var_def in var_defs:
        if (len(var_def) == 6 and
            var_def[1] == "TRANSFORMS" and
            var_def[2] == source_rig and
            var_def[3] == bone_name and
            var_def[4] == transform_axis and
            var_def[5] == space):
            return var_def[0]
    return None


def make_transform_var_def(var_name, source_obj, transform_prop, space="LOCAL_SPACE"):
    var_def = [var_name,
               "TRANSFORMS",
               source_obj,
               None,
               transform_prop,
               space]
    return var_def


def find_transform_var_def(var_defs, source_obj, transform_prop, space="LOCAL_SPACE"):
    for var_def in var_defs:
        if (len(var_def) == 6 and
            var_def[1] == "TRANSFORMS" and
            var_def[2] == source_obj and
            var_def[3] == None and
            var_def[4] == transform_prop and
            var_def[5] == space):
            return var_def[0]
    return None


def make_shape_key_var_def(var_name, source_obj, key_name):
    key = get_shape_key(source_obj, key_name)
    data_path = "shape_keys." + key.path_from_id("value")
    var_def = [var_name,
               "SINGLE_PROP",
               source_obj.data,
               data_path]
    return var_def


def find_shape_key_var_def(var_defs, source_obj, key_name):
    key = get_shape_key(source_obj, key_name)
    data_path = "shape_keys." + key.path_from_id("value")
    for var_def in var_defs:
        if (len(var_def) == 4 and
            var_def[1] == "SINGLE_PROP" and
            var_def[2] == source_obj.data and
            var_def[4] == data_path):
            return var_def[0]
    return None


def get_shape_key_driver(obj, shape_key_name, drive_limit=False) -> bpy.types.Driver:
    if utils.object_mode():
        shape_key = meshutils.find_shape_key(obj, shape_key_name)
        if shape_key:
            prop = "value" if not drive_limit else "slider_max"
            data_path = f"key_blocks[\"{shape_key_name}\"].{prop}"
            for fcurve in obj.data.shape_keys.animation_data.drivers:
                if fcurve.data_path == data_path:
                    return fcurve.driver
    return None


def add_driver_var_defs(driver, var_defs):
    for var_def in var_defs:
        var : bpy.types.DriverVariable = driver.variables.new()
        var.name = var_def[0]
        var.type = var_def[1]
        if var_def[1] == "TRANSFORMS":
            var_obj = var_def[2]
            bone_name = var_def[3]
            var.targets[0].id = var_obj.id_data
            if bone_name:
                var.targets[0].bone_target = bone_name
            var.targets[0].rotation_mode = "AUTO"
            var.targets[0].transform_type = var_def[4]
            var.targets[0].transform_space = var_def[5]
        if var_def[1] == "SINGLE_PROP":
            var_obj = var_def[2]
            var.targets[0].id_type = get_id_type(var_obj)
            var.targets[0].id = var_obj.id_data
            var.targets[0].data_path = var_def[3]


def add_shape_key_driver(rig, obj, shape_key_name, driver_def, var_defs, scale=1.0, drive_limit=False):
    """driver_def = [driver_type, expression]\n
       var_def = [var_name, "TRANSFORMS", bone_name, transform_prop, space]\n
           driver_type = "SCRIPTED" or "SUM",\n
           expression = "var1 + var2" or ""\n
           transform_prop = "ROT_X"/"LOC_X"/"SCA_X" ...,\n
           space = "WORLD_SPACE", "LOCAL_SPACE" ... """
    if utils.object_mode():
        shape_key = meshutils.find_shape_key(obj, shape_key_name)
        if shape_key:
            prop = "value"
            if drive_limit:
                prop = "slider_max"
            shape_key.driver_remove(prop)
            fcurve : bpy.types.FCurve
            fcurve = shape_key.driver_add(prop)
            driver : bpy.types.Driver = fcurve.driver
            driver.type = driver_def[0]
            expression = driver_def[1]
            if driver.type == "SCRIPTED":
                if scale != 1.0:
                    driver.expression = f"({expression})*{scale}"
                else:
                    driver.expression = expression
            add_driver_var_defs(driver, var_defs)
            return driver
    return None


def add_bone_driver(rig, bone_name, driver_def, var_defs, scale=1.0):
    """driver_def = [driver_type, prop, index, expression]\n
       var_def = [var_name, "TRANSFORMS", bone_name, transform_prop, space]\n
           driver_type = "SCRIPTED" or "SUM",\n
           expression = "var1 + var2" or ""\n
           transform_prop = "ROT_X"/"LOC_X"/"SCA_X" ...,\n
           space = "WORLD_SPACE", "LOCAL_SPACE" ... """
    if utils.object_mode():
        if bone_name in rig.pose.bones:
            pose_bone: bpy.types.PoseBone = rig.pose.bones[bone_name]
            fcurve : bpy.types.FCurve
            prop = driver_def[1]
            index = driver_def[2]
            expression = driver_def[3]
            pose_bone.driver_remove(prop, index)
            fcurve = pose_bone.driver_add(prop, index)
            driver: bpy.types.Driver = fcurve.driver
            driver.type = driver_def[0]
            if driver.type == "SCRIPTED":
                if scale != 1.0:
                    driver.expression = f"({expression})*{scale}"
                else:
                    driver.expression = expression
            add_driver_var_defs(driver, var_defs)
            return driver
    return None


def add_constraint_prop_driver(rig, pose_bone_name,
                                    driver_def, var_defs,
                                    constraint=None, constraint_type=""):
    """driver_def = [driver_type, prop, index, expression]\n
       var_def = [var_name, "TRANSFORMS", bone_name, transform_prop, space]\n
           driver_type = "SCRIPTED" or "SUM",\n
           expression = "var1 + var2" or ""\n
           transform_prop = "ROT_X"/"LOC_X"/"SCA_X" ...,\n
           space = "WORLD_SPACE", "LOCAL_SPACE" ... """
    if utils.object_mode():
        if pose_bone_name in rig.pose.bones:
            driver_type = driver_def[0]
            prop = driver_def[1]
            index = driver_def[2]
            expression = driver_def[3]

            pose_bone = rig.pose.bones[pose_bone_name]
            cons = []
            if constraint:
                cons.append(constraint)
            elif constraint_type:
                for con in pose_bone.constraints:
                    if con.type == constraint_type:
                        cons.append(con)

            con: bpy.types.Constraint
            for con in cons:
                con.driver_remove(prop, index)
                if driver_type == "SCRIPTED":
                    driver = make_driver(con, prop, driver_type,
                                         driver_expression=expression, index=index)
                elif driver_type == "SUM":
                    driver = make_driver(con, prop, driver_type,
                                         index=index)
                if driver:
                    add_driver_var_defs(driver, var_defs)
                    return driver