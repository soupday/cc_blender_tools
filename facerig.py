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


def get_objects_shape_key_name(objects, shape_key_name, try_substitutes=False):
    """Some older characters an profiles have inconsisent expression names, resolve them here"""
    if shape_key_name.startswith("Teeth_") or shape_key_name.startswith("Dummy_"):
        return shape_key_name
    for obj in objects:
        if obj.type == "MESH":
            if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
                if shape_key_name in obj.data.shape_keys.key_blocks:
                    return shape_key_name
    if try_substitutes:
        if shape_key_name.endswith("_L"):
            shape_key_name = shape_key_name[:-2] + "_Left"
        elif shape_key_name.endswith("_R"):
            shape_key_name = shape_key_name[:-2] + "_Right"
        else:
            return None
        for obj in objects:
            if obj.type == "MESH":
                if obj.data.shape_keys and obj.data.shape_keys.key_blocks:
                    if shape_key_name in obj.data.shape_keys.key_blocks:
                        return shape_key_name
    return None


def is_valid_control_def(control_name, control_def, rigify_rig, objects):
    bone_collection = rigify_rig.data.edit_bones if utils.get_mode() == "EDIT" else rigify_rig.pose.bones
    count = 0
    total = 0
    #if "CTRL_C_head" not in control_name:
    #    return 0, 0
    if control_def["widget_type"] == "slider" or control_def["widget_type"] == "curve_slider":
        if "blendshapes" in control_def:
            blendshapes = control_def["blendshapes"]
            for shape_key_name in blendshapes:
                total += 1
                real_shape_key_name = get_objects_shape_key_name(objects, shape_key_name)
                if real_shape_key_name:
                    count += 1
        if "rigify" in control_def:
            control_bones = control_def["rigify"]
            for bone_def in control_bones:
                total += 1
                bone_name = bone_def["bone"]
                if bone_name in bone_collection:
                    count += 1
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
                total += 1
                real_shape_key_name = get_objects_shape_key_name(objects, shape_key_name)
                if real_shape_key_name:
                    count += 1
            for shape_key_name in blendshapes_y:
                total += 1
                real_shape_key_name = get_objects_shape_key_name(objects, shape_key_name)
                if real_shape_key_name:
                    count += 1
        if "rigify" in control_def:
            control_bones_x = control_def["rigify"]["horizontal"]
            control_bones_y = control_def["rigify"]["horizontal"]
            for bone_def in control_bones_x:
                total += 1
                bone_name = bone_def["bone"]
                if bone_name in bone_collection:
                    count += 1
            for bone_def in control_bones_y:
                total += 1
                bone_name = bone_def["bone"]
                if bone_name in bone_collection:
                    count += 1
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
    return count, total


def get_facerig_config(chr_cache):
    facial_profile, viseme_profile = chr_cache.get_facial_profile()
    if facial_profile == "EXT":
        return facerig_data.FACERIG_EXT_CONFIG
    elif facial_profile == "STD":
        return facerig_data.FACERIG_STD_CONFIG
    elif facial_profile == "TRA":
        return facerig_data.FACERIG_TRA_CONFIG
    elif facial_profile == "MH":
        return facerig_data.FACERIG_MH_CONFIG
    return None


