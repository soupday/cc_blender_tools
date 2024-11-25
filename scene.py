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
from mathutils import Vector, Quaternion, Matrix, Euler

from . import colorspace, world, meshutils, nodeutils, rigidbody, physics, modifiers, utils, vars


def add_target(name, container, location):
    bpy.ops.object.empty_add(type="PLAIN_AXES", radius = 0.1,
        location = location)
    target = utils.get_active_object()
    target.name = name
    utils.set_ccic_id(target)
    if container:
        target.parent = container
        target.matrix_parent_inverse = container.matrix_world.inverted()
    return target

def set_contact_shadow(light, distance, thickness, no_jitter=False):
    if utils.B420():
        light.data.use_shadow = True
        light.data.use_shadow_jitter = not no_jitter
    else:
        light.data.use_contact_shadow = True
        light.data.contact_shadow_distance = distance
        light.data.contact_shadow_thickness = thickness


def track_to(obj, target):
    constraint = obj.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"


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
    return container


def add_sun_light(name, container, location, rotation, energy, angle):
    bpy.ops.object.light_add(type="SUN",
                    location = location, rotation = rotation)
    light = utils.get_active_object()
    light.name = name
    light.data.name = name
    utils.set_ccic_id(light)
    light.data.energy = energy
    light.data.angle = angle
    if container:
        light.parent = container
        light.matrix_parent_inverse = container.matrix_world.inverted()
    return light


def add_spot_light(name, container, location, rotation, energy, blend, size, distance, radius):
    bpy.ops.object.light_add(type="SPOT",
                    location = location, rotation = rotation)
    light = utils.get_active_object()
    light.name = name
    light.data.name = name
    utils.set_ccic_id(light)
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
    light = utils.get_active_object()
    light.name = name
    light.data.name = name
    utils.set_ccic_id(light)
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
    light = utils.get_active_object()
    light.name = name
    light.data.name = name
    utils.set_ccic_id(light)
    light.data.shadow_soft_size = size
    light.data.energy = energy
    if container:
        light.parent = container
        light.matrix_parent_inverse = container.matrix_world.inverted()
    return light


def remove_all_lights(inc_camera = False):
    for obj in bpy.data.objects:

        if not utils.object_exists(obj):
            continue

        if utils.has_ccic_id(obj):

            if obj.type == "LIGHT":
                bpy.data.objects.remove(obj)

            elif inc_camera and obj.type == "EMPTY" and "CameraTarget" in obj.name:
                bpy.data.objects.remove(obj)
                pass

            elif obj.type == "EMPTY" and \
                ("KeyTarget" in obj.name or \
                "FillTarget" in obj.name or \
                "BackTarget" in obj.name or \
                "Lighting" in obj.name):
                utils.delete_object_tree(obj)

            elif inc_camera and obj.type == "CAMERA":
                bpy.data.objects.remove(obj)

        else:

            if obj.type == "LIGHT":
                utils.hide(obj)
                obj.hide_render = True

            elif inc_camera and obj.type == "EMPTY" and "CameraTarget" in obj.name:
                utils.hide(obj)
                obj.hide_render = True
                pass

            elif obj.type == "EMPTY" and \
                ("KeyTarget" in obj.name or \
                "FillTarget" in obj.name or \
                "BackTarget" in obj.name):
                utils.hide(obj)
                obj.hide_render = True

            elif inc_camera and obj.type == "CAMERA":
                utils.hide(obj)
                obj.hide_render = True


def restore_hidden_camera():
    # enable the first hidden camera
    for obj in bpy.data.objects:
        if obj.type == "CAMERA" and not obj.visible_get():
            utils.unhide(obj)
            bpy.context.scene.camera = obj
            return


def camera_setup(context, camera_loc, target_loc):
    context = vars.get_context(context)

    # find an active camera
    camera = None
    target = None
    for obj in bpy.data.objects:
        if camera is None and obj.type == "CAMERA" and utils.has_ccic_id(obj):
            camera = obj
            camera.location = camera_loc
        if target is None and obj.type == "EMPTY" and "CameraTarget" in obj.name and utils.has_ccic_id(obj):
            target = obj
            target.location = target_loc
    if camera is None:
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=camera_loc)
        camera = utils.get_active_object()
        camera.name = "Camera"
        utils.set_ccic_id(camera)
    if target is None:
        target = add_target("CameraTarget", None, target_loc)

    utils.unhide(camera)
    utils.unhide(target)
    context.scene.camera = camera
    track_to(camera, target)
    camera.data.lens = 80
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = target
    camera.data.dof.aperture_fstop = 5.4
    camera.data.dof.aperture_blades = 5
    camera.data.dof.aperture_rotation = 0
    camera.data.dof.aperture_ratio = 1
    camera.data.display_size = 0.2
    camera.data.show_limits = True

    #camera_auto_target(camera, target)

    context.scene.render.resolution_x = 1920
    context.scene.render.resolution_y = 2560
    context.scene.render.resolution_percentage = 100

    return camera, target

def camera_auto_target(camera, target):
    props = vars.props()

    chr_cache = props.get_context_character_cache()
    if chr_cache is None:
        chr_cache = props.get_character_cache(utils.get_active_object(), None)
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

def compositor_setup(context):
    context = vars.get_context(context)

    context.scene.use_nodes = True
    nodes = context.scene.node_tree.nodes
    links = context.scene.node_tree.links
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
    shading = utils.get_view_3d_shading(context)
    if shading:
        shading.use_scene_world_render = True


def world_setup(context):
    context = vars.get_context(context)
    hide_view_extras(context, False)
    world.copy_material_to_render_world(context)


