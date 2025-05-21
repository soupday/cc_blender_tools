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

import os
import platform
import subprocess
import time
import difflib
import random
import re, json
import traceback
from mathutils import Vector, Quaternion, Matrix, Euler, Color
from hashlib import md5
import bpy

from . import vars

timer = 0

LOG_INDENT = 0

def log_indent():
    global LOG_INDENT
    LOG_INDENT += 3


def log_recess():
    global LOG_INDENT
    LOG_INDENT -= 3


def log_spacing():
    return " " * LOG_INDENT


def log_detail(msg):
    prefs = vars.prefs()
    """Log an info message to console."""
    if prefs.log_level == "DETAILS":
        print((" " * LOG_INDENT) + msg)


def log_info(msg):
    prefs = vars.prefs()
    """Log an info message to console."""
    if prefs.log_level == "ALL" or prefs.log_level == "DETAILS":
        print((" " * LOG_INDENT) + msg)


def log_always(msg):
    prefs = vars.prefs()
    """Log an info message to console."""
    print((" " * LOG_INDENT) + msg)


def log_warn(msg):
    prefs = vars.prefs()
    """Log a warning message to console."""
    if prefs.log_level == "ALL" or prefs.log_level == "DETAILS" or prefs.log_level == "WARN":
        print((" " * LOG_INDENT) + "Warning: " + msg)


def log_error(msg, e: Exception = None):
    """Log an error message to console and raise an exception."""
    indent = LOG_INDENT
    if indent > 1: indent -= 1
    print("*" + (" " * indent) + "Error: " + msg)
    if e is not None:
        print("    -> " + getattr(e, 'message', repr(e)))
        print("Stack Trace: ")
        traceback.print_exc()



def start_timer():
    global timer
    timer = time.perf_counter()


def log_timer(msg, unit = "s"):
    prefs = vars.prefs()
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


def update_ui(context = None, area_type="VIEW_3D", region_type="UI", all=False):
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == area_type or all:
                for region in area.regions:
                    if region.type == region_type or all:
                        region.tag_redraw()


def report_multi(op, icon = 'INFO', messages = None):
    if messages:
        text = ""
        for msg in messages:
            text += msg + " \n"
        if text:
            op.report({icon}, text)


