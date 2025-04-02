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

import bpy, struct, json
from mathutils import Vector, Matrix, Color, Quaternion
from enum import IntEnum
from . import utils

class RLXCodes(IntEnum):
    RLX_ID_LIGHT = 0xCC01
    RLX_ID_CAMERA = 0xCC02

RECTANGULAR_AS_AREA = False
TUBE_AS_AREA = True
ENERGY = 35

class BinaryData():
    data: bytearray = None
    offset: int = 0

    def __init__(self, data: bytearray = None, start_offset = 0,
                       file_path: str = None, file = None):
        if data:
            self.data = data
        elif file_path:
            with open(file_path, 'rb') as read_file:
                self.data = bytearray(read_file.read())
        elif file:
            self.data = bytearray(file.read())
        self.offset = start_offset

    def json(self):
        size = self.int()
        data = self.bytes(size)
        text = data.decode("utf-8")
        obj = json.loads(text)
        return obj

    def float(self):
        value = struct.unpack_from("!f", self.data, self.offset)[0]
        self.offset += 4
        return value

    def int(self):
        value = struct.unpack_from("!I", self.data, self.offset)[0]
        self.offset += 4
        return value

    def bool(self):
        value = struct.unpack_from("!?", self.data, self.offset)[0]
        self.offset += 1
        return value

    def string(self):
        length = self.int()
        data = self.bytes(length)
        value = data.decode(encoding="utf-8")
        return value

    def time(self):
        time_code = self.int()
        return float(time_code) / 6000.0

    def vector(self):
        x = self.float()
        y = self.float()
        z = self.float()
        value = Vector((x, y, z))
        return value

    def quaternion(self):
        x = self.float()
        y = self.float()
        z = self.float()
        w = self.float()
        value = Quaternion((w, x, y, z))
        return value

    def color(self):
        r = self.float()
        g = self.float()
        b = self.float()
        value = Color((r, g, b))
        return value

    def bytes(self, size):
        sub_data = self.data[self.offset:self.offset+size]
        self.offset += size
        return sub_data

    def block(self):
        size = self.int()
        data = self.bytes(size)
        return BinaryData(data=data)

    def eof(self):
        return self.offset >= len(self.data)


def import_rlx(file_path):
    data = BinaryData(file_path=file_path)
    rlx_code = data.int()
    utils.log_info(f"RLX Code: {rlx_code}")
    if rlx_code == RLXCodes.RLX_ID_LIGHT:
        return import_rlx_light(data)
    elif rlx_code == RLXCodes.RLX_ID_CAMERA:
        return import_rlx_camera(data)
    return None