def setup_scene_default(context, scene_type):
    props = vars.props()
    prefs = vars.prefs()
    context = vars.get_context(context)

    # reset brightness
    props.lighting_brightness = 1.0

    # store selection and mode
    current_selected = context.selected_objects
    current_active = utils.get_active_object()
    current_mode = context.mode
    shading = utils.get_view_3d_shading(context)
    space_data = utils.get_view_3d_space(context)

    # go to object mode
    try:
        if current_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        if scene_type == "BLENDER":

            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = False
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.2
                context.scene.eevee.gtao_factor = 1.0
                context.scene.eevee.use_bloom = False
                context.scene.eevee.bloom_threshold = 0.8
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 6.5
                context.scene.eevee.bloom_intensity = 0.05
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "None", 0.0, 1.0)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100


            remove_all_lights(False)
            restore_hidden_camera()

            key1 = add_point_light("Light", None,
                    (4.076245307922363, 1.0054539442062378, 5.903861999511719),
                    (0.6503279805183411, 0.055217113345861435, 1.8663908243179321),
                    1000, 0.1)

            if shading:
                shading.type = 'MATERIAL'
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.studio_light = 'forest.exr'
                shading.studiolight_rotate_z = 0
                shading.studiolight_intensity = 1
                shading.studiolight_background_alpha = 0
                shading.studiolight_background_blur = 0
                space_data.clip_start = 0.1

        elif scene_type == "MATCAP":

            remove_all_lights(False)
            restore_hidden_camera()

            if shading:
                shading.type = 'SOLID'
                shading.light = 'MATCAP'
                shading.studio_light = 'basic_1.exr'
                shading.show_cavity = True

        elif scene_type == "CC3":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.25
                context.scene.eevee.gtao_factor = 0.5
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.800000011920929
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 2.0
                context.scene.eevee.bloom_intensity = 1.0
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32.0
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium High Contrast",
                                         1.0, 0.5)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(False)
            restore_hidden_camera()
            container = add_light_container()


            spot_light_000 = add_spot_light("Key", container,
                (-0.9423741102218628, 0.30936846137046814, 0.5819238424301147),
                (-0.07044415920972824, 1.2362500429153442, 2.5432639122009277),
                50.0, 1.0,
                2.0943946838378906, 9.729999542236328,
                1.0)
            set_contact_shadow(spot_light_000, 0.05000000074505806, 0.0024999999441206455)
            spot_light_000.data.color = (1.0, 0.9843137860298157, 0.9529412388801575)


            spot_light_001 = add_spot_light("Back", container,
                (0.12941402196884155, 1.31780207157135, 0.5352238416671753),
                (-0.02363934926688671, 0.8857088685035706, 1.4288825988769531),
                96.0, 1.0,
                2.6179935932159424, 9.149999618530273,
                0.0)
            set_contact_shadow(spot_light_001, 0.05000000074505806, 0.0024999999441206455)
            spot_light_001.data.color = (1.0, 1.0, 1.0)


            spot_light_002 = add_spot_light("Fill", container,
                (0.529399573802948, -1.2917252779006958, 0.682123064994812),
                (-0.0518769733607769, 1.2371199131011963, -1.1787829399108887),
                40.0, 0.32565000653266907,
                1.5707961320877075, 50.0,
                0.30000001192092896)
            set_contact_shadow(spot_light_002, 0.05000000074505806, 0.0024999999441206455)
            spot_light_002.data.color = (1.0, 0.9843137860298157, 0.9529412388801575)


            sun_light_003 = add_sun_light("Dir. Light", container,
                (-0.001717992126941681, -0.03369736298918724, -1.4594181776046753),
                (0.8644760847091675, 0.09251046180725098, 0.19978450238704681),
                0.5625,
                0.009180432185530663)
            set_contact_shadow(sun_light_003, 0.05000000074505806, 0.0024999999441206455)
            sun_light_003.data.color = (1.0, 1.0, 1.0)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = False
                shading.studio_light = "studio.exr"
                shading.studiolight_rotate_z = 0
                shading.studiolight_intensity = 1.0
                shading.studiolight_background_alpha = 0.0
                shading.studiolight_background_blur = 0.5
                space_data.clip_start = 0.009999999776482582

            align_to_head(context, container)


        elif scene_type == "STUDIO":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.25
                context.scene.eevee.gtao_factor = 0.5
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.3499999940395355
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 2.0
                context.scene.eevee.bloom_intensity = 0.10000000149011612
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32.0
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "High Contrast",
                                         0.5, 1.0)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(False)
            restore_hidden_camera()
            container = add_light_container()


            spot_light_000 = add_spot_light("Key_cc3iid_2528", container,
                (0.3071320056915283, -4.603137016296387, 1.1155518293380737),
                (0.39095383882522583, 1.387536644935608, -1.1138966083526611),
                400.0, 0.75,
                0.75, 7.5,
                0.4000000059604645)
            set_contact_shadow(spot_light_000, 0.05000000074505806, 0.0024999999441206455)
            spot_light_000.data.color = (1.0, 1.0, 1.0)


            area_light_001 = add_area_light("Right_cc3iid_2529", container,
                (2.065807819366455, 0.8457366824150085, -0.3064761161804199),
                (-0.02618018537759781, 1.4189527034759521, 0.3748694360256195),
                50.0, 2.0, 9.0)
            set_contact_shadow(area_light_001, 0.05000000074505806, 0.0024999999441206455)
            area_light_001.data.color = (1.0, 1.0, 1.0)


            spot_light_002 = add_spot_light("Ear_cc3iid_2530", container,
                (0.6722820401191711, 1.8733025789260864, 0.2355818748474121),
                (-0.03316128998994827, 1.3578661680221558, 1.1847020387649536),
                100.0, 1.0,
                1.0995999574661255, 9.100000381469727,
                0.5)
            set_contact_shadow(spot_light_002, 0.20000000298023224, 0.20000000298023224)
            spot_light_002.data.color = (1.0, 1.0, 1.0)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = False
                shading.studio_light = "studio.exr"
                shading.studiolight_rotate_z = 0
                shading.studiolight_intensity = 0.20000000298023224
                shading.studiolight_background_alpha = 0.05
                shading.studiolight_background_blur = 0.5
                space_data.clip_start = 0.009999999776482582

            align_to_head(context, container)





        # New presets

        elif scene_type == "PRESET_1":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
                context.scene.world.sun_threshold = 0.1
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.200
                context.scene.eevee.gtao_factor = 1.000
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.800
                context.scene.eevee.bloom_knee = 0.500
                context.scene.eevee.bloom_radius = 6.500
                context.scene.eevee.bloom_intensity = 0.050
                context.scene.eevee.use_ssr = False
                context.scene.eevee.use_ssr_refraction = False
            context.scene.eevee.bokeh_max_size = 100.000
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium Contrast",
                                         0.000, 0.900)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            area_light_001 = add_area_light("Light.002", container, (-1.051, -0.809, -0.354), (0.000, -1.266, 0.802), 35.0, 1.0, 40.0)
            set_contact_shadow(area_light_001, 0.200, 0.200)
            area_light_001.data.color = (1.0000, 1.0000, 1.0000)
            target_001 = add_target("target_001", container, (0.000, 0.000, 0.000))
            track_to(area_light_001, target_001)

            spot_light_002 = add_spot_light("Light.003", container, (1.230, -1.303, -0.191), (-0.000, -1.368, 2.288), 12.0, 0.8, 1.6, 40.0, 0.1)
            set_contact_shadow(spot_light_002, 0.200, 0.200)
            spot_light_002.data.color = (1.0000, 1.0000, 1.0000)
            track_to(spot_light_002, target_001)

            area_light_003 = add_area_light("Light.001", container, (0.453, 0.974, 0.000), (0.004, -1.175, 2.927), 10.0, 1.0, 40.0)
            set_contact_shadow(area_light_003, 0.200, 0.200)
            area_light_003.data.color = (1.0000, 1.0000, 1.0000)
            track_to(area_light_003, target_001)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = True
                shading.studio_light = "studio.exr"
                shading.studiolight_rotate_z = -0.7854
                shading.studiolight_intensity = 1.25
                shading.studiolight_background_alpha = 0.000
                shading.studiolight_background_blur = 0.500
                space_data.clip_start = 0.010

            world.world_setup(context,
                              utils.get_resource_path("presets", "veranda_4k.hdr"),
                              (1,1,1,1),
                              Vector((0,0,0)), Vector((0, 0, 0)), 1.0,
                              1.0)
            align_to_head(context, container, use_delta_rot=False)
            create_backdrop(container, (0.799, 0.799, 0.799, 1.0), 0.75)

        elif scene_type == "PRESET_2":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
                context.scene.world.sun_threshold = 0.1
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.200
                context.scene.eevee.gtao_factor = 1.000
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.800
                context.scene.eevee.bloom_knee = 0.500
                context.scene.eevee.bloom_radius = 6.500
                context.scene.eevee.bloom_intensity = 0.050
                context.scene.eevee.use_ssr = False
                context.scene.eevee.use_ssr_refraction = False
            context.scene.eevee.bokeh_max_size = 100.000
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium Contrast",
                                         0.000, 1.000)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            area_light_001 = add_area_light("Light.002", container, (-1.051, -0.809, -0.354), (0.000, -1.266, 0.802), 35.0, 1.0, 40.0)
            set_contact_shadow(area_light_001, 0.200, 0.200)
            area_light_001.data.color = (1.0000, 1.0000, 1.0000)
            target_001 = add_target("target_001", container, (0.000, 0.000, 0.000))
            track_to(area_light_001, target_001)

            spot_light_002 = add_spot_light("Light.003", container, (1.230, -1.303, -0.191), (-0.000, -1.368, 2.288), 12.0, 0.8, 1.6, 40.0, 0.1)
            set_contact_shadow(spot_light_002, 0.200, 0.200)
            spot_light_002.data.color = (1.0000, 1.0000, 1.0000)
            track_to(spot_light_002, target_001)

            area_light_003 = add_area_light("Light.001", container, (0.453, 0.974, 0.000), (0.004, -1.175, 2.927), 10.0, 1.0, 40.0)
            set_contact_shadow(area_light_003, 0.200, 0.200)
            area_light_003.data.color = (1.0000, 1.0000, 1.0000)
            track_to(area_light_003, target_001)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = True
                shading.studio_light = "studio.exr"
                shading.studiolight_rotate_z = 0.000
                shading.studiolight_intensity = 0.000
                shading.studiolight_background_alpha = 0.000
                shading.studiolight_background_blur = 0.500
                space_data.clip_start = 0.010

            world.world_setup(context,
                              "",
                              (0,0,0,1),
                              Vector((0,0,0)), Vector((0, 0, 0)), 1.0,
                              1.0)
            align_to_head(context, container, use_delta_rot=False)
            create_backdrop(container, (0.799, 0.799, 0.799, 1.0), 0.75)

        elif scene_type == "PRESET_3":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
                context.scene.world.sun_threshold = 0.1
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.200
                context.scene.eevee.gtao_factor = 1.000
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.800
                context.scene.eevee.bloom_knee = 0.500
                context.scene.eevee.bloom_radius = 6.500
                context.scene.eevee.bloom_intensity = 0.050
                context.scene.eevee.use_ssr = False
                context.scene.eevee.use_ssr_refraction = False
            context.scene.eevee.bokeh_max_size = 100.000
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium Contrast",
                                         0.000, 1.000)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            spot_light_001 = add_spot_light("Light.001", container, (0.546, -1.256, 0.281), (-0.000, -1.368, 2.288), 50.0, 0.8, 1.6, 40.0, 0.2)
            set_contact_shadow(spot_light_001, 0.200, 0.200)
            spot_light_001.data.color = (1.0000, 1.0000, 1.0000)
            target_001 = add_target("target_001", container, (0.000, 0.000, 0.000))
            track_to(spot_light_001, target_001)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = True
                shading.studio_light = "courtyard.exr"
                shading.studiolight_rotate_z = 0.1745
                shading.studiolight_intensity = 1.25
                shading.studiolight_background_alpha = 0.000
                shading.studiolight_background_blur = 0.500
                space_data.clip_start = 0.010

            world.world_setup(context,
                              utils.get_resource_path("presets", "kiara_1_dawn_4k.hdr"),
                              (1,1,1,1),
                              Vector((0,0,0)), Vector((0, 0, -0.87266)), 1.0,
                              1.0)
            align_to_head(context, container, use_delta_rot=False)
            create_backdrop(container, (0.799, 0.799, 0.799, 1.0), 0.75)

        elif scene_type == "PRESET_4":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
                context.scene.world.sun_threshold = 0.1
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.200
                context.scene.eevee.gtao_factor = 1.000
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.800
                context.scene.eevee.bloom_knee = 0.500
                context.scene.eevee.bloom_radius = 6.500
                context.scene.eevee.bloom_intensity = 0.050
                context.scene.eevee.use_ssr = False
                context.scene.eevee.use_ssr_refraction = False
            context.scene.eevee.bokeh_max_size = 100.000
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium Contrast",
                                         0.000, 1.000)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            area_light_001 = add_area_light("Light.001", container, (-1.051, -0.809, -0.354), (0.000, -1.266, 0.802), 35.0, 1.0, 40.0)
            set_contact_shadow(area_light_001, 0.200, 0.200)
            area_light_001.data.color = (0.4760, 0.7875, 1.0000)
            target_001 = add_target("target_001", container, (0.000, 0.000, 0.000))
            track_to(area_light_001, target_001)

            spot_light_002 = add_spot_light("Light.002", container, (1.230, -1.303, -0.191), (-0.000, -1.368, 2.288), 12.0, 0.8, 1.6, 40.0, 0.1)
            set_contact_shadow(spot_light_002, 0.200, 0.200)
            spot_light_002.data.color = (1.0000, 1.0000, 1.0000)
            track_to(spot_light_002, target_001)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = True
                shading.studio_light = "studio.exr"
                shading.studiolight_rotate_z = 0.000
                shading.studiolight_intensity = 0.05
                shading.studiolight_background_alpha = 0.000
                shading.studiolight_background_blur = 0.500
                space_data.clip_start = 0.010

            world.world_setup(context,
                              "",
                              (0.109461,0.104617,0.291771,1),
                              Vector((0,0,0)), Vector((0, 0, 0)), 1.0,
                              1.0)
            align_to_head(context, container, use_delta_rot=False)
            create_backdrop(container, (0.799, 0.799, 0.799, 1.0), 0.75)

        elif scene_type == "PRESET_5":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
                context.scene.world.sun_threshold = 0.1
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.200
                context.scene.eevee.gtao_factor = 1.000
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.800
                context.scene.eevee.bloom_knee = 0.500
                context.scene.eevee.bloom_radius = 6.500
                context.scene.eevee.bloom_intensity = 0.050
                context.scene.eevee.use_ssr = False
                context.scene.eevee.use_ssr_refraction = False
            context.scene.eevee.bokeh_max_size = 100.000
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium Contrast",
                                         0.000, 1.000)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            spot_light_001 = add_spot_light("Light.003", container, (1.230, -1.303, -0.191), (-0.000, -1.368, 2.288), 12.0, 0.8, 1.6, 40.0, 0.1)
            set_contact_shadow(spot_light_001, 0.200, 0.200)
            spot_light_001.data.color = (1.0000, 1.0000, 1.0000)
            target_001 = add_target("target_001", container, (0.000, 0.000, 0.000))
            track_to(spot_light_001, target_001)

            area_light_002 = add_area_light("Light.001", container, (-1.051, -0.809, -0.354), (0.000, -1.266, 0.802), 55.0, 1.0, 40.0)
            set_contact_shadow(area_light_002, 0.200, 0.200)
            area_light_002.data.color = (0.4760, 0.7875, 1.0000)
            track_to(area_light_002, target_001)

            area_light_003 = add_area_light("Light.002", container, (-0.395, 0.584, 0.064), (0.000, -1.266, 0.802), 35.0, 1.0, 40.0)
            set_contact_shadow(area_light_003, 0.200, 0.200)
            area_light_003.data.color = (1.0000, 0.6038, 0.2462)
            track_to(area_light_003, target_001)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = True
                shading.studio_light = "studio.exr"
                shading.studiolight_rotate_z = 0.000
                shading.studiolight_intensity = 0.1
                shading.studiolight_background_alpha = 0.000
                shading.studiolight_background_blur = 0.500
                space_data.clip_start = 0.010

            world.world_setup(context,
                              "",
                              (0.107022,0.23074,0.05127,1),
                              Vector((0,0,0)), Vector((0, 0, 0)), 1.0,
                              1.0)
            align_to_head(context, container, use_delta_rot=False)
            create_backdrop(container, (0.799, 0.799, 0.799, 1.0), 0.75)

        elif scene_type == "PRESET_6":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
                context.scene.world.sun_threshold = 0.1
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.200
                context.scene.eevee.gtao_factor = 1.000
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.800
                context.scene.eevee.bloom_knee = 0.500
                context.scene.eevee.bloom_radius = 6.500
                context.scene.eevee.bloom_intensity = 0.050
                context.scene.eevee.use_ssr = False
                context.scene.eevee.use_ssr_refraction = False
            context.scene.eevee.bokeh_max_size = 100.000
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium Contrast",
                                         0.000, 1.000)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()

            area_light_001 = add_area_light("Light.001", container, (-0.981, -0.808, -0.343), (0.000, -1.266, 0.802), 20.0, 1.0, 40.0)
            set_contact_shadow(area_light_001, 0.200, 0.200)
            area_light_001.data.color = (1.0000, 0.0329, 0.8662)
            target_001 = add_target("target_001", container, (0.000, 0.000, 0.000))
            track_to(area_light_001, target_001)

            area_light_002 = add_area_light("Light.002", container, (1.087, 0.150, 0.071), (0.000, -1.266, 0.802), 20.0, 1.0, 40.0)
            set_contact_shadow(area_light_002, 0.200, 0.200)
            area_light_002.data.color = (0.0194, 0.0354, 1.0000)
            track_to(area_light_002, target_001)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = True
                shading.studio_light = "studio.exr"
                shading.studiolight_rotate_z = 0.000
                shading.studiolight_intensity = 0.05
                shading.studiolight_background_alpha = 0.000
                shading.studiolight_background_blur = 0.500
                space_data.clip_start = 0.010

            world.world_setup(context,
                              "",
                              (0.0185,0.008568,0.07036,1),
                              Vector((0,0,0)), Vector((0, 0, 0)), 1.0,
                              1.0)
            align_to_head(context, container, use_delta_rot=False)
            create_backdrop(container, (0.799, 0.799, 0.799, 1.0), 0.75)



        # Old presets

        elif scene_type == "COURTYARD":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.25
                context.scene.eevee.gtao_factor = 0.5
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.3499999940395355
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 2.0
                context.scene.eevee.bloom_intensity = 0.10000000149011612
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32.0
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium High Contrast",
                                         0.5, 0.6000000238418579)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(False)
            restore_hidden_camera()
            container = add_light_container()


            area_light_000 = add_area_light("Key_cc3iid_2524", container,
                (-1.5095206499099731, -1.1228091716766357, 0.7494019269943237),
                (1.0848180055618286, -0.881056010723114, -0.5583388805389404),
                40.0, 2.0, 9.0)
            set_contact_shadow(area_light_000, 0.05000000074505806, 0.0024999999441206455)
            area_light_000.data.color = (1.0, 1.0, 1.0)


            area_light_001 = add_area_light("Fill_cc3iid_2525", container,
                (2.2841720581054688, -1.5477973222732544, -0.051998138427734375),
                (1.4248265027999878, 0.975606381893158, 0.8607898354530334),
                20.0, 2.0, 9.0)
            set_contact_shadow(area_light_001, 0.05000000074505806, 0.0024999999441206455)
            area_light_001.data.color = (1.0, 1.0, 1.0)


            area_light_002 = add_area_light("Back_cc3iid_2526", container,
                (0.36617201566696167, 0.5814126133918762, 0.9025918245315552),
                (-0.7961875796318054, 0.4831638038158417, -0.12206275016069412),
                20.0, 1.0, 9.0)
            set_contact_shadow(area_light_002, 0.20000000298023224, 0.20000000298023224)
            area_light_002.data.color = (1.0, 1.0, 1.0)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = False
                shading.studio_light = "courtyard.exr"
                shading.studiolight_rotate_z = 0.7854
                shading.studiolight_intensity = 0.3499999940395355
                shading.studiolight_background_alpha = 0.05
                shading.studiolight_background_blur = 0.5
                space_data.clip_start = 0.009999999776482582

            align_to_head(context, container)


        elif scene_type == "AQUA":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.25
                context.scene.eevee.gtao_factor = 0.5
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.3499999940395355
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 2.0
                context.scene.eevee.bloom_intensity = 0.10000000149011612
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32.0
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium High Contrast",
                                         0.800000011920929, 0.550000011920929)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(False)
            restore_hidden_camera()
            container = add_light_container()


            sun_light_000 = add_sun_light("Dir. Light", container,
                (-0.001717992126941681, -0.03369736298918724, -1.4594181776046753),
                (-2.115131378173828, 0.18253736197948456, 1.0880452394485474),
                0.14580000936985016,
                0.009180432185530663)
            set_contact_shadow(sun_light_000, 0.05000000074505806, 0.0024999999441206455)
            sun_light_000.data.color = (0.5601616501808167, 0.5601616501808167, 0.7620295882225037)


            spot_light_001 = add_spot_light("Back", container,
                (-1.9980238676071167, -0.5209299921989441, 0.47781240940093994),
                (-0.6497521996498108, 1.344329595565796, 2.641986131668091),
                800.0, 1.0,
                0.6806783080101013, 2.4000000953674316,
                0.9646999835968018)
            set_contact_shadow(spot_light_001, 0.05000000074505806, 0.0024999999441206455)
            spot_light_001.data.color = (0.7183890342712402, 0.8502671718597412, 1.2038928270339966)


            spot_light_002 = add_spot_light("Back.001", container,
                (-1.0672816038131714, 1.770845651626587, 0.26936018466949463),
                (-0.5413775444030762, 1.4816209077835083, 1.5110341310501099),
                2000.0, 1.0,
                0.6806783080101013, 2.4000000953674316,
                2.392199993133545)
            set_contact_shadow(spot_light_002, 0.05000000074505806, 0.0024999999441206455, no_jitter=True)
            spot_light_002.data.color = (0.7183890342712402, 0.8502671718597412, 1.2038928270339966)


            spot_light_003 = add_spot_light("Key", container,
                (-4.202385902404785, -0.3203423023223877, 2.212378978729248),
                (-0.0384182371199131, 1.0002037286758423, -2.871201753616333),
                220.0, 0.75,
                0.7504914402961731, 9.640000343322754,
                0.5088000297546387)
            set_contact_shadow(spot_light_003, 0.05000000074505806, 0.0024999999441206455)
            spot_light_003.data.color = (0.7106313705444336, 0.753057062625885, 0.8657234311103821)


            spot_light_004 = add_spot_light("Key.001", container,
                (-0.6216474771499634, -1.700995922088623, -0.5031678676605225),
                (-0.425364226102829, -2.1132423877716064, 1.6004295349121094),
                107.20000457763672, 1.0,
                1.4486230611801147, 9.149999618530273,
                0.5)
            set_contact_shadow(spot_light_004, 0.05000000074505806, 0.0024999999441206455)
            spot_light_004.data.color = (0.6796281933784485, 0.7500560283660889, 0.8958061933517456)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = False
                shading.studio_light = "studio.exr"
                shading.studiolight_rotate_z = 3.1416
                shading.studiolight_intensity = 0.4
                shading.studiolight_background_alpha = 0.05000000074505806
                shading.studiolight_background_blur = 0.5
                space_data.clip_start = 0.009999999776482582

            align_to_head(context, container)


        elif scene_type == "AUTHORITY":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.25
                context.scene.eevee.gtao_factor = 0.5
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.35
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 2.0
                context.scene.eevee.bloom_intensity = 0.1
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium High Contrast", 0.5, 0.6)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(False)
            restore_hidden_camera()
            container = add_light_container()

            spot_light_000 = add_spot_light("Back", container,
                (-0.006970776244997978, 2.0284667015075684, 0.23129618167877197),
                (-0.032768018543720245, 1.3572243452072144, 1.5501036643981934),
                214.40000915527344, 1.0,
                1.4486230611801147, 9.149999618530273,
                1.0)
            set_contact_shadow(spot_light_000, 0.05000000074505806, 0.0024999999441206455)
            spot_light_000.data.color = (0.8352941870689392, 0.5882353186607361, 0.4705882668495178)


            sun_light_001 = add_point_light("Point light", container,
                (-0.4660474359989166, -2.8790249824523926, 2.4746880531311035),
                (-0.0, -0.0, 0.001198019366711378),
                80.0,
                0.0)
            set_contact_shadow(sun_light_001, 0.05000000074505806, 0.0024999999441206455)
            sun_light_001.data.color = (0.7843137979507446, 0.7843137979507446, 0.7843137979507446)


            spot_light_002 = add_spot_light("Fill", container,
                (1.072341799736023, 0.6809514164924622, -0.8709145784378052),
                (2.765415906906128, -0.7434117197990417, 0.9125480055809021),
                20.0, 1.0,
                2.460913896560669, 5.03000020980835,
                0.2020999938249588)
            set_contact_shadow(spot_light_002, 0.05000000074505806, 0.0024999999441206455)
            spot_light_002.data.color = (0.5058823823928833, 0.5803921818733215, 0.6274510025978088)


            spot_light_003 = add_spot_light("Key", container,
                (-0.855573832988739, -1.4020836353302002, 1.0885698795318604),
                (0.0018498882418498397, -1.2320795059204102, 0.9594647884368896),
                320.0, 1.0,
                1.4486230611801147, 9.149999618530273,
                0.800000011920929)
            set_contact_shadow(spot_light_003, 0.05000000074505806, 0.0024999999441206455)
            spot_light_003.data.color = (0.7568628191947937, 0.8235294818878174, 0.8352941870689392)


            spot_light_004 = add_spot_light("Back Light Head", container,
                (-0.5010148882865906, -1.1003491878509521, 0.7674758434295654),
                (1.3239206075668335, 0.023048613220453262, -0.5318448543548584),
                0.0, 0.2524999976158142,
                1.2740901708602905, 2.5899999141693115,
                0.5163000226020813)
            set_contact_shadow(spot_light_004, 0.05000000074505806, 0.0024999999441206455)
            spot_light_004.data.color = (0.7843137979507446, 0.7843137979507446, 0.686274528503418)


            spot_light_005 = add_spot_light("Key 2", container,
                (-3.1835274696350098, 2.886387586593628, 2.2099413871765137),
                (-0.03842170163989067, 1.0002015829086304, 2.6080286502838135),
                500.0, 0.75,
                0.7504914402961731, 9.640000343322754,
                0.5088000297546387)
            set_contact_shadow(spot_light_005, 0.05000000074505806, 0.0024999999441206455)
            spot_light_005.data.color = (1.0, 0.9843137860298157, 0.9529412388801575)


            spot_light_006 = add_spot_light("Key Front", container,
                (1.283434510231018, 4.030579090118408, 1.8864820003509521),
                (-0.3483297824859619, 1.1461026668548584, 0.833476185798645),
                60.0, 0.75,
                0.7504914402961731, 9.640000343322754,
                0.6155999898910522)
            set_contact_shadow(spot_light_006, 0.05000000074505806, 0.0024999999441206455)
            spot_light_006.data.color = (0.8823530077934265, 0.9411765336990356, 1.0)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = False
                shading.studio_light = "studio.exr"
                shading.studiolight_rotate_z = 0
                shading.studiolight_intensity = 0.2
                shading.studiolight_background_alpha = 0.05
                shading.studiolight_background_blur = 0.5
                space_data.clip_start = 0.01

            align_to_head(context, container)


        elif scene_type == "EXQUISITE":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.25
                context.scene.eevee.gtao_factor = 0.5
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.800000011920929
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 2.0
                context.scene.eevee.bloom_intensity = 1.0
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32.0
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium High Contrast",
                                         0.550000011920929, 0.6000000238418579)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(False)
            restore_hidden_camera()
            container = add_light_container()


            spot_light_000 = add_spot_light("Back", container,
                (-0.007075886707752943, 1.986365795135498, 0.23595929145812988),
                (-0.03276771679520607, 1.3572238683700562, 1.5502748489379883),
                214.40000915527344, 1.0,
                1.4486230611801147, 9.149999618530273,
                1.0)
            set_contact_shadow(spot_light_000, 0.05000000074505806, 0.0024999999441206455)
            spot_light_000.data.color = (0.8352941870689392, 0.5882353186607361, 0.4705882668495178)


            spot_light_001 = add_spot_light("Key", container,
                (0.2691590487957001, -1.4757589101791382, 0.42834436893463135),
                (0.06910523027181625, 1.289427638053894, -1.2877484560012817),
                14.0, 1.0,
                1.710422396659851, 9.729999542236328,
                0.570900022983551)
            set_contact_shadow(spot_light_001, 0.05000000074505806, 0.0024999999441206455)
            spot_light_001.data.color = (0.48235297203063965, 0.5647059082984924, 0.8352941870689392)


            spot_light_002 = add_spot_light("Fill", container,
                (1.290446400642395, 0.9552819728851318, 0.18248343467712402),
                (-1.58391535282135, -1.23851478099823, -0.9736499190330505),
                20.0, 1.0,
                2.460913896560669, 5.03000020980835,
                0.2020999938249588)
            set_contact_shadow(spot_light_002, 0.05000000074505806, 0.0024999999441206455)
            spot_light_002.data.color = (0.5058823823928833, 0.5803921818733215, 0.6274510025978088)


            spot_light_003 = add_spot_light("Key.001", container,
                (-1.0078679323196411, -1.402224063873291, -0.8448393940925598),
                (-0.44580304622650146, -2.239304304122925, 1.3679754734039307),
                350.0, 1.0,
                1.4486230611801147, 9.149999618530273,
                0.800000011920929)
            set_contact_shadow(spot_light_003, 0.05000000074505806, 0.0024999999441206455)
            spot_light_003.data.color = (0.48235297203063965, 0.5647059082984924, 0.8352941870689392)


            spot_light_004 = add_spot_light("Back Light_Head", container,
                (-0.5920167565345764, -1.0476973056793213, -0.6991136074066162),
                (2.2965502738952637, 0.219370499253273, -0.49700337648391724),
                0.0, 0.2524999976158142,
                1.2740901708602905, 2.5899999141693115,
                0.5163000226020813)
            set_contact_shadow(spot_light_004, 0.05000000074505806, 0.0024999999441206455)
            spot_light_004.data.color = (0.7843137979507446, 0.7843137979507446, 0.686274528503418)


            spot_light_005 = add_spot_light("Key.002", container,
                (-4.265609264373779, -0.32033464312553406, 2.0730538368225098),
                (-0.03842073678970337, 1.0002021789550781, -2.8712077140808105),
                300.0, 0.75,
                0.7504914402961731, 9.640000343322754,
                0.5088000297546387)
            set_contact_shadow(spot_light_005, 0.05000000074505806, 0.0024999999441206455)
            spot_light_005.data.color = (0.48235297203063965, 0.5647059082984924, 0.8352941870689392)


            spot_light_006 = add_spot_light("Key_Front", container,
                (1.2833281755447388, 3.9884731769561768, 1.8911453485488892),
                (-0.3483291268348694, 1.1461023092269897, 0.8336480855941772),
                60.0, 0.75,
                0.7504914402961731, 9.640000343322754,
                0.6155999898910522)
            set_contact_shadow(spot_light_006, 0.05000000074505806, 0.0024999999441206455)
            spot_light_006.data.color = (0.8823530077934265, 0.9411765336990356, 1.0)


            spot_light_007 = add_spot_light("Fill.001", container,
                (3.7928030490875244, -0.731768786907196, 2.6132020950317383),
                (-0.03842347860336304, 1.0002011060714722, -0.283409982919693),
                12.0, 0.75,
                0.7504914402961731, 9.640000343322754,
                0.6155999898910522)
            set_contact_shadow(spot_light_007, 0.05000000074505806, 0.0024999999441206455)
            spot_light_007.data.color = (0.8823530077934265, 0.9411765336990356, 1.0)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = False
                shading.studio_light = "sunset.exr"
                shading.studiolight_rotate_z = 0.6440264591947198
                shading.studiolight_intensity = 0.20000000298023224
                shading.studiolight_background_alpha = 0.0
                shading.studiolight_background_blur = 0.5
                space_data.clip_start = 0.009999999776482582

            align_to_head(context, container)


        elif scene_type == "BLUR_WARM":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.25
                context.scene.eevee.gtao_factor = 0.5
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.35
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 4.0
                context.scene.eevee.bloom_intensity = 0.15
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium High Contrast", 0.0, 0.8)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(False)
            restore_hidden_camera()
            container = add_light_container()


            area_light_000 = add_area_light("Key", container,
                (0.23867405951023102, -1.4948756694793701, 0.3496365547180176),
                (0.06910630315542221, 1.2894277572631836, -1.3055258989334106),
                13.334359169006348, 0.570900022983551, 9.729999542236328)
            set_contact_shadow(area_light_000, 0.20000000298023224, 0.20000000298023224)
            area_light_000.data.color = (1.0385820865631104, 0.9224395155906677, 0.9496166706085205)


            area_light_001 = add_area_light("Rim_red", container,
                (0.09254506230354309, 0.8227812051773071, 0.0968252420425415),
                (-0.01860235258936882, 1.3557215929031372, 1.3542215824127197),
                1.392878770828247, 0.30000001192092896, 1.5299999713897705)
            set_contact_shadow(area_light_001, 0.20000000298023224, 0.20000000298023224)
            area_light_001.data.color = (0.746380627155304, 0.2494838982820511, 0.1724458634853363)


            area_light_002 = add_area_light("Face", container,
                (0.3584509789943695, -1.7150081396102905, -0.013369083404541016),
                (1.354569673538208, 1.4951262474060059, -0.10444492101669312),
                4.196816921234131, 0.732699990272522, 9.149999618530273)
            set_contact_shadow(area_light_002, 0.20000000298023224, 0.20000000298023224)
            area_light_002.data.color = (0.7566361427307129, 0.6142145395278931, 0.6137133836746216)


            area_light_003 = add_area_light("Key Light - Up", container,
                (0.0537683479487896, -1.2218871116638184, -0.45024120807647705),
                (0.21799428761005402, 1.0667732954025269, -1.6040315628051758),
                8.910563468933105, 1.0, 2.799999952316284)
            set_contact_shadow(area_light_003, 0.20000000298023224, 0.20000000298023224)
            area_light_003.data.color = (0.8588783144950867, 0.7302938103675842, 0.7108697295188904)


            sun_light_004 = add_sun_light("Dir. Light", container,
                (-0.03220297023653984, -0.05281418189406395, -1.538125991821289),
                (0.7853979468345642, 1.619704370625641e-08, 2.9214975833892822),
                3.6000001430511475,
                0.009180432185530663)
            set_contact_shadow(sun_light_004, 0.20000000298023224, 0.20000000298023224)
            sun_light_004.data.color = (0.7544040083885193, 0.5007292032241821, 0.4338947832584381)


            sun_light_005 = add_sun_light("Dir. Light_closeup", container,
                (-0.03220297023653984, -0.05281418189406395, -1.538125991821289),
                (0.7853981852531433, -2.2826515788665347e-08, 0.19805686175823212),
                2.0999999046325684,
                0.009180432185530663)
            set_contact_shadow(sun_light_005, 0.20000000298023224, 0.20000000298023224)
            sun_light_005.data.color = (0.651659369468689, 0.5787855982780457, 0.5958379507064819)


            spot_light_006 = add_spot_light("Rim_yellow", container,
                (0.2832099497318268, 0.8227812051773071, 0.0968252420425415),
                (-0.01860201172530651, 1.3557212352752686, 1.354223370552063),
                13.374069213867188, 1.0,
                2.6179935932159424, 1.5299999713897705,
                0.0)
            set_contact_shadow(spot_light_006, 0.20000000298023224, 0.20000000298023224)
            spot_light_006.data.color = (1.0332900285720825, 0.6694098114967346, 0.2778758704662323)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = False
                shading.studio_light = "redWall.hdr"
                shading.studiolight_rotate_z = 2.356194391846657
                shading.studiolight_intensity = 0.25
                shading.studiolight_background_alpha = 0.05
                shading.studiolight_background_blur = 0.5
                space_data.clip_start = 0.009999999776482582

            align_to_head(context, container)


        elif scene_type == "INTERIOR":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.25
                context.scene.eevee.gtao_factor = 0.5
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.800000011920929
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 2.0
                context.scene.eevee.bloom_intensity = 1.0
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32.0
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "High Contrast",
                                         0.0, 0.75)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(False)
            restore_hidden_camera()
            container = add_light_container()


            spot_light_000 = add_spot_light("Back", container,
                (0.5539839267730713, 1.8741519451141357, 0.18556976318359375),
                (-0.032768093049526215, 1.3572243452072144, 1.3471097946166992),
                214.40000915527344, 1.0,
                1.4486230611801147, 9.149999618530273,
                1.0)
            set_contact_shadow(spot_light_000, 0.05000000074505806, 0.0024999999441206455)
            spot_light_000.data.color = (0.8352941870689392, 0.5882353186607361, 0.4705882668495178)


            sun_light_001 = add_point_light("Point light", container,
                (-0.8802585601806641, -2.8414785861968994, 2.4289615154266357),
                (-0.0, -0.0, -0.20179717242717743),
                120.0,
                0.25)
            set_contact_shadow(sun_light_001, 0.05000000074505806, 0.0024999999441206455)
            sun_light_001.data.color = (0.7843137979507446, 0.7843137979507446, 0.7843137979507446)


            spot_light_002 = add_spot_light("Key Lower", container,
                (-0.7574724555015564, -1.0714011192321777, -1.0519981384277344),
                (2.292457342147827, -0.48952972888946533, -1.1989017724990845),
                50.29998779296875, 1.0,
                0.541051983833313, 10.989999771118164,
                0.25)
            set_contact_shadow(spot_light_002, 0.05000000074505806, 0.0024999999441206455)
            spot_light_002.data.color = (0.7568628191947937, 0.8235294818878174, 0.8352941870689392)


            spot_light_003 = add_spot_light("Top Spot", container,
                (-0.31087398529052734, -1.1979326009750366, 1.2510926723480225),
                (0.8557190895080566, -1.1747671280204486e-08, -0.3761661648750305),
                65.69999694824219, 0.375,
                1.221730351448059, 5.0,
                0.0)
            set_contact_shadow(spot_light_003, 0.05000000074505806, 0.0024999999441206455)
            spot_light_003.data.color = (0.760784387588501, 1.0, 0.9803922176361084)


            spot_light_004 = add_spot_light("Key", container,
                (-0.7617886066436768, 4.546901226043701, 0.31877660751342773),
                (-2.300450086593628, 1.8846901655197144, -0.3277812898159027),
                800.0, 0.75,
                0.7504914402961731, 9.640000343322754,
                0.5088000297546387)
            set_contact_shadow(spot_light_004, 0.05000000074505806, 0.0024999999441206455)
            spot_light_004.data.color = (0.760784387588501, 1.0, 0.9803922176361084)


            spot_light_005 = add_spot_light("Key Back", container,
                (2.2198028564453125, 3.576693296432495, 1.8407554626464844),
                (-0.3483298718929291, 1.146102786064148, 0.6304814219474792),
                73.5999984741211, 0.75,
                0.7504914402961731, 9.640000343322754,
                0.6155999898910522)
            set_contact_shadow(spot_light_005, 0.05000000074505806, 0.0024999999441206455)
            spot_light_005.data.color = (1.0, 1.0, 1.0)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = False
                shading.studio_light = "interior.exr"
                shading.studiolight_rotate_z = 1.0472
                shading.studiolight_intensity = 0.4551074802875519
                shading.studiolight_background_alpha = 0.05000000074505806
                shading.studiolight_background_blur = 0.5
                space_data.clip_start = 0.009999999776482582

            align_to_head(context, container)


        elif scene_type == "LEADING_ROLE":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.25
                context.scene.eevee.gtao_factor = 0.5
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.65
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 3.0
                context.scene.eevee.bloom_intensity = 1.0
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32.0
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium Contrast",
                                         0.5, 0.6)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(False)
            restore_hidden_camera()
            container = add_light_container()


            sun_light_000 = add_sun_light("Dir. Light", container,
                (-0.001717992126941681, -0.03369736298918724, -1.4594181776046753),
                (-2.115131378173828, 0.18253736197948456, 1.0880452394485474),
                0.14580000936985016,
                0.009180432185530663)
            set_contact_shadow(sun_light_000, 0.05000000074505806, 0.0024999999441206455)
            sun_light_000.data.color = (0.6222654581069946, 0.5600389242172241, 0.7000486254692078)


            sun_light_001 = add_sun_light("Dir. Light_0", container,
                (-0.001717992126941681, -0.03369736298918724, -1.4594181776046753),
                (1.254795789718628, -0.12031947821378708, 1.9957903623580933),
                0.18000000715255737,
                0.009180432185530663)
            set_contact_shadow(sun_light_001, 0.05000000074505806, 0.0024999999441206455)
            sun_light_001.data.color = (0.5751467943191528, 0.5711802244186401, 0.4105357825756073)


            spot_light_002 = add_spot_light("Back Light_Head", container,
                (0.0018105169292539358, 1.526957392692566, 0.16657984256744385),
                (-1.2665398120880127, 4.095466674125525e-11, 0.0013687603641301394),
                201.60000610351562, 0.2524999976158142,
                2.0943946838378906, 10.0,
                0.05000000074505806)
            set_contact_shadow(spot_light_002, 0.05000000074505806, 0.0024999999441206455)
            spot_light_002.data.color = (0.7852135300636292, 0.5582867860794067, 0.5388527512550354)


            spot_light_003 = add_spot_light("Key", container,
                (-1.1670068502426147, -1.4828466176986694, 0.5728923082351685),
                (-0.40884634852409363, -1.5184019804000854, 1.2575336694717407),
                98.4000015258789, 1.0,
                1.4486230611801147, 9.149999618530273,
                0.5)
            set_contact_shadow(spot_light_003, 0.05000000074505806, 0.0024999999441206455)
            spot_light_003.data.color = (0.8283909559249878, 0.7455518841743469, 0.9319397807121277)


            spot_light_004 = add_spot_light("Back", container,
                (-2.088263511657715, -0.4154135584831238, 0.44909727573394775),
                (-0.6497525572776794, 1.3443297147750854, 2.5910379886627197),
                602.7999877929688, 1.0,
                0.6806783080101013, 2.4000000953674316,
                0.9646999835968018)
            set_contact_shadow(spot_light_004, 0.05000000074505806, 0.0024999999441206455)
            spot_light_004.data.color = (0.9917355179786682, 0.8925620317459106, 1.1157023906707764)


            spot_light_005 = add_spot_light("Key.001", container,
                (-1.2335113286972046, -0.4877118170261383, 1.5836292505264282),
                (0.4597858488559723, -0.7509121894836426, -0.4294576942920685),
                100.80000305175781, 1.0,
                1.4486230611801147, 9.149999618530273,
                0.5)
            set_contact_shadow(spot_light_005, 0.05000000074505806, 0.0024999999441206455)
            spot_light_005.data.color = (0.8283909559249878, 0.7455518841743469, 0.9319397807121277)

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = False
                shading.studio_light = "night.exr"
                shading.studiolight_rotate_z = 2.3561945
                shading.studiolight_intensity = 0.4000000059604645
                shading.studiolight_background_alpha = 0.0
                shading.studiolight_background_blur = 0.5
                space_data.clip_start = 0.009999999776482582

            align_to_head(context, container)


        elif scene_type == "NEON":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.25
                context.scene.eevee.gtao_factor = 0.5
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.65
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 3.0
                context.scene.eevee.bloom_intensity = 1.0
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32.0
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium High Contrast",
                                         0.75, 0.5)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(False)
            restore_hidden_camera()
            container = add_light_container()


            spot_light_000 = add_spot_light("Back", container,
                (-0.007075886707752943, 1.986365795135498, 0.23595929145812988),
                (-0.03276771679520607, 1.3572238683700562, 1.5502748489379883),
                214.40000915527344, 1.0,
                1.4486230611801147, 9.149999618530273,
                1.0)
            set_contact_shadow(spot_light_000, 0.05000000074505806, 0.0024999999441206455)
            spot_light_000.data.color = (0.0, 0.9276570081710815, 0.5703822374343872)


            sun_light_001 = add_sun_light("Dir. Light", container,
                (-0.001717992126941681, -0.03369736298918724, -1.4594181776046753),
                (1.3712451457977295, 0.11371027678251266, 2.9736037254333496),
                1.6200001239776611,
                0.009180432185530663)
            set_contact_shadow(sun_light_001, 0.05000000074505806, 0.0024999999441206455)
            sun_light_001.data.color = (0.0, 0.0, 1.0)


            spot_light_002 = add_spot_light("Key", container,
                (-1.7280012369155884, 0.9464914202690125, -0.048926472663879395),
                (-1.139359951019287, -1.967456579208374, 0.5540574193000793),
                292.0, 1.0,
                1.4486230611801147, 9.149999618530273,
                0.800000011920929)
            set_contact_shadow(spot_light_002, 0.05000000074505806, 0.0024999999441206455)
            spot_light_002.data.color = (0.8950275778770447, 0.0, 1.1049724817276)


            spot_light_003 = add_spot_light("Key.001", container,
                (-0.7152296304702759, -1.5677061080932617, -0.8448387384414673),
                (-0.44580310583114624, -2.239304304122925, 1.5598453283309937),
                101.5999984741211, 1.0,
                1.4486230611801147, 9.149999618530273,
                0.800000011920929)
            set_contact_shadow(spot_light_003, 0.05000000074505806, 0.0024999999441206455)
            spot_light_003.data.color = (0.7645107507705688, 0.9239347577095032, 1.127240777015686)


            spot_light_004 = add_spot_light("Fill", container,
                (1.2904465198516846, 0.9552818536758423, 0.18248367309570312),
                (-1.583914875984192, -1.2385149002075195, -0.9736509919166565),
                20.0, 1.0,
                2.460913896560669, 5.03000020980835,
                0.2020999938249588)
            set_contact_shadow(spot_light_004, 0.05000000074505806, 0.0024999999441206455)
            spot_light_004.data.color = (0.0, 0.0, 1.0)


            spot_light_005 = add_spot_light("Back Light_Head", container,
                (-0.5920169949531555, -1.0476973056793213, -0.6991136074066162),
                (2.2965502738952637, 0.21937033534049988, -0.4970036447048187),
                0.0, 0.2524999976158142,
                1.2740901708602905, 2.5899999141693115,
                0.5163000226020813)
            set_contact_shadow(spot_light_005, 0.05000000074505806, 0.0024999999441206455)
            spot_light_005.data.color = (0.5844155550003052, 0.0, 1.0822510719299316)


            spot_light_006 = add_spot_light("Fill.001", container,
                (3.792802333831787, -0.7317703366279602, 2.6132020950317383),
                (-0.03842347487807274, 1.0002011060714722, -0.28341037034988403),
                12.0, 0.75,
                0.7504914402961731, 9.640000343322754,
                0.6155999898910522)
            set_contact_shadow(spot_light_006, 0.05000000074505806, 0.0024999999441206455)
            spot_light_006.data.color = (0.0, 0.0, 1.0)


            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = False
                shading.studio_light = "studio.exr"
                shading.studiolight_rotate_z = 0.0
                shading.studiolight_intensity = 0.4000000059604645
                shading.studiolight_background_alpha = 0.0
                shading.studiolight_background_blur = 0.5
                space_data.clip_start = 0.009999999776482582

            align_to_head(context, container)


        elif scene_type == "TEMPLATE":

            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
            else:
                context.scene.eevee.use_gtao = True
                context.scene.eevee.gtao_distance = 0.25
                context.scene.eevee.gtao_factor = 0.5
                context.scene.eevee.use_bloom = True
                context.scene.eevee.bloom_threshold = 0.5
                context.scene.eevee.bloom_knee = 0.5
                context.scene.eevee.bloom_radius = 5.0
                context.scene.eevee.bloom_intensity = 0.1
                context.scene.eevee.use_ssr = True
                context.scene.eevee.use_ssr_refraction = True
            context.scene.eevee.bokeh_max_size = 32
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "Medium High Contrast", 0.6, 0.6)
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(False)
            head_pos, camera_pos = target_head(context, 1.0)
            camera, camera_target = camera_setup(context, camera_pos, head_pos)
            context.scene.camera = camera
            container = add_light_container()

            key = add_area_light("Key", container,
                    (-1.5078026056289673, -1.0891118049621582, 2.208820104598999),
                    (1.0848181247711182, -0.881056010723114, -0.5597077012062073),
                    40, 1, 9)
            target_key = add_target("KeyTarget", container, (-0.006276353262364864, -0.004782751202583313, 1.503425121307373))
            track_to(key, target_key)

            fill = add_area_light("Fill", container,
                    (2.28589, -1.51410, 1.40742),
                    (1.4248263835906982, 0.9756063222885132, 0.8594209551811218),
                    10, 1, 9)
            target_fill = add_target("FillTarget", container, (0.013503191992640495, 0.005856933072209358, 1.1814184188842773))
            track_to(fill, target_fill)

            back = add_area_light("Back", container,
                    (0.36789, 0.61511, 2.36201),
                    (-0.7961875796318054, 0.4831638038158417, -0.12343151122331619),
                    40, 0.5, 9, )
            target_back = add_target("BackTarget", container, (0.0032256320118904114, 0.06994983553886414, 1.6254671812057495))
            track_to(back, target_back)

            set_contact_shadow(key, 0.05, 0.0025)
            set_contact_shadow(fill, 0.05, 0.0025)

            if shading:
                #shading.type = 'RENDERED'
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = True

            context.space_data.clip_start = 0.01

        if context.scene.view_settings.view_transform == "AgX":
            filter_lights((0.875, 1, 1, 1))

    except Exception as e:
        utils.log_error("Something went wrong adding lights:", e)

    # restore selection
    bpy.ops.object.select_all(action='DESELECT')
    for obj in current_selected:
        try:
            obj.select_set(True)
        except:
            pass
    try:
        context.view_layer.objects.active = current_active
        if current_mode != "OBJECT":
            bpy.ops.object.mode_set(mode=current_mode)
    except:
        pass