def message_box_multi(title = "Info", icon = 'INFO', messages = None):
    def draw(self, context):
        if messages:
            for message in messages:
                self.layout.label(text = message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def unique_name(name, no_version = False):
    """Generate a unique name for the node or property to quickly
       identify texture nodes or nodes with parameters."""

    props = vars.props()
    if no_version:
        name = name + "_" + vars.NODE_PREFIX + str(props.node_id)
    else:
        name = vars.NODE_PREFIX + name + "_" + vars.VERSION_STRING + "_" + str(props.node_id)
    props.node_id = props.node_id + 1
    return name


def set_ccic_id(obj: bpy.types.Object):
    props = vars.props()
    obj["ccic_id"] = vars.VERSION_STRING + "_" + str(props.node_id)
    props.node_id = props.node_id + 1


def has_ccic_id(obj: bpy.types.Object):
    if "ccic_id" in obj:
        return True
    if vars.NODE_PREFIX in obj.name:
        return True
    return False


def deduplicate_names(names: list, func=None, replace: dict=None, partial=False):
    totals = {}
    name: str = None
    for i, name in enumerate(names):
        if replace:
            if partial:
                for r in replace:
                    if r in name:
                        name = name.replace(r, replace[r])
                        break
            elif name in replace:
                name = replace[name]
        if func:
            name = func(name)
        if name in totals:
            count = totals[name]
        else:
            count = 0
            totals[name] = 0
        names[i] = name if count == 0 else f"{name}.{count:03d}"
        totals[name] += 1
    return names


def obj_is_linked(obj):
    try:
        if obj.library is not None:
            return True
    except: ...
    return False


def obj_is_override(obj):
    try:
        if obj.override_library is not None:
            return True
    except: ...
    return False


def unique_material_name(name, mat=None, start_index=1):
    name = strip_name(name)
    index = start_index
    if name in bpy.data.materials and bpy.data.materials[name] != mat:
        while name + "_" + str(index).zfill(2) in bpy.data.materials:
            index += 1
        return name + "_" + str(index).zfill(2)
    return name


def unique_image_name(name, image=None, start_index=1):
    name = strip_name(name)
    index = start_index
    if name in bpy.data.images and bpy.data.images[name] != image:
        while name + "_" + str(index).zfill(2) in bpy.data.images:
            index += 1
        return name + "_" + str(index).zfill(2)
    return name


def unique_object_name(name, obj=None, capitalize=False, start_index=1, suffix=""):
    name = strip_name(name)
    if capitalize:
        name = name.capitalize()
    if suffix:
        suffix = "_" + suffix
    try_name = name + suffix
    if try_name in bpy.data.objects and bpy.data.objects[try_name] != obj:
        index = start_index
        try_name = name + str(index).zfill(2) + suffix
        while try_name in bpy.data.objects:
            index += 1
            try_name = name + str(index).zfill(2) + suffix
    return try_name


def un_suffix_name(name):
    """Removes any combination of numerical suffixes from the end of a string"""
    base_name = re.sub("([._+|/\,]\d+)*$", "", name)
    return base_name


def is_same_path(pa, pb):
    try:
        if pa and pb:
            return os.path.normpath(os.path.realpath(pa)) == os.path.normpath(os.path.realpath(pb))
        else:
            return False
    except:
        return False


def is_in_path(a, b):
    """Is path a in path b"""
    try:
        if a and b:
            return os.path.normpath(os.path.realpath(a)) in os.path.normpath(os.path.realpath(b))
        else:
            return False
    except:
        return False


def path_is_parent(parent_path, child_path):
    try:
        parent_path = os.path.abspath(parent_path)
        child_path = os.path.abspath(child_path)
        return os.path.commonpath([parent_path]) == os.path.commonpath([parent_path, child_path])
    except:
        return False


def local_repath(path, original_start):
    """Takes the path relative to the original_start and makes
       it relative to the blend file location instead.
       Returns the full path."""
    rel_path = relpath(path, original_start)
    return os.path.normpath(bpy.path.abspath(f"//{rel_path}"))


def local_path(path = ""):
    """Get the full path of <path> relative to the blend file. Returns empty if no blend file path."""
    if bpy.path.abspath("//"):
        abs_path = bpy.path.abspath(f"//{path}")
        return os.path.normpath(abs_path)
    else:
        return ""


def blend_file_name():
    file_path = bpy.data.filepath
    name = ""
    if file_path:
        folder, file = os.path.split(file_path)
        name, ext = os.path.splitext(file)
    return name


def relpath(path, start):
    try:
        return os.path.relpath(path, start)
    except ValueError:
        return os.path.abspath(path)


def search_up_path(path, folder):
    path = os.path.normpath(path)
    dir : str = os.path.dirname(path)
    if dir == path or dir == "" or dir is None:
        return ""
    elif dir.lower().endswith(os.path.sep + folder.lower()):
        return dir
    return search_up_path(dir, folder)


def object_has_material(obj, name):
    name = name.lower()
    if obj.type == "MESH":
        for mat in obj.data.materials:
            if mat and name in mat.name.lower():
                return True
    return False


def object_exists_is_empty(obj):
    """Test if Object: obj still exists as an object in the scene, and is an empty."""
    if obj is None:
        return False
    try:
        name = obj.name
        return len(obj.users_scene) > 0 and obj.type == "EMPTY"
    except:
        return False


def object_exists_is_mesh(obj):
    """Test if Object: obj still exists as an object in the scene, and is a mesh."""
    if obj is None:
        return False
    try:
        name = obj.name
        return len(obj.users_scene) > 0 and obj.type == "MESH"
    except:
        return False


def object_exists_is_armature(obj) -> bool:
    """Test if Object: obj still exists as an object in the scene, and is an armature."""
    if obj is None:
        return False
    try:
        name = obj.name
        return len(obj.users_scene) > 0 and obj.type == "ARMATURE"
    except:
        return False


def object_exists_is_light(obj):
    """Test if Object: obj still exists as an object in the scene, and is a light."""
    if obj is None:
        return False
    try:
        name = obj.name
        return len(obj.users_scene) > 0 and obj.type == "LIGHT"
    except:
        return False


def object_exists_is_camera(obj):
    """Test if Object: obj still exists as an object in the scene, and is a camera."""
    if obj is None:
        return False
    try:
        name = obj.name
        return len(obj.users_scene) > 0 and obj.type == "CAMERA"
    except:
        return False


def object_exists(obj: bpy.types.Object):
    """Test if Object: obj still exists as an object in the scene."""
    if obj is None:
        return False
    try:
        name = obj.name
        return len(obj.users_scene) > 0
    except:
        return False


def material_exists(mat: bpy.types.Material):
    """Test if material still exists."""
    if mat is None:
        return False
    try:
        name = mat.name
        return True
    except:
        return False


def image_exists(img: bpy.types.Image):
    """Test if material still exists."""
    if img is None:
        return False
    try:
        name = img.name
        return True
    except:
        return False


def purge_image(img: bpy.types.Image):
    if image_exists(img):
        users = img.users - (1 if img.use_extra_user else 0)
        if users <= 0:
            bpy.data.images.remove(img)


def get_selected_mesh():
    if object_exists_is_mesh(get_active_object()):
        return get_active_object()
    elif bpy.context.selected_objects:
        for obj in bpy.context.selected_objects:
            if object_exists_is_mesh(obj):
                return obj
    return None


def get_selected_meshes(context = None):
    """Gets selected meshes and includes any current context mesh"""
    objects = [ obj for obj in bpy.context.selected_objects if object_exists_is_mesh(obj) ]
    if context and context.object:
        if object_exists_is_mesh(context.object):
            if context.object not in objects:
                objects.append(context.object)
    return objects


def get_selected_armatures(context = None):
    """Gets selected armatures and includes any current context armature"""
    objects = [ obj for obj in bpy.context.selected_objects if object_exists_is_armature(obj) ]
    if context and context.object:
        if object_exists_is_armature(context.object):
            if context.object not in objects:
                objects.append(context.object)
    return objects


def safe_remove(item, force = False):

    if object_exists(item):

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
    cleaned = False
    for item in collection:
        if (include_fake and item.use_fake_user and item.users == 1) or item.users == 0:
            log_detail(f"Clean Collection Removing: {item}")
            collection.remove(item)
            cleaned = True
    return cleaned


def clean_up_unused():
    clean_collection(bpy.data.images)
    clean_collection(bpy.data.materials)
    clean_collection(bpy.data.textures)
    clean_collection(bpy.data.meshes)
    clean_collection(bpy.data.armatures)
    # as some node_groups are nested...
    while clean_collection(bpy.data.node_groups):
        clean_collection(bpy.data.node_groups)


def same_sign(a, b):
    if a < 0 and b < 0:
        return True
    if a > 0 and b > 0:
        return True
    return False


def sign(a):
    if a >= 0:
        return 1
    return -1


def clamp(x, min = 0.0, max = 1.0):
    if x < min:
        x = min
    if x > max:
        x = max
    return x


def smoothstep(edge0, edge1, x):
    x = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return x * x * (3 - 2 * x)


def map_smoothstep(edge0, edge1, value0, value1, x):
    if edge1 == edge0:
        return value1
    x = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    t = x * x * (3 - 2 * x)
    return value0 + (value1 - value0) * t


def saturate(x):
    if x < 0.0:
        x = 0.0
    if x > 1.0:
        x = 1.0
    return x


def remap(from_min, from_max, to_min, to_max, x):
    return to_min + ((x - from_min) * (to_max - to_min) / (from_max - from_min))


def lerp(v0, v1, t, clamp=True):
    if clamp:
        t = max(0, min(1, t))
    l = v0 + (v1 - v0) * t
    return l


def inverse_lerp(vmin, vmax, value):
    return min(1.0, max(0.0, (value - vmin) / (vmax - vmin)))


def lerp_color(c0, c1, t):
    if len(c0) == 4:
        r = (lerp(c0[0], c1[0], t),
            lerp(c0[1], c1[1], t),
            lerp(c0[2], c1[2], t),
            lerp(c0[3], c1[3], t))
    else:
        r = (lerp(c0[0], c1[0], t),
            lerp(c0[1], c1[1], t),
            lerp(c0[2], c1[2], t))
    return r


def inverse_lerp_color(min, max, value):
    return (inverse_lerp(min[0], max[0], value[0]),
            inverse_lerp(min[1], max[1], value[1]),
            inverse_lerp(min[2], max[2], value[2]),
            inverse_lerp(min[3], max[3], value[3]))


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
    if len(color) == 4:
        return (linear_to_srgbx(color[0]),
                linear_to_srgbx(color[1]),
                linear_to_srgbx(color[2]),
                color[3])
    else:
        return (linear_to_srgbx(color[0]),
                linear_to_srgbx(color[1]),
                linear_to_srgbx(color[2]))

def srgb_to_linearx(x):
    if x <= 0.04045:
        return x / 12.95
    elif x < 1.0:
        return pow((x + 0.055) / 1.055, 2.4)
    else:
        return pow(x, 2.2)


def srgb_to_linear(color):
    if len(color) == 4:
        return (srgb_to_linearx(color[0]),
                srgb_to_linearx(color[1]),
                srgb_to_linearx(color[2]),
                color[3])
    else:
        return (srgb_to_linearx(color[0]),
                srgb_to_linearx(color[1]),
                srgb_to_linearx(color[2]))


def count_maps(*maps):
    count = 0
    for map in maps:
        if map is not None:
            count += 1
    return count


def key_count(obj: bpy.types.Object):
    if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
        return len(obj.data.shape_keys.key_blocks)
    return 0


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


def find_pose_bone(chr_cache, *name):
    props = vars.props()

    arm = chr_cache.get_armature()
    for n in name:
        if n in arm.pose.bones:
            return arm.pose.bones[n]
    return None


def find_pose_bone_in_armature(arm, *name):
    if (arm.type == "ARMATURE"):
        for n in name:
            if n in arm.pose.bones:
                return arm.pose.bones[n]
    return None


def find_edit_bone_in_armature(arm, *name):
    if (arm.type == "ARMATURE"):
        for n in name:
            if n in arm.data.edit_bones:
                return arm.data.edit_bones[n]
    return None


def get_active_object():
    """Return the actual active object and not the context reference."""
    try:
        if bpy.context.active_object:
            return bpy.data.objects[bpy.context.active_object.name]
    except:
        pass
    return None


def get_active_view_layer_object():
    return bpy.context.view_layer.objects.active


def set_active_object(obj, deselect_all = False):
    try:
        if deselect_all:
            bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        return (bpy.context.active_object == obj)
    except:
        return False

def set_only_active_object(obj):
    return set_active_object(obj, True)


def set_mode(mode):
    try:
        if bpy.context.object == None:
            if mode != "OBJECT":
                log_error("No context object, unable to set any mode but OBJECT!")
                return False
            return True
        else:
            if bpy.context.object.mode != mode:
                bpy.ops.object.mode_set(mode=mode)
                if bpy.context.object.mode != mode:
                    log_error("Unable to set " + mode + " on object: " + bpy.context.object.name)
                    return False
            return True
    except:
        return False


def get_mode():
    try:
        return bpy.context.object.mode
    except:
        return "OBJECT"


def is_selected_and_active(obj):
    return get_active_object() == obj and obj in bpy.context.selected_objects


def is_only_selected_and_active(obj):
    return (get_active_object() == obj and
            obj in bpy.context.selected_objects and
            len(bpy.context.selected_objects) == 1)


def edit_mode_to(obj, only_this = False):
    if object_exists(obj):
        if only_this and not is_only_selected_and_active(obj):
            set_only_active_object(obj)
        if is_selected_and_active(obj) and get_mode() == "EDIT":
            return True
        else:
            if set_mode("OBJECT") and set_active_object(obj) and set_mode("EDIT"):
                return True
    return False


def object_mode():
    return set_mode("OBJECT")


def object_mode_to(obj):
    if object_exists(obj):
        if get_mode() == "OBJECT" and get_active_object() == obj:
            return True
        if set_mode("OBJECT"):
            if try_select_object(obj):
                if set_active_object(obj):
                    return True
    return False


def pose_mode_to(arm):
    if object_exists_is_armature(arm):
        if get_mode() == "POSE" and get_active_object() == arm:
            return True
        if object_mode_to(arm):
            if set_mode("POSE"):
                return True
    return False


def duplicate_object(obj, include_action=False) -> bpy.types.Object:
    if object_exists(obj) and set_mode("OBJECT"):
        if try_select_object(obj, True) and set_active_object(obj):

            obj_action = None
            shape_key_action = None

            # store existing actions
            obj_action = safe_get_action(obj)
            if not include_action:
                safe_set_action(obj, None, create=False)
            if obj.type == "MESH":
                shape_key_action = safe_get_action(obj.data.shape_keys)
                if not include_action:
                    safe_set_action(obj.data.shape_keys, None, create=False)

            # duplicate object
            bpy.ops.object.duplicate()

            # restore non-duplicated actions
            if not include_action:
                if shape_key_action:
                    safe_set_action(obj.data.shape_keys, shape_key_action)
                if obj_action:
                    safe_set_action(obj, obj_action)

            return get_active_object()
    return None


def remove_all_shape_keys(obj: bpy.types.Object):
    # Bugged in Blender 4.4 (Maybe other versions too) - reverting to operators
    #if obj and obj.data.shape_keys and obj.data.shape_keys.key_blocks:
    #    key: bpy.types.ShapeKey = None
    #    keys = [key for key in obj.data.shape_keys.key_blocks]
    #    keys.reverse() # make sure basis is last to be removed...
    #    for key in keys:
    #        obj.shape_key_remove(key)
    if obj and obj.data.shape_keys and obj.data.shape_keys.key_blocks:
        sms = store_mode_selection_state()
        set_active_object(obj, True)
        bpy.ops.object.shape_key_remove(all=True, apply_mix=False)
        restore_mode_selection_state(sms)


def force_object_name(obj, name):
    if name in bpy.data.objects:
        existing = bpy.data.objects[name]
        if existing != obj:
            old_name = obj.name
            rnd_id = generate_random_id(10)
            existing.name = existing.name + "_" + rnd_id
            obj.name = name
            existing.name = old_name
    else:
        obj.name = name


def force_mesh_name(mesh, name):
    if name in bpy.data.meshes:
        existing = bpy.data.meshes[name]
        if existing != mesh:
            old_name = mesh.name
            rnd_id = generate_random_id(10)
            existing.name = existing.name + "_" + rnd_id
            mesh.name = name
            existing.name = old_name
    else:
        mesh.name = name


def force_armature_name(arm, name):
    if name in bpy.data.armatures:
        existing = bpy.data.armatures[name]
        if existing != arm:
            old_name = arm.name
            rnd_id = generate_random_id(10)
            existing.name = existing.name + "_" + rnd_id
            arm.name = name
            existing.name = old_name
    else:
        arm.name = name


def force_material_name(mat, name):
    if name in bpy.data.materials:
        existing = bpy.data.materials[name]
        if existing != mat:
            old_name = mat.name
            rnd_id = generate_random_id(10)
            existing.name = existing.name + "_" + rnd_id
            mat.name = name
            existing.name = old_name
    else:
        mat.name = name


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


def strip_name(name: str):
    """Remove any .001 from the material name"""
    if len(name) >= 4:
        if name[-4] == "." and name[-3:].isdigit():
            name = name[:-4]
    return name


def deduplicate_name(name: str):
    """Remove any _01 from the material name"""
    if len(name) >= 3:
        if name[-3] == "_" and name[-2:].isdigit():
            name = name[:-3]
    return name


def source_name(name):
    return strip_name(deduplicate_name(name))


def is_same_source_name(name1, name2):
    return source_name(name1) == source_name(name2)


def names_to_list(names: str, delim: str = "|") -> list:
    name_list = None
    if names:
        split = names.strip().split(delim)
        for s in split:
            s = s.strip()
            if s:
                if name_list is None:
                    name_list = []
                name_list.append(s)
    return name_list


def get_auto_index_suffix(name):
    auto_index = 0
    try:
        if type(name) is not str:
            name = name.name
        if name[-4] == "|" and name[-3:].isdigit():
            auto_index = int(name[-3:])
        elif name[-5] == "|" and name[-4:].isdigit():
            auto_index = int(name[-4:])
    except:
        pass
    return auto_index


def is_blender_duplicate(name):
    if len(name) >= 4:
        if (name[-1:].isdigit() and
            name[-2:].isdigit() and
            name[-3:].isdigit() and
            name[-4] == "."):
            return True
    return False


def get_duplication_suffix(name):
    if len(name) >= 4:
        if (name[-1:].isdigit() and
            name[-2:].isdigit() and
            name[-3:].isdigit() and
            name[-4] == "."):
            return int(name[-3:])
    return 0


def make_unique_name_in(name, keys):
    """"""
    if name in keys:
        i = 1
        while name + "_" + str(i) in keys:
            i += 1
        return name + "_" + str(i)
    return name


def partial_match(text, search, start = 0):
    """Action names can be truncated so sometimes we have to fall back on partial name matches."""
    if text and search:
        ls = len(search)
        lt = len(text)
        if start > -1 and lt > start:
            if text[start:] == search:
                return True
            j = 0
            for i in range(start, min(start + ls, lt)):
                if text[i] != search[j]:
                    return False
                j += 1
            return True
    return False


def get_longest_alpha_match(a : str, b : str):
    match = difflib.SequenceMatcher(lambda x: x in " 0123456789", a, b).find_longest_match()
    if match[2] == 0:
        return ""
    else:
        return a[match[0]:(match[0] + match[2])]


def get_common_name(names):
    common_name = names[0]
    for i in range(1, len(names)):
        common_name = get_longest_alpha_match(common_name, names[i])
    while common_name[-1] in "_0123456789":
        common_name = common_name[:-1]
    return common_name


def get_dot_file_ext(ext):
    try:
        if ext[0] == ".":
            return ext.lower()
        else:
            return f".{ext}".lower()
    except:
        return ""


def get_file_ext(ext):
    try:
        if ext[0] == ".":
            return ext[1:].lower()
        else:
            return ext.lower()
    except:
        return ""


def is_file_ext(test, ext):
    try:
        if ext[0] == ".":
            ext = ext[1:]
        if test[0] == ".":
            test = test[1:]
        return test.lower() == ext.lower()
    except:
        return False


def get_set(collection) -> set:
    return set(collection)


def get_set_new(collection, old: set) -> list:
    current = get_set(collection)
    return list(current - old)


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
        if mat:
            mat.tag = True


def untagged_materials():
    untagged = []
    for mat in bpy.data.materials:
        if mat and mat.tag == False:
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


def tag_actions():
    for action in bpy.data.actions:
        action.tag = True


def untagged_actions():
    untagged = []
    for action in bpy.data.actions:
        if action.tag == False:
            untagged.append(action)
        action.tag = False
    return untagged


def try_select_child_objects(obj):
    try:
        if obj:
            if obj.type == "ARMATURE" or obj.type == "MESH" or obj.type == "EMPTY":
                obj.select_set(True)
            result = True
            for child in obj.children:
                if not try_select_child_objects(child):
                    result = False
            return result
        else:
            return False
    except:
        return False


def add_child_objects(obj, objects, follow_armatures=False, of_type=None):
    for child in obj.children:
        if child not in objects:
            if child.type == "ARMATURE" and not follow_armatures:
                continue
            if not of_type or child.type == of_type:
                objects.append(child)
            if child.children:
                add_child_objects(child, objects, follow_armatures, of_type)


def expand_with_child_objects(objects, follow_armatures=False, of_type=None):
    for obj in objects:
        if obj.type == "ARMATURE" and not follow_armatures:
            continue
        add_child_objects(obj, objects, follow_armatures, of_type)


def get_child_objects(obj, include_parent=False, follow_armatures=False, of_type=None):
    objects = []
    if include_parent:
        if not of_type or obj.type == of_type:
            objects.append(obj)
    add_child_objects(obj, objects, follow_armatures, of_type)
    return objects


def try_select_object(obj, clear_selection = False):
    if clear_selection:
        clear_selected_objects()
    try:
        obj.select_set(True)
        return True
    except:
        return False


def try_select_objects(objects, clear_selection = False, object_type = None, make_active = False):
    if clear_selection:
        clear_selected_objects()
    result = True
    for obj in objects:
        if object_type and obj.type != object_type:
            continue
        if not try_select_object(obj):
            result = False
        else:
            if make_active:
                bpy.context.view_layer.objects.active = obj
    return result


def clear_selected_objects():
    try:
        bpy.ops.object.select_all(action='DESELECT')
        return True
    except:
        return False


def get_armature(name):
    if (name in bpy.data.armatures and
        name in bpy.data.objects and
        bpy.data.objects[name].data == bpy.data.armatures[name] and
        object_exists_is_armature(bpy.data.objects[name])):
        return bpy.data.objects[name]
    return None


def create_reuse_armature(name):
    if name in bpy.data.armatures:
        bpy.data.armatures.remove(bpy.data.armatures[name])
    if name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.armatures[name])
    arm = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new(name, arm)
    bpy.context.collection.objects.link(obj)
    return obj