def build_facerig(chr_cache, rigify_rig, meta_rig, cc3_rig):
    prefs = vars.prefs()

    if not chr_cache.can_expression_rig():
        return

    chr_cache.rigify_face_control_color = prefs.rigify_face_control_color
    facial_profile, viseme_profile = chr_cache.get_facial_profile()

    objects = chr_cache.get_cache_objects()
    wgt_collection = f"WGTS_{cc3_rig.name}_rig"
    WGT_OUTLINE, WGT_GROUPS, WGT_LABELS, WGT_LINES, WGT_SLIDER, WGT_RECT, WGT_NUB, WGT_NAME = \
                                                rigutils.get_expression_widgets(chr_cache, wgt_collection)
    WGT_OUTLINE2, WGT_GROUPS2, WGT_LABELS2, WGT_LINES2 = \
                                                rigutils.get_expression_widgets_2(chr_cache, wgt_collection)
    bone_scale = Vector((0.125, 0.125, 0.125))
    R = Matrix.Rotation(90*math.pi/180, 3, 'X')
    slider_controls = {}
    rect_controls = {}

    utils.log_info(f"Building Expression Rig for facial profile: {facial_profile}")

    if rigutils.edit_rig(rigify_rig):
        # place the face rig parent at eye level
        eye_l = bones.get_edit_bone(rigify_rig, "ORG-eye.L")
        eye_r = bones.get_edit_bone(rigify_rig, "ORG-eye.R")
        head = bones.get_edit_bone(rigify_rig, "head")
        eye_pos = (eye_l.head + eye_r.head) * 0.5
        head_pos = head.head.copy()
        z_pos = eye_pos.z
        head_pos.z = z_pos
        mch_parent = bones.copy_edit_bone(rigify_rig, "head", "MCH-facerig_parent", "neck", 1.0)
        mch_parent.head = head_pos
        mch_parent.tail = head_pos + Vector((0,0,0.1))
        mch_parent.align_roll(Vector((0,-1,0)))
        bones.copy_edit_bone(rigify_rig, "MCH-facerig_parent", "MCH-facerig", "", 0.5)
        # place the face rig control ~20cm in front of face
        facerig_bone = bones.copy_edit_bone(rigify_rig, "MCH-facerig", "facerig", "MCH-facerig", 1.0)
        facerig_bone.head += Vector((0, -0.2, 0))
        facerig_bone.tail += Vector((0, -0.2, 0))
        bones.copy_edit_bone(rigify_rig, "facerig", "facerig_name", "facerig", 0.8)
        bones.copy_edit_bone(rigify_rig, "facerig", "facerig_groups", "facerig", 0.6)
        bones.copy_edit_bone(rigify_rig, "facerig", "facerig_labels", "facerig", 0.4)
        bones.copy_edit_bone(rigify_rig, "facerig", "MCH-facerig_controls", "facerig", 0.2)
        if facial_profile == "MH":
            facerig2_bone = bones.copy_edit_bone(rigify_rig, "MCH-facerig", "facerig2", "facerig", 1.0)
            facerig2_bone.head += Vector((0.2, -0.2, 0))
            facerig2_bone.tail += Vector((0.2, -0.2, 0))
            bones.copy_edit_bone(rigify_rig, "facerig2", "facerig2_groups", "facerig2", 0.6)
            bones.copy_edit_bone(rigify_rig, "facerig2", "facerig2_labels", "facerig2", 0.4)
            bones.copy_edit_bone(rigify_rig, "facerig2", "MCH-facerig2_controls", "facerig2", 0.2)
        # add MCH bone for head controls
        # MCH-ROT-head needs offset loc/rot constraints
        head_ctrl = bones.copy_edit_bone(rigify_rig, "head", "MCH-CTRL-head", "MCH-ROT-head", 0.4)
        head_ctrl.align_roll(Vector((0,-1,0)))
        head.parent = head_ctrl
        # add MCH bone for eye tracking controls
        left_eye_ctrl = bones.copy_edit_bone(rigify_rig, "MCH-eye.L", "MCH-CTRL-eye.L", "master_eye.L", 0.5)
        left_eye_mch = bones.get_edit_bone(rigify_rig, "MCH-eye.L")
        left_eye_ctrl.align_roll(Vector((0,0,1)))
        left_eye_mch.parent = left_eye_ctrl
        right_eye_ctrl = bones.copy_edit_bone(rigify_rig, "MCH-eye.R", "MCH-CTRL-eye.R", "master_eye.R", 0.5)
        right_eye_mch = bones.get_edit_bone(rigify_rig, "MCH-eye.R")
        right_eye_ctrl.align_roll(Vector((0,0,1)))
        right_eye_mch.parent = right_eye_ctrl
        # add MCH bone for jaw controls
        jaw_ctrl = bones.copy_edit_bone(rigify_rig, "jaw_master", "MCH-CTRL-jaw", "ORG-face", 0.5)
        jaw_master = bones.get_edit_bone(rigify_rig, "jaw_master")
        jaw_ctrl.align_roll(Vector((0,0,-1)))
        jaw_master.parent = jaw_ctrl

        FACERIG_CONFIG = get_facerig_config(chr_cache)

        for control_name, control_def in FACERIG_CONFIG.items():

            count, total = is_valid_control_def(control_name, control_def, rigify_rig, objects)

            if count == 0:
                utils.log_warn(f"Invalid expression control: {control_name}")
                continue
            elif count != total:
                utils.log_warn(f"Missing shape keys or bones for control: {control_name}")

            if control_def["widget_type"] == "slider" or control_def["widget_type"] == "curve_slider":

                outline = control_def.get("outline", 1)
                if facial_profile == "MH" and outline == 2:
                    LINES = WGT_LINES2
                    mch_facerig_name = "MCH-facerig2_controls"
                    facerig_parent = facerig2_bone
                else:
                    LINES = WGT_LINES
                    mch_facerig_name = "MCH-facerig_controls"
                    facerig_parent = facerig_bone

                invert = control_def["range"][1] < control_def["range"][0]
                zero = utils.inverse_lerp(control_def["range"][0], control_def["range"][1], 0.0)
                indices = control_def["indices"]
                coords = [ LINES.data.vertices[i].co.copy() for i in indices ]
                #shrink_slider_coords(coords, 0.01)
                line_bone = bones.new_edit_bone(rigify_rig, control_name+"_line", mch_facerig_name)
                line_bone.head = (R @ coords[0] * bone_scale * 1.0) + facerig_parent.head
                line_bone.tail = (R @ utils.lerp(coords[0], coords[1], 0.5) * bone_scale * 1.0) + facerig_parent.head
                line_bone.align_roll(Vector((0, -1, 0)))
                length = 2 * (line_bone.head - line_bone.tail).length
                nub_bone = bones.new_edit_bone(rigify_rig, control_name, line_bone.name)
                zy = (1-zero) if invert else zero
                nub_bone.head = utils.lerp(line_bone.head, line_bone.tail, zy * 2, clamp=False)
                nub_bone.tail = (line_bone.tail - line_bone.head).normalized() * (length / 2) + nub_bone.head
                nub_bone.align_roll(Vector((0, -1, 0)))
                slider_controls[control_name] = (control_def, line_bone.name, nub_bone.name, length, zero)

            elif control_def["widget_type"] == "rect":

                outline = control_def.get("outline", 1)
                if facial_profile == "MH" and outline == 2:
                    LINES = WGT_LINES2
                    mch_facerig_name = "MCH-facerig2_controls"
                    facerig_parent = facerig2_bone
                else:
                    LINES = WGT_LINES
                    mch_facerig_name = "MCH-facerig_controls"
                    facerig_parent = facerig_bone

                x_invert = control_def["x_range"][1] < control_def["x_range"][0]
                y_invert = control_def["y_range"][1] < control_def["y_range"][0]
                zero_x = utils.inverse_lerp(control_def["x_range"][0], control_def["x_range"][1], 0.0)
                zero_y = utils.inverse_lerp(control_def["y_range"][0], control_def["y_range"][1], 0.0)
                indices = control_def["indices"]
                coords = [ LINES.data.vertices[i].co.copy() for i in indices ]
                p_min = Vector((min(coords[0].x, coords[1].x, coords[2].x, coords[3].x),
                                min(coords[0].y, coords[1].y, coords[2].y, coords[3].y), 0))
                p_max = Vector((max(coords[0].x, coords[1].x, coords[2].x, coords[3].x),
                                max(coords[0].y, coords[1].y, coords[2].y, coords[3].y), 0))
                width = (p_max.x - p_min.x)
                height = (p_max.y - p_min.y)
                pB0 = Vector((p_min.x + width / 2, p_min.y, 0.0))
                pB1 = Vector((p_min.x + width / 2, p_min.y + height / 2, 0.0))
                zx = (1-zero_x) if x_invert else zero_x
                zy = (1-zero_y) if y_invert else zero_y
                pN0 = Vector((p_min.x + width * zx, p_min.y + height * zy, 0))
                pN1 = Vector((pN0.x, pN0.y + height / 2, 0))
                pN2 = Vector((pN0.x, pN0.y - height / 2, 0))
                box_bone = bones.new_edit_bone(rigify_rig, control_name+"_box", mch_facerig_name)
                box_bone.head = (R @ pB0 * bone_scale * 1.0) + facerig_parent.head
                box_bone.tail = (R @ pB1 * bone_scale * 1.0) + facerig_parent.head
                box_bone.align_roll(Vector((0, -1, 0)))
                nub_bone = bones.new_edit_bone(rigify_rig, control_name, box_bone.name)
                if control_def.get("x_mirror", False):
                    nub_bone.head = (R @ pN0 * bone_scale * 1.0) + facerig_parent.head
                    nub_bone.tail = (R @ pN2 * bone_scale * 1.0) + facerig_parent.head
                else:
                    nub_bone.head = (R @ pN0 * bone_scale * 1.0) + facerig_parent.head
                    nub_bone.tail = (R @ pN1 * bone_scale * 1.0) + facerig_parent.head
                nub_bone.align_roll(Vector((0, -1, 0)))
                width *= bone_scale.x
                height *= bone_scale.y
                rect_controls[control_name] = (control_def, box_bone.name, nub_bone.name, width, height, zero_x, zero_y)

    if rigutils.select_rig(rigify_rig):

        bones.set_bone_collection(rigify_rig, "MCH-CTRL-head", "MCH", None, 30)
        bones.set_bone_collection(rigify_rig, "MCH-CTRL-jaw", "MCH", None, 30)
        face_rig = bones.get_pose_bone(rigify_rig, "facerig")
        drivers.add_custom_float_property(face_rig, "eyes_track", 0.0, 0.0, 1.0, description="Eye tracking influence from Rigify eye rig")
        #drivers.add_custom_float_property(face_rig, "eyes_track_enable", 1.0, 0.0, 1.0, description="Enable/disable eye tracking from Rigify eye rig")

        bones.add_bone_collection(rigify_rig, "Face (Expressions)", "Face", color_set="CUSTOM", custom_color=chr_cache.rigify_face_control_color, lerp=0)
        bones.add_bone_collection(rigify_rig, "Face (UI)", "UI", color_set="CUSTOM", custom_color=(1,1,1))
        bones.set_bone_collection_visibility(rigify_rig, "Face (Expressions)", 22, True)
        bones.set_bone_collection_visibility(rigify_rig, "Face (UI)", 23, True)

        bones.set_bone_collection(rigify_rig, "MCH-jaw_move", "MCH", None, 30)
        bones.set_bone_collection(rigify_rig, "MCH-facerig", "MCH", None, 30)
        bones.set_bone_collection(rigify_rig, "MCH-facerig_controls", "MCH", None, 30)
        bones.set_bone_collection(rigify_rig, "MCH-facerig_parent", "MCH", None, 30)
        if facial_profile == "MH":
            bones.set_bone_collection(rigify_rig, "MCH-facerig2", "MCH", None, 30)
            bones.set_bone_collection(rigify_rig, "MCH-facerig2_controls", "MCH", None, 30)
        bone_names = [ "facerig", "facerig_groups", "facerig_labels", "facerig_name",
                       "facerig2", "facerig2_groups", "facerig2_labels" ]
        bone_colors = [ "WHITE", "GROUP", "WHITE", "WHITE",
                        "WHITE", "GROUP", "WHITE" ]
        bone_groups = [ "UI", "UI", "UI", "UI",
                        "UI", "UI", "UI" ]
        bone_shapes = [ WGT_OUTLINE, WGT_GROUPS, WGT_LABELS, WGT_NAME,
                        WGT_OUTLINE2, WGT_GROUPS2, WGT_LABELS2 ]
        bone_selectable = [ True, False, False, False,
                            True, False, False ]
        for i, bone_name in enumerate(bone_names):
            pose_bone = bones.get_pose_bone(rigify_rig, bone_name)
            if pose_bone:
                bones.set_bone_collection(rigify_rig, pose_bone, "Face (UI)", bone_groups[i], 23)
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
            hue_shift = control_def.get("color_shift", 0.0)
            bones.keep_locks(nub_bone)
            bones.set_bone_collection(rigify_rig, line_bone, "Face (UI)", "Face", 22)
            bones.set_bone_color(rigify_rig, line_bone, "FACERIG_DARK", "FACERIG_DARK", "FACERIG_DARK", chr_cache=chr_cache, hue_shift=hue_shift)
            bones.set_bone_collection(rigify_rig, nub_bone, "Face (Expressions)", "Face", 22)
            bones.set_bone_color(rigify_rig, nub_bone, "FACERIG", "FACERIG", "FACERIG", chr_cache=chr_cache, hue_shift=hue_shift)
            control_range_y = control_def["range"]
            y_invert = control_range_y[1] < control_range_y[0]
            if y_invert:
                neg_y = -length * (1 - zero) * control_range_y[1]
                pos_y = -length * zero * control_range_y[0]
            else:
                neg_y = length * zero * control_range_y[0]
                pos_y = length * (1 - zero) * control_range_y[1]
            drivers.add_custom_float_property(line_bone, "slider_length", length)
            bones.add_limit_location_constraint(rigify_rig, nub_bone_name,
                                                0, neg_y, 0,
                                                0, pos_y, 0,
                                                space="LOCAL", use_transform_limit=True)

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
            nub_bone.lock_rotation_w = True
            nub_bone.lock_rotations_4d = True
            hue_shift = control_def.get("color_shift", 0.0)
            bones.keep_locks(nub_bone)
            bones.set_bone_collection(rigify_rig, box_bone, "Face (UI)", "Face", 22)
            bones.set_bone_color(rigify_rig, box_bone, "FACERIG_DARK", "FACERIG_DARK", "FACERIG_DARK", chr_cache=chr_cache, hue_shift=hue_shift)
            bones.set_bone_collection(rigify_rig, nub_bone, "Face (Expressions)", "Face", 22)
            bones.set_bone_color(rigify_rig, nub_bone, "FACERIG", "FACERIG", "FACERIG", chr_cache=chr_cache, hue_shift=hue_shift)
            control_range_x = control_def["x_range"]
            control_range_y = control_def["y_range"]
            x_invert = control_range_x[1] < control_range_x[0]
            y_invert = control_range_y[1] < control_range_y[0]
            if x_invert:
                neg_x = width * (1 - zero_x) * control_range_x[1]
                pos_x = width * zero_x * control_range_x[0]
            else:
                neg_x = width * zero_x * control_range_x[0]
                pos_x = width * (1 - zero_x) * control_range_x[1]
            if y_invert:
                neg_y = height * (1 - zero_y) * control_range_y[1]
                pos_y = height * zero_y * control_range_y[0]
            else:
                neg_y = height * zero_y * control_range_y[0]
                pos_y = height * (1 - zero_y) * control_range_y[1]
            if control_def.get("x_mirror"):
                nub_bone.scale.y = -1
                #m = min_y
                #min_y = max_y
                #max_y = m

            drivers.add_custom_float_property(box_bone, "x_slider_length", width)
            drivers.add_custom_float_property(box_bone, "y_slider_length", height)
            bones.add_limit_location_constraint(rigify_rig, nub_bone_name,
                                                neg_x, neg_y, 0,
                                                pos_x, pos_y, 0,
                                                space="LOCAL", use_transform_limit=True)


