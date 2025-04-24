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
import math
import copy
from . import utils, vars
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
                    print(f"MISSING BONE {bone_name}")
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


def generate_facerig_config(chr_cache, rigify_rig):

    objects = chr_cache.get_cache_objects()

    FACERIG_CONFIG = copy.deepcopy(FACERIG_EXT_CC3PLUS)

    for control_name, control_def in FACERIG_CONFIG:

        if control_def["widget_type"] == "slider":

            blendshapes = control_def["blendshapes"]
            control_bones = control_def["bones"]

            num_keys = len(blendshapes)
            del_keys = []
            for i, (shape_key_name, shape_key_value) in enumerate(blendshapes.items()):
                if not objects_have_shape_key(objects, shape_key_name):
                    if num_keys == 2:
                        control_def["range"][i] = 0.0
                        del_keys.append(shape_key_name)
                        num_keys -= 1
                    elif num_keys == 1:
                        control_def["range"][1] = 0.0
                        del_keys.append(shape_key_name)
                        num_keys -= 1
            if num_keys == 0:
                del(control_def["blendshapes"])
            for shape_key_name in del_keys:
                del(control_def["blendshapes"][shape_key_name])


def build_expression_rig(chr_cache, rigify_rig, meta_rig, cc3_rig):
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

        for control_name, control_def in FACERIG_EXT_CC3PLUS.items():

            if not is_valid_control_def(control_def, rigify_rig, objects):
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
                if control_def.get("y_invert"):
                    pN0 = Vector((p_min.x + width * zero_x, p_min.y + height * (1 - zero_y), 0))
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
                bones.set_bone_collection(rigify_rig, pose_bone, "Face (Expressions)", None, None)
                bones.set_bone_color(rigify_rig, pose_bone, bone_colors[i])
                pose_bone.custom_shape = bone_shapes[i]
                pose_bone.custom_shape_scale_xyz = bone_scale
                pose_bone.bone.hide_select = not bone_selectable[i]
                pose_bone.use_custom_shape_bone_size = False
                bones.keep_locks(pose_bone, no_bake=True)

        # TODO: lock the scale and rotation of the nub bones
        #       dont unlock face rig automaticcally (retarget/bake doing it?)

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
            bones.set_bone_collection(rigify_rig, line_bone, "Face (Expressions)", None, None)
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
            bones.set_bone_collection(rigify_rig, box_bone, "Face (Expressions)", None, None)
            bones.set_bone_color(rigify_rig, box_bone, "FACERIG_DARK", "FACERIG_DARK", "FACERIG_DARK", chr_cache=chr_cache)
            bones.set_bone_collection(rigify_rig, nub_bone, "Face (Expressions)", None, None)
            bones.set_bone_color(rigify_rig, nub_bone, "FACERIG", "FACERIG", "FACERIG", chr_cache=chr_cache)
            control_range_x = control_def["x_range"]
            control_range_y = control_def["y_range"]
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

    for control_name, control_def in FACERIG_EXT_CC3PLUS.items():

        if control_name not in rigify_rig.pose.bones:
            continue

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

        if "blendshapes" in control_def:

            num_keys = len(control_def["blendshapes"])
            for i, (shape_key_name, shape_key_value) in enumerate(control_def["blendshapes"].items()):
                distance = min_y if shape_key_value == control_range_y[0] else max_y
                var_axis = LOC_AXES.get("y")[1]
                if shape_key_name not in shape_key_driver_defs:
                    shape_key_driver_defs[shape_key_name] = {}
                key_control_def = {
                    "value": abs(shape_key_value),
                    "distance": distance,
                    "var_axis": var_axis,
                }
                shape_key_driver_defs[shape_key_name][nub_bone_name] = key_control_def

        rigify_bones = control_def.get("rigify")

        if rigify_bones:
            for i, bone_def in enumerate(rigify_bones):
                bone_name = bone_def["bone"]
                if bone_name in rigify_rig.pose.bones:
                    # slider controls translate by default
                    if bone_def.get("mode", "position") == "position":
                        prop, axis, index = LOC_AXES.get(bone_def["axis"], (None, None, None))
                    else:
                        prop, axis, index = ROT_AXES.get(bone_def["axis"], (None, None, None))
                    if axis:
                        driver_id = (bone_name, prop, index)
                        var_axis = LOC_AXES.get("y")[1]
                        bone_control_def = {
                            "bone": bone_def["bone"],
                            "offset": bone_def["offset"] / 100, # convert from
                            "scalar": bone_def["scalar"] / 100, # cm to m
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

        ctrl_axes = [
            ("horizontal", "x", min_x, max_x, control_range_x),
            ("vertical", "y", min_y, max_y, control_range_y)
        ]

        if "blendshapes" in control_def:

            for ctrl_dir, ctrl_axis, min_d, max_d, control_range in ctrl_axes:

                num_keys = len(control_def["blendshapes"][ctrl_axis])
                for i, (shape_key_name, shape_key_value) in enumerate(control_def["blendshapes"][ctrl_axis].items()):
                    distance = min_d if utils.same_sign(shape_key_value, control_range[0]) else max_d
                    var_axis = LOC_AXES.get(ctrl_axis)[1]
                    if shape_key_name not in shape_key_driver_defs:
                        shape_key_driver_defs[shape_key_name] = {}
                    key_control_def = {
                        "value": abs(shape_key_value),
                        "distance": distance,
                        "var_axis": var_axis,
                    }
                    shape_key_driver_defs[shape_key_name][nub_bone_name] = key_control_def

        rigify_bones = control_def.get("rigify")

        if rigify_bones:

            for ctrl_dir, ctrl_axis, min_d, max_d, control_range in ctrl_axes:
                for bone_def in rigify_bones[ctrl_dir]:
                    bone_name = bone_def["bone"]
                    if bone_name in rigify_rig.pose.bones:
                        # rect controls rotate by default
                        if bone_def.get("mode", "rotation") == "position":
                            prop, axis, index = LOC_AXES.get(bone_def["axis"], (None, None, None))
                        else:
                            prop, axis, index = ROT_AXES.get(bone_def["axis"], (None, None, None))
                        if axis:
                            driver_id = (bone_name, prop, index)
                            var_axis = LOC_AXES.get(ctrl_axis)[1]
                            bone_control_def = {
                                "bone": bone_def["bone"],
                                "offset": bone_def["offset"] * math.pi/180, # convert angles
                                "scalar": bone_def["scalar"] * math.pi/180, # to radians
                                "distance": [min_d, max_d],
                                "var_axis": var_axis
                            }
                            if driver_id not in bone_driver_defs:
                                bone_driver_defs[driver_id] = {}
                            bone_driver_defs[driver_id][nub_bone_name] = bone_control_def

    return shape_key_driver_defs, bone_driver_defs


def build_expression_rig_drivers(chr_cache, rigify_rig):

    # first drive the shape keys on any other body objects from the head body object
    # expression rig will then override these
    drivers.add_body_shape_key_drivers(chr_cache, True)

    BONE_CLEAR_CONSTRAINTS = [
            "MCH-eye.L", "MCH-eye.R"
        ]

    # initialize target bone rotation modes and clear unwanted constraints
    for control_name, control_def in FACERIG_EXT_CC3PLUS.items():

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
        bones.add_constraint_scripted_influence_driver(rigify_rig, "MCH-facerig", data_path, "rf", child_con, expression="(1.0 if rf else 0.0)")
        bones.add_constraint_scripted_influence_driver(rigify_rig, "MCH-facerig", data_path, "rf", loc_con)
        bones.add_constraint_scripted_influence_driver(rigify_rig, "MCH-facerig", data_path, "rf", rot_con1)
        bones.add_constraint_scripted_influence_driver(rigify_rig, "MCH-facerig", data_path, "rf", rot_con2, expression="(rf - 1)")

        shape_key_driver_defs, bone_driver_defs = collect_driver_defs(chr_cache, rigify_rig,
                                                                      slider_controls, rect_controls)

        # build shape key drivers from shape key driver defs
        for shape_key_name, shape_key_driver_def in shape_key_driver_defs.items():
            expression = ""
            var_defs = []
            vidx = 0
            for nub_bone_name, key_control_def in shape_key_driver_def.items():
                if nub_bone_name in rigify_rig.pose.bones:
                    var_axis = key_control_def["var_axis"]
                    distance = key_control_def["distance"]
                    value = key_control_def["value"]
                    var_name = f"var{vidx}"
                    vidx += 1
                    if expression:
                        expression += "+"
                    expression += f"max({value:0.6f}*{var_name}/{distance:0.6f},0)"
                    var_def = [var_name,
                               "TRANSFORMS",
                               nub_bone_name,
                               var_axis,
                               "LOCAL_SPACE"]
                    var_defs.append(var_def)
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
                if offset != 0.0:
                    expression += f"({offset:0.6f}+{scalar:0.6f}*({var_name}/{distance[1]:0.6f}))"
                else:
                    expression += f"({scalar:0.6f}*({var_name}/{distance[1]:0.6f}))"
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


def build_expression_rig_retarget_drivers(chr_cache, rigify_rig, source_rig, source_objects):

    bone_drivers = {}
    bone_retarget_defs = {}

    if rigutils.select_rig(rigify_rig):

        for control_name, control_def in FACERIG_EXT_CC3PLUS.items():

            if control_def["widget_type"] == "rect":
                prefixes = [ ("x_", "x", "horizontal", "_box",  0, "rotation"),
                             ("y_", "y", "vertical",   "_box",  1, "rotation") ]
            else:
                prefixes = [ ("",   "",  "",           "_line", 1, "position") ]

            for prefix, key_group, bone_group, line_suffix, index, default_mode in prefixes:
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

                if rl_bones and len(rl_bones) > 0:

                    bone_drivers[driver_id] = { "method": method,
                                                "parent": parent,
                                                "length": slider_length,
                                                "bones": [] }

                    for bone_def in rl_bones:
                        source_name = bone_def["bone"]
                        if source_name in source_rig.pose.bones:
                            if bone_def.get("mode", default_mode) == "position":
                                prop, prop_axis, prop_index = LOC_AXES.get(bone_def["axis"], (None, None, None))
                                offset = bone_def["offset"]
                                scalar = bone_def["scalar"]
                            else:
                                prop, prop_axis, prop_index = ROT_AXES.get(bone_def["axis"], (None, None, None))
                                offset = bone_def["offset"] * math.pi / 180
                                scalar = bone_def["scalar"] * math.pi / 180
                            bone_drivers[driver_id]["bones"].append({ "bone": source_name,
                                                                        "scale": slider_length/(control_range[1] * scalar),
                                                                        "offset": offset,
                                                                        "axis": prop_axis })
                else:

                    left_shape = right_shape = None
                    for i, (blend_shape_name, blend_shape_value) in enumerate(blend_shapes.items()):
                        # if 'retarget' list exists in control def, only retarget blendshapes
                        # in the list, to avoid uncontrolled duplicate retargets
                        if "retarget" in control_def:
                            if blend_shape_name not in control_def["retarget"]:
                                continue
                        if utils.same_sign(blend_shape_value, control_range[0]):
                            left_shape = (blend_shape_name, abs(blend_shape_value), slider_length/control_range[0])
                        elif utils.same_sign(blend_shape_value, control_range[1]):
                            right_shape = (blend_shape_name, abs(blend_shape_value), slider_length/control_range[1])

                    bone_drivers[driver_id] = { "method": method,
                                                "parent": parent,
                                                "length": slider_length,
                                                "shape_keys": [] }
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
                                                             no_driver=True, length_override=driver_def["length"])
                build_retarget_driver(chr_cache, rigify_rig, driver_id, driver_def,
                                      source_rig, source_objects,
                                      pre_expression=expression, pre_var_defs=var_defs)
            else:
                build_retarget_driver(chr_cache, rigify_rig, driver_id, driver_def, source_rig, source_objects)