def get_armature_from_objects(objects):
    armatures = get_armatures_from_objects(objects)
    return get_topmost_object(armatures)


def get_armatures_from_objects(objects):
    armatures = []
    if objects:
        for obj in objects:
            arm = get_armature_from_object(obj)
            if arm and arm not in armatures:
                armatures.append(arm)
    return armatures


def get_armature_from_object(obj):
    arm = None
    if obj.type == "ARMATURE":
        arm = obj
    elif obj.type == "MESH" and obj.parent and obj.parent.type == "ARMATURE":
        arm = obj.parent
    return arm


def is_child_of(obj, test):
    """Returns True if obj is a child or sub-child of test"""
    while test.parent:
        if test.parent == obj:
            return True
        test = test.parent
    return False


def get_topmost_object(objects):
    if not objects:
        return None
    if len(objects) == 1:
        return objects[0]
    else:
        for obj in objects:
            for test in objects:
                if obj != test:
                    if not is_child_of(obj, test):
                        return obj
    return None


def float_equals(a, b):
    return abs(a - b) < 0.00001


def array_to_vector(arr):
    if len(arr) == 3:
        return Vector((arr[0], arr[1], arr[2]))
    return Vector()


def array_to_color(arr, to_srgb=False, to_linear=False):
    if len(arr) == 1:
        r = g = b = arr[0]
        a = 1
    elif len(arr) == 2:
        r = arr[0]
        g = arr[1]
        b = 0
        a = 1
    elif len(arr) == 3:
        r = arr[0]
        g = arr[1]
        b = arr[2]
        a = 1
    elif len(arr) == 4:
        r = arr[0]
        g = arr[1]
        b = arr[2]
        a = arr[3]
    if to_srgb:
        return Color((linear_to_srgbx(r), linear_to_srgbx(g), linear_to_srgbx(b)))
    elif to_linear:
        return Color((srgb_to_linearx(r), srgb_to_linearx(g), srgb_to_linearx(b)))
    else:
        return Color((r,g,b))