def get_generated_controls(chr_cache, rigify_rig):
    slider_controls = {}
    curve_slider_controls = {}
    rect_controls = {}

    FACERIG_CONFIG = get_facerig_config(chr_cache)

    for control_name, control_def in FACERIG_CONFIG.items():

        if control_def["widget_type"] == "slider":
            zero_point = utils.inverse_lerp(control_def["range"][0], control_def["range"][1], 0.0)
            line_bone_name = control_name + "_line"
            nub_bone_name = control_name
            if line_bone_name in rigify_rig.pose.bones:
                line_pose_bone = rigify_rig.pose.bones[line_bone_name]
                line_bone = line_pose_bone.bone
                length = line_pose_bone["slider_length"] if "slider_length" in line_pose_bone else line_bone.length * 2
                slider_controls[control_name] = (control_def, line_bone_name, nub_bone_name, length, zero_point)

        if control_def["widget_type"] == "curve_slider":
            zero_point = utils.inverse_lerp(control_def["range"][0], control_def["range"][1], 0.0)
            line_bone_name = control_name + "_line"
            nub_bone_name = control_name
            if line_bone_name in rigify_rig.pose.bones:
                line_pose_bone = rigify_rig.pose.bones[line_bone_name]
                line_bone = line_pose_bone.bone
                length = line_pose_bone["slider_length"] if "slider_length" in line_pose_bone else line_bone.length * 2
                curve_slider_controls[control_name] = (control_def, line_bone_name, nub_bone_name, length, zero_point)

        if control_def["widget_type"] == "rect":
            zero_x = utils.inverse_lerp(control_def["x_range"][0], control_def["x_range"][1], 0.0)
            zero_y = utils.inverse_lerp(control_def["y_range"][0], control_def["y_range"][1], 0.0)
            box_bone_name = control_name+"_box"
            nub_bone_name = control_name
            if box_bone_name in rigify_rig.pose.bones:
                box_pose_bone = rigify_rig.pose.bones[box_bone_name]
                box_bone = box_pose_bone.bone
                width = box_pose_bone["x_slider_length"] if "x_slider_length" in box_pose_bone else box_bone.length * 2
                height = box_pose_bone["y_slider_length"] if "y_slider_length" in box_pose_bone else box_bone.length * 2
                rect_controls[control_name] = (control_def, box_bone_name, nub_bone_name, width, height, zero_x, zero_y)

    return slider_controls, curve_slider_controls, rect_controls


def get_expression_bones_def(chr_cache, control_name, control_def):
    bones_def = None
    if chr_cache:
        if control_def["widget_type"] == "rect":
            bones_def = {}
            for ctrl_dir, ctrl_axis in [("horizontal", "x"), ("vertical", "y")]:
                bones_def[ctrl_dir] = []
                if "blendshapes" in control_def:
                    for shape_key_name, value in control_def["blendshapes"][ctrl_axis].items():
                        range_value = utils.sign(value)
                        for expression_cache in chr_cache.expression_set:
                            if expression_cache.key_name == shape_key_name:
                                bones_def[ctrl_dir].append({
                                    "shape_key": shape_key_name,
                                    "bone": expression_cache.rigify_bone_name,
                                    "value": range_value,
                                    "Translate": utils.prop_to_list(expression_cache.rigify_translation),
                                    "Rotation": utils.prop_to_list(expression_cache.rigify_rotation),
                                    "Source Bone": expression_cache.bone_name,
                                    "Source Translate": utils.prop_to_list(expression_cache.translation),
                                    "Source Rotation": utils.prop_to_list(expression_cache.rotation),
                                    "Offset Bone": expression_cache.offset_bone_name,
                                    "Offset Translate": utils.prop_to_list(expression_cache.offset_translation),
                                    "Offset Rotation": utils.prop_to_list(expression_cache.offset_rotation),
                                })
        else:
            bones_def = []
            if "blendshapes" in control_def:
                for shape_key_name, value in control_def["blendshapes"].items():
                    range_value = utils.sign(value)
                    for expression_cache in chr_cache.expression_set:
                        if expression_cache.key_name == shape_key_name:
                            bones_def.append({
                                "shape_key": shape_key_name,
                                "bone": expression_cache.rigify_bone_name,
                                "value": range_value,
                                "Translate": utils.prop_to_list(expression_cache.rigify_translation),
                                "Rotation": utils.prop_to_list(expression_cache.rigify_rotation),
                                "Source Bone": expression_cache.bone_name,
                                "Source Translate": utils.prop_to_list(expression_cache.translation),
                                "Source Rotation": utils.prop_to_list(expression_cache.rotation),
                                "Offset Bone": expression_cache.offset_bone_name,
                                "Offset Translate": utils.prop_to_list(expression_cache.offset_translation),
                                "Offset Rotation": utils.prop_to_list(expression_cache.offset_rotation),
                            })
    return bones_def


