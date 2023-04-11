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
import time
import difflib
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
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    """Log an info message to console."""
    if prefs.log_level == "DETAILS":
        print((" " * LOG_INDENT) + msg)


def log_info(msg):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    """Log an info message to console."""
    if prefs.log_level == "ALL" or prefs.log_level == "DETAILS":
        print((" " * LOG_INDENT) + msg)


def log_always(msg):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    """Log an info message to console."""
    print((" " * LOG_INDENT) + msg)


def log_warn(msg):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    """Log a warning message to console."""
    if prefs.log_level == "ALL" or prefs.log_level == "DETAILS" or prefs.log_level == "WARN":
        print((" " * LOG_INDENT) + "Warning: " + msg)


def log_error(msg, e = None):
    """Log an error message to console and raise an exception."""
    indent = LOG_INDENT
    if indent > 1: indent -= 1
    print("*" + (" " * indent) + "Error: " + msg)
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

    props = bpy.context.scene.CC3ImportProps
    if no_version:
        name = name + "_" + vars.NODE_PREFIX + str(props.node_id)
    else:
        name = vars.NODE_PREFIX + name + "_" + vars.VERSION_STRING + "_" + str(props.node_id)
    props.node_id = props.node_id + 1
    return name


def unique_material_name(name, mat = None):
    name = strip_name(name)
    index = 1001
    if name in bpy.data.materials and bpy.data.materials[name] != mat:
        while name + "_" + str(index) in bpy.data.materials:
            index += 1
        return name + "_" + str(index)
    return name


def unique_object_name(name, obj = None):
    name = strip_name(name)
    if name in bpy.data.objects and bpy.data.objects[name] != obj:
        index = 1
        while name + "_" + str(index).zfill(2) in bpy.data.objects:
            index += 1
        return name + "_" + str(index).zfill(2)
    return name


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


def still_exists(obj):
    """Test if obj still exists."""
    try:
        name = obj.name
        return True
    except:
        return False


def object_exists_is_mesh(obj):
    """Test if Object: obj still exists as an object in the scene, and is a mesh."""
    try:
        name = obj.name
        return len(obj.users_scene) > 0 and obj.type == "MESH"
    except:
        return False


def object_exists_is_armature(obj):
    """Test if Object: obj still exists as an object in the scene, and is an armature."""
    try:
        name = obj.name
        return len(obj.users_scene) > 0 and obj.type == "ARMATURE"
    except:
        return False


def object_exists(obj):
    """Test if Object: obj still exists as an object in the scene."""
    try:
        name = obj.name
        return len(obj.users_scene) > 0
    except:
        return False


def get_selected_mesh():
    if object_exists_is_mesh(bpy.context.active_object):
        return bpy.context.active_object
    elif bpy.context.selected_objects:
        for obj in bpy.context.selected_objects:
            if object_exists_is_mesh(obj):
                return obj
    return None


def get_selected_meshes(context = None):
    objects = [ obj for obj in bpy.context.selected_objects if object_exists_is_mesh(obj) ]
    if context and context.object:
        if object_exists_is_mesh(context.object):
            if context.object not in objects:
                objects.append(context.object)
    return objects


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


def lerp(vmin, vmax, t):
    return min(vmax, max(vmin, vmin + (vmax - vmin) * t))


def inverse_lerp(vmin, vmax, value):
    return min(1.0, max(0.0, (value - vmin) / (vmax - vmin)))


def lerp_color(c0, c1, t):
    return (lerp(c0[0], c1[0], t),
            lerp(c0[1], c1[1], t),
            lerp(c0[2], c1[2], t),
            lerp(c0[3], c1[3], t))


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
    return bpy.context.active_object


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


def get_mode():
    try:
        return bpy.context.object.mode
    except:
        return "OBJECT"


def edit_mode_to(obj, only_this = False):
    if only_this and (get_active_object() != obj or len(bpy.context.selected_objects) > 1 or obj not in bpy.context.selected_objects):
        set_only_active_object(obj)
    if obj in bpy.context.selected_objects and get_active_object() == obj and get_mode() == "EDIT":
        return True
    else:
        if set_mode("OBJECT") and set_active_object(obj) and set_mode("EDIT"):
            return True
    return False


