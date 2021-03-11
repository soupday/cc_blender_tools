import os

import bpy

from .utils import *
from .vars import *

def get_node_group(name):
    for group in bpy.data.node_groups:
        if NODE_PREFIX in group.name and name in group.name:
            if VERSION_STRING in group.name:
                return group
    return fetch_node_group(name)


def check_node_groups():
    for name in NODE_GROUPS:
        get_node_group(name)


def remove_all_groups():
    for group in bpy.data.node_groups:
        if NODE_PREFIX in group.name:
            bpy.data.node_groups.remove(group)


def rebuild_node_groups():
    remove_all_groups()
    check_node_groups()
    return


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
            g.name = unique_name(object_name)
        g.tag = False
    return appended_group


def fetch_node_group(name):

    paths = [bpy.path.abspath("//"),
             os.path.dirname(os.path.realpath(__file__)),
             ]
    for path in paths:
        log_info("Trying to append: " + path + " > " + name)
        if os.path.exists(path):
            group = append_node_group(path, name)
            if group is not None:
                return group
    log_error("Trying to append group: " + name + ", _LIB.blend library file not found?")
    raise ValueError("Unable to append node group from library file!")