def import_rlx_light(data: BinaryData):
    light_data = data.json()
    # make the light
    link_id = light_data["link_id"]
    light = find_link_id(link_id)
    if utils.B440():
        action: bpy.types.Action = None
        if light:
            action = utils.safe_get_action(light)
    else:
        ob_action = None
        light_action = None
        if light:
            ob_action = utils.safe_get_action(light)
            light_action = utils.safe_get_action(light.data)
    light = decode_rlx_light(light_data, light)
    # static properties
    name: str = light_data["name"]
    type: str = light_data["type"]
    inverse_square: bool = light_data["inverse_square"]
    transmission: bool = light_data["transmission"]
    is_tube: bool = light_data["is_tube"]
    tube_length: float = light_data["tube_length"] / 100
    tube_radius: float = light_data["tube_radius"] / 100
    tube_soft_radius: float = light_data["tube_soft_radius"] / 100
    is_rectangle: bool = light_data["is_rectangle"]
    rect: tuple = (light_data["rect"][0] / 100, light_data["rect"][1] / 100)
    cast_shadow: bool = light_data["cast_shadow"]
    num_frames = light_data["frame_count"]
    light_type = get_light_type(type, is_rectangle, is_tube)
    # now read in the frames and create an action for the light...
    frames = data.block()

    loc_cache = frame_cache(num_frames, 3)
    rot_cache = frame_cache(num_frames, 4)
    sca_cache = frame_cache(num_frames, 3)
    color_cache = frame_cache(num_frames, 3)
    energy_cache = frame_cache(num_frames)
    cutoff_distance_cache = frame_cache(num_frames)
    spot_blend_cache = frame_cache(num_frames)
    spot_size_cache = frame_cache(num_frames)

    frame = 0
    while not frames.eof():
        frame += 1
        time = frames.time()
        frame = frames.int()
        active = frames.bool()
        loc = frames.vector() / 100
        rot = frames.quaternion()
        sca = frames.vector()
        color = frames.color()
        multiplier = frames.float()
        range = frames.float() / 100
        angle = frames.float() * 0.01745329
        falloff = frames.float() / 100
        attenuation = frames.float() / 100
        darkness = frames.float()
        if not active:
            multiplier = 0.0
        cutoff_distance = range
        store_frame(loc_cache, frame, loc)
        store_frame(rot_cache, frame, rot)
        store_frame(sca_cache, frame, sca)
        store_frame(color_cache, frame, color)
        store_frame(cutoff_distance_cache, frame, cutoff_distance)
        if light_type == "SUN":
            energy = 2 * multiplier
            store_frame(energy_cache, frame, energy)
        elif light_type == "SPOT":
            energy = ENERGY * multiplier
            spot_blend = (falloff + attenuation) / 2
            spot_size = angle
            store_frame(energy_cache, frame, energy)
            store_frame(spot_blend_cache, frame, spot_blend)
            store_frame(spot_size_cache, frame, spot_size)
        elif light_type == "AREA":
            energy = ENERGY * multiplier
            store_frame(energy_cache, frame, energy)


    if utils.B440():
        action_name = f"{name}|Export_{utils.datetimes()}"
        ob_slot_name = f"{name}|O|Export_{utils.datetimes()}"
        light_slot_name = f"{name}|L|Export_{utils.datetimes()}"
        if action:
            utils.clear_action(action)
            action.name = action_name
        else:
            action = bpy.data.actions.new(action_name)
        ob_slot = action.slots.new("OBJECT", ob_slot_name)
        light_slot = action.slots.new("LIGHT", light_slot_name)
        channelbag = utils.get_channel_bag(action, ob_slot)
        add_cache_fcurves(action, light.path_from_id("location"), loc_cache, num_frames, "Location", channelbag=channelbag)
        add_cache_fcurves(action, light.path_from_id("rotation_quaternion"), rot_cache, num_frames, "Rotation Quaternion", channelbag=channelbag)
        add_cache_fcurves(action, light.path_from_id("scale"), sca_cache, num_frames, "Scale", channelbag=channelbag)
        channelbag = utils.get_channel_bag(action, light_slot)
        add_cache_fcurves(action, light.data.path_from_id("color"), color_cache, num_frames, "Color", channelbag=channelbag)
        add_cache_fcurves(action, light.data.path_from_id("energy"), energy_cache, num_frames, "Energy", channelbag=channelbag)
        add_cache_fcurves(action, light.data.path_from_id("cutoff_distance"), cutoff_distance_cache, num_frames, "Cutoff Distance", channelbag=channelbag)
        if light_type == "SPOT":
            add_cache_fcurves(action, light.data.path_from_id("spot_blend"), spot_blend_cache, num_frames, "Spot Blend", channelbag=channelbag)
            add_cache_fcurves(action, light.data.path_from_id("spot_size"), spot_size_cache, num_frames, "Spot Size", channelbag=channelbag)
        utils.safe_set_action(light, action, slot=ob_slot)
        utils.safe_set_action(light.data, action, slot=light_slot)
    else:
        ob_action_name = f"{name}|O|Export_{utils.datetimes()}"
        light_action_name = f"{name}|L|Export_{utils.datetimes()}"
        if ob_action:
            utils.clear_action(ob_action)
            ob_action.name = ob_action_name
        else:
            ob_action = bpy.data.actions.new(ob_action_name)
        if light_action:
            utils.clear_action(light_action)
            light_action.name = light_action_name
        else:
            light_action = bpy.data.actions.new(light_action_name)
        add_cache_fcurves(ob_action, light.path_from_id("location"), loc_cache, num_frames, "Location")
        add_cache_fcurves(ob_action, light.path_from_id("rotation_quaternion"), rot_cache, num_frames, "Rotation Quaternion")
        add_cache_fcurves(ob_action, light.path_from_id("scale"), sca_cache, num_frames, "Scale")
        add_cache_fcurves(light_action, light.data.path_from_id("color"), color_cache, num_frames, "Color")
        add_cache_fcurves(light_action, light.data.path_from_id("energy"), energy_cache, num_frames, "Energy")
        add_cache_fcurves(light_action, light.data.path_from_id("cutoff_distance"), cutoff_distance_cache, num_frames, "Cutoff Distance")
        if light_type == "SPOT":
            add_cache_fcurves(light_action, light.data.path_from_id("spot_blend"), spot_blend_cache, num_frames, "Spot Blend")
            add_cache_fcurves(light_action, light.data.path_from_id("spot_size"), spot_size_cache, num_frames, "Spot Size")
        utils.safe_set_action(light, ob_action)
        utils.safe_set_action(light.data, light_action)