def collect_driver_defs(chr_cache, rigify_rig,
                        slider_controls, curve_slider_controls, rect_controls):

    shape_key_driver_defs = {}
    bone_driver_defs = {}
    offset_driver_defs = {}
    use_offset_rig = True

    # collect slider control data into shapekey and bone driver defs
    for slider_name, slider_def in slider_controls.items():

        control_def, line_bone_name, nub_bone_name, length, zero_point = slider_def
        control_range_y = control_def["range"]
        y_invert = control_range_y[1] < control_range_y[0]
        if y_invert:
            neg_y = length * (1 - zero_point) * control_range_y[1]
            pos_y = length * zero_point * control_range_y[0]
        else:
            neg_y = length * zero_point * control_range_y[0]
            pos_y = length * (1 - zero_point) * control_range_y[1]

        influence = control_def.get("influence", None)

        if "blendshapes" in control_def:

            num_keys = len(control_def["blendshapes"])
            use_negative = (control_def.get("negative", False) or
                            ((num_keys == 1) and (abs(control_range_y[1] - control_range_y[0]) == 2)))
            for i, (shape_key_name, shape_key_value) in enumerate(control_def["blendshapes"].items()):
                var_axis = facerig_data.LOC_AXES.get("y")[1]
                if shape_key_name not in shape_key_driver_defs:
                    shape_key_driver_defs[shape_key_name] = {}
                key_control_def = {
                    "value": abs(shape_key_value),
                    "distance": neg_y if shape_key_value < 0 else pos_y,
                    "var_axis": var_axis,
                    "num_keys": num_keys,
                    "invert": y_invert,
                    "use_strength": control_def.get("strength", True),
                    "use_negative": use_negative,
                    "influence": influence,
                }
                shape_key_driver_defs[shape_key_name][nub_bone_name] = key_control_def

        #rigify_bones = control_def.get("rigify")

        bones_def = get_expression_bones_def(chr_cache, slider_name, control_def)
        if bones_def:
            for i, bone_def in enumerate(bones_def):
                bone_name = bone_def["bone"]
                value = bone_def.get("value", 1)
                if bone_name in rigify_rig.pose.bones:

                    if "Translate" in bone_def:
                        for i, def_axis in enumerate(["x", "y", "z"]):
                            prop, axis, index = facerig_data.LOC_AXES.get(def_axis, (None, None, None))
                            scalar = bone_def["Translate"][i]
                            if abs(scalar) > 0.0001:
                                driver_id = (bone_name, prop, index)
                                var_axis = facerig_data.LOC_AXES.get("y")[1]
                                bone_control_def = {
                                    "bone": bone_def["bone"],
                                    "offset": 0,
                                    "scalar": scalar,
                                    "range": value,
                                    "distance": neg_y if value < 0 else pos_y,
                                    "var_axis": var_axis,
                                    "use_strength": control_def.get("strength", True),
                                    "use_negative": use_negative,
                                    "influence": influence,
                                }
                                if driver_id not in bone_driver_defs:
                                    bone_driver_defs[driver_id] = {}
                                bone_driver_defs[driver_id][(nub_bone_name, value, var_axis)] = bone_control_def

                    if "Rotation" in bone_def:
                        for i, def_axis in enumerate(["x", "y", "z"]):
                            prop, axis, index = facerig_data.ROT_AXES.get(def_axis, (None, None, None))
                            scalar = bone_def["Rotation"][i]
                            if abs(scalar) > 0.001:
                                driver_id = (bone_name, prop, index)
                                var_axis = facerig_data.LOC_AXES.get("y")[1]
                                bone_control_def = {
                                    "bone": bone_def["bone"],
                                    "offset": 0,
                                    "scalar": scalar,
                                    "range": value,
                                    "distance": neg_y if value < 0 else pos_y,
                                    "var_axis": var_axis,
                                    "use_strength": control_def.get("strength", True),
                                    "use_negative": use_negative,
                                    "influence": influence,
                                }
                                if driver_id not in bone_driver_defs:
                                    bone_driver_defs[driver_id] = {}
                                bone_driver_defs[driver_id][(nub_bone_name, value, var_axis)] = bone_control_def

                    if use_offset_rig and bone_def["Offset Bone"] and control_def.get("offset", False):
                        offset_bone = bone_def["Offset Bone"]
                        shape_key_name = bone_def["shape_key"]
                        source_tra = utils.array_to_vector(bone_def["Offset Translate"]) if "Offset Translate" in bone_def else Vector((0,0,0))
                        source_euler = bone_def["Offset Rotation"] if "Offset Rotation" in bone_def else  [0,0,0]
                        axes = ["x", "y", "z"]
                        if abs(source_euler[0]) + abs(source_euler[1]) + abs(source_euler[2]) > 0.01:
                            index = utils.largest_index(source_euler, use_abs=True)
                            axis = axes[index]
                            prop, prop_axis, prop_index = facerig_data.ROT_AXES.get(axis, (None, None, None))
                            scalar = source_euler[index]
                        elif source_tra.length > 0.001:
                            index = utils.largest_index(source_tra, use_abs=True)
                            axis = axes[index]
                            prop, prop_axis, prop_index = facerig_data.LOC_AXES.get(axis, (None, None, None))
                            scalar = source_tra[index]
                        if source_tra.length > 0.001 or (abs(source_euler[0]) + abs(source_euler[1]) + abs(source_euler[2])) > 0.01:
                            if shape_key_name not in offset_driver_defs:
                                offset_driver_defs[shape_key_name] = {}
                            offset_driver_defs[shape_key_name][(nub_bone_name, value)] = { "dir": bone_def["value"],
                                                                                  "bone": bone_def["Offset Bone"],
                                                                                  "value": scalar,
                                                                                  "influence": influence,
                                                                                  "axis": prop_axis }

    # collect curve_slider control data into shapekey and bone driver defs
    for slider_name, slider_def in curve_slider_controls.items():

        control_def, line_bone_name, nub_bone_name, length, zero_point = slider_def
        control_range_y = control_def["range"]
        y_invert = control_range_y[1] < control_range_y[0]
        if y_invert:
            neg_y = length * (1 - zero_point) * control_range_y[1]
            pos_y = length * zero_point * control_range_y[0]
        else:
            neg_y = length * zero_point * control_range_y[0]
            pos_y = length * (1 - zero_point) * control_range_y[1]

        influence = control_def.get("influence", None)

        # only blend shapes in curve sliders
        if "blendshapes" in control_def:

            num_keys = len(control_def["blendshapes"])
            use_negative = (control_def.get("negative", False) or
                            ((num_keys == 1) and (abs(control_range_y[1] - control_range_y[0]) == 2)))
            for i, (shape_key_name, shape_key_value) in enumerate(control_def["blendshapes"].items()):
                curve: list = control_def["curve"][i].copy()
                curve.sort()
                var_axis = facerig_data.LOC_AXES.get("y")[1]
                if shape_key_name not in shape_key_driver_defs:
                    shape_key_driver_defs[shape_key_name] = {}
                key_control_def = {
                    "start": curve[0],
                    "mid": curve[1],
                    "end": curve[-1],
                    "value": abs(shape_key_value),
                    "distance": neg_y if shape_key_value < 0 else pos_y,
                    "invert": y_invert,
                    "var_axis": var_axis,
                    "num_keys": num_keys,
                    "use_strength": control_def.get("strength", True),
                    "use_negative": use_negative,
                    "influence": influence,
                }
                shape_key_driver_defs[shape_key_name][nub_bone_name] = key_control_def

    # collect rect control data into shape key and bone driver defs
    for rect_name, rect_def in rect_controls.items():

        control_def, box_bone_name, nub_bone_name, width, height, zero_x, zero_y = rect_def
        control_range_x = control_def["x_range"]
        control_range_y = control_def["y_range"]
        x_invert = control_range_x[1] < control_range_x[0]
        y_invert = control_range_y[1] < control_range_y[0]
        if x_invert:
            neg_x = width * (1 - zero_x) * control_range_x[1]
            pos_x = width * zero_x * control_range_x[0]
        else:
            neg_x = width * zero_x * control_range_x[0]
            pos_x = width * (1 - zero_x) * control_range_x[1]
        if y_invert:
            neg_y = height * (1 - zero_y) * control_range_y[1]
            pos_y = height * zero_y * control_range_y[0]
        else:
            neg_y = height * zero_y * control_range_y[0]
            pos_y = height * (1 - zero_y) * control_range_y[1]

        influence = control_def.get("influence", None)

        ctrl_axes = [
            ("horizontal", "x", neg_x, pos_x, control_range_x, x_invert),
            ("vertical", "y", neg_y, pos_y, control_range_y, y_invert)
        ]

        if "blendshapes" in control_def:

            for ctrl_dir, ctrl_axis, neg_d, pos_d, control_range, invert in ctrl_axes:

                num_keys = len(control_def["blendshapes"][ctrl_axis])
                use_negative = (control_def.get("negative", False) or
                                ((num_keys == 1) and (abs(control_range[1] - control_range[0]) == 2)))
                parent = control_def.get(f"{ctrl_axis}_parent")
                for i, (shape_key_name, shape_key_value) in enumerate(control_def["blendshapes"][ctrl_axis].items()):
                    var_axis = facerig_data.LOC_AXES.get(ctrl_axis)[1]
                    if shape_key_name not in shape_key_driver_defs:
                        shape_key_driver_defs[shape_key_name] = {}
                    key_control_def = {
                        "value": abs(shape_key_value),
                        "distance": neg_d if shape_key_value < 0 else pos_d,
                        "invert": invert,
                        "var_axis": var_axis,
                        "num_keys": num_keys,
                        "use_strength": control_def.get("strength", True),
                        "use_negative": use_negative,
                        "influence": influence,
                    }
                    shape_key_driver_defs[shape_key_name][nub_bone_name] = key_control_def

        bones_def = get_expression_bones_def(chr_cache, rect_name, control_def)
        if bones_def:

            for ctrl_dir, ctrl_axis, neg_d, pos_d, control_range, invert in ctrl_axes:
                for bone_def in bones_def[ctrl_dir]:
                    bone_name = bone_def["bone"]
                    value = bone_def.get("value", 1)
                    if bone_name in rigify_rig.pose.bones:

                        if "Translate" in bone_def:
                            for i, def_axis in enumerate(["x", "y", "z"]):
                                prop, axis, index = facerig_data.LOC_AXES.get(def_axis, (None, None, None))
                                scalar = bone_def["Translate"][i]
                                if abs(scalar) > 0.0001:
                                    driver_id = (bone_name, prop, index)
                                    var_axis = facerig_data.LOC_AXES.get(ctrl_axis)[1]
                                    bone_control_def = {
                                        "bone": bone_def["bone"],
                                        "offset": 0,
                                        "range": value,
                                        "scalar": scalar,
                                        "distance": neg_d if value < 0 else pos_d,
                                        "var_axis": var_axis,
                                        "use_strength": control_def.get("strength", True),
                                        "use_negative": use_negative,
                                        "influence": influence,
                                    }
                                    if driver_id not in bone_driver_defs:
                                        bone_driver_defs[driver_id] = {}
                                    bone_driver_defs[driver_id][(nub_bone_name, value, var_axis)] = bone_control_def

                        if "Rotation" in bone_def:
                            for i, def_axis in enumerate(["x", "y", "z"]):
                                prop, axis, index = facerig_data.ROT_AXES.get(def_axis, (None, None, None))
                                scalar = bone_def["Rotation"][i]
                                if abs(scalar) > 0.001:
                                    driver_id = (bone_name, prop, index)
                                    var_axis = facerig_data.LOC_AXES.get(ctrl_axis)[1]
                                    bone_control_def = {
                                        "bone": bone_def["bone"],
                                        "offset": 0,
                                        "scalar": scalar,
                                        "range": value,
                                        "distance": neg_d if value < 0 else pos_d,
                                        "var_axis": var_axis,
                                        "use_strength": control_def.get("strength", True),
                                        "use_negative": use_negative,
                                        "influence": influence,
                                    }
                                    #if bone_def["bone"] == "MCH-CTRL-eye.L":
                                    #    print ("MCH-CTRL-eye.L")
                                    #    print(driver_id)
                                    #    print(bone_control_def)
                                    if driver_id not in bone_driver_defs:
                                        bone_driver_defs[driver_id] = {}
                                    bone_driver_defs[driver_id][(nub_bone_name, value, var_axis)] = bone_control_def

                        if use_offset_rig and bone_def["Offset Bone"] and control_def.get("offset", False):
                            offset_bone = bone_def["Offset Bone"]
                            shape_key_name = bone_def["shape_key"]
                            source_tra = utils.array_to_vector(bone_def["Offset Translate"]) if "Offset Translate" in bone_def else Vector((0,0,0))
                            source_euler = bone_def["Offset Rotation"] if "Offset Rotation" in bone_def else  [0,0,0]
                            axes = ["x", "y", "z"]
                            if abs(source_euler[0]) + abs(source_euler[1]) + abs(source_euler[2]) > 0.01:
                                index = utils.largest_index(source_euler, use_abs=True)
                                axis = axes[index]
                                prop, prop_axis, prop_index = facerig_data.ROT_AXES.get(axis, (None, None, None))
                                scalar = source_euler[index]
                            elif source_tra.length > 0.001:
                                index = utils.largest_index(source_tra, use_abs=True)
                                axis = axes[index]
                                prop, prop_axis, prop_index = facerig_data.LOC_AXES.get(axis, (None, None, None))
                                scalar = source_tra[index]
                            if source_tra.length > 0.001 or (abs(source_euler[0]) + abs(source_euler[1]) + abs(source_euler[2])) > 0.01:
                                if shape_key_name not in offset_driver_defs:
                                    offset_driver_defs[shape_key_name] = {}
                                offset_driver_defs[shape_key_name][(nub_bone_name, value)] = { "dir": bone_def["value"],
                                                                                      "bone": offset_bone,
                                                                                      "value": scalar,
                                                                                      "influence": influence,
                                                                                      "axis": prop_axis }

    return shape_key_driver_defs, bone_driver_defs, offset_driver_defs


