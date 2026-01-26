
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


import bpy, os
from . import utils, vars


def get_object(object_names,
               lib_tag="RL_Library_Object",
               allow_duplicates=True,
               names=None):

    single = False
    if type(object_names) is str:
        object_names = [ object_names ]
        if names:
            names = [ names ]
        single = True
    appended_objects = [None]*len(object_names)

    found = 0

    if not allow_duplicates:
        for obj in bpy.data.objects:
            for i, object_name in enumerate(object_names):
                if ((obj.name.startswith(object_name) or
                    (obj.name.startswith(names[i]))) and
                    utils.get_prop(obj, lib_tag) and
                    is_version(obj)):
                    appended_objects[i] = obj
                    found += 1

    files = [ {"name": object_name } for i, object_name in enumerate(object_names) if appended_objects[i] is None ]

    if files:
        path = os.path.dirname(os.path.realpath(__file__))
        filename = "_LIB341.blend"
        datablock = "Object"
        file = os.path.join(path, filename)
        if os.path.exists(file):
            objects = utils.get_set(bpy.data.objects)
            bpy.ops.wm.append(directory=os.path.join(path, filename, datablock),
                              files=files,
                              set_fake=True,
                              link=False)
            new = utils.get_set_new(bpy.data.objects, objects)
            for i, object_name in enumerate(object_names):
                if appended_objects[i] is None:
                    for obj in new:
                        if utils.strip_name(obj.name) == object_name and lib_tag not in obj:
                            obj[lib_tag] = True
                            obj["RL_Addon_Version"] = vars.VERSION_STRING
                            if names:
                                obj.name = names[i]
                                try:
                                    obj.data.name = names[i]
                                except: ...
                            utils.log_info(f"Appended Library Object: {path} / {object_name} > {obj.name}")
                            appended_objects[i] = obj
                            found += 1

    if found < len(object_names):
        raise ValueError(f"Unable to append all Library Objects: {object_names} from {path}")

    if single:
        return appended_objects[0]
    else:
        return appended_objects


def get_image(image_name, lib_tag="RL_Library_Image"):
    for img in bpy.data.images:
        if (img.name.startswith(image_name) and
            utils.get_prop(img, lib_tag) and
            is_version(img)):
            if not img.packed_file:
                img.pack()
            return img
    path = os.path.dirname(os.path.realpath(__file__))
    filename = "_LIB341.blend"
    datablock = "Image"
    file = os.path.join(path, filename)
    appended_image = None
    if os.path.exists(file):
        images = utils.get_set(bpy.data.images)
        bpy.ops.wm.append(directory=os.path.join(path, filename, datablock),
                          filename=image_name,
                          set_fake=True,
                          link=False)
        new = utils.get_set_new(bpy.data.images, images)
        for img in new:
            if utils.strip_name(img.name) == image_name and lib_tag not in img:
                img[lib_tag] = True
                img["RL_Addon_Version"] = vars.VERSION_STRING
                utils.log_info(f"Appended Library Image: {path} / {image_name} > {img.name}")
                appended_image = img

    if not appended_image:
        raise ValueError(f"Unable to append Library Image: {image_name} from {path}")
    else:
        if not appended_image.packed_file:
            appended_image.pack()

    return appended_image


def get_node_group(group_name, lib_tag="RL_Node_Group"):
    for node_tree in bpy.data.node_groups:
        if (node_tree.name.startswith(group_name) and
            utils.get_prop(node_tree, lib_tag) and
            is_version(node_tree)):
            return node_tree
    path = os.path.dirname(os.path.realpath(__file__))
    filename = "_LIB341.blend"
    datablock = "NodeTree"
    file = os.path.join(path, filename)
    appended_object = None
    if os.path.exists(file):
        node_groups = utils.get_set(bpy.data.node_groups)
        bpy.ops.wm.append(directory=os.path.join(path, filename, datablock),
                          filename=group_name,
                          set_fake=True,
                          link=False)
        new = utils.get_set_new(bpy.data.node_groups, node_groups)
        for node_tree in new:
            if utils.strip_name(node_tree.name) == group_name and lib_tag not in node_tree:
                node_tree[lib_tag] = True
                node_tree["RL_Addon_Version"] = vars.VERSION_STRING
                utils.log_info(f"Appended Library Node Group: {path} / {group_name} > {node_tree.name}")
                appended_object = node_tree

    if not appended_object:
        raise ValueError(f"Unable to append Library Image: {group_name} from {path}")

    return appended_object


def check_node_groups():
    for name in vars.NODE_GROUPS:
        get_node_group(name)


def remove_all_groups():
    for group in bpy.data.node_groups:
        if vars.NODE_PREFIX in group.name or "RL_Node_Group" in group:
            bpy.data.node_groups.remove(group)


def rebuild_node_groups():
    remove_all_groups()
    check_node_groups()
    return


def is_version(obj):
    return (vars.VERSION_STRING in obj.name or
            utils.get_prop(obj, "RL_Addon_Version") == vars.VERSION_STRING)