def build_retarget_driver(chr_cache, rigify_rig, driver_id, driver_def, source_rig, source_objects,
                                     no_driver=False, pre_expression=None,
                                     pre_var_defs=None, length_override=None):
    bone_name, prop, index = driver_id
    method = driver_def["method"]
    parent = driver_def["parent"]
    length = driver_def["length"]
    pose_bone = bones.get_pose_bone(rigify_rig, bone_name)

    expression = ""
    var_defs = []

    vidx = 0 if not pre_var_defs else len(pre_var_defs)

    if "shape_keys" in driver_def:

        count = 0
        shape_key_defs = driver_def["shape_keys"]
        for key_def in shape_key_defs:
            scale = key_def["scale"]
            value = key_def["value"]
            if length_override:
                scale *= length_override / length
            shape_key_name = key_def["shape_key"]
            obj = get_key_object(source_objects, shape_key_name)
            if obj:
                var_name = f"var{vidx}"
                if count > 0:
                    expression += "+"
                expression += f"({var_name}*{scale:0.6f}/{value:0.6f})"
                var_defs.append((var_name, shape_key_name))
                vidx += 1
                count += 1

        if expression:
            expression = f"({expression})"

        if expression and method == "AVERAGE" and count > 1:
            expression = f"({expression}/{count})"

        if expression and parent != "NONE" and pre_expression and pre_var_defs:
            expression = f"{expression} - min(max({pre_expression},-1),1)"
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

    if "bones" in driver_def:

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
                expression += f"(({var_name}+{offset:0.6f})*{scale:0.6f})"
                var_defs.append((var_name, source_name, axis))
                vidx += 1
                count += 1

        if expression:
            expression = f"min(1,max(-1,{expression}))"

        if expression and method == "AVERAGE" and count > 1:
            expression = f"({expression}/{count})"

        if expression and parent != "NONE" and pre_expression and pre_var_defs:
            expression = f"{expression} - {pre_expression}"
            var_defs.extend(pre_var_defs)

        if expression and not no_driver:
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