def import_rlx_camera(data: BinaryData):
    camera_data = data.json()
    # make the camera
    link_id = camera_data["link_id"]
    camera = find_link_id(link_id)
    if utils.B440():
        action = None
        if camera:
            action = utils.safe_get_action(camera)
    else:
        ob_action = None
        cam_action = None
        if camera:
            ob_action = utils.safe_get_action(camera)
            cam_action = utils.safe_get_action(camera.data)
    camera = decode_rlx_camera(camera_data, camera)
    # static properties
    link_id = camera_data["link_id"]
    name: str = camera_data["name"]
    fit = camera_data["fit"]
    width = camera_data["width"] # mm
    height = camera_data["height"] # mm
    far_clip = camera_data["far_clip"] / 100
    near_clip = camera_data["near_clip"] / 100
    pivot_pos = utils.array_to_vector(camera_data["pos"]) / 100
    dof_weight = camera_data["dof_weight"]
    dof_decay = camera_data["dof_decay"]
    # now read in the frames and create an action for the light...
    num_frames = camera_data["frame_count"]
    frames = data.block()
    loc_cache = frame_cache(num_frames, 3)
    rot_cache = frame_cache(num_frames, 4)
    sca_cache = frame_cache(num_frames, 3)
    lens_cache = frame_cache(num_frames)
    dof_cache = frame_cache(num_frames)
    focus_distance_cache = frame_cache(num_frames)
    f_stop_cache = frame_cache(num_frames)

    frame = 0
    while not frames.eof():
        frame += 1
        time = frames.time()
        frame = frames.int()
        loc = frames.vector() / 100
        rot = frames.quaternion()
        sca = frames.vector()
        focal_length = frames.float() # mm
        dof_enable = frames.bool()
        dof_focus = frames.float() / 100
        dof_range = frames.float() / 100
        dof_far_blur = frames.float()
        dof_near_blur = frames.float()
        dof_far_transition = frames.float() / 100
        dof_near_transition = frames.float() / 100
        dof_min_blend_distance = frames.float()
        store_frame(loc_cache, frame, loc)
        store_frame(rot_cache, frame, rot)
        store_frame(sca_cache, frame, sca)
        store_frame(lens_cache, frame, focal_length)
        store_frame(dof_cache, frame, 1.0 if dof_enable else 0.0)
        store_frame(focus_distance_cache, frame, dof_focus)
        blur = (dof_far_blur + dof_near_blur) / 2
        transition = (dof_far_transition + dof_near_transition) / 2
        f_stop = transition
        store_frame(f_stop_cache, frame, f_stop)

    if utils.B440():
        action_name = f"{name}|Export_{utils.datetimes()}"
        ob_slot_name = f"{name}|O|Export_{utils.datetimes()}"
        cam_slot_name = f"{name}|C|Export_{utils.datetimes()}"
        if action:
            utils.clear_action(action)
            action.name = action_name
        else:
            action = bpy.data.actions.new(action_name)
        ob_slot = action.slots.new("OBJECT", ob_slot_name)
        cam_slot = action.slots.new("CAMERA", cam_slot_name)
        channelbag = utils.get_channel_bag(action, ob_slot)
        add_cache_fcurves(action, "location", loc_cache, num_frames, "Location", channelbag=channelbag)
        add_cache_fcurves(action, "rotation_quaternion", rot_cache, num_frames, "Rotation Quaternion", channelbag=channelbag)
        add_cache_fcurves(action, "scale", sca_cache, num_frames, "Scale", channelbag=channelbag)
        channelbag = utils.get_channel_bag(action, cam_slot)
        add_cache_fcurves(action, "lens", lens_cache, num_frames, "Camera", channelbag=channelbag)
        add_cache_fcurves(action, "dof.use_dof", dof_cache, num_frames, "DOF", channelbag=channelbag)
        add_cache_fcurves(action, "dof.focus_distance", focus_distance_cache, num_frames, "DOF", channelbag=channelbag)
        add_cache_fcurves(action, "dof.f_stop", f_stop_cache, num_frames, "DOF", channelbag=channelbag)
        utils.safe_set_action(camera, action, slot=ob_slot)
        utils.safe_set_action(camera.data, action, slot=cam_slot)
    else:
        ob_action_name = f"{name}|O|Export_{utils.datetimes()}"
        cam_action_name = f"{name}|C|Export_{utils.datetimes()}"
        if ob_action:
            utils.clear_action(ob_action)
            ob_action.name = ob_action_name
        else:
            ob_action = bpy.data.actions.new(ob_action_name)
        if cam_action:
            utils.clear_action(cam_action)
            cam_action.name = cam_action_name
        else:
            cam_action = bpy.data.actions.new(cam_action_name)
        add_cache_fcurves(action, "location", loc_cache, num_frames, "Location")
        add_cache_fcurves(action, "rotation_quaternion", rot_cache, num_frames, "Rotation Quaternion")
        add_cache_fcurves(action, "scale", sca_cache, num_frames, "Scale")
        add_cache_fcurves(action, "lens", lens_cache, num_frames, "Camera")
        add_cache_fcurves(action, "dof.use_dof", dof_cache, num_frames, "DOF")
        add_cache_fcurves(action, "dof.focus_distance", focus_distance_cache, num_frames, "DOF")
        add_cache_fcurves(action, "dof.f_stop", f_stop_cache, num_frames, "DOF")
        utils.safe_set_action(camera, ob_action)
        utils.safe_set_action(camera.data, cam_action)