def color_filter(color: Color, filter: Color):
    cf = Color((color.r * filter.r, color.g * filter.g, color.b * filter.b))
    if cf.v < 0.001:
        return color
    return cf * (color.v / cf.v)


def array_to_quaternion(arr):
    if len(arr) == 4:
        return Quaternion((arr[3], arr[0], arr[1], arr[2]))
    return Quaternion()


def strip_cc_base_name(name):
    obj_name = strip_name(name.strip())
    if obj_name.startswith("CC_Base_") or obj_name.startswith("CC_Game_"):
        obj_name = obj_name[8:]
    return obj_name


def remove_from_collection(coll, item):
    for i in range(0, len(coll)):
        if coll[i] == item:
            coll.remove(i)
            return


def delete_armature_object(arm):
    if object_exists_is_armature(arm):
        data = arm.data
        bpy.data.objects.remove(arm)
        if data:
            bpy.data.armatures.remove(data)


def delete_mesh_object(obj):
    if object_exists_is_mesh(obj):
        data = obj.data
        bpy.data.objects.remove(obj)
        if data:
            bpy.data.meshes.remove(data)


def delete_light_object(obj):
    if object_exists_is_light(obj):
        data = obj.data
        bpy.data.objects.remove(obj)
        if data:
            bpy.data.lights.remove(data)


def delete_objects(objects, log=False):
    if objects:
        for obj in objects:
            if log:
                log_info(f" - Deleting object: {obj.name}")
            delete_object(obj)


def delete_object(obj):
    if object_exists(obj):
        try:
            data = obj.data
        except:
            data = None
        if data:
            if obj.type == "MESH":
                try:
                    bpy.data.meshes.remove(data)
                except:
                    pass
            elif obj.type == "ARMATURE":
                try:
                    bpy.data.armatures.remove(data)
                except:
                    pass
            elif obj.type == "LIGHT":
                try:
                    bpy.data.lights.remove(data)
                except:
                    pass
            elif obj.type == "CAMERA":
                try:
                    bpy.data.camera.remove(data)
                except:
                    pass
            elif obj.type == "CURVE" or obj.type=="SURFACE" or obj.type == "FONT":
                try:
                    bpy.data.curves.remove(data)
                except:
                    pass
            elif obj.type == "META":
                try:
                    bpy.data.metaballs.remove(data)
                except:
                    pass
            elif obj.type == "VOLUME":
                try:
                    bpy.data.volumes.remove(data)
                except:
                    pass
            elif obj.type == "GPENCIL":
                try:
                    bpy.data.grease_pencils.remove(data)
                except:
                    pass
            elif obj.type == "LATICE":
                try:
                    bpy.data.lattices.remove(data)
                except:
                    pass
            elif obj.type == "EMPTY":
                try:
                    if obj.data:
                        if obj.data.type == "IMAGE":
                            bpy.data.images.remove(data)
                except:
                    pass
            elif obj.type == "LIGHT_PROBE":
                try:
                    bpy.data.lightprobes.remove(data)
                except:
                    pass
            elif obj.type == "SPEAKER":
                try:
                    bpy.data.speakers.remove(data)
                except:
                    pass
        try:
            bpy.data.objects.remove(obj)
        except:
            pass


def get_object_tree(obj, objects = None):
    if objects is None:
        objects = []
    if object_exists(obj):
        objects.append(obj)
        for child_obj in obj.children:
            get_object_tree(child_obj, objects)
    return objects


def delete_object_tree(obj):
    objects = get_object_tree(obj)
    for obj in objects:
        delete_object(obj)


def hide_tree(obj, hide=True, render=False):
    objects = get_object_tree(obj)
    for obj in objects:
        try:
            obj.hide_set(hide)
            if render:
                obj.hide_render = hide
        except: ...


def hide(obj: bpy.types.Object, hide=True, render=False):
    try:
        obj.hide_set(hide)
        if render:
            obj.hide_render = hide
        return True
    except:
        return False


def unhide(obj):
    # TODO expand this to force visible in tmp collection if unable to make visible with hide_set
    # but will require something to remove tmp collection later...
    return hide(obj, hide=False)


def get_context_area(context, area_type):
    if context is None:
        context = bpy.context
    for area in context.screen.areas:
        if area.type == area_type:
            return area
    return None


def get_context_mesh(context=None):
    if context is None:
        context = bpy.context
    if object_exists_is_mesh(context.object):
        return context.object
    return None


def get_context_material(context=None):
    if context is None:
        context = bpy.context
    try:
        return context.object.material_slots[context.object.active_material_index].material
    except:
        return None


def get_context_armature(context):
    if context.object:
        if object_exists_is_armature(context.object):
            return context.object
        try:
            arm = context.object.parent
            if object_exists_is_armature(arm):
                return arm
        except:
            pass
    return None


def get_context_character(context, strict=False):
    """strict: selected must part of the character"""
    props = vars.props()
    if not context:
        context = bpy.context
    chr_cache = props.get_context_character_cache(context)

    obj = context.object
    mat = get_context_material(context)
    obj_cache = None
    mat_cache = None

    if chr_cache:
        obj_cache = chr_cache.get_object_cache(obj)
        mat_cache = chr_cache.get_material_cache(mat)
        arm = chr_cache.get_armature()

        # if the context object is an armature or child of armature that is not part of this chr_cache
        # clear the chr_cache, as this is a separate generic character.
        if obj and not obj_cache:
            if not chr_cache.is_related_object(obj):
                if obj.type == "ARMATURE" and obj != arm:
                    chr_cache = None
                elif obj.type == "MESH" and obj.parent and obj.parent != arm:
                    chr_cache = None

    # if strict only return chr_cache from valid object_cache context object
    # otherwise it could return the first and only chr_cache
    if strict and (not obj or not obj_cache):
        chr_cache = None

    return chr_cache, obj, mat, obj_cache, mat_cache


def get_current_tool_idname(context = None):
    if context is None:
        context = bpy.context
    tool_idname = context.workspace.tools.from_space_view3d_mode(context.mode).idname
    return tool_idname


def add_layer_collections(layer_collection: bpy.types.LayerCollection, layer_collections, search = None):
    if search:
        if type(search) is str and search in layer_collection.name:
            layer_collections.append(layer_collection)
        elif type(search) is bpy.types.Collection and layer_collection.collection == search:
            layer_collections.append(layer_collection)
        elif type(search) is bpy.types.LayerCollection and layer_collection == search:
            layer_collections.append(layer_collection)
    else:
        layer_collections.append(layer_collection)
    child_layer_collection : bpy.types.LayerCollection
    for child_layer_collection in layer_collection.children:
        add_layer_collections(child_layer_collection, layer_collections, search)


