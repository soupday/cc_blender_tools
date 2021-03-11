import os

import bpy

from .vars import *


def log_info(msg):
    """Log an info message to console."""
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    if prefs.log_level == "ALL":
        print(msg)


def log_warn(msg):
    """Log a warning message to console."""
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences
    if prefs.log_level == "ALL" or prefs.log_level == "WARN":
        print("Warning: " + msg)


def log_error(msg):
    """Log an error message to console and raise an exception. """
    print("Error: " + msg)


def message_box(message = "", title = "Info", icon = 'INFO'):
    """Shows a pop-up message box with the message and optional title and icon."""
    def draw(self, context):
        self.layout.label(text = message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def unique_name(name):
    """Generate a unique name for the node or property to quickly
    identify texture nodes or nodes with parameters.
    """

    props = bpy.context.scene.CC3ImportProps
    name = NODE_PREFIX + name + "_" + VERSION_STRING + "_" + str(props.node_id)
    props.node_id = props.node_id + 1
    return name


def strip_name(name):
    """Strips any blender duplicate name number suffix (e.g. Material.003) from the name.
    """

    if name[-3:].isdigit() and name[-4] == ".":
        name = name[:-4]
    return name


def load_image(filepath, color_space):
    """Loads an image from a file, but tries to find it in the existing images first by matching the filepath.
    """

    for i in bpy.data.images:
        if (i.type == "IMAGE" and i.filepath != ""):
            try:
                if os.path.normcase(i.filepath) == os.path.normcase(filepath):
                    log_info("    Using existing image: " + i.filepath)
                    return i
            except:
                pass

    log_info("    Loading new image: " + filepath)
    try:
        image = bpy.data.images.load(filepath)
        image.colorspace_settings.name = color_space
        return image
    except:
        return None


def clean_colletion(collection):
    """Deletes everything from a collection that has no active users, including fake users.
    """

    for item in collection:
        if (item.use_fake_user and item.users == 1) or item.users == 0:
            collection.remove(item)


def tag_objects(default = True):
    """Sets the tag on all objects in the blend file.

    When importing objects with the FBX or OBJ importer, it does not return a list of imported objects.
    So we tag the existing objects before the import and thus any objects without the tag are the new ones.
    """

    for obj in bpy.data.objects:
        obj.tag = default


def untagged_objects(default = True):
    """Returns a list of all untagged objects.
    """

    untagged = []

    for obj in bpy.data.objects:
        if not obj.tag == default:
            untagged.append(obj)
        obj.tag = default

    return untagged


def select_all_child_objects(obj):
    """Recursively selects all mesh objects this object is the parent of, including this object.
    """

    if obj.type == "ARMATURE" or obj.type == "MESH":
        obj.select_set(True)
    for child in obj.children:
        select_all_child_objects(child)


def s2lin(x):
    """sRGB colour space to Linear colour space conversion."""
    a = 0.055
    if x <= 0.04045:
        y = x * (1.0/12.92)
    else:
        y = pow((x + a)*(1.0/(1 + a)), 2.4)
    return y


def lin2s(x):
    """Linear colour space to sRGB colour space conversion."""
    a = 0.055
    if x <= 0.0031308:
        y = x * 12.92
    else:
        y = (1 + a)*pow(x, 1/2.4) - a
    return y


def context_material(context):
    """Tries to return the current active object for the given context, or None."""
    try:
        return context.object.material_slots[context.object.active_material_index].material
    except:
        return None