def fvar(float_value):
    return "{0:0.5f}".format(float_value).rstrip('0').rstrip('.')


def build_facerig_drivers(chr_cache, rigify_rig):

    # first drive the shape keys on any other body objects from the head body object
    # expression rig will then override these
    drivers.add_body_shape_key_drivers(chr_cache, True)

    BONE_CLEAR_CONSTRAINTS = [
            #"MCH-eye.L", "MCH-eye.R"
        ]

    FACERIG_CONFIG = get_facerig_config(chr_cache)
    facerig_bone = bones.get_pose_bone(rigify_rig, "facerig")

    # initialize target bone rotation modes and clear unwanted constraints
    for control_name, control_def in FACERIG_CONFIG.items():
        bones_def = get_expression_bones_def(chr_cache, control_name, control_def)

        if control_def["widget_type"] == "rect":
            if bones_def:
                for axis_dir, bone_list in bones_def.items():
                    for bone_def in bone_list:
                        bone_name = bone_def["bone"]
                        if bone_name in rigify_rig.pose.bones:
                            pose_bone = rigify_rig.pose.bones[bone_name]
                            pose_bone.rotation_mode = "XYZ"
                            if bone_name in BONE_CLEAR_CONSTRAINTS:
                                bones.clear_constraints(rigify_rig, bone_name)
        else:
            if bones_def:
                for bone_def in bones_def:
                    bone_name = bone_def["bone"]
                    if bone_name in rigify_rig.pose.bones:
                        pose_bone = rigify_rig.pose.bones[bone_name]
                        pose_bone.rotation_mode = "XYZ"
                        if bone_name in BONE_CLEAR_CONSTRAINTS:
                            bones.clear_constraints(rigify_rig, bone_name)

    if rigutils.select_rig(rigify_rig):

        bones.set_bone_collection_visibility(rigify_rig, "Face", 0, False)
        bones.set_bone_collection_visibility(rigify_rig, "Face (Primary)", 1, False)
        bones.set_bone_collection_visibility(rigify_rig, "Face (Secondary)", 2, False)

        facerig_bone = bones.get_pose_bone(rigify_rig, "facerig")
        if "head_follow" not in facerig_bone:
            drivers.add_custom_float_property(facerig_bone, "head_follow", 0.5,
                                              value_min=0.0, value_max=2.0,
                                              description="How much the expression rig follows the head movements")
        if "key_strength" not in facerig_bone:
            drivers.add_custom_float_property(facerig_bone, "key_strength", 1.0,
                                              value_min=0.0, value_max=2.0, precision=1,
                                              description="Overall strength of the expression rig shape keys")
        if "bone_strength" not in facerig_bone:
            drivers.add_custom_float_property(facerig_bone, "bone_strength", 1.0,
                                              value_min=0.0, value_max=2.0, precision=1,
                                              description="Overall strength of the expression rig bone movements")
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
        face_rig = bones.get_pose_bone(rigify_rig, "facerig")
        data_paths = [ face_rig.path_from_id("[\"eyes_track\"]"),
                       #face_rig.path_from_id("[\"eyes_track_enable\"]")
                       ]
        var_names = [ "trck",
                      #"trck_enable"
                      ]
        bones.add_constraint_influence_driver(rigify_rig, "MCH-eye.L", face_rig, data_paths, var_names, constraint_type="DAMPED_TRACK", expression="trck")
        bones.add_constraint_influence_driver(rigify_rig, "MCH-eye.R", face_rig, data_paths, var_names, constraint_type="DAMPED_TRACK", expression="trck")
        # special control bone offsets for jaw, eyes and head
        #bones.add_copy_location_constraint(rigify_rig, rigify_rig, "MCH-CTRL-head", "MCH-ROT-head", space="LOCAL_OWNER_ORIENT", use_offset=True)
        #bones.add_copy_rotation_constraint(rigify_rig, rigify_rig, "MCH-CTRL-head", "MCH-ROT-head", space="LOCAL_OWNER_ORIENT", use_offset=True)
        #bones.add_copy_location_constraint(rigify_rig, rigify_rig, "MCH-CTRL-jaw", "MCH-jaw_master", space="LOCAL_OWNER_ORIENT", use_offset=True)
        #bones.add_copy_rotation_constraint(rigify_rig, rigify_rig, "MCH-CTRL-jaw", "MCH-jaw_master", space="LOCAL_OWNER_ORIENT", use_offset=True)
        #bones.add_copy_location_constraint(rigify_rig, rigify_rig, "MCH-CTRL-eye.L", "MCH-eye.L", space="LOCAL_OWNER_ORIENT", use_offset=True)
        #bones.add_copy_rotation_constraint(rigify_rig, rigify_rig, "MCH-CTRL-eye.L", "MCH-eye.L", space="LOCAL_OWNER_ORIENT", use_offset=True)
        #bones.add_copy_location_constraint(rigify_rig, rigify_rig, "MCH-CTRL-eye.R", "MCH-eye.R", space="LOCAL_OWNER_ORIENT", use_offset=True)
        #bones.add_copy_rotation_constraint(rigify_rig, rigify_rig, "MCH-CTRL-eye.R", "MCH-eye.R", space="LOCAL_OWNER_ORIENT", use_offset=True)

        objects = chr_cache.get_cache_objects()
        slider_controls, curve_slider_controls, rect_controls = get_generated_controls(chr_cache, rigify_rig)
        shape_key_driver_defs, bone_driver_defs, offset_driver_defs = \
                    collect_driver_defs(chr_cache, rigify_rig,
                                        slider_controls, curve_slider_controls, rect_controls)

        # build shape key drivers from shape key driver defs
        for shape_key_name, shape_key_driver_def in shape_key_driver_defs.items():
            real_shape_key_name = get_objects_shape_key_name(objects, shape_key_name)
            var_defs = []
            vidx = 0
            var_expression = ""
            offset_expression = ""
            num_key_controls = len(shape_key_driver_def)
            use_negative = False
            use_strength = False
            value = 1.0
            influence = None
            for nub_bone_name, key_control_def in shape_key_driver_def.items():
                if nub_bone_name in rigify_rig.pose.bones:
                    is_curve = "start" in key_control_def
                    if is_curve:
                        start = key_control_def.get("start", 0.0)
                        mid = key_control_def.get("mid", 0.5)
                        end = key_control_def.get("end", 1.0)
                        if end == mid:
                            end = mid + mid - start
                        range = (end - mid + mid - start) / 2
                    num_keys = key_control_def["num_keys"]
                    var_axis = key_control_def["var_axis"]
                    distance = key_control_def["distance"]
                    use_strength = key_control_def["use_strength"]
                    influence = key_control_def["influence"]
                    if "use_negative" in key_control_def:
                        use_negative = key_control_def.get("use_negative", False)
                    value = key_control_def["value"]
                    var_name = drivers.find_bone_transform_var_def(var_defs, rigify_rig, nub_bone_name, var_axis, "TRANSFORM_SPACE")
                    if not var_name:
                        var_name = f"V{vidx}"
                        vidx += 1
                        var_def = drivers.make_bone_transform_var_def(var_name, rigify_rig, nub_bone_name, var_axis, "TRANSFORM_SPACE")
                        var_defs.append(var_def)
                    expr = f"{value}*{var_name}/{fvar(distance)}"
                    if is_curve:
                        ve = f"({expr})"
                        expr = f"min(1,max(0,1-abs({ve}-{fvar(mid)})/{fvar(range)}))"
                    if var_expression:
                        var_expression += "+"
                    #use_negative = use_negative and (num_keys == 1 or num_key_controls > 1)
                    if use_negative:
                        var_expression += f"({expr})"
                    else:
                        var_expression += f"max(0,{expr})"

            if shape_key_name in offset_driver_defs:
                offset_driver_def = offset_driver_defs[shape_key_name]
                #print("OFFSET:", shape_key_name, offset_driver_def)
                for (nub_bone_name, nub_value), offset_key_control_def in offset_driver_def.items():
                    #print("NUBS", nub_bone_name, nub_value, offset_key_control_def)
                    if nub_bone_name in rigify_rig.pose.bones:
                        offset_bone_name = offset_key_control_def["bone"]
                        value = offset_key_control_def["value"]
                        var_axis = offset_key_control_def["axis"]
                        dir = offset_key_control_def["dir"]
                        var_name = drivers.find_bone_transform_var_def(var_defs, rigify_rig, offset_bone_name, var_axis)
                        if not var_name:
                            var_name = f"V{vidx}"
                            vidx += 1
                            var_def = drivers.make_bone_transform_var_def(var_name, rigify_rig, offset_bone_name, var_axis)
                            var_defs.append(var_def)
                        expr = f"{var_name}/{fvar(value)}"
                        if offset_expression:
                            offset_expression += "+"
                        if use_negative:
                            offset_expression += f"({expr})"
                        else:
                            offset_expression += f"max(0,{expr})"
                #print(offset_expression)

            if influence:
                influence_var_name = drivers.find_custom_prop_var_def(var_defs, facerig_bone, "eyes_track")
                if not influence_var_name:
                    influence_var_name = "IV"
                    var_def = drivers.make_custom_prop_var_def(influence_var_name, facerig_bone, "eyes_track")
                    var_defs.append(var_def)
                if var_expression:
                    var_expression = f"(1-{influence_var_name})*({var_expression})"
                if offset_expression:
                    offset_expression = f"{influence_var_name}*({offset_expression})"

            if var_expression and offset_expression:
                var_expression = f"{var_expression}+{offset_expression}"

            if use_strength:
                var_expression = f"KS*({var_expression})"
                var_def = drivers.make_custom_prop_var_def("KS", facerig_bone, "key_strength")
                var_defs.append(var_def)

            shape_key_range = 1.0
            high = shape_key_range
            low = -shape_key_range if use_negative else 0
            expression = f"max({fvar(low)},min({fvar(high)},{var_expression}))"
            driver_def = ["SCRIPTED", expression]

            for obj in objects:
                if utils.object_has_shape_keys(obj):
                    drivers.add_shape_key_driver(rigify_rig, obj, real_shape_key_name, driver_def, var_defs, 1.0)

        # build bone transform drivers from bone driver defs
        for driver_id, bone_driver_def in bone_driver_defs.items():
            bone_name, prop, index = driver_id
            #if bone_name == "MCH-CTRL-eye.L":
            #    print("MCH-CTRL-eye.L")
            #    print(driver_id, bone_driver_def)
            var_defs = []
            vidx = 0
            var_expression = ""
            use_strength = False
            influence = None
            for (nub_bone_name, nub_value, var_axis_id), bone_control_def in bone_driver_def.items():
                offset = bone_control_def["offset"]
                scalar = bone_control_def["scalar"]
                var_axis = bone_control_def["var_axis"]
                distance = bone_control_def["distance"]
                dir_range = bone_control_def["range"]
                use_strength = bone_control_def["use_strength"]
                use_negative = bone_control_def.get("use_negative", False)
                influence = bone_control_def["influence"]
                var_name = drivers.find_bone_transform_var_def(var_defs, rigify_rig, nub_bone_name, var_axis, "TRANSFORM_SPACE")
                if not var_name:
                    var_name = f"V{vidx}"
                    vidx += 1
                    var_def = drivers.make_bone_transform_var_def(var_name, rigify_rig, nub_bone_name, var_axis, "TRANSFORM_SPACE")
                    var_defs.append(var_def)
                if var_expression:
                    var_expression += "+"
                if use_negative:
                    var_expression += f"({var_name}*{fvar(scalar/distance)})"
                elif nub_value >= 0:
                    var_expression += f"(max(0,{var_name})*{fvar(scalar/distance)})"
                else:
                    var_expression += f"(min(0,{var_name})*{fvar(scalar/distance)})"

            if influence:
                influence_var_name = drivers.find_custom_prop_var_def(var_defs, facerig_bone, "eyes_track")
                if not influence_var_name:
                    influence_var_name = "IV"
                    var_def = drivers.make_custom_prop_var_def(influence_var_name, facerig_bone, "eyes_track")
                    var_defs.append(var_def)
                if var_expression:
                    var_expression = f"(1-{influence_var_name})*({var_expression})"

            expression = var_expression
            if use_strength:
                expression = f"BS*({var_expression})"
                var_def = drivers.make_custom_prop_var_def("BS", facerig_bone, "bone_strength")
                var_defs.append(var_def)
            else:
                expression = var_expression

            driver_def = ["SCRIPTED", prop, index, expression]

            drivers.add_bone_driver(rigify_rig, bone_name, driver_def, var_defs, 1.0)

    # constraint drivers
    facial_profile, viseme_profile = chr_cache.get_facial_profile()
    if facial_profile == "MH":
        build_expression_constraint_drivers(chr_cache, rigify_rig)


