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
import math, os, random
from . import facerig_data, lib, utils, vars
from . import drivers, bones
from . import rigutils
from mathutils import Vector, Matrix, Quaternion


def shrink_slider_coords(coords, by_length):
    d = coords[1] - coords[0]
    l = d.length
    t = max(0, min(by_length / l, 0.5))
    v0 = utils.lerp(coords[0], coords[1], t)
    v1 = utils.lerp(coords[0], coords[1], 1 - t)
    coords[0] = v0
    coords[1] = v1


def objects_have_shape_key(objects, shape_key_name):
    for obj in objects:
        if obj.type == "MESH":
            if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
                if shape_key_name in obj.data.shape_keys.key_blocks:
                    return True
    return False


def is_valid_control_def(control_def, rigify_rig, objects):
    bone_collection = rigify_rig.data.edit_bones if utils.get_mode() == "EDIT" else rigify_rig.pose.bones
    if control_def["widget_type"] == "slider":
        if "blendshapes" in control_def:
            blendshapes = control_def["blendshapes"]
            for shape_key_name in blendshapes:
                if not objects_have_shape_key(objects, shape_key_name):
                    return False
        if "rigify" in control_def:
            control_bones = control_def["rigify"]
            for bone_def in control_bones:
                bone_name = bone_def["bone"]
                if bone_name not in bone_collection:
                    return False
        #if "bones" in control_def:
        #    control_bones = control_def["bones"]
        #    for bone_def in control_bones:
        #        bone_name = bone_def["bone"]
        #        if bone_name not in rigify_rig.pose.bones:
        #            return False
    elif control_def["widget_type"] == "rect":
        if "blendshapes" in control_def:
            blendshapes_x = control_def["blendshapes"]["x"]
            blendshapes_y = control_def["blendshapes"]["y"]
            for shape_key_name in blendshapes_x:
                if not objects_have_shape_key(objects, shape_key_name):
                    return False
            for shape_key_name in blendshapes_y:
                if not objects_have_shape_key(objects, shape_key_name):
                    return False
        if "rigify" in control_def:
            control_bones_x = control_def["rigify"]["horizontal"]
            control_bones_y = control_def["rigify"]["horizontal"]
            for bone_def in control_bones_x:
                bone_name = bone_def["bone"]
                if bone_name not in bone_collection:
                    return False
            for bone_def in control_bones_y:
                bone_name = bone_def["bone"]
                if bone_name not in bone_collection:
                    return False
        #if "bones" in control_def:
        #    control_bones_x = control_def["bones"]["horizontal"]
        #    control_bones_y = control_def["bones"]["horizontal"]
        #    for bone_def in control_bones_x:
        #        bone_name = bone_def["bone"]
        #        if bone_name not in rigify_rig.pose.bones:
        #            return False
        #    for bone_def in control_bones_y:
        #        bone_name = bone_def["bone"]
        #        if bone_name not in rigify_rig.pose.bones:
        #            return False
    return True


def get_facerig_config(chr_cache):
    facial_profile, viseme_profile = chr_cache.get_facial_profile()
    if facial_profile == "EXT":
        return facerig_data.FACERIG_EXT_CONFIG
    elif facial_profile == "STD":
        return facerig_data.FACERIG_STD_CONFIG
    elif facial_profile == "TRA":
        return facerig_data.FACERIG_TRA_CONFIG
    return None