def frame_cache(frames, indices=1, default_value=0.0):
    cache = []
    for i in range(0, indices):
        data = [0, default_value] * frames
        for j in range(0, frames):
            data[j * 2] = j
        cache.append(data)
    return cache


def store_frame(cache, frame, value):
    T = type(value)
    if T is Vector or T is Color or T is Quaternion:
        l = len(value)
        for i in range(0, l):
            cache[i][frame * 2 + 1] = value[i]
    else:
        cache[0][frame * 2 + 1] = value


def add_cache_fcurves(action: bpy.types.Action, data_path, cache, num_frames, group_name=None, channelbag=None):
    num_curves = len(cache)
    fcurve: bpy.types.FCurve
    if channelbag:
        if group_name not in channelbag.groups:
            channelbag.groups.new(group_name)
        for i in range(0, num_curves):
            fcurve = channelbag.fcurves.new(data_path, index=i)
            fcurve.group = channelbag.groups[group_name]
            fcurve.keyframe_points.add(num_frames)
            fcurve.keyframe_points.foreach_set('co', cache[i])
    else:
        for i in range(0, num_curves):
            fcurve = action.fcurves.new(data_path, index=i, action_group=group_name)
            fcurve.keyframe_points.add(num_frames)
            fcurve.keyframe_points.foreach_set('co', cache[i])