def build_facerig_retarget_drivers(chr_cache, rigify_rig, source_rig, source_objects, shape_key_only=False, arkit=False):

    ctrl_drivers = {}

    FACERIG_CONFIG = get_facerig_config(chr_cache)

    if rigutils.select_rig(rigify_rig):

        facial_profile, viseme_profile = chr_cache.get_facial_profile()
        if facial_profile == "MH":
            # ensure curve retarget function is in driver namespace
            if ("rl_curve_retarget" not in bpy.app.driver_namespace or
                bpy.app.driver_namespace["rl_curve_retarget"] != func_rl_curve_slider_retarget):
                bpy.app.driver_namespace["rl_curve_retarget"] = func_rl_curve_slider_retarget

        for control_name, control_def in FACERIG_CONFIG.items():

            bones_def = get_expression_bones_def(chr_cache, control_name, control_def)

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
                invert = control_range[1] < control_range[0]
                mirror = control_def.get(f"{prefix}mirror", False)
                blend_shapes = control_def.get("blendshapes")
                if blend_shapes and key_group:
                    blend_shapes = blend_shapes[key_group]
                bones_def = get_expression_bones_def(chr_cache, control_name, control_def)
                if bones_def and bone_group:
                    bones_def = bones_def[bone_group]
                has_bones = bones_def and len(bones_def) > 0
                line_bone_name = control_name + line_suffix
                line_bone = bones.get_pose_bone(rigify_rig, line_bone_name)
                if not line_bone: continue
                slider_length = line_bone[f"{prefix}slider_length"] if f"{prefix}slider_length" in line_bone else line_bone.bone.length * 2
                #inv = -1 if control_def.get(f"{prefix}invert") else 1
                #inv = 1
                #if key_group == "y":
                #    inv *= -1
                slider_length *= control_scale

                driver_id = (control_name, "location", index)

                # only retarget from the bones if there are no blendshapes to use as a source
                retarget_bones = not blend_shapes and source_rig and has_bones
                if blend_shapes:
                    for blend_shape in blend_shapes:
                        if (blend_shape.startswith(("Dummy_")) or
                            blend_shape.startswith(("Teeth_"))):
                            retarget_bones = source_rig and has_bones
                if shape_key_only:
                    retarget_bones = False

                if retarget_bones:

                    ctrl_drivers[driver_id] = { "method": method,
                                                "parent": parent,
                                                "length": slider_length,
                                                "bones": [] }
                    for bone_def in bones_def:
                        source_name = bone_def["Source Bone"]
                        if "retarget_bones" in control_def:
                            if source_name not in control_def["retarget_bones"]:
                                continue
                        axis_dir = bone_def["value"]
                        if source_name in source_rig.pose.bones:
                            source_tra = utils.array_to_vector(bone_def["Source Translate"]) if "Source Translate" in bone_def else Vector((0,0,0))
                            source_euler = bone_def["Source Rotation"] if "Source Rotation" in bone_def else [0,0,0]
                            axes = ["x", "y", "z"]
                            if source_tra.length > 0.001:
                                index = utils.largest_index(source_tra, use_abs=True)
                                axis = axes[index]
                                prop, prop_axis, prop_index = facerig_data.LOC_AXES.get(axis, (None, None, None))
                                scalar = source_tra[index]
                                scale = slider_length
                                ctrl_drivers[driver_id]["bones"].append({ "bone": source_name,
                                                                          "dir": axis_dir,
                                                                          "value": scalar,
                                                                          "scale": scale,
                                                                          "axis": prop_axis })
                            elif abs(source_euler[0]) + abs(source_euler[1]) + abs(source_euler[2]) > 0.01:
                                index = utils.largest_index(source_euler, use_abs=True)
                                axis = axes[index]
                                prop, prop_axis, prop_index = facerig_data.ROT_AXES.get(axis, (None, None, None))
                                scalar = source_euler[index]
                                scale = slider_length
                                ctrl_drivers[driver_id]["bones"].append({ "bone": source_name,
                                                                          "dir": axis_dir,
                                                                          "value": scalar,
                                                                          "scale": scale,
                                                                          "axis": prop_axis })
                elif blend_shapes:

                    is_curve = control_def["widget_type"] == "curve_slider"
                    ctrl_drivers[driver_id] = { "method": method,
                                                "parent": parent,
                                                "length": slider_length,
                                                "is_curve": is_curve,
                                                "shape_keys": [] }

                    for i, (blend_shape_name, blend_shape_value) in enumerate(blend_shapes.items()):
                        # if 'retarget' list exists in control def, only retarget blendshapes
                        # in the list, to avoid uncontrolled duplicate retargets
                        if "retarget" in control_def:
                            if blend_shape_name not in control_def["retarget"]:
                                continue

                        if is_curve:
                            curve = control_def["curve"][i]
                            start = curve[0]
                            mid = curve[1]
                            end = curve[-1]
                            if end == mid:
                                end = mid + mid - start
                            range = (end - mid + mid - start) / 2
                        else:
                            mid = 0.5
                            range = 1

                        # if retargeting from an ARKit proxy, remap the shapes and only target these shapes
                        if arkit:
                            arkit_blend_shape_name = arkit_find_target_blend_shape(facial_profile, blend_shape_name)
                            if arkit_blend_shape_name:
                                blend_shape_name = arkit_blend_shape_name
                            else:
                                continue

                        ctrl_drivers[driver_id]["shape_keys"].append({ "shape_key": blend_shape_name,
                                                                       "value": blend_shape_value,
                                                                       "scale": slider_length,
                                                                       "mid": mid,
                                                                       "range": range })

        for driver_id, driver_def in ctrl_drivers.items():
            bone_name, prop, index = driver_id
            parent = driver_def["parent"]

            if parent != "NONE":
                parent_id = (parent, prop, index)
                parent_def = ctrl_drivers[parent_id]
                expression, var_defs = build_retarget_driver(chr_cache, rigify_rig, parent_id, parent_def,
                                                             source_rig, source_objects,
                                                             no_driver=True, length_override=abs(driver_def["length"]),
                                                             arkit=arkit)
                #print(bone_name, driver_id, parent_id, expression)
                #print("DRIVER:",driver_id, driver_def)
                #print("PARENT:",parent_id, parent_def)
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
    scale_override = 1
    if length_override is not None:
        length_override = abs(length_override)
        scale_override = length_override / length
        length = length_override
    pose_bone = bones.get_pose_bone(rigify_rig, bone_name)

    expression = ""
    var_defs = []
    prop_defs = []
    is_curve = driver_def.get("is_curve", False)

    vidx = 0 if not pre_var_defs else len(pre_var_defs)

    if "shape_keys" in driver_def:

        count = 0
        shape_key_defs = driver_def["shape_keys"]
        scale = 1
        for key_def in shape_key_defs:
            scale = key_def["scale"]
            value = key_def["value"]
            mid = key_def["mid"]
            range = key_def["range"]
            if length_override:
                scale *= scale_override
            shape_key_name = key_def["shape_key"]
            real_shape_key_name = get_objects_shape_key_name(source_objects, shape_key_name)
            if real_shape_key_name:
                var_name = f"V{vidx}"
                var_expr = f"min(1,{var_name})"
                if count > 0:
                    expression += "," if is_curve else "+"
                if is_curve:
                    var_expression = f"({var_expr}/{fvar(value)},{fvar(mid)},{fvar(range)})"
                else:
                    var_expression = f"({var_expr}*{fvar(scale/value)})"
                if arkit:
                    var_expression = add_arkit_driver_func(chr_cache, var_expression, length,
                                                           shape_key_name, prop_defs)
                expression += var_expression
                var_defs.append((var_name, real_shape_key_name))
                vidx += 1
                count += 1

        shape_key_range = length
        low = -shape_key_range
        high = shape_key_range

        if bone_name == "CTRL_C_eye" and method == "AVERAGE" and count == 4:
            count = 2

        if expression:
            if is_curve:
                expression = f"rl_curve_retarget([{expression}])*{fvar(scale)}"
            else:
                expression = f"({expression})"

        if expression and method == "AVERAGE" and count > 1:
            expression = f"min({fvar(high)},max({fvar(low)},{expression}/{count}))"

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
            value = bone_def["value"]
            axis = bone_def["axis"]
            axis_dir = bone_def["dir"]
            source_name = bone_def["bone"]
            if source_name in source_rig.pose.bones:
                var_name = f"V{vidx}"
                if count > 0:
                    expression += "+"
                if axis_dir == 0:
                    expression += f"({var_name}*{fvar(axis_dir*scale/value)})"
                elif axis_dir > 0:
                    expression += f"max(0,{var_name}*{fvar(axis_dir*scale/value)})"
                else:
                    expression += f"min(0,{var_name}*{fvar(axis_dir*scale/value)})"
                var_defs.append((var_name, source_name, axis))
                vidx += 1
                count += 1

        control_range = length
        low = -control_range
        high = control_range

        #if expression:
        #    expression = f"min({fvar(high)},max({fvar(low)},{expression}))"

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