def build_facerig(chr_cache, rigify_rig, meta_rig, cc3_rig):
    prefs = vars.prefs()

    chr_cache.rigify_face_control_color = prefs.rigify_face_control_color
    objects = chr_cache.get_cache_objects()
    wgt_collection = f"WGTS_{cc3_rig.name}_rig"
    WGT_OUTLINE, WGT_GROUPS, WGT_LABELS, WGT_LINES, WGT_SLIDER, WGT_RECT, WGT_NUB, WGT_NAME = \
                                                rigutils.get_expression_widgets(chr_cache, wgt_collection)
    bone_scale = Vector((0.125, 0.125, 0.125))
    R = Matrix.Rotation(90*math.pi/180, 3, 'X')
    slider_controls = {}
    rect_controls = {}

    facial_profile, viseme_profile = chr_cache.get_facial_profile()
    print(f"Building Expression Rig for facial profile: {facial_profile}")

    if rigutils.edit_rig(rigify_rig):
        # place the face rig parent at eye level
        eye_l = bones.get_edit_bone(rigify_rig, "ORG-eye.L")
        eye_r = bones.get_edit_bone(rigify_rig, "ORG-eye.R")
        eye_pos = (eye_l.head + eye_r.head) * 0.5
        z_pos = eye_pos.z
        mch_parent = bones.copy_edit_bone(rigify_rig, "head", "MCH-facerig_parent", "head", 1.0)
        mch_parent.head.z = z_pos
        mch_parent.tail.z = z_pos + 0.1
        bones.copy_edit_bone(rigify_rig, "MCH-facerig_parent", "MCH-facerig", "", 0.5)
        # place the face rig control ~20cm in front of face
        facerig_bone = bones.copy_edit_bone(rigify_rig, "MCH-facerig", "facerig", "MCH-facerig", 1.0)
        facerig_bone.head += Vector((0, -0.2, 0))
        facerig_bone.tail += Vector((0, -0.2, 0))
        bones.copy_edit_bone(rigify_rig, "facerig", "facerig_name", "facerig", 0.8)
        bones.copy_edit_bone(rigify_rig, "facerig", "facerig_groups", "facerig", 0.6)
        bones.copy_edit_bone(rigify_rig, "facerig", "facerig_labels", "facerig", 0.4)
        bones.copy_edit_bone(rigify_rig, "facerig", "MCH-facerig_controls", "facerig", 0.2)
        # add MCH bone for aligned axis based jaw move
        jaw_move = bones.copy_edit_bone(rigify_rig, "jaw_master", "MCH-jaw_move", "ORG-face", 0.5)
        jaw_move.tail = jaw_move.head + Vector((0, jaw_move.length, 0))
        # reparent jaw_master to jaw_move
        jaw_master = bones.get_edit_bone(rigify_rig, "jaw_master")
        jaw_master.parent = jaw_move

        FACERIG_CONFIG = get_facerig_config(chr_cache)

        for control_name, control_def in FACERIG_CONFIG.items():

            if not is_valid_control_def(control_def, rigify_rig, objects):
                utils.log_warn(f"Invalid expression control: {control_name}")
                continue

            if control_def["widget_type"] == "slider":
                zero = utils.inverse_lerp(control_def["range"][0], control_def["range"][1], 0.0)
                indices = control_def["indices"]
                coords = [ WGT_LINES.data.vertices[i].co.copy() for i in indices ]
                #shrink_slider_coords(coords, 0.01)
                line_bone = bones.new_edit_bone(rigify_rig, control_name+"_line", "MCH-facerig_controls")
                line_bone.head = (R @ coords[0] * bone_scale * 1.0) + facerig_bone.head
                line_bone.tail = (R @ utils.lerp(coords[0], coords[1], 0.5) * bone_scale * 1.0) + facerig_bone.head
                line_bone.align_roll(Vector((0, -1, 0)))
                length = 2 * (line_bone.head - line_bone.tail).length
                nub_bone = bones.new_edit_bone(rigify_rig, control_name, line_bone.name)
                nub_bone.head = utils.lerp(line_bone.head, line_bone.tail, zero * 2, clamp=False)
                nub_bone.tail = (line_bone.tail - line_bone.head).normalized() * (length / 2) + nub_bone.head
                nub_bone.align_roll(Vector((0, -1, 0)))
                slider_controls[control_name] = (control_def, line_bone.name, nub_bone.name, length, zero)

            elif control_def["widget_type"] == "rect":
                zero_x = utils.inverse_lerp(control_def["x_range"][0], control_def["x_range"][1], 0.0)
                zero_y = utils.inverse_lerp(control_def["y_range"][0], control_def["y_range"][1], 0.0)
                indices = control_def["indices"]
                coords = [ WGT_LINES.data.vertices[i].co.copy() for i in indices ]
                p_min = Vector((min(coords[0].x, coords[1].x, coords[2].x, coords[3].x),
                                min(coords[0].y, coords[1].y, coords[2].y, coords[3].y), 0))
                p_max = Vector((max(coords[0].x, coords[1].x, coords[2].x, coords[3].x),
                                max(coords[0].y, coords[1].y, coords[2].y, coords[3].y), 0))
                width = (p_max.x - p_min.x)
                height = (p_max.y - p_min.y)
                pB0 = Vector((p_min.x + width / 2, p_min.y, 0.0))
                pB1 = Vector((p_min.x + width / 2, p_min.y + height / 2, 0.0))
                if control_def.get("y_invert") and control_def.get("x_invert"):
                    pN0 = Vector((p_min.x + width * (1-zero_x), p_min.y + height * (1-zero_y), 0))
                elif control_def.get("y_invert"):
                    pN0 = Vector((p_min.x + width * zero_x, p_min.y + height * (1-zero_y), 0))
                elif control_def.get("x_invert"):
                    pN0 = Vector((p_min.x + width * (1-zero_x), p_min.y + height * zero_y, 0))
                else:
                    pN0 = Vector((p_min.x + width * zero_x, p_min.y + height * zero_y, 0))
                pN1 = Vector((pN0.x, pN0.y + height / 2, 0))
                box_bone = bones.new_edit_bone(rigify_rig, control_name+"_box", "MCH-facerig_controls")
                box_bone.head = (R @ pB0 * bone_scale * 1.0) + facerig_bone.head
                box_bone.tail = (R @ pB1 * bone_scale * 1.0) + facerig_bone.head
                box_bone.align_roll(Vector((0, -1, 0)))
                nub_bone = bones.new_edit_bone(rigify_rig, control_name, box_bone.name)
                nub_bone.head = (R @ pN0 * bone_scale * 1.0) + facerig_bone.head
                nub_bone.tail = (R @ pN1 * bone_scale * 1.0) + facerig_bone.head
                nub_bone.align_roll(Vector((0, -1, 0)))
                width *= bone_scale.x
                height *= bone_scale.y
                rect_controls[control_name] = (control_def, box_bone.name, nub_bone.name, width, height, zero_x, zero_y)

    if rigutils.select_rig(rigify_rig):

        bones.set_bone_collection(rigify_rig, "MCH-jaw_move", "MCH", None, None)
        bones.set_bone_collection(rigify_rig, "MCH-facerig", "MCH", None, None)
        bones.set_bone_collection(rigify_rig, "MCH-facerig_controls", "MCH", None, None)
        bones.set_bone_collection(rigify_rig, "MCH-facerig_parent", "MCH", None, None)
        bone_names = ["facerig", "facerig_groups", "facerig_labels", "facerig_name"]
        bone_colors = ["WHITE", "GROUP", "WHITE", "WHITE"]
        bone_shapes = [ WGT_OUTLINE, WGT_GROUPS, WGT_LABELS, WGT_NAME ]
        bone_selectable = [ True, False, False, False ]
        for i, bone_name in enumerate(bone_names):
            pose_bone = bones.get_pose_bone(rigify_rig, bone_name)
            if pose_bone:
                bones.set_bone_collection(rigify_rig, pose_bone, "Face (UI)", None, None)
                bones.set_bone_color(rigify_rig, pose_bone, bone_colors[i])
                pose_bone.custom_shape = bone_shapes[i]
                pose_bone.custom_shape_scale_xyz = bone_scale
                pose_bone.bone.hide_select = not bone_selectable[i]
                pose_bone.use_custom_shape_bone_size = False
                bones.keep_locks(pose_bone, no_bake=True)

        for slider_name, slider_def in slider_controls.items():
            control_def, line_bone_name, nub_bone_name, length, zero = slider_def
            line_bone = bones.get_pose_bone(rigify_rig, line_bone_name)
            nub_bone = bones.get_pose_bone(rigify_rig, nub_bone_name)
            line_bone.custom_shape = WGT_SLIDER
            nub_bone.custom_shape = WGT_NUB
            line_bone.bone.hide_select = True
            bones.keep_locks(line_bone, no_bake=True)
            nub_bone.use_custom_shape_bone_size = False
            nub_bone.custom_shape_scale_xyz = bone_scale
            nub_bone.lock_location = [True, False, True]
            nub_bone.lock_rotation = [True, True, True]
            nub_bone.lock_scale = [True, True, True]
            bones.keep_locks(nub_bone)
            bones.set_bone_collection(rigify_rig, line_bone, "Face (UI)", None, None)
            bones.set_bone_color(rigify_rig, line_bone, "FACERIG_DARK", "FACERIG_DARK", "FACERIG_DARK", chr_cache=chr_cache)
            bones.set_bone_collection(rigify_rig, nub_bone, "Face (Expressions)", None, None)
            bones.set_bone_color(rigify_rig, nub_bone, "FACERIG", "FACERIG", "FACERIG", chr_cache=chr_cache)
            control_range = control_def["range"]
            min_y = (length * zero) * control_range[0]
            max_y = length * (1 - zero) * control_range[1]
            drivers.add_custom_float_property(line_bone, "slider_length", length)
            bones.add_limit_location_constraint(rigify_rig, nub_bone_name, 0, min_y, 0, 0, max_y, 0, space="LOCAL")

        for rect_name, rect_def in rect_controls.items():
            control_def, box_bone_name, nub_bone_name, width, height, zero_x, zero_y = rect_def
            box_bone = bones.get_pose_bone(rigify_rig, box_bone_name)
            nub_bone = bones.get_pose_bone(rigify_rig, nub_bone_name)
            box_bone.custom_shape = WGT_RECT
            nub_bone.custom_shape = WGT_NUB
            box_bone.bone.hide_select = True
            bones.keep_locks(box_bone, no_bake=True)
            aspect = width / height
            box_bone.custom_shape_scale_xyz = Vector((aspect,1,1))
            nub_bone.use_custom_shape_bone_size = False
            nub_bone.custom_shape_scale_xyz = bone_scale
            nub_bone.lock_location = [False, False, True]
            nub_bone.lock_rotation = [True, True, True]
            nub_bone.lock_scale = [True, True, True]
            bones.keep_locks(nub_bone)
            bones.set_bone_collection(rigify_rig, box_bone, "Face (UI)", None, None)
            bones.set_bone_color(rigify_rig, box_bone, "FACERIG_DARK", "FACERIG_DARK", "FACERIG_DARK", chr_cache=chr_cache)
            bones.set_bone_collection(rigify_rig, nub_bone, "Face (Expressions)", None, None)
            bones.set_bone_color(rigify_rig, nub_bone, "FACERIG", "FACERIG", "FACERIG", chr_cache=chr_cache)
            control_range_x = control_def["x_range"]
            control_range_y = control_def["y_range"]
            if control_def.get("x_invert"):
                min_x = -(width * (1 - zero_x)) * control_range_x[0]
                max_x = -width * zero_x * control_range_x[1]
            else:
                min_x = (width * zero_x) * control_range_x[0]
                max_x = width * (1 - zero_x) * control_range_x[1]
            if control_def.get("y_invert"):
                min_y = -height * (1 - zero_y) * control_range_y[1]
                max_y = -(height * zero_y) * control_range_y[0]
            else:
                min_y = (height * zero_y) * control_range_y[0]
                max_y = height * (1 - zero_y) * control_range_y[1]

            drivers.add_custom_float_property(line_bone, "x_slider_length", width)
            drivers.add_custom_float_property(line_bone, "y_slider_length", height)
            bones.add_limit_location_constraint(rigify_rig, nub_bone_name, min_x, min_y, 0, max_x, max_y, 0, True, space="LOCAL")


