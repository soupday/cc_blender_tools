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


def read_json(fbx_path, errors):
    json_file_exists = False
    try:
        fbx_file = os.path.basename(fbx_path)
        fbx_folder = os.path.dirname(fbx_path)
        fbx_name = os.path.splitext(fbx_file)[0]
        json_path = os.path.join(fbx_folder, fbx_name + ".json")
        # if the json doesn't exist in the expected path, look for it in the blend file path
        if not os.path.exists(json_path):
            json_path = utils.local_path(fbx_name + ".json")

        if json_path and os.path.exists(json_path):
            json_file_exists = True

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
        if errors:
            errors.append("NO_JSON")
        return None
    except:
        utils.log_warn("Failed to read Json data: " + json_path)
        if errors:
            if json_file_exists:
                errors.append("CORRUPT")
            else:
                errors.append("PATH_FAILED")
        return None


def write_json(json_data, path, is_fbx_path = False):
    if is_fbx_path:
        file = os.path.basename(path)
        folder = os.path.dirname(path)
        name = os.path.splitext(file)[0]
        path = os.path.join(folder, name + ".json")
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


def get_character_generation_json(chr_json, character_id):
    try:
        return chr_json[character_id]["Object"][character_id]["Generation"]
    except:
        utils.log_warn("Failed to read character generation data!")
        return None


def set_character_generation_json(chr_json, character_id, generation):
    try:
        chr_json[character_id]["Object"][character_id]["Generation"] = generation
        return True
    except:
        utils.log_warn(f"Failed to set character generation to: {generation}")
        return False


def get_character_root_json(json_data, character_id):
    if not json_data:
        return None
    try:
        return json_data[character_id]["Object"]
    except:
        utils.log_warn("Failed to get character root Json data!")
        return None

def get_character_json(json_data, character_id):
    if not json_data:
        return None
    try:
        chr_json = json_data[character_id]["Object"][character_id]
        utils.log_detail("Character Json data found for: " + character_id)
        return chr_json
    except:
        utils.log_warn("Failed to get character Json data!")
        return None


def get_facial_profile_json(json_data, character_id):
    try:
        return json_data[character_id]["Facial_Profile"]
    except:
        return None


def get_facial_profile_categories_json(json_data, character_id):
    try:
        return json_data[character_id]["Facial_Profile"]["Categories"]
    except:
        return None


def set_facial_profile_categories_json(json_data, character_id, categories_json):
    try:
        if "Facial_Profile" not in json_data[character_id].keys():
            json_data[character_id]["Facial_Profile"] = {}
        json_data[character_id]["Facial_Profile"]["Categories"] = categories_json
        return True
    except:
        return False


def get_object_json(chr_json, obj):
    if not chr_json:
        return None
    try:
        name = utils.strip_name(obj.name).lower()
        meshes_json = chr_json["Meshes"]
        for object_name in meshes_json.keys():
            if object_name.lower() == name:
                utils.log_detail("Object Json data found for: " + obj.name)
                return meshes_json[object_name]
    except:
        utils.log_warn("Failed to get object Json data!")
        return None


def get_physics_json(chr_json):
    try:
        return chr_json["Physics"]
    except:
        return None


def get_soft_physics_json(physics_json, obj, mat):
    try:
        obj_name = utils.strip_name(obj.name).lower()
        mat_name = utils.strip_name(mat.name).lower()
        soft_physics_mesh_json = physics_json["Soft Physics"]["Meshes"]
        for object_name in soft_physics_mesh_json:
            if object_name.lower() == obj_name:
                materials_json = soft_physics_mesh_json[object_name]["Materials"]
                for material_name in materials_json:
                    if material_name.lower() == mat_name:
                        return materials_json[material_name]
        return None
    except:
        utils.log_warn("Failed to get soft physics material Json data!")
        return None


def get_physics_mesh_json(physics_json, obj):
    if not physics_json:
        return None
    try:
        name = utils.strip_name(obj.name).lower()
        for object_name in physics_json.keys():
            if object_name.lower() == name:
                utils.log_detail("Physics Object Json data found for: " + obj.name)
                return physics_json[object_name]
    except:
        utils.log_warn("Failed to get physics object Json data!")
        return None


def get_custom_shader(mat_json):
    try:
        return mat_json["Custom Shader"]["Shader Name"]
    except:
        try:
            return mat_json["Material Type"]
        except:
            utils.log_warn("Failed to find material shader data!")
            return "Pbr"

def get_material_json(obj_json, material):
    if not obj_json:
        return None
    try:
        name = utils.strip_name(material.name).lower()
        materials_json = obj_json["Materials"]
        for material_name in materials_json.keys():
            if material_name.lower() == name:
                utils.log_detail("Material Json data found for: " + material.name)
                return materials_json[material_name]
    except:
        utils.log_warn("Failed to get material Json data!")
        return None

def get_physics_material_json(physics_mesh_json, material):
    if not physics_mesh_json:
        return None
    try:
        name = utils.strip_name(material.name).lower()
        materials_json = physics_mesh_json["Materials"]
        for material_name in materials_json.keys():
            if material_name.lower() == name:
                utils.log_detail("Physics Material Json data found for: " + material.name)
                return materials_json[material_name]
    except:
        utils.log_warn("Failed to get physics material Json data!")
        return None