def object_mode_to(obj):
    if set_mode("OBJECT"):
        if try_select_object(obj):
            if set_active_object(obj):
                return True
    return False


def pose_mode_to(arm):
    if object_mode_to(arm):
        if set_mode("POSE"):
            return True
    return False


def duplicate_object(obj):
    if set_mode("OBJECT"):
        if try_select_object(obj, True) and set_active_object(obj):
            bpy.ops.object.duplicate()
            return get_active_object()
    return None


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
    if len(name) >= 4:
        if name[-3:].isdigit() and name[-4] == ".":
            name = name[:-4]
    return name


def is_blender_duplicate(name):
    if len(name) >= 4:
        if name[-3:].isdigit() and name[-4] == ".":
            return True
    return False


def make_unique_name(name, keys):
    if name in keys:
        i = 1
        while name + "_" + str(i) in keys:
            i += 1
        return name + "_" + str(i)
    return name


def partial_match(text, search, start = 0):
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
    if ext[0] == ".":
        return ext.lower()
    else:
        return f".{ext}".lower()


def get_file_ext(ext):
    if ext[0] == ".":
        return ext[1:].lower()
    else:
        return ext.lower()


def is_file_ext(test, ext):
    if ext[0] == ".":
        ext = ext[1:]
    if test[0] == ".":
        test = test[1:]
    return test.lower() == ext.lower()


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


def add_child_objects(obj, objects):
    for child in obj.children:
        if child not in objects:
            objects.append(child)
            add_child_objects(child, objects)


def expand_with_child_objects(objects):
    for obj in objects:
        add_child_objects(obj, objects)


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


def get_armature_in_objects(objects):
    arm = None
    if objects:
        for obj in objects:
            if obj.type == "ARMATURE":
                return obj
            elif obj.type == "MESH":
                if arm is None and obj.parent and obj.parent.type == "ARMATURE":
                    arm = obj.parent
    return arm


def float_equals(a, b):
    return abs(a - b) < 0.00001


def get_action_shape_key_object_name(name):
    obj_name = strip_name(name)
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
        if obj.type == "MESH" and obj.data:
            try:
                bpy.data.meshes.remove(obj.data)
            except:
                pass
        elif obj.type == "ARMATURE" and obj.data:
            try:
                bpy.data.armatures.remove(obj.data)
            except:
                pass
        try:
            bpy.data.objects.remove(obj)
        except:
            pass


def hide_tree(obj, hide = True):
    objects = get_object_tree(obj)
    for obj in objects:
        try:
            obj.hide_set(hide)
        except:
            pass


def get_context_area(context, area_type):
    for area in context.screen.areas:
        if area.type == area_type:
            return area
    return None


def get_current_tool_idname(context = None):
    if context is None:
        context = bpy.context
    tool_idname = context.workspace.tools.from_space_view3d_mode(context.mode).idname
    return tool_idname



def add_layer_collections(layer_collection : bpy.types.LayerCollection, layer_collections, search = None):
    if search:
        if search in layer_collection.name:
            layer_collections.append(layer_collection)
    else:
        layer_collections.append(layer_collection)
    child_collection : bpy.types.LayerCollection
    for child_collection in layer_collection.children:
        if not child_collection.exclude:
            add_layer_collections(layer_collection, layer_collections, search)


def get_view_layer_collections(search = None):
    layer_collections = []
    for view_layer in bpy.context.scene.view_layers:
        layer_collection : bpy.types.LayerCollection
        for layer_collection in view_layer.layer_collection.children:
            if not layer_collection.exclude:
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
                    sub_item.hide_set(False)
            else:
                tmp_collection.objects.link(item)
                item.hide_set(False)
    # return the temp collection and the layers exlcuded
    return tmp_collection, layer_collections, to_hide


def create_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    else:
        collection = bpy.data.collections.new(name)
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
        obj.hide_set(True)