def get_generated_controls(chr_cache, rigify_rig):
    slider_controls = {}
    rect_controls = {}

    FACERIG_CONFIG = get_facerig_config(chr_cache)

    for control_name, control_def in FACERIG_CONFIG.items():

        if control_def["widget_type"] == "slider":
            zero_point = utils.inverse_lerp(control_def["range"][0], control_def["range"][1], 0.0)
            line_bone_name = control_name + "_line"
            nub_bone_name = control_name
            line_pose_bone = rigify_rig.pose.bones[line_bone_name]
            line_bone = line_pose_bone.bone
            length = line_pose_bone["slider_length"] if "slider_length" in line_pose_bone else line_bone.length * 2
            slider_controls[control_name] = (control_def, line_bone_name, nub_bone_name, length, zero_point)

        if control_def["widget_type"] == "rect":
            zero_x = utils.inverse_lerp(control_def["x_range"][0], control_def["x_range"][1], 0.0)
            zero_y = utils.inverse_lerp(control_def["y_range"][0], control_def["y_range"][1], 0.0)
            box_bone_name = control_name+"_box"
            nub_bone_name = control_name
            box_pose_bone = rigify_rig.pose.bones[box_bone_name]
            box_bone = box_pose_bone.bone
            width = box_pose_bone["x_slider_length"] if "x_slider_length" in box_pose_bone else box_bone.length * 2
            height = box_pose_bone["y_slider_length"] if "y_slider_length" in box_pose_bone else box_bone.length * 2
            rect_controls[control_name] = (control_def, box_bone_name, nub_bone_name, width, height, zero_x, zero_y)

    return slider_controls, rect_controls


def collect_driver_defs(chr_cache, rigify_rig, slider_controls, rect_controls):

    shape_key_driver_defs = {}
    bone_driver_defs = {}

    # collect slider control data into shapekey and bone driver defs
    for slider_name, slider_def in slider_controls.items():

        control_def, line_bone_name, nub_bone_name, length, zero_point = slider_def
        control_range_y = control_def["range"]
        min_y = (length * zero_point) * control_range_y[0]
        max_y = length * (1 - zero_point) * control_range_y[1]
        allow_negative = control_def.get("negative", False)

        if "blendshapes" in control_def:

            num_keys = len(control_def["blendshapes"])
            for i, (shape_key_name, shape_key_value) in enumerate(control_def["blendshapes"].items()):
                distance = min_y if shape_key_value == control_range_y[0] else max_y
                var_axis = facerig_data.LOC_AXES.get("y")[1]
                if shape_key_name not in shape_key_driver_defs:
                    shape_key_driver_defs[shape_key_name] = {}
                key_control_def = {
                    "value": abs(shape_key_value),
                    "distance": distance,
                    "var_axis": var_axis,
                    "num_keys": num_keys,
                    "negative": allow_negative,
                }
                shape_key_driver_defs[shape_key_name][nub_bone_name] = key_control_def

        rigify_bones = control_def.get("rigify")

        if rigify_bones:
            for i, bone_def in enumerate(rigify_bones):
                bone_name = bone_def["bone"]
                if bone_name in rigify_rig.pose.bones:
                    if "translation" in bone_def:
                        prop, axis, index = facerig_data.LOC_AXES.get(bone_def["axis"], (None, None, None))
                        offset = bone_def["offset"] / 100 # convert from
                        scalar = bone_def["translation"] / 100 # cm to m
                    else:
                        prop, axis, index = facerig_data.ROT_AXES.get(bone_def["axis"], (None, None, None))
                        offset = bone_def["offset"] * math.pi/180 # convert angles
                        scalar = bone_def["rotation"] * math.pi/180 # to radians
                    if axis:
                        driver_id = (bone_name, prop, index)
                        var_axis = facerig_data.LOC_AXES.get("y")[1]
                        bone_control_def = {
                            "bone": bone_def["bone"],
                            "offset": offset,
                            "scalar": scalar,
                            "distance": [min_y, max_y],
                            "var_axis": var_axis
                        }
                        if driver_id not in bone_driver_defs:
                            bone_driver_defs[driver_id] = {}
                        bone_driver_defs[driver_id][nub_bone_name] = bone_control_def

    # collect rect control data into shape key and bone driver defs
    for rect_name, rect_def in rect_controls.items():

        control_def, box_bone_name, nub_bone_name, width, height, zero_x, zero_y = rect_def
        control_range_x = control_def["x_range"]
        control_range_y = control_def["y_range"]
        min_x = (width * zero_x) * control_range_x[0]
        max_x = width * (1 - zero_x) * control_range_x[1]
        min_y = -(height * zero_y) * control_range_y[0]
        max_y = -height * (1 - zero_y) * control_range_y[1]
        allow_negative = control_def.get("negative", False)

        ctrl_axes = [
            ("horizontal", "x", min_x, max_x, control_range_x),
            ("vertical", "y", min_y, max_y, control_range_y)
        ]

        if "blendshapes" in control_def:

            for ctrl_dir, ctrl_axis, min_d, max_d, control_range in ctrl_axes:

                num_keys = len(control_def["blendshapes"][ctrl_axis])
                parent = control_def.get(f"{ctrl_axis}_parent")
                for i, (shape_key_name, shape_key_value) in enumerate(control_def["blendshapes"][ctrl_axis].items()):
                    distance = min_d if utils.same_sign(shape_key_value, control_range[0]) else max_d
                    var_axis = facerig_data.LOC_AXES.get(ctrl_axis)[1]
                    if shape_key_name not in shape_key_driver_defs:
                        shape_key_driver_defs[shape_key_name] = {}
                    key_control_def = {
                        "value": abs(shape_key_value),
                        "distance": distance,
                        "var_axis": var_axis,
                        "num_keys": num_keys,
                        "negative": allow_negative,
                    }
                    shape_key_driver_defs[shape_key_name][nub_bone_name] = key_control_def

        rigify_bones = control_def.get("rigify")

        if rigify_bones:

            for ctrl_dir, ctrl_axis, min_d, max_d, control_range in ctrl_axes:
                for bone_def in rigify_bones[ctrl_dir]:
                    bone_name = bone_def["bone"]
                    if bone_name in rigify_rig.pose.bones:
                        if "translation" in bone_def:
                            prop, axis, index = facerig_data.LOC_AXES.get(bone_def["axis"], (None, None, None))
                            offset = bone_def["offset"] / 100 # convert from
                            scalar = bone_def["translation"] / 100 # cm to m
                        else:
                            prop, axis, index = facerig_data.ROT_AXES.get(bone_def["axis"], (None, None, None))
                            offset = bone_def["offset"] * math.pi/180 # convert angles
                            scalar = bone_def["rotation"] * math.pi/180 # to radians
                        if axis:
                            driver_id = (bone_name, prop, index)
                            var_axis = facerig_data.LOC_AXES.get(ctrl_axis)[1]
                            bone_control_def = {
                                "bone": bone_def["bone"],
                                "offset": offset,
                                "scalar": scalar,
                                "distance": [min_d, max_d],
                                "var_axis": var_axis
                            }
                            if driver_id not in bone_driver_defs:
                                bone_driver_defs[driver_id] = {}
                            bone_driver_defs[driver_id][nub_bone_name] = bone_control_def

    return shape_key_driver_defs, bone_driver_defs


def fvar(float_value):
    return "{0:0.6f}".format(float_value).rstrip('0').rstrip('.')