def lighting_setup_camera(context):
    context = vars.get_context(context)

    hide_view_extras(context, False)
    head_pos, camera_pos = target_head(context, 1.0)
    camera, camera_target = camera_setup(context, camera_pos, head_pos)
    context.scene.camera = camera


def get_head_delta(context, chr_cache):
    context = vars.get_context(context)

    z_angle = 0
    head_pos = Vector((0,0,1.4))
    head_rot_z = Quaternion((1, 0, 0, 0))
    if chr_cache:
        arm = chr_cache.get_armature()
        head_bone = None
        for try_name in ["CC_Base_Head", "head", "ORG-spine.006"]:
            if try_name in arm.pose.bones:
                head_bone = arm.pose.bones[try_name]
                break
        if arm and head_bone:
            T: Matrix = arm.matrix_world @ head_bone.matrix
            head_pos = T.to_translation()
            rot = T.to_quaternion()
            forward = rot @ Vector((0,0,1))
            f_2d = Vector((forward.x, forward.y)).normalized()
            z_angle = f_2d.angle_signed(Vector((0,-1)), 0)
            #shading = utils.get_view_3d_shading(context)
            #if shading:
            #    shading.studiolight_rotate_z += z_angle
            head_rot_z = Euler((0,0,z_angle), "XYZ").to_quaternion()
    return z_angle, head_pos, head_rot_z