def get_texture_info(mat_json, texture_id):
    tex_info = get_pbr_texture_info(mat_json, texture_id)
    if tex_info is None:
        tex_info = get_shader_texture_info(mat_json, texture_id)
    if tex_info is None:
        tex_info = get_wrinkle_texture_info(mat_json, texture_id)
    return tex_info

def get_texture_channel_strength(mat_json, texture_id, default_value=None):
    tex_info = get_texture_info(mat_json, texture_id)
    if tex_info and "Strength" in tex_info:
        return tex_info["Strength"] / 100
    return default_value

def get_pbr_texture_info(mat_json, texture_id):
    if not mat_json:
        return None
    try:
        return mat_json["Textures"][texture_id]
    except:
        return None

def get_shader_texture_info(mat_json, texture_id):
    if not mat_json:
        return None
    try:
        return mat_json["Custom Shader"]["Image"][texture_id]
    except:
        return None

def get_wrinkle_texture_info(mat_json, texture_id):
    if not mat_json:
        return None
    try:
        return mat_json["Wrinkle"]["Textures"][texture_id]
    except:
        return None

def get_material_json_var(mat_json, var_path: str):
    paths = var_path.split('/')
    var_type = paths[0]
    var_name = paths[1]
    if var_type == "Custom":
        return get_shader_var(mat_json, var_name)
    elif var_type == "SSS":
        return get_sss_var(mat_json, var_name)
    elif var_type == "Pbr":
        return get_pbr_var(mat_json, var_name, paths)
    else: # var_type == "Base":
        return get_material_var(mat_json, var_name)


def get_shader_var(mat_json, var_name):
    if not mat_json:
        return None
    try:
        return mat_json["Custom Shader"]["Variable"][var_name]
    except:
        return None

def get_pbr_var(mat_json, var_name, paths):
    if not mat_json:
        return None
    try:
        if len(paths) == 3:
            return mat_json["Textures"][var_name][paths[2]]
        else:
            return mat_json["Textures"][var_name]["Strength"] / 100.0
    except:
        return None

def get_material_var(mat_json, var_name):
    if not mat_json:
        return None
    try:
        return mat_json[var_name]
    except:
        return None

def get_sss_var(mat_json, var_name):
    if not mat_json:
        return None
    try:
        return mat_json["Subsurface Scatter"][var_name]
    except:
        return None


def set_material_json_var(mat_json, var_path: str, value):
    paths = var_path.split('/')
    var_type = paths[0]
    var_name = paths[1]
    if var_type == "Custom":
        set_shader_var(mat_json, var_name, value)
    elif var_type == "SSS":
        set_sss_var(mat_json, var_name, value)
    elif var_type == "Pbr":
        set_pbr_var(mat_json, var_name, paths, value)
    else: # var_type == "Base":
        set_material_var(mat_json, var_name, value)


def set_shader_var(mat_json, var_name, value):
    if mat_json:
        try:
            mat_json["Custom Shader"]["Variable"][var_name] = value
        except:
            return

def set_pbr_var(mat_json, var_name, paths, value):
    if mat_json:
        try:
            if len(paths) == 3:
                mat_json["Textures"][var_name][paths[2]] = value
            else:
                # metallic and roughness don't have controllable strength settings, so always set to max
                if var_name == "Metallic" or var_name != "Roughness":
                    value = 1.0
                mat_json["Textures"][var_name]["Strength"] = value * 100.0
        except:
            return

def set_material_var(mat_json, var_name, value):
    if mat_json:
        try:
            mat_json[var_name] = value
        except:
            return

def set_sss_var(mat_json, var_name, value):
    if mat_json:
        try:
            mat_json["Subsurface Scatter"][var_name] = value
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


def get_shader_var_color(mat_json, var_name):
    if not mat_json:
        return None
    try:
        json_color = mat_json["Custom Shader"]["Variable"][var_name]
        return convert_to_color(json_color)
    except:
        return None


def get_json(json_data, path: str):
    if json_data:
        keys = path.split("/")
        for key in keys:
            if key in json_data:
                json_data = json_data[key]
            else:
                return None
        return json_data
    return None


def set_json(json_data, path: str, value):
    if json_data:
        json_key = None
        keys = path.split("/")
        for i, key in enumerate(keys):
            if key in json_data:
                if i == len(keys) - 1:
                    json_data[key] = value
                    return True
                else:
                    json_data = json_data[key]
            else:
                break
    return False


def generate_character_json_data(name):
    json_data = {
        name: {
            "Version": "1.10.1822.1",
            "Scene": {
                "Name": True,
                "SupportShaderSelect": True
            },
            "Object": {
                name: {
                    "Generation": "",
                    "Meshes": {
                    },
                },
            },
        }
    }
    return json_data


def add_json_path(json_data, path):
    keys = path.split("/")
    for key in keys:
        if key not in json_data.keys():
            json_data[key] = {}
        json_data = json_data[key]
    return json_data


def rename_json_key(json_data, old_name, new_name):
    if old_name in json_data.keys():
        json_data[new_name] = json_data.pop(old_name)
        return True
    return False


