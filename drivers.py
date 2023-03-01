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
from . import utils, vars
from rna_prop_ui import rna_idprop_ui_create


def make_driver_var(driver, var_type, var_name, target, target_type = "OBJECT", data_path = "", bone_target = "", transform_type = "", transform_space = ""):
    """
    var_type = "SINGLE_PROP", "TRANSFORMS"\n
    var_name = variable name\n
    target = target object/bone\n
    target_type = "OBJECT", "MESH"...
    target_data_path = "..."
    """
    var : bpy.types.DriverVariable = driver.variables.new()
    var.name = var_name
    if var_type == "SINGLE_PROP":
        var.type = var_type
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


def make_driver(source, prop_name, driver_type, driver_expression = ""):
    """
    prop_name = "value", "influence"\n
    driver_type = "SUM", "SCRIPTED"\n
    driver_expression = "..."
    """
    driver = None
    if source:
        fcurve : bpy.types.FCurve
        fcurve = source.driver_add(prop_name)
        driver : bpy.types.Driver = fcurve.driver
        if driver_type == "SUM":
            driver.type = driver_type
        elif driver_type == "SCRIPTED":
            driver.type = driver_type
            driver.expression = driver_expression
    return driver


def add_custom_float_property(object, prop_name, prop_value, value_min = 0, value_max = 1, overridable = True):
    rna_idprop_ui_create(object, prop_name, default=prop_value, overridable=overridable, min=value_min, max=value_max)