def target_eyes_plane(chr_cache, head_pos, forward):
    fN = forward.normalized()
    if chr_cache:
        arm = chr_cache.get_armature()
        left_eye_bone = None
        right_eye_bone = None
        for try_name in ["CC_Base_L_Eye", "ORG-eye.L"]:
            if try_name in arm.pose.bones:
                left_eye_bone = arm.pose.bones[try_name]
                break
        for try_name in ["CC_Base_R_Eye", "ORG-eye.R"]:
            if try_name in arm.pose.bones:
                right_eye_bone = arm.pose.bones[try_name]
                break
        if left_eye_bone and right_eye_bone:
            TL = arm.matrix_world @ left_eye_bone.matrix
            TR = arm.matrix_world @ right_eye_bone.matrix
            p = (TL.to_translation() + TR.to_translation()) / 2
            dp = p - head_pos
            d = fN.dot(dp) + 0.02
            return head_pos + fN * d
    return head_pos + fN * 0.09


def target_head(context, distance):
    context = vars.get_context(context)

    context.view_layer.update()
    props = vars.props()
    chr_cache = props.get_context_character_cache(context)
    z_angle, head_pos, head_rot = get_head_delta(context, chr_cache)
    forward = head_rot @ Vector((0,-1,0))
    head_eyes_plane = target_eyes_plane(chr_cache, head_pos, forward)
    return head_eyes_plane, head_eyes_plane + forward*distance