def remove_expression_rig_retarget_drivers(chr_cache, rigify_rig: bpy.types.Object):
    if rigutils.select_rig(rigify_rig):
        for control_name, control_def in FACERIG_EXT_CC3PLUS.items():
            if control_name in rigify_rig.pose.bones:
                pose_bone = rigify_rig.pose.bones[control_name]
                pose_bone.driver_remove("location", 0)
                pose_bone.driver_remove("location", 1)


def clear_expression_pose(chr_cache, rigify_rig, selected=False):
    if selected:
        selected_names = []
        if bpy.context.selected_bones:
            selected_names = [ b.name for b in bpy.context.selected_bones ]
        elif bpy.context.selected_pose_bones:
            selected_names = [ b.name for b in bpy.context.selected_pose_bones ]
        control_bones = []
        for control_bone_name in FACERIG_EXT_CC3PLUS:
            if control_bone_name in rigify_rig.pose.bones and control_bone_name in selected_names:
                control_bones.append(control_bone_name)
    else:
        control_bones = [ "MCH-jaw_move", "jaw_master", "MCH-jaw_master" ]
        for control_bone_name in FACERIG_EXT_CC3PLUS:
            if control_bone_name in rigify_rig.pose.bones:
                control_bones.append(control_bone_name)

    state = bones.store_armature_settings(rigify_rig, include_selection=True)
    vis = bones.store_bone_locks_visibility(rigify_rig)
    bones.clear_pose(rigify_rig, control_bones)
    bones.restore_bone_locks_visibility(rigify_rig, vis)
    bones.restore_armature_settings(rigify_rig, state, include_selection=True)