def decode_rlx_light(light_data, light: bpy.types.Object=None, container=None):
    # static properties
    link_id = light_data["link_id"]
    name: str = light_data["name"]
    type: str = light_data["type"]
    inverse_square: bool = light_data["inverse_square"]
    transmission: bool = light_data["transmission"]
    is_tube: bool = light_data["is_tube"]
    tube_length: float = light_data["tube_length"] / 100
    tube_radius: float = light_data["tube_radius"] / 100
    tube_soft_radius: float = light_data["tube_soft_radius"] / 100
    is_rectangle: bool = light_data["is_rectangle"]
    rect: tuple = (light_data["rect"][0] / 100, light_data["rect"][1] / 100)
    cast_shadow: bool = light_data["cast_shadow"]
    # animateable properties
    active = light_data["active"]
    loc = utils.array_to_vector(light_data["loc"]) / 100
    rot = utils.array_to_quaternion(light_data["rot"])
    sca = utils.array_to_vector(light_data["sca"])
    color = utils.array_to_color(light_data["color"])
    multiplier = light_data["multiplier"]
    range = light_data["range"] / 100
    angle = light_data["angle"] * 0.01745329
    falloff = light_data["falloff"] / 100
    attenuation = light_data["attenuation"] / 100
    darkness = light_data["darkness"]
    light_type = get_light_type(type, is_rectangle, is_tube)


    if light and (light.type != "LIGHT" or light.data.type != light_type):
        utils.delete_light_object(light)
        light = None

    if not light:
        if light_type == "AREA":
            light = add_area_light(light_data["name"], container)
        elif light_type == "POINT":
            light = add_point_light(light_data["name"], container)
        elif light_type == "SUN":
            light = add_dir_light(light_data["name"], container)
        else:
            light = add_spot_light(light_data["name"], container)
        utils.set_rl_link_id(light, link_id)

    light.location = loc
    light.rotation_mode = "QUATERNION"
    light.rotation_quaternion = rot
    light.scale = sca
    light.data.color = color

    if light_type == "SUN":
        light.data.energy = 2 * multiplier

    elif light_type == "SPOT":
        light.data.energy = ENERGY * multiplier
        light.data.use_custom_distance = True
        light.data.cutoff_distance = range
        light.data.spot_blend = (falloff + attenuation) / 2
        light.data.spot_size = angle
        light.data.use_soft_falloff = True
        if is_rectangle:
            light.data.shadow_soft_size = (rect[0] + rect[1]) / 3
        elif is_tube:
            light.data.shadow_soft_size = (tube_radius + tube_length) / 3


    elif light_type == "AREA":
        light.data.energy = ENERGY * multiplier
        light.data.use_custom_distance = True
        light.data.cutoff_distance = range
        if is_rectangle:
            light.data.shape = "RECTANGLE"
            light.data.size = rect[0]
            light.data.size_y = rect[1]
        elif is_tube:
            light.data.shape = "ELLIPSE"
            light.data.size = 10 * max(0.01, tube_length)
            light.data.size_y = tube_radius

    elif light_type == "POINT":
        light.data.energy = ENERGY * 2.0 * multiplier
        light.data.use_custom_distance = True
        light.data.cutoff_distance = range

    light.data.use_shadow = cast_shadow
    if cast_shadow:
        if utils.B420():
            light.data.use_shadow_jitter = True
        else:
            if light_type != "SUN":
                light.data.shadow_buffer_clip_start = 0.0025
                light.data.shadow_buffer_bias = 1.0
            light.data.use_contact_shadow = True
            light.data.contact_shadow_distance = 0.1
            light.data.contact_shadow_bias = 0.03
            light.data.contact_shadow_thickness = 0.001
    if not active:
        utils.hide(light)
    return light


def decode_rlx_camera(camera_data, camera):
    # static properties
    link_id = camera_data["link_id"]
    name: str = camera_data["name"]
    fit = camera_data["fit"]
    width = camera_data["width"] # mm
    height = camera_data["height"] # mm
    far_clip = camera_data["far_clip"] / 100
    near_clip = camera_data["near_clip"] / 100
    pivot_pos = utils.array_to_vector(camera_data["pos"]) / 100
    dof_weight = camera_data["dof_weight"]
    dof_decay = camera_data["dof_decay"]
    # animateable properties
    fov = camera_data["fov"]
    focal_length = camera_data["focal_length"] # mm
    loc = utils.array_to_vector(camera_data["loc"]) / 100
    rot = utils.array_to_quaternion(camera_data["rot"])
    sca = utils.array_to_vector(camera_data["sca"])
    dof_enable = camera_data["dof_enable"]
    dof_focus = camera_data["dof_focus"] / 100
    dof_range = camera_data["dof_range"] / 100
    dof_far_blur = camera_data["dof_far_blur"] # 0.1 - 1.8
    dof_near_blur = camera_data["dof_near_blur"] # 0.1 - 1.8
    dof_far_transition = camera_data["dof_far_transition"] / 100
    dof_near_transition = camera_data["dof_near_transition"] / 100
    dof_min_blend_distance = camera_data["dof_min_blend_distance"] # 0.0 - 1.0

    if camera and camera.type != "CAMERA":
        utils.delete_object(camera)
        camera = None

    if not camera:
        camera = add_camera(name)
        utils.set_rl_link_id(camera, link_id)

    camera.location = loc
    camera.rotation_mode = "QUATERNION"
    camera.rotation_quaternion = rot
    camera.scale = sca
    camera.data.lens = focal_length
    camera.data.sensor_fit = fit
    camera.data.sensor_width = width
    camera.data.sensor_height = height
    camera.data.clip_start = near_clip
    camera.data.clip_end = far_clip
    # depth of field
    camera.data.dof.use_dof = dof_enable
    camera.data.dof.focus_distance = dof_focus
    # not much we can do about blur as DOF blur is a global scene setting in Blender (and only for Eevee)
    # bpy.data.scenes["Scene"].eevee.bokeh_max_size
    # TODO maybe blur can be incorporated into f_stop
    # TODO maybe dof_range too (perfect focus range)
    blur = (dof_far_blur + dof_near_blur) / 2
    # transition range can be interpreted as the f-stop
    transition = (dof_far_transition + dof_near_transition) / 2
    f_stop = transition
    camera.data.dof.aperture_fstop = f_stop
    return camera