def align_to_head(context, container, use_delta_rot=True):
    context = vars.get_context(context)

    shading = utils.get_view_3d_shading(context)
    current_angle = 0.0
    if shading:
        current_angle = shading.studiolight_rotate_z
    context.view_layer.update()
    props = vars.props()
    chr_cache = props.get_context_character_cache(context)
    z_angle, delta_loc, delta_rot = get_head_delta(context, chr_cache)
    new_angle = current_angle - z_angle
    if new_angle > math.pi:
        new_angle -= 2*math.pi
    elif new_angle < -math.pi:
        new_angle += 2*math.pi
    if shading and use_delta_rot:
        shading.studiolight_rotate_z = new_angle
    for child in container.children:
        loc = child.location.copy()
        if use_delta_rot:
            loc = delta_rot @ loc
        child.location = loc + delta_loc
        if use_delta_rot:
            if child.rotation_mode == "XYZ":
                rot = child.rotation_euler.to_quaternion()
            elif child.rotation_mode == "QUATERNION":
                rot = child.rotation_quaternion
            child.rotation_mode = "QUATERNION"
            child.rotation_quaternion = delta_rot @ rot


def dump_location(o, delta_loc=None):
     if delta_loc is None:
        delta_loc = Vector((0,0,0))
     pos = o.location - delta_loc
     return f"({pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f})"