def update_face_rig_color(context):
    props = vars.props()
    chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)
    if chr_cache:
        rig = chr_cache.get_armature()
        if rig and "facerig" in rig.pose.bones:
            for control_bone_name, control_def in FACERIG_EXT_CC3PLUS.items():
                bones.set_bone_color(rig, control_bone_name, "FACERIG", "FACERIG", "FACERIG", chr_cache=chr_cache)
                if control_def["widget_type"] == "rect":
                    lines_bone_name = control_bone_name + "_box"
                else:
                    lines_bone_name = control_bone_name + "_line"
                bones.set_bone_color(rig, lines_bone_name, "FACERIG_DARK", "FACERIG_DARK", "FACERIG_DARK", chr_cache=chr_cache)


def is_position_locked(rig):
    if "facerig" in rig.pose.bones:
        return rig.pose.bones["facerig"].bone.hide_select


def toggle_lock_position(chr_cache, rig):
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
    for control_name in FACERIG_EXT_CC3PLUS:
        if control_name in rig.pose.bones:
            pose_bone = rig.pose.bones[control_name]
            pose_bone.bone.hide_select = False
        if control_name+"_line" in rig.pose.bones:
            pose_bone = rig.pose.bones[control_name+"_line"]
            pose_bone.bone.hide_select = True
        if control_name+"_box" in rig.pose.bones:
            pose_bone = rig.pose.bones[control_name+"_box"]
            pose_bone.bone.hide_select = True


LOC_AXES = {
        "x": ("location", "LOC_X", 0),
        "y": ("location", "LOC_Y", 1),
        "z": ("location", "LOC_Z", 2),
    }

ROT_AXES = {
    "x": ("rotation_euler", "ROT_X", 0),
    "y": ("rotation_euler", "ROT_Y", 1),
    "z": ("rotation_euler", "ROT_Z", 2),
}