def build_facerig_drivers(chr_cache, rigify_rig):

    # first drive the shape keys on any other body objects from the head body object
    # expression rig will then override these
    drivers.add_body_shape_key_drivers(chr_cache, True)

    BONE_CLEAR_CONSTRAINTS = [
            "MCH-eye.L", "MCH-eye.R"
        ]

    FACERIG_CONFIG = get_facerig_config(chr_cache)

    # initialize target bone rotation modes and clear unwanted constraints
    for control_name, control_def in FACERIG_CONFIG.items():

        if control_def["widget_type"] == "slider":
            rigify_bones = control_def.get("rigify")
            if rigify_bones:
                for bone_def in rigify_bones:
                    bone_name = bone_def["bone"]
                    if bone_name in rigify_rig.pose.bones:
                        pose_bone = rigify_rig.pose.bones[bone_name]
                        pose_bone.rotation_mode = "XYZ"
                        if bone_name in BONE_CLEAR_CONSTRAINTS:
                            bones.clear_constraints(rigify_rig, bone_name)

        if control_def["widget_type"] == "rect":
            rigify_bones = control_def.get("rigify")
            if rigify_bones:
                for axis_dir, bone_list in rigify_bones.items():
                    for bone_def in bone_list:
                        bone_name = bone_def["bone"]
                        if bone_name in rigify_rig.pose.bones:
                            pose_bone = rigify_rig.pose.bones[bone_name]
                            pose_bone.rotation_mode = "XYZ"
                            if bone_name in BONE_CLEAR_CONSTRAINTS:
                                bones.clear_constraints(rigify_rig, bone_name)

    slider_controls, rect_controls = get_generated_controls(chr_cache, rigify_rig)
    objects = chr_cache.get_cache_objects()

    if rigutils.select_rig(rigify_rig):

        bones.set_bone_collection_visibility(rigify_rig, "Face", None, False)
        bones.set_bone_collection_visibility(rigify_rig, "Face (Primary)", None, False)
        bones.set_bone_collection_visibility(rigify_rig, "Face (Secondary)", None, False)

        facerig_bone = bones.get_pose_bone(rigify_rig, "facerig")
        if "head_follow" not in facerig_bone:
            drivers.add_custom_float_property(facerig_bone, "head_follow", 0.5,
                                              value_min=0.0, value_max=2.0,
                                              description="How much the expression rig follows the head movements")
        data_path = facerig_bone.path_from_id("[\"head_follow\"]")
        bones.clear_constraints(rigify_rig, "MCH-facerig")
        child_con = bones.add_child_of_constraint(rigify_rig, rigify_rig, "root", "MCH-facerig", 1.0)
        loc_con = bones.add_copy_location_constraint(rigify_rig, rigify_rig, "MCH-facerig_parent", "MCH-facerig", 0.2)
        rot_con1 = bones.add_copy_rotation_constraint(rigify_rig, rigify_rig, "MCH-facerig_parent", "MCH-facerig", 0.6,
                                                     use_x=False, use_y=False, use_z=True)
        rot_con2 = bones.add_copy_rotation_constraint(rigify_rig, rigify_rig, "MCH-facerig_parent", "MCH-facerig", 0.6,
                                                     use_x=True, use_y=True, use_z=False)
        bones.add_constraint_influence_driver(rigify_rig, "MCH-facerig",
                                              rigify_rig, data_path, "rf",
                                              constraint=child_con, expression="(1.0 if rf else 0.0)")
        bones.add_constraint_influence_driver(rigify_rig, "MCH-facerig",
                                              rigify_rig, data_path, "rf",
                                              loc_con)
        bones.add_constraint_influence_driver(rigify_rig, "MCH-facerig",
                                              rigify_rig, data_path, "rf",
                                              rot_con1)
        bones.add_constraint_influence_driver(rigify_rig, "MCH-facerig",
                                              rigify_rig, data_path, "rf",
                                              rot_con2, expression="(rf - 1)")

        shape_key_driver_defs, bone_driver_defs = collect_driver_defs(chr_cache, rigify_rig,
                                                                      slider_controls, rect_controls)

        # build shape key drivers from shape key driver defs
        for shape_key_name, shape_key_driver_def in shape_key_driver_defs.items():
            expression = ""
            var_defs = []
            vidx = 0
            num_key_controls = len(shape_key_driver_def)
            allow_negative = False

            for nub_bone_name, key_control_def in shape_key_driver_def.items():
                if nub_bone_name in rigify_rig.pose.bones:
                    num_keys = key_control_def["num_keys"]
                    var_axis = key_control_def["var_axis"]
                    distance = key_control_def["distance"]
                    if key_control_def["negative"]:
                        allow_negative = True
                    value = key_control_def["value"]
                    var_name = f"var{vidx}"
                    vidx += 1
                    if expression:
                        expression += "+"
                    use_negative = num_keys == 1 or num_key_controls > 1
                    if use_negative:
                        expression += f"({fvar(value)}*{var_name}/{fvar(distance)})"
                    else:
                        expression += f"max({fvar(value)}*{var_name}/{fvar(distance)},0)"

                    var_def = [var_name,
                               "TRANSFORMS",
                               nub_bone_name,
                               var_axis,
                               "LOCAL_SPACE"]
                    var_defs.append(var_def)

            allow_negative = False
            shape_key_range = 1.5
            if "Eye" in shape_key_name and "_Look_" in shape_key_name:
                shape_key_range = 2.0
            high = shape_key_range
            low = -shape_key_range if allow_negative else 0
            expression = f"max({low},min({high},{expression}))"
            driver_def = ["SCRIPTED", expression]

            for obj in objects:
                if utils.object_has_shape_keys(obj):
                    drivers.add_shape_key_driver(rigify_rig, obj, shape_key_name, driver_def, var_defs, 1.0)

        # build bone transform drivers from bone driver defs
        for driver_id, bone_driver_def in bone_driver_defs.items():
            bone_name, prop, index = driver_id
            expression = ""
            var_defs = []
            vidx = 0
            for nub_bone_name, bone_control_def in bone_driver_def.items():
                offset = bone_control_def["offset"]
                scalar = bone_control_def["scalar"]
                var_axis = bone_control_def["var_axis"]
                distance = bone_control_def["distance"]
                var_name = f"var{vidx}"
                vidx += 1
                if expression:
                    expression += "+"
                #expression += f"({offset}+{scalar}*(max({var_name}/{distance[1]},0)-max({var_name}/{distance[0]},0)))"
                #if offset != 0.0:
                #    expression += f"({fvar(offset)}+{fvar(scalar)}*({var_name}/{fvar(distance[1])}))"
                #else:
                expression += f"({fvar(scalar)}*({var_name}/{fvar(distance[1])}))"
                var_def = [var_name,
                           "TRANSFORMS",
                           nub_bone_name,
                           var_axis,
                           "LOCAL_SPACE"]
                var_defs.append(var_def)
            driver_def = ["SCRIPTED", prop, index, expression]

            drivers.add_bone_driver(rigify_rig, bone_name, driver_def, var_defs, 1.0)


def get_key_object(objects, shape_key_name):
    for obj in objects:
        key = drivers.get_shape_key(obj, shape_key_name)
        if key:
            return obj
    return None


