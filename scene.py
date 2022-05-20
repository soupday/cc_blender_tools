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

import bpy

from . import imageutils, nodeutils, physics, modifiers, utils, vars


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

def add_spot_light(name, location, rotation, energy, blend, size, distance, radius):
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
    return light

def add_area_light(name, location, rotation, energy, size):
    bpy.ops.object.light_add(type="AREA",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = utils.unique_name(name, True)
    light.data.shape = "DISK"
    light.data.size = size
    light.data.energy = energy
    return light

def add_point_light(name, location, rotation, energy, size):
    bpy.ops.object.light_add(type="POINT",
                    location = location, rotation = rotation)
    light = bpy.context.active_object
    light.name = utils.unique_name(name, True)
    light.data.shadow_soft_size = size
    light.data.energy = energy
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
                "BackTarget" in obj.name):
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

    arm = None
    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
        if (obj.type == "ARMATURE"):
            arm = obj
            break

    if arm is not None:
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
    lens_node.inputs["Dispersion"].default_value = 0.025
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
    nodeutils.set_node_input(bg_node, "Strength", 0.5)
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

            bpy.context.scene.eevee.use_gtao = False
            bpy.context.scene.eevee.gtao_distance = 0.2
            bpy.context.scene.eevee.gtao_factor = 1.0
            bpy.context.scene.eevee.use_bloom = False
            bpy.context.scene.eevee.bloom_threshold = 0.8
            bpy.context.scene.eevee.bloom_knee = 0.5
            bpy.context.scene.eevee.bloom_radius = 6.5
            bpy.context.scene.eevee.bloom_intensity = 0.05
            if prefs.refractive_eyes == "SSR":
                bpy.context.scene.eevee.use_ssr = True
                bpy.context.scene.eevee.use_ssr_refraction = True
            else:
                bpy.context.scene.eevee.use_ssr = False
                bpy.context.scene.eevee.use_ssr_refraction = False
            bpy.context.scene.eevee.bokeh_max_size = 32
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "None"
            bpy.context.scene.view_settings.exposure = 0.0
            bpy.context.scene.view_settings.gamma = 1.0
            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            restore_hidden_camera()

            key1 = add_point_light("Light",
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
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "Medium Contrast"
            bpy.context.scene.view_settings.exposure = 0.5
            bpy.context.scene.view_settings.gamma = 0.5

            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            restore_hidden_camera()

            strength = 50

            key1 = add_spot_light("Key1",
                    (0.71149, -1.49019, 2.04134),
                    (1.2280241250991821, 0.4846124053001404, 0.3449903726577759),
                    2.5 * strength, 0.5, 2.095, 9.7, 0.225)

            key2 = add_spot_light("Key2",
                    (0.63999, -1.3600, 0.1199),
                    (1.8845493793487549, 0.50091552734375, 0.6768553256988525),
                    2.5 * strength, 0.5, 2.095, 9.7, 1.0)

            back = add_spot_light("Back",
                    (0.0, 2.0199, 1.69),
                    (-1.3045594692230225, 0.11467886716127396, 0.03684665635228157),
                    3 * strength, 0.5, 1.448, 9.14, 1.0)
            back.data.color = utils.linear_to_srgb([213.0/155.0, 150.0/255.0, 120.0/255.0, 1.0])[0:3]

            set_contact_shadow(key1, 0.1, 0.01)

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
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "High Contrast"
            bpy.context.scene.view_settings.exposure = 0.5
            bpy.context.scene.view_settings.gamma = 1.0
            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            restore_hidden_camera()

            key = add_spot_light("Key",
                    (0.3088499903678894, -4.569439888000488, 2.574970006942749),
                    (0.39095374941825867, 1.3875367641448975, -1.1152653694152832),
                    400, 0.75, 0.75, 7.5, 0.4)

            right = add_area_light("Right",
                    (2.067525863647461, 0.8794340491294861, 1.1529420614242554),
                    (3.115412712097168, 1.7226399183273315, 9.79827880859375),
                    50, 2)

            back = add_spot_light("Ear",
                    (0.6740000247955322, 1.906999945640564, 1.6950000524520874),
                    (-0.03316125646233559, 1.3578661680221558, 1.1833332777023315),
                    100, 1, 1.0996, 9.1, 0.5)

            set_contact_shadow(key, 0.1, 0.01)
            set_contact_shadow(right, 0.1, 0.01)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'studio.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 0.0
            bpy.context.space_data.shading.studiolight_intensity = 0.2
            bpy.context.space_data.shading.studiolight_background_alpha = 0.5
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
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "Medium High Contrast"
            bpy.context.scene.view_settings.exposure = 0.5
            bpy.context.scene.view_settings.gamma = 0.6
            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            restore_hidden_camera()

            key = add_area_light("Key",
                    (-1.5078026056289673, -1.0891118049621582, 2.208820104598999),
                    (1.0848181247711182, -0.881056010723114, -0.5597077012062073),
                    40, 2)

            fill = add_area_light("Fill",
                    (2.28589, -1.51410, 1.40742),
                    (1.4248263835906982, 0.9756063222885132, 0.8594209551811218),
                    20, 2)

            back = add_area_light("Back",
                    (0.36789, 0.61511, 2.36201),
                    (-0.7961875796318054, 0.4831638038158417, -0.12343151122331619),
                    20, 1)

            set_contact_shadow(key, 0.1, 0.01)
            set_contact_shadow(fill, 0.1, 0.01)

            bpy.context.space_data.shading.type = 'MATERIAL'
            bpy.context.space_data.shading.use_scene_lights = True
            bpy.context.space_data.shading.use_scene_world = False
            bpy.context.space_data.shading.studio_light = 'courtyard.exr'
            bpy.context.space_data.shading.studiolight_rotate_z = 2.00713
            bpy.context.space_data.shading.studiolight_intensity = 0.35
            bpy.context.space_data.shading.studiolight_background_alpha = 0.5
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
            bpy.context.scene.view_settings.view_transform = "Filmic"
            bpy.context.scene.view_settings.look = "Medium High Contrast"
            bpy.context.scene.view_settings.exposure = 0.6
            bpy.context.scene.view_settings.gamma = 0.6
            if bpy.context.scene.cycles.transparent_max_bounces < 50:
                bpy.context.scene.cycles.transparent_max_bounces = 50


            remove_all_lights(True)
            camera, camera_target = camera_setup((0.1, -0.75, 1.6), (0, 0, 1.5))
            bpy.context.scene.camera = camera

            key = add_area_light("Key",
                    (-1.5078026056289673, -1.0891118049621582, 2.208820104598999),
                    (1.0848181247711182, -0.881056010723114, -0.5597077012062073),
                    40, 1)
            target_key = add_target("KeyTarget", (-0.006276353262364864, -0.004782751202583313, 1.503425121307373))
            track_to(key, target_key)

            fill = add_area_light("Fill",
                    (2.28589, -1.51410, 1.40742),
                    (1.4248263835906982, 0.9756063222885132, 0.8594209551811218),
                    10, 1)
            target_fill = add_target("FillTarget", (0.013503191992640495, 0.005856933072209358, 1.1814184188842773))
            track_to(fill, target_fill)

            back = add_area_light("Back",
                    (0.36789, 0.61511, 2.36201),
                    (-0.7961875796318054, 0.4831638038158417, -0.12343151122331619),
                    40, 0.5)
            target_back = add_target("BackTarget", (0.0032256320118904114, 0.06994983553886414, 1.6254671812057495))
            track_to(back, target_back)

            set_contact_shadow(key, 0.1, 0.01)
            set_contact_shadow(fill, 0.1, 0.01)

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
            obj_cache.object.select_set(True)
        bpy.ops.view3d.view_selected()
    except:
        pass


def active_select_body(chr_cache):
    for obj_cache in chr_cache.object_cache:
        obj = obj_cache.object
        if obj.type == "MESH":
            if obj_cache.object_type == "BODY":
                utils.set_active_object(obj)


def render_image(context):
    # TODO
    pass


def render_animation(context):
    # TODO
    pass


def fetch_anim_range(context):
    """Fetch anim range from character animation.
    """
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_context_character_cache(context)

    for obj_cache in chr_cache.object_cache:
        if obj_cache.object is not None and obj_cache.object.type == "ARMATURE":
            obj = obj_cache.object
            action = utils.safe_get_action(obj)
            if action:
                frame_start = math.floor(action.frame_range[0])
                frame_end = math.ceil(action.frame_range[1])
                context.scene.frame_start = frame_start
                context.scene.frame_end = frame_end
                return


def cycles_setup(context):
    props = bpy.context.scene.CC3ImportProps
    chr_cache = props.get_context_character_cache(context)
    for obj_cache in chr_cache.object_cache:
        if obj_cache.object is not None and obj_cache.object.type == "MESH":
            obj : bpy.types.Object = obj_cache.object
            if not modifiers.has_modifier(obj, "SUBSURF"):
                mod = obj.modifiers.new(name = "Subdivision", type = "SUBSURF")
                if utils.is_blender_version("2.91.0"):
                    mod.boundary_smooth = 'PRESERVE_CORNERS'
            if utils.is_blender_version("2.90.0"):
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
        elif self.param == "ANIM_RANGE":
            fetch_anim_range(context)
        elif self.param == "PHYSICS_PREP":
            physics.prepare_physics_bake(context)
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
        elif properties.param == "ANIM_RANGE":
            return "Sets the animation range to the same range as the Action on the current character"
        elif properties.param == "PHYSICS_PREP":
            return "Sets all the physics bake ranges to the same as the current scene animation range"
        elif properties.param == "CYCLES_SETUP":
            return "Applies Shader Terminator Offset and subdivision to all meshes"

        return ""
