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
    print(f"RLX Code: {rlx_code}")
    if rlx_code == RLXCodes.RLX_ID_LIGHT:
        return import_rlx_light(data)
    return None


def import_rlx_light(data: BinaryData):
    light_data = data.json()
    # make the light
    print(light_data)
    link_id = light_data["link_id"]
    light = find_link_id(link_id)
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
    # now read in the frames and create an action for the light...
    frames = data.block()
    while not frames.eof():
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
        print(f"time: {time}, frame: {frame}")


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
    shape = "RECTANGLE" if is_rectangle else "TUBE" if is_tube else "NONE"

    if type == "DIR":
        light_type = "SUN"
    else:
        light_type = type
    if TUBE_AS_AREA and shape == "TUBE":
        light_type = "AREA"
    if RECTANGULAR_AS_AREA and shape == "RECTANGLE":
        light_type = "AREA"
    # area lights reproduce linear falloff (none inverse_square) lights best
    #if light_type == "SPOT" or light_type == "POINT":
    #    if (shape == "TUBE" or shape == "NONE") and not inverse_square:
    #        light_type = "AREA"

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
        light["link_id"] = link_id

    light.location = loc
    rot_mode = light.rotation_mode
    light.rotation_mode = "QUATERNION"
    light.rotation_quaternion = rot
    light.rotation_mode = rot_mode
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


def find_link_id(link_id: str):
    for obj in bpy.data.objects:
        if "link_id" in obj and obj["link_id"] == link_id:
            return obj
    return None


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

