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
import time
from . import vars

timer = 0

def log_info(msg):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    """Log an info message to console."""
    if prefs.log_level == "ALL":
        print(msg)


def log_warn(msg):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    """Log a warning message to console."""
    if prefs.log_level == "ALL" or prefs.log_level == "WARN":
        print("Warning: " + msg)


def log_error(msg, e = None):
    """Log an error message to console and raise an exception."""
    print("Error: " + msg)
    if e is not None:
        print("    -> " + getattr(e, 'message', repr(e)))


def start_timer():
    global timer
    timer = time.perf_counter()


def log_timer(msg, unit = "s"):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    global timer
    if prefs.log_level == "ALL":
        duration = time.perf_counter() - timer
        if unit == "ms":
            duration *= 1000
        elif unit == "us":
            duration *= 1000000
        elif unit == "ns":
            duration *= 1000000000
        print(msg + ": " + str(duration) + " " + unit)


def message_box(message = "", title = "Info", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text = message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def unique_name(name, no_version = False):
    """Generate a unique name for the node or property to quickly
       identify texture nodes or nodes with parameters."""

    props = bpy.context.scene.CC3ImportProps
    if no_version:
        name = name + "_" + vars.NODE_PREFIX + str(props.node_id)
    else:
        name = vars.NODE_PREFIX + name + "_" + vars.VERSION_STRING + "_" + str(props.node_id)
    props.node_id = props.node_id + 1
    return name


def is_same_path(pa, pb):
    return os.path.normcase(os.path.realpath(pa)) == os.path.normcase(os.path.realpath(pb))


def is_in_path(pa, pb):
    return os.path.normcase(os.path.realpath(pa)) in os.path.normcase(os.path.realpath(pb))


def object_has_material(obj, name):
    name = name.lower()
    if obj.type == "MESH":
        for mat in obj.data.materials:
            if name in mat.name.lower():
                return True
    return False


def clamp(x, min = 0.0, max = 1.0):
    if x < min:
        x = min
    if x > max:
        x = max
    return x


def smoothstep(edge0, edge1, x):
    x = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return x * x * (3 - 2 * x)


def saturate(x):
    return clamp(x)


def remap(edge0, edge1, min, max, x):
    return min + ((x - edge0) * (max - min) / (edge1 - edge0))


def count_maps(*maps):
    count = 0
    for map in maps:
        if map is not None:
            count += 1
    return count