def dump_vector(v):
     return f"({v.x:.5f}, {v.y:.5f}, {v.z:.5f})"


def dump_color(c):
    return f"({c.r:.4f}, {c.g:.4f}, {c.b:.4f})"


def dump_euler(e):
    return f"({e.x:.3f}, {e.y:.3f}, {e.z:.3f})"


def dump_rotation_euler(o, delta_rot=None):
    if delta_rot is None:
        delta_rot = Quaternion((1,0,0,0))
    if o.rotation_mode == "XYZ":
        rot = -delta_rot @ o.rotation_euler.to_quaternion()
        euler = rot.to_euler()
        return f"({euler.x:.3f}, {euler.y:.3f}, {euler.z:.3f})"
    elif o.rotation_mode == "QUATERNION":
        rot = -delta_rot @ o.rotation_quaternion
        euler = rot.to_euler()
        return f"({euler.x:.3f}, {euler.y:.3f}, {euler.z:.3f})"


def filter_lights(filter):
    for light in bpy.data.objects:
        if light.type == "LIGHT":
            col = light.data.color
            r = col.r
            g = col.g
            b = col.b
            l0 = (r+g+b)/3
            r *= filter[0]
            g *= filter[1]
            b *= filter[2]
            l1 = (r+g+b)/3
            m = l0/l1
            r *= m
            g *= m
            b *= m
            light.data.color = (r,g,b)