def build_facerig_retarget_drivers(chr_cache, rigify_rig, source_rig, source_objects, shape_key_only=False, arkit=False):

    bone_drivers = {}

    FACERIG_CONFIG = get_facerig_config(chr_cache)

    if rigutils.select_rig(rigify_rig):

        facial_profile, viseme_profile = chr_cache.get_facial_profile()

        for control_name, control_def in FACERIG_CONFIG.items():

            if control_def["widget_type"] == "rect":
                prefixes = [ ("x_", "x", "horizontal", "_box",  0),
                             ("y_", "y", "vertical",   "_box",  1) ]
            else:
                prefixes = [ ("",   "",  "",           "_line", 1) ]

            for prefix, key_group, bone_group, line_suffix, index in prefixes:
                method = control_def.get(f"{prefix}method", "SUM")
                parent = control_def.get(f"{prefix}parent", "NONE")
                control_range = control_def.get(f"{prefix}range")
                control_scale = 1 / abs(control_range[1] - control_range[0])
                blend_shapes = control_def.get("blendshapes")
                if blend_shapes and key_group:
                    blend_shapes = blend_shapes[key_group]
                rl_bones = control_def.get("bones")
                if rl_bones and bone_group:
                    rl_bones = rl_bones[bone_group]
                line_bone_name = control_name + line_suffix
                line_bone = bones.get_pose_bone(rigify_rig, line_bone_name)
                slider_length = line_bone[f"{prefix}slider_length"] if f"{prefix}slider_length" in line_bone else line_bone.bone.length * 2
                #inv = -1 if control_def.get(f"{prefix}invert") else 1
                inv = 1
                if key_group == "y":
                    inv *= -1
                slider_length *= control_scale * inv

                driver_id = (control_name, "location", index)

                if not shape_key_only and source_rig and rl_bones and len(rl_bones) > 0:

                    bone_drivers[driver_id] = { "method": method,
                                                "parent": parent,
                                                "length": slider_length,
                                                "bones": [] }

                    for bone_def in rl_bones:
                        source_name = bone_def["bone"]
                        if source_name in source_rig.pose.bones:
                            if "translation" in bone_def:
                                prop, prop_axis, prop_index = facerig_data.LOC_AXES.get(bone_def["axis"], (None, None, None))
                                offset = bone_def["offset"]
                                scalar = bone_def["translation"]
                            else:
                                prop, prop_axis, prop_index = facerig_data.ROT_AXES.get(bone_def["axis"], (None, None, None))
                                offset = bone_def["offset"] * math.pi / 180
                                scalar = bone_def["rotation"] * math.pi / 180
                            bone_drivers[driver_id]["bones"].append({ "bone": source_name,
                                                                      "scale": slider_length/(control_range[1] * scalar),
                                                                      "offset": offset,
                                                                      "axis": prop_axis })
                elif blend_shapes:

                    bone_drivers[driver_id] = { "method": method,
                                                "parent": parent,
                                                "length": slider_length,
                                                "shape_keys": [] }

                    left_shape = right_shape = None
                    for i, (blend_shape_name, blend_shape_value) in enumerate(blend_shapes.items()):
                        # if 'retarget' list exists in control def, only retarget blendshapes
                        # in the list, to avoid uncontrolled duplicate retargets
                        if "retarget" in control_def:
                            if blend_shape_name not in control_def["retarget"]:
                                continue
                        # if retargeting from an ARKit proxy, remap the shapes and only target these shapes
                        if arkit:
                            arkit_blend_shape_name = arkit_find_target_blend_shape(facial_profile, blend_shape_name)
                            if arkit_blend_shape_name:
                                blend_shape_name = arkit_blend_shape_name
                            else:
                                continue
                        if utils.same_sign(blend_shape_value, control_range[0]):
                            left_shape = (blend_shape_name, abs(blend_shape_value), slider_length/control_range[0])
                        elif utils.same_sign(blend_shape_value, control_range[1]):
                            right_shape = (blend_shape_name, abs(blend_shape_value), slider_length/control_range[1])

                        if left_shape and right_shape:
                            if left_shape:
                                bone_drivers[driver_id]["shape_keys"].append({ "shape_key": left_shape[0],
                                                                                "value": left_shape[1],
                                                                                "scale": left_shape[2] })
                            if right_shape:
                                bone_drivers[driver_id]["shape_keys"].append({ "shape_key": right_shape[0],
                                                                                "value": right_shape[1],
                                                                                "scale": right_shape[2] })
                            left_shape = right_shape = None

                    if left_shape:
                        bone_drivers[driver_id]["shape_keys"].append({ "shape_key": left_shape[0],
                                                                        "value": left_shape[1],
                                                                        "scale": left_shape[2] })
                    if right_shape:
                        bone_drivers[driver_id]["shape_keys"].append({ "shape_key": right_shape[0],
                                                                        "value": right_shape[1],
                                                                        "scale": right_shape[2] })

        for driver_id, driver_def in bone_drivers.items():
            bone_name, prop, index = driver_id
            parent = driver_def["parent"]

            if parent != "NONE":
                parent_id = (parent, prop, index)
                parent_def = bone_drivers[parent_id]
                expression, var_defs = build_retarget_driver(chr_cache, rigify_rig, parent_id, parent_def,
                                                             source_rig, source_objects,
                                                             no_driver=True, length_override=abs(driver_def["length"]),
                                                             arkit=arkit)
                build_retarget_driver(chr_cache, rigify_rig, driver_id, driver_def,
                                      source_rig, source_objects,
                                      pre_expression=expression, pre_var_defs=var_defs,
                                      arkit=arkit)
            else:
                build_retarget_driver(chr_cache, rigify_rig, driver_id, driver_def, source_rig, source_objects,
                                      arkit=arkit)

        update_facerig_color(None, chr_cache=chr_cache)


def build_retarget_driver(chr_cache, rigify_rig, driver_id, driver_def, source_rig, source_objects,
                                     no_driver=False, pre_expression=None,
                                     pre_var_defs=None, length_override=None, arkit=False):
    bone_name, prop, index = driver_id
    method = driver_def["method"]
    parent = driver_def["parent"]
    length = abs(driver_def["length"])
    if length_override is not None:
        length_override = abs(length_override)
    pose_bone = bones.get_pose_bone(rigify_rig, bone_name)

    expression = ""
    var_defs = []
    prop_defs = []

    vidx = 0 if not pre_var_defs else len(pre_var_defs)

    if "shape_keys" in driver_def:

        count = 0
        shape_key_defs = driver_def["shape_keys"]
        for key_def in shape_key_defs:
            scale = key_def["scale"]
            value = key_def["value"]
            if length_override:
                scale *= length_override / length
                length = length_override
            shape_key_name = key_def["shape_key"]
            obj = get_key_object(source_objects, shape_key_name)
            if obj:
                var_name = f"var{vidx}"
                if count > 0:
                    expression += "+"
                var_expression = f"({var_name}*{fvar(scale)}/{fvar(value)})"
                if arkit:
                    var_expression = add_arkit_driver_func(chr_cache, var_expression, length,
                                                           shape_key_name, prop_defs)
                expression += var_expression
                var_defs.append((var_name, shape_key_name))
                vidx += 1
                count += 1

        shape_key_range = length
        low = -shape_key_range
        high = shape_key_range

        if bone_name == "CTRL_C_eye" and method == "AVERAGE" and count == 4:
            count = 2

        if expression:
            expression = f"({expression})"

        if expression and method == "AVERAGE" and count > 1:
            expression = f"min({high},max({low},{expression}/{count}))"

        if expression and parent != "NONE" and pre_expression and pre_var_defs:
            expression = f"{expression} - {pre_expression}"
            var_defs.extend(pre_var_defs)

        if expression and not no_driver:
            driver = drivers.make_driver(pose_bone, prop, "SCRIPTED", driver_expression=expression, index=index)
            if driver:
                for var_name, shape_key_name in var_defs:
                    for obj in source_objects:
                        key = drivers.get_shape_key(obj, shape_key_name)
                        if key:
                            # target_type="MESH", data_path="shape_keys.key_blocks[\"{shape_key}\"].value"
                            data_path = "shape_keys." + key.path_from_id("value")
                            var = drivers.make_driver_var(driver,
                                                        "SINGLE_PROP",
                                                        var_name,
                                                        obj.data,
                                                        target_type="MESH",
                                                        data_path=data_path)
                            break
                for var_name, prop_obj, prop_name in prop_defs:
                    # target_type="MESH", data_path="shape_keys.key_blocks[\"{shape_key}\"].value"
                    data_path = f"[\"{prop_name}\"]"
                    var = drivers.make_driver_var(driver,
                                                  "SINGLE_PROP",
                                                  var_name,
                                                  prop_obj,
                                                  target_type="OBJECT",
                                                  data_path=data_path)

    if source_rig and "bones" in driver_def:

        count = 0
        bone_defs = driver_def["bones"]
        for bone_def in bone_defs:
            scale = bone_def["scale"]
            axis = bone_def["axis"]
            offset = bone_def["offset"]
            source_name = bone_def["bone"]
            if source_name in source_rig.pose.bones:
                var_name = f"var{vidx}"
                if count > 0:
                    expression += "+"
                #expression += f"(({var_name}+{fvar(offset)})*{fvar(scale)})"
                expression += f"(({var_name})*{fvar(scale)})"
                var_defs.append((var_name, source_name, axis))
                vidx += 1
                count += 1

        shape_key_range = length
        low = -shape_key_range
        high = shape_key_range

        if expression:
            expression = f"min({high},max({low},{expression}))"

        if expression and method == "AVERAGE" and count > 1:
            expression = f"({expression}/{count})"

        if expression and parent != "NONE" and pre_expression and pre_var_defs:
            expression = f"{expression} - {pre_expression}"
            var_defs.extend(pre_var_defs)

        if expression and not no_driver:
            bones.set_bone_color(rigify_rig, pose_bone, "DRIVER", "DRIVER", "DRIVER", chr_cache=chr_cache)
            driver = drivers.make_driver(pose_bone, prop, "SCRIPTED", driver_expression=expression, index=index)
            if driver:
                for var_name, source_name, axis in var_defs:
                    var = drivers.make_driver_var(driver,
                                                    "TRANSFORMS",
                                                    var_name,
                                                    source_rig,
                                                    bone_target=source_name,
                                                    transform_type=axis,
                                                    transform_space="LOCAL_SPACE")

    return expression, var_defs


def remove_facerig_retarget_drivers(chr_cache, rigify_rig: bpy.types.Object):
    if rigutils.select_rig(rigify_rig):
        FACERIG_CONFIG = get_facerig_config(chr_cache)
        for control_name, control_def in FACERIG_CONFIG.items():
            if control_name in rigify_rig.pose.bones:
                pose_bone = rigify_rig.pose.bones[control_name]
                pose_bone.driver_remove("location", 0)
                pose_bone.driver_remove("location", 1)
        update_facerig_color(None, chr_cache=chr_cache)