FACERIG_EXT_CC3PLUS = {
    "CTRL_L_eye_blink":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [107, 110],
        "blendshapes":
        {
            "Eye_Blink_L": 1.0,
            "Eye_Wide_L": -1.0
        }
    },
    "CTRL_R_eye_blink":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [10, 13],
        "blendshapes":
        {
            "Eye_Blink_R": 1.0,
            "Eye_Wide_R": -1.0
        }
    },
    "CTRL_eye_pupil":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [168, 169],
        "blendshapes":
        {
            "Eye_Pupil_Dilate": 1.0,
            "Eye_Pupil_Contract": -1.0
        }
    },
    # theres only one set of pupil shape keys for both eyes
    #"CTRL_L_eye_pupil":
    #{
    #    "widget_type": "slider",
    #    "range": [-1.0, 1.0],
    #    "indices": [170, 171],
    #    "blendshapes":
    #    {
    #        "Eye_Pupil_Dilate": 1.0,
    #        "Eye_Pupil_Contract": -1.0
    #    }
    #},
    "CTRL_L_eye_squintInner":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [115, 116],
        "blendshapes": {"Eye_Squint_L": 1.0}
    },
    "CTRL_R_eye_squintInner":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [18, 19],
        "blendshapes": {"Eye_Squint_R": 1.0}
    },
    "CTRL_L_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_parent": "CTRL_C_eye",
        "y_parent": "CTRL_C_eye",
        "indices": [188, 189, 190, 191],
        "blendshapes":
        {
            "x":
            {
                "Eye_L_Look_L": 1.0,
                "Eye_L_Look_R": -1.0
            },
            "y":
            {
                "Eye_L_Look_Up": -1.0,
                "Eye_L_Look_Down": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "scalar": 20.0
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "scalar": 20.0
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.L",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "scalar": 20.0
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.L",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "scalar": -20.0
                }
            ]
        }

    },
    "CTRL_R_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_parent": "CTRL_C_eye",
        "y_parent": "CTRL_C_eye",
        "indices": [175, 174, 173, 172],
        "blendshapes":
        {
            "x":
            {
                "Eye_R_Look_L": 1.0,
                "Eye_R_Look_R": -1.0
            },
            "y":
            {
                "Eye_R_Look_Up": -1.0,
                "Eye_R_Look_Down": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "scalar": 20.0
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "scalar": 20.0
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "scalar": 20.0
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "scalar": -20.0
                }
            ]
        }
    },
    "CTRL_C_eye":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "x_method": "AVERAGE",
        "y_method": "AVERAGE",
        "indices": [176, 177, 178, 179],  #+172
        "blendshapes":
        {
            "x":
            {
                "Eye_R_Look_L": 1.0,
                "Eye_R_Look_R": -1.0,
                "Eye_L_Look_L": 1.0,
                "Eye_L_Look_R": -1.0
            },
            "y":
            {
                "Eye_R_Look_Up": -1.0,
                "Eye_R_Look_Down": 1.0,
                "Eye_L_Look_Up": -1.0,
                "Eye_L_Look_Down": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "scalar": 20.0
                },
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "z",
                    "offset": 0, # -90.0,
                    "scalar": 20.0
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_R_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "scalar": 20.0
                },
                {
                    "bone": "CC_Base_L_Eye",
                    "axis": "x",
                    "offset": 0, # -90.0,
                    "scalar": 20.0
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "scalar": 20.0
                },
                {
                    "bone": "MCH-eye.L",
                    "axis": "z",
                    "cc_axis": "z",
                    "offset": 0,
                    "scalar": 20.0
                }
            ],
            "vertical":
            [
                {
                    "bone": "MCH-eye.R",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "scalar": -20.0
                },
                {
                    "bone": "MCH-eye.L",
                    "axis": "x",
                    "cc_axis": "x",
                    "offset": 0,
                    "scalar": -20.0
                }
            ]
        }
    },
    "CTRL_C_mouth":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [184, 187, 186, 185],
        "blendshapes":
        {
            "x":
            {
                "Mouth_L": 1.0,
                "Mouth_R": -1.0
            },
            "y":
            {
                "Mouth_Up": -1.0,
                "Mouth_Down": 1.0
            }
        }
    },
    "CTRL_C_jaw":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [0.0, 1.0],
        "y_invert": True,
        "indices": [202, 203, 204, 205],
        "blendshapes":
        {
            "x":
            {
                "Jaw_L": 1.0,
                "Jaw_R": -1.0
            },
            "y":
            {
                "Jaw_Open": 1.0
            }
        },
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_JawRoot",
                    "axis": "y",
                    "offset": 0,
                    "scalar": -15.0
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_JawRoot",
                    "axis": "z",
                    "offset": 0, # 90.0,
                    "scalar": 30.0
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "jaw_master",
                    "axis": "y",
                    "cc_axis": "y",
                    "offset": 0,
                    "scalar": 15.0
                }
            ],
            "vertical":
            [
                {
                    "bone": "jaw_master",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0.0,
                    "scalar": 30.0
                }
            ]
        }
    },
    "CTRL_R_brow_lateral":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [2, 7],
        "blendshapes":
        {
            "Brow_Compress_R": 1.0
        }
    },
    "CTRL_L_brow_lateral":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [99, 104],
        "blendshapes":
        {
            "Brow_Compress_L": 1.0
        }
    },
    "CTRL_R_brow_down":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [4, 8],
        "blendshapes":
        {
            "Brow_Drop_R": 1.0
        }
    },
    "CTRL_L_brow_down":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [101, 105],
        "blendshapes":
        {
            "Brow_Drop_L": 1.0
        }
    },
    "CTRL_L_brow_raiseOut":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [97, 102],
        "blendshapes":
        {
            "Brow_Raise_Outer_L": 1.0
        }
    },
    "CTRL_L_brow_raiseIn":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [98, 103],
        "blendshapes":
        {
            "Brow_Raise_Inner_L": 1.0
        }
    },
    "CTRL_R_brow_raiseOut":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [0, 5],
        "blendshapes":
        {
            "Brow_Raise_Outer_R": 1.0
        }
    },
    "CTRL_R_brow_raiseIn":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [1, 6],
        "blendshapes":
        {
            "Brow_Raise_Inner_R": 1.0
        }
    },
    "CTRL_R_ear_up":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [15, 16],
        "blendshapes":
        {
            "Ear_Up_R": 1.0
        }
    },
    "CTRL_L_ear_up":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [112, 113],
        "blendshapes":
        {
            "Ear_Up_L": 1.0
        }
    },
    "CTRL_L_nose_wrinkleUpper":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [106, 133],
        "blendshapes":
        {
            "Nose_Sneer_L": 1.0
        }
    },
    "CTRL_R_nose_wrinkleUpper":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [9, 94],
        "blendshapes":
        {
            "Nose_Sneer_R": 1.0
        }
    },
    "CTRL_L_eye_cheekRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [111, 114],
        "blendshapes":
        {
            "Cheek_Raise_L": 1.0
        }
    },
    "CTRL_R_eye_cheekRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [14, 17],
        "blendshapes":
        {
            "Cheek_Raise_R": 1.0
        }
    },
    "CTRL_R_nose": {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [180, 181, 182, 183],
        "blendshapes":
        {
            "x":
            {
                "Nose_Nostril_Dilate_R": -1.0,
                "Nose_Nostril_In_R": 1.0
            },
            "y":
            {
                "Nose_Nostril_Raise_R": -1.0,
                "Nose_Nostril_Down_R": 1.0
            }
        }
    },
    "CTRL_L_nose":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [181, 192, 193, 182],
        "blendshapes":
        {
            "x":
            {
                "Nose_Nostril_Dilate_L": 1.0,
                "Nose_Nostril_In_L": -1.0
            },
            "y":
            {
                "Nose_Nostril_Raise_L": -1.0,
                "Nose_Nostril_Down_L": 1.0
            }
        }
    },
    "CTRL_L_mouth_lowerLipDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [126, 132],
        "blendshapes":
        {
            "Mouth_Down_Lower_L": 1.0
        }
    },
    "CTRL_R_mouth_lowerLipDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [27, 33],
        "blendshapes":
        {
            "Mouth_Down_Lower_R": 1.0
        }
    },
    "CTRL_L_mouth_cornerDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [124, 130],
        "blendshapes":
        {
            "Mouth_Frown_L": 1.0
        }
    },
    "CTRL_R_mouth_cornerDepress":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [25, 31],
        "blendshapes":
        {
            "Mouth_Frown_R": 1.0
        }
    },
    "CTRL_L_mouth_cornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [122, 128],
        "blendshapes":
        {
            "Mouth_Smile_L": 1.0
        }
    },
    "CTRL_R_mouth_cornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [23, 29],
        "blendshapes":
        {
            "Mouth_Smile_R": 1.0
        }
    },
    "CTRL_L_mouth_upperLipRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [120, 119],
        "blendshapes":
        {
            "Mouth_Up_Upper_L": 1.0
        }
    },
    "CTRL_R_mouth_upperLipRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [21, 20],
        "blendshapes":
        {
            "Mouth_Up_Upper_R": 1.0
        }
    },
    "CTRL_L_mouth_sharpCornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [121, 127],
        "blendshapes":
        {
            "Mouth_Smile_Sharp_L": 1.0
        }
    },
    "CTRL_R_mouth_sharpCornerPull":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [22, 28],
        "blendshapes":
        {
            "Mouth_Smile_Sharp_R": 1.0
        }
    },
    "CTRL_L_mouth_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [125, 131],
        "blendshapes":
        {
            "Mouth_Stretch_L": 1.0
        }
    },
    "CTRL_R_mouth_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [26, 32],
        "blendshapes":
        {
            "Mouth_Stretch_R": 1.0
        }
    },
    "CTRL_L_mouth_dimple":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [123, 129],
        "blendshapes":
        {
            "Mouth_Dimple_L": 1.0
        }
    },
    "CTRL_R_mouth_dimple":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [24, 30],
        "blendshapes":
        {
            "Mouth_Dimple_R": 1.0
        }
    },
    "CTRL_R_mouth_towardsU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [61, 65],
        "blendshapes":
        {
            "Mouth_Push_Upper_R": 1.0
        }
    },
    "CTRL_R_mouth_towardsD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [59, 63],
        "blendshapes":
        {
            "Mouth_Push_Lower_R": 1.0
        }
    },
    "CTRL_L_mouth_towardsU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [60, 64],
        "blendshapes":
        {
            "Mouth_Push_Upper_L": 1.0
        }
    },
    "CTRL_L_mouth_towardsD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [58, 62],
        "blendshapes":
        {
            "Mouth_Push_Lower_L": 1.0
        }
    },
    "CTRL_R_mouth_purseU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [54, 69],
        "blendshapes":
        {
            "Mouth_Pucker_Up_R": 1.0
        }
    },
    "CTRL_R_mouth_purseD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [56, 67],
        "blendshapes":
        {
            "Mouth_Pucker_Down_R": 1.0
        }
    },
    "CTRL_L_mouth_purseU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [55, 68],
        "blendshapes":
        {
            "Mouth_Pucker_Up_L": 1.0
        }
    },
    "CTRL_L_mouth_purseD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [57, 66],
        "blendshapes":
        {
            "Mouth_Pucker_Down_L": 1.0
        }
    },
    "CTRL_R_mouth_funnelU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [70, 77],
        "blendshapes":
        {
            "Mouth_Funnel_Up_R": 1.0
        }
    },
    "CTRL_R_mouth_funnelD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [72, 75],
        "blendshapes":
        {
            "Mouth_Funnel_Down_R": 1.0
        }
    },
    "CTRL_L_mouth_funnelU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [71, 76],
        "blendshapes":
        {
            "Mouth_Funnel_Up_L": 1.0
        }
    },
    "CTRL_L_mouth_funnelD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [73, 74],
        "blendshapes":
        {
            "Mouth_Funnel_Down_L": 1.0
        }
    },
    "CTRL_R_mouth_lipBiteU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [78, 90],
        "blendshapes":
        {
            "Mouth_Roll_In_Upper_R": 1.0
        }
    },
    "CTRL_R_mouth_lipBiteD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [80, 92],
        "blendshapes":
        {
            "Mouth_Roll_In_Lower_R": 1.0
        }
    },
    "CTRL_L_mouth_lipBiteU":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [79, 91],
        "blendshapes":
        {
            "Mouth_Roll_In_Upper_L": 1.0
        }
    },
    "CTRL_L_mouth_lipBiteD":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [81, 93],
        "blendshapes":
        {
            "Mouth_Roll_In_Lower_L": 1.0
        }
    },
    "CTRL_R_mouth_tighten":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [82, 86],
        "blendshapes":
        {
            "Mouth_Tighten_R": 1.0
        }
    },
    "CTRL_L_mouth_tighten":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [83, 87],
        "blendshapes":
        {
            "Mouth_Tighten_L": 1.0
        }
    },
    "CTRL_C_jaw_chinRaise":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [95, 96],
        "blendshapes":
        {
            "Mouth_Chin_Up": 1.0
        }
    },
    "CTRL_C_jaw_fwdBack":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [144, 145],
        "blendshapes":
        {
            "Jaw_Forward": 1.0,
            "Jaw_Backward": -1.0
        },
        "bones":
        [
            {
                "bone": "CC_Base_JawRoot",
                "axis": "x",
                "offset": 0, # 1.8288450241088867,
                "scalar": 1.0
            }
        ],
        "rigify":
        [
            {
                "bone": "MCH-jaw_move",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "scalar": 1.0
            }
        ]
    },
    "CTRL_L_mouth_suckBlow":
    {
        "widget_type": "slider",
        "retarget": ["Cheek_Suck_L"],
        "range": [-1.0, 1.0],
        "indices": [44, 42],
        "blendshapes":
        {
            "Cheek_Suck_L": 1.0,
            "Mouth_Blow_L": -1.0
        }
    },
    "CTRL_R_mouth_suckBlow": {
        "widget_type": "slider",
        "retarget": ["Cheek_Suck_R"],
        "range": [-1.0, 1.0],
        "indices": [43, 45],
        "blendshapes":
        {
            "Cheek_Suck_R": 1.0,
            "Mouth_Blow_R": -1.0
        }
    },
    "CTRL_L_neck_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [149, 147],
        "blendshapes":
        {
            "Neck_Tighten_L": 1.0
        }
    },
    "CTRL_R_neck_stretch":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [148, 146],
        "blendshapes":
        {
            "Neck_Tighten_R": 1.0
        }
    },
    "CTRL_C_mouth_lipsTogether":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [152, 153],
        "blendshapes":
        {
            "Mouth_Close": 0.2
        }
    },
    "CTRL_R_mouth_press":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [84, 88],
        "blendshapes":
        {
            "Mouth_Press_R": 1.0
        }
    },
    "CTRL_L_mouth_press":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [85, 89],
        "blendshapes":
        {
            "Mouth_Press_L": 1.0
        }
    },
    "CTRL_C_tongue":  #270, 380
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [214, 215, 216, 217],
        "blendshapes":
        {
            "x":
            {
                "Tongue_L": 1.0,
                "Tongue_R": -1.0
            },
            "y":
            {
                "Tongue_Up": -1.0,
                "Tongue_Down": 1.0
            }
        }
    },
    "CTRL_C_tongue_inOut":  #250, 380
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [165, 164],
        "blendshapes":
        {
            "Tongue_In": 1.0,
            "Tongue_Out": -1.0
        }
    },
    "CTRL_C_tongue_tip":  #330, 380
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [218, 219, 220, 221],
        "blendshapes":
        {
            "x":
            {
                "Tongue_Tip_L": 1.0,
                "Tongue_Tip_R": -1.0
            },
            "y":
            {
                "Tongue_Tip_Up": -1.0,
                "Tongue_Tip_Down": 1.0
            }
        }
    },
    "CTRL_C_tongue_roll":  #370, 380
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [219, 222, 223, 220],
        "blendshapes":
        {
            "x":
            {
                "Tongue_Twist_L": 1.0,
                "Tongue_Twist_R": -1.0
            },
            "y":
            {
                "V_Tongue_Curl_U": -1.0,
                "V_Tongue_Curl_D": 1.0
            }
        }
    },
    "CTRL_C_tongue_press":  #310, 380
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [167, 166],
        "blendshapes":
        {
            "Tongue_Mid_Up": 1.0
        }
    },
    "CTRL_L_mouth_lipsBlow":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [156, 157],
        "blendshapes":
        {
            "Mouth_Blow_L": 1.0
        }
    },
    "CTRL_R_mouth_lipsBlow":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [154, 155],
        "blendshapes":
        {
            "Mouth_Blow_R": 1.0
        }
    },
    "CTRL_C_tongue_narrowWide":  #300, 360
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [162, 163],
        "blendshapes":
        {
            "Tongue_Wide": 1.0,
            "Tongue_Narrow": -1.0
        }
    },
    "CTRL_R_nose_nasolabialDeepen":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [11, 12],
        "blendshapes":
        {
            "Nose_Crease_R": 1.0
        }
    },
    "CTRL_L_nose_nasolabialDeepen":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [108, 109],
        "blendshapes":
        {
            "Nose_Crease_L": 1.0
        }
    },
    "CTRL_R_mouth_lipsRollU":
    {
        "widget_type": "slider",
        "retarget": ["Mouth_Roll_Out_Upper_R"],
        "range": [-1.0, 1.0],
        "indices": [34, 36],
        "blendshapes":
        {
            "Mouth_Roll_In_Upper_R": 1.0,
            "Mouth_Roll_Out_Upper_R": -1.0
        }
    },
    "CTRL_R_mouth_lipsRollD":
    {
        "widget_type": "slider",
        "retarget": ["Mouth_Roll_Out_Lower_R"],
        "range": [-1.0, 1.0],
        "indices": [38, 40],
        "blendshapes":
        {
            "Mouth_Roll_In_Lower_R": -1.0,
            "Mouth_Roll_Out_Lower_R": 1.0
        }
    },
    "CTRL_L_mouth_lipsRollU":
    {
        "widget_type": "slider",
        "retarget": ["Mouth_Roll_Out_Upper_L"],
        "range": [-1.0, 1.0],
        "indices": [35, 37],
        "blendshapes":
        {
            "Mouth_Roll_In_Upper_L": 1.0,
            "Mouth_Roll_Out_Upper_L": -1.0
        }
    },
    "CTRL_L_mouth_lipsRollD":
    {
        "widget_type": "slider",
        "retarget": ["Mouth_Roll_Out_Lower_L"],
        "range": [-1.0, 1.0],
        "indices": [39, 41],
        "blendshapes":
        {
            "Mouth_Roll_In_Lower_L": -1.0,
            "Mouth_Roll_Out_Lower_L": 1.0
        }
    },
    "CTRL_R_mouth_corner":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "retarget": [],
        "indices": [206, 207, 208, 209],
        "blendshapes":
        {
            "x":
            {
                "Mouth_Tighten_R": 1.0,
                "Mouth_Stretch_R": -1.0
            },
            "y":
            {
                "Mouth_Smile_Sharp_R": -1.0,
                "Mouth_Frown_R": 1.0
            }
        }
    },
    "CTRL_L_mouth_corner":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "retarget": [],
        "indices": [210, 211, 212, 213],
        "blendshapes":
        {
            "x":
            {
                "Mouth_Tighten_L": -1.0,
                "Mouth_Stretch_L": 1.0
            },
            "y":
            {
                "Mouth_Smile_Sharp_L": -1.0,
                "Mouth_Frown_L": 1.0
            }
        }
    },
    "CTRL_C_mouth_lipShiftU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [158, 159],
        "blendshapes":
        {
            "Mouth_Upper_L": 1.0,
            "Mouth_Upper_R": -1.0
        }
    },
    "CTRL_C_mouth_lipShiftD":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [160, 161],
        "blendshapes":
        {
            "Mouth_Lower_L": 1.0,
            "Mouth_Lower_R": -1.0
        }
    },
    "CTRL_R_mouth_pushPullU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [50, 46],
        "blendshapes":
        {
            "Mouth_Push_Upper_R": -1.0,
            "Mouth_Pull_Upper_R": 1.0
        }
    },
    "CTRL_R_mouth_pushPullD":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [52, 48],
        "blendshapes":
        {
            "Mouth_Push_Lower_R": -1.0,
            "Mouth_Pull_Lower_R": 1.0
        }
    },
    "CTRL_L_mouth_pushPullU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [47, 51],
        "blendshapes":
        {
            "Mouth_Push_Upper_L": 1.0,
            "Mouth_Pull_Upper_L": -1.0
        }
    },
    "CTRL_L_mouth_pushPullD":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [49, 53],
        "blendshapes":
        {
            "Mouth_Push_Lower_L": 1.0,
            "Mouth_Pull_Lower_L": -1.0
        }
    },
    "CTRL_C_teethD":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [198, 199, 200, 201],
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_Teeth02",
                    "axis": "z",
                    "offset": 0, # -0.04119798541069031,
                    "scalar": 1.0,
                    "mode": "position"
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_Teeth02",
                    "axis": "y",
                    "offset": 0, # 1.249316930770874,
                    "scalar": 1.0,
                    "mode": "position"
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "teeth.B",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0,
                    "scalar": 1.0,
                    "mode": "position"
                }
            ],
            "vertical":
            [
                {
                    "bone": "teeth.B",
                    "axis": "z",
                    "cc_axis": "y",
                    "offset": 0,
                    "scalar": -1.0,
                    "mode": "position"
                }
            ]
        }
    },
    "CTRL_C_teethU":
    {
        "widget_type": "rect",
        "x_range": [-1.0, 1.0],
        "y_range": [-1.0, 1.0],
        "y_invert": False,
        "indices": [194, 195, 196, 197],
        "bones":
        {
            "horizontal":
            [
                {
                    "bone": "CC_Base_Teeth01",
                    "axis": "z",
                    "offset": 0, # -0.03492468595504761,
                    "scalar": 1.0,
                    "mode": "position"
                }
            ],
            "vertical":
            [
                {
                    "bone": "CC_Base_Teeth01",
                    "axis": "y",
                    "offset": 0, # -0.06047694757580757,
                    "scalar": 1.0,
                    "mode": "position"
                }
            ]
        },
        "rigify":
        {
            "horizontal":
            [
                {
                    "bone": "teeth.T",
                    "axis": "x",
                    "cc_axis": "z",
                    "offset": 0,
                    "scalar": 1.0,
                    "mode": "position"
                }
            ],
            "vertical":
            [
                {
                    "bone": "teeth.T",
                    "axis": "z",
                    "cc_axis": "y",
                    "offset": 0,
                    "scalar": -1.0,
                    "mode": "position"
                }
            ]
        }
    },
    "CTRL_C_teeth_fwdBackD":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [117, 134],
        "bones":
        [
            {
                "bone": "CC_Base_Teeth02",
                "axis": "x",
                "offset": 0, # 2.879988670349121,
                "scalar": 1.0
            }
        ],
        "rigify":
        [
            {
                "bone": "teeth.B",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "scalar": -1.0
            }
        ]
    },
    "CTRL_C_teeth_fwdBackU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [118, 135],
        "bones":
        [
            {
                "bone": "CC_Base_Teeth01",
                "axis": "x",
                "offset": 0, # -0.16094255447387695,
                "scalar": 1.0
            }
        ],
        "rigify":
        [
            {
                "bone": "teeth.T",
                "axis": "y",
                "cc_axis": "x",
                "offset": 0,
                "scalar": -1.0
            }
        ]
    },
    "CTRL_R_eyelashU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [136, 138],
        "blendshapes":
        {
            "Eyelash_Upper_Up_R": -1.0,
            "Eyelash_Upper_Down_R": 1.0
        }
    },
    "CTRL_R_eyelashD":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [140, 142],
        "blendshapes":
        {
            "Eyelash_Lower_Up_R": -1.0,
            "Eyelash_Lower_Down_R": 1.0
        }
    },
    "CTRL_L_eyelashU":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [137, 139],
        "blendshapes":
        {
            "Eyelash_Upper_Up_L": -1.0,
            "Eyelash_Upper_Down_L": 1.0
        }
    },
    "CTRL_L_eyelashD":
    {
        "widget_type": "slider",
        "range": [-1.0, 1.0],
        "indices": [141, 143],
        "blendshapes":
        {
            "Eyelash_Lower_Up_L": -1.0,
            "Eyelash_Lower_Down_L": 1.0
        }
    },
    "CTRL_C_mouth_thickness":
    {
        "widget_type": "slider",
        "range": [0.0, 1.0],
        "indices": [150, 151],
        "blendshapes":
        {
            "Mouth_Contract": 0.4
        }
    }
}
