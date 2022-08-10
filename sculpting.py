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

import os
import bpy
from . import nodeutils, modifiers, utils, vars


def setup_sculpt_bake_images(chr_cache, sculpt_body):
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    for mat in sculpt_body.data.materials:
        nodes = mat.node_tree.nodes

        # base the image name on the character name
        character_name = chr_cache.character_name
        image_name = f"{character_name}_{mat.name}_Sculpt_Bake_Normal"

        # find or create the bake image
        size = int(prefs.normal_bake_size)
        image = None
        if image_name in bpy.data.images:
            image = bpy.data.images[image_name]
            if image.size[0] != size or image.size[1] != size:
                bpy.data.images.remove(image)
                image = None

        if not image:
            image = bpy.data.images.new(image_name, size, size, alpha=False, is_data=True)

        # find or create the bake image node
        image_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", image_name)
        if not image_node:
            image_node = nodeutils.make_image_node(nodes, image, image_name)
        image_node.location = (1000, -1000)
        if image_node.image != image:
            image_node.image = image

        # make active so it uses this image to bake on
        nodes.active = image_node


def set_multi_res_level(chr_cache, level):
    sculpt_body = chr_cache.get_sculpt_body()
    if sculpt_body:
        mod : bpy.types.MultiresModifier
        mod = modifiers.get_object_modifier(sculpt_body, "MULTIRES", "Multi_Res_Sculpt")
        if mod:
            if level > mod.total_levels:
                level = mod.total_levels
            if level < 0:
                level = 0
            mod.levels = level
            mod.render_levels = level
            mod.sculpt_levels = level


def do_sculpt_bake(chr_cache, sculpt_body):
    bpy.context.scene.render.use_bake_multires = True
    bpy.context.scene.render.bake_type = 'NORMALS'
    if utils.is_blender_version("2.92.0"):
        bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'
    if utils.set_only_active_object(sculpt_body):
        set_multi_res_level(chr_cache, 0)
        bpy.ops.object.bake_image()
        set_multi_res_level(chr_cache, 9)


def save_skin_gen_bake(chr_cache, sculpt_body):
    base_dir = utils.local_path()
    if not base_dir:
        base_dir = chr_cache.import_dir

    skin_gen_dir = os.path.join(base_dir, "Skingen")
    os.makedirs(skin_gen_dir, exist_ok=True)

    character_name = chr_cache.character_name
    sculpt_body = chr_cache.get_sculpt_body()
    if sculpt_body:
        for mat in sculpt_body.data.materials:
            nodes = mat.node_tree.nodes

            image_name = f"{character_name}_{mat.name}_Sculpt_Bake_Normal"
            image_node = nodeutils.find_node_by_type_and_keywords(nodes, "TEX_IMAGE", image_name)
            image = None
            if image_node and image_node.image:
                image = image_node.image
            elif image_name in bpy.data.images:
                image = bpy.data.images[image]

            if image:
                image_file = image_name + ".png"
                image.file_format = "PNG"
                image_path = os.path.join(skin_gen_dir, image_file)
                print(image_path)
                try:
                    rel_path = bpy.path.relpath(image_path)
                except:
                    rel_path = image_path
                if image.filepath:
                    image.save()
                    image.reload()
                else:
                    image.filepath_raw = rel_path
                    image.save()
                    image.reload()



def apply_sculpt_bake_normal(chr_cache, sculpt_body, bake_target):
    return


def bake_sculpt(chr_cache, bake_target):
    sculpt_body = chr_cache.get_sculpt_body()
    # make sure to go into object mode otherwise the sculpt is not applied.
    if utils.object_mode_to(sculpt_body):
        setup_sculpt_bake_images(chr_cache, sculpt_body)
        do_sculpt_bake(chr_cache, sculpt_body)
        save_skin_gen_bake(chr_cache, sculpt_body)
        apply_sculpt_bake_normal(chr_cache, sculpt_body, bake_target)


def set_hide_character(chr_cache, hide):
    arm = chr_cache.get_armature()
    if utils.object_exists(arm):
        for child in arm.children:
            if utils.object_exists(child):
                child.hide_set(hide)
    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
        if utils.object_exists(obj):
            obj.hide_set(hide)
    arm.hide_set(hide)


def set_hide_sculpt_body(chr_cache, hide):
    sculpt_body = chr_cache.get_sculpt_body()
    if utils.object_exists_is_mesh(sculpt_body):
        sculpt_body.hide_set(hide)