def clear_expression_pose(chr_cache, rigify_rig, selected=False):
    FACERIG_CONFIG = get_facerig_config(chr_cache)
    if selected:
        selected_names = []
        if bpy.context.selected_bones:
            selected_names = [ b.name for b in bpy.context.selected_bones ]
        elif bpy.context.selected_pose_bones:
            selected_names = [ b.name for b in bpy.context.selected_pose_bones ]
        control_bones = []
        for control_bone_name in FACERIG_CONFIG:
            if control_bone_name in rigify_rig.pose.bones and control_bone_name in selected_names:
                control_bones.append(control_bone_name)
    else:
        control_bones = [ "MCH-jaw_move", "jaw_master", "MCH-jaw_master" ]
        for control_bone_name in FACERIG_CONFIG:
            if control_bone_name in rigify_rig.pose.bones:
                control_bones.append(control_bone_name)

    state = bones.store_armature_settings(rigify_rig, include_selection=True)
    vis = bones.store_bone_locks_visibility(rigify_rig)
    bones.clear_pose(rigify_rig, control_bones)
    bones.restore_bone_locks_visibility(rigify_rig, vis)
    bones.restore_armature_settings(rigify_rig, state, include_selection=True)


def control_bone_has_driver(rigify_rig, control_bone_name):
    try:
        search = f"[\"{control_bone_name}\"]"
        for driver in rigify_rig.animation_data.drivers:
            data_path = driver.data_path
            if data_path.endswith("location"):
                if search in data_path:
                    return True
    except: ...
    return False



def update_facerig_color(context, chr_cache=None):
    props = vars.props()
    if not chr_cache:
        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)
    if chr_cache:
        FACERIG_CONFIG = get_facerig_config(chr_cache)
        rigify_rig = chr_cache.get_armature()
        if rigify_rig and "facerig" in rigify_rig.pose.bones:
            for control_bone_name, control_def in FACERIG_CONFIG.items():
                if control_bone_has_driver(rigify_rig, control_bone_name):
                    color_code = "DRIVER"
                else:
                    color_code = "FACERIG"
                bones.set_bone_color(rigify_rig, control_bone_name, color_code, color_code, color_code, chr_cache=chr_cache)
                if control_def["widget_type"] == "rect":
                    lines_bone_name = control_bone_name + "_box"
                else:
                    lines_bone_name = control_bone_name + "_line"
                bones.set_bone_color(rigify_rig, lines_bone_name, "FACERIG_DARK", "FACERIG_DARK", "FACERIG_DARK", chr_cache=chr_cache)


def is_position_locked(rig):
    if "facerig" in rig.pose.bones:
        return rig.pose.bones["facerig"].bone.hide_select


def toggle_lock_position(chr_cache, rig):
    FACERIG_CONFIG = get_facerig_config(chr_cache)
    bone_names = ["facerig", "facerig_groups", "facerig_labels", "facerig_name"]
    bone_selectable = [ True, False, False, False ]
    is_locked = is_position_locked(rig)
    for i, bone_name in enumerate(bone_names):
        if bone_name in rig.pose.bones:
            pose_bone = rig.pose.bones[bone_name]
            if bone_selectable[i]:
                pose_bone.bone.hide_select = not is_locked
            else:
                pose_bone.bone.hide_select = True
    # make sure the controls selection properties are correct
    for control_name in FACERIG_CONFIG:
        if control_name in rig.pose.bones:
            pose_bone = rig.pose.bones[control_name]
            pose_bone.bone.hide_select = False
        if control_name+"_line" in rig.pose.bones:
            pose_bone = rig.pose.bones[control_name+"_line"]
            pose_bone.bone.hide_select = True
        if control_name+"_box" in rig.pose.bones:
            pose_bone = rig.pose.bones[control_name+"_box"]
            pose_bone.bone.hide_select = True


def build_arkit_bone_constraints(chr_cache, rigify_rig, proxy_rig):
    con1 = bones.add_copy_rotation_constraint(proxy_rig, rigify_rig, "head", "head")
    con2 = bones.add_copy_rotation_constraint(proxy_rig, rigify_rig, "head", "neck", 0.25)
    con3 = bones.add_copy_rotation_constraint(proxy_rig, rigify_rig, "offset", "head", use_offset=True, space="LOCAL")
    con4 = bones.add_copy_rotation_constraint(proxy_rig, rigify_rig, "offset", "neck", use_offset=True, space="LOCAL")
    con1.name = con1.name + "_ARKit_Proxy"
    con2.name = con2.name + "_ARKit_Proxy"
    con3.name = con1.name + "_ARKit_Proxy"
    con4.name = con2.name + "_ARKit_Proxy"
    data_path = proxy_rig.path_from_id("[\"head_blend\"]")
    bones.add_constraint_influence_driver(rigify_rig, "head",
                                          proxy_rig, data_path, "var_head_blend", con1, expression="var_head_blend*0.01")
    bones.add_constraint_influence_driver(rigify_rig, "neck",
                                          proxy_rig, data_path, "var_head_blend", con2, expression="var_head_blend*0.005")
    bones.add_constraint_influence_driver(rigify_rig, "head",
                                          proxy_rig, data_path, "var_head_blend", con3, expression="var_head_blend*0.01")
    bones.add_constraint_influence_driver(rigify_rig, "head",
                                          proxy_rig, data_path, "var_head_blend", con4, expression="var_head_blend*0.01")

    offset_bone = proxy_rig.pose.bones["offset"]
    offset_bone.rotation_mode = "XYZ"
    bones.add_bone_custom_props_driver(proxy_rig, "offset", "rotation_euler", 0, proxy_rig, "[\"head_pitch_offset\"]", "P", "-P")
    bones.add_bone_custom_props_driver(proxy_rig, "offset", "rotation_euler", 2, proxy_rig, "[\"head_roll_offset\"]", "R", "-R")
    bones.add_bone_custom_props_driver(proxy_rig, "offset", "rotation_euler", 1, proxy_rig, "[\"head_yaw_offset\"]", "Y", "Y")


def remove_arkit_bone_constraints(chr_cache, rigify_rig):
    head_bone = bones.get_pose_bone(rigify_rig, "head")
    neck_bone = bones.get_pose_bone(rigify_rig, "neck")
    all_bones = []
    if head_bone:
        all_bones.append(head_bone)
    if neck_bone:
        all_bones.append(neck_bone)
    for bone in all_bones:
        remove = []
        for con in bone.constraints:
            if utils.strip_name(con.name).endswith("_ARKit_Proxy"):
                remove.append(con)
        for con in remove:
            bone.constraints.remove(con)


def generate_arkit_proxy(chr_cache):
    if chr_cache and chr_cache.rigified:

        remove_arkit_proxy(chr_cache)

        rigify_rig = chr_cache.get_armature()
        facial_profile, viseme_profile = chr_cache.get_facial_profile()
        if rigify_rig and facial_profile in facerig_data.ARKIT_SHAPE_KEY_TARGETS:

            neck_bone = bones.get_pose_bone(rigify_rig, "neck")
            root_bone = bones.get_pose_bone(rigify_rig, "root")
            M = rigify_rig.matrix_world @ neck_bone.matrix
            loc = M @ Vector((-0.4, -0.05, -0.05))
            rot = (rigify_rig.matrix_world @ root_bone.matrix).to_quaternion()

            chr_collections = utils.get_object_scene_collections(rigify_rig)

            objects = lib.get_object(["RL_ARKit_Proxy", "RL_ARKit_Proxy_Head"])
            rig_name = f"{chr_cache.character_name}_ARKit_Proxy"
            mesh_name = f"{chr_cache.character_name}_ARKit_Proxy_Head"
            proxy_rig = None
            proxy_mesh = None
            for obj in objects:
                utils.move_object_to_scene_collections(obj, chr_collections)
                if obj.type == "ARMATURE":
                    obj.name = rig_name
                    obj.data.name = rig_name
                    proxy_rig = obj
                elif obj.type == "MESH":
                    obj.name = mesh_name
                    obj.data.name = mesh_name
                    proxy_mesh = obj
                obj["arkit_proxy"] = "fDsOJtp42n68X0e4ETVP"

            if proxy_rig and proxy_mesh:
                proxy_rig.location = loc
                utils.set_transform_rotation(proxy_rig, rot)

            chr_cache.arkit_proxy = proxy_rig

            build_arkit_proxy_drivers(chr_cache, rigify_rig, proxy_rig, proxy_mesh)

            wgt_collection = rigutils.get_widget_rig_collection(chr_cache)
            wgt_root = bones.make_root_widget(f"WGT-{chr_cache.character_name}_rig_arkit_proxy_root", 3.25)
            if wgt_collection:
                utils.remove_from_scene_collections(wgt_root)
                bones.add_widget_to_collection(wgt_root, wgt_collection)
            proxy_root_bone: bpy.types.PoseBone = proxy_rig.pose.bones["root"]
            proxy_root_bone.custom_shape = wgt_root
            bones.set_bone_color(proxy_rig, proxy_root_bone, "ROOT")

            return proxy_rig

    return None