EYE_TRACK_STORE = {}

def set_facerig_eye_tracking(rigify_rig, enable=True):
    face_rig = bones.get_pose_bone(rigify_rig, "facerig")
    if face_rig:
        face_rig["eyes_track"] = 1 if enable else 0


def func_rl_curve_slider_retarget(args):
    """args = [ (v0, m0, r0), (v1, m1, r1), ... ]"""
    T = 0.0001
    result = 0
    max_v = 0
    min_v = 1
    L = len(args) - 1
    for arg in args:
        v = arg[0]
        if v > max_v: max_v = v
        if v < min_v: min_v = v
    if max_v < T:
        result = 0
    elif args[L][0] > 1 - T:
        result = 1
    else:
        for i, arg in enumerate(args):
            v, m, r = arg
            if v == max_v:
                if i == 0:
                    v1 = args[i+1][0]
                    if v1 < T:
                        result = m - r * (1 - v)
                    else:
                        result = m + r * (1 - v)
                    break
                elif i == L:
                    result = m - r * (1 - v)
                    break
                else:
                    v0 = args[i-1][0]
                    v1 = args[i+1][0]
                    if v0 > v1:
                        result = m - r * (1 - v)
                    else:
                        result = m + r * (1 - v)
                    break
    return min(1, max(0, result))


def get_expression_shape_key_source_object(objects, head, shape_key_name):
    if utils.object_exists_is_mesh(head) and utils.object_has_shape_key(head, shape_key_name):
        return head
    for obj in objects:
        if utils.object_exists_is_mesh(obj) and utils.object_has_shape_key(obj, shape_key_name):
            return obj
    return None


def get_expression_constraint_var_expression(var_name, points):
    var_expression = ""
    if len(points) == 2:
        x0 = points[0][0] # should be 0.0
        x1 = points[1][0] # should be 0.0
        y0 = points[0][1] # should be 1.0
        y1 = points[1][1] # should be 1.0
        dy = y1 - y0
        dx = x1 - x0
        if dx == 0: dx = 1
        dybydx = dy / dx
        # y0 + (V - x0) * dy/dx
        var_expression = f"max(0,min(1,{fvar(y0)}+{fvar(dybydx)}*({var_name}-{fvar(x0)})))"
    elif len(points) == 3:
        xs = points[0][0] # should be 0.0
        ys = points[0][1] # should be 0.0
        xm = points[1][0] # should be 0.5
        ym = points[1][1] # should be 1.0
        xe = points[2][0] # should be 1.0
        ye = points[2][1] # should be 0.0
        dx = ((xe - xm) + (xm - xs)) / 2 # should be 0.5
        dy = ((ye - ym) + (ys - ym)) / 2 # should be -1
        if dx == 0: dx = 1
        dybydx = dy / dx
        # ym + abs(V - xm) * dy/dx
        var_expression = f"max(0,min(1,{fvar(ym)}+{fvar(dybydx)}*abs({var_name}-{fvar(xm)})))"
    elif len(points) == 5:
        xs = points[1][0] # should be 0.25
        ys = points[1][1] # should be 0.0
        xm = points[2][0] # should be 0.5
        ym = points[2][1] # should be 1.0
        xe = points[3][0] # should be 0.75
        ye = points[3][1] # should be 0.0
        dx = ((xe - xm) + (xm - xs)) / 2 # should be 0.25
        dy = ((ye - ym) + (ys - ym)) / 2 # should be -1
        if dx == 0: dx = 1
        dybydx = dy / dx
        var_expression = f"max(0,min(1,{fvar(ym)}+{fvar(dybydx)}*abs({var_name}-{fvar(xm)})))"
    return var_expression


