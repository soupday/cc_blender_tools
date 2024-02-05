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

import math
import os
import time

import bpy

from . import colorspace, imageutils, nodeutils, rigidbody, physics, modifiers, utils, vars


def add_target(name, location):
    bpy.ops.object.empty_add(type="PLAIN_AXES", radius = 0.1,
        location = location)
    target = bpy.context.active_object
    target.name = utils.unique_name(name, True)
    return target

def set_contact_shadow(light, distance, thickness):
    light.data.use_contact_shadow = True
    light.data.contact_shadow_distance = distance
    light.data.contact_shadow_thickness = thickness

def track_to(obj, target):
    constraint = obj.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"


def add_light_container():
    bpy.ops.object.empty_add(type="PLAIN_AXES", radius=0.01)
    container = bpy.context.active_object
    container.name = utils.unique_name("Lighting", True)
    return container


def add_sun_light(name, container, location, rotation, energy, angle):
    bpy.ops.object.light_add(type="SUN",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = utils.unique_name(name, True)
    light.data.energy = energy
    light.data.angle = angle
    if container:
        light.parent = container
        light.matrix_parent_inverse = container.matrix_world.inverted()
    return light


def add_spot_light(name, container, location, rotation, energy, blend, size, distance, radius):
    bpy.ops.object.light_add(type="SPOT",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = utils.unique_name(name, True)
    light.data.energy = energy
    light.data.shadow_soft_size = radius
    light.data.spot_blend = blend
    light.data.spot_size = size
    light.data.use_custom_distance = True
    light.data.cutoff_distance = distance
    if container:
        light.parent = container
        light.matrix_parent_inverse = container.matrix_world.inverted()
    return light


def add_area_light(name, container, location, rotation, energy, size, distance):
    bpy.ops.object.light_add(type="AREA",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = utils.unique_name(name, True)
    light.data.shape = "DISK"
    light.data.size = size
    light.data.energy = energy
    light.data.use_custom_distance = True
    light.data.cutoff_distance = distance
    if container:
        light.parent = container
        light.matrix_parent_inverse = container.matrix_world.inverted()
    return light


def add_point_light(name, container, location, rotation, energy, size):
    bpy.ops.object.light_add(type="POINT",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = utils.unique_name(name, True)
    light.data.shadow_soft_size = size
    light.data.energy = energy
    if container:
        light.parent = container
        light.matrix_parent_inverse = container.matrix_world.inverted()
    return light


def remove_all_lights(inc_camera = False):
    for obj in bpy.data.objects:
        if vars.NODE_PREFIX in obj.name:

            if obj.type == "LIGHT":
                bpy.data.objects.remove(obj)

            elif inc_camera and obj.type == "EMPTY" and "CameraTarget" in obj.name:
                bpy.data.objects.remove(obj)

            elif obj.type == "EMPTY" and \
                ("KeyTarget" in obj.name or \
                "FillTarget" in obj.name or \
                "BackTarget" in obj.name or \
                "Lighting" in obj.name):
                bpy.data.objects.remove(obj)

            elif inc_camera and obj.type == "CAMERA":
                bpy.data.objects.remove(obj)
        else:
            if obj.type == "LIGHT":
                obj.hide_set(True)

            elif inc_camera and obj.type == "EMPTY" and "CameraTarget" in obj.name:
                obj.hide_set(True)

            elif obj.type == "EMPTY" and \
                ("KeyTarget" in obj.name or \
                "FillTarget" in obj.name or \
                "BackTarget" in obj.name):
                obj.hide_set(True)

            elif inc_camera and obj.type == "CAMERA":
                obj.hide_set(True)


def restore_hidden_camera():
    # enable the first hidden camera
    for obj in bpy.data.objects:
        if obj.type == "CAMERA" and not obj.visible_get():
            obj.hide_set(False)
            bpy.context.scene.camera = obj
            return


def camera_setup(camera_loc, target_loc):
    # find an active camera
    camera = None
    target = None
    for obj in bpy.data.objects:
        if camera is None and vars.NODE_PREFIX in obj.name and obj.type == "CAMERA" and obj.visible_get():
            camera = obj
            camera.location = camera_loc
        if target is None and vars.NODE_PREFIX in obj.name and obj.type == "EMPTY" and obj.visible_get() and "CameraTarget" in obj.name:
            target = obj
            target.location = target_loc
    if camera is None:
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=camera_loc)
        camera = bpy.context.active_object
        camera.name = utils.unique_name("Camera", True)
    if target is None:
        target = add_target("CameraTarget", target_loc)

    track_to(camera, target)
    camera.data.lens = 80
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = target
    camera.data.dof.aperture_fstop = 2.8
    camera.data.dof.aperture_blades = 5
    camera.data.dof.aperture_rotation = 0
    camera.data.dof.aperture_ratio = 1
    camera.data.display_size = 0.2
    camera.data.show_limits = True

    camera_auto_target(camera, target)

    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 2560
    bpy.context.scene.render.resolution_percentage = 100

    return camera, target

def camera_auto_target(camera, target):
    props = bpy.context.scene.CC3ImportProps

    chr_cache = props.get_context_character_cache()
    if chr_cache is None:
        chr_cache = props.get_character_cache(bpy.context.active_object, None)
    if chr_cache is None:
        chr_cache = props.import_cache[0]

    arm = chr_cache.get_armature()
    if arm:
        left_eye = utils.find_pose_bone(chr_cache, "CC_Base_L_Eye", "L_Eye")
        right_eye = utils.find_pose_bone(chr_cache, "CC_Base_R_Eye", "R_Eye")
        head = utils.find_pose_bone(chr_cache, "CC_Base_FacialBone", "FacialBone")

        if left_eye is None or right_eye is None or head is None:
            return

        head_location = arm.matrix_world @ head.head
        head_dir = (arm.matrix_world @ head.vector).normalized()
        target_location = arm.matrix_world @ ((left_eye.head + right_eye.head) * 0.5)
        target.location = target_location + head_dir * 0.03
        camera.location = head_location + head_dir * 2

def compositor_setup():
    bpy.context.scene.use_nodes = True
    nodes = bpy.context.scene.node_tree.nodes
    links = bpy.context.scene.node_tree.links
    nodes.clear()
    rlayers_node = nodeutils.make_shader_node(nodes, "CompositorNodeRLayers")
    c_node = nodeutils.make_shader_node(nodes, "CompositorNodeComposite")
    glare_node = nodeutils.make_shader_node(nodes, "CompositorNodeGlare")
    lens_node = nodeutils.make_shader_node(nodes, "CompositorNodeLensdist")
    rlayers_node.location = (-780,260)
    c_node.location = (150,140)
    glare_node.location = (-430,230)
    lens_node.location = (-100,150)
    glare_node.glare_type = 'FOG_GLOW'
    glare_node.quality = 'HIGH'
    glare_node.threshold = 0.85
    lens_node.use_fit = True
    nodeutils.set_node_input_value(lens_node, "Dispersion", 0.025)
    nodeutils.link_nodes(links, rlayers_node, "Image", glare_node, "Image")
    nodeutils.link_nodes(links, glare_node, "Image", lens_node, "Image")
    nodeutils.link_nodes(links, lens_node, "Image", c_node, "Image")

def world_setup():
    bpy.context.scene.world.use_nodes = True
    nodes = bpy.context.scene.world.node_tree.nodes
    links = bpy.context.scene.world.node_tree.links
    nodes.clear()
    tc_node = nodeutils.make_shader_node(nodes, "ShaderNodeTexCoord")
    mp_node = nodeutils.make_shader_node(nodes, "ShaderNodeMapping")
    et_node = nodeutils.make_shader_node(nodes, "ShaderNodeTexEnvironment")
    bg_node = nodeutils.make_shader_node(nodes, "ShaderNodeBackground")
    wo_node = nodeutils.make_shader_node(nodes, "ShaderNodeOutputWorld")
    tc_node.location = (-820,350)
    mp_node.location = (-610,370)
    et_node.location = (-300,320)
    bg_node.location = (10,300)
    wo_node.location = (300,300)
    nodeutils.set_node_input_value(bg_node, "Strength", 0.5)
    nodeutils.link_nodes(links, tc_node, "Generated", mp_node, "Vector")
    nodeutils.link_nodes(links, mp_node, "Vector", et_node, "Vector")
    nodeutils.link_nodes(links, et_node, "Color", bg_node, "Color")
    nodeutils.link_nodes(links, bg_node, "Background", wo_node, "Surface")
    bin_dir, bin_file = os.path.split(bpy.app.binary_path)
    version = bpy.app.version_string[:4]
    hdri_path = os.path.join(bin_dir, version, "datafiles", "studiolights", "world", "forest.exr")
    et_node.image = imageutils.load_image(hdri_path, "Linear")


def setup_scene_default(scene_type):
    props = bpy.context.scene.CC3ImportProps
    prefs = bpy.context.preferences.addons[__name__.partition(".")[0]].preferences

    # store selection and mode
    current_selected = bpy.context.selected_objects
    current_active = bpy.context.active_object
    current_mode = bpy.context.mode
    # go to object mode
    try:
        if current_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        if scene_type == "BLENDER":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.2
            bpy.context.scene.eevee.gtao_factor = 1.0
            bpy.context.scene.eevee.use_bloom = False
            bpy.context.scene.eevee.bloom_threshold = 0.8
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 6.5
            bpy.context.scene.eevee.bloom_intensity = 0.05
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            colorspace.set_view_settings("Filmic", "None", 0.0, 1.0)
            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            restore_hidden_camera()

            key1 = add_point_light("Light", None,
                    (4.076245307922363, 1.0054539442062378, 5.903861999511719),
                    (0.6503279805183411, 0.055217113345861435, 1.8663908243179321),
                    1000, 0.1)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'forest.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 0
            bpy.context.space_data.shading.studiolight_intensity = 1
            bpy.context.space_data.shading.studiolight_background_alpha = 0
            bpy.context.space_data.shading.studiolight_background_blur = 0
            bpy.context.space_data.clip_start = 0.1

        elif scene_type == "MATCAP":

            remove_all_lights(True)
            restore_hidden_camera()

            bpy.context.space_data.shading.type = 'SOLID'
            bpy.context.space_data.shading.light = 'MATCAP'
            bpy.context.space_data.shading.studio_light = 'basic_1.exr'
            bpy.context.space_data.shading.show_cavity = True

        elif scene_type == "CC3":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 2.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            colorspace.set_view_settings("Filmic", "Medium Contrast", 0.5, 0.5)

            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50

            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            strength = 50

            key1 = add_spot_light("Key1", container,
                    (0.71149, -1.49019, 2.04134),
                    (1.2280241250991821, 0.4846124053001404, 0.3449903726577759),
                    2.5 * strength, 0.5, 2.095, 9.7, 0.225)

            key2 = add_spot_light("Key2", container,
                    (0.63999, -1.3600, 0.1199),
                    (1.8845493793487549, 0.50091552734375, 0.6768553256988525),
                    2.5 * strength, 0.5, 2.095, 9.7, 1.0)

            back = add_spot_light("Back", container,
                    (0.0, 2.0199, 1.69),
                    (-1.3045594692230225, 0.11467886716127396, 0.03684665635228157),
                    3 * strength, 0.5, 1.448, 9.14, 1.0)
            back.data.color = utils.linear_to_srgb([213.0/155.0, 150.0/255.0, 120.0/255.0, 1.0])[0:3]

            set_contact_shadow(key1, 0.05, 0.0025)

            bpy.context.space_data.shading.type = 'SOLID'
            bpy.context.space_data.shading.light = 'MATCAP'
            bpy.context.space_data.shading.studio_light = 'basic_1.exr'
            bpy.context.space_data.shading.show_cavity = True
            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'studio.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = -0.349066
            bpy.context.space_data.shading.studiolight_intensity = 0.6
            bpy.context.space_data.shading.studiolight_background_alpha = 0
            bpy.context.space_data.shading.studiolight_background_blur = 0
            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "STUDIO":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 2.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            colorspace.set_view_settings("Filmic", "High Contrast", 0.5, 1.0)
            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            key = add_spot_light("Key", container,
                    (0.3088499903678894, -4.569439888000488, 2.574970006942749),
                    (0.39095374941825867, 1.3875367641448975, -1.1152653694152832),
                    400, 0.75, 0.75, 7.5, 0.4)

            right = add_area_light("Right", container,
                    (2.067525863647461, 0.8794340491294861, 1.1529420614242554),
                    (3.115412712097168, 1.7226399183273315, 9.79827880859375),
                    50, 2, 9)

            back = add_spot_light("Ear", container,
                    (0.6740000247955322, 1.906999945640564, 1.6950000524520874),
                    (-0.03316125646233559, 1.3578661680221558, 1.1833332777023315),
                    100, 1, 1.0996, 9.1, 0.5)

            set_contact_shadow(key, 0.05, 0.0025)
            set_contact_shadow(right, 0.05, 0.0025)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'studio.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 0.0
            bpy.context.space_data.shading.studiolight_intensity = 0.2
            bpy.context.space_data.shading.studiolight_background_alpha = 0.1
            bpy.context.space_data.shading.studiolight_background_blur = 0.5
            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "COURTYARD":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 2.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            colorspace.set_view_settings("Filmic", "Medium High Contrast", 0.5, 0.6)
            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            key = add_area_light("Key", container,
                    (-1.5078026056289673, -1.0891118049621582, 2.208820104598999),
                    (1.0848181247711182, -0.881056010723114, -0.5597077012062073),
                    40, 2, 9)

            fill = add_area_light("Fill", container,
                    (2.28589, -1.51410, 1.40742),
                    (1.4248263835906982, 0.9756063222885132, 0.8594209551811218),
                    20, 2, 9)

            back = add_area_light("Back", container,
                    (0.36789, 0.61511, 2.36201),
                    (-0.7961875796318054, 0.4831638038158417, -0.12343151122331619),
                    20, 1, 9)

            set_contact_shadow(key, 0.05, 0.0025)
            set_contact_shadow(fill, 0.05, 0.0025)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'courtyard.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 2.00713
            bpy.context.space_data.shading.studiolight_intensity = 0.35
            bpy.context.space_data.shading.studiolight_background_alpha = 0.05
            bpy.context.space_data.shading.studiolight_background_blur = 0.5

            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "AQUA":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 2.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            colorspace.set_view_settings("Filmic", "Medium High Contrast", 0.5, 0.6)
            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            key1 = add_area_light("Key", container,
                    (-0.6483273506164551, -2.073286771774292, 0.9459081292152405),
                    (1.8756767511367798, -0.6675444841384888, -0.49660807847976685),
                    40, 0.5, 9)

            back1 = add_area_light("Back", container,
                    (-1.1216378211975098, 1.4875532388687134, 1.6059372425079346),
                    (-1.4973092079162598, -0.07008785009384155, 0.6377549767494202),
                    40, 1, 9)

            back2 = add_area_light("Back", container,
                    (-1.9412485361099243, -0.5231357216835022, 1.8983763456344604),
                    (1.278488278388977, 0.6497069001197815, -1.6310228109359741),
                    60, 1, 9)

            set_contact_shadow(key1, 0.05, 0.0025)
            set_contact_shadow(back2, 0.05, 0.0025)
            key1.data.color = (0.8999999761581421, 1.0, 0.9494728446006775)
            back1.data.color = (0.6919613480567932, 0.9645320177078247, 1.0)
            back2.data.color = (0.6919613480567932, 0.9645320177078247, 1.0)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'studio.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 2.443461
            bpy.context.space_data.shading.studiolight_intensity = 0.35
            bpy.context.space_data.shading.studiolight_background_alpha = 0.05
            bpy.context.space_data.shading.studiolight_background_blur = 0.5

            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "AUTHORITY":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 2.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            colorspace.set_view_settings("Filmic", "Medium High Contrast", 0.5, 0.6)
            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50

            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            back = add_spot_light('Back', container,
                                  (-0.005357889924198389, 2.0200612545013428, 1.695375919342041),
                                  (-0.03276786953210831, 1.3572242259979248, 1.548905849456787),
                                  250.0, 1.0, 1.4486232995986938, 9.149999618530273, 0.5)
            set_contact_shadow(back, 0.1, 0.005)
            back.data.color = (0.6653872728347778, 0.3049870431423187, 0.18782085180282593)

            fill = add_spot_light('Fill', container,
                                  (1.0739537477493286, 0.6725472807884216, 0.593166172504425),
                                  (2.765416145324707, -0.7434117197990417, 0.9113498330116272),
                                  50.29999923706055, 1.0, 2.460914134979248, 40.0, 0.20000000298023224)
            #set_contact_shadow(fill, 0.05, 0.0025)
            fill.data.color = (0.2195257842540741, 0.2961380183696747, 0.35153260827064514)

            #key = add_spot_light('Key', container,
            #                     (-3.1819117069244385, 2.877981185913086, 3.6740193367004395),
            #                     (-0.038421738892793655, 1.0002018213272095, 2.6068308353424072),
            #                     500.0, 1.0, 0.7504915595054626, 9.640000343322754, 0.5)
            #set_contact_shadow(key, 0.05, 0.0025)
            #key.data.color = (1.0, 1.0, 1.0)

            key_0 = add_spot_light('Key_0', container,
                                   (-0.8539601564407349, -1.410485863685608, 2.5526487827301025),
                                   (0.00185012212023139, -1.2320791482925415, 0.9582659006118774),
                                   350.0, 1.0, 1.4486232995986938, 9.149999618530273, 0.4000000059604645)
            set_contact_shadow(key_0, 0.05, 0.0025)
            key_0.data.color = (0.6321180462837219, 0.6601223349571228, 0.6653874516487122)

            key_front = add_spot_light('Key_Front', container,
                                       (1.2850462198257446, 4.022171497344971, 3.350560188293457),
                                       (-0.34832963347435, 1.1461026668548584, 0.8322783708572388),
                                       400.0, 1.0, 0.7504915595054626, 9.640000343322754, 0.6200000047683716)
            #set_contact_shadow(key_front, 0.05, 0.0025)
            key_front.data.color = (1.0, 1.0, 1.0)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'studio.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = -45 * 0.01745329
            bpy.context.space_data.shading.studiolight_intensity = 0.35
            bpy.context.space_data.shading.studiolight_background_alpha = 0.05
            bpy.context.space_data.shading.studiolight_background_blur = 0.5

            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "BLUR_WARM":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.35
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 4.0
            bpy.context.scene.eevee.bloom_intensity = 0.15
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            colorspace.set_view_settings("Filmic", "Medium High Contrast", 0.75, 0.6)
            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50

            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            dir__light_closeup = add_area_light('Closeup', container,
                                                (0.5158149600028992, -2.368131399154663, 2.423656702041626),
                                                (0.7853980660438538, -5.3335220684402884e-08, 0.2144654393196106),
                                                40.0, 0.5, 9.0)
            set_contact_shadow(dir__light_closeup, 0.05, 0.0025)
            dir__light_closeup.data.color = (1.0, 0.875, 0.929)

            #face = add_spot_light('Face', container,
            #                      (0.3906535804271698, -1.662192463874817, 1.5247554779052734),
            #                      (1.354565978050232, 1.4951248168945312, -0.08803682774305344),
            #                      20.0, 1.0, 1.9373154640197754, 40.0, 0.4000000059604645)
            #set_contact_shadow(face, 0.05, 0.0025)
            #face.data.color = (0.4910203516483307, 0.4400765895843506, 0.42536425590515137)

            key = add_spot_light('Key', container,
                                 (0.27087676525115967, -1.4420602321624756, 1.8877607583999634),
                                 (0.06910622119903564, 1.289427638053894, -1.2891168594360352),
                                 60.0, 1.0, 1.7104226350784302, 973.0, 0.25)
            set_contact_shadow(key, 0.05, 0.0025)
            key.data.color = (1.0, 0.875, 0.929)

            #key_light___up = add_spot_light('Key_Up', container,
            #                                (0.08597123622894287, -1.169071912765503, 1.087883710861206),
            #                                (0.21799443662166595, 1.0667731761932373, -1.5876233577728271),
            #                                20.0, 1.0, 2.094395160675049, 9.0, 0.5)
            #set_contact_shadow(key_light___up, 0.05, 0.0025)
            #key_light___up.data.color = (0.6514051556587219, 0.6514051556587219, 0.6514051556587219)

            #rim_red = add_spot_light('Rim_Red', container,
            #                         (0.12474790960550308, 0.8755945563316345, 1.634949803352356),
            #                         (-0.018602706491947174, 1.3557215929031372, 1.3706303834915161),
            #                         60.0, 1.0, 2.6179938316345215, 2.0, 0.20000000298023224)
            #set_contact_shadow(rim_red, 0.05, 0.0025)
            #rim_red.data.color = (0.4910208284854889, 0.2579752206802368, 0.24017876386642456)

            rim_yellow = add_spot_light('Rim_Yellow', container,
                                        (0.315, 0.875, 1.634),
                                        (-0.019, 1.355, 1.370),
                                        65.0, 1.0, 2.617, 9.0, 0.100)
            #set_contact_shadow(rim_yellow, 0.05, 0.0025)
            rim_yellow.data.color = (1.0, 0.647, 0.519)

            dir__light = add_sun_light('Dir', container,
                                       (0.0, 0.0, 0.0),
                                       (0.7853981852531433, 3.429620676342893e-08, 2.937906503677368),
                                       4.5, 0.009250245057046413)
            set_contact_shadow(dir__light, 0.1, 0.05)
            dir__light.data.color = (0.4910205900669098, 0.349460631608963, 0.3006436228752136)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'courtyard.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = -60 * 0.01745329
            bpy.context.space_data.shading.studiolight_intensity = 0.1
            bpy.context.space_data.shading.studiolight_background_alpha = 0.05
            bpy.context.space_data.shading.studiolight_background_blur = 0.5

            bpy.context.space_data.clip_start = 0.01

        elif scene_type == "TEMPLATE":

            bpy.context.scene.eevee.use_gtao = True
            bpy.context.scene.eevee.gtao_distance = 0.25
            bpy.context.scene.eevee.gtao_factor = 0.5
            bpy.context.scene.eevee.use_bloom = True
            bpy.context.scene.eevee.bloom_threshold = 0.5
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 5.0
            bpy.context.scene.eevee.bloom_intensity = 0.1
            bpy.context.scene.eevee.use_ssr = True
            bpy.context.scene.eevee.use_ssr_refraction = True
            bpy.context.scene.eevee.bokeh_max_size = 32
            colorspace.set_view_settings("Filmic", "Medium High Contrast", 0.6, 0.6)
            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            camera, camera_target = camera_setup((0.1, -0.75, 1.6), (0, 0, 1.5))
            bpy.context.scene.camera = camera

            key = add_area_light("Key",
                    (-1.5078026056289673, -1.0891118049621582, 2.208820104598999),
                    (1.0848181247711182, -0.881056010723114, -0.5597077012062073),
                    40, 1, 9)
            target_key = add_target("KeyTarget", (-0.006276353262364864, -0.004782751202583313, 1.503425121307373))
            track_to(key, target_key)

            fill = add_area_light("Fill",
                    (2.28589, -1.51410, 1.40742),
                    (1.4248263835906982, 0.9756063222885132, 0.8594209551811218),
                    10, 1, 9)
            target_fill = add_target("FillTarget", (0.013503191992640495, 0.005856933072209358, 1.1814184188842773))
            track_to(fill, target_fill)

            back = add_area_light("Back",
                    (0.36789, 0.61511, 2.36201),
                    (-0.7961875796318054, 0.4831638038158417, -0.12343151122331619),
                    40, 0.5, 9)
            target_back = add_target("BackTarget", (0.0032256320118904114, 0.06994983553886414, 1.6254671812057495))
            track_to(back, target_back)

            set_contact_shadow(key, 0.05, 0.0025)
            set_contact_shadow(fill, 0.05, 0.0025)

            bpy.context.space_data.shading.type = 'RENDERED'
            bpy.context.space_data.shading.use_scene_lights_render = True
            bpy.context.space_data.shading.use_scene_world_render = True

            bpy.context.space_data.clip_start = 0.01

    except Exception as e:
        utils.log_error("Something went wrong adding lights...", e)

    # restore selection
    bpy.ops.object.select_all(action='DESELECT')
    for obj in current_selected:
        try:
            obj.select_set(True)
        except:
            pass
    try:
        bpy.context.view_layer.objects.active = current_active
        if current_mode != "OBJECT":
            bpy.ops.object.mode_set(mode=current_mode)
    except:
        pass

# zoom view to imported character
def zoom_to_character(chr_cache):
    props = bpy.context.scene.CC3ImportProps
    try:
        bpy.ops.object.select_all(action='DESELECT')
        for obj_cache in chr_cache.object_cache:
            obj = obj_cache.get_object()
            if obj:
                obj.select_set(True)
        bpy.ops.view3d.view_selected()
    except:
        pass


def active_select_body(chr_cache):
    for obj_cache in chr_cache.object_cache:
        if obj_cache.is_mesh():
            obj = obj_cache.get_object()
            if obj_cache.object_type == "BODY":
                utils.set_active_object(obj)


def render_image(context):
    # TBD
    pass


def render_animation(context):
    # TBD
    pass


def fetch_anim_range(context, expand = False, fit = True):
    """Fetch anim range from character animation.
    """
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_context_character_cache(context)
    arm = chr_cache.get_armature()
    if arm:
        action = utils.safe_get_action(arm)
        if action:
            if bpy.context.scene.use_preview_range:
                start = bpy.context.scene.frame_preview_start
                end = bpy.context.scene.frame_preview_end
            else:
                start = bpy.context.scene.frame_start
                end = bpy.context.scene.frame_end
            action_start = math.floor(action.frame_range[0])
            action_end = math.ceil(action.frame_range[1])
            if expand:
                if action_start < start:
                    start = action_start
                if action_end > end:
                    end = action_end
            elif fit:
                start = action_start
                end = action_end
            if bpy.context.scene.use_preview_range:
                bpy.context.scene.frame_preview_start = start
                bpy.context.scene.frame_preview_end = end
            else:
                bpy.context.scene.frame_start = start
                bpy.context.scene.frame_end = end


def cycles_setup(context):
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_context_character_cache(context)
    for obj_cache in chr_cache.object_cache:
        if obj_cache.is_mesh():
            obj = obj_cache.get_object()
            if not modifiers.has_modifier(obj, "SUBSURF"):
                mod = obj.modifiers.new(name = "Subdivision", type = "SUBSURF")
                if utils.B291():
                    mod.boundary_smooth = 'PRESERVE_CORNERS'
            if utils.B290():
                if obj.cycles.shadow_terminator_offset == 0.0:
                    obj.cycles.shadow_terminator_offset = 0.1


class CC3Scene(bpy.types.Operator):
    """Scene Tools"""
    bl_idname = "cc3.scene"
    bl_label = "Scene Tools"
    bl_options = {"REGISTER", "UNDO"}

    param: bpy.props.StringProperty(
            name = "param",
            default = ""
        )

    def execute(self, context):

        if self.param == "RENDER_IMAGE":
            render_image(context)

        elif self.param == "RENDER_ANIMATION":
            render_animation(context)

        elif self.param == "ANIM_RANGE_EXPAND":
            fetch_anim_range(context, expand=True)

        elif self.param == "ANIM_RANGE_FIT":
            fetch_anim_range(context, fit=True)

        elif self.param == "PHYSICS_PREP_CLOTH":
            # stop any playing animation
            if context.screen.is_animation_playing:
                bpy.ops.screen.animation_cancel(restore_frame=False)
            # reset the physics
            physics.reset_cache(context)
            # reset the animation
            bpy.ops.screen.frame_jump(end = False)

        elif self.param == "PHYSICS_PREP_RBW":
            # stop any playing animation
            if context.screen.is_animation_playing:
                bpy.ops.screen.animation_cancel(restore_frame=False)
            # reset the physics
            rigidbody.reset_cache(context)
            # reset the animation
            bpy.ops.screen.frame_jump(end = False)

        elif self.param == "PHYSICS_PREP_ALL":
            # stop any playing animation
            if context.screen.is_animation_playing:
                bpy.ops.screen.animation_cancel(restore_frame=False)
            # jump to end
            bpy.ops.screen.frame_jump(end = True)
            # reset the physics
            physics.reset_cache(context, all_objects=True)
            rigidbody.reset_cache(context)
            bpy.ops.ptcache.free_bake_all()
            # reset the animation
            bpy.ops.screen.frame_jump(end = False)
            bpy.context.view_layer.update()

        elif self.param == "CYCLES_SETUP":
            cycles_setup(context)
        else:
            setup_scene_default(self.param)
            if (self.param == "TEMPLATE"):
                compositor_setup()
                world_setup()
                utils.message_box("World nodes and compositor template set up.")

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "BLENDER":
            return "Restore the render settings and lighting to the Blender defaults"
        elif properties.param == "MATCAP":
            return "Use solid shading with matcap rendering"
        elif properties.param == "CC3":
            return "Use material shading with render settings and lighting to a replica of the default CC3 lighting"
        elif properties.param == "STUDIO":
            return "Use rendered shading with the Studio HDRI and left sided 3 point lighting"
        elif properties.param == "COURTYARD":
            return "Use rendered shading with the Courtyard HDRI and right sided 3 point lighting"
        elif properties.param == "TEMPLATE":
            return "Sets up a rendering template with rendered shading and world lighting. Sets up the Compositor and World nodes with a basic setup and adds tracking lights, a tracking camera and targetting objects"
        elif properties.param == "RENDER_IMAGE":
            return "Renders a single image"
        elif properties.param == "RENDER_ANIMATION":
            return "Renders the current animation range"
        elif properties.param == "ANIM_RANGE_EXPAND":
            return "Expands the animation range to include the range on the Action on the current character"
        elif properties.param == "ANIM_RANGE_FIT":
            return "Sets the animation range to the same range as the Action on the current character"
        elif properties.param == "PHYSICS_PREP_CLOTH":
            return "Resets the physics point cache on all cloth objects and synchronizes the physics point cache ranges " \
                   "on all cloth objects to fit the current scene animation range.\n\n" \
                   "i.e. if the point cache frame range does not cover the current scene range (or preview range) it will be extended to fit"
        elif properties.param == "PHYSICS_PREP_RBW":
            return "Resets the physics point cache for the rigid body world and synchronizes the physics point cache range " \
                   "to fit the current scene animation range.\n\n" \
                   "i.e. if the point cache frame range does not cover the current scene range (or preview range) it will be extended to fit"
        elif properties.param == "CYCLES_SETUP":
            return "Applies Shader Terminator Offset and subdivision to all meshes"

        return ""