def add_arkit_driver_func(chr_cache, expression, length, shape_key_name, prop_defs: list):
    # dont adjust for these arkit blend shapes
    shape_key_name = shape_key_name.lower()
    exclude = ["eyelook", "eyewide", "eyeblink", "mouthclose", "jaw", "eyeroll", "eyepitch", "eyeyaw"]
    for pattern in exclude:
        if pattern in shape_key_name:
            return expression

    # ensure arkit function is in driver namespace
    if ("rl_arkit" not in bpy.app.driver_namespace or
        bpy.app.driver_namespace["rl_arkit"] != func_rl_arkit_proxy_mod):
        bpy.app.driver_namespace["rl_arkit"] = func_rl_arkit_proxy_mod

    # determine directional bias
    if "left" in shape_key_name:
        horz_bias = "1+H"
        horz_var = "horizontal_bias"
    elif "right" in shape_key_name:
        horz_bias = "1-H"
        horz_var = "horizontal_bias"
    else:
        horz_bias = "1"
        horz_var = None
    if "up" in shape_key_name or "upper" in shape_key_name:
        vert_bias = "1-V"
        vert_var = "vertical_bias"
    elif "down" in shape_key_name or "lower" in shape_key_name:
        vert_bias = "1+V"
        vert_var = "vertical_bias"
    else:
        vert_bias = "1"
        vert_var = None

    # extent expression with arkit adjustments
    proxy_rig, proxy_mesh = get_arkit_proxy(chr_cache)
    if proxy_rig:
        expression = f"rl_arkit({expression},{fvar(length)},S,{horz_bias},{vert_bias},R)"
        if ("S", proxy_rig, "strength") not in prop_defs:
            prop_defs.append(("S", proxy_rig, "strength"))
        if ("R", proxy_rig, "relaxation") not in prop_defs:
            prop_defs.append(("R", proxy_rig, "relaxation"))
        if horz_var and ("H", proxy_rig, horz_var) not in prop_defs:
            prop_defs.append(("H", proxy_rig, horz_var))
        if vert_var and ("V", proxy_rig, vert_var) not in prop_defs:
            prop_defs.append(("V", proxy_rig, vert_var))
    return expression


def func_rl_arkit_proxy_mod(value, length, strength, horz_bias, vert_bias, relaxation):
    length = abs(length)
    if relaxation != 1.0:
        vN = value / length
        if vN < 0:
            vN = -pow(min(1,max(0,-vN)), relaxation)
        else:
            vN = pow(min(1,max(0,vN)), relaxation)
        value = vN * length
    # multiply the value by the adjustments
    value = (value * strength * horz_bias * vert_bias / 100.0)
    return max(-1, min(1, value))


def build_arkit_proxy_drivers(chr_cache, rigify_rig, proxy_rig, proxy_mesh):
    if chr_cache and rigify_rig and proxy_rig and proxy_mesh:
        build_facerig_retarget_drivers(chr_cache, rigify_rig, proxy_rig, [ proxy_mesh ], shape_key_only=True, arkit=True)
        drivers.add_custom_float_property(proxy_rig, "strength", 100.0, 0.0, 200.0, subtype="PERCENTAGE", precision=1,
                                            description="Overall strength of expressions")
        drivers.add_custom_float_property(proxy_rig, "relaxation", 1.0, 0.25, 2.0,
                                            description="How much to relax or exaggerate the expressions")
        drivers.add_custom_float_property(proxy_rig, "horizontal_bias", 0.0, -0.75, 0.75,
                                            description="How much to relax or exaggerate the expressions")
        drivers.add_custom_float_property(proxy_rig, "vertical_bias", 0.0, -0.75, 0.75,
                                            description="How much to relax or exaggerate the expressions")
        drivers.add_custom_float_property(proxy_rig, "random_variance", 0.0, 0.0, 80.0, subtype="PERCENTAGE", precision=1,
                                            description="How much to relax or exaggerate the expressions")
        drivers.add_custom_int_property(proxy_rig, "random_seed", 1000, 0, 99999999,
                                            description="Random seed for variance")
        drivers.add_custom_float_property(proxy_rig, "filter", 0.0, 0.0, 80.0, subtype="PERCENTAGE", precision=1,
                                            description="Low pass filter to reduce noise in expression data")
        drivers.add_custom_string_property(proxy_rig, "csv_file", "",
                                            description="path to the csv file to import")
        drivers.add_custom_string_property(proxy_rig, "bake_motion_id", "ARKit_Bake",
                                            description="Motion Name for baked action")
        drivers.add_custom_string_property(proxy_rig, "bake_motion_prefix", "",
                                            description="Motion prefix for baked action")
        drivers.add_custom_float_property(proxy_rig, "head_blend", 100.0, 0.0, 100.0, subtype="PERCENTAGE", precision=1,
                                            description="How much of the head movement to blend into the rig")
        drivers.add_custom_float_property(proxy_rig, "head_yaw_offset", 0.0, -60.0*math.pi/180, 60.0*math.pi/180, subtype="ANGLE",
                                            description="Head rotation Yaw adjust")
        drivers.add_custom_float_property(proxy_rig, "head_pitch_offset", 0.0, -60.0*math.pi/180, 60.0*math.pi/180, subtype="ANGLE",
                                            description="Head rotation Pitch adjust")
        drivers.add_custom_float_property(proxy_rig, "head_roll_offset", 0.0, -60.0*math.pi/180, 60.0*math.pi/180, subtype="ANGLE",
                                            description="Head rotation Roll adjust")
        build_arkit_bone_constraints(chr_cache, rigify_rig, proxy_rig)


def get_arkit_proxy(chr_cache):
    if chr_cache and chr_cache.rigified and utils.object_exists_is_armature(chr_cache.arkit_proxy):
        proxy_rig = chr_cache.arkit_proxy
        for child in proxy_rig.children:
            if utils.prop(child, "arkit_proxy") == "fDsOJtp42n68X0e4ETVP":
                proxy_mesh = child
                return proxy_rig, proxy_mesh
    return None, None


def remove_arkit_proxy(chr_cache):
    if chr_cache and chr_cache.rigified and chr_cache.arkit_proxy:
        rigify_rig = chr_cache.get_armature()
        if rigify_rig:
            remove_facerig_retarget_drivers(chr_cache, rigify_rig)
            remove_arkit_bone_constraints(chr_cache, rigify_rig)
        if utils.object_exists_is_armature(chr_cache.arkit_proxy):
            utils.delete_object_tree(chr_cache.arkit_proxy)
        chr_cache.arkit_proxy = None


def arkit_find_target_blend_shape(facial_profile, blend_shape_name):
    if facial_profile in facerig_data.ARKIT_SHAPE_KEY_TARGETS:
        TARGETS = facerig_data.ARKIT_SHAPE_KEY_TARGETS[facial_profile]
        for arkit_blend_shape_name, targets in TARGETS.items():
            if type(targets) is list:
                if blend_shape_name in targets:
                    return arkit_blend_shape_name
            else:
                if targets == blend_shape_name:
                    return arkit_blend_shape_name
    return None


def decode_timecode(timecode: str, fps):
    split = timecode.split(":")
    h = int(split[0])
    m = int(split[1])
    s = int(split[2])
    f = float(split[3])
    return (int(h * 3600 + m * fps + s), int(f * 10000 / fps))


def timecode_to_frame(timecode: tuple, fps: int):
    s = timecode[0]
    f = timecode[1] * fps / 10000
    return (s * fps) + f