def build_expression_constraint_add_driver(chr_cache, rigify_rig, objects, head,
                                source_keys, target_key,
                                curve_mode, points):
    var_defs = []
    vidx = 0
    expression = ""

    for key in source_keys:
        source_obj = get_expression_shape_key_source_object(objects, head, key)
        var_name = f"V{vidx}"
        vidx += 1
        var_def = drivers.make_shape_key_var_def(var_name, source_obj, key)
        var_defs.append(var_def)

        var_expression = get_expression_constraint_var_expression(var_name, points)

        if expression:
            expression += "*"
        expression += var_expression

    driver_def = ["SCRIPTED", expression]

    for obj in objects:
        if utils.object_has_shape_key(obj, target_key):
            drivers.add_shape_key_driver(rigify_rig, obj, target_key, driver_def, var_defs, 1.0)


def apply_control_limit_constraint_drivers(rigify_rig, control_name, control_def, target_key, expression, var_defs,
                                          line_suffix="_line", key_group="", axis="y"):
    nub_bone_name = control_name
    nub_bone = bones.get_pose_bone(rigify_rig, nub_bone_name)
    line_bone_name = control_name + line_suffix
    line_bone = bones.get_pose_bone(rigify_rig, line_bone_name)
    if nub_bone and line_bone:
        if "blendshapes" in control_def:
            if key_group:
                prefix = f"{key_group}_"
                shapes = control_def["blendshapes"][key_group]
            else:
                prefix = ""
                shapes = control_def["blendshapes"]
            for i, (key_name, key_value) in enumerate(shapes.items()):
                if key_name == target_key:
                    slider_length = line_bone[f"{prefix}slider_length"] if f"{prefix}slider_length" in line_bone else line_bone.bone.length * 2
                    control_range = control_def.get(f"{prefix}range")
                    invert = control_range[1] < control_range[0]
                    mirror = control_def.get(f"{prefix}mirror", False)
                    if invert:
                        key_value = -key_value
                    if mirror:
                        key_value = -key_value
                    limit_value = slider_length * key_value
                    if key_value < 0:
                        prop = f"min_{axis}"
                    else:
                        prop = f"max_{axis}"
                    limit_expression = f"{fvar(limit_value)}*{expression}"
                    driver_def = ["SCRIPTED", prop, -1, limit_expression]
                    drivers.add_constraint_prop_driver(rigify_rig, nub_bone_name,
                                                        driver_def, var_defs,
                                                        constraint_type="LIMIT_LOCATION")


def build_expression_constraint_limit_driver(chr_cache, rigify_rig, objects, head, source_keys, target_key, curve_mode, points):
    prefs = vars.prefs()

    var_defs = []
    vidx = 0
    limit_expression = ""

    for key in source_keys:
        source_obj = get_expression_shape_key_source_object(objects, head, key)
        var_name = f"lv{vidx}"
        vidx += 1
        var_def = drivers.make_shape_key_var_def(var_name, source_obj, key)
        var_defs.append(var_def)

        var_expression = get_expression_constraint_var_expression(var_name, points)

        if limit_expression:
            limit_expression += "*"
        limit_expression += var_expression

    # limit facerig control movement ranges
    if prefs.rigify_limit_control_range:
        FACERIG_CONFIG = get_facerig_config(chr_cache)
        for control_name, control_def in FACERIG_CONFIG.items():
            if control_def["widget_type"] == "slider":
                apply_control_limit_constraint_drivers(rigify_rig, control_name, control_def,
                                                    target_key, limit_expression, var_defs,
                                                    "_line", "", "y")
            elif control_def["widget_type"] == "rect":
                apply_control_limit_constraint_drivers(rigify_rig, control_name, control_def,
                                                    target_key, limit_expression, var_defs,
                                                    "_box", "x", "x")
                apply_control_limit_constraint_drivers(rigify_rig, control_name, control_def,
                                                    target_key, limit_expression, var_defs,
                                                    "_box", "y", "y")

    # apply a min(expression, limit_expression) to existing shape key value driver
    # (driving the shape key max value has no effect)
    for obj in objects:
        if utils.object_has_shape_key(obj, target_key):
            driver: bpy.types.Driver = drivers.get_shape_key_driver(obj, target_key)
            if driver and driver.expression:
                driver_expression = driver.expression
                drivers.add_driver_var_defs(driver, var_defs)
                new_expression = f"min({driver_expression}, {limit_expression})"
                driver.expression = new_expression
            else:
                utils.log_warn(f"NO DRIVER: {obj.name} {target_key}")


def build_expression_constraint_drivers(chr_cache, rigify_rig):
    objects = chr_cache.get_cache_objects()
    head = drivers.get_head_body_object(chr_cache)
    constraint_json = chr_cache.get_constraint_json()
    if constraint_json:
        for constraint_name, constraint_def in constraint_json.items():
            source_keys = constraint_def["Source Channels"]
            target_key = constraint_def["Target Channel"]
            curve_mode = constraint_def["Curve Mode"]
            mode = constraint_def["Mode"]
            points = []
            for point in constraint_def["Curve"]:
                co = (min(1, max(0, point[0])), (min(1, max(0, point[1]))))
                if co not in points:
                    points.append(co)
            # sort by x value
            points.sort(key=lambda co: co[0])
            if mode == "Add":
                build_expression_constraint_add_driver(chr_cache, rigify_rig, objects, head, source_keys, target_key, curve_mode, points)
            elif mode == "Limit":
                build_expression_constraint_limit_driver(chr_cache, rigify_rig, objects, head, source_keys, target_key, curve_mode, points)


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
    bones.clear_pose(rigify_rig, control_bones)
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
    if not chr_cache:
        chr_cache, obj, mat, obj_cache, mat_cache = utils.get_context_character(context)
    if chr_cache:
        FACERIG_CONFIG = get_facerig_config(chr_cache)
        rigify_rig = chr_cache.get_armature()
        if rigify_rig and "facerig" in rigify_rig.pose.bones:
            if utils.B410():
                for control_bone_name, control_def in FACERIG_CONFIG.items():
                    color_shift = control_def.get("color_shift", 0.0)
                    if control_bone_has_driver(rigify_rig, control_bone_name):
                        color_code = "DRIVER"
                    else:
                        color_code = "FACERIG"
                    bones.set_bone_color(rigify_rig, control_bone_name, color_code, color_code, color_code, chr_cache=chr_cache, hue_shift=color_shift)
                    if control_def["widget_type"] == "rect":
                        lines_bone_name = control_bone_name + "_box"
                    else:
                        lines_bone_name = control_bone_name + "_line"
                    bones.set_bone_color(rigify_rig, lines_bone_name, "FACERIG_DARK", "FACERIG_DARK", "FACERIG_DARK", chr_cache=chr_cache, hue_shift=color_shift)
            else:
                props_color = chr_cache.rigify_face_control_color
                custom_color = (props_color[0], props_color[1], props_color[2])
                bone_group = rigify_rig.pose.bone_groups["Face"]
                bone_group.colors.normal = utils.linear_to_srgb(custom_color)


def is_position_locked(rig):
    if "facerig" in rig.pose.bones:
        return rig.pose.bones["facerig"].bone.hide_select


def toggle_lock_position(chr_cache, rig):
    FACERIG_CONFIG = get_facerig_config(chr_cache)
    bone_names = [ "facerig", "facerig_groups", "facerig_labels", "facerig_name",
                   "facerig2", "facerig2_groups", "facerig2_labels", ]
    bone_selectable = [ True, False, False, False,
                        True, False, False ]
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
    con1 = bones.add_copy_rotation_constraint(proxy_rig, rigify_rig, "head", "head", space="LOCAL_WITH_PARENT")
    con2 = bones.add_copy_rotation_constraint(proxy_rig, rigify_rig, "head", "neck", 0.25, space="LOCAL_WITH_PARENT")
    con3 = bones.add_copy_rotation_constraint(proxy_rig, rigify_rig, "offset", "head", use_offset=True, space="LOCAL_WITH_PARENT")
    con4 = bones.add_copy_rotation_constraint(proxy_rig, rigify_rig, "offset", "neck", 0.25, use_offset=True, space="LOCAL_WITH_PARENT")
    con1.name = con1.name + "_ARKit_Proxy"
    con2.name = con2.name + "_ARKit_Proxy"
    con3.name = con1.name + "_ARKit_Proxy"
    con4.name = con2.name + "_ARKit_Proxy"
    data_path = proxy_rig.path_from_id("[\"head_blend\"]")
    bones.add_constraint_influence_driver(rigify_rig, "head",
                                          proxy_rig, data_path, "var_head_blend", con1, expression="var_head_blend*0.01")
    bones.add_constraint_influence_driver(rigify_rig, "neck",
                                          proxy_rig, data_path, "var_head_blend", con2, expression="var_head_blend*0.0025")
    bones.add_constraint_influence_driver(rigify_rig, "head",
                                          proxy_rig, data_path, "var_head_blend", con3, expression="var_head_blend*0.01")
    bones.add_constraint_influence_driver(rigify_rig, "head",
                                          proxy_rig, data_path, "var_head_blend", con4, expression="var_head_blend*0.0025")

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
        tcurve: TCurve = None
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
            fcurve_data[i * 2 + 1] = v * mod
        fcurve.keyframe_points.clear()
        fcurve.keyframe_points.add(num_frames)
        fcurve.keyframe_points.foreach_set('co', fcurve_data)

    def dump(self):
        utils.log_always(self.name)
        utils.log_always(self.length)
        for i, (f, v) in enumerate(self.points):
            utils.log_always(i, f, v)
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