def force_visible_in_scene(collection_name, *objects):
    tmp_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(tmp_collection)
    for obj in objects:
        if not obj.visible_get():
            log_info(f"Object: {obj.name} is not visible or in a hidden collection. Linking to temporary root collection and making visible.")
            obj.hide_set(False)
            tmp_collection.objects.link(obj)
    return tmp_collection


def restore_visible_in_scene(tmp_collection : bpy.types.Collection):
    objects = []
    for obj in tmp_collection.objects:
        objects.append(obj)
    for obj in objects:
        log_info(f"Object: {obj.name} Unlinking from temporary root collection and hiding.")
        obj.hide_set(True)
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
    return [mode, active, selection]


def restore_mode_selection_state(store):
    try:
        set_mode("OBJECT")
        try_select_objects(store[2], True)
        set_active_object(store[1])
        set_mode(store[0])
    except:
        pass


def store_render_visibility_state():
    rv = {}
    obj : bpy.types.Object
    for obj in bpy.data.objects:
        if object_exists(obj):
            visible = obj.visible_get()
            render = not obj.hide_render
            if render or visible:
                rv[obj.name] = [visible, render]
    return rv


def restore_render_visibility_state(rv):
    obj : bpy.types.Object
    for obj in bpy.data.objects:
        if object_exists(obj):
            if obj.name in rv:
                visible, render = rv[obj.name]
                try:
                    obj.hide_render = not render
                    obj.hide_set(not visible)
                except:
                    pass

            else:
                try:
                    obj.hide_render = False
                    obj.hide_set(True)
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
                    obj.hide_set(False)
                except:
                    pass
            else:
                try:
                    obj.hide_render = True
                    obj.hide_set(True)
                except:
                    pass


def safe_get_action(obj):
    if obj:
        try:
            if obj.animation_data:
                return obj.animation_data.action
        except:
            log_warn(f"Unable to get action from {obj.name}")
    return None


def safe_set_action(obj, action):
    if obj:
        try:
            if obj.animation_data is None:
                obj.animation_data_create()
            obj.animation_data.action = action
            return True
        except:
            action_name = action.name if action else "None"
            log_warn(f"Unable to set action {action_name} to {obj.name}")
    return False


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


def copy_collection_property(props_a, props_b):
    props_a.clear()
    for from_prop in props_b:
        to_prop = props_a.add()
        copy_property_group(to_prop, from_prop)


def copy_property_group(props_a, props_b):
    """Copy properties from collection b into collection a.
    """
    vars.block_property_update = True
    log_indent()

    # items contains only those properties changed from the detaults in the collection group
    items = props_b.items()
    prop_list = []

    for i in items:
        prop_list.append(i)

    for i in range(0, len(prop_list)):

        prop_name = prop_list[i][0]

        if prop_name:

            value = prop_list[i][1]
            value_type = type(prop_list[i][1])

            try:
                # first try setting directly
                code = f"props_a.{prop_name} = props_b.{prop_name}"
                exec(code, None, locals())
                log_info(f"{code} ({value})")
            except:
                props_to = eval(f"props_a.{prop_name}")
                props_from = eval(f"props_b.{prop_name}")
                try:
                    # only collections (should) have clear() so copy the collection
                    props_to.clear()
                    log_info(f"Attepting to copy as collection property: {prop_name}")
                    copy_collection_property(props_to, props_from)
                except:
                    try:
                        # finally try copying as a property group
                        log_info(f"Attepting to copy as property group: {prop_name}")
                        copy_property_group(props_to, props_from)
                    except:
                        log_error(f"Unable to copy property {prop_name} / {value_type}")

    log_recess()
    vars.block_property_update = False


def stop_now():
    raise Exception("STOP!")


def is_valid_icon(icon):
    return icon in bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys()


def check_icon(icon):
    if is_blender_version("3.2.1"):
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


def safe_export_name(name, is_material = False):
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


def object_scale(obj):
    try:
        return (obj.scale[0] + obj.scale[1] + obj.scale[2]) / 3.0
    except:
        return 1.0


def is_local_view(context):
    try:
        return context.space_data.local_view is not None
    except:
        return False


def fix_local_view(context):
    if is_local_view(context):
        bpy.ops.view3d.localview()