def get_light_type(rl_type, is_rectangle, is_tube):
    shape = "RECTANGLE" if is_rectangle else "TUBE" if is_tube else "NONE"
    if rl_type == "DIR":
        light_type = "SUN"
    else:
        light_type = rl_type
    if TUBE_AS_AREA and shape == "TUBE":
        light_type = "AREA"
    if RECTANGULAR_AS_AREA and shape == "RECTANGLE":
        light_type = "AREA"
    # area lights reproduce linear falloff (none inverse_square) lights best
    #if light_type == "SPOT" or light_type == "POINT":
    #    if (shape == "TUBE" or shape == "NONE") and not inverse_square:
    #        light_type = "AREA"
    return light_type


def find_link_id(link_id: str):
    for obj in bpy.data.objects:
        obj_link_id = utils.get_rl_link_id(obj)
        if obj_link_id == link_id:
            return obj
    return None


def add_camera(name, container=None):
    bpy.ops.object.camera_add()
    camera = utils.get_active_object()
    camera.name = name
    camera.data.name = name
    utils.set_ccic_id(camera)
    if container:
        camera.parent = container
        camera.matrix_parent_inverse = container.matrix_world.inverted()
    return camera


def add_spot_light(name, container=None):
    bpy.ops.object.light_add(type="SPOT")
    light = utils.get_active_object()
    light.name = name
    light.data.name = name
    utils.set_ccic_id(light)
    if container:
        light.parent = container
        light.matrix_parent_inverse = container.matrix_world.inverted()
    return light


def add_area_light(name, container=None):
    bpy.ops.object.light_add(type="AREA")
    light = utils.get_active_object()
    light.name = name
    light.data.name = name
    utils.set_ccic_id(light)
    if container:
        light.parent = container
        light.matrix_parent_inverse = container.matrix_world.inverted()
    return light


def add_point_light(name, container=None):
    bpy.ops.object.light_add(type="POINT")
    light = utils.get_active_object()
    light.name = name
    light.data.name = name
    utils.set_ccic_id(light)
    if container:
        light.parent = container
        light.matrix_parent_inverse = container.matrix_world.inverted()
    return light


def add_dir_light(name, container=None):
    bpy.ops.object.light_add(type="SUN")
    light = utils.get_active_object()
    light.name = name
    light.data.name = name
    utils.set_ccic_id(light)
    if container:
        light.parent = container
        light.matrix_parent_inverse = container.matrix_world.inverted()
    return light


def add_light_container():
    container = None
    for obj in bpy.data.objects:
        if obj.type == "EMPTY" and "Lighting" in obj.name and utils.has_ccic_id(obj):
            container = obj
    if not container:
        bpy.ops.object.empty_add(type="PLAIN_AXES", radius=0.01)
        container = utils.get_active_object()
        container.name = "Lighting"
        utils.set_ccic_id(container)
    children = utils.get_child_objects(container)
    for child in children:
        if utils.has_ccic_id(child) and child.type == "LIGHT":
            utils.delete_object_tree(child)
    return container

