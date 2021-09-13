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

import os
import time

import bpy

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


def still_exists(obj):
    try:
        name = obj.name
        return True
    except:
        return False


def try_remove(item, force = False):

    if still_exists(item):

        if type(item) == bpy.types.Armature:
            if (item.use_fake_user and item.users == 1) or item.users == 0 or force:
                log_info("Removing Armature: " + item.name)
                bpy.data.armatures.remove(item)
            else:
                log_info("Armature: " + item.name + " still in use!")

        elif type(item) == bpy.types.Mesh:
            if (item.use_fake_user and item.users == 1) or item.users == 0 or force:
                log_info("Removing Mesh: " + item.name)
                bpy.data.meshes.remove(item)
            else:
                log_info("Mesh: " + item.name + " still in use!")

        elif type(item) == bpy.types.Object:
            if (item.use_fake_user and item.users == 1) or item.users == 0 or force:
                log_info("Removing Object: " + item.name)
                bpy.data.objects.remove(item)
            else:
                log_info("Object: " + item.name + " still in use!")

        elif type(item) == bpy.types.Material:
            if (item.use_fake_user and item.users == 1) or item.users == 0 or force:
                log_info("Removing Material: " + item.name)
                bpy.data.materials.remove(item)
            else:
                log_info("Material: " + item.name + " still in use!")

        elif type(item) == bpy.types.Image:
            if (item.use_fake_user and item.users == 1) or item.users == 0 or force:
                log_info("Removing Image: " + item.name)
                bpy.data.images.remove(item)
            else:
                log_info("Image: " + item.name + " still in use!")

        elif type(item) == bpy.types.Texture:
            if (item.use_fake_user and item.users == 1) or item.users == 0 or force:
                log_info("Removing Texture: " + item.name)
                bpy.data.textures.remove(item)
            else:
                log_info("Texture: " + item.name + " still in use!")

        elif type(item) == bpy.types.Action:
            if (item.use_fake_user and item.users == 1) or item.users == 0 or force:
                log_info("Removing Action: " + item.name)
                bpy.data.textures.remove(item)
            else:
                log_info("Action: " + item.name + " still in use!")


def clean_collection(collection, include_fake = False):
    for item in collection:
        if (include_fake and item.use_fake_user and item.users == 1) or item.users == 0:
            collection.remove(item)


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
    if x < 0.0:
        x = 0.0
    if x > 1.0:
        x = 1.0
    return x


def remap(edge0, edge1, min, max, x):
    return min + ((x - edge0) * (max - min) / (edge1 - edge0))


def lerp(min, max, t):
    return min + (max - min) * t


def inverse_lerp(min, max, value):
    return (value - min) / (max - min)


def lerp_color(c0, c1, t):
    return (lerp(c0[0], c1[0], t),
            lerp(c0[1], c1[1], t),
            lerp(c0[2], c1[2], t),
            lerp(c0[3], c1[3], t))


def linear_to_srgbx(x):
    if x < 0.0:
        return 0.0
    elif x < 0.0031308:
        return x * 12.92
    elif x < 1.0:
        return 1.055 * pow(x, 1.0 / 2.4) - 0.055
    else:
        return pow(x, 5.0 / 11.0)


def linear_to_srgb(color):
    return (linear_to_srgbx(color[0]),
            linear_to_srgbx(color[1]),
            linear_to_srgbx(color[2]),
            color[3])


def srgb_to_linearx(x):
    if x <= 0.04045:
        return x / 12.95
    elif x < 1.0:
        return pow((x + 0.055) / 1.055, 2.4)
    else:
        return pow(x, 2.2)


def srgb_to_linear(color):
    return (srgb_to_linearx(color[0]),
            srgb_to_linearx(color[1]),
            srgb_to_linearx(color[2]),
            color[3])


def count_maps(*maps):
    count = 0
    for map in maps:
        if map is not None:
            count += 1
    return count


def dimensions(x):
    try:
        l = len(x)
        return l
    except:
        return 1
    return 1


def match_dimensions(socket, value):
    socket_dimensions = dimensions(socket)
    value_dimensions = dimensions(value)
    if socket_dimensions == 3 and value_dimensions == 1:
        return (value, value, value)
    elif socket_dimensions == 2 and value_dimensions == 1:
        return (value, value)
    else:
        return value


def context_material(context):
    try:
        return context.object.material_slots[context.object.active_material_index].material
    except:
        return None


def find_pose_bone(chr_cache, *name):
    props = bpy.context.scene.CC3ImportProps

    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
        if (obj.type == "ARMATURE"):
            for n in name:
                if n in obj.pose.bones:
                    return obj.pose.bones[n]
    return None


def find_pose_bone_in_armature(arm, *name):
    if (arm.type == "ARMATURE"):
        for n in name:
            if n in arm.pose.bones:
                return arm.pose.bones[n]
    return None


def get_active_object():
    return bpy.context.view_layer.objects.active


def set_active_object(obj):
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return bpy.context.active_object == obj


def set_mode(mode):
    if bpy.context.object == None:
        if mode != "OBJECT":
            log_error("No context object, unable to set any mode but OBJECT!")
            return False
        return True
    else:
        bpy.ops.object.mode_set(mode=mode)
        if bpy.context.object.mode != mode:
            log_error("Unable to set " + mode + " on object: " + bpy.context.object.name)
            return False
        return True


def edit_mode_to(obj):
    if set_mode("OBJECT") and set_active_object(obj) and set_mode("EDIT"):
        return True
    return False


def s2lin(x):
    a = 0.055
    if x <= 0.04045:
        y = x * (1.0/12.92)
    else:
        y = pow((x + a)*(1.0/(1 + a)), 2.4)
    return y

def lin2s(x):
    a = 0.055
    if x <= 0.0031308:
        y = x * 12.92
    else:
        y = (1 + a)*pow(x, 1/2.4) - a
    return y


# remove any .001 from the material name
def strip_name(name):
    if name[-3:].isdigit() and name[-4] == ".":
        name = name[:-4]
    return name


def tag_objects():
    for obj in bpy.data.objects:
        obj.tag = True


def untagged_objects():
    untagged = []
    for obj in bpy.data.objects:
        if obj.tag == False:
            untagged.append(obj)
        obj.tag = False
    return untagged


def tag_materials():
    for mat in bpy.data.materials:
        mat.tag = True


def untagged_materials():
    untagged = []
    for mat in bpy.data.materials:
        if mat.tag == False:
            untagged.append(mat)
        mat.tag = False
    return untagged


def tag_images():
    for img in bpy.data.images:
        img.tag = True


def untagged_images():
    untagged = []
    for img in bpy.data.images:
        if img.tag == False:
            untagged.append(img)
        img.tag = False
    return untagged


def select_all_child_objects(obj):
    if obj.type == "ARMATURE" or obj.type == "MESH":
        obj.select_set(True)
    for child in obj.children:
        select_all_child_objects(child)


def remove_from_collection(coll, item):
    for i in range(0, len(coll)):
        if coll[i] == item:
            coll.remove(i)
            return

