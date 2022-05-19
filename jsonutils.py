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

import json
import os
import bpy

from . import utils


def read_json(fbx_path):
    try:
        fbx_file = os.path.basename(fbx_path)
        fbx_folder = os.path.dirname(fbx_path)
        fbx_name = os.path.splitext(fbx_file)[0]
        json_path = os.path.join(fbx_folder, fbx_name + ".json")
        # if the json doesn't exist in the expected path, look for it in the blend file path
        if not os.path.exists(json_path):
            json_path = utils.local_path(fbx_name + ".json")

        if os.path.exists(json_path):

            # determine start of json text data
            file_bytes = open(json_path, "rb")
            bytes = file_bytes.read(3)
            file_bytes.close()
            start = 0
            # json files outputted from Visual Studio projects start with a byte mark order block (3 bytes EF BB BF)
            if bytes[0] == 0xEF and bytes[1] == 0xBB and bytes[2] == 0xBF:
                start = 3

            # read json text
            file = open(json_path, "rt")
            file.seek(start)
            text_data = file.read()
            json_data = json.loads(text_data)
            file.close()
            utils.log_info("Json data successfully parsed: " + json_path)
            return json_data

        utils.log_info("No Json data to parse, using defaults...")
        return None
    except:
        utils.log_warn("Failed to read Json data: " + json_path)
        return None


def write_json(json_data, path):
    json_object = json.dumps(json_data, indent = 4)
    with open(path, "w") as write_file:
        write_file.write(json_object)


def get_all_object_keys(chr_json):
    if chr_json:
        meshes_json = chr_json["Meshes"]
        return meshes_json.keys()
    return []


def get_all_material_keys(chr_json):
    if chr_json:
        keys = []
        meshes_json = chr_json["Meshes"]
        for obj_json_name in meshes_json.keys():
            obj_json = meshes_json[obj_json_name]
            materials_json = obj_json["Materials"]
            for mat_key in materials_json.keys():
                keys.append(mat_key)
        return keys


def get_character_generation_json(character_json, file_name, character_id):
    try:
        return character_json[file_name]["Object"][character_id]["Generation"]
    except:
        utils.log_warn("Failed to read character generation data!")
        return None


def get_character_root_json(json_data, file_name):
    if not json_data:
        return None
    try:
        return json_data[file_name]["Object"]
    except:
        utils.log_warn("Failed to get character root Json data!")
        return None

def get_character_json(json_data, file_name, character_id):
    if not json_data:
        return None
    try:
        character_json = json_data[file_name]["Object"][character_id]
        utils.log_detail("Character Json data found for: " + character_id)
        return character_json
    except:
        utils.log_warn("Failed to get character Json data!")
        return None

def get_object_json(character_json, obj):
    if not character_json:
        return None
    try:
        name = utils.strip_name(obj.name).lower()
        meshes_json = character_json["Meshes"]
        for object_name in meshes_json.keys():
            if object_name.lower() == name:
                utils.log_detail("Object Json data found for: " + obj.name)
                return meshes_json[object_name]
    except:
        utils.log_warn("Failed to get object Json data!")
        return None

def get_custom_shader(material_json):
    try:
        return material_json["Custom Shader"]["Shader Name"]
    except:
        try:
            return material_json["Material Type"]
        except:
            utils.log_warn("Failed to find material shader data!")
            return "Pbr"

def get_material_json(object_json, material):
    if not object_json:
        return None
    try:
        name = utils.strip_name(material.name).lower()
        materials_json = object_json["Materials"]
        for material_name in materials_json.keys():
            if material_name.lower() == name:
                utils.log_detail("Material Json data found for: " + material.name)
                return materials_json[material_name]
    except:
        utils.log_warn("Failed to get material Json data!")
        return None

def get_texture_info(material_json, texture_id):
    tex_info = get_pbr_texture_info(material_json, texture_id)
    if tex_info is None:
        tex_info = get_shader_texture_info(material_json, texture_id)
    return tex_info

def get_pbr_texture_info(material_json, texture_id):
    if not material_json:
        return None
    try:
        return material_json["Textures"][texture_id]
    except:
        return None

def get_shader_texture_info(material_json, texture_id):
    if not material_json:
        return None
    try:
        return material_json["Custom Shader"]["Image"][texture_id]
    except:
        return None

def get_material_json_var(material_json, var_path: str):
    var_type, var_name = var_path.split('/')
    if var_type == "Custom":
        return get_shader_var(material_json, var_name)
    elif var_type == "SSS":
        return get_sss_var(material_json, var_name)
    elif var_type == "Pbr":
        return get_pbr_var(material_json, var_name)
    else: # var_type == "Base":
        return get_material_var(material_json, var_name)


def get_shader_var(material_json, var_name):
    if not material_json:
        return None
    try:
        return material_json["Custom Shader"]["Variable"][var_name]
    except:
        return None

def get_pbr_var(material_json, var_name):
    if not material_json:
        return None
    try:
        return material_json["Textures"][var_name]["Strength"] / 100.0
    except:
        return None

def get_material_var(material_json, var_name):
    if not material_json:
        return None
    try:
        return material_json[var_name]
    except:
        return None

def get_sss_var(material_json, var_name):
    if not material_json:
        return None
    try:
        return material_json["Subsurface Scatter"][var_name]
    except:
        return None


def set_material_json_var(material_json, var_path: str, value):
    var_type, var_name = var_path.split('/')
    if var_type == "Custom":
        set_shader_var(material_json, var_name, value)
    elif var_type == "SSS":
        set_sss_var(material_json, var_name, value)
    elif var_type == "Pbr":
        set_pbr_var(material_json, var_name, value)
    else: # var_type == "Base":
        set_material_var(material_json, var_name, value)


def set_shader_var(material_json, var_name, value):
    if material_json:
        try:
            material_json["Custom Shader"]["Variable"][var_name] = value
        except:
            return

def set_pbr_var(material_json, var_name, value):
    if material_json:
        try:
            material_json["Textures"][var_name]["Strength"] = value * 100.0
        except:
            return

def set_material_var(material_json, var_name, value):
    if material_json:
        try:
            material_json[var_name] = value
        except:
            return

def set_sss_var(material_json, var_name, value):
    if material_json:
        try:
            material_json["Subsurface Scatter"][var_name] = value
        except:
            return


def convert_to_color(json_var):
    if type(json_var) == list:
        for i in range(0, len(json_var)):
            json_var[i] /= 255.0
        if len(json_var) == 3:
            json_var.append(1)
    return json_var


def convert_from_color(color):
    try:
        return [ int(color[0] * 255.0), int(color[1] * 255.0), int(color[2] * 255.0) ]
    except:
        return [255,255,255]


def get_shader_var_color(material_json, var_name):
    if not material_json:
        return None
    try:
        json_color = material_json["Custom Shader"]["Variable"][var_name]
        return convert_to_color(json_color)
    except:
        return None