def get_view_layer_collections(search=None):
    layer_collections = []
    for view_layer in bpy.context.scene.view_layers:
        for layer_collection in view_layer.layer_collection.children:
            add_layer_collections(layer_collection, layer_collections, search)
    return layer_collections


# C.scene.view_layers[0].layer_collection.children[0].exclude
def limit_view_layer_to_collection(collection_name, *items):
    layer_collections = []
    to_hide = []
    # exclude all active layer collections
    for view_layer in bpy.context.scene.view_layers:
        layer_collection : bpy.types.LayerCollection
        for layer_collection in view_layer.layer_collection.children:
            if not layer_collection.exclude:
                for obj in layer_collection.collection.objects:
                    if not obj.visible_get():
                        to_hide.append(obj)
                layer_collections.append(layer_collection)
                layer_collection.exclude = True
    # add a new collection just for these items
    tmp_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(tmp_collection)
    for item in items:
        if item:
            if type(item) is list:
                for sub_item in item:
                    tmp_collection.objects.link(sub_item)
                    unhide(sub_item)
            else:
                tmp_collection.objects.link(item)
                unhide(item)
    # return the temp collection and the layers exlcuded
    return tmp_collection, layer_collections, to_hide


def create_collection(name, existing=True, parent_collection: bpy.types.Collection = None):
    if name in bpy.data.collections and existing:
        return bpy.data.collections[name]
    else:
        collection = bpy.data.collections.new(name)
        if parent_collection:
            parent_collection.children.link(collection)
        else:
            bpy.context.scene.collection.children.link(collection)
        return collection


def restore_limited_view_layers(tmp_collection, layer_collections, to_hide):
    objects = []
    for obj in tmp_collection.objects:
        objects.append(obj)
    for obj in objects:
        tmp_collection.objects.unlink(obj)
    bpy.context.scene.collection.children.unlink(tmp_collection)
    bpy.data.collections.remove(tmp_collection)
    for layer_collection in layer_collections:
        layer_collection.exclude = False
    for obj in to_hide:
        hide(obj)


def force_visible_in_scene(collection_name, *objects):
    tmp_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(tmp_collection)
    for obj in objects:
        if not obj.visible_get():
            log_info(f"Object: {obj.name} is not visible or in a hidden collection. Linking to temporary root collection and making visible.")
            unhide(obj)
            tmp_collection.objects.link(obj)
    return tmp_collection


def restore_visible_in_scene(tmp_collection : bpy.types.Collection):
    objects = []
    for obj in tmp_collection.objects:
        objects.append(obj)
    for obj in objects:
        log_info(f"Object: {obj.name} Unlinking from temporary root collection and hiding.")
        hide(obj)
        tmp_collection.objects.unlink(obj)
    bpy.context.scene.collection.children.unlink(tmp_collection)
    bpy.data.collections.remove(tmp_collection)


def get_object_scene_collections(obj, exclude_rbw = True):
    collections = []
    if obj.name in bpy.context.scene.collection.objects:
        collections.append(bpy.context.scene.collection)
    rbw = bpy.context.scene.rigidbody_world
    for col in bpy.data.collections:
        # exclude rigid body world collections
        if exclude_rbw and rbw and (col == rbw.collection or col == rbw.constraints):
            continue
        if col != bpy.context.scene.collection and obj.name in col.objects:
            collections.append(col)
    return collections


def get_all_scene_collections(exclude_rbw = True):
    collections = []
    collections.append(bpy.context.scene.collection)
    rbw = bpy.context.scene.rigidbody_world
    for col in bpy.data.collections:
        # exclude rigid body world collections
        if exclude_rbw and rbw and (col == rbw.collection or col == rbw.constraints):
            continue
        if col != bpy.context.scene.collection:
            collections.append(col)
    return collections


def remove_from_scene_collections(obj, collections = None, exclude_rbw = True):
    if collections is None:
        collections = get_all_scene_collections()
    rbw = bpy.context.scene.rigidbody_world
    for col in collections:
        # exclude rigid body world collections
        if exclude_rbw and rbw and (col == rbw.collection or col == rbw.constraints):
            continue
        if obj.name in col.objects:
            col.objects.unlink(obj)


def move_object_to_scene_collections(obj, collections, exclude_rbw = True):
    remove_from_scene_collections(obj)
    rbw = bpy.context.scene.rigidbody_world
    for col in collections:
        # exclude rigid body world collections
        if exclude_rbw and rbw and (col == rbw.collection or col == rbw.constraints):
            continue
        if obj.name not in col.objects:
            col.objects.link(obj)


def store_mode_selection_state():
    mode = get_mode()
    active = get_active_object()
    selection = bpy.context.selected_objects.copy()
    return [mode, active, selection,
            (bpy.context.scene.frame_current, bpy.context.scene.frame_start, bpy.context.scene.frame_end)]


def restore_mode_selection_state(store, include_frames=True):
    try:
        set_mode("OBJECT")
        try_select_objects(store[2], True)
        set_active_object(store[1])
        set_mode(store[0])
        if include_frames:
            bpy.context.scene.frame_current = store[3][0]
            bpy.context.scene.frame_start = store[3][1]
            bpy.context.scene.frame_end = store[3][2]
    except:
        pass


def store_render_visibility_state(objects=None):
    rv = {}
    obj : bpy.types.Object
    if objects is None:
        objects = bpy.data.objects
    elif type(objects) is bpy.types.Object:
        objects = [objects]
    for obj in objects:
        if object_exists(obj):
            visible = obj.visible_get()
            render = not obj.hide_render
            rv[obj.name] = [visible, render]
    return rv


def restore_render_visibility_state(rv):
    obj : bpy.types.Object
    for obj_name in rv:
        if obj_name in bpy.data.objects:
            obj = bpy.data.objects[obj_name]
            if object_exists(obj):
                visible, render = rv[obj.name]
                try:
                    obj.hide_render = not render
                    hide(obj, not visible)
                except:
                    pass


def set_only_render_visible(object):
    obj : bpy.types.Object
    for obj in bpy.data.objects:
        if object_exists(obj):
            visible = obj.visible_get()
            render = not obj.hide_render
            if obj == object:
                try:
                    obj.hide_render = False
                    unhide(obj)
                except:
                    pass
            else:
                try:
                    obj.hide_render = True
                    hide(obj)
                except:
                    pass


def store_object_transform(obj: bpy.types.Object):
    T = (obj.location.copy(),
         obj.rotation_mode,
         obj.rotation_quaternion.copy(),
         [a for a in obj.rotation_axis_angle],
         obj.rotation_euler.copy(),
         obj.scale.copy())
    return T


def restore_object_transform(obj: bpy.types.Object, T: tuple, ignore_scale=False):
    if ignore_scale:
        obj.location, obj.rotation_mode, obj.rotation_quaternion, obj.rotation_axis_angle, obj.rotation_euler, scale = T
    else:
        obj.location, obj.rotation_mode, obj.rotation_quaternion, obj.rotation_axis_angle, obj.rotation_euler, obj.scale = T


def reset_object_transform(obj: bpy.types.Object):
    obj.location = Vector((0,0,0))
    obj.rotation_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))
    obj.rotation_euler = Euler((0.0, -0.0, 0.0), 'XYZ')
    obj.rotation_axis_angle = [0,0,0,0]


def get_region_3d(context=None):
    space = get_view_3d_space(context)
    if space:
        return space, space.region_3d
    return None, None


def get_3d_regions(context=None):
    spaces = get_view_3d_spaces(context)
    if spaces:
        return [ s.region_3d for s in spaces ]
    return []


def get_view_3d_space(context=None) -> bpy.types.Space:
    try:
        if not context:
            context = bpy.context
        space_data = bpy.context.space_data
        if space_data and space_data.tpye == "VIEW_3D":
            return space_data
    except: ...
    try:
        area = get_view_3d_area(context)
        if area:
            return area.spaces.active
    except: ...
    log_warn("Unable to get view 3d space!")
    return None


def get_view_3d_spaces(context=None) -> bpy.types.Space:
    try:
        areas = get_view_3d_areas(context)
        if areas:
            return [ area.spaces.active for area in areas ]
    except: ...
    log_warn("Unable to get view 3d spaces!")
    return []


def get_view_3d_shading(context=None) -> bpy.types.View3DShading:
    try:
        if not context:
            context = bpy.context
        space_data = context.space_data
        if space_data and space_data.type == "VIEW_3D":
            return space_data.shading
    except: ...
    try:
        space_data = get_view_3d_space(context)
        if space_data:
            return space_data.shading
    except: ...
    log_warn("Unable to get view space shading!")
    return None