def begin_sculpting(chr_cache):
    sculpt_body = chr_cache.get_sculpt_body()
    if utils.object_exists_is_mesh(sculpt_body):
        set_hide_character(chr_cache, True)
        set_hide_sculpt_body(chr_cache, False)
        utils.set_only_active_object(sculpt_body)
        utils.set_mode("SCULPT")
        bpy.context.space_data.shading.type = 'SOLID'
        bpy.context.space_data.shading.light = 'MATCAP'
        bpy.context.space_data.shading.studio_light = 'basic_1.exr'
        bpy.context.space_data.shading.show_cavity = True


def end_sculpting(chr_cache):
    body = chr_cache.get_body()
    set_hide_character(chr_cache, False)
    set_hide_sculpt_body(chr_cache, True)
    utils.set_only_active_object(body)
    utils.set_mode("OBJECT")
    bpy.context.space_data.shading.type = 'MATERIAL'


def clean_up_sculpt(chr_cache):
    end_sculpting(chr_cache)
    remove_sculpt_body(chr_cache)


def remove_sculpt_body(chr_cache):
    sculpt_body = chr_cache.get_sculpt_body()
    if utils.object_exists_is_mesh(sculpt_body):
        utils.delete_mesh_object(sculpt_body)
    chr_cache.sculpt_body = None


def add_sculpt_body(chr_cache, sculpt_target):

    # duplicate the body
    body = chr_cache.get_body()
    sculpt_body = utils.duplicate_object(body)

    # split the objects by material
    utils.clear_selected_objects()
    utils.edit_mode_to(sculpt_body)
    bpy.ops.mesh.separate(type='MATERIAL')
    objects = bpy.context.selected_objects.copy()
    rejoin = []

    # delete the material parts not wanted by the sculpt target
    for obj in objects:
        if len(obj.material_slots) > 0:
            mat = obj.material_slots[0].material
            mat_cache = chr_cache.get_material_cache(mat)
            remove = False

            # always remove eyelashes and nails
            if (mat_cache.material_type == "NAILS" or
                mat_cache.material_type == "EYELASH"):
                remove = True

            if sculpt_target == "BODY":
                # remove head
                if mat_cache.material_type == "SKIN_HEAD":
                    remove = True

            elif sculpt_target == "HEAD":
                # remove everything but head
                if mat_cache.material_type != "SKIN_HEAD":
                    remove = True

            if remove:
                utils.delete_mesh_object(obj)
            else:
                rejoin.append(obj)

    # rejoin the remaining objects
    utils.try_select_objects(rejoin, True)
    sculpt_body = rejoin[0]
    utils.set_active_object(sculpt_body)
    bpy.ops.object.join()

    if utils.set_only_active_object(sculpt_body):

        # remove doubles
        if utils.edit_mode_to(sculpt_body):
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()

        if utils.object_mode_to(sculpt_body):

            # remove all modifiers
            sculpt_body.modifiers.clear()

            # remove all shapekeys
            bpy.ops.object.shape_key_remove(all=True)

            # unparent and keep transform
            bpy.ops.object.parent_clear(type = "CLEAR_KEEP_TRANSFORM")

            # add multi-res modifier (3 subdivisions)
            modifiers.add_multi_res_modifier(sculpt_body, 4)

    # store the references
    chr_cache.sculpt_body = sculpt_body
    chr_cache.sculpt_target = sculpt_target

    return sculpt_body


def setup_sculpt(chr_cache):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    if chr_cache:

        sculpt_body = chr_cache.get_sculpt_body()
        sculpt_target = chr_cache.sculpt_target

        if sculpt_body and sculpt_target == prefs.sculpt_target:

            begin_sculpting(chr_cache)

        elif sculpt_body and sculpt_target != prefs.sculpt_target:

            remove_sculpt_body(chr_cache)
            sculpt_body = add_sculpt_body(chr_cache, prefs.sculpt_target)
            begin_sculpting(chr_cache)

        elif sculpt_body is None:

            sculpt_body = add_sculpt_body(chr_cache, prefs.sculpt_target)
            begin_sculpting(chr_cache)


class CC3OperatorSculpt(bpy.types.Operator):
    """Sculpt Functions"""
    bl_idname = "cc3.sculpting"
    bl_label = "Sculpting Functions"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):
        props = bpy.context.scene.CC3ImportProps
        prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

        chr_cache = props.get_context_character_cache(context)

        if self.param == "SETUP":
            setup_sculpt(chr_cache)

        elif self.param == "BEGIN":
            begin_sculpting(chr_cache)

        elif self.param == "END":
            end_sculpting(chr_cache)

        elif self.param == "BAKE":
            bake_sculpt(chr_cache, prefs.sculpt_bake_target)

        elif self.param == "CLEAN":
            clean_up_sculpt(chr_cache)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "":
            return ""

        return ""