def align_with_view(context, obj=None):
    context = vars.get_context(context)

    hide_view_extras(context, False)
    if obj is None:
        obj = utils.get_active_object()
    if utils.object_exists(obj):
        utils.align_object_to_view(obj, context)
        if obj.type == "CAMERA":
            view_space, r3d = utils.get_region_3d(context)
            obj.data.lens = view_space.lens


def hide_view_extras(context, hide):
    context = vars.get_context(context)

    view_space: bpy.types.Area = utils.get_view_3d_space(context)
    if view_space:
        view_space.overlay.show_extras = not hide


def add_view_aligned_camera(context):
    context = vars.get_context(context)

    hide_view_extras(context, False)
    bpy.ops.object.camera_add(enter_editmode=False, align='VIEW')
    camera = utils.get_active_object()
    try:
        context.scene.camera = camera
    except: pass
    align_with_view(context, camera)
    camera.name = "Camera"
    utils.set_ccic_id(camera)
    view_space, r3d = utils.get_region_3d(context)
    if view_space:
        camera.data.lens = view_space.lens
    camera.data.dof.use_dof = False
    camera.data.dof.aperture_fstop = 5.4
    camera.data.dof.aperture_blades = 5
    camera.data.dof.aperture_rotation = 0
    camera.data.dof.aperture_ratio = 1
    camera.data.display_size = 0.2
    camera.data.show_limits = True


def dump_scene_pycode(context):
    context = vars.get_context(context)

    props = vars.props()
    chr_cache = props.get_context_character_cache(context)
    if chr_cache:
        za, dl, dr = get_head_delta(context, chr_cache)
    else:
        za = 0
        dl = bpy.context.active_object.location
        dr = Euler((0,0,0), "XYZ").to_quaternion()
    shading = utils.get_view_3d_shading(context)
    space_data = utils.get_view_3d_space(context)

    code = f"""
            context.scene.eevee.use_taa_reprojection = True
            if utils.B420():
                context.scene.eevee.use_shadows = True
                context.scene.eevee.use_volumetric_shadows = True
                context.scene.eevee.use_raytracing = True
                context.scene.eevee.ray_tracing_options.use_denoise = True
                context.scene.eevee.use_shadow_jitter_viewport = True
                context.scene.eevee.use_bokeh_jittered = True
                context.scene.world.use_sun_shadow = True
                context.scene.world.use_sun_shadow_jitter = True
                context.scene.world.sun_threshold = 0.1
            else:
                context.scene.eevee.use_gtao = {context.scene.eevee.use_gtao}
                context.scene.eevee.gtao_distance = {context.scene.eevee.gtao_distance:.3f}
                context.scene.eevee.gtao_factor = {context.scene.eevee.gtao_factor:.3f}
                context.scene.eevee.use_bloom = {context.scene.eevee.use_bloom}
                context.scene.eevee.bloom_threshold = {context.scene.eevee.bloom_threshold:.3f}
                context.scene.eevee.bloom_knee = {context.scene.eevee.bloom_knee:.3f}
                context.scene.eevee.bloom_radius = {context.scene.eevee.bloom_radius:.3f}
                context.scene.eevee.bloom_intensity = {context.scene.eevee.bloom_intensity:.3f}
                context.scene.eevee.use_ssr = {context.scene.eevee.use_ssr}
                context.scene.eevee.use_ssr_refraction = {context.scene.eevee.use_ssr_refraction}
            context.scene.eevee.bokeh_max_size = {context.scene.eevee.bokeh_max_size:.3f}
            view_transform = prefs.lighting_use_look if utils.B400() else "Filmic"
            colorspace.set_view_settings(view_transform, "{context.scene.view_settings.look}",
                                         {context.scene.view_settings.exposure:.3f}, {context.scene.view_settings.gamma:.3f})
            if context.scene.cycles.transparent_max_bounces < 100:
                context.scene.cycles.transparent_max_bounces = 100

            remove_all_lights(True)
            restore_hidden_camera()
            container = add_light_container()"""

    i = 1
    t = 1
    done_targets = {}
    for light in context.selected_objects:
        if light.type == "LIGHT" and light.data.type == "AREA":
            name = f"area_light_{i:03d}"
            i += 1
            code += f"""

            {name} = add_area_light("{light.name}", container, {dump_location(light, dl)}, {dump_rotation_euler(light, dr)}, {light.data.energy:.1f}, {light.data.size:.1f}, {light.data.cutoff_distance:.1f})
            set_contact_shadow({name}, {light.data.contact_shadow_distance:.3f}, {light.data.contact_shadow_thickness:.3f})
            {name}.data.color = {dump_color(light.data.color)}"""

        if light.type == "LIGHT" and light.data.type == "SPOT":
            name = f"spot_light_{i:03d}"
            i += 1
            code += f"""

            {name} = add_spot_light("{light.name}", container, {dump_location(light, dl)}, {dump_rotation_euler(light, dr)}, {light.data.energy:.1f}, {light.data.spot_blend:.1f}, {light.data.spot_size:.1f}, {light.data.cutoff_distance:.1f}, {light.data.shadow_soft_size:.1f})
            set_contact_shadow({name}, {light.data.contact_shadow_distance:.3f}, {light.data.contact_shadow_thickness:.3f})
            {name}.data.color = {dump_color(light.data.color)}"""

        if light.type == "LIGHT" and light.data.type == "SUN":
            name = f"sun_light_{i:03d}"
            i += 1
            code += f"""

            {name} = add_sun_light("{light.name}", container, {dump_location(light, dl)}, {dump_rotation_euler(light, dr)}, {light.data.energy:.1f}, {light.data.angle:.1f})
            set_contact_shadow({name}, {light.data.contact_shadow_distance:.3f}, {light.data.contact_shadow_thickness:.3f})
            {name}.data.color = {dump_color(light.data.color)}"""

        if light.type == "LIGHT" and light.data.type == "POINT":
            name = f"sun_light_{i:03d}"
            i += 1
            code += f"""

            {name} = add_point_light("{light.name}", container, {dump_location(light, dl)}, {dump_rotation_euler(light, dr)}, {light.data.energy:.1f}, {light.data.shadow_soft_size:.1f})
            set_contact_shadow({name}, {light.data.contact_shadow_distance:.3f}, {light.data.contact_shadow_thickness:.3f})
            {name}.data.color = {dump_color(light.data.color)}"""

        for con in light.constraints:
            if con.type == "TRACK_TO":
                target = con.target
                if target and target not in done_targets:
                    target_name = f"target_{t:03d}"
                    done_targets[target] = target_name
                    t += 1
                    code += f"""
            {target_name} = add_target({target_name}, container, {dump_location(target, dl)})"""
                else:
                    target_name = done_targets[target]
                code += f"""
            track_to({name}, {target_name})"""

    code += f"""

            if shading:
                if shading.type not in ["MATERIAL", "RENDERED"]:
                    shading.type = "MATERIAL"
                shading.use_scene_lights = True
                shading.use_scene_world = False
                shading.use_scene_lights_render = True
                shading.use_scene_world_render = False
                shading.studio_light = "{shading.studio_light}"
                shading.studiolight_rotate_z = {(shading.studiolight_rotate_z - za):.3f}
                shading.studiolight_intensity = {shading.studiolight_intensity:.3f}
                shading.studiolight_background_alpha = {shading.studiolight_background_alpha:.3f}
                shading.studiolight_background_blur = {shading.studiolight_background_blur:.3f}
                space_data.clip_start = {space_data.clip_start:.3f}

            align_to_head(context, container)

    """

    print(code)


# zoom view to imported character
def zoom_to_character(chr_cache):
    props = vars.props()
    try:
        if chr_cache:
            utils.try_select_objects(chr_cache.get_cache_objects(), clear_selection=True)
            zoom_to_selected()
    except:
        pass


def zoom_to_selected():
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            for region in area.regions:
                if region.type == "WINDOW":
                    context = bpy.context.copy()
                    context['area'] = area
                    context['region'] = region
                    if utils.B320():
                        with bpy.context.temp_override(**context):
                            bpy.ops.view3d.view_selected()
                            # bpy.ops.view3d.camera_to_view_selected()
                    else:
                        bpy.ops.view3d.view_selected(context)


