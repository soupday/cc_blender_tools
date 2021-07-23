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
import os
import mathutils
from . import utils



def append_node_group(path, object_name):
    for g in bpy.data.node_groups:
        g.tag = True

    filename = "_LIB.blend"
    datablock = "NodeTree"
    file = os.path.join(path, filename)
    if os.path.exists(file):
        bpy.ops.wm.append(directory=os.path.join(path, filename, datablock), filename=object_name, set_fake=False, link=False)

    appended_group = None
    for g in bpy.data.node_groups:
        if not g.tag and object_name in g.name:
            appended_group = g
            g.name = utils.unique_name(object_name)
        g.tag = False
    return appended_group


def fetch_node_group(name):

    paths = [bpy.path.abspath("//"),
             os.path.dirname(os.path.realpath(__file__)),
             ]
    for path in paths:
        utils.log_info("Trying to append: " + path + " > " + name)
        if os.path.exists(path):
            group = append_node_group(path, name)
            if group is not None:
                return group
    utils.log_error("Trying to append group: " + name + ", _LIB.blend library file not found?")
    raise ValueError("Unable to append node group from library file!")


def append_lib_image(path, object_name):
    for i in bpy.data.images:
        i.tag = True

    filename = "_LIB.blend"
    datablock = "Image"
    file = os.path.join(path, filename)
    if os.path.exists(file):
        bpy.ops.wm.append(directory=os.path.join(path, filename, datablock), filename=object_name, set_fake=False, link=False)

    appended_image = None
    for i in bpy.data.images:
        if not i.tag and object_name in i.name:
            appended_image = i
            i.name = utils.unique_name(object_name)
        i.tag = False
    return appended_image


def fetch_lib_image(name):

    paths = [bpy.path.abspath("//"),
             os.path.dirname(os.path.realpath(__file__)),
             ]
    for path in paths:
        utils.log_info("Trying to append image: " + path + " > " + name)
        if os.path.exists(path):
            image = append_lib_image(path, name)
            if image:
                return image
    utils.log_error("Trying to append image: " + name + ", _LIB.blend library file not found?")
    raise ValueError("Unable to append iamge from library file!")