def load_csv(chr_cache, file_path):
    proxy_rig, proxy_mesh = get_arkit_proxy(chr_cache)
    if proxy_rig and proxy_mesh:
        tcurves = parse_arkit_csv(file_path)
        process_tcurves(proxy_rig, tcurves)
        if tcurves:
            facial_profile, viseme_profile = chr_cache.get_facial_profile()
            if facial_profile in facerig_data.ARKIT_SHAPE_KEY_TARGETS:
                keys = facerig_data.ARKIT_SHAPE_KEY_TARGETS[facial_profile].keys()
                key_action = utils.make_action(f"{chr_cache.character_name}_ARKit_Proxy_Head", slot_type="KEY", clear=True, reuse=True)
                arm_action = utils.make_action(f"{chr_cache.character_name}_ARKit_Proxy", slot_type="OBJECT", clear=True, reuse=True)
                key_channels = utils.get_action_channels(key_action, slot_type="KEY")
                for key in keys:
                    fcurve = key_channels.fcurves.new(f"key_blocks[\"{key}\"].value")
                    for tcurve in tcurves:
                        if tcurve.name.lower() == key.lower():
                            tcurve.to_fcurve(fcurve)
                            break
                utils.safe_set_action(proxy_mesh.data.shape_keys, key_action)
            bone_channels = utils.get_action_channels(arm_action, slot_type="OBJECT")
            for tcurve_name, bone_def in facerig_data.ARK_BONE_TARGETS.items():
                for tcurve in tcurves:
                    if tcurve.name.lower() == tcurve_name.lower():
                        bone_name = bone_def["bone"]
                        bone = proxy_rig.pose.bones[bone_name]
                        bone.rotation_mode = "XYZ"
                        axis = bone_def["axis"]
                        rotation = bone_def["rotation"] * math.pi / 180
                        prop, var, index = facerig_data.ROT_AXES[axis]
                        data_path = bone.path_from_id(prop)
                        fcurve = bone_channels.fcurves.new(data_path, index=index)
                        tcurve.to_fcurve(fcurve, rotation)
            utils.safe_set_action(proxy_rig, arm_action)


def get_arkit_proxy_prop(proxy_rig, prop):
    return proxy_rig[prop]


def parse_arkit_csv(file_path):
    csv = []
    maxf = 0
    with open(file_path, "r") as file:
        file.seek(0)
        for line in file:
            cols = line.split(",")
            if not csv:
                for i, col in enumerate(cols):
                    name = col.strip()
                    data = []
                    column = {
                        "index": i,
                        "data": data,
                        "name": name,
                        "tcurve": None,
                    }
                    csv.append(column)
            else:
                for i, col in enumerate(cols):
                    column = csv[i]
                    data = column["data"]
                    cell = col.strip()
                    if i == 0:
                        value = cell
                        f = float(cell.split(":")[-1])
                        maxf = max(f, maxf)
                    elif i == 1:
                        value = int(cell)
                    else:
                        value = float(cell)
                    data.append(value)

    csvfps = 60 if maxf >= 59 else 30
    time_data = csv[0]["data"]
    tc_start = (0, 1)
    tc_end = (0, 1)
    for i, timestr in enumerate(time_data):
        tc = decode_timecode(time_data[i], csvfps)
        time_data[i] = tc
        if i == 0:
            tc_start = tc
    tc_end = tc

    tcurves = []
    fps = bpy.context.scene.render.fps
    fps_base = bpy.context.scene.render.fps_base
    for i, column in enumerate(csv):
        if i > 1:
            tcurve = TCurve(csv, i, fps)
            tcurves.append(tcurve)
            #tcurve.dump()

    frame_start = timecode_to_frame(tc_start, fps)
    frame_end = timecode_to_frame(tc_end, fps)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = int(frame_end - frame_start) + 1

    return tcurves

def process_tcurves(proxy_rig, tcurves):

    variance = get_arkit_proxy_prop(proxy_rig, "random_variance") / 100
    seed = get_arkit_proxy_prop(proxy_rig, "random_seed")
    filter = get_arkit_proxy_prop(proxy_rig, "filter") / 100

    random.seed(seed)
    tcurve: TCurve

    for tcurve in tcurves:
        tcurve.process(filter, variance)


class TCurve():
    name = ""
    points = None
    length = 0
    frames = 0

    def __init__(self, csv: list, column_index: int, fps: int):
        self.points = []
        start_frame = 0
        self.name = csv[column_index]["name"]
        for i, timecode in enumerate(csv[0]["data"]):
            if i == 0:
                start_frame = timecode_to_frame(timecode, fps)
            frame = timecode_to_frame(timecode, fps) - start_frame + 1
            self.points.append((frame, csv[column_index]["data"][i]))
        self.frames = frame
        self.length = len(self.points)

    def eval(self, frame, start=0):
        for i in range(start, self.length):
            f, v = self.points[i]
            if frame <= f or frame >= self.frames:
                return v, i
            else:
                fn, vn = self.points[i + 1]
                if frame > f and frame < fn:
                    res = v + (vn - v) * (frame - f) / (fn - f)
                    return res, i
                    #return utils.remap(f, fn, v, vn, frame)
        return 0.0, i

    def to_fcurve(self, fcurve: bpy.types.FCurve, mod=1.0):
        num_frames = int(self.frames)
        fcurve_data = [0] * (num_frames * 2)
        j = 0
        for i in range(0, num_frames):
            fcurve_data[i * 2] = i + 1
            v, j = self.eval(i + 0.5, j)
            v *= mod
            fcurve_data[i * 2 + 1] = v
        fcurve.keyframe_points.clear()
        fcurve.keyframe_points.add(num_frames)
        fcurve.keyframe_points.foreach_set('co', fcurve_data)

    def dump(self):
        print(self.name)
        print(self.length)
        for i, (f, v) in enumerate(self.points):
            print(i, f, v)
            if i > 10:
                return

    def process(self, filter, variance):
        exclude = ["EyeLook", "Blink", "MouthClose", "Jaw", "EyeRoll", "EyePitch", "EyeYaw"]
        modify = True
        for e in exclude:
            if e in self.name:
                modify = False
        variance_mod = 1.0
        if variance:
            variance_mod += random.random() * variance_mod * variance
        for i, (f, v) in enumerate(self.points):
            if i > 0:
                v = v0 * filter + v * (1 - filter)
                # TODO maybe scale the filter by the difference in f-f0 as the time stamps are uneven
            f0 = f
            v0 = v
            if modify:
                v = max(-1, min(1, (v * variance_mod)))
            self.points[i] = (f, v)


class CCICImportARKitCSV(bpy.types.Operator):
    """Import ARKit LiveLink CSV"""
    bl_idname = "ccic.import_arkit_csv"
    bl_label = "Import ARKit LiveLink CSV"
    bl_options = {"REGISTER", "UNDO", 'PRESET'}

    filepath: bpy.props.StringProperty(
        name="Filepath",
        description="Filepath of the csv to import.",
        subtype="FILE_PATH"
    )

    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    files: bpy.props.CollectionProperty(
            type=bpy.types.OperatorFileListElement,
            options={'HIDDEN', 'SKIP_SAVE'}
    )

    filter_glob: bpy.props.StringProperty(
        default="*.csv",
        options={"HIDDEN"}
    )

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
    )

    def execute(self, context):
        props = vars.props()
        prefs = vars.prefs()

        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)
        proxy_rig, proxy_mesh = get_arkit_proxy(chr_cache)

        if proxy_rig:

            if self.param == "RELOAD" and proxy_rig["csv_file"]:
                load_csv(chr_cache, proxy_rig["csv_file"])

            elif self.files:
                list_file = self.files[0]
                dir = self.directory
                file = list_file.name
                proxy_rig["csv_file"] = os.path.join(dir, file)

            elif self.filepath:
                proxy_rig["csv_file"] = self.filepath

            else:
                proxy_rig["csv_file"] = ""

            if proxy_rig["csv_file"]:
                load_csv(chr_cache, proxy_rig["csv_file"])

        return {"FINISHED"}

    def invoke(self, context, event):
        if self.param == "RELOAD":
            return self.execute(context)
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    @classmethod
    def description(cls, context, properties):
        return ""