def get_view_3d_override_context():
    for window_manager in bpy.data.window_managers:
        for window in window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            return dict(window=window, area=area, region=region)
    return None


def get_view_3d_area(context=None) -> bpy.types.Area:
    try:
        if not context:
            context = bpy.context
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                return area
    except: ...
    return None


def get_view_3d_areas(context=None) -> bpy.types.Area:
    areas = []
    try:
        if not context:
            context = bpy.context
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                areas.append(area)
    except:
        areas = []
    return areas


def align_object_to_view(obj, context):
    if context is None:
        context = bpy.context
    area_3d = None
    if context.area and context.area.type == 'VIEW_3D':
        area_3d = bpy.context.area
    else:
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area_3d = area
    if area_3d:
        view_space = area_3d.spaces.active
        r3d = view_space.region_3d
        loc = r3d.view_location
        rot = r3d.view_rotation
        D = r3d.view_distance
        v = Vector((0,0,1)) * D

        obj.location = loc + rot @ v
        set_transform_rotation(obj, rot)


def copy_action(action: bpy.types.Action, new_name):
    new_action = action.copy()
    new_action.name = new_name
    return new_action


def make_action(name, reuse=False, slot_type=None, target_obj=None, slot_name=None, clear=False):
    action = None
    if reuse and name in bpy.data.actions:
        action = bpy.data.actions[name]
    if not action:
        action = bpy.data.actions.new(name)
    if clear:
        clear_action(action)
    if B440():
        if target_obj:
            if not slot_type:
                slot_type = get_slot_type_for(target_obj)
            if not slot_name:
                slot_name = f"SLOT-{slot_type}"
            make_action_slot(action, slot_type, slot_name)
    return action


def make_action_slot(action, slot_type, slot_name):
    if B440():
        for slot in action.slots:
            if slot.target_id_type == slot_type and strip_name(slot.name) == slot_name:
                return slot
        for slot in action.slots:
            if slot.target_id_type == slot_type:
                return slot
        return action.slots.new(slot_type, slot_name)
    return None


def get_action_slot(action, slot_type):
    if B440():
        for slot in action.slots:
            if slot.target_id_type == slot_type:
                return slot
    return None


def get_slot_type_for(obj):
    T = type(obj)
    slot_type = "OBJECT"
    if T is bpy.types.Key:
        slot_type = "KEY"
    if (T is bpy.types.Light or
        T is bpy.types.SpotLight or
        T is bpy.types.SunLight or
        T is bpy.types.AreaLight or
        T is bpy.types.PointLight):
        slot_type = "LIGHT"
    if T is bpy.types.Camera:
        slot_type = "CAMERA"
    return slot_type


def set_action_slot(obj, action, slot=None):
    """Blender 4.4+ Only:
       Set the obj.animation_data.action_slot to the supplied slot or
       the first action slot with the matching slot_type"""
    if obj and action and B440():
        if slot:
            try:
                obj.animation_data.action_slot = slot
            except:
                log_error(f"Unable to set action slot {action} / {slot}")
            return True
        else:
            slot_type = get_slot_type_for(obj)
            slot = get_action_slot(action, slot_type)
            if slot:
                try:
                    obj.animation_data.action_slot = slot
                except:
                    log_error(f"Unable to set action slot by type: {slot_type} / {action} / {slot}")
        return False
    return True


def safe_get_action(obj) -> bpy.types.Action:
    if obj:
        try:
            if obj.animation_data:
                return obj.animation_data.action
        except:
            log_warn(f"Unable to get action from {obj.name}")
    return None


def safe_set_action(obj, action, create=True, slot=None):
    result = False
    if obj:
        try:
            if create and not obj.animation_data:
                obj.animation_data_create()
            if obj.animation_data:
                obj.animation_data.action = action
                set_action_slot(obj, action, slot)
                result = True
        except Exception as e:
            action_name = action.name if action else "None"
            log_error(f"Unable to set action {action_name} to {obj.name}", e)
            result = False
    return result


def clear_action(action, slot_type=None, slot_name=None):
    if action:
        try:
            if B440():
                for layer in action.layers:
                    for strip in layer.strips:
                        for channelbag in strip.channelbags:
                            channelbag.fcurves.clear()
                while action.slots:
                    action.slots.remove(action.slots[0])
            action.fcurves.clear()
            if B440():
                if slot_type and slot_name:
                    action.slots.new(slot_type, slot_name)
            return True
        except:
            log_error(f"Unable to clear action: {action}")
    return False


def get_action_channels(action: bpy.types.Action, slot=None, slot_type=None):
    if not action:
        return None
    if B440() and (slot or slot_type):
        if not action.layers:
            layer = action.layers.new("Layer")
        else:
            layer = action.layers[0]
        if not layer.strips:
            strip = layer.strips.new(type='KEYFRAME')
        else:
            strip = layer.strips[0]
        if not slot and slot_type:
            slot = get_action_slot(action, slot_type)
        if slot:
            channelbag = strip.channelbag(slot, ensure=True)
            return channelbag
        return action
    else:
        return action


def index_of_collection(item, collection):
    for i, o in enumerate(collection):
        if o == item:
            return i
    return -1


def collection_at_index(index, collection):
    if index >= 0 and index < len(collection):
        return collection[index]
    return None


def set_active_layer_collection(layer_collection):
     old = bpy.context.view_layer.active_layer_collection
     bpy.context.view_layer.active_layer_collection = layer_collection
     return old


def get_active_layer_collection():
     return bpy.context.view_layer.active_layer_collection


def set_active_layer_collection_from(obj):
    nlc = find_layer_collection_containing(obj)
    return set_active_layer_collection(nlc)


def find_layer_collection_containing(obj, layer_collection = None):
    if not layer_collection:
        layer_collection = bpy.context.view_layer.layer_collection
    if obj.name in layer_collection.collection.objects:
        return layer_collection
    for child in layer_collection.children:
        found = find_layer_collection_containing(obj, child)
        if found:
            return found
    return None


def find_layer_collection(name, layer_collection = None):
    if not layer_collection:
        layer_collection = bpy.context.view_layer.layer_collection
    if layer_collection.name == name:
        return layer_collection
    for child in layer_collection.children:
        found = find_layer_collection(name, child)
        if found:
            return found
    return None


def clear_prop_collection(col):
    try:
        col.clear()
        return True
    except:
        pass
    try:
        while col:
            col.remove(col[0])
        return True
    except:
        pass
    log_error(f"Unable to clear property collection: {col}")
    return False


def B290():
    return is_blender_version("2.90.0")

def B291():
    return is_blender_version("2.91.0")

def B292():
    return is_blender_version("2.92.0")

def B293():
    return is_blender_version("2.93.0")

def B300():
    return is_blender_version("3.0.0")

def B310():
    return is_blender_version("3.1.0")

def B320():
    return is_blender_version("3.2.0")

def B321():
    return is_blender_version("3.2.1")

def B330():
    return is_blender_version("3.3.0")

def B340():
    return is_blender_version("3.4.0")

def B341():
    return is_blender_version("3.4.1")

def B350():
    return is_blender_version("3.5.0")

def B360():
    return is_blender_version("3.6.0")

def B400():
    return is_blender_version("4.0.0")

def B401():
    return is_blender_version("4.0.1")

def B410():
    return is_blender_version("4.1.0")

def B420():
    return is_blender_version("4.2.0")

def B430():
    return is_blender_version("4.3.0")

def B440():
    return is_blender_version("4.4.0")


def is_blender_version(version: str, test = "GTE"):
    """e.g. is_blender_version("3.0.0", "GTE")"""
    major, minor, subversion = version.split(".")
    blender_version = bpy.app.version

    v_test = int(major) * 1000000 + int(minor) * 1000 + int(subversion)
    v_blender = blender_version[0] * 1000000 + blender_version[1] * 1000 + blender_version[2]

    if test == "GTE" and v_blender >= v_test:
        return True
    elif test == "GT" and v_blender > v_test:
        return True
    elif test == "LT" and v_blender < v_test:
        return True
    elif test == "LTE" and v_blender <= v_test:
        return True
    elif test == "EQ" and v_blender == v_test:
        return True
    elif test == "NE" and v_blender != v_test:
        return True
    return False