def render_image(context):
    # TBD
    pass


def render_animation(context):
    # TBD
    pass


def dump_mesh_pycode(obj: bpy.types.Object):
    code = f"""
    location = {dump_location(obj)}
    rotation = {dump_rotation_euler(obj)}
    """
    mesh: bpy.types.Mesh = obj.data
    vert_code = ""
    for i, vert in enumerate(mesh.vertices):
        if i > 0:
            vert_code += ", "
            if i % 4 == 0:
                vert_code += """
                        """
        vert_code += dump_vector(vert.co)
    face_code = ""
    for i, face in enumerate(mesh.polygons):
        if i > 0:
            face_code += ", "
            if i % 4 == 0:
                face_code += """
                        """
        face_code += "("
        for j, vert in enumerate(face.vertices):
            if j > 0: face_code += ", "
            face_code += f"{vert}"
        face_code += ")"
    code += f"""
    mesh.from_pydata([{vert_code}],
                     [],
                     [{face_code}])
    """
    print(code)


def create_backdrop(container, color, roughness):
    backdrop_name = "Backdrop"
    backdrop_prop = "rl_backdrop_preset"
    backdrop: bpy.types.Object = None
    for obj in bpy.data.objects:
        if obj.name.startswith(backdrop_name) and backdrop_prop in obj:
            backdrop = obj
            break
    if not backdrop:
        mesh = bpy.data.meshes.new(backdrop_name)
        mesh.from_pydata([(-2.34281, -2.34281, 0.00000), (2.34281, -2.34281, 0.00000), (-2.34281, 2.34281, 3.41876), (2.34281, 2.34281, 3.41876),
                          (-2.34281, 1.51495, 0.00000), (-2.34281, 2.34281, 0.82786), (-2.34281, 1.58331, 0.00283), (-2.34281, 1.65121, 0.01129),
                          (-2.34281, 1.71817, 0.02533), (-2.34281, 1.78375, 0.04486), (-2.34281, 1.84749, 0.06973), (-2.34281, 1.90896, 0.09978),
                          (-2.34281, 1.96774, 0.13480), (-2.34281, 2.02343, 0.17456), (-2.34281, 2.07564, 0.21878), (-2.34281, 2.12402, 0.26717),
                          (-2.34281, 2.16825, 0.31938), (-2.34281, 2.20800, 0.37506), (-2.34281, 2.24303, 0.43384), (-2.34281, 2.27308, 0.49531),
                          (-2.34281, 2.29795, 0.55905), (-2.34281, 2.31748, 0.62463), (-2.34281, 2.33152, 0.69160), (-2.34281, 2.33998, 0.75950),
                          (2.34281, 2.34281, 0.82786), (2.34281, 1.51495, 0.00000), (2.34281, 2.33998, 0.75950), (2.34281, 2.33152, 0.69160),
                          (2.34281, 2.31748, 0.62463), (2.34281, 2.29795, 0.55905), (2.34281, 2.27308, 0.49531), (2.34281, 2.24303, 0.43384),
                          (2.34281, 2.20800, 0.37506), (2.34281, 2.16825, 0.31938), (2.34281, 2.12402, 0.26717), (2.34281, 2.07564, 0.21878),
                          (2.34281, 2.02343, 0.17456), (2.34281, 1.96774, 0.13480), (2.34281, 1.90896, 0.09978), (2.34281, 1.84749, 0.06973),
                          (2.34281, 1.78375, 0.04486), (2.34281, 1.71817, 0.02533), (2.34281, 1.65121, 0.01129), (2.34281, 1.58331, 0.00283)],
                         [],
                         [(5, 24, 3, 2), (24, 5, 23, 26), (26, 23, 22, 27), (27, 22, 21, 28),
                          (28, 21, 20, 29), (29, 20, 19, 30), (30, 19, 18, 31), (31, 18, 17, 32),
                          (32, 17, 16, 33), (33, 16, 15, 34), (34, 15, 14, 35), (35, 14, 13, 36),
                          (36, 13, 12, 37), (37, 12, 11, 38), (38, 11, 10, 39), (39, 10, 9, 40),
                          (40, 9, 8, 41), (41, 8, 7, 42), (42, 7, 6, 43), (43, 6, 4, 25),
                          (0, 1, 25, 4)])
        for poly in mesh.polygons:
            poly.use_smooth = True
        mesh.update()
        backdrop = bpy.data.objects.new(backdrop_name, mesh)
        bpy.context.collection.objects.link(backdrop)
    if backdrop:
        if container:
            backdrop.parent = container
            backdrop.matrix_parent_inverse = container.matrix_world.inverted()
        backdrop.location = Vector((0.000, -0.994, 0.000))
        backdrop.rotation_mode = "XYZ"
        backdrop.rotation_euler = Euler((0.000, -0.000, 0.000), "XYZ")
        backdrop[backdrop_prop] = True
    # Material
    material: bpy.types.Material = None
    material_name = "Backdrop"
    material_prop = "rl_backdrop_preset"
    for mat in bpy.data.materials:
        if mat.name.startswith(material_name) and material_prop in mat:
            material = mat
            break
    if not material:
        material = bpy.data.materials.new(material_name)
        material[material_prop] = True
    if material:
        backdrop.data.materials.append(material)
        material.use_nodes = True
        for node in material.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                node.inputs["Base Color"].default_value = color
                node.inputs["Roughness"].default_value = roughness
    return backdrop


def fetch_anim_range(context, expand = False, fit = True):
    """Fetch anim range from character animation.
    """
    props = vars.props()
    context = vars.get_context(context)

    chr_cache = props.get_context_character_cache(context)
    arm = chr_cache.get_armature()
    if arm:
        action = utils.safe_get_action(arm)
        if action:
            if context.scene.use_preview_range:
                start = context.scene.frame_preview_start
                end = context.scene.frame_preview_end
            else:
                start = context.scene.frame_start
                end = context.scene.frame_end
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
            if context.scene.use_preview_range:
                context.scene.frame_preview_start = start
                context.scene.frame_preview_end = end
            else:
                context.scene.frame_start = start
                context.scene.frame_end = end


def cycles_setup(context):
    props = vars.props()
    context = vars.get_context(context)

    hide_view_extras(context, False)
    chr_cache = props.get_context_character_cache(context)
    extracted = False

    # extract eyelashes from body objects
    for obj in chr_cache.get_cache_objects():
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and not obj_cache.disabled and obj_cache.is_mesh():
            if obj_cache.object_type == "BODY":
                eyelashes = meshutils.separate_mesh_material_type(chr_cache, obj, "EYELASH")
                if eyelashes:
                    extracted = True
                    eyelashes.name = obj.name.replace("CC_Base_Body", "CC_Base_Eyelash")

    # add modifiers and terminator offsets
    for obj in chr_cache.get_cache_objects():
        obj_cache = chr_cache.get_object_cache(obj)
        if obj_cache and not obj_cache.disabled and obj_cache.is_mesh():
            if not modifiers.has_modifier(obj, "SUBSURF"):
                mod = obj.modifiers.new(name = "Subdivision", type = "SUBSURF")
                if utils.B291():
                    mod.boundary_smooth = 'PRESERVE_CORNERS'
            if utils.B290():
                if obj.cycles.shadow_terminator_offset == 0.0:
                    obj.cycles.shadow_terminator_offset = 0.1

    # rebuild for cycles if needed
    if chr_cache.render_target != "CYCLES":
        bpy.ops.cc3.importer(param="REBUILD_CYCLES")
    else:
        if extracted:
            bpy.ops.cc3.importer(param="BUILD_DRIVERS")

    try:
        context.scene.render.engine = 'CYCLES'
        context.scene.cycles.device = 'GPU'
    except:
        pass

    try:
        # preview
        context.scene.cycles.use_preview_adaptive_sampling = True
        #context.scene.cycles.preview_adaptive_threshold = 0.05
        #context.scene.cycles.preview_samples = 512
        context.scene.cycles.use_preview_denoising = True
        #context.scene.cycles.preview_denoising_start_sample = 1
        context.scene.cycles.preview_denoising_input_passes = 'RGB_ALBEDO_NORMAL'
        # render
        context.scene.cycles.use_adaptive_sampling = True
        #context.scene.cycles.adaptive_threshold = 0.02
        #context.scene.cycles.samples = 512
        context.scene.cycles.use_denoising = True
        context.scene.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    except:
        pass

    try:
        context.scene.cycles.preview_denoiser = 'OPTIX'
        context.scene.cycles.denoiser = 'OPTIX'
    except:
        pass


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
        props = vars.props()

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
            context.view_layer.update()

        elif self.param == "CYCLES_SETUP":
            cycles_setup(context)

        elif self.param == "DUMP_SETUP":
            dump_scene_pycode(context)

        elif self.param == "DUMP_OBJ":
            dump_mesh_pycode(context.active_object)

        elif self.param == "FILTER_LIGHTS":
            filter_lights(props.light_filter)

        elif self.param == "ALIGN_WITH_VIEW":
            align_with_view(context)

        elif self.param == "ADD_CAMERA":
            add_view_aligned_camera(context)

        elif self.param == "SETUP_CAMERA":
            lighting_setup_camera(context)

        elif self.param == "SETUP_WORLD":
            compositor_setup(context)
            world_setup(context)

        else:
            setup_scene_default(context, self.param)
            if self.param == "TEMPLATE":
                compositor_setup(context)
                world_setup(context)
                utils.message_box("World nodes and compositor template set up.")
            else:
                if not self.param.startswith("PRESET_"):
                    world_setup(context)

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
        elif properties.param == "FILTER_LIGHTS":
            return "Filter all light colors by this color"
        elif properties.param == "ALIGN_WITH_VIEW":
            return "Align active object to current viewpoint location and rotation. Useful for quickly positioning and aligning lights and cameras"
        elif properties.param == "ADD_CAMERA":
            return "Add a camera aligned with the current viewpoint location and rotation, and make it the currently active camera"

        return ""