def is_addon_version(version: str, test = "GTE"):
    """e.g. is_addon_version("v1.1.8", "GTE")"""
    major, minor, subversion = version[1:].split(".")
    addon_version = vars.VERSION_STRING
    addon_major, addon_minor, addon_subversion = addon_version[1:].split(".")

    v_test = int(major) * 1000000 + int(minor) * 1000 + int(subversion)
    v_addon = int(addon_major) * 1000000 + int(addon_minor) * 1000 + int(addon_subversion)

    if test == "GTE" and v_addon >= v_test:
        return True
    elif test == "GT" and v_addon > v_test:
        return True
    elif test == "LT" and v_addon < v_test:
        return True
    elif test == "LTE" and v_addon <= v_test:
        return True
    elif test == "EQ" and v_addon == v_test:
        return True
    elif test == "NE" and v_addon != v_test:
        return True
    return False


def clear_reports():
    win = bpy.context.window_manager.windows[0]
    temp_area = True
    info_area = win.screen.areas[0]
    # try to find an existing info area
    for area in win.screen.areas:
        if info_area.type == "INFO":
            info_area = area
            temp_area = False

    # other wise turn the first area into an info area temporarily
    if temp_area:
        area_type = info_area.type
        info_area.type = "INFO"

    context = bpy.context.copy()
    context['window'] = win
    context['screen'] = win.screen
    context['area'] = win.screen.areas[0]
    bpy.ops.info.select_all(context, action='SELECT')
    bpy.ops.info.report_delete(context)

    # restore the temp area
    if temp_area:
        info_area.type = area_type


def get_last_report():
    win = bpy.context.window_manager.windows[0]
    temp_area = True
    info_area = win.screen.areas[0]
    # try to find an existing info area
    for area in win.screen.areas:
        if info_area.type == "INFO":
            info_area = area
            temp_area = False

    # other wise turn the first area into an info area temporarily
    if temp_area:
        area_type = info_area.type
        info_area.type = "INFO"

    context = bpy.context.copy()
    context['window'] = win
    context['screen'] = win.screen
    context['area'] = win.screen.areas[0]
    bpy.ops.info.select_all(context, action='SELECT')
    bpy.ops.info.report_copy(context)

    # restore the temp area
    if temp_area:
        info_area.type = area_type

    # return the last line
    clipboard = bpy.context.window_manager.clipboard
    lines = clipboard.splitlines()
    return lines[-1]


def match_wild(test: str, match_list: list) -> bool:
    if test and match_list:
        for match in match_list:
            if test == match:
                return True
            elif match.startswith("*") and match.endswith("*"):
                if match[1:-1] in test:
                    return True
            elif match.startswith("*"):
                if match[1:] in test:
                    return True
            elif match.endswith("*"):
                if match[:-1] in test:
                    return True
    return False


def copy_collection_property(prop_a, prop_b, exclude: list = None):
    prop_b.clear()
    for prop in prop_a:
        to_prop = prop_b.add()
        copy_property_group(prop, to_prop, exclude=exclude)


def copy_property_group(group_a, group_b, exclude: list = None):
    vars.block_property_update = True
    # items() returns a list of properties that have been changed
    # from the defaults, or been set, in the property group:
    # returns a list of tuples [(prop, value), (prop, value)...]
    items_a = group_a.items()
    # get a list of all property names in group_a that have been altered
    props_a = [ i[0] for i in items_a ]
    # get a list of all properties in group_b
    props_b = dir(group_b)
    # get a list of all properties that have been changed in group_a and are present in group_b
    props = [ p for p in props_a if p in props_b ]
    for prop in props:
        if exclude and match_wild(prop, exclude):
            log_info(f" - excluding: {prop}")
            continue
        value = getattr(group_a, prop)
        target = getattr(group_b, prop)
        if type(target) == type(value) or value is None or target is None:
            if issubclass(type(value), bpy.types.PropertyGroup):
                # all property groups are subclasses of bpy.types.PropertyGroup
                log_info(f" - copying property group: {prop}")
                copy_property_group(value, target, exclude=exclude)
            elif hasattr(value, "clear") and hasattr(value, "add"):
                # collection properties have add() and clear() functions
                log_info(f" - copying collection property: {prop}")
                copy_collection_property(value, target, exclude=exclude)
            else:
                log_info(f" - setting: {prop} {value}")
                setattr(group_b, prop, value)
        else:
            log_error(f"Properties are of different types: {prop} {type(value)} != {type(target)}")
    vars.block_property_update = False


def stop_now():
    raise Exception("STOP!")


def object_world_location(obj : bpy.types.Object, delta = None):
    location = obj.location.copy()
    if delta:
        location += delta
    if obj.parent:
        return obj.parent.matrix_world @ location
    else:
        return location


def is_valid_icon(icon):
    return icon in bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys()


def check_icon(icon):
    if B321():
        if icon == "OUTLINER_OB_HAIR":
            return "OUTLINER_OB_CURVES"
        elif icon == "HAIR":
            return "CURVES"
    return icon


def md5sum(filename):
    hash = md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(128 * hash.block_size), b""):
            hash.update(chunk)
    return hash.hexdigest()


def store_object_state(objects=None):
    """Store object & mesh/armature and material names and slots."""
    if objects is None:
        objects = bpy.data.objects
    obj_state = {}
    for obj in objects:
        if (object_exists_is_armature(obj) or object_exists_is_mesh(obj)) and obj not in obj_state:
            obj_state[obj] = {
                "names": [obj.name, obj.data.name],
                "visible": obj.visible_get(),
            }
            if obj.type == "MESH":
                obj_state[obj]["slots"] = [ slot.material for slot in obj.material_slots ]
                for mat in obj.data.materials:
                    if material_exists(mat) and mat not in obj_state:
                        obj_state[mat] = { "name": mat.name }
                if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
                    obj_state[obj]["action"] = safe_get_action(obj.data.shape_keys)
            if obj.type == "ARMATURE":
                obj_state[obj]["action"] = safe_get_action(obj)
    return obj_state


def restore_object_state(obj_state):
    """Restore object & mesh/armature and material names and slots."""
    for item in obj_state:
        state = obj_state[item]
        if type(item) is bpy.types.Object:
            obj: bpy.types.Object = item
            restore_name = True
            if "rl_do_not_restore_name" in obj:
                restore_name = False
                del obj["rl_do_not_restore_name"]
            if object_exists(obj):
                if restore_name:
                    force_object_name(obj, state["names"][0])
                if obj.type == "MESH":
                    if restore_name:
                        force_mesh_name(obj.data, state["names"][1])
                    for i, mat in enumerate(state["slots"]):
                        if not material_exists(mat):
                            mat = None
                        if obj.material_slots[i].material != mat:
                            obj.material_slots[i].material = mat
                    if "action" in state:
                        safe_set_action(obj.data.shape_keys, state["action"])
                elif obj.type == "ARMATURE":
                    if restore_name:
                        force_armature_name(obj.data, state["names"][1])
                    if "action" in state:
                        safe_set_action(obj, state["action"])
        elif type(item) is bpy.types.Material:
            mat: bpy.types.Material = item
            if material_exists(mat):
                force_material_name(mat, state["name"])


def reset_shape_keys(objects):
    """Unlock and reset object shape keys to zero."""
    for obj in objects:
        if obj.type == "MESH":
            # disable shape key lock
            obj.show_only_shape_key = False
            # reset all shape keys to zero
            if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
                for key in obj.data.shape_keys.key_blocks:
                    key.value = 0.0


INVALID_EXPORT_CHARACTERS = "`¬!\"£$%^&*()+-=[]{}:@~;'#<>?,./\| "
DIGITS = "0123456789"


def is_invalid_export_name(name, is_material = False):
    for char in INVALID_EXPORT_CHARACTERS:
        if char in name:
            return True
    if is_material:
        if name[0] in DIGITS:
            return True
    return False


def safe_export_name(name, is_material = False, is_split=False):
    if is_split:
        if is_blender_duplicate(name):
            num = get_duplication_suffix(name)
            name = strip_name(name) + f"_S{num:02}"
    for char in INVALID_EXPORT_CHARACTERS:
        if char in name:
            name = name.replace(char, "_")
    if is_material:
        if name[0] in DIGITS:
            name = f"_{name}"
    return name


def determine_object_export_name(chr_cache, obj, obj_cache = None):
    """Work out what the object should be named when exporting
       by comparing the current name with the original name when imported.
    """
    obj_name = obj.name
    if not obj_cache:
        obj_cache = chr_cache.get_object_cache(obj)
    source_changed = False
    is_new_object = False
    if obj_cache:
        obj_expected_source_name = safe_export_name(strip_name(obj_name))
        obj_source_name = obj_cache.source_name
        source_changed = obj_expected_source_name != obj_source_name
        if source_changed:
            obj_safe_name = safe_export_name(obj_name)
        else:
            obj_safe_name = obj_source_name
    else:
        is_new_object = True
        obj_safe_name = safe_export_name(obj_name)
        obj_source_name = obj_safe_name
    return obj_safe_name


def furthest_from(p0, *points):
    most = 0
    result = p0
    for p in points:
        dp = (p - p0).length
        if dp > most:
            most = dp
            result = p
    return result


def name_contains_distinct_keywords(name : str, *keywords : str):
    """Does the name contain the supplied keywords in distinct form:\n
       i.e. capitalized "OneTwoThree"\n
            or hungarian notation "oneTwoThree"\n
            or surrouned by underscores "one_two_three"
    """

    name_lower = name.lower()
    name_length = len(name)

    for k in keywords:
        k_lower = k.lower()
        k_length = len(k)

        s = name_lower.find(k_lower)
        e = s + k_length

        if s >= 0:

            # is keyword in name separated by underscores
            if (name_lower.startswith(k_lower + "_") or
                name_lower.endswith("_" + k_lower) or
                "_" + k_lower + "_" in name_lower or
                name_lower == k_lower):
                return True

            # match distinct keyword at start of name (any capitalization) or captitalized anywhere else
            if s == 0 or name[s].isupper():
                if e >= name_length or not name[e].islower():
                    return True

    return False


def is_name_or_duplication(a, b):
    return strip_name(a) == strip_name(b)


def object_has_shape_keys(obj):
    try:
        if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
            return True
        else:
            return False
    except:
        return False


def object_scale(obj):
    try:
        return (obj.scale[0] + obj.scale[1] + obj.scale[2]) / 3.0
    except:
        return 1.0


def make_transform_matrix(loc: Vector, rot: Quaternion, sca: Vector):
    return Matrix.Translation(loc) @ (rot.to_matrix().to_4x4()) @ Matrix.Diagonal(sca).to_4x4()


def set_transform_rotation(obj: bpy.types.Object, rotation: Quaternion):
    if obj and rotation:
        T = type(rotation)
        if T is Euler:
            rotation_quaternion = Quaternion(rotation)
        elif T is tuple and len(rotation) == 2:
            axis, angle = rotation
            rotation_quaternion = axis_angle_to_quaternion(axis, angle)
        elif T is Quaternion:
            rotation_quaternion = rotation.copy()
        else:
            return

        if obj.rotation_mode == "QUATERNION":
            obj.rotation_quaternion = rotation_quaternion
        elif obj.rotation_mode == "AXIS_ANGLE":
            axis_angle = rotation_quaternion.to_axis_angle()
            obj.rotation_axis_angle = axis_angle
        else:
            euler = rotation_quaternion.to_euler(obj.rotation_mode)
            obj.rotation_euler = euler


def axis_angle_to_quaternion(axis: Vector, angle: float):
    return Matrix.Rotation(angle, 4, axis).to_quaternion()


def get_transform_rotation(obj: bpy.types.Object) -> Quaternion:
    if obj:
        if obj.rotation_mode == "QUATERNION":
            return obj.rotation_quaternion.copy()
        elif obj.rotation_mode == "AXIS_ANGLE":
            axis = obj.rotation_axis_angle[0:3]
            angle = obj.rotation_axis_angle[3]
            return axis_angle_to_quaternion(axis, angle)
        else:
            return obj.rotation_euler.to_quaternion()
    return None


def is_local_view(context):
    try:
        return context.space_data.local_view is not None
    except:
        return False


def fix_local_view(context):
    if is_local_view(context):
        bpy.ops.view3d.localview()


def show_system_file_browser(path):
    if platform.system() == "Windows":
        try:
            explorer_path = os.path.join(os.getenv("WINDIR"), "explorer.exe")
            subprocess.Popen((explorer_path, "/select,", path))
        except:
            pass


def get_scene_frame_range():
    scene = bpy.context.scene
    if scene.use_preview_range:
        return scene.frame_preview_start, scene.frame_preview_end
    else:
        return scene.frame_start, scene.frame_end


def set_scene_frame_range(start, end):
    scene = bpy.context.scene
    if scene.use_preview_range:
        scene.frame_preview_start = start
        scene.frame_preview_end = end
    else:
        scene.frame_start = start
        scene.frame_end = end


def make_empty(name, loc=None, rot=None, scale=None, matrix=None):
    ob = bpy.data.objects.new(name, None)
    if matrix:
        ob.matrix_world = matrix
    else:
        if loc:
            ob.location = loc
        if rot:
            set_transform_rotation(ob, rot)
        if scale:
            ob.scale = scale
    bpy.context.scene.collection.objects.link(ob)


def is_n_panel_sub_tabs():
    for prefs in bpy.context.preferences.addons.keys():
        if "n_panel_sub_tabs" in prefs:
            return True
    return False


def generate_random_id(length):
    CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    id = ""
    for i in range(0, length):
        id += random.choice(CHARS)
    return id


def set_prop(obj, prop_name, value):
    try:
        obj[prop_name] = value
        return True
    except:
        try:
            del(obj[prop_name])
            obj[prop_name] = value
            return True
        except: ...
    return False


def set_rl_link_id(obj, link_id=None):
    if link_id is None:
        link_id = generate_random_id(20)
    if obj:
        set_prop(obj, "rl_link_id", link_id)
    return link_id


def get_rl_link_id(obj):
    if obj:
        if "link_id" in obj:
            link_id = obj["link_id"]
            del(obj["link_id"])
            set_rl_link_id(obj, link_id)
            return link_id
        elif "rl_link_id" in obj:
            return obj["rl_link_id"]
    return None


def set_rl_object_id(obj, new_id=None):
    if new_id is None:
        new_id = generate_random_id(20)
    if obj:
        if obj.type == "ARMATURE":
            set_prop(obj, "rl_armature_id", new_id)
            if "rl_object_id" in obj:
                del(obj["rl_object_id"])
        else:
            set_prop(obj, "rl_object_id", new_id)
    return new_id


def get_rl_object_id(obj):
    if obj:
        if obj.type == "ARMATURE" and "rl_armature_id" in obj:
            return obj["rl_armature_id"]
        if "rl_object_id" in obj:
            return obj["rl_object_id"]
    return None


def prop(obj, prop_name, default=None):
    if obj and prop_name in obj:
        return obj[prop_name]
    return default


def merge(a: list, b: list):
    c = a.copy()
    for i in b:
        if i not in c:
            c.append(i)
    return c


def fix_texture_rel_path(rel_path: str):
    """Fixes json texture relative path export bug in CC4 when exporting character directly
       to the root folder of a drive"""

    if rel_path.startswith(".textures"):
        rel_path = rel_path[1:]
    elif rel_path.startswith("./"):
        rel_path = rel_path[2:]
    return rel_path


def get_resource_path(folder, file):
    addon_path = os.path.dirname(os.path.realpath(__file__))
    resource_path = os.path.join(addon_path, folder, file)
    return resource_path


def get_resource_folder(folder):
    addon_path = os.path.dirname(os.path.realpath(__file__))
    resource_folder = os.path.join(addon_path, folder)
    return resource_folder


def get_unique_folder_path(parent_folder, folder_name, create=False, reuse=False):
    suffix = 1
    base_name = folder_name
    folder_path = os.path.normpath(os.path.join(parent_folder, folder_name))
    if not reuse:
        while os.path.exists(folder_path):
            folder_name = f"{base_name}_{str(suffix)}"
            folder_path = os.path.normpath(os.path.join(parent_folder, folder_name))
            suffix += 1
    if create:
        os.makedirs(folder_path, exist_ok=reuse)
    return folder_path


def get_unique_file_path(parent_folder, file_name, reuse=False):
    suffix = 1
    base_name, ext = os.path.splitext(file_name)
    file_path = os.path.normpath(os.path.join(parent_folder, file_name))
    if not reuse:
        while os.path.exists(file_path):
            file_name = f"{base_name}_{str(suffix)}{ext}"
            file_path = os.path.normpath(os.path.join(parent_folder, file_name))
            suffix += 1
    return file_path


def make_sub_folder(parent_folder, folder_name):
    folder_path = os.path.normpath(os.path.join(parent_folder, folder_name))
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def timestampns():
    return str(time.time_ns())


def datetimes():
    return time.strftime("%Y%m%d%H%M%S")


def json_dumps(json_data):
    print(json.dumps(json_data, indent=4))


def open_folder(folder_path):
    os.startfile(folder_path)


def get_enum_prop_name(obj, prop_name, enum_value=None):
    try:
        prop = type(obj).bl_rna.properties[prop_name]
        if enum_value is None:
            enum_value = getattr(obj, prop_name)
        return prop.enum_items[enum_value].name
    except:
        return prop_name

